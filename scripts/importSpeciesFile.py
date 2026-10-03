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
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from osfLocalities import continent_for  # noqa: E402
from sources import archive_dir as _ad, work_dir as _wd  # noqa: E402

csv.field_size_limit(10_000_000)

# The extracted tree lives in work/ and the .zip in archives/, so the work copy
# is disposable. Unpacking on demand is what makes that split safe: if someone
# clears work/ to reclaim the 7GB, the next run rebuilds it rather than failing.
SLUG = "orthoptera"
SRC = _wd(SLUG) + "/ortho"


# slug -> archive directory under sources/archives/. Explicit because the
# convention is not derivable: the Orthoptera archive is "orthoptera", the eight
# sibling checklists are "species-file-<slug>", and the Aphid Species File is
# "aphid-species-file" -- its name reads backwards from the others.
ARCHIVE_SLUG = {s: f"species-file-{s}" for s in (
    "phasmida", "plecoptera", "mantodea", "dermaptera", "grylloblattodea",
    "zoraptera", "coleorrhyncha", "chrysididae")}
ARCHIVE_SLUG["aphid"] = "aphid-species-file"
for _s in ("psocodea", "cockroach", "coreoidea", "embioptera", "lygaeoidea",
           "mantophasmatodea"):
    ARCHIVE_SLUG.setdefault(_s, f"species-file-{_s}")
# Not a Species File, but it shares the extract/archive plumbing.
ARCHIVE_SLUG["afromoths"] = "afromoths"
ARCHIVE_SLUG.setdefault("orthoptera", "orthoptera")


def archive_for(slug: str) -> str:
    key = ARCHIVE_SLUG.get(slug)
    if key is None:
        sys.exit(f"FATAL: no archive mapping for slug {slug!r}.\n"
                 f"       Add it to ARCHIVE_SLUG in {os.path.basename(__file__)}.")
    return _ad(key)


def work_dir_for(slug: str) -> str:
    """Where a slug's extracted tree belongs under sources/work/."""
    return _wd(ARCHIVE_SLUG.get(slug, slug)) + f"/{slug}"


def ensure_extracted(slug: str, dest: str, marker: str = "taxon.txt") -> str:
    """Unpack the archive into work/<archive-slug>/ if it is not already there."""
    if os.path.exists(os.path.join(dest, marker)):
        return dest
    adir = _ad(slug)
    zips = [f for f in os.listdir(adir) if f.endswith((".zip", ".tgz", ".tar.gz"))]
    if not zips:
        sys.exit(f"FATAL: no archive for '{slug}' in {adir}")
    os.makedirs(dest, exist_ok=True)
    print(f"  unpacking {zips[0]} -> {dest}", flush=True)
    with zipfile.ZipFile(os.path.join(adir, zips[0])) as z:
        z.extractall(dest)
    return dest
INSECTA = os.path.join("taxonomy", "animalia", "arthropoda", "insecta")
# Order directory per slug. Only Orthoptera was imported by hand; the other eight
# Species Files arrived later, so the mapping is explicit rather than guessed --
# a slug that is not here should fail loudly instead of creating a directory that
# turns out to be the wrong order.
ORDER_DIR = {
    "orthoptera": "orthoptera",
    "phasmida": "phasmida",
    "plecoptera": "plecoptera",
    "mantodea": "mantodea",
    "dermaptera": "dermaptera",
    "grylloblattodea": "grylloblattodea",
    "zoraptera": "zoraptera",
    "coleorrhyncha": "coleorrhyncha",
    "aphid": None,          # Aphidomorpha is an infraorder of Hemiptera, not an order
    # The SFG calls its cockroach file Blattodea, which is the modern placement
    # (Isoptera, the termites, are folded into Blattodea rather than ranked
    # separately). Two of the six are superfamilies within Hemiptera and carry no
    # order of their own, so --out must be given for them.
    "psocodea": "psocodea",
    "cockroach": "blattodea",
    "embioptera": "embioptera",
    "mantophasmatodea": "mantophasmatodea",
    "coreoidea": None,
    "lygaeoidea": None,
    "chrysididae": None,  # a family of Hymenoptera, not an order of its own
}
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


def genus_node_for(r, nm, buckets, chain, lin=""):
    """The GENUS node a species row belongs under, created if absent.

    Sources do not reliably include an explicit genus row for every species, so
    the genus is manufactured from the binomial when it is missing -- which is
    why `lineage` is threaded through to fill in the `lineage` field the same way
    the Species File importer does.
    """
    node = {"id": None, "name": None, "rank": "GENUS", "children": []}
    gen = next((x for x in reversed(chain(r))
                if (x.get("taxonRank") or "").lower() == "genus"), None)
    gname = nodename((gen or {}).get("scientificName") or nm.split(" ")[0])
    gnode = buckets["GENUS"].get(gname)
    if gnode is None:
        gnode = {"id": node_id("GENUS", gname), "name": gname, "rank": "GENUS",
                 "children": []}
        if lin:
            gnode["lineage"] = lin
        buckets["GENUS"][gname] = gnode
    return gnode


