# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,303 | 98.38% |
| `INFORMAL` | 5,841 | 1.22% |
| `OTU` | 954 | 0.20% |
| `PLACEHOLDER` | 402 | 0.08% |
| `NO_NAME` | 209 | 0.04% |
| `DOUBTFUL` | 177 | 0.04% |
| `HYBRID` | 127 | 0.03% |
| `CULTIVAR` | 16 | 0.00% |
| `BLACKLISTED` | 10 | 0.00% |
| `CANDIDATUS` | 7 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,287 | 352 | 2,445 |
| GENUS | 0 | 153 | 33,790 |
| SUBSPECIES | 0 | 19 | 0 |
| FAMILY | 316 | 8 | 1,456 |

## Examples by type

**`INFORMAL`**

- `Notopygos sp.`
- `Euphrosinella sp.`
- `Achaetobonellia sp.`
- `Lissomyema sp.`
- `Dorvilleidae sp.`
- `Marphysa sp.`

**`NO_NAME`**

- `NIcomache`
- `cf. Hickmanolobus`
- `cf. Agelista`
- `cf. Mopsus`
- `cf. Microrchestris`
- `cf. Pholcophora`

**`OTU`**

- `Linyphiidae BOLD:AAE6136`
- `Eufriesea sp. BOLD:AEF4645`
- `Exaerete sp. BOLD:AAD7618`
- `Euglossa sp. BOLD:AAC1673`
- `Euglossa sp. BOLD:AEL8907`
- `Psalidodon cf. pampa BOLD:AAC5910`

**`VIRUS`**

- `Tidabius vector`

**`PLACEHOLDER`**

- `IncertaeSedis dubius`
- `Onychiurini IncertaeSedis`
- `Unplaced affine`
- `nr. Quasitermes`
- `pr. Miocalles`
- `Unplaced asperipennis`

**`DOUBTFUL`**

- `[Chironomus] virens`
- `[Limnobia] decasbila`
- `[Limnobia] marginepunctata`
- `[Dasymorellia]`
- `[Psychoda] obscura`
- `[Rhopaloscatopse]`

**`CULTIVAR`**

- `'Ochlerotatus' ('Finlaya')`
- `Nanochromis cv.`
- `Hemichromis cv.`
- `Rubricatochromis cv.`
- `Lepidiolamprologus cv.`
- `Lamprologus cv.`

**`HYBRID`**

- `Ectatomma sp. Neotropics x Ectatomma sp. Oaxaca 1`
- `Nidirana sp. x ZTL-2020`
- `Bufo americanus x fowleri`
- `Diplostomidae gen. sp. x mag-2019`
- `Amblystegium fluitans x aduncum`
- `Allium atroviolaceum x Allium polyanthum`

**`BLACKLISTED`**

- `There suffusa`
- `Haploops nov`
- `Amphilochus nov`
- `Halicoides nov`
- `Liljeborgia nov`
- `Hippomedon nov`

**`CANDIDATUS`**

- `Candidatus Nanobsidianus`
- `Candidatus Methanogranum`
- `Candidatus Methanomethylophilus`
- `Candidatus Nitrosoabyssus`
- `Candidatus Zestomicrobium`
- `Candidatus Lokiarchaeum`

