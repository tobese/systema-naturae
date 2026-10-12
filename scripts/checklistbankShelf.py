#!/usr/bin/env python3
"""What is on the ChecklistBank shelf, and what of it do we not already hold?

ChecklistBank is where new sources get picked from, and its listing is worth
reading properly rather than one dataset at a time. The endpoint that serves the
data is api.checklistbank.org; www.checklistbank.org answers a 307 into a GoAway
bot challenge and returns no data.

Two things about the filters, because the obvious query is the wrong one:

    origin=project&origin=external   ->  65,225   (everything; the two origins
                                                  are alternatives, not a
                                                  conjunction, so this is the
                                                  65k firehose)
    origin=project                   ->       4   (the curated set: COL, COL
                                                  Lepidoptera, Moths of the
                                                  World tutorial, Chrysididae)
    type=taxonomic                   ->     475   (the usable shelf)
    origin=external                  ->  65,221   (everything anyone ever pushed)

475 is the number that matters for this project. Two fields make the listing
triageable rather than a scroll: `size` is the name-usage count (COL 5,446,323,
COLH 2,844 -- which is how the 2019 COL Hierarchy remnant gave itself away), and
`taxonomicGroupScope` is a list of group tags per dataset, so "which Lepidoptera
sources exist that we do not hold" is a filter rather than a search.

Matches our sources by DOI where we have one, then by ChecklistBank key, then by
normalised title. A title match is weaker and is reported separately.

    python3 scripts/checklistbankShelf.py
    python3 scripts/checklistbankShelf.py --group lepidoptera
"""
import argparse
import collections
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from sources import MANIFEST

API = "https://api.checklistbank.org/dataset"
KNOWN_KEYS = {
    3: "catalogue-of-life", 1000: "COL Hierarchy (superseded)", 1005: "craneflies",
    1008: "reptile-db", 1010: "FishBase (offered, declined)",
    1011: "flow", 1012: "Glomeromycota (licence unchecked)",
    1015: "ildis", 1018: "LepIndex (offered)", 1019: "moss-tropicos",
    314569: "wikidata-species",
}


def get(url):
    with urllib.request.urlopen(url, timeout=90) as fh:
        return json.load(fh)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def ours():
    """(dois, titles, slugs) from the manifest, for matching."""
    try:
        d = json.load(open(MANIFEST, encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"FATAL: {MANIFEST} not found -- is the volume mounted?")
    dois, titles = set(), {}
    for slug, rec in d["sources"].items():
        blob = " ".join(str(rec.get(k) or "") for k in
                        ("identifier", "title", "url", "took"))
        for m in re.findall(r"10\.\d{4,9}/\S+", blob):
            dois.add(m.rstrip(".,);").lower())
        titles[norm(rec.get("title"))] = slug
    return dois, titles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="",
                    help="only datasets whose taxonomicGroupScope contains this")
    ap.add_argument("--min-size", type=int, default=0)
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    dois, titles = ours()
    print(f"  our manifest: {len(titles)} sources, {len(dois)} DOIs")

    rows, offset = [], 0
    while True:
        d = get(f"{API}?type=taxonomic&limit=100&offset={offset}")
        res = d.get("result") or []
        if not res:
            break
        rows.extend(res)
        offset += 100
        if offset >= (d.get("total") or 0):
            break
    print(f"  ChecklistBank taxonomic datasets: {len(rows):,}")

    def held(r):
        blob = " ".join(str(r.get(k) or "") for k in ("doi", "url", "title"))
        for m in re.findall(r"10\.\d{4,9}/\S+", blob):
            if m.rstrip(".,);").lower() in dois:
                return "doi"
        if r.get("key") in KNOWN_KEYS:
            return "key"
        return None

    unheld, matched = [], collections.Counter()
    for r in rows:
        why = held(r)
        if why:
            matched[why] += 1
            continue
        if norm(r.get("title")) in titles:
            matched["title"] += 1
            continue
        unheld.append(r)

    print(f"  matched to something we hold: {sum(matched.values()):,} "
          f"({dict(matched)})")
    print(f"  not matched: {len(unheld):,}")

    if args.group:
        g = args.group.lower()
        unheld = [r for r in unheld
                  if any(g in (x or "").lower()
                         for x in (r.get("taxonomicGroupScope") or []))]
        print(f"  ...of which tag '{args.group}': {len(unheld):,}")
    if args.min_size:
        unheld = [r for r in unheld if (r.get("size") or 0) >= args.min_size]
        print(f"  ...with at least {args.min_size:,} name usages: {len(unheld):,}")

    # Monthly releases of one source are not N sources. ChecklistBank keeps
    # every COL build, so the shelf is dominated by eighteen "Catalogue of Life"
    # rows of 5-9M name usages each, and all of them are the source we already
    # hold as key 3. Collapse by normalised title and show the largest plus how
    # many other vintages exist, which is the only part that tells you anything.
    groups_ = collections.defaultdict(list)
    for r in unheld:
        groups_[norm(r.get("title")) or f"key{r.get('key')}"].append(r)
    print(f"  distinct sources after collapsing repeats: {len(groups_):,}")

    rows_out = []
    for _k, rs in groups_.items():
        rs.sort(key=lambda r: -(r.get("size") or 0))
        rows_out.append((rs[0], len(rs)))
    rows_out.sort(key=lambda t: -(t[0].get("size") or 0))

    print(f"\n  {'size':>10}  {'key':>6}  {'lic':10s} {'vintage':12s} "
          f"{'also':>5}  title")
    for r, n in rows_out[:args.limit]:
        print(f"  {r.get('size') or 0:>10,}  {r.get('key'):>6}  "
              f"{str(r.get('license'))[:9]:10s} "
              f"{str(r.get('version') or '')[:11]:12s} "
              f"{(str(n - 1) + ' more') if n > 1 else '':>5}  "
              f"{str(r.get('title'))[:46]}")
        groups = ",".join((r.get("taxonomicGroupScope") or [])[:5])
        if groups:
            print(f"{'':>46}{groups}")
    return 0


if __name__ == "__main__":
    sys.exit(main())