#!/usr/bin/env python3
"""Remove `Genus sp.` / `Genus spp.` placeholder nodes held as species.

Measured 2026-11-02: 52,763 SPECIES nodes named `<Genus> sp.` (49,933),
`spp` (2,626) or a variant (`sp. BOLD:AAB7268`, `sp. 1 ...`) -- 41,708 with no
dataset recorded, ENA 7,229, COL XR 2,618; 3 with a description, 6 with a
common name. They are not species, and every count in the portal included
them. Decided by the user the same day: remove them all, and keep the genus a
placeholder leaves empty -- a genus held without species is still a genus we
hold from a source (5,184 genera, 22 families would otherwise go).
taxamatch.bare_binomial() now refuses these names, so imports cannot add
them back.

A placeholder with child nodes (subspecies) is reported and left alone.
A genus emptied this way is marked `noSpeciesHeld: true`; sanity_scan's
EMPTY_GENUS and fix_empty_genera.py skip a genus so marked.
Every removal goes to `<sources>/work/remove-placeholder-species/ledger.jsonl`.
Writes under maintenanceLock -- run it through maintenanceSession.py, then
resyncFamilyCounts.py --apply.

    python3 scripts/removePlaceholderSpecies.py            # dry run
    python3 scripts/removePlaceholderSpecies.py --apply
"""
import argparse
import collections
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
import sources  # noqa: E402
from tree import count_species, iter_family_files, kingdom_names, save_json  # noqa: E402

PLACEHOLDER = re.compile(r"^\S+ (sp|spp)\.?( |$)")
LEDGER = os.path.join(sources.ROOT, "work", "remove-placeholder-species", "ledger.jsonl")


def run(apply):
    stat = collections.Counter()
    ledger = []
    for kingdom in kingdom_names():
        for fam in iter_family_files(kingdom):
            with open(fam.path, encoding="utf-8") as fh:
                text = fh.read()
            if " sp" not in text:
                continue
            doc = json.loads(text)
            before = count_species(doc)
            removed = 0
            stack = [doc]
            while stack:
                n = stack.pop()
                kids = n.get("children") or []
                keep = []
                for c in kids:
                    if c.get("rank") == "SPECIES" and PLACEHOLDER.match((c.get("name") or "").strip('"')):
                        if c.get("children"):
                            stat["placeholder with child nodes, left"] += 1
                            keep.append(c)
                            continue
                        ledger.append({"file": fam.path, "id": c.get("id"), "name": c.get("name"),
                                       "sourceIds": c.get("sourceIds"), "kingdom": kingdom})
                        removed += 1
                        continue
                    keep.append(c)
                if len(keep) != len(kids):
                    n["children"] = keep
                    if n.get("rank") == "GENUS" and not keep:
                        # Held as a genus, with no species: sanity_scan and
                        # fix_empty_genera.py leave a genus marked so alone.
                        n["noSpeciesHeld"] = True
                        stat["genus kept with no species (noSpeciesHeld)"] += 1
                stack.extend(keep)
            if not removed:
                continue
            if count_species(doc) != before - removed:
                sys.exit(f"FATAL: {fam.path}: {before} - {removed} != {count_species(doc)}")
            if "speciesCount" in doc:      # verifyTree: a file's own count matches its contents
                doc["speciesCount"] = count_species(doc)
            stat[f"removed from {kingdom}"] += removed
            stat["files written"] += 1
            if apply:
                save_json(fam.path, doc)
    return stat, ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.apply:
        with maintenanceLock.hold_exclusive():
            stat, ledger = run(True)
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        at = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(LEDGER, "a", encoding="utf-8") as fh:
            for row in ledger:
                fh.write(json.dumps({"at": at, **row}, ensure_ascii=False) + "\n")
    else:
        stat, ledger = run(False)
    print(f"  {len(ledger):,} placeholder species")
    for k, v in sorted(stat.items()):
        print(f"  {v:>9,}  {k}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
