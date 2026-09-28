#!/usr/bin/env python3
"""Find every family data file, wherever the taxonomy puts it.

The enrichers used a fixed-depth glob - `*/*/*/src/data/*.json` - which assumed
the family directory sat at exactly class/order/family. Under
`taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/` that matches nothing,
and a glob that matches nothing is the worst kind of failure: it returns [],
the loop body never runs, and the script prints its normal success summary and
exits 0 having enriched nothing at all.

So the layout is discovered rather than assumed, and the count is asserted
rather than hoped for.
"""
import os
import sys

TAXONOMY = "taxonomy"
DATA_TAIL = os.path.join("src", "data")


def iter_family_files(root):
    """Yield absolute paths of every <family>/src/data/*.json under taxonomy/."""
    base = os.path.join(root, TAXONOMY)
    if not os.path.isdir(base):
        return
    for kingdom in sorted(os.listdir(base)):
        kdir = os.path.join(base, kingdom)
        if not os.path.isdir(kdir):
            continue
        for dirpath, dirnames, filenames in os.walk(kdir):
            if os.path.basename(dirpath) == "data" and os.path.basename(os.path.dirname(dirpath)) == "src":
                for f in sorted(filenames):
                    if f.endswith(".json"):
                        yield os.path.join(dirpath, f)


def collect(root, minimum=1):
    """(path -> parsed tree) for every family file, refusing an empty result."""
    out = {}
    for p in iter_family_files(root):
        try:
            with open(p, encoding="utf-8") as fh:
                out[p] = json.load(fh)
        except Exception as e:
            print(f"  WARN could not parse {p}: {e}", file=sys.stderr)
    if len(out) < minimum:
        sys.exit(
            f"FATAL: found only {len(out)} family files under {root}/{TAXONOMY}, "
            f"expected at least {minimum}.\n"
            f"       A glob that matches nothing exits 0 and enriches nothing, so this\n"
            f"       refuses to run rather than reporting success having done no work."
        )
    return out


import json  # noqa: E402  (kept below the docstring's imports for clarity)


def family_slug(path):
    """The family directory name, which is the appSlug."""
    return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    files = list(iter_family_files(root))
    print(f"{len(files):,} family data files under {root}/{TAXONOMY}")
    depths = {}
    for p in files:
        rel = os.path.relpath(p, root)
        depths[rel.count(os.sep) - 2] = depths.get(rel.count(os.sep) - 2, 0) + 1
    for d in sorted(depths):
        print(f"  {d} levels below root: {depths[d]:,}")
