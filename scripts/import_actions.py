#!/usr/bin/env python3
"""Append-only log of every build/import action. Python counterpart of
portal/scripts/lib/importActions.ts — both write the same JSONL file
(portal/data/import-actions.jsonl) so a TS build and a Python import are
indistinguishable in the log.

Why this exists: a long-running buildData run stamps a deterministic uuid
onto every species node and writes those uuids back into the source family
files. If that run is killed partway through (a session closes, a machine
reboots, OOM), nothing on disk says "this build started at T, stamped these
families, and died here" — the tree is simply left half-stamped with no
record of what produced it. That is exactly how the 2026-10-13 uuid backfill
ended up uncommitted and untraceable.

So every action logs start, and logs finish/error/interrupted. The
uuid-stamp events record per-family what was written, which is the detail
that lets you reconstruct "what produced the missing uuids" after the fact.
The file is JSONL by design: appends are atomic single-line writes, so a
crash can never corrupt earlier entries, and tailing it is trivial.

Usage:
    from import_actions import log_action, install_interrupt_handlers
    install_interrupt_handlers("bacteria")
    log_action("start", "bacteria", {"archive": args.archive})
    ... do work ...
    log_action("finish", "bacteria", {"families": n, "species": m})
"""
import json
import os
import signal
import subprocess
import sys
import time

ACTIONS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "portal", "data", "import-actions.jsonl",
)

_GIT_SHA = None


def _git_sha():
    global _GIT_SHA
    if _GIT_SHA is not None:
        return _GIT_SHA or None
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=3,
        )
        _GIT_SHA = out.stdout.strip() or ""
    except Exception:
        _GIT_SHA = ""
    return _GIT_SHA or None


def log_action(event, kingdom, detail=None):
    """Append one JSONL line. Never raises — logging must not break a run."""
    try:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
                   + ".%03dZ" % (time.time() * 1000 % 1000),
            "event": event,
            "pid": os.getpid(),
            "host": os.environ.get("HOSTNAME", "localhost"),
            "kingdom": kingdom,
            "command": " ".join(sys.argv[1:]) or "(none)",
            "gitSha": _git_sha(),
        }
        if detail:
            entry.update(detail)
        os.makedirs(os.path.dirname(ACTIONS_PATH), exist_ok=True)
        with open(ACTIONS_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def install_interrupt_handlers(kingdom):
    """Write an `interrupted` event before exiting on SIGINT/SIGTERM."""
    def _handler(signum, frame):
        log_action("interrupted", kingdom,
                   {"signal": signum,
                    "note": "import killed before finish event"})
        os._exit(130)
    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)