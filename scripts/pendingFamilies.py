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

`report --scaffoldable` splits that actionable part further, because a family
node existing in taxonomy.json is not the same as being importable -- it also
needs a data file on disk (see `family_data_files()`). Rows missing one are
printed separately ("registered but no data file yet") instead of being
lumped in with genuinely ready rows, which otherwise just hit
importColChecklist.py's "N files found, skipping" silently on re-import --
the bug that cost the EUNIS import 20 species to xanthorrhoeaceae having no
file. Genuinely ready rows are grouped by `archive` (the path an importer was
invoked with, recorded by add_family() since this session) with the literal
re-import command to run -- closing the loop from "this family is ready" to
"run this" without manually figuring out which of ~180 archives offered it.

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


def held_family_slugs():
    """family name (lowercased) -> appSlug, for the families that have one.

    A family can be `held` (its FAMILY node exists in taxonomy.json) without
    being importable yet -- it also needs a data file on disk, and the node
    carries the appSlug that names it. Separate from held_families() because
    most callers only need the kingdom set.
    """
    out = {}
    for f in TAXONOMIES:
        if not os.path.exists(f):
            continue
        tree = json.load(open(f, encoding="utf-8"))

        def walk(n):
            if n.get("rank") == "FAMILY" and n.get("name") and n.get("appSlug"):
                out[n["name"].strip().lower()] = n["appSlug"]
            for c in n.get("children") or []:
                walk(c)
        walk(tree)
    return out


def family_data_files():
    """appSlug (lowercased) -> data file path, for every family file on disk.

    Same index importColChecklist.py builds per run (basename -> path glob
    over taxonomy/*/**/src/data/*.json) -- built once here too, so
    report --scaffoldable can tell "family registered, file missing" (the
    xanthorrhoeaceae/EUNIS class of bug) apart from "genuinely ready".
    """
    out = {}
    for path in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        slug = os.path.basename(path)[:-5].lower()
        out.setdefault(slug, []).append(path)
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
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STORE), prefix="families.jsonl.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(tmp, STORE)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


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


def add_families(records, source="manual", reason="", archive=""):
    """Record many missed families in one read/write of the store.

    `records` is an iterable of `(family, kingdom, species)`. Importers refuse
    thousands of families in a single run; calling `add_family` per family
    rewrote the whole 17.8k-row store each time (GBIF backbone: 7,211 rewrites
    of ~4 MB, tens of minutes of pure JSON encoding). This reads once, applies
    every record, and writes once.

    `archive` is the literal path the importer was invoked with -- not
    derivable later from `source` (which is often a generic tag like
    "checklistbank:archive" when the archive's own metadata carries no
    title/key; see slug_hint() in importColChecklist.py). Without it,
    closing the loop on a scaffoldable family means manually figuring out
    which of ~180 archives to re-run; with it, report --scaffoldable can
    print the exact command.
    """
    ensure_link()
    rows = read_store()
    index = {}
    for r in rows:
        index.setdefault((r.get("family") or "").lower(), r)
    added = 0
    for family, kingdom, species in records:
        fam = (family or "").strip()
        if not fam:
            continue
        r = index.get(fam.lower())
        if r is not None:
            r["species"] = int(r.get("species") or 0) + int(species or 0)
            if not r.get("kingdom") and kingdom:
                r["kingdom"] = kingdom
            if not r.get("archive") and archive:
                r["archive"] = archive
        else:
            r = {"family": fam, "kingdom": kingdom or "", "source": source,
                 "species": int(species or 0),
                 "firstSeen": date.today().isoformat(),
                 "reason": reason or "not in taxonomy",
                 "archive": archive or ""}
            rows.append(r)
            index[fam.lower()] = r
        added += 1
    if added:
        write_store(rows)
    return added


def add_family(family, kingdom="", species=0, source="manual", reason="", archive=""):
    """Record one missed family. Thin wrapper over `add_families`."""
    return add_families([(family, kingdom, species)], source=source,
                        reason=reason, archive=archive) == 1


def cmd_add(args):
    add_family(args.family, kingdom=args.kingdom, species=args.species,
               source=args.source or "manual", reason=args.reason or "",
               archive=args.archive or "")
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

    if not args.scaffoldable:
        for r in sorted(still, key=lambda r: -int(r.get("species") or 0))[:args.limit]:
            print(f"      {int(r.get('species') or 0):>6,}  "
                  f"{(r.get('kingdom') or '?'):10s} {(r.get('family'))}"
                  f"   [{r.get('source')}]")
        return

    # A family node existing in taxonomy.json (held) is not the same as being
    # importable: the importer also needs a data FILE for it on disk, keyed
    # by appSlug (see family_data_files()). Without this split, a family that
    # is "ready" by node alone still gets silently skipped by
    # importColChecklist.py's own "N files found, skipping" -- the exact
    # xanthorrhoeaceae/EUNIS bug this report would otherwise have missed.
    slugs = held_family_slugs()
    files = family_data_files()
    importable, needs_file = [], []
    for r in ready:
        slug = slugs.get((r.get("family") or "").lower(), "")
        hits = files.get(slug.lower(), []) if slug else []
        (importable if len(hits) == 1 else needs_file).append(r)

    if needs_file:
        print(f"\n  registered but no data file yet ({len(needs_file)}) -- "
              f"scaffold the file before re-importing, same fix as "
              f"xanthorrhoeaceae:")
        for r in sorted(needs_file, key=lambda r: -int(r.get("species") or 0))[:args.limit]:
            print(f"      {int(r.get('species') or 0):>6,}  "
                  f"{(r.get('kingdom') or '?'):10s} {(r.get('family'))}")

    if not importable:
        print("\n  nothing importable yet (every ready family still needs a data file)")
        return

    by_archive = collections.defaultdict(list)
    for r in importable:
        by_archive[r.get("archive") or ""].append(r)

    print(f"\n  importable now ({len(importable)}), grouped by source to re-run:")
    for archive, group in sorted(by_archive.items(), key=lambda kv: -sum(int(r.get("species") or 0) for r in kv[1])):
        total = sum(int(r.get("species") or 0) for r in group)
        fams = ", ".join(sorted({r.get("family") for r in group})[:5])
        more = f" (+{len(group) - 5} more)" if len(group) > 5 else ""
        if archive:
            print(f"      {total:>6,} species across {len(group)} families -- {fams}{more}")
            print(f"          python3 scripts/importColChecklist.py {archive} --apply")
        else:
            print(f"      {total:>6,} species across {len(group)} families -- "
                  f"{fams}{more}   [no archive recorded -- pre-dates the "
                  f"archive-tracking fix; re-run whichever source offered these]")


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
    p.add_argument("--archive", default="",
                   help="path this family was offered from, so report "
                        "--scaffoldable can print the exact re-import command")
    p = sub.add_parser("report", help="what is pending, and what is now doable")
    p.add_argument("--scaffoldable", action="store_true",
                   help="only rows whose family is now in the taxonomy")
    p.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()
    {"seed": cmd_seed, "add": cmd_add, "report": cmd_report}[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
