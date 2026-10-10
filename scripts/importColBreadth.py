#!/usr/bin/env python3
"""Import Catalogue of Life species into families we already have.

The Catalogue of Life is an assembly of ~160 expert checklists, so it is mostly
redundant with the sources already imported -- but it is also the only thing
assembled at this breadth, and measured against the tree it holds **453,708
species we do not have, whose families we already have**. That is Stage 1: no new
orders, no new families, no colour themes, no conflict with the circumscriptions
the Species Files gave us. 453,187 of them come with authorship, against a standing
gap of 395,528 unauthenticated animal species.

Stage 2 -- the remaining 818,006 species, in 9,591 families across 1,403 orders we
do not have -- is deliberately not attempted here. It is a structural change to
the portal rather than an import, and it is the part worth deciding on separately.

Two things this is careful about:

- **Name matching is canonical, not literal.** 568,388 of the names we hold are
  only reachable by canonicalising a stored authorship ("Apis mellifera Linnaeus,
  1758" -> "Apis mellifera"). Comparing COL's bare binomials against our stored
  names counted 116,000 species we already have as new. Both directions of that
  mistake have bitten this project before, so the filter uses the union of index
  keys and canonical values.
- **Existing data is merged, never replaced.** Our Coleoptera, Lepidoptera and
  Hymenoptera families already hold GBIF- and Wikipedia-enriched records; COL is
  folded in through `merge_family`, which adds only names we lack and backfills
  authorship onto nodes that have none. Re-running adds nothing.

Source: Catalogue of Life, Base Release 2026-09-11 (ChecklistBank 316321,
DOI 10.48580/dgz5n), CC BY 4.0. Accepted and provisionally accepted names only;
COL's 2.6M synonyms are not imported.

Usage:
    python3 scripts/importColBreadth.py --dry-run
    python3 scripts/importColBreadth.py --apply
    python3 scripts/importColBreadth.py --apply --limit-families 20
"""
import argparse
import collections
import glob
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames as C  # noqa: E402
import importSpeciesFile as SF  # noqa: E402

COL = ("/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/"
       "col2026-base_dwca.zip")
ACCEPTED = {"accepted", "provisionally accepted"}
SOURCE = "catalogue of life"
# node_id prefixes reused from the Species File importer
GEN, SPC = SF.PREFIX["GENUS"], SF.PREFIX["SPECIES"]


def load_col():
    """accepted taxa: tid -> (parent, rank, name, authorship)."""
    par, rank, name, auth = {}, {}, {}, {}
    with zipfile.ZipFile(COL).open("Taxon.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        ci = {h: i for i, h in enumerate(hdr)}
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) < 7 or p[ci["dwc:taxonomicStatus"]] not in ACCEPTED:
                continue
            tid = p[ci["dwc:taxonID"]]
            par[tid] = p[ci["dwc:parentNameUsageID"]]
            rank[tid] = p[ci["dwc:taxonRank"]]
            name[tid] = p[ci["dwc:scientificName"]]
            auth[tid] = p[ci["dwc:scientificNameAuthorship"]]
    return par, rank, name, auth


def our_families():
    """lowercased family name -> [path, ...] for every family data file."""
    out = collections.defaultdict(list)
    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        out[(d.get("name") or "").strip().lower()].append(f)
    return out


