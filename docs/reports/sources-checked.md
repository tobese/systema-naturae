# Sources checked and rejected, 2026-10-01

Every free source found for the four open gaps, with what each one actually
yields. Written because the next session will otherwise re-open files already
measured, and because the pattern in the "why not" column is more useful than
any individual number.

## The four gaps

From `scripts/sanity_scan.py`, 2026-10-02 (after the enrichment passes in
`af5669043`):

| | count |
|---|---|
| `MISSING_COMMON_NAME` | 1,089,091 |
| `MISSING_CONTINENTS` | 1,047,687 |
| `MISSING_LINEAGE` | 1 |

The two large figures fell because both GBIF enrichers were matching on our raw
stored name while indexing GBIF canonical names, so the 156,392 species that keep
an authorship inside `name` all missed silently. See `af5669043`.

## Applied

| source | yield | notes |
|---|---|---|
| GBIF `Distribution.tsv` → `countryCode` | **78,910** continents | fungi 20%, protozoa 31% |
| GBIF `VernacularName.tsv` | **23,171** common names | English only; 801,425 non-English rows dropped |
| GBIF name parser + MycoBank | **646,613** authorships | MycoBank first for fungi |
| id repair, 4 genus merges | 566 ids, 4 nodes | see `docs/reports/hybrid-names.md` |

## Rejected, with the measurement

**GBIF `Description.tsv`** — 1,755,793 rows, the 1.2 GB prose table. 1.33% of our
undescribed species have any prose; **0.79%** after the genus-opening gate.
Content is Plazi literature treatments: `materials_examined` rows, spore
measurements in µm, parasite prevalence tables. `Syphacia peromysci` →
*"Prevalence and mean intensity (range): 20% (1/5) and 465…"*. 4,551 of 5,870
candidates were morphometric text or HTML fragments. **Prose comes from
Plazi, and there is none for fungi or algae.**

**GBIF `Distribution.locality`** — 3,449,018 rows have a locality but no
country code. An explicit 268-entry gazetteer fills **64,996** (5.82%). Rejected:
**39% of names present in both passes disagree**, and 92% of those are cases
where locality *adds* continents the reliable `countryCode` column lacked — often
wrongly (`Huechys sanguinea`, a Chinese cicada, gains North America). Bare
continent names were excluded after finding `Stenostira scita`, a New Zealand
moth, with a GBIF row reading `locality=Africa`. **A country code is evidence; a
locality string is a restatement someone typed.**

**GBIF `Multimedia.tsv`** — 614,709 rows, 192,159 taxa with media, but only
**7,908** with a free-to-reuse licence (88% of rows carry no licence at all;
most of the rest are CC BY-NC-ND). **1,882 of those are species in our tree.
`creator` is empty on all 7,908** — CC BY requires attribution, so these cannot
be used. Wikimedia Commons is the only source that carries images *with*
attribution, which is why 161,737 of our 305,426 `wiki-images.json` entries have
one. The ~144k without are genuinely uncoverable: no photograph exists.

**iNaturalist** — `taxa.json` is a 13-record stub, `taxa.csv.gz` is 403, so the
only route is paging `?rank=species&per_page=200` (5,651 pages, 1,130,039
species) and iNat 403s after ~50 pages. Sampled yield: **12.1% of its preferred
common names are not already in our GBIF index** (`Cooper's Hawk`,
`Carolina Mantis`, `Golden Silk Spider`). `conservation_status_name` and
`wikipedia_summary` are **empty on all 9,996 sampled** — present in the schema,
populated at no species. Worth ~8–10k common names for 4.7h against a
volunteer-run API.
**Two traps, both silent:** `autocomplete` fuzzy-matches to a *different*
species (`Lactarius spec` → `Lactarius speciosus`), and `?q=` ranks a different
species first (`Canis lupus` → *Canis familiaris*, "Domestic Dog", position 1).
Any bulk join must verify exact identity.

