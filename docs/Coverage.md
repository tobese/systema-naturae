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

| Kingdom | Enriched | Total | Rate | Status |
|---|---|---|---|---|
| Animalia | 49,791 | 529,298 | 9.4% | Source-limited for invertebrates (Gastropoda 99k, Bivalvia 35k, etc. at 0%). Vertebrates have Wikipedia coverage where available. |
| Plantae | 347,581 | 435,114 | 79.9% | At ceiling — remaining 20% is mosses/liverworts/hornworts/algae with no POWO/WCVP/Wikipedia descriptions available. |

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
