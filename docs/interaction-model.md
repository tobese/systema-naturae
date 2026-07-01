# Interaction Model — Click Behavior by Node Type

This document describes exactly what happens when a user clicks a taxonomic node, covering every rank, every entry point, and every context modifier.

## 1. Click Entry Points

| Entry point | Mechanism | Ranks that trigger `handleSelect` | Notes |
|---|---|---|---|
| **Graph** (SVG tree) | `merged.on("click")` → `onSelect(d.data)` | ALL ranks | Saves `zoomAnchorRef` before dispatch for stay-in-place zoom |
| **Sidebar** (TaxonomySidebar) | `li.onClick` → `toggle()` + `onSelect()` | KINGDOM, PHYLUM, CLASS, FAMILY | Deeper ranks (ORDER–SPECIES) only toggle expand in the sidebar |
| **BookView** | `button.onClick` → `onSelect()` + `toggle()` | ALL ranks | Every click calls `onSelect` AND toggles expand |
| **NodeNav breadcrumb** | `span.onClick` → `onNavigate()` | All ancestors of selected node | KINGDOM filtered out via `SKIP_RANKS` |
| **NodeNav sibling arrows** | `button.onClick` → `onNavigate()` | Siblings (any rank) | Wraps around (first←→last) |
| **StatisticsHeader pills** | `span.onClick` → `onSelect()` | All ranks in ancestors path | Compact breadcrumb (KINGDOM filtered out) |
| **SearchBox results** | `li.onClick` → `onNavigate()` | Any rank | Navigates to family+node or just node |
| **Modal links** (SpeciesOfTheDay, EponymModal, WheelOfNature) | `button.onClick` → `navigateTo(slug, id)` | Any rank | Sets family+node; does NOT go through `handleSelect` |
| **Keyboard** | `keydown` listener | Current selection's siblings/parent | Escape, ArrowLeft/Right/Up, C/Home, Q/E |

## 2. Rank Behavior Matrix

Each row: what `handleSelect` does when a node of this rank is clicked from **any** entry point that dispatches `handleSelect`.

| Rank | URL effect | Focus effect | Zoom | Select toggle | Expand toggle (in tree view) |
|---|---|---|---|---|---|
| **KINGDOM** | `?node=<id>`, clears `class`, clears `family` | `focusedClassId = null` | Yes (pendingZoomId) | Yes (via `setFocusedClass(null, id)`) | No |
| **PHYLUM** | `?node=<id>`, clears `class`, clears `family` | `focusedClassId = null` | Yes | Yes (via `setFocusedClass(null, id)`) | No |
| **CLASS** (unfocused) | `?class=<id>&node=<id>`, clears `family` | `focusedClassId = id` | Yes | Yes (via `setFocusedClass(id, id)`) | No |
| **CLASS** (focused, click same) | `?class=` removed, `node` cleared | `focusedClassId = null` | Yes | Cleared | No |
| **FAMILY** (unfocused) | `?family=<slug>&node=<id>`, clears `class` | `focusedFamilySlug = slug` | Yes | Yes (via `navigateTo`) | No |
| **FAMILY** (focused, click same) | `?family=` removed, `node` cleared | `focusedFamilySlug = null` | No | Cleared | No |
| **ORDER** | `?node=<id>` (preserves existing family/class) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **SUBFAMILY** | `?node=<id>` (preserves existing) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **TRIBE** | `?node=<id>` (preserves existing) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **GENUS** | `?node=<id>` (preserves existing) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **BREED_GROUP** | `?node=<id>` (preserves existing) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **HYBRID_GROUP** | `?node=<id>` (preserves existing) | — | Yes (ZOOM_RANKS) | Toggle | No |
| **SPECIES** (no children) | `?node=<id>` (preserves existing) | — | No | Toggle | No |
| **SPECIES** (w/ subspecies) | `?node=<id>` and toggles subspecies | — | Yes (on expand only) | Toggle | Expand/collapse subspecies children |
| **SPECIES** (w/ breeds) | `?node=<id>` and toggles breed group | — | Yes (on expand only) | Toggle | Expand/collapse breed children |
| **SUBSPECIES** | `?node=<id>` (preserves existing) | — | No | Toggle | No |
| **BREED** | `?node=<id>` (preserves existing) | — | No | Toggle | No |
| **HYBRID** | `?node=<id>` (preserves existing) | — | No | Toggle | No |

### Cross-family navigation (applies to all ranks below FAMILY)

If a node has `familySlug !== focusedFamilySlug` when clicked:

