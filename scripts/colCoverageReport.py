#!/usr/bin/env python3
"""COL's own classification, kingdom down to family, with what we hold of it.

The counterpart of coverageReport.py from the other side. coverageReport's
"stated" is our own speciesCount, which resyncFamilyCounts raises to what we
hold, so it cannot say how complete a family is. This walks the Catalogue of
Life's tree instead: every node carries COL's accepted species count and how
many of those names we hold, which is an independent measure.

Same JSON shape and the same page (coverageReport.html), so the portal can
show either:

  stated         COL accepted species (rank species, not synonyms)
  held           of those, how many canonical names we hold in any of our six
                 kingdoms -- by name, wherever we placed it, so a species we
                 hold under another family still counts
  families       COL families below; emptyFamilies: of those, none held
  notInTree      on a COL family: no FAMILY node of that name in our six
                 taxonomy documents

Grouping: COL 26.x files prokaryotes under the new kingdoms (Bacillati,
Methanobacteriati, ...) and viruses under realm kingdoms. Archaeal kingdoms
are grouped under Archaea; bacterial and viral ones under Bacteria and
Viruses, marked as not portal kingdoms. Missing ranks are skipped (a family
with no order hangs from its class); species with no family are gathered in
a "(no family given)" node.

Reads the archive's taxa cache (written by colChecklist on first read), not
the zip. Default is the newest catalogue-of-life-* archive.

    python3 scripts/colCoverageReport.py
    python3 scripts/colCoverageReport.py --cache <archive>.taxa-cache.parquet
"""
import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
from tree import ROOT, kingdom_names, load_kingdom_taxonomy  # noqa: E402

PARQUET = os.path.join(ROOT, "portal", "data", "species.parquet")
OUT_DIR = os.path.join(ROOT, "portal", "data")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coverageReport.html")
FORMAT_VERSION = 1

ARCHAEA = {"Methanobacteriati", "Thermoproteati", "Nanobdellati", "Promethearchaeati"}
BACTERIA = {"Bacillati", "Pseudomonadati", "Thermotogati", "Fusobacteriati"}
PORTAL = {"Animalia", "Plantae", "Fungi", "Chromista", "Protozoa"}


def group_of(kingdom):
    if kingdom in PORTAL:
        return kingdom
    if kingdom in ARCHAEA:
        return "Archaea"
    if kingdom in BACTERIA:
        return "Bacteria"
    if kingdom and kingdom.endswith("virae"):
        return "Viruses"
    return "(no kingdom given)"


def newest_cache():
    found = sorted(glob.glob(os.path.join(sources.ROOT, "archives", "catalogue-of-life-*",
                                          "*.taxa-cache.parquet")))
    if not found:
        sys.exit("no catalogue-of-life-* taxa cache under the sources volume; pass --cache")
    return found[-1]


def our_family_names():
    names = set()
    for k in kingdom_names():
        stack = [load_kingdom_taxonomy(k)]
        while stack:
            n = stack.pop()
            if n.get("rank") == "FAMILY":
                names.add((n.get("name") or "").replace("†", "").strip().lower())
                continue
            stack.extend(n.get("children") or [])
    return names


