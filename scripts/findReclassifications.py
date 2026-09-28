#!/usr/bin/env python3
"""Find species the portal names that GBIF now places in a different genus.

The description pass turned up a class of problem that is not about text at all.
When a species is moved to another genus, the old binomial becomes a synonym
and stops having an article of its own; Wikipedia redirects it to the new name.
`Abaraeus hamifer` is now `Temnosceloides hamifer`, and the tree is carrying the
old one. That is wrong data rather than missing data, and a synonym mapping
fixes it in a way that more prose never could.

GBIF's backbone is the authority here: `/v1/species/match` reports
`taxonomicStatus` and `acceptedUsageKey` for a name. A name whose status is not
ACCEPTED, or whose accepted usage sits in a different genus, is a
reclassification candidate. The Wikipedia redirect recorded in
portal/data/description-lookup.jsonl is kept alongside as an independent
second opinion, and the two are compared.

Usage:
    python3 scripts/findReclassifications.py                    # dry run
    python3 scripts/findReclassifications.py --out reclass.json --apply
"""
import argparse
import collections
import json
import os
import re
import time
import urllib.parse
import urllib.request

LEDGER = os.path.join("portal", "data", "description-lookup.jsonl")
UA = "systema-naturae-audit/1.0 (https://github.com/tobese/systema-naturae)"
DELAY = 0.12          # be polite to a public API


def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            if a == tries - 1:
                return None
            time.sleep(1.2 * (a + 1))
    return None


def binomial(n):
    p = re.sub(r"\s+[A-Z][a-z]+,?\s*\d{4}.*$", "", n.strip()).split()
    p = [x for x in p if x]
    if len(p) < 2:
        return None, None
    return p[0], p[1]


def candidates(path=LEDGER):
    """Rejected species whose Wikipedia redirect kept the epithet but changed
    the genus - the signature of a reclassification rather than a collision."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i == 0:
                continue
            r = json.loads(line)
            if r.get("s") != "rejected":
                continue
            g1, e1 = binomial(r["n"])
            g2, e2 = binomial(r.get("t") or "")
            if not (g1 and e1 and g2 and e2):
                continue
            if g1.lower() == g2.lower():
                continue
            if e1.lower() == e2.lower():
                out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=LEDGER)
    ap.add_argument("--out", default="")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cands = candidates(args.ledger)
    print(f"{len(cands)} rejected names redirect to a different genus, same epithet")
    if not cands:
        return

    out, tally = [], collections.Counter()
    for i, r in enumerate(cands, 1):
        name = r["n"]
        m = get("https://api.gbif.org/v1/species/match?strict=false&name="
                + urllib.parse.quote(name))
        time.sleep(DELAY)
        if not m:
            tally["gbif-error"] += 1
            continue
        status = (m.get("status") or "").upper()
        accepted_key = m.get("acceptedUsageKey") or m.get("usageKey")
        acc_name = None
        if status != "ACCEPTED" and accepted_key:
            a = get(f"https://api.gbif.org/v1/species/{accepted_key}")
            time.sleep(DELAY)
            if a:
                acc_name = a.get("canonicalName") or a.get("scientificName")
        g1, e1 = binomial(name)
        ga, ea = binomial(acc_name or "")
        moved_genus = bool(ga and ea and ga.lower() != g1.lower() and ea.lower() == e1.lower())
        rec = {
            "name": name,
            "gbifStatus": status or None,
            "gbifAccepted": acc_name,
            "gbifMatch": m.get("scientificName"),
            "confidence": m.get("confidence"),
            "wikipediaRedirect": r.get("t"),
            "movedGenus": moved_genus,
        }
        out.append(rec)
        if status == "ACCEPTED" and not moved_genus:
            tally["gbif-says-accepted"] += 1
        elif moved_genus:
            tally["confirmed-reclassified"] += 1
        else:
            tally["ambiguous"] += 1
        if i % 50 == 0:
            print(f"  {i}/{len(cands)} {dict(tally)}", flush=True)

    print(f"\n{dict(tally)}")
    conf = [r for r in out if r["movedGenus"]]
    print(f"\nconfirmed genus moves: {len(conf)}")
    agree = sum(1 for r in conf
                if (binomial(r["wikipediaRedirect"] or "")[0] or "").lower()
                == (binomial(r["gbifAccepted"] or "")[0] or "").lower())
    print(f"  of which Wikipedia redirect agrees with GBIF: {agree}/{len(conf)}")
    for r in conf[:15]:
        print(f"    {r['name']}  ->  {r['gbifAccepted']}   "
              f"(GBIF {r['gbifStatus']}, wikipedia {r['wikipediaRedirect']})")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)
        print(f"\nwrote {len(out)} records -> {args.out}")


if __name__ == "__main__":
    main()
