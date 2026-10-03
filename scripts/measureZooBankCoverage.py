#!/usr/bin/env python3
"""Measure how much of our animal names ZooBank can actually speak to.

ZooBank is the ICZN's official nomenclatural register and is the only
nomenclatural authority we have for animals. It is worth measuring rather than
assuming: 395,528 of our 634,055 animalia species carry no authorship at all, so
if ZooBank resolves a decent share of them it is the largest single
authorship-enrichment opportunity visible.

Deliberately sequential and rate-limited, with a local cache. ZooBank's own
notice says they are "experiencing extremely high demand" and are "testing a new
system to block the high volume of web traffic from robots"; the API answers in
about 1.5 s a request, so a 395k-name sweep is roughly seven days sequential and
is not something to launch at someone's service without asking. This measures a
sample so the decision can be made on a number. The cache means re-running costs
nothing and a larger sample can be accumulated in slices.

Usage:
    python3 scripts/measureZooBankCoverage.py --sample 150
    python3 scripts/measureZooBankCoverage.py --sample 150 --delay 2.0
"""
import argparse
import glob
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://zoobank.org/NomenclaturalActs.json"
# Kept in git: 400 measured queries with their answers is the evidence behind the
# 8.8% coverage figure in docs/globalnames-triage.md, and it makes re-measuring
# with a larger sample incremental rather than starting over.
CACHE = "portal/data/zoobank-coverage.json"
UA = ("SystemaNaturae/1.0 (taxonomy portal; nomenclatural coverage measurement; "
      "contact via the repository maintainer)")


def load_cache():
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(c, fh, indent=1, ensure_ascii=False)


def sample_names(n, seed=17):
    names = []
    for f in glob.glob("taxonomy/animalia/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        stack = [d]
        while stack:
            x = stack.pop()
            if x.get("rank") == "SPECIES" and x.get("name") and not x.get("authorship"):
                names.append(x["name"])
            stack.extend(x.get("children") or [])
            stack.extend(x.get("speciesList") or [])
    random.seed(seed)
    return random.sample(names, min(n, len(names)))


def epithet(name):
    """Second word of a binomial, with any authorship or rank marker removed."""
    parts = (name or "").split()
    if len(parts) < 2:
        return None
    return parts[1]


def query(name, timeout=45):
    url = f"{API}?{urllib.parse.urlencode({'search_term': name})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def match_for(records, name):
    """The ZooBank act for this name, or None.

    ZooBank's search is substring-based over `cleanprotonym`, so a binomial query
    returns every subspecies act filed under it -- "Homo sapiens" comes back as
    Afer, Americanus and Aſiaticus, the subspecies of ours. Matching therefore
    compares the epithet, not the query string, or every binomial would look like
    a hit.
    """
    want = epithet(name)
    if not want:
        return None
    genus = name.split()[0]
    for r in records or []:
        ns = (r.get("namestring") or "").strip()
        protonym = (r.get("cleanprotonym") or "").strip()
        if ns.casefold() == want.casefold():
            # prefer an act whose full name carries our genus
            if not protonym or protonym.split()[0].casefold() == genus.casefold():
                return r
    for r in records or []:
        if (r.get("namestring") or "").strip().casefold() == want.casefold():
            return r
    return None


def authorship_of(rec, name=None):
    """Clean authorship out of an act's label.

    The raw label duplicates fragments: an act for Cophixalus phaeobalius comes
    back as "phaeobalius Kraus & Allison 2009 2009", and one for Amastra
    spirizona as "spirizona de Ferussac in de Ferussac in de Ferussac 1821". So
    the epithet prefix is stripped, the label is handed to GNparser, and the
    authorship and year are taken from its separate fields rather than from the
    raw string. Falls back to the stripped label when GNparser is unavailable.
    """
    lab = re.sub(r"\s+", " ", (rec.get("label") or rec.get("value") or "").strip())
    ns = (rec.get("namestring") or "").strip()
    if ns and lab.lower().startswith(ns.lower()):
        lab = lab[len(ns):].strip()
    try:
        import taxamatch
        parsed = taxamatch.parse_names([lab]).get(lab)
    except Exception:
        parsed = None
    if parsed and (parsed["authors"] or parsed["years"]):
        auth = parsed["authors"][0] if parsed["authors"] else ""
        yr = str(parsed["years"][0]) if parsed["years"] else ""
        out = " ".join(x for x in (auth, yr) if x)
        if out:
            return out
    return lab


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=150)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between requests; the API answers in ~1.5s, so "
                         "this keeps us at roughly one request per response")
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()

    cache = load_cache()
    if cache:
        print(f"  cache: {len(cache):,} names already queried")
    names = sample_names(args.sample, args.seed)
    todo = [n for n in names if n not in cache]
    print(f"  sample: {len(names):,} names without authorship "
          f"({len(todo):,} not yet cached)")

    hits = misses = errors = 0
    for i, nm in enumerate(todo, 1):
        try:
            recs = query(nm)
            m = match_for(recs, nm)
            cache[nm] = {"hit": bool(m),
                         "authorship": authorship_of(m) if m else None,
                         "lsid": m.get("lsid") if m else None,
                         "candidates": len(recs or [])}
            hits += bool(m)
            misses += not m
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # ZooBank answers 404 when a search matches nothing, which is
                # indistinguishable from an unknown endpoint unless you know it --
                # a nonsense name 404s the same way a real absent name does. Read
                # as a transport error this reported "100% of answered queries
                # matched" on the 18 responses that did arrive, when the honest
                # figure was 18 in 120.
                cache[nm] = {"hit": False, "authorship": None, "lsid": None,
                             "candidates": 0}
                misses += 1
            else:
                cache[nm] = {"hit": None, "error": f"HTTP {e.code}"}
                errors += 1
        except (urllib.error.URLError, TimeoutError,
                json.JSONDecodeError, OSError) as e:
            cache[nm] = {"hit": None, "error": str(e)[:120]}
            errors += 1
        if i % 10 == 0:
            save_cache(cache)
            print(f"    {i:>4}/{len(todo)}  hits {hits}  misses {misses}  errors {errors}")
        time.sleep(args.delay)
    save_cache(cache)

    answered = hits + misses
    print(f"\n  queried {len(todo):,}; answered {answered:,}; errors {errors:,}")
    if answered:
        print(f"  ZooBank resolves {hits:,}/{answered:,} = {hits/answered*100:.1f}%")
    ex = [(n, v["authorship"]) for n, v in cache.items()
          if v.get("hit") and v.get("authorship")][:12]
    if ex:
        print("\n  sample authorship recovered:")
        for n, a in ex:
            print(f"    {n:<44}{a}")
    print(f"\n  cache: {CACHE} ({len(cache):,} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
