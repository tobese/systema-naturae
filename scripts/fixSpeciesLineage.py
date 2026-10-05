#!/usr/bin/env python3
"""Repair species `lineage`: fill the absent, and replace the family.

`lineage` is the immediate parent's name. annotatePortalLevels stamps FAMILY
nodes with their order and keeps `node.lineage` for species and below rather
than deriving it, so on a species it is the genus -- 1,449,923 of ours agree
with that. Two things are wrong, in opposite directions:

1. **The family instead of the genus** -- 980,786 species, from an importer that
   wrote the family name onto both levels. Because a species always lives in a
   file named for its family, the wrong value reads as correct, which is why
   `testDataContract` never caught it: it only asserts the genus case.

2. **Absent** -- 2,906 animalia species with no lineage at all. This is the only
   field-presence defect the tree-wide sanity scan found that is not coverage
   work, and it is invisible to any check that tests values rather than
   presence.

Deliberately NOT touched: a species whose lineage is neither its genus nor its
family. That is 1.17M plantae carrying a superseded genus -- Gyroporella
pauciforata has `lineage: "Physoporella"` -- which is a much larger question
about how those files were built than a repair pass should decide. Those are
counted and reported. The graph already avoids the problem by reading genus from
the tree structure rather than from this field.

The genus used to fill a blank is the GENUS node the species structurally hangs
under, not the first token of its name, so a species whose genus node is
correctly named but whose name carries an authority suffix still gets the genus.

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

    refixed = 0        # lineage was the family, now the genus
    filled = 0         # lineage was absent, now filled
    neither = 0        # left alone: neither genus nor family
    touched = 0
    left = collections.Counter()

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

        # (node, genus name from the enclosing GENUS node)
        stack = [(nd, None) for nd in reversed(d.get("children") or [])]
        while stack:
            node, genus = stack.pop()
            if node.get("rank") == "GENUS":
                genus = (node.get("name") or "").strip() or genus
            if node.get("rank") == "SPECIES":
                lin = (node.get("lineage") or "").strip().lower()
                nm = (node.get("name") or "").strip()
                from_name = nm.split()[0].lower() if nm else ""
                if not lin:
                    want = genus or from_name
                    if want:
                        if args.apply:
                            node["lineage"] = want
                        filled += 1
                        n_changed += 1
                    else:
                        left[("no name to derive from", "blank")] += 1
                elif lin == fam and from_name and from_name != fam:
                    if args.apply:
                        node["lineage"] = genus or from_name
                    refixed += 1
                    n_changed += 1
                elif lin != from_name and lin != fam:
                    neither += 1
                    left[(node.get("sourcedFrom") or "none", "neither")] += 1
                elif lin == fam:
                    left[(node.get("sourcedFrom") or "none",
                           "genus == family")] += 1
            for c in reversed(node.get("children") or []):
                stack.append((c, genus))

        if n_changed:
            touched += 1
            if args.apply:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"  lineage was the family, now the genus: {refixed:,}")
    print(f"  lineage was absent, now filled:         {filled:,}")
    print(f"  family files touched:                  {touched:,}")
    print(f"  left alone (neither genus nor family): {neither:,}")
    if left:
        print("  by source:")
        for (src, why), n in left.most_common(8):
            print(f"      {n:>8,}  [{src}] {why}")
    if neither:
        print("\n  The 'neither' bucket is the 1.17M plantae carrying a superseded\n"
              "  genus. That is a question about how those files were built, not a\n"
              "  repair, so it is reported rather than guessed at.")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
