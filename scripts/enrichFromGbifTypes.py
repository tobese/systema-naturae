#!/usr/bin/env python3
"""Fill the no-article species from GBIF, selecting descriptions by `type`.

`docs/coverage.md` rejected GBIF as a prose source after measuring 0.1% yield on
Cephalopoda, and the reason given was that what comes back is specimen and
holotype debris. That measurement is right about the *result* and wrong about
the *cause*.

GBIF's `/species/{key}/descriptions` does not return one blob of text. It
returns one record per treatment section, each tagged with a `type`:

    type=description          "Length to 9.5 mm, width 0.59 mm. Body with up to
                               79 chaetigers. Prostomium with a pair of anterior
                               eyespots..."          <- 921 chars of real morphology
    type=distribution         "Mediterranean Sea, Bermuda, Antilles, ..."    <- not a description
    type=materials_examined   "EAST TIMOR. East of Atauro reef, 08 13 48 S..."  <- specimen log
    type=etymology, discussion, diagnosis, morphology, ...

`portal/scripts/enrichFromGbifDescriptions.ts` gates on the *text prefix*
(`REJECT_PREFIX` includes `description|diagnosis|remarks|...`), so it throws
away the good records for containing the word "Description." while keeping
whatever slipped past. Selecting on `type` instead, against the same 120-species
sample:

    prefix gate   2/120  (2%)   -> ~10,000 species
    type gate     9/120  (8%)   -> ~31,600 species

Four times the yield for a stricter, not looser, criterion - the difference is
entirely which records get read.

The type vocabulary is not clean: it includes Spanish values ("hábitat", "uso")
and outright junk (an authority string, "astyanax baird & girard", used as a
type). Hence a whitelist rather than a blacklist. `discussion` is left out on
purpose: it is often good, but it is also where speculation lives.

This writes the same ledger shape as the enwiki pass, one file per source, so
"tried and found nothing" is recorded and never re-asked.

Usage:
    python3 scripts/enrichFromGbifTypes.py --scope portal/data/description-lookup.jsonl
    python3 scripts/enrichFromGbifTypes.py --scope ... --out gbif.json --apply
"""
import argparse
import collections
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from familyFiles import iter_family_files  # discovers the layout instead of assuming it
from enrichEmptySpecies import count_records, read_ledger, write_ledger  # noqa: E402

UA = "systema-naturae/1.0 (https://github.com/tobese/systema-naturae)"
LEDGER = os.path.join("portal", "data", "description-lookup-gbif.jsonl")

# Types that carry a description of the taxon itself.
GOOD_TYPES = {"description", "diagnosis", "morphology", "generic_description",
              "specific_description", "redescription"}
MIN_LEN = 120         # below this it is a stub sentence, not a description
WORKERS = 8
DELAY = 0.10

# The section label GBIF inherits from the treatment, e.g. "Description. ..." or
# "Diagnosis: ...". Kept, it reads as debris in a species panel.
LABEL = re.compile(r"^\s*(description|diagnosis|redescription|morphology|"
                   r"generic description|specific description|treat(?:ment)?)\b"
                   r"[\s:.\-–—]*", re.I)

# A taxonomic description is allowed to be measurement-heavy - that is what it
# is for - but a record that is *only* measurements is a data table, not prose.
JUNK = (
    re.compile(r"^\s*\d{4}\.\s"),                       # bare citation stub
    re.compile(r"complete description in\b", re.I),     # cross-reference, no text
    re.compile(r"\b(trud|zoologisk|zeitschrift|ann\.? soc)\b", re.I),
)


def strip_label(t):
    return LABEL.sub("", t).strip()


def looks_like_prose(t):
    """Cheap quality bar for treatment prose."""
    if len(t) < MIN_LEN:
        return False
    if any(p.search(t) for p in JUNK):
        return False
    words = re.findall(r"[A-Za-z]{3,}", t)
    if len(words) < 25:
        return False
    numbers = len(re.findall(r"\d", t))
    if numbers > len(t) * 0.22:            # mostly a measurement table
        return False
    return True


def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 429:            # back off politely, it is a public API
                time.sleep(2 + 2 * a)
                continue
            if a == tries - 1:
                return None
            time.sleep(1.0 * (a + 1))
        except Exception:
            if a == tries - 1:
                return None
            time.sleep(1.0 * (a + 1))
    return None


def probe(name):
    """-> (key, [descriptions]) or (None, [])"""
    m = get("https://api.gbif.org/v1/species/match?strict=false&name="
            + urllib.parse.quote(name))
    time.sleep(DELAY)
    if not m or not m.get("usageKey"):
        return name, None, []
    d = get(f"https://api.gbif.org/v1/species/{m['usageKey']}/descriptions?limit=50")
    time.sleep(DELAY)
    if not d:
        return name, m["usageKey"], []
    return name, m["usageKey"], (d.get("results") or [])


