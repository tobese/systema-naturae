#!/usr/bin/env python3
"""Resync taxonomy.json speciesCount with what the family files actually hold.

`speciesCount` on a FAMILY node is the real-world total the Coverage modal
divides by, while the family data file holds what we actually have. They are
written by different code: the importers update the node when they add to a
family, but a family can gain species by other routes, and a merge that adds
nothing still leaves a node that was already behind.

The assertion `coverage portalCount never exceeds totalCount` is what catches it,
and it is not cosmetic: a family holding 138 species against a stated total of 19
reads as over-full in the UI, and the gap-report computes every percentage from
the node.

The session notes recorded 24 families in this state after the Stage 2 import.
Wikispecies took it to 102, because it added species across 2,493 family files
while only updating the nodes for the families it staged.

This resyncs the node to the file, which is the direction that makes the two
agree. It does not try to guess a real-world total: we hold a sample of most
families and not all of it, so the honest number for "total species known" is a
separate judgement, and `taxonomy-plantae-snippet.json` in particular carries
speciesCounts from POWO that are larger than anything we hold on purpose.

Joining by rank path, not by slug
----------------------------------
This used to key its lookup on `(kingdom, appSlug)`, and reported "understated
0" for fungi while `verifyTree.py` reported 27 understated families worth 3,307
species -- on the same data, at the same time. Both were right about their own
code and the data said otherwise.

The reason is that `appSlug` is not unique. **87** fungi family directories are
all called `incertae-sedis` (the largest holds 1,220 species) and 12 chromista
ones are, so a slug-keyed dict kept one file per kingdom and compared all 27
nodes against that single file. The 27 that "matched" matched a sibling's count.
Families are resolved by rank path instead, via `tree.resolve_family_file`,
which is the Python mirror of the build's `familyPath.ts`.

    python3 scripts/resyncFamilyCounts.py            # dry run
    python3 scripts/resyncFamilyCounts.py --apply
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
from tree import (  # noqa: E402
    KINGDOMS,
    count_species,
    iter_family_files,
    iter_family_nodes,
    kingdom_input,
    resolve_family_file,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sync_file_counts(apply: bool) -> None:
    """A family file's own `speciesCount` must equal what the file holds.

    Distinct from the node's value, which is the real-world total and is
    deliberately larger for families we sample rather than exhaust. The file's
    root `speciesCount` describes the file's own contents, so there is no
    judgement call: it either matches or it is wrong.
    """
    fixed = 0
    absent = 0
    for fam in iter_family_files():
        try:
            d = fam.load()
        except Exception:
            continue
        if "speciesCount" not in d:
            absent += 1
            continue
        n = count_species(d)
        if d["speciesCount"] == n:
            continue
        if apply:
            d["speciesCount"] = n
            if "genusCount" in d:
                d["genusCount"] = len(d.get("children") or [])
            fam.save(d)
        fixed += 1
    print(f"  data files whose own speciesCount disagrees with contents: "
          f"{fixed:,}" + ("" if apply else "  (dry run)"))
    print(f"  data files with no speciesCount field: left alone "
          f"({absent:,} files; the field is not universal)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.apply:
        with maintenanceLock.hold_exclusive():
            return _run(args)
    return _run(args)


def _run(args) -> int:
    sync_file_counts(args.apply)
    print()

    grand = {"same": 0, "under": 0, "over": 0, "missing": 0}
    # (kingdom, doc, node, name, have, want) -- the node object itself, so that
    # applying never has to look it up again by a key that is not unique.
    all_changes = []
    dirty = {}

    for kingdom in KINGDOMS:
        rel = kingdom_input(kingdom)
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"  {rel}: absent, skipped")
            continue

        counts = {"over": 0, "under": 0, "same": 0, "missing": 0}
        changes = []
        # One load of the taxonomy document, held for the whole kingdom, so the
        # nodes classified below are the same objects that get written back.
        doc = json.load(open(path, encoding="utf-8"))
        for node, ranks in iter_family_nodes(kingdom, doc):
            slug = node.get("appSlug")
            if not slug:
                continue
            resolved = resolve_family_file(**ranks, slug=slug)
            if resolved is None:
                counts["missing"] += 1
                continue
            try:
                want = count_species(json.load(open(resolved, encoding="utf-8")))
            except Exception:
                counts["missing"] += 1
                continue
            have = node.get("speciesCount")
            if have is None:
                counts["missing"] += 1
            elif want > have:
                counts["over"] += 1
                changes.append((kingdom, doc, node, node.get("name"), have, want))
            elif want < have:
                counts["under"] += 1
            else:
                counts["same"] += 1

        for k in counts:
            grand[k] += counts[k]
        all_changes.extend(changes)
        if changes:
            dirty[kingdom] = doc
        flag = "" if not counts["over"] else f"   <-- {counts['over']} understated"
        print(f"  {kingdom:10s} matching {counts['same']:>6,}   "
              f"understated {counts['over']:>4,}   "
              f"correctly larger {counts['under']:>5,}   "
              f"no file {counts['missing']:>4,}{flag}")

    print(f"\n  TOTAL: matching {grand['same']:,}   "
          f"understated {grand['over']:,}   "
          f"correctly larger {grand['under']:,}   "
          f"no file {grand['missing']:,}")
    if all_changes:
        print("\n  largest understated:")
        for _k, _doc, _node, name, have, want in sorted(
                all_changes, key=lambda c: c[5] - c[4], reverse=True)[:10]:
            print(f"    {str(name)[:34]:34s} {_k:9s} {have:>7,} -> {want:>7,}  "
                  f"(+{want - have:,})")

    if not args.apply:
        print(f"\n  would update {len(all_changes)} nodes "
              f"(dry run -- pass --apply)")
        return 0

    # Mutate the node objects already held, then write each kingdom's document
    # once. Keying the apply step by slug would reintroduce the collision this
    # script exists to avoid, and 27 of the nodes it just found are
    # `incertae-sedis` sharing one slug.
    for _kingdom, _doc, node, _name, _have, want in all_changes:
        node["speciesCount"] = want

    for kingdom, doc in dirty.items():
        path = os.path.join(ROOT, kingdom_input(kingdom))
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        n = sum(1 for c in all_changes if c[0] == kingdom)
        print(f"  wrote {kingdom_input(kingdom)}: {n:,} speciesCount values raised")

    print(f"\n  {len(all_changes):,} nodes raised to match their family files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())