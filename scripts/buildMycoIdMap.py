#!/usr/bin/env python3
"""Build species_id_map from mycobank-index.json for fungi (streaming).

Adds mycobank MB IDs to the existing species_id_map.parquet.

    python3 scripts/buildMycoIdMap.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT

DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")
MYCO_INDEX = os.path.join(ROOT, "portal", "data", "mycobank-index.json")


def load_myco_index_streaming(con) -> int:
    """Load mycobank-index.json into species_id_map using streaming."""
    if not os.path.exists(MYCO_INDEX):
        return 0

    print(f"Streaming {MYCO_INDEX}...")
    t0 = time.time()
    rows = []
    batch_size = 50000
    total = 0

    with open(MYCO_INDEX) as f:
        # Parse as a JSON object - iterate keys
        decoder = json.JSONDecoder()
        content = f.read()
        print(f"  Read {len(content)/1e6:.1f} MB in {time.time() - t0:.1f}s")
        
        # The JSON is a flat object with keys as lowercase names
        data = json.loads(content)
        print(f"  Parsed {len(data):,} entries in {time.time() - t0:.1f}s")

        for key, val in data.items():
            if val.get("rank") != "sp.":
                continue
            name = val.get("name", "").strip()
            mb = val.get("mb", "").strip()
            if not name or not mb:
                continue
            rows.append((name, "mycobank", mb, "exact", 1.0, "2026-07-01"))
            total += 1
            if len(rows) >= batch_size:
                con.executemany(
                    "INSERT INTO species_id_map (scientific_name, source, external_id, matched_on, confidence, source_version) VALUES (?, ?, ?, ?, ?, ?)",
                    rows,
                )
                rows = []
                if total % 200000 == 0:
                    print(f"  Inserted {total:,} rows...")

        if rows:
            con.executemany(
                "INSERT INTO species_id_map (scientific_name, source, external_id, matched_on, confidence, source_version) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
    print(f"  Total mycobank species: {total:,}")
    return con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        print("duckdb is not installed.")
        print("    python3 -m venv .venv-parquet && .venv-parquet/bin/pip install duckdb")
        return 2

    t0 = time.time()
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE IF NOT EXISTS species_id_map (
            scientific_name VARCHAR,
            source VARCHAR,
            external_id VARCHAR,
            matched_on VARCHAR,
            confidence DOUBLE,
            source_version VARCHAR
        )
    """)

    # Load existing map if present
    if os.path.exists(args.out):
        print(f"Loading existing {args.out}...")
        con.execute(f"INSERT INTO species_id_map SELECT * FROM read_parquet('{args.out}')")
        existing = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]
        print(f"  Existing rows: {existing:,}")

    # Load mycobank
    myco_count = load_myco_index_streaming(con)

    # Deduplicate: keep highest confidence per (scientific_name, source)
    print("Deduplicating...")
    con.execute("""
        CREATE TABLE species_id_map_dedup AS
        SELECT scientific_name, source, external_id, matched_on, confidence, source_version
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY scientific_name, source
                       ORDER BY confidence DESC, source_version DESC
                   ) AS rn
            FROM species_id_map
        ) WHERE rn = 1
    """)

    # Write parquet
    con.execute(f"COPY species_id_map_dedup TO '{args.out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    rows = con.execute(f"SELECT count(*) FROM read_parquet('{args.out}')").fetchone()[0]
    con.close()

    size = os.path.getsize(args.out)
    print(f"\n  wrote {os.path.relpath(args.out, ROOT)}: {rows:,} rows, {size / 1e6:.0f} MB in {time.time() - t0:.0f}s")

    # Summary by source
    import duckdb
    con2 = duckdb.connect()
    srcs = con2.execute(f"SELECT source, count(*) FROM read_parquet('{args.out}') GROUP BY source").fetchall()
    for s, c in srcs:
        print(f"  {s}: {c:,}")
    con2.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())