#!/usr/bin/env python3
"""Import the Catalogue of Afrotropical Bees into Hymenoptera.

9,109 species across six families, 0% name overlap with the tree, and 7,449
distribution rows keyed on ISO country codes -- so the same CC2CONT path as
Afromoths applies. Two things needed handling that a Species File does not:

- **The `family` column is polluted.** It carries subfamily names (Apinae,
  Nomadinae, Dasypodainae) for a handful of rows, so families are taken from
  parentNameUsageID ancestry instead, which resolves all 9,109 species to six
  families cleanly.
- **Names carry inline authorship**, often with a subgenus: `Lasioglossum
  (Ctenonomia) ernesti Paul`. `nodename()` strips parenthesised authorship but
  not a trailing bare one, so the name is rebuilt from the `genus` and
  `specificEpithet` columns, which are fully populated, and authorship/year come
  from their own columns.

**English names are deliberately not imported.** The source carries 7,400
vernacular rows but only 107 distinct values, 106 of them single run-together
tokens -- "Sandwalkercuckoobee", "Earwinggroundbee", "Bandeddiggerbee". These are
Pauly's informal group names with the spaces stripped somewhere in the
conversion. 107 mangled names are worse than none.

Families that already exist are merged, not overwritten: our Apidae holds 6,526
species enriched from GBIF and Wikipedia, and this file would otherwise replace
them with 2,408 bare names.

Usage:
    python3 scripts/importBees.py
    python3 scripts/importBees.py --apply
"""
import argparse
import collections
import csv
import importlib.util
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importSpeciesFile as SF  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "ec", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "enrichContinentsFromGbif.py"))
_ec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ec)

SLUG = "afrotropical-bees"
ACCEPTED = {"valid", "accepted"}
OUT = os.path.join("taxonomy", "animalia", "arthropoda", "insecta", "hymenoptera")
RANK_MARKER = {"subspecies": "subsp.", "variety": "var.", "form": "form."}


def load_src():
    from sources import work_dir
    d = work_dir(SLUG)
    marker = os.path.join(d, "taxon.txt")
    if not os.path.exists(marker):
        os.makedirs(d, exist_ok=True)
        from sources import archive_dir
        with zipfile.ZipFile(os.path.join(archive_dir(SLUG), "bees.zip")) as z:
            z.extractall(d)
    return d


