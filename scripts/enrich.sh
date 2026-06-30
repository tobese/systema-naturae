#!/bin/bash
# Quick bird enrichment script - simplified and ready to run

# Clean up any existing processes
pkill -f "tsx.*enrichFromWikipedia.ts" 2>/dev/null || true

# Start enrichment from the portal directory (where npm run enrich is configured)
nohup npm run enrich > scripts/enrichment.log 2>&1 &

echo "🐦 Bird Enrichment Started"
echo "========================"
echo "📝 Logs: tail -f scripts/enrichment.log"
echo "📊 Check: monitor-birds-simple.sh"
echo "📈 Progress: cat /Users/tb/Dev/systema-naturae/bird-monitor-last.txt"

echo "🔍 To see enrichment in real-time: tail -f scripts/enrichment.log"
echo "🔍 To monitor progress: ./monitor-birds-simple.sh"
