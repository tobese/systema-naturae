#!/usr/bin/env bash
#
# dispatch.sh — coordinate distributed plant enrichment from Macie.
#
#   1. Ensure dbserved is running on Macie (:9877).
#   2. Launch one enrichWorker shard per host.
#   3. Watch progressd (:9876) for per-host progress.
#
# Modes:
#   sh scripts/dispatch.sh --dry-run        # one local shard (0/1) against localhost
#   sh scripts/dispatch.sh                  # fan out to HOSTS below
#
# Multi-host prerequisites (per worker): repo reachable at REPO_PATH (SMB mount
# of this machine's repo), `npx tsx` available, network access to Macie:9877/9876.
set -euo pipefail

# --- config ------------------------------------------------------------------
MACIE_HOST="${MACIE_HOST:-macie.local}"       # how workers reach this box
REPO_PATH="${REPO_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"  # path on each worker (SMB mount)
DB_PORT=9880   # 9877 is taken by ocd modelsd
PROGRESSD_PORT=9876
LIVE_FLAG="${LIVE_FLAG:---live}"              # set LIVE_FLAG="" to skip Tier-2 REST
PUSH_FLAG="${PUSH_FLAG:---push}"              # set PUSH_FLAG="" to keep writes local (SMB-mount model)

# Worker hosts, in shard order. Macie itself is shard 0 (runs locally).
# Format: "label:ssh_target" — ssh_target empty means run locally.
HOSTS=(
  "MACIE:"
  "STEAMIE:opencode@steamie.local"
  "BIGGIE:biggie.local"
  "DEBBIE:debbie.local"
)
# -----------------------------------------------------------------------------

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Ensuring dbserved on :$DB_PORT"
if curl -s -m 2 "http://localhost:$DB_PORT/health" >/dev/null 2>&1; then
  echo "    already up: $(curl -s "http://localhost:$DB_PORT/health")"
else
  echo "    starting dbserved (background)…"
  nohup npx tsx scripts/dbserved.ts --port "$DB_PORT" >/tmp/dbserved.log 2>&1 &
  for i in $(seq 1 60); do
    curl -s -m 2 "http://localhost:$DB_PORT/health" >/dev/null 2>&1 && break
    sleep 2
  done
  curl -s -m 2 "http://localhost:$DB_PORT/health" >/dev/null 2>&1 \
    && echo "    up: $(curl -s http://localhost:$DB_PORT/health)" \
    || { echo "    FAILED to start dbserved (see /tmp/dbserved.log)"; exit 1; }
fi

PROGRESS_ID="${PROGRESS_ID:-plant-enrich-2026-07-05}"
start_session() { curl -s -m 3 -X POST "http://localhost:$PROGRESSD_PORT/api/sessions/$PROGRESS_ID/start" >/dev/null 2>&1 || true; }
done_session()  { curl -s -m 3 -X POST "http://localhost:$PROGRESSD_PORT/api/sessions/$PROGRESS_ID/done"  >/dev/null 2>&1 || true; }

if [ "$DRY_RUN" = "1" ]; then
  echo "==> DRY RUN: single local shard 0/1 against localhost"
  start_session
  npx tsx scripts/enrichWorker.ts --shard 0/1 $LIVE_FLAG \
    --db-url "http://localhost:$DB_PORT" \
    --progressd "http://localhost:$PROGRESSD_PORT"
  done_session
  echo "==> dry run complete"
  exit 0
fi

N=${#HOSTS[@]}
echo "==> Fanning out to $N shards"
DB_URL="http://$MACIE_HOST:$DB_PORT"
PD_URL="http://$MACIE_HOST:$PROGRESSD_PORT"
start_session

for k in "${!HOSTS[@]}"; do
  entry="${HOSTS[$k]}"
  label="${entry%%:*}"
  target="${entry#*:}"
  cmd="cd '$REPO_PATH' && npx tsx scripts/enrichWorker.ts --shard $k/$N $LIVE_FLAG $PUSH_FLAG --db-url '$DB_URL' --progressd '$PD_URL'"
  if [ -z "$target" ]; then
    echo "    [$label] shard $k/$N (local)"
    ( eval "$cmd" >"/tmp/enrich-$label.log" 2>&1 & )
  else
    echo "    [$label] shard $k/$N → ssh $target"
    ssh -o BatchMode=yes -o ConnectTimeout=8 "$target" "$cmd" >"/tmp/enrich-$label.log" 2>&1 &
  fi
done

echo "==> All shards launched. Logs: /tmp/enrich-*.log"
echo "==> Watch progress: http://localhost:$PROGRESSD_PORT/  (or curl :$PROGRESSD_PORT/api/sessions)"
wait
done_session
echo "==> All shards finished."

# Coordinator merge: each worker published its shard as origin/enrich/<id>-s<k>
# (disjoint files). Merge them into main here so only ONE push hits main → one
# Pages deploy, no worker-vs-worker push races.
if [ -n "$PUSH_FLAG" ]; then
  echo "==> Merging shard branches into main"
  git fetch origin --quiet
  merged=0
  for k in $(seq 0 $((N - 1))); do
    b="enrich/${PROGRESS_ID}-s${k}"
    if git rev-parse --verify --quiet "origin/$b" >/dev/null 2>&1; then
      if git merge --no-edit "origin/$b"; then
        merged=$((merged + 1))
      else
        echo "!! merge conflict on $b — resolve manually, then: git push origin main"
        exit 1
      fi
    fi
  done
  if [ "$merged" -gt 0 ]; then
    git push origin main
    echo "==> merged $merged shard branch(es) → main pushed (single deploy)"
    for k in $(seq 0 $((N - 1))); do
      git push origin --delete "enrich/${PROGRESS_ID}-s${k}" >/dev/null 2>&1 || true
    done
  else
    echo "==> no shard branches found to merge"
  fi
fi
