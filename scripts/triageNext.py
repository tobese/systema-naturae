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
    """Every way the manifest can claim a dataset: slug key, DOI, title."""
    keys, dois, titles = set(), set(), set()
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
            titles.add(norm(rec["title"]))
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
    ap.add_argument("--min-size", type=int, default=0)
    ap.add_argument("--keys-only", action="store_true")
    args = ap.parse_args()

    keys, dois, titles = held_keys()
    # Never re-triagen an already-queued key, whatever its terminal stage.
    keys |= queue_keys()
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
        if norm(title) in titles or REISSUE.search(title):
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
    print(f"\n{len(out)} candidates (of {len(rows)} on the shelf); run with --keys-only to feed fetchBatch.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
