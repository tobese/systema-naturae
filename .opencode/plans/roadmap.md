# Systema Naturae — Development Roadmap

**Target:** 143 families, 8,956 real species. Navigation documented (`docs/navigation.md`). Zero sanity issues.

---

## Phase 1: Data Value — enrich what we have

| What | How | Impact |
|------|-----|--------|
| **Conservation status** | Add IUCN status field to species data (CR/EN/VU/NT/LC/DD) → colored node rings in tree, status filter in sidebar | High — every species gains context at a glance |
| **Species images** | Wire `thumbnailCache` + tooltip image to Wikimedia Commons API via binomial name. Already partially built in FamilyTree tooltip | High — tooltips become visually informative |
| **Wikipedia descriptions** | Connect `useWikipediaSummary` hook to UnifiedInfoPanel. Hook and Wikipedia API call exist, just not rendered in the panel | Medium — species pages get auto-generated summaries |
| **Pending eponyms** | Import 5 "David Attenborough" species from `shared/data/pending-eponyms.json`. Requires adding 5 new data-only families (tachyglossidae, cordylidae, polioptilidae, libellulidae, nothobranchiidae) | Low effort, closes a data gap |

## Phase 2: Geographic & Discovery

| What | How | Impact |
|------|-----|--------|
| **Continent/range viz** | Wire `continents[]` data to `HabitatMap` — highlight distribution for selected node. Currently species have continent data but map is static | High — unlocks the geographic dimension |
| **Continent-filtered tree** | Click a continent region → `highlightedContinent` set → only matching species shown at full opacity. Already partially built: `highlightedNodeIds` + `highlightedContinent` in useUnifiedTree | Medium — exploration by region |
| **Search improvements** | Fuzzy matching, filter-by-rank/class, show conservation badge in search results | Medium — search is functional but basic |

## Phase 3: Content Growth

| What | How | Impact |
|------|-----|--------|
| **New family batches** | Pick under-represented classes (Actinopterygii has 6/400+ families; Insecta has 1 family) and add curated real species | High — coverage expands |
| **Full-app conversion** | Promote data-only families with rich data to standalone apps (App.tsx, colors.ts, vite.config.ts). Pattern: felidae, canidae | Medium — enables standalone dev workflow |
| **Pending eponym families** | Add the 5 families from `shared/data/pending-eponyms.json` as data-only families with the Attenborough species | Low effort, unblocks eponyms |

## Phase 4: Polish & Infrastructure

| What | How | Impact |
|------|-----|--------|
| **Deployment** | Static export → GitHub Pages or Vercel | High — shareable |
| **Mobile responsive** | Collapse sidebar on narrow viewports, touch-friendly tree zoom | High — usable on tablets/phones |
| **Keyboard shortcuts** | `/` focus search, Arrow keys navigate results, `f` focus current family, `n`/`p` next/prev species | Medium — power-user flow |
| **Tree transitions** | Smoother species enter/exit, consistent 600ms D3 transitions across all state changes | Low — polish |
