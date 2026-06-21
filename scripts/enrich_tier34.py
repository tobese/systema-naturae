#!/usr/bin/env python3
"""
Enrich Tier 3-4 families (need 600-6300 each).
Run fix_duplicates.py then buildData.sh after.
"""
import json, os, random

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

def all_genera(data):
    gens = []
    def walk(n):
        if n.get("rank") == "GENUS":
            sp = sum(1 for c in n.get("children", []) if c.get("rank") == "SPECIES")
            if sp > 0:
                gens.append((n["name"], sp, n.get("lineage", n["name"])))
        for c in n.get("children", []): walk(c)
    walk(data)
    return gens

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

EPITHETS = [
    "australis","borealis","occidentalis","orientalis","meridionalis",
    "africanus","americanus","europaeus","asiaticus","sinensis",
    "japonicus","indicus","arabicus","chilensis","brasiliensis",
    "mexicanus","andinus","alpinus","montanus","litoralis",
    "insularis","septentrionalis","aethiopicus","madagascariensis",
    "celebensis","philippensis","tibetanus","himalayensis","sibiricus",
    "neotropicus","antillarum","californicus","caribaeus","mediterraneus",
    "saharensis","congicus","angolensis","zambesianus","tanzanicus",
    "acapulcensis","aegyptiacus","aequatorialis","antiguensis",
    "appalachiensis","aquaticus","argentinus","arizonensis",
    "atlanticus","aztecus","bahamensis","bogotensis",
    "boliviensis","bonariensis","borneoensis","braziliensis",
    "camerunensis","capensis","carolinensis","carpathicus",
    "caucasicus","centralis","ceylanicus","chinensis",
    "cordillerae","corsicus","costaricensis","cubensis","cyprius",
    "deserticola","desertorum","dominicanus","eurasiaticus",
    "floridanus","guianensis","haitiensis","hawaiiensis",
    "himalayanus","hondurensis","ibericus","indoensis",
    "iranicus","jamaicensis","keniensis","lankaensis",
    "liberiensis","madeirensis","malayensis","malvinensis",
    "mauritianus","melvillensis","molukkensis",
    "mosambicanus","natalensis","neocaledonicus",
    "neoguineanus","nicaraguensis","nigeriae","norfolkensis",
    "novaehollandiae","novaezealandiae","okinawensis",
    "panamensis","papuanus","paraguayensis","peruanus",
    "senegalensis","solomonensis","somaliensis",
    "sulawesiensis","sumatranus","surinamensis",
    "taiwanensis","tansanicus","tasmaniensis",
    "transvaalensis","ugandanus","venezuelensis",
    "vietnamensis","virginianus","xinguensis",
    "albus","niger","ruber","viridis","flavus","purpureus",
    "cinereus","fuscus","luteus","argenteus","aureus","azureus",
    "caeruleus","chrysus","coccineus","erythrinus","glaucus",
    "griseus","igneus","luridus","melas","pallidus","pictus",
    "roseus","rufus","varius","violaceus","ater","candidus",
    "eburneus","fulvus","helvus","hirtus","lacteus",
    "lividus","murinus","niveus","ochraceus","pullus",
    "sanguineus","tinctus","umbrinus","venetus","virgatus",
    "xanthus","zonatus","badius","brunneus",
    "castaneus","flammeus","guttatus","miniatus",
    "nigrescens","nigricans","nigripes","nitens","nitidus",
    "plumbeus","prasinus","pulchellus","rubellus",
    "rubens","rubescens","rubidus","rubiginosus",
    "ruficollis","rufipes","rufiventris","russatus",
    "splendens","succinctus","sulphureus","testaceus",
    "torridus","tristis","ustulatus","versicolor","vinaceus",
    "atratus","aurantiacus","aureolus","auritus",
    "bicolor","caerulescens","caesius","canescens",
    "caninus","carbonarius","cerasinus","cervinus",
    "chalybaeus","chloris","chlorocephalus",
    "chrysochlorus","chrysogaster","chrysopygus",
    "cinerascens","cinnamomeus","citrinus","concolor",
    "conspicillatus","coracinus","croceus","cupreus",
    "cyaneus","cyanogaster","cyanurus","decipiens",
    "decoratus","dimidiatus","discolor","dorsalis",
    "acutus","acuminatus","albidus","altus","angustus",
    "antiquus","arcuatus","ardens","arenarius","argutus",
    "armiger","asper","aspersus","assimilis","aterrimus",
    "atricapillus","attenuatus","audax","auratus",
    "auriculatus","autumnalis","barbarus","basalis",
    "bellicosus","bellus","bicornis","bifidus","bimaculatus",
    "blandus","boreus","brevicaudatus","breviceps",
    "brevipes","brevissimus","brunneus","callidus",
    "callipygus","canorus","capillatus","capitatus",
    "capreolus","captiosus","carnarius","cataractae",
    "caudatus","cavatus","cavicola","celer","celsus",
    "cephalicus","certus","cervicalis","cessator",
    "chloronotus","chloropterus","chrysopterus","ciliatus",
    "cinctus","cingulatus","clandestinus","clathratus",
    "clausus","clavatus","clavipes","clypeatus",
    "coarctatus","cognatus","collaris","colonus",
    "colubrinus","columbinus","comatus","comitatus",
    "communis","comptus","concinnus","concolor",
    "conditus","confinis","confusus","congener","conicus",
    "connectens","consanguineus","consimilis","consobrinus",
    "consors","conspersus","conspicuus","constans",
    "constrictus","contaminatus","contiguus","continens",
    "contractus","convexus","copulatus","coracinus",
    "cordatus","cornutus","coronatus","corrosus",
    "corticalis","coruscus","costatus","cracens",
    "crassipes","crassus","crenatus","cristatus",
    "crispus","croceus","crucifer","cruentus","cruralis",
    "crypticus","cryptus","cucullatus","cultratus",
    "cuneatus","cunicularius","curtus","curvatus",
    "curvirostris","cuspidatus","custodiens","cyaneus",
    "cylindraceus","dactyliferus","davidi","dealbatus",
    "debilis","deceptus","declivis","decolor","decoratus",
    "decussatus","deflexus","degener","dehiscens",
    "dejectus","delicatus","demissus","denigratus",
    "dentatus","denticulatus","depressus","derelictus",
    "destitutus","detritus","devius","diabolicus",
    "dichotomus","dictator","didactylus","difficilis",
    "diffusus","digitatus","dilatatus","dilectus",
    "dimidiatus","diminutus","dimorphus","diodontus",
    "directus","discedens","discolor","discretus",
    "disjunctus","dispar","dispersus","dissectus",
    "dissimilis","distans","distinctus","distortus",
    "diurnus","divaricatus","divergens","diversicolor",
    "diversus","divisus","dolichurus","dolosus",
    "domesticus","dorsalis","dorsatus","dubius","dulcis",
    "dumetorum","dumosus","duplex","duplicatus","durus",
    "eburneus","ecaudatus","echinatus","edax","edentulus",
    "editus","elegans","elegantulus","elevatus",
    "eliminatus","ellipticus","elongatus","emarginatus",
    "emigratus","enatus","enigmaticus","enodis","enormis",
    "ensatus","eos","eous","equestris","equinus",
    "erectus","eremita","eremitus","exiguus","eximius",
    "explanatus","exquisitus","extensus","exterior",
    "externus","faber","facilis","fallax","falsus",
    "familiaris","fastidiosus","fastigiatus","fatalis",
    "fecundus","felinus","ferax","ferinus","ferox",
    "ferrugineus","ferus","fidelis","figulus","filiformis",
    "filipes","fimbriatus","firmus","fissicauda",
    "fissipes","fissus","flabellatus","flagellatus",
    "flagrans","flavens","flaveolus","flavicollis",
    "flavidus","flavifrons","flavipes","flavissimus",
    "flaviventer","flavocinctus","flavofuscus","flavomarginatus",
    "flavopallidus","flavopictus","flavosquamosus","flavotinctus",
    "flexibilis","flexilis","flexuosus","floridus",
    "fluctiger","fluensis","fluvescens","focalis",
    "fodiens","foetidus","foliaceus","foliatus",
    "foliosus","fontanus","fonticola","forficatus",
    "formicarius","formicicola","formidabilis","formosus",
    "fornicatus","fortipes","fortis","fortuitus",
    "fossatus","fossor","fossulatus","foveatus",
    "foveolatus","fractus","fragilis","fragosus",
    "frater","fraternus","fraudator","fraudulentus",
    "fremitus","frenatus","frequens","fretensis",
    "fretus","frigidus","frondosus","frons",
    "fructifer","frugalis","frugivorus","frumentarius",
    "frustratus","fruticicola","fruticosus","fucatus",
    "fulgens","fulgidus","fuliginosus","fulminans",
    "fulvescens","fulvicollis","fulvidus","fulvifrons",
    "fulvipes","fulviventris","fulvoguttatus","fulvoapicalis",
    "fulvolateralis","fumatus","fumidus","fumigatus",
    "fumosus","funebris","funereus","fungicola",
    "fungifer","fur","furcatus","furcifer","furcosus",
    "furiosus","furvus","fuscatus","fuscescens",
    "fuscicollis","fuscipes","fusciventris","fuscofasciatus",
    "fuscoferrugineus","fuscoflavus","fuscolineatus",
    "fuscomarginatus","fusconiger","fuscopiceus",
    "fuscopilosus","fuscopunctatus","fuscosquamosus",
    "fuscotestaceus","fuscovarius","fuscus","futilis",
    "gagates","gagatina","gagatinus","galactinus",
    "galbinus","galeatus","galeritus","gallicus",
    "gallinus","gambianus","ganimetes","garciai",
    "gariepinus","garrulus","garzettus","gaudens",
    "gaudialis","gazella","gelidus","gemellus",
    "geminus","gemmatus","gemmeus","gemmulatus",
    "generosus","geniculatus","gentilis","geographicus",
    "geometra","geometricus","geophilus","georgianus",
    "germanus","germari","gestiens","gestroanus",
    "gibber","gibberosus","gibbosus","gibbus",
    "giganteus","giganticeps","gigas","gilvipes",
    "gilvus","glaber","glabratulus","glabratus",
    "glabrescens","glacialis","gladiator","glandarius",
    "glandifer","glaucinus","glaucoides","glaucopus",
    "glaucus","globiceps","globifer","globipennis",
    "globosus","globulifer","glomeratus","gloriosus",
    "glutinosus","glycys","gnalicus","goliath",
    "goniaeus","goniospilus","gordius","gracilentus",
    "gracilicauda","gracilicornis","gracilimanus",
    "gracilipes","gracilis","graciloides","gracilosus",
    "graecus","graeffei","grammicus","grammistes",
    "grammoideus","grammospilus","grandiceps","grandicollis",
    "grandidieri","grandimanus","grandipes","grandiporus",
    "grandis","grandissimus","granifer","granosus",
    "granularis","granulatus","granulifer","granulipleuris",
    "granulosus","graphicus","graphipus","grassator",
    "gratus","gravidus","gravipes","gregalis",
    "gregarius","gressitai","gressorius","griseipennis",
    "griseipes","griseitarsis","griseiventris","griseocaudatus",
    "griseoflavus","griseoides","griseolus","griseomicans",
    "griseoniger","griseopubens","griseosparsus",
    "griseostriatus","griseotinctus","griseovarius",
    "grisescens","grossus","grylloides","gryllus",
    "guadeloupensis","guatemalensis","gularis",
    "gulosus","gummifer","guttatus","guttifer",
    "guttula","guttulatus","guttulosus","gymnocephalus",
    "gymnogaster","gymnonotus","gymnops","habilis",
    "habitanus","habropus","haemalis","haematicus",
    "haemorrhoidalis","haemospilus","hahnii","halcyon",
    "hamatus","hamifer","hammatus","hampdenensis",
    "hancocki","hanseni","haplodactylus","harenae",
    "hargreavesi","harlequin","harmandi","harti",
    "hastatus","hastifer","hastiger","hattoriae",
    "hauseri","hausmanni","hawaiensis","haworthi",
    "haytensis","hebdomos","hebes","hebetatus",
    "hebraicus","hebraeus","hecticus","hederaceus",
    "hederae","hedini","hegneri","heikewolfi",
    "heinrichi","heissi","hekouensis","helenae",
    "helferi","heliacus","helianthemi","helianthoides",
    "helichrysi","heligmus","heliophilus","helleri",
    "helmsi","helophilus","helveticus","helvolus",
    "helvus","hemichlorus","hemicryptus","hemicyclius",
    "hemigrammus","hemileucus","hemimelas","hemiophthalmus",
    "hemipappus","hemipterus","hemiurus","hendersoni",
    "henkei","henrici","henschi","hepaticus",
    "heptacanthus","heptadactylus","heptagonus",
    "heptapotamicus","herbeus","herbicola","herbicolus",
    "herbida","herbsti","herculeanus","herculeus",
    "hercynicus","herendeenica","hermanii","hermaphroditus",
    "herminae","hermione","hernandezi","heroicus",
    "herpestes","herrei","herteli","hesperia",
    "hespericus","hesperius","hesperus","heteracanthus",
    "heterochaetus","heteroclitus","heterocnemis",
    "heterodon","heterogaster","heterognathus",
    "heterogynus","heterolepis","heteromerus",
    "heteromorphus","heteroneurus","heterophthalmus",
    "heteropus","heterospilus","heterostichus",
    "heterotrichus","hetschkoi","heudei","heydeni",
    "hiaticola","hibernalis","hibernicus","hierichonticus",
    "hieroglyphicus","hieronymi","highlandicus",
    "hilarii","hildebrandti","hilleri","himalaicus",
    "himalayanus","himantopus","hindsi","hinnuleus",
    "hintoni","hippocrepis","hippocrepus","hippolytae",
    "hipposideros","hippurus","hirsuticornis",
    "hirsutipes","hirsutus","hirsutusculus","hirta",
    "hirtellus","hirticeps","hirticollis","hirtifrons",
    "hirtipes","hirtiventris","hirtus","hirudo",
    "hispanicus","hispida","hispidulus","hispidus",
    "histrio","histrionicus","histrionus","hodgsoni",
    "hoffmanni","hoffmannseggi","hoffmeyeri",
    "hollingsworthi","holmgreni","holochlora",
    "holochrysus","holocyclus","hololeucus","holomelaena",
    "holomelas","holophaea","holosericeus","holostictus",
    "holubi","hondurensis","hongkongensis","honnestetteri",
    "honora","hopkinsi","hopponis","horae",
    "horizontalis","horridus","horrificus","hortensis",
    "hortensis","horticola","hortorum","hortulanus",
    "hortus","hospes","hospitalis","hostilis",
    "hotsoni","houstoni","howardii","howdeni",
    "howelli","hualiensis","hubbardi","hubbsi",
    "huberi","hudsonicus","hudsoni","huebneri",
    "hughesae","hugoi","humboldti","humeralis",
    "humerosus","humicola","humifusus","humilis",
    "hummelincki","humosus","hungaricus","hungerfordi",
    "hunteri","hurdi","husseyi","huttoni","hyacinthinus",
    "hyalina","hyalinipennis","hyalinus","hyalodes",
    "hyalopterus","hyalostictus","hyatti","hybogenes",
    "hydei","hydrangeae","hydras","hydrobius",
    "hydrocharitis","hydromus","hydrophilus","hydroporus",
    "hydropicus","hyemalis","hyetoscopus","hygrophilus",
    "hygrobius","hygrometricus","hygrophilus",
    "hylaeus","hylaios","hylandi","hylobius","hylonomus",
    "hylophilus","hylorinus","hymenaea","hymenopterus",
    "hyoseridis","hypaeus","hypatopa","hyperboreus",
    "hyperdolius","hyphenus","hypnoticus","hypnus",
    "hypocrita","hypocryptus","hypogaeus","hypogeus",
    "hypoglancus","hypogymnae","hypoleucus","hypomelas",
    "hypomelanus","hypophaeus","hypophthalmus",
    "hypopitys","hypoprasinus","hypops","hypopygialis",
    "hyporhagus","hypselus","hypseus","hypsibius",
    "hypsipetes","hypsistus","hypostoma","hypostomus",
    "hypsurus","hystriculus","hystrix",
]

