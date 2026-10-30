#!/usr/bin/env python3
"""Scaffold families the taxonomy lacks, from the GBIF backbone.

The importers refuse every species whose family we do not hold (see
`importColChecklist.route_species`), recording the miss in the pending-family
store. This script is the other half of that loop: it takes the families the
backbone offers and we lack, and creates the taxonomy node and empty data file
so a normal re-import can place their species.

Nothing taxonomic is invented. The family name, its kingdom/phylum/class/order
chain and its species count all come from the GBIF backbone (CC0 / CC BY /
CC BY-NC, per constituent dataset); when the backbone leaves an intermediate
rank empty, the family is placed at the nearest rank it does state rather than
having a class or order manufactured for it (the same rule that keeps
Tardigrada at KINGDOM > PHYLUM > FAMILY).

Species are NOT imported here. The scaffold only adds a FAMILY node with
`appSlug` and an empty `<slug>.json`, which is exactly what
`importColChecklist.py` needs in order to stop refusing that family:

    python3 scripts/scaffoldFamilies.py --kingdom archaea            # dry run
    python3 scripts/scaffoldFamilies.py --kingdom archaea --apply
    python3 scripts/importColChecklist.py <backbone.zip> --apply

The species count is read from the backbone in the same streaming pass that
finds the family rows, not from the pending store: the store is seeded by hand
(`pendingFamilies.py seed`) and goes stale as imports reshape the tree. The
archaea run on 2026-10-21 was scaffolded from 16-day-old rows claiming 17-63
species for families the current backbone gives 0-1, so re-seed the store when
the worklist itself starts looking wrong:

    python3 scripts/pendingFamilies.py seed

Bacteria and viruses are scaffolded like any other kingdom since 2026-10-30
(only the portal stays on hold for them -- see CLAUDE.md), into
`portal/data/taxonomy-{bacteria,viruses}.json`, never kingdom-config.json.
Every kingdom is subject to the writer partition (scripts/writerKingdoms.py):
on Macie those two are q-bert's, so scaffolding them there exits non-zero.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources as _sources  # noqa: E402
import writerKingdoms as WK  # noqa: E402
from importColChecklist import BACTERIA_VIRUSES_INPUT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINGDOM_CONFIG = os.path.join(ROOT, "portal", "data", "kingdom-config.json")
PENDING = os.path.join(_sources.ROOT, "pending", "families.jsonl")
BACKBONE = os.path.join(_sources.ROOT, "archives", "gbif-backbone", "backbone.zip")
SOURCE = "gbif-backbone"
SKIP_NAMES = {"", "(no family)", "incertae sedis", "incertae-sedis"}
PREFIX = {"realm": "RLM", "kingdom": "KNG", "phylum": "PHY", "class": "CLS", "order": "ORD"}
RULES = os.path.join(ROOT, "data", "kingdom-rules.json")


def taxonomy_input(kingdom: str) -> str:
    if kingdom in BACTERIA_VIRUSES_INPUT:
        return os.path.join(ROOT, "portal", BACTERIA_VIRUSES_INPUT[kingdom])
    cfg = json.load(open(KINGDOM_CONFIG, encoding="utf-8"))["kingdoms"]
    if kingdom not in cfg:
        sys.exit(f"FATAL: kingdom {kingdom!r} is not in kingdom-config.json "
                 f"({', '.join(sorted(cfg))})")
    return os.path.join(ROOT, "portal", cfg[kingdom]["input"])


def slugify(name: str) -> str:
    s = re.sub(r"\s+", "_", (name or "").strip().lower())
    s = re.sub(r"[^a-z0-9_-]", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-_")


def node_id(prefix: str, name: str) -> str:
    return prefix + "_" + re.sub(r"[^A-Z0-9]+", "_", (name or "").upper()).strip("_")


def child_by_name(parent: dict, name: str) -> dict | None:
    want = (name or "").strip().lower()
    for c in parent.get("children") or []:
        if (c.get("name") or "").strip().lower() == want:
            return c
    return None


def held_families(tax: dict) -> set[str]:
    out = set()

    def walk(n):
        if n.get("rank") == "FAMILY":
            out.add((n.get("name") or "").strip().lower())
        for c in n.get("children") or []:
            walk(c)

    walk(tax)
    return out


def pending_rows(kingdom: str) -> dict[str, dict]:
    """family-name-lower -> pending row, for the GBIF backbone rows of one kingdom."""
    out = {}
    if not os.path.exists(PENDING):
        return out
    with open(PENDING, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not (r.get("source") or "").startswith(SOURCE):
                continue
            if (r.get("kingdom") or "").strip().lower() != kingdom:
                continue
            fam = (r.get("family") or "").strip()
            if fam.lower() in SKIP_NAMES:
                continue
            out[fam.lower()] = r
    return out


def backbone_chains(wanted: set[str]) -> tuple[dict[str, dict], dict[str, int]]:
    """Stream Taxon.tsv once and return family-name-lower -> chain, plus the
    number of accepted species/subspecies the backbone assigns to each family.

    The species count is counted here rather than taken from the pending store
    because that store is seeded by hand (`pendingFamilies.py seed`): the
    archaea rows used on 2026-10-21 were 16 days old and claimed 17-63 species
    for families the current backbone gives 0-1. A family was scaffolded on a
    number nobody had re-checked since the COL import reshaped the tree.

    When a family has several rows, an accepted one with a populated chain
    wins.
    """
    if not os.path.exists(BACKBONE):
        sys.exit(f"FATAL: backbone archive not found at {BACKBONE}")
    csv.field_size_limit(10**9)
    out: dict[str, dict] = {}
    counts: dict[str, int] = {}
    z = zipfile.ZipFile(BACKBONE)
    try:
        fh = io.TextIOWrapper(z.open("Taxon.tsv"), encoding="utf-8")
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            fam = (row.get("family") or "").strip()
            if not fam or fam.lower() not in wanted:
                continue
            rank = (row.get("taxonRank") or "").strip().lower()
            status = (row.get("taxonomicStatus") or "").strip().lower()
            if rank in ("species", "subspecies") and status in (
                    "accepted", "provisionally accepted"):
                counts[fam.lower()] = counts.get(fam.lower(), 0) + 1
                continue
            if rank != "family":
                continue
            rec = {
                "family": fam,
                "kingdom": (row.get("kingdom") or "").strip(),
                "phylum": (row.get("phylum") or "").strip(),
                "class": (row.get("class") or "").strip(),
                "order": (row.get("order") or "").strip(),
                "status": status,
                "id": (row.get("taxonID") or "").strip(),
            }
            key = fam.lower()
            prior = out.get(key)
            if prior is None or (
                rec["status"] == "accepted"
                and sum(bool(rec[k]) for k in ("phylum", "class", "order"))
                > sum(bool(prior[k]) for k in ("phylum", "class", "order"))
            ):
                out[key] = rec
    finally:
        z.close()
    return out, counts


def ensure_path(root: dict, chain: dict) -> tuple[dict, list[str]]:
    """Return (parent node, names created) for the ranks above the family."""
    created = []
    parent = root
    for rank in ("phylum", "class", "order"):
        name = chain.get(rank)
        if not name:
            continue
        node = child_by_name(parent, name)
        if node is None:
            node = {"id": node_id(PREFIX[rank], name), "name": name,
                    "rank": rank.upper(), "children": []}
            parent.setdefault("children", []).append(node)
            created.append(f"{rank.upper()} {name}")
        parent = node
    return parent, created


def write_family_file(kingdom: str, parent_names: list[str], family: str,
                      fid: str, app_slug: str, dry_run: bool) -> str:
    parts = [kingdom]
    for n in parent_names:
        parts.append(re.sub(r"\s+", "_", n.strip().lower()))
    parts.append(app_slug)
    rel = os.path.join("taxonomy", *parts, "src", "data", app_slug + ".json")
    path = os.path.join(ROOT, rel)
    if dry_run:
        return rel
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"id": fid, "name": family, "rank": "FAMILY",
                       "appSlug": app_slug, "speciesCount": 0,
                       "children": []}, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return rel


def load_rules() -> dict:
    with open(RULES, encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


def all_pending_families(kingdom: str) -> dict[str, list[str]]:
    """family-name-lower -> sources that refused it, every source. The GBIF
    Backbone worklist above only sees the Backbone's own refusals; for a
    rules kingdom the NCBI, ENA and GTDB runs' refusals count too."""
    out: dict[str, list[str]] = {}
    if not os.path.exists(PENDING):
        return out
    with open(PENDING, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("kingdom") or "").strip().lower() != kingdom:
                continue
            fam = (r.get("family") or "").strip()
            if fam.lower() in SKIP_NAMES:
                continue
            out.setdefault(fam.lower(), []).append(r.get("source") or "?")
    return out


