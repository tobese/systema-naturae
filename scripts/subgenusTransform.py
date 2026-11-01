#!/usr/bin/env python3
"""Subgenus fills from COL, for applyEnrichment.py.

docs/sub-ranks-plan.md step 1: the subgenus is a field on the SPECIES node,
not a tree level, and the name and its identity (the bare binomial) stay as
they are. COL writes it inside the name -- "Tipula (Triplicitipula)
aequalis" -- so every accepted COL species whose name carries one gives a
fill for the species we hold under the same binomial.

Fill-only, like the nomenclatural track: a species with a subgenus already
is left alone (applyEnrichment checks again at write time), and a binomial
held more than once in a kingdom is skipped and counted rather than guessed.
No sourceId is added -- the species keep the COL ids their imports gave them.

Reads the archive's taxa cache (newest catalogue-of-life-* by default) and
writes enrich.jsonl + summary.json to <sources>/work/<slug>-subgenus/.

    python3 scripts/subgenusTransform.py            # measure
    python3 scripts/subgenusTransform.py --apply    # write the work files
    python3 scripts/applyEnrichment.py <work>/enrich.jsonl --apply
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
from colCoverageReport import group_of, newest_cache  # noqa: E402
from nomenclatureTransform import held  # noqa: E402

SUBGENUS = re.compile(r"^(\S+) \(([^)\s]+)\) (\S+)")
KINGDOM = {"Animalia": "animalia", "Plantae": "plantae", "Fungi": "fungi",
           "Chromista": "chromista", "Protozoa": "protozoa", "Archaea": "archaea"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None)
    ap.add_argument("--apply", action="store_true", help="write the work files")
    args = ap.parse_args()
    cache = args.cache or newest_cache()
    slug = os.path.basename(os.path.dirname(cache))
    source = slug

    import duckdb
    rows = duckdb.sql(f"""
        SELECT kingdom_name, name FROM read_parquet('{cache}')
        WHERE rank = 'species' AND NOT is_synonym AND name LIKE '% (%) %'""").fetchall()
    offered = collections.defaultdict(dict)
    stat = collections.Counter()
    for k, name in rows:
        kingdom = KINGDOM.get(group_of(k))
        m = SUBGENUS.match(name)
        if not kingdom or not m:
            stat["offered, not a portal kingdom or no subgenus shape"] += 1
            continue
        binomial = f"{m.group(1)} {m.group(3)}".lower()
        prev = offered[kingdom].get(binomial)
        if prev and prev != m.group(2):
            offered[kingdom][binomial] = None  # COL itself gives two
            continue
        offered[kingdom][binomial] = m.group(2)

    out = []
    for kingdom, wanted in offered.items():
        index = held(kingdom)
        for binomial, sub in wanted.items():
            if sub is None:
                stat[f"{kingdom}: COL gives two subgenera"] += 1
                continue
            nodes = index.get(binomial) or []
            if not nodes:
                stat[f"{kingdom}: not held"] += 1
            elif len(nodes) > 1:
                stat[f"{kingdom}: held more than once, skipped"] += 1
            else:
                path, nid = nodes[0][0], nodes[0][1]
                out.append({"file": path, "id": nid, "set": {"subgenus": sub}, "source": source})
                stat[f"{kingdom}: fill"] += 1
        print(f"  {kingdom:10s} {len(wanted):>8,} COL species with a subgenus", flush=True)

    for k, v in sorted(stat.items()):
        print(f"  {v:>9,}  {k}")
    if args.apply:
        work = os.path.join(sources.ROOT, "work", f"{slug}-subgenus")
        os.makedirs(work, exist_ok=True)
        with open(os.path.join(work, "enrich.jsonl"), "w", encoding="utf-8") as fh:
            for r in out:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(work, "summary.json"), "w", encoding="utf-8") as fh:
            json.dump({"cache": cache, "fills": len(out), "counts": dict(stat)}, fh, indent=1)
        print(f"  wrote {work}/enrich.jsonl  ({len(out):,} fills)")
    else:
        print("\n  (measure only -- pass --apply to write the work files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
