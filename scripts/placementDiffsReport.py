#!/usr/bin/env python3
"""Summarise a --diff-log written by importColChecklist.py.

The log is one JSON line per species the source places in a different family
than the tree does (`data/gbif-placement-diffs.jsonl` for the GBIF backbone).
34k species is more than anyone reads one line at a time, so this groups them
by (our family -> source family) and prints the pairs worth looking at first.

    python3 scripts/placementDiffsReport.py                       # top pairs
    python3 scripts/placementDiffsReport.py --kingdom animalia
    python3 scripts/placementDiffsReport.py --family Polypodiaceae
    python3 scripts/placementDiffsReport.py --markdown docs/gbif-placement-diffs.md

A pair is a question, not a verdict: either our placement came from a
specialist source that disagrees with the aggregate (the usual case -- COL
splits Polypodiaceae, GBIF keeps more in Dryopteridaceae), or the aggregate is
right and our node is stale. Reviewing a pair means checking the species'
`sourceIds`/`sourcedFrom`, not automatically siding with either.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def report(rows, kingdom="", family="", limit=0):
    if kingdom:
        rows = [r for r in rows if r.get("kingdom") == kingdom]
    if family:
        f = family.lower()
        rows = [r for r in rows
                if f in (r.get("ourFamily") or "").lower()
                or f in (r.get("ourFamilyName") or "").lower()
                or f in (r.get("sourceFamily") or "").lower()]
    pairs = collections.defaultdict(list)
    for r in rows:
        key = (r.get("ourFamilyName") or r.get("ourFamily") or "?",
               r.get("sourceFamily") or "?", r.get("kingdom") or "?")
        pairs[key].append(r)
    ordered = sorted(pairs.items(), key=lambda kv: -len(kv[1]))
    if limit:
        ordered = ordered[:limit]
    return rows, ordered


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", default="data/gbif-placement-diffs.jsonl")
    ap.add_argument("--kingdom", default="")
    ap.add_argument("--family", default="",
                    help="substring match on either family name or slug")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-count", type=int, default=1)
    ap.add_argument("--markdown", default="",
                    help="write the full grouped table here instead of stdout")
    args = ap.parse_args()
    if not os.path.exists(args.log):
        sys.exit(f"FATAL: {args.log} not found -- run importColChecklist.py "
                 f"with --diff-log {args.log}")
    rows, ordered = report(load(args.log), args.kingdom, args.family, args.limit)
    ordered = [(k, v) for k, v in ordered if len(v) >= args.min_count]

    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write("# Placement diffs against the GBIF backbone\n\n")
            fh.write(f"{len(rows):,} species, {len(ordered):,} "
                     f"(our family -> GBIF family) pairs. "
                     f"Source: `data/gbif-placement-diffs.jsonl`.\n\n")
            fh.write("| species | our family | GBIF family | kingdom | example |\n")
            fh.write("|---:|---|---|---|---|\n")
            for (ours, theirs, k), group in ordered:
                ex = group[0].get("name") or ""
                fh.write(f"| {len(group):,} | {ours} | {theirs} | {k} | "
                         f"*{ex}* |\n")
        print(f"  wrote {args.markdown}: {len(rows):,} species in "
              f"{len(ordered):,} pairs")
        return 0

    by_k = collections.Counter(r.get("kingdom") or "?" for r in rows)
    print(f"  species with a placement diff: {len(rows):,}")
    for k, n in by_k.most_common():
        print(f"      {k:12s} {n:>7,}")
    print(f"  family pairs: {len(ordered):,}\n")
    for (ours, theirs, k), group in ordered:
        ex = group[0].get("name") or ""
        print(f"  {len(group):>6,}  [{k:9s}] {ours} -> {theirs}   e.g. {ex}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
