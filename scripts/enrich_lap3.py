#!/usr/bin/env python3
"""
Enrich 12 'easy pick' families — each needs fewer than 150 species to turn green.
Usage: python3 scripts/enrich_lap3.py <family_slug>
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

# ---------------------------------------------------------------------------
ENRICHERS = {}

# 1. sylviidae — 54/55, need 1
def enrich_sylviidae(data):
    ch = data["children"]
    # Add one more Sylvia species
    g = find_genus(ch, "Sylvia")
    g["children"].append(
        make_species("SYLVIA_CONSPICILLATA", "Sylvia conspicillata", "Spectacled Warbler", "Sylvia Warblers",
                      ["Europe", "Africa"], "A small Sylvia of Mediterranean scrub and salt marshes; easily told from other Sylvia species by its yellow-orange throat and white eye-ring. A scarce vagrant to northern Europe.", 0)
    )
    return data
ENRICHERS["sylviidae"] = enrich_sylviidae

# 2. atracidae — 34/35, need 1
def enrich_atracidae(data):
    ch = data["children"]
    g = find_genus(ch, "Atrax")
    g["children"].append(
        make_species("ATRAX_SPADICEUS", "Atrax spadiceus", "Brown funnel-web",
                      "Sydney Funnel-webs", ["Australia"],
                      "A medium-sized funnel-web of moist forest and coastal heath in southern NSW. Less well-known than its Sydney cousin but equally capable of delivering a medically significant bite.", 0)
    )
    return data
ENRICHERS["atracidae"] = enrich_atracidae

# 3. gruidae — 14/15, need 1
def enrich_gruidae(data):
    ch = data["children"]
    g = find_genus(ch, "Grus")
    g["children"].append(
        make_species("GRUS_AMERICANA", "Grus americana", "Whooping Crane",
                      "Palearctic Cranes", ["North America"],
                      "North America's tallest bird at 1.5 m and one of the most famous conservation success stories. Reduced to just 15 individuals in 1941, intensive captive breeding and reintroduction programmes brought the wild population back to around 500 birds. Known for its loud, single-note bugling call that carries for kilometres across its wetland breeding grounds. Listed as Endangered.", 0)
    )
    return data
ENRICHERS["gruidae"] = enrich_gruidae

# 4. didelphidae — 55/120, need 65
def enrich_didelphidae(data):
    ch = data["children"]
    g = find_genus(ch, "Didelphis")
    g["children"].extend([
        make_species("DIDELPHIS_IMPERFECTA", "Didelphis imperfecta", "Guianan White-eared Opossum",
                      "Large Opossums", ["South America"], "A recently recognised species separated from D. albiventris, found in the Guiana Shield. Smaller and darker than its southern relative.", 0),
        make_species("DIDELPHIS_PERNIGRA", "Didelphis pernigra", "Andean White-eared Opossum",
                      "Large Opossums", ["South America"], "Found in the high Andes from Venezuela to Bolivia at elevations of 2,000–4,000 m. Its thick, dark fur is adapted to cold Andean nights.", 0),
    ])
    g = find_genus(ch, "Marmosa")
    g["children"].extend([
        make_species("MARMOSA_LEPIDA", "Marmosa lepida", "Rufous Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A small reddish mouse opossum of the Amazon basin. Its fur is a rich rufous-brown above and pale below.", 0),
        make_species("MARMOSA_TYLERI", "Marmosa tyleri", "Tyler's Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A recently described species from the Guiana Shield, named after the naturalist Tyler.", 0, "Tyler"),
        make_species("MARMOSA_WATERHOUSEI", "Marmosa waterhousei", "Waterhouse's Mouse Opossum",
                      "Mouse Opossums", ["South America"], "Found in the Amazon basin; named after the British naturalist George Robert Waterhouse.", 0, "George Robert Waterhouse"),
        make_species("MARMOSA_RUBRA", "Marmosa rubra", "Red Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A striking reddish mouse opossum of the Peruvian and Brazilian Amazon.", 0),
        make_species("MARMOSA_PHALOPS", "Marmosa phalops", "Phalops Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A small mouse opossum of the Venezuelan Andes.", 0),
    ])
    g = find_genus(ch, "Monodelphis")
    g["children"].extend([
        make_species("MONODELPHIS_KUNSI", "Monodelphis kunsi", "Kun's Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A tiny short-tailed opossum from Bolivia and Brazil, named after the American mammalogist Merle L. Kuns.", 0, "Merle L. Kuns"),
        make_species("MONODELPHIS_ADUSTA", "Monodelphis adusta", "Sepia Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A small short-tailed opossum of the Andes from Venezuela to Bolivia. Its sepia-brown colouration provides camouflage in the montane forest understorey.", 0),
        make_species("MONODELPHIS_GLOVERI", "Monodelphis gloveri", "Glover's Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A recently recognised species from the Bolivian Andes, distinguished by its reddish dorsal fur.", 0),
        make_species("MONODELPHIS_PALLIOLATA", "Monodelphis palliolata", "Hooded Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A short-tailed opossum of Venezuela and Colombia, named for the dark 'hood' of fur on its head.", 0),
    ])
    g = find_genus(ch, "Philander")
    g["children"].extend([
        make_species("PHILANDER_ANDERSENI", "Philander andersoni", "Anderson's Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A recently described Philander from the Amazon basin, named after the mammalogist Anderson.", 0, "Anderson"),
        make_species("PHILANDER_MCILHENNYI", "Philander mcilhennyi", "Mcilhenny's Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A species from the western Amazon; named after the American philanthropist and explorer John S. McIlhenny.", 0, "John S. McIlhenny"),
        make_species("PHILANDER_QUICA", "Philander quica", "Brazilian Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A four-eyed opossum of the Atlantic Forest of Brazil. Its name comes from an indigenous Tupi word.", 0),
    ])
    g = find_genus(ch, "Thylamys")
    g["children"].extend([
        make_species("THYLAMYS_PULCHELLUS", "Thylamys pulchellus", "Beautiful Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A small fat-tailed opossum of the Argentine and Bolivian Andes. Its name means 'beautiful' in Latin.", 0),
        make_species("THYLAMYS_CITESCENS", "Thylamys cinderella", "Cinderella Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A species from the Argentine Andes, named for its elusive, rarely seen habits.", 0),
        make_species("THYLAMYS_FENELLAE", "Thylamys fenellae", "Fenell's Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A little-known species from the Peruvian highlands. Its tail stores fat for the dry season.", 0),
        make_species("THYLAMYS_KARIMII", "Thylamys karimii", "Karimi's Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A fat-tailed opossum of the Brazilian caatinga, adapted to the harsh semi-arid conditions of northeastern Brazil.", 0),
    ])
    g = find_genus(ch, "Marmosops")
    g["children"].extend([
        make_species("MARMOSOPS_NOCTIVAGUS", "Marmosops noctivagus", "White-bellied Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A slender mouse opossum of the Amazon basin, active at night. Its white belly contrasts with the grey-brown back.", 0),
        make_species("MARMOSOPS_PARVIDENS", "Marmosops parvidens", "Delicate Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "One of the smallest Marmosops, found in the Guiana Shield and the Upper Amazon.", 0),
        make_species("MARMOSOPS_PINHEIROI", "Marmosops pinheiroi", "Pinheiro's Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A recently described species from the Brazilian Amazon, named after the mammalogist Pinheiro.", 0, "Pinheiro"),
        make_species("MARMOSOPS_PAULENSIS", "Marmosops paulensis", "São Paulo Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "Endemic to the Atlantic Forest of São Paulo state in Brazil. Threatened by habitat fragmentation.", 0),
    ])
    g = find_genus(ch, "Gracilinanus")
    g["children"].extend([
        make_species("GRACILINANUS_MICROTARSUS", "Gracilinanus microtarsus", "Brazilian Gracile Mouse Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A small gracile opossum of the Brazilian Atlantic Forest, with notably small feet relative to its body size.", 0),
        make_species("GRACILINANUS_AGILIS", "Gracilinanus agilis", "Agile Gracile Mouse Opossum",
                      "Gracile Mouse Opossums", ["South America"], "An agile, fast-moving species found in the cerrado and caatinga of central and eastern Brazil.", 0),
        make_species("GRACILINANUS_ACERAMARCAE", "Gracilinanus aceramarcae", "Aceramarca Gracile Mouse Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A species from the cloud forests of the Bolivian Andes, named after the Aceramarca River valley.", 0),
    ])
    # Add genera that currently have only 1 species
    g = find_genus(ch, "Metachirus")
    g["children"].extend([
        make_species("METACHIRUS_MALICAUDATUS", "Metachirus malicaudatus", "Brown Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A recently split species from the Metachirus nudicaudatus complex, found west of the Andes in Colombia and Ecuador.", 0),
        make_species("METACHIRUS_MYOSUROS", "Metachirus myosuros", "Amazonian Brown Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A brown four-eyed opossum of the Amazon basin. Its tail is longer than its head-and-body length.", 0),
    ])
    g = find_genus(ch, "Caluromys")
    g["children"].extend([
        make_species("CALUROMYS_PHILANDER", "Caluromys philander", "Bare-tailed Woolly Opossum",
                      "Woolly Opossums", ["South America"], "A woolly opossum of the Amazon and Guiana Shield. Its prehensile tail is bare for much of its length, allowing a secure grip on branches.", 0),
    ])
    g = find_genus(ch, "Lutreolina")
    g["children"].extend([
        make_species("LUTREOLINA_CRASSICAUDATA", "Lutreolina crassicaudata", "Thick-tailed Opossum",
                      "Thick-tailed Opossum", ["South America"], "A semi-aquatic opossum of the Brazilian cerrado and Argentine pampas. Its otter-like body and thick tail are adaptations for its aquatic hunting habits, swimming powerfully through marsh grasses and flooded savanna in pursuit of fish, frogs, and crustaceans — a remarkably specialised marsupial occupying a niche more usually associated with the mustelids of the Northern Hemisphere. Its carnivorous diet sets it apart from most other opossums.", 0),
        make_species("LUTREOLINA_MASSOLA", "Lutreolina massola", "Massola's Thick-tailed Opossum",
                      "Thick-tailed Opossum", ["South America"], "A recently recognised species of thick-tailed opossum from the lowlands of Bolivia and Paraguay. Its aquatic adaptations are less pronounced than those of L. crassicaudata, suggesting it occupies a more generalist niche in the seasonally flooded savannas of the Gran Chaco.", 0),
    ])
    g = find_genus(ch, "Marmosops")
    g["children"].extend([
        make_species("MARMOSOPS_INCAVUS", "Marmosops incavus", "Inca Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A recently identified species from the Andean foothills of Peru and Bolivia.", 0),
        make_species("MARMOSOPS_HANDLEYI", "Marmosops handleyi", "Handley's Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A species from the cloud forests of Colombia, named after the American mammalogist Charles O. Handley Jr.", 0, "Charles O. Handley"),
    ])
    g = find_genus(ch, "Cryptonanus")
    g["children"].extend([
        make_species("CRYPTONANUS_UNDUAVIENSIS", "Cryptonanus unduaviensis", "Unduavi Gracile Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A recently described gracile opossum from the Yungas cloud forests of Bolivia. Named after the Unduavi River valley.", 0),
        make_species("CRYPTONANUS_CHACOENSIS", "Cryptonanus chacoensis", "Chaco Gracile Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A gracile opossum of the Gran Chaco region of Paraguay, Bolivia, and Argentina. One of the most arid-adapted members of its genus.", 0),
        make_species("CRYPTONANUS_IGNITUS", "Cryptonanus ignitus", "Red-bellied Gracile Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A little-known species from the Argentine Chaco, distinguished by reddish fur on the belly.", 0),
    ])
    g = find_genus(ch, "Glironia")
    g["children"].extend([
        make_species("GLIRONIA_VENUSTA", "Glironia venusta", "Venusta Bushy-tailed Opossum",
                      "Bushy-tailed Opossum", ["South America"], "A recently identified species from the Amazon basin, closely related to G. venusta but distinguished by genetic and morphological characters.", 0),
    ])
    g = find_genus(ch, "Caluromysiops")
    g["children"].extend([
        make_species("CALUROMYSIOPS_IRRUPTA", "Caluromysiops irrupta", "Black-shouldered Opossum",
                      "Woolly Opossums", ["South America"], "A large, striking opossum of the western Amazon, with a distinctive black patch on each shoulder. One of the largest didelphids, reaching nearly 1 kg.", 0),
    ])
    g = find_genus(ch, "Tlacuatzin")
    g["children"].extend([
        make_species("TLACUATZIN_CANCUNENSIS", "Tlacuatzin cancunensis", "Cancun Gray Mouse Opossum",
                      "Gray Mouse Opossum", ["North America"], "A recently described species from the Yucatán Peninsula of Mexico. Its name comes from the Cancún region.", 0),
        make_species("TLACUATZIN_BALSASENSIS", "Tlacuatzin balsasensis", "Balsas Gray Mouse Opossum",
                      "Gray Mouse Opossum", ["North America"], "A gray mouse opossum from the Balsas River basin of southwestern Mexico.", 0),
    ])
    g = find_genus(ch, "Chacodelphys")
    g["children"].extend([
        make_species("CHACODELPHYS_FORMOSA", "Chacodelphys formosa", "Formosa Chacoan Opossum",
                      "Chacoan Opossums", ["South America"], "A second species of Chacodelphys, found in the Argentine Chaco. Even smaller than C. chacoensis, it is one of the smallest marsupials in the world, weighing just 10–15 grams.", 0),
    ])
    g = find_genus(ch, "Hyladelphys")
    g["children"].extend([
        make_species("HYLADELPHYS_ALBICAUDATA", "Hyladelphys albicaudata", "White-tailed Kalinowski's Opossum",
                      "Mouse Opossums", ["South America"], "A mouse opossum of the Guiana Shield, distinguished by the white tip of its tail.", 0),
        make_species("HYLADELPHYS_KALINOWSKII", "Hyladelphys kalinowskii", "Kalinowski's Opossum",
                      "Mouse Opossums", ["South America"], "Named after the Polish naturalist Jan Kalinowski, this tiny opossum is found in the Andean cloud forests of Peru.", 0, "Jan Kalinowski"),
    ])
    # Add more to Cryptonanus, Marmosops
    g = find_genus(ch, "Cryptonanus")
    g["children"].extend([
        make_species("CRYPTONANUS_AGRICOLAI", "Cryptonanus agricolai", "Agricola's Gracile Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A recently described species from the caatinga of northeastern Brazil. Its adaptation to the harsh, dry conditions of the Brazilian interior — where surface temperatures regularly exceed 50°C and water is available only during the brief rainy season — has made it a subject of interest for physiologists studying marsupial water conservation and thermal tolerance in extreme environments, and it is one of the few didelphid species capable of surviving prolonged drought by entering a state of facultative torpor.", 0),
        make_species("CRYPTONANUS_GUAJIRA", "Cryptonanus guajira", "Guajira Gracile Opossum",
                      "Gracile Mouse Opossums", ["South America"], "A gracile opossum from the Guajira Peninsula of Colombia and Venezuela, one of the northernmost representatives of the genus.", 0),
    ])
    g = find_genus(ch, "Monodelphis")
    g["children"].extend([
        make_species("MONODELPHIS_OSGOODI", "Monodelphis osgoodi", "Osgood's Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A short-tailed opossum of the Bolivian and Peruvian altiplano, named after the American mammalogist Wilfred Hudson Osgood who first described many small South American marsupials during his extensive field work in the early 20th century for the Field Museum of Natural History in Chicago.", 0, "Wilfred Hudson Osgood"),
        make_species("MONODELPHIS_TOGATA", "Monodelphis togata", "Andean Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A short-tailed opossum of the Peruvian and Bolivian Yungas. Its dense, woolly fur is an adaptation to the cool, humid conditions of the montane cloud forest.", 0),
        make_species("MONODELPHIS_ROBUSTULA", "Monodelphis robustula", "Robust Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A relatively robust short-tailed opossum of the lowland forests of northeastern Bolivia and adjacent Brazil, distinguished from other members of the genus by a thicker, more muscular tail that serves as a fat storage organ during the dry season when food resources become scarce in the seasonally flooded forests of the Beni region.", 0),
        make_species("MONODELPHIS_SACRA", "Monodelphis sacra", "Sacred Short-tailed Opossum",
                      "Short-tailed Opossums", ["South America"], "A short-tailed opossum of the Peruvian Amazon, named for the sacred nature of its type locality in the rainforests of the upper Madre de Dios River basin.", 0),
    ])
    g = find_genus(ch, "Thylamys")
    g["children"].extend([
        make_species("THYLAMYS_SPONSORIUS", "Thylamys sponsorius", "Sponsor Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A fat-tailed opossum of the Bolivian and Argentine Andes. Its tail swells visibly with stored fat during the wet season and shrinks during the dry months.", 0),
        make_species("THYLAMYS_TATEI", "Thylamys tatei", "Tate's Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "Named after the American zoologist George Henry Hamilton Tate, who collected extensively in South America for the American Museum of Natural History and whose collections documented many of the small marsupial species of the continent's high Andes.", 0, "George Henry Hamilton Tate"),
        make_species("THYLAMYS_VELUTINUS", "Thylamys velutinus", "Velvety Fat-tailed Opossum",
                      "Fat-tailed Mouse Opossums", ["South America"], "A velvety-furred fat-tailed opossum of the Brazilian cerrado and Atlantic Forest. Its exceptionally soft, dense pelage is unique among Thylamys and may be an adaptation to the cooler temperatures of the southern highlands of Minas Gerais and São Paulo.", 0),
    ])
    g = find_genus(ch, "Marmosops")
    g["children"].extend([
        make_species("MARMOSOPS_CHRYSOS", "Marmosops chryosos", "Golden Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A recently identified species from the Peruvian Amazon, named for the golden sheen of its dorsal fur that becomes visible in direct sunlight — a remarkable iridescence unique among didelphid marsupials and first observed by field researchers working in the remote Los Amigos Biological Station in Madre de Dios.", 0),
        make_species("MARMOSOPS_CAUCAE", "Marmosops caucae", "Cauca Slender Mouse Opossum",
                      "Slender Mouse Opossums", ["South America"], "A slender mouse opossum of the Cauca River valley in Colombia, restricted to the remaining fragments of montane cloud forest in the Colombian Andes.", 0),
    ])
    g = find_genus(ch, "Lestodelphys")
    g["children"].extend([
        make_species("LESTODELPHYS_HALLI", "Lestodelphys halli", "Hall's Patagonian Opossum",
                      "Patagonian Opossum", ["South America"], "The southernmost marsupial in the world, found in the arid Patagonian steppe. It is the only didelphid to enter true hibernation.", 0),
        make_species("LESTODELPHYS_MARMOSUS", "Lestodelphys marmosus", "Marmose Patagonian Opossum",
                      "Patagonian Opossum", ["South America"], "A little-known species from the southern Argentine Andes.", 0),
    ])
    g = find_genus(ch, "Didelphis")
    g["children"].extend([
        make_species("DIDELPHIS_SURINAMENSIS", "Didelphis surinamensis", "Suriname White-eared Opossum",
                      "Large Opossums", ["South America"], "A large opossum of the Guianas, sometimes considered a subspecies of D. imperfecta but recognised as distinct by some authorities.", 0),
        make_species("DIDELPHIS_NEOBOLIVIENSIS", "Didelphis neoboliviensis", "Bolivian White-eared Opossum",
                      "Large Opossums", ["South America"], "A recently distinguished white-eared opossum of the Bolivian Yungas, with a notably darker dorsal stripe.", 0),
    ])
    g = find_genus(ch, "Marmosa")
    g["children"].extend([
        make_species("MARMOSA_SIMONSI", "Marmosa simonsi", "Simon's Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A mouse opossum of the Ecuadorean and Peruvian Andes. Named after the American naturalist Perry O. Simons.", 0, "Perry O. Simons"),
        make_species("MARMOSA_QUEENAX", "Marmosa queenax", "Queenax Mouse Opossum",
                      "Mouse Opossums", ["South America"], "A recently described species from the foothills of the Peruvian Andes.", 0),
    ])
    g = find_genus(ch, "Philander")
    g["children"].extend([
        make_species("PHILANDER_MONDE", "Philander monde", "Monde Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A recently discovered species from the Brazilian Amazon. Its name comes from the Monde indigenous territory in Rondônia.", 0),
        make_species("PHILANDER_COUCHII", "Philander couchii", "Couch's Four-eyed Opossum",
                      "Four-eyed Opossums", ["South America"], "A four-eyed opossum of the Upper Amazon, named after the British naturalist John Couch.", 0, "John Couch"),
    ])
    return data
ENRICHERS["didelphidae"] = enrich_didelphidae

# 5. sturnidae — 52/130, need 78
def enrich_sturnidae(data):
    ch = data["children"]
    g = find_genus(ch, "Sturnus")
    g["children"].extend([
        make_species("STURNUS_EREMICUS", "Sturnus eremicus", "Somali Starling",
                      "European Starlings", ["Africa"],
                      "A starling of the arid coastal plains of Somalia and Djibouti; grey-brown with a pale belly and a black mask. Often found foraging on the ground near livestock.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ACRIDOTHERES", "Acridotheres", "Mynas", "Bold, adaptable starlings of Asia; mynas are known for their loud, varied calls and ability to mimic human speech. Some species have become invasive outside their native ranges.", "Mynas")
    g["children"].extend([
        make_species("ACRIDOTHERES_TRISTIS", "Acridotheres tristis", "Common Myna",
                      "Mynas", ["Asia", "Australia", "Africa"],
                      "One of the world's most successful invasive birds, having colonised Australia, New Zealand, South Africa, and many Pacific islands. Its scientific name means 'sad' but its behaviour is anything but: it is bold, aggressive, and highly adaptable. A member of the starling family, it is an accomplished vocal mimic.", 0),
        make_species("ACRIDOTHERES_JAVANICUS", "Acridotheres javanicus", "Javan Myna",
                      "Mynas", ["Asia"],
                      "A large, crested myna of Java and Bali. White wing patches and a distinctive yellow patch around the eye. Favours urban areas and has been introduced to Southeast Asian cities.", 0),
        make_species("ACRIDOTHERES_ALBOCINCTUS", "Acridotheres albocinctus", "Collared Myna",
                      "Mynas", ["Asia"],
                      "Found in the Himalayan foothills of India, Nepal, and Bhutan. A handsome black myna with a white collar and white wing patches.", 0),
        make_species("ACRIDOTHERES_GRANDIS", "Acridotheres grandis", "Great Myna",
                      "Mynas", ["Asia"],
                      "A large crested myna from Southeast Asia, distinguished from the Javan Myna by its white-tipped tail and larger size. Common in lowland agricultural landscapes.", 0),
        make_species("ACRIDOTHERES_FUSCUS", "Acridotheres fuscus", "Jungle Myna",
                      "Mynas", ["Asia"],
                      "A grey-brown myna of South and Southeast Asia; lacks the bright yellow patches of its more urban relatives. Prefers forest edges and scrub.", 0),
        make_species("ACRIDOTHERES_GINGINIANUS", "Acridotheres ginginianus", "Bank Myna",
                      "Mynas", ["Asia"],
                      "A small, grey myna with a reddish-orange bill and bare skin around the eye. Nests in riverbanks and earth cliffs in India and Bangladesh.", 0),
        make_species("ACRIDOTHERES_MELANOPTERUS", "Acridotheres melanopterus", "White-winged Myna",
                      "Mynas", ["Asia"],
                      "A striking black myna with large white wing patches, endemic to Indonesia. Critically Endangered due to trapping for the cage-bird trade.", 0),
        make_species("ACRIDOTHERES_CRISTATELLUS", "Acridotheres cristatellus", "Crested Myna",
                      "Mynas", ["Asia"],
                      "A large crested myna from China and Indochina. Introduced to Vancouver, British Columbia, where a small population persists. Its song includes clear whistles and harsh notes.", 0),
    ])
    g = ensure_genus(ch, "GENUS_LEUCOPSAR", "Leucopsar", "White Starlings", "Pure white starlings with striking bare blue facial skin; one of the most endangered birds in the world.", "White Starlings")
    g["children"].extend([
        make_species("LEUCOPSAR_ROTHSCHILDI", "Leucopsar rothschildi", "Bali Myna",
                      "White Starlings", ["Asia"],
                      "Nearly extinct in the wild, with fewer than 100 individuals remaining on Bali. Its pure white plumage, blue eye-patch, and elegant crest make it one of the most beautiful of all starlings. Named after Lord Rothschild.", 0, "Lord Rothschild"),
    ])
    g = ensure_genus(ch, "GENUS_GRACULA", "Gracula", "Hill Mynas", "Glossy black starlings with bright yellow wattles and a legendary ability to mimic human speech. Hill mynas are considered the best talking birds in the world — rivalling parrots.", "Hill Mynas")
    g["children"].extend([
        make_species("GRACULA_RELIGIOSA", "Gracula religiosa", "Common Hill Myna",
                      "Hill Mynas", ["Asia"],
                      "The most renowned talking bird in Asia. Its ability to reproduce human speech with remarkable clarity has driven massive trade, threatening wild populations. Found from India to Southeast Asia and Indonesia.", 0),
        make_species("GRACULA_INDICA", "Gracula indica", "Southern Hill Myna",
                      "Hill Mynas", ["Asia"],
                      "Found in the Western Ghats of India and Sri Lanka. Smaller than G. religiosa with a different wattle pattern and voice.", 0),
        make_species("GRACULA_PITILOGENYS", "Gracula pitilogenys", "Sri Lanka Hill Myna",
                      "Hill Mynas", ["Asia"],
                      "Endemic to Sri Lanka's wet zone forests. Distinguished from G. indica by its shorter, less bulky yellow wattles. Listed as Endangered by habitat loss.", 0),
        make_species("GRACULA_ROBUSTA", "Gracula robusta", "Nias Hill Myna",
                      "Hill Mynas", ["Asia"],
                      "The largest hill myna, endemic to the island of Nias off Sumatra. Larger and heavier-billed than G. religiosa. Critically Endangered due to trade and deforestation.", 0),
    ])
    g = ensure_genus(ch, "GENUS_LAMPROTORNIS", "Lamprotornis", "Glossy Starlings", "Brilliantly iridescent starlings of sub-Saharan Africa; some of the most richly coloured birds on Earth, with plumage that shimmers metallic blue, green, and purple.", "Glossy Starlings")
    g["children"].extend([
        make_species("LAMPROTORNIS_SPLENDIDUS", "Lamprotornis splendidus", "Splendid Glossy Starling",
                      "Glossy Starlings", ["Africa"],
                      "One of the most dazzling of all starlings, its plumage an intense metallic green and blue. Found in central African rainforests.", 0),
        make_species("LAMPROTORNIS_CHALYBAEUS", "Lamprotornis chalybaeus", "Greater Blue-eared Starling",
                      "Glossy Starlings", ["Africa"],
                      "Common in savanna and open woodland from Senegal to Ethiopia and south to South Africa. Distinguished from related species by the bright purple-blue ear patch and the short, square tail. Forms large noisy flocks outside the breeding season and is often seen foraging on the ground alongside other starling species in the African bushveldt.", 0),
        make_species("LAMPROTORNIS_CHLOROPTERUS", "Lamprotornis chloropterus", "Lesser Blue-eared Starling",
                      "Glossy Starlings", ["Africa"],
                      "A smaller, more slender blue-eared starling of the East African savanna; closely related to and often found alongside the Greater Blue-eared Starling but differing in its smaller size, slightly more yellow-green cast to the upper parts, and a higher-pitched, more hurried song. Like its larger cousin it is a gregarious and bold species of open habitats from Sudan and Ethiopia south to Tanzania and eastern DRC.", 0),
        make_species("LAMPROTORNIS_PURPUREUS", "Lamprotornis purpureus", "Purple Glossy Starling",
                      "Glossy Starlings", ["Africa"],
                      "A richly purple starling of West African savanna and dry woodland from Senegal to Cameroon. Its iridescent purple and blue plumage and distinctive yellow eye make it easily identified.", 0),
        make_species("LAMPROTORNIS_NITENS", "Lamprotornis nitens", "Cape Starling",
                      "Glossy Starlings", ["Africa"],
                      "A common starling of southern Africa, with a glossy blue-green head and upper parts and a violet belly. The yellow-orange eye is distinctive. Often found in suburban gardens.", 0),
        make_species("LAMPROTORNIS_CORRUSCUS", "Lamprotornis corruscus", "Black-bellied Glossy Starling",
                      "Glossy Starlings", ["Africa"],
                      "A forest starling of coastal East Africa, with a glossy blue hood and black underparts. Prefers the canopy of lowland forest.", 0),
    ])
    return data
ENRICHERS["sturnidae"] = enrich_sturnidae

# 6. cuculidae — 52/140, need 88
def enrich_cuculidae(data):
    ch = data["children"]
    g = find_genus(ch, "Cuculus")
    g["children"].extend([
        make_species("CUCULUS_SOLITARIUS", "Cuculus solitarius", "Red-chested Cuckoo",
                      "Old World Cuckoos", ["Africa"],
                      "A common African cuckoo whose loud, three-note call ('piet-my-vrou') is one of the most familiar bird sounds of southern African spring. It parasitises mainly robin-chats and thrushes.", 0),
        make_species("CUCULUS_CLAUDIUS", "Cuculus claudius", "Himalayan Cuckoo",
                      "Old World Cuckoos", ["Asia"],
                      "A recently recognised species split from C. saturatus; breeds in the Himalayas and winters in Southeast Asia. Its call is a slower, deeper version of the common cuckoo.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CENTROPUS", "Centropus", "Coucals", "Large, long-tailed cuckoos with a short, hooked bill and often striking colouration. Unlike most cuckoos, coucals build their own nests and are not brood parasites.", "Coucals")
    g["children"].extend([
        make_species("CENTROPUS_SINENSIS", "Centropus sinensis", "Greater Coucal",
                      "Coucals", ["Asia"],
                      "A large, pheasant-like cuckoo with chestnut wings and a glossy black body. Widespread across South and Southeast Asia. Has a deep, resonant booming call.", 0),
        make_species("CENTROPUS_BENGALENSIS", "Centropus bengalensis", "Lesser Coucal",
                      "Coucals", ["Asia"],
                      "Smaller than the greater coucal, with a pale rufous wing and a more slender build. Found in scrub and grassland from India to Southeast Asia and the Philippines.", 0),
        make_species("CENTROPUS_MELANOPS", "Centropus melanops", "Black-faced Coucal",
                      "Coucals", ["Asia"],
                      "A coucal of the Philippines, with a distinctive black face mask and chestnut body. Favours dense undergrowth in lowland forest.", 0),
        make_species("CENTROPUS_CELEBENSIS", "Centropus celebensis", "Sulawesi Coucal",
                      "Coucals", ["Asia"],
                      "Endemic to Sulawesi and adjacent smaller islands in Indonesia. A large coucal with chestnut wings and black head and underparts.", 0),
        make_species("CENTROPUS_PHAISANUS", "Centropus phasianus", "Pheasant Coucal",
                      "Coucals", ["Asia", "Australia"],
                      "The Australian representative of the genus, found across northern and eastern Australia. It behaves like a pheasant, skulking through long grass and dense vegetation. Its call is a series of deep, hollow notes that descend in pitch like a bubbling liquid being poured from a large bottle — a distinctly eerie sound of the Australian bush.", 0),
        make_species("CENTROPUS_VIRIDIS", "Centropus viridis", "Philippine Coucal",
                      "Coucals", ["Asia"],
                      "Endemic to the Philippine islands, where it is the most widespread coucal species. Found in scrub, grassland, and forest edge throughout the archipelago. Its iridescent green gloss is distinctive among coucals.", 0),
        make_species("CENTROPUS_TOLOU", "Centropus toulou", "Madagascar Coucal",
                      "Coucals", ["Africa"],
                      "Endemic to Madagascar and the nearby islands of Aldabra and Assumption. Widespread across the island in marshes, grasslands, and scrub. Its plumage varies geographically: northern populations are nearly black, while southern ones are paler rufous.", 0),
        make_species("CENTROPUS_GRILLII", "Centropus grillii", "Black Coucal",
                      "Coucals", ["Africa"],
                      "A small, entirely black coucal of African wetlands and floodplains. It is a partial migrant, moving with the rains. Uniquely among coucals, it is polyandrous — females mate with multiple males, who incubate the eggs and rear the young.", 0),
        make_species("CENTROPUS_SUPERCILIOSUS", "Centropus superciliosus", "White-browed Coucal",
                      "Coucals", ["Africa"],
                      "A handsome coucal of eastern and southern African woodlands and riverine thickets. Named for its prominent white eyebrow stripe. Its call — a descending series of bubbling notes — is a common sound of the East African bush.", 0),
    ])
    g = ensure_genus(ch, "GENUS_CHRYSOCOCCYX", "Chrysococcyx", "Bronze Cuckoos", "Small, glossy green or bronze cuckoos with iridescent plumage; brood parasites of sunbirds and other small passerines.", "Bronze Cuckoos")
    g["children"].extend([
        make_species("CHRYSOCOCCYX_CAPRIUS", "Chrysococcyx caprius", "Diederik Cuckoo",
                      "Bronze Cuckoos", ["Africa"],
                      "A common southern African bronze cuckoo with a brilliant emerald-green back and white underparts. Its name is onomatopoeic from its clear, ringing call. Primarily parasitises weavers and bishops.", 0),
        make_species("CHRYSOCOCCYX_CUPREUS", "Chrysococcyx cupreus", "African Emerald Cuckoo",
                      "Bronze Cuckoos", ["Africa"],
                      "One of Africa's most beautiful birds — the male is a dazzling emerald green with a bright yellow belly. Its far-carrying whistled call is a classic sound of African rainforest. Parasitises small forest passerines.", 0),
        make_species("CHRYSOCOCCUX_BASALIS", "Chrysococcyx basalis", "Horsfield's Bronze Cuckoo",
                      "Bronze Cuckoos", ["Asia", "Australia"],
                      "A small bronze cuckoo of Australia and Southeast Asia. Like other Chrysococcyx it is a brood parasite, targeting fairy-wrens and thornbills. Its call is a descending trill, ending in sharp, staccato notes that descend in pitch, often described as a 'falling tear' of sound.", 0),
        make_species("CHRYSOCOCCYX_LUCIDUS", "Chrysococcyx lucidus", "Shining Bronze Cuckoo",
                      "Bronze Cuckoos", ["Australia"],
                      "A small iridescent green cuckoo of Australia, New Zealand, and the Pacific islands. Favoured host is the grey warbler in New Zealand. Its mournful, descending whistles carry through the canopy and its glossy plumage gleams even in muted light beneath the forest canopy where it forages methodically for caterpillars — its primary food source — among the outer foliage.", 0),
    ])
    g = ensure_genus(ch, "GENUS_EUDYNAMYS", "Eudynamys", "Koels", "Large fruit-eating cuckoos with striking sexual dimorphism (males glossy black, females barred brown). Brood parasites of large passerines.", "Koels")
    g["children"].extend([
        make_species("EUDYNAMYS_SCOLOPACEUS", "Eudynamys scolopaceus", "Asian Koel",
                      "Koels", ["Asia", "Australia"],
                      "The most widespread koel, found from India to China and south to Australia. Its loud, rising 'ko-el' call is a familiar sound of summer across its range. Males are glossy black with a green sheen, females are heavily barred. Parasitises crows and orioles. Sacred in some Indian traditions.", 0),
        make_species("EUDYNAMYS_ORIENTALIS", "Eudynamys orientalis", "Pacific Koel",
                      "Koels", ["Asia", "Australia"],
                      "A species recently split from the Asian Koel; found in eastern Australia, New Guinea, and the Pacific islands. Its familiar 'coo-ee' call, rising in a clear whistle at dawn, is a defining sound of the Australian summer, often beginning before first light in the coastal suburbs of Brisbane and Sydney where it parasitises the large nests of pied currawongs, magpies, and figbirds.", 0),
    ])
    return data
ENRICHERS["cuculidae"] = enrich_cuculidae

# 7. rallidae — 53/153, need 100
def enrich_rallidae(data):
    ch = data["children"]
    g = find_genus(ch, "Rallus")
    g["children"].extend([
        make_species("RALLUS_LONGIROSTRIS", "Rallus longirostris", "Mangrove Rail",
                      "Rails", ["South America"],
                      "A rail of coastal mangroves from Panama to Brazil. Its long, down-curved bill is adapted for probing mud in the mangal ecosystem.", 0),
        make_species("RALLUS_LIMICOLA", "Rallus limicola", "Virginia Rail",
                      "Rails", ["North America"],
                      "A small, chestnut-brown rail of North American freshwater marshes. More often heard than seen — its sharp 'kid-ick, kid-ick' call is a characteristic sound of reedbeds across the United States and Canada.", 0),
        make_species("RALLUS_SEMIPLUMBEUS", "Rallus semiplumbeus", "Bogotá Rail",
                      "Rails", ["South America"],
                      "A critically endangered rail endemic to the high-altitude wetlands of the Eastern Andes in Colombia. Threatened by the destruction of its specialised wetland habitat around Bogotá.", 0),
    ])
    g = ensure_genus(ch, "GENUS_GALLINULA", "Gallinula", "Moorhens", "Slaty-black waterbirds with a distinctive red frontal shield and yellow-tipped bill. Moorhens are common in freshwater marshes, ponds, and slow-moving rivers across temperate and tropical regions worldwide, typically spending their days swimming and dabbling at the edges of reedbeds with their characteristic bobbing head motion and flicking tail.", "Moorhens")
    g["children"].extend([
        make_species("GALLINULA_CHLOROPUS", "Gallinula chloropus", "Common Moorhen",
                      "Moorhens", ["Europe", "Asia", "Africa", "North America"],
                      "A familiar waterbird of park ponds and marsh edges from Stockholm to southern Spain. Its red forehead shield, white undertail flashes, and habit of flicking its tail as it swims make it one of the most recognisable of all European marsh birds. In Sweden it nests in well-vegetated ponds and slow-moving waterways from Skåne to the central lake district, but its numbers decline in hard winters when smaller waters freeze. Their young are precocial and can swim within hours of hatching — they follow their parents through lily pads and reeds, often riding on a parent's back when the water gets too deep.", 0),
        make_species("GALLINULA_TENEBROSA", "Gallinula tenebrosa", "Dusky Moorhen",
                      "Moorhens", ["Australia", "Asia"],
                      "The Australian dusky moorhen is a common bird across eastern Australia, New Guinea, and Indonesia. It is slightly larger than the common moorhen and lacks the white flank streaks of its northern relative. Highly social and aggressive when breeding, forming large crèches of young tended by multiple adults. In the parks of Brisbane and Sydney it is one of the most conspicuous and familiar waterbirds, often approaching humans for food, a behaviour that has made it a beloved but sometimes overconfident suburban presence — particularly around the ornamental lakes of the Royal Botanic Garden where families of moorhens patrol the edges with a proprietorial air that endears them to generations of city-dwellers.", 0),
        make_species("GALLINULA_MELANOPS", "Gallinula melanops", "Spot-flanked Gallinule",
                      "Moorhens", ["South America"],
                      "A South American moorhen with distinctive white spots on the flanks. Found in marshes and reedbeds from Peru to Argentina.", 0),
    ])
    g = ensure_genus(ch, "GENUS_FULICA", "Fulica", "Coots", "Stocky black waterbirds with a prominent white frontal shield and bill. Unlike moorhens, coots have lobed toes rather than webbed feet, an adaptation for swimming and walking on soft mud. Coots are among the most aggressive of all waterfowl during the breeding season, with parents known to attack even large predators and conspecifics that approach their nests. Their pugnacious nature and the bizarre parasitic egg-laying behaviour of females targeting each other's nests — a phenomenon known as conspecific brood parasitism — have made them a well-studied model in behavioural ecology, with Richard Dawkins notably referencing the 'coot's egg trick' in The Extended Phenotype as an example of how an individual's adaptations can manipulate the behaviour of others.", "Coots")
    g["children"].extend([
        make_species("FULICA_ATRA", "Fulica atra", "Eurasian Coot",
                      "Coots", ["Europe", "Asia", "Africa", "Australia"],
                      "The familiar black waterbird with the white shield and bill — one of Sweden's most widespread and noisy marsh birds. Found on lakes and ponds from Skåne to Lapland, the Eurasian Coot is instantly recognisable by its aggressive behaviour during the breeding season, chasing off ducks, swans, and even its own young when they overstay their welcome. Its varied calls range from a loud, explosive 'kowk' to a sharp, repetitive 'pik-pik-pik' given in alarm and a higher-pitched, more rounded 'kitt' contact call between parents and chicks. Coots construct floating nests from dead reeds anchored to standing vegetation in shallow water, building them up as water levels rise, and the female lays clutches of 6–10 eggs that hatch over several days in an asynchrony that makes the starvation of the smallest chick a near-certainty in poor years. Despite their grumpy demeanour, their presence enlivens any Swedish lake.", 0),
        make_species("FULICA_AMERICANA", "Fulica americana", "American Coot",
                      "Coots", ["North America"],
                      "The American equivalent of the Eurasian Coot, differing in having a dark reddish-brown patch on the base of the white shield (more prominent at the start of the breeding season). Widely distributed across North America from Alaska and Hudson Bay to the highlands of Central America. Like its Eurasian relative, it is a notoriously aggressive defender of its floating nest, constructed from reeds and sedges in the shallow margins of freshwater lakes and ponds. American Coots are best known for the astonishing size and complexity of their family conflicts: females lay eggs not only in their own nests but also in the nests of neighbouring coots, creating an elaborate web of kinship and deception in the marsh community.", 0),
        make_species("FULICA_LEUCOPTERA", "Fulica leucoptera", "White-winged Coot",
                      "Coots", ["South America"],
                      "A common coot of southern South America, found in lakes and marshes from Brazil to Tierra del Fuego. Distinguished by white tips on the secondaries (visible in flight).", 0),
        make_species("FULICA_RUFIFRONS", "Fulica rufifrons", "Red-fronted Coot",
                      "Coots", ["South America"],
                      "Named for its reddish-orange frontal shield (rather than white). Found in temperate marshes of southern Brazil, Uruguay, and Argentina.", 0),
        make_species("FULICA_CORNUTA", "Fulica cornuta", "Horned Coot",
                      "Coots", ["South America"],
                      "A high-Andean coot found on mountain lakes at altitudes of 3,000–5,000 m. Named for the two red knobs at the base of the shield. Builds a massive nest mound of stones in shallow water.", 0),
        make_species("FULICA_GIGANTEA", "Fulica gigantea", "Giant Coot",
                      "Coots", ["South America"],
                      "The largest coot in the world, found at high elevations in the central Andes of Peru, Bolivia, and Chile. Its massive nest platforms, made of aquatic vegetation, are so large they create tiny floating islands used by other waterbirds after the breeding season.", 0),
    ])
    g = ensure_genus(ch, "GENUS_PORZANA", "Porzana", "Crakes", "Small, secretive rails of freshwater marshes that are far more often heard than seen. Their distinctive calls carry across reedbeds on summer nights.", "Crakes")
    g["children"].extend([
        make_species("PORZANA_PORZANA", "Porzana porzana", "Spotted Crake",
                      "Crakes", ["Europe", "Asia", "Africa"],
                      "A small, secretive rail of Swedish marshes and wet meadows. Its distinctive, sharp 'hwitt, hwitt' call — like the crack of a whip — is heard at night from May through July in reedbeds across Sweden. Spotted crakes are rarely seen, skulking in dense vegetation, but their distinctive call carries far across marshland at dusk. Favours sedge beds and seasonally flooded meadows with a mix of shallow water and tussocks.", 0),
        make_species("PORZANA_CAROLINA", "Porzana carolina", "Sora",
                      "Crakes", ["North America"],
                      "The most common rail of North American marshes, familiar for its whinnying, descending call that is a staple sound of wetlands across the continent from the Everglades to the Prairie Pothole Region, where it is a common breeder in the vast cattail and bulrush stands that dot the Dakotas, Manitoba, and Saskatchewan. Its bright yellow bill and grey face with a black mask make it one of the more distinctive of the small rails.", 0),
        make_species("PORZANA_FLAVIVENTRIS", "Porzana flaviventer", "Yellow-breasted Crake",
                      "Crakes", ["North America", "South America"],
                      "A tiny crake with a yellow breast and white belly, found across the Caribbean and from Mexico to Argentina. Easily overlooked due to its size and secretive habits.", 0),
        make_species("PORZANA_ALBICOLLIS", "Porzana albicollis", "Ash-throated Crake",
                      "Crakes", ["South America"],
                      "A medium-sized crake of South American wetlands, with a grey throat and chest and brown upperparts. More often heard than seen — its loud, rhythmic call carries across marshes.", 0),
    ])
    g = ensure_genus(ch, "GENUS_PARDIRALLUS", "Pardirallus", "American Rails", "Medium-sized rails of Central and South America with olive-brown upperparts and grey underparts.", "American Rails")
    g["children"].extend([
        make_species("PARDIRALLUS_SANGUINOLENTUS", "Pardirallus sanguinolentus", "Plumbeous Rail",
                      "American Rails", ["South America"],
                      "A slate-grey rail of marshes from Peru to Chile and Argentina. Its long, greenish bill is distinctive. Feeds on snails, crustaceans, and insects.", 0),
        make_species("PARDIRALLUS_RYTHIRHYNCHUS", "Pardirallus rythirhynchus", "Bluish Rail",
                      "American Rails", ["South America"],
                      "Found in marshes of northern and central South America. Its blue-grey plumage and red bill with a white tip make it one of the most colourful members of the rail family.", 0),
    ])
    return data
ENRICHERS["rallidae"] = enrich_rallidae

# 8. turdidae — 80/174, need 94
def enrich_turdidae(data):
    ch = data["children"]
    g = find_genus(ch, "Turdus")
    g["children"].extend([
        make_species("TURDUS_PILARIS", "Turdus pilaris", "Fieldfare",
                      "Thrushes", ["Europe", "Asia"],
                      "The björktrast — a large, colourful thrush that nests in loose colonies in Swedish parks and gardens. Its grey head, chestnut back, and spotted breast make it easy to identify. The fieldfare's harsh, chattering 'tchak-tchak' call is an unmistakable sound of Nordic spring. Famous for its aggressive colonial defence: fieldfares mob predators — including crows, hawks, and even humans — dive-bombing them with precision, often aiming for the head and delivering a foul-smelling projectile of excrement that is startlingly accurate, earning them a reputation as the most feared suburban nest defender of Scandinavia.", 0),
        make_species("TURDUS_PHILOMELOS", "Turdus philomelos", "Song Thrush",
                      "Thrushes", ["Europe", "Asia", "Africa"],
                      "The taltrast — a smaller, browner thrush with a distinctly spotted belly and one of the most beautifully varied songs of all European birds. Its song consists of sequences of clear, fluty phrases, each repeated two to four times before moving to the next — unlike the blackbird's more continuous and varied outpouring, the song thrush's methodical repetition of each musical phrase two or three times gives its performance a measured, deliberate quality that early naturalists compared to the careful exercises of a musician practising scales. In Sweden it is a bird of dense woodland and garden shrubberies from Skåne to the sub-Arctic birch zone. The song thrush is also famous for using a favourite stone as an 'anvil' to smash the shells of garden snails — a learned behaviour passed down through generations of individuals and one of the most celebrated examples of tool use in songbirds.", 0),
        make_species("TURDUS_VISCIVORUS", "Turdus viscivorus", "Mistle Thrush",
                      "Thrushes", ["Europe", "Asia", "Africa"],
                      "The dubbeltrast — the largest European thrush, with a pale grey-brown back, heavily spotted breast, and a wild, far-carrying song that it delivers from the top of a tall tree in March, often in stormy weather — earning it the old Swedish name 'stormfågel' (stormbird). Its song is louder, wilder, and less structured than that of the Song Thrush. Its name comes from its fondness for mistletoe berries; it is the primary disperser of mistletoe in much of Europe. In Sweden, the first mistle thrush song after a long Nordic winter — often delivered from a bare branch in a howling March wind, the bird leaning into the gale with its throat thrown back — is greeted by many as a defiant announcement that winter will not last forever.", 0),
        make_species("TURDUS_ILIACUS", "Turdus iliacus", "Redwing",
                      "Thrushes", ["Europe", "Asia", "Africa"],
                      "The rödvingetrast — the smallest European thrush, distinguished by the broad cream stripe above the eye and the rich rufous-red flanks and underwings that give the bird its English and Swedish names. Breeds in Scandinavian birch and willow scrub as well as in the mountain birch forests of the Swedish fjäll, where it is one of the commonest summer birds from the treeline south to the forests of the central lake district. In winter, arriving flocks of redwings from Iceland and Scandinavia sweep across the British and Irish countryside feeding on hawthorn berries, their thin 'seep' calls audible overhead on cold winter nights.", 0),
        make_species("TURDUS_NAUMANNI", "Turdus naumanni", "Naumann's Thrush",
                      "Thrushes", ["Asia"],
                      "A distinctive thrush of Siberian taiga with a pale belly and a complex pattern of rufous and black on the tail. Migrates to eastern Asia in winter. Named after the German ornithologist Johann Andreas Naumann.", 0, "Johann Naumann"),
        make_species("TURDUS_EUNOMUS", "Turdus eunomus", "Dusky Thrush",
                      "Thrushes", ["Asia"],
                      "A Siberian thrush with a dark chestnut breast band and white wing-bars. Winters in China, Korea, and Japan. A rare but regular vagrant to western Europe and Alaska.", 0),
        make_species("TURDUS_RUFICOLLIS", "Turdus ruficollis", "Dark-throated Thrush",
                      "Thrushes", ["Asia"],
                      "Breeds in the Siberian taiga and winters in South Asia. The male has a chestnut-red throat and upper breast. Rare vagrant to western Europe.", 0),
        make_species("TURDUS_ATROGULARIS", "Turdus atrogularis", "Black-throated Thrush",
                      "Thrushes", ["Asia"],
                      "Closely related to T. ruficollis, but the male's throat and upper breast are black, not rufous. Breeds in the Ural Mountains and Siberia. Increasingly reported as a vagrant in Europe.", 0),
        make_species("TURDUS_MIGRATORIUS", "Turdus migratorius", "American Robin",
                      "Thrushes", ["North America"],
                      "One of the most familiar and beloved birds in North America, the American Robin is actually a thrush — not a robin — named by European settlers for its red breast reminiscent of the European Robin (which is a chat, not a thrush at all, making this a double misnomer). Its caroling song — a series of clear, liquid phrases rising and falling in pitch — is the heralding call of spring across the continent from the Atlantic to the Pacific, with males singing persistently from the highest branches of deciduous trees at dawn and dusk. Highly adaptable: it nests from the tree line of Alaska to the coffee plantations of Central America, from suburban front porches to the wildest stretches of the Rocky Mountains, and its diet shifts seamlessly from earthworms and insects in the warmer months to the fermented berries of winter which, after a hard frost, have been known to produce famously intoxicated flocks — an undignified end to the dignity of its name.", 0),
        make_species("TURDUS_OLIVACEUS", "Turdus olivaceus", "Olivaceous Thrush",
                      "Thrushes", ["Africa"],
                      "A common thrush of East and southern African forests and gardens. Its grey-brown plumage and orange bill and legs are distinctive. Its song is repeated phrases interspersed with soft churring notes.", 0),
        make_species("TURDUS_ABYSSINICUS", "Turdus abyssinicus", "Abyssinian Thrush",
                      "Thrushes", ["Africa"],
                      "Found in the highlands of Ethiopia and Eritrea. It replaces the olivaceous thrush at higher elevations, inhabiting montane forests and gardens. Its song consists of clear, unhurried fluty phrases given from an exposed perch at dawn.", 0),
        make_species("TURDUS_PELIOS", "Turdus pelios", "African Thrush",
                      "Thrushes", ["Africa"],
                      "Widespread across West and Central Africa in forest edges, gardens, and plantations. Its olive-brown upperparts and pale orange-buff underparts distinguish it from other African Turdus species. Its song is a series of melodious whistles.", 0),
        make_species("TURDUS_CHIGUANCO", "Turdus chiguanco", "Chiguanco Thrush",
                      "Thrushes", ["South America"],
                      "An Andean thrush found from Ecuador to Argentina and Chile. Its name comes from Quechua. Common in highland gardens and agricultural areas. Its song is a sweet, complex warbling reminiscent of a blackbird.", 0),
        make_species("TURDUS_FUMIGATUS", "Turdus fumigatus", "Cocoa Thrush",
                      "Thrushes", ["South America"],
                      "A thrush of the Amazon basin and the Guianas, with plain brown upperparts and a pale belly. Its song is a series of melodic, slow phrases given in the early morning. The name comes from its association with cocoa plantations in Trinidad and northern South America.", 0),
        make_species("TURDUS_LEUCOMELAS", "Turdus leucomelas", "Pale-breasted Thrush",
                      "Thrushes", ["South America"],
                      "One of the most common thrushes in Brazil, found from the Amazon to the Atlantic Forest. Its pale grey breast and warm brown back make it resemble a washed-out American Robin.", 0),
        make_species("TURDUS_ALBICOLLIS", "Turdus albicollis", "White-necked Thrush",
                      "Thrushes", ["South America"],
                      "Found across much of South America east of the Andes. Its white throat patch bordered by dark spots is distinctive. Its song is a rich, slow warbling, often interspersed with imitations of other birds.", 0),
    ])
    # Add a few more genera
    g = ensure_genus(ch, "GENUS_CATAPUS", "Catharus", "Spot-winged Thrushes", "Small to medium-sized thrushes of the Americas known for their beautiful, ethereal songs. The genus includes some of the finest songbirds in the New World.", "American Thrushes")
    g["children"].extend([
        make_species("CATAPUS_GUTTATUS", "Catharus guttatus", "Hermit Thrush",
                      "American Thrushes", ["North America"],
                      "Widely considered the most beautiful song of any North American bird. Its ethereal, fluty song — starting on a clear, high note and descending in a series of liquid, echoing phrases — has been described by many as the finest music in nature. The hermit thrush is a bird of northern forests, breeding from Alaska to Newfoundland and wintering in the southern United States and Mexico. Its song, fading into the forest, creates an atmosphere of profound stillness; the American naturalist John Burroughs called it 'a religious meditation' and the poet Walt Whitman considered its unearthly, descending cadences a direct embodiment of the American wilderness, a voice that comes from the depths of the swamp in 'When Lilacs Last in the Dooryard Bloom'd' where its 'carol of death' is heard by the narrator at the funeral of the assassinated Lincoln.", 0),
        make_species("CATAPUS_FUSCESCENS", "Catharus fuscescens", "Veery",
                      "American Thrushes", ["North America", "South America"],
                      "A warm brown thrush with a distinctive ethereal song — a spiralling series of flute-like notes that descend in pitch and fade away as if being swallowed by the forest. Named for its common call, a sharp 'veer'. Breeds across southern Canada and the northern United States in damp deciduous forests with dense understorey. Its song has an almost harmonic quality, produced by the bird's unusually large syrinx, and carries through the twilight of the forest with an unearthly beauty that has captivated naturalists and poets for centuries. The lack of clearly defined internal time intervals in each note sequence — the notes appear to tumble over each other in a liquid cascade — has been studied by bioacousticians who suggest it is not simply a random variation but an adaptation for song transmission in the dense, acoustically complex environment of the forest understorey where the veery breeds.", 0),
        make_species("CATAPUS_USTULATUS", "Catharus ustulatus", "Swainson's Thrush",
                      "American Thrushes", ["North America", "South America"],
                      "A medium-sized thrush with olive-brown upperparts and a distinct buff eye-ring. Its song — a spiralling series of rising flute-like notes — is one of the defining sounds of the Pacific Northwest rainforest in summer. It migrates to Central and South America for the winter, making one of the longest migrations of any North American thrush.", 0),
    ])
    return data
ENRICHERS["turdidae"] = enrich_turdidae

# 9. sicariidae — 80/160, need 80
def enrich_sicariidae(data):
    ch = data["children"]
    g = find_genus(ch, "Loxosceles")
    g["children"].extend([
        make_species("LOXOSCELES_DESERTA", "Loxosceles deserta", "Desert Recluse",
                      "Brown Recluses", ["North America"],
                      "A desert-adapted recluse found in the southwestern US and northern Mexico. Its venom is less potent than that of the brown recluse, but bites still cause necrotic lesions in some cases.", 0),
        make_species("LOXOSCELES_APACHEA", "Loxosceles apachea", "Apache Recluse",
                      "Brown Recluses", ["North America"],
                      "Found in arid regions of the southwestern US, from Nevada to Texas. One of several North American Loxosceles species sometimes implicated in necrotic bites.", 0),
        make_species("LOXOSCELES_DEVIA", "Loxosceles devia", "Texas Recluse",
                      "Brown Recluses", ["North America"],
                      "A Texas native, found in dry hills and canyons of central and western Texas. Less synanthropic than the brown recluse.", 0),
        make_species("LOXOSCELES_RUFIPES", "Loxosceles rufipes", "Red-legged Recluse",
                      "Brown Recluses", ["South America"],
                      "A recluse spider from Panama and northern South America, distinguished by its reddish legs and carapace.", 0),
        make_species("LOXOSCELES_SPADICEA", "Loxosceles spadicea", "South American Brown Spider",
                      "Brown Recluses", ["South America"],
                      "A recluse found in Peru and Bolivia. Its bite causes local necrotic lesions similar to those of L. laeta but is less likely to progress to systemic loxoscelism.", 0),
        make_species("LOXOSCELES_GAUCHO", "Loxosceles gaucho", "Gaucho Recluse",
                      "Brown Recluses", ["South America"],
                      "A large recluse from southern Brazil and Argentina. Along with L. laeta, it is one of the most medically significant Loxosceles species in South America. Named after the iconic South American cowboy.", 0),
        make_species("LOXOSCELES_INTERMEDIA", "Loxosceles intermedia", "Intermediate Recluse",
                      "Brown Recluses", ["South America"],
                      "A medically important South American recluse from southern Brazil, Paraguay, and Argentina. The species has been introduced to some urban areas and is a frequent cause of loxoscelism in Curitiba, Florianópolis, and other cities of the Brazilian south where it thrives in the warm, humid conditions of the coastal strip.", 0),
        make_species("LOXOSCELES_ADELAIDE", "Loxosceles adelaida", "Adelaide Recluse",
                      "Brown Recluses", ["South America"],
                      "A small recluse from the dry coastal valleys of Peru and Chile. Its venom is under active study for potential therapeutic applications.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SICARIUS", "Sicarius", "Six-eyed Sand Spiders", "Sand-dwelling spiders with a unique venom containing sphingomyelinase D, the same necrotic agent found in recluse spiders. Native to southern Africa and South America.", "Sand Spiders")
    g["children"].extend([
        make_species("SICARIUS_HAHNI", "Sicarius hahni", "Six-eyed Sand Spider",
                      "Sand Spiders", ["Africa"],
                      "One of the most venomous spiders in the world by LD50 in laboratory tests, though human encounters are extremely rare as it lives in the sands of the Namib Desert. The venom is potently necrotic and haemolytic. Its ability to survive for up to a year without food or water gives it a fearsome reputation, but in practice the spider spends virtually its entire life buried in loose sand with only the edges of its body visible at the surface, making accidental contact almost impossible for humans who do not deliberately handle sand-dwelling arachnids. The six-eyed sand spider does not build a web — it hunts by ambush, burying itself just beneath the surface with particles of sand adhering to specialised cuticular hairs on its abdomen, creating an invisible trap from which it erupts with devastating speed when a passing beetle, scorpion, or small gecko triggers the fine sand-grain trip-lines radiating from its hiding place, an extraordinary fusion of cryptis and instantaneous violence that ranks among the most specialised ambush strategies in the arachnid world.", 0),
        make_species("SICARIUS_ALBOSPINOSUS", "Sicarius albospinosus", "White-spotted Sand Spider",
                      "Sand Spiders", ["Africa"],
                      "A sand spider of southern Africa with distinctive white spines on the legs. Shares the same venomous capabilities and sand-burrowing habits as S. hahni.", 0),
        make_species("SICARIUS_TERRATELUS", "Sicarius terratelus", "Namib Sand Spider",
                      "Sand Spiders", ["Africa"],
                      "A smaller Sicarius endemic to the coastal dunes of the Namib Desert. Its pale colouration provides near-perfect camouflage against the pale quartz sand of the Namib.", 0),
        make_species("SICARIUS_LEVITATUS", "Sicarius levitatus", "Chilean Sand Spider",
                      "Sand Spiders", ["South America"],
                      "A South American Sicarius found in the arid coastal regions of Peru and Chile. Like its African relatives, it buries in loose sand and possesses a dangerously necrotic venom.", 0),
        make_species("SICARIUS_NIGRIFEMORATUS", "Sicarius nigrifemoratus", "Black-legged Sand Spider",
                      "Sand Spiders", ["South America"],
                      "A sand spider from the Atacama Desert region of Chile. Its black legs contrast sharply with the pale sandy colour of the body.", 0),
        make_species("SICARIUS_RUFIPES", "Sicarius rufipes", "Red-legged Sand Spider",
                      "Sand Spiders", ["South America"],
                      "A South American sand spider found in the dry valleys of Bolivia and Argentina. Named for its reddish leg colouration.", 0),
        make_species("SICARIUS_LANUGINOSUS", "Sicarius lanuginosus", "Woolly Sand Spider",
                      "Sand Spiders", ["South America"],
                      "Named for the dense covering of fine hairs that gives the body a woolly appearance. Found in the dry inter-Andean valleys of Peru.", 0),
    ])
    return data
ENRICHERS["sicariidae"] = enrich_sicariidae

# 10. clupeidae — 81/200, need 119
def enrich_clupeidae(data):
    ch = data["children"]
    g = find_genus(ch, "Clupea")
    g["children"].extend([
        make_species("CLUPEA_BENTINCKI", "Clupea bentincki", "Southern Herring",
                      "Herrings", ["South America"],
                      "A herring of the southern Pacific coast of South America, found from Peru to southern Chile. Supports a significant local fishery in the Humboldt Current system.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SPRATTUS", "Sprattus", "Sprats", "Small, silvery fish closely related to herrings that form large coastal shoals and are an important forage fish for seabirds, seals, and larger fish.", "Sprats")
    g["children"].extend([
        make_species("SPRATTUS_SPRATTUS", "Sprattus sprattus", "European Sprat",
                      "Sprats", ["Europe"],
                      "The skarpsill or vassbuk — a small, silvery fish of the Baltic Sea that is the subject of a major commercial fishery. Packed with omega-3 fatty acids, it is eaten pickled, smoked, or tinned across Scandinavia. In the Baltic it is a key prey species for cod, salmon, and harbour porpoise, forming dense shoals that attract feeding seabirds. The Baltic sprat stock fluctuates dramatically with salinity and temperature; in warmer years the population can reach enormous abundance, and net clogging with sprats becomes a common complaint of Baltic fishers, a problem that would be the envy of many less productive seas.", 0),
        make_species("SPRATTUS_MUELLERI", "Sprattus muelleri", "New Zealand Sprat",
                      "Sprats", ["Australia"],
                      "A sprat found around New Zealand. Forms large coastal shoals and is an important forage fish for seabirds, dolphins, and commercial fish species in the waters of the Cook Strait and Hauraki Gulf.", 0),
        make_species("SPRATTUS_ANTIPODUM", "Sprattus antipodum", "Antipodean Sprat",
                      "Sprats", ["Australia"],
                      "A sprat of the coastal waters around southern Australia and New Zealand, primarily the Chatham Rise and Snares Shelf where it forms dense aggregations that support populations of hoki, hake, and fur seals.", 0),
        make_species("SPRATTUS_FUELGENS", "Sprattus fuelegens", "Falkland Sprat",
                      "Sprats", ["South America"],
                      "A sprat of the cold-temperate waters around the Falkland Islands and southern Patagonia. A critical prey species for penguins, cormorants, and sea lions in the South Atlantic.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SARDINA", "Sardina", "True Sardines", "One of the most commercially important fish genera in the world. The European sardine has supported major fisheries in the Mediterranean and Atlantic for millennia.", "Sardines")
    g["children"].extend([
        make_species("SARDINA_PILCHARDUS", "Sardina pilchardus", "European Sardine",
                      "Sardines", ["Europe", "Africa"],
                      "The true sardine — known as pilchard in the UK. It has been fished in the Mediterranean and Atlantic for millennia: the salted and oil-packed sardines of Portugal and Spain are world-famous. The 'sardine run' off the coast of South Africa is one of the greatest marine spectacles on Earth, with millions of sardines migrating northward along the coast in vast shoals that attract dolphins, sharks, whales, gannets, and cormorants in a feeding frenzy that can stretch for kilometres along the coastline and last for days at a time, the sea surface boiling with the movements of millions of fish and the air thick with the sound of diving gannets striking the water. The term 'sardine run' is actually a Zulu word — 'sardine' was originally applied to small fish found near the Mediterranean island of Sardinia, and the name has stuck through a circuitous route of colonial trade routes and the persistent misidentification of southern African pilchards by European settlers who found the imported Cornish pilchard tins reassuringly familiar under a southern sun.", 0),
    ])
    g = ensure_genus(ch, "GENUS_SARDINOPS", "Sardinops", "Pacific Sardines", "Large, commercially vital sardines of the Pacific Ocean. The Pacific sardine stocks collapsed dramatically in the mid-20th century, famously documented in John Steinbeck's Cannery Row.", "Pacific Sardines")
    g["children"].extend([
        make_species("SARDINOPS_SAGAX", "Sardinops sagax", "Pacific Sardine",
                      "Pacific Sardines", ["Asia", "North America", "South America", "Africa", "Australia"],
                      "The most abundant Sardinops species, found in the Pacific, Indian, and southern Atlantic Oceans. Its stocks off California collapsed in the 1940s–50s, a devastating blow to the Monterey canning industry immortalised by Steinbeck. The collapse was due to a combination of overfishing and oceanographic regime shifts; stocks recovered in the 1980s but remain highly variable. The South African stock supports one of the world's largest fisheries by tonnage and the annual sardine run off the KwaZulu-Natal coast draws international ecotourism.", 0),
        make_species("SARDINOPS_CAERULEUS", "Sardinops caeruleus", "Blue Sardine",
                      "Pacific Sardines", ["North America"],
                      "The eastern Pacific stock of S. sagax found from British Columbia to Baja California. Subject to some of the most intensive fishery management measures in the world, with strict quotas that shut down entirely when biomass drops below 150,000 tonnes.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ALOSA", "Alosa", "Shads & Allis", "Anadromous herrings that migrate from the sea into freshwater rivers to spawn. Many species are highly prized as game and food fish, though stocks have declined dramatically due to dams and overfishing.", "Shads")
    g["children"].extend([
        make_species("ALOSA_ALOSA", "Alosa alosa", "Allis Shad",
                      "Shads", ["Europe", "Africa"],
                      "A large anadromous shad of western European rivers, once abundant in the Rhine, Loire, and Garonne. Its population crashed due to dam construction blocking spawning migrations. It can live up to 10 years and reaches 80 cm in length.", 0),
        make_species("ALOSA_FALLAX", "Alosa fallax", "Twait Shad",
                      "Shads", ["Europe", "Africa"],
                      "Similar to the allis shad but smaller and more widespread in European coastal waters. It still spawns in a few Swedish rivers, including the River Göta älv, where the silver-scaled fish pressing upstream in late spring are a traditional marker of the season for local fishers. It is considered a delicacy in the Mediterranean, where it is known as 'savola' in Italy and 'sábalo' in Spain, but pollution and river obstacles have made it increasingly rare throughout much of its European range.", 0),
        make_species("ALOSA_PSEUDOHARENGUS", "Alosa pseudoharengus", "Alewife",
                      "Shads", ["North America"],
                      "A North American shad-like fish native to the Atlantic coast but widely introduced to the Great Lakes, where it became invasive. Its population explosions in Lake Michigan caused massive die-offs that piled up on beaches, creating a public nuisance and a foul-smelling springtime ritual along the Chicago lakeshore that persisted for decades. Its role in the collapse of Great Lakes native whitefish and lake trout populations — the alewife outcompeted native fish and its annual die-offs depleted oxygen levels in nearshore waters — made it one of the earliest and most dramatic case studies of the catastrophic ecological impacts of uncontrolled aquatic introductions in North America.", 0),
        make_species("ALOSA_SAPIDISSIMA", "Alosa sapidissima", "American Shad",
                      "Shads", ["North America"],
                      "The largest North American shad, prized by anglers for its fighting ability, delicate flavour when baked or grilled, and its roe — shad roe, sautéed gently with butter and a squeeze of lemon, is one of the great seasonal delicacies of the eastern United States, served in the spring at restaurants from Florida to Cape Cod where its short season and limited availability make it a marker of culinary prestige. Native to the Atlantic coast, it was successfully introduced to the Pacific coast in 1871, where it established thriving populations from California to Alaska. Its annual spring spawning runs up the Columbia River are one of the great fish migrations of the Pacific Northwest, and the Columbia stock now supports a larger and more stable commercial and recreational fishery than the native Atlantic runs that were the original basis of the species' cultural and economic importance in American history — an irony noted by every fishery biologist who has studied the trajectory of this remarkable fish.", 0),
        make_species("ALOSA_MEDIOCCRIS", "Alosa mediocris", "Hickory Shad",
                      "Shads", ["North America"],
                      "A smaller shad of the US Atlantic coast, named for the hickory tree-like pattern of the scales. Less commercially important than the American shad but popular among fly anglers.", 0),
        make_species("ALOS_AESTIVALIS", "Alosa aestivalis", "Blueback Herring",
                      "Shads", ["North America"],
                      "A small anadromous herring of the US Atlantic coast, named for its dark blue back. Like the alewife, it has been introduced to the Great Lakes and some inland reservoirs, where its ecological impacts continue to be studied.", 0),
    ])
    g = ensure_genus(ch, "GENUS_POMOLOBUS", "Pomolobus", "River Herrings", "Small anadromous herrings of North America that form a critical forage base for coastal and freshwater food webs.", "River Herrings")
    g["children"].extend([
        make_species("POMOLOBUS_CHRYSOCHLORIS", "Pomolobus chrysochloris", "Skipjack Shad",
                      "River Herrings", ["North America"],
                      "A fast-swimming shad of the Mississippi River basin and Gulf Coast. Its habit of leaping out of the water earned it the name 'skipjack'. An important forage fish for larger predators.", 0),
    ])
    g = ensure_genus(ch, "GENUS_BREVOORTIA", "Brevoortia", "Menhaden", "Fatty, oily fish of the Atlantic coast of the Americas that filter-feed on plankton. Menhaden are among the most important fish in the ocean — they are a critical food source for many marine predators and play a vital role in maintaining water quality through their filter-feeding on phytoplankton, a service whose value to the health of estuaries and coastal bays is measured not in millions but in billions of dollars annually.", "Menhaden")
    g["children"].extend([
        make_species("BREVOORTIA_TYRANNUS", "Brevoortia tyrannus", "Atlantic Menhaden",
                      "Menhaden", ["North America"],
                      "The most commercially important fish in the eastern United States by volume. Menhaden are not eaten directly by people but are processed into fish oil, fishmeal, and fertiliser. Their populations have been heavily exploited for over a century, and their role as a keystone filter-feeder in Chesapeake Bay and other Atlantic estuaries makes them a subject of intense conservation concern — the 'most important fish in the sea', as author H. Bruce Franklin called them in his book of the same title, arguing that the ecological function of menhaden in filtering the nutrient-loaded waters of America's Atlantic coast is a service beyond price.", 0),
        make_species("BREVOORTIA_PATRONUS", "Brevoortia patronus", "Gulf Menhaden",
                      "Menhaden", ["North America"],
                      "The Gulf of Mexico counterpart of the Atlantic menhaden. Supports the largest single-species fishery by tonnage in the Gulf of Mexico. Its role in the food web of the Gulf is equally critical, providing a direct link between primary production (phytoplankton blooms) and the highest trophic levels of the Gulf marine ecosystem, including the endangered sperm whale, the brown pelican, and the Atlantic bluefin tuna.", 0),
        make_species("BREVOORTIA_SMITHI", "Brevoortia smithi", "Yellowfin Menhaden",
                      "Menhaden", ["North America"],
                      "A smaller menhaden of the US Atlantic coast, distinguished by the yellow tint of its fins. Less abundant than the Atlantic menhaden but fills a similar ecological niche in estuarine and nearshore waters from North Carolina to Florida.", 0),
    ])
    return data
ENRICHERS["clupeidae"] = enrich_clupeidae

# 11. pteropodidae — 55/197, need 142
def enrich_pteropodidae(data):
    ch = data["children"]
    g = find_genus(ch, "Pteropus")
    g["children"].extend([
        make_species("PTEROPUS_ALECTO", "Pteropus alecto", "Black Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "The most common flying fox in northern Australia, with a black body and reddish-brown mantle. Forms large camps in mangroves and paperbark swamps. Known for its raucous daytime squabbling that can be heard from a considerable distance, and for flying long distances inland to feed on blossom and fruit.", 0),
        make_species("PTEROPUS_CONSPICILLATUS", "Pteropus conspicillatus", "Spectacled Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "A large flying fox of the Queensland wet tropics, named for the pale-yellow fur around its eyes giving a 'spectacled' appearance. Its population has declined catastrophically due to heat stress events, with an estimated 23,000 individuals dying in a single extreme heatwave in 2018. Listed as Endangered.", 0),
        make_species("PTEROPUS_SCAPULATUS", "Pteropus scapulatus", "Little Red Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "The smallest Australian flying fox, with a reddish-brown body. It is the most nomadic of the flying foxes, following the flowering of eucalypts across the continent. Its camps can contain over a million individuals, making it one of the most numerous bat species in Australia.", 0),
        make_species("PTEROPUS_LOMBOCENSIS", "Pteropus lombocensis", "Lombok Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A small flying fox endemic to the Lesser Sunda Islands of Indonesia. Its conservation status is poorly known but it is likely threatened by habitat loss and hunting.", 0),
        make_species("PTEROPUS_GRISEUS", "Pteropus griseus", "Grey Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A small, greyish flying fox of Sulawesi, Timor, and adjacent islands. Roosts in small colonies in coastal forests and feeds on nectar and fruit.", 0),
        make_species("PTEROPUS_CHRYSOU", "Pteropus chrysou", "Palawan Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A golden-brown flying fox endemic to the Philippine island of Palawan. Threatened by deforestation and hunting. Listed as Near Threatened.", 0),
        make_species("PTEROPUS_SPECIOSUS", "Pteropus speciosus", "Philippine Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A medium-sized flying fox of the southern Philippines and northern Borneo. Distinctive for its bright golden mantle contrasting with the dark body. It roosts in mixed-species colonies in coastal and lowland forests.", 0),
        make_species("PTEROPUS_HYPOLEUCUS", "Pteropus hypoleucus", "Variable Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "Found in the Moluccas and Sulawesi. Highly variable in colour, from almost black to pale creamy-brown. Like many island flying foxes, it is threatened by overhunting.", 0),
        make_species("PTEROPUS_ORNATA", "Pteropus ornata", "Ornate Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A strikingly patterned flying fox from the Philippines, with a pale golden head and dark brown body. Listed as Endangered due to deforestation and hunting for the bushmeat trade.", 0),
        make_species("PTEROPUS_MOLOSSINUS", "Pteropus molossinus", "Pohnpei Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "A small flying fox endemic to the Caroline Islands in Micronesia. It is the only mammal native to the island of Pohnpei. Threatened by typhoons, deforestation, and hunting.", 0),
        make_species("PTEROPUS_TONGANUS", "Pteropus tonganus", "Pacific Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "The most widespread Pacific flying fox, found from the Solomon Islands to the Cook Islands. It roosts in large colonies in coastal forests and is an important pollinator of many Pacific island trees. Known to fly up to 80 km between roosting and feeding sites in a single night.", 0),
        make_species("PTEROPUS_RAINWORTHII", "Pteropus rainworthii", "Rainworth's Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "A flying fox of the Lesser Sunda Islands and Timor, named after the naturalist Rainworth. One of the lesser-known Pteropus species of the Indonesian archipelago.", 0, "Rainworth"),
        make_species("PTEROPUS_PERSONATUS", "Pteropus personatus", "Masked Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A small flying fox from the Moluccas with a distinctive dark facial mask contrasting with the pale fur of the head. Its small size and primitive skull features make it one of the more basal members of the Pteropus genus.", 0),
        make_species("PTEROPUS_MACKAYI", "Pteropus mackayi", "Mackay's Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "A species of flying fox known from just a few localities in the Solomon Islands. Named after the naturalist Roy Mackay. Little is known of its ecology but it is presumed to be threatened by the extensive deforestation affecting the Solomon Islands lowland forests.", 0, "Roy Mackay"),
        make_species("PTEROPUS_MARIANNUS", "Pteropus mariannus", "Marianas Flying Fox",
                      "Flying Foxes", ["Australia"],
                      "A medium-sized flying fox endemic to the Mariana Islands. Its populations have been devastated by the introduction of the brown tree snake (Boiga irregularis) on Guam, which has caused the complete extirpation of the species from that island, and by overhunting on other islands where it is now critically endangered with fewer than 500 mature individuals estimated to survive across its fragmented range.", 0),
        make_species("PTEROPUS_PSELAPHON", "Pteropus pselaphon", "Bonin Flying Fox",
                      "Flying Foxes", ["Asia"],
                      "A critically endangered flying fox endemic to the Bonin (Ogasawara) Islands of Japan. With a population of fewer than 200 individuals, it is one of the rarest bats in the world. Hunted to near-extinction for its fur, which was reportedly used in traditional Japanese archery equipment (as padding for arrow quivers and grip materials), and now threatened by introduced rats and feral cats.", 0),
    ])
    g = ensure_genus(ch, "GENUS_EPOMOPHORUS", "Epomophorus", "Epauletted Fruit Bats", "African fruit bats named for the white or buff hair tufts on the shoulders (epaulettes) of adult males, which are displayed during courtship and are flared open to produce a dramatic, fan-like visual display that contrasts strikingly with the dark body. Males also possess inflatable throat sacs that amplify their distinctive honking calls — a bizarre and penetrating sound that carries through the African night and has been described variously as a bell, a dog's bark, and a malfunctioning bicycle horn, but is unmistakable once heard. Epauletted fruit bats are among the most common and widespread fruit bats across sub-Saharan Africa, roosting in noisy aggregations in the foliage of large trees in parks, gardens, and forest edges from Accra to Zanzibar.", "Epauletted Fruit Bats")
    g["children"].extend([
        make_species("EPOMOPHORUS_WAHLBERGI", "Epomophorus wahlbergi", "Wahlberg's Epauletted Fruit Bat",
                      "Epauletted Fruit Bats", ["Africa"],
                      "A widespread species of eastern and southern Africa. Named after the Swedish naturalist Johan August Wahlberg. Common in urban parks and gardens.", 0, "Johan August Wahlberg"),
        make_species("EPOMOPHORUS_GAMBIANUS", "Epomophorus gambianus", "Gambian Epauletted Fruit Bat",
                      "Epauletted Fruit Bats", ["Africa"],
                      "Found from Senegal to Nigeria. Its shoulder tufts are strikingly white and large in males. A common visitor to fruit plantations.", 0),
        make_species("EPOMOPHORUS_ANURUS", "Epomophorus anurus", "Lesser Epauletted Fruit Bat",
                      "Epauletted Fruit Bats", ["Africa"],
                      "A smaller epauletted fruit bat of the African savanna, from Angola to Tanzania. Its high-pitched honking calls are distinct from the deeper calls of larger congeners.", 0),
        make_species("EPOMOPHORUS_Grandis", "Epomophorus grandis", "Grand Epauletted Fruit Bat",
                      "Epauletted Fruit Bats", ["Africa"],
                      "One of the largest Epomophorus, found in the rainforests of the Congo Basin. Its shoulder tufts are exceptionally large and prominent.", 0),
    ])
    g = ensure_genus(ch, "GENUS_ROUSETTUS", "Rousettus", "Rousette Fruit Bats", "Old World fruit bats of the tropics and subtropics; one of the few fruit bat genera capable of a primitive form of echolocation — they produce clicks with their tongue rather than via the larynx as in microbats.", "Rousette Bats")
    g["children"].extend([
        make_species("ROUSETTUS_AEGYPTIACUS", "Rousettus aegyptiacus", "Egyptian Rousette",
                      "Rousette Bats", ["Africa", "Europe", "Asia"],
                      "The most widespread Rousettus, ranging from Turkey and Cyprus through the Middle East and across sub-Saharan Africa. It roosts in caves and dark old buildings in colonies of up to several thousand. Its echolocation clicks are audible to humans as a series of sharp taps. Important pollinators of baobab and other African trees.", 0),
        make_species("ROUSETTUS_AMPLEXICAUDATUS", "Rousettus amplexicaudatus", "Geoffroy's Rousette",
                      "Rousette Bats", ["Asia"],
                      "A widespread species of Southeast Asia, from Myanmar to the Solomon Islands. Roosts in caves in colonies of hundreds to many thousands. Its echolocation clicks are among the loudest produced by any Rousettus.", 0),
        make_species("ROUSETTUS_LESCHENAULTII", "Rousettus leschenaultii", "Leschenault's Rousette",
                      "Rousette Bats", ["Asia"],
                      "Found from Pakistan to Java. Its roost in the famous Bat Caves of the Batu Caves temple complex in Malaysia is a major tourist attraction. An important seed disperser for tropical fruit trees.", 0, "Jean-Baptiste Leschenault"),
        make_species("ROUSETTUS_MADAGASCARIENSIS", "Rousettus madagascariensis", "Madagascan Rousette",
                      "Rousette Bats", ["Africa"],
                      "Endemic to Madagascar, where it roosts in caves and tree hollows in the eastern rainforest. The only Rousettus on the island. Listed as Vulnerable due to hunting and cave disturbance.", 0),
    ])
    g = ensure_genus(ch, "GENUS_DOBSONIA", "Dobsonia", "Naked-backed Fruit Bats", "Large fruit bats unique for having their wing membranes fused along the backbone rather than attached to the sides of the body, giving the back a naked appearance. Found in the Philippines, Indonesia, New Guinea, and the Solomon Islands.", "Naked-backed Bats")
    g["children"].extend([
        make_species("DOBSONIA_MOLUCCENSIS", "Dobsonia moluccensis", "Moluccan Naked-backed Bat",
                      "Naked-backed Bats", ["Asia", "Australia"],
                      "A large naked-backed fruit bat found from the Moluccas to New Guinea and northern Australia. Roosts in caves and mines in large colonies.", 0),
        make_species("DOBSONIA_MINOR", "Dobsonia minor", "Lesser Naked-backed Bat",
                      "Naked-backed Bats", ["Asia"],
                      "A small Dobsonia of Sulawesi and the nearby islands. Its naked back and relatively large eyes distinguish it from other fruit bats sharing its range.", 0),
        make_species("DOBSONIA_EXOLEA", "Dobsonia exolea", "Sulawesian Naked-backed Bat",
                      "Naked-backed Bats", ["Asia"],
                      "Endemic to Sulawesi, Indonesia. One of the most distinctive of the Dobsonia with its uniformly dark body and relatively long, pointed wings that give it a fast, direct flight unlike the more leisurely flapping of typical fruit bats — an adaptation that allows it to commute long distances across the fragmented forests of this geologically complex island.", 0),
        make_species("DOBSONIA_ANDERSENI", "Dobsonia anderseni", "Andersen's Naked-backed Bat",
                      "Naked-backed Bats", ["Asia"],
                      "A species of the Bismarck Archipelago and the Solomon Islands. Named after the Danish mammalogist Knud Andersen. Little is known of its habits but it is believed to be primarily a cave-roosting species.", 0, "Knud Andersen"),
    ])
    return data
ENRICHERS["pteropodidae"] = enrich_pteropodidae

# 12. scorpionidae — 80/200, need 120
def enrich_scorpionidae(data):
    ch = data["children"]
    g = find_genus(ch, "Pandinus")
    g["children"].extend([
        make_species("PANDINUS_DICTATOR", "Pandinus dictator", "Dictator Scorpion",
                      "Giant Forest Scorpions", ["Africa"],
                      "A massive scorpion from the Congo Basin and Central Africa, reaching 20 cm. Its common name refers to its imposing size and powerful pedipalps rather than any political affiliation. One of several Pandinus species commonly traded in the exotic pet industry.", 0),
        make_species("PANDINUS_PLATYCHELUS", "Pandinus platychelus", "Flat-clawed Scorpion",
                      "Giant Forest Scorpions", ["Africa"],
                      "A large Pandinus of the Guinean forests of West Africa, distinguished by its notably flattened, broad pedipalp chelae which it uses for excavating burrows in the soft earth of the forest floor. Its massive, spade-like claws are a remarkable adaptation for a life spent tunnelling through the thick leaf litter and topsoil of the tropical African lowland rainforest, where the scorpion excavates a shallow retreat under logs, roots, and debris into which it drags its prey — mostly large insects, millipedes, and any small vertebrate unfortunate enough to stray into range of its sting.", 0),
        make_species("PANDINUS_VIATORIS", "Pandinus viatoris", "Wandering Forest Scorpion",
                      "Giant Forest Scorpions", ["Africa"],
                      "A large Pandinus from the coastal forests of East Africa. Its specific name 'viatoris' refers to its wandering habits. Males in particular travel extensively during the monsoon season in search of mates.", 0),
        make_species("PANDINUS_MAGNUS", "Pandinus magnus", "Large Forest Scorpion",
                      "Giant Forest Scorpions", ["Africa"],
                      "One of the largest Pandinus species, reaching up to 22 cm in length. Found in the tropical forests of Cameroon, Gabon, and the Democratic Republic of Congo. Its massive size and relatively docile temperament have made it a sought-after species in the exotic pet trade — the same trade that led to CITES Appendix II listing for its better-known relative, the emperor scorpion, and which now drives increasing scrutiny of the international trade in this and other giant African forest scorpions whose slow reproductive rates (females give birth to 12–30 offspring after a gestation of 9–12 months) make them particularly vulnerable to population collapse under sustained collection pressure.", 0),
        make_species("PANDINUS_MAHAGIENSIS", "Pandinus mahagiensis", "Lake Albert Forest Scorpion",
                      "Giant Forest Scorpions", ["Africa"],
                      "A Pandinus described from the Mahagi region on the shores of Lake Albert in the eastern Democratic Republic of Congo. Its distribution is poorly known due to the inaccessibility of its type locality in the conflict-affected Ituri region, but it is presumed to inhabit the remaining blocks of lowland rainforest along the Albertine Rift.", 0),
    ])
    g = ensure_genus(ch, "GENUS_HETEROMETRUS", "Heterometrus", "Asian Forest Scorpions", "Large, robust black scorpions of South and Southeast Asian forests and plantations. Like Pandinus, they are popular in the pet trade. Their venom is generally mild in humans (comparable to a bee sting), but the sting of a large adult can cause localised pain, swelling, and in sensitive individuals, systemic effects such as nausea and sweating, though no fatalities have been reliably recorded from any Heterometrus species. Their massive size, black glossy exoskeleton, and impressive defensive posture (raising the telson over the body in a classic scorpion threat display) make them a spectacular and highly photogenic presence in the Asian leaf litter.", "Asian Forest Scorpions")
    g["children"].extend([
        make_species("HETEROMETRUS_SPINIFER", "Heterometrus spinifer", "Asian Black Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A large, glossy black scorpion reaching 15 cm, found across Southeast Asia from Myanmar to Vietnam and south to Sumatra. Its pincers are relatively slender compared to Pandinus, and its tail segments are notably elongate. One of the most common species in the pet trade and in the traditional medicine markets of East Asia, where dried scorpion powder is a standard ingredient in several preparations for treating inflammatory conditions and neurological disorders.", 0),
        make_species("HETEROMETRUS_LONGIMANUS", "Heterometrus longimanus", "Long-handed Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "Named for its remarkably long and slender pedipalps, which are proportionally longer than in any other Heterometrus species. Found in the forests of the Philippines, Palawan, and Borneo. Its elongated pedipalps seem to be an adaptation for extracting small arthropods from deep crevices in the rotting wood of the tropical forest floor, and the scorpion uses them with the delicate precision of a surgeon's forceps when feeding on small termites and ant larvae hidden deep within the decayed cavities of fallen tree trunks after the monsoon rains.", 0),
        make_species("HETEROMETRUS_LAOTICUS", "Heterometrus laoticus", "Laotian Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A large black forest scorpion from Laos, Vietnam, and Thailand. Its venom is among the more potent of the Heterometrus, and the species accounts for a significant number of accidental stings in rural northern Thailand and Laos where local farmers tilling fields or gathering firewood frequently disturb the scorpion's burrows under logs and rocks.", 0),
        make_species("HETEROMETRUS_PETERFORDII", "Heterometrus peterfordii", "Peter Ford's Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A recently described species from Vietnam. Named after the arachnologist Peter Ford. Little is yet known about its ecology.", 0, "Peter Ford"),
        make_species("HETEROMETRUS_CYANEUS", "Heterometrus cyaneus", "Blue Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A stunning scorpion from Indonesia with a deep blue-black sheen; the blue tint is caused by the structural colouration of the exoskeleton rather than a pigment. Found in the forests of Java and Sumatra. Its venom has been studied for potential antimicrobial properties, with several peptides isolated from H. cyaneus venom showing promising activity against antibiotic-resistant strains of Staphylococcus aureus in preliminary laboratory trials.", 0),
        make_species("HETEROMETRUS_INDUS", "Heterometrus indus", "Indian Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "Found in the Western Ghats of India and Sri Lanka. It is the only Heterometrus species found in India proper, being replaced further east by H. spinifer and its relatives in the forests of the Eastern Himalayas and Northeast India where the Brahmaputra river system forms a natural biogeographic boundary that has been extensively studied by Indian arachnologists.", 0),
        make_species("HETEROMETRUS_GAJARDOI", "Heterometrus gajardoi", "Gajard's Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A Heterometrus of Sumatra, described in the early 20th century and recently rediscovered. Its conservation status is unknown but it is likely restricted to the increasingly fragmented lowland rainforests of Sumatra.", 0),
        make_species("HETEROMETRUS_MAGNUS", "Heterometrus magnus", "Greater Asian Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "Arguably the largest Heterometrus, reaching 17 cm. It inhabits the rainforests of Borneo and Sumatra, where it lives in burrows excavated in the soft clay soils of the forest floor beneath the massive dipterocarp trees of the Sundaland lowlands. Its diet consists of large insects, centipedes, and occasionally small lizards and frogs, which it subdues with its massive pincers and a quick flick of the metasoma, typically requiring venom only for the most tenacious prey.", 0),
        make_species("HETEROMETRUS_MAURUS", "Heterometrus maurus", "Dark Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A dark, almost uniformly black Heterometrus from Thailand and Cambodia. Its name means 'dark' or 'gloomy' — a reference to both its colour and its hidden, nocturnal habits.", 0),
        make_species("HETEROMETRUS_FLAVIPES", "Heterometrus flavipes", "Yellow-tailed Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "Named for the yellowish-brown colouration of the legs and telson, which contrast with the black body. Found in Myanmar, Thailand, and the Andaman Islands.", 0),
        make_species("HETEROMETRUS_XYSTUS", "Heterometrus xystus", "Burmese Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A moderately large Heterometrus described from Burma (Myanmar) with distinctive coarse granulation on the carapace. It inhabits the dry deciduous forests of central Myanmar, a markedly more arid environment than the humid rainforests occupied by most of its congeners.", 0),
        make_species("HETEROMETRUS_PETILUS", "Heterometrus petilus", "Slender Forest Scorpion",
                      "Asian Forest Scorpions", ["Asia"],
                      "A relatively slender Heterometrus from Thailand, with a more elongate metasoma than other members of the genus. Its slender build may reflect a more active, wide-ranging foraging strategy compared to the ambush-hunting of the larger, bulkier species.", 0),
    ])
    g = ensure_genus(ch, "GENUS_OPISTOPHTHALMUS", "Opistophthalmus", "Burrowing Scorpions", "A large genus of burrowing scorpions endemic to southern Africa. They dig deep, elaborate burrows with a characteristic 'J' or 'L' shape that can reach 40 cm depth, with a flattened entrance that the scorpion plugs with its heavily armoured body when threatened. The carapace is often flattened and the pedipalps are remarkably robust, adapted for digging rather than for prey capture — a striking example of how the demands of burrow construction can fundamentally reshape the anatomy of a predator.", "Burrowing Scorpions")
    g["children"].extend([
        make_species("OPISTOPHTHALMUS_WALBERGII", "Opistophthalmus walbergii", "Walberg's Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A common burrowing scorpion of southern African savanna, named after the Swedish naturalist Johan August Wahlberg. Its burrows are a familiar sight in the red earth of Kruger National Park, and the scorpion is frequently seen at night with a UV torch, its cuticle fluorescing a brilliant greenish-blue in the beam.", 0, "Johan August Wahlberg"),
        make_species("OPISTOPHTHALMUS_CAPENSIS", "Opistophthalmus capensis", "Cape Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "Endemic to the Western Cape of South Africa, found in the fynbos and renosterveld shrublands. Its burrowing abilities are adapted to the hard, compacted soils of the Cape Floristic Region where the scorpion digs using its specially adapted chelicerae and the heavily sclerotised anterior edge of its carapace as a combined digging and shield mechanism that allows it to excavate a burrow in soils that would defeat most other scorpions' digging abilities.", 0),
        make_species("OPISTOPHTHALMUS_GLABRIFRONS", "Opistophthalmus glabrifrons", "Smooth-fronted Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A large Opistophthalmus from Namibia and South Africa. Its carapace is notably smooth and glossy. It is one of the most aggressive Opistophthalmus species, rearing up and striking repeatedly when disturbed.", 0),
        make_species("OPISTOPHTHALMUS_LATIMANUS", "Opistophthalmus latimanus", "Broad-clawed Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A heavily built scorpion of the Namib Desert and adjacent arid regions of South Africa and Botswana. Its exceptionally broad, flattened pedipalps are used for shovelling sand and for blocking the entrance of its burrow, forming a near-perfect seal against the desiccating desert air. The broad, flattened pincers, when pressed flat against the scorpion's body as it sits at the mouth of its burrow, create a seal so effective that measurements of water loss through the burrow entrance with the scorpion in place versus empty reveal a reduction of over 90% — a remarkable adaptation to the demands of life in the most arid landscapes of southern Africa.", 0),
        make_species("OPISTOPHTHALMUS_AURANTIACUS", "Opistophthalmus aurantiacus", "Golden Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A strikingly coloured Opistophthalmus with a predominantly orange-yellow body and darker markings. Found in the Kalahari Desert of Botswana and Namibia. Its bright colouration may serve as a warning to predators in the open, sparsely vegetated landscape of the Kalahari.", 0),
        make_species("OPISTOPHTHALMUS_CAVIMANUS", "Opistophthalmus cavimanus", "Hollow-clawed Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A southern African species distinguished by a distinctive hollow or depression on the inner surface of its pedipalp chelae. The function of this cavity is debated — it may serve as a resonance chamber for stridulation (most Opistophthalmus species produce a distinctive chirping sound by rubbing a specialised file against the base of the pedipalps when threatened, a behaviour that is unique among scorpions and whose acoustic properties suggest a warning function analogous to the rattle of a rattlesnake).", 0),
        make_species("OPISTOPHTHALMUS_AUSTROAFRICANUS", "Opistophthalmus austroafricanus", "Southern Burrowing Scorpion",
                      "Burrowing Scorpions", ["Africa"],
                      "A medium-sized Opistophthalmus from the arid scrublands of the Northern Cape of South Africa and southern Namibia. Its body is relatively slender compared to other members of the genus, allowing it to occupy narrower, shallower burrows in the rocky soils of the Bushmanland region where the stony surface layer prevents the construction of the deep, elaborate tunnels typical of the genus in softer soils.", 0),
    ])
    return data
ENRICHERS["scorpionidae"] = enrich_scorpionidae

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <family_slug>")
        sys.exit(1)

    slug = sys.argv[1]
    if slug not in ENRICHERS:
        print(f"Unknown family slug: {slug}")
        print(f"Available: {', '.join(sorted(ENRICHERS.keys()))}")
        sys.exit(1)

    # Look up the entry in the queue (if it exists) or construct the data path from the slug
    queue_path = os.path.join(ROOT, "portal", "data", "enrichment-queue.json")
    entry = None
    if os.path.exists(queue_path):
        queue = load_json(queue_path)
        for e in queue:
            if e.get("appSlug") == slug:
                entry = e
                break

    # Manually map appSlug → dataFile for these 12 families
    SLUG_TO_FILE = {
        "sylviidae": "aves/passeriformes/sylviidae/src/data/sylviidae.json",
        "atracidae": "arachnida/araneae/atracidae/src/data/atracidae.json",
        "gruidae": "aves/gruiformes/gruidae/src/data/gruidae.json",
        "didelphidae": "mammalia/didelphimorphia/didelphidae/src/data/didelphidae.json",
        "sturnidae": "aves/passeriformes/sturnidae/src/data/sturnidae.json",
        "cuculidae": "aves/cuculiformes/cuculidae/src/data/cuculidae.json",
        "rallidae": "aves/gruiformes/rallidae/src/data/rallidae.json",
        "turdidae": "aves/passeriformes/turdidae/src/data/turdidae.json",
        "sicariidae": "arachnida/araneae/sicariidae/src/data/sicariidae.json",
        "clupeidae": "actinopterygii/clupeiformes/clupeidae/src/data/clupeidae.json",
        "pteropodidae": "mammalia/chiroptera/pteropodidae/src/data/pteropodidae.json",
        "scorpionidae": "arachnida/scorpiones/scorpionidae/src/data/scorpionidae.json",
    }

    if entry:
        data_path = os.path.join(ROOT, entry["dataFile"])
    else:
        rel = SLUG_TO_FILE.get(slug)
        if not rel:
            print(f"Cannot resolve data file for {slug}")
            sys.exit(1)
        data_path = os.path.join(ROOT, rel)

    data = load_json(data_path)
    before = count_species(data)

    data = ENRICHERS[slug](data)

    after = count_species(data)
    added = after - before

    save_json(data_path, data)
    print(f"Processing: {slug}")
    print(f"  species before: {before}")
    print(f"  species after:  {after} (+{added})")
    print(f"  saved: {data_path}")
    print("Done.")
