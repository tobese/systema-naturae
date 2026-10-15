# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,173 | 98.35% |
| `INFORMAL` | 5,964 | 1.25% |
| `OTU` | 968 | 0.20% |
| `PLACEHOLDER` | 377 | 0.08% |
| `NO_NAME` | 207 | 0.04% |
| `DOUBTFUL` | 183 | 0.04% |
| `HYBRID` | 135 | 0.03% |
| `CULTIVAR` | 21 | 0.00% |
| `BLACKLISTED` | 10 | 0.00% |
| `CANDIDATUS` | 5 | 0.00% |
| `VIRUS` | 4 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,173 | 336 | 2,455 |
| GENUS | 0 | 137 | 33,975 |
| SUBSPECIES | 0 | 13 | 0 |
| FAMILY | 291 | 9 | 1,465 |

## Examples by type

**`INFORMAL`**

- `Antarctodrilus sp.`
- `Linopherus sp.`
- `Chloeia sp.`
- `Ochetostoma sp.`
- `Thalassema sp.`
- `Dinophilus sp.`

**`NO_NAME`**

- `cf. Myrmecotypus`
- `cf. Mallecolobus`
- `aff. Tenuiphantes`
- `cf. Saitis`
- `cf. Synema`
- `cf. Triaenonyx`

**`BLACKLISTED`**

- `Rhyphelia okay`
- `Anasillomos unidentified`
- `Abantis ja`
- `There clotho`
- `Dasyatis say`
- `Clarias nov`

**`PLACEHOLDER`**

- `IncertaeSedis cadaverinus`
- `IncertaeSedis trojan`
- `Unplaced`
- `nr.`
- `Cephaloleia undetermined`
- `pr.`

**`DOUBTFUL`**

- `Brancuporus gottwaldi`
- `[Haplusia] brevipalpis`
- `[Chironomus] incertus`
- `[Diaphora] pellucida`
- `Culicidae P_269_FSTHT`
- `[Limnophila] pallens`

**`VIRUS`**

- `Euragallia prion`
- `Potamophylax coronavirus`
- `Neoaemula vector`
- `"Neoaemula vector"`

**`CULTIVAR`**

- `Typhlocybini ('Eupterygini')`
- `Andrena 'viciae'`
- `Lunulites 'ligulata'`
- `Ectodus cv.`
- `Ptychochromis cv.`
- `Andinoacara cv.`

**`OTU`**

- `Euglossa sp. BOLD:AAC0545`
- `Euglossa sp. BOLD:AEL8905`
- `Cichla sp. BOLD:AAF2605`
- `Sardinella sp. BOLD:AAD1175`
- `Hyphessobrycon sp. 1 BOLD:AAA7660`
- `Haplochromis sp. BOLD:AAB6620`

**`HYBRID`**

- `Megalobrama skolokovii x Megalobrama amblycephala`
- `Oreochromis sp. ZW-2018 x Oreochromis mossambicus`
- `Clanga pomarina x clanga`
- `Hypnum molle x turgescens`
- `Mnium punctatum x subglobosum`
- `Arum italicum x Arum maculatum`

**`CANDIDATUS`**

- `Candidatus Methanofilum`
- `Candidatus Methanohalarchaeum`
- `Candidatus Methanovirga`
- `Candidatus Nitrosopumilus`
- `Candidatus Nitrososphaera`

