#!/usr/bin/env python3
"""Remove species copies that a source put in a second family we already had.

An import writes each offered species into the family the *source* assigns it
to. Where a source's circumscription differs from ours, that writes a species we
already hold somewhere else into a second family: 236 such copies across 57
file-pairs after the ILDIS, FLOW, Moss and Wikispecies runs, Kinnaridae and
Meenoplidae each holding the other's cixiid relatives.

This drops the copy that the import added and keeps the one the tree already
had, which is the rule `dedupe_genera_across_families.py` already applies for a
duplicated *genus*: the curated placement wins, and the taxonomy disagreement is
recorded rather than silently resolved in the source's favour.

"Added by an import" is decided from the node's own provenance, not from mtimes
or from which file happens to be larger. Where both copies came from an import,
the one in the family with more species keeps it, which is the same tie-break the
genus dedupe uses.

Two species are the same taxon when either the tree's own id says so, or an
external authority does. The second test is new and much stronger: 4,455 pairs
of our species share a GBIF usageKey within one kingdom, which is GBIF saying
they are one taxon rather than us inferring it from a name. Every previous
dedupe this session ran on name or id heuristics.

Cross-kingdom collisions are excluded by construction, because they are a
kingdom-placement disagreement rather than a duplicate -- 67 of the 4,522
collisions are of that kind, and the 7 deliberately undecided placements
(Cincloramphus, Poodytes, Oryzoborus) are left alone.

Idempotent.

    python3 scripts/dedupeSpeciesAcrossFamilies.py
    python3 scripts/dedupeSpeciesAcrossFamilies.py --apply
"""
import argparse
import collections
import glob
import json
import os
import sys

KINGDOM_DIR = "taxonomy"
IMPORTED = {"checklistbank", "catalogue of life"}


def walk_species(doc):
    """(owning genus, species) for every species, at any nesting depth.

    This was a single level deep -- top-level children, then their children --
    which silently skipped every family whose top-level children are SUBFAMILY or
    TRIBE nodes rather than GENUS. 143,300 of our 1,680,516 animalia species sit
    under such a node, so the deduper was blind to them and reported 7 duplicate
    ids where there were 22. A tool that reports "nothing to do" is the most
    dangerous kind, because it is indistinguishable from a clean tree.
    """
    def rec(node):
        for g in node.get("children") or []:
            for s in g.get("children") or []:
                if s.get("rank") == "SPECIES":
                    yield g, s
            for s in g.get("speciesList") or []:
                yield g, s
            if g.get("rank") != "SPECIES":
                yield from rec(g)
    yield from rec(doc)


def count_species(node):
    """Recursive, because families nest under subfamilies and buildData
    compresses minimal species into speciesList at every level."""
    n = len(node.get("speciesList") or [])
    for c in node.get("children") or []:
        n += 1 if c.get("rank") == "SPECIES" else count_species(c)
    return n


