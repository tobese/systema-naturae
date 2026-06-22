#!/usr/bin/env python3
"""Add missing bird families and orders to taxonomy.json and colorRegistry.ts."""

import json
import os
import re

TAXONOMY_PATH = "portal/data/taxonomy.json"
REGISTRY_PATH = "portal/src/colorRegistry.ts"

# Load taxonomy
with open(TAXONOMY_PATH) as f:
    taxonomy = json.load(f)

def find_aves(taxonomy):
    """Find the AVES class node."""
    for phylum in taxonomy.get("children", []):
        for chordata_child in phylum.get("children", []):
            if chordata_child.get("id") == "AVES":
                return chordata_child
    return None

aves = find_aves(taxonomy)
if not aves:
    print("Could not find AVES class!")
    exit(1)

# Get existing order IDs
existing_order_ids = {o["id"] for o in aves.get("children", [])}

# New orders to add (after existing orders, before REPTILIA)
new_orders = [
    {
        "id": "STRUTHIONIFORMES",
        "name": "Struthioniformes",
        "rank": "ORDER",
        "commonName": "Ostriches & allies",
        "description": "Ostriches — the largest living birds. Struthioniformes includes the flightless ratites of Africa. Ostriches are the fastest birds on land, reaching speeds of 70 km/h, and lay the largest eggs of any living bird. Males are striking black-and-white; females are brown.",
        "children": [
            {"id": "FAM_STRUTHIONIDAE", "name": "Struthionidae", "rank": "FAMILY", "commonName": "Ostriches", "appSlug": "struthionidae", "speciesCount": 2, "notableMembers": ["Common Ostrich", "Somali Ostrich"]}
        ]
    },
    {
        "id": "RHEIFORMES",
        "name": "Rheiformes",
        "rank": "ORDER",
        "commonName": "Rheas",
        "description": "Rheas — large, flightless birds of South America, resembling ostriches but smaller. Three-toed feet distinguish them from the two-toed ostrich. Males incubate eggs and raise chicks alone, often gathering clutches from multiple females.",
        "children": [
            {"id": "FAM_RHEIDAE", "name": "Rheidae", "rank": "FAMILY", "commonName": "Rheas", "appSlug": "rheidae", "speciesCount": 2, "notableMembers": ["Greater Rhea", "Lesser Rhea"]}
        ]
    },
    {
        "id": "APTERYGIFORMES",
        "name": "Apterygiformes",
        "rank": "ORDER",
        "commonName": "Kiwis",
        "description": "Kiwis — iconic, flightless birds of New Zealand, unique among birds. They have tiny vestigial wings, hair-like feathers, nostrils at the tip of the bill, and lay the largest egg relative to body size of any bird. Nocturnal and highly endangered, with all five species threatened.",
        "children": [
            {"id": "FAM_APTERYGIDAE", "name": "Apterygidae", "rank": "FAMILY", "commonName": "Kiwis", "appSlug": "apterygidae", "speciesCount": 5, "notableMembers": ["Brown Kiwi", "Great Spotted Kiwi", "Little Spotted Kiwi"]}
        ]
    },
    {
        "id": "CASUARIIFORMES",
        "name": "Casuariiformes",
        "rank": "ORDER",
        "commonName": "Cassowaries & emu",
        "description": "Cassowaries and the Emu — large, flightless birds of Australasia. The Southern Cassowary is often called the world's most dangerous bird for its powerful legs and dagger-like claws. The Emu is Australia's largest bird and can sprint at 50 km/h.",
        "children": [
            {"id": "FAM_CASUARIIDAE", "name": "Casuariidae", "rank": "FAMILY", "commonName": "Cassowaries & emu", "appSlug": "casuariidae", "speciesCount": 4, "notableMembers": ["Southern Cassowary", "Emu"]}
        ]
    },
    {
        "id": "TINAMIFORMES",
        "name": "Tinamiformes",
        "rank": "ORDER",
        "commonName": "Tinamous",
        "description": "Tinamous — secretive, ground-dwelling birds of Central and South America. Despite their quail-like appearance, tinamous are the closest living relatives of the giant flightless ratites. Unlike ratites, they can fly, but poorly. Their whistled songs are characteristic sounds of Neotropical forests.",
        "children": [
            {"id": "FAM_TINAMIDAE", "name": "Tinamidae", "rank": "FAMILY", "commonName": "Tinamous", "appSlug": "tinamidae", "speciesCount": 47, "notableMembers": ["Great Tinamou", "Chilean Tinamou", "Elegant Crested Tinamou"]}
        ]
    },
    {
        "id": "MUSOPHAGIFORMES",
        "name": "Musophagiformes",
        "rank": "ORDER",
        "commonName": "Turacos",
        "description": "Turacos — medium-sized, arboreal birds of sub-Saharan Africa. Their plumage contains unique copper-based pigments (turacin and turacoverdin) found in no other bird group. They are weak fliers but agile clamberers through tree canopies. Their loud, raucous calls are a signature sound of African forests.",
        "children": [
            {"id": "FAM_MUSOPHAGIDAE", "name": "Musophagidae", "rank": "FAMILY", "commonName": "Turacos", "appSlug": "musophagidae", "speciesCount": 23, "notableMembers": ["Great Blue Turaco", "Knysna Turaco", "Violet Turaco"]}
        ]
    },
    {
        "id": "PHAETHONTIFORMES",
        "name": "Phaethontiformes",
        "rank": "ORDER",
        "commonName": "Tropicbirds",
        "description": "Tropicbirds — elegant, white seabirds of tropical oceans with extremely long central tail feathers. They are pelagic, coming to land only to breed on remote islands. Their ringing calls and graceful flight have made them legendary among sailors.",
        "children": [
            {"id": "FAM_PHAETHONTIDAE", "name": "Phaethontidae", "rank": "FAMILY", "commonName": "Tropicbirds", "appSlug": "phaethontidae", "speciesCount": 3, "notableMembers": ["Red-billed Tropicbird", "White-tailed Tropicbird"]}
        ]
    },
    {
        "id": "EUPYPGIIFORMES",
        "name": "Eurypygiformes",
        "rank": "ORDER",
        "commonName": "Kagu & sunbittern",
        "description": "A small order of two remarkable species. The Kagu of New Caledonia has a spectacular crest and powder-down feathers. The Sunbittern of the Americas displays brilliant eyespots on its wings in a threat display. Both exhibit unique features not found in other birds.",
        "children": [
            {"id": "FAM_RHYNOCHETIDAE", "name": "Rhynochetidae", "rank": "FAMILY", "commonName": "Kagu", "appSlug": "rhynochetidae", "speciesCount": 1, "notableMembers": ["Kagu"]},
            {"id": "FAM_EURYPYGIDAE", "name": "Eurypygidae", "rank": "FAMILY", "commonName": "Sunbittern", "appSlug": "eurypygidae", "speciesCount": 1, "notableMembers": ["Sunbittern"]}
        ]
    },
    {
        "id": "COLIIFORMES",
        "name": "Coliiformes",
        "rank": "ORDER",
        "commonName": "Mousebirds",
        "description": "Mousebirds — small, gregarious birds of sub-Saharan Africa named for their mousy-grey plumage and habit of scurrying mouse-like through bushes. They have unique feet with reversible outer toes and feed almost entirely on fruit and leaves. The only order endemic entirely to Africa.",
        "children": [
            {"id": "FAM_COLIIDAE", "name": "Coliidae", "rank": "FAMILY", "commonName": "Mousebirds", "appSlug": "coliidae", "speciesCount": 6, "notableMembers": ["Speckled Mousebird", "White-backed Mousebird", "Red-faced Mousebird"]}
        ]
    },
    {
        "id": "LEPTOSOMIFORMES",
        "name": "Leptosomiformes",
        "rank": "ORDER",
        "commonName": "Cuckoo-roller",
        "description": "The cuckoo-roller — a single species placed in its own order, endemic to Madagascar and the Comoros. Its evolutionary relationships have puzzled ornithologists for centuries; DNA now places it closest to the owls and mousebirds.",
        "children": [
            {"id": "FAM_LEPTOSOMIDAE", "name": "Leptosomidae", "rank": "FAMILY", "commonName": "Cuckoo-roller", "appSlug": "leptosomidae", "speciesCount": 1, "notableMembers": ["Cuckoo-roller"]}
        ]
    },
    {
        "id": "TROGONIFORMES",
        "name": "Trogoniformes",
        "rank": "ORDER",
        "commonName": "Trogons & quetzals",
        "description": "Trogons and quetzals — strikingly colourful birds of tropical forests, with iridescent green and red plumage, a distinctive 'trogon' posture (perching upright with tail drooping), and heterodactyl feet (first two toes forward, two back). The Resplendent Quetzal is the national bird of Guatemala.",
        "children": [
            {"id": "FAM_TROGONIDAE", "name": "Trogonidae", "rank": "FAMILY", "commonName": "Trogons & quetzals", "appSlug": "trogonidae", "speciesCount": 46, "notableMembers": ["Resplendent Quetzal", "Elegant Trogon", "Masked Trogon"]}
        ]
    },
    {
        "id": "BUCEOTIFORMES",
        "name": "Bucerotiformes",
        "rank": "ORDER",
        "commonName": "Hornbills & hoopoes",
        "description": "Hornbills, wood hoopoes, and ground hornbills — birds with large, often casqued bills. Hornbills are famous for their nesting behaviour: the female seals herself inside a tree cavity with mud, leaving only a slit for the male to pass food through. Found across Africa and Asia.",
        "children": [
            {"id": "FAM_PHOENICULIDAE", "name": "Phoeniculidae", "rank": "FAMILY", "commonName": "Wood hoopoes", "appSlug": "phoeniculidae", "speciesCount": 8, "notableMembers": ["Green Wood Hoopoe", "Common Scimitarbill"]},
            {"id": "FAM_BUCORVIDAE", "name": "Bucorvidae", "rank": "FAMILY", "commonName": "Ground hornbills", "appSlug": "bucorvidae", "speciesCount": 2, "notableMembers": ["Southern Ground Hornbill", "Northern Ground Hornbill"]},
            {"id": "FAM_BUCEROTIDAE", "name": "Bucerotidae", "rank": "FAMILY", "commonName": "Hornbills", "appSlug": "bucerotidae", "speciesCount": 62, "notableMembers": ["Great Hornbill", "Rhinoceros Hornbill", "Helmeted Hornbill"]}
        ]
    },
    {
        "id": "CARIAMIFORMES",
        "name": "Cariamiformes",
        "rank": "ORDER",
        "commonName": "Seriemas",
        "description": "Seriemas — long-legged, predatory birds of South American grasslands. They are the closest living relatives of the extinct terror birds (Phorusrhacidae) that dominated South American ecosystems for 60 million years. Seriemas hunt insects, reptiles, and small mammals, striking with powerful feet.",
        "children": [
            {"id": "FAM_CARIAMIDAE", "name": "Cariamidae", "rank": "FAMILY", "commonName": "Seriemas", "appSlug": "cariamidae", "speciesCount": 2, "notableMembers": ["Red-legged Seriema", "Black-legged Seriema"]}
        ]
    }
]

