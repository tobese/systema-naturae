#!/usr/bin/env python3
"""One traversal for the whole tree. Everything else imports this.

The tree is a set of nested JSON documents under
`taxonomy/<kingdom>/[<phylum>/][<class>/]<order>/<family>/src/data/*.json`,
read on demand by the portal. As of 2026-10-05 that is 14,085 family files and
2,388,477 species across six kingdoms, about 0.97 GB.

Why this module exists
----------------------
Twenty-seven scripts each globbed those files and hand-rolled their own walk.
They did not agree, and every serious defect found while importing sources in
October 2026 was two of them disagreeing rather than a missing feature:

- `resyncFamilyCounts.py` first counted only a family's direct children and
  reported "node UNDERstates the file: 0" -- true, and true only of the kingdom
  it happened to read. The other five had 574 understated nodes worth 2,546
  species, and the same pass rewrote 360 files' `speciesCount` down to a wrong
  number.
- `dedupeSpeciesAcrossFamilies.py` was single-level deep, so it was blind to the
  143,300 animalia species that hang under a SUBFAMILY or TRIBE node, and
  reported 7 duplicate ids where there were 22. A tool that reports "nothing to
  do" is the most dangerous kind, because it is indistinguishable from a clean
  tree.
- `fix_*.py` globbed bare `**/src/data/*.json` from the current directory,
  which matches 14,087 files rather than the 14,085 families: it swept in
  `shared/src/data/continents.json` (not a family at all) and
  `portal/bivalvia/ostreida/bivalvia_margaritidae/...`, a stale family left
  behind by the move to `taxonomy/<kingdom>/...`. Both are tracked, so the
  fixers really were writing to them.

`speciesList` is a build-output shape, not a source shape
---------------------------------------------------------
Worth stating because it is the obvious thing to get wrong, and getting it
wrong in either direction is a silent factor-of-20 error:

- **0 of the 14,085 source family files** contain `speciesList`. It is created by
  the compression pass in `portal/scripts/buildData.ts`, which folds minimal
  species into `speciesList[]` so the skeleton stays small.
- In the built animalia order files, **1,516,480 of 1,630,700 species (93%) sit
  inside `speciesList`**; only 114,220 are in `children`.

So a walk that skips `speciesList` is correct on a family file and wrong by 93%
on a built order file. `iter_nodes` therefore descends both, and the traversal
is uniform rather than source-aware -- one shape, so there is nothing to get
wrong depending on which file you were handed.

A real query engine was measured and rejected (`BACKLOG.md`, "Plan: one
traversal, then a query layer"): DuckDB reads the nested JSON via `json_tree()`
but a view over 14,085 files costs ~50s and a flatten attempt OOM'd at 12.7 GiB,
against `verifyTree`'s 2m21s for nine invariants. The engine was never the
bottleneck -- JSON parsing is. So the fix is a single traversal, and only then
a query layer on top of it.

The contract
------------
Three shapes, and the differences are load-bearing:

- `iter_nodes` — every node, including the root, descending into **both**
  `children` and `speciesList`.
- `iter_species` — every node whose `rank == "SPECIES"`, **including the root
  if the root is itself a species**. `count_species` is `sum(1 for _ in
  iter_species(doc))` by construction, so the two can never drift.
- `iter_species_with_parent` — `(parent, species)` pairs, for the tools that
  need the owning genus.

Iteration order is document order: the node, then `children` recursively, then
`speciesList`. It is deterministic so that a script's output ordering is stable
across runs.

Guarding against silent disagreement
------------------------------------
`assert_count_matches` is deliberately in this module rather than left to each
caller: it is the assertion that would have caught the `speciesList` bug class.
New code should prefer `count_species` outright and reach for this only when
comparing against a second, independently derived number.

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    from tree import iter_family_files, iter_species, count_species

    for fam in iter_family_files("animalia"):
        doc = fam.load()
        print(fam.slug, count_species(doc))
"""
from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_DIR = "taxonomy"
KINGDOM_CONFIG = os.path.join("portal", "data", "kingdom-config.json")
SPECIES_RANK = "SPECIES"

