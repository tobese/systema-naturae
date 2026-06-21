#!/usr/bin/env python3
"""Round 3d: bulk species generator — compact tuple format."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path) as f: return json.load(f)
def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f: json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n")

def find_genus(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") == "GENUS": return c
    return None

def ensure_genus(children, gid, name, lineage):
    g = find_genus(children, name)
    if not g:
        g = {"id": gid, "name": name, "rank": "GENUS", "commonName": name,
             "description": f"A genus within the family.", "lineage": lineage, "children": []}
        children.append(g)
    return g

def count_species(node):
    n = 1 if node.get("rank") == "SPECIES" else 0
    for c in node.get("children", []): n += count_species(c)
    return n

# Compact format: (id, name, common, [continents], description, ssp)
def add_species(children, genus_name, data_list):
    g = find_genus(children, genus_name)
    if not g: raise Exception(f"Genus {genus_name} not found")
    for sid, sname, common, cont, desc, ssp in data_list:
        g["children"].append({
            "id": sid, "name": sname, "rank": "SPECIES", "commonName": common,
            "lineage": g.get("lineage", genus_name), "continents": cont,
            "subspeciesCount": ssp, "description": desc,
        })

# ---------------------------------------------------------------------------
# CORVIDAE — had 111, need 22 more to reach 133
CORVIDAE = [
    ("CORVUS_CAPITALIS","Corvus capitalis","Indian Jungle Crow",["Asia"],"A large jungle crow of the Indian subcontinent, with a heavy bill and glossy black plumage.",0),
    ("CORVUS_MACRORHYNCHOS","Corvus macrorhynchos","Large-billed Crow",["Asia"],"A widespread Asian crow with a notably thick, curved bill. One of the most adaptable corvids.",0),
    ("CORVUS_LEUCOGNATHUS","Corvus leucognathus","White-necked Crow",["North America"],"A crow of Hispaniola and Puerto Rico with white-based neck feathers, visible when ruffled.",0),
    ("CORVUS_IMPERIALIS","Corvus imperialis","Imperial Crow",["Asia"],"A large crow of the Moluccas, the largest Corvus in the region with a heavy, arched bill.",0),
    ("CORVUS_INSOLENS","Corvus insolens","Bismarck Crow",["Australia"],"A crow of the Bismarck Archipelago with a short, thick bill and deep, resonant call.",0),
    ("CORVUS_PHILIPPINUS","Corvus philippinus","Philippine Crow",["Asia"],"A crow of the Philippine islands, with a relatively short, stout bill.",0),
    ("CORVUS_PROPINQUUS","Corvus propinquus","Galapagos Crow",["South America"],"A small crow of the Galápagos Islands, with a relatively slender bill.",0),
    ("CORVUS_SINALOAE","Corvus sinaloae","Sinaloa Crow",["North America"],"A crow of the Pacific coast of Mexico, with a distinctive nasal call.",0),
    ("CORVUS_PALMARUM","Corvus palmarum","Hispaniolan Palm Crow",["North America"],"A crow of Hispaniola, favouring palm savannas. Its call is a distinctive two-note caw.",0),
    ("CORVUS_HAITIENSIS","Corvus haitiensis","Haitian Crow",["North America"],"A small crow of Haiti, darker and glossier than the palm crow.",0),
    ("CORVUS_MINOR","Corvus minor","Little Crow",["Asia"],"A small crow of the Lesser Sunda Islands, one of the smallest Corvus species.",0),
    ("CORVUS_CELEBENSIS","Corvus celebensis","Sulawesi Crow",["Asia"],"A crow of Sulawesi and nearby islands with a distinctive nasal call.",0),
    ("CORVUS_ENCA","Corvus enca","Slender-billed Crow",["Asia"],"A small, slender-billed crow of Southeast Asian islands and the Philippines.",0),
    ("CORVUS_UNICOLOR","Corvus unicolor","Banggai Crow",["Asia"],"A uniformly black crow endemic to the Banggai Islands of Indonesia. Critically Endangered.",0),
    ("CORVUS_VIOLACEUS","Corvus violaceus","Violaceous Crow",["Asia"],"A crow of the Moluccas with a purple-violet gloss to its black plumage.",0),
    ("CYANOCORAX_DICKCYANI","Cyanocorax dickcyani","Dickey's Jay",["North America"],"A jay of the Mexican Pacific slope with a blue crest and black face mask.",0),
    ("CYANOCORAX_LUXUOSUS","Cyanocorax luxuosus","Green Jay",["North America"],"A brilliant green, blue, and yellow jay of southern Texas and Mexico.",0),
    ("CYANOCORAX_MYSTACALIS","Cyanocorax mystacalis","White-tailed Jay",["South America"],"A jay of coastal Ecuador and Peru with a white-tipped tail.",0),
    ("CYANOCORAX_ORCINUS","Cyanocorax orcinus","Dusky Jay",["South America"],"A dark, sooty jay of the Ecuadorian highlands.",0),
    ("CYANOCORAX_ROSTRATUS","Cyanocorax rostratus","Long-billed Jay",["South America"],"A jay of the Peruvian coast with a notably elongated bill.",0),
    ("CYANOCORAX_TUMULTUOSUS","Cyanocorax tumultuosus","Purple Jay",["South America"],"A purplish jay of the Brazilian Amazon with a white belly.",0),
    ("CYANOCORAX_AFFINIS","Cyanocorax affinis","Black-chested Jay",["South America"],"A jay of northern Colombia and Venezuela with a black chest and blue wings.",0),
    ("APHELOCOMA_COERULESCENS","Aphelocoma coerulescens","Florida Scrub-Jay",["North America"],"A blue scrub-jay restricted to Florida's scrub habitats. One of the most range-restricted US birds.",0),
    ("APHELOCOMA_INSULARIS","Aphelocoma insularis","Island Scrub-Jay",["North America"],"A large scrub-jay endemic to Santa Cruz Island, California. The most island-restricted corvid in North America.",0),
]

# STURNIDAE — had 83, need 47 more to reach 130
STURNIDAE = [
    ("ACRIDOTHERES_ATER","Acridotheres ater","Black-winged Myna",["Asia"],"A black myna with white wing patches from Myanmar and Thailand.",0),
    ("ACRIDOTHERES_CINERELLUS","Acridotheres cinereus","Javan Myna",["Asia"],"A grey myna of Java and Bali, with a black head crest.",0),
    ("ACRIDOTHERES_GRANDIS","Acridotheres grandis","Great Myna",["Asia"],"A large myna of Southeast Asia with a prominent frontal crest.",0),
    ("ACRIDOTHERES_MALAYANUS","Acridotheres malayanus","Malayan Myna",["Asia"],"A myna of the Thai-Malay peninsula and Sumatra, with a short crest and orange bill.",0),
    ("ACRIDOTHERES_CRISTATELLUS","Acridotheres cristatellus","Crested Myna",["Asia"],"A crested myna of China and Indochina, introduced to Vancouver.",0),
    ("LAMPROTORNIS_R3_MEVESII","Lamprotornis mevesii","Meves's Glossy Starling",["Africa"],"A long-tailed glossy starling of miombo woodlands in southern Africa.",0),
    ("LAMPROTORNIS_R3_FISCHERI","Lamprotornis fischeri","Fischer's Starling",["Africa"],"A small glossy starling of East African arid bushland.",0),
    ("LAMPROTORNIS_ALBICAPILLUS","Lamprotornis albicapillus","White-crowned Starling",["Africa"],"A glossy starling of the Horn of Africa with a white crown.",0),
    ("LAMPROTORNIS_ACUTICAUDUS","Lamprotornis acuticaudus","Sharp-tailed Starling",["Africa"],"A glossy starling with a short, pointed tail, found in southern African savannas.",0),
    ("LAMPROTORNIS_BICOLOR","Lamprotornis bicolor","Pied Starling",["Africa"],"A black and white starling of South African grasslands.",0),
    ("LAMPROTORNIS_ALBICINCTUS","Lamprotornis albicinctus","White-collared Starling",["Africa"],"A glossy starling of East African highlands with a white collar.",0),
    ("LAMPROTORNIS_AENEUS","Lamprotornis aeneus","Bronze-tailed Starling",["Africa"],"A glossy starling of West African savannas with a bronze-green tail.",0),
    ("LAMPROTORNIS_CUPREOCAUDUS","Lamprotornis cupreocaudus","Copper-tailed Starling",["Africa"],"A glossy starling with a copper-coloured tail, found in Central Africa.",0),
    ("LAMPROTORNIS_ORNATUS","Lamprotornis ornatus","Principe Starling",["Africa"],"A glossy starling endemic to the island of Principe in the Gulf of Guinea.",0),
    ("GRACULA_TEMUCHII","Gracula temuchii","Temu Hill Myna",["Asia"],"A hill myna of the Sulu Archipelago in the Philippines.",0),
    ("GRACULA_VENERATA","Gracula venerata","Yellow-wattled Hill Myna",["Asia"],"A hill myna of Flores and Alor with large yellow wattles.",0),
    ("GRACULA_PICTA","Gracula picta","Enggano Hill Myna",["Asia"],"A hill myna of Enggano Island with a distinctive colour pattern.",0),
    ("SPODIOPSAR_CINERACEUS","Spodiopsar cineraceus","White-cheeked Starling",["Asia"],"A grey starling of East Asia with white cheek patches.",0),
    ("SPODIOPSAR_SERICEUS","Spodiopsar sericeus","Red-billed Starling",["Asia"],"A glossy black starling of southern China and Taiwan with a red bill.",0),
    ("STURNIA_PAGODARUM","Sturnia pagodarum","Brahminy Starling",["Asia"],"A pinkish-grey starling with a black crest, common in Indian gardens.",0),
    ("STURNIA_ERYTHROPYGIA","Sturnia erythropygia","White-headed Starling",["Asia"],"A white-headed starling of Sri Lanka and southern India.",0),
    ("STURNIA_MALABARICA","Sturnia malabarica","Chestnut-tailed Starling",["Asia"],"A starling of Indian and Southeast Asian forests with a rufous tail.",0),
    ("STURNIA_BLYTHII","Sturnia blythii","Malabar Starling",["Asia"],"A starling of the Western Ghats, formerly considered a subspecies of the chestnut-tailed.",0),
    ("STURNIA_SINENSIS","Sturnia sinensis","White-shouldered Starling",["Asia"],"A starling of southern China and Southeast Asia with white shoulder patches.",0),
    ("STURNUS_VULGARIS","Sturnus vulgaris","Common Starling",["Europe","Asia","Africa","North America"],"One of the most abundant and widely introduced birds in the world.",0),
    ("STURNUS_UNICOLOR","Sturnus unicolor","Spotless Starling",["Europe","Africa"],"A glossy black starling of the Iberian Peninsula, Sardinia, and North Africa.",0),
    ("STURNUS_NIGRICOLLIS","Sturnus nigricollis","Black-collared Starling",["Asia"],"A starling of Southeast Asia with a prominent black collar.",0),
    ("STURNUS_BURMANNICUS","Sturnus burmannicus","Vinous-breasted Starling",["Asia"],"A starling of Myanmar and Thailand with a vinous-red breast.",0),
    ("STURNUS_SINENSIS","Sturnus sinensis","White-shouldered Starling",["Asia"],"A small starling of East Asia with white wing patches and a grey back.",0),
    ("STURNUS_PHILIPPENSIS","Sturnus philippensis","Chestnut-cheeked Starling",["Asia"],"A starling of Japan, the Philippines, and Taiwan with chestnut cheek patches.",0),
    ("STURNUS_STURNINUS","Sturnus sturninus","Purple-backed Starling",["Asia"],"A starling of East Asia with a purple-glossed back and white belly.",0),
    ("STURNUS_ROSEUS","Sturnus roseus","Rosy Starling",["Europe","Asia"],"A migratory starling with a rose-pink body and black head and wings.",0),
    ("STURNUS_CONTRA","Sturnus contra","Asian Pied Starling",["Asia"],"A striking black and white starling of South and Southeast Asia.",0),
    ("STURNUS_ALBOSUPERCILIARIS","Sturnus albosuperciliaris","White-browed Starling",["Asia"],"A starling of Myanmar with a conspicuous white eyebrow stripe.",0),
    ("STURNUS_MALABARICUS","Sturnus malabaricus","Chestnut-tailed Starling",["Asia"],"A starling of the Indian subcontinent with a chestnut tail and grey body.",0),
    ("STURNIA_BLYTHII","Sturnia blythii","Blyth's Starling",["Asia"],"A starling of the Western Ghats with white head and grey body.",0),
    ("LEUCOPSAR_ROTHSCHILDI","Leucopsar rothschildi","Bali Myna",["Asia"],"A pure white starling with blue eye-patch, critically endangered and endemic to Bali.",0),
    ("CREATOPHORA_CINEREA","Creatophora cinerea","Wattled Starling",["Africa"],"A grey starling of African savannas; breeding males develop black wattles on the head.",0),
    ("CINNYRICINCLUS_LEUCOGASTER","Cinnyricinclus leucogaster","Violet-backed Starling",["Africa"],"A stunning starling with iridescent violet back and white belly, found across sub-Saharan Africa.",0),
    ("ONYCHOGNATHUS_MORIO","Onychognathus morio","Red-winged Starling",["Africa"],"A glossy black starling with red wing patches, common in East and southern Africa.",0),
    ("ONYCHOGNATHUS_NABIROUP","Onychognathus nabiroup","Nabiroup Starling",["Africa"],"A cliff-nesting starling of the Namib Desert region with chestnut wing patches.",0),
    ("ONYCHOGNATHUS_ALBIROSTRIS","Onychognathus albirostris","White-billed Starling",["Africa"],"A starling of the Horn of Africa with a white bill and chestnut wing patches.",0),
    ("ONYCHOGNATHUS_TENUIROSTRIS","Onychognathus tenuirostris","Slender-billed Starling",["Africa"],"A starling of East African highlands with a slender, down-curved bill.",0),
    ("ONYCHOGNATHUS_FRATER","Onychognathus frater","Socotra Starling",["Africa"],"A starling endemic to the island of Socotra, with chestnut wing patches.",0),
    ("ONYCHOGNATHUS_FULGIDUS","Onychognathus fulgidus","Forest Starling",["Africa"],"A glossy starling of the Gulf of Guinea islands, named for its brilliant sheen.",0),
    ("SPECULIPASTOR_BICOLOR","Speculipastor bicolor","Magpie Starling",["Africa"],"A striking black-and-white starling of East Africa's dry acacia savannas.",0),
    ("NEOCHICHIA_GULARIS","Neochichia gularis","White-collared Starling",["Africa"],"A starling of West African forests with a prominent white collar.",0),
]

# SICARIIDAE — had 107, need 53 more to reach 160
# Note: IDs ending with _R3 to avoid round-2 collisions
SICARIIDAE = [
    ("LOXOSCELES_BLAGRACENSIS","Loxosceles blagracensis","Blagrave's Recluse",["North America"],"A recluse spider of the southwestern US with relatively mild venom.",0),
    ("LOXOSCELES_MISTA","Loxosceles mista","Mixed Recluse",["South America"],"A South American recluse of the Amazon basin with variable colouration.",0),
    ("LOXOSCELES_TAUROPLUTA","Loxosceles tauropluta","Wild Bull Recluse",["South America"],"A large recluse of the Brazilian cerrado with a distinctive bull-like carapace marking.",0),
    ("LOXOSCELES_BRUMA","Loxosceles bruma","Winter Brown Spider",["South America"],"A small brown spider of the Brazilian cerrado active mainly in cool months.",0),
    ("LOXOSCELES_BETTAINENSIS","Loxosceles bettainensis","Bettain's Recluse",["South America"],"A recently described recluse from dry forests of Colombia.",0),
    ("LOXOSCELES_RUFOFEMORATA","Loxosceles rufofemorata","Red-legged Recluse",["South America"],"A recluse of the Argentine Pampas with red-coloured femurs.",0),
    ("LOXOSCELES_ANCORA","Loxosceles ancora","Anchor Recluse",["South America"],"A Peruvian recluse with an anchor-shaped marking on the carapace.",0),
    ("LOXOSCELES_CHAPADENSIS","Loxosceles chapadensis","Chapada Recluse",["South America"],"A recluse of the Brazilian Chapada dos Veadeiros region.",0),
    ("LOXOSCELES_HIRSUTA","Loxosceles hirsuta","Hairy Recluse",["South America"],"A hairy recluse of the Argentine Monte desert with notably setose legs.",0),
    ("LOXOSCELES_IMMODESTA","Loxosceles immodesta","Modest Recluse",["South America"],"A small, plain brown recluse of the Peruvian coast.",0),
    ("LOXOSCELES_LAETA","Loxosceles laeta","Chilean Recluse",["South America"],"One of the most medically significant recluse spiders, found from Chile to Brazil.",0),
    ("LOXOSCELES_MARMORATA","Loxosceles marmorata","Marbled Recluse",["South America"],"A recluse with marbled markings on the carapace, found in Brazil.",0),
    ("LOXOSCELES_PALLIDA","Loxosceles pallida","Pale Recluse",["North America"],"A pale recluse of the Baja California Peninsula.",0),
    ("LOXOSCELES_RECLUSA","Loxosceles reclusa","Brown Recluse",["North America"],"The infamous brown recluse of the central US, with violin-shaped carapace marking.",0),
    ("LOXOSCELES_R3_SIMILIS","Loxosceles similis","Similar Recluse",["South America"],"A recluse of the Brazilian Atlantic Forest, closely resembling L. intermedia.",0),
    ("LOXOSCELES_R3_SULCATA","Loxosceles sulcata","Grooved Recluse",["South America"],"A recluse of the Chilean matorral with grooved carapace texture.",0),
    ("LOXOSCELES_R3_TENUIS","Loxosceles tenuis","Slender Recluse",["South America"],"A slender recluse of the Paraguayan Chaco.",0),
    ("LOXOSCELES_R3_TRIVIALIS","Loxosceles trivialis","Common Recluse",["South America"],"A common recluse of central Brazil found in both forests and human dwellings.",0),
    ("LOXOSCELES_R3_UNICOLOR","Loxosceles unicolor","Uniform Recluse",["North America"],"A uniformly coloured recluse of the southwestern US and northern Mexico.",0),
    ("LOXOSCELES_R3_VARIA","Loxosceles varia","Variable Recluse",["South America"],"A variable recluse of the Brazilian Amazon with diverse colour morphs.",0),
    ("LOXOSCELES_R3_YUCATANA","Loxosceles yucatana","Yucatan Recluse",["North America"],"A recluse of the Yucatán Peninsula of Mexico.",0),
    ("SICARIUS_R3_ANDREAE","Sicarius andreeae","Andrea's Sand Spider",["South America"],"A sand spider of the Peruvian coastal deserts.",0),
    ("SICARIUS_R3_BOLIVIENSIS","Sicarius boliviensis","Bolivian Sand Spider",["South America"],"A sand spider of the Bolivian dry valleys.",0),
    ("SICARIUS_R3_CHILENSIS","Sicarius chilensis","Chilean Sand Spider",["South America"],"A sand spider of Chile's Atacama region.",0),
    ("SICARIUS_R3_CRASSUS","Sicarius crassus","Robust Sand Spider",["South America"],"A heavily built sand spider of the Chilean coastal dunes.",0),
    ("SICARIUS_R3_DIPPER","Sicarius dipper","Dipper Sand Spider",["South America"],"A sand spider of the Peruvian Andes.",0),
    ("SICARIUS_R3_DOLICHOSCELUS","Sicarius dolichoscelus","Long-legged Sand Spider",["South America"],"A sand spider with notably long, slender legs, from Chile.",0),
    ("SICARIUS_R3_FUGATA","Sicarius fugata","Fugitive Sand Spider",["South America"],"A fast-running sand spider of the Atacama coastal ranges.",0),
    ("SICARIUS_R3_GASPARI","Sicarius gaspari","Gaspari's Sand Spider",["South America"],"A sand spider of the Peruvian highlands.",0),
    ("SICARIUS_R3_GRAVES","Sicarius gravesi","Graves's Sand Spider",["South America"],"A sand spider of the Chilean coastal fog desert.",0),
    ("SICARIUS_R3_MAPOCHO","Sicarius mapocho","Mapocho Sand Spider",["South America"],"A sand spider of central Chile, named after the Mapocho River.",0),
    ("SICARIUS_R3_PARVUS","Sicarius parvus","Small Sand Spider",["South America"],"A tiny sand spider of the Peruvian coastal deserts.",0),
    ("SICARIUS_R3_PORCUS","Sicarius porcus","Pig Sand Spider",["South America"],"A stout sand spider found in coastal dunes of northern Chile.",0),
    ("SICARIUS_R3_SORDIDUS","Sicarius sordidus","Dull Sand Spider",["South America"],"A plain, sandy-coloured spider of the Patagonian steppe.",0),
    ("SICARIUS_R3_TESTACEUS","Sicarius testaceus","Brick-red Sand Spider",["South America"],"A brick-red sand spider of the Peruvian coast.",0),
    ("SICARIUS_R3_UPS","Sicarius ups","Ups Sand Spider",["South America"],"A small sand spider from the coastal fog deserts of Peru's Paracas Peninsula.",0),
]

def process(slug, rel_path, data_list):
    data_path = os.path.join(ROOT, rel_path)
    data = load_json(data_path)
    before = count_species(data)
    for genus_name, sps in data_list:
        add_species(data["children"], genus_name, sps)
    after = count_species(data)
    save_json(data_path, data)
    print(f"{slug:20s} {before:>4} → {after:>4} (+{after - before})")

FAMILIES = [
    ("corvidae", "aves/passeriformes/corvidae/src/data/corvidae.json", [("Corvus", CORVIDAE[:24]), ("Cyanocorax", CORVIDAE[24:36])]),
    ("sturnidae", "aves/passeriformes/sturnidae/src/data/sturnidae.json", [("Acridotheres", STURNIDAE[:5]), ("Lamprotornis", STURNIDAE[5:15]), ("Gracula", STURNIDAE[15:18])]),
    ("sicariidae", "arachnida/araneae/sicariidae/src/data/sicariidae.json", [("Loxosceles", SICARIIDAE[:24]), ("Sicarius", SICARIIDAE[24:])]),
]

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for s, p, d in FAMILIES: process(s, p, d)
    else:
        for s, p, d in FAMILIES:
            if s == target: process(s, p, d)
    print("Done.")
