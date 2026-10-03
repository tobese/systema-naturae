#!/usr/bin/env python3
"""Remove same-name species duplicates across every family, and realign speciesCount.

The importers dedupe within a single run, but a family accumulates duplicates
across *sources*: our Apidae held 6,526 species from GBIF, Wikipedia and
iNaturalist, the Afrotropical bees file added 2,408 more, and the two disagreed
about authorship often enough to produce Xylocopa capensis four times over --
once with no authority, once as "Spinola", as "Lepeletier, 1841" and as
"Lepeletier". That produced 2,366 redundant nodes across the six bee families.

Matching a source against what we already hold has to be by name alone. A
binomial's genus is its first word, so two nodes with the same name are the same
species; subspecies carry a rank marker ("Apis mellifera subsp. mellifera") and
so never collide with the species. Where authorship disagrees, the node carrying
the most information wins, so a bare stub is enriched rather than the reverse.

This also rewrites each family's speciesCount and genusCount, and reports what
changed. taxonomy.json's speciesCount is realigned separately by
addSpeciesFileOrders.py, which counts the data files rather than trusting one
source's fragment.

Usage:
    python3 scripts/dedupeSpeciesTree.py            # dry run
    python3 scripts/dedupeSpeciesTree.py --apply
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importSpeciesFile as SF  # noqa: E402

EXCLUDE = ("node_modules", "unified-taxonomy")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = [f for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True)
             if not any(e in f for e in EXCLUDE)]
    touched, total_removed, total_before, total_after = [], 0, 0, 0
    for path in sorted(files):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        before = sum(1 for _ in SF.iter_species(d))
        removed = SF.drop_redundant_species(d)
        after = sum(1 for _ in SF.iter_species(d))
        total_before += before
        total_after += after
        if not removed:
            continue
        total_removed += removed
        touched.append((removed, os.path.basename(path), before, after))
        if args.apply:
            d["speciesCount"] = after
            d["genusCount"] = sum(1 for _ in SF.iter_genera(d))
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(d, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    touched.sort(reverse=True)
    print(f"family files scanned: {len(files):,}")
    print(f"species nodes before: {total_before:,}")
    print(f"species nodes after:  {total_after:,}")
    print(f"redundant nodes removed: {total_removed:,}")
    print(f"families changed: {len(touched)}")
    for n, name, b, a in touched[:20]:
        print(f"   {name:<34}{b:>7,} -> {a:>7,}  (-{n:,})")
    if not args.apply and touched:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
