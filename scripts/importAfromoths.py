#!/usr/bin/env python3
"""Import the Afromoths checklist into Lepidoptera.

29,983 accepted species across 94 families, and the reason this exists rather than
being folded into importSpeciesFile.py: the distribution data is keyed on ISO
country codes instead of free-text localities. 91,005 rows over 65 countries, all
of them populated -- so continents come from `CC2CONT` rather than from a
place-name table that has to be curated and audited. That is the difference
between this and the World Spider Catalog's 7,184 unmapped area strings.

Three schema differences from a Species File:

- `taxonomicStatus` is `accepted` / `misapplied` / `Synonym`, not
  `valid` / `junior synonym`. The 21,489 `misapplied` rows are names applied to
  the wrong taxon -- the Afrotropical literature is full of them -- and taking
  those would write confidently wrong names into the tree, so they are excluded
  along with the 10,882 synonyms.
- No `vernacularname.txt`, so no common names come from this source.
- No `extinct` markers and no subgenus-to-species nesting problems; subgenus is
  dropped to lineage as in the Species File importer.

Our Lepidoptera is two butterfly families (Nymphalidae, Papilionidae, 8,475
species); these are moths. Overlap measured at 2 species.

Usage:
    python3 scripts/importAfromoths.py --dry-run
    python3 scripts/importAfromoths.py --apply
"""
import argparse
import collections
import csv
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util  # noqa: E402

import importSpeciesFile as SF  # noqa: E402  -- name/id/authorship handling

_spec = importlib.util.spec_from_file_location(
    "ec", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "enrichContinentsFromGbif.py"))
_ec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ec)
CC2CONT = _ec.CC2CONT

SLUG = "afromoths"
ARCHIVE = "afromoths"
OUT = os.path.join("taxonomy", "animalia", "arthropoda", "insecta", "lepidoptera")
ACCEPTED = "accepted"
SKIP_STATUSES = {"misapplied", "synonym"}


