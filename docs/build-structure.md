# Build structure

How the build works, what is incremental, and what was decided about it.

Status: **decided and implemented.** The original note on this page proposed
building the taxonomy in parts and rebuilding only what changed. That is what
the build does now, at family granularity, with the kingdom as the output
boundary. The one part that was *not* made incremental — the monolithic
unified tree — is now opt-in. Recorded here so the next reader does not have
to rediscover it from the code.

## The three tiers

`buildData.ts` produces three different artifacts, and they have different
consumers. Confusing them is the source of most questions about the build.

| Artifact | Where | Size (plantae) | Who reads it |
|---|---|---|---|
| Skeleton | `public/data/kingdoms/<k>/unified-taxonomy-skeleton.json` | 188 KB | the app, on load |
| Per-order subtrees | `public/data/kingdoms/<k>/orders[-<suffix>]/` | 237 files, 248 MB | the app, on demand |
| Order manifest | `public/data/kingdoms/<k>/order-manifest.json` | 136 KB | the app, to find those files |
| Monolithic tree | `data/kingdoms/<k>/unified-taxonomy.json` | 316 MB | build tooling only |

The app never fetches the monolith. `useTaxonomyLoader.ts:58-63` reads the
skeleton and the manifest, then fetches individual order files on demand. The
monolith is read only by `testBuild.ts` and `testDataContract.ts`, and the
`Dockerfile:33` excludes it from the build context so it never reaches a
deployed image.

## What is incremental

**Inputs — per family.** `.build-cache/families/<slug>.json` holds each
family's grafted-and-compressed subtree, keyed on the source file's
`mtime` + `size` plus `cls`, `ord`, `phylum` and `layout`
(`buildData.ts:136-158`). A hit skips the read, parse, graft and compress
entirely. `SN_BUILD_NO_CACHE=1` bypasses it.

`layout` and `phylum` are in the key on purpose. The cache stores *derived*
data, so if a family moves to the kingdom-first layout and the key does not
move with it, the cache silently returns a graft of the wrong file — wrong
species, no error. That is the failure this whole area is hardened against.

**Outputs — per order.** `buildData.ts:424` writes an order file only if
`taxonomy.json` changed, or one of that order's families was a cache miss, or
the file is missing. 237 declared plantae orders, typically 0 rewritten.

**The monolith — skipped, and now opt-in.** See below.

Granularity is family for the cache and kingdom for the output, which are the
two boundaries the source tree and the data files already impose. See
"Why not a coarser tier" for the tier that was considered and rejected.

## The decision: the monolith is opt-in

`SN_BUILD_UNIFIED=1` (or `npm run build:unified`) writes
`unified-taxonomy.json`. Without it, the build does not.

The reason is the cost, measured on plantae (1,022 families, 346,271 physical
nodes, 456,342 nodes represented). Single runs, not averages:

| Build | Monolith | Time | Peak RSS |
|---|---|---|---|
| nothing changed | skipped | 2.4 s | 454 MB |
| one family edited | **written** | 5.7 s | 2,140 MB |
| one family edited | skipped | 3.3 s | 451 MB |
| one family edited | opt-in | 8.5 s | 2,153 MB |

One dirty family out of 1,022 forces a full `JSON.stringify` of the whole
tree: ~5 s and +1.7 GB of RSS, to produce a file nothing fetches. The
incremental work was all on the input side; the output was still monolithic.

### Staleness is part of the contract

Skipping the write leaves whatever is on disk, which is now stale. A stale
monolith that a test validates without complaint is precisely the silent
success this build has been hardened against, so skipping is not enough on its
own. Freshness is therefore explicit:

- `buildData.ts` records `unified: "current" | "stale"` in
  `.build-cache/state.json`, written last, after every other write succeeds.
- The build prints which one it is, rather than passing over it in silence.
- `testDataContract.ts` reads that field and **skips** the size assertion when
  the monolith is absent or not known to be current. A skip, not a pass —
  `testDataContract.ts` counts the three outcomes separately so it cannot be
  mistaken for a green run.
