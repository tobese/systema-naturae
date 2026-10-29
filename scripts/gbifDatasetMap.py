#!/usr/bin/env python3
"""Map each GBIF checklist dataset to its ChecklistBank copy.

The import-ordinator dashboard's GBIF tab lists GBIF's checklist datasets
(<sources>/gbif-datasets.tsv) so every one of them can carry a decision:
already in the pipeline, held, declined -- or skipped / added from the
dashboard. The pipeline itself is keyed by ChecklistBank dataset
(checklistbank-<key>), and GBIF keys are UUIDs, so the two only line up
through this map. CLAUDE.md's warning applies in reverse here: a GBIF
dataset is very often a dataset ChecklistBank already serves under another
key, and that is exactly what the map is for.

Matching, strongest first -- the method is recorded per row:
  gbifKey  ChecklistBank's own record of the GBIF dataset it mirrors
  doi      same DOI on both sides
  title    same normalised title (only when exactly one ChecklistBank
           dataset has it -- an ambiguous title is left unmatched)

Writes <sources>/gbif-dataset-map.json: {gbif_uuid: {"clb": key, "by": method}}.
The ChecklistBank catalogue is cached at <sources>/clb-catalogue.json;
--refresh re-pages it (~66 requests).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.request

ROOT = os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources")
TSV = os.path.join(ROOT, "gbif-datasets.tsv")
CATALOGUE = os.path.join(ROOT, "clb-catalogue.json")
OUT = os.path.join(ROOT, "gbif-dataset-map.json")
API = "https://api.checklistbank.org/dataset"
UA = "systema-naturae-triage/1.0 (+https://github.com/tobese/systema-naturae)"
PAGE = 1000


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def norm_doi(s: str) -> str:
    s = (s or "").strip().lower()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", s)


def fetch_catalogue() -> list:
    rows, offset = [], 0
    while True:
        req = urllib.request.Request(f"{API}?limit={PAGE}&offset={offset}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            page = json.load(r)
        result = page.get("result") or []
        rows += [{k: d.get(k) for k in ("key", "gbifKey", "doi", "title", "origin")}
                 for d in result]
        offset += PAGE
        print(f"  catalogue {len(rows):,}/{page.get('total', '?'):,}", flush=True)
        if not result or offset >= page.get("total", 0):
            return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true", help="re-fetch the ChecklistBank catalogue")
    args = ap.parse_args()

    if args.refresh or not os.path.exists(CATALOGUE):
        cat = fetch_catalogue()
        with open(CATALOGUE, "w", encoding="utf-8") as fh:
            json.dump(cat, fh)
    else:
        with open(CATALOGUE, encoding="utf-8") as fh:
            cat = json.load(fh)

    by_gbif, by_doi, by_title = {}, {}, {}
    for d in cat:
        if d.get("gbifKey"):
            by_gbif.setdefault(d["gbifKey"], d["key"])
        if d.get("doi"):
            by_doi.setdefault(norm_doi(d["doi"]), d["key"])
        by_title.setdefault(norm(d.get("title")), []).append(d["key"])

    out, counts = {}, {"gbifKey": 0, "doi": 0, "title": 0, "none": 0}
    with open(TSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            uuid = (row.get("key") or "").strip()
            if not uuid:
                continue
            # gbif-datasets.tsv rows are ragged (an empty column before the
            # DOI on some), so look for the DOI in any field.
            doi = next((norm_doi(v) for v in row.values()
                        if isinstance(v, str) and v.strip().startswith("10.")), "")
            hit, by = None, "none"
            if uuid in by_gbif:
                hit, by = by_gbif[uuid], "gbifKey"
            elif doi and doi in by_doi:
                hit, by = by_doi[doi], "doi"
            else:
                keys = by_title.get(norm(row.get("title")), [])
                if len(keys) == 1:
                    hit, by = keys[0], "title"
            counts[by] += 1
            if hit is not None:
                out[uuid] = {"clb": hit, "by": by}

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=0)
    print(f"wrote {OUT}: {len(out):,} mapped ({counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
