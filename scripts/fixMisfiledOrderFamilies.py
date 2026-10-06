#!/usr/bin/env python3
"""
Remove the jellyfish genera filed under the priapulid family Halicryptidae.

What this is
------------
Chasing the 35 same-kingdom duplicate genera turned up one file that is genuinely
wrong, and three that are not.

`Halicryptomorpha` is a **class** of priapulid worms, and its sole order in
`portal/data/taxonomy.json` is `Halicryptidae`. So the directory
`.../halicryptomorpha/halicryptomorpha/halicryptidae/` is where the *order* goes,
but the file there carries `rank: "FAMILY"` and holds four scyphozoan
**jellyfish**:

    Chrysaora (22 species), Pelagia (9), Mawia (1), Sanderia (2)

Every one is duplicated from `Pelagiidae` -- same `GENUS_*` id, same species ids --
and their own generated descriptions read "a genus of pelagiid jellyfish", which
contradicts the family they sit in. So a reader browsing jellyfish saw them twice,
and a reader browsing priapulid worms saw a jellyfish family.

That single file accounts for the 35 `Chrysaora` / `Pelagia` / `Mawia` / `Sanderia`
genus-id collisions between those two families.

The three that are NOT wrong
----------------------------
`lamniformes.json` (71 genera, 193 unique species), `orectolobiformes.json` (47
genera, 164 unique) and `cetacea.json` (2 genera, 92 unique) also live at
`<order>/<order>/` and also carry `rank: "FAMILY"`. It is tempting to call these
misfiled order-level duplicates. They are not, and the first version of this
script got that wrong and would have deleted 449 species.

They are real families that happen to share their order's name:

    Chondrichthyes > Lamniformes      (order)
                    > Lamniformes    (family, "Mackerel sharks", 320 species)
                    > Lamnidae       (family)

A family named after its order is unremarkable. The guard below is what caught
it: it refuses to delete a file holding species that exist nowhere else, and all
three were refused. Only `halicryptidae.json`, whose 34 species are all present in
`pelagiidae.json`, passes.

Safety
------
These are deletions, so the script refuses unless the content is provably
duplicated:

- every species id in the file must exist in at least one other family file, so
  nothing unique is lost
- refuses if any species is unique to the file
- refuses if the file's species are the whole tree, which would mean the
  exclusion filter had silently matched nothing
- `--revert` restores from git

    python3 scripts/fixMisfiledOrderFamilies.py            # dry run
    python3 scripts/fixMisfiledOrderFamilies.py --apply    # delete the file

Read-only unless `--apply`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import family_data_files, species_ids  # noqa: E402

# The one file to remove, and the file that legitimately holds its content.
# The three order-named families are checked and refused at runtime rather than
# listed here, so that a future run cannot act on a wrong assumption about them.
CANDIDATES = [
    ("taxonomy/animalia/priapulida/halicryptomorpha/halicryptomorpha/halicryptidae/src/data/halicryptidae.json",
     "pelagiidae.json"),
]




def all_species_ids(root: str = "taxonomy") -> set:
    out = set()
    for dirpath, _d, names in os.walk(root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        for n in names:
            if not n.endswith(".json"):
                continue
            p = os.path.join(dirpath, n)
            try:
                with open(p, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError):
                continue
            out |= species_ids(doc)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    if args.revert:
        subprocess.run(["git", "checkout", "--"] + [c[0] for c in CANDIDATES], check=True)
        print("  restored from git")
        return 0

    universe = all_species_ids()
    print(f"Tree holds {len(universe):,} distinct species ids\n")

    # The three families that share their order's name, reported and refused.
    # They look identical to the real defect from the outside -- same directory
    # shape, same rank -- and are not, so they are checked explicitly rather than
    # left to look like an oversight.
    for lookalike, home in [
        ("lamniformes/lamniformes/src/data/lamniformes.json", "its own 193 species"),
        ("orectolobiformes/orectolobiformes/src/data/orectolobiformes.json", "its own 164 species"),
        ("cetacea/cetacea/src/data/cetacea.json", "its own 92 species"),
    ]:
        for dirpath, _d, names in os.walk("taxonomy"):
            if not dirpath.endswith("src/data") or os.path.basename(lookalike.split("/")[-1]) not in names:
                continue
            p = os.path.join(dirpath, os.path.basename(lookalike))
            if not os.path.exists(p) or "jellyfish" in home:
                continue
            with open(p, encoding="utf-8") as fh:
                doc = json.load(fh)
            mine = species_ids(doc)
            others = all_species_ids_excluding(p)
            if len(mine - others) > 0:
                print(f"  {doc.get('name')!r}: NOT misfiled -- it holds {len(mine - others)} "
                      f"species found nowhere else ({home}). Leaving it.")

    print()
    removed = 0
    for path, real_home in CANDIDATES:
        if not os.path.exists(path):
            print(f"  {os.path.basename(path)} already absent")
            continue
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)

        mine = species_ids(doc)
        if not mine:
            print(f"  {doc.get('name')}: holds no species, nothing to check")
            continue

        # Is this content anywhere else? Anything unique to this file must not be
        # deleted, so the test is against the whole tree MINUS this file.
        others = all_species_ids_excluding(path)
        orphan = mine - others

        genera = len(doc.get("children") or [])
        if orphan:
            print(f"  {doc.get('name')}: REFUSING - {len(orphan)} species exist only here")
            print(f"      e.g. {sorted(orphan)[:3]}")
            continue
        if mine == others:
            print(f"  {doc.get('name')}: REFUSING - its species are the whole of the tree")
            continue

        print(f"  {doc.get('name')!r} rank={doc.get('rank')} {genera} genera, "
              f"{len(mine)} species, all duplicated from {real_home}")
        if args.apply:
            os.remove(path)
            removed += 1

    print(f"\n  removed {removed} file(s)" if args.apply else "\n  (dry run -- pass --apply to delete)")
    return 0


def all_species_ids_excluding(skip: str) -> set:
    out = set()
    for dirpath, _d, names in os.walk("taxonomy"):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        for n in names:
            if not n.endswith(".json"):
                continue
            p = os.path.join(dirpath, n)
            if os.path.abspath(p) == os.path.abspath(skip):
                continue
            try:
                with open(p, encoding="utf-8") as fh:
                    out |= species_ids(json.load(fh))
            except (OSError, ValueError):
                continue
    return out


if __name__ == "__main__":
    sys.exit(main())