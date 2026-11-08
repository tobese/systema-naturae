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
pure function of the tree and the archive.

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
from tree import ROOT, iter_family_files, kingdom_names  # noqa: E402

DATASET = "checklistbank-316441"
ARCHIVE = os.path.join(sources.ROOT, "archives", DATASET, "archive.zip")
WORK = os.path.join(sources.ROOT, "work", "citations-" + DATASET)
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


def tree_species():
    """(kingdom, species id, [COL ids]) for every species that has a COL id."""
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
                        ids = col_ids(sp)
                        if ids:
                            yield kingdom, sp["id"], ids


def extract():
    """NameUsage.tsv and Reference.tsv out of the archive, once."""
    os.makedirs(WORK, exist_ok=True)
    for member in ("NameUsage.tsv", "Reference.tsv"):
        dst = os.path.join(WORK, member)
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(ARCHIVE):
            continue
        print(f"  extracting {member} from {ARCHIVE}", flush=True)
        with open(dst + ".part", "wb") as fh:
            subprocess.run(["unzip", "-p", ARCHIVE, member], stdout=fh, check=True)
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    import duckdb
    extract()
    con = duckdb.connect()
    opts = "delim='\\t', header=true, quote='', escape='', all_varchar=true, ignore_errors=true"
    con.execute(f"""CREATE TABLE nu AS SELECT "col:ID" AS id, "col:nameReferenceID" AS ref,
                    "col:namePublishedInPage" AS page, "col:namePublishedInPageLink" AS pagelink
                    FROM read_csv('{os.path.join(WORK, "NameUsage.tsv")}', {opts})
                    WHERE "col:nameReferenceID" IS NOT NULL AND "col:nameReferenceID" <> ''""")

    print("  reading the tree's species", flush=True)
    rows, held = [], collections.Counter()
    for kingdom, sid, ids in tree_species():
        held[kingdom] += 1
        for rank, cid in enumerate(ids):
            rows.append((kingdom, sid, cid, rank))
    con.execute("CREATE TABLE sp (kingdom VARCHAR, sid VARCHAR, cid VARCHAR, rk INTEGER)")
    con.executemany("INSERT INTO sp VALUES (?, ?, ?, ?)", rows)
    del rows

    links = con.execute("""SELECT kingdom, sid, ref, page, pagelink FROM (
                             SELECT sp.kingdom, sp.sid, nu.ref, nu.page, nu.pagelink,
                                    row_number() OVER (PARTITION BY sp.kingdom, sp.sid ORDER BY sp.rk) AS n
                             FROM sp JOIN nu ON nu.id = sp.cid) WHERE n = 1""").fetchall()
    used = sorted({r[2] for r in links})
    con.execute("CREATE TABLE used (ref VARCHAR)")
    con.executemany("INSERT INTO used VALUES (?)", [(r,) for r in used])
    refs = con.execute(f"""SELECT r."col:ID", r."col:citation", r."col:doi", r."col:link",
                                  r."col:issued", r."col:sourceID"
                           FROM read_csv('{os.path.join(WORK, "Reference.tsv")}', {opts}) r
                           JOIN used u ON u.ref = r."col:ID" """).fetchall()

    have_ref = {r[0] for r in refs if r[1]}
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
    references = collections.defaultdict(dict)
    for rid, citation, doi, link, issued, via in refs:
        if not citation:
            continue
        rec = {"citation": citation}
        # COL's `issued` is sometimes page text from IPNI ("-42, fig. 12");
        # only a plain year is kept.
        year = issued if issued and re.fullmatch(r"1[5-9]\d\d|20\d\d", issued) else None
        for k, v in (("doi", doi), ("link", link), ("year", year),
                     ("via", f"checklistbank-{via}" if via else None)):
            if v:
                rec[k] = v
        references[shard("col:" + rid)]["col:" + rid] = rec

    for kingdom in kingdom_names():
        n, h = per_kingdom[kingdom], held[kingdom]
        print(f"  {kingdom:10} {n:>10,} of {h:>10,} species with a COL id get a reference"
              f" ({100 * n / max(1, h):.0f}%)")
    print(f"  {sum(per_kingdom.values()):,} species links, "
          f"{sum(len(v) for v in references.values()):,} references")
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
