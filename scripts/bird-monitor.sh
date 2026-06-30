#!/bin/bash
# Simple terminal monitoring of bird enrichment

echo "🐦 BIRD ENRICHMENT MONITOR"
echo "======================="
echo ""

echo "✅ Enrichment: RUNNING"
echo "📝 Log: tail -f scripts/enrichment.log"
echo ""

cd /Users/tb/Dev/systema-naturae/portal

while true; do
    clear
    echo "🐦 BIRD ENRICHMENT MONITOR - $(date)"
    echo "======================="
    echo ""
    
    echo "📊 CURRENT STATUS:"
    echo "----------------"
    
    if [ -f "data/stuck-species-report.json" ]; then
        total_stuck=$(jq '.totalWikiStuck' data/stuck-species-report.json)
        birds_stuck=$(jq '.families | map(select(.class == "aves")) | sum(.stuck)' data/stuck-species-report.json)
        total_birds=$(jq '.families | map(select(.class == "aves")) | sum(.total)' data/stuck-species-report.json)
        
        echo "  Total Stuck Species: $total_stuck"
        echo "  Birds Stuck: $birds_stuck"
        echo "  Bird Coverage: $((total_birds - birds_stuck))/$total_birds"
        
        if [ "$birds_stuck" -lt 1000 ]; then
            echo "  📈 Status: ⚡ EXCELLENT! (Less than 1,000 stuck!)"
        elif [ "$birds_stuck" -lt 2000 ]; then
            echo "  📈 Status: ✅ Good progress"
        elif [ "$birds_stuck" -lt 3000 ]; then
            echo "  📈 Status: 👉 Progressing"
        else
            echo "  📈 Status: ❌ Critical (Needs attention)"
        fi
    fi
    
    echo ""
    echo "🔍 RECENT ENRICHMENT ACTIVITY:"
    echo "-----------------------------"
    
    if [ -f "scripts/enrichment.log" ]; then
        tail -10 "scripts/enrichment.log" | while read line; do
            if [[ "$line" == "*candidates*" ]]; then
                if [[ "$line" == *"100%"* ]]; then
                    echo "  ✅ COMPLETED: $(echo "$line" | head -c 60)"
                elif [[ "$line" == *"0%*" ]]; then
                    echo "  ❌ FAILED: $(echo "$line" | head -c 60)"
                fi
            fi
        done
    fi
    
    echo ""
    echo "📋 FAMILIES STILL NEEDING WORK:"
    echo "-----------------------------"
    
    if [ -f "data/stuck-species-report.json" ]; then
        jq '.families | map(select(.class == "aves" and .stuck > 50)) | {slug, stuck}' data/stuck-species-report.json | head -10
    fi
    
    echo ""
    echo "⏰ Last updated: $(date)"
    echo "🔄 Auto-refreshes every 10 seconds..."
    echo ""
    echo "Commands:"
    echo "  tail -f scripts/enrichment.log     - Real-time enrichment logs"
    echo "  cat scripts/enrichment.log | grep "/*%.*" - Case report"
    
    sleep 10
done