**Wikidata Species** — ChecklistBank `314569`, DOI `10.48580/dgx38`, 3,962,614
taxa / 3,263,980 species, CC0, version 2026-08-02. Looks ideal; is not.
Every content endpoint 404s — no descriptions, no media, no distributions, no
vernacular names. Names and structure only. Touches none of the four gaps.
Note GBIF reports `count: 0` for it; that is indexing lag, not absence.

**Encyclopedia of Life** — classic API serves `taxonConcept` with
`dataObject: 0` on every variant tried (`key` absent, empty, garbage,
UUID-shaped). The `key` parameter is ignored. A positive control
(`Pinus contorta`) returns zero too, so the endpoint returns no content objects
at all. The traits API needs an admin-issued JWT and returns structured traits,
which have no field in our schema. **Re-test if someone gets a key.**

**Catalogue of Life** — `api.checklistbank.org`, dataset `3LR`, free and
keyless. Carries `status: accepted|synonym` per name, which resolved the 352
safe fungal reclassifications. No prose. COL reports both genera in a
split pair as accepted, so the lookup must be **per species**, not per genus.

**MycoBank** — `mycobank.org/Images/MBList.zip`, 144 MB, no key, no
registration. 521,819 names; covers **97.3%** of our undescribed fungal species.
Nomenclature only. Supersedes the EOL/Zenodo DwCA route (84.3%).
**No email address exists** — contact form only, with reCAPTCHA. Licence is
**CC BY-NC**, not the CC-BY 4.0 an earlier draft asserted. See
`docs/drafts/mycobank-token-request.md`.

**AlgaeBase** — paid, €500–1000/yr, key by emailing. Nominally already inside
COL's `3LR`, which exposes no descriptive content either. Separate decision, do
not merge with the MycoBank conversation.

## The pattern

Three of the rejections are the same shape: **the column being easy to read is
not evidence it is right.**

- `countryCode` vs `locality` — both free text somewhere, only one validated.
- GBIF descriptions — present and plentiful, but the wrong *kind* of text.
- iNat's `conservation_status_name` — exists in the schema, empty at every rank.

And four times in one session a regex fired far too often and only a dry run
caught it: 153,317 "malformed" ids of which 153,172 were correct; `PHY` treated
as a rank prefix when it is the first three letters of *Phyllosticta*; an
`ACCESSION_NAME` pattern that reached 45,939 hits by matching every binomial; a
"two capitalised words" common-name filter that rejected 9,997 correct English
names. **A filter permissive enough to fire often is a filter nobody can trust,
and a number that cannot be wrong is a number nobody checks.**

## Zenodo record 344329 — GBIF observation counts

`kingdom,phylum,class,order,species,basisOfRecord,count`. 1,927,235 rows,
1,165,039 distinct species names, **477,668,814 observations**. CC-BY,
published 2017-02-28, **exported from GBIF 2014-12-07**. Supplementary
material to *"Integrating and visualizing primary data from prospective and
legacy taxonomic literature"*, BDJ 3:e5063.

Not used, for one reason: it is an 11-year-old snapshot of something queryable
live. Observation counts are the fastest-moving number in the system, this
covers 22.7% of our animalia, and GBIF serves current counts via
`/species/{key}` — free and keyless. Batchable 1,000 names per POST through
`v2/species/match`, the same bulk path `scripts/compareGbifMycobank.py` uses.

Worth keeping only because it is the one thing here we have no other source for:
**we hold no observation counts at all**, so this is the sole candidate for a
field the schema does not yet have.

Two traps in the file itself, both of which cost time:

- **Aggregate rows are interleaved with taxa rows.** `Animalia, NULL, NULL,
  NULL, NULL, PRESERVED_SPECIMEN, 202273` is a kingdom total, not a species, and
  the file is sorted so these come first. Reading the head of the file and
  concluding *Canis lupus* was absent was wrong — it has 85,255 observations.
- **`NULL` is a literal string**, not a missing value, so a naive parse treats
  it as data. And `count` is per-basis-of-record, so a species total is a sum
  across its rows.
