# Coverage & Import Status

*Stats generated 10/07/2026 from `portal/data/kingdoms/{animalia,plantae}/unified-taxonomy.json` and `portal/data/gap-report.json`.*

## Current Portal State — Animalia

- **100,622 physical nodes** in the D3 taxonomy tree
- **492,600 compressed flat species** in genus-level `speciesList` arrays
- **593,222 total nodes represented** across the unified taxonomy
- **529,298 total species** tracked in the portal
- **5,071 families** across **75 classes** in **32 phyla** (all animal phyla)
- **49,791 species** enriched from offline Wikipedia (`sourcedFrom: "wikipedia"`)
- **5,071 / 5,071 families** are at or above their `speciesCount` target (100%)
- **GBIF caches** (`portal/data/gbif-cache-*.json[.gz]`): Aves, Mammalia, Reptilia, Amphibia, Elasmobranchii, Asteroidea, Echinoidea, Holothuroidea, Insecta, Arachnida, Actinopterygii, Cephalopoda, Anthozoa, Hydrozoa. Plus phylum scout: `gbif-scout-cnidaria.json`.

## Current Portal State — Plantae

- **110,936 physical nodes** in the D3 taxonomy tree
- **297,785 compressed flat species** in genus-level `speciesList` arrays
- **408,721 total nodes represented** across the unified taxonomy
- **43 classes**, **1,267 families** in phylum Tracheophyta (vascular plants)
- **789 families** are scaffolded but have zero species (conifers, ferns, mosses, algae, etc.)

## Phylum Completion Snapshot

(See [`gap-tasks-phyla.md`](./gap-tasks-phyla.md) for the auto-generated full breakdown.)

All 32 animal phyla are at 100% completion. The plant kingdom has been bootstrapped with 478 of 1,267 families populated (~391k species), covering Magnoliopsida and Liliopsida; the remaining 789 families across ~40 non-flowering-plant classes await species import.

## Regenerating these stats

```bash
cd portal
sh scripts/buildData.sh                  # rebuild animal unified taxonomy
SN_KINGDOM=plantae sh scripts/buildData.sh  # rebuild plant unified taxonomy
npx tsx scripts/findGaps.ts              # → portal/data/gap-report.json
npx tsx scripts/reportPhyla.ts           # → docs/gap-tasks-phyla.md
npx tsx scripts/generateGapTasks.ts      # → docs/gap-tasks.md
```

## Regenerating these stats

```bash
cd portal
sh scripts/buildData.sh                  # rebuild unified-taxonomy.json
npx tsx scripts/findGaps.ts              # → portal/data/gap-report.json
npx tsx scripts/reportPhyla.ts           # → docs/gap-tasks-phyla.md
npx tsx scripts/generateGapTasks.ts      # → docs/gap-tasks.md
```
