#!/usr/bin/env python3
"""Remove species copies that a source put in a second family we already had.

An import writes each offered species into the family the *source* assigns it
to. Where a source's circumscription differs from ours, that writes a species we
already hold somewhere else into a second family: 236 such copies across 57
file-pairs after the ILDIS, FLOW, Moss and Wikispecies runs, Kinnaridae and
Meenoplidae each holding the other's cixiid relatives.

This drops the copy that the import added and keeps the one the tree already
had, which is the rule `dedupe_genera_across_families.py` already applies for a
duplicated *genus*: the curated placement wins, and the taxonomy disagreement is
recorded rather than silently resolved in the source's favour.

"Added by an import" is decided from the node's own provenance, not from mtimes
or from which file happens to be larger. Where both copies came from an import,
the one in the family with more species keeps it, which is the same tie-break the
genus dedupe uses.

Two species are the same taxon when either the tree's own id says so, or an
external authority does. The second test is new and much stronger: 4,455 pairs
of our species share a GBIF usageKey within one kingdom, which is GBIF saying
they are one taxon rather than us inferring it from a name. Every previous
dedupe this session ran on name or id heuristics.

Cross-kingdom collisions are excluded by construction, because they are a
kingdom-placement disagreement rather than a duplicate -- 67 of the 4,522
collisions are of that kind, and the 7 deliberately undecided placements
(Cincloramphus, Poodytes, Oryzoborus) are left alone.

Choosing the survivor. Three signals, ranked, and the first is the only one that
knows which FAMILY is correct:

    1. --authority-family, when passed: does this copy sit in the family GBIF
       assigns to that usageKey. A copy that does is a correct placement; a copy
       that does not is a misfiling, however well documented it is.
    2. conforming name (a name that has swallowed its authorship is an import
       artefact, not a better record)
    3. richness (description / commonName / continents / reference / year)

Signal 1 is not the default because it makes an external taxonomy an input to a
decision the tree is otherwise entitled to make itself, and because the script's
standing rule is that the curated placement wins over a source's. It is also the
difference between right and wrong: without it, 1,242 of the 4,480 removals threw
away the only correctly-placed copy in favour of a richer one filed under the
wrong family -- `anobiidae` losing 159 species to `ptinidae`, `lobariaceae`
losing 128 to `peltigeraceae`, 159 distinct family-pair patterns. With it, zero.

Build the cache with `fetchGbifFamilyCache.py`, which fetches only the keys
actually in duplicate (~4,500 requests, not 2.7 million). Pass it whenever
this script has authority collisions to resolve:

    python3 scripts/dedupeSpeciesAcrossFamilies.py \\
        --authority-family portal/data/gbif-family-cache.json

One case the provenance rule cannot see
-------------------------------------

"Added by an import" is the right question about a *duplicate*, but declining to
answer it is the wrong answer about the tree. On the current tree the provenance
rule leaves 118 id-groups alone, and every one of them is a documented record
sitting beside a bare stub:

    SP_ENHYDRIS_ENHYDRIS_SCHNEIDER_1799   homalopsidae  wikidata  desc+common
                                       colubridae  worms         (bare)

A stub with no description, no common name, no continents and no reference is
not a second record of the taxon -- it is the absence of one, filed in the wrong
family by a source whose circumscription differs from ours. Keeping it means
`verifyTree` stays red on `no species id in two families` forever, and the portal
shows the same animal twice, once with no information.

So there is a fourth case, narrower than the other three, and it needs no
external taxonomy and no cache:

    4. one documented copy beside one bare copy -- keep the documented one, and
       carry the bare one's `sourceIds` across before dropping it.

The payload is provenance rather than description: the documented copy already
has the description, and what the stub uniquely holds is the external id the
other source issued, which is exactly what stops the next import re-adding it.

Deliberately narrow, because a stub is only recognisable as one:

  * different families only -- a within-file duplicate is
    `verifyTree.check_duplicate_species`' business and carries its own
    allowance, so it is counted and left;
  * every copy rank SPECIES -- a subspecies filed as a species must never be
    deleted by a rule about stubs;
  * exactly one documented copy -- two documented copies are a real tie and are
    counted for a human, not guessed at;
  * the documented copy not already marked for removal by the authority rule --
    undoing that would silently reverse a decision made for a different reason.

Idempotent either way.

    python3 scripts/dedupeSpeciesAcrossFamilies.py
    python3 scripts/dedupeSpeciesAcrossFamilies.py --apply

    Precedence
    ----------
    The provenance rule runs first and the richness rule second, and that order
    matters. `sourcedFrom` decides whether a copy is "an import's", but the set
    is incomplete -- `worms`, `gbif`, `wikipedia` and `itis` are imports too and
    are not in it. So the provenance rule can keep a bare stub and drop the
    documented record beside it, which it did on 61 of the 171 groups this pass
    handled: every documented copy was removed and every bare one kept. When the
    copy the provenance rule would keep is bare and one it would drop is
    documented, the call is deferred to the richness rule, so the documented
    copy wins and the gate stays green. The two rules cannot disagree on which
    copy is documented, so nothing is double-counted.
"""
import argparse
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402
from tree import (  # noqa: E402
    save_json,  # noqa: E402
    KINGDOMS,
    count_rank,
    count_species,
    iter_family_files,
    iter_species_with_parent,
)

