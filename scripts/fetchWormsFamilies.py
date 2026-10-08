#!/usr/bin/env python3
"""Fetch 758 empty marine/fossil families from WoRMS (World Register of Marine Species).

Reads portal/data/worms-candidates.json, queries WoRMS REST API for each family,
writes populated family JSONs to taxonomy/animalia/<phylum>/<class>/<order>/<appSlug>/src/data/<appSlug>.json

    python3 scripts/fetchWormsFamilies.py
    python3 scripts/fetchWormsFamilies.py --phylum Mollusca
    python3 scripts/fetchWormsFamilies.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = ROOT / "portal" / "data" / "worms-candidates.json"
CACHE_DIR = ROOT / "portal" / "data" / "worms-cache"
TAXONOMY_ROOT = ROOT / "taxonomy" / "animalia"
TAXONOMY_JSON = ROOT / "portal" / "data" / "taxonomy.json"

WORMS_BASE = "https://www.marinespecies.org/rest"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SystemaNaturae/1.0 (worms-backfill)"})


def sp_id(name: str) -> str:
    return "SP_" + re.sub(r"[^a-zA-Z0-9]", "_", name).upper().strip("_")


def genus_id(name: str) -> str:
    return "GENUS_" + re.sub(r"[^a-zA-Z0-9]", "_", name).upper().strip("_")


def family_id(name: str) -> str:
    return "FAM_" + re.sub(r"[^a-zA-Z0-9]", "_", name).upper().strip("_")


def cache_path(phylum: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]", "_", phylum)
    return CACHE_DIR / f"worms-cache-{safe}.json"


def load_cache(phylum: str) -> dict:
    p = cache_path(phylum)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_cache(phylum: str, cache: dict) -> None:
    cache_path(phylum).write_text(json.dumps(cache, indent=2))


def get_json(url: str, params: dict = None) -> Any | None:
    for attempt in range(3):
        try:
            r = SESSION.get(url, params=params, timeout=30)
            if r.status_code == 204:
                return []
            if r.status_code == 404:
                return None
            r.raise_for_status()
            # Check content type
            ct = r.headers.get("Content-Type", "")
            if "application/json" not in ct:
                print(f"    WARNING: non-JSON response ({ct}) for {url}")
                time.sleep(2 ** attempt)
                continue
            return r.json()
        except requests.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except json.JSONDecodeError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return None


def get_aphia_id_by_name(name: str) -> int | None:
    url = f"{WORMS_BASE}/AphiaIDByName/{requests.utils.quote(name)}"
    params = {"marine_only": "false"}
    data = get_json(url, params)
    if data is None:
        return None
    if isinstance(data, list):
        for rec in data:
            if rec.get("status") == "accepted":
                return rec.get("AphiaID")
        return data[0].get("AphiaID") if data else None
    if isinstance(data, int):
        return data if data > 0 else None
    return None


def get_aphia_children(aphia_id: int) -> list[dict]:
    children = []
    offset = 1
    while True:
        url = f"{WORMS_BASE}/AphiaChildrenByAphiaID/{aphia_id}"
        params = {"marine_only": "false", "offset": offset}
        page = get_json(url, params)
        if not page:
            break
        children.extend(page)
        if len(page) < 50:
            break
        offset += 50
        time.sleep(0.2)
    return children


def fetch_family_data(candidate: dict, dry_run: bool = False) -> dict | None:
    family_name = candidate["family"]
    app_slug = candidate["appSlug"]
    phylum = candidate["phylum"]
    cls = candidate["class"]
    gbif_key = candidate.get("gbifFamilyKey")

    print(f"  [{phylum}] {family_name} ({app_slug})")

    # Load phylum cache
    cache = load_cache(phylum)
    cache_key = family_name

    if cache_key in cache:
        cached = cache[cache_key]
        aphia_id = cached.get("aphiaID")
        if aphia_id is None:
            print(f"    cached: no AphiaID")
            return None
        print(f"    cached AphiaID: {aphia_id}")
    else:
        aphia_id = get_aphia_id_by_name(family_name)
        cache[cache_key] = {"aphiaID": aphia_id, "fetchedAt": time.time()}
        save_cache(phylum, cache)
        if aphia_id is None:
            print(f"    no AphiaID found")
            return None
        print(f"    AphiaID: {aphia_id}")
        time.sleep(0.3)

    # Fetch genera
    genera_cache_key = f"{aphia_id}_genera"
    if genera_cache_key in cache:
        genera = cache[genera_cache_key]
        print(f"    cached genera: {len(genera)}")
    else:
        children = get_aphia_children(aphia_id)
        genera = [c for c in children if c.get("rank") == "Genus"]
        cache[genera_cache_key] = genera
        save_cache(phylum, cache)
        print(f"    fetched genera: {len(genera)}")
        time.sleep(0.3)

    if not genera:
        print(f"    no genera")
        return None

    # For each genus, fetch species
    genus_nodes = []
    total_species = 0
    for gen in genera:
        g_name = gen.get("scientificname") or gen.get("name")
        if not g_name:
            continue
        g_aphia = gen.get("AphiaID")
        if not g_aphia:
            continue

        # Check species cache
        species_cache_key = f"{g_aphia}_species"
        if species_cache_key in cache:
            species_list = cache[species_cache_key]
        else:
            sp_children = get_aphia_children(g_aphia)
            species_list = [
                s for s in sp_children
                if s.get("rank") == "Species"
                and s.get("status") in ("accepted", "alternate representation")
            ]
            cache[species_cache_key] = species_list
            save_cache(phylum, cache)
            time.sleep(0.15)

        if not species_list:
            continue

        species_nodes = []
        for sp in species_list:
            sp_name = sp.get("scientificname") or sp.get("name")
            if not sp_name or " " not in sp_name:
                continue
            sp_aphia = sp.get("AphiaID")
            source_ids = {"worms": str(sp_aphia)} if sp_aphia else {}
            species_nodes.append({
                "id": sp_id(sp_name),
                "name": sp_name,
                "rank": "SPECIES",
                "lineage": g_name,
                "subspeciesCount": 0,
                "sourcedFrom": "worms",
                "sourceIds": source_ids,
            })

        if species_nodes:
            genus_nodes.append({
                "id": genus_id(g_name),
                "name": g_name,
                "rank": "GENUS",
                "lineage": g_name,
                "description": f"{g_name} — a genus in the family {family_name}.",
                "children": species_nodes,
            })
            total_species += len(species_nodes)

    if not genus_nodes:
        print(f"    no accepted species")
        return None

    print(f"    {len(genus_nodes)} genera, {total_species} species")

    if dry_run:
        return {"family": family_name, "appSlug": app_slug, "species": total_species}

    # Build family JSON
    data = {
        "id": family_id(family_name),
        "name": family_name,
        "rank": "FAMILY",
        "commonName": family_name,
        "description": f"{family_name} — a family in the class {cls}.",
        "sourcedFrom": "worms",
        "children": genus_nodes,
    }

    # Determine order from taxonomy.json
    order_name = "Unknown"
    try:
        tax = json.loads(TAXONOMY_JSON.read_text())
        def find_order(n, current_class=None, current_order=None):
            nonlocal order_name
            r = n.get("rank")
            if r == "CLASS":
                current_class = n.get("name")
            if r == "ORDER":
                current_order = n.get("name")
            if r == "FAMILY" and n.get("appSlug") == app_slug:
                order_name = current_order or "Unknown"
                return True
            for c in n.get("children", []):
                if find_order(c, current_class, current_order):
                    return True
            return False
        find_order(tax)
    except Exception:
        pass

    # Write family file
    order_dir = order_name.lower().replace(" ", "_")
    if order_dir == "unknown":
        order_dir = "unknown"
    cls_dir = cls.lower().replace(" ", "_")
    phylum_dir = phylum.lower().replace(" ", "_")

    outdir = TAXONOMY_ROOT / phylum_dir / cls_dir / order_dir / app_slug / "src" / "data"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / f"{app_slug}.json"
    outfile.write_text(json.dumps(data, indent=2) + "\n")
    print(f"    wrote {outfile.relative_to(ROOT)}")

    return {"family": family_name, "appSlug": app_slug, "species": total_species}


def update_taxonomy_counts(results: list[dict]) -> None:
    """Update taxonomy.json with speciesCount for successfully fetched families."""
    if not results:
        return
    tax = json.loads(TAXONOMY_JSON.read_text())
    updated = 0

    def walk(n):
        nonlocal updated
        if n.get("rank") == "FAMILY":
            app_slug = n.get("appSlug")
            for res in results:
                if res["appSlug"] == app_slug:
                    n["speciesCount"] = res["species"]
                    updated += 1
                    break
        for c in n.get("children", []):
            walk(c)

    walk(tax)
    TAXONOMY_JSON.write_text(json.dumps(tax, indent=2) + "\n")
    print(f"  Updated taxonomy.json: {updated} families")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phylum", help="Process only this phylum")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, help="Process only N families")
    args = ap.parse_args()

    if not CANDIDATES_PATH.exists():
        print(f"Missing {CANDIDATES_PATH}")
        return 1

    data = json.loads(CANDIDATES_PATH.read_text())
    candidates = data["families"]

    if args.phylum:
        candidates = [c for c in candidates if c["phylum"] == args.phylum]
        print(f"Filtered to phylum {args.phylum}: {len(candidates)} families")

    if args.limit:
        candidates = candidates[:args.limit]
        print(f"Limited to {args.limit} families")

    print(f"Processing {len(candidates)} families...")

    results = []
    errors = 0
    for i, cand in enumerate(candidates):
        try:
            res = fetch_family_data(cand, dry_run=args.dry_run)
            if res:
                results.append(res)
        except Exception as e:
            errors += 1
            print(f"    ERROR: {e}")
        if i % 10 == 0 and i > 0:
            time.sleep(1)

    print(f"\nDone. {len(results)} families written, {errors} errors.")
    if results:
        total = sum(r["species"] for r in results)
        print(f"Total species: {total}")
        if not args.dry_run:
            update_taxonomy_counts(results)
        else:
            print("(dry run — nothing written)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())