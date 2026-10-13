#!/usr/bin/env python3
"""NCBI Taxonomy (ChecklistBank 2169): top up Bacteria, scaffold Viruses.

Both run from the same already-downloaded ColDP archive and the same reader
(`coldp.py`) that the main NCBI Taxonomy import already used -- no new format
work needed. **Deliberately does not touch `portal/data/kingdom-config.json`**,
same policy as `importGtdbBacteria.py`: bacteria and viruses stay data
structures only until that decision is made.

Two different shapes, because the tree already holds Bacteria (from GTDB) but
holds no Viruses at all yet:

  bacteria: part A (merge into a family GTDB already wrote) + part B
            (scaffold a family GTDB didn't have). Both exist because GTDB and
            NCBI's family sets only partly overlap.
  viruses:  part B/C only -- there is no existing virus family to merge into,
            same as importGtdbBacteria.py's very first run.

**NCBI's species rank is overwhelmingly not species.** Of 536,359 rows under
taxid 2 (Bacteria), the bulk are strain/clone/environmental-sample records
("bacterium enrichment culture clone En_UW_77", "uncultured gamma
proteobacterium MB10g-RC5") that a binomial-species importer has no business
writing as a species node -- that is NOT what COL/GTDB mean by species, and
accepting them uncritically is how "536,359 species" becomes a false claim.
`looks_binomial()` rejects them before `canonical()` ever runs GNparser on
them, the same role the hand-rolled regex in archiveOverlap.py's audit script
plays for other sources' junk rows. After that filter: 26,295 clean bacterial
binomials and 16,740 clean viral names not already held (measured
2026-10-12). Virus names are not Latin binomials in the classical sense
(ICTV's 2021+ reform writes compound epithets like
"Cytomegalovirus saimiriinebeta4"), so the filter only requires two
space-separated tokens with no junk keyword, not Latin morphology.

NCBI's own taxdump already carries ICTV's modern virus ranks (realm, kingdom,
phylum, class, order, family, genus, species) under taxid 10239 -- 358
families, 93 orders, 21 phyla, 7 realms -- so `coldp.chain()`'s ranks tuple
is extended with "realm" for this run rather than needing ICTV's own export
at all. ICTV MSL stays worth having later as the dedicated, more rigorously
curated virus authority; this is NCBI's own copy of the same taxonomy, usable
today because the reader already exists.

Usage:
    python3 scripts/importNcbiBacteriaViruses.py <archive.zip> --domain bacteria
    python3 scripts/importNcbiBacteriaViruses.py <archive.zip> --domain viruses --apply
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

DOMAINS = {
    "bacteria": {"root": "2", "kingdom": "Bacteria",
                 "taxonomy_file": "portal/data/taxonomy-bacteria.json",
                 "dir": "bacteria", "source": "ncbi-taxonomy"},
    "viruses": {"root": "10239", "kingdom": "Viruses",
                "taxonomy_file": "portal/data/taxonomy-viruses.json",
                "dir": "viruses", "source": "ncbi-taxonomy"},
}
UNPLACED = "Incertae sedis"
CHAIN = ("phylum", "class", "order")
RANK_NODE = {"phylum": "PHYLUM", "class": "CLASS", "order": "ORDER"}
RANKS = ("realm", "kingdom", "domain", "superkingdom") + CHAIN + ("family",)

BAD = re.compile(r"\b(sp\.?|uncultured|unidentified|bacterium|clone|culture|"
                  r"enrichment|isolate|strain|symbiont|endosymbiont|"
                  r"environmental|metagenome|candidatus|aff\.)\b", re.I)


def looks_binomial(nm):
    if not nm or BAD.search(nm):
        return False
    parts = nm.split()
    if len(parts) != 2:
        return False
    g, s = parts
    return g[:1].isupper() and g[1:].islower() and s.islower()


def dirname(name):
    return re.sub(r"\s+", "_", (name or "").lower())


def subtree_ids(root, children):
    out, st = set(), [root]
    while st:
        c = st.pop()
        if c in out:
            continue
        out.add(c)
        st.extend(children.get(c, []))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--domain", choices=sorted(DOMAINS), required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    cfg = DOMAINS[args.domain]
    KINGDOM, TAXONOMY_FILE, DIR, SOURCE = (
        cfg["kingdom"], cfg["taxonomy_file"], cfg["dir"], cfg["source"])

    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())
    par, rank, name, extra = coldp.load_core(args.archive)
    print(f"  NCBI accepted taxa: {len(par):,}")

    children = collections.defaultdict(list)
    for t, p in par.items():
        children[p].append(t)
    scope = subtree_ids(cfg["root"], children)
    print(f"  {KINGDOM} subtree: {len(scope):,} taxa")

    def chain(tid):
        return coldp.chain(tid, par, rank, name, ranks=RANKS)

    if os.path.exists(TAXONOMY_FILE):
        tax = json.load(open(TAXONOMY_FILE, encoding="utf-8"))
    else:
        tax = {"id": KINGDOM.upper(), "name": KINGDOM, "rank": "KINGDOM",
               "children": []}

    # ---- on-disk families already under this kingdom (part A target) ----
    fam_paths = {}
    genus_family = {}
    import glob
    for f in glob.glob(f"taxonomy/{DIR}/**/src/data/*.json", recursive=True):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        fname = (d.get("name") or "").strip().lower()
        fam_paths[fname] = f
        for g in d.get("children") or []:
            if g.get("rank") == "GENUS":
                genus_family.setdefault((g.get("name") or "").strip().lower(), f)
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
        while f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(nm).upper()}_{n}" in used_ids:
            n += 1
        cand = f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(nm).upper()}_{n}"
        used_ids.add(cand)
        return cand

    # ---- bucket species into A (existing family) / B (new family) / C (none) ----
    existing_kids = collections.defaultdict(list)
    new_kids = collections.defaultdict(list)
    nofam_kids = []
    for t in scope:
        if rank.get(t) != "species":
            continue
        nm = name.get(t)
        if not looks_binomial(nm) or nm.strip().lower() in canon:
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
            continue
        fkey = (name.get(fam) or "").strip().lower()
        if fkey in fam_paths:
            existing_kids[fkey].append(t)
        else:
            new_kids[fam].append(t)

    n_a = sum(len(v) for v in existing_kids.values())
    n_b = sum(len(v) for v in new_kids.values())
    print(f"  A existing families: {len(existing_kids):,} families, {n_a:,} species")
    print(f"  B new families:      {len(new_kids):,} families, {n_b:,} species")
    print(f"  C no family in NCBI: {len(nofam_kids):,} species")

    raw = sorted({name[t] for kids in
                  list(existing_kids.values()) + list(new_kids.values()) + [nofam_kids]
                  for t in kids})
    print(f"  normalising {len(raw):,} names through GNparser ...", flush=True)
    parsed = taxamatch.parse_names(raw)
    placed = set()

    def canonical(nm):
        g, s = taxamatch.bare_binomial(nm, parsed)
        if not g or not s:
            return None, None
        bare = taxamatch.bare_name(nm, parsed)
        for form in (bare, f"{g} ×{s}", f"{g} × {s}"):
            if form.lower() in canon or form.lower() in placed:
                return None, None
        placed.add(bare.lower())
        return bare, g

    new_orders = []
    counters = {"written": 0, "skipped": 0, "unplaced": 0}

    def place(phylum, klass, order, fname, kids, path=None):
        fslug = SF.slug(fname)
        if path is None and not phylum:
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
        n_species = sum(len(v) for v in genus_of.values())

        if path is None:
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
            if existing is None:
                fam_id = new_id("FAM", fname, [x for x in (phylum, klass, order) if x])
                existing = {"id": fam_id, "name": fname, "rank": "FAMILY",
                            "appSlug": fslug, "speciesCount": n_species}
                parent.setdefault("children", []).append(existing)
            else:
                fam_id = existing.get("id")
                existing["speciesCount"] = (existing.get("speciesCount") or 0) + n_species
            seg = [DIR, dirname(phylum), dirname(klass), dirname(order), fslug]
            target = os.path.join("taxonomy", *seg, "src", "data", f"{fslug}.json")
        else:
            target = path
            fam_id = None

        new_root = {"id": fam_id, "name": fname, "rank": "FAMILY", "children": [],
                    "speciesCount": n_species, "appSlug": fslug, "sourcedFrom": SOURCE}
        for g, species in genus_of.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
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
            m = SF.merge_family(old, new_root, kingdom=DIR, family_slug=fslug)
            root = old
            if m.get("authority_conflicts"):
                print(f"  ! {fslug}: {m['authority_conflicts']} authority conflicts")
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

    # part C: no family in NCBI -> resolve by genus, else Incertae sedis
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

    # part B: families NCBI names that we lack
    targets = sorted(new_kids.items(), key=lambda kv: -len(kv[1]))
    for fam, kids in targets:
        fname = (name.get(fam) or "").strip()
        if not fname:
            continue
        ch = chain(fam)
        place((ch.get("phylum") or "").strip(), (ch.get("class") or "").strip(),
              (ch.get("order") or "").strip(), fname, kids)

    print(f"\n  family files written/merged: {counters['written']:,}")
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
