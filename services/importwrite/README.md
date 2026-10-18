# importwrite

A single-writer HTTP service for `taxonomy/<kingdom>/.../<family>/src/data/
<family>.json` files. Started as a proof of concept on
`feature/import-write-server`; merged into `main` 2026-10-18 and now the
canonical write path (see `docs/import.md` §0).

## Problem this solves

Importers currently run on whichever machine (Macie, Steamie, Debbie,
q-bert) and write family JSON files directly, then commit. When two
importers touch the same family concurrently, the result is two independent
edits that later get git-merged — and git has no concept of "these two
objects are the same species," so a union merge keeps both. That's what
produced the 42,725-duplicate-copy cleanup commit and the ongoing dedupe
work. It's also why imports have been run from an isolated `git worktree`
rather than the shared tree — a workaround for not having a single writer.

`importwrite` is that single writer. Importers POST species nodes to it
instead of editing files directly; one goroutine per family serializes
concurrent writes and makes the dedupe decision once, with a real identity
key, instead of twice independently.

## What it is not

- **Not a replica of the whole tree in memory.** Only families with recent
  write traffic are loaded; idle ones are evicted (see
  `IMPORTWRITE_IDLE_EVICT`). This is deliberately narrower than "hold the
  skeleton up to the full tree" — the actual problem is write contention
  on a handful of families during any given import run, not read
  performance over the whole tree.
- **Not a replacement for `buildData.ts`.** The portal build still reads
  family JSON files off disk exactly as before; this service's output *is*
  those same files, same format. Trigger a build after a flush, same as
  today.
- **Not touching `portal/data/taxonomy.json`.** Adding a brand-new family
  (new `appSlug`, new colour theme) stays a manual, reviewed edit — it's
  low-volume and not where the concurrent-write problem happens.
- **Not yet multi-instance-safe.** This assumes one `importwrite` process
  is the writer for a given repo checkout. Running two instances against
  the same `IMPORTWRITE_ROOT` reintroduces the exact race this exists to
  remove. If multiple machines need to import, they should all point at
  one running instance (e.g. over Tailscale), not each run their own.