# Which sources count as "written by an import", i.e. a copy that arrived in a
# family the *source* chose rather than one the tree already held. Set 2026-10-05
# with only the two sources that had run by then, and not widened when WoRMS
# landed -- so a wikipedia<->worms pair read as "neither copy is an import" and
# this script left it alone. Of the 172 same-kingdom cross-family duplicates
# verifyTree reported afterwards, WoRMS had written 110 of them; they are the
# same disagreement this docstring describes, one import later.
#
# Keep this a named list rather than "any node with a sourcedFrom": see the
# allow-list note above.
IMPORTED = {"checklistbank", "catalogue of life", "worms"}


def _authority_ids(source_ids: dict) -> str:
    """The same projection fillAuthorityIds.py writes, so a merge does not
    leave `authorityIds` disagreeing with the `sourceIds` it derives from."""
    parts = []
    for source in sorted(source_ids):
        ids = source_ids[source]
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        for v in sorted({str(i) for i in ids}):
            parts.append(f"{source}:{v}")
    return ",".join(parts)


# Fields worth carrying across a merge. A duplicate is the same taxon held
# twice, so the two records between them hold one taxon's data and deleting
# one of them destroys half of it.
MERGEABLE = ("description", "commonName", "continents", "reference",
             "yearPublished", "namedAfter", "namedAfterDetail",
             "wikipediaUrl", "iucnStatus", "extinct", "subspeciesCount")


def merge_into(winner, loser):
    """Fold `loser`'s record into `winner` in place. Returns what moved.

    Module level so dedupeNamesAgainstCol.py merges by the same rule."""
    moved = []
    for field in MERGEABLE:
        # only where the winner has nothing: two records disagreeing on a
        # description is not resolved by preferring one of them here.
        if not winner.get(field) and loser.get(field):
            if field == "subspeciesCount":
                # a count, not a truthy flag: take the larger.
                if int(loser.get(field) or 0) <= int(winner.get(field) or 0):
                    continue
            winner[field] = loser[field]
            moved.append(field)
    si_w = winner.get("sourceIds") or {}
    si_l = loser.get("sourceIds") or {}
    if si_l:
        merged = dict(si_w)
        for source, ids in si_l.items():
            have = merged.get(source)
            if not isinstance(have, list):
                have = [have] if have else []
            add = ids if isinstance(ids, list) else [ids]
            for v in add:
                if v not in have:
                    have.append(v)
            merged[source] = have
        winner["sourceIds"] = merged
        # authorityIds is a derived projection of sourceIds, so a merge that
        # widened sourceIds leaves it stale and the app reads the stale one.
        winner["authorityIds"] = _authority_ids(merged)
    return moved


