# Import Workflow and Scripts

This document covers the tools, caches, and procedures used to import, enrich, and maintain species data inside the Systema Naturae portal.

The scripts split across two folders:
- **`portal/scripts/`** — runs from `cd portal && npx tsx scripts/<name>.ts`, scoped to the portal data pipeline.
- **`scripts/`** (repo root) — runs from `npx tsx scripts/<name>.ts`, scoped to multi-class/Wikipedia/Wikidata bulk work.

---

## 0. The current pipeline: `services/importwrite` + split transform/import

This is the canonical path for importing a prepared dataset today — sections
1-2 below predate it and cover a different, still-valid use case (building a
*new* family from GBIF/Wikipedia rather than importing a *prepared checklist*
into existing families).

**The write path.** `services/importwrite` (Go) is the single writer for
`taxonomy/<kingdom>/.../<family>/src/data/<family>.json`. Importers POST
species to it over HTTP instead of writing files directly, so two importers
touching the same family — or the same species via two different families —
get one serialized merge decision instead of two independent edits that
later collide in a git merge. See `services/importwrite/README.md` for the
identity/merge rules and API. As of this commit it also **refuses to
silently create a file for a family that isn't registered** in
`portal/data/kingdom-config.json`'s taxonomy skeleton — a request naming an
unregistered slug gets back `422`/`404` with the family/kingdom named,
instead of writing an orphaned file nothing will ever build or graft
(`registry.go`). `portal/scripts/fetchSpeciesFromApi.ts` is wired to it via
`IMPORTWRITE_URL`; most per-machine importers (Steamie, Debbie, q-bert) are
not wired yet.

**The transform/import split.** For bulk checklist imports, one pass
*transforms* a source into our own intermediary record format
(`scripts/sources.py`'s `record_transformed()` — flat JSONL + a metadata
sidecar carrying the original download, org/dataset id, URL, timestamp, and
a UUID for the set) and writes it to a shared location on the external
volume, so the machine that ran the transform doesn't have to be the one
that applies it. A separate pass, `scripts/importTransformed.py`, reads that
sidecar back and does the actual apply (dry-run by default, `--apply` to
write). This is deliberately two steps so "did we parse this right" and "is
it safe to write" are reviewed independently, and so the transform can run
on whichever machine happens to have the source data staged.

**The careful-apply path for prepared archives.** `scripts/importColChecklist.py`
is the real importer for an already-downloaded checklist archive (ColDP,
DwC-A, EUNIS, etc. — see `colChecklist.py`/`coldp.py`/`dwca.py` for the shape
dispatch). It infers kingdom from the rank chain, then by family-name
lookup, and — as of the 2026-10-18 fix — reports `UNRESOLVED KINGDOM`
honestly instead of silently defaulting unresolved cases to animalia (a real
bug that had mis-flagged ~3,020 plant species as needing a new animal
family). `--kingdom <name>` overrides the inference when a source is known
in advance to be single-kingdom (e.g. LCVP is always plantae). Also dry-run
by default.

**Families it refuses.** When an importer encounters a family that doesn't
exist in `taxonomy.json`/`taxonomy-<kingdom>.json` yet, that's a taxonomy
decision (does this family exist at all), not a data decision (where does
this species go) — see `scripts/pendingFamilies.py`, which records it for
later triage rather than letting the importer invent one. `importwrite`'s
refusal above is the same decision enforced at the write layer too.

---

## 1. Single-family import (GBIF + Wikipedia REST)

### `portal/scripts/fetchSpeciesFromApi.ts`
Downloads authoritative GBIF data for a family, enriches it with Wikipedia REST API summaries (descriptions, common names, continents), and writes the result to `<class>/<order>/<appSlug>/src/data/<appSlug>.json`. Updates `taxonomy.json#speciesCount` to GBIF's count.

```bash
cd portal
npx tsx scripts/fetchSpeciesFromApi.ts <slug> [limit]
```

