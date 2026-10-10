#!/usr/bin/env python3
"""
Fill empty `commonName` from the Wikidata Species archive's VernacularName
table.

Why
---
Follow-up to the 2026-10-10 wikidata-species re-check
(docs/bacteria-and-viruses.md, scripts/sourcesManifest.py): the
species-import question for this archive is downstream of the
bacteria-and-viruses hold, but its sidecar tables are not -- enrichment
only needs species we already hold. Measured against the held tree:

    95,067 taxa with an en/blank vernacular name (108 languages total,
    816,277 rows) · 70,935 held · 36,620 already have a commonName ·
    34,315 do not

That gap is larger than the 23,287 the already-applied
scripts/enrichCommonNamesFromGbif.py pass filled, with no licence problem
(CC0) and the same safety pattern.

Why this needs a filter where continents did not
-----------------------------------------------
Identical reasoning to the GBIF importer's: `commonName` is the *display*
name, so a bad fill is more visible than a bad `description`, and
Wikidata's VernacularName table spans 108 languages contributed with no
quality gate. The filters themselves are imported from
`enrichCommonNamesFromGbif` rather than re-written, because the question
"is this string a usable English common name" does not change with the
source -- only which language codes count as English does.

Which language codes count as English
---------------------------------------
Wikidata writes regional variants (`en-us`, `en-gb`, `en-au`, `en-ca`,
`en-in`, `en-nz`) alongside bare `en`, and -- unlike GBIF's table --
carries no blank-language rows at all (0 of 816,277), so there is no
"blank is not English" trap to repeat here.

Which of several names
-----------------------
Same rule as the GBIF importer: shortest wins, ties break
lexicographically, and only names for the *exact* species are considered.
That last part comes for free here rather than needing a join: Wikidata's
`NameUsage.tsv` carries `rank` directly, so the index is only ever built
from taxonIDs where `rank == "species"` -- a genus-level vernacular name
never enters the candidate pool in the first place.

Safety
------
- **Empty nodes only.** An existing `commonName` is never read or
  overwritten.
- **No description is written**, and `sourcedFrom` is set only where a
  name was actually written.
- **Idempotent**; a second run fills 0.

    python3 scripts/enrichCommonNamesFromWikidata.py --build-index
    python3 scripts/enrichCommonNamesFromWikidata.py             # dry run
    python3 scripts/enrichCommonNamesFromWikidata.py --apply
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enrichCommonNamesFromGbif import usable  # noqa: E402
from canonicalNames import lookup  # noqa: E402
from tree import iter_family_files, iter_species  # noqa: E402

ARCHIVE = "/Volumes/MacieExternal/sources/archives/wikidata-species/wikidata.zip"
INDEX = os.path.join("portal", "data", "wikidata-vernacular-index.json")

# Wikidata carries regional variants alongside bare `en`, and -- unlike
# GBIF's VernacularName table -- zero blank-language rows (checked against
# all 816,277), so there is no blank-is-not-English trap to guard here.
ENGLISH = {"en", "en-us", "en-gb", "en-au", "en-ca", "en-in", "en-nz"}

_WORD = re.compile(r"[A-Za-z]+")


def _norm_word(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


def is_restated_binomial(sciname: str, candidate: str) -> bool:
    """True when `candidate` is just `sciname` re-capitalised, not translated.

    31 of 83,981 candidates (0.037%), found by eyeballing a sample before
    applying anything: `Sitta frontalis -> Sitta frontalis`, `Illicium
    anisatum -> Illicium anisatum`, `Messor pergandei -> Messor pergandei`.
    Narrower than it looks tempting to write: a species epithet used as a
    reversed, capitalised adjective (`Argiope florida -> Florida Argiope`,
    `Hyliota usambara -> Usambara Hyliota`) is a real, common English naming
    convention for geographically-named species and must not be caught here
    -- only the *same word order* as the Latin, nothing added, counts as "not
    a translation happened." A single genus word reused alone (`Ginkgo
    biloba -> Ginkgo`, `Litchi chinensis -> litchi`) is correct, standard
    usage and is a different shape entirely (one word, not two).
    """
    parts = sciname.split()
    if len(parts) != 2:
        return False
    gn, sn = _norm_word(parts[0]), _norm_word(parts[1])
    words = [_norm_word(w) for w in _WORD.findall(candidate)]
    return len(words) == 2 and words[0] == gn and words[1] == sn


def build_index(archive: str, out: str) -> int:
    if not os.path.exists(archive):
        sys.exit(f"FATAL: {archive} not found.")
    z = zipfile.ZipFile(archive)
    started = time.time()

    print("  NameUsage.tsv -> taxonID/scientificName (species rank only) ...",
          flush=True)
    id_to_name: dict[str, str] = {}
    with z.open("NameUsage.tsv") as f:
        r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                       delimiter="\t")
        hdr = next(r)
        i_id = hdr.index("col:ID")
        i_rank = hdr.index("col:rank")
        i_name = hdr.index("col:scientificName")
        for row in r:
            if len(row) <= i_name or row[i_rank] != "species" or not row[i_name]:
                continue
            id_to_name[row[i_id]] = row[i_name]
    print(f"    {len(id_to_name):,} species-rank taxa "
          f"({time.time() - started:.0f}s)")

    print("  VernacularName.tsv -> candidate names ...", flush=True)
    by_name: dict[str, set] = collections.defaultdict(set)
    rows = dropped_lang = dropped_rank = 0
    with z.open("VernacularName.tsv") as f:
        r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                       delimiter="\t")
        hdr = next(r)
        i_id = hdr.index("col:taxonID")
        i_lang = hdr.index("col:language")
        i_v = hdr.index("col:name")
        for row in r:
            if len(row) <= i_v:
                continue
            rows += 1
            sciname = id_to_name.get(row[i_id])
            if not sciname:
                dropped_rank += 1
                continue
            if (row[i_lang] or "").strip().lower() not in ENGLISH:
                dropped_lang += 1
                continue
            v = (row[i_v] or "").strip()
            if v:
                by_name[sciname.strip().lower()].add(v)
    print(f"    {rows:,} rows, {len(by_name):,} species with a candidate "
          f"English name ({dropped_rank:,} non-species, {dropped_lang:,} "
          f"non-English skipped)")

    final: dict[str, str] = {}
    dropped = restated = 0
    for nm, vs in by_name.items():
        good = sorted(
            {v for v in vs if usable(v) and not is_restated_binomial(nm, v)},
            key=lambda s: (len(s), s))
        if not good:
            if vs:
                restated += sum(1 for v in vs if is_restated_binomial(nm, v))
            dropped += 1
            continue
        final[nm] = good[0]
    print(f"    {len(final):,} names usable ({dropped:,} fully filtered out, "
          f"including {restated:,} that were only the binomial restated, "
          f"{time.time() - started:.0f}s)")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(final, fh, ensure_ascii=False)
    print(f"  wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--index", default=INDEX)
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--sample", type=int, default=12)
    args = ap.parse_args()

    if args.build_index:
        return build_index(args.archive, args.index)

    if not os.path.exists(args.index):
        sys.exit(f"FATAL: no index at {args.index}. Build it with --build-index")
    with open(args.index, encoding="utf-8") as fh:
        index = json.load(fh)
    print(f"Wikidata vernacular index: {len(index):,} usable English names\n")

    tally: collections.Counter = collections.Counter()
    per_kingdom: collections.Counter = collections.Counter()
    samples: list[tuple] = []
    touched = 0
    started = time.time()

    for fam in iter_family_files():
        doc = fam.load()
        changed = False
        for node in iter_species(doc):
            tally["species"] += 1
            existing = (node.get("commonName") or "").strip()
            if existing:
                tally["already-has"] += 1
                continue
            tally["empty"] += 1
            name = (node.get("name") or "").strip().lower()
            cn = lookup(index, name)
            if not cn:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            per_kingdom[fam.kingdom] += 1
            changed = True
            if len(samples) < args.sample:
                samples.append((node.get("name"), cn))
            if args.apply:
                node["commonName"] = cn
                node["sourcedFrom"] = "wikidata"
        if changed:
            touched += 1
            if args.apply:
                fam.save(doc)

    empty = tally["empty"]
    print(f"{'=' * 66}")
    print(f"species scanned          {tally['species']:>9,}")
    print(f"already has commonName   {tally['already-has']:>9,}")
    print(f"empty                    {empty:>9,}")
    print(f"wikidata can fill        {tally['filled']:>9,}  "
          f"({100 * tally['filled'] / max(1, empty):.2f}%)")
    print(f"no match                 {tally['no-match']:>9,}")
    print(f"\nfiles: {touched:,}   ({time.time() - started:.0f}s)")
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
