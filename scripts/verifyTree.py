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
# The one definition of "these two names are not the same taxon", shared with
# the dedupe so the gate and the script that satisfies it cannot disagree.
from dedupeSpeciesAcrossFamilies import _same_taxon  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# kingdom -> repo-relative taxonomy input path. Was hardcoded here, which meant
# a kingdom added to kingdom-config.json was silently invisible to this script.
KINGDOM_DOCS = {k: kingdom_input(k) for k in KINGDOMS}

failures = []
passes = []
notes = []


def fail(check, detail):
    failures.append((check, detail))
    print(f"  FAIL  {check}: {detail}")


def ok(check, detail=""):
    passes.append((check, detail))
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


# Per-family species-count cache keyed by (path, mtime_ns, size). verifyTree
# re-parses every family document on each run (~0.97 GB of JSON across 14,085
# files) just to count species; that made check 2 hang on the current tree.
# The cache survives across runs and is invalidated per-file by mtime+size, so
# the first run pays the parse cost once and subsequent runs are stat-only.
COUNT_CACHE_PATH = os.path.join(ROOT, "portal", "data", "species-count-cache.json")
PARQUET_PATH = os.path.join(ROOT, "portal", "data", "species.parquet")


def _load_count_cache():
    try:
        with open(COUNT_CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_count_cache(cache):
    os.makedirs(os.path.dirname(COUNT_CACHE_PATH), exist_ok=True)
    tmp = COUNT_CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)
    os.replace(tmp, COUNT_CACHE_PATH)


def species_count_cached(fam, cache, doc=None):
    """Species count for one family file, served from cache when unchanged.

    Cache entry: `[mtime_ns, size, count, speciesCount]` — the last element is
    the file's own declared `speciesCount`, so a warm cache avoids reading the
    file at all. Old 3-element entries are upgraded on first re-read.
    """
    st = os.stat(fam.path)
    entry = cache.get(fam.path)
    if entry and len(entry) >= 4 and entry[0] == st.st_mtime_ns and entry[1] == st.st_size:
        return entry[2], entry[3]
    if doc is None:
        doc = json.load(open(fam.path, encoding="utf-8"))
    count = count_species(doc)
    declared = doc.get("speciesCount")
    cache[fam.path] = [st.st_mtime_ns, st.st_size, count, declared]
    return count, declared


_NEWEST = None


def _newest_family_file():
    """`(mtime_ns, path)` of the most recently written family data file.

    Memoised: five checks walk the same ~19,000 paths and a stat() each time is
    not worth repeating.
    """
    global _NEWEST
    if _NEWEST is None:
        newest, where = 0, None
        for kingdom in KINGDOM_DOCS:
            for fam in family_files(kingdom):
                try:
                    m = os.stat(fam.path).st_mtime_ns
                except OSError:
                    continue
                if m > newest:
                    newest, where = m, fam.path
        _NEWEST = (newest, where)
    return _NEWEST


def _age(seconds):
    """A duration short enough to read in a failure line."""
    m = round(seconds / 60)
    if m < 60:
        return f"{m} min"
    h = round(m / 60)
    return f"{h} h" if h < 48 else f"{round(h / 24)} d"


def _parquet_unusable():
    """Why `species.parquet` must not be read, or None when it may be.

    The parquet replaced ~14,000 recursive tree walks with one columnar load,
    which is only a faithful stand-in while it still describes the tree. It is a
    snapshot, so a family file written after it was built is simply not in it,
    and nothing downstream can tell the difference.
    """
    if not os.path.exists(PARQUET_PATH):
        return "portal/data/species.parquet is missing"
    newest, where = _newest_family_file()
    pq = os.stat(PARQUET_PATH).st_mtime_ns
    if newest > pq:
        rel = os.path.relpath(where, ROOT)
        return (f"portal/data/species.parquet predates {rel} by "
                f"{_age((newest - pq) / 1e9)}")
    return None


