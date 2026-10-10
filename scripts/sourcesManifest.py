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
        "Distribution is thin (664 rows) and is applied. The 5,067 unapplied "
        "synonyms are held by policy, not left over: COL's 2.6M and every other "
        "source's synonyms are held back too, because importing them is a "
        "taxonomy decision rather than a data one"),
    "afromoths": (
        "Afromoths -- Afrotropical moths", "DOI 10.15468/s1kwuw",
        "https://www.gbif.org/dataset/65c9103f-2fbf-414b-9b0b-e47ca96c5df2",
        "CC BY 4.0", "applied",
        "APPLIED by scripts/importAfromoths.py, which the entry previously said "
        "was still to write. Measured against the tree: 29,983 of 29,983 species "
        "present, spread over 94 family files, every one stamped "
        "sourcedFrom='afromoths'. Our Lepidoptera went from two butterfly "
        "families to 143. The 137 in this entry is how many families the source "
        "has; 94 is how many we hold, the difference being families whose "
        "species our other sources already covered. The 91,005 distribution "
        "rows ARE used: importAfromoths.py reads distribution.txt and maps its "
        "ISO country codes through CC2CONT into `continents`, which is what "
        "makes this source worth having -- no other checklist we hold carries "
        "occurrence data for moths. 87.3% of its 35,893 nodes carry a "
        "continent; the remainder are countries left unmapped on purpose (48 IO "
        "British Indian Ocean Territory, 15 TF French Southern Territories). An "
        "earlier version of this entry said those rows were 'still unused', "
        "which was wrong, and '136 localities' was never this source's shape: "
        "the file holds 65 country codes, not free text. Needs its own importer "
        "because the DwCA status is 'accepted' not 'valid' and there is no "
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
        "service asking for less automated traffic. That objection is now DEAD: "
        "ChecklistBank dataset 2037 is the same publisher's bulk export, CC0, "
        "version 2026-08-29, one archive. The verdict did not improve, because "
        "the bulk export is missing the one column that would make it "
        "importable -- see `checklistbank-2037`. Both routes declined, for "
        "different reasons: this one on cost, that one on the absent "
        "accepted/synonym split. The 8.8% +/- 1.4% above was measured "
        "correctly, unlike the shard sums in the 2026-10-09 triage"),
    "catalogue-of-life": (
        "Catalogue of Life, Base Release", "DOI 10.48580/dgz5n (ChecklistBank 316321)",
        "https://www.catalogueoflife.org/data/download",
        "CC BY 4.0", "applied",
        "Stage 1 applied: 427,804 species merged into the 3,413 animalia "
        "families we already had, 431,305 authorship records. Stage 2 applied "
        "to Fungi and Chromista (importColStage2.py): 27,812 species, of which "
        "27,462 in 719 new family files and 350 into 95 existing ones; Fungi "
        "773 -> 1,193 families, Chromista 703 -> 1,002. Stage 2 then applied to "
        "Animalia: 672,185 species, 5,152 new family files and 33 enriched in "
        "place, families 5,472 -> 10,601, orders 394 -> 721. Stage 2 then "
        "applied to the three remaining declared kingdoms (2026-10-09): 850 "
        "species into 89 existing plantae family files, 0 new family files, 0 "
        "new orders, 93 already present. Protozoa and Archaea yielded nothing: "
        "COL holds no accepted species for either outside families we already "
        "had. That closes Stage 2 for all six kingdoms in "
        "kingdom-config.json. What is deliberately NOT taken is not outstanding "
        "work: the 2.6M synonyms and the bacteria/virus clades are both policy "
        "decisions -- a synonym is a taxonomy decision, and see the paragraph "
        "below on the clades. Bacteria and viruses are NOT two "
        "kingdoms and are not a kingdom-config.json problem: COL holds them as "
        "17 clades at kingdom rank (Bacillati 13,873 species, Pseudomonadati "
        "12,368, Orthornavirae 7,201, Heunggongvirae 6,521, Shotokuvirae 2,351, "
        "and 12 smaller), so filtering on kingdom name reaches almost none of "
        "them and how to group them is an open decision -- see "
        "docs/dataset-inbox.md. COL's 2.6M synonyms are still not imported. "
        "ColDP with per-name source attribution is not currently downloadable "
        "(404); the DwCA has 7 columns and no source field, so provenance is "
        "recorded as COL rather than per-checklist"),
    "ncbi-taxonomy": (
        "NCBI Taxonomy", "DOI 10.15468/rhydar (GBIF dataset "
        "fab88965-e69d-4491-a04d-e3198b626e52, published 2026-04-17)",
        "https://www.gbif.org/dataset/fab88965-e69d-4491-a04d-e3198b626e52",
        "CC0", "assessed",
        "overlap-measured 2026-10-08: 197,971 accepted species, 44,946 held "
        "(27.1%), 120,665 species not held (of which 1,853 are prokaryote/virus "
        "names on hold by decision). 3,120 of its 10,907 families are not in the "
        "tree. The only candidate that carries Bacteria and Viruses as real "
        "divisions with real authorities, which is exactly what COL will not give "
        "us: COL holds the prokaryotes and viruses in 17 clades at kingdom rank, "
        "so neither '--kingdom Bacteria' nor '--kingdom Viruses' reaches them "
        "(see docs/dataset-inbox.md). Against that, GBIF Backbone is already "
        "applied and is itself built from NCBI among others, so for the kingdoms "
        "we do hold this is largely a second copy of names we already have. "
        "Its value is narrower and real: prokaryote and viral coverage, and the "
        "type material and literature citations the NCBI record carries and no "
        "checklist we hold does. CC0, so licensing is not an obstacle. Not "
        "downloaded."),
    "gtdb": (
        "Genome Taxonomy Database r232", "DOI 10.15468/dpzg84 (GBIF dataset "
        "a97f36e5-ded1-49cc-bdec-ac6170fc7b9c); ColDP endpoint "
        "gtdb_r232_coldp.zip, issued 2026-08-25",
        "https://hosted-datasets.gbif.org/gtdb/gtdb_r232_coldp.zip",
        "CC BY 4.0", "assessed",
        "DOWNLOADED AND READ, and it settles the question it was fetched for. "
        "242,895 accepted name usages: 189,801 bacterial species in 3,967 "
        "families plus 10,122 archaeal, 125 phyla, two domains (Bacteria, "
        "Archaea) and no kingdom rank anywhere. "
        "That last fact is the one: COL's eight prokaryote clades -- Bacillati, "
        "Pseudomonadati, Thermotogati, Fusobacteriati, Methanobacteriati, "
        "Thermoproteati, Nanobdellati, Promethearchaeati -- return zero hits at "
        "any rank. They are not older spellings of GTDB names but a different "
        "convention (-ati where GTDB writes -ota) on the same organisms, ranked "
        "one level too high. COL's 'Bacillati' is GTDB's Bacillota, a phylum. "
        "So the tree's existing treatment of Archaea -- GTDB phyla such as "
        "Methanobacteriota and Thermoproteota as kingdom-rank nodes -- is the "
        "authority's own, and the bacteria question reduces to applying the "
        "same rule. "
        "Scope note: GTDB covers Bacteria and Archaea only and holds no viral "
        "taxa, so it says nothing about the virus half. See "
        "docs/bacteria-and-viruses.md."),
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
    "afrotropical-bees": (
        "Catalogue of Afrotropical Bees", "GBIF dataset "
        "8de37d73-4016-4dba-9934-b3ac24cb15c6; IPT resource "
        "catalogueofafrotropicalbees; Connal Eardley (Agricultural Research "
        "Council, Pretoria), published via SAIAB",
        "https://www.gbif.org/dataset/8de37d73-4016-4dba-9934-b3ac24cb15c6",
        "CC BY 4.0 (stated in the archive's own eml.xml intellectualRights)",
        "applied",
        "APPLIED by scripts/importBees.py: 7,082 species, every one stamped "
        "sourcedFrom='afrotropical bees'. This entry did not exist until "
        "2026-10-04, which is the failure this registry exists to prevent -- the "
        "data was in the product and in the tree for a week with its licence "
        "recorded nowhere, and the archive sat unregistered on the volume "
        "beside four others. Licence read out of bees.zip rather than assumed: "
        "CC BY 4.0, so citable with attribution. DwCA in the older profile "
        "(taxon.txt, tab-separated)."),
    "msw3": (
        "Mammal Species of the World, 3rd edition", "ASM, Johns Hopkins "
        "University Press, 2005",
        "https://www.mammaldiversity.org/", "ALL RIGHTS RESERVED",
        "refused",
        "NOT USED, and deliberately. The archive's own eml states: 'This online "
        "list was compiled under the auspices of the American Society of "
        "Mammalogists. Copyright 2005 Johns Hopkins University Press. All "
        "rights are reserved.' Zero species in the tree derive from it. Unlike "
        "the four refused media harvests this is a taxonomic authority rather "
        "than NC photographs, which makes it more tempting and not less "
        "restricted: deriving public species records from an all-rights-reserved "
        "compilation is redistribution of derived data, which is exactly what the "
        "EOL harvester republishes without filtering on licence. Kept on disk so "
        "the decision can be re-checked if permission is ever obtained. Mammal "
        "names are covered regardless: COL supplies 1.13M species including every "
        "mammal we hold."),
    "iczn-lists": (
        "Official Lists and Indexes of Names in Zoology (ICZN)", "ICZN, "
        "packageId da38f103-4410-43d1-b716-ea6b1b92bbac",
        "https://www.iczn.org/", "CC0 1.0 (waived, per the archive's eml.xml)",
        "applied",
        "VALIDATED 2026-10-09 by scripts/validateIczn.py, which parses the "
        "archive's `names.txt` positionally -- the file has no header and the "
        "column order is the one in the README's `\\copy names (...)` "
        "statement -- and matches our names against the Commission's rulings. "
        "12,403 names (8,158 available, 4,043 unavailable, 202 blank) against "
        "1,755,597 animalia species: 1,159 matched (0.07%), of which 983 are "
        "available and 157 are **unavailable** -- the finding no amount of "
        "name or id matching had surfaced, across 72 families. The opinions "
        "column carries each ruling (a plenary power, a Direction, a homonymy "
        "decision), which is the only place that reasoning lives. "
        "This is not an import and does not write a data field: the lists are "
        "a judgement about availability, not a record of which species exist, "
        "so 0.1% coverage means it fills no gap and the finding is a report "
        "rather than a boolean. Full list in docs/reports/iczn-lists.md. "
        "The archive is a GitHub clone, not a DwCA as the old note said; "
        "it also carries a 5.7MB PDF of the lists themselves and an opinions "
        "directory, neither of which is parsed."),
    "taiwan-endemic": (
        "Endemic species in Taiwan", "GBIF DwCA, 3 members (taxon.txt)",
        "(no DOI in the archive's eml.xml)", "CC0 1.0 (waived, per the eml.xml)",
        "assessed",
        "NOT YET APPLIED, and assessed as narrow: 0.5 MB, one DwCA, endemic "
        "species of one island nation. Not a gap-filler -- it overlaps Taiwan "
        "material we already hold from COL and POWO. Worth taking only for the "
        "occurrence data if the distribution table carries it, which is the one "
        "thing here that is not a name we already have."),
    "ictv-msl": (
        "ICTV Master Species List (MSL41)", "DOI 10.5281/zenodo.19154110; "
        "published 2026-03-21; the 2025-2026 ICTV taxonomy, ratified February "
        "2026",
        "https://zenodo.org/records/19154110", "CC BY 4.0", "assessed",
        "NOT DOWNLOADED, and deliberately so: viruses are on hold until further "
        "notice, so registering the source is the whole of the work for now. "
        "Recorded because it is the virus authority -- the one source that states "
        "the official ICTV taxonomy, which COL and Wikidata both decline to give "
        "at a usable rank. "
        "Two things to know before anyone does download it. It is an XLSX "
        "(ICTV_Master_Species_List_2025_MSL41.v1.xlsx, 1.80 MB), a fifth format "
        "this repo has no reader for, alongside NEWICK and DOT -- see "
        "docs/archive-formats.md. And sources/archives/ictv-msl/ exists but is "
        "EMPTY, left by an abandoned download, which is why this entry appears "
        "now rather than when the archive landed. "
        "Also CC BY 4.0, so citable with attribution once taken."),
    "ildis": (
        "ILDIS -- World Database of Legumes", "DOI 10.48580/d382 "
        "(ChecklistBank dataset 1015); version 12, May 2014, issued 2014-05-05",
        "https://api.checklistbank.org/dataset/1015/archive.zip",
        "CC BY 4.0 (from the ChecklistBank dataset record; the archive carries "
        "no metadata file)", "applied",
        "APPLIED, and the largest single gain in this batch: **16,296 species "
        "into Fabaceae**, which went 24,496 -> 41,771. Of 16,371 species "
        "offered, only 64 were already held. It was the one genuine gap in a "
        "batch that also contained FishBase, where 600 of 600 sampled species "
        "were already present. "
        "Three things about the archive, all of which cost time: the endpoint is "
        "called archive.zip and answers content-type application/zip but returns "
        "a gzip'd TAR, so opening it as a zip raises BadZipFile on a perfectly "
        "good download; the tables are ILDIS's own (AcceptedSpecies.tsv, "
        "Synonyms.tsv, CommonNames.tsv, ...) rather than COL's Taxon/Name split; "
        "and it is the only one of the three shapes whose denormalised chain "
        "columns are actually populated, so placement needs no parent walk. "
        "scripts/colChecklist.py now normalises all three to one internal shape."),
    "reptile-db": (
        "The Reptile Database", "DOI 10.48580/d37s (ChecklistBank dataset 1008); "
        "version 2026-06, issued 2026-06-24; contact Peter Uetz",
        "https://api.checklistbank.org/dataset/1008/archive.zip",
        "CC BY 4.0 (from the archive's own Metadata.json)", "applied",
        "APPLIED, and it turned out to be very nearly a duplicate of what we "
        "already had -- which is the finding, and the reason it is worth having "
        "been checked rather than assumed. 15,612 accepted species offered, "
        "15,611 already on disk, **1 added** (to Scincidae). "
        "The earlier triage of this source called it 'the larger gap of the two' "
        "and that was wrong: it compared our 16,612 node speciesCount against "
        "the source's 34,366 name usages, but 34,366 includes 17,325 synonyms "
        "and 2,962 subspecies. Name against name, it is a near-total "
        "overlap. Four species were refused rather than placed, all with no "
        "family in the source."),
    "craneflies": (
        "Catalogue of Craneflies of the World", "DOI 10.48580/d37p "
        "(ChecklistBank dataset 1005); version Apr 2025, issued 2025-04-10",
        "https://api.checklistbank.org/dataset/1005/archive.zip",
        "CC0 (from the archive's own Metadata.json)", "applied",
        "APPLIED. 16,061 accepted species offered across 4 families, of which "
        "**372 were added**: 370 to Limoniidae and 2 to Tipulidae. "
        "This source is the clearest case in the project of a name count being "
        "the wrong measure. The canonical index -- a snapshot taken before the "
        "Stage 2 import -- scored 15,563 of these species as new; measured "
        "against the family files on disk it is 378, and the importer's own "
        "merge settled it at 372, with 15,191 already present. Our "
        "crane-fly families hold 15,454 names, so CCW roughly doubles a group "
        "we are already strong in rather than opening a hole."),
    # Assessed 2026-10-05 from six ChecklistBank datasets offered together.
    # None was taken, and none was downloaded: scripts/sampleDatasetOverlap.py
    # pages a sample of each through the API and tests it against the tree, so
    # six verdicts cost six minutes. Full write-ups in docs/dataset-inbox.md.
    # The three that are declined on licensing rather than coverage are the
    # point of registering them at all -- "no licence stated" is not a
    # permissive licence, and that is not visible from the name count.
    # The fifth batch, 2026-10-05: the top of ChecklistBank by size rather than
    # a pile of group checklists. Measured with scripts/apiOverlapReport.py,
    # which pages a dataset's whole accepted list through the API instead of
    # sampling 600 names -- the sampling bias on an alphabetical list was worth
    # 23 points, which is most of a dataset's apparent gap. Full write-ups in
    # docs/dataset-inbox.md.
    "wfo-plant-list": (
        "World Flora Online Plant List 2026-06 (ChecklistBank dataset 2004)",
        "DOI 10.5281/zenodo.7460141; version 2026-06 01, issued 2026-06-21",
        "https://api.checklistbank.org/dataset/2004/archive.zip",
        "CC0", "applied",
        "TAKEN and applied. 1,663,770 name usages, 408,939 accepted "
        "species/subspecies, 1,026,322 synonyms excluded. 158,701 species added "
        "into 719 existing plant families; 1,071 refused, which is 0.26% -- the "
        "reason being that 97.4% of WFO's 738 families are ones we already "
        "hold, so the import extends the tree rather than manufacturing "
        "placeholders. That ratio is the whole argument for this source over "
        "Wikispecies, which refused 191,866 for want of families we lack. "
        "Arrives as the standard ChecklistBank DwCA (taxon.tsv + name.tsv + "
        "synonym.tsv), which colChecklist.load() dispatches on already."),
    "checklistbank-2144": (
        "ITIS, The Integrated Taxonomic Information System (dataset 2144)",
        "DOI 10.48580/d4ky; version 2026-08-26",
        "https://api.checklistbank.org/dataset/2144/archive.zip",
        "CC0", "applied",
        "TAKEN and applied, on the user's authorisation over my recorded "
        "reservation. 993,349 name usages, 582,013 accepted species/subspecies. "
        "68,813 added across 4,776 families in all six kingdoms; 259,037 "
        "already held, 31,760 refused (5.5%) and recorded in the pending store. "
        "The naive API estimate was ~150,000 new; the importer's own test found "
        "68,813, because its held-check undercounts and merge_family catches "
        "another 167,074 already present. "
        "The reservation, kept on the record: ITIS is a synoptic management "
        "taxonomy with a North-American centre of gravity and a tail of obsolete "
        "concepts, the same judgement call as taking COL's 2.6M synonyms. One "
        "consequence arrived immediately -- ITIS filed the nudibranch "
        "Actinocyclus bifrons Karsten, 1905 into the diatom family "
        "Hemidiscaceae, so its chromista copy was removed and our curated "
        "nudibranch placement kept. That is the shape of the risk this source "
        "carries, so expect more of it. "
        "Note the export endpoint returns a multipart/form-data wrapper "
        "containing coldp.zip rather than a bare archive, so the DwCA has to be "
        "unwrapped from the first PK signature; the ColDP edition IS available "
        "for this dataset even though /coldp.zip 406s."),
    "checklistbank-310868": (
        "Tropicos (dataset 310868)",
        "DOI 10.48580/dgrnm; version 2021, issued 2021-11-04",
        "https://api.checklistbank.org/dataset/310868/archive.zip",
        "CC BY", "assessed",
        "NOT taken. 1,368,229 name usages, 977,904 accepted species, and only "
        "19.4% held over 20,580 measured -- the largest apparent gap in its "
        "batch, and declined anyway. It is 2021 data offered alongside a 2026 "
        "WFO list covering the same ground, so taking it would import older "
        "nomenclatural data over newer. Its 44.0% family coverage says most of "
        "what it offers is families WFO handles and we do not."),
    "checklistbank-1028": (
        "Species Fungorum, Index Fungorum API crawl (dataset 1028)",
        "DOI 10.48580/d38h; version 2026-09-24",
        "https://api.checklistbank.org/dataset/1028/archive.zip",
        None, "assessed",
        "NOT taken, blocked on permission rather than coverage. 541,761 name "
        "usages, three months old, and 30.1% of its species are new to us "
        "(69.9% held over 70,961 measured) with 85.3% of its families held -- on "
        "the numbers the second-best source in its batch. ChecklistBank records "
        "NO licence for it, the same position as 1023 and 1025, and no stated "
        "terms is not permissive terms. Worth one email to Index Fungorum; the "
        "archive is otherwise ready to take. The action is on BACKLOG.md: one "
        "email to Missouri Botanical Garden, which runs Index Fungorum and "
        "Tropicos alike."),
    "checklistbank-2007": (
        "IRMNG, Interim Register of Marine and Nonmarine Genera (dataset 2007)",
        "DOI 10.48580/d4f8; version 2026-09-16",
        "https://api.checklistbank.org/dataset/2007/archive.zip",
        "CC BY", "assessed",
        "NOT taken, and not comparable to the species sources. 269,528 accepted "
        "genera and 2 species: it is a register of genus names, so '59.9% of its "
        "genera are held' answers a different question from the rest of the "
        "batch. Its value is nomenclatural availability, which this tree does "
        "not model. Sampled at species rank before the tooling was fixed, it "
        "reported a confident 100% already-held from a two-name sample."),
    "worms": (
        "World Register of Marine Species (GBIF dataset "
        "2d59e5db-57ad-41ff-97d6-11f5fb264527)",
        "CC BY 4.0; published 2026-09-01; 1,219,588 species in GBIF",
        "https://www.marinespecies.org/",
        "CC BY 4.0", "assessed",
        "NOT taken, and blocked on a person rather than on tooling. This is the "
        "source that would close the largest remaining gap in the animal tree, "
        "which is marine worms: measured after the ITIS import, 17.9% of their "
        "species are held. Platyhelminthes is 0 of 600 -- the phylum exists with "
        "families under Animalia and no species at all -- and Polychaeta 30.8%, "
        "Nemertea 27.0%, Sipunculida 13.5%, Priapulida 22.0%. That is the "
        "inverse of the usual gap and neither WFO nor ITIS touched it. "
        "Acquisition is deliberate, not technical: GBIF's DwC-A endpoint for "
        "this dataset returns HTTP 403 and its description says to obtain a full "
        "copy from marinespecies.org/usersrequest.php. GBIF's API would let us "
        "enumerate all 1.2M names, but the offset ceiling is 100,000 so it is "
        "~4,000 paged requests, and scraping around an explicit request form is "
        "the wrong answer to being told to request. Worth registering as the "
        "highest-value blocked item. The action is on BACKLOG.md under 'Open "
        "right now': request marinespecies.org/usersrequest.php. Recorded as "
        "NO_ARCHIVE because nothing was fetched, and because the access route is "
        "a request form rather than a URL -- listing an archive path here would "
        "imply a download that does not exist."),
    "checklistbank-2037": (
        "ZooBank (ChecklistBank bulk export)", "DOI 10.48580/d4g9",
        "https://www.checklistbank.org/dataset/2037",
        "CC0 (confirmed in the archive's own eml.xml)", "assessed",
        "NOT TAKEN, and downloaded: 81MB DwCA at "
        "archives/checklistbank-2037/archive.zip, 527,127 rows, version "
        "2026-08-29. Measured 2026-10-09 from the archive: 275,961 names "
        "offered, 114,908 held, 160,728 NOT held, 148 of 427 families absent. "
        "The licence, the vintage and the effort are all fine; what is missing "
        "is one column. This is a NOMENCLATURAL register (ChecklistBank types "
        "it `nomenclatural`) and the DwCA writes `accepted` on every row with "
        "every acceptedNameUsageID self-referencing -- 283,875 species rows, all "
        "accepted. The ColDP edition carrying the per-name accepted/synonym "
        "split returns HTTP 406. Without it there is no way to separate the new "
        "taxa from the synonymy, so importing it is the same decision as "
        "importing COL's 2.6M synonyms, which this project holds back by "
        "policy. Only 909 of the 160,728 are ZooBank's own `Aa...` placeholder "
        "index names; the rest look like ordinary binomials (Ababactus "
        "depressus), which is what makes the register hard to refuse on data "
        "quality alone. "
        "RE-ASSESSED 2026-10-10: the archive is still on disk and still the "
        "same version. `/dataset/2037/coldp.zip` still 406s, but "
        "`/dataset/2037/export?format=ColDP` works -- it is a classification-"
        "tree JSON, not a ColDP archive -- and it carries no synonym status "
        "either: 524,236 `accepted`, 2,933 `provisionally accepted`, zero "
        "`synonym`. The flat DwCA's own taxonomicStatus agrees -- 527,106 "
        "`accepted`, 21 `invalid`, and those 21 are the only rows where id != "
        "acceptedNameUsageID, pointing not to a synonym but to an obsolete "
        "18th-century Linnaean group name (e.g. Clupeidae -> \"Abdominales "
        "Linnæus, 1758\") -- noise, not synonymy. So the missing column "
        "is not an export-format gap to wait out: ZooBank's data model has no "
        "accepted/synonym concept to export, in any format ChecklistBank "
        "offers. Verdict unchanged, and nothing left to re-open on"),
    "checklistbank-311094": (
        "BOLD Systems Taxonomy -- Insecta", "DOI 10.48580/dgrxf",
        "https://www.checklistbank.org/dataset/311094",
        "CC BY 4.0", "applied",
        "APPLIED 2026-10-09 by scripts/importColChecklist.py: 388,724 accepted "
        "species/subspecies offered, 122,474 already held, 214,617 staged, "
        "**58,587 species added** into 466 existing families across animalia, "
        "194,235 found already present on merge, 33,952 refused as needing a "
        "family we do not have (63 families, recorded in the pending-family "
        "store), 7 non-binominal. Animalia went 1,718,864 -> 1,777,451 "
        "species. Insecta was the largest single line in the 2026-10-08 gap "
        "report at 973,576 missing species. No new families and no new orders: "
        "the source fills families we already hold rather than scaffolding. "
        "Downloaded: 9.5MB ColDP at archives/checklistbank-311094/archive.zip, "
        "version 2025-07-17. Measured 2026-10-09 from the archive: 371,044 "
        "names offered, 300,035 held (80.9%), 71,009 NOT held, 165 of 1,186 "
        "families absent -- the largest opening in the 2026-10-09 batch. The "
        "misses are real gaps rather than name artefacts: Ambulyx regia, "
        "Theretra mercedes and Cocytius mephisto are all confirmed absent from "
        "the index, which is what a cosmopolitan hawkmoth looks like when "
        "Afromoths (Afrotropical) and the Orthoptera Species File (one order) "
        "are the only Lepidoptera-adjacent sources applied. AUDITED 2026-10-09 "
        "with scripts/auditChecklistArchive.py: on the 321,784 names both "
        "sources hold, family placement agrees 90.2% and disagrees on 6,033 "
        "(1.9%). The disagreements are systematic, not noise -- BOLD raises "
        "subfamilies we keep inside larger families (Oecanthinae as "
        "Oecanthidae 1,407, Ascalaphidae as Myrmeleontidae 436, Bembicinae as "
        "Bembicidae 290, Philanthinae as Philanthidae 151), which is a "
        "legitimate but different circumscription. Name form is clean: 384,317 "
        "plain binomials, 20,021 trinomials, 7 hybrids. One real weakness: "
        "only 116,239 of 489,672 taxa carry authorship (23.7%), so most names "
        "arrived unciteable against a later edition. "
        "The import ran twice and the log row understates it: the first run "
        "wrote 319 of 466 files and was interrupted before logging, before "
        "recording refusals and before resyncing speciesCount. A dry run is "
        "what showed it -- 20,382 species still addable in 147 families whose "
        "files had never been written. Re-running finished it, the importer "
        "being idempotent for families that gained nothing. "
        "The 6,033 family disagreements were then resolved by "
        "scripts/dedupeSpeciesAcrossFamilies.py as the audit predicted, the "
        "curated placement winning over the source's: Oecanthus nigricornis "
        "is held once, in Gryllidae, and not again in Oecanthidae. "
        "21 cross-kingdom homonyms arrived with it -- thrips whose genus names "
        "coincide with recently described plant genera, plus Phoenix "
        "reclinata, a palm that is also a scale insect -- and all 21 are gone "
        "again, the plant half of each pair having been one of the in-family "
        "duplicates merged the same day"),
    "checklistbank-55434": (
        "Global Lepidoptera Index (GLI)", "DOI 10.48580/d49xk",
        "https://www.checklistbank.org/dataset/55434",
        "CC BY 4.0", "applied",
        "APPLIED 2026-10-09 by scripts/importColChecklist.py: 196,874 accepted "
        "species/subspecies offered, 143,771 already held, 20,637 staged, "
        "**6,947 species added** into 72 existing families across animalia, "
        "13,690 found already present on merge, 121 refused as needing a family "
        "we do not have (recorded in the pending-family store), 199 "
        "non-binominal. Animalia went 1,711,917 -> 1,718,864 species. No new "
        "families and no new orders: 141 of GLI's 142 families were already "
        "held, which is why this extends the tree instead of scaffolding it. "
        "Both verifyTree duplicate-id counts were unchanged by the import (35 "
        "and 322,928, both pre-existing). Downloaded: 19.9MB ColDP at "
        "archives/checklistbank-55434/"
        "archive.zip, version 1.1.26.247 issued 2026-09-04 -- a month old, the "
        "best vintage in its batch. Measured 2026-10-09 from the archive: "
        "164,529 names offered, 156,340 held (95.0%), 8,189 NOT held, and 141 "
        "of its 142 families already held, so it extends the tree rather than "
        "scaffolding placeholders. Lepidoptera is our weakest large order after "
        "Afromoths covered only the Afrotropics. An earlier pass put this at 80 "
        "real misses and declined it: that number came from a broken shard sum, "
        "and its 671 raw miss was itself 591 subgenus trinomials -- two errors "
        "of opposite sign on the same page"),
    "checklistbank-1024": (
        "World Checklist of Selected Plant Families (WCSP)", "DOI 10.48580/d38c",
        "https://www.checklistbank.org/dataset/1024",
        "CC BY 4.0", "assessed",
        "NOT TAKEN, vintage. 416,075 name usages, all 116 families held, "
        "accepted-species count 120,288 -- and the edition is 2017-08-25, nine "
        "years old, against WFO Plant List 2026-06 (CC0, applied), POWO and the "
        "World Checklist of Vascular Plants (applied). The same verdict as "
        "Tropicos: importing older nomenclatural data over newer is a taxonomy "
        "decision, not a data one. Its archive endpoint also returns HTTP 404, "
        "so it cannot be measured offline at all"),
    "checklistbank-1021": (
        "Orthoptera Species File, ChecklistBank edition (dataset 1021)",
        "DOI 10.48580/d388; version Oct 2026, issued 2026-10-01",
        "https://www.checklistbank.org/dataset/1021",
        "CC BY", "assessed",
        "NOT taken. 30,890 name usages, 88.3% of a 600-name sample already "
        "held -- the lowest overlap in its batch, which reads as an opening but "
        "is not one: this is the current release of manifest `orthoptera`, "
        "which we applied from GBIF at 28,081 species, and the 27,194 species "
        "carrying sourcedFrom 'orthoptera species file' come from it. What is "
        "left is one release cycle of taxonomic churn in one group, not names "
        "we are missing. Re-importing as a replacement and diffing is the only "
        "clean way to take it."),
    "checklistbank-1022": (
        "Parhost World Database of Fleas (dataset 1022)",
        "DOI 10.48580/d389; version 2, issued 2005-11-14",
        "https://www.checklistbank.org/dataset/1022",
        "other", "assessed",
        "NOT taken. 2,047 name usages, 96.7% of a 600-name sample already "
        "held. ChecklistBank records the licence as 'other', so permission is "
        "not established -- which settles it independently of the weak "
        "coverage argument."),
    "checklistbank-1023": (
        "Phyllachorales (dataset 1023)",
        "DOI 10.48580/d38b; issued 2017-10-27",
        "https://www.checklistbank.org/dataset/1023",
        None, "assessed",
        "NOT taken. 1,311 name usages, 95.8% of a 600-name sample already "
        "held. ChecklistBank records NO licence for this dataset, which is not "
        "the same as a permissive one and is not usable on evidence."),
    "checklistbank-1025": (
        "Rhytismatales (dataset 1025)",
        "DOI 10.48580/d38d; issued 2017-10-27",
        "https://www.checklistbank.org/dataset/1025",
        None, "assessed",
        "NOT taken. 769 name usages, 96.7% of a 600-name sample already held. "
        "No licence stated, as 1023."),
    "checklistbank-1026": (
        "ScaleNet, Systematic Database of the Scale Insects of the World "
        "(dataset 1026)",
        "DOI 10.48580/d38f; version Dec 2004, issued 2004-12-05",
        "https://www.checklistbank.org/dataset/1026",
        "CC BY", "assessed",
        "NOT taken. 7,074 name usages, 83.7% of a 600-name sample held -- the "
        "largest miss in its batch at 16.3%, and still declined. Same grounds "
        "as LepIndex (1018): a twenty-year-old circumscription, so much of what "
        "it would add is obsolete names rather than missing taxa, and importing "
        "those is a taxonomy decision rather than a data one. Worth revisiting "
        "only alongside LepIndex if we decide to take synonym coverage instead "
        "of accepted taxa alone."),
    "checklistbank-1030": (
        "TicksBase (dataset 1030)",
        "DOI 10.48580/d38k; issued 2005-06-15",
        "https://www.checklistbank.org/dataset/1030",
        "CC BY", "assessed",
        "NOT taken. 796 name usages in total, 600 of 600 sampled species "
        "already held. The whole dataset is smaller than the sample several of "
        "its neighbours got, so 100% here is exhaustive rather than "
        "indicative. Nothing there for us."),
    "wikispecies": (
        "Wikispecies (ChecklistBank dataset 314570)",
        "DOI 10.48580/dgx39; version 2026-08-02; "
        "generated by CatalogueOfLife/coldp-generator",
        "https://www.checklistbank.org/dataset/314570",
        "CC BY", "applied",
        "TAKEN and applied, twice. 458,568 accepted species offered. The first "
        "run added 51,706 to animalia and refused 192,372; the second, after "
        "the importer was fixed to route per taxon rather than per source, "
        "added 80,382 across six kingdoms and refused 84,035. Both refusals "
        "went into the pending-family store rather than dying with the "
        "counter. Worth recording that the first run's refusals were almost "
        "entirely plants and fungi looked for in Animalia: Wikispecies carries "
        "no kingdom in any of its rank chains, so 'read the kingdom off the "
        "source' degenerated to a fallback. The largest single refusal, "
        "Pentatomidae at 1,137 species, was a family the store had already "
        "flagged as missing from an independent GBIF count."),
    "wikidata-species": (
        "Wikidata Species (ChecklistBank dataset 314569)",
        "DOI 10.48580/dgx38; version 2026-08-02; contact Markus Doering (GBIF); "
        "generated by CatalogueOfLife/coldp-generator",
        "https://www.checklistbank.org/dataset/314569",
        "CC0", "assessed",
        "NOT IMPORTED, and not yet a decision either. Measured with "
        "scripts/overlapReport.py, which uses the importers' own held/new test "
        "rather than a raw string comparison: 3,207,163 accepted species, of "
        "which 1,395,018 (43.5%) we already hold and 1,811,989 (56.5%) are new. "
        "Of the new ones 91% resolve both a family and an order and would land "
        "in a real family rather than an Incertae sedis placeholder. Zero "
        "duplicates within the archive, 156 non-binomials. Taken, this would "
        "roughly double animalia and bring prokaryotes and viruses with it. "
        "CC0, so licensing is not an obstacle. "
        "It does NOT resolve the bacteria-and-viruses rank question: Wikidata "
        "carries the same 17 kingdom-rank clades COL does (Bacillati, "
        "Pseudomonadati, Orthornavirae, Heunggongvirae, ...) because it is "
        "built from the same upstream, and 1,612,751 of the new species have no "
        "parent at all. See docs/bacteria-and-viruses.md for the options. "
        "First archive in the ColDP format we hold, and first to exercise "
        "scripts/coldp.py. "
        "RE-CHECKED 2026-10-10: species-import question still correctly "
        "undecided -- it is downstream of the bacteria-and-viruses hold, which "
        "is unchanged (GTDB has since settled the bacterial rank; viruses are "
        "still blocked on ICTV). The 2026-10-04 measurement was already taken "
        "after Animalia Stage 2, so the ~135k species added since (ITIS, BOLD, "
        "GLI, Craneflies, Reptiles) shave a little off 1,811,989 but do not "
        "change the shape of the decision -- not worth re-measuring on its own. "
        "SEPARATE FINDING, not previously assessed: the same archive's sidecar "
        "tables carry real content the species-count note above never "
        "mentions -- VernacularName.tsv (816,277 rows, 236,487 taxa), "
        "Media.tsv (664,930 rows, 340,979 taxa with Commons image URL + "
        "licence), Distribution.tsv (293,850 rows, 103,221 taxa, "
        "establishmentMeans native/invasive, free-text place names rather than "
        "ISO codes). Of the 340,979 media taxa, 211,855 are not in "
        "shared/data/wiki-images.json's image set at all. This is an "
        "enrichment question, not an import one -- it only needs species we "
        "already hold, so it does not wait on the bacteria-and-viruses hold. "
        "Not yet measured: how many of the 211,855/161,390 (media/vernacular) "
        "gaps are species actually in the tree rather than among the 1.81M "
        "not-yet-held candidates -- that join is the next step if this is "
        "worth pursuing."),
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
        "CC BY 4.0", "applied",
        "APPLIED 2026-10-09 by scripts/importWsc.py, which reads the "
        "Distribution.tsv in the DwCA and writes `continents` onto species "
        "that carry no one. 66,766 distribution rows naming 7,184 places "
        "(China, Brazil, USA, Australia (Queensland), Hispaniola ...); 65,452 "
        "of the names resolve to a continent, and 48,738 of those resolve "
        "completely, which is the only safe subset -- a record reading "
        "'Canada, USA, and an island the table has never heard of' must not "
        "become North America, so the other 16,714 are left alone. 40,794 "
        "tree species gained a continent across 135 families (Asia 13,339, "
        "South America 8,601, Africa 7,597, Australia 5,954, North America "
        "3,871, Europe 2,134); 485 already had one and kept it. This is "
        "2.3% of the MISSING_CONTINENTS backlog, and it is where a spider "
        "catalogue beats a general one: GBIF has almost no country data for "
        "Araneae, so there is nothing here to conflict with. The 487 "
        "synonyms are held by policy and not imported. The place-name "
        "decomposition lives in scripts/osfLocalities.py, which has no "
        "country table (no `USA`, never needed one -- the Orthoptera file "
        "records TDWG level-1/3/4 names instead), so the remaining 16,714 "
        "names need one before the rest of this source is usable"),
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
        "mixed; images are CC BY-NC 3.0", "assessed",
        "NOT APPLIED, and nothing here is pending. English names measured: 28 "
        "marginal after GBIF vernacular, which is not a trade. Images are CC "
        "BY-NC 3.0 and refused. The separate ChecklistBank edition of FishBase "
        "(dataset 1010, CC BY) measured 100% already held over 600 of 600 "
        "sampled species. Nothing to do unless a policy question changes"),
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
# Sources registered deliberately without an archive on disk. Two reasons:
# either the data is regenerable by a script rather than downloaded
# (inaturalist), or the verdict was "not taken" and nothing was ever fetched --
# the six 2026-10-05 assessments, where the whole point is that a verdict can
# be reached from a sample without downloading the dataset. Treating those as
# missing archives would train us to ignore this warning.
NO_ARCHIVE = {
    "inaturalist", "zoobank", "catalogue-of-life",
    "checklistbank-1021", "checklistbank-1022", "checklistbank-1023",
    "checklistbank-1025", "checklistbank-1026", "checklistbank-1030",
    "checklistbank-1028", "checklistbank-2007", "checklistbank-2144",
    "checklistbank-310868",
    # 2026-10-09 batch, no archive on disk: 1024's endpoint 404s, and 311094 /
    # 55434 are verdicts whose archives are fetched (so NOT listed here)
    "checklistbank-1024",
    # blocked on WoRMS's own request form, not on anything we can do
    "worms",
}


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
