# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,143 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,421 | 98.39% |
| `INFORMAL` | 5,828 | 1.21% |
| `OTU` | 955 | 0.20% |
| `PLACEHOLDER` | 406 | 0.08% |
| `NO_NAME` | 202 | 0.04% |
| `DOUBTFUL` | 177 | 0.04% |
| `HYBRID` | 127 | 0.03% |
| `CULTIVAR` | 10 | 0.00% |
| `BLACKLISTED` | 9 | 0.00% |
| `CANDIDATUS` | 7 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 440,988 | 344 | 2,425 |
| GENUS | 0 | 154 | 34,154 |
| SUBSPECIES | 0 | 20 | 0 |
| FAMILY | 305 | 13 | 1,525 |

## Examples by type

**`INFORMAL`**

- `Cernosvitoviella sp.`
- `Hemienchytraeus sp.`
- `Achaeta sp.`
- `Decimodrilus sp.`
- `Periscolex sp.`
- `Lamprodrilus sp.`

**`NO_NAME`**

- `cf.`
- `cf. Gyptis`
- `cf. Petaloclymene`
- `cf. Pseudoscalibregma`
- `cf. Amphicorina`
- `cf. Myrmecotypus`

**`VIRUS`**

- `Turkozelotes attavirus`

**`CULTIVAR`**

- `Eremochelis 'simplex'`
- `Paraneetroplus cv.`
- `Yssichromis cv.`
- `Tropheus cv.`
- `Ophthalmotilapia cv.`
- `Nannacara cv.`

**`PLACEHOLDER`**

- `IncertaeSedis brahma`
- `IncertaeSedis fimetarioides`
- `nr. Quasitermes`
- `nr. Zorilispe`
- `Unplaced insignicornis`
- `Unplaced verticalis`

**`DOUBTFUL`**

- `[Chironomus]`
- `[Microtendipes] truncatus`
- `[Agromyza]`
- `Culicidae P_270_FSTHT`
- `[Limnobia] humeralis`
- `[Polymoria] tenella`

**`OTU`**

- `Eufriesea sp. BOLD:AEF4646`
- `Eulaema sp. BOLD:AAC6324`
- `Exaerete sp. BOLD:AAD7618`
- `Euglossa sp. BOLD:AAL4038`
- `Jenkinsia sp. BOLD:AAA7901`
- `Astyanax sp. BOLD:AAA7660`

**`BLACKLISTED`**

- `Dysschema on`
- `Telipna ja`
- `There pinastrina`
- `There fukienensis`
- `Anisogamus nov`
- `Haploops nov`

**`HYBRID`**

- `Ctenopharyngodon idellus x Elopichthys bambusa`
- `Pundamilia sp. 'red head' x Pundamilia pundamilia`
- `Clanga pomarina x clanga`
- `Nidirana sp. x ZTL-2020`
- `Potamogeton gramineus × lucens`
- `Sagittaria natans × sagittifolia`

**`CANDIDATUS`**

- `Candidatus Zestomicrobium`
- `Candidatus Nanobsidianus`
- `Candidatus Methanogranum`
- `Candidatus Methanomethylophilus`
- `Candidatus Nitrosoabyssus`
- `Candidatus Lokiarchaeum`

