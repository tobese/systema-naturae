#!/usr/bin/env python3
"""Clear the template descriptions: an empty description is something to
compare against, a template only looks like coverage.

`fix_all_descriptions.py` once wrote one sentence onto every species that had
no description, built from fields the node already carries:

    "Apororhynchus aculeatus Meyer, 1931 is a apororhynchidae species found in its native region."
    "Asota chionea is a noctuoidea > asota species found in Africa region."

It says nothing the name, family and continents do not, and counted as
"described" it made the coverage report read 69%. Decided 2026-11-01 with the
Wikipedia v2 plan (docs/wiki-enrichment-v2-plan.md): stub articles are not
taken, so our own stubs go too, and empty means empty everywhere.

Only a description that is *entirely* that sentence is cleared -- the name
(optionally with a common name in parentheses), "is a(n) <x> species found
in", then "its native region" or a continent list and "region(s)". Prose
that merely contains "species found in" is left. The common name and
continents the sentence repeated stay as fields. Wikipedia's own stub leads
("X is a moth of the family Y.") are not touched here; v2 decides those by
the article's stub template.

Writes under maintenanceLock; run through maintenanceSession.py. Each cleared
text goes to the ledger (<sources>/work/clear-template-descriptions/), so it
can be counted or restored.

    python3 scripts/clearTemplateDescriptions.py            # dry run
    python3 scripts/clearTemplateDescriptions.py --apply
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
from tree import count_species, iter_family_files, iter_species, kingdom_names, save_json  # noqa: E402

TEMPLATE = re.compile(
    r"^(?P<name>.+?)(?: \([^()]*\))? is an? (?P<what>[^.]{1,200}?) species found in "
    r"(?:its native region|[A-Z†][^.]{0,120}? regions?)\.$")
LEDGER_DIR = os.path.join(sources.ROOT, "work", "clear-template-descriptions")


def is_template(desc: str, name: str) -> bool:
    m = TEMPLATE.match(desc.strip())
    # The sentence opens with the node's own name; a description about
    # another taxon is not this template whatever its shape.
    # Quotes: the WoRMS take's quoted names left a few sentences opening
    # with "\"Genus species\"" (fixQuotedNames.py).
    return bool(m) and m.group("name").replace('"', "").split()[:2] == name.replace('"', "").split()[:2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    stat = collections.Counter()
    ledger = []

    def run():
        for k in kingdom_names():
            for fam in iter_family_files(k):
                with open(fam.path, encoding="utf-8") as fh:
                    doc = json.load(fh)
                before = count_species(doc)
                changed = 0
                for sp in iter_species(doc):
                    d = sp.get("description")
                    if not isinstance(d, str) or not d:
                        continue
                    if is_template(d, sp.get("name") or ""):
                        ledger.append({"file": os.path.relpath(fam.path), "id": sp.get("id"), "description": d})
                        del sp["description"]
                        changed += 1
                    elif "species found in" in d:
                        stat["near miss (kept)"] += 1
                if count_species(doc) != before:
                    sys.exit(f"FATAL: species count changed in {fam.path}")
                if changed:
                    stat[f"{k}: cleared"] += changed
                    stat["files"] += 1
                    if args.apply:
                        save_json(fam.path, doc)
            print(f"  {k:10s} {stat[f'{k}: cleared']:>10,} cleared", flush=True)

    if args.apply:
        with maintenanceLock.hold_exclusive():
            run()
        os.makedirs(LEDGER_DIR, exist_ok=True)
        path = os.path.join(LEDGER_DIR, time.strftime("%Y%m%d-%H%M%S") + ".jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for row in ledger:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  ledger: {path}")
    else:
        run()
    for key, v in sorted(stat.items()):
        print(f"  {v:>10,}  {key}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
