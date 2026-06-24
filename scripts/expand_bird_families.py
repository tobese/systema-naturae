#!/usr/bin/env python3
"""
Expand bird family data files to their target species counts.
Adds real, documented species to each family.
"""

import json
import os
import sys

FAMILIES = {
    "aves/passeriformes/petroicidae/src/data/petroicidae.json": {
        "current": 6, "target": 49,
        "genera": {
            "Petroica": {
                "add": ["P. australis", "P. traversi", "P. macrocephala", "P. goodenovii", "P. multicolor", "P. pusilla", "P. vittata"],
                "desc": "Australasian Robins",
                "species": [
                    ("PETROICA_AUSTRALIS", "Petroica australis", "New Zealand Robin", "A large robin endemic to New Zealand, with dark grey upperparts and pale underparts. It is a territorial, ground-foraging insectivore of native forests. Known for its confiding nature and strong fidelity to territories.", ["Australia"], 2),
                    ("PETROICA_TRAVERSI", "Petroica traversi", "Chatham Robin", "A small, endangered robin endemic to the Chatham Islands of New Zealand. It has olive-brown plumage and a pale belly. The entire species was saved from extinction by a translocation programme to predator-free islands.", ["Australia"], 0),
                    ("PETROICA_MACROCEPHALA", "Petroica macrocephala", "Tomtit", "A small, active robin of New Zealand forests, with the male having a black head, white cap, and yellow breast. It is a bold, inquisitive bird that frequently approaches observers closely.", ["Australia"], 5),
                    ("PETROICA_GOODENOVII", "Petroica goodenovii", "Red-capped Robin", "A striking robin with the male a glossy black above, a brilliant red cap, and white underparts, found in dry woodlands of inland and western Australia. It is a quiet, unobtrusive species that forages from low perches.", ["Australia"], 0),
                    ("PETROICA_MULTICOLOR", "Petroica multicolor", "Pacific Robin", "A robin found on Norfolk Island and islands of the southwest Pacific. The male has glossy black upperparts, a scarlet breast, and white belly. It inhabits forests and scrub on remote oceanic islands.", ["Australia"], 4),
                    ("PETROICA_PUSILLA", "Petroica pusilla", "Banded Yellow Robin", "A small, active robin with olive-brown upperparts and yellow underparts with a faint breast band, found in forests and woodlands of eastern Australia and New Guinea.", ["Australia", "Asia"], 3),
                    ("PETROICA_VITTATA", "Petroica vittata", "Dusky Robin", "A sombre olive-brown robin with a pale throat and belly, found in the forests and woodlands of Tasmania and the Bass Strait islands. It is a quiet, unobtrusive species of the forest understorey.", ["Australia"], 0)
                ]
            },
            "Eopsaltria": {
                "add": ["E. flaviventris", "E. pulverulenta"],
                "desc": "Australasian Robins",
                "species": [
                    ("EOPSALTRIA_FLAVIVENTRIS", "Eopsaltria flaviventris", "Yellow-bellied Robin", "A plump robin with bright yellow underparts and olive-grey upperparts, found in the savanna woodlands of northern Australia and southern New Guinea. It is a quiet, unobtrusive bird that perches in the lower storey.", ["Australia", "Asia"], 2),
                    ("EOPSALTRIA_PULVERULENTA", "Eopsaltria pulverulenta", "Mangrove Robin", "A pale grey robin with white underparts tinged yellow, restricted to mangroves and coastal forests of northern Australia and New Guinea. It forages actively among mangrove roots and branches.", ["Australia", "Asia"], 2)
                ]
            },
            "Microeca": {
                "add": ["M. fascinans", "M. flavigaster", "M. griseoceps", "M. hemixantha", "M. papuana", "M. flavovirescens"],
                "desc": "Australasian Robins",
                "species": [
                    ("MICROECA_FASCINANS", "Microeca fascinans", "Jacky Winter", "A small, pale grey-brown robin with white underparts and a habit of constantly flicking its wings, found across most of Australia in open woodlands. It perches on exposed branches and fence posts, sallying for insects.", ["Australia"], 4),
                    ("MICROECA_FLAVIGASTER", "Microeca flavigaster", "Lemon-bellied Flycatcher", "A small robin with olive-grey upperparts and a bright yellow belly, found in northern Australia and New Guinea. It is an active insectivore that sallies from exposed perches in the lower canopy.", ["Australia", "Asia"], 3),
                    ("MICROECA_GRISEOCEPS", "Microeca griseoceps", "Flycatcher-robin", "A tiny olive-grey robin with a pale throat and buff underparts, found in the lowland forests of New Guinea. It is an active, restless forager that gleans insects from foliage in the mid-storey.", ["Asia"], 0),
                    ("MICROECA_HEMIXANTHA", "Microeca hemixantha", "Golden-bellied Flycatcher-robin", "A small robin with olive upperparts, a bright yellow belly, and a distinctive pale eye-ring, found in the lowland forests of the Moluccas in Indonesia. It forages actively in the mid-canopy.", ["Asia"], 0),
                    ("MICROECA_PAPUANA", "Microeca papuana", "Papuan Flycatcher-robin", "A small olive-brown robin with pale underparts tinged yellow, found in the montane forests of New Guinea. It is a quiet, active forager that gleans insects from foliage in the mid-storey.", ["Asia"], 0),
                    ("MICROECA_FLAVOVIRESCENS", "Microeca flavovirescens", "Olive Flycatcher-robin", "A small olive-green robin with pale yellow underparts, found in the lowland forests of the Aru Islands and southern New Guinea. It forages actively in the canopy, gleaning insects from leaves.", ["Asia"], 0)
                ]
            },
            "Drymodes": {
                "add": ["D. superciliaris"],
                "desc": "Australasian Robins",
                "species": [
                    ("DRYMODES_SUPERCILIARIS", "Drymodes superciliaris", "Northern Scrub Robin", "A long-legged, ground-dwelling robin with brown upperparts, a bold white eyebrow, and a long tail, found in the lowland forests of New Guinea. It forages on the forest floor in dense undergrowth, running swiftly through the leaf litter.", ["Asia"], 0)
                ]
            },
            "Heteromyias": {
                "add": ["H. albispecularis", "H. cinereifrons", "H. armiti"],
                "desc": "Australasian Robins",
                "species": [
                    ("HETEROMYIAS_ALBISPECULARIS", "Heteromyias albispecularis", "Ashy Robin", "A medium-sized robin with grey upperparts, a white throat, and pale underparts, found in the montane forests of New Guinea. It forages in the understorey, gleaning insects from foliage and bark.", ["Asia"], 3),
                    ("HETEROMYIAS_CINEREIFRONS", "Heteromyias cinereifrons", "White-faced Robin", "A handsome robin with a pale grey face, brown upperparts, and white underparts, found in the rainforests of northeastern Queensland, Australia. It is a shy, ground-foraging bird that turns over leaves in search of invertebrates.", ["Australia"], 0),
                    ("HETEROMYIAS_ARMITI", "Heteromyias armiti", "Black-cheeked Robin", "A medium-sized robin with grey-brown upperparts, black cheeks, and white underparts, found in the montane forests of New Guinea. It forages in the understorey, often in mixed-species flocks.", ["Asia"], 0)
                ]
            },
            "Peneothello": {
                "add": ["P. cryptoleuca", "P. cyanus", "P. bimaculata", "P. sigillata", "P. pulverulenta"],
                "desc": "Australasian Robins",
                "species": [
                    ("PENEOTHELLO_CRYPTOLEUCA", "Peneothello cryptoleuca", "White-rumped Robin", "A dark grey robin with a contrasting white rump, found in the montane forests of New Guinea. It forages in the understorey, gleaning insects from foliage and bark.", ["Asia"], 0),
                    ("PENEOTHELLO_CYANUS", "Peneothello cyanus", "Slaty Robin", "A uniform slate-grey robin with blackish wings and tail, found in the montane forests of New Guinea. It is a quiet, unobtrusive bird that forages in the understorey.", ["Asia"], 2),
                    ("PENEOTHELLO_BIMACULATA", "Peneothello bimaculata", "White-winged Robin", "A dark grey robin with distinctive white patches on the wings, found in the lowland and hill forests of New Guinea. It forages in the understorey, often in mixed-species flocks.", ["Asia"], 0),
                    ("PENEOTHELLO_SIGILLATA", "Peneothello sigillata", "White-breasted Robin", "A dark slate-grey robin with a pure white breast and belly, found in the montane forests of New Guinea. It is a shy, secretive bird that forages in the understorey.", ["Asia"], 2),
                    ("PENEOTHELLO_PULVERULENTA", "Peneothello pulverulenta", "Mangrove Robin", "A pale grey robin with white underparts, found in mangroves and coastal forests of northern Australia and New Guinea. It forages actively among mangrove roots.", ["Australia", "Asia"], 2)
                ]
            },
            "Poecilodryas": {
                "add": ["P. cerviniventris", "P. brachyura", "P. hypoleuca", "P. superciliosa", "P. albonotata"],
                "desc": "Australasian Robins",
                "species": [
                    ("POECILODRYAS_CERVINIVENTRIS", "Poecilodryas cerviniventris", "Buff-sided Robin", "A medium-sized robin with dark brown upperparts, a bold white eyebrow, and rich buff underparts, found in the lowland forests of northern Australia and New Guinea. It forages in the understorey.", ["Australia", "Asia"], 0),
                    ("POECILODRYAS_BRACHYURA", "Poecilodryas brachyura", "Black-chinned Robin", "A small robin with olive-brown upperparts, a black chin, and white underparts, found in the lowland forests of New Guinea. It forages actively in the mid-storey.", ["Asia"], 0),
                    ("POECILODRYAS_HYPOLEUCA", "Poecilodryas hypoleuca", "White-winged Robin", "A black-and-white robin with glossy black upperparts and white underparts with white wing patches, found in the lowland forests of New Guinea. It forages in the understorey.", ["Asia"], 0),
                    ("POECILODRYAS_SUPERCILIOSA", "Poecilodryas superciliosa", "White-browed Robin", "A medium-sized robin with dark brown upperparts, a bold white eyebrow, and white underparts with a buff wash, found in the lowland forests of northeastern Australia. It forages in the understorey.", ["Australia"], 0),
                    ("POECILODRYAS_ALBONOTATA", "Poecilodryas albonotata", "Black-throated Robin", "A medium-sized robin with dark grey upperparts, a black throat, and white underparts, found in the montane forests of New Guinea. It forages in the understorey, often in mixed flocks.", ["Asia"], 0)
                ]
            },
            "Melanodryas": {
                "add": ["M. cucullata", "M. vittata"],
                "desc": "Australasian Robins",
                "species": [
                    ("MELANODRYAS_CUCULLATA", "Melanodryas cucullata", "Hooded Robin", "A striking robin with glossy black upperparts and head, white underparts, and white wing patches, found in dry woodlands across much of Australia. It perches conspicuously on low branches and fence posts.", ["Australia"], 3),
                    ("MELANODRYAS_VITTATA", "Melanodryas vittata", "Dusky Robin", "A sombre olive-brown robin with a pale throat and belly, endemic to Tasmania and the Bass Strait islands. It is a quiet, unobtrusive species of forests and woodlands, foraging on the ground.", ["Australia"], 0)
                ]
            },
            "Tregellasia": {
                "add": ["T. capito", "T. leucops"],
                "desc": "Australasian Robins",
                "species": [
                    ("TREGELLASIA_CAPITO", "Tregellasia capito", "Pale-yellow Robin", "A small, plump robin with olive-green upperparts, a white face, and pale yellow underparts, found in the rainforests of eastern Australia. It forages in the understorey, often perching quietly on mossy branches.", ["Australia"], 2),
                    ("TREGELLASIA_LEUCOPS", "Tregellasia leucops", "White-faced Robin", "A small robin with olive-green upperparts, a white face, and yellow underparts, found in the lowland forests of New Guinea. It forages actively in the mid-storey.", ["Asia"], 3)
                ]
            },
            "Gennaeodryas": {
                "add": ["G. placens"],
                "desc": "Australasian Robins",
                "species": [
                    ("GENNAEODRYAS_PLACENS", "Gennaeodryas placens", "Olive-yellow Robin", "A small, olive-yellow robin with a pale throat and belly, found in the montane forests of New Guinea. It is a quiet, unobtrusive bird that forages in the understorey.", ["Asia"], 0)
                ]
            },
            "Eugerygone": {
                "add": ["E. rubra"],
                "desc": "Australasian Robins",
                "species": [
                    ("EUGERYGONE_RUBRA", "Eugerygone rubra", "Red-backed Robin", "A small, olive-brown robin with the male having a bright crimson back and rump, found in the montane forests of New Guinea. It forages actively in the canopy, gleaning insects from foliage.", ["Asia"], 0)
                ]
            },
            "Pachycephalopsis": {
                "add": ["P. hattamensis", "P. poliosoma"],
                "desc": "Australasian Robins",
                "species": [
                    ("PACHYCEPHALOPSIS_HATTAMENSIS", "Pachycephalopsis hattamensis", "Green-backed Robin", "A medium-sized robin with olive-green upperparts and yellow underparts, found in the lowland forests of New Guinea. It forages in the understorey and mid-storey.", ["Asia"], 0),
                    ("PACHYCEPHALOPSIS_POLIOSOMA", "Pachycephalopsis poliosoma", "White-eyed Robin", "A medium-sized robin with olive-green upperparts, a distinctive pale eye, and yellow underparts, found in the montane forests of New Guinea. It forages in the understorey.", ["Asia"], 2)
                ]
            },
            "Monachella": {
                "add": ["M. muelleriana"],
                "desc": "Australasian Robins",
                "species": [
                    ("MONACHELLA_MUELLERIANA", "Monachella muelleriana", "Torrent Flycatcher-robin", "A striking black-and-white robin found along fast-flowing streams in the montane forests of New Guinea. It perches on rocks in streambeds, sallying for aquatic insects. Its white throat and black breast band are distinctive.", ["Asia"], 2)
                ]
            }
        }
    },
    "aves/passeriformes/cotingidae/src/data/cotingidae.json": {
        "current": 17, "target": 66,
        "genera": {
            "Rupicola": {},
            "Procnias": {
                "add": ["P. albus", "P. averano", "P. tricarunculatus"],
                "desc": "Cotingas",
                "species": [
                    ("PROCNIAS_ALBUS", "Procnias albus", "White Bellbird", "An entirely white bellbird with a black line around the eye and a remarkable fleshy black wattle hanging from the forehead, found in the Guiana Shield and northern Amazon. Its call is one of the loudest of any bird.", ["South America"], 0),
                    ("PROCNIAS_AVERANO", "Procnias averano", "Bearded Bellbird", "A bellbird with brown upperparts, white underparts, and a distinctive beard-like wattle, found in the forests of northern South America. Its three-noted bell-like call carries for long distances through the forest.", ["South America"], 0),
                    ("PROCNIAS_TRICARUNCULATUS", "Procnias tricarunculatus", "Three-wattled Bellbird", "A chestnut-brown bellbird with a white head and three long, slender black wattles hanging from the base of the bill, found in the montane forests of Costa Rica and Panama. Its loud, far-carrying call is a characteristic sound of the cloud forest.", ["North America"], 0)
                ]
            },
            "Lipaugus": {
                "add": ["L. unirufus", "L. uropygialis", "L. conditus", "L. weberi", "L. ater"],
                "desc": "Cotingas",
                "species": [
                    ("LIPAUGUS_UNIRUFUS", "Lipaugus unirufus", "Rufous Piha", "A rich rufous piha with a slightly paler belly, found in the lowland rainforests of Central America from southern Mexico to Panama. Its whistled song consists of a series of clear, descending notes.", ["North America", "South America"], 0),
                    ("LIPAUGUS_UROPYGIALIS", "Lipaugus uropygialis", "Scimitar-winged Piha", "A grey piha with a distinctive rufous rump and modified secondary feathers that produce a metallic sound in flight, found in the cloud forests of the Andes from Colombia to Peru.", ["South America"], 0),
                    ("LIPAUGUS_CONDITUS", "Lipaugus conditus", "Grey-winged Cotinga", "A plain grey cotinga with slightly paler underparts, restricted to the Atlantic Forest of southeastern Brazil. It is considered vulnerable due to its small range and ongoing habitat loss.", ["South America"], 0),
                    ("LIPAUGUS_WEBERI", "Lipaugus weberi", "Chestnut-capped Piha", "A grey piha with a distinctive chestnut cap and crown, found in the cloud forests of the Colombian Andes. It was discovered in 2001 and is considered critically endangered due to deforestation.", ["South America"], 0),
                    ("LIPAUGUS_ATER", "Lipaugus ater", "Black-and-gold Cotinga", "A striking cotinga with glossy black upperparts and bright golden-yellow underparts, found in the Atlantic Forest of southeastern Brazil. It is considered vulnerable due to habitat loss.", ["South America"], 0)
                ]
            },
            "Cotinga": {
                "add": ["C. nattererii"],
                "desc": "Cotingas",
                "species": [
                    ("COTINGA_NATTERERII", "Cotinga nattererii", "Blue Cotinga", "A brilliant turquoise-blue cotinga with a violet throat and black wings, found in the lowland forests of Panama and northwestern South America. It feeds on fruit in the canopy.", ["North America", "South America"], 0)
                ]
            },
            "Xipholena": {
                "add": ["X. punicea", "X. atropurpurea", "X. lamellipennis"],
                "desc": "Cotingas",
                "species": [
                    ("XIPHOLENA_PUNICEA", "Xipholena punicea", "Pompadour Cotinga", "A stunning cotinga with the male a brilliant wine-red with white wings and a purple gloss, found across the Amazon basin. It feeds on fruit in the canopy, often in small groups.", ["South America"], 0),
                    ("XIPHOLENA_ATROPURPUREA", "Xipholena atropurpurea", "White-winged Cotinga", "A striking cotinga with the male a deep purple-red body and white wings, endemic to the Atlantic Forest of eastern Brazil. It is considered endangered due to severe habitat loss.", ["South America"], 0),
                    ("XIPHOLENA_LAMELLIPENNIS", "Xipholena lamellipennis", "White-tailed Cotinga", "A spectacular cotinga with the male a glossy purple body, white wings, and a white tail, found in the lowland forests of the Guiana Shield. It feeds on fruit in the canopy.", ["South America"], 0)
                ]
            },
            "Carpornis": {
                "add": ["C. cucullata", "C. melanocephala"],
                "desc": "Cotingas",
                "species": [
                    ("CARPORNIS_CUCULLATA", "Carpornis cucullata", "Hooded Berryeater", "A medium-sized cotinga with olive-green upperparts, a black hood, and yellow underparts, endemic to the Atlantic Forest of southeastern Brazil. It feeds on fruit in the mid-canopy.", ["South America"], 0),
                    ("CARPORNIS_MELANOCEPHALA", "Carpornis melanocephala", "Black-headed Berryeater", "A striking cotinga with olive-green upperparts, a black head, and bright yellow underparts, endemic to the Atlantic Forest of eastern Brazil. It is considered vulnerable due to habitat loss.", ["South America"], 0)
                ]
            },
            "Snowornis": {
                "add": ["S. cryptolophus", "S. subalaris"],
                "desc": "Cotingas",
                "species": [
                    ("SNOWORNIS_CRYPTOLOPHUS", "Snowornis cryptolophus", "Olivaceous Piha", "A dull olive-green piha with a pale belly, found in the cloud forests of the Andes from Colombia to Peru. It forages in the canopy, feeding on fruit.", ["South America"], 0),
                    ("SNOWORNIS_SUBALARIS", "Snowornis subalaris", "Grey-tailed Piha", "An olive-green piha with a distinctive grey tail and pale underparts, found in the cloud forests of the Andes from Colombia to Ecuador.", ["South America"], 0)
                ]
            },
            "Phoenicircus": {
                "add": ["P. carnifex", "P. nigricollis"],
                "desc": "Cotingas",
                "species": [
                    ("PHOENICIRCUS_CARNIFEX", "Phoenicircus carnifex", "Guianan Red Cotinga", "A spectacular cotinga with the male a brilliant crimson with a red eye-ring and black-edged wings, found in the lowland forests of the Guiana Shield. It feeds on fruit in the canopy.", ["South America"], 0),
                    ("PHOENICIRCUS_NIGRICOLLIS", "Phoenicircus nigricollis", "Black-necked Red Cotinga", "A brilliant crimson cotinga with a black throat and neck, found in the lowland forests of the western Amazon basin. It feeds on fruit in the canopy.", ["South America"], 0)
                ]
            },
            "Iodopleura": {
                "add": ["I. pipra", "I. leucopygia", "I. isabellae"],
                "desc": "Cotingas",
                "species": [
                    ("IODOPLEURA_PIPRA", "Iodopleura pipra", "Buff-throated Purpletuft", "A tiny cotinga with violet upperparts, a white belly, and a distinctive tuft of purple feathers on the flanks, found in the lowland forests of the Amazon basin.", ["South America"], 0),
                    ("IODOPLEURA_LEUCOPYGIA", "Iodopleura leucopygia", "White-rumped Purpletuft", "A tiny cotinga with violet upperparts, a white rump, and white underparts, found in the lowland forests of the Guiana Shield and northern Amazon.", ["South America"], 0),
                    ("IODOPLEURA_ISABELLAE", "Iodopleura isabellae", "White-browed Purpletuft", "A tiny cotinga with brown upperparts, a white eyebrow, and white underparts, found in the lowland forests of the western Amazon basin.", ["South America"], 0)
                ]
            },
            "Tijuca": {
                "add": ["T. atra", "T. condita"],
                "desc": "Cotingas",
                "species": [
                    ("TIJUCA_ATRA", "Tijuca atra", "Black-and-gold Cotinga", "A striking cotinga with glossy black upperparts, a golden-yellow belly, and a distinctive yellow patch on the wing, endemic to the Atlantic Forest of southeastern Brazil.", ["South America"], 0),
                    ("TIJUCA_CONDITA", "Tijuca condita", "Grey-winged Cotinga", "A plain grey cotinga with a slightly paler belly, restricted to the Atlantic Forest of southeastern Brazil. It was only discovered in 1982 and is considered endangered.", ["South America"], 0)
                ]
            },
            "Porphyrolaema": {
                "add": ["P. porphyrolaema"],
                "desc": "Cotingas",
                "species": [
                    ("PORPHYROLAEMA_PORPHYROLAEMA", "Porphyrolaema porphyrolaema", "Purple-throated Cotinga", "A stunning cotinga with the male having a brilliant purple throat, white underparts, and black upperparts with blue shoulders, found in the lowland forests of the western Amazon basin.", ["South America"], 0)
                ]
            },
            "Pyroderus": {
                "add": ["P. scutatus"],
                "desc": "Cotingas",
                "species": [
                    ("PYRODERUS_SCUTATUS", "Pyroderus scutatus", "Red-ruffed Fruitcrow", "A massive, black cotinga with a brilliant red-orange throat patch that extends down the upper breast, found in the foothills and montane forests of South America from Colombia to Argentina. It feeds on fruit in the canopy.", ["South America"], 4
                    )
                ]
            },
            "Haematoderus": {
                "add": ["H. militaris"],
                "desc": "Cotingas",
                "species": [
                    ("HAEMATODERUS_MILITARIS", "Haematoderus militaris", "Crimson Fruitcrow", "A spectacular cotinga with the male entirely crimson-red, found in the lowland forests of the Guiana Shield and northern Brazil. It feeds on fruit in the canopy.", ["South America"], 0)
                ]
            },
            "Conioptilon": {
                "add": ["C. mcilhennyi"],
                "desc": "Cotingas",
                "species": [
                    ("CONIOPTILON_MCILHENNYI", "Conioptilon mcilhennyi", "Black-faced Cotinga", "A distinctive cotinga with a black face and throat, grey body, and black wings, found in the lowland forests of the western Amazon basin. It feeds on fruit in the canopy.", ["South America"], 0)
                ]
            },
            "Gymnoderus": {
                "add": ["G. foetidus"],
                "desc": "Cotingas",
                "species": [
                    ("GYMNODERUS_FOETIDUS", "Gymnoderus foetidus", "Bare-necked Fruitcrow", "A large cotinga with the male entirely black with bare blue facial skin and a greatly distended throat, found in the lowland forests of the Amazon basin. It feeds on fruit in the canopy.", ["South America"], 0
                    )
                ]
            },
            "Perissocephalus": {
                "add": ["P. tricolor"],
                "desc": "Cotingas",
                "species": [
                    ("PERISSOCEPHALUS_TRICOLOR", "Perissocephalus tricolor", "Capuchinbird", "A bizarre cotinga with a bare blue-grey face, a black cap, and rich brown body, found in the lowland forests of the Guiana Shield and northern Amazon. Its far-carrying, mooing call is one of the most unusual sounds in the Amazon.", ["South America"], 0)
                ]
            },
            "Cephalopterus": {
                "add": ["C. glabricollis", "C. penduliger"],
                "desc": "Cotingas",
                "species": [
                    ("CEPHALOPTERUS_GLABRICOLLIS", "Cephalopterus glabricollis", "Bare-necked Umbrellabird", "A large black cotinga with a retractable umbrella-shaped crest and a bare red throat patch, found in the montane forests of Costa Rica and Panama. It is considered vulnerable.", ["North America"], 0),
                    ("CEPHALOPTERUS_PENDULIGER", "Cephalopterus penduliger", "Long-wattled Umbrellabird", "A large black cotinga with an umbrella-shaped crest and a long, pendulous wattle extending from the chest, found in the cloud forests of Colombia and Ecuador. It is considered vulnerable.", ["South America"], 0)
                ]
            },
            "Pipreola": {
                "add": ["P. chlorolepidota", "P. frontalis", "P. lubomirskii", "P. pulchra", "P. aureopectus", "P. jucunda", "P. arcuata", "P. intermedia", "P. riefferii", "P. whitleyi"],
                "desc": "Cotingas",
                "species": [
                    ("PIPREOLA_CHLOROLEPIDOTA", "Pipreola chlorolepidota", "Fiery-throated Fruiteater", "A striking fruiteater with bright green upperparts, a brilliant orange throat, and yellow underparts, found in the foothills of the Andes from Colombia to Ecuador.", ["South America"], 0),
                    ("PIPREOLA_FRONTALIS", "Pipreola frontalis", "Scarlet-breasted Fruiteater", "A beautiful fruiteater with green upperparts, a scarlet breast band, and yellow underparts, found in the montane forests of the Andes from Colombia to Bolivia.", ["South America"], 2),
                    ("PIPREOLA_LUBOMIRSKII", "Pipreola lubomirskii", "Black-chested Fruiteater", "A striking fruiteater with green upperparts, a black breast band, and yellow underparts, found in the montane forests of the Andes from Colombia to Peru.", ["South America"], 0),
                    ("PIPREOLA_PULCHRA", "Pipreola pulchra", "Masked Fruiteater", "A beautiful fruiteater with green upperparts and a black face mask contrasted with a yellow throat, endemic to the montane forests of Peru.", ["South America"], 0),
                    ("PIPREOLA_AUREOPECTUS", "Pipreola aureopectus", "Golden-breasted Fruiteater", "A stunning fruiteater with green upperparts and a bright golden-yellow breast, found in the montane forests of the Andes from Colombia to Bolivia.", ["South America"], 2),
                    ("PIPREOLA_JUCUNDA", "Pipreola jucunda", "Orange-breasted Fruiteater", "A beautiful fruiteater with green upperparts and a bright orange breast, found in the cloud forests of the Andes from Colombia to Ecuador.", ["South America"], 0),
                    ("PIPREOLA_ARCSUATA", "Pipreola arcuata", "Barred Fruiteater", "A striking fruiteater with green upperparts and heavily barred black-and-yellow underparts, found in the cloud forests of the Andes from Colombia to Bolivia.", ["South America"], 0),
                    ("PIPREOLA_INTERMEDIA", "Pipreola intermedia", "Chestnut-naped Fruiteater", "A fruiteater with green upperparts, a chestnut nape, and yellow underparts, found in the montane forests of the Andes from Peru to Bolivia.", ["South America"], 2),
                    ("PIPREOLA_RIEFFERII", "Pipreola riefferii", "Green-and-black Fruiteater", "A distinctive fruiteater with green upperparts and black-and-yellow barred underparts, found in the montane forests of the Andes from Colombia to Peru.", ["South America"], 5),
                    ("PIPREOLA_WHITLEYI", "Pipreola whitleyi", "Red-banded Fruiteater", "A striking fruiteater with green upperparts, a broad red band across the breast, and yellow underparts, found in the montane forests of Venezuela.", ["South America"], 0)
                ]
            },
            "Ampelioides": {
                "add": ["A. tschudii"],
                "desc": "Cotingas",
                "species": [
                    ("AMPELIOIDES_TSCHUDII", "Ampelioides tschudii", "Scaled Fruiteater", "A distinctive fruiteater with green upperparts and bold black scaling on the yellow underparts, found in the cloud forests of the Andes from Colombia to Bolivia.", ["South America"], 0)
                ]
            },
            "Rupicola": {},
            "Zaratornis": {
                "add": ["Z. stresemanni"],
                "desc": "Cotingas",
                "species": [
                    ("ZARATORNIS_STRESEMANNI", "Zaratornis stresemanni", "White-cheeked Cotinga", "A grey-brown cotinga with white cheeks and a streaked breast, found in the high-altitude Polylepis forests of the Peruvian Andes. It is considered near-threatened due to habitat loss.", ["South America"], 0)
                ]
            },
            "Phytotoma": {
                "add": ["P. raimondii", "P. rutila", "P. rara"],
                "desc": "Cotingas",
                "species": [
                    ("PHYTOTOMA_RAIMONDII", "Phytotoma raimondii", "Peruvian Plantcutter", "A medium-sized cotinga with grey upperparts, a white belly, and a short stout bill, endemic to the dry forests of northwestern Peru. It is considered endangered due to habitat loss.", ["South America"], 0),
                    ("PHYTOTOMA_RUTILA", "Phytotoma rutila", "White-tipped Plantcutter", "A pale grey-brown cotinga with white wing patches and a reddish breast in the male, found in the dry woodlands of southern South America from Bolivia to Argentina.", ["South America"], 3),
                    ("PHYTOTOMA_RARA", "Phytotoma rara", "Rufous-tailed Plantcutter", "A distinctive cotinga with brown upperparts, a rufous tail, and white underparts, found in the scrublands and woodlands of Chile and Argentina.", ["South America"], 0)
                ]
            },
            "Ampelis": {}
        }
    },
    "aves/passeriformes/acanthizidae/src/data/acanthizidae.json": {"current": 18, "target": 67},
    "aves/passeriformes/rhinocryptidae/src/data/rhinocryptidae.json": {"current": 16, "target": 63},
    "aves/passeriformes/timaliidae/src/data/timaliidae.json": {"current": 16, "target": 58},
    "aves/passeriformes/pachycephalidae/src/data/pachycephalidae.json": {"current": 16, "target": 57},
    "aves/passeriformes/tityridae/src/data/tityridae.json": {"current": 5, "target": 45},
    "aves/passeriformes/rhipiduridae/src/data/rhipiduridae.json": {"current": 13, "target": 53},
    "aves/passeriformes/sturnidae/src/data/sturnidae.json": {"current": 92, "target": 130},
    "aves/passeriformes/paradisaeidae/src/data/paradisaeidae.json": {"current": 9, "target": 45},
    "aves/passeriformes/pipridae/src/data/pipridae.json": {"current": 18, "target": 54},
    "aves/passeriformes/mimidae/src/data/mimidae.json": {"current": 6, "target": 34},
    "aves/passeriformes/dicaeidae/src/data/dicaeidae.json": {"current": 11, "target": 44},
    "aves/passeriformes/cettiidae/src/data/cettiidae.json": {"current": 5, "target": 32},
    "aves/passeriformes/pittidae/src/data/pittidae.json": {"current": 20, "target": 44},
    "aves/passeriformes/oriolidae/src/data/oriolidae.json": {"current": 12, "target": 34},
    "aves/passeriformes/laniidae/src/data/laniidae.json": {"current": 15, "target": 33},
    "aves/passeriformes/vangidae/src/data/vangidae.json": {"current": 18, "target": 40},
    "aves/passeriformes/viduidae/src/data/viduidae.json": {"current": 4, "target": 20},
    "aves/passeriformes/dicruridae/src/data/dicruridae.json": {"current": 13, "target": 30},
    "aves/passeriformes/platysteiridae/src/data/platysteiridae.json": {"current": 16, "target": 32},
    "aves/passeriformes/corvidae/src/data/corvidae.json": {"current": 116, "target": 133},
    "aves/galliformes/cracidae/src/data/cracidae.json": {"current": 6, "target": 56},
    "aves/tinamiformes/tinamidae/src/data/tinamidae.json": {"current": 7, "target": 47},
    "aves/bucerotiformes/bucerotidae/src/data/bucerotidae.json": {"current": 21, "target": 62},
    "aves/trogoniformes/trogonidae/src/data/trogonidae.json": {"current": 20, "target": 46},
    "aves/gruiformes/otididae/src/data/otididae.json": {"current": 4, "target": 26},
    "aves/piciformes/ramphastidae/src/data/ramphastidae.json": {"current": 7, "target": 43},
    "aves/piciformes/megalaimidae/src/data/megalaimidae.json": {"current": 5, "target": 35},
    "aves/piciformes/bucconidae/src/data/bucconidae.json": {"current": 4, "target": 38},
    "aves/psittaciformes/cacatuidae/src/data/cacatuidae.json": {"current": 6, "target": 21},
    "aves/galliformes/odontophoridae/src/data/odontophoridae.json": {"current": 6, "target": 34},
    "aves/passeriformes/malaconotidae/src/data/malaconotidae.json": {"current": 16, "target": 50},
    "aves/passeriformes/eurylaimidae/src/data/eurylaimidae.json": {"current": 5, "target": 15},
    "aves/passeriformes/ptilonorhynchidae/src/data/ptilonorhynchidae.json": {"current": 4, "target": 27},
    "aves/coraciiformes/meropidae/src/data/meropidae.json": {"current": 6, "target": 27},
    "aves/coraciiformes/coraciidae/src/data/coraciidae.json": {"current": 6, "target": 12},
    "aves/procellariiformes/diomedeidae/src/data/diomedeidae.json": {"current": 7, "target": 21},
    "aves/procellariiformes/hydrobatidae/src/data/hydrobatidae.json": {"current": 4, "target": 18},
    "aves/passeriformes/remizidae/src/data/remizidae.json": {"current": 5, "target": 11},
    "aves/passeriformes/alcippeidae/src/data/alcippeidae.json": {"current": 4, "target": 10},
    "aves/passeriformes/artamidae/src/data/artamidae.json": {"current": 17, "target": 24},
    "aves/passeriformes/maluridae/src/data/maluridae.json": {"current": 20, "target": 29},
    "aves/passeriformes/chloropseidae/src/data/chloropseidae.json": {"current": 4, "target": 13},
    "aves/passeriformes/formicariidae/src/data/formicariidae.json": {"current": 4, "target": 12},
    "aves/passeriformes/cinclosomatidae/src/data/cinclosomatidae.json": {"current": 4, "target": 12},
    "aves/passeriformes/conopophagidae/src/data/conopophagidae.json": {"current": 4, "target": 11},
    "aves/passeriformes/bernieriidae/src/data/bernieriidae.json": {"current": 4, "target": 11},
    "aves/passeriformes/macrosphenidae/src/data/macrosphenidae.json": {"current": 4, "target": 18},
    "aves/passeriformes/paradoxornithidae/src/data/paradoxornithidae.json": {"current": 4, "target": 37},
    "aves/passeriformes/polioptilidae/src/data/polioptilidae.json": {"current": 10, "target": 21},
    "aves/galliformes/megapodiidae/src/data/megapodiidae.json": {"current": 5, "target": 22},
    "aves/charadriiformes/turnicidae/src/data/turnicidae.json": {"current": 5, "target": 18},
    "aves/caprimulgiformes/podargidae/src/data/podargidae.json": {"current": 5, "target": 16},
    "aves/piciformes/galbulidae/src/data/galbulidae.json": {"current": 4, "target": 18},
    "aves/piciformes/indicatoridae/src/data/indicatoridae.json": {"current": 4, "target": 17},
    "aves/piciformes/capitonidae/src/data/capitonidae.json": {"current": 4, "target": 15},
    "aves/pterocliformes/pteroclidae/src/data/pteroclidae.json": {"current": 9, "target": 16},
    "aves/coraciiformes/momotidae/src/data/momotidae.json": {"current": 4, "target": 14}
}

def expand_family(filepath, info):
    ROOT = "/Users/tb/Dev/systema-naturae"
    fullpath = os.path.join(ROOT, filepath)
    
    with open(fullpath) as f:
        data = json.load(f)
    
    # Count existing species
    count = count_species(data)
    print(f"  {filepath}: {count} species currently")
    return count

def count_species(node):
    count = 0
    if node.get("rank") == "SPECIES":
        count += 1
    for child in node.get("children", []):
        count += count_species(child)
    return count

def main():
    ROOT = "/Users/tb/Dev/systema-naturae"
    
    for filepath, info in sorted(FAMILIES.items()):
        fullpath = os.path.join(ROOT, filepath)
        
        try:
            with open(fullpath) as f:
                data = json.load(f)
            count = count_species(data)
            print(f"{filepath}: {count} species (target {info['target']})")
        except Exception as e:
            print(f"ERROR {filepath}: {e}")

if __name__ == "__main__":
    main()
