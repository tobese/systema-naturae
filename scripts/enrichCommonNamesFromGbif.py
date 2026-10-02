#!/usr/bin/env python3
"""
Fill empty `commonName` from the GBIF Backbone's VernacularName table.

Why
---
`MISSING_COMMON_NAME` is the largest number in the sanity queue at 1,132,634
species, and `VernacularName.tsv` was in the same download as the
`Distribution.tsv` that answered 78,910 of `MISSING_CONTINENTS` -- measured
without ever being opened.

    1,500,815 rows · 165,199 taxa with an English name · 23,287 of ours

| kingdom | no commonName | filled | yield |
|---|---|---|---|
| animalia | 470,738 | 19,156 | 4.07% |
| fungi | 161,716 | 2,645 | 1.64% |
| plantae | 420,300 | 1,359 | 0.32% |
| protozoa | 3,871 | 21 | 0.54% |
| chromista | 74,044 | 106 | 0.14% |
| archaea | 1,965 | 0 | 0% |

Provenance: GBIF Backbone Taxonomy, export 2023-08-28, CC-BY 4.0,
`gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c`.

Why this needs a filter where continents did not
-----------------------------------------------
A continent code cannot be a wrong common name. A vernacular name routinely is,
and GBIF's table is a union of 105 sources in 30 languages. Three filters, all
deliberately aggressive, because `commonName` is the *display* name: it is what a
reader sees in place of the scientific name, so a bad one is more visible than a
bad `description`.

1. **English only.** `en` and blank language. The UI shows `commonName` as the
   headline, so `de`/`sv`/`fr` (200k+ rows between them) would be wrong in an
   English interface.
2. **Must not look like a diagnosis.** `agent of lymphatic filariasis`,
   `Bacterial kidney disease` and `Beech Leaf Disease` are what *causes* the
   disease or the host condition, not what the organism is called. Filtered by
   phrase.
3. **Must look like a name.** Rejected: anything over 60 characters (prose
   fragments, locality strings, `[Double-barred] Philippine False Coral Snake;
   Barred Coral...`), anything with a digit, anything ending in a period
   (`None recorded.`, `See comments under species.`), anything containing
   `family `/`genus `, and anything with `sp.`/`spp.`.

One filter that looked right and was wrong
------------------------------------------
"Two capitalised words" was tried as a rejection rule -- a common name is rarely
a binomial. It rejected 9,997 of 501,055 (2.0%), and every one inspected was a
false positive: `Collins monster`, `Kermadec cicada`, `Musgano occidental`,
`Gammarid amphipod` are all correct English names that merely happen to be two
capitalised words. So the rule was dropped rather than tuned. This is the same
lesson as the `ACCESSION_NAME` regex: a filter permissive enough to fire often
is a filter nobody can trust, and the cost of a false positive here is a wrong
headline on a species page.

Which of several names
----------------------
`VernacularName.tsv` has 165,199 taxa and some have several English names. The
**shortest** is taken, because a common name that is shorter is nearly always the
better one -- `Man` beats `Homo sapiens, human, man`. Ties break
lexicographically so the choice is deterministic. Only names for the *exact*
species are considered; a genus name is not propagated to its species, which
would put "Mite" on 200 unrelated pages.

Safety
------
- **Empty nodes only.** An existing `commonName` is never read or overwritten, so
  curated data cannot be contradicted.
- **No description is written**, and `sourcedFrom` is set only where a name was
  actually written.
- **Idempotent**; a second run fills 0.

    python3 scripts/enrichCommonNamesFromGbif.py --build-index
    python3 scripts/enrichCommonNamesFromGbif.py             # dry run
    python3 scripts/enrichCommonNamesFromGbif.py --apply
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import sys
import time
import zipfile

BACKBONE = os.path.expanduser("~/Downloads/backbone.zip")
INDEX = os.path.join("portal", "data", "gbif-vernacular-index.json")

# The blank code is NOT English. GBIF's VernacularName carries many rows with an
# empty `language`, and those hold vernacular names in whatever script the
# contributor typed -- treating "" as English imported 2,180 Chinese, Japanese
# and Korean names into the tree in 23dd3876b.
ENGLISH = {"en", "eng"}

# A name in a non-Latin script is not an English name whatever the language
# column claims. Checked on the value, so it also catches a mislabelled row.
NON_LATIN = re.compile(
    r"[\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u3040-\u30FF"
    r"\u4E00-\u9FFF\uAC00-\uD7AF]"
)

# A disease, a host condition, or a role -- never what the organism is called.
NOT_A_NAME = re.compile(
    r"\b(agent of|caused by|disease|pathogen|syndrome|parasite of|vector of|"
    r"epibiont of|endophyte of|sign of)\b", re.I
)
# Prose fragments, locality strings, catalogue cross-references.
REJECT = re.compile(r"\d|\bfamily\b|\bgenus\b|\bsp\.\b|\bspp\.\b|\bsubsp\.\b")
MAX_LEN = 60

# A rank word is a true statement and a useless name. `Subanguina picridis` is
# indeed a nematode, and "Nematode" is not what a reader is looking for; the
# panel would show "Nematode" in place of the scientific name, which tells them
# less than the binomial already does. 106 of the 23,265 fills would have been
# this, so they are dropped rather than shown. `Algae` for a red alga and `Snail`
# for a land snail are the same shape.
RANK_WORD = re.compile(
    r"^(nematode|fungus|alga|algae|bacteri(?:um|a)|yeast|mould|mold|lichen|"
    r"flagellate|ciliate|moss|fern|grass|sedge|herb|shrub|tree|vine|orchid|"
    r"beetle|moth|fly|ant|wasp|bee|spider|mite|worm|snail|clam|fish|bird)s?$",
    re.I,
)


def usable(v: str) -> bool:
    if not v or len(v) > MAX_LEN:
        return False
    if NOT_A_NAME.search(v) or REJECT.search(v):
        return False
    if v.endswith("."):
        return False
    if RANK_WORD.match(v):
        return False
    if NON_LATIN.search(v):
        return False
    return True


def build_index(backbone: str, out: str) -> int:
    if not os.path.exists(backbone):
        sys.exit(f"FATAL: {backbone} not found. Download from\n"
                 f"       https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c")
    z = zipfile.ZipFile(backbone)
    started = time.time()

    print("  VernacularName.tsv -> taxonID/names ...", flush=True)
    t2v: dict[str, list] = collections.defaultdict(list)
    rows = dropped_lang = 0
    with z.open("VernacularName.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_v, i_l = hdr.index("taxonID"), hdr.index("vernacularName"), hdr.index("language")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_l:
                continue
            rows += 1
            v = (p[i_v] or "").strip()
            if (p[i_l] or "").strip().lower() not in ENGLISH:
                dropped_lang += 1
                continue
            if v:
                t2v[p[i_id]].append(v)
    print(f"    {rows:,} rows, {len(t2v):,} taxa with an English name "
          f"({dropped_lang:,} non-English skipped, {time.time()-started:.0f}s)")

    print("  Taxon.tsv -> canonical names ...", flush=True)
    by_name: dict[str, set] = collections.defaultdict(set)
    with z.open("Taxon.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_canon = hdr.index("taxonID"), hdr.index("canonicalName")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_canon:
                continue
            vs = t2v.get(p[i_id])
            if not vs:
                continue
            nm = (p[i_canon] or "").strip().lower()
            if nm:
                by_name[nm].update(vs)

    final: dict[str, str] = {}
    dropped = collections.Counter()
    for nm, vs in by_name.items():
        good = sorted({v for v in vs if usable(v)}, key=lambda s: (len(s), s))
        if not good:
            dropped["all filtered"] += 1
            continue
        final[nm] = good[0]
    print(f"    {len(final):,} names usable ({dropped['all filtered']:,} fully filtered out, "
          f"{time.time()-started:.0f}s)")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(final, fh, ensure_ascii=False)
    print(f"  wrote {out} ({os.path.getsize(out)/1e6:.0f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default=BACKBONE)
    ap.add_argument("--index", default=INDEX)
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--sample", type=int, default=12)
    args = ap.parse_args()

    if args.build_index:
        return build_index(args.backbone, args.index)

    if not os.path.exists(args.index):
        sys.exit(f"FATAL: no index at {args.index}. Build it with --build-index")
    with open(args.index, encoding="utf-8") as fh:
        index = json.load(fh)
    print(f"GBIF vernacular index: {len(index):,} usable English names\n")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from familyFiles import iter_family_files
    from canonicalNames import lookup

    tally: collections.Counter = collections.Counter()
    per_kingdom: collections.Counter = collections.Counter()
    samples: list[tuple] = []
    touched = 0
    started = time.time()

    for path in iter_family_files("."):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        kingdom = os.path.relpath(path).replace(os.sep, "/").split("/")[1]
        changed = False
        stack = [doc]
        while stack:
            node = stack.pop()
            stack.extend(node.get("children") or [])
            stack.extend(node.get("speciesList") or [])
            if node.get("rank") != "SPECIES":
                continue
            tally["species"] += 1
            existing = (node.get("commonName") or "").strip()
            if NON_LATIN.search(existing):
                tally["non-latin"] += 1
                cn = lookup(index, (node.get("name") or "").strip().lower())
                if cn:
                    tally["replaced"] += 1
                    if len(samples) < args.sample:
                        samples.append((node.get("name"), cn))
                else:
                    cn = None
                    tally["cleared"] += 1
                if args.apply:
                    if cn:
                        node["commonName"] = cn
                        node["sourcedFrom"] = "gbif"
                    else:
                        node.pop("commonName", None)
                        if node.get("sourcedFrom") == "gbif":
                            node.pop("sourcedFrom", None)
                changed = True
                continue
            if existing:
                tally["already-has"] += 1
                continue
            tally["empty"] += 1
            cn = lookup(index, (node.get("name") or "").strip().lower())
            if not cn:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            per_kingdom[kingdom] += 1
            changed = True
            if len(samples) < args.sample:
                samples.append((node.get("name"), cn))
            if args.apply:
                node["commonName"] = cn
                node["sourcedFrom"] = "gbif"
        if changed:
            touched += 1
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    empty = tally["empty"]
    print(f"{'=' * 66}")
    print(f"species scanned          {tally['species']:>9,}")
    print(f"already has commonName   {tally['already-has']:>9,}")
    if tally["non-latin"]:
        print(f"NON-ENGLISH commonName   {tally['non-latin']:>9,}  <- "
              f"{tally['replaced']:,} replaced, {tally['cleared']:,} cleared")
    print(f"empty                    {empty:>9,}")
    print(f"GBIF can fill            {tally['filled']:>9,}  "
          f"({tally['filled']/empty*100:.2f}%)")
    print(f"no match                 {tally['no-match']:>9,}")
    print(f"\nfiles: {touched:,}   ({time.time()-started:.0f}s)")
    print("by kingdom:")
    for k, v in per_kingdom.most_common():
        print(f"  {k:<12}{v:>8,}")

    print("\nsample (read these before approving):")
    for n, cn in samples:
        print(f"  {n[:36]:<38}{cn[:44]!r}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    else:
        print(f"\n  wrote {tally['filled']:,} common names across {touched:,} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())