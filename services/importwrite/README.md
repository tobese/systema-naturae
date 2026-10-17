# importwrite

A single-writer HTTP service for `taxonomy/<kingdom>/.../<family>/src/data/
<family>.json` files, built as a proof of concept on `feature/import-write-
server`.

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

## Identity / merge rules

A species is matched against the genus it's being imported into in two
passes, ID first (`identity.go`), name as the fallback (`family.go`):

1. **By external ID.** Every importer already writes `sourceIds` on a
   species node — `{"gbif": "2436351"}`, `{"col": ["N5F3"], "itis":
   ["624887"]}`, etc. (the shape is per-dataset and inconsistent — a bare
   string for some, a string array for others — both are accepted). Any
   single shared `(source, id)` pair between the incoming species and an
   existing one is treated as the same species, even if the name differs
   entirely. This is the part that survives a spelling fix, an author
   correction, or a genus move between imports — a name-only match
   wouldn't.
2. **By normalized name**, when neither side has a resolvable ID yet (the
   common case for a first import, or an importer that doesn't resolve
   cross-reference IDs at all): lowercased, trimmed, with stray wrapping
   quote characters stripped (some existing data has them, e.g.
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
- `uuid`, `subspeciesCount`: kept if existing already has one, else taken
  from incoming.

Verified against real data: ran `fetchSpeciesFromApi.ts` for `bradypodidae`
with `IMPORTWRITE_URL` set, twice. First run merged GBIF's 4 matched
species into the existing entries and added `sourceIds.gbif` to each (a
clean, minimal diff — only the new key, nothing reordered or re-escaped).
Second, identical run produced **zero** further diff. Unit tests cover the
ID-over-name-change case directly (`TestApply_MatchesByGbifIDDespiteNameChange`,
`TestApply_MatchesByIDFromStringArraySourceIds`,
`TestApply_FallsBackToNameWhenNeitherSideHasAnID`).

## API

```
POST /family/{slug}/species
  body: {
    "kingdom": "animalia", "phylum": "chordata", "class": "mammalia", "order": "carnivora",
    "genus": { "id": "GENUS_PANTHERA", "name": "Panthera" },
    "species": [ { "id": "...", "name": "Panthera leo", "rank": "SPECIES", ... } ]
  }
  -> { "added": ["..."], "merged": ["..."], "genusCreated": bool }

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
