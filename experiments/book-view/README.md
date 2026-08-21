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

At runtime, `src/hooks/useBookData.ts`'s `loadChapter` fetches the portal
order file (via the symlink) and the matching small extensions sidecar in
parallel, then `src/lib/decorateChapter.ts` merges them in one client-side
tree walk: strips corrupted `enrichFromWikipedia.ts` extracts (raw
`{{Speciesbox|...}}` markup, `Category:` links, `#REDIRECT` pages —
disproportionately common on fossil/extinct species), attaches portrait
images/IUCN status, injects Family-level `description` (see below), and
- for curated Parts only - filters down to the whitelisted families.

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
that every Part is complete (391 families across 14 classes), the
great majority have no hand-written intro and fall back to `notableMembers`
- a follow-up LLM enrichment pass targeting `FAMILY`-rank `description` in
the portal's own data (the same kind of pass that already produced the
Order/Genus prose) would benefit every consumer, not just this
app, and is a separate task from anything in `experiments/`.

## Curated scope (v13) — 14 Parts, all complete

Part I — Mammalia: **complete — all 17 orders, all 39 families.** Same
treatment as Aves below: Mammalia's class-wide Wikipedia coverage (61.3% of
~7,900 species, per `gap-report.json` — even better than Aves') was judged
good enough to skip curation. Newly included beyond the original hand-picked
set: full Artiodactyla (pigs, deer, cattle, not just giraffes/caprines), full
Carnivora (dogs, weasels, seals, not just cats/bears), Chiroptera (bats -
four families, ~1,400 species, ~20% of all mammal species), full Eulipotyphla
(+shrews), Monotremata (echidnas - the platypus family isn't in the source
taxonomy yet), and full Primates/Rodentia (squirrels, muridae, cricetidae).
All three marsupial orders are covered (Diprotodontia, Dasyuromorphia,
Didelphimorphia).

Part II — Aves: **complete — all 37 orders, all 254 families.** Aves'
class-wide Wikipedia coverage (45.6% of ~11,750 species) was judged good
enough to skip curation entirely — see the "more birds" progression below.
The Passeriformes chapter alone carries 146 families and ~3,200
fully-enriched species entries; verified live in Chrome that it renders and
scrolls without hanging (deep-scrolled past Corvidae into Fringillidae, real
content throughout, no jank observed) — the app's "single
continuously-scrollable spread per chapter" design, chosen for a curated
handful of families, turned out to hold up fine even at full-order scale
(see "Large chapters: scroll-driven collapse" below for how the DOM-weight
side of that scale is actually handled).

Part III — Chondrichthyes: **complete — all 4 orders, all 7 families**
(Carcharhiniformes, Lamniformes, Myliobatiformes, Orectolobiformes). Lowest
class-wide coverage of any Part (26.9% of ~1,190 species) but still small
enough (7 families total) that "every family" costs nothing to include.
Lamnidae's 122 extinct-fossil species (Otodus/Carcharocles-adjacent
megalodon kin, etc.) and Carcharhinidae's 6 wholly-fossil genera are
explicitly flagged `extinct: true` at the source
(`chondrichthyes/*/src/data/*.json`) — done by hand since `buildData.ts`'s
auto-detection only fires on description text, and these are almost all
unenriched stub species with no description to detect from.

Part IV — Reptilia: **complete — all 4 orders, all 23 families**
(Crocodylia, Rhynchocephalia, Squamata, Testudines). Best class-wide
coverage of any Part in this book (71.3% of ~8,100 species) — Squamata alone
(snakes, lizards, amphisbaenians) contributes 16 families: vipers,
chameleons, colubrids, monitor lizards, geckos, skinks, cobras/elapids,
pythons, boas, and more. Squamata's order file is named
`SQUAMATA_ORDER.json` in the portal's data (a naming collision elsewhere in
the taxonomy), handled via a `nameOverrides` param on
`extractSlice.ts`'s `allFamilyChapters()` helper so the chapter still
displays as "Squamata."

Part V — Amphibia: **complete — all 3 orders, all 13 families** (Anura -
frogs & toads, Gymnophiona - caecilians, Urodela - salamanders & newts).
62.3% class-wide coverage (~3,700 species), on par with Mammalia/Reptilia
despite being the smallest class in the book by order count.

