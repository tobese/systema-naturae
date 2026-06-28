# Tooltip

Hover tooltips for tree nodes, rendered by [`FamilyTree.tsx`](../../shared/src/components/FamilyTree.tsx).

## Current Behaviour

- Tooltips appear on **hover** over any node in the radial or vertical tree.
- Content varies by rank:
  - **Species** — scientific name, common name, named-after note, and a **Wikipedia thumbnail** (fetched lazily from the REST API).
  - **Genus / Subfamily / Tribe** — name, species count, colour indicator.
  - **Family** — common name, species count, class colour.
- Position follows the mouse with a small offset.
- **Horizontal flip** (`flipLeft`) — switches to left of cursor when near the right edge.
- **Vertical flip** (`flipTop` when `y > containerH - 220`) — switches to above the cursor when near the bottom edge (fixes small-viewport clipping).

## Touch support (shipped)

- **500ms long-press** on any node triggers the tooltip (`touchstart` + `setTimeout(...,500)`, cancelled by `touchend` / `touchmove`).
- Implemented in `attachTooltip()` inside `FamilyTree.tsx` (around line 318).

## Keyboard tooltip (shipped)

- Arrow-key navigation in `App.tsx` sets `tooltipTargetId` for 2 seconds.
- `FamilyTree.tsx` computes the on-screen position of that node and renders the tooltip without requiring mouse hover.

## Files

| File | Role |
|------|------|
| `shared/src/components/FamilyTree.tsx` | Renders tooltip div inside the SVG container; updates on `mouseover` / `mousemove` / `mouseout` / `touchstart` / `tooltipTargetId`. |
| `portal/src/components/UnifiedInfoPanel.tsx` | Sidebar panel that shows the same (and more) information in a persistent form. |

## Backlog

- [ ] **Fade-in thumbnails** — animate the Wikipedia hover preview instead of a sudden flash.

## Related

- [`navigation.md`](./navigation.md) — click vs. hover interaction model.
- [`Screen Handling.md`](./Screen%20Handling.md) — touch interaction patterns.