def authority_chains(archive: str, ranks: list[str]):
    """-> (family-name-lower -> {"family", "chain": [(rank, name)], "problem"},
    family-name-lower -> accepted species count) from one ColDP/DwCA archive.
    The chain keeps only `ranks`, top first. `problem` is set when the
    authority itself places the family inside another family (ICTV 1014 does
    this for Adintoviridae), which is not a placement to copy."""
    import colChecklist as K
    taxa = K.load_cached(archive)[0]
    by_id = {t["id"]: t for t in taxa}
    fams = {}
    for t in taxa:
        if (t.get("rank") or "").lower() != "family" or t.get("is_synonym"):
            continue
        chain, problem, p = [], "", t.get("parent")
        seen = set()
        while p in by_id and p not in seen:
            seen.add(p)
            n = by_id[p]
            r = (n.get("rank") or "").lower()
            if r == "family":
                problem = f"the authority places it inside family {n['name']}"
            if r in ranks:
                chain.append((r, n["name"]))
            p = n.get("parent")
        chain.reverse()
        key = t["name"].lower()
        prior = fams.get(key)
        if prior is None or (prior["problem"] and not problem):
            fams[key] = {"family": t["name"], "chain": chain, "problem": problem, "id": t["id"]}
    # Accepted species per family: walk each species up to its family.
    fam_ids = {v["id"]: k for k, v in fams.items()}
    counts: dict[str, int] = {}
    for t in taxa:
        if (t.get("rank") or "").lower() != "species" or t.get("is_synonym"):
            continue
        p, hops = t.get("parent"), 0
        while p in by_id and hops < 12:
            if p in fam_ids:
                counts[fam_ids[p]] = counts.get(fam_ids[p], 0) + 1
                break
            p, hops = by_id[p].get("parent"), hops + 1
    return fams, counts


