# COL 26.10 XR: names filed under a homonym genus in another kingdom

Measured 2026-11-13, while applying `checklistbank-316691` (Catalogue of Life
2026-10-16 XR, DOI 10.48580/dgzlf). A dated snapshot, not kept current.

## What happened

The apply added 22 species ids to a second kingdom. In 20 of them both copies
carry the same author and year, so they are not homonyms but one organism
held twice. The wrong copy usually follows COL26.10 XR's own placement: the
release files the name under a genus of the same spelling in another kingdom
(the shield bug *Urostylis blattiformis* Bergroth, 1916 under Plantae /
Asteraceae, where *Urostylis* is also an aster genus). Our transform followed
the release, as it should; the record is wrong at the source.

Two cases go the other way: an animal copy from COL26.9 XR or Wikidata in a
kingdom the 26.10 release gets right (*Graphium penicillioides*,
*Plasmodiophora alni*).

## How each was decided

For each binomial, ChecklistBank's exact name search
(`/nameusage/search?q=<name>&content=SCIENTIFIC_NAME&type=EXACT`) counted the
kingdoms other datasets give it, leaving out the COL releases and Wikidata
Species, which are the copies in question. GBIF Backbone's match is listed
too, as support only. The rule is the one the 2026-11-02 lookup used: remove a
copy when the other datasets place the binomial in one kingdom at least 3:1.
Each decision, with its counts and query URLs, is in
`data/cross-kingdom-homonym-decisions.json` (decided 2026-11-13), which also
stops `importTransformed.py` putting the copy back on a re-import.
`scripts/resolveWeakHomonyms.py --apply` removed the copies and moved their
source ids to the kept one.

## Removed (16)

| species | kept | removed | other datasets (kept : removed) | wrong copy from | COL26.10 XR id |
|---|---|---|---:|---|---|
| *Callianira bucephalon* | animalia / Ocyropsidae | plantae / Moraceae | 13 : 1 | COL26.10 XR | VSHX2 |
| *Camptocarpus dilatipleura* Martins and Pereira, 1965 | animalia / Erotylidae | plantae / Apocynaceae | 12 : 1 | COL26.10 XR | V4435 |
| *Graphium penicillioides* Corda | fungi / Microascaceae | animalia / Papilionidae | 72 : 2 | Wikidata | 6KRCC (right) |
| *Gymnaster pentasteris* | chromista / Amphilothaceae | plantae / Asteraceae | 14 : 3 | COL26.10 XR | VSJXL |
| *Ioanella mimon* (Fain, 1973) | animalia / Myobiidae | chromista / Eponididae | 15 : 1 | COL26.10 XR | QQ3JV |
| *Lamarckiana atlantica* Cushman, 1931 | chromista / Ceratobuliminidae | animalia / Pamphagidae | 13 : 1 | COL26.10 XR | Q2NBH |
| *Lamarckiana atlantiformis* McCulloch, 1981 | chromista / Ceratobuliminidae | animalia / Pamphagidae | 13 : 1 | COL26.10 XR | Q2NBM |
| *Leptotrema dentifemur* (Stelfox, 1943) | animalia / Braconidae | fungi / Graphidaceae | 18 : 1 | COL26.10 XR | PQVJF |
| *Loxocephalus boops* (Wesmael, 1835) | animalia / Braconidae | chromista / Loxocephalidae | 15 : 1 | COL26.10 XR | Q8VKT |
| *Meria tripunctata* (Rossi, 1790) | animalia / Tiphiidae | fungi / Hemiphacidiaceae | 24 : 1 | COL26.10 XR | QM58Q |
| *Mickelia cressoni* Suarez, 1966 | animalia / Mutillidae | plantae / Dryopteridaceae | 15 : 2 | COL26.10 XR | R4FW7 |
| *Orthacanthus gracilis* (Giebel, 1848) | animalia / Orthacanthidae | plantae / Poaceae | 33 : 1 | COL26.10 XR | RH2PT |
| *Plasmodiophora alni* (Woronin) Möller | chromista / Plasmodiophoridae | fungi / Plasmodiophoraceae | 14 : 1 | COL26.9 XR | RZJG6 (right) |
| *Urostylis blattiformis* Bergroth, 1916 | animalia / Urostylididae | plantae / Asteraceae | 20 : 1 | COL26.10 XR | TWHCJ |
| *Urostylis chinai* Maa, 1947 | animalia / Urostylididae | plantae / Asteraceae | 18 : 1 | COL26.10 XR | TWHCQ |
| *Urostylis paratrifidus* Ren & Lin, 2003 | animalia / Urostylididae | plantae / Asteraceae | 18 : 1 | COL26.10 XR | TWHFF |

A COL26.10 XR id opens at
`https://www.checklistbank.org/dataset/316691/taxon/<id>`. The 14 marked
COL26.10 XR are the ones worth reporting to COL.

## Open (6): the other datasets do not settle them

| species | held in | other datasets | COL26.10 XR places it in |
|---|---|---:|---|
| *Dinamoeba mirabilis* Leidy, 1874 | chromista, protozoa | protozoa 4 : chromista 3 | chromista / Dinamoebidiaceae (VDQ7V) |
| *Isospora annthomassonae* Jamriška, López & Modrý, 2012 | animalia, chromista | animalia 9 : chromista 4 | chromista / Eimeriidae (PRGCM) |
| *Kempia longicolpites* Friis, Crane & Pedersen | animalia, plantae | plantae 9 : animalia 5; GBIF animalia | animalia / Philopotamidae (QBLVY) |
| *Ophiocordyceps gotrae* Wang et al., 2026 | animalia, fungi | animalia 2 : fungi 1 | fungi / Ophiocordycipitaceae (VQJTH) |
| *Ophiocordyceps yuanyangensis* Wang et al., 2026 | animalia, fungi | animalia 2 : fungi 1 | fungi / Ophiocordycipitaceae (VQJTG) |
| *Phialina salinarum* (Kahl, 1928) | chromista, fungi | chromista 2 : fungi 2; GBIF chromista | fungi / Pezizellaceae (VSL89) |

Dinamoeba and Plasmodiophora are not misfilings but the two COL releases
disagreeing on the kingdom. The animal copies of the two *Ophiocordyceps*
(Hepialidae, from COL26.9 XR) and of *Isospora* (Tyrannidae) look like a host
taken for the parent, but too few datasets hold these recent names to show it
3:1. They stay in verifyTree's undeclared set until a register decides them.
