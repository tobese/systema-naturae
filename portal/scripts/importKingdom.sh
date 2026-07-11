#!/bin/bash
# importKingdom.sh — end-to-end population of an already-scaffolded kingdom.
#
# Given data/taxonomy-<kingdom>.json (built by scaffoldKingdomTaxonomy.ts) and a
# registered kingdom-config entry, this:
#   1. GBIF-caches every class (cacheGbifData.ts)
#   2. imports every family from cache (fetchSpeciesFromApi.ts, NO_WIKI, NO_BUILD)
#   3. enriches descriptions from the offline Wikipedia DB (enrichFromWikipediaDB.ts)
# Publishes progress to progressd (session import-<kingdom>-<date>).
#
# It does NOT build or commit — do those after (build once, review, commit).
#
# Usage:  sh scripts/importKingdom.sh <kingdom>
#   e.g.  sh scripts/importKingdom.sh protozoa
set -u

KINGDOM="${1:?usage: importKingdom.sh <kingdom>}"
PORTAL="$(cd "$(dirname "$0")/.." && pwd)"
TAX="$PORTAL/data/taxonomy-${KINGDOM}.json"
[ -f "$TAX" ] || { echo "❌ $TAX not found — scaffold the kingdom first"; exit 1; }

SID="import-${KINGDOM}-$(date +%Y-%m-%d)"
PURL="http://localhost:9876/api/sessions/$SID/progress"
LOG="/tmp/import-${KINGDOM}.log"
export TMPDIR=/Volumes/MacieExternal/tmp; [ -d "$TMPDIR" ] || export TMPDIR=/tmp
: > "$LOG"

# Derive class names (for GBIF cache, smallest-first), class dirs (lowercased,
# for enrichment) and family appSlugs (for import) from the taxonomy.
python3 - "$TAX" > /tmp/${KINGDOM}-lists.tmp <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
classes = []   # (name, species)
dirs = set()
fams = []
for ph in d.get("children", []):
    for cl in ph.get("children", []):
        sp = 0
        def cnt(n):
            global sp
            if n["rank"] == "FAMILY": sp += n.get("speciesCount", 0)
            for c in n.get("children", []): cnt(c)
        cnt(cl)
        classes.append((cl["name"], sp)); dirs.add(cl["name"].lower())
        def col(n):
            if n["rank"] == "FAMILY": fams.append(n["appSlug"])
            for c in n.get("children", []): col(c)
        col(cl)
classes.sort(key=lambda x: x[1])
print("CLASSES\t" + "\t".join(c for c, _ in classes))
print("DIRS\t" + "\t".join(sorted(dirs)))
print("FAMS\t" + "\t".join(fams))
PY

CLASSES=$(grep '^CLASSES' /tmp/${KINGDOM}-lists.tmp | cut -f2-)
DIRS=$(grep '^DIRS' /tmp/${KINGDOM}-lists.tmp | cut -f2-)
FAMS=$(grep '^FAMS' /tmp/${KINGDOM}-lists.tmp | cut -f2-)
NCLS=$(echo "$CLASSES" | tr '\t' '\n' | grep -c .)
NFAM=$(echo "$FAMS" | tr '\t' '\n' | grep -c .)

log(){ echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; echo "$*"; }
prog(){ curl -s -X POST "$PURL" -H "Content-Type: application/json" -d "$(jq -n --arg m "$1" --argjson p "$2" '{message:$m,p:$p}')" -o /dev/null 2>/dev/null; }

curl -s -X POST "http://localhost:9876/api/sessions" -H "Content-Type: application/json" -d "{\"id\":\"$SID\"}" -o /dev/null 2>/dev/null
prog "Import $KINGDOM: $NCLS classes, $NFAM families" 0
log "########## IMPORT $KINGDOM START ($NCLS classes, $NFAM families) ##########"

# Phase 1: GBIF cache
i=0
for cls in $CLASSES; do
  i=$((i+1)); log "CACHE $cls ($i/$NCLS)"
  (cd "$PORTAL" && npx tsx scripts/cacheGbifData.ts "$cls" >>"$LOG" 2>&1) || log "  cache $cls FAILED"
  prog "GBIF cache $i/$NCLS ($cls)" $(( i*10/NCLS ))
done
log "=== caching done ==="

# Phase 2: import families (no wiki, no per-family build)
j=0
for slug in $FAMS; do
  j=$((j+1))
  out=$(cd "$PORTAL" && NO_WIKI=1 NO_BUILD=1 SN_KINGDOM="$KINGDOM" npx tsx scripts/fetchSpeciesFromApi.ts "$slug" 2>&1)
  n=$(echo "$out" | grep -oE 'Wrote [0-9]+ species' | grep -oE '[0-9]+'); [ -z "$n" ] && n=0
  log "IMPORT $slug ($j/$NFAM) -> $n species"
  if [ $((j % 25)) -eq 0 ] || [ "$j" -eq "$NFAM" ]; then prog "Import $j/$NFAM families" $(( 10 + j*60/NFAM )); fi
done
log "=== import done ==="

# Phase 3: local-DB Wikipedia enrichment (per class dir)
k=0; total=0
for dir in $DIRS; do
  k=$((k+1))
  out=$(cd "$PORTAL" && npx tsx scripts/enrichFromWikipediaDB.ts --class "$dir" 2>&1)
  n=$(echo "$out" | grep -oE '[0-9]+ species enriched' | tail -1 | grep -oE '[0-9]+'); [ -z "$n" ] && n=0
  total=$((total+n)); log "ENRICH $dir ($k/$NCLS) -> $n (cum $total)"
  prog "Enrich $k/$NCLS ($dir): cum $total" $(( 70 + k*30/NCLS ))
done
log "=== enrich done: $total enriched ==="
curl -s -X POST "$PURL" -H "Content-Type: application/json" -d "$(jq -n --arg m "$KINGDOM import+enrich complete: $total enriched. Ready to build+commit." '{message:$m,p:100,d:true}')" -o /dev/null 2>/dev/null
log "########## IMPORT $KINGDOM DONE ($total enriched) ##########"
