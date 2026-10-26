#!/usr/bin/env python3
"""Pending-family watcher: re-runs sources after families are created.

Closes the loop that `scripts/pendingFamilies.py report --scaffoldable`
opens: it prints which refused families are now in the taxonomy (and have a
data file on disk), grouped by archive with the exact re-import command --
but nothing actually runs those commands. This watcher does.

Every cycle:

  1. Read the pending-family store (families.jsonl on the sources volume).
  2. Compute which family names the taxonomy now holds, and which have a
     data file on disk (the same index importColChecklist.py builds).
  3. Find rows whose family is now "ready" (held + file exists) and that
     have not been re-imported within the cooldown window.
  4. Group those rows by their recorded `archive` path.
  5. For each archive, skip it if a lock file shows another watcher process
     is still mid-run against it (see `archive_locked()`); otherwise take
     the lock and run `importColChecklist.py <archive> --apply`.
     Re-running is safe: already-held species are skipped by the importer's
     dedup, so only newly-placeable species get added.
  6. Mark every row from that archive with a fresh `reimportedAt` so we
     don't re-scan the same archive every cycle when nothing new could
     plausibly be ready yet -- refreshed on every successful run, not just
     the first, so the throttle actually repeats (a bug until 2026-10-25:
     the guard only ever set this once per row, so after the first
     COOLDOWN_HOURS window every archive got re-scanned every single cycle,
     forever).

The lock and the cooldown solve two different problems and neither should
be dropped in favour of the other: the lock stops two processes writing the
same family files at once (a correctness hazard); the cooldown just avoids
paying the cost of a full re-scan when it's very unlikely to find anything
(an efficiency tweak). Before 2026-10-25 a single 24-hour cooldown tried to
do both jobs and did neither well -- 24h is a long time to wait to pick up
a newly-scaffolded family, and it was never the right tool for "is the
previous run still active" in the first place.

Usage:
    python3 scripts/pendingFamilyWatcher.py           # one cycle, then exit
    python3 scripts/pendingFamilyWatcher.py --loop    # keep polling
    nohup caffeinate -dimsu python3 scripts/pendingFamilyWatcher.py --loop \
        > /tmp/pendingFamilyWatcher.log 2>&1 &
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
import pendingFamilies as PF  # noqa: E402

COOLDOWN_HOURS = 1
CYCLE_SECONDS = 300

LOCK_DIR = os.path.join(os.path.dirname(PF.STORE), "watcher-locks")


def _lock_path(archive: str) -> str:
    # Archive paths are absolute and contain "/" -- flatten to a safe filename.
    return os.path.join(LOCK_DIR, re.sub(r"[^A-Za-z0-9]+", "_", archive) + ".lock")


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not ours to signal
    return True


def archive_locked(archive: str) -> bool:
    """True if another watcher process is still mid-run against this exact
    archive. This is the real guard the cooldown used to stand in for: a
    cycle fires every 60s (orchestrator) / 5min (--loop), but a run against
    something the size of the GBIF Backbone takes well over that (measured
    2026-10-25: 15+ minutes), so without this a second cycle would start a
    second `importColChecklist.py` against the same archive while the first
    is still writing the same family files -- the exact "no concurrent
    writers" hazard CLAUDE.md warns about. A stale lock (process no longer
    alive -- e.g. the prior run crashed) is not honored."""
    path = _lock_path(archive)
    try:
        with open(path, encoding="utf-8") as fh:
            pid = int(fh.read().strip())
    except (OSError, ValueError):
        return False
    return _pid_alive(pid)


def acquire_lock(archive: str) -> None:
    os.makedirs(LOCK_DIR, exist_ok=True)
    with open(_lock_path(archive), "w", encoding="utf-8") as fh:
        fh.write(str(os.getpid()))


def release_lock(archive: str) -> None:
    try:
        os.remove(_lock_path(archive))
    except OSError:
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def recently_reimported(row: dict) -> bool:
    """True if this row was re-imported within the cooldown window."""
    ts = row.get("reimportedAt")
    if not ts:
        return False
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - dt < timedelta(hours=COOLDOWN_HOURS)


def ready_rows(rows: list[dict]) -> list[dict]:
    """Rows whose family is now in the taxonomy, has a data file, and is
    outside the re-import cooldown."""
    held = PF.held_family_slugs()
    files = PF.family_data_files()
    out = []
    for r in rows:
        fam = (r.get("family") or "").strip().lower()
        if not fam or fam not in held:
            continue
        slug = held[fam]
        hits = files.get(slug.lower(), [])
        if len(hits) > 1:
            # Same family name validly placed at two different taxonomic
            # placements (Microsporidia under both Fungi and Protozoa,
            # testate amoebae under both Protozoa and Chromista, etc.)
            # rather than a genuinely missing file -- narrow to this row's
            # own kingdom before giving up on it. Same fix as
            # pendingFamilies.py's report and importColChecklist.py's
            # importer; this was the third, still-silent copy.
            kingdom = (r.get("kingdom") or "").lower()
            kingdom_hits = [h for h in hits
                            if h.split("taxonomy/")[-1].split("/")[0] == kingdom]
            if len(kingdom_hits) == 1:
                hits = kingdom_hits
        if len(hits) != 1:
            continue  # registered but no data file yet -- scaffold first
        if recently_reimported(r):
            continue
        out.append(r)
    return out


def group_by_archive(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r.get("archive") or ""].append(r)
    return dict(groups)


def run_reimport(archive: str, rows: list[dict]) -> bool:
    """Run importColChecklist.py --apply for one archive. Returns True on
    success."""
    total = sum(int(r.get("species") or 0) for r in rows)
    fams = ", ".join(sorted({r.get("family") for r in rows})[:5])
    more = f" (+{len(rows) - 5} more)" if len(rows) > 5 else ""
    print(f"\n== Re-importing {archive}", flush=True)
    print(f"    {len(rows)} family(s), ~{total:,} pending species: {fams}{more}",
          flush=True)
    cmd = ["python3", os.path.join(SCRIPT_DIR, "importColChecklist.py"),
           archive, "--apply"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.splitlines():
            if line.strip():
                print(f"    {line}", flush=True)
    if result.returncode != 0 and result.stderr:
        for line in result.stderr.splitlines():
            if line.strip():
                print(f"    ! {line}", flush=True)
    if result.returncode == 0:
        print(f"    {archive}: re-import OK", flush=True)
    else:
        print(f"    {archive}: re-import FAILED (rc={result.returncode})",
              flush=True)
    return result.returncode == 0


def mark_reimported(rows: list[dict], store_path: str) -> None:
    """Set reimportedAt on every row whose family matches one of `rows`,
    then rewrite the store atomically. Always overwrites -- not just the
    first time -- so the cooldown actually repeats; a row that keeps
    getting re-imported cycle after cycle (e.g. one that's genuinely
    popular) still gets the throttle applied each time, not just once."""
    now = now_iso()
    targets = {(r.get("family") or "").strip().lower() for r in rows}
    all_rows = PF.read_store()
    changed = 0
    for r in all_rows:
        if (r.get("family") or "").strip().lower() in targets:
            r["reimportedAt"] = now
            changed += 1
    if changed:
        PF.write_store(all_rows)
        print(f"    marked {changed} row(s) reimportedAt={now}", flush=True)


def cycle() -> int:
    rows = PF.read_store()
    if not rows:
        print("  pending store is empty", flush=True)
        return 0

    ready = ready_rows(rows)
    if not ready:
        print("  no ready pending families this cycle", flush=True)
        return 0

    groups = group_by_archive(ready)
    any_ok = False
    for archive, group in groups.items():
        if not archive:
            print(f"  {len(group)} ready family(ies) have no archive recorded, "
                  f"skipping (pre-dates archive-tracking fix)", flush=True)
            continue
        if archive_locked(archive):
            print(f"  {archive}: another run is still in progress, skipping "
                  f"this cycle", flush=True)
            continue
        acquire_lock(archive)
        try:
            if run_reimport(archive, group):
                mark_reimported(group, PF.STORE)
                any_ok = True
        finally:
            release_lock(archive)
    return 0


def main() -> int:
    global COOLDOWN_HOURS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loop", action="store_true",
                    help="keep polling every CYCLE_SECONDS seconds")
    ap.add_argument("--cooldown-hours", type=int, default=COOLDOWN_HOURS,
                    help="hours to wait before re-importing the same archive")
    args = ap.parse_args()

    COOLDOWN_HOURS = args.cooldown_hours

    if args.loop:
        while True:
            try:
                cycle()
            except Exception as e:  # never die the watcher
                print(f"  cycle error: {e}", flush=True)
            time.sleep(CYCLE_SECONDS)
    return cycle()


if __name__ == "__main__":
    sys.exit(main())
