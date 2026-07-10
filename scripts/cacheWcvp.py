#!/usr/bin/env python3
"""
cacheWcvp.py — Download the WCVP DwCA and build a local JSON cache indexed
by family.

Parses wcvp_taxon.csv (pipe-delimited, ~507 MB uncompressed) and
wcvp_distribution.csv (~65 MB) from the DwCA zip.

Output: portal/data/wcvp-cache.json
  {
    version: str,
    downloadedAt: str,
    acceptedByFamily: {
      "<family>": [
        {
          ipniId: "urn:lsid:ipni.org:names:...",
          binomial: "Pinus sylvestris",
          genus: "Pinus",
          species: "sylvestris" (epithet),
          authors: "L.",
          taxonRemarks: "Europe to E. Siberia",  # native range description
          lifeform: "tree" | null,
          climate: "temperate" | null,
        }
      ]
    }
  }
"""

import json
import os
import sys
import time
import urllib.request
import zipfile
import io

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_PATH = os.path.join(ROOT, "portal", "data", "wcvp-cache.json")

WCVP_URL = "http://sftp.kew.org/pub/data-repositories/WCVP/wcvp_dwca.zip"
LOCAL_ZIP = os.path.join(ROOT, "portal", "data", "wcvp_dwca.zip")
TAXON_FILE = "wcvp_taxon.csv"
DIST_FILE = "wcvp_distribution.csv"

# Headers (skipped in processing): taxonid|family|genus|specificepithet|...
TAXON_FAMILY = 1
TAXON_GENUS = 2
TAXON_EPITHET = 3
TAXON_NAME = 5
TAXON_AUTH = 6
TAXON_RANK = 7
TAXON_STATUS = 8
TAXON_PARENT = 10
TAXON_REMARKS = 14
TAXON_NAMEID = 15
TAXON_PROPS = 16

ACCEPTED = "Accepted"
SP_RANKS = {"Species", "species", "SPECIES"}


def parse_ipni(nameid: str) -> str | None:
    if not nameid or nameid == "\\N":
        return None
    nameid = nameid.strip()
    if nameid.startswith("ipni:"):
        pid = nameid[5:]
    else:
        pid = nameid
    if not pid:
        return None
    return f"urn:lsid:ipni.org:names:{pid}"


def parse_dynamic_props(raw: str):
    """Extract lifeform and climate from the JSON dynamicProperties column."""
    if not raw or raw == "\\N":
        return {}, {}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return {}, {}
    lf = d.get("lifeform") or None
    cl = d.get("climate") or None
    return lf, cl


def download_wcvp(url: str) -> bytes:
    print(f"Downloading {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "SystemaNaturae/1.0 (WCVP cache)"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    print(f"  Received {len(data):,} bytes")
    return data


def build_cache(data: bytes):
    species_by_family = {}
    total = 0
    accepted = 0
    skipped = 0
    t0 = time.time()

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        # ── taxon file ──
        print(f"  Parsing {TAXON_FILE} ...")
        with z.open(TAXON_FILE) as f:
            reader = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
            for i, raw_line in enumerate(reader):
                if i == 0:
                    continue  # header
                total += 1
                line = raw_line.rstrip("\n\r")
                parts = line.split("|")
                if len(parts) < 18:
                    continue

                if total % 200000 == 0:
                    elapsed = time.time() - t0
                    rate = total / elapsed if elapsed > 0 else 0
                    print(f"    {total:,} lines ({rate:,.0f}/s) accepted={accepted} skip={skipped}")

                rank = parts[TAXON_RANK].strip()
                status = parts[TAXON_STATUS].strip()
                family = parts[TAXON_FAMILY].strip()
                genus = parts[TAXON_GENUS].strip()
                epithet = parts[TAXON_EPITHET].strip()

                # Only accepted species
                if status != ACCEPTED or rank not in SP_RANKS:
                    skipped += 1
                    continue

                if not genus or not epithet:
                    skipped += 1
                    continue

                ipni_id = parse_ipni(parts[TAXON_NAMEID])
                if not ipni_id:
                    skipped += 1
                    continue

                lifeform, climate = parse_dynamic_props(parts[TAXON_PROPS])
                remarks = parts[TAXON_REMARKS].strip() if parts[TAXON_REMARKS].strip() and parts[TAXON_REMARKS].strip() != "\\N" else None

                accepted += 1
                species_by_family.setdefault(family, []).append({
                    "ipniId": ipni_id,
                    "binomial": parts[TAXON_NAME].strip(),
                    "genus": genus,
                    "species": epithet,
                    "authors": parts[TAXON_AUTH].strip(),
                    "taxonRemarks": remarks,
                    "lifeform": lifeform,
                    "climate": climate,
                })

    elapsed = time.time() - t0
    print(f"\n  Processed {total:,} lines in {elapsed:.0f}s")
    print(f"  Accepted species: {accepted:,}")
    print(f"  Skipped (non-accepted / non-species): {skipped:,}")
    print(f"  Families with species: {len(species_by_family):,}")

    return {
        "version": "WCVP DwCA (sftp.kew.org)",
        "downloadedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "acceptedByFamily": species_by_family,
    }


def load_zip() -> bytes:
    if os.path.exists(LOCAL_ZIP):
        print(f"Using cached {LOCAL_ZIP}")
        with open(LOCAL_ZIP, "rb") as f:
            return f.read()
    raw = download_wcvp(WCVP_URL)
    os.makedirs(os.path.dirname(LOCAL_ZIP), exist_ok=True)
    with open(LOCAL_ZIP + ".tmp", "wb") as f:
        f.write(raw)
    os.replace(LOCAL_ZIP + ".tmp", LOCAL_ZIP)
    return raw


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    raw = load_zip()
    cache = build_cache(raw)

    print(f"\nWriting {OUT_PATH} ...")
    with open(OUT_PATH + ".tmp", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(OUT_PATH + ".tmp", OUT_PATH)

    fam_count = len(cache["acceptedByFamily"])
    sp_count = sum(len(v) for v in cache["acceptedByFamily"].values())
    print(f"Done — {fam_count} families, {sp_count:,} accepted species")
    return 0


if __name__ == "__main__":
    sys.exit(main())
