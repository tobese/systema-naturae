#!/usr/bin/env python3
"""
Fix DUPLICATE_SPECIES: Remove duplicate species entries, keep first occurrence.
"""
import json
import glob

def find_data_files():
    files = glob.glob("**/src/data/*.json", recursive=True)
    excluded = ['unified-taxonomy', 'node_modules', 'portal/data', 'shared/data']
    return [f for f in files if not any(e in f for e in excluded)]

def remove_duplicates(node):
    """Remove duplicate species within a node's children."""
    removed = 0
    if isinstance(node, dict) and "children" in node:
        seen = set()
        new_children = []
        for child in node.get("children", []):
            if child.get("rank") == "SPECIES":
                name = child.get("name")
                if name in seen:
                    print(f"  Removing duplicate: {name}")
                    removed += 1
                    continue
                seen.add(name)
            new_children.append(child)
        node["children"] = new_children
        
        for child in node["children"]:
            removed += remove_duplicates(child)
    return removed

def main():
    data_files = glob.glob("**/src/data/*.json", recursive=True)
    excluded = ['unified-taxonomy', 'node_modules', 'portal/data', 'shared/data']
    data_files = [f for f in data_files if not any(e in f for e in excluded)]
    
    print(f"Found {len(data_files)} family data files")
    
    total_removed = 0
    for path in sorted(data_files):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if data.get("rank") != "FAMILY":
                continue
            
            removed = remove_duplicates(data)
            if removed > 0:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"  Removed {removed} duplicates in {path}")
                total_removed += removed
        except Exception as e:
            print(f"  ERROR in {path}: {e}")
    
    print(f"\nTotal duplicates removed: {total_removed}")
    return total_removed

if __name__ == "__main__":
    main()