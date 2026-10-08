#!/usr/bin/env python3
"""Derive authorityIds from sourceIds where it is missing.

patchFamilyIds.py only writes authorityIds when it merges a match from
species_id_map.parquet. Species that already carried sourceIds from an earlier
backfillSourceIds.py run -- 214,239 of them, all gbif or worms -- were left
with sourceIds and no authorityIds, which is the field the app actually reads.

This closes that gap in one pass: authorityIds is a derived projection of
sourceIds, so build it whenever it is absent or stale.

    python3 scripts/fillAuthorityIds.py
    python3 scripts/fillAuthorityIds.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import iter_family_files, iter_species_with_parent, save_json


def build_authority_ids(source_ids: dict) -> str:
    parts = []
    for source in sorted(source_ids):
        ids = source_ids[source]
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        for id_val in sorted(set(str(i) for i in ids)):
            parts.append(f"{source}:{id_val}")
    return ",".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    patched = 0
    already = 0
    no_source = 0
    files = 0
    t0 = time.time()

    for fam in iter_family_files():
        files += 1
        doc = fam.load()
        changed = False
        for _parent, sp in iter_species_with_parent(doc):
            si = sp.get("sourceIds") or {}
            if not si:
                no_source += 1
                continue
            existing = sp.get("authorityIds") or ""
            desired = build_authority_ids(si)
            if existing == desired:
                already += 1
                continue
            sp["authorityIds"] = desired
            changed = True
            patched += 1

        if changed and not args.dry_run:
            save_json(fam.path, doc)

        if files % 1000 == 0:
            print(f"  {files:>6,} files  {patched:>9,} patched  {already:>9,} ok  {no_source:>9,} no sourceIds  {time.time() - t0:.0f}s")

    print(f"\n  {files:,} files processed in {time.time() - t0:.0f}s")
    print(f"  Patched: {patched:,}  Already correct: {already:,}  No sourceIds: {no_source:,}")
    if args.dry_run:
        print("  (dry run -- nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())