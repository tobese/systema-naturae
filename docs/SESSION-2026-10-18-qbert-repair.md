# Session 2026-10-18 — q-bert: 171 duplicates, a stale-parquet gate, 101 invented species

All work below is committed on **q-bert** (`agent@q-bert.bearded-panga.ts.net`,
`/home/agent/src/systema-naturae`, branch `main`), six commits ending
`be55bb40a6`. The tree was clean and all nine `verifyTree` invariants held when
the session ended. Nothing here was pushed to `origin`.

Nothing was committed on Macie, and **Macie is in the worse state** — see
*Still open* at the end, which is the first thing a reader should act on.

## Where the task stood at restart

The previous session ended mid-task with a parquet swap on q-bert. The last
thing on screen was an atomic move that had succeeded: `species.parquet` was
replaced by an `.incoming` file whose sha256 matched the expected value, and
`git status` was clean. The parquet exists so `verifyTree` can count a changed
family's species in one columnar load instead of re-parsing 14,000 JSON files —
it is a derived, gitignored artefact and `make check` reads it.

The swap had worked. The gate it feeds was failing, and the swap is what made
it fast enough to see: `make check` dropped from hanging to ~57s and immediately
reported 1 of 9 invariants red.

## Result

| | before | after |
|---|---|---|
| same-kingdom cross-family duplicate species | 172 | **1** (allow-listed) |
| `verifyTree` invariants passing | 8 / 9 | **9 / 9** |
| `make check` | fails, ~57s | **passes, ~3m39s** |
| `species.parquet` staleness | undetected | **gate fails on a stale file** |
| name-parse index key | family name | **rank path (unique per file)** |
| families without a fresh sidecar (q-bert) | 103 | **0** |
| `sourcedFrom: "ollama"` nodes | 101 | **0** |
| empty genus nodes | 0 | 12 → **0** |
| gap reports | 6h stale vs the merges | **current** |
| `sanity-queue.json` | 2026-10-16 snapshot | **current** |

Six commits:

| | |
|---|---|
| `518815a02c` | Dedupe 171 WoRMS-written cross-family copies: widen `IMPORTED` |
| `05758eb8cb` | Gate the parquet: fail a stale one, and make it rebuildable by default |
| `af7558faed` | Key name-parse sidecars on the rank path, not the family name |
| `8cb2a59287` | Regenerate gap reports after the q-bert merges |
| `47855855ec` | Purge the 101 invented species, and write the tool BACKLOG said existed |
| `be55bb40a6` | Remove the 12 genera the ollama purge emptied |

## The 171 duplicates

`make check` failed on `no species id in two families of the same kingdom: 171
unexpected`. All 172 were the **same taxon**, not homonyms: 155 had identical
names in both families, and 16 were one copy spelling the authorship into `name`
(`Cirrhipathes contorta van Pesch, 1910`) against one without, both carrying the
same `SP_` id.

The blocker was not the one the previous commit named. `645cddf37f` said a
second pass with `--authority-family` was needed because q-bert "needs the GBIF
family cache". It has one — but `fetchGbifFamilyCache.py` reports **0 keys to
fetch**, because GBIF holds no `usageKey` in more than one species of one kingdom
among these 171. That pass could not have acted on any of them.

What was blocking is that `IMPORTED = {"checklistbank", "catalogue of life"}` was
written 2026-10-05, before WoRMS ran. A `sourcedFrom: "worms"` copy therefore did
not read as import-written, so a wikipedia↔worms pair fell through to "neither
copy is an import" and the script declined. **WoRMS had written 110 of the 172.**
Adding `"worms"` resolved all of them: 110 import-copies dropped, 61
both-imported where the larger family kept it, 171 removed from 82 files.

## The parquet gate

`check_file_counts` counts a *changed* family's species out of the parquet rather
than walking the file, then pins that count to the file's **new** mtime in the
warm cache. Nothing asserted the parquet still described the tree, so a parquet
older than an edit made the tree compare its declared `speciesCount` against a
number from before the edit, and remember that answer.

