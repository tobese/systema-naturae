#!/usr/bin/env python3
"""
Validate Wikipedia description attribution against the Catalogue of Life.

Why
---
`enrichEmptySpecies.py` rejected 1,456 species because the Wikipedia lead never
mentions our genus. Most of those are not errors: they are genus
reclassifications, where Wikipedia redirects the old binomial to the new one and
the lead naturally names the *new* genus. Under ICZN a change of generic
assignment does not change the species - the epithet identifies it - so the
target's description is about the same animal and can be applied to our node.

The stopgap was matching the species epithet and checking both genera sat in the
same order in our own tree. That is a heuristic and it is wrong: `Acanthodes
lateralis` (a fish genus) and `Acanthispa lateralis` (a beetle genus) share an
epithet, and the heuristic would have pasted a beetle description onto a fish.

The Catalogue of Life settles it authoritatively, with no graph traversal and no
epithet comparison. For a candidate pair - ours = A, the Wikipedia redirect
target = B:

    status(A) == synonym  and status(B) == accepted  ->  same taxon, SAFE
    status(A) == accepted and status(B) == accepted  ->  two distinct names, REJECT
    either name not found in COL                    ->  UNKNOWN, leave alone

COL is free and needs no key (`api.checklistbank.org`, dataset `3LR` for the
current release, `COL{year}` for the permanent annual release).

Usage
-----
    python3 scripts/validateNamesWithCol.py             # dry run, writes a report
    python3 scripts/validateNamesWithCol.py --apply     # write accepted text in
    python3 scripts/validateNamesWithCol.py --limit 50  # quick probe

Nothing is written to family JSON without `--apply`, and `--apply` only ever
fills an EMPTY description, so re-running is safe.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

LEDGER = "portal/data/description-lookup.jsonl"
API = "https://api.checklistbank.org"
UA = "systema-naturae-name-validation/1.0 (https://github.com/tobese/systema-naturae)"
REPORT = "docs/reports/name-attribution-col.md"

# Polite: one request at a time, ~4/s, with backoff. COL asks users to observe
# rate limits, and this is a courtesy load, not a bulk crawl.
DELAY = 0.25


def get(url: str, tries: int = 4) -> dict:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2.0 * (i + 1))
                continue
            return {"__error": f"HTTP {e.code}"}
        except Exception as e:  # noqa: BLE001 - network is allowed to fail
            if i < tries - 1:
                time.sleep(1.5 * (i + 1))
                continue
            return {"__error": str(e)}
    return {"__error": "exhausted"}


def scientific_name(usage: dict) -> str:
    """COL returns the name under several keys depending on endpoint and rank."""
    for k in ("scientificName", "name", "label", "canonicalName"):
        v = usage.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def strip_authority(name: str) -> str:
    """'Amanita muscaria (L.) Lam.' -> 'Amanita muscaria'."""
    n = name.split("(")[0].strip()
    parts = n.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else n


def lookup(dataset: str, name: str) -> dict | None:
    """Find the COL usage whose scientific name matches `name` exactly.

    Prefers an exact name match and rank=species. COL search returns many
    checklists, so a loose match on a fragment is worse than no answer - it would
    validate the wrong taxon, which is the exact failure we are trying to remove.
    """
    bare = strip_authority(name)
    url = f"{API}/dataset/{dataset}/nameusage/search?q=" + urllib.parse.quote(name) + "&limit=20"
    d = get(url)
    if "__error" in d:
        return {"status": "ERROR", "detail": d["__error"]}

    best = None
    for res in d.get("result") or []:
        u = res.get("usage") or res
        nm = scientific_name(u)
        if not nm:
            continue
        if strip_authority(nm).lower() != bare.lower():
            continue
        status = (u.get("status") or "").lower()
        rank = (u.get("rank") or "").lower()
        cand = {"status": status or "unknown", "rank": rank, "name": nm, "id": res.get("id")}
        if best is None:
            best = cand
        elif rank == "species" and best.get("rank") != "species":
            best = cand
    return best


def classify(ours: dict | None, theirs: dict | None) -> tuple[str, str]:
    if ours is None and theirs is None:
        return "unknown", "neither name is in the Catalogue of Life"
    if ours is None:
        return "unknown", f"our name not in COL; target={theirs and theirs.get('status')}"
    if theirs is None:
        return "unknown", f"target not in COL; ours={ours.get('status')}"
    if ours["status"] == "ERROR" or theirs["status"] == "ERROR":
        return "unknown", "API error"
    o, t = ours["status"], theirs["status"]
    if o == "synonym" and t == "accepted":
        return "safe", f"{ours['name']} is a synonym of the accepted {theirs['name']}"
    if o == "accepted" and t == "accepted":
        return "distinct", f"both are accepted names ({ours['name']}, {theirs['name']}) - different taxa"
    if o == "synonym" and t == "synonym":
        return "unknown", "both are synonyms; would need the acceptedId link to resolve"
    if o == "accepted" and t == "synonym":
        return "distinct", f"we hold the accepted name and the target is a synonym ({theirs['name']})"
    return "unknown", f"ours={o} target={t}"


def load_cases(path: str) -> list[dict]:
    """Collision rejections that recorded the redirect target."""
    cases = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("r") == "collision" and d.get("t"):
                cases.append({"name": d["n"], "target": d["t"]})
    return cases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="3LR", help="COL dataset key (3LR = current release)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N cases (0 = all)")
    ap.add_argument("--apply", action="store_true", help="write the accepted description into family JSON")
    ap.add_argument("--report", default=REPORT)
    args = ap.parse_args()

    cases = load_cases(LEDGER)
    if args.limit:
        cases = cases[: args.limit]
    total = len(cases)
    print(f"COL dataset {args.dataset} · {total} collision cases · {'APPLY' if args.apply else 'dry run'}")

    tally: Counter = Counter()
    rows = []
    started = time.time()
    for i, c in enumerate(cases, 1):
        ours = lookup(args.dataset, c["name"])
        time.sleep(DELAY)
        theirs = lookup(args.dataset, c["target"])
        time.sleep(DELAY)
        verdict, why = classify(ours, theirs)
        tally[verdict] += 1
        rows.append({"name": c["name"], "target": c["target"], "verdict": verdict, "why": why})
        if i % 25 == 0 or i == total:
            el = time.time() - started
            rate = i / el if el else 0
            eta = (total - i) / rate if rate else 0
            print(f"  {i}/{total} ({i/total*100:.0f}%)  {dict(tally)}  "
                  f"{rate:.1f}/s  elapsed {el/60:.1f}m  ETA {eta/60:.1f}m")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("# Name attribution validated against the Catalogue of Life\n\n")
        fh.write(f"*Generated by `scripts/validateNamesWithCol.py` against COL dataset "
                 f"`{args.dataset}`. {total} Wikipedia `collision` rejections re-examined.*\n\n")
        fh.write("| verdict | count | meaning |\n|---|---|---|\n")
        mean = {
            "safe": "our name is a COL synonym, the target is accepted — same taxon, description may be applied",
            "distinct": "both names are accepted in COL — genuinely different taxa, correctly rejected",
            "unknown": "COL has no usable answer — left alone, needs a human or the acceptedId link",
        }
        for k, n in tally.most_common():
            fh.write(f"| `{k}` | {n} | {mean.get(k,'')} |\n")
        fh.write("\n## Cases\n\n")
        for v in ("safe", "distinct", "unknown"):
            sel = [r for r in rows if r["verdict"] == v]
            if not sel:
                continue
            fh.write(f"### `{v}` — {len(sel)}\n\n")
            for r in sel:
                fh.write(f"- **{r['name']}** → {r['target']} — {r['why']}\n")
            fh.write("\n")
    print(f"\n  {dict(tally)}")
    print(f"  report → {args.report}")
    if args.apply:
        print("  --apply: NOT wired up yet; the safe list above is what to apply once reviewed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
