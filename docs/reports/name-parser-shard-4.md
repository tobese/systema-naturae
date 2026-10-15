# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 477,047 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 469,241 | 98.36% |
| `INFORMAL` | 5,952 | 1.25% |
| `OTU` | 954 | 0.20% |
| `PLACEHOLDER` | 388 | 0.08% |
| `NO_NAME` | 188 | 0.04% |
| `DOUBTFUL` | 176 | 0.04% |
| `HYBRID` | 107 | 0.02% |
| `CULTIVAR` | 19 | 0.00% |
| `BLACKLISTED` | 11 | 0.00% |
| `CANDIDATUS` | 9 | 0.00% |
| `VIRUS` | 2 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 438,277 | 344 | 2,355 |
| GENUS | 0 | 148 | 33,903 |
| SUBSPECIES | 0 | 15 | 0 |
| FAMILY | 339 | 10 | 1,426 |

## Examples by type

**`INFORMAL`**

- `Hemienchytraeus sp.`
- `Chamaedrilus sp.`
- `Propappus sp.`
- `Odontobdella sp.`
- `Salifidae sp.`
- `Righiodrilus sp.`

**`DOUBTFUL`**

- `Stylarioides bengalensis_duplicate`
- `[Cecidomyia]`
- `[Orthocladius]`
- `[Limnobia] gracilis`
- `[Limnobia] platyptera`
- `[Polymoria]`

**`NO_NAME`**

- `cf. Livius`
- `NIcomache lumbricalis`
- `cf. Psiloderces`
- `cf. Paramicromerys`
- `cf. Aschema`
- `cf. Arachnomura`

**`VIRUS`**

- `Turkozelotes attavirus`
- `Microgoneplax prion`

**`PLACEHOLDER`**

- `IncertaeSedis`
- `IncertaeSedis fimetarioides`
- `nr. Mesosa`
- `pr. Oreda`
- `nr. Ecclisister`
- `Unplaced ephippiatus`

**`CULTIVAR`**

- `Eremochelis 'simplex'`
- `Danakilia cv.`
- `Cyprichromis cv.`
- `Paracyprichromis cv.`
- `Altolamprologus cv.`
- `Julidochromis cv.`

**`BLACKLISTED`**

- `Labiobaetis mon`
- `Casinaria xxx`
- `Catada ja`
- `There latreillei`
- `There nessus`
- `Pungitius type sp.Omono`

**`OTU`**

- `Eufriesea sp. BOLD:AEF4646`
- `Eulaema sp. BOLD:AAC6324`
- `Exaerete sp. BOLD:AAD9729`
- `Euglossa sp. BOLD:AAC3172`
- `Euglossa sp. BOLD:AEL8909`
- `Oligosarcus sp. BOLD:AAI3590`

**`HYBRID`**

- `Cichla cf. monoculus TUC-2004 x Cichla sp. 'Azul'`
- `Bufo americanus x hemiophrys`
- `Amblystegium glaucum x falcatum`
- `Hypnum lycopodioides x fluitans`
- `Galanthus elwesii × nivalis`
- `Narcissus cyclamineus × pseudonarcissus`

**`CANDIDATUS`**

- `Candidatus Nanopusillus`
- `Candidatus Methanoplasma`
- `Candidatus Methanoprimaticola`
- `Candidatus Nitrosokoinonia`
- `Candidatus Thermodiscus`
- `Candidatus Harpocratesius`

