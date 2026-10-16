# GBIF name parser over every name in the tree

`POST /v1/parser/name`, 480,142 distinct (name, rank) pairs. The repeated-`name` GET is unusable (see the script docstring); the POST form was asserted positionally safe on every batch.

## Parser `type`

The validity signal. `parsed: true` does not mean valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and `genusOrAbove: "?"`.

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 472,176 | 98.34% |
| `INFORMAL` | 6,054 | 1.26% |
| `OTU` | 956 | 0.20% |
| `PLACEHOLDER` | 392 | 0.08% |
| `NO_NAME` | 205 | 0.04% |
| `DOUBTFUL` | 186 | 0.04% |
| `HYBRID` | 131 | 0.03% |
| `CULTIVAR` | 23 | 0.00% |
| `BLACKLISTED` | 9 | 0.00% |
| `CANDIDATUS` | 6 | 0.00% |
| `VIRUS` | 4 | 0.00% |

## rankMarker vs our rank

Only comparable where the parser has vocabulary for our rank. Note the
marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,
and is often simply absent -- which is not a disagreement.

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 441,376 | 358 | 2,400 |
| GENUS | 0 | 175 | 33,895 |
| SUBSPECIES | 0 | 10 | 0 |
| FAMILY | 298 | 9 | 1,400 |

## Examples by type

**`INFORMAL`**

- `Marionina sp.`
- `Buchholzia sp.`
- `Urobenus sp.`
- `Styloscolex sp.`
- `Guestphalinus sp.`
- `Myzobdella sp.`

**`VIRUS`**

- `Pterodrilus prion`
- `Tidabius vector`
- `Cryptops vector`
- `Psenulus trevirus`

**`NO_NAME`**

- `cf. Leitoscoloplos`
- `cf. Levinsenia`
- `cf. Prethopalpus`
- `cf. Arandisa`
- `cf. Cyllodania`
- `cf. Maenola`

**`PLACEHOLDER`**

- `IncertaeSedis membranea`
- `IncertaeSedis michelbacheri`
- `IncertaeSedis pancici`
- `Unplaced fulvum`
- `undetermined Kalotermes`
- `pr. Miocalles`

**`BLACKLISTED`**

- `As alae`
- `There pallicosta`
- `Limnoporeia inﬁrmichelata`
- `Clarias nov`
- `unidentified non-geniculate`
- `Angraecum nov`

**`DOUBTFUL`**

- `[Leucophora] grisea`
- `[Chironomus] virens`
- `[Limnophila] cineracea`
- `[Limnobia] nigricans`
- `[Alfredia] acrobata`
- `[Orosmya] apennina`

**`CULTIVAR`**

- `Typhlocybini ('Zyginellini')`
- `Tetragonopterus cv.`
- `Sarotherodon cv.`
- `Steatocranus cv.`
- `Benthochromis cv.`
- `Mbipia cv.`

**`OTU`**

- `Euglossa sp. BOLD:AAC0545`
- `Euglossa sp. BOLD:AEL8905`
- `Cichla sp. BOLD:AAF2605`
- `Sardinella sp. BOLD:AAB7268`
- `Hyphessobrycon sp. 1 BOLD:AAA7660`
- `Haplochromis sp. BOLD:AAB6620`

**`HYBRID`**

- `Oreochromis sp. ZW-2018 x Oreochromis mossambicus`
- `(Pungitius sinensis x Pungitius pungitius) x Pungitius pungitius`
- `Quistrachia sp. X MSJ2014`
- `Brachythecium reflexum x populeum`
- `Hypnum cordifolium x richardsonii`
- `Potamogeton acutifolius × berchtoldii`

**`CANDIDATUS`**

- `Candidatus Methanoculleus`
- `Candidatus Methanovorans`
- `Candidatus Hestiella`
- `Candidatus Acidianus`
- `Candidatus Methanosphaera`
- `Candidatus Methanomicula`

