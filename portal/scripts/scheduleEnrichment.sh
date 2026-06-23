#!/bin/bash
# Schedule Wikipedia enrichment to run after GBIF cache downloads complete.
# Usage: bash scripts/scheduleEnrichment.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTAL_DIR="$SCRIPT_DIR/.."
ROOT_DIR="$SCRIPT_DIR/../.."

# Download PIDs (set these from the running downloads)
# Fish: 42175, Arachnida: 41852, Insecta: 41851
FISH_PID=${1:-42175}
ARACH_PID=${2:-41852}
INSECTA_PID=${3:-41851}

echo "⏳ Waiting for GBIF cache downloads to complete..."
echo "   Fish PID: $FISH_PID"
echo "   Arachnida PID: $ARACH_PID"
echo "   Insecta PID: $INSECTA_PID"
echo ""

# Wait for each download (skip if process already exited)
for pid in "$FISH_PID" "$ARACH_PID" "$INSECTA_PID"; do
  if kill -0 "$pid" 2>/dev/null; then
    echo "   Waiting for PID $pid..."
    wait "$pid" 2>/dev/null
    echo "   PID $pid completed."
  else
    echo "   PID $pid already completed."
  fi
done

echo ""
echo "✅ All downloads complete."
echo ""

# Now run the enrichment
echo "📖 Starting Wikipedia enrichment for all bird families..."
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.nvm/versions/node/v23.3.0/bin:$PATH"
cd "$PORTAL_DIR"
npx tsx scripts/enrichFromWikipedia.ts

echo ""
echo "✅ Wikipedia enrichment complete."
echo "📊 Run 'npm run typecheck' then commit changes."
