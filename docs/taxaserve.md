# taxaserve

An in-memory taxonomy lookup service. It answers "do we already hold this name,
and where?" from memory instead of re-reading 2.5GB of family JSON every time.

```bash
python3 scripts/taxaserve.py                # serve on 127.0.0.1:9882
python3 scripts/taxaserve.py --build-only   # build the indexes, report, exit
```

Then point any tool at it:

```bash
export TAXASERVE=http://127.0.0.1:9882
python3 scripts/sampleDatasetOverlap.py 1021 1022 1023
```

Every tool falls back to reading the tree when the variable is unset or the
service is not answering, so nothing depends on it running.

## Why it exists

Fourteen scripts answer this question, and each one answers it from scratch:

| script | what it re-reads |
|---|---|
| `sampleDatasetOverlap.py` | all 14,085 family files, to build a held-set |
| `importColStage2.py` | the 544MB canonical-name index |
| `importColChecklist.py` | one kingdom's family files, for its held-check |
| `dedupeSpeciesAcrossFamilies.py` | every family file, twice |
| `fixSpeciesLineage.py`, `resyncFamilyCounts.py`, `dedupe_genera_*.py` | the same, again |

The cost is not hypothetical. `sampleDatasetOverlap.py` called `held_names()`
five times for animalia alone — three of them inside an f-string — and each call
re-reads all 10,601 animalia family files. Five passes over 14,085 files ran
before the first API request, and triaging three datasets did not finish in 30
minutes. The same six datasets now take **19.8 seconds** through the service,
and produce identical numbers (88.3 / 96.7 / 95.8 / 96.7 / 83.7 / 100%).

## What it holds

Built once at startup, ~44s, ~1.2GB resident:

- **held** — 2,506,049 species names → (kingdom, family, genus) across all six
  kingdoms. Family and genus strings are interned, so 2.5M rows share ~14k
  family and ~206k genus strings instead of one apiece. Without interning this
  is 1.2GB of mostly repeated text.
- **parse** — 2,735,539 name → canonical-form mappings from
  `portal/data/name-parse-index.jsonl`. Served rather than recomputed because
  `taxamatch.parse_names()` shells out to GNparser, an external binary.
- **pending** — the 11,765-family pending store from
  `/Volumes/MacieExternal/sources/pending/families.jsonl`.

## Endpoints

| | |
|---|---|
| `GET /health` | liveness, index sizes, build seconds |
| `POST /held {"names":[…]}` | which are held, and where |
| `GET /held?name=A&name=B` | same, GET form |
| `POST /parse {"names":[…]}` | canonical form per name |
| `GET /parse?offset=&limit=` | the whole parse index, paged |
| `GET /stats` | per-kingdom counts, families, genera |
| `GET /pending?scaffoldable=1` | the pending-family store |
| `POST /reload` | rebuild after a write |

## Staleness

A cache over files that importers rewrite is only safe if it cannot lie quietly,
so three things are deliberate:

1. **`/held` answers *where*, not just *yes*.** A caller that gets `[]` for a
   name it expected to hold can see that the family is wrong. A bare boolean has
   no such tell — which is exactly what `held_names()` returned in the importers,
   and why the Craneflies and ILDIS verdicts disagreed with the tree by 15,000
   species in opposite directions.
2. **Every response carries `indexed` and `treeMtime`.** A caller can compare
   that against its own view of the tree. `indexed` is when the index was built,
   `treeMtime` is the newest family file at that moment; if a caller has written
   since, it knows to `POST /reload`.
3. **`POST /reload` exists and is cheap** (same ~44s as startup). After an
   `--apply`, reload before the next tool runs. A stale index is not a
   correctness problem here, it is a `POST` away.

`canonicalNames._load()` prefers the service over the 544MB index file when
`TAXASERVE` is set. The index is a snapshot, and it has been on the wrong side
of that fact repeatedly: 13,347 of 16,371 ILDIS legumes scored as held when 64
were, and 15,563 Cranefly species scored as new when 15,191 were held. The
service rebuilds the same table from the family files, so it is never a snapshot
of anything but the current tree.

## Two bugs found while measuring, both silent

Worth recording because both produced plausible numbers rather than errors.

**Genus must not come from `lineage`.** That field holds three different things
in this tree: the genus for most species, the *family* for the 980,786 an
importer wrote that way (fixed in `4cc40bcbf`'s predecessor, `b1fc73ae6`), and a
**superseded genus** for 1.17M plantae — `Gyroporella pauciforata` carries
`lineage: "Physoporella"`. Reading it as the genus made `Homo sapiens` report
genus `human`, because that species' `lineage` field holds its common name.
`/held` takes the genus from the GENUS node the species structurally hangs
under.

**Leading daggers must be stripped.** `†Progonocimicidae` appears in our family
files but not in the name lists tools sample. `held_names()` stripped the dagger;
the service did not at first, and OSF scored 84.7% through the service against
88.3% from the tree. Both paths normalise now, and
`sampleDatasetOverlap.py` refuses to record a verdict if the served path reports
0 of 600 sampled species held.

## Modeled on

`scripts/dbserved.ts`, which already does this for the Wikipedia plant DB:
stdlib, no dependencies, JSONL on disk. Neither service has invalidation logic,
which is the obvious next thing to fix in both.
