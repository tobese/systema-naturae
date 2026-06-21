# Graph UI — design & issues

## 1. Node sizing

Nodes scale by rank. Current radii (`nodeR()` in `FamilyTree.tsx`):

| Rank | Radius |
|---|---|
| KINGDOM | 16 |
| FAMILY | 9 |
| SUBFAMILY / TRIBE | 7 |
| GENUS / HYBRID_GROUP | 5 |
| BREED_GROUP | 4 |
| HYBRID | 3.5 |
| BREED / SUBSPECIES | 2.5 |
| SPECIES (default) | 3 |

This works but the scale is shallow — family (9) vs species (3) is only 3× despite representing orders of magnitude more taxa.

### Proposed

- Keep size by rank, but widen the scale: FAMILY → 12, SPECIES → 2.5
- Family-level nodes that have been "expanded" (their children visible) could shrink slightly to make room

## 2. Family overflow

When a family is expanded in the portal, its children (genus+species) overwhelm the tree. Currently handled by arc remapping (`remapAngles` in `FamilyTree.tsx`) — the focused family gets 65% of the circle, everything else gets 35%.

### Issues

- 65% is still too tight for families with 200+ species
- No visual cue that the tree is "zoomed" into a family

### Options

- Reduce arc to 50/50 when a genus within the family is focused (drill deeper)
- Collapse other families to just their FAMILY node when one family is expanded (hide their children)
- Animate the transition between arc ratios

## 3. Node color consistency

Nodes are coloured by lineage via `fillColor()`, which uses the same `COLOR_REGISTRY` as `accentForNode()` in the side panel. This is already consistent for the most part.

### Inconsistencies

- KINGDOM nodes get `#c8a84a` in both — good
- FAMILY nodes get `#F5F5F5` fill in tree vs `#F5F5F5` accent in panel — good
- GENUS nodes inherit lineage color or fall back to subfamily color — same as panel — good
- SPECIES nodes get lineage color at 60% opacity (`${color}99`) in tree; panel uses full opacity. This is intentional for readability but might confuse — consider matching opacity.

## 4. Side panel — genus view

Currently `GenusPanel` (`UnifiedInfoPanel.tsx:382`):

```
[Italic name]
[commonName]
[description]
[N species]

List: species → [name] [commonName]
```

### Problem

- Higher ranks (class, order, family) show a structured header with rank label, big name, description, then a clickable list of children with counts
- Genus drops the header pattern — no rank label, no accent colour stripe, no children count in the header area
- Genus listing species is fine, but the layout doesn't feel like a cohesive "panel" with the rest

### Proposed

- Add rank badge: `GENUS` label with accent colour (matching lineage/subfamily colour)
- Standardise the data layout: name → description → count → children list
- Keep existing layout but add the rank badge and ensure consistent padding/font sizing with other panels

## 5. Side panel — subfamily/tribe view

`SubfamilyPanel` works well — has the same structure as higher ranks with accent colour.

## 6. Unaddressed

- Wikipedia thumbnails on hover (`TooltipBox`) — works but could fade in instead of appearing suddenly
- The `pendingZoomId` mechanism correctly centres on a node but doesn't always pick the right zoom level for genus-level views
- Search results (`highlightedNodeIds`) dim non-matching nodes to 0.1 opacity — consider a pulsing glow on matched nodes instead
