#!/usr/bin/env python3
"""Repair species whose `lineage` holds their family name instead of their genus.

`lineage` is the parent name at each level: the family on a genus node, the
genus on a species node. 1.45M species in the tree follow that. importColChecklist.py
wrote the family onto species as well, and because a species always lives in a
file named for its family the wrong value looks plausible -- 72,270 species from
the ChecklistBank imports carry it.

Only unambiguous cases are touched: a species whose `lineage` equals the family
name of the file it sits in, and whose name starts with a different token. A
species whose lineage is neither its genus nor its family is left alone, since
something else wrote it and this does not know what it meant.

Idempotent.

    python3 scripts/fixSpeciesLineage.py
    python3 scripts/fixSpeciesLineage.py --apply
"""
import argparse
import collections
import glob
import json
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    fixed = 0
    left = collections.Counter()
    touched = 0
    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        fam = (d.get("name") or "").strip().lower()
        if not fam:
            continue
        n_changed = 0
        stack = list(d.get("children") or [])
        while stack:
            node = stack.pop()
            if node.get("rank") == "SPECIES":
                lin = (node.get("lineage") or "").strip().lower()
                nm = (node.get("name") or "").strip()
                genus = nm.split()[0].lower() if nm else ""
                if lin == fam and genus and genus != fam:
                    if args.apply:
                        node["lineage"] = genus
                    n_changed += 1
                elif lin and lin != genus and lin != fam:
                    left[(node.get("sourcedFrom") or "none", "neither")] += 1
                elif lin == fam:
                    left[(node.get("sourcedFrom") or "none", "genus==family")] += 1
            stack.extend(node.get("children") or [])
            # speciesList holds name-only species with no genus to derive
            for sp in node.get("speciesList") or []:
                lin = (sp.get("lineage") or "").strip().lower()
                if lin == fam:
                    left[(sp.get("sourcedFrom") or "none", "speciesList")] += 1
        if n_changed:
            fixed += n_changed
            touched += 1
            if args.apply:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
    print(f"  species whose lineage was the family: {fixed:,}"
          f"  across {touched:,} family files")
    if left:
        print("  left alone (not this bug):")
        for (src, why), n in left.most_common(8):
            print(f"      {n:>7,}  [{src}] {why}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
