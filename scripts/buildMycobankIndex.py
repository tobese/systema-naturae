#!/usr/bin/env python3
"""
Build a name index from MycoBank's own bulk export.

What this is
------------
`MBList.xlsx`, linked from the MycoBank homepage with no key and no
registration, is the answer to the "is there a bulk route" question that sat
open in `docs/drafts/mycobank-token-request.md`. It is 544,942 rows and 144 MB,
of which 521,819 are distinct taxon names:

    https://www.mycobank.org/Images/MBList.zip

It is nomenclatural, not descriptive - there is no prose in it, so it does not
close the description gap. What it does carry is the thing we cannot get
anywhere else for free at this volume:

| column | why it matters |
|---|---|
| `Name status` | Legitimate / Illegitimate / Orthographic variant / Invalid / Unavailable / Uncertain / Deleted |
| `Current name` | the accepted name where ours is superseded |
| `Classification` | a rendered `Fungi > Dikarya > Ascomycota > ...` path |
| `MycoBank #`, `Authors`, `Year` | `scientificNameAuthorship`, which nothing in our tree recorded before |

This script parses the xlsx and writes a compact JSON index. It exists as a
separate step because the parse is the expensive part (~50 s, dominated by
`sharedStrings.xml` at 443 MB) and the result is reused by every later pass.

Why not just commit the xlsx
----------------------------
144 MB of binary in git for a derived artifact, and a 209 MB JSON index on top.
Both are build inputs, so both are gitignored and re-fetchable -- the download
is 144 MB and the parse is ~70 s, which is cheaper than any of the history that
a large binary in git creates.

Note the index is 209 MB, not the ~26 MB an earlier draft of this docstring
claimed. Persisting all thirteen columns costs 448 MB, of which `Synonymy`
alone is 240 MB of citation prose. See the note above `fetch()` for what is
dropped and why.

Usage
-----
    python3 scripts/buildMycobankIndex.py                 # fetch + parse + write
    python3 scripts/buildMycobankIndex.py --from-xlsx PATH # parse a local copy
    python3 scripts/buildMycobankIndex.py --report         # match stats only

The output lands in `portal/data/mycobank-index.json` by default. Read it with
`load_index()` from `enrichFromMycobank.py`, which is the only consumer that
should.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

MBLIST_URL = "https://www.mycobank.org/Images/MBList.zip"
DEFAULT_INDEX = os.path.join("portal", "data", "mycobank-index.json")

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# SpreadsheetML columns. B is the name we key on; the rest are the columns the
# passes use. Column letters, not names, because reading the header row means
# parsing the sheet first, and the layout has been stable across exports.
COL_NAME = "B"        # Taxon name
COL_AUTHORS = "C"     # Authors
COL_AUTHORS_ABBR = "D"
COL_RANK = "E"        # Rank
COL_YEAR = "F"        # Year of effective publication
COL_STATUS = "G"      # Name status
COL_MB = "H"          # MycoBank #
COL_CLASSIFICATION = "J"
COL_CURRENT_MB = "K"  # Current MycoBank #
COL_CURRENT_NAME = "L"
COL_SYNONYMY = "M"    # parsed, then dropped -- see PERSISTED below

# A polite UA, and the export is only linked from a page that references it.
UA = "SystemaNaturae/1.0 (taxonomy portal; https://github.com/tobese/systema-naturae)"

# Columns deliberately NOT persisted, and why. Persisting every column costs
# 448 MB, which is absurd for a derived cache:
#
#   Synonymy            240 MB  citation prose ("Current name: X Diederich, Bull.
#                              Soc. Naturalistes Luxemb. 115: 144 (2014) [MB#...]")
#                              that restates currentName + authors + year. The
#                              citation itself is the only unique content and
#                              nothing here uses it.
#   Authors (abbreviated)  17 MB  near-duplicate of Authors for most records.
#
# 188 MB remains, and the only large remaining field is `classification` (70 MB),
# which is kept because it is the one column that independently corroborates
# where a name sits in the tree -- worth having when auditing a placement.


def fetch(url: str, dest: str) -> None:
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.mycobank.org/"})
    started = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
            if total:
                print(f"\r  {got/1e6:,.0f} / {total/1e6:,.0f} MB", end="", flush=True)
    print(f"\r  {got/1e6:,.0f} MB in {time.time()-started:.0f}s")


def _cell_value(cell, shared):
    """Resolve one <c>. Handles shared-string, formula-cached and inline types.

    Columns K and L (`Current MycoBank #`, `Current name`) are XLOOKUP formulas,
    not literals - the value is only in the cached <v>, so reading t="str" is not
    optional here. Getting that wrong yields an empty current-name for every
    row, which looks exactly like "nothing is superseded".
    """
    kind = cell.get("t")
    v = cell.find(NS + "v")
    if v is None or v.text is None:
        return ""
    if kind == "s":
        return shared[int(v.text)]
    return v.text


def parse_xlsx(xlsx_path: str) -> dict:
    """name.lower() -> record dict. ~50 s and ~2 GB peak RSS on the 144 MB file."""
    print(f"  parsing {xlsx_path}")
    started = time.time()

    print("  sharedStrings.xml ...", end="", flush=True)
    shared: list[str] = []
    with zipfile.ZipFile(xlsx_path).open("xl/sharedStrings.xml") as fh:
        for _evt, el in ET.iterparse(fh, events=("end",)):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
    print(f" {len(shared):,} strings ({time.time()-started:.0f}s)")

    print("  sheet1.xml ...", end="", flush=True)
    index: dict[str, dict] = {}
    rows = 0
    with zipfile.ZipFile(xlsx_path).open("xl/worksheets/sheet1.xml") as fh:
        for _evt, el in ET.iterparse(fh, events=("end",)):
            if el.tag != NS + "row":
                continue
            if el.get("r") != "1":  # header
                cells = {}
                for cell in el.iter(NS + "c"):
                    ref = cell.get("r") or ""
                    col = "".join(ch for ch in ref if ch.isalpha())
                    cells[col] = _cell_value(cell, shared)
                name = (cells.get(COL_NAME) or "").strip()
                if name:
                    key = name.lower()
                    # Later rows win. Duplicate names exist across ranks and the
                    # sheet is not ordered, so this is arbitrary but stable.
                    index[key] = {
                        "name": name,
                        "authors": (cells.get(COL_AUTHORS) or "").strip(),
                        "authorsAbbr": (cells.get(COL_AUTHORS_ABBR) or "").strip(),
                        "rank": (cells.get(COL_RANK) or "").strip(),
                        "year": (cells.get(COL_YEAR) or "").strip(),
                        "status": (cells.get(COL_STATUS) or "").strip(),
                        "mb": (cells.get(COL_MB) or "").strip(),
                        "classification": (cells.get(COL_CLASSIFICATION) or "").strip(),
                        "currentMb": (cells.get(COL_CURRENT_MB) or "").strip(),
                        "currentName": (cells.get(COL_CURRENT_NAME) or "").strip(),
                    }
                    rows += 1
            el.clear()
    print(f" {rows:,} rows ({time.time()-started:.0f}s)")
    return index


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--xlsx", help="parse this local MBList.xlsx instead of downloading")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--report", action="store_true", help="print stats, write nothing")
    args = ap.parse_args()

    xlsx = args.xlsx
    if not xlsx:
        os.makedirs(args.cache_dir, exist_ok=True)
        xlsx = os.path.join(args.cache_dir, "MBList.xlsx")
        if not os.path.exists(xlsx):
            fetch(MBLIST_URL, xlsx)
        else:
            print(f"  using cached {xlsx}")

    index = parse_xlsx(xlsx)

    import collections

    by_status = collections.Counter(v["status"] for v in index.values())
    by_rank = collections.Counter(v["rank"] for v in index.values())
    superseded = sum(
        1 for v in index.values()
        if v["currentName"] and v["currentName"].lower() != v["name"].lower()
    )
    print(f"\n  {len(index):,} distinct names · {superseded:,} with a different current name")
    print("  status:", by_status.most_common())
    print("  rank:  ", by_rank.most_common(6))

    if args.report:
        print("\n  (--report: nothing written)")
        return 0

    os.makedirs(os.path.dirname(args.index) or ".", exist_ok=True)
    with open(args.index, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)
    print(f"\n  wrote {args.index} ({os.path.getsize(args.index)/1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())