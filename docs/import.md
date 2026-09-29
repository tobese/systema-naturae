# Import Workflow and Scripts

This document covers the tools, caches, and procedures used to import, enrich, and maintain species data inside the Systema Naturae portal.

The scripts split across two folders:
- **`portal/scripts/`** — runs from `cd portal && npx tsx scripts/<name>.ts`, scoped to the portal data pipeline.
- **`scripts/`** (repo root) — runs from `npx tsx scripts/<name>.ts`, scoped to multi-class/Wikipedia/Wikidata bulk work.

---

## 1. Single-family import (GBIF + Wikipedia REST)

### `portal/scripts/fetchSpeciesFromApi.ts`
Downloads authoritative GBIF data for a family, enriches it with Wikipedia REST API summaries (descriptions, common names, continents), and writes the result to `<class>/<order>/<appSlug>/src/data/<appSlug>.json`. Updates `taxonomy.json#speciesCount` to GBIF's count.

```bash
cd portal
npx tsx scripts/fetchSpeciesFromApi.ts <slug> [limit]
```

### `portal/scripts/importFamily.ts` — LLM gap fill
Uses Ollama to generate descriptions and synthesise missing species for known gaps.

```bash
cd portal
OLLAMA_MODEL=qwen2.5:7b npx tsx scripts/importFamily.ts <slug> [count]
```

Environment:
- `OLLAMA_HOST` — point at `localhost`, `steamie.taile27c11.ts.net`, `100.95.246.65`, or `100.101.65.92` as needed.
- `OLLAMA_MODEL` — model to use; `qwen2.5-coder:3b` is the current Biggie default.
- `OLLAMA_NUM_GPU` — set to `0` for the Biggie import path when using CPU-only generation.

### `portal/scripts/importPapilionidaeWikipedia.ts`
Template for a **Wikipedia-first** importer that scans GBIF, only keeps species with a Wikipedia article, and enriches inline. Copy + adapt per family.

---

## 2. Whole-class & phylum imports (root `scripts/`)

### `scripts/scoutPhylum.ts`
Discovers all orders and families inside a phylum via GBIF, with species counts. Writes `portal/data/gbif-scout-<phylum>.json`.

```bash
npx tsx scripts/scoutPhylum.ts <phylumName>
```

### `scripts/cacheGbifClass.ts` / `portal/scripts/cacheGbifData.ts`
Pulls every species GBIF knows for a class into `portal/data/gbif-cache-<class>.json[.gz]`. Run once per class, then reuse for imports.

```bash
cd portal && npx tsx scripts/cacheGbifData.ts <ClassName>
# OR (root variant, slightly different output)
npx tsx scripts/cacheGbifClass.ts <ClassName>
```

### `scripts/bootstrapClass.ts`
Scaffolds an entire class from its GBIF cache: creates the `<class>/<order>/<family>/` folders, family JSON stubs, taxonomy entries, and seeds color themes via `gen_themes.py`.

```bash
npx tsx scripts/bootstrapClass.ts <ClassName> <GbifClassName> <CLASS_ID> <gbifKey> <speciesCount>
# Example:
npx tsx scripts/bootstrapClass.ts Hydrozoa Hydrozoa HYDROZOA 205 4545
```

### `scripts/importClass.ts`
One-pass importer for every family in a class. Reads the GBIF cache and writes all family JSONs.

```bash
npx tsx scripts/importClass.ts <ClassName> <gbifKey> <CLASS_ID>
# Example (Anthozoa):
npx tsx scripts/importClass.ts Anthozoa 206 ANTHOZOA
```

### `scripts/generateFromCache.ts`
Regenerates a family JSON from the cached GBIF + Wikipedia data without re-fetching anything. Useful after a sanity fix.

### `scripts/importHydrozoa.ts`
Class-specific importer kept as a template for new classes.

---

## 3. Offline Wikipedia pipeline (Macie host only)

Local copy of the 2026-06-01 enwiki dump lives on external volumes — see global `~/.config/opencode/AGENTS.md` for paths.

### `scripts/buildWikipediaDb.py`
Parses `/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream.xml.bz2` into a single SQLite DB:

```bash
python3 scripts/buildWikipediaDb.py
# Live progress:
python3 scripts/tailWikiDbProgress.py
# Auto-resume when the volume is mounted:
sh scripts/watchWikipediaDump.sh
```

Output: `/Volumes/WikiDump/wiki-pages.sqlite` (title → wikitext + parsed `infobox_json`).

### `scripts/enrichFromWikipedia.ts` (root, SQLite-aware)
Pulls descriptions/continents/IUCN from the SQLite DB. Falls back to the Wikipedia REST API for species missing from the dump. Sets `sourcedFrom: "wikipedia"` on every species it touches.

```bash
npx tsx scripts/enrichFromWikipedia.ts --class <class>
# or all-at-once via Makefile:
make enrich   # loops 11 classes, builds + commits + pushes after each
```

`portal/scripts/enrichFromWikipedia.ts` is the **REST-API-only** sibling — use it when the dump volume is not mounted (any non-Macie host).

