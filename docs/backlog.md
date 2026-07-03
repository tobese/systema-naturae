# Backlog

Living roadmap for the Systema Naturae portal.

---

## UI / Interaction

### Screen Handling — Touch & Desktop
**Status:** Mostly shipped.

- [x] Touch: multi-finger zoom & rotate — handled by D3 zoom.
- [x] Center on current node — `C` / `Home` key re-centres on selected node.
- [x] Rotate tree on desktop — `Q` / `E` keys rotate radial layout by 15°.
- [ ] **Improve genus-centering zoom** — refine zoom scale/level when centering on genus nodes.

### Statistics Header
**Status:** Shipped.

- [x] Arrow-pill breadcrumb from Phylum → Species.
- [x] Integrated colour themes (`colorRegistry.ts`, `PORTAL_THEME`) per rank.
- [x] Placement: `StatisticsHeader.tsx` above `NodeNav` in sidebar.
- [x] Deep paths scroll horizontally in narrow sidebars.

### Tooltip
**Status:** Shipped.

- [x] Viewport clipping fix — vertical flip when near bottom edge.
- [x] Touch equivalent — 500ms long-press on nodes.
- [x] Rich preview with Wikipedia thumbnail — fetched lazily from REST API.
- [x] Keyboard-triggered tooltip during arrow-key navigation.
- [ ] **Fade-in thumbnails** — make hover previews feel less abrupt.
  - Fade the image in after load instead of popping it in.
  - Keep the caption/text visible while the image resolves.
  - Avoid layout shift when the thumbnail appears.

### Wheel of Nature
**Status:** Shipped.

- [x] Build `WheelOfNature.tsx` component (SVG animation).
- [x] 12-sector wheel with class-level categories.
- [x] Outer rim pins + flapper pointer.
- [x] Random species selection + side-panel opening.
- [x] "Spin again" button + modal overlay.
- [ ] Optional: tick audio while spinning.
- [ ] Optional: cache last winner per session to avoid immediate repeats.

### Book View
**Status:** Shipped.

- [x] Recursive Book View — toggleable nested expandable taxonomy sections.
- [ ] **Bookmarks & Anchor Links** — deep linking per section.
- [ ] **Search highlights** — scrolling to and opening relevant section on search matches.

### Search Visualization
**Status:** Queued.

- [ ] **Pulsing Search Matches** — replace simple 10% opacity dimming with pulsing glow on matching nodes.

---

## Infrastructure

- [x] Offline Wikipedia pipeline — `buildWikipediaDb.py` → SQLite DB at `/Volumes/WikiDump/wiki-pages.sqlite`.
- [x] Gap-tracking daemon — `phylumProgressd.ts` (port 9876) records POSTs from gap reports.
- [x] 17 phyla, 4,797 families, 429,488 species (2026-07-03).
- [x] On-demand data loading: skeleton (~307 KB) + per-order chunks (363 files) + LRU cache, replaces monolithic 375 MB `unified-taxonomy.json` fetch.
- [x] **Fix `reportPhyla.ts`** — hardcoded class list doesn't see Mollusca's 7 classes; discover classes dynamically from `taxonomy.json`.

---

## Data

- [ ] **Wikipedia enrichment: high-volume classes** — batch the biggest zero/near-zero coverage classes first: Gastropoda, Bivalvia, Annelida, Bryozoa, Porifera, Platyhelminthes, Nematoda.
- [ ] **Wikipedia enrichment: run strategy** — make the enrichment pass resumable per class so long runs can stop/start without losing progress.
- [ ] **Wikipedia enrichment: quality** — keep empty or weak extracts out of `sourcedFrom=wikipedia` and surface only real descriptions.
- [ ] **Micro-phyla scaffolding** — add manual taxonomy treatment for Gastrotricha, Phoronida, Priapulida, Loricifera, Gnathostomulida, Entoprocta, Onychophora, Xenacoelomorpha.
- [ ] **Micro-phyla validation** — verify how each manual phylum should appear in `taxonomy.json`, gap reports, and the UI tree.
- [ ] **Chunk refinement: per-family loading** — split `portal/data/orders/` into per-family files for finer-grained lazy loading.
- [ ] **Chunk refinement: loader update** — teach the runtime manifest/loader to resolve family chunks instead of order chunks.

---

## Resolved — July 2026

### 2026-07-03 — GH Pages deploy + test fixes
- Fixed deploy workflow: copy `data/` into `dist/` for runtime fetch
- Fixed `useTaxonomyLoader.ts`: use `import.meta.env.BASE_URL` for data path resolution on subpath deploy
- Fixed test URLs: relative `?param=val` instead of `/?param=val` for baseURL compatibility
- All 27 Playwright tests pass against live GH Pages site
- Fixed `reportPhyla.ts`: dynamic class→phylum mapping from `taxonomy.json` instead of hardcoded list

### 2026-07-02 — On-demand data loading architecture
- Split `unified-taxonomy.json` (375 MB) into skeleton (~307 KB) + 363 per-order chunk files
- Built `useTaxonomyLoader.ts` with LRU cache (max 3 orders), skeleton-first fetch, merge-on-focus
- Generated `order-manifest.json` (444 KB) with `familyToOrder` reverse lookup
- Deep-link support: `?family=` slug resolves to order and triggers lazy load
- Old monolithic JSON retained for backward compat but no longer fetched

## Resolved — June 2026 Import Sessions

### 2026-06-30 — Mollusca expansion + 10 new phyla (+250k species)
- Mollusca expanded from 1 class (Cephalopoda, 8 fam) to 7 classes (1,529 fam)
- Added Caudofoveata, Monoplacophora, Scaphopoda, Polyplacophora, Bivalvia, Gastropoda
- Expanded Cephalopoda from 8→94 families
- 7 new phyla: Cycliophora, Micrognathozoa, Nematomorpha, Sipuncula, Kinorhyncha,
  Chaetognatha, Nemertea, Brachiopoda, Hemichordata, Rotifera, Acanthocephala,
  Bryozoa, Porifera, Annelida, Platyhelminthes, Nematoda
- Fixed `importClass.ts` phylum parameter, `findGaps.ts` blank class handling
- Added `docs/oddities.md`, `docs/mollusca-expansion-plan.md`

### 2026-06-29 — Wikipedia offline enrichment
- Enriched 19,828 species from SQLite Wikipedia DB
- Zero stuck species across all classes
- Fixed enrichment script bug (marking species as sourcedFrom=wikipedia with empty extracts)

### 2026-06-27/28 — Cnidaria + Ctenophora bootstrap
- Established `scoutPhylum.ts` + `importClass.ts` pipeline for whole-phylum imports
- Cnidaria: 725 families, 22,268 species
- Ctenophora: 6 families, 123 species

### 2026-06-25 — UI Polish + bulk imports
- Tooltip clipping fix, touch long-press, keyboard tooltip
- Centre-on-node / tree rotation keys
- Statistics Header, Wheel of Nature
- Wikipedia Source Filter UI in OptionsPanel
- GBIF cache re-fetch (+14k species)
- Papilionidae Wikipedia import (~500 spp)
