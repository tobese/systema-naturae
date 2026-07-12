# Graph UI — design & issues

## 1. Node sizing
*Status:* ✅ **Done** — Ratios widened to: family (12), subfamily (9), genus (6.5), species (2.5) to provide a clearer hierarchy distinction.

Nodes scale by rank. Radius mappings in `FamilyTree.tsx`:

| Rank | Radius |
|---|---|
| KINGDOM | 16 |
| FAMILY | 12 |
| SUBFAMILY / TRIBE | 9 |
| GENUS / HYBRID_GROUP | 6.5 |
| BREED_GROUP | 4 |
| HYBRID | 3.5 |
| BREED / SUBSPECIES | 2.5 |
| SPECIES (default) | 2.5 |

## 2. Family overflow
*Status:* ✅ **Done** — Family focus pruning implemented. When a family is focused, all other families' children collapse/prune to single dots, giving the focused family the full circle naturally without complex arc remapping.

## 3. Node color consistency
*Status:* ℹ️ **Design Choice Accepted**

- KINGDOM nodes get `#c8a84a` in both — good
- FAMILY nodes get `#F5F5F5` fill in tree vs `#F5F5F5` accent in panel — good
- GENUS nodes inherit lineage color or fall back to subfamily color — same as panel — good
- SPECIES nodes get lineage color at 60% opacity (`${color}99`) in tree; panel uses full opacity. This is intentional for readability but might confuse — consider matching opacity.

## 4. Side panel — genus view
*Status:* ✅ **Done** — Added rank badge `GENUS` label with accent color in `GenusPanel` (`UnifiedInfoPanel.tsx`). Standardized layout.

## 5. Side panel — subfamily/tribe view
`SubfamilyPanel` works well — has the same structure as higher ranks with accent colour.

## 6. Unaddressed / Backlog Items
The following items are moved to the active roadmap in `docs/backlog.md`:

- **Wikipedia thumbnails on hover** (`TooltipBox`) — works but could fade in instead of appearing suddenly.
- **Tree centering** — the `pendingZoomId` mechanism correctly centres on a node but doesn't always pick the right zoom level for genus-level views.
- **Pulsing search results** — Search results (`highlightedNodeIds`) dim non-matching nodes to 0.1 opacity — consider a pulsing glow on matched nodes instead.
