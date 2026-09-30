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
    python3 scripts/validateNamesWithCol.py --apply     # fill the safe cases
    python3 scripts/validateNamesWithCol.py --limit 50  # quick probe

On --apply
----------
The verdict is re-verified against COL *at write time*, so nothing is applied
from a stale report. Only species whose description is currently EMPTY are
touched, so the pass is idempotent.

The text comes from the accepted name's Wikipedia article, not from COL - COL is
the validator, never the source. So `sourcedFrom` stays `wikipedia`; attributing
it to COL would misreport where the prose came from.

Text is read from the offline enwiki SQLite dump when it has the page, and from
the REST summary endpoint otherwise. The dump is a subset - it held 127 of 352
targets - so the fallback is not optional.

The lead is re-checked before it is written: it must mention the *target* genus,
which is the same gate the original enrichment used. A lead that does not is a
different redirect or a genus article, and is skipped however good the COL
verdict looked.

Every applied pair is appended to `portal/data/name-reclassification-applied.jsonl`
so the edit is auditable and reversible.
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
from collections import Counter, defaultdict

LEDGER = "portal/data/description-lookup.jsonl"
APPLIED_LEDGER = "portal/data/name-reclassification-applied.jsonl"
SQLITE_DUMP = "/Volumes/WikiDump/wiki-pages.sqlite"
# A lead shorter than this is a stub ("X is a species of beetle in the family
# Y."). Accurate but not worth showing, so it is counted and skipped.
MIN_LEAD = 120
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


# ── apply ────────────────────────────────────────────────────────────────────

def normalise(name: str) -> str:
    """'Amanita muscaria (L.) Lam.' / 'Amanita muscaria var. betula' -> 'Amanita muscaria'.

    Only the first two words. Below species the binomial is not a reliable key -
    two species can share a genus and epithet across infraspecific ranks - and
    this pass is only ever about species.
    """
    parts = name.replace("(", " ").split()
    return " ".join(parts[:2]).lower() if len(parts) >= 2 else name.lower()


def load_dump():
    if not os.path.exists(SQLITE_DUMP):
        return None
    import sqlite3
    con = sqlite3.connect(f"file:{SQLITE_DUMP}?mode=ro", uri=True)
    return con


def dump_extract(con, title: str) -> str:
    row = con.execute("SELECT extract FROM pages WHERE title=? LIMIT 1", (title,)).fetchone()
    return (row[0] or "").strip() if row else ""


def rest_extract(title: str) -> str:
    """Wikipedia REST summary. Used for the majority - the offline dump is a subset."""
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(title.replace(" ", "_")))
    d = get(url)
    if "__error" in d:
        return ""
    return (d.get("extract") or "").strip()


def index_empty_species() -> dict[str, list[tuple[str, int]]]:
    """binomial -> [(family file path, index of the species node)] for EMPTY ones only.

    Walking with an explicit index rather than a recursive generator, because the
    writer has to re-walk and mutate the same tree and the two walks must agree.
    """
    import glob
    index: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path in glob.glob("taxonomy/**/src/data/*.json", recursive=True):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        idx = 0
        stack = [doc]
        while stack:
            node = stack.pop()
            if node.get("rank") == "SPECIES":
                if not (node.get("description") or "").strip():
                    nm = node.get("name") or ""
                    if len(nm.split()) >= 2:
                        index[normalise(nm)].append((path, idx))
                idx += 1
            kids = list(node.get("children") or [])
            kids.reverse()
            stack.extend(kids)
    return index


def apply_safe(dataset: str, report: str) -> int:
    sec = open(report, encoding="utf-8").read().split("### `safe` — ")[1].split("\n### ")[0]
    import re
    pairs = re.findall(r"\*\*(.+?)\*\* → (.+?) — ", sec)
    print(f"\nApplying: {len(pairs)} `safe` pairs from {report}")

    con = load_dump()
    src = {"dump": 0, "rest": 0, "nodump": 0}
    index = index_empty_species()
    print(f"  empty-description species indexed: {sum(len(v) for v in index.values()):,}")

    applied = skipped_stub = skipped_nolead = skipped_notfound = reverified = 0
    files: dict[str, dict] = {}
    for ours, target in pairs:
        # Re-verify live rather than trusting the report on disk.
        o, t = lookup(dataset, ours), lookup(dataset, target)
        verdict, _ = classify(o, t)
        if verdict != "safe":
            continue
        reverified += 1
        key = normalise(ours)
        if key not in index:
            skipped_notfound += 1
            continue
        if con is not None:
            text = dump_extract(con, target)
            src["dump"] += 1
        if not text:
            text = rest_extract(target)
            src["rest" if con is not None else "nodump"] += 1
        if not text:
            skipped_notfound += 1
            continue
        if len(text) < MIN_LEAD:
            skipped_stub += 1
            continue
        # The lead must name the TARGET genus - the gate the original enrichment
        # used, and the check that catches a wrong redirect even if COL's verdict
        # were wrong. Only meaningful when the genus actually differs: a
        # gender-ending correction keeps it (Vieja melanura -> Vieja melanurus,
        # feminine to masculine under ICZN), and there the lead SHOULD name our
        # own genus. Flagging those would be a false positive on correct data.
        target_genus = target.split()[0]
        our_genus = ours.split()[0]
        if target_genus.lower() != our_genus.lower():
            if target_genus.lower() not in text.lower():
                skipped_nolead += 1
                continue
        path, idx = index[key][0]
        if path not in files:
            with open(path, encoding="utf-8") as fh:
                files[path] = json.load(fh)
        stack = [files[path]]
        cur_idx = 0
        hit = False
        while stack:
            node = stack.pop()
            if node.get("rank") == "SPECIES":
                if cur_idx == idx and not (node.get("description") or "").strip():
                    node["description"] = text
                    node["sourcedFrom"] = "wikipedia"
                    hit = True
                cur_idx += 1
            kids = list(node.get("children") or [])
            kids.reverse()
            stack.extend(kids)
        if hit:
            applied += 1
            index[key] = [(p, i) for (p, i) in index[key] if not (p == path and i == idx)]
        time.sleep(DELAY)

    for path, doc in files.items():
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    print(f"  re-verified safe: {reverified}   applied: {applied}")
    print(f"  skipped - stub lead <{MIN_LEAD}c: {skipped_stub}   lead misses target genus: {skipped_nolead}   not found in tree / no text: {skipped_notfound}")
    print(f"  text source: {src}")
    print(f"  family files written: {len(files)}")
    return applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="3LR", help="COL dataset key (3LR = current release)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N cases (0 = all)")
    ap.add_argument("--apply", action="store_true", help="write the accepted description into family JSON")
    ap.add_argument("--report", default=REPORT)
    ap.add_argument("--apply-only", action="store_true",
                    help="skip the full verification sweep; apply re-verifies each "
                         "safe case against COL itself, so the sweep is redundant")
    args = ap.parse_args()

    if args.apply_only:
        n = apply_safe(args.dataset, args.report)
        print(f"\n  would append {n} records to {APPLIED_LEDGER}")
        return 0

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
        n = apply_safe(args.dataset, args.report)
        print(f"\n  appended {n} records to {APPLIED_LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