`check_parquet_freshness()` now runs first in `main()` and compares the parquet
mtime against the newest family file — the same question `nameIndexStatus.py`
already answers for the name index. On a mismatch it FAILs with the fix inline,
and `_parquet_unusable()` makes both parquet readers return empty so the other
eight invariants fall back to reading files and stay correct.

Verified by touching `felidae.json`: FAIL, exit 1, the other eight still ok.
Recovered by plain `make species-parquet`.

That command needed fixing to be usable as the remedy: it defaulted `PARQUET_PY`
to the system python, but duckdb only ever lives in `.venv-parquet`, so the
documented command failed on a machine that had it and the override was buried in
a Makefile comment. It now probes the venv.

## The sidecar key collision

Migrating q-bert to sidecars exposed that the sidecar key was
`FamilyFile.slug` — the family directory's basename, which is **not unique**.
The tree holds 14,821 family documents under 14,718 distinct slugs: 103 families
are called `incertae-sedis` (the placeholder reused down dozens of phyla) and two
are called `personidae`.

Keyed on slug, all 103 write one file, so the survivor holds one family's records
and the other 102 read it back. A GBIF parse verdict is per *name string*, so
those reads return a well-formed answer about the wrong family rather than an
obvious miss. Measured before the fix: one sidecar with 7 rows standing in for 103
families, ~3,753 name pairs with no record anywhere.

`tree.sidecar_key_for()` derives the key from the rank path instead. It is a pure
function of the path, so `iter_family_files` and the name scanner — which never
pass anything to each other — cannot disagree. `assert_sidecar_keys_unique()`
checks it before anything is keyed on it, because the `_`-join is ambiguous in
principle (six directories already contain `_`) and unambiguous only by today's
directory names.

After: 14,821 sidecars, every family fresh, `nameIndexStatus` clean where it
previously reported 103 permanently stale. All 103 `incertae-sedis` sidecars hold
exactly their own names — none missing, none foreign.

`syncNameIndex.py` needed no change; it passes keys through.

## The invented species

`CLAUDE.md` bans LLM-generated content from this tree as of 2026-10-17.
`BACKLOG.md` had already resolved how to remove the residue — drop the nodes
rather than downgrade them to `sourcedFrom: "none"`, "because a species that
exists only because a model invented it should not be in a taxonomy at all" —
and named `scripts/stripBoilerplate.py` to do it. **That script had never been
committed**, so the item had been unactionable since it was written.

The new script drops a node only when it *and every descendant* are
ollama-sourced; an invented node with real species below it is reported and
skipped, and the script exits non-zero so a run cannot look clean while skipping
them.

101 SPECIES nodes across 5 families — `anthribidae` (93), `cardinalidae` (4),
`burhinidae` (2), `passerellidae`, `aegothelidae` — all of the form
*"Araeocerodes elongatus is a araeocerodes species found in its native region."*
Nothing in the tree's own checks could have caught them: each had a well-formed
`SP_` id and a path-derived uuid, because the importer generated both.
`sourcedFrom` was the only record of where they came from.

None of the 101 names appears anywhere else in the tree, so they are gone rather
than relocated, and they left the parquet (3,602,447 → 3,602,346 rows) and the
name-parse index (3,939,066 → 3,938,965 rows) with them — neither can now be
cited as though a source had confirmed they exist.

The purge emptied 12 genera that held only invented species (10 in
`anthribidae`, plus `Hesperoburhinus` and `Driophlox` — the last being the genus
`BACKLOG.md` itself quoted). Removed with `fix_empty_genera.py`; `EMPTY_GENUS` is
back to clean.

## Defects found, and what was done about them

