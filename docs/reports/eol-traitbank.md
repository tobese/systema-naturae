# EOL TraitBank — Zenodo 22927080 and 22129810

## What these records are

**`22927080`** — "Encyclopedia of Life's TraitBank: Neo4j Graph Database Archive
and Example Cypher Queries", Schulz & Hammock (Hammock is the EOL administrator
the backlog said to contact for a key). **Published 2026-09-23, nine days ago.**
CC-BY 4.0. A 15 GB Neo4j v5.2.30 dump plus sample Cypher queries.

**`22129810`** — "All trait data". **592 MB**, five CSVs:
`pages.csv`, `traits.csv` (6.2 GB uncompressed), `metadata.csv`, `inferred.csv`,
`terms.csv`. Licence `notspecified`.

Same content, no Neo4j. **`22129810` is the one to use** — the dump in 22927080
is a Java bootstrap script requiring Neo4j 4.2.19/5.2.30 and Java 21 to read, and
this machine has Java 17 and no Neo4j.

## The backlog was half right

`BACKLOG.md` says of EOL:

> EOL's publishing/traits API needs an admin-issued JWT ("contact hammockj AT
> si.edu"), returns structured traits rather than prose, and has no field in our
> schema.

Both halves hold. **Hammock has now published a full CC-BY archive**, so the
JWT is no longer the only route. And the data is still structured traits, not
prose, still with no field in our schema.

## Measured

11,394,558 trait rows, 11,389,932 with a value, **2,516,119 distinct species
names**, each row carrying `scientific_name` as a join key.

Against our undescribed species:

| kingdom | undescribed | EOL has traits | yield |
|---|---|---|---|
| fungi | 157,690 | 18,293 | **11.60%** |
| plantae | 110,226 | 9,404 | 8.53% |
| protozoa | 3,817 | 289 | 7.57% |
| animalia | 398,730 | 10,164 | 2.55% |
| archaea | 1,942 | 46 | 2.37% |
| chromista | 73,840 | 1,592 | 2.16% |
| **total** | **746,245** | **39,788** | **5.33%** |

Highest yield of anything measured today, and on fungi — the weakest kingdom.

## Why it is still not a description source

Inspected 3,014 undescribed fungal species that carry a non-trivial trait. The
values are **ontology URIs, not text**:

```
lichenostigma subradians    EcomorphologicalGuild   .../terms/lichenicole
corollospora portsaidica    RO_0002303 (habitat)    .../ENVO_00000447
hypotrachyna palmarum      FLOPO_0900032          .../PATO_0000402
```

`RO_0002303` alone is 682,293 rows and its "values" are ENVO terms — 107,696 of
them the single URI `ENVO_00000446` (marine habitat). There are **571** values
longer than 40 characters in the entire 682,293-row habitat column.

So "39,788 species covered" means *39,788 species with an ontology-coded
classification*, not *39,788 species with prose*. Pasting `ENVO_00000446` into a
description field would be the media-caption mistake in a new costume.

## What it genuinely is worth

Not nothing — it is the only structured data source found, and three predicate
families map onto things we already track:

| predicate | rows | maps to |
|---|---|---|
| `NativeRange` / `IntroducedRange` / `InvasiveRange` | 213,722 + 88,135 + 12 | our `continents`, **native vs introduced** — a distinction we do not model at all |
| `ConservationStatus` (SPMInfoItems) | 157,853 | our `iucnStatus` |
| `ExtinctionStatus` / `population_trend` | 89,217 + 107,116 | our `extinct`, which is currently only detected from `†` or the word "extinct" in prose |

**The range one is the real find.** 213,722 native-range records against our
1,047,687 missing continents, and unlike GBIF's `locality` string these are
coded to a controlled vocabulary rather than typed by a contributor. That is the
same "controlled vocabulary vs free text" distinction that killed the GBIF
locality pass — here the data is on the good side of it.

It is a **feature, not a backfill**: adding `nativeContinents` and
`introducedContinents` is a schema change and a design decision, and native
versus introduced is information a reader genuinely wants. Whether `introduced`
belongs in `continents[]` (where GBIF's data already put everything) is a
question worth deciding before writing anything.

Also worth noting: `TypeSpecimenRepository` (1,717,340) and
`decimalLatitude`/`decimalLongitude` (221,925 each) exist but have no field in
our schema, and neither does any measurement trait — `body mass` for
`Odocoileus hemionus` reads `54213 g` from a DOI-cited source.

## Recommendation

1. **Do not treat this as a description source.** The number is 5.33% of names
   with ontology codes, and describing a lichen as `lichenicole` is not prose.
2. **Do consider `nativeContinents` / `introducedContinents`.** 213,722 rows,
   controlled vocabulary, and it fixes a real modelling gap. Measure it the same
   way as everything else before applying.
3. The measurement traits need a schema decision first — a `traits` array on
   `TaxonNode` is a bigger change than a field, and worth discussing before
   11.4M rows are ingested.

Nothing has been written from this source. The archive is unpacked at
`/Volumes/MacieExternal/tmp/opencode/eol_traits.zip`.

The open question is item 2: `nativeContinents` / `introducedContinents` is a
schema decision, not a backfill, and nothing has been taken from TraitBank until
that is settled. The `ConservationStatus` rows would slot straight into the
existing `iucnStatus`, which is the cheapest of the three if a start is wanted
somewhere.
