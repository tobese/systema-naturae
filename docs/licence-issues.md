# Licence issues

One place for every open licensing question about data in, or offered to,
the tree. Started 2026-10-29 from the pre-pipeline re-take inventory. Older
notes live in [`data-sources.md`](data-sources.md) (attribution gaps) and
[`dataset-inbox.md`](dataset-inbox.md) (per-batch verdicts); this file
collects the open questions and points back to them.

## Policy as practised

- **Open licences only:** CC0, CC BY, public domain. CC BY-SA is accepted,
  but its share-alike term is not surfaced yet (see below).
- **Non-commercial (NC) needs a standing-policy decision, not a per-source
  default.** There is exactly one documented exception: **iNaturalist**
  (CC BY-NC 4.0), and only for filling empty `commonName` slots. See
  [`data-sources.md` § iNaturalist](data-sources.md).
- **Enforcement:**
  - `triageNext.py` drops NC from discovery.
  - The pipeline (import-ordinator and importQueueDriver) blocks any queue
    row whose licence reads `nc` as a word.
  - The dashboard's GBIF tab disables **Add** for NC sets.
- **Unknown licences** ("not stated", "other", "notspecified") are not
  applied until checked against the publisher or ChecklistBank.

## Open — needs a decision

| # | Source | Licence | State | What's at stake | Options |
|---|---|---|---|---|---|
| 1 | **Checklist of Vermont Species** (ChecklistBank 24580) | ChecklistBank: **CC BY-NC**. Manifest: CC BY. | **Applied** before the pipeline's licence gate existed. | 1,335 species carry its id; **47 rely on it alone** (36 fungi, 8 animalia, 2 plantae, 1 protozoa). | (a) Second NC exception. (b) Remove the 47 sole-source species and strip `checklistbank-24580` from the other 1,288. (c) Find out whether it was CC BY when taken, and record that. |
| 2 | **MycoBank** (`mycobank`) | Manifest: CC BY 4.0, but the manifest doesn't say where that comes from. ChecklistBank's copy (2002): **"other"**. EOL's Zenodo copy (13321883): `notspecified` per Zenodo's API, although BACKLOG.md calls it CC-BY. | **Imported**: `MBList.xlsx` (146 MB, archived under `sources/archives/mycobank`), downloaded through the project owner's registered MycoBank login. Used for fungal authorship and name validity: 28,253 disagreements with GBIF, no renames applied; `portal/data/mycobank-index.json`. | Three distributions, three different licence statements. Data obtained under a registration carries that account's terms of use, which the manifest doesn't record. | Look up the terms of use attached to the login (the account page, or the terms shown at registration) and record them in the manifest instead of a bare "CC BY 4.0". Never re-take it through ChecklistBank 2002, which states a different licence. |
| 3 | **AlgaeBase** (ChecklistBank 304756) | CC BY-NC | Assessed, deferred since 2026-10-10. | Unmeasured. It is also the authority for some algal homonym calls (e.g. *Ulva plantaginifolia*, low/medium confidence in `data/cross-kingdom-homonym-decisions.json`). | Second NC exception, or keep declined. |
| 4 | **GlobalTreeSearch** (ChecklistBank 310690) | CC BY-NC | Assessed | Unmeasured | Same policy question as 3. |
| 5 | **NC GBIF checklist sets** | CC BY-NC | 192 of the top 1,000 in the dashboard's GBIF tab, Add disabled. | Each needs a decision row. | Bulk **Skip** under the NC policy, or revisit once 1, 3 and 4 settle it. |
| 6 | **GBIF Backbone constituents** | CC0 / CC BY / **CC BY-NC**, per constituent dataset | Applied | 200,677 nodes tagged `gbif` have no dataset DOI, so no single record's licence can be stated ([`data-sources.md`](data-sources.md) gap 3). | Trace each node to its constituent dataset, or replace it from the constituent where that dataset is open. |
| 7 | **Permission-based `websearch` sources**: FloraBase, Flora of China, NZPCN, SANBI | Permission, not a licence | Applied (~8 species) | See the attribution doc. | Get written permission, or replace them. |
| 8 | **Unverified licences, not applied:** Fauna Europaea (2026, "other (unverified)"), Parhost fleas (1022, "other"), FLOW, Moss Tropicos, USDA PLANTS, Phasmida SF v2, EOL TraitBank, ZooBank ("per-publication rights vary"), Species Fungorum crawl (1028), Phyllachorales (1023), Rhytismatales (1025) | not stated / other | Assessed | Blocks taking them. | Check ChecklistBank and the publisher one by one, as done for the six resolved below. |

### Also open, on attribution rather than licence

From [`data-sources.md`](data-sources.md):
- BY-SA share-alike is not shown anywhere a user can see it (~68k entries).
- There is no dataset-level attribution notice.
- 620,509 nodes carry no `sourcedFrom`.

## Resolved 2026-10-29

These six were applied with the manifest licence "not stated". ChecklistBank
states an open licence for each. Only the manifest's `licence` field is out of
date.

| Source | ChecklistBank licence |
|---|---|
| Systema Dipterorum (1101) | CC BY |
| Universal Chalcidoidea Database (124661) | CC BY |
| World Catalogue of Opiliones (2256) | CC BY |
| The World Spider Catalog (56185) | CC BY |
| iNaturalist Taxonomy (139831) | CC BY (the taxonomy; the NC exception above covers iNaturalist's observation-side *names* data) |
| ITIS (2144) | CC0 |

## Refused on licence (settled)

| Source | Licence |
|---|---|
| AntWeb | CC BY-NC-SA 4.0 |
| BioImages | CC BY-NC-SA 3.0 |
| CalPhotos | CC BY-NC-SA 3.0 |
| Flickr (EOL group) | mostly NC, per image |
| Mammal Species of the World, 3rd ed. | all rights reserved |

## Not a licence question, recorded here because it surfaced in the same pass

The **ICZN Official Lists and Indexes** (`iczn-lists`, CC0) were used for
nomenclature, not as an import. `scripts/validateIczn.py` matched names
against the Commission's availability rulings: 1,159 matches, 157 of them
**unavailable** names. Their manifest status reads `applied` like an import.
A `nomenclature`/`genus-authority`-style status would stop them being mistaken
for a re-take candidate.
