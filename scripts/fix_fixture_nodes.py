#!/usr/bin/env python3
"""
Remove synthetic fixture nodes that leaked into a real family file.

What happened
-------------
`taxonomy/animalia/echinodermata/echinoidea/camarodonta/echinidae/src/data/
echinidae.json` — a real family of 99 named sea-urchin species in 9 real genera
— carries seven nodes that are unmistakably test data:

    GENUS  id=GENUS_GENUS1  name=Genus1
        children: Genus1 SpeciesA, Genus2 SpeciesB, Genus3 SpeciesC
    and the same three ids again, injected into real genera:
        Dermechinus   > Genus1SpeciesA
        Gracilechinus > Genus2SpeciesB
        Echinus       > Genus3SpeciesC

So a reader browsing sea urchins saw a genus called "Genus1" containing
"Genus1 SpeciesA". The phantom genus node also carried a generated description,
"Genus1 — a genus of true sea urchins.", which is how this survived as long as
it did: it looked described.

Detection is deliberately narrow
--------------------------------
An id of `GENUS<n>SPECIES<LETTER>` or `GENUS_GENUS<n>`, or a name of exactly
`Genus<n>` / `Genus<n> Species<LETTER>`. Nothing else matches, and nothing real
can: no genus or species is named after a placeholder token. A looser "contains
Genus followed by a digit" heuristic would eventually catch something like
`Genusia`, so this uses anchors on both sides.

Scope: exactly one file is affected tree-wide. The script finds them wherever
they are rather than hardcoding the path, but it prints what it matched so a
surprise is visible.

    python3 scripts/fix_fixture_nodes.py taxonomy
    python3 scripts/fix_fixture_nodes.py taxonomy --apply

Idempotent — a tree with no fixtures reports zero and changes nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

FIXTURE_ID = re.compile(r"^GENUS\d+SPECIES[A-Z]$|^GENUS_GENUS\d+$")
FIXTURE_NAME = re.compile(r"^Genus\s?\d+(\s+Species\s?[A-Z])?$", re.I)
RANK = ("GENUS", "SPECIES")


def is_fixture(node: dict) -> bool:
    if node.get("rank") not in RANK:
        return False
    return bool(FIXTURE_ID.match(node.get("id") or "")) or bool(
        FIXTURE_NAME.match((node.get("name") or "").strip())
    )


def prune(node: dict, path: list[str], found: list) -> bool:
    """Return True if this node itself should be dropped by its parent."""
    if is_fixture(node):
        found.append((" > ".join(path[-3:]), node.get("rank"), node.get("name"), node.get("id")))
        return True
    kids = node.get("children") or []
    kept = []
    for c in kids:
        if not prune(c, path + [str(node.get("name"))], found):
            kept.append(c)
    if len(kept) != len(kids):
        node["children"] = kept
    lst = node.get("speciesList") or []
    keptl = []
    for s in lst:
        if not prune(s, path + [str(node.get("name")) + ".speciesList"], found):
            keptl.append(s)
    if len(keptl) != len(lst):
        node["speciesList"] = keptl
    return False


def count_species(node) -> int:
    n = 0
    st = [node]
    while st:
        x = st.pop()
        if x.get("rank") == "SPECIES":
            n += 1
        st.extend(x.get("children") or [])
        st.extend(x.get("speciesList") or [])
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = []
    for dirpath, _d, names in os.walk(args.root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    files.sort()

    total = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        before = count_species(doc)
        found: list = []
        drop_root = prune(doc, [str(doc.get("name"))], found)
        if not found or drop_root:
            continue
        total += len(found)
        print(f"  {path}")
        for chain, rank, name, nid in found:
            print(f"    drop {rank:<8} {name!r:<22} id={nid}   under {chain}")
        if args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        print(f"    species {before} -> {count_species(doc)}")

    verb = "Applied" if args.apply else "Would remove"
    print(f"\n{verb}: {total} fixture nodes"
          + ("" if total else " — tree is clean"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
