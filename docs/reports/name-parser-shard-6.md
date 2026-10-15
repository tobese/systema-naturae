# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,046 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,182 | 98.35% |
| `INFORMAL` | 5,963 | 1.25% |
| `OTU` | 951 | 0.20% |
| `PLACEHOLDER` | 394 | 0.08% |
| `NO_NAME` | 215 | 0.05% |
| `DOUBTFUL` | 186 | 0.04% |
| `HYBRID` | 126 | 0.03% |
| `CULTIVAR` | 10 | 0.00% |
| `BLACKLISTED` | 9 | 0.00% |
| `CANDIDATUS` | 6 | 0.00% |
| `VIRUS` | 4 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,295 | 346 | 2,411 |
| GENUS | 0 | 173 | 33,776 |
| SUBSPECIES | 0 | 16 | 0 |
| FAMILY | 334 | 12 | 1,461 |

## Examples by type

**`INFORMAL`**

- `Dichogaster sp.`
- `Argilophilini sp.`
- `Buchholzia sp.`
- `Urobenus sp.`
- `Stylodrilus sp.`
- `Haementeria sp.`

**`NO_NAME`**

- `cf.`
- `cf. Gyptis`
- `cf. Amphicorina`
- `cf. Pseudoscalibregma`
- `cf. Entychides`
- `cf. Thorelliola`

**`VIRUS`**

- `Pterodrilus prion`
- `Cryptops vector`
- `Exochus virus`
- `Bolivina prion`

**`DOUBTFUL`**

- `Lamispina horstii`
- `[Leucophora]`
- `[Asilus]`
- `Culicidae P_278_FSTHT`
- `[Limnobia] fuscofemorata`
- `[Gonomyia]`

**`BLACKLISTED`**

- `Bisetocreagris que`
- `Cruzobius type`
- `Say kirgizicus`
- `Milocera ja`
- `There oldenlandiae`
- `Hypanus say`

**`PLACEHOLDER`**

- `IncertaeSedis crassicornis`
- `IncertaeSedis caprariae`
- `IncertaeSedis justiprovisorius`
- `undetermined`
- `Unplaced aberrans`
- `fossil carabid`

**`OTU`**

- `Eulaema sp. BOLD:ABY7873`
- `Euglossa sp. BOLD:AAL4038`
- `Astyanax sp. BOLD:AAA7660`
- `Odontostilbe sp. BOLD:AAE1686`
- `Jenkinsia sp. BOLD:AAA7901`
- `Harengula sp. BOLD:AAB1582`

**`CULTIVAR`**

- `Formica 'micro'`
- `Yssichromis cv.`
- `Tropheus cv.`
- `Ophthalmotilapia cv.`
- `Nannacara cv.`
- `Amphilophus cv.`

**`HYBRID`**

- `Pundamilia sp. 'red head' x Pundamilia pundamilia`
- `Etheostoma sp. x JW-2022`
- `Bryum pallescens x pohlia crudoides var revolvens`
- `Amblystegium badium x latifolium`
- `Amblystegium intermedium x vernicosum`
- `Stuckenia chakassiensis   Klinkova × S. macrocarpa  Tzvel.`

**`CANDIDATUS`**

- `Candidatus Methanoculleus`
- `Candidatus Methanovorans`
- `Candidatus Methanosphaera`
- `Candidatus Acidianus`
- `Candidatus Methanomicula`
- `Candidatus Hestiella`

