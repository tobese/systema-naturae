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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    meta = K.metadata(args.archive)
    print(f"  {meta.get('title') or os.path.basename(args.archive)}  "
          f"({meta.get('version') or 'no version'}, {meta.get('license') or 'no licence'})")

    taxa, _names, _ = K.load(args.archive)
    by_id = {t["id"]: t for t in taxa}
    cand = [t for t in taxa
            if (t["rank"] or "").lower() in ("species", "subspecies")
            and t["name"] and not t["is_synonym"]]
    print(f"  accepted species/subspecies offered: {len(cand):,}")

    placed = set()

    # The source's kingdom comes from its own rank chain, read off the first
    # taxon that carries one.
    src_kingdom = None
    probe = {t["id"]: t for t in taxa}
    for t in cand[:200]:
        c = K.chain(t, probe)
        if c.get("kingdom"):
            src_kingdom = c["kingdom"]
            break
    # Kingdom is resolved PER TAXON, not once per source. Reading it off the
    # first taxon that has one -- which is what this did -- sent every plant and
    # fungus in a mixed source to animalia, because the first taxon was an
    # animal: Wikispecies offered 244,078 species and refused 192,372 of them,
    # nearly all of them plants and fungi that animalia has no family for. The
    # refusals looked like a coverage problem and were a routing bug. One
    # kingdom per source is only defensible when the source is single-kingdom,
    # which is asserted below rather than assumed.
    KINDS = {}
    for k in ("animalia", "plantae", "fungi", "chromista", "protozoa", "archaea"):
        KINDS[k] = our_families(k, quiet=True)
    DEFAULT_K = (src_kingdom or FALLBACK_KINGDOM).lower()
    if DEFAULT_K not in KINDS:
        DEFAULT_K = "animalia"

    # per kingdom: taxonomy doc, family->[slug, node], and every species id on
    # disk, which is what the held-check arbitrates against
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

    # Most sources carry no kingdom at all -- Wikispecies offers 458,568 species
    # and not one of them has a kingdom in its rank chain, so "read the kingdom
    # off the taxon" degenerates to the animalia fallback and every orchid and
    # puffball gets looked for in Animalia. The family name is the only signal
    # a source reliably has, and it is a good one: we hold 14,203 of them and
    # they are kingdom-specific in practice. So fall back to the family.
    FAM2K = collections.defaultdict(set)
    for k, (_t, fams_k) in KINDS.items():
        for fam in fams_k:
            FAM2K[fam].add(k)

    staged = collections.defaultdict(list)      # (kingdom, slug) -> [(genus, name, auth)]
    held = refused = nonb = 0
    no_family = collections.Counter()
    missed = collections.Counter()
    routed = collections.Counter()
    routed_by_kingdom = routed_by_family = routed_unknown = 0

    for t in cand:
        nm = t["name"]
        p = parsed.get(nm) or {}
        g, s = p.get("genus"), p.get("species")
        if not s:
            parts = [x for x in nm.replace("\u00d7", " ").split()
                     if x.lower() != "x"]
            if len(parts) >= 2:
                g, s = parts[0], parts[1]
        if not g or not s:
            nonb += 1
            continue
        bare = f"{g} \u00d7{s}" if "\u00d7" in nm else f"{g} {s}"
        # Deliberately NOT consulting the canonical index here. It is a snapshot
        # of the tree taken at a point in time, and on ILDIS it is wrong in the
        # expensive direction: it scored 13,347 of 16,371 legume species as
        # already held when only 64 are, so an index-driven run would have
        # staged 3,024 and silently skipped the other 13,283. On Craneflies the
        # same index erred the other way, scoring 15,563 as new when 15,191
        # were held. A snapshot disagrees with the tree it indexes in whichever
        # direction it drifted, so the only arbiter here is merge_family, which
        # reads the family file it is about to write and reports what it really
        # added and what was already present.
        if bare.lower() in placed:
            continue
        placed.add(bare.lower())
        # Held in ANOTHER family. This check has to be against the files, not
        # the canonical index: the index is a snapshot and was wrong in both
        # directions, but removing the held-check entirely was worse than a bad
        # index. Without it this importer wrote a species into whichever family
        # the source assigned even when we already held it elsewhere -- 236
        # copies across 57 file pairs, Kinnaridae and Meenoplidae each holding
        # the other's cixiid relatives, because the source's circumscription
        # differs from ours. Skipping is the right call and matches
        # dedupe_genera_across_families.py, which keeps the copy we already had.
        sid = SF.node_id(SF.PREFIX["SPECIES"], bare, (t.get("authorship") or "").strip() or "")
        ch = K.chain(t, by_id)
        fam = (ch.get("family") or "").lower().strip()
        k = (ch.get("kingdom") or "").strip().lower()
        if k not in KINDS:
            k = ""
            # the family decides. Ambiguous across kingdoms, or unknown to us
            # entirely, falls back to the source's own kingdom.
            owners = FAM2K.get(fam) or set()
            if len(owners) == 1:
                k = next(iter(owners))
                routed_by_family += 1
            else:
                k = DEFAULT_K
                routed_unknown += 1
        else:
            routed_by_kingdom += 1
        routed[k] += 1
        if sid in ON_DISK[k]:
            held += 1
            continue
        fams_k = KINDS[k][1]
        if fam not in fams_k:
            no_family[(k, fam or "(no family)")] += 1
            missed[(k, fam)] += 1
            refused += 1
            continue
        slug = fams_k[fam][0]
        staged[(k, slug)].append((g, bare, (t.get("authorship") or "").strip() or None))

    print("  routed per taxon: " + ", ".join(f"{k} {v:,}" for k, v in routed.most_common()))
    print(f"      kingdom from the taxon: {routed_by_kingdom:,}"
          f"   from the family name: {routed_by_family:,}"
          f"   fell back to {DEFAULT_K}: {routed_unknown:,}")
    # `held` is the already-on-disk count, not a parse failure. Labelling it
    # "unparseable" made WFO's dry run read "staged 226,683 (+148,381
    # unparseable)", which looks like 40% of the dataset failing to parse. It is
    # 148,381 species we already hold. A counter with the wrong name on it is
    # worse than no counter.
    print(f"\n  already held (skipped): {held:,}")
    print(f"  staged:              {sum(len(v) for v in staged.values()):,}")
    print(f"  non-binominal:       {nonb:,}")
    print(f"  new, into a family we hold: {sum(len(v) for v in staged.values()):,}"
          f"  across {len(staged)} families in {len({k for k, _ in staged})} kingdoms")
    print(f"  REFUSED (would need a new family): {refused:,}"
          f"  -- dropped, not placed: no placeholder family, no orphan node")
    print(f"      (these are recorded in the pending-family store; "
          f"see scripts/pendingFamilies.py)")
    for (k, fam), v in no_family.most_common(10):
        print(f"      {v:>6,}  [{k}] {fam}")

    # A refused species is refused because its family is missing. That is a
    # fact about the world, not about this run, so it goes in the pending-family
    # store rather than dying with the counter. That store is the whole reason
    # the misses are recoverable: `pendingFamilies.py report --scaffoldable`
    # later lists the families that have since been imported.
    # Only on --apply. A dry run that records its misses leaves the store
    # describing an import that never happened, and since the rows accumulate
    # species counts there is no way to tell that apart from a real one later.
    if missed and args.apply:
        try:
            import pendingFamilies as PF
        except ImportError:
            PF = None
        if PF:
            recorded = 0
            for (k, fam), n in missed.items():
                if not fam:
                    continue          # no family name to record; nothing to scaffold
                PF.add_family(fam, kingdom=k, species=n, source=f"{SOURCE}:{slug_hint(args.archive)}",
                              reason="offered by source, family not in taxonomy")
                recorded += 1
            print(f"  recorded {recorded} families in the pending store")
        else:
            print("  ! pendingFamilies.py not importable, misses NOT recorded")
    elif missed:
        print(f"  (dry run: {sum(missed.values()):,} refusals across "
              f"{len({f for _, f in missed if f}):} families would be recorded "
              f"in the pending store)")

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
        for g, nm, a in rows:
            genera[g].append((nm, a))
        new_root = {"id": None, "name": None, "rank": "FAMILY", "children": []}
        touched_path = None
        for g, species in genera.items():
            # lineage is the PARENT name at each level: the family on a genus
            # node, the genus on a species node. That is what the 1.45M existing
            # species do. Writing the family onto species, as this did, is
            # redundant -- the species already lives in a file named for that
            # family -- and it stamped 72,270 Wikispecies/ILDIS/FLOW/Moss
            # species with the wrong value. testDataContract only asserts the
            # genus case (>=95%), which is why it never caught the other half.
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
            new_root["children"].append(gnode)
            for nm, a in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm, a or ""),
                      "name": nm, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
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
        m = SF.merge_family(doc, new_root)
        added_total += m.get("species_added", 0)
        dedup_total += m.get("species_deduped", 0)
        print(f"    {slug:28s} staged {len(rows):>4,}  added {m.get('species_added', 0):>4,}  "
              f"already present {m.get('species_deduped', 0):>4,}")
        # Only write what actually gained something. Writing unconditionally
        # reformats every family that was merely scanned -- json.dump re-emits
        # each array one item per line -- and the first run rewrote 75 family
        # files to add 373 species to three of them.
        if args.apply and not m.get("species_added"):
            print(f"      unchanged, not rewritten")
        elif args.apply:
            with open(touched_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            # taxonomy.json's speciesCount is what the Coverage modal reads
            n = sum(len(g.get("children") or []) for g in doc.get("children") or [])
            for g in doc.get("children") or []:
                st = [g]
                while st:
                    nd = st.pop()
                    n += len(nd.get("speciesList") or [])
                    st.extend(nd.get("children") or [])
            fam = fams_k[[n for n, v in fams_k.items() if v[0] == slug][0]][1]
            if fam.get("speciesCount") != n:
                fam["speciesCount"] = n
            print(f"      {touched_path}  speciesCount -> {n}")

    print(f"\n  species added: {added_total:,}   already present: {dedup_total:,}")
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