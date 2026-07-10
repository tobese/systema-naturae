#!/usr/bin/env python3
"""Import the 205 Insecta scaffold families (no appSlug) from the old GBIF cache.

For each no-appSlug FAMILY under Insecta:
  - build a genus->species tree from gbif-cache-insecta-old.json.gz
  - write <class>/<order>/<slug>/src/data/<slug>.json
  - set appSlug on the family node in taxonomy.json
  - emit a ColorTheme + COLOR_REGISTRY entry into colorRegistry.ts
Species are kept minimal (no description) so buildData compresses them into speciesList.
"""
import json, gzip, colorsys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAX = ROOT/"portal"/"data"/"taxonomy.json"
CACHE = ROOT/"portal"/"data"/"gbif-cache-insecta-old.json.gz"
COLORS = ROOT/"portal"/"src"/"colorRegistry.ts"

def sp_id(name):
    return "SP_" + re.sub(r'[^a-zA-Z0-9]', '_', name).upper().strip('_')
def canon(sp):
    n = sp.get("canonicalName") or sp.get("species") or ""
    if not n:
        raw = sp.get("scientificName") or ""
        n = re.sub(r'\([^)]*\)', '', raw).strip()
    return n.strip()

tax = json.loads(TAX.read_text())
cache = json.load(gzip.open(CACHE, "rt"))
sbf = cache["speciesByFamily"]

# find Insecta no-appSlug families with their order
targets = []  # (family_node, order_name)
def walk(n, cls=None, order=None):
    r = n.get("rank")
    if r == "CLASS": cls = n.get("name")
    if r == "ORDER": order = n.get("name")
    if r == "FAMILY":
        if cls == "Insecta" and not n.get("appSlug"):
            targets.append((n, order))
        return
    for c in n.get("children", []): walk(c, cls, order)
walk(tax)
print(f"Insecta scaffold families (no appSlug): {len(targets)}")

def hexcol(i, total, light):
    h = (i * 137.508 % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(h, light, 0.55)
    return "#%02X%02X%02X" % (int(r*255), int(g*255), int(b*255))

theme_consts = []
registry_lines = []
written = 0
total_species = 0
skipped_no_cache = []

for i, (fam, order) in enumerate(sorted(targets, key=lambda x: x[0]["name"])):
    name = fam["name"]
    slug = name.lower()
    order = order or "Unknown"
    entry = sbf.get(name)
    if not entry:
        skipped_no_cache.append(name); continue
    # group by genus
    genera = {}
    for sp in entry["species"]:
        cn = canon(sp)
        if not cn or " " not in cn: continue
        g = sp.get("genus") or cn.split(" ")[0]
        genera.setdefault(g, {})
        genera[g][cn] = sp  # dedupe by canonical name
    children = []
    fam_species = 0
    for g in sorted(genera):
        sps = []
        for cn in sorted(genera[g]):
            sp = genera[g][cn]
            node = {"id": sp_id(cn), "name": cn, "rank": "SPECIES",
                    "lineage": g, "subspeciesCount": 0, "sourcedFrom": "gbif"}
            if sp.get("extinct"): node["extinct"] = True
            sps.append(node)
        if not sps: continue
        children.append({"id": f"GENUS_{re.sub(r'[^a-zA-Z0-9]','_',g).upper()}",
                         "name": g, "rank": "GENUS", "lineage": g,
                         "description": f"{g} — a genus in the family {name}.",
                         "children": sps})
        fam_species += len(sps)
    data = {"id": f"FAM_{re.sub(r'[^a-zA-Z0-9]','_',name).upper()}",
            "name": name, "rank": "FAMILY", "commonName": name,
            "description": f"{name} — a family in the order {order}.",
            "sourcedFrom": "gbif", "children": children}
    outdir = ROOT/"insecta"/order.lower()/slug/"src"/"data"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/f"{slug}.json").write_text(json.dumps(data, indent=2) + "\n")
    fam["appSlug"] = slug
    written += 1
    total_species += fam_species
    main = hexcol(i, len(targets), 0.55)
    hyb = hexcol(i, len(targets), 0.70)
    const = f"insecta_{slug}"
    theme_consts.append(
        f'const {const}: ColorTheme = {{ subfamilyColors: {{}}, breedGroupColor: "{main}", '
        f'hybridColor: "{hyb}", appSlug: "{slug}", className: "Insecta", orderName: "{order}", '
        f'name: "{name}", mainColor: "{main}", lineageColors: {{ "{name}": "{hyb}" }} }};')
    registry_lines.append(f"  {slug}: {const},")

print(f"Wrote {written} family data files, {total_species:,} species")
if skipped_no_cache:
    print(f"NO CACHE DATA ({len(skipped_no_cache)}): {skipped_no_cache}")

TAX.write_text(json.dumps(tax, indent=2) + "\n")
print("Updated taxonomy.json with appSlugs")

# splice into colorRegistry.ts
txt = COLORS.read_text()
marker = "export const COLOR_REGISTRY: Record<string, ColorTheme> = {"
idx = txt.index(marker)
consts_block = "\n".join(theme_consts) + "\n\n"
txt = txt[:idx] + consts_block + txt[idx:]
# now insert registry entries right after the marker's line
idx2 = txt.index(marker) + len(marker)
nl = txt.index("\n", idx2)
txt = txt[:nl+1] + "\n".join(registry_lines) + "\n" + txt[nl+1:]
COLORS.write_text(txt)
print(f"Inserted {len(theme_consts)} themes + registry entries into colorRegistry.ts")