def _strip_authorship(name):
    """Drop everything that is not the scientific name proper.

    Our names carry authorship the authority's `species` field does not
    (`Aethaloperca rogaa Forsskål, 1775`, or `Eisenia patriciae Szederjesi,
    Pavlíček, Coşkun & Csuzdi, 2014`), and sometimes a bracketed note.

    Rank markers are also dropped, because the trinomial a subspecies or
    variety carries is a rank marker rather than part of the name:
    `Buthus occitanus israelis` becomes `buthus occitanus`. That is correct
    here, and `_same_taxon` is where the distinction is made -- it compares
    against the full canonical name, not the stripped one.
    """
    nm = (name or "").strip()
    if not nm:
        return ""
    nm = nm.split(" (")[0].strip()
    nm = nm.split(" [")[0].strip()
    if "(" in nm and nm.endswith(")"):
        nm = nm[: nm.rindex("(")].strip()
    parts = nm.split()
    keep = []
    for w in parts:
        bare = w.strip(".,")
        if bare.lower() in {"x", "×", "var", "subsp", "f", "forma", "ssp", "subvar"}:
            break
        # A bare year is a date, not an epithet: one importer writes
        # `Glaciambulata neumayeri` and another `Glaciambulata neumayeri, 2016`
        # for the same species, and the year is the only difference.
        if len(keep) >= 2 and bare.isdigit() and 1000 <= int(bare) <= 2100:
            continue
        # A bare (unparenthesised) authorship is capitalised mid-string while a
        # specific or subspecific epithet is not, so the capital is the marker:
        # `Caprodon schlegelii Günther, 1859` and `Eisenia patriciae
        # Szederjesi, Pavlíček, Coşkun & Csuzdi, 2014` both carry their
        # authorship this way. `Buthus occitanus israelis` must survive it, and
        # does -- `israelis` is lower case. Only consulted after the second word,
        # since the genus is always capitalised.
        if len(keep) >= 2 and bare[:1].isupper() and bare.isalpha():
            break
        keep.append(w)
    return " ".join(keep).lower().strip().rstrip(".,")


def _same_taxon(node_name, canonical):
    """True when the two names denote the same taxon, not merely the same genus.

    GBIF's `species` is a binomial (`Buthus occitanus`) or, where it filed one,
    a trinomial (`Homo sapiens sapiens`). Ours is that name, optionally plus a
    subspecies or variety epithet and optionally plus authorship. So:

      node == canonical                     the same taxon, a true duplicate
      node == canonical + one more word     a subspecies/variety of it -- NOT a
                                           duplicate, and collapsing the pair
                                           deletes the subspecies
      node contains `x` or `×`              a hybrid, which shares its parents'
                                           keys -- also not a duplicate

    An earlier version truncated both sides to two words before comparing, which
    made `buthus occitanus israelis` equal `buthus occitanus` and deleted 194
    subspecies. The extra words are the whole difference, so they are compared.
    """
    raw = (node_name or "").strip()
    canon = (canonical or "").strip().lower()
    raw_l = raw.lower()

    # A hybrid is checked on the raw name, before anything is stripped: the `x`
    # is in the middle, so truncation removes it and the check never fires.
    if " x " in f" {raw_l} " or raw_l.startswith("x ") or "×" in raw_l:
        return False

    nm = _strip_authorship(raw)
    if not nm or not canon:
        return True                       # cannot disprove; leave the pair alone
    if nm == canon:
        return True
    # The one asymmetry that matters. Ours may be *shorter* than GBIF's only
    # because the stripper removed a rank word (`Homo sapiens` against GBIF's
    # `Homo sapiens sapiens`). Ours may never be *longer*: that is a subspecies
    # or variety epithet, and `canon.startswith(nm)` would admit exactly the
    # `Buthus occitanus israelis` / `Buthus occitanus` case this exists to
    # reject.
    if canon.startswith(nm + " ") and len(canon.split()) > len(nm.split()):
        return True
    return False


DEDUPE_LOG = os.path.join("data", "dedupe-log.jsonl")

