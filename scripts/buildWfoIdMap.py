#!/usr/bin/env python3
"""Build species_id_map rows from the WFO Plant List.

WFO's taxon.tsv carries `wfo-0000000000` identifiers and name.tsv carries the
scientific name and rank. The WFO import (commit 9fd8d1266e) wrote 158,701
species into the tree but discarded the wfo- id, because importColChecklist.py
stamps sourceIds from the archive's own identifier and that archive is a
ChecklistBank shelf whose per-dataset ids are not the wfo- ids. This rebuilds
the mapping from the archive so the patch pipeline can stamp it.

    python3 scripts/buildWfoIdMap.py
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT

WFO_ARCHIVE = "/Volumes/MacieExternal/sources/archives/wfo-plant-list/archive.zip"
DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species_id_map.parquet")
ACCEPTED_RANKS = {"species", "subspecies", "variety", "subvariety", "form",
                  "subform"}


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

    with zipfile.ZipFile(WFO_ARCHIVE) as z:
        with z.open("name.tsv") as f, open(name_tmp.name, "wb") as out:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        with z.open("taxon.tsv") as f, open(taxon_tmp.name, "wb") as out:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    print(f"  extracted name.tsv + taxon.tsv", flush=True)

    con.execute(f"""
        INSERT INTO species_id_map
        SELECT
            n.`scientificName`,
            'wfo',
            t.ID,
            'exact',
            1.0,
            'wfo-2026-06'
        FROM read_csv('{name_tmp.name}', header=true, sep='\t', quote='"', escape='"', ignore_errors=true) n
        JOIN read_csv('{taxon_tmp.name}', header=true, sep='\t', quote='"', escape='"', ignore_errors=true) t
            ON t.nameID = n.ID
        WHERE lower(n.rank) IN ('species','subspecies','variety','subvariety','form','subform')
          AND TRIM(n.`scientificName`) != ''
          AND TRIM(t.ID) != ''
    """)
    os.unlink(name_tmp.name)
    os.unlink(taxon_tmp.name)
    added = con.execute("SELECT count(*) FROM species_id_map").fetchone()[0] - before
    print(f"  WFO rows added: {added:,}", flush=True)

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
    print(f"\n  WFO species: {added:,}")
    print(f"  wrote {os.path.relpath(args.out, ROOT)}: {rows_out:,} rows, {size/1e6:.0f} MB in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())