#!/usr/bin/env python3
"""Build species_id_map rows from the ITIS archive.

ITIS's Taxon.tsv carries the TSN (Taxonomic Serial Number) as `ID` and points
at Name.tsv via `nameID`. The ITIS import (commit b35f739059, +68,813 species)
wrote the tree but dropped the TSN, because importColChecklist.py stamps
sourceIds from the ChecklistBank shelf identifier rather than the source's own.
This rebuilds the mapping so the patch pipeline can stamp it.

    python3 scripts/buildItisIdMap.py
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT

ITIS_ARCHIVE = "/Volumes/MacieExternal/sources/archives/itis/archive.zip"
DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")
ACCEPTED_RANKS = {"species", "subspecies", "hybrid"}


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

    import tempfile
    name_tmp = tempfile.NamedTemporaryFile(suffix=".tsv", delete=False)
    name_tmp.close()
    taxon_tmp = tempfile.NamedTemporaryFile(suffix=".tsv", delete=False)
    taxon_tmp.close()

    with zipfile.ZipFile(ITIS_ARCHIVE) as z:
        with z.open("Name.tsv") as f, open(name_tmp.name, "wb") as out:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        with z.open("Taxon.tsv") as f, open(taxon_tmp.name, "wb") as out:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    print(f"  extracted Name.tsv + Taxon.tsv", flush=True)

    con.execute(f"""
        INSERT INTO species_id_map
        SELECT
            n.`scientificName`,
            'itis',
            t.ID,
            'exact',
            1.0,
            'itis-2026-10'
        FROM read_csv('{name_tmp.name}', header=true, sep='\t', quote='"', escape='"', ignore_errors=true) n
        JOIN read_csv('{taxon_tmp.name}', header=true, sep='\t', quote='"', escape='"', ignore_errors=true) t
            ON t.nameID = n.ID
        WHERE lower(n.rank) IN ('species','subspecies','hybrid')
          AND TRIM(n.`scientificName`) != ''
          AND TRIM(t.ID) != ''
    """)
    os.unlink(name_tmp.name)
    os.unlink(taxon_tmp.name)
    added = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0] - before
    print(f"  ITIS rows added: {added:,}", flush=True)

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
    print(f"\n  ITIS species: {added:,}")
    print(f"  wrote {os.path.relpath(args.out, ROOT)}: {rows_out:,} rows, {size/1e6:.0f} MB in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())