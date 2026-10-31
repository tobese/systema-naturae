#!/usr/bin/env python3
"""Drop `authorship` values that carry no authorship: the literal "NULL" and
its kin ("null", "?", "-"), which taxamatch.clean_authorship rejects.

6,692 species carried one on 2026-10-31, nearly all "NULL" (ITIS-sourced
algae, diatoms and sponges among the most). A "NULL" author made two copies of
one species look like two authors' names, and shows as an author in the
portal. Absent is the honest value: nothing is invented in its place.

Ids are left as they are, including the 771 that a "NULL" authorship was
folded into (SP_..._NULL). Ids are referenced from sidecars and decision
files; renaming them is its own job, reported here, not done.

    python3 scripts/clearJunkAuthorship.py
    python3 scripts/maintenanceSession.py --run "python3 scripts/clearJunkAuthorship.py --apply"
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
import taxamatch  # noqa: E402
from tree import KINGDOMS, iter_family_files, iter_nodes, save_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cleared = collections.Counter()
    values = collections.Counter()
    null_ids = files = 0
    for k in KINGDOMS:
        for fam in iter_family_files(k):
            with open(fam.path, encoding="utf-8") as fh:
                doc = json.load(fh)
            n = 0
            for node in iter_nodes(doc):
                a = node.get("authorship")
                if isinstance(a, str) and taxamatch.clean_authorship(a) is None:
                    values[a] += 1
                    if (node.get("id") or "").endswith("_NULL"):
                        null_ids += 1
                    del node["authorship"]
                    n += 1
            if not n:
                continue
            cleared[k] += n
            if args.apply:
                save_json(fam.path, doc)
                files += 1
    total = sum(cleared.values())
    print("  per kingdom: " + ", ".join(f"{k} {v:,}" for k, v in cleared.most_common()))
    print("  values: " + ", ".join(f"{v!r} {c:,}" for v, c in values.most_common()))
    print(f"  ids carrying the junk (_NULL), left unchanged: {null_ids:,}")
    if args.apply:
        print(f"\n  cleared {total:,} authorships in {files:,} files")
    else:
        print(f"\n  {total:,} authorships to clear (dry run -- pass --apply)")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        with maintenanceLock.hold_exclusive():
            sys.exit(main())
    sys.exit(main())
