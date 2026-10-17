#!/usr/bin/env bash
# Scaffold-and-place an absent-family dataset, under caffeinate.
#
#   scripts/scaffold.sh <checklistbank-key> [kingdom] [source]
#   scripts/scaffold.sh 2011 animalia worms
#
# This is the second half of an import. `importColChecklist.py` takes a dataset
# into families the tree already has and **refuses** everything else, by design:
# a species it cannot place gets no node, no placeholder family and no orphan.
# That leaves the source's absent families on the floor, which for WoRMS is
# 1,041 families and for the turbellarian list is 83.
#
# This wrapper runs the other half -- `importColStage2.py`, which scaffolds the
# missing family and places the species in it -- and then commits. Both halves
# are needed and neither substitutes for the other.
#
# caffeinate -dimsu is not optional *on macOS*. The run is tens of thousands of
# GNparser normalisations and several thousand family-file writes, so it outlives
# display sleep; without the assertion the Mac sleeps mid-run and the job stops
# with no error and no log line, which is indistinguishable from a hang.
#
# It is also macOS-only, so it is detected rather than assumed: the first run on
# q-bert (WSL2) died with rc=127 on every dataset, and `command not found` for a
# power-management wrapper is a poor way to learn which host you are on.
HOLD="$(command -v caffeinate || true)"
if [ -n "$HOLD" ]; then HOLD="$HOLD -dimsu"; else HOLD=""; fi

# Drain the queue in `docs/dataset-inbox.md` ("Measured 2026-10-17") with this.
set -uo pipefail

cd "$(dirname "$0")/.."

KEY="${1:?usage: scaffold.sh <checklistbank-key> [kingdom] [source]}"
KINGDOM="${2:-animalia}"
SOURCE="${3:-checklistbank}"
ARCHIVES="${SN_SOURCES_ROOT:-/Volumes/MacieExternal/sources}/archives"
ARCHIVE="$ARCHIVES/checklistbank-$KEY/archive.zip"
LOG="/tmp/scaffold-$KEY.log"

if [ ! -s "$ARCHIVE" ]; then
  echo "FATAL: no archive at $ARCHIVE" >&2
  echo "       fetch it first:  sh scripts/fetchBatch.sh $KEY" >&2
  exit 1
fi

: > "$LOG"
echo "=== $KEY kingdom=$KINGDOM source=$SOURCE  $(date -u +%H:%M:%S)" >> "$LOG"

$HOLD python3 scripts/importColStage2.py \
  --kingdom "$KINGDOM" --archive "$ARCHIVE" --source "$SOURCE" --apply \
  >> "$LOG" 2>&1
rc=$?

echo "=== $KEY exit=$rc  $(date -u +%H:%M:%S)" >> "$LOG"

if [ "$rc" -ne 0 ]; then
  echo "--- $KEY FAILED (rc=$rc); nothing committed, tail of $LOG:" >&2
  tail -20 "$LOG" >&2
  exit "$rc"
fi

# Only the files the scaffolder writes. taxonomy.json and colorRegistry.ts are
# included because a new family needs a node and a theme, and a family without a
# theme renders with no colours at all.
git add -A taxonomy/ portal/data/taxonomy.json portal/src/colorRegistry.ts
if git diff --cached --quiet; then
  echo "=== $KEY nothing to commit (every family it offered is already held)" >> "$LOG"
else
  git commit -q -m "Scaffold absent families: checklistbank-$KEY

$(grep -E 'B new families|new family files written|species added|new ORDER nodes' "$LOG" | sed 's/^ *//')"
  echo "=== $KEY committed" >> "$LOG"
fi

grep -E "accepted taxa|A existing|B new|C no family|new family files written|existing family files merged|species added|already present|new ORDER nodes|committed|exit=" "$LOG"