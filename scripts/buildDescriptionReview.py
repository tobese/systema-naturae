#!/usr/bin/env python3
"""
Build the review queue: long `sourcedFrom: "none"` descriptions, classified.

Why a queue and not a fix
-------------------------
``fix_misattached_descriptions.py`` clears the records whose text carries
unambiguous GBIF-treatment vocabulary - specimen abbreviations, "sp. nov.",
"General", measurements. It leaves everything else, because the leftovers are
not one population and a heuristic that removed all of them would delete real
data. Sorting them by *why* they look wrong is what makes them decidable.

The classes
-----------
  latin-filler      lorem ipsum in a dead language. Never was a description.
  ocr-junk          lifted from something that was not a treatment - a road map,
                    a station timetable, a specimen label. The giveaway is
                    content about the world rather than about the animal.
  distribution-only a distribution note with no morphology or diagnosis. True,
                    and about the right species, but not a description.
  bibliography      a synonymy list or page citations. About the right species
                    and arguably worth keeping as "taxonomic history", but not
                    prose, and it should not be shown as a description.
  specimen-records  a locality or specimen list - coordinates, county names,
                    collector initials. A collection record, not a description.
  distribution-only a range note with no morphology. True, and about the right
                    species, but not a description.
  morphology        prose about the animal's own structure or habitat. The only
                    class that is straightforwardly a description; everything
                    else is a decision about what else counts as one.

Nothing here is modified. The point is a list you can read in one sitting.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_misattached_descriptions import data_files, walk, TREATMENT, MIN_LEN  # noqa: E402

LATIN = re.compile(
    r"\b(organisatione|organisationis|percipiunt|sentiunt|regerentur|"
    r"animalia|vegetabil|reprod[u]?ctio|generationis|exponentia)\b", re.I)
# Text about the world, not the animal: OCR off a non-taxonomic source.
OFF_TOPIC = re.compile(
    r"\b(highway|route|map|railway|station|airport|province of|county|"
    r"literature:|cf\.|ibid\.|op\. cit\.|km north|elevation of)\b", re.I)
BIBLIOGRAPHY = re.compile(
    r"(\d{4}\s*:\s*\d+|comb\.\s*n\.|syn\.\s*nov\.|comb\.\s*nov\.|"
    r"Am\.\s+Midl\. Nat|Acad\. Sci|Beitr\. Zool|sp\.\s*nov\.)")
# Specimen and locality records: coordinates, counties, collectors, "Records:".
SPECIMEN = re.compile(
    r"(\d+\s*[°º]\s*\d+|\bCo\.:|\bCounty\b|\bdet\.\s|\bleg\.\s|"
    r"^\s*records?:|\bpreviously recorded\b|\bnew record\b|\bcounty\b)", re.I)
DISTRIBUTION = re.compile(
    r"^\s*(general distribution|geographic distribution|distribution)\b", re.I)
# Prose about the animal itself. The headings are the GBIF treatment sections
# these records were split from, so the class is a heading plus morphology.
MORPHOLOGY = re.compile(
    r"(descriptive features and remarks|medium sized (leeches|worms)|"
    r"large leeches|small sized worms|habitats:|"
    r"\bmm long\b|\bbody length\b|dorsally|ventrally|clitellum|"
    r"genital pores|\bkeels?\b)", re.I)
LEAD = re.compile(r"^(.{0,70}?)\s+is\s+a\s+(species|genus|family|subfamily)\b", re.I)


def classify(name: str, desc: str, genus: str | None) -> str:
    # Order matters: the most specific evidence first, so a specimen list that
    # also happens to mention a measurement lands as a specimen record.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--out", default="docs/reports/description-review.md")
    args = ap.parse_args()

    rows = []
    for path in data_files(args.root):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        for sp, genus in walk(doc):
            if sp.get("rank") != "SPECIES" or sp.get("sourcedFrom") != "none":
                continue
            desc = (sp.get("description") or "").strip()
            if len(desc) < MIN_LEN:
                continue
            rows.append((classify(sp.get("name") or "", desc, genus), path,
                         sp.get("id"), sp.get("name"), genus, desc))

    counts = Counter(r[0] for r in rows)
    by_class = {}
    for kind, path, sid, name, genus, desc in rows:
        by_class.setdefault(kind, []).append((path, sid, name, genus, desc))

    lines = [
        "# Description review queue",
        "",
        f"*{len(rows)} species hold a long `sourcedFrom: \"none\"` description that*",
        "*`fix_misattached_descriptions.py` would not clear. Nothing here is*",
        "*modified - the point is a list that can be decided in one sitting.*",
        "",
        "Generated by `scripts/buildDescriptionReview.py`. Descriptions are",
        "truncated to 200 characters; open the file for the rest.",
        "",
        "| class | count | what it means |",
        "|---|---|---|",
    ]
    blurb = {
        "latin-filler": "lorem ipsum in a dead language; never was a description",
        "ocr-junk": "OCR off something that was not a treatment - a road map, a label",
        "specimen-records": "a locality or specimen list - coordinates, counties, collectors",
        "bibliography": "synonymy list or page citations; right species, not prose",
        "distribution-only": "a range note with no morphology; true, not a description",
        "morphology": "prose about the animal's own structure or habitat",
        "possibly-genuine": "reads as prose but matched none of the above",
    }
    for kind, n in counts.most_common():
        lines.append(f"| `{kind}` | {n} | {blurb.get(kind, '')} |")

    for kind, n in counts.most_common():
        lines += ["", f"## `{kind}` — {n}", ""]
        for path, sid, name, genus, desc in by_class[kind]:
            lines.append(f"- **{name}** (`{sid}`) in `{genus or '?'}`")
            lines.append(f"  `{path}`")
            lines.append(f"> {desc[:200]}{'…' if len(desc) > 200 else ''}")
            lines.append("")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"{len(rows)} records -> {args.out}")
    for kind, n in counts.most_common():
        print(f"  {kind:<20}{n:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
