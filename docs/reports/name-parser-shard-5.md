# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,142 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,344 | 98.38% |
| `INFORMAL` | 5,941 | 1.24% |
| `OTU` | 942 | 0.20% |
| `PLACEHOLDER` | 365 | 0.08% |
| `NO_NAME` | 219 | 0.05% |
| `DOUBTFUL` | 197 | 0.04% |
| `HYBRID` | 115 | 0.02% |
| `BLACKLISTED` | 8 | 0.00% |
| `CULTIVAR` | 8 | 0.00% |
| `CANDIDATUS` | 3 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,412 | 330 | 2,326 |
| GENUS | 0 | 154 | 33,944 |
| SUBSPECIES | 0 | 13 | 0 |
| FAMILY | 306 | 11 | 1,412 |

## Examples by type

**`INFORMAL`**

- `Dendrodrilus sp.`
- `Imetescolex sp.`
- `Diplocardia sp.`
- `Microchaetus sp.`
- `Octochaetus sp.`
- `Guaranidrilus sp.`

**`NO_NAME`**

- `NIcomache`
- `cf. Livius`
- `cf. Psiloderces`
- `cf. Mallecolobus`
- `cf. Thorelliola`
- `cf. Colopsus`

**`BLACKLISTED`**

- `Koppe no`
- `Casinaria xxx`
- `There clotho`
- `Halicoides nov`
- `Gekko nov.`
- `Trimeresurus nov`

**`PLACEHOLDER`**

- `Unplaced affine`
- `IncertaeSedis sensitivus`
- `IncertaeSedis ravanicae`
- `pr. Oreda`
- `Unplaced sordidus`
- `Unplaced quinquenotatus`

**`DOUBTFUL`**

- `Brancuporus pennifoldae`
- `[Orthocladius]`
- `[Limnophila] pallens`
- `[Limnobia] obsoleta`
- `[Diaphora]`
- `[Curtonevra]`

**`CULTIVAR`**

- `'Ochlerotatus' ('Finlaya')`
- `Neolamprologus cv.`
- `Astatotilapia cv.`
- `Guianacara cv.`
- `Coregonus cv.`
- `Heracleum 'Kungsholm'`

**`OTU`**

- `Euglossa sp. BOLD:AAC0547`
- `Euglossa sp. BOLD:AEL8906`
- `Hemigrammus cf. gracilis BOLD:AAY2122`
- `Hyphessobrycon sp. 2 BOLD:AAD0588`
- `Psalidodon cf. fasciatus BOLD:AAA7660`
- `Sardinella sp. BOLD:AAD1175`

**`HYBRID`**

- `Megalobrama skolokovii x Megalobrama amblycephala`
- `Amblystegium fluitans x aduncum`
- `Stuckenia chakassiensis   Klinkova × S. macrocarpa  Tzvel.`
- `Potamogeton alpinus × crispus`
- `Narcissus poeticus x pseudonarcissus`
- `Romulea columnae x Romulea ramiflora`

**`CANDIDATUS`**

- `Candidatus Calypsonella`
- `Candidatus Aramenus`
- `Candidatus Methanoflexus`

