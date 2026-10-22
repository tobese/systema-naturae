#!/usr/bin/env bash
# Commit working-tree changes in bounded chunks instead of one giant
# `git add` + `git commit` over 13k+ family files.
#
# Disk-safety: kilo's per-family / per-phylum chunk commits left orphaned
# .git/objects/pack/tmp_pack_* files (from auto-gc repacks) that filled the
# disk (~16 GB). This script now:
#   - disables local gc.auto for the duration (no mid-run repacks)
#   - splits oversized buckets into --chunk-size commits (default 100 files)
#   - sweeps orphaned tmp_pack_* files before/after the run
#
# Usage:
#   scripts/commit-chunks.sh "Enrich plantae + protozoa from ITIS/Wikidata" [--chunk-size 100] [--include-untracked]
#
# Each taxonomy/<kingdom>/<phylum> bucket is one chunk (n/m). Files outside
# taxonomy/ land in "__other__" and are committed last. The untracked files
# (derived indexes, tasks/) are NOT committed unless --include-untracked is
# passed, in which case they are added as a final chunk.
set -euo pipefail

MSG=""
CHUNK_SIZE=100
INCLUDE_UNTRACKED=""

while [ $# -gt 0 ]; do
  case "$1" in
    --chunk-size)
      CHUNK_SIZE="${2:-100}"
      shift 2
      ;;
    --include-untracked)
      INCLUDE_UNTRACKED=1
      shift
      ;;
    *)
      if [ -z "$MSG" ]; then MSG="$1"; else MSG="$MSG $1"; fi
      shift
      ;;
  esac
done

MSG="${MSG:-WIP: chunked commit}"

cd "$(dirname "$0")/.."

GIT_DIR="${GIT_DIR:-.git}"
PACK_DIR="$GIT_DIR/objects/pack"

# ── disk safety ─────────────────────────────────────────────────────────────
# Disable auto-gc so no commit mid-run triggers a repack that leaves behind
# orphaned tmp_pack_* files if the run is interrupted.
git config --local gc.auto 0 2>/dev/null || true

sweep_tmp_packs() {
  if [ -d "$PACK_DIR" ]; then
    local n
    n=$(find "$PACK_DIR" -maxdepth 1 -name 'tmp_pack_*' -type f 2>/dev/null | wc -l)
    if [ "$n" -gt 0 ]; then
      echo "sweeping $n orphaned tmp_pack_* files from $PACK_DIR"
      find "$PACK_DIR" -maxdepth 1 -name 'tmp_pack_*' -type f -delete 2>/dev/null || true
    fi
  fi
}
sweep_tmp_packs

mapfile -t ALL < <(git status --porcelain | awk '{print $2}')
if [ ${#ALL[@]} -eq 0 ]; then
  echo "nothing to commit"
  exit 0
fi

# Group by taxonomy/<kingdom>/<phylum>/... — the first two path components
# after taxonomy/. Files outside taxonomy/ (or with fewer components) land in
# the "__other__" bucket and are committed last.
declare -A BUCKETS
for f in "${ALL[@]}"; do
  if [[ "$f" == taxonomy/* ]]; then
    rest="${f#taxonomy/}"
    key="$(echo "$rest" | cut -d/ -f1-2 | tr '/' '_')"
    BUCKETS["$key"]+=" $f"
  else
    BUCKETS["__other__"]+=" $f"
  fi
done

readarray -t KEYS < <(printf '%s\n' "${!BUCKETS[@]}" | sort)
total="${#KEYS[@]}"
n=0

commit_chunk() {
  local label="$1" files="$2"
  local count
  count=$(echo "$files" | wc -w)
  echo "=== chunk  $label  ($count files)"
  # Single git add with all paths at once (one spawn, fast).
  # shellcheck disable=SC2086
  git add -- $files
  if git diff --cached --quiet; then
    echo "  (empty after add, skipping commit)"
    git reset -q
    return 0
  fi
  git commit -m "$label" || { echo "  commit failed — fix and re-run"; return 1; }
}

for key in "${KEYS[@]}"; do
  n=$((n + 1))
  files="${BUCKETS[$key]}"
  # Split oversized buckets into chunk-size commits so no single commit packs
  # too many objects (keeps each round-trip quick and resumable).
  local_idx=0
  chunk_files=""
  for f in $files; do
    chunk_files="$chunk_files $f"
    local_idx=$((local_idx + 1))
    if [ "$local_idx" -ge "$CHUNK_SIZE" ]; then
      commit_chunk "$MSG ($n/$total.p$local_idx)" "$chunk_files"
      chunk_files=""
      local_idx=0
    fi
  done
  if [ -n "$chunk_files" ]; then
    commit_chunk "$MSG ($n/$total.premainder)" "$chunk_files"
  fi
done

if [ "$INCLUDE_UNTRACKED" = "1" ]; then
  echo "=== final chunk: untracked files"
  git add -A
  git diff --cached --quiet || git commit -m "$MSG (untracked)" || true
fi

# Re-enable gc.auto and sweep any tmp packs left by this run.
git config --local gc.auto 1 2>/dev/null || true
sweep_tmp_packs

echo "=== done ($n buckets)"
