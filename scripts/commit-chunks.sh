#!/usr/bin/env bash
# Commit working-tree changes in bounded chunks instead of one giant
# `git add` + `git commit` over 13k+ family files.
#
# Why: this repo's taxonomy/ tree is ~22k files. A single `git add -A` takes
# ~15-20 min (fsmonitor handshake + hashing), which blows past tool timeouts
# and loses the whole staging if it is killed midway. Chunking by kingdom+phylum
# bounds each round-trip to a few minutes and makes the operation resumable:
# re-running skips chunks that are already committed.
#
# Usage:
#   scripts/commit-chunks.sh "Enrich plantae + protozoa from ITIS/Wikidata"
#
# Each chunk is committed with the supplied message plus " (n/m)". The
# untracked files (derived indexes, tasks/) are NOT committed — pass
# --include-untracked to add them all as a final chunk.
set -euo pipefail

MSG="${1:-WIP: chunked commit}"
INCLUDE_UNTRACKED="${2:-}"

cd "$(dirname "$0")/.."

mapfile -t ALL < <(git status --porcelain | awk '{print $2}')
if [ ${#ALL[@]} -eq 0 ]; then
  echo "nothing to commit"
  exit 0
fi

# Group by taxonomy/<kingdom>/<phylum>/... — the first three path components
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

# Deterministic order.
readarray -t KEYS < <(printf '%s\n' "${!BUCKETS[@]}" | sort)
total="${#KEYS[@]}"
n=0
for key in "${KEYS[@]}"; do
  n=$((n + 1))
  files="${BUCKETS[$key]}"
  count=$(echo "$files" | wc -w)
  echo "=== chunk $n/$total  $key  ($count files)"
  git add -- $files
  if git diff --cached --quiet; then
    echo "  (empty after add, skipping commit)"
    git reset -q
    continue
  fi
  git commit -m "$MSG ($n/$total)" || echo "  commit failed — fix and re-run"
done

if [ "$INCLUDE_UNTRACKED" = "--include-untracked" ]; then
  echo "=== final chunk: untracked files"
  git add -A
  git diff --cached --quiet || git commit -m "$MSG (untracked)" || true
fi

echo "=== done ($n chunks)"