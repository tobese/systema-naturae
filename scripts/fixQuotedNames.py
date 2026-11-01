#!/usr/bin/env python3
"""Undo the quoted names the WoRMS take left in the tree.

The WoRMS take of 2026-10-12 (checklistbank-2011, a903bcfa72e) kept the CSV
quote characters: SPECIES nodes named `"Apororhynchus hemignathi"` (quotes in
name, authorship, lineage, description) under a GENUS `"Apororhynchus` that
sits beside the real `Apororhynchus` and shares its id. Measured 2026-11-01:
49,083 quoted species, 47,547 of them a second copy of a species held
unquoted in the same kingdom; 1,347 are subgenus names stored as species
(`"Pallisentis (Brevitritospinus)`). docs/sub-ranks-plan.md, step 0.

Per quoted SPECIES node:

  subgenus name   `Genus (Subgenus)` with no epithet: not a species; removed
  twin            the dequoted canonical name is held unquoted in the same
                  kingdom (same file preferred): the quoted node is removed,
                  and its sourceIds and authorship go to the twin where the
                  twin has none (fill-only; a different id under the same
                  source key is kept as the twin's and counted)
  otherwise       dequoted in place and moved under the unquoted genus

A quoted GENUS node is merged into the unquoted genus of the same name in
the same file, or dequoted when there is none, and removed once empty.

Writes under maintenanceLock -- run it through maintenanceSession.py, then
resyncFamilyCounts.py --apply. Every removal and merge goes to the ledger
(`<sources>/work/fix-quoted-names/ledger.jsonl`).

    python3 scripts/fixQuotedNames.py              # dry run
    python3 scripts/fixQuotedNames.py --apply
"""
import argparse
import collections
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
import sources  # noqa: E402
from buildSpeciesParquet import canonicalize  # noqa: E402
from tree import count_species, iter_family_files, kingdom_names, save_json  # noqa: E402

LEDGER = os.path.join(sources.ROOT, "work", "fix-quoted-names", "ledger.jsonl")
SUBGENUS_ONLY = re.compile(r"^\S+ \([^)]*\)$")
TEXT_FIELDS = ("name", "authorship", "lineage", "description", "commonName")
WORMS_KEY = "checklistbank-2011"


def quoted(s) -> bool:
    return isinstance(s, str) and s.startswith('"')


def dequote(s: str) -> str:
    return s.strip().strip('"').replace('""', '"').strip()


def canon_of(name: str) -> str:
    toks = name.split()
    return canonicalize(name, toks[0] if toks else "", "SPECIES")[0]


def walk_with_parent(node, parent=None):
    yield parent, node
    for c in node.get("children") or []:
        yield from walk_with_parent(c, node)


def index_kingdom(kingdom):
    """Unquoted canonical name -> [(path, id)], and the files holding quotes."""
    index = collections.defaultdict(list)
    dirty = []
    for fam in iter_family_files(kingdom):
        with open(fam.path, encoding="utf-8") as fh:
            text = fh.read()
        has_quotes = '"name": "\\"' in text
        doc = json.loads(text)
        for _, n in walk_with_parent(doc):
            if n.get("rank") == "SPECIES" and n.get("name") and not quoted(n["name"]):
                index[canon_of(n["name"])].append((fam.path, n.get("id")))
        if has_quotes:
            dirty.append(fam.path)
    return index, dirty


