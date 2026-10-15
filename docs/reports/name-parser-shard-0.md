# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,271 | 98.37% |
| `INFORMAL` | 5,882 | 1.23% |
| `OTU` | 962 | 0.20% |
| `PLACEHOLDER` | 366 | 0.08% |
| `NO_NAME` | 216 | 0.05% |
| `DOUBTFUL` | 193 | 0.04% |
| `HYBRID` | 137 | 0.03% |
| `BLACKLISTED` | 8 | 0.00% |
| `CULTIVAR` | 8 | 0.00% |
| `CANDIDATUS` | 3 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,188 | 336 | 2,398 |
| GENUS | 0 | 159 | 33,932 |
| SUBSPECIES | 0 | 10 | 0 |
| FAMILY | 322 | 9 | 1,462 |

## Examples by type

**`INFORMAL`**

- `Cernosvitoviella sp.`
- `Mesenchytraeus sp.`
- `Henlea sp.`
- `Grania sp.`
- `Delaya sp.`
- `Trichodrilus sp.`

**`NO_NAME`**

- `cf. Protobonellia`
- `cf. Myrmecium`
- `aff. Novafrontina`
- `cf. Prethopalpus`
- `cf. Orthobula`
- `cf. Maeota`

**`PLACEHOLDER`**

- `uncultured Riftia`
- `IncertaeSedis membranea`
- `IncertaeSedis sensitivus`
- `IncertaeSedis ravanicae`
- `Subulitermes group`
- `Unplaced australicus`

**`DOUBTFUL`**

- `Brancuporus pennifoldae`
- `[Haplusia]`
- `[Chironomus]`
- `[Microtendipes] truncatus`
- `Culicidae P_321_FSTCO`
- `[Agromyza] flava`

**`BLACKLISTED`**

- `Stenus mon`
- `There pallicosta`
- `Petrochromis nov`
- `Chlorostilbon illeg`
- `Fanellia new`
- `Triboniophorus nov`

**`OTU`**

- `Euglossa sp. BOLD:AEL8904`
- `Oreochromis sp. BOLD:AAA8512`
- `Hemichromis sp. BOLD:AAI6807`
- `Laetacara sp. BOLD:AAO5884`
- `Jenkinsia sp. BOLD:AAM5101`
- `Sardinella sp. BOLD:AAB7268`

**`VIRUS`**

- `Psenulus trevirus`

**`CULTIVAR`**

- `Lunulites 'spiralis'`
- `Cyphotilapia cv.`
- `Pyxichromis cv.`
- `Pharyngochromis cv.`
- `Pundamilia cv.`
- `Xenotilapia cv.`

**`HYBRID`**

- `Pundamilia sp. pundamilia-like x Pundamilia sp. nyererei-like`
- `(Pungitius sinensis x Pungitius pungitius) x Pungitius pungitius`
- `Haemonchus contortus x Haemonchus placei`
- `Stuckenia pectinata × vaginata`
- `Potamogeton coloratus × gramineus`
- `Potamogeton friesii × obtusifolius`

**`CANDIDATUS`**

- `Candidatus Methanorudis`
- `Candidatus Nitrosarchaeum`
- `Candidatus Nitrosocosmicus`