### `scripts/mergeWikiInfoboxes.ts`
Folds infobox fields (image, range_map, IUCN status) from the SQLite DB into `shared/data/wiki-images.json`. Conflict policy: prefer existing Wikidata-cached values; only fill MISSING fields.

```bash
npx tsx scripts/mergeWikiInfoboxes.ts             # full run
npx tsx scripts/mergeWikiInfoboxes.ts --dry-run   # report only
```

### `scripts/fetchWikidataImages.ts`
Populates `shared/data/wiki-images.json` from Wikidata SPARQL — separate from the Wikipedia pipeline above.

---

## 4. Gap reporting

After every significant import, regenerate the gap files:

```bash
cd portal
sh scripts/buildData.sh                  # rebuild unified-taxonomy.json
npx tsx scripts/findGaps.ts              # → portal/data/gap-report.json
npx tsx scripts/reportPhyla.ts           # → docs/gap-tasks-phyla.md
npx tsx scripts/generateGapTasks.ts      # → docs/gap-tasks.md
```

`reportPhyla.ts` and `generateGapTasks.ts` also POST progress to `http://localhost:9876` if `phylumProgressd.ts` is running:

```bash
cd portal && npx tsx scripts/phylumProgressd.ts   # daemon, port 9876
```

The daemon stores each POST so progress is graphable over time.

---

## 5. GBIF cache reference

Caches live in `portal/data/`, compressed when large:

| File | Class / Phylum |
|---|---|
| `gbif-cache-aves.json.gz` | Birds |
| `gbif-cache-mammalia.json.gz` | Mammals |
| `gbif-cache-reptilia.json.gz` | Reptiles |
| `gbif-cache-amphibia.json.gz` | Amphibians |
| `gbif-cache-actinopterygii.json[.gz]` | Ray-finned fish |
| `gbif-cache-elasmobranchii.json.gz` | Sharks & rays |
| `gbif-cache-cephalopoda.json.gz` | Squids, octopuses |
| `gbif-cache-arachnida.json.gz` | Arachnids |
| `gbif-cache-asteroidea.json.gz` | Starfish |
| `gbif-cache-echinoidea.json.gz` | Sea urchins |
| `gbif-cache-holothuroidea.json.gz` | Sea cucumbers |
| `gbif-cache-insecta-old.json.gz` | Insects (legacy snapshot) |
| `gbif-cache-anthozoa.json` | Corals, anemones |
| `gbif-cache-hydrozoa.json` | Hydrozoans |
| `gbif-scout-cnidaria.json` | Cnidaria phylum-level scout |

To (re)build a cache:

```bash
cd portal
npx tsx scripts/cacheGbifData.ts <ClassName>
```

---

## 6. Secondary helpers

| Script | Purpose |
|---|---|
| `portal/scripts/scanInsectWikipediaCoverage.ts` | Estimate Wikipedia coverage density for insect families before deciding import strategy |
| `portal/scripts/importReport.ts` | Per-import summary (counts, sources, duration) |
| `portal/scripts/importSmallGaps.sh` | Batch script that loops over small `gap` values from `gap-report.json` |
| `portal/scripts/scheduleEnrichment.sh` | Cron-style wrapper that runs enrichment in batches |
| `portal/scripts/testBuild.ts` | Integration sanity test for the unified build |
| `portal/scripts/mergeNamedAfter.ts`, `backupNamedAfter.ts` | Bulk-merge `namedAfter` (people species are named after); always back up first |
| `scripts/enrich_*.py` | One-shot enrichment passes (`tier1`, `tier2`, `tier34`, `near_green`, `lap2`, `lap3*`, `final*`) — keep as historical reference |
| `scripts/fix_*.py` | Sanity fixers (continents, duplicates, empty genera, lineage, subspecies, descriptions) — see CLAUDE.md "Fixing sanity issues" |
| `scripts/gen_themes.py` | Seed color themes for newly bootstrapped families |
| `scripts/add_bird_families.py`, `expand_bird_families.{py,js}` | IOC bird family backfill helpers |

---

## 7. Makefile shortcuts

```bash
make data            # rebuild unified-taxonomy.json
make dev             # cd portal && npm run dev
make build           # cd portal && npm run build
make typecheck       # cd portal && npm run typecheck
make lint            # cd portal && npm run lint
make import ARGS="<slug> 10"        # local Ollama (qwen2.5:3b)
make import-steamie ARGS="<slug> 10" # Steamie host, qwen2.5-coder:7b
make import-biggie ARGS="<slug> 10"  # Biggie host
make enrich          # loop Wikipedia enrichment over 11 classes, commit + push after each
make cache-gbif      # rebuild GBIF cache for the current class
```

---

## 8. Tiered plant enrichment (2026-07, Liliopsida + Magnoliopsida)

A newer, source-tiered pipeline used to fill descriptions on the two plant
classes. Each species records its provenance in `sourcedFrom` (values:
`wikipedia`, `gbif`, `powo`, `nzpcn`, `websearch`, or `none`). **For the licence
and attribution owed to each source, see `docs/data-sources-attribution.md`.**

