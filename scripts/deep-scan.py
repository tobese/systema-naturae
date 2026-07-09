#!/usr/bin/env python3
"""Full deep scan: appSlug<->file<->taxonomy + theme symmetric diff (both kingdoms)."""
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def load_tax(k):
    p = REPO/"portal"/"data"/("taxonomy.json" if k=="animalia" else "taxonomy-plantae-snippet.json")
    return json.loads(p.read_text()) if p.exists() else None

def colors_text(k):
    p = REPO/"portal"/"src"/("colorRegistry.ts" if k=="animalia" else "colorRegistryPlantae.ts")
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
for k in ("animalia","plantae"):
    print("="*60); print(f"  {k.upper()}"); print("="*60)
    tax=load_tax(k)
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

    if k=="animalia":
        # animalia uses on-disk data files
        missing_file=sorted(s for s in slugs if s not in disk)
        rep("appSlugs with NO data file on disk", missing_file)
    print()

print("="*60)
print(f"  TOTAL structural issues: {issues_total}")
print("="*60)
