# Documentation & Tooling Index

What's current, what's superseded, and what replaced it. `Last-verified` is
the date someone (or an audit) last actually checked the entry against the
code — reuse of this repo's own "measured, not applied" convention, not a
new one. An entry with no date was not individually re-checked; trust the
status column less for those until it is.

Status values: **active** (describes/implements the current workflow),
**superseded** (describes an older version of something that changed —
see Superseded-by), **obsolete** (no longer applicable at all), **historical**
(a dated snapshot, kept for the record, not meant to stay current),
**unclear** (not individually verified; bucketed by best guess).

## Docs

| Path | Purpose | Status | Superseded-by | Last-verified |
|---|---|---|---|---|
| `README.md` | Thin pointer into this index | active | — | 2026-10-18 |
| `import.md` | Import workflow & scripts | active | — | 2026-10-18 (§0 added, dead script refs removed) |
| `data-sources.md` | Dataset registry | active | — | 2026-10-18 |
| `data-sources-attribution.md` | Licence/attribution per source | active | — | 2026-10-18 |
| `dataset-inbox.md` | Triage queue for new dataset links | active | — | 2026-10-18 |
| `id-backfill-plan.md` | sourceIds backfill plan | active | — | 2026-10-18 |
| `taxaserve.md` | `taxaserve.py` held-names index | active | — | 2026-10-18 |
| `dedupeSpeciesAcrossFamilies.md` | Cross-family dedupe (script side) | unclear | partly `services/importwrite/crossfamily.go` (server side) | — |
| `archive-formats.md` | Checklist archive shape reference | unclear | — | — |
| `globalnames-triage.md` | GNparser triage notes | unclear | — | — |
| `bacteria-and-viruses.md` | Why those 2 kingdoms are on hold | active | — | — |
| `navigation.md` | Portal navigation architecture | active | — | — |
| `build-structure.md` | Skeleton/order-file/manifest build output | active | — | — |
| `deploy-debbie.md` | Docker deploy on Debbie | active | — | — |
| `worms-integration.md` | WoRMS candidate-family plan | active | — | — |
| `interaction-model.md` | Node click behavior by rank | active | — | — |
| `coverage.md`, `graph-ui.md`, `data-tiers.md`, `screen-handling.md`, `statistics-header.md`, `tooltip.md`, `wheel-of-nature.md`, `book-view.md` | Portal UI/architecture docs | active | — | — |
| `gap-tasks.md`, `gap-tasks-phyla.md` | Generated gap reports | active, but machine-written | — | regenerated on every `findGaps.ts`/`reportPhyla.ts` run |
| `drafts/mycobank-token-request.md` | Draft outreach note | active | — | — |
| `book-integration-plan.md`, `graph-vs-book-parity.md`, `wiki-on-debbie-plan.md`, `plantae-gaps.md`, `mollusca-expansion-plan.md`, `non-vertebrate-enrichment-plan.md`, `oddities.md`, `kingdoms-phyla-report.md`, `missing-phyla.md`, `phyla-gap-report.md`, `remaining-gaps-source-analysis.md`, `fossil-extinct-classification.md` | Jun-Jul dated plan/report snapshots | unclear | possibly the regenerated `gap-tasks*.md` | — |
| `insecta-scout.json` | GBIF scout data, misfiled as a doc | misfiled | should live under `portal/data/` with the other `gbif-scout-*.json` files | — |
| `reports/` (37 files, incl. 4 relocated `SESSION-*.md` logs) | Historical run reports & session logs | historical | — | 2026-10-18 (session logs moved in here) |
| `services/importwrite/README.md` | importwrite service docs | active | — | 2026-10-18 (registry check + merged-to-main noted) |
| `services/wikiserved/README.md` | wikiserved service docs | unclear | — | not cross-referenced from root `CLAUDE.md` yet |
| `experiments/book-view/README.md` | Book-view experiment | unclear | overlaps `docs/book-view.md` and the `prototype/book-view` branch — needs reconciling | — |
| `tasks/{steamie,q-bert,biggie}/README.md` | Per-host runbooks | active | — | — |

## Tooling

### Current canonical pipeline (see `import.md` §0)

