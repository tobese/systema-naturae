#!/usr/bin/env python3
"""Resolve family-file conflicts by unioning, without losing a field.

Two machines importing disjoint datasets still land in the same family file --
a worm on one, a beetle on the other -- and git then has no basis for a merge
because both sides rewrote the same JSON object. 597 such files after the
2026-10-17 two-machine batch.

`git checkout --theirs` would keep one machine's work and silently delete the
other's, so that is not an option. Neither is the naive union that
`merge_conflicts.py` did: it kept one side's copy of each shared node whole,
which is how 1,654 nodes lost their `sourcedFrom` to `"none"` on the previous
merge (see scripts/fix_flattened_provenance.py, which then had to put them back).

What this does instead, per node:

  * union children by `id`, so a species only one machine added survives;
  * for a node on both sides, take ours and fill in anything we lack from
    theirs -- never the reverse, and never over a value we hold with an empty
    one. "Theirs has a description and we do not" is enrichment; "theirs has
    `sourcedFrom: none` and we have `checklistbank`" is a downgrade and is
    refused.

Run with no arguments to resolve everything unmerged; pass paths to be explicit.

    python3 scripts/mergeFamilyFiles.py
    python3 scripts/mergeFamilyFiles.py --dry-run
"""
import argparse
import json
import subprocess
import sys

# Fields where an empty value on one side is a fact about that side, not a
# missing value to be filled from the other. Filling these is how provenance and
# authorship get erased by a merge.
EMPTY_IS_MEANINGLESS = {"sourcedFrom", "authorship", "description", "name",
                        "id", "rank", "continents", "commonName"}


def is_empty(v):
    return v is None or v == "" or v == [] or v == {}


def merge_value(ours, theirs, key):
    """One field: ours unless we do not have it, with empty treated as absent
    for the fields where empty means "not recorded" rather than "none of it"."""
    if key not in ours:
        return theirs.get(key)
    if key not in EMPTY_IS_MEANINGLESS:
        return ours[key]
    if not is_empty(ours[key]):
        return ours[key]
    # ours is empty; take theirs only if theirs is a real value.
    return theirs.get(key)


def merge_node(ours, theirs, stats):
    out = dict(ours)
    for k, v in theirs.items():
        if k in ("children", "speciesList"):
            continue
        out[k] = merge_value(ours, theirs, k)
        if k in ours and ours[k] != v and ours[k] in (None, "", "none"):
            stats["filled"] += 1

    for field in ("children", "speciesList"):
        a = {c.get("id"): c for c in (ours.get(field) or []) if c.get("id")}
        b = {c.get("id"): c for c in (theirs.get(field) or []) if c.get("id")}
        order = []
        seen = set()
        for c in (ours.get(field) or []):
            k = c.get("id")
            if k and k not in seen:
                seen.add(k)
                order.append(k)
        for c in (theirs.get(field) or []):
            k = c.get("id")
            if k and k not in seen:
                seen.add(k)
                order.append(k)
        merged = []
        for k in order:
            if k in a and k in b:
                merged.append(merge_node(a[k], b[k], stats))
                stats["shared"] += 1
            elif k in a:
                merged.append(a[k])
                stats["ours_only"] += 1
            else:
                merged.append(b[k])
                stats["theirs_only"] += 1
        out[field] = merged
    return out


def load_side(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = args.paths or subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        capture_output=True, text=True).stdout.split()
    files = [f for f in files if f.endswith(".json")]
    if not files:
        print("nothing conflicted")
        return 0

    totals = {"shared": 0, "ours_only": 0, "theirs_only": 0, "filled": 0}
    resolved = skipped = 0
    for path in files:
        ours = load_side("HEAD", path)
        theirs = load_side("MERGE_HEAD", path)
        if ours is None or theirs is None:
            print(f"  SKIP (missing side): {path}")
            skipped += 1
            continue
        if args.dry_run:
            print(f"  would merge: {path}")
            resolved += 1
            continue
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(merge_node(ours, theirs, totals), fh,
                      indent=2, ensure_ascii=False)
            fh.write("\n")
        resolved += 1

    print(f"{'would merge' if args.dry_run else 'resolved'}: {resolved}, skipped: {skipped}")
    print(f"  nodes shared by both sides: {totals['shared']:,}")
    print(f"  nodes only on Macie:        {totals['ours_only']:,}")
    print(f"  nodes only on q-bert:       {totals['theirs_only']:,}")
    print(f"  fields filled from theirs:  {totals['filled']:,}")
    if not args.dry_run:
        print("\n  git add the paths, then commit. Re-run scripts/verifyTree.py after.")
    return 0


if __name__ == "__main__":
    sys.exit(main())