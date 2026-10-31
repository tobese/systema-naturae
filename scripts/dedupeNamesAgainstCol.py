#!/usr/bin/env python3
"""Remove species filed under the same binomial in two families of one
kingdom, where the Catalogue of Life says which family is right.

Dry run by default: writes a plan and changes nothing. `--apply` writes,
holding `maintenanceLock` for the whole run (scan included, so the plan and
the writes see the same files).

`dedupeSpeciesAcrossFamilies.py` groups copies by tree id or a shared external
key (a GBIF usageKey). Neither sees a copy that differs in both: the tree id
embeds the authorship (SP_CYMOSAFIA_DOLOROSA_K_HLER_1979 beside
SP_CYMOSAFIA_DOLOROSA) and the two copies came from different sources (a COL
id beside a Wikidata QID). Measured 2026-10-31: 123,686 animalia binomials sit
in more than one family -- 6,512 between Erebidae and Noctuidae alone, an old
and a new circumscription both kept as families.

A name match alone is not proof of one taxon: a binomial can be a homonym.
So a group qualifies only when COL accepts the binomial in exactly ONE family
of that kingdom and we hold a copy in that family. The authority then decides
both questions at once -- that it is one taxon, and where it belongs -- the
same role `--authority-family` gives GBIF in the id-based dedupe. Against the
2026-10-31 tree that is 130,799 groups. Not touched, only counted:

  * COL accepts the binomial in 2+ families (a homonym COL recognises);
  * COL holds it only as a synonym (a synonym filed as a species -- a
    different problem from a duplicate);
  * COL accepts it in a family we hold no copy in;
  * COL does not have it (the genus register can say more, but at genus
    level only: that is weaker evidence and is left for a later pass).

Within a qualifying group:

  * every copy in COL's family is kept (two copies inside one file are
    `verifyTree.check_duplicate_species`' business, not this script's);
  * every copy elsewhere is planned for removal, its `sourceIds` merged
    into the kept copy, and any MERGEABLE field the kept copy lacks carried
    across -- the same fields and rule as dedupeSpeciesAcrossFamilies.py's
    `merge_into`, which an --apply here should share rather than copy;
  * a copy with child nodes (subspecies) skips the whole group: a rule about
    duplicate species must never delete a subspecies.

`--weak-only` narrows removal to copies whose only provenance is the Wikidata
Species import (or that carry no sourceIds at all), and only beside a kept copy
that carries a COL id: the weakest-sourced copy against the strongest, which
needs no decision about whose classification is current. Decided 2026-10-31 as
the first pass; the full set waits on a per-family-pair review, because in
some pairs COL lags current usage (Ectobiidae -> Blattellidae, 1,010 copies).

Apply safeguards, after dedupeSpeciesAcrossFamilies.py's 2026-10 prune bug
(351,882 species destroyed while the report claimed 8,745):

  * a copy is removed by object identity, found by id + name; an id that
    matches more than one node in its file skips that copy;
  * only containers emptied by these removals are pruned, never others;
  * each file's species count must drop by exactly its planned removals,
    and planned must equal removed + skipped, or nothing is written.

    python3 scripts/dedupeNamesAgainstCol.py
    python3 scripts/dedupeNamesAgainstCol.py --weak-only
    python3 scripts/dedupeNamesAgainstCol.py --weak-only --apply
    python3 scripts/dedupeNamesAgainstCol.py --kingdom animalia
"""
import argparse
import collections
import csv
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
import sources  # noqa: E402
from dedupeSpeciesAcrossFamilies import merge_into  # noqa: E402
from tree import (KINGDOMS, count_rank, count_species, iter_family_files,  # noqa: E402
                  iter_species, save_json)

# The Wikidata Species import (ChecklistBank 314569); see
# quarantineSourceAdditions.py, written for the same source.
WIKIDATA = "ac5f72cf-172d-4eb4-ad8c-db66ea1c78e5"

COL_DWCA = os.path.join(sources.ROOT, "archives", "catalogue-of-life-2025",
                        "col2026-base_dwca.zip")

# What the dry run reports as carried; --apply uses merge_into itself, which
# also carries extinct and subspeciesCount.
MERGEABLE = ("description", "commonName", "continents", "reference",
             "yearPublished", "namedAfter", "namedAfterDetail",
             "wikipediaUrl", "iucnStatus")

COL_KINGDOMS = {"Animalia", "Plantae", "Fungi", "Chromista", "Protozoa",
                "Archaea", "Bacteria", "Viruses"}


