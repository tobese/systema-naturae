#!/usr/bin/env python3
"""
Measure what each projection of an order file would cost on the wire.

Why this exists
---------------
The portal serves one file per ORDER, and those files are wildly uneven: the
median animalia order file is 112KB and the largest is 86MB (COLEOPTERA, 134
families / 15,168 genera / 151,512 species entries). The client caches a few
at a time, so a reader clicking through the big orders holds 100-200MB of JSON
and pays several times that again in JSON.parse heap. gzip already makes the
*transfer* cheap - COLEOPTERA is 5.4MB over the wire - so the cost is the parse,
not the download, and no amount of server-side help changes that unless the
client stops parsing the whole order.

But the two surfaces want different things from the same data. The graph draws
minimally-described species as pruned dots and only needs structure to lay out
and navigate. The book wants every species as its own entry, with prose. Both
currently pay for the union, on every order they open.

This measures four projections so the split can be chosen from numbers rather
than intuition:

  shipped   the file as buildData.ts writes it today
  noLists   speciesList[] dropped; described species keep their nodes and prose
  counts    family -> genus with counts, no children below genus, no species.
            The minimum that can draw and navigate the tree.
  names     counts, plus every species reduced to {id, name, rank}. Enough for
            the book to list a genus's species without shipping the prose of
            species the reader has not opened.
  nav       the tier the graph would actually render from: FAMILY and GENUS
            keep their prose, counts and stamps; species collapse to
            {_speciesCount, _describedCount} on the genus. This is the one
            that matters - "counts only" drops genus descriptions, which the
            graph's info panel shows, so it is not shippable as-is.

Sizes are the minified JSON length, which is what a server would send with gzip
and what the client has to parse. Descriptions are the bulk of the bytes, so
the interesting comparison is how much each projection drops.

Usage:
    python3 scripts/measureProjections.py                     # all six kingdoms
    python3 scripts/measureProjections.py --kingdom animalia
    python3 scripts/measureProjections.py --worst 15
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDERS_ROOT = os.path.join(ROOT, "portal", "public", "data", "kingdoms")
KINGDOMS = ["animalia", "plantae", "fungi", "chromista", "protozoa", "archaea"]

# Mirrors kingdom-config.json's dataSuffix: animalia has none, the rest do.
SUFFIX = {
    "animalia": "", "plantae": "-plantae", "fungi": "-fungi",
    "chromista": "-chromista", "protozoa": "-protozoa", "archaea": "-archaea",
}


def orders_dir(kingdom: str) -> str:
    return os.path.join(ORDERS_ROOT, kingdom, f"orders{SUFFIX[kingdom]}")


# ── projections ──────────────────────────────────────────────────────────────

def strip_species_lists(node: dict) -> None:
    node.pop("speciesList", None)
    for child in node.get("children") or []:
        strip_species_lists(child)


def to_counts(node: dict) -> None:
    """Family -> genus with counts. Everything below genus is removed."""
    kept: list[dict] = []
    for child in node.get("children") or []:
        if child.get("rank") == "GENUS":
            described = _walk_species(child)
            kept.append({
                "id": child.get("id"),
                "name": child.get("name"),
                "rank": "GENUS",
                "_speciesCount": described["total"],
                "_describedCount": described["described"],
            })
        else:
            to_counts(child)
            kept.append(child)
    node["children"] = kept
    node.pop("speciesList", None)


def to_names(node: dict) -> None:
    """counts, plus every species as a bare {id, name, rank} record."""
    kept: list[dict] = []
    for child in node.get("children") or []:
        if child.get("rank") == "SPECIES":
            kept.append({"id": child.get("id"), "name": child.get("name"), "rank": "SPECIES"})
        else:
            to_names(child)
            kept.append(child)
    node["children"] = kept
    node.pop("speciesList", None)


def to_nav(node: dict) -> None:
    """Families and genera keep their prose; species collapse into counts."""
    kept: list[dict] = []
    for child in node.get("children") or []:
        rank = child.get("rank")
        if rank == "SPECIES":
            kept.append({"id": child.get("id"), "name": child.get("name"), "rank": "SPECIES"})
        elif rank == "GENUS":
            stats = _walk_species(child)
            kept.append({
                "id": child.get("id"),
                "name": child.get("name"),
                "rank": "GENUS",
                "description": child.get("description", ""),
                "lineage": child.get("lineage"),
                "familySlug": child.get("familySlug"),
                "className": child.get("className"),
                "orderName": child.get("orderName"),
                "extinct": child.get("extinct"),
                "_speciesCount": stats["total"],
                "_describedCount": stats["described"],
            })
        else:
            to_nav(child)
            kept.append(child)
    node["children"] = kept
    node.pop("speciesList", None)


def _walk_species(node: dict) -> dict:
    total = described = 0
    if node.get("rank") == "SPECIES":
        total += 1
        if (node.get("description") or "").strip():
            described += 1
    for sp in node.get("speciesList") or []:
        total += 1
        if (sp.get("description") or "").strip():
            described += 1
    for child in node.get("children") or []:
        sub = _walk_species(child)
        total += sub["total"]
        described += sub["described"]
    return {"total": total, "described": described}


# ── measurement ──────────────────────────────────────────────────────────────

@dataclass
class Row:
    kingdom: str
    name: str
    shipped: int = 0
    no_lists: int = 0
    counts: int = 0
    names: int = 0
    nav: int = 0
    families: int = 0
    genera: int = 0
    species: int = 0


@dataclass
class Totals:
    files: int = 0
    shipped: int = 0
    no_lists: int = 0
    counts: int = 0
    names: int = 0
    nav: int = 0
    families: int = 0
    genera: int = 0
    species: int = 0
    worst_shipped: tuple = ("", 0)
    worst_counts: tuple = ("", 0)
    # (name, size) for the single largest file under each projection, tracked
    # across every file rather than derived from the shipped-size ranking -
    # the biggest counts-only file is often not the biggest shipped one.
    max_by_projection: dict = field(default_factory=dict)


def measure_file(kingdom: str, path: str) -> Row:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    row = Row(kingdom=kingdom, name=os.path.basename(path))
    row.shipped = len(json.dumps(doc, separators=(",", ":")))

    stats = _walk_species(doc)
    row.species = stats["total"]
    row.families = _count_rank(doc, "FAMILY")
    row.genera = _count_rank(doc, "GENUS")

    strip_species_lists(doc)
    row.no_lists = len(json.dumps(doc, separators=(",", ":")))

    to_counts(doc)
    row.counts = len(json.dumps(doc, separators=(",", ":")))

    to_names(doc)
    row.names = len(json.dumps(doc, separators=(",", ":")))

    # Every projection above mutates `doc` in place, so the nav tier has to be
    # measured against a fresh parse or it would see the already-stripped tree.
    row.nav = measure_nav(path)
    return row


def measure_nav(path: str) -> int:
    """Nav-tier size for one file, from a parse of its own."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    to_nav(doc)
    return len(json.dumps(doc, separators=(",", ":")))


