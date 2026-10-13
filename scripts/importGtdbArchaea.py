#!/usr/bin/env python3
"""GTDB r232: top up the declared Archaea kingdom.

The bacteria scaffold (`importGtdbBacteria.py`) was deliberately
inert -- bacteria are not in kingdom-config.json. Archaea IS a
declared kingdom, and its tree already speaks GTDB's names
(Aenigmatarchaeota, Halobacteriota, Methanobacteriota,
Thermoproteota ... are GTDB phyla), so this run is the same
scoping and placement with three differences that follow from
the kingdom being live:

  * it writes the declared kingdom's own input file,
    `portal/data/taxonomy-archaea.json`, which the build reads;
  * part A exists -- 131 archaeal family files are already on
    disk (NCBI/ITIS imports), so GTDB species whose family we
    hold merge into those files instead of scaffolding a
    parallel copy;
  * part C resolves family-less species through the genera we
    hold, parking the rest under 'Incertae sedis' exactly as
    the bacteria run did.

GTDB ranks domain/phylum/class/order/family/genus/species and
has no kingdom rank at all, so 'domain' is in the rank tuple
and the Archaea kingdom label is a literal. The domain filter
keeps the 189,801 bacterial species out: only the 10,122
archaeal species of the Archaea domain are in scope.

Usage:
    python3 scripts/importGtdbArchaea.py <gtdb_archive.zip>
    python3 scripts/importGtdbArchaea.py <gtdb_archive.zip> --apply
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames as C  # noqa: E402
import coldp  # noqa: E402
import importSpeciesFile as SF  # noqa: E402
import taxamatch  # noqa: E402

KINGDOM = "Archaea"
TAXONOMY_FILE = "portal/data/taxonomy-archaea.json"
DIR = "archaea"
SOURCE = "gtdb"
UNPLACED = "Incertae sedis"
CHAIN = ("phylum", "class", "order")
RANK_NODE = {"phylum": "PHYLUM", "class": "CLASS", "order": "ORDER"}
RANKS = ("domain", "superkingdom", "kingdom") + CHAIN + ("family",)


def dirname(name):
    return re.sub(r"\s+", "_", (name or "").lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())
    par, rank, name, extra = coldp.load_core(args.archive)
    print(f"  GTDB accepted taxa: {len(par):,}")

    def chain(tid):
        return coldp.chain(tid, par, rank, name, ranks=RANKS)

    if os.path.exists(TAXONOMY_FILE):
        tax = json.load(open(TAXONOMY_FILE, encoding="utf-8"))
    else:
        tax = {"id": KINGDOM.upper(), "name": KINGDOM, "rank": "KINGDOM",
               "children": []}

    # ---- on-disk families and genera already under this kingdom ----
    fam_paths = {}
    genus_family = {}
    import glob
    for f in glob.glob(f"taxonomy/{DIR}/**/src/data/*.json",
                         recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        fam_paths[(d.get("name") or "").strip().lower()] = f
        for g in d.get("children") or []:
            if g.get("rank") == "GENUS":
                genus_family.setdefault((g.get("name") or "").strip()
                                        .lower(), f)
    print(f"  existing {DIR} families on disk: {len(fam_paths):,}")

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

    # ---- bucket every Archaea-domain species by its GTDB family ----
    fam_kids = collections.defaultdict(list)   # family id -> [species]
    nofam_kids = []
    for t, r in rank.items():
        if r not in ("species", "subspecies"):
            continue
        nm = name.get(t)
        if not nm or nm.strip().lower() in canon:
            continue
        ch = chain(t)
        dom = ch.get("domain") or ch.get("superkingdom") \
            or ch.get("kingdom")
        if dom != KINGDOM:
            continue
        fam = None
        c, n = t, 0
        while c and n < 60:
            if rank.get(c) == "family":
                fam = c
                break
            c = par.get(c)
            n += 1
        if fam is None:
            nofam_kids.append(t)
        else:
            fam_kids[fam].append(t)

    n_new = sum(len(v) for v in fam_kids.values())
    print(f"  families: {len(fam_kids):,}   species: {n_new:,}")
    print(f"  no family in GTDB: {len(nofam_kids):,}")

    # part A target: families GTDB names that we already hold
    existing_kids = {}
    new_kids = {}
    for fam, kids in fam_kids.items():
        fname = (name.get(fam) or "").strip()
        if not fname:
            continue
        if fname.lower() in fam_paths:
            existing_kids[fname.lower()] = kids
        else:
            new_kids[fam] = kids
    print(f"  A existing families: {len(existing_kids):,} families,"
          f" {sum(len(v) for v in existing_kids.values()):,} species")
    print(f"  B new families:      {len(new_kids):,} families,"
          f" {sum(len(v) for v in new_kids.values()):,} species")

    raw = sorted({name[t] for kids in list(existing_kids.values())
                  + list(new_kids.values()) + [nofam_kids]
                  for t in kids})
    print(f"  normalising {len(raw):,} names through GNparser ...",
          flush=True)
    parsed = taxamatch.parse_names(raw)
    placed = set()

    def canonical(nm):
        g, s = taxamatch.bare_binomial(nm, parsed)
        if not g or not s:
            return None, None
        bare = taxamatch.bare_name(nm, parsed)
        for form in (bare, f"{g} {s}", f"{g} ×{s}", f"{g} × {s}"):
            if form.lower() in canon or form.lower() in placed:
                return None, None
        placed.add(bare.lower())
        return bare, g

    new_orders = []
    counters = {"written": 0, "skipped": 0, "unplaced": 0}

    def place(phylum, klass, order, fname, kids, path=None):
        fslug = SF.slug(fname)
        if not phylum:
            counters["skipped"] += len(kids)
            return
        if not order:
            order = UNPLACED
            counters["unplaced"] += 1
        if not klass:
            klass = phylum

        genus_of = {}
        seen = set()
        for t in kids:
            bare, g = canonical(name[t])
            if bare is None:
                counters["skipped"] += 1
                continue
            key = (g, bare.lower())
            if key in seen:
                counters["skipped"] += 1
                continue
            seen.add(key)
            genus_of.setdefault(g, []).append(
                (bare, (extra.get(t, {}).get("authorship") or "")
                 .strip() or None))
        if not genus_of:
            return
        n_species = sum(len(v) for v in genus_of.values())

        if path is None:
            parent = tax
            chain_names = [n for n in (phylum, klass, order) if n]
            for i, (tag, val) in enumerate((("phylum", phylum),
                                             ("class", klass),
                                             ("order", order))):
                found = next((c for c in (parent.get("children") or [])
                              if c.get("rank") == RANK_NODE[tag]
                              and (c.get("name") or "").lower()
                              == val.lower()), None)
                if found is None:
                    found = {"id": new_id(RANK_NODE[tag], val,
                                              chain_names[:i + 1]),
                             "name": val, "rank": RANK_NODE[tag]}
                    if tag == "order" and order == UNPLACED:
                        found["commonName"] = "Unplaced"
                        new_orders.append(val)
                    parent.setdefault("children", []).append(found)
                parent = found
            existing = next((c for c in (parent.get("children") or [])
                             if c.get("rank") == "FAMILY"
                             and SF.slug(c.get("name") or "") == fslug),
                            None)
            if existing is None:
                fam_id = new_id("FAM", fname,
                                [x for x in (phylum, klass, order)
                                 if x])
                existing = {"id": fam_id, "name": fname, "rank": "FAMILY",
                            "appSlug": fslug, "speciesCount": n_species}
                parent.setdefault("children", []).append(existing)
            else:
                fam_id = existing.get("id")
                existing["speciesCount"] = (
                    (existing.get("speciesCount") or 0) + n_species)
            seg = [DIR, dirname(phylum), dirname(klass), dirname(order),
                   fslug]
            target = os.path.join("taxonomy", *seg, "src", "data",
                                  f"{fslug}.json")
        else:
            target = path
            fam_id = None

        new_root = {"id": fam_id, "name": fname, "rank": "FAMILY",
                    "children": [], "speciesCount": n_species,
                    "appSlug": fslug, "sourcedFrom": SOURCE}
        for g, species in genus_of.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom":
                         SOURCE, "lineage": fname}
            new_root["children"].append(gnode)
            for nm2, a in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm2, a or ""),
                      "name": nm2, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
                gnode["children"].append(sp)
        new_root["genusCount"] = len(genus_of)

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
        place("", "", "", existing.get("name") or fkey, kids, path=path)

    # part C: no family in GTDB -> resolve by genus, else Incertae sedis
    incerta = collections.defaultdict(list)
    for t in nofam_kids:
        bare, g = canonical(name[t])
        if bare is None:
            counters["skipped"] += 1
            continue
        hit = genus_family.get((g or "").strip().lower())
        if hit:
            existing = json.load(open(hit, encoding="utf-8"))
            place("", "", "", existing.get("name") or "", [t], path=hit)
            continue
        ch = chain(t)
        phylum = (ch.get("phylum") or "").strip()
        klass = (ch.get("class") or "").strip()
        order = (ch.get("order") or "").strip() or UNPLACED
        if not phylum:
            counters["skipped"] += 1
            continue
        incerta[(phylum, klass, order)].append(t)
    for (phylum, klass, order), kids in sorted(incerta.items()):
        place(phylum, klass, order, UNPLACED, kids)

    # part B: families GTDB names that we lack
    targets = sorted(new_kids.items(), key=lambda kv: -len(kv[1]))
    for fam, kids in targets:
        fname = (name.get(fam) or "").strip()
        if not fname:
            continue
        ch = chain(fam)
        place((ch.get("phylum") or "").strip(),
              (ch.get("class") or "").strip(),
              (ch.get("order") or "").strip(), fname, kids)

    print(f"\n  family files written/merged: {counters['written']:,}")
    print(f"  species skipped (unbinominal or already held):"
          f" {counters['skipped']:,}")
    print(f"  families placed under '{UNPLACED}': {counters['unplaced']:,}")
    print(f"  new ORDER nodes: {len(new_orders):,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    with open(TAXONOMY_FILE, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"\n  wrote {TAXONOMY_FILE}"
          "  (declared kingdom -- the build reads this file)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