def check_parquet_freshness():
    """Fail when the parquet no longer describes the tree.

    This is not a formality. `check_file_counts` counts a *changed* family's
    species out of the parquet rather than by walking the file, then pins that
    count to the file's new mtime in the warm cache -- so a parquet older than
    an edit makes the tree compare its declared `speciesCount` against a count
    taken before the edit, and then remember that answer until the next edit. A
    gate that certifies numbers it never read is worse than the hang the parquet
    was added to fix.

    The checks below fall back to reading the files, so they stay correct while
    this one fails: the report is "your derived file is out of date", not a set
    of invented failures.
    """
    why = _parquet_unusable()
    if why:
        fail("species.parquet still describes the tree",
             f"{why} -- run: make species-parquet")
        return
    pq = os.stat(PARQUET_PATH).st_mtime_ns
    newest, where = _newest_family_file()
    ok("species.parquet still describes the tree",
       f"built {_age((pq - newest) / 1e9)} after the newest family file, "
       f"{os.path.relpath(where, ROOT)}")


def _parquet_species_counts() -> dict:
    """Count SPECIES rows per (kingdom, phylum, cls, ord, family) from parquet.

    One columnar load replaces ~14,000 recursive tree walks. Falls back to an
    empty dict if duckdb or the parquet is unavailable or out of date, in which
    case the count cache takes over. Staleness matters more than availability:
    an absent parquet costs time, a stale one costs correctness.
    """
    if _parquet_unusable():
        return {}
    try:
        import duckdb
    except ImportError:
        return {}
    try:
        con = duckdb.connect()
        rows = con.execute("""
            SELECT kingdom, phylum, cls, ord, family, count(*) AS n
            FROM read_parquet(?)
            WHERE rank = 'SPECIES'
            GROUP BY 1, 2, 3, 4, 5
        """, [PARQUET_PATH]).fetchall()
        con.close()
        return {(k, p, c, o, f): n for k, p, c, o, f, n in rows}
    except Exception:
        return {}


def _family_ranks_by_path() -> dict:
    """Map family file path -> its rank components, from taxonomy documents.

    Uses `iter_family_nodes` + `resolve_family_file`, the same verified
    bijection `buildSpeciesParquet` uses. Falls back to empty dict on error.
    """
    out = {}
    try:
        for kingdom in KINGDOMS:
            for node, ranks in iter_family_nodes(kingdom):
                slug = node.get("appSlug")
                if not slug:
                    continue
                resolved = resolve_family_file(**ranks, slug=slug)
                if resolved:
                    out[resolved] = {
                        "kingdom": ranks["kingdom"],
                        "phylum": ranks.get("phylum") or "",
                        "cls": ranks.get("cls") or "",
                        "ord": ranks.get("ord") or "",
                        "family": slug,
                    }
    except Exception:
        pass
    return out


def check_species_counts(max_understated=0):
    """Every FAMILY node's speciesCount must be >= what its file holds.

    Overstating is allowed and correct: a node carries the real-world total for
    a family we sample rather than exhaust. Understating is the error case.
    """
    total_under = 0
    cache = _load_count_cache()
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
            held = species_count_cached(by_path[resolved], cache)[0]
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
    _save_count_cache(cache)
    if total_under == 0:
        ok("no taxonomy node understates its family file",
           "all six kingdoms")


