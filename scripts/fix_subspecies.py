#!/usr/bin/env python3
"""
Fix MISSING_SUBSPECIES_COUNT: Add subspeciesCount field defaulting to 0.
"""
import json
import glob

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from tree import family_data_files  # noqa: E402

def find_data_files():
    return family_data_files()

def add_subspecies_count(node):
    """Recursively add subspeciesCount to species nodes."""
    added = 0
    if isinstance(node, dict):
        if node.get("rank") == "SPECIES" and "subspeciesCount" not in node:
            node["subspeciesCount"] = 0
            added += 1
        for child in node.get("children", []):
            added += add_subspecies_count(child)
    return added

def main():
    data_files = family_data_files()
    
    print(f"Found {len(data_files)} family data files")
    
    total_added = 0
    for path in sorted(data_files):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if data.get("rank") != "FAMILY":
                continue
            
            added = 0
            def process(node):
                nonlocal added
                if isinstance(node, dict):
                    if node.get("rank") == "SPECIES" and "subspeciesCount" not in node:
                        node["subspeciesCount"] = 0
                        added += 1
                    for child in node.get("children", []):
                        process(child)
            
            process(data)
            
            if added > 0:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"  Added subspeciesCount to {added} species in {path}")
                total_added += added
        except Exception as e:
            print(f"  ERROR in {path}: {e}")
    
    print(f"\nTotal subspeciesCount fields added: {total_added}")
    return total_added

if __name__ == "__main__":
    main()