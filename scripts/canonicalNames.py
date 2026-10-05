#!/usr/bin/env python3
"""Resolve a stored name to its canonical form, for name-keyed enrichment.

156,392 of our species names keep the authorship inside `name` -- `Smilax walteri
Pursh`, `Majanthemophyllum pusillum Heer, 1883`. The GBIF enrichers build their
indexes from GBIF *canonical* names and look them up with our *raw* stored name,
so every one of those species silently missed: an empty `commonName` with no
warning and no counter movement.

`name-parse-index.jsonl` already holds the split -- 562,378 entries carry an
authorship and all of them parse cleanly into `canonical` + `authorship`. It is
written by `parseAllNames.py` and is gitignored, so this degrades to an identity
map when it is absent rather than failing.

Use it as a fallback, never as a replacement: a raw hit is an exact match on the
name we actually store, and only if that misses is the canonical form worth
trying.
"""
import json
import os

INDEX = os.path.join("portal", "data", "name-parse-index.jsonl")

_cache = None


TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")


def _load_served():
    """name.lower() -> canonical.lower() from taxaserve, or None."""
    if not TAXASERVE:
        return None
    import urllib.request
    try:
        with urllib.request.urlopen(TAXASERVE + "/health", timeout=10) as r:
            health = json.load(r)
    except Exception:
        print(f"  WARN {TAXASERVE} is not answering; reading {INDEX} instead")
        return None
    print(f"  canonical names from {TAXASERVE}: {health['parseNames']:,} "
          f"(indexed {health['indexed']:.0f})")
    table = {}
    B = 4000
    base = f"{TAXASERVE}/parse?limit={B}"
    off = 0
    while True:
        try:
            with urllib.request.urlopen(f"{base}&offset={off}", timeout=600) as r:
                page = json.load(r)
        except Exception as e:
            print(f"  WARN taxaserve /parse failed at offset {off} ({e}); "
                  f"falling back to the file")
            return None
        rows = page.get("rows") or []
        if not rows:
            break
        for rec in rows:
            raw = (rec.get("n") or "").strip().lower()
            canon = (rec.get("canonical") or "").strip().lower()
            if raw and canon:
                table[raw] = canon
        if len(rows) < B:
            break
        off += B
    print(f"  canonical names via service: {len(table):,}")
    return table


def _load(path=INDEX):
    """name.lower() -> canonical.lower(), or None if the index is unusable.

    With TAXASERVE set, ask a running scripts/taxaserve.py instead of reading
    the 544MB index. The index is a snapshot and this has been the wrong side of
    that fact repeatedly: it scored 13,347 of 16,371 ILDIS legume species as
    already held when only 64 were, and 15,563 Cranefly species as new when
    15,191 were held -- two runs in opposite directions, both from the same
    stale file. The service builds the same table from the family files at
    startup and can be reloaded with POST /reload after an import, so it is
    never a snapshot of anything but the current tree.

    Falls back to the file when the service is not running, so nothing depends
    on it being up.
    """
    global _cache
    if _cache is not None:
        return _cache
    served = _load_served()
    if served is not None:
        _cache = served
        return _cache
    table = {}
    if not os.path.exists(path):
        print(f"  WARN canonical index {path} not found; "
              f"falling back to raw-name matching only")
        _cache = table
        return _cache
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            raw = (rec.get("n") or "").strip().lower()
            canon = (rec.get("canonical") or "").strip().lower()
            if raw and canon:
                table[raw] = canon
    print(f"  canonical index: {len(table):,} names "
          f"({sum(1 for v in table.values() if v):,} with a canonical form)")
    _cache = table
    return _cache


def lookup(index, key):
    """Look `key` up in a GBIF-derived `index`, retrying with the canonical form.

    Returns the index value, or None. The canonical retry is only attempted for
    names that actually carry an authorship, so it costs one dict probe for the
    87% of names that do not.

    Both probes are lowercased, because `_load()` keys its table by
    `name.lower()`. They were not, and every scientific name is mixed case, so
    every caller got None and silently degraded to no match at all -- which is
    how the iNaturalist import filled zero names on its first run, and why
    Mammal Species of the World measured as 100% new when 3,762 of our 7,900
    mammal species are in it. The failure is invisible either way: no exception,
    no warning, just a lookup table that never hits.
    """
    if not key:
        return None
    k = key.strip().lower()
    hit = index.get(k)
    if hit is not None:
        return hit
    canon = _load().get(k)
    if not canon or canon == k:
        return None
    return index.get(canon)
