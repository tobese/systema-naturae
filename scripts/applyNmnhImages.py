#!/usr/bin/env python3
"""Add Smithsonian NMNH specimen photographs to the image sidecar.

The NMNH harvest (Zenodo 20174554, CC-BY 4.0 at the record level) carries 453,486
media rows whose `UsageTerms` is CC0 on every one, each with an `accessURI` and a
302 to ids.si.edu. Under CC0 the attribution requirement is waived, so `Owner`
being empty on all 453,486 rows is not a gap.

These are absolute URLs on a Smithsonian host, not Commons filenames, so they
cannot go in `wiki-images.json`'s `image` field: `useWikiImages` turns that field
into a `Special:FilePath` URL and would build a broken Commons link. They go in
`imageUrl`, which the hook prefers and which does not require a Wikidata qid.

Only species with no image at all are filled. An existing Wikidata P18 portrait
is not displaced by a specimen photograph.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import work_file as _wf  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # noqa: E402
from canonicalNames import _load as load_canonical  # noqa: E402

SIDECAR = os.path.join("shared", "data", "wiki-images.json")
NMNH = _wf("nmnh", "nmnh_media.json")
# h= is the delivery service's height parameter; 800 keeps the panel's payload
# sane next to the 600px Commons thumbnails useWikiImages asks for.
HEIGHT = 800


def retarget(uri: str) -> str:
    if "collections.nmnh.si.edu/media/" in uri and "h=" in uri:
        return uri.split("&h=")[0] + f"&h={HEIGHT}"
    return uri


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=NMNH)
    ap.add_argument("--sidecar", default=SIDECAR)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"FATAL: {args.source} not found. Unpack the NMNH harvest first:\n"
                 f"       curl -L 'https://zenodo.org/records/20174554/files/nmnh_images.tar.gz?download=1'")

    canon = load_canonical()
    with open(args.source, encoding="utf-8") as fh:
        raw = json.load(fh)

    # EOL's names carry authorities ("Pyrrhura frontalis frontalis (vieillot,
    # 1818)"), so the source side needs canonicalising too.
    by_canon: dict[str, str] = {}
    exact: dict[str, str] = {}
    for name, rec in raw.items():
        uri = retarget(rec["uri"])
        exact[name.lower()] = uri
        c = canon.get(name.lower())
        by_canon[c or name.lower()] = uri
    print(f"NMNH source names: {len(raw):,}  ({len(by_canon):,} after canonicalising)")

    with open(args.sidecar, encoding="utf-8") as fh:
        images = json.load(fh)
    print(f"sidecar entries:     {len(images):,}")

    tally = {"species": 0, "has-image": 0, "no-match": 0, "filled": 0}
    added: dict[str, str] = {}
    for path in iter_family_files("."):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        stack = [doc]
        while stack:
            node = stack.pop()
            stack.extend(node.get("children") or [])
            stack.extend(node.get("speciesList") or [])
            if node.get("rank") != "SPECIES":
                continue
            tally["species"] += 1
            name = (node.get("name") or "").strip()
            if not name:
                continue
            key = name.lower()
            entry = images.get(name) or images.get(key) or {}
            if entry.get("image") or entry.get("imageUrl"):
                tally["has-image"] += 1
                continue
            uri = exact.get(key) or by_canon.get(canon.get(key) or key)
            if not uri:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            added[name] = uri

    print("=" * 66)
    print(f"species scanned            {tally['species']:>9,}")
    print(f"already has an image       {tally['has-image']:>9,}")
    print(f"no NMNH match              {tally['no-match']:>9,}")
    print(f"NMNH can fill              {tally['filled']:>9,}")

    if not args.apply:
        print("\nsample (read these before approving):")
        for n in list(added)[:10]:
            print(f"  {n[:36]:<38}{added[n][:56]}")
        print("\n  (dry run -- pass --apply to write)")
        return 0

    for name, uri in added.items():
        entry = images.setdefault(name, {})
        entry["imageUrl"] = uri
        entry["imageSource"] = "nmnh"
    with open(args.sidecar, "w", encoding="utf-8") as fh:
        # indent=2 to match how the sidecar is already formatted: a compact dump
        # rewrites all 1.5M lines and buries the few thousand real additions in a
        # diff nobody can review.
        json.dump(images, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    total = sum(1 for v in images.values() if v.get("imageUrl"))
    print(f"\n  wrote {len(added):,} NMNH imageUrl entries -> {args.sidecar}")
    print(f"  sidecar now holds {total:,} external imageUrl entries, {os.path.getsize(args.sidecar)/1e6:.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
