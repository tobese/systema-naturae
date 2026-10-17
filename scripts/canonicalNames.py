#!/usr/bin/env python3
"""Resolve a stored name to its canonical form, for name-keyed enrichment.

156,392 of our species names keep the authorship inside `name` -- `Smilax walteri
Pursh`, `Majanthemophyllum pusillum Heer, 1883`. The GBIF enrichers build their
indexes from GBIF *canonical* names and look them up with our *raw* stored name,
so every one of those species silently missed: an empty `commonName` with no
warning and no counter movement.

`portal/data/species.parquet` carries a `canonicalName` column (derived locally
at build time, no GBIF parser call), so this prefers that as its first source:
it is always as fresh as the tree and costs a single DuckDB read rather than the
3.2h network round-trip that `name-parse-index.jsonl` needs. The jsonl and the
`taxaserve` service remain as fallbacks.

Use it as a fallback, never as a replacement: a raw hit is an exact match on the
name we actually store, and only if that misses is the canonical form worth
trying.
"""
import json
import os
import sys
import time

INDEX = os.path.join("portal", "data", "name-parse-index.jsonl")
SPECIES_PARQUET = os.path.join("portal", "data", "species.parquet")

_cache = None

TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")


def _load_parquet():
    """name.lower() -> canonical.lower() from species.parquet, or None.

    Prefers the parquet over the 544 MB jsonl: it is built alongside the tree
    (buildSpeciesParquet.py) and always current, whereas the jsonl is a stale
    snapshot that has silently drifted in both directions before.

    DuckDB is only in the project's .venv-parquet, so when it is not importable
    in the current interpreter the query is run as a subprocess via PARQUET_PY.
    """
    if not os.path.exists(SPECIES_PARQUET):
        return None
    parquet_py = os.environ.get("PARQUET_PY", os.path.join(os.path.dirname(__file__),
                                   "..", ".venv-parquet", "bin", "python3"))
    parquet_py = parquet_py if os.path.exists(parquet_py) else "python3"
    probe = (
        "import duckdb,json;"
        "con=duckdb.connect();"
        "rows=con.execute(\"SELECT name, canonicalName FROM "
        "read_parquet('portal/data/species.parquet') "
        "WHERE canonicalName IS NOT NULL AND canonicalName != name\").fetchall();"
        "print(json.dumps(rows))"
    )
    try:
        import duckdb  # noqa: F401
        in_process = True
    except ImportError:
        in_process = False
    if not in_process:
        import subprocess
        try:
            out = subprocess.run([parquet_py, "-c", probe],
                                 capture_output=True, text=True, timeout=120)
            if out.returncode != 0:
                print(f"  WARN parquet subprocess failed ({out.stderr.strip()[:200]}); "
                      f"falling back to {INDEX}")
                return None
            rows = json.loads(out.stdout)
        except Exception as e:
            print(f"  WARN parquet subprocess failed ({e}); falling back to {INDEX}")
            return None
    else:
        con = duckdb.connect()
        t0 = time.time()
        rows = con.execute(
            "SELECT name, canonicalName FROM read_parquet(?) "
            "WHERE canonicalName IS NOT NULL AND canonicalName != name"
            , [SPECIES_PARQUET]
        ).fetchall()
        con.close()
        print(f"  canonical from parquet: {len(rows):,} rows ({time.time()-t0:.1f}s)")
    table = {n.strip().lower(): c.strip().lower() for n, c in rows if n and c}
    print(f"  canonical from parquet: {len(table):,} names")
    return table


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
    the index. The index (monolith or per-family sidecars) is a snapshot and
    this has been the wrong side of that fact repeatedly: it scored 13,347 of
    16,371 ILDIS legume species as already held when only 64 were, and 15,563
    Cranefly species as new when 15,191 were held -- two runs in opposite
    directions, both from the same stale file. The service builds the same table
    from the family files at startup and can be reloaded with POST /reload after
    an import, so it is never a snapshot of anything but the current tree.

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
    pq = _load_parquet()
    if pq is not None:
        _cache = pq
        return _cache
    table = {}
    if not os.path.exists(path):
        print(f"  WARN canonical index {path} not found; "
              f"falling back to raw-name matching only")
        _cache = table
        return _cache
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import nameIndexCache  # noqa: E402
    records = nameIndexCache.load_all_records()
    for rec in records:
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