def build_name(r):
    """genus + epithet(s), ignoring any authorship left inline in the name.

    Rank-aware because the structured columns are only populated for species:
    all 260 genus rows have an *empty* `genus` column and carry the name only in
    scientificName ("Chloralictus Robertson, 1902"), so a purely column-driven
    builder returns the empty string for every genus and the family collapses to
    one. A genus name is a single word, so the first token of scientificName is
    the genus and the rest is authorship.
    """
    rank = (r.get("taxonRank") or "").lower()
    infra = (r.get("infraspecificEpithet") or "").strip()
    name = " ".join(p for p in ((r.get("genus") or "").strip(),
                                (r.get("specificEpithet") or "").strip()) if p)
    if infra and name:
        name = f"{name} {RANK_MARKER.get(rank, rank)} {infra}"
    if not name:
        sci = (r.get("scientificName") or "").strip()
        if sci:
            name = SF.nodename(sci.split()[0]) if rank == "genus" else SF.nodename(sci)
    return name.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    src = load_src()
    rows = list(csv.DictReader(
        open(f"{src}/taxon.txt", newline="", encoding="utf-8", errors="replace"),
        delimiter="\t"))
    by_id = {r["id"]: r for r in rows}

    def chain(r):
        out, cur, seen = [], r, set()
        while cur and cur.get("parentNameUsageID") and cur["parentNameUsageID"] in by_id:
            pid = cur["parentNameUsageID"]
            if pid in seen:
                break
            seen.add(pid)
            cur = by_id[pid]
            out.append(cur)
        return list(reversed(out))

    dist = collections.defaultdict(set)
    unmapped = collections.Counter()
    drows = 0
    for r in csv.DictReader(
            open(f"{src}/distribution.txt", newline="", encoding="utf-8",
                 errors="replace"), delimiter="\t"):
        cc = (r.get("countryCode") or "").strip()
        if not cc:
            continue
        drows += 1
        cont = _ec.CC2CONT.get(cc)
        if cont:
            dist[r.get("id")].add(cont)
        else:
            unmapped[cc] += 1

    fams = collections.defaultdict(lambda: {"rows": [], "genera": set()})
    stats = collections.Counter()
    lineage_of = {}
    for r in rows:
        rank = (r.get("taxonRank") or "").lower()
        status = (r.get("taxonomicStatus") or "").strip().lower()
        if status and status not in ACCEPTED:
            stats[f"skipped-{status}"] += 1
            continue
        if rank not in SF.RANK_OF:
            stats[f"skipped-rank-{rank}"] += 1
            continue
        anc = chain(r)
        fam = next((a for a in anc if (a.get("taxonRank") or "").lower() == "family"), None)
        if fam is None:
            stats["no-family-ancestor"] += 1
            continue
        stats[f"kept-{rank}"] += 1
        fams[fam["id"]]["rows"].append(r)
        if rank == "genus":
            fams[fam["id"]]["genera"].add(build_name(r))
        lineage_of[fam["id"]] = [a.get("scientificName") for a in anc
                                 if (a.get("taxonRank") or "").lower() in SF.RANK_LINEAGE]

    print(f"taxon rows            {len(rows):,}")
    print(f"distribution rows     {drows:,}")
    print(f"families              {len(fams):,}")
    print(f"accepted taxa         {sum(len(f['rows']) for f in fams.values()):,}")
    print(f"genera                {sum(len(f['genera']) for f in fams.values()):,}")
    print("skipped:")
    for k, v in stats.most_common(8):
        print(f"   {v:>7,}  {k}")
    print("kept by rank:")
    for k, v in sorted((k, v) for k, v in stats.items() if k.startswith("kept-")):
        print(f"   {v:>7,}  {k[5:]}")
    if unmapped:
        print("country codes unmapped:",
              ", ".join(f"{k}({v})" for k, v in unmapped.most_common()))
    for fid, info in sorted(fams.items(), key=lambda kv: -len(kv[1]["rows"])):
        print(f"   {SF.nodename(by_id[fid].get('scientificName') or ''):<18}"
              f"{len(info['rows']):>7,} taxa  {len(info['genera']):>5,} genera")

    frag = []
    for fid, info in fams.items():
        fname = SF.nodename(by_id[fid].get("scientificName") or "")
        frag.append({"name": fname, "appSlug": SF.slug(fname),
                     "speciesCount": len(info["rows"])})
    frag.sort(key=lambda x: -x["speciesCount"])
    frag_path = f"/tmp/{SLUG}_families.json"
    with open(frag_path, "w", encoding="utf-8") as fh:
        json.dump(frag, fh, ensure_ascii=False, indent=1)
    print(f"  taxonomy fragment: {frag_path} ({len(frag)} families)")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    if args.clean and os.path.isdir(args.out):
        shutil.rmtree(args.out)
    written = total = 0
    for fid, info in fams.items():
        frow = by_id[fid]
        fname = SF.nodename(frow.get("scientificName") or "")
        fslug = SF.slug(fname)
        lin = " > ".join(x for x in (lineage_of.get(fid) or []) if x)

        root = {"id": SF.node_id("FAM", fname), "name": fname, "rank": "FAMILY",
                "children": [], "speciesCount": 0, "appSlug": fslug}
        if lin:
            root["lineage"] = lin

        buckets = {"SUBFAMILY": {}, "TRIBE": {}, "GENUS": {}}
        seen_species = set()
        for r in sorted(info["rows"], key=lambda x: build_name(x)):
            rank = SF.RANK_OF[(r.get("taxonRank") or "").lower()]
            nm = build_name(r)
            if not nm:
                stats["skipped-no-name"] += 1
                continue
            a = (r.get("scientificNameAuthorship") or "").strip() or None
            y = (r.get("namePublishedInYear") or "").strip() or None
            node = {"id": SF.node_id(SF.PREFIX[rank], nm,
                                     " ".join(x for x in (a, y) if x)),
                    "name": nm, "rank": rank}
            if a:
                node["authorship"] = a
            if y:
                node["yearPublished"] = y
            c = sorted(dist.get(r["id"]) or ())
            if c:
                node["continents"] = c
            node["sourcedFrom"] = "afrotropical bees"
            if rank in ("SPECIES", "SUBSPECIES"):
                key = (rank, nm, a, y)
                if key in seen_species:
                    stats["skipped-duplicate-species"] += 1
                    continue
                seen_species.add(key)
                node.setdefault("subspeciesCount", 0)
                # Same lineage the Species File importer writes: family lineage
                # plus genus, with setdefault so a merge into an existing family
                # never overwrites what is already there.
                g_row = next((x for x in chain(r)
                              if (x.get("taxonRank") or "").lower() == "genus"), {})
                node.setdefault("lineage", " > ".join(filter(None, [
                    lin, SF.nodename(g_row.get("scientificName") or
                                     nm.split(" ")[0])])))
                g = SF.genus_node_for(r, nm, buckets,
                                      lambda x: chain(x), lin)
                g.setdefault("children", []).append(node)
            elif rank == "GENUS":
                buckets["GENUS"].setdefault(nm, node)
            else:
                buckets[rank].setdefault(nm, node)

        genus_rows = {build_name(x): x for x in info["rows"]
                      if (x.get("taxonRank") or "").lower() == "genus"}
        kept = SF.assemble_genera_tree(root, buckets, genus_rows, chain, stats)
        root["genusCount"] = kept
        root["enrichmentStatus"] = "empty"

        d = os.path.join(args.out, fslug, "src", "data")
        os.makedirs(d, exist_ok=True)
        target = os.path.join(d, f"{fslug}.json")
        if os.path.exists(target):
            try:
                existing = json.load(open(target, encoding="utf-8"))
            except Exception:
                existing = None
            if existing and existing.get("rank") == "FAMILY":
                m = SF.merge_family(existing, root)
                print(f"   merged into existing {fslug}: +{m['species_added']:,} species "
                      f"({m['genera_added']} new genera, {m['genera_merged']} extended)")
                root = existing
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(root, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        total += sum(1 for _ in SF.iter_species(root))
        written += 1

    print(f"\nwrote {written} family files under {args.out}")
    print(f"  {total:,} species now in those families (after merges)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
