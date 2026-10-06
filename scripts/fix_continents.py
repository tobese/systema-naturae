#!/usr/bin/env python3
"""
Fix UNKNOWN_CONTINENT: Replace abbreviated continent codes with full names.
"""
import json
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import family_data_files  # noqa: E402

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
    # Ocean basins and multi-continent regions are not continents, but the GBIF
    # continent fill wrote them as if they were. They expand to the continents the
    # region actually borders rather than being dropped, so the range information
    # survives -- "Pacific" is real evidence, just not in continent form.
    "Worldwide": ["Europe", "Asia", "Africa", "North America", "South America",
                  "Australia", "Oceania", "Antarctica"],
    "Atlantic": ["North America", "South America", "Europe", "Africa"],
    "Pacific": ["Asia", "Australia", "North America", "South America"],
    "Indian": ["Asia", "Africa", "Australia"],
    "Indo-Pacific": ["Asia", "Africa", "Australia"],
    "Mediterranean": ["Europe", "Africa"],
    "Southeast Asia": ["Asia"],
}

VALID_CONTINENTS = {
    "Europe", "Asia", "Africa", "North America",
    "South America", "Australia", "Oceania", "Antarctica"
}

def find_data_files():
    """Find all family data JSON files."""
    return family_data_files()

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
                        mapped = CONTINENT_MAP[cont]
                        # A region may expand to several continents, and the node
                        # may already list some of them -- so union, don't append,
                        # or a species found in both the Pacific and Asia ends up
                        # with Asia twice.
                        new_continents.extend(mapped if isinstance(mapped, list) else [mapped])
                        fixed += 1
                    elif cont in VALID_CONTINENTS:
                        new_continents.append(cont)
                    else:
                        # Keep unknown but log
                        print(f"  WARNING: Unknown continent '{cont}' in {node.get('name', 'unknown')}")
                        new_continents.append(cont)
                # Preserve order but drop duplicates introduced by the expansion.
                node["continents"] = list(dict.fromkeys(new_continents))
        
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
            
            if data.get("rank") != "FAMILY":
                continue
            
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