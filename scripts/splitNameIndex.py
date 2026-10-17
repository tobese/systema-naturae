#!/usr/bin/env python3
"""Migrate portal/data/name-parse-index.jsonl into per-family sidecars.

Reads the monolith index, walks every family file to learn which names belong to
which family, and writes each family's parse records to its own sidecar plus a
manifest. Does NOT re-parse anything -- just re-attributes existing records.

A name that appears in multiple families (homonym) is written to each family's
sidecar, since GBIF's parse verdict applies to the name string regardless of
which family holds it.

Usage:
    python3 scripts/splitNameIndex.py        # dry run
    python3 scripts/splitNameIndex.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import iter_family_files  # noqa: E402
import nameIndexCache  # noqa: E402

MONOLITH = os.path.join("portal", "data", "name-parse-index.jsonl")


def load_monolith_by_key() -> dict:
    """(name, rank) -> list of parse records, from the monolith."""
    out = {}
    if not os.path.exists(MONOLITH):
        return out
    with open(MONOLITH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            n = (rec.get("n") or "").strip()
            r = rec.get("ourRank")
            if not n or not r:
                continue
            out.setdefault((n, r), []).append(rec)
    return out


def family_names(fam_path: str) -> set:
    """All distinct (name, rank) pairs in one family document."""
    import json as _json
    pairs = set()
    try:
        with open(fam_path, encoding="utf-8") as fh:
            doc = _json.load(fh)
    except Exception:
        return pairs
    stack = [doc]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        name = (node.get("name") or "").strip()
        rank = node.get("rank")
        if name and rank:
            pairs.add((name, rank))
        stack.extend(node.get("children") or [])
        stack.extend(node.get("speciesList") or [])
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write sidecars and manifest (dry run otherwise)")
    args = ap.parse_args()

    monolith = load_monolith_by_key()
    print(f"monolith records: {sum(len(v) for v in monolith.values()):,}"
          f" across {len(monolith):,} distinct (name, rank) pairs")

    manifest = nameIndexCache.load_manifest() if args.apply else {}
    families = list(iter_family_files())
    total_written = 0
    total_rows = 0
    missing = 0

    for fam in families:
        slug = fam.slug
        pairs = family_names(fam.path)
        records = []
        for name, rank in sorted(pairs):
            recs = monolith.get((name, rank), [])
            if not recs:
                missing += 1
                continue
            # Homonym in multiple families -> same record duplicated per sidecar
            records.extend(recs)

        if records:
            total_rows += len(records)
            total_written += 1
            if args.apply:
                st = os.stat(fam.path)
                nameIndexCache.save_family_index(
                    slug, records, st.st_mtime_ns, st.st_size, manifest)

    print(f"families with sidecars: {total_written:,} / {len(families):,}")
    print(f"rows written: {total_rows:,}")
    print(f"(name, rank) pairs with no monolith record: {missing:,}")

    if args.apply:
        nameIndexCache.save_manifest(manifest)
        print(f"  wrote {nameIndexCache.MANIFEST_PATH}")
        print(f"  sidecars in {nameIndexCache.INDEX_DIR}")
    else:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
