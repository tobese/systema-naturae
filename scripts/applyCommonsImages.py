#!/usr/bin/env python3
"""Add Wikimedia Commons photographs to the image sidecar.

The Commons harvest (Zenodo 17509532, CC-BY 4.0 at the record level) maps taxa to
individual files. 34,724 of our species are covered, but 32,083 of those already
had a portrait from Wikidata P18 -- which resolves to a Commons file anyway. Only
2,641 are genuinely new.

Unlike the NMNH harvest these are Commons-hosted, so they go in the `image` field
as a bare filename, which useWikiImages resolves to a Special:FilePath thumbnail.
What they add over P18 is the `Owner` and `UsageTerms` columns, so this also
records the author and licence -- 1,656 of the 2,641 carry an artist, and the
rest still get a link to the Commons file page, where the author can be read.

NC and ND are refused outright. A public portal cannot redistribute them, and the
EOL harvester does not filter: of the ten harvests assessed, seven were
non-commercial. Two of these 2,641 are BY-NC and are dropped here rather than
counted as usable.

Usage:
    python3 scripts/applyCommonsImages.py            # dry run
    python3 scripts/applyCommonsImages.py --apply
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # noqa: E402
from canonicalNames import _load as load_canonical  # noqa: E402

SIDECAR = os.path.join("shared", "data", "wiki-images.json")
COMMONS = "/Volumes/MacieExternal/tmp/opencode/commons_new_images.json"

# Refuse anything that forbids commercial use or derivatives. Checked against the
# licence URL, and "no known copyright restrictions" is treated as public domain
# rather than as permission, since that is what the Commons template means.
def licence_ok(lic: str) -> bool:
    l = (lic or "").lower()
    if not l:
        return False
    if "-nc" in l or "-nd" in l:
        return False
    if "known copyright restrictions" in l:
        return False
    return ("licenses/" in l) or ("publicdomain" in l)


# A Commons category says a file is *about* a taxon, not that it *depicts* one.
# The harvest's files are the taxon's subject-matter, so the category legitimately
# holds its predators, prey, hosts and diseases -- and the first pass duly gave
# Tylenchulus semipenetrans "Slow decline disease.jpg" and Rotylenchulus
# reniformis "Sweetpotato infected by reniform nematode.jpg". Both are pictures of
# something else entirely.
#
# This is a title-word blocklist, so it is neither complete nor sound: it cannot
# tell a portrait of a nematode from a nematode's disease, and a file titled only
# with a binomial may still be a scanning artefact. It is applied anyway because
# the alternative is a portrait slot full of pictures of other organisms, and a
# wrong image is worse than a missing one. Anything it lets through is a residual
# risk, not a verified portrait.
NOT_PORTRAIT = re.compile(
    r"\b(distributi|range|verbreit|carte|map|"
    r"disease|host|hosts|prey|predator|parasite|parasiti|infected|infection|"
    r"symptom|damage|damaged|galls|signs|larva|larvae|eggs?|cocoon|nest|"
    r"fungus|fungal|mould|mold|bacteria|bacterial|virus|viral|"
    r"habitat|habitats|habitat|symbiont|mycorrhiz|"
    r"fossil|footprint|track|burrow|web|camouflage|mimicry|"
    r"specimen|holotype|syntype|lectotype|neotype|label|labelling|capsule|"
    r"nest|nesting|shell|carapace|exuvia|cast)\b", re.I)
BAD_EXT = re.compile(r"\.(svg|tif|tiff|gif|png|ogg|ogv|webm|wav|mp3|mp4|pdf)$", re.I)


def filename_of(rec) -> str | None:
    """The bare Commons filename, which is what the sidecar's `image` holds."""
    title = (rec.get("title") or "").strip()
    subject = title or (rec.get("uri") or "").split("?")[0].rsplit("/", 1)[-1]
    if NOT_PORTRAIT.search(subject.replace("%20", " ")):
        return None
    if not subject or "/" in subject or BAD_EXT.search(subject):
        return None
    return subject


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=COMMONS)
    ap.add_argument("--sidecar", default=SIDECAR)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"FATAL: {args.source} not found. Produce it by streaming\n"
                 f"       https://zenodo.org/records/17509532/files/71_delta.tar.gz")

    canon = load_canonical()
    with open(args.source, encoding="utf-8") as fh:
        raw = json.load(fh)

    exact: dict[str, dict] = {}
    by_canon: dict[str, dict] = {}
    refused = 0
    for name, rec in raw.items():
        fn = filename_of(rec)
        if not fn or not licence_ok(rec.get("lic", "")):
            refused += 1
            continue
        entry = {
            "image": fn,
            "imageSource": "commons",
            "imageArtist": (rec.get("owner") or "").strip() or None,
            "imageLicense": (rec.get("lic") or "").strip(),
        }
        exact[name.lower()] = entry
        by_canon[canon.get(name.lower()) or name.lower()] = entry
    print(f"Commons candidates: {len(raw):,}  | refused (NC/ND/unknown): {refused:,}")

    with open(args.sidecar, encoding="utf-8") as fh:
        images = json.load(fh)

    tally = {"species": 0, "has-image": 0, "no-match": 0, "filled": 0}
    added: dict[str, dict] = {}
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
            cur = images.get(name) or images.get(key) or {}
            if cur.get("image") or cur.get("imageUrl"):
                tally["has-image"] += 1
                continue
            rec = exact.get(key) or by_canon.get(canon.get(key) or key)
            if not rec:
                tally["no-match"] += 1
                continue
            tally["filled"] += 1
            added[name] = rec

    withartist = sum(1 for v in added.values() if v.get("imageArtist"))
    print("=" * 66)
    print(f"species scanned            {tally['species']:>9,}")
    print(f"already has an image       {tally['has-image']:>9,}")
    print(f"no Commons match           {tally['no-match']:>9,}")
    print(f"Commons can fill           {tally['filled']:>9,}")
    print(f"  of which have an artist  {withartist:>9,}")

    if not args.apply:
        print("\nsample (read these before approving):")
        for n in list(added)[:10]:
            r = added[n]
            print(f"  {n[:30]:<32}{r['image'][:38]:<40}{(r.get('imageArtist') or '-')[:26]}")
        print("\n  (dry run -- pass --apply to write)")
        return 0

    for name, rec in added.items():
        entry = images.setdefault(name, {})
        entry["image"] = rec["image"]
        entry["imageSource"] = rec["imageSource"]
        entry["imageLicense"] = rec["imageLicense"]
        if rec.get("imageArtist"):
            entry["imageArtist"] = rec["imageArtist"]
    with open(args.sidecar, "w", encoding="utf-8") as fh:
        # indent=2 matches the existing sidecar format; a compact dump rewrites
        # all 1.5M lines and buries the additions.
        json.dump(images, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    total = sum(1 for v in images.values() if v.get("imageArtist"))
    print(f"\n  wrote {len(added):,} Commons portraits -> {args.sidecar}")
    print(f"  {total:,} entries now carry an artist; "
          f"{os.path.getsize(args.sidecar)/1e6:.0f} MB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
