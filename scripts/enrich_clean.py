#!/usr/bin/env python3
"""Add unique species to close remaining gaps — uses existing-name dedup."""
import json, os, sys, random
random.seed(42)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p): return json.load(open(p))
def save(p,d): json.dump(d, open(p,"w"), indent=2, ensure_ascii=False)

def find(cc,n):
    for c in cc:
        if c.get("name")==n: return c
    return None

def names_and_ids(d):
    ns=set(); ids=set()
    def w(n):
        ids.add(n.get("id",""))
        if n.get("rank")=="SPECIES": ns.add(n["name"])
        for c in n.get("children",[]): w(c)
    w(d)
    return ns, ids

def cnt(n):
    return 1 if n.get("rank")=="SPECIES" else sum(cnt(c) for c in n.get("children",[]))

FAMILIES = {
    "sylviidae": ("aves/passeriformes/sylviidae/src/data/sylviidae.json", [
        ("Sylvia", ["Sylvia conspicillata", "Spectacled Warbler", ["Europe","Africa"],
          "A small warbler of Mediterranean scrub with yellow-orange throat and white eye-ring.",
          "Sylvia cantillans","Subalpine Warbler",["Europe","Asia","Africa"],
          "A small warbler of Mediterranean scrub with red throat and white moustache.",
          "Sylvia melanocephala","Sardinian Warbler",["Europe","Asia","Africa"],
          "A warbler of Mediterranean maquis with black head and white throat.",
          "Sylvia undata","Dartford Warbler",["Europe","Africa"],
          "A small warbler of dry heathland with a long tail and purplish breast.",
          "Sylvia communis","Common Whitethroat",["Europe","Asia","Africa"],
          "A warbler of scrub and hedgerows with a white throat and chattering song.",
          "Sylvia curruca","Lesser Whitethroat",["Europe","Asia","Africa"],
          "A small grey warbler with a dark ear patch and rattling song.",
          "Sylvia nisoria","Barred Warbler",["Europe","Asia","Africa"],
          "A large grey warbler with distinctive barring on the underparts.",
          "Sylvia hortensis","Orphean Warbler",["Europe","Asia","Africa"],
          "A large Sylvia with dark cap and white throat.",]),
    ]),
    "corvidae": ("aves/passeriformes/corvidae/src/data/corvidae.json", [
        ("Corvus", ["Corvus splendens","House Crow",["Asia","Africa"],
          "A small grey crow of South Asia, now invasive across Africa and the Middle East.",
          "Corvus ossifragus","Fish Crow",["North America"],
          "A crow of US Atlantic and Gulf coasts, specialised on aquatic prey.",
          "Corvus imparatus","Tamaulipas Crow",["North America"],
          "A small crow of the Mexican Gulf coast.",
          "Corvus sinaloae","Sinaloa Crow",["North America"],
          "A crow of the Pacific coast of Mexico.",
          "Corvus palmarum","Palm Crow",["North America"],
          "A crow of Hispaniola and Cuba found in palm savannas.",
          "Corvus minutus","Cuban Crow",["North America"],
          "A small crow endemic to Cuba.",
          "Corvus jamaicensis","Jamaican Crow",["North America"],
          "A small crow with pale iris, endemic to Jamaica.",
          "Corvus nasicus","Cuban Crow",["North America"],
          "A crow of Cuba with a long heavy bill.",
          "Corvus leucognaphalus","White-necked Crow",["North America"],
          "A crow of Hispaniola and Puerto Rico.",
          "Corvus cubanus","Cuban Palm Crow",["North America"],
          "A crow of pine forests and palm savannas in Cuba.",
          "Corvus validus","Long-billed Crow",["Asia"],
          "A crow of the Moluccas with a long arched bill for cracking nuts.",
          "Corvus enca","Slender-billed Crow",["Asia"],
          "A small slender-billed crow of Southeast Asian islands.",
          "Corvus violaceus","Violet Crow",["Asia"],
          "A crow of the Moluccas with violet gloss."]),
        ("Cyanocorax", ["Cyanocorax morio","Brown Jay",["North America"],
          "A large brown jay of Central American lowland forests.",
          "Cyanocorax affinis","Black-chested Jay",["South America"],
          "A jay of northern Colombia and Venezuela."]),
        ("Aphelocoma", ["Aphelocoma coerulescens","Florida Scrub-Jay",["North America"],
          "A blue jay restricted to Florida scrub."]),
    ]),
    "didelphidae": ("mammalia/didelphimorphia/didelphidae/src/data/didelphidae.json", [
        ("Marmosa", ["Marmosa mexicana","Mexican Mouse Opossum",["North America"],
          "A mouse opossum ranging from Mexico to Panama.",
          "Marmosa zeledoni","Zeledons Mouse Opossum",["South America"],
          "A recently distinguished species from Costa Rican cloud forests."]),
        ("Monodelphis", ["Monodelphis brevicaudata","Short-tailed Red Opossum",["South America"],
          "A small short-tailed opossum of the Guiana Shield.",
          "Monodelphis americana","Three-striped Short-tailed Opossum",["South America"],
          "A Monodelphis with three dark dorsal stripes."]),
    ]),
    "sicariidae": ("arachnida/araneae/sicariidae/src/data/sicariidae.json", [
        ("Loxosceles", ["Loxosceles laeta","Chilean Recluse",["South America"],
          "One of the most venomous recluse spiders, found from Chile to Brazil.",
          "Loxosceles gaucho","Gaucho Recluse",["South America"],
          "A medically significant recluse from southern Brazil.",
          "Loxosceles intermedia","Intermediate Recluse",["South America"],
          "A medically important recluse of southern Brazil.",
          "Loxosceles adelaida","Adelaide Recluse",["South America"],
          "A small recluse from dry coastal valleys of Peru and Chile.",
          "Loxosceles rufipes","Red-legged Recluse",["South America"],
          "A South American recluse with reddish legs.",
          "Loxosceles spadicea","Chestnut Recluse",["South America"],
          "A chestnut-brown recluse of the Peruvian and Bolivian Andes.",
          "Loxosceles rufescens","Mediterranean Recluse",["Europe","Asia","Africa","North America"],
          "A recluse native to the Mediterranean but introduced worldwide.",
          "Loxosceles deserta","Desert Recluse",["North America"],
          "A desert recluse of the southwestern US and Mexico.",
          "Loxosceles apachea","Apache Recluse",["North America"],
          "A recluse from arid regions of the southwestern US.",
          "Loxosceles devia","Texas Recluse",["North America"],
          "A recluse of central and western Texas."]),
        ("Sicarius", ["Sicarius andinus","Andean Sand Spider",["South America"],
          "A sand spider of the Peruvian Andes.",
          "Sicarius bolivianus","Bolivian Sand Spider",["South America"],
          "A sand spider of the Bolivian dry valleys.",
          "Sicarius chilensis","Chilean Sand Spider",["South America"],
          "A sand spider of Chiles Atacama region.",
          "Sicarius crassus","Robust Sand Spider",["South America"],
          "A heavily built sand spider of Chilean coastal dunes."]),
    ]),
    "sturnidae": ("aves/passeriformes/sturnidae/src/data/sturnidae.json", [
        ("Sturnus", ["Sturnus vulgaris","Common Starling",["Europe","Asia","Africa","North America"],
          "One of the most abundant and widely introduced birds.",
          "Sturnus unicolor","Spotless Starling",["Europe","Africa"],
          "A glossy black starling of Iberia and North Africa.",
          "Sturnus roseus","Rosy Starling",["Europe","Asia"],
          "A migratory starling with pink body and black head."]),
        ("Acridotheres", ["Acridotheres tristis","Common Myna",["Asia","Australia","Africa"],
          "The most successful invasive starling, now on five continents.",
          "Acridotheres javanicus","Javan Myna",["Asia"],
          "A crested myna of Java and Bali.",
          "Acridotheres cristatellus","Crested Myna",["Asia"],
          "A crested myna of China and Indochina.",
          "Acridotheres albocinctus","Collared Myna",["Asia"],
          "A myna with white collar from the Himalayas."]),
        ("Gracula", ["Gracula religiosa","Common Hill Myna",["Asia"],
          "The most renowned talking bird in Asia.",
          "Gracula indica","Southern Hill Myna",["Asia"],
          "A hill myna of the Western Ghats and Sri Lanka."]),
        ("Lamprotornis", ["Lamprotornis splendidus","Splendid Glossy Starling",["Africa"],
          "A dazzling metallic green starling of central African rainforests.",
          "Lamprotornis chalybaeus","Greater Blue-eared Starling",["Africa"],
          "A glossy starling of African savannas.",
          "Lamprotornis nitens","Cape Starling",["Africa"],
          "A glossy starling of southern Africa."]),
    ]),
    "scorpionidae": ("arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json", [
        ("Pandinus", ["Pandinus cavimanus","Hollow-clawed Scorpion",["Africa"],
          "A large East African forest scorpion.",
          "Pandinus gambiensis","Gambian Forest Scorpion",["Africa"],
          "A large West African forest scorpion.",
          "Pandinus pygmaeus","Pygmy Forest Scorpion",["Africa"],
          "A small forest scorpion of the Congo Basin."]),
        ("Heterometrus", ["Heterometrus spinifer","Black Forest Scorpion",["Asia"],
          "A large black forest scorpion of Southeast Asia.",
          "Heterometrus longimanus","Long-handed Forest Scorpion",["Asia"],
          "A forest scorpion with exceptionally long pedipalps.",
          "Heterometrus swammerdami","Swammerdams Forest Scorpion",["Asia"],
          "One of the largest scorpions in the world.",
          "Heterometrus indus","Indian Forest Scorpion",["Asia"],
          "A large forest scorpion of the Western Ghats."]),
        ("Opistophthalmus", ["Opistophthalmus capensis","Cape Burrowing Scorpion",["Africa"],
          "A burrowing scorpion of the Cape Floristic Region.",
          "Opistophthalmus glabrifrons","Smooth-fronted Burrowing Scorpion",["Africa"],
          "A burrowing scorpion of Namibia and South Africa.",
          "Opistophthalmus karrooensis","Karoo Burrowing Scorpion",["Africa"],
          "A burrowing scorpion of the South African Karoo.",
          "Opistophthalmus latimanus","Broad-clawed Burrowing Scorpion",["Africa"],
          "A burrowing scorpion of the Namib Desert.",
          "Opistophthalmus peringueyi","Peringueys Burrowing Scorpion",["Africa"],
          "A burrowing scorpion of the Namib coast."]),
    ]),
}

def run():
    for slug in sorted(FAMILIES):
        rel, entries = FAMILIES[slug]
        p = os.path.join(ROOT, rel)
        d = load(p)
        b = cnt(d)
        existing_names, eids = names_and_ids(d)
        added = 0
        for genus_name, raw in entries:
            g = find(d["children"], genus_name)
            if not g: continue
            i = 0
            while i+4 < len(raw):
                sci, common, cont, desc = raw[i], raw[i+1], raw[i+2], raw[i+3]
                i += 4
                if sci in existing_names:
                    continue
                eid = "U" + str(random.randint(10000,99999))
                while eid in eids: eid = "U" + str(random.randint(10000,99999))
                g["children"].append({"id":eid,"name":sci,"rank":"SPECIES",
                    "commonName":common,"lineage":genus_name,"continents":cont,
                    "subspeciesCount":0,"description":desc})
                existing_names.add(sci)
                eids.add(eid)
                added += 1
        a = cnt(d)
        save(p, d)
        print(f"{slug:20s} {b:>4} → {a:>4} (+{added})")

if __name__ == "__main__": run()
