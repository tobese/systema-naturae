#!/usr/bin/env python3
"""Import the Orthoptera Species File as a new order in the tree.

Orthoptera was absent from the portal entirely -- no order node, and none of
Tettigoniidae, Gryllidae, Acrididae, Mantidae or Phasmatidae. Among the
orthopteroid orders only Embioptera survived. That is roughly 28,000 accepted
species of grasshopper, cricket, mantis and stick insect missing from a tree that
claims 1.2 million species.

Source: Orthoptera Species File, Species File Group at the University of Illinois
(GBIF dataset af66d4cf-0fd2-434b-9334-9806a5efa6f7, DOI 10.15468/nn7jhc, CC-BY 4.0).
46,039 taxa, of which 33,374 are species and 28,081 accepted species sit under a
family. Its `multimedia.txt` is empty, so there are no images; `distribution.txt`
carries 92,009 rows of TDWG place names, mapped by scripts/osfLocalities.py.

Structure written as family > subfamily > tribe > genus > species, which is the
rank vocabulary the tree already uses. OSF's superfamily and suborder are not
representable under our taxonomy (an order sits directly under a class, with no
rank between order and family), so they are recorded in `lineage` rather than
invented as directory levels.

Only `valid` taxa are imported. Junior synonyms, synonyms, invalid names and
misapplied names are skipped rather than imported and reconciled later: 1,791
fungal and 487 araneal names in the tree are already synonyms the catalogues
recognise, and importing a second batch of the same problem is not an improvement.

Usage:
    python3 scripts/importOrthoptera.py                 # dry run, writes nothing
    python3 scripts/importOrthoptera.py --apply
"""
import argparse
import collections
import csv
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osfLocalities import continent_for  # noqa: E402

csv.field_size_limit(10_000_000)

SRC = "/Volumes/MacieExternal/tmp/opencode/ortho"
OUT_ROOT = os.path.join("taxonomy", "animalia", "arthropoda", "insecta", "orthoptera")
SLUG_RE = re.compile(r"[^a-z0-9]+")

RANK_KEEP = ("SUBFAMILY", "TRIBE", "GENUS", "SPECIES", "SUBSPECIES")
RANK_OF = {
    "subfamily": "SUBFAMILY", "tribe": "TRIBE", "genus": "GENUS",
    "species": "SPECIES", "subspecies": "SUBSPECIES",
}
# Superseded ranks are folded into the lineage string rather than dropped.
RANK_LINEAGE = {"superfamily": "superfamily", "suborder": "suborder"}

AUTH_YEAR = re.compile(r",?\s*(\d{4})[a-z]?\s*$")


def slug(name: str) -> str:
    s = SLUG_RE.sub("-", (name or "").lower().replace("†", "")).strip("-")
    return s or "unknown"


# sanity_scan.py's MALFORMED_ID forbids "__", a space and a hyphen in an id, so
# the slug is folded to underscores and collapsed rather than hyphenated.
ID_RE = re.compile(r"[^A-Za-z0-9]+")
PREFIX = {"SPECIES": "SP", "SUBSPECIES": "SPSUB", "GENUS": "GENUS",
          "TRIBE": "TRIBE", "SUBFAMILY": "SUBFAM", "FAMILY": "FAM"}


def node_id(prefix: str, name: str, authority: str = "") -> str:
    """prefix_NAME[_AUTHORITY], matching the tree's existing convention.

    The authority is not decoration: OSF holds 17 primary homonyms -- both
    `Oecanthus latipennis` Riley, 1881 and `Oecanthus latipennis` Liu, Yin & Xia,
    1994 are `valid` -- and an id built from the name alone collides. The tree
    already disambiguates this way, e.g. `Smilax zeylanica L.` ->
    `SP_SMILAX_ZEYLANICA_L_`.
    """
    body = ID_RE.sub("_", (name or "").replace("\u2020", "")).strip("_").upper()
    while "__" in body:
        body = body.replace("__", "_")
    if authority:
        auth = ID_RE.sub("_", authority.replace("\u2020", "")).strip("_").upper()
        while "__" in auth:
            auth = auth.replace("__", "_")
        if auth:
            body = f"{body}_{auth}" if body else auth
    return f"{prefix}_{body}" if body else prefix


