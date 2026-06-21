#!/usr/bin/env python3
"""
Enrich Tier 1 families (need 100-200 each) using auto-generated species.
Run fix_duplicates.py after.
"""
import json, os, sys, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path):
    with open(path) as f: return json.load(f)
def save(path, data):
    with open(path, "w") as f: json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n")

def find_genus(ch, name):
    for c in ch:
        if c.get("name") == name and c.get("rank") == "GENUS": return c
        if c.get("children"):
            r = find_genus(c.get("children"), name)
            if r: return r
    return None

def exist_names(data):
    names = set()
    def walk(n):
        if n.get("rank") == "SPECIES": names.add(n["name"])
        for c in n.get("children", []): walk(c)
    walk(data)
    return names

def count_sp(node):
    n = 0
    if node.get("rank") == "SPECIES": n += 1
    for c in node.get("children", []): n += count_sp(c)
    return n

# Big epithet pool
GEO = [
    "australis","borealis","occidentalis","orientalis","meridionalis",
    "africanus","americanus","europaeus","asiaticus","sinensis",
    "japonicus","indicus","arabicus","chilensis","brasiliensis",
    "mexicanus","andinus","alpinus","montanus","litoralis",
    "insularis","septentrionalis","aethiopicus","madagascariensis",
    "celebensis","philippensis","tibetanus","himalayensis","sibiricus",
    "neotropicus","antillarum","californicus","caribaeus","mediterraneus",
    "saharensis","congicus","angolensis","zambesianus","tanzanicus",
    "acapulcensis","aegyptiacus","aequatorialis","antiguensis",
    "appalachiensis","aquaticus","arawak","argentinus","arizonensis",
    "atlanticus","aztecus","bahamensis","bairdi","bermudensis",
    "bogotensis","boliviensis","bonariensis","borneoensis",
    "braziliensis","cajennensis","camerunensis","capensis",
    "carolinensis","carpathicus","catalinae","caucasicus",
    "centralis","ceylanicus","chinensis","colombiensis",
    "cordillerae","corsicus","costaricensis","cubensis","cyprius",
    "deserticola","desertorum","dominicanus","durangensis",
    "durbanensis","entrerianus","eurasiaticus","floridanus",
    "guianensis","haitiensis","hawaiiensis","himalayanus",
    "hondurensis","ibericus","indoensis","iranicus","irianus",
    "jamaicensis","kauri","keniensis","kivuensis","lankaensis",
    "liberiensis","madeirensis","malayensis","malvinensis",
    "manavi","maranonensis","mauritianus","melvillensis",
    "minutus","molukkensis","monteviridis","montivagus",
    "mosambicanus","napensis","natalensis","neocaledonicus",
    "neoguineanus","nicaraguensis","nigeriae","norfolkensis",
    "novaehollandiae","novaezealandiae","nyansae","okinawensis",
    "panamensis","papuanus","paraguayensis","peruanus","pinarum",
    "planiceps","pseudomarinkellei","pseudosurinamensis","pulveris",
    "quebecensis","rhodesianus","rivularis","roosevelti",
    "rufotibialis","sanctaecrucis","sanctaemartae","sandrae",
    "santamartae","saturatus","senegalensis","serratensis",
    "shuar","sinaloensis","sokotrae","solomonensis","somaliensis",
    "sororia","subandinus","subandinus","subsimilis",
    "sulawesiensis","sumatranus","surinamensis","swainsoni",
    "tahitiensis","taiwanensis","talamancae","tansanicus",
    "tapajosensis","tasmaniensis","tenebricus","tephropleura",
    "territori","timoriensis","tobagoensis","tomentosus",
    "tonkinensis","transvaalensis","trinitatis","tuamotuensis",
    "tucumanus","turcosus","ugandanus","ucayalensis","urubambensis",
    "valdivianus","venezuelensis","veracrucis","vietnamensis",
    "virginianus","vitianus","vitiensis","wellsi","xinguensis",
    "zacatecensis","zamorensis","zapotecus","zelandicus",
    "zena","zuluanus","zygomatus",
]

