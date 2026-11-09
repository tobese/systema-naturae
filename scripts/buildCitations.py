#!/usr/bin/env python3
"""Citations track, step 6: where each species name was first published.

Joins the COL ids our species already carry (`sourceIds.col`,
`sourceIds.checklistbank-316441`) to COL XR's NameUsage `nameReferenceID`
and `namePublishedInPage`, and that to COL's Reference table. Nothing is
inferred: a species gets a reference only where COL states one for that
exact COL id, and the reference text is COL's `citation` verbatim.

Sidecars keyed by species id, as docs/citations-and-authors-plan.md step 3
lays out for authors -- species move between families, ids do not:

    data/citations/species/<kingdom>/<xx>.json
        { speciesId: {"r": "col:<referenceID>", "p": page, "pl": pageLink} }
    data/citations/references/<xx>.json
        { "col:<referenceID>": {"citation", "doi", "link", "year", "via"} }

`xx` is the first two hex digits of the md5 of the key, so no file grows
large. `via` is the dataset COL took the reference from (its sourceID).
Only references some species points at are written.

A species with several COL ids takes the first (sorted) that has a
reference. Re-running rebuilds every sidecar from scratch: the files are a
pure function of the tree and the archives.

A species COL leaves without a reference falls back to WoRMS
(checklistbank-2011), joined on the WoRMS taxonID it carries in
`sourceIds.checklistbank-2011`. WoRMS states `namePublishedIn` as text on
the name itself, without a reference id for most rows, so a WoRMS reference
is keyed `worms:<md5 of the text>[:12]`: the same text is one reference.
`namePublishedInID`, when present, is a DOI URL and kept as `link`. The text
is WoRMS's verbatim, inline HTML (<em>, <i>) included.

A species with neither falls back to COL by name (2026-11-09): ~500k of our
species carry no COL id though COL XR holds the same name, most of them
imported from other sources and never merged with COL. The match is the
canonical name (buildSpeciesParquet.canonicalize) against COL's accepted
species of the same kingdom, taken only when exactly one accepted species
has that name; the link carries `"by": "name"` so it can be told apart.

    python3 scripts/buildCitations.py            # measure, write nothing
    python3 scripts/buildCitations.py --apply
"""
import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
from buildSpeciesParquet import canonicalize  # noqa: E402
from tree import ROOT, iter_family_files, kingdom_names  # noqa: E402

DATASET = "checklistbank-316441"
ARCHIVE = os.path.join(sources.ROOT, "archives", DATASET, "archive.zip")
WORK = os.path.join(sources.ROOT, "work", "citations-" + DATASET)
WORMS = "checklistbank-2011"
WORMS_ARCHIVE = os.path.join(sources.ROOT, "archives", WORMS, "archive.zip")
WORMS_WORK = os.path.join(sources.ROOT, "work", "citations-" + WORMS)
YEAR = re.compile(r"1[5-9]\d\d|20\d\d")
OUT = os.path.join(ROOT, "data", "citations")
COL_KEYS = ("col", DATASET)


def shard(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:2]


def col_ids(sp) -> list[str]:
    ids = set()
    for k in COL_KEYS:
        v = (sp.get("sourceIds") or {}).get(k)
        for x in (v if isinstance(v, list) else [v]):
            if x:
                ids.add(str(x))
    return sorted(ids)


def worms_id(sp):
    v = (sp.get("sourceIds") or {}).get(WORMS)
    v = v[0] if isinstance(v, list) and v else v
    return str(v) if v else None


def tree_species():
    """(kingdom, species id, [COL ids], WoRMS id, canonical name) for every
    species."""
    for kingdom in kingdom_names():
        for fam in iter_family_files(kingdom):
            with open(fam.path, encoding="utf-8") as fh:
                doc = json.load(fh)
            st = list(doc.get("children") or [])
            while st:
                n = st.pop()
                st.extend(n.get("children") or [])
                for sp in [n, *(n.get("speciesList") or [])]:
                    if sp.get("rank") == "SPECIES" and sp.get("id"):
                        name = sp.get("name") or ""
                        canon = canonicalize(name, name.split(" ")[0], "SPECIES")[0]
                        yield kingdom, sp["id"], col_ids(sp), worms_id(sp), canon


