#!/usr/bin/env python3
"""Clear descriptions that are not in the portal's language.

GBIF treatment text is contributed in whatever language the source publication
used, and `enrichFromGbifTypes.py` was selecting on record `type` alone, so 1,110
species ended up with a French, German, Spanish or Italian description in an
English interface -- `Camponotus quadrilaterus` showed a reader German morphology
for its worker. A further 69 arrived tagged `sourcedFrom: wikipedia` with no
`wikipediaTitle` at all, so they never came from an English article either.

The guard in `enrichFromGbifTypes.py` stops new ones. This clears the ones
already written.

Clearing rather than translating: the text is not wrong, it is in the wrong
language, and machine-translating a taxonomic treatment would put invented
morphology in front of a reader. Every one of these was written into a slot that
was previously empty -- the fillers only ever fill an empty description -- so
clearing restores the prior state instead of discarding curated prose.

Removed text is written to a JSONL backup first, so this is reversible.

Usage:
    python3 scripts/clearNonEnglishDescriptions.py            # dry run
    python3 scripts/clearNonEnglishDescriptions.py --apply
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # noqa: E402
from textLanguage import foreign_language  # noqa: E402

BACKUP = os.path.join("portal", "data", "non-english-descriptions.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--backup", default=BACKUP)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    tally = {"scanned": 0, "described": 0, "cleared": 0}
    langs: dict[str, int] = {}
    removed = []
    per_file = 0

    for path in iter_family_files(args.root):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        hits = 0
        stack = [doc]
        while stack:
            node = stack.pop()
            stack.extend(node.get("children") or [])
            stack.extend(node.get("speciesList") or [])
            desc = (node.get("description") or "").strip()
            if not desc:
                continue
            tally["described"] += 1
            code = foreign_language(desc)
            if not code:
                continue
            tally["cleared"] += 1
            langs[code] = langs.get(code, 0) + 1
            removed.append({
                "name": node.get("name"),
                "file": os.path.relpath(path, args.root),
                "lang": code,
                "sourcedFrom": node.get("sourcedFrom"),
                "wikipediaTitle": node.get("wikipediaTitle"),
                "description": desc,
            })
            hits += 1
            if args.apply:
                node.pop("description", None)
                if (node.get("wikipediaTitle") or "").startswith("gbif:"):
                    node.pop("wikipediaTitle", None)
                if node.get("sourcedFrom") == "gbif":
                    node.pop("sourcedFrom", None)
        if hits:
            per_file += 1
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"species with a description  {tally['described']:>9,}")
    print(f"not in English              {tally['cleared']:>9,}")
    for code, n in sorted(langs.items(), key=lambda kv: -kv[1]):
        print(f"   {code}: {n:,}")
    print(f"family files affected       {per_file:>9,}")

    if not args.apply:
        print("\nsample (read these before approving):")
        for r in removed[:10]:
            print(f"  [{r['lang']}] {r['name'][:34]:<36}{r['description'][:56]!r}")
        print("\n  (dry run -- pass --apply to write)")
        return 0

    os.makedirs(os.path.dirname(args.backup) or ".", exist_ok=True)
    with open(args.backup, "w", encoding="utf-8") as fh:
        for r in removed:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n  cleared {len(removed):,} descriptions across {per_file:,} files")
    print(f"  removed text kept in {args.backup} "
          f"({os.path.getsize(args.backup)/1e6:.1f} MB) -- restore from here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
