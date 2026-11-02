#!/usr/bin/env python3
"""Remove cross-kingdom copies that rest only on Wikidata, where another
kingdom holds the same species from a real source.

verifyTree's "cross-kingdom homonyms are the documented set" failed on 439
species ids after the Wikidata Species apply (10-30). Measured 2026-11-02:
most are not homonyms but one organism placed twice. Wikidata items carry a
`parent taxon` that sometimes points at a homonym genus in another kingdom --
Q137656143, the weevil *Dendropemon japonicus* (Morimoto, 1979), has the
mistletoe genus Q5256779 as parent instead of the weevil genus Q54959522 --
and the import followed it faithfully, so the copy lands under Loranthaceae
with the weevil's authorship and only a Wikidata id.

Rule, per species id held in more than one kingdom and not already in
data/known-cross-kingdom-homonyms.json or data/cross-kingdom-homonym-decisions.json:

  weak copy    its sourceIds are only Wikidata Species and/or the bare
               `checklistbank` container id (or none)
  sourced      any other dataset id

  exactly one kingdom holds a sourced copy, every other kingdom only weak
  copies  ->  the weak copies are removed; their ids move to the sourced copy
              where it has none under that key (fill-only), and a genus left
              empty by the removal goes too.
  anything else (two sourced kingdoms, or none), or a weak copy whose
  authorship differs from the sourced copy's (it may be a real homonym:
  another organism with the same binomial)  ->  left for a person.

A recorded decision whose removed placement is back in the tree (45 on
2026-11-02: importColChecklist.py's direct-write path had no guard until
then) is re-applied as recorded, before the rule runs.

Every removal is recorded in data/cross-kingdom-homonym-decisions.json
(action "remove", confidence "medium", decidedBy this script), which is also
what stops importTransformed.py putting the copy back on the next re-import.

Writes under maintenanceLock -- run it through maintenanceSession.py, then
resyncFamilyCounts.py --apply.

    python3 scripts/resolveWeakHomonyms.py            # dry run
    python3 scripts/resolveWeakHomonyms.py --apply
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
from tree import count_species, iter_family_files, kingdom_names, save_json  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECISIONS = os.path.join(ROOT, "data", "cross-kingdom-homonym-decisions.json")
KNOWN = os.path.join(ROOT, "data", "known-cross-kingdom-homonyms.json")
WIKIDATA = "ac5f72cf-172d-4eb4-ad8c-db66ea1c78e5"   # Wikidata Species (ChecklistBank 314569)
WEAK_KEYS = {WIKIDATA, "checklistbank"}


def is_weak(node) -> bool:
    return set(node.get("sourceIds") or {}) <= WEAK_KEYS


def same_author(a, b) -> bool:
    norm = lambda s: re.sub(r"[^a-z]", "", (s or "").lower().replace(" and ", "&"))
    return not a or not b or norm(a) == norm(b)


def walk(node, parent=None):
    yield parent, node
    for c in node.get("children") or []:
        yield from walk(c, node)


def index():
    """species id -> [(kingdom, family slug, path)] for every species node."""
    where = collections.defaultdict(list)
    for kingdom in kingdom_names():
        for fam in iter_family_files(kingdom):
            with open(fam.path, encoding="utf-8") as fh:
                doc = json.load(fh)
            for _, n in walk(doc):
                if n.get("rank") == "SPECIES" and n.get("id"):
                    where[n["id"]].append((kingdom, fam.slug, fam.path))
    return where


def node_in(path, sid):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    for parent, n in walk(doc):
        if n.get("rank") == "SPECIES" and n.get("id") == sid:
            return doc, parent, n
    return doc, None, None


def plan(where, settled):
    """Yield (sid, weak placements, the sourced placement) for each id the
    rule decides; count the rest by why they were left."""
    left = collections.Counter()
    out = []
    for sid, places in sorted(where.items()):
        if len({k for k, _, _ in places}) < 2 or sid in settled:
            continue
        by_kingdom = collections.defaultdict(list)
        for k, slug, path in places:
            _, _, n = node_in(path, sid)
            by_kingdom[k].append((slug, path, n))
        sourced = [k for k, copies in by_kingdom.items() if any(not is_weak(n) for _, _, n in copies)]
        if len(sourced) != 1:
            left["two or more kingdoms sourced" if sourced else "no kingdom sourced"] += 1
            continue
        keep_k = sourced[0]
        keep = next((s, p, n) for s, p, n in by_kingdom[keep_k] if not is_weak(n))
        weak = [(k, s, p, n) for k, copies in by_kingdom.items() if k != keep_k for s, p, n in copies]
        if any(not same_author(n.get("authorship"), keep[2].get("authorship")) for _k, _s, _p, n in weak):
            left["authorship differs from the sourced copy (maybe a real homonym)"] += 1
            continue
        out.append((sid, keep_k, keep, weak))
    return out, left


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(DECISIONS, encoding="utf-8") as fh:
        decisions = json.load(fh)
    with open(KNOWN, encoding="utf-8") as fh:
        known = json.load(fh)
    settled = set(decisions) | set(known)

    def run(apply):
        where = index()
        todo, left = plan(where, settled)
        stat = collections.Counter()
        by_file = collections.defaultdict(list)      # path -> [sid] to remove
        fills = collections.defaultdict(dict)         # keep path -> {sid: {key: value}}
        author_fills = collections.defaultdict(dict)  # keep path -> {sid: {field: [ids]}}

        def carry_authors(keep_path, sid, n, keep_n):
            for field in ("authorIds", "basionymAuthorIds"):
                if n.get(field) and not keep_n.get(field):
                    author_fills[keep_path].setdefault(sid, {})[field] = n[field]
        new = {}
        # Recorded decisions first: a removed placement that came back goes again.
        for sid, d in decisions.items():
            if not str(d.get("action", "")).startswith("remove"):
                continue
            places = d.get("removed_from") or []
            places = {places} if isinstance(places, str) else set(places)
            back = [(k, slug, path) for k, slug, path in where.get(sid, []) if f"{k}/{slug}" in places]
            kept = [(k, slug, path) for k, slug, path in where.get(sid, []) if f"{k}/{slug}" not in places]
            for k, slug, path in back:
                by_file[path].append(sid)
                stat["recorded decision re-applied (placement had come back)"] += 1
                if kept:
                    _, _, n = node_in(path, sid)
                    _, _, keep_n = node_in(kept[0][2], sid)
                    for key, val in (n.get("sourceIds") or {}).items():
                        if key != "checklistbank" and key not in (keep_n.get("sourceIds") or {}):
                            fills[kept[0][2]].setdefault(sid, {})[key] = val
                    carry_authors(kept[0][2], sid, n, keep_n)
        for sid, keep_k, (keep_slug, keep_path, keep_n), weak in todo:
            for k, slug, path, n in weak:
                by_file[path].append(sid)
                for key, val in (n.get("sourceIds") or {}).items():
                    if key != "checklistbank" and key not in (keep_n.get("sourceIds") or {}):
                        fills[keep_path].setdefault(sid, {})[key] = val
                carry_authors(keep_path, sid, n, keep_n)
                stat[f"weak copy removed from {k}"] += 1
            new[sid] = {
                "decided": time.strftime("%Y-%m-%d"),
                "action": "remove",
                "evidence": (
                    f"rule (resolveWeakHomonyms.py): the {', '.join(sorted({w[0] + '/' + w[1] for w in weak}))} "
                    f"copy rests only on Wikidata Species / an unrecorded ChecklistBank id; "
                    f"{keep_k}/{keep_slug} holds it from "
                    f"{', '.join(sorted(set(keep_n.get('sourceIds') or {}) - WEAK_KEYS))}. "
                    f"Wikidata items can point their parent taxon at a homonym genus in another kingdom "
                    f"(Q137656143 Dendropemon japonicus -> the plant genus Q5256779)."),
                "confidence": "medium",
                "decidedBy": "scripts/resolveWeakHomonyms.py",
                "placements": [{"kingdom": keep_k, "family": keep_slug,
                                "sources": sorted((keep_n.get("sourceIds") or {}).keys())}]
                              + [{"kingdom": k, "family": s, "sources": sorted((n.get("sourceIds") or {}).keys())}
                                 for k, s, _p, n in weak],
                "removed_from": sorted({f"{k}/{s}" for k, s, _p, _n in weak}),
                "kept": [f"{keep_k}/{keep_slug}"],
            }

        for path, sids in sorted(by_file.items()):
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            before = count_species(doc)
            gone = set(sids)
            removed = 0
            for parent, n in list(walk(doc)):
                kids = n.get("children") or []
                keep_kids = [c for c in kids if not (c.get("rank") == "SPECIES" and c.get("id") in gone)]
                removed += len(kids) - len(keep_kids)
                if len(keep_kids) != len(kids):
                    n["children"] = keep_kids
            # a genus emptied by the removal goes as well
            for parent, n in list(walk(doc)):
                kids = n.get("children") or []
                emptied = [c for c in kids if c.get("rank") == "GENUS" and not c.get("children")
                           and any(sid.startswith("SP_" + (c.get("name") or "").upper() + "_") for sid in gone)]
                if emptied:
                    n["children"] = [c for c in kids if c not in emptied]
                    stat["genus emptied and removed"] += len(emptied)
            if count_species(doc) != before - removed or removed != len(set(sids)):
                sys.exit(f"FATAL: {path}: removed {removed} of {len(gone)}, "
                         f"{before} -> {count_species(doc)}")
            if "speciesCount" in doc:      # verifyTree: a file's own count matches its contents
                doc["speciesCount"] = count_species(doc)
            if apply:
                save_json(path, doc)

        for path in sorted(set(fills) | set(author_fills)):
            per, per_a = fills.get(path, {}), author_fills.get(path, {})
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            for _, n in walk(doc):
                if n.get("rank") == "SPECIES" and n.get("id") in per:
                    n.setdefault("sourceIds", {}).update(per[n["id"]])
                    stat["ids moved to the sourced copy"] += len(per[n["id"]])
                if n.get("rank") == "SPECIES" and n.get("id") in per_a:
                    n.update(per_a[n["id"]])
                    stat["author links moved to the sourced copy"] += 1
            if apply:
                save_json(path, doc)

        if apply and new:
            decisions.update(new)
            tmp = DECISIONS + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(decisions, fh, indent=1, ensure_ascii=False)
                fh.write("\n")
            os.replace(tmp, DECISIONS)
        return todo, left, stat

    if args.apply:
        with maintenanceLock.hold_exclusive():
            todo, left, stat = run(True)
    else:
        todo, left, stat = run(False)

    print(f"  {len(todo):,} species ids resolved by the rule")
    for k, v in sorted(stat.items()):
        print(f"  {v:>7,}  {k}")
    for k, v in sorted(left.items()):
        print(f"  {v:>7,}  left for a person: {k}")
    for sid, keep_k, keep, weak in todo[:8]:
        print(f"      {sid}: keep {keep_k}/{keep[0]}, remove "
              + ", ".join(f"{k}/{s}" for k, s, _p, _n in weak))
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
