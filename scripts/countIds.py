#!/usr/bin/env python3
"""ID and description coverage report.

Reads the derived species.parquet (requires duckdb) and prints counts for each
ID/metadata field against the total species, with kingdom breakdowns and
cross-tabs against description coverage.

    make count
    make count PARQUET_PY=.venv-parquet/bin/python
    make count --json /Volumes/MacieExternal/tmp/kilo/coverage-report-2026-10-07.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(ROOT, "portal", "data", "species.parquet")
PARQUET_PY = os.environ.get("PARQUET_PY", os.path.join(ROOT, ".venv-parquet", "bin", "python3"))


def run_duckdb(sql: str):
    script = f"import duckdb; con = duckdb.connect(); con.execute({repr(sql)}); print(con.fetchone()[0])"
    result = subprocess.run(
        [PARQUET_PY, "-c", script],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"duckdb error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()


def run_duckdb_rows(sql: str):
    script = f"import json; import duckdb; con = duckdb.connect(); con.execute({repr(sql)}); rows = con.fetchall(); print(json.dumps(rows))"
    result = subprocess.run(
        [PARQUET_PY, "-c", script],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"duckdb error: {result.stderr}", file=sys.stderr)
        return []
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="PATH",
                        help="write machine-readable JSON report to this path")
    args = parser.parse_args()

    if not os.path.exists(PARQUET):
        print(f"Missing {PARQUET}. Run make species-parquet first.")
        return 1

    total = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet")'))

    def pct(n):
        return f"{n/total*100:.1f}%" if total else "0.0%"

    with_id = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE id IS NOT NULL AND length(id) > 0'))
    with_desc = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE hasDescription'))
    with_source = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE authorityIds IS NOT NULL AND length(authorityIds) > 0'))
    wiki_sourced = int(run_duckdb("SELECT count(*) FROM read_parquet('portal/data/species.parquet') WHERE sourcedFrom = 'wikipedia'"))
    with_iucn = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE iucnStatus IS NOT NULL AND length(iucnStatus) > 0'))
    desc_and_source = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE hasDescription AND authorityIds IS NOT NULL AND length(authorityIds) > 0'))
    desc_no_source = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE hasDescription AND (authorityIds IS NULL OR length(authorityIds) = 0)'))
    source_no_desc = int(run_duckdb('SELECT count(*) FROM read_parquet("portal/data/species.parquet") WHERE (authorityIds IS NOT NULL AND length(authorityIds) > 0) AND NOT hasDescription'))
    wiki_and_desc = int(run_duckdb("SELECT count(*) FROM read_parquet('portal/data/species.parquet') WHERE sourcedFrom = 'wikipedia' AND hasDescription"))

    auth_rows = run_duckdb_rows('''
        WITH split_ids AS (
            SELECT unnest(string_split(authorityIds, ',')) as auth
            FROM read_parquet("portal/data/species.parquet")
            WHERE authorityIds IS NOT NULL AND length(authorityIds) > 0
        )
        SELECT auth, count(*) as n FROM split_ids GROUP BY auth ORDER BY n DESC
    ''')
    auths = {row[0]: row[1] for row in auth_rows}

    prefix_rows = run_duckdb_rows('''
        SELECT CASE
            WHEN id LIKE 'SP_%' THEN 'SP_'
            WHEN id LIKE 'GENUS_%' THEN 'GENUS_'
            WHEN id LIKE 'FAM_%' THEN 'FAM_'
            WHEN id LIKE 'ORD_%' THEN 'ORD_'
            WHEN id LIKE 'CLS_%' THEN 'CLS_'
            WHEN id LIKE 'SUB_%' THEN 'SUB_'
            WHEN id LIKE 'HYBRID_%' THEN 'HYBRID_'
            WHEN id LIKE 'KINGDOM_%' THEN 'KINGDOM_'
            ELSE 'NO_PREFIX'
        END as prefix, count(*) as n
        FROM read_parquet('portal/data/species.parquet')
        GROUP BY prefix ORDER BY n DESC
    ''')
    prefixes = {row[0]: row[1] for row in prefix_rows}

    kingdom_rows = run_duckdb_rows('''SELECT kingdom, count(*) as total,
        sum(CASE WHEN id IS NOT NULL AND length(id) > 0 THEN 1 ELSE 0 END) as with_id,
        sum(CASE WHEN hasDescription THEN 1 ELSE 0 END) as with_desc,
        sum(CASE WHEN authorityIds IS NOT NULL AND length(authorityIds) > 0 THEN 1 ELSE 0 END) as with_source,
        sum(CASE WHEN sourcedFrom = 'wikipedia' THEN 1 ELSE 0 END) as wiki_sourced,
        sum(CASE WHEN iucnStatus IS NOT NULL AND length(iucnStatus) > 0 THEN 1 ELSE 0 END) as with_iucn
        FROM read_parquet("portal/data/species.parquet")
        GROUP BY kingdom ORDER BY total DESC''')

    wiki_path = os.path.join(ROOT, "shared", "data", "wiki-images.json")
    wiki_total = 0
    wiki_with_qid = 0
    wiki_with_image = 0
    wiki_with_iucn = 0
    if os.path.exists(wiki_path):
        with open(wiki_path) as f:
            wiki = json.load(f)
        wiki_total = len(wiki)
        wiki_with_qid = sum(1 for v in wiki.values() if v.get("qid"))
        wiki_with_image = sum(1 for v in wiki.values() if v.get("image"))
        wiki_with_iucn = sum(1 for v in wiki.values() if v.get("iucnStatus"))

    kingdom_breakdown = {}
    for row in kingdom_rows:
        k, tot, wid, wdesc, wsrc, wiki, wiucn = row
        kingdom_breakdown[k] = {
            "total": tot,
            "withId": wid,
            "withDesc": wdesc,
            "withSource": wsrc,
            "wikiSourced": wiki,
            "withIucn": wiucn,
        }

    report = {
        "generatedAt": sys.argv[0] if False else "1970-01-01T00:00:00",
        "source": "species.parquet",
        "totalSpecies": total,
        "id": {
            "present": with_id,
            "pct": round(with_id / total * 100, 2) if total else 0.0,
            "prefixes": prefixes,
        },
        "sourceIds": {
            "any": with_source,
            "pct": round(with_source / total * 100, 2) if total else 0.0,
            "authorities": auths,
        },
        "wikipedia": {
            "sourcedFrom": wiki_sourced,
            "pct": round(wiki_sourced / total * 100, 2) if total else 0.0,
        },
        "wikiImages": {
            "entries": wiki_total,
            "withQid": wiki_with_qid,
            "withImage": wiki_with_image,
            "withIucn": wiki_with_iucn,
        },
        "descriptions": {
            "withDescription": with_desc,
            "pct": round(with_desc / total * 100, 2) if total else 0.0,
            "andSourceIds": desc_and_source,
            "noSourceIds": desc_no_source,
            "sourceIdsNoDesc": source_no_desc,
            "wikipediaAndDesc": wiki_and_desc,
        },
        "crossTabs": {
            "descAndSourceIdsPct": round(desc_and_source / total * 100, 2) if total else 0.0,
            "ofDescribedWithSourceIds": round(desc_and_source / with_desc * 100, 2) if with_desc else 0.0,
            "ofSourceIdsWithDescription": round(desc_and_source / with_source * 100, 2) if with_source else 0.0,
        },
        "byKingdom": kingdom_breakdown,
    }

    if args.json:
        report["generatedAt"] = __import__("datetime").datetime.now().isoformat()
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Wrote {args.json}")
    else:
        print("=" * 70)
        print("ID AND DESCRIPTION COVERAGE")
        print("=" * 70)
        print(f"Total species in tree: {total:,}")
        print()
        print("Internal ID (id field)")
        print(f"  Present:        {with_id:>10,} / {total:,}  ({pct(with_id)})")
        print()
        print("External authority IDs (sourceIds)")
        print(f"  Any authority:  {with_source:>10,} / {total:,}  ({pct(with_source)})")
        if auths:
            for auth, n in sorted(auths.items(), key=lambda x: -x[1]):
                print(f"    {auth:15s}: {n:>10,}  ({n/total*100:.2f}%)")
        print()
        print("Wikipedia")
        print(f"  sourcedFrom='wikipedia': {wiki_sourced:>10,} / {total:,}  ({pct(wiki_sourced)})")
        print()
        print("Wiki-images sidecar")
        if wiki_total:
            print(f"  Entries:        {wiki_total:>10,}")
            print(f"  With qid:       {wiki_with_qid:>10,} / {wiki_total:,}  ({wiki_with_qid/wiki_total*100:.1f}%)")
            print(f"  With image:     {wiki_with_image:>10,} / {wiki_total:,}  ({wiki_with_image/wiki_total*100:.1f}%)")
            print(f"  With iucnStatus:{wiki_with_iucn:>10,} / {wiki_total:,}  ({wiki_with_iucn/wiki_total*100:.1f}%)")
        else:
            print("  (not present)")
        print()
        print("ID prefix distribution (species IDs):")
        for prefix, n in sorted(prefixes.items(), key=lambda x: -x[1]):
            print(f"  {prefix:15s}: {n:>10,}  ({n/total*100:.1f}%)")
        print()
        print("Descriptions")
        print(f"  With description:           {with_desc:>10,} / {total:,}  ({pct(with_desc)})")
        print()
        print("Cross-tabs: descriptions vs IDs")
        print(f"  Description + sourceIds:    {desc_and_source:>10,} / {total:,}  ({pct(desc_and_source)})")
        print(f"  Description, no sourceIds:  {desc_no_source:>10,} / {total:,}  ({pct(desc_no_source)})")
        print(f"  SourceIds, no description:  {source_no_desc:>10,} / {total:,}  ({pct(source_no_desc)})")
        print(f"  Wikipedia + description:    {wiki_and_desc:>10,} / {total:,}  ({pct(wiki_and_desc)})")
        if with_desc:
            print(f"  Of described species with sourceIds: {desc_and_source/with_desc*100:.1f}%")
        if with_source:
            print(f"  Of sourceIds species with description: {desc_and_source/with_source*100:.1f}%")
        print()
        print("By kingdom:")
        print(f"{'Kingdom':<12} {'Total':>10} {'id%':>7} {'desc%':>7} {'src%':>7} {'wiki%':>7} {'iucn%':>7}")
        for row in kingdom_rows:
            k, tot, wid, wdesc, wsrc, wiki, wiucn = row
            print(f"{k:<12} {tot:>10,} {wid/tot*100:>6.1f}% {wdesc/tot*100:>6.1f}% {wsrc/tot*100:>6.1f}% {wiki/tot*100:>6.1f}% {wiucn/tot*100:>6.1f}%")
        print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
