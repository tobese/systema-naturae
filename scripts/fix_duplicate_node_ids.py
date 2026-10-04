#!/usr/bin/env python3
"""Make node ids unique inside every kingdom taxonomy.

`SF.node_id(prefix, name)` builds an id from the name alone, which is unique for
a real taxon name and useless for a placeholder. The COL Stage 2 import scaffolds
an order or family literally called `Incertae sedis` wherever COL declines to
say where a taxon sits, and every one of those placeholders got the same id:

    animalia   ORDER_INCERTAE_SEDIS  x21
    fungi      ORDER_INCERTAE_SEDIS  x21,  FAM_INCERTAE_SEDIS x91
    chromista  ORDER_INCERTAE_SEDIS  x3,   FAM_INCERTAE_SEDIS x12

Ids are not decoration. `findNodeById` resolves one node and the manifest keys
order files by order id, so 21 orders sharing an id means 20 of them never get an
entry: the build wrote 721 order files and the manifest came out with 701, and
the 20 families under them are unreachable from the UI. 91 families sharing
`FAM_INCERTAE_SEDIS` breaks node lookup and the coverage roll-up the same way.

The fix qualifies the colliding ids with their ancestry, in the style the tree
already uses for `SCAPHOPODA_UNKNOWN`: the parent's name, then the grandparent's
if that is not enough, then a counter. So `FAM_INCERTAE_SEDIS` under Dothideales
becomes `DOTHIDEALES_INCERTAE_SEDIS`, and one under an order that is itself
duplicated takes the class as well.

Only ids that actually collide are touched, and a family data file's own root id
is updated to match its taxonomy node -- the build discards it (`graftFamily`
returns the taxonomy node) but the source should not contradict the tree.

    python3 scripts/fix_duplicate_node_ids.py
    python3 scripts/fix_duplicate_node_ids.py --apply
"""
import argparse
import collections
import json
import os
import re
import sys

TAXONOMIES = [
    "portal/data/taxonomy.json",
    "portal/data/taxonomy-fungi.json",
    "portal/data/taxonomy-chromista.json",
    "portal/data/taxonomy-plantae.json",
    "portal/data/taxonomy-protozoa.json",
    "portal/data/taxonomy-archaea.json",
]
ID_RE = re.compile(r"[^A-Za-z0-9]+")


def slug(name):
    return ID_RE.sub("_", (name or "").replace("†", "")).strip("_").upper()


def walk(node, path=()):
    yield node, path
    for c in node.get("children") or []:
        yield from walk(c, path + (node,))


def resolve(taken, node, path):
    """A unique id for `node`, qualified by as much ancestry as it needs."""
    body = slug(node.get("name"))
    for depth in (1, 2, 3):
        prefix = "_".join(slug(a.get("name")) for a in reversed(path[-depth:]))
        cand = f"{prefix}_{body}" if prefix else body
        if cand not in taken:
            return cand
    n = 2
    while f"{slug(path[-1].get('name'))}_{body}_{n}" in taken:
        n += 1
    return f"{slug(path[-1].get('name'))}_{body}_{n}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed_files = 0
    for path in TAXONOMIES:
        if not os.path.exists(path):
            continue
        tax = json.load(open(path, encoding="utf-8"))
        nodes = list(walk(tax))
        counts = collections.Counter(n.get("id") for n, _ in nodes if n.get("id"))
        dupes = {i for i, c in counts.items() if c > 1}
        rewrote = False
        if not dupes:
            print(f"  {os.path.basename(path):28} {len(nodes):>6,} nodes, ids unique")
        else:
            # `taken` starts as every id used exactly once: those keep their id
            # and must not be handed out again to a node being renamed.
            taken = {i for i, c in counts.items() if c == 1}
            renames = []
            for node, anc in nodes:
                if node.get("id") not in dupes:
                    continue
                new = resolve(taken, node, anc)
                renames.append((node, anc, node["id"], new))
                taken.add(new)

            print(f"  {os.path.basename(path):28} {len(nodes):>6,} nodes, "
                  f"{len(dupes):,} ids collide -> {len(renames):,} nodes renamed")
            for node, anc, old, new in renames[:4]:
                where = " > ".join(a.get("name") or "" for a in anc)
                print(f"      {old:28} -> {new:34} under {where}")
            if len(renames) > 4:
                print(f"      ... and {len(renames) - 4:,} more")
            changed_files += 1
            if args.apply:
                for node, anc, old, new in renames:
                    node["id"] = new
                rewrote = True

        # Every family, renamed or not: a data file still carrying an id that
        # other families also carry is a leftover of the collision, and the tree
        # is the authority on what it should be. The build ignores the id --
        # graftFamily returns the taxonomy node -- so nothing catches this, but
        # the source should not contradict the tree it feeds.
        #
        # Only ids shared by more than one file are touched. 140 animalia family
        # files disagree with their node on their own, uniquely (`cetacea.json`
        # says `CET`), and that disagreement predates any of this: it is a
        # different question from an id that means two things at once.
        fams = []
        for node, anc in nodes:
            if node.get("rank") != "FAMILY" or not node.get("appSlug"):
                continue
            fam = resolve_family_file(anc + (node,), node["appSlug"])
            if fam:
                fams.append((fam, node))
        file_ids = collections.Counter()
        for fam, _ in fams:
            file_ids[json.load(open(fam, encoding="utf-8")).get("id")] += 1
        shared = {i for i, c in file_ids.items() if c > 1}

        stale = []
        for fam, node in fams:
            data = json.load(open(fam, encoding="utf-8"))
            if data.get("id") in shared and data.get("id") != node.get("id"):
                stale.append((fam, data, node["id"]))
        if stale:
            print(f"      {len(stale):,} family data files still carry a shared "
                  f"id, e.g. {stale[0][0]}: "
                  f"{stale[0][1].get('id')} -> {stale[0][2]}")
            changed_files += 1
            if args.apply:
                for fam, data, new in stale:
                    data["id"] = new
                    with open(fam, "w", encoding="utf-8") as fh:
                        json.dump(data, fh, indent=2, ensure_ascii=False)
                        fh.write("\n")

        if args.apply and (rewrote or stale):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(tax, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    print(f"\n  taxonomies needing a rewrite: {changed_files:,}")
    if changed_files and not args.apply:
        print("  dry run -- pass --apply to write")
    return 0


def resolve_family_file(chain, slug):
    """taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json,
    most specific first, mirroring portal/scripts/lib/familyPath.ts. The last
    segment is the node's appSlug, not its name: `Incertae sedis` lives in
    `incertae-sedis/`, and a filename built from the name finds nothing."""
    kingdom = chain[0].get("name")
    ranks = [n.get("name") for n in chain[1:]]
    phylum, cls, order = (list(ranks) + ["", "", ""])[:3]
    tails = [[phylum, cls, order], [cls, order], [phylum, order],
             [phylum, cls], [phylum], [cls], []]
    for tail in tails:
        segs = [s for s in tail if s]
        if not segs:
            continue
        cand = os.path.join("taxonomy", (kingdom or "").lower(),
                            *[s.lower().replace(" ", "_") for s in segs],
                            slug, "src", "data", slug + ".json")
        if os.path.exists(cand):
            return cand
    return None


if __name__ == "__main__":
    sys.exit(main())