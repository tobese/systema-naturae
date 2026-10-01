#!/usr/bin/env python3
"""
Split the authority out of `name` into `authorship` and `yearPublished`.

Why
---
548,304 species names -- 45.5% of the tree -- carry the authority inside both
`name` and `id`:

    Smilax zeylanica L.   ->   SP_SMILAX_ZEYLANICA_L_

So the information was present and unusable. `fixMalformedIds.py` normalises the
*id* but deliberately leaves the trailing underscore alone, because the name
genuinely ends in an abbreviation. Nothing stored the authorship separately, so
a panel could not show "Linnaeus, 1758" without re-parsing the display string.

Two sources, and which one wins
-------------------------------
1. **`portal/data/name-parse-index.jsonl`** (GBIF's parser, 1,306,268 names) —
   562,378 authorship values, 198,613 years, all six kingdoms, free and keyless.
2. **`portal/data/mycobank-index.json`** — for fungi, MycoBank's own
   `Authors` column, which is the nomenclatural authority for fungal names.

MycoBank is checked first for fungi because it beats the parser: it carries
`scientificNameAuthorship` for 153,443 of our 157,690 undescribed fungal species,
where the parser only separates the string. GBIF cannot confirm fungal names at
all -- measured, `agaricomycetes` yields 0.37% and `MycoBank` and `COL` disagree
with GBIF on 98.7% of the names GBIF says are superseded
(`docs/reports/gbif-mycobank-disagreement.md`).

What is skipped, and why it matters
-----------------------------------
Nodes whose name does not denote a taxon are **not** written to. There are 4,551
of them (`Acorus spec Linnaeus, 1753`, `Salmo sp. BOLD:AAB3872`,
`UBA9949 sp10516u`), and `Acorus spec Linnaeus, 1753` does carry an authority --
but writing `authorship: "Linnaeus, 1753"` onto a node called `Acorus spec` is
noise that makes a placeholder look like a described species. The parser index
records the type, so skipping is a lookup rather than a guess. Skipped names are
listed in the report.

Never overwrites an existing value, so `--apply` is idempotent and a human edit
survives a re-run. Also never touches `name` or `id`: this only adds fields.

    python3 scripts/writeAuthorship.py             # dry run
    python3 scripts/writeAuthorship.py --apply

Read-only unless `--apply`.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import time

PARSE_INDEX = os.path.join("portal", "data", "name-parse-index.jsonl")
MYCOBANK_INDEX = os.path.join("portal", "data", "mycobank-index.json")

# Node names that do not denote a taxon. Same list as UNRESOLVED_TAXON in
# sanity_scan.py; an unresolved placeholder must not be given an authorship.
NON_TAXON = {"INFORMAL", "OTU", "NO_NAME", "PLACEHOLDER", "BLACKLISTED"}


def load_parse(path: str) -> tuple[dict, set]:
    """(name -> (authorship, year)), and the set of non-taxon names."""
    if not os.path.exists(path):
        sys.exit(f"FATAL: no parser index at {path}.\n"
                 f"       Build it with:  sh scripts/parseAllNamesSliced.sh")
    out: dict[str, tuple] = {}
    skip: set[str] = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("{"):
                continue
            d = json.loads(line)
            n = d.get("n") or ""
            if not n:
                continue
            if d.get("type") in NON_TAXON:
                skip.add(n)
                continue
            a, y = d.get("authorship"), d.get("year")
            if a or y:
                out[n] = (a, y)
    return out, skip


def load_mycobank(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        idx = json.load(fh)
    return {v["name"]: v.get("authors") for v in idx.values() if v.get("authors")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parse-index", default=PARSE_INDEX)
    ap.add_argument("--mycobank-index", default=MYCOBANK_INDEX)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    parsed, skip = load_parse(args.parse_index)
    print(f"parser index: {len(parsed):,} names with an authorship or year")
    print(f"             {len(skip):,} skipped as non-taxonomic")
    myc = load_mycobank(args.mycobank_index)
    print(f"mycobank:     {len(myc):,} names with an authorship")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from familyFiles import iter_family_files

    files = list(iter_family_files("."))
    tally: collections.Counter = collections.Counter()
    per_kingdom: collections.Counter = collections.Counter()
    written = 0
    touched = 0
    examples: list[tuple] = []
    started = time.time()

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        kingdom = os.path.relpath(path).replace(os.sep, "/").split("/")[1]
        changed = False
        stack = [doc]
        while stack:
            node = stack.pop()
            stack.extend(node.get("children") or [])
            stack.extend(node.get("speciesList") or [])
            name = (node.get("name") or "").strip()
            if not name:
                continue
            if name in skip:
                tally["skipped-non-taxon"] += 1
                continue

            # MycoBank first for fungi; the parser everywhere else.
            auth = myc.get(name) if kingdom == "fungi" else None
            year = None
            if not auth:
                got = parsed.get(name)
                auth, year = got if got else (None, None)

            if not auth and not year:
                tally["no-source"] += 1
                continue

            if node.get("authorship") or node.get("yearPublished"):
                tally["already-set"] += 1
                continue

            if auth:
                node["authorship"] = auth
                tally["authorship"] += 1
            if year:
                node["yearPublished"] = year
                tally["year"] += 1
            written += 1
            per_kingdom[kingdom] += 1
            changed = True
            if len(examples) < 8:
                examples.append((kingdom, name, auth, year))

        if changed:
            touched += 1
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"\n{'=' * 66}")
    print(f"would write:  {written:>9,} nodes")
    print(f"  authorship  {tally['authorship']:>9,}")
    print(f"  year        {tally['year']:>9,}")
    print(f"already set:  {tally['already-set']:>9,}  (never overwritten)")
    print(f"no source:    {tally['no-source']:>9,}")
    print(f"skipped:      {tally['skipped-non-taxon']:>9,}  (non-taxonomic names)")
    print(f"\nfiles: {touched:,}   ({time.time()-started:.0f}s)")
    print("by kingdom:")
    for k, v in per_kingdom.most_common():
        print(f"  {k:<12}{v:>8,}")

    print("\nexamples:")
    for k, n, a, y in examples:
        print(f"  {k:<10}{n[:34]:<36}{str(a)[:24]:<26}{y or ''}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    else:
        print(f"\n  wrote authorship to {written:,} nodes across {touched:,} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())