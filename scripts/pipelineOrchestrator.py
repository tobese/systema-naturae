#!/usr/bin/env python3
"""Single entry point for the whole import pipeline -- the one process
that watches the source queue (scripts/sourceQueue.py,
data/source-queue/<key>.json) and the pending-family store, and calls
the right tool for whatever state it finds.

Before this (2026-10-22), the pipeline was two independent, narrow
daemons: importQueueDriver.py only ever watched stage `downloaded`, and
pendingFamilyWatcher.py watched the pending-family store directly,
bypassing the source queue's stage machine entirely. Nothing watched
`needs-rerun` at all -- found when checklistbank-2008 (TAXREF) sat there
with no process that would ever pick it up, needing a human to notice
and run scripts/importColStage2.py by hand.

Both daemons' logic still lives in their own files and is imported here
rather than duplicated -- importQueueDriver.process_downloaded() and
pendingFamilyWatcher.cycle() are unchanged. This script is the
supervisor that calls them, plus the new needs-rerun stage, in one
process with one log.

Each pass:
    1. importQueueDriver.refill_queue() -- top up `downloaded` from
       triageNext.py when it runs low.
    2. importQueueDriver.process_downloaded() -- licence gate, triage,
       apply: downloaded -> triaging -> triaged -> queued -> applying
       -> applied (or blocked).
    3. process_needs_rerun() -- run each needs-rerun source's own
       `rerunCommand` (set via `sourceQueue.py set --stage needs-rerun
       --rerun-command '[...]'`); no stored command is a configuration
       error, not a format this can guess at, so it's left alone with a
       loud note rather than retried blindly.
    4. pendingFamilyWatcher.cycle() -- one sweep of the pending-family
       store for now-ready families.

Usage:
    python3 scripts/pipelineOrchestrator.py              # one pass, then exit
    python3 scripts/pipelineOrchestrator.py --loop        # keep polling
    nohup caffeinate -dimsu python3 scripts/pipelineOrchestrator.py --loop \\
        > /tmp/pipelineOrchestrator.log 2>&1 &

Either stage's own script still runs standalone for one-off debugging
(`python3 scripts/importQueueDriver.py`, `python3
scripts/pendingFamilyWatcher.py`) -- but in production this is the one
to run, not those two separately.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import importQueueDriver as IQD  # noqa: E402
import pendingFamilyWatcher as PFW  # noqa: E402

CYCLE_SECONDS = 60


def process_needs_rerun(q: dict) -> None:
    """Run every `needs-rerun` source's stored `rerunCommand` verbatim.

    A source lands here because the standard transform/apply pipeline
    isn't the right tool for it (TAXREF's 958 unscaffolded families need
    importColStage2.py --kingdom, once per kingdom, not a plain re-run) --
    so there is no generic fallback command to guess at. Missing one is
    left alone with a loud note on every pass rather than silently
    skipped, so it surfaces on the dashboard instead of sitting invisible
    the way needs-rerun itself did before this script existed.
    """
    pending = [(k, v) for k, v in q.items() if v.get("stage") == "needs-rerun"]
    if not pending:
        print("No sources at stage 'needs-rerun'.", flush=True)
        return

    print(f"{len(pending)} source(s) at stage 'needs-rerun'.", flush=True)
    for key, entry in pending:
        cmd = entry.get("rerunCommand")
        if not cmd:
            print(f"  {key}: no rerunCommand stored -- set one with "
                  f"`sourceQueue.py set --key {key} --stage needs-rerun "
                  f"--rerun-command '[...]'`; leaving as-is", flush=True)
            continue
        print(f"\n== {key} (needs-rerun) -- {' '.join(cmd)}", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in (result.stdout or "").splitlines():
            if line.strip():
                print(f"    {line}", flush=True)
        if result.returncode != 0:
            if result.stderr:
                for line in result.stderr.splitlines():
                    if line.strip():
                        print(f"    ! {line}", flush=True)
            print(f"  {key}: rerunCommand FAILED (rc={result.returncode}), "
                  f"leaving at needs-rerun", flush=True)
            continue
        IQD.set_stage(q, key, "applied", rerunAt=datetime.now(timezone.utc).isoformat())
        print(f"  {key}: applied via stored rerunCommand", flush=True)


def main() -> int:
    loop = "--loop" in sys.argv

    q = IQD.load_queue()
    q = IQD.refill_queue(q)
    IQD.process_downloaded(q)

    q = IQD.load_queue()
    process_needs_rerun(q)

    print("\n-- pending-family sweep --", flush=True)
    PFW.cycle()

    if loop:
        print(f"\n(pass complete; looping in {CYCLE_SECONDS}s)", flush=True)
        time.sleep(CYCLE_SECONDS)
        return main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
