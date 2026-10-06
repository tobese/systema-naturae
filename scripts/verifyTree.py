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
    python3 scripts/verifyTree.py --after-import          # gate a run that just applied
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import (  # noqa: E402
    KINGDOMS,
    count_species,
    iter_family_files,
    iter_family_nodes,
    kingdom_input,
    resolve_family_file,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# kingdom -> repo-relative taxonomy input path. Was hardcoded here, which meant
# a kingdom added to kingdom-config.json was silently invisible to this script.
KINGDOM_DOCS = {k: kingdom_input(k) for k in KINGDOMS}

failures = []
notes = []


def fail(check, detail):
    failures.append((check, detail))
    print(f"  FAIL  {check}: {detail}")


def ok(check, detail=""):
    print(f"  ok    {check}{': ' + detail if detail else ''}")


def doc_kingdom(path):
    """Kingdom a taxonomy document belongs to, from its filename.

    `kingdom-config.json` names plantae's input `taxonomy-plantae-snippet.json`,
    so the suffix rule has to cope with both `-fungi` and `-plantae-snippet`.
    """
    base = os.path.basename(path)
    if base == "taxonomy.json":
        return "animalia"
    k = base[len("taxonomy-"):-len(".json")]
    return k[:-len("-snippet")] if k.endswith("-snippet") else k


def family_files(kingdom):
    """Every family document in one kingdom, as a list of `tree.FamilyFile`.

    Was a `slug -> path` dict, which is lossy: slug is the basename, and
    distinct families share one. Fungi has **87** family directories called
    `incertae-sedis` (1,220 species in the largest), chromista 12, and animalia
    has two `personidae` -- a 1-species Grylloblattodea file and a 45-species
    gastropod one. Keying by slug silently dropped 86 of the 87 fungi families
    and 11 of the 12 chromista ones from every check in this script.

    It went unnoticed because the dict's winner depended on `glob` order, which
    is filesystem-dependent. Sorting made the winner deterministic and turned a
    silent skip into a visible FAIL, which is how this was found: the slug-keyed
    dict had been reporting on whichever `personidae` the filesystem listed last.
    """
    return list(iter_family_files(kingdom))


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
        by_path = {fam.path: fam for fam in files}
        tax = json.load(open(p, encoding="utf-8"))
        under = []
        resolved_paths = set()

        # Join taxonomy node -> data file by RANK PATH, not by appSlug. The slug
        # is not unique -- 87 fungi families are all called `incertae-sedis` --
        # so a slug join silently compared the wrong file, and the loser was
        # whichever one the filesystem happened to list last.
        for node, ranks in iter_family_nodes(kingdom):
            slug = node.get("appSlug") or ""
            resolved = resolve_family_file(**ranks, slug=slug)
            if resolved is None or resolved not in by_path:
                continue
            resolved_paths.add(resolved)
            held = count_species(json.load(open(resolved, encoding="utf-8")))
            have = node.get("speciesCount")
            if have is None or have < held:
                under.append((node.get("name"), have, held))

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
        orphans = set(by_path) - resolved_paths
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
        for fam in family_files(kingdom):
            f = fam.path
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
        for fam in family_files(kingdom):
            try:
                d = json.load(open(fam.path, encoding="utf-8"))
            except Exception:
                continue
            st = list(d.get("children") or [])
            while st:
                n = st.pop()
                if n.get("rank") == "SPECIES" and n.get("id"):
                    seen[n["id"]].add((kingdom, fam.path))
                st.extend(n.get("children") or [])
                for sp in n.get("speciesList") or []:
                    if sp.get("id"):
                        seen[sp["id"]].add((kingdom, fam.path))
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
    for fam in family_files(kingdom):
        try:
            d = json.load(open(fam.path, encoding="utf-8"))
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
    for fam in family_files("animalia")[:sample]:
        try:
            d = json.load(open(fam.path, encoding="utf-8"))
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


CODE_LIKE_NAME = re.compile(r"^\d+[-_]\d+|^\d+$")

# Two archaea families are named for a GBIF taxon key rather than a name. Both
# are honest placeholders for organisms that have no binomial: NCBI environmental
# sequences from candidate phyla, where the "genus" is a locus tag --
# 21-14-0-10-32-9 holds 6 species under genera SKIS01 and PWWA01, and
# 1-14-0-10-31-34 holds 3 under a genus with the same code. Renaming them to
# "Incertae sedis" would match the project's 103 existing placeholder families,
# but it moves directories, appSlugs and node ids, so it is a decision rather
# than a repair. Listed here so the gate is honest instead of permanently red.
KNOWN_CODE_LIKE_FAMILIES = {"1-14-0-10-31-34", "21-14-0-10-32-9"}
PLACEHOLDER_NAME = re.compile(
    r"^(unknown|incertae\s+sedis|unclassified|unplaced)$", re.I)


def check_authority_collisions():
    """Two of our species must not share an external authority id in one kingdom.

    This is the strongest duplicate signal available: a GBIF usageKey or an ITIS
    TSN is issued by the authority, so two records carrying the same one are the
    same taxon by definition rather than by name resemblance. Backfilling
    sourceIds surfaced 4,248 such groups worth 8,499 copies, which no amount of
    name or internal-id matching had found.

    Cross-kingdom collisions are excluded, because they are a kingdom-placement
    disagreement (67 of the original 4,522) rather than a duplicate, and the 7
    deliberately undecided placements stay put.
    """
    seen = collections.defaultdict(list)
    for kingdom in KINGDOM_DOCS:
        for fam in family_files(kingdom):
            try:
                d = json.load(open(fam.path, encoding="utf-8"))
            except Exception:
                continue
            st = list(d.get("children") or [])
            while st:
                n = st.pop()
                if n.get("rank") == "SPECIES":
                    for auth, key in (n.get("sourceIds") or {}).items():
                        if key:
                            seen[(kingdom, auth, str(key))].append(
                                f"{n.get('name')}[{fam.slug}]")
                st.extend(n.get("children") or [])
                for sp in n.get("speciesList") or []:
                    if sp.get("rank") == "SPECIES":
                        for auth, key in (sp.get("sourceIds") or {}).items():
                            if key:
                                seen[(kingdom, auth, str(key))].append(
                                    f"{sp.get('name')}[{slug}]")
    dupes = {k: v for k, v in seen.items() if len(set(v)) > 1}
    if dupes:
        ex = list(dupes)[:3]
        fail("no two species share an authority id in one kingdom",
             f"{len(dupes):,} collisions, e.g. "
             + "; ".join(f"{k[1]} {k[2]} in {k[0]}" for k in ex)
             + " -- run scripts/dedupeSpeciesAcrossFamilies.py")
    else:
        ok("no two species share an authority id in one kingdom",
           f"{len(seen):,} identifiers checked")


def check_family_names():
    """A FAMILY node's name should be a name.

    Two exceptions exist in the tree and both are junk from the GBIF backbone
    import: archaea `1-14-0-10-31-34` and `21-14-0-10-32-9`, which are GBIF
    taxon keys rather than names. Everything else that looks like a placeholder
    is reported rather than failed, because "Incertae sedis" is a deliberate
    editorial decision and 103 families carry it.
    """
    junk, placeholders = [], collections.Counter()
    for path in KINGDOM_DOCS.values():
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            continue
        kingdom = doc_kingdom(path)
        tax = json.load(open(p, encoding="utf-8"))

        def walk(n):
            if n.get("rank") == "FAMILY":
                nm = (n.get("name") or "").strip()
                if CODE_LIKE_NAME.match(nm):
                    junk.append((kingdom, nm))
                elif PLACEHOLDER_NAME.match(nm):
                    placeholders[kingdom] += 1
            for c in n.get("children") or []:
                walk(c)
        walk(tax)
    unexpected = [(k, n) for k, n in junk if n not in KNOWN_CODE_LIKE_FAMILIES]
    if unexpected:
        fail("no family node named like a taxon key",
             f"{len(unexpected)}: "
             + ", ".join(f"{k}/{n}" for k, n in unexpected[:4]))
    else:
        ok("no unexpected family node named like a taxon key",
           f"{len(junk)} documented ({', '.join(sorted(KNOWN_CODE_LIKE_FAMILIES))}"
           + (")" if junk else ")"))
    gone = KNOWN_CODE_LIKE_FAMILIES - {n for _k, n in junk}
    if gone:
        notes.append(f"documented code-like family names now resolved: "
                     f"{', '.join(sorted(gone))} -- drop them from "
                     f"KNOWN_CODE_LIKE_FAMILIES")
    if placeholders:
        notes.append("families named Unknown/Incertae sedis: "
                     + ", ".join(f"{k} {n}" for k, n in placeholders.most_common())
                     + " -- a deliberate editorial state, not a defect")


def check_missing_lineage(limit=0):
    """Every species should carry a lineage (its genus).

    2,906 animalia species did not as of 2026-10-05, which is the only
    field-presence defect the tree-wide sanity scan found that is not coverage
    work. Presence only: whether the value is *correct* is a separate and much
    larger question (1.17M plantae carry a superseded genus).
    """
    missing = collections.Counter()
    examples = []
    for kingdom in KINGDOM_DOCS:
        n = 0
        for fam in family_files(kingdom):
            try:
                d = json.load(open(fam.path, encoding="utf-8"))
            except Exception:
                continue
            st = list(d.get("children") or [])
            while st:
                x = st.pop()
                if x.get("rank") == "SPECIES" and not (x.get("lineage") or "").strip():
                    n += 1
                    if len(examples) < 4:
                        examples.append(f"{kingdom}/{os.path.basename(f)}:"
                                        f"{x.get('name')}")
                st.extend(x.get("children") or [])
        if n:
            missing[kingdom] = n
    if missing:
        fail("every species carries a lineage",
             f"{sum(missing.values()):,} without one "
             f"({', '.join(f'{k} {v:,}' for k, v in missing.most_common())})"
             + (f" e.g. {examples[0]}" if examples else ""))
    else:
        ok("every species carries a lineage")


def check_import(refusal_ceiling=0.20):
    """Gate the last applied import, from data/import-log.jsonl.

    The refusal rate is the number that matters and the one no exit code has ever
    caught: WFO Plant List refused 1,071 of 408,939 (0.26%) and ITIS 31,760 of
    582,013 (5.5%), both healthy because those sources name families we mostly
    hold. A run that refused 60% would print the same shape of output and leave
    the tree with a fifth of its potential, and there is nothing else in the
    pipeline that would object.
    """
    log = os.path.join(ROOT, "data", "import-log.jsonl")
    if not os.path.exists(log):
        notes.append("no data/import-log.jsonl yet -- nothing to gate")
        return
    rows = []
    with open(log, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if not rows:
        notes.append("data/import-log.jsonl is empty")
        return
    r = rows[-1]
    rate = r.get("refusalRate") or 0.0
    print(f"\n  last applied import: {r.get('slugHint')} "
          f"({r.get('at')})")
    print(f"    offered {r.get('offered', 0):,}  already held "
          f"{r.get('alreadyHeld', 0):,}  staged {r.get('staged', 0):,}  "
          f"refused {r.get('refused', 0):,}  added {r.get('added', 0):,}")
    if rate > refusal_ceiling:
        fail("last import's refusal rate is within tolerance",
             f"{rate:.1%} of offered species refused, ceiling is "
             f"{refusal_ceiling:.0%} -- that is the signature of a source whose "
             f"families we do not hold (cf. Wikispecies at 45%), or of a "
             f"kingdom-routing bug. Check the pending-family store before "
             f"treating the shortfall as real")
    else:
        ok("last import's refusal rate is within tolerance",
           f"{rate:.2%} (ceiling {refusal_ceiling:.0%})")
    if r.get("added") == 0 and r.get("staged", 0) > 0:
        fail("last import added something it staged",
             f"staged {r.get('staged'):,} but added 0 -- every staged species "
             f"was already present, which usually means the held-check is "
             f"wrong rather than the source being exhausted")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--after-import", action="store_true",
                    help="also gate the last applied import's refusal rate")
    ap.add_argument("--refusal-ceiling", type=float, default=0.20,
                    help="fraction of offered species an import may refuse "
                         "before this fails (default 0.20)")
    args = ap.parse_args()
    os.chdir(ROOT)
    print("verifying the tree's data invariants")
    check_species_counts()
    check_file_counts()
    check_duplicate_species()
    check_species_names()
    check_authority_collisions()
    check_family_names()
    check_missing_lineage()
    check_lineage()
    if args.after_import:
        check_import(refusal_ceiling=args.refusal_ceiling)
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
