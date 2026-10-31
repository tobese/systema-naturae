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
never the source of truth, and `ensure_fresh` brings it up to date before the
first lookup in a process, so an import run never consults a stale picture.

Refreshing is per file (2026-10-31). The index records each family file's
mtime; `ensure_fresh` stats them all and re-reads only the ones that changed.
It used to rebuild the whole 2 GB index whenever *any* family file was newer,
and in the queue pipeline every apply writes family files, so the next
source's transform paid a full rebuild -- about 4.5 of every source's ~5.5
minutes, for a 59-taxon archive as much as for a large one.

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
from tree import ROOT, iter_family_files, iter_species  # noqa: E402
from dedupeSpeciesAcrossFamilies import _same_taxon  # noqa: E402

INDEX_PATH = os.path.join(ROOT, "portal", "data", ".authority-index.sqlite3")
# 3: rows carry an integer file_id into `files`, which holds each family
# file's path and mtime. (2 stored the path on every row; see build().)
SCHEMA_VERSION = "3"


def _read(fam):
    """(mtime, rows) for one family file; rows are (kingdom, authority, key,
    name, family_slug, node_id). The mtime is taken *before* the read, so a
    write landing mid-read leaves the file looking changed to the next
    refresh rather than looking current with stale rows."""
    mtime = os.path.getmtime(fam.path)
    rows = []
    for sp in iter_species(fam.load()):
        for auth, key in (sp.get("sourceIds") or {}).items():
            if key:
                rows.append((fam.kingdom, auth, str(key), sp.get("name"),
                             fam.slug, sp.get("id")))
    return mtime, rows


def _insert(con, file_id, rows):
    con.executemany(
        "INSERT INTO authority_keys VALUES (?, ?, ?, ?, ?, ?, ?)",
        [r + (file_id,) for r in rows])


def build(path: str = INDEX_PATH) -> int:
    """(Re)write the whole index from the family files on disk. Returns row
    count. `ensure_fresh` only calls this when there is no usable index;
    otherwise it refreshes the changed files in place.

    `tmp` is per-process (pid in the name): two importers run at once --
    which happened, an eunis/LCVP/Nortaxa/Brazil batch all mid-import at
    once -- both see the index as stale and both rebuild, and a shared tmp
    name means the second one's `os.remove` or `os.replace` can land on the
    first one's in-progress file. `sqlite3.OperationalError: attempt to
    write a readonly database` was that collision, not a permissions bug.
    """
    tmp = f"{path}.{os.getpid()}.tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(tmp)
    # Rows point at their file by integer id, not by path: a 100-byte path
    # on each of ~12.5M rows, plus an index over it, took the file from
    # 2.0 to 5.3 GB (schema 2, live for an hour on 2026-10-31 with the
    # data volume at 99%).
    con.execute("""
        CREATE TABLE authority_keys (
            kingdom TEXT, authority TEXT, key TEXT,
            name TEXT, family_slug TEXT, node_id TEXT, file_id INTEGER
        )
    """)
    con.execute("CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT UNIQUE, mtime REAL)")
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    n = 0
    for fam in iter_family_files():
        mtime, rows = _read(fam)
        file_id = con.execute("INSERT INTO files (path, mtime) VALUES (?, ?)",
                              (fam.path, mtime)).lastrowid
        _insert(con, file_id, rows)
        n += len(rows)
    con.execute("CREATE INDEX idx_lookup ON authority_keys (kingdom, authority, key)")
    con.execute("CREATE INDEX idx_file ON authority_keys (file_id)")
    con.execute("INSERT INTO meta VALUES ('schema', ?)", (SCHEMA_VERSION,))
    con.commit()
    con.close()
    os.replace(tmp, path)
    return n


def refresh(path: str = INDEX_PATH) -> tuple:
    """Re-read the family files whose mtime differs from the one recorded,
    and drop the rows of files that no longer exist. Returns
    (changed, removed) file counts.

    One write transaction, so a concurrent reader sees the index before or
    after, never half-way; a second refresher racing this one waits on the
    lock and then finds nothing left to do.
    """
    current = {}
    for fam in iter_family_files():
        try:
            current[fam.path] = (fam, os.path.getmtime(fam.path))
        except OSError:
            continue
    con = sqlite3.connect(path, timeout=600)
    try:
        con.execute("BEGIN IMMEDIATE")
        stored = {p: (i, m) for i, p, m in con.execute("SELECT id, path, mtime FROM files")}
        changed = [fam for p, (fam, m) in current.items()
                   if p not in stored or stored[p][1] != m]
        removed = [p for p in stored if p not in current]
        for p in removed:
            con.execute("DELETE FROM authority_keys WHERE file_id = ?", (stored[p][0],))
            con.execute("DELETE FROM files WHERE id = ?", (stored[p][0],))
        for fam in changed:
            try:
                mtime, rows = _read(fam)
            except (OSError, ValueError) as e:
                # Mid-write or vanished: leave its old rows and old mtime,
                # so the next refresh tries it again.
                print(f"  authorityIndex: skipped {fam.path}: {e}")
                continue
            if fam.path in stored:
                # Write only the difference. An apply adds a few species to a
                # family like Carabidae (200k rows); deleting and re-inserting
                # all of them touched every page of idx_lookup and took 20
                # minutes for one busy cycle of applies.
                file_id = stored[fam.path][0]
                have = {}
                for rowid, *r in con.execute(
                        "SELECT rowid, kingdom, authority, key, name, family_slug, "
                        "node_id FROM authority_keys WHERE file_id = ?", (file_id,)):
                    have.setdefault(tuple(r), []).append(rowid)
                want = {}
                for r in rows:
                    want[r] = want.get(r, 0) + 1
                gone, new = [], []
                for r, rowids in have.items():
                    extra = len(rowids) - want.get(r, 0)
                    gone.extend(rowids[:max(0, extra)])
                for r, n in want.items():
                    new.extend([r] * max(0, n - len(have.get(r, ()))))
                con.executemany("DELETE FROM authority_keys WHERE rowid = ?",
                                [(i,) for i in gone])
                con.execute("UPDATE files SET mtime = ? WHERE id = ?", (mtime, file_id))
                _insert(con, file_id, new)
            else:
                file_id = con.execute("INSERT INTO files (path, mtime) VALUES (?, ?)",
                                      (fam.path, mtime)).lastrowid
                _insert(con, file_id, rows)
        con.commit()
    finally:
        con.close()
    return len(changed), len(removed)


_conn_cache = {}
_checked_fresh = set()


def ensure_fresh(path: str = INDEX_PATH) -> str:
    """Build the index if there is none in the current schema, otherwise
    refresh only the family files that changed. Cheap when nothing changed:
    a stat per family file, no JSON parse -- but still too much to pay per
    lookup, so `_conn` only calls this once per process per path."""
    usable = False
    if os.path.exists(path):
        try:
            con = sqlite3.connect(path)
            row = con.execute(
                "SELECT value FROM meta WHERE key = 'schema'").fetchone()
            con.close()
            usable = bool(row) and row[0] == SCHEMA_VERSION
        except sqlite3.Error:
            usable = False
    if usable:
        refresh(path)
    else:
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
