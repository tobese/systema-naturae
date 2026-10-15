#!/usr/bin/env bash
# post-import.sh — standard post-import workflow.
#
# Why this exists: a buildData run stamps a deterministic uuid onto every
# species node and writes those uuids back into the source family files. The
# uuid is SHA-1 v5 of `kingdom|phylum|class|order|family|genus|species|
# authorship`, so it is reproducible — but only from the tree that produced
# it. If you backfill uuids onto a working tree that is *behind* origin/main,
# and then merge, the backfill and the upstream enrich both edit the same
# regions (uuid lines vs descriptions on adjacent lines) and git produces
# thousands of unresolvable conflicts. That is exactly what happened with the
# 2026-10-13 uuid backfill, which ended up uncommitted and untraceable.
#
# The fix is not "merge more carefully". It is: never backfill onto a stale
# tree. Always fast-forward to origin/main first, then backfill, then commit
# the *backfill only*. Because the uuid is deterministic, re-running it on the
# current tree produces the same values as the previous run for unchanged
# nodes — so a re-backfill is idempotent and safe to commit as a single clean
# commit. The import-actions log (portal/data/import-actions.jsonl) records
# every uuid-stamp, so if a run dies partway the log answers "what produced
# the missing uuids".
#
# Usage:
#   sh scripts/post-import.sh [--kingdom animalia] [--unified]
#
#   --kingdom   which kingdom to backfill+build (default: all declared)
#   --unified   also write the monolithic unified-taxonomy.json (opt-in;
#               normally skipped — see buildData.ts)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# The six kingdoms declared in portal/data/kingdom-config.json are the source
# of truth for what to backfill+build. bacteria and viruses are not in that
# config (they resolve their input via SN_INPUT in buildData.ts), so they are
# appended explicitly here.
UNIFIED=""
if [ -z "${SN_KINGDOMS:-}" ]; then
  CONFIG_KINGDOMS="$(python3 -c "
import json,sys
print(' '.join(json.load(open('portal/data/kingdom-config.json'))['kingdoms'].keys()))
" 2>/dev/null)"
  if [ -n "$CONFIG_KINGDOMS" ]; then
    KINGDOMS=($CONFIG_KINGDOMS bacteria viruses)
  else
    KINGDOMS=(animalia plantae fungi chromista protozoa archaea bacteria viruses)
  fi
else
  KINGDOMS=(${SN_KINGDOMS})
fi
while [ $# -gt 0 ]; do
  case "$1" in
    --kingdom) KINGDOMS=("$2"); shift 2 ;;
    --unified) UNIFIED="SN_BUILD_UNIFIED=1"; shift ;;
    *) echo "post-import.sh: unknown arg $1" >&2; exit 2 ;;
  esac
done

echo "==> 0. Sync to origin/main (fast-forward only — never merge)"
git fetch origin
if ! git diff --quiet HEAD origin/main; then
  echo "    local is behind; fast-forwarding"
  git merge --ff-only origin/main
else
  echo "    up to date"
fi
git status --short | head -5 || true

for KINGDOM in "${KINGDOMS[@]}"; do
  echo ""
  echo "==> 1. Backfill uuids + build $KINGDOM"
  export SN_KINGDOM="$KINGDOM"
  export NODE_OPTIONS="--max-old-space-size=8192"
  # bacteria and viruses are not in kingdom-config.json — they resolve their
  # input via SN_INPUT in buildData.ts.
  case "$KINGDOM" in
    bacteria) export SN_INPUT="data/taxonomy-bacteria.json" ;;
    viruses)  export SN_INPUT="data/taxonomy-viruses.json" ;;
    *) unset SN_INPUT ;;
  esac
  cd portal
  if [ -n "$UNIFIED" ]; then export SN_BUILD_UNIFIED=1; fi
  sh scripts/buildData.sh
  cd "$ROOT"

  echo "==> 2. Commit the backfill only (chunked)"
  # Only the uuid-stamped family JSONs belong in this commit. The build
  # outputs under portal/data/ are gitignored; the import-actions log is
  # gitignored. Nothing derived should land here.
  git add -A -- taxonomy/
  if git diff --cached --quiet; then
    echo "    nothing to commit (backfill already current)"
  else
    git commit -m "uuid backfill: stamp deterministic uuid onto every species node ($KINGDOM)

Re-run of the deterministic SHA-1 v5 backfill on a tree fast-forwarded to
origin/main first, so the values match what origin already carries and the
commit is a clean single commit rather than a merge with thousands of
conflicts. See scripts/post-import.sh."
  fi
done

echo ""
echo "==> 3. Push"
git push origin main

echo ""
echo "==> 4. Refresh gap reports"
cd portal
npx tsx scripts/findGaps.ts
npx tsx scripts/reportPhyla.ts
npx tsx scripts/generateGapTasks.ts
cd "$ROOT"

echo ""
echo "==> 5. Verify"
make verify || echo "    (verify reported issues — see scripts/fix_*.py)"

echo ""
echo "post-import.sh: done."