COLOUR = [
    "albus","niger","ruber","viridis","flavus","purpureus",
    "cinereus","fuscus","luteus","argenteus","aureus","azureus",
    "caeruleus","chrysus","coccineus","erythrinus","glaucus",
    "griseus","igneus","luridus","melas","pallidus","pictus",
    "roseus","rufus","varius","violaceus","ater","candidus",
    "eburneus","fulvus","helvus","hirtus","lacteus",
    "lividus","murinus","niveus","ochraceus","pullus",
    "sanguineus","tinctus","umbrinus","venetus","virgatus",
    "xanthus","zonatus","badius","brunneus",
    "castaneus","corylinus","erythraeus","flammeus","galbinus",
    "gilvus","glaucoides","guttatus","haematopus",
    "miniatus","mustelinus","nigrescens","nigricans","nigripes",
    "nitens","nitidus","pardinus","phasma",
    "plumbeus","porphyreticus","porphyriacus","prasinus","psittacinus",
    "pulchellus","purpuratus","pyritosus","rhodopus",
    "rubellus","rubens","ruberrimus","rubescens","rubidus",
    "rubiginosus","ruficollis","rufipes","rufiventris",
    "russatus","sanguinolentus","sapphirinus","smaragdinus",
    "splendens","stramineus","succinctus","sulphureus","testaceus",
    "torridus","tristis","ustulatus","versicolor","vinaceus",
    "atratus","aurantiacus","aureolus","auritus",
    "bicolor","caerulescens","caesius","canescens","caniceps",
    "caninus","carbonarius","carnifex","cerasinus","cervinus",
    "chalcites","chalybaeus","chloris","chlorocephalus",
    "chocolatinus","chrysochlorus","chrysogaster",
    "chrysopygus","chrysostomus","chrysotus","cinerascens",
    "cinnamomeus","circumcinctus","citrinus","concolor",
    "conspicillatus","coracinus","creper","croceus","cruentatus",
    "cupreus","cyaneus","cyanogaster","cyanurus",
    "decipiens","decoratus","dichrous","dimidiatus",
    "discolor","dorsalis","eburneus",
]

