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
- [ ] **Improve genus-centering zoom** — refine zoom scale/level when centering on genus nodes.

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

### Book View
**Status:** Queued.  
**Doc:** [`Book View.md`](./Book%20View.md)

- [ ] **Recursive Book View** — toggleable nested expandable taxonomy sections styled with the portal theme.
- [ ] **Bookmarks & Anchor Links** — deep linking per section.
- [ ] **Search highlights** — scrolling to and opening the relevant section on search matches.

### Search Visualization
**Status:** Queued.

- [ ] **Pulsing Search Matches** — replace simple 10% opacity dimming with an active, pulsing glow on matching nodes.

---

## Infrastructure

- [x] Keep docs in sync with code changes — updated CLAUDE.md node counts (110,827), added docs/README.md index.
- [x] Add `docs/README.md` index — 7 docs files now indexed.
- [x] Fix `buildData.sh` timeout — increased from 60s → 180s in `importFamily.ts` and `fetchSpeciesFromApi.ts` (build takes ~60-90s).

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

### Shipped 2026-06-25 — Papilionidae Wikipedia Import

- **Script:** `portal/scripts/importPapilionidaeWikipedia.ts` — fetches from GBIF, checks Wikipedia REST API, enriches with descriptions/continents
- **Result:** ~500 species with `sourcedFrom: "wikipedia"` written to `insecta/lepidoptera/papilionidae/src/data/papilionidae.json`
- **Scanner:** `portal/scripts/scanInsectWikipediaCoverage.ts` — partial scan of 8 insect families (see Insect Filtration section below)

### Shipped 2026-06-25 — Wikipedia Source Filter UI

- **OptionsPanel** — new "Highlight Wikipedia species" checkbox in ⚙ gear menu
- **useUnifiedTree** — merges `highlightedContinent` and `highlightWikipedia` into a single `highlightedNodeIds` set
- **FamilyTree.tsx** — already dims non-highlighted leaf nodes to 0.1 opacity; no changes needed
- **TaxonNode type** — added `sourcedFrom?: string` field

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
- **Network note:** Steamie (primary Ollama, Windows 11, user `opencode`) unreachable — "No route to host". Check Biggie (Windows 10), Debbie (Debian), or Macie (macOS) as fallbacks. All four machines run Ollama.

### Wikipedia Source Filter
- **Status:** Shipped.
- **Implementation:** `highlightWikipedia` toggle in OptionsPanel (⚙ gear menu). When enabled, dims non-Wikipedia species to 10% opacity within the focused family.
- **Files changed:** `OptionsPanel.tsx` (new toggle), `App.tsx` (state + prop), `useUnifiedTree.ts` (builds highlight set), `shared/src/types.ts` (added `sourcedFrom` field).

### Insect Filtration — Wikipedia Coverage Scan
**Status:** Partial scan complete. Papilionidae import done.

**Scripts:**
- `portal/scripts/scanInsectWikipediaCoverage.ts` — scans GBIF + Wikipedia coverage per family
- `portal/scripts/importPapilionidaeWikipedia.ts` — fetches + enriches from Wikipedia (DONE)

**Results:**

| Family | Target | GBIF | Wikipedia | Coverage | Status |
|---|---|---|---|---|---|
| `papilionidae` | 554 | 892 | ~296 | **33.2%** | ✅ Imported |
| `apidae` | 6,526 | 6,526 | ~640 | **9.8%** | 📝 Queued |
| `formicidae` | 15,057 | 15,057 | ~1,476 | **9.8%** | 📝 Queued |
| `vespidae` | 5,000 | 2,069 | ~196 | **9.5%** | 📝 Queued |
| `nymphalidae` | 7,583 | 7,583 | ? | **0%*** | ⚠️ Re-scan needed |
| `libellulidae` | 1,126 | 1,126 | ? | **0%*** | ⚠️ Re-scan needed |
| `carabidae` | 40,000 | 41,556 | ? | **?** | ⏳ Scan too slow |
| `chrysomelidae` | 35,000 | ? | ? | **?** | ⏳ Not scanned |

*0% results may be API errors — needs re-scan with better error handling.

**Plan:**
1. Fix scanner script to handle rate limits and retry logic
2. Re-scan `nymphalidae`, `libellulidae`, `carabidae`, `chrysomelidae`
3. For families with >15% coverage: import Wikipedia-backed species only
4. For families with 5–15% coverage: mixed import (Wikipedia + synthetic)
5. For families with <5% coverage: full synthetic import, mark as such

**Priority:** Medium — Papilionidae done. Next: re-scan the 0% families.

### Data Quality
- Re-fetch `cyprinidae` from live API (cache returned 1,795 vs target 3,000)
- Re-fetch `vespidae` from live API (cache returned 2,069 vs target 5,000)
- Re-fetch `agelenidae` from live API (cache returned 612 vs target 1,200)
