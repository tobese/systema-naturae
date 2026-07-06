#!/usr/bin/env python3
"""
powo_enrich.py — Tier-3 plant enrichment from Plants of the World Online (POWO).

Bridge: species name -> cached GBIF usageKey -> GBIF /related -> IPNI LSID
        -> POWO /api/2/taxon/{ipni} -> reconstruct a native-range/lifeform/climate
        summary -> write description + sourcedFrom="powo".

Only touches species currently sourcedFrom "none" (or with no sourcedFrom) that
have a cached GBIF key. Leaves wikipedia/gbif/powo entries alone. Runs standalone
(walks the family JSONs in place) and MUST NOT run while enrichServe is writing.

Caches (portal/data/):
  gbif-cache-{class}.json         -> read: usageKeys map (binomial -> gbif key)
  powo-ipni-cache.json            -> gbif key -> IPNI LSID (or null)
  powo-fields-cache.json          -> IPNI LSID -> reconstructed text (or null)

Usage:
  python3 tools/powo_enrich.py                    # full run
  python3 tools/powo_enrich.py --id 0 --total 4   # shard 0 of 4 (parallel)
  python3 tools/powo_enrich.py --dry              # no file writes
  python3 tools/powo_enrich.py --limit 200        # process at most N species (test)
"""
import json, os, sys, time, threading, argparse
from concurrent.futures import ThreadPoolExecutor

try:
    import cloudscraper
except ImportError:
    sys.exit("cloudscraper required: pip install cloudscraper")
import urllib.request
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "portal", "data")
CLASSES = ["liliopsida", "magnoliopsida"]
IPNI_DATASET = "046bbc50-cae2-47ff-aa43-729fbf53f7c5"
GBIF_UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; POWO enrich)"
POWO_FIELDS = "taxonRemarks,lifeform,climate,hybrid,hybridFormula,taxonomicStatus,name"

IPNI_CACHE_PATH = os.path.join(DATA, "powo-ipni-cache.json")
FIELDS_CACHE_PATH = os.path.join(DATA, "powo-fields-cache.json")

ap = argparse.ArgumentParser()
ap.add_argument("--id", type=int, default=0)
ap.add_argument("--total", type=int, default=1)
ap.add_argument("--dry", action="store_true")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--concurrency", type=int, default=4)
ap.add_argument("--save-every", type=int, default=2000)
args = ap.parse_args()

# When sharded, each process keeps its own cache files to avoid clobbering.
if args.total > 1:
    IPNI_CACHE_PATH = os.path.join(DATA, f"powo-ipni-cache.s{args.id}of{args.total}.json")
    FIELDS_CACHE_PATH = os.path.join(DATA, f"powo-fields-cache.s{args.id}of{args.total}.json")

_tls = threading.local()
def scraper():
    if not hasattr(_tls, "s"):
        _tls.s = cloudscraper.create_scraper()
    return _tls.s

# ---------- caches ----------
_lock = threading.Lock()

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def binomial(name):
    return " ".join(name.split()[:2])

# GBIF key map: binomial -> key
usage_keys = {}
for cls in CLASSES:
    cache = load_json(os.path.join(DATA, f"gbif-cache-{cls}.json"), {})
    for k, v in (cache.get("usageKeys") or {}).items():
        usage_keys[k] = v

ipni_cache = load_json(IPNI_CACHE_PATH, {})    # str(gbifKey) -> ipni | null
fields_cache = load_json(FIELDS_CACHE_PATH, {})  # ipni -> text | null

def save_caches():
    with _lock:
        tmp = IPNI_CACHE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(ipni_cache, f)
        os.replace(tmp, IPNI_CACHE_PATH)
        tmp = FIELDS_CACHE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(fields_cache, f)
        os.replace(tmp, FIELDS_CACHE_PATH)

# ---------- bridge + fetch ----------
def gbif_related_ipni(key):
    skey = str(key)
    if skey in ipni_cache:
        return ipni_cache[skey]
    url = f"https://api.gbif.org/v1/species/{key}/related?limit=100"
    ipni = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": GBIF_UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        for rec in data.get("results", []):
            if rec.get("datasetKey") == IPNI_DATASET:
                tid = rec.get("taxonID", "")
                if tid.startswith("urn:lsid:ipni.org:names:"):
                    ipni = tid
                    break
    except Exception:
        return None  # transient; don't poison cache
    with _lock:
        ipni_cache[skey] = ipni
    return ipni

