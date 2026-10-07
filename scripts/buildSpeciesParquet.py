#!/usr/bin/env python3
"""Derive a flat species.parquet from the family files, for ad-hoc questions.

Derived, gitignored, and never the source of truth. The tree is the tree; this
is a projection of it that answers questions without a 4-minute parse. Rebuild
it whenever the tree changes -- it carries no state worth keeping.

    python3 scripts/buildSpeciesParquet.py
    python3 scripts/buildSpeciesParquet.py --out /tmp/s.parquet
    python3 scripts/buildSpeciesParquet.py --kingdom fungi

What this is for
----------------
`BACKLOG.md` asked whether an object/file database would suit the tree and the
answer after measuring was no: DuckDB reads the nested JSON via `json_tree()`
but a view over 14,084 files costs ~50s and a flatten attempt OOM'd at 12.7 GiB.
That was a view, re-parsing 0.97 GB of JSON on every query. Flattening once into
columnar is the cheaper shape for the same engine: one parse at build time, then
milliseconds per question, with no JSON involved in the query at all.

The alternative is re-running a Python script per question, and at 4 minutes a
run that is how a question goes unasked. This exists so "which families gained
species in the last import" is a query rather than a project.

One row per species, with its full rank path denormalised. The rank path is not
inferred: a family document lives at
`taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json`,
so the path *is* the ranks, which is the same fact `tree.resolve_family_file`
reverses.

    SELECT familyName, count(*) AS n
    FROM 'portal/data/species.parquet'
    WHERE kingdom = 'fungi' AND rank = 'SPECIES'
    GROUP BY 1 ORDER BY n DESC LIMIT 10;

Requires duckdb, which is not a project dependency (it is a ~20 MB wheel and
nothing else here needs it). If the import fails this prints the command:

    python3 -m venv .venv-parquet && .venv-parquet/bin/pip install duckdb
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import (  # noqa: E402
    KINGDOMS,
    ROOT,
    dir_name,
    iter_family_files,
    iter_family_nodes,
    iter_species_with_parent,
    resolve_family_file,
)

DEFAULT_OUT = os.path.join(ROOT, "portal", "data", "species.parquet")

# Written as one JSON object per line, then let DuckDB's reader infer the schema
# and do the columnar write. Streaming to a temp file keeps peak memory at one
# family document rather than 2.4M rows, which is the same reason `tree.py` is
# iterative.
COLUMNS = (
    "kingdom", "phylum", "cls", "ord", "family", "familyName",
    "genus", "genusRank", "name", "id", "uuid", "rank", "lineage", "commonName",
    "continents", "subspeciesCount", "hasDescription", "sourcedFrom",
    "iucnStatus", "authorityIds",
)


def rank_map(kingdom: str) -> dict:
    """family file path -> its ranks, read from the kingdom's taxonomy document.

    Not guessed from the path, which does not contain enough information.
    `taxonomy/animalia/tardigrada/tardigrada/src/data/tardigrada.json` has one
    segment between the kingdom and the family directory, and that one segment is
    both the phylum and the family: Tardigrada is KINGDOM > PHYLUM > FAMILY with
    no class and no order. Any positional reading of the path either invents an
    order or files it as a class.

    So the ranks come from the taxonomy document, walked with `tree.iter_family_nodes`
    and resolved with `tree.resolve_family_file` -- the same join `verifyTree`
    asserts, and a verified bijection in five of six kingdoms.
    """
    out = {}
    for node, ranks in iter_family_nodes(kingdom):
        slug = node.get("appSlug")
        if not slug:
            continue
        resolved = resolve_family_file(**ranks, slug=slug)
        if resolved is None:
            continue
        out[resolved] = {
            "kingdom": kingdom,
            "phylum": dir_name(ranks.get("phylum")),
            "cls": dir_name(ranks.get("cls")),
            "ord": dir_name(ranks.get("ord")),
            "family": dir_name(slug),
        }
    return out


def rows_for_family(fam, ranks: dict) -> list:
    """One row per species in one family document."""
    doc = fam.load()
    family_name = (doc.get("name") or "").strip()
    out = []
    for parent, sp in iter_species_with_parent(doc):
        parent_rank = (parent or {}).get("rank")
        # The owning genus is the nearest ancestor; a species directly under a
        # SUBFAMILY has none, and that is recorded rather than invented.
        genus = ""
        if parent_rank == "GENUS":
            genus = (parent.get("name") or "").strip()
        continents = sp.get("continents") or []
        source_ids = sp.get("sourceIds") or {}
        out.append({
            **ranks,
            "familyName": family_name,
            "genus": genus,
            "genusRank": parent_rank or "",
            "name": (sp.get("name") or "").strip(),
            "id": sp.get("id") or "",
            "uuid": sp.get("uuid") or "",
            "rank": sp.get("rank") or "",
            "lineage": (sp.get("lineage") or "").strip(),
            "commonName": sp.get("commonName") or "",
            "continents": ",".join(str(c) for c in continents),
            "subspeciesCount": sp.get("subspeciesCount"),
            "hasDescription": bool(sp.get("description")),
            "sourcedFrom": sp.get("sourcedFrom") or "",
            "iucnStatus": sp.get("iucnStatus") or "",
            # A map in a flat table has to go somewhere; DuckDB has MAP, but the
            # common case is "how many identifiers does this species carry", so
            # the count is its own column and the keys are kept as CSV.
            "authorityIds": ",".join(sorted(source_ids)),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--kingdom", choices=KINGDOMS,
                    help="one kingdom; default all six")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even if the output is newer than the tree")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        print("duckdb is not installed. This is the only thing in the repo that "
              "needs it:\n")
        print("    python3 -m venv .venv-parquet && "
              ".venv-parquet/bin/pip install duckdb\n")
        return 2

    kingdoms = [args.kingdom] if args.kingdom else KINGDOMS

    if os.path.exists(args.out) and not args.force:
        newest = 0.0
        for k in KINGDOMS:
            for fam in iter_family_files(k):
                try:
                    newest = max(newest, os.path.getmtime(fam.path))
                except OSError:
                    pass
        if os.path.getmtime(args.out) >= newest:
            print(f"  {os.path.relpath(args.out, ROOT)} is newer than the "
                  f"tree; pass --force to rebuild")
            return 0

    t0 = time.time()
    jsonl = args.out + ".jsonl"
    total = 0
    files = 0
    unranked = 0
    with open(jsonl, "w", encoding="utf-8") as fh:
        for k in kingdoms:
            k_t0, k_rows = time.time(), 0
            ranks_by_path = rank_map(k)
            for fam in iter_family_files(k):
                ranks = ranks_by_path.get(fam.path)
                if ranks is None:
                    # No FAMILY node resolves to this file. Recorded rather than
                    # silently given invented ranks; see verifyTree's note about
                    # plantae's 223 declared-but-empty families.
                    unranked += 1
                    ranks = {"kingdom": k, "phylum": "", "cls": "", "ord": "",
                             "family": fam.slug}
                rows = rows_for_family(fam, ranks)
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                k_rows += len(rows)
                files += 1
                if files % 1000 == 0:
                    print(f"  {files:>6,} files  {total:>9,} rows  "
                          f"{time.time() - t0:.0f}s elapsed", flush=True)
            print(f"  {k:10s} {k_rows:>9,} species in "
                  f"{time.time() - k_t0:.0f}s")
            total += k_rows
    if unranked:
        print(f"  note: {unranked:,} family files had no taxonomy node and were "
              f"written with empty phylum/class/order")

    print(f"\n  {total:,} species from {files:,} family files in "
          f"{time.time() - t0:.0f}s; writing parquet")

    con = duckdb.connect()
    cols = ", ".join(f'"{c}"' for c in COLUMNS)
    con.execute(f"""
        COPY (
            SELECT {cols} FROM read_json_auto('{jsonl}', maximum_object_size=10485760)
        ) TO '{args.out}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    rows_out = con.execute(
        f"SELECT count(*) FROM read_parquet('{args.out}')").fetchone()[0]
    con.close()
    os.remove(jsonl)

    size = os.path.getsize(args.out)
    print(f"  wrote {os.path.relpath(args.out, ROOT)}: {rows_out:,} rows, "
          f"{size / 1e6:.0f} MB in {time.time() - t0:.0f}s total")
    print("\n  derived and gitignored -- the family files remain the truth. "
          "Rebuild after an import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())