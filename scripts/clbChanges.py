#!/usr/bin/env python3
"""What changed on ChecklistBank since we last looked: new datasets, and
datasets re-imported (a newer version) -- especially ones we hold.

ChecklistBank has no documented change feed (its created/modified filters are
ignored and the importer log is closed), but its dataset list sorts newest
first: `sortBy=created` for datasets added, `sortBy=imported` for datasets
re-imported. Paging each until the timestamp drops below our last check costs
a few requests instead of re-reading 65k records.

Records only; changes nothing in the queue or the tree:

  <sources>/clb-changes/changes.jsonl  one line per change: {at, kind:
                                       new|updated, key, title, created|imported,
                                       issued, held}
  <sources>/clb-changes/state.json     when we last looked

New datasets reach the queue the usual way (triageNext.py's open-licence and
size rules, on the next refill); an updated dataset we hold is a
"newer version available" for the measured refetch -- see
sourceVersions.py and docs/source-versions.md.

    python3 scripts/clbChanges.py                    # since the last run
    python3 scripts/clbChanges.py --since 2026-10-29
    python3 scripts/clbChanges.py --min-interval-hours 6   # pipelineOrchestrator's side tasks
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.checklistbank.org/dataset"
UA = "systema-naturae-clb-changes/0.1"
# On the sources volume, not in the repo: derived, and both Macie and q-bert
# run it from their side tasks, so a repo file would be appended on two
# machines at once.
LOG = os.path.join(sources.ROOT, "clb-changes", "changes.jsonl")
STATE = os.path.join(sources.ROOT, "clb-changes", "state.json")
PAGE = 100
MAX_PAGES = 50  # 5,000 records: a backstop if a timestamp is missing


def page(sort, offset):
    url = f"{API}?{urllib.parse.urlencode({'sortBy': sort, 'limit': PAGE, 'offset': offset})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get("result") or []
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def newer_than(sort, field, since):
    """Records whose `field` is after `since`, newest first, until older."""
    out = []
    for n in range(MAX_PAGES):
        rows = page(sort, n * PAGE)
        if not rows:
            break
        for r in rows:
            if (r.get(field) or "") <= since:
                return out
            out.append(r)
        time.sleep(0.3)
    return out


def held_keys():
    keys = set()
    try:
        manifest = json.load(open(os.path.join(sources.ROOT, "manifest.json")))["sources"]
        keys |= {int(m.group(1)) for k in manifest for m in [re.match(r"checklistbank-(\d+)$", k)] if m}
    except (OSError, ValueError, KeyError):
        pass
    qdir = os.path.join(ROOT, "data", "source-queue")
    for f in os.listdir(qdir) if os.path.isdir(qdir) else []:
        m = re.match(r"checklistbank-(\d+)\.json$", f)
        if m:
            keys.add(int(m.group(1)))
    return keys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="", help="ISO date/time; default: the last run")
    ap.add_argument("--min-interval-hours", type=float, default=0,
                    help="do nothing if the last run was more recent (for the "
                         "pipeline's side tasks, which run every few minutes)")
    args = ap.parse_args()

    since = args.since
    if not since and os.path.exists(STATE):
        since = json.load(open(STATE)).get("lastChecked", "")
        if args.min_interval_hours and since:
            age = datetime.datetime.now() - datetime.datetime.fromisoformat(since)
            if age < datetime.timedelta(hours=args.min_interval_hours):
                return 0
    if not since:
        since = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        print(f"  no previous run; looking back a week, to {since}")
    started = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    held = held_keys()

    new = newer_than("created", "created", since)
    updated = newer_than("imported", "imported", since)
    created_keys = {r["key"] for r in new}

    lines = []
    for r in new:
        lines.append({"at": started, "kind": "new", "key": r["key"], "title": r.get("title"),
                      "created": r.get("created"), "issued": r.get("issued"),
                      "licence": r.get("license"), "held": r["key"] in held})
    for r in updated:
        if r["key"] in created_keys:
            continue  # its first import, already logged as new
        lines.append({"at": started, "kind": "updated", "key": r["key"], "title": r.get("title"),
                      "imported": r.get("imported"), "issued": r.get("issued"),
                      "held": r["key"] in held})
    if lines:
        with open(LOG, "a", encoding="utf-8") as fh:
            for l in lines:
                fh.write(json.dumps(l, ensure_ascii=False) + "\n")
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump({"lastChecked": started, "previous": since}, fh, indent=1)
        fh.write("\n")

    held_updates = [l for l in lines if l["kind"] == "updated" and l["held"]]
    print(f"  since {since}: {len(new)} new datasets, "
          f"{len(lines) - len(new)} re-imported ({len(held_updates)} of them held)")
    for l in held_updates[:20]:
        print(f"    newer version of a held source: checklistbank-{l['key']}  "
              f"{(l['title'] or '')[:60]}  (issued {l.get('issued')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