def col_accepted_families(path):
    """binomial (lowercase) -> {kingdom: {family}} for accepted species.

    COL's DwCA has no family column, only parent links, so the family is
    found by walking up -- memoised, since siblings share every ancestor.
    """
    csv.field_size_limit(10 ** 8)
    node = {}
    with zipfile.ZipFile(path) as z, z.open("Taxon.tsv") as fh:
        rd = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"),
                        delimiter="\t", quoting=csv.QUOTE_NONE)
        ix = {h.split(":")[-1]: i for i, h in enumerate(next(rd))}
        for r in rd:
            node[r[ix["taxonID"]]] = (r[ix["parentNameUsageID"]],
                                      r[ix["taxonRank"]],
                                      r[ix["scientificName"]],
                                      r[ix["taxonomicStatus"]])
    memo = {}

    def above(tid):
        path, fam, king, cur = [], None, None, tid
        while cur and cur in node:
            if cur in memo:
                f, k = memo[cur]
                fam, king = fam or f, king or k
                break
            path.append(cur)
            parent, rank, name, _ = node[cur]
            if rank == "family" and not fam:
                fam = name.split()[0].lower()
            if rank == "kingdom":
                first = name.split()[0]
                king = first.lower() if first in COL_KINGDOMS else None
                break
            cur = parent
        for t in path:
            memo[t] = (fam, king)
        return fam, king

    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for tid, (_p, rank, name, status) in node.items():
        if rank != "species" or len(name.split()) != 2:
            continue
        if status not in ("accepted", "provisionally accepted"):
            continue
        fam, king = above(tid)
        if fam and king:
            out[name.lower()][king].add(fam)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kingdom", default="", help="default: every kingdom")
    ap.add_argument("--plan", default=os.path.join(
        sources.ROOT, "work", "dedupe-names-against-col", "plan.jsonl"))
    ap.add_argument("--weak-only", action="store_true",
                    help="remove only Wikidata-only / unsourced copies beside a "
                         "COL-sourced kept copy (see module docstring)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print(f"  reading {COL_DWCA}")
    col = col_accepted_families(COL_DWCA)
    print(f"  {len(col):,} accepted COL binomials")

    os.makedirs(os.path.dirname(args.plan), exist_ok=True)
    plan = open(args.plan, "w", encoding="utf-8")
    kingdoms = [args.kingdom] if args.kingdom else KINGDOMS
    grand = collections.Counter()
    planned = []
    for k in kingdoms:
        by = collections.defaultdict(list)
        for fam in iter_family_files(k):
            for sp in iter_species(fam.load()):
                n = (sp.get("name") or "").replace("†", "").strip().lower()
                if len(n.split()) == 2:
                    by[n].append((fam, sp))

        stat = collections.Counter()
        pairs = collections.Counter()
        carried = collections.Counter()
        for n, copies in by.items():
            fams = {f.slug for f, _ in copies}
            if len(fams) < 2:
                continue
            stat["groups"] += 1
            accepted = col.get(n, {}).get(k, set())
            if len(accepted) != 1:
                stat["skipped: COL accepts it in 0 or 2+ families"] += 1
                continue
            target = next(iter(accepted))
            if target not in fams:
                stat["skipped: COL's family holds no copy of ours"] += 1
                continue
            if any(sp.get("children") for _, sp in copies):
                stat["skipped: a copy has child nodes"] += 1
                continue
            keep = [(f, sp) for f, sp in copies if f.slug == target]
            drop = [(f, sp) for f, sp in copies if f.slug != target]
            keeper = keep[0][1]
            if args.weak_only:
                if "col" not in (keeper.get("sourceIds") or {}):
                    stat["skipped (weak-only): kept copy has no COL id"] += 1
                    continue
                drop = [(f, sp) for f, sp in drop
                        if set(sp.get("sourceIds") or {}) <= {WIKIDATA}]
                if not drop:
                    stat["skipped (weak-only): every other copy is better sourced"] += 1
                    continue
            moved = []
            for field in MERGEABLE:
                if not keeper.get(field) and any(sp.get(field) for _, sp in drop):
                    moved.append(field)
                    carried[field] += 1
            new_ids = sum(1 for _, sp in drop for src in (sp.get("sourceIds") or {})
                          if src not in (keeper.get("sourceIds") or {}))
            stat["planned groups"] += 1
            stat["copies to remove"] += len(drop)
            stat["removed copies with a description"] += sum(
                1 for _, sp in drop if sp.get("description"))
            for f, _ in drop:
                pairs[(f.slug, target)] += 1
            planned.append((k, n, keep[0][0].path, keeper.get("id"),
                            [(f.path, sp.get("id")) for f, sp in drop]))
            plan.write(json.dumps({
                "kingdom": k, "name": n, "colFamily": target,
                "keep": [{"family": f.slug, "path": os.path.relpath(f.path),
                          "id": sp.get("id"), "authorship": sp.get("authorship")}
                         for f, sp in keep],
                "remove": [{"family": f.slug, "path": os.path.relpath(f.path),
                            "id": sp.get("id"), "authorship": sp.get("authorship"),
                            "sourceIds": sp.get("sourceIds") or {}}
                           for f, sp in drop],
                "carryFields": moved, "newSourceIdKeys": new_ids,
            }, ensure_ascii=False) + "\n")

        grand.update({key: v for key, v in stat.items()})
        print(f"\n== {k}: {stat['groups']:,} binomials in 2+ families")
        for key in ("planned groups", "copies to remove",
                    "removed copies with a description",
                    "skipped: COL accepts it in 0 or 2+ families",
                    "skipped: COL's family holds no copy of ours",
                    "skipped: a copy has child nodes",
                    "skipped (weak-only): kept copy has no COL id",
                    "skipped (weak-only): every other copy is better sourced"):
            print(f"   {stat[key]:9,}  {key}")
        if carried:
            print("   fields the kept copy would gain: " + ", ".join(
                f"{f} {c:,}" for f, c in carried.most_common()))
        if pairs:
            print("   most removals, from -> kept in:")
            for (a, b), c in pairs.most_common(12):
                print(f"   {c:9,}  {a} -> {b}")
    plan.close()
    print(f"\n  total: {grand['planned groups']:,} groups, "
          f"{grand['copies to remove']:,} copies to remove")
    if not args.apply:
        print(f"  plan: {args.plan}  (dry run -- nothing written to the tree)")
        return 0
    print(f"  plan: {args.plan}")
    return apply(planned)


def _index(doc):
    """id -> [species node] for every species, and child -> (parent, list key)
    for every node, keyed by object identity."""
    by_id = collections.defaultdict(list)
    parent_of = {}
    stack = [doc]
    while stack:
        node = stack.pop()
        for key in ("children", "speciesList"):
            for child in node.get(key) or []:
                parent_of[id(child)] = (node, key)
                if child.get("rank") == "SPECIES":
                    by_id[child.get("id")].append(child)
                stack.append(child)
    return by_id, parent_of


def apply(planned):
    docs, index, before = {}, {}, {}

    def find(path, node_id, name):
        if path not in docs:
            with open(path, encoding="utf-8") as fh:
                docs[path] = json.load(fh)
            index[path] = _index(docs[path])
            before[path] = count_species(docs[path])
        hits = [n for n in index[path][0].get(node_id, ())
                if (n.get("name") or "").replace("\u2020", "").strip().lower() == name]
        return hits[0] if len(hits) == 1 else None

    removed_from = collections.Counter()
    emptied = {}
    skipped = collections.Counter()
    for _k, name, keep_path, keep_id, drops in planned:
        keeper = find(keep_path, keep_id, name)
        if keeper is None:
            skipped["kept copy not found exactly once"] += len(drops)
            continue
        for path, node_id in drops:
            loser = find(path, node_id, name)
            if loser is None:
                skipped["copy to remove not found exactly once"] += 1
                continue
            merge_into(keeper, loser)
            parent, key = index[path][1][id(loser)]
            parent[key] = [c for c in parent[key] if c is not loser]
            removed_from[path] += 1
            emptied[id(parent)] = (path, parent)

    # Prune only what these removals emptied, walking up while empty: a genus
    # left with nothing, then a subfamily/tribe left with nothing -- never the
    # family root, never a container this run did not empty.
    pruned = 0
    for path, node in emptied.values():
        parent_of = index[path][1]
        while (node is not docs[path] and node.get("rank") != "FAMILY"
               and not node.get("children") and not node.get("speciesList")):
            up, key = parent_of[id(node)]
            up[key] = [c for c in up[key] if c is not node]
            pruned += 1
            node = up

    bad = 0
    for path, doc in docs.items():
        after = count_species(doc)
        if before[path] - after != removed_from.get(path, 0):
            print(f"  MISMATCH {path}: {before[path]:,} -> {after:,}, "
                  f"planned to remove {removed_from.get(path, 0):,}")
            bad += 1
    planned_n = sum(len(d) for *_, d in planned)
    removed = sum(removed_from.values())
    if removed + sum(skipped.values()) != planned_n:
        print(f"  MISMATCH: removed {removed:,} + skipped "
              f"{sum(skipped.values()):,} != planned {planned_n:,}")
        bad += 1
    if bad:
        print("  NOTHING written")
        return 1

    for path, doc in docs.items():
        doc["speciesCount"] = count_species(doc)
        doc["genusCount"] = count_rank(doc, "GENUS")
        save_json(path, doc)
    print(f"\n  wrote {len(docs):,} family files: removed {removed:,} copies "
          f"(planned {planned_n:,}), pruned {pruned:,} emptied containers")
    for why, n in skipped.items():
        print(f"  skipped {n:,}: {why}")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        with maintenanceLock.hold_exclusive():
            sys.exit(main())
    sys.exit(main())
