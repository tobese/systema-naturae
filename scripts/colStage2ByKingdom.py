"""Stage 2 of the Catalogue of Life import, broken down by kingdom.

Stage 1 took the species COL has in families we already have. Stage 2 is
everything else, and the question "which kingdoms?" is not answerable from the
headline number -- the answer decides how much of it is an import and how much
is a change to the shape of the portal.
"""
import collections
import io
import json
import sys
import zipfile

sys.path.insert(0, 'scripts')
import canonicalNames as C  # noqa: E402

COL = ('/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/'
       'col2026-base_dwca.zip')
ACCEPTED = {'accepted', 'provisionally accepted'}

idx = C._load()
canon = set(idx.keys()) | set(idx.values())

z = zipfile.ZipFile(COL)
par, rank, name = {}, {}, {}
with z.open('Taxon.tsv') as f:
    hdr = f.readline().decode('utf-8', 'replace').rstrip('\n').split('\t')
    ci = {h: i for i, h in enumerate(hdr)}
    for line in io.TextIOWrapper(f, encoding='utf-8', errors='replace'):
        p = line.rstrip('\n').split('\t')
        if len(p) < 7 or p[ci['dwc:taxonomicStatus']] not in ACCEPTED:
            continue
        tid = p[ci['dwc:taxonID']]
        par[tid] = p[ci['dwc:parentNameUsageID']]
        rank[tid] = p[ci['dwc:taxonRank']]
        name[tid] = p[ci['dwc:scientificName']]


def top(tid, want):
    cur, n = tid, 0
    while cur and n < 50:
        if rank.get(cur) == want:
            return cur
        cur = par.get(cur)
        n += 1
    return None


def kingdom_of(tid):
    k = top(tid, 'kingdom')
    if k:
        return name.get(k, '?')
    for want in ('superkingdom', 'domain'):
        k = top(tid, want)
        if k:
            return name.get(k, '?')
    return '(unresolved)'


# families we hold, by lowercased name
ours = set()
import glob  # noqa: E402
for f in glob.glob('taxonomy/*/**/src/data/*.json', recursive=True):
    if 'node_modules' in f:
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if d.get('rank') == 'FAMILY':
        ours.add((d.get('name') or '').strip().lower())

ours_k = collections.Counter()
for f in glob.glob('taxonomy/*/**/src/data/*.json', recursive=True):
    if 'node_modules' in f:
        continue
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if d.get('rank') == 'FAMILY':
        ours_k[f.split('/')[1].lower()] += 1

s2_species = collections.Counter()
s2_fams = collections.defaultdict(set)
s2_ords = collections.defaultdict(set)
s1_by_k = collections.Counter()

for tid, r in rank.items():
    if r != 'species':
        continue
    nm = name[tid]
    if nm.strip().lower() in canon:
        continue
    k = kingdom_of(tid)
    kk = k.lower()
    fam = top(tid, 'family')
    famname = name.get(fam) if fam else None
    if famname and famname.strip().lower() in ours:
        s1_by_k[k] += 1
        continue
    s2_species[k] += 1
    o = top(tid, 'order')
    if o:
        s2_ords[k].add(name.get(o))
    if famname:
        s2_fams[k].add(famname)

print(f"  Stage 1 already applied, by kingdom: {dict(s1_by_k.most_common())}\n")
print(f"  {'kingdom':<26}{'stage2 species':>15}{'new families':>14}{'new orders':>12}{'our families':>14}")
tot = [0, 0, 0]
for k, v in s2_species.most_common(14):
    fams = len(s2_fams[k])
    ords = len(s2_ords[k])
    tot[0] += v
    tot[1] += fams
    tot[2] += ords
    print(f"  {k:<26}{v:>15,}{fams:>14,}{ords:>12,}{ours_k.get(kk, 0):>14,}")
print(f"  {'TOTAL':<26}{tot[0]:>15,}{tot[1]:>14,}{tot[2]:>12,}")