def fix_file(path, doc, index, stat, ledger, merges):
    """Fix one family document in place. Returns the species removed."""
    removed = 0
    genera = {}
    for _, n in walk_with_parent(doc):
        if n.get("rank") == "GENUS" and n.get("name") and not quoted(n["name"]):
            genera.setdefault(n["name"], n)

    for parent, n in list(walk_with_parent(doc)):
        if n.get("rank") != "SPECIES" or not quoted(n.get("name")):
            continue
        name = dequote(n["name"])
        if SUBGENUS_ONLY.match(name):
            parent["children"].remove(n)
            removed += 1
            stat["subgenus name removed"] += 1
            ledger.append({"action": "remove-subgenus-name", "file": path, "id": n.get("id"), "name": n["name"]})
            continue
        twins = index.get(canon_of(name)) or []
        twin = next((t for t in twins if t[0] == path), twins[0] if twins else None)
        if twin:
            parent["children"].remove(n)
            removed += 1
            stat["twin: quoted copy removed"] += 1
            stat["twin in another file" if twin[0] != path else "twin in same file"] += 1
            merges[twin[0]].append((twin[1], n))
            ledger.append({"action": "merge-into-twin", "file": path, "id": n.get("id"), "name": n["name"],
                           "twinFile": twin[0], "twinId": twin[1]})
            continue
        for f in TEXT_FIELDS:
            if quoted(n.get(f)) or (isinstance(n.get(f), str) and '"' in n[f] and f in ("name", "lineage")):
                n[f] = dequote(n[f]) if quoted(n[f]) else n[f].replace('"', "")
        if isinstance(n.get("description"), str):
            n["description"] = n["description"].replace('"', "")
        stat["dequoted in place"] += 1
        ledger.append({"action": "dequote", "file": path, "id": n.get("id"), "name": n["name"]})
        target = genera.get(name.split()[0])
        if parent is not None and quoted(parent.get("name")) and target is not None and target is not parent:
            parent["children"].remove(n)
            target.setdefault("children", []).append(n)
            stat["moved to unquoted genus"] += 1

    # Quoted genera: merge what is left into the unquoted one, or dequote.
    for parent, n in list(walk_with_parent(doc)):
        if n.get("rank") != "GENUS" or not quoted(n.get("name")):
            continue
        name = dequote(n["name"])
        target = genera.get(name)
        if target is not None and target is not n:
            target.setdefault("children", []).extend(n.get("children") or [])
            parent["children"].remove(n)
            stat["quoted genus merged"] += 1
        elif not n.get("children"):
            parent["children"].remove(n)
            stat["quoted genus removed (empty)"] += 1
        else:
            for f in TEXT_FIELDS:
                if quoted(n.get(f)):
                    n[f] = dequote(n[f])
            genera[name] = n
            stat["quoted genus dequoted"] += 1
    return removed


def merge_into(path, wanted, stat, apply):
    """Fill twins in one file from their quoted copies (fill-only)."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    before = count_species(doc)
    by_id = {}
    for _, n in walk_with_parent(doc):
        if n.get("rank") == "SPECIES":
            by_id.setdefault(n.get("id"), n)
    changed = False
    for twin_id, q in wanted:
        t = by_id.get(twin_id)
        if t is None:
            stat["twin gone at merge time"] += 1
            continue
        ids = t.setdefault("sourceIds", {})
        for k, v in (q.get("sourceIds") or {}).items():
            if k not in ids:
                ids[k] = v
                stat["sourceId carried to twin"] += 1
                changed = True
            elif ids[k] != v:
                # The quoted copies hold their WoRMS LSID under the generic
                # "checklistbank" key, which the twin usually holds for another
                # dataset (1,169 of 1,172 sampled). WoRMS ids are keyed
                # "checklistbank-2011" elsewhere in the tree; keep it there.
                if isinstance(v, str) and "marinespecies.org" in v and WORMS_KEY not in ids:
                    ids[WORMS_KEY] = v
                    stat["WoRMS id carried to twin as " + WORMS_KEY] += 1
                    changed = True
                else:
                    stat["sourceId differs, twin's kept"] += 1
        for f in ("authorship", "yearPublished"):
            if q.get(f) and not t.get(f):
                t[f] = dequote(q[f]) if isinstance(q[f], str) else q[f]
                stat[f"{f} carried to twin"] += 1
                changed = True
    if count_species(doc) != before:
        sys.exit(f"FATAL: species count changed merging into {path}")
    if changed and apply:
        save_json(path, doc)


def run(apply):
    stat = collections.Counter()
    ledger = []
    for k in kingdom_names():
        t0 = time.time()
        index, dirty = index_kingdom(k)
        merges = collections.defaultdict(list)
        for path in dirty:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            before = count_species(doc)
            removed = fix_file(path, doc, index, stat, ledger, merges)
            if count_species(doc) != before - removed:
                sys.exit(f"FATAL: {path}: {before} - {removed} != {count_species(doc)}")
            stat["files fixed"] += 1
            if apply:
                save_json(path, doc)
        # Twins in the files just fixed were read before the fix, so re-read.
        for path, wanted in merges.items():
            merge_into(path, wanted, stat, apply)
        print(f"  {k:10s} {len(dirty):>5,} files with quoted names  ({time.time() - t0:.0f}s)", flush=True)
    return stat, ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.apply:
        with maintenanceLock.hold_exclusive():
            stat, ledger = run(True)
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            at = time.strftime("%Y-%m-%dT%H:%M:%S")
            for row in ledger:
                fh.write(json.dumps({"at": at, **row}, ensure_ascii=False) + "\n")
    else:
        stat, ledger = run(False)
    for key, v in sorted(stat.items()):
        print(f"  {v:>9,}  {key}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
