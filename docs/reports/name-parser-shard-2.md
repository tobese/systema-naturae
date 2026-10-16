# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,143 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,459 | 98.40% |
| `INFORMAL` | 5,803 | 1.21% |
| `OTU` | 961 | 0.20% |
| `PLACEHOLDER` | 397 | 0.08% |
| `NO_NAME` | 200 | 0.04% |
| `DOUBTFUL` | 172 | 0.04% |
| `HYBRID` | 119 | 0.02% |
| `CULTIVAR` | 13 | 0.00% |
| `BLACKLISTED` | 9 | 0.00% |
| `CANDIDATUS` | 9 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,474 | 345 | 2,420 |
| GENUS | 0 | 135 | 33,740 |
| SUBSPECIES | 0 | 18 | 0 |
| FAMILY | 313 | 12 | 1,464 |

## Examples by type

**`INFORMAL`**

- `Mesenchytraeus sp.`
- `Chamaedrilus sp.`
- `Propappus sp.`
- `Odontobdella sp.`
- `Salifidae sp.`
- `Righiodrilus sp.`

**`NO_NAME`**

- `cf. Hamingia`
- `cf. Oweniidae`
- `cf. Agelista`
- `cf. Mopsus`
- `cf. Hemistus`
- `cf. Glipostena`

**`PLACEHOLDER`**

- `uncultured`
- `IncertaeSedis justi`
- `Thalassaphorurini IncertaeSedis`
- `IncertaeSedis crassicornis`
- `nr. Opsidota`
- `Unplaced australicus`

**`BLACKLISTED`**

- `Stenus mon`
- `Abantis ja`
- `There oldenlandiae`
- `Liljeborgia nov`
- `Hippomedon nov`
- `Aequidens nov`

**`DOUBTFUL`**

- `[Haplusia]`
- `[Chironomus] incertus`
- `[Agromyza] flava`
- `Culicidae P_321_FSTCO`
- `[Asilus]`
- `[Limnobia] fuscofemorata`

**`VIRUS`**

- `Euragallia prion`

**`OTU`**

- `Eufriesea sp. BOLD:AEM5056`
- `Eulaema sp. BOLD:AAM5237`
- `Exaerete sp. BOLD:AAD9729`
- `Euglossa sp. BOLD:ABY5852`
- `Astyanax sp. BOLD:AAB3435`
- `Hasemania sp. BOLD:AAO6055`

**`CULTIVAR`**

- `Lunulites 'spiralis'`
- `Coptodon cv.`
- `Oreochromis cv.`
- `Congochromis cv.`
- `Chalinochromis cv.`
- `Thoracochromis cv.`

**`HYBRID`**

- `Pundamilia sp. nyererei-like x Pundamilia sp. pundamilia-like`
- `Etheostoma sp. x JW-2022`
- `Alisma lanceolatum × plantago-aquatica`
- `Philodendron pedatum x P. squamiferum`
- `Allium atroviolaceum x Allium polyanthum`
- `Scilla forbesii × luciliae`

**`CANDIDATUS`**

- `Candidatus Harpocratesius`
- `Candidatus Methanoglobus`
- `Candidatus Halobonum`
- `Candidatus Methanofrustulum`
- `Candidatus Nanopusillus`
- `Candidatus Methanoplasma`