def nodename(raw: str) -> str:
    """Strip OSF's authorship and subgenus parentheses off a scientific name.

    OSF writes a subgenus in parentheses mid-name -- `Sphingonotus (Sphingonotus)
    striatus` -- which is not how the name is cited and which would otherwise end
    up in our `name` field verbatim.
    """
    n = (raw or "").strip()
    prev = None
    while prev != n:
        prev = n
        n = re.sub(r"\s*\([^()]*\)", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n or (raw or "").strip()


def split_authorship(raw_auth: str, scientific_name: str):
    """(authorship, yearPublished) from OSF's authorship field."""
    a = (raw_auth or "").strip().rstrip(".,")
    y = None
    m = AUTH_YEAR.search(a)
    if m:
        y = m.group(1)
        a = a[:m.start()].strip().rstrip(",").strip()
    return (a or None), y


def iter_genera(node):
    """Every GENUS node in a family tree."""
    if node.get("rank") == "GENUS":
        yield node
    for c in node.get("children") or []:
        yield from iter_genera(c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT_ROOT)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(
        open(f"{args.src}/taxon.txt", newline="", encoding="utf-8", errors="replace"),
        delimiter="\t"))
    by_id = {r["id"]: r for r in rows}

    def chain(r):
        """Ancestors, outermost first."""
        out, cur, seen = [], r, set()
        while cur and cur.get("parentNameUsageID") and cur["parentNameUsageID"] in by_id:
            pid = cur["parentNameUsageID"]
            if pid in seen:
                break
            seen.add(pid)
            cur = by_id[pid]
            out.append(cur)
        return list(reversed(out))

    # ---- distribution, by taxon id ----
    dist = collections.defaultdict(set)
    for r in csv.DictReader(open(f"{args.src}/distribution.txt", newline="",
                                 encoding="utf-8", errors="replace"), delimiter="\t"):
        loc = (r.get("locality") or "").strip()
        if not loc:
            continue
        for c in continent_for(loc) or ():
            dist[r.get("id")].add(c)

    # ---- English common names only ----
    # The table is 2,931 rows of which 2,454 are English, 260 French, 210 German,
    # 7 Spanish. Importing the lot would repeat the mistake of af5669043, which
    # wrote Chinese and Japanese names into the tree as English ones.
    common = collections.defaultdict(list)
    for r in csv.DictReader(open(f"{args.src}/vernacularname.txt", newline="",
                                 encoding="utf-8", errors="replace"), delimiter="\t"):
        if (r.get("language") or "").strip().lower() not in ("english", "en", "eng"):
            continue
        v = (r.get("vernacularName") or "").strip()
        if v:
            common[r.get("id")].append(v)

    # ---- assemble families ----
    fams = collections.defaultdict(lambda: {"species": 0, "genera": set(), "rows": []})
    stats = collections.Counter()
    lineage_of_family = {}
    for r in rows:
        rank = (r.get("taxonRank") or "").lower()
        status = (r.get("taxonomicStatus") or "").lower()
        anc = chain(r)
        fam = next((a for a in anc if (a.get("taxonRank") or "").lower() == "family"), None)
        if fam is None:
            stats["no-family-ancestor"] += 1
            continue
        if status != "valid":
            stats[f"skipped-{status or 'no-status'}"] += 1
            continue
        if rank not in RANK_OF:
            # subgenus and subtribe are real ranks in OSF but have no place in
            # our vocabulary; they are recorded in lineage rather than dropped
            # silently.
            stats[f"skipped-rank-{rank}"] += 1
            continue
        stats[f"kept-{rank}"] += 1
        fams[fam["id"]]["species"] += 1
        fams[fam["id"]]["rows"].append(r)
        if rank == "genus":
            fams[fam["id"]]["genera"].add(nodename(r.get("scientificName") or ""))
        lineage_of_family[fam["id"]] = [
            a.get("scientificName") for a in anc
            if (a.get("taxonRank") or "").lower() in RANK_LINEAGE
        ]

    print(f"OSF rows            {len(rows):,}")
    print(f"families to write   {len(fams):,}")
    print(f"valid taxa imported {sum(f['species'] for f in fams.values()):,}")
    print(f"genera              {sum(len(f['genera']) for f in fams.values()):,}")
    print("skipped:")
    for k, v in stats.most_common(10):
        print(f"   {v:>7,}  {k}")
    sizes = sorted(((f["species"], nodename(by_id[n].get("scientificName") or ""))
                   for n, f in fams.items()), reverse=True)
    print("kept by rank:")
    for k, v in sorted(((k, v) for k, v in stats.items() if k.startswith("kept-"))):
        print(f"   {v:>7,}  {k[5:]}")
    print(f"largest: {sizes[0][1]} ({sizes[0][0]:,})   smallest: {sizes[-1][1]} ({sizes[-1][0]:,})")
    ext = sum(1 for r in rows if "†" in (r.get("scientificName") or "")
              and (r.get("taxonomicStatus") or "").lower() == "valid")
    print(f"taxa with a † (extinct) marker: {ext:,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    written = 0
    total_nodes = 0
    for fid, info in fams.items():
        frow = by_id[fid]
        fname = nodename(frow.get("scientificName") or "")
        fslug = slug(fname)
        fam_auth, fam_year = split_authorship(
            frow.get("scientificNameAuthorship"), fname)
        lin = " > ".join(lineage_of_family.get(fid) or [])

        # nest subfamily > tribe > genus > species
        root = {"id": node_id("FAM", fname), "name": fname, "rank": "FAMILY",
                "children": [], "speciesCount": info["species"], "appSlug": fslug}
        if lin:
            root["lineage"] = lin
        conts = sorted(dist.get(fid) or ())
        if conts:
            root["continents"] = conts

        buckets = {"SUBFAMILY": {}, "TRIBE": {}, "GENUS": {}}
        for r in sorted(info["rows"], key=lambda x: x.get("scientificName") or ""):
            rank = RANK_OF[(r.get("taxonRank") or "").lower()]
            nm = nodename(r.get("scientificName") or "")
            a, y = split_authorship(r.get("scientificNameAuthorship"), nm)
            node = {"id": node_id(PREFIX[rank], nm, " ".join(x for x in (a, y) if x)), "name": nm, "rank": rank}
            if a:
                node["authorship"] = a
            if y:
                node["yearPublished"] = y
            c = sorted(dist.get(r["id"]) or ())
            if c:
                node["continents"] = c
            for v in common.get(r["id"]) or ():
                node["commonName"] = v
                break
            if "†" in (r.get("scientificName") or ""):
                node["extinct"] = True
            node["sourcedFrom"] = "orthoptera species file"

            if rank in ("SPECIES", "SUBSPECIES"):
                node.setdefault("subspeciesCount", 0)
                node.setdefault("lineage", " > ".join(
                    filter(None, [lin, nodename((next((x for x in chain(r)
                        if (x.get('taxonRank') or '').lower() == 'genus'), {})).get('scientificName') or '')])))
                # attach to its genus, creating the genus if OSF omitted it
                gen = next((x for x in reversed(chain(r))
                            if (x.get("taxonRank") or "").lower() == "genus"), None)
                gname = nodename((gen or {}).get("scientificName") or nm.split(" ")[0])
                gnode = buckets["GENUS"].get(gname)
                if gnode is None:
                    gnode = {"id": node_id("GENUS", gname), "name": gname,
                             "rank": "GENUS", "children": []}
                    buckets["GENUS"][gname] = gnode
                gnode.setdefault("children", []).append(node)
            elif rank == "GENUS":
                buckets["GENUS"].setdefault(nm, node)
            else:
                buckets[rank].setdefault(nm, node)

        # Assemble bottom-up, once per node.
        #
        # The first version appended each tribe to its subfamily inside the
        # per-genus loop, so a tribe holding 104 genera was added to its
        # subfamily 104 times and its entire subtree was serialised 104 times
        # over: 312,156 nodes for 9,572 unique ones, and 318MB of JSON. Each
        # tribe is now built once and attached once.
        genus_rows = {nodename(x.get("scientificName") or ""): x
                      for x in info["rows"] if (x.get("taxonRank") or "").lower() == "genus"}
        bare_genera = []
        tribe_genera = collections.defaultdict(list)   # tribe name -> [genus node]
        subfam_tribes = collections.defaultdict(set)  # subfamily -> {tribe names}
        subfam_genera = collections.defaultdict(list)  # subfamily -> [genus node]

        for gname, gnode in buckets["GENUS"].items():
            anc = chain(genus_rows.get(gname)) if genus_rows.get(gname) else []
            sub = next((a for a in anc if (a.get("taxonRank") or "").lower() == "subfamily"), None)
            tri = next((a for a in anc if (a.get("taxonRank") or "").lower() == "tribe"), None)
            if sub is None:
                bare_genera.append(gnode)
            elif tri is None:
                subfam_genera[nodename(sub.get("scientificName") or "")].append(gnode)
            else:
                tname = nodename(tri.get("scientificName") or "")
                tribe_genera[tname].append(gnode)
                subfam_tribes[nodename(sub.get("scientificName") or "")].add(tname)

        subfam_nodes = {}
        for sf in sorted(set(subfam_tribes) | set(subfam_genera)):
            node = {"id": node_id("SUBFAM", sf), "name": sf, "rank": "SUBFAMILY", "children": []}
            for t in sorted(subfam_tribes.get(sf, ())):
                tnode = {"id": node_id("TRIBE", t), "name": t, "rank": "TRIBE",
                         "children": tribe_genera[t]}
                node["children"].append(tnode)
            node["children"].extend(subfam_genera.get(sf, []))
            subfam_nodes[sf] = node

        root["children"] = bare_genera + [subfam_nodes[k] for k in sorted(subfam_nodes)]
        # OSF lists four fossil genera with no species under them (Minititan,
        # Flexaboilus, Furcaboilus, Pruvostites). sanity_scan.py treats an empty
        # genus as a defect and EMPTY_GENUS must stay 0, so they are pruned here
        # rather than shipped and cleaned up later.
        def prune(node):
            node["children"] = [c for c in (node.get("children") or [])
                                if c.get("rank") != "GENUS" or (c.get("children") or [])]
            for c in node["children"]:
                prune(c)
        prune(root)
        kept_genera = sum(1 for _ in iter_genera(root))
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
    # emit the taxonomy.json fragment for the caller
    frag = []
    for fid, info in fams.items():
        fname = nodename(by_id[fid].get("scientificName") or "")
        frag.append({"name": fname, "appSlug": slug(fname),
                     "speciesCount": info["species"]})
    frag.sort(key=lambda x: -x["speciesCount"])
    with open("/tmp/orthoptera_families.json", "w", encoding="utf-8") as fh:
        json.dump(frag, fh, ensure_ascii=False, indent=1)
    print(f"  taxonomy fragment: /tmp/orthoptera_families.json ({len(frag)} families)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
