#!/usr/bin/env python3
"""Merge the Commons credits cache into the image sidecar.

`wiki-images.json` holds a bare Commons filename for every portrait, and the
filename is not a credit. Wikidata's P18 gives the file and nothing else, so
before this the portal displayed ~162,000 images with no author and no licence --
which for CC BY and BY-SA, which most of them are, is the licence condition
rather than a cosmetic gap.

backfillCommonsCredits.py resolves each filename to its Artist and licence from
the Commons API into a JSONL cache. This merges that cache, and deliberately:

  - never overwrites an existing imageArtist/imageLicense
  - skips NC and ND outright, so a non-commercial portrait cannot enter through
    the back door even though 100k of the existing ones predate any licence check
  - records the uploader as the artist only when there is no Artist field at all,
    since an uploader is a poor substitute but better than nothing

Usage:
    python3 scripts/applyCommonsCredits.py            # dry run
    python3 scripts/applyCommonsCredits.py --apply
"""
import argparse
import html
import json
import os
import re
import sys
import unicodedata

SIDECAR = os.path.join("shared", "data", "wiki-images.json")
CACHE = os.path.join("portal", "data", "commons-credits.jsonl")

NC_ND = re.compile(r"\b(NC|ND)\b|-nc|-nd", re.I)
ENTITY = re.compile(r"&(?:quot|amp|apos|lt|gt|#\d+|#x[0-9a-fA-F]+);")


def norm(s: str) -> str:
    """A key both sides agree on.

    Joining on the raw filename matched only 164,181 of 175,978, and the misses
    went both ways: the API returns `title` HTML-escaped in some responses, and
    otherwise normalises underscores to spaces and Unicode to NFC. Comparing
    decoded, NFC, space-folded, casefolded text matches 175,777 instead -- the
    remaining 201 are titles Commons does not have.
    """
    s = html.unescape(s or "")
    s = unicodedata.normalize("NFC", s).replace("_", " ")
    return re.sub(r"\s+", " ", s).strip().casefold()


def licence_url(row) -> str:
    url = (row.get("licenceUrl") or "").strip()
    if url:
        return url
    # Fall back to the short name when Commons omits the URL, so the panel can
    # still show something rather than an empty credit.
    short = (row.get("licence") or "").strip()
    return short


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sidecar", default=SIDECAR)
    ap.add_argument("--cache", default=CACHE)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.cache):
        sys.exit(f"FATAL: {args.cache} not found. Run backfillCommonsCredits.py first.")

    credits: dict[str, dict] = {}
    collisions = 0
    with open(args.cache, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            f = r.get("file")
            if not f:
                continue
            k = norm(f)
            if k in credits:
                collisions += 1
                continue
            credits[k] = r
    print(f"cache rows: {len(credits):,} distinct keys ({collisions:,} collided and were dropped)")

    with open(args.sidecar, encoding="utf-8") as fh:
        images = json.load(fh)

    tally = {"matched": 0, "already": 0, "filled": 0, "no-credit": 0,
             "blocked-nc-nd": 0, "no-file": 0, "filename-repaired": 0}
    for entry in images.values():
        fn = entry.get("image")
        if not fn:
            continue
        # 59 filenames carry HTML entities from however they were written upstream,
        # and useWikiImages percent-encodes them straight into a Special:FilePath
        # URL, so those portraits have always 404'd. Decoding fixes the image and
        # lets the credit join.
        if ENTITY.search(fn):
            tally["filename-repaired"] += 1
            if args.apply:
                entry["image"] = html.unescape(fn)
            fn = html.unescape(fn)
        row = credits.get(norm(fn))
        if not row:
            tally["no-file"] += 1
            continue
        tally["matched"] += 1
        if entry.get("imageArtist") or entry.get("imageLicense"):
            tally["already"] += 1
            continue
        lic = row.get("licence") or ""
        if not lic or row.get("missing"):
            tally["no-credit"] += 1
            continue
        if NC_ND.search(lic) or NC_ND.search(row.get("licenceUrl") or ""):
            tally["blocked-nc-nd"] += 1
            continue
        artist = row.get("artist") or ""
        if not artist:
            # An uploader is not the author, but an unattributed CC BY image is
            # worse than one naming whoever at least put it there.
            artist = row.get("uploader") or ""
            if artist:
                artist += " (uploader)"
        if not artist:
            tally["no-credit"] += 1
            continue
        entry["imageArtist"] = artist
        entry["imageLicense"] = licence_url(row)
        tally["filled"] += 1

    print("=" * 66)
    for k in ("matched", "already", "filled", "no-credit", "blocked-nc-nd",
              "no-file", "filename-repaired"):
        print(f"{k:<24}{tally[k]:>9,}")

    withartist = sum(1 for v in images.values() if v.get("imageArtist"))
    print(f"\nsidecar entries with an artist: {withartist:,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    with open(args.sidecar, "w", encoding="utf-8") as fh:
        json.dump(images, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"  wrote {args.sidecar} ({os.path.getsize(args.sidecar)/1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