def append_dedupe_log(sid: str, winner_file: str, loser_file: str, reason: str) -> None:
    """Append one deduplication decision so machines don't undo each other."""
    os.makedirs(os.path.dirname(DEDUPE_LOG), exist_ok=True)
    entry = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "species_id": sid,
        "winner_file": winner_file,
        "loser_file": loser_file,
        "reason": reason,
    }
    with open(DEDUPE_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", default="",
                    help="default: every kingdom, which is what verifyTree.py "
                         "checks. Scoping this to one kingdom is how 4,310 "
                         "plantae duplicates went unnoticed next to a clean "
                         "animalia run.")
    ap.add_argument("--authority-family", default="",
                    help="path to the GBIF family cache from "
                         "fetchGbifFamilyCache.py. When given, the copy sitting "
                         "in the family GBIF assigns to that usageKey wins, "
                         "which is the only signal here that knows which FAMILY "
                         "is right: without it 1,242 species lost their correct "
                         "placement to a richer misfiled copy.")
    args = ap.parse_args()

    authority_family = {}
    authority_name = {}
    if args.authority_family:
        with open(args.authority_family, encoding="utf-8") as fh:
            cache = json.load(fh)
        authority_family = cache.get("families") or {}
        authority_name = cache.get("names") or {}
        print(f"  authority families: {len(authority_family):,} usageKeys from "
              f"{os.path.basename(args.authority_family)}")
        if not authority_name:
            print("    (cache has no `names` -- subspecies filed under a "
                  "parent's key cannot be told from duplicates; refetch with "
                  "fetchGbifFamilyCache.py)")

    kingdoms = [args.kingdom] if args.kingdom else KINGDOMS
    where = collections.defaultdict(list)
    by_authority = collections.defaultdict(list)
    docs = {}
    # path -> family name, so a copy can be scored on whether it sits in the
    # family the authority assigns to it. Derived from the path because that is
    # where the family already is; reading it from a node field would mean two
    # sources of truth for the same thing.
    file_family = {}
    file_kingdom = {}
    for fam in [x for k in kingdoms for x in iter_family_files(k)]:
        f, kingdom = fam.path, fam.kingdom
        try:
            d = fam.load()
        except Exception:
            continue
        docs[f] = d
        # `slug` is the directory name, so already lower case (`anobiidae`),
        # while GBIF returns display case (`Anobiidae`).
        file_family[f] = fam.slug.lower()
        file_kingdom[f] = kingdom
        for _parent, s in iter_species_with_parent(d):
            if s.get("id"):
                where[s["id"]].append((f, s))
                # authority identity, which needs no name judgement at all
                for auth, key in (s.get("sourceIds") or {}).items():
                    if key:
                        by_authority[(kingdom, auth, str(key))].append((f, s))

    dupes = {i: v for i, v in where.items() if len(v) > 1}
    print(f"  {'+'.join(kingdoms)}: {len(where):,} species ids, "
          f"{len(dupes):,} held in more than one family")

    # An authority-keyed collision is a duplicate without any name judgement:
    # GBIF issued that usageKey, so the two records are one taxon. Reported
    # separately from id collisions because the two sets barely overlap and the
    # authority one is the trustworthy one.
    # Same-file collisions count too. The first pass filtered to cross-file only
    # and left 107 behind, all of one kind: an authority written "&" inline and
    # "and" in the authorship field, which node_id reduces differently --
    # SP_CHUNIPHYES_MULTIDENTATA_LENS_AND_VAN_RIEMSDIJK_1908 beside
    # SP_CHUNIPHYES_MULTIDENTATA_LENS_VAN_RIEMSDIJK_1908 -- so one taxon had two
    # ids in one genus. GBIF says they are one; we were holding both.
    auth_groups = {}
    for (kingdom, auth, key), places in by_authority.items():
        if len(places) > 1:
            auth_groups.setdefault(kingdom, []).append((auth, key, places))
    n_auth = sum(len(v) for v in auth_groups.values())
    if n_auth:
        print(f"  authority-proven duplicates: {n_auth:,} "
              f"(same kingdom, same external id)")
        for kingdom, groups in list(auth_groups.items())[:3]:
            auth, key, places = groups[0]
            print(f"      e.g. {kingdom}/{auth} {key}: "
                  + ", ".join(sorted({(n.get('name') or '') for _f, n in places})[:2]))

    # Ranked most-significant first, and defined once at main() scope because the
    # safety pass below has to reuse the identical function: two scorers that can
    # disagree mean the guard silently undoes the rule it exists to protect.
    #
    #   1. in_the_right_family -- only when a cache was passed and it has an
    #      opinion. GBIF issued the usageKey, so the family it reports is a
    #      statement about the taxon; every other signal here is a statement
    #      about our node, and a node can be rich and wrong. This is what
    #      decides the 1,242 cases where a species sat in its correct family and
    #      in another, and the other one was better documented.
    #   2. conforming -- a name that has swallowed its own authorship is a
    #      formatting artefact of an import, not a better record.
    #   3. richness -- a copy that carries a description, common name or
    #      continents is worth more than one that does not.
    #   4. path -- deterministic, and the file that is not first alphabetically
    #      keeps, so two runs cannot disagree.
    #
    # What counts as data on a node, defined once because two definitions is how
    # the bare-stub rule below and the scorer above would come to disagree about
    # which copy is the documented one.
    RICH_FIELDS = ("description", "commonName", "continents",
                   "reference", "yearPublished")

    def richness_of(node):
        return sum(1 for k in RICH_FIELDS if node.get(k))

    def score(fp, auth=None, key=None):
        n = fp[1]
        nm = (n.get("name") or "").strip()
        au = (n.get("authorship") or "").strip()
        conforming = not (au and len(nm) > len(au) + 2 and nm.endswith(au))
        rich = richness_of(n)
        if authority_family and auth == "gbif":
            want = authority_family.get(key)
            if want:
                # Normalised on both sides: our slug is `anobiidae` from the
                # directory name, GBIF answers `Anobiidae`.
                want_n = want.lower().replace(" ", "").replace("-", "")
                in_family = file_family.get(fp[0], "") == want_n
                return (in_family, conforming, rich, fp[0])
        return (False, conforming, rich, fp[0])

    ranks = collections.Counter()
    renamed = 0
    drops = collections.defaultdict(set)      # file -> set(species id)
    keep_report = collections.Counter()
    for kingdom, groups in list(auth_groups.items()):
        survivors = []
        for auth, key, places in groups:
            canonical = authority_name.get(key)
            keep = []
            for fp in places:
                rank = fp[1].get("rank") or "SPECIES"
                if rank != "SPECIES":
                    ranks[rank] += 1
                    continue
                if canonical and not _same_taxon(fp[1].get("name"), canonical):
                    renamed += 1
                    continue
                keep.append(fp)
            if len(keep) > 1:
                survivors.append((auth, key, keep))
        auth_groups[kingdom] = survivors
    if ranks:
        print(f"    excluded, not rank SPECIES: "
              + ", ".join(f"{v:,} {k}" for k, v in ranks.most_common()))
    if renamed:
        print(f"    excluded, name differs from GBIF's name for the shared key: "
              f"{renamed:,} (a subspecies or hybrid filed under its parent)")



    merged_groups = 0
    merged_fields = collections.Counter()
    for kingdom, groups in auth_groups.items():
        for auth, key, places in groups:
            winner = max(places, key=lambda fp: score(fp, auth, key))
            # Copies inside ONE family are not a placement disagreement, they
            # are one taxon written twice -- which is what an importer that
            # folds authorship into `name` produces, and 322,076 plantae
            # species have a `name` that ends with their own `authorship`
            # beside a twin whose name does not. Deleting either copy loses
            # data: 77,902 of these pairs carry a description on one side
            # only, and 19,904 carry continents on one side only. So merge.
            same_family = len({fp[0] for fp in places}) == 1
            if same_family:
                merged_groups += 1
            # `fp is winner`, NOT `(f, n) is winner`. Unpacking and re-packing
            # builds a new tuple, so the identity test was False for every entry
            # including the winner -- which meant every copy of every authority
            # group was marked for deletion, and the winner survived only
            # because the safety pass below rescued one copy per group. That
            # rescue scored without the path tiebreak, so `max` returned
            # whichever family the sorted glob reached first and the survivor was
            # decided by alphabet: 1,648 of the 4,480 removals kept the copy in
            # a family GBIF contradicts.
            for fp in places:
                if fp is winner:
                    continue
                if same_family:
                    for field in merge_into(winner[1], fp[1]):
                        merged_fields[field] += 1
                    keep_report[f"merged in-family on {auth} id"] += 1
                drops[fp[0]].add(fp[1]["id"])
                append_dedupe_log(fp[1]["id"], winner[0], fp[0], f"collapsed on {auth} id")
            keep_report[f"collapsed on {auth} id"] += 1

    merge_touched = set()      # files written only because a merge changed them
    cross_bare_groups = 0
    deferred_provenance = 0   # groups the provenance rule would have dropped the
                              # documented copy for, because the copy it would
                              # keep was bare -- these are folded into the bare
                              # count below, so they are NOT a separate category
    for sid, places in dupes.items():
        files = {f for f, _ in places}
        # Cross-kingdom first, before any provenance-based branch gets a
        # chance to `continue`. This used to sit after the native/imported
        # and both-imported branches below, which don't check kingdom at
        # all -- so a cross-kingdom pair where one side's `sourcedFrom`
        # happened to land in IMPORTED and the other didn't (a real,
        # checklistbank-sourced record against a sourcedFrom:"none"
        # fabricated stub in a different kingdom, e.g. SP_ORTHOCERAS_
        # ANNULATA_SOWERBY_1818 in animalia vs. plantae) got resolved by
        # the kingdom-blind branch before this guard ever ran, deleting
        # the real copy and keeping the stub. Moving the check here is
        # what the module docstring already claimed happened "by
        # construction" -- it didn't, until now.
        if len({file_kingdom.get(f) for f, _s in places}) > 1:
            keep_report["left alone (cross-kingdom homonym)"] += 1
            continue
        imported = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") in IMPORTED]
        native = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") not in IMPORTED]
        if native and imported:
            # keep the copy we already had; drop every import-written one.
            # But "already had" is decided from `sourcedFrom`, and that set is
            # incomplete: `worms`, `gbif`, `wikipedia` and `itis` are imports too,
            # they just are not in IMPORTED. So this rule can keep a bare stub
            # and drop the documented record beside it -- which is exactly what
            # happened on 61 of the 171 groups this pass handled, where every
            # documented copy was removed and every bare one kept. When the copy
            # this rule would keep is bare and one it would drop is documented,
            # defer to the richness rule below: the documented copy is the
            # correctly-filed one (the bare one is the misfiling), and the gate
            # stays green either way.
            if richness_of(native[0][1]) == 0 and any(
                    richness_of(s) > 0 for _f, s in imported):
                deferred_provenance += 1
            else:
                for f, _s in imported:
                    drops[f].add(sid)
                    append_dedupe_log(sid, native[0][0], f,
                                      "dropped an imported copy, kept the existing one")
                keep_report["dropped an imported copy, kept the existing one"] += 1
                continue
        if len(imported) > 1:
            # both from imports: the bigger family keeps it
            sizes = {f: count_species(docs[f]) for f, _s in imported}
            win = max(sizes, key=lambda f: sizes[f])
            win_node = next(s for f, s in imported if f == win)
            losers = [(f, s) for f, s in imported if f != win]
            if richness_of(win_node) == 0 and any(
                    richness_of(s) > 0 for _f, s in losers):
                deferred_provenance += 1
            else:
                for f, _s in losers:
                    drops[f].add(sid)
                    append_dedupe_log(sid, win, f,
                                      "both imported; the larger family kept it")
                keep_report["both imported; the larger family kept it"] += 1
                continue
        # Nothing above fired, so no copy here is an import's. That settles the
        # provenance and says nothing about the tree: the group is a documented
        # record beside a bare stub, and a stub is the absence of a record, not a
        # second one. See "One case the provenance rule cannot see" in the module
        # docstring -- why this is narrow, and why the documented copy is also
        # the correctly-filed one (the bare copy is the one a source with a
        # different circumscription dropped into the wrong family).
        #
        # `merge_touched` exists because the merge below writes into the file
        # that KEPT the record, and that file is not in `drops` -- so the write
        # loop would never save it and the sourceIds carried across would be
        # computed and discarded. That is option (b) wearing option (a)'s label.
        if len({f for f, _s in places}) < 2:
            keep_report["left alone (both copies in one family)"] += 1
            continue
        # Cross-kingdom is already excluded at the top of this loop, before
        # the provenance branches above -- see the comment there. `Graphium
        # sarpedon` is a butterfly in papilionidae and a fungus in
        # microascaceae; `Diploderma polygonatum` is an agamid and a
        # diplocystidiid; `Hexagonia bicolor` is a carabid and a polypore.
        # They share an id because the id is derived from the name, not
        # because they are one taxon.
        if any((s.get("rank") or "SPECIES") != "SPECIES" for _f, s in places):
            keep_report["left alone (a copy is not rank SPECIES)"] += 1
            continue
        documented = [t for t in places if richness_of(t[1]) > 0]
        bare = [t for t in places if richness_of(t[1]) == 0]
        if not bare:
            keep_report["left alone (no copy is bare)"] += 1
            continue
        if len(documented) != 1:
            # Two documented copies disagree, or all copies are bare. Either way
            # this rule has no opinion, and guessing between two real records is
            # the one thing it must never do.
            keep_report[f"left alone ({len(documented)} documented copies)"] += 1
            continue
        win_f, win_n = documented[0]
        if win_f in drops and sid in drops[win_f]:
            # The authority rule already removed this copy. Rescuing it would
            # silently reverse a decision made for a different reason -- and that
            # reason (a subspecies filed under its parent's key) is exactly the
            # one this rule is not able to see.
            keep_report["left alone (documented copy already marked)"] += 1
            continue
        merge_touched.add(win_f)
        for f, s in bare:
            for field in merge_into(win_n, s):
                merged_fields[field] += 1
            drops[f].add(sid)
            append_dedupe_log(sid, win_f, f,
                              "dropped a bare copy, kept the documented one")
        cross_bare_groups += 1
        keep_report["dropped a bare copy, kept the documented one"] += 1

    # Safety: a dedupe must never delete the last copy of a species. Without
    # this guard the original script emptied 689 families (351,882 species),
    # and even the corrected prune can still drop every copy of a group when
    # the authority and id rules both fire on the same file.
    # The rescue must reuse `score` exactly. A local variant that scored only
    # the node -- conforming, richness, and a constant -- tied on every real
    # pair of bare import records, and `max` then returned the first entry in
    # glob order.
    # An authority key is not always one taxon. GBIF files a subspecies or a
    # hybrid under its parent's usageKey: key 4553865 is `Buthus occitanus`, and
    # our `Buthus occitanus israelis` carries the same number. Collapsing on the
    # key alone therefore deletes the subspecies and keeps the parent -- 207
    # nodes, of which 194 are subspecies like `BUTHUS_OCCITANUS_ISRAELIS` and
    # hybrids like `Carassius auratus x Cyprinus carpio`.
    #
    # Rank does not identify these: in our tree the subspecies is rank SPECIES,
    # because it is filed as one. The name does. So a copy is only a duplicate
    # if it is the same name as the key's canonical name in GBIF, and any copy
    # that disagrees is excluded from the collapse entirely -- not merely losing
    # the scoring, because scoring would still pick one of the two.
    # `auth_groups`, not `by_authority`: the latter is the unfiltered index and
    # still holds the subspecies and hybrids just excluded, so the guard would
    # rescue one of those and put back what the filter removed.
    collapsed = [(gauth, gkey, places) for groups in auth_groups.values()
                 for gauth, gkey, places in groups]
    orphaned = 0
    for gauth, gkey, places in collapsed:
        if len(places) > 1:
            survivors = [(f, s) for f, s in places if s["id"] not in drops[f]]
            if not survivors:
                # Same scorer, same arguments. This used to call `score` with no
                # authority key, which under --authority-family dropped the
                # first element for every candidate and so ranked the rescue
                # exactly as if no cache had been passed -- reintroducing, inside
                # the guard, the very misfiling the cache exists to prevent.
                best = max(places, key=lambda fp: score(fp, gauth, gkey))
                drops[best[0]].discard(best[1]["id"])
                orphaned += 1
    if orphaned:
        print(f"    safety: kept {orphaned:,} species whose every copy was "
              f"marked for deletion")

    for k, v in keep_report.items():
        print(f"    {v:>4}  {k}")
    if deferred_provenance:
        print(f"    {deferred_provenance:>4}  provenance deferred: the copy it would "
              f"keep was bare, so the documented copy wins instead")
    if merged_fields:
        print(f"  merged {merged_groups:,} in-family duplicate groups; fields "
              f"carried across from the copy that was removed:")
        for f, n in merged_fields.most_common():
            print(f"    {n:>7,}  {f}")
    if cross_bare_groups:
        merged_only = sorted(f for f in merge_touched if f not in drops)
        print(f"  collapsed {cross_bare_groups:,} bare copies into the documented "
              f"copy of the same species, carrying their sourceIds across "
              f"({len(merged_only)} family files rewritten for the merge alone)")
    print(f"  species to remove: {sum(len(v) for v in drops.values()):,} "
          f"from {len(drops)} files")

    # Running without the cache is still possible and still wrong in a way that
    # is invisible in the numbers: the removals are fewer, because nothing is
    # being spared, so the count looks healthier than the run that is careful.
    # 33 subspecies and hybrids are the difference on the current tree.
    if drops and not args.authority_family:
        print("  WARNING: no --authority-family given. This cannot tell a "
              "subspecies from a duplicate (they share a GBIF usageKey with "
              "their parent) and it cannot tell which family a copy belongs in. "
              "Run fetchGbifFamilyCache.py and pass the cache.")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    planned = sum(len(v) for v in drops.values())
    touched = 0
    removed = 0
    for f, ids in drops.items():
        d = docs[f]

        def prune(node):
            # `removed` is a local of main(), so this needs nonlocal -- with
            # `global` it raises NameError the first time prune runs, which is
            # after the family file has been mutated in memory and before it is
            # written, so --apply died on the first family.
            nonlocal removed
            if node.get("children"):
                before = len(node["children"])
                node["children"] = [s for s in node["children"]
                                    if s.get("id") not in ids]
                removed += before - len(node["children"])
            if node.get("speciesList"):
                before = len(node["speciesList"])
                node["speciesList"] = [s for s in node["speciesList"]
                                       if s.get("id") not in ids]
                removed += before - len(node["speciesList"])
            kept = []
            for g in node.get("children") or []:
                prune(g)
                if g.get("rank") == "SPECIES":
                    # A species is kept unless its id was in `ids`, and the
                    # filter above has already removed those. This branch used to
                    # `continue`, which dropped EVERY species in `children` --
                    # and species live in `children`, not `speciesList`, because
                    # speciesList is a shape `buildData.ts` invents at build time
                    # (0 of 14,084 family files contain one). So every family the
                    # dedupe touched was emptied: 351,882 species destroyed across
                    # 689 files, including all of Asteraceae and Orchidaceae, in a
                    # commit whose message reported "8,745 copies removed".
                    #
                    # The species drop below is the only one that should ever
                    # happen, and the non-species branch below is what this loop
                    # was actually for: dropping a genus, subfamily or tribe that
                    # removing duplicates has left empty.
                    kept.append(g)
                elif g.get("children") or g.get("speciesList"):
                    kept.append(g)
            node["children"] = kept

        prune(d)
        d["children"] = [g for g in d.get("children") or [] if g.get("children")]
        d["speciesCount"] = count_species(d)
        d["genusCount"] = count_rank(d, "GENUS")
        # Atomic -- see scripts/tree.py save_json. This loop writes hundreds of
        # family documents and a SIGTERM part way through used to leave the
        # first one it had reached truncated.
        save_json(f, d)
        touched += 1
    # The file that KEPT a merged record is not in `drops` -- nothing was removed
    # from it -- so the loop above never reaches it and the sourceIds carried
    # across from the dropped stub would be recomputed on every run and lost
    # every time, which also makes the script non-idempotent. No prune here: this
    # file lost nothing, and pruning would drop empty genera in a file that has
    # nothing to do with this dedupe.
    merged_only = sorted(f for f in merge_touched if f not in drops)
    for f in merged_only:
        d = docs[f]
        d["speciesCount"] = count_species(d)
        d["genusCount"] = count_rank(d, "GENUS")
        save_json(f, d)
    if merged_only:
        touched += len(merged_only)
    # The whole bug in one assertion. The dry run said "species to remove:
    # 8,745" and this line used to print whatever `removed` happened to reach,
    # with nothing comparing the two -- so a prune that dropped every species in
    # a family instead of the eight thousand duplicates reported success. The
    # count of what was planned and the count of what went must agree, and an
    # --apply that disagrees has already written the files, so say so loudly
    # rather than exiting 0.
    print(f"\n  wrote {touched} family files, removed {removed} species copies")
    if removed != planned:
        print(f"  MISMATCH: planned to remove {planned:,} but removed "
              f"{removed:,}. The files are already written; inspect them and "
              f"restore from git before committing.")
        return 1
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        with maintenanceLock.hold_exclusive():
            sys.exit(main())
    else:
        sys.exit(main())