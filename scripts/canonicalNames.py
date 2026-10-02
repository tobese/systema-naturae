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


def _load(path=INDEX):
    """name.lower() -> canonical.lower(), or None if the index is unusable."""
    global _cache
    if _cache is not None:
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
    """
    hit = index.get(key)
    if hit is not None:
        return hit
    canon = _load().get(key)
    if not canon or canon == key:
        return None
    return index.get(canon)
