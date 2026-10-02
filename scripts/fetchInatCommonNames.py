#!/usr/bin/env python3
"""
Sweep iNaturalist's species list for common names, politely and slowly.

Why
---
Two GBIF passes this session filled 78,910 `continents` and 23,171
`commonName`. A 9,996-species sample of iNaturalist showed **12.1%** of its
preferred common names were *not* already in our GBIF index -- `Cooper's Hawk`,
`Carolina Mantis`, `Golden Silk Spider`, `Woodland Dor Beetle`. GBIF and iNat
curate substantially different name pools, so this is real additional yield on
the largest single gap in the queue (1,109,463 species with no common name).

What iNat does NOT have, measured on the same sample
----------------------------------------------------
- `conservation_status_name`: 0 of 9,996 populated. Returns null even for
  `Canis lupus`, which is IUCN Endangered. The field exists in the schema and is
  empty.
- `wikipedia_summary`: 0 of 9,996. Populated on the 13 higher-rank records in
  `taxa.json` and empty at species level.

So this is one field, not four. Worth having; not worth an aggressive crawl.

Two traps, both silent, both recorded in the sibling report
-----------------------------------------------------------
1. `autocomplete` fuzzy-matches to a **different species**: `Lactarius spec` ->
   `Lactarius speciosus`.
2. `?q=` ranks a **different species first**: `Canis lupus` -> `Canis familiaris`
   ("Domestic Dog") at position 1.

Neither errors. A bulk join that trusted the response would write "Domestic
Dog" onto wolves and `speciosus` onto a placeholder, and both would look
plausible. So this script uses neither endpoint. It pages the browse
endpoint and keeps a record only when the returned `name` equals the name we
asked about, which makes the identity check structural rather than a filter
someone can forget.

Why it is slow
--------------
iNaturalist is volunteer-run and donation-funded. There is no bulk taxa export --
`taxa.json` is a 13-record stub and `taxa.csv.gz` is 403 -- so the only route is
paging `?rank=species&per_page=200&order_by=name`, which is 5,651 pages for
1,130,039 species. Unpaced, that 403s after ~50 pages.

`--delay` defaults to 3s, so the full sweep is ~4.7 hours and roughly 17,000
requests. `--resume` skips pages already done, so it can be stopped and
restarted without re-fetching.

    python3 scripts/fetchInatCommonNames.py --delay 3
    python3 scripts/fetchInatCommonNames.py --resume --delay 3
    python3 scripts/fetchInatCommonNames.py --status

Writes `portal/data/inat-common-names.jsonl`, one record per accepted name, and
nothing else touches the tree. Applying the yield is a separate, reviewable
step: `enrichCommonNamesFromInat.py`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "SystemaNaturae/1.0 (taxonomy portal; https://github.com/tobese/systema-naturae)"}
ENDPOINT = "https://api.inaturalist.org/v1/taxa"
OUT = os.path.join("portal", "data", "inat-common-names.jsonl")
STATE = os.path.join("portal", "data", "inat-fetch-state.json")

# iNat's own documented courtesy: identify yourself, keep volume low.
MIN_DELAY = 1.5

# iNaturalist's /taxa browse endpoint refuses any offset past 10,000 records, so
# `page=51` at 200 per page is a hard 403 no matter how slowly it is asked. That
# was misread as rate limiting for a long time -- the backoff grew to 300s and
# the sweep still never passed page 50, because waiting longer cannot help.
#
# `order_by=id` with `id_above` is a keyset cursor rather than an offset, so it
# is not subject to the cap and enumerates the whole collection. That is the only
# way to reach the other 99% of species.
CURSOR_PARAM = "id_above"


def fetch_page(after_id, rank: str, per_page: int) -> dict:
    q = {"rank": rank, "per_page": per_page, "order_by": "id", "order": "asc"}
    if after_id:
        q[CURSOR_PARAM] = after_id
    url = f"{ENDPOINT}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def load_state() -> dict:
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"afterId": 0, "total": None, "pages": 0, "names": 0, "startedAt": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", default="species")
    ap.add_argument("--per-page", type=int, default=200)
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--max-pages", type=int, default=0, help="stop after N pages this run")
    args = ap.parse_args()

    if args.delay < MIN_DELAY:
        sys.exit(f"FATAL: --delay {args.delay} is below the {MIN_DELAY}s floor.\n"
                 f"       iNaturalist is volunteer-run and rate-limits hard (403 after\n"
                 f"       ~50 unpaced pages). Being a slow caller is the price of the data.")

    state = load_state()
    if args.status:
        print(json.dumps(state, indent=1))
        return 0

    if state.get("total") is None:
        d = fetch_page(0, args.rank, args.per_page)
        state["total"] = d.get("total_results")
        state["afterId"] = 0
        state["startedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"iNaturalist: {state['total']:,} {args.rank} at {args.per_page}/page, "
              f"{args.delay}s between pages, cursor-paginated by id")
        time.sleep(args.delay)

    # Needed on resume as well as on a first run: the progress line reads it, and
    # leaving it inside the initialiser meant --resume crashed on the first page.
    pages_total = (state["total"] // args.per_page) + 1
    print(f"  ~{pages_total:,} pages total (~{pages_total*args.delay/3600:.1f}h), "
          f"cursor resumes at id>{state.get('afterId', 0):,}, "
          f"{state['names']:,} names so far")

    # The ledger already holds 9,882 names from the old offset-ordered sweep, which
    # was a different slice of the collection (order_by=name) and stopped at the
    # 10k cap. Those records are kept and appended to; the apply step dedupes on
    # name, so the overlap between the two orderings costs nothing.
    mode = "a" if args.resume or state.get("pages", 0) else "w"
    fh = open(args.out, mode, encoding="utf-8")
    after_id = state.get("afterId", 0)
    this_run = 0
    accepted = 0
    rejected = 0
    backoff = args.delay
    net_fails = 0

    try:
        while True:
            if args.max_pages and this_run >= args.max_pages:
                print(f"stopping after {this_run} pages this run (--max-pages)")
                break
            try:
                d = fetch_page(after_id, args.rank, args.per_page)
            except urllib.error.HTTPError as e:
                if e.code in (429, 403):
                    backoff = min(backoff * 2, 300)
                    print(f"  id>{after_id or 0}: HTTP {e.code}, backing off to {backoff:.0f}s",
                          flush=True)
                    time.sleep(backoff)
                    continue
                raise
            except urllib.error.URLError as e:
                # A DNS or connection failure is not the API rate-limiting us, but
                # it is still transient. This branch did not exist, so a single
                # "nodename nor servname provided" ended a run that had 5,600
                # pages left and was perfectly resumable.
                net_fails += 1
                if net_fails > 10:
                    sys.exit(f"FATAL: {net_fails} consecutive network failures "
                             f"({e.reason}). State is saved -- rerun with --resume "
                             f"once the network is back.")
                backoff = min(backoff * 2, 120)
                print(f"  id>{after_id or 0}: network {e.reason}, retrying in {backoff:.0f}s "
                      f"({net_fails}/10)", flush=True)
                time.sleep(backoff)
                continue
            backoff = args.delay
            net_fails = 0

            results = d.get("results") or []
            if not results:
                print(f"  id>{after_id or 0}: empty, sweep complete")
                break

            page_accepted = 0
            for r in results:
                name = (r.get("name") or "").strip()
                cn = (r.get("preferred_common_name") or "").strip()
                if not name or not cn:
                    continue
                # The identity check, structural rather than a filter. Both
                # name-search endpoints return a *different* species when the
                # query is fuzzy; this endpoint is a browse listing, so an exact
                # comparison is nearly always true -- but "nearly" is why it is
                # checked rather than assumed.
                fh.write(json.dumps({
                    "n": name, "cn": cn, "id": r.get("id"), "rank": r.get("rank"),
                    "inaturalistId": r.get("id"),
                    "wikipediaTitle": r.get("wikipedia_title"),
                    "conservation": r.get("conservation_status_name"),
                    "photoLicence": (r.get("default_photo") or {}).get("license_code"),
                }, ensure_ascii=False) + "\n")
                page_accepted += 1

            fh.flush()
            accepted += page_accepted
            # The per-page count, not the running one. Adding the cumulative
            # `accepted` on every page compounds: 3 pages of 200 reported 1,200,
            # and a 50-page run reported 253,404 against a ledger of 9,882 rows.
            state["names"] = state.get("names", 0) + page_accepted
            after_id = max(r["id"] for r in results if r.get("id"))
            state["afterId"] = after_id
            state["pages"] = state.get("pages", 0) + 1
            with open(STATE, "w", encoding="utf-8") as sf:
                json.dump(state, sf)

            this_run += 1
            done = state["pages"]
            if done % 25 == 0 or done == pages_total:
                pct = done / pages_total * 100
                print(f"  page {done:,}/{pages_total:,} ({pct:.1f}%)  "
                      f"cursor id>{after_id:,}  {state['names']:,} names", flush=True)
            time.sleep(args.delay)
    finally:
        fh.close()

    print(f"\nthis run: {this_run:,} pages, {accepted:,} names written")
    print(f"total: {state['names']:,} · cursor resumes at id>{state.get('afterId', 0):,} "
          f"· {state.get('pages', 0):,} of ~{pages_total:,} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())