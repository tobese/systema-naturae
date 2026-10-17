#!/usr/bin/env bash
# Apply the 2026-10-17 marine-worm batch on this machine, one dataset at a time.
#
# Sequential on purpose: every one of these writes the same family files, and two
# concurrent runs of an importer that rewrites whole family documents corrupt
# each other's writes in a way git cannot see until it is already a conflict.
#
# The insect half of the batch (WTaxa 1039, ScaleNet 315880, Nymphalidae 309267)
# runs on q-bert instead. The split is by phylum, not by convenience: weevils,
# scale insects and nymphalids share no family with Platyhelminthes, Nematoda
# or Decapoda, so the two machines touch disjoint files and cannot collide.
set -uo pipefail

cd "$(dirname "$0")/.."
ARCH="${SN_SOURCES_ROOT:-/Volumes/MacieExternal/sources}/archives"
LOG="${LOG:-/tmp/import-worms.log}"
KEYS="${KEYS:-1128 2302 1108 1193}"

: > "$LOG"
for key in $KEYS; do
  archive="$ARCH/checklistbank-$key/archive.zip"
  if [ ! -s "$archive" ]; then
    echo "=== $key  SKIP (no archive at $archive)" >> "$LOG"
    continue
  fi
  echo "=== $key  start $(date -u +%H:%M:%S)" >> "$LOG"
  if python3 scripts/importColChecklist.py "$archive" --apply >> "$LOG" 2>&1; then
    echo "=== $key  ok $(date -u +%H:%M:%S)" >> "$LOG"
  else
    echo "=== $key  FAILED rc=$? $(date -u +%H:%M:%S)" >> "$LOG"
  fi
done
echo "=== batch done $(date -u +%H:%M:%S)" >> "$LOG"