def check_file_counts(max_mismatch=0):
    """A family DATA FILE's own speciesCount must equal what the file holds.

    Warm cache entries carry both the counted species and the file's declared
    `speciesCount`, so unchanged files cost a stat() rather than a JSON parse.
    Stale files are read once, counted from parquet (one columnar load shared
    across all stale files), and the cache is updated. Falls back to the count
    cache's recursive walk if duckdb or the parquet is unavailable.
    """
    bad = 0
    parquet_counts = _parquet_species_counts()
    ranks_by_path = _family_ranks_by_path() if parquet_counts else {}
    cache = _load_count_cache()
    for kingdom in KINGDOM_DOCS:
        for fam in family_files(kingdom):
            f = fam.path
            st = os.stat(f)
            entry = cache.get(f)
            if entry and len(entry) >= 4 and entry[0] == st.st_mtime_ns and entry[1] == st.st_size:
                # Warm cache: no file read needed.
                count, declared = entry[2], entry[3]
            else:
                # Stale or missing: read the file, count from parquet.
                d = json.load(open(f, encoding="utf-8"))
                declared = d.get("speciesCount")
                if declared is None:
                    continue
                n = None
                ranks = ranks_by_path.get(f)
                if ranks:
                    key = (ranks["kingdom"], ranks["phylum"], ranks["cls"],
                           ranks["ord"], ranks["family"])
                    n = parquet_counts.get(key)
                if n is None:
                    count, _ = species_count_cached(fam, cache)
                else:
                    count = n
                    cache[f] = [st.st_mtime_ns, st.st_size, count, declared]
                if d.get("speciesCount") != count:
                    bad += 1
                continue
            if declared is not None and declared != count:
                bad += 1
    _save_count_cache(cache)
    if bad > max_mismatch:
        # Not resyncFamilyCounts.py, which is what this used to say. That script
        # maintains the *taxonomy input*'s speciesCount -- the real-world total
        # the Coverage modal divides by -- while this check compares the family
        # *file's* declared count against what the file holds. Two different
        # numbers written by different code, so following the advice cannot
        # clear this failure; it reports "would update 0 nodes" and leaves the
        # gate red. Whoever changed a family file's species set owns updating
        # that file's declared count.
        fail("family data file speciesCount matches contents",
             f"{bad} files' declared speciesCount disagrees with their own "
             f"contents -- the script that changed those files' species must "
             f"update their declared count (resyncFamilyCounts.py maintains a "
             f"different number: the taxonomy input's real-world total)")
    else:
        ok("every family data file's speciesCount matches its contents")


# The deliberately undecided placements used to live here: three genera whose
# family assignment is genuinely disputed, so we held a copy under each
# candidate rather than picking -- Cincloramphus and Poodytes under both
# Locustellidae and Acanthizidae, Oryzoborus under both Vangidae and
# Passerellidae.
#
# They are all resolved now, and not by a taxonomic argument: the dedupe
# collapsed each pair on its own rules -- one by authority id, and
# Oryzoborus by "both from imports, the larger family keeps it". All three
# landed on the second-named family. So the placement question these were
# holding open has been answered by a data signal (family size) rather than by
# anyone looking at the birds, and that is worth knowing if it is ever
# re-opened: the choice is recorded in the tree, not justified by it.
#
# Both allowlists below are data, not code -- moved out of this file
# (2026-10-22) into data/known-same-kingdom-duplicates.json and
# data/known-cross-kingdom-homonyms.json, each a flat {id: reason} map, so
# a script (this one, or a future dedupeSpeciesAcrossFamilies.py pass that
# wants to register its own "left alone (cross-kingdom homonym)" verdicts)
# can read or write the record without touching this file's source. Load
# failure is fatal rather than silently treated as empty: an allowlist that
# can't be read is not the same thing as an allowlist with nothing in it,
# and the latter is what every "unexpected" collision below would then be
# compared against.
#
# KNOWN_SAME_KINGDOM_DUPLICATES: the check asserts that whatever is listed
# is still duplicated -- so a placement that comes back fails loudly
# instead of passing on a stale allowance. (The three genera whose family
# assignment was once genuinely disputed -- Cincloramphus and Poodytes
# under both Locustellidae and Acanthizidae, Oryzoborus under both
# Vangidae and Passerellidae -- are resolved now, not by a taxonomic
# argument: the dedupe collapsed each pair on its own rules, one by
# authority id and Oryzoborus by "both from imports, the larger family
# keeps it". All three landed on the second-named family -- the placement
# question was answered by a data signal, not by anyone looking at the
# birds, which is worth knowing if it is ever re-opened.)
#
# KNOWN_CROSS_KINGDOM_HOMONYMS: these are NOT a bug and must never be
# "fixed" -- unrelated organisms that share a binomial. Alfaria minuta is
# an ant and a fungus; Graphium sarpedon is a butterfly and a fungus;
# Phyllocardium complanatum is a bivalve and a plant. BACKLOG.md records
# this as settled.
def _load_allowlist(name: str) -> set[str]:
    path = os.path.join(ROOT, "data", name)
    with open(path, encoding="utf-8") as fh:
        return set(json.load(fh).keys())


