#!/bin/bash
set -euo pipefail

PROGRESSD_URL="${PROGRESSD_URL:-http://localhost:9876}"
SESSION_ID="wiki_dump"
LABEL="Wikipedia Offline Index"
TARGET="/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream.xml.bz2"
TOTAL_BYTES=26437250146
STATE_FILE="/Volumes/WikiDump/work/wiki_dump_progress.txt"

mkdir -p "$(dirname "$STATE_FILE")"
last_pct=0

while true; do
  if [ -f "$TARGET" ]; then
    apparent=$(stat -f%z "$TARGET" 2>/dev/null || echo 0)
    # Use actual disk usage (du -k) since aria2 writes sparse files
    actual_kb=$(du -k "$TARGET" 2>/dev/null | awk '{print $1}')
    actual=$(( ${actual_kb:-0} * 1024 ))
    # Use whichever is smaller — once download completes, apparent==actual
    if [ "$apparent" -lt "$actual" ] || [ "$apparent" -eq 0 ]; then
      current=$apparent
    else
      current=$actual
    fi
    pct=$(python3 - <<'PY' "$current" "$TOTAL_BYTES" "$last_pct"
import sys
current = int(sys.argv[1])
total = int(sys.argv[2])
last = float(sys.argv[3])
val = round((current / total) * 100, 2) if total else 0.0
print(max(last, val))
PY
)
    last_pct="$pct"
    gib=$(python3 -c "print(f'{$current/1073741824:.2f}')")
    msg="Downloading multistream dump... ${gib} GiB"
  else
    pct=0
    msg="Waiting for dump download..."
  fi
  printf '%s\n' "$pct" > "$STATE_FILE"
  npx tsx portal/scripts/phylumProgressd.ts --id "$SESSION_ID" --label "$LABEL" --pct "$pct" --msg "$msg" >/dev/null 2>&1 || true
  sleep 60
done
