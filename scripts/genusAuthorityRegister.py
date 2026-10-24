#!/usr/bin/env python3
"""Aggregate every genus-level nomenclatural register we hold into one place.

Grew out of the 2026-10-24 cross-kingdom-homonym triage: `verifyTree.py`'s
`check_duplicate_species` can tell you a species id exists under two kingdoms
and nothing more, leaving "is this a real homonym or a misattributed
duplicate?" to a human checking one external source by hand each time. IRMNG
alone settled most of a 36-genus sample that day; adding Nomenclator
Zoologicus settled several more IRMNG had marked uncertain, and caught one
(`Tubifera`) that IRMNG itself flags inconsistently (valid historical
publication, but "unavailable name" today) -- a signal no single source
gives you alone.

This script builds `portal/data/.genus-authority-register.sqlite3`, one row
per (genus, source, row) rather than deduplicated, because a genus can have
multiple historical entries from one source that themselves disagree
(`Monomastix`: Diesing 1848, Roux 1899, and Scherffel 1912 explicitly marked
"[non Diesing 1848]" -- a documented junior-homonym ruling, which collapsing
to one row per genus would have erased). Derived and gitignored, like
`species.parquet` and `.authority-index.sqlite3` -- never the source of
truth, rebuilt from the archives on disk whenever one of them is newer than
the register's recorded source mtimes.

Sources (all on ChecklistBank, all already assessed-and-declined as SPECIES
sources in sourcesManifest.py for being nomenclatural rather than
occurrence data -- that rejection doesn't apply here, this is a different
job):
  - IRMNG (dataset 2007): 269,528 genera, all six kingdoms, CC BY.
  - Nomenclator Zoologicus (dataset 126539): 340k+ zoological (ICZN) genus
    name instances back to 1758, CC0.
  - Species Fungorum Plus (dataset 2073): ~490k fungal (ICN) names.
  - ZooBank (dataset 2037): 527,127 ICZN name usages, CC0. Declined as an
    import source because its data model has no accepted/synonym concept
    at all (sourcesManifest.py, re-assessed twice) -- irrelevant here,
    since this register only asks "does this genus exist, under what
    kingdom/family", not "is this a new species". Added 2026-10-24.
  - Australian Faunal Directory (dataset 127379): zoological-only
    nomenclatural register, CC BY. Declined as an import source for
    lacking a taxon table/family data at all -- same "nomenclatural
    register, not a classification" shape as Nomenclator Zoologicus,
    which this register already uses the same way. Added 2026-10-24.

Usage:
    python3 scripts/genusAuthorityRegister.py --build      # force a rebuild
    python3 scripts/genusAuthorityRegister.py --stats
    python3 scripts/genusAuthorityRegister.py --lookup Sophia
"""
import argparse
import csv
import io
import os
import sqlite3
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER_PATH = os.path.join(ROOT, "portal", "data", ".genus-authority-register.sqlite3")
ARCHIVES = os.path.join("/Volumes/MacieExternal/sources/archives")

SOURCES = {
    "irmng": os.path.join(ARCHIVES, "checklistbank-2007", "archive.zip"),
    "nomenclator-zoologicus": os.path.join(ARCHIVES, "checklistbank-126539", "archive.zip"),
    "species-fungorum-plus": os.path.join(ARCHIVES, "checklistbank-2073", "archive.zip"),
    "zoobank": os.path.join(ARCHIVES, "checklistbank-2037", "archive.zip"),
    "afd": os.path.join(ARCHIVES, "checklistbank-127379", "archive.zip"),
}


def _norm(genus: str) -> str:
    return (genus or "").strip().lower()


def _read_tsv_from_zip(archive_path, member_suffix):
    with zipfile.ZipFile(archive_path) as zf:
        name = next(n for n in zf.namelist() if n.endswith(member_suffix))
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8")
            yield from csv.DictReader(text, delimiter="\t")


