#!/usr/bin/env python3
"""Authors track, import: merge a source's people into the registry.

`data/authors/people.jsonl` holds one person per line, in git like the
source queue. A person's `id` is the first id a source gave them (a Wikidata
QID for Wikidata Species); `ids` is every id known for them, prefixed by
scheme where the source prefixes it (orcid:…, ipni:…). An incoming person is
the same as a registered one when any id is shared; fields are then filled
where empty, never overwritten, and ids are unioned. A person matching two
registered people is not merged and is counted -- that is a decision, not a
merge.

The species side (`authorIds` / `basionymAuthorIds`) goes through
applyEnrichment.py with the transform's links.jsonl; run that after this,
in the same maintenance session, so every id it writes resolves here
(verifyTree checks that).

    python3 scripts/applyAuthors.py <work>/people.jsonl            # dry run
    python3 scripts/applyAuthors.py <work>/people.jsonl --apply
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
from tree import ROOT  # noqa: E402

REGISTRY = os.path.join(ROOT, "data", "authors", "people.jsonl")
FIELDS = ("given", "family", "abbreviationBotany", "birth", "death", "country", "link")


def load(path=REGISTRY):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def known_ids(path=REGISTRY):
    """Every id the registry resolves -- for verifyTree."""
    return {i for p in load(path) for i in [p["id"], *p.get("ids", [])]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("people")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    def run():
        reg = load()
        by_id = {}
        for i, p in enumerate(reg):
            for x in [p["id"], *p.get("ids", [])]:
                by_id[x] = i
        stat = collections.Counter()
        with open(args.people, encoding="utf-8") as fh:
            for line in fh:
                q = json.loads(line)
                ids = [q["id"], *q.get("alternativeIds", [])]
                hits = {by_id[x] for x in ids if x in by_id}
                if len(hits) > 1:
                    stat["matches two registered people, not merged"] += 1
                    continue
                if hits:
                    at = hits.pop()
                    stat["already registered"] += 1
                else:
                    reg.append({"id": q["id"], "ids": []})
                    at = len(reg) - 1
                    stat["added"] += 1
                p = reg[at]
                for f in FIELDS:
                    if q.get(f) and not p.get(f):
                        p[f] = q[f]
                        stat[f"{f} filled"] += 1
                new = [x for x in ids if x != p["id"] and x not in p["ids"]]
                p["ids"] = sorted(set(p["ids"]) | set(new))
                src = sorted(set(p.get("sources", [])) | {q.get("source", "")} - {""})
                p["sources"] = src
                for x in ids:
                    by_id.setdefault(x, at)
        if args.apply:
            os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
            tmp = REGISTRY + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                for p in sorted(reg, key=lambda p: p["id"]):
                    fh.write(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n")
            os.replace(tmp, REGISTRY)
        stat["registry size"] = len(reg)
        return stat

    if args.apply:
        with maintenanceLock.hold_exclusive():
            stat = run()
    else:
        stat = run()
    for k, v in sorted(stat.items()):
        print(f"  {v:>9,}  {k}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
