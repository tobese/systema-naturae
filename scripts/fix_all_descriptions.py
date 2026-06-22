#!/usr/bin/env python3
import json, glob

caprinae_data = {
    "Ammotragus lervia": {"cn": "Barbary Sheep", "cont": ["Africa"]},
    "Budorcas taxicolor": {"cn": "Takin", "cont": ["Asia"]},
    "Capra aegagrus": {"cn": "Wild Goat", "cont": ["Asia"]},
    "Capra caucasica": {"cn": "West Caucasian Tur", "cont": ["Asia"]},
    "Capra cylindricornis": {"cn": "East Caucasian Tur", "cont": ["Asia"]},
    "Capra falconeri": {"cn": "Markhor", "cont": ["Asia"]},
    "Capra hircus": {"cn": "Domestic Goat", "cont": ["Asia"]},
    "Capra ibex": {"cn": "Alpine Ibex", "cont": ["Europe"]},
    "Capra nubiana": {"cn": "Nubian Ibex", "cont": ["Africa", "Asia"]},
    "Capra pyrenaica": {"cn": "Spanish Ibex", "cont": ["Europe"]},
    "Capra sibirica": {"cn": "Siberian Ibex", "cont": ["Asia"]},
    "Capra walie": {"cn": "Walia Ibex", "cont": ["Africa"]},
    "Capricornis crispus": {"cn": "Japanese Serow", "cont": ["Asia"]},
    "Capricornis rubidus": {"cn": "Red Serow", "cont": ["Asia"]},
    "Capricornis sumatraensis": {"cn": "Mainland Serow", "cont": ["Asia"]},
    "Capricornis swinhoei": {"cn": "Taiwan Serow", "cont": ["Asia"]},
    "Capricornis thar": {"cn": "Himalayan Serow", "cont": ["Asia"]},
    "Hemitragus jemlahicus": {"cn": "Himalayan Tahr", "cont": ["Asia"]},
    "Naemorhedus baileyi": {"cn": "Red Goral", "cont": ["Asia"]},
    "Naemorhedus caudatus": {"cn": "Long-tailed Goral", "cont": ["Asia"]},
    "Naemorhedus goral": {"cn": "Himalayan Goral", "cont": ["Asia"]},
    "Naemorhedus griseus": {"cn": "Chinese Goral", "cont": ["Asia"]},
    "Nilgiritragus hylocrius": {"cn": "Nilgiri Tahr", "cont": ["Asia"]},
    "Oreamnos americanus": {"cn": "Mountain Goat", "cont": ["North America"]},
    "Ovibos moschatus": {"cn": "Muskox", "cont": ["North America"]},
    "Ovis ammon": {"cn": "Argali", "cont": ["Asia"]},
    "Ovis aries": {"cn": "Domestic Sheep", "cont": ["Asia"]},
    "Ovis canadensis": {"cn": "Bighorn Sheep", "cont": ["North America"]},
    "Ovis dalli": {"cn": "Dall Sheep", "cont": ["North America"]},
    "Ovis gmelini": {"cn": "Mouflon", "cont": ["Asia"]},
    "Ovis nivicola": {"cn": "Snow Sheep", "cont": ["Asia"]},
    "Ovis vignei": {"cn": "Urial", "cont": ["Asia"]},
    "Pantholops hodgsonii": {"cn": "Tibetan Antelope", "cont": ["Asia"]},
    "Pseudois nayaur": {"cn": "Bharal", "cont": ["Asia"]},
    "Pseudois schaeferi": {"cn": "Dwarf Blue Sheep", "cont": ["Asia"]},
    "Rupicapra pyrenaica": {"cn": "Pyrenean Chamois", "cont": ["Europe"]},
    "Rupicapra rupicapra": {"cn": "Chamois", "cont": ["Europe"]},
}

felidae_missing = {
    "Felis chaus": {"cn": "Jungle Cat", "cont": ["Asia", "Africa"]},
    "Leopardus colocola": {"cn": "Pampas Cat", "cont": ["South America"]},
    "Leopardus tigrinus": {"cn": "Oncilla", "cont": ["South America"]},
    "Lynx canadensis": {"cn": "Canada Lynx", "cont": ["North America"]},
    "Lynx rufus": {"cn": "Bobcat", "cont": ["North America"]},
    "Puma yagouaroundi": {"cn": "Jaguarundi", "cont": ["North America", "South America"]},
}

