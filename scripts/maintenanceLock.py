#!/usr/bin/env python3
"""Shared advisory lock so the live pipeline and one-off maintenance passes
never write taxonomy.json / family files at the same time.

Found 2026-10-23: resyncFamilyCounts.py and dedupeSpeciesAcrossFamilies.py
write the same files pipelineOrchestrator.py (via pendingFamilyWatcher) keeps
writing every ~60s. With no locking, whichever finishes last wins and the
other's fix silently vanishes -- that's why speciesCount fixes kept
reappearing identically run after run. Rule: a maintenance pass holds this
lock for its whole run; the orchestrator takes a non-blocking shot each cycle
and skips the cycle's writes rather than blocking or racing.

Two additions, 2026-10-31, after a dedupe released the lock the moment its
writes were done and the ordinator's next pending-family re-import landed
three new authority collisions before verifyTree had run:

* The holder passes its pid to children (SN_MAINTENANCE_LOCK_PID), and
  `hold_exclusive` in a process whose ancestor (or own earlier frame) already
  holds it goes straight through. So maintenanceSession.py can hold the lock
  across a script that takes it itself -- the wrap that self-deadlocked when
  tried by hand on dedupeSpeciesAcrossFamilies.py --apply.

* HOLD_PATH, a file, keeps the pipeline out after the lock is released: while
  it exists `try_nonblocking` (and the Go ordinator's maintlock.TryAcquire)
  refuse. maintenanceSession.py leaves it when verification finds an invariant
  got worse, so nothing writes on top of a tree no one has looked at yet.
  `hold_exclusive` ignores it -- the human fixing things must still get in.
"""
from __future__ import annotations
import contextlib
import fcntl
import os
import subprocess

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
LOCK_PATH = os.path.join(_DATA, ".maintenance.lock")
HOLD_PATH = os.path.join(_DATA, ".maintenance.hold")
ENV = "SN_MAINTENANCE_LOCK_PID"


def _parent(pid: int) -> int:
    try:
        out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                             capture_output=True, text=True).stdout.strip()
        return int(out) if out else 0
    except (OSError, ValueError):
        return 0


def _held_by_us() -> bool:
    """True when this process or one of its ancestors holds the lock."""
    try:
        holder = int(os.environ.get(ENV, "0"))
    except ValueError:
        return False
    if holder <= 1:  # 1 is launchd/init: everyone's ancestor
        return False
    pid = os.getpid()
    for _ in range(64):
        if pid == holder:
            return True
        if pid <= 1:
            return False
        pid = _parent(pid)
    return False


@contextlib.contextmanager
def hold_exclusive():
    """Maintenance scripts: block until the lock is free, then hold it."""
    if _held_by_us():
        yield
        return
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    fh = open(LOCK_PATH, "w")
    previous = os.environ.get(ENV)
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        os.environ[ENV] = str(os.getpid())
        yield
    finally:
        if previous is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = previous
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def hold_reason() -> str | None:
    """The hold file's content when the pipeline is held out, else None."""
    try:
        with open(HOLD_PATH, encoding="utf-8") as fh:
            return fh.read().strip() or "(no reason recorded)"
    except FileNotFoundError:
        return None


@contextlib.contextmanager
def try_nonblocking():
    """The orchestrator: yields True if the lock was free (and now held), else
    False immediately -- never blocks the pipeline loop. Also False while a
    maintenance hold is in place (see HOLD_PATH)."""
    if hold_reason() is not None:
        yield False
        return
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    fh = open(LOCK_PATH, "w")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            got = True
        except BlockingIOError:
            got = False
        yield got
    finally:
        if got:
            fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()
