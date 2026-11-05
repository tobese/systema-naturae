#!/usr/bin/env python3
"""Transform for a nomenclatural source: enrich species we hold, add none.

A names index (IPNI, ChecklistBank 2006) is not a checklist: its Taxon table
has no status, no rank and no parent, so the species transform offers 0 and
the source looks useless. It is the opposite for nomenclature -- every name
with its authorship, year and page, plus basionym, replacement-name and
later-homonym links. Decided 2026-11-01: such a source gets its own path,
this transform and applyEnrichment.py, instead of the species importer.

Reads a ColDP names index (Name.tsv, NameRelation.tsv) and our family files
for the kingdoms the source's code covers, matches by canonical binomial,
and writes into <sources>/work/<work-slug>/:

  enrich.jsonl     fills, for applyEnrichment.py: authorship (and the
                   year with it) on a species that has none, where the source
                   gives exactly one authorship for the name. The source id
                   goes into sourceIds only where we hold the binomial once in
                   the kingdom -- two nodes carrying one IPNI id would be an
                   authority-id collision (verifyTree).
  review-authorship.jsonl   our authorship and the source's disagree even
                   after taxamatch.same_authorship with the Wikidata author
                   index (DC. = de Candolle); a human call, never applied
  review-basionym-pairs.jsonl  both names of a basionym / replacement /
                   synonym pair held as separate species: one is a synonym of
                   the other; which one is accepted is COL's/WCVP's call (a
                   checklist-shaped source's own synonymy is one more vote)
  review-later-homonyms.jsonl  names we hold that the source marks as a
                   later homonym (illegitimate)
  summary.json

A source whose authorship agrees with ours on fewer than MIN_AGREEMENT of the
names both carry fills nothing (verdict "review-only" in summary.json): its
would-be fills go to review-fills.jsonl and the queue parks it.

Read-only on the tree. Without --apply only the counts are printed.

    python3 scripts/nomenclatureTransform.py <archive.zip> <work-slug> [--apply]
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
import taxamatch  # noqa: E402
import writerKingdoms  # noqa: E402
from buildSpeciesParquet import canonicalize  # noqa: E402
from tree import ROOT, iter_family_files, iter_species_with_parent  # noqa: E402

# The registry of nomenclatural sources, keyed by the archive's metadata alias
# (or --code): which of our kingdoms each speaks for, and the author index's
# code. IPNI covers vascular plants (ICN). Species Fungorum Plus is shaped
# like a checklist (Taxon + Synonym tables) but used here for its names and
# authorship -- being listed is the decision that it belongs on this track;
# only a pure names index is recognised by shape (is_names_index).
# LPSN (prokaryotes, ICNP) speaks for two kingdoms on two machines: Macie
# writes archaea, q-bert bacteria (writerKingdoms); each run takes only the
# kingdoms its machine may write. Its authors are in neither the zoological
# nor the botanical index, so it compares with both (code None).
# Index Animalium (Sherborn 1758-1850, 316855) is animal names as first
# published: its authorship is "J. C. Fabricius" with the year apart, which
# zoological_authorship() turns into our "Fabricius, 1798".
KINGDOMS_FOR = {"IPNI": ("plantae",), "Species Fungorum Plus": ("fungi",),
                "LPSN": ("archaea", "bacteria"), "Index Animalium": ("animalia",)}
AUTHOR_CODE = {"IPNI": "bot", "Species Fungorum Plus": "bot", "LPSN": None,
               "Index Animalium": "zoo"}
SPECIES_RANKS = {"spec.", "sp.", "species"}
# The verdict, from the source itself: on the names it shares with us and
# where both sides give an authorship, how often do they agree? IPNI, Species
# Fungorum Plus and LPSN agree 98.4-98.7%; Index Animalium 69% -- Sherborn
# records a binomial's first printing, so a later combination's author or a
# re-listing's year, and 14 of 26 sampled fills were wrong against GBIF
# (2026-11-05). A source below the bar, or with too few names to judge,
# fills nothing: its fills go to review-fills.jsonl for a human instead.
MIN_AGREEMENT = 0.95
MIN_COMPARED = 500
PAIR_RELATIONS = {"BASIONYM", "REPLACEMENT_NAME", "SYNONYM"}


def _rows(z, member):
    csv.field_size_limit(10 ** 8)
    with z.open(member) as fh:
        rd = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t",
                        quoting=csv.QUOTE_NONE)
        head = [h.split(":")[-1] for h in next(rd)]
        for r in rd:
            yield dict(zip(head, r))


def _member(z, name):
    return next((n for n in z.namelist() if n.split("/")[-1].lower() == name.lower()), None)


def is_names_index(archive):
    """A ColDP with a Name table and no classification: no Synonym table, no
    NameUsage table, and a Taxon table (if any) with no parent links. Status
    says nothing -- a ColDP checklist's Taxon table is accepted by
    definition and often leaves it blank (World Plants, 2026-11-01) -- and
    the parent column is spelled parentID, parentId or parent_id.

    Also a NameUsage table that is nothing but bare names, with no parents:
    Index Animalium (316855) is shaped so, and failed as a checklist with "no
    column col:parentID". Status decides here, unlike above: MDD (9802) has
    no parents either but is a checklist, its rows accepted or synonyms. The
    whole table, not a sample: uBio (316856) opens with 12,000 bare names
    and then carries its uBiota classification, accepted rows with parents;
    a checklist stops at its first such row, so this stays quick for one."""
    try:
        z = zipfile.ZipFile(archive)
    except (OSError, zipfile.BadZipFile):
        return False
    usage = _member(z, "NameUsage.tsv")
    if usage and not _member(z, "Name.tsv") and not _member(z, "Synonym.tsv"):
        n = 0
        try:
            for n, r in enumerate(_rows(z, usage), 1):
                if any(v for k, v in r.items() if k.lower().replace("_", "") == "parentid"):
                    return False
                if (r.get("status") or "").strip().lower() != "bare name":
                    return False
        except (UnicodeDecodeError, csv.Error):
            # not ours to read (NZ EPA 313481 is Latin-1): the checklist
            # reader decides, as before this branch existed
            return False
        return n > 0
    if not _member(z, "Name.tsv") or _member(z, "NameUsage.tsv") or _member(z, "Synonym.tsv"):
        return False
    taxon = _member(z, "Taxon.tsv")
    if not taxon:
        return True
    for i, r in enumerate(_rows(z, taxon)):
        if any(v for k, v in r.items() if k.lower().replace("_", "") == "parentid"):
            return False
        if i >= 5000:
            break
    return True


_INITIALS = re.compile(r"\b(?:[A-Z][a-z]{0,2}\.\s*)+(?=\S)")


def zoological_authorship(raw, year):
    """Sherborn's "J. C. Fabricius" + 1798 -> "Fabricius, 1798", the form our
    zoological species carry. Initials go ("G. R. Gray" -> "Gray", "W. de
    Haan" -> "de Haan"), "in" stays ("Franklin in Gray, 1848"). No
    parentheses: a matched binomial is the combination as first published.
    Without a four-digit year there is nothing to fill, so ""."""
    year = (year or "").strip()[:4]
    if not raw or not year.isdigit():
        return ""
    who = " in ".join(_INITIALS.sub("", part).strip() for part in raw.split(" in "))
    return f"{' '.join(who.split())}, {year}" if who else ""


def load_index(archive, code=""):
    """name id -> (canonical lower, authorship, year, status); relations.

    The names are in Name.tsv, or NameUsage.tsv for a bare-name index
    (Index Animalium), which has no rank: a binomial is a species there."""
    z = zipfile.ZipFile(archive)
    names = {}
    table = _member(z, "Name.tsv") or _member(z, "NameUsage.tsv")
    zoo = AUTHOR_CODE.get(code) == "zoo"
    for r in _rows(z, table):
        rank = (r.get("rank") or "").lower()
        if rank and rank not in SPECIES_RANKS:
            continue
        nm = " ".join((r.get("scientificName") or "").split())
        if len(nm.split()) < 2 or (not rank and len(nm.split()) != 2):
            continue
        au = (r.get("authorship") or "").strip()
        yr = (r.get("publishedInYear") or "").strip()
        if zoo:
            au = zoological_authorship(au, yr)
        names[r["ID"]] = (nm.lower(), au, yr, r.get("link") or "")
    rel = []
    m = _member(z, "NameRelation.tsv")
    if m:
        for r in _rows(z, m):
            rel.append((r.get("nameID"), r.get("relatedNameID"), r.get("type")))
    # A checklist-shaped source (Species Fungorum Plus): its Synonym table
    # links a synonym's name to its accepted taxon, whose name is the pair.
    syn, tax = _member(z, "Synonym.tsv"), _member(z, "Taxon.tsv")
    if syn and tax:
        taxon_name = {r.get("ID"): r.get("nameID") for r in _rows(z, tax)}
        for r in _rows(z, syn):
            acc = taxon_name.get(r.get("taxonID"))
            if acc and r.get("nameID") and acc != r.get("nameID"):
                rel.append((r.get("nameID"), acc, "SYNONYM"))
    return names, rel


def held(kingdom):
    """canonical lower -> [(file path, node id, authorship, year, sourceIds)]."""
    out = collections.defaultdict(list)
    for fam in iter_family_files(kingdom):
        doc = fam.load()
        for parent, sp in iter_species_with_parent(doc):
            if sp.get("rank") != "SPECIES":
                continue
            genus = (parent.get("name") or "") if parent and parent.get("rank") == "GENUS" else ""
            canon, inline = canonicalize((sp.get("name") or "").strip(), genus, "SPECIES")
            if not canon:
                continue
            auth = (sp.get("authorship") or "").strip() or inline
            out[canon.lower()].append((os.path.relpath(fam.path, ROOT),
                                       sp.get("id"), auth, sp.get("yearPublished"),
                                       sorted(sp.get("sourceIds") or {})))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("work_slug")
    ap.add_argument("--code", default="", choices=[""] + sorted(KINGDOMS_FOR),
                    help="default: the archive's metadata alias, when it is one we map")
    ap.add_argument("--source-key", default="",
                    help="sourceIds key; default the work slug (checklistbank-2006)")
    ap.add_argument("--apply", action="store_true", help="write the work files")
    args = ap.parse_args()
    source_key = args.source_key or args.work_slug
    if not args.code:
        try:
            import colChecklist
            alias = (colChecklist.metadata(args.archive) or {}).get("alias") or ""
        except Exception:
            alias = ""
        if alias not in KINGDOMS_FOR:
            print(f"  no kingdom mapping for names index {alias or '(no alias)'!r}: add it to "
                  f"KINGDOMS_FOR (which of our kingdoms its code speaks for), or pass --code")
            return 4
        args.code = alias

    print(f"  reading {args.archive}", flush=True)
    names, rel = load_index(args.archive, args.code)
    by_name = collections.defaultdict(list)
    for nid, (nm, au, yr, link) in names.items():
        by_name[nm].append((nid, au, yr))
    print(f"    {len(names):,} species names, {len(rel):,} relations", flush=True)

    try:
        import authorNames
        idx = authorNames.load(code=AUTHOR_CODE.get(args.code))
        same_person = lambda a, b: authorNames.same_person(a, b, idx)  # noqa: E731
    except Exception as e:
        print(f"    author index unavailable ({e}); comparing strings only")
        same_person = None

    work = os.path.join(sources.ROOT, "work", args.work_slug)
    stat = collections.Counter()
    fills, conflicts, compare = [], [], []
    ours_all = {}
    for kingdom in KINGDOMS_FOR[args.code]:
        if not writerKingdoms.may_write(kingdom):
            print(f"  {kingdom}: not this machine's kingdom (SN_WRITE_KINGDOMS), skipped")
            continue
        print(f"  reading our {kingdom} family files", flush=True)
        ours = held(kingdom)
        ours_all[kingdom] = ours
        for canon, nodes in ours.items():
            cands = by_name.get(canon)
            if not cands:
                stat["not in the index"] += len(nodes)
                continue
            auths = {au for _, au, _ in cands if au}
            for path, nid, auth, year, sids in nodes:
                stat["held in the index"] += 1
                if not auth:
                    if len(auths) != 1:
                        stat["no authorship, index ambiguous (homonyms)"] += 1
                        continue
                    au = next(iter(auths))
                    ids = sorted({i for i, a, _ in cands if a == au})
                    yrs = sorted({y for i, a, y in cands if a == au and y})
                    rec = {"kingdom": kingdom, "file": path, "id": nid, "name": canon,
                           "set": {"authorship": au}, "source": source_key}
                    if len(yrs) == 1 and not year:
                        rec["set"]["yearPublished"] = int(yrs[0]) if yrs[0].isdigit() else yrs[0]
                    if len(ids) == 1 and len(nodes) == 1 and source_key not in sids:
                        rec["sourceId"] = ids[0]
                    fills.append(rec)
                    stat["authorship filled"] += 1
                elif len(auths) == 1:
                    compare.append((kingdom, path, nid, canon, auth, next(iter(auths))))
    if compare:
        print(f"  comparing {len(compare):,} authorships", flush=True)
        parsed = taxamatch.parse_authorships(sorted({x for c in compare for x in c[4:]}))
        for kingdom, path, nid, canon, a, b in compare:
            if a.replace(" ", "") == b.replace(" ", ""):
                stat["authorship agrees (same string)"] += 1
                continue
            same = taxamatch.same_authorship(a, b, parsed, same_person)
            if same:
                stat["authorship agrees (same authors, other form)"] += 1
            elif same is None:
                stat["authorship not comparable"] += 1
            else:
                stat["authorship conflicts"] += 1
                conflicts.append({"kingdom": kingdom, "file": path, "id": nid, "name": canon,
                                  "ours": a, "source": source_key, "theirs": b})

    pairs, homonyms = [], []
    for a, b, t in rel:
        na, nb = names.get(a), names.get(b)
        if not na:
            continue
        for kingdom, ours in ours_all.items():
            if t == "LATER_HOMONYM" and na[0] in ours:
                homonyms.append({"kingdom": kingdom, "name": na[0], "authorship": na[1],
                                 "sourceId": a, "earlierHomonym": (nb or ("", ""))[0] + " " + (nb or ("", ""))[1],
                                 "nodes": [n[1] for n in ours[na[0]]], "source": source_key})
            elif t in PAIR_RELATIONS and nb and na[0] != nb[0] and na[0] in ours and nb[0] in ours:
                pairs.append({"kingdom": kingdom, "relation": t,
                              "name": na[0], "nameAuthorship": na[1], "nodes": [n[1] for n in ours[na[0]]],
                              "related": nb[0], "relatedAuthorship": nb[1],
                              "relatedNodes": [n[1] for n in ours[nb[0]]], "source": source_key})
    stat["basionym/replacement pairs both held"] = len(pairs)
    stat["later homonyms held"] = len({h["name"] for h in homonyms})

    agree = (stat["authorship agrees (same string)"]
             + stat["authorship agrees (same authors, other form)"])
    compared = agree + stat["authorship conflicts"]
    rate = agree / compared if compared else 0.0
    if compared < MIN_COMPARED:
        verdict = f"review-only: {compared:,} authorships compared, too few to judge (< {MIN_COMPARED})"
    elif rate < MIN_AGREEMENT:
        verdict = (f"review-only: agrees with our authorship on {rate:.1%} of {compared:,} "
                   f"shared names (< {MIN_AGREEMENT:.0%})")
    else:
        verdict = f"fill: agrees on {rate:.1%} of {compared:,} shared names"
    review_fills = []
    if verdict.startswith("review-only"):
        review_fills, fills = fills, []

    for k, v in stat.most_common():
        print(f"  {v:>10,}  {k}")
    print(f"\n  verdict: {verdict}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write the work files)")
        return 0
    os.makedirs(work, exist_ok=True)
    for fn, rows in (("enrich.jsonl", fills), ("review-fills.jsonl", review_fills),
                     ("review-authorship.jsonl", conflicts),
                     ("review-basionym-pairs.jsonl", pairs),
                     ("review-later-homonyms.jsonl", homonyms)):
        with open(os.path.join(work, fn), "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(work, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump({"archive": args.archive, "code": args.code, "source": source_key,
                   "counts": dict(stat), "agreement": round(rate, 4),
                   "verdict": verdict}, fh, indent=1)
        fh.write("\n")
    print(f"\n  wrote {work}/: enrich.jsonl ({len(fills):,}), review files, summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
