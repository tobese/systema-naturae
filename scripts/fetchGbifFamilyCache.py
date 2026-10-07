#!/usr/bin/env python3
"""Record, for every GBIF usageKey held twice in one kingdom, the family GBIF says.

`dedupeSpeciesAcrossFamilies.py` collapses a species that two family files both
hold, and it has to pick a survivor. It was picking on richness -- the copy with
a description, a common name, continents -- which has nothing to do with which
family is right. So it kept the misfiled copy and discarded the correctly-placed
one in 1,242 cases: `anobiidae` lost 159 species to `ptinidae`, `lobariaceae`
lost 128 to `peltigeraceae`, across 159 distinct family-pair patterns.

GBIF already holds the answer. For a usageKey it issued, `/v1/species/{key}`
returns the family that key belongs to, which is a statement about the taxon
rather than a guess about our node. This script collects those, and the dedupe
reads them back with `--authority-family`.

Only the keys that are actually in duplicate are fetched. That is ~4,500
requests for the current tree rather than the 2.7 million the tree holds, and it
is the only set the dedupe can act on. Re-run after an import adds duplicates;
the cost is proportional to what was added, not to the tree.

    python3 scripts/fetchGbifFamilyCache.py            # dry run, prints the plan
    python3 scripts/fetchGbifFamilyCache.py --apply

Writes `portal/data/gbif-family-cache.json`. Committed rather than gitignored:
the dedupe's choice of survivor is a judgement, and a judgement you cannot
reproduce is one you have to take on trust.
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import KINGDOMS, iter_family_files, iter_species_with_parent  # noqa: E402

OUT = "portal/data/gbif-family-cache.json"
UA = ("systema-naturae/1.0 (https://github.com/tobese/systema-naturae; "
      "taxonomy tree maintenance)")

# GBIF is a courtesy API and this walks it politely: one request at a time with
# a pause, retried on 429/5xx. 4,500 sequential requests is minutes, not hours,
# and the alternative -- no User-Agent, or a burst -- gets rate-limited or
# blocked, which costs more time than the pause does.
PAUSE = 0.12
RETRIES = 4


def duplicate_keys(kingdoms, ref=None):
    """Every gbif usageKey held by more than one species inside one kingdom.

    `ref` reads the tree out of a git snapshot instead of the working tree. That
    is the normal way to run this: once the dedupe has collapsed every group
    there are no duplicates left to look up, so the cache has to be built from
    the state *before* it -- which after the fact is a commit, not the checkout.
    """
    if ref:
        return _duplicate_keys_from_ref(kingdoms, ref)

    where = collections.defaultdict(list)
    for k in kingdoms:
        for fam in iter_family_files(k):
            try:
                d = fam.load()
            except Exception:
                continue
            for _parent, s in iter_species_with_parent(d):
                key = (s.get("sourceIds") or {}).get("gbif")
                if key:
                    where[(k, str(key))].append(s)
    return {key for key, v in where.items() if len(v) > 1}


def _duplicate_keys_from_ref(kingdoms, ref):
    """Same question, answered from `git ls-tree` + one batched `git cat-file`.

    One `git show` per file is 14,000 subprocesses and takes long enough to look
    like a hang; a single batched cat-file reads the same blobs in seconds.
    """
    paths = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "--",
                            "taxonomy"], capture_output=True, text=True,
                           check=True).stdout.split()
    files = [p for p in paths
             if p.endswith(".json") and "/src/data/" in p
             and p.split("/")[1] in kingdoms]

    proc = subprocess.Popen(["git", "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    where = collections.defaultdict(list)
    try:
        for path in files:
            proc.stdin.write(f"{ref}:{path}\n".encode())
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) < 3:
                continue                      # absent from this ref
            size = int(header[2])
            body = proc.stdout.read(size)
            proc.stdout.read(1)                # trailing newline
            try:
                d = json.loads(body)
            except ValueError:
                continue
            kingdom = path.split("/")[1]
            for _parent, s in iter_species_with_parent(d):
                key = (s.get("sourceIds") or {}).get("gbif")
                if key:
                    where[(kingdom, str(key))].append(s)
    finally:
        proc.stdin.close()
        proc.wait()
    return {key for key, v in where.items() if len(v) > 1}


def fetch(key):
    """GBIF's family and canonical name for a usageKey.

    The name matters as much as the family. A usageKey is not always one taxon:
    subspecies and hybrids are filed under their parent's key, so key 4553865 is
    `Buthus occitanus` and our `Buthus occitanus israelis` carries the same
    number. Two records sharing a key are therefore only duplicates if they
    also share a name, and the dedupe needs the authority's own name to tell
    that apart.
    """
    url = f"https://api.gbif.org/v1/species/{key}"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            return d.get("family"), d.get("species") or d.get("scientificName")
        except urllib.error.HTTPError as e:
            # 404 is a real answer: the key is gone from GBIF. Anything else is
            # transient and worth retrying.
            if e.code == 404:
                return None, None
            if attempt == RETRIES - 1:
                return None, None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == RETRIES - 1:
                return None, None
            time.sleep(1.5 * (attempt + 1))
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", default="",
                    help="default: every kingdom, matching the dedupe's default")
    ap.add_argument("--from-ref", default="",
                    help="read the tree from this git ref instead of the "
                         "working tree -- e.g. --from-ref HEAD to rebuild the "
                         "cache for duplicates a dedupe has since collapsed")
    args = ap.parse_args()

    kingdoms = [args.kingdom] if args.kingdom else KINGDOMS
    keys = sorted(duplicate_keys(kingdoms, ref=args.from_ref or None))
    print(f"  {len(kingdoms)} kingdom(s): {len(keys):,} gbif usageKeys held in "
          f"more than one species of one kingdom")

    previous = {}
    previous_names = {}
    if os.path.exists(OUT):
        doc = json.load(open(OUT, encoding="utf-8"))
        previous = doc.get("families") or {}
        previous_names = doc.get("names") or {}
        # A key cached before `names` existed has to be refetched, or the dedupe
        # cannot tell a subspecies from a duplicate and will delete it again.
        todo = [k for _kd, k in keys
                if k not in previous or k not in previous_names]
        print(f"  {len(previous):,} already cached, {len(todo):,} to fetch")
    else:
        todo = [k for _kd, k in keys]

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    families = dict(previous)
    names = dict(previous_names)
    got = miss = 0
    for i, key in enumerate(todo, 1):
        fam, name = fetch(key)
        if fam:
            families[key] = fam
            if name:
                names[key] = name
            got += 1
        else:
            miss += 1
        if i % 250 == 0:
            print(f"    {i}/{len(todo)}  fetched {got:,}  no family {miss:,}",
                  flush=True)
            _write(families, names, len(keys))
        time.sleep(PAUSE)

    _write(families, names, len(keys))
    print(f"\n  wrote {OUT}: {len(families):,} keys, {got:,} fetched this run, "
          f"{miss:,} with no family from GBIF")
    return 0


def _write(families, names, total):
    doc = {
        "source": "GBIF species API, GET /v1/species/{usageKey}"
                  " -> .family and .species",
        "note": "keyed by GBIF usageKey; only keys held twice in one kingdom. "
                "`species` is GBIF's canonical name for the key, which is how a "
                "subspecies filed under its parent's key is told apart from a "
                "true duplicate.",
        "duplicateKeysAtLastRun": total,
        "families": dict(sorted(families.items())),
        "names": dict(sorted(names.items())),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
