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

Idempotent either way.

    python3 scripts/dedupeSpeciesAcrossFamilies.py
    python3 scripts/dedupeSpeciesAcrossFamilies.py --apply
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import (  # noqa: E402
    KINGDOMS,
    count_rank,
    count_species,
    iter_family_files,
    iter_species_with_parent,
)

IMPORTED = {"checklistbank", "catalogue of life"}


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
    def score(fp, auth=None, key=None):
        n = fp[1]
        nm = (n.get("name") or "").strip()
        au = (n.get("authorship") or "").strip()
        conforming = not (au and len(nm) > len(au) + 2 and nm.endswith(au))
        richness = sum(1 for k in ("description", "commonName", "continents",
                                  "reference", "yearPublished") if n.get(k))
        if authority_family and auth == "gbif":
            want = authority_family.get(key)
            if want:
                # Normalised on both sides: our slug is `anobiidae` from the
                # directory name, GBIF answers `Anobiidae`.
                want_n = want.lower().replace(" ", "").replace("-", "")
                in_family = file_family.get(fp[0], "") == want_n
                return (in_family, conforming, richness, fp[0])
        return (False, conforming, richness, fp[0])

    ranks = collections.Counter()
    renamed = 0
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



    drops = collections.defaultdict(set)      # file -> set(species id)
    keep_report = collections.Counter()
    for kingdom, groups in auth_groups.items():
        for auth, key, places in groups:
            winner = max(places, key=lambda fp: score(fp, auth, key))
            for fp in places:
                # `fp is winner`, NOT `(f, n) is winner`. Unpacking and
                # re-packing builds a new tuple, so the identity test was False
                # for every entry including the winner -- which meant every copy
                # of every authority group was marked for deletion, and the
                # winner survived only because the safety pass below rescued one
                # copy per group. That rescue scored without the path tiebreak,
                # so `max` returned whichever family the sorted glob reached
                # first and the survivor was decided by alphabet: 1,648 of the
                # 4,480 removals kept the copy in a family GBIF contradicts.
                if fp is winner:
                    continue
                drops[fp[0]].add(fp[1]["id"])
            keep_report[f"collapsed on {auth} id"] += 1

    for sid, places in dupes.items():
        files = {f for f, _ in places}
        imported = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") in IMPORTED]
        native = [(f, s) for f, s in places if (s.get("sourcedFrom") or "") not in IMPORTED]
        if native and imported:
            # keep the copy we already had; drop every import-written one
            for f, _s in imported:
                drops[f].add(sid)
            keep_report["dropped an imported copy, kept the existing one"] += 1
            continue
        if len(imported) > 1:
            # both from imports: the bigger family keeps it
            sizes = {f: count_species(docs[f]) for f, _s in imported}
            win = max(sizes, key=lambda f: sizes[f])
            for f, _s in imported:
                if f != win:
                    drops[f].add(sid)
            keep_report["both imported; the larger family kept it"] += 1
            continue
        keep_report["left alone (no imported copy)"] += 1

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
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        touched += 1
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
    sys.exit(main())