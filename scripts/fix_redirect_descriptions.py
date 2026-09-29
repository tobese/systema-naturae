#!/usr/bin/env python3
"""
Remove species descriptions that are actually genus-article text.

What went wrong
---------------
``portal/scripts/enrichFromWikipedia.ts`` asked the Wikipedia REST summary
endpoint for a binomial and wrote whatever extract came back as that species'
description. The summary endpoint follows redirects, so a binomial with no
article of its own returns 200 with the *genus* article instead:

    requested: Dermechinus horridus
    title:     Dermechinus
    extract:   "Dermechinus is a genus of sea urchin in the family Echinidae ..."

327 species across 15 phyla ended up carrying their own genus' description,
and the returned title - the genus name - was stored as their commonName. Both
signals are still in the data, so they are what this script keys on:

  * ``commonName`` equals the parent genus' name (the old code's
    ``commonName: data.title !== sciName ? data.title : sciName``)
  * the description opens with "<Genus> is a genus of ..."

Only records where *both* signals agree are rewritten, so a species that merely
mentions its genus in passing is left alone. Anything matching just one is
printed for a human to look at rather than silently cleared.

What it does
------------
Clears the description, resets ``sourcedFrom`` to "none" and drops the
genus-name commonName. It does not try to fetch a replacement: re-running the
enricher (now that it checks the returned title) is what recovers the species
that do have their own article. A genus description is not a species
description, so leaving one in place is worse than an honest gap - and the gap
is visible in the coverage numbers, which a wrong description is not.

Species that lose their last description are counted per family and printed, so
the cost is visible rather than inferred from a diff.
"""
import glob
import json
import os
import re
import sys
from collections import Counter

# "<Genus> is a genus of ..." - the shape of a genus article's opening sentence.
GENUS_ARTICLE = re.compile(r"^\s*([A-Z][a-z]+)\s+is\s+a\s+(genus|family|subfamily|order|class|tribe)\b", re.I)

EXCLUDED = ("unified-taxonomy", "node_modules", "portal/data", "shared/data", "continents")


def data_files(root: str):
    pattern = os.path.join(root, "**", "src", "data", "*.json")
    return [
        f for f in glob.glob(pattern, recursive=True)
        if not any(e in f for e in EXCLUDED)
    ]


def walk(node, genus=None):
    """Yield every species node with its parent genus name."""
    if isinstance(node, list):
        for item in node:
            yield from walk(item, genus)
        return
    if not isinstance(node, dict):
        return
    if node.get("rank") == "GENUS":
        genus = (node.get("name") or "").strip()
    if node.get("rank") == "SPECIES":
        yield node, genus
    for child in node.get("children") or []:
        yield from walk(child, genus)
    for child in node.get("speciesList") or []:
        yield from walk(child, genus)


def classify(species: dict, genus: str):
    """Return (action, reason). action is "clear", "name" or None.

    The description signal is sufficient on its own. A species article opens
    with the species' binomial, so a description that opens with the *genus*
    name followed by "is a genus of" is a genus article by definition. The
    commonName signal is corroborating rather than required, because the two
    kingdoms were enriched by different scripts and only one of them set
    commonName from the returned title.
    """
    if not genus:
        return None, ""
    desc = (species.get("description") or "").strip()
    common = (species.get("commonName") or "").strip()
    by_common = bool(common) and common.lower() == genus.lower()
    match = GENUS_ARTICLE.match(desc)
    by_desc = bool(match) and match.group(1).lower() == genus.lower()

    if by_desc:
        return "clear", f"description is the {genus} genus article"
    if by_common:
        return "name", f"commonName is the genus name {genus!r}"
    return None, ""


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    apply = "--apply" in sys.argv

    files = data_files(root)
    print(f"{len(files)} family data files under {root}")
    if not apply:
        print("Dry run. Re-run with --apply to write.")

    cleared = 0
    review: list[str] = []
    emptied: Counter = Counter()
    touched: list[str] = []

    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"  !! {path}: {exc}")
            continue

        file_cleared = 0
        for species, genus in walk(doc):
            action, reason = classify(species, genus)
            if action == "clear":
                file_cleared += 1
                species["description"] = ""
                species["sourcedFrom"] = "none"
                if (species.get("commonName") or "").strip().lower() == (genus or "").lower():
                    species["commonName"] = ""
                # `continents` is left alone deliberately. It was inferred from
                # the genus article, so it is the genus' range rather than the
                # species' - but a genus and its species usually do share a
                # range, so it is approximately right, and clearing it would
                # trade a slightly-wrong value for a hole in the coverage data.
            elif action == "name":
                file_cleared += 1
                species["commonName"] = ""
                review.append(f"  {path}  {species.get('id')}  {reason}")

        if file_cleared:
            cleared += file_cleared
            touched.append(f"  {file_cleared:>4}  {path}")
            if apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, ensure_ascii=False, indent=2)
                    fh.write("\n")

    print(f"\n{'Applied' if apply else 'Would clear'} {cleared} species in {len(touched)} files:")
    for line in sorted(touched):
        print(line)

    if review:
        print(f"\n{len(review)} records match only one signal - left alone, needs a look:")
        for line in review[:40]:
            print(line)
        if len(review) > 40:
            print(f"  ... and {len(review) - 40} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
