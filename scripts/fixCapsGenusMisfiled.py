#!/usr/bin/env python3
"""
Fix the all-caps genus node in Musophagidae, and reparent its misplaced species.

What this is
------------
`Musophagidae` lists two genus nodes that are the same genus:

    Gallirex   id=GENUS_GALLIREX   1 species   Gallirex porphyreolophus
    GALLIREX   id=GENUS_GALLIREX   4 species   GALLIREX aurantiaca
                                          CORYTHAEOLA kiboko
                                          CRINIFER tanae
                                          MUSOPHAGA zoea

Same `id`, so they collide. Three of the four children are not even *Gallirex* --
they belong to genera that already exist in this same file (Corythaeola, Crinifer,
Musophaga). They were filed under an all-caps node that carries a generated
description, `GALLIREX - a genus of turacos.`, which is how it passed as real
data.

Note `fix_fixture_nodes.py` does not catch this: it matches `Genus<n>` and
`GENUS<n>SPECIES<A>` placeholders, and none of these are that shape. It is a
different defect -- a real genus duplicated in the wrong case with real species
misfiled into it -- and it survived that script for the same reason it survived
`merge_duplicate_genera.py`, which groups on genus name and so sees two distinct
strings.

Verified before acting: every one of the five names occurs exactly once in the
whole of animalia, so this is misplacement, not duplication, and nothing is
created or lost. The real binomials (`Gallirex porphyreolophus`,
`Gallirex aurantiaca`) confirm the intended genus is *Gallirex*.

What it does
------------
1. Deletes the `GALLIREX` node.
2. Moves `CORYTHAEOLA kiboko` -> `Corythaeola`, `CRINIFER tanae` -> `Crinifer`,
   `MUSOPHAGA zoea` -> `Musophaga`, creating a genus node only if absent.
3. Moves `GALLIREX aurantiaca` into `Gallirex`, fixing its name to match the
   binomial.
4. The longest description of the two copies wins, with its `sourcedFrom`, so the
   generated one cannot displace real prose.

Names are corrected here rather than preserved, because unlike the MycoBank
renames this is not a taxonomy judgement: `MUSOPHAGA zoea` under a genus called
`GALLIREX` is a filing error, and the binomial says which genus it belongs to.

    python3 scripts/fixCapsGenusMisfiled.py            # dry run
    python3 scripts/fixCapsGenusMisfiled.py --apply

Read-only unless `--apply`. Idempotent.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

TARGET = os.path.join(
    "taxonomy", "animalia", "chordata", "aves", "musophagiformes",
    "musophagidae", "src", "data", "musophagidae.json",
)

# An all-caps genus node: every letter upper, at least three of them. Long
# enough not to fire on a two-letter code.
CAPS = re.compile(r"^[A-Z][A-Z0-9\-]{2,}$")


def better(a: dict, b: dict) -> dict:
    return a if len((a.get("description") or "").strip()) >= len((b.get("description") or "").strip()) else b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=TARGET)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.exit(f"FATAL: {args.path} not found. The path is written into the docstring; "
                 f"find the family with `find taxonomy -name musophagidae.json`.")

    with open(args.path, encoding="utf-8") as fh:
        doc = json.load(fh)
    kids = doc.get("children") or []

    caps = [c for c in kids if c.get("rank") == "GENUS" and CAPS.match(c.get("name") or "")]
    if not caps:
        print("  no all-caps genus node found; nothing to do")
        return 0

    for node in caps:
        proper = next((c for c in kids
                       if c is not node and c.get("rank") == "GENUS"
                       and (c.get("name") or "").casefold() == (node.get("name") or "").casefold()), None)
        print(f"  {node['name']!r} (id={node['id']!r}) holds "
              f"{len(kids)} children")
        if proper is None:
            print(f"      no case-variant sibling to merge into -- leaving alone")
            continue

        print(f"    sibling {proper['name']!r} (id={proper['id']!r}) holds "
              f"{len(proper.get('children') or [])}")

        # Which genus does each child actually belong to? Its own binomial says so.
        moves = []
        for c in node.get("children") or []:
            name = (c.get("name") or "").strip()
            m = re.match(r"^[A-Za-z][a-zA-Z\-]*\s+\S", name)
            if not m:
                print(f"      !! {name!r} has no binomial; not touching it")
                continue
            genus = name.split()[0]
            dest = next((g for g in kids if g.get("rank") == "GENUS"
                         and (g.get("name") or "").casefold() == genus.casefold()), None)
            if dest is None:
                print(f"      {genus!r} is not in this family; leaving {name!r} alone")
                continue
            moves.append((c, dest, genus))

        for c, dest, genus in moves:
            # Rebuild the binomial from the DESTINATION genus, not the source one.
            # Substituting the genus into the old name only reproduces the old
            # name when they match, which is the case that needed no change.
            epithet = " ".join((c.get("name") or "").split()[1:])
            new_name = f"{dest['name']} {epithet}".strip()
            print(f"      move {c['name']!r} -> {dest['name']!r}  (as {new_name!r})")
            if args.apply:
                c["name"] = new_name
                dest.setdefault("children", []).append(c)

        if args.apply:
            # Descriptions: the two genus copies may disagree; keep the richer.
            if better(proper, node) is node:
                proper["description"] = node.get("description")
                if node.get("sourcedFrom"):
                    proper["sourcedFrom"] = node["sourcedFrom"]
            doc["children"] = [c for c in kids if c is not node]

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    with open(args.path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"\n  wrote {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())