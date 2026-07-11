# Coverage & Import Status

*Stats generated 11/07/2026 from `portal/data/kingdoms/{animalia,plantae}/unified-taxonomy.json` and `portal/data/gap-report.json`.*

## Current Portal State — Animalia

- **100,845 physical nodes** in the D3 taxonomy tree
- **492,377 compressed flat species** in genus-level `speciesList` arrays
- **593,222 total nodes represented** across the unified taxonomy
- **529,298 total species** tracked in the portal
- **5,071 families** across **75 classes** in **32 phyla** (all animal phyla)
- **49,804 species** enriched with real descriptions (9.4% of total)
- **5,071 / 5,071 families** are at or above their `speciesCount` target (100%)
- **GBIF caches** (`portal/data/gbif-cache-*.json[.gz]`): Aves, Mammalia, Reptilia, Amphibia, Elasmobranchii, Asteroidea, Echinoidea, Holothuroidea, Insecta, Arachnida, Actinopterygii, Cephalopoda, Anthozoa, Hydrozoa. Plus phylum scout: `gbif-scout-cnidaria.json`.

## Current Portal State — Plantae

- **43 classes**, **1,259 families** across all 7 plant phyla (657 in Tracheophyta / vascular plants)
- **1,022 of 1,259 families** populated (~435k species); **237 families** remain scaffolded with zero species (mostly Magnoliopsida, Polypodiopsida, and various algae)
- **~347,581 species** enriched (79.9% of total) — at POWO/WCVP source ceiling

## Enrichment ceiling

Enrichment means "has a real description (>20 chars, not boilerplate)." A Wikipedia pass was run across all 6 vertebrate classes (Aves, Actinopterygii, Mammalia, Reptilia, Amphibia, Chondrichthyes) in July 2026. It tagged 211 species as Wikipedia-sourced, but the enriched count was unchanged — those species already had descriptions from GBIF/POWO/other sources. A follow-up pass on Insecta (213 families, 170k species) and Arachnida (11 families, 18k species) in July 2026 yielded only 13 new enrichments total, confirming the ceiling is real for all Animalia classes.

**Animalia: 49,791 / 529,298 (9.4%)** — effectively at its ceiling for description enrichment.

| Class | Species | Enriched | Rate | Notes |
|---|---|---|---|---|
| Insecta | 186,174 | 15,410 | 8.3% | Ceiling confirmed — 13 new from Wikipedia pass |
| Gastropoda | 99,563 | 0 | 0.0% | Source-limited — no descriptive data available |
| Bivalvia | 34,960 | 0 | 0.0% | Source-limited |
| Arachnida | 21,937 | 3,768 | 17.2% | Ceiling confirmed — 0 new from Wikipedia pass |
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

The 0% classes (Gastropoda, Bivalvia, Polychaeta, Nematoda, Bryozoa, Brachiopoda, etc.) are genuinely source-limited — no Wikipedia articles, no POWO/WCVP data, and no GBIF descriptive content exists for these taxa. The Wikipedia enrichment ceiling has been confirmed for all Animalia classes (see [non-vertebrate-enrichment-plan.md](./non-vertebrate-enrichment-plan.md)).

**Plantae: ~347,581 / 435,114 (79.9%)** — at POWO/WCVP source ceiling. The ~20% unenriched is concentrated in mosses (Bryopsida 12k), liverworts (Jungermanniopsida 7k), hornworts, and algae — groups where neither POWO, WCVP, nor Wikipedia provide descriptions.

## Phylum Completion Snapshot

All 32 animal phyla are at 100% species-count completion. The plant kingdom has 1,022 of 1,259 families populated (~435k species); the remaining 237 families await species import — chiefly 48 Magnoliopsida (dicot) and 42 Polypodiopsida (fern) families, plus assorted red/green algae.

## Description sources evaluated

Species descriptions are only ever populated from sources that yield real,
encyclopedic prose. Fabricated/boilerplate text is never written (see the
July 2026 strip of ~591k template descriptions). Each `sourcedFrom` tag:

| Source | Scope | Status | Notes |
|--------|-------|--------|-------|
| `wikipedia` | all kingdoms | **Primary.** ~132k species | Switched from the rate-limited live REST API to the **offline full-Wikipedia SQLite dump** (`/Volumes/WikiDump/wiki-pages.sqlite`, `pages.title→extract`) via `enrichFromWikipediaDB.ts`. No network/rate limit; a full `--all` pass enriches in ~1h and has *better* coverage than the API (no 404/429 losses). Idempotent — only fills empty descriptions. |
| `powo` / `wcvp` | plants | Authoritative botanical. ~250k | Native-range/lifeform summaries via `tools/powo_enrich.py`. **At ceiling:** a July 2026 re-run on the 19,287 empty flowering-plant/monocot species with cached GBIF keys yielded only 75 (0.39%) — the rest had no IPNI match or no reconstructable POWO fields. |
| `gbif` (descriptions) | animals | **Evaluated and rejected for gap-filling.** | See below. |
| `websearch`, `nzpcn` | manual | 65 + 1 | One-off hand-curated entries. |

### GBIF species descriptions — evaluated, not used for gap-filling

GBIF's `/species/{key}/descriptions` endpoint was assessed as a fallback for the
~470k empty (obscure, mostly invertebrate) animal species. A dedicated,
quality-gated importer exists — **`portal/scripts/enrichFromGbifDescriptions.ts`**
(English-only; uses cached family GBIF keys for fast enumeration; strict gate
rejecting specimen-catalog codes, type-description jargon, `Description/Remarks/
Holotype/…` prefixes, and non-Latin script).

Testing showed it is **not a viable quality source for our remaining gaps**:

- **Cephalopoda** (1,898 empty): 2/1,898 passed the strict gate (0.1%), and even
  those were poor ("(Figure 5 C) was collected, but the tentacles were in poor
  condition…").
- **Echinoidea** (living, 100 empty): 1/100, a data fragment ("Global maximum
  size. Maximum test diameter 80 mm.").

**Why:** GBIF description records for obscure taxa come from taxonomic treatment
banks (Plazi) and OCR'd morphological monographs — specimen/holotype descriptions,
not encyclopedic prose. Species with clean prose are already Wikipedia-covered
(and skipped as non-empty). Net yield over Wikipedia is ~0.1% at marginal quality,
so it is **kept as available tooling but intentionally not run broadly** —
empty is preferred over specimen fragments. Wikipedia (offline dump) is the
practical ceiling for animal descriptions.

## Regenerating these stats

```bash
cd portal
sh scripts/buildData.sh                        # rebuild animal unified taxonomy
SN_KINGDOM=plantae sh scripts/buildData.sh    # rebuild plant unified taxonomy
npx tsx scripts/findGaps.ts                    # → portal/data/gap-report.json
SN_KINGDOM=plantae npx tsx scripts/findGaps.ts # → portal/data/gap-report-plantae.json
python3 ../scripts/deep-scan.py               # structural integrity check (both kingdoms)
```
