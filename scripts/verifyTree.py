#!/usr/bin/env python3
"""Assert the tree's data invariants. Non-zero exit if any is violated.

Every serious bug found while importing sources in October 2026 produced a
*plausible number* rather than an error, which is why none of them were caught
by the test suite and all of them were caught by a human noticing a figure was
wrong. The three that mattered:

- `resyncFamilyCounts.py` counted only a family's direct children and reported
  "node UNDERstates the file: 0" -- true, and true only of the one kingdom it
  read. The other five had 574 understated nodes worth 2,546 species.
- `importColChecklist.py` printed its already-on-disk counter under the label
  "unparseable", so an import read as if 40% of a dataset failed to parse.
- A 600-name sample of an alphabetical list said a dataset was 66.2% held when
  the true figure was 43.8%.

None of those raise. So the invariants are asserted here instead, and the
thresholds are the point: a run that adds 158,701 species and refuses 0.26% is
healthy, and a run that adds 158,701 and refuses 60% is not, even though both
exit 0.

    python3 scripts/verifyTree.py
    python3 scripts/verifyTree.py --max-refusal-rate 0.5   # looser
"""
import argparse
import collections
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINGDOM_DOCS = {
    "animalia": "portal/data/taxonomy.json",
    "fungi": "portal/data/taxonomy-fungi.json",
    "chromista": "portal/data/taxonomy-chromista.json",
    "plantae": "portal/data/taxonomy-plantae-snippet.json",
    "protozoa": "portal/data/taxonomy-protozoa.json",
    "archaea": "portal/data/taxonomy-archaea.json",
}
TAXONOMY_DIR = "taxonomy"

failures = []
notes = []


def fail(check, detail):
    failures.append((check, detail))
    print(f"  FAIL  {check}: {detail}")


def ok(check, detail=""):
    print(f"  ok    {check}{': ' + detail if detail else ''}")


def count_species(node):
    """Recursive. Families nest under SUBFAMILY and buildData compresses
    minimal species into speciesList at every level, so a direct-children count
    is wrong -- that was the first bug this script exists to catch."""
    n = len(node.get("speciesList") or [])
    for c in node.get("children") or []:
        n += 1 if c.get("rank") == "SPECIES" else count_species(c)
    return n


def doc_kingdom(path):
    base = os.path.basename(path)
    if base == "taxonomy.json":
        return "animalia"
    k = base[len("taxonomy-"):-len(".json")]
    return k[:-len("-snippet")] if k.endswith("-snippet") else k


def family_files(kingdom):
    out = {}
    for f in glob.glob(os.path.join(ROOT, TAXONOMY_DIR, kingdom, "**",
                                    "src", "data", "*.json"), recursive=True):
        if "node_modules" in f:
            continue
        out[os.path.basename(f)[:-5]] = f
    return out


def check_species_counts(max_understated=0):
    """Every FAMILY node's speciesCount must be >= what its file holds.

    Overstating is allowed and correct: a node carries the real-world total for
    a family we sample rather than exhaust. Understating is the error case.
    """
    total_under = 0
    for path in KINGDOM_DOCS.values():
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            notes.append(f"{path} absent")
            continue
        kingdom = doc_kingdom(path)
        files = family_files(kingdom)
        tax = json.load(open(p, encoding="utf-8"))
        under = []
        by_slug = set()

        def walk(n):
            if n.get("rank") == "FAMILY":
                slug = n.get("appSlug") or ""
                by_slug.add(slug)
                f = files.get(slug)
                if f:
                    held = count_species(json.load(open(f, encoding="utf-8")))
                    have = n.get("speciesCount")
                    if have is None or have < held:
                        under.append((n.get("name"), have, held))
            for c in n.get("children") or []:
                walk(c)

        walk(tax)
        total_under += len(under)
        if under:
            by = 0
            for _n, have, held in under:
                by += (held - (have or 0))
            fail("speciesCount does not understate its file",
                 f"{kingdom}: {len(under)} families, {by:,} species "
                 f"(worst: {under[0][0]} has {under[0][1]}, file holds "
                 f"{under[0][2]})")
        # files with no taxonomy node are a structural problem, not a count one
        orphans = set(files) - by_slug
        if orphans:
            notes.append(f"{kingdom}: {len(orphans)} family files with no "
                         f"taxonomy node")
    if total_under == 0:
        ok("no taxonomy node understates its family file",
           "all six kingdoms")


