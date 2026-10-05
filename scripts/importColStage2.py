#!/usr/bin/env python3
"""Catalogue of Life, Stage 2: families we do not have yet.

Stage 1 (importColBreadth.py) took the 427,804 species COL holds in families
already in the tree, which needed no scaffolding. It ran on animalia only, so
the other kingdoms' family files have never been enriched against COL. This
takes everything Stage 1 left, in three parts:

  A. species whose COL family we already have   -> merge into that family file
  B. species in families COL has and we do not  -> scaffold + new family file
  C. species COL records with no family at all  -> genus lookup, else placeholder

Verified scope for Fungi + Chromista (the pair imported first), measured with
this script's own bucketing against the current tree:

    A existing families      64 families      751 species staged
    B new families          652 families   24,535 species
    C no family in COL                       8,416 species
                                 -> 348 resolved to an existing genus's family
                                 -> 8,068 into 117 'Incertae sedis' families
    Result: ~32,950 new species, of which 350 land in existing families.

Two earlier drafts of this docstring carried a per-kingdom table quoting
701,564 Animalia / 9,952 Fungi / 22,994 Chromista species and 6,294 / 357 /
320 families. All of it was wrong and none of it should be trusted:

- The family counts were impossible. COL holds 10,507 Animalia families, and
  we already hold 990 chromist families against COL's 776, so "320 new chromist
  families" cannot be true.
- The "existing families" column was inflated by subgenus trinomials. COL
  writes `Aloconota (Aloconota) tenerrima`; we store `Aloconota tenerrima`.
  Compared as raw strings they look like 400,000 missing animalia species;
  normalised through GNparser, 95,915 of them become 22. Comparing before
  normalising is the single easiest way to get this number wrong.
- Animalia, Plantae, Protozoa and Archaea have not been re-measured with the
  corrected logic. Re-run with `--kingdom X` and read the A/B/C lines rather
  than trusting any table copied from here.

COL supplies a rank chain for most families, so the tree path is derived from
COL rather than guessed. Two cases need a decision rather than a default:

- **Families with no order, and species with no family.** COL does not always
  use the rank. Rather than invent a placement, they go under an order or family
  literally named `Incertae sedis` (common name "Unplaced"). Inventing a
  plausible-looking order would assert something nobody knows; an explicit
  placeholder asserts only that we could not place it. For part C we try
  harder first: the genus is usually known, and if that genus already exists in
  the tree the species joins the family it is already in.
- **The kingdom is taken from COL's own rank**, so bacteria and viruses arrive as
  their own kingdoms and need adding to kingdom-config.json before they can
  build. `--kingdom` filters, and the run refuses a kingdom the config does not
  declare rather than writing data nothing will ever load.

Names go through the same GNparser normalisation Stage 1 uses, including all
three spellings of the hybrid marker -- COL spaced, GNparser spaced, our data
tight, and COL sometimes omitting it. That was three separate duplicate-generating
bugs in Stage 1 and they are all handled in one place here.

Usage:
    python3 scripts/importColStage2.py --kingdom Fungi --kingdom Chromista
    python3 scripts/importColStage2.py --kingdom Fungi --apply
    python3 scripts/importColStage2.py --kingdom Animalia --apply --limit-families 50
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonicalNames as C  # noqa: E402
import importSpeciesFile as SF  # noqa: E402
import taxamatch  # noqa: E402

COL = ("/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/"
       "col2026-base_dwca.zip")
ACCEPTED = {"accepted", "provisionally accepted"}
SOURCE = "catalogue of life"
KINGDOM_CONFIG = "portal/data/kingdom-config.json"
UNPLACED = "Incertae sedis"

# COL's rank names to ours, and the order they sit in from the kingdom down.
CHAIN = ("phylum", "class", "order")
RANK_NODE = {"phylum": "PHYLUM", "class": "CLASS", "order": "ORDER"}


def dirname(name):
    """Mirror of dirName() in portal/scripts/lib/familyPath.ts.

    The graft finds a family by walking its rank path, lowercasing each rank
    and turning whitespace into underscores. SF.slug() turns the same
    characters into hyphens, so a directory built with it is one the graft
    never looks in. Single-word rank names are unaffected, which is why this
    stayed hidden until the 'Incertae sedis' placeholder order arrived -- the
    first rank name with a space in it, and 113 families were unreachable.
    """
    return re.sub(r"\s+", "_", (name or "").lower())


def load_col():
    par, rank, name, auth = {}, {}, {}, {}
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
            auth[t] = p[ci["dwc:scientificNameAuthorship"]]
    return par, rank, name, auth


def index_taxonomy(tax):
    """(rank, name) -> node, globally. Names are unique enough in practice and a
    collision across two kingdoms is reported rather than silently merged."""
    by_name = collections.defaultdict(list)

    def walk(n):
        r = n.get("rank")
        if r:
            by_name[(r, (n.get("name") or "").strip().lower())].append(n)
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    return by_name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", action="append", default=[],
                    help="COL kingdom name; repeatable. Defaults to Fungi and "
                         "Chromista, the smallest pair that exercises the path.")
    ap.add_argument("--limit-families", type=int, default=0)
    args = ap.parse_args()

    kingdoms = args.kingdom or ["Fungi", "Chromista"]
    cfg = json.load(open(KINGDOM_CONFIG, encoding="utf-8"))
    declared = set(cfg["kingdoms"]) if isinstance(cfg, dict) else {k["id"] for k in cfg}
    # COL capitalises; the config is lower-case.
    for k in kingdoms:
        if k.lower() not in declared:
            sys.exit(f"FATAL: kingdom {k!r} is not declared in {KINGDOM_CONFIG}.\n"
                     f"       Declared: {', '.join(sorted(declared))}\n"
                     f"       COL groups bacteria and viruses as separate kingdoms, "
                     f"which need adding there before they can be built.")

    idx = C._load()
    canon = set(idx.keys()) | set(idx.values())
    par, rank, name, auth = load_col()
    print(f"  COL accepted taxa: {len(par):,}")

    def chain(tid):
        out = {}
        for w in ("kingdom", "superkingdom", "domain") + CHAIN:
            c, n = tid, 0
            while c and n < 60:
                if rank.get(c) == w:
                    out[w] = name.get(c)
                    break
                c = par.get(c)
                n += 1
        return out

    # Each kingdom has its own taxonomy file; portal/data/taxonomy.json is
    # animalia only, so the other kingdoms are not reachable from one root.
    kcfg = cfg["kingdoms"]
    tax_files = {}
    for k in kingdoms:
        rel = kcfg[k.lower()]["input"]
        path = os.path.join("portal", rel)
        if not os.path.exists(path):
            sys.exit(f"FATAL: {path} not found for kingdom {k}")
        tax_files[k] = json.load(open(path, encoding="utf-8"))
    print("  taxonomy files: " + ", ".join(
        f"{k} -> {os.path.join('portal', kcfg[k.lower()]['input'])}" for k in tax_files))

    # On-disk families, keyed by (kingdom, family name) so a name shared by two
    # kingdoms cannot be merged into the wrong one. Also a genus -> family map,
    # which is what lets a family-less COL species find its family (part C).
    fam_paths = collections.defaultdict(list)
    genus_family = {}
    for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        if "node_modules" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("rank") != "FAMILY":
            continue
        king = f.split("/")[1]
        fname = (d.get("name") or "").strip().lower()
        fam_paths[(king, fname)].append(f)
        for g in d.get("children") or []:
            if g.get("rank") == "GENUS":
                genus_family.setdefault((king, (g.get("name") or "").strip().lower()), f)

    # ---- bucket every in-scope species into A / B / C ----
    existing_kids = collections.defaultdict(list)      # A: family we have
    fam_kids = collections.defaultdict(list)           # B: family we lack
    nofam_kids = []                                    # C: COL has no family
    for t, r in rank.items():
        if r != "species":
            continue
        nm = name[t]
        if not nm or nm.strip().lower() in canon:
            continue
        ch = chain(t)
        k = ch.get("kingdom") or ch.get("superkingdom") or ch.get("domain")
        if k not in kingdoms:
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
            nofam_kids.append(t)                       # C
            continue
        key = (k.lower(), (name.get(fam) or "").strip().lower())
        if key in fam_paths:
            existing_kids[key].append(t)               # A
        else:
            fam_kids[fam].append(t)                    # B

    n_existing = sum(len(v) for v in existing_kids.values())
    n_new = sum(len(v) for v in fam_kids.values())
    print(f"  A existing families: {len(existing_kids):,} families, {n_existing:,} species")
    print(f"  B new families:      {len(fam_kids):,} families, {n_new:,} species")
    print(f"  C no family in COL:  {len(nofam_kids):,} species")

    # normalise every name once, in one GNparser pass
    raw = sorted({name[t]
                  for kids in list(existing_kids.values()) + list(fam_kids.values()) + [nofam_kids]
                  for t in kids})
    print(f"  normalising {len(raw):,} names through GNparser ...", flush=True)
    parsed = taxamatch.parse_names(raw)

    # Names claimed during this run. COL regularly places one genus in more
    # than one family -- Acantha lands in several hymenopteran families,
    # Abbreviata in several others -- and the canonical index cannot see that,
    # because it is a snapshot taken before the run. Without this, each of those
    # species is written into every family COL offers it under, and 3,472 ids
    # end up duplicated across the tree after an Animalia run. First placement
    # wins, and part A runs before parts B and C so that an existing family
    # beats a new one for a contested name: we would rather add a species to a
    # family we already hold than start a second one to hold the same name.
    placed = set()

    def canonical(nm):
        """COL name -> our bare name, or None if it is not binominal."""
        p = parsed.get(nm) or {}
        g, s = p.get("genus"), p.get("species")
        if not s:
            parts = [x for x in nm.replace("\u00d7", " ").split()
                     if x.lower() != "x"]
            if len(parts) >= 2:
                g, s = parts[0], parts[1]
        if not g or not s:
            return None, None
        bare = f"{g} \u00d7{s}" if "\u00d7" in nm else f"{g} {s}"
        for form in (bare, f"{g} {s}", f"{g} \u00d7{s}", f"{g} \u00d7 {s}"):
            if form.lower() in canon or form.lower() in placed:
                return None, None                      # already held
        placed.add(bare.lower())
        return bare, g

    new_orders, unplaced = [], 0
    written = skipped = 0

    # ---- route part C, and turn part A into per-file buckets ----
    #
    # Path A buckets are keyed by family name, but the write is per file, and a
    # family name can in principle exist twice in one kingdom. Resolving A and
    # C-resolved into one path-keyed map means the merge below runs once per
    # file and cannot double-count a species that arrived by both routes.
    path_kids = collections.defaultdict(list)
    ambiguous = 0
    for (king, fkey), kids in existing_kids.items():
        paths = fam_paths[(king, fkey)]
        if len(paths) != 1:
            ambiguous += len(kids)
            continue
        path_kids[paths[0]].extend(kids)

    c_resolved = c_unresolved = 0
    incerta = collections.defaultdict(list)          # C, no family we can find
    for t in nofam_kids:
        bare, g = canonical(name[t])
        if bare is None:
            skipped += 1
            continue
        ch = chain(t)
        k = ch.get("kingdom") or ch.get("superkingdom") or ch.get("domain") or ""
        hit = genus_family.get((k.lower(), (g or "").strip().lower()))
        if hit:
            path_kids[hit].append(t)
            c_resolved += 1
            continue
        c_unresolved += 1
        phylum = (ch.get("phylum") or "").strip()
        klass = (ch.get("class") or "").strip()
        order = (ch.get("order") or "").strip() or UNPLACED
        if not phylum and not klass:
            skipped += 1
            continue
        incerta[(k, phylum, klass, order)].append(t)

    if ambiguous:
        print(f"  ! {ambiguous:,} species skipped: family name matches several "
              f"files in one kingdom")
    print(f"  C resolved to an existing family:  {c_resolved:,}")
    print(f"  C needing an 'Incertae sedis' family: {c_unresolved:,} "
          f"in {len(incerta):,} placements")

    counters = {"written": 0, "skipped": 0, "unplaced": 0}

    used_ids = set()

    def collect_ids(node):
        if node.get("id"):
            used_ids.add(node["id"])
        for c in node.get("children") or []:
            collect_ids(c)

    for _t in tax_files.values():
        collect_ids(_t)

    def new_id(prefix, name, ancestry=()):
        """An id no other node holds.

        `SF.node_id` builds from the name alone, which is unique for a real taxon
        name and useless for a placeholder: every order COL declines to name
        became `ORDER_INCERTAE_SEDIS`, 21 of them in animalia and 21 more in
        fungi, and the manifest keys order files by order id, so 20 of each went
        into the same file and the families under them became unreachable. On a
        collision, qualify with the ancestry the way the tree already does for
        `SCAPHOPODA_UNKNOWN` -- the parent's name, then further out. Mirrors
        scripts/fix_duplicate_node_ids.py, which repaired the ids this produced.
        """
        base = SF.node_id(prefix, name)
        if base not in used_ids:
            used_ids.add(base)
            return base
        for depth in (1, 2, 3):
            anc = [a for a in ancestry[-depth:] if a]
            cand = "_".join([SF.slug(a).upper() for a in reversed(anc)]
                            + [SF.slug(name).upper()])
            if cand not in used_ids:
                used_ids.add(cand)
                return cand
        n = 2
        while f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(name).upper()}_{n}" in used_ids:
            n += 1
        cand = f"{SF.slug(ancestry[-1]).upper()}_{SF.slug(name).upper()}_{n}"
        used_ids.add(cand)
        return cand

    def place(kingdom, phylum, klass, order, fname, kids, placeholder=False):
        """Scaffold phylum/class/order/family and write the family file.

        Shared by part B (a family COL names that we lack) and by the part C
        leftovers (species we can neither match to a genus nor to a family).
        """
        fslug = SF.slug(fname)
        if not phylum or not klass:
            counters["skipped"] += 1
            return
        if not order:
            order = UNPLACED
            counters["unplaced"] += 1
        # COL's class is sometimes absent for invertebrates; fall back to phylum
        if not klass:
            klass = phylum
            phylum = ""

        genus_of = {}
        nodes = []
        # One node per (genus, name) per family. COL offers the same species
        # twice more often than you would hope -- sometimes as a literal
        # duplicate row with identical authorship, sometimes as one accepted
        # name per competing authorship (`Saccammina grzybowskii Schubert, 1902`
        # and `... Bogdanovich, 1960`). Neither can become two nodes in one
        # genus, and the sanity scan counts the second as a duplicate species.
        seen = set()
        for t in kids:
            nm = name[t]
            bare, g = canonical(nm)
            if bare is None:
                counters["skipped"] += 1
                continue
            key = (g, bare.lower())
            if key in seen:
                counters["skipped"] += 1
                continue
            seen.add(key)
            genus_of.setdefault(g, []).append((bare, (auth.get(t) or "").strip() or None))
            nodes.append(bare)
        if not nodes:
            return

        # build the taxonomy chain
        ktax = tax_files.get(kingdom)
        if ktax is None or (ktax.get("rank") or "").upper() != "KINGDOM":
            print(f"  no KINGDOM root for {kingdom!r}; skipping {fname}")
            counters["skipped"] += 1
            return
        king_node = ktax
        parent = king_node
        for _tag_i, label in enumerate((("phylum", phylum), ("class", klass),
                                         ("order", order))):
            _tag, val = label
            if not val:
                continue
            found = next((c for c in (parent.get("children") or [])
                          if c.get("rank") == RANK_NODE[_tag]
                          and (c.get("name") or "").lower() == val.lower()), None)
            if found is None:
                chain_names = [n for n in (phylum, klass, order) if n]
                found = {"id": new_id(RANK_NODE[_tag], val, chain_names[:_tag_i + 1]),
                         "name": val, "rank": RANK_NODE[_tag]}
                if _tag == "order":
                    found["commonName"] = "Unplaced" if order == UNPLACED else None
                    if found["commonName"] is None:
                        del found["commonName"]
                    found["extinct"] = False
                    found["fossil"] = False
                    new_orders.append(val)
                parent.setdefault("children", []).append(found)
            parent = found

        # Match on the slug, not the name. SF.slug() strips the extinct marker,
        # so a family we already hold as "\u2020Protodiplatyidae" and the same
        # family from COL as "Protodiplatyidae" are one directory with two
        # possible names -- matching on the name created a parallel node with a
        # colliding appSlug, and testFamilyPaths flagged 31 such duplicates.
        # Comparing slugs also folds the pre-existing case where the Cebidae
        # node and data file are misnamed "Platyrrhini" but hold Cebidae.
        existing = next((c for c in (parent.get("children") or [])
                         if c.get("rank") == "FAMILY"
                         and SF.slug(c.get("name") or "") == fslug), None)
        if existing is None:
            # Minted once and reused for the data file's root below: calling
            # new_id twice would hand out two ids, because the first one is by
            # then taken.
            fam_id = new_id("FAM", fname, [x for x in (phylum, klass, order) if x])
            existing = {"id": fam_id, "name": fname, "rank": "FAMILY",
                        "appSlug": fslug, "speciesCount": len(nodes)}
            parent.setdefault("children", []).append(existing)
        else:
            fam_id = existing.get("id")
            existing["speciesCount"] = (existing.get("speciesCount") or 0) + len(nodes)

        # the data file
        seg = [kingdom.lower()]
        if phylum:
            seg.append(dirname(phylum))
        seg.append(dirname(klass))
        seg.append(dirname(order))
        seg.append(fslug)
        d = os.path.join("taxonomy", *seg, "src", "data")
        if args.apply:
            os.makedirs(d, exist_ok=True)
        target = os.path.join(d, f"{fslug}.json")

        root = {"id": fam_id, "name": fname, "rank": "FAMILY",
                "children": [], "speciesCount": len(nodes), "appSlug": fslug,
                "sourcedFrom": SOURCE}
        lin = " > ".join(x for x in (
            phylum and SF.nodename(phylum), klass and SF.nodename(klass)) if x)
        if lin:
            root["lineage"] = lin
        buckets = {"GENUS": {}}
        for g, species in genus_of.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
            buckets["GENUS"][g] = gnode
            root["children"].append(gnode)
            for nm2, a in species:
                # lineage is the immediate parent's name: the order on a FAMILY
                # node (see annotatePortalLevels), the family on a GENUS node, the
                # GENUS on a species node. Writing fname here put the family on
                # ~900k species, and because a species always lives in a file
                # named for its family the wrong value reads as correct.
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm2, a or ""),
                      "name": nm2, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
                gnode["children"].append(sp)
        root["genusCount"] = len(buckets["GENUS"])

        if os.path.exists(target):
            old = json.load(open(target, encoding="utf-8"))
            SF.merge_family(old, root)
            root = old
        if args.apply:
            with open(target, "w", encoding="utf-8") as fh:
                json.dump(root, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        counters["written"] += 1

    # ---- part A: enrich family files we already have ----
    #
    # Identical to what Stage 1 did, because it is the same operation: hand
    # merge_family a synthetic root of genus/species and let it add only what is
    # missing. Stage 1 never ran on these kingdoms, which is why 680 of our
    # families are still short of COL.
    a_added = a_dedup = 0
    for path in sorted(path_kids):
        kids = path_kids[path]
        try:
            existing = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR {path}: {e}")
            continue
        fam_name = existing.get("name") or ""
        new_root = {"id": existing.get("id"), "name": fam_name,
                    "rank": "FAMILY", "children": []}
        genera = {}
        staged = 0
        seen = set()
        for t in kids:
            bare, g = canonical(name[t])
            if bare is None:
                skipped += 1
                continue
            key = (g, bare.lower())
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            gnode = genera.get(g)
            if gnode is None:
                gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                         "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                         "lineage": fam_name}
                genera[g] = gnode
                new_root["children"].append(gnode)
            a = (auth.get(t) or "").strip() or None
            sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], bare, a or ""),
                  "name": bare, "rank": "SPECIES", "subspeciesCount": 0,
                  "sourcedFrom": SOURCE, "lineage": g}
            if a:
                sp["authorship"] = a
            gnode["children"].append(sp)
            staged += 1
        if not staged:
            continue
        m = SF.merge_family(existing, new_root)
        a_added += m["species_added"]
        a_dedup += m["species_deduped"]
        if args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(existing, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    # ---- part C leftovers: one 'Incertae sedis' family per placement ----
    for (k, phylum, klass, order), kids in sorted(incerta.items()):
        place(k, phylum, klass, order, UNPLACED, kids, placeholder=True)

    # ---- part B: families COL names and we lack ----
    targets = sorted(fam_kids.items(), key=lambda kv: -len(kv[1]))
    if args.limit_families:
        targets = targets[:args.limit_families]
    for fam, kids in targets:
        fname = (name.get(fam) or "").strip()
        if not fname:
            continue
        ch = chain(fam)
        place((ch.get("kingdom") or ch.get("superkingdom")
               or ch.get("domain") or "").strip(),
              (ch.get("phylum") or "").strip(),
              (ch.get("class") or "").strip(),
              (ch.get("order") or "").strip(),
              fname, kids)

    print(f"\n  new family files written:      {counters['written']:,}")
    print(f"  existing family files merged:   {len(path_kids):,}")
    print(f"  species added:                  {a_added:,}")
    print(f"  already present, merged:        {a_dedup:,}")
    print(f"  species skipped (unbinominal or already held): {skipped + counters['skipped']:,}")
    print(f"  families placed under '{UNPLACED}': {counters['unplaced']:,}")
    print(f"  new ORDER nodes:   {len(new_orders):,}")
    if new_orders:
        print("   ", ", ".join(sorted(set(new_orders))[:14]))

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0
    for k, ktax in tax_files.items():
        path = os.path.join("portal", kcfg[k.lower()]["input"])
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(ktax, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    with open("/tmp/col-stage2-orders.json", "w", encoding="utf-8") as fh:
        json.dump(sorted(set(new_orders)), fh, indent=1)
    print("\n  wrote " + ", ".join(
        os.path.join("portal", kcfg[k.lower()]["input"]) for k in tax_files)
        + " and /tmp/col-stage2-orders.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())