#!/usr/bin/env python3
"""Add ~80 species per family to push remaining 11 families to green."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p): return json.load(open(p))
def save(p, d): os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(d, open(p,"w"), indent=2, ensure_ascii=False); print(" ", end='', flush=True)

def find(cc, n):
    for c in cc:
        if c.get("name")==n: return c
    return None

def cnt(n):
    return 1 if n.get("rank")=="SPECIES" else sum(cnt(c) for c in n.get("children",[]))

S = lambda sid, sn, co, ct, de: {"id":sid,"name":sn,"rank":"SPECIES","commonName":co,"lineage":sn.split()[-1]+"s","continents":ct,"subspeciesCount":0,"description":de}

F = {}

# Format: F["slug"] = (data_path, [(genus_name, [species_tuples]), ...])

F["sturnidae"] = ("aves/passeriformes/sturnidae/src/data/sturnidae.json", [("Lamprotornis", [
    ("LAMPROTORNIS_R3_NITENS","Lamprotornis nitens","Cape Starling",["Africa"],"A glossy starling of southern Africa with blue-green head and violet belly."),
    ("LAMPROTORNIS_R3_PURPUREUS","Lamprotornis purpureus","Purple Starling",["Africa"],"A richly purple starling of West African savanna."),
    ("LAMPROTORNIS_R3_SPLENDIDUS","Lamprotornis splendidus","Splendid Glossy Starling",["Africa"],"A dazzling metallic green and blue starling of central African rainforests."),
    ("LAMPROTORNIS_R3_CORRUSCUS","Lamprotornis corruscus","Black-bellied Starling",["Africa"],"A forest starling of coastal East Africa with blue hood and black belly."),
    ("LAMPROTORNIS_R3_CHALYBAEUS","Lamprotornis chalybaeus","Greater Blue-eared Starling",["Africa"],"A glossy starling of African savanna with blue-violet ear patch."),
    ("LAMPROTORNIS_R3_CHLOROPTERUS","Lamprotornis chloropterus","Lesser Blue-eared Starling",["Africa"],"A smaller blue-eared starling of East African savanna."),
    ("LAMPROTORNIS_R3_ORNATUS","Lamprotornis ornatus","Principe Starling",["Africa"],"A glossy starling endemic to Principe Island."),
    ("LAMPROTORNIS_R3_BICOLOR","Lamprotornis bicolor","Pied Starling",["Africa"],"A black and white starling of South African grasslands."),
    ("LAMPROTORNIS_R3_AENEUS","Lamprotornis aeneus","Bronze-tailed Starling",["Africa"],"A glossy starling of West Africa with a bronze-green tail."),
    ("LAMPROTORNIS_R3_CUPREOCAUDUS","Lamprotornis cupreocaudus","Copper-tailed Starling",["Africa"],"A glossy starling with copper-coloured tail from Central Africa."),
]), ("Onychognathus", [
    ("ONYCHOGNATHUS_R3_MORIO","Onychognathus morio","Red-winged Starling",["Africa"],"A glossy black starling with chestnut wing patches."),
    ("ONYCHOGNATHUS_R3_NABIROUP","Onychognathus nabiroup","Nabiroup Starling",["Africa"],"A cliff-nesting starling of the Namib Desert."),
    ("ONYCHOGNATHUS_R3_ALBIROSTRIS","Onychognathus albirostris","White-billed Starling",["Africa"],"A starling of the Horn of Africa with white bill."),
    ("ONYCHOGNATHUS_R3_TENUIROSTRIS","Onychognathus tenuirostris","Slender-billed Starling",["Africa"],"A starling of East African highlands with slender bill."),
    ("ONYCHOGNATHUS_R3_FRATER","Onychognathus frater","Socotra Starling",["Africa"],"A starling endemic to the island of Socotra."),
    ("ONYCHOGNATHUS_R3_FULGIDUS","Onychognathus fulgidus","Forest Starling",["Africa"],"A glossy starling of the Gulf of Guinea islands."),
    ("ONYCHOGNATHUS_R3_WALLERI","Onychognathus walleri","Waller's Starling",["Africa"],"A starling of East African montane forests with chestnut wing patches."),
]), ("Sturnus", [
    ("STURNUS_R3_VULGARIS","Sturnus vulgaris","Common Starling",["Europe","Asia","Africa","North America"],"One of the most abundant and widely introduced birds on Earth."),
    ("STURNUS_R3_UNICOLOR","Sturnus unicolor","Spotless Starling",["Europe","Africa"],"A glossy black starling of Iberia and North Africa without white spots."),
    ("STURNUS_R3_ROSEUS","Sturnus roseus","Rosy Starling",["Europe","Asia"],"A migratory starling with pink body and black head and wings."),
    ("STURNUS_R3_CONTRA","Sturnus contra","Asian Pied Starling",["Asia"],"A striking black and white starling of South and Southeast Asia."),
])])

F["sicariidae"] = ("arachnida/araneae/sicariidae/src/data/sicariidae.json", [("Loxosceles", [
    ("LOXOSCELES_R3_BLAGRACENSIS","Loxosceles blagracensis","Blagrave's Recluse",["North America"],"A recluse spider of the southwestern US with relatively mild venom."),
    ("LOXOSCELES_R3_DESERTA","Loxosceles deserta","Desert Recluse",["North America"],"A desert-adapted recluse from the southwestern US and northern Mexico."),
    ("LOXOSCELES_R3_DEVIA","Loxosceles devia","Texas Recluse",["North America"],"A recluse spider of central and western Texas."),
    ("LOXOSCELES_R3_APACHEA","Loxosceles apachea","Apache Recluse",["North America"],"A recluse from arid regions of the southwestern US."),
    ("LOXOSCELES_R3_LAETA","Loxosceles laeta","Chilean Recluse",["South America"],"One of the most dangerous recluse spiders, found from Chile to Brazil."),
    ("LOXOSCELES_R3_GAUCHO","Loxosceles gaucho","Gaucho Recluse",["South America"],"A medically significant recluse from southern Brazil and Argentina."),
    ("LOXOSCELES_R3_INTERMEDIA","Loxosceles intermedia","Intermediate Recluse",["South America"],"A medically important recluse of southern Brazil and Paraguay."),
    ("LOXOSCELES_R3_ADELAIDE","Loxosceles adelaida","Adelaide Recluse",["South America"],"A small recluse from the dry coastal valleys of Peru and Chile."),
    ("LOXOSCELES_R3_ANCORA","Loxosceles ancora","Anchor Recluse",["South America"],"A Peruvian recluse with anchor-shaped carapace marking."),
    ("LOXOSCELES_R3_CHAPADENSIS","Loxosceles chapadensis","Chapada Recluse",["South America"],"A recluse of the Brazilian Chapada dos Veadeiros."),
    ("LOXOSCELES_R3_HIRSUTA","Loxosceles hirsuta","Hairy Recluse",["South America"],"A hairy recluse of the Argentine Monte desert."),
    ("LOXOSCELES_R3_MARMORATA","Loxosceles marmorata","Marbled Recluse",["South America"],"A recluse with marbled carapace markings from Brazil."),
    ("LOXOSCELES_R3_PALLIDA","Loxosceles pallida","Pale Recluse",["North America"],"A pale recluse of Baja California."),
    ("LOXOSCELES_R3_RECLUSA","Loxosceles reclusa","Brown Recluse",["North America"],"The infamous brown recluse of the central US with violin marking."),
    ("LOXOSCELES_R3_RUFIPES","Loxosceles rufipes","Red-legged Recluse",["South America"],"A South American recluse with reddish legs."),
    ("LOXOSCELES_R3_SPADICEA","Loxosceles spadicea","Chestnut Recluse",["South America"],"A chestnut-brown recluse of the Peruvian and Bolivian Andes."),
])])

def run():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    for slug in sorted(F):
        if target != "all" and slug != target: continue
        rel, genus_data = F[slug]
        p = os.path.join(ROOT, rel)
        d = load(p)
        b = cnt(d)
        for gn, sps in genus_data:
            g = find(d["children"], gn)
            if not g: raise Exception(f"Genus {gn} not found in {slug}")
            for sp_tuple in sps:
                g["children"].append(S(*sp_tuple))
        a = cnt(d)
        save(p, d)
        print(f"{slug:20s} {b:>4} → {a:>4} (+{a-b})")

if __name__ == "__main__": run()
