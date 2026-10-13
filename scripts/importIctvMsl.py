#!/usr/bin/env python3
"""ICTV Master Species List (MSL41.v1): the curated virus authority.

The xlsx served from ictv.global/msl (CC BY 4.0, MSL41.v1 ratified
2026-03-20) carries the full realm -> kingdom -> phylum -> class ->
order -> family -> genus -> species hierarchy in denormalised columns --
the same chain `coldp.chain()` reads out of a ColDP archive -- so the
part A/B placement of `importNcbiBacteriaViruses.py` applies verbatim,
reading the xlsx instead of an archive.

ICTV is the authority the NCBI pass was standing in for
(`importNcbiBacteriaViruses.py`'s own docstring says "ICTV MSL stays
worth having later as the dedicated, more rigorously curated virus
authority"). This run merges into the family files that pass already
wrote wherever the family name matches -- ICTV and NCBI derive their
family names from the same source, so a family file keyed by name is
the merge point -- and scaffolds the families the MSL names that NCBI
did not. Each species keeps its provenance in `sourcedFrom`
("ictv-msl"), and the MSL's own stable identifier (ICTV202420188 and
friends) is stamped as `ictvId` so a later re-run can re-identify
every name against a newer MSL edition.

Only the eight main ranks plus SUBFAMILY are read. The MSL also
carries subrealm, subkingdom, subphylum, subclass, suborder and
subgenus columns; those six ranks do not exist in the tree's
vocabulary (KINGDOM → PHYLUM → CLASS → ORDER → FAMILY → SUBFAMILY
→ GENUS → SPECIES → SUBSPECIES), so they are dropped. Subfamily
does exist -- buildData grafts genera under it and merge_family
matches by (rank, name) anywhere in the family, so a genus the
MSL nests under a subfamily merges into a file that holds that
genus directly -- and the MSL carries 232 of them, so it is read.

Usage:
    python3 scripts/importIctvMsl.py <msl.xlsx>            # dry run
    python3 scripts/importIctvMsl.py <msl.xlsx> --apply
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames as C  # noqa: E402
import importSpeciesFile as SF  # noqa: E402
import taxamatch  # noqa: E402

KINGDOM = "Viruses"
TAXONOMY_FILE = "portal/data/taxonomy-viruses.json"
DIR = "viruses"
SOURCE = "ictv-msl"
UNPLACED = "Incertae sedis"
CHAIN = ("phylum", "class", "order")
RANK_NODE = {"realm": "REALM", "kingdom": "KINGDOM",
             "phylum": "PHYLUM", "class": "CLASS", "order": "ORDER"}
# the hierarchy the MSL carries, outermost first; `family` and below are
# handled separately
HIERARCHY = ("realm", "kingdom", "phylum", "class", "order")

# ICTV's 2021+ reform writes binomial species names
# ("Alphalipothrixvirus beppuense"), but a quarter of the MSL
# still carries pre-reform legacy names ("Tobacco mosaic virus",
# "Tomato yellow leaf curl virus") -- real, curated species that
# the reform has not reached yet. Every row of the MSL is a valid
# species by construction, so the only filter needed is the junk
# one; the MSL's own Genus column supplies the genus for legacy
# names, so they never go through GNparser's binomial parse.
BAD = re.compile(r"\b(sp\.?|uncultured|unidentified|clone|culture|"
                  r"isolate|strain|symbiont|environmental|metagenome|"
                  r"candidatus|unclassified|environmental sample)\b", re.I)


def is_junk(nm):
    if not nm or BAD.search(nm):
        return True
    parts = nm.split()
    return not (2 <= len(parts) <= 8)


def looks_binomial(nm):
    parts = (nm or "").split()
    if len(parts) != 2:
        return False
    g, s = parts
    return g[:1].isupper() and g[1:].islower() and s.islower()


def dirname(name):
    return re.sub(r"\s+", "_", (name or "").lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    import openpyxl
    wb = openpyxl.load_workbook(args.xlsx, read_only=True,
                                data_only=True)
    ws = wb["MSL"]
    rows = ws.iter_rows(values_only=True)
    hdr = [str(h).strip() if h is not None else "" for h in next(rows)]
    ci = {h.lower(): i for i, h in enumerate(hdr)}
    need = list(HIERARCHY) + ["family", "genus", "species",
                                  "subfamily", "ictv_id", "genome"]
    missing = [c for c in need if c not in ci]
    if missing:
        sys.exit(f"MSL sheet is missing columns: {missing}")

    def cell(row, col):
        v = row[ci[col.lower()]]
        return str(v).strip() if v is not None else ""

    def ictv_id(row):
        # data_only=True reads the cached HYPERLINK display string
        # ("ICTV202420188"); when the cache is absent the raw formula
        # carries the same string as its label.
        v = row[ci["ictv_id"]]
        if v is None:
            return None
        v = str(v).strip()
        m = re.search(r"ICTV\d+", v)
        return m.group(0) if m else None

    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())

    # ---- read the MSL: one row per species, hierarchy in columns ----
    species_rows = []
    hierarchy_nodes = collections.defaultdict(set)  # rank -> names
    n_rows = 0
    n_skipped = 0
    n_binomial = 0
    for row in rows:
        n_rows += 1
        for rank in HIERARCHY:
            v = cell(row, rank)
            if v:
                hierarchy_nodes[rank].add(v)
        sp = cell(row, "species")
        if not sp:
            continue
        if is_junk(sp):
            n_skipped += 1
            continue
        if looks_binomial(sp):
            n_binomial += 1
        species_rows.append((row, sp))
    wb.close()
    print(f"  MSL rows: {n_rows:,}  species: {len(species_rows):,}"
          f" (binomial {n_binomial:,}, legacy"
          f" {len(species_rows) - n_binomial:,})"
          f"  junk rows: {n_skipped:,}")
    for rank in HIERARCHY:
        print(f"  {rank}: {len(hierarchy_nodes[rank]):,}")

    # ---- on-disk families already under this kingdom (part A target) ----
    fam_paths = {}
    import glob
    for f in glob.glob(f"taxonomy/{DIR}/**/src/data/*.json", recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        fam_paths[(d.get("name") or "").strip().lower()] = f
    print(f"  existing {DIR} families on disk: {len(fam_paths):,}")

    if os.path.exists(TAXONOMY_FILE):
        tax = json.load(open(TAXONOMY_FILE, encoding="utf-8"))
    else:
        tax = {"id": KINGDOM.upper(), "name": KINGDOM, "rank": "KINGDOM",
               "children": []}

    used_ids = set()

    def collect_ids(node):
        if node.get("id"):
            used_ids.add(node["id"])
        for c in node.get("children") or []:
            collect_ids(c)
    collect_ids(tax)

    def new_id(prefix, nm, ancestry=()):
        base = SF.node_id(prefix, nm)
        if base not in used_ids:
            used_ids.add(base)
            return base
        for depth in (1, 2, 3):
            anc = [a for a in ancestry[-depth:] if a]
            cand = "_".join([SF.slug(a).upper() for a in reversed(anc)]
                            + [SF.slug(nm).upper()])
            if cand not in used_ids:
                used_ids.add(cand)
                return cand
        n = 2
        base = SF.slug(nm).upper()
        if ancestry:
            base = f"{SF.slug(ancestry[-1]).upper()}_{base}"
        while f"{base}_{n}" in used_ids:
            n += 1
        cand = f"{base}_{n}"
        used_ids.add(cand)
        return cand

    # ---- bucket species into A (existing family) / B (new family) ----
    existing_kids = collections.defaultdict(list)
    new_kids = collections.defaultdict(list)
    for row, sp in species_rows:
        fname = cell(row, "family")
        fkey = fname.lower()
        if fkey in fam_paths:
            existing_kids[fkey].append((row, sp))
        else:
            new_kids[fname].append((row, sp))

    n_a = sum(len(v) for v in existing_kids.values())
    n_b = sum(len(v) for v in new_kids.values())
    print(f"  A existing families: {len(existing_kids):,} families,"
          f" {n_a:,} species")
    print(f"  B new families:      {len(new_kids):,} families,"
          f" {n_b:,} species")

    raw = sorted({sp for kids in list(existing_kids.values())
                  + list(new_kids.values()) for _, sp in kids})
    print(f"  normalising {len(raw):,} names through GNparser ...",
          flush=True)
    parsed = taxamatch.parse_names(raw)
    placed = set()

    def canonical(nm, row):
        if looks_binomial(nm):
            g, s = taxamatch.bare_binomial(nm, parsed)
            if not g or not s:
                return None, None
            bare = taxamatch.bare_name(nm, parsed)
            for form in (bare, f"{g} ×{s}", f"{g} × {s}"):
                if form.lower() in canon or form.lower() in placed:
                    return None, None
            placed.add(bare.lower())
            return bare, g
        # legacy name: the MSL's Genus column is the authority for
        # the genus, and the name as written is the canonical form
        # (ICTV names carry no authorship to strip)
        bare = nm.strip()
        if bare.lower() in canon or bare.lower() in placed:
            return None, None
        placed.add(bare.lower())
        return bare, cell(row, "genus")

    counters = {"written": 0, "skipped": 0}

    def place(realm, kingdom, phylum, klass, order, fname, kids,
              path=None):
        fslug = SF.slug(fname)
        if not realm:
            counters["skipped"] += len(kids)
            return
        if not order:
            order = UNPLACED
        if not klass:
            klass = phylum
        if not phylum:
            phylum = kingdom

        subfamily_of = {}  # subfamily ("" = none) -> genus -> species
        seen = set()
        for row, sp in kids:
            bare, g = canonical(sp, row)
            if bare is None:
                counters["skipped"] += 1
                continue
            key = (g, bare.lower())
            if key in seen:
                counters["skipped"] += 1
                continue
            seen.add(key)
            sub = cell(row, "subfamily")
            subfamily_of.setdefault(sub, {}).setdefault(g, []).append(
                (bare, ictv_id(row), cell(row, "Genome")))
        if not subfamily_of:
            return
        n_species = sum(len(v) for genera in subfamily_of.values()
                          for v in genera.values())

        if path is None:
            parent = tax
            chain_names = [n for n in (realm, kingdom, phylum, klass,
                                       order) if n]
            for i, (tag, val) in enumerate((("realm", realm),
                             ("kingdom", kingdom), ("phylum", phylum),
                             ("class", klass), ("order", order))):
                found = next((c for c in (parent.get("children") or [])
                              if c.get("rank") == RANK_NODE[tag]
                              and (c.get("name") or "").lower()
                              == val.lower()), None)
                if found is None:
                    found = {"id": new_id(RANK_NODE[tag], val,
                                          chain_names[:i + 1]),
                             "name": val, "rank": RANK_NODE[tag]}
                    parent.setdefault("children", []).append(found)
                parent = found
            existing = next((c for c in (parent.get("children") or [])
                             if c.get("rank") == "FAMILY"
                             and SF.slug(c.get("name") or "") == fslug),
                            None)
            if existing is None:
                fam_id = new_id("FAM", fname,
                                [x for x in (realm, kingdom, phylum,
                                             klass, order) if x])
                existing = {"id": fam_id, "name": fname, "rank": "FAMILY",
                            "appSlug": fslug, "speciesCount": n_species}
                parent.setdefault("children", []).append(existing)
            else:
                fam_id = existing.get("id")
                existing["speciesCount"] = (
                    (existing.get("speciesCount") or 0) + n_species)
            seg = [DIR, dirname(realm), dirname(kingdom), dirname(phylum),
                   dirname(klass), dirname(order), fslug]
            target = os.path.join("taxonomy", *seg, "src", "data",
                                  f"{fslug}.json")
        else:
            target = path
            fam_id = None

        new_root = {"id": fam_id, "name": fname, "rank": "FAMILY",
                    "children": [], "speciesCount": n_species,
                    "appSlug": fslug, "sourcedFrom": SOURCE}
        for sub, genera in sorted(subfamily_of.items(),
                                    key=lambda kv: (kv[0] != "", kv[0])):
            parent = new_root
            if sub:
                sfnode = {"id": new_id("SUBFAM", sub, [fname]),
                          "name": sub, "rank": "SUBFAMILY",
                          "children": [],
                          "sourcedFrom": SOURCE, "lineage": fname}
                new_root["children"].append(sfnode)
                parent = sfnode
            for g, species in genera.items():
                gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g),
                         "name": g, "rank": "GENUS", "children": [],
                         "sourcedFrom": SOURCE, "lineage": fname}
                parent["children"].append(gnode)
                for nm2, ictvid, genome in species:
                    sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm2),
                          "name": nm2, "rank": "SPECIES",
                          "subspeciesCount": 0, "sourcedFrom": SOURCE,
                          "lineage": g}
                    if ictvid:
                        sp["ictvId"] = ictvid
                    if genome:
                        sp["genome"] = genome
                    gnode["children"].append(sp)
        new_root["genusCount"] = sum(len(genera)
                                       for genera in
                                       subfamily_of.values())

        root = new_root
        if os.path.exists(target):
            old = json.load(open(target, encoding="utf-8"))
            m = SF.merge_family(old, new_root, kingdom=DIR,
                                family_slug=fslug)
            root = old
            if m.get("authority_conflicts"):
                print(f"  ! {fslug}: {m['authority_conflicts']}"
                      " authority conflicts")
        if args.apply:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                json.dump(root, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        counters["written"] += 1

    # part A: merge into families already on disk
    for fkey, kids in existing_kids.items():
        path = fam_paths[fkey]
        existing = json.load(open(path, encoding="utf-8"))
        row0, _ = kids[0]
        place(cell(row0, "realm"), cell(row0, "kingdom"),
              cell(row0, "phylum"), cell(row0, "class"),
              cell(row0, "order"), existing.get("name") or fkey, kids,
              path=path)

    # part B: families the MSL names that we lack
    targets = sorted(new_kids.items(), key=lambda kv: -len(kv[1]))
    for fname, kids in targets:
        if not fname:
            continue
        row0, _ = kids[0]
        place(cell(row0, "realm"), cell(row0, "kingdom"),
              cell(row0, "phylum"), cell(row0, "class"),
              cell(row0, "order"), fname, kids)

    print(f"\n  family files written/merged: {counters['written']:,}")
    print(f"  species skipped (unbinominal or already held):"
          f" {counters['skipped']:,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    with open(TAXONOMY_FILE, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"\n  wrote {TAXONOMY_FILE}"
          "  (NOT registered in kingdom-config.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