def scaffold_by_rules(kingdom: str, rules: dict, apply_: bool) -> int:
    """Scaffold from the kingdom's own authority under data/kingdom-rules.json.

    Measured 2026-10-30: the GBIF Backbone's bacteria chains use older and
    GTDB placeholder names (Proteobacteria, Firmicutes_A..D) where this tree,
    built from NCBI, holds Pseudomonadota and Bacillota, and its virus chains
    revive the abolished Caudovirales. Scaffolding from it would have built
    parallel phyla next to the ones we hold. Here every name comes from the
    authority, the path is followed from the KINGDOM node down so a new
    family joins the branch the authority names (never a same-named node
    elsewhere), and a new top rank is reported rather than created."""
    tax_path = taxonomy_input(kingdom)
    tax = json.load(open(tax_path, encoding="utf-8"))
    held = held_families(tax)
    pend = all_pending_families(kingdom)
    wanted = {f for f in pend if f not in held}
    auth = rules["authority"]
    archive = os.path.join(_sources.ROOT, "archives", auth["key"], "archive.zip")
    if not os.path.exists(archive):
        sys.exit(f"FATAL: authority archive not found at {archive}")
    rejects = [(re.compile(r["pattern"]), r["why"]) for r in rules.get("rejectNames", [])]
    ranks = rules["ranks"]

    print(f"  kingdom:         {kingdom}")
    print(f"  taxonomy input:  {tax_path}")
    print(f"  authority:       {auth['title']} ({auth['key']}, {auth['licence']})")
    print(f"  pending families (all sources): {len(pend):,}   already held: "
          f"{len(pend) - len(wanted):,}   to consider: {len(wanted):,}")
    if not wanted:
        print("  nothing to scaffold")
        return 0

    fams, spp = authority_chains(archive, ranks)
    refused: dict[str, list[str]] = {}
    added = []

    def refuse(why, fam):
        refused.setdefault(why, []).append(fam)

    for key in sorted(wanted):
        rec = fams.get(key)
        if rec is None:
            refuse(f"not a family in {auth['key']}", key)
            continue
        if rec["problem"]:
            refuse(rec["problem"], rec["family"])
            continue
        bad = next((why for rx, why in rejects
                    for n in [rec["family"]] + [n for _, n in rec["chain"]] if rx.search(n)), None)
        if bad:
            refuse(bad, rec["family"])
            continue
        chain = rec["chain"]
        if not chain and rules.get("unassigned") != "kingdom":
            refuse("the authority gives no rank above it", rec["family"])
            continue
        parent, created, why = tax, [], ""
        for i, (rank, nm) in enumerate(chain):
            node = child_by_name(parent, nm)
            if node is None:
                if i == 0 and not rules.get("createTopRank"):
                    why = f"would need a new {rank} ({nm})"
                    break
                node = {"id": node_id(PREFIX[rank], nm), "name": nm,
                        "rank": rank.upper(), "children": []}
                parent.setdefault("children", []).append(node)
                created.append(f"{rank.upper()} {nm}")
            parent = node
        if why:
            refuse(why, rec["family"])
            continue
        if child_by_name(parent, rec["family"]):
            continue
        app_slug = slugify(rec["family"])
        fid = node_id("FAM", rec["family"])
        parent.setdefault("children", []).append({
            "id": fid, "name": rec["family"], "rank": "FAMILY",
            "appSlug": app_slug, "speciesCount": spp.get(key, 0),
            "scaffoldedFrom": auth["key"], "children": [],
        })
        rel = write_family_file(kingdom, [n for _, n in chain], rec["family"], fid,
                                app_slug, dry_run=not apply_)
        added.append((rec["family"], " > ".join(n for _, n in chain) or "(unassigned)",
                      spp.get(key, 0), created))

    for fam, chain, n, created in added:
        print(f"  + {fam:28s} {n:>7,} spp  {chain}")
        if created:
            print(f"      created intermediates: {', '.join(created)}")
    print(f"\n  families scaffolded: {len(added)}   species the authority gives them: "
          f"{sum(a[2] for a in added):,}")
    print(f"  refused: {sum(len(v) for v in refused.values()):,}")
    for why, names in sorted(refused.items(), key=lambda kv: -len(kv[1])):
        print(f"    {len(names):>5,}  {why}: {', '.join(sorted(names)[:6])}"
              f"{' …' if len(names) > 6 else ''}")
    if apply_ and added:
        text = json.dumps(tax, indent=2, ensure_ascii=False) + "\n"
        with open(tax_path + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tax_path + ".tmp", tax_path)
        print(f"  wrote {tax_path}")
    elif added:
        print("  (dry run -- pass --apply to write)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kingdom", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    kingdom = args.kingdom.strip().lower()
    if kingdom not in set(WK.portal_kingdoms()) | set(WK.BACTERIA_VIRUSES):
        sys.exit(f"FATAL: unknown kingdom {kingdom!r}")
    if not WK.may_write(kingdom):
        sys.exit(f"FATAL: {kingdom} is not this writer's kingdom "
                 f"(SN_WRITE_KINGDOMS={','.join(sorted(WK.allowed()))}); "
                 f"see scripts/writerKingdoms.py")

    rules = load_rules().get(kingdom)
    if rules:
        return scaffold_by_rules(kingdom, rules, args.apply)

    tax_path = taxonomy_input(kingdom)
    tax = json.load(open(tax_path, encoding="utf-8"))
    held = held_families(tax)
    pend = pending_rows(kingdom)
    wanted = {f for f in pend if f not in held}

    print(f"  kingdom:         {kingdom}")
    print(f"  taxonomy input:  {tax_path}")
    print(f"  pending GBIF families: {len(pend):,}   already held: {len(pend) - len(wanted):,}"
          f"   to scaffold: {len(wanted):,}")
    if not wanted:
        print("  nothing to scaffold")
        return 0

    chains, spp = backbone_chains(wanted)
    missing_chain = sorted(wanted - set(chains))
    if missing_chain:
        print(f"  ! {len(missing_chain):,} pending families have no family-rank "
              f"row in the backbone: {', '.join(missing_chain[:8])}"
              f"{' …' if len(missing_chain) > 8 else ''}")

    added = []
    for key in sorted(chains):
        rec = chains[key]
        if rec.get("kingdom") and rec["kingdom"].strip().lower() != kingdom:
            print(f"  ! {rec['family']}: backbone kingdom is {rec['kingdom']!r}, "
                  f"skipping")
            continue
        parent, created = ensure_path(tax, rec)
        if child_by_name(parent, rec["family"]):
            continue
        app_slug = slugify(rec["family"])
        fid = node_id("FAM", rec["family"])
        parent.setdefault("children", []).append({
            "id": fid,
            "name": rec["family"],
            "rank": "FAMILY",
            "appSlug": app_slug,
            "speciesCount": spp.get(key, 0),
            "children": [],
        })
        chain_names = [r for r in (rec.get("phylum"), rec.get("class"),
                                   rec.get("order")) if r]
        rel = write_family_file(kingdom, chain_names, rec["family"], fid,
                                app_slug, dry_run=not args.apply)
        added.append((rec["family"], " > ".join(chain_names) or "(no chain)",
                      spp.get(key, 0), rel, created))
        stale = int(pend[key].get("species") or 0)
        if stale and stale != spp.get(key, 0):
            print(f"  ! {rec['family']}: pending store says {stale:,} species, "
                  f"current backbone says {spp.get(key, 0):,} -- using the backbone")

    for fam, chain, n, rel, created in added:
        print(f"  + {fam:28s} {n:>7,} spp  {chain}")
        if created:
            print(f"      created intermediates: {', '.join(created)}")
    print(f"\n  families scaffolded: {len(added)}"
          f"   species this unlocks: {sum(a[2] for a in added):,}")
    if args.apply and added:
        with open(tax_path, "w", encoding="utf-8") as fh:
            json.dump(tax, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"  wrote {tax_path}")
    elif added:
        print("  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
