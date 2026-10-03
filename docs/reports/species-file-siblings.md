# Species File Group — eight sibling checklists

**Status: downloaded and assessed, not imported.** Everything needed to import
them is in place; the hold is described at the end.

Found by following the Orthoptera Species File's own publisher rather than
guessing URLs: GBIF dataset `af66d4cf-…` has `publishingOrganizationKey`
`47a779a6-a230-4edd-b787-19c3d2c80ab5`, which is **Species File Group**, and
querying that publisher returns **17 datasets**, of which 16 are checklists.

All 16 are **CC BY 4.0**. All were last modified in GBIF on **2019-01-14** —
seven years stale as of retrieval, which is a caveat on currency, not on licence.

## What we already had

| Dataset | In our tree? |
|---|---|
| Orthoptera Species File | imported — 80 families, 28,081 species (`36a3b591d`) |
| Psocodea Species File | yes — 54 families |
| Embioptera Species File | yes — 12 families |
| Mantophasmatodea Species File | probably inside OSF — it yielded `eumastacidae` and `triassomantidae` |

## The eight missing ones

Taxa are DwCA rows, not accepted-species counts.

| Dataset | GBIF key | Taxa | Distinct localities |
|---|---|---|---|
| Phasmida Species File (stick insects) | `598678e4` | 5,144 | 212 |
| Plecoptera Species File (stoneflies) | `fbab0194` | 5,471 | 338 |
| Mantodea Species File (mantises) | `99948a8b` | 4,046 | 70 |
| Dermaptera Species File (earwigs) | `71e3fb9b` | 2,930 | 16 |
| Grylloblattodea Species File (rock crawlers) | `bc1d816e` | 1,000 | 30 |
| Zoraptera Species File | `f5f4d316` | 71 | 45 |
| Coleorrhyncha Species File (barklice) | `db93cee5` | 184 | 11 |
| Chrysididae Species File (cuckoo wasps) | `490cff72` | 268 | 63 |

Together that is roughly **19,100 taxa across eight groups we hold none of** —
Dermaptera, Mantodea, Phasmida, Plecoptera, Grylloblattodea, Zoraptera and
Coleorrhyncha are all absent from `taxonomy.json`, and Chrysididae would take
Hymenoptera from 4 families to 5.

Not pursued, but available from the same publisher: Aphid Species File,
Lygaeoidea, Coreoidea, World Auchenorrhyncha Database (an OCCURRENCE dataset,
so a different shape).

## Why this is cheap

The eight archives have **byte-identical file sets** to Orthoptera:

```
eml.xml  meta.xml  taxon.txt  distribution.txt  vernacularname.txt
multimedia.txt  speciesprofile.txt  typesandspecimen.txt  reference.txt
description.txt
```

Same `taxon.txt` columns (`id`, `parentNameUsageID`, `acceptedNameUsageID`,
`taxonomicStatus`, `taxonRank`, `scientificNameAuthorship`), same TDWG
localities, same `valid` status vocabulary. `scripts/importSpeciesFile.py` was
renamed from `importOrthoptera.py` for exactly this reason and works unchanged
once given `--src` and an output order.

Downloaded and unpacked at `/Volumes/MacieExternal/tmp/opencode/sf_<name>.zip`
and `sfx_<name>/`.

## Locality mapping

The union across all eight datasets is **381 distinct TDWG place names**, and the
Orthoptera table already covered 94.2% of them. `scripts/osfLocalities.py` was
extended with the 22 that were missing — Aleutian Is., Antipodean Is.,
Belorussiya, Central American Pacific Is., Desventuradas Is., Easter Is.,
Føroyar, Greenland, Kermadec Is., Laccadive Is., Mozambique Channel Is.,
Northern Europe, Northwestern Pacific, Nunavut, Selvagens, South China Sea,
South-Central U.S.A. and others — giving **375 of 381 mapped (98.4%)**.

Six remain unmapped, five of them on purpose (Aldabra, Chagos Archipelago,
Netherlands Antilles, Palestine, Rodrigues — subantarctic or political).

## Why this is on hold

`osfLocalities.py`'s self-audit reports `Desventuradas Is.` as unmapped, while a
direct `LOCALITY_TO_CONTINENT.get('Desventuradas Is.')` in the same interpreter
returns `['North America']` — and a plain `dict` walk over the same file says it
is absent. Same process, same argument, two answers. `CONTINENTS` in the
committed Orthoptera data are all valid (36,772 values, 0 invalid), so the
importer's output is sound; the disagreement is confined to the audit path and I
could not explain it.

That is not a good enough state to import eight more orders into unattended. The
mapping is the one place where a silent error would write confidently-wrong
continents onto ~19,000 nodes, and a self-check that contradicts itself is
exactly the kind of thing that hides a real bug until much later.

### To pick this up

1. Rebuild `scripts/osfLocalities.py` from scratch rather than by further
   patching — it has been edited by string surgery enough tonight that a clean
   regeneration is faster than continuing to diagnose it. Emit the table as JSON
   and load it, so there is no module-level construction to go wrong.
2. Make the importer **assert every continent value it writes** against
   `VALID_CONTINENTS` before the file is committed. That is the check that
   actually matters, and it is straightforward to verify.
3. Then import in order of size: Phasmida, Plecoptera, Mantodea, Dermaptera,
   Grylloblattodea, Zoraptera, Coleorrhyncha, and Chrysididae as a family under
   the existing Hymenoptera order rather than as a new one.