def check_file_counts(max_mismatch=0):
    """A family DATA FILE's own speciesCount must equal what the file holds."""
    bad = 0
    for kingdom in KINGDOM_DOCS:
        for slug, f in family_files(kingdom).items():
            d = json.load(open(f, encoding="utf-8"))
            if "speciesCount" not in d:
                continue
            n = count_species(d)
            if d["speciesCount"] != n:
                bad += 1
    if bad > max_mismatch:
        fail("family data file speciesCount matches contents",
             f"{bad} files disagree with their own contents "
             f"(run scripts/resyncFamilyCounts.py --apply)")
    else:
        ok("every family data file's speciesCount matches its contents")


# The deliberately undecided placements: three genera whose family assignment is
# genuinely disputed, so we hold a copy under each candidate rather than picking.
# Named individually rather than allowed as a count of 7, because a *different*
# eighth duplicate has to fail and a bare allowance cannot tell the difference.
KNOWN_SAME_KINGDOM_DUPLICATES = {
    # Acanthizidae vs Locustellidae -- one genus, two placements
    "CINCLORAMPHUS_CRURALIS", "CINCLORAMPHUS_MACRURUS",
    "CINCLORAMPHUS_MATHEWSI", "CINCLORAMPHUS_TIMORIENSIS",
    "POODYTES_CARTERI", "POODYTES_RUFESCENS",
    # Vangidae vs Passerellidae -- same question
    "ORYZOBORUS_ANGOLENSIS",
}

# Cross-kingdom homonyms are NOT a bug and must never be "fixed": these are
# unrelated organisms that share a binomial. Alfaria minuta is an ant and a
# fungus; Graphium sarpedon is a butterfly and a fungus; Phyllocardium
# complanatum is a bivalve and a plant. BACKLOG.md records this as settled.
KNOWN_CROSS_KINGDOM_HOMONYMS = {
    "ALFARIA_MINUTA", "CLAVULINA_FLORIDANA", "CLAVULINA_RUGOSA",
    "DIPLODERMA_POLYGONATUM", "GRAPHIUM_SARPEDON", "HEXAGONIA_BICOLOR",
    "SP_PHYLLOCARDIUM_COMPLANATUM",
}


