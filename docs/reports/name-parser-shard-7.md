# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,046 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,267 | 98.37% |
| `INFORMAL` | 5,876 | 1.23% |
| `OTU` | 950 | 0.20% |
| `PLACEHOLDER` | 388 | 0.08% |
| `NO_NAME` | 219 | 0.05% |
| `DOUBTFUL` | 198 | 0.04% |
| `HYBRID` | 122 | 0.03% |
| `CULTIVAR` | 16 | 0.00% |
| `BLACKLISTED` | 6 | 0.00% |
| `CANDIDATUS` | 3 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,124 | 330 | 2,339 |
| GENUS | 0 | 156 | 34,120 |
| SUBSPECIES | 0 | 13 | 0 |
| FAMILY | 303 | 13 | 1,445 |

## Examples by type

**`INFORMAL`**

- `Phreodrilidae sp.`
- `Paramphinome sp.`
- `Hermodice sp.`
- `Bonellia sp.`
- `Dimorphilus sp.`
- `Diurodrilus sp.`

**`NO_NAME`**

- `cf. Hamingia`
- `cf. Petaloclymene`
- `cf. Oweniidae`
- `aff.`
- `cf. Trilacuna`
- `cf. Coryphasia`

**`PLACEHOLDER`**

- `uncultured`
- `uncultured Allonothrus`
- `IncertaeSedis intermedia`
- `IncertaeSedis michelbacheri`
- `IncertaeSedis pancici`
- `undetermined Kalotermes`

**`DOUBTFUL`**

- `[Leucophora] grisea`
- `[Microtendipes]`
- `[Agromyza]`
- `[Asilus] punctatus`
- `Culicidae P_270_FSTHT`
- `[Dasyphora]`

**`OTU`**

- `Euglossa sp. BOLD:ABY5852`
- `Astyanax sp. BOLD:AAB3435`
- `Hasemania sp. BOLD:AAO6055`
- `Odontostilbe sp. BOLD:AAO5650`
- `Oreochromis sp. BOLD:AAA6537`
- `Gasterosteus sp. BOLD:AAA8488`

**`VIRUS`**

- `Ophion virus`

**`BLACKLISTED`**

- `Telipna ja`
- `There japonica`
- `Sturnidoecus mon`
- `Aequidens nov`
- `unidentified protist`
- `unidentified archaeon`

**`CULTIVAR`**

- `Coptodon cv.`
- `Oreochromis cv.`
- `Congochromis cv.`
- `Chalinochromis cv.`
- `Thoracochromis cv.`
- `Lethrinops cv.`

**`HYBRID`**

- `Pundamilia sp. nyererei-like x Pundamilia sp. pundamilia-like`
- `Stuckenia filiformis × pectinata`
- `Potamogeton lucens × natans`
- `Potamogeton perfoliatus × praelongus`
- `Attalea eichleri x speciosa`
- `Orchis anthropophora x militaris`

**`CANDIDATUS`**

- `Candidatus Methanoflexus`
- `Candidatus Aramenus`
- `Candidatus Calypsonella`

