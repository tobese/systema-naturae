#!/usr/bin/env python3
"""Flag GTDB genome-cluster placeholders as what they are.

GTDB names every genome cluster it has, described or not: `CBDUSG01
sp965602895` (a cluster with no species name, 161,743 in bacteria) and
`Onstottus_A frigus` (a name GTDB split off with a letter suffix, 6,497). They
are not described species, and counting them as species is what
inventory-over-volume warns against. Decided 2026-11-05 (user): keep them,
but mark them -- docs/qbert-bacteria-viruses-plan.md, "Decisions for the
user". Removing or moving them stays open; a flag is the reversible step.

Sets `placeholder` on the species node and nothing else:

  "gtdb-genome"  epithet is `sp` + an accession number (sp965602895, sp10516u)
  "gtdb-suffix"  genus or epithet carries GTDB's `_A`/`_B` split suffix

Only the kingdoms this machine may write (writerKingdoms): bacteria on
q-bert, archaea on Macie. Dry run by default; --apply holds maintenanceLock.

    python3 scripts/markGenomePlaceholders.py
    python3 scripts/maintenanceSession.py --run "python3 scripts/markGenomePlaceholders.py --apply"
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
import writerKingdoms  # noqa: E402
from tree import iter_family_files, iter_species, save_json  # noqa: E402

KINGDOMS = ("bacteria", "archaea")
GENOME = re.compile(r"^sp\d{3,}[a-z]?$")
SUFFIX = re.compile(r"_[A-Z]{1,2}$")


def kind(name):
    parts = (name or "").split()
    if len(parts) != 2:
        return None
    genus, epithet = parts
    if GENOME.match(epithet):
        return "gtdb-genome"
    if SUFFIX.search(genus) or SUFFIX.search(epithet):
        return "gtdb-suffix"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    stat = collections.Counter()
    for k in KINGDOMS:
        if not writerKingdoms.may_write(k):
            print(f"  {k}: not this machine's kingdom (SN_WRITE_KINGDOMS), skipped")
            continue
        files = 0
        for fam in iter_family_files(k):
            with open(fam.path, encoding="utf-8") as fh:
                doc = json.load(fh)
            changed = False
            for sp in iter_species(doc):
                want = kind(sp.get("name"))
                stat[(k, want or "named")] += 1
                if sp.get("placeholder") != want:
                    if want:
                        sp["placeholder"] = want
                    else:
                        sp.pop("placeholder", None)
                    changed = True
            if changed:
                files += 1
                if args.apply:
                    save_json(fam.path, doc)
        stat[(k, "files changed")] = files
    for (k, what), n in sorted(stat.items()):
        print(f"  {k:9s} {what:14s} {n:>9,}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        with maintenanceLock.hold_exclusive():
            sys.exit(main())
    sys.exit(main())