| Defect | Status |
|---|---|
| `verifyTree` invariant 2 named `resyncFamilyCounts.py`, which maintains a *different* `speciesCount` — following the advice reports "would update 0 nodes" and leaves the gate red | fixed: the script that changes a file's species set now owns its declared count, and the failure message says which number is wrong |
| `check_missing_lineage`'s slow path was gated on `not os.path.exists(PARQUET_PATH)`, so with the parquet present but duckdb missing, `missing` stayed empty and the invariant **passed having read nothing** | fixed: now gated on whether the query actually ran |
| `parseAllNames.py --split` cannot write a sidecar and never has: an early `return 0` when nothing needs parsing skips sidecar distribution entirely, and the distribution loop iterates `List[str]` paths then reads `.sidecar_key` off them | **recorded in `BACKLOG.md`, not fixed** — so `BACKLOG.md`'s claim it "writes sidecars directly" is false, and Macie's 13,991 sidecars all came from `splitNameIndex.py` |
| `fix_empty_genera.py` parses no arguments — `--dry-run` and `--apply` are both ignored and it writes on contact | **not fixed** — one-line change, but it belongs with the fix above |
| `sanity-queue.json` was a 2026-10-16 snapshot (6,982,021 entries) against a tree yielding 6,806,677 | refreshed |

`UNRESOLVED_TAXON` went **4,940 → 58,551**, which is not from the purge. It is
from the sidecar key fix: the check now has a *current* index instead of a stale
one, so it measures for the first time. 53,611 findings that were previously
unmeasured.

## Still open

**Macie is the urgent one.** It is on a divergent commit line (`fdcf1be779`,
coldp work) and its name-parse index is worse than q-bert's ever was:

```
STALE: 8,263 family files lack a fresh sidecar   (of 14,821)
```

Those sidecars are slug-keyed and the tree has 103 `incertae-sedis` families
against 2 `incertae-sedis*.jsonl` files, so the collision is already live there.
Its monolith is from Oct 5, so its sidecars also encode a month-old tree. Until
it is rebuilt, its own status line says importers must not treat the index as an
oracle — which makes it the machine where a scaffolder run right now would
reproduce the 42,725-copy problem from `645cddf37f`.

Fixing it needs `af7558faed` on Macie, which means reconciling two divergent
lines. That is a deliberate merge, not a mechanical step. When it is done: delete
`portal/data/name-parse-index/`, then
`make name-index ARGS='--split --workers 6'` — except see the
`parseAllNames.py --split` fault above, so use `python3 scripts/splitNameIndex.py --apply`
until that is fixed.

**`BACKLOG.md:1230` — untrack five derived files, 123 MB.** All five are still
tracked (`species_id_map.parquet`, `mycobank-species.jsonl`, both
`description-lookup*.jsonl`, `full-run.trace.json.json.gz`). Its prescription is
`git-filter-repo` plus **force-push**, and Macie is divergent, so it needs both
machines and an explicit decision. `.git` is 4.6 GB. The related near-limit risk
has already gone: `gbif-cache-aves.json` and `gbif-cache-mammalia.json` are no
longer tracked.

**Deferred by choice:** a precondition on the scaffolders so they refuse to run
without a usable parquet. The freshness gate now catches the consequence at
`make check` time rather than letting it go silent, which is why it was deferred.

**Untouched:** `SPECIES_ID_REPEATED 8`, `DUPLICATE_GENUS 161`,
`ACCESSION_NAME 2,490`. `UNRESOLVED_TAXON 4,940` (now 58,551) wants its own pass.
Each is report-only, not a gate failure.

## Notes for the next session

- `make check` needs `SHELL=/bin/bash` on q-bert — `SHELL=/bin/zsh` is set in
  the agent profile and zsh is not installed there.
- The 841 MB monolith is **kept on purpose**. It holds 4.18M parse verdicts that
  regenerating would cost GBIF calls, so it is the only cheap recovery path if
  the sidecars are ever wrong.
- `taxonomy/` holds ~3,784 bacteria and ~393 viruses families that are a known
  artefact of a past import, unreachable and deliberately not acted on. See
  `CLAUDE.md`.