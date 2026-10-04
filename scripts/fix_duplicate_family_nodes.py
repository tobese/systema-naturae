#!/usr/bin/env python3
"""Fold family nodes that exist twice under one appSlug into a single family.

The COL Stage 2 import scaffolds a FAMILY node wherever COL's rank chain puts
the family, and it can only match a family we already hold when the *same parent
order* holds it. 23 insect families are held already and COL puts them somewhere
else -- Progonocimicidae under Coleorrhyncha for us, under Hemiptera for COL --
so the run added a second FAMILY node with the same appSlug and a second data
directory next to the first:

    insecta/coleorrhyncha/progonocimicidae/   59 species, curated, tracked
    insecta/hemiptera/progonocimicidae/       21 species, written by the run

Both graft, both render, and `testFamilyPaths` counts them twice. Measured
across all 23, the two copies share exactly one species name, so merging is
141 species gained and nothing lost. `personidae` is also an appSlug seen twice
but is left alone: that one is a real name collision between an insect family
in Grylloblattodea and a gastropod family in Littorinimorpha, both pre-existing,
and the two are unrelated animals.

Target selection: the copy whose file git already tracks, i.e. the curated one,
so the merge keeps the existing placement, its subfamily structure and its
extinct marker. Only when both copies are untracked does it fall back to the
larger file.

    python3 scripts/fix_duplicate_family_nodes.py
    python3 scripts/fix_duplicate_family_nodes.py --apply
"""
import argparse
import collections
import json
import os
import subprocess
import sys

TAXONOMY = "portal/data/taxonomy.json"
RANK_ORDER = ("KINGDOM", "PHYLUM", "CLASS", "ORDER", "FAMILY")


def dirname(name):
    """Mirror of dirName() in portal/scripts/lib/familyPath.ts."""
    return "_".join((name or "").lower().split())


def candidates(kingdom, path, slug):
    """Mirror of candidatePaths() in portal/scripts/lib/familyPath.ts: the rank
    path is a preference order, not a fixed shape, because Tardigrada has no
    class and no order."""
    p, c, o = ([dirname(x) for x in path] + ["", "", ""])[:3]
    out, seen = [], set()
    for tail in ([p, c, o], [c, o], [p, o], [p, c], [p], [c], []):
        segs = [s for s in tail if s] + [slug]
        rel = os.path.join("taxonomy", dirname(kingdom), *segs, "src", "data",
                           slug + ".json")
        if rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


def data_path(kingdom, path, slug):
    """The family data file the graft would read, mirroring resolveFamilyFile()."""
    for rel in candidates(kingdom, path, slug):
        if os.path.exists(rel):
            return rel
    return candidates(kingdom, path, slug)[0]


def norm(name):
    return (name or "").lstrip("†").strip().lower()


def tracked():
    return set(subprocess.run(["git", "ls-files", "taxonomy"],
                              capture_output=True, text=True).stdout.split())


def collect(tax):
    """Every FAMILY node with an appSlug, with the rank path above it."""
    fams = []

    def walk(n, path):
        rank = n.get("rank")
        here = path + [n.get("name")]
        if rank == "FAMILY" and n.get("appSlug"):
            fams.append({"slug": n["appSlug"], "path": here[1:-1],
                         "node": n, "parent": None})
            for c in n.get("children") or []:
                walk(c, here)
            return
        for c in n.get("children") or []:
            walk(c, here)

    walk(tax, [])
    return fams


def link_parents(tax, fams):
    """Attach each family to the node whose children list holds it, so a
    duplicate can be removed from the right place."""
    def walk(n):
        for c in n.get("children") or []:
            for f in fams:
                if f["node"] is c:
                    f["parent"] = n
            walk(c)
    walk(tax)


def find_genera(node, out):
    if node.get("rank") == "GENUS":
        out.append(node)
    for c in node.get("children") or []:
        find_genera(c, out)
    return out


def species_names(node, out):
    if node.get("rank") == "SPECIES":
        out.append(norm(node.get("name")))
    for c in node.get("children") or []:
        species_names(c, out)
    return out


