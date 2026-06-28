# Backlog

Living roadmap for the Systema Naturae portal. Items are grouped by theme and roughly prioritised.

---

## UI / Interaction

### Screen Handling — Touch & Desktop
**Status:** Mostly shipped.  
**Doc:** [`Screen Handling.md`](./Screen%20Handling.md)

- [x] **Touch: multi-finger zoom & rotate** — handled by D3 zoom. ✅ Already works.
- [x] **Center on current node** — `C` / `Home` key re-centres the viewport on the selected node.
- [x] **Rotate tree on desktop** — `Q` / `E` keys rotate the radial layout by 15° increments.
- [ ] **Improve genus-centering zoom** — refine zoom scale/level when centering on genus nodes.

### Statistics Header
**Status:** Shipped.  
**Doc:** [`Statistics header.md`](./Statistics%20header.md)

- [x] Arrow-pill breadcrumb from Phylum → Species.
- [x] Integrated colour themes (`colorRegistry.ts`, `PORTAL_THEME`) per rank.
- [x] Placement: new `StatisticsHeader.tsx` component above `NodeNav`.
- [x] Deep paths scroll horizontally in narrow sidebars.
- [ ] **Click pills to jump** — make rank pills clickable to navigate to that ancestor.

### Tooltip
**Status:** Shipped.  
**Doc:** [`Tooltip.md`](./Tooltip.md)

- [x] Fix viewport clipping on small screens — vertical flip when near bottom edge.
- [x] Add touch equivalent — 500ms long-press on nodes.
- [x] Rich preview with Wikipedia thumbnail — fetched lazily from Wikipedia REST API.
- [x] Keyboard-triggered tooltip during arrow-key navigation — shown for 2s after arrow-key nav.
- [ ] **Fade-in thumbnails** — animate/fade in Wikipedia hover previews instead of sudden flash.

---

## Features

### Wheel of Nature
**Status:** Shipped.  
**Doc:** [`Wheel of Nature.md`](./Wheel%20of%20Nature.md)

- [x] Build `WheelOfNature.tsx` component (SVG animation).
- [x] 12-sector wheel with class-level categories (one per class in the tree).
- [x] Outer rim pins + flapper pointer.
- [x] Random species selection + side-panel opening via "View species".
- [x] "Spin again" button.
- [x] Modal overlay.
- [ ] Optional: tick audio while spinning.
- [ ] Optional: cache last winner per session to avoid immediate repeats.

### Book View
**Status:** Shipped.  
**Doc:** [`Book View.md`](./Book%20View.md)

- [x] **Recursive Book View** — toggleable nested expandable taxonomy sections in `BookView.tsx`.
- [ ] **Bookmarks & Anchor Links** — deep linking per section.
- [ ] **Search highlights** — scrolling to and opening the relevant section on search matches.

### Search Visualization
**Status:** Queued.

- [ ] **Pulsing Search Matches** — replace simple 10% opacity dimming with an active, pulsing glow on matching nodes.

---

## Infrastructure

- [x] Keep docs in sync with code — full audit done 2026-06-28; CLAUDE.md, Coverage.md, Import.md, navigation.md, missing-phyla.md and all feature docs refreshed against actual state (183,329 nodes / 1,114 families / 7 phyla).
- [x] Add `docs/README.md` index.
- [x] Fix `buildData.sh` timeout — increased from 60s → 180s in `importFamily.ts` and `fetchSpeciesFromApi.ts`.
- [x] **Offline Wikipedia pipeline** — `buildWikipediaDb.py` builds `/Volumes/WikiDump/wiki-pages.sqlite`; `enrichFromWikipedia.ts` and `mergeWikiInfoboxes.ts` consume it. 52,655 species now carry `sourcedFrom: "wikipedia"`.
- [x] **Gap-tracking daemon** — `portal/scripts/phylumProgressd.ts` (port 9876) records every `reportPhyla.ts` / `generateGapTasks.ts` POST so progress is graphable over time.

---

## Archive — Shipped & Resolved

### Shipped 2026-06-25 — UI Polish Batch

