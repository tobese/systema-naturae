# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,142 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,481 | 98.40% |
| `INFORMAL` | 5,759 | 1.20% |
| `OTU` | 964 | 0.20% |
| `PLACEHOLDER` | 380 | 0.08% |
| `NO_NAME` | 209 | 0.04% |
| `DOUBTFUL` | 175 | 0.04% |
| `HYBRID` | 142 | 0.03% |
| `CULTIVAR` | 14 | 0.00% |
| `BLACKLISTED` | 10 | 0.00% |
| `CANDIDATUS` | 5 | 0.00% |
| `VIRUS` | 3 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,015 | 357 | 2,407 |
| GENUS | 0 | 159 | 34,219 |
| SUBSPECIES | 0 | 9 | 0 |
| FAMILY | 313 | 11 | 1,453 |

## Examples by type

**`INFORMAL`**

- `Naidinae sp.`
- `Euphrosine sp.`
- `Prometor sp.`
- `Arhynchite sp.`
- `Thalassematini sp.`
- `Ophryotrocha sp.`

**`NO_NAME`**

- `NIcomache trispinata`
- `cf. Gasparia`
- `aff.`
- `cf. Pholcophora`
- `cf. Hickmanolobus`
- `cf. Maeota`

**`BLACKLISTED`**

- `Bisetocreagris que`
- `Cruzobius type`
- `Say kirgizicus`
- `There suffusa`
- `Teretamon mon`
- `Pungitius type sp.Freshwater`

**`PLACEHOLDER`**

- `uncultured Allonothrus`
- `IncertaeSedis certus`
- `nr.`
- `fossil`
- `nr. Mesosa`
- `nr. Gloeosoma`

**`DOUBTFUL`**

- `[Cecidomyia]`
- `Culicidae Ae_JM910`
- `[Chlorops]`
- `[Dasymorellia]`
- `[Limnobia] decasbila`
- `[Limnobia] marginepunctata`

**`OTU`**

- `Eufriesea sp. BOLD:AAY3127`
- `Euglossa sp. BOLD:AAC3172`
- `Euglossa sp. BOLD:AEL8909`
- `Oligosarcus sp. BOLD:AAI3590`
- `Icelus sp. BOLD:AAB1023`
- `Hippocampus cf. barbouri BOLD:AAF0603`

**`VIRUS`**

- `Dasyproctus cevirus`
- `Microgoneplax prion`
- `Bolivina prion`

**`CULTIVAR`**

- `Danakilia cv.`
- `Cyprichromis cv.`
- `Paracyprichromis cv.`
- `Altolamprologus cv.`
- `Julidochromis cv.`
- `Hemitaeniochromis cv.`

**`HYBRID`**

- `Cichla cf. monoculus TUC-2004 x Cichla sp. 'Azul'`
- `Bufo americanus x fowleri`
- `Bryum inclinatum x caespiticium`
- `Hypnum lycopodioides x revolvens`
- `Thaumatophyllum bipinnatifidum x undulatum`
- `Stuckenia pectinata × vaginata`

**`CANDIDATUS`**

- `Candidatus Nitrososphaera`
- `Candidatus Methanovirga`
- `Candidatus Nitrosopumilus`
- `Candidatus Methanofilum`
- `Candidatus Methanohalarchaeum`