### `portal/scripts/importFamily.ts` — **RETIRED, do not run**
Used Ollama to generate descriptions and synthesise missing species for known
gaps. Retired 2026-10-17 by the repo's "No LLM-generated content" policy
(root `CLAUDE.md`) — no model may write taxa, names, or descriptions into
the tree. Kept on disk, with an in-file banner, for reference only.
`make import` / `make import-steamie` are dead ends that point here.

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
| `portal/scripts/importReport.ts` | Per-import summary (counts, sources, duration) |
| `portal/scripts/importSmallGaps.sh` | Batch script that loops over small `gap` values from `gap-report.json` |
| `portal/scripts/scheduleEnrichment.sh` | Cron-style wrapper that runs enrichment in batches |
| `portal/scripts/testBuild.ts` | Integration sanity test for the unified build |
| `scripts/enrich_*.py` | One-shot enrichment passes (`tier1`, `tier2`, `tier34`, `near_green`, `lap2`, `lap3*`, `final*`) — done, kept as historical reference, not meant to be re-run |
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

### Held-name lookups — `scripts/taxaserve.py`

**`scripts/taxaserve.py`** — an in-memory index of everything we already hold,
served over HTTP on port 9882. Fourteen scripts answer "do we hold this name?"
and each was answering it by re-reading 2.5GB of family JSON; this holds the
answer once (~44s to build, ~1.2GB resident) and serves it.

```bash
python3 scripts/taxaserve.py --port 9882
export TAXASERVE=http://127.0.0.1:9882
python3 scripts/sampleDatasetOverlap.py 1021 1022 1023   # 19.8s, was ~6 min
```

- `POST /held {"names":[…]}` → where each name is held (kingdom, family, genus).
  Returns *where*, not just whether, so a caller can see a wrong family rather
  than trusting a bare boolean.
- `POST /parse {"names":[…]}` → canonical form, served from the parse index
  rather than shelling out to GNparser.
- `GET /pending?scaffoldable=1` → the pending-family store.
- `POST /reload` after an `--apply`. Every response carries `indexed` and
  `treeMtime` so a caller can tell whether the index reflects the tree.

`canonicalNames._load()` and `sampleDatasetOverlap.py` use it when `TAXASERVE`
is set and fall back to reading the files when it is not. Full description,
including the two silent bugs found while measuring it (genus must not be read
from `lineage`; leading daggers must be stripped), in
[`taxaserve.md`](taxaserve.md).

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

---

## 10. Storing a name: `taxamatch.bare_name`

Every importer that reads a checklist needs the same thing — turn a source's
`scientificName` into the spelling we store, or decide it is not a binomial we
can store. That is `taxamatch.bare_name(name, parsed)` (and
`taxamatch.bare_binomial(name, parsed)` for the parts), and importers call it
rather than re-deriving it.

### The hybrid rule, and what it cost

GNparser does not read a hybrid the way the name is written. For
`Strelitzia × kewensis` it returns **genus `Strelitzia`, species `×`,
infraspecies `kewensis`**: the marker takes the species slot and the epithet is
demoted. So `if not species` — the obvious guard — never fires, because `'×'` is
a perfectly good truthy string, and the importer builds `Strelitzia ××`.

| | |
|---|---|
| In the tree before 2026-10-09 | **1,044** nodes named `Genus ××` — 676 from `importColChecklist.py`, 368 from the COL importers |
| Blast radius | one broken name **per genus**, not per species: the within-run dedup kept the first and dropped the rest, so every hybrid after the first in a genus was silently discarded |
| Cost on the run that exposed it | `importColStage2.py --kingdom Plantae` added **218** species with the bug and **850** without it |
| `bare_binomial` | treats an epithet that is only the marker (`×`, `x`) as *lost*, not *absent*, and recovers it from `infraspecies` or from the raw tokens. Returns `(None, None)` when there is genuinely no epithet (`Strelitzia ×`) |