def _rows_irmng(archive_path):
    for row in _read_tsv_from_zip(archive_path, "taxon.txt"):
        if row.get("taxonRank") != "Genus":
            continue
        genus = row.get("genus") or row.get("scientificName")
        if not genus:
            continue
        yield {
            "genus": genus, "genus_norm": _norm(genus),
            "kingdom": row.get("kingdom") or None,
            "code": row.get("nomenclaturalCode") or None,
            "family": row.get("family") or None,
            "status": row.get("taxonomicStatus") or None,
            "author": row.get("scientificNameAuthorship") or None,
            "year": row.get("namePublishedInYear") or None,
            "remarks": row.get("taxonRemarks") or None,
        }


def _rows_nomenclator_zoologicus(archive_path):
    for row in _read_tsv_from_zip(archive_path, "names.tsv"):
        if row.get("rank") != "genus":
            continue
        genus = row.get("uninomial") or row.get("scientificName")
        if not genus:
            continue
        yield {
            "genus": genus, "genus_norm": _norm(genus),
            "kingdom": "Animalia",   # the whole dataset is ICZN
            "code": row.get("code") or "ICZN",
            "family": None,         # not carried in this export
            "status": None,
            "author": row.get("authorship") or None,
            "year": row.get("publishedInYear") or None,
            "remarks": row.get("remarks") or None,
        }


def _rows_species_fungorum_plus(archive_path):
    # This export carries no bare genus-rank taxa (every Taxon.tsv row has a
    # species filled in) and Name.tsv's `rank` column is species/infra-
    # specific only ("sp.", "var.", ...) -- no "genus" value exists in it.
    # So a genus's presence here is derived by grouping the species rows
    # it sits under, rather than read off one dedicated row the way IRMNG
    # and Nomenclator Zoologicus provide it.
    seen = {}   # (genus_norm, kingdom, family) -> count
    for row in _read_tsv_from_zip(archive_path, "Taxon.tsv"):
        genus = row.get("genus")
        if not genus:
            continue
        key = (genus, row.get("kingdom") or "Fungi", row.get("family") or None)
        seen[key] = seen.get(key, 0) + 1
    for (genus, kingdom, family), n in seen.items():
        yield {
            "genus": genus, "genus_norm": _norm(genus),
            "kingdom": kingdom,
            "code": "ICN",
            "family": family,
            "status": None,
            "author": None,
            "year": None,
            "remarks": f"{n} species under this genus in Species Fungorum Plus",
        }


def _rows_zoobank(archive_path):
    # Standard DwCA taxon table, same shape as IRMNG's -- confirmed
    # 2026-10-24 the taxon.txt export genuinely carries genus/family/
    # kingdom columns despite sourcesManifest.py declining it as an
    # IMPORT source (ZooBank's data model has no accepted/synonym
    # concept at all, so it can't tell a new species from a synonym --
    # a different question from "does this genus exist, and under what
    # kingdom/family", which is all this register ever asks).
    for row in _read_tsv_from_zip(archive_path, "taxon.txt"):
        if (row.get("taxonRank") or "").lower() != "genus":
            continue
        genus = row.get("genus") or row.get("scientificName")
        if not genus:
            continue
        yield {
            "genus": genus, "genus_norm": _norm(genus),
            "kingdom": row.get("kingdom") or None,
            "code": row.get("nomenclaturalCode") or None,
            "family": row.get("family") or None,
            "status": row.get("taxonomicStatus") or None,
            "author": row.get("scientificNameAuthorship") or None,
            "year": row.get("namePublishedInYear") or None,
            "remarks": row.get("taxonRemarks") or None,
        }


def _rows_afd(archive_path):
    # name.tsv is the same nomenclatural-register shape as Nomenclator
    # Zoologicus's names.tsv (uninomial/scientificName, ICZN code,
    # authorship, publishedInYear) -- declined as an import source for
    # exactly that reason (sourcesManifest.py: "no taxon.* table at all,
    # no parent/accepted links, no family"), which is also why `family`
    # is always None here. Australian Faunal Directory is zoological
    # only, like Nomenclator Zoologicus, so kingdom is hardcoded.
    for row in _read_tsv_from_zip(archive_path, "name.tsv"):
        if (row.get("rank") or "").lower() != "genus":
            continue
        genus = row.get("uninomial") or row.get("scientificName")
        if not genus:
            continue
        yield {
            "genus": genus, "genus_norm": _norm(genus),
            "kingdom": "Animalia",
            "code": row.get("code") or "ICZN",
            "family": None,
            "status": row.get("status") or None,
            "author": row.get("authorship") or None,
            "year": row.get("publishedInYear") or None,
            "remarks": row.get("remarks") or None,
        }


