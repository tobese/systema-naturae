#!/usr/bin/env python3
"""Apply a nomenclatural source's fills (nomenclatureTransform.py's
enrich.jsonl) to the family files: set a field only where the species has
none, and add the source's id to sourceIds. Adds no species, removes none,
and never overwrites -- a disagreement is the transform's review file, not
an edit here.

Each record: {"file", "id", "set": {field: value}, "source", "sourceId"?}.
Checked again at write time, under maintenanceLock: a field filled since the
transform ran is left alone and counted, a node no longer in its file is
skipped and counted. Per file the species count must not change.

    python3 scripts/applyEnrichment.py <work>/enrich.jsonl            # dry run
    python3 scripts/applyEnrichment.py <work>/enrich.jsonl --apply
"""
import argparse
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
from tree import ROOT, count_species, iter_species, save_json  # noqa: E402

# subgenus: a field on the species, not a tree level (docs/sub-ranks-plan.md).
# authorIds / basionymAuthorIds: the authors track (docs/authors-track-plan.md);
# every id must resolve in data/authors/people.jsonl (verifyTree).
FIELDS = {"authorship", "yearPublished", "subgenus", "authorIds", "basionymAuthorIds"}
# Its own log: import-log.jsonl is one record per import, read as such by
# verifyTree and the dashboards.
LOG = os.path.join(ROOT, "data", "enrichment-log.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("enrich")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    by_file = collections.defaultdict(list)
    sources = set()
    with open(args.enrich, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if set(r.get("set") or {}) - FIELDS:
                sys.exit(f"FATAL: {r['id']}: only {sorted(FIELDS)} may be filled, got {sorted(r['set'])}")
            by_file[r["file"]].append(r)
            sources.add(r["source"])
    print(f"  {sum(map(len, by_file.values())):,} fills across {len(by_file):,} family files "
          f"from {', '.join(sorted(sources))}")

    def run():
        stat = collections.Counter()
        for rel, recs in sorted(by_file.items()):
            path = os.path.join(ROOT, rel)
            try:
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError):
                stat["file missing or unreadable"] += len(recs)
                continue
            before = count_species(doc)
            nodes = {sp.get("id"): sp for sp in iter_species(doc)}
            changed = False
            for r in recs:
                sp = nodes.get(r["id"])
                if sp is None:
                    stat["node gone"] += 1
                    continue
                for field, value in r["set"].items():
                    if sp.get(field) not in (None, "", []):
                        stat[f"{field} already set"] += 1
                        continue
                    sp[field] = value
                    stat[f"{field} filled"] += 1
                    changed = True
                if r.get("sourceId"):
                    ids = sp.setdefault("sourceIds", {})
                    if r["source"] not in ids:
                        ids[r["source"]] = r["sourceId"]
                        stat["sourceId added"] += 1
                        changed = True
            if count_species(doc) != before:
                sys.exit(f"FATAL: species count changed in {rel}; nothing more written")
            if changed:
                stat["files written"] += 1
                if args.apply:
                    save_json(path, doc)
        return stat

    if args.apply:
        with maintenanceLock.hold_exclusive():
            stat = run()
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "action": "enrich", "sources": sorted(sources),
                                 "input": os.path.relpath(args.enrich, ROOT) if args.enrich.startswith(ROOT) else args.enrich,
                                 "counts": dict(stat)}, ensure_ascii=False) + "\n")
    else:
        stat = run()
    for k, v in stat.most_common():
        print(f"  {v:>10,}  {k}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