Node = Dict[str, Any]


# --------------------------------------------------------------------------
# Kingdoms
# --------------------------------------------------------------------------

def kingdom_names() -> List[str]:
    """The six kingdoms, in `kingdom-config.json` order.

    Read from the config rather than hardcoded. `verifyTree.py` carried its own
    copy of this mapping (and therefore its own copy of the plantae `-snippet`
    filename quirk, which is the kind of thing that goes stale silently).
    """
    with open(os.path.join(ROOT, KINGDOM_CONFIG), encoding="utf-8") as fh:
        return list(json.load(fh)["kingdoms"])


KINGDOMS: List[str] = kingdom_names()


# Imported but not built (portal stays six kingdoms, see CLAUDE.md); same
# mapping as importColChecklist.BACTERIA_VIRUSES_INPUT. Only reachable by
# naming the kingdom -- KINGDOMS and every default walk stay the six.
BACTERIA_VIRUSES_INPUT = {
    "bacteria": "data/taxonomy-bacteria.json",
    "viruses": "data/taxonomy-viruses.json",
}


def kingdom_input(kingdom: str) -> str:
    """Repo-relative path to a kingdom's taxonomy input document."""
    if kingdom in BACTERIA_VIRUSES_INPUT:
        return os.path.join("portal", BACTERIA_VIRUSES_INPUT[kingdom])
    with open(os.path.join(ROOT, KINGDOM_CONFIG), encoding="utf-8") as fh:
        cfg = json.load(fh)["kingdoms"][kingdom]
    return os.path.join("portal", cfg["input"])


def load_kingdom_taxonomy(kingdom: str) -> Node:
    """The skeleton document: ranks down to FAMILY, no species."""
    path = os.path.join(ROOT, kingdom_input(kingdom))
    if not os.path.exists(path):
        raise FileNotFoundError(f"{kingdom}: {kingdom_input(kingdom)} absent")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Traversal
# --------------------------------------------------------------------------

def iter_nodes(doc: Node) -> Iterator[Node]:
    """Every node in the document, root first, at any depth.

    Descends into `speciesList` as well as `children`, because which of the two
    carries the species depends on whether you were handed a family file or a
    built order file -- and on a built order file `speciesList` carries 93% of
    them. Iterative rather than recursive: the tree is only 9 deep, but the
    traversal runs 2.4M times and there is no reason to pay Python frames for it.
    """
    stack = [doc]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        yield node
        # Reversed so that popping restores document order.
        children = node.get("children") or []
        for child in reversed(children):
            stack.append(child)
        for sp in reversed(node.get("speciesList") or []):
            stack.append(sp)


def iter_species(doc: Node) -> Iterator[Node]:
    """Every SPECIES node, including the root when the root is a species.

    The root-inclusive part is deliberate: a species node passed in directly
    yields itself rather than nothing. `importSpeciesFile.iter_species` already
    worked that way and `resyncFamilyCounts.count_species` did not, which is
    another pair that disagreed on the same document.
    """
    for node in iter_nodes(doc):
        if node.get("rank") == SPECIES_RANK:
            yield node


def iter_species_with_parent(doc: Node) -> Iterator[tuple]:
    """`(parent, species)` for every species, at any nesting depth.

    For the tools that need the owning genus -- the deduper, and anything that
    reports a species under a family. `parent` is `None` only if `doc` is itself
    a species and was passed in at the root.
    """
    stack = [(None, doc)]
    while stack:
        parent, node = stack.pop()
        if not isinstance(node, dict):
            continue
        if node.get("rank") == SPECIES_RANK:
            yield parent, node
        children = node.get("children") or []
        for child in reversed(children):
            stack.append((node, child))
        for sp in reversed(node.get("speciesList") or []):
            stack.append((node, sp))


def count_species(doc: Node) -> int:
    """Species under `doc`, at any depth, including `speciesList`.

    Defined in terms of `iter_species` on purpose. The twenty-seven hand-rolled
    versions of this function were where the tree's worst bugs lived, and the
    cheapest defence is to make it impossible for the count and the walk to
    disagree.
    """
    return sum(1 for _ in iter_species(doc))


