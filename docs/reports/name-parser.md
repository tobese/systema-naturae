# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 3,939,066 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 3,878,132 | 98.45% |
| `INFORMAL` | 44,740 | 1.14% |
| `OTU` | 7,731 | 0.20% |
| `PLACEHOLDER` | 3,973 | 0.10% |
| `NO_NAME` | 2,028 | 0.05% |
| `DOUBTFUL` | 1,236 | 0.03% |
| `HYBRID` | 995 | 0.03% |
| `CULTIVAR` | 91 | 0.00% |
| `BLACKLISTED` | 80 | 0.00% |
| `CANDIDATUS` | 44 | 0.00% |
| `VIRUS` | 16 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 3,580,461 | 2,607 | 19,122 |
| GENUS | 0 | 1,321 | 318,905 |
| SUBSPECIES | 0 | 115 | 0 |
| FAMILY | 2,520 | 92 | 12,208 |

## Examples by type

**`INFORMAL`**

- `Microthyriaceae sp.`
- `Paramirandina sp.`
- `Pseudocorniculariella sp.`
- `Scolecopeltidium sp.`
- `Tumidispora sp.`
- `Asparagobius sp.`

**`PLACEHOLDER`**

- `Mesovelia indeterminate`
- `uncultured`
- `uncultured Amphiporthe`
- `uncultured Cryptodiaporthe`
- `uncultured Cytospora`
- `uncultured Endothiella`

**`OTU`**

- `UBA12382`
- `UBA12382`
- `UBA12382 sp002503845`
- `UBA12382 sp009889625`
- `UBA12382 sp009889685`
- `CAZAFX01`

**`NO_NAME`**

- `ANME1a`
- `ANME1a sp003194425`
- `Methanoculleus_A frigidifontis`
- `Methanoculleus_A taiwanensis`
- `cf.`
- `cf. Ototyphlonemertes`

**`DOUBTFUL`**

- `Methanoculleus chikugoensis_A`
- `Methanoculleus marisnigri_B`
- `[Dipteracanthus]`
- `[Dipteracanthus] australasicus`
- `[Acontia]`
- `[Acontia] semiatra`

**`HYBRID`**

- `Aphelandra gracilis leonard x sinclairiana`
- `Populus alba x tremula`
- `Populus deltoides var. monilifera × Populus tremuloides`
- `Populus laurifolia x nigra var. italica`
- `Populus maximowiczii x trichocarpa`
- `Salix aegyptiaca × caprea subsp. caprea`

**`BLACKLISTED`**

- `Avicennia catalog`
- `Xylosma new`
- `Stipa ladakhensis M. Nobis, Klichowska, A. Nowak & P. D. Gudkova, nothosp. nov.`
- `Miconia nov`
- `unidentified`
- `unidentified archaeon`

**`CULTIVAR`**

- `Salix 'Brekkavier'`
- `Andrena 'viciae'`
- `Pomacentrus sp.'minami-iso-suzumedai'`
- `Gypsophila ´Rosenschleier´`
- `Amanita sp.'chiricahuana'`
- `Echinopsis ×wilkensii  hort.`

**`CANDIDATUS`**

- `Candidatus Methanoculleus`
- `Candidatus Calypsonella`
- `Candidatus Hestiella`
- `Candidatus Tiamatella`
- `Candidatus Acidianus`
- `Candidatus Aramenus`

**`VIRUS`**

- `Bolivina prion`
- `"Neoaemula vector"`
- `Neoaemula vector`
- `Cryptops vector`
- `Turkozelotes attavirus`
- `Tidabius vector`

