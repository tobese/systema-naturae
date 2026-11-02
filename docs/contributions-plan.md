# Contributions: crediting sources in the portal — plan

Drafted 2026-11-02. **Steps 1–4 built the same day** (decisions: institution
logos shown by default, institutions first, nomenclature sources credited in
their own section, GBIF Backbone as one row). What exists:

- `scripts/buildContributors.py` / `make contributors` → `data/contributors.json`
  (registry), `portal/public/data/contributors-report.json` and
  `contributors-index.json`, logos in `portal/public/data/logos/`, and
  `data/licence-crosscheck.json`. Hand corrections live in
  `data/contributors-overrides.json` (aggregator publishers, institution
  grouping, sections).
- `data/source-aliases.json` is now the one alias table; `aggregateSources.ts`
  reads it too.
- The Sources modal opens on a **Contributors** tab (institution cards; each
  expands to its datasets with licence, DOI and citation). The old tables are
  under *Per-node tallies*. Species panels list their **Sources**, linking to the
  record in each ChecklistBank dataset.
- Logo fallback: when neither ChecklistBank nor GBIF has a logo, the
  institution site's own icon (apple-touch-icon/favicon) is used, and
  `logoFrom` records that.

Still open: step 5 (licence re-check, the user's calls; see
`licence-issues.md` rows 1–10), ~140 institutions without a logo, and the
species that carry only the generic `checklistbank` id.

Goal: the portal credits every institution and dataset the tree draws on.
Each one gets at least a **name, a logo and a link**. Sources that ask for
more (a citation, a DOI, required wording, a share-alike notice) get that too.
Alongside it, the sources refused or held on licence are re-checked by hand,
because hand checks have already overturned recorded licences (see
[`licence-issues.md`](licence-issues.md), *Resolved 2026-10-29*).

## Where things stand

- **`SourcesModal.tsx` + `portal/scripts/aggregateSources.ts`** already
  exist. They tally `sourcedFrom` and `sourceIds` per kingdom and join
  licences from the manifest. But:
  - `public/data/sources-report.json` dates from **2026-10-17**, two weeks
    and most of the queue-driven imports ago.
  - It has **38 rows**, keyed by `sourcedFrom`. The `checklistbank`
    container maps to only two datasets. The queue records **956 applied
    sources**, and none of them is credited individually.
  - Nodes now carry per-dataset `sourceIds` keys (`checklistbank-316441`,
    `checklistbank-2036`, GBIF dataset UUIDs, …), so the per-dataset credit
    is recoverable from the tree. The report just doesn't read it yet.
- **The manifest** (`/Volumes/MacieExternal/sources/manifest.json`, 185
  entries) has title, identifier, url and licence fields. It has no
  institution, logo or citation, and it lives off-repo.
- **ChecklistBank's dataset API** returns `doi`, `versionDoi`, `citation`
  (CSL, HTML), `creator`, `contact`, `url`, `license` and sometimes `logo`
  for each dataset. For example, 32593 has the Svampeatlas logo.
- **GBIF's dataset API** gives a `publishingOrganizationKey`. The
  organisation endpoint gives title, homepage and `logoUrl`.

## Design

### 1. Registry: `data/contributors.json` (tracked)

Two levels, because one institution often supplies several datasets
(Natural History Museum Denmark: 2047, 32593; COL alone: several releases):

```jsonc
{
  "institutions": {
    "<id>": { "name": "", "url": "", "logo": "logos/<id>.png",
              "logoSource": "<url it was fetched from>", "ror": null }
  },
  "datasets": {
    "checklistbank-2047": {
      "title": "", "institutions": ["<id>"], "doi": "", "citation": "",
      "licence": "CC BY-NC 4.0", "licenceUrl": "",
      "attribution": null,          // required wording, if the source specifies one
      "shareAlike": false,
      "evidence": [{ "field": "licence", "url": "", "checked": "2026-11-02" }]
    }
  }
}
```

Every field comes from an API response or is entered by hand with the URL it
came from, in keeping with the no-LLM-content rule: no generated blurbs and no
guessed institutions. A dataset with no known institution stays
institution-less and is listed under its own title.

### 2. Harvest: `scripts/buildContributors.py`

