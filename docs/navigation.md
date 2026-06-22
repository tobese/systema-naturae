# Navigation System Architecture

The navigation system is distributed across `useUrlState`, `App.tsx` `handleSelect`, `useUnifiedTree` pruning, and `FamilyTree` zoom/interaction. This doc covers how they interlock.

## 1. URL State (`portal/src/hooks/useUrlState.ts`)

Three URL search params drive state:

| Param    | Meaning                          | Set by                           |
| -------- | -------------------------------- | -------------------------------- |
| `family` | `focusedFamilySlug` (app slug)   | family click, navigateTo         |
| `node`   | `selectedNodeId` (any taxon id)  | species/genus/order click        |
| `class`  | `focusedClassId` (CLASS node id) | class click                      |

**Ordering constraint** (`buildUrl`): `class` is always written first, then `family`, then `node`. If `class` is set, `family` and `node` are omitted. If `family` is set, `class` is cleared.

**pushState for all updates** — never `replaceState`, so browser back/forward history works fully.

**popstate listener** re-reads the URL on back/forward. `setState(parseUrl())` triggers re-render.

**Per-param updaters:**
- `setFocus(slug)` — sets family=slug, clears node+class. Single pushState.
- `setFocusedClass(id, nodeId?)` — sets class=id (and optional node), clears family. Single pushState.
- `setSelectedNodeId(id)` — updates node param only, preserving existing family/class. Spreads prev state.
- `navigateTo(family, nodeId)` — sets family+node, clears class. Single pushState.

## 2. App Dispatch (`portal/src/App.tsx`, `handleSelect`)

`handleSelect(node)` is the single entry point for all tree clicks. It dispatches by `node.rank`:

```
KINGDOM / PHYLUM
  → setFocusedClass(null, nodeId)  // clear class focus, select node
  → pendingZoomId.current = nodeId

CLASS
  → if already focused: setFocusedClass(null, null)  // unfocus
  → else: setFocusedClass(id, id)                     // focus
  → pendingZoomId.current = nodeId

FAMILY
  → if slug === focusedFamilySlug: setFocus(null)     // unfocus
  → else: navigateTo(slug, id)                        // focus
  → reset expandedSubspeciesIds, expandedBreedIds, highlightedContinent
  → pendingZoomId.current = nodeId (on focus only)

NODE OUTSIDE FOCUSED FAMILY (node.familySlug !== focusedFamilySlug)
  → navigateTo(node.familySlug, node.id)  // switch to that family
  → reset expansions
  → pendingZoomId.current = nodeId

SPECIES with subspecies/breeds
  → toggle expandedSubspeciesIds or expandedBreedIds
  → pendingZoomId.current = nodeId (on expand only)

ORDER / SUBFAMILY / TRIBE / GENUS / BREED_GROUP / HYBRID_GROUP
  → pendingZoomId.current = nodeId  // zoom to this node

ALL RANKS (fallthrough)
  → toggle selectedNodeId (click same node deselects)
```

### Focus/Unfocus Flows

| Action | URL effect | Tree effect |
|--------|-----------|-------------|
| Click focused family | `?family=` removed | overview mode (143 families as dots) |
| Click different family | `?family=<slug>&node=<id>` | prune to that family |
| Click focused class | `?class=` removed | full tree, no compression |
| Click different class | `?class=<id>&node=<id>` | remap angles: 65% focused class |
| Click family node out of focus | `?family=<slug>&node=<id>` | switch to that family |
| Escape | collapses family, or class | same as unfocus |
| "← All families" button | `handleCollapseFamily` | same as unfocus |

### State Reset on Focus Change

When focusing a new family (or unfocusing):
- `expandedSubspeciesIds` = new Set()
- `expandedBreedIds` = new Set()
- `highlightedContinent` = null

## 3. Pruning (`portal/src/hooks/useUnifiedTree.ts`)

`pruneTree(node, focusedFamilyId, ...)` has two modes.