- `testBuild.ts` sets `SN_BUILD_UNIFIED=1` itself, because validating the
  monolith is its entire purpose.

## Why not a coarser tier

A phylum- or class-level cache was considered and rejected. Family is already
the right unit, because it is the unit the source tree is actually edited in:
solo edits are 1-36 files, against occasional bulk imports of 100-1200+
(`buildData.ts:257-258`). The expensive per-family work is read + parse +
compress, and that is already skipped on a hit — so a coarser tier would add
bookkeeping without cutting work.

The thing that was genuinely monolithic is output serialisation, and that does
not want a *granularity* solution. It wants the output sharded, which it
already is for the tier the app reads.

## Still open

**Three copies of the same tree on disk** (plantae): monolith 316 MB, per-order
files 248 MB, family cache 161 MB. The natural end state is for the per-order
files to *be* the cache, after which `.build-cache/families` only needs the
stamps — a few hundred KB — instead of carrying full `children` payloads. That
is only worth doing once the monolith is no longer written by default, since
the cache exists to avoid regenerating it.

**A memory cache for taxonomy data** — still the right idea, but aimed at
serialisation rather than caching. Peak RSS tracks the monolithic
`JSON.stringify`, not the tree walk: a clean build never exceeds ~450 MB while
holding the same `unified` object that costs 2.1 GB to serialise. Streaming
the output would address it; an in-process cache would not.

## Known test rot

Found while validating the above. Pre-existing, and not caused by the opt-in
change — the restructure altered the build's summary format and its output
paths without updating the two build tests, so both have been failing:

- `testBuild.ts:74` matched `/Done\. (\d+) total nodes/`, but the summary line
  now reads `Done. 346271 physical nodes … (456342 total nodes represented)`.
  The digits are not followed by `total nodes`, so the match never succeeded
  and the script always reported "Build failed or output format unexpected".
  It also defaulted to no kingdom, so it built animalia and then read the legacy
  flat `data/unified-taxonomy.json` — a 375MB file last written in July, before
  the per-kingdom restructure. And its 10,000-node floor is an animalia-shaped
  number that chromista (6,651), protozoa (726) and archaea (983) can never
  clear; the floor is now the skeleton the build just wrote.
- `testDataContract.ts:171-177` resolves each manifest `file` against
  `portal/`, but those paths are web-root-relative — correct for the browser,
  since `public/` is the web root, and wrong for a filesystem resolve. It
  should resolve against `public/`. As written, "every manifest order file
  exists on disk" cannot pass.

Six further `testDataContract.ts` failures (rank-count and manifest snapshots,
one duplicated species, three families where `portalCount > totalCount`) were
also of this vintage. All six are now resolved — the snapshots were refreshed,
the duplicate merged, and the `portalCount` assertion replaced with one that
requires the excess to be explained by nodes that are not species (a domestic
trinomial like *Canis lupus familiaris*, or a "sp. spec" placeholder).

### The 28 missing genera are not missing

The snapshot asserted `GENUS: 57348`; the tree has 57,320. That reads like
data loss, and it is worth being precise about why it is not.

The baseline was written by `e452bd90b` (2026-07-09). Six weeks later
`e6a03ab05` removed fabricated taxa from 17 families after checking each
against the cached GBIF backbone and Wikidata QIDs — invented genus containers
(`GENUS_GENUS1`/"Genus1", `GENUS_DOLORESCUTTLE`, `GENUS_SEPIASQUILLARIA`), and
wrong-class grafts such as a bird genus in a frog family. That commit took 30
genus nodes out and put 1 back, and 177 species out and 1 back. The remaining
one genus and three species came from later imports, which is why the observed
movement is 28 and 173 rather than 29 and 176.

So the old baseline was counting hallucinated taxa, and the data is now more
accurate than the baseline it was checked against. The same commit corrected
two `speciesCount` values in `taxonomy.json` for the same reason
(Paragordiidae 10→0, Dendrobatidae 300→210).

Counting the source family files directly gives 57,320 genera, which is what
the skeleton reports, so the build is faithful in both directions here: it did
not drop anything, and the number it reports is the number the data holds.

