#!/usr/bin/env bash
# sync.sh — keep this checkout in sync with origin/main.
#
# Why this exists: both Macie and q-bert run the import pipeline against the
# same tree, and the uuid backfill is deterministic (SHA-1 v5 of
# `kingdom|phylum|class|order|family|genus|species|authorship`), so running it
# on either machine converges to the same tree. What is *not* deterministic is
# the import pipeline itself — NCBI/GTDB runs add new species, and two machines
# importing the same source at the same time produce divergent, unmergeable
# trees.
#
# So the rule is simple and it is what this script enforces:
#
#   1. Pull origin/main first. Fast-forward only — never merge, never rebase
#      onto a tree that has uncommitted work. A merge here is how the 2026-10-13
#      uuid backfill produced 11,046 unresolvable conflicts: the local backfill
#      and the upstream enrich both edit the same regions.
#   2. Do the work.
#   3. Commit the *backfill only*. Build outputs under portal/data/ are
#      gitignored; the import-actions log is gitignored. Nothing derived lands
#      in the commit.
#   4. Push. If the push is rejected, the other machine wrote something — pull
#      again and re-run the backfill (it is idempotent, so it produces the same
#      values for unchanged nodes and only adds the new ones).
#
# Usage:
#   sh scripts/sync.sh pull            # fast-forward to origin/main
#   sh scripts/sync.sh push            # push local commits
#   sh scripts/sync.sh both            # pull, then push
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cmd="${1:-both}"
case "$cmd" in
  pull)
    echo "==> git fetch"
    git fetch origin
    if git diff --quiet HEAD origin/main; then
      echo "    up to date"
    else
      echo "    fast-forwarding"
      git merge --ff-only origin/main
    fi
    ;;
  push)
    echo "==> git push"
    git push origin main
    ;;
  both)
    "$0" pull
    echo ""
    "$0" push
    ;;
  *)
    echo "sync.sh: unknown command $1 (pull|push|both)" >&2
    exit 2
    ;;
esac

echo "==> status"
git status --short | head -10 || true
echo "    $(git rev-parse --short HEAD)  $(git rev-parse --short origin/main)"