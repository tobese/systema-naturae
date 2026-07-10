#!/usr/bin/env python3
"""Round 7: bidirectional cross-kingdom audit — concise summary."""
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def load_taxonomy(k):
    p = REPO / "portal" / "data" / ("taxonomy.json" if k == "animalia" else "taxonomy-plantae-snippet.json")
    return json.loads(p.read_text()) if p.exists() else None

def load_colors(k):
    p = REPO / "portal" / "src" / ("colorRegistry.ts" if k == "animalia" else "colorRegistryPlantae.ts")
    return p.read_text() if p.exists() else ""

def extract_color_slugs(text):
    """Extract family appSlug keys from COLOR_REGISTRY map section."""
    slugs = set()
    # Find the COLOR_REGISTRY section
    m = re.search(r'export const COLOR_REGISTRY.*?= \{', text)
    if not m:
        return slugs
    start = m.end()
    # Find closing }
    depth = 1
    pos = start
    while depth > 0 and pos < len(text):
        if text[pos] == '{': depth += 1
        elif text[pos] == '}': depth -= 1
        pos += 1
    registry_section = text[start:pos-1]
    for m2 in re.finditer(r'["\']?(\w+)["\']?\s*:', registry_section):
        slugs.add(m2.group(1))
    return slugs

def walk_families(node):
    if isinstance(node, list):
        for item in node: yield from walk_families(item)
        return
    if node.get("rank") == "FAMILY": yield node
    for child in node.get("children", []): yield from walk_families(child)

def build_data_file_index():
    idx = {}
    skip = {"node_modules","portal","shared","scripts","tools","docs","tasks"}
    for d in REPO.iterdir():
        if not d.is_dir() or d.name.startswith(".") or d.name in skip:
            continue
        df = d / "src" / "data" / f"{d.name}.json"
        if df.exists():
            idx[d.name] = df; continue
        for fd in d.iterdir():
            if not fd.is_dir(): continue
            df2 = fd / "src" / "data" / f"{fd.name}.json"
            if df2.exists():
                idx[fd.name] = df2; continue
            for gd in fd.iterdir():
                if not gd.is_dir(): continue
                df3 = gd / "src" / "data" / f"{gd.name}.json"
                if df3.exists(): idx[gd.name] = df3
    return idx

def count_dots(path):
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    count = 0
    stack = [data]
    while stack:
        n = stack.pop()
        if isinstance(n, dict):
            if n.get("rank") == "SPECIES": count += 1
            stack.extend(n.get("children", []))
            count += len(n.get("speciesList", []))
        elif isinstance(n, list): stack.extend(n)
    return count

def audit(k, other, df_idx, color_slugs):
    print(f"\n{'='*60}")
    print(f"  {k.upper()}  (baseline: {other})")
    print(f"{'='*60}")
    tax = load_taxonomy(k)
    if not tax: return print("  No taxonomy file\n")

    all_fams = list(walk_families(tax))
    T = len(all_fams)
    print(f"  Families: {T}")

    imported, unimported = set(), set()
    for fam in all_fams:
        s = fam.get("appSlug","")
        if not s: continue
        sc = fam.get("speciesCount",0)
        kids = bool(fam.get("children"))
        nm = bool(fam.get("notableMembers"))
        # A stub data file (0 species) does not count as imported
        df = s in df_idx and (count_dots(df_idx[s]) or 0) > 0
        if k == "plantae":
            imp = (sc or 0) > 0 or nm
        else:
            imp = kids or df
        (imported if imp else unimported).add(s)

    Im, Un = len(imported), len(unimported)
    print(f"  Imported: {Im}  |  Unimported: {Un}")

    issues = []

    # 1. Color themes
    mt = []
    for f in all_fams:
        s = f.get("appSlug","")
        if s and s not in color_slugs:
            mt.append(s)
    if mt: issues.append(f"THEME GAP: {len(mt)} families w/o theme — {mt[:5]}")
    else: print("  ✓ Themes: all present")

    # 2. speciesCount for imported
    zw = [f["appSlug"] for f in all_fams if f.get("appSlug") in imported and (f.get("speciesCount") or 0) == 0]
    if zw: issues.append(f"speciesCount=0 (imported): {len(zw)} — {zw[:5]}")
    else: print("  ✓ speciesCount: all imported > 0")

    # 3. Orphan data files
    orphan = []
    for s in unimported:
        if s in df_idx:
            c = count_dots(df_idx[s])
            if c and c > 0: orphan.append(f"{s}({c})")
    if orphan: issues.append(f"ORPHAN FILES: {len(orphan)} data files not hooked — {orphan[:3]}")
    else: print("  ✓ No orphan data files")

    for iss in issues:
        print(f"  ❌ {iss}")
    if not issues:
        print("  ✅ Clean")
    return issues

print("Indexing data files...")
idx = build_data_file_index()
print(f"  {len(idx)} files found")

# Pre-parse color slugs
col_a = extract_color_slugs(load_colors("animalia"))
col_p = extract_color_slugs(load_colors("plantae"))
print(f"  Animalia color slugs: {len(col_a)}")
print(f"  Plantae color slugs: {len(col_p)}")

all_issues = []
all_issues.extend(audit("plantae","animalia",idx,col_p))
all_issues.extend(audit("animalia","plantae",idx,col_a))

print(f"\n{'='*60}")
print(f"  TOTAL: {len(all_issues)} cross-kingdom issues")
print(f"{'='*60}")
