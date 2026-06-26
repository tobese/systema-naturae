#!/bin/bash
# portal/scripts/importSmallGaps.sh

# The list of 10 families that have small remaining species gaps
FAMILIES=(
  "grallariidae"
  "eublepharidae"
  "lacertidae"
  "chamaeleonidae"
  "colubridae"
  "scincidae"
  "sepiidae"
  "echinidae"
  "dendrobatidae"
  "pelobatidae"
)

export OLLAMA_MODEL="qwen2.5:3b"

echo "=== Starting Automated Batch Import of 10 Small-Gap Families ==="
GLOBAL_START=$SECONDS
COUNT=0
TOTAL_FAMILIES=${#FAMILIES[@]}

for family in "${FAMILIES[@]}"; do
  COUNT=$((COUNT + 1))
  echo ""
  echo "--------------------------------------------------------"
  echo "[$COUNT/$TOTAL_FAMILIES] Processing family: $family"
  echo "--------------------------------------------------------"
  
  FAMILY_START=$SECONDS
  
  # 1. Run local import with qwen2.5:3b
  npx tsx scripts/importFamily.ts "$family"
  
  if [ $? -eq 0 ]; then
    FAMILY_DURATION=$(( SECONDS - FAMILY_START ))
    echo "✅ Successfully imported $family in ${FAMILY_DURATION}s."
    
    # 2. Run sanity-fixing suite on the updated codebase
    echo "🧹 Running sanity fixes..."
    python3 ../scripts/fix_duplicates.py
    python3 ../scripts/fix_continents.py
    python3 ../scripts/fix_lineage.py
    python3 ../scripts/fix_subspecies.py
    python3 ../scripts/fix_all_descriptions.py
    
    # 3. Rebuild unified taxonomy and recalculate import logs
    echo "🏗️ Rebuilding taxonomy data..."
    sh scripts/buildData.sh
    
    # 4. Create an incremental git commit for this family
    echo "💾 Creating git checkpoint..."
    git add ../
    git commit -m "feat: import remaining gaps for family $family + quality fixes"
  else
    echo "❌ Failed to import $family. Skipping to next..."
  fi
done

GLOBAL_DURATION=$(( SECONDS - GLOBAL_START ))
GLOBAL_MINS=$(( GLOBAL_DURATION / 60 ))
GLOBAL_SECS=$(( GLOBAL_DURATION % 60 ))
echo ""
echo "=== Batch Import Completed in ${GLOBAL_MINS}m ${GLOBAL_SECS}s! ==="
