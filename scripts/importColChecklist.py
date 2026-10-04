#!/usr/bin/env python3
"""Import a ChecklistBank per-checklist export into family files we already hold.

Scaffolding is deliberately not implemented. Both datasets this was written for
turn out to land entirely inside families the tree already has -- Craneflies adds
376 species to Limoniidae and 2 to Tipulidae, ReptileDB adds 1 to Scincidae --
so the only operation needed is part A of `importColStage2.py`: hand
`merge_family` a synthetic genus/species root and let it add what is missing.
Rather than implement placement and guess it untested, anything that would need a
new family is counted and refused, and the run says so.

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


def our_families(kingdom=None):
    """lower-cased family name -> (appSlug, node)"""
    path, k = taxonomy_input(kingdom)
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
    tax, fams = our_families(src_kingdom)
    tax_path, _k = taxonomy_input(src_kingdom)
    parsed = taxamatch.parse_names(sorted({t["name"] for t in cand}))

    staged = collections.defaultdict(list)      # appSlug -> [(genus, name, auth)]
    held = refused = nonb = 0
    no_family = collections.Counter()

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
        ch = K.chain(t, by_id)
        fam = (ch.get("family") or "").lower().strip()
        if fam not in fams:
            no_family[fam or "(no family)"] += 1
            refused += 1
            continue
        slug = fams[fam][0]
        staged[slug].append((g, bare, (t.get("authorship") or "").strip() or None))

    print(f"  source kingdom: {src_kingdom or '(none found; using ' + FALLBACK_KINGDOM + ')'}")
    print(f"\n  staged:              {sum(len(v) for v in staged.values()):,} "
          f"(+{held:,} unparseable)")
    print(f"  non-binominal:       {nonb:,}")
    print(f"  new, into a family we hold: {sum(len(v) for v in staged.values()):,}"
          f"  across {len(staged)} families")
    print(f"  REFUSED (would need a new family): {refused:,}")
    for k, v in no_family.most_common(10):
        print(f"      {v:>6,}  {k}")

    if not staged:
        print("\n  nothing to do")
        return 0

    print()
    added_total = dedup_total = 0
    for slug, rows in sorted(staged.items()):
        genera = collections.defaultdict(list)
        for g, nm, a in rows:
            genera[g].append((nm, a))
        new_root = {"id": None, "name": None, "rank": "FAMILY", "children": []}
        touched_path = None
        for g, species in genera.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE}
            new_root["children"].append(gnode)
            for nm, a in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm, a or ""),
                      "name": nm, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE}
                if a:
                    sp["authorship"] = a
                gnode["children"].append(sp)

        # find the file for this slug
        import glob
        hits = [f for f in glob.glob(f"taxonomy/*/**/{slug}/src/data/{slug}.json",
                                     recursive=True)
                if "node_modules" not in f]
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
            fam = fams[[k for k, v in fams.items() if v[0] == slug][0]][1]
            if fam.get("speciesCount") != n:
                fam["speciesCount"] = n
            print(f"      {touched_path}  speciesCount -> {n}")

    print(f"\n  species added: {added_total:,}   already present: {dedup_total:,}")
    if args.apply:
        with open(tax_path, "w", encoding="utf-8") as fh:
            json.dump(tax, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"  wrote {tax_path}")
    else:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())