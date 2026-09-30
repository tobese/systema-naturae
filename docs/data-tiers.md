# Data tiers for the graph and the book

*Measured 2026-09-29 with `scripts/measureProjections.py`.* Every number below
comes from that script, so it can be re-run after an import and the note
corrected rather than trusted.

## The two surfaces already share a source

`docs/graph-vs-book-parity.md` (audit dated 2026-09-26) opens by saying the two
surfaces do not get their data from the same place: the graph from the
*compressed* `unified-taxonomy.json`, the book from *uncompressed* per-order
files. That stopped being true when the monolith became opt-in and the app
stopped fetching it. They read the same bytes today, by two different routes:

```
graph  useTaxonomyLoader.ts:96    fetch(`${base}${orderPath}`)   orderPath from order-manifest.json
book   useBookChapters.ts:119     fetch(`.../orders${suffix}/${meta.orderFile}.json`)
```

The order files are compressed too — `CARNIVORA.json` holds 406 species as
nodes and 609 flattened into `speciesList[]` — so "compressed vs uncompressed"
is not a live distinction. The comment at `useBookChapters.ts:14-18`, which
justifies *not* using the monolith on the grounds that the book needs every
species as its own entry, is defending a choice that no longer applies.

What is genuinely left to unify is small:

| Gap | Nature |
|---|---|
| Two resolution paths for one file | `order-manifest.json` vs `book-skeleton.json` — duplicated logic, free to drift |
| PHYLUM and KINGDOM absent | **Structural.** Order files are rooted at ORDER, so neither surface can reach a phylum. The book's backlog item, and the one thing a projection cannot fix |
| Book-only sidecar | `extensions/<ORDER>.json` — portraits, IUCN, chapterStats. Legitimately book-only |

## Where the bytes are

One file per ORDER, and those files are wildly uneven. Across the six kingdoms
there are 1,100 of them holding 1,204,339 species entries.

| | median animalia file | p99 | largest |
|---|---|---|---|
| shipped | 112 KB | 12.5 MB | `COLEOPTERA.json` 52.6 MB |

`COLEOPTERA` alone is 134 families, 15,168 genera and 151,512 species entries.
The graph caches 3 order files and the book 8, so a reader clicking through the
large ones holds 100-200 MB of JSON and pays roughly 2.5× that again in
`JSON.parse` heap — 430-600 MB, on a phone.

Worth being clear about what is *not* the problem: transfer. `COLEOPTERA` is
52.6 MB of JSON and 5.4 MB over the wire, a 16:1 ratio, and `nginx.conf` already
sets `gzip on` for `application/json`. The cost is the parse, not the download.

## The two surfaces want opposite things

The graph draws minimally-described species as pruned dots and needs structure
to lay out and navigate. The book wants every species as its own entry, with
prose. Both currently pay for the union on every order they open.

There is also a structural reason the graph cannot avoid it today. The skeleton
carries no FAMILY or GENUS nodes at all — its 159 genera are Tardigrada's,
inlined because that phylum has no order file — only order-level
`_familyCount` and `_speciesCount`. So **the graph cannot see any of animalia's
57,161 genera without fetching a whole order file.**

## Measured

A *nav tier* keeps FAMILY and GENUS with their prose, counts and stamps, and
collapses species into `_speciesCount` / `_describedCount` on the genus. It is
the minimum the graph can render from, and unlike a bare counts projection it
keeps the genus descriptions the info panel shows.

All sizes minified — what a server sends and the client parses. The on-disk
files are pretty-printed and about 1.6× larger.

| Kingdom | shipped | nav tier | | largest shipped | largest nav tier |
|---|---|---|---|---|---|
| animalia | 208.9 MB | **17.8 MB** | 11.7× | COLEOPTERA 52.6 MB | 4.3 MB (12×) |
| plantae | 160.1 MB | **5.9 MB** | 27.2× | ASPARAGALES 17.1 MB | 0.5 MB |
| fungi | 49.0 MB | **3.3 MB** | 14.8× | AGARICALES 7.8 MB | 0.3 MB |
| chromista | 22.6 MB | **2.0 MB** | 11.3× | ROTALIIDA 4.4 MB | 0.4 MB |
| protozoa | 1.3 MB | **0.2 MB** | 6.5× | | |
| archaea | 0.8 MB | **0.3 MB** | | | |
| **all six** | **442.6 MB** | **29.5 MB** | **15×** | | |

`plantae` is the instructive one: dropping `speciesList[]` alone takes it from
160 MB to 131 MB, because its bytes are mostly *described* species with prose.
It is only the full projection that collapses it. So "just drop speciesList" is
not the fix.

## Status: the tier is built, the client switch is deliberately not done

`buildData.ts` now emits a nav tier per order alongside the order files, and
each manifest entry carries a `navFile`. Verified on the real build:

| | predicted | actual |
|---|---|---|
| animalia nav tier | 17.8 MB, worst 4.3 MB | **17.8 MB, worst 4.27 MB** |
| all six kingdoms | 29.5 MB minified | 43.4 MB on disk (pretty-printed) |

