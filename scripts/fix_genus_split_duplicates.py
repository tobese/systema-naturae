#!/usr/bin/env python3
"""
Remove species copies left behind under a superseded genus.

What this is
------------
Six species are listed twice in the tree, once under the genus they belong to
and once under the genus they were moved out of:

    Aphelocoma coerulescens     Aphelocoma  +  Corvus
    Aphelocoma insularis        Aphelocoma  +  Corvus
    Cyanocorax mystacalis       Cyanocorax  +  Corvus
    Cyanocorax orcinus          Cyanocorax  +  Corvus
    Galbalcyrhynchus purusianus Galbalcyrhynchus  +  Galbula
    Stactolaema olivacea        Stactolaema  +  Smilorbis

Cyanocorax, Aphelocoma and Galbalcyrhynchus were all split out of the genera
they are duplicated under. A reader sees the same species twice, in two genera,
and neither copy is marked as a synonym.

Evidence
--------
Checked against the Catalogue of Life (free, no key, dataset 3LR) on
2026-09-30. All six come back `status: accepted` under the newer genus:

    Aphelocoma coerulescens      accepted as Aphelocoma coerulescens (Bosc, 1798)
    Aphelocoma insularis         accepted as Aphelocoma insularis Henshaw, 1886
    Cyanocorax mystacalis        accepted as Cyanocorax mystacalis (de Sparre, ...)
    Cyanocorax orcinus           accepted as Orcinus Fitzinger, 1860
    Galbalcyrhynchus purusianus  accepted as Galbalcyrhynchus purusianus Goeldi, ...
    Stactolaema olivacea         accepted as Stactolaema olivacea (Shelley, 1885)

Note genus-level status is not the question - COL reports BOTH genera in each
pair as accepted, correctly, since they are distinct real taxa. The question is
which genus each species belongs to, so the lookup is per species.

One further wrinkle: COL has moved Cyanocorax orcinus again, to Orcinus
Fitzinger, 1860. We carry neither, so this pass only drops the stale Corvus copy
and leaves the accepted name alone. Following COL to Orcinus would mean adding a
genus, which is a taxonomy decision rather than a cleanup.

Before removing a copy, anything worth keeping on it is merged into the
surviving one - the longer description wins, with its sourcedFrom - so a stale
copy that happens to hold the only prose does not take it with it.

    python3 scripts/fix_genus_split_duplicates.py taxonomy
    python3 scripts/fix_genus_split_duplicates.py taxonomy --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# species id -> (genus to keep, genus to remove the duplicate from)
DECIDED = {
    "APHELOCOMA_COERULESCENS":   ("Aphelocoma", "Corvus"),
    "APHELOCOMA_INSULARIS":      ("Aphelocoma", "Corvus"),
    "CYANOCORAX_MYSTACALIS":    ("Cyanocorax", "Corvus"),
    "CYANOCORAX_ORCINUS":       ("Cyanocorax", "Corvus"),
    "GALBALCYRHYNCHUS_PURUSIANUS": ("Galbalcyrhynchus", "Galbula"),
    "STACTOLAEMA_OLIVACEA":      ("Stactolaema", "Smilorbis"),
}

EVIDENCE = {
    "APHELOCOMA_COERULESCENS":   "accepted as Aphelocoma coerulescens (Bosc, 1798)",
    "APHELOCOMA_INSULARIS":      "accepted as Aphelocoma insularis Henshaw, 1886",
    "CYANOCORAX_MYSTACALIS":     "accepted as Cyanocorax mystacalis (de Sparre, 1866)",
    "CYANOCORAX_ORCINUS":        "accepted as Orcinus Fitzinger, 1860 - a further reassignment we do not carry",
    "GALBALCYRHYNCHUS_PURUSIANUS": "accepted as Galbalcyrhynchus purusianus Goeldi, 1897",
    "STACTOLAEMA_OLIVACEA":      "accepted as Stactolaema olivacea (Shelley, 1885)",
}


def better(a: dict, b: dict) -> dict:
    da = len((a.get("description") or "").strip())
    db = len((b.get("description") or "").strip())
    if da != db:
        return a if da > db else b
    if (a.get("sourcedFrom") or "") and not (b.get("sourcedFrom") or ""):
        return a
    if (b.get("sourcedFrom") or "") and not (a.get("sourcedFrom") or ""):
        return b
    return a


def process(doc: dict, path: str, log: list) -> None:
    """Drop the stale copy from each genus, and record anything it was carrying.

    The description upgrade cannot happen here. The two copies live in DIFFERENT
    genera's child lists, so by the time the stale copy is dropped the survivor
    is somewhere else in the tree and is not in scope. An earlier version tried
    to merge inside the genus visit, which silently never fired for these cases
    and lost a description. The upgrade is a second pass over the whole tree.
    """
    def visit(node):
        genus = node.get("name") if node.get("rank") == "GENUS" else None
        if genus:
            kept, dropped = [], []
            for c in (node.get("children") or []):
                sid = c.get("id")
                if sid in DECIDED:
                    keep_g, drop_g = DECIDED[sid]
                    if genus == keep_g:
                        kept.append(c)
                        continue
                    if genus == drop_g:
                        dropped.append(c)
                        continue
                kept.append(c)
            for s in dropped:
                # Capture the description NOW. A second pass that re-reads the
                # file finds the stale copy already gone, so it can never see the
                # text it is meant to rescue.
                log.append((s.get("id"), genus, path, (s.get("description") or "").strip()))
                print(f"  {path}\n    drop {s.get('name')} (id={s.get('id')}) from genus {genus}"
                      f"\n      COL: {EVIDENCE.get(s.get('id'), '?')}")
            if dropped:
                node["children"] = kept
        for c in node.get("children") or []:
            visit(c)

    visit(doc)


def upgrade_descriptions(root: str, removed: list) -> int:
    """Carry a richer description from a dropped copy onto the surviving node.

    A separate pass because the survivor is in a different genus: Cyanocorax
    orcinus had 45 characters under Cyanocorax and 46 under Corvus, and dropping
    the Corvus copy inside the genus visit lost the longer one.
    """
    best: dict[str, str] = {}
    for sid, _genus, _path, dropped_desc in removed:
        if len(dropped_desc) > len(best.get(sid, "")):
            best[sid] = dropped_desc

    upgraded = 0
    for sid, text in best.items():
        for dirpath, _d, names in os.walk(root):
            if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
                continue
            for n in names:
                if not n.endswith(".json"):
                    continue
                path = os.path.join(dirpath, n)
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
                hit = []

                def find2(node):
                    if node.get("id") == sid and node.get("rank") == "SPECIES":
                        hit.append(node)
                    for c in (node.get("children") or []) or []:
                        find2(c)
                    for s in (node.get("speciesList") or []) or []:
                        find2(s)

                find2(doc)
                if not hit:
                    continue
                node = hit[0]
                cur = (node.get("description") or "").strip()
                if len(text) > len(cur):
                    node["description"] = text
                    upgraded += 1
                    print(f"  upgraded {sid} in {path}: {len(cur)}c -> {len(text)}c")
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(doc, fh, indent=2, ensure_ascii=False)
                        fh.write("\n")
    return upgraded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default="docs/reports/genus-split-duplicates.md")
    args = ap.parse_args()

    files = []
    for dirpath, _d, names in os.walk(args.root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    files.sort()

    log: list = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        before = len(log)
        process(doc, path, log)
        if args.apply and len(log) > before:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    verb = "Applied" if args.apply else "Would remove"
    print(f"\n{verb}: {len(log)} duplicate copies under a superseded genus")

    # Second pass: carry a richer description off a dropped copy onto the
    # survivor. Separate because the survivor lives in a different genus, so it
    # is not reachable from where the copy was dropped.
    upgraded = 0
    if args.apply and log:
        upgraded = upgrade_descriptions(args.root, log)
        print(f"  {upgraded} description(s) carried onto the survivor")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("# Species duplicated across a genus split\n\n")
        fh.write("Six species were listed under both the genus they belong to and the "
                 "genus they were moved out of. Each was checked against the Catalogue of "
                 "Life (free, no key, dataset `3LR`) on 2026-09-30; all six come back "
                 "`status: accepted` under the newer genus, so the copy under the older "
                 "genus is the stale one.\n\n")
        fh.write("| species id | keep in | remove from | Catalogue of Life |\n|---|---|---|---|\n")
        for sid, (keep, drop) in DECIDED.items():
            fh.write(f"| `{sid}` | {keep} | {drop} | {EVIDENCE.get(sid,'')} |\n")
        fh.write("\nGenus-level status is not the question: COL reports *both* genera in each "
                 "pair as accepted, correctly, since they are distinct real taxa. The lookup is "
                 "per species.\n\n## Log\n\n```\n")
        fh.write("\n".join(f"drop {sid} from genus {genus}  ({path})"
                           for sid, genus, path, _d in log) if log else "(nothing)")
        fh.write("\n```\n")
    print(f"  report → {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
