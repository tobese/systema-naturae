#!/usr/bin/env python3
"""Move an inline authorship out of `name` into the `authorship` field.

314,539 species carry their authority twice -- `name` is
"Smilax zeylanica L." and `authorship` is "L." -- because POWO, the Wikipedia
enricher and `websearch` write the authority inline while COL, WFO, ITIS and
GBIF write it separately.

That is not cosmetic. `nodename()` and `split_authorship()` exist in
importSpeciesFile.py specifically to enforce the bare-binomial convention, so
the codebase's own rule is one convention and three enrichment paths break it.
The cost showed up as a bug rather than a style question: two sources spelling
one species differently produce the same id, `drop_redundant_species` then picks
a survivor by richness alone, and 4,310 bare binomials were discarded in
fabaceae alone in favour of the inline spelling. `merge_family` now prefers the
conforming name and recovers the bare one; this cleans up the damage already
written.

Ids are unaffected. node_id(prefix, name, authority) builds
PREFIX_NAME_AUTHORITY from the two fields separately, so `Smilax zeylanica` with
authorship `L.` yields SP_SMILAX_ZEYLANICA_L_ exactly as the inline spelling did.

Only unambiguous cases are touched: `name` must end with the node's own
`authorship`, and what remains after stripping it must still be a binomial.
Anything else is left alone, including a hybrid marker, and including the ~7,900
names where stripping would leave something that is not a binomial.

    python3 scripts/normaliseSpeciesNames.py
    python3 scripts/normaliseSpeciesNames.py --apply
"""
import argparse
import collections
import glob
import json
import re
import sys

# A bare binomial, optionally with a hybrid marker. Deliberately strict: if the
# remainder is not this shape, the name is left alone rather than guessed at.
BINOMIAL = re.compile(r"^[A-Z][a-z]+(\s+\u00d7)?\s+[a-z][a-z-]+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed = 0
    per_kingdom = collections.Counter()
    per_source = collections.Counter()
    skipped = collections.Counter()
    examples = []
    touched = 0

    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        kingdom = f.split("taxonomy/")[1].split("/")[0]
        n_file = 0
        stack = list(d.get("children") or [])
        while stack:
            node = stack.pop()
            if node.get("rank") == "SPECIES":
                nm = (node.get("name") or "").strip()
                au = (node.get("authorship") or "").strip()
                if au and len(nm) > len(au) + 2 and nm.endswith(au):
                    bare = nm[: -len(au)].strip()
                    if BINOMIAL.match(bare):
                        if args.apply:
                            node["name"] = bare
                        n_file += 1
                        per_source[node.get("sourcedFrom") or "none"] += 1
                        if len(examples) < 6:
                            examples.append((kingdom, nm, au, bare))
                    else:
                        skipped[("remainder is not a binomial",)] += 1
            stack.extend(node.get("children") or [])
        if n_file:
            changed += n_file
            per_kingdom[kingdom] += n_file
            touched += 1
            if args.apply:
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"  names normalised: {changed:,}  across {touched:,} family files")
    print(f"  by kingdom: {dict(per_kingdom.most_common())}")
    print(f"  by source:  {dict(per_source.most_common(8))}")
    for kingdom, nm, au, bare in examples:
        print(f"    [{kingdom}] {nm!r} + {au!r} -> {bare!r}")
    if skipped:
        print(f"  left alone: {sum(skipped.values()):,} "
              f"(stripping would not leave a binomial)")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
