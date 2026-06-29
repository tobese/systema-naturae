# Insecta Import Plan

Date: 2026-06-29
Current state: 8 families, 74,119 spp imported, 0 enriched (prior to enrichment run)

## Scope

GBIF estimates ~1,059,000 described insect species. The portal currently covers 8 families (74K spp) out of thousands of families across 43 orders.

## Coverage analysis

The offline Wikipedia SQLite DB has essentially zero insect species coverage. Most insects lack individual English Wikipedia articles. Therefore:

- **Families with Wikipedia coverage:** Enrich from SQLite, create full nodes
- **Families without Wikipedia coverage:** Add to taxonomy.json with species count only; no individual species nodes

## Strategy: Focus on families with enrichment potential

Only families that can be enriched from Wikipedia get full import treatment. All others get a `speciesCount` entry in taxonomy.json.

### Tier 1 — Chrysomelidae gap fill (highest priority)

33,690 species remain to reach the 35,000 target. We already have 1,310 spp in the portal. Chrysomelidae already has some Wikipedia enrichment (778 spp) via the earlier enrichment pass.

**Approach:**
1. Download fresh GBIF cache for Chrysomelidae specifically (not the whole class)
2. Check which missing species have Wikipedia coverage
3. Add missing species as full nodes if they have Wikipedia content
4. Update taxonomy.json speciesCount to match actual coverage

### Tier 2 — Family skeleton (count-only, no nodes)

For the remaining ~200+ families in the old GBIF cache (Coleoptera, Psocodea, Embioptera, Mecoptera), **do not create species nodes**. Instead:

1. Add family entries to taxonomy.json with `speciesCount`
2. No data files created (no `src/data/<family>.json`)
3. Build script handles these as "scaffold" families — shown in taxonomy tree but not expandable

This matches the user directive: families where species only have names don't need individual nodes.

### Tier 3 — Wikipedia-coverage families (if found)

If any new family is found to have English Wikipedia coverage (e.g., popular insect families like Coccinellidae, Lampyridae), create full nodes for those species.

**To check:** Run `scripts/enrichFromWikipedia.ts` on specific families after import to see enrichment yield.

## Execution sequence

1. Cache Chrysomelidae data from GBIF
2. Import missing Chrysomelidae species (filter for Wikipedia coverage)
3. Add remaining non-Chrysomelidae families to taxonomy.json as count-only
4. Rebuild and verify
5. Enrichment pass on any newly imported species
6. Update gap reports

## Status tracking

Track via `ocd_progressd` with id `insecta-import`.

## Deferred

- Full Coleoptera class import (134 families, 98K spp — no WP coverage)
- All other insect orders (Lepidoptera, Hymenoptera, Diptera, etc. — cache doesn't cover them yet)
