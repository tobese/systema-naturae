#!/usr/bin/env python3
"""
Compare GBIF's name resolution against MycoBank's, on the names they disagree about.

Why
---
MycoBank's `MBList.xlsx` export flags 28,620 of our fungal names as superseded
(26,857 species, 1,763 genera). That is not a rename this project should apply
blind, and the first sign of why came from a single probe against the GBIF
Species API `v2` match service:

    Karlingia lobata        GBIF: ACCEPTED
    Karlingiomyces:lobatus  GBIF: SYNONYM -> Karlingia lobata

which is the **exact reverse** of MycoBank, whose `Current name` for
`Karlingia lobata` is `Karlingiomyces lobatus`. One of them has the direction
backwards, and we do not yet know which.

This measures the disagreement over the whole set instead of guessing from one
example. It is a read-only measurement: nothing here writes to the tree.

Usage
-----
    python3 scripts/compareGbifMycobank.py --limit 200    # quick probe
    python3 scripts/compareGbifMycobank.py                # all 28,620

Notes
-----
`v2/species/match` takes a POST array of up to 1000 `{scientificName}` objects
and answers in input order. The spec's `NameUsageQuery` schema is a dangling
`$ref` -- referenced from the request body but absent from
`components.schemas` -- so the real request shape was determined by probing.
Sending bare strings returns 400.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

MATCH_URL = "https://api.gbif.org/v2/species/match"
UA = "SystemaNaturae/1.0 (taxonomy portal; https://github.com/tobese/systema-naturae)"
BATCH = 500


def match_batch(names: list[str]) -> list[dict]:
    body = json.dumps([{"scientificName": n} for n in names]).encode()
    req = urllib.request.Request(MATCH_URL, data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                sys.exit(f"FATAL: GBIF rejected the batch ({e.code}). "
                         f"The request shape changed; re-probe before trusting output.")
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)
        except urllib.error.URLError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)
    return []


def classify(ours: str, mb_target: str, result: dict) -> tuple[str, str]:
    """(verdict, detail) for one name, comparing the two authorities."""
    usage = result.get("usage") or {}
    diag = result.get("diagnostics") or {}
    accepted = result.get("acceptedUsage") or {}

    gbif_status = usage.get("status") or diag.get("matchType") or "NONE"
    match_type = diag.get("matchType") or ""
    conf = diag.get("confidence")
    note = diag.get("note") or ""
    gbif_canonical = usage.get("canonicalName") or ""
    gbif_accepted = accepted.get("canonicalName") or ""

    # `matchType` decides whether GBIF found the name AT ALL, and it has to be
    # read first. When GBIF cannot place a name it falls back to a higher taxon
    # and still reports `status: ACCEPTED` -- for `Synchytrium phaseoli` that is
    # the KINGDOM Fungi, not the species. Judging on `status` alone therefore
    # scores a failed lookup as agreement, which is how a first pass reported
    # 98.7% "GBIF keeps our name" when most of it was GBIF not knowing.
    if match_type in ("NONE", "HIGHERRANK"):
        return "gbif-does-not-know", f"matchType={match_type} conf={conf} note={note!r}"
    if match_type in ("AMBIGUOUS", "FUZZY"):
        # A fuzzy match may still be on our name, but it is not authority to
        # overrule a nomenclatural registry, so it never counts as agreement.
        return "gbif-fuzzy", f"matchType={match_type} conf={conf} -> {gbif_canonical!r}"

    if gbif_status == "ACCEPTED":
        if gbif_canonical.lower() == ours.lower():
            # GBIF keeps our name; MycoBank wants to move it.
            return "disagree-gbif-keeps", f"gbif=ACCEPTED conf={conf}"
        if gbif_canonical.lower() == mb_target.lower():
            return "agree", f"both move to {mb_target}"
        return "disagree-third-name", f"gbif={gbif_canonical!r} mb={mb_target!r}"

    if gbif_status == "SYNONYM":
        target = gbif_accepted or gbif_canonical
        if target.lower() == ours.lower():
            # GBIF says ours is the accepted one and the OTHER name is the synonym.
            return "reversed", f"gbif keeps {ours!r}, calls {mb_target!r} a synonym"
        if target.lower() == mb_target.lower():
            return "agree", f"both -> {target}"
        return "disagree-third-name", f"gbif synonym of {target!r}, mb -> {mb_target!r}"
    return f"gbif-{gbif_status.lower()}", f"conf={conf}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/tmp/mb_superseded.json")
    ap.add_argument("--out", default="docs/reports/gbif-mycobank-disagreement.md")
    ap.add_argument("--json-out", default="portal/data/gbif-mycobank-comparison.json")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"FATAL: no input at {args.input}. Produce it first, e.g.:\n"
                 f"       python3 scripts/enrichFromMycobank.py --kingdom fungi")
    items = json.load(open(args.input))
    if args.limit:
        items = items[: args.limit]
    print(f"Comparing GBIF against MycoBank on {len(items):,} names MycoBank calls superseded\n")

    verdicts: list[dict] = []
    tally = Counter()
    started = time.time()

    for i in range(0, len(items), BATCH):
        chunk = items[i : i + BATCH]
        results = match_batch([c["ours"] for c in chunk])
        if len(results) != len(chunk):
            sys.exit(f"FATAL: batch returned {len(results)} for {len(chunk)} names; "
                     f"positional alignment would be wrong. Aborting rather than mis-pairing.")
        for c, r in zip(chunk, results):
            v, detail = classify(c["ours"], c["mycobank"], r)
            tally[v] += 1
            verdicts.append({**c, "verdict": v, "detail": detail})
        done = i + len(chunk)
        el = time.time() - started
        rate = done / el if el else 0
        print(f"  {done:>6,}/{len(items):,}  {el:>5.0f}s  "
              f"{rate:>5.1f} names/s  ETA {(len(items)-done)/rate:>4.0f}s")

    total = len(verdicts)
    print(f"\n{'=' * 66}")
    for v, n in tally.most_common():
        print(f"  {v:<26}{n:>8,}  {n/total*100:>5.1f}%")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# GBIF vs MycoBank: who says a fungal name is superseded\n\n")
        fh.write(f"GBIF Species API `v2/species/match` vs the `Current name` column of "
                 f"MycoBank's `MBList.xlsx`, over the names MycoBank flags as superseded.\n")
        fh.write(f"Measured {total:,} names.\n\n")
        fh.write("| verdict | count | share | meaning |\n|---|---|---|---|\n")
        meanings = {
            "agree": "both authorities move the name the same way",
            "disagree-gbif-keeps": "MycoBank wants to move it; GBIF has ours as accepted",
            "reversed": "GBIF says OUR name is accepted and the MycoBank target is the synonym",
            "disagree-third-name": "both name an accepted taxon, and they are different names",
            "gbif-does-not-know": "GBIF could not place the name (matchType NONE/HIGHERRANK)",
            "gbif-fuzzy": "GBIF matched fuzzily, which is not authority over a nomenclatural registry",
        }
        for v, n in tally.most_common():
            fh.write(f"| `{v}` | {n:,} | {n/total*100:.1f}% | {meanings.get(v,'')} |\n")
        fh.write("\n## Examples\n\n| ours | MycoBank | GBIF verdict | detail |\n|---|---|---|---|\n")
        seen = set()
        for r in verdicts:
            if r["verdict"] in seen:
                continue
            seen.add(r["verdict"])
            fh.write(f"| {r['ours']} | {r['mycobank']} | `{r['verdict']}` | {r['detail']} |\n")
        for v in tally:
            if v not in seen:
                for r in verdicts:
                    if r["verdict"] == v:
                        fh.write(f"| {r['ours']} | {r['mycobank']} | `{v}` | {r['detail']} |\n")
                        break
    print(f"\n  wrote {args.out}")
    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
        json.dump(verdicts, open(args.json_out, "w"), indent=1)
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())