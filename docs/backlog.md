# Backlog

This is the living roadmap for the Systema Naturae portal. Items are grouped by theme and roughly prioritised.

---

## UI / Interaction

### Screen Handling — Touch & Desktop
**Status:** Partially implemented.  
**Doc:** [`Screen Handling.md`](./Screen%20Handling.md)

- [x] **Touch: multi-finger zoom & rotate** — handled by D3 zoom. ✅ Already works.
- [x] **Center on current node** — `C` / `Home` key re-centres the viewport on the selected node.
- [x] **Rotate tree on desktop** — `Q` / `E` keys rotate the radial layout by 15° increments.

### Statistics Header
**Status:** Shipped.  
**Doc:** [`Statistics header.md`](./Statistics%20header.md)

- [x] Arrow-pill breadcrumb from Phylum → Species.
- [x] Integrated colour themes (`colorRegistry.ts`, `PORTAL_THEME`) per rank.
- [x] Placement: new `StatisticsHeader.tsx` component above `NodeNav`.
- [x] Deep paths scroll horizontally in narrow sidebars.

### Tooltip
**Status:** Shipped.  
**Doc:** [`Tooltip.md`](./Tooltip.md)

- [x] Fix viewport clipping on small screens — vertical flip when near bottom edge.
- [x] Add touch equivalent — 500ms long-press on nodes.
- [x] Optional: rich preview with Wikipedia thumbnail. — Fetched lazily from Wikipedia REST API.
- [x] Optional: keyboard-triggered tooltip during arrow-key navigation — shown for 2s after arrow-key nav.

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

---

## Infrastructure

- [ ] Keep docs in sync with code changes (update these `.md` files when implementation lands).
- [ ] Add `docs/README.md` index if the docs directory grows beyond 6 files.

---

## Archive

Items that were proposed, decided against, or already shipped live here.

### Shipped 2026-06-25 — UI Polish Batch

- **Tooltip clipping fix** — `TooltipBox` now receives `containerH` and flips upward when near the bottom edge.
- **Touch long-press** — `attachTooltip` in `FamilyTree.tsx` now listens for `touchstart`/`touchend`/`touchmove` with a 500ms timer.
- **Keyboard tooltip** — Arrow-key navigation in `App.tsx` sets `tooltipTargetId` for 2s; `FamilyTree.tsx` computes screen position and renders tooltip.
- **Center on node** — `C` / `Home` keys set `pendingZoomId` and force re-render.
- **Tree rotation** — `Q` / `E` keys adjust `treeRotation` state; `FamilyTree.tsx` adds `rotationRad` offset to radial layout angles, links, text anchors, click anchors, zoom targets, and special-link positions.
- **Statistics Header** — New `StatisticsHeader.tsx` renders pill breadcrumb with `pillColor()` using `PORTAL_THEME` and `COLOR_REGISTRY`; sits above `NodeNav` in sidebar.
- **Wheel of Nature** — New `WheelOfNature.tsx` modal with CSS-animated SVG wheel, 12 class sectors coloured from `CLASS_PALETTE`, random species selection, and navigation.

### Shipped 2026-06-25 — Import Session (14K species)

- **Removed `enriched` whitelist** from `findGaps.ts` — was hiding 21 families from gap reporting.
- **GBIF cache re-fetch** (+13,977 species):
  - `cichlidae` +2,446 | `nymphalidae` +7,583 | `lycosidae` +2,376 | `buthidae` +1,572
  - `dendrobatidae` +16 (Ollama, partial)
- **Portal:** 106,691 → 110,872 nodes (+4,181)
- **Issues found:** Arachnida GBIF cache stale for some families; Ollama `qwen2.5:3b` cannot handle large prompts.

---

## Queued for Future Sessions

### Heavy Insect Fetch (80K+ species)
- `carabidae` — 38,960 gap
- `chrysomelidae` — 33,690 gap
- Rebuild Insecta GBIF cache if stale

### Ollama with Larger Model
- **Failed in this session** (`qwen2.5:3b` timed out on all but one):
  - `dendrobatidae` — 74 remaining (partial: +16)
  - `pelobatidae` — 82 gap
  - `echinidae` — 57 gap
  - `sepiidae` — 43 gap
  - `colubridae` — 31 gap
  - `scincidae` — 17 gap
  - `chamaeleonidae` — 7 gap
  - `lacertidae` — 5 gap
  - `eublepharidae` — 5 gap
  - `grallariidae` — 3 gap
- **Requires:** `qwen2.5:7b` or `llama3.2` — current `3b` model cannot handle prompts for families with existing genus structures

### Wikipedia Source Filter
- **Goal:** Toggle to highlight only `sourcedFrom === "wikipedia"` species
- **Pattern:** Reuse existing `highlightedContinent` / `highlightedNodeIds` mechanism in `FamilyTree.tsx`
- **State:** Add `highlightWikipedia` to `App.tsx` + `useUnifiedTree.ts`
- **UI:** Checkbox in `OptionsPanel.tsx` or badge in `CoverageModal.tsx`
- **Impact:** Would reveal that 6 of 8 insect families are 100% synthetic

### Insect Filtration — Wikipedia Coverage Scan
- **Research done:** All 8 insect families scanned for Wikipedia coverage
- **Result:** 6 families are 100% synthetic, 2 are >97% synthetic
- **Plan:** Implement species-level `sourcedFrom` tracking, then add family-level Wikipedia coverage badges in Coverage modal
- **Priority:** Low — data quality issue, not a feature gap

### Data Quality
- Re-fetch `cyprinidae` from live API (cache returned 1,795 vs target 3,000)
- Re-fetch `vespidae` from live API (cache returned 2,069 vs target 5,000)
- Re-fetch `agelenidae` from live API (cache returned 612 vs target 1,200)
- Fix `buildData.sh` timeout when spawned from scripts
