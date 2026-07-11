#!/usr/bin/env python3
"""Full deep scan: appSlug<->file<->taxonomy + theme symmetric diff (both kingdoms)."""
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

TAX_FILE = {"animalia":"taxonomy.json", "plantae":"taxonomy-plantae-snippet.json", "fungi":"taxonomy-fungi.json"}
COLOR_FILE = {"animalia":"colorRegistry.ts", "plantae":"colorRegistryPlantae.ts", "fungi":"colorRegistryFungi.ts"}
KINGDOMS = ("animalia","plantae","fungi")

def load_tax(k):
    p = REPO/"portal"/"data"/TAX_FILE[k]
    return json.loads(p.read_text()) if p.exists() else None

def colors_text(k):
    p = REPO/"portal"/"src"/COLOR_FILE[k]
    return p.read_text() if p.exists() else ""

def registry_slugs(text):
    slugs=set()
    m=re.search(r'export const COLOR_REGISTRY.*?= \{', text)
    if not m: return slugs
    start=m.end(); depth=1; pos=start
    while depth>0 and pos<len(text):
        if text[pos]=='{': depth+=1
        elif text[pos]=='}': depth-=1
        pos+=1
    for m2 in re.finditer(r'["\']?([a-z0-9_-]+)["\']?\s*:', text[start:pos-1]):
        slugs.add(m2.group(1))
    return slugs

def walk_fams(n):
    if isinstance(n,list):
        for x in n: yield from walk_fams(x)
        return
    if n.get("rank")=="FAMILY": yield n
    for c in n.get("children",[]): yield from walk_fams(c)

def disk_index():
    idx={}
    skip={"node_modules","portal","shared","scripts","tools","docs","tasks",".git"}
    for d in REPO.iterdir():
        if not d.is_dir() or d.name.startswith(".") or d.name in skip: continue
        for depth1 in [d]:
            df=depth1/"src"/"data"/f"{depth1.name}.json"
            if df.exists(): idx.setdefault(depth1.name,df)
        for fd in d.iterdir():
            if not fd.is_dir(): continue
            df2=fd/"src"/"data"/f"{fd.name}.json"
            if df2.exists(): idx.setdefault(fd.name,df2)
            for gd in fd.iterdir():
                if not gd.is_dir(): continue
                df3=gd/"src"/"data"/f"{gd.name}.json"
                if df3.exists(): idx.setdefault(gd.name,df3)
                for hd in gd.iterdir():
                    if not hd.is_dir(): continue
                    df4=hd/"src"/"data"/f"{hd.name}.json"
                    if df4.exists(): idx.setdefault(hd.name,df4)
    return idx

disk = disk_index()
print(f"Data files on disk: {len(disk)}\n")

issues_total=0
for k in KINGDOMS:
    tax=load_tax(k)
    if tax is None:
        print("="*60); print(f"  {k.upper()}"); print("="*60)
        print(f"  (skipped — {TAX_FILE[k]} not present yet)\n")
        continue
    print("="*60); print(f"  {k.upper()}"); print("="*60)
    fams=list(walk_fams(tax))
    slugs={f.get("appSlug") for f in fams if f.get("appSlug")}
    themes=registry_slugs(colors_text(k))
    print(f"  taxonomy families: {len(fams)}  |  appSlugs: {len(slugs)}  |  themes: {len(themes)}")

    # 1. taxonomy appSlug w/o theme
    no_theme=sorted(s for s in slugs if s not in themes)
    # 2. themes not referenced by any taxonomy appSlug (unused)
    unused=sorted(t for t in themes if t not in slugs)
    # 3. duplicate appSlugs in taxonomy
    seen={}; dups=[]
    for f in fams:
        s=f.get("appSlug")
        if not s: continue
        seen[s]=seen.get(s,0)+1
    dups=sorted(s for s,c in seen.items() if c>1)

    def rep(label,lst):
        global issues_total
        if lst:
            issues_total+=len(lst)
            print(f"  ❌ {label}: {len(lst)} — {lst[:8]}")
        else:
            print(f"  ✓ {label}: none")

    rep("appSlugs without a color theme", no_theme)
    rep("themes not used by any family (orphan themes)", unused)
    rep("duplicate appSlugs in taxonomy", dups)

    if k in ("animalia","fungi"):
        # these kingdoms use on-disk data files
        missing_file=sorted(s for s in slugs if s not in disk)
        rep("appSlugs with NO data file on disk", missing_file)
    print()

print("="*60)
print("  REVERSE: on-disk data files -> taxonomy (both ways)")
print("="*60)
slugs_by_k={k:({f["appSlug"] for f in walk_fams(load_tax(k)) if f.get("appSlug")} if load_tax(k) else set()) for k in KINGDOMS}
resolved={k:0 for k in KINGDOMS}
orphans=[]
for s in disk:
    for k in KINGDOMS:
        if s in slugs_by_k[k]: resolved[k]+=1; break
    else:
        orphans.append(s)
for k in KINGDOMS:
    print(f"  ✓ {k}: {resolved[k]} on-disk data files resolve to a taxonomy appSlug")
if orphans:
    issues_total+=len(orphans)
    print(f"  ❌ orphan data files (on disk, in NEITHER taxonomy): {len(orphans)} — {sorted(orphans)[:8]}")
else:
    print(f"  ✓ 0 orphans — all {len(disk)} on-disk data files referenced in some taxonomy")
print()

print("="*60)
print(f"  TOTAL structural issues: {issues_total}")
print("="*60)