def species_ids(doc: Node) -> Set[str]:
    """Every species `id` under `doc`. Nodes without an `id` are skipped."""
    return {s["id"] for s in iter_species(doc) if s.get("id")}


def count_rank(doc: Node, rank: str) -> int:
    """Nodes at `rank` under `doc`, at any depth.

    `count_species` is `count_rank(doc, "SPECIES")`; this exists so the rarer
    counters -- genera, subspecies, the fossil check -- stop being hand-rolled
    one per script. `genus_count` in `dedupeSpeciesAcrossFamilies.py` and
    `genusCount` written into family files are both this.
    """
    return sum(1 for n in iter_nodes(doc) if n.get("rank") == rank)


def assert_count_matches(doc: Node, expected: int, label: str = "") -> None:
    """Raise unless `count_species(doc) == expected`.

    Exists so the `speciesList` bug class has a cheap assertion available.
    Prefer `count_species` directly; use this when comparing against a number
    derived some other way.
    """
    got = count_species(doc)
    if got != expected:
        raise AssertionError(f"{label or '<doc>'}: expected {expected} species, counted {got}")


# --------------------------------------------------------------------------
# Family files on disk
# --------------------------------------------------------------------------

def sidecar_key_for(path: str) -> str:
    """A key that is unique per family *file*, not per family *name*.

    `FamilyFile.slug` is the family directory's basename, and that is not
    unique: 103 families are called `incertae-sedis` -- the placeholder name
    reused down dozens of phyla -- and two are called `personidae`, so the tree
    holds 14,821 family documents under 14,718 distinct slugs.

    Anything keyed on slug therefore collapses those together. The name-parse
    index did, and the damage was worse than a missing entry: a sidecar keyed by
    slug is written by all 103 in turn, so the one that survives holds one
    family's records and the other 102 read it back. A GBIF parse verdict is per
    *name string*, so those reads return a well-formed answer about the wrong
    family rather than an obvious miss.

    The rank path is what actually distinguishes them, and it is what the tree
    already uses to place a family. Derived from the path alone, so the family
    walker and the name scanner -- which never pass anything to each other --
    cannot disagree about a family's key.
    """
    parts = os.path.relpath(os.path.abspath(path), ROOT).split(os.sep)
    # taxonomy/<kingdom>/[phylum/][class/]<order>/<family>/src/data/<file>.json
    try:
        cut = parts.index("src")
    except ValueError:
        cut = len(parts)
    return "_".join(p for p in parts[1:cut] if p)


class FamilyFile(NamedTuple):
    """One family document on disk, with the identity callers keep needing."""

    slug: str
    kingdom: str
    path: str

    @property
    def sidecar_key(self) -> str:
        """Path-derived and unique per file, unlike `slug`. See
        `sidecar_key_for` -- 103 families share the slug `incertae-sedis`."""
        return sidecar_key_for(self.path)

    def load(self) -> Node:
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, doc: Node) -> None:
        save_json(self.path, doc)


def _is_family_file(path: str) -> bool:
    """A family document is named after the directory that holds it.

    `<family>/src/data/<family>.json`. This is the same rule `familyPath.ts`
    builds with, so filtering by it cannot diverge from what the graft reads.

    The filter is not cosmetic: `taxonomy/animalia/.../felidae/src/data/` also
    holds `continents.json`, a 169 KB GeoJSON continent map that every
    `**/src/data/*.json` glob has been picking up and parsing as a family. It
    held 0 species, so no count was ever wrong -- but a 0-species family is
    exactly what a fixer writes `speciesCount: 0` onto, and this one is not a
    family.

    Both sides are normalised because the two conventions coexist: some
    directories are `incertae_sedis` and some `incertae-sedis`, and in every
    case the file matches its own directory rather than a global convention.
    """
    family_dir = os.path.basename(os.path.dirname(os.path.dirname(
        os.path.dirname(path))))
    slug = os.path.basename(path)[:-5]

    def norm(s: str) -> str:
        return s.lower().replace("-", "_").replace(" ", "_")

    return norm(slug) == norm(family_dir)


