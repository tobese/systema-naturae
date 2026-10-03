#!/usr/bin/env python3
"""
Fill empty `continents[]` from the GBIF Backbone's Distribution table.

Why this is the best-value thing in that dataset
-------------------------------------------------
The GBIF Backbone Taxonomy ships a 1.2 GB `Description.tsv` and a 493 MB
`Distribution.tsv`. Measured against the tree (`docs/reports/gbif-continents.md`):

| table | yield |
|---|---|
| Description.tsv, any prose | 1.33% |
| Description.tsv, after the genus-opening gate | 0.79% |
| **Distribution.tsv, continent codes** | **6.29%** — 75,237 species |

Descriptions score badly because they come from Plazi literature treatments and
there is very little for fungi or algae. Distributions come from the range maps
of the 105 source datasets instead, and those cover fungi well: fungi 20%,
protozoa 31%, chromista 7%.

Safety, and why no validation gate is needed
--------------------------------------------
Every other enricher needs a gate because prose can be attached to the wrong
taxon -- hence `enrichEmptySpecies.py`'s "must open with the genus" rule and
`fix_misattached_descriptions.py`. A two-letter country code mapped through a
fixed table cannot be mis-attached, so there is nothing to validate.

Two further guarantees:

- **Empty nodes only.** An existing `continents[]` is never read, let alone
  overwritten, so this cannot contradict curated data and cannot create a
  conflict. All 11,331 multi-continent hits are kept whole.
- **Idempotent.** A second run finds no empty nodes.

Provenance: GBIF Backbone Taxonomy, export 2023-08-28, CC-BY 4.0,
`gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c`.

Usage
-----
    python3 scripts/enrichContinentsFromGbif.py --build-index   # parse backbone.zip
    python3 scripts/enrichContinentsFromGbif.py                 # dry run
    python3 scripts/enrichContinentsFromGbif.py --apply

Read-only unless `--apply`. Writes `continents` and `sourcedFrom`, never a
description.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import sys
import time
import zipfile

BACKBONE = os.path.expanduser("~/Downloads/backbone.zip")
INDEX = os.path.join("portal", "data", "gbif-continents-index.json")

# countryCode -> our continent vocabulary. Only real ISO codes the backbone
# actually uses; `VALID_CONTINENTS` in sanity_scan.py is the authority and every
# value here is verified against it.
CC2CONT = {
    "GB": "Europe", "IE": "Europe", "FR": "Europe", "DE": "Europe", "ES": "Europe",
    "IT": "Europe", "NL": "Europe", "SE": "Europe", "NO": "Europe", "DK": "Europe",
    "FI": "Europe", "PL": "Europe", "RU": "Europe", "UA": "Europe", "PT": "Europe",
    "BE": "Europe", "AT": "Europe", "CH": "Europe", "CZ": "Europe", "GR": "Europe",
    "RO": "Europe", "HU": "Europe", "BG": "Europe", "RS": "Europe", "HR": "Europe",
    "SK": "Europe", "SI": "Europe", "LT": "Europe", "LV": "Europe", "EE": "Europe",
    "IS": "Europe", "IE ": "Europe", "GB ": "Europe",
    "US": "North America", "CA": "North America", "MX": "North America",
    "CU": "North America", "CR": "North America", "GT": "North America",
    "PA": "North America", "DO": "North America", "HN": "North America",
    "NI": "North America", "SV": "North America", "BZ": "North America",
    "JM": "North America", "TT": "North America", "BS": "North America",
    "PR": "North America", "HT": "North America",
    "BR": "South America", "AR": "South America", "PE": "South America",
    "CL": "South America", "CO": "South America", "VE": "South America",
    "EC": "South America", "BO": "South America", "PY": "South America",
    "UY": "South America", "GY": "South America", "SR": "South America",
    "GF": "South America", "BO ": "South America",
    "AF": "Africa", "ZA": "Africa", "EG": "Africa", "KE": "Africa", "NG": "Africa",
    "TZ": "Africa", "MA": "Africa", "DZ": "Africa", "ET": "Africa", "GH": "Africa",
    "TZ ": "Africa", "ZW": "Africa", "ZM": "Africa", "MZ": "Africa", "UG": "Africa",
    "SN": "Africa", "CI": "Africa", "CM": "Africa", "AO": "Africa", "MZ ": "Africa",
    "AU": "Australia", "NZ": "Australia", "PG": "Australia", "FJ": "Australia",
    "NC": "Australia", "VU": "Australia", "SB": "Australia", "WS": "Australia",
    "AQ": "Antarctica",
    # Africa, completed. The block above stopped at a handful of Anglophone and
    # North African countries, which was invisible until a source used ISO codes
    # for the whole continent: Afromoths lists 65 codes and only 17 resolved, so
    # 48 countries across Africa mapped to nothing at all. Kept here rather than
    # in that importer so there is still one country->continent authority.
    "AO": "Africa", "BF": "Africa", "BI": "Africa", "BJ": "Africa", "BW": "Africa",
    "CD": "Africa", "CF": "Africa", "CG": "Africa", "CI": "Africa", "CV": "Africa",
    "DJ": "Africa", "EH": "Africa", "ER": "Africa", "ET": "Africa", "GA": "Africa",
    "GH": "Africa", "GM": "Africa", "GN": "Africa", "GQ": "Africa", "GW": "Africa",
    "KM": "Africa", "LR": "Africa", "LS": "Africa", "LY": "Africa", "MA": "Africa",
    "MG": "Africa", "ML": "Africa", "MR": "Africa", "MU": "Africa", "MW": "Africa",
    "MZ": "Africa", "NA": "Africa", "NE": "Africa", "RE": "Africa", "RW": "Africa",
    "SC": "Africa", "SD": "Africa", "SH": "Africa", "SL": "Africa", "SN": "Africa",
    "SO": "Africa", "SS": "Africa", "ST": "Africa", "SZ": "Africa", "TD": "Africa",
    "TG": "Africa", "TZ": "Africa", "UG": "Africa", "YT": "Africa", "ZA": "Africa",
    "ZM": "Africa", "ZW": "Africa", "NG": "Africa", "EG": "Africa",
    # Gulf and Yemen, which Afromoths reaches across the Red Sea.
    "AE": "Asia", "BH": "Asia", "KW": "Asia", "MV": "Asia", "OM": "Asia",
    "QA": "Asia", "SA": "Asia", "YE": "Asia",
    # IO (Chagos) and TF (French Southern Territories) are deliberately absent.
    # Both are genuinely ambiguous rather than merely unlisted, and
    # osfLocalities.py already leaves the Chagos Archipelago unmapped on purpose
    # -- the same reasoning, so the omission stays visible in one place instead of
    # being quietly resolved differently by each source.
}

VALID_CONTINENTS = {
    "Europe", "Asia", "Africa", "North America",
    "South America", "Australia", "Oceania", "Antarctica",
}


def build_index(backbone: str, out: str) -> int:
    """taxonID -> [continents], joined to canonical names. ~90 s, ~2 GB RSS."""
    if not os.path.exists(backbone):
        sys.exit(f"FATAL: {backbone} not found. Download the GBIF Backbone Taxonomy from\n"
                 f"       https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c")
    z = zipfile.ZipFile(backbone)
    started = time.time()

    print("  Distribution.tsv -> taxonID/continents ...", flush=True)
    t2c: dict[str, set] = collections.defaultdict(set)
    rows = 0
    no_cc = 0
    with z.open("Distribution.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_cc = hdr.index("taxonID"), hdr.index("countryCode")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_cc:
                continue
            rows += 1
            cont = CC2CONT.get((p[i_cc] or "").strip())
            if cont:
                t2c[p[i_id]].add(cont)
            elif (p[i_cc] or "").strip():
                no_cc += 1
    print(f"    {rows:,} rows, {len(t2c):,} taxa with a continent "
          f"({no_cc:,} unmapped country codes, {time.time()-started:.0f}s)")

    print("  Taxon.tsv -> canonical names ...", flush=True)
    by_name: dict[str, set] = collections.defaultdict(set)
    with z.open("Taxon.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_canon = hdr.index("taxonID"), hdr.index("canonicalName")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_canon:
                continue
            c = t2c.get(p[i_id])
            if not c:
                continue
            nm = (p[i_canon] or "").strip().lower()
            if nm:
                by_name[nm].update(c)
    print(f"    {len(by_name):,} names ({time.time()-started:.0f}s)")

    bad = {x for v in by_name.values() for x in v} - VALID_CONTINENTS
    if bad:
        sys.exit(f"FATAL: produced continents outside the vocabulary: {sorted(bad)}. "
                 f"Refusing to write; fix CC2CONT rather than widening VALID_CONTINENTS.")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({k: sorted(v) for k, v in by_name.items()}, fh)
    print(f"  wrote {out} ({os.path.getsize(out)/1e6:.0f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default=BACKBONE)
    ap.add_argument("--index", default=INDEX)
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.build_index:
        return build_index(args.backbone, args.index)

    if not os.path.exists(args.index):
        sys.exit(f"FATAL: no index at {args.index}. Build it first:\n"
                 f"       python3 scripts/enrichContinentsFromGbif.py --build-index")
    with open(args.index, encoding="utf-8") as fh:
        index = json.load(fh)
    print(f"GBIF continent index: {len(index):,} names\n")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from familyFiles import iter_family_files
    from canonicalNames import lookup

    files = list(iter_family_files("."))
    tally: collections.Counter = collections.Counter()
    per_kingdom: collections.Counter = collections.Counter()
    would_write = 0
    touched = 0
    started = time.time()

    for path in files:
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
            if node.get("continents"):
                tally["already-has"] += 1
                continue
            tally["empty"] += 1
            conts = lookup(index, (node.get("name") or "").strip().lower())
            if not conts:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            per_kingdom[kingdom] += 1
            would_write += 1
            if args.apply:
                node["continents"] = list(conts)
                node["sourcedFrom"] = "gbif"
                changed = True
        if changed:
            touched += 1
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    empty = tally["empty"]
    filled = tally["filled"]
    print(f"{'=' * 66}")
    print(f"species scanned          {tally['species']:>9,}")
    print(f"already has continents   {tally['already-has']:>9,}")
    print(f"empty                    {empty:>9,}")
    print(f"GBIF can fill            {filled:>9,}  ({filled/empty*100:.2f}%)")
    print(f"no match                 {tally['no-match']:>9,}")
    print(f"\nfiles touched: {touched:,}   ({time.time()-started:.0f}s)")
    print("by kingdom:")
    for k, v in per_kingdom.most_common():
        print(f"  {k:<12}{v:>8,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    else:
        print(f"\n  wrote {would_write:,} continents across {touched:,} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())