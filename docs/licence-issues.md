# Licence issues

One place for every open licensing question about data in, or offered to,
the tree. Started 2026-10-29 from the pre-pipeline re-take inventory. Older
notes live in [`data-sources.md`](data-sources.md) (attribution gaps) and
[`dataset-inbox.md`](dataset-inbox.md) (per-batch verdicts); this file
collects the open questions and points back to them.

## Policy as practised

- **Open licences by default:** CC0, CC BY, public domain. CC BY-SA is
  accepted; the Contributors view marks it share-alike.
- **Non-commercial (NC) rule, decided 2026-11-02, relaxed the same day.**
  The project is strictly non-commercial, so NC sources may be used. Since
  their licence follows their records to anyone reusing the data:
  1. **Prefer the open version where both exist.** If an open source holds the
     same thing (or the same source is published openly in a newer version),
     the open one is used.
  2. **Record it per source:** the licence as the archive states it (its own
     `eml.xml` / `metadata.yaml` / `Metadata.json`; `make contributors` reads
     it), in the manifest entry and here.
  3. **Show it:** the portal's Contributors view lists sources by licence, NC
     marked, and `DATA_LICENSE.md` explains that NC parts may not be reused
     commercially.
  4. **Keep share-alike and no-derivatives in mind.** CC BY-SA and CC BY-NC-SA
     parts must stay separable (a merged work cannot satisfy both), and a
     no-derivatives term (MycoBank's "unadapted form only") allows ids and
     checks against the source, not republishing its content reworked.

  NC sources are still never taken automatically (the gates below stay): each
  is measured, then taken by hand and listed here.

  Sources taken under this rule:
  - **iNaturalist** (CC BY-NC 4.0): common names, filling empty `commonName`
    slots. See [`data-sources.md` § iNaturalist](data-sources.md).
  - **Checklist of Vermont Species** ([24580](https://www.checklistbank.org/dataset/24580/about),
    CC BY-NC 4.0 as taken): 1,335 species, 47 no open source holds.
  - **MycoBank** (CC BY-NC per its site terms, no-derivatives): MB numbers and
    authorship checks on 173,644 fungal species.
  - **Cockroach Species File** ([1051](https://www.checklistbank.org/dataset/1051/about)
    and the GBIF copy, CC BY-NC 4.0 as taken).
  - **BioAcoustica** ([62703](https://www.checklistbank.org/dataset/62703/about),
    CC BY-NC-SA 3.0 as taken): 342 species, 58 alone.

  The project's own contribution is CC BY 4.0 (`DATA_LICENSE.md`).
- **Enforcement:**
  - `triageNext.py` drops NC from discovery.
  - The pipeline (import-ordinator and importQueueDriver) blocks any queue
    row whose licence reads `nc` as a word.
  - The dashboard's GBIF tab disables **Add** for NC sets.
  - These stay as they are under the NC rule: an NC source is never taken
    automatically. It is measured first (what would rest on it alone), and
    taken by hand only if point 1 holds, then listed above.
- **Unknown licences** ("not stated", "other", "notspecified") are not
  applied until checked against the publisher or ChecklistBank.

## Open — needs a decision

| # | Source | Licence | State | What's at stake | Options |
|---|---|---|---|---|---|
| 1 | **Checklist of Vermont Species** (ChecklistBank [24580](https://www.checklistbank.org/dataset/24580/about)) | CC BY-NC 4.0, as the archive taken 2026-10-25 states (version 2026-08-31); the manifest's "CC BY" was a recording error, corrected. | **Decided 2026-11-02:** kept under the NC rule (above). | 47 species rest on it alone; 1,288 more carry its id beside other sources. | Done -- listed under the NC rule. |
| 2 | **MycoBank** (`mycobank`) | CC BY-NC (MycoBank's site terms, 'unadapted form only'); three distributions state three things. | **Decided 2026-11-02 (user): kept under the NC rule.** | 173,644 fungal species carry its MB number, 875 rest on it alone; used for ids and authorship checks, no renames. | Done -- listed under the NC rule. Still worth recording the terms of the login it was downloaded with. |
| 3 | **AlgaeBase** (ChecklistBank [304756](https://www.checklistbank.org/dataset/304756/about)) | CC BY-NC | Assessed, deferred since 2026-10-10. | Unmeasured. It is also the authority for some algal homonym calls (e.g. *Ulva plantaginifolia*, low/medium confidence in `data/cross-kingdom-homonym-decisions.json`). | Under the relaxed NC rule: may be taken -- measure first (what it adds that no open source holds). |
| 4 | **GlobalTreeSearch** (ChecklistBank [310690](https://www.checklistbank.org/dataset/310690/about)) | CC BY-NC | Assessed | Unmeasured | Under the relaxed NC rule: may be taken -- measure first. |
| 5 | **NC GBIF checklist sets** | CC BY-NC | 192 of the top 1,000 in the dashboard's GBIF tab, Add disabled. | Each needs a decision row. | Under the relaxed NC rule: may be taken one by one after measuring; the dashboard's Add stays disabled, so each is a by-hand call. |
| 6 | **GBIF Backbone constituents** | CC0 / CC BY / **CC BY-NC**, per constituent dataset | Applied | 200,677 nodes tagged `gbif` have no dataset DOI, so no single record's licence can be stated ([`data-sources.md`](data-sources.md) gap 3). | Trace each node to its constituent dataset, or replace it from the constituent where that dataset is open. |
| 7 | **Permission-based `websearch` sources**: FloraBase, Flora of China, NZPCN, SANBI | Permission, not a licence | Applied (~8 species) | See the attribution doc. | Get written permission, or replace them. |
| 8 | **Unverified licences, not applied:** Fauna Europaea ([2026](https://www.checklistbank.org/dataset/2026/about), "other (unverified)"), Parhost fleas ([1022](https://www.checklistbank.org/dataset/1022/about), "other"), FLOW, Moss Tropicos, USDA PLANTS, Phasmida SF v2, EOL TraitBank, ZooBank ("per-publication rights vary"), Species Fungorum crawl ([1028](https://www.checklistbank.org/dataset/1028/about)), Phyllachorales ([1023](https://www.checklistbank.org/dataset/1023/about)), Rhytismatales ([1025](https://www.checklistbank.org/dataset/1025/about)) | not stated / other | Assessed | Blocks taking them. | Check ChecklistBank and the publisher one by one, as done for the six resolved below. |
| 9 | **Cockroach Species File** (ChecklistBank [1051](https://www.checklistbank.org/dataset/1051/about)) | **CC BY-NC 4.0, settled:** the GBIF copy we hold (`species-file-cockroach`) states it in its own eml.xml (2019); ChecklistBank 1051 states it today. The manifest's 'CC BY 4.0' was a recording error, like Vermont's. | Applied: 2026-10-22 (1051) and the earlier GBIF-copy import. | 51 species carry the 1051 id, 7 rest on it alone; 2,755 species have their record from the GBIF-copy import. | **Done 2026-11-02:** kept under the relaxed NC rule. |
| 10 | **Danish fungi** ([2047](https://www.checklistbank.org/dataset/2047/about), [32593](https://www.checklistbank.org/dataset/32593/about)) and **Vermont Fungi** ([304886](https://www.checklistbank.org/dataset/304886/about)) | ChecklistBank: CC BY-NC. Queue rows: `cc by`. | Blocked anyway (the block reason already says NC). | The queue's `licence` field is what the pipeline's NC gate reads, so a wrong `cc by` there is a gate that would have let them through. | Queue rows corrected to `cc by nc` 2026-11-02 (`licenceChecked` records the source and the old value); blocked, so nothing in the tree. If ever wanted: ask the publishers (Natural History Museum of Denmark; J. Loomis for Vermont) whether NC is still current. |
| 11 | **BioAcoustica: Wildlife Sounds Database** (ChecklistBank [62703](https://www.checklistbank.org/dataset/62703/about)) | **CC BY-NC-SA 3.0** in the archive's own `dwca/eml.xml`; ChecklistBank says CC BY today; recorded as CC BY. Found 2026-11-02 by the archive cross-check. | Applied. | 342 species carry its id, 58 rest on it alone. | **Done 2026-11-02:** kept under the relaxed NC rule (share-alike: keep separable). |
| 12 | **Catalogue of Life China 2025** (ChecklistBank [312616](https://www.checklistbank.org/dataset/312616/about)) | **CC BY-NC 4.0** in the eml.xml of the version we took (2025-05-22); **CC BY** at ChecklistBank today. Found 2026-11-02. | Applied, species reverted 2026-10-31, ids kept. | 56,334 species carry its id, 625 rest on it alone. | Rule point 1: the open (CC BY) current version exists, so re-take it; the ids then rest on an open licence. |

### Licence cross-check

`make contributors` writes `data/licence-crosscheck.json`, comparing three
statements per source: what we **recorded** (queue row / manifest), what the
**archive we took** states in its own `eml.xml` / `metadata.yaml` /
`Metadata.json` (`asTaken`, read for 970 of 1,354 archives), and what
**ChecklistBank** says today. Flags: "recorded differs from the archive",
"relicensed since taken", "NC not recorded", "no licence anywhere". 2026-11-02:
56 sources flagged; the NC ones are rows 9, 11 and 12 above. Earlier, the
two-way version found As of 2026-11-02, 33 differences. Five are ones where
ChecklistBank says non-commercial and our record does not (rows 1, 9 and 10
above). Most of the rest are records more restrictive than ChecklistBank
(`cc by` recorded, ChecklistBank `cc0`) or "not stated" where ChecklistBank
now states CC BY, so they're harmless but worth correcting. ChecklistBank's
value is its *current* licence; a dataset can have been relicensed since we
took it, so a difference is a question, not a verdict.

### Also open, on attribution rather than licence

From [`data-sources.md`](data-sources.md):
- BY-SA share-alike is not shown anywhere a user can see it (~68k entries).
- There is no dataset-level attribution notice.
- 620,509 nodes carry no `sourcedFrom`.

## Resolved 2026-11-02, from the archives

- **NCBI Taxonomy** (2169): CC0 as taken (`metadata.yaml`, 2026-04-17);
  ChecklistBank says CC BY now. We hold the more open version.
- **Archis botany / zoology** (53677, 53684): CC0 as taken (recorded CC BY).
- **Vermont** (row 1) and **MycoBank** (row 2): under the NC rule.
- **Cockroach Species File** (row 9): licence settled as CC BY-NC.

## Resolved 2026-10-29

These six were applied with the manifest licence "not stated". ChecklistBank
states an open licence for each. Only the manifest's `licence` field is out of
date.

| Source | ChecklistBank licence |
|---|---|
| Systema Dipterorum ([1101](https://www.checklistbank.org/dataset/1101/about)) | CC BY |
| Universal Chalcidoidea Database ([124661](https://www.checklistbank.org/dataset/124661/about)) | CC BY |
| World Catalogue of Opiliones ([2256](https://www.checklistbank.org/dataset/2256/about)) | CC BY |
| The World Spider Catalog ([56185](https://www.checklistbank.org/dataset/56185/about)) | CC BY |
| iNaturalist Taxonomy ([139831](https://www.checklistbank.org/dataset/139831/about)) | CC BY (the taxonomy; the NC exception above covers iNaturalist's observation-side *names* data) |
| ITIS ([2144](https://www.checklistbank.org/dataset/2144/about)) | CC0 |

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