def iter_family_files(kingdom: Optional[str] = None) -> Iterator[FamilyFile]:
    """Yield every family document, optionally narrowed to one kingdom.

    Family files sit at `taxonomy/<kingdom>/[<phylum>/][<class>/]<order>/<family>/src/data/*.json`.
    The rank depth varies -- Tardigrada has no class -- so a joined path is a
    guess and the glob is the honest way in. Scoped to `taxonomy/` rather than
    a bare `**/src/data/*.json` from the working directory, and `node_modules`
    is filtered once here for every caller.

    14,084 documents, in sorted order so that two runs agree. Order was load
    bearing by accident: `verifyTree` keyed these by slug into a dict, so glob's
    arbitrary order decided which of two same-slug files survived.

    `kingdom=None` walks all six.
    """
    kingdoms = [kingdom] if kingdom else kingdom_names()
    for k in kingdoms:
        pattern = os.path.join(ROOT, TAXONOMY_DIR, k, "**", "src", "data", "*.json")
        for path in sorted(glob.glob(pattern, recursive=True)):
            if "node_modules" in path or not _is_family_file(path):
                continue
            yield FamilyFile(os.path.basename(path)[:-5], k, path)


def assert_sidecar_keys_unique(families=None) -> int:
    """Raise if two family files would share a sidecar. Returns the count.

    The key joins rank-path segments with `_`, and six directories in this tree
    already contain `_`, so the join is in principle ambiguous -- it happens not
    to be for the current 14,821 documents. That is a property of today's
    directory names, not a guarantee, and a rename could break it silently and
    in the same way: several families writing one sidecar. So it is checked, and
    it is checked by callers that are about to key a file on it.
    """
    families = list(iter_family_files()) if families is None else list(families)
    seen = {}
    for fam in families:
        key = fam.sidecar_key
        if key in seen:
            raise AssertionError(
                f"sidecar key collision: {seen[key]} and {fam.path} both key "
                f"as {key!r}. sidecar_key_for joins rank-path segments with "
                f"'_', so a directory name containing '_' can collide; change "
                f"the separator rather than letting two families share a "
                f"sidecar.")
        seen[key] = fam.path
    return len(seen)


def family_data_files() -> List[str]:
    """Absolute paths of every family document, all six kingdoms, sorted.

    What the `fix_*.py` sweepers want. They used to glob bare
    `**/src/data/*.json` from the working directory and filter it with the
    denylist `["unified-taxonomy", "node_modules", "portal/data", "shared/data"]`,
    which is four guesses about where the family files are not, rather than one
    statement of where they are. Two files slipped through: `felidae`'s GeoJSON
    `continents.json`, and `portal/bivalvia/ostreida/bivalvia_margaritidae/...`,
    a family left behind by the 2026-09-28 move to `taxonomy/<kingdom>/...`.
    Both were being opened and rewritten.
    """
    return [fam.path for fam in iter_family_files()]


def find_family_file(slug: str) -> Optional[FamilyFile]:
    """Locate one family's document by slug, or None.

    Searches every kingdom. A slug is unique in practice; if it ever is not, the
    first match wins and that is the caller's problem to notice.
    """
    for fam in iter_family_files():
        if fam.slug == slug:
            return fam
    return None


def iter_all_species(kingdom: Optional[str] = None) -> Iterator[tuple]:
    """`(FamilyFile, species)` across whole kingdoms.

    The expensive one: it parses every family document in the kingdom, so a
    caller that needs this should build its index once rather than call it in a
    loop. That is what `tree.py` exists to make possible, and what the derived
    `species.parquet` in `BACKLOG.md` is for once disk allows.
    """
    for fam in iter_family_files(kingdom):
        for sp in iter_species(fam.load()):
            yield fam, sp


# --------------------------------------------------------------------------
# Family -> path resolution
# --------------------------------------------------------------------------
#
# Python mirror of `portal/scripts/lib/familyPath.ts`, which is the build's
# authority for the same question. Two implementations of one rule is already
# two, so this one is kept deliberately short and mechanical; if you change the
# rule, change it there first.
#
#     taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json
#
# Every rank is optional because the tree decides. Tardigrada is
# KINGDOM > PHYLUM > FAMILY with no class and no order.

