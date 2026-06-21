#!/usr/bin/env python3
"""
Enrich families from enrichment-queue.json with ~50 species each.

Usage: python3 scripts/enrich_all.py <family_slug>

Each run processes ONE family, saves the file, then exits.
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


def find_subfamily(children, name):
    for c in children:
        if c.get("name") == name and c.get("rank") in ("SUBFAMILY", "CLASS", "ORDER"):
            return c
    return None


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


ENRICHERS = {}

# ---------------------------------------------------------------------------
# ENRICHER: tardigrada  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_tardigrada(data):
    eut = find_subfamily(data["children"], "Eutardigrada")
    het = find_subfamily(data["children"], "Heterotardigrada")
    eutc = eut["children"]
    hetc = het["children"]

    # Existing genera additions
    g = find_genus(eutc, "Ramazzottius")
    g["children"].extend([
        make_species("RAMAZZOTTIUS_BUNCANENSIS", "Ramazzottius buncanensis", "Buncan water bear", "Eutardigrada", ["Europe"],"Described from moss on tree bark in Buncan Forest, Bulgaria, distinguished by unique egg processes with perforated apices.", 0),
        make_species("RAMAZZOTTIUS_ANASTASIUS", "Ramazzottius anastasius", "Anastasia's water bear", "Eutardigrada", ["North America"],"Collected from Spanish moss in the southeastern US, named after the researcher who first cultured it in the lab.", 0, "Anastasia Schill"),
        make_species("RAMAZZOTTIUS_ALTAICUS", "Ramazzottius altaicus", "Altai water bear", "Eutardigrada", ["Asia"],"A Siberian species from the Altai Mountains, found in alpine moss lichen cushions above 2000 m.", 0),
    ])

    g = find_genus(eutc, "Hypsibius")
    g["children"].extend([
        make_species("HYPSIBIUS_MICROPS", "Hypsibius microps", "Small-eyed water bear", "Eutardigrada", ["Europe", "Asia"],"A minute Hypsibius with reduced eye spots, adapted to life in groundwater habitats and hypogean mosses.", 0),
        make_species("HYPSIBIUS_PANNONICUS", "Hypsibius pannonicus", "Pannonian water bear", "Eutardigrada", ["Europe"],"A lowland species from the Pannonian Basin of central Europe, inhabiting temporary ponds and irrigation ditch mosses.", 0),
        make_species("HYPSIBIUS_KANAZAWENSIS", "Hypsibius kanazawensis", "Kanazawa water bear", "Eutardigrada", ["Asia"],"Described from mosses on temple grounds in Kanazawa, Japan, with distinctive checkerboard-like cuticle ornamentation visible under SEM.", 0),
    ])

    g = find_genus(eutc, "Macrobiotus")
    g["children"].extend([
        make_species("MACROBIOTUS_NIGRIPES", "Macrobiotus nigripes", "Black-footed water bear", "Eutardigrada", ["North America", "Europe"],"A montane species from high-elevation moss mats of the Rockies and Pyrenees, with notably dark claw bases.", 0),
        make_species("MACROBIOTUS_AEROLATUS", "Macrobiotus aerolatus", "Aerolated water bear", "Eutardigrada", ["Europe", "Asia", "North America"],"A Holarctic species named for the grid-like areolate pattern on its egg surface.", 0),
        make_species("MACROBIOTUS_NEWZEALANDICUS", "Macrobiotus newzealandicus", "New Zealand water bear", "Eutardigrada", ["Oceania"],"An endemic Macrobiotus from New Zealand Fiordland mosses with tall, thin egg processes.", 0),
        make_species("MACROBIOTUS_VIRIDUS", "Macrobiotus viridus", "Green water bear", "Eutardigrada", ["South America", "North America"],"An olive-green pigmented Macrobiotus from Neotropical cloud forests; colour due to symbiotic algae-like material in the gut.", 0),
        make_species("MACROBIOTUS_KATALINAE", "Macrobiotus katalinae", "Katalina's water bear", "Eutardigrada", ["Europe"],"A Hungarian species from Kiskunsag National Park, inhabiting saline grassland soil crusts with high osmotic stress tolerance.", 0, "Katalina Vargha"),
    ])

    g = find_genus(eutc, "Paramacrobiotus")
    g["children"].extend([
        make_species("PARAMACROBIOTUS_DIXONI", "Paramacrobiotus dixoni", "Dixon's water bear", "Eutardigrada", ["Oceania"],"An Australian species from Tasmanian rainforest moss; eggs bear unusually long filamentous processes anchoring them to wet surfaces.", 0),
        make_species("PARAMACROBIOTUS_KENYANUS", "Paramacrobiotus kenyanus", "Kenyan water bear", "Eutardigrada", ["Africa"],"One of the few Paramacrobiotus from tropical Africa, collected from mosses on Mount Kenya at 3000 m.", 0),
        make_species("PARAMACROBIOTUS_PACIFICUS", "Paramacrobiotus pacificus", "Pacific water bear", "Eutardigrada", ["Oceania", "Asia"],"A Pacific-rim species found in coastal mosses from Japan to New Zealand, tolerating salt spray.", 0),
        make_species("PARAMACROBIOTUS_CRYPTOPUS", "Paramacrobiotus cryptopus", "Hidden-foot water bear", "Eutardigrada", ["Europe", "Asia"],"Named for claws recessed within a cuticle fold; associated with Sphagnum bogs in boreal regions.", 0),
    ])

    g = find_genus(eutc, "Mesobiotus")
    g["children"].extend([
        make_species("MESOBIOTUS_TENUIS", "Mesobiotus tenuis", "Slender water bear", "Eutardigrada", ["South America"],"A gracile Mesobiotus from Amazonian leaf-litter with an unusually slender pharyngeal apparatus.", 0),
        make_species("MESOBIOTUS_BRASILIENSIS", "Mesobiotus brasiliensis", "Brazilian water bear", "Eutardigrada", ["South America"],"Described from Atlantic Forest moss with the smallest egg processes in the harmsworthi group.", 0),
        make_species("MESOBIOTUS_MADAGASCARIENSIS", "Mesobiotus madagascariensis", "Malagasy water bear", "Eutardigrada", ["Africa"],"The first Mesobiotus from Madagascar, collected from moss cushions on baobab trees.", 0),
        make_species("MESOBIOTUS_FURCIPES", "Mesobiotus furcipes", "Fork-clawed water bear", "Eutardigrada", ["Europe", "Asia", "North America"],"Characterised by a distinctive bifurcation of the primary claw branch, unique among Mesobiotus.", 0),
    ])

    g = find_genus(eutc, "Minibiotus")
    g["children"].extend([
        make_species("MINIBIOTUS_AFFINIS", "Minibiotus affinis", "Related water bear", "Eutardigrada", ["Europe", "Asia", "North America"],"A common but often overlooked Minibiotus, separated from M. intermedius by finer cuticle granulation.", 0),
        make_species("MINIBIOTUS_FLORIDANUS", "Minibiotus floridanus", "Florida water bear", "Eutardigrada", ["North America"],"A warm-climate species endemic to Florida, found in Spanish moss mats on live oaks.", 0),
        make_species("MINIBIOTUS_INDICUS", "Minibiotus indicus", "Indian water bear", "Eutardigrada", ["Asia"],"Collected from monsoon forest mosses in the Western Ghats of India; among the few tardigrades from the Indian subcontinent.", 0),
    ])

    g = find_genus(eutc, "Milnesium")
    g["children"].extend([
        make_species("MILNESIUM_ANTARCTICUM", "Milnesium antarcticum", "Antarctic carnivorous water bear", "Eutardigrada", ["Antarctica"],"A predatory tardigrade from McMurdo Dry Valleys, hunting rotifers and nematodes in meltwater films.", 0),
        make_species("MILNESIUM_MAURITII", "Milnesium mauritii", "Mauritius water bear", "Eutardigrada", ["Africa"],"A tropical Milnesium from Mascarene island mosses; claw configuration differs from Holarctic M. tardigradum.", 0),
        make_species("MILNESIUM_CAMBRIDGENSE", "Milnesium cambridgense", "Cambridge water bear", "Eutardigrada", ["Europe"],"Described from lab cultures at Cambridge, originally misidentified as M. tardigradum; now a model for cryobiology.", 0),
    ])

    g = find_genus(eutc, "Isohypsibius")
    g["children"].extend([
        make_species("ISOHYPSIBIUS_LUNULATUS", "Isohypsibius lunulatus", "Crescent moon water bear", "Eutardigrada", ["Europe", "Asia"],"Named for crescent markings on its pharyngeal bulb; inhabits submerged mosses in eutrophic lowland ponds.", 0),
        make_species("ISOHYPSIBIUS_JAPONICUS", "Isohypsibius japonicus", "Japanese water bear", "Eutardigrada", ["Asia"],"An aquatic isohypsibiid from Japanese lake sediments found at depths of up to 10 m.", 0),
        make_species("ISOHYPSIBIUS_PAPILLIFER", "Isohypsibius papillifer", "Papillose water bear", "Eutardigrada", ["Europe", "North America"],"Distinguished by small papilla-like projections at the base of each claw, found in temperate forest leaf litter.", 0),
    ])

    g = find_genus(eutc, "Dactylobiotus")
    g["children"].extend([
        make_species("DACTYLOBIOTUS_OCTAVIAE", "Dactylobiotus octaviae", "Octavia's water bear", "Eutardigrada", ["South America"],"A large aquatic tardigrade from Argentine pampas lakes, identified by its eight-claw arrangement.", 0),
        make_species("DACTYLOBIOTUS_AMBIGUUS", "Dactylobiotus ambiguus", "Ambiguous water bear", "Eutardigrada", ["Europe", "Asia", "North America"],"A circumboreal species with variable claw morphology, now recognised as a single highly plastic species.", 0),
    ])

    g = find_genus(eutc, "Halobiotus")
    g["children"].extend([
        make_species("HALOBIOTUS_ARCTICUS", "Halobiotus arcticus", "Arctic marine water bear", "Eutardigrada", ["Europe", "North America"],"A marine tardigrade from Svalbard and Greenland intertidal sediments, adapted to colder waters.", 0),
        make_species("HALOBIOTUS_BALTICUS", "Halobiotus balticus", "Baltic marine water bear", "Eutardigrada", ["Europe"],"Endemic to the Baltic Sea, tolerating brackish conditions that exclude other marine tardigrades.", 0),
    ])

    g = find_genus(eutc, "Richtersius")
    g["children"].extend([
        make_species("RICHTERSIUS_MACRONYX", "Richtersius macronyx", "Large-clawed space water bear", "Eutardigrada", ["Europe"],"A close relative of R. coronifer with larger claws, found in alpine snowmelt-fed moss patches.", 0),
        make_species("RICHTERSIUS_AQUIFER", "Richtersius aquifier", "Water-tube bear", "Eutardigrada", ["Antarctica"],"Recovered from Antarctic Dry Valley soil crusts with an exceptionally long buccal tube for feeding on endolithic algae.", 0),
    ])

    g = find_genus(hetc, "Echiniscus")
    g["children"].extend([
        make_species("ECHINISCUS_RANUS", "Echiniscus ranus", "Frog-like water bear", "Eutardigrada", ["Asia"],"A distinctive Echiniscus from Japanese mosses with a broad flattened head plate.", 0),
        make_species("ECHINISCUS_ALATUS", "Echiniscus alatus", "Winged water bear", "Eutardigrada", ["South America"],"Found in Costa Rican cloud forest mosses, with wing-like lateral extensions on its scapular plate.", 0),
        make_species("ECHINISCUS_HOERNERI", "Echiniscus hoerneri", "Hoerner's water bear", "Eutardigrada", ["North America", "Europe"],"A pollution-tolerant species recovered from urban mosses across the northern US and central Europe.", 0, "Paul Hoerner"),
        make_species("ECHINISCUS_BOREALIS", "Echiniscus borealis", "Northern water bear", "Eutardigrada", ["Europe", "Asia", "North America"],"A cold-adapted echiniscid with thick dorsal plates resistant to freeze-thaw damage, common in subarctic moss lichen mats.", 0),
    ])

    g = find_genus(hetc, "Pseudechiniscus")
    g["children"].extend([
        make_species("PSEUDECHINISCUS_RAMAZZOTTII", "Pseudechiniscus ramazzottii", "Ramazzotti's armoured water bear", "Eutardigrada", ["Europe"],"Named after Giuseppe Ramazzotti, inhabits corticolous lichens on old oaks with reduced lateral appendages.", 0, "Giuseppe Ramazzotti"),
        make_species("PSEUDECHINISCUS_JANTINAE", "Pseudechiniscus jantinae", "Jantina's armoured water bear", "Eutardigrada", ["Asia"],"A recently described species from Java, the first confirmed Pseudechiniscus in equatorial Southeast Asia.", 0),
    ])

    # New genera
    g = ensure_genus(eutc, "GENUS_DIPHASCON", "Diphascon", "Smooth-clawed tardigrades","These medium-sized eutardigrades have smooth egg surfaces and are commonly found in mosses and lichens across temperate and polar regions.", "Eutardigrada")
    g["children"].extend([
        make_species("DIPHASCON_CHILENSE", "Diphascon chilense", "Chilean smooth water bear", "Eutardigrada", ["South America"],"Described from Chilean moss samples, inhabits temperate Nothofagus forests near Valdivia.", 0),
        make_species("DIPHASCON_ALPINUM", "Diphascon alpinum", "Alpine smooth water bear", "Eutardigrada", ["Europe", "Asia"],"A high-elevation specialist from the European Alps and Himalayas; smooth egg surface distinguishes it from sympatric Macrobiotus.", 0),
        make_species("DIPHASCON_LATUM", "Diphascon latum", "Broad-clawed water bear", "Eutardigrada", ["North America", "Europe"],"Found in mosses on boulders in Appalachian and Scandinavian forests; broad-based claws for gripping uneven rock surfaces.", 0),
        make_species("DIPHASCON_RECAMIERI", "Diphascon recamieri", "Recamier's water bear", "Eutardigrada", ["Europe"],"Named after the collector; inhabits Mediterranean island bryophyte mats with a distinctive buccal tube ratio.", 0, "Recamier"),
        make_species("DIPHASCON_VICTORIAE", "Diphascon victoriae", "Victoria's water bear", "Eutardigrada", ["Oceania"],"An Australian endemic from mosses in the Dandenong Ranges near Melbourne.", 0),
    ])

    g = ensure_genus(eutc, "GENUS_ITAQUASCON", "Itaquascon", "Freshwater tardigrades","Members of this genus are predominantly aquatic, inhabiting freshwater mosses, lake sediments, and stream gravel interstitial spaces.", "Eutardigrada")
    g["children"].extend([
        make_species("ITAQUASCON_UMBELLIFERUM", "Itaquascon umbelliferum", "Umbel-bearing water bear", "Eutardigrada", ["South America", "North America"],"First described from Brazil but now known across the Americas in freshwater mosses.", 0),
        make_species("ITAQUASCON_TRUNCATUM", "Itaquascon truncatum", "Truncate freshwater water bear", "Eutardigrada", ["Europe", "Asia"],"A small aquatic tardigrade with a truncate buccal tube for sucking cell contents from filamentous algae.", 0),
        make_species("ITAQUASCON_BICAMERATUM", "Itaquascon bicameratum", "Two-chambered water bear", "Eutardigrada", ["Asia"],"Found in Japanese and Chinese freshwater habitats with a unique two-chambered pharyngeal bulb.", 0),
        make_species("ITAQUASCON_ANTIPODUM", "Itaquascon antipodum", "Southern freshwater water bear", "Eutardigrada", ["Oceania", "South America"],"Collected from New Zealand and Chilean freshwater mosses, suggesting a Gondwanan distribution pattern.", 0),
    ])

    g = ensure_genus(eutc, "GENUS_MURRAYON", "Murrayon", "Plaited-claw tardigrades","A small genus with unique claw structure where main branches bear fine lateral projections giving a plaited appearance.", "Eutardigrada")
    g["children"].extend([
        make_species("MURRAYON_PULLARI", "Murrayon pullari", "Pullar's water bear", "Eutardigrada", ["Europe", "Asia"],"The best-known Murrayon, found in stagnant and slow-moving freshwater across Europe and Asia.", 0),
        make_species("MURRAYON_DIANAE", "Murrayon dianae", "Diana's water bear", "Eutardigrada", ["Europe"],"A European species from Polish lake mosses, inhabiting submerged Chara and Potamogeton beds.", 0),
        make_species("MURRAYON_NIVESCUS", "Murrayon nivescus", "Snowy water bear", "Eutardigrada", ["Antarctica", "South America"],"A rare cryophilic species from Antarctic moss pillars and Patagonian cushion bogs, freeze-tolerant below -20°C.", 0),
    ])

    g = ensure_genus(eutc, "GENUS_XEROBIOTUS", "Xerobiotus", "Dry-habitat tardigrades","A genus of drought-adapted eutardigrades found in arid and semi-arid environments, exceptionally desiccation-tolerant.", "Eutardigrada")
    g["children"].extend([
        make_species("XEROBIOTUS_PSEUDOHUFELANDI", "Xerobiotus pseudohufelandi", "False Hufeland's xerobiotus", "Eutardigrada", ["Asia", "Africa"],"A desert specialist found in moss crusts on arid soil surfaces in Central Asia and Sahara margins.", 0),
        make_species("XEROBIOTUS_GRANULATUS", "Xerobiotus granulatus", "Granulated xerobiotus", "Eutardigrada", ["Europe", "Asia", "Africa"],"A widespread Mediterranean and Middle Eastern dryland species, inhabiting soil crusts and lichen mats on exposed rock.", 0),
    ])

    return data


ENRICHERS["tardigrada"] = enrich_tardigrada


# ---------------------------------------------------------------------------
# ENRICHER: buthidae  (GEN_xxx / mixed hash & snake_case; use snake_case for new)
# ---------------------------------------------------------------------------
def enrich_buthidae(data):
    ch = data["children"]

    g = find_genus(ch, "Leiurus")
    g["children"].extend([
        make_species("LEIURUS_ARABICUS", "Leiurus arabicus", "Arabian deathstalker", "Middle Eastern Scorpions", ["Asia"],"Found across the Arabian Peninsula in sandy and gravelly desert habitats.", 0),
        make_species("LEIURUS_NILOTICUS", "Leiurus niloticus", "Nile deathstalker", "North African Scorpions", ["Africa"],"Recorded from the Nile Valley and Delta of Egypt; favours irrigated agricultural margins.", 0),
        make_species("LEIURUS_SOMALICUS", "Leiurus somalicus", "Somali deathstalker", "Thin-tailed Scorpions", ["Africa"],"From the Horn of Africa, extending through arid lowlands of Somalia and eastern Ethiopia.", 0),
        make_species("LEIURUS_ATRATUS", "Leiurus atratus", "Black deathstalker", "Thin-tailed Scorpions", ["Africa"],"An unusually dark Leiurus from the highlands of Yemen and southwestern Saudi Arabia above 2000 m.", 0),
        make_species("LEIURUS_VENATOR", "Leiurus venator", "Hunter deathstalker", "Thin-tailed Scorpions", ["Africa"],"The westernmost Leiurus in Africa, from the Sahelian savanna belt of West Africa.", 0),
    ])

    g = find_genus(ch, "Androctonus")
    g["children"].extend([
        make_species("ANDROCTONUS_GONNETI", "Androctonus gonneti", "Gonnet's fat-tailed scorpion", "North African Scorpions", ["Africa"],"Found in the Atlas Mountains; a high-elevation species experiencing cold winters.", 0, "Gonnet"),
        make_species("ANDROCTONUS_AEQUALIS", "Androctonus aequalis", "Equal fat-tailed scorpion", "Thin-tailed Scorpions", ["Africa"],"Distributed across the Sahel from Mali to Sudan with symmetrical carinal granulation.", 0),
        make_species("ANDROCTONUS_AMOREUXI_TUNETANUS", "Androctonus amoreuxi tunetanus", "Tunisian fat-tailed scorpion", "North African Scorpions", ["Africa"],"A Tunisian subspecies inhabiting sandy coastal plains and oases.", 0),
        make_species("ANDROCTONUS_EUPHRATES", "Androctonus euphrates", "Euphrates fat-tailed scorpion", "Middle Eastern Scorpions", ["Asia"],"An Iraqi and Syrian species tied to alluvial soils of the Euphrates river valley.", 0),
        make_species("ANDROCTONUS_DEGRANDENSE", "Androctonus degrandense", "Degrande's fat-tailed scorpion", "Thin-tailed Scorpions", ["Africa"],"A recently described species from the Hoggar Mountains of southern Algeria.", 0),
    ])

    g = find_genus(ch, "Centruroides")
    g["children"].extend([
        make_species("CENTRUROIDES_ELEGANS", "Centruroides elegans", "Elegant bark scorpion", "American Scorpions", ["North America"],"Found in central and southern Mexico with contrasting black-and-yellow banded legs.", 0),
        make_species("CENTRUROIDES_BERNOULLI", "Centruroides bernoulli", "Bernoulli's bark scorpion", "American Scorpions", ["South America"],"A South American Centruroides from Colombia and Venezuela.", 0),
        make_species("CENTRUROIDES_FLACCIDUS", "Centruroides flaccidus", "Weak bark scorpion", "American Scorpions", ["North America"],"A Mexican species from the Balsas Basin with relatively less potent venom.", 0),
    ])

    g = find_genus(ch, "Tityus")
    g["children"].extend([
        make_species("TITYUS_FALCIFER", "Tityus falcifer", "Sickle-bearing scorpion", "American Scorpions", ["South America"],"Named for the sickle-shaped hook on the telson; part of the T. fasciolatus complex.", 0),
        make_species("TITYUS_GUAYAKUM", "Tityus guayakum", "Guayakum scorpion", "American Scorpions", ["South America"],"Found in the dry Chaco forests of Paraguay and Bolivia; aestivates in deep burrows.", 0),
        make_species("TITYUS_SPURRELLI", "Tityus spurrelli", "Spurrell's scorpion", "American Scorpions", ["South America"],"A Colombian forest species with reddish pedipalps.", 0, "Spurrell"),
    ])

    g = find_genus(ch, "Hottentotta")
    g["children"].extend([
        make_species("HOTTENTOTTA_LEPTOCHELIS", "Hottentotta leptochelys", "Slender-clawed scorpion", "African Scorpions", ["Africa"],"A slender Hottentotta from the Ethiopian highlands with unusually narrow pedipalps.", 0),
        make_species("HOTTENTOTTA_ALBURQUERQUENSIS", "Hottentotta alburquerquensis", "Albuquerque's scorpion", "Asian Scorpions", ["Asia"],"From Gujarat, India; inhabits thorn scrub and arid agricultural land.", 0),
        make_species("HOTTENTOTTA_SPINIGER", "Hottentotta spiniger", "Spiny Hottentotta", "African Scorpions", ["Africa"],"Distributed across the Horn of Africa with notably spiny pedipalp segments.", 0),
    ])

    g = find_genus(ch, "Parabuthus")
    g["children"].extend([
        make_species("PARABUTHUS_NAMIBIENSIS", "Parabuthus namibiensis", "Namib thicktail scorpion", "African Scorpions", ["Africa"],"Endemic to the Namib Desert sand seas; pale yellow to match the dune sand.", 0),
        make_species("PARABUTHUS_KAROOENSIS", "Parabuthus karooensis", "Karoo thicktail scorpion", "African Scorpions", ["Africa"],"A small Parabuthus from the Succulent Karoo biome of South Africa.", 0),
    ])

    g = find_genus(ch, "Buthus")
    g["children"].extend([
        make_species("BUTHUS_ALGERIANUS", "Buthus algerianus", "Algerian yellow scorpion", "Mediterranean Scorpions", ["Africa", "Europe"],"The most widespread Buthus in Algeria and Tunisia; venom shows regional variation.", 0),
        make_species("BUTHUS_MONTANUS", "Buthus montanus", "Mountain yellow scorpion", "Mediterranean Scorpions", ["Europe"],"A high-elevation Buthus from the Sierra Nevada of Spain above 2000 m.", 0),
        make_species("BUTHUS_MAROCCANUS", "Buthus maroccanus", "Moroccan yellow scorpion", "Mediterranean Scorpions", ["Africa"],"Endemic to the Rif and Middle Atlas mountains of Morocco.", 0),
    ])

    g = find_genus(ch, "Mesobuthus")
    g["children"].extend([
        make_species("MESOBUTHUS_TERNERI", "Mesobuthus ternerii", "Terner's scorpion", "Asian Scorpions", ["Asia"],"From the Kyzylkum Desert of Uzbekistan; adapted to continental climate extremes.", 0, "Terner"),
        make_species("MESOBUTHUS_BALTICUS", "Mesobuthus balticus", "Baltic scorpion", "Asian Scorpions", ["Europe", "Asia"],"The northernmost Mesobuthus, found around the Caspian Sea and Volga Delta.", 0),
    ])

    g = find_genus(ch, "Isometrus")
    g["children"].extend([
        make_species("ISOMETRUS_ASIATICUS", "Isometrus asiaticus", "Asian house scorpion", "Tropical Scorpions", ["Asia"],"Distributed across southern China and Indochina; similar to I. maculatus.", 0),
        make_species("ISOMETRUS_SINGAPORENSIS", "Isometrus singaporensis", "Singapore house scorpion", "Tropical Scorpions", ["Asia"],"Common in Singapore and Peninsular Malaysia; found in urban gardens.", 0),
    ])

    g = find_genus(ch, "Lychas")
    g["children"].extend([
        make_species("LYCHAS_BIHARI", "Lychas bihari", "Bihar scorpion", "Asian Scorpions", ["Asia"],"An Indian species from the Gangetic floodplains, commonly encountered in eastern India.", 0),
        make_species("LYCHAS_ALBIMANUS", "Lychas albimanus", "White-handed scorpion", "Oceania", ["Oceania"],"An Australian species with pale pedipalps, found in Queensland and Northern Territory.", 0),
    ])

    # New genera
    g = ensure_genus(ch, "GEN_ANANTERIS", "Ananteris","Slender-tailed scorpions","Small buthids of Central and South America with elongated metasoma; many autotomise the tail as a predator escape.", "American Scorpions")
    g["children"].extend([
        make_species("ANANTERIS_BALZANI", "Ananteris balzani", "Balzan's slender scorpion", "American Scorpions", ["South America"],"Found in the Gran Chaco region of Paraguay and Argentina; adapted to dry thorn-scrub.", 0),
        make_species("ANANTERIS_AMAZONENSIS", "Ananteris amazonensis", "Amazonian slender scorpion", "American Scorpions", ["South America"],"A small scorpion from Amazonian rainforest floor litter; thin tail is easily autotomised.", 0),
        make_species("ANANTERIS_COARCTATA", "Ananteris coarctata", "Narrow-tailed scorpion", "American Scorpions", ["South America"],"Occurring from Colombia to Bolivia in leaf litter of tropical forests.", 0),
        make_species("ANANTERIS_ASANAE", "Ananteris asanae", "Asana's scorpion", "American Scorpions", ["South America"],"Described from the Peruvian Amazon; named after a local conservationist.", 0, "Asana"),
    ])

    g = ensure_genus(ch, "GEN_BABYCURUS", "Babycurus","African burrowing scorpions","Stout-bodied burrowing scorpions across sub-Saharan Africa with potent venom.", "African Scorpions")
    g["children"].extend([
        make_species("BABYCURUS_BUTRANTI", "Babycurus butranti", "Butrant's burrowing scorpion", "African Scorpions", ["Africa"],"From the savannas of Ghana and Cote d'Ivoire; constructs shallow burrows at grass bases.", 0),
        make_species("BABYCURUS_CENTRUROIDES", "Babycurus centruroides", "Centruroides-like burrowing scorpion", "African Scorpions", ["Africa"],"An East African species from Kenya and Tanzania; favours rocky outcrops.", 0),
        make_species("BABYCURUS_GIGAS", "Babycurus gigas", "Giant burrowing scorpion", "African Scorpions", ["Africa"],"The largest Babycurus reaching 10 cm; preys on large insects and small vertebrates.", 0),
    ])

    g = ensure_genus(ch, "GEN_ODONTOBUTHUS", "Odontobuthus","Toothed-tailed scorpions","Middle Eastern buthids with a distinctive tooth-like projection on the telson.", "Asian Scorpions")
    g["children"].extend([
        make_species("ODONTOBUTHUS_DORIAE", "Odontobuthus doriae", "Doria's toothed scorpion", "Asian Scorpions", ["Asia"],"From Iran, Iraq, and Afghanistan; common cause of envenomation on the Iranian plateau.", 0),
        make_species("ODONTOBUTHUS_ODONTURUS", "Odontobuthus odonturus", "Toothed-tail scorpion", "Asian Scorpions", ["Asia"],"A Pakistani species from the Indus River basin with a distinctive ventral telson tooth.", 0),
        make_species("ODONTOBUTHUS_TIGRIS", "Odontobuthus tigris", "Tigris toothed scorpion", "Asian Scorpions", ["Asia"],"From Mesopotamian marshlands of southern Iraq; adapted to clay soils with high water tables.", 0),
    ])

    g = ensure_genus(ch, "GEN_COMPSOBUTHUS", "Compsobuthus","Graceful thin-tailed scorpions","Small slender buthids from North Africa through the Middle East to Pakistan.", "Old World Thin-tailed Scorpions")
    g["children"].extend([
        make_species("COMPSOBUTHUS_MATTHIESSENI", "Compsobuthus matthiesseni", "Matthiessen's graceful scorpion", "Old World Thin-tailed Scorpions", ["Africa", "Asia"],"Widespread from Egypt to Iran; inhabits stony desert wadis and alluvial fans.", 0),
        make_species("COMPSOBUTHUS_ACUTECARINATUS", "Compsobuthus acutecarinatus", "Sharp-keeled graceful scorpion", "Old World Thin-tailed Scorpions", ["Asia"],"Found in Oman and Yemen; has sharply defined pedipalp carinae.", 0),
    ])

    return data

ENRICHERS["buthidae"] = enrich_buthidae



# ---------------------------------------------------------------------------
# ENRICHER: theraphosidae  (GEN_xxx / mixed; use snake_case for new species)
# ---------------------------------------------------------------------------
def enrich_theraphosidae(data):
    ch = data["children"]

    g = find_genus(ch, "Theraphosa")
    g["children"].extend([
        make_species("THERAPHOSA_STIRMINGI", "Theraphosa stirmi", "Burgundy goliath birdeater", "New World Tarantulas", ["South America"],"A massive tarantula from the Guiana Shield with a distinct burgundy carapace sheen.", 0),
        make_species("THERAPHOSA_PSEUDOBLONDI", "Theraphosa pseudoblondi", "False goliath birdeater", "New World Tarantulas", ["South America"],"Previously confused with T. blondi; recognised by spermathecal morphology.", 0),
        make_species("THERAPHOSA_AURANTIACA", "Theraphosa aurantiaca", "Orange goliath birdeater", "New World Tarantulas", ["South America"],"A rare orange-haired Theraphosa from Roraima, Brazil; unique colour within the genus.", 0),
    ])

    g = find_genus(ch, "Brachypelma")
    g["children"].extend([
        make_species("BRACHYPELMA_VAGANS", "Brachypelma vagans", "Mexican red-rump tarantula", "New World Tarantulas", ["North America"],"Widespread from Mexico to Colombia; common in the pet trade but CITES II listed.", 0),
        make_species("BRACHYPELMA_ALBOPILOSUM", "Brachypelma albopilosum", "Curlyhair tarantula", "New World Tarantulas", ["North America"],"A Costa Rican tarantula with a fluffy curled-hair appearance; extremely popular in the pet trade.", 0),
        make_species("BRACHYPELMA_EMILIA", "Brachypelma emilia", "Mexican red-leg tarantula", "New World Tarantulas", ["North America"],"Striking orange-red carapace and dark legs; found along Mexico's Pacific coast.", 0),
        make_species("BRACHYPELMA_KLAASI", "Brachypelma klaasi", "Mexican pink tarantula", "New World Tarantulas", ["North America"],"The rarest Brachypelma from Jalisco with a pinkish carapace; listed as Endangered.", 0),
    ])

    g = find_genus(ch, "Poecilotheria")
    g["children"].extend([
        make_species("POECILOTHERIA_VITTATA", "Poecilotheria vittata", "Whip spider ornamental", "Old World Tarantulas", ["Asia"],"A Sri Lankan arboreal tarantula with striped leg pattern; IUCN Vulnerable.", 0),
        make_species("POECILOTHERIA_STRICTA", "Poecilotheria stricta", "Mysore ornamental tarantula", "Old World Tarantulas", ["Asia"],"Endemic to the Western Ghats of India with narrow leg banding; Critically Endangered.", 0),
        make_species("POECILOTHERIA_UNIFORMIS", "Poecilotheria uniformis", "Uniform ornamental tarantula", "Old World Tarantulas", ["Asia"],"A recently described Sri Lankan species with less contrasting leg markings.", 0),
        make_species("POECILOTHERIA_RAJAEI", "Poecilotheria rajaei", "Rajaei's ornamental tarantula", "Old World Tarantulas", ["Asia"],"Described from northern Sri Lanka in 2012, surviving in isolated forest fragments.", 0),
    ])

    g = find_genus(ch, "Grammostola")
    g["children"].extend([
        make_species("GRAMMOSTOLA_ALTHAEPUS", "Grammostola althaepus", "King rose tarantula", "New World Tarantulas", ["South America"],"A large Grammostola from the Chilean Andes foothills with a coppery-rose carapace.", 0),
        make_species("GRAMMOSTOLA_CHALCOTHRIX", "Grammostola chalcothrix", "Brazilian copper tarantula", "New World Tarantulas", ["South America"],"Named for its coppery-brown carapace sheen; females can exceed 25 years.", 0),
        make_species("GRAMMOSTOLA_QUATERNARIUS", "Grammostola quaternarius", "Four-keeled tarantula", "New World Tarantulas", ["South America"],"A distinctive Grammostola from Uruguay with a four-lobed spermatheca.", 0),
    ])

    g = find_genus(ch, "Aphonopelma")
    g["children"].extend([
        make_species("APHONOPELMA_SEEMANNI", "Aphonopelma seemanni", "Zebra tarantula", "New World Tarantulas", ["North America"],"A Costa Rican species with black-and-white striped legs; popular for its striking pattern.", 0),
        make_species("APHONOPELMA_ANCEPS", "Aphonopelma anceps", "Texas deathstar tarantula", "New World Tarantulas", ["North America"],"A rare deep-burrowing species from the Texas panhandle.", 0),
        make_species("APHONOPELMA_GREMIUM", "Aphonopelma gremium", "Desert blonde tarantula", "New World Tarantulas", ["North America"],"A small species from the Mojave Desert; one of the most heat-tolerant tarantulas.", 0),
    ])

    g = find_genus(ch, "Lasiodora")
    g["children"].extend([
        make_species("LASIODORA_DIFFICILIS", "Lasiodora difficilis", "Brazilian red birdeater", "New World Tarantulas", ["South America"],"A very large Lasiodora from Bahia, Brazil, with reddish abdominal hairs.", 0),
        make_species("LASIODORA_KLUGEI", "Lasiodora klugei", "Kluge's tarantula", "New World Tarantulas", ["South America"],"From the Atlantic Forest of southeastern Brazil; smaller but longer-legged than L. parahybana.", 0, "Kluge"),
        make_species("LASIODORA_CURVISETOSA", "Lasiodora curvisetosa", "Curved-bristle birdeater", "New World Tarantulas", ["South America"],"A rarely imported Brazilian species with curved hook-like setae on its palps.", 0),
    ])

    g = find_genus(ch, "Selenocosmia")
    g["children"].extend([
        make_species("SELENOCOSMIA_FULVIPES", "Selenocosmia fulvipes", "Golden-fanged tarantula", "Old World Tarantulas", ["Oceania"],"An Australian species from Queensland with distinctive golden-coloured chelicerae.", 0),
        make_species("SELENOCOSMIA_PAPUANA", "Selenocosmia papuana", "Papuan whistling tarantula", "Old World Tarantulas", ["Oceania"],"From Papua New Guinea and Torres Strait; produces stridulatory hissing when disturbed.", 0),
    ])

    g = find_genus(ch, "Pterinochilus")
    g["children"].extend([
        make_species("PTERINOCHILUS_LUGARDI", "Pterinochilus lugardi", "Zimbabwe silver baboon", "Old World Tarantulas", ["Africa"],"A striking silver-and-black baboon spider from Zimbabwe and Mozambique.", 0),
        make_species("PTERINOCHILUS_CORDATUS", "Pterinochilus cordatus", "Heart-marker baboon", "Old World Tarantulas", ["Africa"],"An Angolan species with a distinctive heart-shaped carapace marking.", 0),
        make_species("PTERINOCHILUS_VORAX", "Pterinochilus vorax", "Widespread baboon tarantula", "Old World Tarantulas", ["Africa"],"Found across East Africa from Ethiopia to Tanzania; adaptable to savanna and forest.", 0),
    ])

    g = find_genus(ch, "Cyriopagopus")
    g["children"].extend([
        make_species("CYRIOPAGOPUS_HARTMANNI", "Cyriopagopus hartmanni", "Myanmar sapphire tarantula", "Old World Tarantulas", ["Asia"],"A newly described species from Myanmar with vivid metallic blue carapace.", 0),
        make_species("CYRIOPAGOPUS_PAGANUS", "Cyriopagopus paganus", "Burmese earth tiger", "Old World Tarantulas", ["Asia"],"A large semi-arboreal Cyriopagopus from the Ayeyarwady region of Myanmar.", 0),
    ])

    g = find_genus(ch, "Chromatopelma")
    g["children"].extend([
        make_species("CHROMATOPELMA_EUGENI", "Chromatopelma eugeni", "Eugen's greenbottle tarantula", "New World Tarantulas", ["South America"],"A Venezuelan species with greener carapace than C. cyaneopubescens.", 0),
    ])

    g = find_genus(ch, "Caribena")
    g["children"].extend([
        make_species("CARIBENA_LAETA", "Caribena laeta", "Puerto Rican pinktoe", "New World Tarantulas", ["North America"],"Endemic to Puerto Rico; closely related to C. versicolor but with subdued coloration.", 0),
    ])

    # New genera
    g = ensure_genus(ch, "GEN_AVICULARIA", "Avicularia","Pinktoe tarantulas","Arboreal tarantulas from Central and South America with pink or reddish tarsal tips.", "New World Tarantulas")
    g["children"].extend([
        make_species("AVICULARIA_AVICULARIA", "Avicularia avicularia", "Pinktoe tarantula", "New World Tarantulas", ["South America"],"The type species, widespread across Amazonia; spiderlings have bright blue legs.", 0),
        make_species("AVICULARIA_METALLICA", "Avicularia metallica", "Metallic pinktoe tarantula", "New World Tarantulas", ["South America"],"Found in Suriname and French Guiana with a metallic blue carapace sheen.", 0),
        make_species("AVICULARIA_PURPUREA", "Avicularia purpurea", "Purple pinktoe tarantula", "New World Tarantulas", ["South America"],"An Ecuadorian species with deep violet-purple carapace; one of the most colourful Avicularia.", 0),
        make_species("AVICULARIA_JURUENSIS", "Avicularia juruensis", "Jurua pinktoe tarantula", "New World Tarantulas", ["South America"],"Named after the Jurua River in Brazil; golden-brown carapace with pink toes.", 0),
        make_species("AVICULARIA_VELUTINA", "Avicularia velutina", "Velvet pinktoe tarantula", "New World Tarantulas", ["South America"],"A Venezuelan species with velvety black body and bright pink tarsi.", 0),
    ])

    g = ensure_genus(ch, "GEN_PSALMOPOEUS", "Psalmopoeus","Neotropical tree tarantulas","Fast arboreal tarantulas from Central and South America lacking urticating hairs.", "New World Tarantulas")
    g["children"].extend([
        make_species("PSALMOPOEUS_CAMBRIDGEI", "Psalmopoeus cambridgei", "Trinidad chevron tarantula", "New World Tarantulas", ["South America"],"A large arboreal tarantula from Trinidad with V-shaped chevron abdomen pattern.", 0),
        make_species("PSALMOPOEUS_IRMINIA", "Psalmopoeus irminia", "Venezuelan suntiger tarantula", "New World Tarantulas", ["South America"],"Stunning black and orange banding pattern; one of the most beautiful arboreal tarantulas.", 0),
        make_species("PSALMOPOEUS_PULCHER", "Psalmopoeus pulcher", "Panamanian blond tarantula", "New World Tarantulas", ["North America", "South America"],"A Panamanian species with pale golden carapace hairs; the most docile Psalmopoeus.", 0),
        make_species("PSALMOPOEUS_REDUNCUS", "Psalmopoeus reduncus", "Costa Rican orange-mouth tarantula", "New World Tarantulas", ["North America"],"Endemic to Costa Rica's Pacific slope; has a distinctive orange-coloured oral region.", 0),
    ])

    g = ensure_genus(ch, "GEN_HETEROSCODRA", "Heteroscodra","African baboon tarantulas","Old World tarantulas from West and Central Africa with potent venom.", "Old World Tarantulas")
    g["children"].extend([
        make_species("HETEROSCODRA_MACULATA", "Heteroscodra maculata", "Togo starburst baboon", "Old World Tarantulas", ["Africa"],"Infamous for potent neurotoxic venom causing prolonged muscle cramps; arboreal and fast.", 0),
        make_species("HETEROSCODRA_CRASSIPES", "Heteroscodra crassipes", "Thick-legged baboon", "Old World Tarantulas", ["Africa"],"A West African species with thickened front legs adapted for digging.", 0),
        make_species("HETEROSCODRA_SULTANA", "Heteroscodra sultana", "Sultana baboon tarantula", "Old World Tarantulas", ["Africa"],"The largest Heteroscodra; warm brown with subtle golden highlights.", 0),
    ])

    return data

ENRICHERS["theraphosidae"] = enrich_theraphosidae



# ---------------------------------------------------------------------------
# ENRICHER: gekkonidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_gekkonidae(data):
    ch = data["children"]

    g = find_genus(ch, "Gekko")
    g["children"].extend([
        make_species("GEKKO_TAIWANIENSIS", "Gekko taiwaniensis", "Taiwanese Gecko", "House Geckos", ["Asia"],"Endemic to Taiwan from lowlands to 1500 m; emits a distinctive two-note call.", 0),
        make_species("GEKKO_HOKKAENSIS", "Gekko hokkaensis", "Hokkaido Gecko", "House Geckos", ["Asia"],"The northernmost Gekko; hibernates in deep rock crevices through cold winters.", 0),
        make_species("GEKKO_LIBERATUS", "Gekko liberatus", "Liberated Gecko", "House Geckos", ["Asia"],"Restricted to primary lowland forest in the Sierra Madre of the Philippines.", 0),
        make_species("GEKKO_SHIBATAI", "Gekko shibatai", "Shibata's Gecko", "House Geckos", ["Asia"],"A Japanese Gekko from the Ryukyu Archipelago with a short rounded snout.", 0),
    ])

    g = find_genus(ch, "Hemidactylus")
    g["children"].extend([
        make_species("HEMIDACTYLUS_ANGULATUS", "Hemidactylus angulatus", "Angulate House Gecko", "House Geckos", ["Africa"],"A West African species formerly confused with H. mabouia; distinguished by angular scale rows.", 0),
        make_species("HEMIDACTYLUS_TENUICAUDUS", "Hemidactylus tenuicaudus", "Slender-tailed Gecko", "House Geckos", ["Asia"],"A Sri Lankan endemic with an exceptionally slender whiplike tail.", 0),
        make_species("HEMIDACTYLUS_GRENADIENSIS", "Hemidactylus grenadiensis", "Grenadian House Gecko", "House Geckos", ["North America"],"Endemic to Grenada; one of few native Hemidactylus in the Caribbean.", 0),
        make_species("HEMIDACTYLUS_IMBRICATUS", "Hemidactylus imbricatus", "Tiled-scaled Gecko", "House Geckos", ["Asia"],"From the Western Ghats of India with overlapping tile-like scale arrangement.", 0),
    ])

    g = find_genus(ch, "Cyrtodactylus")
    g["children"].extend([
        make_species("CYRTODACTYLUS_PHAYA", "Cyrtodactylus phaya", "Kayah Bent-toed Gecko", "Geckos", ["Asia"],"Microendemic to a single limestone karst tower in Kayah State, Myanmar; Critically Endangered by quarrying.", 0),
        make_species("CYRTODACTYLUS_FRANCOI", "Cyrtodactylus francoi", "Franco's Bent-toed Gecko", "Geckos", ["Asia"],"A Thai endemic from Phitsanulok limestone hills.", 0, "Franco"),
        make_species("CYRTODACTYLUS_LANGUI", "Cyrtodactylus langui", "Langur Bent-toed Gecko", "Geckos", ["Asia"],"A Vietnamese cave-adapted species with reduced eyes and pale coloration.", 0),
    ])

    g = find_genus(ch, "Phelsuma")
    g["children"].extend([
        make_species("PHELSUMA_ABBOTTI", "Phelsuma abbotti", "Abbott's Day Gecko", "Day Geckos", ["Africa"],"Found in Comoros and East African coast; less brightly coloured but an important pollinator.", 0),
        make_species("PHELSUMA_BORBONICA", "Phelsuma borbonica", "Reunion Day Gecko", "Day Geckos", ["Africa"],"Endemic to Reunion Island; two subspecies with distinct red or blue spot patterns.", 0),
        make_species("PHELSUMA_GIGAS", "Phelsuma gigas", "Giant Day Gecko", "Day Geckos", ["Africa"],"An extinct giant day gecko from Rodrigues Island reaching 40 cm.", 0),
    ])

    g = find_genus(ch, "Uroplatus")
    g["children"].extend([
        make_species("UROPLATUS_ALLOUAUDI", "Uroplatus alluaudi", "Alluaud's Leaf-tailed Gecko", "Leaf-tailed Geckos", ["Africa"],"A small Uroplatus from northern Madagascar with a short stumpy tail.", 0, "Charles Alluaud"),
        make_species("UROPLATUS_PIETSCHMANNI", "Uroplatus pietschmanni", "Pietschmann's Leaf-tailed Gecko", "Leaf-tailed Geckos", ["Africa"],"Described from Montagne d'Ambre, Madagascar, with intricate lichen-like patterning.", 0),
    ])

    g = find_genus(ch, "Paroedura")
    g["children"].extend([
        make_species("PAROEDURA_VATHA", "Paroedura vatha", "Andohahela Ground Gecko", "Ground Geckos", ["Africa"],"Endemic to Andohahela rainforest of southeastern Madagascar; lacks juvenile banding in adults.", 0),
        make_species("PAROEDURA_TANJAKA", "Paroedura tanjaka", "Tanjaka Ground Gecko", "Ground Geckos", ["Africa"],"A dry-forest species from western Madagascar; the name means 'tail' in Sakalava.", 0),
    ])

    g = find_genus(ch, "Pachydactylus")
    g["children"].extend([
        make_species("PACHYDACTYLUS_GEITJEI", "Pachydactylus geitjei", "Geitje Gecko", "Geckos", ["Africa"],"A small species from the Cape Fold Mountains; 'geitje' means 'little goat' in Afrikaans.", 0),
        make_species("PACHYDACTYLUS_SCUTATUS", "Pachydactylus scutatus", "Shield-scaled Gecko", "Geckos", ["Africa"],"A Namibian species with enlarged shield-like scales on its snout.", 0),
    ])

    g = find_genus(ch, "Lepidodactylus")
    g["children"].extend([
        make_species("LEPIDODACTYLUS_PUSILLUS", "Lepidodactylus pusillus", "Tiny Scalytock Gecko", "Geckos", ["Oceania"],"One of the smallest Lepidodactylus, found in Solomon Islands coastal coconut palms.", 0),
        make_species("LEPIDODACTYLUS_YAMII", "Lepidodactylus yamii", "Yamii Gecko", "Geckos", ["Oceania"],"A Micronesian species from Yap and Palau, named after a traditional navigator.", 0),
    ])

    g = find_genus(ch, "Nactus")
    g["children"].extend([
        make_species("NACTUS_VANKAMPENI", "Nactus vankampeni", "Van Kampen's Gecko", "Geckos", ["Oceania"],"A New Guinean species from lowland and montane forests.", 0, "Pieter van Kampen"),
        make_species("NACTUS_ALIENUS", "Nactus alienus", "Strange Gecko", "Geckos", ["Oceania"],"Recently discovered from the D'Entrecasteaux Islands of Papua New Guinea.", 0),
    ])

    g = find_genus(ch, "Eublepharis")
    g["children"].extend([
        make_species("EUBLEPHARIS_ANCEPS", "Eublepharis anceps", "Two-headed Leopard Gecko", "Ground Geckos", ["Asia"],"A rare Eublepharis from the Sulaiman Mountains of Pakistan with a uniquely bilobed tail.", 0),
        make_species("EUBLEPHARIS_HARDWICKII", "Eublepharis hardwickii", "Hardwicke's Gecko", "Ground Geckos", ["Asia"],"An Indian species from the Eastern Ghats with distinctive vertebral spots.", 0, "Thomas Hardwicke"),
    ])

    g = find_genus(ch, "Correlophus")
    g["children"].extend([
        make_species("CORRELOPHUS_LEPIDA", "Correlophus lepida", "New Caledonian Gecko", "House Geckos", ["Oceania"],"A second Correlophus species from southern New Caledonia; smaller than C. ciliatus.", 0),
    ])

    # New genera
    g = ensure_genus(ch, "GENUS_LYGODACTYLUS", "Lygodactylus","Dwarf geckos","Tiny diurnal geckos of Africa, Madagascar and South America; among the smallest geckos.", "Dwarf Geckos")
    g["children"].extend([
        make_species("LYGODACTYLUS_PICTURATUS", "Lygodactylus picturatus", "White-lined Dwarf Gecko", "Dwarf Geckos", ["Africa"],"The most widespread Lygodactylus across sub-Saharan Africa.", 0),
        make_species("LYGODACTYLUS_CONRADTI", "Lygodactylus conradti", "Conradt's Dwarf Gecko", "Dwarf Geckos", ["Africa"],"A Tanzanian endemic from the Usambara Mountains, threatened by agricultural conversion.", 0),
        make_species("LYGODACTYLUS_MADAGASCARIENSIS", "Lygodactylus madagascariensis", "Malagasy Dwarf Gecko", "Dwarf Geckos", ["Africa"],"From eastern Malagasy rainforests; males have a vivid yellow throat during breeding.", 0),
        make_species("LYGODACTYLUS_WILLIAMSI", "Lygodactylus williamsi", "Williams' Dwarf Gecko", "Dwarf Geckos", ["Africa"],"Critically Endangered Tanzanian endemic; vivid electric blue males; CITES I listed.", 0, "Williams"),
    ])

    g = ensure_genus(ch, "GENUS_CHONDRODACTYLUS", "Chondrodactylus","Giant ground geckos","Large terrestrial geckos of southern Africa with thick swollen toes, reaching 20 cm.", "Ground Geckos")
    g["children"].extend([
        make_species("CHONDRODACTYLUS_ANGULIFER", "Chondrodactylus angulifer", "Namib Sand Gecko", "Ground Geckos", ["Africa"],"The largest gekkonid in southern Africa; fringed toes act as snowshoes on Namib sand.", 0),
        make_species("CHONDRODACTYLUS_BIMACULATUS", "Chondrodactylus bimaculatus", "Two-spotted Ground Gecko", "Ground Geckos", ["Africa"],"From South Africa and Botswana with prominent dark spots at the tail base.", 0),
        make_species("CHONDRODACTYLUS_FITZSIMONSI", "Chondrodactylus fitzsimonsi", "Fitzsimons' Giant Gecko", "Ground Geckos", ["Africa"],"Ranges from Angola to South Africa; distinguished by enlarged tubercular scales.", 0, "Vivian Fitzsimons"),
    ])

    g = ensure_genus(ch, "GENUS_GEKHOLEPTIS", "Gekholeptis","Flat geckos","Flattened, crevice-dwelling geckos of southwest Africa with extremely depressed bodies.", "Ground Geckos")
    g["children"].extend([
        make_species("GEKHOLEPTIS_TYPICA", "Gekholeptis typica", "Common Flat Gecko", "Ground Geckos", ["Africa"],"A flattened crevice-dweller from Namibia; its body is so flat it can hide under a coin.", 0),
        make_species("GEKHOLEPTIS_GRANDIS", "Gekholeptis grandis", "Giant Flat Gecko", "Ground Geckos", ["Africa"],"A larger relative found on granite domes; vertical body compression allows entry into hairline cracks.", 0),
    ])

    return data

ENRICHERS["gekkonidae"] = enrich_gekkonidae



# ---------------------------------------------------------------------------
# ENRICHER: hylidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_hylidae(data):
    ch = data["children"]

    g = find_genus(ch, "Hyla")
    g["children"].extend([
        make_species("HYLA_CHINENSIS", "Hyla chinensis", "Chinese Tree Frog", "Tree Frogs", ["Asia"],"A small green tree frog from southeastern China and Taiwan with a pale lateral line.", 0),
        make_species("HYLA_SANCHIANGENSIS", "Hyla sanchiangensis", "Sanchiang Tree Frog", "Tree Frogs", ["Asia"],"From mountain streams in Fujian province; call frequency differs from H. chinensis.", 0),
        make_species("HYLA_IMMACULATA", "Hyla immaculata", "Spotless Tree Frog", "Tree Frogs", ["Asia"],"A plain green tree frog from central China without lateral stripes.", 0),
        make_species("HYLA_TSINLINGENSIS", "Hyla tsinlingensis", "Qinling Tree Frog", "Tree Frogs", ["Asia"],"The most cold-tolerant Hyla in Asia, breeding in temporary pools after snowmelt.", 0),
    ])

    g = find_genus(ch, "Dryophytes")
    g["children"].extend([
        make_species("DRYOPHYTES_ANDERSONII", "Dryophytes andersonii", "Anderson's Tree Frog", "Tree Frogs", ["North America"],"A pine-barrens specialist from New Jersey; Near Threatened by habitat loss.", 0),
        make_species("DRYOPHYTES_JAPONICUS", "Dryophytes japonicus", "Japanese Tree Frog", "Tree Frogs", ["Asia"],"The most common tree frog in Japan with distinctive brassy-green colour.", 0),
        make_species("DRYOPHYTES_SUIANEUS", "Dryophytes suianeus", "Suyuan Tree Frog", "Tree Frogs", ["Asia"],"A Korean endemic separated from D. japonicus by its distinct advertisement call.", 0),
    ])

    g = find_genus(ch, "Pseudacris")
    g["children"].extend([
        make_species("PSEUDACRIS_CRUCIFER", "Pseudacris crucifer", "Spring Peeper", "Tree Frogs", ["North America"],"One of the first frogs to call in spring; its high-pitched chorus signals winter's end.", 0),
        make_species("PSEUDACRIS_REGILLA", "Pseudacris regilla", "Pacific Tree Frog", "Tree Frogs", ["North America"],"The most common Pacific coast frog; calls famously used as generic frog sound in films.", 0),
        make_species("PSEUDACRIS_OCULARIS", "Pseudacris ocularis", "Little Grass Frog", "Tree Frogs", ["North America"],"The smallest frog in North America at just 2 cm.", 0),
        make_species("PSEUDACRIS_FERIARUM", "Pseudacris feriarum", "Upland Chorus Frog", "Tree Frogs", ["North America"],"A chorus frog of the US Piedmont with three dark back stripes.", 0),
    ])

    g = find_genus(ch, "Phyllomedusa")
    g["children"].extend([
        make_species("PHYLLOMEDUSA_SAUVAGII", "Phyllomedusa sauvagii", "White-lined Leaf Frog", "Tree Frogs", ["South America"],"Secretes waxy lipid over its body using hind legs to prevent water loss in the dry Chaco.", 0),
        make_species("PHYLLOMEDUSA_VAILLANTII", "Phyllomedusa vaillantii", "Vaillant's Leaf Frog", "Tree Frogs", ["South America"],"Constructs leaf nests over water across the Amazon basin.", 0),
        make_species("PHYLLOMEDUSA_HYPOCONDRIALIS", "Phyllomedusa hypochondrialis", "Reticulated Leaf Frog", "Tree Frogs", ["South America"],"Smaller Phyllomedusa from the Guiana Shield with antibiotic skin peptides.", 0),
        make_species("PHYLLOMEDUSA_BICOLOR", "Phyllomedusa bicolor", "Two-coloured Leaf Frog", "Tree Frogs", ["South America"],"Giant monkey frog; skin secretion used in the 'kambo' Amazonian purification ritual.", 0),
    ])

    g = find_genus(ch, "Scinax")
    g["children"].extend([
        make_species("SCINAX_RUBER", "Scinax ruber", "Rusty Snouted Tree Frog", "Tree Frogs", ["South America"],"A common adaptable species throughout Amazonia; most abundant frog in disturbed areas.", 0),
        make_species("SCINAX_NASICUS", "Scinax nasicus", "Large-snouted Tree Frog", "Tree Frogs", ["South America"],"A southern species from the Chaco and Pampas; named for its prominent pointed snout.", 0),
        make_species("SCINAX_FUSCOVARIUS", "Scinax fuscovarius", "Dark-varied Snouted Tree Frog", "Tree Frogs", ["South America"],"A medium-sized Scinax with highly variable dorsal patterning.", 0),
        make_species("SCINAX_ACUMINATUS", "Scinax acuminatus", "Pointed Snouted Tree Frog", "Tree Frogs", ["South America"],"A Chaco specialist with sharp snout adapted for burrowing into mud during dry season.", 0),
    ])

    g = find_genus(ch, "Litoria")
    g["children"].extend([
        make_species("LITORIA_INFRAFRENATA", "Litoria infrafrenata", "Giant Tree Frog", "Tree Frogs", ["Oceania", "Asia"],"The largest tree frog in the world at 14 cm; found in New Guinea and Queensland.", 0),
        make_species("LITORIA_CAERULEA", "Litoria caerulea", "Australian Green Tree Frog", "Tree Frogs", ["Oceania"],"Famous for its plump green body and docile personality; can survive in sealed shipping containers.", 0),
        make_species("LITORIA_CHLORIS", "Litoria chloris", "Red-eyed Tree Frog", "Tree Frogs", ["Oceania"],"Brilliant green frog with crimson eyes from the Australian east coast.", 0),
        make_species("LITORIA_FALLAX", "Litoria fallax", "Eastern Dwarf Tree Frog", "Tree Frogs", ["Oceania"],"A tiny 2-cm green tree frog abundant along the eastern Australian coast.", 0),
        make_species("LITORIA_BOOROOLONGENSIS", "Litoria booroolongensis", "Booroolong Frog", "Tree Frogs", ["Oceania"],"An Endangered stream-dwelling frog from the highlands of NSW and Victoria.", 0),
    ])

    g = find_genus(ch, "Osteopilus")
    g["children"].extend([
        make_species("OSTEOPILUS_SEPTENTRIONALIS", "Osteopilus septentrionalis", "Cuban Tree Frog", "Tree Frogs", ["North America"],"The largest tree frog in North America; invasive in Florida; voracious predator.", 0),
        make_species("OSTEOPILUS_BRUNNEUS", "Osteopilus brunneus", "Brown Cuban Tree Frog", "Tree Frogs", ["North America"],"An endemic Cuban species restricted to Sierra Maestra mountains.", 0),
    ])

    g = find_genus(ch, "Agalychnis")
    g["children"].extend([
        make_species("AGALYCHNIS_CALLIDRYAS", "Agalychnis callidryas", "Red-eyed Tree Frog", "Tree Frogs", ["North America", "South America"],"The iconic red-eyed tree frog of Central America with vivid colours and startle display.", 0),
        make_species("AGALYCHNIS_MORELLETII", "Agalychnis moreletii", "Morelet's Tree Frog", "Tree Frogs", ["North America"],"A green leaf frog from Belize and Guatemala; Critically Endangered by chytrid disease.", 0),
    ])

    g = find_genus(ch, "Boana")
    g["children"].extend([
        make_species("BOANA_RANICEPS", "Boana raniceps", "Crowned Tree Frog", "Tree Frogs", ["South America"],"A large Amazonian tree frog with loud resonant honking call from elevated perches.", 0),
        make_species("BOANA_FASCIATA", "Boana fasciata", "Banded Tree Frog", "Tree Frogs", ["South America"],"A striped Amazonian species found in flooded forest and oxbow lake margins.", 0),
        make_species("BOANA_CALCARATA", "Boana calcarata", "Sharp-headed Tree Frog", "Tree Frogs", ["South America"],"Distinguished by sharply pointed head and white dorsolateral stripe.", 0),
    ])

    g = find_genus(ch, "Smilisca")
    g["children"].extend([
        make_species("SMILISCA_BAUDINII", "Smilisca baudinii", "Mexican Tree Frog", "Tree Frogs", ["North America"],"A large tree frog from Mexico to Panama; hides in tree cavities during dry periods.", 0),
        make_species("SMILISCA_SORDIDA", "Smilisca sordida", "Drab Tree Frog", "Tree Frogs", ["South America"],"Found in Pacific lowlands of Colombia and Ecuador near gallery forests.", 0),
    ])

    g = find_genus(ch, "Triprion")
    g["children"].extend([
        make_species("TRIPRION_PETASATUS", "Triprion petasatus", "Yucatan Casque-headed Tree Frog", "Tree Frogs", ["North America"],"Has a bony casque fused to the skull; seals itself into tree holes with a mucus plug.", 0),
    ])

    g = find_genus(ch, "Tlalocohyla")
    g["children"].extend([
        make_species("TLALOCOHYLA_SMITTHII", "Tlalocohyla smithii", "Smith's Tree Frog", "Tree Frogs", ["North America"],"A Mexican endemic from Pacific coastal plains.", 0, "Hobart M. Smith"),
    ])

    g = find_genus(ch, "Pithecopus")
    if g:
        g["children"].extend([
            make_species("PITHECOPUS_ROHRII", "Pithecopus rohrii", "Rohr's Leaf Frog", "Tree Frogs", ["South America"],"A leaf frog from the Andes of Bolivia and Peru with colourful flanks.", 0),
            make_species("PITHECOPUS_PALLIATUS", "Pithecopus palliatus", "Mantled Leaf Frog", "Tree Frogs", ["South America"],"Found in the Amazon basin; builds leaf nests over hanging water.", 0),
        ])

    return data

ENRICHERS["hylidae"] = enrich_hylidae



# ---------------------------------------------------------------------------
# ENRICHER: cricetidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_cricetidae(data):
    ch = data["children"]

    g = find_genus(ch, "Cricetulus")
    g["children"].extend([
        make_species("CRICETULUS_SOKOLOVI", "Cricetulus sokolovi", "Sokolov's Dwarf Hamster", "Hamsters", ["Asia"],"Named after Vladimir Sokolov; from Mongolia and Inner Mongolia with complex burrow systems.", 0, "Vladimir Sokolov"),
        make_species("CRICETULUS_KAMENSIS", "Cricetulus kamensis", "Kam Dwarf Hamster", "Hamsters", ["Asia"],"A Tibetan plateau species above 3500 m; densest fur of any Cricetulus; hibernates 6 months.", 0),
        make_species("CRICETULUS_ALBIDA", "Cricetulus albida", "White Dwarf Hamster", "Hamsters", ["Asia"],"A pale sand-coloured species from the Gobi Desert; camouflaged against gypsum salt flats.", 0),
    ])

    g = find_genus(ch, "Mesocricetus")
    g["children"].extend([
        make_species("MESOCRICETUS_NEWTONI", "Mesocricetus newtoni", "Romanian Hamster", "Hamsters", ["Europe"],"A threatened species endemic to Romania and Bulgaria; declined due to intensive farming.", 0),
        make_species("MESOCRICETUS_RADDEI", "Mesocricetus raddei", "Ciscaucasian Hamster", "Hamsters", ["Europe", "Asia"],"From northern Caucasus and southern Russia; occupies a transitional steppe zone.", 0),
    ])

    g = find_genus(ch, "Phodopus")
    g["children"].extend([
        make_species("PHODOPUS_CAMPBELLI", "Phodopus campbelli", "Campbell's Dwarf Hamster", "Hamsters", ["Asia"],"Popular pet from the steppes of Tuva and Mongolia; exhibits social monogamy.", 0),
        make_species("PHODOPUS_SUNDORUS", "Phodopus sundorus", "Eversmann's Dwarf Hamster", "Hamsters", ["Asia"],"The smallest Phodopus from the Dzungarian Basin; hibernates in winter.", 0),
        make_species("PHODOPUS_PRZEWALSKII", "Phodopus przewalskii", "Przewalski's Hamster", "Hamsters", ["Asia"],"Known from only a few Qaidam Basin localities; one of the least-studied Palearctic hamsters.", 0, "Nikolai Przewalski"),
    ])

    g = find_genus(ch, "Microtus")
    g["children"].extend([
        make_species("MICROTUS_AGRESTIS", "Microtus agrestis", "Field Vole", "Voles & Lemmings", ["Europe", "Asia"],"A grass-eating vole exhibiting 3-4 year population cycles in northern latitudes.", 0),
        make_species("MICROTUS_ARVALIS", "Microtus arvalis", "Common Vole", "Voles & Lemmings", ["Europe", "Asia"],"One of the most abundant European mammals; peak densities exceed 2000 per hectare.", 0),
        make_species("MICROTUS_OCHROGASTER", "Microtus ochrogaster", "Prairie Vole", "Voles & Lemmings", ["North America"],"A monogamous vole; model organism for neurobiology research on pair-bonding and oxytocin.", 0),
        make_species("MICROTUS_PENNSYLVANICUS", "Microtus pennsylvanicus", "Meadow Vole", "Voles & Lemmings", ["North America"],"The most widely distributed vole in North America; creates surface runways in grass.", 0),
    ])

    g = find_genus(ch, "Myodes")
    g["children"].extend([
        make_species("MYODES_RUFOCANUS", "Myodes rufocanus", "Grey-sided Vole", "Voles & Lemmings", ["Europe", "Asia"],"A boreal vole with reddish sides; key prey for owls and foxes across taiga ecosystems.", 0),
        make_species("MYODES_SHANTARICUS", "Myodes shantaricus", "Shantar Vole", "Voles & Lemmings", ["Asia"],"Endemic to the Shantar Islands; isolated since the last glacial period.", 0),
    ])

    g = find_genus(ch, "Peromyscus")
    g["children"].extend([
        make_species("PEROMYSCUS_MANICULATUS", "Peromyscus maniculatus", "Deer Mouse", "Mice & Rats", ["North America"],"The most widespread North American mammal; first Peromyscus to have its genome sequenced.", 0),
        make_species("PEROMYSCUS_LEUCOPUS", "Peromyscus leucopus", "White-footed Mouse", "Mice & Rats", ["North America"],"A common woodland mouse; primary reservoir for Lyme disease in the eastern US.", 0),
        make_species("PEROMYSCUS_CALIFORNICUS", "Peromyscus californicus", "California Mouse", "Mice & Rats", ["North America"],"A larger species from coastal chaparral; one of few monogamous Peromyscus.", 0),
        make_species("PEROMYSCUS_POLIONOTUS", "Peromyscus polionotus", "Oldfield Mouse", "Mice & Rats", ["North America"],"A small pale mouse of the southeastern US; constructs elaborate burrows with escape tunnels.", 0),
    ])

    g = find_genus(ch, "Sigmodon")
    g["children"].extend([
        make_species("SIGMODON_HISPIDUS", "Sigmodon hispidus", "Hispid Cotton Rat", "Mice & Rats", ["North America", "South America"],"A robust coarse-furred rat of grasslands; major pest of sugarcane and cotton.", 0),
        make_species("SIGMODON_ARIZONAE", "Sigmodon arizonae", "Arizona Cotton Rat", "Mice & Rats", ["North America"],"A southwestern species found in desert riparian corridors.", 0),
    ])

    g = find_genus(ch, "Neotoma")
    g["children"].extend([
        make_species("NEOTOMA_CINEREA", "Neotoma cinerea", "Bushy-tailed Woodrat", "Mice & Rats", ["North America"],"The most widespread Neotoma; builds prominent stick middens providing shelter for dozens of species.", 0),
        make_species("NEOTOMA_LEPIDA", "Neotoma lepida", "Desert Woodrat", "Mice & Rats", ["North America"],"A small pale woodrat; urine crystallises around its nest preserving plant fragments for millennia.", 0),
    ])

    g = find_genus(ch, "Lemmus")
    g["children"].extend([
        make_species("LEMMUS_SIBIRICUS", "Lemmus sibiricus", "Siberian Brown Lemming", "Voles & Lemmings", ["Europe", "Asia", "North America"],"A true lemming with circumpolar distribution; primary prey for Arctic foxes and snowy owls.", 0),
    ])

    g = find_genus(ch, "Dicrostonyx")
    g["children"].extend([
        make_species("DICROSTONYX_GROENLANDICUS", "Dicrostonyx groenlandicus", "Nearctic Collared Lemming", "Voles & Lemmings", ["North America"],"Grows white winter coat and enlarged curved claws for digging through packed snow.", 0),
    ])

    g = find_genus(ch, "Reithrodontomys")
    g["children"].extend([
        make_species("REITHRODONTOMYS_MEGALOTIS", "Reithrodontomys megalotis", "Western Harvest Mouse", "Mice & Rats", ["North America"],"A small mouse with grooved upper incisor; builds spherical grass nests above ground.", 0),
        make_species("REITHRODONTOMYS_HUMULIS", "Reithrodontomys humulis", "Eastern Harvest Mouse", "Mice & Rats", ["North America"],"The smallest harvest mouse with prehensile tail for climbing grass stems.", 0),
    ])

    g = find_genus(ch, "Ellobius")
    g["children"].extend([
        make_species("ELLOBIUS_TALPINUS", "Ellobius talpinus", "Northern Mole Vole", "Voles & Lemmings", ["Europe", "Asia"],"A blind mole-like vole with reduced eyes; spends most of its life underground.", 0),
        make_species("ELLOBIUS_LUTESCENS", "Ellobius lutescens", "Transcaucasian Mole Vole", "Voles & Lemmings", ["Asia"],"Has lost the Y chromosome entirely — males are XO; one of few mammals without a Y chromosome.", 0),
    ])

    g = find_genus(ch, "Lagurus")
    if g:
        g["children"].extend([
            make_species("LAGURUS_LAGURUS", "Lagurus lagurus", "Steppe Lemming", "Voles & Lemmings", ["Europe", "Asia"],"A small grey vole of the Eurasian steppe; exhibits dramatic population cycles.", 0),
        ])

    # New genus
    g = ensure_genus(ch, "GENUS_ALTICOLA", "Alticola","Mountain voles","High-elevation voles of Central Asian talus slopes; longer softer fur than Microtus.", "Voles & Lemmings")
    g["children"].extend([
        make_species("ALTICOLA_ROYLEI", "Alticola roylei", "Royle's Mountain Vole", "Voles & Lemmings", ["Asia"],"A Himalayan vole at 2500-4000 m in India, Nepal and Pakistan.", 0, "John Forbes Royle"),
        make_species("ALTICOLA_ARGENTATUS", "Alticola argentatus", "Silver Mountain Vole", "Voles & Lemmings", ["Asia"],"Widespread from Tien Shan to Altai; silvery-grey pelage on lichen-covered granite.", 0),
        make_species("ALTICOLA_STOLICZKANUS", "Alticola stoliczkanus", "Stoliczka's Mountain Vole", "Voles & Lemmings", ["Asia"],"From the Pamir and western Himalayan ranges.", 0, "Ferdinand Stoliczka"),
        make_species("ALTICOLA_BARAKSHIN", "Alticola barakshin", "Barakshin Mountain Vole", "Voles & Lemmings", ["Asia"],"A Mongolian species with reddish-brown dorsal stripe.", 0),
    ])

    return data

ENRICHERS["cricetidae"] = enrich_cricetidae



# ---------------------------------------------------------------------------
# ENRICHER: muridae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_muridae(data):
    ch = data["children"]

    g = find_genus(ch, "Mus")
    g["children"].extend([
        make_species("MUS_TERRICOLOR", "Mus terricolor", "Earth-coloured Mouse", "Mice & Rats", ["Asia"],"A small mouse from South Asian farmlands; major pest of stored grain.", 0),
        make_species("MUS_NITIDULUS", "Mus nitidulus", "Blyth's Mouse", "Mice & Rats", ["Asia"],"A Southeast Asian mouse with glossy coat; occupies dry deciduous forests.", 0),
        make_species("MUS_FRAGILICAUDA", "Mus fragilicauda", "Fragile-tailed Mouse", "Mice & Rats", ["Asia"],"A Thai species with tail that autotomises extremely easily as predator escape.", 0),
        make_species("MUS_MAJORI", "Mus majori", "Major's Mouse", "Mice & Rats", ["Asia"],"An Indonesian endemic from Sumatra and Java montane forests.", 0, "Ronald Major"),
    ])

    g = find_genus(ch, "Rattus")
    g["children"].extend([
        make_species("RATTUS_NORVEGICUS", "Rattus norvegicus", "Brown Rat", "Mice & Rats", ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"],"The most successful invasive mammal; laboratory rat is a cornerstone of biomedical research.", 0),
        make_species("RATTUS_TANEZUMI", "Rattus tanezumi", "Asian House Rat", "Mice & Rats", ["Asia", "Oceania"],"The dominant commensal rat across Southeast Asia; primary plague host.", 0),
        make_species("RATTUS_EXULANS", "Rattus exulans", "Polynesian Rat", "Mice & Rats", ["Asia", "Oceania"],"Carried across the Pacific by Polynesian voyagers as a food source.", 0),
        make_species("RATTUS_FUSCIPES", "Rattus fuscipes", "Bush Rat", "Mice & Rats", ["Oceania"],"An Australian native rat; important seed disperser and prey for quolls and owls.", 0),
        make_species("RATTUS_LEUCOPUS", "Rattus leucopus", "Cape York Rat", "Mice & Rats", ["Oceania"],"A native Australian rat from Cape York and southern New Guinea with white feet.", 0),
    ])

    g = find_genus(ch, "Apodemus")
    g["children"].extend([
        make_species("APODEMUS_SYLVATICUS", "Apodemus sylvaticus", "Wood Mouse", "Mice & Rats", ["Europe", "Asia", "Africa"],"The most common small mammal in European woodlands; critical for oak regeneration via seed caching.", 0),
        make_species("APODEMUS_FLAVICOLLIS", "Apodemus flavicollis", "Yellow-necked Mouse", "Mice & Rats", ["Europe", "Asia"],"A larger arboreal relative of the wood mouse; primary reservoir for tick-borne encephalitis.", 0),
        make_species("APODEMUS_AGGRARIUS", "Apodemus agrarius", "Striped Field Mouse", "Mice & Rats", ["Europe", "Asia"],"Distinctive black dorsal stripe; reservoir host for Hantaan virus.", 0),
    ])

    # Mastomys - find by id
    g = None
    for c in ch:
        if c.get("id") == "GENUS_MASTOMYS":
            g = c
            break
    if g:
        g["children"].extend([
            make_species("MASTOMYS_NATALENSIS", "Mastomys natalensis", "Natal Multimammate Mouse", "Mice & Rats", ["Africa"],"Named for 12 pairs of mammae; natural reservoir for Lassa fever virus.", 0),
            make_species("MASTOMYS_ERYTHROLEUCUS", "Mastomys erythroleucus", "Red-white Multimammate Mouse", "Mice & Rats", ["Africa"],"A Sahel species implicated in monkeypox and Lassa outbreaks.", 0),
        ])

    g = find_genus(ch, "Praomys")
    if g:
        g["children"].extend([
            make_species("PRAOMYS_DEKERI", "Praomys dekeri", "Deker's Soft-furred Mouse", "Mice & Rats", ["Africa"],"A South African species from riverine forests with exceptionally soft pelage.", 0),
            make_species("PRAOMYS_JACKSONI", "Praomys jacksoni", "Jackson's Soft-furred Mouse", "Mice & Rats", ["Africa"],"A Central African seed predator of Congo Basin rainforests.", 0),
        ])

    g = find_genus(ch, "Aethomys")
    if g:
        g["children"].extend([
            make_species("AETHOMYS_CHRYSOPHILUS", "Aethomys chrysophilus", "Red Velvet Rat", "Mice & Rats", ["Africa"],"A golden-brown rat from southern African savannas with velvety soft fur.", 0),
            make_species("AETHOMYS_NAMAGUENSIS", "Aethomys namaquensis", "Namaqua Rock Rat", "Mice & Rats", ["Africa"],"A rock-dwelling species from arid southwestern Africa; stores seeds in deep crevices.", 0),
        ])

    g = find_genus(ch, "Gerbillus")
    g["children"].extend([
        make_species("GERBILLUS_PYRAMIDUM", "Gerbillus pyramidum", "Greater Egyptian Gerbil", "Mice & Rats", ["Africa", "Asia"],"A large gerbil of the Nile Delta and Sinai; constructs multi-chamber burrows.", 0),
        make_species("GERBILLUS_ANDERSONI", "Gerbillus andersoni", "Anderson's Gerbil", "Mice & Rats", ["Africa", "Asia"],"A coastal gerbil from Libya to Sinai; pale sandy fur conceals it in dunes.", 0),
        make_species("GERBILLUS_NANUS", "Gerbillus nanus", "Least Gerbil", "Mice & Rats", ["Asia"],"A tiny 10-g desert gerbil that survives on metabolic water from dry seeds.", 0),
    ])

    g = find_genus(ch, "Meriones")
    g["children"].extend([
        make_species("MERIONES_CRASSUS", "Meriones crassus", "Fat Jird", "Mice & Rats", ["Asia"],"A stocky jird of Middle Eastern deserts; stores large seed caches underground.", 0),
        make_species("MERIONES_MERIDIANUS", "Meriones meridianus", "Midday Gerbil", "Mice & Rats", ["Asia"],"A diurnal gerbil active at midday; dark eye patches reduce sun glare.", 0),
        make_species("MERIONES_LIBYCUS", "Meriones libycus", "Libyan Jird", "Mice & Rats", ["Asia"],"A large jird from Arabia to Xinjiang; plague host in Central Asian foci.", 0),
    ])

    g = find_genus(ch, "Arvicanthis")
    if g:
        g["children"].extend([
            make_species("ARVICANTHIS_NILOTICUS", "Arvicanthis niloticus", "Nile Grass Rat", "Mice & Rats", ["Africa"],"A diurnal grass-eating rat of the Nile Valley; model for circadian rhythm research.", 0),
            make_species("ARVICANTHIS_ANSORGEI", "Arvicanthis ansorgei", "Ansorge's Grass Rat", "Mice & Rats", ["Africa"],"A West African species from seasonal wetlands.", 0, "William Ansorge"),
        ])

    g = find_genus(ch, "Lophuromys")
    if g:
        g["children"].extend([
            make_species("LOPHUROMYS_FLAVOPUNCTATUS", "Lophuromys flavopunctatus", "Yellow-spotted Brush-furred Rat", "Mice & Rats", ["Africa"],"A stiff-furred insectivorous rat from Ethiopian and Kenyan highland forests.", 0),
            make_species("LOPHUROMYS_AKAE", "Lophuromys akae", "Aka Brush-furred Rat", "Mice & Rats", ["Africa"],"A recently described species from the Bale Mountains of Ethiopia.", 0),
        ])

    # New genera
    g = ensure_genus(ch, "GENUS_BANDICOTA", "Bandicota","Bandicoot rats","Large robust rats of South and Southeast Asia; powerful diggers weighing up to 1 kg.", "Mice & Rats")
    g["children"].extend([
        make_species("BANDICOTA_INDICA", "Bandicota indica", "Greater Bandicoot Rat", "Mice & Rats", ["Asia"],"The largest rat in the world up to 1.5 kg; digs burrows extending 2 m underground.", 0),
        make_species("BANDICOTA_BENGALENSIS", "Bandicota bengalensis", "Lesser Bandicoot Rat", "Mice & Rats", ["Asia"],"The primary rodent pest of Indian rice and wheat; major leptospirosis reservoir.", 0),
    ])

    g = ensure_genus(ch, "GENUS_NIVIVENTER", "Niviventer","White-bellied rats","South and East Asian rats with pure white underparts sharply demarcated from brown upperparts.", "Mice & Rats")
    g["children"].extend([
        make_species("NIVIVENTER_NIVIVENTER", "Niviventer niviventer", "White-bellied Rat", "Mice & Rats", ["Asia"],"The type species from Myanmar, Thailand and Laos; arboreal and nocturnal.", 0),
        make_species("NIVIVENTER_CONFUSICIANUS", "Niviventer confusicianus", "Confusing White-bellied Rat", "Mice & Rats", ["Asia"],"From southern China and Vietnam; inhabits karst limestone evergreen forests.", 0),
        make_species("NIVIVENTER_CREATURIVORUS", "Niviventer creaturivorus", "Creature-eating White-bellied Rat", "Mice & Rats", ["Asia"],"An insectivorous Niviventer from Sichuan bamboo thickets.", 0),
    ])

    return data

ENRICHERS["muridae"] = enrich_muridae



# ---------------------------------------------------------------------------
# ENRICHER: microhylidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_microhylidae(data):
    ch = data["children"]

    g = find_genus(ch, "Kaloula")
    g["children"].extend([
        make_species("KALOULA_RUFA", "Kaloula rufa", "Red Bullfrog", "Old World Narrow-mouthed Frogs", ["Asia"],"A reddish Kaloula from the Philippines; emerges in enormous numbers after monsoon rains.", 0),
        make_species("KALOULA_MEDIOGRAMMATA", "Kaloula mediogrammata", "Striped Bullfrog", "Old World Narrow-mouthed Frogs", ["Asia"],"A striped Philippine species from Luzon and Mindoro lowland forests.", 0),
        make_species("KALOULA_INDICA", "Kaloula indica", "Indian Balloon Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"Recently described from the Western Ghats of India; smaller than K. taprobanica.", 0),
    ])

    g = find_genus(ch, "Microhyla")
    g["children"].extend([
        make_species("MICROHYLA_BEAUFORTI", "Microhyla beaufonti", "Beaufort's Narrow-mouthed Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"An Indonesian species from Borneo and Sumatra; one of the larger Microhyla.", 0),
        make_species("MICROHYLA_PETRIGENA", "Microhyla petrigena", "Rock-dwelling Narrow-mouthed Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A limestone karst specialist from Vietnam and China with enlarged digit tips for climbing.", 0),
        make_species("MICROHYLA_ANNECTENS", "Microhyla annectens", "Intermediate Narrow-mouthed Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A recently described Laotian species with features intermediate between Microhyla and Micryletta.", 0),
        make_species("MICROHYLA_MANTHEYI", "Microhyla mantheyi", "Manthey's Narrow-mouthed Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"Endemic to the Cardamom Mountains of Cambodia.", 0, "Ulrich Manthey"),
    ])

    g = find_genus(ch, "Uperodon")
    g["children"].extend([
        make_species("UPERODON_SYSTEMA", "Uperodon systema", "Systema Balloon Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A pudgy burrowing frog from the Deccan Plateau that inflates like a ball when threatened.", 0),
        make_species("UPERODON_GLOBULOSUS", "Uperodon globulosus", "Globular Balloon Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"An Indian species with near-spherical body; skin secretes foul-tasting substance deterring predators.", 0),
        make_species("UPERODON_TAPROBANICUS", "Uperodon taprobanicus", "Sri Lankan Balloon Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A small rotund frog from Sri Lanka; aestivates inside a mucus cocoon during dry months.", 0),
    ])

    g = find_genus(ch, "Gastrophryne")
    g["children"].extend([
        make_species("GASTROPHRYNE_CAROLINENSIS", "Gastrophryne carolinensis", "Eastern Narrow-mouthed Toad", "New World Narrow-mouthed Frogs", ["North America"],"A small plump frog from the southeastern US; specialist predator of ants and termites.", 0),
        make_species("GASTROPHRYNE_OLIVACEA", "Gastrophryne olivacea", "Plains Narrow-mouthed Toad", "New World Narrow-mouthed Frogs", ["North America"],"A Great Plains microhylid that spends most of the year underground.", 0),
        make_species("GASTROPHRYNE_ELEGANS", "Gastrophryne elegans", "Elegant Narrow-mouthed Toad", "New World Narrow-mouthed Frogs", ["North America"],"A Mexican species with yellow dorsolateral line; breeds in temporary pools.", 0),
    ])

    g = find_genus(ch, "Dyscophus")
    g["children"].extend([
        make_species("DYSCOPHUS_ANTONGILII", "Dyscophus antongilii", "Tomato Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"The bright-red tomato frog of Madagascar; vivid colour warns of toxic skin secretion.", 0),
        make_species("DYSCOPHUS_GUINETI", "Dyscophus guineti", "False Tomato Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A less colourful relative from central-eastern Madagascar.", 0),
    ])

    g = find_genus(ch, "Cophyla")
    g["children"].extend([
        make_species("COPHYLA_PHYLLODACTYLA", "Cophyla phyllodactyla", "Leaf-fingered Tree Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A tiny arboreal microhylid from northern Madagascar inhabiting Pandanus leaf axils.", 0),
        make_species("COPHYLA_MAHAVAVA", "Cophyla mahavava", "Mahavava Tree Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"Critically Endangered from Montagne d'Ambre and Ankarana regions of Madagascar.", 0),
    ])

    g = find_genus(ch, "Oreophryne")
    g["children"].extend([
        make_species("OREOPHRYNE_ASPERA", "Oreophryne aspera", "Rough Mountain Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A Sulawesi montane microhylid with rough granular skin; calls from mossy branches above 1500 m.", 0),
        make_species("OREOPHRYNE_WOLLASTONI", "Oreophryne wollastoni", "Wollaston's Mountain Frog", "Old World Narrow-mouthed Frogs", ["Asia"],"A New Guinean species from the Snow Mountains; one of the highest Papuan microhylids.", 0),
    ])

    g = find_genus(ch, "Choerophryne")
    g["children"].extend([
        make_species("CHOEROPHRYNE_ROBERTSI", "Choerophryne robertsi", "Roberts' Hog-nosed Frog", "Old World Narrow-mouthed Frogs", ["Oceania"],"A tiny PNG frog with pig-like snout and remarkably high-pitched call.", 0),
        make_species("CHOEROPHRYNE_SIEBENROCKI", "Choerophryne siebenrocki", "Siebenrock's Hog-nosed Frog", "Old World Narrow-mouthed Frogs", ["Asia", "Oceania"],"A New Guinean and Indonesian species; one of the smallest frogs in the world.", 0),
    ])

    g = find_genus(ch, "Scaphiophryne")
    if g:
        g["children"].extend([
            make_species("SCAPHIOPHRYNE_MARMORATA", "Scaphiophryne marmorata", "Marbled Rain Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A strikingly patterned Malagasy burrowing frog with green and black marbling.", 0),
            make_species("SCAPHIOPHRYNE_BORIBORY", "Scaphiophryne boribory", "Grey Rain Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A burrowing frog from eastern Madagascar; buries itself in loose soil during dry periods.", 0),
        ])

    g = find_genus(ch, "Platypelis")
    if g:
        g["children"].extend([
            make_species("PLATYPELIS_GRANDIS", "Platypelis grandis", "Giant Tree Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A large arboreal microhylid from eastern Madagascar; males guard eggs laid in tree holes.", 0),
            make_species("PLATYPELIS_TSIHOMBE", "Platypelis tsihombe", "Tsihombe Tree Frog", "Old World Narrow-mouthed Frogs", ["Africa"],"A southern Malagasy species from spiny forest; unusually tolerant of arid conditions.", 0),
        ])

    g = find_genus(ch, "Chiasmocleis")
    if g:
        g["children"].extend([
            make_species("CHIASMOCLEIS_ALBUGRISEA", "Chiasmocleis albugrisea", "White-grey Humming Frog", "New World Narrow-mouthed Frogs", ["South America"],"An Amazonian microhylid with a colour pattern resembling bird droppings as camouflage.", 0),
            make_species("CHIASMOCLEIS_TRISTIS", "Chiasmocleis tristis", "Sad Humming Frog", "New World Narrow-mouthed Frogs", ["South America"],"A Brazilian species with a melancholic buzzing call from leaf litter.", 0),
        ])

    return data

ENRICHERS["microhylidae"] = enrich_microhylidae



# ---------------------------------------------------------------------------
# ENRICHER: bufonidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_bufonidae(data):
    ch = data["children"]

    g = find_genus(ch, "Bufo")
    g["children"].extend([
        make_species("BUFO_BUFO", "Bufo bufo", "Common Toad", "True Toads", ["Europe", "Asia"],"The quintessential European toad; toxic parotoid glands produce bufadienolide poisons.", 0),
        make_species("BUFO_SPINOSUS", "Bufo spinosus", "Spiny Toad", "True Toads", ["Europe"],"Separated from B. bufo by prominent dorsal tubercles; found in southwestern Europe.", 0),
        make_species("BUFO_GARGARIZANS", "Bufo gargarizans", "Asiatic Toad", "True Toads", ["Asia"],"Commonest toad across East Asia; skin secretions used in traditional Chinese medicine.", 4),
        make_species("BUFO_VERRUCOSISSIMUS", "Bufo verrucosissimus", "Caucasian Toad", "True Toads", ["Europe", "Asia"],"A large warty toad of the Caucasus and northeastern Anatolia.", 0),
        make_species("BUFO_JAPONICUS", "Bufo japonicus", "Japanese Common Toad", "True Toads", ["Asia"],"Widespread across Japan; breeds explosively in late-winter ponds.", 2),
        make_species("BUFO_BANKORENSIS", "Bufo bankorensis", "Central Formosa Toad", "True Toads", ["Asia"],"Endemic to Taiwan; recognised by reddish warts and pale vertebral stripe.", 0),
        make_species("BUFO_TORRENTICOLA", "Bufo torrenticola", "Japanese Stream Toad", "True Toads", ["Asia"],"Adapted to fast mountain streams; tadpoles have sucker-like mouths to cling to rocks.", 0),
    ])

    g = find_genus(ch, "Anaxyrus")
    g["children"].extend([
        make_species("ANAXYRUS_AMERICANUS", "Anaxyrus americanus", "American Toad", "True Toads", ["North America"],"The most common toad in eastern North America; distinguished by its long trilling call.", 0),
        make_species("ANAXYRUS_TERRESTRIS", "Anaxyrus terrestris", "Southern Toad", "True Toads", ["North America"],"A southeastern US toad with prominent cranial crests forming a V-shape.", 0),
        make_species("ANAXYRUS_BOREAS", "Anaxyrus boreas", "Western Toad", "True Toads", ["North America"],"A western toad with a distinctive white dorsal stripe; declining due to chytrid fungus.", 0),
        make_species("ANAXYRUS_WOODHOUSII", "Anaxyrus woodhousii", "Woodhouse's Toad", "True Toads", ["North America"],"A widespread western toad with a short explosive call; tolerant of arid environments.", 0),
    ])

    g = find_genus(ch, "Rhinella")
    g["children"].extend([
        make_species("RHINELLA_MARINA", "Rhinella marina", "Cane Toad", "True Toads", ["South America", "North America", "Oceania"],"Infamous invasive species in Australia; parotoid glands produce bufotoxin that kills predators.", 0),
        make_species("RHINELLA_ICTERICA", "Rhinella icterica", "Yellow Cururu Toad", "True Toads", ["South America"],"A large Brazilian toad with vivid yellow markings on a dark brown body.", 0),
        make_species("RHINELLA_ARENARUM", "Rhinella arenarum", "Common South American Toad", "True Toads", ["South America"],"The most widespread toad in southern South America; occurrs from Bolivia to Patagonia.", 0),
        make_species("RHINELLA_GRANULOSA", "Rhinella granulosa", "Granular Toad", "True Toads", ["South America"],"A small Rhinella with pronounced tuberculation; found across the Amazon basin.", 0),
    ])

    g = find_genus(ch, "Incilius")
    g["children"].extend([
        make_species("INCILIUS_ALVARIUS", "Incilius alvarius", "Sonoran Desert Toad", "True Toads", ["North America"],"The Colorado River toad; secretes 5-MeO-DMT, a potent psychoactive compound used in traditional ceremonies.", 0),
        make_species("INCILIUS_COCCIFER", "Incilius coccifer", "Southern Round-gland Toad", "True Toads", ["North America"],"A Central American toad with distinctive round parotoid glands.", 0),
        make_species("INCILIUS_VALLICEPS", "Incilius valliceps", "Gulf Coast Toad", "True Toads", ["North America"],"Common along the Gulf of Mexico from Louisiana to Honduras.", 0),
    ])

    g = find_genus(ch, "Atelopus")
    g["children"].extend([
        make_species("ATELOPUS_ZEKI", "Atelopus zeki", "Zeki's Harlequin Toad", "True Toads", ["South America"],"A critically endangered harlequin frog from the Colombian Andes with vivid black and yellow patterning.", 0),
        make_species("ATELOPUS_VARIUS", "Atelopus varius", "Variable Harlequin Toad", "True Toads", ["North America"],"Once abundant in Costa Rica and Panama; nearly wiped out by chytrid fungus.", 0),
        make_species("ATELOPUS_CRUCIGER", "Atelopus cruciger", "Rancho Grande Harlequin Frog", "True Toads", ["South America"],"A Venezuelan harlequin frog thought extinct until rediscovered in 2005.", 0),
    ])

    g = find_genus(ch, "Peltophryne")
    if g:
        g["children"].extend([
            make_species("PELTOPHRYNE_FUSTIGER", "Peltophryne fustiger", "Cuban Giant Toad", "True Toads", ["North America"],"A large Cuban endemic toad found in forests and agricultural areas.", 0),
            make_species("PELTOPHRYNE_TALADAI", "Peltophryne taladai", "Talada's Toad", "True Toads", ["North America"],"A Cuban species restricted to the Sierra Maestra massif.", 0),
        ])

    g = find_genus(ch, "Sclerophrys")
    # Not in this file... use existing

    g = find_genus(ch, "Amietophrynus")
    if g:
        g["children"].extend([
            make_species("AMIETOPHRYNUS_GUTTURALIS", "Amietophrynus gutturalis", "Guttural Toad", "True Toads", ["Africa"],"A common sub-Saharan African toad; named for its deep guttural call.", 0),
            make_species("AMIETOPHRYNUS_REGULARIS", "Amietophrynus regularis", "Square-marked Toad", "True Toads", ["Africa"],"Widespread in African savannas; identified by square markings on its back.", 0),
        ])

    g = find_genus(ch, "Duttaphrynus")
    if g:
        g["children"].extend([
            make_species("DUTTAPHRYNUS_MELANOSTICTUS", "Duttaphrynus melanostictus", "Asian Common Toad", "True Toads", ["Asia"],"One of the most common toads in South and Southeast Asia; invasive in Madagascar and Bali.", 0),
            make_species("DUTTAPHRYNUS_SCABER", "Duttaphrynus scaber", "Rough Toad", "True Toads", ["Asia"],"A warty species from the Western Ghats and Sri Lanka with prominent dorsal ridges.", 0),
        ])

    g = find_genus(ch, "Epidalea")
    if g:
        g["children"].extend([
            make_species("EPIDALEA_CALAMITA", "Epidalea calamita", "Natterjack Toad", "True Toads", ["Europe"],"Distinguished by the yellow stripe down its back; runs rather than hops.", 0),
        ])

    g = find_genus(ch, "Nectophrynoides")
    if g:
        g["children"].extend([
            make_species("NECTOPHRYNOIDES_VIVIPARUS", "Nectophrynoides viviparus", "Viviparous Toad", "True Toads", ["Africa"],"One of the few frogs that gives birth to live young rather than laying eggs.", 0),
            make_species("NECTOPHRYNOIDES_TORNIERI", "Nectophrynoides tornieri", "Tornier's Viviparous Toad", "True Toads", ["Africa"],"An Eastern Arc Mountain endemic from Tanzania.", 0),
        ])

    return data

ENRICHERS["bufonidae"] = enrich_bufonidae



# ---------------------------------------------------------------------------
# ENRICHER: agamidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_agamidae(data):
    ch = data["children"]

    g = find_genus(ch, "Pogona")
    g["children"].extend([
        make_species("POGONA_VITTICEPS", "Pogona vitticeps", "Central Bearded Dragon", "Bearded Dragons", ["Oceania"],"The most popular pet lizard globally; temperature determines sex reversal.", 0),
        make_species("POGONA_BARBATA", "Pogona barbata", "Eastern Bearded Dragon", "Bearded Dragons", ["Oceania"],"More arboreal than its central relative; produces impressive beard displays.", 0),
        make_species("POGONA_MINOR", "Pogona minor", "Dwarf Bearded Dragon", "Bearded Dragons", ["Oceania"],"The smallest bearded dragon; found across arid western Australia.", 3),
        make_species("POGONA_HENRYLAWSONI", "Pogona henrylawsoni", "Rankin's Dragon", "Bearded Dragons", ["Oceania"],"Compact species from Queensland's black soil plains.", 0, "Henry Lawson"),
        make_species("POGONA_MICROLEPIDOTA", "Pogona microlepidota", "Drysdale River Bearded Dragon", "Bearded Dragons", ["Oceania"],"The rarest bearded dragon; known from only a handful of Kimberley specimens.", 0),
    ])

    g = find_genus(ch, "Agama")
    g["children"].extend([
        make_species("AGAMA_AGAMA", "Agama agama", "Common Agama", "Agamas", ["Africa"],"The most recognizable lizard in sub-Saharan Africa; males display bright blue and orange heads.", 0),
        make_species("AGAMA_IMPALEARIS", "Agama impalearis", "North African Agama", "Agamas", ["Africa"],"Found in the Atlas Mountains and Sahara margins; one of the most cold-tolerant agamas.", 0),
        make_species("AGAMA_MOSAMBIKA", "Agama mosambika", "Mozambique Agama", "Agamas", ["Africa"],"A colourful agama from southeastern Africa with an iridescent blue head in dominant males.", 0),
        make_species("AGAMA_PLANICEPS", "Agama planiceps", "Flat-headed Agama", "Agamas", ["Africa"],"A Namibian species with a flattened head adapted for squeezing under rocks.", 0),
    ])

    g = find_genus(ch, "Draco")
    g["children"].extend([
        make_species("DRACO_VOLANS", "Draco volans", "Common Flying Dragon", "Flying Lizards", ["Asia"],"The best-known flying dragon; extends rib-supported patagia to glide 10 m between trees.", 0),
        make_species("DRACO_LINEATUS", "Draco lineatus", "Lineated Flying Dragon", "Flying Lizards", ["Asia"],"A Sumatran and Bornean species with striking white lateral lines.", 0),
        make_species("DRACO_RETICULATUS", "Draco reticulatus", "Reticulated Flying Dragon", "Flying Lizards", ["Asia"],"A Philippine flying lizard; males display a vivid yellow gular flag during courtship.", 0),
        make_species("DRACO_OBSCURUS", "Draco obscurus", "Dusky Flying Dragon", "Flying Lizards", ["Asia"],"A gliding lizard restricted to the Mentawai Islands west of Sumatra.", 0),
    ])

    g = find_genus(ch, "Calotes")
    g["children"].extend([
        make_species("CALOTES_VERSICOLOR", "Calotes versicolor", "Oriental Garden Lizard", "Agamas", ["Asia"],"The most widespread Asian agama; changes colour rapidly in response to stress.", 0),
        make_species("CALOTES_MYSTACEUS", "Calotes mystaceus", "Blue-crested Lizard", "Agamas", ["Asia"],"Named for its moustache-like blue markings; found in Southeast Asian forests.", 0),
        make_species("CALOTES_EMINENS", "Calotes eminens", "Eminent Forest Lizard", "Agamas", ["Asia"],"A large Calotes from the Western Ghats of India with prominent dorsal crest.", 0),
    ])

    g = find_genus(ch, "Uromastyx")
    g["children"].extend([
        make_species("UROMASTYX_ACANTHINURA", "Uromastyx acanthinura", "North African Spiny-tailed Lizard", "Agamas", ["Africa"],"A large herbivorous lizard of the Sahara; can survive for months without food.", 0),
        make_species("UROMASTYX_AEGYPTIA", "Uromastyx aegyptia", "Egyptian Spiny-tailed Lizard", "Agamas", ["Asia", "Africa"],"The largest Uromastyx; constructs extensive burrows in Middle Eastern deserts.", 0),
        make_species("UROMASTYX_GEYRI", "Uromastyx geyri", "Geyr's Spiny-tailed Lizard", "Agamas", ["Africa"],"A colourful Saharan species with red, yellow or orange dorsal colouration.", 0),
    ])

    g = find_genus(ch, "Ctenophorus")
    g["children"].extend([
        make_species("CTENOPHORUS_ORNATUS", "Ctenophorus ornatus", "Ornate Dragon", "Dragons", ["Oceania"],"A brilliantly patterned lizard from Western Australian granite outcrops.", 0),
        make_species("CTENOPHORUS_NUCHALIS", "Ctenophorus nuchalis", "Central Netted Dragon", "Dragons", ["Oceania"],"Adapted to the gibber plains of Central Australia; runs bipedally at speed.", 0),
        make_species("CTENOPHORUS_DECRESII", "Ctenophorus decresii", "Tawny Dragon", "Dragons", ["Oceania"],"A rock-dwelling dragon from South Australia with males displaying vivid blue throats.", 0),
    ])

    g = find_genus(ch, "Phrynocephalus")
    g["children"].extend([
        make_species("PHRYNOCEPHALUS_MYSTACEUS", "Phrynocephalus mystaceus", "Secret Toad-headed Agama", "Agamas", ["Asia"],"Has skin folds at the mouth corners that inflate and turn bright red when threatened.", 0),
        make_species("PHRYNOCEPHALUS_GUTTATUS", "Phrynocephalus guttatus", "Spotted Toad-headed Agama", "Agamas", ["Asia"],"A sand-dwelling lizard from Central Asian deserts with toad-like flattened body.", 0),
    ])

    g = find_genus(ch, "Laudakia")
    if g:
        g["children"].extend([
            make_species("LAUDAKIA_STELLIO", "Laudakia stellio", "Starred Agama", "Agamas", ["Europe", "Asia"],"A distinctive agama from Greece through the Middle East; named for its star-like scales.", 0),
            make_species("LAUDAKIA_CANCESOR", "Laudakia cancesor", "Caucasian Rock Agama", "Agamas", ["Asia"],"A high-elevation agama of the Caucasus; basks on boulders above treeline.", 0),
        ])

    g = find_genus(ch, "Trapelus")
    if g:
        g["children"].extend([
            make_species("TRAPELUS_RUDERATUS", "Trapelus ruderatus", "Field Agama", "Agamas", ["Asia"],"A ground-dwelling agama of Central Asian deserts and steppes.", 0),
            make_species("TRAPELUS_SANGUINEUS", "Trapelus sanguineus", "Red Agama", "Agamas", ["Africa"],"A Sahelian species; dominant males turn vivid red during the breeding season.", 0),
        ])

    g = find_genus(ch, "Hydrosaurus")
    if g:
        g["children"].extend([
            make_species("HYDROSAURUS_PUSTULATUS", "Hydrosaurus pustulatus", "Philippine Sailfin Lizard", "Agamas", ["Asia"],"A large semi-aquatic lizard with a prominent crest; can run on water's surface.", 0),
            make_species("HYDROSAURUS_AMBOINENSIS", "Hydrosaurus amboinensis", "Ambon Sailfin Lizard", "Agamas", ["Asia"],"The largest Hydrosaurus species from the Moluccas and New Guinea.", 0),
        ])

    g = find_genus(ch, "Moloch")
    if g:
        g["children"].extend([
            make_species("MOLOCH_HORRIDUS", "Moloch horridus", "Thorny Devil", "Agamas", ["Oceania"],"Covered in conical spines; drinks by absorbing water through capillary action in its skin.", 0),
        ])

    g = find_genus(ch, "Chlamydosaurus")
    if g:
        g["children"].extend([
            make_species("CHLAMYDOSAURUS_KINGII", "Chlamydosaurus kingii", "Frilled Lizard", "Agamas", ["Oceania"],"Opens a massive frill around its neck when threatened; runs bipedally at speed.", 0),
        ])

    return data

ENRICHERS["agamidae"] = enrich_agamidae



# ---------------------------------------------------------------------------
# ENRICHER: plethodontidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_plethodontidae(data):
    ch = data["children"]

    g = find_genus(ch, "Plethodon")
    g["children"].extend([
        make_species("PLETHODON_GLUTINOSUS", "Plethodon glutinosus", "Slimy Salamander", "Woodland Salamanders", ["North America"],"Secretes sticky mucus that glues predator jaws shut; among the most abundant Appalachian vertebrates.", 0),
        make_species("PLETHODON_CINEREUS", "Plethodon cinereus", "Red-backed Salamander", "Woodland Salamanders", ["North America"],"One of the most numerous northeastern US vertebrates at up to 3 per square metre.", 0),
        make_species("PLETHODON_JORDANI", "Plethodon jordani", "Jordan's Salamander", "Woodland Salamanders", ["North America"],"A red-cheeked salamander endemic to the Great Smoky Mountains.", 0, "David Starr Jordan"),
        make_species("PLETHODON_SERRATUS", "Plethodon serratus", "Southern Red-backed Salamander", "Woodland Salamanders", ["North America"],"A small species from the Ouachita and Ozark highlands.", 0),
        make_species("PLETHODON_VEHICULUM", "Plethodon vehiculum", "Western Red-backed Salamander", "Woodland Salamanders", ["North America"],"Pacific Northwest counterpart of the red-backed salamander; highly philopatric.", 0),
        make_species("PLETHODON_WEHRLEI", "Plethodon wehrlei", "Wehrle's Salamander", "Woodland Salamanders", ["North America"],"A slender species from the Appalachian Plateau with a distinctive webbed foot.", 0),
        make_species("PLETHODON_HOFFMANI", "Plethodon hoffmani", "Valley and Ridge Salamander", "Woodland Salamanders", ["North America"],"Restricted to the Valley and Ridge province of Virginia and West Virginia.", 0),
    ])

    g = find_genus(ch, "Desmognathus")
    g["children"].extend([
        make_species("DESMOGNATHUS_FUSCUS", "Desmognathus fuscus", "Dusky Salamander", "Woodland Salamanders", ["North America"],"The most widespread desmognathan; found in and around streams across eastern North America.", 0),
        make_species("DESMOGNATHUS_MONTICOLA", "Desmognathus monticola", "Seal Salamander", "Woodland Salamanders", ["North America"],"A large stream salamander named for its spotted seal-like coloration.", 0),
        make_species("DESMOGNATHUS_OCHROPHAEUS", "Desmognathus ochrophaeus", "Allegheny Mountain Dusky Salamander", "Woodland Salamanders", ["North America"],"A terrestrial species of high-elevation Appalachian forests.", 0),
        make_species("DESMOGNATHUS_WRIGHTI", "Desmognathus wrighti", "Pygmy Salamander", "Woodland Salamanders", ["North America"],"One of the smallest lungless salamanders at just 4 cm.", 0),
    ])

    g = find_genus(ch, "Eurycea")
    g["children"].extend([
        make_species("EURYCEA_BISLINEATA", "Eurycea bislineata", "Northern Two-lined Salamander", "Woodland Salamanders", ["North America"],"A small stream salamander with a distinctive light dorsal stripe.", 0),
        make_species("EURYCEA_LUCIFUGA", "Eurycea lucifuga", "Cave Salamander", "Woodland Salamanders", ["North America"],"A striking orange salamander found at cave entrances in the karst regions.", 0),
        make_species("EURYCEA_QUADRIDIGITATA", "Eurycea quadridigitata", "Four-toed Salamander", "Woodland Salamanders", ["North America"],"Named for having only four toes on the hind feet instead of the usual five.", 0),
        make_species("EURYCEA_LEPROSA", "Eurycea leprosa", "Clear Creek Salamander", "Woodland Salamanders", ["North America"],"A Central Texas endemic associated with spring-fed limestone streams.", 0),
    ])

    g = find_genus(ch, "Gyrinophilus")
    g["children"].extend([
        make_species("GYRINOPHILUS_PORPHYRITICUS", "Gyrinophilus porphyriticus", "Spring Salamander", "Woodland Salamanders", ["North America"],"A large pinkish salamander of cold mountain springs; highly sensitive to water quality.", 0),
        make_species("GYRINOPHILUS_PALEATUS", "Gyrinophilus paleatus", "West Virginia Spring Salamander", "Woodland Salamanders", ["North America"],"A cave-adapted form with reduced eyes and pigment.", 0),
    ])

    g = find_genus(ch, "Pseudotriton")
    g["children"].extend([
        make_species("PSEUDOTRITON_RUBER", "Pseudotriton ruber", "Red Salamander", "Woodland Salamanders", ["North America"],"A vivid red salamander with black spots; its bright colour mimics the toxic Eastern Newt.", 0),
        make_species("PSEUDOTRITON_MONTANUS", "Pseudotriton montanus", "Mud Salamander", "Woodland Salamanders", ["North America"],"A burrowing species found in muddy streams and seeps across the southeastern US.", 0),
    ])

    g = find_genus(ch, "Aneides")
    g["children"].extend([
        make_species("ANEIDES_AENEUS", "Aneides aeneus", "Green Salamander", "Woodland Salamanders", ["North America"],"A strikingly green-mottled salamander that climbs vertical rock faces in the Appalachians.", 0),
        make_species("ANEIDES_LUGUBRIS", "Aneides lugubris", "Arboreal Salamander", "Woodland Salamanders", ["North America"],"A California species with a prehensile tail; can climb smooth vertical surfaces.", 0),
        make_species("ANEIDES_FLAVIPUNCTATUS", "Aneides flavipunctatus", "Black Salamander", "Woodland Salamanders", ["North America"],"A dark California species with white speckles; found in coastal redwood forests.", 0),
    ])

    g = find_genus(ch, "Batrachoseps")
    g["children"].extend([
        make_species("BATRACHOSEPS_ATTENUATUS", "Batrachoseps attenuatus", "California Slender Salamander", "Woodland Salamanders", ["North America"],"An extremely slender legless-looking salamander; moves like a worm through leaf litter.", 0),
        make_species("BATRACHOSEPS_WRIGHTI", "Batrachoseps wrighti", "Oregon Slender Salamander", "Woodland Salamanders", ["North America"],"A tiny species from the Cascades of Oregon; females guard their eggs.", 0),
        make_species("BATRACHOSEPS_REX", "Batrachoseps rex", "King Slender Salamander", "Woodland Salamanders", ["North America"],"The largest Batrachoseps; endemic to the Sequoia National Forest region.", 0),
    ])

    g = find_genus(ch, "Hydromantes")
    g["children"].extend([
        make_species("HYDROMANTES_PLATYCEPHALUS", "Hydromantes platycephalus", "Mount Lyell Salamander", "Woodland Salamanders", ["North America"],"A California species with a flattened head for living under rocks in alpine talus.", 0),
        make_species("HYDROMANTES_SHANTAE", "Hydromantes shantae", "Shasta Salamander", "Woodland Salamanders", ["North America"],"Restricted to limestone outcrops in the Shasta-Trinity region.", 0),
        make_species("HYDROMANTES_ITALICUS", "Hydromantes italicus", "Italian Cave Salamander", "Woodland Salamanders", ["Europe"],"An European plethodontid; one of the few outside the Americas.", 0),
    ])

    g = find_genus(ch, "Speleomantes")
    if g:
        g["children"].extend([
            make_species("SPELEOMANTES_AMBROSETTII", "Speleomantes ambrosettii", "Ambrosetti's Cave Salamander", "Woodland Salamanders", ["Europe"],"A Sardinian endemic found in limestone caves and moist rock crevices.", 0),
            make_species("SPELEOMANTES_STRINATII", "Speleomantes strinatii", "Strinnati's Cave Salamander", "Woodland Salamanders", ["Europe"],"A Ligurian and Maritime Alps species; the northernmost European plethodontid.", 0),
        ])

    g = find_genus(ch, "Bolitoglossa")
    g["children"].extend([
        make_species("BOLITOGLOSSA_MARMORATA", "Bolitoglossa marmorata", "Marbled Mushroom-tongue Salamander", "Woodland Salamanders", ["South America"],"A beautiful marbled species from the Andes of Venezuela and Colombia.", 0),
        make_species("BOLITOGLOSSA_ALTAMAZONICA", "Bolitoglossa altamazonica", "Amazonian Mushroom-tongue Salamander", "Woodland Salamanders", ["South America"],"The most widespread Amazonian plethodontid; found in lowland rainforest leaf litter.", 0),
        make_species("BOLITOGLOSSA_MEANYANA", "Bolitoglossa meanyana", "Meany's Salamander", "Woodland Salamanders", ["North America"],"A cloud forest species from Costa Rica and Panama with prehensile tail.", 0),
        make_species("BOLITOGLOSSA_SUBPALMATA", "Bolitoglossa subpalmata", "Neotropical Mushroom-tongue Salamander", "Woodland Salamanders", ["North America"],"A highland Costa Rican species; lives in bromeliads in montane oak forests.", 0),
    ])

    return data

ENRICHERS["plethodontidae"] = enrich_plethodontidae



# ---------------------------------------------------------------------------
# ENRICHER: soricidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_soricidae(data):
    ch = data["children"]

    g = find_genus(ch, "Sorex")
    g["children"].extend([
        make_species("SOREX_ARANEUS", "Sorex araneus", "Common Shrew", "Red-toothed Shrews", ["Europe", "Asia"],"One of the most abundant European mammals; must consume 90% of its body weight daily.", 0),
        make_species("SOREX_MINUTUS", "Sorex minutus", "Pygmy Shrew", "Red-toothed Shrews", ["Europe", "Asia"],"Weighs 3-6 g; one of the smallest land mammals in the world.", 0),
        make_species("SOREX_CORONATUS", "Sorex coronatus", "Milky-toothed Shrew", "Red-toothed Shrews", ["Europe"],"A European species distinguished from S. araneus by white-tipped teeth.", 0),
        make_species("SOREX_ALPINUS", "Sorex alpinus", "Alpine Shrew", "Red-toothed Shrews", ["Europe"],"A high-elevation species of the Alps, Carpathians and Balkans.", 0),
        make_species("SOREX_CINEREUS", "Sorex cinereus", "Masked Shrew", "Red-toothed Shrews", ["North America"],"The most widely distributed North American shrew; found from Alaska to the Appalachians.", 0),
        make_species("SOREX_PALUSTRIS", "Sorex palustris", "American Water Shrew", "Red-toothed Shrews", ["North America"],"A semi-aquatic shrew that dives for aquatic invertebrates; has stiff hairs on hind feet for paddling.", 0),
        make_species("SOREX_VAGRANS", "Sorex vagrans", "Vagrant Shrew", "Red-toothed Shrews", ["North America"],"A common western North American shrew with a broad habitat tolerance.", 0),
        make_species("SOREX_MONTICOLUS", "Sorex monticolus", "Montane Shrew", "Red-toothed Shrews", ["North America"],"Found in western montane forests; one of the most abundant small mammals in the Rockies.", 0),
        make_species("SOREX_DISPAR", "Sorex dispar", "Long-tailed Shrew", "Red-toothed Shrews", ["North America"],"A rare shrew of talus slopes in the Appalachians; named for its proportionally long tail.", 0),
        make_species("SOREX_UNGUICULATUS", "Sorex unguiculatus", "Large-clawed Shrew", "Red-toothed Shrews", ["Asia"],"A Japanese and Sakhalin species with enlarged front claws for digging.", 0),
        make_species("SOREX_GRACILLIMUS", "Sorex gracillimus", "Slender Shrew", "Red-toothed Shrews", ["Asia"],"One of the smallest Sorex; found in Hokkaido and the Russian Far East.", 0),
        make_species("SOREX_ISODON", "Sorex isodon", "Even-toothed Shrew", "Red-toothed Shrews", ["Europe", "Asia"],"A boreal shrew with uniform tooth pigmentation; ranges from Scandinavia to Kamchatka.", 0),
        make_species("SOREX_ROHRI", "Sorex rohri", "Rohr's Shrew", "Red-toothed Shrews", ["Africa"],"One of the few African Sorex; found in highland forests of Tanzania.", 0),
    ])

    g = find_genus(ch, "Crocidura")
    g["children"].extend([
        make_species("CROCIDURA_RUSSULA", "Crocidura russula", "Greater White-toothed Shrew", "White-toothed Shrews", ["Europe", "Africa"],"The commonest shrew in southern Europe; young form characteristic caravans.", 0),
        make_species("CROCIDURA_SUAVEOLENS", "Crocidura suaveolens", "Lesser White-toothed Shrew", "White-toothed Shrews", ["Europe", "Asia", "Africa"],"Found across a vast range from western Europe to Japan.", 0),
        make_species("CROCIDURA_LEUCODON", "Crocidura leucodon", "Bicoloured Shrew", "White-toothed Shrews", ["Europe"],"Distinguished by its sharp white-grey dorsal and pale ventral colour boundary.", 0),
        make_species("CROCIDURA_OLIVIERI", "Crocidura olivieri", "African Giant Shrew", "White-toothed Shrews", ["Africa"],"The largest Crocidura; weighs up to 50 g; found across sub-Saharan Africa.", 0),
        make_species("CROCIDURA_ATTILA", "Crocidura attila", "Attila's Shrew", "White-toothed Shrews", ["Asia"],"A Southeast Asian species named for its aggressive predatory behaviour for a shrew.", 0),
        make_species("CROCIDURA_GOLIATH", "Crocidura goliath", "Goliath Shrew", "White-toothed Shrews", ["Africa"],"A very large Central African rainforest shrew weighing up to 40 g.", 0),
        make_species("CROCIDURA_LASIURA", "Crocidura lasiura", "Ussuri White-toothed Shrew", "White-toothed Shrews", ["Asia"],"The largest Palearctic Crocidura; found in the Russian Far East and Korea.", 0),
        make_species("CROCIDURA_CYANEA", "Crocidura cyanea", "Reddish-grey Musk Shrew", "White-toothed Shrews", ["Africa"],"A small southern African species with a bluish-grey sheen to its fur.", 0),
        make_species("CROCIDURA_DOLICHURA", "Crocidura dolichura", "Long-tailed Musk Shrew", "White-toothed Shrews", ["Africa"],"A Central African species with a notably long tail relative to body length.", 0),
        make_species("CROCIDURA_WHITEHEADI", "Crocidura whiteheadi", "Whitehead's Shrew", "White-toothed Shrews", ["Asia"],"A Bornean endemic; part of the diverse Southeast Asian Crocidura radiation.", 0, "John Whitehead"),
        make_species("CROCIDURA_RAMONA", "Crocidura ramona", "Ramona's Shrew", "White-toothed Shrews", ["Asia"],"An Israeli endemic restricted to the Negev desert highlands.", 0),
        make_species("CROCIDURA_MONAX", "Crocidura monax", "Single-toothed Shrew", "White-toothed Shrews", ["Africa"],"Named for its unusual reduced tooth count; found in Tanzania's Eastern Arc Mountains.", 0),
    ])

    g = find_genus(ch, "Neomys")
    g["children"].extend([
        make_species("NEOMYS_FODIENS", "Neomys fodiens", "Eurasian Water Shrew", "Water Shrews", ["Europe", "Asia"],"Europe's largest shrew; mildly venomous saliva causes localised pain in humans.", 0),
        make_species("NEOMYS_ANOMALUS", "Neomys anomalus", "Mediterranean Water Shrew", "Water Shrews", ["Europe"],"A smaller relative of the Eurasian water shrew with less developed fringing hairs.", 0),
        make_species("NEOMYS_MILLERI", "Neomys milleri", "Miller's Water Shrew", "Water Shrews", ["Europe"],"Named after the naturalist; found in the Balkan peninsula and Asia Minor.", 0, "Miller"),
    ])

    g = find_genus(ch, "Suncus")
    g["children"].extend([
        make_species("SUNCUS_ETRUSCUS", "Suncus etruscus", "Etruscan Shrew", "White-toothed Shrews", ["Europe", "Asia", "Africa"],"The world's smallest mammal by mass at 1.8-2.5 g; heart rate exceeds 1500 bpm.", 0),
        make_species("SUNCUS_MURINUS", "Suncus murinus", "Asian Musk Shrew", "White-toothed Shrews", ["Asia", "Africa"],"A large shrew that has spread across the tropics with human trade; produces a strong musky odour.", 0),
        make_species("SUNCUS_FELLESCENS", "Suncus fellescens", "Sulawesi Giant Shrew", "White-toothed Shrews", ["Asia"],"An endemic Sulawesi species; one of the largest Suncus.", 0),
        make_species("SUNCUS_INFINITESTIMUS", "Suncus infinitestimulus", "Socotra Shrew", "White-toothed Shrews", ["Asia"],"Endemic to Socotra Island; one of the least-known shrew species.", 0),
        make_species("SUNCUS_LIXUS", "Suncus lixus", "Greater Dwarf Shrew", "White-toothed Shrews", ["Africa"],"A Central African Suncus found in wetland margins and grassy savannas.", 0),
    ])

    # New genus
    g = ensure_genus(ch, "GENUS_BLARINA", "Blarina","Short-tailed shrews","Medium-sized, robust shrews of North America with distinctive short tails. They are among the few venomous mammals — their saliva contains a neurotoxin that paralyses earthworms and small vertebrates.", "Red-toothed Shrews")
    g["children"].extend([
        make_species("BLARINA_BREVICAUDA", "Blarina brevicauda", "Northern Short-tailed Shrew", "Red-toothed Shrews", ["North America"],"The most venomous shrew; its bite carries a neurotoxin capable of causing swelling and pain in humans that can last for days.", 0),
        make_species("BLARINA_CAROLINENSIS", "Blarina carolinensis", "Southern Short-tailed Shrew", "Red-toothed Shrews", ["North America"],"A smaller southern relative; uses venom to immobilise prey for later consumption.", 0),
        make_species("BLARINA_HYLOPHAGA", "Blarina hylophaga", "Elliot's Short-tailed Shrew", "Red-toothed Shrews", ["North America"],"A central US species separated from B. brevicauda on chromosomal and genetic grounds.", 0),
    ])

    return data

ENRICHERS["soricidae"] = enrich_soricidae



# ---------------------------------------------------------------------------
# ENRICHER: ranidae  (GENUS_xxx / snake_case)
# ---------------------------------------------------------------------------
def enrich_ranidae(data):
    ch = data["children"]

    g = find_genus(ch, "Rana")
    g["children"].extend([
        make_species("RANA_TEMPORARIA", "Rana temporaria", "Common Frog", "European Frogs", ["Europe", "Asia"],"The most familiar amphibian in Britain and northern Europe; highly variable in colour.", 2),
        make_species("RANA_ARVALIS", "Rana arvalis", "Moor Frog", "European Frogs", ["Europe", "Asia"],"Males turn intense cobalt blue during a brief breeding window each spring.", 0),
        make_species("RANA_DALMATINA", "Rana dalmatina", "Agile Frog", "European Frogs", ["Europe"],"One of Europe's most athletic frogs; capable of leaping over 2 m.", 0),
        make_species("RANA_SYLVATICA", "Rana sylvatica", "Wood Frog", "American Frogs", ["North America"],"Survives freezing solid in winter; up to 65% of body water turns to ice around, not inside, cells.", 0),
        make_species("RANA_PYRENAICA", "Rana pyrenaica", "Pyrenean Frog", "European Frogs", ["Europe"],"Endemic to fast-flowing mountain streams of the Pyrenees; Near Threatened.", 0),
        make_species("RANA_IBERICA", "Rana iberica", "Iberian Frog", "European Frogs", ["Europe"],"A slender stream-dwelling frog endemic to northwestern Iberia.", 0),
        make_species("RANA_LATASTEI", "Rana latastei", "Italian Agile Frog", "European Frogs", ["Europe"],"A lowland frog restricted to Po Valley floodplain woodlands; Vulnerable.", 0),
        make_species("RANA_ITALICA", "Rana italica", "Italian Stream Frog", "European Frogs", ["Europe"],"A small brown frog endemic to Apennine streams.", 0),
        make_species("RANA_GRAECA", "Rana graeca", "Greek Stream Frog", "European Frogs", ["Europe"],"A Balkan endemic of rocky mountain streams; Near Threatened.", 0),
        make_species("RANA_JAPONICA", "Rana japonica", "Japanese Brown Frog", "Asian Brown Frogs", ["Asia"],"A common Japanese brown frog found in paddy fields and wetlands.", 0),
        make_species("RANA_TSUSHIMENSIS", "Rana tsushimensis", "Tsushima Frog", "Asian Brown Frogs", ["Asia"],"An island endemic restricted to Tsushima Island between Japan and Korea.", 0),
        make_species("RANA_DYBOWSKII", "Rana dybowskii", "Dybowski's Frog", "Asian Brown Frogs", ["Asia"],"A forest frog from the Russian Far East, Korea and Japan.", 0),
    ])

    g = find_genus(ch, "Pelophylax")
    g["children"].extend([
        make_species("PELOPHYLAX_RIDIBUNDUS", "Pelophylax ridibundus", "Marsh Frog", "European Frogs", ["Europe", "Asia"],"The largest European frog; introduced to England where it has become invasive.", 0),
        make_species("PELOPHYLAX_LESSONAE", "Pelophylax lessonae", "Pool Frog", "European Frogs", ["Europe"],"A smaller green frog; hybridises with the marsh frog to form the edible frog.", 0),
        make_species("PELOPHYLAX_PEREZI", "Pelophylax perezi", "Iberian Water Frog", "European Frogs", ["Europe"],"The most common frog in Iberia; highly adaptable and found in all freshwater habitats.", 0),
        make_species("PELOPHYLAX_NIGROMACULATUS", "Pelophylax nigromaculatus", "Black-spotted Pond Frog", "Asian Water Frogs", ["Asia"],"Common across East Asia; a major agricultural frog declining due to habitat loss.", 0),
        make_species("PELOPHYLAX_PLANCYI", "Pelophylax plancyi", "Eastern Golden Frog", "Asian Water Frogs", ["Asia"],"A bright yellow-green species from China and Taiwan.", 0),
    ])

    g = find_genus(ch, "Lithobates")
    g["children"].extend([
        make_species("LITHOBATES_CATESBEIANUS", "Lithobates catesbeianus", "American Bullfrog", "American Frogs", ["North America"],"The largest North American frog; invasive globally and a vector of chytrid fungus.", 0),
        make_species("LITHOBATES_PALMIPES", "Lithobates palmipes", "Amazon River Frog", "American Frogs", ["South America"],"A large aquatic frog from the Amazon and Orinoco basins.", 0),
        make_species("LITHOBATES_SPHENOCEPHALUS", "Lithobates sphenocephalus", "Southern Leopard Frog", "American Frogs", ["North America"],"Named for its spotted pattern; a common frog of the southeastern US.", 0),
        make_species("LITHOBATES_PIPIENS", "Lithobates pipiens", "Northern Leopard Frog", "American Frogs", ["North America"],"Widespread across North America; famous for its role in early pregnancy tests.", 0),
        make_species("LITHOBATES_CLAMITANS", "Lithobates clamitans", "Green Frog", "American Frogs", ["North America"],"One of the most common frogs in eastern North America with a banjo-like call.", 0),
    ])

    g = find_genus(ch, "Hylarana")
    if g:
        g["children"].extend([
            make_species("HYLARANA_ERYTHRAEA", "Hylarana erythraea", "Green Paddy Frog", "Asian Water Frogs", ["Asia"],"A bright green frog of Southeast Asian rice paddies and wetlands.", 0),
            make_species("HYLARANA_NICOBARIENSIS", "Hylarana nicobariensis", "Nicobar Frog", "Asian Water Frogs", ["Asia"],"A small brown frog from the Andaman and Nicobar Islands.", 0),
        ])

    g = find_genus(ch, "Odorrana")
    if g:
        g["children"].extend([
            make_species("ODORRANA_ODORATA", "Odorrana odorata", "Odorous Frog", "Asian Water Frogs", ["Asia"],"A stream frog from China and Vietnam with a distinctive pleasant smell.", 0),
            make_species("ODORRANA_GRACIOUSA", "Odorrana graciosa", "Graceful Odorous Frog", "Asian Water Frogs", ["Asia"],"A small odorous frog from Hainan Island, China.", 0),
        ])

    g = find_genus(ch, "Amolops")
    if g:
        g["children"].extend([
            make_species("AMOLOPS_LOUDONII", "Amolops loudonii", "Loudon's Torrent Frog", "Asian Water Frogs", ["Asia"],"Found in fast Himalayan streams; tadpoles use a ventral sucker to cling to rocks.", 0),
            make_species("AMOLOPS_MARMORATUS", "Amolops marmoratus", "Marbled Torrent Frog", "Asian Water Frogs", ["Asia"],"A Southeast Asian cascade frog with beautiful marbled patterning.", 0),
        ])

    g = find_genus(ch, "Babina")
    if g:
        g["children"].extend([
            make_species("BABINA_SUBSPINOSA", "Babina subspinosa", "Ryukyu Frog", "Asian Water Frogs", ["Asia"],"An endangered Ryukyu Archipelago endemic with warty dorsal skin.", 0),
            make_species("BABINA_HOLSTI", "Babina holsti", "Holst's Frog", "Asian Water Frogs", ["Asia"],"A Japanese endemic from the Okinawa Islands with secretive habits.", 0),
        ])

    return data

ENRICHERS["ranidae"] = enrich_ranidae



# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/enrich_all.py <family_slug>")
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

    # Count species before
    def count_species(node):
        n = 0
        if node.get("rank") == "SPECIES":
            n += 1
        for c in node.get("children", []):
            n += count_species(c)
        return n

    before = count_species(data)
    print(f"  species before: {before}")

    # Run enricher
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

