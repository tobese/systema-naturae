# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
```

## Catalogue of Life

Assessed and **partially applied** — see
[`data-sources.md`](../docs/data-sources.md) and the manifest entry
`catalogue-of-life`.

Base Release 2026-09-11 (DOI 10.48580/dgz5n, CC BY 4.0) holds 2,269,433 accepted
species. Measured against the tree:

| | species | note |
|---|---|---|
| Stage 1 — family we already have | **427,804 applied** | 3,413 families, no new scaffolding, 431,305 authorship records |
| Stage 2 — family we lack | ~818,006 held back | 9,591 families across 1,403 orders we do not have |
| COL synonyms | 2.6M held back | importing them is a taxonomy decision, not a data one |

Stage 2 is deliberately not done: adding 1,403 orders and 9,591 families is a
structural change to the portal rather than an import, and worth deciding on its
own merits. Stage 1 was the part that needed no new orders, no colour themes and
no conflict with the circumscriptions the Species Files gave us.

Two limitations worth recording. The DwCA export has **7 columns and no source
field**, so nodes are attributed to COL rather than to the ~160 underlying
checklists — which weakens the per-source attribution model. And ColDP, which
*would* carry per-name provenance, currently 404s on GET.
