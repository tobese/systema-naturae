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
     carry no `resolvedAt` yet.
  4. Group those rows by their recorded `archive` path.
  5. For each archive, skip it if a lock file shows another watcher process
     is still mid-run against it (see `archive_locked()`); otherwise take
     the lock and run `importColChecklist.py <archive> --apply`.
     Re-running is safe: already-held species are skipped by the importer's
     dedup, so only newly-placeable species get added.
  6. Stamp `resolvedAt` on the rows that run covered -- that archive's rows
     for those families only. A row is re-imported once after its family
     is ready, then never again: a re-run of the same archive cannot place
     more species into a family it has already been run against. A row
     whose re-import fails stays unstamped and is retried next cycle; a
     refusal recorded later is a new row and gets its own run.

Until 2026-10-30 this was a 1-hour cooldown on `reimportedAt`, refreshed on
every run. A sweep took about an hour, so every sweep re-ran the same 23
archives (the GBIF Backbone, UNITE, COL XR, WoRMS ...), each adding 0
species, and the queue was not drained while it did. `reimportedAt` was
also stamped by family name across every archive, so a row could look
re-imported when only another archive had been run. Rows stamped that way
carry no `resolvedAt` and get one honest run each.

The lock is separate and still needed: it stops two processes writing the
same family files at once.

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
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
import pendingFamilies as PF  # noqa: E402

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


def _row_key(row: dict) -> tuple[str, str]:
    return (row.get("archive") or "", (row.get("family") or "").strip().lower())


def ready_rows(rows: list[dict]) -> list[dict]:
    """Rows whose family is now in the taxonomy, has a data file, and that
    have not yet been re-imported against it (no `resolvedAt`)."""
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
        if r.get("resolvedAt"):
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


def mark_resolved(rows: list[dict], store_path: str) -> None:
    """Stamp resolvedAt (and reimportedAt, kept for the record) on the
    store rows matching `rows` by (archive, family), then rewrite the store
    atomically. Matching the archive too matters: the same family is often
    pending from several archives, and only this one was run."""
    now = now_iso()
    targets = {_row_key(r) for r in rows}
    all_rows = PF.read_store()
    changed = 0
    for r in all_rows:
        if _row_key(r) in targets:
            r["reimportedAt"] = now
            r["resolvedAt"] = now
            changed += 1
    if changed:
        PF.write_store(all_rows)
        print(f"    marked {changed} row(s) resolvedAt={now}", flush=True)


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
                mark_resolved(group, PF.STORE)
                any_ok = True
        finally:
            release_lock(archive)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loop", action="store_true",
                    help="keep polling every CYCLE_SECONDS seconds")
    args = ap.parse_args()

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
