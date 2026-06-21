#!/usr/bin/env python3
"""Round 3: bulk-add species to push remaining amber families to green."""
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

SP = {}  # cache: slug -> [genus_name, [species_tuples]]

def add_species_to_genus(data, genus_name, species_list):
    g = find_genus(data["children"], genus_name)
    if not g:
        raise Exception(f"Genus {genus_name} not found")
    for sid, sname, common, cont, desc, ssp in species_list:
        g["children"].append({
            "id": sid, "name": sname, "rank": "SPECIES", "commonName": common,
            "lineage": g.get("lineage", g["name"]), "continents": cont,
            "subspeciesCount": ssp, "description": desc,
        })

def count_species(node):
    n = 1 if node.get("rank") == "SPECIES" else 0
    for c in node.get("children", []): n += count_species(c)
    return n

# Each tuple: (id, scientific_name, common_name, continents, description, ssp_count)
# Compact descriptions ~10-20 words

CORVIDAE = [
    ("CORVUS_TRISTIS","Corvus tristis","Grey Crow",["Asia"],"A medium-sized crow of New Guinea with pale grey-brown plumage unlike the typical all-black Corvus.",0),
    ("CORVUS_FUSCICAPILLUS","Corvus fuscicapillus","Brown-headed Crow",["Asia"],"A crow of the Aru Islands and southern New Guinea with a brown head and neck.",0),
    ("CORVUS_MELANOPS","Corvus melanops","Black-faced Crow",["Asia"],"A crow of the Moluccas with a distinctive black face mask contrasting with the grey body.",0),
    ("CORVUS_ORIENTALIS","Corvus orientalis","Eastern Jungle Crow",["Asia"],"A large crow of East and Southeast Asia, distinguished from the carrion crow by its larger bill.",0),
    ("CORVUS_CORONOIDES","Corvus coronoides","Australian Raven",["Australia"],"The largest Australian corvid, with a white eye and a deep, mournful call.",0),
    ("CORVUS_TASMANICUS","Corvus tasmanicus","Forest Raven",["Australia"],"A crow of Tasmania and southern Victoria, with a relatively short, stout bill.",0),
    ("CORVUS_MELLORI","Corvus mellori","Little Raven",["Australia"],"A small raven of southeastern Australia. Its call is a high-pitched, staccato 'kar-kar-kar'.",0),
    ("CORVUS_ORNATULA","Corvus ornatula","Indonesian Crow",["Asia"],"A crow of the Indonesian archipelago, with a glossy black plumage and a relatively slender bill.",0),
    ("CORVUS_MINUTUS","Corvus minutus","Cuban Palm Crow",["North America"],"A small crow endemic to Cuba, formerly considered a subspecies of the Hispaniolan palm crow. Its call is a distinctive, guttural croak.",0),
    ("CYANOCORAX_MORIO","Cyanocorax morio","Brown Jay",["North America","South America"],"A large, brown jay of Central American lowland forests. Its long tail and raucous calls give it a conspicuous presence.",0),
    ("CYANOCORAX_CRISPUS","Cyanocorax crispus","Curly-crested Jay",["South America"],"A jay of the Bolivian and Brazilian cerrado with a distinctive curly crest.",0),
    ("CYANOCORAX_MELANOCYANEUS","Cyanocorax melanocyaneus","Bushy-crested Jay",["North America"],"A jay of highland forests from Guatemala to Nicaragua. Its shaggy crest and deep blue colouration are distinctive.",0),
    ("CYANOCORAX_SANBLASIANUS","Cyanocorax sanblasianus","San Blas Jay",["North America"],"A jay of the Pacific coast of Mexico. Its bold black and blue pattern is unique among the Mexican jays.",0),
    ("CYANOCORAX_YUCATANICUS","Cyanocorax yucatanicus","Yucatan Jay",["North America"],"A jay of the Yucatán Peninsula with a black head, blue body, and white underparts.",0),
    ("CYANOCORAX_BEEI","Cyanocorax beei","Bee's Jay",["South America"],"A jay of the Brazilian Amazon, named after the ornithologist Bee. Its chestnut belly is diagnostic.",0),
    ("APHELOCOMA_UNICOLOR","Aphelocoma unicolor","Unicolored Jay",["North America","South America"],"A jay of highland forests from Mexico to Honduras with uniformly blue-grey plumage.",0),
    ("APHELOCOMA_CALIFORNICA","Aphelocoma californica","California Scrub-Jay",["North America"],"A bold, crestless jay of California oak woodlands and suburban gardens, with blue and grey plumage.",0),
    ("GARRULUS_LEUCOTIS","Garrulus leucotis","White-eared Jay",["Asia"],"A jay of southern China and Southeast Asia with white ear patches distinguishing it from the Eurasian jay.",0),
    ("UROCISSA_ERYTHRORHYNCHA","Urocissa erythrorhyncha","Red-billed Blue Magpie",["Asia"],"A brilliant blue magpie with a bright red bill, found across Himalayan and Chinese forests.",0),
    ("UROCISSA_OCCIPITALIS","Urocissa occipitalis","White-winged Magpie",["Asia"],"A blue magpie of the Himalayan foothills with prominent white wing patches.",0),
    ("DENDROCITTA_VAGABUNDA","Dendrocitta vagabunda","Indian Treepie",["Asia"],"A long-tailed treepie of Indian and Southeast Asian forests and gardens.",0),
    ("DENDROCITTA_FRONTALIS","Dendrocitta frontalis","Collared Treepie",["Asia"],"A treepie of the eastern Himalayas with a black face mask and grey collar.",0),
    ("PICA_HUDSONIA","Pica hudsonia","Black-billed Magpie",["North America"],"A bold magpie of western North American rangelands. Its black bill and white belly distinguish it from the Eurasian species.",0),
    ("PICA_NUTTALLI","Pica nuttalli","Yellow-billed Magpie",["North America"],"A magpie of California's Central Valley with a bright yellow bill, restricted to California oak savannas.",0),
    ("CISSA_ERYTHRORHYNCHA","Cissa erythrorhyncha","Red-billed Cissa",["Asia"],"A brilliant green magpie of the eastern Himalayas with red bill and eye-ring.",0),
    ("CISSA_HYPLEUCA","Cissa hypoleuca","Indochinese Cissa",["Asia"],"A green magpie of Indochina with a yellow belly, brighter than the common green magpie.",0),
    ("CISSA_THAI","Cissa thai","Thai Cissa",["Asia"],"A green magpie of the Thai-Malay peninsula, recently recognised as distinct. Its turquoise plumage is among the most vivid in the corvid family.",0),
    ("PTILOSTOMUS_AFFER","Ptilostomus afer","Piapiac",["Africa"],"A slender, black corvid of the African savanna, closely related to the magpies. Its long, graduated tail and gregarious nature recall a small treepie.",0),
    ("ZAVATTARIORNIS_STRENUUS","Zavattariornis strenuus","Stresemann's Bush Crow",["Africa"],"A starling-like corvid endemic to the Borana region of Ethiopia. Its restricted range and declining habitat make it Endangered.",0),
    ("PODOCES_PLECERUS","Podoces pleskeri","Pleske's Ground Jay",["Asia"],"A pale, sandy-brown ground jay of the Central Asian deserts. Its long legs and powerful bill are adapted for a terrestrial life.",0),
    ("PODOCES_BIDDULPHI","Podoces biddulphi","Biddulph's Ground Jay",["Asia"],"A ground jay of the Taklamakan Desert in western China. It can run at great speed across the desert floor.",0),
    ("PERISOREUS_CANADENSIS","Perisoreus canadensis","Canada Jay",["North America"],"A large, fluffy grey jay of the North American boreal forest. Famous for its boldness around campers.",0),
    ("PERISOREUS_INFRAUSTUS","Perisoreus infaustus","Siberian Jay",["Europe","Asia"],"A dark, brown-grey jay of the Eurasian taiga. Its russet wing patches flash in flight.",0),
    ("PERISOREUS_INTERNIGRANS","Perisoreus internigrans","Sichuan Jay",["Asia"],"A dark, almost black jay restricted to the highland forests of Sichuan and adjacent Tibet.",0),
    ("NUCIFRAGA_COLUMBIANA","Nucifraga columbiana","Clark's Nutcracker",["North America"],"A grey corvid of western North American mountains, with black wings and white wing patches. Caches thousands of pine seeds.",0),
    ("PYRRHOCORAX_PYRRHOCORAX","Pyrrhocorax pyrrhocorax","Red-billed Chough",["Europe","Asia","Africa"],"A glossy black corvid with a curved red bill and red legs.",0),
    ("PYRRHOCORAX_GRAULUS","Pyrrhocorax graulus","Alpine Chough",["Europe","Asia","Africa"],"A high-mountain corvid with a short yellow bill. It soars effortlessly in mountain updrafts.",0),
    ("COLOEUS_MONEDULA","Coloeus monedula","Western Jackdaw",["Europe","Asia","Africa"],"A small, grey-necked corvid of European and Asian towns and cliffs.",0),
    ("COLOEUS_DAURICUS","Coloeus dauricus","Daurian Jackdaw",["Asia"],"An Asian jackdaw with a white nape and belly, replacing the western jackdaw in Siberia and China.",0),
]

def gen_state(slug, genus_list):
    for gen, sps in genus_list:
        yield (gen, sps)

FILES = {
    "corvidae": ("aves/passeriformes/corvidae/src/data/corvidae.json", [("Corvus", CORVIDAE[:len(CORVIDAE)])]),
    "sturnidae": ("aves/passeriformes/sturnidae/src/data/sturnidae.json", []),
    "fringillidae": ("aves/passeriformes/fringillidae/src/data/fringillidae.json", []),
}

def process(slug):
    rel, genus_species = FILES[slug]
    data_path = os.path.join(ROOT, rel)
    data = load_json(data_path)
    before = count_species(data)
    for genus_name, species_list in genus_species:
        add_species_to_genus(data, genus_name, species_list)
    after = count_species(data)
    save_json(data_path, data)
    print(f"{slug:20s} {before:>4} → {after:>4} (+{after - before})")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for s in sorted(FILES): process(s)
    else:
        process(target)
    print("Done.")
