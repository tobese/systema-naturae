# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,143 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,196 | 98.34% |
| `INFORMAL` | 6,061 | 1.26% |
| `OTU` | 964 | 0.20% |
| `PLACEHOLDER` | 378 | 0.08% |
| `NO_NAME` | 214 | 0.04% |
| `DOUBTFUL` | 183 | 0.04% |
| `HYBRID` | 113 | 0.02% |
| `BLACKLISTED` | 14 | 0.00% |
| `CULTIVAR` | 9 | 0.00% |
| `CANDIDATUS` | 7 | 0.00% |
| `VIRUS` | 4 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,161 | 340 | 2,401 |
| GENUS | 0 | 171 | 34,058 |
| SUBSPECIES | 0 | 12 | 0 |
| FAMILY | 336 | 10 | 1,422 |

## Examples by type

**`INFORMAL`**

- `Prosthenorchis spec  Diesing`
- `Floridosentis sp.`
- `Dollfusentis sp.`
- `Longicollum sp.`
- `Gorgorhynchus sp.`
- `Andracantha sp.`

**`NO_NAME`**

- `cf. Protobonellia`
- `cf. Trilacuna`
- `cf. Arachnomura`
- `cf. Hypaeus`
- `cf. Misumena`
- `cf. Ceratomontia`

**`PLACEHOLDER`**

- `uncultured Riftia`
- `IncertaeSedis intermedia`
- `IncertaeSedis caprariae`
- `IncertaeSedis justiprovisorius`
- `Unplaced`
- `undetermined`

**`OTU`**

- `Linyphiidae BOLD:AAE6136`
- `Eulaema sp. BOLD:ABY7873`
- `Euglossa sp. BOLD:AEL8904`
- `Oreochromis sp. BOLD:AAA8512`
- `Hemichromis sp. BOLD:AAI6807`
- `Laetacara sp. BOLD:AAO5884`

**`BLACKLISTED`**

- `Rhyphelia okay`
- `Labiobaetis mon`
- `Catada ja`
- `Are druryi`
- `Milocera ja`
- `Stoermeriana das`

**`DOUBTFUL`**

- `Ischnoptera rufa_rufa`
- `[Leucophora]`
- `[Haplusia] brevipalpis`
- `[Chironomus] niger`
- `Culicidae P_269_FSTHT`
- `[Asilus] punctatus`

**`CULTIVAR`**

- `Typhlocybini ('Eupterygini')`
- `Lunulites 'ligulata'`
- `Cyphotilapia cv.`
- `Pyxichromis cv.`
- `Pharyngochromis cv.`
- `Pundamilia cv.`

**`HYBRID`**

- `Ectatomma sp. Neotropics x Ectatomma sp. Oaxaca 1`
- `Pundamilia sp. pundamilia-like x Pundamilia sp. nyererei-like`
- `Mnium punctatum x subglobosum`
- `Hypnum molle x turgescens`
- `Arum cylindraceum × maculatum`
- `Triglochin gaspensis × Triglochin maritima`

**`VIRUS`**

- `Exochus virus`
- `Potamophylax coronavirus`
- `Neoaemula vector`
- `"Neoaemula vector"`

**`CANDIDATUS`**

- `Candidatus Methanobinarius`
- `Candidatus Methanomassiliicoccus`
- `Candidatus Methanomethylophilaceae`
- `Candidatus Nitrosomaritimum`
- `Candidatus Tiamatella`
- `Candidatus Halectosymbiota`

