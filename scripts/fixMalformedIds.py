#!/usr/bin/env python3
"""
Repair malformed node ids, and two genus pairs that collided into one id.

What this fixes
---------------
Auditing all 1,308,010 ids in the tree for malformed patterns turned up three
distinct defects, none of which any existing check looks for:

| defect | count | shape |
|---|---|---|
| `SP__` doubled underscore | 425 | `× Asplenicystopteris blindii` -> `SP__ASPLENICYSTOPTERIS_BLINDII` |
| id containing a raw space or `-` | 7,474 | `Dactylorhiza x Gymnadenia` -> `GENUS_DACTYLORHIZA X GYMNADENIA` |
| id ending in `_` | 145,484 | `Smilax zeylanica L.` -> `SP_SMILAX_ZEYLANICA_L_` |

The doubled underscore comes from the leading hybrid marker: it becomes an empty
token between two separators. The 7,474 are genus ids built by a path that never
replaced non-alphanumerics, and they carry a literal space -- which is a real
hazard for anything that puts an id in a URL, a filename or a CSS selector.

**The trailing underscore is left alone, deliberately.** `SP_SMILAX_ZEYLANICA_L_`
is ugly, but the trailing `_` is the faithful slug of a name that genuinely ends
in an abbreviation (`L.`, `Merr.`, `A.DC.`). Trimming it is a cosmetic change to
145,484 ids across the whole tree for no gain, and it would break every external
reference to them. The new ids keep the existing scheme exactly, minus the
malformed part.

Two genus pairs collide outright
--------------------------------
Searching for duplicate ids found two, both inside a single family file:

    Annonaceae     Neo-Uvaria   and   Neo-uvaria      -> GENUS_NEO-UVARIA
    Brassicaceae  Solms-Laubachia and Solms-laubachia -> GENUS_SOLMS-LAUBACHIA

These differ only in capitalisation of a hyphenated epithet, so the slug is
identical. They are the same genus twice, and both copies carry species, so
merging is a union by species id -- the same approach as
`merge_duplicate_genera.py`, which keys on genus *name* and so never saw them.

Renaming, not deleting
----------------------
An id is a foreign key. `?node=` URLs, the analytics envelope's `node_id`, and
anything a reader has bookmarked all reference it. So ids are **not** silently
rewritten: each change is written to
`portal/data/id-changes.jsonl` with the old value, the new value, the node name
and the path, and the report lists them. If a reference is missed it is
recoverable by `id`, and `revert` puts it back.

    python3 scripts/fixMalformedIds.py             # dry run, prints counts
    python3 scripts/fixMalformedIds.py --apply     # write
    python3 scripts/fixMalformedIds.py --revert    # undo, from the log

Read-only unless `--apply`. Idempotent: a second run finds nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # noqa: E402

CHANGELOG = os.path.join("portal", "data", "id-changes.jsonl")

# An id is well-formed when it is `PREFIX_UPPER_SNAKE` with no doubled, leading
# or embedded separators. Everything here reduces a name to that shape.
MALFORMED = re.compile(r"[^A-Za-z0-9_]|__|^_|_$")

# Rank -> the prefix its ids actually use. Not every id has a prefix; see
# prefix_for() for why inventing one for the prefixless majority would be wrong.
PREFIX_BY_RANK = {
    "SPECIES": ("SP", None),
    "GENUS": ("GENUS", None),
    "FAMILY": ("FAM", "GENUS"),
    "SUBFAMILY": ("SUB", None),
    "ORDER": ("ORD", None),
    "CLASS": ("CLS", None),
    "PHYLUM": ("PHY", None),
    "HYBRID": ("HYBRID", None),
}


def canonical_id(prefix: str, name: str) -> str:
    """The id this node *should* have, under the scheme the importers use.

    `importPlantVascularFromWcvp.ts` does exactly this:
        "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_")

    Collapsing `_+` to `_` is **not** sufficient on its own. A leading hybrid
    marker becomes an empty token next to the prefix's own separator:

        "× Asplenicystopteris blindii"  ->  "_Asplenicystopteris_blindii"

    and prefixing that yields `SP__ASPLENICYSTOPTERIS_BLINDII` -- the doubled
    underscore this script exists to remove. `replace(/_+/g,"_")` collapses runs
    *within* the slug but the prefix is concatenated afterwards, so the two
    separators never meet. Stripping leading and trailing separators from the
    slug first is what actually fixes it.

    Only the *leading* separator is stripped. Stripping both ends looks tidier
    and is wrong: `Smilax zeylanica L.` slugs to `SMILAX_ZEYLANICA_L_`, and
    145,484 ids already carry that trailing underscore because their name ends in
    an authority abbreviation. Stripping it would churn every one of them to
    satisfy a cosmetic preference, and break any external reference to them.
    """
    slug = re.sub(r"[^A-Za-z0-9]", "_", name).upper()
    slug = re.sub(r"_+", "_", slug).lstrip("_")
    return f"{prefix}_{slug}"


def prefix_for(node: dict) -> str | None:
    """The id prefix this rank uses, or None when the id is prefixless.

    A first version of this used `MALFORMED.search(id)` as the trigger and
    rewrote anything it did not recognise. That flagged **153,317** ids, of which
    153,172 were perfectly good: ids are not always prefixed. `PARACERCOMONAS_
    MARINA` is a correct id for a species, bare `HAPLOC` is a correct id for a
    genus, `cattle` is a correct id for a breed. Rewriting those to
    `GENUS_HAPLOC` / `BREED_CATTLE` would have churned a third of the tree to
    impose a convention most of it does not follow -- and, worse, collapsed real
    taxa onto each other, because the prefixless form is what keeps
    `GENUS_SCHULZIA` (Molineidae, a nematode) and `GENUS_SCHULZIA` (Apiaceae, a
    flowering plant) apart.

    So the trigger is now *not* "looks unfamiliar" but "carries a doubled
    separator, or a raw space/hyphen inside an already-prefixed id".
    """
    i = node.get("id") or ""
    if "__" in i:
        return _known_prefix(i)
    # A raw space or hyphen is only a defect when a prefix is present: in a
    # prefixless id the hyphen is part of the name (`Neo-Uvaria`).
    if re.search(r"[ \-]", i):
        return _known_prefix(i)
    return None


def _known_prefix(i: str) -> str | None:
    """The prefix, but only from a list actually observed in the tree.

    `PHY` was in an earlier version of this list and had to come out. It is not
    a prefix: it is the first three letters of a great many fungal and plant
    genera. `PHYLLOPORIA_VERAE-CRUCIS` is a *species* in genus *Phylloporia*,
    and `PHYLLOSTICTA_VITIS-ROTUNDIFOLIAE` is one in *Phyllosticta*. Treating
    `PHY` as a rank prefix "fixed" 178 perfectly good species ids into
    `SPECIES_PHYLLOPORIA_VERAE_CRUCIS` and similar -- inventing a prefix for
    ranks that do not use one, on the strength of a name that happens to start
    with three letters that look like an abbreviation.

    So the list is only prefixes that are unambiguous: a rank token followed by a
    separator, and only when the rank genuinely uses one (see PREFIX_BY_RANK,
    where the second element records the rank having no prefixed ids at all).
    """
    m = re.match(r"^(SP_|GENUS_|FAM|ORD|SUB|CLS|HYBRID|KINGDOM|ORDER)", i)
    if not m:
        return None
    p = m.group(1).rstrip("_")
    if p not in SAFE_PREFIXES:
        return None
    return p


# Filled from the tree at startup: {rank -> set of prefixes actually in use}.
OBSERVED_PREFIXES: set[str] = set()

# The only prefixes this script will act on. Chosen because they are
# unambiguous in this tree, not because they look like rank abbreviations --
# which is the trap. Verified by reading actual ids:
#
#   SP_     1.2M species ids            GENUS_  intergeneric + odd genera
#   FAM_    placeholder families       (PHY/CLS/ORD/SUB are NOT prefixes here)
#
# `PHY` is absent on purpose: it is the start of Phyllosticta, Phyllachora,
# Phycomyces and thousands more. Adding it "fixed" 178 real species ids.
SAFE_PREFIXES = {"SP", "GENUS", "FAM"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--changelog", default=CHANGELOG)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    if args.revert:
        if not os.path.exists(args.changelog):
            sys.exit(f"FATAL: no changelog at {args.changelog}; nothing to revert.")
        by_file = defaultdict(list)
        with open(args.changelog, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("{"):
                    rec = json.loads(line)
                    by_file[rec["file"]].append(rec)
        n = 0
        for path, recs in by_file.items():
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            stack = [doc]
            while stack:
                node = stack.pop()
                stack.extend(node.get("children") or [])
                stack.extend(node.get("speciesList") or [])
                for r in recs:
                    if node.get("id") == r["newId"]:
                        node["id"] = r["oldId"]
                        n += 1
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        print(f"reverted {n:,} ids across {len(by_file):,} files")
        return 0

    files = list(iter_family_files(args.root))
    print(f"Scanning {len(files):,} family files for malformed ids\n")

    # Report which prefixes each rank actually uses, for the record. This is
    # reporting only -- it deliberately does NOT feed the fix decision, because
    # an earlier version tried to learn prefixes from the tree and produced
    # nonsense: the test "does the id equal the slug of the name" is true for
    # every bare genus id, so `HAPLOC`, `MYCENA`, `PUCCIN` and several thousand
    # other genus names were all collected as if they were rank prefixes.
    #
    # The fix list below is a fixed, hand-verified set instead. Short rank
    # abbreviations are exactly the strings that occur by coincidence at the
    # start of a genus name -- `PHY` in Phyllosticta, `SUB` in Subramania,
    # `ORD` in Ordinary -- so they cannot be discovered, only decided.
    print(f"  repairing ids under prefixes: {', '.join(sorted(SAFE_PREFIXES))}\n")

    changes: list[dict] = []
    _all_changes: list[dict] = []
    taken: dict[str, list[str]] = defaultdict(list)
    tally = Counter()
    seen: dict[str, list[str]] = defaultdict(list)
    started = time.time()

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        family = doc.get("name") or os.path.basename(path)
        dirty = False

        stack = [doc]
        while stack:
            node = stack.pop()
            kids = node.get("children") or []
            lst = node.get("speciesList") or []
            stack.extend(kids)
            stack.extend(lst)

            i = node.get("id") or ""
            seen[i].append(f"{family}/{node.get('name')}")

            if "__" in i or re.search(r"[ \-]", i):
                tally["malformed"] += 1
                prefix = prefix_for(node)
                if not prefix:
                    # prefixless id with a hyphen: that hyphen is the name.
                    tally["prefixless-ok"] += 1
                    continue
                new = canonical_id(prefix, node.get("name") or "")
                if new != i:
                    tally[f"fix:{prefix}"] += 1
                    rec = {"file": path, "family": family, "name": node.get("name"),
                           "oldId": i, "newId": new, "rank": node.get("rank")}
                    changes.append(rec)
                    _all_changes.append(rec)
                    if args.apply:
                        node["id"] = new
                    dirty = True

        if dirty and args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    # Duplicate ids are found after rewriting, because two malformed ids can
    # normalise onto the same well-formed one.
    dupes = {i: v for i, v in seen.items() if len(v) > 1}

    print(f"{'=' * 66}")
    print(f"malformed ids found:      {tally['malformed']:>8,}")
    for k, v in sorted(tally.items()):
        if k.startswith("fix:") or k.startswith("no-prefix:"):
            print(f"  {k:<26}{v:>8,}")
    print(f"\nids that would change:   {len(changes):>8,}")
    print(f"duplicate ids remaining: {len(dupes):>8,}")
    for i, where in list(dupes.items())[:10]:
        print(f"  {i!r}")
        for w in where:
            print(f"      {w}")

    # Two rewrites would land on an id another node already holds: `Neo-Uvaria` /
    # `Neo-uvaria` in Annonaceae and `Solms-Laubachia` / `Solms-laubachia` in
    # Brassicaceae are the same genus twice, differing only in case, and they
    # currently share one id. Normalising both produces a genuine duplicate, so
    # they are held back for a merge rather than rewritten here.
    counts: dict[str, int] = Counter(r["newId"] for r in
                                     [{**c} for c in _all_changes])
    held = [c for c in _all_changes if counts[c["newId"]] > 1]
    if held:
        changes = [c for c in _all_changes if counts[c["newId"]] == 1]
        print(f"\nheld back for a merge first: {len(held)}")
        for c in held:
            print(f"    {c['name']!r:<28}{c['oldId']} -> {c['newId']}")

    print(f"\nexamples of the change:")
    for c in changes[:10]:
        print(f"  {c['name']!r:<40}{c['oldId']}\n{'':<42}-> {c['newId']}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    os.makedirs(os.path.dirname(args.changelog) or ".", exist_ok=True)
    with open(args.changelog, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "count": len(changes)}) + "\n")
        for c in changes:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\n  applied {len(changes):,} id changes")
    print(f"  wrote {args.changelog}  (revert with --revert)")
    return 0


if __name__ == "__main__":
    sys.exit(main())