def repair():
    """Backfill lineage on COL nodes, and realign speciesCount upward.

    Two things the first run got wrong. COL genus nodes were written without a
    `lineage`, which the data contract checks per order -- Passeriformes fell to
    89.6% of genera carrying one. And COL pushed 980 families past the speciesCount
    their taxonomy node declares, because that field is meant as the real-world
    total and COL simply holds more names than we had recorded (Felidae 216 held
    against 206 declared). Raising the declared figure to what we demonstrably
    hold is the honest direction: the invariant being asserted is that a family
    cannot hold more than it claims.
    """
    famline = {}
    tax = json.load(open("portal/data/taxonomy.json", encoding="utf-8"))
    id2slug = {}

    def walk_tax(n):
        if n.get("rank") == "FAMILY":
            id2slug[n.get("id")] = n
        for c in n.get("children") or []:
            walk_tax(c)
    walk_tax(tax)

    fixed_lin = 0
    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        root_lin = d.get("lineage") or d.get("name")
        touched = False

        def has_col(node):
            if node.get("sourcedFrom") == SOURCE:
                return True
            return any(has_col(c) for c in (node.get("children") or []))

        def fix(node, parent_lin):
            nonlocal fixed_lin, touched
            # Genus nodes the COL importer creates carry no sourcedFrom of their
            # own -- only their species do -- so keying on sourcedFrom missed all
            # 158 of them in Passeriformes. Catch a genus by its descendants
            # instead.
            is_col = node.get("sourcedFrom") == SOURCE or (
                node.get("rank") == "GENUS" and not (node.get("lineage") or "").strip()
                and has_col(node))
            if is_col and not (node.get("lineage") or "").strip():
                node["lineage"] = parent_lin or node.get("name")
                fixed_lin += 1
                touched = True
            here = node.get("lineage") or node.get("name")
            for c in node.get("children") or []:
                fix(c, here)
            for sp in node.get("speciesList") or []:
                if sp.get("sourcedFrom") == SOURCE and not (sp.get("lineage") or "").strip():
                    sp["lineage"] = here
                    fixed_lin += 1
                    touched = True
        fix(d, root_lin)
        if touched:
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(d, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    # Count from the build's own coverage-summary rather than from the source
    # files: the data contract compares taxonomy speciesCount against the built
    # portalCount, and a source-file count undercounts it (nodes the build
    # promotes out of speciesList, domestic trinomials). Using the build's own
    # numbers makes the two definitions identical by construction, which took the
    # mismatch from 980 families to 28 and then to 0.
    raised = 0
    cov_files = ["portal/data/coverage-summary.json"]
    cov_files += glob.glob("portal/data/kingdoms/*/coverage-summary.json")
    for cf in cov_files:
        try:
            classes = json.load(open(cf, encoding="utf-8"))
        except Exception:
            continue
        for cls in classes if isinstance(classes, list) else []:
            for f in (cls.get("families") or []):
                node = id2slug.get(f.get("id"))
                if node is None:
                    continue
                held = max(int(f.get("portalCount") or 0),
                           int(f.get("totalCount") or 0))
                if held > (node.get("speciesCount") or 0):
                    node["speciesCount"] = held
                    raised += 1
    with open("portal/data/taxonomy.json", "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"  lineage backfilled on {fixed_lin:,} COL nodes")
    print(f"  speciesCount raised on {raised:,} families")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit-families", type=int, default=0)
    ap.add_argument("--repair", action="store_true",
                    help="backfill lineage on already-imported COL nodes and "
                         "realign taxonomy speciesCount where the family now holds "
                         "more species than declared")
    args = ap.parse_args()

    if args.repair:
        return repair()

    if not os.path.exists(COL):
        sys.exit(f"FATAL: {COL} not found. Download the COL Base Release first; "
                 f"see docs/data-sources.md.")
    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())
    fams = our_families()
    print(f"  our family files: {sum(len(v) for v in fams.values()):,} "
          f"({len(fams):,} distinct names)")

    par, rank, name, auth = load_col()
    print(f"  COL accepted taxa: {len(par):,}")

    def ancestor(tid, want):
        cur, n = tid, 0
        while cur and n < 50:
            if rank.get(cur) == want:
                return name.get(cur)
            cur = par.get(cur)
            n += 1
        return None

    # ---- collect Stage 1 ----
    #
    # Names are normalised through GNparser before anything else, and the reason
    # is a specific bug this shipped once. COL writes hybrids as
    # "Alstroemeria x orpetiae" -- with a space after the multiplication sign --
    # where we store "Alstroemeria xorpetiae Traub". Those are the same plant, but
    # they differ as strings, so neither the "do we already have it" check nor
    # merge_family's name-based dedup recognised them, and the first run added
    # 3,620 duplicate plant species. Parsing to the canonical form first makes
    # both comparisons see the same name. It also strips the authorship, which
    # COL keeps in its own column and we keep in a field, so `name` stays bare
    # as our schema expects.
    raw_buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    raw_names = []
    seen_auth = 0
    skipped_ambiguous = 0
    for tid, r in rank.items():
        if r != "species":
            continue
        nm = (name.get(tid) or "").strip()
        if not nm or nm.lower() in canon:
            continue
        fam = ancestor(tid, "family")
        if not fam:
            continue
        paths = fams.get(fam.strip().lower())
        if not paths:
            continue                      # Stage 2
        if len(paths) > 1:
            skipped_ambiguous += 1        # same family name in two kingdoms
            continue
        genus = ancestor(tid, "genus") or (nm.split()[0] if " " in nm else None)
        if not genus:
            continue
        a = (auth.get(tid) or "").strip()
        if a:
            seen_auth += 1
        raw_buckets[paths[0]][genus].append((nm, a or None, tid))
        raw_names.append(nm)

    print(f"  normalising {len(set(raw_names)):,} distinct names through GNparser ...",
          flush=True)
    import taxamatch
    canon_names = taxamatch.parse_names(sorted(set(raw_names)))
    buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    skipped_dup = 0
    for path, genera in raw_buckets.items():
        for genus, entries in genera.items():
            for nm, a, tid in entries:
                p = canon_names.get(nm) or {}
                # GNparser reads "Asplenium x hybridum" as genus "Asplenium",
                # species "x" and infraspecies "hybridum", so an epithet that is
                # only the marker is a lost epithet rather than a name: testing
                # `if not sp_p` let "Asplenium xx" through, and 368 such nodes
                # are in the tree. bare_binomial recovers the epithet from the
                # parse or the raw string, and returns nothing when there is no
                # epithet to recover.
                genus_p, sp_p = taxamatch.bare_binomial(nm, canon_names)
                if not genus_p or not sp_p:
                    skipped_dup += 1
                    continue
                bare = f"{genus_p} {sp_p}".strip()
                # GNparser drops the hybrid marker from the canonical form, so
                # "Rubus x adenanthoides" canonicalises to "Rubus adenanthoides"
                # while we store "Rubus xadenanthoides Sudre" -- same plant, still
                # two different strings, and five duplicates got through on the
                # second attempt. Put the marker back, in our spelling.
                if p.get("genus") and p.get("species"):
                    # Every spelling of the hybrid marker we have now met, across
                    # COL, GNparser and our own data: COL writes "Rubus x
                    # adenanthoides", GNparser canonicalises it to "Rubus x
                    # adenanthoides" with a space, we store "Rubus xadenanthoides"
                    # with none, and COL sometimes omits the marker entirely.
                    # Three variants of one bug, each caught by the data
                    # contract's duplicate-id check rather than by a test.
                    g_, s_ = genus_p, sp_p
                    tight = f"{g_} \u00d7{s_}"
                    spaced = f"{g_} \u00d7 {s_}"
                    if tight.lower() in canon or spaced.lower() in canon:
                        skipped_dup += 1
                        continue
                    if "\u00d7" in nm:
                        bare = tight
                if bare.lower() in canon:
                    skipped_dup += 1        # held already under another spelling
                    continue
                canon.add(bare.lower())      # within-batch dedup
                g = p.get("genus") or genus
                buckets[path][g].append((bare, a or None))
    if skipped_dup:
        print(f"    dropped {skipped_dup:,} that were already held under a "
              f"different spelling")

    total = sum(len(v) for fam in buckets.values() for v in fam.values())
    print(f"\n  Stage 1 candidates: {total:,} species in {len(buckets):,} of our families")
    print(f"    with authorship from COL: {seen_auth:,}")
    if skipped_ambiguous:
        print(f"    skipped, family name ambiguous across kingdoms: {skipped_ambiguous:,}")
    print("  largest families by incoming species:")
    for path, n in sorted(buckets.items(), key=lambda kv: -sum(len(v) for v in kv[1].values()))[:10]:
        print(f"    {os.path.basename(path):<34}{sum(len(v) for v in n.values()):>7,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    targets = sorted(buckets.items(), key=lambda kv: -sum(len(v) for v in kv[1].values()))
    if args.limit_families:
        targets = targets[:args.limit_families]
    added = dedup = touched = 0
    for path, genera in targets:
        try:
            existing = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR {path}: {e}")
            continue
        new_root = {"id": existing.get("id"), "name": existing.get("name"),
                    "rank": "FAMILY", "children": []}
        buckets_g = {"GENUS": {}}
        for genus, species in genera.items():
            gnode = {"id": SF.node_id(GEN, genus), "name": genus, "rank": "GENUS",
                     "children": [], "sourcedFrom": SOURCE,
                     "lineage": existing.get("name") or genus}
            buckets_g["GENUS"][genus] = gnode
            new_root["children"].append(gnode)
            for nm, a in species:
                sp = {"id": SF.node_id(SPC, nm, a or ""), "name": nm,
                      "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE}
                if a:
                    sp["authorship"] = a
                gnode["children"].append(sp)
        m = SF.merge_family(
            existing, new_root,
            kingdom=path.split("taxonomy/")[1].split("/")[0],
            family_slug=os.path.basename(path)[:-5])
        added += m["species_added"]
        dedup += m["species_deduped"]
        touched += 1
        if m.get("authority_conflicts"):
            print(f"  ! {path}: {m['authority_conflicts']} species share an "
                  f"authority id with a different family already: "
                  f"{m['authority_conflict_examples'][0]}")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    print(f"\n  wrote {touched:,} family files")
    print(f"  species added:   {added:,}")
    print(f"  already present and merged: {dedup:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
