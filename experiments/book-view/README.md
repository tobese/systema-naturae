# Book View — prototype

A standalone, decoupled experiment: read the animal kingdom as a book, inspired
by (not a replica of) Linnaeus's *Systema Naturae*. See
`/Users/tb/.claude/plans/checkup-on-the-real-whimsical-marshmallow.md` for the
full design rationale and background.

This is **not** wired into the portal, but it does read the portal's real data
files directly (read-only, via a symlink) rather than a duplicated copy — see
"Data architecture" below.

## Setup

```bash
npm install
npm run extract-data   # rebuilds the small public/data/extensions/*.json sidecars
npm run dev
```

`extract-data` runs `scripts/extractSlice.ts`, which reads
`portal/public/data/kingdoms/animalia/orders/*.json`,
`portal/data/gap-report.json`, and `shared/data/wiki-images.json` from the
repo root and writes one small sidecar per chapter to
`public/data/extensions/${orderFile}.json` (portrait images, IUCN status,
`chapterStats`, curated Family-level prose, and — for curated Parts only —
the family whitelist). Re-run it any time upstream portal data changes.

## Data architecture

`public/data/portal-orders` is a **symlink** to
`portal/public/data/kingdoms/animalia/orders` — the app's base species-tree
data is the portal's own build output, fetched directly at runtime, never
duplicated into this app's own `public/` tree or committed to git. (This
used to be a full pre-filtered copy per chapter; at Aves' full-order scale
that copy was ~12MB of data that went stale the moment the portal rebuilt,
with nothing keeping it in sync short of remembering to re-run
`extract-data` — see git history on this file for the "before" version if
curious.)

**Second kingdom (2026-08-21):** `public/data/portal-plantae-orders` is the
same pattern pointed at `portal/public/data/kingdoms/plantae/orders-plantae`
(237 order files, each named `ORD_<SLUG>.json` uniformly — the portal's
`order-manifest.json` supplies clean display names via `orderSlug`, so no
`nameOverrides` guessing was needed the way it was for a handful of Animalia
orders). Extension sidecars for Plantae chapters write to a separate
`public/data/extensions-plantae/` directory so adding the kingdom never
touched any already-verified Animalia output. Every skeleton `Part` and
`Chapter` now carries a `kingdom: "Animalia" | "Plantae"` field (see
`src/types.ts`), and `useBookData.ts`'s `loadChapter` picks the matching
orders-symlink/extensions-dir pair from it.

At runtime, `src/hooks/useBookData.ts`'s `loadChapter` fetches the portal
order file (via the kingdom-appropriate symlink) and the matching small
extensions sidecar in parallel, then `src/lib/decorateChapter.ts` merges
them in one client-side tree walk: strips corrupted
`enrichFromWikipedia.ts` extracts (raw `{{Speciesbox|...}}` markup,
`Category:` links, `#REDIRECT` pages — disproportionately common on
fossil/extinct species), attaches portrait images/IUCN status, injects
Family-level `description` (see below), and - for curated Parts only -
filters down to the whitelisted families.

## Family/Genus/Order prose

Checked directly against the portal's real data: `ORDER` nodes already carry
real hand/AI-written `description` prose (rendered as-is, e.g. Carnivora:
*"Despite the name, Carnivora is defined by shared ancestry..."*), and so do
most `GENUS` nodes (e.g. Paridae's `Parus`: *"The great tits — large, bold
members of the family..."*) - both were already in the data but Genus prose
was never rendered until now. `FAMILY` nodes have **no** `description` field
anywhere in the portal's data, but do carry a `notableMembers: string[]`
array. So: `FamilySection.tsx` now renders `genus.description` when present,
and for Family, renders `family.description` when present (sourced from
`src/familyIntros.ts` - ~30 hand-written entries from when
Chondrichthyes/Reptilia were still small hand-curated Parts) or falls back
to a "Notable: ..." line from `notableMembers` when no prose exists yet. Now
that the book covers every class in both kingdoms (see "Scope" below), the
vast majority of families have no hand-written intro and fall back to
`notableMembers` (or nothing, for Plantae) - a follow-up LLM enrichment pass
targeting `FAMILY`-rank `description` in
the portal's own data (the same kind of pass that already produced the
Order/Genus prose) would benefit every consumer, not just this
app, and is a separate task from anything in `experiments/`.

