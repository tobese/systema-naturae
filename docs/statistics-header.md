# Statistics Header

A visual header that summarises the taxonomic path from **Phylum → Class → Order → Family → Genus → Species** for the currently selected node.

**Status:** Shipped — `portal/src/components/StatisticsHeader.tsx`, used inside `TaxonomySidebar.tsx`.

## What it does

1. Renders every rank in the lineage as a rounded **arrow pill** with a chevron tip that slots into the next pill — a connected breadcrumb trail.
2. Pill colour is resolved per-rank via `pillColor()`, which composes `PORTAL_THEME` for global ranks (Phylum/Class) and `COLOR_REGISTRY` (`portal/src/colorRegistry.ts`) for the family-specific palette below.
3. Sits above [`NodeNav.tsx`](../../shared/src/components/NodeNav.tsx) in the sidebar.
4. Scrolls horizontally inside narrow sidebars so deep paths (e.g. subspecies of a hybrid) never break the layout.

## Data Source

The breadcrumb path is computed in [`App.tsx`](../../portal/src/App.tsx) via `getPathToNode(annotatedData, selected.id)`. It contains the full chain from Kingdom down to the selected node. `StatisticsHeader` filters out `KINGDOM` (same as `NodeNav` does via `SKIP_RANKS`).

## Files

| File | Role |
|---|---|
| `portal/src/components/StatisticsHeader.tsx` | Renders the arrow-pill row, computes per-rank colour. |
| `portal/src/components/TaxonomySidebar.tsx` | Hosts `StatisticsHeader` above `NodeNav`. |
| `portal/src/colorRegistry.ts` | `PORTAL_THEME` + per-family `COLOR_REGISTRY`. |

## Backlog

- [ ] **Click pills to jump** — clicking a rank pill could navigate to that ancestor (currently visual-only; ancestor navigation lives in `NodeNav`).

## Related

- [`navigation.md`](./navigation.md) — breadcrumb path computation and `NodeNav` behaviour.