### Overview mode (`focusedFamilyId === null`)
- Every FAMILY node is collapsed to a leaf (children stripped, only metadata kept).
- All other nodes are kept normally.
- Result: 143 families as dots, 0 species visible.

### Focused mode (`focusedFamilyId` is set)
- Walks the tree to find the matching FAMILY node.
- Returns ONLY that family subtree (family becomes the tree root).
- Ancestors (Kingdom → Phylum → Class → Order) are removed entirely.
- Within the family subtree: subspecies and breed groups are collapsed by default (use `expandedSubspeciesIds` / `expandedBreedIds` to expand).
- Non-focused families: the `find` helper returns null for them — they don't appear in the output at all.

### Ancestor display

Ancestors are NOT in the tree. They're shown in the sidebar's `NodeNav` breadcrumb, which walks `annotatedData` (the full unfiltered tree) via `getPathToNode(annotatedData, selected.id)`. This ensures the path is always complete regardless of pruning.

## 4. Zoom (`shared/src/components/FamilyTree.tsx`)

### pendingZoomId ref

A ref (`MutableRefObject<string | null>`) passed from App to FamilyTree. The protocol:

1. **Set** in `handleSelect` (or during render for URL-driven initial focus) before the re-render.
2. **Read** once inside the `render` effect. If non-null, finds the target node and zooms to it.
3. **Cleared** to null right after read (`pendingZoomId.current = null`), so subsequent renders (ResizeObserver, etc.) don't re-zoom.
4. **Guard**: auto-fit zoom is skipped when `pendingZoomId.current !== null`, so the zoom-to-target animation isn't interrupted.

### URL-driven initial zoom

```ts
// In App.tsx render (not effect):
if (!pendingZoomId.current && focusedFamilyId) {
  pendingZoomId.current = focusedFamilyId;
}
```

This sets the ref during initial render when URL has `?family=...`, so the first effect run zooms to the focused family. No click required.

### Stay-in-place zoomAnchorRef

A ref `{ sx: number; sy: number } | null` that saves the target node's screen position BEFORE the click-triggered re-render.

**Set** in the FamilyTree click handler:
```ts
merged.on("click", (_, d) => {
  const cur = d3.zoomTransform(svg);
  // compute target's current screen position
  zoomAnchorRef.current = { sx, sy };
  onSelect(d.data);
});
```

**Read** in the zoom target handler:
```ts
const anchor = zoomAnchorRef.current;
if (anchor) {
  sx = anchor.sx; sy = anchor.sy;
} else {
  // fallback: use current transform
}
```

**Never cleared** — the anchor value persists across Strict Mode double-render (the second render re-reads the same value, and the click hasn't happened again so it's still valid). On the next click, the anchor is overwritten.

The zoom transform is computed to keep the target at (sx, sy) screen position:
```ts
d3.zoomIdentity.translate(sx - tx * scale, sy - ty * scale).scale(scale)
```

### Auto-fit fallback

When `pendingZoomId.current === null` and the tree changed (layout switch or different focus), the tree is auto-fitted:
```ts
d3.select(svg).call(zoom.transform, defaultTransform);
```

`defaultTransform` centers the tree with `d3.zoomIdentity.translate(W/2, H/2)` for radial layout.

### Position transition

On every render, node positions transition:
- `duration(0)` when `layoutChanged` (switching between radial/vertical), preventing the 600ms slide of nodes into a straight line.
- `duration(DURATION)` (600ms) otherwise.

At the end of the effect, if `layoutChanged`, the zoom transform also transitions (600ms) to `defaultTransform`.

### Zoom target animation

The zoom-to-target always uses 700ms duration with `d3.select(svg).transition().duration(700).call(zoom.transform, ...)`.

## 5. Click Handler (`FamilyTree.tsx`)

The merged node group click handler:
1. Computes the target's current screen position using `d3.zoomTransform(svg)`.
2. Saves it to `zoomAnchorRef.current`.
3. Calls `onSelect(d.data)` which triggers App's `handleSelect`.

The handler is refreshed on every render (assigned to `merged.on("click", ...)` inside the effect), so closures over `onSelect` are always current.

