#!/usr/bin/env python3
"""The pending-family store: families that exist but that we do not hold.

Not an empty skeleton. Nothing here is pre-created in the tree. This is a
worklist of *misses* -- the families a source knows about and our taxonomy
lacks -- so that when one is imported, or scaffolded on demand, the miss is
already written down and nobody has to re-derive it from a refusal count.

Data lives on the external volume at

    /Volumes/MacieExternal/sources/pending/families.jsonl

because it is derived from the archives and weighs more than belongs in git.
`portal/data/pending-families.jsonl` is a symlink to it, and is gitignored, the
same treatment name-parse-index.jsonl gets.

Two kinds of row share the file, distinguished by `source`:

  * `gbif-backbone:53147` -- seeded from the GBIF Backbone DwCA. GBIF is the
    global answer to "what actually exists": 24,324 real family names across
    all kingdoms, of which the taxonomy holds 14,203. `species` is how many
    accepted GBIF species sit in that family, i.e. what a scaffold would gain.
  * anything else -- a family an import hit and could not place, recorded at
    import time by `add`. `species` is how many offered species wanted it.

The union is the worklist; `report` prints it, and marks rows whose family has
since appeared in the tree, which is the actionable part: those are ready to be
scaffolded or imported.

    python3 scripts/pendingFamilies.py seed      # rebuild the global gap
    python3 scripts/pendingFamilies.py add --family Abelisauridae --kingdom Animalia
    python3 scripts/pendingFamilies.py report
    python3 scripts/pendingFamilies.py report --scaffoldable
"""
import argparse
import collections
import csv
import glob
import io
import json
import os
import re
import sys
import zipfile
from datetime import date

# Resolved through scripts/sources.py, which honours SN_SOURCES_ROOT. These two
# were the last hardcoded /Volumes paths in an importer's write path, and the
# failure mode was silent and late: importColChecklist.py --apply wrote its
# refusals to the pending store LAST, so a run on any machine without the
# Macie volume got all the way through the import and then died with
# `PermissionError: '/Volumes'` -- after the tree walk, not before it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources as _sources  # noqa: E402

_ROOT = _sources.ROOT
STORE = os.path.join(_ROOT, "pending", "families.jsonl")
LINK = "portal/data/pending-families.jsonl"
GBIF = os.path.join(_ROOT, "archives", "gbif-backbone", "backbone.zip")
GBIF_SOURCE = "gbif-backbone:53147"

TAXONOMIES = (
    "portal/data/taxonomy.json",
    "portal/data/taxonomy-plantae-snippet.json",
    "portal/data/taxonomy-fungi.json",
    "portal/data/taxonomy-chromista.json",
    "portal/data/taxonomy-protozoa.json",
    "portal/data/taxonomy-archaea.json",
)

# GBIF's family-rank taxa are not all names: 2,298 of the 26,622 are internal
# codes like "0-14-0-20-34-12" and "01-FULL-45-10b". Keep only things shaped like
# a family name, which also drops our own placeholders ("..._incertae_sedis").
FAMILY_NAME = re.compile(r"^[A-Z][A-Za-z]+(idae|aceae|ales|inae|oidea|eae)$")

KINGDOM_FILE = {
    "animalia": "portal/data/taxonomy.json",
    "plantae": "portal/data/taxonomy-plantae-snippet.json",
    "fungi": "portal/data/taxonomy-fungi.json",
    "chromista": "portal/data/taxonomy-chromista.json",
    "protozoa": "portal/data/taxonomy-protozoa.json",
    "archaea": "portal/data/taxonomy-archaea.json",
}


def ensure_link():
    """The repo path is a symlink to the external store, so both work."""
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    if not os.path.exists(STORE):
        open(STORE, "a").close()
    if os.path.islink(LINK):
        if os.readlink(LINK) == STORE:
            return
        os.unlink(LINK)
    elif os.path.exists(LINK):
        raise SystemExit(f"{LINK} exists and is not a symlink -- refusing to "
                         f"replace it; move it aside first")
    os.symlink(STORE, LINK)
    print(f"  linked {LINK} -> {STORE}")


def held_families():
    """Every family name the taxonomy holds, lowercased, per kingdom."""
    out = {}
    for f in TAXONOMIES:
        if not os.path.exists(f):
            continue
        kingdom = os.path.basename(f).replace("taxonomy-", "").replace(
            ".json", "").replace(".json", "")
        kingdom = "animalia" if kingdom == ".json" else kingdom
        tree = json.load(open(f, encoding="utf-8"))

        def walk(n):
            if n.get("rank") == "FAMILY" and n.get("name"):
                out.setdefault(n["name"].strip().lower(), set()).add(kingdom)
            for c in n.get("children") or []:
                walk(c)
        walk(tree)
    return out


def read_store():
    rows = []
    if os.path.exists(STORE):
        with open(STORE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return rows


def write_store(rows):
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, STORE)


