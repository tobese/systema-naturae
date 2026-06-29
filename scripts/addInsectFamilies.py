"""Add remaining Insecta families to taxonomy.json as count-only entries.
Reads from the old GBIF cache and adds families not already present.
"""
import json
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAX_PATH = ROOT / "portal" / "data" / "taxonomy.json"
CACHE_PATH = ROOT / "portal" / "data" / "gbif-cache-insecta-old.json.gz"

# Families already imported (have appSlug, full data files)
ALREADY_IMPORTED = {"carabidae", "chrysomelidae", "apidae", "formicidae", "vespidae", "papilionidae", "nymphalidae", "libellulidae"}

# Load cache
with gzip.open(CACHE_PATH, "rt") as f:
    cache = json.load(f)

# Group by order
orders: dict[str, dict[str, int]] = {}
for fam_name, fam_data in cache["speciesByFamily"].items():
    spp = fam_data.get("species", [])
    order = ""
    for s in spp:
        if s.get("order"):
            order = s["order"]
            break
    if not order:
        order = "Unknown"
    orders.setdefault(order, {})[fam_name] = len(spp)

print(f"Found {len(orders)} orders with {sum(len(v) for v in orders.values())} families")

# Load taxonomy
with open(TAX_PATH) as f:
    tax = json.load(f)

def find_insecta(node):
    if isinstance(node, dict):
        if node.get("rank") == "CLASS" and node.get("name") == "Insecta":
            return node
        if "children" in node:
            for c in node["children"]:
                r = find_insecta(c)
                if r:
                    return r
    return None

insecta = find_insecta(tax)
assert insecta, "Insecta class not found in taxonomy.json"

# Build set of existing family names (lowercased)
existing_families = set()
existing_orders = set()
for order in insecta.get("children", []):
    existing_orders.add(order["name"].lower())
    for fam in order.get("children", []):
        if fam.get("rank") == "FAMILY":
            existing_families.add(fam["name"].lower())

print(f"Existing orders: {sorted(existing_orders)}")
print(f"Existing families ({len(existing_families)}): {sorted(existing_families)[:10]}...")

# Orders the old cache has that are NOT in taxonomy yet (skip Hymenoptera, it's different)
CACHE_ORDERS_TO_ADD = {
    "Coleoptera", "Psocodea", "Embioptera", "Mecoptera",
}
# These orders exist with FAMILIES in taxonomy already
EXISTING_TAX_ORDERS = {
    "coleoptera", "hymenoptera", "lepidoptera", "odonata",
}

def make_family_id(name):
    base = name.upper().replace(" ", "_").replace("-", "_").replace("'", "")
    return f"FAM_{base}"

def make_order_id(name):
    return name.upper().replace(" ", "_").replace("-", "_")

added = 0
created_orders = []

for order_name, families in orders.items():
    if order_name not in CACHE_ORDERS_TO_ADD:
        continue
    if order_name.lower() in EXISTING_TAX_ORDERS:
        # Find existing order node
        order_node = None
        for child in insecta["children"]:
            if child.get("rank") == "ORDER" and child["name"].lower() == order_name.lower():
                order_node = child
                break
        if not order_node:
            print(f"  Order {order_name} not found in taxonomy, skipping")
            continue
    else:
        # Create new order node
        order_node = {
            "id": make_order_id(order_name),
            "name": order_name,
            "rank": "ORDER",
            "children": [],
        }
        insecta["children"].append(order_node)
        # Sort children by name
        insecta["children"].sort(key=lambda x: x["name"])
        created_orders.append(order_name)
        print(f"  Created new order: {order_name}")

    for fam_name, spp_count in sorted(families.items()):
        slug = fam_name.lower().replace(" ", "_").replace("-", "_")
        if slug in ALREADY_IMPORTED:
            continue
        if fam_name.lower() in existing_families:
            continue
        fam_node = {
            "id": make_family_id(fam_name),
            "name": fam_name,
            "rank": "FAMILY",
            "speciesCount": spp_count,
        }
        order_node["children"].append(fam_node)
        existing_families.add(fam_name.lower())
        added += 1

if created_orders:
    print(f"\nCreated {len(created_orders)} new orders: {created_orders}")

print(f"\nAdded {added} new families to taxonomy.json")

# Save
with open(TAX_PATH, "w") as f:
    json.dump(tax, f, indent=2)
    f.write("\n")

print(f"Saved to {TAX_PATH}")