**Plantae prose is real but thinner.** Species descriptions are POWO-sourced
boilerplate (*"The native range of this species is China (Zhejiang). It is a
tree and grows primarily in the temperate biome."*), and `GENUS` nodes carry
a generic placeholder (*"Pinus — a genus of pinopsidas."*) rather than real
prose like Animalia genera. `FAMILY` nodes have neither a `description` nor
a `notableMembers` array at all - `FamilySection.tsx`'s existing fallback
chain just renders no Family-level prose for any Plantae family (not
broken, same graceful path an Animalia family without a `familyIntros.ts`
entry already takes).

## Class-level prose + species collage (added 2026-08-21)

Every Part already had a rendering slot for an intro paragraph
(`ChapterPage.tsx`'s `showPartIntro` header, above "Chapter 1") - it just
almost never had anything to show. `src/curatedParts.ts`'s `PART_INTROS` map
had exactly 4 hand-written entries (Mammalia, Aves, Chondrichthyes, Reptilia)
out of 118 Parts; everywhere else it silently rendered `""`. Checking the
real source data directly: `CLASS.description` and `ORDER.description` both
live in `portal/data/taxonomy.json` (Animalia) /
`portal/data/taxonomy-plantae-snippet.json` (Plantae) - and **57 of 75
Animalia classes (76%) plus 280 of 383 Animalia orders (73%)** had no
`description` at all. Plantae, by contrast, was already essentially fully
described (0/43 classes, 10/237 orders missing).

**`scripts/enrichHigherRanksFromWikipedia.ts`** (new, root-level, sibling to
`scripts/enrichFromWikipedia.ts`) fills these in from the **live** Wikipedia
API - not the offline SQLite dump, which turned out not to be a general
mirror: `scripts/buildWikipediaDb.py` only ever imports pages matching a
species-name candidate list, confirmed empty for `"Insecta"`,
`"Coleoptera"`, `"Gastropoda"`, etc. At only ~347 remaining lookups
(57+280+10), the live API alone is fast (`fetchBatch()` reuses
`enrichFromWikipedia.ts`'s proven batch-of-50/1.5s-throttle mechanics,
trying the scientific name first, then `commonName` as a fallback title -
both CLASS and ORDER nodes already carry one, e.g. `Coleoptera` →
`"Beetles"`). Idempotent, never fabricates (a miss is left empty). First
run: **226/337 Animalia** filled, **0/10 Plantae** (the 10 remaining are
obscure fossil algae orders genuinely absent from Wikipedia - correctly
left empty rather than invented). Also strips a recurring Wikipedia-extract
artifact (a stray leading `(;` or empty `()` where an IPA-pronunciation
template got stripped) that showed up in a couple of results, e.g.
`"Bivalvia () or..."` → `"Bivalvia or..."`.

This writes back into the two taxonomy source files directly - real,
portal-wide data (the live deployed animal portal reads `taxonomy.json`
too), so re-run `cd portal && sh scripts/buildData.sh &&
SN_KINGDOM=plantae sh scripts/buildData.sh` afterward to graft the new
descriptions into the generated order files before `npm run extract-data`
picks them up.

**Book-view side:** `extractSlice.ts`'s `buildKingdomParts()` now also loads
the relevant taxonomy file per kingdom (`loadClassDescriptions()`) and
attaches each class's description to its Part's skeleton entry.
`App.tsx` prefers the hand-written `PART_INTROS` entry when one exists,
falling back to this real data otherwise - so the 4 original hand-written
intros are untouched, not overwritten by a generic Wikipedia paragraph.

**Species collage:** alongside the description, each Part's skeleton also
carries a `collage: { name, commonName, imageUrl }[]` (a **9x9 plate, 81
entries**) - species with *both* a real (non-stub) description *and* a
portrait image, sampled evenly across every chapter in the Part
(`collectCollageCandidates` + `sampleEvenly()` in `extractSlice.ts`,
deterministic, no randomness, so `extract-data` output stays reproducible
run to run). No new upstream data needed - this reuses the same per-chapter
`images` map (sourced from `shared/data/wiki-images.json`)
`extractSlice.ts` already built for species-level portraits. New
`src/components/PartCollage.tsx` renders it as a strict 9-column CSS grid
in the same `showPartIntro` header block, reusing `SpeciesEntry.tsx`'s
`object-fit: contain` + paper-shadow-background treatment (see the
shark-image-cropping fix above) so collage photos of elongated animals
don't lose their nose/tail either.

**Curated placements for flagship Parts** (`src/collageOverrides.ts`,
consumed by `extractSlice.ts`'s `buildCollage()`): a class can pin specific
species at specific grid slots, with an optional `center` forced to index
40 (the exact middle of the 9x9 grid, row-major) - everything else in the
grid still auto-fills from the same real, evenly-sampled candidate pool.
Every name in `collageOverrides.ts` was confirmed to exist with a real
portrait image in the actual data before being added - none fabricated or
assumed.
- **Mammalia**: `Homo sapiens` centered, surrounded by *Gorilla gorilla*
  (largest living primate), *Balaenoptera musculus* (blue whale - largest
  animal ever known), *Suncus etruscus* (Etruscan shrew - smallest mammal
  by mass), *Giraffa camelopardalis* (tallest living animal), *Acinonyx
  jubatus* (cheetah - fastest land mammal), *Loxodonta africana* (African
  bush elephant - largest land animal), *Physeter macrocephalus* (sperm
  whale - deepest-diving mammal).
- **Aves**: no natural "center" analog for birds the way a human centers
  Mammalia, so this Part pins ten record-holders with no forced center -
  *Struthio camelus* (ostrich, largest/heaviest bird), *Mellisuga minima*
  (vervain hummingbird - among the smallest living birds; the actual
  smallest, the bee hummingbird, has no portrait in the data, so this is
  the honestly-labeled second-smallest rather than a misattributed claim),
  *Falco peregrinus* (fastest animal alive, diving), *Diomedea exulans*
  (largest wingspan of any living bird), *Haliaeetus leucocephalus* (bald
  eagle), *Corvus corax* (common raven, most intelligent bird),
  *Sterna paradisaea* (Arctic tern - longest migration of any animal),
  *Pavo cristatus* (peacock), *Aptenodytes forsteri* (emperor penguin -
  deepest-diving bird), *Apteryx australis* (kiwi).

Verified live in Chrome: Mammalia's 9x9 grid shows all 7 pinned
record-holders in row 1 with *Homo sapiens* exactly centered in row 5
(confirmed both by array index 40 in `book-skeleton.json` and visually,
flanked symmetrically); Aves' grid shows all 10 pinned birds across row 1.
Insecta (a class with no override, previously zero intro at all) shows a
real paragraph and a full 81-photo collage above Chapter 1; a genuinely
tiny class with no image-bearing enriched species (Xenoturbellida, 2
species) renders with no collage and no intro paragraph - clean
degradation, not an error. 97/118 Parts now have a description, 89/118
have a non-empty collage.

## Scope (v16, 2026-08-21) — full parity with the portal, 118 Parts / 620 Chapters

Through v15 this section hand-enumerated every Part, each with its own
enrichment-% rationale for why it was (or wasn't) included — a curation
model that made sense while the book covered a hand-picked subset of
well-enriched classes. **That model is retired.** The goal is now explicit:
cover the same ground as the portal itself. `scripts/extractSlice.ts` no
longer has a hand-written `PARTS` array at all — `buildKingdomParts()`
generates one Part per class and one Chapter per order **directly from each
kingdom's `order-manifest.json`**, unconditionally, regardless of
enrichment %. Every class with real, built species data in the portal is a
Part in this book:

- **Kingdom Animalia**: all 75 classes / 383 orders (was 15/55).
- **Kingdom Plantae**: all 43 classes / 237 orders (was 7/21).
- Combined: **118 Parts, 620 Chapters**, aggregate species totals verified
  against `docs/Coverage.md`'s published kingdom figures (Animalia 527,703
  vs. ~529,298 published; Plantae 435,111 vs. ~435,114 published — both
  within rounding/snapshot-timing distance, confirming nothing was silently
  dropped in the generation pass).

**Part numbering follows the manifest's own order**, which was verified to
exactly match `taxonomy.json`'s real class sequence — so Part I is still
Mammalia, but Part III is now Reptilia rather than Chondrichthyes (which
becomes Part IV): the *previous* hand-picked ordering didn't follow the
portal's real taxonomic sequence, the generated one does. Nothing in the
app depends on a stable Part number (chapters load by `orderFile`, not Part
index), so this reordering is purely cosmetic. Cephalopoda, previously
Octopoda-only as a deliberate sparse-branch test case, now includes all 11
orders like every other class — there's no more curated/uncurated
distinction.

**Most of the newly added Parts are invisible by default** — this is
expected, not a bug. Most of the 60 newly-added Animalia classes have very
low Wikipedia-description enrichment (Insecta 8.3%, Gastropoda/Bivalvia 0%,
Anthozoa 1.7%, per `docs/Coverage.md`), and `TableOfContents.tsx` already
filters out any chapter/Part where every family reads `enrichedCount === 0`
whenever "Show empty families" (below) is off. With default toggles, 102 of
118 Parts show in Contents; toggling **Show empty families** on reveals all
118. This is exactly the scenario the toggle was built and validated for
last round (on Cephalopoda/Octopoda) — full parity at real-world data
density needs it turned on to actually see everything.

**Naming collisions no longer need special-casing.** The old
`nameOverrides` mechanism (hand-typed per naming-collision order, e.g.
`SQUAMATA_ORDER` → "Squamata") is gone — `buildKingdomParts()` always reads
the display name from the manifest's own `orderSlug`, which already
resolves every collision correctly (verified: `SQUAMATA_ORDER` →
`orderSlug: "squamata"`, `PERCIFORMES_FISH` → `orderSlug: "perciformes"`).

**Scale realities, verified live, not assumed:**
- `COLEOPTERA.json` (beetles) is **79.7MB**, the single largest order file
  in the portal — opened live in Chrome, loads in a few seconds on
  localhost, renders real content (order description, 95 families, genus
  prose, cited species descriptions), and the scroll-collapse reading
  window still keeps only 2 of 95 families open at a time (~699 mounted
  genus sections, not the full 41,556-species Carabidae family rendered
  flat). Several Gastropoda/insect order files are 6-13MB; none of this
  costs anything until a reader actually opens that specific chapter.
- Production `npm run build` completes in ~4s and produces a 604MB `dist/`
  (this was already true before this round at a smaller scale — Vite
  copies the entire symlinked orders directories since it can't symlink a
  subset; not a new cost introduced here, just now measured at full size).
- Dolphins, Cetacea/Alcedinidae's extra SUBFAMILY→TRIBE layer
  (`FamilySection.tsx`'s `collectGenera()` walks past it generically), and
  every other structural note from earlier rounds still apply unchanged.

Note: Cetacea and Alcedinidae (kingfishers) are modeled in the source
taxonomy with an extra SUBFAMILY(→TRIBE) layer between FAMILY and GENUS,
unlike every other curated family's flat FAMILY→GENUS→SPECIES shape.
`FamilySection.tsx`'s `collectGenera()` walks past non-genus ranks to handle
this generically.

## Options

A ⚙ button in the top-right of the reading shell (`Breadcrumb.tsx` →
`src/components/OptionsPanel.tsx`) opens a small dropdown of three toggles,
all default **off** - mirrors the portal's own `OptionsPanel.tsx` pattern
(gear button → checkbox-row dropdown), restyled for book-view's paper
palette. State lives in `src/context/BookOptions.tsx` (each toggle
independently persisted to `localStorage`), read via
`src/hooks/useBookOptions.ts`.

- **Show extinct species** — `FamilySection.tsx` filters on the
  `extinct`/`fossil` flags at species and genus granularity; a genus
  that's entirely extinct (e.g. Felidae's *Smilodon*, *Proailurus*)
  disappears completely rather than showing an empty heading, and genus
  numbering stays contiguous around whatever's hidden.
- **Show stub species** — reveals the plain "Also in this genus: ..." name
  list for unenriched species (no real description). Off by default, a
  genus whose species are *all* stubs disappears from the family entirely
  rather than showing a bare "Also in this genus" line with nothing above
  it.
- **Show empty families** — reveals families with zero enriched species
  (`chapterStats.enrichedCount === 0`). Off by default, both in the chapter
  body (`FamilySection.tsx`) *and* in the Contents page
  (`TableOfContents.tsx`, which now consumes `useBookOptions()` too) - a
  chapter or Part that has no *non-empty* families left after filtering
  disappears from Contents entirely, so the reading list only ever shows
  destinations with something to actually read. Note the two toggles
  interact in the chapter body: a family with zero enrichment has no
  content to show at all unless *both* "Show empty families" and "Show
  stub species" are on together (stats-only families with nothing but a
  stub list need stubs visible to render anything below the header) -
  "Show empty families" alone mainly changes what's *listed* in Contents.

Validated together against a deliberately "sparse branch" - Octopoda (then
the whole of Part XV Cephalopoda), 7 of 19 families with zero enrichment -
confirmed live in Chrome: Contents lists 12/19 families by default, all 19
with "Show empty families" on; the chapter body mounts 11/19 `<details>` by
default with zero stub-list paragraphs, 19/19 with both toggles on.
Re-confirmed at full-book scale (v16): with default toggles, 102 of 118
Parts appear in Contents; "Show empty families" reveals all 118.

## Scaling notes

`src/hooks/useBookData.ts` mirrors `portal/src/hooks/useTaxonomyLoader.ts`'s
skeleton + on-demand-fetch + LRU-cache pattern, at Chapter (= taxonomic
Order) granularity. Now that Aves fetches the portal's real order files
directly (see "Data architecture"), the biggest single fetch is Passeriformes
at ~5MB - well within what a lazy per-chapter fetch can absorb.

## Large chapters: scroll-driven collapse

Passeriformes alone carries 146 families and ~3,200 fully-enriched species -
too many `SpeciesEntry` components (each with a lazy-loaded image,
description, badges) to mount all at once in one continuous scroll.
`src/hooks/useReadingWindow.ts` + `FamilySection.tsx` solve this with a
scroll-driven "reading window": only the family currently crossing the top
of the viewport, plus one before and one after, stay expanded (fully
mounted) - everything else collapses to just its header
(`<details>`/`<summary>`, always mounted; the body is conditionally
rendered, a real unmount, not CSS-hide). One shared `IntersectionObserver`
per `ChapterPage` instance drives it (a scrollspy watching a thin trigger
band near the top of the viewport), not one observer per family.

Clicking a collapsed family's header pins it open (via `readingWindow.pin`);
a pin auto-releases once scrolled well past. Verified live in Chrome on
Passeriformes: deep-scrolling through Corvidae → Turdidae → Fringillidae
correctly collapses earlier families (mounted `<img>` count stays in the
tens/hundreds, not thousands) and re-expands them scrolling back up.

Two real bugs were found and fixed building this (both instructive if this
pattern gets reused elsewhere in the app):
1. **Observer-timing bug**: creating the `IntersectionObserver` inside a
   `useEffect` meant it was still `null` the first time ref callbacks fired
   (refs attach during commit, *before* effects run) - every family observed
   nothing, so the window never advanced regardless of scroll position.
   Fixed by queuing elements that mount before the observer exists and
   flushing the queue once it's created.
2. **Ref-churn perf bug**: an inline `ref={registerSentinel(slug)}` created a
   new closure every render, so React detached+reattached every family's ref
   on every render, each reattach re-triggering `.observe()` (which queues a
   fresh notification) - at 145+ families this became a render loop that
   froze the tab. Fixed by caching one stable callback per slug.
3. **Over-eager pinning bug**: the native `toggle` event fires for *any*
   `open` attribute change, including React setting it from scroll position
   - not just real clicks - so every family that ever became scroll-active
   got permanently pinned, and nothing ever collapsed. Fixed by pinning from
   a `click` handler on `<summary>` instead of the `toggle` event, which
   only fires for genuine user interaction.