def assemble_genera_tree(root, buckets, genus_rows, chain, stats):
    """Nest genera under tribes and subfamilies, then prune empty genera.

    Shared because getting this wrong is silent and expensive. A first attempt
    appended every genus straight to the family root and every species to the
    root as well, which produced 94 moth families full of childless genus nodes
    and failed the data contract's empty-genus check -- a shape no test on the
    importer itself would have caught, because the tree was well-formed JSON, just
    not the tree the portal expects.

    Assembled bottom-up, once per node: building each tribe inside the per-genus
    loop adds a tribe holding N genera to its subfamily N times and serialises
    its whole subtree N times over.
    """
    bare_genera = []
    tribe_genera = collections.defaultdict(list)
    subfam_tribes = collections.defaultdict(set)
    subfam_genera = collections.defaultdict(list)

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
        node = {"id": node_id("SUBFAM", sf), "name": sf, "rank": "SUBFAMILY",
                "children": []}
        for t in sorted(subfam_tribes.get(sf, ())):
            node["children"].append({"id": node_id("TRIBE", t), "name": t,
                                     "rank": "TRIBE", "children": tribe_genera[t]})
        node["children"].extend(subfam_genera.get(sf, []))
        subfam_nodes[sf] = node

    root["children"] = bare_genera + [subfam_nodes[k] for k in sorted(subfam_nodes)]

    # sanity_scan.py treats an empty genus as a defect and EMPTY_GENUS must stay 0,
    # so they are pruned here rather than shipped and cleaned up later.
    def prune(node):
        node["children"] = [c for c in (node.get("children") or [])
                            if c.get("rank") != "GENUS" or (c.get("children") or [])]
        for c in node["children"]:
            prune(c)
    prune(root)
    kept = sum(1 for _ in iter_genera(root))
    return kept


def iter_genera(node):
    """Every GENUS node in a family tree."""
    if node.get("rank") == "GENUS":
        yield node
    for c in node.get("children") or []:
        yield from iter_genera(c)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="", help="override the extracted source directory")
    ap.add_argument("--slug", default="orthoptera",
                    help="Species File slug; picks the archive and output order")
    ap.add_argument("--out", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--clean", action="store_true",
                    help="delete the output directory first (stale families on a "
                         "re-import). Off by default: --out may point at a parent "
                         "like hymenoptera/ that holds families from other sources, "
                         "and clearing it would delete them.")
    args = ap.parse_args()

    order = ORDER_DIR.get(args.slug, "?")
    if order is None:
        out = args.out  # caller supplies the Hymenoptera path
    elif args.out:
        out = args.out
    else:
        out = os.path.join(INSECTA, order)
    src = args.src or ensure_extracted(ARCHIVE_SLUG.get(args.slug, args.slug),
                                       work_dir_for(args.slug))
    rows = list(csv.DictReader(
        open(f"{src}/taxon.txt", newline="", encoding="utf-8", errors="replace"),
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
    for r in csv.DictReader(open(f"{src}/distribution.txt", newline="",
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
    for r in csv.DictReader(open(f"{src}/vernacularname.txt", newline="",
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


    # emit the taxonomy.json fragment for the caller
    frag = []
    for fid, info in fams.items():
        fname = nodename(by_id[fid].get("scientificName") or "")
        frag.append({"name": fname, "appSlug": slug(fname),
                     "speciesCount": info["species"]})
    frag.sort(key=lambda x: -x["speciesCount"])
    frag_path = f"/tmp/{args.slug}_families.json"
    with open(frag_path, "w", encoding="utf-8") as fh:
        json.dump(frag, fh, ensure_ascii=False, indent=1)
    print(f"  taxonomy fragment: {frag_path} ({len(frag)} families)")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    if args.clean and os.path.isdir(out):
        shutil.rmtree(out)
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
        # Sources occasionally list the same species twice -- Geocoris nocturnus
        # arrived from the Lygaeoidea file with identical name, authorship and year
        # in two rows. buildData's id scheme is name+authority based, so both
        # collapse onto one id and the family ships with a duplicated species.
        # Deduped on the triple that forms that id, which is also the only
        # definition of "the same species" this data supports.
        seen_species = set()
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
            # Per checklist, not per importer. A hardcoded "orthoptera species
            # file" made 12,325 nodes from Plecoptera, Mantodea and the rest
            # claim Orthoptera provenance -- wrong on both the source and the DOI
            # that has to be cited for it.
            node["sourcedFrom"] = f"{args.slug} species file"

            if rank in ("SPECIES", "SUBSPECIES"):
                key = (rank, nm, a, y)
                if key in seen_species:
                    stats["skipped-duplicate-species"] += 1
                    continue
                seen_species.add(key)
                node.setdefault("subspeciesCount", 0)
                node.setdefault("lineage", " > ".join(
                    filter(None, [lin, nodename((next((x for x in chain(r)
                        if (x.get('taxonRank') or '').lower() == 'genus'), {})).get('scientificName') or '')])))
                # attach to its genus, creating the genus if OSF omitted it
                gnode = genus_node_for(r, nm, buckets, chain, node.get("lineage") or "")
                gnode.setdefault("children", []).append(node)
            elif rank == "GENUS":
                buckets["GENUS"].setdefault(nm, node)
            else:
                buckets[rank].setdefault(nm, node)

        genus_rows = {nodename(x.get("scientificName") or ""): x
                      for x in info["rows"] if (x.get("taxonRank") or "").lower() == "genus"}
        kept_genera = assemble_genera_tree(root, buckets, genus_rows, chain, stats)
        if kept_genera != len(info["genera"]):
            stats["pruned-empty-genera"] += len(info["genera"]) - kept_genera

        root["genusCount"] = kept_genera
        root["enrichmentStatus"] = "empty"

        d = os.path.join(out, fslug, "src", "data")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{fslug}.json"), "w", encoding="utf-8") as fh:
            json.dump(root, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

        def count(n):
            return 1 + sum(count(c) for c in n.get("children") or [])
        total_nodes += count(root)
        written += 1

    print(f"\nwrote {written:,} family files under {out}")
    print(f"  {total_nodes:,} nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
