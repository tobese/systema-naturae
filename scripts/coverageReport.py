#!/usr/bin/env python3
"""Coverage report, kingdom down to family, as JSON plus a static page.

One nested document per run: every rank node of the six kingdoms' taxonomy
documents (KINGDOM > PHYLUM > CLASS > ORDER > FAMILY, whatever depth a
kingdom actually has) with counts rolled up from its families. Shaped so the
portal can load it later; for now `coverage-report.html` beside it embeds the
same JSON and renders expandable levels, opened straight from disk.

Counts per node:

  held        species we hold (species.parquet)
  stated      the FAMILY nodes' speciesCount, summed. Not an independent
              real-world total: resyncFamilyCounts.py raises it to what the
              file holds, so held > stated cannot happen and held == stated
              often means "no better total recorded", not "complete".
  described   held species with a description
  authored    held species with an authorship
  common      held species with a common name
  families    FAMILY nodes below; emptyFamilies: of those, holding none

Joined by rank path, not by slug (87 fungi families are all called
`incertae-sedis`): a FAMILY node is matched to the parquet's
(kingdom, phylum, cls, ord, family) the same way buildSpeciesParquet.py
derived those columns. Family files no FAMILY node resolves to are counted
per kingdom as `unplacedFiles`, not dropped.

Reads the parquet as it is; run `make species-parquet` first for fresh
numbers. The parquet's build time is recorded in the output.

    python3 scripts/coverageReport.py
    python3 scripts/coverageReport.py --out-dir /tmp/coverage
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT, dir_name, kingdom_names, load_kingdom_taxonomy, resolve_family_file  # noqa: E402

PARQUET = os.path.join(ROOT, "portal", "data", "species.parquet")
OUT_DIR = os.path.join(ROOT, "portal", "data")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coverageReport.html")
FORMAT_VERSION = 1
METRICS = ("held", "described", "authored", "common")
RANK_KEY = {"PHYLUM": "phylum", "CLASS": "cls", "ORDER": "ord"}


def held_counts(parquet: str) -> dict:
    """(kingdom, phylum, cls, ord, family) -> {metric: n}."""
    import duckdb
    rows = duckdb.sql(f"""
        SELECT kingdom, phylum, cls, ord, family,
               count(*),
               count(*) FILTER (WHERE hasDescription),
               count(*) FILTER (WHERE coalesce(authorship, '') <> ''),
               count(*) FILTER (WHERE coalesce(commonName, '') <> '')
        FROM read_parquet('{parquet}')
        GROUP BY ALL""").fetchall()
    return {r[:5]: dict(zip(METRICS, r[5:])) for r in rows}


def empty_stats() -> dict:
    return {**{m: 0 for m in METRICS}, "stated": 0, "families": 0, "emptyFamilies": 0}


def add(into: dict, s: dict) -> None:
    for k, v in s.items():
        into[k] += v


def build_kingdom(kingdom: str, held: dict) -> dict:
    claimed = set()

    def walk(node, ranks):
        rank = node.get("rank") or ""
        out = {"name": node.get("name") or "", "rank": rank}
        if node.get("commonName"):
            out["commonName"] = node["commonName"]
        if rank == "FAMILY":
            slug = node.get("appSlug") or ""
            key = (kingdom, dir_name(ranks.get("phylum")), dir_name(ranks.get("cls")),
                   dir_name(ranks.get("ord")), dir_name(slug))
            out["slug"] = slug
            if key in claimed:
                # A second FAMILY node with the same slug under the same order
                # (37 in animalia on 2026-11-01): one file, counted once.
                out["duplicateNode"] = True
                out["stats"] = empty_stats()
                return out
            has_file = bool(slug) and resolve_family_file(**ranks, slug=slug) is not None
            got = held.get(key) if has_file else None
            claimed.add(key)
            s = empty_stats()
            add(s, got or {})
            s["stated"] = node.get("speciesCount") or 0
            s["families"] = 1
            s["emptyFamilies"] = 0 if s["held"] else 1
            if not has_file:
                out["noFile"] = True
            out["stats"] = s
            return out
        if rank in RANK_KEY:
            ranks = dict(ranks, **{RANK_KEY[rank]: node.get("name")})
        s = empty_stats()
        kids = []
        for child in node.get("children") or []:
            c = walk(child, ranks)
            add(s, c["stats"])
            kids.append(c)
        out["stats"] = s
        out["children"] = kids
        return out

    doc = load_kingdom_taxonomy(kingdom)
    root = walk(doc, {"kingdom": kingdom, "phylum": None, "cls": None, "ord": None})
    root["name"] = root["name"] or kingdom.capitalize()
    root["rank"] = "KINGDOM"
    unplaced = empty_stats()
    files = 0
    for key, got in held.items():
        if key[0] == kingdom and key not in claimed:
            add(unplaced, got)
            files += 1
    root["unplacedFiles"] = {"files": files, **{m: unplaced[m] for m in METRICS}}
    return root


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=PARQUET)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()

    held = held_counts(args.parquet)
    kingdoms = [build_kingdom(k, held) for k in kingdom_names()]
    total = empty_stats()
    for k in kingdoms:
        add(total, k["stats"])
    report = {
        "formatVersion": FORMAT_VERSION,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "parquetBuiltAt": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                        time.localtime(os.path.getmtime(args.parquet))),
        "metrics": {
            "held": "species held",
            "stated": "sum of FAMILY speciesCount (raised to held by resyncFamilyCounts; not an independent total)",
            "described": "held species with a description",
            "authored": "held species with an authorship",
            "common": "held species with a common name",
            "families": "FAMILY nodes",
            "emptyFamilies": "FAMILY nodes holding no species",
        },
        "total": total,
        "kingdoms": kingdoms,
    }

    os.makedirs(args.out_dir, exist_ok=True)
    out_json = os.path.join(args.out_dir, "coverage-report.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, separators=(",", ":"))
    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()
    # </ in a name would end the script element early.
    embedded = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out_html = os.path.join(args.out_dir, "coverage-report.html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(page.replace("/*COVERAGE_DATA*/null", embedded))

    for k in kingdoms:
        s, u = k["stats"], k["unplacedFiles"]
        print(f"  {k['name']:10s} {s['families']:>6,} families ({s['emptyFamilies']:,} empty)  "
              f"{s['held']:>10,} held / {s['stated']:>10,} stated"
              + (f"   + {u['held']:,} in {u['files']:,} unplaced files" if u["files"] else ""))
    print(f"  wrote {out_json}\n  wrote {out_html}  (parquet built {report['parquetBuiltAt']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
