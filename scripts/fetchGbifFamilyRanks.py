#!/usr/bin/env python3
"""Stamp GBIF's own rank-key chain onto every family's own data file.

A single `/v1/species/match?name=...&rank=FAMILY` call returns not just
GBIF's `familyKey` for that name but the whole ancestor chain in one
response -- `kingdomKey`, `phylumKey`, `classKey`, `orderKey`, `familyKey` --
because GBIF's backbone (built from the Catalogue of Life) assigns a
`usageKey` to every rank, not just family. Confirmed live:

    name=Hemidiscaceae&rank=FAMILY ->
        kingdomKey 4, phylumKey 98, classKey 7947184, orderKey 1098,
        familyKey 2922

Species nodes already carry `sourceIds` from whichever importer touched
them (col, itis, gbif, checklistbank, wfo, ...). No FAMILY-rank node ever
has: a scan of all 14,083 family files found zero. The only identifiers a
family has today are `id`/`appSlug`, which are the family's own name,
unique only within the one kingdom that declares it -- not globally. That
gap is exactly what let 328 species of the diatom genus Actinocyclus ride
into the nudibranch family Actinocyclidae: some source archive filed them
under an old/alternate family name that happens to collide with a real,
unrelated family in a different kingdom, and nothing anywhere compared a
stable external id to catch it.

GBIF's familyKey is cross-kingdom-unique by construction (one backbone,
all six kingdoms), so stamping it here gives every family a check digit a
future importer -- or a future audit -- can compare against, rather than
trusting a bare name string the way `importColChecklist.py`'s FAM2K did.

Most of GBIF's own data is already sitting on disk, from the 191 per-class
caches `cacheGbifData.ts` built (`portal/data/gbif-cache-<class>.json`,
each carrying a `familyKeyToName` map). 3,464 of our 14,084 families
already have their familyKey there for free -- re-fetching it live would
just repeat a call this repo already made. But those per-class caches
never persisted the classKey they looked up to run their own query (same
discard-after-use pattern this script exists to stop repeating), so the
rest of the chain -- kingdomKey, phylumKey, classKey, orderKey -- isn't in
them. Those four are also identical for every family in the same order, so
rather than one live call per already-cached family, this makes one live
ORDER-rank match per distinct (kingdom, order) pair instead -- 622 calls
covering all 3,464, not 3,464 calls each repeating the same four numbers.
Only families with no local familyKey make the full per-family call.

Two phases, both resumable:

    python3 scripts/fetchGbifFamilyRanks.py                 # fetch + cache only
    python3 scripts/fetchGbifFamilyRanks.py --apply          # also stamp sourceIds.gbif
    python3 scripts/fetchGbifFamilyRanks.py --kingdom chromista --limit 20   # test run

Writes `portal/data/gbif-family-ranks-cache.json` unconditionally (the
fetch is the expensive part; the cache makes a second run, or --apply on
its own, free). Only `--apply` touches any file under `taxonomy/`, and
only families where GBIF returned a confident FAMILY match change at all.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import iter_family_files  # noqa: E402

OUT = "portal/data/gbif-family-ranks-cache.json"
UA = ("systema-naturae/1.0 (https://github.com/tobese/systema-naturae; "
      "taxonomy tree maintenance)")
MATCH_URL = "https://api.gbif.org/v1/species/match"

# Same courtesy pace as fetchGbifFamilyCache.py: one request at a time with a
# pause, retried on transient failures.
PAUSE = 0.12
RETRIES = 4

RANK_KEYS = ("kingdomKey", "phylumKey", "classKey", "orderKey", "familyKey")
ANCESTOR_KEYS = ("kingdomKey", "phylumKey", "classKey", "orderKey")


def load_local_family_keys() -> dict[str, int]:
    """name.lower() -> GBIF familyKey, mined from the per-class caches already
    on disk (`portal/data/gbif-cache-<class>.json[.gz]`, built by
    `cacheGbifClass.ts`/`cacheGbifData.ts`). Across all 191 of them, no family
    name maps to more than one distinct key, so first-seen wins without
    needing to reconcile a conflict.
    """
    out: dict[str, int] = {}
    for path in glob.glob("portal/data/gbif-cache-*.json*"):
        try:
            opener = gzip.open if path.endswith(".gz") else open
            with opener(path, "rt", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        for key, name in (d.get("familyKeyToName") or {}).items():
            out.setdefault(name.lower(), int(key))
    return out


def _request(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == RETRIES - 1:
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == RETRIES - 1:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def match_family(name: str) -> dict | None:
    """GBIF's rank-key chain for a family name, or None with no confident match."""
    url = f"{MATCH_URL}?{urllib.parse.urlencode({'name': name, 'rank': 'FAMILY'})}"
    d = _request(url)
    if d is None:
        return None
    # GBIF's match can resolve to a different rank than asked (a genus, if
    # the name collides with one) or to nothing at all (matchType "NONE").
    # Only trust it when GBIF itself agrees the match IS a family.
    if d.get("rank") != "FAMILY" or d.get("matchType") in (None, "NONE"):
        return None
    out = {k: d[k] for k in RANK_KEYS if k in d}
    if "familyKey" not in out:
        return None
    out["matchType"] = d.get("matchType")
    out["confidence"] = d.get("confidence")
    out["gbifName"] = d.get("canonicalName") or d.get("scientificName")
    return out


