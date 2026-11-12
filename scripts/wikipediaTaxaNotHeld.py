#!/usr/bin/env python3
"""Which taxa does English Wikipedia have an article for that the tree does not hold?

The other direction -- which of our species have an article -- is measured in
BACKLOG.md ("The species long tail"). This one reads the full enwiki dump, not
/Volumes/WikiDump/wiki-pages.sqlite: that file was built from our own name list
(species-names.json), so it can only contain names we already had.

Two passes:

  scan     every article carrying a taxobox (Speciesbox, Subspeciesbox,
           Infraspeciesbox, Taxobox, Automatic taxobox, Virusbox) and every
           Template:Taxonomy/<name> page (rank + parent, which is how
           Wikipedia places a Speciesbox taxon) -> <out>/wiki-taxa.jsonl,
           <out>/wiki-taxonomy-templates.jsonl. Parallel over the
           multistream blocks; about 1.5 hours for the 2026-06-01 dump.
  compare  those names against portal/data/species.parquet (the six portal
           kingdoms) and the bacteria/viruses family files ->
           data/wikipedia-taxa-not-held.json (summary) and
           <out>/wikipedia-taxa-not-held.jsonl (every name).

A name in the report is a lead, not a record: Wikipedia is not a source this
tree takes names from (CLAUDE.md, "No LLM-generated content" -- every node needs
a checkable source). What it shows is where a dataset we have not imported, or
a synonym we do not resolve, is likely to be.

    python3 scripts/wikipediaTaxaNotHeld.py scan
    python3 scripts/wikipediaTaxaNotHeld.py compare
"""
import argparse
import bz2
import collections
import datetime
import glob
import json
import multiprocessing as mp
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = "/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream.xml.bz2"
INDEX = "/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream-index.txt.bz2"
OUT = "/Volumes/MacieExternal/sources/wikipedia-taxa"
PARQUET = os.path.join(ROOT, "portal", "data", "species.parquet")
REPORT = os.path.join(ROOT, "data", "wikipedia-taxa-not-held.json")
# species.parquet holds the six portal kingdoms; these two are read from their family files.
FAMILY_FILE_KINGDOMS = ("bacteria", "viruses")

BOX = re.compile(r"\{\{\s*(Speciesbox|Subspeciesbox|Infraspeciesbox|Taxobox|Automatic[ _]taxobox|Virusbox)\s*[|}\n]",
                 re.I)
PAGE = re.compile(r"<page>(.*?)</page>", re.S)
TITLE = re.compile(r"<title>(.*?)</title>")
NS = re.compile(r"<ns>(\d+)</ns>")
TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
REDIRECT = re.compile(r'<redirect title="([^"]*)"')
# Kingdoms as Wikipedia's taxonomy templates name them, mapped onto ours.
KINGDOM = {"animalia": "animalia", "plantae": "plantae", "fungi": "fungi",
           "chromista": "chromista", "protozoa": "protozoa", "archaea": "archaea",
           "bacteria": "bacteria", "virus": "viruses", "viruses": "viruses"}


def unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
             .replace("&#039;", "'").replace("&amp;", "&"))


def template_params(text, start):
    """Top-level |key=value params of the template opening at `start`."""
    depth, i, n = 0, start, len(text)
    while i < n:
        two = text[i:i + 2]
        if two in ("{{", "[["):
            depth += 1; i += 2; continue
        if two in ("}}", "]]"):
            depth -= 1; i += 2
            if depth == 0:
                break
            continue
        i += 1
    body = text[start + 2:i - 2]
    parts, cur, d, j = [], [], 0, 0
    while j < len(body):
        two = body[j:j + 2]
        if two in ("{{", "[["):
            d += 1; cur.append(two); j += 2; continue
        if two in ("}}", "]]"):
            d -= 1; cur.append(two); j += 2; continue
        if body[j] == "|" and d == 0:
            parts.append("".join(cur)); cur = []; j += 1; continue
        cur.append(body[j]); j += 1
    parts.append("".join(cur))
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().lower()] = v.strip()
    return params


