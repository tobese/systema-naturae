#!/usr/bin/env python3
"""Check our names against the ICZN Official Lists and Indexes.

The archive is a GitHub clone, not a DwCA: `names.txt` is a tab-delimited
file of 12,403 names with `canonical`, `status` (available / unavailable) and
`opinions` (Opinion number + ruling), parsed positionally because the file has
no header -- the column order is the one in the README's `\\copy names ...`
statement.

Its value is validation rather than coverage, and it is worth being explicit
about both. It matches 0.1% of the tree -- 1,159 species of 1,755,597 in
animalia -- so it does not fill a gap and is not a candidate for an import
pass. What it does is tell us whether a name we hold is one the Commission has
ruled on: 983 of the matches are `available` and 157 are `unavailable`, which
is the kind of thing no amount of name or id matching had found, and the
opinions column carries the ruling -- a plenary power, a Direction, a
homonymy decision -- which is the only place that reasoning lives.

It is not applied as a data field. A species is not "ICZN-valid" in the way it
is "in Asia"; the Commission's lists are a judgement about availability, and
encoding that as a boolean would be a claim about a name we may not even be
using in the same sense. This writes a report instead, so the finding is
reviewable and the tree is untouched.

    python3 scripts/validateIczn.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402
from tree import iter_family_files  # noqa: E402

SLUG = "iczn-lists"
ARCHIVE = "iczn.zip"
MEMBER = "iczn-lists-master/names.txt"

# Column order from the README's \copy names (...) from names.txt. Positional
# because names.txt has no header row.
IDX = {
    "id": 0, "canonical": 1, "authorship": 2, "datepublished": 3,
    "originalcitation": 4, "status": 5, "classification": 6, "phylum": 7,
    "class": 8, "order": 9, "rank": 10, "typestatus": 11, "typename": 12,
    "typespecimen": 13, "typedesignatedby": 14, "typedesignationtype": 15,
    "gender": 16, "sic": 17, "synopsis": 18, "direction": 19,
    "opinions": 20, "rlpcomments": 21, "plaintext": 22,
}


def load_names(archive: str):
    with zipfile.ZipFile(archive) as z:
        with z.open(MEMBER) as raw:
            lines = [ln.decode("utf-8", "replace") for ln in raw]
    out = {}
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 22:
            continue
        canonical = parts[IDX["canonical"]].strip()
        if not canonical:
            continue
        out[canonical] = {
            "status": parts[IDX["status"]].strip(),
            "opinions": parts[IDX["opinions"]].strip(),
            "rank": parts[IDX["rank"]].strip(),
        }
    return out


def main() -> int:
    archive = os.path.join(sources.archive_dir(SLUG), ARCHIVE)
    if not os.path.exists(archive):
        print(f"FATAL: {archive} not found")
        return 2
    iczn = load_names(archive)
    print(f"  ICZN names: {len(iczn):,}  "
          f"({sum(1 for v in iczn.values() if v['status']=='available'):,} available, "
          f"{sum(1 for v in iczn.values() if v['status']=='unavailable'):,} unavailable)")

    matched = collections.Counter()
    unavailable = []
    checked = 0
    for fam in iter_family_files("animalia"):
        doc = json.load(open(fam.path, encoding="utf-8"))
        stack = list(doc.get("children") or [])
        while stack:
            n = stack.pop()
            if n.get("rank") == "SPECIES":
                checked += 1
                b = (n.get("name") or "").strip().split(" (")[0].strip()
                if b in iczn:
                    matched[iczn[b]["status"]] += 1
                    if iczn[b]["status"] == "unavailable":
                        unavailable.append((fam.slug, b, iczn[b]["opinions"]))
            stack.extend(n.get("children") or [])

    print(f"\n  tree species checked: {checked:,}")
    print(f"  matched by the Commission: {sum(matched.values()):,} "
          f"({sum(matched.values())/checked*100:.2f}%)")
    print(f"  by ICZN status: {dict(matched)}")
    print(f"\n  unavailable names we hold: {len(unavailable):,}")
    for slug, name, opinions in sorted(unavailable)[:40]:
        print(f"    {slug:22s} {name:32s} {opinions[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())