| Before | After |
|---|---|
| `?family=felidae&node=GENUS_FELIS` | `?family=canidae&node=CANIS_LUPUS` |
| `focusedFamilySlug = "felidae"` | `focusedFamilySlug = "canidae"` |
| Subspecies/breed expansions reset | Fresh state |
| Zoom to target node | Yes |

This happens **before** any rank-specific logic in `handleSelect`.

## 3. Entry-Point Differences

The same rank behaves differently depending on *where* the click happens.

### Sidebar vs Graph

| Rank | In Graph | In Sidebar |
|---|---|---|
| **ORDER** | Calls `onSelect` → selects node, zooms | Only `toggle()` (expand/collapse). `onSelect` NOT called. |
| **GENUS** | Calls `onSelect` → selects node, zooms | Only `toggle()` (expand/collapse). `onSelect` NOT called. |
| **SPECIES** | Calls `onSelect` → selects node, toggles subspecies/breeds | Only `toggle()` (expand/collapse). `onSelect` NOT called. |
| **SUBSPECIES, BREED, HYBRID** | Calls `onSelect` → selects node | `onSelect` NOT called |

**Reason:** Sidebar `onClick` has a gate: `if (isDeep && hasChildren) toggle(node.id); if (isClass || isFamily || !isDeep) onSelect(node);` where `isDeep = depth >= 3`.

### BookView

BookView calls `onSelect` for **every** rank, including ORDER, GENUS, SPECIES. This differs from the sidebar where deep ranks only toggle.

### SearchBox

Search does NOT call `handleSelect` at all. It calls `onNavigate` (from `useUrlState`) directly:

```
FAMILY result → navigateTo(familySlug, null)    // no node selection
non-FAMILY w/ familySlug → navigateTo(slug, id) // family focus + node selection
no familySlug → navigateTo(null, id)             // node selection only
```

### NodeNav breadcrumb

Each breadcrumb segment (except the last/selected) calls `toNavigate(node)` → `handleSelect(node)`. Kingdom is always hidden.

### NodeNav sibling arrows

"‹" and "›" buttons navigate to the previous/next sibling within the parent. Wraps around (first and last connect).

### StatisticsHeader pills

Each pill in the chain (e.g. "Phylum → Class → Order → Family → Genus") is clickable. Clicking a pill calls `onSelect(node)` → `handleSelect`.

### Modal-driven navigation

- **SpeciesOfTheDayModal**: `navigateTo(slug, id)` — sets family+node, clears class
- **EponymModal**: `navigateTo(slug, id)` — same
- **WheelOfNature**: `navigateTo(slug, id)` — same
- **InternationalDaysModal**: `setFocus(slug)` — sets family only, no node selection
- **CoverageModal**: `setFocus(slug)` — sets family only

All modals skip `handleSelect` and go directly to URL state updaters.

## 4. URL State Transition Reference

### `buildUrl` ordering constraint

Params are always written in this order: `class` first, then `family`, then `node`. If `class` is set, `family` and `node` are omitted. If `family` is set, `class` is cleared.

### Per-action URL output

| Action | URL | `class` | `family` | `node` |
|---|---|---|---|---|
| Click KINGDOM/PHYLUM | `?node=<id>` | cleared | cleared | set |
| Click CLASS (unfocused) | `?class=<id>&node=<id>` | set | cleared | set (= class id) |
| Click CLASS (same, focused) | *(clean)* | cleared | cleared | cleared |
| Click FAMILY (unfocused) | `?family=<slug>&node=<id>` | cleared | set | set |
| Click FAMILY (same, focused) | *(clean)* | cleared | cleared | cleared |
| Click ORDER/GENUS/SPECIES | `?...&node=<id>` | preserved | preserved | toggled |
| Cross-family click | `?family=<new>&node=<id>` | cleared | set | set |
| Escape (family focused) | *(clean)* | cleared | cleared | cleared |
| Escape (class focused) | *(clean)* | cleared | cleared | cleared |
| ← All families button | *(clean)* | cleared | cleared | cleared |
| Search FAMILY result | `?family=<slug>` | cleared | set | cleared |
| Search non-FAMILY result | `?family=<slug>&node=<id>` | cleared | set | set |

## 5. Node Properties That Affect Behavior