KNOWN_SAME_KINGDOM_DUPLICATES: set[str] = _load_allowlist(
    "known-same-kingdom-duplicates.json")
KNOWN_CROSS_KINGDOM_HOMONYMS: set[str] = _load_allowlist(
    "known-cross-kingdom-homonyms.json")

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

# Moved to data/known-code-like-families.json (2026-10-22), same reasoning
# as KNOWN_SAME_KINGDOM_DUPLICATES / KNOWN_CROSS_KINGDOM_HOMONYMS above:
# archaea families GTDB names by genome placeholder code rather than a
# Latin name, real designations rather than importer bugs.
KNOWN_CODE_LIKE_FAMILIES: set[str] = _load_allowlist("known-code-like-families.json")
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

    A collision is also excluded when the two records are not the same taxon,
    which an authority id alone does not guarantee. GBIF files a subspecies, a
    variety and a hybrid under its parent's usageKey -- key 4553865 is `Buthus
    occitanus` and our `Buthus occitanus israelis` carries the same number -- so
    "same usageKey" is "same taxon" only when the names agree too. Checking the
    key alone reported 24 collisions that are 24 correctly-kept subspecies, and
    pointing at the dedupe, which is careful enough not to touch them.
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
                                (n.get("name"), fam.slug))
                st.extend(n.get("children") or [])
                for sp in n.get("speciesList") or []:
                    if sp.get("rank") == "SPECIES":
                        for auth, key in (sp.get("sourceIds") or {}).items():
                            if key:
                                seen[(kingdom, auth, str(key))].append(
                                    (sp.get("name"), fam.slug))
    dupes = {}
    for k, places in seen.items():
        distinct = {f"{nm}[{slug}]" for nm, slug in places}
        if len(distinct) <= 1:
            continue
        # Same usageKey does not mean same taxon. `_same_taxon` is the one
        # definition of that question, shared with the dedupe, so this gate
        # cannot fail on something the dedupe is right to keep -- which it did
        # on 24 subspecies before, pointing at a script that deliberately spares
        # them.
        nms = {nm for nm, _s in places}
        if all(_same_taxon(a, b) for a in nms for b in nms):
            dupes[k] = sorted(distinct)
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
    read_parquet = False
    try:
        import duckdb
        if not _parquet_unusable():
            con = duckdb.connect()
            rows = con.execute("""
                SELECT kingdom, count(*) AS n
                FROM read_parquet(?)
                WHERE rank = 'SPECIES'
                  AND (lineage IS NULL OR lineage = '')
                GROUP BY kingdom
            """, [PARQUET_PATH]).fetchall()
            con.close()
            read_parquet = True
            for kingdom, n in rows:
                missing[kingdom] = n
    except Exception:
        pass
    if missing:
        fail("every species carries a lineage",
             f"{sum(missing.values()):,} without one "
             f"({', '.join(f'{k} {v:,}' for k, v in missing.most_common())})")
        return
    # Slow path whenever the parquet did not answer -- missing, stale, or
    # duckdb absent. `missing` being empty is not evidence the check passed; it
    # is only evidence nothing was read.
    if not read_parquet:
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
    ap.add_argument("--json", default="",
                    help="also write {failures, passes} here, for "
                         "maintenanceSession.py's before/after comparison")
    args = ap.parse_args()
    os.chdir(ROOT)
    print("verifying the tree's data invariants")
    check_parquet_freshness()
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
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"failures": failures, "passes": passes}, fh, indent=1)
    if failures:
        print(f"\n  {len(failures)} FAILED")
        return 1
    print("\n  all invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
