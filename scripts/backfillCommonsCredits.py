#!/usr/bin/env python3
"""Backfill author and licence for the Commons portraits we already hold.

`wiki-images.json` carries a bare Commons filename for every Wikidata P18
portrait, and Wikidata gives the file but not its credit. So the portal shows
161,737 images with no attribution at all, which is a licence problem rather than
a cosmetic one: most are CC BY or BY-SA, both of which require naming the author.

The author is one API call away. `prop=imageinfo` with
`iiextmetadatafilter=Artist|LicenseShortName|LicenseUrl` returns exactly those
three fields and nothing else, which matters across 3,520 requests -- the
unfiltered extmetadata for a Commons file runs to several kilobytes.

Politeness, because this is 3,520 requests against volunteer-run infrastructure:
  - a descriptive User-Agent naming the project and a contact route, which
    Wikimedia requires and which generic agents get throttled or blocked for
  - four workers, so ~4 requests/second, not a burst
  - a resumable JSONL cache, so a failure costs one batch and not the run

Output is a cache, not the sidecar. scripts/applyCommonsCredits.py merges it, so
the fetch can be re-run without touching data.

Usage:
    python3 scripts/backfillCommonsCredits.py            # fetch, resumable
    python3 scripts/backfillCommonsCredits.py --status
"""
import argparse
import html
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks for a descriptive agent with a contact route. A generic one gets
# throttled or refused outright.
UA = ("SystemaNaturae/1.0 (taxonomy portal; https://github.com/tobese/systema-naturae) "
      "Python-urllib/3")
SIDECAR = os.path.join("shared", "data", "wiki-images.json")
CACHE = os.path.join("portal", "data", "commons-credits.jsonl")
BATCH = 50
WORKERS = 4

TAGS = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
# Creator templates that survive tag-stripping and mean nothing to a reader.
TEMPLATE = re.compile(r"\{\{[^}]*\}\}|\[\[(?:File|Image|Category):[^\]]*\]\]", re.I)

_lock = threading.Lock()
_done = 0
_written = 0
_missing = 0


def clean_artist(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(TAGS.sub(" ", raw))
    text = TEMPLATE.sub(" ", text)
    text = SPACE.sub(" ", text).strip(" ,;|")
    return text[:120]


def query(titles: list[str]) -> dict:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "1",
        "prop": "imageinfo", "iiprop": "extmetadata|user",
        "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
        "titles": "|".join("File:" + t for t in titles),
    })
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def worker(batch: list[str], out, state) -> None:
    global _done, _written, _missing
    for attempt in range(4):
        try:
            d = query(batch)
            break
        except Exception:
            if attempt == 3:
                with _lock:
                    _done += len(batch)
                print(f"  WARN gave up on {len(batch)} titles", flush=True)
                return
            time.sleep(2 ** attempt + random.random())
    else:
        return

    rows = []
    for p in (d.get("query", {}).get("pages") or {}).values():
        # The API returns `title` HTML-escaped in some responses, so a file
        # called '" Flor do cacto". JPG.jpg' comes back as
        # '&quot; Flor do cacto&quot;. JPG.jpg'. Storing that verbatim left
        # 11,797 titles that could never join back to the sidecar, and the
        # status counter then sat still however many passes were run.
        title = html.unescape((p.get("title") or "").removeprefix("File:"))
        if "missing" in p:
            rows.append({"file": title, "missing": True})
            continue
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        rows.append({
            "file": title,
            "artist": clean_artist((em.get("Artist") or {}).get("value", "")),
            "licence": (em.get("LicenseShortName") or {}).get("value") or "",
            "licenceUrl": (em.get("LicenseUrl") or {}).get("value") or "",
            "uploader": ii.get("user") or "",
        })

    with _lock:
        for r in rows:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            _written += 1
            if r.get("missing"):
                _missing += 1
        out.flush()
        _done += len(batch)
        pct = _done / state["total_titles"] * 100
        if _done % 2000 < BATCH:
            print(f"  {_done:,}/{state['total_titles']:,} ({pct:.1f}%)  "
                  f"{_written:,} resolved, {_missing:,} missing", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sidecar", default=SIDECAR)
    ap.add_argument("--cache", default=CACHE)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    with open(args.sidecar, encoding="utf-8") as fh:
        side = json.load(fh)
    wanted = sorted({v["image"] for v in side.values() if v.get("image")})

    have = set()
    if os.path.exists(args.cache):
        with open(args.cache, encoding="utf-8") as fh:
            for line in fh:
                try:
                    have.add(json.loads(line)["file"])
                except Exception:
                    pass
    todo = [t for t in wanted if t not in have]
    if args.status:
        print(f"distinct files   {len(wanted):,}")
        print(f"already resolved {len(have):,}")
        print(f"remaining        {len(todo):,}  ({len(todo)//BATCH:,} batches)")
        return 0
    if not todo:
        print("nothing to do")
        return 0
    if args.limit:
        todo = todo[:args.limit]

    print(f"resolving {len(todo):,} titles in {len(todo)//BATCH:,} batches "
          f"at {BATCH}/request, {WORKERS} workers")
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    started = time.time()
    os.makedirs(os.path.dirname(args.cache) or ".", exist_ok=True)
    with open(args.cache, "a", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            list(ex.map(lambda b: worker(b, out, {"total_titles": len(todo)}), batches))
    took = time.time() - started
    print(f"\n{_written:,} titles resolved ({_missing:,} missing) in {took/60:.1f} min")
    print(f"cache: {args.cache} ({os.path.getsize(args.cache)/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