`testDataContract.ts` asserts the tier exists, matches the order file count,
is more than 5× smaller, and that its species carry no descriptions — so the
projection cannot rot, and the client switch becomes wiring rather than a
rebuild.

Getting there caught a bug worth recording, because it is the kind that looks
like a modest shortfall rather than an error. The first implementation built
each genus as `{...child, speciesList: undefined, _speciesCount, ...}`. Spreading
keeps the genus's own `children` — which is every species node under it, with
its full description — so COLEOPTERA came out at 25.4 MB instead of 4.3 MB and
the tier at 102 MB instead of 17.8 MB. A 2× win instead of 11.7×, with no error
anywhere. The genus node now lists its fields explicitly, and the contract
assertion is on the ratio precisely because "smaller" alone would have passed.

**Nothing reads the tier yet**, and that is the honest position rather than an
oversight. The next step is not the wiring it looks like.

## Why the client cannot simply switch

`SearchBox` builds its index from the loaded tree by walking `children` **and
`speciesList`**, taking `name` and `commonName`
(`SearchBox.tsx:14-25`). The nav tier has no `speciesList` and reduces species
to `{id, name, rank}` with no `commonName`. Pointing `loadOrder` at `navFile`
would therefore silently lose:

- search over the 110,614 entries in animalia's `speciesList` — over a fifth of
  the 527,630 species in the kingdom;
- common-name search for species entirely;
- `EponymModal` and Species of the Day, which both read `namedAfter` off the
  loaded tree.

None of that throws. It is a quieter and much worse failure than a fetch error.

## The decomposition — corrected, and it is not what this note first said

The first version of this section claimed prose was 63% of the bytes and that
shipping prose on demand was therefore the lever. **That was wrong**, and the
way it was wrong is worth recording, because the mistake is easy to repeat.

It came from comparing totals-with-`speciesList`-removed against totals, which
attributes *all* per-species field overhead to prose. Measuring the fields
directly, on `COLEOPTERA` (52.6 MB, 151,512 species entries):

| | MB | share |
|---|---|---|
| `description`, all ranks | 13.2 | 25% |
| `id` + `name` | 9.6 | 18% |
| `familySlug` + `orderName` + `className` | 12.3 | 23% |
| `lineage` + `rank` | 6.6 | 13% |
| `sourcedFrom` + `subspeciesCount` + `extinct` | rest | ~21% |

**The largest single component is denormalisation**: `familySlug`, `orderName`,
`className`, `lineage` and `rank` are repeated on all 151,512 species, where
they are constant for the family or genus they sit under. Prose is a quarter of
the file, not two thirds.

So the tiers that are actually available, measured rather than assumed:

