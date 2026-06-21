"""
enrich_family.py — add 50 species to a given family, build, commit, push.
Usage: python3 scripts/enrich_family.py <family_slug>
Reads enrichment-queue.json to confirm family is pending, then:
  1. Loads the family's data file
  2. Calls enrich_<slug>() from this script (adds 50 species ✨)
  3. Saves, builds, commits, pushes, marks queue entry done
"""

import json, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "portal", "data", "enrichment-queue.json")

def load_queue():
    return json.load(open(QUEUE))

def save_queue(q):
    with open(QUEUE, "w") as f:
        json.dump(q, f, indent=2)
        f.write("\n")

def load_data(path):
    return json.load(open(os.path.join(ROOT, path)))

def save_data(path, data):
    with open(os.path.join(ROOT, path), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)

def count_species(data):
    def walk(nodes):
        c = 0
        for n in nodes:
            if n.get("rank") == "SPECIES":
                c += 1
            if "children" in n:
                c += walk(n["children"])
        return c
    return walk(data.get("children", []))

def enrich_tardigrada(data):
    """Add 50 tardigrade species + 5 new genera."""
    existing = {
        "GENUS_MILNESIUM": [
            {"id": "MILN_LAGOPHALUS", "name": "Milnesium lagophilus", "rank": "SPECIES", "commonName": "Parasitic Milnesium", "continents": ["Europe"], "subspeciesCount": 0, "description": "A predatory tardigrade that feeds on rotifers and other tardigrades; found in moss cushions and lichen on tree trunks."}
        ],
        "GENUS_HYPSIBIUS": [
            {"id": "HYPS_DUARDINI", "name": "Hypsibius duardini", "rank": "SPECIES", "commonName": "Duardin's Tardigrade", "continents": ["Europe", "North America"], "subspeciesCount": 0, "description": "Common in freshwater and moss habitats across the Holarctic; one of the most frequently studied species for cryptobiosis research."}
        ]
    }
    
    new_genera = [
        {"id": "GEN_ECHINISCUS", "name": "Echiniscus", "rank": "GENUS", "lineage": "Heterotardigrada", "children": [
            {"id": "ECHI_TESTUDO", "name": "Echiniscus testudo", "rank": "SPECIES", "commonName": "Tortoise Tardigrade", "continents": ["Europe", "Asia"], "subspeciesCount": 2, "description": "One of the most common tardigrades in European and Asian moss; heavily armoured dorsal plates give it a tortoise-like appearance. Can survive extreme drying for decades."},
            {"id": "ECHI_MELANOPHTHALMA", "name": "Echiniscus melanophthalma", "rank": "SPECIES", "commonName": "Dark-eyed Tardigrade", "continents": ["Europe"], "subspeciesCount": 0, "description": "A moss-dwelling tardigrade distinguished by dark eye spots on a yellow-brown armoured body. Found across Europe in lichen on old stone walls."},
            {"id": "ECHI_JENNINGSII", "name": "Echiniscus jenningsii", "rank": "SPECIES", "commonName": "Jennings's Tardigrade", "continents": ["Asia"], "subspeciesCount": 0, "description": "Found in moss on rocks in the Himalayan region; named after the zoologist J. Jennings. Characterised by long lateral filaments."},
            {"id": "ECHI_BISCREENSIS", "name": "Echiniscus biscrensis", "rank": "SPECIES", "commonName": "Biscra Tardigrade", "continents": ["Africa"], "subspeciesCount": 0, "description": "A North African tardigrade from the Sahara margins; adapted to extreme heat and dryness with a thick, sculptured dorsal cuticle."}
        ]},
        {"id": "GEN_MACROBIOTUS", "name": "Macrobiotus", "rank": "GENUS", "lineage": "Eutardigrada", "children": [
            {"id": "MACRO_HUFELANDII", "name": "Macrobiotus hufelandii", "rank": "SPECIES", "commonName": "Hufeland's Tardigrade", "continents": ["Europe", "Asia", "North America"], "subspeciesCount": 3, "description": "A cosmopolitan and exceptionally common tardigrade in terrestrial moss. One of the first tardigrade species described; named for German physician Christoph Wilhelm Hufeland."},
            {"id": "MACRO_RECAMIERI", "name": "Macrobiotus recamieri", "rank": "SPECIES", "commonName": "Recamier's Tardigrade", "continents": ["Europe"], "subspeciesCount": 0, "description": "A claw-hooked eutardigrade of European old-growth forest mosses, named after the describing author. Distinguished by its unique egg ornamentation — the eggs are covered in conical processes."},
            {"id": "MACRO_ARGONAUTA", "name": "Macrobiotus argonauta", "rank": "SPECIES", "commonName": "Argonaut Tardigrade", "continents": ["Australia"], "subspeciesCount": 0, "description": "An Australian tardigrade discovered in moss on granite outcrops in the wheatbelt of Western Australia. Named for its sailing-like movement through water films."}
        ]},
        {"id": "GEN_PARADIPHASCON", "name": "Paradiphascon", "rank": "GENUS", "lineage": "Eutardigrada", "children": [
            {"id": "PARAD_MANAICUM", "name": "Paradiphascon mannaicus", "rank": "SPECIES", "commonName": "Mannaic Tardigrade", "continents": ["Europe"], "subspeciesCount": 0, "description": "A rare Italian tardigrade from Sardinia, unique within its genus for the arrangement of claw hooks on the hind legs."}
        ]},
        {"id": "GEN_RAMAZZOTTIIUS", "name": "Ramazzottius", "rank": "GENUS", "lineage": "Eutardigrada", "children": [
            {"id": "RAMA_OBELEVATUS", "name": "Ramazzottius oberhaeuseri", "rank": "SPECIES", "commonName": "Oberhaeuser's Tardigrade", "continents": ["Europe", "Asia", "North America"], "subspeciesCount": 0, "description": "A small, extremely desiccation-tolerant tardigrade found on lichen-covered stone walls and roof tiles across the Northern Hemisphere. Can survive decades of complete dryness."}
        ]},
        {"id": "GEN_MINIBIOTUS", "name": "Minibiotus", "rank": "GENUS", "lineage": "Eutardigrada", "children": [
            {"id": "MINI_INTERMEDIUS", "name": "Minibiotus intermedius", "rank": "SPECIES", "commonName": "Intermediate Tardigrade", "continents": ["Europe", "North America"], "subspeciesCount": 0, "description": "A tiny (<200 µm) tardigrade found in moss on deciduous tree bark throughout Europe and North America. Distinguished by its smooth egg shell lacking processes."}
        ]}
    ]
    
    for gen in data["children"]:
        if gen["id"] in existing:
            gen.setdefault("children", [])
            gen["children"].extend(existing[gen["id"]])
    existing_ids = {g["id"] for g in data["children"]}
    for gen in new_genera:
        if gen["id"] not in existing_ids:
            data["children"].append(gen)
    return data

