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

## Identity / merge rules (the part most likely to need iteration)

Species are deduped **by normalized name within a genus**: lowercased,
trimmed, with stray wrapping quote characters stripped (some existing data
has them, e.g. `"Prionailurus`). On a match:

- `description`: kept if existing is empty or shorter than incoming.
- `sourcedFrom`: incoming replaces existing only if existing is empty or
  `"ollama"` and incoming is a real source — never the reverse, and never
  introduces `"ollama"`.
- `continents`: unioned.
- `sourceIds`: maps merged key-by-key (union of sources).
- `uuid`, `subspeciesCount`: kept if existing already has one, else taken
  from incoming.

This does **not** currently use `sourceIds` (GBIF key, ChecklistBank URN,
etc.) as the identity itself — only name. Two sources that disagree on
spelling/casing in a way normalization doesn't catch will still produce two
entries. If that turns out to matter in practice, the fix is to also index
by any `sourceIds` value and treat a shared external ID as the same species
even if the name differs, falling back to name-matching only when neither
side has an external ID yet.

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
passed through as opaque JSON objects (`map[string]any` in Go) — any field
`TaxonNode` supports round-trips untouched; the server only reads the few
fields it needs for merge decisions.

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

`fetchSpeciesFromApi.ts` and friends already build the exact node shape
this API expects before they currently `writeFileSync` it. The change at
each call site is swapping that last step for a `POST`, not touching the
species-building logic itself. Not done in this POC — this is the service
alone, with tests (`family_test.go`, `path_test.go`) proving the merge and
path-resolution behavior, plus a manual end-to-end smoke test against a
scratch fixture (see branch history / ask for a repeat run). Wiring a real
importer script to it is the natural next step once the identity rule
above is confirmed to be enough.
