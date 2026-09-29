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

## Recommendation

Emit the nav tier alongside the order files, per order, and point the graph at
it. **+6.7% on disk** (442.6 → 472.0 MB total) for a **15× smaller worst fetch**,
and the per-order sharding is kept, so the skeleton and manifest indirection
survives untouched. The book keeps reading the shipped order files, because it
genuinely needs the prose.

That makes the two surfaces' difference *intentional and named* — structure
versus detail — rather than two code paths happening to converge on one file.
It also retires the duplicated lookup: with both tiers published, the graph's
manifest entry gains a `navFile` field and the book keeps its own, and
converging them becomes a deliberate step rather than an accident nobody
notices.

Two things this does **not** do. The book still fetches a 52.6 MB order file
when a reader opens Coleoptera, so per-genus paging for the worst genera is
still worth doing separately. And PHYLUM/KINGDOM stay absent, because a
projection of an order-rooted file cannot invent the ranks above it — that
needs the order files re-rooted at PHYLUM, or a phylum tier of its own.

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

Order of work: the projection first, then paging for the worst genera, then a
build-time rewrite only if build memory becomes annoying, and a server only if
search is the thing actually wanted.
