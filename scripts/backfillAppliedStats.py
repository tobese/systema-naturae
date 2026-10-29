#!/usr/bin/env python3
"""Fill in `applied` stats on source-queue rows that were applied without them.

Two writers left `applied` sources with no usable numbers:

- the import-ordinator before 2026-10-29 never read its scripts' output,
  so it stamped every applied source `added/merged/families = 0`;
- importQueueDriver.set_stage() writes the stats at the row's top level
  (`added`, `merged`, ...) instead of under `applied`, which is where
  sourceQueue.py's report and the dashboards read them.

importTransformed.py appends the real counts to data/import-log.jsonl on
every apply, keyed by `slugHint`, so that log is the source of truth here.
A row is only touched when it is `applied` and either has no `applied`
block or an all-zero one -- and an all-zero row is only changed when the
log shows a non-zero apply for it, since "nothing to do" is a real zero.

Dry run by default; --apply writes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import sourceQueue as SQ  # noqa: E402

LOG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "import-log.jsonl")
FIELDS = ("added", "merged", "crossFamily", "families")


def latest_log_rows() -> dict:
    """slugHint -> the last import-log row for it (the latest apply)."""
    rows = {}
    with open(LOG_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = row.get("slugHint") or ""
            if key.isdigit():
                key = f"checklistbank-{key}"
            if key:
                rows[key] = row
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    log = latest_log_rows()
    changed = 0
    for key, entry in SQ.read_store().items():
        if entry.get("stage") != "applied":
            continue
        applied = entry.get("applied")
        if applied and any(applied.get(f) for f in FIELDS):
            continue  # already has real numbers

        new = None
        why = ""
        top = {f: entry[f] for f in FIELDS if isinstance(entry.get(f), int)}
        if not applied and top:
            new, why = top, "row's own top-level stats"
        row = log.get(key)
        # A log row older than the recorded apply belongs to an earlier
        # run (55434: logged 10-18, re-applied 10-22 by a path that did
        # not log) -- its numbers would describe the wrong apply.
        applied_at = (applied or {}).get("at") or ""
        if row and applied_at and (row.get("at") or "")[:10] < applied_at[:10]:
            row = None
        if row and any(row.get(f) for f in ("added", "families")):
            new = {"added": row.get("added", 0), "merged": row.get("merged", row.get("deduped", 0)),
                   "families": row.get("families", 0)}
            if "crossFamily" in row:
                new["crossFamily"] = row["crossFamily"]
            elif "crossFamily" in top:
                # import-log doesn't record it; the driver's own stats do
                new["crossFamily"] = top["crossFamily"]
            why = f"import-log row at {row.get('at')}"
        if new is None:
            continue

        new.setdefault("crossFamily", 0)
        new["at"] = (applied or {}).get("at") or (row or {}).get("at", "")
        print(f"  {key}: {applied or 'no applied block'} -> {new}  ({why})")
        changed += 1
        if args.apply:
            entry["applied"] = new
            SQ.write_entry(key, entry)

    print(f"\n{changed} applied row(s) {'updated' if args.apply else 'would be updated (dry run -- pass --apply)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