- **`store.get`'s cache is keyed by slug alone, which the real tree proved
  is not globally unique** (103 families are all named `incertae-sedis`,
  sharing a slug across different kingdoms/phyla — the same collision
  `tree.py`'s `sidecar_key_for` exists to fix for the name-parse index).
  Not hit in practice: this service only loads a family through an
  explicit `importRequest` (kingdom+phylum+class+order+slug), never by a
  slug-only search. But a caller submitting the same slug under two
  different locations in one server lifetime would collide. Flagged, not
  fixed, pending a decision on whether `familyLocation` should be the
  cache key everywhere instead of just `Slug`.

## Identity / merge rules

A species is matched in three widening scopes, checked in order, ID first
then name within each (`identity.go`, `family.go`, `crossfamily.go`):

0. **Across families.** Before anything else, `store.applyImport` checks a
   kingdom-scoped, server-wide index of every species identity this
   process has seen, built incrementally as families load (not a startup
   walk of the whole tree — see `crossfamily.go`'s doc comment). A match
   elsewhere merges into that existing record instead of adding a second
   copy here; `apply()`'s own within-family matching below only ever sees
   whatever didn't already match a known identity somewhere else. This is
   the fix for the exact failure mode behind the 2026-10-18 incident: two
   independent passes each decided a different family should keep a
   disputed species, and because the edits landed in different files,
   nothing caught the disagreement before 35 species vanished from both.
   One family lock is held at a time, never two at once by one goroutine,
   so two requests that each find their match in the other's family can't
   deadlock — `TestApplyImport_ConcurrentCrossFamilyLookupsDoNotDeadlock`
   is the regression test, 200 concurrent pairs shaped exactly like that.
   Scoped per kingdom, same as `dedupeSpeciesAcrossFamilies.py`'s own
   `by_authority` index: a name shared across kingdoms is a homonym
   (`Graphium sarpedon` is a butterfly in one and a fungus in another),
   never a duplicate.
1. **Across genera, within the family already being written to.** A
   species submitted under a different genus than the one it's already
   filed under in the SAME family — a revision moving it, or two importers
   disagreeing about which genus is right. One level narrower than #0, and
   handled inside the already-held family lock (`findInOtherGenera`), not
   the store-level index.
2. **Within the target genus** — the original matching this service shipped
   with, and the shape reused by scopes #0 and #1 above:
   1. **By external ID.** Every importer already writes `sourceIds` on a
      species node — `{"gbif": "2436351"}`, `{"col": ["N5F3"], "itis":
      ["624887"]}`, etc. (the shape is per-dataset and inconsistent — a bare
      string for some, a string array for others — both are accepted). Any
      single shared `(source, id)` pair between the incoming species and an
      existing one is treated as the same species, even if the name differs
      entirely. This is the part that survives a spelling fix, an author
      correction, or a genus move between imports — a name-only match
      wouldn't.
   2. **By normalized name**, when neither side has a resolvable ID yet
      (the common case for a first import, or an importer that doesn't
      resolve cross-reference IDs at all): lowercased, trimmed, with stray
      wrapping quote characters stripped (some existing data has them, e.g.
      `"Prionailurus`).

There's deliberately no separate "ImportKey" wire format — `sourceIds` is
already the contract every importer writes into, on both the Go side
(`identity.go`'s `sourceIDPairs`, which reads whatever keys are present,
no fixed list) and the TypeScript side (`fetchSpeciesFromApi.ts`'s
`SourceIds` interface, which names the keys actually in use today —
`checklistbank`, `col`, `gbif`, `itis`, `wikidata`, `wfo`, `mycobank`,
`worms`, per `portal/public/data/sources-report.json` — so an importer
gets typo protection filling it in, without the Go matcher needing to
know the list).

On a match (by either pass), fields merge rather than overwrite:

- `description`: kept if existing is empty or shorter than incoming.
- `sourcedFrom`: incoming replaces existing only if existing is empty or
  `"ollama"` and incoming is a real source — never the reverse, and never
  introduces `"ollama"`.
- `continents`: unioned.
- `sourceIds`: merged key-by-key (union of sources) — so a species that
  only had `col`/`itis` picks up `gbif` the first time a GBIF-sourced
  import resolves it, and can be matched by either from then on.
- `uuid`: kept if existing already has one, else taken from incoming if
  incoming has one, else **assigned fresh** -- a random v4, generated once
  by the arbiter at the moment a species is first added, never recomputed.
  Deliberately not `buildData.ts`'s v5-over-rank-path scheme: that formula
  bakes in placement (kingdom/.../family/genus), so a species later matched
  into a different family or genus would get a *different* uuid under it,
  even though it's the same species. A random v4 has nothing to go stale.
  `POST /family/{slug}/species`'s response carries each species' uuid back
  (`added`/`merged` are now `{name, id, uuid}` objects, not bare name
  strings) so a transformer logging its own import run records the
  identity the arbiter actually assigned, not one it guessed itself.
- `subspeciesCount`: kept if existing already has one, else taken from
  incoming.

Verified against real data: ran `fetchSpeciesFromApi.ts` for `bradypodidae`
with `IMPORTWRITE_URL` set, twice. First run merged GBIF's 4 matched
species into the existing entries and added `sourceIds.gbif` to each (a
clean, minimal diff — only the new key, nothing reordered or re-escaped).
Second, identical run produced **zero** further diff. Unit tests cover the
ID-over-name-change case directly (`TestApply_MatchesByGbifIDDespiteNameChange`,
`TestApply_MatchesByIDFromStringArraySourceIds`,
`TestApply_FallsBackToNameWhenNeitherSideHasAnID`).

## Family registration check

`loadFamily` used to create a new family JSON file for any slug it hadn't
seen before — fine for the two callers that existed at the time, since both
pre-validate against `taxonomy.json` before ever calling in, but a latent
gap for any future caller that doesn't: a typo'd or genuinely new slug would
get a file silently written for it that nothing builds, grafts, or has a
colour theme for (see "Scaffolding Gaps" in project memory for an existing
instance of this exact failure mode).

`registry.go`'s `familyRegistry` closes that gap: before creating a file for
a slug, `loadFamily` checks it against `portal/data/kingdom-config.json`'s
taxonomy skeleton for that kingdom (cached per kingdom after the first
check). An unregistered slug returns `*unregisteredFamilyError` instead of
creating anything:

- `POST /family/{slug}/species` → `422`, body `{"error", "unregistered":
  true, "kingdom", "family", "speciesOffered"}` — enough for the caller to
  record this as a pending family itself (`pendingFamilies.add_family()`,
  e.g.) without `importwrite` depending on Python to do it directly.
- `GET /family/{slug}` → `404`.

Passing a `nil` registry (every pre-existing test) skips the check entirely,
preserving the old unconditional-create behavior — the real `store.go` call
site is the only one that passes a non-nil registry, since it's the only
path that can reach a slug nobody has ever written a file for.

## API

```
POST /family/{slug}/species
  body: {
    "kingdom": "animalia", "phylum": "chordata", "class": "mammalia", "order": "carnivora",
    "genus": { "id": "GENUS_PANTHERA", "name": "Panthera" },
    "species": [ { "id": "...", "name": "Panthera leo", "rank": "SPECIES", ... } ]
  }
  -> { "added": [{"name","id","uuid"}], "merged": [{"name","id","uuid","family"?}], "genusCreated": bool }

GET /family/{slug}?kingdom=animalia&phylum=...&class=...&order=...
  -> the family's current in-memory JSON tree (useful for an importer's dry-run/diff)

POST /family/{slug}/flush
  -> forces an immediate disk write (+ git commit if enabled) instead of waiting for the next tick

GET /healthz
```

`kingdom`/`phylum`/`class`/`order` are only needed to resolve the file path
(mirrors `portal/scripts/lib/familyPath.ts` — see `path.go`'s doc comment on
why there's exactly one implementation of that resolution logic and this is
a deliberate, tested port of it, not a second one). Species nodes are
passed through as opaque, order-preserving JSON objects (`onode` in Go,
see `ojson.go`) — any field `TaxonNode` supports round-trips untouched,
in the order it arrived; the server only reads the few fields it needs
for merge decisions.

## Running it

```bash
cd services/importwrite
go build -o importwrite .
IMPORTWRITE_ROOT=../.. ./importwrite        # defaults to ../.. (repo root) anyway
```

Env vars:

| Var | Default | Meaning |
|---|---|---|
| `IMPORTWRITE_ROOT` | `../..` | Repo root containing `taxonomy/` |
| `IMPORTWRITE_PORT` | `8089` | HTTP port |
| `IMPORTWRITE_GIT_COMMIT` | `0` | Set `1` to have the server `git add && git commit` each flushed family. **Off by default** — flips on only when you're ready for it to touch git history; never pushes. |
| `IMPORTWRITE_FLUSH_INTERVAL` | `5s` | How often dirty families are written to disk |
| `IMPORTWRITE_IDLE_EVICT` | `10m` | Drop a clean, idle family from memory after this long |

Flushing is eager by design: in-memory state is a staging buffer in front
of the file on disk, not a second source of truth, so a crash between
flushes should lose at most a few seconds of writes, not a whole import
run's worth.

## Migration path for existing importers

`portal/scripts/fetchSpeciesFromApi.ts` is wired up: set `IMPORTWRITE_URL`
and it POSTs each genus to the service (one request per genus, then a
`/flush`) instead of `writeFileSync`-ing the whole family file; leave it
unset and the script behaves exactly as before. The change was isolated to
the last step — the species-building logic (GBIF fetch, Wikipedia
enrichment, continent inference) didn't move.

Verified against live GBIF, not just the scratch fixture: ran it for real
against `bradypodidae` (6 species already on disk, real descriptions/uuids/
sourceIds from wikipedia+col+itis+checklistbank) with the server pointed at
the real repo root and `IMPORTWRITE_GIT_COMMIT=0`. GBIF matched 4 of the 6
species; all 4 merged into the existing entries (0 added, 0 duplicates),
every existing field — `uuid`, `sourceIds`, `description`, `authorship` —
survived untouched, and the 2 species GBIF didn't return stayed in place.
That's the concurrent-import collision this service exists to prevent,
reproduced and fixed end to end. The test write was reverted with `git
checkout --` afterward; it's not an established workflow yet, just a
one-off verification.

**Two diff-noise bugs turned up by that test, both fixed (see `ojson.go`):**

- Keys came out alphabetically sorted (`encoding/json` on a `map[string]
  any` has no memory of input order), while the files on disk have
  hand/tool-chosen key order. A no-op merge was a 180-line diff for zero
  actual data changes. Fixed by replacing the plain-map `node` type with
  `onode`, a small ordered-object type with its own `UnmarshalJSON` (walks
  tokens, records key order as it reads them) and `MarshalJSON` (writes
  them back in that same order). `TestFlush_PreservesKeyOrder` is the
  regression test.
- `&` (and anything else HTML-sensitive: `<`, `>`, U+2028/U+2029) came out
  as `&` etc. — `encoding/json`'s default HTML-escaping, which exists
  for embedding JSON in `<script>` tags and has no reason to apply to a
  file on disk. Fixed with `marshalNoEscape`/`marshalIndentNoEscape`
  (`enc.SetEscapeHTML(false)`) — this is the general switch for the whole
  category, not an `&`-specific patch. `TestFlush_DoesNotHTMLEscape` is the
  regression test. (Non-ASCII text was never at risk: Go's encoder passes
  valid UTF-8 through raw by default.)

Both verified against the real `bradypodidae` re-run: the merge diff went
from 180 lines to **zero** for a request that changed no actual data.

Other importers (`scaffoldKingdomTaxonomy.ts`, the per-machine scripts on
Steamie/Debbie/q-bert) aren't wired yet — same shape of change, not done.
