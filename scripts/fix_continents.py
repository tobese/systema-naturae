#!/usr/bin/env python3
"""
Fix UNKNOWN_CONTINENT: Replace abbreviated continent codes with full names.
"""
import json
import os
import glob

CONTINENT_MAP = {
    "EU": "Europe",
    "AS": "Asia",
    "NA": "North America",
    "SA": "South America",
    "AF": "Africa",
    "AU": "Australia",
    "OC": "Oceania",
    "AN": "Antarctica",
    "CENTRAL AMERICA": "North America",
    "Central America": "North America",
}

VALID_CONTINENTS = {
    "Europe", "Asia", "Africa", "North America",
    "South America", "Australia", "Oceania", "Antarctica"
}

def find_data_files():
    """Find all family data JSON files."""
    files = glob.glob("**/src/data/*.json", recursive=True)
    # Exclude generated and system files
    excluded = ['unified-taxonomy', 'node_modules', 'portal/data', 'shared/data']
    return [f for f in files if not any(e in f for e in excluded)]

def fix_continents_in_node(node):
    """Recursively fix continent codes in a node."""
    fixed = 0
    if isinstance(node, dict):
        if node.get("rank") == "SPECIES" and "continents" in node:
            continents = node.get("continents", [])
            if isinstance(continents, list):
                new_continents = []
                for cont in continents:
                    if cont in CONTINENT_MAP:
                        new_continents.append(CONTINENT_MAP[cont])
                        fixed += 1
                    elif cont in VALID_CONTINENTS:
                        new_continents.append(cont)
                    else:
                        # Keep unknown but log
                        print(f"  WARNING: Unknown continent '{cont}' in {node.get('name', 'unknown')}")
                        new_continents.append(cont)
                node["continents"] = new_continents
        
        for child in node.get("children", []):
            fixed += fix_continents_in_node(child)
    return fixed

def main():
    data_files = find_data_files()
    print(f"Found {len(data_files)} family data files")
    
    total_fixed = 0
    for path in sorted(data_files):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            fixed = fix_continents_in_node(data)
            if fixed > 0:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"  Fixed {fixed} continents in {path}")
                total_fixed += fixed
        except Exception as e:
            print(f"  ERROR in {path}: {e}")
    
    print(f"\nTotal continent codes fixed: {total_fixed}")
    return total_fixed

if __name__ == "__main__":
    main()