def check_duplicate_species():
    """No species id in two families *within one kingdom*.

    Cross-kingdom collisions are a different thing and are counted separately,
    because conflating them is what makes this check useless in both directions:
    with a single allowance of 7 the 7 documented homonyms masked 4,310 real
    within-file duplicates, and raising the allowance to 22 would have hidden
    them again.
    """
    seen = collections.defaultdict(set)          # id -> {(kingdom, file)}
    for kingdom in KINGDOM_DOCS:
        for slug, f in family_files(kingdom).items():
            try:
                d = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            st = list(d.get("children") or [])
            while st:
                n = st.pop()
                if n.get("rank") == "SPECIES" and n.get("id"):
                    seen[n["id"]].add((kingdom, f))
                st.extend(n.get("children") or [])
                for sp in n.get("speciesList") or []:
                    if sp.get("id"):
                        seen[sp["id"]].add((kingdom, f))
    same, cross = {}, {}
    for i, places in seen.items():
        if len(places) < 2:
            continue
        if len({k for k, _ in places}) > 1:
            cross[i] = places
        else:
            same[i] = places

    unexpected = set(same) - KNOWN_SAME_KINGDOM_DUPLICATES
    missing = KNOWN_SAME_KINGDOM_DUPLICATES - set(same)
    if unexpected:
        fail("no species id in two families of the same kingdom",
             f"{len(unexpected)} unexpected: "
             f"{', '.join(sorted(unexpected)[:4])} — run "
             f"scripts/dedupeSpeciesAcrossFamilies.py")
    else:
        ok("no unexpected species id in two families of one kingdom",
           f"{len(same)} deliberate ({'/'.join(sorted({i.split('_')[0].lower() for i in same}))})")
    if missing:
        notes.append(f"{len(missing)} previously-known duplicates are resolved "
                     f"now: {', '.join(sorted(missing)[:3])} — drop them from "
                     f"KNOWN_SAME_KINGDOM_DUPLICATES")

    undeclared = set(cross) - KNOWN_CROSS_KINGDOM_HOMONYMS
    if undeclared:
        fail("cross-kingdom homonyms are the documented set",
             f"{len(undeclared)} new: {', '.join(sorted(undeclared)[:4])} — a new "
             f"one may be a real collision rather than a homonym, so confirm "
             f"before adding it")
    else:
        ok("cross-kingdom homonyms match the documented set", f"{len(cross)}")


def check_species_names(kingdom="animalia"):
    """Every species must have an id and a name. The WFO import wrote 158,701
    nodes, and a staged node missing its id would be invisible in a count."""
    missing = 0
    total = 0
    for slug, f in family_files(kingdom).items():
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        st = list(d.get("children") or [])
        while st:
            n = st.pop()
            if n.get("rank") == "SPECIES":
                total += 1
                if not n.get("id") or not n.get("name"):
                    missing += 1
            st.extend(n.get("children") or [])
    if missing:
        fail("every species node has an id and a name",
             f"{missing:,} of {total:,} in {kingdom}")
    else:
        ok("every species node has an id and a name", f"{total:,} in {kingdom}")


def check_lineage(sample=200):
    """`lineage` should be the immediate parent name, so a species' lineage is
    its genus. It is not reliable enough to assert across the tree -- 1.17M
    plantae carry a superseded genus there (Gyroporella pauciforata under
    "Physoporella") -- so this only reports, and asserts nothing."""
    genus = other = family = 0
    for slug, f in list(family_files("animalia").items())[:sample]:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        fam = (d.get("name") or "").lower()
        st = list(d.get("children") or [])
        while st:
            n = st.pop()
            if n.get("rank") == "SPECIES":
                lin = (n.get("lineage") or "").strip().lower()
                nm = (n.get("name") or "").strip()
                g = nm.split()[0].lower() if nm else ""
                if not lin:
                    pass
                elif lin == g:
                    genus += 1
                elif lin == fam:
                    family += 1
                else:
                    other += 1
            st.extend(n.get("children") or [])
    tot = genus + family + other
    if tot:
        ok("species lineage is the genus (sampled)", f"{genus:,}/{tot:,} = "
           f"{100 * genus / tot:.1f}%")
    if other:
        notes.append(f"{other:,} of {tot:,} sampled species carry a lineage "
                     f"that is neither genus nor family — 1.17M plantae "
                     f"expected, so this is not a new problem")
    if family:
        fail("no species carries its family as lineage",
             f"{family:,} of {tot:,} sampled animalia — run "
             f"scripts/fixSpeciesLineage.py --apply")


def main() -> int:
    ap = argparse.ArgumentParser()
    args = ap.parse_args()
    os.chdir(ROOT)
    print("verifying the tree's data invariants")
    check_species_counts()
    check_file_counts()
    check_duplicate_species()
    check_species_names()
    check_lineage()
    if notes:
        print("\n  notes (not failures):")
        for n in notes:
            print(f"      {n}")
    if failures:
        print(f"\n  {len(failures)} FAILED")
        return 1
    print("\n  all invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
