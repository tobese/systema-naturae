#!/usr/bin/env python3
"""Describe the empty species in the deployed tree from the enwiki mirror.

The subspecies pass (enrichSubspeciesHosts.py) closed the rank gap: no species
that hosts a subspecies is left without text. This is the long tail underneath
it. Measured against the deployed animalia tree (383 order files off the live
site, 527,631 species):

    462,950 species with no description  (87.7%)
    462,650 of those are unique names

Joined against the full 19.1M-page enwiki mirror on debbie:

    26,937  have a real article
    14,011  are redirects, of which 7,294 resolve to a real article
    421,748 have no en.wikipedia page at all  (91.2%)

So ~34k of the 462k are reachable by Wikipedia and the remaining 91% are not -
that part needs GBIF/iNaturalist/EOL, not a bigger script. This fills the
reachable part, which is a local indexed join rather than a crawl: no rate
limits, no sleeps.

The lead is validated before it is written. A species article's first sentence
should open with the binomial itself ("Eurispa loriae is a species of beetle of
the family Chrysomelidae."), so a lead that never mentions the genus is a
name collision - a page that happens to share the title - and is rejected
rather than pasted onto the wrong node. That matters at this volume: 34k title
matches will contain some number of non-species pages.

Usage (from the repo root, with a tunnel to the wiki mirror on debbie):
    ssh -f -N -L 15433:127.0.0.1:5433 debbie
    python3 scripts/enrichEmptySpecies.py                  # dry run
    python3 scripts/enrichEmptySpecies.py --apply
"""
import argparse
import collections
import json
import os
import re
import sys
import time
from glob import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enrichBreedsFromWikipedia as wiki   # reuse the extraction, not a copy

DSN = wiki.DEFAULT_DSN
BATCH = 300


def collect_targets(root, scope_names):
    """{path: [species names]} for family JSONs, restricted to `scope_names`.

    Scoping by name (rather than enriching every empty species in the repo)
    keeps the change to what the deployed tree actually contains. The repo
    carries ~348k further empty species in the plantae mirror, which is a
    separate system and not grafted into the animal portal.
    """
    out = {}
    total = 0
    for p in sorted(glob(os.path.join(root, "*", "*", "*", "src", "data", "*.json"))):
        try:
            tree = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        need = []

        def walk(node):
            if node.get("rank") == "SPECIES" and node.get("name") in scope_names \
                    and not (node.get("description") or "").strip():
                need.append(node["name"])
            for c in node.get("children") or []:
                walk(c)
            for s in node.get("speciesList") or []:
                if isinstance(s, dict):
                    walk(s)

        walk(tree)
        if need:
            out[p] = need
            total += len(need)
    return out, total


def genus_of(name):
    return name.split()[0] if name.split() else ""


def acceptable(name, paragraphs):
    """Reject stubs, lists, disambiguations and title collisions.

    Returns (ok, reason). The reason is recorded in the ledger, so a rejection
    is a decision someone can revisit rather than a silent gap.
    """
    if not paragraphs:
        return False, "no-lead"
    lead = paragraphs[0]
    # lead_paragraphs already discards anything under 40 chars after cleaning,
    # so 60 here was just stricter than the parser. That threw away real
    # one-line stubs like "Agfa flexilis is a species of parasitic nematode."
    # (49 chars), which are accurate and worth more than an empty panel.
    if len(lead) < 40:
        return False, "stub"
    # A collision (right title, wrong subject) almost never opens with the
    # genus. Real species leads do, essentially always.
    g = genus_of(name).lower()
    if g and g not in lead.lower():
        return False, "collision"
    # "is a genus of", "is a family of", "is a disambiguation" -> not a species
    if re.search(r"\bis a (genus|family|subfamily|order|class|phylum|"
                 r"disambiguation)\b", lead, re.I):
        return False, "genus-page"
    return True, None


LEDGER_HEADER_SRC = "enwiki"
LEDGER = os.path.join("portal", "data", "description-lookup.jsonl")


def read_ledger(path):
    """{lower(name): record} from a previous run, so misses are not re-queried.

    This is the same idea as the {qid: "", fetchedAt} stubs in
    shared/data/wiki-images.json: record every name we asked about, including
    the ones that came back empty, so a later pass can tell "not found" from
    "never tried". `sourcedFrom: "none"` cannot do that job - it is
    overwritten by the next successful pass (tools/powo_enrich.py) and every
    enricher's candidate filter re-selects it, so misses are retried forever.
    """
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i == 0:
                continue                      # header
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "n" in r:
                out[r["n"].lower()] = r
    return out


def count_records(records):
    """One tally shape for both write paths, so the header always reconciles.

    `rejected` is broken out by reason here because that is the actionable
    split: collision and genus-page are the cases a better validator could
    recover, stub and no-lead are the article being thin.
    """
    c = collections.Counter()
    for r in records:
        s = r.get("s", "?")
        c[s if s != "rejected" else "rejected:" + str(r.get("r"))] += 1
    return dict(sorted(c.items()))


