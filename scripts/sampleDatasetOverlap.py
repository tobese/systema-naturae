#!/usr/bin/env python3
"""Sampled overlap between a ChecklistBank dataset and the tree, via the API.

Six archives arrived in the inbox and downloading all of them to find out whether
they are worth anything is the expensive way to answer the question. This asks
the API instead: page a sample of a dataset's accepted names, test each against
the species names actually on disk, and report the hit rate with the dataset's
true name-usage total beside it.

The sampling is not a shortcut around the earlier mistake, it is the correction
to it. Comparing a dataset's name-usage count against our node counts is what
made ReptileDB look like a 2x gap when 15,611 of its 15,612 species were already
on disk -- the counts include synonyms and subspecies. A hit rate over real names
does not have that failure mode, and with a few hundred names per dataset the
uncertainty is small enough to triage on.

Names come from `usage.name.scientificName` in ChecklistBank's search response;
`name` at the top level of each hit is null, which is worth knowing before
writing the loop that reads it.

    python3 scripts/sampleDatasetOverlap.py 1018 [1010 ...]

Set TAXASERVE=http://127.0.0.1:9882 to ask a running scripts/taxaserve.py
instead of reading the tree. That is the difference between triaging six
datasets in a minute and not finishing in half an hour: the fallback below
walks all 14,085 family files to build its held-set, which is the single
largest fixed cost in this script and is paid again by every caller.
"""
import glob
import json
import os
import sys
import urllib.request

API = "https://api.checklistbank.org"
PAGES = 6
PAGE_SIZE = 100


def get(url):
    with urllib.request.urlopen(url, timeout=60) as fh:
        return json.load(fh)


def meta(key):
    d = get(f"{API}/dataset/{key}")
    if isinstance(d, list):
        d = d[0] if d else {}
    return d


def sample_names(key, pages=PAGES, size=PAGE_SIZE):
    """(accepted names by rank, total name usages)."""
    names = []
    total = None
    for p in range(pages):
        d = get(f"{API}/dataset/{key}/nameusage/search?limit={size}"
                 f"&offset={p * size}&rank=SPECIES&status=ACCEPTED")
        if total is None:
            total = d.get("total")
        res = d.get("result") or []
        if not res:
            break
        for r in res:
            u = r.get("usage") or {}
            if u.get("status") != "accepted":
                continue
            nm = (u.get("name") or {}).get("scientificName")
            rank = (u.get("name") or {}).get("rank")
            if nm:
                names.append((nm, rank))
    return names, total


TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")


def serve_health():
    if not TAXASERVE:
        return None
    try:
        r = json.loads(urllib.request.urlopen(TAXASERVE + "/health", timeout=10).read())
        return r
    except Exception:
        return None


def served_held(names):
    """Ask taxaserve which of `names` we hold. None if it is not running."""
    if not TAXASERVE:
        return None
    out = {}
    B = 4000
    ns = list(names)
    for i in range(0, len(ns), B):
        chunk = ns[i:i + B]
        req = urllib.request.Request(
            TAXASERVE + "/held", data=json.dumps({"names": chunk}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception:
            return None
        out.update(r.get("held") or {})
    # taxaserve echoes the caller's casing back as the key, but the caller
    # compares lowercased names, so a mixed-case sample silently reads as 0%
    # held. Normalise once, here, where the client's own contract lives.
    return {k.lower(): v for k, v in out.items()}


def held_names(kingdom="animalia"):
    """every species name on disk for a kingdom, lower-cased, dagger stripped."""
    out = set()
    for f in glob.glob(f"taxonomy/{kingdom}/**/src/data/*.json", recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        st = list(d.get("children") or [])
        while st:
            n = st.pop()
            if n.get("rank") == "SPECIES" and n.get("name"):
                out.add(n["name"].lstrip("\u2020").strip().lower())
            st.extend(n.get("children") or [])
    return out


def main() -> int:
    keys = [int(a) for a in sys.argv[1:]] or [1018]
    # Walk each kingdom's files ONCE. This called held_names() five times for
    # animalia alone -- once per print, once per assignment -- and each call
    # re-reads all 10,601 animalia family files, so the fixed cost was five
    # full passes over 14,085 files before a single API call was made. With
    # animalia at 1.68M species that dominated the runtime and made triaging
    # three datasets look like a hang.
    h = serve_health()
    if h:
        print(f"  taxaserve at {TAXASERVE}: {h['speciesNames']:,} species names, "
              f"{h['families']:,} families, indexed {h['indexed']:.0f}")
    else:
        if TAXASERVE:
            print(f"  {TAXASERVE} is not answering; reading the tree instead")
        held = {k: held_names(k) for k in ("animalia", "plantae", "fungi",
                                           "chromista")}
        all_held = set()
        for v in held.values():
            all_held |= v
        print("  our tree on disk: " + ", ".join(
            f"{k} {len(v):,}" for k, v in held.items()))

    for key in keys:
        m = meta(key)
        print(f"\n=== {key}  {m.get('alias')} — {m.get('title')}")
        print(f"    v{m.get('version')} issued {str(m.get('issued'))[:10]}  "
              f"licence {m.get('license')}  doi {m.get('doi')}")
        names, total = sample_names(key)
        sp = [(n, r) for n, r in names if (r or "").lower() in ("species", "subspecies")]
        if not sp:
            print(f"    sample: no species in {len(names)} names "
                  f"(ranks: {sorted({r for _, r in names})[:6]})")
            continue
        served = served_held([n for n, _r in sp])
        if served is not None and not served and len(sp) > 50:
            raise SystemExit(
                f"  taxaserve reports 0 of {len(sp)} sampled species held, "
                f"which cannot be right for this tree. Refusing to write that "
                f"down as a verdict -- check the key casing in served_held() "
                f"or run without TAXASERVE.")
        hit = 0
        miss = []
        for n, _r in sp:
            k = n.lower()
            if served is not None:
                if k in served:
                    hit += 1
                else:
                    miss.append(n)
            elif k in all_held:
                hit += 1
            else:
                miss.append(n)
        pct = hit / len(sp) * 100
        print(f"    dataset total name usages: {total:,}")
        print(f"    sampled {len(sp):,} species of {len(names):,} names  ->  "
              f"{hit:,} already held ({pct:.1f}%)")
        print(f"    sampled-not-held: {len(sp) - hit:,} of {len(sp):,} "
              f"({100 - pct:.1f}%)")
        for n in miss[:6]:
            print(f"        not held: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())