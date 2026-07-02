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
- [ ] **Click pills to jump** — make rank pills clickable to navigate to that ancestor.

### Tooltip
**Status:** Shipped.

- [x] Viewport clipping fix — vertical flip when near bottom edge.
- [x] Touch equivalent — 500ms long-press on nodes.
- [x] Rich preview with Wikipedia thumbnail — fetched lazily from REST API.
- [x] Keyboard-triggered tooltip during arrow-key navigation.
- [ ] **Fade-in thumbnails** — animate/fade in Wikipedia hover previews instead of sudden flash.

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
- [x] 17 phyla, 4,796 families, 429,472 species (2026-06-30).

---

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
