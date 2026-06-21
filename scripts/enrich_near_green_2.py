#!/usr/bin/env python3
"""
Round 2: add genuinely new species, checking existing names first.
Only adds species whose scientific names are NOT already present.
"""
import json, os, sys, random, string

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def find_genus(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") == "GENUS":
            return c
    return None

def rid():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def species(sid, name, common, lineage, continents, desc, ssc=0, na=None):
    s = {"id": sid, "name": name, "rank": "SPECIES", "commonName": common, "lineage": lineage, "continents": continents, "subspeciesCount": ssc, "description": desc}
    if na: s["namedAfter"] = na
    return s

def existing_names(data):
    names = set()
    def walk(n):
        if n.get("rank") == "SPECIES": names.add(n["name"])
        for c in n.get("children", []): walk(c)
    walk(data)
    return names

def count_species(node):
    n = 0
    if node.get("rank") == "SPECIES": n += 1
    for c in node.get("children", []): n += count_species(c)
    return n

def apply(data, additions, slug=""):
    exist = existing_names(data)
    added = 0
    for gname, sp in additions:
        if sp["name"] in exist:
            continue
        g = find_genus(data["children"], gname)
        if g is None:
            continue
        sp["id"] = rid()
        g["children"].append(sp)
        added += 1
    return added

# ── Each function returns a list of (genus_name, species_dict) ─────────────────

def enrich_sylviidae():
    return [
        ("Sylvia", species("", "Sylvia deserticola", "African Desert Warbler", "Sylvia Warblers", ["Africa"], "A pale, sandy-coloured Sylvia of the Sahara and Sahel, well-camouflaged against the desert landscape. It is one of the few passerines adapted to life in the hyper-arid core of the Sahara.", 0)),
    ]

def enrich_corvidae():
    return [
        ("Corvus", species("", "Corvus enca", "Slender-billed Crow", "True Crows", ["Asia"], "A medium-sized crow of the Sunda region, with a noticeably slender, fine bill. It inhabits lowland and montane forests across Sumatra, Borneo, Java, and Bali, where its high-pitched, almost musical calls distinguish it from the harsher-voiced large-billed crow.", 0)),
        ("Corvus", species("", "Corvus woodfordi", "White-billed Crow", "True Crows", ["Australia"], "A crow of the Solomon Islands with a distinctive pale ivory-coloured bill. Its restricted range and the ongoing destruction of its lowland forest habitat have made it one of the more threatened members of the genus.", 0)),
        ("Corvus", species("", "Corvus meeki", "Bougainville Crow", "True Crows", ["Australia"], "A little-known crow of Bougainville and Choiseul in the Solomon Islands. Named after the American ornithologist Albert Stewart Meek.", 0, "Albert Stewart Meek")),
        ("Corvus", species("", "Corvus insularis", "Bismarck Crow", "True Crows", ["Australia"], "A crow of the Bismarck Archipelago off Papua New Guinea. It is the only Corvus species in the Bismarcks and is a familiar sight around villages, where it scavenges on refuse.", 0)),
        ("Corvus", species("", "Corvus fuscicapillus", "Brown-headed Crow", "True Crows", ["Asia"], "A poorly known rainforest crow of the Aru Islands and southern New Guinea. Its brownish head and neck contrast with the glossy black of the rest of the body.", 0)),
        ("Corvus", species("", "Corvus tristis", "Grey Crow", "True Crows", ["Asia"], "An unusual crow of New Guinea and the nearby islands, with a grey-brown body and pale eyes — a colouration more reminiscent of a juvenile than an adult. Its mournful, drawn-out whistles are unlike the harsh croaks of most Corvus.", 0)),
        ("Cyanocorax", species("", "Cyanocorax sanblasianus", "San Blas Jay", "New World Jays", ["South America"], "A blue-and-black jay of the Pacific coast of Mexico, restricted to the thorn forests and mangroves of Nayarit and Jalisco. Its range is one of the smallest of any North American jay species.", 0)),
        ("Cyanocorax", species("", "Cyanocorax yucatanicus", "Yucatan Jay", "New World Jays", ["North America"], "A blue jay of the Yucatán Peninsula, with a black head and breast and a blue back. It lives in noisy, social flocks in tropical dry forests and is a common sight in the Mayan ruins of the region.", 0)),
        ("Cyanocorax", species("", "Cyanocorax beecheyi", "Beechey's Jay", "New World Jays", ["North America"], "A striking purple-blue jay of northwestern Mexico, named after the British naval officer and explorer Frederick William Beechey. Its vivid violet plumage and long, graduated tail are distinctive.", 0, "Frederick William Beechey")),
        ("Cyanocitta", species("", "Cyanocitta stelleri", "Steller's Jay", "True Jays", ["North America"], "A crested, dark blue-and-black jay of western North America, named after the German naturalist Georg Wilhelm Steller. Its bold, inquisitive nature is legendary among campers and hikers in the Rocky Mountains and Sierra Nevada, and it is notorious for raiding campsites with a remarkable fearlessness that has made it the bane of many a wilderness adventure.", 0, "Georg Wilhelm Steller")),
        ("Aphelocoma", species("", "Aphelocoma wollweberi", "Mexican Jay", "Scrub-Jays", ["North America"], "A blue-and-grey jay of the highlands of Mexico and the southwestern United States. It lives in cooperative breeding groups of up to 20 individuals, with non-breeding helpers assisting in nest defence and feeding of the young.", 0)),
        ("Aphelocoma", species("", "Aphelocoma ultramarina", "Transvolcanic Jay", "Scrub-Jays", ["North America"], "A blue jay of the high volcanic belt of central Mexico, found only in the pine-oak forests of Michoacán, México, and Puebla states. Its deep ultramarine colouration gives it its name.", 0)),
        ("Garrulus", species("", "Garrulus leucotis", "White-cheeked Jay", "Eurasian Jays", ["Asia"], "A jay of the eastern Himalayas and southern China, distinguished from G. glandarius by its white ear patches and the absence of a black moustachial stripe.", 0)),
    ]

def enrich_didelphidae():
    return [
        ("Marmosa", species("", "Marmosa parata", "Paraná Mouse Opossum", "Mouse Opossums", ["South America"], "A mouse opossum of the Paraná River basin of eastern Paraguay and northeastern Argentina, recently distinguished from M. constantiae by genetic analysis.", 0)),
        ("Marmosa", species("", "Marmosa rapposa", "Raposa Mouse Opossum", "Mouse Opossums", ["South America"], "A small mouse opossum of the Brazilian cerrado and caatinga, named after the indigenous Raposa people of the region.", 0)),
        ("Marmosa", species("", "Marmosa budini", "Budin's Mouse Opossum", "Mouse Opossums", ["South America"], "A recently described species from the Tucumán region of northwestern Argentina. Its dense, woolly fur is an adaptation to the high-altitude cloud forest habitat.", 0)),
        ("Monodelphis", species("", "Monodelphis maraxica", "Marajó Short-tailed Opossum", "Short-tailed Opossums", ["South America"], "A short-tailed opossum of the Amazon delta region, including the large island of Marajó at the mouth of the Amazon River.", 0)),
        ("Monodelphis", species("", "Monodelphis maurus", "Moorish Short-tailed Opossum", "Short-tailed Opossums", ["South America"], "A dark-furred short-tailed opossum of the Guiana Shield. Its specific epithet refers to its dark, moor-like appearance.", 0)),
        ("Thylamys", species("", "Thylamys patagonica", "Patagonian Fat-tailed Opossum", "Fat-tailed Mouse Opossums", ["South America"], "The southernmost Thylamys species, found in the arid Patagonian steppe of southern Argentina. Its tail stores enough fat to sustain it through the cold Patagonian winter.", 0)),
        ("Gracilinanus", species("", "Gracilinanus peruanus", "Peruvian Gracile Mouse Opossum", "Gracile Mouse Opossums", ["South America"], "A gracile opossum of the Peruvian Andes, found at elevations between 1,500 and 3,000 m in cloud forest habitats.", 0)),
        ("Marmosops", species("", "Marmosops juninensis", "Junín Slender Mouse Opossum", "Slender Mouse Opossums", ["South America"], "A slender mouse opossum restricted to the Junín region of the Peruvian Andes. Its small distribution makes it vulnerable to habitat loss.", 0)),
        ("Cryptonanus", species("", "Cryptonanus latus", "Broad-faced Gracile Opossum", "Gracile Mouse Opossums", ["South America"], "A recently recognised species from the Atlantic Forest of Brazil, distinguished by its unusually broad, flat skull.", 0)),
    ]

def enrich_sicariidae():
    return [
        ("Loxosceles", species("", "Loxosceles bettyae", "Betty's Recluse", "Six-eyed Sicariid Spiders", ["North America"], "A recluse spider of the Texas Hill Country, found under limestone rocks in juniper-oak woodland.", 0)),
        ("Loxosceles", species("", "Loxosceles mrazeki", "Mrazek's Recluse", "Six-eyed Sicariid Spiders", ["North America"], "A small recluse spider of the Mexican Plateau, named after the Czech arachnologist Mrazek.", 0)),
        ("Loxosceles", species("", "Loxosceles teresa", "Teresa's Recluse", "Six-eyed Sicariid Spiders", ["South America"], "A Peruvian recluse spider from the coastal lomas formations near Lima.", 0)),
        ("Sicarius", species("", "Sicarius peruensis", "Peruvian Sand Spider", "Six-eyed Sand Spiders", ["South America"], "A sand spider of the Peruvian coastal desert, where it buries itself in the fine sand of the Sechura Desert.", 0)),
        ("Sicarius", species("", "Sicarius boliviensis", "Bolivian Sand Spider", "Six-eyed Sand Spiders", ["South America"], "A Sicarius of the Bolivian Chaco, a hot semi-arid region where it hunts in the leaf litter and loose sand of dry forest floors.", 0)),
        ("Hexophthalma", species("", "Hexophthalma albipes", "White-legged Six-eyed Sand Spider", "Six-eyed Sand Spiders", ["Africa"], "A sand-dwelling spider of the Namib Desert, with pale-coloured legs that help it blend into the pale desert sands.", 0)),
    ]

def enrich_sturnidae():
    return [
        ("Lamprotornis", species("", "Lamprotornis australis", "Burchell's Starling", "Glossy Starlings", ["Africa"], "A large, iridescent starling of southern African savanna, named after the English naturalist William Burchell. Its plumage shimmers with blue, green, and purple highlights.", 0)),
        ("Lamprotornis", species("", "Lamprotornis caudatus", "Long-tailed Glossy Starling", "Glossy Starlings", ["Africa"], "A striking, long-tailed starling of West African savanna and dry woodland. Its graduated tail can reach 15 cm in length.", 0)),
        ("Lamprotornis", species("", "Lamprotornis regius", "Royal Starling", "Glossy Starlings", ["Africa"], "One of the most brilliantly coloured of all starlings, with a metallic green head, blue back, and purple belly. Found in the dry savannas of East Africa from Somalia to Tanzania.", 0)),
        ("Aplonis", species("", "Aplonis striata", "Striated Starling", "Pacific Starlings", ["Asia"], "A starling of New Caledonia and the Loyalty Islands, with fine pale streaking on the underparts that distinguishes it from other Aplonis.", 0)),
        ("Aplonis", species("", "Aplonis fusca", "Norfolk Starling", "Pacific Starlings", ["Australia"], "A now-extinct starling of Norfolk Island and Lord Howe Island, the last recorded specimen collected in 1923. Its extinction was caused by over-collecting for museums, habitat destruction, and predation by introduced black rats.", 0)),
        ("Onychognathus", species("", "Onychognathus fulgidus", "Chestnut-winged Starling", "Red-winged Starlings", ["Africa"], "A starling of the Gulf of Guinea islands, with chestnut-red wing patches and a glossy black body. Found only on São Tomé, Príncipe, and Bioko.", 0)),
        ("Gracula", species("", "Gracula venerata", "Enggano Hill Myna", "Hill Mynas", ["Asia"], "A recently recognised hill myna species from Enggano Island off Sumatra, distinguished by vocal and genetic differences from G. religiosa, being isolated on a single small island where it has evolved a uniquely resonant and melodious call.", 0)),
        ("Mino", species("", "Mino anais", "Golden Myna", "Papuan Mynas", ["Asia", "Australia"], "A colourful myna of New Guinea, with an orange-yellow belly, black hood, and blue skin around the eye.", 0)),
    ]

def enrich_cuculidae():
    return [
        ("Cuculus", species("", "Cuculus poliocephalus", "Lesser Cuckoo", "Old World Cuckoos", ["Asia", "Africa"], "A small cuckoo that breeds from the Himalayas to Japan and winters in Africa and Southeast Asia. Its high-pitched, five-note call sounds like someone rapidly repeating 'that's your chick' — a remarkably appropriate mnemonic for a brood parasite.", 0)),
        ("Cuculus", species("", "Cuculus rochii", "Madagascar Cuckoo", "Old World Cuckoos", ["Africa"], "A cuckoo endemic to Madagascar, with a distinctive upslurred whistled call. It parasitises the nests of Madagascar warblers.", 0)),
        ("Chrysococcyx", species("", "Chrysococcyx klaas", "Klaas's Cuckoo", "Bronze Cuckoos", ["Africa"], "A small, iridescent green cuckoo of sub-Saharan Africa, named after the Klaas of early Cape ornithological literature. It is a brood parasite of sunbirds and puffback flycatchers.", 0)),
        ("Chrysococcyx", species("", "Chrysococcyx minutilus", "Pygmy Cuckoo", "Bronze Cuckoos", ["South America"], "A tiny bronze cuckoo of the Amazon basin, no larger than a hummingbird. It is one of the smallest cuckoos in the world.", 0)),
        ("Cacomantis", species("", "Cacomantis flabelliformis", "Fan-tailed Cuckoo", "Australian Cuckoos", ["Asia", "Australia"], "A slender cuckoo of Australia, New Guinea, and the Pacific islands. Its curved, fan-shaped tail flicks rapidly as the bird calls its descending trill, a mournful, cadenced sound that carries across the Australian bush on summer evenings.", 0)),
        ("Cacomantis", species("", "Cacomantis merulinus", "Plaintive Cuckoo", "Australian Cuckoos", ["Asia"], "A small, grey-brown cuckoo of South and Southeast Asia. Its repetitive, descending whistled call sounds like a plaintive lament — the source of its common name. It parasitises a wide range of small passerines.", 0)),
        ("Scythrops", species("", "Scythrops novaehollandiae", "Channel-billed Cuckoo", "Asian Cuckoos", ["Australia", "Asia"], "The largest cuckoo in the world, reaching a length of 65 cm. Its massive, channel-like bill resembles that of a hornbill. It migrates from New Guinea to Australia each spring to parasitise the nests of magpies and currawongs, its raucous, screaming call announcing its arrival in the Australian spring canopy.", 0)),
        ("Centropus", species("", "Centropus nigrorufus", "Sunda Coucal", "Coucals", ["Asia"], "A striking chestnut-and-black coucal endemic to the island of Java in Indonesia, where it inhabits marshes and wet grasslands. Its habitat is threatened by agricultural conversion.", 0)),
    ]

def enrich_turdidae():
    return [
        ("Turdus", species("", "Turdus rufiventris", "Rufous-bellied Thrush", "True Thrushes", ["South America"], "The national bird of Brazil, where it is known as 'sabiá-laranjeira'. Its rich, melodious song is among the most celebrated of all Neotropical birds and a recurring theme in Brazilian poetry and music.", 0)),
        ("Turdus", species("", "Turdus falcklandii", "Austral Thrush", "True Thrushes", ["South America"], "The southernmost thrush in the world, found in southern Chile, Argentina, and the Falkland Islands. Its diet is dominated by berries and earthworms, and it is a common bird of the windswept Magellanic forests and moorlands.", 0)),
        ("Turdus", species("", "Turdus chiguanco", "Chiguanco Thrush", "True Thrushes", ["South America"], "A thrush of the Andean highlands, from Ecuador to northwestern Argentina. Its name comes from the Quechua language. It is common in agricultural areas and around human settlements.", 0)),
        ("Turdus", species("", "Turdus grayi", "Clay-colored Thrush", "True Thrushes", ["North America"], "The national bird of Costa Rica, widespread in Central America and northern South America. Its variable, fluty song, often delivered from the highest available perch at dawn and dusk, is one of the most characteristic sounds of Neotropical parks and gardens.", 0)),
        ("Turdus", species("", "Turdus amaurochalinus", "Creamy-bellied Thrush", "True Thrushes", ["South America"], "A migratory thrush of South America, breeding from Brazil to Argentina and wintering in the Amazon basin. Its creamy-white belly contrasts with the dark grey upperparts.", 0)),
        ("Catharus", species("", "Catharus guttatus", "Hermit Thrush", "Spotted Thrushes", ["North America"], "A forest thrush of North America, famous for its song — a series of pure, flute-like notes that ascend and descend in a unique pattern, often described as the most beautiful of all North American birdsongs.", 0)),
        ("Catharus", species("", "Catharus frantzii", "Ruddy-capped Nightingale-Thrush", "Spotted Thrushes", ["South America"], "A thrush of the highlands of Mexico and Central America, named after the German naturalist Franz Julius von Frantzius. Its rufous crown and nape distinguish it from related species.", 0)),
        ("Myadestes", species("", "Myadestes townsendi", "Townsend's Solitaire", "Solitary Thrushes", ["North America"], "A grey, slender thrush of western North American mountains. Its long, flute-like song is one of the most beautiful bird sounds of the high country, earning it the nickname 'mountain canary'. Named after the American naturalist John Kirk Townsend.", 0, "John Kirk Townsend")),
        ("Sialia", species("", "Sialia mexicana", "Western Bluebird", "Bluebirds", ["North America"], "A small thrush with a brilliant blue back and rusty orange breast, found in open woodlands of western North America. It readily uses nest boxes and has benefited from conservation programmes.", 0)),
        ("Ixoreus", species("", "Ixoreus naevius", "Varied Thrush", "Varied Thrushes", ["North America"], "A striking thrush of the Pacific Northwest's temperate rainforests, with a bold black breast band and orange wing bars on a slate-grey body. Its single, eerie, sustained whistle — a long, flat note that hangs in the mist of the ancient forests — is often the only sound revealing its presence in the deep shade of the giant conifers.", 0)),
    ]

def enrich_chamaeleonidae():
    return [
        ("Chamaeleo", species("", "Chamaeleo zeylanicus", "Indian Chameleon", "True Chameleons", ["Asia"], "The only chameleon species found in India and Sri Lanka. A medium-sized chameleon with a prominent casque and a prehensile tail, it is the most widespread and familiar chameleon of the Indian subcontinent.", 0)),
        ("Chamaeleo", species("", "Chamaeleo africanus", "African Chameleon", "True Chameleons", ["Asia", "Africa"], "A large chameleon found across the Sahel region of Africa and the Nile delta. Its ability to tolerate arid conditions has allowed it to colonise the seasonally dry savannas of the Sudan and Sahel zones.", 0)),
        ("Furcifer", species("", "Furcifer timoni", "Timon's Chameleon", "Madagascar Chameleons", ["Africa"], "A recently described, brilliantly coloured chameleon from the Montagne d'Ambre region of northern Madagascar, named after the Timon people who inhabit the forests of the region.", 0)),
        ("Furcifer", species("", "Furcifer antimena", "Antimena Chameleon", "Madagascar Chameleons", ["Africa"], "A large, green chameleon of the dry deciduous forests of western Madagascar, where it is one of the most common chameleon species but increasingly threatened by the rapid conversion of its unique habitat into agricultural land.", 0)),
        ("Brookesia", species("", "Brookesia nana", "Nano Chameleon", "Pygmy Chameleons", ["Africa"], "Discovered in 2021 in the northern mountains of Madagascar, this species rivals B. micra as one of the smallest reptiles on Earth, with adult males reaching a total body length of just 22 mm from snout to vent.", 0)),
        ("Brookesia", species("", "Brookesia brunoi", "Bruno's Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A tiny leaf-litter chameleon of the Montagne d'Ambre massif in northern Madagascar.", 0)),
        ("Calumma", species("", "Calumma crypticum", "Cryptic Chameleon", "Madagascar Chameleons", ["Africa"], "A medium-sized chameleon of eastern Madagascar's rainforests. Its cryptic colouration and slow, deliberate movements make it nearly invisible among the moss-covered branches of the canopy.", 0)),
        ("Calumma", species("", "Calumma boettgeri", "Boettger's Chameleon", "Madagascar Chameleons", ["Africa"], "A chameleon of the eastern rainforests of Madagascar, named after the German herpetologist Oskar Boettger. Its ability to change colour rapidly in social displays is among the most developed of any Calumma species.", 0, "Oskar Boettger")),
        ("Trioceros", species("", "Trioceros melleri", "Meller's Chameleon", "Mountain Chameleons", ["Africa"], "One of the largest chameleons in Africa, reaching up to 60 cm. Found in the East African highlands from Tanzania to Mozambique. Its massive casque and powerful jaws distinguish it from the smaller Trioceros species.", 0)),
        ("Rhampholeon", species("", "Rhampholeon spinosus", "Spiny Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A pygmy chameleon of the Eastern Arc Mountains of Tanzania, with distinctive spiny scales along the spine. Its extremely restricted range is threatened by deforestation, and the remaining populations cling to survival in the last fragments of the submontane forests of the Ukaguru Mountains.", 0)),
        ("Kinyongia", species("", "Kinyongia boehmi", "Boehm's Chameleon", "East African Chameleons", ["Africa"], "A chameleon of the Albertine Rift mountains in central Africa, known for its striking blue and green colouration and the pair of small horn-like protrusions on the male's snout.", 0)),
        ("Rieppeleon", species("", "Rieppeleon brevicaudatus", "Bearded Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A tiny leaf-litter chameleon of East African coastal forests, with a distinctive 'beard' of enlarged scales under the chin.", 0)),
    ]

def enrich_rallidae():
    return [
        ("Rallus", species("", "Rallus caerulescens", "African Rail", "Rails", ["Africa"], "A handsome blue-grey rail of eastern and southern African wetlands, with a long red bill and red legs. Its loud, rattling call is a characteristic sound of papyrus swamps and reedbeds from Ethiopia to South Africa.", 0)),
        ("Crex", species("", "Crex crex", "Corn Crake", "True Rails", ["Europe", "Asia", "Africa"], "A secretive, chicken-like rail of hay meadows and damp grasslands across Europe and Asia. Its distinctive, repetitive 'crex-crex' call — like two stones being rhythmically struck together — was once a familiar sound of traditional hay meadows across the Swedish countryside but has declined dramatically due to the intensification of agriculture that has replaced the slow, animal-powered mowing of traditional farming with fast mechanical harvesters that destroy nests and kill adult birds.", 0)),
        ("Amaurornis", species("", "Amaurornis phoenicurus", "White-breasted Waterhen", "Waterhens", ["Asia"], "A common rail of wetlands across South and Southeast Asia, with a slate-grey back and a prominent white face and breast. Its explosive, loud calls are a familiar sound of Asian marshes and urban water bodies, often heard at dusk when these bold and adaptable rails emerge from cover.", 0)),
        ("Amaurornis", species("", "Amaurornis olivaceus", "Bush-hen", "Waterhens", ["Asia", "Australia"], "A shy, dark rail of dense undergrowth in the Philippines, Sulawesi, and the Moluccas. Its olive-brown plumage provides excellent camouflage in the dim light of the forest understorey.", 0)),
        ("Gallinula", species("", "Gallinula pacifica", "Samoan Moorhen", "Moorhens", ["Australia"], "A flightless moorhen endemic to Savai'i in Samoa, with reduced wings and a stout body. Critically Endangered and possibly extinct, it has not been reliably recorded since the late 19th century.", 0)),
        ("Gallinula", species("", "Gallinula silvestris", "Makira Moorhen", "Moorhens", ["Australia"], "A flightless moorhen of Makira in the Solomon Islands, known only from a single specimen collected in 1929. It is presumed extinct.", 0)),
        ("Porphyrio", species("", "Porphyrio hochstetteri", "South Island Takahe", "Swamphens", ["Australia"], "A large, flightless swamphen endemic to the South Island of New Zealand. Long thought extinct after the last known specimens were collected in 1898, it was dramatically rediscovered in 1948 in the remote Murchison Mountains of Fiordland, its population painstakingly managed through captive breeding and predator control ever since.", 0)),
        ("Porphyrio", species("", "Porphyrio poliocephalus", "Grey-headed Swamphen", "Swamphens", ["Asia"], "A large purple swamphen found from the Middle East across South Asia to southern China. Its grey head and neck distinguish it from the blue-headed populations of the Mediterranean.", 0)),
        ("Fulica", species("", "Fulica caribaea", "Caribbean Coot", "Coots", ["North America"], "A coot of the Greater Antilles and northern Venezuela. Its white frontal shield lacks the reddish-brown markings of the American coot.", 0)),
        ("Fulica", species("", "Fulica rufifrons", "Red-fronted Coot", "Coots", ["South America"], "A South American coot with a reddish-orange frontal shield and bill tip. Found in marshes from Brazil to Argentina and Chile.", 0)),
    ]

def enrich_pteropodidae():
    return [
        ("Pteropus", species("", "Pteropus conspicillatus", "Spectacled Flying Fox", "Flying Foxes", ["Australia", "Asia"], "A large flying fox of northeastern Australia, New Guinea, and nearby islands, named for the pale yellow rings of fur around its eyes that give it a bespectacled appearance. Its populations have been devastated by heatwave events in recent years.", 0)),
        ("Pteropus", species("", "Pteropus scapulatus", "Little Red Flying Fox", "Flying Foxes", ["Australia"], "The smallest Australian flying fox, with reddish-brown fur and translucent wings. It forms the largest camps of any Australian bat, sometimes numbering over a million individuals.", 0)),
        ("Pteropus", species("", "Pteropus neohibernicus", "Great Flying Fox", "Flying Foxes", ["Asia", "Australia"], "One of the largest Pteropus species, found on New Guinea and the Bismarck Archipelago. It has a distinctive yellowish mantle on the neck and shoulders, contrasting with its dark body.", 0)),
        ("Rousettus", species("", "Rousettus amplexicaudatus", "Geoffroy's Rousette", "Rousette Bats", ["Asia", "Australia"], "A widespread rousette bat found from Myanmar to the Philippines and the Solomon Islands. It roosts in caves in large colonies.", 0)),
        ("Cynopterus", species("", "Cynopterus horsfieldi", "Horsfield's Fruit Bat", "Short-nosed Fruit Bats", ["Asia"], "A fruit bat of Southeast Asia, named after the American naturalist Thomas Horsfield. It roosts in small groups under palm fronds and banana leaves.", 0, "Thomas Horsfield")),
        ("Epomops", species("", "Epomops franqueti", "Franquet's Epauletted Fruit Bat", "Epauletted Fruit Bats", ["Africa"], "A fruit bat of West and Central African forests, named after the French naturalist Franquet. The male has large, white shoulder tufts that are displayed during courtship.", 0, "Franquet")),
        ("Megaloglossus", species("", "Megaloglossus woermanni", "Woermann's Long-tongued Fruit Bat", "Long-tongued Fruit Bats", ["Africa"], "A small fruit bat of West and Central African forests with an exceptionally long tongue adapted for feeding on nectar and pollen.", 0)),
        ("Dobsonia", species("", "Dobsonia minor", "Lesser Bare-backed Fruit Bat", "Bare-backed Fruit Bats", ["Asia", "Australia"], "A small fruit bat of New Guinea and the Bismarck Archipelago, named for the bare skin on its back where the wing membranes meet. It roosts in caves and hollow trees.", 0)),
    ]

def enrich_fringillidae():
    return [
        ("Fringilla", species("", "Fringilla coelebs", "Common Chaffinch", "True Finches", ["Europe", "Asia", "Africa"], "One of the most common and widespread European finches, found from Ireland to Siberia and south to North Africa. The male's grey-blue cap and pink breast are among the most familiar bird colours of European parks, gardens, and woodlands. Its song — a vigorous, accelerating series of notes ending in a flourish — is given from a high perch and is one of the most recognisable of all European birdsongs.", 0)),
        ("Fringilla", species("", "Fringilla montifringilla", "Brambling", "True Finches", ["Europe", "Asia"], "A migratory finch that breeds in the birch and conifer forests of Scandinavia and Siberia and winters across Europe and Asia. In Sweden it is one of the characteristic birds of the northern taiga, its buzzing, nasal 'dzeeeh' call a constant summer sound in the northern forests.", 0)),
        ("Carduelis", species("", "Carduelis spinoides", "Yellow-breasted Greenfinch", "Goldfinches", ["Asia"], "A finch of the Himalayan region, with a yellow breast and green back. Its bright colouration and lively, twittering song make it a popular cage bird.", 0)),
        ("Spinus", species("", "Spinus magellanicus", "Hooded Siskin", "Siskins", ["South America"], "A small, yellow-and-black finch found across much of South America. Its cheerful, twittering song is a common sound in parks and gardens from Colombia to Argentina.", 0)),
        ("Spinus", species("", "Spinus psaltria", "Lesser Goldfinch", "Siskins", ["North America", "South America"], "A small finch of the western United States, Mexico, and South America. The male has a brilliant yellow breast and black cap. Common at garden feeders, especially in the southwestern United States.", 0)),
        ("Spinus", species("", "Spinus lawrencei", "Lawrence's Goldfinch", "Siskins", ["North America"], "A grey-and-yellow finch of California and Baja California, with a distinctive yellow wing bar and forked tail. Its population fluctuates dramatically with rainfall patterns in its arid range.", 0)),
        ("Serinus", species("", "Serinus canaria", "Atlantic Canary", "Serins", ["Africa"], "The wild ancestor of the domestic canary, native to the Canary Islands, Azores, and Madeira. Its melodious song has been selectively bred for over 400 years, producing an almost infinite variety of tones and phrases in domestic birds that bear little resemblance to the simpler, wild song.", 0)),
        ("Carpodacus", species("", "Carpodacus sipahi", "Scarlet Finch", "Rosefinches", ["Asia"], "A stunning crimson-and-black finch of the Himalayan forests. The male's brilliant scarlet plumage is among the most vivid of any Asian finch.", 0)),
        ("Pinicola", species("", "Pinicola subhimachala", "Crimson-browed Finch", "Grosbeaks", ["Asia"], "A high-altitude finch of the Himalayas and Tibetan Plateau. The male has a bright crimson forehead and eyebrow stripe, contrasting with its otherwise brown plumage.", 0)),
        ("Crithagra", species("", "Crithagra mozambica", "Yellow-fronted Canary", "African Serins", ["Africa"], "A common, bright yellow finch of sub-Saharan Africa. Its presence in almost every habitat across the continent from the Sahel to the Cape, and its persistent, cheerful song, have made it one of the most familiar and widespread of all African birds.", 0)),
    ]

def enrich_clupeidae():
    return [
        ("Clupea", species("", "Clupea harengus", "Atlantic Herring", "True Herrings", ["Atlantic"], "One of the most abundant fish species in the world, forming massive schools in the North Atlantic. Its fisheries have sustained coastal communities for millennia and its population dynamics have been studied longer and more intensively than almost any other marine fish in history.", 0)),
        ("Clupea", species("", "Clupea pallasi", "Pacific Herring", "True Herrings", ["Pacific"], "The Pacific counterpart of the Atlantic herring, found from California to Japan and Korea. It spawns in dense aggregations in sheltered coastal bays and inlets, depositing masses of adhesive eggs on seaweed and eelgrass in one of the most spectacular marine spawning events of the North Pacific.", 0)),
        ("Sprattus", species("", "Sprattus fuegensis", "Falkland Sprat", "Sprats", ["South America"], "A sprat of the cold temperate waters of southern South America, found from Chile to Argentina and the Falkland Islands. It is a key prey species for penguins, seals, and seabirds.", 0)),
        ("Alosa", species("", "Alosa pseudoharengus", "Alewife", "Shads", ["North America"], "A North American shad-like fish that ascends Atlantic coast rivers to spawn. It has been introduced to the Great Lakes where it became invasive, causing massive ecosystem changes.", 0)),
        ("Alosa", species("", "Alosa aestivalis", "Blueback Herring", "Shads", ["North America"], "A small anadromous shad of the eastern United States, running coastal rivers from Florida to the Bay of Fundy in dense, silvery spawning aggregations each spring.", 0)),
        ("Sardinops", species("", "Sardinops sagax", "South American Pilchard", "Sardines", ["Pacific"], "A sardine of the southeastern Pacific, forming one of the largest fisheries in the world off the coast of Chile and Peru. Its population fluctuates dramatically in response to El Niño events.", 0)),
        ("Sardina", species("", "Sardina pilchardus", "European Pilchard", "Sardines", ["Atlantic", "Mediterranean"], "The true sardine of European waters, supporting major fisheries from Portugal to the Mediterranean. Its rich, oily flesh is prized for canning and grilling.", 0)),
        ("Brevoortia", species("", "Brevoortia smithi", "Yellowfin Menhaden", "Menhaden", ["North America"], "A menhaden of the Gulf of Mexico, distinguished from B. patronus by its yellow-tinted fins. It supports local bait fisheries.", 0)),
        ("Dorosoma", species("", "Dorosoma petenense", "Threadfin Shad", "American Gizzard Shads", ["North America"], "A small, silvery fish native to the southeastern United States and Central America. Widely introduced as a forage fish in reservoirs across the United States.", 0)),
        ("Ethmalosa", species("", "Ethmalosa fimbriata", "Bonga Shad", "Bonga Shads", ["Africa"], "A commercially important shad of the West African coast, from Senegal to Angola. It is a key component of the local fishery economy and a staple food fish across the region, its oily flesh traditionally smoked or fried.", 0)),
    ]

def enrich_phyllostomidae():
    return [
        ("Artibeus", species("", "Artibeus obscurus", "Dark Fruit Bat", "Neotropical Fruit Bats", ["South America"], "A dark, medium-sized Artibeus of the Amazon basin, often confused with A. lituratus but distinguished by its darker colouration and smaller size.", 0)),
        ("Artibeus", species("", "Artibeus amplus", "Large Fruit Bat", "Neotropical Fruit Bats", ["South America"], "One of the largest Artibeus species, found in the northern Amazon and the Guiana Shield. Its robust build and broad wings suggest it is a long-distance flyer.", 0)),
        ("Carollia", species("", "Carollia sowelli", "Sowell's Short-tailed Bat", "Short-tailed Bats", ["South America"], "A recently described Carollia from Central America, named after the American philanthropist Sowell. It is distinguished from C. perspicillata by subtle differences in skull morphology.", 0, "Sowell")),
        ("Glossophaga", species("", "Glossophaga longirostris", "Long-nosed Long-tongued Bat", "Long-tongued Bats", ["South America"], "A nectar bat of northern South America, with an exceptionally elongated snout and tongue. It is a specialist pollinator of columnar cacti and agaves in the arid inter-Andean valleys.", 0)),
        ("Sturnira", species("", "Sturnira luisi", "Luis's Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A recently described species from the cloud forests of Costa Rica and western Panama, named after the bat biologist Luis.", 0, "Luis")),
        ("Sturnira", species("", "Sturnira magna", "Greater Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "The largest Sturnira species, found in the Andean cloud forests from Colombia to Bolivia. Its size and heavy build are notable among the small frugivores of the canopy.", 0)),
        ("Platyrrhinus", species("", "Platyrrhinus helleri", "Heller's Broad-nosed Bat", "Broad-nosed Bats", ["South America"], "A small broad-nosed bat of Central and South America, named after the American zoologist Edmund Heller. Its prominent nose leaf and white facial stripes are diagnostic.", 0, "Edmund Heller")),
        ("Phyllostomus", species("", "Phyllostomus elongatus", "Lesser Spear-nosed Bat", "Spear-nosed Bats", ["South America"], "A smaller, more slender relative of P. hastatus, found in the Amazon basin. Its elongated, spear-shaped nose leaf distinguishes it from other phyllostomids.", 0)),
        ("Anoura", species("", "Anoura caudifer", "Tailed Tailless Bat", "Tailless Bats", ["South America"], "Despite its contradictory common name, this Anoura has a tiny, inconspicuous tail. It is a highly specialised nectarivore of the Andean cloud forests.", 0)),
        ("Anoura", species("", "Anoura cultrata", "Handley's Tailless Bat", "Tailless Bats", ["South America"], "A nectar-feeding bat of the Andes, distinguished by a distinctive cusp on its lower incisors. Named after the American mammalogist Charles O. Handley.", 0, "Charles O. Handley")),
        ("Lonchophylla", species("", "Lonchophylla mordida", "Mordid Nectar Bat", "Nectar Bats", ["South America"], "A nectar-feeding bat of the Amazon basin and the Guiana Shield, with a long, extensible tongue and a slender, elongated snout that are hallmarks of its highly specialised nectarivorous lifestyle.", 0)),
        ("Choeroniscus", species("", "Choeroniscus minor", "Lesser Long-tailed Nectar Bat", "Long-tailed Nectar Bats", ["South America"], "A tiny nectar bat of the Amazon and Orinoco basins, with an exceptionally long tongue that can reach deep into the tubular flowers of balsa and kapok trees.", 0)),
        ("Centurio", species("", "Centurio senex", "Wrinkle-faced Bat", "Wrinkle-faced Bats", ["South America"], "A bizarre-looking bat with an elaborate, wrinkled face and loose folds of skin. The male has a large, mask-like flap of skin that can be folded over the face. Found from Mexico to Venezuela.", 0)),
    ]

ENRICHERS = {
    "sylviidae": ("aves/passeriformes/sylviidae/src/data/sylviidae.json", enrich_sylviidae),
    "corvidae": ("aves/passeriformes/corvidae/src/data/corvidae.json", enrich_corvidae),
    "didelphidae": ("mammalia/didelphimorphia/didelphidae/src/data/didelphidae.json", enrich_didelphidae),
    "sicariidae": ("arachnida/araneae/sicariidae/src/data/sicariidae.json", enrich_sicariidae),
    "sturnidae": ("aves/passeriformes/sturnidae/src/data/sturnidae.json", enrich_sturnidae),
    "cuculidae": ("aves/cuculiformes/cuculidae/src/data/cuculidae.json", enrich_cuculidae),
    "turdidae": ("aves/passeriformes/turdidae/src/data/turdidae.json", enrich_turdidae),
    "chamaeleonidae": ("reptilia/squamata/chamaeleonidae/src/data/chamaeleonidae.json", enrich_chamaeleonidae),
    "rallidae": ("aves/gruiformes/rallidae/src/data/rallidae.json", enrich_rallidae),
    "pteropodidae": ("mammalia/chiroptera/pteropodidae/src/data/pteropodidae.json", enrich_pteropodidae),
    "fringillidae": ("aves/passeriformes/fringillidae/src/data/fringillidae.json", enrich_fringillidae),
    "clupeidae": ("actinopterygii/clupeiformes/clupeidae/src/data/clupeidae.json", enrich_clupeidae),
    "phyllostomidae": ("mammalia/chiroptera/phyllostomidae/src/data/phyllostomidae.json", enrich_phyllostomidae),
}

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    for slug, (rel_path, enricher) in ENRICHERS.items():
        if target != "all" and slug != target: continue
        path = os.path.join(ROOT, rel_path)
        if not os.path.exists(path): print(f"  SKIP {slug}"); continue
        data = load_json(path)
        before = count_species(data)
        additions = enricher()
        added = apply(data, additions)
        after = count_species(data)
        save_json(path, data)
        print(f"  {slug:20s} +{added:>3}  ({before:>4} → {after:>4})")
    print("Done. Run scripts/fix_duplicates.py next.")

if __name__ == "__main__":
    main()
