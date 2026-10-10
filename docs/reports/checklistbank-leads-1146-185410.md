# Carabcat (1146) and the Geometridae facility (185410) — full measurement

Companion to the `checklistbank-1146` / `checklistbank-185410` entries in
`scripts/sourcesManifest.py` and the "Evaluated, 2026-10-10" section of
`docs/dataset-inbox.md`. Both declined; this is the detailed data behind the
summary, including the full "new species" lists neither of those documents
carries in full. Raw data: [`checklistbank-1146-185410-overlap.json`](checklistbank-1146-185410-overlap.json).

## Method

No downloadable export exists for either dataset (`export.zip?format=ColDP`
404s on both; the POST that would generate one needs credentials this
project does not have). Measured via `scripts/apiOverlapReport.py`'s
`page_all`, called unsharded (`shard=False`) since both totals are well
under the API's 100k offset cap — sharding on `q` is exactly what
2026-10-09's triage (`dataset-inbox.md`) proved unreliable without checking
against the unfiltered total. Names are then run through
`archiveOverlap.strip_authorship` and `taxamatch.parse_names` /
`bare_name`, the same normalisation `archiveOverlap.py` applies, before
checking held status against `taxaserve`.

## Summary

| | Carabcat (1146) | Geometridae facility (185410) |
|---|---|---|
| gap family | Carabidae (#3, 31,316 missing) | Geometridae (#5, 24,459 missing) |
| licence | cc by | cc by |
| vintage | 2021-08-20 (v.03, 08/2021) | 2024-06-06 (v1.1.24.158, 6 Jun 2024) |
| API accepted species | 40,934 | 23,793 |
| distinct normalised forms | 40,927 | 23,742 |
| already held | 40,886 (99.9%) | 23,613 (99.5%) |
| **new** | **41** | **129** |
| families offered | Carabidae, Trachypachidae | Geometridae, Pseudobistonidae |

Both families are already 100% held at the family level — this is a
species-level top-up at best, not a structural gain.

## The 41 new Carabcat species

Acupalpus interstitialis, Agonum lutulentum, Agonum simile, Amara blanchardi, Amara discors, Amara gibba, Amara idahoana, Amara strenua, Apristus constrictus, Bembidion tenellum, Calathus aztec, Cephalota hispanica, Chlaenius glaucus, Cicindela rufiventris, Cylindera mutata, Cymindis macularis, Demetrida forma, Goniotropis olivieri, Harpalus animosus, Harpalus faunus, Harpalus fraternus, Harpalus neglectus, Harpalus servus, Lebia ornata, Lebia viridipennis, Oodes fluvialis, Oodes gracilis, Pasimachus obsoletus, Pentagonica picticornis, Platynus cincticollis, Poecilus corvus, Pterostichus amethystinus, Pterostichus castaneus, Pterostichus crenicollis, Pterostichus ecarinatus, Pterostichus empetricola, Pterostichus gracilis, Pterostichus nivalis, Syntomus truncatellus, v sinister, v vanemdeni.

**Two likely parsing artifacts, not species**: `v sinister` and `v
vanemdeni` are almost certainly a subgenus-hyphenated epithet (something
like `Pterostichus (X) v-sinister`) that `strip_authorship`'s parenthetical
removal plus GNparser's split mangled into a bogus one-letter "genus" --
the same failure shape the hybrid-epithet bug in `import.md §10` describes
for a different symbol. Not investigated further since the count (2 of 41)
doesn't change the decline verdict either way; flagged so nobody imports
"v" as a genus.

## The 129 new Geometridae species

Abraxas fasciaria, Abraxas punctifera, Adeixis griseata, Alcis songarica, Amblychia sommereri, Anachloris uncinata, Anavinemina rindgei, Aplocera columbata, Astygisa vexillaria, Astygisa waterstradti, Authaemon poliophara, Biston exalbescens, Capusa cuculloides, Chlenias macrochorda, Chlenomorpha lygdina, Chrysolarentia aprepta, Chrysolarentia interruptata, Chrysolarentia plagiocausta, Chrysolarentia poliophasma, Chrysolarentia tristis, Ciampa melanostrepta, Craspedosis cyanea, Cyclophora silas, Diplurodes semicircularis, Diplurodes triangulata, Docirava pudicata, Drepanogynis bifasciata, Drepanogynis robertsoni, Drepanogynis soni, Dysrhoe rhiogyra, Dysstroma latefasciata, Dysstroma mancipata, Ectropidia harmani, Ectropis argalea, Ectropis despicata, Ectropis tricolor, Eois heliadaria, Eucyclodes leptocosma, Eumilionia mediofasciata, Euphronarcha epiphloea, Euphyia combustaria, Euphyia emberizata, Euphyia fringillata, Euphyia jugurtharia, Eupithecia assectata, Eupithecia denotata, Eupithecia soricella, Eupithecia szelenyica, Eusarca strigularia, Furcatrox paracus, Harpagocnema eremoplana, Hypomecis danieli, Hypomecis momaria, Idaea contractalis, Ischnopteris miseliata, Leucula ablinearia, Leucula simplicaria, Leucula tiresiaria, Macaria signaria, Menophra humeraria, Menophra translineata, Mictodoca callipolia, Myrteta angelica, Nadagara juventinaria, Narraga georgiana, Nephodia favaria, Nephodia pieridaria, Nepytia canosaria, Nothylemera neaera, Nycterephes anthracica, Oenoptila violacearia, Omphalucha prosciodes, Opisthoxia formosante, Orthocabera sericea, Orthocabera tinagmaria, Ourapteryx persica, Ourapteryx podaliriata, Ourapteryx sciticaudaria, Oxydia agliata, Oxydia apidania, Oxydia hispata, Oxydia nimbata, Oxydia peosinata, Oxydia platypterata, Paraboarmia viertlii, Paradarisa consonaria, Paragonia cruraria, Paralaea beggaria, Paralaea ochrosoma, Paralaea porphyrinaria, Paralaea taggorum, Parapercnia giraffata, Peratophyga hyalinata, Peribatodes ilicaria, Peribatodes umbraria, Pero corosha, Pero lustraria, Pero ogmopoea, Pero rapinaria, Pero stolidata, Pero stuposaria, Plutodes unidentata, Poecilasthena iopolia, Poecilasthena oceanias, Poecilasthena panapala, Poecilasthena subpurpureata, Polystroma adumbrata, Pomasia vernacularia, Problepsis craspediata, Psaliodes tripita, Pseudobaptria bogumilaria, Psilalcis holzwegensis, Psilosticha mactaria, Psyra similaria, Pyrinia reflectaria, Rhodophthitus anamesa, Sarracena leptaliaria, Semaeopus fissaria, Smyriodes aplectaria, Stenalcidia congruata, Stibaroma aphronesa, Synegia camptogrammaria, Tasta micaceata, Thysanopyga abdominaria, Xanthorhoe derzhavini, Xanthorhoe pseudoannotinata, Xanthorhoe uralensis, Xanthorhoe vacuaria, Zamarada hyalinaria.

## Why decline rather than take the ~170 for free

Both are small enough that writing a dedicated importer for 41 or 129
species isn't worth the engineering cost relative to just hand-placing them
later if someone wants to — neither needs a new family or order (both
families are already 100% held), so it would be a `merge_family`-style
append, not a structural change. Not done here; flagged as a cheap future
pickup if anyone revisits Carabidae or Geometridae specifically, not a
reason to reverse the decline.