def powo_reconstruct(ipni):
    """Return {"text": <summary or None>, "distribution": <native range or None>}.
    Backward compatible with old cache entries that stored a bare string."""
    if ipni in fields_cache:
        cached = fields_cache[ipni]
        if isinstance(cached, dict):
            return cached
        return {"text": cached, "distribution": None}  # legacy string entry
    url = f"http://www.plantsoftheworldonline.org/api/2/taxon/{urllib.parse.quote(ipni)}?fields={POWO_FIELDS}"
    result = None
    try:
        r = scraper().get(url, timeout=30)
        if r.status_code == 200:
            d = r.json()
            remarks = (d.get("taxonRemarks") or "").strip() or None
            result = {"text": build_summary(d), "distribution": remarks}
    except Exception:
        return None  # transient; don't poison cache
    with _lock:
        fields_cache[ipni] = result
    return result

def build_summary(d):
    if not d:
        return None
    status = (d.get("taxonomicStatus") or "").lower()
    # Only summarize accepted taxa; synonyms rarely have useful fields
    parts = []
    remarks = d.get("taxonRemarks")
    lifeform = d.get("lifeform")
    climate = d.get("climate")
    lf_ok = lifeform and lifeform.strip().lower() != "unknown"
    cl_ok = climate and climate.strip().lower() != "unknown"
    if remarks and remarks.strip():
        parts.append(f"The native range of this species is {remarks.strip()}.")
    if lf_ok and cl_ok:
        parts.append(f"It is a {lifeform} and grows primarily in the {climate} biome.")
    elif lf_ok:
        parts.append(f"It is a {lifeform}.")
    elif cl_ok:
        parts.append(f"It grows primarily in the {climate} biome.")
    hf = d.get("hybridFormula")
    if hf and hf.strip():
        parts.append(f"The hybrid formula is {hf.strip()}.")
    text = " ".join(parts).strip()
    return text if len(text) > 25 else None

# ---------- walk + enrich ----------
def collect_targets():
    files = []
    for cls in CLASSES:
        base = os.path.join(ROOT, cls)
        for dp, _, fns in os.walk(base):
            if os.path.join("src", "data") not in dp:
                continue
            for fn in fns:
                if fn.endswith(".json"):
                    files.append(os.path.join(dp, fn))
    files.sort()
    files = [f for i, f in enumerate(files) if i % args.total == args.id]
    return files

def species_targets(tree):
    """Yield species nodes needing POWO (sourcedFrom none/absent) with a cached key."""
    out = []
    def walk(n):
        if n.get("rank") == "SPECIES":
            sf = n.get("sourcedFrom")
            if sf in (None, "none"):
                b = binomial(n.get("name", ""))
                key = usage_keys.get(b)
                if key:
                    out.append((n, b, key))
            return
        for c in n.get("children", []):
            walk(c)
    walk(tree)
    return out

def main():
    files = collect_targets()
    print(f"[{args.id}/{args.total}] {len(files)} files")

    # Load trees, gather targets
    trees = {}
    targets = []  # (node, binom, key, file)
    for fp in files:
        try:
            with open(fp) as f:
                tree = json.load(f)
        except Exception:
            continue
        trees[fp] = tree
        for node, b, key in species_targets(tree):
            targets.append((node, b, key, fp))

    if args.limit:
        targets = targets[:args.limit]
    print(f"[{args.id}/{args.total}] {len(targets)} species need POWO (none + cached gbif key)")

    done = {"n": 0, "powo": 0, "empty": 0, "noipni": 0}
    dirty = set()

    def work(t):
        node, b, key, fp = t
        ipni = gbif_related_ipni(key)
        if not ipni:
            done["noipni"] += 1
            return
        res = powo_reconstruct(ipni)
        text = res.get("text") if res else None
        dist = res.get("distribution") if res else None
        if text:
            node["description"] = text
            if dist:
                node["distribution"] = dist
            node["sourcedFrom"] = "powo"
            dirty.add(fp)
            done["powo"] += 1
        else:
            done["empty"] += 1

    def flush(paths):
        if args.dry:
            return
        for p in list(paths):
            try:
                tmp = p + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(trees[p], f, indent=2, ensure_ascii=False)
                    f.write("\n")
                os.replace(tmp, p)
            except Exception as e:
                print(f"  write {p}: {e}")
        paths.clear()

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for i, _ in enumerate(ex.map(work, targets), 1):
            done["n"] = i
            if i % args.save_every == 0:
                flush(dirty)
                save_caches()
                pct = i / max(1, len(targets)) * 100
                print(f"[{args.id}/{args.total}] {i}/{len(targets)} ({pct:.1f}%) "
                      f"powo:{done['powo']} empty:{done['empty']} noipni:{done['noipni']}")

    flush(dirty)
    save_caches()
    print(f"[{args.id}/{args.total}] DONE — powo:{done['powo']} empty:{done['empty']} "
          f"noipni:{done['noipni']} of {len(targets)}")

if __name__ == "__main__":
    main()
