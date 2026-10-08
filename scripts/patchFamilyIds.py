#!/usr/bin/env python3
"""Apply consolidated species_id_map to family JSON files.

Reads species_id_map.parquet, walks all family files, and patches each
species with authorityIds built from the mapping.

    python3 scripts/patchFamilyIds.py
    python3 scripts/patchFamilyIds.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import KINGDOMS, ROOT, iter_family_files, iter_species_with_parent, save_json

PARQUET_PY = os.environ.get("PARQUET_PY", os.path.join(ROOT, ".venv-parquet", "bin", "python3"))
ID_MAP_PATH = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")


def load_id_map() -> dict:
    """Load species_id_map.parquet into {scientific_name: {source: [ids]}}."""
    try:
        import duckdb
    except ImportError:
        print("duckdb is not installed.")
        print("    python3 -m venv .venv-parquet && .venv-parquet/bin/pip install duckdb")
        sys.exit(2)

    con = duckdb.connect()
    rows = con.execute(
        "SELECT scientific_name, source, external_id FROM read_parquet(?)",
        (ID_MAP_PATH,),
    ).fetchall()
    con.close()

    mapping: dict[str, dict[str, list[str]]] = {}
    for name, source, ext_id in rows:
        name = name.strip()
        if name not in mapping:
            mapping[name] = {}
        mapping[name].setdefault(source, []).append(ext_id)
    return mapping


def build_authority_ids(info: dict[str, list[str]]) -> str:
    """Build authorityIds string from {source: [ids]} mapping."""
    parts = []
    for source, ids in sorted(info.items()):
        for id_val in sorted(set(ids)):
            parts.append(f"{source}:{id_val}")
    return ",".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(ID_MAP_PATH):
        print(f"Missing {ID_MAP_PATH}. Run scripts/buildIdMap.py first.")
        return 1

    print(f"Loading {os.path.relpath(ID_MAP_PATH, ROOT)}…")
    id_map = load_id_map()
    print(f"  {len(id_map):,} scientific names in ID map")

    patched = 0
    already = 0
    no_match = 0
    files = 0
    t0 = time.time()

    for fam in iter_family_files():
        files += 1
        doc = fam.load()
        changed = False
        for parent, sp in iter_species_with_parent(doc):
            name = (sp.get("name") or "").strip()
            if not name:
                continue
            existing = sp.get("sourceIds") or {}
            if existing:
                already += 1
                continue
            info = id_map.get(name)
            if not info:
                # Try canonical name only (strip authorship)
                canonical = name.split()[0] + " " + name.split()[1] if len(name.split()) >= 2 else name
                info = id_map.get(canonical)
            if info:
                sp["sourceIds"] = info
                sp["authorityIds"] = build_authority_ids(info)
                changed = True
                patched += 1
            else:
                no_match += 1

        if changed and not args.dry_run:
            save_json(fam.path, doc)

        if files % 1000 == 0:
            print(f"  {files:>6,} files  {patched:>9,} patched  {already:>9,} already  {no_match:>9,} no match  {time.time() - t0:.0f}s")

    print(f"\n  {files:,} files processed in {time.time() - t0:.0f}s")
    print(f"  Patched: {patched:,}  Already had: {already:,}  No match: {no_match:,}")
    if args.dry_run:
        print("  (dry run — nothing written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())