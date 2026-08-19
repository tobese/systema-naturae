#!/usr/bin/env python3
"""
One-off repair for /Volumes/WikiDump/wiki-pages.sqlite: re-derives `extract`
for every row where it was corrupted by the (now-fixed) bugs in
buildWikipediaDb.py's strip_wikitext()/extract_lead() — raw {{...}} infobox
fragments left behind by a naive non-nesting-brace regex, [[Category:...]]
links rendered as visible text, and #REDIRECT pages stored verbatim instead
of resolved. Every row's raw wikitext is still in the `content` column, so
this re-derives from that rather than requiring a full dump re-parse.

Usage: python3 scripts/repairWikipediaExtracts.py [--db PATH] [--dry-run]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import buildWikipediaDb as w

DEFAULT_DB = "/Volumes/WikiDump/wiki-pages.sqlite"
CORRUPTION_MARKERS = ("{{", "Category:")


def is_corrupted(extract: str | None) -> bool:
    if not extract:
        return False
    if extract.lower().startswith("#redirect"):
        return True
    return any(m in extract for m in CORRUPTION_MARKERS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--dry-run", action="store_true", help="report counts without writing")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=WAL")

    all_rows = conn.execute("SELECT title, content, extract FROM pages").fetchall()
    corrupted = [(title, content, extract) for title, content, extract in all_rows if is_corrupted(extract)]
    print(f"Total rows: {len(all_rows)}")
    print(f"Corrupted extracts: {len(corrupted)}")

    if args.dry_run:
        fixed_preview = 0
        for title, content, _ in corrupted[:2000]:
            if w.extract_lead(content):
                fixed_preview += 1
        rate = fixed_preview / min(2000, len(corrupted)) if corrupted else 0
        print(f"Dry run: sample of {min(2000, len(corrupted))} rows -> ~{rate:.0%} recover a clean extract.")
        return 0

    updates = []
    now_empty = 0
    for title, content, _ in corrupted:
        new_extract = w.extract_lead(content)
        updates.append((new_extract, title))
        if new_extract is None:
            now_empty += 1

    conn.executemany("UPDATE pages SET extract = ? WHERE title = ?", updates)
    conn.commit()
    print(f"Re-derived {len(updates)} extracts ({len(updates) - now_empty} recovered clean text, "
          f"{now_empty} correctly emptied — redirects/stubs with no real prose).")

    resolved = w.resolve_redirects(conn)
    print(f"Resolved {resolved} redirect pages to their target's extract.")

    remaining = conn.execute(
        "SELECT COUNT(*) FROM pages WHERE extract LIKE '%{{%' OR extract LIKE '%Category:%' OR extract LIKE '#REDIRECT%'"
    ).fetchone()[0]
    print(f"Remaining corrupted rows: {remaining}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
