#!/usr/bin/env python3
"""Restore any Atactophlebiidae species an interrupted fix discarded.

`fix_duplicate_family_nodes.py` merged a COL-written duplicate of this family
into the curated grylloblattodea copy, then crashed on an `rmdir` before it
wrote taxonomy.json. Rolling that back restored the tracked file, which threw
away four species the merge had just gained -- including one, Novokshonovus
ignoratus, that had never been recorded anywhere.

A later re-run of the now-idempotent merge put those four back, so this now
reports *nothing to do (already complete)* against the family as it stands. It
is kept for what it is: a check that takes COL's own species list as the
authority for one family and adds only what is missing, which is how the gap
was confirmed closed rather than assumed closed. Re-running
`importColStage2.py` would be the wrong tool for it -- that is a whole-kingdom
run, and the import it would repeat is already applied and verified (see
docs/reports/SESSION-2026-10-04-col-stage2-animalia.md).

Two conventions are read from the file rather than assumed:

- **The extinct marker.** All four existing genera are named with a leading
  dagger; grylloblattids are wholly extinct, so the new names take it too. A
  family with no marker in its existing names gets none.
- **Node shape and ids.** Nodes carry `authorship` and `yearPublished` split,
  and ids are `SP_<GENUS>_<EPITHET>_<AUTHOR>_<YEAR>` with a second author kept
  as a further underscore-separated surname (`Jubala` is
  `GENUS_JUBALA_ARISTOV_RASNITSYN_2015`). Genus authorship comes from COL's own
  genus-rank rows, not from the species that sit under them.

Idempotent: a second run finds nothing to add.

    python3 scripts/restore_atactophlebiidae_species.py
    python3 scripts/restore_atactophlebiidae_species.py --apply
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import zipfile

COL = ("/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/"
       "col2026-base_dwca.zip")
TAXONOMY = "portal/data/taxonomy.json"
SLUG = "atactophlebiidae"
FAMILY = "Atactophlebiidae"
ACCEPTED = {"accepted", "provisionally accepted"}
SOURCE = "catalogue of life"
DAGGER = "\u2020"


def find_family_files():
    import glob
    hits = [f for f in glob.glob(f"taxonomy/*/**/{SLUG}/src/data/{SLUG}.json",
                                 recursive=True) if "node_modules" not in f]
    if not hits:
        sys.exit(f"FATAL: no data file for slug {SLUG!r}")
    return hits


def load_col_family():
    """COL's accepted species of FAMILY, plus genus authorship for its genera.

    Returns (species, genus_auth) where species is a list of
    (name, authorship, year, genus).
    """
    par, rank, name, auth = {}, {}, {}, {}
    fam_ids, genus_auth = set(), {}
    with zipfile.ZipFile(COL).open("Taxon.tsv") as f:
        hdr = f.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        ci = {h: i for i, h in enumerate(hdr)}
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) < 7 or p[ci["dwc:taxonomicStatus"]] not in ACCEPTED:
                continue
            t = p[ci["dwc:taxonID"]]
            par[t] = p[ci["dwc:parentNameUsageID"]]
            rank[t] = p[ci["dwc:taxonRank"]]
            name[t] = p[ci["dwc:scientificName"]]
            auth[t] = (p[ci["dwc:scientificNameAuthorship"]] or "").strip()
            if rank[t] == "family" and (name[t] or "").strip() == FAMILY:
                fam_ids.add(t)

    species = []
    for t, r in rank.items():
        if r != "species":
            continue
        c, n = t, 0
        while c and n < 60:
            if c in fam_ids:
                nm = (name[t] or "").strip()
                a = auth[t]
                m = re.match(r"^(.*?),\s*(\d{4}[a-z]?)$", a)
                if m:
                    who, year = m.group(1).strip(), m.group(2)
                else:
                    who, year = (a or None), None
                genus = nm.split()[0] if nm else ""
                species.append((nm, who, year, genus))
                break
            c = par.get(c)
            n += 1

    # Authorship of the genus-rank rows themselves. Read from COL rather than
    # carried over from the species that sit under them: Novokshonovus is
    # "Aristov & Rasnitsyn, 2015" while its species are split between
    # "Aristov, 2015" and "Aristov & Rasnitsyn, 2015".
    wanted = {g for _, _, _, g in species if g}
    for t, r in rank.items():
        if r == "genus" and (name[t] or "").strip() in wanted:
            genus_auth[(name[t] or "").strip()] = auth[t]

    species.sort()
    return species, genus_auth


def id_for(prefix, name, who, year):
    parts = [prefix, name.upper()]
    if who:
        parts += [w.upper() for w in re.split(r"[^A-Za-z\u00c0-\u024f]+", who) if w]
    if year:
        parts.append(str(year))
    out = "_".join(parts)
    return re.sub(r"[^A-Z0-9_]+", "_", out).strip("_")


def bare(nm):
    return nm.lstrip(DAGGER).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    paths = find_family_files()
    print(f"  family file: {paths[0]}"
          + (f" (+{len(paths) - 1} more)" if len(paths) > 1 else ""))
    root = json.load(open(paths[0], encoding="utf-8"))

    genera = {g.get("name"): g for g in root.get("children") or []
              if g.get("rank") == "GENUS"}
    held = {bare(s.get("name") or "") for g in genera.values()
            for s in g.get("children") or []}
    # does this family mark its names extinct?
    marked = any((g.get("name") or "").startswith(DAGGER)
                 for g in genera.values())
    mark = DAGGER if marked else ""
    print(f"  existing genera: {len(genera)}, species: {len(held)}, "
          f"extinct marker: {mark or '(none)'}")

    print(f"  reading {os.path.basename(COL)} ...", flush=True)
    species, genus_auth = load_col_family()
    print(f"  COL species for {FAMILY}: {len(species)}")

    added = []
    for nm, who, year, genus in species:
        if bare(nm) in held:
            continue
        gname = mark + genus
        gnode = genera.get(gname)
        if gnode is None:
            ga = genus_auth.get(genus)
            m = re.match(r"^(.*?),\s*(\d{4}[a-z]?)$", ga or "")
            gwho, gyear = (m.group(1).strip(), m.group(2)) if m else (ga or None, None)
            gnode = {"id": id_for("GENUS", genus, gwho, gyear), "name": gname,
                     "rank": "GENUS"}
            if gwho:
                gnode["authorship"] = gwho
            if gyear:
                gnode["yearPublished"] = gyear
            gnode["extinct"] = bool(mark)
            gnode["sourcedFrom"] = SOURCE
            gnode["children"] = []
            genera[gname] = gnode
            root.setdefault("children", []).append(gnode)
        node = {"id": id_for("SP", nm, who, year), "name": mark + nm,
                "rank": "SPECIES"}
        if who:
            node["authorship"] = who
        if year:
            node["yearPublished"] = year
        node["extinct"] = bool(mark)
        node["sourcedFrom"] = SOURCE
        node["subspeciesCount"] = 0
        node["lineage"] = gname
        node["children"] = []
        gnode.setdefault("children", []).append(node)
        held.add(bare(nm))
        added.append((gname, node["name"], node["id"]))

    if not added:
        print("\n  nothing to do (already complete)")
        return 0

    print(f"\n  would add {len(added)} species in "
          f"{len({a[0] for a in added})} genera:")
    for gname, nm, i in added:
        print(f"    + {gname:22s} {nm:32s} {i}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    root["speciesCount"] = len(held)
    root["genusCount"] = len(genera)
    with open(paths[0], "w", encoding="utf-8") as fh:
        json.dump(root, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # the node's speciesCount is what the Coverage modal reads
    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    touched = []

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug") == SLUG:
            n["speciesCount"] = len(held)
            touched.append(n.get("name"))
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    with open(TAXONOMY, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"\n  wrote {paths[0]} (speciesCount={len(held)}, "
          f"genusCount={len(genera)})")
    print(f"  updated speciesCount on {len(touched)} taxonomy node(s): "
          f"{', '.join(touched) or '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())