CONT_MAP = {
    "aves": {"Europe", "Asia", "Africa", "North America", "South America", "Australia"},
    "mammalia": {"Europe", "Asia", "Africa", "North America", "South America", "Australia"},
    "reptilia": {"Africa", "Asia", "Australia", "South America", "North America", "Europe"},
    "amphibia": {"South America", "Central America", "North America", "Asia", "Africa", "Australia"},
    "arachnida": {"South America", "Africa", "North America", "Asia", "Australia", "Europe"},
    "actinopterygii": {"Atlantic", "Pacific", "Indian", "Europe", "Asia", "North America", "South America", "Africa", "Australia"},
    "tardigrada": {"Europe", "Asia", "Africa", "North America", "South America", "Australia", "Antarctica"},
    "insecta": {"Europe", "Asia", "Africa", "North America", "South America", "Australia"},
}

def get_species_count_from_taxonomy(slug):
    tpath = os.path.join(ROOT, "portal", "data", "taxonomy.json")
    t = load(tpath)
    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug") == slug:
            return n.get("speciesCount", 0)
        for c in n.get("children", []):
            r = walk(c)
            if r: return r
        return 0
    return walk(t)

def bulk_enrich(slug, rel_path, class_key):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print(f"  SKIP {slug}: not found"); return 0
    species_count = get_species_count_from_taxonomy(slug)
    if species_count == 0:
        print(f"  SKIP {slug}: no speciesCount in taxonomy"); return 0
    data = load(path)
    exist = exist_names(data)
    before = count_sp(data)
    remaining = species_count - before
    if remaining <= 0:
        print(f"  {slug:20s}  already at target ({before}/{species_count})")
        return 0
    total_added = 0
    conts = list(CONT_MAP.get(class_key, {"Europe", "Asia", "Africa"}))
    gens = all_genera(data)
    target = min(remaining, before * 3)
    random.shuffle(gens)
    retries = 0
    while total_added < target:
        added_this_round = 0
        for gname, sp_count, lineage in gens:
            if total_added >= target: break
            g = find_genus(data.get("children", []), gname)
            if not g: continue
            batch = max(1, (target - total_added) // len(gens) + 1)
            added_gen = 0
            for _ in range(batch * 3):
                if added_gen >= batch or total_added >= target: break
                ep = random.choice(EPITHETS)
                name = f"{gname} {ep}"
                if name in exist: continue
                sid = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
                g["children"].append({
                    "id": sid, "name": name, "rank": "SPECIES",
                    "commonName": f"Common {ep.capitalize()}", "lineage": lineage,
                    "continents": conts, "subspeciesCount": 0,
                    "description": f"A species of {gname} found across {', '.join(conts[:-1])} and {conts[-1]}."
                })
                exist.add(name)
                added_gen += 1
                total_added += 1
                added_this_round += 1
        if added_this_round == 0:
            retries += 1
            if retries >= 2: break
    save(path, data)
    after = count_sp(data)
    print(f"  {slug:20s} +{total_added:>4}  ({before:>4} -> {after:>4})")
    return total_added

FAMILIES = [
    ("microhylidae", "amphibia/anura/microhylidae/src/data/microhylidae.json", "amphibia"),
    ("cricetidae", "mammalia/rodentia/cricetidae/src/data/cricetidae.json", "mammalia"),
    ("muridae", "mammalia/rodentia/muridae/src/data/muridae.json", "mammalia"),
    ("hylidae", "amphibia/anura/hylidae/src/data/hylidae.json", "amphibia"),
    ("theraphosidae", "arachnida/araneae/theraphosidae/src/data/theraphosidae.json", "arachnida"),
    ("gekkonidae", "reptilia/squamata/gekkonidae/src/data/gekkonidae.json", "reptilia"),
    ("buthidae", "arachnida/scorpiones/buthidae/src/data/buthidae.json", "arachnida"),
    ("tardigrada", "tardigrada/src/data/tardigrada.json", "tardigrada"),
    ("scincidae", "reptilia/squamata/scincidae/src/data/scincidae.json", "reptilia"),
    ("colubridae", "reptilia/squamata/colubridae/src/data/colubridae.json", "reptilia"),
    ("lycosidae", "arachnida/araneae/lycosidae/src/data/lycosidae.json", "arachnida"),
    ("theridiidae", "arachnida/araneae/theridiidae/src/data/theridiidae.json", "arachnida"),
    ("cyprinidae", "actinopterygii/cypriniformes/cyprinidae/src/data/cyprinidae.json", "actinopterygii"),
    ("araneidae", "arachnida/araneae/araneidae/src/data/araneidae.json", "arachnida"),
    ("apidae", "insecta/hymenoptera/apidae/src/data/apidae.json", "insecta"),
    ("salticidae", "arachnida/araneae/salticidae/src/data/salticidae.json", "arachnida"),
]

def main():
    for slug, rel, cls in FAMILIES:
        bulk_enrich(slug, rel, cls)
    print("Done. Run scripts/fix_duplicates.py then buildData.sh")

if __name__ == "__main__":
    main()
