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
| `dedupeSpeciesAcrossFamilies.md` | Cross-family dedupe (script side) | active | — (complements `services/importwrite/crossfamily.go`'s live import-time matching with tree-wide maintenance-pass cleanup; `scripts/dedupeSpeciesAcrossFamilies.py` was touched again 2026-10-23, in HEAD `47232a3defe`) | 2026-10-23 |
| `archive-formats.md` | Checklist archive shape reference | active | — | 2026-10-23 (all 4 readers it documents — `colChecklist.py`/`coldp.py`/`dwca.py`/`txtree.py` — exist with recent commits; its 2026-10-04 archive-inventory numbers are a ~3-week-stale snapshot inside an otherwise-current doc) |
| `globalnames-triage.md` | GNparser/Taxamatch triage notes | active, mixed | ZooBank subsection superseded by `0751b77da3a` + `ba4e2be967665` (2026-10-10/11: ZooBank data *was* taken, via a DwC checklist route instead of the authorship-API sweep this doc argued against) | 2026-10-23 |
| `bacteria-and-viruses.md` | Why those 2 kingdoms are on hold | active | — | — |
| `navigation.md` | Portal navigation architecture | active | — | — |
| `build-structure.md` | Skeleton/order-file/manifest build output | active | — | — |
| `deploy-debbie.md` | Docker deploy on Debbie | active | — | — |
| `worms-integration.md` | WoRMS candidate-family plan | active | — | — |
| `interaction-model.md` | Node click behavior by rank | active | — | — |
| `coverage.md`, `graph-ui.md`, `data-tiers.md`, `screen-handling.md`, `statistics-header.md`, `tooltip.md`, `wheel-of-nature.md` | Portal UI/architecture docs | active | — | — |
| `gap-tasks.md`, `gap-tasks-phyla.md` | Generated gap reports | active, but machine-written | — | regenerated on every `findGaps.ts`/`reportPhyla.ts` run |
| `drafts/mycobank-token-request.md` | Draft outreach note | active | — | — |
| `book-integration-plan.md` | Book/portal integration plan | active | — | 2026-10-23 (self-declares "phases 1–4 done 2026-09-25, only book-mode right-panel design open" — verified: `BookView.tsx` absent, `BookReadingPane.tsx` present, matching the claimed Phase 4) |
| `book-view.md` | Pre-implementation book-view concept pitch (ASCII mockup, wishlist) | superseded | `experiments/book-view/README.md` (the real, current implementation doc — 436 lines vs. this one's 58, describes the shipped shell app) | 2026-10-23 |
| `graph-vs-book-parity.md` | Data-provenance parity audit | historical | `data-tiers.md` (2026-09-29, flagged at the top of this doc itself) | 2026-10-23 (findings resolved in-place with strikethroughs; remaining items are in `BACKLOG.md`, not here) |
| `wiki-on-debbie-plan.md` | Offline-wiki service rollout plan | active | — | 2026-10-23 (§1 `wikiserved` done & verified — `services/wikiserved/server.ts` exists, `portal/.env.local` sets `VITE_WIKI_SUMMARY_BASE`; §2 svwiki MediaWiki and §3 search remain genuinely open, not started) |
| `plantae-gaps.md` | Plantae empty-family gap analysis | superseded | current `gap-report-plantae.json` for the numbers (1,259→1,272 families, 237→228 empty); its "Next steps" (POWO/WFO unexplored) overtaken by the completed WCVP/Wikispecies round (`BACKLOG.md`, 2026-10-19) | 2026-10-23 (historical "why families are empty" framing still stands) |
| `mollusca-expansion-plan.md` | Mollusca class-coverage expansion plan | historical | — | 2026-10-23 (fully executed and exceeded: Gastropoda 957 families vs. plan's 634, Bivalvia 445 vs. 339, Cephalopoda 785 vs. 184, plus fossil-only classes the plan had excluded) |
| `non-vertebrate-enrichment-plan.md` | Non-vertebrate enrichment phases | historical | `worms-integration.md` | 2026-10-23 (concluded 2026-07-11 "accept the ceiling"; its 758 empty-family number fed directly into the WoRMS candidate list, which was then imported) |
| `oddities.md` | Standalone natural-history field-guide writeup | historical | — | 2026-10-23 (never wired into app code; not a plan with open/closed tasks, nothing to supersede) |
| `kingdoms-phyla-report.md` | Scouted-but-unscaffolded phyla report | obsolete | `gap-tasks-phyla.md` / `reportPhyla.ts` | 2026-10-23 (generated 2026-07-04; all 8 listed Animalia phyla and all 7 listed Plantae phyla now exist as `taxonomy/` directories) |
| `missing-phyla.md` | Animalia phylum-coverage snapshot | obsolete | `gap-tasks-phyla.md` / `reportPhyla.ts` | 2026-10-23 (dated 2026-06-28, claimed only 7 of 35 animalia phyla existed; all are present now, plus ~20 more) |
| `phyla-gap-report.md` | Cross-kingdom phylum gap snapshot | obsolete | `bacteria-and-viruses.md` + current `kingdom-config.json` | 2026-10-23 (dated 2026-07-04, claimed 4 kingdoms had zero data; all six are now built and the bacteria/viruses hold is a deliberate, separately-documented decision, not an open gap) |
| `remaining-gaps-source-analysis.md` | Per-family species-count gap snapshot | historical | `gap-report.json` / `gap-tasks.md` | 2026-10-23 (dated 2026-06-28; e.g. Chrysomelidae was 1,310/35,000, now 28,445; Hylidae was 766/1,000, now 1,479 — numbers moved on, current state lives in the regenerated reports) |
| `fossil-extinct-classification.md` | Fossil/extinct higher-rank classification pass | historical | — | 2026-10-23 (self-declared "complete," 2026-07-13; `classifyFossils.ts` still exists and is runnable, but this doc is a result record of one finished pass) |
| `portal/data/gbif-scout-insecta.json` | GBIF scout data | active | — | 2026-10-23 (moved out of `docs/` — was misfiled there — and renamed to match the `gbif-scout-<phylum>.json` convention) |
| `reports/` (37 files, incl. 4 relocated `SESSION-*.md` logs) | Historical run reports & session logs | historical | — | 2026-10-18 (session logs moved in here) |
| `services/importwrite/README.md` | importwrite service docs | active | — | 2026-10-18 (registry check + merged-to-main noted) |
| `services/wikiserved/README.md` | wikiserved service docs | active | — | 2026-10-23 (real running service on Debbie, port 9881, docker compose; wired into the build via `shared/src/lib/wikiSummary.ts`'s `VITE_WIKI_SUMMARY_BASE` switch; shares extraction logic with `scripts/enrichBreedsFromWikipedia.py`, which must stay in step) |
| `experiments/book-view/README.md` | Book-view shell-app implementation doc | active | — | 2026-10-23 (describes the shipped build step read by `ensureBookData.sh`; `portal/public/data/book/` confirmed live on disk; `prototype/book-view` branch is 0 commits ahead of `main` — fully merged, nothing left to reconcile) |
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

- Two stale local branches found while reconciling `experiments/book-view/`,
  safe to delete but not deleted here (that's the user's call): `prototype/book-view`
  (0 commits ahead of `main` — fully merged) and `fix/enrich-wikipedia-live-path`
  (1 unmerged commit from 2026-08-20, but the fix it carries — the
  `p.missing` falsy-string bug in `enrichFromWikipedia.ts` — already
  reached `main` independently through a different merge; this branch's
  own commit is dead weight).
- **New, found during this pass (2026-10-23): 356 families sit directly
  under `KINGDOM` in `taxonomy/animalia/` with no `PHYLUM`/`CLASS`/`ORDER`
  ancestor at all** (confirmed in `taxonomy.json`'s own tree, not just the
  filesystem — e.g. `Aceridae`). 270 are empty shells, 86 carry 579 real
  species. `portal/scripts/lib/familyPath.ts`'s `[loc.slug]` fallback
  resolves these by design ("every rank is optional because the tree
  decides"), so this is not a path-resolution bug, and it does not
  contradict root `CLAUDE.md`'s literal "no family directories at the
  repo root" claim (they're under `taxonomy/animalia/`, not the repo
  root) — but it does mean "every family lives at
  `taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/`" overstates
  completeness for these 356. Same pattern `BACKLOG.md` already tracks
  for the 1,091 Fungi / 105 Plantae / 6 Chromista 2026-10-21 scaffolding
  shells ("sit directly under kingdom Fungi, which is not where mycology
  would place them") — that entry doesn't yet mention Animalia's count.
  Worth a `BACKLOG.md` addendum, not done here since it's a data/triage
  decision, not an index-accuracy one.
