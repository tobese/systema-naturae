# Tooltip

Hover tooltips for tree nodes in [`FamilyTree.tsx`](../../shared/src/components/FamilyTree.tsx).

## Current Behaviour

- Tooltips appear on **hover** over any node in the radial or vertical tree.
- Content varies by rank:
  - **Species** — scientific name, common name, named-after note, and a **Wikipedia thumbnail** (fetched lazily from the REST API).
  - **Genus / Subfamily / Tribe** — name, species count, colour indicator.
  - **Family** — common name, species count, class colour.
- Position follows the mouse with a small offset. Flips to the left when near the right edge (`flipLeft`).

## Files

| File | Role |
|------|------|
| `shared/src/components/FamilyTree.tsx` | Renders tooltip div inside the SVG container; updates on `mouseover` / `mousemove` / `mouseout`. |
| `portal/src/components/UnifiedInfoPanel.tsx` | Sidebar panel that shows the same (and more) information in a persistent form. |

## Known Limitations

- Tooltips can clip at the SVG boundary on small viewports.
- No touch equivalent (long-press is not implemented).

## Future Ideas

- **Fixed tooltip** — anchor to the top-right of the tree instead of following the mouse.
- **Rich preview** — include a thumbnail image for species (fetch from the same Wikipedia hook used in `UnifiedInfoPanel`).
- **Keyboard tooltip** — show on focus/hover via keyboard navigation (`↑` / `↓`).

## Related

- [`navigation.md`](./navigation.md) — click vs. hover interaction model.
- [`Screen Handling.md`](./Screen%20Handling.md) — touch interaction gaps.
