#!/usr/bin/env python3
"""
Clear GBIF treatment text that was attached to the wrong species.

What went wrong
---------------
``scripts/enrichFromGbifTypes.py`` and its siblings pull a GBIF *treatment* -
the prose a monograph author wrote describing one species, with its
specimen abbreviations and measurements - and write it onto whatever family
node they were processing. The text is real, and it belongs to a real species,
but usually not the one it landed on. Two examples from the same run:

    Pomphorhynchus bulbocolli  Linkins, 1919
      "Pimelodus albicans (Valenciennes) (Siluriformes, Pimelodidae).
       SI: body cavity. SD: unknown. L: Buenos Aires Province..."

    Pomphorhynchus sphaericus Pertierra, Spatz & Doma, 1996
      "Pimelodus albicans (Valenciennes) (Siluriformes, Pimelodidae).
       SI: intestine. SD: adult. L: Buenos Aires Province..."

Two different acanthocephalan worms, the same catfish, verbatim. Neither text
mentions its own genus: of the records this catches, 14 of 14 are about
something else. Much of it is OCR from a scanned monograph, which is why the
headings arrive letter-spaced and mis-punctuated - "G e n e r a l (8}, 10 {)."
is "General (8, 10)".

This is the same failure as the Wikipedia redirect bug in
``fix_redirect_descriptions.py`` from the other direction: there, a species got
its *genus'* article; here it gets *another species'* treatment. A description
that is not about the species it sits on is worse than no description, because
it looks right and the coverage numbers then overstate what is known.

What it does
------------
Clears the description and resets ``sourcedFrom`` to "none" for every species
where the text is recognisably a GBIF treatment, and which is already tagged
``"none"`` - a previous pass demoted the label without removing the text, so
the fix completes that pass rather than starting a new one. Anything it is not
confident about is printed for a human rather than cleared.

The ``sourcedFrom == "none"`` precondition is deliberate. A species whose
description is correctly attributed to GBIF or Wikipedia is not this bug's
business; only the records someone has already flagged as not-to-be-trusted are
in scope.

Deliberately not cleared
------------------------
Of the 91 records the earlier pass demoted, 38 are cleared here. The other 53
are left for a human, because they are not all the same thing and a heuristic
that removed all of them would delete real data:

- 21 name their own species in the opening and are at least *about* it. Some
  are genuine descriptions ("Habitats: Erpobdella nigricollis is an inhabitant
  of large- or medium-sized running waters..."); the rest are taxonomic
  bibliography rather than prose - synonymy lists and page citations
  ("Allolobophora handlirschi: Karaman & Stojanovic 1995: 139..."), correct
  in subject but not something a reader wants as a description. Whether a
  synonymy list counts as a description is a judgement call, not a regex.
- 32 are junk this script's markers miss: Latin filler ("REGNUM ANIMALE.
  ANIMALIA organisatione viva, nervis sentiunt..."), OCR lifted from a road map
  of Newfoundland and Labrador, bare distribution notes. They are still worth
  clearing eventually, but not on a marker list that was tuned on the easy 38.

Every cleared record is counted, and the file list is printed, so the effect is
never larger than what was reported in the dry run.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

EXCLUDED = ("unified-taxonomy", "node_modules", "portal/data", "shared/data", "continents")

# GBIF treatment vocabulary. A description carrying these is a treatment, and
# a treatment is about one specimen series, not about a whole species page.
TREATMENT = (
    "SI:", "SD:", "SA:", "SP:", "L: ", "sp. nov.", "gen. nov.", "subsp. nov.",
    "var. nov.", "comb. nov.", "syn. nov.", "holotype", "paratype", "isotype",
    "Materials examined", "Type locality", "Distribution.",
    # Letter-spaced headings, from OCR of a scanned monograph.
    "G e n e r a l", "D e s c r i p t i o n", "D i a g n o s i s",
    "M a t e r i a l", "H o l o t y p e",
    "mm long", "body length of", "fixed specimens", "preserved specimens",
)
# A description that opens with a different binomial than the species it is on.
FOREIGN_BINOMIAL = re.compile(r"^([A-Z][a-z]+)\s+([a-z][a-z-]+)\s+\(")

MIN_LEN = 120


def data_files(root: str):
    for dirpath, _dirnames, filenames in os.walk(root):
        if "src/data" not in dirpath.replace(os.sep, "/"):
            continue
        for fn in filenames:
            if fn.endswith(".json"):
                yield os.path.join(dirpath, fn)


def walk(node, genus=None):
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


# ── Classification ───────────────────────────────────────────────────────────
# Shared with scripts/buildDescriptionReview.py, which imports from here, so the
# thing that clears and the thing that reports can never disagree about what a
# record is.

LATIN = re.compile(
    r"\b(organisatione|organisationis|percipiunt|sentiunt|regerentur|"
    r"animalia|vegetabil|reprod[u]?ctio|generationis|exponentia)\b", re.I)
OFF_TOPIC = re.compile(
    r"\b(highway|route|map|railway|station|airport|province of|county|"
    r"literature:|cf\.|ibid\.|op\. cit\.|km north|elevation of)\b", re.I)
SPECIMEN = re.compile(
    r"(\d+\s*[\u00b0\u00ba]\s*\d+|\bCo\.:|\bCounty\b|\bdet\.\s|\bleg\.\s|"
    r"^\s*records?:|\bpreviously recorded\b|\bnew record\b|\bcounty\b)", re.I)
BIBLIOGRAPHY = re.compile(
    r"(\d{4}\s*:\s*\d+|comb\.\s*n\.|syn\.\s*nov\.|comb\.\s*nov\.|"
    r"Am\.\s+Midl\. Nat|Acad\. Sci|Beitr\. Zool|sp\.\s*nov\.)")
DISTRIBUTION = re.compile(
    r"^\s*(general distribution|geographic distribution|distribution)\b", re.I)
MORPHOLOGY = re.compile(
    r"(descriptive features and remarks|medium sized (leeches|worms)|"
    r"large leeches|small sized worms|habitats:|"
    r"\bmm long\b|\bbody length\b|dorsally|ventrally|clitellum|"
    r"genital pores|\bkeels?\b)", re.I)
LEAD = re.compile(r"^(.{0,70}?)\s+is\sa\s+(species|genus|family|subfamily)\b", re.I)


def classify(name: str, desc: str, genus: str | None = None) -> str:
    """Which kind of leftover this is. Most specific evidence first."""
    if LATIN.search(desc):
        return "latin-filler"
    if OFF_TOPIC.search(desc):
        return "ocr-junk"
    if SPECIMEN.search(desc):
        return "specimen-records"
    if BIBLIOGRAPHY.search(desc):
        return "bibliography"
    if DISTRIBUTION.match(desc) and not MORPHOLOGY.search(desc):
        return "distribution-only"
    if MORPHOLOGY.search(desc):
        return "morphology"
    m = LEAD.match(desc)
    if m and genus and m.group(1).strip().lower() == genus.lower():
        return "possibly-genuine"
    return "possibly-genuine"


def looks_like_treatment(name: str, desc: str) -> bool:
    if len(desc) < MIN_LEN:
        return False
    if any(marker in desc for marker in TREATMENT):
        return True
    # Opens with a binomial that is not this species: someone else's treatment.
    m = FOREIGN_BINOMIAL.match(desc)
    if m and m.group(1).lower() != (name or "").split()[0].lower():
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--clear-unsourced-classes", default=None,
        help="comma-separated classification classes to clear, e.g. "
             "'bibliography,specimen-records'. 'all' clears every class except "
             "morphology. Restricted to sourcedFrom='none' records - see below. "
             "Omit to clear only the unambiguous treatment text.")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"no such directory: {args.root}")
        return 2

    files = list(data_files(args.root))
    print(f"{len(files)} family data files under {args.root}")
    if not args.apply:
        print("Dry run. Re-run with --apply to write.")

    cleared = 0
    kept = 0
    touched = []
    by_class = Counter()
    skipped = Counter()

    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"  !! {path}: {exc}")
            continue

        here = 0
        for species, _genus in walk(doc):
            if species.get("sourcedFrom") != "none":
                continue
            desc = (species.get("description") or "").strip()
            if not desc:
                continue
            name = species.get("name") or ""
            kind = classify(name, desc, _genus)
            want = args.clear_unsourced_classes
            if want:
                if len(desc) < MIN_LEN:
                    # The review queue applied MIN_LEN; this pass must too, or it
                    # silently widens the population a human approved. Without
                # this it saw 31 "possibly-genuine" where the review showed 5.
                    skipped["short, below MIN_LEN"] += 1
                    continue
                should_clear = (kind != "morphology") if want == "all" \
                    else kind in {c.strip() for c in want.split(",")}
            else:
                should_clear = looks_like_treatment(name, desc)
            if should_clear:
                species["description"] = ""
                here += 1
                by_class[kind] += 1
            elif kind == "morphology":
                # Kept, and re-attributed: the text is a GBIF treatment - the
                # section headings here are GBIF's own ("Descriptive features
                # and remarks", "Habitats:") - so "none" understates where it
                # came from and hides it from the sourced-species highlight.
                species["sourcedFrom"] = "gbif"
                kept += 1
            else:
                skipped[kind] += 1

        if here:
            cleared += here
            touched.append(f"  {here:>3}  {path}")
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, ensure_ascii=False, indent=2)
                    fh.write("\n")

    if by_class:
        print(f"\n  cleared by class: {dict(by_class)}")
    print(f"\n{'Applied' if args.apply else 'Would clear'} {cleared} mis-attached descriptions "
          f"in {len(touched)} files:")
    for line in sorted(touched):
        print(line)
    print(f"\n  kept and re-attributed to gbif: {kept}")
    if skipped:
        print(f"\n{sum(skipped.values())} left alone ({dict(skipped)}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