canidae_missing = {
    "Atelocynus microtis": {"cn": "Short-eared Dog", "cont": ["South America"]},
    "Dusicyon australis": {"cn": "Falkland Islands Wolf", "cont": ["South America"]},
    "Lycalopex culpaeus": {"cn": "Culpeo", "cont": ["South America"]},
    "Lycalopex fulvipes": {"cn": "Darwin's Fox", "cont": ["South America"]},
    "Lycalopex griseus": {"cn": "South American Grey Fox", "cont": ["South America"]},
    "Lycalopex gymnocercus": {"cn": "Pampas Fox", "cont": ["South America"]},
    "Lycalopex sechurae": {"cn": "Sechuran Fox", "cont": ["South America"]},
    "Lycalopex vetulus": {"cn": "Hoary Fox", "cont": ["South America"]},
    "Speothos venaticus": {"cn": "Bush Dog", "cont": ["South America"]},
}

suidae_missing = {
    "Babyrousa babyrussa": {"cont": ["Asia"]},
}

rallidae_missing = {
    "Gallicrex cinerea": {"cn": "Watercock", "cont": ["Asia"]},
    "Gallirallus striatus": {"cn": "Slaty-breasted Rail", "cont": ["Asia"]},
}

files = glob.glob("**/src/data/*.json", recursive=True)
files = [f for f in files if not any(e in f for e in ["unified-taxonomy", "node_modules", "portal/data", "shared/data"])]

total_fixed_cn = 0
total_fixed_cont = 0
total_fixed_desc = 0

for path in sorted(files):
    try:
        with open(path) as f:
            data = json.load(f)
        if data.get("rank") != "FAMILY":
            continue
        family = data.get("name", "")
        
        extra = {}
        if family == "Caprinae": extra = caprinae_data
        elif family == "Felidae": extra = felidae_missing
        elif family == "Canidae": extra = canidae_missing
        elif family == "Suidae": extra = suidae_missing
        elif family == "Rallidae": extra = rallidae_missing
        
        fixed_cn = [0]
        fixed_cont = [0]
        fixed_desc = [0]
        
        def walk(node, genus=""):
            if isinstance(node, dict):
                if node.get("rank") == "GENUS":
                    genus = node["name"]
                if node.get("rank") == "SPECIES":
                    name = node["name"]
                    if name in extra:
                        if not node.get("commonName") and "cn" in extra[name]:
                            node["commonName"] = extra[name]["cn"]
                            fixed_cn[0] += 1
                        if not node.get("continents") and "cont" in extra[name]:
                            node["continents"] = extra[name]["cont"]
                            fixed_cont[0] += 1
                    
                    desc = node.get("description", "")
                    if not desc or len(desc) < 30:
                        cn = node.get("commonName", "")
                        conts = node.get("continents", [])
                        lineage = node.get("lineage", "")
                        cont_str = " and ".join(conts) if conts else "its native"
                        region = "region" if len(conts) <= 1 else "regions"
                        
                        if lineage and lineage not in ("", genus):
                            nd = f"{name}{' ('+cn+')' if cn else ''} is a {lineage.lower()} species found in {cont_str} {region}."
                        elif cn:
                            nd = f"{name} ({cn}) is a {family.lower()} species found in {cont_str} {region}."
                        else:
                            nd = f"{name} is a {family.lower()} species found in {cont_str} {region}."
                        node["description"] = nd
                        fixed_desc[0] += 1
                for ch in node.get("children", []):
                    walk(ch, genus)
        
        walk(data)
        
        if fixed_cn[0] > 0 or fixed_cont[0] > 0 or fixed_desc[0] > 0:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"{family:20} CN:{fixed_cn[0]} Cont:{fixed_cont[0]} Desc:{fixed_desc[0]}")
            total_fixed_cn += fixed_cn[0]
            total_fixed_cont += fixed_cont[0]
            total_fixed_desc += fixed_desc[0]
    except Exception as e:
        print(f"ERROR {path}: {e}")

print(f"\nTotal: {total_fixed_cn} common names, {total_fixed_cont} continents, {total_fixed_desc} descriptions")
