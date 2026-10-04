# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
```
COL Hierarchy
https://www.checklistbank.org/dataset/1000/metadata

Craneflies
https://www.checklistbank.org/dataset/1005/metadata


Reptiles
https://www.checklistbank.org/dataset/1008/metadata


## Triaged 2026-10-04 — four pastes, one of them a real find

All four arrived with the same URL, `https://www.gbif.org/dataset/search?type=CHECKLIST`,
which is a *search page* rather than a dataset — so none of them named a dataset
to fetch. Resolved through the GBIF dataset API instead:

| pasted as | resolves to | verdict |
|---|---|---|
| **NCBI** | NCBI Taxonomy, DOI [10.15468/rhydar](https://doi.org/10.15468/rhydar), GBIF `fab88965…`, CC0, published 2026-04-17 | **assessed, worth having** — manifest `ncbi-taxonomy` |
| **Vascular Plants** | World Checklist of Vascular Plants, DOI 10.15468/6h8ucr | **already applied** — manifest `wcvp`. Nothing to do |
| **Plants** | ambiguous | **needs a specific dataset** — see below |
| **wiki** | nothing | **no such dataset** — Wikispecies returns 0 GBIF checklists |

**NCBI is the one worth having, and it answers a question COL cannot.** It is
the only candidate that carries Bacteria and Viruses as real divisions with real
authorities — COL holds the prokaryotes and viruses in 17 clades at `kingdom`
rank, which is why neither `--kingdom Bacteria` nor `--kingdom Viruses` reaches
them (see below). Set against that, GBIF Backbone is already applied and is
itself built partly from NCBI, so for the kingdoms we hold this is largely a
second copy of names we already have. The narrow, real value: prokaryote and
viral coverage, plus the type material and literature citations the NCBI record
carries and no checklist we hold does. CC0, so licensing is not an obstacle.

Chasing the same question turned up a second dataset worth having, entered as
manifest `gtdb`: **Genome Taxonomy Database r226.0**, DOI
[10.15468/dpzg84](https://doi.org/10.15468/dpzg84), CC BY 4.0. Bacillati and
Pseudomonadati — the two clades holding 26,241 of COL's bacteria — are GTDB
*phyla*, so GTDB is the authority that says what rank they belong at, and our
Archaea kingdom is already built on GTDB phylum-level ranks. Worth fetching
before deciding how to map COL's bacteria, not before.

**"Plants" is too vague to triage and probably already covered.** GBIF holds
thousands of plant checklists and the search does not surface one canonical
"Plants" dataset; a paste of this kind cannot be acted on. We already hold
`wcvp` (vascular plants, applied), `usda-plants` (assessed, 2,657 NativeRange
records still unresolved) and COL's plant coverage via Stage 2. If the intent is
a specific flora, paste its GBIF dataset key or DOI.

**"wiki" does not resolve.** Wikispecies has no GBIF checklist — the API returns
zero for it. We already take Wikimedia Commons (`wikimedia-commons`, applied) for
media. If a Wikispecies *taxonomy* dump is wanted it has to come from Wikimedia
dumps directly, and it would be a name list competing with what GBIF Backbone
and COL already give us.


## Catalogue of Life

Assessed and **partially applied** — see
[`data-sources.md`](../docs/data-sources.md) and the manifest entry
`catalogue-of-life`.

Base Release 2026-09-11 (DOI 10.48580/dgz5n, CC BY 4.0) holds 2,269,433 accepted
species. Measured against the tree:

| | species | note |
|---|---|---|
| Stage 1 — animalia, family we already have | **427,804 applied** | 3,413 families, no new scaffolding, 431,305 authorship records |
| Stage 2 — Fungi + Chromista | **27,812 applied** | 719 new family files + 350 into 95 existing families |
| Stage 2 — Animalia | **672,185 applied** | 5,152 new family files, 33 enriched in place; families 5,472 → 10,601 |
| Stage 2 — remaining kingdoms | not yet applied | Plantae, Protozoa, Archaea — all small next to Animalia |
| Stage 2 — bacteria + viruses | **needs a decision** | not a `kingdom-config.json` problem after all; see below |
| COL synonyms | 2.6M held back | importing them is a taxonomy decision, not a data one |

Stage 2 was originally deferred as "a structural change rather than an import",
which turned out to be half right: it *is* structural, but only for the kingdoms
whose families we lack. Fungi went 773 → 1,193 families and Chromista 703 → 1,002
with no conflict against the Species File circumscriptions, because the Species
Files covered animals. Animalia needed deciding on and is now applied.

### Bacteria and viruses are not two kingdoms, and COL has no kingdom to target

This was recorded as "blocked: not declared in `kingdom-config.json` yet", on the
strength of `importColStage2.py`'s own docstring. Measured against the DwCA, both
halves are wrong. COL declares `domain Bacteria` — **one accepted species** — and
no virus realm at all; what it actually holds is 17 clades at `kingdom` rank, and
those are what `--kingdom` would filter on:

| COL clade | accepted species | accepted families |
|---|---|---|
| Bacillati | 13,873 | 252 |
| Pseudomonadati | 12,368 | 406 |
| Orthornavirae | 7,201 | 148 |
| Heunggongvirae | 6,521 | 132 |
| Shotokuvirae | 2,351 | 29 |
| Methanobacteriati | 707 | 31 |
| Bamfordvirae | 326 | 26 |
| Pararnavirae | 276 | 6 |
| Thermotogati | 228 | 12 |
| Sangervirae | 131 | 21 |
| Loebvirae | 110 | 3 |
| Thermoproteati | 82 | 12 |
| Fusobacteriati | 55 | 3 |
| Zilligvirae | 34 | 6 |
| Trapavirae | 23 | 3 |
| Abadenavirae | 20 | 9 |
| Helvetiavirae | 11 | 5 |
| Nanobdellati | 2 | 2 |

So `--kingdom Bacteria` would have imported 1 species and `--kingdom Viruses`
none. The totals (~44k) are what the earlier estimate got right; "two kingdoms"
is what it got wrong. Bacillati and Pseudomonadati are GTDB phyla, which is the
rank our Archaea kingdom already uses for the same level, so the open question is
whether to fold each clade into one portal kingdom as a phylum.

Three things about COL's data that cost real time to find, all recorded in
`scripts/importColStage2.py`:

- **Compare names only after GNparser.** COL writes subgenus trinomials —
  `Aloconota (Aloconota) tenerrima` — where we store `Aloconota tenerrima`. Read
  as raw strings they look like ~96,000 missing Animalia species that we
  already hold. Two rounds of scope measurement were wrong because of this.
- **COL offers the same species twice**, sometimes as a duplicate row with
  identical authorship and sometimes as one accepted name per competing
  authorship (`Saccammina grzybowskii` Schubert, 1902 / Bogdanovich, 1960).
- **COL frequently records no family at all** — 23,536 Animalia species and 8,225
  Fungi species hang directly off a genus. Those resolve via the genus where we
  already hold it, and otherwise get an explicit `Incertae sedis` family.

Two limitations worth recording. The DwCA export has **7 columns and no source
field**, so nodes are attributed to COL rather than to the ~160 underlying
checklists — which weakens the per-source attribution model. And ColDP, which
*would* carry per-name provenance, currently 404s on GET.