def genus_count(node):
    n = 0
    for c in node.get("children") or []:
        n += 1 if c.get("rank") == "GENUS" else genus_count(c)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", default="",
                    help="default: every kingdom, which is what verifyTree.py "
                         "checks. Scoping this to one kingdom is how 4,310 "
                         "plantae duplicates went unnoticed next to a clean "
                         "animalia run.")
    args = ap.parse_args()

    kingdoms = ([args.kingdom] if args.kingdom else
                ("animalia", "plantae", "fungi", "chromista", "protozoa",
                 "archaea"))
    where = collections.defaultdict(list)
    by_authority = collections.defaultdict(list)
    docs = {}
    for f in [x for k in kingdoms
              for x in glob.glob(f"{KINGDOM_DIR}/{k}/**/src/data/*.json",
                                 recursive=True)]:
        kingdom = f.split(f"{KINGDOM_DIR}/")[1].split("/")[0]
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        docs[f] = d
        for _g, s in walk_species(d):
            if s.get("id"):
                where[s["id"]].append((f, s))
                # authority identity, which needs no name judgement at all
                for auth, key in (s.get("sourceIds") or {}).items():
                    if key:
                        by_authority[(kingdom, auth, str(key))].append((f, s))

    dupes = {i: v for i, v in where.items() if len(v) > 1}
    print(f"  {'+'.join(kingdoms)}: {len(where):,} species ids, "
          f"{len(dupes):,} held in more than one family")

    # An authority-keyed collision is a duplicate without any name judgement:
    # GBIF issued that usageKey, so the two records are one taxon. Reported
    # separately from id collisions because the two sets barely overlap and the
    # authority one is the trustworthy one.
    # Same-file collisions count too. The first pass filtered to cross-file only
    # and left 107 behind, all of one kind: an authority written "&" inline and
    # "and" in the authorship field, which node_id reduces differently --
    # SP_CHUNIPHYES_MULTIDENTATA_LENS_AND_VAN_RIEMSDIJK_1908 beside
    # SP_CHUNIPHYES_MULTIDENTATA_LENS_VAN_RIEMSDIJK_1908 -- so one taxon had two
    # ids in one genus. GBIF says they are one; we were holding both.
    auth_groups = {}
    for (kingdom, auth, key), places in by_authority.items():
        if len(places) > 1:
            auth_groups.setdefault(kingdom, []).append((auth, key, places))
    n_auth = sum(len(v) for v in auth_groups.values())
    if n_auth:
        print(f"  authority-proven duplicates: {n_auth:,} "
              f"(same kingdom, same external id)")
        for kingdom, groups in list(auth_groups.items())[:3]:
            auth, key, places = groups[0]
            print(f"      e.g. {kingdom}/{auth} {key}: "
                  + ", ".join(sorted({(n.get('name') or '') for _f, n in places})[:2]))

    drops = collections.defaultdict(set)      # file -> set(species id)
    keep_report = collections.Counter()
    for kingdom, groups in auth_groups.items():
        for auth, key, places in groups:
            # keep the richest node, break ties on the file that is not the
            # first alphabetically so the survivor is deterministic
            def score(fp):
                n = fp[1]
                nm = (n.get("name") or "").strip()
                au = (n.get("authorship") or "").strip()
                conforming = not (au and len(nm) > len(au) + 2
                                  and nm.endswith(au))
                return (conforming,
                        sum(1 for k in ("description", "commonName", "continents",
                                        "reference", "yearPublished")
                            if n.get(k)),
                        fp[0])

            winner = max(places, key=score)
            for f, n in places:
                if (f, n) is winner:
                    continue
                drops[f].add(n["id"])
            keep_report[f"collapsed on {auth} id"] += 1

    for sid, places in dupes.items():
        files = {f for f, _ in places}
        imported = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") in IMPORTED]
        native = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") not in IMPORTED]
        if native and imported:
            # keep the copy we already had; drop every import-written one
            for f, _s in imported:
                drops[f].add(sid)
            keep_report["dropped an imported copy, kept the existing one"] += 1
            continue
        if len(imported) > 1:
            # both from imports: the bigger family keeps it
            sizes = {f: count_species(docs[f]) for f, _s in imported}
            win = max(sizes, key=lambda f: sizes[f])
            for f, _s in imported:
                if f != win:
                    drops[f].add(sid)
            keep_report["both imported; the larger family kept it"] += 1
            continue
        keep_report["left alone (no imported copy)"] += 1

    for k, v in keep_report.items():
        print(f"    {v:>4}  {k}")
    print(f"  species to remove: {sum(len(v) for v in drops.values()):,} "
          f"from {len(drops)} files")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    touched = 0
    removed = 0
    for f, ids in drops.items():
        d = docs[f]

        def prune(node):
            # `removed` is a local of main(), so this needs nonlocal -- with
            # `global` it raises NameError the first time prune runs, which is
            # after the family file has been mutated in memory and before it is
            # written, so --apply died on the first family.
            nonlocal removed
            if node.get("children"):
                before = len(node["children"])
                node["children"] = [s for s in node["children"]
                                    if s.get("id") not in ids]
                removed += before - len(node["children"])
            if node.get("speciesList"):
                before = len(node["speciesList"])
                node["speciesList"] = [s for s in node["speciesList"]
                                       if s.get("id") not in ids]
                removed += before - len(node["speciesList"])
            kept = []
            for g in node.get("children") or []:
                if g.get("rank") == "SPECIES":
                    continue
                prune(g)
                if g.get("children") or g.get("speciesList"):
                    kept.append(g)
            node["children"] = kept

        prune(d)
        d["children"] = [g for g in d.get("children") or [] if g.get("children")]
        d["speciesCount"] = count_species(d)
        d["genusCount"] = genus_count(d)
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        touched += 1
    print(f"\n  wrote {touched} family files, removed {removed} species copies")
    return 0


if __name__ == "__main__":
    sys.exit(main())