| Path | Purpose | Status |
|---|---|---|
| `services/importwrite/*.go` | Single-writer HTTP service: cross-family identity, merge rules, family-registration check | active |
| `scripts/sources.py` | Dataset registry + `record_transformed()` (writes the transform-step sidecar) | active |
| `scripts/importTransformed.py` | Reads a transform sidecar back, applies it (dry-run / `--apply`) | active |
| `scripts/importColChecklist.py` | Real importer for a prepared archive (ColDP/DwC-A/EUNIS/…); kingdom inference + honest `UNRESOLVED KINGDOM` reporting | active |
| `scripts/colChecklist.py`, `coldp.py`, `dwca.py`, `txtree.py` | Shape dispatchers for the archive importer | active (`txtree.py` not yet wired into the dispatcher) |
| `scripts/pendingFamilies.py` | Pending-family worklist (taxonomy vs. data decisions) | active |
| `scripts/backfillSourceIds.py` | Backfills `sourceIds` on existing species | active |
| `scripts/mergeFamilyFiles.py` | New, uncommitted — not yet indexed in any doc | unclear, needs its own doc/README note |
| `scripts/dedupeSpeciesAcrossFamilies.py` | Cross-family dedupe (the script-side path, pre-dates `importwrite`'s server-side version) | active |
| `scripts/taxaserve.py` | In-memory held-names index, served over HTTP | active |
| `scripts/splitNameIndex.py`, `sanity_scan.py`, `verifyTree.py`, `tree.py` | Core tree integrity tooling | active |

### Portal pipeline (`portal/scripts/`)

| Path | Purpose | Status |
|---|---|---|
| `buildData.ts`/`.sh`, `buildAllKingdoms.sh` | Grafts family data into the tree per kingdom | active |
| `findGaps.ts`, `reportPhyla.ts`, `generateGapTasks.ts`, `phylumProgressd.ts` | Gap tracking + progress daemon | active |
| `testBuild.ts`, `testDataContract.ts`, `testFamilyPaths.ts` | Integration sanity tests | active |
| `fetchSpeciesFromApi.ts` | Single-family GBIF+Wikipedia importer; wired to `importwrite` via `IMPORTWRITE_URL` | active |
| `enrichFromWikipedia.ts`, `enrichHigherRanks.ts` | Wikipedia enrichment (REST API) | active |
| `cacheGbifData.ts`, `scaffoldKingdomTaxonomy.ts`, `fetchFromChecklistBank.ts` | Cache building / scaffolding / ChecklistBank fetch | active |
| `importReport.ts` | Per-import summary | active |
| `lib/familyPath.ts` | The one authority for family→path resolution | active |
| `lib/importActions.ts` | Bridges into the split transform/import pipeline | active, undocumented outside this index |
| `importFamily.ts` | **Retired** Ollama gap-fill importer | obsolete — in-file banner added 2026-10-18 |
| `testPlaywright.ts`, `profileTests.ts`, `findStuckSpecies.ts`, `classifyFossils.ts`, `stripBoilerplate.ts`, `genColorRegistry.ts`, `scaffoldFungiTaxonomy.ts`, `enrichFromGbifDescriptions.ts`, `enrichFromWikipediaDB.ts`, `aggregateSources.ts`, `importKingdom.sh`, `ensureBookData.sh` | Not cross-referenced anywhere | unclear |

### One-shot / archived (done, not meant to be re-run)

| Path | Status |
|---|---|
| `scripts/enrich_*.py` (18 files: tier1/2/34, near_green, lap2/3, final, …) | historical, superseded by the newer tiered pull-queue pipeline (`enrichServe.ts`) |
| `scripts/fix_duplicate_family_nodes.py`, `fix_duplicate_node_ids.py`, `fix_fixture_nodes.py`, `fix_flattened_provenance.py`, `fix_genus_split_duplicates.py`, `fix_misattached_descriptions.py`, `fix_thumb_captions.py` | historical one-shot fixers, not in CLAUDE.md's reusable 7-script table |

The CLAUDE.md "Fixing sanity issues" table (`fix_continents.py`,
`fix_duplicates.py`, `fix_empty_genera.py`, `fix_lineage.py`,
`fix_subspecies.py`, `fix_all_descriptions.py`,
`fix_redirect_descriptions.py`) stays reusable and is not in this bucket.

### importwrite service (`services/importwrite/*.go`)

All current, built this session; no obsolescence. See
`services/importwrite/README.md` for the API and merge rules.

---

## Known gaps in this index (not yet resolved)

- The dozen "unclear/likely stale" plan docs each need an individual
  "still open or already done?" pass — not done here; that's its own
  session, not a tooling-index chore.
- `docs/insecta-scout.json` should probably move to `portal/data/`
  alongside the other `gbif-scout-*.json` files — not moved yet since
  nothing currently reads it by path, so there's no urgency.
- `services/wikiserved/`, `experiments/book-view/`, and the
  `prototype/book-view` branch are not reconciled with each other or with
  root `CLAUDE.md`'s architecture tree.