Three importers carried the bug and all three now call the helper:
`importColBreadth.py`, `importColChecklist.py`, `importColStage2.py`.

**The 1,044 existing nodes are still broken.** They are one-per-genus placeholders
carrying a name that denotes no taxon, and repairing them means recovering the
epithet from the archive that supplied each one — see the open item below.

### Why the check has to run after every import

`verifyTree.py` is the gate, and it is the only thing that would have caught the
hybrid names as a *class* of defect. It did not, for the same reason
`dedupeSpeciesAcrossFamilies.py` exists: a wrong-but-well-formed name is
indistinguishable from a right one without consulting the source.

The sharper lesson is what a full-tree rewrite can do. Commit `9754ab2e81`
("Normalize species lineage case") left
`taxonomy/animalia/arthropoda/insecta/blattodea/nocticolidae/src/data/nocticolidae.json`
as a **0-byte file** — a whole family, 78 species, deleted in passing. Nothing
caught it: `git status` was clean, the build warned only about unrelated missing
files, and `verifyTree.py` died with a bare `JSONDecodeError` at character 0
rather than naming the file. Restored from `9754ab2e81^` on 2026-10-09.

Two cheap guards, both worth having before the next full-tree pass:

```bash
# 1. any family file that is empty or unparseable -- catches a truncated write
python3 - <<'PY'
import glob, json, os
for f in glob.glob('taxonomy/*/**/src/data/*.json', recursive=True):
    if os.path.getsize(f) == 0:
        print('EMPTY', f); continue
    try: json.load(open(f, encoding='utf-8'))
    except Exception as e: print('BAD', f, e)
PY
```

2. `verifyTree.py` should report the offending path when a family file fails to
parse, not raise out of `json.load`.

---

## 11. Queue-driven import pipeline (Macie → q-bert via importwrite)

The canonical path for bulk ChecklistBank imports since 2026-10-19 is a
**three-stage split pipeline** across two machines:

```
Macie (this host)                      q-bert (WSL2, importwrite host)
┌─────────────────┐                    ┌──────────────────┐
│ sourceQueue.json│  stage: downloaded │  importwrite     │
│                 │ ────────────────► │  :8089 (Go)      │
│ transform step  │ ────────────────► │  POST /genus     │
│ (transformCol-  │                    │  POST /flush     │
│ Checklist.py)   │                    │  per family      │
│ work/<slug>/    │                    └──────────────────┘
│ transformed.jsonl│                   ↑
│                 │                    │  single writer   │
│ import step     │                    │  for family JSON │
│ (importTrans-   │                    │  files           │
| formed.py)      │                    │                  │
│ IMPORTWRITE_URL │                    │                  │
│ =http://q-bert: │                    │                  │
│ 8089            │                    │                  │
└─────────────────┘                    └──────────────────┘
```

### Stage machine: `scripts/sourceQueue.py` / `data/source-queue/<key>.json`

Every tracked source has its own file, `data/source-queue/<key>.json`
(`checklistbank-<key>` for ChecklistBank sources) -- one file per source
since 2026-10-22, not a single `data/source-queue.json`: a process
holding a stale in-memory copy of the whole queue used to clobber every
other source's concurrent update when it saved its own. `stage` moves
through:

```
candidate → downloaded → triaging → triaged → queued → applying → applied
                                     ↑                                    ↑
                                  (dry run)                          (done)

declined / blocked / needs-rerun   (terminal / holding states)
```

`needs-rerun` carries its own `rerunCommand` (a JSON argv list set via
`sourceQueue.py set --stage needs-rerun --rerun-command '[...]'`) --
some sources need a different tool than the standard transform/apply
pipeline (TAXREF needed `importColStage2.py --kingdom`, once per
kingdom, not a plain re-run).

Every stage transition also appends one line to `data/pipeline-events.jsonl`
-- not the source of truth (each source's own file, including its
`history` list, is), but a flat chronological feed across *all* sources,
so "what happened across the whole pipeline, in order" doesn't mean
scanning 300+ files and interleaving their `history` entries by hand.

