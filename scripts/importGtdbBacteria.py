#!/usr/bin/env python3
"""GTDB r232: scaffold the Bacteria domain as data structures only.

**Deliberately does not touch `portal/data/kingdom-config.json`.** Bacteria and
viruses are on hold (`docs/bacteria-and-viruses.md`); what changed is that the
rank question is now settled (GTDB phyla such as Bacillota and Pseudomonadota
sit exactly where our tree already puts Archaea's GTDB phyla -- kingdom-rank
children, not kingdoms of their own), so the *data* can be produced and sat on
disk while the decision to wire it into the portal stays open. Nothing here
runs the portal build, adds a colour registry, or registers a kingdom: it
writes `portal/data/taxonomy-bacteria.json` and
`taxonomy/bacteria/<phylum>/<class>/<order>/<family>/src/data/<family>.json`
and stops. kingdom-config.json's declared-kingdom gate
(`importColStage2.py`'s own check) is the thing this script exists to not
need yet.

GTDB has no existing bacteria family on disk to merge into -- this is the
first import for this kingdom -- so every species is `importColStage2.py`'s
part B (scaffold a new family) or part C (no family resolved; parked under
'Incertae sedis'). There is no part A. The placement logic below is a direct
copy of `importColStage2.place()`, trimmed of the on-disk-family lookup that
part A needs and that an empty kingdom has nothing to populate.

GTDB ranks domain/phylum/class/order/family/genus/species, no kingdom rank at
all (see `coldp.chain()`), which is why 'domain' is in the rank tuple read
here and why the kingdom label 'Bacteria' is a literal rather than something
read off a row.

Usage:
    python3 scripts/importGtdbBacteria.py <gtdb_archive.zip>            # dry run
    python3 scripts/importGtdbBacteria.py <gtdb_archive.zip> --apply
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

KINGDOM = "Bacteria"
TAXONOMY_FILE = "portal/data/taxonomy-bacteria.json"
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
    ap.add_argument("--limit-families", type=int, default=0)
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
        tax = {"id": "BACTERIA", "name": KINGDOM, "rank": "KINGDOM", "children": []}

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
        while f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(nm).upper()}_{n}" in used_ids:
            n += 1
        cand = f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(nm).upper()}_{n}"
        used_ids.add(cand)
        return cand

    # ---- bucket every Bacteria-domain species by its GTDB family ----
    fam_kids = collections.defaultdict(list)   # family taxon id -> [species ids]
    nofam_kids = []
    for t, r in rank.items():
        if r not in ("species", "subspecies"):
            continue
        nm = name.get(t)
        if not nm or nm.strip().lower() in canon:
            continue
        ch = chain(t)
        dom = ch.get("domain") or ch.get("superkingdom") or ch.get("kingdom")
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

    raw = sorted({name[t] for kids in list(fam_kids.values()) + [nofam_kids]
                  for t in kids})
    print(f"  normalising {len(raw):,} names through GNparser ...", flush=True)
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

    def place(phylum, klass, order, fname, kids):
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
                (bare, (extra.get(t, {}).get("authorship") or "").strip() or None))
        if not genus_of:
            return

        parent = tax
        for i, (tag, val) in enumerate((("phylum", phylum), ("class", klass),
                                         ("order", order))):
            found = next((c for c in (parent.get("children") or [])
                          if c.get("rank") == RANK_NODE[tag]
                          and (c.get("name") or "").lower() == val.lower()), None)
            if found is None:
                chain_names = [n for n in (phylum, klass, order) if n]
                found = {"id": new_id(RANK_NODE[tag], val, chain_names[:i + 1]),
                         "name": val, "rank": RANK_NODE[tag]}
                if tag == "order" and order == UNPLACED:
                    found["commonName"] = "Unplaced"
                    new_orders.append(val)
                parent.setdefault("children", []).append(found)
            parent = found

        existing = next((c for c in (parent.get("children") or [])
                         if c.get("rank") == "FAMILY"
                         and SF.slug(c.get("name") or "") == fslug), None)
        n_species = sum(len(v) for v in genus_of.values())
        if existing is None:
            fam_id = new_id("FAM", fname, [x for x in (phylum, klass, order) if x])
            existing = {"id": fam_id, "name": fname, "rank": "FAMILY",
                        "appSlug": fslug, "speciesCount": n_species}
            parent.setdefault("children", []).append(existing)
        else:
            fam_id = existing.get("id")
            existing["speciesCount"] = (existing.get("speciesCount") or 0) + n_species

        seg = ["bacteria", dirname(phylum), dirname(klass), dirname(order), fslug]
        d = os.path.join("taxonomy", *seg, "src", "data")
        target = os.path.join(d, f"{fslug}.json")

        root = {"id": fam_id, "name": fname, "rank": "FAMILY", "children": [],
                "speciesCount": n_species, "appSlug": fslug, "sourcedFrom": SOURCE}
        lin = " > ".join(x for x in (SF.nodename(phylum), SF.nodename(klass)) if x)
        if lin:
            root["lineage"] = lin
        for g, species in genus_of.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
            root["children"].append(gnode)
            for nm2, a in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm2, a or ""),
                      "name": nm2, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
                gnode["children"].append(sp)
        root["genusCount"] = len(genus_of)

        if os.path.exists(target):
            old = json.load(open(target, encoding="utf-8"))
            SF.merge_family(old, root, kingdom="bacteria", family_slug=fslug)
            root = old
        if args.apply:
            os.makedirs(d, exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                json.dump(root, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        counters["written"] += 1

    incerta = collections.defaultdict(list)
    for t in nofam_kids:
        bare, g = canonical(name[t])
        if bare is None:
            counters["skipped"] += 1
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

    targets = sorted(fam_kids.items(), key=lambda kv: -len(kv[1]))
    if args.limit_families:
        targets = targets[:args.limit_families]
    for fam, kids in targets:
        fname = (name.get(fam) or "").strip()
        if not fname:
            continue
        ch = chain(fam)
        place((ch.get("phylum") or "").strip(), (ch.get("class") or "").strip(),
              (ch.get("order") or "").strip(), fname, kids)

    print(f"\n  family files written:  {counters['written']:,}")
    print(f"  species skipped (unbinominal or already held): {counters['skipped']:,}")
    print(f"  families placed under '{UNPLACED}': {counters['unplaced']:,}")
    print(f"  new ORDER nodes: {len(new_orders):,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    with open(TAXONOMY_FILE, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"\n  wrote {TAXONOMY_FILE}  (NOT registered in kingdom-config.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
