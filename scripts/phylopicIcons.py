#!/usr/bin/env python3
"""Fetch PhyloPic metadata for the silhouettes ChecklistBank uses as group icons.

ChecklistBank labels each icon with its own classification bucket
("prokaryotes", "otherfungi", "othermolluscs"), which is NOT what the image
depicts: the one labelled "prokaryotes" is a Fusobacteriales silhouette and the
one labelled "plants" is a Fagales silhouette. Both facts matter, so this
records the label, the licence, the contributor and what the silhouette actually
is, per icon.

    python3 scripts/phylopicIcons.py --ids /tmp/phylopic-ids.txt
    python3 scripts/phylopicIcons.py --ids /tmp/phylopic-ids.txt --fetch
"""
import argparse
import json
import os
import time
import urllib.request

UA = ("systema-naturae-research/1.0 "
      "(https://github.com/tobese/systema-naturae)")
API = "https://api.phylopic.org/images/"
IMG = "https://images.phylopic.org/images/{uuid}/thumbnail/{size}.png"


def fetch(uuid, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(API + uuid, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:                      # noqa: BLE001
            if i == tries - 1:
                return {"_error": str(e)}
            time.sleep(1.5 * (i + 1))


def row(label, d):
    L = d.get("_links", {}) or {}
    lic = (L.get("license") or {}).get("href", "")
    return {
        "label": label,
        "uuid": d.get("uuid", ""),
        # every PhyloPic licence URL ends in "/", so rsplit on it yields ""
        # and all 33 icons silently reported "(none)"
        "licence": lic.rstrip("/").rsplit("/", 1)[-1] if lic else "",
        "licenceUrl": lic,
        "contributor": d.get("attribution")
        or (L.get("contributor") or {}).get("title", ""),
        "depicts": (L.get("generalNode") or {}).get("title", ""),
        "alsoDepictedOn": [n.get("title", "") for n in (L.get("nodes") or [])],
        "created": (d.get("created") or "")[:10],
        "error": d.get("_error", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True,
                    help="file of '<label> <uuid>' lines")
    ap.add_argument("--out", default="data/phylopic-icons.json")
    ap.add_argument("--fetch", action="store_true",
                    help="also download the 256px thumbnails")
    args = ap.parse_args()

    rows = []
    for line in open(args.ids, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        label, uuid = line.split()[:2]
        r = row(label, fetch(uuid))
        rows.append(r)
        if args.fetch and not r["error"]:
            url = IMG.format(uuid=uuid, size="256")
            dest = os.path.join("docs/assets/phylopic", f"{label}.png")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=90) as fh, \
                        open(dest, "wb") as out:
                    out.write(fh.read())
            except Exception as e:                  # noqa: BLE001
                print(f"  ! {label}: {e}")
        time.sleep(0.25)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    bad = [r for r in rows if r["error"]]
    print(f"  {len(rows)} icons -> {args.out}")
    if bad:
        print(f"  {len(bad)} could not be fetched:")
        for r in bad:
            print(f"      {r['label']:18s} {r['error']}")
    lics = {}
    for r in rows:
        lics.setdefault(r["licence"] or "(none)", []).append(r["label"])
    for lic, labels in sorted(lics.items(), key=lambda kv: -len(kv[1])):
        print(f"    {lic:16s} {len(labels):>3}   {', '.join(labels[:6])}"
              + (" ..." if len(labels) > 6 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