def _count_rank(node: dict, rank: str) -> int:
    n = 1 if node.get("rank") == rank else 0
    for child in node.get("children") or []:
        n += _count_rank(child, rank)
    return n


def measure_kingdom(kingdom: str, worst: int) -> tuple[Totals, list[Row]]:
    d = orders_dir(kingdom)
    if not os.path.isdir(d):
        return Totals(), []
    totals = Totals()
    rows: list[Row] = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        row = measure_file(kingdom, os.path.join(d, name))
        rows.append(row)
        totals.files += 1
        totals.shipped += row.shipped
        totals.no_lists += row.no_lists
        totals.counts += row.counts
        totals.names += row.names
        totals.nav += row.nav
        totals.families += row.families
        totals.genera += row.genera
        totals.species += row.species
        if row.shipped > totals.worst_shipped[1]:
            totals.worst_shipped = (row.name, row.shipped)
        if row.counts > totals.worst_counts[1]:
            totals.worst_counts = (row.name, row.counts)
        for attr in ("shipped", "no_lists", "counts", "names", "nav"):
            if getattr(row, attr) > totals.max_by_projection.get(attr, (None, 0))[1]:
                totals.max_by_projection[attr] = (row.name, getattr(row, attr))
    rows.sort(key=lambda r: r.shipped, reverse=True)
    return totals, rows[:worst]


def mb(n: int) -> str:
    return f"{n / 1048576:8.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kingdom", choices=KINGDOMS + ["all"], default="all")
    ap.add_argument("--worst", type=int, default=10)
    args = ap.parse_args()

    kingdoms = KINGDOMS if args.kingdom == "all" else [args.kingdom]
    grand = Totals()

    for k in kingdoms:
        totals, worst = measure_kingdom(k, args.worst)
        if not totals.files:
            print(f"{k}: no order files at {orders_dir(k)} (has the kingdom been built?)")
            continue
        grand.files += totals.files
        for f in ("shipped", "no_lists", "counts", "names", "nav"):
            setattr(grand, f, getattr(grand, f) + getattr(totals, f))
        grand.families += totals.families
        grand.genera += totals.genera
        grand.species += totals.species

        print(f"\n{k}  ({totals.files} order files, {totals.families:,} families, "
              f"{totals.genera:,} genera, {totals.species:,} species entries)")
        print(f"  {'':<12}{'total':>12}{'largest file':>26}")
        for label, attr in (("shipped", "shipped"), ("no speciesList", "no_lists"),
                            ("counts only", "counts"), ("names only", "names"),
                            ("nav tier", "nav")):
            nm, sz = totals.max_by_projection.get(attr, ("-", 0))
            lm = f"{nm[:24]} {sz/1048576:.1f} MB" if nm != "-" else "-"
            print(f"  {label:<12}{mb(getattr(totals, attr)):>12}{lm:>26}")

        print(f"  largest as shipped: {totals.worst_shipped[0]} {totals.worst_shipped[1]/1048576:.1f} MB")
        print(f"  largest counts-only: {totals.worst_counts[0]} {totals.worst_counts[1]/1048576:.1f} MB")
        if worst:
            print(f"  biggest {len(worst)} as shipped:")
            for r in worst:
                print(f"    {r.name:<36}{mb(r.shipped):>12}"
                      f"  counts {mb(r.counts):>11}"
                      f"  {r.families:>4}f {r.genera:>6}g {r.species:>7,}sp")

    if grand.files:
        print(f"\n{'ALL SIX KINGDOMS':<50}{grand.files} files, {grand.species:,} species entries")
        for label, attr in (("shipped (today)", "shipped"), ("no speciesList", "no_lists"),
                            ("nav tier", "nav"), ("counts only", "counts"),
                            ("names only", "names")):
            v = getattr(grand, attr)
            print(f"  {label:<20}{mb(v):>12}   {v/grand.shipped*100:5.1f}% of shipped")
        print(f"  shipped + nav tier together: {mb(grand.shipped + grand.nav)} "
              f"(+{(grand.nav/grand.shipped*100):.1f}% on disk, {grand.shipped/grand.nav:.0f}x smaller per fetch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
