#!/usr/bin/env python3
"""Is there a newer Catalogue of Life release than the one we hold?

COL turned out not to be an annual thing in 2026: ChecklistBank shows a new
release *and* a new xrelease (extended -- more provisional/extra names) for
project key 3 roughly every month (COL26.2 through COL26.9 so far), not once
a year. The base release we actually imported (`scripts/buildColIdMap.py`,
`sourcesManifest.py`'s "catalogue-of-life" entry) is key 316321 / COL26.9,
issued 2026-09-11 -- which was the newest available when it was downloaded
(2026-10-03). This just checks whether that is still true, and what the
xrelease sibling looks like, rather than assuming an annual cadence and
checking back next year.

    python3 scripts/checkColRelease.py

Exit code 0 if HELD_RELEASE_KEY/HELD_XRELEASE_KEY are still the newest
release/xrelease ChecklistBank has for project key 3; 1 if either has moved
on, so this is usable as a cron/check-script gate, not just a report.
"""
import json
import sys
import urllib.request

API = "https://api.checklistbank.org/dataset"

# Update these two after taking a newer release. See sourcesManifest.py's
# "catalogue-of-life" entry for the applied-state record; this is just the
# comparison baseline for "is there something newer yet".
HELD_RELEASE_KEY = 316321   # COL26.9, base, issued 2026-09-11
HELD_XRELEASE_KEY = 316441  # COL26.9 XR, issued 2026-09-25 -- NOT yet imported


def get(url):
    with urllib.request.urlopen(url, timeout=90) as fh:
        return json.load(fh)


def col_releases():
    """Every release/xrelease of project key 3, newest first."""
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
    releases = [r for r in rows if r.get("sourceKey") == 3
                and r.get("origin") in ("release", "xrelease")]
    releases.sort(key=lambda r: r.get("issued") or "", reverse=True)
    return releases


def main() -> int:
    releases = col_releases()
    latest_base = next((r for r in releases if r.get("origin") == "release"), None)
    latest_xr = next((r for r in releases if r.get("origin") == "xrelease"), None)

    print("  held:")
    print(f"    base      key {HELD_RELEASE_KEY:>7}")
    print(f"    xrelease  key {HELD_XRELEASE_KEY:>7}  (not yet imported)")
    print("  latest on ChecklistBank:")
    if latest_base:
        print(f"    base      key {latest_base['key']:>7}  "
              f"{latest_base.get('alias')}  issued {latest_base.get('issued')}  "
              f"{latest_base.get('size') or 0:,} name usages")
    if latest_xr:
        print(f"    xrelease  key {latest_xr['key']:>7}  "
              f"{latest_xr.get('alias')}  issued {latest_xr.get('issued')}  "
              f"{latest_xr.get('size') or 0:,} name usages")

    newer = (latest_base and latest_base["key"] != HELD_RELEASE_KEY) or \
            (latest_xr and latest_xr["key"] != HELD_XRELEASE_KEY)
    if newer:
        print("\n  ! a newer COL release exists -- re-run buildColIdMap.py / "
              "importColChecklist.py against it and update HELD_RELEASE_KEY "
              "/ HELD_XRELEASE_KEY here plus sourcesManifest.py's entry")
        return 1
    print("\n  up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
