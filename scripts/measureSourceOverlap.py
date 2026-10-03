#!/usr/bin/env python3
"""Measure a DwC checklist against the current tree before importing it.

Exists because I got this wrong twice. Both times the bug was the same: testing
whether a *source* name was present by looking it up in `name-parse-index.jsonl`,
which is keyed by the names **we** store -- including the 156,392 that carry an
authorship inside `name` -- while the sources key on bare binomials. Every source
name therefore missed, and Mammal Species of the World came back "100% new" when
3,762 of our 7,900 mammal species are in it. The converse error, checking our
canonical forms against a source set, is the one that works.

So: build the set of names we actually hold, from the family data, and compare
both ways. Then report not just a count but *where* each already-present species
lives, because the failure that matters is a species landing in a second family
rather than merely being recognised.

The tree-wide duplicate check that motivated this found 374 animalia species in
more than one order and 32 more shared across kingdoms -- all pre-existing, all
real homonyms or genera that get moved between families, none from the recent
imports. This script is what keeps that number from growing.

Usage:
    python3 scripts/measureSourceOverlap.py --src <dir-with-taxon.txt>
    python3 scripts/measureSourceOverlap.py --src <dir> --kingdom animalia
"""
import argparse
import collections
import csv
import glob
import json
import os
import sys

ACCEPTED = {"valid", "accepted"}
EXCLUDE = ("node_modules", "unified-taxonomy")


def tree_species(kingdom: str | None):
    """species name -> {(kingdom, order, family)} across the tree."""
    out = collections.defaultdict(set)
    pattern = f"taxonomy/{kingdom}/**/src/data/*.json" if kingdom \
        else "taxonomy/*/**/src/data/*.json"
    files = [f for f in glob.glob(pattern, recursive=True)
             if not any(e in f for e in EXCLUDE)]
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        parts = f.split(os.sep)
        king, order, fam = parts[1], parts[5] if len(parts) > 5 else "?", d.get("name")
        stack = [d]
        while stack:
            n = stack.pop()
            if n.get("rank") == "SPECIES" and n.get("name"):
                out[n["name"]].add((king, order, fam))
            stack.extend(n.get("children") or [])
            stack.extend(n.get("speciesList") or [])
    return out, len(files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory holding taxon.txt")
    ap.add_argument("--kingdom", default=None)
    ap.add_argument("--rank-col", default="taxonRank")
    ap.add_argument("--status-col", default="taxonomicStatus")
    ap.add_argument("--name-col", default="scientificName")
    args = ap.parse_args()

    path = args.src if args.src.endswith("taxon.txt") else os.path.join(args.src, "taxon.txt")
    if not os.path.exists(path):
        sys.exit(f"FATAL: {path} not found")
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8",
                                     errors="replace"), delimiter="\t"))
    if not rows:
        sys.exit(f"FATAL: {path} is empty -- a truncated download looks exactly like "
                 f"an empty source, so verify the archive before trusting this")

    tree, nfiles = tree_species(args.kingdom)
    print(f"tree: {nfiles:,} family files, {len(tree):,} species names"
          f"{f' ({args.kingdom})' if args.kingdom else ''}")

    species, families = set(), set()
    rejected = collections.Counter()
    for r in rows:
        rank = (r.get(args.rank_col) or "").strip().lower()
        status = (r.get(args.status_col) or "").strip().lower()
        if rank == "family":
            if r.get(args.name_col):
                families.add(r[args.name_col])
        if rank != "species":
            continue
        if status and status not in ACCEPTED:
            rejected[status] += 1
            continue
        if r.get(args.name_col):
            species.add(r[args.name_col])

    present = {s for s in species if s in tree}
    new = species - present
    print(f"source rows:        {len(rows):,}")
    print(f"families:           {len(families):,}")
    print(f"species (accepted): {len(species):,}")
    if rejected:
        print(f"  rejected by status: {dict(rejected.most_common(5))}")
    pct = len(present) / max(len(species), 1) * 100
    print(f"already in tree:    {len(present):,}  ({pct:.1f}%)")
    print(f"NEW to us:          {len(new):,}")

    # The number that matters: where an already-present species would land.
    same_family = 0
    collisions = []
    for s in present:
        homes = tree[s]
        if len(homes) > 1:
            collisions.append((s, sorted(homes)))
        else:
            same_family += 1
    print(f"  already present, single home: {same_family:,}")
    if collisions:
        print(f"  ALREADY IN MULTIPLE PLACES:  {len(collisions):,}"
              f"  <- importing will not fix these; expect them to double up")
        for s, homes in sorted(collisions)[:10]:
            print(f"     {s[:40]:<42}{homes}")
    if new:
        print("  sample of new species:")
        for s in sorted(new)[:6]:
            print(f"     {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
