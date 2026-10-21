#!/usr/bin/env python3
"""Import a ChecklistBank per-checklist export into family files we already hold.

Scaffolding is deliberately not implemented. Both datasets this was written for
turn out to land entirely inside families the tree already has -- Craneflies adds
376 species to Limoniidae and 2 to Tipulidae, ReptileDB adds 1 to Scincidae --
so the only operation needed is part A of `importColStage2.py`: hand
`merge_family` a synthetic genus/species root and let it add what is missing.
Rather than implement placement and guess it untested, anything that would need a
new family is counted and refused, and the run says so.

**A refused species is dropped, not placed.** It gets no family of its own, no
`Incertae sedis` placeholder, and no node anywhere in the tree. That is a
deliberate difference from `importColStage2.py`, whose part C does exactly that:
COL offers enough family-less species (23,536 of them in Animalia) that a
placeholder is the least-wrong answer, and an explicitly unplaced family asserts
only that we could not place it. Here the counts do not justify it -- 21 species
in FLOW, 207 in Moss TROPICOS, 4 in ReptileDB -- so a placeholder family would be
a directory and a colour theme per handful of names, and the families are real
and findable in the source. They stay out until someone decides to scaffold them,
which is a taxonomy decision rather than a data one.

The overlap is the headline, and it was measured against the tree rather than
against the canonical index, which is a snapshot taken before the Stage 2
import and reports 15,563 "new" Cranefly species that are in fact already on disk:

    Craneflies   16,061 species -> 15,683 already held, 378 new
    ReptileDB    15,612 species -> 15,611 already held,   1 new

Nothing here filters on `status`: in this export shape Name.tsv carries no
usable status (all 34,366 ReptileDB rows have it empty) and the accepted/synonym
split lives in Synonym.tsv, which `colChecklist.load()` already applies.

Ids are minted with `importSpeciesFile.node_id`, so a species added here gets
the same id the other importers would give it and cannot collide with one added
by COL.

    python3 scripts/importColChecklist.py <archive.zip>            # dry run
    python3 scripts/importColChecklist.py <archive.zip> --apply
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colChecklist as K  # noqa: E402
import importSpeciesFile as SF  # noqa: E402
import taxamatch  # noqa: E402

KINGDOM_CONFIG = "portal/data/kingdom-config.json"
# Fallback only. A source's own kingdom comes from its rank chain, because
# portal/data/taxonomy.json is animalia alone -- looking for Fabaceae in it
# refuses all 3,024 of ILDIS' legume species as needing a new family when the
# tree already holds Fabaceae with 24,496 species.
FALLBACK_KINGDOM = "animalia"
SOURCE = "checklistbank"
FORMS = ("{g} \u00d7{s}", "{g} {s}", "{g} \u00d7{s}", "{g} \u00d7 {s}")


def slug_hint(archive):
    """A stable short identifier for the source, for the pending store.

    The ChecklistBank dataset key when the container carries one, else the
    archive filename. Two runs of the same archive must produce the same string
    or the pending store accumulates duplicate rows for one source.
    """
    try:
        m = K.metadata(archive)
    except Exception:
        m = {}
    key = m.get("key") or m.get("alias") or m.get("title")
    if not key:
        key = os.path.basename(archive).rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "-", str(key).lower()).strip("-")[:40]


def taxonomy_input(kingdom):
    """Path to a kingdom's taxonomy file, from kingdom-config.json.

    Not derived from the kingdom's name: Plantae's input is
    taxonomy-plantae-snippet.json and Animalia's is plain taxonomy.json.
    """
    cfg = json.load(open(KINGDOM_CONFIG, encoding="utf-8"))["kingdoms"]
    k = (kingdom or FALLBACK_KINGDOM).lower()
    if k not in cfg:
        sys.exit(f"FATAL: kingdom {k!r} is not in kingdom-config.json. "
                 f"Declared: {', '.join(sorted(cfg))}")
    return os.path.join("portal", cfg[k]["input"]), k


def our_families(kingdom=None, quiet=False):
    """lower-cased family name -> (appSlug, node)"""
    path, k = taxonomy_input(kingdom)
    if not quiet:
        print(f"  taxonomy input: {path}  (kingdom {k})")
    tax = json.load(open(path, encoding="utf-8"))
    out = {}

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug"):
            out[(n.get("name") or n["appSlug"]).lower()] = (n["appSlug"], n)
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    return tax, out


class RoutedSpecies:
    """Everything route_species() decided, shared by every caller that
    reads a ColDP/DwC-A archive -- the direct-write importer below and
    transformColChecklist.py's split-pipeline transform step. Neither
    re-derives kingdom routing, family matching, or refusal detection;
    both get it from here, so the two paths cannot quietly disagree
    about where a species belongs."""

    def __init__(self):
        self.meta = {}
        self.source_key = SOURCE
        self.staged = collections.defaultdict(list)  # (kingdom, slug) -> [(genus, bare, authorship, source_id, family_name)]
        self.missed = collections.Counter()           # (kingdom, family) -> count
        self.fam_source_ids = collections.defaultdict(set)
        self.cand_count = 0
        self.held = self.refused = self.nonb = self.unresolved = 0
        self.no_family = collections.Counter()
        self.routed = collections.Counter()
        self.routed_by_kingdom = self.routed_by_family = self.routed_unknown = 0
        self.src_kingdom = None
        self.default_k = ""
        self.kinds = {}


def route_species(archive, kingdom_override="") -> RoutedSpecies:
    """Read `archive`, resolve each accepted species/subspecies to a
    (kingdom, family slug) in our taxonomy or a refusal, same logic for
    every caller. Pure routing -- no file writes, no pendingFamilies
    recording (callers decide when a decision is final enough for that:
    importColChecklist.py's main() only records on --apply, and
    transformColChecklist.py follows the same rule)."""
    r = RoutedSpecies()
    r.meta = K.metadata(archive)
    print(f"  {r.meta.get('title') or os.path.basename(archive)}  "
          f"({r.meta.get('version') or 'no version'}, {r.meta.get('license') or 'no licence'})")

    # ChecklistBank's own taxon ids are only unique WITHIN one dataset --
    # small sequential integers that two unrelated datasets routinely
    # reuse. A bare "checklistbank" sourceIds key let importwrite's
    # cross-identity matching (by (source, id) pair, see services/
    # importwrite/identity.go) treat two different species from different
    # datasets as the same one whenever their dataset-local ids collided --
    # found 2026-10-19 when a WTaxa (1039) id collided with an unrelated
    # species already in curculionidae, silently absorbing the new one
    # into the old one's node instead of adding it. Scoping the key by
    # dataset closes that; it only affects the sourceIds identity key, not
    # the sourcedFrom display field, so it does not change which species we
    # already consider "held" (that check hashes name+authorship, not this).
    #
    # r.meta (the archive's own metadata.yaml/eml.xml, when it has one) is
    # NOT used for this -- WTaxa's own archive carries none, metadata() just
    # returns {}. The archive's containing directory is manifest.json's own
    # key for this source (every "archive" entry there is "archives/<key>",
    # confirmed across the whole manifest), on disk whether or not the
    # archive embeds metadata, so it's the one dataset identifier this
    # function can always derive.
    dataset_key = os.path.basename(os.path.dirname(os.path.abspath(archive)))
    r.source_key = dataset_key or SOURCE

    taxa, _names, _ = K.load(archive)
    by_id = {t["id"]: t for t in taxa}
    cand = [t for t in taxa
            if (t["rank"] or "").lower() in ("species", "subspecies")
            and t["name"] and not t["is_synonym"]]
    r.cand_count = len(cand)
    print(f"  accepted species/subspecies offered: {len(cand):,}")

    placed = set()

    src_kingdom = None
    probe = {t["id"]: t for t in taxa}
    for t in cand[:200]:
        c = K.chain(t, probe)
        if c.get("kingdom"):
            src_kingdom = c["kingdom"]
            break
    r.src_kingdom = src_kingdom

    KINDS = {}
    for k in ("animalia", "plantae", "fungi", "chromista", "protozoa", "archaea"):
        KINDS[k] = our_families(k, quiet=True)
    r.kinds = KINDS

    DEFAULT_K = (kingdom_override or src_kingdom or "").lower()
    if DEFAULT_K and DEFAULT_K not in KINDS:
        sys.exit(f"FATAL: --kingdom {DEFAULT_K!r} is not one of "
                  f"{', '.join(sorted(KINDS))}")
    r.default_k = DEFAULT_K

    import glob as _glob
    ON_DISK = {}
    for k in KINDS:
        ids = set()
        for f in _glob.glob(f"taxonomy/{k}/**/src/data/*.json", recursive=True):
            try:
                d = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            st = list(d.get("children") or [])
            while st:
                nd = st.pop()
                if nd.get("rank") == "SPECIES" and nd.get("id"):
                    ids.add(nd["id"])
                st.extend(nd.get("children") or [])
        ON_DISK[k] = ids
        print(f"  {k:10s} families {len(KINDS[k][1]):>7,}   species on disk {len(ids):>9,}")
    print(f"  source kingdom (first taxon with one): {src_kingdom or '(none)'}")

    parsed = taxamatch.parse_names(sorted({t["name"] for t in cand}))

    FAM2K = collections.defaultdict(set)
    for k, (_t, fams_k) in KINDS.items():
        for fam in fams_k:
            FAM2K[fam].add(k)

    for t in cand:
        nm = t["name"]
        g, s = taxamatch.bare_binomial(nm, parsed)
        if not g or not s:
            r.nonb += 1
            continue
        bare = taxamatch.bare_name(nm, parsed)
        if bare.lower() in placed:
            continue
        placed.add(bare.lower())
        sid = SF.node_id(SF.PREFIX["SPECIES"], bare, (t.get("authorship") or "").strip() or "")
        ch = K.chain(t, by_id)
        fam = (ch.get("family") or "").lower().strip()
        k = (ch.get("kingdom") or "").strip().lower()
        if k not in KINDS:
            k = ""
            owners = FAM2K.get(fam) or set()
            if len(owners) == 1:
                k = next(iter(owners))
                r.routed_by_family += 1
            elif DEFAULT_K:
                k = DEFAULT_K
                r.routed_unknown += 1
            else:
                r.unresolved += 1
                continue
        else:
            r.routed_by_kingdom += 1
        r.routed[k] += 1
        if sid in ON_DISK[k]:
            r.held += 1
            continue
        fams_k = KINDS[k][1]
        if fam not in fams_k:
            r.no_family[(k, fam or "(no family)")] += 1
            r.missed[(k, fam)] += 1
            r.refused += 1
            continue
        slug = fams_k[fam][0]
        r.staged[(k, slug)].append((g, bare,
                                    (t.get("authorship") or "").strip() or None,
                                    t.get("id"), fam))
        fid = ch.get("family_id")
        if fid:
            r.fam_source_ids[(k, slug)].add(fid)

    print("  routed per taxon: " + ", ".join(f"{k} {v:,}" for k, v in r.routed.most_common()))
    print(f"      kingdom from the taxon: {r.routed_by_kingdom:,}"
          f"   from the family name: {r.routed_by_family:,}"
          f"   fell back to {DEFAULT_K or '(none given)'}: {r.routed_unknown:,}")
    if r.unresolved:
        print(f"  UNRESOLVED KINGDOM: {r.unresolved:,} -- no --kingdom given, "
              f"the source carries none, and the family name is unknown or "
              f"ambiguous across kingdoms. Not attributed to one and not "
              f"refused under a specific kingdom either; re-run with "
              f"--kingdom <name> if you know what this source is.")
    print(f"\n  already held (skipped): {r.held:,}")
    print(f"  staged:              {sum(len(v) for v in r.staged.values()):,}")
    print(f"  non-binominal:       {r.nonb:,}")
    print(f"  new, into a family we hold: {sum(len(v) for v in r.staged.values()):,}"
          f"  across {len(r.staged)} families in {len({k for k, _ in r.staged})} kingdoms")
    print(f"  REFUSED (would need a new family): {r.refused:,}"
          f"  -- dropped, not placed: no placeholder family, no orphan node")
    print(f"      (these are recorded in the pending-family store; "
          f"see scripts/pendingFamilies.py)")
    for (k, fam), v in r.no_family.most_common(10):
        print(f"      {v:>6,}  [{k}] {fam}")
    return r


def record_misses(r: RoutedSpecies, archive, apply_: bool):
    """Record refusals into the pending-family store -- shared tail for
    both main() and transformColChecklist.py, same rule: only on a real
    apply, never on a dry run (see route_species's docstring)."""
    if r.missed and apply_:
        try:
            import pendingFamilies as PF
        except ImportError:
            PF = None
        if PF:
            recorded = PF.add_families(
                [(fam, k, n) for (k, fam), n in r.missed.items() if fam],
                source=f"{SOURCE}:{slug_hint(archive)}",
                reason="offered by source, family not in taxonomy",
                archive=archive)
            print(f"  recorded {recorded} families in the pending store")
        else:
            print("  ! pendingFamilies.py not importable, misses NOT recorded")
    elif r.missed:
        print(f"  (dry run: {sum(r.missed.values()):,} refusals across "
              f"{len({f for _, f in r.missed if f}):} families would be recorded "
              f"in the pending store)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", default="",
                     help="override kingdom inference entirely for sources "
                          "that carry no kingdom in their own rank chain and "
                          "whose family names don't resolve uniquely (e.g. "
                          "LCVP -- an all-plant database with no kingdom "
                          "field at all -- used to default silently to "
                          "animalia for exactly this reason: a hardcoded "
                          "constant written for a different, narrower bug, "
                          "reused here with no actual justification). "
                          "Pass --kingdom plantae when you know the source.")
    args = ap.parse_args()

    r = route_species(args.archive, kingdom_override=args.kingdom)
    meta = r.meta
    record_misses(r, args.archive, args.apply)
    staged = r.staged
    KINDS = r.kinds

    if not staged:
        print("\n  nothing to do")
        return 0

    print()
    added_total = dedup_total = 0
    files = None
    for (kind, slug), rows in sorted(staged.items()):
        _tax_k, fams_k = KINDS[kind]
        # the family name, needed by the genera loop below for genus lineage
        fname = next((n for n, v in fams_k.items() if v[0] == slug), slug)
        genera = collections.defaultdict(list)
        for g, nm, a, sid, _fam in rows:
            genera[g].append((nm, a, sid))
        new_root = {"id": None, "name": None, "rank": "FAMILY", "children": []}
        touched_path = None
        for g, species in genera.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
            new_root["children"].append(gnode)
            for nm, a, sid in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm, a or ""),
                      "name": nm, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
                if sid:
                    sp["sourceIds"] = {r.source_key: sid}
                gnode["children"].append(sp)
        # One index, built once. A recursive glob per family means a full walk
        # of a 14,085-file tree per family: 34 families took 7 minutes, which
        # puts Wikispecies' 736 at over two hours for what is a dict lookup.
        if files is None:
            import glob
            files = {}
            for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
                if "node_modules" in f:
                    continue
                slug_ = os.path.basename(f)[:-5]
                files.setdefault(slug_, []).append(f)
            print(f"  indexed {sum(len(v) for v in files.values()):,} family "
                  f"data files across {len(files):,} slugs")
        hits = files.get(slug, [])
        if len(hits) != 1:
            print(f"  ! {slug}: {len(hits)} files found, skipping")
            continue
        touched_path = hits[0]
        doc = json.load(open(touched_path, encoding="utf-8"))
        new_root["id"] = doc.get("id")
        new_root["name"] = doc.get("name")
        m = SF.merge_family(
            doc, new_root,
            kingdom=touched_path.split("taxonomy/")[1].split("/")[0],
            family_slug=slug)
        added_total += m.get("species_added", 0)
        dedup_total += m.get("species_deduped", 0)

        # Stamp this archive's own family-rank id onto the family's own root
        # node, the same way species already carry sourceIds (colChecklist.
        # chain() now surfaces it). More than one id feeding one slug means
        # the archive itself disagrees with our tree about what "this family"
        # is -- the Actinocyclidae/Hemidiscaceae class of bug, visible here
        # before a single species crosses into the file.
        fids = r.fam_source_ids.get((kind, slug)) or set()
        fam_id_changed = False
        if len(fids) > 1:
            print(f"    ! {slug}: archive feeds {len(fids)} distinct family "
                  f"ids into this one slug -- possible homonym collision: "
                  f"{sorted(fids)[:5]}")
        elif len(fids) == 1:
            fid = next(iter(fids))
            doc_ids = doc.setdefault("sourceIds", {})
            prior = doc_ids.get(r.source_key)
            if prior != fid:
                if prior:
                    print(f"    ! {slug}: {r.source_key} family id changed "
                          f"{prior} -> {fid}")
                doc_ids[r.source_key] = fid
                fam_id_changed = True

        print(f"    {slug:28s} staged {len(rows):>4,}  added {m.get('species_added', 0):>4,}  "
              f"already present {m.get('species_deduped', 0):>4,}")
        if m.get("authority_conflicts"):
            print(f"    ! {m['authority_conflicts']} species share an "
                  f"authority id with a different family already: "
                  f"{m['authority_conflict_examples'][0]}")
        # Only write what actually gained something. Writing unconditionally
        # reformats every family that was merely scanned -- json.dump re-emits
        # each array one item per line -- and the first run rewrote 75 family
        # files to add 373 species to three of them.
        if args.apply and not m.get("species_added") and not fam_id_changed:
            print(f"      unchanged, not rewritten")
        elif args.apply:
            with open(touched_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            # taxonomy.json's speciesCount is what the Coverage modal reads.
            # Use the same iterator merge_family uses rather than counting here:
            # a hand-rolled count of top-level children counts SUBFAMILY nodes
            # as if they were species, so Aphididae -- whose top-level children
            # are subfamilies -- was written as 193 when it holds 5,873, and 61
            # animalia families came out understating by 103,385 species.
            # Three copies of this counter already existed and disagreed; the
            # fix is to have none.
            n = sum(1 for _ in SF.iter_species(doc))
            fam = fams_k[[n for n, v in fams_k.items() if v[0] == slug][0]][1]
            if fam.get("speciesCount") != n:
                fam["speciesCount"] = n
            print(f"      {touched_path}  speciesCount -> {n}")

    print(f"\n  species added: {added_total:,}   already present: {dedup_total:,}")

    # A durable record of what this run did, so the post-import gate reads
    # numbers rather than scraped stdout. Every serious defect in Oct 2026 was a
    # plausible number rather than an error, and the number that would have
    # caught two of them is the refusal rate: WFO refused 0.26% and ITIS 5.5%,
    # both healthy, while a run refusing 60% looks identical at exit 0. Written
    # on --apply only, because a dry run changed nothing.
    if args.apply:
        import datetime as _dt
        row = {
            "at": _dt.datetime.now().isoformat(timespec="seconds"),
            "source": SOURCE,
            "archive": os.path.basename(args.archive),
            "archivePath": args.archive,
            "slugHint": slug_hint(args.archive),
            "title": meta.get("title") or "",
            "offered": r.cand_count,
            "alreadyHeld": r.held,
            "nonBinominal": r.nonb,
            "staged": sum(len(v) for v in staged.values()),
            "refused": r.refused,
            "refusalRate": round(r.refused / max(1, r.cand_count), 4),
            "added": added_total,
            "deduped": dedup_total,
            "families": len(staged),
            "kingdoms": sorted({k for k, _ in staged}),
            "missedFamilies": len({f for _kk, f in r.missed if f}),
        }
        log = os.path.join("data", "import-log.jsonl")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  recorded {log}")

    if args.apply:
        for kind in sorted({k for k, _ in staged}):
            _tax_k, _ = KINDS[kind]
            tp, _kk = taxonomy_input(kind)
            with open(tp, "w", encoding="utf-8") as fh:
                json.dump(_tax_k, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            print(f"  wrote {tp}")
    else:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())