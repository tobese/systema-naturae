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

### Shipped in this batch

- **Tooltip clipping fix** — `TooltipBox` now receives `containerH` and flips upward when near the bottom edge.
- **Touch long-press** — `attachTooltip` in `FamilyTree.tsx` now listens for `touchstart`/`touchend`/`touchmove` with a 500ms timer.
- **Keyboard tooltip** — Arrow-key navigation in `App.tsx` sets `tooltipTargetId` for 2s; `FamilyTree.tsx` computes screen position and renders tooltip.
- **Center on node** — `C` / `Home` keys set `pendingZoomId` and force re-render.
- **Tree rotation** — `Q` / `E` keys adjust `treeRotation` state; `FamilyTree.tsx` adds `rotationRad` offset to radial layout angles, links, text anchors, click anchors, zoom targets, and special-link positions.
- **Statistics Header** — New `StatisticsHeader.tsx` renders pill breadcrumb with `pillColor()` using `PORTAL_THEME` and `COLOR_REGISTRY`; sits above `NodeNav` in sidebar.
- **Wheel of Nature** — New `WheelOfNature.tsx` modal with CSS-animated SVG wheel, 12 class sectors coloured from `CLASS_PALETTE`, random species selection, and navigation.