Coverage after this work (plants): `none` 287,756 · `wikipedia` 75,360 ·
`gbif` 13,675 · `powo` 5,083 · `websearch` 46 · (no `sourcedFrom`, hybrid names) 9,156.

### Tier 1-2 — pull-queue (Wikipedia SQLite + GBIF)

**`scripts/enrichServe.ts`** — a Macie-side HTTP pull-queue (port 9881), modelled
on snedtankt's receive.py. Macie is the ONLY writer to the family JSONs; tailnet
workers lease batches, enrich locally, and submit results (no git/ssh on workers,
no write races). On start it runs a server-side Wikipedia SQLite pass, then a
server-side GBIF loop, and serves any remaining candidates to workers.

```bash
npx tsx scripts/enrichServe.ts --port 9881
```
- `POST /claim {worker,n}` → `{items:[{id,name,gbifKey}], lease_ms}` (204 if empty).
  `gbifKey` is included when cached (see Tier-2.5) so workers skip the match step.
- `POST /submit {worker,results:[{id,description,sourcedFrom}]}` → `{written}`.
- `GET /status` → counts. `GET /worker.py` / `/worker.mjs` → self-serve worker source.

Workers (stdlib only, no npm): `tools/enrich_worker.mjs`, `tools/enrich_worker.py`
(self-serve, GBIF API from the worker's own IP), and `tools/enrich_worker_gbif.mjs`
(Macie-local). All honour the server-provided `gbifKey`.

### Tier 2.5 — GBIF usageKey cache

**`tools/cache_gbif_keys.mjs`** — resolves every plant binomial to a GBIF
usageKey via `species/match` (129k unique binomials, 99.9% resolved). Shardable:

```bash
node tools/cache_gbif_keys.mjs --id 0 --total 4   # run 4 shards in parallel
```

**`tools/merge_gbif_keys.mjs`** — folds the flat key maps into
`portal/data/gbif-cache-{class}.json` as a top-level `usageKeys` map and stamps
`usageKey` onto per-species records. `enrichServe` loads `usageKeys` at startup
and hands out `gbifKey` in `/claim`, so the whole pipeline skips redundant match
calls. (The temp `gbif-keys-*.json` files are gitignored.)

### Tier 3 — POWO (Plants of the World Online)

**`tools/powo_enrich.py`** — bridges each `none` species that has a cached GBIF
key through **GBIF `/related` → IPNI LSID → POWO `/api/2/taxon`**, then
reconstructs a native-range / lifeform / climate summary and writes it with
`sourcedFrom="powo"`. Needs `cloudscraper` (POWO is behind Cloudflare); Macie-only.
Resumable via `powo-ipni-cache.json` + `powo-fields-cache.json` (gitignored).

```bash
python3 tools/powo_enrich.py --concurrency 10          # single balanced process
python3 tools/powo_enrich.py --id 0 --total 4          # or shard (per-shard caches)
python3 tools/powo_enrich.py --dry --limit 20          # test, no writes
```
Yield was ~5% of the 96,549 `none`-with-key candidates (the long tail is sparse:
~13% have no IPNI, ~81% have IPNI but no usable POWO fields). Also captures the
structured `distribution` (native range) field — see §9.

### Tier 4 — web search (targeted only)

For **near-complete families** (1-2 gap species), gap species were researched via
web search across authoritative sources (POWO, NZPCN, Flora of Australia/China,
ALA, IUCN, SANBI, herbaria, PBDB/IFPNI for fossils) and written with
`sourcedFrom="websearch"`. High per-hit value but heterogeneous and partly
non-open (see attribution doc) — used targeted, never bulk. Fossil-only taxa get
`fossil: true`.

Reports: [`enrich-report-2026-07-05.md`](./reports/enrich-report-2026-07-05.md),
[`enrich-family-report-2026-07-06.md`](./reports/enrich-family-report-2026-07-06.md),
[`web-enrich-report-2026-07-06.md`](./reports/web-enrich-report-2026-07-06.md).

---

## 9. Structured fields on species nodes

Beyond `description`, enrichment sets these on `TaxonNode` (`shared/src/types.ts`):

| Field | Meaning | Set by |
|---|---|---|
| `sourcedFrom` | provenance of the description | all enrichment tiers |
| `distribution` | native range text, e.g. "E. Bolivia to WC. Brazil" | POWO tier (from `taxonRemarks`) — 5,052 species |
| `enrichmentStatus` | family-level coverage: `full` / `partial` / `empty` | set on FAMILY nodes |
| `fossil` | known only from the fossil record (never seen alive) | web-search tier |
| `extinct` | recorded in human history but no longer exists | (reserved) |

Notes:
- `distribution` was deliberately kept as the curated native-range **string**, not
  POWO's raw TDWG `locations` codes (noisy, level-mixed, native+introduced
  conflated). See [distribution-notes-2026-07-06.md](./reports/distribution-notes-2026-07-06.md).
- Open item: the ~89k wiki/gbif species lack `distribution`; it can be backfilled
  cheaply via the cached IPNI bridge as additive metadata (no `sourcedFrom` change).