# Families to add to existing orders
families_by_order = {
    "ANSERIFORMES": [
        {"id": "FAM_ANHIMIDAE", "name": "Anhimidae", "rank": "FAMILY", "commonName": "Screamers", "appSlug": "anhimidae", "speciesCount": 3, "notableMembers": ["Horned Screamer", "Southern Screamer"]},
        {"id": "FAM_ANSERANATIDAE", "name": "Anseranatidae", "rank": "FAMILY", "commonName": "Magpie goose", "appSlug": "anseranatidae", "speciesCount": 1, "notableMembers": ["Magpie Goose"]}
    ],
    "GALLIFORMES": [
        {"id": "FAM_MEGAPODIIDAE", "name": "Megapodiidae", "rank": "FAMILY", "commonName": "Megapodes", "appSlug": "megapodiidae", "speciesCount": 22, "notableMembers": ["Australian Brushturkey", "Malleefowl", "Maleo"]},
        {"id": "FAM_CRACIDAE", "name": "Cracidae", "rank": "FAMILY", "commonName": "Curassows & guans", "appSlug": "cracidae", "speciesCount": 56, "notableMembers": ["Great Curassow", "Crested Guan", "Plain Chachalaca"]},
        {"id": "FAM_ODONTOPHORIDAE", "name": "Odontophoridae", "rank": "FAMILY", "commonName": "New World quail", "appSlug": "odontophoridae", "speciesCount": 34, "notableMembers": ["Northern Bobwhite", "California Quail", "Gambel's Quail"]}
    ],
    "CAPRIMULGIFORMES": [
        {"id": "FAM_PODARGIDAE", "name": "Podargidae", "rank": "FAMILY", "commonName": "Frogmouths", "appSlug": "podargidae", "speciesCount": 16, "notableMembers": ["Tawny Frogmouth", "Marbled Frogmouth"]},
        {"id": "FAM_STEATORNITHIDAE", "name": "Steatornithidae", "rank": "FAMILY", "commonName": "Oilbird", "appSlug": "steatornithidae", "speciesCount": 1, "notableMembers": ["Oilbird"]},
        {"id": "FAM_NYCTIBIIDAE", "name": "Nyctibiidae", "rank": "FAMILY", "commonName": "Potoos", "appSlug": "nyctibiidae", "speciesCount": 7, "notableMembers": ["Common Potoo", "Great Potoo"]},
        {"id": "FAM_AEGOTHELIDAE", "name": "Aegothelidae", "rank": "FAMILY", "commonName": "Owlet-nightjars", "appSlug": "aegothelidae", "speciesCount": 9, "notableMembers": ["Australian Owlet-nightjar"]},
        {"id": "FAM_HEMIPROCNIDAE", "name": "Hemiprocnidae", "rank": "FAMILY", "commonName": "Treeswifts", "appSlug": "hemiprocnidae", "speciesCount": 4, "notableMembers": ["Crested Treeswift", "Whiskered Treeswift"]}
    ],
    "CUCULIFORMES": [
        {"id": "FAM_MESITORNITHIDAE", "name": "Mesitornithidae", "rank": "FAMILY", "commonName": "Mesites", "appSlug": "mesitornithidae", "speciesCount": 3, "notableMembers": ["White-breasted Mesite", "Brown Mesite"]}
    ],
    "GRUIFORMES": [
        {"id": "FAM_HELIORNITHIDAE", "name": "Heliornithidae", "rank": "FAMILY", "commonName": "Finfoots", "appSlug": "heliornithidae", "speciesCount": 3, "notableMembers": ["Sungrebe", "African Finfoot"]},
        {"id": "FAM_SAROTHRURIDAE", "name": "Sarothruridae", "rank": "FAMILY", "commonName": "Flufftails", "appSlug": "sarothruridae", "speciesCount": 15, "notableMembers": ["White-spotted Flufftail", "Buff-spotted Flufftail"]},
        {"id": "FAM_PSOPHIIDAE", "name": "Psophiidae", "rank": "FAMILY", "commonName": "Trumpeters", "appSlug": "psophiidae", "speciesCount": 3, "notableMembers": ["Grey-winged Trumpeter", "Green-winged Trumpeter"]},
        {"id": "FAM_ARAMIDAE", "name": "Aramidae", "rank": "FAMILY", "commonName": "Limpkin", "appSlug": "aramidae", "speciesCount": 1, "notableMembers": ["Limpkin"]}
    ],
    "CHARADRIIFORMES": [
        {"id": "FAM_TURNICIDAE", "name": "Turnicidae", "rank": "FAMILY", "commonName": "Buttonquail", "appSlug": "turnicidae", "speciesCount": 18, "notableMembers": ["Small Buttonquail", "Barred Buttonquail", "Painted Buttonquail"]},
        {"id": "FAM_CHIONIDAE", "name": "Chionidae", "rank": "FAMILY", "commonName": "Sheathbills", "appSlug": "chionidae", "speciesCount": 2, "notableMembers": ["Snowy Sheathbill", "Black-faced Sheathbill"]},
        {"id": "FAM_PLUVIANELLIDAE", "name": "Pluvianellidae", "rank": "FAMILY", "commonName": "Magellanic plover", "appSlug": "pluvianellidae", "speciesCount": 1, "notableMembers": ["Magellanic Plover"]},
        {"id": "FAM_IBIDORHYNCHIDAE", "name": "Ibidorhynchidae", "rank": "FAMILY", "commonName": "Ibisbill", "appSlug": "ibidorhynchidae", "speciesCount": 1, "notableMembers": ["Ibisbill"]},
        {"id": "FAM_PLUVIANIDAE", "name": "Pluvianidae", "rank": "FAMILY", "commonName": "Egyptian plover", "appSlug": "pluvianidae", "speciesCount": 1, "notableMembers": ["Egyptian Plover"]},
        {"id": "FAM_ROSTRATULIDAE", "name": "Rostratulidae", "rank": "FAMILY", "commonName": "Painted-snipes", "appSlug": "rostratulidae", "speciesCount": 3, "notableMembers": ["Greater Painted-snipe", "Australian Painted-snipe"]},
        {"id": "FAM_PEDIONOMIDAE", "name": "Pedionomidae", "rank": "FAMILY", "commonName": "Plains-wanderer", "appSlug": "pedionomidae", "speciesCount": 1, "notableMembers": ["Plains-wanderer"]},
        {"id": "FAM_THINOCORIDAE", "name": "Thinocoridae", "rank": "FAMILY", "commonName": "Seedsnipes", "appSlug": "thinocoridae", "speciesCount": 4, "notableMembers": ["Least Seedsnipe", "Rufous-bellied Seedsnipe"]},
        {"id": "FAM_DROMADIDAE", "name": "Dromadidae", "rank": "FAMILY", "commonName": "Crab-plover", "appSlug": "dromadidae", "speciesCount": 1, "notableMembers": ["Crab-plover"]}
    ],
    "PROCELLARIIFORMES": [
        {"id": "FAM_OCEANITIDAE", "name": "Oceanitidae", "rank": "FAMILY", "commonName": "Austral storm petrels", "appSlug": "oceanitidae", "speciesCount": 9, "notableMembers": ["Wilson's Storm Petrel", "White-faced Storm Petrel"]}
    ],
    "PELECANIFORMES": [
        {"id": "FAM_SCOPIDAE", "name": "Scopidae", "rank": "FAMILY", "commonName": "Hamerkop", "appSlug": "scopidae", "speciesCount": 1, "notableMembers": ["Hamerkop"]},
        {"id": "FAM_BALAENICIPITIDAE", "name": "Balaenicipitidae", "rank": "FAMILY", "commonName": "Shoebill", "appSlug": "balaenicipitidae", "speciesCount": 1, "notableMembers": ["Shoebill"]}
    ],
    "CORACIIFORMES": [
        {"id": "FAM_BRACHYPTERACIIDAE", "name": "Brachypteraciidae", "rank": "FAMILY", "commonName": "Ground rollers", "appSlug": "brachypteraciidae", "speciesCount": 5, "notableMembers": ["Short-legged Ground Roller", "Pitta-like Ground Roller"]},
        {"id": "FAM_TODIDAE", "name": "Todidae", "rank": "FAMILY", "commonName": "Todies", "appSlug": "todidae", "speciesCount": 5, "notableMembers": ["Cuban Tody", "Jamaican Tody"]},
        {"id": "FAM_MOMOTIDAE", "name": "Momotidae", "rank": "FAMILY", "commonName": "Motmots", "appSlug": "momotidae", "speciesCount": 14, "notableMembers": ["Blue-crowned Motmot", "Turquoise-browed Motmot"]}
    ],
    "PICIFORMES": [
        {"id": "FAM_GALBULIDAE", "name": "Galbulidae", "rank": "FAMILY", "commonName": "Jacamars", "appSlug": "galbulidae", "speciesCount": 18, "notableMembers": ["Rufous-tailed Jacamar", "Paradise Jacamar"]},
        {"id": "FAM_BUCONIDAE", "name": "Bucconidae", "rank": "FAMILY", "commonName": "Puffbirds", "appSlug": "bucconidae", "speciesCount": 38, "notableMembers": ["Collared Puffbird", "Swallow-winged Puffbird"]},
        {"id": "FAM_CAPITONIDAE", "name": "Capitonidae", "rank": "FAMILY", "commonName": "New World barbets", "appSlug": "capitonidae", "speciesCount": 15, "notableMembers": ["Scarlet-banded Barbet", "Gilded Barbet"]},
        {"id": "FAM_SEMNORNITHIDAE", "name": "Semnornithidae", "rank": "FAMILY", "commonName": "Toucan barbets", "appSlug": "semnornithidae", "speciesCount": 2, "notableMembers": ["Toucan Barbet", "Prong-billed Barbet"]},
        {"id": "FAM_LYBIIDAE", "name": "Lybiidae", "rank": "FAMILY", "commonName": "African barbets", "appSlug": "lybiidae", "speciesCount": 56, "notableMembers": ["Crested Barbet", "Red-and-yellow Barbet", "Black-collared Barbet"]},
        {"id": "FAM_INDICATORIDAE", "name": "Indicatoridae", "rank": "FAMILY", "commonName": "Honeyguides", "appSlug": "indicatoridae", "speciesCount": 17, "notableMembers": ["Greater Honeyguide", "Lesser Honeyguide"]}
    ],
    "PSITTACIFORMES": [
        {"id": "FAM_STRIGOPIDAE", "name": "Strigopidae", "rank": "FAMILY", "commonName": "New Zealand parrots", "appSlug": "strigopidae", "speciesCount": 9, "notableMembers": ["Kea", "Kakapo", "Kaka"]},
        {"id": "FAM_PSITTACULIDAE", "name": "Psittaculidae", "rank": "FAMILY", "commonName": "Old World parrots", "appSlug": "psittaculidae", "speciesCount": 200, "notableMembers": ["Rainbow Lorikeet", "Budgerigar", "Eclectus Parrot"]}
    ],
}

