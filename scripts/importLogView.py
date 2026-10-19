#!/usr/bin/env python3
"""View data/import-log.jsonl -- one row per --apply run of importColChecklist.py.

There used to be an import-log viewer (`buildImportLog.ts`, feeding the
portal's News tab), removed when the News/import-log features were dropped
for cross-kingdom simplification. This is not that: it reads the current,
unrelated `data/import-log.jsonl` (a flat run-stats log, written on --apply
only -- see importColChecklist.py's comment on why) rather than building a
portal feature, and it exists to watch a run of several imports in a row
rather than to show end users anything.

The two problem signals are the same ones verifyTree.py's `check_import()`
gate already checks, reused here rather than reinvented: a refusal rate
above the ceiling (families the source names that we don't hold, or a
kingdom-routing bug -- cf. Wikispecies at 45%) and "staged something, added
nothing" (usually means the held-check is wrong, not that the source is
exhausted).

Usage:
    python3 scripts/importLogView.py                 # last 20 runs
    python3 scripts/importLogView.py --all
    python3 scripts/importLogView.py --watch          # tail -f, live
    python3 scripts/importLogView.py --ceiling 0.10   # stricter refusal gate
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "import-log.jsonl")


def load_rows(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def problems(row: dict, ceiling: float) -> list[str]:
    """The two real gate criteria (verifyTree.py's check_import) -- not
    missedFamilies, which is the normal, handled case (see notes())."""
    issues = []
    rate = row.get("refusalRate") or 0.0
    if rate > ceiling:
        issues.append(f"refusal rate {rate:.1%} > ceiling {ceiling:.0%}")
    if row.get("added") == 0 and row.get("staged", 0) > 0:
        issues.append(f"staged {row.get('staged'):,} but added 0")
    return issues


def notes(row: dict) -> list[str]:
    """Informational, not a gate failure -- missedFamilies lands in the
    pending-family store and is expected on most runs."""
    out = []
    if row.get("missedFamilies"):
        out.append(f"{row['missedFamilies']} families missed (recorded as pending)")
    return out


def display_name(row: dict) -> str:
    """The archive's own title when the writer captured one (importColChecklist.py,
    since the "title" field was added) -- slugHint/source for older rows that
    predate it, since a title can't be reliably reconstructed after the fact
    from a generic slugHint like "archive"."""
    return row.get("title") or row.get("slugHint") or row.get("source") or "?"


def fmt_row(row: dict, ceiling: float) -> str:
    at = (row.get("at") or "")[:19].replace("T", " ")
    slug = display_name(row)
    offered = row.get("offered", 0)
    held = row.get("alreadyHeld", 0)
    staged = row.get("staged", 0)
    added = row.get("added", 0)
    refused = row.get("refused", 0)
    rate = row.get("refusalRate") or 0.0
    kingdoms = ",".join(row.get("kingdoms") or [])
    issues = problems(row, ceiling)
    flag = "  !!" if issues else ""

    line = (f"{at}  {slug:<40.40} offered {offered:>9,}  held {held:>9,}  "
            f"staged {staged:>7,}  added {added:>7,}  refused {refused:>6,} "
            f"({rate:>5.1%})  [{kingdoms}]{flag}")
    for issue in issues:
        line += f"\n{'':>21}  ^ {issue}"
    for note in notes(row):
        line += f"\n{'':>21}  . {note}"
    return line


def summarize(rows: list[dict]) -> str:
    total_added = sum(r.get("added", 0) for r in rows)
    total_offered = sum(r.get("offered", 0) for r in rows)
    total_refused = sum(r.get("refused", 0) for r in rows)
    return (f"{len(rows)} run(s) shown -- {total_added:,} species added, "
            f"{total_offered:,} offered, {total_refused:,} refused total")


def watch(path: str, ceiling: float) -> int:
    print(f"  watching {path} (Ctrl-C to stop)\n")
    seen = len(load_rows(path))
    rows = load_rows(path)
    for row in rows[-5:]:
        print(fmt_row(row, ceiling))
    try:
        while True:
            time.sleep(2)
            rows = load_rows(path)
            if len(rows) > seen:
                for row in rows[seen:]:
                    print(fmt_row(row, ceiling))
                seen = len(rows)
    except KeyboardInterrupt:
        print("\n  stopped")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="show every run, not just the last 20")
    ap.add_argument("--last", type=int, default=20, help="how many recent runs to show (default 20)")
    ap.add_argument("--watch", action="store_true", help="tail -f the log, printing new runs as they land")
    ap.add_argument("--ceiling", type=float, default=0.20, help="refusal-rate ceiling, same default as verifyTree.py (0.20)")
    args = ap.parse_args()

    if args.watch:
        return watch(LOG, args.ceiling)

    rows = load_rows(LOG)
    if not rows:
        print(f"  no runs yet in {LOG}")
        return 0

    shown = rows if args.all else rows[-args.last:]
    for row in shown:
        print(fmt_row(row, args.ceiling))
    print(f"\n  {summarize(shown)}")
    flagged = [r for r in shown if problems(r, args.ceiling)]
    if flagged:
        print(f"  {len(flagged)} run(s) flagged above -- see '!!' markers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
