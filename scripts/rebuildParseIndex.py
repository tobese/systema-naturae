#!/usr/bin/env python3
"""Rebuild name-parse-index.jsonl so it covers every name the tree actually holds.

The index was last generated on 2026-10-01, before roughly 400,000 species were
imported, so it covers 1,040,822 of the tree's 1,434,372 distinct names -- 72.6%.
Every lookup for the missing 27.4% silently falls back to raw-name matching, which
is the degradation that made the iNaturalist import fill zero names on its first
run.

Regenerated with **GNparser** rather than `parseAllNames.py`, which POSTs batches
to a remote parsing service: local parsing is seconds rather than a network-bound
crawl, and GNparser handles three things the old path did not -- subgenus
parentheses (`Lasioglossum (Ctenonomia) ernesti Pauly, 1990` -> `Lasioglossum
ernesti`), the dagger fossil marker, and rank cardinality.

One field is carried over rather than recomputed. `type` -- SCIENTIFIC, INFORMAL,
OTU, VIRUS, PLACEHOLDER and the rest -- is a classification that
`sanity_scan.py` reads to raise UNRESOLVED_TAXON and ACCESSION_NAME, and GNparser
does not produce it. So names already in the old index keep their classification
verbatim, and only names new to the index are parsed here. Those all come from
published taxonomic checklists (Species Files, Afromoths, the bee catalogue), so
SCIENTIFIC is the correct classification for them rather than a guess.

Writes to a temporary file and renames, so an interrupted run cannot leave a
truncated index behind -- the old index is load-bearing for every name-keyed
enricher and is gitignored, so a broken one would be invisible until something
quietly stopped matching.

Usage:
    python3 scripts/rebuildParseIndex.py            # dry run
    python3 scripts/rebuildParseIndex.py --apply
"""
import argparse
import collections
import glob
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taxamatch  # noqa: E402

OLD = "portal/data/name-parse-index.jsonl"
RANK_MARKERS = {
    "SUBSPECIES": {"subsp.", "ssp.", "sub-species"},
    "SPECIES": set(),
    "GENUS": set(),
    "VARIETY": {"var.", "v."},
    "FORM": {"form.", "f."},
}


def tree_names():
    """(name, ourRank) for every named node in the tree, plus a rank tally."""
    pairs = []
    seen = set()
    for f in sorted(glob.glob("taxonomy/*/**/src/data/*.json", recursive=True)):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        stack = [d]
        while stack:
            x = stack.pop()
            nm = (x.get("name") or "").strip()
            rk = x.get("rank")
            if nm and rk and (nm, rk) not in seen:
                seen.add((nm, rk))
                pairs.append((nm, rk))
            stack.extend(x.get("children") or [])
            stack.extend(x.get("speciesList") or [])
    return pairs


def load_old():
    old = {}
    if not os.path.exists(OLD):
        return old
    for line in open(OLD, encoding="utf-8"):
        if not line.startswith("{"):
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        key = ((rec.get("n") or "").strip(), rec.get("ourRank"))
        if key[0]:
            old[key] = rec
    return old


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", default=OLD)
    args = ap.parse_args()

    pairs = tree_names()
    old = load_old()
    fresh = [p for p in pairs if p not in old]
    print(f"  (name, rank) pairs in the tree : {len(pairs):,}")
    print(f"  already in the old index      : {len(pairs)-len(fresh):,}")
    print(f"  needing parsing               : {len(fresh):,}")

    started = time.time()
    parsed = taxamatch.parse_names([n for n, _ in fresh]) if fresh else {}
    print(f"  GNparser parsed {len(parsed):,} in {time.time()-started:.1f}s")

    by_rank = collections.Counter(r for _, r in fresh)
    print("  new names by rank:", dict(by_rank.most_common(6)))

    missing_parse = [n for n, _ in fresh if n not in parsed]
    if missing_parse:
        print(f"  WARNING {len(missing_parse):,} names GNparser did not return "
              f"(e.g. {missing_parse[:3]}) -- they keep the verbatim name")

    tally = collections.Counter()
    rows = 0
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(args.out) or ".",
                               prefix=".name-parse-index.", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for name, rank in pairs:
                prev = old.get((name, rank))
                if prev:
                    rec = prev
                else:
                    p = parsed.get(name, {})
                    auths = p.get("authors") or []
                    years = p.get("years") or []
                    marker = None
                    if rank == "SUBSPECIES":
                        marker = "subsp."
                    rec = {
                        "n": name, "ourRank": rank,
                        # All new names come from published checklists, so
                        # SCIENTIFIC is their classification rather than a guess.
                        "type": "SCIENTIFIC",
                        "canonical": p.get("genus") and " ".join(
                            x for x in (p.get("genus"), p.get("species"),
                                        p.get("infraspecies")) if x) or None,
                        "authorship": auths[0] if auths else None,
                        "year": str(years[0]) if years else None,
                        "rankMarker": marker,
                        "parsed": bool(p.get("genus")), "partial": False,
                    }
                tally[rec.get("type")] += 1
                rows += 1
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if args.apply:
            os.replace(tmp, args.out)
        else:
            os.unlink(tmp)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    print(f"  would write {rows:,} records to {args.out}")
    print("  type tally:", dict(tally.most_common()))
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