# Passeriformes families - all 104 new families
passeriformes_families = [
    {"id": "FAM_ACANTHISITTIDAE", "name": "Acanthisittidae", "rank": "FAMILY", "commonName": "New Zealand wrens", "appSlug": "acanthisittidae", "speciesCount": 4, "notableMembers": ["Rifleman", "Stephens Island Wren"]},
    {"id": "FAM_SAPAYOIDAE", "name": "Sapayoidae", "rank": "FAMILY", "commonName": "Sapayoa", "appSlug": "sapayoidae", "speciesCount": 1, "notableMembers": ["Sapayoa"]},
    {"id": "FAM_PHILEPITTIDAE", "name": "Philepittidae", "rank": "FAMILY", "commonName": "Asities", "appSlug": "philepittidae", "speciesCount": 4, "notableMembers": ["Velvet Asity", "Sunbird Asity"]},
    {"id": "FAM_EURYLAIMIDAE", "name": "Eurylaimidae", "rank": "FAMILY", "commonName": "Typical broadbills", "appSlug": "eurylaimidae", "speciesCount": 15, "notableMembers": ["Banded Broadbill", "Long-tailed Broadbill"]},
    {"id": "FAM_CALYPTOMENIDAE", "name": "Calyptomenidae", "rank": "FAMILY", "commonName": "African & green broadbills", "appSlug": "calyptomenidae", "speciesCount": 6, "notableMembers": ["African Broadbill", "Green Broadbill"]},
    {"id": "FAM_PITTIDAE", "name": "Pittidae", "rank": "FAMILY", "commonName": "Pittas", "appSlug": "pittidae", "speciesCount": 44, "notableMembers": ["Blue-winged Pitta", "Hooded Pitta", "Gurney's Pitta"]},
    {"id": "FAM_FURNARIIDAE", "name": "Furnariidae", "rank": "FAMILY", "commonName": "Ovenbirds & woodcreepers", "appSlug": "furnariidae", "speciesCount": 315, "notableMembers": ["Rufous Hornero", "White-throated Treerunner"]},
    {"id": "FAM_THAMNOPHILIDAE", "name": "Thamnophilidae", "rank": "FAMILY", "commonName": "Antbirds", "appSlug": "thamnophilidae", "speciesCount": 250, "notableMembers": ["Great Antshrike", "Barred Antshrike", "White-plumed Antbird"]},
    {"id": "FAM_FORMICARIIDAE", "name": "Formicariidae", "rank": "FAMILY", "commonName": "Antthrushes", "appSlug": "formicariidae", "speciesCount": 12, "notableMembers": ["Short-tailed Antthrush", "Rufous-tailed Antthrush"]},
    {"id": "FAM_GRALLARIIDAE", "name": "Grallariidae", "rank": "FAMILY", "commonName": "Antpittas", "appSlug": "grallariidae", "speciesCount": 70, "notableMembers": ["Chestnut-crowned Antpitta", "Undulated Antpitta"]},
    {"id": "FAM_CONOPOPHAGIDAE", "name": "Conopophagidae", "rank": "FAMILY", "commonName": "Gnateaters", "appSlug": "conopophagidae", "speciesCount": 11, "notableMembers": ["Rufous Gnateater", "Chestnut-belted Gnateater"]},
    {"id": "FAM_RHINOCRYPTIDAE", "name": "Rhinocryptidae", "rank": "FAMILY", "commonName": "Tapaculos", "appSlug": "rhinocryptidae", "speciesCount": 63, "notableMembers": ["Magellanic Tapaculo", "Chucao Tapaculo"]},
    {"id": "FAM_MELANOPAREIIDAE", "name": "Melanopareiidae", "rank": "FAMILY", "commonName": "Crescentchests", "appSlug": "melanopareiidae", "speciesCount": 5, "notableMembers": ["Collared Crescentchest", "Elegant Crescentchest"]},
    {"id": "FAM_COTINGIDAE", "name": "Cotingidae", "rank": "FAMILY", "commonName": "Cotingas", "appSlug": "cotingidae", "speciesCount": 66, "notableMembers": ["Andean Cock-of-the-rock", "Screaming Piha", "Purple-throated Fruitcrow"]},
    {"id": "FAM_PIPRIDAE", "name": "Pipridae", "rank": "FAMILY", "commonName": "Manakins", "appSlug": "pipridae", "speciesCount": 54, "notableMembers": ["Red-capped Manakin", "White-bearded Manakin", "Club-winged Manakin"]},
    {"id": "FAM_TITYRIDAE", "name": "Tityridae", "rank": "FAMILY", "commonName": "Tityras & becards", "appSlug": "tityridae", "speciesCount": 45, "notableMembers": ["Masked Tityra", "Rose-throated Becard"]},
    {"id": "FAM_ATRICHORNITHIDAE", "name": "Atrichornithidae", "rank": "FAMILY", "commonName": "Scrubbirds", "appSlug": "atrichornithidae", "speciesCount": 2, "notableMembers": ["Noisy Scrubbird", "Rufous Scrubbird"]},
    {"id": "FAM_CLIMACTERIDAE", "name": "Climacteridae", "rank": "FAMILY", "commonName": "Australasian treecreepers", "appSlug": "climacteridae", "speciesCount": 7, "notableMembers": ["White-throated Treecreeper", "Red-browed Treecreeper"]},
    {"id": "FAM_MALURIDAE", "name": "Maluridae", "rank": "FAMILY", "commonName": "Fairy-wrens", "appSlug": "maluridae", "speciesCount": 29, "notableMembers": ["Superb Fairy-wren", "Splendid Fairy-wren", "Red-backed Fairy-wren"]},
    {"id": "FAM_MELIPHAGIDAE", "name": "Meliphagidae", "rank": "FAMILY", "commonName": "Honeyeaters", "appSlug": "meliphagidae", "speciesCount": 190, "notableMembers": ["Tui", "Noisy Miner", "New Holland Honeyeater"]},
    {"id": "FAM_DASYORNITHIDAE", "name": "Dasyornithidae", "rank": "FAMILY", "commonName": "Bristlebirds", "appSlug": "dasyornithidae", "speciesCount": 3, "notableMembers": ["Eastern Bristlebird", "Rufous Bristlebird"]},
    {"id": "FAM_PARDALOTIDAE", "name": "Pardalotidae", "rank": "FAMILY", "commonName": "Pardalotes", "appSlug": "pardalotidae", "speciesCount": 4, "notableMembers": ["Spotted Pardalote", "Striated Pardalote"]},
    {"id": "FAM_ACANTHIZIDAE", "name": "Acanthizidae", "rank": "FAMILY", "commonName": "Australasian warblers", "appSlug": "acanthizidae", "speciesCount": 67, "notableMembers": ["White-browed Scrubwren", "Weebill"]},
    {"id": "FAM_POMATOSTOMIDAE", "name": "Pomatostomidae", "rank": "FAMILY", "commonName": "Australasian babblers", "appSlug": "pomatostomidae", "speciesCount": 5, "notableMembers": ["Grey-crowned Babbler", "White-browed Babbler"]},
    {"id": "FAM_ORTHONYCHIDAE", "name": "Orthonychidae", "rank": "FAMILY", "commonName": "Logrunners", "appSlug": "orthonychidae", "speciesCount": 2, "notableMembers": ["Australian Logrunner", "Chowchilla"]},
    {"id": "FAM_CNEMOPHILIDAE", "name": "Cnemophilidae", "rank": "FAMILY", "commonName": "Satinbirds", "appSlug": "cnemophilidae", "speciesCount": 3, "notableMembers": ["MacGregor's Satinbird", "Yellow-breasted Satinbird"]},
    {"id": "FAM_MELANOCHARITIDAE", "name": "Melanocharitidae", "rank": "FAMILY", "commonName": "Berrypeckers", "appSlug": "melanocharitidae", "speciesCount": 13, "notableMembers": ["Black Berrypecker", "Fan-tailed Berrypecker"]},
    {"id": "FAM_PARAMYTHIIDAE", "name": "Paramythiidae", "rank": "FAMILY", "commonName": "Painted berrypeckers", "appSlug": "paramythiidae", "speciesCount": 2, "notableMembers": ["Eastern Crested Berrypecker"]},
    {"id": "FAM_CALLAEIDAE", "name": "Callaeidae", "rank": "FAMILY", "commonName": "New Zealand wattlebirds", "appSlug": "callaeidae", "speciesCount": 3, "notableMembers": ["Kokako", "North Island Saddleback"]},
    {"id": "FAM_NOTIOMYSTIDAE", "name": "Notiomystidae", "rank": "FAMILY", "commonName": "Stitchbird", "appSlug": "notiomystidae", "speciesCount": 1, "notableMembers": ["Hihi / Stitchbird"]},
    {"id": "FAM_PSOPHODIDAE", "name": "Psophodidae", "rank": "FAMILY", "commonName": "Whipbirds", "appSlug": "psophodidae", "speciesCount": 5, "notableMembers": ["Eastern Whipbird", "Western Whipbird"]},
    {"id": "FAM_CINCLOSOMATIDAE", "name": "Cinclosomatidae", "rank": "FAMILY", "commonName": "Quail-thrushes", "appSlug": "cinclosomatidae", "speciesCount": 12, "notableMembers": ["Spotted Quail-thrush", "Blue Jewel-babbler"]},
    {"id": "FAM_PLATYSTEIRIDAE", "name": "Platysteiridae", "rank": "FAMILY", "commonName": "Wattle-eyes & batises", "appSlug": "platysteiridae", "speciesCount": 32, "notableMembers": ["Common Wattle-eye", "Cape Batis"]},
    {"id": "FAM_MALACONOTIDAE", "name": "Malaconotidae", "rank": "FAMILY", "commonName": "Bushshrikes", "appSlug": "malaconotidae", "speciesCount": 50, "notableMembers": ["Grey-headed Bushshrike", "Crimson-breasted Shrike"]},
    {"id": "FAM_MACHAERIRHYNCHIDAE", "name": "Machaerirhynchidae", "rank": "FAMILY", "commonName": "Boatbills", "appSlug": "machaerirhynchidae", "speciesCount": 2, "notableMembers": ["Yellow-breasted Boatbill"]},
    {"id": "FAM_VANGIDAE", "name": "Vangidae", "rank": "FAMILY", "commonName": "Vangas", "appSlug": "vangidae", "speciesCount": 40, "notableMembers": ["Hook-billed Vanga", "Sickle-billed Vanga"]},
    {"id": "FAM_PITYRIASIDAE", "name": "Pityriasidae", "rank": "FAMILY", "commonName": "Bristlehead", "appSlug": "pityriasidae", "speciesCount": 1, "notableMembers": ["Bornean Bristlehead"]},
    {"id": "FAM_ARTAMIDAE", "name": "Artamidae", "rank": "FAMILY", "commonName": "Woodswallows & butcherbirds", "appSlug": "artamidae", "speciesCount": 24, "notableMembers": ["Australian Magpie", "Pied Butcherbird"]},
    {"id": "FAM_RHAGOLOGIDAE", "name": "Rhagologidae", "rank": "FAMILY", "commonName": "Mottled berryhunter", "appSlug": "rhagologidae", "speciesCount": 1, "notableMembers": ["Mottled Berryhunter"]},
    {"id": "FAM_AEGITHINIDAE", "name": "Aegithinidae", "rank": "FAMILY", "commonName": "Ioras", "appSlug": "aegithinidae", "speciesCount": 4, "notableMembers": ["Common Iora", "Marshall's Iora"]},
    {"id": "FAM_CAMPEPHAGIDAE", "name": "Campephagidae", "rank": "FAMILY", "commonName": "Cuckooshrikes", "appSlug": "campephagidae", "speciesCount": 93, "notableMembers": ["Black-faced Cuckooshrike", "White-winged Triller"]},
    {"id": "FAM_MOHOUIDAE", "name": "Mohouidae", "rank": "FAMILY", "commonName": "Whiteheads", "appSlug": "mohouidae", "speciesCount": 3, "notableMembers": ["Whitehead", "Yellowhead"]},
    {"id": "FAM_NEOSITTIDAE", "name": "Neosittidae", "rank": "FAMILY", "commonName": "Sittellas", "appSlug": "neosittidae", "speciesCount": 3, "notableMembers": ["Varied Sittella", "Black Sittella"]},
    {"id": "FAM_EULACESTOMATIDAE", "name": "Eulacestomatidae", "rank": "FAMILY", "commonName": "Ploughbill", "appSlug": "eulacestomatidae", "speciesCount": 1, "notableMembers": ["Wattled Ploughbill"]},
    {"id": "FAM_OREOICIDAE", "name": "Oreoicidae", "rank": "FAMILY", "commonName": "Australo-Papuan bellbirds", "appSlug": "oreoicidae", "speciesCount": 3, "notableMembers": ["Crested Bellbird", "Crested Pitohui"]},
    {"id": "FAM_FALCUNCULIDAE", "name": "Falcunculidae", "rank": "FAMILY", "commonName": "Shriketit", "appSlug": "falcunculidae", "speciesCount": 1, "notableMembers": ["Northern Shriketit"]},
    {"id": "FAM_PACHYCEPHALIDAE", "name": "Pachycephalidae", "rank": "FAMILY", "commonName": "Whistlers", "appSlug": "pachycephalidae", "speciesCount": 57, "notableMembers": ["Golden Whistler", "Rufous Whistler"]},
    {"id": "FAM_DICRURIDAE", "name": "Dicruridae", "rank": "FAMILY", "commonName": "Drongos", "appSlug": "dicruridae", "speciesCount": 30, "notableMembers": ["Black Drongo", "Greater Racket-tailed Drongo"]},
    {"id": "FAM_RHIPIDURIDAE", "name": "Rhipiduridae", "rank": "FAMILY", "commonName": "Fantails", "appSlug": "rhipiduridae", "speciesCount": 53, "notableMembers": ["Willie Wagtail", "New Zealand Fantail"]},
    {"id": "FAM_MONARCHIDAE", "name": "Monarchidae", "rank": "FAMILY", "commonName": "Monarch flycatchers", "appSlug": "monarchidae", "speciesCount": 115, "notableMembers": ["Black-naped Monarch", "Japanese Paradise Flycatcher", "Magpie-lark"]},
    {"id": "FAM_PLATYLOPHIDAE", "name": "Platylophidae", "rank": "FAMILY", "commonName": "Crested jay", "appSlug": "platylophidae", "speciesCount": 1, "notableMembers": ["Crested Jay"]},
    {"id": "FAM_CORCORACIDAE", "name": "Corcoracidae", "rank": "FAMILY", "commonName": "Australian mudnesters", "appSlug": "corcoracidae", "speciesCount": 2, "notableMembers": ["White-winged Chough", "Apostlebird"]},
    {"id": "FAM_MELAMPITTIDAE", "name": "Melampittidae", "rank": "FAMILY", "commonName": "Melampittas", "appSlug": "melampittidae", "speciesCount": 2, "notableMembers": ["Lesser Melampitta", "Greater Melampitta"]},
    {"id": "FAM_IFRITIDAE", "name": "Ifritidae", "rank": "FAMILY", "commonName": "Ifrita", "appSlug": "ifritidae", "speciesCount": 1, "notableMembers": ["Blue-capped Ifrita"]},
    {"id": "FAM_PETROICIDAE", "name": "Petroicidae", "rank": "FAMILY", "commonName": "Australasian robins", "appSlug": "petroicidae", "speciesCount": 49, "notableMembers": ["Scarlet Robin", "Flame Robin", "Eastern Yellow Robin"]},
    {"id": "FAM_PICATHARTIDAE", "name": "Picathartidae", "rank": "FAMILY", "commonName": "Rockfowl", "appSlug": "picathartidae", "speciesCount": 2, "notableMembers": ["White-necked Rockfowl", "Grey-necked Rockfowl"]},
    {"id": "FAM_CHAETOPIDAE", "name": "Chaetopidae", "rank": "FAMILY", "commonName": "Rockjumpers", "appSlug": "chaetopidae", "speciesCount": 2, "notableMembers": ["Cape Rockjumper", "Drakensberg Rockjumper"]},
    {"id": "FAM_EUPETIDAE", "name": "Eupetidae", "rank": "FAMILY", "commonName": "Rail-babbler", "appSlug": "eupetidae", "speciesCount": 1, "notableMembers": ["Malaysian Rail-babbler"]},
    {"id": "FAM_PTILIOGONATIDAE", "name": "Ptiliogonatidae", "rank": "FAMILY", "commonName": "Silky-flycatchers", "appSlug": "ptiliogonatidae", "speciesCount": 4, "notableMembers": ["Phainopepla", "Grey Silky-flycatcher"]},
    {"id": "FAM_HYPOCOLIIDAE", "name": "Hypocoliidae", "rank": "FAMILY", "commonName": "Hypocolius", "appSlug": "hypocoliidae", "speciesCount": 1, "notableMembers": ["Hypocolius"]},
    {"id": "FAM_DULIDAE", "name": "Dulidae", "rank": "FAMILY", "commonName": "Palmchat", "appSlug": "dulidae", "speciesCount": 1, "notableMembers": ["Palmchat"]},
    {"id": "FAM_MOHOIDAE", "name": "Mohoidae", "rank": "FAMILY", "commonName": "Hawaiian honeyeaters", "appSlug": "mohoidae", "speciesCount": 0, "notableMembers": ["Oahu Oo (extinct)"]},
    {"id": "FAM_HYLOCITREIDAE", "name": "Hylocitreidae", "rank": "FAMILY", "commonName": "Hylocitrea", "appSlug": "hylocitreidae", "speciesCount": 1, "notableMembers": ["Hylocitrea"]},
    {"id": "FAM_STENOSTIRIDAE", "name": "Stenostiridae", "rank": "FAMILY", "commonName": "Fairy flycatchers", "appSlug": "stenostiridae", "speciesCount": 9, "notableMembers": ["African Blue Flycatcher", "Fairy Flycatcher"]},
    {"id": "FAM_NICATORIDAE", "name": "Nicatoridae", "rank": "FAMILY", "commonName": "Nicators", "appSlug": "nicatoridae", "speciesCount": 3, "notableMembers": ["Western Nicator", "Eastern Nicator"]},
    {"id": "FAM_PNOEPYGIDAE", "name": "Pnoepygidae", "rank": "FAMILY", "commonName": "Cupwings", "appSlug": "pnoepygidae", "speciesCount": 5, "notableMembers": ["Scaly-breasted Cupwing", "Pygmy Cupwing"]},
    {"id": "FAM_MACROSPHENIDAE", "name": "Macrosphenidae", "rank": "FAMILY", "commonName": "Crombecs & African warblers", "appSlug": "macrosphenidae", "speciesCount": 18, "notableMembers": ["Red-capped Crombec", "Cape Grassbird"]},
    {"id": "FAM_CETTIIDAE", "name": "Cettiidae", "rank": "FAMILY", "commonName": "Cettia bush warblers", "appSlug": "cettiidae", "speciesCount": 32, "notableMembers": ["Japanese Bush Warbler", "Aberrant Bush Warbler"]},
    {"id": "FAM_SCOTOCERCIDAE", "name": "Scotocercidae", "rank": "FAMILY", "commonName": "Streaked scrub warbler", "appSlug": "scotocercidae", "speciesCount": 1, "notableMembers": ["Streaked Scrub Warbler"]},
    {"id": "FAM_ERYTHROCERCIDAE", "name": "Erythrocercidae", "rank": "FAMILY", "commonName": "Yellow flycatchers", "appSlug": "erythrocercidae", "speciesCount": 3, "notableMembers": ["Chestnut-capped Flycatcher", "Livingstone's Flycatcher"]},
    {"id": "FAM_HYLIIDAE", "name": "Hyliidae", "rank": "FAMILY", "commonName": "Hylias", "appSlug": "hyliidae", "speciesCount": 2, "notableMembers": ["Green Hylia", "Tit Hylia"]},
    {"id": "FAM_DONACOBIIDAE", "name": "Donacobiidae", "rank": "FAMILY", "commonName": "Donacobius", "appSlug": "donacobiidae", "speciesCount": 1, "notableMembers": ["Black-capped Donacobius"]},
    {"id": "FAM_BERNIERIIDAE", "name": "Bernieriidae", "rank": "FAMILY", "commonName": "Madagascan warblers", "appSlug": "bernieriidae", "speciesCount": 11, "notableMembers": ["Long-billed Bernieria", "Spectacled Tetraka"]},
    {"id": "FAM_PARADOXORNITHIDAE", "name": "Paradoxornithidae", "rank": "FAMILY", "commonName": "Parrotbills", "appSlug": "paradoxornithidae", "speciesCount": 37, "notableMembers": ["Vinous-throated Parrotbill", "Reed Parrotbill"]},
    {"id": "FAM_ZOSTEROPIDAE", "name": "Zosteropidae", "rank": "FAMILY", "commonName": "White-eyes", "appSlug": "zosteropidae", "speciesCount": 140, "notableMembers": ["Japanese White-eye", "Silvereye", "Cape White-eye"]},
    {"id": "FAM_TIMALIIDAE", "name": "Timaliidae", "rank": "FAMILY", "commonName": "Babblers", "appSlug": "timaliidae", "speciesCount": 58, "notableMembers": ["Pin-striped Tit-babbler", "Chestnut-capped Babbler"]},
    {"id": "FAM_PELLORNEIDAE", "name": "Pellorneidae", "rank": "FAMILY", "commonName": "Ground babblers", "appSlug": "pellorneidae", "speciesCount": 70, "notableMembers": ["Puff-throated Babbler", "Abbott's Babbler"]},
    {"id": "FAM_ALCIPPEIDAE", "name": "Alcippeidae", "rank": "FAMILY", "commonName": "Fulvettas", "appSlug": "alcippeidae", "speciesCount": 10, "notableMembers": ["Brown-cheeked Fulvetta", "Grey-cheeked Fulvetta"]},
    {"id": "FAM_LEIOTHRICHIDAE", "name": "Leiothrichidae", "rank": "FAMILY", "commonName": "Laughingthrushes", "appSlug": "leiothrichidae", "speciesCount": 135, "notableMembers": ["Greater Necklaced Laughingthrush", "Red-billed Leiothrix", "Silver-eared Mesia"]},
    {"id": "FAM_MODULATRICIDAE", "name": "Modulatricidae", "rank": "FAMILY", "commonName": "Dapple-throat & allies", "appSlug": "modulatricidae", "speciesCount": 3, "notableMembers": ["Dapple-throat", "Spot-throat"]},
    {"id": "FAM_PROMEROPIDAE", "name": "Promeropidae", "rank": "FAMILY", "commonName": "Sugarbirds", "appSlug": "promeropidae", "speciesCount": 2, "notableMembers": ["Cape Sugarbird", "Gurney's Sugarbird"]},
    {"id": "FAM_IRENIDAE", "name": "Irenidae", "rank": "FAMILY", "commonName": "Fairy-bluebirds", "appSlug": "irenidae", "speciesCount": 3, "notableMembers": ["Asian Fairy-bluebird", "Philippine Fairy-bluebird"]},
    {"id": "FAM_ELACHURIDAE", "name": "Elachuridae", "rank": "FAMILY", "commonName": "Elachura", "appSlug": "elachuridae", "speciesCount": 1, "notableMembers": ["Spotted Elachura"]},
    {"id": "FAM_HYLIOTIDAE", "name": "Hyliotidae", "rank": "FAMILY", "commonName": "Hyliotas", "appSlug": "hyliotidae", "speciesCount": 4, "notableMembers": ["Yellow-bellied Hyliota", "Violet-backed Hyliota"]},
    {"id": "FAM_TICHODROMIDAE", "name": "Tichodromidae", "rank": "FAMILY", "commonName": "Wallcreeper", "appSlug": "tichodromidae", "speciesCount": 1, "notableMembers": ["Wallcreeper"]},
    {"id": "FAM_SALPORNITHIDAE", "name": "Salpornithidae", "rank": "FAMILY", "commonName": "Spotted creepers", "appSlug": "salpornithidae", "speciesCount": 2, "notableMembers": ["Indian Spotted Creeper", "African Spotted Creeper"]},
    {"id": "FAM_BUPHAGIDAE", "name": "Buphagidae", "rank": "FAMILY", "commonName": "Oxpeckers", "appSlug": "buphagidae", "speciesCount": 2, "notableMembers": ["Red-billed Oxpecker", "Yellow-billed Oxpecker"]},
    {"id": "FAM_CHLOROPSEIDAE", "name": "Chloropseidae", "rank": "FAMILY", "commonName": "Leafbirds", "appSlug": "chloropseidae", "speciesCount": 13, "notableMembers": ["Golden-fronted Leafbird", "Blue-winged Leafbird"]},
    {"id": "FAM_DICAEIDAE", "name": "Dicaeidae", "rank": "FAMILY", "commonName": "Flowerpeckers", "appSlug": "dicaeidae", "speciesCount": 44, "notableMembers": ["Scarlet-backed Flowerpecker", "Mistletoebird"]},
    {"id": "FAM_PLOCEIDAE", "name": "Ploceidae", "rank": "FAMILY", "commonName": "Weavers", "appSlug": "ploceidae", "speciesCount": 118, "notableMembers": ["Village Weaver", "Baya Weaver", "Red-billed Quelea"]},
    {"id": "FAM_VIDUIDAE", "name": "Viduidae", "rank": "FAMILY", "commonName": "Indigobirds & whydahs", "appSlug": "viduidae", "speciesCount": 20, "notableMembers": ["Pin-tailed Whydah", "Long-tailed Paradise Whydah"]},
    {"id": "FAM_PEUCEDRAMIDAE", "name": "Peucedramidae", "rank": "FAMILY", "commonName": "Olive warbler", "appSlug": "peucedramidae", "speciesCount": 1, "notableMembers": ["Olive Warbler"]},
    {"id": "FAM_UROCYNCHRAMIDAE", "name": "Urocynchramidae", "rank": "FAMILY", "commonName": "Przevalski's finch", "appSlug": "urocynchramidae", "speciesCount": 1, "notableMembers": ["Przevalski's Pinktail"]},
    {"id": "FAM_CALCARIIDAE", "name": "Calcariidae", "rank": "FAMILY", "commonName": "Longspurs & snow buntings", "appSlug": "calcariidae", "speciesCount": 6, "notableMembers": ["Snow Bunting", "Lapland Longspur"]},
    {"id": "FAM_RHODINOCICHLIDAE", "name": "Rhodinocichlidae", "rank": "FAMILY", "commonName": "Thrush-tanager", "appSlug": "rhodinocichlidae", "speciesCount": 1, "notableMembers": ["Rosy Thrush-tanager"]},
    {"id": "FAM_PASSERELLIDAE", "name": "Passerellidae", "rank": "FAMILY", "commonName": "New World sparrows", "appSlug": "passerellidae", "speciesCount": 140, "notableMembers": ["White-crowned Sparrow", "Song Sparrow", "Dark-eyed Junco"]},
    {"id": "FAM_CALYPTOPHILIDAE", "name": "Calyptophilidae", "rank": "FAMILY", "commonName": "Chat-tanagers", "appSlug": "calyptophilidae", "speciesCount": 2, "notableMembers": ["Eastern Chat-tanager", "Western Chat-tanager"]},
    {"id": "FAM_PHAENICOPHILIDAE", "name": "Phaenicophilidae", "rank": "FAMILY", "commonName": "Hispaniolan tanagers", "appSlug": "phaenicophilidae", "speciesCount": 4, "notableMembers": ["Black-crowned Palm Tanager", "White-winged Warbler"]},
    {"id": "FAM_NESOSPINGIDAE", "name": "Nesospingidae", "rank": "FAMILY", "commonName": "Puerto Rican tanager", "appSlug": "nesospingidae", "speciesCount": 1, "notableMembers": ["Puerto Rican Tanager"]},
    {"id": "FAM_SPINDALIDAE", "name": "Spindalidae", "rank": "FAMILY", "commonName": "Spindalises", "appSlug": "spindalidae", "speciesCount": 4, "notableMembers": ["Western Spindalis", "Jamaican Spindalis"]},
    {"id": "FAM_ZELEDONIIDAE", "name": "Zeledoniidae", "rank": "FAMILY", "commonName": "Wrenthrush", "appSlug": "zeledoniidae", "speciesCount": 1, "notableMembers": ["Wrenthrush"]},
    {"id": "FAM_TERETISTRIDAE", "name": "Teretistridae", "rank": "FAMILY", "commonName": "Cuban warblers", "appSlug": "teretistridae", "speciesCount": 2, "notableMembers": ["Yellow-headed Warbler", "Oriente Warbler"]},
    {"id": "FAM_ICTERIIDAE", "name": "Icteriidae", "rank": "FAMILY", "commonName": "Yellow-breasted chat", "appSlug": "icteriidae", "speciesCount": 1, "notableMembers": ["Yellow-breasted Chat"]},
    {"id": "FAM_MITROSPINGIDAE", "name": "Mitrospingidae", "rank": "FAMILY", "commonName": "Mitrospingid tanagers", "appSlug": "mitrospingidae", "speciesCount": 4, "notableMembers": ["Dusky-faced Tanager", "Red-billed Pied Tanager"]},
]

