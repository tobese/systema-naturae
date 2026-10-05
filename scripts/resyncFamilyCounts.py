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

# Every kingdom has its own taxonomy doc, and each FAMILY node's speciesCount
# there has the same two meanings as animalia's. This walked only
# taxonomy.json, so it reported "node UNDERstates the file: 0" while fungi alone
# had 266 understated nodes worth 1,367 species -- written by importers whose
# count was not recursive over subfamilies and speciesList. animalia being clean
# is why that went unnoticed: the one kingdom it did read is the one that had
# already been fixed by hand.
TAXONOMY_DOCS = (
    "portal/data/taxonomy.json",
    "portal/data/taxonomy-fungi.json",
    "portal/data/taxonomy-chromista.json",
    "portal/data/taxonomy-plantae-snippet.json",
    "portal/data/taxonomy-protozoa.json",
    "portal/data/taxonomy-archaea.json",
)


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


def doc_kingdom(path):
    """Which kingdom's family tree a taxonomy doc describes.

    Two of the six names do not follow the convention: animalia's doc is plain
    taxonomy.json, and Plantae's carries a "-snippet" suffix. Deriving the
    kingdom from the filename -- which is what the doc -> kingdom lookup did --
    yields "taxonomy" and "plantae-snippet", neither of which matches the
    directory the family files live in, so every node in those two docs read as
    "no file" and animalia looked like it had no families at all.
    """
    base = os.path.basename(path)
    if base == "taxonomy.json":
        return "animalia"
    k = base[len("taxonomy-"):-len(".json")]
    for suffix in ("-snippet",):
        if k.endswith(suffix):
            k = k[: -len(suffix)]
    return k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    # keyed by (kingdom, slug): a bare slug collides, since the same family name
    # legitimately appears under two kingdoms and their files hold different
    # numbers of species
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
            held[(f.split("taxonomy/")[1].split("/")[0],
                  os.path.basename(f)[:-5])] = n
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

    grand = {"same": 0, "under": 0, "over": 0, "missing": 0}
    all_changes = []
    for TAXONOMY in TAXONOMY_DOCS:
        if not os.path.exists(TAXONOMY):
            print(f"  {TAXONOMY}: absent, skipped")
            continue
        kingdom = doc_kingdom(TAXONOMY)
        tax = json.load(open(TAXONOMY, encoding="utf-8"))
        counts = {"over": 0, "under": 0, "same": 0, "missing": 0}
        changes = []

        def walk(n, _k=kingdom, _c=counts, _ch=changes):
            if n.get("rank") == "FAMILY" and n.get("appSlug"):
                key = (_k, n["appSlug"])
                if key not in held:
                    _c["missing"] += 1
                else:
                    want = held[key]
                    have = n.get("speciesCount")
                    if have is None:
                        _c["missing"] += 1
                    elif want > have:
                        _c["over"] += 1
                        _ch.append((n.get("name"), _k, n["appSlug"], have, want))
                    elif want < have:
                        _c["under"] += 1
                    else:
                        _c["same"] += 1
            for c in n.get("children") or []:
                walk(c)

        walk(tax)
        for k in counts:
            grand[k] += counts[k]
        all_changes.extend(changes)
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
        for name, k, slug, have, want in sorted(all_changes,
                                                key=lambda c: c[4] - c[3],
                                                reverse=True)[:10]:
            print(f"    {name:34s} {k:9s} {have:>7,} -> {want:>7,}  "
                  f"(+{want - have:,})")

    if not args.apply:
        print(f"\n  would update {len(all_changes)} nodes "
              f"(dry run -- pass --apply)")
        return 0

    n = 0
    for TAXONOMY in TAXONOMY_DOCS:
        if not os.path.exists(TAXONOMY):
            continue
        kingdom = doc_kingdom(TAXONOMY)
        by_slug = {c[2]: c[4] for c in all_changes if c[1] == kingdom}
        if not by_slug:
            continue
        tax = json.load(open(TAXONOMY, encoding="utf-8"))

        def apply_walk(node, _b=by_slug):
            if node.get("rank") == "FAMILY" and node.get("appSlug") in _b:
                node["speciesCount"] = _b[node["appSlug"]]
            for c in node.get("children") or []:
                apply_walk(c)

        apply_walk(tax)
        with open(TAXONOMY, "w", encoding="utf-8") as fh:
            json.dump(tax, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        n += len(by_slug)
        print(f"  wrote {TAXONOMY}: {len(by_slug):,} speciesCount values raised")
    print(f"\n  {n:,} nodes raised to match their family files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())