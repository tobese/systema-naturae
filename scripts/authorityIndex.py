#!/usr/bin/env python3
"""(kingdom, authority, key) -> species, for the import-time duplicate gate.

`verifyTree.py`'s `check_authority_collisions` finds the same signal -- two of
our species sharing one GBIF usageKey or ITIS TSN, which is proof of duplication
rather than a name match -- but it finds it after the fact, by walking every
species in every kingdom. `merge_family` needs the answer before it adds one
species, and re-running that walk per import would make the gate itself the
bottleneck: 1,755,600 species in animalia alone.

This is that walk done once and persisted, so a lookup is a keyed SQLite query
instead of a tree traversal. Derived and gitignored, like `species.parquet` --
never the source of truth, and `ensure_fresh` rebuilds it automatically when any
family file on disk is newer than the index, so an import run never consults a
stale picture without also paying to refresh it first (a cheap stat sweep, not a
reparse, since only mtimes are compared).

    python3 scripts/authorityIndex.py --build      # force a rebuild
    python3 scripts/authorityIndex.py --stats

`conflicts_for` is what `merge_family` calls. It reuses `_same_taxon` from
`dedupeSpeciesAcrossFamilies.py` -- the one definition of "same key, same
taxon?" already shared with `verifyTree.py` -- so the gate and the post-hoc
audit cannot disagree with each other. GBIF files a subspecies under its
parent's usageKey, and that is not a duplicate; `_same_taxon` is what keeps the
gate from flagging it.
"""
import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import ROOT, family_data_files, iter_all_species  # noqa: E402
from dedupeSpeciesAcrossFamilies import _same_taxon  # noqa: E402

INDEX_PATH = os.path.join(ROOT, "portal", "data", ".authority-index.sqlite3")


def _newest_family_mtime() -> float:
    """Cheapest possible staleness signal: stat every family file, parse none."""
    newest = 0.0
    for path in family_data_files():
        try:
            newest = max(newest, os.path.getmtime(path))
        except OSError:
            continue
    return newest


def build(path: str = INDEX_PATH) -> int:
    """(Re)write the index from the family files on disk. Returns row count."""
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    source_mtime = _newest_family_mtime()
    con = sqlite3.connect(tmp)
    con.execute("""
        CREATE TABLE authority_keys (
            kingdom TEXT, authority TEXT, key TEXT,
            name TEXT, family_slug TEXT, node_id TEXT
        )
    """)
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    rows = []
    for fam, sp in iter_all_species():
        sid = sp.get("sourceIds") or {}
        for auth, key in sid.items():
            if key:
                rows.append((fam.kingdom, auth, str(key), sp.get("name"),
                             fam.slug, sp.get("id")))
    con.executemany(
        "INSERT INTO authority_keys VALUES (?, ?, ?, ?, ?, ?)", rows)
    con.execute("CREATE INDEX idx_lookup ON authority_keys (kingdom, authority, key)")
    con.execute("INSERT INTO meta VALUES ('source_mtime', ?)", (str(source_mtime),))
    con.commit()
    con.close()
    os.replace(tmp, path)
    return len(rows)


_conn_cache = {}
_checked_fresh = set()


def ensure_fresh(path: str = INDEX_PATH) -> str:
    """Build the index if it is missing, or if any family file is newer than
    it. Cheap when nothing changed: a stat per family file (~14,085 of them,
    a few seconds via glob+stat), no JSON parse -- but still too much to pay
    per lookup, so `_conn` only calls this once per process per path."""
    stale = True
    if os.path.exists(path):
        try:
            con = sqlite3.connect(path)
            row = con.execute(
                "SELECT value FROM meta WHERE key = 'source_mtime'").fetchone()
            con.close()
            if row and float(row[0]) >= _newest_family_mtime():
                stale = False
        except sqlite3.Error:
            stale = True
    if stale:
        build(path)
        _conn_cache.pop(path, None)
    return path


def _conn(path: str = INDEX_PATH):
    if path not in _checked_fresh:
        ensure_fresh(path)
        _checked_fresh.add(path)
    if path not in _conn_cache:
        _conn_cache[path] = sqlite3.connect(path)
    return _conn_cache[path]


def conflicts_for(kingdom: str, family_slug: str, name: str, source_ids: dict,
                   path: str = INDEX_PATH):
    """Other families already holding `name` under one of `source_ids`.

    Returns a list of (authority, key, other_name, other_family_slug,
    other_node_id) tuples, excluding matches inside `family_slug` itself (that
    is `merge_family`'s own within-family dedup, not this gate's job) and
    excluding same-key matches `_same_taxon` says are not the same taxon.
    """
    if not source_ids:
        return []
    con = _conn(path)
    out = []
    for auth, key in source_ids.items():
        if not key:
            continue
        for other_name, other_slug, other_id in con.execute(
                "SELECT name, family_slug, node_id FROM authority_keys "
                "WHERE kingdom = ? AND authority = ? AND key = ?",
                (kingdom, auth, str(key))):
            if other_slug == family_slug:
                continue
            if not _same_taxon(name, other_name):
                continue
            out.append((auth, key, other_name, other_slug, other_id))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="force a rebuild")
    ap.add_argument("--stats", action="store_true", help="report row counts")
    ap.add_argument("--out", default=INDEX_PATH)
    args = ap.parse_args()

    if args.build:
        t0 = time.time()
        n = build(args.out)
        size = os.path.getsize(args.out) / 1e6
        print(f"  {n:,} (authority, key) rows across all kingdoms, "
              f"{size:.1f} MB, {time.time() - t0:.0f}s -> {args.out}")
        return 0

    path = ensure_fresh(args.out)
    con = sqlite3.connect(path)
    n = con.execute("SELECT count(*) FROM authority_keys").fetchone()[0]
    by_auth = con.execute(
        "SELECT authority, count(*) FROM authority_keys "
        "GROUP BY authority ORDER BY 2 DESC").fetchall()
    print(f"  {n:,} rows in {path}")
    for auth, c in by_auth:
        print(f"    {auth:12s} {c:>10,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