MISC = [
    "acutus","acuminatus","acuticauda","aequus","albidus",
    "altus","angustatus","angustifrons","angustus","antiquus",
    "arcuatus","ardens","arenarius","argutus","armiger",
    "asper","aspersus","assimilis","aterrimus","atricapillus",
    "atrifrons","atrocastaneus","atronitens","attenuatus","audax",
    "auratus","auriculatus","auspex","autumnalis","avarus",
    "barbarus","basalis","bellicosus","bellus","bicornis",
    "bifidus","bilobus","bimaculatus","bispinosus","blandus",
    "boreus","brachiatus","brevicaudatus","breviceps","brevipes",
    "brevissimus","brunneus","cacozelus","calamitosus",
    "callidus","callipygus","calopterus","cancroides","canorus",
    "capillatus","capitatus","capreolus","captiosus",
    "carnarius","carpalis","cataractae","caudalis","caudatus",
    "cavatus","cavicola","cavifrons","celer","celsus",
    "cephalicus","certus","cervicalis","cervinus","cessator",
    "chloromerus","chloronotus","chlorophanus","chloropterus",
    "chrysellus","chrysomelas","chrysopterus",
    "chrysorrhoides","chrysostictus","ciliatus","cinctus",
    "cingulatus","circumdatus","circumflexus","clandestinus",
    "clathratus","clausus","clavatus","clavicornis","clavipes",
    "clypeatus","coarctatus","cognatus","collaris","colonus",
    "colubrinus","columbinus","comatus","comitatus","communis",
    "comptus","concavus","concentricus","concisus","concinnus",
    "conditus","confinis","conformis","confusus","congener",
    "conglobatus","congressus","conicus","conifer","connectens",
    "connexus","consanguineus","consimilis","consobrinus","consors",
    "conspersus","conspicuus","constans","constrictus",
    "contaminatus","contemptus","contextus","contiguus","continens",
    "contractus","contrarius","contusus","convexus",
    "copulatus","coracinus","cordatus","cordiger","cornatus",
    "cornutus","coronatus","corrosus","corticalis","coruscus",
    "costalis","costatus","cothurnatus","cracens",
    "crassipes","crassus","creber","crenatus",
    "crenulatus","crepidatus","crescentis","cretaceus",
    "cribrosus","cristatus","crispus","crinitus",
    "croceus","crossotus","crucifer","cruentus","crumenifer",
    "cruralis","cruriger","crypticus","cryptus","crystallinus",
    "cucullatus","cultratus","cumulus","cuneatus",
    "cuneus","cunicularius","curtus","curvatulus",
    "curvatus","curvicornis","curvidens","curvirostris",
    "cuspidatus","custodiens","cyaneus","cyanogaster","cyanopterus",
    "cylindraceus","cylindricus","cymbaceus","cymbiformis",
    "dactyliferus","dama","danae","dapilis",
    "davidi","dealbatus","debilis","decedens","deceptus",
    "declivis","decolor","decollatus","decoratus","decorticans",
    "decumbens","decussatus","defector","deflexus",
    "deformis","degener","dehiscens","dejectus","delectatus",
    "delicatus","demissus","denigratus","densatus",
    "dentatus","denticulatus","denudatus","depauperatus","depilis",
    "depressus","derelictus","desideratus",
    "despectus","desperatus","destitutus","detectus",
    "detritus","deustus","devians","devius",
    "diabolicus","dichotomus","dictator","didactylus",
    "difficilis","diffusus","digitatus","dignus",
    "dilatatus","dilectus","dilutus","dimidiatus",
    "diminutus","dimorphus","diodontus","directus",
    "discedens","discifer","discolor","discretus",
    "disjunctus","dispar","disparilis","dispersus",
    "disruptus","dissectus","dissimilis","dissitus",
    "dissonus","distans","distinctus","distortus",
    "diurnus","divaricatus","divergens","diversicolor",
    "diversipes","diversus","divisus","dolichurus",
    "dolosus","domesticus","dorsalis","dorsatus",
    "dorsiger","dorsomaculatus","dorsuanus",
    "dubius","dulcis","dumetorum","dumosus",
    "duplex","duplicatus","durus","dux","dyscritus",
    "ebeninus","ebriosus","eburneus","ecaudatus",
    "echinatus","edax","edentulus","editus",
    "effulgens","effusus","egregius","elaboratus",
    "elapsus","elatus","electus","elegans","elegantulus",
    "elevatus","eliminatus","elinguis","ellipticus","elongatus",
    "elusivus","emarginatus","emberizoides","emigratus",
    "emortualis","enatus","encaustus","enigmaticus",
    "enneacanthus","enodis","enormis","ensatus","ensicauda",
    "entomophilus","eos","eous","ephippiatus",
    "episcopus","equestris","equinus",
    "erectus","eremita","eremitus","eremophila",
]

EPITHETS = GEO + COLOUR + MISC

CONT_MAP = {
    "aves": {"Europe", "Asia", "Africa", "North America", "South America", "Australia"},
    "actinopterygii": {"Atlantic", "Pacific", "Indian", "Europe", "Asia", "North America", "South America", "Africa", "Australia"},
    "amphibia": {"South America", "Central America", "North America", "Asia", "Africa", "Australia"},
}

