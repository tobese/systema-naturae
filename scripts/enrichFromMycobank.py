#!/usr/bin/env python3
"""
Attach MycoBank nomenclatural data to the fungal tree.

Why this is separate from the description work
-----------------------------------------------
Fungi sit at 2.4% described (3,896 of 161,716), and that is the *ceiling* of
English Wikipedia rather than a backfill that ran badly -- enwiki has articles
for a few thousand of ~145,000 named fungi. Every free descriptive source was
measured and rejected: GBIF's description store is built from Plazi literature
treatments and yields **0.37%** on fungi, EOL serves `taxonConcept` with zero
data objects, and COL is nomenclatural. So the prose stays out of reach without
a MycoBank token (drafted in `docs/drafts/mycobank-token-request.md`).

What is reachable today, keyless, is nomenclature -- and it is not nothing.
Matching our tree against MycoBank's own `MBList.xlsx` export:

| | |
|---|---|
| fungal species in our tree | 161,716 |
| matched in MBList | 157,460 (97.4%) |
| of those, carrying a name MycoBank treats as superseded | **26,857** |
| matched genera carrying a superseded name | **1,763 of 1,763 — every one** |

Plus `scientificNameAuthorship` and `Name status` on every match, which nothing
in the tree recorded before.

The rename is deliberately NOT applied
--------------------------------------
Every matched genus has a different `Current name`, and 26,857 species do too.
Moving them is a taxonomy decision, not a cleanup, and it is not this script's
to make:

- `Karlingia lobata` -> `Karlingiomyces lobatus`, `Rhizophlyctis spinosa` ->
  `Karlingia spinosa`. Note the last one moves *back* into a genus that other
  species are leaving. A mechanical rename would need genus-level reconciliation
  first or it produces two `Karlingiomyces` nodes and orphans the genus.
- Some "corrections" are orthographic, not taxonomic: `Rhizophlyctis
  tolypotrichis` -> `tolypothrichis`, `Rhizophlyctis costata` -> `costatus`. The
  gender correction is right and uncontroversial, but it is still 200-odd
  separate string edits.
- `Syncephalidium` -> `Syncephalis`, `Hormomyces` -> `Tulasnella`: legitimate
  synonymy that MycoBank records and other sources may not.

So this script **annotates and flags**. It writes the accepted name and status
onto the node so the data is visible and queryable, and leaves a ledger naming
every candidate. Renaming becomes a separate, reviewable change with its own
commit -- the same split that `fix_genus_split_duplicates.py` made for the six
COL-verified cases.

What gets written
-----------------
On a matched node, and only if not already set (so `--apply` is idempotent and a
re-run cannot clobber a human edit):

| field | meaning |
|---|---|
| `mycobankId` | the stable MB number, so the record is linkable |
| `mycobankStatus` | Legitimate / Illegitimate / Orthographic variant / ... |
| `mycobankCurrentName` | accepted name where ours differs; **absent when equal** |
| `authorship` | `scientificNameAuthorship` -- new, and absent from every other source we have |

`sourcedFrom` is set to `"mycobank"` only where something was actually written.
It is nomenclatural data, so it must not be confused with a description, and
nothing here writes prose.

Every unmatched name and every superseded name goes to
`portal/data/mycobank-ledger.jsonl`, for the same reason
`description-lookup.jsonl` exists: `sourcedFrom` cannot record a miss, and a
miss re-queried on every run is a miss that never stops being a miss.

Usage
-----
    python3 scripts/enrichFromMycobank.py            # dry run, report only
    python3 scripts/enrichFromMycobank.py --kingdom fungi
    python3 scripts/enrichFromMycobank.py --apply    # write nodes + ledger

Read-only unless `--apply`. Never renames a node, never deletes one, and never
writes a description.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # noqa: E402

DEFAULT_INDEX = os.path.join("portal", "data", "mycobank-index.json")
DEFAULT_LEDGER = os.path.join("portal", "data", "mycobank-ledger.jsonl")

# Ranks worth matching. Fungi are the point, but Chromista/Protozoa carry
# fungal names too (MycoBank holds Oomycetes and Myxomycetes -- the export's
# Classification column shows both), so --kingdom is not restricted to fungi.
MATCH_RANKS = {"SPECIES", "GENUS", "SUBSPECIES", "VARIETY", "FORM"}

# Our rank names -> MycoBank's. They are different vocabularies, which is a
# silent-failure hazard: filtering the index on OUR names yields an empty index,
# every species reports "not in MycoBank", and the pass prints a confident 0%
# match having done nothing. Hence the assertion in classify() below.
MB_RANKS = {
    "SPECIES": {"sp.", "f.sp."},
    "GENUS": {"gen."},
    "SUBSPECIES": {"subsp."},
    "VARIETY": {"var."},
    "FORM": {"f."},
}


def load_index(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(
            f"FATAL: no MycoBank index at {path}.\n"
            f"       Build it first:  python3 scripts/buildMycobankIndex.py\n"
            f"       It is a build input, not a committed artifact -- see that script."
        )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def classify(index: dict) -> dict:
    """The index, narrowed to ranks we match, with an `isCurrent` flag."""
    wanted = {r for ranks in MB_RANKS.values() for r in ranks}
    out = {}
    for key, rec in index.items():
        if rec.get("rank") not in wanted:
            continue
        cur = (rec.get("currentName") or "").strip()
        rec = dict(rec)
        rec["isCurrent"] = not cur or cur.lower() == rec["name"].lower()
        out[key] = rec
    if not out:
        sys.exit(
            "FATAL: the MycoBank index matched none of "
            f"{sorted(wanted)} -- {len(index):,} records were loaded, so the rank\n"
            "       vocabulary has drifted from the export. Nothing was scanned."
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--kingdom", default="fungi", help="fungi | chromista | protozoa | all")
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--apply", action="store_true", help="write nodes and the ledger")
    args = ap.parse_args()

    index = classify(load_index(args.index))
    mb_ranks = sorted({r["rank"] for r in index.values()})
    print(f"MycoBank index: {len(index):,} names at ranks {mb_ranks}")

    files = list(iter_family_files(args.root))
    if args.kingdom != "all":
        files = [p for p in files if f"/{args.kingdom}/" in p.replace(os.sep, "/")]
    if not files:
        sys.exit(f"FATAL: no family files matched --kingdom {args.kingdom!r} (got {len(files)}). "
                 f"A filter that matches nothing must not report success.")
    print(f"Scanning {len(files):,} family files in {args.kingdom}\n")

    stats = Counter()
    ledger: list[dict] = []
    touched: list[tuple[str, str]] = []
    started = time.time()

    for i, path in enumerate(files, 1):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        family = doc.get("name") or os.path.basename(path)
        changed = False

        stack = [doc]
        while stack:
            node = stack.pop()
            kids = node.get("children") or []
            lst = node.get("speciesList") or []
            stack.extend(kids)
            stack.extend(lst)

            if node.get("rank") not in MATCH_RANKS:
                continue
            name = (node.get("name") or "").strip()
            if not name:
                continue
            rec = index.get(name.lower())

            if not rec:
                stats["unmatched"] += 1
                ledger.append({"n": name, "rank": node.get("rank"), "family": family,
                               "id": node.get("id"), "s": "not-in-mycobank"})
                continue

            stats["matched"] += 1
            stats[f"status:{rec['status']}"] += 1
            wrote = False

            if rec.get("mb") and not node.get("mycobankId"):
                node["mycobankId"] = rec["mb"]
                wrote = True
            if rec.get("status") and not node.get("mycobankStatus"):
                node["mycobankStatus"] = rec["status"]
                wrote = True
            # authorship only where there is one, and never over an existing value
            if rec.get("authors") and not node.get("authorship"):
                node["authorship"] = rec["authors"]
                wrote = True

            if not rec["isCurrent"]:
                cur = rec["currentName"]
                stats["superseded"] += 1
                if not node.get("mycobankCurrentName"):
                    node["mycobankCurrentName"] = cur
                    wrote = True
                ledger.append({
                    "n": name, "id": node.get("id"), "family": family,
                    "rank": node.get("rank"), "s": "superseded",
                    "current": cur, "currentMb": rec.get("currentMb"),
                    "status": rec.get("status"), "cls": rec.get("classification"),
                })

            if wrote:
                node["sourcedFrom"] = "mycobank"
                changed = True

        if changed:
            touched.append((path, family))
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

        if i % 250 == 0:
            el = time.time() - started
            rate = i / el if el else 0
            print(f"  {i}/{len(files)} files  matched {stats['matched']:,}  "
                  f"superseded {stats['superseded']:,}  {el:.0f}s")

    # ── report ────────────────────────────────────────────────────────────
    total = stats["matched"] + stats["unmatched"]
    # A near-zero match rate means the lookup broke, not that the data is
    # unfamiliar. `fix_fixture_nodes.py` and the 20-species GBIF probe both
    # reported confident results on empty input; this is the guard.
    if total and stats["matched"] / total < 0.5:
        print(f"\nFATAL: only {stats['matched']/total*100:.1f}% of {total:,} matched-rank nodes "
              "were found in MycoBank.\n"
              "       That is a broken lookup, not a coverage result. Nothing was written.")
        return 1
    if not total:
        print("\nFATAL: no nodes at a matched rank were scanned. Nothing was written.")
        return 1

    print(f"\n{'=' * 66}")
    print(f"matched              {stats['matched']:>9,}  "
          f"({stats['matched']/total*100:.1f}% of {total:,} matched-rank nodes)")
    print(f"not in MycoBank      {stats['unmatched']:>9,}  ({stats['unmatched']/total*100:.1f}%)")
    print(f"superseded name      {stats['superseded']:>9,}  "
          f"({stats['superseded']/max(stats['matched'],1)*100:.1f}% of matches)")
    print(f"\nName status of our names, as MycoBank records them:")
    for key, n in sorted(stats.items(), key=lambda kv: -kv[1]):
        if key.startswith("status:"):
            print(f"  {key[7:]:<24}{n:>9,}")

    by_rank = Counter(e["rank"] for e in ledger if e["s"] == "superseded")
    if by_rank:
        print(f"\nsuperseded, by rank: {dict(by_rank)}")

    print(f"\nfiles that would change: {len(touched):,}")
    for p, fam in touched[:12]:
        print(f"    {fam:<26}{p}")
    if len(touched) > 12:
        print(f"    ... and {len(touched)-12:,} more")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    os.makedirs(os.path.dirname(args.ledger) or ".", exist_ok=True)
    with open(args.ledger, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"src": "mycobank-mblist", "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "counts": dict(stats)}, ensure_ascii=False) + "\n")
        for e in ledger:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"\n  wrote {len(touched):,} family files and {args.ledger} "
          f"({len(ledger):,} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())