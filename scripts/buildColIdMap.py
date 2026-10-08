#!/usr/bin/env python3
"""Build species_id_map rows from the COL Taxon.tsv.

COL's accepted taxa carry a `dwc:taxonID` (a 5-6 char alphanumeric LSID-style
key) that is stable and unique. Every species we imported from COL lost it --
importColStage2 reads name/parent/rank/authorship but never writes the id back.
This rebuilds the mapping from the archive, keyed on scientific name, so the
existing patch pipeline can stamp it.

    python3 scripts/buildColIdMap.py
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT

COL_ARCHIVE = "/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/col2026-base_dwca.zip"
DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")


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

    if not os.path.exists(args.out):
        print(f"Missing {args.out}. Run scripts/buildIdMap.py first.")
        return 1

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
    con.execute(f"INSERT INTO species_id_map SELECT * FROM read_parquet('{args.out}')")
    before = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0]
    print(f"  existing rows: {before:,}", flush=True)

    # Extract Taxon.tsv to a temp file so DuckDB can read it natively (it
    # cannot read straight out of a zip). 369 MB on disk, ~5.4M rows.
    tmp = tempfile.NamedTemporaryFile(suffix=".tsv", delete=False)
    tmp.close()
    with zipfile.ZipFile(COL_ARCHIVE).open("Taxon.tsv") as f:
        with open(tmp.name, "wb") as out:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    print(f"  extracted Taxon.tsv ({os.path.getsize(tmp.name)/1e6:.0f} MB)", flush=True)

    con.execute(f"""
        INSERT INTO species_id_map
        SELECT
            TRIM("dwc:scientificName") AS scientific_name,
            'col' AS source,
            TRIM("dwc:taxonID") AS external_id,
            'exact' AS matched_on,
            1.0 AS confidence,
            'col2026-base' AS source_version
        FROM read_csv(
            '{tmp.name}',
            header=true,
            sep='\t',
            quote='"',
            escape='"',
            ignore_errors=true
        )
        WHERE "dwc:taxonomicStatus" IN ('accepted', 'provisionally accepted')
          AND "dwc:taxonRank" IN ('species', 'subspecies')
          AND TRIM("dwc:scientificName") != ''
          AND TRIM("dwc:taxonID") != ''
    """)
    os.unlink(tmp.name)
    added = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0] - before
    print(f"  COL rows added: {added:,}", flush=True)

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
    con.execute(f"COPY species_id_map_dedup TO '{args.out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    rows_out = con.execute(f"SELECT count(*) FROM read_parquet('{args.out}')").fetchone()[0]
    con.close()

    size = os.path.getsize(args.out)
    print(f"\n  COL species: {added:,}")
    print(f"  wrote {os.path.relpath(args.out, ROOT)}: {rows_out:,} rows, {size/1e6:.0f} MB in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())