Part VI — Actinopterygii: **complete — all 14 orders, all 16 families**
(carp/goldfish, cichlids, characins, wrasses, seahorses & pipefish, salmon,
killifish, sculpins, perch, herrings, flounders, tuna & mackerel,
sticklebacks, cod, eels, pike). 45.1% class-wide coverage (~10,900 species),
on par with Aves. Perciformes' order file is `PERCIFORMES_FISH.json` in the
portal's data (another naming collision, same `nameOverrides` handling as
Squamata above).

Part VII — Onychophora: **complete — the one order, both families**
(Peripatidae, Peripatopsidae - velvet worms). 91.4% class-wide coverage,
the best of any Part in the book, though tiny (~230 species). Order file is
`ORD_EUONYCHOPHORA.json` in the portal's data - a *prefix*-style naming
variant this time, unlike the *suffix* pattern in Squamata/Perciformes
above; same `nameOverrides` mechanism handles either.

Part VIII — Cubozoa: **complete — both orders, all 8 families** (box
jellyfish, including the notorious Irukandji). 64.3% class-wide coverage,
~56 species.

Part IX — Scyphozoa: **complete — all 3 orders, all 20 families** (true
jellyfish - lion's mane, moon, cannonball, upside-down). 46.6% class-wide
coverage, ~305 species.

Part X — Phoronida: **complete — the one order, the one family**
(Phoronidae - horseshoe worms). 100% class-wide coverage (all 13 known
species) - tiny but fully described. Order file is `ORD_PHORONIDA.json`
(another prefix-variant name).

Part XI — Nuda: **complete — the one order, the one family** (Beroidae -
beroid comb jellies, predatory ctenophores with no tentacles). 33.3%
class-wide coverage.

Part XII — Tentaculata: **complete — all 4 orders, all 5 families** (sea
gooseberries, creeping/lobed/ribbon comb jellies) - the other ctenophore
class in this taxonomy's scheme (comb jellies are split across Nuda and
Tentaculata rather than one unified class). 31.2% class-wide coverage.

Part XIII — Asteroidea: **complete — the one order, the one family**
(Asteriidae - starfish, including the common starfish *Asterias rubens*).
Only 18.6% class-wide coverage, below this book's usual bar, but included
anyway for the same reason as Columbidae/Didelphidae earlier: unmistakably
recognizable, and the 37 enriched species are real Wikipedia-sourced
content, not filler.

Part XIV — Holothuroidea: **complete — the one order, the one family**
(Holothuriidae - sea cucumbers). 24% class-wide coverage.

These eight (Amphibia, Actinopterygii, Onychophora, Cubozoa, Scyphozoa,
Phoronida, Nuda, Tentaculata) plus Asteroidea/Holothuroidea were found by
surveying *every* remaining Animalia class in `gap-report.json` by
class-wide enrichment % directly (not sorted by species count, which is how
the first survey pass missed the smaller ones) — everything else (Insecta,
Gastropoda, Arachnida, Cephalopoda, Bivalvia, and dozens more) sits well
below this book's quality bar, mostly stub descriptions, not "book"
material yet.

Note: dolphins were already in scope before Chondrichthyes was added —
Delphinidae is one of the families nested inside the Cetacea chapter.

Note: Cetacea and Alcedinidae (kingfishers) are modeled in the source
taxonomy with an extra SUBFAMILY(→TRIBE) layer between FAMILY and GENUS,
unlike every other curated family's flat FAMILY→GENUS→SPECIES shape.
`FamilySection.tsx`'s `collectGenera()` walks past non-genus ranks to handle
this generically.

## Options

A "Show extinct species" toggle sits in the top-right of the reading shell
(`Breadcrumb.tsx`), default **off**. State lives in `src/context/BookOptions.tsx`
(persisted to `localStorage`), read via `src/hooks/useBookOptions.ts`.
`FamilySection.tsx` filters on the `extinct`/`fossil` flags at species and
genus granularity — a genus that's entirely extinct (e.g. Felidae's
*Smilodon*, *Proailurus*) disappears completely rather than showing an empty
heading, and genus numbering stays contiguous around whatever's hidden.

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
