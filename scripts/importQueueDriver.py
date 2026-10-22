#!/usr/bin/env python3
"""Macie-side driver for the import pipeline.

Drives the split pipeline end-to-end for every source sitting at
stage `downloaded` in data/source-queue.json:

    1. transformColChecklist.py <archive> <slug> --apply
       -> writes work/<slug>/transformed.jsonl (+ meta sidecar)
    2. importTransformed.py <slug> with IMPORTWRITE_URL=http://q-bert:8089
       -> POSTs each (family, genus) to importwrite, flushes per family,
          appends to data/import-log.jsonl
    3. sourceQueue.py set --key <slug> --stage applied --added N --merged M ...

Run once (processes all downloaded sources, then exits) or loop with --loop.

Usage:
    python3 scripts/importQueueDriver.py              # one pass, then exit
    python3 scripts/importQueueDriver.py --loop       # keep polling
    nohup caffeinate -dimsu python3 scripts/importQueueDriver.py --loop > /tmp/importQueueDriver.log 2>&1 &
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
QUEUE_PATH = os.path.join(REPO_ROOT, "data", "source-queue.json")
IMPORTWRITE_URL = os.environ.get("IMPORTWRITE_URL", "http://q-bert:8089")
REFILL_THRESHOLD = 5
REFILL_BATCH = 10


def load_queue() -> dict:
    with open(QUEUE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_queue(q: dict) -> None:
    tmp = QUEUE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(q, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, QUEUE_PATH)


def set_stage(q: dict, key: str, stage: str, **stats) -> None:
    entry = q[key]
    entry["stage"] = stage
    entry.setdefault("history", []).append(
        {"at": datetime.now(timezone.utc).isoformat(), "stage": stage}
    )
    if stats:
        entry.update(stats)
    save_queue(q)


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

    # Get candidate keys from triageNext.py
    rc, out = run(
        ["python3", os.path.join(SCRIPT_DIR, "triageNext.py"),
         "--keys-only", "--limit", str(limit)],
        "triage",
    )
    if rc != 0:
        print(f"  triage FAILED (rc={rc}), cannot refill", flush=True)
        return q

    keys = [line.strip() for line in out.splitlines() if line.strip()]
    if not keys:
        print("  triage returned no candidates", flush=True)
        return q

    # Get full metadata (title, size, licence) for each key by re-running
    # triage without --keys-only and parsing the table.
    rc2, table = run(
        ["python3", os.path.join(SCRIPT_DIR, "triageNext.py"),
         "--limit", str(limit)],
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


def main() -> int:
    loop = "--loop" in sys.argv
    q = load_queue()

    # Auto-refill: if downloaded queue is low, triage + fetch new candidates.
    q = refill_queue(q)

    downloaded = [
        (k, v) for k, v in q.items() if v.get("stage") == "downloaded"
    ]
    if not downloaded:
        if loop:
            print("No sources at stage 'downloaded'. Sleeping 30s before retry.", flush=True)
            time.sleep(30)
            return main()
        print("No sources at stage 'downloaded'. Nothing to do.", flush=True)
        return 0

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
                save_queue(q)
            else:
                print(f"  {key} ({title}): archive not on disk ({candidate}), skipping", flush=True)
                set_stage(q, key, "blocked", reason="archive missing on disk")
                continue

        if not os.path.exists(archive):
            print(f"  {key} ({title}): archive not on disk ({archive}), skipping", flush=True)
            set_stage(q, key, "blocked", reason="archive missing on disk")
            continue

        print(f"\n== {key} — {title}", flush=True)

        # Step 1: transform
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

        # Step 2: apply via importwrite
        env = dict(os.environ, IMPORTWRITE_URL=IMPORTWRITE_URL)
        rc, out = run(
            ["python3", os.path.join(SCRIPT_DIR, "importTransformed.py"), key],
            "apply",
            env=env,
        )
        if rc != 0:
            print(f"  {key}: apply FAILED (rc={rc}), leaving at downloaded", flush=True)
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

    if loop:
        print("\n(pass complete; looping in 30s)", flush=True)
        time.sleep(30)
        return main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
