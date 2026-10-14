#!/usr/bin/env python3
"""
Fill empty `commonName` from the ITIS archive's VernacularName table.

ITIS (Integrated Taxonomic Information System) is the primary source authority
for ~580k of our species (the `itis` key in `authorityIds`). Its
`VernacularName.tsv` carries 1,264,246 English and multilingual vernacular
names linked to TSNs, and `Taxon.tsv` + `Name.tsv` map those TSNs to
canonical scientific names.

    python3 scripts/enrichCommonNamesFromItis.py --build-index
    python3 scripts/enrichCommonNamesFromItis.py             # dry run
    python3 scripts/enrichCommonNamesFromItis.py --apply

The index maps canonicalName (lowercase) -> best English common name.
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

ITIS_ARCHIVE = os.path.expanduser("~/Downloads/itis/archive.zip")
INDEX = os.path.join("portal", "data", "itis-vernacular-index.json")

ENGLISH = {"en", "eng", "english"}
NON_LATIN = re.compile(
    r"[\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u3040-\u30FF"
    r"\u4E00-\u9FFF\uAC00-\uD7AF]"
)
NOT_A_NAME = re.compile(
    r"\b(agent of|caused by|disease|pathogen|syndrome|parasite of|vector of|"
    r"epibiont of|endophyte of|sign of)\b", re.I
)
REJECT = re.compile(r"\d|\bfamily\b|\bgenus\b|\bsp\.\b|\bspp\.\b|\bsubsp\.\b")
MAX_LEN = 60
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


def build_index(archive: str, out: str) -> int:
    if not os.path.exists(archive):
        sys.exit(f"FATAL: {archive} not found. Download ITIS archive from\n"
                 f"       https://www.itis.gov/")
    started = time.time()
    z = zipfile.ZipFile(archive)

    print("  VernacularName.tsv -> TSN/names ...", flush=True)
    t2v: dict[str, list] = collections.defaultdict(list)
    rows = dropped_lang = 0
    with z.open("VernacularName.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_tsn, i_v, i_l = (
            hdr.index("taxonID"),
            hdr.index("name"),
            hdr.index("language"),
        )
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_l:
                continue
            rows += 1
            v = (p[i_v] or "").strip()
            lang = (p[i_l] or "").strip().lower()
            if lang not in ENGLISH:
                dropped_lang += 1
                continue
            if v:
                t2v[p[i_tsn]].append(v)
    print(f"    {rows:,} rows, {len(t2v):,} taxa with a name "
          f"({dropped_lang:,} non-English skipped, {time.time()-started:.0f}s)")

    print("  Taxon.tsv + Name.tsv -> canonical names ...", flush=True)
    tsn_to_name: dict[str, str] = {}
    with z.open("Taxon.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_tsn, i_nameid = hdr.index("ID"), hdr.index("nameID")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_nameid:
                continue
            tsn_to_name[p[i_tsn]] = p[i_nameid]
    name_to_canon: dict[str, str] = {}
    with z.open("Name.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        i_id, i_canon = hdr.index("ID"), hdr.index("scientificName")
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_canon:
                continue
            name_to_canon[p[i_id]] = (p[i_canon] or "").strip()

    final: dict[str, str] = {}
    dropped = collections.Counter()
    for tsn, vs in t2v.items():
        canon = name_to_canon.get(tsn_to_name.get(tsn, ""))
        if not canon:
            continue
        good = sorted({v for v in vs if usable(v)}, key=lambda s: (len(s), s))
        if not good:
            dropped["all filtered"] += 1
            continue
        final[canon.lower()] = good[0]
    print(f"    {len(final):,} names usable ({dropped['all filtered']:,} fully filtered, "
          f"{time.time()-started:.0f}s)")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(final, fh, ensure_ascii=False)
    print(f"  wrote {out} ({os.path.getsize(out)/1e6:.0f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=ITIS_ARCHIVE)
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
    print(f"ITIS vernacular index: {len(index):,} usable English names\n")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from familyFiles import iter_family_files

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
                cn = index.get((node.get("name") or "").strip().lower())
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
                        node["sourcedFrom"] = "itis"
                    else:
                        node.pop("commonName", None)
                        if node.get("sourcedFrom") == "itis":
                            node.pop("sourcedFrom", None)
                changed = True
                continue
            if existing:
                tally["already-has"] += 1
                continue
            tally["empty"] += 1
            cn = index.get((node.get("name") or "").strip().lower())
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
                node["sourcedFrom"] = "itis"
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
    print(f"ITIS can fill            {tally['filled']:>9,}  "
          f"({tally['filled']/empty*100:.2f}%)" if empty else "empty                    0")
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
