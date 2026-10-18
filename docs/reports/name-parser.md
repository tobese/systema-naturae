# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 4,181,311 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 4,118,712 | 98.50% |
| `INFORMAL` | 46,216 | 1.11% |
| `OTU` | 7,659 | 0.18% |
| `PLACEHOLDER` | 3,092 | 0.07% |
| `HYBRID` | 2,480 | 0.06% |
| `NO_NAME` | 1,683 | 0.04% |
| `DOUBTFUL` | 1,223 | 0.03% |
| `CULTIVAR` | 107 | 0.00% |
| `BLACKLISTED` | 77 | 0.00% |
| `CANDIDATUS` | 44 | 0.00% |
| `VIRUS` | 18 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 3,851,175 | 2,657 | 20,585 |
| GENUS | 0 | 1,260 | 281,530 |
| SUBSPECIES | 372 | 6,914 | 1 |
| FAMILY | 2,520 | 92 | 12,105 |

## Examples by type

**`INFORMAL`**

- `Ulothrix spec`
- `Ulva spec`
- `Ulvella spec`
- `Desmodesmus spec`
- `Planktococcomyxa spec`
- `Ankistrodesmus spec`

**`NO_NAME`**

- `×`
- `× ×Cyclobotrya`
- `× ×Alpingera`
- `× ×Cattlianthe`
- `× ×Neotinarhiza`
- `× ×Neotinacamptis`

**`HYBRID`**

- `Colchicum cilicicum × speciosum`
- `Colchicum autumnale × speciosum`
- `Colchicum alpinum x Colchicum autumnale`
- `Gagea lutea x Gagea pratensis`
- `Gagea lutea × pratensis`
- `Anacamptis x Dactylorhiza`

**`BLACKLISTED`**

- `Stipa ladakhensis M. Nobis, Klichowska, A. Nowak & P. D. Gudkova, nothosp. nov.`
- `Caryota no`
- `Hypanus say`
- `Pungitius type sp.Omono`
- `Pungitius type sp.Freshwater`
- `Pungitius type sp.Brackish`

**`CULTIVAR`**

- `Echinopsis ×wilkensii  hort.`
- `Perca cv.`
- `Etheostoma cv.`
- `Paretroplus cv.`
- `Paratilapia cv.`
- `Cichla cv.`

**`VIRUS`**

- `Neoaemula vector Mackinnon, Hiller, Long & Marshall, 2008`
- `Neoaemula vector`
- `Microgoneplax prion`
- `Euragallia prion`
- `Ophion virus`
- `Exochus virus`

**`OTU`**

- `Choerodon cf. gymnogenys BOLD:AAJ0249`
- `Scarus sp. BOLD:AAE9514`
- `Scarus sp. BOLD:AAD0897`
- `Scarus sp. BOLD:AAA8751`
- `Sparisoma sp. BOLD:AAC8879`
- `Sparisoma sp. BOLD:AAC0186`

**`PLACEHOLDER`**

- `Balaenoptera acutorostrata unnamed`
- `Actinocyclus polyradiatus Tempère & Peragallo, 1912`
- `Actinocyclus calix Tempère & Brun, 1889`
- `Ser sasekumari`
- `Ser amoyensis`
- `Ser mikawaensis`

**`DOUBTFUL`**

- `Eudonia viettei_homonym`
- `Thaumato­grapha`
- `Thaumato­grapha tamdaoana`
- `Thaumato­grapha melinhana`
- `Thaumato­grapha cucphuongana`
- `Thaumato­grapha carapaceana`

**`CANDIDATUS`**

- `Candidatus Lokiarchaeum`
- `Candidatus Harpocratesius`
- `Candidatus Methanoglobus`
- `Candidatus Halobonum`
- `Candidatus Halectosymbiota`
- `Candidatus Methanocorpusculum`

