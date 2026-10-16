# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 900,268 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 885,848 | 98.40% |
| `INFORMAL` | 10,869 | 1.21% |
| `OTU` | 1,798 | 0.20% |
| `PLACEHOLDER` | 719 | 0.08% |
| `NO_NAME` | 395 | 0.04% |
| `DOUBTFUL` | 354 | 0.04% |
| `HYBRID` | 227 | 0.03% |
| `CULTIVAR` | 32 | 0.00% |
| `BLACKLISTED` | 17 | 0.00% |
| `CANDIDATUS` | 9 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 827,864 | 667 | 4,466 |
| GENUS | 0 | 308 | 63,204 |
| SUBSPECIES | 0 | 30 | 0 |
| FAMILY | 592 | 21 | 2,725 |

## Examples by type

**`INFORMAL`**

- `Limnodriloidinae sp.`
- `Euphrosinopsis sp.`
- `Protobonellia sp.`
- `Bonelliidae sp.`
- `Histriobdella sp.`
- `Lumbrinerides sp.`

**`NO_NAME`**

- `cf. Polynoe`
- `cf. Myrmecium`
- `aff. Novafrontina`
- `cf. Saitis`
- `cf. Paramicromerys`
- `cf. Lamania`

**`DOUBTFUL`**

- `Lamispina horstii`
- `[Cecidomyia] pennicornis`
- `Culicidae P_278_FSTHT`
- `[Microtendipes]`
- `[Limnobia] gracilis`
- `[Limnobia] platyptera`

**`PLACEHOLDER`**

- `slender`
- `IncertaeSedis dubius`
- `Onychiurini IncertaeSedis`
- `IncertaeSedis`
- `Anoplotermes group`
- `nr. Cavitermes`

**`BLACKLISTED`**

- `Anasillomos unidentified`
- `There latreillei`
- `There nessus`
- `Pungitius type sp.Omono`
- `Chlorostilbon illeg`
- `Tous ayamaruensis`

**`CULTIVAR`**

- `Andrena 'viciae'`
- `Aleiodes 'gland'`
- `Formica 'micro'`
- `Cichla cv.`
- `Parananochromis cv.`
- `Telmatochromis cv.`

**`OTU`**

- `Eufriesea sp. BOLD:AEF4645`
- `Euglossa sp. BOLD:AAD1076`
- `Euglossa sp. BOLD:AEM3190`
- `Nematalosa sp. BOLD:ACB7545`
- `Oligosarcus sp. BOLD:ABZ2120`
- `Salmo cf. cenerinus BOLD:AAB3872`

**`HYBRID`**

- `Bufo americanus x hemiophrys`
- `Pundamilia sp. 'nyererei-like' x Neochromis omnicaeruleus`
- `Diplostomidae gen. sp. x mag-2019`
- `Bryum pallescens x pohlia crudoides var revolvens`
- `Amblystegium badium x latifolium`
- `Amblystegium intermedium x vernicosum`

**`CANDIDATUS`**

- `Candidatus Methanocorpusculum`
- `Candidatus Methanocrinis`
- `Candidatus Nitrosomarinus`
- `Candidatus Nitrosopolaris`
- `Candidatus Acidianus`
- `Candidatus Halectosymbiota`

