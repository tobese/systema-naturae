#!/usr/bin/env python3
"""Describe the species that host subspecies.

The subspecies rank is a dead end on its own: of the 851 SUBSPECIES nodes in the
tree, only **2** have an en.wikipedia article of their own (132 are redirects,
717 have no page), because Wikipedia documents subspecies inside the species
article rather than at the trinomial. There is nothing to fetch per subspecies.

The leverage is one level up. Those 851 subspecies hang off **230 host
species**, and 91 of those hosts have no stored description — so enriching
just those 91 is both a small target and the thing that gives their subspecies
real text. `SubspeciesPanel` then reads the parent's stored prose (via
`findNodeByName`) instead of duplicating it onto all 851 nodes.

So this fills descriptions for host species that (a) have at least one
SUBSPECIES child and (b) have none of their own. Species that already have text
are left alone, and so is everything else in the tree.

Usage (from the repo root, with a tunnel to the wiki mirror on debbie):
    ssh -f -N -L 15433:127.0.0.1:5433 debbie
    python3 scripts/enrichSubspeciesHosts.py            # dry run
    python3 scripts/enrichSubspeciesHosts.py --apply
"""
import argparse
import json
import os
import re
import sys
from glob import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # discovers the layout instead of assuming it
import enrichBreedsFromWikipedia as wiki   # reuse the extraction, not a copy

DSN = wiki.DEFAULT_DSN


def collect_hosts(root):
    """{family_dir: (path, [species names])} - hosts of subspecies with no text."""
    out = {}
    for p in sorted(list(iter_family_files(root))):
        try:
            tree = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        need = []

        def walk(node):
            if node.get("rank") == "SPECIES":
                kids = node.get("children") or []
                has_sub = any(c.get("rank") == "SUBSPECIES" for c in kids)
                if has_sub and not node.get("description") and node.get("name"):
                    need.append(node["name"])
            for c in node.get("children") or []:
                walk(c)

        walk(tree)
        if need:
            out[p.split(os.sep)[-4]] = (p, need)
    return out


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--root", default=root)
    ap.add_argument("--dsn", default=os.environ.get("WIKI_PG_DSN", DSN))
    ap.add_argument("--apply", action="store_true", help="write descriptions into the family JSONs")
    ap.add_argument("--force", action="store_true", help="re-extract hosts that already have text")
    args = ap.parse_args()

    hosts = collect_hosts(args.root)
    total = sum(len(v[1]) for v in hosts.values())
    print(f"{len(hosts)} families, {total} subspecies-host species without a description")

    conn = wiki.connect(args.dsn)
    cur = conn.cursor()

    names = sorted({n for _p, need in hosts.values() for n in need})
    pages = wiki.fetch_pages(cur, names)
    print(f"fetched {len(pages)} of {len(names)} candidate articles")

    result = {}
    for name in names:
        rec = pages.get(name.lower())
        if not rec or "text" not in rec:
            continue
        paras = wiki.lead_paragraphs(rec["text"])
        # A species article's lead should read as a species description; reject
        # anything that is really a disambiguation or a list.
        if len(paras) < 1 or len(paras[0]) < 60:
            continue
        result[name] = {"title": rec["title"], "paragraphs": paras}

    print(f"resolved {len(result)}; unresolved {len(names) - len(result)}")
    for n in names:
        if n not in result:
            print(f"  UNRESOLVED {n}")
    if not args.apply:
        print("(dry run - pass --apply)")
        return

    written = 0
    for fam, (path, need) in hosts.items():
        tree = json.load(open(path, encoding="utf-8"))
        hits = [0]

        def stamp(node):
            if node.get("rank") == "SPECIES" and node.get("name") in result \
                    and (args.force or not node.get("description")):
                node["description"] = "\n".join(result[node["name"]]["paragraphs"])
                node["wikipediaTitle"] = result[node["name"]]["title"]
                node["sourcedFrom"] = "wikipedia"
                hits[0] += 1
            for c in node.get("children") or []:
                stamp(c)

        stamp(tree)
        if hits[0]:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(tree, indent=2, ensure_ascii=False) + "\n")
            written += hits[0]
            print(f"  {fam}: described {hits[0]} subspecies-host species")
    print(f"done - {written} species described")


if __name__ == "__main__":
    main()
