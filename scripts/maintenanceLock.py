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
"""
from __future__ import annotations
import contextlib
import fcntl
import os

LOCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", ".maintenance.lock")


@contextlib.contextmanager
def hold_exclusive():
    """Maintenance scripts: block until the lock is free, then hold it."""
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    fh = open(LOCK_PATH, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


@contextlib.contextmanager
def try_nonblocking():
    """The orchestrator: yields True if the lock was free (and now held), else
    False immediately -- never blocks the pipeline loop."""
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
