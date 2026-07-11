# Non-vertebrate enrichment plan

*Created 11/07/2026*

## Background

After the July 2026 Wikipedia enrichment pass across all 6 vertebrate classes, Animalia enrichment sits at **49,791 / 529,298 (9.4%)**. The 0% classes (Gastropoda 99k, Bivalvia 35k, Nematoda 15k, etc.) are genuinely source-limited — no Wikipedia articles, no POWO/WCVP data, and no GBIF descriptive content exists.

GBIF caches for invertebrate classes are all empty/stale (2 species each — failed imports). No Insecta or Arachnida cache exists.

## Phase 1: Structural completeness (import names, accept minimal descriptions)

**Goal:** Import species names from GBIF for the two largest partially-enriched classes (Insecta, Arachnida) to achieve structural completeness. Descriptions stay minimal/boilerplate.

**Steps:**
1. Build proper GBIF caches for Insecta and Arachnida via `scripts/cacheGbifClass.ts`
   - Rate-limited (GBIF API), could take hours/days
   - Cache output: `portal/data/gbif-cache-insecta.json`, `portal/data/gbif-cache-arachnida.json`
2. Use `fillFamilyGap.ts` to import species names from rebuilt caches
   - Fills speciesCount targets for families that are currently under-populated
   - Descriptions will be minimal (GBIF provides taxonomy, not descriptions)
3. Rebuild both kingdoms: `sh scripts/buildData.sh` + `SN_KINGDOM=plantae sh scripts/buildData.sh`
4. Run `findGaps.ts` + `deep-scan.py` to verify
5. Commit: `Import Insecta + Arachnida species from rebuilt GBIF caches`

**Estimated impact:**
- Insecta: structural completeness (all families at speciesCount target)
- Arachnida: same
- No enrichment gain for most species (descriptions stay minimal)

**Status:** Not yet started.

## Phase 2a: Targeted enrichment for Insecta + Arachnida

**Goal:** Run Wikipedia enrichment pass on Insecta and Arachnida — the two classes with partial Wikipedia coverage and non-trivial existing enrichment.

**Steps:**
1. `npx tsx scripts/enrichFromWikipedia.ts --class insecta`
2. `sh scripts/buildData.sh` → commit
3. `npx tsx scripts/enrichFromWikipedia.ts --class arachnida`
4. `sh scripts/buildData.sh` → commit
5. Run `findGaps.ts` to measure improvement

**Estimated impact:**
- Insecta: 8.3% → ~12-15% (best case, depends on Wikipedia coverage for beetles/butterflies/hymenoptera)
- Arachnida: 17.2% → ~25% (best case, depends on spider coverage)

**Depends on:** Phase 1 (rebuilt caches for species names).

## Phase 3: Accept the ceiling

Everything else (Gastropoda, Bivalvia, Nematoda, Polychaeta, Bryozoa, Trematoda, etc.) stays at 0% enriched — genuinely source-limited. The portal is structurally complete (all families have appSlugs, themes, and species counts) even if descriptions are minimal.

## Remaining empty families

758 Animalia families have portalCount=0 and speciesCount=0. These are scaffolded (have appSlug + color theme) but hold zero species. They are concentrated in source-limited invertebrate groups. 237 Plantae families are similarly empty.