def cmd_seed(_args):
    """Rebuild the GBIF half of the worklist from the local DwCA."""
    csv.field_size_limit(sys.maxsize)
    ensure_link()
    if not os.path.exists(GBIF):
        raise SystemExit(f"  {GBIF} is missing -- the GBIF Backbone archive has "
                         f"not been fetched")
    z = zipfile.ZipFile(GBIF)
    fams = {}          # family name -> [kingdom, species count]
    print("  scanning GBIF Backbone Taxon.tsv (7.7M rows)...")
    with z.open("Taxon.tsv") as fh:
        rd = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8",
                                              errors="replace"), delimiter="\t")
        for r in rd:
            if (r.get("taxonomicStatus") or "").strip() not in (
                    "accepted", "provisionally accepted"):
                continue
            rank = (r.get("taxonRank") or "").strip()
            if rank not in ("family", "species"):
                continue
            name = (r.get("canonicalName") or r.get("scientificName") or "").strip()
            if rank == "family":
                if not FAMILY_NAME.match(name):
                    continue
                slot = fams.setdefault(name, [(r.get("kingdom") or "").strip(), 0])
            else:
                fam = (r.get("family") or "").strip()
                if fam in fams:
                    fams[fam][1] += 1
    held = held_families()
    held_lower = set(held)
    today = date.today().isoformat()
    rows = []
    kept = 0
    for name, (kingdom, species) in fams.items():
        if name.lower() in held_lower:
            continue
        rows.append({"family": name, "kingdom": kingdom, "source": GBIF_SOURCE,
                     "species": species, "firstSeen": today,
                     "reason": "not in taxonomy"})
        kept += 1
    # keep any non-GBIF rows an import recorded; they are not regenerable here
    other = [r for r in read_store() if r.get("source") != GBIF_SOURCE]
    rows.extend(other)
    write_store(rows)
    by_k = collections.Counter(r["kingdom"] or "?" for r in rows
                                if r.get("source") == GBIF_SOURCE)
    print(f"  GBIF families held by the taxonomy: {len(held_lower):,}")
    print(f"  GBIF families missing:               {kept:,}")
    for k, n in by_k.most_common():
        print(f"      {k or '?':12s} {n:>7,}")
    print(f"  non-GBIF rows carried through:      {len(other):,}")
    print(f"  wrote {len(rows):,} rows to {STORE}")


def add_family(family, kingdom="", species=0, source="manual", reason=""):
    """Record one missed family. Callable from an importer mid-run."""
    ensure_link()
    fam = family.strip()
    if not fam:
        return False
    rows = read_store()
    for r in rows:
        if (r.get("family") or "").lower() == fam.lower():
            r["species"] = int(r.get("species") or 0) + int(species or 0)
            if not r.get("kingdom") and kingdom:
                r["kingdom"] = kingdom
            break
    else:
        rows.append({"family": fam, "kingdom": kingdom or "", "source": source,
                     "species": int(species or 0),
                     "firstSeen": date.today().isoformat(),
                     "reason": reason or "not in taxonomy"})
    write_store(rows)
    return True


def cmd_add(args):
    add_family(args.family, kingdom=args.kingdom, species=args.species,
               source=args.source or "manual", reason=args.reason or "")
    print(f"  pending: {args.family} (+{args.species})")


def cmd_report(args):
    rows = read_store()
    if not rows:
        print("  pending store is empty -- run `seed` first")
        return
    held = held_families()
    still, ready = [], []
    for r in rows:
        (ready if (r.get("family") or "").lower() in held else still).append(r)
    by_src = collections.Counter(r.get("source") or "?" for r in rows)
    print(f"  pending families: {len(rows):,}")
    for s, n in by_src.most_common():
        print(f"      {s:28s} {n:>7,}")
    print(f"  still missing from the taxonomy: {len(still):,}")
    print(f"  now present in the taxonomy:     {len(ready):,}"
          f"   <- scaffoldable or ready to import")
    tot = sum(int(r.get("species") or 0) for r in rows)
    print(f"  species those families would add: {tot:,}")
    out = ready if args.scaffoldable else still
    for r in sorted(out, key=lambda r: -int(r.get("species") or 0))[:args.limit]:
        print(f"      {int(r.get('species') or 0):>6,}  "
              f"{(r.get('kingdom') or '?'):10s} {(r.get('family'))}"
              f"   [{r.get('source')}]")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed", help="rebuild the global gap from the GBIF Backbone")
    p = sub.add_parser("add", help="record a family an import could not place")
    p.add_argument("--family", required=True)
    p.add_argument("--kingdom", default="")
    p.add_argument("--species", type=int, default=0)
    p.add_argument("--source", default="")
    p.add_argument("--reason", default="")
    p = sub.add_parser("report", help="what is pending, and what is now doable")
    p.add_argument("--scaffoldable", action="store_true",
                   help="only rows whose family is now in the taxonomy")
    p.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()
    {"seed": cmd_seed, "add": cmd_add, "report": cmd_report}[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