def dir_name(rank_name: Optional[str]) -> str:
    """Directory name for a rank: lower-case, spaces to underscores."""
    return (rank_name or "").lower().replace(" ", "_")


def candidate_paths(kingdom: str, phylum=None, cls=None, ord=None,
                    slug: str = "") -> List[str]:
    """Relative candidate paths for a family's file, most specific first.

    Absent ranks are omitted rather than defaulted, so a family with no class or
    no order still resolves.
    """
    k, p, c, o = (dir_name(x) for x in (kingdom, phylum, cls, ord))
    tails = [
        [p, c, o, slug], [c, o, slug], [p, o, slug],
        [p, c, slug], [p, slug], [c, slug], [slug],
    ]
    out, seen = [], set()
    for tail in tails:
        segs = [s for s in tail if s]
        if not segs:
            continue
        rel = os.path.join(TAXONOMY_DIR, k, *segs, "src", "data", f"{slug}.json")
        if rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


def resolve_family_file(kingdom: str, phylum=None, cls=None, ord=None,
                        slug: str = "") -> Optional[str]:
    """Absolute path to a family's file, or None if it is not on disk.

    Existence, not construction, is the test. The rank depth varies, so a joined
    path is a guess until something confirms it -- and a guess that is never
    confirmed is how `importFamily.ts` and friends used to report success having
    enriched nothing.
    """
    for rel in candidate_paths(kingdom, phylum, cls, ord, slug):
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            return path
    return None


def iter_family_nodes(kingdom: str, doc: Optional[Node] = None) -> Iterator[tuple]:
    """`(node, ranks)` for every FAMILY node in a kingdom's taxonomy document.

    `ranks` is `{"kingdom", "phylum", "cls", "ord"}` -- the input
    `resolve_family_file` needs. Walking the document is the only way to get
    these: `appSlug` alone is not unique, and joining a node to its file by slug
    silently drops families (87 distinct `incertae-sedis` directories in fungi).

    Pass `doc` when you have already loaded the document and intend to write it
    back -- the yielded nodes are the objects inside *your* document, so
    mutating them is what actually changes the file. Without it the document is
    loaded here and the mutation is thrown away.
    """
    if doc is None:
        doc = load_kingdom_taxonomy(kingdom)
    stack = [(doc,
              {"kingdom": kingdom, "phylum": None, "cls": None, "ord": None})]
    while stack:
        node, ranks = stack.pop()
        rank = node.get("rank")
        if rank == "FAMILY":
            yield node, ranks
            continue
        if rank in ("PHYLUM", "CLASS", "ORDER"):
            ranks = dict(ranks, **{{"PHYLUM": "phylum", "CLASS": "cls",
                                   "ORDER": "ord"}[rank]: node.get("name")})
        for child in reversed(node.get("children") or []):
            stack.append((child, ranks))


# --------------------------------------------------------------------------
# IO
# --------------------------------------------------------------------------