def clean(v):
    v = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", "", v or "", flags=re.S)
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"\{\{[^{}]*\}\}", "", v)
    v = re.sub(r"<[^>]+>", "", v).replace("'''", "").replace("''", "")
    v = v.replace("†", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", v).strip()


def name_key(name):
    """Lowercase, without the hybrid sign: "Citrus × paradisi" and "Citrus ×paradisi" meet."""
    return " ".join(name.replace("×", " ").lower().split())


def unqualify(name):
    return re.sub(r"\s*\([^)]*\)", "", name).strip()


def taxon_from_box(kind, p):
    """(name, rank, genus, extra) for one taxobox, or None."""
    kind = kind.lower().replace("_", " ")
    # A genus that needs disambiguating is spelled like its taxonomy template,
    # "Eisenia (alga)": the name drops the qualifier, the template lookup keeps it.
    if kind == "speciesbox":
        genus = clean(p.get("genus")) or clean(p.get("taxon")).split(" ")[0]
        name = clean(p.get("taxon")) or " ".join(filter(None, [genus, clean(p.get("species"))]))
        return unqualify(name), "SPECIES", genus, {}
    if kind in ("subspeciesbox", "infraspeciesbox"):
        parts = [clean(p.get("genus")), clean(p.get("species")),
                 clean(p.get("subspecies") or p.get("variety") or p.get("forma"))]
        return unqualify(" ".join(filter(None, parts))), "SUBSPECIES", parts[0], {}
    if kind == "virusbox" and p.get("species"):
        # A virus species names itself in `species`, its genus in `parent`.
        return clean(p["species"]), "SPECIES", clean(p.get("parent")), {}
    if kind in ("automatic taxobox", "virusbox"):
        name = clean(p.get("taxon"))
        return name, "", name.split(" ")[0] if name else "", {}
    # Manual Taxobox: binomial/trinomial, else the lowest rank given.
    extra = {k: clean(p[k]) for k in ("regnum", "familia", "ordo", "classis", "phylum", "divisio")
             if p.get(k)}
    if p.get("trinomial"):
        name = clean(p["trinomial"])
        return name, "SUBSPECIES", name.split(" ")[0], extra
    if p.get("binomial"):
        name = clean(p["binomial"])
        return name, "SPECIES", name.split(" ")[0], extra
    for rank in ("genus", "familia", "ordo", "classis", "phylum", "divisio", "regnum"):
        if p.get(rank):
            return clean(p[rank]), rank.upper(), "", extra
    return None


def scan_block(args):
    start, end = args
    with open(DUMP, "rb") as fh:
        fh.seek(start)
        raw = fh.read(end - start if end else -1)
    try:
        xml = bz2.decompress(raw).decode("utf-8", "replace")
    except Exception:
        return [], []
    taxa, templates = [], []
    for m in PAGE.finditer(xml):
        page = m.group(1)
        ns = NS.search(page)
        ns = int(ns.group(1)) if ns else -1
        title = unescape(TITLE.search(page).group(1))
        if "<redirect" in page:
            # A taxonomy template that moved still sits in other templates' parent chains.
            r = REDIRECT.search(page)
            if ns == 10 and title.startswith("Template:Taxonomy/") and r \
                    and unescape(r.group(1)).startswith("Template:Taxonomy/"):
                templates.append({"t": title[len("Template:Taxonomy/"):],
                                  "redirect": unescape(r.group(1))[len("Template:Taxonomy/"):]})
            continue
        t = TEXT.search(page)
        if not t:
            continue
        text = unescape(t.group(1))
        if ns == 10 and title.startswith("Template:Taxonomy/"):
            # The data is in {{Don't edit this line …}}; a {{High-use}} banner
            # inside <noinclude> often comes first.
            i = text.find("{{Don't edit this line")
            if i < 0:
                i = text.find("{{")
            if i < 0:
                continue
            p = template_params(text, i)
            templates.append({"t": title[len("Template:Taxonomy/"):],
                              "rank": clean(p.get("rank")).lower(),
                              "parent": clean(p.get("parent")),
                              "link": clean(p.get("link")).split("|")[0],
                              "same_as": clean(p.get("same_as") or p.get("same as")),
                              "extinct": bool(p.get("extinct"))})
        elif ns == 0:
            b = BOX.search(text)
            if not b:
                continue
            p = template_params(text, b.start())
            # A box with no readable name is still written, so compare can count it.
            name, rank, genus, extra = taxon_from_box(b.group(1), p) or ("", "", "", {})
            rec = {"title": title, "box": b.group(1), "name": name, "rank": rank,
                   "genus": genus, "authority": clean(p.get("authority") or
                                                       p.get("binomial_authority")),
                   "extinct": bool(p.get("extinct"))}
            if p.get("parent"):
                rec["parent"] = clean(p["parent"])
            rec.update(extra)
            taxa.append(rec)
    return taxa, templates


def blocks():
    offsets = set()
    with bz2.open(INDEX, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            offsets.add(int(line.split(":", 1)[0]))
    offs = sorted(offsets)
    return [(o, offs[i + 1] if i + 1 < len(offs) else 0) for i, o in enumerate(offs)]


def cmd_scan(args):
    os.makedirs(OUT, exist_ok=True)
    bl = blocks()
    print(f"  {len(bl):,} blocks, {args.workers} workers", flush=True)
    tf = open(os.path.join(OUT, "wiki-taxa.jsonl.part"), "w", encoding="utf-8")
    pf = open(os.path.join(OUT, "wiki-taxonomy-templates.jsonl.part"), "w", encoding="utf-8")
    nt = np_ = 0
    with mp.Pool(args.workers) as pool:
        for i, (taxa, tmpl) in enumerate(pool.imap_unordered(scan_block, bl, chunksize=64)):
            for r in taxa:
                tf.write(json.dumps(r, ensure_ascii=False) + "\n")
            for r in tmpl:
                pf.write(json.dumps(r, ensure_ascii=False) + "\n")
            nt += len(taxa); np_ += len(tmpl)
            if i % 20000 == 0:
                print(f"  {i:,}/{len(bl):,} blocks  {nt:,} taxobox articles  {np_:,} taxonomy templates",
                      flush=True)
    tf.close(); pf.close()
    for f in ("wiki-taxa.jsonl", "wiki-taxonomy-templates.jsonl"):
        os.replace(os.path.join(OUT, f + ".part"), os.path.join(OUT, f))
    print(f"  done: {nt:,} taxobox articles, {np_:,} taxonomy templates -> {OUT}")


def lineage(name, tmpl, cache):
    """{rank: name} walking Template:Taxonomy parents from `name` upward."""
    if name in cache:
        return cache[name]
    out, cur, seen = {"_chain": []}, name, set()
    while cur and cur not in seen:
        seen.add(cur)
        # "Archaeplastida/showdomain" is a display variant of "Archaeplastida".
        t = tmpl.get(cur) or tmpl.get(cur.split("/")[0])
        if not t:
            break
        if t.get("redirect"):
            cur = t["redirect"]
            continue
        # same_as: rank and parent come from the other template unless given here.
        base = tmpl.get(t.get("same_as") or "", {})
        rank, parent = t["rank"] or base.get("rank", ""), t["parent"] or base.get("parent", "")
        taxon = unqualify(cur.split("/")[0])
        out["_chain"].append(taxon)
        if rank:
            # The template name is the taxon; `link` is an article title ("Animal").
            out.setdefault(rank, taxon)
        cur = parent
    cache[name] = out
    return out


def cmd_compare(args):
    import duckdb
    tmpl = {}
    for line in open(os.path.join(OUT, "wiki-taxonomy-templates.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        tmpl.setdefault(r["t"], r)
    con = duckdb.connect()
    held = collections.defaultdict(set)
    genera = collections.defaultdict(set)
    for k, name, canon, genus in con.sql(
            f"select kingdom, name, canonicalName, genus from '{PARQUET}'").fetchall():
        for n in (name, canon):
            if n:
                held[name_key(n)].add(k)
        if genus:
            genera[name_key(genus)].add(k)
    for k in FAMILY_FILE_KINGDOMS:
        for path in glob.glob(os.path.join(ROOT, "taxonomy", k, "**", "src", "data", "*.json"),
                              recursive=True):
            stack = [json.load(open(path, encoding="utf-8"))]
            while stack:
                n = stack.pop()
                if n.get("rank") in ("SPECIES", "SUBSPECIES") and n.get("name"):
                    held[name_key(n["name"])].add(k)
                elif n.get("rank") == "GENUS" and n.get("name"):
                    genera[name_key(n["name"])].add(k)
                stack.extend(n.get("children") or [])
    # Wikipedia has no Chromista or Protozoa kingdom (its protists stop at Eukaryota),
    # so a lineage without one is placed by any higher taxon the tree holds in one kingdom.
    higher = collections.defaultdict(set)
    for row in con.sql(f"select distinct kingdom, phylum, cls, ord, familyName from '{PARQUET}'").fetchall():
        for n in row[1:]:
            if n:
                higher[name_key(n)].add(row[0])
    built = datetime.datetime.fromtimestamp(os.path.getmtime(PARQUET)).isoformat(timespec="seconds")

    cache = {}
    seen = set()
    counts = collections.Counter()
    by_kingdom = collections.defaultdict(collections.Counter)
    by_family = collections.Counter()
    fossils = collections.Counter()
    out = open(os.path.join(OUT, "wikipedia-taxa-not-held.jsonl"), "w", encoding="utf-8")
    # Every article lands in exactly one of these, so they add up to taxoboxArticles.
    articles = collections.Counter()
    for line in open(os.path.join(OUT, "wiki-taxa.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        # '"Cochranella" euhystrix': quotes mark a genus not yet placed, not part of the name.
        name = r["name"].replace('"', "")
        rank = r["rank"]
        if rank not in ("SPECIES", "SUBSPECIES") and len(name_key(unqualify(name)).split()) == 2:
            rank = "SPECIES"  # an Automatic taxobox on a binomial
        if not name:
            articles["box without a taxon name"] += 1
            continue
        if rank not in ("SPECIES", "SUBSPECIES"):
            articles["above species rank"] += 1
            continue
        # Hybrids keep their "×": "Citrus × paradisi", "× Triticosecale rimpaui";
        # botanical names keep a diaeresis: "Epichloë typhina".
        if not re.match(r"^(× )?[A-Z][a-zäëïöü-]+( ×)? [a-zäëïöü-]+( [a-zäëïöü-]+)?$", name):
            articles["name not a plain binomial or trinomial"] += 1
            continue
        if name in seen:
            articles["second article for the same name"] += 1
            continue
        seen.add(name)
        articles[f"compared, {rank.lower()}"] += 1
        lin = lineage(r.get("parent") or r["genus"], tmpl, cache)
        kingdom = KINGDOM.get((lin.get("regnum") or lin.get("kingdom") or r.get("regnum") or "")
                              .lower().split()[0] if (lin.get("regnum") or lin.get("kingdom")
                                                      or r.get("regnum")) else "", "")
        if not kingdom and lin.get("domain", "").lower() in ("bacteria", "archaea"):
            kingdom = KINGDOM[lin["domain"].lower()]
        if not kingdom and (lin.get("virus_realm") or lin.get("realm")):
            kingdom = "viruses"
        if not kingdom:
            for taxon in lin["_chain"]:
                if len(higher.get(name_key(taxon), ())) == 1:
                    kingdom = next(iter(higher[name_key(taxon)]))
                    break
        family = lin.get("familia") or lin.get("family") or r.get("familia") or ""
        # Wikipedia marks a fossil genus extinct on its taxonomy template, not on each species.
        gt = tmpl.get(r.get("parent") or r["genus"]) or {}
        extinct = bool(r.get("extinct") or gt.get("extinct"))
        key = name_key(name)
        if rank == "SUBSPECIES":
            species = " ".join(key.split()[:2])
            status = ("held" if key in held else
                      "species held" if species in held else "not held")
        else:
            status = "held" if key in held else "not held"
        if status != "held":
            status += (", genus held" if name_key(unqualify(r["genus"])) in genera
                       else ", genus not held")
        counts[(rank, status)] += 1
        by_kingdom[kingdom or "unknown"][(rank, status)] += 1
        if status.startswith("not held") and rank == "SPECIES":
            by_family[(kingdom or "unknown", family or "?")] += 1
            if extinct:
                fossils[kingdom or "unknown"] += 1
        if status != "held":
            out.write(json.dumps({"name": name, "rank": rank, "status": status, "kingdom": kingdom,
                                  "family": family, "authority": r.get("authority"),
                                  "extinct": extinct, "title": r["title"]},
                                 ensure_ascii=False) + "\n")
    out.close()

    def table(c):
        return {f"{rank} {status}": n for (rank, status), n in sorted(c.items())}
    report = {
        "generatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "dump": os.path.basename(DUMP),
        "speciesParquet": built,
        "note": ("Leads, not records: a name here has an English Wikipedia article and no node in "
                 "the tree. Wikipedia is not a source the tree takes names from; the list points at "
                 "datasets not imported yet and synonyms not resolved. bacteria/viruses are matched "
                 "against their family files on this checkout (q-bert writes them), so they are "
                 "only as current as its last landing."),
        "taxoboxArticles": sum(1 for _ in open(os.path.join(OUT, "wiki-taxa.jsonl"), encoding="utf-8")),
        "taxonomyTemplates": len(tmpl),
        "articles": dict(articles.most_common()),
        "totals": table(counts),
        "byKingdom": {k: table(v) for k, v in sorted(by_kingdom.items())},
        "speciesNotHeldExtinct": dict(sorted(fossils.items())),
        "topFamiliesNotHeld": [{"kingdom": k, "family": f, "species": n}
                               for (k, f), n in by_family.most_common(100)],
    }
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    assert sum(articles.values()) == report["taxoboxArticles"], (articles, report["taxoboxArticles"])
    print(json.dumps({k: report[k] for k in ("taxoboxArticles", "taxonomyTemplates", "articles",
                                             "totals")},
                     indent=1))
    for k, v in report["byKingdom"].items():
        print(f"  {k:<10} " + "  ".join(f"{s}: {n:,}" for s, n in v.items()))
    print(f"  wrote {REPORT} and {OUT}/wikipedia-taxa-not-held.jsonl")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    sub.add_parser("compare")
    args = ap.parse_args()
    {"scan": cmd_scan, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
