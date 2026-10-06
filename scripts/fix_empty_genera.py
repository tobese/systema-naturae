#!/usr/bin/env python3
"""
Fix EMPTY_GENUS: Remove genus nodes with no children.
"""
import json
import glob

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from tree import family_data_files  # noqa: E402

def find_data_files():
    return family_data_files()

def remove_empty_genera(node):
    """Remove genus nodes with no children."""
    removed = 0
    if isinstance(node, dict) and "children" in node:
        new_children = []
        for child in node.get("children", []):
            if child.get("rank") == "GENUS" and not child.get("children"):
                print(f"  Removing empty genus: {child.get('name', 'unknown')}")
                removed += 1
                continue
            new_children.append(child)
            removed += remove_empty_genera(child)
        node["children"] = new_children
    return removed

def main():
    data_files = family_data_files()
    
    print(f"Found {len(data_files)} family data files")
    
    total_removed = 0
    for path in sorted(data_files):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if data.get("rank") != "FAMILY":
                continue
            
            removed = 0
            def process(node):
                nonlocal removed
                if isinstance(node, dict) and "children" in node:
                    new_children = []
                    for child in node.get("children", []):
                        if child.get("rank") == "GENUS" and not child.get("children"):
                            print(f"  Removing empty genus: {child.get('name', 'unknown')}")
                            removed += 1
                            continue
                        new_children.append(child)
                        process(child)
                    node["children"] = new_children
            
            process(data)
            
            if removed > 0:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"  Removed {removed} empty genera in {path}")
                total_removed += removed
        except Exception as e:
            print(f"  ERROR in {path}: {e}")
    
    print(f"\nTotal empty genera removed: {total_removed}")
    return total_removed

if __name__ == "__main__":
    main()