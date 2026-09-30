#!/usr/bin/env python3
"""
Merge duplicate GENUS nodes within a family.

The defect
----------
12 families contain the same genus twice, so its species are copied with it:

  Otididae[6] > Lophotis[0]  Lophotis ruficrista
  Otididae[8] > Lophotis[0]  Lophotus ruficrista        <- same node, same id

22 redundant genus nodes, 65 species nodes that are copies. Nothing is wrong
with any single node; the family simply lists the genus twice.

Why NOT scripts/fix_duplicates.py
---------------------------------
It keeps the first duplicate child and drops the rest. That is fine for exact
copies and **wrong here**: 14 of the 20 duplicate genus pairs hold different
subsets. Paradisaeidae's two Parotia nodes list 5 and 6 species - the second has
PAROTIA_WAHNESI, the first does not. Keeping the first would silently delete a
species from the tree, which is the opposite of tidying it.

So this unions by species id. The base is the richest copy (most species); any
species present only in another copy is appended, in the list that copy used, so
nothing is lost and the structure stays as the compression pass left it.

If two copies of the same species disagree, the longer description wins and
sourcedFrom comes with it - the longer one is the more enriched, and the two
are otherwise the same taxon under the same id.

    python3 scripts/merge_duplicate_genera.py taxonomy
    python3 scripts/merge_duplicate_genera.py taxonomy --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict


def species_count(genus: dict) -> int:
    return sum(
        1
        for c in (genus.get("children") or [])
        if c.get("rank") == "SPECIES"
    ) + sum(1 for s in (genus.get("speciesList") or []) if s.get("rank") == "SPECIES")


def richness(genus: dict) -> tuple:
    """Rank copies so the best one becomes the base: most species first, then
    most total described characters, then name for a stable order."""
    chars = 0
    stack = [genus]
    while stack:
        n = stack.pop()
        chars += len((n.get("description") or "").strip())
        stack.extend(n.get("children") or [])
        stack.extend(n.get("speciesList") or [])
    return (species_count(genus), chars, genus.get("name") or "")


def species_count_of_copies(genus_list) -> int:
    return sum(species_count(g) for g in genus_list)


def better(a: dict, b: dict) -> dict:
    """Keep the richer of two nodes that share an id."""
    da = len((a.get("description") or "").strip())
    db = len((b.get("description") or "").strip())
    if da != db:
        return a if da > db else b
    return a if (a.get("sourcedFrom") or "") else b if (b.get("sourcedFrom") or "") else a


def merge_genus(copies: list[dict]) -> tuple[dict, int, int]:
    """Return (merged genus, species gained, species enriched)."""
    copies = sorted(copies, key=richness, reverse=True)
    base = copies[0]
    have_children = {c.get("id") for c in (base.get("children") or [])}
    have_sl = {s.get("id") for s in (base.get("speciesList") or [])}
    gained = enriched = 0

    for other in copies[1:]:
        for c in (other.get("children") or []):
            if c.get("rank") != "SPECIES":
                continue
            if c.get("id") in have_children:
                for existing in base["children"]:
                    if existing.get("id") == c.get("id"):
                        merged = better(existing, c)
                        if merged is not existing:
                            base["children"][base["children"].index(existing)] = merged
                            enriched += 1
                        break
            else:
                base.setdefault("children", []).append(c)
                have_children.add(c.get("id"))
                gained += 1
        for s in (other.get("speciesList") or []):
            if s.get("rank") != "SPECIES":
                continue
            if s.get("id") in have_sl:
                for existing in base.get("speciesList", []):
                    if existing.get("id") == s.get("id"):
                        merged = better(existing, s)
                        if merged is not existing:
                            base["speciesList"][base["speciesList"].index(existing)] = merged
                            enriched += 1
                        break
            elif s.get("id") not in have_children:
                base.setdefault("speciesList", []).append(s)
                have_sl.add(s.get("id"))
                gained += 1

    # Drop ids that ended up in both lists through different copies.
    dupes = have_children & have_sl
    if dupes:
        base["speciesList"] = [s for s in base.get("speciesList", []) if s.get("id") not in dupes]
    return base, gained, enriched


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

    fams = genera_removed = species_gained = species_enriched = redundancy_removed = 0
    detail = []

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        kids = doc.get("children") or []
        byname = defaultdict(list)
        for c in kids:
            byname[c.get("name")].append(c)
        dupes = {n: g for n, g in byname.items() if n and len(g) > 1}
        if not dupes:
            continue
        fams += 1
        # Distinct species ids in the family, before and after. NOT the sum over
        # genus copies: two identical copies of a 3-species genus sum to 6, and
        # the union is legitimately 3 - that difference is the redundancy being
        # removed, not a loss. The invariant that actually matters is that the
        # merge neither drops a species nor invents one.
        def distinct_species(genus_list):
            ids = set()
            for g in genus_list:
                stack = [g]
                while stack:
                    n = stack.pop()
                    if n.get("rank") == "SPECIES" and n.get("id"):
                        ids.add(n["id"])
                    stack.extend(n.get("children") or [])
                    stack.extend(n.get("speciesList") or [])
            return ids

        before = distinct_species(kids)
        merged_nodes = []
        for name, copies in dupes.items():
            base, gained, enriched = merge_genus(copies)
            merged_nodes.append((name, len(copies), base, gained, enriched))
            species_gained += gained
            species_enriched += enriched
            detail.append((doc.get("name"), name, len(copies), gained, enriched))
        kept = []
        seen = set()
        for c in kids:
            n = c.get("name")
            if n in dupes:
                if n in seen:
                    genera_removed += 1
                    continue
                seen.add(n)
                kept.append(next(base for nm, _c, base, _g, _e in merged_nodes if nm == n))
                continue
            kept.append(c)
        doc["children"] = kept
        # Measured on the NEW list. Computing this over `kids` is wrong:
        # merge_genus mutates the base copy in place, so `kids` then holds the
        # enriched base AND the untouched copies, and every merged genus counts
        # twice. The first run of this reported Ploceidae going 118 -> 137,
        # which was the check lying rather than the merge.
        after = distinct_species(kept)
        lost = before - after
        invented = after - before
        assert not lost, f"{path}: merge LOST species {sorted(lost)[:5]}"
        assert not invented, f"{path}: merge INVENTED species {sorted(invented)[:5]}"
        redundancy_removed += species_count_of_copies(kids) - len(after)
        if args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    print(f"{'Applied' if args.apply else 'Would merge'}: {fams} families, "
          f"{genera_removed} redundant genus nodes removed")
    print(f"  species recovered that keep-first would have deleted: {species_gained}")
    print(f"  redundant species nodes removed:                        {redundancy_removed}")
    print(f"  duplicate species enriched with the longer description:  {species_enriched}")
    for fam, name, copies, gained, enriched in detail:
        print(f"    {fam} / {name}: {copies} copies, +{gained} species, {enriched} enriched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
