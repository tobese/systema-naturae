#!/usr/bin/env python3
"""Move family directories to taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/.

The 258 top-level directories are a flat mix of six kingdoms, so which kingdom
a family belongs to is recorded nowhere in the filesystem - it is resolved at
build time from kingdom-config.json. That is why "do not graft plant nodes into
the animal tree" is a rule maintained by discipline rather than by the shape of
the tree. This puts kingdom in the path, and phylum with it, so every level
means the same thing everywhere.

Every path is derived by walking the kingdom's taxonomy tree. Nothing here is
hand-typed, because the prefix varies per family and a regex cannot produce it:
a family at insECta/lepidoptera/papilionidae becomes
taxonomy/animalia/arthropoda/insecta/lepidoptera/papilionidae, while a
mollusc goes to taxonomy/animalia/mollusca/gastropoda/stylommatophora/...

Three legacy shapes are in play and all three have to keep working until the
move is done:

    <class>/<order>/<family>            7,785 families
    <phylum>/<class>/<order>/<family>      24 families, reachable only through
                                        six git-tracked symlinks at the root
    <family>                              1, Tardigrada, which has no CLASS
                                        ancestor in the tree

Tardigrada stays a phylum with a family directly beneath it. Inventing a class
to make the path look uniform would be fabricating taxonomy; the resolver in
portal/scripts/lib/familyPath.ts probes variants and the shape follows the tree.

Usage:
    python3 scripts/restructureTaxonomy.py                     # plan, all kingdoms
    python3 scripts/restructureTaxonomy.py --kingdom fungi      # plan one kingdom
    python3 scripts/restructureTaxonomy.py --kingdom fungi --apply
    python3 scripts/restructureTaxonomy.py --check              # verify only
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTAL = os.path.join(ROOT, "portal")
TOP = "taxonomy"

# The six root symlinks that alias a class inside a phylum dir of the same name.
# They exist so buildData's 3-segment resolve can find those 24 families at all.
# Once everything lives under taxonomy/<kingdom>/ they are redundant, and leaving
# them would put a phantom class dir back at the root.
SYMLINKS = {
    "acoela": "xenacoelomorpha/acoela",
    "nemertodermatida": "xenacoelomorpha/nemertodermatida",
    "xenoturbellida": "xenacoelomorpha/xenoturbellida",
    "halicryptomorpha": "priapulida/halicryptomorpha",
    "priapulimorpha": "priapulida/priapulimorpha",
    "seticoronaria": "priapulida/seticoronaria",
}


def dirname_(name):
    return (name or "").lower().replace(" ", "_")


def load_kingdoms():
    cfg = json.load(open(os.path.join(PORTAL, "data", "kingdom-config.json")))["kingdoms"]
    return cfg


def plan_kingdom(kingdom, cfg):
    """[{slug, kingdom, phylum, cls, ord, rel, current}] for every family node."""
    tree = json.load(open(os.path.join(PORTAL, cfg["input"]), encoding="utf-8"))
    rows = []

    def walk(node, phylum=None, cls=None, ord_=None):
        if not isinstance(node, dict):
            return
        r = node.get("rank")
        nm = node.get("name")
        if r == "PHYLUM":
            phylum, cls = nm, None
        elif r == "CLASS":
            cls = nm
        elif r == "ORDER":
            ord_ = nm
        elif r == "FAMILY" and node.get("appSlug"):
            slug = node["appSlug"]
            p, c, o = (dirname_(phylum), dirname_(cls), dirname_(ord_))
            # Target: every level, with absent ranks simply absent.
            target = os.path.join(TOP, kingdom,
                                  *[x for x in (p, c, o) if x], slug)
            # Pre-move location, class-first. The legacy path omits the phylum in
            # the normal case (mammalia/carnivora/felidae, not chordata/mammalia/
            # carnivora/felidae); the phylum-nested shape only applies to the 24
            # families whose class shares its phylum's name, and the classless
            # shape to Tardigrada.
            if c:
                legacy = os.path.join(c, o, slug) if o else c
            else:
                legacy = slug
            rows.append({
                "slug": slug, "kingdom": kingdom, "phylum": phylum, "cls": cls,
                "ord": ord_, "name": nm, "legacy": legacy, "target": target,
                "depth": len([x for x in (p, c, o) if x]) + 1,
            })
        for c in node.get("children") or []:
            walk(c, phylum, cls, ord_)

    walk(tree)
    return rows


def find_current(root, row):
    """Where the family actually is now.

    The legacy path omits the phylum in the normal case - mammalia/carnivora/
    felidae, not chordata/mammalia/carnivora/felidae. The phylum-nested shape
    only applies to the 24 families whose class shares its phylum's name, and
    the classless shape to Tardigrada. Mirrors portal/scripts/lib/familyPath.ts.
    """
    p, c, o, slug = (dirname_(row["phylum"]), dirname_(row["cls"]),
                     dirname_(row["ord"]), row["slug"])
    cands = []
    # Already moved? The target is tried first, so a resumed run reports
    # families at their destination as done rather than as "no data on disk".
    cands.append(os.path.join(TOP, row["kingdom"], *[x for x in (p, c, o) if x], slug))
    if c:
        cands.append(os.path.join(c, o, slug) if o else c)
    if p and c:
        cands.append(os.path.join(p, c, o, slug))
    cands.append(slug)
    for cand in cands:
        if os.path.isdir(os.path.join(root, cand, "src", "data")):
            return cand
    return None


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip()


# Directories that are not the source taxonomy. Anything under one of these is
# not a family, and anything at the root that is not one of these and not a
# kingdom class dir is suspect.
NOT_TAXONOMY = ("portal", "shared", "scripts", "tools", "docs", "tasks",
                "services", "experiments", ".git", "node_modules", TOP)


def find_orphans(claimed):
    """Family data dirs on disk that no taxonomy node claims.

    Scans the whole tree including places that are normally skipped, because
    the point is to catch a family that ended up somewhere no build looks. That
    is exactly the state portal/bivalvia/ostreida/bivalvia_margaritidae is in:
    every enricher and every builder has "portal" in its skip list, so it has
    never been enriched and never would be, silently.
    """
    found = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT)
        top = rel.split(os.sep)[0]
        if top in ("node_modules", ".git", "shared", "scripts", "tools", "docs",
                   "tasks", "services", "experiments"):
            dn[:] = []
            continue
        if os.sep + "src" + os.sep + "data" + os.sep in dp:
            for f in fn:
                if f.endswith(".json"):
                    d = os.path.relpath(os.path.join(dp, f[:-5]), ROOT)
                    if d not in claimed:
                        found.append(d)
            dn[:] = []
    return sorted(found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kingdom", default="", help="limit to one kingdom")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true", help="verify only, never move")
    ap.add_argument("--show", type=int, default=6, help="example moves to print")
    args = ap.parse_args()

    cfg = load_kingdoms()
    kingdoms = [args.kingdom] if args.kingdom else sorted(cfg)
    for k in kingdoms:
        if k not in cfg:
            sys.exit(f"unknown kingdom {k!r}; have {sorted(cfg)}")

    by_kingdom = {}
    problems = []
    declared_no_data = []
    for k in kingdoms:
        rows = plan_kingdom(k, cfg[k])
        for r in rows:
            r["current"] = find_current(ROOT, r)
            if r["current"] is None:
                # The taxonomy declares more families than have data files. That
                # is normal - it is what the "758 empty families" WoRMS work is
                # about - so it is counted rather than treated as a failure.
                declared_no_data.append((k, r["slug"]))
                continue
            # A real conflict is a target that exists while the family is still
            # somewhere else. current == target just means a resumed run already
            # moved it, which is not a problem.
            if r["current"] != r["target"] and os.path.isdir(os.path.join(ROOT, r["target"])):
                problems.append((k, r["slug"], f"target occupied: {r['target']}"))
        by_kingdom[k] = rows

    print(f"{'kingdom':10} {'declared':>9} {'moves':>7} {'no data':>8}  target depths")
    total_moves = 0
    for k, rows in by_kingdom.items():
        moves = [r for r in rows if r["current"] and r["current"] != r["target"]]
        nodata = sum(1 for r in rows if not r["current"])
        total_moves += len(moves)
        depths = Counter(r["depth"] for r in rows if r["current"])
        ds = " ".join(f"{d}L={c}" for d, c in sorted(depths.items()))
        print(f"{k:10} {len(rows):>9,} {len(moves):>7,} {nodata:>8,}  {ds}")

    # Slug collisions within a kingdom would silently overwrite each other.
    for k, rows in by_kingdom.items():
        seen = defaultdict(list)
        for r in rows:
            if r["current"]:
                seen[r["target"]].append(r["slug"])
        for target, slugs in seen.items():
            if len(slugs) > 1:
                problems.append((k, ",".join(sorted(slugs)), f"target collision: {target}"))

    # The reverse check. Every family data file on disk must be claimed by
    # exactly one taxonomy node, or no kingdom will ever build it and it
    # disappears from the portal without a single error. This is how the
    # misfiled portal/bivalvia/... family gets found.
    claimed = {r["current"] for rows in by_kingdom.values() for r in rows if r["current"]}
    orphans = find_orphans(claimed)
    print(f"\ntotal moves       : {total_moves:,}")
    print(f"declared, no data : {len(declared_no_data):,}   "
          f"(taxonomy outruns the data; these graft empty today)")
    print(f"orphan data files : {len(orphans):,}   (on disk but claimed by no taxonomy)")
    for o in orphans[:20]:
        print(f"  ORPHAN {o}")

    if problems:
        print(f"\n{len(problems)} PROBLEMS")
        for k, slug, msg in problems[:25]:
            print(f"  [{k}] {slug}: {msg}")
        sys.exit(1)

    print(f"\ntotal moves: {total_moves:,}")
    for k, rows in by_kingdom.items():
        moves = [r for r in rows if r["current"] != r["target"]][:args.show]
        if not moves:
            continue
        print(f"\n{k} examples:")
        for r in moves:
            print(f"  {r['current']}")
            print(f"  -> {r['target']}")

    if args.check:
        print("\ncheck only; nothing moved")
        return
    if not args.apply:
        print("\n(dry run - pass --apply)")
        return

    moved = 0
    for k, rows in by_kingdom.items():
        # `r["current"]` must be truthy: a family declared by the taxonomy with no
        # file on disk has current=None, and None != target, so a filter on
        # inequality alone let those through and git mv was handed a None path
        # part-way through a kingdom.
        kmoves = [r for r in rows if r["current"] and r["current"] != r["target"]]
        if not kmoves:
            continue
        # Deepest first so we never move a parent directory out from under a
        # child we have not moved yet.
        kmoves.sort(key=lambda r: -r["depth"])
        # Stage the old paths too. A `git mv` records both sides, but the caller
        # stages by path, and staging only taxonomy/<kingdom> leaves the old
        # files tracked in the index - the commit then *copies* the family
        # instead of moving it, and the next status shows every old path as an
        # unstaged deletion. That is what happened to archaea, chromista and
        # fungi the first time.
        for r in kmoves:
            dest = os.path.join(ROOT, r["target"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            git("mv", r["current"], r["target"])
            moved += 1
        # git mv stages both sides, so nothing extra is needed for the move
        # itself. What the caller must not do is commit with a pathspec of
        # taxonomy/<kingdom> alone: that records the new files and leaves the
        # old ones tracked in the index, so the commit copies rather than
        # moves. Stage everything and commit it all - at this point the only
        # pending changes are this kingdom's.
        git("add", "-A")
        print(f"  {k}: moved {len(kmoves):,} families (staged; commit without a pathspec)")

    print(f"\nmoved {moved:,} family directories")
    print("next: rebuild, then re-run with --check to confirm nothing is left")


if __name__ == "__main__":
    main()
