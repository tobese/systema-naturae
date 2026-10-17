#!/usr/bin/env python3
"""Shared read/write for per-family name-parse-index sidecars.

The monolith `portal/data/name-parse-index.jsonl` (559MB) is split into
`portal/data/name-parse-index/<familySlug>.jsonl` sidecars, one per family,
plus `portal/data/name-parse-index-manifest.json` tracking each sidecar's
freshness against its family file's mtime+size.

Reading: `load_family_index(slug)` returns the parse records for one family's
names, invalidated by the family file's mtime+size.

Writing: `save_family_index(slug, records, mtime_ns, size, manifest)` writes one
sidecar and updates the manifest atomically (`.tmp` + `os.replace`).

Monolith fallback: `load_monolith()` reads the old `name-parse-index.jsonl` if
present, for transitional runs where some families haven't been split yet.

Sync: `syncNameIndex.py` diffs manifests between machines and transfers only
changed sidecars.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

INDEX_DIR = os.path.join(ROOT, "portal", "data", "name-parse-index")
MANIFEST_PATH = os.path.join(INDEX_DIR, "manifest.json")
MONOLITH_PATH = os.path.join(ROOT, "portal", "data", "name-parse-index.jsonl")


def family_sidecar_path(slug: str) -> str:
    return os.path.join(INDEX_DIR, f"{slug}.jsonl")


def load_manifest() -> dict:
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_manifest(manifest: dict) -> None:
    os.makedirs(INDEX_DIR, exist_ok=True)
    tmp = MANIFEST_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    os.replace(tmp, MANIFEST_PATH)


def family_index_fresh(slug: str, mtime_ns: int, size: int, manifest: dict | None = None) -> bool:
    """True if the sidecar for `slug` matches the family file's mtime+size."""
    if manifest is None:
        manifest = load_manifest()
    entry = manifest.get(slug)
    if not entry:
        return False
    return entry.get("mtime_ns") == mtime_ns and entry.get("size") == size


def load_family_index(slug: str) -> list:
    """All parse records for one family's names, from its sidecar."""
    path = family_sidecar_path(slug)
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def save_family_index(slug: str, records: list, mtime_ns: int, size: int,
                      manifest: dict) -> None:
    """Write one family's sidecar and record it in the manifest."""
    path = family_sidecar_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    manifest[slug] = {
        "path": f"name-parse-index/{slug}.jsonl",
        "mtime_ns": mtime_ns,
        "size": size,
        "rows": len(records),
    }
    save_manifest(manifest)


def load_monolith() -> list:
    """Read the old monolith index, if present (transitional fallback)."""
    if not os.path.exists(MONOLITH_PATH):
        return []
    records = []
    with open(MONOLITH_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def all_sidecar_slugs() -> list:
    """Every family slug that has a sidecar."""
    if not os.path.isdir(INDEX_DIR):
        return []
    return [f[:-6] for f in os.listdir(INDEX_DIR)
            if f.endswith(".jsonl") and f != "manifest.json"]


def load_all_records() -> list:
    """All parse records, from sidecars if present, else monolith fallback.

    Consumers that used to read `portal/data/name-parse-index.jsonl` in full
    should call this instead. It transparently reads per-family sidecars when
    they exist, falling back to the monolith for transitional runs.
    """
    slugs = all_sidecar_slugs()
    if slugs:
        records = []
        for slug in slugs:
            records.extend(load_family_index(slug))
        return records
    return load_monolith()
