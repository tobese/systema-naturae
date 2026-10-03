#!/usr/bin/env python3
"""Fill missing species common names from iNaturalist.

1,115,259 species in the tree have no common name. The iNaturalist sweep
collected 165,679 distinct names to help with that, and measures against them as
filling about 10,205 — 0.9%.

That is a small return for 5,651 pages of fetching, and the honest framing is
that this is a gap-filler, not a source: iNaturalist names are crowdsourced, so
they are a long way behind GBIF's backbone or Wikipedia for anything either of
them covers, which is exactly why nothing existing is overwritten here.

**Licence.** iNaturalist *data* — names, ranks, conservation status — is
CC BY-NC 4.0. Images are separate and mostly CC BY / CC BY-SA / public domain,
but the names are not. This project has refused NC sources throughout, so
applying this puts NC data into a public portal. That was a deliberate decision,
not an oversight; it is recorded in docs/data-sources-attribution.md and the
manifest, and it is the one import in the repo that breaks the otherwise
consistent licensing story.

Usage:
    python3 scripts/applyInatCommonNames.py            # dry run
    python3 scripts/applyInatCommonNames.py --apply
"""
import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames  # noqa: E402

LEDGER = "portal/data/inat-common-names.jsonl"
EXCLUDED = ("portal/data", "shared/data", "node_modules", "unified-taxonomy")


def load_names():
    """name -> common name, with the ambiguous and useless cases dropped.

    iNaturalist carries one name key across taxa, so a homonym gets whichever
    common name each taxon happens to have. Three names collide that way here,
    and they are not near-misses: "Ficus variegata" is both a plant and a fig
    shell, "Laelia rosea" is an orchid and a mite. Applying either value would
    write a confidently wrong common name onto a species in the other kingdom,
    so they are skipped rather than picked between.
    """
    by_name = collections.defaultdict(set)
    for line in open(LEDGER, encoding="utf-8"):
        r = json.loads(line)
        cn = (r.get("cn") or "").strip()
        n = (r.get("n") or "").strip()
        if not cn or not n:
            continue
        # A "common name" identical to the scientific name carries no
        # information and would only make the node look filled.
        if cn.casefold() == n.casefold():
            continue
        by_name[n].add(cn)

    table, skipped = {}, []
    for n, vals in by_name.items():
        if len(vals) > 1:
            skipped.append((n, sorted(vals)))
            continue
        table[n] = next(iter(vals))
    return table, skipped


def find_cn(stored_name, index, table):
    """Common name for a stored node name, or None.

    Tries the stored name first, then its canonical form.

    The order matters and is the reverse of what the GBIF enrichers do. Those
    index GBIF canonical names and look them up with our raw stored name, so they
    try raw and fall back to canonical; canonicalNames.lookup() implements exactly
    that. Here iNaturalist keys on bare binomials while 156,392 of our names keep
    the authorship inside `name`, so the canonical form is what usually matches
    and the raw name is the fallback -- and for names the parse index has never
    seen (a bare "Anas platyrhynchos" is not a key in it), canonicalNames.lookup()
    returns None for both attempts and the species silently misses. So this does
    the two probes itself rather than reusing lookup().
    """
    if not stored_name:
        return None
    hit = table.get(stored_name)
    if hit:
        return hit
    canon = index.get(stored_name)
    if canon and canon != stored_name:
        return table.get(canon)
    return None


def family_files():
    return [f for f in glob.glob("**/src/data/*.json", recursive=True)
            if not any(e in f for e in EXCLUDED)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N families (testing)")
    args = ap.parse_args()

    if not os.path.exists(LEDGER):
        sys.exit(f"FATAL: {LEDGER} not found.\n"
                 f"       Run scripts/fetchInatCommonNames.py first; the ledger is\n"
                 f"       gitignored, so it exists only on this machine.")
    table, skipped = load_names()
    print(f"iNaturalist names usable: {len(table):,} "
          f"(skipped {len(skipped)} ambiguous)")
    for n, v in skipped:
        print(f"    ambiguous, left empty: {n} -> {v}")

    index = canonicalNames._load()
    print(f"canonical index entries:  {len(index):,}")

    files = family_files()
    print(f"family files:             {len(files):,}")

    filled = 0
    considered = 0
    files_touched = 0
    sample = []

    for path in sorted(files):
        if args.limit and files_touched >= args.limit:
            break
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR {path}: {e}")
            continue
        if data.get("rank") != "FAMILY":
            continue
        touched = False

        def walk(node):
            # nonlocal, not global: these are locals of main(), and `global`
            # would send Python looking for them in the module namespace where
            # they do not exist.
            nonlocal filled, considered, touched
            if node.get("rank") == "SPECIES":
                considered += 1
                if not (node.get("commonName") or "").strip():
                    cn = find_cn(node.get("name"), index, table)
                    if cn:
                        node["commonName"] = cn
                        node["sourcedFrom"] = "inaturalist"
                        filled += 1
                        touched = True
                        if len(sample) < 8:
                            sample.append((node["name"], cn))
            for c in node.get("children") or []:
                walk(c)
            for s in node.get("speciesList") or []:
                if s.get("rank") == "SPECIES":
                    considered += 1
                    if not (s.get("commonName") or "").strip():
                        cn = find_cn(s.get("name"), index, table)
                        if cn:
                            s["commonName"] = cn
                            s["sourcedFrom"] = "inaturalist"
                            filled += 1
                            touched = True
                            if len(sample) < 8:
                                sample.append((s["name"], cn))

        walk(data)
        if touched:
            files_touched += 1
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    pct = filled / max(considered, 1) * 100
    print(f"\nspecies considered: {considered:,}")
    print(f"common names filled: {filled:,}  ({pct:.2f}% of species)")
    print(f"family files touched: {files_touched:,}")
    for n, c in sample:
        print(f"    {n} -> {c}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
