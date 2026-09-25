# Book integration plan — replacing the portal's Book view with the standalone book

Status: **phases 1–4 done** (2026-09-25); only the book-mode right-panel design is open.
Related: [`navigation.md`](./navigation.md), [`SESSION-2026-09-25.md`](./SESSION-2026-09-25.md).

## The two "books"

| | Integrated (in portal) | Standalone (`experiments/book-view`) |
|---|---|---|
| Component | `portal/src/components/BookView.tsx` (349 lines) | `experiments/book-view/src/App.tsx` + components |
| Data | the grafted/compressed `unified-taxonomy.json` (passed in as `filteredTreeData`) | per-order files `data/kingdoms/<kingdom>/orders/<ORDER>.json` + a small generated `extensions/` sidecar, merged at runtime by `decorateChapter()` |
| Look | inherits the portal's dark dashboard chrome | its own paper palette (`--paper #f3ead4`, `--ink`, `--rule-gold`, per-class accents) |
| Content | a collapsible tree of the focused subtree | book reading experience: Parts → Chapters (orders) → family `<details>` sections → species entries with portraits, IUCN badges, breed groups, synonym links |
| Perf | renders whatever is focused | scroll-driven "reading window" (`useReadingWindow`) keeps only ±1 family mounted, so Passeriformes (~3,200 species) stays responsive |
| Navigation | portal `viewMode` toggle in the header | own phase machine: cover → TOC → kingdom intro → chapter, plus a fore-edge index |

The integrated one is a tree browser with a "Book" label. The standalone one is the actual book.
This plan replaces the former with the latter **inside the portal shell**, and leaves the
standalone app working as its own thing for now.

## Decisions (agreed)

1. **In-shell replacement.** Keep the portal's existing `📖 Book` `viewMode` button and swap its
   guts for the standalone book's reading surface. The book is *not* a separate route/iframe —
   it renders inside the portal frame so graph and book stay siblings sharing the header, kingdom
   selection and selection state.
2. **Right Details tab: graph-only for now.** The right panel (HabitatMap + StatisticsHeader +
   NodeNav + UnifiedInfoPanel) is a *graph* affordance. It already only shows a toggle button in
   graph mode, but the panel itself still renders in book mode and steals 380px, because
   `handleSelect` auto-opens it on any selection. Gate both to graph mode and leave the book a
   full-width reading column. Design a proper book-mode right panel later (see "Open questions").
3. **Design doc first** (this file), then implement in reviewable phases.
4. The standalone app keeps working untouched throughout — it is the reference implementation and
   the visual regression target. Nothing in phases 1–3 may break it.

## Why the book needs its own data path (and why that's fine)

The book deliberately does *not* read `unified-taxonomy.json`. That file is **compressed**: every
genus's minimally-described species are flattened into a `speciesList[]` to keep the bundled tree
small, and family data is grafted in. The book needs the *uncompressed* per-order trees so it can
render every species as its own entry with its image, IUCN badge, subspecies count, breed groups,
and "Also in this genus: …" stubs.

The portal already ships those uncompressed per-order files at
`portal/public/data/kingdoms/<kingdom>/orders/<ORDER>.json`, and book-view reaches them through a
symlink (`experiments/book-view/public/data/portal-orders` → the same directory). So both apps can
read the *same* order files — no duplication of the species tree.

The only thing the portal doesn't yet serve is the generated `extensions/` sidecar and
`book-skeleton.json` (currently generated into `experiments/book-view/public/data/`).

## Phases

### Phase 1 — Gate the right Details panel to graph mode — **DONE**

- `portal/src/App.tsx`:
  - the panel block (`{showRightSidebar && …}`, ~line 999) is now
    `{showRightSidebar && viewMode === "graph" && …}`;
  - the auto-open on selection (~line 168) is guarded by `viewMode === "graph"`, so selecting a
    species while reading no longer pops a graph panel over the text.
- Effect: book mode is a clean full-width reading column; graph behavior (including the panel's
  remembered open state) is unchanged.
- Verified: Playwright probe — graph+select → 380px panel; switch to Book → gone; back to Graph →
  returns. Full portal suite **35/35 green**, zero page errors.

### Phase 2 — Relocate the book reading surface to `shared/src/book/` — **DONE**