def merge_file(target_path, dup_path):
    """(added, skipped) species from the duplicate file into the target. A
    duplicate whose file is already gone -- an interrupted earlier run -- folds
    in nothing and is still removed from the tree."""
    target = json.load(open(target_path, encoding="utf-8"))
    dup = json.load(open(dup_path, encoding="utf-8")) if os.path.exists(dup_path) else None
    held = set(species_names(target, []))
    genera = {norm(g.get("name")): g for g in find_genera(target, [])}

    added = skipped = 0
    for sp in species_names_nodes(dup) if dup else []:
        key = norm(sp.get("name"))
        if key in held:
            skipped += 1
            continue
        genus = key.split(" ")[0]
        gnode = genera.get(genus)
        if gnode is None:
            gnode = {"id": "GEN_" + genus.upper(), "name": genus,
                     "rank": "GENUS", "lineage": target.get("name"),
                     "children": []}
            target.setdefault("children", []).append(gnode)
            genera[genus] = gnode
        sp = dict(sp)
        sp["sourcedFrom"] = "catalogue of life"
        gnode.setdefault("children", []).append(sp)
        held.add(key)
        added += 1

    target["speciesCount"] = len(held)
    target["genusCount"] = len(find_genera(target, []))
    with open(target_path, "w", encoding="utf-8") as fh:
        json.dump(target, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return added, skipped


def species_names_nodes(node, out=None):
    if out is None:
        out = []
    if node.get("rank") == "SPECIES":
        out.append(node)
    for c in node.get("children") or []:
        species_names_nodes(c, out)
    return out


def empty_ranks(tax):
    """Ids of every ORDER/CLASS/PHYLUM node that is already empty, so pruning
    can stay out of business it was not called for. `Priapulida > Halicrypto-
    morpha > Halicryptomorpha` is one: an order named after its own class, empty
    since before this data existed, and not this script's to delete."""
    out = set()

    def walk(n):
        for c in n.get("children") or []:
            if c.get("rank") in ("ORDER", "CLASS", "PHYLUM"):
                if not c.get("children") and c.get("id"):
                    out.add(c["id"])
                walk(c)
    walk(tax)
    return out


def prune(tax, keep):
    """Drop ORDER/CLASS/PHYLUM nodes left holding nothing but families we just
    removed. Reculida held seven families, all seven duplicates, so the order
    goes with them -- COL still lists it, we simply carry none of it uniquely."""
    dropped = []

    def walk(n):
        for c in list(n.get("children") or []):
            if c.get("rank") in ("ORDER", "CLASS", "PHYLUM"):
                walk(c)
                if not c.get("children") and c.get("id") not in keep:
                    n["children"].remove(c)
                    dropped.append(" > ".join(
                        [n.get("name") or "", c.get("name") or ""]).strip(" >"))
            else:
                walk(c)
    walk(tax)
    return dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    kingdom = tax.get("name") or "Animalia"
    fams = collect(tax)
    link_parents(tax, fams)

    groups = {}
    for f in fams:
        groups.setdefault(f["slug"], []).append(f)
    dupes = {s: g for s, g in groups.items() if len(g) > 1}
    if not dupes:
        print("  no duplicate family nodes")
        return 0

    keep_empty = empty_ranks(tax)
    git_tracked = tracked()
    print(f"  family nodes: {len(fams):,}")
    print(f"  appSlugs held by more than one node: {len(dupes):,}")

    plan, skipped_groups = [], []
    for slug, group in sorted(dupes.items()):
        rows = []
        for f in group:
            p = data_path(kingdom, f["path"], f["slug"])
            rows.append({"path": p, "exists": os.path.exists(p),
                         "tracked": p in git_tracked, "fam": f})
        # The curated copy is the one git already tracks; every other copy was
        # written by the run that created the duplicate.
        old = [r for r in rows if r["exists"] and r["tracked"]]
        fresh = [r for r in rows if r not in old]
        if not old:
            skipped_groups.append((slug, "no tracked copy to merge into"))
            continue
        if not fresh:
            skipped_groups.append((slug, "every copy pre-existing, nothing to fold"))
            continue
        target = max(old, key=lambda r: os.path.getsize(r["path"]))
        for dup in fresh:
            plan.append({"slug": slug, "target": target, "dup": dup})

    for slug, why in skipped_groups:
        print(f"  leaving {slug} alone: {why}")
    if not plan:
        return 0

    print(f"\n  merging {len(plan):,} duplicate families:")
    for p in plan:
        t = json.load(open(p["target"]["path"], encoding="utf-8"))
        d = (json.load(open(p["dup"]["path"], encoding="utf-8"))
             if p["dup"]["exists"] else {})
        print(f"    {p['slug']:22} keep {p['target']['fam']['path'][-1]:>14}"
              f" ({len(species_names(t, [])):>3} sp)"
              f"   fold {p['dup']['fam']['path'][-1]:>14}"
              f" ({len(species_names(d, [])):>3} sp)")

    if not args.apply:
        print("\n  dry run -- pass --apply to write")
        return 0

    total_added = total_skipped = 0
    for p in plan:
        added, skipped = merge_file(p["target"]["path"], p["dup"]["path"])
        total_added += added
        total_skipped += skipped
        fam = p["dup"]["fam"]
        fam["parent"]["children"].remove(fam["node"])
        if not p["dup"]["exists"]:
            continue
        os.remove(p["dup"]["path"])
        d = os.path.dirname(os.path.dirname(p["dup"]["path"]))
        for sub in ("src/data", "src"):
            sub_dir = os.path.join(d, sub)
            if os.path.isdir(sub_dir):
                try:
                    os.rmdir(sub_dir)
                except OSError:
                    # A family with its own App.tsx/colors.ts is a standalone
                    # sub-app; leave the directory alone rather than delete work.
                    print(f"    kept {sub_dir} (not empty)")

    dropped = prune(tax, keep_empty)
    with open(TAXONOMY, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    left = collections.Counter(f["slug"] for f in collect(tax))
    still = sorted(s for s, c in left.items() if c > 1)
    print(f"\n  species added:   {total_added:,}")
    print(f"  already held:    {total_skipped:,}")
    print(f"  family nodes removed: {len(plan):,}")
    print(f"  ranks dropped:   {', '.join(dropped) if dropped else 'none'}")
    print(f"  appSlugs still held twice: {', '.join(still) if still else 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())