def match_order_ancestors(order_name: str) -> dict | None:
    """kingdomKey/phylumKey/classKey/orderKey for an order name, or None."""
    url = f"{MATCH_URL}?{urllib.parse.urlencode({'name': order_name, 'rank': 'ORDER'})}"
    d = _request(url)
    if d is None:
        return None
    if d.get("rank") != "ORDER" or d.get("matchType") in (None, "NONE"):
        return None
    out = {k: d[k] for k in ANCESTOR_KEYS if k in d}
    if "orderKey" not in out:
        return None
    return out


def order_dir_of(path: str) -> str | None:
    """The order-rank directory name from a family file's path.

    `taxonomy/<kingdom>/[<phylum>/][<class>/]<order>/<family>/src/data/*.json`
    -- the order is always the directory directly above the family one.
    """
    parts = path.split(os.sep)
    try:
        family_idx = parts.index("src") - 1
    except ValueError:
        return None
    return parts[family_idx - 1] if family_idx >= 1 else None


def _write(cache: dict, order_cache: dict) -> None:
    doc = {
        "source": "GBIF species API, GET /v1/species/match?name=...&rank=FAMILY "
                  "(or ORDER, for families whose familyKey came from the local "
                  "per-class caches instead)",
        "note": "families: keyed by '<kingdom>/<slug>'; null means GBIF had no "
                "confident FAMILY match for that name. matchType "
                "'LOCAL_CACHE' means familyKey came from an existing "
                "gbif-cache-<class>.json rather than a live call, with the "
                "ancestor keys filled in from orderGroups. orderGroups: keyed "
                "by '<kingdom>/<order-dir>', one live ORDER-rank call shared "
                "across every LOCAL_CACHE family in that order.",
        "families": cache,
        "orderGroups": order_cache,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="stamp sourceIds.gbif onto each family's own data file")
    ap.add_argument("--kingdom", default="", help="default: every kingdom")
    ap.add_argument("--limit", type=int, default=0,
                     help="stop after N families (testing)")
    args = ap.parse_args()

    families = list(iter_family_files(args.kingdom or None))
    if args.limit:
        families = families[:args.limit]
    print(f"  {len(families):,} family files" +
          (f" ({args.kingdom})" if args.kingdom else " (all kingdoms)"))

    local_keys = load_local_family_keys()
    print(f"  {len(local_keys):,} distinct family names already in local "
          f"gbif-cache-*.json files")

    cache = {}
    order_cache = {}
    if os.path.exists(OUT):
        doc = json.load(open(OUT, encoding="utf-8"))
        cache = doc.get("families", {})
        order_cache = doc.get("orderGroups", {})

    todo = [f for f in families if f"{f.kingdom}/{f.slug}" not in cache]
    print(f"  {len(cache):,} already cached, {len(todo):,} to resolve")

    got = miss = from_local = live_family_calls = live_order_calls = 0
    for i, f in enumerate(todo, 1):
        try:
            doc_f = f.load()
        except Exception as e:
            print(f"    ! {f.path}: {e}")
            continue
        name = doc_f.get("name") or f.slug
        key = f"{f.kingdom}/{f.slug}"

        local_key = local_keys.get(name.lower())
        result = None
        if local_key is not None:
            order_dir = order_dir_of(f.path)
            group_key = f"{f.kingdom}/{order_dir}"
            if group_key not in order_cache:
                order_name = (order_dir or "").replace("_", " ").replace("-", " ").title()
                order_cache[group_key] = match_order_ancestors(order_name)
                live_order_calls += 1
                time.sleep(PAUSE)
            ancestors = order_cache.get(group_key)
            if ancestors:
                result = dict(ancestors)
                result["familyKey"] = local_key
                result["matchType"] = "LOCAL_CACHE"
                result["confidence"] = None
                result["gbifName"] = name
                from_local += 1

        if result is None:
            result = match_family(name)
            live_family_calls += 1
            time.sleep(PAUSE)

        cache[key] = result
        if result:
            got += 1
        else:
            miss += 1
        if i % 200 == 0 or i == len(todo):
            print(f"    {i}/{len(todo)}  matched {got:,} ({from_local:,} from "
                  f"local cache)  no match {miss:,}  live calls: "
                  f"{live_family_calls:,} family + {live_order_calls:,} order",
                  flush=True)
            _write(cache, order_cache)

    _write(cache, order_cache)
    print(f"\n  wrote {OUT}: {len(cache):,} families cached "
          f"({got:,} matched -- {from_local:,} from local cache, "
          f"{miss:,} unmatched this run)")
    print(f"  live calls this run: {live_family_calls:,} family-rank, "
          f"{live_order_calls:,} order-rank")

    if not args.apply:
        print("  (dry run -- pass --apply to stamp sourceIds.gbif onto family files)")
        return 0

    stamped = unchanged = skipped = 0
    for f in families:
        key = f"{f.kingdom}/{f.slug}"
        result = cache.get(key)
        if not result:
            skipped += 1
            continue
        doc_f = f.load()
        ids = doc_f.setdefault("sourceIds", {})
        new_val = {k: result[k] for k in RANK_KEYS if k in result}
        if ids.get("gbif") == new_val:
            unchanged += 1
            continue
        prior = ids.get("gbif")
        if prior:
            print(f"    ! {key}: gbif rank keys changed {prior} -> {new_val}")
        ids["gbif"] = new_val
        f.save(doc_f)
        stamped += 1
    print(f"  stamped {stamped:,}  unchanged {unchanged:,}  "
          f"no gbif match {skipped:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
