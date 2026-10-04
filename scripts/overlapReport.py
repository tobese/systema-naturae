#!/usr/bin/env python3
"""How much of a ColDP archive would actually be new to this tree?

Run before importing anything from a new checklist, because the answer is
rarely the row count. Wikidata Species announces 3,262,898 species; the question
is how many we do not already hold, measured with the *same test the importers
use* rather than a raw string comparison.

That distinction is not pedantry. `importColStage2.py`'s docstring records two
rounds of scope measurement coming out wrong because names were compared before
GNparser normalisation: COL writes subgenus trinomials (`Aloconota (Aloconota)
tenerrima`) where we store `Aloconota tenerrima`, and read as raw strings those
look like 96,000 missing animalia species we already hold. So every comparison
here goes through `taxamatch.parse_names` first, in chunks, and the held/new
test is `canonical()`'s: all four spellings of the hybrid marker, against the
canonical index, plus a `placed` set so a name Wikidata lists under two QIDs
does not get counted twice.

Reports, for the new species only, whether the archive could actually place
them: a family chain that resolves lands in a real family, a genus-only chain
needs the genus lookup, and neither lands in an `Incertae sedis` placeholder --
which is the difference between an import that extends the tree and one that
mostly manufactures placeholders.

    python3 scripts/overlapReport.py ~/Downloads/wikidata.zip
    python3 scripts/overlapReport.py ~/Downloads/wikidata.zip --limit 400000
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames as C  # noqa: E402
import coldp  # noqa: E402
import taxamatch  # noqa: E402

# the four spellings importColStage2.canonical() tries
FORMS = ("{g} \u00d7{s}", "{g} {s}", "{g} \u00d7{s}", "{g} \u00d7 {s}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--chunk", type=int, default=400_000,
                    help="names per GNparser invocation")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    print(f"  archive: {os.path.basename(args.archive)} "
          f"({os.path.getsize(args.archive) / 1e6:.0f} MB)")
    md = coldp.metadata(args.archive)
    print(f"  {md.get('title', '?')}  issued {md.get('issued', '?')}  "
          f"licence {md.get('license', '?')}")

    print("  reading core ...", flush=True)
    par, rank, name, _extra = coldp.load_core(args.archive,
                                              want_authorship=False)
    print(f"  accepted name usages: {len(par):,}", flush=True)

    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())
    print(f"  our canonical index: {len(canon):,} names")

    # species, with the root they hang off so the report can break down by
    # kingdom -- Wikidata's roots are not the ones our tree uses, so the root is
    # reported as-is and labelled, not mapped
    species = []
    for t, r in rank.items():
        if r == "species" and name.get(t):
            species.append(t)
    print(f"  species: {len(species):,}", flush=True)

    placed = set()
    stats = collections.Counter()
    new_by_root = collections.Counter()
    tot_by_root = collections.Counter()
    chain_of = collections.Counter()
    examples = collections.defaultdict(list)

    for start in range(0, len(species), args.chunk):
        batch = species[start:start + args.chunk]
        names = [name[t] for t in batch]
        parsed = taxamatch.parse_names(names)
        for t in batch:
            nm = name[t]
            root = name.get(coldp.root_of(t, par)) or "(no root)"
            tot_by_root[root] += 1
            p = parsed.get(nm) or {}
            g, s = p.get("genus"), p.get("species")
            if not s:
                parts = [x for x in nm.replace("\u00d7", " ").split()
                         if x.lower() != "x"]
                if len(parts) >= 2:
                    g, s = parts[0], parts[1]
            if not g or not s:
                stats["not binominal"] += 1
                continue
            bare = f"{g} \u00d7{s}" if "\u00d7" in nm else f"{g} {s}"
            if any(f.format(g=g, s=s).lower() in canon
                   or f.format(g=g, s=s).lower() in placed for f in FORMS):
                stats["already held"] += 1
                continue
            if bare.lower() in placed:
                stats["duplicate within the archive"] += 1
                continue
            placed.add(bare.lower())
            stats["NEW"] += 1
            new_by_root[root] += 1
            ch = coldp.chain(t, par, rank, name)
            if ch.get("family") and ch.get("order"):
                where = "family chain resolves"
            elif ch.get("family"):
                where = "family but no order"
            else:
                where = "no family (genus lookup or Incertae sedis)"
            chain_of[where] += 1
            if len(examples[where]) < 6:
                examples[where].append(f"{nm} [{ch.get('family') or '-'}]")
        done = min(start + args.chunk, len(species))
        print(f"    {done:,}/{len(species):,} species  "
              f"new={stats['NEW']:,}  held={stats['already held']:,}",
              flush=True)

    total = len(species)
    print("\n  === overlap with the current tree ===")
    for k in ("already held", "NEW", "duplicate within the archive",
              "not binominal"):
        print(f"    {k:32s} {stats[k]:>10,}  {stats[k] / total * 100:5.1f}%")
    print(f"    {'species total':32s} {total:>10,}")

    print("\n  === where the new species would go ===")
    for k, v in chain_of.most_common():
        print(f"    {k:44s} {v:>9,}")
        for e in examples[k]:
            print(f"        {e}")

    print("\n  === new species by Wikidata root (top 20) ===")
    for r, v in new_by_root.most_common(20):
        print(f"    {r:44s} {v:>9,}  of {tot_by_root[r]:>9,}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"archive": os.path.basename(args.archive),
                       "metadata": {k: md.get(k) for k in
                                    ("title", "issued", "license")},
                       "accepted_name_usages": len(par),
                       "species": total,
                       "already_held": stats["already held"],
                       "new": stats["NEW"],
                       "duplicate_within_archive":
                           stats["duplicate within the archive"],
                       "not_binominal": stats["not binominal"],
                       "placement": dict(chain_of),
                       "new_by_root": dict(new_by_root),
                       "total_by_root": dict(tot_by_root)}, fh, indent=1)
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())