READERS = {
    "irmng": _rows_irmng,
    "nomenclator-zoologicus": _rows_nomenclator_zoologicus,
    "species-fungorum-plus": _rows_species_fungorum_plus,
    "zoobank": _rows_zoobank,
    "afd": _rows_afd,
}


def _source_mtimes():
    return {name: os.path.getmtime(path) for name, path in SOURCES.items()
            if os.path.exists(path)}


def build(path: str = REGISTER_PATH) -> int:
    tmp = f"{path}.{os.getpid()}.tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(tmp)
    con.execute("""
        CREATE TABLE genus_authority (
            genus TEXT, genus_norm TEXT, source TEXT, kingdom TEXT,
            code TEXT, family TEXT, status TEXT, author TEXT, year TEXT,
            remarks TEXT
        )
    """)
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    total = 0
    for source, path_ in SOURCES.items():
        if not os.path.exists(path_):
            print(f"  ({source}: archive not on disk, skipping)")
            continue
        reader = READERS[source]
        rows = []
        for r in reader(path_):
            rows.append((r["genus"], r["genus_norm"], source, r["kingdom"],
                         r["code"], r["family"], r["status"], r["author"],
                         r["year"], r["remarks"]))
        con.executemany(
            "INSERT INTO genus_authority VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        print(f"  {source}: {len(rows):,} genus-rank rows")
        total += len(rows)
    con.execute("CREATE INDEX idx_genus ON genus_authority (genus_norm)")
    for name, mtime in _source_mtimes().items():
        con.execute("INSERT INTO meta VALUES (?, ?)", (f"mtime:{name}", str(mtime)))
    con.commit()
    con.close()
    os.replace(tmp, path)
    return total


def ensure_fresh(path: str = REGISTER_PATH) -> str:
    stale = True
    if os.path.exists(path):
        try:
            con = sqlite3.connect(path)
            recorded = dict(con.execute(
                "SELECT key, value FROM meta WHERE key LIKE 'mtime:%'").fetchall())
            con.close()
            current = _source_mtimes()
            stale = any(
                recorded.get(f"mtime:{name}") != str(mtime)
                for name, mtime in current.items())
        except sqlite3.Error:
            stale = True
    if stale:
        build(path)
    return path


def verdict(genus: str, path: str = REGISTER_PATH) -> dict:
    """What every held register says about `genus`, grouped by source.

    Doesn't make the call for you -- a genus with conflicting historical
    entries (see Monomastix in the module docstring) needs a human reading
    `remarks`, not a boolean. Returns {source: [rows]} for every source that
    has ANY entry for this genus, so an empty dict for a source means "this
    register has never heard of this name," which is itself informative.
    """
    ensure_fresh(path)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM genus_authority WHERE genus_norm = ?",
        (_norm(genus),)).fetchall()
    con.close()
    out = {}
    for r in rows:
        out.setdefault(r["source"], []).append(dict(r))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="force a rebuild")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--lookup", default="", help="print every register's verdict for this genus")
    args = ap.parse_args()

    if args.lookup:
        v = verdict(args.lookup)
        if not v:
            print(f"{args.lookup}: not found in any held register")
        for source, rows in v.items():
            print(f"{source}:")
            for r in rows:
                print(f"  kingdom={r['kingdom']!r} code={r['code']!r} "
                      f"family={r['family']!r} status={r['status']!r} "
                      f"author={r['author']!r} year={r['year']!r} "
                      f"remarks={r['remarks']!r}")
        return 0

    if args.build:
        n = build()
        print(f"wrote {REGISTER_PATH}: {n:,} rows")
        return 0

    path = ensure_fresh()
    if args.stats or True:
        con = sqlite3.connect(path)
        total = con.execute("SELECT COUNT(*) FROM genus_authority").fetchone()[0]
        by_source = con.execute(
            "SELECT source, COUNT(*) FROM genus_authority GROUP BY source").fetchall()
        con.close()
        print(f"{REGISTER_PATH}: {total:,} rows")
        for source, n in by_source:
            print(f"  {source}: {n:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