| Property | Effect on click |
|---|---|
| **`hasChildren`** | If `true` and `isDeep` in sidebar → toggles expand/collapse in addition to selection. In BookView → always toggles expand regardless of rank. |
| **`speciesList`** (compressed species array on GENUS) | Species inside `speciesList` still render as clickable SVG nodes. `findNavContext` includes them as siblings. `walkFind` finds them in the full tree. |
| **`extinct`** | Filtered out of `filteredTreeData` when `showExtinct` is `false` (default). These nodes cannot be clicked from the graph. They remain in the sidebar and in `taxonomyData`. |
| **`familySlug`** | Determines cross-family navigation guard. If `null`/`undefined`, cross-family check is skipped (can't navigate to an unknown family). |
| **`subspeciesCount`** | Used in `speciesList` nodes to decide whether to render a subspecies hint ring in the graph. Does NOT directly affect click behavior (the ring is visual only). |
| **`iucnStatus`** | Renders an IUCN-colored ring in graph. Visual-only, no click effect. |
| **`namedAfter`** | Displayed in tooltip and EponymModal. No click effect. |
| **`sourcedFrom`** | Used by OptionsPanel "Highlight Wikipedia species" toggle. No direct click effect. |
| **`continents[]`** | Used by highlight toggle for continent filtering. No direct click effect. |

## 6. Sidebar Behavior Details

### `showChildren` gate (which ranks render their children)

| Parent rank | Children visible when |
|---|---|
| KINGDOM | Always (shows phyla) |
| PHYLUM | Always (shows classes) |
| CLASS | Always (shows orders) |
| ORDER | Only when `focusedClassId !== null` |
| FAMILY | Always (if expanded) |
| SUBFAMILY / TRIBE / GENUS / SPECIES | Only when `focusedFamilySlug !== null` AND node's `familySlug` matches |

### `onClick` gate (which ranks call `onSelect`)

| Rank | `isDeep` (depth ≥ 3) | Calls `onSelect` | Calls `toggle()` |
|---|---|---|---|
| KINGDOM | No | Yes | No |
| PHYLUM | No | Yes | No |
| CLASS | No | Yes | No |
| ORDER | Yes | No | Yes (if has children) |
| FAMILY | Yes | Yes | Yes (if has children) |
| SUBFAMILY | Yes | No | Yes (if has children) |
| GENUS | Yes | No | Yes (if has children) |
| SPECIES | Yes | No | Yes (if has children) |

### Auto-expansion triggers

| Event | Sidebar auto-expands |
|---|---|
| Class focused | The focused class and all ORDER/FAMILY/PHYLUM ancestors |
| Family focused | The focused family's ancestors and all GENUS children |
| `selectedId` changes (BookView) | All ancestors of the selected node |

## 7. Keyboard Navigation

| Key | Context | Action |
|---|---|---|
| `Escape` | Family focused | Unfocus family (back to overview) |
| `Escape` | Class focused (no family) | Unfocus class |
| `c` / `C` / `Home` | Node selected | Center graph on selected node, show temporary tooltip |
| `q` / `Q` | Radial layout | Rotate tree -15 degrees |
| `e` / `E` | Radial layout | Rotate tree +15 degrees |
| `ArrowLeft` | Node selected | Previous sibling (wraps around) |
| `ArrowRight` | Node selected | Next sibling (wraps around) |
| `ArrowUp` | Node selected | Navigate to parent node |

Keyboard events are ignored when focus is on `INPUT`, `TEXTAREA`, or `A` elements.

## 8. Edge Cases

### Strict Mode double-render (React)

- `zoomAnchorRef` is never cleared, so the second effect pass reads the same anchor — no stale-position bug.
- `pendingZoomId` is cleared after read → second pass skips zoom. Auto-fit for the small pruned tree is close enough.

### `selectedInTree` fallback

If the selected node exists in the pruned tree (with family focus), the pruned-tree version is used. If not (node is outside focused family), falls back to the full-tree reference. This ensures the sidebar always shows the correct tree-branch version.

### ResizeObserver

Triggers the render callback. Since `pendingZoomId` is always null after initial zoom, ResizeObserver triggers auto-fit zoom, not a zoom-to-target.

### Species with mixed children

A species can have both SUBSPECIES and BREED_GROUP children. Each is toggled independently via `expandedSubspeciesIds` and `expandedBreedIds`. The first click on a species with subspecies expands subspecies; a second click on the same species collapses them.

### `speciesList` compressed nodes

Genus nodes with compressed `speciesList[]` render those species as clickable SVG nodes with `data-rank="SPECIES"`. Clicking them behaves identically to clicking a physical species node — they go through `handleSelect`, get the cross-family check, etc. `findNavContext` treats them as siblings alongside physical children.
