#!/usr/bin/env python3
"""
Fix DUPLICATE_SPECIES: Remove duplicate species entries, keep first occurrence.

⚠ DO NOT RUN ON THE CURRENT TREE. KEEP-FIRST IS THE WRONG POLICY HERE.
--------------------------------------------------------------------------
Measured 2026-09-30 against the real data: this would delete 27 real species.

The duplicates it targets are duplicate GENERUS nodes - the same genus listed
twice in a family, each copy holding a different subset of its species. Ploceus
alone appears twice with 57 and 60 species and no overlap in the smaller copy,
and the 19 species unique to it exist only in the copy this script would discard.
Vangidae's Tylas, Erinaceidae's four genera and Galbula account for the rest.

"Keep first occurrence" assumes the copies are identical. 14 of the 20 are not.

Use scripts/merge_duplicate_genera.py instead, which unions by species id. That
has been applied, so the duplicate genera this script was written for no longer
exist - but if they come back, merge them, do not delete them.
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