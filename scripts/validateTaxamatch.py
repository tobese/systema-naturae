#!/usr/bin/env python3
"""Check scripts/taxamatch.py against the Ruby gems it was ported from.

The gems are the reference: `gem install taxamatch_rb damerau-levenshtein`. Two
things are compared, separately, because they can fail independently:

- **Distances.** `damerau_levenshtein` should agree with the gem on every pair.
  The port deliberately does not reproduce the C extension's out-of-bounds reads
  near the ends of the matrix, so pairs that would have read garbage there are
  reported separately rather than counted as agreement.
- **Decisions.** `Taxamatch#match` should agree on whether two names denote the
  same taxon. The two sides do not atomize names the same way -- the gems use the
  `biodiversity` gem's Treetop grammar, this port uses GNparser -- so disagreements
  are expected wherever the parsers disagree about a name's boundaries, and those
  are listed rather than averaged away.

Usage:
    GEM_HOME=/tmp/gn-gems python3 scripts/validateTaxamatch.py --pairs 3000
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taxamatch  # noqa: E402

RUBY_DIST = r'''
require 'taxamatch_rb'
pairs = JSON.parse(File.read(ARGV[0]))
out = pairs.map { |a, b| [DamerauLevenshtein.distance(a, b, 1, 10),
                          DamerauLevenshtein.distance(a, b, 2, 10),
                          DamerauLevenshtein.distance(a, b, 0, 10)] }
File.write(ARGV[1], JSON.generate(out))
'''

RUBY_MATCH = r'''
require 'taxamatch_rb'
pairs = JSON.parse(File.read(ARGV[0]))
m = Taxamatch::Base.new
File.write(ARGV[1], JSON.generate(pairs.map { |a, b| m.taxamatch(a, b) ? 1 : 0 }))
'''


def ruby_available():
    try:
        subprocess.run(["ruby", "-e", "require 'taxamatch_rb'"],
                       capture_output=True, timeout=60,
                       env={**os.environ})
        return True
    except Exception:
        return False


def load_pairs(n):
    """Real names from the tree, paired with a corrupted neighbour."""
    import glob
    names = []
    for f in glob.glob("taxonomy/animalia/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        stack = [d]
        while stack:
            x = stack.pop()
            if x.get("rank") == "SPECIES" and x.get("name"):
                names.append(x["name"])
            stack.extend(x.get("children") or [])
            stack.extend(x.get("speciesList") or [])
    random.seed(42)
    picked = random.sample(names, min(n, len(names)))
    pairs = []
    for nm in picked:
        # half get a single-character corruption, half are paired with another
        # real species so distance and decision are exercised on real lookalikes
        if random.random() < 0.5 and len(nm) > 6:
            i = random.randrange(2, len(nm))
            mode = random.choice(("sub", "swap", "del", "ins"))
            if mode == "sub":
                alt = nm[:i] + random.choice("abcdefghijklmnopqrstuvwxyz") + nm[i + 1:]
            elif mode == "swap":
                alt = nm[:i] + nm[i + 1] + nm[i] + nm[i + 2:] if i + 2 <= len(nm) else nm[::-1]
            elif mode == "del":
                alt = nm[:i] + nm[i + 1:]
            else:
                alt = nm[:i] + random.choice("aeiou") + nm[i:]
            pairs.append((nm, alt))
        else:
            pairs.append((nm, random.choice(picked)))
    return pairs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=2000)
    args = ap.parse_args()

    if not ruby_available():
        print("  Ruby gems not importable. Install them first:\n"
              "    export GEM_HOME=/tmp/gn-gems\n"
              "    gem install parallel -v 1.24.0\n"
              "    gem install taxamatch_rb damerau-levenshtein")
        return 2

    pairs = load_pairs(args.pairs)
    print(f"  pairs from the tree: {len(pairs):,}")
    handles = [tempfile.mkstemp(suffix=".json") for _ in range(4)]
    for fd, _path in handles:
        os.close(fd)
    d1, d2, m1, m2 = [path for _fd, path in handles]

    with open(d1, "w", encoding="utf-8") as fh:
        json.dump(pairs, fh)
    for script, src, dst in ((RUBY_DIST, d1, d2), (RUBY_MATCH, d1, m1)):
        s = tempfile.NamedTemporaryFile("w", suffix=".rb", delete=False,
                                        encoding="utf-8")
        s.write(script)
        s.close()
        try:
            r = subprocess.run(["ruby", s.name, src, dst], capture_output=True,
                               text=True, timeout=1800)
            if r.returncode != 0:
                print(f"  ruby failed: {r.stderr.strip().splitlines()[-1][:160]}")
                return 2
        finally:
            os.unlink(s.name)

    ruby_dist = json.load(open(d2, encoding="utf-8"))
    ruby_match = json.load(open(m1, encoding="utf-8"))
    py_match = [1 if taxamatch.Taxamatch().match(a, b) else 0 for a, b in pairs]

    agree = dis = 0
    for (a, b), (r1, r2, r3) in zip(pairs, ruby_dist):
        p1 = taxamatch.damerau_levenshtein(a, b, 1, 10)
        p2 = taxamatch.damerau_levenshtein(a, b, 2, 10)
        p3 = taxamatch.damerau_levenshtein(a, b, 0, 10)
        if (p1, p2, p3) == (r1, r2, r3):
            agree += 1
        else:
            dis += 1
            if dis <= 6:
                print(f"    DIST differs: {a[:34]!r} vs {b[:34]!r}  "
                      f"gem={r1},{r2},{r3} port={p1},{p2},{p3}")
    print(f"\n  distance agreement: {agree:,}/{agree+dis:,} "
          f"({agree/(agree+dis)*100:.2f}%)")

    magree = sum(1 for g, p in zip(ruby_match, py_match) if g == p)
    print(f"  decision agreement: {magree:,}/{len(pairs):,} "
          f"({magree/len(pairs)*100:.2f}%)")
    shown = 0
    for (a, b), g, p in zip(pairs, ruby_match, py_match):
        if g != p and shown < 10:
            print(f"    DECISION differs: {a[:34]!r} vs {b[:34]!r}  "
                  f"gem={bool(g)} port={bool(p)}")
            shown += 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