`scripts/sourceQueue.py` is the CLI for moving a source between stages:

```bash
python3 scripts/sourceQueue.py add   --key checklistbank-1020 \
    --title "Global Species Database of Odonata" --size 9028 --licence "cc by"
python3 scripts/sourceQueue.py set   --key checklistbank-1020 --stage downloaded
python3 scripts/sourceQueue.py set   --key checklistbank-1020 --stage applied \
    --added 351 --merged 3789 --families 117
python3 scripts/sourceQueue.py report   # grouped by stage, terminal
```

### Stage 1 — Transform (Macie)

`scripts/transformColChecklist.py <archive.zip> <work-slug> --apply`

Reads a downloaded ChecklistBank archive, routes each species into its
family using `importColChecklist.route_species()` (kingdom inference,
family matching, refusal detection), and writes a JSONL sidecar:

```
/Volumes/MacieExternal/sources/work/<work-slug>/transformed.jsonl
/Volumes/MacieExternal/sources/work/<work-slug>/transformed.meta.json
```

Each record has `kingdom`, `family` (appSlug), `genus` (name + optional
id/sourcedFrom/lineage), and `species` (full species node). Species whose
family has no data file on disk are skipped with a warning (found 2026-10-19
on WoRMS 2011, which routes single species into three unscaffolded families).

Species that would need a brand-new family are **refused** — dropped, not
placed, no `Incertae sedis` placeholder — and recorded in the pending-family
store via `scripts/pendingFamilies.py`.

### Stage 2 — Apply (Macie → q-bert)

`IMPORTWRITE_URL=http://q-bert:8089 python3 scripts/importTransformed.py <work-slug>`

Reads the transformed.jsonl sidecar, groups records by (family, genus),
POSTs each genus's species to importwrite's `/family/<slug>/species`,
then flushes each family immediately after its own genera are posted
(per-family flush, not end-of-run — this prevents idle eviction of small
families while a big one is still posting, which caused data loss on
2026-10-19).

importwrite responds per genus with `added` and `merged` species lists;
`importTransformed.py` appends a summary row to `data/import-log.jsonl`
and returns the aggregate counts.

### Stage 3 — Queue update

`sourceQueue.py set --key <slug> --stage applied --added N --merged M ...`

The source's `applied` block holds the result; `history` is append-only.

### Orchestrator: `scripts/pipelineOrchestrator.py`

The single entry point that drives the whole pipeline -- one process,
one log, owns every stage transition. Before 2026-10-22 this was two
independent, narrow daemons (`importQueueDriver.py` watching only
`downloaded`, `pendingFamilyWatcher.py` watching the pending-family
store directly and bypassing the stage machine entirely); nothing
watched `needs-rerun` at all, found when TAXREF sat there with no
process that would ever pick it up. Both daemons' logic is unchanged and
imported here, not duplicated.

```bash
# One pass (processes everything, then exits):
python3 scripts/pipelineOrchestrator.py

# Loop forever, polling every 60s between passes:
python3 scripts/pipelineOrchestrator.py --loop

# Run under caffeinate (macOS, holds lid open):
nohup caffeinate -dimsu python3 scripts/pipelineOrchestrator.py --loop \
    > /tmp/pipelineOrchestrator.log 2>&1 &
```

Each pass:
1. **Refill:** if fewer than 5 sources are at stage `downloaded`, triage up
   to 10 new open-licence ChecklistBank candidates via
   `scripts/triageNext.py --keys-only --limit 10`, download each archive
   with `scripts/fetchBatch.sh <key>`, register via
   `sourceQueue.py add ... --stage candidate`, then set to `downloaded`.
   `sourceQueue.py add` itself refuses to register a key the manifest
   already has a verdict for (found 2026-10-22: a bulk add that bypassed
   this re-queued six already-taken sources and GTDB, on hold by policy).
