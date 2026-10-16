# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,142 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,293 | 98.37% |
| `INFORMAL` | 5,953 | 1.24% |
| `OTU` | 955 | 0.20% |
| `PLACEHOLDER` | 383 | 0.08% |
| `NO_NAME` | 214 | 0.04% |
| `DOUBTFUL` | 194 | 0.04% |
| `HYBRID` | 123 | 0.03% |
| `CULTIVAR` | 14 | 0.00% |
| `BLACKLISTED` | 9 | 0.00% |
| `CANDIDATUS` | 3 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,232 | 324 | 2,420 |
| GENUS | 0 | 152 | 34,003 |
| SUBSPECIES | 0 | 13 | 0 |
| FAMILY | 315 | 11 | 1,471 |

## Examples by type

**`INFORMAL`**

- `Neoprosthenorchis sp.`
- `Gorgorhynchoides sp.`
- `Polymorphus sp.`
- `Chtonobdella sp.`
- `Haemadipsa sp.`
- `Drilocrius sp.`

**`DOUBTFUL`**

- `Stylarioides bengalensis_duplicate`
- `Brancuporus gottwaldi`
- `[Orthocladius] turficola`
- `[Diaphora] pellucida`
- `[Limnobia]`
- `[Limnobia] ignobilis`

**`NO_NAME`**

- `NIcomache lumbricalis`
- `cf. Entychides`
- `cf. Afrilobus`
- `cf. Synema`
- `cf. Capheris`
- `cf. Coryphasia`

**`BLACKLISTED`**

- `Speocera none`
- `say`
- `There alecto`
- `Sturnidoecus mon`
- `Pungitius type sp.Brackish`
- `Dasyatis say`

**`PLACEHOLDER`**

- `IncertaeSedis cadaverinus`
- `IncertaeSedis trojan`
- `Willowsiinae IncertaeSedis`
- `Subulitermes group`
- `pr. Perissops`
- `nr. Ancylocnemis`

**`OTU`**

- `Euglossa sp. BOLD:AAC1673`
- `Euglossa sp. BOLD:AEL8907`
- `Epipyropidae BOLD:AAY7260`
- `Alosa sp. BOLD:ACF3178`
- `Sardinella sp. BOLD:AAO1626`
- `Halichoeres sp. BOLD:AAY1850`

**`VIRUS`**

- `Ophion virus`

**`CULTIVAR`**

- `Paretroplus cv.`
- `Nanochromis cv.`
- `Hemichromis cv.`
- `Rubricatochromis cv.`
- `Lepidiolamprologus cv.`
- `Lamprologus cv.`

**`HYBRID`**

- `Alopia straminicollis straminicollis x Alopia livida`
- `Haemonchus contortus x Haemonchus placei`
- `Amblystegium glaucum x falcatum`
- `Hypnum lycopodioides x fluitans`
- `Weissia crispata x astomum crispum`
- `Stuckenia filiformis × pectinata`

**`CANDIDATUS`**

- `Candidatus Nitrosocosmicus`
- `Candidatus Methanorudis`
- `Candidatus Nitrosarchaeum`

