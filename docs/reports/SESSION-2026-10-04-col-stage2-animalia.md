# Session 2026-10-04 — COL Stage 2: Animalia applied, three structural bugs fixed

Committed as `a268f11c0`; the file itself rode along in that commit. Macie restarted
mid-task twice, so this session picked the import up from where the previous one left
it, and the parts below are written as they stood at the first restart.

## Where the task stood at restart

The pre-restart session had **finished** the Animalia run of
`scripts/importColStage2.py` (taxonomy.json written 07:46, 5,185 family files touched
07:40–07:46) and had written `scripts/addAnimaliaStage2Themes.py` at 07:51 without
running it. So the import itself did not need re-running — only the colour pass,
verification, and the commit.

`/Volumes/MacieExternal` is **not mounted** after the restart (`diskutil list external`
is empty; only `MacieExtOld` is). The COL DwCA
(`…/sources/archives/catalogue-of-life-2025/col2026-base_dwca.zip`) lives there, so
`importColStage2.py` cannot be re-run until the drive is back. Everything below was
done against the tree the previous run left behind.

## Result

| | before | after |
|---|---|---|
| families | 5,472 | **10,601** |
| orders | 394 | **721** |
| classes | 75 | 119 |
| phyla | 32 | 33 |
| species | 1,033,411 | **1,705,596** |
| manifest orders | 394 | 721 |

Verification, all green:

- `cd portal && sh scripts/buildData.sh` — 10,601/10,601 families resolved, no missing files
- `cd portal && npm run typecheck` — clean
- `npx tsx scripts/testFamilyPaths.ts` — "OK: every family's directory matches its taxonomy rank path"
- `npx tsx scripts/testDataContract.ts` — **72 passed, 1 skipped, 0 failed** (the skip is
  the opt-in `SN_BUILD_UNIFIED=1` monolith)

## Three bugs found, all from the same root cause

The importer scaffolds an order or family literally named `Incertae sedis` wherever COL
declines to say where a taxon sits. `SF.node_id(prefix, name)` builds an id from the
name alone, which is unique for a real taxon name and useless for a placeholder.

**1. Duplicate FAMILY nodes.** The importer matches a family we already hold only
within the *same parent order*. 23 insect families are held already and COL puts them
elsewhere — Progonocimicidae under Coleorrhyncha for us, under Hemiptera for COL — so
the run added a second node with the same `appSlug` and a second data directory beside
the first. `scripts/fix_duplicate_family_nodes.py` folds the COL copy into the curated
one: the two share exactly one species name across all 23, so the merge is 137 species
gained and nothing lost. `personidae` is left alone on purpose — a real name collision
between a gastropod family and an insect family, both pre-existing. Reculida held seven
families, all seven duplicates, so the order went with them.

**2. Duplicate node ids, which cost data.** 21 orders shared `ORDER_INCERTAE_SEDIS`; the
manifest keys order files by order id, so 20 of them wrote to the same file and their
families were unreachable from the UI — the build wrote 721 order files and the manifest
came out with 701. Same for families: `FAM_INCERTAE_SEDIS` ×91 in fungi and ×12 in
chromista (both already committed). `scripts/fix_duplicate_node_ids.py` qualifies
colliding ids with their ancestry in the style the tree already uses for
`SCAPHOPODA_UNKNOWN` — `FAM_INCERTAE_SEDIS` under Dothideales becomes
`DOTHIDEALES_INCERTAE_SEDIS`. It also syncs family data files that still carry a
*shared* id, and deliberately ignores the 140 animalia files that disagree with their
node uniquely (`cetacea.json` says `CET`) — different question, predates this work.
`importColStage2.py` now mints unique ids itself, via a `new_id()` closure seeded from
the loaded trees.

The `sum of order _speciesCount is within 1% of rankCounts.SPECIES` assertion went from
a 22,593-species gap (1.32%, and failing before this session too) to 1,495 (0.09%).
Almost all of it was the 20 lost orders.

**3. The colour registry was written into the wrong place.**
`scripts/addAnimaliaStage2Themes.py` found the registry's closing brace with
`tail.rindex("};")`, and this file ends with `export { PORTAL_THEME };` — so 5,129
themes were spliced through the end of the file, producing
`export { PORTAL_THEME   "abacionidae": S2_ABACIONIDAE_THEME,`. Caught by reading the
result rather than the diff. `portal/src/colorRegistry.ts` was restored with
`git checkout` and rewritten with a brace-matching `end_of_object()`. The same script
had a second bug: it built its "already themed" set with a regex that discarded quoted
keys, and 4,696 of the 5,472 registry keys are quoted, so it thought 9,923 families
needed themes instead of 5,129.

Also fixed: 24 families whose data file holds more species than their node's
`speciesCount` claims (the Coverage modal reported them as over-full — Cebidae 143 vs
130, and the 22 merges), and `testDataContract.ts`'s structural snapshots, refreshed by
hand as that file intends after an import of this kind.

## Working tree (uncommitted)

168 modified, 1,178 untracked.

- `portal/data/taxonomy.json` — 5,152 new families, 328 new orders, 24 raised speciesCounts
- `taxonomy/animalia/**` — 5,152 new family files, 33 enriched in place, 23 directories
  removed as duplicates
- `portal/src/colorRegistry.ts` — +5,129 themes (1.8 MB → 3.8 MB; the Fungi and Plantae
  registries are 542 KB and 613 KB, so this is in line with the existing convention)
- `portal/data/taxonomy-{fungi,chromista}.json` — 112 and 15 id renames, plus 105 family
  data files whose root id was resynced
- `scripts/importColStage2.py` — `new_id()`, and part A now runs before B and C so an
  existing family beats a new one for a contested name
- `portal/scripts/testDataContract.ts` — snapshots
- `portal/scripts/testBuild.ts` — spawn timeout 60 s → 30 min; the animalia build went
  from ~50 s to ~4.5 min and the test was reporting a spawn timeout rather than
  whatever it meant to test
- new: `scripts/addAnimaliaStage2Themes.py`, `scripts/fix_duplicate_family_nodes.py`,
  `scripts/fix_duplicate_node_ids.py`

## Known gap — closed after the first restart, verified after the second

**Four COL species of Atactophlebiidae were lost.** The first run of
`fix_duplicate_family_nodes.py` wrote one merged file, then crashed on an `rmdir` before
writing `taxonomy.json`. Rolling that back restored the tracked file, which discarded the
four species it had just merged. Three of the four names were known (Malmyzhia kazanica,
Issadophlebia fusa, Novokshonovus boreus); the fourth was not.

They are back. A re-run of the now-idempotent merge restored them once the volume was
mounted, and the family carries all nine of its species — including the fourth,
**Novokshonovus ignoratus**, which the DwCA identified.

`scripts/restore_atactophlebiidae_species.py` was written to close the gap by taking
COL's own species list for the family as the authority and adding only what is missing.
It is kept because that is the check worth repeating, but it now reports *nothing to do
(already complete)*, which is how the gap was confirmed closed rather than assumed.

## What is left

1. ~~Commit the above.~~ Done — `a268f11c0`.
2. **Bacteria + viruses Stage 2** — ~43k species. Needs two kingdoms added to
   `portal/data/kingdom-config.json` first; `importColStage2.py` refuses a kingdom the
   config does not declare rather than writing data nothing will load. Was blocked on
   `/Volumes/MacieExternal`; the volume is mounted again, so this is next.
3. Update `docs/dataset-inbox.md` and the `catalogue-of-life` manifest entry, which
   still say Animalia Stage 2 is "not yet applied".