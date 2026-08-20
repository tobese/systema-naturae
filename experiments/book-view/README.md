# Book View — prototype

A standalone, decoupled experiment: read the animal kingdom as a book, inspired
by (not a replica of) Linnaeus's *Systema Naturae*. See
`/Users/tb/.claude/plans/checkup-on-the-real-whimsical-marshmallow.md` for the
full design rationale and background.

This is **not** wired into the portal. It reads a curated, pre-extracted slice
of the portal's already-built data (read-only) and stands entirely on its own.

## Setup

```bash
npm install
npm run extract-data   # rebuilds public/data/*.json from the portal's output
npm run dev
```

`extract-data` reads `portal/public/data/kingdoms/animalia/orders/*.json` and
`portal/data/gap-report.json` from the repo root — re-run it any time the
upstream portal data changes (e.g. after an enrichment pass). It also strips a
handful of corrupted `description` fields where `enrichFromWikipedia.ts`'s
extraction grabbed raw MediaWiki markup (category links, `{{Speciesbox|...}}`
infobox templates — disproportionately common on fossil/extinct species whose
articles open with a taxobox before any prose, or article redirects) instead
of real prose. That's a display-layer cleanup done at extraction time — the
portal's source data is never modified.

## Curated scope (v8)

Part I — Mammalia: Carnivora (Felidae, Ursidae), Primates (Hominidae,
Cercopithecidae, Cebidae, Lemuridae), Cetacea (whales, dolphins & porpoises),
Proboscidea (Elephantidae), Perissodactyla (Equidae), Diprotodontia
(Macropodidae, Vombatidae), Lagomorpha (Leporidae), Dasyuromorphia
(Dasyuridae), Artiodactyla (Giraffidae, Caprinae), Eulipotyphla (Erinaceidae,
Talpidae), Cingulata (Dasypodidae), Rodentia (Caviidae, Castoridae), Pholidota
(Manidae), Pilosa (Bradypodidae, Myrmecophagidae), Didelphimorphia
(Didelphidae) — 24 families across 15 chapters. All three marsupial orders
present in the taxonomy are covered (Diprotodontia, Dasyuromorphia,
Didelphimorphia); Didelphidae is the one family in this scope below the usual
~100%-enriched bar (120/304, 39%) but it's the only opossum family and the
only remaining marsupial group, so it's included regardless.

Part II — Aves: **complete — all 37 orders, all 254 families.** Unlike every
other Part, Aves is no longer hand-curated: `extractSlice.ts` special-cases
`familySlugs: "ALL"` for this class (Aves' class-wide Wikipedia coverage,
45.6% of ~11,750 species, was judged good enough to skip curation entirely —
see the "more birds" progression below). The Passeriformes chapter alone
carries 146 families and ~3,200 fully-enriched species entries in one
continuous scroll; verified live in Chrome that it renders and scrolls
without hanging (deep-scrolled past Corvidae into Fringillidae, real content
throughout, no jank observed) — the app's "single continuously-scrollable
spread per chapter" design, chosen for a curated handful of families, turned
out to hold up fine even at full-order scale.

Part III — Chondrichthyes: Lamniformes (Lamnidae — great white, makos),
Carcharhiniformes (Carcharhinidae — requiem sharks, Sphyrnidae — hammerheads).
Lamnidae's 122 extinct-fossil species (Otodus/Carcharocles-adjacent megalodon
kin, etc.) and Carcharhinidae's 6 wholly-fossil genera are explicitly flagged
`extinct: true` at the source (`chondrichthyes/*/src/data/*.json`) — this had
to be done by hand since `buildData.ts`'s auto-detection only fires on
description text, and these are almost all unenriched stub species with no
description to detect from.

Part IV — Reptilia: Testudines (Testudinidae — tortoises, Cheloniidae — sea
turtles, Dermochelyidae — leatherback).

Note: dolphins were already in scope before Chondrichthyes was added —
Delphinidae is one of the families nested inside the Cetacea chapter.

Chosen from `portal/data/gap-report.json` for real Wikipedia-derived
enrichment coverage, favoring name-recognizable groups over higher-but-obscure
coverage elsewhere in the tree (several Squamata families score 75-80%
enriched vs. Hominidae's 57% — see the plan doc for the tradeoff).

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

`src/hooks/useBookData.ts` deliberately mirrors
`portal/src/hooks/useTaxonomyLoader.ts`'s skeleton + on-demand-fetch + LRU-cache
pattern, at Chapter (= taxonomic Order) granularity, even though this
prototype only ever has 3 chapters. At full scale, `loadChapter` should fetch
`portal/public/data/kingdoms/animalia/orders/${orderId}.json` directly instead
of this app's own filtered `public/data/chapters/*.json`, and
`extractSlice.ts`'s family whitelist goes away — the loading *pattern*
wouldn't need to change, only the fetch target and the removal of filtering.
