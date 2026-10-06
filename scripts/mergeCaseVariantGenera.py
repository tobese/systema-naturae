#!/usr/bin/env python3
"""
Merge genus nodes whose names differ only in letter case.

What this is
------------
`fixMalformedIds.py` held back two genus pairs because normalising their ids
would have produced a genuine duplicate rather than removing one. Both are the
same genus listed twice in one family file, differing only in capitalisation:

    Annonaceae     Neo-Uvaria (2 species)   +   Neo-uvaria (3 species)
    Brassicaceae   Solms-Laubachia (1 sp.)  +   Solms-laubachia (34 spp.)

Both copies carry species and the sets are **disjoint**, so this is redundancy,
not a conflict. A reader sees two genera where there is one.

Why the existing merge missed them
----------------------------------
`merge_duplicate_genera.py` groups genus nodes by `name`, so it sees two
distinct names and reports nothing. Its own docstring records that keying on
anything coarser is unsafe -- grouping by parent *id* conflates kingdoms,
counting by position conflates genera that merely share a name -- and casefolded
name is no safer a key in general.

What makes it safe *here* is that both pairs sit inside a single family file, so
"same genus name, casefolded, twice in one family" cannot be a homonym across
kingdoms. The rule is still scoped tightly: same family file, same casefolded
name, two copies. It will not merge `Schulzia` (Molineidae) with `Schulzia`
(Apiaceae), which are a nematode and a flowering plant.

Which copy survives
-------------------
**The better-formed name**, not the more populous node. A first version kept the
larger copy and got both cases wrong: it kept `Solms-laubachia` (34 species) over
`Solms-Laubachia` (1), and `Neo-uvaria` (3) over `Neo-Uvaria` (2). Species count
says nothing about which spelling is correct -- these are duplicate *nodes*, and
the larger one is often the copy with a corrupt or generated name.

The tiebreak is explicit rather than clever:

1. prefer the name with an internal capital after a hyphen (`Solms-Laubachia`,
   `Neo-Uvaria` -- both confirmed against GBIF, where `Neo-Uvaria
   acuminatissima` matches `EXACT`/`ACCEPTED`)
2. otherwise prefer the more populous copy
3. otherwise prefer lexicographically, so the result is deterministic

The species *are* all unioned either way, so the choice affects only which string
the genus node ends up carrying. Where a species appears in both copies the
longer description wins with its `sourcedFrom` -- the rule
`merge_duplicate_genera.py` uses, for the same reason: a copy holding the only
prose must not lose it.

Species names are **not** recased. `Neo-uvaria laosensis` sits under a genus node
now called `Neo-Uvaria`; that inconsistency is visible and is a taxonomy decision
rather than a cleanup, exactly as with the MycoBank renames. Fixing the ids and
genus node and leaving the epithets alone is the reversible half.

    python3 scripts/mergeCaseVariantGenera.py            # dry run
    python3 scripts/mergeCaseVariantGenera.py --apply

Read-only unless `--apply`. Idempotent.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import species_ids  # noqa: E402


def better(a: dict, b: dict) -> dict:
    """The copy with the longer description, keeping its sourcedFrom with it."""
    da = (a.get("description") or "").strip()
    db = (b.get("description") or "").strip()
    return a if len(da) >= len(db) else b




def merge(base: dict, other: dict) -> tuple[dict, int]:
    """Union other's species into base. Returns (base, species_added)."""
    have = species_ids(base)
    added = 0
    for key in ("children", "speciesList"):
        for s in other.get(key) or []:
            if s.get("rank") != "SPECIES":
                continue
            sid = s.get("id")
            if sid in have:
                # Present in both copies: keep the richer description.
                for lst in ("children", "speciesList"):
                    bucket = base.get(lst) or []
                    for i, existing in enumerate(bucket):
                        if existing.get("id") == sid:
                            merged = better(existing, s)
                            if merged is not existing:
                                base[lst][i] = merged
                            break
            else:
                base.setdefault(key, []).append(s)
                have.add(sid)
                added += 1
    return base, added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = []
    for dirpath, _d, names in os.walk(args.root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    files.sort()

    merges = 0
    species_added = 0
    detail = []
    started = time.time()

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        kids = doc.get("children") or []
        if len(kids) < 2:
            continue

        # Casefolded, within this one family file only.
        by_fold: dict[str, list] = defaultdict(list)
        for c in kids:
            n = (c.get("name") or "").strip()
            if n and c.get("rank") == "GENUS":
                by_fold[n.casefold()].append(c)
        groups = {k: v for k, v in by_fold.items()
                  if len(v) > 1 and len({c["name"] for c in v}) > 1}

        if not groups:
            continue

        before = species_ids_all(kids)
        for _fold, copies in groups.items():
            # The better-formed name wins; see the module docstring. A hyphenated
            # capital is the strongest signal of deliberate authorship, so it
            # outranks species count, which is a poor proxy here.
            def rank_key(c):
                name = c.get("name") or ""
                well_formed = bool(re.search(r"-[A-Z]", name))
                return (0 if well_formed else 1, -len(species_ids(c)), name)

            copies.sort(key=rank_key)
            base, others = copies[0], copies[1:]
            added = 0
            for o in others:
                base, n = merge(base, o)
                added += n
            detail.append((doc.get("name"), [c["name"] for c in copies],
                           base["name"], added))
            species_added += added
            merges += 1

        after = species_ids_all(doc.get("children") or [])
        # The invariant that matters: a merge removes a redundant NODE. It must
        # neither drop a species nor invent one.
        if before != after:
            sys.exit(f"FATAL: {path}\n  species set changed: "
                     f"{len(before - after)} lost, {len(after - before)} gained. "
                     f"Refusing to write a lossy merge.")

        doc["children"] = [c for c in (doc.get("children") or [])
                           if not any(c is o for _f, copies in groups.items()
                                      for o in copies[1:])]
        if args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    print(f"Scanned {len(files):,} family files in {time.time()-started:.0f}s\n")
    if not detail:
        print("  no case-variant duplicate genera found")
        return 0
    print(f"  genus merges:      {merges:>5,}")
    print(f"  species added:     {species_added:>5,}\n")
    for fam, names_, kept, added in detail:
        print(f"  {fam}: {' + '.join(repr(n) for n in names_)}")
        print(f"      kept {kept!r}, folded in {added} species")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


def species_ids_all(genus_list: list) -> set:
    out = set()
    for g in genus_list:
        out |= species_ids(g)
    return out


if __name__ == "__main__":
    sys.exit(main())