def save_json(path: str, doc: Node, indent: int = 2) -> None:
    """Write a family document back, matching what the importers write.

    `ensure_ascii=False` and a trailing newline, because the existing 14,085
    committed family files were written that way and a different format turns
    every one of them into a spurious whole-file diff.

    **Atomic.** The write goes to a sibling temp file and is renamed into place,
    so an interrupted run cannot leave a half-written family document behind.
    This is not hypothetical: a `dedupeSpeciesAcrossFamilies.py` run that took a
    SIGTERM mid-write truncated
    `lepidoptera/crambidae/src/data/crambidae.json` by 119,337 lines, leaving a
    file whose last line was an unterminated object. The next run to read it
    failed on JSONDecodeError at a byte offset, which says nothing about which
    of the several thousand writes in the run was at fault -- the damage is
    indistinguishable from bad data until you diff it.

    A rename within the same directory is atomic on POSIX, so a reader either
    sees the old file or the new one and never a partial one. The `finally`
    unlinks the temp file on an exception, so a failed write leaves nothing.
    """
    tmp = f"{path}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=indent, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _selftest() -> int:
    """Assert the traversal contract against the shapes that broke it.

    Cheap enough to run anywhere, and it is the only test the module has, so it
    carries the cases that have actually bitten:
      - species compressed into `speciesList` must be counted
      - species under a SUBFAMILY/TRIBE must be counted
      - `count_species` must equal `len(list(iter_species(...)))` always
      - a species passed in as the root must count itself
    """
    fam = {
        "rank": "FAMILY",
        "children": [
            {"rank": "SUBFAMILY", "children": [
                {"rank": "GENUS", "children": [
                    {"rank": "SPECIES", "id": "deep-1"},
                    {"rank": "SPECIES", "id": "deep-2"},
                ]},
            ]},
            {"rank": "GENUS", "speciesList": [
                {"rank": "SPECIES", "id": "compressed-1"},
                {"rank": "SPECIES", "id": "compressed-2"},
                {"rank": "SPECIES", "id": "compressed-3"},
            ]},
        ],
    }
    assert count_species(fam) == 5, count_species(fam)
    assert count_species(fam) == len(list(iter_species(fam)))
    # fam, subfamily, deep genus, 2 deep species, compressed genus, 3 compressed
    assert len(list(iter_nodes(fam))) == 9
    assert species_ids(fam) == {"deep-1", "deep-2", "compressed-1",
                               "compressed-2", "compressed-3"}
    assert count_species({"rank": "SPECIES", "id": "root"}) == 1
    assert [p["rank"] for p, _ in iter_species_with_parent(fam)] == ["GENUS"] * 5

    # Document order must be stable, because callers print in it.
    assert [n.get("id") for n in iter_species(fam)] == [
        "deep-1", "deep-2", "compressed-1", "compressed-2", "compressed-3"]

    try:
        assert_count_matches(fam, 4, "selftest")
    except AssertionError:
        pass
    else:
        raise SystemExit("assert_count_matches did not fire")

    # The shape a family file actually has: species in `children`, no
    # `speciesList` anywhere. A traversal or a pruner that reasons from
    # `speciesList` looks correct against a built order file and destroys a
    # family file -- which is what dedupeSpeciesAcrossFamilies did to 689 of
    # them, emptying every one (351,882 species) while its commit message
    # reported 8,745 removals.
    source_shaped = {
        "rank": "FAMILY",
        "children": [{"rank": "GENUS", "children": [
            {"rank": "SPECIES", "id": "a"},
            {"rank": "SPECIES", "id": "b"},
        ]}],
    }
    # A GBIF usageKey is not always one taxon: subspecies, varieties and
    # hybrids are filed under their parent's key, so `Buthus occitanus
    # israelis` shares key 4553865 with `Buthus occitanus`. Collapsing on the key
    # alone deleted 194 subspecies and hybrids in one pass. These four
    # comparisons are what tell a true duplicate from a namesake relative, and
    # they failed in both directions before they were pinned here: truncating
    # both sides to two words made the subspecies equal its parent, and testing
    # for the hybrid marker after truncation never saw the `x`.
    from dedupeSpeciesAcrossFamilies import _same_taxon
    assert _same_taxon("Buthus occitanus", "Buthus occitanus")
    assert not _same_taxon("Buthus occitanus israelis", "Buthus occitanus")
    assert _same_taxon("Aethaloperca rogaa Forsskål, 1775", "Aethaloperca rogaa")
    assert _same_taxon("Caprodon schlegelii Günther, 1859", "Caprodon schlegelii")
    assert _same_taxon("Eisenia patriciae Szederjesi, Pavlíček, "
                       "Coşkun & Csuzdi, 2014", "Eisenia patriciae")
    assert not _same_taxon("Carassius auratus x Cyprinus carpio",
                           "Carassius auratus")
    assert _same_taxon("Homo sapiens", "Homo sapiens sapiens")

    assert "speciesList" not in json.dumps(source_shaped)
    assert count_species(source_shaped) == 2
    assert [n["id"] for n in iter_species(source_shaped)] == ["a", "b"]

    print("tree.py selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())