2. **Drain `downloaded`:** licence gate (NC → blocked, no archive work
   spent), then transform (stage 1) + apply via importwrite (stage 2),
   then mark `applied` with the summary stats.
3. **Drain `needs-rerun`:** run each source's stored `rerunCommand`
   verbatim; a source with none stored is left alone with a loud note
   every pass rather than guessed at.
4. **Pending-family sweep:** one cycle of `pendingFamilyWatcher.cycle()`
   (see §12 below).

Either daemon's own file still runs standalone for one-off debugging of
just that stage (`python3 scripts/importQueueDriver.py`, `python3
scripts/pendingFamilyWatcher.py`) -- but in production run the
orchestrator, not those two separately.

### Related scripts

| Script | Role |
|---|---|
| `scripts/sourceQueue.py` | Queue state: add / set / report; `data/source-queue/<key>.json` storage, `data/pipeline-events.jsonl` log |
| `scripts/triageNext.py` | List open-licence ChecklistBank datasets we don't hold |
| `scripts/fetchBatch.sh` | Download a ChecklistBank archive.zip to the sources volume |
| `scripts/transformColChecklist.py` | Transform archive → transformed.jsonl sidecar |
| `scripts/importTransformed.py` | Apply sidecar via importwrite (POST per genus, flush per family) |
| `scripts/importwriteClient.py` | Python HTTP client for importwrite wire contract |
| `scripts/importLogServer.py` | HTTP dashboard on :9883 serving import-log.jsonl + queue |
| `services/importwrite` | Go single-writer service on q-bert:8089 |
| `scripts/pendingFamilies.py` | Pending-family store for refused species |
| `scripts/importColStage2.py` | Scaffold+merge a source's families across kingdoms, for a `needs-rerun`-style second pass |

### Ports in use

| Port | Service | Host |
|---|---|---|
| 8089 | importwrite | q-bert |
| 9883 | importLogServer.py dashboard | macie |
| 9876 | progressd (gap-task tracking) | macie |

### Dashboard: `scripts/importLogServer.py` (port 9883)

A read-only HTTP dashboard — the human-friendly sibling of
`importLogView.py`'s terminal table, for watching a run of several
imports in a row without squinting at a monospace table. It reuses
`importLogView.py`'s row-loading and `problems()`/`notes()` logic
directly rather than re-deriving it, and reads `sourceQueue.py`'s store
live rather than embedding a hand-written queue list in the page (the
first version, 2026-10-19, hardcoded both the completed-today list and
the open-items list, and was already wrong by the time the next
candidate batch finished triaging).

```bash
python3 scripts/importLogServer.py                 # serve on :9883
python3 scripts/importLogServer.py --port 9883
open http://localhost:9883/

# Production, survives a lid-close (macOS):
nohup caffeinate -dimsu python3 scripts/importLogServer.py --port 9883 \
    > /tmp/importLogServer.log 2>&1 &
```

The page polls four endpoints every 3 seconds and re-renders in place —
nothing server-side is pushed, so a stale tab just needs a reload after
a long gap:

| Endpoint | Source | Renders |
|---|---|---|
| `/api/log` | `data/import-log.jsonl` via `importLogView.load_rows()` | Summary cards (runs, species added, offered, refused, flagged) + the per-run table, newest first. Each row's `issues` (refusal rate over 20% ceiling, or staged-but-added-zero) and `notes` (missed-families count) come from `importLogView.problems()`/`notes()` — the same two gate criteria `verifyTree.py`'s `check_import()` uses, not reinvented here. |
| `/api/queue` | `sourceQueue.read_store()` (`data/source-queue/<key>.json`) | "Up next" list (stages `candidate`…`needs-rerun`, active ones — `triaging`/`applying` — sorted first) and the collapsible "open items" list (`declined`/`blocked`). |
| `/api/driver` | `pgrep -f importQueueDriver.py` + queue's `downloaded` count | The driver badge (running/stopped) and the auto-refill detail line. Note: checks for `importQueueDriver.py` specifically — when the orchestrator (`pipelineOrchestrator.py`) is driving the pipeline instead (the production path since 2026-10-22), this badge reads **stopped** even though refilling is happening; it hasn't been updated to also check for the orchestrator. |
| `/api/pending` | `pendingFamilies.read_store()` + `held_families()` | The "missing families" panel (hidden when empty): total pending, species they'd add, how many are now scaffoldable vs. still genuinely absent, broken down by source. |

