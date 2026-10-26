#!/usr/bin/env python3
"""List openly-licensed ChecklistBank datasets we do not hold, biggest first.

`checklistbankShelf.py` prints a human table and cross-references the manifest,
which is the right tool for reading the shelf. This one exists for the case
that comes next -- deciding what to download -- and answers it in a form a shell
can loop over:

  * machine-readable, one `--key` per line, so `fetchBatch.sh` can take it
  * open licences only (CC0 / CC BY), because anything NC needs a policy call we
    have already had twice and declined twice
  * dropped: datasets whose *title* says they are another dataset we hold. COL
    republishes itself as ~15 annual releases and NCBI/GTDB appear as COL
    checklists; importing those is a duplicate import wearing a new key.

    python3 scripts/triageNext.py --limit 25
    python3 scripts/triageNext.py --group lepidoptera --limit 10
    python3 scripts/triageNext.py --keys-only
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import MANIFEST  # noqa: E402
import sourceQueue as SQ  # noqa: E402

API = "https://api.checklistbank.org/dataset"
UA = "systema-naturae-triage/1.0 (+https://github.com/tobese/systema-naturae)"
OPEN = ("cc0", "cc by", "cc-by")

# Titles that are a re-issue of something already registered. Matched on the
# normalised title, so "Catalogue of Life 2019" and "Catalogue of Life" both hit.
REISSUE = re.compile(
    r"catalogue of life|species 2000|ncbi taxonomy|genome taxonomy|"
    r"index fungorum|test dataset|annual checklist", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _doi_in(citation):
    """DOI out of a free-text citation string, or "" if there is not one."""
    m = re.search(r"10\.\d{4,9}/\S+", citation or "")
    return m.group(0) if m else ""


def held_keys():
    """Every way the manifest can claim a dataset: slug key, DOI, and title
    -- title as a token set (`SQ._title_tokens`), not an exact normalised
    string: a stricter exact match let "South African National Plant
    Checklist (SANPC)" (ChecklistBank key 312236) through as "new" past an
    already-assessed "South African National Plant Checklist" (key 312166),
    found 2026-10-25 widening this script to --all-types. Reusing
    `sourceQueue.py`'s matcher (added the same day for the mirror-image
    problem -- `add` registering a duplicate under a new key) rather than
    keeping two slightly different title-matching implementations."""
    keys, dois, titles = set(), set(), []
    try:
        src = json.load(open(MANIFEST, encoding="utf-8")).get("sources", {})
    except (OSError, ValueError):
        sys.exit(f"FATAL: {MANIFEST} unreadable — is the sources volume mounted?")
    for slug, rec in src.items():
        m = re.match(r"checklistbank-(\d+)$", slug)
        if m:
            keys.add(int(m.group(1)))
        blob = " ".join(str(rec.get(f) or "") for f in ("identifier", "url", "title"))
        for doi in re.findall(r"10\.\d{4,9}/\S+", blob):
            dois.add(norm(doi.rstrip(".,;)")))
        if rec.get("title"):
            titles.append((rec["title"], SQ._title_tokens(rec["title"])))
    return keys, dois, titles


def queue_keys() -> set[int]:
    """Every checklistbank key already registered in the source queue
    (scripts/sourceQueue.py), at any stage — so refill doesn't keep
    handing back keys we've queued."""
    out = set()
    for slug in SQ.read_store():
        m = re.match(r"checklistbank-(\d+)$", slug)
        if m:
            out.add(int(m.group(1)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--group", default="", help="taxonomicGroupScope filter")
    ap.add_argument("--min-size", type=int, default=200,
                     help="floor on a dataset's own `size` field (default 200 "
                          "-- ChecklistBank's 65,480-dataset catalog is 95%% "
                          "single-paper `article`-type records this project "
                          "has no use for; 0 scans the whole thing)")
    ap.add_argument("--all-types", action="store_true",
                     help="also list datasets outside type=taxonomic. "
                          "ChecklistBank's dataset `type` field is mostly a "
                          "publishing/workflow tag, not a reliable signal for "
                          "'is this a checklist' -- found 2026-10-25 via "
                          "fna-accepted-names (ChecklistBank key 197537), a "
                          "genuine 27k-name US flora checklist filed as "
                          "`article`, already taken despite this script never "
                          "surfacing it. A size>=200 scan of every non-"
                          "taxonomic type the same day found 1,607 open-"
                          "licence datasets this script's old hardcoded "
                          "`type=taxonomic` filter had never once shown --  "
                          "mostly real regional/national checklists and red "
                          "lists (Dutch Caribbean Species Register, Korean "
                          "Peninsula Flora, Swedish Red List, DAISIE...), not "
                          "noise. Off by default because `type=taxonomic` "
                          "alone is already a fast, clean 480-dataset shelf "
                          "and most callers want that; turn this on "
                          "deliberately; still subject to the held/licence/"
                          "reissue filters below.")
    ap.add_argument("--keys-only", action="store_true")
    args = ap.parse_args()

    keys, dois, titles = held_keys()
    # Never re-triagen an already-queued key, whatever its terminal stage.
    keys |= queue_keys()

    rows = []
    if args.all_types:
        # Paginate the whole catalog, sorted largest-first, and stop once a
        # page's smallest row drops below --min-size (sort is descending, so
        # nothing larger remains past that point).
        offset = 0
        page = 1000
        while True:
            url = f"{API}?limit={page}&offset={offset}&sortBy=size"
            if args.group:
                url += "&taxonomicGroupScope=" + urllib.parse.quote(args.group)
            doc = get(url)
            batch = doc.get("result") or []
            if not batch:
                break
            rows.extend(batch)
            offset += page
            if offset >= (doc.get("total") or 0):
                break
            if (batch[-1].get("size") or 0) < args.min_size:
                break
    else:
        url = f"{API}?type=taxonomic&limit=1000"
        if args.group:
            url += "&taxonomicGroupScope=" + urllib.parse.quote(args.group)
        doc = get(url)
        rows = doc.get("result") or []

    out = []
    for d in rows:
        key = d.get("key")
        size = d.get("size") or 0
        # The listing spells it `license`, not `licence`. Reading `licence`
        # returns None for all 479 rows, every one of them fails the open
        # filter, and the tool reports "0 candidates" with no hint why.
        lic = (d.get("license") or d.get("licence") or "").lower()
        title = d.get("title") or ""
        if key in keys or size < args.min_size:
            continue
        if not lic.startswith(OPEN):
            continue
        # "cc by-nc" and "cc by-nc-sa" both start with "cc by", so the prefix
        # check above alone lets non-commercial licences through -- exactly
        # the policy question this project has declined twice already (see
        # docs/dataset-inbox.md). Split on word boundaries including the
        # hyphen so "by-nc" is seen as two tokens, not one that fails a
        # plain substring test differently than "by nc" would.
        if "nc" in re.split(r"[\s-]+", lic):
            continue
        # `citation` is a string here, not an object with a doi field.
        doi = norm(d.get("doi") or _doi_in(d.get("citation")))
        if doi and doi in dois:
            continue
        if SQ._title_overlap_match(SQ._title_tokens(title), titles) or REISSUE.search(title):
            continue
        out.append((size, key, lic, title, d.get("alias") or ""))

    out.sort(reverse=True)
    out = out[:args.limit]

    if args.keys_only:
        for _size, key, _lic, _title, _alias in out:
            print(key)
        return 0

    print(f"{'size':>11}  {'key':>7}  {'licence':<12}  title")
    for size, key, lic, title, alias in out:
        name = f"{title} ({alias})" if alias and alias.lower() not in title.lower() else title
        print(f"{size:>11,}  {key:>7}  {lic:<12}  {name[:70]}")
    scanned = f"{len(rows)} scanned above --min-size {args.min_size}" if args.all_types \
        else f"{len(rows)} on the shelf"
    print(f"\n{len(out)} candidates ({scanned}); run with --keys-only to feed fetchBatch.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
