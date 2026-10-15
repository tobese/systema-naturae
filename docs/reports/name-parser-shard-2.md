# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,304 | 98.38% |
| `INFORMAL` | 5,855 | 1.23% |
| `OTU` | 964 | 0.20% |
| `PLACEHOLDER` | 380 | 0.08% |
| `NO_NAME` | 211 | 0.04% |
| `DOUBTFUL` | 182 | 0.04% |
| `HYBRID` | 131 | 0.03% |
| `BLACKLISTED` | 10 | 0.00% |
| `CULTIVAR` | 5 | 0.00% |
| `CANDIDATUS` | 4 | 0.00% |
| `VIRUS` | 1 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,291 | 357 | 2,382 |
| GENUS | 0 | 153 | 33,859 |
| SUBSPECIES | 0 | 14 | 0 |
| FAMILY | 320 | 12 | 1,460 |

## Examples by type

**`INFORMAL`**

- `Dendrobaena sp.`
- `Pithemera sp.`
- `Toutellus sp.`
- `Microchaetid sp.`
- `Astacopsidrilus sp.`
- `Acanthobonellia sp.`

**`NO_NAME`**

- `cf. Leitoscoloplos`
- `cf. Levinsenia`
- `cf. Neaetha`
- `cf. Rogmocrypta`
- `cf. Arandisa`
- `cf. Afrilobus`

**`BLACKLISTED`**

- `Koppe no`
- `As alae`
- `Dysschema on`
- `There alecto`
- `Anisogamus nov`
- `Limnoporeia inﬁrmichelata`

**`PLACEHOLDER`**

- `Willowsiinae IncertaeSedis`
- `IncertaeSedis certus`
- `Unplaced fulvum`
- `Anoplotermes group`
- `nr. Cavitermes`
- `pr. Eubulus`

**`DOUBTFUL`**

- `[Chironomus] niger`
- `[Limnobia]`
- `[Limnobia] ignobilis`
- `[Curtonevra] (Trichomorellia)`
- `[Cordiluroides] cornicerca`
- `[Psychoda]`

**`CULTIVAR`**

- `Typhlocybini ('Zyginellini')`
- `Neolamprologus cv.`
- `Astatotilapia cv.`
- `Coregonus cv.`
- `Guianacara cv.`

**`OTU`**

- `Eufriesea sp. BOLD:AAY3127`
- `Euglossa sp. BOLD:AAC0547`
- `Euglossa sp. BOLD:AEL8906`
- `Epipyropidae BOLD:AAY7260`
- `Hemigrammus cf. gracilis BOLD:AAY2122`
- `Hyphessobrycon sp. 2 BOLD:AAD0588`

**`VIRUS`**

- `Dasyproctus cevirus`

**`HYBRID`**

- `Brachythecium reflexum x populeum`
- `Hypnum cordifolium x richardsonii`
- `Sagittaria natans × sagittifolia`
- `Potamogeton gramineus × lucens`
- `Scilla bifolia × sardensis`
- `Scilla luciliae x siehei`

**`CANDIDATUS`**

- `Candidatus Nitrosomarinus`
- `Candidatus Nitrosopolaris`
- `Candidatus Methanocorpusculum`
- `Candidatus Methanocrinis`