Moved (via `git mv`, internal layout preserved so relative imports inside the moved tree kept
resolving untouched) to `shared/src/book/`:
- `types.ts` (BookNode / ChapterDoc / ChapterExtensions)
- `components/{ChapterPage,FamilySection,SpeciesEntry,PartCollage}.tsx`
- `hooks/{useReadingWindow,useBookOptions}.ts`
- `context/{BookOptions.tsx,bookOptionsContext.ts}`
- `lib/{decorateChapter,synonyms,paragraphs,chapterVisibility}.ts`

Stayed in `experiments/book-view/src/` (the standalone's shell): `App.tsx`, `main.tsx`,
`components/{CoverSplash,TableOfContents,ForeEdgeIndex,KingdomIntroPage,Breadcrumb,OptionsPanel}.tsx`,
`hooks/useBookData.ts`, and the content tables `curatedParts.ts` / `kingdomIntros.ts` /
`familyIntros.ts` / `collageOverrides.ts` (the last two are also imported by
`scripts/extractSlice.ts`, which has no alias mapping — so they must stay local).

Notes:
- Fixed a latent bug: `experiments/book-view/tsconfig.app.json` mapped `@shared/*` to
  `../shared/src/*` — right for `portal/` (one level deep) but wrong for `experiments/book-view/`
  (two). It was never exercised because the book had no `@shared` imports until now. Now `../../shared/src/*`.
- The book's `localStorage` keys (`book-view:show-extinct`, …) were deliberately left alone so
  existing users' saved toggles survive.
- Verified: standalone `npm run typecheck` clean, portal `tsc -b` clean, and a Playwright probe of
  the standalone (cover → TOC → CARNIVORA) renders 5 families / 182 images with zero page+console
  errors — byte-for-byte the same reading surface as before the move.

### Phase 3 — Render the reading surface in the portal's Book mode — **DONE**

- `portal/src/hooks/useBookChapters.ts` — the portal's data hook. Fetches the skeleton once, then
  per chapter: the order file from `data/kingdoms/<kingdom>/orders[-suffix]/<ORDER>.json` (already
  generated by `buildData.ts`) and the sidecar from `data/book/extensions[-suffix]/<ORDER>.json`,
  then merges them with the shared `decorateChapter()`. LRU-capped chapter cache. The
  skeleton→node join is on `orderName`, case-insensitively (portal nodes carry the lowercase stem
  `"carnivora"`, the skeleton `"Carnivora"`), **scoped to the active kingdom** — the skeleton spans
  every kingdom but a portal build serves one.
- `portal/src/components/BookReadingPane.tsx` — mounts the shared `ChapterPage` inside a
  `.book-surface` scroll container (the reading window's IntersectionObserver needs the pane to be
  the scroll root), wrapped in `BookOptionsProvider`. Falls back to the active part's first visible
  chapter when nothing is selected; shows the part intro (title/prose/collage) only on that first
  chapter, matching the standalone's rule.
- `portal/src/App.tsx` — the `viewMode === "book"` branch renders `<BookReadingPane>` with
  `orderName={selected?.orderName}` and `focusFamilySlug={selectedInTree?.familySlug ?? focusedFamilySlug}`,
  so the book opens on the chapter/family the reader is actually looking at.
- `shared/src/book/book.css` — the palette + page typography, declared on `:root, .book-surface`
  (standalone keeps it app-wide; the portal's pane re-declares it, so the dark chrome and the paper
  page can't meet). Verified safe: the portal defines and references **no** custom properties
  today, so there is nothing to collide with. The standalone's `index.css` now keeps only its shell
  rules and imports the shared sheet from `main.tsx` (a bare-alias CSS `@import` isn't reliably
  resolved by Vite; a JS import is).
- `shared/src/book/hooks/useReadingWindow.ts` + `components/ChapterPage.tsx` — optional
  `focusFamilySlug`: the window starts centred on that family, pins it, and scrolls it into view on
  mount. Undefined in the standalone, whose behaviour is unchanged.
- **Data canonicalised** so there's one copy and no drift: `extractSlice.ts`'s `OUT_DIR` is now
  `portal/public/data/book/` (override with `SN_BOOK_OUT`), the standalone's
  `public/data/{book-skeleton.json,extensions*}` became symlinks to it (same pattern as its
  existing `portal-orders` symlinks), and `portal/public/data/book/` is **gitignored** — the
  sidecars are generated data, exactly like the per-order files they decorate (that untracking
  drops ~17MB of generated JSON from the repo). Because the target no longer exists in a fresh
  clone, both apps self-heal: `portal/scripts/ensureBookData.sh` runs before `dev` (only when
  missing) and always before `build`; the standalone has a `predev` hook calling the same script.
- Verified: selecting a node then switching to Book opens that order's chapter (e.g. `?node=RODENTIA`
  → "Chapter 8 — Rodentia", families Muridae/Sciuridae/Cricetidae/Castoridae/Caviidae); with nothing
  selected it opens "Part I — Mammalia" + the 49-tile collage and Carnivora's 5 curated families.
  Pane computes `background #f3ead4`, EB Garamond body / Cormorant headings; no right panel; zero
  page errors. Portal suite 35/35 green. Fresh-clone simulation (deleted the data dir, ran
  `ensureBookData.sh`): rebuilt all 1,101 sidecars + skeleton, both apps served correctly after.

### Phase 4 — Retire the old integrated BookView — **mechanical part done**

- `portal/src/components/BookView.tsx` deleted (nothing imported it once the pane landed). Portal
  typecheck clean, suite 35/35 green.
- **Still open:** what the right panel becomes in book mode — see "Open questions".

## Notes for the next session

- Image loading in the book is `loading="lazy"`: measuring "how many images are there" right after
  a chapter opens reads as ~0 loaded. Wait ~5s, or scroll, before concluding images are broken
  (this fooled two probes).
- Both apps read the book data from `portal/public/data/book/`; if the sidecars look stale, run
  `sh portal/scripts/ensureBookData.sh --force` (or `npm run extract-data` in
  `experiments/book-view`, which writes to the same place).
- The generator still lives in `experiments/book-view/scripts/extractSlice.ts` and the portal's
  build shells out to it. If the standalone is ever retired, move the generator into
  `portal/scripts/` and the four content tables (`curatedParts`, `kingdomIntros`, `familyIntros`,
  `collageOverrides`) into `shared/src/book/`.

## Open questions (decide after phase 3, with the real thing in front of us)

- **What replaces the right tab in book mode?** The Details panel is graph-centric
  (HabitatMap/NodeNav/graph navigation). For a book, candidates: a "you are here" chapter
  navigator mirroring the left TaxonomySidebar; a persistent species card for the current
  selection (so clicking a species in the graph and reading it in the book keeps context); or
  nothing (full-bleed page) with the details folded into the entry itself (it already shows
  description, IUCN, continents, eponyms).
- **How much of the standalone's chrome travels?** Cover splash / fore-edge index are lovely but
  are an *app*, not a *pane*. Likely: keep the paper page + reading window + typography in the
  portal; leave cover/TOC/fore-edge to the standalone.
- **Standalone's long-term home.** It stays a first-class app (its own URL/deploy) or gets folded
  into the portal as a route later. Out of scope for phases 1–4.
- **Should the book navigate the portal?** The reading surface takes clicks for images
  (hover/lightbox) and Wikipedia links, but a species click doesn't yet drive portal selection.
  Wiring that (entry → `onSelect`, so reading and graph stay in sync) is the obvious next
  integration step, and probably belongs with the right-panel decision.

## Risks / notes

- **Dual React.** Both apps are React 19.2.6 + Vite 8 + TS 6 — identical, so moving components
  into `@shared` compiles under either app's toolchain with no version skew.
- **CSS scoping.** The book styles assume its own paper page. Wrap the portal-mounted surface in a
  `.book-surface` container (paper background, serif measure) so the dark shell frames it rather
  than the reverse.
- **Scroll containment.** The portal's main column is `overflow: hidden` with internal scroll
  containers; the reading window's IntersectionObserver needs the *book pane* to be the scroll
  root. Make the book pane the scrolling element in phase 3.
- **Extensions freshness.** `extract-data` must run before the portal's book mode has images/stats;
  hook it into the portal's existing `buildData.sh` chain so a normal `npm run dev`/`build` keeps
  the sidecar in sync.
- **Kingdom builds.** Portal builds are per-kingdom (`SN_KINGDOM`); the book skeleton spans all
  kingdoms. Filter by active kingdom in phase 3.
- **Known flake (pre-existing, not from this work).** `tests/thumbnails.spec.ts` ("species panel
  reserves space and fades in the thumbnail") fails intermittently in full-suite runs (~2 of 3)
  while always passing in isolation — it asserts on a CSS fade-in with an artificial 700ms image
  delay, so it is sensitive to machine load. Same species of problem as the genus-centering test
  fixed earlier in this project. Worth stabilising (wait for image `complete` rather than polling
  opacity) if it keeps costing time.
