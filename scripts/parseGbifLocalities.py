#!/usr/bin/env python3
"""
Recover continents from GBIF `Distribution.locality` where `countryCode` is empty.

Why
---
`MISSING_CONTINENTS` is 1,109,463 species after the `countryCode` pass filled
78,910. Of the 5,530,297 rows in `Distribution.tsv`, **3,449,018 have a
`locality` but no `countryCode`** -- so the earlier pass read the single most
reliable column and left 62% of the table untouched.

Those localities are not prose. 80.1% are Title Case place or region names:

    150,091  Global
     40,896  Southern Asia
     37,543  Colombia
     37,167  Africa
     28,755  China South-Central
     23,408  Cape Provinces
     22,190  New Guinea

An explicit gazetteer, not inference
------------------------------------
This is deliberately a lookup table, not a parser. The tempting alternative --
infer a continent from a free-text place name -- is how a Finnish swamp ends up
in Antarctica, and the cost of that here is a wrong range map on a species page.

So: `GAZETTEER` maps a locality string to a continent, explicitly, one entry per
place. A string not in the table contributes nothing. There is no fallback, no
fuzzy match, no substring search, and no partial parse. That makes a wrong answer
structurally impossible rather than merely unlikely.

`Global` is excluded, and deliberately so: 150,091 rows say `Global` and it means
"the distribution spans continents", not "every continent". Filling all seven
would be worse than leaving it empty, since it is a different claim.

What is left out, and why
--------------------------
| shape | rows | why excluded |
|---|---|---|
| Title Case | 2,762,988 | parsed via the gazetteer |
| prose | 433,958 | `Europe & Northern Asia (excluding China)` needs region logic |
| comma-separated | 125,271 | `Brazil(Rio Grande do Sul, Colombia, Peru)` mixes countries and states |
| ALL CAPS | 96,665 | `YUG`, `YUGCR` are former-Yugoslavia codes; mapping them is a history lesson, not a gazetteer entry |
| `Region: detail` | 16,231 | `North America: United States of America (Kentucky and Tennessee)` needs the prefix logic that the prose case needs |
| coordinates | 13,905 | `7` is not a place |

The first comma-separated row is also a trap worth naming: `Brazil(Rio Grande do
Sul, Colombia, French Guiana, Peru, Venezuela)` contains five countries and is
attributed to the first. Reading the first token would give Brazil alone and be
wrong in the way that matters.

Usage
-----
    python3 scripts/parseGbifLocalities.py --report
    python3 scripts/parseGbifLocalities.py --apply

`--report` prints the top unmatched localities, which is how the gazetteer grows:
each round, whatever is left at the top is either added with its continent or
left alone deliberately. Read-only unless `--apply`.
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
OUT_INDEX = os.path.join("portal", "data", "gbif-locality-index.json")

# Explicit locality -> continent. Only unambiguous, whole-string entries.
#
# Countries (ISO 3166 short names as GBIF spells them), plus the regions that
# appear as their own locality values.
GAZETTEER: dict[str, str] = {}


def _c(continent: str, *places: str) -> None:
    for p in places:
        GAZETTEER[p] = continent


_c("Europe", "Albania", "Andorra", "Austria", "Azores", "Belarus", "Belgium",
   "Bosnia and Herzegovina", "Bulgaria", "Canary Is.", "Corsica", "Croatia",
   "Cyprus", "Czech Republic", "Denmark", "Estonia", "Faroe Is.", "Finland",
   "France", "Germany", "Gibraltar", "Greece", "Greenland", "Hungary",
   "Iceland", "Ireland", "Isle of Man", "Italy", "Latvia", "Liechtenstein",
   "Lithuania", "Luxembourg", "Madeira", "Malta", "Moldova", "Monaco",
   "Netherlands", "Norway", "Poland", "Portugal", "Romania", "Russia",
   "Sardinia", "Sicily", "Slovakia", "Slovenia", "Spain", "Sweden",
   "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Yugoslavia",
   "Svalbard", "Jan Mayen", "Svalbard and Jan Mayen", "Åland Islands")

_c("North America", "Antigua and Barbuda", "Aruba", "Bahamas", "Barbados",
   "Belize", "Bermuda", "Canada", "Cayman Is.", "Costa Rica", "Cuba",
   "Dominica", "Dominican Republic", "El Salvador", "Grenada", "Guatemala",
   "Haiti", "Honduras", "Jamaica", "Mexico", "Netherlands Antilles",
   "Nicaragua", "Panama", "Puerto Rico", "Saint Kitts and Nevis",
   "Saint Lucia", "Saint Vincent and the Grenadines", "Trinidad and Tobago",
   "Turks and Caicos Is.", "United States of America", "USA",
   "Virgin Is.", "Bermuda Is.", "Cayman Is.")

_c("South America", "Argentina", "Bolivia", "Brazil", "Chile", "Colombia",
   "Ecuador", "Falkland Is.", "French Guiana", "Guyana", "Paraguay", "Peru",
   "Suriname", "Uruguay", "Venezuela")

_c("Africa", "Cape Provinces", "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso",
   "Burundi", "Cameroon", "Cape Provinces", "Cape Verde", "Central African Republic",
   "Chad", "Comoros", "Congo", "Djibouti", "Egypt", "Equatorial Guinea",
   "Eritrea", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau",
   "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
   "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique",
   "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe",
   "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa",
   "St. Helena", "Sudan", "Swaziland", "Tanzania", "Togo", "Tunisia",
   "Uganda", "Zaire", "Zambia", "Zimbabwe", "Reunion", "Mayotte",
   "Sao Tome & Principe", "Kalahari", "Cape Region")

_c("Asia", "Afghanistan", "Armenia", "Azerbaijan", "Bahrain", "Bangladesh",
   "Bhutan", "Brunei", "Cambodia", "China", "Cyprus", "Georgia", "Hong Kong",
   "India", "Indonesia", "Iran", "Iraq", "Israel", "Japan", "Jordan",
   "Kazakhstan", "Korea", "Kuwait", "Kyrgyzstan", "Laos", "Lebanon", "Macao",
   "Malaysia", "Maldives", "Mongolia", "Myanmar", "Nepal", "Oman", "Pakistan",
  ("Palestine"), "Philippines", "Qatar", "Saudi Arabia", "Singapore",
   "Sri Lanka", "Syria", "Taiwan", "Tajikistan", "Thailand", "Timor",
   "Turkey", "Turkmenistan", "UAE", "Uzbekistan", "Vietnam", "Yemen",
   "China South-Central", "China Southeast", "China North-Central", "Mongolia",
   "Sikkim", "Indian Subcontinent", "Southern Asia", "Central Asia",
   "Western Asia", "Eastern Asia", "Sakhalin", "Ryukyu Is.")

_c("Australia", "New Caledonia", "New Zealand", "Norfolk Is.",
   "Papua New Guinea", "New Guinea", "Queensland", "New South Wales",
   "Northern Territory", "South Australia", "Tasmania", "Victoria",
   "Western Australia", "Lord Howe Is.", "Christmas Is.", "Cocos Is.",
   "Melanesia", "Micronesia", "Polynesia", "Wallis and Futuna", "Samoa",
   "Tonga", "Fiji", "Solomon Is.", "Vanuatu", "New Hebrides", "Australia South",
   "Australia Southeast", "Australia East", "Australia Central")

_c("Antarctica", "Antarctic Peninsula", "Ross Sea", "Weddell Sea",
   "Antarctique")

# Multi-region values: unambiguous because they name whole continents.
#
# NOT included: bare continent names (`Africa`, `North America`, ...), 129,175
# rows and the single most error-prone class here. A continent is not evidence
# of a distribution, it is a restatement of one -- and GBIF carries demonstrably
# wrong ones. `Stenostira scita`, a New Zealand moth, has a distribution row
# reading `locality=Africa` and nothing else. Admitting continent names let a
# single bad row put a wrong range map on a species, which is worse than leaving
# the node empty. Excluded deliberately, and the cost is real: those 129,175 rows
# are left unharvested rather than harvested unreliably.
for _r in ["Neotropics", "Nearctic", "Palearctic", "Afrotropic", "Afrotropical",
           "Indomalaya", "Sino-Japan", "Saharo-Arabian", "Madrean", "Neotropic",
           "Holarctic", "Boreal", "Austral", "Oceanic"]:
    GAZETTEER.setdefault(_r, {
        "Neotropics": "South America", "Nearctic": "North America",
        "Palearctic": "Europe", "Afrotropic": "Africa",
        "Afrotropical": "Africa", "Indomalaya": "Asia", "Sino-Japan": "Asia",
        "Saharo-Arabian": "Africa", "Madrean": "North America",
        "Neotropic": "South America", "Holarctic": "Europe",
        "Boreal": "Europe", "Austral": "Australia", "Oceanic": "Australia",
    }[_r])

# Never a continent: "this distribution spans continents".
MULTI_CONTINENT = {"Global", "Cosmopolitan", "Worldwide", "world wide"}

VALID_CONTINENTS = {
    "Europe", "Asia", "Africa", "North America",
    "South America", "Australia", "Oceania", "Antarctica",
}


def gazetteer_size() -> int:
    return len(GAZETTEER)


def build_index(backbone: str, out: str) -> int:
    if not os.path.exists(backbone):
        sys.exit(f"FATAL: {backbone} not found")
    z = zipfile.ZipFile(backbone)
    started = time.time()

    print("  Distribution.tsv -> taxonID/locality ...", flush=True)
    t2c: dict[str, set] = collections.defaultdict(set)
    rows = no_cc = multi = matched = 0
    with z.open("Distribution.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_cc, i_loc = hdr.index("taxonID"), hdr.index("countryCode"), hdr.index("locality")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_loc:
                continue
            rows += 1
            if (p[i_cc] or "").strip():
                continue          # already handled by the countryCode pass
            no_cc += 1
            loc = (p[i_loc] or "").strip()
            if not loc:
                continue
            if loc in MULTI_CONTINENT:
                multi += 1
                continue
            cont = GAZETTEER.get(loc)
            if cont:
                t2c[p[i_id]].add(cont)
                matched += 1
    print(f"    {rows:,} rows, {no_cc:,} without a countryCode, {matched:,} matched "
          f"the gazetteer, {multi:,} skipped as multi-continent ({time.time()-started:.0f}s)")

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

    bad = {x for v in by_name.values() for x in v} - VALID_CONTINENTS
    if bad:
        sys.exit(f"FATAL: gazetteer produced continents outside the vocabulary: "
                 f"{sorted(bad)}. Fix GAZETTEER rather than widening VALID_CONTINENTS.")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({k: sorted(v) for k, v in by_name.items()}, fh)
    print(f"  wrote {out} ({len(by_name):,} names, {os.path.getsize(out)/1e6:.0f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default=BACKBONE)
    ap.add_argument("--index", default=OUT_INDEX)
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--top-unmatched", type=int, default=0)
    args = ap.parse_args()

    if args.top_unmatched:
        return top_unmatched(args.backbone, args.top_unmatched)

    if args.build_index:
        return build_index(args.backbone, args.index)

    if not os.path.exists(args.index):
        sys.exit(f"FATAL: no index at {args.index}. Build it with --build-index")
    with open(args.index, encoding="utf-8") as fh:
        index = json.load(fh)
    print(f"locality-derived continent index: {len(index):,} names\n")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from familyFiles import iter_family_files

    tally: collections.Counter = collections.Counter()
    per_kingdom: collections.Counter = collections.Counter()
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
            if node.get("continents"):
                tally["already-has"] += 1
                continue
            tally["empty"] += 1
            conts = index.get((node.get("name") or "").strip().lower())
            if not conts:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            per_kingdom[kingdom] += 1
            changed = True
            if args.apply:
                node["continents"] = list(conts)
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
    print(f"already has continents   {tally['already-has']:>9,}")
    print(f"empty                    {empty:>9,}")
    print(f"locality index can fill  {tally['filled']:>9,}  "
          f"({tally['filled']/empty*100:.2f}%)")
    print(f"no match                 {tally['no-match']:>9,}")
    print(f"\nfiles: {touched:,}   ({time.time()-started:.0f}s)")
    print("by kingdom:")
    for k, v in per_kingdom.most_common():
        print(f"  {k:<12}{v:>8,}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    else:
        print(f"\n  wrote {tally['filled']:,} continents across {touched:,} files")
    return 0


def top_unmatched(backbone: str, n: int) -> int:
    """What is left at the top, so the gazetteer can grow deliberately."""
    z = zipfile.ZipFile(backbone)
    unmatched: collections.Counter = collections.Counter()
    with z.open("Distribution.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_cc, i_loc = hdr.index("countryCode"), hdr.index("locality")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_loc or (p[i_cc] or "").strip():
                continue
            loc = (p[i_loc] or "").strip()
            if not loc or loc in MULTI_CONTINENT or loc in GAZETTEER:
                continue
            unmatched[loc] += 1
    print(f"{gazetteer_size()} gazetteer entries; {len(unmatched):,} distinct unmatched localities\n")
    print(f"top {n} unmatched (candidates for the gazetteer):")
    for loc, c in unmatched.most_common(n):
        print(f"  {c:>7,}  {loc[:74]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
