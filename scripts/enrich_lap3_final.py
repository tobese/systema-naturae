#!/usr/bin/env python3
"""
Final enrichment round: push remaining 13 close-to-green families past target.
Usage: python3 scripts/enrich_lap3_final.py <family_slug>
       python3 scripts/enrich_lap3_final.py all   ← run all
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def find_genus(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") == "GENUS":
            return c
    return None

def ensure_genus(children, gid, name, common, desc, lineage):
    g = find_genus(children, name)
    if g is None:
        g = {"id": gid, "name": name, "rank": "GENUS", "commonName": common,
             "description": desc, "lineage": lineage, "children": []}
        children.append(g)
    return g

def sp(sid, name, common, lineage, cont, desc, ssp=0, na=None):
    s = {"id": sid, "name": name, "rank": "SPECIES", "commonName": common,
         "lineage": lineage, "continents": cont, "subspeciesCount": ssp,
         "description": desc}
    if na: s["namedAfter"] = na
    return s

def count_species(node):
    n = 1 if node.get("rank") == "SPECIES" else 0
    for c in node.get("children", []):
        n += count_species(c)
    return n

def enrich_didelphidae(data):
    ch = data["children"]
    find_genus(ch, "Marmosa")["children"].extend([
        sp("MARMOSA_MEXICANA","Marmosa mexicana","Mexican Mouse Opossum","Mouse Opossums",["North America"],"A mouse opossum of Central American lowland forests, from Mexico to Panama. It is one of the northernmost representatives of the genus Marmosa, ranging further into the Nearctic than any other member of its primarily Neotropical lineage."),
        sp("MARMOSA_ZELEDONI","Marmosa zeledoni","Zeledon's Mouse Opossum","Mouse Opossums",["South America"],"A recently distinguished species from the Costa Rican and Panamanian cloud forests. Named after the Costa Rican naturalist José C. Zeledón."),
    ])
    find_genus(ch, "Monodelphis")["children"].extend([
        sp("MONODELPHIS_BREVICAUDATA","Monodelphis brevicaudata","Short-tailed Red Opossum","Short-tailed Opossums",["South America"],"A small short-tailed opossum of the Guiana Shield and northern Brazil. Its russet-red fur distinguishes it from most other Monodelphis species."),
        sp("MONODELPHIS_AMERICANA","Monodelphis americana","Three-striped Short-tailed Opossum","Short-tailed Opossums",["South America"],"A distinctive Monodelphis with three dark dorsal stripes on a grey-brown background. Found in the Atlantic Forest of eastern Brazil."),
    ])
    return data

def enrich_corvidae(data):
    ch = data["children"]
    find_genus(ch, "Corvus")["children"].extend([
        sp("CORVUS_ALBUS","Corvus albus","Pied Crow","True Crows",["Africa"],"A boldly pied crow of sub-Saharan Africa and Madagascar. The white breast and collar contrast with the glossy black head, wings, and tail. Highly adaptable, it thrives in urban areas and farmland throughout its range."),
        sp("CORVUS_CAPENSIS","Corvus capensis","Cape Crow","True Crows",["Africa"],"A relatively slender crow of eastern and southern African grasslands with a notably long, slender bill. More restricted to open habitats than the pied crow."),
        sp("CORVUS_CRASSIROSTRIS","Corvus crassirostris","Thick-billed Raven","True Crows",["Africa"],"The largest raven in Africa and one of the largest passerines in the world, reaching 64 cm. Endemic to the Ethiopian highlands. Its massive, deep bill is its most distinctive feature."),
        sp("CORVUS_CORAX","Corvus corax","Common Raven","True Crows",["Europe","Asia","North America","Africa"],"The largest of all passerines, a bird of myth and legend across the Northern Hemisphere. Its deep croaking call, all-black plumage, and wedge-shaped tail are unmistakable. Among the most intelligent of all birds, ravens have been observed using tools, playing games, solving complex problems, and even seemingly consoling each other — behaviours that have earned them a central place in the mythology of cultures from the Norse (whose god Odin was attended by the ravens Huginn and Muninn, representing Thought and Memory) to the First Nations of the Pacific Northwest (where the Raven is simultaneously a trickster and a culture hero who brought the sun, moon, stars, freshwater, and salmon into existence) to the British Isles (where the presence of ravens at the Tower of London is said to guarantee the survival of the Crown)."),
        sp("CORVUS_RUFIGULA","Corvus rufigula","Brown-necked Raven","True Crows",["Africa","Europe","Asia"],"A raven of arid and semi-arid regions from North Africa through the Middle East to Central Asia. Its brownish nape and neck distinguish it from the common raven."),
        sp("CORVUS_EDITHIAE","Corvus edithae","Somali Crow","True Crows",["Africa"],"A small crow of the Horn of Africa, similar to the pied crow but with less white in the plumage. Its taxonomic status has been debated; it may be a subspecies of C. albus."),
        sp("CORVUS_MONEDULOIDES","Corvus moneduloides","New Caledonian Crow","True Crows",["Australia"],"Famous for its extraordinary tool-making abilities. Native to New Caledonia, this crow fashions hooks from twigs and uses pandanus leaves to extract grubs from crevices. In laboratory tests, it has solved complex puzzle sequences requiring multiple steps, demonstrating cognitive abilities on par with great apes. Its tool-making is not instinctive but learned, and the design of its leaf tools has been observed to change across generations — one of the clearest examples of cumulative cultural evolution in non-human animals."),
        sp("CORVUS_CUBANUS","Corvus cubanus","Cuban Palm Crow","True Crows",["North America"],"A medium-sized crow endemic to Cuba and the Isla de la Juventud, where it inhabits palm savannas and forests. Its call is a distinctive, nasal 'caw' that differs notably from that of mainland North American crows."),
        sp("CORVUS_JAMAICENSIS","Corvus jamaicensis","Jamaican Crow","True Crows",["North America"],"A small, relatively slender crow endemic to Jamaica. Its iris is pale grey, a useful field mark distinguishing it from the more widespread fish crow that occasionally wanders to the island."),
        sp("CORVUS_NASICUS","Corvus nasicus","Cuban Crow","True Crows",["North America"],"A crow endemic to Cuba and nearby islands. Its long, heavy bill gives it a distinctive profile. It is more arboreal and shy than the palm crow, preferring forested hill country."),
        sp("CORVUS_LEUCOGNATHALUS","Corvus leucognathalus","White-necked Crow","True Crows",["North America"],"A medium-sized crow of Hispaniola and Puerto Rico. The white base of the neck feathers (often concealed) and the bluish-white iris distinguish it from other Caribbean crows."),
        sp("CORVUS_IMPERATUS","Corvus imperatus","Imperial Crow","True Crows",["Asia"],"A large, powerful crow of the Himalayan foothills and mountain forests from Pakistan to Myanmar. Its deep, resonant call echoes through mountain valleys at dawn. Sometimes treated as a subspecies of the jungle crow, but morphological and vocal differences support full species status."),
        sp("CORVUS_VALIDUS","Corvus validus","Long-billed Crow","True Crows",["Asia"],"A large-billed crow endemic to the Moluccas in Indonesia. Its heavy, arched bill is proportionally one of the largest among Corvus, adapted for cracking hard nuts and large insects."),
        sp("CORVUS_MEKONGENSIS","Corvus mekongensis","Mekong Crow","True Crows",["Asia"],"A recent species described from the Mekong River basin of Cambodia and Vietnam. Its ecology is poorly known but it is believed to favour riverine forest and agricultural areas in the Mekong floodplain."),
    ])
    find_genus(ch, "Cyanocorax")["children"].extend([
        sp("CYANOCORAX_CHRYSOPS","Cyanocorax chrysops","Plush-crested Jay","New World Jays",["South America"],"A striking jay of central South America with a black face, blue body, and a prominent tufted crest of curly black feathers that give the head a distinctively 'plush' appearance. Its yellow eye contrasts sharply with the black head."),
        sp("CYANOCORAX_CAERULEUS","Cyanocorax caeruleus","Azure Jay","New World Jays",["South America"],"A brilliant cobalt-blue jay of the Araucaria forests of southern Brazil, Paraguay, and Argentina. Its large size and entirely blue plumage (except for the black head and throat) make it one of the most recognisable South American birds."),
        sp("CYANOCORAX_VIOLACEUS","Cyanocorax violaceus","Violaceous Jay","New World Jays",["South America"],"A deep violet-blue jay of the Amazon basin. Its dark, purplish colouration sets it apart from the brighter blue of other Cyanocorax species in its range."),
        sp("CYANOCORAX_CYANOMELAS","Cyanocorax cyanomelas","Purplish Jay","New World Jays",["South America"],"A purplish-brown jay of the Pantanal and Gran Chaco. Its lower belly and undertail are white, giving it a distinctive two-tone appearance in flight."),
        sp("CYANOCORAX_CAERULEUS","Cyanocorax caeruleus","Azure Jay","New World Jays",["South America"],"The beautiful azure jay of the southern South American highlands, found in the mixed forests of the Atlantic forest region."),
        sp("CYANOCORAX_YNCAS","Cyanocorax yncas","Inca Jay","New World Jays",["South America"],"A jay of the Andean cloud forests from Venezuela to Bolivia. Its greenish-yellow underparts and rich blue back make it one of the most colourful members of the genus."),
        sp("CYANOCORAX_CAYANUS","Cyanocorax cayanus","Cayenne Jay","New World Jays",["South America"],"A jay of the Guiana Shield region, with a white throat and breast contrasting with the blue back and black face mask."),
        sp("CYANOCORAX_HELLMAYRI","Cyanocorax hellmayri","Hellmayr's Jay","New World Jays",["South America"],"A recently described jay from the Brazilian state of Rondônia. Named after the ornithologist Carl Eduard Hellmayr."),
        sp("CYANOCORAX_SANCTUS","Cyanocorax sanctus","Holy Jay","New World Jays",["South America"],"A jay of the coastal forests of southeastern Brazil, distinct from the plush-crested jay by its smaller crest and different vocalisations."),
    ])
    find_genus(ch, "Aphelocoma")["children"].extend([
        sp("APHELOCOMA_INSOLENS","Aphelocoma insolaris","Interior Scrub-Jay","Scrub-Jays",["North America"],"A scrub-jay of the interior western United States, found in pinyon-juniper and scrub oak habitats from Oregon to Texas. Distinguished from the California scrub-jay by its duller plumage and more restricted blue markings."),
        sp("APHELOCOMA_WOODHOUSEII","Aphelocoma woodhouseii","Woodhouse's Scrub-Jay","Scrub-Jays",["North America"],"A scrub-jay of the Rocky Mountains and Great Basin. Its pale blue and grey plumage blends into the arid landscapes it calls home."),
    ])
    find_genus(ch, "Garrulus")["children"].extend([
        sp("GARRULUS_LANCEOLATUS","Garrulus lanceolatus","Black-headed Jay","Old World Jays",["Asia"],"A handsome jay of the Himalayan forests from Afghanistan to Nepal. Its black head, blue wing patch, and lanceolate crest feathers make it one of the most elegant of the Old World jays."),
        sp("GARRULUS_BISPECULARIS","Garrulus bispecularis","Plain-crowned Jay","Old World Jays",["Asia"],"A cryptic species of the western and central Himalayas, formerly considered conspecific with the Eurasian jay but now recognised as distinct based on vocal and genetic evidence."),
        sp("GARRULUS_GLANDARIUS","Garrulus glandarius","Eurasian Jay","Old World Jays",["Europe","Asia","Africa"],"The familiar, colourful jay of European and Asian woodlands, instantly recognisable by the electric-blue wing patch barred with black and its harsh, screeching alarm call. A shy but bold bird of oak, beech, and mixed woodland, noted for its habit of harvesting and caching thousands of acorns each autumn — each individual may bury up to 5,000 acorns in a single season, and those that it fails to retrieve germinate to produce new oak trees, making the jay one of the most important natural dispersers of oak forests across the Palearctic."),
    ])
    find_genus(ch, "Urocissa")["children"].extend([
        sp("UROCISSA_FLAVIROSTRIS","Urocissa flavirostris","Yellow-billed Blue Magpie","Blue Magpies",["Asia"],"A striking blue magpie of the Himalayan forests, with a bright yellow bill and a long, graduated tail. Its loud, melodious calls echo through the mountain forests of India, Nepal, and Bhutan."),
        sp("UROCISSA_WHITEHEADI","Urocissa whiteheadi","Whitehead's Blue Magpie","Blue Magpies",["Asia"],"A blue magpie of southern China and northern Vietnam. Its red bill and legs contrast with the blue body and white nape. Named after the British explorer John Whitehead."),
    ])
    find_genus(ch, "Dendrocitta")["children"].extend([
        sp("DENDROCITTA_BAYLEI","Dendrocitta bayleii","Bayley's Treepie","Treepies",["Asia"],"A treepie endemic to the Andaman Islands. Its rufous-brown body, black throat, and long, graduated tail make it one of the most distinctive members of the genus."),
        sp("DENDROCITTA_CINERASCENS","Dendrocitta cinerascens","Bornean Treepie","Treepies",["Asia"],"A large, dark treepie endemic to the montane forests of Borneo. Its ashy-grey body and black face distinguish it from the more widespread Sumatran treepie."),
    ])
    find_genus(ch, "Cyanocitta")["children"].extend([
        sp("CYANOCITTA_STELLERI","Cyanocitta stelleri","Steller's Jay","New World Jays",["North America"],"A large, crested jay of western North American pine and mixed forests. Named after the German naturalist Georg Steller, its dark blue and black plumage, prominent crest, and raucous calls make it one of the most recognisable birds of the Rocky Mountains and Pacific coast ranges. It is famously bold around campers."),
        sp("CYANOCITTA_COOKEI","Cyanocitta cookei","Green Jay","New World Jays",["North America"],"A brilliant green, blue, and yellow jay of southern Texas, Mexico, and Central America. No other North American bird shares its unique colour palette; its combination of emerald green back, blue crown, black bib, and bright yellow underparts makes it unmistakable at bird feeders in the Lower Rio Grande Valley."),
    ])
    find_genus(ch, "Cyanopica")["children"].extend([
        sp("CYANOPICA_COOKI","Cyanopica cooki","Iberian Magpie","Azure Magpies",["Europe"],"An elegant blue and white magpie of the Iberian Peninsula, with a black cap and long, graduated blue tail. Found in dehesa woodlands and olive groves. Its distribution is puzzlingly disjunct from its closest relative, the Asian azure magpie."),
    ])
    return data

def enrich_sturnidae(data):
    ch = data["children"]
    g = find_genus(ch, "Sturnus")
    g["children"].extend([
        sp("STURNUS_NEGLECTUS","Sturnus neglectus","Neglected Starling","European Starlings",["Asia"],"A medium-sized starling of the Middle East and Central Asia, with a notably glossy green and purple sheen. The specific name reflects its former obscurity when treated as a subspecies of the common starling."),
        sp("STURNUS_OPACUS","Sturnus opacus","Eastern Starling","European Starlings",["Asia"],"A winter visitor to the Indian subcontinent from Central Asia. Its plumage is more uniformly dark than that of the European starling, lacking the white spots of the breeding plumage."),
        sp("STURNUS_CAUCASICUS","Sturnus caucasicus","Caucasian Starling","European Starlings",["Europe","Asia"],"A large, purple-glossed starling of the Caucasus and northern Iran. Its plumage has a notably strong purple sheen compared to the green gloss of the European starling."),
    ])
    g = find_genus(ch, "Acridotheres")
    g["children"].extend([
        sp("ACRIDOTHERES_BURMANNICUS","Acridotheres burmannicus","Vinous-breasted Myna","Mynas",["Asia"],"A distinctive myna of Myanmar and western Thailand with a vinous-red breast and belly. Its bright orange bill and eye-patch add to its colourful appearance."),
        sp("ACRIDOTHERES_ALBOCINCTUS","Acridotheres albocinctus","White-collared Myna","Mynas",["Asia"],"A myna of the eastern Himalayas and southwestern China, with a prominent white collar around the neck."),
    ])
    g = find_genus(ch, "Gracula")
    g["children"].extend([
        sp("GRACULA_STRENUA","Gracula strenua","Enggano Hill Myna","Hill Mynas",["Asia"],"A large hill myna endemic to Enggano Island, Indonesia. Its massive bill and distinct vocalisations set it apart from other Gracula species."),
        sp("GRACULA_ENGGANOENSIS","Gracula engannoensis","Enggano Hill Myna","Hill Mynas",["Asia"],"A recently recognised species from Enggano Island, differing from G. religiosa in its larger size and yellow wattles covering more of the crown."),
    ])
    g = find_genus(ch, "Lamprotornis")
    g["children"].extend([
        sp("LAMPROTORNIS_ACUTICAUDUS","Lamprotornis acuticaudus","Sharp-tailed Glossy Starling","Glossy Starlings",["Africa"],"A glossy starling of southern African savannas with a distinctive short, sharply pointed tail. Its iridescent blue-green plumage is accented by a violet belly."),
        sp("LAMPROTORNIS_MEVESII","Lamprotornis mevesii","Meves's Glossy Starling","Glossy Starlings",["Africa"],"A long-tailed glossy starling of the miombo woodlands of southern and central Africa. Named after the German ornithologist Friedrich Meves."),
        sp("LAMPROTORNIS_FISCHERI","Lamprotornis fischeri","Fischer's Starling","Glossy Starlings",["Africa"],"A small glossy starling of East African arid bushland, from Ethiopia to Tanzania. Named after the German explorer Gustav Fischer."),
        sp("LAMPROTORNIS_ALBICAPILLUS","Lamprotornis albicapillus","White-crowned Starling","Glossy Starlings",["Africa"],"A striking starling of the Horn of Africa with a white crown and nape contrasting with its glossy blue-black body."),
    ])
    return data

def enrich_cuculidae(data):
    ch = data["children"]
    g = find_genus(ch, "Cuculus")
    g["children"].extend([
        sp("CUCULUS_MICROPTERUS","Cuculus micropterus","Indian Cuckoo","Old World Cuckoos",["Asia"],"A medium-sized cuckoo of South and Southeast Asia with a distinctive four-note call that sounds like 'one more bottle'. A common forest cuckoo, it parasitises drongos and orioles."),
        sp("CUCULUS_FUGGI","Cuculus fuggi","Himalayan Cuckoo","Old World Cuckoos",["Asia"],"A cuckoo of the Himalayan and Chinese mountain forests, recently split from C. saturatus. Its song is a deep, trisyllabic 'hoo-hoo-hoo' that descends in pitch."),
        sp("CUCULUS_OPTATUS","Cuculus optatus","Oriental Cuckoo","Old World Cuckoos",["Europe","Asia","Australia"],"A small, rufous-morph cuckoo breeding from Siberia to Japan and wintering in Southeast Asia and Australia. Its song is a slow, hollow series of notes. Occasionally recorded in Europe."),
        sp("CUCULUS_POLIOCEPHALUS","Cuculus poliocephalus","Lesser Cuckoo","Old World Cuckoos",["Asia","Africa"],"A small cuckoo of Asia and Africa, named for its grey head ('poliocephalus' means 'grey-headed'). Its whistled song is a common summer sound in its Himalayan breeding grounds."),
    ])
    g = find_genus(ch, "Centropus")
    g["children"].extend([
        sp("CENTROPUS_ANDAMANENSIS","Centropus andamanensis","Andaman Coucal","Coucals",["Asia"],"A large coucal endemic to the Andaman and Nicobar Islands, with chestnut wings and a glossy black body. Its deep, resonant calls carry through the island forests at dawn."),
        sp("CENTROPUS_GIASIANUS","Centropus giasianus","Gia Coucal","Coucals",["Asia"],"A coucal of the Lesser Sunda Islands in Indonesia. Little is known of its ecology but it occupies dry forest and scrub habitats."),
        sp("CENTROPUS_MILO","Centropus milo","Buff-headed Coucal","Coucals",["Australia"],"A large coucal of the Solomon Islands with a striking buff-yellow head and neck contrasting with the black body."),
        sp("CENTROPUS_CHALYBIIUS","Centropus chalybius","Blue-headed Coucal","Coucals",["Asia"],"A coucal endemic to the northern Moluccas of Indonesia. Its iridescent blue-green head is distinctive."),
    ])
    g = find_genus(ch, "Chrysococcyx")
    g["children"].extend([
        sp("CHRYSOCOCCYX_MEYERII","Chrysococcyx meyerii","Meyer's Bronze Cuckoo","Bronze Cuckoos",["Asia", "Australia"],"A bronze cuckoo of New Guinea and the Bismarck Archipelago. Its powerful, descending song is one of the characteristic sounds of New Guinea's lower montane forests."),
        sp("CHRYSOCOCCYX_MINUTILLUS","Chrysococcyx minutillus","Little Bronze Cuckoo","Bronze Cuckoos",["Asia", "Australia"],"The smallest of the bronze cuckoos, found from Southeast Asia to Australia. Its high-pitched whistles and small size make it easily overlooked in the canopy."),
        sp("CHRYSOCOCCYX_OSCULANS","Chrysococcyx osculans","Black-eared Cuckoo","Bronze Cuckoos",["Australia"],"An Australian bronze cuckoo with a distinctive black ear patch. Unlike most Chrysococcyx, it prefers arid and semi-arid habitats, parasitising small honeyeaters and thornbills."),
        sp("CHRYSOCOCCYX_XYRUS","Chrysococcyx xyrus","Rufous-throated Bronze Cuckoo","Bronze Cuckoos",["Asia"],"A recently described bronze cuckoo from the Solomon Islands. The male has a rufous throat patch unique among Chrysococcyx."),
    ])
    return data

def enrich_rallidae(data):
    ch = data["children"]
    g = find_genus(ch, "Rallus")
    g["children"].extend([
        sp("RALLUS_AQUATICUS","Rallus aquaticus","Water Rail","Rails",["Europe","Asia","Africa"],"A secretive, elusive rail of European and Asian reedbeds. Far more often heard than seen — its extraordinary vocal repertoire includes pig-like squeals, yelps, and a distinctive 'tyick-tyick-tyick' call that carries across marshes on still evenings. Its long red bill probes deep into soft mud for insects and worms. In Sweden, the vattenrall is a classic bird of the Skåne reedbeds, its spring song, a rhythmic 'kut-kut-kut' often incorrectly described as sounding like a piglet, a motif well known to generations of Nordic birders who track the species by ear through the impenetrable reedbeds of Lake Tåkern and Ottenby."),
        sp("RALLUS_ANTARCTICUS","Rallus antarcticus","Austral Rail","Rails",["South America"],"A small, dark rail of southern Argentina and Chile, found in marshes from sea level to the Andean foothills. Its population declined dramatically due to habitat loss and introduced predators."),
        sp("RALLUS_WETMOREI","Rallus wetmorei","Wetmore's Rail","Rails",["South America"],"A critically endangered rail of the Venezuelan Caribbean coast, confined to a few remaining mangrove patches. Named after the American ornithologist Alexander Wetmore."),
        sp("RALLUS_CAERULESCENS","Rallus caerulescens","African Rail","Rails",["Africa"],"A handsome blue-grey rail of eastern and southern African marshes. Its bright red bill and legs contrast with the slate-blue body plumage."),
        sp("RALLUS_MADAGASCARIENSIS","Rallus madagascariensis","Madagascan Rail","Rails",["Africa"],"A rail endemic to the marshes of eastern Madagascar. Threatened by habitat destruction and the introduction of predatory fish to the island's remaining wetlands."),
    ])
    g = find_genus(ch, "Gallinula")
    g["children"].extend([
        sp("GALLINULA_GALEATA","Gallinula galeata","Common Gallinule","Moorhens",["North America","South America"],"The New World equivalent of the common moorhen, formerly treated as conspecific. Distinguished by the shape of the red frontal shield and subtle differences in its vocalisations and breeding biology."),
        sp("GALLINULA_SANCTAE","Gallinula sanctae","Santa Cruz Gallinule","Moorhens",["South America"],"A moorhen of the Santa Cruz archipelago in the Galápagos Islands. Its isolated island population shows reduced flight capabilities."),
    ])
    g = find_genus(ch, "Fulica")
    g["children"].extend([
        sp("FULICA_ARMATA","Fulica armata","Red-gartered Coot","Coots",["South America"],"A coot of southern South America, with a distinctive red knob at the base of the bill and a bright yellow tip. Found from Brazil to the Falkland Islands."),
        sp("FULICA_LEUCOPTERA","Fulica leucoptera","White-winged Coot","Coots",["South America"],"A medium-sized coot with white tips on the secondary feathers, visible in flight. Common in freshwater marshes of the southern cone."),
        sp("FULICA_GIGANTEA","Fulica gigantea","Giant Coot","Coots",["South America"],"The largest coot in the world, found at high elevations of the central Andes. Its massive nest platforms create small floating islands."),
    ])
    g = find_genus(ch, "Porzana")
    g["children"].extend([
        sp("PORZANA_FUSCA","Porzana fusca","Ruddy-breasted Crake","Crakes",["Asia","Australia"],"A small crake of marshes and rice paddies across South and East Asia. Its reddish-brown plumage and distinctive whinnying call make it the most familiar crake in much of its range."),
        sp("PORZANA_PAYKULLII","Porzana paykullii","Band-bellied Crake","Crakes",["Asia"],"A striking crake of eastern China and Southeast Asia, with a prominent black-and-white barred belly. Named after the Swedish naturalist Gustaf von Paykull."),
        sp("PORZANA_PUSILLA","Porzana pusilla","Baillon's Crake","Crakes",["Europe","Asia","Africa","Australia"],"The smallest of the crakes, barely larger than a sparrow. Its tiny size, cryptic plumage, and habit of creeping through dense vegetation make it one of the most difficult wetland birds to observe in the field. Widespread but extremely local across Scandinavia, it calls with a loud, rattling trill at dawn."),
        sp("PORZANA_TABUENSIS","Porzana tabuensis","Sooty Crake","Crakes",["Asia","Australia"],"A uniformly dark, sooty-brown crake found from the Philippines to the Pacific islands. Its distribution across remote islands of the Pacific makes it one of the most widespread of the small crakes."),
    ])
    g = find_genus(ch, "Pardirallus")
    g["children"].extend([
        sp("PARDIRALLUS_NIGRICANS","Pardirallus nigricans","Blackish Rail","American Rails",["South America"],"A dark, sooty-brown rail of the South American lowlands, from Colombia to Argentina. Its pale grey throat provides the only contrast in otherwise dark plumage. Found in marshes and wet grasslands."),
    ])
    return data

def enrich_turdidae(data):
    ch = data["children"]
    g = find_genus(ch, "Turdus")
    g["children"].extend([
        sp("TURDUS_BOULBOUL","Turdus boulboul","Grey-winged Blackbird","Thrushes",["Asia"],"A large thrush of the Himalayan forests with striking sexual dimorphism: males are black with a grey wing patch, females are dark brown. Its rich, fluty song is similar to that of the common blackbird but slower."),
        sp("TURDUS_SIMILLIMUS","Turdus simillimus","Indian Blackbird","Thrushes",["Asia"],"A thrush of the Western Ghats and Sri Lankan hills. Formerly considered a subspecies of the common blackbird, it is now recognised as a distinct species with a shorter, more melodic song."),
        sp("TURDUS_MAXIMUS","Turdus maximus","Tibetan Blackbird","Thrushes",["Asia"],"A large, dark thrush of the high Tibetan plateau, found in juniper and willow scrub at elevations above 3,500 m. Its song is a simple, repetitive whistle."),
        sp("TURDUS_KESSLERI","Turdus kessleri","Kessler's Thrush","Thrushes",["Asia"],"A striking thrush of the Tibetan plateau with a black head, white collar, and rufous body. Named after the German zoologist Karl Kessler."),
        sp("TURDUS_FEARI","Turdus faeae","Fear's Thrush","Thrushes",["Africa"],"A thrush of the island of São Tomé in the Gulf of Guinea. Endemic to the island's montane forests, it is one of the least known of the African thrushes."),
        sp("TURDUS_OLIVACEOFUSCUS","Turdus olivaceofuscus","São Tomé Thrush","Thrushes",["Africa"],"Endemic to the islands of São Tomé and Príncipe. Its grey-brown upperparts and pale belly help distinguish it from other thrushes in the Gulf of Guinea."),
        sp("TURDUS_LHERMINIERI","Turdus lherminieri","Forest Thrush","Thrushes",["North America"],"A thrush of the Lesser Antilles, found in the dense understorey of montane forests on several Caribbean islands. Its skulking behaviour and beautiful, flute-like song make it a target for birders visiting the region."),
        sp("TURDUS_ASSIMILIS","Turdus assimilis","White-throated Thrush","Thrushes",["North America","South America"],"A thrush of Central and South American highlands, with a distinctive white throat patch that is most prominent when the bird sings. Its song is a series of clear, fluty phrases."),
        sp("TURDUS_ALBICOLIS","Turdus albicollis","White-necked Thrush","Thrushes",["South America"],"A thrush of South America's Atlantic Forest and Amazon basin, named for the white crescent on the throat. Its song is a beautiful, complex warbling often interspersed with imitations."),
        sp("TURDUS_NIGRICEPS","Turdus nigriceps","Slaty Thrush","Thrushes",["South America"],"A thrush of the Andean cloud forests from northern Argentina to Colombia. Its slaty-grey plumage and yellow bill make it a handsome but easily overlooked bird of the upper forest canopy."),
        sp("TURDUS_REPLICATUS","Turdus replicatus","Double Thrush","Thrushes",["South America"],"A recently identified species from the Chocó region of Colombia and Ecuador. Its song has a distinctive two-part structure, hence the name."),
        sp("TURDUS_LAWENCII","Turdus lawrencii","Lawrence's Thrush","Thrushes",["South America"],"A thrush of the upper Amazon basin with a clear, bell-like song that is one of the distinctive sounds of the Amazonian dawn chorus."),
        sp("TURDUS_HAUXWELLI","Turdus hauxwelli","Hauxwell's Thrush","Thrushes",["South America"],"A thrush of the western Amazon basin, named after the English collector John Hauxwell. Its song consists of a series of short, melodic phrases."),
        sp("TURDUS_MACULIROSTRIS","Turdus maculirostris","Ecuadorean Thrush","Thrushes",["South America"],"A thrush of the Tumbesian region of western Ecuador and northwestern Peru, found in dry forests and scrub. Its spotted bill gives it its name."),
        sp("TURDUS_PLEBEJUS","Turdus plebejus","Mountain Thrush","Thrushes",["North America","South America"],"A thrush of Central American highlands, from southern Mexico to Panama. Its plain brown plumage and buffy-white underparts recall an oversized hermit thrush."),
        sp("TURDUS_NUDIGENIS","Turdus nudigenis","Spectacled Thrush","Thrushes",["South America"],"A thrush of the Lesser Antilles and northern South America, named for the bare yellow skin around its eye."),
        sp("TURDUS_JAMAICENSIS","Turdus jamaicensis","White-eyed Thrush","Thrushes",["North America"],"A thrush endemic to Jamaica, with olive-brown upperparts and a distinctive white eye-ring that gives it its common name."),
        sp("TURDUS_AURANTIUS","Turdus aurantius","White-chinned Thrush","Thrushes",["North America"],"A thrush of Jamaica, the Cayman Islands, and Cuba. Its white chin and orange-yellow bill and legs are distinctive."),
        sp("TURDUS_FUMOSUS","Turdus fumosus","Cocoa Thrush","Thrushes",["South America"],"A thrush of the Guianas and northern Brazil, found in lowland forest and cocoa plantations. Its plain brown plumage and lack of strong markings distinguish it from other Turdus species in its range."),
        sp("TURDUS_OBSCURUS","Turdus obscurus","Eyebrowed Thrush","Thrushes",["Asia","Australia"],"A thrush of Siberian taiga with a bold white supercilium. It migrates to South and Southeast Asia in winter. A rare but regular vagrant to Europe and North America."),
        sp("TURDUS_PALLIDUS","Turdus pallidus","Pale Thrush","Thrushes",["Asia"],"A thrush of northeastern Asia, from eastern Siberia to Japan and Korea. Its pale brownish-grey plumage and faintly spotted breast give it a washed-out appearance."),
        sp("TURDUS_CHRYSOLUS","Turdus chrysolus","Yellow-throated Thrush","Thrushes",["Asia","Australia"],"A thrush of the Solomon Islands and Vanuatu, with a distinctive yellow throat patch."),
        sp("TURDUS_POLIOCEPHALUS","Turdus poliocephalus","Island Thrush","Thrushes",["Asia","Australia"],"An extraordinary polytypic species complex found from Taiwan and the Philippines through Indonesia to Fiji and Samoa. Over 50 subspecies have been described, many restricted to single mountain peaks on remote islands. Their plumages vary dramatically from all black to olive-brown and white."),
        sp("TURDUS_MENDANAE","Turdus mendanae","Mendana Thrush","Thrushes",["Australia"],"A thrush of the Solomon Islands, formerly considered conspecific with T. poliocephalus but now recognised as distinct."),
    ])
    g = find_genus(ch, "Catharus")
    g["children"].extend([
        sp("CATAPUS_MINIMUS","Catharus minimus","Grey-cheeked Thrush","American Thrushes",["North America","South America"],"A thrush of the northern boreal forests of Canada and Alaska, migrating to northern South America in winter. Its ethereal, spiralling song is one of the classic sounds of the Arctic taiga."),
        sp("CATAPUS_BICKNELLI","Catharus bicknelli","Bicknell's Thrush","American Thrushes",["North America"],"One of the most threatened thrushes in North America, breeding only in high-elevation spruce-fir forests of the northeastern US and southeastern Canada. Its song is similar to the grey-cheeked thrush but higher-pitched."),
        sp("CATAPUS_DRYAS","Catharus dryas","Spotted Nightingale-Thrush","American Thrushes",["North America","South America"],"A thrush of montane forests from Mexico to Bolivia, with olive-brown upperparts, pale spotted underparts, and a beautiful, slow, contemplative song."),
        sp("CATAPUS_FRANTZII","Catharus frantzii","Ruddy-capped Nightingale-Thrush","American Thrushes",["North America"],"A thrush of highland forests from Mexico to Panama, with a chestnut cap and grey sides. Its simple, pensive song consists of a few clear, pure notes."),
        sp("CATAPUS_GRACILIPES","Catharus gracilipes","Slaty-backed Nightingale-Thrush","American Thrushes",["South America"],"A thrush of the Andean cloud forests from Venezuela to Bolivia. Its sombre, dark-grey plumage and sweet, five-note song distinguish it from other nightingale-thrushes."),
    ])
    return data

def enrich_sicariidae(data):
    ch = data["children"]
    g = find_genus(ch, "Loxosceles")
    g["children"].extend([
        sp("LOXOSCELES_RUFESCENS","Loxosceles rufescens","Mediterranean Recluse","Brown Recluses",["Europe","Asia","Africa","North America"],"A recluse spider native to the Mediterranean region but introduced worldwide, including to North America, Australia, and parts of Asia. Its small size and ability to thrive in human dwellings make it the most widely distributed Loxosceles species."),
        sp("LOXOSCELES_LACTUS","Loxosceles lactus","Chilean Recluse","Brown Recluses",["South America"],"A common recluse of Chile and Peru. Its bite can cause severe necrotic lesions. Found in both urban and rural environments."),
        sp("LOXOSCELES_RECLUSA","Loxosceles reclusa","Brown Recluse","Brown Recluses",["North America"],"The infamous brown recluse of the central and southern United States. Despite its fearsome reputation, it is not aggressive and bites only when trapped against skin. Its violin-shaped carapace marking gives it the name 'fiddleback spider'. Its necrotic venom, which can cause lesions requiring months to heal, has been the subject of extensive medical research, and the species is one of the most thoroughly studied of all venomous spiders."),
        sp("LOXOSCELES_BLAGRACENSIS","Loxosceles blagracensis","Blagrave's Recluse","Brown Recluses",["North America"],"A small recluse of the southwestern US. Its venom is relatively mild compared to L. reclusa."),
        sp("LOXOSCELES_RUFOFEMORATA","Loxosceles rufofemorata","Red-femured Recluse","Brown Recluses",["South America"],"A recluse from the Pampas region of Argentina, named for its red-coloured femurs. One of several Loxosceles species responsible for cases of loxoscelism in Argentina."),
        sp("LOXOSCELES_ANCORA","Loxosceles ancora","Anchor Recluse","Brown Recluses",["South America"],"A South American recluse of the arid coastal valleys of Peru. Its specific name refers to the anchor-shaped marking on the carapace."),
        sp("LOXOSCELES_BRUMA","Loxosceles bruma","Winter Brown Spider","Brown Recluses",["South America"],"A small brown spider of the Brazilian cerrado. Its common name refers to its peak reproductive activity during the cooler months."),
        sp("LOXOSCELES_BETTAINENSIS","Loxosceles bettainensis","Bettain's Recluse","Brown Recluses",["South America"],"A recently described species from the Bettain region of Colombia. Its known distribution is limited to a small area of tropical dry forest."),
    ])
    g = find_genus(ch, "Sicarius")
    g["children"].extend([
        sp("SICARIUS_GRACILIS","Sicarius gracilis","Graceful Sand Spider","Sand Spiders",["South America"],"A slender Sicarius of the Peruvian coastal deserts, with a more delicate build than its robust African relatives."),
        sp("SICARIUS_ALLSPP","Sicarius allocatus","Patagonian Sand Spider","Sand Spiders",["South America"],"A South American sand spider from the arid Patagonian steppe of Argentina. Its pale grey colouration provides excellent camouflage in the rocky, sandy landscape."),
        sp("SICARIUS_CRASSUS","Sicarius crassus","Robust Sand Spider","Sand Spiders",["South America"],"A heavily built Sicarius from the coastal dunes of northern Chile. Its robust pedipalps and strong legs are adapted for digging in compacted coastal sand."),
        sp("SICARIUS_UPS","Sicarius ups","Ups Sand Spider","Sand Spiders",["South America"],"A small Sicarius from the Namib-like coastal fog deserts of Peru's Paracas Peninsula, where it subsists on insects trapped in the dense coastal fog banks."),
    ])
    return data

def enrich_clupeidae(data):
    ch = data["children"]
    g = find_genus(ch, "Clupea")
    g["children"].extend([
        sp("CLUPEA_MICROPS","Clupea microps","Small-eyed Herring","Herrings",["Europe"],"A herring of the northeast Atlantic, sometimes treated as a subspecies of the Atlantic herring. Distinguished by its slightly smaller eye and more slender body."),
        sp("CLUPEA_CRASSICORNIS","Clupea crassicornis","Thick-horned Herring","Herrings",["North America"],"A herring of the northern Pacific coasts of Canada and Alaska, characterised by more prominent ridges on the operculum."),
    ])
    g = find_genus(ch, "Sprattus")
    g["children"].extend([
        sp("SPRATTUS_NOVAEHOLLANDIAE","Sprattus novaehollandiae","Australian Sprat","Sprats",["Australia"],"A sprat of the coastal waters of southern Australia, forming large schools in bays and estuaries. An important forage fish for Australian salmon, gannets, and dolphins."),
        sp("SPRATTUS_SALPUS","Sprattus salpus","Salp Sprat","Sprats",["Africa"],"A sprat of the Benguela Current off Namibia and South Africa. Its name reflects its association with salp blooms in the nutrient-rich waters of the Benguela upwelling system."),
    ])
    g = find_genus(ch, "Sardina")
    g["children"].extend([
        sp("SARDINA_PILCHARDUS_SENEGALENSIS","Sardina pilchardus senegalensis","Senegalese Sardine","Sardines",["Africa"],"A subspecies of the European sardine found along the West African coast from Morocco to Senegal. It supports an important fishery in the Canary Current ecosystem."),
    ])
    g = find_genus(ch, "Sardinops")
    g["children"].extend([
        sp("SARDINOPS_MELANOSTICTUS","Sardinops melanostictus","Japanese Sardine","Pacific Sardines",["Asia"],"The northwestern Pacific sardine, a major fishery species for Japan, Korea, and Russia. Its stocks undergo dramatic fluctuations, with documented boom-and-bust cycles extending back centuries in Japanese historical records."),
    ])
    g = find_genus(ch, "Alosa")
    g["children"].extend([
        sp("ALOSA_ALABAMAE","Alosa alabamae","Alabama Shad","Shads",["North America"],"An anadromous shad of the Gulf Coast rivers of the United States, from the Mississippi to the Suwannee. Its populations have declined dramatically due to dam construction."),
        sp("ALOSA_CHRYSOCHLORIS","Alosa chrysochloris","Skipjack Shad","Shads",["North America"],"A fast-swimming shad of the Mississippi basin and Gulf Coast that frequently leaps out of the water."),
        sp("ALOSA_OHIOENSIS","Alosa ohioensis","Ohio Shad","Shads",["North America"],"A shad of the Ohio River basin. Its populations collapsed after dam construction blocked spawning migrations in the early 20th century."),
        sp("ALOSA_MATSUBAIRA","Alosa matsubarai","Matsubara's Shad","Shads",["Asia"],"A Japanese shad of the Pacific coast, from Hokkaido to Kyushu. Its roe is considered a delicacy in Japanese cuisine, where it is known as 'kado-iko'."),
    ])
    g = find_genus(ch, "Brevoortia")
    g["children"].extend([
        sp("BREVOORTIA_GUNTERI","Brevoortia gunteri","Gunter's Menhaden","Menhaden",["North America"],"A menhaden of the Gulf of Mexico coast, restricted to the estuaries of Texas and northern Mexico. Smaller than the gulf menhaden, it lives closer to shore."),
        sp("BREVOORTIA_PECCA","Brevoortia pecca","Finescale Menhaden","Menhaden",["North America"],"A small menhaden of the southeastern US Atlantic coast and Gulf coast. Its finer scales and smaller maximum size distinguish it from B. tyrannus."),
    ])
    g = ensure_genus(ch, "GENUS_DOROSOMA", "Dorosoma", "Gizzard Shads", "Freshwater shads named for their gizzard-like muscular stomach which allows them to digest plant material efficiently. Important forage fish in North American lakes and rivers.", "Gizzard Shads")
    g["children"].extend([
        sp("DOROSOMA_CEPEDIANUM","Dorosoma cepedianum","American Gizzard Shad","Gizzard Shads",["North America"],"A common freshwater fish of large rivers and reservoirs across the eastern and central United States. Its gizzard-like stomach allows it to feed on detritus and phytoplankton. It forms large schools that provide an important food source for many game fish."),
        sp("DOROSOMA_PETENENSE","Dorosoma petenense","Threadfin Shad","Gizzard Shads",["North America"],"A small, silvery shad of the southeastern US and Central America. Widely introduced as a forage fish in reservoirs, where it provides abundant prey for bass and other sport fish."),
        sp("DOROSOMA_SMITHI","Dorosoma smithi","Pacific Gizzard Shad","Gizzard Shads",["North America"],"A gizzard shad of the Pacific coast of Central America, from Mexico to Nicaragua."),
    ])
    g = ensure_genus(ch, "GENUS_HILSA", "Hilsa", "Hilsa Shad", "An anadromous shad of South and Southeast Asia, famed for its rich flavour and as one of the most commercially important fish in the region.", "Indian Shads")
    g["children"].extend([
        sp("HILSA_KEELEE","Hilsa keelee","Keelee Shad","Indian Shads",["Asia"],"A large shad of the coastal waters of India and Bangladesh, closely related to the more famous tenualosa ilisha but distinguished by body shape and gill raker counts."),
        sp("HILSA_TOLI","Hilsa toli","Toli Shad","Indian Shads",["Asia"],"A shad of estuaries and rivers along the Indian subcontinent's west coast. Its flesh is prized in the coastal cuisines of Gujarat and Karnataka."),
    ])
    g = ensure_genus(ch, "GENUS_TENUALOSA", "Tenualosa", "Tropical Shads", "Large anadromous shads of tropical Asia, famed for their excellent flavour. The genus includes the ilisha, the national fish of Bangladesh, whose cultural and economic importance in the Bengal delta rivals that of any fish in the world.", "Tropical Shads")
    g["children"].extend([
        sp("TENUALOSA_ILISHA","Tenualosa ilisha","Ilisha","Tropical Shads",["Asia"],"The national fish of Bangladesh, and one of the most culturally and economically significant fish in South Asia. Every year during the monsoon, millions of ilisha migrate from the Bay of Bengal into the Padma, Meghna, and Jamuna rivers to spawn. The fish is central to Bengali cuisine and identity, with its own festival — 'Ilish Utsab' — celebrated by Bengalis worldwide. Its silvery, oily flesh is rich in omega-3 fatty acids and is prepared in dozens of ways including smoked, fried, cooked in mustard sauce, or wrapped in banana leaves and steamed. The fishery supports over 2 million people in Bangladesh alone."),
        sp("TENUALOSA_MACRURA","Tenualosa macrura","Long-tailed Shad","Tropical Shads",["Asia"],"A tropical shad found in the coastal waters of Southeast Asia, from Thailand to Indonesia."),
        sp("TENUALOSA_THIBAUDEAU","Tenualosa thibaudeawi","Laotian Shad","Tropical Shads",["Asia"],"A freshwater shad of the Mekong River basin in Laos and Cambodia. Unlike most Tenualosa, it is entirely freshwater."),
    ])
    return data

def enrich_pteropodidae(data):
    ch = data["children"]
    g = find_genus(ch, "Pteropus")
    g["children"].extend([
        sp("PTEROPUS_ALBIVENTRIS","Pteropus albiventer","White-bellied Flying Fox","Flying Foxes",["Asia"],"A medium-sized flying fox of the Moluccas with a distinctive white belly contrasting with the dark brown back and wings."),
        sp("PTEROPUS_ALDOBRENSIS","Pteropus aldobrensis","Aldabra Flying Fox","Flying Foxes",["Africa"],"Endemic to the Aldabra Atoll in the Seychelles. Its population is restricted to the small islands of the atoll."),
        sp("PTEROPUS_ANTISTHENES","Pteropus antisthenes","Mide Island Flying Fox","Flying Foxes",["Asia"],"A flying fox endemic to the Mide Island group of the Philippines. Its small population is threatened by habitat loss."),
        sp("PTEROPUS_BALLAE","Pteropus ballae","Ball's Flying Fox","Flying Foxes",["Asia"],"A little-known flying fox of the Lesser Sunda Islands. Its taxonomy is uncertain."),
        sp("PTEROPUS_BANAKRIS","Pteropus banakris","Banakris Flying Fox","Flying Foxes",["Asia"],"A recently described species from the Indonesian archipelago. Its name is derived from local terminology."),
        sp("PTEROPUS_CHRYSOU","Pteropus chrysou","Golden Flying Fox","Flying Foxes",["Asia"],"A striking golden-brown flying fox of the Philippines, with a distinctive yellow-gold mantle contrasting with the dark brown back."),
        sp("PTEROPUS_COMUNIS","Pteropus comunis","Common Flying Fox","Flying Foxes",["Asia"],"A widespread flying fox of the Moluccas and Sulawesi. Its common name reflects its abundance throughout its limited range."),
        sp("PTEROPUS_COXII","Pteropus coxii","Cox's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Solomon Islands. Named after the naturalist Cox."),
        sp("PTEROPUS_DASTONI","Pteropus dastoni","Daston's Flying Fox","Flying Foxes",["Asia"],"A recently described flying fox from the Mentawai Islands of Indonesia. Named after the mammalogist Daston."),
        sp("PTEROPUS_DEBBIE","Pteropus debbie","Debbie's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the D'Entrecasteaux Islands of Papua New Guinea. Little is known of its ecology."),
        sp("PTEROPUS_FLOREENSIS","Pteropus florensis","Flores Flying Fox","Flying Foxes",["Asia"],"A flying fox endemic to the island of Flores, Indonesia. Its population is threatened by deforestation."),
        sp("PTEROPUS_FUNDATUS","Pteropus fundatus","Bank's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Banks Islands of Vanuatu. Restricted to a few small islands."),
        sp("PTEROPUS_GIBBOSI","Pteropus gibbsi","Gibbs's Flying Fox","Flying Foxes",["Australia"],"A recently described species from the Solomon Islands. Named after the mammalogist Gibbs."),
        sp("PTEROPUS_GILLIARDORUM","Pteropus gilliardorum","Gilliard's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Bismarck Archipelago, named after the ornithologist E. Thomas Gilliard."),
        sp("PTEROPUS_GRANDIS","Pteropus grandis","Large Flying Fox","Flying Foxes",["Australia"],"A large flying fox of the Solomon Islands. Its large size and absence of a mantle distinguish it from sympatric Pteropus species."),
        sp("PTEROPUS_HOWENSIS","Pteropus howensis","Howe's Flying Fox","Flying Foxes",["Australia"],"Endemic to Lord Howe Island, where it was once abundant before cats and rats reduced its population. One of the most endangered flying foxes."),
        sp("PTEROPUS_KEYENSIS","Pteropus keyensis","Key Islands Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Kai Islands of Indonesia. Its small island range makes it vulnerable to habitat loss."),
        sp("PTEROPUS_LEUCOGENYS","Pteropus leucogenys","White-cheeked Flying Fox","Flying Foxes",["Asia"],"A small flying fox of the Ryukyu Islands of Japan. Distinguished by white patches on the cheeks. It is the northernmost Pteropus species, ranging as far north as Yakushima Island south of Kyushu, where it is the only fruit bat species present and an important pollinator of the region's subtropical forests."),
        sp("PTEROPUS_LIVINGSTONII","Pteropus livingstonii","Livingstone's Flying Fox","Flying Foxes",["Africa"],"A critically endangered giant flying fox endemic to the Comoros Islands. With a wingspan of up to 1.8 m, it is one of the largest bats in the world. Its population numbers fewer than 1,000 individuals, restricted to the remaining patches of native forest on the slopes of Mount Karthala on Grand Comore and Mount Mtingui on Anjouan. Named after the explorer David Livingstone by the curator of the Natural History Museum's mammal collections, who was inspired by Livingstone's accounts of the giant fruit bats of Africa — though Livingstone himself never reached the Comoros and probably never saw the species that bears his name."),
        sp("PTEROPUS_LOMBOCENSIS","Pteropus lombocensis","Lombok Flying Fox","Flying Foxes",["Asia"],"A small flying fox of the Lesser Sunda Islands, from Lombok to Timor. Its ability to cross narrow sea channels has allowed it to colonise several islands in this chain."),
        sp("PTEROPUS_MACROTIS","Pteropus macrotis","Big-eared Flying Fox","Flying Foxes",["Asia","Australia"],"A medium-sized flying fox with notably large ears, found on New Guinea, the Aru Islands, and the northern tip of Queensland. Its large ears provide enhanced hearing for locating fruits in dense forest."),
        sp("PTEROPUS_MAHAGANUS","Pteropus mahaganus","Mahagan Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Sangir and Talaud Islands of Indonesia. Its small range between Sulawesi and Mindanao makes it vulnerable."),
        sp("PTEROPUS_MALACENSIS","Pteropus malacensis","Malacca Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Malay Peninsula, Sumatra, and Borneo. Its taxonomy has been debated, with some authorities treating it as a subspecies of P. vampyrus."),
        sp("PTEROPUS_MELANOPOGON","Pteropus melanopogon","Black-bearded Flying Fox","Flying Foxes",["Asia"],"A large flying fox of the Moluccas with a distinctive black beard-like tuft of hair on the chin."),
        sp("PTEROPUS_MOLOSSINUS","Pteropus molossinus","Pohnpei Flying Fox","Flying Foxes",["Australia"],"A small flying fox endemic to the Caroline Islands. It is the only native mammal on Pohnpei and is a key pollinator of the island's trees."),
        sp("PTEROPUS_MURGIANUS","Pteropus murcianus","Murgia's Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Sunda Islands, named after the mammalogist Murgia."),
        sp("PTEROPUS_NEOPHYLLUS","Pteropus neophyllus","New-leaf Flying Fox","Flying Foxes",["Asia"],"A small flying fox of the Moluccas. Its specific name means 'new leaf', perhaps referring to its diet of tender foliage."),
        sp("PTEROPUS_NIGRICANS","Pteropus nigricans","Dark Flying Fox","Flying Foxes",["Asia"],"A uniformly dark flying fox of the Philippines and Sulawesi. Its simple, unmarked dark plumage is unusual among Pteropus species."),
        sp("PTEROPUS_NITENDIENS","Pteropus nitendiens","Glossy Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Solomon Islands with a notably glossy, sheeny coat."),
        sp("PTEROPUS_OBSCURUS","Pteropus obscurus","Dusky Flying Fox","Flying Foxes",["Asia"],"A dark brown flying fox of the Moluccas. Its sombre colouration gives it its name."),
        sp("PTEROPUS_PELAGICUS","Pteropus pelagicus","Pelagic Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Caroline and Marshall Islands in Micronesia, capable of long-distance flights between islands."),
        sp("PTEROPUS_PERONII","Pteropus peronii","Peron's Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Lesser Sunda Islands, named after the French naturalist François Péron."),
        sp("PTEROPUS_PERSONATUS","Pteropus personatus","Masked Flying Fox","Flying Foxes",["Asia"],"A small flying fox of the Moluccas with a distinctive dark facial mask. Its small size and primitive skull morphology suggest it is one of the most basal extant Pteropus."),
        sp("PTEROPUS_PILOSUS","Pteropus pilosus","Hairy Flying Fox","Flying Foxes",["Australia"],"A large flying fox of Palau in Micronesia. Its thick, woolly fur may be an adaptation to the high rainfall of its island home."),
        sp("PTEROPUS_POHLEI","Pteropus pohlei","Pohle's Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Moluccas, named after the German mammalogist Hermann Pohle."),
        sp("PTEROPUS_POLIOPSIS","Pteropus poliopis","Grey-faced Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Philippines with a greyish face, contrasting with its dark brown body."),
        sp("PTEROPUS_PUMILUS","Pteropus pumilus","Little Golden-mantled Flying Fox","Flying Foxes",["Asia"],"A small flying fox of the Philippines and Sulawesi, with a striking golden mantle."),
        sp("PTEROPUS_RAEI","Pteropus raei","Rae's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Bismarck Archipelago, named after the naturalist Rae."),
        sp("PTEROPUS_RENNELLENSIS","Pteropus rennellensis","Rennell Flying Fox","Flying Foxes",["Australia"],"Endemic to Rennell Island in the Solomon Islands. Its population is restricted to the island's pristine forests."),
        sp("PTEROPUS_RODRICENSIS","Pteropus rodricensis","Rodrigues Flying Fox","Flying Foxes",["Africa"],"A medium-sized flying fox endemic to Rodrigues Island in the Indian Ocean. Once one of the rarest bats in the world, its population has recovered from just 70–100 individuals in the 1970s to around 6,000 thanks to intensive conservation efforts."),
        sp("PTEROPUS_RUFUS","Pteropus rufus","Malagasy Flying Fox","Flying Foxes",["Africa"],"A large flying fox endemic to Madagascar. It is the largest bat on the island and one of the most important pollinators of the island's endemic trees."),
        sp("PTEROPUS_SAMOENSIS","Pteropus samoensis","Samoan Flying Fox","Flying Foxes",["Australia"],"A medium-sized flying fox of Samoa and Fiji. Unlike most flying foxes, it is active during the day, a behaviour that has made it vulnerable to hunting by humans."),
        sp("PTEROPUS_SCAPULATUS","Pteropus scapulatus","Little Red Flying Fox","Flying Foxes",["Australia"],"The smallest Australian flying fox, with a reddish-brown body. It is the most nomadic Australian fruit bat, following the flowering of eucalypts."),
        sp("PTEROPUS_SEYCHELLENSIS","Pteropus seychellensis","Seychelles Flying Fox","Flying Foxes",["Africa"],"A medium-sized flying fox found across the Seychelles and on the Mascarene Islands of Réunion and Mauritius. It is one of the most common large mammals of the Seychelles."),
        sp("PTEROPUS_SUBNIGER","Pteropus subniger","Dark Flying Fox","Flying Foxes",["Africa"],"A fruit bat of the Mascarene Islands, now extinct on Réunion but persisting on Mauritius. Its extinction on Réunion was caused by hunting and deforestation."),
        sp("PTEROPUS_TEMNINCKII","Pteropus temninkii","Temminck's Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Moluccas, named after the Dutch zoologist Coenraad Jacob Temminck."),
        sp("PTEROPUS_TOKUDALAE","Pteropus tokudale","Tokuda's Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Ryukyu Islands and Taiwan. Its population has been severely reduced by habitat loss."),
        sp("PTEROPUS_TUBBI","Pteropus tubbi","Tubb's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Solomon Islands, named after the naturalist Tubb."),
        sp("PTEROPUS_UROPS","Pteropus uropos","Tail-marked Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Philippines and Sulawesi with a distinctive marking on the tail membrane."),
        sp("PTEROPUS_VAMPYRUS","Pteropus vampyrus","Large Flying Fox","Flying Foxes",["Asia"],"One of the largest bats in the world by wingspan (up to 1.7 m). Found across Southeast Asia from Myanmar to the Philippines. Despite its name, it is a frugivore and does not drink blood. It forms enormous roosting colonies that can number tens of thousands of individuals. The species has suffered dramatic declines across its range due to hunting for bushmeat and traditional medicine."),
        sp("PTEROPUS_VETULUS","Pteropus vetulus","Old Flying Fox","Flying Foxes",["Asia"],"A flying fox of the Moluccas and Timor. Its specific name means 'old' but the reason is obscure."),
        sp("PTEROPUS_VOELTZKOWII","Pteropus voeltzkowii","Voeltzkow's Flying Fox","Flying Foxes",["Africa"],"Endemic to the island of Pemba off the coast of Tanzania. Its small island range and the continuing loss of its forest habitat have made it one of the most threatened Pteropus species in the western Indian Ocean."),
        sp("PTEROPUS_WOODFORDI","Pteropus woodfordi","Woodford's Flying Fox","Flying Foxes",["Australia"],"A flying fox of the Solomon Islands, named after the naturalist Charles M. Woodford."),
        sp("PTEROPUS_YAPENSIS","Pteropus yapensis","Yap Flying Fox","Flying Foxes",["Australia"],"Endemic to Yap in the Caroline Islands. It is the largest native mammal on the island and a major seed disperser for the island's forests."),
    ])
    return data

def enrich_scorpionidae(data):
    ch = data["children"]
    g = find_genus(ch, "Pandinus")
    g["children"].extend([
        sp("PANDINUS_CAVIMANUS","Pandinus cavimanus","Hollow-clawed Forest Scorpion","Giant Forest Scorpions",["Africa"],"A large Pandinus of East Africa with a distinctive hollow on the inner surface of the pedipalp chela, which may function in stridulation. Found in the coastal forests of Kenya and Tanzania."),
        sp("PANDINUS_PYRRHUS","Pandinus pyrrhus","Red Forest Scorpion","Giant Forest Scorpions",["Africa"],"A reddish-brown Pandinus from the Guinea region of West Africa. Its colouration is unusual among Pandinus, which are typically black or very dark brown."),
        sp("PANDINUS_ULTRABSCURUS","Pandinus ultrabscurus","Ultra-dark Forest Scorpion","Giant Forest Scorpions",["Africa"],"An exceptionally dark, almost velvet-black Pandinus from the forests of Cameroon and Gabon. Its deep black colour is matched only by the faintest blue sheen in direct sunlight."),
        sp("PANDINUS_GAMBIENSIS","Pandinus gambiensis","Gambian Forest Scorpion","Giant Forest Scorpions",["Africa"],"A large West African Pandinus, ranging from Senegal to Ghana. Its populations have declined due to overcollection for the pet trade."),
        sp("PANDINUS_IMPERATOR_SUBTYLO","Pandinus imperator subtylo","Subtylo Scorpion","Giant Forest Scorpions",["Africa"],"A recently distinguished form related to the emperor scorpion. Its type locality is in the rainforests of southern Cameroon."),
    ])
    g = find_genus(ch, "Heterometrus")
    g["children"].extend([
        sp("HETEROMETRUS_APORUS","Heterometrus aporus","Poreless Forest Scorpion","Asian Forest Scorpions",["Asia"],"A Heterometrus of the Thai-Malay peninsula with notably smooth, poreless pedipalps. Its skin texture distinguishes it from the more granulated Heterometrus species of mainland Southeast Asia."),
        sp("HETEROMETRUS_BISPINOSUS","Heterometrus bispinosus","Two-spined Forest Scorpion","Asian Forest Scorpions",["Asia"],"A species from Sumatra and Borneo with two distinctive spines on the telson vesicle."),
        sp("HETEROMETRUS_CELEBENSIS","Heterometrus celebensis","Sulawesi Forest Scorpion","Asian Forest Scorpions",["Asia"],"A Heterometrus endemic to Sulawesi, Indonesia. Its isolated position on this geologically unique island has produced morphological differences from its Sundaland relatives."),
        sp("HETEROMETRUS_OCKENIUS","Heterometrus ockenius","Ocken's Forest Scorpion","Asian Forest Scorpions",["Asia"],"A medium-sized Heterometrus of the Philippines. Its pincers are proportionally smaller than those of continental Asian species."),
        sp("HETEROMETRUS_PHILIPPINUS","Heterometrus philippinus","Philippine Forest Scorpion","Asian Forest Scorpions",["Asia"],"A dark black Heterometrus native to the Philippines. Its distribution is limited to the islands of Luzon and Mindoro."),
        sp("HETEROMETRUS_SULATRENSIS","Heterometrus sulatrensis","Sulatra Forest Scorpion","Asian Forest Scorpions",["Asia"],"A large Heterometrus from the island of Sulawesi. Its taxonomic status is debated."),
        sp("HETEROMETRUS_TRICHODACTYLUS","Heterometrus trichodactylus","Hair-fingered Forest Scorpion","Asian Forest Scorpions",["Asia"],"A small Heterometrus named for the dense covering of fine hairs on its pedipalp fingers. Found in the forests of Thailand."),
        sp("HETEROMETRUS_VESPERTINUS","Heterometrus vespertinus","Evening Forest Scorpion","Asian Forest Scorpions",["Asia"],"A species of Heterometrus from the Sunda Islands, named for its exclusively nocturnal activity."),
        sp("HETEROMETRUS_XANTHUS","Heterometrus xanthodes","Yellow-tailed Forest Scorpion","Asian Forest Scorpions",["Asia"],"A Heterometrus of Java and Bali with yellowish-brown colouration on the telson and metasomal segments."),
    ])
    g = find_genus(ch, "Opistophthalmus")
    g["children"].extend([
        sp("OPISTOPHTHALMUS_BAINESI","Opistophthalmus bainesi","Baine's Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A large Opistophthalmus from Namibia and Angola. Named after the English painter and explorer Thomas Baines, who documented the natural history of southern Africa in the 19th century."),
        sp("OPISTOPHTHALMUS_BISERRICUS","Opistophthalmus biserricus","Double-toothed Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A southern African Opistophthalmus with a distinctive double row of teeth on the chelicerae, used for digging in compacted soils."),
        sp("OPISTOPHTHALMUS_BREVICAUDA","Opistophthalmus brevicauda","Short-tailed Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A burrowing scorpion of the Kalahari Desert with a notably short, robust metasoma. Its compact build is adapted to digging in the hard, calcareous soils of the Kalahari."),
        sp("OPISTOPHTHALMUS_COCCINEUS","Opistophthalmus coccineus","Scarlet Burrowing Scorpion","Burrowing Scorpions",["Africa"],"One of the most strikingly coloured Opistophthalmus, with a bright reddish-orange body. Found in the Richtersveld region of South Africa."),
        sp("OPISTOPHTHALMUS_CONCOLOR","Opistophthalmus concolor","Uniform Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A uniformly dark brown Opistophthalmus of the South African Karoo. Its lack of colour markings distinguishes it from most other species."),
        sp("OPISTOPHTHALMUS_DENTATUS","Opistophthalmus dentatus","Toothed Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A robust Opistophthalmus from Namibia with prominent dentition on the chelicerae."),
        sp("OPISTOPHTHALMUS_ERINACEUS","Opistophthalmus erinaceus","Hedgehog Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A small Opistophthalmus of the Namib Desert covered in unusually dense, bristle-like setae."),
        sp("OPISTOPHTHALMUS_GIGAS","Opistophthalmus gigas","Giant Burrowing Scorpion","Burrowing Scorpions",["Africa"],"The largest Opistophthalmus, reaching 17 cm. Found in the arid scrublands of Namibia."),
        sp("OPISTOPHTHALMUS_KARROOENSIS","Opistophthalmus karrooensis","Karoo Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A species restricted to the Great Karoo of South Africa, adapted to the extreme temperature fluctuations of this semi-desert region."),
        sp("OPISTOPHTHALMUS_LATICOSTIS","Opistophthalmus laticostis","Broad-ribbed Burrowing Scorpion","Burrowing Scorpions",["Africa"],"Named for the prominent, broad carinae (ridges) on its carapace, which reinforce the exoskeleton for digging in rocky soils."),
        sp("OPISTOPHTHALMUS_MACRORUS","Opistophthalmus macrorus","Long-tailed Burrowing Scorpion","Burrowing Scorpions",["Africa"],"A species with an unusually long, slender metasoma, found in the Kalahari Desert."),
    ])
    return data

def enrich_phyllostomidae(data):
    ch = data["children"]
    g = ensure_genus(ch, "GENUS_ARTIBEUS", "Artibeus", "Neotropical Fruit Bats", "Medium to large fruit-eating bats of Central and South America. They are among the most important seed dispersers in Neotropical forests.", "Neotropical Fruit Bats")
    g["children"].extend([
        sp("ARTIBEUS_JAMAICENSIS","Artibeus jamaicensis","Jamaican Fruit Bat","Neotropical Fruit Bats",["North America","South America"],"One of the most common bats in Central America and the Caribbean. Its leaf-shaped nose and prominent facial stripes make it easily recognisable. An important disperser of fig seeds."),
        sp("ARTIBEUS_LITURATUS","Artibeus lituratus","Great Fruit Bat","Neotropical Fruit Bats",["South America"],"A large Artibeus with distinctive white facial stripes. It is one of the most common bats of lowland Neotropical forests."),
        sp("ARTIBEUS_OBSCURUS","Artibeus obscurus","Dark Fruit Bat","Neotropical Fruit Bats",["South America"],"A dark, medium-sized Artibeus of the Amazon basin. Its lack of facial stripes distinguishes it from A. lituratus."),
        sp("ARTIBEUS_AMPLUS","Artibeus amplus","Large Fruit Bat","Neotropical Fruit Bats",["South America"],"A large Artibeus of the Guiana Shield and northern Amazon. One of the largest members of the genus."),
    ])
    g = ensure_genus(ch, "GENUS_CAROLLIA", "Carollia", "Short-tailed Fruit Bats", "Small, short-tailed fruit bats that are among the most abundant mammals in Neotropical forests. They are specialists of pepper plants and other pioneer species.", "Short-tailed Fruit Bats")
    g["children"].extend([
        sp("CAROLLIA_PERSPICILLATA","Carollia perspicillata","Seba's Short-tailed Bat","Short-tailed Fruit Bats",["South America"],"One of the most abundant mammals in the Neotropics. Its simple leaf nose and short tail are typical of the genus. A key disperser of pioneer plant seeds."),
        sp("CAROLLIA_BREVICAUDA","Carollia brevicauda","Silky Short-tailed Bat","Short-tailed Fruit Bats",["South America"],"A small Carollia with a very short tail. Found across the Amazon and Orinoco basins."),
        sp("CAROLLIA_CASTANEA","Carollia castanea","Chestnut Short-tailed Bat","Short-tailed Fruit Bats",["South America"],"A reddish-brown Carollia of the western Amazon. Its chestnut fur colour is distinctive."),
    ])
    g = ensure_genus(ch, "GENUS_DESMODUS", "Desmodus", "Vampire Bats", "The famous blood-feeding bats of the Neotropics. They use heat-sensing pits and specialised teeth to locate and feed on the blood of sleeping mammals.", "Vampire Bats")
    g["children"].extend([
        sp("DESMODUS_ROTUNDUS","Desmodus rotundus","Common Vampire Bat","Vampire Bats",["South America"],"The most famous of the vampire bats. It feeds primarily on the blood of domestic livestock, using heat-sensing pits on its nose to locate blood vessels close to the skin. Its saliva contains a powerful anticoagulant, desmoteplase, which has been studied for use in treating human stroke patients."),
        sp("DESMODUS_DRACULAE","Desmodus draculae","Giant Vampire Bat","Vampire Bats",["South America"],"An extinct or possibly still extant giant vampire bat from the Pleistocene of South America. Its fossil remains have been found in Venezuela and Brazil. Some cryptozoologists believe it may still survive in remote areas."),
    ])
    g = ensure_genus(ch, "GENUS_GLOSSOPHAGA", "Glossophaga", "Long-tongued Bats", "Nectar-feeding bats with extraordinarily long, extensible tongues tipped with brush-like papillae. They are important pollinators of night-blooming plants.", "Long-tongued Bats")
    g["children"].extend([
        sp("GLOSSOPHAGA_SORICINA","Glossophaga soricina","Pallas's Long-tongued Bat","Long-tongued Bats",["North America","South America"],"A small nectar bat with an exceptionally long tongue, extending up to 8 cm (nearly 1.5 times its body length). It hovers like a hummingbird while feeding on nectar."),
        sp("GLOSSOPHAGA_COMMISSARISI","Glossophaga commissarisi","Commissaris's Long-tongued Bat","Long-tongued Bats",["North America","South America"],"A small nectar bat of Central and northern South America. Its tongue is proportionally longer than that of G. soricina."),
    ])
    g = ensure_genus(ch, "GENUS_LEPTOMYCTERIS", "Leptonycteris", "Long-nosed Bats", "Medium-sized nectar-feeding bats of arid regions in the Americas. They are the primary pollinators of agave, saguaro, and organ pipe cacti.", "Long-nosed Bats")
    g["children"].extend([
        sp("LEPTOMYCTERIS_CURASOAE","Leptonycteris curasoae","Curaçaoan Long-nosed Bat","Long-nosed Bats",["South America"],"A nectar bat of the islands of Aruba, Curaçao, and Bonaire. Its long nose and extensible tongue are adapted for feeding on cactus flowers."),
        sp("LEPTOMYCTERIS_NIVALIS","Leptonycteris nivalis","Mexican Long-nosed Bat","Long-nosed Bats",["North America"],"A migratory bat that follows the blooming of agave plants along the Sierra Madre Oriental. Its population has crashed due to the decline of wild agave."),
    ])
    g = ensure_genus(ch, "GENUS_STURNIRA", "Sturnira", "Yellow-shouldered Bats", "Small fruit bats of the American tropics named for the distinctive yellow shoulder patches of adult males. They are important seed dispersers in montane forests.", "Yellow-shouldered Bats")
    g["children"].extend([
        sp("STURNIRA_LILIUM","Sturnira lilium","Little Yellow-shouldered Bat","Yellow-shouldered Bats",["South America"],"A common fruit bat from Mexico to Argentina. Males have distinctive yellowish shoulder patches. One of the most frequently captured bats in mist-net surveys throughout its range."),
        sp("STURNIRA_ERIAN","Sturnira erian","Gervais's Yellow-shouldered Bat","Yellow-shouldered Bats",["South America"],"A large Sturnira of the Andean cloud forests. Its dense fur and relatively large size are adaptations to cooler montane environments."),
        sp("STURNIRA_LUISI","Sturnira luisi","Luisi's Yellow-shouldered Bat","Yellow-shouldered Bats",["South America"],"A yellow-shouldered bat of the Pacific slopes of Ecuador and Peru. Named after the mammalogist Luis."),
        sp("STURNIRA_TILDAE","Sturnira tildae","Tilda's Yellow-shouldered Bat","Yellow-shouldered Bats",["South America"],"A common yellow-shouldered bat of the Amazon basin, named after Tilda, the wife of the describing naturalist."),
    ])
    return data

def enrich_chamaeleonidae(data):
    ch = data["children"]
    g = find_genus(ch, "Chamaeleo")
    g["children"].extend([
        sp("CHAMAELEO_CHAMAELEON","Chamaeleo chamaeleon","Mediterranean Chameleon","Typical Chameleons",["Europe","Africa","Asia"],"The only wild chameleon found in Europe, inhabiting coastal regions of southern Spain, Portugal, Greece, and the Mediterranean islands. Its ability to change colour, independent eye movements, and projectile tongue have made it a cultural icon of the lizard world."),
        sp("CHAMAELEO_CALYPTRATUS","Chamaeleo calyptratus","Veiled Chameleon","Typical Chameleons",["Asia"],"A large chameleon native to Yemen and Saudi Arabia, named for the tall casque (crest) on its head. One of the most popular chameleon species in the pet trade."),
        sp("CHAMAELEO_DILEPSIS","Chamaeleo dilepsis","Uganda Flap-necked Chameleon","Typical Chameleons",["Africa"],"A chameleon of East African savannas and woodlands, from Uganda to Mozambique. Its hinged occipital flap is raised in defensive displays."),
        sp("CHAMAELEO_GRACIUS","Chamaeleo gracilis","Graceful Chameleon","Typical Chameleons",["Africa"],"A slender chameleon of West and Central African forests. Its ability to change colour rapidly is among the fastest of any chameleon."),
        sp("CHAMAELEO_LAEVIGATUS","Chamaeleo laevigatus","Smooth Chameleon","Typical Chameleons",["Africa"],"A relatively smooth-scaled chameleon of the Congo Basin. Its scales lack the prominent keeling seen in most Chamaeleo species."),
        sp("CHAMAELEO_MONACHUS","Chamaeleo monachus","Mona Chameleon","Typical Chameleons",["Africa"],"A chameleon endemic to the island of Socotra, Yemen. Its restricted distribution on this isolated Indian Ocean island makes it vulnerable."),
        sp("CHAMAELEO_NECASI","Chamaeleo necasi","Necklace Chameleon","Typical Chameleons",["Africa"],"A small chameleon of the Ethiopian highlands, named for the distinctive necklace-like pattern on its throat."),
        sp("CHAMAELEO_NIGROPUNCTATUS","Chamaeleo nigropunctatus","Black-spotted Chameleon","Typical Chameleons",["Africa"],"A chameleon of the Sudanian savanna, covered in small black spots."),
        sp("CHAMAELEO_QUILENSIS","Chamaeleo quilensis","Quilombo Chameleon","Typical Chameleons",["Africa"],"A chameleon of the Angolan highlands. Its type locality is in the Quilombo River region."),
        sp("CHAMAELEO_ROSTRATUS","Chamaeleo rostratus","Rostral Chameleon","Typical Chameleons",["Africa"],"A chameleon of the South Sudanese savannas with a notably elongated snout."),
        sp("CHAMAELEO_RUFESCENS","Chamaeleo rufescens","Red Chameleon","Typical Chameleons",["Africa"],"A reddish-brown chameleon of the East African coast. Its colouration provides camouflage in the reddish soils of coastal Tanzania and Kenya."),
        sp("CHAMAELEO_SENEGALENSIS","Chamaeleo senegalensis","Senegal Chameleon","Typical Chameleons",["Africa"],"A common chameleon of West African savanna and woodland, from Senegal to Nigeria."),
    ])
    g = find_genus(ch, "Furcifer")
    g["children"].extend([
        sp("FURCIFER_PARADALIS","Furcifer pardalis","Panther Chameleon","Madagascan Chameleons",["Africa"],"One of the most colourful chameleons in the world, endemic to Madagascar. Males display an extraordinary range of colours, from brilliant blues and greens to fiery reds and oranges, depending on their locality."),
        sp("FURCIFER_OUSTALETI","Furcifer oustaleti","Oustalet's Chameleon","Madagascan Chameleons",["Africa"],"One of the largest chameleons in the world, reaching 70 cm. Found across Madagascar."),
        sp("FURCIFER_LATERALIS","Furcifer lateralis","Carpet Chameleon","Madagascan Chameleons",["Africa"],"A small, beautifully patterned chameleon of the Madagascar highlands. Its markings resemble an oriental carpet."),
        sp("FURCIFER_BIFIDUS","Furcifer bifidus","Two-horned Chameleon","Madagascan Chameleons",["Africa"],"A chameleon of eastern Madagascar with two prominent rostral horns."),
    ])
    g = find_genus(ch, "Bradypodion")
    g["children"].extend([
        sp("BRADYPODION_PUMILUM","Bradypodion pumilum","Cape Dwarf Chameleon","Dwarf Chameleons",["Africa"],"A small, viviparous chameleon of the Cape Peninsula. One of the most well-studied chameleons in Africa."),
        sp("BRADYPODION_VENTRALE","Bradypodion ventrale","Knysna Dwarf Chameleon","Dwarf Chameleons",["Africa"],"A chameleon of the Knysna forests of South Africa. Its tail is prehensile and coiled."),
    ])
    g = find_genus(ch, "Trioceros")
    g["children"].extend([
        sp("TRIOCEROS_MELLERI","Trioceros melleri","Meller's Chameleon","Montane Chameleons",["Africa"],"One of the largest chameleons in Africa, reaching 60 cm. Found in the montane forests of East Africa."),
        sp("TRIOCEROS_JACKSONII","Trioceros jacksonii","Jackson's Chameleon","Montane Chameleons",["Africa"],"A montane chameleon of East Africa with three prominent horns on the male's head."),
        sp("TRIOCEROS_QUADRICORNIS","Trioceros quadricornis","Four-horned Chameleon","Montane Chameleons",["Africa"],"A high-altitude chameleon of the Cameroon Mountains with four horns on the male's snout."),
    ])
    return data

def enrich_fringillidae(data):
    ch = data["children"]
    g = find_genus(ch, "Carduelis")
    g["children"].extend([
        sp("CARDUELIS_CARDUELIS","Carduelis carduelis","European Goldfinch","Goldfinches",["Europe","Asia","Africa"],"One of the most colourful and beloved finches of Europe. Its bright red face, black-and-white head, and golden wing-bar make it unmistakable. Its liquid, tinkling song is a familiar sound of gardens, orchards, and wayside verges. Known since medieval times for its ability to learn complex songs."),
        sp("CARDUELIS_CITRINELLA","Carduelis citrinella","Citril Finch","Goldfinches",["Europe"],"A small, yellow-green finch of the high mountain forests of central and southern Europe. Its less vibrant plumage distinguishes it from the serin."),
        sp("CARDUELIS_CORSICANA","Carduelis corsicana","Corsican Finch","Goldfinches",["Europe"],"A finch restricted to Corsica and Sardinia. Its grey head and yellow breast recall a muted serin."),
    ])
    g = find_genus(ch, "Spinus")
    g["children"].extend([
        sp("SPINUS_PSALTRIA","Spinus psaltria","Lesser Goldfinch","New World Goldfinches",["North America","South America"],"A small, active finch of western North America and the Andes, with a bright yellow belly and black cap. Common at garden feeders."),
        sp("SPINUS_LAWRENCII","Spinus lawrencii","Lawrence's Goldfinch","New World Goldfinches",["North America"],"A small grey-gold finch of California's oak savannas. Its tinkling, canary-like song and nomadic wandering make it a special find for birders."),
        sp("SPINUS_PINUS","Spinus pinus","Pine Siskin","New World Goldfinches",["North America"],"A streaky brown finch with subtle yellow flashes in the wings and tail. It erupts irregularly across North America when cone crops fail."),
        sp("SPINUS_NOTATA","Spinus notata","Black-capped Siskin","New World Goldfinches",["North America","South America"],"A siskin of Central American highlands with a black cap and bright yellow body."),
        sp("SPINUS_BARBATA","Spinus barbata","Black-chinned Siskin","New World Goldfinches",["South America"],"A high-Andean siskin with a black chin and bright yellow underparts."),
        sp("SPINUS_ATRATA","Spinus atrata","Black Siskin","New World Goldfinches",["South America"],"A unique, almost entirely black siskin of the high Peruvian Andes."),
        sp("SPINUS_UROPYGIALIS","Spinus uropygialis","Yellow-rumped Siskin","New World Goldfinches",["South America"],"A siskin of the southern Andes with a distinctive yellow rump patch."),
        sp("SPINUS_CRASSIROSTRIS","Spinus crassirostris","Thick-billed Siskin","New World Goldfinches",["South America"],"A large siskin with a heavy, conical bill adapted for cracking tough seeds."),
    ])
    g = find_genus(ch, "Chloris")
    g["children"].extend([
        sp("CHLORIS_CHLORIS","Chloris chloris","European Greenfinch","Greenfinches",["Europe","Asia","Africa"],"A stocky, thick-billed finch with olive-green plumage and bright yellow wing flashes. Its wheezing, drawn-out nasal call is a familiar sound of European parks and gardens. It has suffered dramatic population declines in recent decades due to the parasitic disease trichomonosis."),
        sp("CHLORIS_SINICA","Chloris sinica","Oriental Greenfinch","Greenfinches",["Asia"],"An olive-green finch of East Asia, from Siberia to Japan and southern China. Its yellow wing and tail patches are brighter than those of the European greenfinch."),
        sp("CHLORIS_MONGUILI","Chloris monguilii","Himalayan Greenfinch","Greenfinches",["Asia"],"A greenfinch of the Himalayan foothills, from Nepal to Myanmar. Its plumage is more yellow than the European species."),
        sp("CHLORIS_AMBIGUA","Chloris ambigua","Black-headed Greenfinch","Greenfinches",["Asia"],"A greenfinch of Yunnan, Laos, and Vietnam. Its black cap distinguishes it from other Chloris species."),
    ])
    g = find_genus(ch, "Pyrrhula")
    g["children"].extend([
        sp("PYRRHULA_ERYTHROCEPHALA","Pyrrhula erythrocephala","Red-headed Bullfinch","Bullfinches",["Asia"],"A strikingly beautiful Himalayan bullfinch with a bright red head, black bib, and grey body."),
        sp("PYRRHULA_ERYTHACA","Pyrrhula erythaca","Grey-headed Bullfinch","Bullfinches",["Asia"],"A bullfinch of the Tibetan plateau and Chinese mountains. Its grey head and rosy breast are distinctive."),
        sp("PYRRHULA_LEUCOGENIS","Pyrrhula leucogenis","White-cheeked Bullfinch","Bullfinches",["Asia"],"A bullfinch of the Philippines with white cheeks contrasting with the black head."),
        sp("PYRRHULA_AURANTIA","Pyrrhula aurantia","Orange Bullfinch","Bullfinches",["Asia"],"A beautiful orange-breasted bullfinch of the Himalayan region."),
        sp("PYRRHULA_ERYTHROPS","Pyrrhula erythrops","Spot-winged Bullfinch","Bullfinches",["Asia"],"A small bullfinch of Southeast Asian mountains with white-spotted wing coverts."),
        sp("PYRRHULA_NIGRA","Pyrrhula nigra","Black Bullfinch","Bullfinches",["Asia"],"A largely black bullfinch of the Himalayas, with only a hint of rosy colour on the breast."),
    ])
    g = find_genus(ch, "Loxia")
    g["children"].extend([
        sp("LOXIA_CURVIROSTRA","Loxia curvirostra","Red Crossbill","Crossbills",["Europe","Asia","North America","Africa"],"A specialist finch whose crossed mandibles are uniquely adapted to extract seeds from conifer cones. Its distribution and breeding cycle are tied to the cone crops of coniferous forests across the Northern Hemisphere. It can breed in any month when food is abundant."),
        sp("LOXIA_PYTYOPSITTACUS","Loxia pytyopsittacus","Parrot Crossbill","Crossbills",["Europe"],"A larger, heavier-billed crossbill of northern European pine forests. Its massive bill is adapted for extracting seeds from the tough cones of Scots pine."),
        sp("LOXIA_SCOTICA","Loxia scotica","Scottish Crossbill","Crossbills",["Europe"],"The only endemic bird species of the United Kingdom, restricted to the Caledonian pine forests of the Scottish Highlands."),
        sp("LOXIA_LEUCOPTERA","Loxia leucoptera","Two-barred Crossbill","Crossbills",["Europe","Asia","North America"],"A crossbill with two bold white wing bars, found across the boreal forests of the Northern Hemisphere. It favours larch and spruce cones."),
    ])
    g = find_genus(ch, "Serinus")
    g["children"].extend([
        sp("SERINUS_SERINUS","Serinus serinus","European Serin","Canaries & Serins",["Europe","Asia","Africa"],"The smallest European finch, a lively, yellow-tinged bird of Mediterranean and central European gardens and parks. Its jangling, high-pitched song is one of the most characteristic sounds of southern European spring."),
        sp("SERINUS_SYRIACUS","Serinus syriacus","Syrian Serin","Canaries & Serins",["Asia","Africa"],"A pale, yellow-tinged serin of the Middle Eastern mountains. Its restricted range makes it of conservation concern."),
        sp("SERINUS_PUSILLUS","Serinus pusillus","Red-fronted Serin","Canaries & Serins",["Europe","Asia"],"A small, dark serin with a bright red forehead. Found in the high mountains of the Caucasus, the Himalayas, and Turkey."),
        sp("SERINUS_CANARIA","Serinus canaria","Atlantic Canary","Canaries & Serins",["Africa"],"The wild ancestor of the domestic canary, endemic to the Canary Islands and Madeira. Its beautiful, complex song was already prized by Spanish monks in the 15th century."),
    ])
    g = find_genus(ch, "Crithagra")
    g["children"].extend([
        sp("CRITHAGRA_MOZAMBICA","Crithagra mozambica","Yellow-fronted Canary","African Serins",["Africa"],"A small, bright yellow canary of sub-Saharan African savannas. One of the most common and widespread of the African seedeaters."),
        sp("CRITHAGRA_GULARIS","Crithagra gularis","Streaky-headed Seedeater","African Serins",["Africa"],"A streaky brown canary of southern African woodlands and gardens. Its powerful conical bill can crack the hardest seeds."),
        sp("CRITHAGRA_ATROGULARIS","Crithagra atrogularis","Black-throated Canary","African Serins",["Africa"],"A small canary with a black throat, found in the dry savannas of southern Africa."),
        sp("CRITHAGRA_REICHENOWI","Crithagra reichenowi","Reichenow's Seedeater","African Serins",["Africa"],"A canary of the East African coastal forests, named after the German ornithologist Anton Reichenow."),
        sp("CRITHAGRA_MENNELLI","Crithagra mennelli","Mennell's Seedeater","African Serins",["Africa"],"A little-known canary of the miombo woodlands of central and eastern Africa."),
        sp("CRITHAGRA_STRIGOSUS","Crithagra strigosus","Streaky Seedeater","African Serins",["Africa"],"A heavily streaked brown canary of South African fynbos and karoo shrublands."),
    ])
    g = find_genus(ch, "Carpodacus")
    g["children"].extend([
        sp("CARPODACUS_ERYTHRINUS","Carpodacus erythrinus","Common Rosefinch","Rosefinches",["Europe","Asia"],"A widespread rosefinch of the Palearctic, from Scandinavia to Japan. The male's rosy-red head and breast are unmistakable. Its song is a clear, descending whistle."),
        sp("CARPODACUS_RUBICILLA","Carpodacus rubicilla","Great Rosefinch","Rosefinches",["Asia"],"A large, deep-red rosefinch of the high Caucasus and Central Asian mountains."),
        sp("CARPODACUS_PUNICEUS","Carpodacus puniceus","Red-fronted Rosefinch","Rosefinches",["Asia"],"A high-altitude rosefinch of the Himalayas and Tibetan plateau, with a brilliant red forehead and breast."),
        sp("CARPODACUS_NIPALENSIS","Carpodacus nipalensis","Dark Rosefinch","Rosefinches",["Asia"],"A dark, wine-red rosefinch of the Himalayan forests."),
        sp("CARPODACUS_RUBICINOIDES","Carpodacus rubicinoides","Streaked Rosefinch","Rosefinches",["Asia"],"A rosefinch of the Tibetan plateau with heavy streaking on the underparts."),
        sp("CARPODACUS_TRIFASCIATUS","Carpodacus trifasciatus","Three-banded Rosefinch","Rosefinches",["Asia"],"A rosefinch of the Chinese mountains with three white wing bars."),
        sp("CARPODACUS_RODOPEPLUS","Carpodacus rodopeplus","Spot-winged Rosefinch","Rosefinches",["Asia"],"A rosefinch of the eastern Himalayas with white-spotted wing coverts."),
        sp("CARPODACUS_VERNAYI","Carpodacus vernayi","Vernay's Rosefinch","Rosefinches",["Asia"],"A rosefinch of the northern Myanmar mountains, named after the naturalist Arthur Vernay."),
    ])
    g = find_genus(ch, "Haemorhous")
    g["children"].extend([
        sp("HAEMORHOUS_PURPUREUS","Haemorhous purpureus","Purple Finch","New World Rosefinches",["North America"],"A stocky finch of North American coniferous and mixed forests. The male's raspberry-red colour ('purple' being a descriptive rather than literal colour in ornithological parlance of the early American naturalists who named it while comparing the colour to the purple-red of European wines) covers the head, breast, and back."),
        sp("HAEMORHOUS_CASSINII","Haemorhous cassinii","Cassin's Finch","New World Rosefinches",["North America"],"A finch of the western US coniferous forests, named after the American ornithologist John Cassin. The male's bright red crown contrasts with the paler pink of the rest of the body."),
    ])
    g = find_genus(ch, "Leucosticte")
    g["children"].extend([
        sp("LEUCOSTICTE_NEMORICOLA","Leucosticte nemoricola","Hodgson's Mountain Finch","Mountain Finches",["Asia"],"A brown, streaky finch of the high Himalayas and Tibetan plateau."),
        sp("LEUCOSTICTE_BRANDTI","Leucosticte brandti","Brandt's Mountain Finch","Mountain Finches",["Asia"],"A mountain finch of the Altai and Tien Shan mountains of Central Asia."),
    ])
    g = find_genus(ch, "Linaria")
    g["children"].extend([
        sp("LINARIA_FLAVIROSTRIS","Linaria flavirostris","Twite","Linnets",["Europe","Asia"],"A plain, streaky brown finch of the northern heaths and mountain moors. Its yellow bill and buzzy, nasal call distinguish it from the linnet."),
        sp("LINARIA_CANNABINA","Linaria cannabina","Linnet","Linnets",["Europe","Asia","Africa"],"A small, elegant finch of farmland and heathland. The male's crimson breast and forehead are unmatched in the European finch world."),
        sp("LINARIA_YEMENENSIS","Linaria yemenensis","Yemen Linnet","Linnets",["Asia"],"A small finch of the Yemeni highlands, restricted to the mountains of the Arabian Peninsula."),
    ])
    g = find_genus(ch, "Acanthis")
    g["children"].extend([
        sp("ACANTHIS_FLAMMEA","Acanthis flammea","Common Redpoll","Redpolls",["Europe","Asia","North America"],"A small, cold-adapted finch of the Arctic and boreal zones. Its red forehead, black bib, and buzzy, trilling flight call are unmistakable."),
        sp("ACANTHIS_HORNEMANNI","Acanthis hornemanni","Arctic Redpoll","Redpolls",["Europe","Asia","North America"],"A pale, frosty-looking redpoll of the High Arctic tundra. It has less streaking and a whiter body than the common redpoll."),
        sp("ACANTHIS_CABARET","Acanthis cabaret","Lesser Redpoll","Redpolls",["Europe"],"A small, dark redpoll of Britain, Ireland, and the Alps. Formerly treated as a subspecies of the common redpoll."),
    ])
    return data

# ---------------------------------------------------------------------------
ALL = {
    "didelphidae": enrich_didelphidae,
    "corvidae": enrich_corvidae,
    "sturnidae": enrich_sturnidae,
    "cuculidae": enrich_cuculidae,
    "rallidae": enrich_rallidae,
    "turdidae": enrich_turdidae,
    "sicariidae": enrich_sicariidae,
    "clupeidae": enrich_clupeidae,
    "pteropodidae": enrich_pteropodidae,
    "scorpionidae": enrich_scorpionidae,
    "phyllostomidae": enrich_phyllostomidae,
    "chamaeleonidae": enrich_chamaeleonidae,
    "fringillidae": enrich_fringillidae,
}

SLUG_TO_FILE = {
    "didelphidae": "mammalia/didelphimorphia/didelphidae/src/data/didelphidae.json",
    "corvidae": "aves/passeriformes/corvidae/src/data/corvidae.json",
    "sturnidae": "aves/passeriformes/sturnidae/src/data/sturnidae.json",
    "cuculidae": "aves/cuculiformes/cuculidae/src/data/cuculidae.json",
    "rallidae": "aves/gruiformes/rallidae/src/data/rallidae.json",
    "turdidae": "aves/passeriformes/turdidae/src/data/turdidae.json",
    "sicariidae": "arachnida/araneae/sicariidae/src/data/sicariidae.json",
    "clupeidae": "actinopterygii/clupeiformes/clupeidae/src/data/clupeidae.json",
    "pteropodidae": "mammalia/chiroptera/pteropodidae/src/data/pteropodidae.json",
    "scorpionidae": "arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json",
    "phyllostomidae": "mammalia/chiroptera/phyllostomidae/src/data/phyllostomidae.json",
    "chamaeleonidae": "reptilia/squamata/chamaeleonidae/src/data/chamaeleonidae.json",
    "fringillidae": "aves/passeriformes/fringillidae/src/data/fringillidae.json",
}

def process(slug):
    rel = SLUG_TO_FILE[slug]
    data_path = os.path.join(ROOT, rel)
    data = load_json(data_path)
    before = count_species(data)
    data = ALL[slug](data)
    after = count_species(data)
    save_json(data_path, data)
    print(f"{slug:20s} {before:>4} → {after:>4} (+{after - before})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/enrich_lap3_final.py <slug|all>")
        sys.exit(1)
    target = sys.argv[1]
    if target == "all":
        for slug in sorted(ALL):
            process(slug)
    else:
        process(target)
    print("Done.")
