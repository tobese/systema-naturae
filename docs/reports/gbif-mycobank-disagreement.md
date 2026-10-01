# GBIF vs MycoBank: who says a fungal name is superseded

GBIF Species API `v2/species/match` vs the `Current name` column of MycoBank's `MBList.xlsx`, over the names MycoBank flags as superseded.
Measured 28,620 names.

| verdict | count | share | meaning |
|---|---|---|---|
| `disagree-gbif-keeps` | 28,253 | 98.7% | MycoBank wants to move it; GBIF has ours as accepted |
| `gbif-does-not-know` | 366 | 1.3% | GBIF could not place the name (matchType NONE/HIGHERRANK) |
| `disagree-third-name` | 1 | 0.0% | both name an accepted taxon, and they are different names |

## Examples

| ours | MycoBank | GBIF verdict | detail |
|---|---|---|---|
| Karlingia lobata | Karlingiomyces lobatus | `disagree-gbif-keeps` | gbif=ACCEPTED conf=99 |
| Synchytrium phaseoli | Protomycopsis phaseoli | `gbif-does-not-know` | matchType=HIGHERRANK conf=97 note='' |
| Pestalozzia | Seiridium | `disagree-third-name` | gbif synonym of 'Gynostemma', mb -> 'Seiridium' |