def stats():
    return {"held": 0, "stated": 0, "families": 0, "emptyFamilies": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None)
    ap.add_argument("--parquet", default=PARQUET)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()
    cache = args.cache or newest_cache()

    import duckdb
    rows = duckdb.sql(f"""
        WITH col AS (
            SELECT kingdom_name k, phylum_name p, class_name c, order_name o, family_name f,
                   -- authorship off the end, and the subgenus out: COL writes
                   -- "Tipula (Triplicitipula) aequalis", we hold "Tipula aequalis"
                   -- (175k of the first run's 180k unmatched animals)
                   regexp_replace(
                       CASE WHEN authorship IS NOT NULL AND authorship <> ''
                                 AND ends_with(name, authorship)
                            THEN trim(left(name, length(name) - length(authorship)))
                            ELSE name END,
                       ' \\([^)]*\\) ', ' ') AS canon
            FROM read_parquet('{cache}')
            WHERE rank = 'species' AND NOT is_synonym),
        ours AS (SELECT DISTINCT canonicalName FROM read_parquet('{args.parquet}'))
        SELECT k, p, c, o, f, count(*), count(ours.canonicalName)
        FROM col LEFT JOIN ours ON ours.canonicalName = col.canon
        GROUP BY ALL""").fetchall()
    ours = our_family_names()

    def node(name, rank):
        return {"name": name, "rank": rank, "stats": stats(), "_kids": {}}

    groups = {}
    for k, p, c, o, f, n_col, n_held in rows:
        g = group_of(k)
        top = groups.setdefault(g, node(g, "KINGDOM"))
        path = top
        steps = []
        if k and k != g:
            steps.append((k, "KINGDOM"))
        steps += [(p, "PHYLUM"), (c, "CLASS"), (o, "ORDER")]
        for name, rank in steps:
            if not name:
                continue
            path = path["_kids"].setdefault((rank, name), node(name, rank))
        fam = path["_kids"].setdefault(("FAMILY", f or ""), node(f or "(no family given)", "FAMILY"))
        if not f:
            fam["noFamily"] = True
        elif f.replace("†", "").strip().lower() not in ours:
            fam["notInTree"] = True
        fam["stats"]["stated"] += n_col
        fam["stats"]["held"] += n_held

    def finish(n):
        if n["rank"] == "FAMILY" and not n["_kids"]:
            del n["_kids"]
            s = n["stats"]
            s["families"] = 0 if n.get("noFamily") else 1
            s["emptyFamilies"] = 1 if s["families"] and not s["held"] else 0
            return n
        kids = [finish(c) for c in n.pop("_kids").values()]
        s = stats()
        for c in kids:
            for key in s:
                s[key] += c["stats"][key]
        n["stats"] = s
        n["children"] = kids
        return n

    order = ["Animalia", "Plantae", "Fungi", "Chromista", "Protozoa", "Archaea",
             "Bacteria", "Viruses", "(no kingdom given)"]
    kingdoms = [finish(groups[g]) for g in order if g in groups]
    for k in kingdoms:
        if k["name"] in ("Bacteria", "Viruses"):
            k["commonName"] = "not a portal kingdom"
    total = stats()
    for k in kingdoms:
        for key in total:
            total[key] += k["stats"][key]

    report = {
        "formatVersion": FORMAT_VERSION,
        "title": "COL coverage, kingdom to family",
        "source": {"cache": cache, "builtAt": time.strftime(
            "%Y-%m-%dT%H:%M:%S%z", time.localtime(os.path.getmtime(cache)))},
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "parquetBuiltAt": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                        time.localtime(os.path.getmtime(args.parquet))),
        "labels": {"held": "Held (by name)", "stated": "COL species"},
        "metrics": {
            "stated": "COL accepted species",
            "held": "of those, canonical names held in any of our six kingdoms",
            "families": "COL families",
            "emptyFamilies": "COL families of which we hold no species",
        },
        "note": "COL's classification, not ours. Held counts a COL species when we hold its canonical name "
                "anywhere in our six kingdoms, under whatever family we placed it. 'not in our tree' marks a COL "
                "family with no FAMILY node of that name in our taxonomy.",
        "total": total,
        "kingdoms": kingdoms,
    }

    os.makedirs(args.out_dir, exist_ok=True)
    out_json = os.path.join(args.out_dir, "col-coverage-report.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, separators=(",", ":"))
    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()
    embedded = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out_html = os.path.join(args.out_dir, "col-coverage-report.html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(page.replace("/*COVERAGE_DATA*/null", embedded))

    for k in kingdoms:
        s = k["stats"]
        print(f"  {k['name']:18s} {s['families']:>6,} families ({s['emptyFamilies']:,} none held)  "
              f"{s['held']:>10,} held of {s['stated']:>10,} COL species")
    print(f"  wrote {out_json}\n  wrote {out_html}\n  from {cache}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