## 6. Sidebar / NodeNav (`shared/src/components/NodeNav.tsx`)

### Breadcrumb path

`breadcrumbPath` is computed in App:
```ts
const breadcrumbPath = useMemo(
  () => selected ? getPathToNode(annotatedData, selected.id) : [],
  [selected, annotatedData],
);
```

Walks `annotatedData` (full tree), not `treeData` (pruned). This ensures the path always includes all ancestors (Kingdom → Phylum → Class → Order → Family → Subfamily → Genus → Species).

`NodeNav` filters KINGDOM from display via `SKIP_RANKS`.

Ranks show `commonName` for KINGDOM→FAMILY, scientific `name` for SUBFAMILY+.

### Keyboard navigation

Window-level `keydown` listener:
| Key | Action |
|-----|--------|
| Escape | Collapse family (or class) focus |
| ArrowLeft | Previous sibling (wraps around) |
| ArrowRight | Next sibling (wraps around) |
| ArrowUp | Navigate to parent node |

Skips when focus is on an input/textarea/a element. Only fires when a node is selected.

### Sibling/parent navigation

`navContext` is computed from the pruned `treeData`:
```ts
const navContext = useMemo(
  () => selected ? findNavContext(treeData, selected.id) : null,
  [selected, treeData],
);
```

`findNavContext` locates the selected node in the tree and returns `{ parent, siblings, index }`. This is pruned-context, so siblings only include what's visible.

## 7. Edge Cases

### Strict Mode double-render
- `zoomAnchorRef` is never cleared, so the second effect pass re-reads the same anchor. No stale-position bug.
- `pendingZoomId` is cleared after read, so the second pass skips zoom. Auto-fit for the small pruned tree is close to the zoom target anyway.
- Setup (`setupRef.current`) is initialized once; the guard `if (!setupRef.current)` prevents duplicate DOM inits.

### ResizeObserver
- The `render` callback is also called by a ResizeObserver. Since `pendingZoomId` is always null after the initial effect run, ResizeObserver triggers auto-fit zoom instead of a zoom-to-target.
- SVG dimensions are read fresh on every `render` call (`container.clientWidth/Height`).

### selectedInTree fallback
```ts
const selectedInTree = useMemo(
  () => selected ? (walkFind(treeData, selected.id) ?? selected) : null,
  [selected, treeData],
);
```

If the selected node exists in the pruned tree, uses that reference (so sidebar reads current tree data). If not (e.g., node was selected before pruning), falls back to the annotatedData reference.

### Out-of-family node selection
When a node from a non-focused family is clicked (e.g., clicking a Canidae species while focused on Felidae):
- `handleSelect` detects `node.familySlug !== focusedFamilySlug`.
- Calls `navigateTo(node.familySlug, node.id)` to switch focus.
- Resets all expansion state.
- Sets `pendingZoomId` for zoom-to-target.

### Saved zoom across renders
On every effect cleanup:
```ts
savedZoomRef.current = d3.zoomTransform(svgRef.current);
```

On next init:
```ts
const restoredZoom = savedZoomRef.current ?? d3.zoomIdentity.translate(W/2, H/2);
```

Preserves the viewport across dependency-triggered re-inits (not just unmounts).

## File Map

| File | Responsibility |
|------|---------------|
| `portal/src/hooks/useUrlState.ts` | URL param parsing, pushState, history |
| `portal/src/App.tsx` | handleSelect dispatch, focus/unfocus, keyboard nav, breadcrumb/anchor computation |
| `portal/src/hooks/useUnifiedTree.ts` | tree pruning (overview vs focused), color theme, highlights |
| `shared/src/components/FamilyTree.tsx` | D3 tree layout, zoom (auto-fit + target), click anchor, node rendering, tooltip |
| `shared/src/components/NodeNav.tsx` | breadcrumb path display, sibling/parent navigation |
| `shared/src/components/Breadcrumb.tsx` | (unused in focused mode, legacy) |