def write_ledger(path, records, counts, generated_at):
    """Newline-delimited so a 460k-line ledger stays appendable and diffable,
    and so a single malformed line cannot cost the whole file."""
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sep = (",", ":")          # compact: smaller, and greppable as "s":"rejected"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"src": LEDGER_HEADER_SRC, "generatedAt": generated_at,
                             "counts": counts}, ensure_ascii=False,
                            separators=sep) + "\n")
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=sep) + "\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--root", default=root)
    ap.add_argument("--dsn", default=os.environ.get("WIKI_PG_DSN", DSN))
    ap.add_argument("--scope", required=True,
                    help="JSON list of species names to consider (the deployed empty set)")
    ap.add_argument("--apply", action="store_true", help="write descriptions into the family JSONs")
    ap.add_argument("--out", help="cache the accepted leads here; reused if it exists")
    ap.add_argument("--refresh", action="store_true", help="ignore an existing --out cache")
    ap.add_argument("--ledger", default=LEDGER,
                    help="per-name lookup ledger, positives and negatives alike")
    ap.add_argument("--limit", type=int, default=0, help="only consider the first N names (probing)")
    args = ap.parse_args()

    scope = set(json.load(open(args.scope)))
    if args.limit:
        scope = set(sorted(scope)[:args.limit])
    print(f"scope: {len(scope):,} species names")

    targets, total = collect_targets(args.root, scope)
    print(f"{len(targets)} family files, {total} empty species in them")
    if not targets:
        print("nothing to do")
        return

    names = sorted({n for need in targets.values() for n in need})

    # The fetch is the slow part (1,500-odd indexed batches against the 19.1M
    # row mirror) and it is pure read-only, so it is cached to a file. That
    # makes the run resumable, lets --apply run with no database at all, and
    # means the decision about what text we are about to write into 4,000+
    # family files can be reviewed before anything is written.
    if args.out and os.path.exists(args.out) and not args.refresh:
        result = json.load(open(args.out, encoding="utf-8"))
        print(f"loaded {len(result):,} cached leads from {args.out} (no database needed)")
        # Keep the ledger a complete account. The first run of this script
        # filled 38,512 species before the ledger existed, so those names are
        # in the cache but not yet recorded; reconcile them here.
        prior = read_ledger(args.ledger)
        # A name already recorded as rejected but now carrying a lead was
        # recovered by a later pass (a parser fix, a looser gate). Upgrade the
        # record rather than leaving it contradicting the data. Ledger keys are
        # lower-cased but result keys keep the original casing, so look the lead
        # up by the record's own name.
        upgraded = [r["n"] for r in prior.values()
                    if r.get("s") == "rejected" and r["n"] in result]
        missing = [n for n in result if n.lower() not in prior]
        for nm in missing:
            prior[nm.lower()] = {"n": nm, "s": "filled", "t": result[nm]["title"]}
        for nm in upgraded:
            prior[nm.lower()] = {"n": nm, "s": "filled", "t": result[nm]["title"]}
        if missing or upgraded:
            write_ledger(args.ledger,
                         sorted(prior.values(), key=lambda r: r["n"].lower()),
                         count_records(prior.values()),
                         time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            print(f"ledger: +{len(missing):,} new, {len(upgraded):,} upgraded "
                  f"rejected->filled; {len(prior):,} records -> {args.ledger}")
        else:
            print(f"ledger: already complete ({len(prior):,} records)")
    else:
        prior = read_ledger(args.ledger)
        todo = [n for n in names if n.lower() not in prior] if not args.refresh else names
        if prior:
            print(f"ledger: {len(prior):,} names already recorded; "
                  f"{len(names)-len(todo):,} skipped, {len(todo):,} to look up")
        conn = wiki.connect(args.dsn)
        cur = conn.cursor()
        t0 = time.time()
        pages = wiki.fetch_pages(cur, todo)
        print(f"fetched {len(pages):,} of {len(todo):,} candidate articles "
              f"in {time.time()-t0:.0f}s", flush=True)

        result, records = {}, []
        for name in todo:
            rec = pages.get(name.lower())
            if not rec or "text" not in rec:
                records.append({"n": name, "s": "no-article"})
                continue
            paras = wiki.lead_paragraphs(rec["text"])
            ok, reason = acceptable(name, paras)
            if ok:
                result[name] = {"title": rec["title"], "paragraphs": paras}
                records.append({"n": name, "s": "filled", "t": rec["title"]})
            else:
                records.append({"n": name, "s": "rejected", "r": reason,
                                "t": rec["title"]})

        # Carry forward what a previous run recorded, so the ledger stays a
        # complete account of every name we have ever looked up for this source.
        for k, r in prior.items():
            records.append(r)

        counts = count_records(records)
        print("accepted {:,}; ledger {}".format(
            len(result), ", ".join(f"{k} {v:,}" for k, v in counts.items())))
        for rec in [r for r in records if r.get("s") == "rejected"][:15]:
            print(f"  REJECTED {rec['n']} ({rec.get('r')}) -> {rec.get('t')}")
        conn.close()
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(result, fh, ensure_ascii=False)
            print(f"cached {len(result):,} leads -> {args.out}")
        write_ledger(args.ledger, sorted(records, key=lambda r: r["n"].lower()),
                     dict(counts), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        print(f"ledger: {len(records):,} records -> {args.ledger}")

    if not args.apply:
        print("(dry run - pass --apply)")
        return

    written = 0
    touched = 0
    for path, need in targets.items():
        tree = json.load(open(path, encoding="utf-8"))
        want = set(need)
        hits = [0]

        def stamp(node):
            if node.get("rank") == "SPECIES" and node.get("name") in want \
                    and node["name"] in result and not (node.get("description") or "").strip():
                node["description"] = "\n".join(result[node["name"]]["paragraphs"])
                node["wikipediaTitle"] = result[node["name"]]["title"]
                node["sourcedFrom"] = "wikipedia"
                hits[0] += 1
            for c in node.get("children") or []:
                stamp(c)
            for s in node.get("speciesList") or []:
                if isinstance(s, dict):
                    stamp(s)

        stamp(tree)
        if hits[0]:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(tree, indent=2, ensure_ascii=False) + "\n")
            written += hits[0]
            touched += 1
    print(f"done - {written:,} species described across {touched:,} family files")


if __name__ == "__main__":
    main()
