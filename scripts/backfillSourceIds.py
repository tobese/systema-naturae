#!/usr/bin/env python3
"""Stamp source-authority identifiers onto species nodes as `sourceIds`.

We keep no external identifiers at all today. A census of every field on 313,006
species nodes found exactly one identifier-shaped field, our own `id`, which is
derived from the name and deliberately non-canonical: 387,528 of the tree's
species ids carry no prefix at all, because prefixing them would collapse
`GENUS_SCHULZIA` (a nematode) onto `GENUS_SCHULZIA` (a flowering plant). So the
id cannot be joined to an authority, and neither can one species to another
without going through name heuristics.

Every source we import already hands us a stable identifier and we discard it:

    COL   dwc:taxonID          ITIS  ID (the TSN)
    WFO   wfo-0001302015        GBIF  taxonKey

`importColChecklist.py` now stamps `sourceIds` as it writes. This backfills the
two sources that are already on disk locally:

    --source gbif    portal/data/gbif-cache-*.json, 1,217,447 usageKeys cached
                     by tools/cache_gbif_keys.mjs. docs/import.md claims that
                     script "stamps usageKey onto per-species records"; it does
                     not, which is why this is a separate pass.
    --source archive <zip> [taxon.tsv|Name.tsv]   any DwCA already downloaded

Ids accumulate rather than replace, so a species that both GBIF and ITIS know
ends up with both.

The by-product is worth more than the field. **Two of our species carrying the
same GBIF usageKey is proof they are the same taxon** -- not a name match, not a
canonicalisation, an identifier issued by the authority. That is a stronger
duplicate signal than anything the tree has had, and this reports every
collision it finds.

    python3 scripts/backfillSourceIds.py --source gbif
    python3 scripts/backfillSourceIds.py --source gbif --apply
"""
import argparse
import collections
import csv
import glob
import io
import json
import os
import re
import sys
import zipfile

AUTH_TAIL = re.compile(r"\s+[A-Z][A-Za-z.\-']*(\s+ex\s+.*)?$")


def bare(name):
    """The binomial from a name that may carry its authority inline."""
    n = (name or "").strip()
    if " " in n:
        first, rest = n.split(" ", 1)
        if len(first) > 2 and first[0].isupper() and first[1:].islower():
            return first + " " + rest.split(" ")[0]
    return n


def load_gbif_cache():
    """canonicalName/scientificName (lower) -> usageKey."""
    idx = {}
    files = sorted(glob.glob("portal/data/gbif-cache-*.json"))
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for fam, v in (d.get("speciesByFamily") or {}).items():
            if not isinstance(v, dict):
                continue
            for sp in v.get("species") or []:
                key = sp.get("key")
                if not key:
                    continue
                for field in ("canonicalName", "scientificName"):
                    nm = (sp.get(field) or "").strip().lower()
                    if nm:
                        idx.setdefault(nm, key)
    return idx, len(files)


def load_archive_index(archive_path: str) -> dict:
    """scientificName (lower) -> the row's own id, from a zip's name/taxon
    table.

    Was `idx = {}` with nothing that ever populated it -- `--source
    archive` validated its `--archive` argument and then ran against an
    empty index, silently reporting every species "unmatched" rather than
    reading the file at all. Generic column-name matching rather than
    DwC-A's exact `taxonID`/`scientificName` so this also reads a
    nomenclatural-register export like Index Nominum Algarum's `name.tsv`
    (`ID`, `scientificName`, no `taxon.*` table at all -- see
    BACKLOG.md's "nomenclatural-register datasets" entry), not just a
    DwCA.
    """
    idx: dict[str, str] = {}
    name_candidates = ("scientificname", "name", "dwc:scientificname")
    id_candidates = ("id", "taxonid", "dwc:taxonid")
    with zipfile.ZipFile(archive_path) as z:
        members = [n for n in z.namelist()
                   if os.path.basename(n).lower() in
                   ("taxon.tsv", "taxon.txt", "name.tsv", "name.txt")]
        if not members:
            return idx
        with z.open(members[0]) as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t")
            fieldnames = reader.fieldnames or []
            name_col = next((c for c in fieldnames if c.lower() in name_candidates), None)
            id_col = next((c for c in fieldnames if c.lower() in id_candidates), None)
            if not name_col or not id_col:
                return idx
            for row in reader:
                nm = (row.get(name_col) or "").strip().lower()
                rid = (row.get(id_col) or "").strip()
                if nm and rid:
                    idx.setdefault(nm, rid)
    return idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="gbif", choices=("gbif", "archive"))
    ap.add_argument("--archive", default="", help="zip, for --source archive")
    ap.add_argument("--authority", default="", help="key under sourceIds")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.source == "gbif":
        idx, nfiles = load_gbif_cache()
        authority = args.authority or "gbif"
        print(f"  gbif cache: {len(idx):,} names across {nfiles} files")
    else:
        if not args.archive:
            sys.exit("  --source archive needs --archive")
        authority = args.authority or "archive"
        idx = load_archive_index(args.archive)
        print(f"  archive {args.archive}: {len(idx):,} names indexed")

    stamped = 0
    already = 0
    unmatched = collections.Counter()
    keys_seen = collections.defaultdict(list)
    files_touched = 0
    total = 0

    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        n_file = 0
        stack = list(d.get("children") or [])
        while stack:
            node = stack.pop()
            if node.get("rank") == "SPECIES":
                total += 1
                sid = node.get("sourceIds") or {}
                if sid.get(authority):
                    already += 1
                else:
                    nm = (node.get("name") or "").strip()
                    key = idx.get(nm.lower()) or idx.get(bare(nm).lower())
                    if key:
                        sid[authority] = key
                        node["sourceIds"] = sid
                        keys_seen[key].append(
                            (f, node.get("id"), nm))
                        n_file += 1
                    else:
                        unmatched[f.split("taxonomy/")[1].split("/")[0]] += 1
            stack.extend(node.get("children") or [])

        if n_file:
            stamped += n_file
            files_touched += 1
            if args.apply:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"  species: {total:,}")
    print(f"  stamped {authority}: {stamped:,}  (already had one: {already:,})")
    print(f"  files touched: {files_touched:,}")
    print(f"  unmatched by kingdom: {dict(unmatched.most_common(6))}")

    collisions = {k: v for k, v in keys_seen.items() if len(v) > 1}
    if collisions:
        print(f"\n  PROVEN DUPLICATES: {len(collisions):,} {authority} keys on "
              f"more than one of our species")
        for k, v in list(collisions.items())[:10]:
            print(f"    {authority} {k}:")
            for f, i, nm in v[:3]:
                print(f"       {nm!r}  id={i}  {f.split('taxonomy/')[-1]}")
    else:
        print(f"\n  no {authority} key appears on two of our species")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