# Find AVES children and separate existing orders from REPTILIA
aves_children = aves["children"]
existing_count = len(aves_children)

# Find the index of REPTILIA (or the last AVES order)
# The last items are the orders. We need to insert new orders before REPTILIA.
# Actually looking at the data structure, REPTILIA is a sibling of AVES, not a child.
# AVES children are all ORDERS. The last order is PTEROCLIFORMES.

# Let me just append new orders to AVES children
for new_order in new_orders:
    aves["children"].append(new_order)

# Now add families to existing orders
def find_order(order_id):
    for child in aves["children"]:
        if child["id"] == order_id:
            return child
    return None

for order_id, families in families_by_order.items():
    order = find_order(order_id)
    if order:
        for family in families:
            order["children"].append(family)
    else:
        print(f"Order {order_id} not found!")

# Add passeriformes families to PASSERIFORMES
passeriformes_order = find_order("PASSERIFORMES")
for family in passeriformes_families:
    passeriformes_order["children"].append(family)

# Write back
with open(TAXONOMY_PATH, 'w') as f:
    json.dump(taxonomy, f, indent=2, ensure_ascii=False)

print(f"Added {len(new_orders)} new orders")
total_families_added = sum(len(v) for v in families_by_order.values()) + len(passeriformes_families)
print(f"Added {total_families_added} families to existing orders")
print(f"AVES now has {len(aves['children'])} orders")
