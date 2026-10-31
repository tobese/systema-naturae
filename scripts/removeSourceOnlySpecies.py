#!/usr/bin/env python3
"""Remove listed species whose only provenance is one source.

For a source found to place species wrongly after it was applied: the 13
species ChecklistBank 2231 ("Linnaean Plant Names and their Types", part L)
alone supports on 2026-10-31 include Taraxacum officinale in Boraginaceae and
the lichen genus Collema in Goodeniaceae. A species that any other source
also supports is left alone -- the source's id on it is provenance, not the
reason it exists.

Only species named in a decisions file are removed (data/source-only-
removals-*.json, each entry with the evidence for it): "the source alone
supports it" is not a reason by itself. Of 2231's twelve, three are the tree's
only or correctly placed copy, and removing them would delete good records.

quarantineSourceAdditions.py answers a different question (what did a run add
since HEAD), by reading every family at HEAD through git: right for undoing a
whole import, an hour's work for a handful of known species. This reads the
working tree only.

Same safeguards as dedupeNamesAgainstCol.py's apply: removal by object
identity; only containers these removals empty are pruned; every file's
species count must drop by exactly its planned removals or nothing is written.

    python3 scripts/removeSourceOnlySpecies.py --decisions data/source-only-removals-2026-10-31.json
    python3 scripts/maintenanceSession.py --run "python3 scripts/removeSourceOnlySpecies.py \\
        --decisions data/source-only-removals-2026-10-31.json --apply"
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
from tree import (KINGDOMS, count_rank, count_species, iter_family_files,  # noqa: E402
                  save_json)


def _walk(doc):
    """(parent, list key, node) for every node under doc."""
    stack = [doc]
    while stack:
        node = stack.pop()
        for key in ("children", "speciesList"):
            for child in node.get(key) or []:
                yield node, key, child
                stack.append(child)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", required=True,
                    help="JSON with `source` and a `remove` list of {family, name}")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    with open(args.decisions, encoding="utf-8") as fh:
        decisions = json.load(fh)
    source = decisions["source"]
    wanted = {(d["family"], d["name"]) for d in decisions["remove"]}
    seen = set()

    planned = written = pruned = 0
    for k in KINGDOMS:
        for fam in iter_family_files(k):
            with open(fam.path, encoding="utf-8") as fh:
                doc = json.load(fh)
            parent_of, hits = {}, []
            for parent, key, node in _walk(doc):
                parent_of[id(node)] = (parent, key)
                if (node.get("rank") == "SPECIES"
                        and (fam.slug, node.get("name")) in wanted
                        and set(node.get("sourceIds") or {}) == {source}):
                    hits.append((parent, key, node))
                    seen.add((fam.slug, node.get("name")))
            if not hits:
                continue
            for _p, _k, node in hits:
                print(f"  {k:10s} {fam.slug:22s} {node.get('name')}  "
                      f"{node.get('authorship') or ''}")
            planned += len(hits)
            if not args.apply:
                continue
            before = count_species(doc)
            emptied = []
            for parent, key, node in hits:
                parent[key] = [c for c in parent[key] if c is not node]
                emptied.append(parent)
            for node in emptied:
                while (node is not doc and node.get("rank") != "FAMILY"
                       and not node.get("children") and not node.get("speciesList")):
                    up, key = parent_of[id(node)]
                    up[key] = [c for c in up[key] if c is not node]
                    pruned += 1
                    node = up
            if before - count_species(doc) != len(hits):
                print(f"  MISMATCH {fam.path}: {before} -> {count_species(doc)}, "
                      f"planned {len(hits)}; this file NOT written")
                return 1
            doc["speciesCount"] = count_species(doc)
            doc["genusCount"] = count_rank(doc, "GENUS")
            save_json(fam.path, doc)
            written += 1
    for fam_slug, name in sorted(wanted - seen):
        print(f"  not found as a {source}-only species, left alone: "
              f"{fam_slug} {name}")
    if args.apply:
        print(f"\n  removed {planned:,} species from {written:,} files, "
              f"pruned {pruned:,} emptied containers")
    else:
        print(f"\n  {planned:,} of {len(wanted)} listed species found "
              f"(dry run -- pass --apply to remove)")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        with maintenanceLock.hold_exclusive():
            sys.exit(main())
    sys.exit(main())
