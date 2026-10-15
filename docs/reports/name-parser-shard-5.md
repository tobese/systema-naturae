# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,198 | 98.35% |
| `INFORMAL` | 5,968 | 1.25% |
| `OTU` | 956 | 0.20% |
| `PLACEHOLDER` | 391 | 0.08% |
| `NO_NAME` | 209 | 0.04% |
| `DOUBTFUL` | 174 | 0.04% |
| `HYBRID` | 118 | 0.02% |
| `CULTIVAR` | 14 | 0.00% |
| `BLACKLISTED` | 12 | 0.00% |
| `CANDIDATUS` | 7 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,300 | 349 | 2,408 |
| GENUS | 0 | 170 | 33,834 |
| SUBSPECIES | 0 | 15 | 0 |
| FAMILY | 295 | 16 | 1,444 |

## Examples by type

**`INFORMAL`**

- `Octolasium sp.`
- `Lumbricid sp.`
- `Lutodrilus sp.`
- `Euphrosinopsis sp.`
- `Protobonellia sp.`
- `Bonelliidae sp.`

**`PLACEHOLDER`**

- `slender`
- `IncertaeSedis brahma`
- `IncertaeSedis justi`
- `Thalassaphorurini IncertaeSedis`
- `Termes group`
- `undetermined Microcerotermes`

**`NO_NAME`**

- `NIcomache trispinata`
- `cf. Polynoe`
- `cf. Gasparia`
- `cf. Tricongius`
- `cf. Cyllodania`
- `cf. Maenola`

**`BLACKLISTED`**

- `Speocera none`
- `say`
- `Are druryi`
- `Stoermeriana das`
- `There pinastrina`
- `There fukienensis`

**`DOUBTFUL`**

- `Ischnoptera rufa_rufa`
- `[Cecidomyia] pennicornis`
- `[Orthocladius] turficola`
- `Culicidae Ae_JM910`
- `[Limnobia] humeralis`
- `[Polymoria] tenella`

**`OTU`**

- `Eufriesea sp. BOLD:AEM5056`
- `Eulaema sp. BOLD:AAM5237`
- `Euglossa sp. BOLD:AAD1076`
- `Euglossa sp. BOLD:AEM3190`
- `Oligosarcus sp. BOLD:ABZ2120`
- `Nematalosa sp. BOLD:ACB7545`

**`CULTIVAR`**

- `Aleiodes 'gland'`
- `Parananochromis cv.`
- `Telmatochromis cv.`
- `Orthochromis cv.`
- `Haplochromis cv.`
- `Protomelas cv.`

**`HYBRID`**

- `Pundamilia sp. 'nyererei-like' x Neochromis omnicaeruleus`
- `Ctenopharyngodon idellus x Elopichthys bambusa`
- `Quistrachia sp. X MSJ2014`
- `Alopia straminicollis straminicollis x Alopia livida`
- `Bryum inclinatum x caespiticium`
- `Hypnum lycopodioides x revolvens`

**`CANDIDATUS`**

- `Candidatus Methanomassiliicoccus`
- `Candidatus Methanomethylophilaceae`
- `Candidatus Nitrosomaritimum`
- `Candidatus Tiamatella`
- `Candidatus Halectosymbiota`
- `Candidatus Methanimicrococcus`

