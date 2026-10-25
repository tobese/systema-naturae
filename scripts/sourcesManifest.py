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

# ROOT is overridable (SN_SOURCES_ROOT) so this runs on q-bert too -- see
# scripts/sources.py, which this used to duplicate rather than import,
# leaving q-bert's SN_SOURCES_ROOT silently unconsulted here.
sys.path.insert(0, os.path.dirname(__file__))
from sources import ROOT, MANIFEST

# slug -> (title, identifier, source url, licence, status, what we took)
# status: applied | ready | assessed | refused | declined | genus-authority | hold
#   genus-authority: declined as a SPECIES-import source (nomenclatural
#   register, no taxon table, no accepted/synonym split, etc.) but wired
#   into genusAuthorityRegister.py's build -- named for that one specific
#   job, not a generic "repurposed" label, because every source carrying
#   this status is used the exact same way: `--lookup <genus>` answers
#   "does this genus exist, under what kingdom/family", a question a bare
#   nomenclatural register can still answer even though it can't support
#   an import decision. The "took" text for each of these keeps BOTH
#   verdicts: why it was declined for import, and what it is actually
#   feeding now. Distinct from "assessed" (looked at, no decision reached
#   or decision was simply "no") because a genus-authority source has an
#   active consumer today, not just a note. If a future source gets
#   repurposed for something OTHER than genus lookups, give it its own
#   status naming THAT job rather than growing this one into a catch-all
#   again.
#   hold: measured for real (an actual `--apply`-shaped dry run, not a
#   one-line guess) and genuinely substantial -- but the apply decision is
#   deliberately deferred because of its scale or an unresolved data-
#   quality question, the same shape as the project-wide bacteria-and-
#   viruses hold (CLAUDE.md), just scoped to one source instead of two
#   kingdoms. Distinct from "ready" (measured, modest, just queued -- no
#   real reason not to apply whenever) and from "assessed" (looked at
#   lightly, not actually dry-run). Retires "partial": a source that is
#   both hold (species import deferred) and already serving a smaller
#   purpose (a sidecar applied, a lookup wired in) records BOTH in its
#   notes rather than needing a second status slot -- status names the
#   headline state, notes carry the rest.
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
        "downloaded. "
        "Bacteria and Viruses domains applied 2026-10-12 by "
        "scripts/importNcbiBacteriaViruses.py on q-bert (the "
        "other 2.5M accepted names are the eukaryotic kingdoms "
        "the main NCBI import of the same date already took): "
        "Bacteria 603,027 subtree taxa -> 819 family files "
        "(554 merged into the GTDB scaffold's families with "
        "19,422 species, 267 new families with 6,634 species, "
        "722 families parked under 'Incertae sedis'); Viruses "
        "275,709 subtree taxa -> 298 family files (337 ICTV "
        "families, 13,019 species, 61 under 'Incertae sedis'). "
        "Both passes filter to clean binomials (26,295 bacterial "
        "and 16,740 viral names not already held, measured "
        "2026-10-12) -- NCBI's species rank is overwhelmingly "
        "strain/clone/environmental records, which "
        "looks_binomial() rejects. The ICTV MSL pass "
        "(see ictv-msl) superseded the virus half the same "
        "day with the curated authority."),
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
        "docs/bacteria-and-viruses.md. "
        "APPLIED twice, both on q-bert 2026-10-12: the Bacteria "
        "domain was scaffolded as inert structures by "
        "scripts/importGtdbBacteria.py (184,809 species, 3,519 "
        "families, 571 parked under 'Incertae sedis'), and the "
        "Archaea domain topped up the DECLARED Archaea kingdom by "
        "scripts/importGtdbArchaea.py (10,122 in scope, ~3,130 "
        "genuinely new -- the rest the NCBI/ITIS archaea imports "
        "already held, both deriving from the same nomenclature -- "
        "into 248 family files: 112 merged into the 131 existing "
        "families, 259 new GTDB families, 20 groups parked under "
        "'Incertae sedis', 13 new orders). Archaea's tree already "
        "spoke GTDB phylum names (Aenigmatarchaeota, Halobacteriota, "
        "Thermoproteota ...), so the merge was clean; three of "
        "GTDB's unnamed-family placeholder codes (0-14-0-20-30-16 "
        "and siblings) landed as family names and are documented in "
        "verifyTree's KNOWN_CODE_LIKE_FAMILIES."),
    "lpsn": (
        "List of Prokaryotic names with Standing in Nomenclature",
        "ChecklistBank dataset 2015, nomenclatural, issued "
        "2026-10-04",
        "https://www.checklistbank.org/dataset/2015", "CC BY 4.0",
        "declined",
        "DECLINED 2026-10-12: a nomenclatural register, not a "
        "taxonomy. Type is 'nomenclatural', it has no taxon table, "
        "and paging its species through the ChecklistBank API "
        "returns zero accepted species -- the same shape that "
        "declined ZooBank and the Australian Faunal Directory: a "
        "name register with no accepted/synonym split and no "
        "hierarchy to place names in. No archive export either "
        "(both ColDP and DwCA 404)."),
    "silva-ssu": (
        "SILVA SSU Taxonomy", "ChecklistBank dataset 315045, DOI "
        "10.48580/dgxmn, v144 issued 2026-10-04",
        "https://www.checklistbank.org/dataset/315045", "CC BY 4.0",
        "declined",
        "DECLINED 2026-10-12: a genus-level rRNA taxonomy, not a "
        "species list. 1,497 families of which we hold 430 "
        "(28.7%), but paging its species through the API returns "
        "zero accepted species -- SILVA's 16S classification "
        "resolves to genus for nearly all taxa, and what "
        "species-level names it carries are the "
        "uncultured/environmental isolate names (the same class "
        "the NCBI pass's filter rejects) rather than described "
        "species. No archive export either (both formats 404)."),
    "silva-lsu": (
        "SILVA LSU Taxonomy", "ChecklistBank dataset 315044, DOI "
        "10.48580/dgxmm, v138.2 issued 2026-08-23",
        "https://www.checklistbank.org/dataset/315044", "CC BY 4.0",
        "declined",
        "DECLINED 2026-10-12: same verdict as SILVA SSU, "
        "smaller -- 805 families, 204 held (25.3%), zero accepted "
        "species via the API, no archive export. A genus-level "
        "23S/28S rRNA taxonomy."),
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
        "2026; also ChecklistBank dataset 1014 (DOI 10.48580/d37z) and, "
        "directly, ictv.global/msl/current",
        "https://ictv.global/msl/current", "CC BY 4.0", "applied",
        "APPLIED 2026-10-12 by scripts/importIctvMsl.py on q-bert: the "
        "xlsx is served directly from ictv.global/msl/current (Zenodo "
        "403s this network range, and ChecklistBank 1014 has no archive "
        "export -- both export formats 404 -- so the ICTV site is the "
        "only working download). openpyxl installed on q-bert for it. "
        "17,554 species -- 13,528 post-2021-reform binomials plus "
        "4,026 pre-reform legacy names (\"Tobacco mosaic virus\" and "
        "friends, which the MSL's own Genus column places, so they never "
        "go through GNparser's binomial parse) -- into 393 family files "
        "(298 merged with the NCBI pass's files, 130 new), 10 realms, "
        "11 kingdoms, 22 phyla, 50 classes, 105 orders, and the MSL's "
        "stable ids (ICTV202420188) stamped as ictvId. Subfamily is "
        "read (232 of them; the tree's rank vocabulary has it); "
        "subrealm/subkingdom/subphylum/subclass/suborder/subgenus are "
        "not -- no such rank exists in the model. "
        "Wrote portal/data/taxonomy-viruses.json and "
        "taxonomy/viruses/<realm>/.../src/data/*.json; NOT registered "
        "in kingdom-config.json, same policy as the bacteria scaffold."),
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
        "CC BY", "genus-authority",
        "NOT taken as a species source, and not comparable to them. 269,528 "
        "accepted genera and 2 species: it is a register of genus names, so "
        "'59.9% of its genera are held' answers a different question from the "
        "rest of the batch. Its value is nomenclatural availability, which "
        "this tree does not model as species occurrence. Sampled at species "
        "rank before the tooling was fixed, it reported a confident 100% "
        "already-held from a two-name sample. REPURPOSED 2026-10-24: now one "
        "of genusAuthorityRegister.py's genus-authority sources, used to "
        "settle cross-kingdom-homonym triage against a real external record "
        "instead of one-by-one manual lookups."),
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
        "CC0 (confirmed in the archive's own eml.xml)", "genus-authority",
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
        "offers. Verdict unchanged as an import source, nothing left to "
        "re-open on that question. REPURPOSED 2026-10-24: added to "
        "genusAuthorityRegister.py's genus-authority sources anyway -- the "
        "accepted/synonym gap that rules it out for import is irrelevant to "
        "'does this genus exist, under what kingdom/family', which is all "
        "that register ever asks."),
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
    "checklistbank-1146": (
        "Carabcat database", "DOI 10.48580/d3dk; version v.03 (08/2021)",
        "https://www.checklistbank.org/dataset/1146",
        "CC BY", "assessed",
        "NOT taken. Found 2026-10-10 searching ChecklistBank by gap family "
        "(Carabidae, our #3 animalia gap at 31,316 missing per "
        "docs/reports/animalia-gaps.md) rather than waiting for a paste. No "
        "downloadable export exists (export.zip?format=ColDP 404s, and the "
        "POST that would generate one needs credentials this project does "
        "not have), so measured via scripts/apiOverlapReport.py's page_all, "
        "called unsharded since the 40,934 total is well under the API's "
        "100k offset cap. The first pass (no subgenus stripping) read 58.5% "
        "as new -- the same GLI/BOLD mistake, since the misses were almost "
        "all `Genus (Subgenus) species` forms COL already holds without the "
        "parenthetical. Re-measured with strip_authorship + GNparser "
        "bare_name, the same way archiveOverlap.py does it: 40,886 of 40,934 "
        "(99.9%) already held, **41 new**. Declined -- not on licence (CC "
        "BY) or vintage (2021-08, fine for a stable group), but because the "
        "real opening is three orders of magnitude smaller than the search "
        "result's size column (108,488) suggested. COL Stage 2's animalia "
        "import already swept in most of what this independently-compiled "
        "database holds, from overlapping sources."),
    "checklistbank-185410": (
        "Online Taxonomic Facility of Geometridae",
        "DOI 10.48580/d9mhh; version 1.1.24.158 (2024-06-06)",
        "https://www.checklistbank.org/dataset/185410",
        "CC BY", "assessed",
        "NOT taken. Found 2026-10-10 the same way as checklistbank-1146, for "
        "our #5 animalia gap family (Geometridae, 24,459 missing per "
        "docs/reports/animalia-gaps.md). Same measurement method (no "
        "downloadable export; apiOverlapReport.py's page_all, unsharded, "
        "23,793 total well under the offset cap). Geometridae has few "
        "subgenus trinomials, so the subgenus-stripping step barely moves "
        "the number (130 raw -> 129 normalised misses) the way it did for "
        "Carabcat -- but the conclusion is the same: 23,613 of 23,742 "
        "(99.5%) already held, **129 new**. Declined for the same reason: "
        "the real opening is two orders of magnitude smaller than the "
        "search result's size column (52,742) suggested."),
    "checklistbank-1032": (
        "Cerambycidae database", "DOI 10.48580/d38t; version 2026-04-07",
        "https://www.checklistbank.org/dataset/1032",
        "CC BY", "assessed",
        "NOT taken. Found 2026-10-10 sweeping the rest of the top-30 "
        "animalia-gaps.md families through the same search, for our #8 gap "
        "family (Cerambycidae, 23,228 missing). Measured the same way "
        "(unsharded page_all + strip_authorship + GNparser bare_name): "
        "36,776 accepted species, 36,755 of 36,768 normalised forms "
        "(100.0%) already held, **13 new**. Declined -- same shape as "
        "Carabcat: a specialist database that COL Stage 2 already mostly "
        "absorbed."),
    "checklistbank-219318": (
        "World Catalogue of the Tortricidae", "DOI 10.48580/d38s; version 4.0",
        "https://www.checklistbank.org/dataset/219318",
        "CC BY", "assessed",
        "NOT taken. Found the same sweep, for our #13 gap family "
        "(Tortricidae, 12,239 missing). 10,718 accepted species, 10,678 of "
        "10,685 normalised forms (99.9%) held, **7 new**. Declined; 2018 "
        "vintage adds nothing -- the gain is negligible regardless."),
    "checklistbank-1171": (
        "On-line Systematic Catalog of Plant Bugs (Heteroptera: Miridae)",
        "DOI 10.48580/d38w; version Mar 2013",
        "https://www.checklistbank.org/dataset/1171",
        "CC BY", "assessed",
        "NOT taken. Found the same sweep, for our #14 gap family (Miridae, "
        "11,477 missing). 11,132 accepted species, 11,108 (99.8%) held, "
        "**24 new**. Declined; negligible gain."),
    "checklistbank-1046": (
        "Global Butterfly Information System (GloBIS)",
        "DOI 10.48580/d38u; version Sep 2013",
        "https://www.checklistbank.org/dataset/1046",
        "CC BY", "assessed",
        "NOT YET DECIDED -- the one real find in the 2026-10-10 sweep. "
        "Found searching for our #30 gap family (Lycaenidae, 7,107 "
        "missing); the dataset actually covers three families "
        "(Lycaenidae, Papilionidae, Pieridae), all three already 100% "
        "held. 7,982 accepted species, 7,255 (90.9%) already held, **727 "
        "new** -- an order of magnitude more than every other 2026-10-10 "
        "lead combined (Carabcat 41 + Geometridae facility 129 + "
        "Cerambycidae 13 + Tortricidae 7 + Miridae 24 = 214). The catch is "
        "vintage: issued 2013-09, thirteen years old, the same shape as "
        "LepIndex (1018, 2012-01, hedged 'take -- biggest absolute gain' "
        "in docs/dataset-inbox.md on 2026-10-04 and never actually "
        "resolved either way). Whether a 13-year-old butterfly "
        "circumscription's novelty is real species or obsolete names "
        "superseded since is not answered by this measurement -- it is a "
        "taxonomy question, the same one Tropicos and ScaleNet were "
        "declined over, not a data one. Full species list in "
        "docs/reports/checklistbank-gap-sweep-batch2.json."),
    "checklistbank-2122": (
        "EUNIS", "DOI 10.48580/d4k7; version/issued not recorded by "
        "ChecklistBank (completeness: 0)",
        "https://www.checklistbank.org/dataset/2122",
        "CC BY", "applied",
        "APPLIED 2026-10-10 by scripts/importColChecklist.py. Its export is "
        "a denormalised `taxons.tsv`/`names.tsv` pair (plural filenames, "
        "flat family/order/class/phylum/kingdom columns, no parent chain) "
        "that neither archiveOverlap.py nor colChecklist.py recognised -- "
        "measured first with a one-off join script (60,289 not held), then "
        "colChecklist.py gained an `_eunis()` reader (dispatches on the two "
        "table names existing before any other shape check) so the real "
        "importer could read it like any other ChecklistBank export, same "
        "contract as the ILDIS and ColDP branches. Multi-kingdom, not "
        "animalia-only as the first sample row suggested: 197,971 accepted "
        "species/subspecies offered, routed animalia 155,886 / plantae "
        "18,885 / chromista 1,973 / protozoa 1,066 / fungi 491. 79,511 "
        "already held in some family, **36,568 species added** across "
        "3,338 families in 5 kingdoms, 0 authority-id conflicts flagged by "
        "the new merge_family gate. 20,954 refused for lacking a family "
        "(720 recorded in the pending-family store; largest: Compositae "
        "1,927 -- almost certainly our Asteraceae under a pre-APG "
        "synonym, a name-match miss rather than a true gap -- "
        "Tenthredinidae 1,042, Eriophyidae 892). 12 families our taxonomy "
        "node claims but whose file could not be found on disk were "
        "skipped (aceraceae, hippocastanaceae, alliaceae and 9 others -- "
        "all pre-APG segregate names, a pre-existing orphaned-node issue "
        "unrelated to this import). Vintage still unrecorded by "
        "ChecklistBank; taken anyway on CC BY + the species-level evidence. "
        "verifyTree.py's cross-kingdom-homonym check caught a real data bug "
        "in EUNIS itself afterward: 4 Oxynoemacheilus (a Balkan loach genus, "
        "animalia-only) landed under fungi/Coniocybaceae because EUNIS's "
        "own source data joins those 4 rows to the wrong kingdom/order/"
        "class/phylum (order read literally '[unassigned] Pulmonata', a "
        "gastropod clade -- the tell). Removed from coniocybaceae.json, the "
        "same call as ITIS's nudibranch-filed-under-a-diatom-family case. "
        "One further new homonym was genuine and kept: Chondracanthus "
        "angustatus Heller 1865 is both a copepod (animalia, already held) "
        "and a red alga (plantae, Gigartinaceae, this import) -- allow-"
        "listed in verifyTree.py next to the other seven documented pairs."),
    "checklistbank-127379": (
        "Australian Faunal Directory (AFD)",
        "DOI 10.48580/d78hf; version 2022-10-12",
        "https://www.checklistbank.org/dataset/127379",
        "CC BY", "genus-authority",
        "NOT taken as a species source. Pasted 2026-10-10. ChecklistBank "
        "types it `nomenclatural`, and the export proves why: `name.tsv` "
        "(scientificName, rank, status, ICZN/ICN code) plus "
        "`reference.tsv` -- the archive also carries `taxa.tsv` and "
        "`synonym.tsv`, but neither gives the parent/family links an "
        "import needs. This is the Ozymandias "
        "nomenclatural layer AFD publishes through ChecklistBank, not "
        "AFD's actual classification (which lives at "
        "biodiversity.org.au/afd, not as a ChecklistBank export). Same "
        "underlying problem as ZooBank (checklistbank-2037) one step "
        "further -- ZooBank at least had a taxon table to read. Declined "
        "on data shape, not licence (CC BY) or vintage. REPURPOSED "
        "2026-10-24: added to genusAuthorityRegister.py's genus-authority "
        "sources anyway, same reasoning as IRMNG/ZooBank -- a bare genus "
        "name register still answers 'does this genus exist, under what "
        "kingdom/family' even though it can't support an import decision."),
    "checklistbank-2026": (
        "Fauna Europaea (FaEu)", "DOI 10.48580/d4fw; version 2016-09-09",
        "https://www.checklistbank.org/dataset/2026",
        "other (unverified)", "assessed",
        "NOT taken. Pasted 2026-10-10. DwCA with `ignoreHeaderLines=\"0\"` "
        "(no header row; columns positional per meta.xml) -- read after "
        "prepending a synthetic header from the field order meta.xml "
        "declares. 131,672 species, 30.5% (40,120) not held, but "
        "**97.3% of that miss (39,045 names) already appears in eunis's "
        "own miss list** (checklistbank-2122) -- the two cover the same "
        "European fauna and FaEu is the smaller, older, lower-confidence "
        "half of the overlap. Declined twice over: redundant with eunis, "
        "which is worth taking instead, and its own licence is recorded "
        "by ChecklistBank as `other` rather than a named CC term, which "
        "this project treats as unverified rather than permissive "
        "regardless (the same standard applied to Parhost/1022, Phyllachorales/1023 "
        "and Rhytismatales/1025)."),
    "checklistbank-2262": (
        "LCVP -- the Leipzig catalogue of vascular plants",
        "DOI 10.48580/d4q2; version 3.01, issued 2022-11-07",
        "https://www.checklistbank.org/dataset/2262",
        "CC BY", "applied",
        "APPLIED 2026-10-10. GBIF's raw upload uses namespaced DwC headers "
        "(`dwc:taxonID`, not `taxonID`/`ID`) which neither archiveOverlap.py "
        "nor colChecklist.py recognised as-is -- both fixed to strip the "
        "`dwc:`/`col:` prefixes, recognise `parentNameUsageID`/`taxonRank`, "
        "and let name_id be optional for a single-table DwCA with no "
        "Name.tsv to join against. Audited with "
        "scripts/auditChecklistArchive.py before deciding, rather than "
        "acted on the raw 173,187/48.1% not-held figure: 75.2% family-"
        "placement agreement on the 211,776 shared names, with "
        "disagreement concentrated in a dozen well-known pre-/post-APG "
        "segregate-family splits (Myrsinaceae vs Primulaceae, Asparagaceae "
        "vs Hyacinthaceae/Ruscaceae/Agavaceae, Malvaceae vs three of its "
        "old segregates) -- alternate circumscriptions, not errors, the "
        "same shape BOLD's take rested on. A spot check (Abarema, Aa, "
        "Goeppertia, Calathea all already held as genera, with the "
        "specific species checked genuinely absent rather than renamed) "
        "supported a real gap. importColChecklist.py's own held-check "
        "settled the number: 378,210 offered, 212,067 already held, "
        "**71,663 added** across 540 families (4,057 refused for lacking "
        "a family, mostly pre-APG segregate names like Myrsinaceae/"
        "Ruscaceae that don't exist as separate files in our tree)."),
    "checklistbank-2030": (
        "Nortaxa (Artsnavnebasen)", "DOI not recorded; version 2026-09-11",
        "https://www.checklistbank.org/dataset/2030",
        "CC BY", "applied",
        "APPLIED 2026-10-10. Norwegian species-name database, ChecklistBank "
        "native `.txt` DwCA -- colChecklist.py's table matching only knew "
        "`.tsv` names (the ColDP-split convention) and read this as zero "
        "taxa with no error until it started matching by filename stem. "
        "Also writes authorship inline on every rank's name "
        "('Curculionidae Latreille, 1802') and uses `valid` for DwC's "
        "`accepted`, both now handled. 109,058 accepted species/subspecies "
        "offered, 32,975 already held, **12,028 added** across hundreds of "
        "families in 5 kingdoms. Surfaced 8 real data bugs in Nortaxa's "
        "own records -- a correct record's citation joined to the wrong "
        "kingdom/family (a brittle star tagged kingdom=Fungi while its own "
        "remarks field quotes the WoRMS Ophiuroidea citation verbatim; "
        "same shape for a polychaete under a dry-rot fungus genus, a gall "
        "midge under a red-algae family, a bird family gaining a plant "
        "species, and three more) -- all removed after verifyTree's "
        "cross-kingdom-homonym check caught them."),
    "checklistbank-281817": (
        "Catálogo Taxonômico da Fauna do Brasil (Brazilian Fauna catalogue)",
        "DOI not recorded; version 2026-09-15",
        "https://www.checklistbank.org/dataset/281817",
        "CC BY", "applied",
        "APPLIED 2026-10-10, same colChecklist.py fixes as Nortaxa (native "
        "`.txt` DwCA, inline authorship on every rank). Animalia-only; no "
        "kingdom field in the source, all 131,040 candidates routed "
        "animalia (122,160 by family-name match, 8,880 fell back to the "
        "animalia default, which happens to be correct here). 137,924 "
        "accepted species/subspecies offered, 62,997 already held, "
        "**29,431 added** across 2,329 families -- dominated by arthropods "
        "(Curculionidae, Cicadellidae, Formicidae). 8,186 refused for "
        "lacking a family, including Geoplanidae (253) and Dipsadidae "
        "(261), both documented gaps already. Its correct new entries "
        "exposed 2 older, pre-existing bugs: a nematode (Schulzia "
        "travassosi, genus named for parasitologist Travassos, described "
        "by helminthologist Durette-Desset) and a flea beetle "
        "(Pseudostenophyma modesta) each had a same-named ghost sitting "
        "under an unrelated plant family already -- both removed."),
    "checklistbank-312616": (
        "Catalogue of Life China 2025 Annual Checklist",
        "DOI not recorded; version 2025-05-22",
        "https://www.checklistbank.org/dataset/312616",
        "CC BY", "applied",
        "TAKEN 2026-10-10 (commit f772bd6c435): 24,597 species added, plus "
        "the rank-inference fix this entry used to say was still needed --"
        " `taxon.txt` carries no rank column anywhere, inferred as species "
        "only when NO row in the whole table carries a rank and the name "
        "looks like a binomial under a known family (colChecklist.py). "
        "RE-APPLIED 2026-10-24 via importColChecklist.py --apply: a "
        "further 3,377 added, the real remaining gap after this session's "
        "kingdom-fallback and family-scaffolding fixes let more of it "
        "resolve cleanly (921 bacteria/virus taxa correctly fell to "
        "UNRESOLVED KINGDOM instead of being refused under a wrong one). "
        "This entry previously read 'NOT YET DECIDED' -- stale; the import "
        "commit never updated it."),
    "checklistbank-9818": (
        "COL Lepidoptera Project", "version/issued not recorded by "
        "ChecklistBank",
        "https://www.checklistbank.org/dataset/9818",
        "CC BY", "assessed",
        "BLOCKED, not declined. Pasted 2026-10-10. No downloadable "
        "archive (`archive.zip` 404s; `export?format=ColDP` returns a "
        "51MB classification-tree JSON, not an archive any reader here "
        "opens -- the same non-answer ZooBank's export gave). 131,135 "
        "accepted species is over the 100k-offset cap that makes "
        "unsharded apiOverlapReport.py paging safe, the same ceiling that "
        "limited the 2026-10-10 gap-sweep batch. No safe measurement path "
        "right now."),
    "checklistbank-2003": (
        "Index Nominum Algarum (INA)", "DOI not recorded; version 2019-05-10",
        "https://www.checklistbank.org/dataset/2003",
        "CC BY", "genus-authority",
        "NOT taken as a species source. Pasted 2026-10-10. ChecklistBank "
        "types it `nomenclatural`, and the export proves why, the exact AFD "
        "(checklistbank-127379) shape: `name.tsv` + `name-rel.tsv` + "
        "`reference.tsv` only, no `taxon.*` table, nothing to place "
        "against a family. Declined on data shape, not licence (CC BY) "
        "or vintage. REPURPOSED 2026-10-24: used ad hoc (not yet wired in) "
        "during the cross-kingdom-homonym triage -- confirmed Solenomeris "
        "as chromista-only (matching IRMNG), which resolved a case neither "
        "the tree nor gbif-backbone could settle alone. WIRED IN 2026-10-25: "
        "added as genusAuthorityRegister.py's `ina` reader (12,834 genus-"
        "rank rows from name.tsv), so the next algal-genus question is a "
        "`--lookup` instead of a one-off read of the archive. What it's "
        "for: ICN-governed algal nomenclature specifically -- the one gap "
        "IRMNG/Nomenclator Zoologicus/Species Fungorum Plus/AFD/ZooBank/ "
        "IPNI don't cover between them, since none of those is an algae "
        "authority. `kingdom` is left unset for every INA row (unlike "
        "AFD's hardcoded Animalia) because algae this tree holds split "
        "across plantae and chromista and INA's own export doesn't say "
        "which -- it answers \"does this genus exist\" only, same as "
        "every other genus-authority source."),
    "checklistbank-126539": (
        "Nomenclator Zoologicus (dataset 126539)",
        "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/126539",
        "CC0", "genus-authority",
        "Never run through a species-import assessment, and never added to "
        "this manifest or to the external manifest.json until 2026-10-24 -- "
        "fetched directly for genusAuthorityRegister.py's own build, which "
        "predates this entry. 340k+ zoological (ICZN) genus name instances "
        "back to 1758. Settled several cross-kingdom-homonym cases IRMNG "
        "alone had marked uncertain in the 2026-10-24 triage, and caught "
        "one (`Tubifera`) IRMNG itself flags inconsistently."),
    "checklistbank-2073": (
        "Species Fungorum Plus (dataset 2073)",
        "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/2073",
        "CC BY", "genus-authority",
        "Same gap as Nomenclator Zoologicus above: fetched directly for "
        "genusAuthorityRegister.py, never assessed as a species-import "
        "source or added to this manifest until 2026-10-24. ~490k fungal "
        "(ICN) names; this export carries no bare genus-rank taxa (every "
        "Taxon.tsv row has a species filled in), so a genus's presence is "
        "derived by grouping its species rows rather than read off one "
        "dedicated row the way IRMNG/Nomenclator Zoologicus provide it."),
    "gbif-ipni": (
        "International Plant Names Index (IPNI)",
        "version not recorded; archive fetched 2026-10-18",
        "https://www.gbif.org/dataset/046bbc50-cae2-47ff-aa43-729fbf53f7c5",
        "CC0", "genus-authority",
        "Never assessed as a species-import source -- cache built "
        "2026-10-25 purely to wire into genusAuthorityRegister.py, same "
        "shape as the other nomenclatural registers on this list. ColDP "
        "export, but split across two tables unlike the rest: Taxon.tsv "
        "carries family (col:status is blank on all 1.78M rows -- no "
        "accepted/synonym concept, the usual reason these get repurposed "
        "rather than imported) while rank/scientificName/authorship/year "
        "live in Name.tsv, joined on nameID==ID. 60,130 genus-rank (col:"
        "rank=='gen.') names, vascular plants only (ICN)."),
    "checklistbank-2041": (
        "Dyntaxa -- Svensk taxonomisk databas",
        "DOI not recorded; version 2026-10-09",
        "https://www.checklistbank.org/dataset/2041",
        "CC0", "applied",
        "APPLIED 2026-10-10. Swedish taxonomic database, all life, issued "
        "the day before it was pasted. Single-table DwCA, but its id "
        "column is BOM-prefixed 'taxonId' -- the BOM itself is stripped "
        "correctly already, but 'taxonid' wasn't yet a recognised "
        "variant of the generic `id` field, now fixed in colChecklist.py. "
        "78,716 accepted species/subspecies offered, 35,033 already "
        "held, 34,487 staged, **3,521 added**. Most of what Dyntaxa "
        "offers was already covered by eunis and Nortaxa's own Nordic/"
        "European content -- expected for a fourth source over the same "
        "ground, not a problem."),
    "checklistbank-1204": (
        "StaphBase", "DOI not recorded; version Sep 2026",
        "https://www.checklistbank.org/dataset/1204",
        "CC BY", "applied",
        "APPLIED 2026-10-10. Global rove/clown/water-scavenger beetle "
        "specialist database (Staphylinidae, Histeridae, Hydrophilidae "
        "and kin). Read cleanly through the existing ColDP-split path, no "
        "reader work needed. 89,119 offered, 77,472 already held, 9,077 "
        "staged, **5,134 added** across 16 families (7,363 staged / "
        "4,374 added in Staphylinidae alone). 0 authority-id conflicts."),
    "checklistbank-133813": (
        "Australian Plant Name Index and Census (APNI-APC)",
        "DOI not recorded; version 2022-08-31",
        "https://www.checklistbank.org/dataset/133813",
        "CC BY", "applied",
        "APPLIED 2026-10-10. ColDP CSV split, but under a fourth table-"
        "name spelling (`taxa.tsv`, plural) colChecklist.py's `_find` "
        "didn't know, and ranked entirely in Latin (Regnum, Division, "
        "Classis, Ordo, Familia) rather than the English terms every "
        "other source here uses -- both fixed (`_find` takes multiple "
        "stems now; `chain()` translates the Latin ranks it knows before "
        "matching). 24,148 accepted species/subspecies offered, 13,714 "
        "already held, **1,011 added** across 266 families -- a small "
        "Australian-endemic top-up over WFO/POWO/LCVP."),
    "checklistbank-2010": (
        "The National Checklist of Taiwan (TaiCOL)",
        "DOI not recorded; version 2024-07-31",
        "https://www.checklistbank.org/dataset/2010",
        "CC BY", "applied",
        "APPLIED 2026-10-10. Single-table DwCA, read without further "
        "reader changes. 66,504 offered, 23,827 already held, 33,308 "
        "staged, **10,815 added** across hundreds of families in all six "
        "kingdoms -- the first import this session to touch archaea. "
        "Surfaced five more wrong-kingdom-join bugs in its own data, same "
        "shape as EUNIS and Nortaxa's: a Chinese moss (Hageniella micans, "
        "cited from a 1999 Sematophyllaceae revision) tagged kingdom="
        "Animalia/Insecta on all six of its listed synonyms, and four "
        "Siphonariidae limpet species (subatra, rucuana, sipho, sirius; "
        "zoological authorships Pilsbry/Sowerby) grafted onto a chytrid "
        "fungus genus node that already held four genuinely fungal "
        "Siphonaria species with unrelated epithets. All five removed; "
        "the four legitimate fungal Siphonaria species untouched."),
    "checklistbank-304756": (
        "AlgaeBase (AlgaeGNA)", "DOI not recorded; version 2021",
        "https://www.checklistbank.org/dataset/304756",
        "CC BY-NC", "assessed",
        "DEFERRED, not declined -- licence question raised, not "
        "resolved. Pasted 2026-10-10 as 'Algea'. 172,351 name usages, "
        "unmeasured. ChecklistBank records its licence as CC BY-NC, and "
        "this project holds exactly one documented non-commercial "
        "exception already (the iNaturalist common-names ledger, see "
        "its own entry above) -- taking AlgaeBase would be a second one, "
        "which is a standing-policy call for the project owner, not "
        "something to default into. Not measured against the tree "
        "pending that decision."),
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
        "CC0", "hold",
        "RE-MEASURED 2026-10-25 with a real dry run (scripts/importColChecklist.py, "
        "not overlapReport.py's estimate): 3,358,961 offered, 582,684 already "
        "held, 2,533,679 staged into a family we hold, of which the real "
        "per-family merge_family() dedup settles at **786,806 genuinely new**, "
        "1,746,049 already present -- well down from the stale 1,811,989 "
        "figure below (expected: ~135k species/session since 2026-10-10 alone, "
        "ten times over by now), but still a large, real number. Sampled 60 "
        "of the new names directly (filtered against the canonical-name "
        "index, not just eyeballed) rather than trusting the count: Dryopteris "
        "zollingeriana Kuntze 1891, Canna denudata Roscoe 1825, Encyclia "
        "magnicallosa Pabst 1967, Gobius ceramensis, and so on -- well-formed "
        "binomials in real genera/families with legitimate historical "
        "authorship, not barcode-cluster or bot-generated junk (contrast "
        "checklistbank-37384, declined below for exactly that). Put on HOLD "
        "rather than applied or declined: the content looks genuine, but "
        "applying 786,806 species in one shot is a scale decision in its own "
        "right (see 'roughly double animalia' below), and the still-unresolved "
        "chunk (50,208 UNRESOLVED KINGDOM this run, 1,612,751 with literally "
        "no parent per the original measurement) means the yield number isn't "
        "even final. Same hold shape as the bacteria-and-viruses one "
        "(CLAUDE.md) -- a real, deliberate deferral, not a forgotten item.\n"
        "SPECIES IMPORT NOT TAKEN, and not yet a decision either -- see "
        "below, the question is downstream of the bacteria-and-viruses hold. "
        "The commonName sidecar IS applied; see VernacularName.tsv further "
        "down. Measured with "
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
        "SIDECAR FINDING, measured 2026-10-10 against the held tree "
        "(scripts/tree.py, one walk, 2,531,312 held names): the same archive's "
        "sidecar tables carry real content the species-count note above never "
        "looked at, and most of each one lands on species we already hold -- "
        "this is an enrichment question, not an import one, so none of it "
        "waits on the bacteria-and-viruses hold. "
        "Media.tsv: 340,025 distinct taxa, 192,847 held, of which 110,224 "
        "already have an image in wiki-images.json and 82,623 do not -- but "
        "663,287 of 664,930 rows (99.75%) carry no licence string at all, so "
        "that gap needs a per-image Commons licence lookup before anything is "
        "written, not a straight copy. "
        "VernacularName.tsv: APPLIED 2026-10-10 by "
        "scripts/enrichCommonNamesFromWikidata.py -- 816,277 rows in 108 "
        "languages, filtered to species-rank taxa and en/blank the way "
        "scripts/enrichCommonNamesFromGbif.py filters GBIF's table, plus one "
        "filter neither needed: 31 candidates that were just the binomial "
        "re-capitalised, not a translation, found by sampling before "
        "applying. **39,322 commonName filled** across 2,150 files (animalia "
        "21,960, plantae 15,457, fungi 1,903, chromista 2) -- bigger than the "
        "23,287 the GBIF Backbone pass filled. Idempotent, verified. "
        "Distribution.tsv: 293,850 rows, 103,213 distinct taxa, 66,815 held, "
        "35,043 already have continents, 31,772 do not; 83.9% of rows are "
        "free-text place names needing resolution (the USDA PLANTS problem "
        "again) and 16.1% are ISO codes mappable through the existing CC2CONT "
        "table today -- roughly 5,100 of the 31,772 need no new plumbing. "
        "Not yet done: writing the importer. Vernacular is the obvious first "
        "pick -- biggest clean gap, smallest new code."),
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
    "checklistbank-1130": (
        "MolluscaBase", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1130",
        "CC BY", "assessed",
        "Major mollusk checklist, 493k species, current. High priority for mollusca gaps."),
    "checklistbank-2018": (
        "Germplasm Resources Information Network (GRIN)", "DOI not recorded; version 2026-10-04",
        "https://www.checklistbank.org/dataset/2018",
        "CC0", "assessed",
        "Plant genetic resources, 167k species. USDA-backed, permissive licence."),
    "checklistbank-2039": (
        "The Plant List with literature", "DOI not recorded",
        "https://www.checklistbank.org/dataset/2039",
        "CC BY", "assessed",
        "1.3M species, plant literature-linked checklist. Large potential top-up."),
    "checklistbank-312898": (
        "Banco Taxonômico Integrado da Biodiversidade Brasileira", "DOI not recorded; version 2025-10-25",
        "https://www.checklistbank.org/dataset/312898",
        "CC BY", "assessed",
        "Brazilian integrated biodiversity bank, 348k species. Complements Brazilian Fauna."),
    "checklistbank-2317": (
        "3i World Auchenorrhyncha Database", "DOI not recorded; version Oct 2026",
        "https://www.checklistbank.org/dataset/2317",
        "CC0", "assessed",
        "Hemiptera: Auchenorrhyncha specialist, 129k species. CC0 licence."),
    "checklistbank-170394": (
        "Bryophyte Nomenclator", "DOI not recorded; version 7 Oct 2026",
        "https://www.checklistbank.org/dataset/170394",
        "CC BY", "assessed",
        "Bryophyte specialist checklist, 111k species. Fills bryophyte gaps."),
    "checklistbank-1039": (
        "Electronic Catalogue of Weevil names (WTaxa)", "DOI 10.48580/d4ft; version 2021-04",
        "https://www.checklistbank.org/dataset/1039",
        "CC BY", "ready",
        "Curculionidae nomenclator. Measured 2026-10-17 from the archive: 96,320 "
        "distinct names offered, 32,520 held, 63,800 NOT held (66.2%) -- the "
        "largest single addition found in this batch. It corrects the entry it "
        "replaces, which called this a 'large coleoptera family gap': all 14 "
        "families WTaxa offers are already in the tree, so the gap is species, "
        "not families. Read the 66.2% with the register's nature in mind -- WTaxa "
        "is a nomenclator, so part of the miss is nomina nuda rather than "
        "described species. Measured, not applied."),
    "checklistbank-307515": (
        "MELISR Taxonomy", "DOI not recorded; version 9",
        "https://www.checklistbank.org/dataset/307515",
        "CC BY", "assessed",
        "169k species, licence CC BY. Needs measurement."),
    "checklistbank-312272": (
        "ZA National list", "DOI not recorded; version 2025-09-13",
        "https://www.checklistbank.org/dataset/312272",
        "CC BY", "assessed",
        "South African national checklist, 137k species. Regional endemic coverage."),
    "checklistbank-312227": (
        "South African National Species Checklist", "DOI not recorded; version 2025-09-17",
        "https://www.checklistbank.org/dataset/312227",
        "CC BY", "assessed",
        "South African catalogue, 137k species. Complements ZA National list."),
    "checklistbank-316038": (
        "ZOOtest", "DOI not recorded; version 2026-08-11",
        "https://www.checklistbank.org/dataset/316038",
        "CC BY", "assessed",
        "Test dataset, 446k species. Prokaryotes/bacteria/eukaryotes/protists/plants."),
    "checklistbank-1157": (
        "World Foraminifera Database", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1157",
        "CC BY", "assessed",
        "Foraminifera specialist database, 90k species. Marine protist coverage."),
    "checklistbank-37384": (
        "International Barcode of Life project (iBOL) - Barcode Index Numbers (BINs)",
        "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/37384",
        "CC BY", "declined",
        "Triaged 2026-10-25 during the top-10-by-size sweep (2.03M size, 8th "
        "largest ChecklistBank dataset overall). ChecklistBank itself types "
        "it `other`, not `taxonomic` -- its own description says why: a BIN "
        "is \"a cluster of COI barcode sequences that BOLD's algorithm "
        "treats as a putative species\", placed within BOLD's own Linnaean "
        "classification. An operational taxonomic unit from DNA-barcode "
        "clustering is not a formally described species; importing BINs as "
        "species would be the exact mistake NCBI's strain/clone/"
        "environmental-sample filtering in importNcbiBacteriaViruses.py "
        "already guards against for a different source. Declined on data "
        "shape, not licence (CC BY) or size."),
    "checklistbank-316045": (
        "sintax", "DOI 10.48580/dgyt5; version 2026-09-09",
        "https://www.checklistbank.org/dataset/316045",
        "CC BY", "declined",
        "Triaged 2026-10-25 during the top-10-by-size sweep (1.66M size, "
        "10th largest). ChecklistBank types it `other`; its own "
        "`lastImportState` is `failed` -- ChecklistBank's own pipeline "
        "cannot ingest this archive. Published by ICMBio (Brazil's "
        "biodiversity/protected-species agency); description is one line, "
        "\"Arvore taxonomica do sintax\" (\"SINTAX's taxonomic tree\"), "
        "which reads like an internal regulatory classification rather than "
        "a general species checklist. Declined on the failed-import signal "
        "alone -- not worth a manual archive read when ChecklistBank's own "
        "importer already gave up on it."),
    "checklistbank-2006": (
        "International Plant Names Index (IPNI) -- ChecklistBank mirror",
        "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/2006",
        "CC0", "declined",
        "Triaged 2026-10-25 during the top-10-by-size sweep (1.79M size, "
        "9th largest). Same data as `gbif-ipni` (wired into "
        "genusAuthorityRegister.py as a genus-authority source the same "
        "day) mirrored through a different registry -- ChecklistBank "
        "reports 1,786,610 taxa here against gbif-ipni's own 1,786,537 "
        "Taxon.tsv rows, close enough to be the same export via two hosts, "
        "not a meaningfully different dataset. Declined as redundant rather "
        "than re-deriving the same genus-authority rows twice."),
    "checklistbank-310770": (
        "Biodiversity Heritage Library", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/310770",
        "CC0", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 834,852 size). A "
        "literature-digitisation library, not a taxonomy -- ChecklistBank "
        "types it `other`; its own description is explicit: \"the largest "
        "open-access digital library dedicated to global biodiversity "
        "literature\". Declined without downloading."),
    "checklistbank-53131": (
        "The IUCN Red List of Threatened Species", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/53131",
        "CC BY", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 338,085 size). "
        "Conservation-status data, not species discovery -- an enrichment "
        "question (we already pull `iucnStatus` via the wiki-images.json "
        "sidecar), same category as wikidata-species's Media/Distribution "
        "sidecars, not the species-import pipeline. Declined for import "
        "purposes; worth a separate enrichment look sometime, not done here."),
    "checklistbank-128415": (
        "BioNames Literature", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/128415",
        "CC0", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 598,683 size). "
        "ChecklistBank types it `nomenclatural`; own description: \"a "
        "database of taxa, texts, and trees... full text literature from "
        "BioStor and BHL, links to digital literature\" -- a citation/"
        "literature cross-reference tool, not a name register in the "
        "IRMNG/Nomenclator-Zoologicus shape. Downloaded archive (48.8MB) "
        "arrived corrupted (truncated central directory, twice); given the "
        "lean toward decline from the description alone, not worth a third "
        "attempt."),
    "checklistbank-164203": (
        "International Plant Names Index with Literature", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/164203",
        "CC0", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 444,323 size). Own "
        "description: \"builds upon IPNI by adding persistent identifiers "
        "for publications\" -- a literature-enriched variant of IPNI, "
        "redundant with `gbif-ipni` (already wired into "
        "genusAuthorityRegister.py) for this project's purposes."),
    "checklistbank-129659": (
        "Index Fungorum with Literature", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/129659",
        "CC0", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 100,904 size). Same "
        "literature-enrichment-variant shape as checklistbank-164203 above, "
        "for Index Fungorum -- overlaps checklistbank-1028 (Species "
        "Fungorum/Index Fungorum API crawl, already assessed)."),
    "checklistbank-316336": (
        "Dutch bio-archaeological taxa list", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/316336",
        "CC BY", "declined",
        "Triaged 2026-10-25 (next-10-by-size sweep, 100,213 size). "
        "Archaeological-finds taxonomy (Netherlands Cultural Heritage "
        "Agency), not a general species checklist; ChecklistBank's own "
        "`lastImportState` is unset -- never actually imported there "
        "either. Niche scope, declined without downloading."),
    "checklistbank-30477": (
        "UNITE - Unified system for the DNA based fungal species linked to the classification",
        "DOI not recorded; version 2026-08-10",
        "https://www.checklistbank.org/dataset/30477",
        "CC BY", "applied",
        "Triaged + applied 2026-10-25 (next-10-by-size sweep, 1,048,338 "
        "size). ChecklistBank types it `other`, same initial worry as "
        "iBOL BINs (DNA-cluster-derived \"species\"), but UNITE's fungal "
        "species hypotheses are curated against classical taxonomy "
        "(taxon.csv carries conventional kingdom/family/genus/species "
        "fields, not raw sequence clusters), unlike BOLD's BINs. Measured: "
        "101,789 offered, 1,246 genuinely new -- applied. First download "
        "attempt corrupted via aria2c's multi-connection split (16MB vs "
        "the real 120MB); single-connection curl got a clean file."),
    "checklistbank-7888": (
        "United Kingdom Species Inventory (UKSI)", "DOI not recorded; version 2023-03-13",
        "https://www.checklistbank.org/dataset/7888",
        "CC BY", "applied",
        "Triaged + applied 2026-10-25 (next-10-by-size sweep, 278,226 "
        "size). The most comprehensive curated UK wildlife taxonomy/"
        "nomenclature database (built for JNCC's Recorder package). "
        "Measured: 78,719 offered, 2,260 genuinely new -- applied (2,249 "
        "landed after a small drift from an earlier apply in the same "
        "batch). Also the source of 3 of the 5 new cross-kingdom-homonym "
        "pairs this sweep surfaced (Contarinia, Kefersteinia, Pirula, "
        "Schizochlamydella all trace through UKSI) -- see "
        "data/known-cross-kingdom-homonyms.json and the 2026-10-25 commit "
        "for the triage."),
    "checklistbank-1018": (
        "LepIndex: The Global Lepidoptera Names Index", "DOI not recorded; version not recorded",
        "https://www.checklistbank.org/dataset/1018",
        "CC BY", "applied",
        "Triaged + applied 2026-10-25 (next-10-by-size sweep, 188,409 "
        "size). Digitised card-index archive of Lepidoptera names, "
        "Natural History Museum London. Initially misread as unreadable: "
        "the ILDIS-shape flat AcceptedSpecies.tsv table "
        "(colChecklist.py's `_ildis()` reader, same shape as checklistbank-"
        "1190/1118 which genuinely lack a reader) -- but colChecklist.py "
        "already handles this exact shape, and the real blocker was a "
        "corrupted download (a stale cached response via ChecklistBank's "
        "CDN; a cache-busted re-fetch got a clean gzip'd tar, which "
        "`colChecklist._Container` already magic-byte-detects, the same "
        "handling it documents for ILDIS/1015 itself). Measured: 135,010 "
        "offered, 12,197 genuinely new -- the largest single yield of this "
        "sweep. Applied."),
    "checklistbank-9712": (
        "National Checklist of all species occurring in Denmark", "DOI not recorded; version 2026-10-14",
        "https://www.checklistbank.org/dataset/9712",
        "CC BY", "applied",
        "Triaged + applied 2026-10-25 (next-10-by-size sweep, 60,862 "
        "size). Danish national species checklist. Measured: 41,852 "
        "offered, 980 genuinely new -- applied (811 landed after drift "
        "from earlier applies in the same batch)."),
    "checklistbank-53133": (
        "Belgian Species List", "DOI not recorded; version 2011-05-30",
        "https://www.checklistbank.org/dataset/53133",
        "CC0", "applied",
        "Triaged + applied 2026-10-25 (next-10-by-size sweep, 59,448 "
        "size). Belgian Biodiversity Platform's species.be backend "
        "database. Measured: 32,945 offered, 1,481 genuinely new -- "
        "applied (1,397 landed after drift from earlier applies in the "
        "same batch)."),
    "checklistbank-2014": (
        "Checklist Dutch Species Register - Nederlands Soortenregister", "DOI not recorded; version 2026-09-24",
        "https://www.checklistbank.org/dataset/2014",
        "CC BY", "assessed",
        "Dutch national species register, 101k species. European regional coverage."),
    "checklistbank-2304": (
        "The World Checklist of Vascular Plants (WCVP): review", "DOI not recorded; version 2026, v.7",
        "https://www.checklistbank.org/dataset/2304",
        "CC BY", "assessed",
        "WCVP review edition, 90k species. Duplicate of 2000/2232 - verify if distinct."),
    "checklistbank-290762": (
        "The FinBIF checklist of Finnish species", "DOI not recorded; version 2026-07-29",
        "https://www.checklistbank.org/dataset/290762",
        "CC BY", "assessed",
        "Finnish biodiversity checklist, 79k species. Nordic regional coverage."),
    "checklistbank-308974": (
        "The Protist Ribosomal Reference database (PR2)", "DOI not recorded; version 5.1.0",
        "https://www.checklistbank.org/dataset/308974",
        "CC0", "assessed",
        "Protist rRNA reference database, 73k species. CC0 licence, microbial eukaryotes."),
    "checklistbank-312578": (
        "Catalogue of Life (main)", "DOI not recorded; version 2025-10-10",
        "https://www.checklistbank.org/dataset/312578",
        "CC BY", "assessed",
        "Main Catalogue of Life, 9.4M species. Largest unified checklist."),
    "checklistbank-9910": (
        "Catalogue of Life Checklist", "DOI not recorded; Annual Checklist",
        "https://www.checklistbank.org/dataset/9910",
        "CC BY", "assessed",
        "Catalogue of Life Annual Checklist, 4.9M species. Annual snapshot."),
    "checklistbank-201890": (
        "Open Tree of Life reference taxonomy", "DOI not recorded; version 3.7.2",
        "https://www.checklistbank.org/dataset/201890",
        "CC0", "hold",
        "Barely assessed until 2026-10-25's top-10-by-size sweep (4th largest "
        "ChecklistBank dataset overall, 4.5M size) -- the one-line note above "
        "was never backed by an actual dry run; easy to conflate with OTL's "
        "Synthetic Tree (checklistbank-201891, applied), a different dataset "
        "from the same project. Archive shape: a single flat NameUsage.tsv "
        "(col:ID/parentID/status/rank/scientificName/alternativeID/extinct), "
        "not the usual Taxon/Name split -- colChecklist.py's loader already "
        "handles this (scripts/coldp.py's CORE constant). REAL dry run "
        "2026-10-25: 3,827,048 offered, 1,376,194 already held, 330,909 "
        "genuinely new after per-family dedup. Notably weaker provenance than "
        "most sources here: only 255,016 of 2.48M resolved taxa carry an "
        "explicit kingdom in OTT's own rank chain (the rest resolve purely by "
        "family-name match), and 128,885 fall to UNRESOLVED KINGDOM outright "
        "-- consistent with OTT's own description as \"an algorithmic "
        "combination of several source taxonomies\" rather than a curated "
        "one. Put on HOLD, same reasoning as wikidata-species: real, "
        "substantial new content, but a scale decision plus an unresolved "
        "provenance-quality question, not a quick apply."),
    "checklistbank-9802": (
        "The Mammal Diversity Database", "DOI not recorded; version 2.1",
        "https://www.checklistbank.org/dataset/9802",
        "CC BY", "assessed",
        "Mammal specialist database, 95k species. CC BY licence."),
    "checklistbank-1027": (
        "World Scarabaeidae Database", "DOI not recorded; version 2026-10-05",
        "https://www.checklistbank.org/dataset/1027",
        "CC BY", "applied",
        "MEASURED AND TAKEN 2026-10-24 -- never actually run before despite "
        "being on disk since 2026-10-11. 42,388 offered across Scarabaeidae, "
        "Lucanidae, Trogidae, Passalidae, Pleocomidae and Ochodaeidae; "
        "already near-completely covered by other sources -- 20,532 of "
        "20,534 staged candidates matched an existing species by name. "
        "**2 species added.** Not a gap-filler in practice, just confirms "
        "the Coleoptera coverage already achieved elsewhere is solid."),
    "checklistbank-1140": (
        "Checklist of Ferns and Lycophytes of the World", "DOI not recorded; version 26.08",
        "https://www.checklistbank.org/dataset/1140",
        "CC BY", "assessed",
        "Pteridophyte specialist checklist, 70k species. Fern/lycophyte gap filler."),
    "checklistbank-2013": (
        "The eBird/Clements Checklist of Birds of the World", "DOI not recorded; version 2025",
        "https://www.checklistbank.org/dataset/2013",
        "CC BY", "assessed",
        "Bird taxonomy from eBird/Clements, 67k species. Avian specialist."),
    "checklistbank-2017": (
        "Afromoths, online database of Afrotropical moths", "DOI not recorded; version 2026-10-01",
        "https://www.checklistbank.org/dataset/2017",
        "CC BY", "assessed",
        "Afrotropical Lepidoptera database, 64k species. Regional moth coverage."),
    "checklistbank-1068": (
        "Taxapad Ichneumonoidea", "DOI not recorded; version May 2009",
        "https://www.checklistbank.org/dataset/1068",
        "CC BY", "assessed",
        "Ichneumonoidea (Hymenoptera) specialist database, 60k species. Parasitoid wasp coverage."),
    "checklistbank-310690": (
        "GlobalTreeSearch", "DOI not recorded; version 2025-07-01",
        "https://www.checklistbank.org/dataset/310690",
        "CC BY-NC", "assessed",
        "Global tree species checklist, 62k species. Non-commercial licence (CC BY-NC)."),
    "checklistbank-312166": (
        "South African National Plant Checklist", "DOI not recorded; version 2025-09-13",
        "https://www.checklistbank.org/dataset/312166",
        "CC BY", "assessed",
        "South African plant checklist (COLDP), 63k species. Regional endemic plants."),
    "checklistbank-1200": (
        "MilliBase", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1200",
        "CC BY", "applied",
        "Millipede specialist database (Diplopoda), 34k species. Applied on q-bert."),
    "checklistbank-170809": (
        "Handbook of the Birds of the World and BirdLife", "DOI not recorded; version 9.1",
        "https://www.checklistbank.org/dataset/170809",
        "CC BY", "assessed",
        "Bird taxonomy from HBW/BirdLife, 34k species. Avian specialist."),
    "checklistbank-54937": (
        "An Online Catalog of the Ants of the World", "DOI not recorded; version 2026-10-04",
        "https://www.checklistbank.org/dataset/54937",
        "CC BY", "applied",
        "Ant specialist database (Formicidae), 34k species. Applied on q-bert."),
    "checklistbank-2012": (
        "Database of Vascular Plants of Canada (VASCAN)", "DOI not recorded; version 2026-08-04",
        "https://www.checklistbank.org/dataset/2012",
        "CC0", "assessed",
        "Canadian vascular plants database, 33k species. CC0 licence."),
    "checklistbank-2036": (
        "IOC World Bird List", "DOI not recorded; version 15.2",
        "https://www.checklistbank.org/dataset/2036",
        "CC BY", "assessed",
        "International Ornithological Congress bird list, 33k species. Avian taxonomy standard."),
    "checklistbank-1191": (
        "World of Copepods Database", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1191",
        "CC BY", "assessed",
        "Copepod (Crustacea) specialist database, 31k species. Marine crustacean coverage."),
    "checklistbank-1175": (
        "World Ostracoda Database", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1175",
        "CC BY", "assessed",
        "Ostracod (Crustacea) specialist database, 31k species. Marine crustacean coverage."),
    "checklistbank-1166": (
        "World Entiminae Database", "DOI not recorded; version Oct 2026",
        "https://www.checklistbank.org/dataset/1166",
        "CC BY", "assessed",
        "Entiminae weevil subfamily specialist database, 30k species. Curculionidae gap filler."),
    "checklistbank-2042": (
        "Cichorieae Systematics Portal", "DOI not recorded; version 2024-01-03",
        "https://www.checklistbank.org/dataset/2042",
        "CC BY", "assessed",
        "Cichorieae (dandelion tribe) plant specialist database, 30k species. Asteraceae gap filler."),
    "checklistbank-1090": (
        "World Polychaeta Database", "DOI not recorded; version 2026-10-12",
        "https://www.checklistbank.org/dataset/1090",
        "CC BY", "assessed",
        "Polychaete worm specialist database, 30k species. Annelida gap filler."),
    "checklistbank-1118": (
        "Hymenoptera Information System", "DOI 10.48580/d3cl; version Jul 2017",
        "https://www.checklistbank.org/dataset/1118",
        "CC BY", "assessed",
        "Hymenoptera nomenclature, 30,259 names. Wasp/bee/ant gap filler. Still "
        "unmeasured as of 2026-10-17, now for a concrete reason rather than "
        "because nobody looked: the archive is the flat-table ColDP shape "
        "(AcceptedSpecies.tsv, no Taxon/Name pair) and scripts/archiveOverlap.py "
        "cannot read it. 0.5 MB on disk. Same for checklistbank-1190."),
    "catalogue-of-life-2025": (
        "Catalogue of Life, September 2026 edition", "DOI 10.48580/dgz5n (ChecklistBank 316321)",
        "https://www.catalogueoflife.org/data/download", "CC BY 4.0", "assessed",
        "COL base release September 2026; 91 checklists updated including ITIS, ScaleNet, UCD, WCO, WSC."),
    "checklistbank-1108": (
        "World List of marine Brachyura", "DOI 10.48580/d3g8", "https://www.checklistbank.org/dataset/1108",
        "CC BY", "ready",
        "WoRMS Brachyura; crabs. Measured 2026-10-17: 10,498 names offered, 325 not held (3.1%), 4 of 181 families absent. Almost entirely covered already -- taken only because it ships Distribution.txt, which is continent data we otherwise lack for 181 crab families. Measured, not applied."),
    "checklistbank-1128": (
        "World List of Trematoda", "DOI 10.48580/d3cx; version 2026-10-12", "https://www.checklistbank.org/dataset/1128",
        "CC BY", "ready",
        "WoRMS Trematoda; flukes. Measured 2026-10-17: 12,073 names offered, 3,714 not held (30.8%), 7 of 165 families absent. This is what answers the old 'Platyhelminthes 0 of 600' finding -- the trematode half of the phylum is already 69% covered, so that figure no longer describes the tree. Ships Distribution.txt. Measured, not applied."),
    "checklistbank-1190": (
        "The World of Jewel Beetles (Buprestidae)", "DOI 10.48580/d3g5", "https://www.checklistbank.org/dataset/1190",
        "CC BY", "assessed",
        "Buprestidae, 29,976 names. NOT measured as of 2026-10-17, for a concrete reason: the archive is the flat-table ColDP shape (AcceptedSpecies.tsv, no Taxon/Name pair) and scripts/archiveOverlap.py cannot read it. Same as checklistbank-1118. 0.6 MB on disk."),
    "checklistbank-2011": (
        "World Register of Marine Species (WoRMS)", "DOI 10.48580/d4fd; version 2026-10-01", "https://www.marinespecies.org",
        "CC BY", "ready",
        "The standing top item, and the largest single import available: measured 2026-10-17 from the archive, 564,441 distinct names offered, 465,423 held, 99,018 NOT held (17.5%), and 1,124 of its 9,466 families absent from the tree entirely. Two things follow. First, the 2026-10-05 finding that marine worms were 17.9% held and Platyhelminthes 0 of 600 is retired: it predates the COL breadth import, ITIS and Fauna Europaea, which have since taken most of what WoRMS offered. Second, the blocker is gone -- GBIF's DwC-A endpoint 403s and marinespecies.org asks for a request form, but https://api.checklistbank.org/dataset/2011/archive.zip answers 200 with no registration, so the 346 MB archive on disk needs no email to anyone. Worth recording that the 600-name sample put this at 88.8% held against the exact 82.5%, a 6-point gap on the project's biggest go/no-go. Measured, not applied."),
    "checklistbank-2302": (
        "Nemys: World Database of Nematodes", "DOI 10.48580/d4rf; version 2026-10-12", "https://www.checklistbank.org/dataset/2302",
        "CC BY", "ready",
        "WoRMS Nemys; nematodes. Measured 2026-10-17: 20,815 names offered, 3,748 not held (18.0%), 6 of 252 families absent. Extends families we already hold; worth taking for the 3,748 names plus Distribution.txt."),
    "checklistbank-309267": (
        "Nymphalidae", "DOI not recorded", "https://www.checklistbank.org/dataset/309267",
        "CC BY", "ready",
        "Brush-footed butterflies. Measured 2026-10-17: 6,450 names offered, 894 not held (13.9%), one family already held. Modest -- recorded because it is already downloaded and measured, not because it is needed."),
    "checklistbank-315880": (
        "Systematic Database of the Scale Insects of the World (ScaleNet)", "DOI not recorded", "https://www.checklistbank.org/dataset/315880",
        "CC BY", "ready",
        "Scale insects. Measured 2026-10-17: 8,615 names offered, 1,804 not held (20.9%), all 57 families already held. Extension only, no new families."),
    "checklistbank-1044": (
        "World Porifera Database", "DOI 10.14284/359", "https://www.marinespecies.org/porifera",
        "CC BY", "applied", "WoRMS Porifera; sponges, 96% complete."),
    "checklistbank-1081": (
        "World List of Bryozoa", "DOI not recorded", "https://www.marinespecies.org",
        "CC BY", "applied", "WoRMS Bryozoa; moss animals, 100% complete."),
    "checklistbank-1094": (
        "World Marine, Freshwater and Terrestrial Isopod Crustaceans database", "DOI 10.14284/365",
        "https://www.marinespecies.org/isopoda", "CC BY", "applied", "WoRMS Isopoda."),
    "checklistbank-1101": (
        "Systema Dipterorum", "DOI 10.48580/d3bz", "https://www.checklistbank.org/dataset/1101",
        "not stated", "applied", "Diptera nomenclator, ~160k extant + 4.5k extinct species."),
    "checklistbank-1141": (
        "Synonymic Checklists of the Vascular Plants of the World", "DOI 10.48580/d3dd",
        "https://www.checklistbank.org/dataset/1141", "CC BY", "applied", "World Plants; vascular plants."),
    "checklistbank-1174": (
        "The Paleobiology Database", "DOI not recorded", "https://www.paleobiodb.org",
        "CC BY", "assessed", "Fossil occurrences; paleontological data."),
    "checklistbank-1193": (
        "World List of turbellarian worms", "DOI 10.48580/d3g6; version 2026-10-12",
        "https://www.marinespecies.org/turbellarians",
        "CC BY", "ready",
        "Acoelomorpha, Catenulida, Rhabditophora. ALREADY APPLIED at an older "
        "version (3,425 accepted species); this is the re-version delta, measured "
        "2026-10-17 against the tree: 6,507 names offered, 1,742 held, 4,765 NOT "
        "held (73.2%), and 83 of its 152 families are still absent entirely. The "
        "best ratio in the 2026-10-17 batch and the only entry in it that both "
        "extends species and scaffolds families -- this is where the flatworm gap "
        "actually survived, because the trematode half was taken and the "
        "turbellarian half was not."),
    "checklistbank-124661": (
        "Universal Chalcidoidea Database", "DOI 10.48580/d758p", "https://www.checklistbank.org/dataset/124661",
        "not stated", "applied", "Chalcidoidea; 28,590 valid species."),
    "checklistbank-139831": (
        "iNaturalist Taxonomy", "DOI not recorded", "https://www.inaturalist.org/taxa",
        "no IP restrictions stated", "applied", "iNaturalist taxonomy."),
    "checklistbank-2000": (
        "World Checklist of Vascular Plants", "DOI not recorded", "https://powo.science.kew.org",
        "not stated", "assessed", "WCVP (Kew)."),
    "checklistbank-2008": (
        "TAXREF", "DOI not recorded", "https://www.checklistbank.org/dataset/2008",
        "CC BY 4.0", "applied", "French national taxonomic reference."),
    "checklistbank-201891": (
        "Open Tree of Life Synthetic Tree", "DOI not recorded", "https://tree.opentreeoflife.org",
        "CC0", "applied", "OTL synthetic tree, v13.4."),
    "checklistbank-2031": (
        "Flora e Funga do Brasil - Lista Oficial", "DOI not recorded", "https://www.checklistbank.org/dataset/2031",
        "CC BY 4.0", "applied", "Brazilian flora/funga."),
    "checklistbank-2130": (
        "Checklist of the Collembola of the World", "DOI not recorded", "https://www.collembola.org",
        "CC BY", "applied", "Springtails."),
    "checklistbank-2169": (
        "NCBI Taxonomy", "DOI not recorded", "https://www.ncbi.nlm.nih.gov/taxonomy",
        "CC0", "applied", "NCBI taxonomy."),
    "checklistbank-2214": (
        "Genome Taxonomy Database (GTDB) r232", "DOI 10.48580/dgz7q; version r232",
        "https://www.checklistbank.org/dataset/2214",
        "not stated", "refused",
        "GTDB microbial taxonomy. Status corrected 2026-10-17 from applied to "
        "refused: GTDB carries 189,801 bacterial species and the bacteria "
        "kingdom is on hold by decision (docs/bacteria-and-viruses.md, 2026-10-04), "
        "so an import of this dataset is out of scope. The q-bert run "
        "'Import NCBI bacteria/viruses + GTDB' did take it, and left 3,784 "
        "bacteria families on disk; they are unreachable (not in "
        "kingdom-config.json) and are documented in that doc as an artefact "
        "of the hold being honoured rather than lifted. Re-verify before any "
        "run: this entry is the machine-readable half of that decision."),
    "checklistbank-2256": (
        "World Catalogue of Opiliones", "DOI 10.48580/d4pt", "https://wcolite.com",
        "not stated", "applied", "Harvestmen (Opiliones)."),
    "checklistbank-2265": (
        "The European Nucleotide Archive (ENA) taxonomy", "DOI not recorded", "http://www.ebi.ac.uk/ena",
        "public", "assessed", "ENA taxonomy."),
    "checklistbank-56185": (
        "The World Spider Catalog", "DOI 10.24436/2", "https://www.checklistbank.org/dataset/56185",
        "not stated", "applied", "Spider taxonomy (WSC)."),
    "flow": (
        "FLOW (Fulgoromorpha Lists On the Web)", "DOI not recorded", "https://flow.hemiptera-databases.org",
        "not stated", "assessed", "Planthoppers; TSV format."),
    "itis": (
        "Integrated Taxonomic Information System", "DOI 10.48580/d4ky", "https://www.itis.gov",
        "not stated", "applied", "ITIS; all seven kingdoms."),
    "moss-tropicos": (
        "Moss Tropicos", "DOI not recorded", "https://www.tropicos.org", "not stated", "assessed",
        "Moss data (gzip)."),
    "species-file-phasmida-v2": (
        "Phasmida Species File v2", "DOI not recorded", "https://www.checklistbank.org", "not stated",
        "assessed", "Stick insects."),
    "usda-plants-extracted": (
        "USDA Plants (extracted)", "DOI not recorded", "https://plants.usda.gov", "not stated", "assessed",
        "USDA plant taxonomy."),
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
