#!/usr/bin/env python3
"""The unplaced store: species an import offered and we could not place.

pendingFamilies.py remembers *which* families we lack and how many species
wanted each; the unresolved-taxa store remembers family names with five
samples. Neither keeps the species, so scaffolding a family meant re-reading
every archive that had offered it. Decided 2026-11-01 (the user's "virtual
kingdom" idea, kept as a store rather than tree nodes): keep the records.

One row per (kingdom, name, authorship, source) -- the same name offered by
three sources is three rows, each with that source's id and family claim:

  kingdom     where the source (or its family name) put it; "" when the
              kingdom did not resolve either
  family      the family the source gives, as written; "" for none
  reason      family-not-held | kingdom-unresolved
  source      e.g. "checklistbank:1174" (importColChecklist's slug hint)
  sourceId    the taxon id in that source

Not the tree: kingdom-config.json stays at six, verifyTree and the dedupes
never see it, and the portal does not show it (the user, 2026-11-01: "not
visible for now"). Written only on an apply, beside the pending-family
store, never on a dry run. A name we already hold in that kingdom (in some
other family) is not unplaced and is not written.

Lives on the sources volume, like the pending stores: derived from
archives, machine-local (q-bert keeps its own for bacteria/viruses).

    python3 scripts/unplacedStore.py report
    python3 scripts/unplacedStore.py report --kingdom animalia --top 30
"""
import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources as _sources  # noqa: E402

STORE = os.path.join(_sources.ROOT, "unplaced", "unplaced.sqlite3")

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    kingdom    TEXT NOT NULL,
    name       TEXT NOT NULL,
    authorship TEXT NOT NULL,
    source     TEXT NOT NULL,
    sourceId   TEXT,
    family     TEXT NOT NULL,
    genus      TEXT,
    reason     TEXT NOT NULL,
    firstSeen  TEXT NOT NULL,
    lastSeen   TEXT NOT NULL,
    PRIMARY KEY (kingdom, name, authorship, source)
);
CREATE INDEX IF NOT EXISTS offers_family ON offers (kingdom, family);
"""


def connect(path=STORE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path, timeout=300)
    db.executescript(SCHEMA)
    return db


def record(rows, source, path=STORE):
    """rows: (kingdom, family, genus, name, authorship, sourceId, reason).
    A row already there keeps its firstSeen and takes this run's id, family
    and lastSeen. Returns (new, seen again)."""
    now = time.strftime("%Y-%m-%d")
    db = connect(path)
    with db:
        before = db.execute("SELECT count(*) FROM offers WHERE source = ?", (source,)).fetchone()[0]
        db.executemany(
            """INSERT INTO offers (kingdom, name, authorship, source, sourceId, family,
                                   genus, reason, firstSeen, lastSeen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (kingdom, name, authorship, source) DO UPDATE SET
                   sourceId = excluded.sourceId, family = excluded.family,
                   genus = excluded.genus, reason = excluded.reason,
                   lastSeen = excluded.lastSeen""",
            [(k or "", n, a or "", source, sid or "", f or "", g or "", why, now, now)
             for k, f, g, n, a, sid, why in rows])
        after = db.execute("SELECT count(*) FROM offers WHERE source = ?", (source,)).fetchone()[0]
    db.close()
    return after - before, len(rows) - (after - before)


def report(kingdom="", top=20, path=STORE):
    if not os.path.exists(path):
        print(f"  no unplaced store yet ({path})")
        return
    db = connect(path)
    where, args = ("WHERE kingdom = ?", (kingdom,)) if kingdom else ("", ())
    rows, names, sources = db.execute(
        f"SELECT count(*), count(DISTINCT kingdom || '|' || name), count(DISTINCT source) "
        f"FROM offers {where}", args).fetchone()
    print(f"  {rows:,} offers of {names:,} distinct names from {sources:,} sources  ({path})")
    for k, why, n in db.execute(
            f"SELECT kingdom, reason, count(DISTINCT name) FROM offers {where} "
            f"GROUP BY kingdom, reason ORDER BY 3 DESC", args):
        print(f"    {n:>9,}  {k or '(kingdom unresolved)':22s} {why}")
    print(f"\n  families most wanted (distinct names):")
    for k, fam, n, s in db.execute(
            f"SELECT kingdom, family, count(DISTINCT name), count(DISTINCT source) FROM offers "
            f"{where} GROUP BY kingdom, family ORDER BY 3 DESC LIMIT ?", args + (top,)):
        print(f"    {n:>9,}  [{k or '?'}] {fam or '(no family)'}  ({s} sources)")
    db.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("report")
    p.add_argument("--kingdom", default="")
    p.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    if args.cmd == "report":
        report(args.kingdom, args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