- **Tooltip clipping fix** — `TooltipBox` now receives `containerH` and flips upward when near the bottom edge.
- **Touch long-press** — `attachTooltip` in `FamilyTree.tsx` listens for `touchstart` / `touchend` / `touchmove` with a 500ms timer.
- **Keyboard tooltip** — Arrow-key navigation in `App.tsx` sets `tooltipTargetId` for 2s; `FamilyTree.tsx` computes screen position and renders tooltip.
- **Center on node** — `C` / `Home` keys set `pendingZoomId` and force re-render.
- **Tree rotation** — `Q` / `E` keys adjust `treeRotation` state; `FamilyTree.tsx` adds `rotationRad` offset to radial layout angles, links, text anchors, click anchors, zoom targets, and special-link positions.
- **Statistics Header** — `StatisticsHeader.tsx` renders pill breadcrumb with `pillColor()` using `PORTAL_THEME` and `COLOR_REGISTRY`; sits above `NodeNav` in sidebar.
- **Wheel of Nature** — `WheelOfNature.tsx` modal with CSS-animated SVG wheel, 12 class sectors coloured from `CLASS_PALETTE`, random species selection, navigation.

### Shipped 2026-06-25 — Import Session (14K species)

- Removed `enriched` whitelist from `findGaps.ts` (was hiding 21 families).
- GBIF cache re-fetch (+13,977 species): `cichlidae` +2,446 | `nymphalidae` +7,583 | `lycosidae` +2,376 | `buthidae` +1,572 | `dendrobatidae` +16.

### Shipped 2026-06-25 — Papilionidae Wikipedia Import

- `portal/scripts/importPapilionidaeWikipedia.ts` — fetches from GBIF, checks Wikipedia REST API, enriches with descriptions/continents.
- Result: ~500 species with `sourcedFrom: "wikipedia"` written to `insecta/lepidoptera/papilionidae/src/data/papilionidae.json`.

### Shipped 2026-06-25 — Wikipedia Source Filter UI

- `OptionsPanel` — "Highlight Wikipedia species" checkbox in ⚙ gear menu.
- `useUnifiedTree` — merges `highlightedContinent` and `highlightWikipedia` into a single `highlightedNodeIds` set.
- `TaxonNode` type — added `sourcedFrom?: string` field.

### Shipped 2026-06-27/28 — Cnidaria + Ctenophora bootstrap

- `scripts/scoutPhylum.ts` + `scripts/importClass.ts` + `scripts/bootstrapClass.ts` workflow established for whole-phylum imports.
- **Cnidaria** — 725 families (Anthozoa 549, Hydrozoa 141, Scyphozoa 20, Cubozoa 8, Staurozoa 7), 22,268 species — 100% complete.
- **Ctenophora** — 6 families (Tentaculata 5, Nuda 1), 123 species — 100% complete.

### Resolved — Insect Filtration & Ollama gap list

The 2026-06-25 "Queued for Future Sessions" insect / Ollama gap list was fully cleared during the late-June bulk-import passes. The following families are now at or above target:

`papilionidae`, `apidae`, `formicidae`, `vespidae`, `nymphalidae`, `libellulidae`, `carabidae`, `dendrobatidae`, `echinidae`, `sepiidae`, `colubridae`, `scincidae`, `chamaeleonidae`, `lacertidae`, `eublepharidae`, `grallariidae`, `cyprinidae`, `agelenidae`.

---

## Queued

### Heavy gap (Insecta)

- `chrysomelidae` — **gap 33,690** (have 1,310 / target 35,000). The single largest outstanding gap in the entire portal — ~98% of all remaining missing species. Likely needs a dedicated GBIF cache rebuild and a multi-pass import.

### Medium gaps

Pulled from `portal/data/gap-report.json` (28/06/2026):

| Family | Class | Have | Target | Gap |
|---|---|---:|---:|---:|
| `hylidae` | Amphibia | 766 | 1,000 | 234 |
| `pelobatidae` | Amphibia | 50 | 100 | 50 |
| `pleuronectidae` | Actinopterygii | 72 | 101 | 29 |
| `nothobranchiidae` | Actinopterygii | 326 | 340 | 14 |

### Aves long-tail (62 families, all gap < 30)

Most remaining bird gaps are tiny IOC top-ups — `sturnidae` (26), `cracidae` (24), `pachycephalidae` (18), `timaliidae` (18), `tityridae` (17), `rhipiduridae` (16), `tinamidae` (15), `trogonidae` (15), etc. Best tackled with a single Wikipedia-REST batch enrichment pass.

### New phyla (per `missing-phyla.md`)

1. **Annelida** (~22,000 species) — segmented worms; recommended next phylum target.
2. **Onychophora** (~200 species) — velvet worms; small enough for a 100% pass.
3. **Porifera** (~8,500 species) — sponges.
