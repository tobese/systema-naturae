#!/usr/bin/env python3
"""Macie-side driver for the import pipeline.

Drives the split pipeline end-to-end for every source sitting at
stage `downloaded` in the source queue (scripts/sourceQueue.py,
data/source-queue/<key>.json):

    0. licence gate -- an NC licence goes straight to blocked, no archive
       work spent on it (see docs/dataset-inbox.md's AlgaeBase entry)
    1. transformColChecklist.py <archive> <slug> --apply (stage: triaging)
       -> writes work/<slug>/transformed.jsonl (+ meta sidecar); its
          printed routing stats are recorded as `triaged`, then the row
          is auto-promoted to `queued` -- this is the one pass that also
          serves as the dry run, since route_species() prints the same
          offered/held/staged/refused numbers with or without --apply
    2. importTransformed.py <slug> with IMPORTWRITE_URL=http://q-bert:8089
       (stage: applying)
       -> POSTs each (family, genus) to importwrite, flushes per family,
          appends to data/import-log.jsonl
    3. sourceQueue.py set --key <slug> --stage applied --added N --merged M ...

A source that needs a human call before any of this -- bacteria/virus
carry-through, a synthetic tree, a reader-format gap, a duplicate of an
already-decided source -- should never reach `downloaded` in the first
place: sourceQueue.py's `add()` refuses to register a key the manifest
already has a verdict for, and `triageNext.py`'s own candidate listing
filters the same way. Found 2026-10-22: a bulk add that bypassed both
left 33 ungated `downloaded` entries, including GTDB (on hold by policy)
and six already-taken sources, that this driver would have blindly
applied.

Run once (processes all downloaded sources, then exits) or loop with --loop.

Usage:
    python3 scripts/importQueueDriver.py              # one pass, then exit
    python3 scripts/importQueueDriver.py --loop       # keep polling
    nohup caffeinate -dimsu python3 scripts/importQueueDriver.py --loop > /tmp/importQueueDriver.log 2>&1 &
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
import sourceQueue as SQ  # noqa: E402

IMPORTWRITE_URL = os.environ.get("IMPORTWRITE_URL", "http://q-bert:8089")
REFILL_THRESHOLD = 5
REFILL_BATCH = 10


def load_queue() -> dict:
    """Every source, read fresh from its own file -- see sourceQueue.py's
    read_store(). Kept as a thin alias here since callers in this module
    already say `load_queue()`, not `SQ.read_store()`."""
    return SQ.read_store()


def set_stage(q: dict, key: str, stage: str, **stats) -> None:
    entry = q[key]
    entry["stage"] = stage
    entry.setdefault("history", []).append(
        {"at": datetime.now(timezone.utc).isoformat(), "stage": stage}
    )
    if stats:
        if stage == "applied":
            # Under `applied`, where sourceQueue.py report and the
            # dashboards read them -- top-level stats were invisible there
            # (see scripts/backfillAppliedStats.py).
            entry.setdefault("applied", {}).update(stats)
        else:
            entry.update(stats)
    SQ.write_entry(key, entry)
    SQ.log_event(key, stage, action="driver", **stats)


def refill_queue(q: dict, limit: int = REFILL_BATCH) -> dict:
    """If fewer than REFILL_THRESHOLD sources are at stage 'downloaded',
    triage `limit` new candidates from ChecklistBank, download each archive
    with fetchBatch.sh, and register them in the queue at stage 'downloaded'.

    Returns the (possibly updated) queue.
    """
    downloaded = [k for k, v in q.items() if v.get("stage") == "downloaded"]
    if len(downloaded) >= REFILL_THRESHOLD:
        return q

    need = REFILL_THRESHOLD - len(downloaded)
    print(f"\nOnly {len(downloaded)} source(s) at stage 'downloaded' "
          f"(< {REFILL_THRESHOLD}); refilling with up to {limit} candidates", flush=True)

    # Get candidate keys from triageNext.py. The type=taxonomic shelf goes
    # first; once it is used up (2026-10-30: all 481 held or decided, and
    # every refill came back empty) fall back to --all-types, which is where
    # 623 of the GBIF tab's 643 open-licence undecided sets are.
    for extra in ([], ["--all-types"]):
        rc, out = run(
            ["python3", os.path.join(SCRIPT_DIR, "triageNext.py"),
             "--keys-only", "--limit", str(limit)] + extra,
            "triage",
        )
        if rc != 0:
            print(f"  triage FAILED (rc={rc}), cannot refill", flush=True)
            return q
        keys = [line.strip() for line in out.splitlines() if line.strip()]
        if keys:
            break
        if not extra:
            print("  taxonomic shelf empty, trying --all-types", flush=True)
    if not keys:
        print("  triage returned no candidates", flush=True)
        return q

    # Get full metadata (title, size, licence) for each key by re-running
    # triage without --keys-only and parsing the table.
    rc2, table = run(
        ["python3", os.path.join(SCRIPT_DIR, "triageNext.py"),
         "--limit", str(limit)] + extra,
        "triage-meta",
    )
    meta: dict[str, dict] = {}
    if rc2 == 0:
        for line in table.splitlines():
            # Format: "   1,449,468     2232  cc by         The World Checklist..."
            # Fields separated by 2+ spaces; licence may contain a space ("cc by").
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4:
                try:
                    size = int(parts[0].replace(",", ""))
                except ValueError:
                    continue  # header / summary line, not data
                key = parts[1]
                licence = parts[2]
                title = parts[3]
                meta[key] = {"size": size, "title": title, "licence": licence}

    for key in keys:
        qkey = f"checklistbank-{key}"
        if qkey in q:
            print(f"  {qkey}: already in queue, skipping", flush=True)
            continue
        info = meta.get(key, {"size": 0, "title": key, "licence": "cc by"})
        # 1. Register as candidate
        run(
            ["python3", os.path.join(SCRIPT_DIR, "sourceQueue.py"), "add",
             "--key", qkey, "--title", info["title"], "--size", str(info["size"]),
             "--licence", info["licence"]],
            "queue-add",
        )
        # Reload so the in-memory queue sees the newly added entry.
        q = load_queue()
        # 2. Download archive (fetchBatch.sh takes the bare ChecklistBank key)
        rc, _ = run(
            ["bash", os.path.join(SCRIPT_DIR, "fetchBatch.sh"), key],
            "fetch",
        )
        sources_root = os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources")
        archive_path = os.path.join(sources_root, "archives", qkey, "archive.zip")
        if rc != 0 or not os.path.exists(archive_path):
            print(f"  {qkey}: archive not on disk after fetch, marking blocked", flush=True)
            set_stage(q, qkey, "blocked", reason="archive missing after fetch")
            continue
        # 3. Mark downloaded
        set_stage(q, qkey, "downloaded")
        print(f"  {qkey}: registered and downloaded", flush=True)

    return q


def run(cmd: list[str], label: str, env: dict | None = None) -> tuple[int, str]:
    print(f"  [{label}] {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.stdout:
        for line in result.stdout.splitlines():
            if line.strip():
                print(f"    {line}", flush=True)
    if result.returncode != 0 and result.stderr:
        for line in result.stderr.splitlines():
            if line.strip():
                print(f"    ! {line}", flush=True)
    return result.returncode, result.stdout


def process_downloaded(q: dict) -> None:
    """Run every `downloaded` source through the split pipeline to a
    terminal stage (applied/blocked/queued-on-failure). Mutates `q`'s
    stages on disk as it goes (via set_stage); does not return anything,
    since the caller always re-reads from disk afterward if it needs the
    current state. Split out of main() so scripts/pipelineOrchestrator.py
    can call this alongside the other stages it owns, in one process."""
    downloaded = [
        (k, v) for k, v in q.items() if v.get("stage") == "downloaded"
    ]
    if not downloaded:
        print("No sources at stage 'downloaded'.", flush=True)
        return

    print(f"{len(downloaded)} source(s) at stage 'downloaded'.", flush=True)

    for key, entry in downloaded:
        title = entry.get("title", key)
        archive = entry.get("archivePath")
        if not archive:
            sources_root = os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources")
            candidate = os.path.join(sources_root, "archives", key, "archive.zip")
            if os.path.exists(candidate):
                archive = candidate
                entry["archivePath"] = archive
                SQ.write_entry(key, entry)
            else:
                print(f"  {key} ({title}): archive not on disk ({candidate}), skipping", flush=True)
                set_stage(q, key, "blocked", reason="archive missing on disk")
                continue

        if not os.path.exists(archive):
            print(f"  {key} ({title}): archive not on disk ({archive}), skipping", flush=True)
            set_stage(q, key, "blocked", reason="archive missing on disk")
            continue

        print(f"\n== {key} — {title}", flush=True)

        # Licence gate, before spending any time on the archive: an NC
        # licence needs a standing-policy call this project has declined
        # twice already (one documented exception, iNaturalist), not a
        # per-source default. Checked against the row's own `licence`
        # field (set at `add` time) rather than re-fetching it, so this
        # has no cost for the common open-licence case.
        licence = (entry.get("licence") or "").lower()
        if re.search(r"\bnc\b", re.sub(r"[\s-]+", " ", licence)):
            set_stage(q, key, "blocked",
                      reason=f"CC BY-NC licence ({licence or 'nc'}) -- needs a policy "
                             f"decision, this project holds one documented NC exception "
                             f"already (iNaturalist), see docs/dataset-inbox.md")
            print(f"  {key}: blocked — NC licence", flush=True)
            continue

        # Stage 1: triage. transformColChecklist.py prints the full routing
        # stats (offered/held/staged/refused) whether or not --apply is
        # passed, so running it with --apply does double duty as both the
        # triage dry run and the real transform -- no second pass needed.
        set_stage(q, key, "triaging")
        rc, transform_out = run(
            ["python3", os.path.join(SCRIPT_DIR, "transformColChecklist.py"), archive, key, "--apply"],
            "transform",
        )
        # rc 3/4 mean transformColChecklist.py deliberately wrote nothing --
        # a format this pipeline can't read yet, not a transient failure.
        # Leaving these at "downloaded" makes the driver retry them forever
        # (found 2026-10-22 racing against an orphaned duplicate driver on
        # checklistbank-139831); blocked is the correct terminal state.
        if rc == 3:
            set_stage(q, key, "blocked", reason="txtree format — needs scripts/txtree.py path, see docs/import.md")
            print(f"  {key}: blocked — txtree format, not handled by this driver", flush=True)
            continue
        if rc == 4:
            set_stage(q, key, "blocked", reason="unsupported archive format (no .txtree, no DwCA/ColDP table)")
            print(f"  {key}: blocked — unsupported archive format", flush=True)
            continue
        if rc != 0:
            print(f"  {key}: transform FAILED (rc={rc}), leaving at downloaded", flush=True)
            continue

        # If nothing was staged ("nothing to do"), there's no transformed.jsonl
        # to apply — mark applied with zero stats and move on.
        if "nothing to do" in transform_out:
            set_stage(q, key, "applied", added=0, merged=0, crossFamily=0, families=0)
            print(f"  {key}: applied — nothing to do (all already held)", flush=True)
            continue

        # Record the triage numbers route_species() already printed, then
        # auto-promote: open licence and a real transformed.jsonl written is
        # the "safe to apply automatically" case this driver handles. A
        # dataset that needs a human call (bacteria/virus carry-through, a
        # synthetic tree, a reader-format gap) is kept out of `downloaded`
        # in the first place -- see the source queue's blocked/declined
        # entries and sourceQueue.py add()'s manifest check.
        def _num(pattern):
            m = re.search(pattern, transform_out)
            return int(m.group(1).replace(",", "")) if m else None
        triaged = {
            "offered": _num(r"offered:\s*([\d,]+)"),
            "alreadyHeld": _num(r"already held \(skipped\):\s*([\d,]+)"),
            "staged": _num(r"staged:\s*([\d,]+)"),
            "refused": _num(r"REFUSED \(would need a new family\):\s*([\d,]+)"),
        }
        offered, refused = triaged["offered"], triaged["refused"]
        triaged["refusalRate"] = round(refused / offered, 4) if offered and refused is not None else None
        set_stage(q, key, "triaged", triaged=triaged)
        set_stage(q, key, "queued")

        # Step 2: apply via importwrite
        set_stage(q, key, "applying")
        env = dict(os.environ, IMPORTWRITE_URL=IMPORTWRITE_URL)
        rc, out = run(
            ["python3", os.path.join(SCRIPT_DIR, "importTransformed.py"), key],
            "apply",
            env=env,
        )
        if rc != 0:
            print(f"  {key}: apply FAILED (rc={rc}), leaving at queued", flush=True)
            set_stage(q, key, "queued")
            continue

        # Parse summary from importTransformed output (well-formed lines):
        #   "      importwrite: 841 added, 6398 merged (9 already existed in a different family)"
        #   "      flushed 90 families"
        import re as _re
        added = merged = cross_family = families = 0
        m = _re.search(r"importwrite:\s*(\d+)\s+added,\s*(\d+)\s+merged", out)
        if m:
            added = int(m.group(1))
            merged = int(m.group(2))
        m2 = _re.search(r"\(\s*(\d+)\s+already existed", out)
        if m2:
            cross_family = int(m2.group(1))
        m3 = _re.search(r"flushed\s+(\d+)\s+famil(?:y|ies)", out)
        if m3:
            families = int(m3.group(1))

        # Step 3: mark applied
        set_stage(
            q, key, "applied",
            added=added, merged=merged, crossFamily=cross_family, families=families,
        )
        print(f"  {key}: applied — +{added} added, {merged} merged, {cross_family} cross-family, {families} families", flush=True)


def main() -> int:
    """Standalone CLI, kept for manual single-pass debugging of just this
    stage. In production this module is imported by
    scripts/pipelineOrchestrator.py, which also owns needs-rerun and the
    pending-family sweep in the same process/log -- run that, not this,
    to drive the pipeline end-to-end."""
    loop = "--loop" in sys.argv
    q = load_queue()
    q = refill_queue(q)
    process_downloaded(q)
    if loop:
        print("\n(pass complete; looping in 30s)", flush=True)
        time.sleep(30)
        return main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