Rows whose `slugHint` looks like a ChecklistBank dataset key
(`checklistbank-<id>` or a bare numeric id) get a `publisher` field
resolved via `cb_publisher()` — one GET to
`api.checklistbank.org/dataset/<id>` for `contact.organisation` (falling
back to `creator[0].organisation`), cached in-process for 10 minutes so
the 3-second tick doesn't hammer the API. The same lookup decorates both
the run table (replacing a bare slug with a readable name) and the
queue panel's up-next/open rows.

The queue panel's footer is a static reminder of what's deliberately
*not* in this dashboard: the `pendingFamilies.py` worklist's
no-archive-recorded backlog, and the tree-wide audits logged in
`BACKLOG.md` (WoRMS name-quoting, historical `sourceIds` collisions) —
both cross-cutting rather than per-source, so they don't fit this
page's source-keyed model. See `docs/dataset-inbox.md` for that
narrative.

---

## 12. Pending-family watcher (close the loop after family creation)

The split pipeline (§11) refuses species whose family doesn't exist in the
taxonomy yet — they're recorded in the pending-family store
(`/Volumes/MacieExternal/sources/pending/families.jsonl`, symlinked at
`portal/data/pending-families.jsonl`) by `scripts/pendingFamilies.py add`.
`pendingFamilies.py report --scaffoldable` identifies which refused families
are now in the taxonomy (and have a data file on disk), grouped by archive
with the exact re-import command — but it doesn't run them. That's the
watcher's job.

`scripts/pendingFamilyWatcher.py`'s `cycle()` closes the loop, called
once per pass by `scripts/pipelineOrchestrator.py` (§11) in production --
run the file below standalone only for one-off debugging of just this
stage:

  1. Reads the pending-family store.
  2. Computes which family names the taxonomy now holds (`held_family_slugs()`)
     and which have a data file on disk (`family_data_files()`).
  3. Finds rows whose family is now "ready" (held + file exists) and outside
     the 24-hour re-import cooldown.
  4. Groups those rows by their recorded `archive` path.
  5. Runs `importColChecklist.py <archive> --apply` for each archive.
     Re-running is safe: already-held species are skipped by dedup, so only
     newly-placeable species get added.
  6. Marks every row from that archive with `reimportedAt` so the same
     archive isn't re-run every cycle while its families are still being
     scaffolded.

Standalone usage (debugging only -- the orchestrator is the production path):
```bash
# One cycle, then exit:
python3 scripts/pendingFamilyWatcher.py

# Loop forever, polling every 5 minutes:
python3 scripts/pendingFamilyWatcher.py --loop
```

First cycle results (2026-10-20): re-imported 4 archives with recorded
paths — checklistbank-2011 (+360 / 37,681 held, 21 families),
wikispecies (3 families), checklistbank-311726 (+216 / 1,322 held, 59
families), checklistbank-1113 (+5 / 7,680 held, 1 family). 861 families
with no archive recorded (pre-date the archive-tracking fix) were skipped.

### Related scripts (added)

| Script | Role |
|---|---|
| `scripts/pendingFamilies.py` | Pending-family store: seed / add / report |
| `scripts/pendingFamilyWatcher.py` | Watches store, re-runs imports when families become ready; `cycle()` called by the orchestrator |
| `scripts/pipelineOrchestrator.py` | §11 -- the production entry point that calls this + importQueueDriver.py each pass |


