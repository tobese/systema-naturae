#!/usr/bin/env python3
"""Build and verify the external source manifest.

Every external dataset this project has downloaded lives under
`/Volumes/MacieExternal/sources/archives/<slug>/`, and the derived, regenerable
artifacts under `.../work/<slug>/`. This script owns the index of both.

Two things it is for:

  1. **Knowing what we have without re-downloading.** A Zenodo record or a GBIF
     dataset can be 500MB and take twenty minutes; the answer to "do we already
     have it" should be a file read, not a download.

  2. **Knowing what it may be used for.** The licence sits in the manifest next
     to the archive, not in a wiki page someone has to remember to update. The
     EOL harvester republishes whatever a project publishes and does not filter
     by licence -- of the ten harvests assessed, seven were non-commercial -- so
     an archive whose terms nobody recorded is how NC data ends up being used by
     accident.

`--verify` recomputes sha256 for every archive. That check earns its keep: a
truncated download produces a partial dataset that reads as "this source has poor
coverage" rather than as an error, which is a much more expensive thing to notice.

Usage:
    python3 scripts/sourcesManifest.py            # write manifest.json
    python3 scripts/sourcesManifest.py --verify   # check sizes + checksums
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = "/Volumes/MacieExternal/sources"
MANIFEST = os.path.join(ROOT, "manifest.json")

# slug -> (title, identifier, source url, licence, status, what we took)
# status: applied | partial | ready | assessed | refused
SOURCES = {
    "gbif-backbone": (
        "GBIF Backbone Taxonomy", "GBIF dataset d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
        "https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
        "CC0 / CC BY / CC BY-NC, per constituent dataset",
        "applied",
        "taxonomy backbone, vernacular names, country codes; the GBIF enrichers "
        "key off GBIF canonical names"),
    # Not an archive: the iNaturalist ledger is 31MB of gitignored JSON under
    # portal/data/, regenerable by scripts/fetchInatCommonNames.py, so it is not
    # stored under sources/. Recorded here because it is applied data and its
    # licence is the one NC exception in the project.
    "aphid-species-file": (
        "Aphid Species File", "DOI 10.15468/v4tboe",
        "https://www.gbif.org/dataset/214c3109-d37a-40f8-9c24-5b6e59915394",
        "CC BY 4.0", "applied",
        "IMPORTED. 5,544 species across 32 families, infraorder Aphidomorpha; "
        "created the Hemiptera order, which we did not have at all. Only 3 of "
        "the 32 families are extant, the rest are daggered fossils. "
        "Distribution is thin (664 rows); 5,067 synonyms remain unapplied"),
    "afromoths": (
        "Afromoths -- Afrotropical moths", "DOI 10.15468/s1kwuw",
        "https://www.gbif.org/dataset/65c9103f-2fbf-414b-9b0b-e47ca96c5df2",
        "CC BY 4.0", "ready",
        "NOT YET APPLIED. 29,983 accepted species across 137 families, and the "
        "standout is 91,005 distribution rows over 136 localities -- far richer "
        "than any checklist so far. 0% overlap: our Lepidoptera is two "
        "butterfly families (Nymphalidae, Papilionidae), these are moths. Needs "
        "a new importer: status is 'accepted' not 'valid', and there is no "
        "vernacularname.txt"),
    "species-file-psocodea": (
        "Psocoda Species File", "DOI 10.15468/baeaax",
        "https://www.gbif.org/dataset/6fb9265c-2d98-40ad-989d-7b6bf4820519",
        "CC BY 4.0", "applied",
        "12,113 taxa across 68 families, extending an order we held with 1,096 "
        "species. No English common names in the source"),
    "species-file-cockroach": (
        "Cockroach Species File (Blattodea)", "Species File Group",
        "https://www.gbif.org/dataset/3e812f13-bd5f-46b6-9bae-710766be526d",
        "CC BY 4.0", "applied",
        "5,312 taxa across 9 families; created the Blattodea order, which "
        "includes the termites (Isoptera is not ranked separately). 13,436 "
        "distribution rows and 144 English common names"),
    "species-file-coreoidea": (
        "Coreoidea Species File", "Species File Group",
        "https://www.gbif.org/dataset/e0a61544-c923-4fd7-8ed1-9b692655cf6b",
        "CC BY 4.0", "applied",
        "3,843 taxa across 7 families. A superfamily, so its families were "
        "placed under Hemiptera with the superfamily kept in lineage -- our "
        "ranks have no tier between ORDER and FAMILY"),
    "species-file-lygaeoidea": (
        "Lygaeoidea Species File", "Species File Group",
        "https://www.gbif.org/dataset/ca694ebf-2b52-4c67-b2e1-0f423149401c",
        "CC BY 4.0", "applied",
        "5,986 taxa across 16 families, also flattened into Hemiptera. No "
        "distribution rows at all -- names and structure only"),
    "species-file-embioptera": (
        "Embioptera Species File", "Species File Group",
        "https://www.gbif.org/dataset/203863b6-2adb-43f8-b648-959bcbaec091",
        "CC BY 4.0", "applied",
        "544 taxa across 16 families, extending an order we held with 272"),
    "species-file-mantophasmatodea": (
        "Mantophasmatodea Species File", "Species File Group",
        "https://www.gbif.org/dataset/c5b58f9d-54b3-4ecf-933e-a9f785a54924",
        "CC BY 4.0", "applied",
        "48 taxa across 2 families; created the order. Only 25 valid species in "
        "the source -- the order is far larger as fossils"),
    "zoobank": (
        "ZooBank -- ICZN Official Register", "Zoobank LSID",
        "https://zoobank.org", "open access registry; per-publication rights vary",
        "assessed",
        "NOT APPLIED. Reachable (the site gate is one confirmation per IP, not a "
        "block) and it is the only nomenclatural authority we have for animals, "
        "but measured coverage of our unauthenticated names is 8.8% +/- 1.4% over "
        "400 queries, projecting to ~34,600 of 395,528. Reaching even those means "
        "querying every candidate -- about seven days sequential -- against a "
        "service asking for less automated traffic. Worth doing if a bulk dump "
        "ever appears"),
    "inaturalist": (
        "iNaturalist taxa and names", "iNaturalist API",
        "https://www.inaturalist.org",
        "CC BY-NC 4.0 for data (photographs are separate, per-photo licences)",
        "applied",
        "10,485 species common names, filling empty slots only. Ledger is "
        "gitignored at portal/data/inat-common-names.jsonl, not archived here"),
    "wcvp": (
        "WCVP — World Checklist of Vascular Plants", "POWO/WCVP",
        "https://powo.science.kew.org/about/wcvp", "CC BY",
        "applied", "vascular plant names and distribution"),
    "mycobank": (
        "MycoBank MBList", "MycoBank / Index Fungorum",
        "https://www.mycobank.org/page/Name%20search%20page", "CC BY 4.0",
        "applied", "fungal authorship and name validity; compared against GBIF "
        "(28,253 disagreements, no renames applied)"),
    "orthoptera": (
        "Orthoptera Species File", "DOI 10.15468/nn7jhc",
        "https://www.gbif.org/dataset/af66d4cf-0fd2-434b-9334-9806a5efa6f7",
        "CC BY 4.0", "applied",
        "28,081 valid species across 80 families, authorship, hierarchy, "
        "distribution"),
    "nmnh": (
        "Smithsonian NMNH images from GBIF export", "DOI 10.5281/zenodo.20174554",
        "https://zenodo.org/records/20174554",
        "CC0 per media row (record is CC BY 4.0)", "applied",
        "5,628 specimen photographs; attribution waived by CC0"),
    "wikimedia-commons": (
        "Wikimedia Commons (EOL harvest)", "DOI 10.5281/zenodo.17509532",
        "https://zenodo.org/records/17509532",
        "CC BY 4.0 at record level; per-file licences recorded individually",
        "applied",
        "29,447 portraits with author + licence; also resolved author/licence "
        "for 175,978 filenames already held"),
    "species-fungorum": (
        "Species Fungorum Plus", "DOI 10.15468/ts7wsb",
        "https://www.gbif.org/dataset/bf3db7c9-5e5d-4fd0-bd5b-94539eaf9598",
        "CC BY 4.0", "assessed",
        "nothing yet. 90% name match measured; 1,791 synonyms pending, and a "
        "checklist carries no descriptions"),
    "world-spider-catalog": (
        "World Spider Catalog", "DOI 10.24436/2",
        "https://www.gbif.org/dataset/80dd9c94-241b-4d49-999f-c89de7648525",
        "CC BY 4.0", "assessed",
        "nothing yet. 487 synonyms pending; its 7,184 place names need a "
        "continent mapping first"),
    "eol-traitbank": (
        "EOL TraitBank — all trait data", "DOI 10.5281/zenodo.22129810",
        "https://zenodo.org/records/22129810", "notspecified", "assessed",
        "nothing yet. 11.4M trait rows, but values are ontology URIs rather "
        "than prose, and the licence is unspecified"),
    "usda-plants": (
        "USDA PLANTS structured data", "EOL harvest",
        "https://zenodo.org/records/20646743", "notspecified", "assessed",
        "nothing yet. 2,657 NativeRange records measured; values are Wikidata "
        "QIDs and GeoNames IDs needing resolution"),
    "zenodo-344329": (
        "Observation-count cross-tab", "Zenodo 344329",
        "https://zenodo.org/records/344329", "notspecified", "assessed",
        "nothing. A stale count table; live GBIF counts are preferable"),
    "species-file-phasmida": (
        "Phasmida Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 5,144 taxa; absent from our tree"),
    "species-file-plecoptera": (
        "Plecoptera Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 5,471 taxa; absent from our tree"),
    "species-file-mantodea": (
        "Mantodea Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 4,046 taxa; absent from our tree"),
    "species-file-dermaptera": (
        "Dermaptera Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 2,930 taxa; absent from our tree"),
    "species-file-grylloblattodea": (
        "Grylloblattodea Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 1,000 taxa; absent from our tree"),
    "species-file-zoraptera": (
        "Zoraptera Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 71 taxa; absent from our tree"),
    "species-file-coleorrhyncha": (
        "Coleorrhyncha Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 184 taxa; absent from our tree"),
    "species-file-chrysididae": (
        "Chrysididae Species File", "Species File Group", "", "CC BY 4.0", "applied",
        "IMPORTED. 239 taxa; extended Hymenoptera from 4 families to 5"),
    "fishbase": (
        "FishBase (EOL harvest)", "DOI 10.5281/zenodo.22739608",
        "https://zenodo.org/records/22739608",
        "mixed; images are CC BY-NC 3.0", "partial",
        "English names measured: only 28 marginal after GBIF vernacular, so "
        "not applied. Images not used (NC)"),
    "bioimages": (
        "BioImages — the Virtual Fieldguide (UK)", "DOI 10.5281/zenodo.21123026",
        "https://zenodo.org/records/21123026", "CC BY-NC-SA 3.0", "refused",
        "nothing. 132,528 media rows, non-commercial"),
    "calphotos": (
        "CalPhotos — Moorea Biocode", "DOI 10.5281/zenodo.15597434",
        "https://zenodo.org/records/15597434", "CC BY-NC-SA 3.0", "refused",
        "nothing. 20,942 media rows, non-commercial"),
    "antweb": (
        "AntWeb", "DOI 10.5281/zenodo.19027382",
        "https://zenodo.org/records/19027382", "CC BY-NC-SA 4.0", "refused",
        "nothing. 140,143 media rows, non-commercial. Its long text is textmined "
        "AntCat citations, not prose"),
    "flickr-eol": (
        "Flickr — Encyclopedia of Life group", "DOI 10.5281/zenodo.20272755",
        "https://zenodo.org/records/20272755",
        "mostly non-commercial per image", "refused",
        "nothing. Only 9,703 of 77,404 taxa carry a free-to-reuse licence"),
}


# Applied sources whose payload is regenerable and deliberately not archived, so
# the "no archive on disk" warning should not fire for them every run.
NO_ARCHIVE = {"inaturalist", "zoobank"}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def dir_stats(d):
    files = []
    total = 0
    for dp, _dd, fs in os.walk(d):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            files.append({"name": os.path.relpath(p, d), "bytes": sz})
            total += sz
    return files, total


def build(verify: bool):
    if not os.path.isdir(ROOT):
        sys.exit(f"FATAL: {ROOT} not found.\n"
                 f"       The external volume may not be mounted. Sources live on\n"
                 f"       /Volumes/MacieExternal, which is a separate disk --\n"
                 f"       unmounting it does not affect the repo, but nothing that\n"
                 f"       reads a downloaded dataset can work until it is back.")
    entries = {}
    for slug, (title, ident, url, licence, status, took) in sorted(SOURCES.items()):
        adir = os.path.join(ROOT, "archives", slug)
        wdir = os.path.join(ROOT, "work", slug)
        files, total = dir_stats(adir) if os.path.isdir(adir) else ([], 0)
        work_files, work_total = dir_stats(wdir) if os.path.isdir(wdir) else ([], 0)
        rec = {
            "title": title,
            "identifier": ident,
            "url": url,
            "licence": licence,
            "status": status,
            "took": took,
            "archive": {"path": f"archives/{slug}", "bytes": total, "files": files},
            "work": {"path": f"work/{slug}", "bytes": work_total, "files": work_files},
        }
        if verify and files:
            for f in files:
                p = os.path.join(adir, f["name"])
                f["sha256"] = sha256(p)
        entries[slug] = rec

    doc = {
        "root": ROOT,
        "note": ("Archives are immutable downloads; work/ holds derived artifacts "
                 "that can be regenerated from them and deleted freely. Licence "
                 "travels with the file on purpose: the EOL harvester does not "
                 "filter by licence, so 7 of the 10 harvests assessed were "
                 "non-commercial."),
        "sources": entries,
    }
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="recompute sha256 (slow)")
    ap.add_argument("--out", default=MANIFEST)
    args = ap.parse_args()

    doc = build(args.verify)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    tot = sum(r["archive"]["bytes"] for r in doc["sources"].values())
    wtot = sum(r["work"]["bytes"] for r in doc["sources"].values())
    counts = {}
    for r in doc["sources"].values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"wrote {args.out}")
    print(f"  {len(doc['sources'])} datasets · archives {tot/1e9:.2f} GB · "
          f"work {wtot/1e9:.2f} GB")
    print("  status:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    missing = [s for s, r in doc["sources"].items()
               if not r["archive"]["files"] and s not in NO_ARCHIVE]
    if missing:
        print(f"  WARNING no archive on disk: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