def pick(name, descs):
    """Best usable description record for this name, or (None, reason).

    Deliberately does *not* reuse the enwiki `acceptable()`, which requires the
    genus to appear in the text. A Wikipedia lead always opens with the binomial
    ("Eurispa loriae is a species of beetle..."), but a taxonomic treatment
    starts mid-description - "Description. BL: 6.3 mm; BW: 3.78 mm. Body black
    except mouth parts brownish..." - and never restates the name. Applying the
    enwiki rule here rejected good descriptions wholesale: 19 of 36 usable
    records in a 300-name probe were turned down for "collision" when they were
    the best text available for those species.
    """
    seen = set()
    cands = []
    for r in descs:
        t = (r.get("type") or "?").strip().lower()
        seen.add(t)
        if t not in GOOD_TYPES:
            continue
        txt = strip_label((r.get("description") or "").strip())
        if looks_like_prose(txt):
            cands.append(txt)
    if not cands:
        return None, ("no-good-type" if seen else "no-description")
    return max(cands, key=len), None


MAX_CHARS = 1500       # a treatment can run to 50,000 chars; a panel cannot


def truncate(t, cap=MAX_CHARS):
    """Cut at a sentence boundary so the result still reads as prose.

    47% of the 27,492 recovered descriptions exceed 2,000 characters and the
    longest is 49,906 - a whole treatment paper, not a species description.
    The full length stays in the ledger; only what a panel shows is capped.
    """
    if len(t) <= cap:
        return t
    cut = t[:cap]
    m = list(re.finditer(r"[.!?](?=\s|$)", cut))
    if m and m[-1].end() > cap * 0.5:
        return cut[:m[-1].end()].strip()
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 0 else cut).strip() + "…"


def apply_descriptions(result, root):
    """Write the recovered prose into the family JSONs."""
    import glob
    written = touched = 0
    by_name = {}
    for name, v in result.items():
        by_name.setdefault(name, v)
    for p in sorted(list(iter_family_files(root))):
        tree = json.load(open(p, encoding="utf-8"))
        hits = [0]

        def stamp(node):
            if node.get("rank") == "SPECIES":
                n = node.get("name")
                rec = by_name.get(n)
                if rec and not (node.get("description") or "").strip():
                    node["description"] = truncate(rec["paragraphs"][0])
                    node["wikipediaTitle"] = rec["title"]
                    node["sourcedFrom"] = "gbif"
                    hits[0] += 1
            for c in node.get("children") or []:
                stamp(c)
            for s in node.get("speciesList") or []:
                if isinstance(s, dict):
                    stamp(s)

        stamp(tree)
        if hits[0]:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(tree, indent=2, ensure_ascii=False) + "\n")
            written += hits[0]
            touched += 1
    return written, touched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--scope", default="portal/data/description-lookup.jsonl",
                    help="the enwiki ledger; only its no-article rows are retried")
    ap.add_argument("--ledger", default=LEDGER)
    ap.add_argument("--out", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", type=int, default=0,
                    help="probe a random N instead of everything (measurement)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    todo = []
    with open(args.scope, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i == 0:
                continue
            r = json.loads(line)
            if r.get("s") == "no-article":
                todo.append(r["n"])
    if args.sample:
        random.seed(7)
        todo = random.sample(todo, min(args.sample, len(todo)))
    print(f"{len(todo):,} no-article species to try against GBIF")

    prior = read_ledger(args.ledger)
    if prior and not args.refresh:
        before = len(todo)
        todo = [n for n in todo if n.lower() not in prior]
        print(f"ledger: {len(prior):,} already recorded, "
              f"{before - len(todo):,} skipped, {len(todo):,} to look up")

    if not todo:
        # Everything already looked up. If a results cache exists, this is a
        # re-apply after the tree moved - the fetch is the expensive part and
        # it does not need repeating.
        if args.out and os.path.exists(args.out):
            cached = json.load(open(args.out, encoding="utf-8"))
            print(f"ledger complete; re-applying {len(cached):,} cached descriptions")
            if args.apply:
                written, touched = apply_descriptions(cached, args.root)
                print(f"applied: {written:,} species described across {touched:,} family files")
            else:
                print("(dry run - pass --apply)")
        else:
            print("nothing to do")
        return

    result, records = {}, []
    tally = collections.Counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for done, (name, key, descs) in enumerate(ex.map(probe, todo), 1):
            if key is None:
                records.append({"n": name, "s": "no-match"})
                tally["no-match"] += 1
            else:
                txt, reason = pick(name, descs)
                if txt:
                    result[name] = {"title": f"gbif:{key}", "paragraphs": [txt]}
                    records.append({"n": name, "s": "filled", "t": f"gbif:{key}"})
                    tally["filled"] += 1
                else:
                    records.append({"n": name, "s": "rejected", "r": reason})
                    tally[reason] += 1
            if done % 250 == 0:
                rate = done / max(0.001, time.time() - START)
                print(f"  {done:,}/{len(todo):,} {rate:.0f}/s  {dict(tally)}", flush=True)

    for r in prior.values():
        records.append(r)
    counts = count_records(records)
    write_ledger(args.ledger, sorted(records, key=lambda r: r["n"].lower()),
                 counts, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(f"\n{dict(tally)}")
    print(f"filled {len(result):,} / {len(todo):,} = {100*len(result)/max(1,len(todo)):.1f}%")
    print(f"ledger: {len(records):,} records -> {args.ledger}")
    if args.out:
        json.dump(result, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"wrote {len(result):,} descriptions -> {args.out}")
    if not args.apply:
        print("(dry run - pass --apply)")
        return
    written, touched = apply_descriptions(result, args.root)
    print(f"applied: {written:,} species described across {touched:,} family files")


START = time.time()

if __name__ == "__main__":
    main()
