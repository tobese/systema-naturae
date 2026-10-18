#!/usr/bin/env python3
"""Drop the nodes the last gap-fill run invented.

Ollama-generated content is banned from this tree as of 2026-10-17
(`CLAUDE.md`, "No LLM-generated content"). What that run left behind is 101
nodes carrying `sourcedFrom: "ollama"`, and every one of them is template
boilerplate of the form

    "Araeocerodes elongatus is a araeocerodes species found in its native region."

-- the genus name interpolated into a sentence that says nothing. There is no
researched content in them to keep, so `BACKLOG.md` resolves the open question
this script existed to answer: drop the nodes rather than downgrade them to
`sourcedFrom: "none"`, because a species that exists only because a model
produced it should not be in a taxonomy at all. Relabelling invented content as
hand-checked would be the opposite of what the field means.

Dropping rather than blanking also has a second effect worth stating: these
names leave the name-parse index and the species parquet with them, so neither
can later be cited as though a source had confirmed the species exists.

The tree's own id check would not have caught this. Every one of these species
has a well-formed `SP_...` id and a uuid derived from its rank path, because the
importer generated both. They were indistinguishable from imported species to
everything except the `sourcedFrom` field, which is the only place the
provenance was recorded.

Refused, not dropped: an ollama node with a non-ollama descendant. Dropping its
parent would orphan real species, and an invented genus holding GBIF species is
a provenance mistake to fix rather than a subtree to delete. Those are printed
and the script exits non-zero, so the run cannot look clean while quietly
skipping them.

    python3 scripts/stripBoilerplate.py --dry-run
    python3 scripts/stripBoilerplate.py --apply

This script updates each touched family's own declared `speciesCount`, because
it is what changed the file's species set and so owns keeping that number true.
`scripts/resyncFamilyCounts.py` is the wrong tool for it despite being what
`verifyTree` names: that one maintains the *taxonomy input*'s `speciesCount`,
which is the real-world total the Coverage modal divides by, while invariant 2
checks the family *file's* declared count against what the file holds. Two
different numbers, written by different code.

`make species-parquet` must be re-run after `--apply` -- `verifyTree` refuses to
read a parquet older than the newest family file.
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import count_species, iter_family_files  # noqa: E402

SOURCE = "ollama"


def invented_state(node) -> bool | None:
    """Is this node part of a wholly model-invented subtree?

    `None`   not ollama-sourced at all, so not a candidate.
    `True`   ollama-sourced and so is every descendant -- safe to drop whole.
    `False`  ollama-sourced but something real hangs below it -- refuse.

    Note the direction: a non-ollama node is `None`, not `False`. Treating
    "not from the model" as "refuse" flags the entire tree, which is the first
    version of this function's mistake.
    """
    if not isinstance(node, dict) or node.get("sourcedFrom") != SOURCE:
        return None
    stack = list(node.get("children") or []) + list(node.get("speciesList") or [])
    while stack:
        child = stack.pop()
        if not isinstance(child, dict) or child.get("sourcedFrom") != SOURCE:
            return False
        stack.extend(child.get("children") or [])
        stack.extend(child.get("speciesList") or [])
    return True


def _subtree_count(node) -> int:
    """Descendants below `node`, which go away with it."""
    n = 0
    stack = list(node.get("children") or []) + list(node.get("speciesList") or [])
    while stack:
        c = stack.pop()
        n += 1
        stack.extend(c.get("children") or [])
        stack.extend(c.get("speciesList") or [])
    return n


def strip(node, tally, refused, path):
    """Remove invented subtrees in place. Returns how many nodes went."""
    removed = 0

    kept = []
    for child in node.get("children") or []:
        state = invented_state(child)
        if state is True:
            tally[child.get("rank")] += 1
            removed += 1 + _subtree_count(child)
        elif state is False:
            refused.append(f"{path}: {child.get('name')} "
                           f"({child.get('rank')}, ollama-sourced, holds "
                           f"non-{SOURCE} species)")
            removed += strip(child, tally, refused, path)
            kept.append(child)
        else:
            removed += strip(child, tally, refused, path)
            kept.append(child)
    if node.get("children") is not None:
        node["children"] = kept

    kept = []
    for sp in node.get("speciesList") or []:
        state = invented_state(sp)
        if state is True:
            tally[sp.get("rank")] += 1
            removed += 1 + _subtree_count(sp)
        elif state is False:
            refused.append(f"{path}: {sp.get('name')} "
                           f"({sp.get('rank')}, ollama-sourced, holds "
                           f"non-{SOURCE} species)")
            removed += strip(sp, tally, refused, path)
            kept.append(sp)
        else:
            removed += strip(sp, tally, refused, path)
            kept.append(sp)
    if node.get("speciesList") is not None:
        node["speciesList"] = kept

    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the stripped files (dry run otherwise)")
    # Accepted and a no-op: BACKLOG.md documents this invocation, and a dry run
    # spelled the same way as the flag that undoes it is one less way to run the
    # destructive one by accident.
    ap.add_argument("--dry-run", action="store_true",
                    help="no-op; dry run is the default")
    args = ap.parse_args()

    total = files = 0
    tally: collections.Counter = collections.Counter()
    refused: list[str] = []
    resync = []

    for fam in iter_family_files():
        doc = fam.load()
        before = count_species(doc)
        rel = os.path.relpath(fam.path)
        removed = strip(doc, tally, refused, rel)
        if not removed:
            continue
        files += 1
        total += removed
        after = count_species(doc)
        declared = doc.get("speciesCount")
        if declared is not None and declared != after:
            resync.append(f"{rel}: {declared} -> {after}")
            doc["speciesCount"] = after
        if args.apply:
            fam.save(doc)
        print(f"  {'stripped  ' if args.apply else 'would strip'} "
              f"{removed:4d} nodes  species {before} -> {after}  {rel}")

    print(f"\n{SOURCE!r} nodes removed: {total} across {files} families")
    for rank, n in tally.most_common():
        print(f"  {str(rank):22s}{n:>6}")
    if resync:
        verb = "resynced" if args.apply else "would resync"
        print(f"  {len(resync)} families' declared speciesCount {verb}:")
        for r in resync:
            print(f"    {r}")

    if refused:
        print(f"\n  REFUSED {len(refused)}: ollama-sourced node with real "
              f"species below it -- not dropped, needs a human:")
        for r in refused:
            print(f"    {r}")
        return 1

    if args.apply:
        print("\n  wrote stripped family files")
    else:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())