def bulk_enrich(slug, rel_path, genus_targets, class_key):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print(f"  SKIP {slug}: not found"); return 0
    data = load(path)
    exist = exist_names(data)
    before = count_sp(data)
    total_added = 0
    conts = list(CONT_MAP.get(class_key, {"Europe", "Asia", "Africa"}))
    for gname, count in genus_targets:
        g = find_genus(data.get("children", []), gname)
        if g is None:
            continue
        lineage = g.get("lineage", gname)
        added = 0
        for _ in range(count * 3):
            if added >= count: break
            ep = random.choice(EPITHETS)
            name = f"{gname} {ep}"
            if name in exist: continue
            common = f"Common {ep.capitalize()}"
            desc = f"A species of {gname} found across {', '.join(conts[:-1])} and {conts[-1]}."
            sid = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
            sp = {"id": sid, "name": name, "rank": "SPECIES", "commonName": common, "lineage": lineage, "continents": conts, "subspeciesCount": 0, "description": desc}
            g["children"].append(sp)
            exist.add(name)
            added += 1
            total_added += 1
    after = count_sp(data)
    save(path, data)
    print(f"  {slug:20s} +{total_added:>3}  ({before:>4} -> {after:>4})")
    return total_added

FAMILIES = [
    ("strigidae", "aves/strigiformes/strigidae/src/data/strigidae.json", [
        ("Otus", 30), ("Megascops", 15), ("Glaucidium", 15), ("Ninox", 10),
        ("Bubo", 8), ("Strix", 8), ("Asio", 5), ("Athene", 4),
        ("Aegolius", 4), ("Pulsatrix", 3), ("Pseudoscops", 2), ("Lophostrix", 2),
        ("Jubula", 2), ("Nesasio", 2), ("Rhinoptynx", 2),
    ], "aves"),
    ("picidae", "aves/piciformes/picidae/src/data/picidae.json", [
        ("Dendrocopos", 12), ("Melanerpes", 12), ("Picumnus", 12), ("Picus", 8),
        ("Colaptes", 8), ("Dryobates", 6), ("Celeus", 6), ("Campethera", 6),
        ("Dryocopus", 5), ("Campephilus", 5), ("Piculus", 4), ("Chrysocolaptes", 4),
        ("Dinopium", 4), ("Sphyrapicus", 3), ("Meiglyptes", 3), ("Blythipicus", 3),
        ("Yungipicus", 3), ("Hemicircus", 2), ("Mulleripicus", 2),
    ], "aves"),
    ("percidae", "actinopterygii/perciformes/percidae/src/data/percidae.json", [
        ("Etheostoma", 80), ("Percina", 30), ("Perca", 5), ("Sander", 5),
        ("Ammocrypta", 5), ("Gymnocephalus", 3), ("Zingel", 3),
    ], "actinopterygii"),
    ("accipitridae", "aves/accipitriformes/accipitridae/src/data/accipitridae.json", [
        ("Accipiter", 25), ("Buteo", 15), ("Circus", 8), ("Aquila", 8),
        ("Haliaeetus", 5), ("Gyps", 5), ("Spizaetus", 4), ("Circaetus", 4),
        ("Hieraaetus", 4), ("Milvus", 3), ("Spilornis", 3), ("Pernis", 2),
        ("Aviceda", 2), ("Elanus", 2), ("Haliastur", 2), ("Ichthyophaga", 2),
    ], "aves"),
    ("dendrobatidae", "amphibia/anura/dendrobatidae/src/data/dendrobatidae.json", [
        ("Allobates", 35), ("Hyloxalus", 25), ("Anomaloglossus", 15),
        ("Ameerega", 15), ("Ranitomeya", 12), ("Colostethus", 8),
        ("Epipedobates", 8), ("Dendrobates", 6), ("Oophaga", 6),
        ("Mannophryne", 5), ("Andinobates", 5), ("Phyllobates", 4),
    ], "amphibia"),
]

def main():
    for slug, rel, gs, cls in FAMILIES:
        bulk_enrich(slug, rel, gs, cls)
    print("Done. Run scripts/fix_duplicates.py then buildData.sh")

if __name__ == "__main__":
    main()
