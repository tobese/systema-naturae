# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
https://www.gbif.org/dataset/80dd9c94-241b-4d49-999f-c89de7648525

https://www.gbif.org/dataset/65c9103f-2fbf-414b-9b0b-e47ca96c5df2

https://www.gbif.org/dataset/e01b0cbb-a10a-420c-b5f3-a3b20cc266ad

https://www.gbif.org/dataset/214c3109-d37a-40f8-9c24-5b6e59915394

https://www.gbif.org/dataset/6fb9265c-2d98-40ad-989d-7b6bf4820519
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
| [World Spider Catalog](https://www.gbif.org/dataset/80dd9c94-241b-4d49-999f-c89de7648525) | already assessed | Duplicate — indexed since 2026-10-02. 487 synonyms and a continent map for 17,492 of the 18,710 continent-less araneae are still unapplied, which is the highest-value spider work outstanding. |
| [Afromoths](https://www.gbif.org/dataset/65c9103f-2fbf-414b-9b0b-e47ca96c5df2) | **ready** | Downloaded (6.4 MB). 29,983 accepted species, 137 families, **91,005 distribution rows**. Needs a new importer. |
| [Aphid Species File](https://www.gbif.org/dataset/214c3109-d37a-40f8-9c24-5b6e59915394) | **ready** | Downloaded (3.5 MB). 5,544 species, 32 families. Dry run already passes on existing tooling. |
| [ICTV Master Species List](https://www.gbif.org/dataset/e01b0cbb-a10a-420c-b5f3-a3b20cc266ad) | assessed | Not importable. Covers viruses, which belong to none of the six kingdoms in `kingdom-config.json`. Its declared archive endpoint 404s as well. |

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
