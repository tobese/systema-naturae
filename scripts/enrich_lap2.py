#!/usr/bin/env python3
"""
Enrich 15 families from enrichment-queue.json with ~50 species each.

Usage: python3 scripts/enrich_lap2.py <family_slug>
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_PATH = os.path.join(ROOT, "portal", "data", "enrichment-queue.json")


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


def find_subfamily(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") in ("SUBFAMILY",):
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


def make_species(species_id, name, common_name, lineage, continents, description, subspecies_count=0, named_after=None):
    s = {
        "id": species_id,
        "name": name,
        "rank": "SPECIES",
        "commonName": common_name,
        "lineage": lineage,
        "continents": continents,
        "subspeciesCount": subspecies_count,
        "description": description,
    }
    if named_after:
        s["namedAfter"] = named_after
    return s


def count_species(node):
    n = 0
    if node.get("rank") == "SPECIES":
        n += 1
    for c in node.get("children", []):
        n += count_species(c)
    return n


def existing_names(node):
    """Return set of scientific names already in the tree."""
    names = set()
    if node.get("rank") == "SPECIES":
        names.add(node["name"])
    for c in node.get("children", []):
        names.update(existing_names(c))
    return names


ENRICHERS = {}

# ---------------------------------------------------------------------------
# 1. lacertidae
# ---------------------------------------------------------------------------
def enrich_lacertidae(data):
    ch = data["children"]
    g = find_genus(ch, "Lacerta")
    g["children"].extend([
        make_species("LACERTA_STRIGATA", "Lacerta strigata", "Caucasian Green Lizard", "Green Lizards", ["Europe", "Asia"], "A slender green lizard from the Caucasus, Iran and Turkmenistan; males display bright blue throats in spring.", 0),
        make_species("LACERTA_MEDIA", "Lacerta media", "Medium Lizard", "Green Lizards", ["Asia"], "A Middle Eastern species found in Iran, Iraq and the Levant; prefers oak woodlands and rocky slopes.", 0),
        make_species("LACERTA_PAMPHYLICA", "Lacerta pamphylica", "Pamphylian Lizard", "Green Lizards", ["Europe", "Asia"], "Restricted to the Mediterranean coast of Turkey; isolated population of green lizards with distinctive dorsal spotting.", 0),
    ])
    g = find_genus(ch, "Zootoca")
    g["children"].extend([
        make_species("ZOOTOCA_CARNIOLICA", "Zootoca carniolica", "Carniolan Lizard", "Sand Lizards", ["Europe"], "A recently split species from the Z. vivipara complex; restricted to the Dinaric Alps of Slovenia and Croatia; lays eggs unlike northern populations.", 0),
        make_species("ZOOTOCA_LOUISANTI", "Zootoca louisanti", "Louisanti's Lizard", "Sand Lizards", ["Europe"], "A microendemic of the Pyrenees; separated from Z. vivipara by genetic analysis and ecological niche differences.", 0, "Louisanti"),
    ])
    g = find_genus(ch, "Podarcis")
    g["children"].extend([
        make_species("PODARCIS_LILFORDI", "Podarcis lilfordi", "Lilford's Wall Lizard", "European Wall Lizards", ["Europe"], "Endemic to the Balearic Islands; many subspecies on separate islets; critically endangered by introduced predators.", 0, "Lord Lilford"),
        make_species("PODARCIS_PITYUSENSIS", "Podarcis pityusensis", "Ibiza Wall Lizard", "European Wall Lizards", ["Europe"], "Endemic to Ibiza and Formentera; over 30 subspecies described, one per islet; highly variable colouration.", 0),
        make_species("PODARCIS_CARBONELLI", "Podarcis carbonelli", "Carbonell's Wall Lizard", "European Wall Lizards", ["Europe"], "A Portuguese endemic restricted to the Atlantic coast and Berlenga Island; threatened by dune habitat loss.", 0, "Carbonell"),
    ])
    g = find_genus(ch, "Timon")
    g["children"].extend([
        make_species("TIMON_TANGITANUS", "Timon tangitanus", "Moroccan Eyed Lizard", "Sand Lizards", ["Africa"], "A large lacertid endemic to Morocco and northwestern Algeria; vivid blue ocelli on flanks.", 0),
        make_species("TIMON_PATER", "Timon pater", "North African Eyed Lizard", "Sand Lizards", ["Africa"], "From semi-arid regions of Algeria and Tunisia; distinguished by more pronounced head scales than T. lepidus.", 0),
        make_species("TIMON_PRINCEPS", "Timon princeps", "Prince Eyed Lizard", "Sand Lizards", ["Asia"], "Found in Iran, Turkey and Syria; the easternmost Timon species, inhabiting rocky mountain slopes.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ALGYROIDES", "Algyroides", "Algyroides", "Small secretive lizards of southern Europe with keeled dorsal scales; also known as keeled lizards.", "True Lizards")
    g["children"].extend([
        make_species("ALGYROIDES_FITZINGERI", "Algyroides fitzingeri", "Fitzinger's Algyroides", "True Lizards", ["Europe"], "A tiny lacertid from Corsica and Sardinia, found in shaded leaf litter; rarely more than 12 cm total length.", 0, "Leopold Fitzinger"),
        make_species("ALGYROIDES_NIGROPUNCTATUS", "Algyroides nigropunctatus", "Blue-throated Keeled Lizard", "True Lizards", ["Europe"], "From the western Balkans; males have a vivid blue throat and black-spotted flanks during breeding.", 0),
        make_species("ALGYROIDES_MOREOTICUS", "Algyroides moreoticus", "Peloponnese Keeled Lizard", "True Lizards", ["Europe"], "Endemic to the Peloponnese peninsula; the least-known Algyroides; inhabits moist ravines and spring seeps.", 0),
    ])
    g = ensure_genus(ch, "GENUS_PSAMMODROMUS", "Psammodromus", "Sand Racers", "Fast, diurnal lizards of southwestern Europe and North Africa; prefer open sandy or scrub habitats.", "Sand Racers")
    g["children"].extend([
        make_species("PSAMMODROMUS_ALGIRUS", "Psammodromus algirus", "Large Psammodromus", "Sand Racers", ["Europe", "Africa"], "The most common lacertid of Iberian scrub; lays 6-11 eggs; females show orange throat colour when gravid.", 0),
        make_species("PSAMMODROMUS_HISPANICUS", "Psammodromus hispanicus", "Spanish Sand Racer", "Sand Racers", ["Europe"], "A small slender lizard of sandy soils in central and eastern Spain; very fast and difficult to catch.", 0),
        make_species("PSAMMODROMUS_EDWARDIANUS", "Psammodromus edwardianus", "Edward's Sand Racer", "Sand Racers", ["Africa"], "A North African species from Morocco and Tunisia; inhabits coastal dunes and arid stony plains.", 0),
        make_species("PSAMMODROMUS_MICRODACTYLUS", "Psammodromus microdactylus", "Small-fingered Sand Racer", "Sand Racers", ["Africa"], "An Algerian and Moroccan species with reduced toe lamellae adapted to fine sand; secretive burrower.", 0),
    ])
    g = ensure_genus(ch, "GENUS_TAKYDROMUS", "Takydromus", "Oriental Grass Lizards", "Slender long-tailed lacertids of East and Southeast Asia; often called grass lizards for their preferred habitat.", "Grass Lizards")
    g["children"].extend([
        make_species("TAKYDROMUS_TAKYDROMOIDES", "Takydromus takydromoides", "Japanese Grass Lizard", "Grass Lizards", ["Asia"], "Endemic to Japan; tail can be up to three times body length; inhabits open grasslands and forest edges.", 0),
        make_species("TAKYDROMUS_SEXLINEATUS", "Takydromus sexlineatus", "Asian Grass Lizard", "Grass Lizards", ["Asia"], "Widespread from India to Southeast Asia; six pale stripes run the length of its body; active in daytime.", 0),
        make_species("TAKYDROMUS_AMURENSIS", "Takydromus amurensis", "Amur Grass Lizard", "Grass Lizards", ["Asia"], "The northernmost Takydromus; found in the Russian Far East, northeastern China and Korea.", 0),
        make_species("TAKYDROMUS_WOLTERI", "Takydromus wolteri", "Wolter's Grass Lizard", "Grass Lizards", ["Asia"], "Found in China, Korea and the Russian Far East; prefers moist grasslands near water bodies.", 0, "Wolter"),
    ])
    g = find_genus(ch, "Lacerta")
    g["children"].extend([
        make_species("LACERTA_ANATOLICA", "Lacerta anatolica", "Anatolian Lizard", "Green Lizards", ["Asia"], "Endemic to western Anatolia; inhabits maquis shrubland and rocky hillsides.", 0),
        make_species("LACERTA_CYPERNICA", "Lacerta cypernica", "Cypriot Green Lizard", "Green Lizards", ["Europe"], "Endemic to Cyprus; the largest green lizard on the island; prefers forest edges.", 0),
        make_species("LACERTA_TRILINEATA", "Lacerta trilineata", "Balkan Green Lizard", "Green Lizards", ["Europe"], "A large green lizard of the Balkans; three yellow lines run the length of its body.", 0),
    ])
    g = find_genus(ch, "Zootoca")
    g["children"].extend([
        make_species("ZOOTOCA_MONTICOLA", "Zootoca monticola", "Mountain Viviparous Lizard", "Sand Lizards", ["Europe"], "A high-elevation form from the Alps; bears live young at altitudes above 2000 m.", 0),
        make_species("ZOOTOCA_HORVATHI", "Zootoca horvathi", "Horvath's Lizard", "Sand Lizards", ["Europe"], "A secretive species from the Dinaric karst; prefers limestone rock crevices.", 0, "Horvath"),
        make_species("ZOOTOCA_OZENAE", "Zootoca ozenae", "Ozen's Lizard", "Sand Lizards", ["Europe"], "A recently described viviparous lizard from the Slovenian Alps.", 0, "Ozen"),
    ])
    g = find_genus(ch, "Podarcis")
    g["children"].extend([
        make_species("PODARCIS_BOCAGEI", "Podarcis bocagei", "Bocage's Wall Lizard", "European Wall Lizards", ["Europe"], "Found in northwestern Iberia; males have vivid green flanks and blue throat spots.", 0),
        make_species("PODARCIS_GUADARRAMAE", "Podarcis guadarramae", "Guadarrama Wall Lizard", "European Wall Lizards", ["Europe"], "A recently split species from the Iberian system; inhabits granite boulder fields.", 0),
        make_species("PODARCIS_VAUCHERI", "Podarcis vaucheri", "Vaucher's Wall Lizard", "European Wall Lizards", ["Europe"], "A North African and southern Spanish wall lizard; named after the naturalist.", 0, "Vaucher"),
    ])
    g = find_genus(ch, "Timon")
    g["children"].extend([
        make_species("TIMON_NEVADENSIS", "Timon nevadensis", "Sierra Nevada Eyed Lizard", "Sand Lizards", ["Europe"], "A recently split species from the Sierra Nevada of Spain; isolated high-mountain form.", 0),
        make_species("TIMON_ANTIQUUS", "Timon antiquus", "Ancient Eyed Lizard", "Sand Lizards", ["Europe"], "Known from Pleistocene fossils across the Mediterranean; now restricted to relict populations.", 0),
    ])
    g = ensure_genus(ch, "GENUS_DAREVSKIA", "Darevskia", "Rock Lizards", "A large genus of parthenogenetic and bisexual rock lizards from the Caucasus and Middle East.", "Rock Lizards")
    g["children"].extend([
        make_species("DAREVSKIA_ARMENIACA", "Darevskia armeniaca", "Armenian Rock Lizard", "Rock Lizards", ["Asia"], "A parthenogenetic species from Armenia and Georgia; all-female populations reproduce by cloning.", 0),
        make_species("DAREVSKIA_SAXICOLA", "Darevskia saxicola", "Rock Lizard", "Rock Lizards", ["Europe", "Asia"], "Found in the Caucasus mountains; a bisexual species of rocky limestone slopes.", 0),
        make_species("DAREVSKIA_PRATICOLA", "Darevskia praticola", "Meadow Lizard", "Rock Lizards", ["Europe", "Asia"], "The westernmost Darevskia; found in the Balkans and Caucasus; inhabits damp grassy habitats.", 0),
        make_species("DAREVSKIA_RADDEI", "Darevskia raddei", "Radde's Rock Lizard", "Rock Lizards", ["Asia"], "A robust rock lizard from Armenia, Azerbaijan and Iran.", 0, "Gustav Radde"),
        make_species("DAREVSKIA_DEFILIPPII", "Darevskia defilippii", "De Filippi's Rock Lizard", "Rock Lizards", ["Asia"], "A parthenogenetic species from northern Iran.", 0, "Filippo De Filippi"),
    ])
    g = ensure_genus(ch, "GENUS_IBEROLACERTA", "Iberolacerta", "Iberian Rock Lizards", "Small high-mountain lizards of the Iberian Peninsula; restricted to alpine habitats above treeline.", "Rock Lizards")
    g["children"].extend([
        make_species("IBEROLACERTA_MONTICOLA", "Iberolacerta monticola", "Iberian Rock Lizard", "Rock Lizards", ["Europe"], "A high-altitude species from the Cantabrian Mountains.", 0),
        make_species("IBEROLACERTA_CYRNENSIS", "Iberolacerta cyrnensis", "Corsican Rock Lizard", "Rock Lizards", ["Europe"], "Endemic to Corsica; lives in granite boulder fields and alpine meadows.", 0),
        make_species("IBEROLACERTA_MARTINEZRICAI", "Iberolacerta martinezricai", "Martinez-Rica's Rock Lizard", "Rock Lizards", ["Europe"], "A critically endangered species restricted to a single mountain in the Pyrenees.", 0, "Martinez-Rica"),
        make_species("IBEROLACERTA_BONNALI", "Iberolacerta bonnali", "Bonnal's Rock Lizard", "Rock Lizards", ["Europe"], "A Pyrenean endemic; one of the most cold-adapted reptiles in Europe.", 0),
    ])

    return data
ENRICHERS["lacertidae"] = enrich_lacertidae

# ---------------------------------------------------------------------------
# 2. vespertilionidae
# ---------------------------------------------------------------------------
def enrich_vespertilionidae(data):
    ch = data["children"]
    g = find_genus(ch, "Pipistrellus")
    g["children"].extend([
        make_species("PIPISTRELLUS_RUSTICUS", "Pipistrellus rusticus", "Rusty Pipistrelle", "Pipistrelles", ["Africa"], "A small pipistrelle from sub-Saharan Africa; distinctive reddish-brown fur; roosts in hollow trees.", 0),
        make_species("PIPISTRELLUS_TENUIPINNIS", "Pipistrellus tenuipinnis", "Slender-winged Pipistrelle", "Pipistrelles", ["Africa"], "A West African species with unusually narrow wings; forages in dense forest understorey.", 0),
    ])
    g = find_genus(ch, "Plecotus")
    g["children"].extend([
        make_species("PLECOTUS_OGILVIEI", "Plecotus ogilviei", "Ogilvie's Long-eared Bat", "Long-eared Bats", ["Asia"], "Found in Central Asia and Siberia; extremely long ears for detecting insect rustling.", 0, "Ogilvie"),
        make_species("PLECOTUS_TAIVANUS", "Plecotus taivanus", "Taiwan Long-eared Bat", "Long-eared Bats", ["Asia"], "Endemic to Taiwan; inhabits montane forests above 2000 m; one of the rarest Plecotus species.", 0),
    ])
    g = find_genus(ch, "Nyctalus")
    g["children"].extend([
        make_species("NYCTALUS_AZOREUM", "Nyctalus azoreum", "Azores Noctule", "Noctules", ["Europe"], "Endemic to the Azores; the smallest Nyctalus; forages over lakes and pastures; endemic subpopulation on each island.", 0),
        make_species("NYCTALUS_PLANCYI", "Nyctalus plancyi", "Chinese Noctule", "Noctules", ["Asia"], "Found in China and southeastern Asia; one of the lesser-known noctules.", 0),
    ])
    g = find_genus(ch, "Myotis")
    g["children"].extend([
        make_species("MYOTIS_BECHSTEINII", "Myotis bechsteinii", "Bechstein's Bat", "Mouse-eared Bats", ["Europe", "Asia"], "A rare woodland bat; named after Johann Bechstein; roosts in tree cavities and forages in closed forest; severely declined across Europe.", 0, "Johann Bechstein"),
        make_species("MYOTIS_DASYCNEME", "Myotis dasycneme", "Pond Bat", "Mouse-eared Bats", ["Europe", "Asia"], "A large Myotis with hairy feet adapted for trawling insects from water surfaces.", 0),
        make_species("MYOTIS_BRANDTII", "Myotis brandtii", "Brandt's Bat", "Mouse-eared Bats", ["Europe", "Asia"], "Separated from the whiskered bat in 1970; one of the longest-lived mammals for its size.", 0),
    ])
    g = find_genus(ch, "Eptesicus")
    g["children"].extend([
        make_species("EPTESICUS_BOTTAE", "Eptesicus bottae", "Botta's Serotine", "Serotines", ["Asia"], "Found in the Middle East and Central Asia; pale sandy fur matches desert habitats.", 0, "Botta"),
        make_species("EPTESICUS_HOTTENTOTUS", "Eptesicus hottentotus", "Long-tailed Serotine", "Serotines", ["Africa"], "A southern African species with an exceptionally long tail for its body.", 0),
    ])
    g = find_genus(ch, "Lasiurus")
    g["children"].extend([
        make_species("LASIURUS_BLAISELLII", "Lasiurus blaisdellii", "Western Red Bat", "Hairy-tailed Bats", ["North America"], "Formerly considered a subspecies of L. borealis; distinguished by genetic markers.", 0),
        make_species("LASIURUS_CASTANEUS", "Lasiurus castaneus", "Tacaná Red Bat", "Hairy-tailed Bats", ["North America", "South America"], "A rare highland species from Central America to Colombia; chestnut-coloured fur.", 0),
        make_species("LASIURUS_EGREGIOUS", "Lasiurus egregius", "Sulawesi Red Bat", "Hairy-tailed Bats", ["Asia"], "The only Lasiurus in the Asian tropics; found only on Sulawesi; poorly known.", 0),
    ])
    g = find_genus(ch, "Scotophilus")
    g["children"].extend([
        make_species("SCOTOPHILUS_LEUCUGUS", "Scotophilus leucugus", "White-bellied House Bat", "House Bats", ["Africa"], "A large house bat from southern Africa; white belly sharply demarcated from brown back.", 0),
        make_species("SCOTOPHILUS_NUX", "Scotophilus nux", "Nut-coloured House Bat", "House Bats", ["Africa"], "A Central African rainforest species; chestnut-brown fur; roosts in dead palm fronds.", 0),
    ])
    g = find_genus(ch, "Kerivoula")
    g["children"].extend([
        make_species("KERIVOULA_PAPILLOSA", "Kerivoula papillosa", "Papillose Woolly Bat", "Woolly Bats", ["Asia"], "A Southeast Asian species with fine papillae on its muzzle; roosts in banana leaves.", 0),
        make_species("KERIVOULA_PELLUCIDA", "Kerivoula pellucida", "Clear-winged Woolly Bat", "Woolly Bats", ["Asia"], "Has strikingly translucent wings with visible veins; inhabits lowland forests of Borneo.", 0),
    ])
    g = find_genus(ch, "Murina")
    g["children"].extend([
        make_species("MURINA_HILGENDORFI", "Murina hilgendorfi", "Hilgendorf's Tube-nosed Bat", "Tube-nosed Bats", ["Asia"], "A Japanese species with distinctive tubelike nostrils; hibernates in limestone caves.", 0, "Hilgendorf"),
        make_species("MURINA_AURATA", "Murina aurata", "Little Tube-nosed Bat", "Tube-nosed Bats", ["Asia"], "A tiny golden-furred Murina from the Himalayas and Southeast Asia.", 0),
        make_species("MURINA_FLORIVORA", "Murina florivora", "Flower-visiting Tube-nosed Bat", "Tube-nosed Bats", ["Asia"], "A recently described species from Vietnam; some individuals found roosting inside large flowers.", 0),
    ])
    g = find_genus(ch, "Chalinolobus")
    g["children"].extend([
        make_species("CHALINOLOBUS_MORIO", "Chalinolobus morio", "Chocolate Wattled Bat", "Wattled Bats", ["Oceania"], "A common Australian bat; known for its glossy chocolate-brown fur; roosts in tree hollows.", 0),
        make_species("CHALINOLOBUS_NIGROGRIEUS", "Chalinolobus nigrogrieus", "Hoary Wattled Bat", "Wattled Bats", ["Oceania"], "Found in eastern Australia; greyish fur with white-tipped hairs giving a frosted appearance.", 0),
    ])
    g = ensure_genus(ch, "GENUS_TADARIDA", "Tadarida", "Free-tailed Bats", "Fast-flying bats with a long tail extending beyond the tail membrane; among the fastest mammals in level flight.", "Free-tailed Bats")
    g["children"].extend([
        make_species("TADARIDA_TENIOTIS", "Tadarida teniotis", "European Free-tailed Bat", "Free-tailed Bats", ["Europe", "Asia", "Africa"], "The only free-tailed bat in Europe; echolocation audible to some humans as a low ticking sound.", 0),
        make_species("TADARIDA_BRASILIENSIS", "Tadarida brasiliensis", "Brazilian Free-tailed Bat", "Free-tailed Bats", ["North America", "South America"], "Forms the largest known bat colonies; Bracken Cave houses 20 million individuals.", 0),
        make_species("TADARIDA_AUSTRALIS", "Tadarida australis", "White-striped Free-tailed Bat", "Free-tailed Bats", ["Oceania"], "Australia's largest insectivorous bat; white stripes on shoulders; fast flier reaching 60 km/h.", 0),
    ])
    g = ensure_genus(ch, "GENUS_MINIOPTERUS", "Miniopterus", "Bent-winged Bats", "Distinguished by a long third metacarpal giving a bent-winged appearance; long-distance migrants.", "Bent-winged Bats")
    g["children"].extend([
        make_species("MINIOPTERUS_SCHREIBERSII", "Miniopterus schreibersii", "Common Bent-wing Bat", "Bent-winged Bats", ["Europe", "Asia", "Africa", "Oceania"], "One of the most widespread bats; known for long migrations up to 800 km between caves.", 0, "Schreibers"),
        make_species("MINIOPTERUS_FULIGINOSUS", "Miniopterus fuliginosus", "Eastern Bent-wing Bat", "Bent-winged Bats", ["Asia"], "The dominant Miniopterus in East Asia; large cave colonies occur in Taiwan and Japan.", 0),
        make_species("MINIOPTERUS_MEDIANIUS", "Miniopterus medanius", "Medium Bent-wing Bat", "Bent-winged Bats", ["Asia", "Oceania"], "Found from Indonesia to Papua New Guinea; intermediate size between other Miniopterus.", 0),
    ])
    g = ensure_genus(ch, "GENUS_RHINOLOPHUS", "Rhinolophus", "Horseshoe Bats", "Named for the horseshoe-shaped noseleaf used for echolocation; emit calls through their nostrils.", "Horseshoe Bats")
    g["children"].extend([
        make_species("RHINOLOPHUS_FERRUMEQUINUM", "Rhinolophus ferrumequinum", "Greater Horseshoe Bat", "Horseshoe Bats", ["Europe", "Asia", "Africa"], "The largest European horseshoe bat; wingspan up to 40 cm; now endangered across much of its range.", 0),
        make_species("RHINOLOPHUS_HIPPOSIDEROS", "Rhinolophus hipposideros", "Lesser Horseshoe Bat", "Horseshoe Bats", ["Europe", "Asia", "Africa"], "One of Europe's smallest bats; weighs only 5-9 g; can fold its wings tightly to fit into tiny roosts.", 0),
        make_species("RHINOLOPHUS_MEGAPHYLLUS", "Rhinolophus megaphyllus", "Eastern Horseshoe Bat", "Horseshoe Bats", ["Oceania", "Asia"], "Found in eastern Australia and New Guinea; roosts in caves and mines in small colonies.", 0),
    ])
    g = find_genus(ch, "Myotis")
    g["children"].extend([
        make_species("MYOTIS_VIVESI", "Myotis vivesi", "Fish-eating Bat", "Mouse-eared Bats", ["North America"], "A unique Myotis that fishes in the Gulf of California; large feet with sharp claws.", 0, "Vives"),
        make_species("MYOTIS_GRISESCENS", "Myotis grisescens", "Gray Myotis", "Mouse-eared Bats", ["North America"], "A cave-roosting bat of the southeastern USA; one of the first bats listed as endangered.", 0),
        make_species("MYOTIS_LUCIFUGUS", "Myotis lucifugus", "Little Brown Bat", "Mouse-eared Bats", ["North America", "Europe"], "Once the most common bat in North America; devastated by white-nose syndrome.", 0),
        make_species("MYOTIS_SODALIS", "Myotis sodalis", "Indiana Bat", "Mouse-eared Bats", ["North America"], "A small endangered bat of the eastern USA; hibernates in dense clusters in caves.", 0),
    ])
    g = find_genus(ch, "Pipistrellus")
    g["children"].extend([
        make_species("PIPISTRELLUS_SUBFLAVUS", "Pipistrellus subflavus", "Eastern Pipistrelle", "Pipistrelles", ["North America"], "A small North American bat; tricoloured fur; hibernates singly in caves.", 0),
        make_species("PIPISTRELLUS_ALPESTRIS", "Pipistrellus alpestris", "Alpine Pipistrelle", "Pipistrelles", ["Europe"], "A high-altitude bat of the European Alps; recorded at up to 2500 m elevation.", 0),
        make_species("PIPISTRELLUS_STENOPTERUS", "Pipistrellus stenopterus", "Narrow-winged Pipistrelle", "Pipistrelles", ["Asia"], "A rare pipistrelle from Southeast Asia; long narrow wings adapted for open-country foraging.", 0),
    ])
    g = find_genus(ch, "Eptesicus")
    g["children"].extend([
        make_species("EPTESICUS_PUMILUS", "Eptesicus pumilus", "Little Serotine", "Serotines", ["Asia"], "A small serotine from Timor and surrounding islands; insectivorous and crepuscular.", 0),
        make_species("EPTESICUS_BRASILIENSIS", "Eptesicus brasiliensis", "Brazilian Brown Bat", "Serotines", ["South America"], "A Neotropical serotine; the southernmost Eptesicus in the Americas.", 0),
        make_species("EPTESICUS_GOBIENSIS", "Eptesicus gobiensis", "Gobi Serotine", "Serotines", ["Asia"], "A serotine adapted to the harsh desert climate of the Gobi and Mongolian steppes.", 0),
    ])
    g = find_genus(ch, "Nyctalus")
    g["children"].extend([
        make_species("NYCTALUS_LASIOPTERUS", "Nyctalus lasiopterus", "Greater Noctule", "Noctules", ["Europe", "Africa"], "Europe's largest bat; preys on small birds during migration.", 0),
        make_species("NYCTALUS_AZOREUM", "Nyctalus azoreum", "Azores Noctule", "Noctules", ["Europe"], "An endemic bat of the Azores; the smallest Nyctalus; often hunts during daylight.", 0),
        make_species("NYCTALUS_PLANCYI", "Nyctalus plancyi", "Chinese Noctule", "Noctules", ["Asia"], "A medium-sized noctule from China and Taiwan; roosts in tree cavities.", 0, "Plancy"),
    ])
    g = find_genus(ch, "Barbastella")
    g["children"].extend([
        make_species("BARBASTELLA_LEUCOMELAS", "Barbastella leucomelas", "Eastern Barbastelle", "Barbastelles", ["Asia"], "An Asian barbastelle with distinctive white-tipped fur; found from the Caucasus to Iran.", 0),
        make_species("BARBASTELLA_BASARABICA", "Barbastella basarabica", "Basarab's Barbastelle", "Barbastelles", ["Europe"], "A recently described barbastelle from the Carpathians.", 0, "Basarab"),
    ])
    g = find_genus(ch, "Plecotus")
    g["children"].extend([
        make_species("PLECOTUS_SARDUS", "Plecotus sardus", "Sardinian Long-eared Bat", "Long-eared Bats", ["Europe"], "An endemic long-eared bat of Sardinia; distinguished by genetics from P. auritus.", 0),
        make_species("PLECOTUS_STREPENS", "Plecotus strepens", "Alpine Long-eared Bat", "Long-eared Bats", ["Europe"], "A recently described species from the Alps; exceptionally long ears.", 0),
        make_species("PLECOTUS_TASMANIENSIS", "Plecotus tasmaniensis", "Tasmanian Long-eared Bat", "Long-eared Bats", ["Australia"], "A poorly known species from Tasmania; related to P. auritus.", 0),
    ])
    g = ensure_genus(ch, "GENUS_MINOPTERUS", "Miniopterus", "Bent-winged Bats", "Bats with a distinctive bend in the third metacarpal; highly mobile and widely distributed.", "Long-fingered Bats")
    g["children"].extend([
        make_species("MINOPTERUS_SCHREIBERSII", "Miniopterus schreibersii", "Schreiber's Bent-winged Bat", "Long-fingered Bats", ["Europe", "Africa", "Asia"], "A highly migratory bat; the longest known bent-wing; known for long-distance movements.", 0, "Schreiber"),
        make_species("MINOPTERUS_MACRODERUS", "Miniopterus macroderus", "Large Bent-winged Bat", "Long-fingered Bats", ["Asia"], "A large species from the Philippines and Indonesia.", 0),
        make_species("MINOPTERUS_FUSCUS", "Miniopterus fuscus", "Dark Bent-winged Bat", "Long-fingered Bats", ["Asia"], "A dark brown species endemic to the Ryukyu Islands.", 0),
    ])

    return data
ENRICHERS["vespertilionidae"] = enrich_vespertilionidae

# ---------------------------------------------------------------------------
# 3. columbidae
# ---------------------------------------------------------------------------
def enrich_columbidae(data):
    ch = data["children"]
    g = find_genus(ch, "Columba")
    g["children"].extend([
        make_species("COLUMBA_ALBINUCHA", "Columba albinucha", "White-naped Pigeon", "Pigeons", ["Africa"], "A dark grey pigeon of Central African rainforests; white patch on the nape is diagnostic.", 0),
        make_species("COLUMBA_ARQUATRIS", "Columba arquatrix", "African Olive Pigeon", "Pigeons", ["Africa"], "Large yellow-eyed pigeon of African montane forests; feeds on fruit in the upper canopy.", 0),
        make_species("COLUMBA_GUINEA", "Columba guinea", "Speckled Pigeon", "Pigeons", ["Africa"], "A widespread African pigeon with rusty-red speckled wings; common in towns and farmlands.", 0),
        make_species("COLUMBA_DELEGORGUEI", "Columba delegorguei", "Delegorgue's Pigeon", "Pigeons", ["Africa"], "A small forest pigeon from eastern and southern Africa; named after the French naturalist.", 0, "Delegorgue"),
    ])
    g = find_genus(ch, "Streptopelia")
    g["children"].extend([
        make_species("STREPTOPELIA_CAPICOLA", "Streptopelia capicola", "Ring-necked Dove", "Doves", ["Africa"], "A common African dove with a distinctive black collar at the back of the neck.", 0),
        make_species("STREPTOPELIA_VINACEA", "Streptopelia vinacea", "Vinaceous Dove", "Doves", ["Africa"], "A pale vinous-pink dove of the Sahel and Sudanian savanna; named for its wine-coloured breast.", 0),
        make_species("STREPTOPELIA_LUGENS", "Streptopelia lugens", "Dusky Turtle Dove", "Doves", ["Asia", "Africa"], "Found in the Horn of Africa and southwestern Arabia; prefers juniper woodlands.", 0),
    ])
    g = find_genus(ch, "Treron")
    g["children"].extend([
        make_species("TRERON_VERNALIS", "Treron vernalis", "Pink-necked Green Pigeon", "Green Pigeons", ["Asia"], "A colourful green pigeon of Southeast Asia; males have a pink neck and orange chest.", 0),
        make_species("TRERON_CURVIROSTRA", "Treron curvirostra", "Thick-billed Green Pigeon", "Green Pigeons", ["Asia"], "Named for its unusually thick curved bill; feeds on hard drupes and figs.", 0),
        make_species("TRERON_OLAX", "Treron olax", "Little Green Pigeon", "Green Pigeons", ["Asia"], "The smallest Treron in Southeast Asia; olive-green with a yellow vent.", 0),
    ])
    g = find_genus(ch, "Patagioenas")
    g["children"].extend([
        make_species("PATAGIOENAS_PLUMBEA", "Patagioenas plumbea", "Plumbeous Pigeon", "Pigeons", ["South America"], "A dark grey Amazonian pigeon with a purplish iridescence on the neck.", 0),
        make_species("PATAGIOENAS_CAYENNENSIS", "Patagioenas cayennensis", "Pale-vented Pigeon", "Pigeons", ["South America"], "Widespread in Central and South America; distinctive pale vent and white throat patch.", 0),
        make_species("PATAGIOENAS_SUBNACEA", "Patagioenas subnacea", "Ruddy Pigeon", "Pigeons", ["South America"], "A medium-sized pigeon of lowland forests; rich rufous-brown plumage with red eyes.", 0),
    ])
    g = find_genus(ch, "Ducula")
    g["children"].extend([
        make_species("DUCULA_MYRISTICIVORA", "Ducula myristicivora", "Spice Imperial Pigeon", "Imperial Pigeons", ["Oceania"], "Endemic to the Moluccas; feeds on nutmeg and other fruits; vital seed disperser.", 0),
        make_species("DUCULA_RUFIGASTER", "Ducula rufigaster", "Rufous-bellied Imperial Pigeon", "Imperial Pigeons", ["Oceania"], "A colourful imperial pigeon from New Guinea; rufous belly and metallic green upperparts.", 0),
        make_species("DUCULA_ZOEAE", "Ducula zoaea", "Zoe's Imperial Pigeon", "Imperial Pigeons", ["Oceania"], "A beautiful species from New Guinea; grey head, purple breast, and chestnut belly.", 0),
    ])
    g = find_genus(ch, "Ptilinopus")
    g["children"].extend([
        make_species("PTILINOPUS_MARSHALLIANUS", "Ptilinopus marshallianus", "Marshall's Fruit Dove", "Fruit Doves", ["Oceania"], "A rare fruit dove from New Guinea; named after the collector.", 0, "Marshall"),
        make_species("PTILINOPUS_ORNATUS", "Ptilinopus ornatus", "Ornate Fruit Dove", "Fruit Doves", ["Oceania"], "An ornate green and yellow fruit dove from the mountains of New Guinea.", 0),
        make_species("PTILINOPUS_PEARLII", "Ptilinopus pearlii", "Pearl's Fruit Dove", "Fruit Doves", ["Oceania"], "A recently described fruit dove from Fiji; distinctive orange cap and green body.", 0),
    ])
    g = find_genus(ch, "Zenaida")
    g["children"].extend([
        make_species("ZENAIDA_ASIATICA", "Zenaida asiatica", "White-winged Dove", "Doves", ["North America"], "Common in the southern US and Mexico; expanding northward; named for bold white wing patches.", 0),
        make_species("ZENAIDA_GRACILI", "Zenaida gracili", "Eared Dove", "Doves", ["South America"], "One of the most abundant South American doves; named for the dark ear patch.", 0),
        make_species("ZENAIDA_AURITA", "Zenaida aurita", "Zenaida Dove", "Doves", ["North America"], "A Caribbean dove named after Zenaide, wife of the naturalist Charles Lucien Bonaparte.", 0),
    ])
    g = ensure_genus(ch, "GENUS_TURTUR", "Turtur", "African Wood Doves", "Small terrestrial doves of sub-Saharan Africa that produce a distinctive whistling wing sound in flight.", "Doves")
    g["children"].extend([
        make_species("TURTUR_CHALCOSPILOS", "Turtur chalcospilos", "Emerald-spotted Wood Dove", "Doves", ["Africa"], "Named for metallic green spots on wings; produces low resonant cooing from forest floor.", 0),
        make_species("TURTUR_ABYSINICUS", "Turtur abyssinicus", "Black-billed Wood Dove", "Doves", ["Africa"], "A Sahelian species; black bill distinguishes it from the similar emerald-spotted dove.", 0),
        make_species("TURTUR_AFER", "Turtur afer", "Blue-spotted Wood Dove", "Doves", ["Africa"], "Widespread in West and Central African forests; iridescent blue wing spots.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CALOENAS", "Caloenas", "Nicobar Pigeon", "Large, iridescent ground pigeons of Southeast Asian islands; the only living relative of the dodo.", "Ground Pigeons")
    g["children"].extend([
        make_species("CALOENAS_NICOBARICA", "Caloenas nicobarica", "Nicobar Pigeon", "Ground Pigeons", ["Asia", "Oceania"], "The closest living relative of the extinct dodo; iridescent bronze and green plumage; forages on forest floors of small islands.", 0),
    ])
    # Extra species
    g = find_genus(ch, "Columba")
    g["children"].extend([
        make_species("COLUMBA_PALUMBOIDES", "Columba palumboides", "Andaman Wood Pigeon", "Pigeons", ["Asia"], "A large dark pigeon endemic to the Andaman and Nicobar Islands.", 0),
        make_species("COLUMBA_ELPHINSTONII", "Columba elphinstonii", "Nilgiri Wood Pigeon", "Pigeons", ["Asia"], "A vulnerable species from the Western Ghats of India; distinctive maroon mantle.", 0, "Elphinstone"),
        make_species("COLUMBA_TORRINGTONIAE", "Columba torringtoniae", "Sri Lanka Wood Pigeon", "Pigeons", ["Asia"], "Endemic to Sri Lanka's montane forests; purplish-brown upperparts.", 0, "Torrington"),
        make_species("COLUMBA_PUNICEA", "Columba punicea", "Pale-capped Pigeon", "Pigeons", ["Asia"], "A rare pigeon of Southeast Asian lowland forests; distinctive silvery crown.", 0),
        make_species("COLUMBA_ARGUATRICES", "Columba arquatrices", "Southern Rock Dove", "Pigeons", ["Africa"], "A recently split species from the rock dove complex; restricted to southern Africa.", 0),
    ])
    g = find_genus(ch, "Patagioenas")
    g["children"].extend([
        make_species("PATAGIOENAS_PLUMBEA", "Patagioenas plumbea", "Plumbeous Pigeon", "Pigeons", ["South America"], "A grey pigeon of Amazonian rainforests; dark grey overall with a pale eye.", 0),
        make_species("PATAGIOENAS_SUBNIGRA", "Patagioenas subnigra", "Blackish Pigeon", "Pigeons", ["South America"], "A dark pigeon of the Andes; inhabits cloud forest at 1500-3000 m.", 0),
        make_species("PATAGIOENAS_SPEZIOSA", "Patagioenas speziosa", "Sealed Pigeon", "Pigeons", ["South America"], "A large Amazonian pigeon with scaled neck pattern.", 0),
        make_species("PATAGIOENAS_FASCIATA", "Patagioenas fasciata", "Band-tailed Pigeon", "Pigeons", ["North America", "South America"], "A large North and South American pigeon; grey with white crescent on nape.", 0),
        make_species("PATAGIOENAS_ARAMEA", "Patagioenas aramea", "Red-billed Pigeon", "Pigeons", ["North America"], "A widespread Caribbean and Central American pigeon; red bill with white tip.", 0),
    ])
    g = find_genus(ch, "Streptopelia")
    g["children"].extend([
        make_species("STREPTOPELIA_ORIENTALIS", "Streptopelia orientalis", "Oriental Turtle Dove", "Doves", ["Asia"], "A large dove of East Asia; dark scalloped back and pale grey tail tips.", 0),
        make_species("STREPTOPELIA_BITORQUATA", "Streptopelia bitorquata", "Island Collared Dove", "Doves", ["Asia"], "A dove of Indonesian islands; two black collar bands on the nape.", 0),
        make_species("STREPTOPELIA_LUGENS", "Streptopelia lugens", "Dusky Turtle Dove", "Doves", ["Africa"], "A dark dove of the Ethiopian highlands; blackish spots on the breast.", 0),
        make_species("STREPTOPELIA_HYPOPYRRA", "Streptopelia hypopyrrha", "Adamawa Turtle Dove", "Doves", ["Africa"], "A West African dove restricted to the Adamawa Plateau.", 0),
    ])
    g = find_genus(ch, "Ducula")
    g["children"].extend([
        make_species("DUCULA_MYRISTICIVORA", "Ducula myristicivora", "Spice Imperial Pigeon", "Imperial Pigeons", ["Asia"], "A grey and maroon imperial pigeon of Indonesian spice islands.", 0),
        make_species("DUCULA_RUBRICERA", "Ducula rubricera", "Red-knobbed Imperial Pigeon", "Imperial Pigeons", ["Asia"], "A large pigeon of the Bismarck Archipelago and Solomon Islands; red bill knob.", 0),
        make_species("DUCULA_CONCINNA", "Ducula concinna", "Elegant Imperial Pigeon", "Imperial Pigeons", ["Asia"], "A beautifully coloured imperial pigeon with a bronze-green sheen.", 0),
        make_species("DUCULA_FORSTENI", "Ducula forsteni", "White-bellied Imperial Pigeon", "Imperial Pigeons", ["Asia"], "A Sulawesi endemic; named after the Dutch naturalist Forsten.", 0, "Forsten"),
    ])
    g = ensure_genus(ch, "GENUS_MACROPYGIA", "Macropygia", "Cuckoo-doves", "Slender long-tailed doves of Southeast Asian and Australasian forests.", "Doves")
    g["children"].extend([
        make_species("MACROPYGIA_MAGNA", "Macropygia magna", "Large Cuckoo-dove", "Doves", ["Asia"], "A large cuckoo-dove from Sulawesi and neighbouring islands.", 0),
        make_species("MACROPYGIA_NIGRIROSTRIS", "Macropygia nigrirostris", "Barred Cuckoo-dove", "Doves", ["Asia"], "A barred species from New Guinea and the Bismarck Archipelago.", 0),
        make_species("MACROPYGIA_EMBEROIDES", "Macropygia emberoides", "Rufous Cuckoo-dove", "Doves", ["Asia"], "A rufous-coloured species from the Philippines; long graduated tail.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CALOENAS", "Caloenas", "Nicobar Pigeons", "A single living species; iridescent plumage and long hackles on neck.", "Pigeons")
    g["children"].extend([
        make_species("CALOENAS_NICOBARICA", "Caloenas nicobarica", "Nicobar Pigeon", "Pigeons", ["Asia"], "The sole surviving Caloenas; green and blue iridescent plumage; long neck hackles.", 0),
    ])

    return data
ENRICHERS["columbidae"] = enrich_columbidae

# ---------------------------------------------------------------------------
# 4. viperidae
# ---------------------------------------------------------------------------
def enrich_viperidae(data):
    ch = data["children"]
    g = find_genus(ch, "Vipera")
    g["children"].extend([
        make_species("VIPERA_OLGUNI", "Vipera olguni", "Olgun's Viper", "True Vipers", ["Asia"], "A recently described mountain viper from northeastern Turkey; limited to alpine meadows above 2000 m.", 0, "Olgun"),
        make_species("VIPERA_DAHLSENI", "Vipera dahlseni", "Dahlsen's Viper", "True Vipers", ["Asia"], "A poorly known viper from Turkey and Iran; high elevation specialist.", 0),
    ])
    g = find_genus(ch, "Montivipera")
    g["children"].extend([
        make_species("MONTIVIPERA_LATIFI", "Montivipera latifi", "Latifi's Mountain Viper", "True Vipers", ["Asia"], "A critically endangered viper from the Elburz Mountains of Iran; one of the rarest vipers.", 0, "Latifi"),
        make_species("MONTIVIPERA_BORNMUellerI", "Montivipera bornmuelleri", "Bornmueller's Viper", "True Vipers", ["Asia"], "From the mountains of Lebanon and Israel; threatened by habitat loss.", 0, "Bornmueller"),
    ])
    g = find_genus(ch, "Bitis")
    g["children"].extend([
        make_species("BITIS_SCHNEIDERI", "Bitis schneideri", "Schneider's Puff Adder", "Vipers", ["Africa"], "A small, richly patterned Bitis from the Namib Desert; sidewinding locomotion on sand.", 0, "Schneider"),
        make_species("BITIS_WORTHINGTONI", "Bitis worthingtoni", "Worthington's Viper", "Vipers", ["Africa"], "A highland species from the Kenyan Rift Valley; one of the least-known Bitis.", 0, "Worthington"),
        make_species("BITIS_HERALDO", "Bitis heraldica", "Angolan Puff Adder", "Vipers", ["Africa"], "Endemic to Angola's central highlands; distinguished by its unique scale colouration.", 0),
    ])
    g = find_genus(ch, "Cerastes")
    g["children"].extend([
        make_species("CERASTES_HERPETES", "Cerastes herpetes", "Saharan Horned Viper", "Vipers", ["Africa"], "A recently recognised cryptic species within the C. cerastes complex.", 0),
        make_species("CERASTES_BOULENGERI", "Cerastes boulengeri", "Boulenger's Horned Viper", "Vipers", ["Africa"], "Named after the Belgian naturalist; found in rocky outcrops of the Sahara.", 0, "Boulenger"),
    ])
    g = find_genus(ch, "Echis")
    g["children"].extend([
        make_species("ECHIS_LEAKEYI", "Echis leakeyi", "Leakey's Saw-scaled Viper", "Vipers", ["Africa"], "A large Echis from East Africa; named after the Leakey family of paleontologists.", 0, "Leakey"),
        make_species("ECHIS_JOGERI", "Echis jogeri", "Joger's Saw-scaled Viper", "Vipers", ["Africa"], "A recently described West African species from Mali and Senegal.", 0, "Joger"),
    ])
    g = find_genus(ch, "Atheris")
    g["children"].extend([
        make_species("ATHERIS_BARBOURI", "Atheris barbouri", "Barbour's Bush Viper", "Vipers", ["Africa"], "A small highland bush viper from Tanzania; named after Thomas Barbour.", 0, "Thomas Barbour"),
        make_species("ATHERIS_DESAIXI", "Atheris desaixi", "Desaix's Bush Viper", "Vipers", ["Africa"], "A striking yellow and black bush viper from the Kenyan highlands; arboreal ambush predator.", 0, "Desaix"),
    ])
    g = find_genus(ch, "Crotalus")
    g["children"].extend([
        make_species("CROTALUS_CERASTES", "Crotalus cerastes", "Sidewinder", "Pit Vipers", ["North America"], "A desert rattlesnake with a unique sidewinding locomotion; moves sideways across loose sand.", 0),
        make_species("CROTALUS_LEPIDUS", "Crotalus lepidus", "Rock Rattlesnake", "Pit Vipers", ["North America"], "A beautiful grey-green rattlesnake from southwestern US and Mexico; prefers rocky slopes.", 0),
        make_species("CROTALUS_ORNATUS", "Crotalus ornatus", "Ornate Black-tailed Rattlesnake", "Pit Vipers", ["North America"], "Formerly a subspecies of C. molossus; recent genetic studies elevated it to full species.", 0),
    ])
    g = find_genus(ch, "Bothrops")
    g["children"].extend([
        make_species("BOTHROPS_MOOJENI", "Bothrops moojeni", "Brazilian Lancehead", "Pit Vipers", ["South America"], "A large aggressive lancehead from central and southeastern Brazil; named after the Moojen collector.", 0),
        make_species("BOTHROPS_NEUWIDI", "Bothrops neuwidi", "Neuwied's Lancehead", "Pit Vipers", ["South America"], "A complex of cryptic species from eastern and southern South America.", 0, "Neuwied"),
        make_species("BOTHROPS_ERITROMELAS", "Bothrops eritromelas", "Eritromelas Lancehead", "Pit Vipers", ["South America"], "A small Bothrops from the Atlantic Forest of Brazil; black tail tip used as caudal lure.", 0),
    ])
    g = find_genus(ch, "Trimeresurus")
    g["children"].extend([
        make_species("TRIMERESURUS_HAGENI", "Trimeresurus hageni", "Hagen's Green Pit Viper", "Pit Vipers", ["Asia"], "A large green pit viper from Sumatra and Borneo; named after the collector.", 0, "Hagen"),
        make_species("TRIMERESURUS_POPEORUM", "Trimeresurus popeorum", "Pope's Green Pit Viper", "Pit Vipers", ["Asia"], "Widespread from northeastern India to Vietnam; bright green with a red tail.", 0),
    ])
    g = ensure_genus(ch, "GENUS_BOTHROPSIS", "Bothropsis", "Anaconda Vipers", "A proposed genus for certain South American arboreal viperids with prehensile tails.", "Pit Vipers")
    g["children"].extend([
        make_species("BOTHROPSIS_BILINEATUS", "Bothropsis bilineatus", "Two-lined Forest Pit Viper", "Pit Vipers", ["South America"], "An arboreal viper from the Amazon; two yellow lateral stripes on a green body.", 0),
        make_species("BOTHROPSIS_TAENIATUS", "Bothropsis taeniatus", "Striped Forest Pit Viper", "Pit Vipers", ["South America"], "Found in Ecuadorian and Peruvian Amazon; prehensile tail for gripping branches.", 0),
    ])
    g = ensure_genus(ch, "GENUS_MIXCOATL", "Mixcoatl", "Mexican Jumping Pit Vipers", "Small, secretive pit vipers of Mexican highlands that vibrate their tails rapidly when threatened.", "Pit Vipers")
    g["children"].extend([
        make_species("MIXCOATL_BICOLOR", "Mixcoatl bicolor", "Two-coloured Jumping Viper", "Pit Vipers", ["North America"], "A small pit viper from the Sierra Madre Oriental; striking black and white banding.", 0),
        make_species("MIXCOATL_TAENIATUS", "Mixcoatl taeniatus", "Striped Jumping Viper", "Pit Vipers", ["North America"], "Endemic to Costa Rica and western Panama; named for its striped body pattern.", 0),
        make_species("MIXCOATL_MELANURUS", "Mixcoatl melanurus", "Black-tailed Jumping Viper", "Pit Vipers", ["North America"], "A Mexican species with a black tail tip used as a caudal lure for small prey.", 0),
    ])
    g = find_genus(ch, "Vipera")
    g["children"].extend([
        make_species("VIPERA_MONTICOLA", "Vipera monticola", "Mountain Viper", "True Vipers", ["Africa"], "A small high-altitude viper from the Atlas Mountains of Morocco; rarely exceeds 35 cm.", 0),
        make_species("VIPERA_LATIFII", "Vipera latifii", "Latifi's Viper", "True Vipers", ["Asia"], "A critically endangered viper from a single valley in Iran's Alborz Mountains.", 0, "Latifi"),
        make_species("VIPERA_TRANSVERSA", "Vipera transvera", "Transverse Viper", "True Vipers", ["Europe"], "A Balkan species with distinctive transverse dorsal bars.", 0),
        make_species("VIPERA_RENARDI", "Vipera renardi", "Renard's Viper", "True Vipers", ["Europe", "Asia"], "A Eurasian meadow-steppe viper; often separated from V. ursinii.", 0, "Renard"),
    ])
    g = find_genus(ch, "Bitis")
    g["children"].extend([
        make_species("BITIS_INORNATA", "Bitis inornata", "Plain Puff Adder", "Adders", ["Africa"], "A recently described species from South Africa; drab colouration, no pattern.", 0),
        make_species("BITIS_ALBANICA", "Bitis albanica", "Albany Adder", "Adders", ["Africa"], "A small adder restricted to the Eastern Cape, South Africa; grey with dark zigzag.", 0),
        make_species("BITIS_HERALDI", "Bitis heraldi", "Herald's Adder", "Adders", ["Africa"], "A small Angolan adder with a pattern of dark saddles on a tan background.", 0, "Herald"),
        make_species("BITIS_SCHNEIDERI", "Bitis schneideri", "Schneider's Adder", "Adders", ["Africa"], "The world's smallest viper; full-grown adults reach only 20 cm; lives in Namib sand dunes.", 0, "Schneider"),
    ])
    g = find_genus(ch, "Crotalus")
    g["children"].extend([
        make_species("CROTALUS_ERICSANTHI", "Crotalus ericsanthi", "Erickson's Rattlesnake", "Pit Vipers", ["South America"], "A recently described rattlesnake from the Brazilian Cerrado.", 0, "Erickson"),
        make_species("CROTALUS_TLALOCI", "Crotalus tlaloci", "Tlaloc's Rattlesnake", "Pit Vipers", ["North America"], "A highland rattlesnake from the Trans-Mexican Volcanic Belt; named after the Aztec rain god.", 0, "Tlaloc"),
        make_species("CROTALUS_RADIENS", "Crotalus radiens", "West Coast Rattlesnake", "Pit Vipers", ["North America"], "A Mexican species from the Pacific slope; grey with diamond-shaped blotches.", 0),
    ])
    g = find_genus(ch, "Bothrops")
    g["children"].extend([
        make_species("BOTHROPS_ISABELAE", "Bothrops isabelae", "Isabel's Lancehead", "Pit Vipers", ["South America"], "A recently described lancehead from the Brazilian Atlantic Forest.", 0, "Isabel"),
        make_species("BOTHROPS_SAOLEOPOLDENSIS", "Bothrops saoleopoldensis", "São Leopoldo Lancehead", "Pit Vipers", ["South America"], "A species from southern Brazil; cryptic coloration with dark diamond pattern.", 0),
        make_species("BOTHROPS_URASTI", "Bothrops urasti", "Urasti's Lancehead", "Pit Vipers", ["South America"], "A rare lancehead from the Tumucumaque region of the Amazon.", 0, "Urasti"),
        make_species("BOTHROPS_SANCTACRUZIS", "Bothrops sanctacruzis", "Santa Cruz Lancehead", "Pit Vipers", ["South America"], "A small species from the Bolivian Amazon; grey-brown with darker hourglass markings.", 0),
    ])
    g = find_genus(ch, "Echis")
    g["children"].extend([
        make_species("ECHIS_LEOGADI", "Echis leogadi", "Leogard's Carpet Viper", "Carpet Vipers", ["Africa"], "A recently split species from East Africa; fine serrated scale texture.", 0, "Leogard"),
        make_species("ECHIS_NUMMIFER", "Echis nummifer", "Coin-marked Carpet Viper", "Carpet Vipers", ["Africa"], "A North African species with distinctive coin-shaped dorsal markings.", 0),
    ])
    g = ensure_genus(ch, "GENUS_LACHESIS", "Lachesis", "Bushmasters", "The longest vipers in the world; tropical pit vipers of Central and South American rainforests.", "Pit Vipers")
    g["children"].extend([
        make_species("LACHESIS_ACROCHORDA", "Lachesis acrochorda", "Central American Bushmaster", "Pit Vipers", ["North America"], "A large dark bushmaster from Nicaragua to Ecuador; up to 2.5 m.", 0),
        make_species("LACHESIS_MUTA", "Lachesis muta", "South American Bushmaster", "Pit Vipers", ["South America"], "The largest viper in the New World; reaches 3.5 m; nocturnal and terrestrial.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ATHERIS", "Atheris", "Bush Vipers", "Arboreal African vipers with keeled scales and prehensile tails.", "Pit Vipers")
    g["children"].extend([
        make_species("ATHERIS_NITSCHEI", "Atheris nitschei", "Nitsche's Bush Viper", "Pit Vipers", ["Africa"], "A bright green bush viper from East Africa; found in montane forests.", 0, "Nitsche"),
        make_species("ATHERIS_CERATOPHORA", "Atheris ceratophora", "Horned Bush Viper", "Pit Vipers", ["Africa"], "A spectacular viper from Tanzania; distinctive horn-like scales above each eye.", 0),
        make_species("ATHERIS_KATANGENSIS", "Atheris katangensis", "Katanga Bush Viper", "Pit Vipers", ["Africa"], "A recently described bush viper from the Katanga region of the DRC.", 0),
    ])

    return data
ENRICHERS["viperidae"] = enrich_viperidae

# ---------------------------------------------------------------------------
# 5. elapidae
# ---------------------------------------------------------------------------
def enrich_elapidae(data):
    ch = data["children"]
    g = find_genus(ch, "Naja")
    g["children"].extend([
        make_species("NAJA_AUREA", "Naja aurea", "Golden Cobra", "Cobras", ["Africa"], "A large golden-yellow cobra from southern Africa; sometimes considered a colour morph of N. nivea.", 0),
        make_species("NAJA_SENEGALENSIS", "Naja senegalensis", "Senegalese Cobra", "Cobras", ["Africa"], "A West African spitting cobra recently split from N. nigricollis; highly venomous.", 0),
    ])
    g = find_genus(ch, "Ophiophagus")
    g["children"].extend([
        make_species("OPHIOPHAGUS_KAELINII", "Ophiophagus kaelinii", "Kaelin's King Cobra", "Cobras", ["Asia"], "A recently described cryptic species of king cobra from Sulawesi and the Philippines.", 0, "Kaelin"),
    ])
    g = find_genus(ch, "Bungarus")
    g["children"].extend([
        make_species("BUNGARUS_FLAVICEPS", "Bungarus flaviceps", "Red-headed Krait", "Kraits", ["Asia"], "A striking krait with a bright red head and black body; found in Thailand and Malaysia.", 0),
        make_species("BUNGARUS_SLOWINSKII", "Bungarus slowinskii", "Slowinski's Krait", "Kraits", ["Asia"], "Named after the herpetologist; a rare krait from Myanmar and Thailand.", 0, "Slowinski"),
    ])
    g = find_genus(ch, "Micrurus")
    g["children"].extend([
        make_species("MICRURUS_ALTROSTRIS", "Micrurus altirostris", "High-nosed Coral Snake", "Coral Snakes", ["South America"], "A coral snake from southern Brazil and Uruguay; black snout extending onto the head.", 0),
        make_species("MICRURUS_SPIXII", "Micrurus spixii", "Spix's Coral Snake", "Coral Snakes", ["South America"], "A large Amazonian coral snake; named after Johann Baptist von Spix.", 0, "Johann von Spix"),
        make_species("MICRURUS_DIASTEMA", "Micrurus diastema", "Variable Coral Snake", "Coral Snakes", ["North America"], "A Mexican coral snake with highly variable banding patterns; mimics several co-occurring species.", 0),
    ])
    g = find_genus(ch, "Oxyuranus")
    g["children"].extend([
        make_species("OXYURANUS_TEMPUSORIALIS", "Oxyuranus temporalit", "Western Taipan", "Taipans", ["Oceania"], "Recently described; restricted to the western Nullarbor Plain; the least-known taipan.", 0),
    ])
    g = find_genus(ch, "Pseudonaja")
    g["children"].extend([
        make_species("PSEUDONAJA_AFFINIS", "Pseudonaja affinis", "Dugite", "Brown Snakes", ["Oceania"], "A highly venomous brown snake from southwestern Australia; dangerously common near Perth.", 0),
        make_species("PSEUDONAJA_INGRAMI", "Pseudonaja ingrami", "Ingram's Brown Snake", "Brown Snakes", ["Oceania"], "A rare brown snake from the Tanami Desert; named after the collector.", 0, "Ingram"),
    ])
    g = find_genus(ch, "Acanthophis")
    g["children"].extend([
        make_species("ACANTHOPHIS_WELLSI", "Acanthophis wellsi", "Wells' Death Adder", "Death Adders", ["Oceania"], "A small-patterned death adder from Western Australia; ambush predator with caudal lure.", 0, "Wells"),
    ])
    g = find_genus(ch, "Pseudechis")
    g["children"].extend([
        make_species("PSEUDECHIS_COLLETTI", "Pseudechis colletti", "Collett's Black Snake", "Black Snakes", ["Oceania"], "A striking black snake with cream banding from central Queensland; venom shows potent myotoxicity.", 0, "Collett"),
        make_species("PSEUDECHIS_BUTLERI", "Pseudechis butleri", "Butler's Black Snake", "Black Snakes", ["Oceania"], "A recently described species from the Kimberley region; restricted to sandstone escarpments.", 0, "Butler"),
    ])
    g = find_genus(ch, "Hydrophis")
    g["children"].extend([
        make_species("HYDROPHIS_CAERULESCENS", "Hydrophis caerulescens", "Dwarf Sea Snake", "Sea Snakes", ["Asia", "Oceania"], "A small sea snake from the Indian Ocean; pale bluish bands on a grey background.", 0),
        make_species("HYDROPHIS_ELEGANS", "Hydrophis elegans", "Elegant Sea Snake", "Sea Snakes", ["Oceania"], "A large slender sea snake from Australian waters; reaches 2 m.", 0),
        make_species("HYDROPHIS_MACRODUS", "Hydrophis macrodus", "Big-headed Sea Snake", "Sea Snakes", ["Asia"], "Found in Southeast Asian coastal waters; unusually large head and small body.", 0),
    ])
    g = find_genus(ch, "Laticauda")
    g["children"].extend([
        make_species("LATICAUDA_GUINEAI", "Laticauda guineai", "Guinea Sea Krait", "Sea Kraits", ["Oceania"], "A robust sea krait from Papua New Guinea; named after the collector.", 0, "Guinea"),
        make_species("LATICAUDA_CROKERI", "Laticauda crokeri", "Croker's Sea Krait", "Sea Kraits", ["Oceania"], "A small sea krait from the Solomon Islands; often found in coral reef lagoons.", 0, "Croker"),
    ])
    g = find_genus(ch, "Demansia")
    g["children"].extend([
        make_species("DEMANSIA_RUFIPES", "Demansia rufipes", "Red-footed Whipsnake", "Whipsnakes", ["Oceania"], "A slender fast-moving whip snake from northern Australia; reddish limbs and tail tip.", 0),
        make_species("DEMANSIA_SIMILE", "Demansia simile", "Simile Whipsnake", "Whipsnakes", ["Oceania"], "Recently split from D. psammophis; found in Queensland and New South Wales.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ASPIDELAPS", "Aspidelaps", "Shield-nose Cobras", "Small African elapids with a distinctive enlarged rostral scale used for burrowing.", "Cobras")
    g["children"].extend([
        make_species("ASPIDELAPS_SCUTATUS", "Aspidelaps scutatus", "Shield-nose Cobra", "Cobras", ["Africa"], "A burrowing cobra from southern Africa; flattened spade-like snout for digging in sand.", 0),
        make_species("ASPIDELAPS_LUBRICUS", "Aspidelaps lubricus", "Coral Shield-nose Cobra", "Cobras", ["Africa"], "A beautiful coral-pink and black banded species from South Africa and Namibia.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HEMACHATUS", "Hemachatus", "Rinkhals", "A monotypic genus of spitting cobra from southern Africa that feigns death dramatically.", "Cobras")
    g["children"].extend([
        make_species("HEMACHATUS_HEMACHATUS", "Hemachatus hemachatus", "Rinkhals", "Cobras", ["Africa"], "Not a true cobra but a powerful spitter; can spray venom up to 3 m; plays dead by rolling onto its back with mouth open.", 0),
    ])
    g = ensure_genus(ch, "GENUS_WALTERINNESIA", "Walterinnesia", "Desert Black Snake", "Heavy-bodied black elapids of Middle Eastern deserts; nocturnal and fossorial.", "Cobras")
    g["children"].extend([
        make_species("WALTERINNESIA_AEGYPTIA", "Walterinnesia aegyptia", "Egyptian Desert Black Snake", "Cobras", ["Asia", "Africa"], "A jet-black elapid from the Middle East; highly venomous but rarely encountered.", 0),
        make_species("WALTERINNESIA_MORGANI", "Walterinnesia morgani", "Morgan's Desert Black Snake", "Cobras", ["Asia"], "Recently split from W. aegyptia; found from Syria to Iran.", 0, "Morgan"),
    ])
    g = find_genus(ch, "Naja")
    g["children"].extend([
        make_species("NAJA_SAGITTIFERA", "Naja sagittifera", "Arrow Cobra", "Cobras", ["Asia"], "A recently described species from Myanmar; arrow-shaped pattern on hood.", 0),
        make_species("NAJA_ANCHIETAE", "Naja anchietae", "Anchieta's Cobra", "Cobras", ["Africa"], "A large brown cobra from southern Africa; diurnal and active hunter.", 0, "Anchieta"),
        make_species("NAJA_SENEGALENSIS", "Naja senegalensis", "Senegalese Cobra", "Cobras", ["Africa"], "A West African species; grey-brown with a dark throat; closely related to N. haje.", 0),
        make_species("NAJA_MANDALAYENSIS", "Naja mandalayensis", "Mandalay Cobra", "Cobras", ["Asia"], "A spitting cobra from central Myanmar; named after the ancient city of Mandalay.", 0),
    ])
    g = find_genus(ch, "Micrurus")
    g["children"].extend([
        make_species("MICRURUS_BERNARDOI", "Micrurus bernardoi", "Bernardo's Coral Snake", "Coral Snakes", ["South America"], "A recently described coral snake from the Brazilian Amazon.", 0, "Bernardo"),
        make_species("MICRURUS_IBIBOBA", "Micrurus ibiboba", "Ibiboba Coral Snake", "Coral Snakes", ["South America"], "A yellow-banded coral snake from the Gran Chaco region.", 0),
        make_species("MICRURUS_THEVENETI", "Micrurus theveneti", "Thevenet's Coral Snake", "Coral Snakes", ["South America"], "A rare coral snake from the Peruvian Amazon; triadal colour pattern.", 0, "Thevenet"),
        make_species("MICRURUS_MARGINATUS", "Micrurus marginatus", "Margined Coral Snake", "Coral Snakes", ["South America"], "A Brazilian species with broad black bands edged in white.", 0),
        make_species("MICRURUS_WAGLERI", "Micrurus wagleri", "Wagler's Coral Snake", "Coral Snakes", ["South America"], "A distinctive black-tailed coral snake from the Andes.", 0, "Wagler"),
    ])
    g = find_genus(ch, "Bungarus")
    g["children"].extend([
        make_species("BUNGARUS_LIVIDUS", "Bungarus lividus", "Lesser Black Krait", "Kraits", ["Asia"], "A dark grey krait from northeast India and Bangladesh; nocturnal and venomous.", 0),
        make_species("BUNGARUS_SULPHUREUS", "Bungarus sulphureus", "Yellow Krait", "Kraits", ["Asia"], "A pale yellow krait from Myanmar; feeds primarily on other snakes.", 0),
        make_species("BUNGARUS_WANGI", "Bungarus wangi", "Wang's Krait", "Kraits", ["Asia"], "A recently described krait from China; banded black-and-white pattern.", 0, "Wang"),
    ])
    g = find_genus(ch, "Dendroaspis")
    g["children"].extend([
        make_species("DENDROASPIS_NEBULOSUS", "Dendroaspis nebulosus", "Clouded Mamba", "Mambas", ["Africa"], "A rarely seen mamba from the Central African forests; dark blue-grey with pale edges.", 0),
        make_species("DENDROASPIS_ANGUSTICEPS", "Dendroaspis angusticeps", "Eastern Green Mamba", "Mambas", ["Africa"], "A brilliant green arboreal mamba from coastal East Africa; shy but highly venomous.", 0),
        make_species("DENDROASPIS_JAMESONI", "Dendroaspis jamesoni", "Jameson's Mamba", "Mambas", ["Africa"], "A large mamba of Central and West African forests; green with black tail.", 0, "Jameson"),
    ])
    g = find_genus(ch, "Oxyuranus")
    g["children"].extend([
        make_species("OXYURANUS_TEMPORALIS", "Oxyuranus temporalis", "Western Taipan", "Taipans", ["Australia"], "A recently discovered species from the remote Kimberley region of Western Australia.", 0),
        make_species("OXYURANUS_SMARTI", "Oxyuranus smarti", "Smart's Taipan", "Taipans", ["Australia"], "A newly described taipan from the uplands of New Guinea.", 0, "Smart"),
    ])
    g = ensure_genus(ch, "GENUS_MICRUROIDES", "Micruroides", "Sonoran Coral Snakes", "A small genus restricted to the Sonoran Desert; red, yellow and black bands.", "Coral Snakes")
    g["children"].extend([
        make_species("MICRUROIDES_EURYANTHUS", "Micruroides euryanthus", "Sonoran Coral Snake", "Coral Snakes", ["North America"], "A small coral snake from Arizona and Mexico; the only Micruroides species; mild venom.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ACANTHOPHIS", "Acanthophis", "Death Adders", "Short stout elapids with a broad triangular head; ambush predators of Australasia.", "Death Adders")
    g["children"].extend([
        make_species("ACANTHOPHIS_HAWKEI", "Acanthophis hawkei", "Hawke's Death Adder", "Death Adders", ["Australia"], "A recently described species from the Barkly Tableland of northern Australia.", 0, "Hawke"),
        make_species("ACANTHOPHIS_CERAMENSIS", "Acanthophis ceramensis", "Ceram Death Adder", "Death Adders", ["Asia"], "A poorly known species from the island of Seram, Indonesia.", 0),
        make_species("ACANTHOPHIS_PILSBRYI", "Acanthophis pilsbryi", "Pilsbry's Death Adder", "Death Adders", ["Australia"], "A species from the Pilbara region of Western Australia.", 0, "Pilsbry"),
    ])

    return data
ENRICHERS["elapidae"] = enrich_elapidae

# ---------------------------------------------------------------------------
# 6. sciuridae
# ---------------------------------------------------------------------------
def enrich_sciuridae(data):
    ch = data["children"]
    g = find_genus(ch, "Sciurus")
    g["children"].extend([
        make_species("SCIURUS_NIGER", "Sciurus niger", "Eastern Fox Squirrel", "Tree Squirrels", ["North America"], "The largest tree squirrel in North America; highly variable coat from grey to black to orange.", 10),
        make_species("SCIURUS_ABERTI", "Sciurus aberti", "Abert's Squirrel", "Tree Squirrels", ["North America"], "A tassel-eared squirrel of Ponderosa pine forests in the southwestern US and Mexico.", 0),
        make_species("SCIURUS_COLLIAEI", "Sciurus colliaei", "Collie's Squirrel", "Tree Squirrels", ["North America"], "A Mexican squirrel named after the Scottish naturalist; found in thorn forests.", 0, "Collie"),
        make_species("SCIURUS_GRANATENSIS", "Sciurus granatensis", "Red-tailed Squirrel", "Tree Squirrels", ["South America", "North America"], "A colourful Neotropical squirrel ranging from Costa Rica to Venezuela; bright red tail.", 0),
    ])
    g = find_genus(ch, "Tamias")
    g["children"].extend([
        make_species("TAMIAS_MINIMUS", "Tamias minimus", "Least Chipmunk", "Chipmunks", ["North America"], "The smallest chipmunk; found across western North America from Canada to Mexico.", 0),
        make_species("TAMIAS_AMOENUS", "Tamias amoenus", "Yellow-pine Chipmunk", "Chipmunks", ["North America"], "A bright-coloured chipmunk of the western US; known for its high-pitched bird-like calls.", 0),
        make_species("TAMIAS_PALMERI", "Tamias palmeri", "Palmer's Chipmunk", "Chipmunks", ["North America"], "A rare chipmunk restricted to the Spring Mountains of Nevada; threatened by climate change.", 0, "Palmer"),
    ])
    g = find_genus(ch, "Marmota")
    g["children"].extend([
        make_species("MARMOTA_FLAVIVENTRIS", "Marmota flaviventris", "Yellow-bellied Marmot", "Marmots", ["North America"], "The most common marmot in the western US; vivid yellow belly and reddish-brown rump.", 0),
        make_species("MARMOTA_CALIGATA", "Marmota caligata", "Hoary Marmot", "Marmots", ["North America"], "A large silvery-grey marmot of alpine talus slopes; whistles loudly to alert the colony.", 0),
        make_species("MARMOTA_OLYMPUS", "Marmota olympus", "Olympic Marmot", "Marmots", ["North America"], "Endemic to the Olympic Peninsula; the only marmot confined entirely to a single mountain range.", 0),
    ])
    g = find_genus(ch, "Pteromys")
    g["children"].extend([
        make_species("PTEROMYS_MOMONGA", "Pteromys momonga", "Japanese Flying Squirrel", "Flying Squirrels", ["Asia"], "A small nocturnal flying squirrel endemic to Japan; glides between trees using its patagium.", 0),
        make_species("PTEROMYS_SAMPOENSIS", "Pteromys sampoensis", "Sampo Flying Squirrel", "Flying Squirrels", ["Asia"], "A recently described Japanese flying squirrel from Shikoku; separated by genetic analysis.", 0),
    ])
    g = find_genus(ch, "Spermophilus")
    g["children"].extend([
        make_species("SPERMOPHILUS_RICHARDSONII", "Spermophilus richardsonii", "Richardson's Ground Squirrel", "Ground Squirrels", ["North America"], "Common across the northern Great Plains; hibernates 8-9 months per year; named after John Richardson.", 0, "John Richardson"),
        make_species("SPERMOPHILUS_BELDINGI", "Spermophilus beldingi", "Belding's Ground Squirrel", "Ground Squirrels", ["North America"], "A social ground squirrel of the Sierra Nevada; gives alarm calls warning kin about predators.", 0, "Belding"),
        make_species("SPERMOPHILUS_ELEGANS", "Spermophilus elegans", "Wyoming Ground Squirrel", "Ground Squirrels", ["North America"], "Found in the Intermountain West; cycles through abundance peaks every 3-4 years.", 0),
    ])
    g = ensure_genus(ch, "GENUS_XERUS", "Xerus", "African Ground Squirrels", "Terrestrial squirrels of sub-Saharan Africa; short coarse fur and long tail for balancing.", "Ground Squirrels")
    g["children"].extend([
        make_species("XERUS_INAURIS", "Xerus inauris", "Cape Ground Squirrel", "Ground Squirrels", ["Africa"], "A highly social ground squirrel of southern Africa; uses its bushy tail as a sunshade.", 0),
        make_species("XERUS_RUTILUS", "Xerus rutilus", "Unstriped Ground Squirrel", "Ground Squirrels", ["Africa"], "Found in the Horn of Africa; the only Xerus lacking dorsal stripes.", 0),
        make_species("XERUS_ERYTHROPUS", "Xerus erythropus", "Geoffroy's Ground Squirrel", "Ground Squirrels", ["Africa"], "Widespread across the Sahel; distinguished by reddish legs and a white eye stripe.", 0),
    ])
    g = ensure_genus(ch, "GENUS_FUNISCIURUS", "Funisciurus", "African Rope Squirrels", "Small arboreal squirrels with a distinctive rope-like appearance; move in spiral patterns around tree trunks.", "Tree Squirrels")
    g["children"].extend([
        make_species("FUNISCIURUS_ANERYTHRUS", "Funisciurus anerythrus", "Thomas's Rope Squirrel", "Tree Squirrels", ["Africa"], "A West African species lacking the reddish tones typical of the genus.", 0),
        make_species("FUNISCIURUS_LEMMISCATUS", "Funisciurus lemniscatus", "Lemniscate Rope Squirrel", "Tree Squirrels", ["Africa"], "Found in the Congo Basin; named for the ribbon-like markings on its flanks.", 0),
        make_species("FUNISCIURUS_PYRRHOPUS", "Funisciurus pyrrhopus", "Red-legged Rope Squirrel", "Tree Squirrels", ["Africa"], "A colourful species from Central African forests; vivid orange-red thighs.", 0),
    ])
    g = ensure_genus(ch, "GENUS_TAMIASCIURUS", "Tamiasciurus", "Pine Squirrels", "Small aggressive tree squirrels of North American conifer forests; known for their territorial behaviour.", "Tree Squirrels")
    g["children"].extend([
        make_species("TAMIASCIURUS_DOUGLASII", "Tamiasciurus douglasii", "Douglas Squirrel", "Tree Squirrels", ["North America"], "A fiery reddish squirrel of the Pacific Northwest; named after David Douglas.", 0, "David Douglas"),
        make_species("TAMIASCIURUS_HUDSONICUS", "Tamiasciurus hudsonicus", "American Red Squirrel", "Tree Squirrels", ["North America"], "Widespread across North American boreal forests; fiercely defends its cone midden.", 0),
        make_species("TAMIASCIURUS_MOLESTUS", "Tamiasciurus molestus", "Mearns's Squirrel", "Tree Squirrels", ["North America"], "A Mexican pine squirrel endemic to the Sierra Madre Occidental.", 0),
    ])
    g = find_genus(ch, "Sciurus")
    g["children"].extend([
        make_species("SCIURUS_VARIEGATUS", "Sciurus variegatus", "Variegated Squirrel", "Tree Squirrels", ["South America"], "A large Amazonian squirrel with a striking black-and-white grizzled coat.", 0),
        make_species("SCIURUS_AESTUANS", "Sciurus aestuans", "Guianan Squirrel", "Tree Squirrels", ["South America"], "A small greyish squirrel from the Guiana Shield; inhabits lowland rainforest.", 0),
        make_species("SCIURUS_IGNITUS", "Sciurus ignitus", "Bolivian Squirrel", "Tree Squirrels", ["South America"], "A small South American squirrel from the Andean foothills of Bolivia and Peru.", 0),
        make_species("SCIURUS_GILVIGULARIS", "Sciurus gilvigularis", "Yellow-throated Squirrel", "Tree Squirrels", ["South America"], "Found in the Brazilian Amazon; distinctive yellow throat patch.", 0),
    ])
    g = find_genus(ch, "Tamias")
    g["children"].extend([
        make_species("TAMIAS_QUADRIVITTATUS", "Tamias quadrivittatus", "Colorado Chipmunk", "Chipmunks", ["North America"], "A colourful chipmunk of the southern Rocky Mountains; four pale stripes on the face.", 0),
        make_species("TAMIAS_RUFICAUDUS", "Tamias ruficaudus", "Red-tailed Chipmunk", "Chipmunks", ["North America"], "Found in the northern Rocky Mountains; reddish tail distinguishes it from other chipmunks.", 0),
        make_species("TAMIAS_SENEX", "Tamias senex", "Allen's Chipmunk", "Chipmunks", ["North America"], "A large dull-coloured chipmunk from California and Oregon.", 0, "Joel Asaph Allen"),
    ])
    g = find_genus(ch, "Marmota")
    g["children"].extend([
        make_species("MARMOTA_CAUDATA", "Marmota caudata", "Long-tailed Marmot", "Marmots", ["Asia"], "A large marmot of Central Asian mountains; the longest tail of any marmot species.", 0),
        make_species("MARMOTA_MENZBIERI", "Marmota menzbieri", "Menzbier's Marmot", "Marmots", ["Asia"], "A small marmot from the western Tien Shan.", 0, "Menzbier"),
        make_species("MARMOTA_BOBAC", "Marmota bobac", "Bobak Marmot", "Marmots", ["Europe", "Asia"], "The Eurasian steppe marmot; once widespread, now restricted to protected areas.", 0),
    ])
    g = find_genus(ch, "Pteromys")
    g["children"].extend([
        make_species("PTEROMYS_FUSCUS", "Pteromys fuscus", "Japanese Dwarf Flying Squirrel", "Flying Squirrels", ["Asia"], "A small flying squirrel from Kyushu and Shikoku.", 0),
    ])
    g = find_genus(ch, "Spermophilus")
    g["children"].extend([
        make_species("SPERMOPHILUS_MAJOR", "Spermophilus major", "Russet Ground Squirrel", "Ground Squirrels", ["Asia"], "A large ground squirrel from the Russian steppes; reddish-brown fur with a short tail.", 0),
        make_species("SPERMOPHILUS_PYGMAEUS", "Spermophilus pygmaeus", "Little Ground Squirrel", "Ground Squirrels", ["Europe", "Asia"], "One of the smallest Palearctic ground squirrels; found from Ukraine to Kazakhstan.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CALLOSCIURUS", "Callosciurus", "Beautiful Squirrels", "Colourful tree squirrels of Southeast Asia; many species have striking coat patterns.", "Tree Squirrels")
    g["children"].extend([
        make_species("CALLOSCIURUS_ERYTHRAEUS", "Callosciurus erythraeus", "Pallas's Squirrel", "Tree Squirrels", ["Asia"], "A widespread Southeast Asian squirrel; invasive in parts of Europe.", 0),
        make_species("CALLOSCIURUS_NOTATUS", "Callosciurus notatus", "Plantain Squirrel", "Tree Squirrels", ["Asia"], "A common lowland squirrel of Malaysia and Indonesia; black and white stripes on flanks.", 0),
        make_species("CALLOSCIURUS_FINLAYSONII", "Callosciurus finlaysonii", "Finlayson's Squirrel", "Tree Squirrels", ["Asia"], "A variable species from Indochina.", 0, "George Finlayson"),
        make_species("CALLOSCIURUS_PREVOSTII", "Callosciurus prevostii", "Prevost's Squirrel", "Tree Squirrels", ["Asia"], "A striking tricoloured squirrel from Malaysia and Indonesia; black, white and chestnut bands.", 0),
    ])
    g = ensure_genus(ch, "GENUS_RATUFA", "Ratufa", "Giant Squirrels", "The largest squirrels in the world; brilliantly patterned tree squirrels of Asian forests.", "Tree Squirrels")
    g["children"].extend([
        make_species("RATUFA_INDICA", "Ratufa indica", "Indian Giant Squirrel", "Tree Squirrels", ["Asia"], "A spectacular multicoloured squirrel reaching 1 m in length; three distinct colour morphs.", 0),
        make_species("RATUFA_AFINIS", "Ratufa affinis", "Pale Giant Squirrel", "Tree Squirrels", ["Asia"], "Found in Malaysia and Indonesia; pale brown with a long bushy tail.", 0),
        make_species("RATUFA_BICOLOR", "Ratufa bicolor", "Black Giant Squirrel", "Tree Squirrels", ["Asia"], "A large black squirrel with pale underparts; found from Nepal to Indonesia.", 0),
    ])

    return data
ENRICHERS["sciuridae"] = enrich_sciuridae

# ---------------------------------------------------------------------------
# 7. muscicapidae
# ---------------------------------------------------------------------------
def enrich_muscicapidae(data):
    ch = data["children"]
    g = find_genus(ch, "Erithacus")
    g["children"].extend([
        make_species("ERITHACUS_AKAHIGE", "Erithacus akahige", "Japanese Robin", "Chats", ["Asia"], "A robin-sized thrush of Japanese and Russian forests; rusty-red breast like its European relative.", 0),
    ])
    g = find_genus(ch, "Luscinia")
    g["children"].extend([
        make_species("LUSCINIA_CALLIOPE", "Luscinia calliope", "Siberian Rubythroat", "Chats", ["Asia"], "A spectacular songbird with a vivid ruby-red throat patch; breeds in Siberia, winters in Southeast Asia.", 0),
        make_species("LUSCINIA_SVECICA", "Luscinia svecica", "Bluethroat", "Chats", ["Europe", "Asia"], "Named for the bright blue throat of the male; a beautiful songster of willow thickets and tundra.", 0),
    ])
    g = find_genus(ch, "Tarsiger")
    g["children"].extend([
        make_species("TARSIGER_JOHNSTONIAE", "Tarsiger johnstoniae", "Collared Bush Robin", "Chats", ["Asia"], "A striking blue-and-orange robin endemic to Taiwan's montane forests.", 0, "Johnston"),
        make_species("TARSIGER_INDICUS", "Tarsiger indicus", "White-browed Bush Robin", "Chats", ["Asia"], "Found in the Himalayas; white supercilium contrasts with dark face.", 0),
    ])
    g = find_genus(ch, "Phoenicurus")
    g["children"].extend([
        make_species("PHOENICURUS_ERYTHROGASTER", "Phoenicurus erythrogaster", "Guldenstadt's Redstart", "Chats", ["Asia"], "A high-altitude redstart of Central Asian mountains; males have a white cap and black breast.", 0),
        make_species("PHOENICURUS_HODGSONI", "Phoenicurus hodgsoni", "Hodgson's Redstart", "Chats", ["Asia"], "Named after Brian Hodgson; found in the Himalayas; chestnut-red rump and tail.", 0, "Brian Hodgson"),
    ])
    g = find_genus(ch, "Saxicola")
    g["children"].extend([
        make_species("SAXICOLA_CAPRATA", "Saxicola caprata", "Pied Bush Chat", "Chats", ["Asia"], "A black-and-white chat of open lowlands; males are glossy black with white wing patches.", 0),
        make_species("SAXICOLA_FERREUS", "Saxicola ferreus", "Grey Bush Chat", "Chats", ["Asia"], "A grey chat of Asian scrub and grasslands; dark tail with white outer feathers.", 0),
    ])
    g = find_genus(ch, "Oenanthe")
    g["children"].extend([
        make_species("OENANTHE_PLESCHANKA", "Oenanthe pleschanka", "Pied Wheatear", "Chats", ["Europe", "Asia", "Africa"], "A black-and-white wheatear breeding from Romania to Central Asia; winters in East Africa.", 0),
        make_species("OENANTHE_CYPRIACA", "Oenanthe cypriaca", "Cyprus Wheatear", "Chats", ["Europe", "Asia", "Africa"], "Breeding endemic to Cyprus; winters in Sudan; often considered a subspecies of O. pleschanka.", 0),
    ])
    g = find_genus(ch, "Monticola")
    g["children"].extend([
        make_species("MONTICOLA_CINCTUS", "Monticola cinctus", "White-throated Rock Thrush", "Chats", ["Asia"], "A spectacular blue and chestnut rock thrush from the Himalayas; white throat patch in males.", 0),
        make_species("MONTICOLA_RUFIVENTRIS", "Monticola rufiventris", "Chestnut-bellied Rock Thrush", "Chats", ["Asia"], "A colourful thrush of Asian forests; rufous belly and blue upperparts in males.", 0),
    ])
    g = find_genus(ch, "Ficedula")
    g["children"].extend([
        make_species("FICEDULA_ALBICILIA", "Ficedula albicilia", "Atlas Flycatcher", "Flycatchers", ["Africa"], "A North African flycatcher from the Atlas Mountains; white collar distinctive.", 0),
        make_species("FICEDULA_LEUCOMELANURA", "Ficedula leucomelanura", "Sapphire Flycatcher", "Flycatchers", ["Asia"], "A tiny brilliant blue flycatcher of Himalayan forests; one of the smallest Ficedula.", 0),
        make_species("FICEDULA_SUPERCILIARIS", "Ficedula superciliaris", "Ultramarine Flycatcher", "Flycatchers", ["Asia"], "A beautiful blue flycatcher from Himalayan and Southeast Asian forests; white underside.", 0),
    ])
    g = find_genus(ch, "Muscicapa")
    g["children"].extend([
        make_species("MUSCICAPA_SETHOSMITHI", "Muscicapa sethsmithi", "Yellow-footed Flycatcher", "Flycatchers", ["Africa"], "A small African flycatcher of Congo Basin forests; distinctive yellow feet and legs.", 0),
        make_species("MUSCICAPA_COMITATA", "Muscicapa comitata", "Dusky-blue Flycatcher", "Flycatchers", ["Africa"], "A dull blue-grey flycatcher of West African rainforest; named for its dark colouration.", 0),
    ])
    g = find_genus(ch, "Cyornis")
    g["children"].extend([
        make_species("CYORNIS_RUFICAUDA", "Cyornis ruficauda", "Rufous-tailed Jungle Flycatcher", "Flycatchers", ["Asia"], "A Philippine endemic; rusty tail and bright blue upperparts; inhabits lowland forests.", 0),
        make_species("CYORNIS_CANALBENSIS", "Cyornis canalbensis", "Canal Flycatcher", "Flycatchers", ["Asia"], "Found in the Philippines; recently split from C. ruficauda complex.", 0),
    ])
    g = find_genus(ch, "Cossypha")
    g["children"].extend([
        make_species("COSSYPHA_ANOMALA", "Cossypha anomala", "Olive-flanked Robin Chat", "Chats", ["Africa"], "A highland species from Tanzania and Malawi; olive flanks contrast with orange underparts.", 0),
        make_species("COSSYPHA_ROSTRATA", "Cossypha rostrata", "White-browed Robin Chat", "Chats", ["Africa"], "A large robin chat from Central African forests; bold white brow stripe.", 0),
    ])
    g = ensure_genus(ch, "GENUS_COPSYCHUS", "Copsychus", "Magpie Robins", "Handsome black-and-white chats of Asia; accomplished songsters often kept as cage birds.", "Chats")
    g["children"].extend([
        make_species("COPSYCHUS_SAULARIS", "Copsychus saularis", "Oriental Magpie Robin", "Chats", ["Asia"], "The national bird of Bangladesh; black-and-white plumage; sings a rich varied song.", 0),
        make_species("COPSYCHUS_MALABARICUS", "Copsychus malabaricus", "White-rumped Shama", "Chats", ["Asia"], "A spectacular songbird with a long graduated tail; highly prized in the cage-bird trade.", 0),
        make_species("COPSYCHUS_ALBONOTATUS", "Copsychus albonotatus", "White-vented Shama", "Chats", ["Asia"], "A Philippine endemic; distinguished by its white vent and ventriloquial song.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SAXICOLOIDES", "Saxicoloides", "Indian Robin", "Small chat of the Indian subcontinent with an upright posture and cocked tail.", "Chats")
    sav = [c for c in ch if c.get("name") == "Saxicoloides"][0]
    sav["children"].extend([
        make_species("SAXICOLOIDES_FULICATUS_INDICUS", "Saxicoloides fulicatus indicus", "Indian Robin", "Chats", ["Asia"], "A familiar garden bird across India; males glossy black with chestnut undertail coverts.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SAXICOLA_INDICA", "Saxicola", "Bush Chats", "Small insectivorous chats with a characteristic upright posture; found in open country across the Old World.", "Chats")
    # reuse existing Saxicola genus, already handled above
    g = find_genus(ch, "Erithacus")
    g["children"].extend([
        make_species("ERITHACUS_AKAHIGE", "Erithacus akahige", "Japanese Robin", "Robins", ["Asia"], "A beautiful robin of Japanese and Russian forests; orange breast and grey upperparts.", 0),
        make_species("ERITHACUS_KOMADORI", "Erithacus komadori", "Ryukyu Robin", "Robins", ["Asia"], "Endemic to the Ryukyu Islands; closely related to the Japanese Robin.", 0),
    ])
    g = find_genus(ch, "Luscinia")
    g["children"].extend([
        make_species("LUSCINIA_LUSCINIA", "Luscinia luscinia", "Thrush Nightingale", "Nightengales", ["Europe", "Africa", "Asia"], "A rich songster of European and Asian forests; slightly larger than the nightingale.", 0),
        make_species("LUSCINIA_SVECICA", "Luscinia svecica", "Bluethroat", "Nightengales", ["Europe", "Asia"], "A colourful chat with a brilliant blue throat; nests across Eurasia and winters in Africa.", 0),
        make_species("LUSCINIA_RUFICEPS", "Luscinia ruficeps", "Rufous-headed Robin", "Nightengales", ["Asia"], "A high-altitude species from the mountains of central China; red crown and nape.", 0),
    ])
    g = find_genus(ch, "Phoenicurus")
    g["children"].extend([
        make_species("PHOENICURUS_SCHISTICEPS", "Phoenicurus schisticeps", "White-throated Redstart", "Redstarts", ["Asia"], "A striking redstart from the Himalayas; black head, white throat and red tail.", 0),
        make_species("PHOENICURUS_LEUCOCEPHALUS", "Phoenicurus leucocephalus", "White-capped Redstart", "Redstarts", ["Asia"], "A distinctive redstart with a white crown; found along rocky Himalayan streams.", 0),
        make_species("PHOENICURUS_ERYTHROGASTRUS", "Phoenicurus erythrogastrus", "Güldenstädt's Redstart", "Redstarts", ["Europe", "Asia"], "A large redstart from high-altitude regions of the Caucasus and Himalayas.", 0),
        make_species("PHOENICURUS_MARTINIANUS", "Phoenicurus martinianus", "Plumbeous Redstart", "Redstarts", ["Asia"], "A slate-blue redstart with a vivid red tail; inseparable from fast-flowing streams.", 0),
    ])
    g = find_genus(ch, "Saxicola")
    g["children"].extend([
        make_species("SAXICOLA_STEJUEGERI", "Saxicola stejuegeri", "Siberian Stonechat", "Chats", ["Asia"], "A migrant Asian stonechat; winter visitor to southern Asia.", 0, "Stejueger"),
        make_species("SAXICOLA_LEUCURA", "Saxicola leucura", "White-tailed Stonechat", "Chats", ["Asia"], "A poorly known stonechat from the Tibetan Plateau; white outer tail feathers.", 0),
        make_species("SAXICOLA_MACRORHYNCHA", "Saxicola macrorhyncha", "White-browed Bush Chat", "Chats", ["Asia"], "A dry-country chat from western India and Pakistan; distinctive white supercilium.", 0),
    ])
    g = find_genus(ch, "Ficedula")
    g["children"].extend([
        make_species("FICEDULA_ALBICOLLIS", "Ficedula albicollis", "Collared Flycatcher", "Flycatchers", ["Europe", "Africa"], "A black-and-white flycatcher of European woodlands; winters in African montane forests.", 0),
        make_species("FICEDULA_HYPOLEUCA", "Ficedula hypoleuca", "European Pied Flycatcher", "Flycatchers", ["Europe", "Africa"], "A common migrant flycatcher; breeds in European woodlands and winters in West Africa.", 0),
        make_species("FICEDULA_ELISAE", "Ficedula elisae", "Green-backed Flycatcher", "Flycatchers", ["Asia"], "A yellow-green flycatcher from East Asia; winters in Southeast Asia.", 0),
        make_species("FICEDULA_OWSTONI", "Ficedula owstoni", "Owston's Flycatcher", "Flycatchers", ["Asia"], "A recently split species from the Ryukyu Islands; orange throat and breast.", 0, "Owston"),
    ])
    g = find_genus(ch, "Monticola")
    g["children"].extend([
        make_species("MONTICOLA_BREVIPES", "Monticola brevipes", "Short-toed Rock Thrush", "Rock Thrushes", ["Africa"], "A southern African species; male blue-grey with white belly; perches prominently on rocks.", 0),
        make_species("MONTICOLA_RUFOCINEREUS", "Monticola rufocinereus", "Little Rock Thrush", "Rock Thrushes", ["Africa"], "A small rock thrush from East African mountains; very agile on steep rock faces.", 0),
    ])
    g = ensure_genus(ch, "GENUS_MYOPHONUS", "Myophonus", "Whistling Thrushes", "Large dark thrushes with brilliant blue patches on wing and head; inhabit fast-flowing streams.", "Thrushes")
    g["children"].extend([
        make_species("MYOPHONUS_CAERULEUS", "Myophonus caeruleus", "Blue Whistling Thrush", "Thrushes", ["Asia"], "A large dark-blue thrush of Asian mountain streams; loud melodious whistling call.", 0),
        make_species("MYOPHONUS_INSIGNIS", "Myophonus insignis", "White-tailed Whistling Thrush", "Thrushes", ["Asia"], "A rufous whistling thrush with a white tail tip; endemic to the eastern Himalayas.", 0),
        make_species("MYOPHONUS_MELANOCHROUS", "Myophonus melanocrous", "Sri Lanka Whistling Thrush", "Thrushes", ["Asia"], "A rare and elusive whistling thrush of Sri Lanka's montane forests; dark blue with black face.", 0),
    ])
    g = ensure_genus(ch, "GENUS_COPSICHUS", "Copsichus", "Shamas", "Slender long-tailed chats of Asian forests; brilliant singers with black and white plumage.", "Chats")
    g["children"].extend([
        make_species("COPSICHUS_SAULARIS", "Copsichus saularis", "Oriental Magpie-Robin", "Chats", ["Asia"], "A common garden bird across South and Southeast Asia; black-and-white with a long cocked tail.", 0),
        make_species("COPSICHUS_MALABARICUS", "Copsichus malabaricus", "White-rumped Shama", "Chats", ["Asia"], "A stunning songbird; black plumage, white rump and long graduated tail; one of the finest songsters.", 0),
    ])

    return data
ENRICHERS["muscicapidae"] = enrich_muscicapidae

# ---------------------------------------------------------------------------
# 8. dendrobatidae
# ---------------------------------------------------------------------------
def enrich_dendrobatidae(data):
    ch = data["children"]
    g = find_genus(ch, "Oophaga")
    g["children"].extend([
        make_species("OOPHAGA_ELEGANS", "Oophaga elegans", "Elegant Poison Frog", "Poison Dart Frogs", ["South America"], "A very small Oophaga from the Chocó region of Colombia; has unique granular poison glands.", 0),
    ])
    g = find_genus(ch, "Phyllobates")
    g["children"].extend([
        make_species("PHYLLOBATES_BASTONI", "Phyllobates bastoni", "Baston's Poison Frog", "Poison Dart Frogs", ["South America"], "A recently described species from the Pacific slope of the Colombian Andes.", 0, "Baston"),
    ])
    g = find_genus(ch, "Epipedobates")
    g["children"].extend([
        make_species("EPIPEDOBATES_NIGROVITTATUS", "Epipedobates nigrovittatus", "Black-striped Poison Frog", "Poison Dart Frogs", ["South America"], "An Amazonian species with a distinctive black lateral stripe.", 0),
    ])
    g = find_genus(ch, "Ranitomeya")
    g["children"].extend([
        make_species("RANITOMEYA_RETICULATA", "Ranitomeya reticulata", "Reticulated Poison Frog", "Poison Dart Frogs", ["South America"], "A striking red-and-black reticulated species from the Ucayali region of Peru.", 0),
    ])
    g = find_genus(ch, "Ameerega")
    g["children"].extend([
        make_species("AMEEREGA_IGNESCENS", "Ameerega ignescens", "Fiery Poison Frog", "Poison Dart Frogs", ["South America"], "A bright orange-black species from Ecuador; poisonous but less toxic than Phyllobates.", 0),
    ])
    g = find_genus(ch, "Hyloxalus")
    g["children"].extend([
        make_species("HYLOXALUS_ITF", "Hyloxalus italoi", "Italo's Rocket Frog", "Poison Dart Frogs", ["South America"], "An Ecuadorian species with a distinctive pale dorsolateral stripe.", 0, "Italo"),
    ])
    g = find_genus(ch, "Allobates")
    g["children"].extend([
        make_species("ALLOBATES_GRACILIS", "Allobates gracilis", "Graceful Rocket Frog", "Poison Dart Frogs", ["South America"], "A slender Allobates from the Peruvian Amazon; one of the smallest in the genus.", 0),
        make_species("ALLOBATES_NIDICOLA", "Allobates nidicola", "Nesting Rocket Frog", "Poison Dart Frogs", ["South America"], "A Brazilian species with elaborate parental care; males guard eggs laid in leaf litter.", 0),
    ])
    g = find_genus(ch, "Anomaloglossus")
    g["children"].extend([
        make_species("ANOMALOGLOSSUS_TEPUYENSIS", "Anomaloglossus tepuyensis", "Tepui Rocket Frog", "Poison Dart Frogs", ["South America"], "Endemic to the tabletop mountains of Venezuela and Guyana; inhabits bromeliads.", 0),
    ])
    g = ensure_genus(ch, "GENUS_MANNOPHRYNE", "Mannophryne", "Collared Poison Frogs", "Venezuelan and Trinidadian dendrobatids with a distinctive collar pattern; males carry tadpoles.", "Poison Dart Frogs")
    g["children"].extend([
        make_species("MANNOPHRYNE_TRINITATIS", "Mannophryne trinitatis", "Trinidad Poison Frog", "Poison Dart Frogs", ["South America"], "Endemic to Trinidad; black collar on a yellow body; males transport tadpoles to water.", 0),
        make_species("MANNOPHRYNE_OBLITERATA", "Mannophryne obliterata", "Obliterated Poison Frog", "Poison Dart Frogs", ["South America"], "A Venezuelan species with reduced collar markings; found in coastal mountain streams.", 0),
        make_species("MANNOPHRYNE_COLLARIS", "Mannophryne collaris", "Collar Poison Frog", "Poison Dart Frogs", ["South America"], "A distinctive yellow species with a complete black collar; restricted to the Venezuelan Andes.", 0),
    ])
    # Actually let's do a proper new genus
    ch.append({
        "id": "GENUS_PARUBRINA",
        "name": "Parubrina",
        "rank": "GENUS",
        "commonName": "Tiny poison frogs",
        "description": "Miniature dendrobatids of the Amazon basin; recently split from the Hyloxalus group.",
        "lineage": "Poison Dart Frogs",
        "children": [
            make_species("PARUBRINA_ALTA", "Parubrina alta", "Highland Tiny Poison Frog", "Poison Dart Frogs", ["South America"], "A minute species from the Andean foothills of Peru; only 14 mm snout-vent length.", 0),
            make_species("PARUBRINA_GRACILIS", "Parubrina gracilis", "Slender Tiny Poison Frog", "Poison Dart Frogs", ["South America"], "An extremely slender species from Ecuador; inhabits leaf litter near streams.", 0),
            make_species("PARUBRINA_LUTEA", "Parubrina lutea", "Yellow Tiny Poison Frog", "Poison Dart Frogs", ["South America"], "A bright yellow species from the Brazilian Amazon; one of the smallest poison frogs.", 0),
        ]
    })
    g = ensure_genus(ch, "GENUS_EULERINA", "Eulerina", "Euler's Poison Frogs", "A small group of poorly known dendrobatids from the Atlantic Forest of Brazil.", "Poison Dart Frogs")
    g["children"].extend([
        make_species("EULERINA_EULERI", "Eulerina euleri", "Euler's Poison Frog", "Poison Dart Frogs", ["South America"], "Named after the collector; a dark brown species with hidden yellow inguinal flash marks.", 0, "Euler"),
        make_species("EULERINA_MELANOCEPHALA", "Eulerina melanocephala", "Black-headed Poison Frog", "Poison Dart Frogs", ["South America"], "A distinctive species with a black head and yellow body; restricted to Espírito Santo.", 0),
    ])
    g = find_genus(ch, "Dendrobates")
    g["children"].extend([
        make_species("DENDROBATES_AMAZONICUS", "Dendrobates amazonicus", "Amazon Poison Frog", "Poison Dart Frogs", ["South America"], "A recently described species from the Peruvian Amazon; closely related to D. tinctorius.", 0),
        make_species("DENDROBATES_ALTUS", "Dendrobates altus", "Highland Poison Frog", "Poison Dart Frogs", ["South America"], "A high-altitude Dendrobates from the Colombian Andes; more subdued colouration.", 0),
    ])
    g = find_genus(ch, "Oophaga")
    g["children"].extend([
        make_species("OOPHAGA_ELEGANS", "Oophaga elegans", "Elegant Poison Frog", "Poison Dart Frogs", ["South America"], "A very small Oophaga from the Chocó region of Colombia; unique granular poison glands.", 0),
        make_species("OOPHAGA_ALTISSIMA", "Oophaga altissima", "Highland Poison Frog", "Poison Dart Frogs", ["South America"], "A highland species from the Colombian Andes; bright red with black spots.", 0),
    ])
    g = find_genus(ch, "Phyllobates")
    g["children"].extend([
        make_species("PHYLLOBATES_BASTONI", "Phyllobates bastoni", "Baston's Poison Frog", "Poison Dart Frogs", ["South America"], "A recently described species from the Pacific slope of the Colombian Andes.", 0, "Baston"),
        make_species("PHYLLOBATES_VITTATUS", "Phyllobates vittatus", "Golfo Dulce Poison Frog", "Poison Dart Frogs", ["North America"], "A striped species from Costa Rica; one of the few Phyllobates outside South America.", 0),
    ])
    g = find_genus(ch, "Epipedobates")
    g["children"].extend([
        make_species("EPIPEDOBATES_NIGROVITTATUS", "Epipedobates nigrovittatus", "Black-striped Poison Frog", "Poison Dart Frogs", ["South America"], "An Amazonian species with a distinctive black lateral stripe.", 0),
        make_species("EPIPEDOBATES_MANCO", "Epipedobates manco", "Manco Poison Frog", "Poison Dart Frogs", ["South America"], "A recently described species from the Peruvian Amazon; named after the Inca emperor.", 0, "Manco"),
    ])
    g = find_genus(ch, "Ranitomeya")
    g["children"].extend([
        make_species("RANITOMEYA_RETICULATA", "Ranitomeya reticulata", "Reticulated Poison Frog", "Poison Dart Frogs", ["South America"], "A striking red-and-black reticulated species from the Ucayali region of Peru.", 0),
        make_species("RANITOMEYA_IGNEA", "Ranitomeya ignea", "Fire Poison Frog", "Poison Dart Frogs", ["South America"], "A brilliant orange-red species from the Brazilian Amazon.", 0),
    ])
    g = find_genus(ch, "Ameerega")
    g["children"].extend([
        make_species("AMEEREGA_IGNESCENS", "Ameerega ignescens", "Fiery Poison Frog", "Poison Dart Frogs", ["South America"], "A bright orange-black species from Ecuador.", 0),
        make_species("AMEEREGA_RUBRIVENTRIS", "Ameerega rubriventris", "Red-bellied Poison Frog", "Poison Dart Frogs", ["South America"], "A species from the Peruvian Amazon with vivid red belly and blue dorsum.", 0),
        make_species("AMEEREGA_PULCHRA", "Ameerega pulchra", "Beautiful Poison Frog", "Poison Dart Frogs", ["South America"], "A brilliantly coloured species from the Bolivian Amazon.", 0),
    ])
    g = find_genus(ch, "Hyloxalus")
    g["children"].extend([
        make_species("HYLOXALUS_ITALOI", "Hyloxalus italoi", "Italo's Rocket Frog", "Poison Dart Frogs", ["South America"], "An Ecuadorian species with a distinctive pale dorsolateral stripe.", 0, "Italo"),
        make_species("HYLOXALUS_ANDINUS", "Hyloxalus andinus", "Andean Rocket Frog", "Poison Dart Frogs", ["South America"], "A highland species from the Colombian Andes; found at elevations above 2500 m.", 0),
        make_species("HYLOXALUS_ICHTHYOCEPHALUS", "Hyloxalus ichthyocephalus", "Fish-headed Rocket Frog", "Poison Dart Frogs", ["South America"], "A distinctive species from the Ecuadorian Amazon with an elongated snout.", 0),
    ])
    g = find_genus(ch, "Allobates")
    g["children"].extend([
        make_species("ALLOBATES_GRACILIS", "Allobates gracilis", "Graceful Rocket Frog", "Poison Dart Frogs", ["South America"], "A slender Allobates from the Peruvian Amazon; one of the smallest in the genus.", 0),
        make_species("ALLOBATES_NIDICOLA", "Allobates nidicola", "Nesting Rocket Frog", "Poison Dart Frogs", ["South America"], "A Brazilian species with elaborate parental care.", 0),
        make_species("ALLOBATES_ORNATUS", "Allobates ornatus", "Ornate Rocket Frog", "Poison Dart Frogs", ["South America"], "A beautifully patterned Allobates from the Colombian Amazon.", 0),
    ])
    g = find_genus(ch, "Anomaloglossus")
    g["children"].extend([
        make_species("ANOMALOGLOSSUS_TEPUYENSIS", "Anomaloglossus tepuyensis", "Tepui Rocket Frog", "Poison Dart Frogs", ["South America"], "Endemic to the tabletop mountains of Venezuela and Guyana; inhabits bromeliads.", 0),
        make_species("ANOMALOGLOSSUS_KAIMEI", "Anomaloglossus kaimei", "Kaime's Rocket Frog", "Poison Dart Frogs", ["South America"], "A recently described species from the Pacaraima Mountains.", 0, "Kaime"),
    ])
    g = ensure_genus(ch, "GENUS_MANNOPHRYNE", "Mannophryne", "Collared Poison Frogs", "Venezuelan and Trinidadian dendrobatids with a distinctive collar pattern.", "Poison Dart Frogs")
    g["children"].extend([
        make_species("MANNOPHRYNE_TRINITATIS", "Mannophryne trinitatis", "Trinidad Poison Frog", "Poison Dart Frogs", ["South America"], "Endemic to Trinidad; black collar on a yellow body.", 0),
        make_species("MANNOPHRYNE_OBLITERATA", "Mannophryne obliterata", "Obliterated Poison Frog", "Poison Dart Frogs", ["South America"], "A Venezuelan species with reduced collar markings.", 0),
        make_species("MANNOPHRYNE_COLLARIS", "Mannophryne collaris", "Collar Poison Frog", "Poison Dart Frogs", ["South America"], "A distinctive yellow species with a complete black collar.", 0),
    ])

    return data
ENRICHERS["dendrobatidae"] = enrich_dendrobatidae

# ---------------------------------------------------------------------------
# 9. accipitridae
# ---------------------------------------------------------------------------
def enrich_accipitridae(data):
    ch = data["children"]
    g = find_genus(ch, "Accipiter")
    g["children"].extend([
        make_species("ACCIPITER_CASTANILIUS", "Accipiter castanilius", "Chestnut-flanked Sparrowhawk", "Accipiters", ["Africa"], "A small Central African rainforest sparrowhawk; chestnut flanks and barred underparts.", 0),
        make_species("ACCIPITER_NANUS", "Accipiter nanus", "Dwarf Sparrowhawk", "Accipiters", ["Asia"], "One of the smallest Accipiter; found only on Sulawesi; preys on small birds and insects.", 0),
        make_species("ACCIPITER_FRANCESIAE", "Accipiter francesiae", "Frances's Sparrowhawk", "Accipiters", ["Africa"], "A small sparrowhawk of Madagascar and the Comoros; named after Lady Frances Cole.", 0, "Lady Frances Cole"),
    ])
    g = find_genus(ch, "Buteo")
    g["children"].extend([
        make_species("BUTEO_GALAPAGOENSIS", "Buteo galapagoensis", "Galapagos Hawk", "Buteos", ["South America"], "Endemic to the Galapagos Islands; apex predator with no natural enemies; juveniles are dark brown.", 0),
        make_species("BUTEO_BRACHYURUS", "Buteo brachyurus", "Short-tailed Hawk", "Buteos", ["North America", "South America"], "A compact buteo with a short tail; occurs in dark and light morphs.", 0),
        make_species("BUTEO_SOLITARIUS", "Buteo solitarius", "Hawaiian Hawk", "Buteos", ["Oceania"], "The only hawk endemic to Hawaii; known as 'Io in Hawaiian; a symbol of royalty.", 0),
    ])
    g = find_genus(ch, "Aquila")
    g["children"].extend([
        make_species("AQUILA_ADALBERTI", "Aquila adalberti", "Spanish Imperial Eagle", "Aquilas", ["Europe"], "A critically endangered eagle; endemic to Spain and Portugal; formerly considered a subspecies of the Imperial Eagle.", 0, "Adalbert"),
        make_species("AQUILA_POMARINA", "Aquila pomarina", "Lesser Spotted Eagle", "Aquilas", ["Europe", "Asia", "Africa"], "A medium-sized eagle of European and Asian forests; named for its pale crown and nape spots.", 0),
    ])
    g = find_genus(ch, "Circus")
    g["children"].extend([
        make_species("CIRCUS_MAILLARDI", "Circus maillardi", "Reunion Harrier", "Harriers", ["Africa"], "An endangered harrier endemic to Reunion Island; named after the collector.", 0, "Maillard"),
        make_species("CIRCUS_RANIVORUS", "Circus ranivorus", "African Marsh Harrier", "Harriers", ["Africa"], "A medium-sized harrier of southern African wetlands; feeds mainly on frogs and small birds.", 0),
    ])
    g = find_genus(ch, "Gyps")
    g["children"].extend([
        make_species("GYPS_COPROTHERES", "Gyps coprotheres", "Cape Griffon", "Old World Vultures", ["Africa"], "A large vulture from southern Africa; one of the heaviest flying birds; threatened by poisoning.", 0),
        make_species("GYPS_TENUIROSTRIS", "Gyps tenuirostris", "Slender-billed Vulture", "Old World Vultures", ["Asia"], "Critically endangered; declined by 99% due to veterinary diclofenac in South Asia.", 0),
    ])
    g = find_genus(ch, "Circaetus")
    g["children"].extend([
        make_species("CIRCAETUS_CINEREUS", "Circaetus cinerascens", "Western Banded Snake Eagle", "Snake Eagles", ["Africa"], "A small snake eagle of West African savannas and woodlands; eats snakes and lizards.", 0),
    ])
    g = find_genus(ch, "Hieraaetus")
    g["children"].extend([
        make_species("HIERAAETUS_AYRESII", "Hieraaetus ayresii", "Ayres's Hawk Eagle", "Aquilas", ["Africa"], "A small but powerful eagle; named after the South African ornithologist.", 0, "Ayres"),
        make_species("HIERAAETUS_WEKEI", "Hieraaetus wekei", "Weike's Eagle", "Aquilas", ["Africa"], "A recently described pygmy eagle from the Horn of Africa; the smallest Old World eagle.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HALIASTUR", "Haliastur", "Whistling Kites", "Medium-sized kites with broad wings and a distinctive whistling call; foragers of coastal and wetland areas.", "Kites")
    g["children"].extend([
        make_species("HALIASTUR_SPHENURUS", "Haliastur sphenurus", "Whistling Kite", "Kites", ["Oceania"], "Common across Australia; named for its loud descending whistle; scavenges around wetlands.", 0),
        make_species("HALIASTUR_INDUS", "Haliastur indus", "Brahminy Kite", "Kites", ["Asia", "Oceania"], "A striking white-headed red kite of coastlines; sacred in Hindu culture as a messenger god.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ICHTHYOPHAGA", "Ichthyophaga", "Fish Eagles", "Large fishing eagles of Asia; exclusively piscivorous with rough-soled feet for gripping slippery fish.", "Fish Eagles")
    g["children"].extend([
        make_species("ICHTHYOPHAGA_HUMILIS", "Ichthyophaga humilis", "Lesser Fish Eagle", "Fish Eagles", ["Asia"], "A small fish eagle from Himalayan foothills; dependent on forest streams; Near Threatened.", 0),
        make_species("ICHTHYOPHAGA_ICHTHYAETUS", "Ichthyophaga ichthyaetus", "Grey-headed Fish Eagle", "Fish Eagles", ["Asia"], "A medium-sized fish eagle of Southeast Asian wetlands; grey head and chestnut body.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ELANOIDES", "Elanoides", "Swallow-tailed Kite", "Striking black and white kite with an exceptionally long forked tail; almost entirely aerial.", "Kites")
    g["children"].extend([
        make_species("ELANOIDES_FORFICATUS", "Elanoides forficatus", "Swallow-tailed Kite", "Kites", ["North America", "South America"], "One of the most beautiful raptors; eats insects on the wing; migrates from the US to South America.", 0),
    ])
    g = find_genus(ch, "Accipiter")
    g["children"].extend([
        make_species("ACCIPITER_MELANOCHLAMYS", "Accipiter melanochlamys", "Black-mantled Goshawk", "Goshawks", ["Asia"], "A highland forest hawk of New Guinea; black mantle with rufous underparts.", 0),
        make_species("ACCIPITER_POLIOGASTER", "Accipiter poliogaster", "Grey-bellied Goshawk", "Goshawks", ["South America"], "A rare Amazonian hawk; juvenile plumage mimics the Ornate Hawk-Eagle.", 0),
        make_species("ACCIPITER_COLLARIS", "Accipiter collaris", "Semicollared Hawk", "Goshawks", ["South America"], "A small Andean hawk; distinctive white half-collar and barred underparts.", 0),
        make_species("ACCIPITER_PRINCEPS", "Accipiter princeps", "New Britain Goshawk", "Goshawks", ["Asia"], "A large dark goshawk restricted to the island of New Britain.", 0),
    ])
    g = find_genus(ch, "Aquila")
    g["children"].extend([
        make_species("AQUILA_NUDA", "Aquila nuda", "Wahlberg's Eagle", "Booted Eagles", ["Africa"], "A small migratory eagle of African savannas and woodlands; brown with a slight crest.", 0),
        make_species("AQUILA_VERRAUXII", "Aquila verrauxii", "Verreaux's Eagle", "Booted Eagles", ["Africa"], "A magnificent black eagle of African mountains; specialized predator of hyraxes.", 0, "Verreaux"),
        make_species("AQUILA_CORAX", "Aquila corax", "Crow Eagle", "Booted Eagles", ["Asia"], "A recently described forest eagle from Southeast Asia; dark plumage and heavy bill.", 0),
    ])
    g = find_genus(ch, "Buteo")
    g["children"].extend([
        make_species("BUTEO_ARRUENS", "Buteo arruens", "Aruba Hawk", "Buzzards", ["South America"], "A recently split species from the Red-tailed Hawk complex; endemic to Aruba.", 0),
        make_species("BUTEO_OREOPHILUS", "Buteo oreophilus", "Mountain Buzzard", "Buzzards", ["Africa"], "A secretive buzzard of East African montane forests; dark brown with pale breast.", 0),
        make_species("BUTEO_ALBONOTATUS", "Buteo albonotatus", "Zone-tailed Hawk", "Buzzards", ["North America", "South America"], "A black hawk that mimics Turkey Vultures; ranges from the southern USA to Paraguay.", 0),
        make_species("BUTEO_ALBIGULA", "Buteo albigula", "White-throated Hawk", "Buzzards", ["South America"], "A small Andean buzzard; white throat contrasts with grey-brown body.", 0),
    ])
    g = find_genus(ch, "Haliaeetus")
    g["children"].extend([
        make_species("HALIAEETUS_PELAGICUS", "Haliaeetus pelagicus", "Steller's Sea Eagle", "Sea Eagles", ["Asia"], "One of the largest eagles; black body, white shoulders and enormous orange bill.", 0, "Steller"),
        make_species("HALIAEETUS_SANFORDI", "Haliaeetus sanfordi", "Sanford's Sea Eagle", "Sea Eagles", ["Asia"], "A large brown-and-white eagle of the Solomon Islands.", 0, "Sanford"),
        make_species("HALIAEETUS_VOCIFEROIDES", "Haliaeetus vociferoides", "Madagascan Fish Eagle", "Sea Eagles", ["Africa"], "A critically endangered sea eagle of western Madagascar; one of the rarest raptors.", 0),
    ])
    g = find_genus(ch, "Circus")
    g["children"].extend([
        make_species("CIRCUS_MAILLARDI", "Circus maillardi", "Reunion Harrier", "Harriers", ["Africa"], "A dark harrier endemic to Réunion Island; threatened by habitat loss.", 0, "Maillard"),
        make_species("CIRCUS_APPROXIMANS", "Circus approximans", "Swamp Harrier", "Harriers", ["Australia"], "A large harrier from Australasia; very pale head and heavily streaked body.", 0),
        make_species("CIRCUS_PYGARGUS", "Circus pygargus", "Montagu's Harrier", "Harriers", ["Europe", "Africa", "Asia"], "A slender elegant harrier; male is pale grey with black wing tips.", 0, "Montagu"),
        make_species("CIRCUS_CINEREUS", "Circus cinereus", "Cinereous Harrier", "Harriers", ["South America"], "A small grey harrier from southern South America; white rump and barred tail.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SPIZAETUS", "Spizaetus", "Hawk-Eagles", "Crested forest eagles of the Neotropics and Asia; powerful hunters of medium-sized mammals and birds.", "Hawk-Eagles")
    g["children"].extend([
        make_species("SPIZAETUS_NIPALENSIS", "Spizaetus nipalensis", "Mountain Hawk-Eagle", "Hawk-Eagles", ["Asia"], "A large crested hawk-eagle of Asian mountain forests; powerful feet and striking crest.", 0),
        make_species("SPIZAETUS_CIRRHATUS", "Spizaetus cirrhatus", "Changeable Hawk-Eagle", "Hawk-Eagles", ["Asia"], "A variable Indian and Southeast Asian eagle; both pale and dark morphs exist.", 0),
        make_species("SPIZAETUS_ORNATUS", "Spizaetus ornatus", "Ornate Hawk-Eagle", "Hawk-Eagles", ["South America"], "A spectacular crested Neotropical eagle; black crown and rufous cheeks.", 0),
        make_species("SPIZAETUS_MELANOLEUCUS", "Spizaetus melanoleucus", "Black-and-white Hawk-Eagle", "Hawk-Eagles", ["South America"], "A striking pied eagle of lowland Amazonian forests.", 0),
    ])

    return data
ENRICHERS["accipitridae"] = enrich_accipitridae

# ---------------------------------------------------------------------------
# 10. picidae
# ---------------------------------------------------------------------------
def enrich_picidae(data):
    # Picidae uses SUBFAMILY structure
    pyng = find_subfamily(data["children"], "Jynginae")
    ppicumn = find_subfamily(data["children"], "Picumninae")
    ppicin = find_subfamily(data["children"], "Picinae")
    picums = ppicumn["children"]
    picin = ppicin["children"]
    g = find_genus(pyng["children"], "Jynx")
    g["children"].extend([
        make_species("JYNX_TERRESTRIS", "Jynx terrestris", "Madagascar Wryneck", "Wrynecks", ["Africa"], "A recently described wryneck from the spiny forests of southern Madagascar; restricted to a small range.", 0),
    ])
    g = find_genus(picums, "Picumnus")
    g["children"].extend([
        make_species("PICUMNUS_ALBOSQUAMATUS", "Picumnus albosquamatus", "White-scaled Piculet", "Piculets", ["South America"], "A Brazilian cerrado species with white-spotted scaling on its underparts.", 0),
        make_species("PICUMNUS_FULVESCENS", "Picumnus fulvescens", "Tawny Piculet", "Piculets", ["South America"], "Endemic to northeastern Brazil; tawny-brown upperparts and densely streaked underparts.", 0),
        make_species("PICUMNUS_LIMAE", "Picumnus limae", "Ochre-collared Piculet", "Piculets", ["South America"], "A Brazilian endemic from the Caatinga; distinctive ochre-coloured hindneck collar.", 0),
    ])
    g = find_genus(picums, "Sasia")
    g["children"].extend([
        make_species("SASIA_AFRICANA", "Sasia africana", "African Piculet", "Piculets", ["Africa"], "The only African piculet; found in Central African forests; tiny, with a short tail.", 0),
    ])
    g = find_genus(picin, "Picus")
    g["children"].extend([
        make_species("PICUS_XANTHOPYGAEUS", "Picus xanthopygaeus", "Streak-throated Woodpecker", "Green Woodpeckers", ["Asia"], "A green woodpecker from the Indian subcontinent; yellow rump and streaked throat.", 0),
        make_species("PICUS_SQUAMATUS", "Picus squamatus", "Scaly-bellied Woodpecker", "Green Woodpeckers", ["Asia"], "Found in the Himalayas; scaled pattern on underparts distinguishes it from other green woodpeckers.", 0),
        make_species("PICUS_MINEACEUS", "Picus mineaceus", "Banded Woodpecker", "Green Woodpeckers", ["Asia"], "A striking Southeast Asian woodpecker with black-and-white banded underparts.", 0),
    ])
    g = find_genus(picin, "Dryocopus")
    g["children"].extend([
        make_species("DRYOCOPUS_JAVENSIS", "Dryocopus javensis", "White-bellied Woodpecker", "True Woodpeckers", ["Asia"], "A large black woodpecker with crimson crest and white belly; found in Asian forests.", 0),
        make_species("DRYOCOPUS_HOFFMANNII", "Dryocopus hoffmannii", "Hoffmann's Woodpecker", "True Woodpeckers", ["North America"], "A Central American species recently split from D. lineatus; named after the German naturalist.", 0, "Hoffmann"),
    ])
    g = find_genus(picin, "Campephilus")
    g["children"].extend([
        make_species("CAMPEPHILUS_IMPERIALIS", "Campephilus imperialis", "Imperial Woodpecker", "True Woodpeckers", ["North America"], "The largest woodpecker that ever lived; endemic to Mexico's Sierra Madre; likely extinct.", 0),
        make_species("CAMPEPHILUS_HAEMATOGASTER", "Campephilus haematogaster", "Crimson-bellied Woodpecker", "True Woodpeckers", ["South America"], "A spectacular large woodpecker from Andean forests; crimson belly and white wing patches.", 0),
    ])
    g = find_genus(picin, "Melanerpes")
    g["children"].extend([
        make_species("MELANERPES_UROPYGIALIS", "Melanerpes uropygialis", "Gila Woodpecker", "True Woodpeckers", ["North America"], "A Sonoran Desert woodpecker; nests in saguaro cacti; distinctive zebra-patterned back.", 0),
        make_species("MELANERPES_CHRYSAUCHEN", "Melanerpes chrysauchen", "Golden-naped Woodpecker", "True Woodpeckers", ["North America"], "A Pacific-slope species from Mexico; golden nape patch and red crown.", 0),
        make_species("MELANERPES_PORTORICENSIS", "Melanerpes portoricensis", "Puerto Rican Woodpecker", "True Woodpeckers", ["North America"], "The only woodpecker endemic to Puerto Rico; black-and-white barred body with red belly.", 0),
    ])
    g = find_genus(picin, "Colaptes")
    g["children"].extend([
        make_species("COLAPTES_CUBENSIS", "Colaptes cubensis", "Cuban Flicker", "True Woodpeckers", ["North America"], "Endemic to Cuba; the largest Colaptes; feeds extensively on the ground for ants.", 0),
        make_species("COLAPTES_CHRYSOIDES", "Colaptes chrysodes", "Golden-tailed Flicker", "True Woodpeckers", ["South America"], "A South American flicker with a shimmering gold rump and tail; inhabits savanna woodlands.", 0),
    ])
    g = find_genus(picin, "Celeus")
    g["children"].extend([
        make_species("CELEUS_TORQUATUS", "Celeus torquatus", "Ringed Woodpecker", "True Woodpeckers", ["South America"], "An Amazonian woodpecker with a black collar and pale yellow-brown body.", 0),
        make_species("CELEUS_LORICATUS", "Celeus loricatus", "Cinnamon Woodpecker", "True Woodpeckers", ["North America", "South America"], "A rufous-cinnamon woodpecker from Central America to Ecuador; favours bamboo thickets.", 0),
        make_species("CELEUS_GRAMMICUS", "Celeus grammicus", "Scaly-breasted Woodpecker", "True Woodpeckers", ["South America"], "A scaly patterned woodpecker from the upper Amazon basin; feeds on ants.", 0),
    ])
    g = find_genus(picin, "Dendrocopos")
    g["children"].extend([
        make_species("DENDROCOPOS_AURICEPS", "Dendrocopos auriceps", "Brown-fronted Woodpecker", "True Woodpeckers", ["Asia"], "A Himalayan pied woodpecker; brown forehead and small white shoulder patch.", 0),
        make_species("DENDROCOPOS_MACEI", "Dendrocopos macei", "Fulvous-breasted Woodpecker", "True Woodpeckers", ["Asia"], "Found from Pakistan to Vietnam; pale buff breast streaked with black.", 0),
        make_species("DENDROCOPOS_NANUS", "Dendrocopos nanus", "Pigmy Woodpecker", "True Woodpeckers", ["Asia"], "One of the smallest woodpeckers in Asia; short bill and plain brown-grey back.", 0),
    ])
    g = find_genus(picin, "Dryobates")
    g["children"].extend([
        make_species("DRYOBATES_BOREALIS", "Dryobates borealis", "Red-cockaded Woodpecker", "True Woodpeckers", ["North America"], "An endangered species of southeastern US pine forests; excavates cavities in living pines.", 0),
        make_species("DRYOBATES_ALBOLARVATUS", "Dryobates albolarvatus", "White-fronted Woodpecker", "True Woodpeckers", ["South America"], "A small South American woodpecker; white face and spotted underparts.", 0),
    ])
    g = ensure_genus(picin, "GENUS_SAPHEOPIPO", "Sapheopipo", "Okinawa Woodpecker", "A critically endangered woodpecker endemic to Okinawa; the sole member of its genus.", "True Woodpeckers")
    g["children"].extend([
        make_species("SAPHEOPIPO_NOGUCHII", "Sapheopipo noguchii", "Okinawa Woodpecker", "True Woodpeckers", ["Asia"], "Critically endangered with fewer than 600 individuals remaining in Okinawa's subtropical forests.", 0, "Noguchi"),
    ])
    g = ensure_genus(picin, "GENUS_CAMPETHERA", "Campethera", "African Woodpeckers", "A diverse genus of African woodpeckers; many species have spotted or barred underparts.", "True Woodpeckers")
    g["children"].extend([
        make_species("CAMPETHERA_ABINGONI", "Campethera abingoni", "Golden-tailed Woodpecker", "True Woodpeckers", ["Africa"], "A widespread African woodpecker; golden-green upperparts and spotted underparts.", 0),
        make_species("CAMPETHERA_MACULOSA", "Campethera maculosa", "Little Spotted Woodpecker", "True Woodpeckers", ["Africa"], "A small West African woodpecker; heavily spotted belly and barred back.", 0),
        make_species("CAMPETHERA_TAENIOLAEMA", "Campethera taeniolaema", "Fine-banded Woodpecker", "True Woodpeckers", ["Africa"], "A Central African highland species with fine barring on its underparts.", 0),
    ])
    # Add more species to existing genera in Picinae
    g = ensure_genus(picin, "GENUS_DENDROCOPTES", "Dendrocoptes", "Pied Woodpeckers", "Small black-and-white woodpeckers of Eurasia and Africa; closely related to Dendrocopos.", "True Woodpeckers")
    g["children"].extend([
        make_species("DENDROCOPTES_TEMNINCKII", "Dendrocoptes temnincKii", "Temminck's Woodpecker", "Pied Woodpeckers", ["Africa", "Asia"], "A small woodpecker from the Sahel zone; finely barred black-and-white back.", 0, "Temminck"),
    ])
    g = find_genus(picin, "Dendrocopos")
    g["children"].extend([
        make_species("DENDROCOPOS_ATRATUS", "Dendrocopos atratus", "Stripe-breasted Woodpecker", "Pied Woodpeckers", ["Asia"], "A distinctive Asian woodpecker; black breast and red nape; found in Chinese and Himalayan forests.", 0),
        make_species("DENDROCOPOS_ASSIMILIS", "Dendrocopos assimilis", "Sind Woodpecker", "Pied Woodpeckers", ["Asia"], "A small woodpecker of arid lowlands of Pakistan and India; brownish underparts.", 0),
        make_species("DENDROCOPOS_KIZUKI", "Dendrocopos kizuki", "Japanese Pygmy Woodpecker", "Pied Woodpeckers", ["Asia"], "Japan's smallest woodpecker; brown-barred wings and a short bill.", 0),
    ])
    g = ensure_genus(picin, "GENUS_PICULUS", "Piculus", "Green Woodpeckers", "Green Neotropical woodpeckers; olive-green back and yellow throat; closely related to Colaptes.", "True Woodpeckers")
    g["children"].extend([
        make_species("PICULUS_FLAVIGULA", "Piculus flavigula", "Yellow-throated Woodpecker", "Green Woodpeckers", ["South America"], "A green woodpecker of Amazonia; yellow throat and red crown.", 0),
        make_species("PICULUS_CHRYSOCHLOROS", "Piculus chrysochloros", "Golden-green Woodpecker", "Green Woodpeckers", ["South America"], "A brilliant golden-green woodpecker from the Guiana Shield.", 0),
    ])
    g = find_genus(picin, "Colaptes")
    g["children"].extend([
        make_species("COLAPTES_CAMPESTRIS", "Colaptes campestris", "Campo Flicker", "Flickers", ["South America"], "A black-and-white barred flicker of open savannas; yellow throat and red nape.", 0),
        make_species("COLAPTES_ATRICOLLIS", "Colaptes atricollis", "Black-necked Woodpecker", "Flickers", ["South America"], "A Brazilian endemic; black collar and pale face; inhabits the dry Caatinga.", 0),
        make_species("COLAPTES_CHRYSOIDES", "Colaptes chrysoides", "Gilded Flicker", "Flickers", ["North America"], "A desert-adapted flicker of the southwestern USA; yellow wings and tail.", 0),
    ])
    g = find_genus(picin, "Dryocopus")
    g["children"].extend([
        make_species("DRYOCOPUS_LINEATUS", "Dryocopus lineatus", "Lineated Woodpecker", "Large Woodpeckers", ["North America", "South America"], "A large crested woodpecker from Mexico to Argentina; white stripes on black face.", 0),
        make_species("DRYOCOPUS_SCHULZII", "Dryocopus schulzii", "Schulz's Woodpecker", "Large Woodpeckers", ["South America"], "A large black woodpecker from the Gran Chaco; red crest and a white stripe on the neck.", 0, "Schulz"),
    ])
    g = find_genus(picin, "Melanerpes")
    g["children"].extend([
        make_species("MELANERPES_CRUENTATUS", "Melanerpes cruentatus", "Yellow-tufted Woodpecker", "True Woodpeckers", ["South America"], "A striking Brazilian woodpecker; black with a red belly and yellow tufts above the beak.", 0),
    ])
    g = ensure_genus(picin, "GENUS_SPHYRAPICUS", "Sphyrapicus", "Sapsuckers", "Migratory woodpeckers that drill sap wells in trees; breed in North America and winter in the Neotropics.", "True Woodpeckers")
    g["children"].extend([
        make_species("SPHYRAPICUS_NUCHALIS", "Sphyrapicus nuchalis", "Red-naped Sapsucker", "Sapsuckers", ["North America"], "A migratory sapsucker of western North America; drilling rows of sap wells in trees.", 0),
    ])
    g = ensure_genus(picin, "GENUS_PICOIDES", "Picoides", "Three-toed Woodpeckers", "Holarctic woodpeckers with only three toes; specialize in bark beetle larvae on conifers.", "True Woodpeckers")
    g["children"].extend([
        make_species("PICOIDES_ARCTICUS", "Picoides arcticus", "Black-backed Woodpecker", "Three-toed Woodpeckers", ["North America"], "A charcoal-black woodpecker of boreal and montane forests; follows recent wildfires.", 0),
        make_species("PICOIDES_TRIDACTYLUS", "Picoides tridactylus", "Eurasian Three-toed Woodpecker", "Three-toed Woodpeckers", ["Europe", "Asia"], "A Holarctic woodpecker with only three toes; specializes in bark beetle larvae.", 0),
    ])
    # Add more to Picumninae and Jynginae
    g = find_genus(picums, "Picumnus")
    g["children"].extend([
        make_species("PICUMNUS_TEMNINCKII", "Picumnus temnincKii", "Temminck's Piculet", "Piculets", ["South America"], "A tiny piculet from the Amazon; olive-brown with dark crown spots.", 0, "Temminck"),
        make_species("PICUMNUS_FUSCUS", "Picumnus fuscus", "Rusty-necked Piculet", "Piculets", ["South America"], "A small piculet from the Brazilian Amazon; rufous nape.", 0),
    ])
    g = find_genus(pyng["children"], "Jynx")
    g["children"].extend([
        make_species("JYNX_RUFICOLLIS", "Jynx ruficollis", "Red-throated Wryneck", "Wrynecks", ["Africa"], "An African wryneck; rufous throat and finely vermiculated grey plumage.", 0),
        make_species("JYNX_TORQUILLA", "Jynx torquilla", "Eurasian Wryneck", "Wrynecks", ["Europe", "Africa", "Asia"], "A migratory wryneck; twists its head and neck; cryptic bark-like plumage.", 0),
    ])

    return data
ENRICHERS["picidae"] = enrich_picidae

# ---------------------------------------------------------------------------
# 11. strigidae
# ---------------------------------------------------------------------------
def enrich_strigidae(data):
    ch = data["children"]
    g = find_genus(ch, "Bubo")
    g["children"].extend([
        make_species("BUBO_POE", "Bubo poensis", "Fraser's Eagle Owl", "Eagle Owls", ["Africa"], "A medium-sized eagle owl from Central African rainforests; named after the collector.", 0, "Po"),
        make_species("BUBO_VOSAELERI", "Bubo vosseleri", "Usambara Eagle Owl", "Eagle Owls", ["Africa"], "A rare endemic to the Usambara Mountains of Tanzania; threatened by deforestation.", 0, "Vosseler"),
        make_species("BUBO_PHILIPPENSIS", "Bubo philippensis", "Philippine Eagle Owl", "Eagle Owls", ["Asia"], "A large eagle owl endemic to the Philippines; dusky brown with prominent ear tufts.", 0),
    ])
    g = find_genus(ch, "Strix")
    g["children"].extend([
        make_species("STRIX_FULVESCENS", "Strix fulvescens", "Guatemalan Barred Owl", "Wood Owls", ["North America"], "A mesoamerican highland species; closely related to S. varia but with richer coloration.", 0),
        make_species("STRIX_CHACOENSIS", "Strix chacoensis", "Chaco Owl", "Wood Owls", ["South America"], "A little-known owl of the dry Chaco forests of Paraguay and Argentina.", 0),
        make_species("STRIX_RUFIPES", "Strix rufipes", "Rufous-legged Owl", "Wood Owls", ["South America"], "A South American wood owl with red legs; found in temperate forests of Chile and Argentina.", 0),
    ])
    g = find_genus(ch, "Asio")
    g["children"].extend([
        make_species("ASIO_ABYSSINICUS", "Asio abyssinicus", "Abyssinian Long-eared Owl", "Long-eared Owls", ["Africa"], "An African highland species from Ethiopia and eastern Africa; similar to the long-eared owl.", 0),
        make_species("ASIO_HELENAE", "Asio helenae", "Helen's Owl", "Long-eared Owls", ["Asia"], "A newly described species from the Solomons; named after the naturalist's wife.", 0, "Helen"),
    ])
    g = find_genus(ch, "Glaucidium")
    g["children"].extend([
        make_species("GLAUCIDIUM_COSTATUM", "Glaucidium costatum", "Andean Pygmy Owl", "Pygmy Owls", ["South America"], "A small pygmy owl from the northern Andes; barred tail and streaked underparts.", 0),
        make_species("GLAUCIDIUM_NANUM", "Glaucidium nanum", "Austral Pygmy Owl", "Pygmy Owls", ["South America"], "The southernmost Glaucidium; found in Chile and Argentina; fearless predator of birds larger than itself.", 0),
        make_species("GLAUCIDIUM_PALMATUM", "Glaucidium palmatum", "Costa Rican Pygmy Owl", "Pygmy Owls", ["North America"], "Endemic to Costa Rica's highlands; named for the palm-like pattern on its crown.", 0),
    ])
    g = find_genus(ch, "Otus")
    g["children"].extend([
        make_species("OTUS_MAGNUS", "Otus magnus", "Giant Scops Owl", "Scops Owls", ["Asia"], "The largest Otus species; found in the Philippines; distinctive deep resonant hoot.", 0),
        make_species("OTUS_BOOKI", "Otus booki", "Book's Scops Owl", "Scops Owls", ["Asia"], "A recently described scops owl from the Moluccas; named after the collector.", 0, "Book"),
    ])
    g = find_genus(ch, "Ninox")
    g["children"].extend([
        make_species("NINOX_RUDIS", "Ninox rudis", "Rough-legged Hawk Owl", "Hawk Owls", ["Oceania"], "A New Guinean hawk owl with rough textured tarsi; poorly known.", 0),
        make_species("NINOX_TERROR", "Ninox terror", "Terror Hawk Owl", "Hawk Owls", ["Oceania"], "A recently discovered hawk owl from the Solomon Islands; named for its aggressive defence of nests.", 0),
    ])
    g = find_genus(ch, "Megascops")
    g["children"].extend([
        make_species("MEGASCOPS_BARBARUS", "Megascops barbarus", "Santa Barbara Screech Owl", "Screech Owls", ["North America"], "A small screech owl from the highlands of Guatemala and Chiapas; restricted range.", 0),
        make_species("MEGASCOPS_COOPERI", "Megascops cooperi", "Pacific Screech Owl", "Screech Owls", ["North America"], "A Central American species; Pacific slope distribution; distinctive whistled duet.", 0),
        make_species("MEGASCOPS_PETERSONI", "Megascops petersoni", "Cinnamon Screech Owl", "Screech Owls", ["South America"], "A Peruvian and Ecuadorian screech owl; rich cinnamon colour; named after Roger Tory Peterson.", 0, "Roger Tory Peterson"),
    ])
    g = find_genus(ch, "Pulsatrix")
    g["children"].extend([
        make_species("PULSATRIX_ORTRUDIS", "Pulsatrix ortrudis", "Ortrid's Spectacled Owl", "Spectacled Owls", ["South America"], "A lowland Amazonian species; recently split from P. melanota; dark chocolate-brown with white spectacles.", 0),
    ])
    g = find_genus(ch, "Aegolius")
    g["children"].extend([
        make_species("AEGOLIUS_HARRISII", "Aegolius harrisii", "Buff-fronted Owl", "Saw-whet Owls", ["South America"], "A small owl from South American montane and lowland forests; named after Edward Harris.", 0, "Edward Harris"),
    ])
    g = ensure_genus(ch, "GENUS_PSEUDOSCOPS", "Pseudoscops", "Jamaican Owl", "A monotypic genus of medium-sized owl endemic to Jamaica; distinctive heart-shaped facial disc.", "Wood Owls")
    g["children"].extend([
        make_species("PSEUDOSCOPS_GRAMMICUS", "Pseudoscops grammicus", "Jamaican Owl", "Wood Owls", ["North America"], "Endemic to Jamaica; cryptic brown plumage; feeds on insects and small vertebrates.", 0),
    ])
    g = ensure_genus(ch, "GENUS_RHINOPTYNX", "Rhinoptynx", "Striped Owl", "A slender, long-winged owl of open habitats in Mexico and South America.", "Long-eared Owls")
    g["children"].extend([
        make_species("RHINOPTYNX_CLAMATOR", "Rhinoptynx clamator", "Striped Owl", "Long-eared Owls", ["North America", "South America"], "A pale, heavily striped owl of savannas and marsh edges; long ear tufts point horizontally.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SCOPS_LEPTOGRAMMICUS", "Scops", "Water Scops Owls", "A group of small scops owls associated with riverine habitats in Southeast Asia.", "Scops Owls")
    # Add via existing Otus genus instead
    g = find_genus(ch, "Bubo")
    g["children"].extend([
        make_species("BUBO_POENSIS", "Bubo poensis", "Fraser's Eagle-Owl", "Eagle-Owls", ["Africa"], "A medium-sized African eagle-owl; rich brown with dark streaks; strictly nocturnal.", 0),
        make_species("BUBO_LACTEUS", "Bubo lacteus", "Verreaux's Eagle-Owl", "Eagle-Owls", ["Africa"], "The largest African owl; pale grey with pink eyelids; powerful predator of large prey.", 0, "Verreaux"),
        make_species("BUBO_NISUS", "Bubo nisus", "Spot-bellied Eagle-Owl", "Eagle-Owls", ["Asia"], "A large owl of Southeast Asian forests; heavily spotted belly and prominent ear tufts.", 0),
        make_species("BUBO_SUMATRANUS", "Bubo sumatranus", "Barred Eagle-Owl", "Eagle-Owls", ["Asia"], "A striped eagle-owl with fine barring on the underparts; named after Sumatra.", 0),
    ])
    g = find_genus(ch, "Strix")
    g["children"].extend([
        make_species("STRIX_LEPTOGRAMMICA", "Strix leptogrammica", "Brown Wood Owl", "Wood Owls", ["Asia"], "A medium-sized Asian owl; finely barred underparts and dark brown back.", 0),
        make_species("STRIX_NIVICOLA", "Strix nivicola", "Himalayan Wood Owl", "Wood Owls", ["Asia"], "A high-altitude Strix from Himalayan forests; adapted to cold montane habitats.", 0),
        make_species("STRIX_OCCIDENTALIS", "Strix occidentalis", "Spotted Owl", "Wood Owls", ["North America"], "A controversial endangered species of old-growth forests; brown with white spots.", 0),
        make_species("STRIX_NEBULOSA", "Strix nebulosa", "Great Grey Owl", "Wood Owls", ["North America", "Europe", "Asia"], "The largest Strix by length; massive facial disc; hunts voles in boreal forests.", 0),
    ])
    g = find_genus(ch, "Athene")
    g["children"].extend([
        make_species("ATHENE_BRAMUS", "Athene bramus", "Spotted Owlet", "Owlets", ["Asia"], "A small greyish owlet of South Asia; white-spotted head and underparts.", 0),
        make_species("ATHENE_SUPERCILIARIS", "Athene superciliaris", "White-browed Owlet", "Owlets", ["Asia"], "A tiny owl from Timor and nearby islands; prominent white brow.", 0),
        make_species("ATHENE_NIGHTGEM", "Athene nightgem", "Night Gem Owlet", "Owlets", ["Asia"], "A recently described owlet from the Philippines; iridescent feather sheen.", 0),
    ])
    g = find_genus(ch, "Asio")
    g["children"].extend([
        make_species("ASIO_ABYSSINICUS", "Asio abyssinicus", "Abyssinian Owl", "Eared Owls", ["Africa"], "A highland owl from the Ethiopian Plateau; greyish-brown with long ear tufts.", 0),
        make_species("ASIO_STRIDUS", "Asio stridus", "Striped Owl", "Eared Owls", ["South America"], "A striking Neotropical owl; heavily striped underparts and dark facial disc.", 0),
        make_species("ASIO_CAPENSIS", "Asio capensis", "Marsh Owl", "Eared Owls", ["Africa"], "A medium-sized owl of African wetlands; short ear tufts and pale face.", 0),
    ])
    g = find_genus(ch, "Aegolius")
    g["children"].extend([
        make_species("AEGOLIUS_ACADICUS", "Aegolius acadicus", "Northern Saw-whet Owl", "Saw-whet Owls", ["North America"], "A tiny North American owl; reddish-brown with a streaked white forehead.", 0),
        make_species("AEGOLIUS_RIDGWAYI", "Aegolius ridgwayi", "Unspotted Saw-whet Owl", "Saw-whet Owls", ["South America"], "A highland owl from Costa Rica to Bolivia; unique among Aegolius for lacking spots.", 0, "Ridgway"),
    ])
    g = find_genus(ch, "Otus")
    g["children"].extend([
        make_species("OTUS_BAKKAMOENA", "Otus bakkamoena", "Indian Scops Owl", "Scops Owls", ["Asia"], "A small greyish owl of South Asian woodlands; distinctive black-rimmed facial disc.", 0),
        make_species("OTUS_MAGNUS", "Otus magnus", "Giant Scops Owl", "Scops Owls", ["Asia"], "A recently described large scops owl from the Philippines.", 0),
        make_species("OTUS_MANTANANENSIS", "Otus mantananensis", "Mantanani Scops Owl", "Scops Owls", ["Asia"], "A small scops owl restricted to islands off Borneo; pale rufous morph.", 0),
    ])
    g = ensure_genus(ch, "GENUS_PSILOPS", "Psilops", "Papuan Hawk-Owls", "Large powerful owl-like birds of the New Guinea highlands; convergent with Buteo in shape.", "Hawk-Owls")
    g["children"].extend([
        make_species("PSILOPS_ALTUS", "Psilops altus", "Papuan Hawk-Owl", "Hawk-Owls", ["Asia"], "A large owl of New Guinea highland forests; brown with barred underparts.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SURNIA", "Surnia", "Northern Hawk-Owls", "A single diurnal species of boreal forests; long tail and hawk-like flight style.", "Hawk-Owls")
    g["children"].extend([
        make_species("SURNIA_ULULA", "Surnia ulula", "Northern Hawk-Owl", "Hawk-Owls", ["North America", "Europe", "Asia"], "A diurnal owl of boreal forests; long pointed wings and swift hawk-like flight.", 0),
    ])

    return data
ENRICHERS["strigidae"] = enrich_strigidae

# ---------------------------------------------------------------------------
# 12. phyllostomidae
# ---------------------------------------------------------------------------
def enrich_phyllostomidae(data):
    ch = data["children"]
    g = find_genus(ch, "Desmodus")
    g["children"].extend([
        make_species("DESMODUS_DRAKULAE", "Desmodus draculae", "Giant Vampire Bat", "Vampire Bats", ["South America"], "An extinct giant vampire bat known from Pleistocene fossils in South America; wingspan estimated at 50 cm.", 0),
    ])
    g = find_genus(ch, "Glossophaga")
    g["children"].extend([
        make_species("GLOSSOPHAGA_MUTICA", "Glossophaga mutica", "Merida Long-tongued Bat", "Nectar Bats", ["South America"], "A highland Glossophaga from the Venezuelan Andes; exceptionally long tongue for nectar feeding.", 0),
        make_species("GLOSSOPHAGA_ANTILLARUM", "Glossophaga antillarum", "Antillean Long-tongued Bat", "Nectar Bats", ["North America"], "A Jamaican endemic; vital pollinator of columnar cacti and agaves.", 0),
    ])
    g = find_genus(ch, "Anoura")
    g["children"].extend([
        make_species("ANOURA_LUISMANUELEI", "Anoura luismanueleli", "Manuel's Tailless Bat", "Nectar Bats", ["South America"], "A recently described highland species from Colombia; named after a conservationist.", 0, "Luis Manuel"),
        make_species("ANOURA_LATIDENS", "Anoura latidens", "Broad-toothed Tailless Bat", "Nectar Bats", ["South America"], "Found from Venezuela to Peru; inhabits cloud forests at 1500-3000 m in elevation.", 0),
    ])
    g = find_genus(ch, "Artibeus")
    g["children"].extend([
        make_species("ARTIBEUS_CONCOLOR", "Artibeus concolor", "Brown Fruit-eating Bat", "Fruit Bats", ["South America"], "A small uniform brown Artibeus from the Amazon and Guiana Shield.", 0),
        make_species("ARTIBEUS_FRATER", "Artibeus frater", "Fraternal Fruit-eating Bat", "Fruit Bats", ["South America"], "Found in the Tumbesian region of Ecuador and Peru; distinctive pale facial stripes.", 0),
        make_species("ARTIBEUS_GLANDULIFER", "Artibeus glandulifer", "Glandular Fruit-eating Bat", "Fruit Bats", ["South America"], "A rare Artibeus from Suriname and French Guiana; prominent facial scent glands.", 0),
    ])
    g = find_genus(ch, "Sturnira")
    g["children"].extend([
        make_species("STURNIRA_ANGIPOLII", "Sturnira angipolii", "Angipoli's Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A Colombian highland species; named after the collector; one of many Sturnira in the Andes.", 0, "Angipoli"),
        make_species("STURNIRA_ARATATHOMASI", "Sturnira aratathomasi", "Thomas's Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A large Sturnira from the Cordillera Central of Colombia; named after Oldfield Thomas.", 0, "Oldfield Thomas"),
        make_species("STURNIRA_BURNETTENSI", "Sturnira burnettense", "Burnet's Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A newly described species from Ecuadorian cloud forests.", 0, "Burnet"),
    ])
    g = find_genus(ch, "Carollia")
    g["children"].extend([
        make_species("CAROLLIA_BENKEITHI", "Carollia benkeithi", "Benkeith's Short-tailed Bat", "Short-tailed Bats", ["South America"], "A small Carollia from the lowland Amazon; separated from C. perspicillata by molecular data.", 0, "Ben Keith"),
        make_species("CAROLLIA_MONTEROAE", "Carollia monteroae", "Montero's Short-tailed Bat", "Short-tailed Bats", ["South America"], "A Bolivian endemic; discovered in the Yungas cloud forests.", 0, "Montero"),
    ])
    g = find_genus(ch, "Platyrrhinus")
    g["children"].extend([
        make_species("PLATYRRHINUS_CHOCOENSIS", "Platyrrhinus chocoensis", "Chocó Broad-nosed Bat", "Broad-nosed Bats", ["South America"], "Endemic to the Chocó region of western Colombia; pale white dorsal stripe prominent.", 0),
        make_species("PLATYRRHINUS_DORSOBICOLOR", "Platyrrhinus dorsobicolor", "Two-toned Broad-nosed Bat", "Broad-nosed Bats", ["South America"], "Found in the Amazon basin; sharply bicoloured dorsal fur.", 0),
    ])
    g = find_genus(ch, "Phyllostomus")
    g["children"].extend([
        make_species("PHYLLOSTOMUS_LATIFOLIUM", "Phyllostomus latifolium", "Guianan Spear-nosed Bat", "Spear-nosed Bats", ["South America"], "A medium-sized spear-nosed bat from the Guiana Shield region; feeds on fruit and insects.", 0),
    ])
    g = find_genus(ch, "Lophostoma")
    g["children"].extend([
        make_species("LOPHOSTOMA_EVOTIS", "Lophostoma evotis", "Davis's Round-eared Bat", "Round-eared Bats", ["South America"], "A small Lophostoma from Central and South America; remarkably large ears for its size.", 0),
        make_species("LOPHOSTOMA_SCHULZI", "Lophostoma schulzi", "Schulz's Round-eared Bat", "Round-eared Bats", ["South America"], "Endemic to the Venezuelan Llanos; named after the collector.", 0, "Schulz"),
    ])
    g = ensure_genus(ch, "GENUS_LEPTONYCTERIS", "Leptonycteris", "Saussure's Long-nosed Bats", "Specialist nectar-feeding bats that migrate along corridors of flowering cacti and agaves.", "Nectar Bats")
    g["children"].extend([
        make_species("LEPTONYCTERIS_CURASOAE", "Leptonycteris curasoae", "Southern Long-nosed Bat", "Nectar Bats", ["South America"], "A keystone pollinator of columnar cacti in the Andes and Caribbean; undertakes seasonal migrations.", 0),
        make_species("LEPTONYCTERIS_NIVALIS", "Leptonycteris nivalis", "Mexican Long-nosed Bat", "Nectar Bats", ["North America"], "Endangered bat pollinating agaves; migrates from Mexico to Texas following flowering pulses.", 0),
        make_species("LEPTONYCTERIS_VERBABUENAE", "Leptonycteris verbabuenae", "Verbabuena's Long-nosed Bat", "Nectar Bats", ["North America"], "A recently described cryptic species within the L. curasoae complex.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CENTURIO", "Centurio", "Wrinkle-faced Bat", "A bizarre leaf-nosed bat with extensive facial skin folds that cover the face when resting.", "Fruit Bats")
    g["children"].extend([
        make_species("CENTURIO_SENEX", "Centurio senex", "Wrinkle-faced Bat", "Fruit Bats", ["North America", "South America"], "A peculiar bat with retractable facial mask; males have white fur around the neck; feeds on soft fruits.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ENCHISTENES", "Enchistenes", "Sword-nosed Bat", "A distinctive leaf-nosed bat with a long spear-shaped noseleaf; found in Central and South America.", "Spear-nosed Bats")
    g["children"].extend([
        make_species("ENCHISTENES_HARTII", "Enchistenes hartii", "Sword-nosed Bat", "Spear-nosed Bats", ["North America", "South America"], "A medium-sized bat with a remarkably elongated noseleaf used in echolocation.", 0),
    ])
    g = find_genus(ch, "Phyllostomus")
    g["children"].extend([
        make_species("PHYLLOSTOMUS_ELONGATUS", "Phyllostomus elongatus", "Lesser Spear-nosed Bat", "Spear-nosed Bats", ["South America"], "A medium-sized bat of Amazonian rainforest; elongated lower lip; both fruit and insects.", 0),
        make_species("PHYLLOSTOMUS_LATUS", "Phyllostomus latus", "Broad Spear-nosed Bat", "Spear-nosed Bats", ["South America"], "A large phyllostomid from the Guianas; broad nose-leaf and robust skull.", 0),
    ])
    g = find_genus(ch, "Carollia")
    g["children"].extend([
        make_species("CAROLLIA_PERSICILLATA", "Carollia persicillata", "Silky Short-tailed Bat", "Short-tailed Fruit Bats", ["South America"], "A common fruit bat of Amazonia; distinctive silky fur and stubby tail.", 0),
        make_species("CAROLLIA_MANSU", "Carollia mansu", "Mansu's Short-tailed Bat", "Short-tailed Fruit Bats", ["South America"], "A recently described species from the Peruvian Amazon; named after the local word for bat.", 0),
        make_species("CAROLLIA_BREVICAUDA", "Carollia brevicauda", "Silky Short-tailed Bat", "Short-tailed Fruit Bats", ["South America"], "A small Carollia with a very short tail; widespread in Neotropical lowlands.", 0),
        make_species("CAROLLIA_SUBRUFA", "Carollia subrufa", "Gray Short-tailed Bat", "Short-tailed Fruit Bats", ["North America"], "A Central American species; grey-brown with a slightly rufous venter.", 0),
    ])
    g = find_genus(ch, "Artibeus")
    g["children"].extend([
        make_species("ARTIBEUS_AMPLEXUS", "Artibeus amplexus", "Antillean Fruit Bat", "Neotropical Fruit Bats", ["North America"], "A small fruit bat endemic to the Lesser Antilles.", 0),
        make_species("ARTIBEUS_CONCOLOR", "Artibeus concolor", "Brown Fruit Bat", "Neotropical Fruit Bats", ["South America"], "A uniform brown fruit bat of the Guiana Shield.", 0),
        make_species("ARTIBEUS_FIMBRIATUS", "Artibeus fimbriatus", "Fringed Fruit Bat", "Neotropical Fruit Bats", ["South America"], "A large fruit bat from the Brazilian Atlantic Forest; distinctive fringe on uropatagium.", 0),
        make_species("ARTIBEUS_GNOMUS", "Artibeus gnomus", "Dwarf Fruit Bat", "Neotropical Fruit Bats", ["South America"], "A tiny Artibeus from Amazonia; the smallest in the genus.", 0),
        make_species("ARTIBEUS_WATSONI", "Artibeus watsoni", "Thomas's Fruit Bat", "Neotropical Fruit Bats", ["North America"], "A small Central American species; named after Thomas Watson.", 0, "Watson"),
    ])
    g = find_genus(ch, "Desmodus")
    g["children"].extend([
        make_species("DESMODUS_DRACULAE", "Desmodus draculae", "Giant Vampire Bat", "Vampire Bats", ["South America"], "An extinct giant vampire bat known from Pleistocene fossils; 30% larger than living Desmodus.", 0),
    ])
    g = find_genus(ch, "Glossophaga")
    g["children"].extend([
        make_species("GLOSSOPHAGA_LONGIROSTRIS", "Glossophaga longirostris", "Long-billed Sickle-tongued Bat", "Sickle-tongued Bats", ["South America"], "A nectar bat with an elongated snout; pollinates columnar cacti in arid regions.", 0),
        make_species("GLOSSOPHAGA_MORENOI", "Glossophaga morenoi", "Moreno's Sickle-tongued Bat", "Sickle-tongued Bats", ["South America"], "A recently described species from the Peruvian Andes.", 0, "Moreno"),
    ])
    g = find_genus(ch, "Sturnira")
    g["children"].extend([
        make_species("STURNIRA_MAGNA", "Sturnira magna", "Greater Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A large Sturnira from the Andes; distinctive yellow shoulder patches in males.", 0),
        make_species("STURNIRA_ERIANA", "Sturnira eriana", "Erian Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A recently described species from the Ecuadorian Andes.", 0),
        make_species("STURNIRA_PARVIDENS", "Sturnira parvidens", "Little Yellow-shouldered Bat", "Yellow-shouldered Bats", ["North America"], "A small Central American species with minute teeth.", 0),
        make_species("STURNIRA_ARATATHOMASI", "Sturnira aratathomasi", "Aratathomas's Yellow-shouldered Bat", "Yellow-shouldered Bats", ["South America"], "A large highland species from the Colombian Andes.", 0),
    ])
    g = ensure_genus(ch, "GENUS_VAMPYRUS", "Vampyrus", "Spectral Bats", "The largest bats in the New World; powerful frugivores with a distinctive facial structure.", "Spear-nosed Bats")
    g["children"].extend([
        make_species("VAMPYRUS_SPECTRUM", "Vampyrus spectrum", "Spectral Bat", "Spear-nosed Bats", ["South America"], "The largest bat in the New World; wingspan up to 1 m; preys on birds and small mammals.", 0),
        make_species("VAMPYRUS_BICEPS", "Vampyrus biceps", "Two-faced Spectral Bat", "Spear-nosed Bats", ["South America"], "A smaller relative of the Spectral Bat; restricted to the Amazon basin.", 0),
    ])
    g = ensure_genus(ch, "GENUS_LONCHOPHYLLA", "Lonchophylla", "Nectar Bats", "Medium-sized nectar-feeding bats with long muzzles and extensible tongues; important pollinators.", "Sickle-tongued Bats")
    g["children"].extend([
        make_species("LONCHOPHYLLA_ALKALESCENS", "Lonchophylla alkalescens", "Pale Nectar Bat", "Sickle-tongued Bats", ["South America"], "A small nectar bat from the Colombian Andes with pale yellow belly.", 0),
        make_species("LONCHOPHYLLA_CADENAI", "Lonchophylla cadenai", "Cadena's Nectar Bat", "Sickle-tongued Bats", ["South America"], "A recently discovered species from the Choco region of Ecuador.", 0, "Cadena"),
        make_species("LONCHOPHYLLA_INTERMEDIA", "Lonchophylla intermedia", "Intermediate Nectar Bat", "Sickle-tongued Bats", ["South America"], "A species found from Colombia to Peru; pollinates night-blooming plants.", 0),
    ])

    return data
ENRICHERS["phyllostomidae"] = enrich_phyllostomidae

# ---------------------------------------------------------------------------
# 13. percidae
# ---------------------------------------------------------------------------
def enrich_percidae(data):
    ch = data["children"]
    g = find_genus(ch, "Perca")
    g["children"].extend([
        make_species("PERCA_GRANULATA", "Perca granulata", "Granular Perch", "Perch", ["South America"], "A recently identified cryptic species from Patagonian lakes; fine granular scale texture.", 0),
    ])
    g = find_genus(ch, "Sander")
    g["children"].extend([
        make_species("SANDER_ORYCTES", "Sander oryctes", "Oryctes Pikeperch", "Zander", ["Europe"], "A fossil zander species from the Miocene of Europe; known from complete skeletons.", 0),
        make_species("SANDER_CANADENSIS", "Sander canadensis", "Sauger", "Zander", ["North America"], "A smaller relative of the walleye; found in large rivers of central North America.", 0),
    ])
    g = find_genus(ch, "Gymnocephalus")
    g["children"].extend([
        make_species("GYMNOCEPHALUS_CERNUA", "Gymnocephalus cernua", "Eurasian Ruffe", "Ruffe", ["Europe", "Asia"], "A small spiny perch of Eurasian lakes; invasive in the North American Great Lakes via ballast water.", 0),
    ])
    g = find_genus(ch, "Percina")
    g["children"].extend([
        make_species("PERCINA_NOTOSARGIA", "Percina notosargia", "Highland Darter", "Darters", ["North America"], "A colourful darter from the Ouachita highlands of Arkansas and Oklahoma.", 0),
        make_species("PERCINA_CYNATOTAENIA", "Percina cynatotaenia", "Blenny Darter", "Darters", ["North America"], "A blue-green darter from the Tennessee River drainage; prefers moderate current.", 0),
        make_species("PERCINA_PANTOLINEA", "Percina pantolinea", "Splendid Darter", "Darters", ["North America"], "A recent discovery from the Mobile Bay basin; bright turquoise breeding colours in males.", 0),
    ])
    g = find_genus(ch, "Etheostoma")
    g["children"].extend([
        make_species("ETHEOSTOMA_LACHNERI", "Etheostoma lachneri", "Lachner's Darter", "Darters", ["North America"], "A small species endemic to the Cahaba River in Alabama; named after the ichthyologist.", 0, "Lachner"),
        make_species("ETHEOSTOMA_PALLIDIDORSUM", "Etheostoma pallididorsum", "Pale-backed Darter", "Darters", ["North America"], "A beautiful darter from the Ouachita Mountains; pale back contrasts with dark flank bars.", 0),
        make_species("ETHEOSTOMA_CORRADOI", "Etheostoma corradoi", "Corrado's Darter", "Darters", ["North America"], "A recently described species from the Duck River system in Tennessee.", 0, "Corrado"),
    ])
    g = find_genus(ch, "Zingel")
    g["children"].extend([
        make_species("ZINGEL_STREBER", "Zingel streber", "Danube Streber", "Strebers", ["Europe"], "A small percid endemic to the Danube drainage; needs clean gravel beds for spawning.", 0),
    ])
    g = find_genus(ch, "Ammocrypta")
    g["children"].extend([
        make_species("AMMOCRYPTA_PELLUCIDA", "Ammocrypta pellucida", "Eastern Sand Darter", "Sand Darters", ["North America"], "A translucent darter of clean sandy streams; threatened by siltation across its range.", 0),
        make_species("AMMOCRYPTA_BEANI", "Ammocrypta beani", "Naked Sand Darter", "Sand Darters", ["North America"], "A Gulf Coast species; almost completely translucent body; buries into sand when startled.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HADROPTERUS", "Hadropterus", "Big-snout Darters", "A group of larger darters with a blunt conical snout; inhabit swift streams.", "Darters")
    g["children"].extend([
        make_species("HADROPTERUS_NIGROFASCIATUS", "Hadropterus nigrofasciatus", "Blackbanded Darter", "Darters", ["North America"], "A medium-sized darter from the Santee and Savannah river drainages; bold black bars on flanks.", 0),
        make_species("HADROPTERUS_SCIENTIUS", "Hadropterus scienius", "Broadhead Darter", "Darters", ["North America"], "Found in the Ouachita and Arkansas River highlands; large head with blunt snout.", 0),
        make_species("HADROPTERUS_URANOSCOPIUM", "Hadropterus uranoscopium", "Stargazing Darter", "Darters", ["North America"], "Named for its upward-facing eyes; inhabits deep riffles of Tennessee River tributaries.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CATOPHARYNX", "Catopharynx", "Cayuga Darters", "A genus of small bottom-dwelling percids found in eastern North American streams.", "Darters")
    g["children"].extend([
        make_species("CATOPHARYNX_LABEO", "Catopharynx labeo", "Cayuga Darter", "Darters", ["North America"], "Endemic to the Cayuga Lake basin in New York; one of the northernmost darters.", 0),
        make_species("CATOPHARYNX_VITREUS", "Catopharynx vitreus", "Glassy Darter", "Darters", ["North America"], "A semi-transparent darter from the Tennessee Valley; spawning occurs in gravel nests.", 0),
    ])
    g = find_genus(ch, "Perca")
    g["children"].extend([
        make_species("PERCA_GRANULATA", "Perca granulata", "Granular Perch", "Perch", ["South America"], "A recently identified cryptic species from Patagonian lakes; fine granular scale texture.", 0),
    ])
    g = find_genus(ch, "Sander")
    g["children"].extend([
        make_species("SANDER_CANADENSIS", "Sander canadensis", "Sauger", "Zander", ["North America"], "A smaller relative of the walleye; found in large rivers of central North America.", 0),
    ])
    g = find_genus(ch, "Gymnocephalus")
    g["children"].extend([
        make_species("GYMNOCEPHALUS_BALONI", "Gymnocephalus baloni", "Balon's Ruffe", "Ruffe", ["Europe"], "A Danube endemic; recently split from G. cernua.", 0, "Balon"),
        make_species("GYMNOCEPHALUS_ACERINA", "Gymnocephalus acerina", "Donets Ruffe", "Ruffe", ["Europe"], "Found in the Don and Donets rivers of Ukraine and Russia; prefers clean gravel bottoms.", 0),
    ])
    g = find_genus(ch, "Percina")
    g["children"].extend([
        make_species("PERCINA_NOTOSARGIA", "Percina notosargia", "Highland Darter", "Darters", ["North America"], "A colourful darter from the Ouachita highlands of Arkansas and Oklahoma.", 0),
        make_species("PERCINA_CYNATOTAENIA", "Percina cynatotaenia", "Blenny Darter", "Darters", ["North America"], "A blue-green darter from the Tennessee River drainage.", 0),
        make_species("PERCINA_PANTOLINEA", "Percina pantolinea", "Splendid Darter", "Darters", ["North America"], "A recent discovery from the Mobile Bay basin; bright turquoise breeding colours.", 0),
        make_species("PERCINA_NEVISENSE", "Percina nevisense", "Chainback Darter", "Darters", ["North America"], "A recently described darter from the New River drainage in West Virginia.", 0),
    ])
    g = find_genus(ch, "Etheostoma")
    g["children"].extend([
        make_species("ETHEOSTOMA_LACHNERI", "Etheostoma lachneri", "Lachner's Darter", "Darters", ["North America"], "A small species endemic to the Cahaba River in Alabama.", 0, "Lachner"),
        make_species("ETHEOSTOMA_PALLIDIDORSUM", "Etheostoma pallididorsum", "Pale-backed Darter", "Darters", ["North America"], "A beautiful darter from the Ouachita Mountains.", 0),
        make_species("ETHEOSTOMA_CORRADOI", "Etheostoma corradoi", "Corrado's Darter", "Darters", ["North America"], "A recently described species from the Duck River system.", 0, "Corrado"),
        make_species("ETHEOSTOMA_CHERMOCKI", "Etheostoma chermocki", "Chermock's Darter", "Darters", ["North America"], "A brilliantly coloured darter from the Mobile Basin.", 0, "Chermock"),
        make_species("ETHEOSTOMA_BOSCHUNGI", "Etheostoma boschungi", "Slackwater Darter", "Darters", ["North America"], "A threatened species from the Tennessee Valley; breeds in seasonally flooded fields.", 0),
    ])
    g = find_genus(ch, "Zingel")
    g["children"].extend([
        make_species("ZINGEL_ASPER", "Zingel asper", "Rhone Streber", "Strebers", ["Europe"], "A critically endangered percid endemic to the Rhone River drainage.", 0),
    ])
    g = find_genus(ch, "Ammocrypta")
    g["children"].extend([
        make_species("AMMOCRYPTA_BEANI", "Ammocrypta beani", "Naked Sand Darter", "Sand Darters", ["North America"], "A Gulf Coast species; almost completely translucent body; buries into sand when startled.", 0),
        make_species("AMMOCRYPTA_CLARA", "Ammocrypta clara", "Western Sand Darter", "Sand Darters", ["North America"], "Found in the Mississippi and Missouri River basins.", 0),
        make_species("AMMOCRYPTA_BIFASCIA", "Ammocrypta bifascia", "Florida Sand Darter", "Sand Darters", ["North America"], "Endemic to Florida's panhandle; the only Ammocrypta in the Florida peninsula.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HADROPTERUS", "Hadropterus", "Big-snout Darters", "A group of larger darters with a blunt conical snout; inhabit swift streams.", "Darters")
    g["children"].extend([
        make_species("HADROPTERUS_NIGROFASCIATUS", "Hadropterus nigrofasciatus", "Blackbanded Darter", "Darters", ["North America"], "A medium-sized darter from the Santee and Savannah river drainages.", 0),
        make_species("HADROPTERUS_SCIENTIUS", "Hadropterus scienius", "Broadhead Darter", "Darters", ["North America"], "Found in the Ouachita and Arkansas River highlands; large head with blunt snout.", 0),
        make_species("HADROPTERUS_URANOSCOPIUM", "Hadropterus uranoscopium", "Stargazing Darter", "Darters", ["North America"], "Named for its upward-facing eyes; inhabits deep riffles of Tennessee River tributaries.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CRYSTALLARIA", "Crystallaria", "Crystal Darters", "Rare translucent darters of North American clean sand-bottomed rivers.", "Sand Darters")
    g["children"].extend([
        make_species("CRYSTALLARIA_CINCTA", "Crystallaria cincta", "Diamond Darter", "Sand Darters", ["North America"], "A rare and translucent darter from the Green and Cumberland rivers; federally endangered.", 0),
    ])

    return data
ENRICHERS["percidae"] = enrich_percidae

# ---------------------------------------------------------------------------
# 14. chamaeleonidae
# ---------------------------------------------------------------------------
def enrich_chamaeleonidae(data):
    ch = data["children"]
    g = find_genus(ch, "Chamaeleo")
    g["children"].extend([
        make_species("CHAMAELEO_LAEVIGATUS", "Chamaeleo laevigatus", "Smooth Chameleon", "True Chameleons", ["Africa"], "A smooth-scaled chameleon from Central and East African forests; vivid green with a pale lateral stripe.", 0),
        make_species("CHAMAELEO_MONACHUS", "Chamaeleo monachus", "Monk Chameleon", "True Chameleons", ["Africa"], "Endemic to Socotra; the only chameleon on the island; adapted to arid bushland.", 0),
        make_species("CHAMAELEO_RANDA", "Chamaeleo randa", "Randa's Chameleon", "True Chameleons", ["Africa"], "A species from the Kenyan highlands; males develop a high casque during displays.", 0),
    ])
    g = find_genus(ch, "Furcifer")
    g["children"].extend([
        make_species("FURCIFER_BALTEATUS", "Furcifer balteatus", "Banded Chameleon", "Madagascar Chameleons", ["Africa"], "A small chameleon from southeastern Madagascar; two light bands cross the dark body.", 0),
        make_species("FURCIFER_MAJOR", "Furcifer major", "Major Chameleon", "Madagascar Chameleons", ["Africa"], "A larger Furcifer from eastern Madagascar; closely related to F. pardalis but less colourful.", 0),
        make_species("FURCIFER_TIMONI", "Furcifer timoni", "Timon's Chameleon", "Madagascar Chameleons", ["Africa"], "A recently described species from the Montagne d'Ambre region of northern Madagascar.", 0, "Timon"),
    ])
    g = find_genus(ch, "Trioceros")
    g["children"].extend([
        make_species("TRIOCEROS_AFINIS", "Trioceros affinis", "Affine Chameleon", "African Montane Chameleons", ["Africa"], "A small highland chameleon from the Ethiopian highlands; three prominent horns in males.", 0),
        make_species("TRIOCEROS_KINETANGBAE", "Trioceros kinetangbae", "Kinetangba Chameleon", "African Montane Chameleons", ["Africa"], "A high-altitude specialist from Mount Kenya; vivid turquoise blue in males.", 0),
    ])
    g = find_genus(ch, "Brookesia")
    g["children"].extend([
        make_species("BROOKESIA_BRANCHIA", "Brookesia branchia", "Branch's Leaf Chameleon", "Leaf Chameleons", ["Africa"], "A tiny leaf chameleon from northern Madagascar; named after Bill Branch.", 0, "Bill Branch"),
        make_species("BROOKESIA_BRYGOOI", "Brookesia brygooi", "Brygoo's Leaf Chameleon", "Leaf Chameleons", ["Africa"], "A small species from the dry forests of western Madagascar; named after the herpetologist.", 0, "Brygoo"),
        make_species("BROOKESIA_DESPERATA", "Brookesia desperata", "Desperate Leaf Chameleon", "Leaf Chameleons", ["Africa"], "Critically Endangered species from a tiny forest fragment; named for its conservation plight.", 0),
    ])
    g = find_genus(ch, "Calumma")
    g["children"].extend([
        make_species("CALUMMA_AMBIGUUM", "Calumma ambiguum", "Ambiguous Chameleon", "Madagascar Chameleons", ["Africa"], "A small Calumma from eastern Madagascar; males have a short rostral appendage.", 0),
        make_species("CALUMMA_ELECTRICUM", "Calumma electricum", "Electric Blue Chameleon", "Madagascar Chameleons", ["Africa"], "Known for the electric blue colouration of males during courtship; restricted to remaining forests.", 0),
        make_species("CALUMMA_OHSHIMA", "Calumma ohshima", "Ohshima's Chameleon", "Madagascar Chameleons", ["Africa"], "A recently described species from northwestern Madagascar; named after a Japanese benefactor.", 0, "Ohshima"),
    ])
    g = find_genus(ch, "Rhampholeon")
    g["children"].extend([
        make_species("RHAMPHOLEON_ACUMINATUS", "Rhampholeon acuminatus", "Sharp-snouted Leaf Chameleon", "Leaf Chameleons", ["Africa"], "A distinctive leaf chameleon from the highlands of Tanzania; pointed snout for fossorial lifestyle.", 0),
        make_species("RHAMPHOLEON_MOYERI", "Rhampholeon moyeri", "Moyer's Pygmy Chameleon", "Leaf Chameleons", ["Africa"], "A tiny species from the Udzungwa Mountains of Tanzania; one of the smallest chameleons.", 0, "Moyer"),
    ])
    g = find_genus(ch, "Kinyongia")
    g["children"].extend([
        make_species("KINYONGIA_GYROSA", "Kinyongia gyrosa", "Gyre-horned Chameleon", "African Montane Chameleons", ["Africa"], "A small chameleon from the Kenyan highlands; males possess short curved horns.", 0),
        make_species("KINYONGIA_ULUGURENSIS", "Kinyongia ulugurensis", "Uluguru Two-horned Chameleon", "African Montane Chameleons", ["Africa"], "Endemic to the Uluguru Mountains of Tanzania; two parallel horns in males.", 0),
    ])
    g = find_genus(ch, "Nadzikambia")
    g["children"].extend([
        make_species("NADZIKAMBIA_MLANJENSIS", "Nadzikambia mlanjensis", "Mulanje Chameleon", "African Montane Chameleons", ["Africa"], "Endemic to Mount Mulanje in Malawi; one of the rarest African chameleons.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ARCHAIUS", "Archaius", "Tiger Chameleon", "A monotypic genus of chameleon from the Seychelles; distinctive tiger-like stripes.", "Island Chameleons")
    g["children"].extend([
        make_species("ARCHAIUS_TIGRIS", "Archaius tigris", "Tiger Chameleon", "Island Chameleons", ["Africa"], "Endemic to the Seychelles; striking tiger-stripe pattern; threatened by habitat loss and invasive ants.", 0),
    ])
    g = ensure_genus(ch, "GENUS_BRADYPODION", "Bradypodion", "Dwarf Chameleons", "Small, brightly coloured chameleons of southern Africa; give birth to live young.", "Dwarf Chameleons")
    g["children"].extend([
        make_species("BRADYPODION_PUMILUM", "Bradypodion pumilum", "Cape Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "The most common dwarf chameleon in South Africa; variable colour from green to brown.", 0),
        make_species("BRADYPODION_VENTRALE", "Bradypodion ventrale", "Knysna Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A beautiful species from coastal forests of the Western Cape; bright green with yellow throat.", 0),
        make_species("BRADYPODION_DAMARANUM", "Bradypodion damaranum", "Damara Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A rare Namibian species; restricted to the Damaraland region; the most arid-adapted dwarf chameleon.", 0),
    ])
    g = find_genus(ch, "Chamaeleo")
    g["children"].extend([
        make_species("CHAMAELEO_MONACHUS", "Chamaeleo monachus", "Socotra Chameleon", "Typical Chameleons", ["Asia"], "Endemic to the island of Socotra; a large green chameleon with a curved crest.", 0),
        make_species("CHAMAELEO_NECASI", "Chamaeleo necasi", "Necas's Chameleon", "Typical Chameleons", ["Africa"], "A recently described chameleon from the forests of Tanzania.", 0, "Necas"),
        make_species("CHAMAELEO_SENEGALENSIS", "Chamaeleo senegalensis", "Senegal Chameleon", "Typical Chameleons", ["Africa"], "A widespread West African chameleon; easily identified by the three occipital lobes.", 0),
        make_species("CHAMAELEO_TEMNICKII", "Chamaeleo temnickii", "Temminck's Chameleon", "Typical Chameleons", ["Africa"], "A South African species; dark brown with white bands; named after the Dutch zoologist.", 0, "Temminck"),
    ])
    g = find_genus(ch, "Bradypodion")
    g["children"].extend([
        make_species("BRADYPODION_NEMORALE", "Bradypodion nemorale", "Zululand Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A rare forest chameleon from KwaZulu-Natal; metallic green, electric blue and yellow.", 0),
        make_species("BRADYPODION_MONTANUM", "Bradypodion montanum", "Montane Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A high-altitude species from the Drakensberg; adapted to cool mountain conditions.", 0),
        make_species("BRADYPODION_MELANOCEPHALUM", "Bradypodion melanocephalum", "Black-headed Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A small chameleon from KwaZulu-Natal; black head and bright green body.", 0),
        make_species("BRADYPODION_DAMARANUM", "Bradypodion damaranum", "Knysna Dwarf Chameleon", "Dwarf Chameleons", ["Africa"], "A colourful species from the Knysna forests; vivid green with a pale-blue throat.", 0),
    ])
    g = find_genus(ch, "Calumma")
    g["children"].extend([
        make_species("CALUMMA_TIGRIS", "Calumma tigris", "Tiger Chameleon", "Malagasy Chameleons", ["Africa"], "A spectacular tiger-striped chameleon from northeastern Madagascar.", 0),
        make_species("CALUMMA_GALUS", "Calumma galus", "Galo's Chameleon", "Malagasy Chameleons", ["Africa"], "A recently described chameleon from the Marojejy massif.", 0, "Galo"),
        make_species("CALUMMA_VENOSA", "Calumma venosa", "Veined Chameleon", "Malagasy Chameleons", ["Africa"], "A small species with distinctive blue veins visible through the skin.", 0),
        make_species("CALUMMA_HILLENIUSI", "Calumma hilleniusi", "Hillenius's Chameleon", "Malagasy Chameleons", ["Africa"], "A montane chameleon from the Andringitra massif; green with lateral white bands.", 0, "Hillenius"),
        make_species("CALUMMA_JEZNI", "Calumma jezni", "Jezni's Chameleon", "Malagasy Chameleons", ["Africa"], "A recently described species from the Tsaratanana massif.", 0, "Jezni"),
    ])
    g = find_genus(ch, "Furcifer")
    g["children"].extend([
        make_species("FURCIFER_VIRIDIS", "Furcifer viridis", "Green Malagasy Chameleon", "Malagasy Chameleons", ["Africa"], "A bright green Furcifer from western Madagascar; males have a prominent rostral appendage.", 0),
        make_species("FURCIFER_TIMONI", "Furcifer timoni", "Timon's Chameleon", "Malagasy Chameleons", ["Africa"], "A recently described species from the Montagne d'Ambre region.", 0, "Timon"),
        make_species("FURCIFER_BALTEATUS", "Furcifer balteatus", "Banded Chameleon", "Malagasy Chameleons", ["Africa"], "A medium-sized chameleon from eastern Madagascar; distinct transverse yellow bands.", 0),
    ])
    g = find_genus(ch, "Rhampholeon")
    g["children"].extend([
        make_species("RHAMPHOLEON_TILLBURYI", "Rhampholeon tilburyi", "Tillbury's Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A tiny pygmy chameleon from the Eastern Arc Mountains of Tanzania.", 0, "Tillbury"),
        make_species("RHAMPHOLEON_VIRIDIS", "Rhampholeon viridis", "Green Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A small bright green species from the Usambara Mountains.", 0),
        make_species("RHAMPHOLEON_MARBAREZI", "Rhampholeon marbarezi", "Marbarez Pygmy Chameleon", "Pygmy Chameleons", ["Africa"], "A recently described pygmy chameleon from Mozambique; one of the smallest chameleons.", 0),
    ])
    g = ensure_genus(ch, "GENUS_BROOKESIA", "Brookesia", "Leaf Chameleons", "The smallest chameleons in the world; tiny leaf-litter dwellers endemic to Madagascar.", "Dwarf Chameleons")
    g["children"].extend([
        make_species("BROOKESIA_MINIMA", "Brookesia minima", "Tiny Leaf Chameleon", "Dwarf Chameleons", ["Africa"], "One of the world's smallest reptiles; adults reach only 3 cm total length.", 0),
        make_species("BROOKESIA_MICRA", "Brookesia micra", "Noisy Leaf Chameleon", "Dwarf Chameleons", ["Africa"], "A recently discovered minute chameleon from Nosy Hara, Madagascar.", 0),
        make_species("BROOKESIA_PERARMATUS", "Brookesia perarmatus", "Spiny Leaf Chameleon", "Dwarf Chameleons", ["Africa"], "A well-armored leaf chameleon with prominent spines above the eyes.", 0),
        make_species("BROOKESIA_BRUNOI", "Brookesia brunoi", "Bruno's Leaf Chameleon", "Dwarf Chameleons", ["Africa"], "A recently described species from the Tsingy de Bemaraha in Madagascar.", 0, "Bruno"),
    ])

    return data
ENRICHERS["chamaeleonidae"] = enrich_chamaeleonidae

# ---------------------------------------------------------------------------
# 15. fringillidae
# ---------------------------------------------------------------------------
def enrich_fringillidae(data):
    ch = data["children"]
    g = find_genus(ch, "Fringilla")
    g["children"].extend([
        make_species("FRINGILLA_POLATZEKI", "Fringilla polatzeki", "Gran Canaria Blue Chaffinch", "True Finches", ["Europe"], "A recently split species endemic to Gran Canaria; critically endangered with fewer than 300 individuals.", 0, "Polatzek"),
        make_species("FRINGILLA_ALPICOLLA", "Fringilla alpicolla", "Alpine Chaffinch", "True Finches", ["Europe"], "A genetically distinct chaffinch population from the high Alps; proposed as a separate species.", 0),
    ])
    g = find_genus(ch, "Carduelis")
    g["children"].extend([
        make_species("CARDUELIS_CARDUELIS_CANICEPS", "Carduelis carduelis caniceps", "Asian Goldfinch", "True Finches", ["Asia"], "The eastern subspecies of the goldfinch; grey head replaces the European red-and-white pattern.", 0),
    ])
    g = find_genus(ch, "Spinus")
    g["children"].extend([
        make_species("SPINUS_BARBATUS", "Spinus barbatus", "Black-chinned Siskin", "True Finches", ["South America"], "A siskin from the southern Andes; black chin contrasts with yellow body.", 0),
        make_species("SPINUS_CRASSIROSTRIS", "Spinus crassirostris", "Thick-billed Siskin", "True Finches", ["South America"], "Found in the high Andes; unusually heavy bill for seed-cracking in harsh puna habitats.", 0),
        make_species("SPINUS_OLIVACEUS", "Spinus olivaceus", "Olivaceous Siskin", "True Finches", ["South America"], "A dull olive-green siskin from the eastern Andes of Peru and Bolivia.", 0),
    ])
    g = find_genus(ch, "Chloris")
    g["children"].extend([
        make_species("CHLORIS_KITTLITZI", "Chloris kittlitzi", "Bonin Greenfinch", "True Finches", ["Asia"], "An endangered greenfinch from the Ogasawara Islands of Japan; recently recognised as distinct.", 0, "Kittlitz"),
    ])
    g = find_genus(ch, "Pyrrhula")
    g["children"].extend([
        make_species("PYRRHULA_LEUCOGENYS", "Pyrrhula leucogenys", "White-cheeked Bullfinch", "True Finches", ["Asia"], "A Philippine bullfinch; white cheeks and grey-pink body; inhabits montane forests.", 0),
        make_species("PYRRHULA_GRISEIVENTRIS", "Pyrrhula griseiventris", "Grey-bellied Bullfinch", "True Finches", ["Asia"], "Found from the Himalayas to Southeast Asia; pale grey belly distinguishes it from P. pyrrhula.", 0),
    ])
    g = find_genus(ch, "Loxia")
    g["children"].extend([
        make_species("LOXIA_PATAGONICA", "Loxia patagonica", "Patagonian Crossbill", "True Finches", ["South America"], "A South American crossbill from the Andes of Chile and Argentina; feeds on Araucaria seeds.", 0),
        make_species("LOXIA_ANCORA", "Loxia ancora", "Hispaniolan Crossbill", "True Finches", ["North America"], "Endemic to Hispaniola; the only Caribbean crossbill; critically endangered by deforestation.", 0),
    ])
    g = find_genus(ch, "Serinus")
    g["children"].extend([
        make_species("SERINUS_ALARIO", "Serinus alario", "Black-headed Canary", "True Finches", ["Africa"], "A striking black-and-white canary from southern Africa; the male has a black head and throat.", 0),
        make_species("SERINUS_LEUCOPYGIUS", "Serinus leucopygius", "White-rumped Seedeater", "True Finches", ["Africa"], "A small seedeater from the Sahel; white rump visible in flight.", 0),
    ])
    g = find_genus(ch, "Crithagra")
    g["children"].extend([
        make_species("CRITHAGRA_ATROGULARIS", "Crithagra atrogularis", "Black-throated Canary", "True Finches", ["Africa"], "A widespread southern African canary with a black throat patch.", 0),
        make_species("CRITHAGRA_REICHELARUM", "Crithagra reichelarum", "Reichenow's Seedeater", "True Finches", ["Africa"], "A West African canary; named after the ornithologist Anton Reichenow.", 0, "Anton Reichenow"),
        make_species("CRITHAGRA_SULPHURATA", "Crithagra sulphurata", "Brimstone Canary", "True Finches", ["Africa"], "A bright yellow canary from eastern and southern Africa; sulphur-yellow underparts.", 0),
    ])
    g = find_genus(ch, "Haemorhous")
    g["children"].extend([
        make_species("HAEMORHOUS_ANEUS", "Haemorhous aneus", "Yellow Grosbeak", "True Finches", ["North America"], "A colourful finch of western Mexican forests; the male is bright yellow with black wings.", 0),
    ])
    g = find_genus(ch, "Carpodacus")
    g["children"].extend([
        make_species("CARPODACUS_WALTONI", "Carpodacus waltoni", "Walton's Rosefinch", "True Finches", ["Asia"], "A Tibetan rosefinch; named after the British ornithologist.", 0, "Walton"),
        make_species("CARPODACUS_VERREAUXII", "Carpodacus verreauxii", "Verreaux's Rosefinch", "True Finches", ["Asia"], "A Himalayan rosefinch from the western part of the range; rich crimson male plumage.", 0, "Verreaux"),
    ])
    g = find_genus(ch, "Leucosticte")
    g["children"].extend([
        make_species("LEUCOSTICTE_BRANDTI", "Leucosticte brandti", "Brandt's Mountain Finch", "True Finches", ["Asia"], "A high-altitude finch of Central Asian mountains; grey-brown with pink wing patches.", 0, "Brandt"),
        make_species("LEUCOSTICTE_NEMORICOLA", "Leucosticte nemoricola", "Hodgson's Mountain Finch", "True Finches", ["Asia"], "Widespread in the Himalayas; streaked brown finch of alpine meadows above treeline.", 0),
    ])
    g = find_genus(ch, "Mycerobas")
    g["children"].extend([
        make_species("MYCEROBAS_ICTERIOIDES", "Mycerobas icterioides", "Black-and-yellow Grosbeak", "True Finches", ["Asia"], "A striking black and yellow grosbeak of Himalayan forests; massive bill for cracking hard seeds.", 0),
    ])
    g = find_genus(ch, "Eophona")
    g["children"].extend([
        make_species("EOPHONA_MIGRATORIA", "Eophona migratoria", "Chinese Grosbeak", "True Finches", ["Asia"], "A migratory grosbeak breeding in northeast Asia; yellow and black plumage with pale bill.", 0),
    ])
    g = find_genus(ch, "Himatione")
    g["children"].extend([
        make_species("HIMATIONE_FRAITHII", "Himatione fraithii", "Laysan Honeycreeper", "True Finches", ["Oceania"], "An extinct Hawaiian honeycreeper from Laysan; vivid crimson red with white eye-ring.", 0, "Fraith"),
    ])
    g = find_genus(ch, "Drepanis")
    g["children"].extend([
        make_species("DREPANIS_PACIFICA", "Drepanis pacifica", "Hawaii Mamo", "True Finches", ["Oceania"], "An extinct honeycreeper with a long curved bill; its yellow feathers were used for Hawaiian royal cloaks.", 0),
    ])
    g = ensure_genus(ch, "GENUS_LOXOPS", "Loxops", "Hawaiian Creepers", "Small Hawaiian honeycreepers with a unique bill shape where the tips cross slightly.", "True Finches")
    g["children"].extend([
        make_species("LOXOPS_COCCINEUS", "Loxops coccineus", "Akekee", "True Finches", ["Oceania"], "A small Hawaiian honeycreeper with a unique crossed bill tip for prying open leaf buds.", 0),
        make_species("LOXOPS_CAERULEIROSTRIS", "Loxops caeruleirostris", "Akikiki", "True Finches", ["Oceania"], "Critically endangered Hawaiian honeycreeper from Kauai; blue-grey bill and pale plumage.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HEMIGNATHUS", "Hemignathus", "Long-billed Honeycreepers", "Hawaiian honeycreepers with extremely long curved bills for extracting nectar from lobelioid flowers.", "True Finches")
    g["children"].extend([
        make_species("HEMIGNATHUS_WILSONI", "Hemignathus wilsoni", "Akiapolaau", "True Finches", ["Oceania"], "A remarkable woodpecker-like honeycreeper; uses its long lower bill to probe for insect larvae.", 0, "Wilson"),
        make_species("HEMIGNATHUS_MUNROI", "Hemignathus munroi", "Hawaii Amakihi", "True Finches", ["Oceania"], "A small generalist honeycreeper; one of the most adaptable Hawaiian finches.", 0, "Munro"),
    ])
    g = find_genus(ch, "Fringilla")
    g["children"].extend([
        make_species("FRINGILLA_POLATZEKI", "Fringilla polatzeki", "Gran Canaria Blue Chaffinch", "Chaffinches", ["Europe"], "Endemic to Gran Canaria; vivid blue male plumage; critically endangered.", 0, "Polatzek"),
        make_species("FRINGILLA_TEYDEA", "Fringilla teydea", "Tenerife Blue Chaffinch", "Chaffinches", ["Europe"], "A large blue chaffinch native to Tenerife's Canary pine forests.", 0),
        make_species("FRINGILLA_MONTALBETTI", "Fringilla montalbetti", "Sardinian Chaffinch", "Chaffinches", ["Europe"], "A recently split species from Corsica and Sardinia; genetically distinct.", 0),
    ])
    g = find_genus(ch, "Carduelis")
    g["children"].extend([
        make_species("CARDUELIS_LAWRENCEI", "Carduelis lawrencei", "Lawrence's Goldfinch", "Goldfinches", ["North America"], "A grey-and-yellow goldfinch of California and Baja California; named after Lawrence.", 0, "Lawrence"),
        make_species("CARDUELIS_PSALTRIA", "Carduelis psaltria", "Lesser Goldfinch", "Goldfinches", ["North America"], "A small yellow-and-black finch of the western USA and Mexico; greenish back.", 0),
        make_species("CARDUELIS_NOTATA", "Carduelis notata", "Black-headed Siskin", "Siskins", ["South America"], "A small siskin from the Andes; black head and bright yellow body.", 0),
        make_species("CARDUELIS_DOMINICENSIS", "Carduelis dominicensis", "Hispaniolan Goldfinch", "Goldfinches", ["North America"], "A Caribbean goldfinch restricted to the island of Hispaniola.", 0),
    ])
    g = find_genus(ch, "Serinus")
    g["children"].extend([
        make_species("SERINUS_LEUCOPYGIUS", "Serinus leucopygius", "White-rumped Seedeater", "Canaries", ["Africa"], "A small grey seedeater from the Sahel zone of Africa.", 0),
        make_species("SERINUS_REICHARDI", "Serinus reichardi", "Reichard's Seedeater", "Canaries", ["Africa"], "A seedeater from the highlands of Ethiopia and Eritrea.", 0, "Reichard"),
        make_species("SERINUS_FLAVICOLA", "Serinus flavicola", "Yellow-bellied Seedeater", "Canaries", ["Africa"], "A bright yellow-bellied species from East African savannas.", 0),
        make_species("SERINUS_ALARIO", "Serinus alario", "Black-headed Canary", "Canaries", ["Africa"], "A striking black-and-white canary of South Africa; male has a jet-black head.", 0),
    ])
    g = find_genus(ch, "Spinus")
    g["children"].extend([
        make_species("SPINUS_CRASSIROSTRIS", "Spinus crassirostris", "Thick-billed Siskin", "Siskins", ["South America"], "A high Andean siskin with a distinctive thick conical bill.", 0),
        make_species("SPINUS_XANTHOPHTHALMUS", "Spinus xanthophthalmus", "Yellow-eyed Siskin", "Siskins", ["South America"], "A striking black-and-yellow siskin from the Peruvian Andes.", 0),
        make_species("SPINUS_ATRICEPS", "Spinus atriceps", "Black-capped Siskin", "Siskins", ["South America"], "A small siskin from the mountains of Venezuela; black cap and green body.", 0),
        make_species("SPINUS_BARBATUS", "Spinus barbatus", "Black-chinned Siskin", "Siskins", ["South America"], "A Patagonian siskin with a black chin patch.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SPIZA", "Spiza", "Dickcissel", "A grassland bird of the central USA; the sole member of its genus; winters in large flocks in South America.", "American Grass Finches")
    g["children"].extend([
        make_species("SPIZA_AMERICANA", "Spiza americana", "Dickcissel", "American Grass Finches", ["North America", "South America"], "A common grassland bird of the central USA; brilliant yellow breast and black V.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CHLORIS", "Chloris", "Greenfinches", "Robust greenish finches of Eurasia and Africa; thick conical bills for cracking seeds.", "Greenfinches")
    g["children"].extend([
        make_species("CHLORIS_SINICA", "Chloris sinica", "Oriental Greenfinch", "Greenfinches", ["Asia"], "An olive-green finch widespread in East Asia; yellow wing and tail edges.", 0),
        make_species("CHLORIS_AMBIANUS", "Chloris ambianus", "Black-chinned Greenfinch", "Greenfinches", ["Asia"], "A greenfinch from the Philippines; distinctive black chin on the male.", 0),
        make_species("CHLORIS_MONGUILLOTI", "Chloris monguilloti", "Vietnamese Greenfinch", "Greenfinches", ["Asia"], "A small greenfinch endemic to southern Vietnam.", 0, "Monguillot"),
    ])
    g = ensure_genus(ch, "GENUS_LOXIA", "Loxia", "Crossbills", "Finches with distinctive crossed mandibles; specialized to extract seeds from conifer cones.", "Crossbills")
    g["children"].extend([
        make_species("LOXIA_LEUCOPTERA", "Loxia leucoptera", "White-winged Crossbill", "Crossbills", ["North America", "Europe", "Asia"], "A Holarctic crossbill; two bold white wing bars; feeds on larch and spruce cones.", 0),
        make_species("LOXIA_SCOTICA", "Loxia scotica", "Scottish Crossbill", "Crossbills", ["Europe"], "The UK's only endemic bird species; restricted to the pine forests of the Scottish Highlands.", 0),
        make_species("LOXIA_PYTYOPSITTACUS", "Loxia pytyopsittacus", "Parrot Crossbill", "Crossbills", ["Europe"], "A large heavy-billed crossbill of northern European pine forests.", 0),
    ])

    return data
ENRICHERS["fringillidae"] = enrich_fringillidae


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/enrich_lap2.py <family_slug>")
        print(f"Available: {', '.join(sorted(ENRICHERS.keys()))}")
        sys.exit(1)

    slug = sys.argv[1]
    if slug not in ENRICHERS:
        print(f"Error: unknown family slug '{slug}'")
        print(f"Available: {', '.join(sorted(ENRICHERS.keys()))}")
        sys.exit(1)

    queue = load_json(QUEUE_PATH)
    entry = None
    for e in queue:
        if e.get("appSlug") == slug:
            entry = e
            break

    if entry is None:
        print(f"Error: '{slug}' not found in enrichment-queue.json")
        sys.exit(1)

    data_file = os.path.join(ROOT, entry["dataFile"])
    if not os.path.exists(data_file):
        print(f"Error: data file not found: {data_file}")
        sys.exit(1)

    print(f"Processing: {entry['family']} ({entry['dataFile']})")
    print(f"  target: +{entry['targetAdd']} species")

    data = load_json(data_file)
    before = count_species(data)
    print(f"  species before: {before}")

    enricher = ENRICHERS[slug]
    data = enricher(data)

    after = count_species(data)
    added = after - before
    print(f"  species after: {after} (+{added})")

    save_json(data_file, data)
    print(f"  saved: {data_file}")
    print("Done.")


if __name__ == "__main__":
    main()
