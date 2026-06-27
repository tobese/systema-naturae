#!/usr/bin/env python3
"""Tail-follows buildWikipediaDb.log and pushes (seen / total) percent to progressd.

Log lines we care about:
    seen=50000 matched=12 infobox=2 range=0
    Done. seen=N matched=N infobox=N range=N

The total page count is read from /tmp/wiki-dump-page-count.txt (written by
`bzcat … | wc -l`). If absent, a 6_200_000 fallback is used.

Usage:
    nohup python3 scripts/tailWikiDbProgress.py \
        > /Volumes/WikiDump/work/logs/tailer.log 2>&1 &
"""
from __future__ import annotations

import os
import re
import sys
import time
import urllib.request
from pathlib import Path

LOG = Path("/Volumes/WikiDump/work/logs/buildWikiDb.log")
PAGE_COUNT_FILE = Path("/tmp/wiki-dump-page-count.txt")
FALLBACK_TOTAL = 6_200_000

PROGRESSD = os.environ.get("PROGRESSD_URL", "http://localhost:9876")
SESSION_ID = "wiki_db_build"
SESSION_LABEL = "Wikipedia Offline DB Builder"

SEEN_RE = re.compile(r"seen=(\d+)\s+matched=(\d+)\s+infobox=(\d+)\s+range=(\d+)")
DONE_RE = re.compile(r"Done\.?\s+seen=(\d+)", re.I)
LINE_TIMEOUT_S = 1200  # 20 min — we keep tailing even if log is quiet


def get_total() -> int:
    try:
        return int(PAGE_COUNT_FILE.read_text().strip())
    except Exception:
        return FALLBACK_TOTAL


def post_progress(pct: float, msg: str, done: bool = False) -> None:
    payload = (
        '{"message":%s,"pct":%s,"done":%s,"label":%s}'
        % (
            _json_str(msg),
            f"{pct:.3f}",
            "true" if done else "false",
            _json_str(SESSION_LABEL),
        )
    ).encode()
    req = urllib.request.Request(
        f"{PROGRESSD}/api/sessions/{SESSION_ID}/progress",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            r.read()
    except Exception as e:
        print(f"  progressd push failed: {e}", file=sys.stderr, flush=True)


def _json_str(s: str) -> str:
    """Minimal JSON string encoder (stdlib urllib avoids importing json)."""
    out = ['"']
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def follow(fh):
    """Generator yielding lines as they appear (tail -f)."""
    fh.seek(0, os.SEEK_END)
    pos = fh.tell()
    idle = 0
    while True:
        line = fh.readline()
        if line.endswith("\n"):
            idle = 0
            yield line.rstrip()
            continue
        # No new data — wait and retry.
        time.sleep(2)
        idle += 2
        if idle > LINE_TIMEOUT_S:
            print(f"  no log activity for {idle}s, exiting", flush=True)
            return
        # If file was truncated, rewind; if younger than pos, also rewind (new file)
        try:
            cur = os.fstat(fh.fileno()).st_size
            if cur < pos:
                fh.seek(0)
                pos = 0
        except OSError:
            return


def main() -> int:
    total = get_total()
    print(f"tailer starting; total pages = {total:,}", flush=True)
    last_seen = -1
    last_push_ts = 0.0

    with LOG.open("r", encoding="utf-8", errors="replace") as fh:
        for line in follow(fh):
            m = SEEN_RE.search(line)
            if m:
                seen = int(m.group(1))
                matched = int(m.group(2))
                infobox = int(m.group(3))
                rng = int(m.group(4))
                if seen == last_seen:
                    continue
                last_seen = seen
                pct = min(100.0, (seen / total) * 100)
                msg = f"seen={seen:,}/{total:,} · matched={matched:,} · infobox={infobox:,} · range={rng:,}"
                now = time.time()
                if now - last_push_ts < 5 and seen < total:
                    continue
                last_push_ts = now
                post_progress(pct, msg)
                print(f"  {pct:6.2f}%  {msg}", flush=True)
                continue

            m = DONE_RE.search(line)
            if m:
                seen = int(m.group(1))
                post_progress(100.0, f"done · seen={seen:,}", done=True)
                print(f"  done · seen={seen:,}", flush=True)
                return 0

            # Fallback: the script writes "Done. seen=… matched=…" — match by hand.
            if line.lower().startswith("done") and "seen=" in line:
                post_progress(100.0, line[:200], done=True)
                print(f"  done fallback", flush=True)
                return 0

            if line.startswith("Matched "):
                post_progress(0.0, line[:200])
                print(f"  index phase: {line}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())