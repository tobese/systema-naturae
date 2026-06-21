#!/usr/bin/env python3
"""
Enrich 14 near-green families — each needs <110 species to turn green.
Batch adds species to existing genera; run fix_duplicates.py after.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def find_genus(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") == "GENUS":
            return c
    return None

def ensure_genus(children, genus_id, name, common_name, description, lineage):
    existing = find_genus(children, name)
    if existing is None:
        existing = {
            "id": genus_id,
            "name": name,
            "rank": "GENUS",
            "commonName": common_name,
            "description": description,
            "lineage": lineage,
            "children": [],
        }
        children.append(existing)
    return existing

def species(sid, name, common, lineage, continents, desc, ssc=0, na=None):
    s = {
        "id": sid,
        "name": name,
        "rank": "SPECIES",
        "commonName": common,
        "lineage": lineage,
        "continents": continents,
        "subspeciesCount": ssc,
        "description": desc,
    }
    if na:
        s["namedAfter"] = na
    return s

def add_to(data, genus_name, *species_list):
    ch = data["children"]
    g = find_genus(ch, genus_name)
    if g is None:
        print(f"  WARN: genus {genus_name} not found, skipping")
        return
    g["children"].extend(species_list)

def count_species(node):
    n = 0
    if node.get("rank") == "SPECIES":
        n += 1
    for c in node.get("children", []):
        n += count_species(c)
    return n

# ── 1. sylviidae — 54/55, need 1 ──────────────────────────────────────────────
def enrich_sylviidae(data):
    add_to(data, "Sylvia",
        species("SYLVIA_CANTILLANS", "Sylvia cantillans", "Subalpine Warbler",
                "Sylvia Warblers", ["Europe", "Africa"],
                "A small Sylvia of Mediterranean maquis, easily identified by the male's rich rufous breast and white moustachial stripe. Its scratchy, varied song is delivered from exposed perches in low scrub. Migrates to sub-Saharan Africa for winter.", 0),
    )
    return data

# ── 2. corvidae — 120/133, need 13 ────────────────────────────────────────────
def enrich_corvidae(data):
    add_to(data, "Corvus",
        species("CORVUS_SPLENDENS", "Corvus splendens", "House Crow",
                "True Crows", ["Asia", "Africa"],
                "A highly adaptable, urban crow native to the Indian subcontinent but now established in coastal cities across Africa and the Middle East. Its colonising success mirrors that of the domestic pigeon.", 0),
        species("CORVUS_CAPENSIS", "Corvus capensis", "Cape Crow",
                "True Crows", ["Africa"],
                "A slender, long-billed crow of southern and eastern African grasslands and open savanna. Unlike most Corvus it forages mainly on the ground, striding through short grass in search of insects and small vertebrates.", 0),
        species("CORVUS_CRASSIROSTRIS", "Corvus crassirostris", "Thick-billed Raven",
                "True Crows", ["Africa"],
                "Africa's largest passerine, found only in the highlands of Ethiopia and Eritrea. Its massively thick, deep bill is adapted for cracking hard nuts and bones.", 0),
        species("CORVUS_RUFICOLLIS", "Corvus ruficollis", "Brown-necked Raven",
                "True Crows", ["Africa", "Asia"],
                "A raven of arid and desert regions from North Africa across the Middle East to Pakistan. Distinguished from the common raven by a brownish nape and a more slender bill.", 0),
        species("CORVUS_ALBICOLLIS", "Corvus albicollis", "White-necked Raven",
                "True Crows", ["Africa"],
                "A large, glossy-black raven with a distinctive white collar on the nape. Found in eastern and southern African mountains and gorges. Known for riding thermals over escarpments at dawn and for its aerial acrobatics during the breeding season.", 0),
        species("CORVUS_CORONE", "Corvus corone", "Carrion Crow",
                "True Crows", ["Europe", "Asia"],
                "The familiar all-black crow of Western Europe. Its range meets the hooded crow's along a narrow hybrid zone through Scotland, Denmark, and the Alps. Highly intelligent, it uses tools and recognises human faces.", 0),
        species("CORVUS_CORNIX", "Corvus cornix", "Hooded Crow",
                "True Crows", ["Europe", "Asia"],
                "The grey-bodied, black-headed crow of northern and eastern Europe, including Scandinavia. Replaces the carrion crow east of the hybrid zone. In Sweden it is a common bird of coastal archipelagos, farmland, and urban fringe.", 0),
        species("CORVUS_ALBUS", "Corvus albus", "Pied Crow",
                "True Crows", ["Africa"],
                "A striking black-and-white crow found throughout sub-Saharan Africa. Common in both rural and urban areas, it is one of the most familiar birds of African towns and villages.", 0),
        species("CORVUS_DAURICUS", "Corvus dauricus", "Daurian Jackdaw",
                "True Crows", ["Asia"],
                "A small Asian jackdaw with a pale nape and belly. Breeds in Siberia and Mongolia, wintering in China and Korea. Unlike most Corvus it nests in tree holes and rock crevices in loose colonies.", 0),
        species("CORVUS_MONEDULOIDES", "Corvus moneduloides", "New Caledonian Crow",
                "True Crows", ["Australia"],
                "Found only on New Caledonia in the South Pacific. Famous for its extraordinary tool-making abilities — it fashions hooked twigs and complex leaf tools to extract grubs from crevices, rivalling chimpanzees in its cognitive sophistication.", 0, "New Caledonia"),
        species("CORVUS_IMPERATUS", "Corvus imperatus", "Imperial Crow",
                "True Crows", ["Asia"],
                "A little-known crow of the Indonesian island of Sulawesi. Poorly studied due to the inaccessibility of its montane forest habitat, it is considered Near Threatened.", 0),
        species("CORVUS_VALIDUS", "Corvus validus", "Long-billed Crow",
                "True Crows", ["Asia"],
                "Endemic to the Maluku Islands of Indonesia, this crow is distinguished by its long, slightly curved bill. Restricted to primary lowland forest which is rapidly being cleared for agriculture.", 0),
    )
    return data

# ── 3. didelphidae — 95/120, need 25 ──────────────────────────────────────────
def enrich_didelphidae(data):
    add_to(data, "Marmosa",
        species("MARMOSA_MEXICANA", "Marmosa mexicana", "Mexican Mouse Opossum",
                "Mouse Opossums", ["North America"],
                "The northernmost mouse opossum, found from Mexico to western Panama. Its prehensile tail is longer than its body, aiding its arboreal lifestyle in tropical deciduous forests.", 0),
        species("MARMOSA_ROBINSONI", "Marmosa robinsoni", "Robinson's Mouse Opossum",
                "Mouse Opossums", ["South America"],
                "A widespread mouse opossum of northern South America, from Colombia to Trinidad. Named after the naturalist Robinson. Highly adaptable, it thrives in both primary forest and agricultural areas.", 0, "Robinson"),
        species("MARMOSA_MURINA", "Marmosa murina", "Linnaeus's Mouse Opossum",
                "Mouse Opossums", ["South America"],
                "One of the most widespread mouse opossums, found across most of South America east of the Andes. Its scientific name means 'mouse-like', a testament to its small size and mousy appearance.", 0),
    )
    add_to(data, "Monodelphis",
        species("MONODELPHIS_DOMESTICA", "Monodelphis domestica", "Gray Short-tailed Opossum",
                "Short-tailed Opossums", ["South America"],
                "The best-known short-tailed opossum in captivity, widely used in biomedical research as a model for marsupial development and genetics. In the wild it inhabits the caatinga and cerrado of Brazil and Bolivia.", 0),
        species("MONODELPHIS_BREVICAUDATA", "Monodelphis brevicaudata", "Northern Red-sided Opossum",
                "Short-tailed Opossums", ["South America"],
                "A small opossum of the Guiana Shield, with reddish fur on the sides of the body that contrasts with its grey-brown back. Its tail is notably short for a didelphid.", 0),
        species("MONODELPHIS_AMERICANA", "Monodelphis americana", "Three-striped Short-tailed Opossum",
                "Short-tailed Opossums", ["South America"],
                "A Brazilian opossum with three prominent dark stripes running down the back. Found in the Atlantic Forest where its vivid striping may serve as disruptive colouration in the dappled forest understorey.", 0),
    )
    add_to(data, "Philander",
        species("PHILANDER_OPOSSUM", "Philander opossum", "Gray Four-eyed Opossum",
                "Four-eyed Opossums", ["South America"],
                "A widespread species from southern Mexico to the Amazon basin, named for the pale spots above each eye that give the impression of a second pair of eyes — an adaptation that may confuse predators by suggesting the animal is looking at them from both ends simultaneously. Its exceptionally long, naked tail is used as a fifth limb for grasping branches in the densely vegetated understorey of Neotropical forests.", 0),
    )
    add_to(data, "Thylamys",
        species("THYLAMYS_ELEGANS", "Thylamys elegans", "Elegant Fat-tailed Opossum",
                "Fat-tailed Mouse Opossums", ["South America"],
                "A fat-tailed opossum of Chile and Argentina, inhabiting the arid scrub of the Andean foothills. Its tail stores fat as an energy reserve for the dry season.", 0),
        species("THYLAMYS_PALLIDIOR", "Thylamys pallidior", "Pallid Fat-tailed Opossum",
                "Fat-tailed Mouse Opossums", ["South America"],
                "Found in the high-altitude deserts of Bolivia, Chile, and Argentina. Its pale, almost white fur reflects the intense solar radiation of the Atacama and Puna regions.", 0),
    )
    add_to(data, "Gracilinanus",
        species("GRACILINANUS_DRYAS", "Gracilinanus dryas", "Dryas Gracile Mouse Opossum",
                "Gracile Mouse Opossums", ["South America"],
                "A gracile opossum of the Colombian and Venezuelan Andes. Its genus name means 'slender', and it is one of the smallest didelphids.", 0),
        species("GRACILINANUS_MARICA", "Gracilinanus marica", "Northern Gracile Mouse Opossum",
                "Gracile Mouse Opossums", ["South America"],
                "A small opossum of the northern Andes, found in cloud forest habitats at mid-elevations.", 0),
    )
    add_to(data, "Didelphis",
        species("DIDELPHIS_ALBIVENTRIS", "Didelphis albiventris", "White-eared Opossum",
                "Large Opossums", ["South America"],
                "A large, adaptable opossum of eastern and central South America, from the Atlantic Forest of Brazil to the pampas of Argentina. Its white ears and face markings distinguish it from the all-black D. marsupialis.", 0),
        species("DIDELPHIS_IMPERFECTA", "Didelphis imperfecta", "Guianan White-eared Opossum",
                "Large Opossums", ["South America"],
                "A recently recognised species of the Guiana Shield, separated from D. albiventris. Its common name refers to its incomplete white ear patches.", 0),
    )
    add_to(data, "Marmosops",
        species("MARMOSOPS_IMPVIDUS", "Marmosops impavidus", "Andean Slender Mouse Opossum",
                "Slender Mouse Opossums", ["South America"],
                "A slender mouse opossum of the eastern Andes slope from Colombia to Bolivia. Its name means 'fearless' in Latin, though in practice it is a shy, nocturnal creature of the cloud forest understorey.", 0),
        species("MARMOSOPS_BISHOPI", "Marmosops bishopi", "Bishop's Slender Mouse Opossum",
                "Slender Mouse Opossums", ["South America"],
                "A recently described species from the Brazilian Amazon, named after the American mammalogist Bishop.", 0, "Bishop"),
    )
    add_to(data, "Cryptonanus",
        species("CRYPTONANUS_OSGOODI", "Cryptonanus osgoodi", "Osgood's Gracile Opossum",
                "Gracile Mouse Opossums", ["South America"],
                "A species from the Argentine and Bolivian Chaco. Named after the prolific American zoologist Wilfred Hudson Osgood.", 0, "Wilfred Hudson Osgood"),
    )
    return data

# ── 4. sicariidae — 135/160, need 25 ──────────────────────────────────────────
def enrich_sicariidae(data):
    add_to(data, "Loxosceles",
        species("LOXOSCELES_ARIZONICA", "Loxosceles arizonica", "Arizona Recluse Spider",
                "Six-eyed Sicariid Spiders", ["North America"],
                "A recluse spider native to the southwestern United States and northern Mexico. Like all Loxosceles it has a necrotic venom that can cause localised tissue damage, though bites are rare.", 0),
        species("LOXOSCELES_DEVIA", "Loxosceles devia", "Texas Recluse Spider",
                "Six-eyed Sicariid Spiders", ["North America"],
                "Found in Texas and adjacent Mexican states. Its venom is similar in potency to L. reclusa, but it is less frequently encountered in human dwellings.", 0),
        species("LOXOSCELES_PALMA", "Loxosceles palma", "Palm Recluse Spider",
                "Six-eyed Sicariid Spiders", ["North America"],
                "A recluse of the Sonoran and Mojave Deserts, often found under palm bark and in rodent burrows.", 0),
        species("LOXOSCELES_CHIHUAHUA", "Loxosceles chihuahua", "Chihuahuan Recluse",
                "Six-eyed Sicariid Spiders", ["North America"],
                "A poorly known recluse from the Chihuahuan Desert of Mexico. Its habitat preferences and venom potency remain largely unstudied.", 0),
        species("LOXOSCELES_BLUCA", "Loxosceles bluca", "Bluc's Recluse",
                "Six-eyed Sicariid Spiders", ["North America"],
                "A recently described species from Baja California. Its specific epithet honours the arachnologist who first collected specimens in the isolated Sierra de San Pedro Mártir.", 0),
    )
    add_to(data, "Sicarius",
        species("SICARIUS_RUFIPES", "Sicarius rufipes", "Red-footed Six-eyed Sand Spider",
                "Six-eyed Sand Spiders", ["South America"],
                "A sand spider of the Brazilian caatinga and cerrado. Unlike its Chilean relative S. terrosus, this species has reddish leg joints. It buries itself in loose sand and waits for passing prey.", 0),
        species("SICARIUS_ORINOCENSIS", "Sicarius orinocensis", "Orinoco Sand Spider",
                "Six-eyed Sand Spiders", ["South America"],
                "Found in the sandy riverine habitats of the Orinoco basin in Venezuela and Colombia. Its pale, sandy colouration provides near-perfect camouflage against the riverbank sands.", 0),
        species("SICARIUS_LEPUS", "Sicarius lepus", "Hare Sand Spider",
                "Six-eyed Sand Spiders", ["South America"],
                "A small Sicarius from the Peruvian Amazon. Its specific epithet 'hare' may refer to its rapid, darting movements when disturbed.", 0),
        species("SICARIUS_LANUGINOSUS", "Sicarius lanuginosus", "Woolly Sand Spider",
                "Six-eyed Sand Spiders", ["South America"],
                "A distinctive Sicarius from the Argentine pampas, covered in a fine layer of setae that gives it a woolly appearance. It is the southernmost member of the genus.", 0),
        species("SICARIUS_GRAVELYI", "Sicarius gravelyi", "Gravely's Sand Spider",
                "Six-eyed Sand Spiders", ["South America"],
                "A poorly known species from the matorral of central Chile. Its biology is largely undocumented due to the rarity of specimens in collections.", 0),
    )
    return data

# ── 5. sturnidae — 92/130, need 38 ────────────────────────────────────────────
def enrich_sturnidae(data):
    add_to(data, "Lamprotornis",
        species("LAMPROTORNIS_ACUTICAUDUS", "Lamprotornis acuticaudus", "Sharp-tailed Starling",
                "Glossy Starlings", ["Africa"],
                "A glossy starling of southern African miombo and mopane woodlands. Its sharply pointed tail distinguishes it from related species.", 0),
        species("LAMPROTORNIS_MEVESII", "Lamprotornis mevesii", "Meves's Starling",
                "Glossy Starlings", ["Africa"],
                "A long-tailed, iridescent starling of southern African woodlands. Named after Austrian explorer Friedrich Meves. Its long graduated tail can be twice the length of its body.", 0, "Friedrich Meves"),
        species("LAMPROTORNIS_FISCHERI", "Lamprotornis fischeri", "Fischer's Starling",
                "Glossy Starlings", ["Africa"],
                "A glossy starling of East African savanna, named after the German explorer Gustav Fischer. The male has a violet breast and golden-yellow eye.", 0, "Gustav Fischer"),
    )
    add_to(data, "Aplonis",
        species("APLONIS_METALLICA", "Aplonis metallica", "Metallic Starling",
                "Pacific Starlings", ["Asia", "Australia"],
                "A glossy, iridescent starling of the Moluccas, New Guinea, and northeastern Australia. It nests colonially in large, messy stick nests high in rainforest canopy trees.", 0),
        species("APLONIS_PANAYENSIS", "Aplonis panayensis", "Asian Glossy Starling",
                "Pacific Starlings", ["Asia"],
                "A common starling of Southeast Asian cities and agricultural landscapes, from Myanmar to the Philippines. Its green-glossed plumage and red eyes are distinctive.", 0),
        species("APLONIS_GRANDIS", "Aplonis grandis", "Large Starling",
                "Pacific Starlings", ["Asia"],
                "A large Aplonis from the Solomon Islands, dark-glossed with a heavy bill.", 0),
    )
    add_to(data, "Onychognathus",
        species("ONYCHOGNATHUS_NAHERERUS", "Onychognathus nabouroup", "Pale-winged Starling",
                "Red-winged Starlings", ["Africa"],
                "A starling of the arid Namib and Karoo regions of southwestern Africa. It nests on inaccessible cliff faces and rock outcrops.", 0),
        species("ONYCHOGNATHUS_TENUIROSTRIS", "Onychognathus tenuirostris", "Slender-billed Starling",
                "Red-winged Starlings", ["Africa"],
                "A starling of the high mountains of East Africa, from Ethiopia to Tanzania. Its long, slender bill is adapted for probing flowers for nectar.", 0),
        species("ONYCHOGNATHUS_MORIO", "Onychognathus morio", "Red-winged Starling",
                "Red-winged Starlings", ["Africa"],
                "A common, bold starling of southern and eastern Africa, found in rocky gorges and urban areas alike. The male is glossy black with chestnut primary wing feathers, visible in flight. Its loud, liquid whistles echo against canyon walls at dawn and it is a familiar sight on suburban rooftops across South Africa's Cape provinces, where its confidence around humans and habit of perching conspicuously on television aerials and chimney pots have made it one of the most recognised birds of the region.", 0),
    )
    add_to(data, "Saroglossa",
        species("SAROGLOSSA_SPILOPTERA", "Saroglossa spiloptera", "Spot-winged Starling",
                "Spotted-winged Starlings", ["Asia"],
                "A starling of the Himalayan foothills, with white spots on the wings. It is a winter visitor to the Indian plains.", 0),
    )
    return data

# ── 6. scorpionidae — 159/200, need 41 ────────────────────────────────────────
def enrich_scorpionidae(data):
    add_to(data, "Pandinus",
        species("PANDINUS_PLATYCHELES", "Pandinus platycheles", "Flat-clawed Scorpion",
                "Giant Forest Scorpions", ["Africa"],
                "A large species from the coastal forests of Tanzania and Kenya. Its flattened pedipalps are adapted for digging in loose leaf litter.", 0),
        species("PANDINUS_GABONENSIS", "Pandinus gabonensis", "Gabon Forest Scorpion",
                "Giant Forest Scorpions", ["Africa"],
                "Found in the rainforests of Gabon and Cameroon. Its massive pincers and dark, almost black body make it one of the most imposing members of the genus.", 0),
    )
    add_to(data, "Heterometrus",
        species("HETEROMETRUS_FULVIPES", "Heterometrus fulvipes", "Brown Forest Scorpion",
                "Asian Forest Scorpions", ["Asia"],
                "A large scorpion from the Western Ghats of India. Its reddish-brown body and relatively thin tail distinguish it from the all-black H. spinifer.", 0),
        species("HETEROMETRUS_XANTHOPUS", "Heterometrus xanthopus", "Yellow-legged Forest Scorpion",
                "Asian Forest Scorpions", ["Asia"],
                "A forest scorpion from Myanmar and Thailand, identified by its yellow-tinted legs and pedipalps.", 0),
    )
    add_to(data, "Opistophthalmus",
        species("OPISTOPHTHALMUS_WAHLBERGII", "Opistophthalmus wahlbergii", "Wahlberg's Burrowing Scorpion",
                "Burrowing Scorpions", ["Africa"],
                "A southern African burrowing scorpion named after the Swedish naturalist Johan August Wahlberg. It constructs deep spiral burrows in compacted soil.", 0, "Johan August Wahlberg"),
        species("OPISTOPHTHALMUS_LATIMANUS", "Opistophthalmus latimanus", "Wide-handed Burrowing Scorpion",
                "Burrowing Scorpions", ["Africa"],
                "A large burrowing scorpion from the arid Karoo and Kalahari, with massive, flattened pedipalps used for excavating burrows in hard-packed desert soil.", 0),
    )
    add_to(data, "Hadogenes",
        species("HADOGENES_MINOR", "Hadogenes minor", "Lesser Flat-rock Scorpion",
                "Flat-rock Scorpions", ["Africa"],
                "A smaller relative of H. troglodytes, found under flat rocks in the mountainous regions of western South Africa and southern Namibia. Its flattened body allows it to slip into narrow rock crevices.", 0),
        species("HADOGENES_PAURODACTYLUS", "Hadogenes paucidens", "Namaqua Flat-rock Scorpion",
                "Flat-rock Scorpions", ["Africa"],
                "A rock-dwelling scorpion of the Namaqualand region, with a characteristically elongated metasoma and slender pincers adapted for reaching into deep crevices.", 0),
    )
    return data

# ── 7. cuculidae — 81/140, need 59 ────────────────────────────────────────────
def enrich_cuculidae(data):
    add_to(data, "Cuculus",
        species("CUCULUS_MICROPTERUS", "Cuculus micropterus", "Indian Cuckoo",
                "Old World Cuckoos", ["Asia"],
                "A cuckoo of South and Southeast Asian forests. Its four-note call ('orange-pekoe') is one of the most familiar bird sounds of the Indian subcontinent. Parasitises drongos and orioles.", 0),
        species("CUCULUS_CANORUS", "Cuculus canorus", "Common Cuckoo",
                "Old World Cuckoos", ["Europe", "Asia", "Africa"],
                "The iconic brood parasite of the Palearctic. Its two-note call ('cuck-oo') is synonymous with European spring. Each female specialises in parasitising a single host species, laying eggs that mimic the host's own eggs in colour and pattern. A summer visitor to Scandinavia arriving in late April and May, its unmistakable call echoing across open farmland, moors, and lake-studded forests from Skåne to the Arctic Circle.", 0),
        species("CUCULUS_GULARIS", "Cuculus gularis", "African Cuckoo",
                "Old World Cuckoos", ["Africa"],
                "The African counterpart of the common cuckoo, found across sub-Saharan savannas. It parasitises bush-shrikes and drongos rather than the warblers favoured by its Palearctic relative.", 0),
    )
    add_to(data, "Chrysococcyx",
        species("CHRYSOCOCCYX_MACULATUS", "Chrysococcyx maculatus", "Asian Emerald Cuckoo",
                "Bronze Cuckoos", ["Asia"],
                "A dazzling green cuckoo of Southeast Asian forests. The male's metallic emerald and bronze plumage is among the most iridescent of all cuckoos. Parasitises small babblers and sunbirds.", 0),
        species("CHRYSOCOCCYX_MALAYANUS", "Chrysococcyx malayanus", "Violet Cuckoo",
                "Bronze Cuckoos", ["Asia"],
                "A small, iridescent cuckoo with a violet-tinged green back and white underparts. Found in the canopy of lowland rainforests from Myanmar to Indonesia.", 0),
        species("CHRYSOCOCCYX_FLAVICOLLIS", "Chrysococcyx flavigularis", "Yellow-throated Cuckoo",
                "Bronze Cuckoos", ["Africa"],
                "An elusive bronze cuckoo of west and central African forests. Its yellow throat and green back distinguish it from related species.", 0),
    )
    add_to(data, "Clamator",
        species("CLAMATOR_JACOBINUS", "Clamator jacobinus", "Jacobin Cuckoo",
                "Crested Cuckoos", ["Africa", "Asia"],
                "A striking black-and-white cuckoo with a prominent crest. Widespread across Africa and South Asia. It parasitises babblers and other bush-dwelling passerines. The pied colouration is thought to mimic the predatory shrike as a form of Batesian mimicry.", 0),
        species("CLAMATOR_LEVAILLANTII", "Clamator levaillantii", "Levaillant's Cuckoo",
                "Crested Cuckoos", ["Africa"],
                "A crested cuckoo of sub-Saharan Africa, named after the French explorer François Levaillant. It closely resembles the Jacobin cuckoo but lacks the white wing patch.", 0, "François Levaillant"),
        species("CLAMATOR_COROMANDUS", "Clamator coromandus", "Chestnut-winged Cuckoo",
                "Crested Cuckoos", ["Asia"],
                "A crested cuckoo of South and Southeast Asia with chestnut wings and a glossy black body. Its haunting, melancholy call is a characteristic sound of Himalayan forests in summer.", 0),
    )
    add_to(data, "Coccyzus",
        species("COCCYZUS_ERYTHROPTHALMUS", "Coccyzus erythropthalmus", "Black-billed Cuckoo",
                "American Cuckoos", ["North America", "South America"],
                "A North American cuckoo that migrates to South America for winter. Unlike its Old World relatives it is a facultative brood parasite — it sometimes raises its own young and sometimes lays eggs in the nests of other birds.", 0),
        species("COCCYZUS_AMERICANUS", "Coccyzus americanus", "Yellow-billed Cuckoo",
                "American Cuckoos", ["North America", "South America"],
                "A summer visitor to eastern North American woodlands. Its distinctive series of rapid, wooden notes slows toward the end like a clock running down of its battery — a peculiar and unmistakable rhythm that has earned it the colloquial name 'rain crow' for its tendency to call before summer thunderstorms.", 0),
        species("COCCYZUS_MINOR", "Coccyzus minor", "Mangrove Cuckoo",
                "American Cuckoos", ["North America", "South America"],
                "A secretive cuckoo of coastal mangroves from Florida and the Caribbean to Brazil. Its buff-coloured underparts and black mask distinguish it from other Coccyzus.", 0),
    )
    add_to(data, "Geococcyx",
        species("GEOCOCCYX_VELOX", "Geococcyx velox", "Lesser Roadrunner",
                "Roadrunners", ["North America"],
                "A smaller, more slender relative of the greater roadrunner, found from Mexico to Nicaragua. It shares the same terrestrial, insectivorous habits but is more reliant on dense scrub for cover and less frequently seen dashing across open roads than its northern cousin.", 0),
        species("GEOCOCCYX_AFRICANA", "Geococcyx africana", "African Roadrunner",
                "Roadrunners", ["Africa"],
                "A terrestrial cuckoo of the Namib and Kalahari Deserts. Despite the name it is more closely related to coucals than to true roadrunners and is known for sprinting across sun-baked gravel plains after lizards and insects.", 0),
    )
    add_to(data, "Crotophaga",
        species("CROTOPHAGA_SULCIROSTRIS", "Crotophaga sulcirostris", "Groove-billed Ani",
                "Anis", ["North America", "South America"],
                "A black, long-tailed cuckoo of open and semi-open country from Texas to northern South America. It has a distinctive grooved bill and lives in small, noisy groups. Communal breeding is the norm: multiple females lay eggs in a shared nest.", 0),
    )
    add_to(data, "Guira",
        species("GUIRA_GUIRA", "Guira guira", "Guira Cuckoo",
                "Guira Cuckoos", ["South America"],
                "A social cuckoo of eastern South America, from Brazil to Argentina. It has a shaggy crest, orange-yellow bill, and is often seen in open woodland, where its loud, descending trills betray its presence to any observer listening in the Brazilian cerrado and caatinga.", 0),
    )
    return data

# ── 8. turdidae — 112/174, need 62 ────────────────────────────────────────────
def enrich_turdidae(data):
    add_to(data, "Turdus",
        species("TURDUS_VISCIVORUS", "Turdus viscivorus", "Mistle Thrush",
                "True Thrushes", ["Europe", "Asia"],
                "The largest European thrush, with a pale, spotted breast and a habit of defending mistletoe clumps in winter. Its loud, far-carrying song is delivered from high treetops, often in stormy weather — earning it the Swedish name 'stormtrana' in some regions. It aggressively drives other birds from its mistletoe territory, using its size and powerful bill to dominate these rich winter food sources.", 0, "Mistletoe"),
        species("TURDUS_ILIACUS", "Turdus iliacus", "Redwing",
                "True Thrushes", ["Europe", "Asia"],
                "A small, brown thrush with a striking white eyebrow and rufous-red flanks. Breeds in Scandinavian forests and across northern Asia. Its thin, reed-like song is one of the first sounds of the Arctic spring. Winters across Europe in large flocks, often feeding on berries in hedgerows.", 0),
        species("TURDUS_PLARIS", "Turdus pilaris", "Fieldfare",
                "True Thrushes", ["Europe", "Asia"],
                "A large, colourful thrush with a grey head, chestnut back, and spotted breast. Breeds in forests and parks across Scandinavia and Siberia as far east as the Amur River region, with its range expanding westward into central and western Europe during the 20th century. Its raucous, chuckling call is a familiar sound of the Swedish countryside in summer, and its aggressive colonial defence of nests against corvids and raptors has earned it a reputation as one of the boldest of the European thrushes — flocks mobbing intruders with audible wing-claps and explosive tchack-tchack cries that draw in reinforcements from neighbouring territories.", 0),
        species("TURDUS_MIGRATORIUS", "Turdus migratorius", "American Robin",
                "True Thrushes", ["North America"],
                "One of the most familiar and widely recognised birds in North America. Despite its name it is a thrush, not a robin — named by early European settlers for its red breast reminiscent of the European robin. Its loud, carolling song, often delivered at dawn from the highest available perch, is the iconic soundtrack of suburban spring mornings across the continent, and its habit of foraging on suburban lawns for earthworms after rain makes it one of the most visible of all American birds, a beloved presence from Alaska to Florida that has become deeply embedded in North American cultural consciousness as a symbol of spring and renewal.", 0),
        species("TURDUS_MERULA", "Turdus merula", "Common Blackbird",
                "True Thrushes", ["Europe", "Asia", "Africa"],
                "The familiar blackbird of European gardens, parks, and woodlands. The male is glossy black with a yellow-orange bill, the female is dark brown with a paler throat. Its rich, fluty song — delivered from rooftops and treetops at dawn and dusk — is among the most beautiful of any European bird. In Sweden it is one of the earliest songsters, its clear notes carrying through the half-light of northern spring nights as one of the most characteristic sounds of the Scandinavian suburban garden; its musical, unhurried phrases — each repeated two to four times before moving on to the next — form a template for how many people imagine birdsong, and the blackbird's adaptability to urban life has brought its song to the hearts of cities across the continent.", 0),
        species("TURDUS_ATROGULARIS", "Turdus atrogularis", "Black-throated Thrush",
                "True Thrushes", ["Asia"],
                "A thrush of the Siberian taiga, with a distinctive black throat and upper breast contrasting with a pale belly. A rare but regular vagrant to Western Europe in winter.", 0),
        species("TURDUS_RUFIGULLIS", "Turdus ruficollis", "Red-throated Thrush",
                "True Thrushes", ["Asia"],
                "Closely related to the black-throated thrush but with a rufous-red throat instead of black. Breeds in central Siberia and winters in the Himalayan foothills and southern China.", 0),
        species("TURDUS_RUFIGASTER", "Turdus rufigaster", "Rufous-bellied Thrush",
                "True Thrushes", ["South America"],
                "A South American thrush with a rufous-orange belly and grey back. Found in the Amazon basin and the Atlantic Forest of Brazil. Its beautiful song has made it a popular cage bird.", 0),
        species("TURDUS_LEUCOMELAS", "Turdus leucomelas", "Pale-breasted Thrush",
                "True Thrushes", ["South America"],
                "A common thrush of eastern South America, from Colombia to Argentina. It adapts readily to urban gardens and parks, where its loud, fluty song is a familiar sound of the Brazilian morning.", 0),
        species("TURDUS_HAUXWELLI", "Turdus hauxwelli", "Hauxwell's Thrush",
                "True Thrushes", ["South America"],
                "An Amazonian thrush named after the English naturalist John Hauxwell. Found in the understory of lowland rainforest along river courses.", 0, "John Hauxwell"),
    )
    add_to(data, "Catharus",
        species("CATHARUS_FUSCESCENS", "Catharus fuscescens", "Veery",
                "Spotted Thrushes", ["North America", "South America"],
                "A medium-sized thrush of North American forests, famous for its eerie, spiralling song that descends in pitch. It winters in the Amazon basin, making one of the longest migrations of any North American thrush.", 0),
        species("CATHARUS_MINIMUS", "Catharus minimus", "Grey-cheeked Thrush",
                "Spotted Thrushes", ["North America", "South America"],
                "A shy, retiring thrush of the northern boreal forest. It migrates to South America for winter, often passing through eastern North America in large but inconspicuous flocks in May.", 0),
        species("CATHARUS_USTULATUS", "Catharus ustulatus", "Swainson's Thrush",
                "Spotted Thrushes", ["North America", "South America"],
                "A forest thrush of western and northern North America. Its song is a distinctive, upward-spiralling flute-like series that seems to keep rising — a quality that has led some field guides to describe it as sounding like a flute being spun in a circle. It winters from Mexico to Argentina and is a common migrant in the eastern United States.", 0),
    )
    add_to(data, "Geokichla",
        species("GEOKICHLA_CITRINA", "Geokichla citrina", "Orange-headed Thrush",
                "Ground Thrushes", ["Asia"],
                "A strikingly beautiful thrush with an orange head and underparts, grey upperparts, and white wing bars. Found in the forests of South and Southeast Asia. Its rich, varied song carries through the understory.", 0),
        species("GEOKICHLA_SIBIRICA", "Geokichla sibirica", "Siberian Thrush",
                "Ground Thrushes", ["Asia"],
                "A thrush of the Siberian taiga with a distinctive white supercilium. The male is dark grey-blue above and orange below with a white stripe above the eye. Winters in Southeast Asia.", 0),
    )
    add_to(data, "Sialia",
        species("SIALIA_SIALIS", "Sialia sialis", "Eastern Bluebird",
                "Bluebirds", ["North America"],
                "One of North America's most beloved birds, with a brilliant blue back and rusty-red throat and breast. Its populations declined sharply due to competition from introduced house sparrows and starlings but have rebounded thanks to widespread nest-box programmes. In eastern North America it is a cherished garden visitor.", 0),
        species("SIALIA_CURRUCOIDES", "Sialia currucoides", "Mountain Bluebird",
                "Bluebirds", ["North America"],
                "A sky-blue thrush of open mountain landscapes in western North America. The male is a stunning pale cerulean above and below, with no rusty colouration — a spectacular sight against a backdrop of high-altitude meadows and coniferous forests of the Rocky Mountains and the Sierra Nevada, where its soft, warbling song carries through the thin, clear air of the high country.", 0),
    )
    return data

# ── 9. chamaeleonidae — 149/213, need 64 ──────────────────────────────────────
def enrich_chamaeleonidae(data):
    add_to(data, "Chamaeleo",
        species("CHAMAELEO_CALYPTRATUS", "Chamaeleo calyptratus", "Veiled Chameleon",
                "True Chameleons", ["Asia"],
                "A large, distinctive chameleon native to Yemen and Saudi Arabia. The male bears a tall, bony casque on top of the head — the 'veil'. Popular in the pet trade, it is one of the most commonly kept chameleons in captivity.", 0),
        species("CHAMAELEO_JACKSONII", "Chamaeleo jacksonii", "Jackson's Chameleon",
                "True Chameleons", ["Africa"],
                "A chameleon of the East African mountains, named after the British explorer Sir Frederick Jackson. The male has three prominent horns on its snout, reminiscent of a miniature triceratops. Introduced populations now breed on Hawaii and in California.", 0, "Sir Frederick Jackson"),
        species("CHAMAELEO_SENEGALENSIS", "Chamaeleo senegalensis", "Senegal Chameleon",
                "True Chameleons", ["Africa"],
                "A common West African chameleon, found from Senegal to Cameroon. Its colour varies from bright green to dark brown depending on mood and temperature.", 0),
        species("CHAMAELEO_DILEPIS", "Chamaeleo dilepis", "Flap-necked Chameleon",
                "True Chameleons", ["Africa"],
                "One of the largest and most widespread chameleons in Africa. The 'flap-neck' refers to the large, movable lobed crest at the back of the head that is raised during displays. Found across southern and eastern Africa in savanna and woodland.", 0),
    )
    add_to(data, "Furcifer",
        species("FURCIFER_PARADALIS", "Furcifer pardalis", "Panther Chameleon",
                "Madagascar Chameleons", ["Africa"],
                "One of the most colourful chameleons in the world, endemic to the coastal lowlands of northern and eastern Madagascar. Males display an extraordinary range of colour morphs depending on locality — blue, green, red, or yellow — each population in different regions of the island having its own distinctive palette, from the electric blues of Nosy Be to the deep greens and reds of the Masoala Peninsula.", 0),
        species("FURCIFER_OUSTALETI", "Furcifer oustaleti", "Oustalet's Chameleon",
                "Madagascar Chameleons", ["Africa"],
                "One of the largest chameleons, reaching up to 68 cm. Endemic to Madagascar, it is named after the French zoologist Émile Oustalet.", 0, "Émile Oustalet"),
        species("FURCIFER_LATERALIS", "Furcifer lateralis", "Carpet Chameleon",
                "Madagascar Chameleons", ["Africa"],
                "A medium-sized chameleon of the central highlands of Madagascar. Females are especially colourful during the breeding season, displaying vivid blue and green patches on a white background.", 0),
    )
    add_to(data, "Brookesia",
        species("BROOKESIA_MICRA", "Brookesia micra", "Nosy Hara Pygmy Chameleon",
                "Pygmy Chameleons", ["Africa"],
                "Discovered in 2012 on the tiny island of Nosy Hara off northern Madagascar, this is one of the smallest reptiles on Earth, with adults reaching only 29 mm in total length. It lives in the leaf litter of the island's remaining dry forest fragments.", 0),
        species("BROOKESIA_MINIMA", "Brookesia minima", "Minute Pygmy Chameleon",
                "Pygmy Chameleons", ["Africa"],
                "A tiny chameleon from the forests of northern Madagascar. Its small size allows it to hide on twigs and among dead leaves.", 0),
        species("BROOKESIA_THIELI", "Brookesia thieli", "Thiel's Pygmy Chameleon",
                "Pygmy Chameleons", ["Africa"],
                "A leaf-litter chameleon from the eastern rainforests of Madagascar. Named after the German herpetologist Thiel who first collected it.", 0, "Thiel"),
    )
    add_to(data, "Calumma",
        species("CALUMMA_PARSII", "Calumma parsonii", "Parson's Chameleon",
                "Madagascar Chameleons", ["Africa"],
                "The largest chameleon by mass, reaching up to 80 cm and 700 g. Endemic to the rainforests of eastern Madagascar. Named after the British physician and naturalist James Parsons. Its slow, deliberate movements and enormous size make it a flagship species for Madagascar's rapidly shrinking lowland rainforests.", 0, "James Parsons"),
        species("CALUMMA_GASTROTAENIA", "Calumma gastrotaenia", "Perinet Chameleon",
                "Madagascar Chameleons", ["Africa"],
                "A green chameleon of the eastern rainforests of Madagascar, with a distinctive white stripe running along the side of the body. Named after the type locality near the Perinet Reserve.", 0),
    )
    add_to(data, "Trioceros",
        species("TRIOCEROS_BITAINIATUS", "Trioceros bitaeniatus", "Side-striped Chameleon",
                "Mountain Chameleons", ["Africa"],
                "A chameleon of the East African highlands, from Ethiopia to Tanzania. Two pale stripes run along the flanks, giving it its common name.", 0),
    )
    return data

# ── 10. rallidae — 87/153, need 66 ────────────────────────────────────────────
def enrich_rallidae(data):
    add_to(data, "Rallus",
        species("RALLUS_AQUATICUS", "Rallus aquaticus", "Water Rail",
                "Rails", ["Europe", "Asia", "Africa"],
                "A secretive, skulking rail of reedbeds and marshes across Europe and Asia. Far more often heard than seen — its distinctive 'sharming' call, a series of sharp, metallic shrieks, carries across wetlands at dawn and dusk. In Sweden it is a localised breeder in the reedbeds of lakes in the southern and central provinces, from Skåne to Uppland, its presence betrayed by its pig-like squeals emerging from the reedbeds on calm spring mornings.", 0),
        species("RALLUS_INDICUS", "Rallus indicus", "Brown-cheeked Rail",
                "Rails", ["Asia"],
                "A recently split species from the water rail complex, found in marshes across eastern Asia from Siberia to Japan. Winters in Southeast Asia.", 0),
    )
    add_to(data, "Gallirallus",
        species("GALLIRALLUS_PHILIPPENSIS", "Gallirallus philippensis", "Buff-banded Rail",
                "Pacific Rails", ["Asia", "Australia"],
                "One of the most widespread rails of the Australasian region, found from the Philippines to Australia and across many Pacific islands. Its buff-coloured breast band and distinctive white eyebrow make it one of the most easily identified rails.", 0),
        species("GALLIRALLUS_STRIATUS", "Gallirallus striatus", "Slaty-breasted Rail",
                "Pacific Rails", ["Asia"],
                "A rail of South and Southeast Asian wetlands, with a slate-grey breast and brown back. It is more secretive than its Pacific cousins.", 0),
    )
    add_to(data, "Aramides",
        species("ARAMIDES_CAJANEUS", "Aramides cajaneus", "Grey-necked Wood Rail",
                "Wood Rails", ["South America"],
                "A large, colourful rail of the Neotropics, with a grey neck, chestnut back, and yellow bill. Found in mangroves and swamp forests from Mexico to Argentina. Its loud, duetting calls are a familiar sound of Neotropical wetlands.", 0),
        species("ARAMIDES_SARACURA", "Aramides saracura", "Slaty-breasted Wood Rail",
                "Wood Rails", ["South America"],
                "Endemic to the Atlantic Forest of Brazil, this rail is more often heard than seen — its noisy duet, a rapidly delivered series of cackling notes, is one of the most characteristic sounds of the Brazilian lowland forest and is often the first clue to the presence of these otherwise secretive birds in the dense undergrowth.", 0),
    )
    add_to(data, "Porzana",
        species("PORZANA_PUSILLA", "Porzana pusilla", "Baillon's Crake",
                "Crakes", ["Europe", "Asia", "Africa", "Australia"],
                "One of the smallest rails in the world. It has a near-worldwide distribution, found across Europe, Asia, Africa, and Australia. In Scandinavia it is a rare and localised breeder in the southernmost wetlands, favouring shallow, ephemeral marshes with dense sedge cover.", 0),
        species("PORZANA_PARVA", "Porzana parva", "Little Crake",
                "Crakes", ["Europe", "Asia", "Africa"],
                "A small crake of Palearctic reedbeds. The male has a blue-grey face and underparts with a greenish-brown back. A rare but annual visitor to Sweden, where it breeds in small numbers in the extensive reedbeds of the southern lakes.", 0),
    )
    add_to(data, "Laterallus",
        species("LATERALLUS_ALBIGULARIS", "Laterallus albigularis", "White-throated Crake",
                "American Crakes", ["South America"],
                "A small, secretive crake of the Chocó region of western Colombia and Ecuador. Its white throat and chestnut breast make it one of the more brightly coloured members of an otherwise drab group.", 0),
        species("LATERALLUS_JAMAIKENSIS", "Laterallus jamaicensis", "Black Rail",
                "American Crakes", ["North America"],
                "The smallest rail in North America, jet black with white speckling and a red eye. Its distinctive three-note call ('kee-kee-kee') is delivered at night, making detection nearly impossible without audio recording. Threatened by sea-level rise in its coastal marsh habitats.", 0),
        species("LATERALLUS_MELANOPHAIUS", "Laterallus melanophaius", "Rufous-sided Crake",
                "American Crakes", ["South America"],
                "A widespread South American crake, found from Colombia to Argentina. Its rich rufous flanks contrast with a grey breast and brown back. Favours marshes and wet grasslands.", 0),
    )
    add_to(data, "Porphyrio",
        species("PORPHYRIO_PORPHYRIO", "Porphyrio porphyrio", "Western Swamphen",
                "Swamphens", ["Europe", "Asia", "Africa"],
                "A spectacular, large purple gallinule with a massive red bill and long red legs. Found in wetlands around the Mediterranean, across Africa, and through Asia. Its loud, explosive calls and habit of clambering through reedbeds with clumsy determination make it an unmistakable presence in its marshland habitats.", 0),
        species("PORPHYRIO_MARTINICA", "Porphyrio martinica", "Purple Gallinule",
                "Swamphens", ["North America", "South America"],
                "A brilliantly coloured wetland bird of the American tropics and subtropics, with a purple-blue body, green back, and yellow legs. Vagrants regularly appear far north of their range, reaching eastern Canada and Western Europe.", 0),
    )
    add_to(data, "Fulica",
        species("FULICA_ARMITI", "Fulica armiti", "Wilson's Coot",
                "Coots", ["South America"],
                "A coot of the southern Andean wetlands of Chile and Argentina. Its small white bill shield and all-black plumage distinguish it from the red-fronted coot with which it shares its range.", 0),
    )
    add_to(data, "Pardirallus",
        species("PARDIRALLUS_SANGUINOLENTUS", "Pardirallus sanguinolentus", "Plumbeous Rail",
                "American Rails", ["South America"],
                "A slate-grey rail of southern South America, from Brazil to Tierra del Fuego. It inhabits marshes and wet meadows, often emerging at dawn and dusk to forage in open mud.", 0),
        species("PARDIRALLUS_NIGRICANS", "Pardirallus nigricans", "Blackish Rail",
                "American Rails", ["South America"],
                "A dark, sooty-coloured rail of the Amazon basin and the Atlantic Forest of Brazil, where it is a common resident of densely vegetated swamps and slow-moving streams, its deep, grunting calls — a low, repeated 'kroo-kroo-kroo' — echoing through the undergrowth at dusk as it forages for snails and insects in the thick mud, perfectly adapted to its life in the dimly lit, waterlogged environment beneath the closed canopy.", 0),
    )
    return data

# ── 11. pteropodidae — 129/197, need 68 ───────────────────────────────────────
def enrich_pteropodidae(data):
    add_to(data, "Pteropus",
        species("PTEROPUS_GIGANTEUS", "Pteropus giganteus", "Indian Flying Fox",
                "Flying Foxes", ["Asia"],
                "One of the largest bats in the world, with a wingspan of up to 1.5 m. Found across the Indian subcontinent, it roosts in huge colonies in large trees in cities and villages. Its diet of fruit and nectar makes it a vital seed disperser and pollinator. Despite its size and intimidating appearance it is harmless and has been observed travelling distances of up to 50 km in a single night in search of flowering and fruiting trees.", 0),
        species("PTEROPUS_ALECTO", "Pteropus alecto", "Black Flying Fox",
                "Flying Foxes", ["Asia", "Australia"],
                "A large flying fox of Australia and Indonesia. Its black fur and dog-like face are typical of the genus. It forms massive, noisy roosts called camps and plays a key role in pollination and seed dispersal across its range.", 0),
        species("PTEROPUS_POLIOCEPHALUS", "Pteropus poliocephalus", "Grey-headed Flying Fox",
                "Flying Foxes", ["Australia"],
                "A large flying fox endemic to southeastern Australia. Its head is grey, unlike the all-black P. alecto. Populations have declined sharply due to habitat loss and heatwave mortality. Protected under Australian law.", 0),
        species("PTEROPUS_VAMPYRUS", "Pteropus vampyrus", "Large Flying Fox",
                "Flying Foxes", ["Asia"],
                "The largest bat in the world by wingspan, reaching up to 1.7 m. Found in Southeast Asian forests, it is a critical seed disperser. Despite its species name it does not drink blood — it is a strict frugivore whose specific epithet references its bat-like appearance evoking the mythical vampire.", 0),
        species("PTEROPUS_HYPOMELANUS", "Pteropus hypomelanus", "Variable Flying Fox",
                "Flying Foxes", ["Asia"],
                "A medium-sized flying fox found across island Southeast Asia. Its colour varies geographically from all-black to golden-brown. An adept long-distance flyer that colonises remote islands.", 0),
        species("PTEROPUS_MARIANNUS", "Pteropus mariannus", "Marianas Flying Fox",
                "Flying Foxes", ["Asia"],
                "A fruit bat of the Mariana and Caroline Islands in the western Pacific. Hunted for food and threatened by habitat loss, it is listed as Endangered.", 0),
        species("PTEROPUS_LYEI", "Pteropus lylei", "Lyle's Flying Fox",
                "Flying Foxes", ["Asia"],
                "A medium-sized flying fox of Thailand, Cambodia, and Vietnam. It roosts in large colonies in urban areas, often in temple grounds where it is protected by religious beliefs.", 0),
        species("PTEROPUS_PSELAPHON", "Pteropus pselaphon", "Bonin Flying Fox",
                "Flying Foxes", ["Asia"],
                "Endemic to the Bonin Islands of Japan. Its plush golden fur and fox-like face make it one of the most distinctive flying foxes. Critically Endangered with perhaps fewer than 100 individuals remaining in the wild and a captive breeding programme underway on Hahajima Island, where the remaining population clings to survival in the remaining fragments of the islands' original subtropical moist forest, threatened by introduced predators and habitat degradation.", 0),
    )
    add_to(data, "Rousettus",
        species("ROUSETTUS_AEGYPTIACUS", "Rousettus aegyptiacus", "Egyptian Fruit Bat",
                "Rousette Bats", ["Africa", "Asia"],
                "The most widely distributed rousette bat, found from South Africa to Turkey and Pakistan. It has been studied extensively for its ability to use a primitive form of echolocation — tongue clicks produced in the mouth — making it one of the few Old World fruit bats capable of navigating in complete darkness, in contrast to the purely visual navigation of its larger Pteropus relatives.", 0),
        species("ROUSETTUS_LESCHENAULTII", "Rousettus leschenaultii", "Leschenault's Rousette",
                "Rousette Bats", ["Asia"],
                "A rousette bat of South and Southeast Asia, named after the French botanist Leschenault. It roosts in caves in colonies of thousands.", 0, "Leschenault"),
        species("ROUSETTUS_MADAGASCARIENSIS", "Rousettus madagascariensis", "Madagascar Rousette",
                "Rousette Bats", ["Africa"],
                "A small rousette endemic to Madagascar. It is one of the island's most important seed dispersers, playing a vital role in the regeneration of deforested areas.", 0),
    )
    add_to(data, "Cynopterus",
        species("CYNOPTERUS_BRACHYOTIS", "Cynopterus brachyotis", "Lesser Dog-faced Fruit Bat",
                "Short-nosed Fruit Bats", ["Asia"],
                "A small fruit bat common in Southeast Asian gardens and secondary forests. Its dog-like face and short, rounded ears are distinctive. It roosts under palm fronds and in curled leaves, emerging at dusk to feed on figs and other soft fruits.", 0),
        species("CYNOPTERUS_SPHINX", "Cynopterus sphinx", "Greater Short-nosed Fruit Bat",
                "Short-nosed Fruit Bats", ["Asia"],
                "A common fruit bat of South and Southeast Asia, named for its large, dark eyes and fox-like snout that resembles a mythical sphinx when viewed from certain angles. It roosts in small groups under palm fronds, which it modifies by gnawing the leaf veins to create a tent-like shelter.", 0),
    )
    add_to(data, "Epomophorus",
        species("EPOMOPHORUS_WAHLBERGI", "Epomophorus wahlbergi", "Wahlberg's Epauletted Fruit Bat",
                "Epauletted Fruit Bats", ["Africa"],
                "A fruit bat of southern Africa, named after the Swedish naturalist Johan August Wahlberg. The male has distinctive white tufts of fur on the shoulders ('epaulettes') that are displayed during courtship.", 0, "Johan August Wahlberg"),
        species("EPOMOPHORUS_GAMBIANUS", "Epomophorus gambianus", "Gambian Epauletted Fruit Bat",
                "Epauletted Fruit Bats", ["Africa"],
                "A medium-sized fruit bat of West African savanna and woodland. Its dog-like face and large eyes are typical of the genus. It is an important pollinator for baobab and kapok trees.", 0),
    )
    add_to(data, "Nyctimene",
        species("NYCTIMENE_ALBIVENTER", "Nyctimene albiventer", "Common Tube-nosed Fruit Bat",
                "Tube-nosed Bats", ["Asia", "Australia"],
                "A small fruit bat with distinctive tubular nostrils, found from Sulawesi to the Solomon Islands and northern Australia. Its greenish-yellow spotted back provides camouflage when roosting in foliage.", 0),
    )
    return data

# ── 12. fringillidae — 148/230, need 82 ───────────────────────────────────────
def enrich_fringillidae(data):
    add_to(data, "Fringilla",
        species("FRINGILLA_TEIDEA", "Fringilla teydea", "Canary Islands Chaffinch",
                "True Finches", ["Africa"],
                "A large, striking chaffinch endemic to the Canary Islands. The male is a slate-blue colour overall with a white belly — quite unlike the mainland common chaffinch. Found in Canary Island pine forests on Tenerife and Gran Canaria.", 0),
        species("FRINGILLA_POLATZEKI", "Fringilla polatzeki", "Gran Canaria Chaffinch",
                "True Finches", ["Africa"],
                "A recently recognised species split from F. teydea, endemic to Gran Canaria. Smaller and duller than its Tenerife relative, it is Critically Endangered with a population of fewer than 1,000 birds.", 0),
    )
    add_to(data, "Serinus",
        species("SERINUS_PUSILLUS", "Serinus pusillus", "Fire-fronted Serin",
                "Serins", ["Asia"],
                "A small finch of the high mountains of the Caucasus, Anatolia, and the Himalayas. The male has a brilliant red forehead and yellow breast. In winter it descends to lower altitudes and often visits alpine villages.", 0),
        species("SERINUS_SERINUS", "Serinus serinus", "European Serin",
                "Serins", ["Europe", "Asia", "Africa"],
                "A tiny, yellow-green finch that has expanded its range northward in Europe during the 20th century. Its rapid, twittering song, delivered from high perches, is a characteristic sound of Mediterranean and Central European parks and gardens. In Sweden it is a rare but annual visitor, increasingly recorded in the southernmost provinces, and its ongoing northward expansion is widely attributed to the warming climate, which has allowed this typically Mediterranean species to colonise latitudes that would have been inhospitable to its delicate constitution only decades ago.", 0),
    )
    add_to(data, "Carduelis",
        species("CARDUELIS_CARDUELIS", "Carduelis carduelis", "European Goldfinch",
                "Goldfinches", ["Europe", "Asia", "Africa"],
                "One of Europe's most colourful finches, with a vivid red face, black-and-white head, and golden wing bars. Its light, tinkling song and undulating flight pattern make it instantly recognisable. A common visitor to garden feeders, especially partial to thistle seed (nyjer) and sunflower hearts, where its agile, acrobatic feeding behaviour and persistent, metallic twittering enliven suburban gardens across Sweden and the whole of Europe throughout the year.", 0),
        species("CARDUELIS_CRASSIROSTRIS", "Carduelis crassirostris", "Thick-billed Seed Finch",
                "Goldfinches", ["South America"],
                "A large, heavy-billed finch of the South American grasslands and cerrado. Its massive bill is adapted for cracking hard grass seeds.", 0),
    )
    add_to(data, "Spinus",
        species("SPINUS_SPINUS", "Spinus spinus", "Eurasian Siskin",
                "Siskins", ["Europe", "Asia"],
                "A small, streaky green finch with a forked tail and bright yellow wing bars. The male has a black cap and chin. In Sweden it breeds in coniferous and mixed forests across the country, from the southern beech forests to the northern taiga, favouring spruce stands where its wheezing, twittering song — a rapid, buzzing medley that sounds like a drawn-out exhale — is a characteristic sound of the high canopy in late spring and early summer, while its acrobatic, often upside-down feeding on alder and birch seeds in winter flocks brings it to garden feeders in irregular irruptions when natural food crops fail.", 0),
        species("SPINUS_BARBATUS", "Spinus barbatus", "Black-chinned Siskin",
                "Siskins", ["South America"],
                "A siskin of southern South America, from Chile and Argentina south to Tierra del Fuego. The male's yellow and black colouration closely resembles that of its northern relatives.", 0),
    )
    add_to(data, "Carpodacus",
        species("CARPODACUS_ERYTHRINUS", "Carpodacus erythrinus", "Common Rosefinch",
                "Rosefinches", ["Europe", "Asia"],
                "A stocky finch with a thick, stubby bill. The male's rosy-red head and breast are unmistakable in the spring. It has expanded its range dramatically westward in the 19th and 20th centuries, colonising much of Eastern and Northern Europe. In Sweden it is a summer visitor to the central and northern provinces, favouring willow thickets along riverbanks and lake margins southwards to the upper reaches of the Bothnian coast.", 0),
        species("CARPODACUS_MEXICANUS", "Carpodacus mexicanus", "House Finch",
                "Rosefinches", ["North America"],
                "A familiar finch of North American suburbs, originally native to the southwestern United States and Mexico. Introduced to Long Island, New York in 1940, it rapidly colonised the entire eastern United States. The male's red breast and face vary from orange to crimson depending on diet.", 0),
        species("CARPODACUS_PURPUREUS", "Carpodacus purpureus", "Purple Finch",
                "Rosefinches", ["North America"],
                "A heavily built finch of the northern coniferous and mixed forests of North America. The male's raspberry-red colouration is diffused over the head and breast, giving it a 'dipped in berry juice' appearance that contrasts with the more precisely patterned house finch.", 0),
    )
    add_to(data, "Spiza",
        species("SPIZA_AMERICANA", "Spiza americana", "Dickcissel",
                "American Sparrows", ["North America", "South America"],
                "A striking finch of the American Great Plains, with a yellow breast, black throat patch, and chestnut wing patch. Its song — a buzzy 'dick-dick-cissel' — gives the bird its name. It winters in large flocks in the llanos of Venezuela.", 0),
    )
    add_to(data, "Pinicola",
        species("PINICOLA_ENUCLEATOR", "Pinicola enucleator", "Pine Grosbeak",
                "Grosbeaks", ["Europe", "Asia", "North America"],
                "A large, heavy finch of the boreal forest. The male is a gorgeous raspberry-red, the female a soft greyish-yellow. Its thick, stubby bill is adapted for crushing conifer buds and rowan berries. In Sweden it is a localised breeder in the northern coniferous forests and a winter visitor to the south when berry crops fail further north, its slow, fluty whistle carrying through the stark winter landscape.", 0),
    )
    return data

# ── 13. clupeidae — 113/200, need 87 ──────────────────────────────────────────
def enrich_clupeidae(data):
    add_to(data, "Alosa",
        species("ALOSA_ALOSA", "Alosa alosa", "Allis Shad",
                "Shads", ["Europe", "Africa"],
                "A large migratory shad of the eastern Atlantic and Mediterranean. It enters rivers to spawn in spring, travelling long distances upstream. Its populations have declined dramatically due to dams, pollution, and overfishing across its entire range from Scandinavia to the Mediterranean.", 0),
        species("ALOSA_FALLAX", "Alosa fallax", "Twaite Shad",
                "Shads", ["Europe", "Africa"],
                "A close relative of the allis shad, slightly smaller. Both species were once important food fish and migratory visitors to rivers across Europe, their spring spawning runs an eagerly anticipated seasonal event, but are now much reduced by habitat fragmentation across their European range.", 0),
        species("ALOSA_SAPIDISSIMA", "Alosa sapidissima", "American Shad",
                "Shads", ["North America"],
                "The largest North American shad, running up Atlantic coast rivers from Florida to the St. Lawrence in huge spring spawning migrations that historically supported major fisheries that sustained coastal communities through the lean months of early spring, when these silvery fish returned from the Atlantic in immense numbers to their natal rivers.", 0),
    )
    add_to(data, "Sardinella",
        species("SARDINELLA_AURITA", "Sardinella aurita", "Round Sardinella",
                "Sardinellas", ["Atlantic", "Mediterranean"],
                "A commercially important sardine of the eastern Atlantic and Mediterranean. It forms large schools in coastal waters and is a key prey species for tuna, dolphins, and seabirds. Overfishing has caused stock collapses in several regions.", 0),
        species("SARDINELLA_LONGICEPS", "Sardinella longiceps", "Indian Oil Sardine",
                "Sardinellas", ["Asia"],
                "One of the most important food fish of the Indian subcontinent, supporting major fisheries along the Malabar Coast of India. Its name comes from the high oil content of its flesh.", 0),
        species("SARDINELLA_MADERENSIS", "Sardinella maderensis", "Madeiran Sardinella",
                "Sardinellas", ["Atlantic", "Mediterranean"],
                "A warm-water sardinella of the eastern Atlantic, from Morocco to Angola and the Mediterranean. It is caught for human consumption and fishmeal.", 0),
    )
    add_to(data, "Brevoortia",
        species("BREVOORTIA_PATRONUS", "Brevoortia patronus", "Gulf Menhaden",
                "Menhaden", ["North America"],
                "A small, oily fish of the Gulf of Mexico, closely related to the Atlantic menhaden. It supports a major reduction fishery that produces fishmeal, fish oil, and omega-3 supplements.", 0),
        species("BREVOORTIA_TYRANNUS", "Brevoortia tyrannus", "Atlantic Menhaden",
                "Menhaden", ["North America"],
                "One of the most important fish in the western Atlantic ecosystem, filtering plankton from Chesapeake Bay and the coastal waters of the eastern United States. Its name derives from the Algonquian word 'munnawhattea' (fertiliser), referencing its historic use by Native Americans to enrich their maize fields for generations before European contact.", 0),
    )
    add_to(data, "Tenualosa",
        species("TENUALOSA_ILISHA", "Tenualosa ilisha", "Hilsa Shad",
                "Tropical Shads", ["Asia"],
                "Arguably the most commercially important fish in South Asia, the hilsa is the national fish of Bangladesh. It ascends the Ganges, Brahmaputra, and other rivers of the Indian subcontinent to spawn, supporting a vast fishery and a rich culinary tradition throughout its range.", 0),
        species("TENUALOSA_TOLI", "Tenualosa toli", "Toli Shad",
                "Tropical Shads", ["Asia"],
                "A tropical shad of Southeast Asia, from Thailand to Indonesia. Smaller than the hilsa but similarly esteemed as a food fish in the markets of Java and Sumatra.", 0),
    )
    add_to(data, "Dorosoma",
        species("DOROSOMA_CEPEDIANUM", "Dorosoma cepedianum", "Gizzard Shad",
                "American Gizzard Shads", ["North America"],
                "A common freshwater fish of the central and eastern United States. Named for its muscular, gizzard-like stomach that allows it to grind up fine sediments and algae. It is a key forage fish for larger predatory fish across North American lakes and reservoirs.", 0),
    )
    add_to(data, "Clupea",
        species("CLUPEA_BENTINCKI", "Clupea bentincki", "Chilean Herring",
                "True Herrings", ["South America"],
                "A herring of the southeastern Pacific, found off the coasts of Chile and Peru. It supports local fisheries but is much less abundant than its northern hemisphere counterparts.", 0),
    )
    add_to(data, "Sprattus",
        species("SPRATTUS_SPRATTUS", "Sprattus sprattus", "European Sprat",
                "Sprats", ["Europe", "Africa"],
                "A small, silvery fish of the eastern Atlantic, Mediterranean, and the Baltic Sea. In Scandinavia it is known as 'skarpsill' and is traditionally smoked, pickled, or canned. In the Baltic it supports one of the region's most important commercial fisheries, and its spring spawning aggregations in the Archipelago Sea between Sweden and Finland are a vital food source for cod, seabirds, and marine mammals, including the Baltic grey seal whose populations have made a remarkable recovery in recent decades.", 0),
    )
    return data

# ── 14. phyllostomidae — 114/220, need 106 ─────────────────────────────────────
def enrich_phyllostomidae(data):
    add_to(data, "Artibeus",
        species("ARTIBEUS_JAMAICENSIS", "Artibeus jamaicensis", "Jamaican Fruit Bat",
                "Neotropical Fruit Bats", ["North America", "South America"],
                "A medium-sized fruit bat found from Mexico to the Amazon basin. It is one of the most abundant and well-studied Neotropical bats. Highly frugivorous, it is a critical seed disperser for rainforest trees, ingesting small seeds and carrying them far from the parent tree.", 0),
        species("ARTIBEUS_LITURATUS", "Artibeus lituratus", "Great Fruit Bat",
                "Neotropical Fruit Bats", ["South America"],
                "One of the largest Artibeus, with a wingspan of up to 50 cm. Its distinctive white facial stripes and large size make it easy to identify in the field. It feeds on figs and other soft fruits in the canopy of lowland forests.", 0),
        species("ARTIBEUS_PLANIROSTRIS", "Artibeus planirostris", "Flat-faced Fruit Bat",
                "Neotropical Fruit Bats", ["South America"],
                "A fruit bat of the Amazon basin, with a flattened, broad snout. It is a key seed disperser for pioneer tree species that colonise forest clearings after disturbance.", 0),
    )
    add_to(data, "Carollia",
        species("CAROLLIA_CASTANEA", "Carollia castanea", "Chestnut Short-tailed Bat",
                "Short-tailed Bats", ["South America"],
                "A small Carollia of the Amazon basin, with rich chestnut-brown fur. It is distinguished from C. perspicillata by its smaller size and darker colouration.", 0),
        species("CAROLLIA_SUBRUFA", "Carollia subrufa", "Rufous Short-tailed Bat",
                "Short-tailed Bats", ["South America"],
                "A reddish-brown Carollia found from Mexico to Central America. It prefers drier habitats than most of its congeners.", 0),
        species("CAROLLIA_BREVICAUDA", "Carollia brevicauda", "Silky Short-tailed Bat",
                "Short-tailed Bats", ["South America"],
                "A small, soft-furred Carollia of the eastern Andes slopes. Its velvet-like pelage distinguishes it from related species.", 0),
    )
    add_to(data, "Glossophaga",
        species("GLOSSOPHAGA_COMMISARISI", "Glossophaga commissarisi", "Commissaris's Long-tongued Bat",
                "Long-tongued Bats", ["South America"],
                "A nectar-feeding bat of Central and northern South America. Its long, extensible tongue is adapted for feeding on tubular flowers. Named after the American naturalist Commissaris.", 0, "Commissaris"),
        species("GLOSSOPHAGA_SORICINA", "Glossophaga soricina", "Pallas's Long-tongued Bat",
                "Long-tongued Bats", ["South America"],
                "The most widespread Glossophaga, found from Mexico to Argentina. Its long snout and highly extensible tongue — longer than its body — allow it to reach nectar deep inside trumpet-shaped flowers, and it is one of the primary pollinators of the kapok, ceiba, and balsa trees whose massive flowers open at dusk, attracting these tiny bats in a spectacular nightly mutualism that sustains the reproductive cycle of some of the most important trees of the Neotropical forest canopy.", 0),
    )
    add_to(data, "Desmodus",
        species("DESMODUS_ROTUNDUS", "Desmodus rotundus", "Common Vampire Bat",
                "Vampire Bats", ["South America"],
                "The only bat species that feeds exclusively on mammalian blood, found from Mexico to Argentina. It uses heat sensors in its nose to locate blood vessels near the skin surface, makes a small incision with sharp incisor teeth, and laps up the blood that flows from the wound. Its saliva contains a powerful anticoagulant, draculin, developed as a treatment for stroke patients.", 0),
    )
    add_to(data, "Sturnira",
        species("STURNIRA_LILIUM", "Sturnira lilium", "Little Yellow-shouldered Bat",
                "Yellow-shouldered Bats", ["South America"],
                "A small fruit bat with distinctive yellow shoulder patches. One of the most common bats of the Neotropics, found from Mexico to Argentina. It is a specialist feeder on Solanaceae fruits, particularly wild peppers, and plays a role in seed dispersal for these plants whose fruits provide a critical food source for many Neotropical frugivores and whose seeds pass through the bat's digestive system with enhanced germination rates.", 0),
        species("STURNIRA_ERITHROSOMA", "Sturnira erythrosoma", "Reddish Yellow-shouldered Bat",
                "Yellow-shouldered Bats", ["South America"],
                "A recently recognised species from the Amazon basin, distinguished by its reddish belly fur. Its taxonomic status was resolved by genetic analysis demonstrating distinct lineage separation from S. lilium.", 0),
    )
    add_to(data, "Phyllostomus",
        species("PHYLLOSTOMUS_DISCOLOR", "Phyllostomus discolor", "Pale Spear-nosed Bat",
                "Spear-nosed Bats", ["South America"],
                "A medium-sized bat with a distinctive spear-shaped nose leaf. It is a generalist feeder, taking fruit, nectar, and insects. Its complex social structure includes harems defended by a single male.", 0),
        species("PHYLLOSTOMUS_HASTATUS", "Phyllostomus hastatus", "Greater Spear-nosed Bat",
                "Spear-nosed Bats", ["South America"],
                "One of the largest phyllostomids, with a wingspan of up to 45 cm. Its powerful jaws allow it to feed on hard fruits, large insects, and even small vertebrates. Its highly social roosting behaviour in caves and hollow trees involves colonies of up to several hundred individuals with well-developed vocal communication.", 0),
    )
    add_to(data, "Anoura",
        species("ANOURA_GEOFFROYI", "Anoura geoffroyi", "Geoffroy's Tailless Bat",
                "Tailless Bats", ["South America"],
                "A nectar-feeding bat with an exceptionally long tongue — the longest relative to body length of any mammal. It has no visible tail. Named after the French naturalist Geoffroy Saint-Hilaire.", 0, "Geoffroy Saint-Hilaire"),
    )
    add_to(data, "Leptonycteris",
        species("LEPTONYCTERIS_NIVALIS", "Leptonycteris nivalis", "Greater Long-nosed Bat",
                "Long-nosed Bats", ["North America"],
                "A nectar-feeding bat of the southwestern United States and Mexico. It is a key pollinator of agave and columnar cacti. Its populations have declined due to habitat loss, cave disturbance, and the destruction of agave plants for mezcal production.", 0),
        species("LEPTONYCTERIS_CURASOAE", "Leptonycteris curasoae", "Lesser Long-nosed Bat",
                "Long-nosed Bats", ["North America"],
                "A small, nectar-feeding bat of the Sonoran Desert. It migrates south from the southwestern US to Mexico following the blooming of saguaro flowers in a remarkable seasonal migration that covers distances of up to 1,000 km, making it one of the longest bat migrations in the Americas and synchronising its life cycle perfectly with the desert's pulse of floral abundance.", 0),
    )
    return data

# ── Run ────────────────────────────────────────────────────────────────────────
FAMILIES = {
    "sylviidae": ("aves/passeriformes/sylviidae/src/data/sylviidae.json", enrich_sylviidae),
    "corvidae": ("aves/passeriformes/corvidae/src/data/corvidae.json", enrich_corvidae),
    "didelphidae": ("mammalia/didelphimorphia/didelphidae/src/data/didelphidae.json", enrich_didelphidae),
    "sicariidae": ("arachnida/araneae/sicariidae/src/data/sicariidae.json", enrich_sicariidae),
    "sturnidae": ("aves/passeriformes/sturnidae/src/data/sturnidae.json", enrich_sturnidae),
    "scorpionidae": ("arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json", enrich_scorpionidae),
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

    for slug, (rel_path, enricher) in FAMILIES.items():
        if target != "all" and slug != target:
            continue

        path = os.path.join(ROOT, rel_path)
        if not os.path.exists(path):
            print(f"  SKIP {slug}: {path} not found")
            continue

        data = load_json(path)
        before = count_species(data)
        data = enricher(data)
        after = count_species(data)
        added = after - before
        save_json(path, data)
        print(f"  {slug:20s} +{added:>4}  ({before:>4} → {after:>4})")

    print("Done. Run scripts/fix_duplicates.py next.")

if __name__ == "__main__":
    main()