def chain(row, by_id):
    out, cur, seen = [], row, set()
    while cur and cur.get("parentNameUsageID") and cur["parentNameUsageID"] in by_id:
        pid = cur["parentNameUsageID"]
        if pid in seen:
            break
        seen.add(pid)
        cur = by_id[pid]
        out.append(cur)
    return list(reversed(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--clean", action="store_true",
                    help="delete the output directory first. Off by default: this "
                         "writes into lepidoptera/, which already holds the two "
                         "butterfly families.")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    src = SF.ensure_extracted(SF.ARCHIVE_SLUG[SLUG], SF.work_dir_for(SLUG))
    rows = list(csv.DictReader(
        open(f"{src}/taxon.txt", newline="", encoding="utf-8", errors="replace"),
        delimiter="\t"))
    by_id = {r["id"]: r for r in rows}

    # ---- distribution, by taxon id, via ISO country code ----
    dist = collections.defaultdict(set)
    unmapped_cc = collections.Counter()
    drows = 0
    for r in csv.DictReader(
            open(f"{src}/distribution.txt", newline="", encoding="utf-8",
                 errors="replace"), delimiter="\t"):
        cc = (r.get("countryCode") or "").strip()
        if not cc:
            continue
        drows += 1
        cont = CC2CONT.get(cc)
        if cont:
            dist[r.get("id")].add(cont)
        else:
            unmapped_cc[cc] += 1

    fams = collections.defaultdict(lambda: {"species": 0, "genera": set(), "rows": []})
    stats = collections.Counter()
    lineage_of_family = {}
    for r in rows:
        rank = (r.get("taxonRank") or "").lower()
        status = (r.get("taxonomicStatus") or "").strip().lower()
        # Status first, then family ancestry. Checking ancestry first reported
        # 17,886 rows as "no-family-ancestor" when every one of them was a
        # misapplied name we meant to drop -- which reads like data loss and is
        # exactly the sort of number that gets argued about instead of trusted.
        # Checking status first shows 0 accepted species unattached.
        if status in SKIP_STATUSES:
            stats[f"skipped-{status}"] += 1
            continue
        if status != ACCEPTED:
            stats[f"skipped-{status or 'no-status'}"] += 1
            continue
        anc = chain(r, by_id)
        fam = next((a for a in anc if (a.get("taxonRank") or "").lower() == "family"), None)
        if fam is None:
            stats["no-family-ancestor"] += 1
            continue
        if rank not in SF.RANK_OF:
            stats[f"skipped-rank-{rank}"] += 1
            continue
        stats[f"kept-{rank}"] += 1
        fams[fam["id"]]["species"] += 1
        fams[fam["id"]]["rows"].append(r)
        if rank == "genus":
            fams[fam["id"]]["genera"].add(SF.nodename(r.get("scientificName") or ""))
        lineage_of_family[fam["id"]] = [
            a.get("scientificName") for a in anc
            if (a.get("taxonRank") or "").lower() in SF.RANK_LINEAGE]

    print(f"taxon rows            {len(rows):,}")
    print(f"distribution rows     {drows:,}")
    print(f"families to write     {len(fams):,}")
    print(f"accepted taxa imported {sum(f['species'] for f in fams.values()):,}")
    print(f"genera                {sum(len(f['genera']) for f in fams.values()):,}")
    print("skipped:")
    for k, v in stats.most_common(10):
        print(f"   {v:>7,}  {k}")
    print("kept by rank:")
    for k, v in sorted((k, v) for k, v in stats.items() if k.startswith("kept-")):
        print(f"   {v:>7,}  {k[5:]}")
    if unmapped_cc:
        print("distribution country codes left unmapped (deliberate):")
        for k, v in unmapped_cc.most_common():
            print(f"   {v:>6,}  {k}")
    sized = sorted(((f["species"], SF.nodename(by_id[n].get("scientificName") or ""))
                    for n, f in fams.items()), reverse=True)
    print(f"largest: {sized[0][1]} ({sized[0][0]:,})   "
          f"smallest: {sized[-1][1]} ({sized[-1][0]:,})")

    frag = []
    for fid, info in fams.items():
        fname = SF.nodename(by_id[fid].get("scientificName") or "")
        frag.append({"name": fname, "appSlug": SF.slug(fname),
                     "speciesCount": info["species"]})
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
    written = total_nodes = 0
    for fid, info in fams.items():
        frow = by_id[fid]
        fname = SF.nodename(frow.get("scientificName") or "")
        fslug = SF.slug(fname)
        fam_auth, fam_year = SF.split_authorship(
            frow.get("scientificNameAuthorship"), fname)
        lin = " > ".join(lineage_of_family.get(fid) or [])

        root = {"id": SF.node_id("FAM", fname), "name": fname, "rank": "FAMILY",
                "children": [], "speciesCount": info["species"], "appSlug": fslug}
        if fam_auth:
            root["authorship"] = fam_auth
        if fam_year:
            root["yearPublished"] = fam_year
        if lin:
            root["lineage"] = lin
        conts = sorted(dist.get(fid) or ())
        if conts:
            root["continents"] = conts

        buckets = {"SUBFAMILY": {}, "TRIBE": {}, "GENUS": {}}
        for r in sorted(info["rows"], key=lambda x: x.get("scientificName") or ""):
            rank = SF.RANK_OF[(r.get("taxonRank") or "").lower()]
            nm = SF.nodename(r.get("scientificName") or "")
            a, y = SF.split_authorship(r.get("scientificNameAuthorship"), nm)
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
            node["sourcedFrom"] = "afromoths"
            # The checklist carries no prose, but it does carry the publication
            # each name appeared in, which is the one piece of real reference
            # value here and otherwise gets thrown away.
            pub = (r.get("namePublishedIn") or "").strip()
            if pub:
                node["reference"] = pub

            if rank in ("SPECIES", "SUBSPECIES"):
                node.setdefault("subspeciesCount", 0)
                node.setdefault("lineage", " > ".join(
                    filter(None, [lin, SF.nodename((next((x for x in chain(r, by_id)
                        if (x.get('taxonRank') or '').lower() == 'genus'), {})).get('scientificName') or '')])))
                gnode = SF.genus_node_for(r, nm, buckets, lambda x: chain(x, by_id),
                                          node.get("lineage") or "")
                gnode.setdefault("children", []).append(node)
            elif rank == "GENUS":
                buckets["GENUS"].setdefault(nm, node)
            else:
                buckets[rank].setdefault(nm, node)

        genus_rows = {SF.nodename(x.get("scientificName") or ""): x
                      for x in info["rows"]
                      if (x.get("taxonRank") or "").lower() == "genus"}
        kept_genera = SF.assemble_genera_tree(
            root, buckets, genus_rows, lambda x: chain(x, by_id), stats)
        if kept_genera != len(info["genera"]):
            stats["pruned-empty-genera"] += len(info["genera"]) - kept_genera
        root["genusCount"] = kept_genera
        root["enrichmentStatus"] = "empty"

        d = os.path.join(args.out, fslug, "src", "data")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{fslug}.json"), "w", encoding="utf-8") as fh:
            json.dump(root, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

        def count(n):
            return 1 + sum(count(c) for c in n.get("children") or [])
        total_nodes += count(root)
        written += 1

    print(f"\nwrote {written:,} family files under {args.out}")
    print(f"  {total_nodes:,} nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
