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

## Curated scope (v1)

Part I — Mammalia: Carnivora (Felidae, Ursidae), Primates (Hominidae).
Part II — Aves: Passeriformes (Corvidae, Fringillidae).

Chosen from `portal/data/gap-report.json` for real Wikipedia-derived
enrichment coverage, favoring name-recognizable groups over higher-but-obscure
coverage elsewhere in the tree (several Squamata families score 75-80%
enriched vs. Hominidae's 57% — see the plan doc for the tradeoff).

## Scaling notes

`src/hooks/useBookData.ts` deliberately mirrors
`portal/src/hooks/useTaxonomyLoader.ts`'s skeleton + on-demand-fetch + LRU-cache
pattern, at Chapter (= taxonomic Order) granularity, even though this
prototype only ever has 3 chapters. At full scale, `loadChapter` should fetch
`portal/public/data/kingdoms/animalia/orders/${orderId}.json` directly instead
of this app's own filtered `public/data/chapters/*.json`, and
`extractSlice.ts`'s family whitelist goes away — the loading *pattern*
wouldn't need to change, only the fetch target and the removal of filtering.
