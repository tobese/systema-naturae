#!/usr/bin/env python3
"""
Fix MISSING_LINEAGE: Infer lineage from parent genus.
"""
import json
import glob

def find_data_files():
    files = glob.glob("**/src/data/*.json", recursive=True)
    excluded = ['unified-taxonomy', 'node_modules', 'portal/data', 'shared/data']
    return [f for f in files if not any(e in f for e in excluded)]

def fix_lineage(node, current_lineage=None):
    """Recursively fix missing lineage by inferring from parent genus."""
    fixed = 0
    if isinstance(node, dict):
        current_rank = node.get("rank")
        current_name = node.get("name")
        
        if current_rank == "GENUS":
            current_lineage = current_name
        elif current_rank == "SPECIES":
            if not node.get("lineage") and current_lineage:
                node["lineage"] = current_lineage
                fixed += 1
        
        for child in node.get("children", []):
            fixed += fix_lineage(child, current_lineage)
    return fixed

def main():
    data_files = glob.glob("**/src/data/*.json", recursive=True)
    excluded = ['unified-taxonomy', 'node_modules', 'portal/data', 'shared/data']
    data_files = [f for f in data_files if not any(e in f for e in excluded)]
    
    print(f"Found {len(data_files)} family data files")
    
    total_fixed = 0
    for path in sorted(data_files):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if data.get("rank") != "FAMILY":
                continue
            
            fixed = fix_lineage(data)
            
            if fixed > 0:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"  Fixed {fixed} lineages in {path}")
                total_fixed += fixed
        except Exception as e:
            print(f"  ERROR in {path}: {e}")
    
    print(f"\nTotal lineages fixed: {total_fixed}")
    return total_fixed

if __name__ == "__main__":
    main()