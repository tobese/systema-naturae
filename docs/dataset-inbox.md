# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```

```

---

## What happens after you paste

Each link gets measured against the tree before anything is applied, because
"this source has poor coverage" and "this download was truncated" look identical
from the outside and only one of them is fixable by re-fetching.

1. **Licence first, before download.** Non-commercial (NC / ND) sources are
   refused. This is not a formality: seven of the ten EOL harvests assessed so
   far turned out non-commercial, and the EOL harvester republishes whatever a
   project publishes without filtering by licence — so the record on Zenodo is
   the thing to read, not the EOL page. Attractively large and entirely unusable.
2. **Capture provenance.** A DOI or GBIF dataset key, recorded in
   `manifest.json`. A source we cannot cite or re-fetch is a liability, not an
   asset.
3. **Measure match rate** of its names against the tree, and note whether it
   brings *new* taxa or just new descriptions. Most of a new checklist's value
   here is the latter; that distinction decides whether it is worth the schema
   work.
4. **Check the shape.** Distribution values that are ocean basins or regions
   rather than continents, and trait values that are ontology URIs rather than
   prose, both look like data and read as noise. EOL TraitBank was 11.4M rows and
   unusable for this reason.
5. **Dry run, then apply.** Nothing is written until the counts and the licence
   are confirmed.

## Triage

| Dataset | Verdict | Where it ended up |
|---|---|---|
| _(nothing triaged yet)_ | | |

Verdicts: **applied** · **partial** · **ready** (downloadable, unapplied) ·
**assessed** (measured, nothing taken) · **refused** (licence).

## Already covered

Don't re-paste anything already indexed — check first, it is one command:

```bash
python3 scripts/sourcesManifest.py     # writes /Volumes/MacieExternal/sources/manifest.json
```

24 datasets are already on the external volume under
`/Volumes/MacieExternal/sources/archives/<slug>/`, each with its licence, status,
and SHA-256 in `manifest.json`. Prose summaries live in
[`data-sources.md`](./data-sources.md); what we owe each of them is in
[`data-sources-attribution.md`](./data-sources-attribution.md). The refused ones
are kept on disk on purpose, so a licence decision can be re-checked instead of
re-argued.
