#!/usr/bin/env python3
"""Build species_id_map staging table from GBIF cache + wiki-images.json.

Loads all 191 GBIF cache files and shared/data/wiki-images.json into a DuckDB
staging table keyed by species UUID. Outputs a consolidated mapping parquet.

    python3 scripts/buildIdMap.py
    python3 scripts/buildIdMap.py --out portal/data/species_id_map.parquet
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import KINGDOMS, ROOT

PARQUET_PY = os.environ.get("PARQUET_PY", os.path.join(ROOT, ".venv-parquet", "bin", "python3"))
DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")
GBIF_CACHE_DIR = os.path.join(ROOT, "portal", "data")
WIKI_IMAGES_PATH = os.path.join(ROOT, "shared", "data", "wiki-images.json")


def load_gbif_cache(con, path: str) -> int:
    """Load one GBIF cache file into species_id_map via DuckDB bulk read."""
    import json
    with open(path) as f:
        data = json.load(f)
    downloaded_at = data.get("downloadedAt", "")
    rows = []
    for fam_obj in data.get("speciesByFamily", {}).values():
        for sp in fam_obj.get("species", []):
            canonical = sp.get("canonicalName")
            nub_key = sp.get("nubKey")
            if canonical and nub_key is not None:
                rows.append((canonical, "gbif", str(nub_key), "exact", 1.0, downloaded_at))
    if rows:
        con.executemany(
            "INSERT INTO species_id_map (scientific_name, source, external_id, matched_on, confidence, source_version) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
    return con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]


def load_wiki_images(con) -> int:
    """Load wiki-images.json into species_id_map."""
    if not os.path.exists(WIKI_IMAGES_PATH):
        return 0
    import json
    with open(WIKI_IMAGES_PATH) as f:
        data = json.load(f)
    rows = []
    for name, val in data.items():
        qid = val.get("qid")
        fetched = val.get("fetchedAt", "")
        if qid and qid != "" and qid != "WIKIDATA_NONE":
            rows.append((name, "wikidata", str(qid), "exact", 0.9, fetched))
    if rows:
        con.executemany(
            "INSERT INTO species_id_map (scientific_name, source, external_id, matched_on, confidence, source_version) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
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

    # Load GBIF caches
    gbif_files = sorted(glob.glob(os.path.join(GBIF_CACHE_DIR, "gbif-cache-*.json")))
    print(f"Found {len(gbif_files)} GBIF cache files")
    gbif_count = 0
    for i, f in enumerate(gbif_files):
        n_before = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]
        load_gbif_cache(con, f)
        n_after = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]
        n = n_after - n_before
        gbif_count += n
        if n:
            print(f"  [{i+1}/{len(gbif_files)}] {os.path.basename(f)}: {n:,} species (total: {gbif_count:,})")
        elif i % 20 == 0:
            print(f"  [{i+1}/{len(gbif_files)}] {os.path.basename(f)}: 0 species")

    # Load wiki-images
    wiki_count = load_wiki_images(con) - gbif_count
    print(f"  wiki-images.json: {wiki_count:,} QIDs")

    # Deduplicate: keep highest confidence per (scientific_name, source)
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
    print(f"  GBIF: {gbif_count:,}  Wikidata: {wiki_count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())