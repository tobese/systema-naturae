# Statistics Header

A visual header that summarises the taxonomic path from **Phylum → Class → Order → Family → Genus → Species** for the currently selected node.

## Goals

1. Display every rank in the lineage with its correct **family/class colour** (as defined in [`colorRegistry.ts`](../../portal/src/colorRegistry.ts) and [`colors.ts`](../../portal/src/colors.ts)).
2. Make the flow feel like connected **arrow pills** that slot into one another, creating a breadcrumb trail.

## Design Ideas

| Idea | Description | Pros | Cons |
|------|-------------|------|------|
| **Arrow pills** (preferred) | Each rank is a rounded pill with a chevron/arrow tip that overlaps the next pill. Colour per rank comes from the existing theme. | Clear directionality, compact, on-brand | Needs custom CSS/SVG shape |
| **Horizontal stepper** | Material-style stepper with dots and lines. | Familiar pattern | Less colour flexibility |
| **Stacked tags** | Simple inline tags separated by slashes. | Easy to implement | Visually flat |

## Data Source

The breadcrumb path is already computed in [`App.tsx`](../../portal/src/App.tsx) via `getPathToNode(annotatedData, selected.id)`. It contains the full chain from Kingdom down to the selected node.

## Open Questions

- Should the header live inside [`NodeNav.tsx`](../../shared/src/components/NodeNav.tsx) or be a new component above it?
- Should clicking a pill jump to that rank (like the existing breadcrumb buttons)?
- How should it behave on very deep paths (e.g. subspecies) in narrow sidebars?

## Related

- [`navigation.md`](./navigation.md) — breadcrumb path computation and `NodeNav` behaviour.
