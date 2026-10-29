# 2026-10-29: pipeline recovery, big pre-queue imports, WFO re-measure

A session report to read the next morning. The ordinator was left running
overnight. Everything below is committed and pushed, except the pipeline's
own in-flight output; see *Overnight* at the end.

## Big pre-queue imports: all five accounted for

Five large datasets were applied before the source queue existed, so the
queue and the dashboard's GBIF tab showed them as unknown.
`data/import-log.jsonl` shows four of them were re-run to convergence (their
last runs add 0). Those got queue entries built from that history, with a
`convergence` block (runs, total added, first/last); no re-run was needed.
Commit `2041b7e13b1`.

| Dataset | ChecklistBank | History | Queue now |
|---|---|---|---|
| GBIF Backbone | 53147 | 18 runs, 10-20..26, **+244,771** total; last runs +0 | applied |
| ITIS | 2144 | 3 runs, **+80,608**; last +0 | applied |
| UNITE | 30477 | 3 runs, **+1,246**; last +0 | applied |
| COL26.9 XR | 316441 | 3 runs, **+40,759**; last +0 | applied |
| CoL base release | 316321 | Applied pre-queue via importColStage1/2 (~1.13M species). COL XR is base + extensions, so it covers the base. | applied (covered by 316441) |
| COL26.6 XR | 315557 | Deliberately parked 10-25 | declined, superseded by 316441 |
| **World Flora Online** | 2004 | **One run on 10-05, before the pipeline fixes** | **re-measured, queued for re-apply** (below) |

**q-bert parquets** (built 10-23..25) are taxa caches for the GBIF Backbone,
COL26.6 XR (315557), the held Wikidata set, IPNI and ENA. Macie holds the
same Backbone and 315557 caches, so q-bert has nothing Macie lacks. A
316441 cache build on q-bert started but never logged "done".
q-bert's `~/src/sources/archives/gbif-backbone/` also holds two stray
2.4 GB `tmp*.jsonl` files. **Decision for you:** delete them?

## WFO: dry run against today's tree

`importColChecklist.py` without `--apply`. It took 5 min and peaked at
2.7 GB, and built both caches, so the real run is fast. Full log:
`<sources>/work/wfo-plant-list/dry-run-2026-10-29.log`.

| | |
|---|---|
| Accepted species offered | 408,939 |
| Already held (skipped) | 308,761 |
| Staged into families we hold | 72,091 |
| → genuinely new | **751** |
| → already present, would merge (WFO provenance in the current format) | 71,266 |
| Refused (needs a family we don't have) | 275 across 6 families, recorded in the pending store |

Queued as `checklistbank-2004` at `downloaded` (commit `49e86a6c44e`).

### The bigger finding: 4,426 species WFO places in a different family

The apply does **not** move these; they stay where they are until someone
decides. Almost all are modern family concepts (APG IV for flowering plants,
PPG I for ferns) that our tree predates. There are 286 family pairs; the top
20 are below. Full list, one JSON line per species:
`<sources>/work/wfo-plant-list/family-diff-2026-10-29.jsonl`.

| Our family | WFO family | Species |
|---|---|---|
| Polypodiaceae | Dryopteridaceae | 1,346 |
| Viscaceae | Santalaceae | 327 |
| Polypodiaceae | Tectariaceae | 268 |
| Hyacinthaceae | Asparagaceae | 244 |
| Thesiaceae | Santalaceae | 183 |
| Turneraceae | Passifloraceae | 134 |
| Sterculiaceae | Malvaceae | 108 |
| Valerianaceae | Caprifoliaceae | 99 |
| Scrophulariaceae | Plantaginaceae | 97 |
| Scrophulariaceae | Orobanchaceae | 67 |
| Dicranaceae | Leucobryaceae | 63 |
| Aspleniaceae | Athyriaceae | 60 |
| Asaraceae | Aristolochiaceae | 54 |
| Polypodiaceae | Davalliaceae | 49 |
| Malvaceae | Thymelaeaceae | 48 |
| Polypodiaceae | Lomariopsidaceae | 47 |
| Quiinaceae | Ochnaceae | 42 |
| Parnassiaceae | Celastraceae | 42 |
| Clusiaceae | Hypericaceae | 39 |
| Pylaisiaceae | Hypnaceae | 38 |

Most rows are lumps of older segregate families into the accepted modern
family. **Malvaceae → Thymelaeaceae (48)** runs the other way and looks like
one misplaced genus on our side; it is worth checking first. **Decision for
you:** adopt WFO's family placements (a structure pass, in line with "a
better inventory beats more volume"), family by family or wholesale.

## Pre-pipeline re-takes (earlier in the session)

28 sources applied before the queue existed are queued for a fresh pass:
- 8 at `downloaded`, with the archive already on disk;
- 20 at `candidate`, which the ordinator downloads: Species Files, ILDIS,
  Reptile DB, Craneflies, Afrotropical Bees, Afromoths, ICTV.

Commit `93aae505add`. Licence questions surfaced by that inventory are in
[`../licence-issues.md`](../licence-issues.md): Vermont NC, MycoBank's
three licence statements, AlgaeBase, and others.

## Overnight

- **Running:** `import-ordinator --loop` under `caffeinate -dimsu`
  (dashboard :8090), and `importwrite` on :8089. Logs:
  `/tmp/import-ordinator.log`, `/tmp/importwrite.log`.
- **Apply timeout raised to 180 min** (`APPLY_TIMEOUT=180`). With the
  30-minute default, DAISIE (25428, 6,240 records across ~300 families)
  timed out, and the WFO apply is about 11× bigger. DAISIE was requeued to
  apply from its existing transform. **Make 180 the default** in
  `cmd/import-ordinator/main.go`, or the next plain restart brings the
  timeouts back.
- **Download path verified live:** Craneflies (1005) was fetched by the
  ordinator with the bare ChecklistBank key (3.4 MB, sha256 logged).
- **Blocked, needs a look:** 274774 *COL XR Patch* (1 species), "txtree
  format". The committed transform path can't read .txtree; the reader is
  on the parked `wip/2026-10-27-inprocess-driver` branch (and is part of
  what was parked for its unknown-rank → species heuristic).
- **Queue at 22:35:** 20 candidate, 32 downloaded, 1 transforming,
  279 applied, 9 declined, 48 blocked, 1 error→requeued.

### Morning checklist

1. Dashboard :8090, Pipeline tab: anything in `error`? Did WFO (2004) and
   DAISIE (25428) reach `applied`?
2. Commit the pipeline's tree output only after a clean pass:
   `dedupeSpeciesAcrossFamilies.py --authority-family
   portal/data/gbif-family-cache.json --apply`, then
   `resyncFamilyCounts.py --apply`, then `make species-parquet`, then
   `make check`. Commit only when it's green, so CI stays green.
3. Decide: WFO family placements; q-bert temp files; the 274774 txtree
   reader; the licence calls in `licence-issues.md`.
4. GBIF tab: 837 undecided sets. Skip the CoL China 2022/2023 editions
   (2025 is held).
