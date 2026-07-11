# Coverage & Import Status

*Stats generated 11/07/2026 from `portal/data/kingdoms/{animalia,plantae}/unified-taxonomy.json` and `portal/data/gap-report.json`.*

## Current Portal State — Animalia

- **100,845 physical nodes** in the D3 taxonomy tree
- **492,377 compressed flat species** in genus-level `speciesList` arrays
- **593,222 total nodes represented** across the unified taxonomy
- **529,298 total species** tracked in the portal
- **5,071 families** across **75 classes** in **32 phyla** (all animal phyla)
- **49,791 species** enriched with real descriptions (9.4% of total)
- **5,071 / 5,071 families** are at or above their `speciesCount` target (100%)
- **GBIF caches** (`portal/data/gbif-cache-*.json[.gz]`): Aves, Mammalia, Reptilia, Amphibia, Elasmobranchii, Asteroidea, Echinoidea, Holothuroidea, Insecta, Arachnida, Actinopterygii, Cephalopoda, Anthozoa, Hydrozoa. Plus phylum scout: `gbif-scout-cnidaria.json`.

## Current Portal State — Plantae

- **43 classes**, **1,259 families** across all 7 plant phyla (657 in Tracheophyta / vascular plants)
- **1,022 of 1,259 families** populated (~435k species); **237 families** remain scaffolded with zero species (mostly Magnoliopsida, Polypodiopsida, and various algae)
- **~347,581 species** enriched (79.9% of total) — at POWO/WCVP source ceiling

## Enrichment ceiling

Enrichment means "has a real description (>20 chars, not boilerplate)." A Wikipedia pass was run across all 6 vertebrate classes (Aves, Actinopterygii, Mammalia, Reptilia, Amphibia, Chondrichthyes) in July 2026. It tagged 211 species as Wikipedia-sourced, but the enriched count was unchanged — those species already had descriptions from GBIF/POWO/other sources.

**Animalia: 49,791 / 529,298 (9.4%)** — effectively at its ceiling for description enrichment.

| Class | Species | Enriched | Rate | Notes |
|---|---|---|---|---|
| Insecta | 186,174 | 15,397 | 8.3% | Most species lack Wikipedia articles |
| Gastropoda | 99,563 | 0 | 0.0% | Source-limited — no descriptive data available |
| Bivalvia | 34,960 | 0 | 0.0% | Source-limited |
| Arachnida | 21,937 | 3,768 | 17.2% | Partial Wikipedia coverage |
| Anthozoa | 17,346 | 297 | 1.7% | Mostly corals — sparse descriptions |
| Chromadorea | 15,180 | 0 | 0.0% | Nematodes — source-limited |
| Polychaeta | 14,028 | 0 | 0.0% | Marine worms — source-limited |
| Aves | 11,754 | 1,888 | 16.1% | Best vertebrate coverage outside mammals |
| Actinopterygii | 10,885 | 3,687 | 33.9% | Fish — decent Wikipedia coverage |
| Reptilia | 8,121 | 5,488 | 67.6% | Strong Wikipedia coverage |
| Mammalia | 7,897 | 1,075 | 13.6% | Most species already had descriptions |
| Amphibia | 3,797 | 2,260 | 59.5% | Good coverage |
| Chondrichthyes | 1,187 | 140 | 11.8% | Sharks/rays — partial coverage |
| Demospongiae | 8,893 | 8,893 | 100.0% | Fully enriched from Wikipedia |

The 0% classes (Gastropoda, Bivalvia, Polychaeta, Nematoda, Bryozoa, Brachiopoda, etc.) are genuinely source-limited — no Wikipedia articles, no POWO/WCVP data, and no GBIF descriptive content exists for these taxa. See [non-vertebrate-enrichment-plan.md](./non-vertebrate-enrichment-plan.md) for Phase 1/2/3 plan to address Insecta and Arachnida.

**Plantae: ~347,581 / 435,114 (79.9%)** — at POWO/WCVP source ceiling. The ~20% unenriched is concentrated in mosses (Bryopsida 12k), liverworts (Jungermanniopsida 7k), hornworts, and algae — groups where neither POWO, WCVP, nor Wikipedia provide descriptions.

## Phylum Completion Snapshot

All 32 animal phyla are at 100% species-count completion. The plant kingdom has 1,022 of 1,259 families populated (~435k species); the remaining 237 families await species import — chiefly 48 Magnoliopsida (dicot) and 42 Polypodiopsida (fern) families, plus assorted red/green algae.

## Regenerating these stats

```bash
cd portal
sh scripts/buildData.sh                        # rebuild animal unified taxonomy
SN_KINGDOM=plantae sh scripts/buildData.sh    # rebuild plant unified taxonomy
npx tsx scripts/findGaps.ts                    # → portal/data/gap-report.json
SN_KINGDOM=plantae npx tsx scripts/findGaps.ts # → portal/data/gap-report-plantae.json
python3 ../scripts/deep-scan.py               # structural integrity check (both kingdoms)
```
