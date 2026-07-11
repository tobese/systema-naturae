# Non-vertebrate enrichment plan

*Created 11/07/2026 · Updated 11/07/2026*

## Background

After the July 2026 Wikipedia enrichment pass across all 6 vertebrate classes, Animalia enrichment sits at **49,804 / 529,298 (9.4%)**. The 0% classes (Gastropoda 99k, Bivalvia 35k, Nematoda 15k, etc.) are genuinely source-limited — no Wikipedia articles, no POWO/WCVP data, no GBIF descriptive content exists.

GBIF caches for invertebrate classes are all empty/stale (2 species each — failed imports). No Insecta or Arachnida cache existed.

## Phase 1: Structural completeness (import names, accept minimal descriptions)

**Goal:** Build GBIF caches for Insecta and Arachnida to enable future enrichment passes.

**Status:** In progress — GBIF caches building in background.
- Arachnida: ~68% (PID from /tmp/gbif-arachnida.log)
- Insecta: ~8% (PID from /tmp/gbif-insecta.log) — will take ~8-10h total

**Note:** All Insecta/Arachnida families already have species data (213 and 11 families respectively). The caches are for future enrichment, not structural import.

## Phase 2a: Targeted enrichment for Insecta + Arachnida

**Goal:** Run Wikipedia enrichment pass on Insecta and Arachnida.

**Status:** COMPLETE — ceiling confirmed.

**Results (11/07/2026):**
- **Arachnida:** 0 new enrichments (18,181 species checked, all source-limited)
- **Insecta:** 13 new enrichments (170,778 species checked, 0.008% yield)
- Combined: 13 new enrichments out of 188,959 species checked

**Conclusion:** The Wikipedia enrichment ceiling is confirmed for all Animalia classes. No class can be significantly improved through Wikipedia alone.

## Phase 3: Accept the ceiling

Everything else (Gastropoda, Bivalvia, Nematoda, Polychaeta, Bryozoa, Trematoda, etc.) stays at 0% enriched — genuinely source-limited. The portal is structurally complete (all families have appSlugs, themes, and species counts) even if descriptions are minimal.

## Remaining empty families

758 Animalia families have portalCount=0 and speciesCount=0. These are scaffolded (have appSlug + color theme) but hold zero species. They are concentrated in source-limited invertebrate groups. 237 Plantae families are similarly empty.