| graph order file | animalia | worst file | COLEOPTERA |
|---|---|---|---|
| as shipped (the book's) | 208.9 MB | 52.6 MB | 52.6 MB |
| **prose moved out only** — what is built now | ~209 MB | 50.8 MB | 50.8 MB |
| + repeated stamps inherited from the parent | 61.1 MB | 14.1 MB | 14.1 MB |
| + names only, no species records at all (nav tier) | 17.8 MB | 4.3 MB | 4.3 MB |

The honest achievable win for the graph is **3.4×**, from 208.9 MB to 61.1 MB,
with a worst file of 14.1 MB and per-genus prose on demand at a 1.23 MB worst
case and a 3 KB median. Not the 15× or 12× quoted above — those are real
arithmetic, but on a tier that cannot be searched, or that still carries the
repeated stamps.

Getting the third row needs one thing the build cannot do alone:
`annotatePortalLevels` already re-derives `className` and `orderName` on the
client, so the machinery exists, but `familySlug`, `lineage` and `rank` are read
per-node today and would have to be inherited on the way down. That is a real
client change, not a mechanical edit, and it is the next piece of work rather
than something to slip in here.

## What is built

- `orders[-suffix]/` — unchanged, full prose. **The book's**; `SpeciesEntry`
  renders `species.description` from it.
- `orders-prose[-suffix]/<ORDER>/<GENUS>.json` — per-genus species prose,
  21,588 files for animalia, worst 1.23 MB, median 3 KB, written only for
  genera that have any described species (38% of them) and only for a dirty
  order.
- `orders-names[-suffix]/` — the order tree without species prose. **The
  graph's**; this is the tier the client should load in place of `file`.
- `orders-nav[-suffix]/` — structure and counts, no species records. The
  layout-only artifact.

Each manifest entry carries `file`, `namesFile`, `navFile` and `proseDir`.
`testDataContract.ts` asserts the nav tier exists, matches the order count, is
over 5× smaller, and holds no species descriptions.

**The client is switched.** `loadOrder` fetches `namesFile`, runs it through
`inheritStamps`, and `loadProseFor` fetches the containing genus's prose file
when a node under a genus is selected. `SearchBox` keeps working because the
names tier retains `name`, `commonName` and the `speciesList` array, and the
Eponyms and Species-of-the-Day modals keep working because `namedAfter` is a
per-species field that is kept.

Two stamps are dropped from the tier and re-derived on the client:
`className`, `orderName` and `familySlug`. `lineage` and `rank` are **kept** —
`lineage` because 379 animalia nodes have none and re-deriving it would invent
a value, `rank` because it is read 79 times and position is a poor substitute
for an explicit value. Together they are 12% of the bytes, which is the price of
a change that is then provably behaviour-neutral.

### The two verifications that make this safe

Both were run against the real build, and both found real bugs before they
passed. They are now contract assertions, not one-off scripts.

**Inheritance parity.** For all 383 animalia order files, the inherited tree is
compared field-by-field against the full order file on all 585,624
species-level nodes: **0 mismatches**. The first version reported 380, all
`lineage: null` against an invented genus name — the projection was deleting
explicit nulls, so the client filled a field the source deliberately left
empty. That is what moved `lineage` out of the dropped set.

**Overlay parity.** For the largest orders, the names tier plus its genus prose
files is compared against the full order file: **0 description differences
across 183,109 species**. The first run reported 52,572, all of them `""`
against `undefined` — semantically identical, so the comparison now
normalises blank to null rather than treating the two as different values.

### What the graph actually saves

| | animalia | COLEOPTERA |
|---|---|---|
| before: the order file | 208.9 MB | 52.6 MB |
| after: names tier on load | 173.0 MB | 43.0 MB |
| plus prose when a genus is opened | | +1.23 MB worst, 3 KB median |

**1.2×, not the 2.2× the Python prototype suggested** and well short of the
3.4× in the table above. The prototype dropped `lineage`, `rank`,
`sourcedFrom` and `subspeciesCount` as well, and every one of those is read
somewhere in the graph — `sourcedFrom` by the OptionsPanel highlight,
`subspeciesCount` by the book and asserted by this suite. Keeping them is why
the real win is smaller than the modelled one, and it is the right trade: a
provable 1.2× beats an unprovable 3.4×.

## Shipped size

All four tiers are written **minified**. They are fetched and `JSON.parse`d by
the browser, so the indentation was a third of the bytes downloaded and walked
past. Measured from the built image (`du` inside
`debbie-systema-naturae:latest`), not estimated:

| tier | shipped | ships? |
|---|---|---|
| `orders/` — the book | 442 MB | yes |
| `orders-names/` — the graph | 376 MB | yes |
| `orders-prose/` — per genus | 415 MB | yes |
| `orders-nav/` — layout only | 0 | **dropped** |
| **data/kingdoms total** | **1233 MB** | |

`orders-nav/` is built (30 MB) but `rm -rf`'d in the Dockerfile, and
`scripts/verifyDist.mjs` warns if it ever reappears. `.build-cache/` — the
per-family graft cache the build uses for incremental rebuilds — used to leak
into the image as well, 458 MB of it, because the rsync's `*cache*.json`
excludes need a `.json` suffix and the directory plus the plain `.json` files
inside it both slipped through. The same script now fails the build on it.

The skeleton and the order manifest stay pretty-printed. Together they are
under 900 KB, they are the human-inspectable index of what a build produced, and
minifying them would buy nothing.

Worst-case single fetch, minified:

| | animalia | plantae |
|---|---|---|
| book, `orders/` | 42.5 MB | 14.0 MB |
| graph, `orders-names/` | 35.4 MB | 13.1 MB |
| prose, on genus open | 1.09 MB (2 KB median) | |

## Why not a server

The test for any server proposal: **does it reduce what the client parses, or
just move the bytes?** A Go service that re-serialises the same 52.6 MB does
nothing for a browser still calling `JSON.parse` on it. Go earns its place only
where it does the parsing, filtering *and* paging server-side so the client
never materialises a whole order.

Judged that way, of the three ways Go could be used here:

- **Build-time replacement for `buildData.ts`** — the strongest case. Memory is
  real at build time: 2.1 GB peak RSS, and the
  `NODE_OPTIONS=--max-old-space-size=8192` every build script carries is a
  standing admission of it. A streaming builder holds one family at a time and
  could emit both tiers directly. Against it: it rewrites the component that
  only just became correct, and the gain is confined to build machines.
- **Serving layer replacing nginx** — worth it only for server-side search
  across ~1.2M species, which is flatly impossible client-side today. Otherwise
  it is a stateful service with cache invalidation, and it gives up the
  "static site, deploy by `git pull`" property `docs/deploy-debbie.md` is built
  around. If built, as a read-only sidecar in front of the static files, not a
  replacement for them.
- **Neither** — do the projection at build time. It is one more output of a
  build that already writes the order files, and it addresses the actual cost.

Order of work, revised by the measurements above: get prose out of the order
file first, since it is 63% of the bytes and the graph only needs the
description of species a reader actually opens. A names tier follows. The
counts tier built here stays as the layout-only artifact. A build-time rewrite
of `buildData.ts` comes only if build memory becomes annoying, and a server only
if search is the thing actually wanted — at which point the answer is still
that it must page and filter server-side, because re-serialising the same bytes
does nothing for a browser that still calls `JSON.parse` on them.
