# Next Import Batch Plan

Date: 2026-06-29
Current state: 165,138 species across 1,114 families in 19 classes (183,329 nodes)

## Tier 1 — Close small gaps (Aves, Reptilia, Mammalia, Actinopterygii)

~800 species spread across ~20 families. GBIC cache has data for all of them.

### Target families (sorted by gap size)

| Family | Class | Gap | Priority |
|---|---|---|---|
| Rallidae | Aves | 86 | 1 |
| Laridae | Aves | 54 | 2 |
| Rhinolophidae | Mammalia | 48 | 3 |
| Turdidae | Aves | 21 | 4 |
| Tityridae | Aves | 17 | 5 |
| Vangidae | Aves | 12 | 6 |
| Caprimulgidae | Aves | 7 | 7 |
| Paradoxornithidae | Aves | 7 | 8 |
| Cacatuidae | Aves | 4 | 9 |
| Artamidae | Aves | 5 | 10 |
| Cinclosomatidae | Aves | 2 | 11 |
| Ommastrephidae | Cephalopoda | 2 | 12 |
| Alcippeidae | Aves | 1 | 13 |
| Chloropseidae | Aves | 1 | 14 |
| Pteroclidae | Aves | 1 | 15 |
| Architeuthidae | Cephalopoda | 1 | 16 |
| Others (reptiles, fish) | various | ~170 | 17 |

**Tool:** `portal/scripts/fillFamilyGap.ts`
**Distribution:** Split across Steamie, Biggie, Debbie, and local Ollama hosts

## Tier 2 — Post-batch

After each tier:
1. Rebuild: `cd portal && sh scripts/buildData.sh`
2. Regenerate reports: `findGaps.ts` → `reportPhyla.ts` → `generateGapTasks.ts` → `buildImportLog.ts`
3. Send progress to phylumProgressd / ocd MCP
4. Update `species-news.json`

## Progress tracking

Use `phylumProgressd.ts` directly if ocd MCP isn't available:
```bash
npx tsx scripts/phylumProgressd.ts --id <batch_id> --label "<label>" --pct <pct> --msg "<msg>" [--done]
```

## Deferred

The following work is on hold until explicitly brought back.

### Insecta (Chrysomelidae + full class)

~33,690 species gap — the largest remaining by far.

**Approach (when resumed):**
1. Run `scripts/scoutPhylum.ts` for Insecta to map orders/families from GBIF
2. Then `scripts/bootstrapClass.ts` for Coleoptera (the order containing Chrysomelidae)
3. Import via `scripts/importClass.ts`
4. Fall back to offline Wikipedia SQLite pipeline for enrichment

**Note:** Likely requires phased import (break into subfamilies/tribes).
