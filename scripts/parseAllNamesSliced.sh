#!/bin/sh
# Parse every name in the tree through GBIF, in slices, slowly enough to not be
# throttled.
#
# Why sliced rather than parallel
# -------------------------------
# GBIF throttles by IP, and it does so without an error: the run simply stops
# advancing. Measured during the first attempt -- a request that had taken 7.5s
# for 1,000 names was taking 11s for 50, and throughput went to zero with the
# process still alive. A single-threaded burst of 1.3M names cannot finish.
#
# `$PARSE_WORKERS` (default 4) inside one shard, 8 shards, and a 10 minute gap between shards.
# That is slow on purpose: 8 shards x ~10 min work + 7 x 10 min gaps is roughly
# 2h20m wall clock for the full 1,306,268 names. Correctness over speed, because
# a throttled run looks identical to a successful one until you check the line
# count.
#
# Sharding is `--shard i/n` on the sorted (name, rank) pair list, so shards are
# disjoint and reproducible. Each writes its own file; they are concatenated
# afterwards rather than appended to, so an interrupted run leaves no
# half-overwritten index.
#
# Usage
# -----
# `PARSE_WORKERS=8 PARSE_GAP_SECONDS=300 sh scripts/parseAllNamesSliced.sh` on q-bert.
#   sh scripts/parseAllNamesSliced.sh 2 4      # only shard 3 of 4
set -eu

SHARDS_TOTAL=8
ONLY_I=${1:-}
ONLY_N=${2:-}
GAP=${GAP_SECONDS:-600}
OUTDIR=portal/data/name-parse-shards
MERGED=portal/data/name-parse-index.jsonl

mkdir -p "$OUTDIR"

if [ -n "$ONLY_I" ]; then
  echo "running only shard $((ONLY_I+1))/$ONLY_N"
  WORKERS="${PARSE_WORKERS:-4}"
  exec python3 scripts/parseAllNames.py --workers "$WORKERS" \
    --shard "$ONLY_I/$ONLY_N" \
    --out "$OUTDIR/shard-$ONLY_I.jsonl" \
    --report "docs/reports/name-parser-shard-$ONLY_I.md"
fi

i=0
while [ "$i" -lt "$SHARDS_TOTAL" ]; do
  echo ""
  echo "=== shard $((i+1))/$SHARDS_TOTAL  $(date '+%H:%M:%S') ==="
  WORKERS="${PARSE_WORKERS:-4}"
  if python3 scripts/parseAllNames.py --workers "$WORKERS" \
       --shard "$i/$SHARDS_TOTAL" \
       --out "$OUTDIR/shard-$i.jsonl" \
       --report "docs/reports/name-parser-shard-$i.md"; then
    echo "    shard $i done: $(wc -l < "$OUTDIR/shard-$i.jsonl" | tr -d ' ') lines"
  else
    echo "    shard $i FAILED - leaving it for a re-run, not merging a partial"
  fi
  i=$((i + 1))
  if [ "$i" -lt "$SHARDS_TOTAL" ]; then
    echo "    sleeping ${GAP}s before the next shard"
    sleep "$GAP"
  fi
done

echo ""
echo "=== merging ==="
cat "$OUTDIR"/shard-*.jsonl > "$MERGED"
total=$(wc -l < "$MERGED" | tr -d ' ')
echo "  $MERGED: $total lines from $(ls "$OUTDIR"/shard-*.jsonl | wc -l | tr -d ' ') shards"
echo "  expected 1,306,268 (1,306,249 distinct names; some carry two ranks)"
if [ "$total" -lt 1306268 ]; then
  echo "  INCOMPLETE - re-run the missing shards; the index is not whole"
fi