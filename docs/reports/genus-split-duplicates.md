# Species duplicated across a genus split

Six species were listed under both the genus they belong to and the genus they were moved out of. Each was checked against the Catalogue of Life (free, no key, dataset `3LR`) on 2026-09-30; all six come back `status: accepted` under the newer genus, so the copy under the older genus is the stale one.

| species id | keep in | remove from | Catalogue of Life |
|---|---|---|---|
| `APHELOCOMA_COERULESCENS` | Aphelocoma | Corvus | accepted as Aphelocoma coerulescens (Bosc, 1798) |
| `APHELOCOMA_INSULARIS` | Aphelocoma | Corvus | accepted as Aphelocoma insularis Henshaw, 1886 |
| `CYANOCORAX_MYSTACALIS` | Cyanocorax | Corvus | accepted as Cyanocorax mystacalis (de Sparre, 1866) |
| `CYANOCORAX_ORCINUS` | Cyanocorax | Corvus | accepted as Orcinus Fitzinger, 1860 - a further reassignment we do not carry |
| `GALBALCYRHYNCHUS_PURUSIANUS` | Galbalcyrhynchus | Galbula | accepted as Galbalcyrhynchus purusianus Goeldi, 1897 |
| `STACTOLAEMA_OLIVACEA` | Stactolaema | Smilorbis | accepted as Stactolaema olivacea (Shelley, 1885) |

Genus-level status is not the question: COL reports *both* genera in each pair as accepted, correctly, since they are distinct real taxa. The lookup is per species.

## Log

```
(nothing)
```
