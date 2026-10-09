#!/usr/bin/env python3
"""Import World Spider Catalog distribution as `continents` on spider species.

The catalogue is a DwCA of three TSVs. `Distribution.tsv` is
(taxonID, gazetteer, area) -- 66,766 rows naming 7,184 distinct places, from
`China` and `Brazil` down to `Australia (Queensland)` and `Hispaniola` -- and
`NameUsage.tsv` carries the names. Nothing else in it is new to us: the species,
the families and the synonyms are all held already, which is why this importer
reads distribution and writes nothing else.

Why it is worth doing: of the 54,738 tree species whose names the catalogue
distributes, 53,582 carry no continent at all. That is 2.3% of the
MISSING_CONTINENTS backlog, and it is where a spider checklist is worth more
than a general one -- GBIF has almost no country data for Araneae, so there is
nothing here to conflict with.

Only the records that resolve COMPLETELY are written. `continent_for_area` is
all-or-nothing by design, and that is what this relies on: a record reading
"Canada, USA, and an island the table has never heard of" must not become
North America, because that states a range narrower than the source does. A
species with no continent is the state it was already in; a species with a
narrower one is a new error. So 48,738 of the catalogue's 65,452 distributed
names are importable now and the other 16,289 are left alone rather than
guessed at -- the largest single block of those needs a country table, which
`scripts/osfLocalities.py` does not have (it has no `USA`, and never needed
one, because the Orthoptera file records TDWG level-1/3/4 names instead).

Existing continents are never overwritten. 1,156 of the matching species have
one already and keep it, on the same reasoning: a merged dedupe prefers a
record that has data over one that does not, so the richer record should win
here too. `sourcedFrom` is left alone for the same reason -- it records which
source contributed the species, and a continent learned from a spider
catalogue does not stop a species having arrived from BOLD.

Matching is on the bare binomial, which is the same test the rest of the
tooling uses and is loose in the way that implies -- `Oecanthus nigricornis`
in Gryllidae and in Oecanthidae both match the catalogue entry. It does not
matter for this field: both are the same species and the range is the same
either way.

    python3 scripts/importWsc.py              # dry run
    python3 scripts/importWsc.py --apply
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import osfLocalities as OSF  # noqa: E402
import sources  # noqa: E402
from tree import iter_family_files, save_json  # noqa: E402

SLUG = "world-spider-catalog"
ARCHIVE = "wsc.zip"
SOURCE = "world spider catalog"


def _rows(z: zipfile.ZipFile, member: str):
    with z.open(member) as raw:
        for line in io.TextIOWrapper(raw, encoding="utf-8", errors="replace"):
            yield line


def _read(z: zipfile.ZipFile, member: str):
    """A TSV member as a dict of column -> list, so a 14MB file is one read."""
    rdr = csv.DictReader(_rows(z, member), delimiter="\t")
    cols = rdr.fieldnames or []
    data = {c: [] for c in cols}
    for row in rdr:
        for c in cols:
            data[c].append(row.get(c) or "")
    return data


def bare(name: str) -> str:
    return (name or "").split(" (")[0].strip()


def load_distribution(archive: str):
    """name -> {areas}, and the count of names whose every area resolves."""
    with zipfile.ZipFile(archive) as z:
        dist = _read(z, "Distribution.tsv")
        usage = _read(z, "NameUsage.tsv")

    tids = collections.defaultdict(set)
    for tid, area in zip(dist["col:taxonID"], dist["col:area"]):
        if tid and area:
            tids[tid.strip()].add(area.strip())

    # `scientificName` is empty for most rows in this export; the name lives in
    # genericName + specificEpithet, and uninomial for the ranks above species.
    id_col = "col:ID"
    sci = usage.get("col:scientificName") or []
    gen = usage.get("col:genericName") or []
    spe = usage.get("col:specificEpithet") or []
    uni = usage.get("col:uninomial") or []

    by_name = collections.defaultdict(set)
    for i, tid in enumerate(usage[id_col]):
        tid = tid.strip()
        if tid not in tids:
            continue
        name = bare(sci[i]) if i < len(sci) else ""
        if not name and gen and spe:
            g, s = gen[i].strip(), spe[i].strip()
            if g and s:
                name = f"{g} {s}"
        if not name and uni:
            name = bare(uni[i])
        if name:
            by_name[name] |= tids[tid]
    return by_name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    archive = os.path.join(sources.archive_dir(SLUG), ARCHIVE)
    if not os.path.exists(archive):
        print(f"FATAL: {archive} not found")
        return 2
    t0 = time.time()

    by_name = load_distribution(archive)
    print(f"  catalogue: {len(by_name):,} distributed names "
          f"({time.time()-t0:.0f}s)")

    # A name is importable only when EVERY area it lists resolves.
    resolved = {}
    partial = 0
    for name, areas in by_name.items():
        conts = set()
        ok = True
        for a in areas:
            c = OSF.continent_for_area(a)
            if not c:
                ok = False
                break
            conts.update(c)
        if ok and conts:
            resolved[name] = sorted(conts)
        else:
            partial += 1
    print(f"  fully resolved: {len(resolved):,}   not resolvable: {partial:,}")

    hit = miss = already = 0
    wrote = 0
    touched_files = 0
    added = collections.Counter()
    for fam in iter_family_files("animalia"):
        doc = json.load(open(fam.path, encoding="utf-8"))
        changed = False
        stack = list(doc.get("children") or [])
        while stack:
            n = stack.pop()
            if n.get("rank") == "SPECIES":
                c = resolved.get(bare(n.get("name") or ""))
                if c:
                    hit += 1
                    if n.get("continents"):
                        already += 1
                    else:
                        n["continents"] = c
                        for x in c:
                            added[x] += 1
                        changed = True
                        wrote += 1
                else:
                    miss += 1
            stack.extend(n.get("children") or [])
        if changed:
            touched_files += 1
            if args.apply:
                save_json(fam.path, doc)

    print(f"\n  tree species matching the catalogue: {hit:,}")
    print(f"    already had a continent, left alone: {already:,}")
    print(f"    continents written:                 {wrote:,} "
          f"in {touched_files:,} files")
    print("  by continent:")
    for c, n in added.most_common():
        print(f"    {n:>7,}  {c}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    else:
        print(f"\n  wrote {touched_files:,} family files")
    return 0


if __name__ == "__main__":
    sys.exit(main())