- Input: every queue row in stage `applied`, plus every manifest entry
  with status `applied`/`genus-authority`/`nomenclatural track`.
- ChecklistBank keys: fetch `/dataset/<key>` and cache it on the external
  volume, the same way other fetches are cached.
- GBIF UUIDs: fetch dataset, then publishing organisation.
- Logos: download once into `portal/public/data/logos/`. Never hotlink.
  Record `logoSource`. If there is no logo, the UI shows a text monogram
  rather than a substitute image.
- Hand-maintained `data/contributors-overrides.json` takes precedence. It
  holds the required-wording cases (LPSN "cite the latest reference",
  GTDB, iNaturalist, MycoBank, WoRMS, ITIS…), institution merges (the
  same museum under two spellings), and logos supplied by hand.
- Re-runnable; `make contributors`.

### 3. Counts: extend `aggregateSources.ts`

Tally per-dataset `sourceIds` keys, read from the species parquet rather than
by walking 4M nodes. Count species per dataset per kingdom, and roll the counts
up to institutions. Nodes that carry only the bare `checklistbank` container id
are shown as their own honest "ChecklistBank, dataset not recorded" row. Tracing
those back to a dataset is a separate task.

### 4. UI

- **A Contributors view** in or replacing `SourcesModal`. It shows a grid of
  institution cards: logo, name, link, number of datasets and species. Each
  card expands to its datasets, with citation, DOI, licence badge, any
  required wording and a share-alike notice. This closes the "BY-SA not shown
  anywhere" and "no dataset-level attribution notice" gaps in
  `licence-issues.md`.
- **Per species:** `UnifiedInfoPanel` lists the node's `sourceIds` as links to
  their dataset entries, which answers "where did this name come from?".
- Sorted by contribution size, with a search box. Six kingdoms, with a kingdom
  scope switch as now.

### 5. Licence re-check (runs in parallel; the user's calls)

One row per source in `licence-issues.md`, each with the ChecklistBank
licence, the publisher's own terms page, a contact, and the outcome with a
dated evidence URL (or a stored permission letter).

| Source | Recorded | Note |
|---|---|---|
| Danish Mycological Society fungi (2047), Checklist of Danish Fungi (32593) | blocked, NC | Same publisher (Natural History Museum of Denmark). Queue `licence` says `cc by`, ChecklistBank says `cc by nc` |
| Checklist of Vermont Fungi (304886) | blocked, NC | Same queue/ChecklistBank mismatch |
| Checklist of Vermont Species (24580) | **applied**, CB says NC | open item #1; 47 sole-source species |
| AlgaeBase (304756) | deferred, NC | also a homonym authority |
| GlobalTreeSearch (310690, BGCI) | assessed, NC | |
| MycoBank | applied, three conflicting statements | open item #2 |
| Fauna Europaea (2026) and the rest of open item #8 | "other"/unverified | |
| FloraBase, Flora of China, NZPCN, SANBI | permission-based | open item #7; a written permission would become a `licence: "permission"` row with the letter as evidence |

The settled media refusals (AntWeb, BioImages, CalPhotos, Flickr-EOL,
MSW3) are not reopened unless the user says so.

Also a mechanical pass: compare every queue row's `licence` with
ChecklistBank's current `license`. The three mismatches above suggest more,
and the pipeline's NC gate reads the queue field.

## Order

1. Registry + harvest (1–2): data only, nothing visible.
2. Counts (3), regenerating `sources-report.json`.
3. Contributors view (4a), then per-species sources (4b).
4. Licence re-check (5) can start now, independent of 1–3.

## Open questions (answered 2026-11-02, see top)

- **Logos:** is showing institutions' own logos, as identification with a link
  back, fine as a default? Or ask first, or show only logos the institutions
  publish via ChecklistBank/GBIF?
- **Grouping:** lead with institutions (as sketched) or datasets?
- **Credits for sources that are not species sources:** should
  genus-authority/nomenclature-only sources (IPNI, LPSN, ICZN lists) and
  cross-check-only ones be credited? (Suggest yes, in a separate section.)
- **GBIF Backbone:** 200k nodes tagged `gbif` don't record their constituent
  dataset (open item #6). Credit the Backbone as one row for now?