def extract(archive, work, members):
    """Members out of an archive, once per archive version."""
    os.makedirs(work, exist_ok=True)
    for member in members:
        dst = os.path.join(work, member)
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(archive):
            continue
        print(f"  extracting {member} from {archive}", flush=True)
        with open(dst + ".part", "wb") as fh:
            subprocess.run(["unzip", "-p", archive, member], stdout=fh, check=True)
        os.replace(dst + ".part", dst)


def write_shards(base: str, by_shard: dict) -> int:
    if os.path.isdir(base):
        shutil.rmtree(base)
    os.makedirs(base)
    for sh, entries in by_shard.items():
        with open(os.path.join(base, sh + ".json"), "w", encoding="utf-8") as fh:
            # One entry per line, so a changed reference is a one-line diff.
            fh.write("{\n")
            fh.write(",\n".join(json.dumps(k, ensure_ascii=False) + ": "
                                + json.dumps(entries[k], ensure_ascii=False, sort_keys=True)
                                for k in sorted(entries)))
            fh.write("\n}\n")
    return len(by_shard)


def load_col_refs(con, ref_ids, references, opts) -> set:
    """COL Reference rows for `ref_ids` into `references`; the ids that have
    citation text."""
    con.execute("CREATE OR REPLACE TABLE used (ref VARCHAR)")
    con.executemany("INSERT INTO used VALUES (?)", [(r,) for r in sorted(ref_ids)])
    have = set()
    for rid, citation, doi, link, issued, via in con.execute(f"""
            SELECT r."col:ID", r."col:citation", r."col:doi", r."col:link",
                   r."col:issued", r."col:sourceID"
            FROM read_csv('{os.path.join(WORK, "Reference.tsv")}', {opts}) r
            JOIN used u ON u.ref = r."col:ID" """).fetchall():
        if not citation:
            continue
        have.add(rid)
        rec = {"citation": citation}
        # COL's `issued` is sometimes page text from IPNI ("-42, fig. 12");
        # only a plain year is kept.
        year = issued if issued and YEAR.fullmatch(issued) else None
        for k, v in (("doi", doi), ("link", link), ("year", year),
                     ("via", f"checklistbank-{via}" if via else None)):
            if v:
                rec[k] = v
        references[shard("col:" + rid)]["col:" + rid] = rec
    return have


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    import duckdb
    extract(ARCHIVE, WORK, ("NameUsage.tsv", "Reference.tsv"))
    extract(WORMS_ARCHIVE, WORMS_WORK, ("taxon.txt",))
    con = duckdb.connect()
    opts = "delim='\\t', header=true, quote='', escape='', all_varchar=true, ignore_errors=true"
    con.execute(f"""CREATE TABLE nu AS SELECT "col:ID" AS id, "col:nameReferenceID" AS ref,
                    "col:namePublishedInPage" AS page, "col:namePublishedInPageLink" AS pagelink
                    FROM read_csv('{os.path.join(WORK, "NameUsage.tsv")}', {opts})
                    WHERE "col:nameReferenceID" IS NOT NULL AND "col:nameReferenceID" <> ''""")

    print("  reading the tree's species", flush=True)
    rows, wrows, names, held = [], [], [], collections.Counter()
    for kingdom, sid, ids, w, canon in tree_species():
        held[kingdom] += 1
        for rank, cid in enumerate(ids):
            rows.append((kingdom, sid, cid, rank))
        if w:
            wrows.append((kingdom, sid, w))
        names.append((kingdom, sid, canon))
    con.execute("CREATE TABLE sp (kingdom VARCHAR, sid VARCHAR, cid VARCHAR, rk INTEGER)")
    con.executemany("INSERT INTO sp VALUES (?, ?, ?, ?)", rows)
    del rows

    links = con.execute("""SELECT kingdom, sid, ref, page, pagelink FROM (
                             SELECT sp.kingdom, sp.sid, nu.ref, nu.page, nu.pagelink,
                                    row_number() OVER (PARTITION BY sp.kingdom, sp.sid ORDER BY sp.rk) AS n
                             FROM sp JOIN nu ON nu.id = sp.cid) WHERE n = 1""").fetchall()
    references = collections.defaultdict(dict)
    have_ref = load_col_refs(con, {r[2] for r in links}, references, opts)
    per_kingdom = collections.Counter()
    species = collections.defaultdict(lambda: collections.defaultdict(dict))
    for kingdom, sid, ref, page, pagelink in links:
        if ref not in have_ref:
            continue
        link = {"r": "col:" + ref}
        if page:
            link["p"] = page
        if pagelink:
            link["pl"] = pagelink
        species[kingdom][shard(sid)][sid] = link
        per_kingdom[kingdom] += 1

    # WoRMS, for the species COL left without one.
    con.execute("CREATE TABLE ws (kingdom VARCHAR, sid VARCHAR, w VARCHAR)")
    con.executemany("INSERT INTO ws VALUES (?, ?, ?)",
                    [r for r in wrows if r[1] not in species.get(r[0], {}).get(shard(r[1]), ())])
    del wrows
    wopts = ("delim='\\t', header=true, quote='\"', escape='\"', strict_mode=false, "
             "all_varchar=true, ignore_errors=true")
    per_worms = collections.Counter()
    for kingdom, sid, text, pid, year in con.execute(f"""
            SELECT ws.kingdom, ws.sid, t.namePublishedIn, t.namePublishedInID,
                   t.namePublishedInYear
            FROM ws JOIN read_csv('{os.path.join(WORMS_WORK, "taxon.txt")}', {wopts}) t
              ON t.taxonID = ws.w
            WHERE t.namePublishedIn IS NOT NULL AND trim(t.namePublishedIn) <> ''""").fetchall():
        text = text.strip()
        key = "worms:" + hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        species[kingdom][shard(sid)][sid] = {"r": key}
        per_worms[kingdom] += 1
        rec = references[shard(key)].setdefault(key, {"citation": text, "via": WORMS})
        if year and YEAR.fullmatch(year):
            rec.setdefault("year", year)
        if pid and pid.startswith("http"):
            rec.setdefault("link", pid)

    # COL by name, for the species neither id reached.
    con.execute("CREATE TABLE sn (kingdom VARCHAR, sid VARCHAR, nm VARCHAR)")
    con.executemany("INSERT INTO sn VALUES (?, ?, ?)",
                    [r for r in names
                     if r[2] and r[1] not in species.get(r[0], {}).get(shard(r[1]), ())])
    del names
    byname = con.execute(f"""
        WITH acc AS (
            SELECT lower("col:kingdom") AS k, "col:scientificName" AS nm,
                   "col:nameReferenceID" AS ref, "col:namePublishedInPage" AS page,
                   "col:namePublishedInPageLink" AS pagelink
            FROM read_csv('{os.path.join(WORK, "NameUsage.tsv")}', {opts})
            WHERE "col:rank" = 'species' AND "col:status" = 'accepted'),
        one AS (
            SELECT k, nm, any_value(ref) AS ref, any_value(page) AS page,
                   any_value(pagelink) AS pagelink
            FROM acc GROUP BY k, nm HAVING count(*) = 1)
        SELECT sn.kingdom, sn.sid, one.ref, one.page, one.pagelink
        FROM sn JOIN one ON one.k = sn.kingdom AND one.nm = sn.nm
        WHERE one.ref IS NOT NULL AND one.ref <> ''""").fetchall()
    have_ref |= load_col_refs(con, {r[2] for r in byname} - have_ref, references, opts)
    per_name = collections.Counter()
    for kingdom, sid, ref, page, pagelink in byname:
        if ref not in have_ref:
            continue
        link = {"r": "col:" + ref, "by": "name"}
        if page:
            link["p"] = page
        if pagelink:
            link["pl"] = pagelink
        species[kingdom][shard(sid)][sid] = link
        per_name[kingdom] += 1

    for kingdom in kingdom_names():
        n, w, m, h = per_kingdom[kingdom], per_worms[kingdom], per_name[kingdom], held[kingdom]
        print(f"  {kingdom:10} {n:>9,} by COL id + {w:>7,} by WoRMS id + {m:>7,} by COL name"
              f" of {h:>9,} species ({100 * (n + w + m) / max(1, h):.0f}%)")
    print(f"  {sum(per_kingdom.values()) + sum(per_worms.values()) + sum(per_name.values()):,}"
          f" species links, {sum(len(v) for v in references.values()):,} references")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write data/citations)")
        return 0
    for kingdom, by_shard in species.items():
        write_shards(os.path.join(OUT, "species", kingdom), by_shard)
    write_shards(os.path.join(OUT, "references"), references)
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
