#!/usr/bin/env python3
"""Is portal/data/name-parse-index.jsonl still telling the truth?

The index is a snapshot of every species name in the tree, taken at a moment, and
it is gitignored -- so nothing in CI notices when it drifts. It drifts on every
import, and it now drifts in whichever direction the imports moved, which is the
part that matters:

- On Craneflies (ChecklistBank 1005) it scored 15,563 species as new when 15,191
  were already held, because it predates the Stage 2 import.
- On ILDIS (1015) it scored 13,347 of 16,371 species as already held when the
  tree holds 64, so an importer trusting it would have skipped 13,283 species
  without a word.

Both were caught by counting names against the family files, not by a test
failing, which is the argument for this check existing at all.

So: report, do not fix. Rebuilding is a network job, not a local reindex --
`parseAllNames.py` POSTs every name to GBIF's parser at roughly 113 names per
second on one connection, about 3.2 hours for 1.3M names and more like six for
the 2.4M the tree holds now. Sharding gets it down to tens of minutes
(`--shard 0/6 --workers 6`) but it is not something a build can do implicitly.

Until it is rebuilt, importers must not treat it as an oracle. The rule that
survives both failures above is: stage everything and let `merge_family` decide,
because it reads the file it is about to write rather than a cached summary of
every file.

    python3 scripts/nameIndexStatus.py          # report
    python3 scripts/nameIndexStatus.py --count  # also count index lines
"""
import argparse
import glob
import os
import sys
import time

INDEX = "portal/data/name-parse-index.jsonl"
# Everything that reads the index, so a stale one is attributable.
CONSUMERS = (
    "scripts/canonicalNames.py  (every importer that asks 'do we hold this name')",
    "scripts/importColStage2.py",
    "scripts/importColChecklist.py  (no longer -- see the docstring)",
    "scripts/importColBreadth.py",
    "portal/scripts/enrichFromWikipedia.ts",
    "portal/scripts/fetchSpeciesFromApi.ts",
)


def newest_family_file():
    newest, newest_ts, count = None, 0.0, 0
    for pat in ("taxonomy/*/**/src/data/*.json",):
        for f in glob.iglob(pat, recursive=True):
            try:
                ts = os.path.getmtime(f)
            except OSError:
                continue
            count += 1
            if ts > newest_ts:
                newest, newest_ts = f, ts
    return newest, newest_ts, count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", action="store_true",
                    help="count index lines (reads the whole file)")
    args = ap.parse_args()

    if not os.path.exists(INDEX):
        print(f"  MISSING: {INDEX}")
        print("  Nothing depends on it yet, but every importer that asks "
              "'do we hold this name?' needs it.")
        print("  Build:  make name-index")
        return 1

    idx_ts = os.path.getmtime(INDEX)
    idx_mb = os.path.getsize(INDEX) / 1e6
    newest, newest_ts, files = newest_family_file()
    newer = sum(1 for f in glob.iglob("taxonomy/*/**/src/data/*.json",
                                      recursive=True)
                if os.path.getmtime(f) > idx_ts)

    print(f"  index:   {INDEX}")
    print(f"           {idx_mb:,.0f} MB, written {time.strftime('%Y-%m-%d %H:%M', time.localtime(idx_ts))}")
    print(f"  tree:    {files:,} family files, newest {time.strftime('%Y-%m-%d %H:%M', time.localtime(newest_ts))}")
    print(f"           {newest}")
    if args.count:
        with open(INDEX, encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh)
        print(f"           index holds {n:,} names")

    age_h = (time.time() - idx_ts) / 3600
    if newer:
        print(f"\n  STALE: {newer:,} family files are newer than the index "
              f"(index is {age_h:.1f} h old).")
        print("  Rebuild:  make name-index ARGS='--workers 6'")
        print("  This is not cosmetic. It has been wrong in both directions:")
        print("    Craneflies  15,563 species scored new, 15,191 already held")
        print("    ILDIS       13,347 of 16,371 scored held, tree holds 64")
        print("  Until it is rebuilt, importers must not treat it as an oracle.")
        print("\n  reads it:")
        for c in CONSUMERS:
            print(f"    {c}")
        return 1

    print("\n  current: no family file is newer than the index.")
    return 0


if __name__ == "__main__":
    sys.exit(main())