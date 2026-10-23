# `scripts/dedupeSpeciesAcrossFamilies.py`

Removes species copies that an import wrote into a second family the tree already holds. The curated placement wins over the source's; the import-written copy is dropped.

## What authority decides which copy is right?

Four ranked signals, the first that breaks the tie wins:

1. **GBIF family cache** (`--authority-family`) — GBIF issued the `usageKey`, so its family assignment decides which placement is correct. This is the *only* signal that knows which FAMILY is right. Without it, 1,242 species lost their correct placement to a richer misfiled copy (anobiidae → ptinidae, lobariaceae → peltigeraceae, etc.). Pass the cache from `fetchGbifFamilyCache.py`.

2. **Conforming name** — a name that swallowed its own authorship is an import artefact, not a better record.

3. **Richness** — description / commonName / continents / reference / year. A copy carrying more of these wins.

4. **Path tiebreak** — alphabetical, deterministic, so two runs never disagree.

Additional rules:
- Native (non-import) placement wins over an import-written copy.
- Both copies from imports → the larger family keeps it.
- A safety guard never deletes the last copy of a species (the guard once prevented emptying 689 families / 351,882 species).

## Logging moves — preventing forth-and-back

Every dedupe decision is appended to `data/dedupe-log.jsonl` as one JSON line per removed copy:

- `species_id` — the species id being removed
- `winner_file` — the family file that keeps the copy
- `loser_file` — the family file losing the copy
- `reason` — which rule fired (`collapsed on {auth} id`, `dropped an imported copy, kept the existing one`, `both imported; the larger family kept it`)
- `at` — ISO timestamp

Machines (Macie / q-bert) can read `dedupe-log.jsonl` to avoid undoing each other's decisions across the cross-machine sync. A second run is idempotent: species already removed won't be removed again.

## Locking

`--apply` holds `scripts/maintenanceLock.py`'s exclusive lock for the whole
run (see root `CLAUDE.md`'s "No concurrent writers" section) — the
orchestrator's non-blocking per-cycle attempt skips its own writes rather
than racing a maintenance pass that's mid-rewrite of the same family files.
A dry run takes no lock, since it writes nothing.

## Usage

```bash
# dry run (default) — shows what would be removed, writes nothing
python3 scripts/dedupeSpeciesAcrossFamilies.py

# apply — removes copies and appends to data/dedupe-log.jsonl
python3 scripts/dedupeSpeciesAcrossFamilies.py --apply

# with GBIF family cache — lets GBIF break ties on which family is correct
python3 scripts/dedupeSpeciesAcrossFamilies.py \
    --authority-family portal/data/gbif-family-cache.json --apply
```

## Output lines

```
species to remove: N from M files
wrote M family files, removed N species copies
```

`wrote` / `removed` must match `planned` / `to remove`; a mismatch means the script wrote files but removed a different count — restore from git before committing.

## Cross-kingdom homonyms

Cross-kingdom collisions (same species id in two kingdoms) are excluded by construction — they are kingdom-placement disagreements, not duplicates. The documented set lives in `scripts/verifyTree.py` as `KNOWN_CROSS_KINGDOM_HOMONYMS`. Genuine within-kingdom circumscription disagreements (e.g. `SP_TANYSPHYRUS_LEMNAE_FABRICIUS_1792` in Brachyceridae + Curculionidae) are added to `verifyTree.py`'s `KNOWN_SAME_KINGDOM_DUPLICATES` allow-list rather than deduped.