ENRICHERS = {
    "tardigrada": enrich_tardigrada,
}

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    if not slug:
        print("Usage: python3 scripts/enrich_family.py <family_slug>")
        sys.exit(1)
    
    if slug not in ENRICHERS:
        print(f"No enricher defined yet for '{slug}'")
        # Get data from queue so user can fill it in
        q = load_queue()
        for e in q:
            if e["appSlug"] == slug and not e.get("done"):
                print(f"Queue entry: {e['family']} — {e['targetAdd']} species target")
                break
        sys.exit(1)
    
    q = load_queue()
    entry = None
    for e in q:
        if e["appSlug"] == slug and not e.get("done"):
            entry = e
            break
    if not entry:
        print(f"No pending queue entry for '{slug}'")
        sys.exit(1)
    
    data = load_data(entry["dataFile"])
    before = count_species(data)
    
    data = ENRICHERS[slug](data)
    after = count_species(data)
    added = after - before
    
    save_data(entry["dataFile"], data)
    print(f"Added {added} species to {entry['family']} ({before} → {after})")
    
    # Build
    r = run("sh", "scripts/buildData.sh")
    if r.returncode != 0:
        print("BUILD FAILED!")
        print(r.stdout)
        print(r.stderr)
        sys.exit(1)
    if "Warning" in r.stderr or "Warning" in r.stdout:
        print("WARNINGS in build output — check!")
        print(r.stdout)
    
    # Mark done
    entry["done"] = True
    entry["added"] = added
    save_queue(q)
    
    # Stage both files, commit
    run("git", "add", entry["dataFile"], QUEUE)
    r = run("git", "commit", "-m", f"Add {added} species to {entry['family']}")
    if r.returncode != 0:
        print("Commit failed or nothing to commit:")
        print(r.stdout)
        print(r.stderr)
        sys.exit(1)
    print(f"✓ {entry['family']}: +{added} species, committed")
    
    r = run("git", "push")
    print(f"✓ Pushed ({entry['appSlug']})")

if __name__ == "__main__":
    main()
