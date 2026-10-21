# Session 2026-10-21 — pending families: archaea trial, then four kingdoms

Commits: `5a903adf32f` (archaea), `108df3f75f9` (placement diff log), `95d1a4b3b92`
(protozoa), `f576b9a0a4d` (plantae), `d329042a294` (chromista), `3543b3e01c6` (fungi).

## Where it started

Not with animalia. The scaffolding pass began with **archaea**, deliberately: seven
families, small enough to run dry, inspect, apply, build and verify end to end before
committing to the several thousand families the store claimed were missing. Animalia
is where the *pending-family work* began — the store, the refusal recording, the
placement diff log all come out of the GBIF backbone import, whose batches were
animalia-first — and animalia still holds 6,708 of the 10,689 missing backbone
families. It is simply the last one to be scaffolded, not the first.

## The store was stale

`/Volumes/MacieExternal/sources/pending/families.jsonl` had been seeded on
2026-10-05 and nothing retires rows, so by 2026-10-21 it claimed hundreds of families
we already held and species counts the backbone no longer gives. The archaea trial
made this visible: the store attributed 17–63 species to five families the current
backbone has zero accepted species for, because `cmd_seed` counts species rows whose
family-rank row happened to be seen earlier in `Taxon.tsv` — an order-dependent count.

Re-seeded against `gbif-backbone:53147`: **18,466 rows** (10,689 GBIF + 7,777
non-GBIF), backup at `families.2026-10-21.bak.jsonl`. `scaffoldFamilies.py` now
derives `speciesCount` from `Taxonomy.tsv` in the same streaming pass that builds the
chains, and warns when the store disagrees.

## Result per kingdom

| kingdom | families before | familias added | families now | species unlocked | species added |
|---|---|---|---|---|---|
| archaea | 379 | 7 | 386 | 160 | 1 |
| protozoa | 108 | 220 | 328 | 272 | 260 |
| plantae | 1,272 | 311 | 1,583 | 1,137 | 1,127 |
| chromista | 1,002 | 877 | 1,879 | 1,706 | 1,618 |
| fungi | 1,193 | 1,234 | 2,427 | 261 | 244 |
| **total** | | **2,649** | | **3,536** | **3,250** |

"Unlocked" is what the scaffolding made importable; the difference is species the
backbone places in a family where the tree already holds them, which is recorded in
the placement diff log rather than added twice. The archaea gap (160 vs 1) is the
stale-store effect above, now corrected in five nodes.

Fungi is the outlier in shape: 1,091 of its 1,234 families are name-only shells — a
family-rank row in the backbone with no species under it and no ancestor chain — so
they land directly under kingdom Fungi with `speciesCount: 0`. Plantae (105) and
chromista (6) have the same kind of shell. Flagged in `BACKLOG.md` because it is a
policy question, not a defect.

## Cross-kingdom collisions

Four ids unlocked by the scaffolding collided with species held under another
kingdom. Each was confirmed against `Taxonomy.tsv` and resolved by removing the side
GBIF disagrees with, not by allow-listing:

| species | removed from | source of the bad copy | GBIF says |
|---|---|---|---|
| *Ebria fornix* | chromista / Dictyochaceae | checklistbank (ITIS 1815) | Protozoa / Ebriaceae |
| *Myospora metanephrops* | fungi / Microsporea incertae sedis | COL 456B5 | Protozoa / Microsporidia |
| *Stictis radiata* | protozoa / Didymiaceae | checklistbank-2008 49952 | Fungi / Stictidaceae |
| *Dinothrix paradoxa* | animalia / Rhinidae | checklistbank 1697652 | Chromista / Dinotrichaceae |

Each removal also deleted the genus left empty and corrected the declared count in
both the taxonomy input and the family data file. `checklistbank-2008`'s habit of
filing ascomycetes as slime moulds is noted in `BACKLOG.md`; it predates the
dataset-scoping fix on `sourceIds`.

## Verification

- Every scaffolded kingdom rebuilt clean; animalia rebuilt after the Rhinidae removal
  (2,382,904 physical nodes).
- `make species-parquet` after each change.
- `make check`: **the same four failures before and after**, all pre-existing and
  documented: plantae 5 families / 7 species understated, fungi 2 / 5, 329 undeclared
  cross-kingdom homonyms (the Actinocyclus batch plus long tail), 347 authority-id
  collisions. No new homonym survives this session — the set is 329, was 329.
- Placement diff log regenerated over the whole tree: 34,135 species in 4,057 pairs
  (`docs/gbif-placement-diffs.md`).
- Pending store after all five passes: 3,413 families now present in the tree
  (2,642 of them gbif-backbone:53147), the rest from older archives to be re-run.

## Decisions left open

1. **Empty families at the kingdom root** — 1,202 shells in total (1,091 fungi,
   105 plantae, 6 chromista). Keep, drop, or require a placement before scaffolding.
2. **MycoBank authorship** — the index is built and compared (28,253 disagreements
   with GBIF) but not applied. Species ids hash name+authorship, so applying it is a
   rename/migration pass, not a metadata edit.
3. **Triage the 329 homonyms and 347 authority-id collisions** — untouched, mostly
   the *Actinocyclus* animalia/chromista batch.
4. **Animalia** — 6,708 backbone families remain, plus the already-present families
   from other archives; a build there is the expensive one and can run on q-bert.

## Note on q-bert

q-bert is reachable (`agent@q-bert`, 22 cores, 742 GB free) but its
`~/src/systema-naturae` checkout is over 1,000 commits behind `main` and carries
2,742 uncommitted files from its own source-queue work, so it was not used for
builds this session. A fresh worktree would be needed to offload the animalia build.
