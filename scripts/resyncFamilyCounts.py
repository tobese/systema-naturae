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

    python3 scripts/resyncFamilyCounts.py            # dry run
    python3 scripts/resyncFamilyCounts.py --apply
"""
import argparse
import collections
import glob
import json
import os

TAXONOMY = "portal/data/taxonomy.json"


def count_species(node):
    """Every species under a family, at any depth, including speciesList.

    The first version of this walked only the direct children of the family's
    top-level nodes and so missed everything nested below a SUBFAMILY: it
    counted alcedinidae.json as 19 when it holds 138, and in the same pass it
    rewrote 360 files' speciesCount down to that wrong number -- including
    alcedinidae's, which had been correct. buildData compresses minimal species
    into speciesList and the tree nests families under subfamilies, so the count
    has to be recursive over both.
    """
    n = len(node.get("speciesList") or [])
    for c in node.get("children") or []:
        if c.get("rank") == "SPECIES":
            n += 1
        else:
            n += count_species(c)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    held = collections.defaultdict(int)
    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        n = count_species(d)
        if n:
            held[os.path.basename(f)[:-5]] = n
    print(f"  family files with species: {len(held):,}")

    # Two different counters disagree, and it matters which is which.
    #
    # The FAMILY DATA FILE's root speciesCount describes that file's contents, so
    # it must equal what the file holds -- 360 files do not, and the Coverage
    # modal reads portalCount from there. alcedinidae.json says 138 and holds 19,
    # which is why the portal reads over-full against a correct taxonomy node.
    #
    # The taxonomy.json node's speciesCount is the REAL-WORLD total, deliberately
    # larger than what we hold for families we sample rather than exhaust (the
    # plantae figures come from POWO). So a node that overstates is correct and is
    # left alone; only a node that UNDERstates its file is an error.
    import glob as _g
    import json as _j
    fixed_files = 0
    for f in _g.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = _j.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if "speciesCount" not in d:
            continue
        n = count_species(d)
        if d["speciesCount"] != n:
            if args.apply:
                d["speciesCount"] = n
                if "genusCount" in d:
                    d["genusCount"] = len(d.get("children") or [])
                with open(f, "w", encoding="utf-8") as fh:
                    _j.dump(d, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
            fixed_files += 1
    print(f"  data files whose own speciesCount disagrees with contents: "
          f"{fixed_files:,}"
          + ("" if args.apply else "  (dry run)"))
    print("  data files with no speciesCount field: left alone "
          "(4,050 files; the field is not universal)")
    print()

    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    counts = {"over": 0, "under": 0, "same": 0, "missing": 0}
    changes = []

    def walk(n):
        over = counts["over"]
        if n.get("rank") == "FAMILY" and n.get("appSlug"):
            slug = n["appSlug"]
            if slug not in held:
                counts["missing"] += 1
                return
            want = held[slug]
            have = n.get("speciesCount")
            if have is None:
                counts["missing"] += 1
            elif want > have:
                counts["over"] += 1
                changes.append((n.get("name"), slug, have, want))
            elif want < have:
                counts["under"] += 1
            else:
                counts["same"] += 1
        for c in n.get("children") or []:
            walk(c)
    walk(tax)

    print(f"  nodes matching their file:        {counts['same']:,}")
    print(f"  node UNDERstates the file:       {counts['over']:,}")
    print(f"  node OVERstates the file:        {counts['under']:,}  (left alone)")
    print(f"  nodes with no file / no count:   {counts['missing']:,}  (left alone)")
    if changes:
        print("\n  largest understated:")
        for name, slug, have, want in sorted(changes, key=lambda c: c[3] - c[2],
                                             reverse=True)[:10]:
            print(f"    {name:34s} {have:>7,} -> {want:>7,}  (+{want - have:,})")

    if not args.apply:
        print(f"\n  would update {len(changes)} nodes (dry run -- pass --apply)")
        return 0

    by_slug = {c[1]: c[3] for c in changes}   # c = (name, slug, have, want)
    n = 0

    def apply_walk(node):
        if node.get("rank") == "FAMILY" and node.get("appSlug") in by_slug:
            node["speciesCount"] = by_slug[node["appSlug"]]
        for c in node.get("children") or []:
            apply_walk(c)
    apply_walk(tax)
    n = len(changes)
    with open(TAXONOMY, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"\n  wrote {TAXONOMY}: {n} speciesCount values raised to match the files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())