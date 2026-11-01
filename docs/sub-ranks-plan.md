# Sub-ranks: subgenus, infraspecific taxa, subfamily/tribe

Status: **plan saved 2026-11-01; step 0 in progress.** Measured against
COL 26.10 (`catalogue-of-life-2026-10`, 14 Oct) and `species.parquet` of
2026-11-01 07:44.

## Where we are

| | Tree | COL 26.10, accepted, six kingdoms |
|---|---|---|
| subfamily / tribe / subtribe | 774 / 924 / 0 nodes (hand-built animal families) | 7,416 / 5,616 / 1,549 |
| subgenus | 0 nodes; matching ignores it | 13,428, plus ~175k animal species names written with one |
| subspecies | 111 nodes; `subspeciesCount > 0` on 2,145 species, mostly Wikipedia | 147,694 |
| variety / form | 0 nodes; 129 plant `var.`/`subsp.` names stored as SPECIES | 24,405 / 776 |

Why: `importColChecklist.py` takes species *and* subspecies as candidates
but reduces each to its bare binomial (`taxamatch.bare_binomial`), so a
subspecies only ever confirms its species and is dropped; varieties and
forms are not candidates at all. The bare binomial -- no authorship, no
subgenus -- is the identity every importer, dedupe and report matches on,
and stays so.

99.9% of COL's accepted infraspecific taxa hang from a species we hold
(animal subspecies 115,334 of 115,393; plant subspecies 29,592 of 29,655;
plant varieties 21,588 of 21,614).

## Steps

0. **Clean up the quoted WoRMS names first** (a defect, found while
   measuring this). The WoRMS take of 2026-10-12 (`checklistbank-2011`,
   `a903bcfa72e`) kept CSV quotes: 49,083 SPECIES nodes named like
   `"Apororhynchus hemignathi"`, quotes in name, authorship, lineage and id.
   47,547 duplicate an unquoted species held in the same kingdom (merge,
   keeping sourceIds); 1,347 are subgenus names stored as species
   (`"Pallisentis (Brevitritospinus)`; remove); ~190 have no twin (strip
   the quotes). Through a maintenance session.

1. **Subgenus as a field on the species, not a tree level.** `subgenus` on
   the SPECIES node; name and identity unchanged. Sources disagree about
   subgenus placement far more than about genus, and as a level every
   disagreement becomes a duplicate or a move. Fits the nomenclatural track:
   `applyEnrichment.py` takes one more fill-only field, filled from COL.
   The portal can group a genus by it later.

2. **Infraspecific taxa as nodes under their species.** SUBSPECIES /
   VARIETY / FORM children of a held species, ~173k from COL 26.10 (+3.5%
   nodes); `subspeciesCount` then comes from a source. The 129 plant
   infraspecifics stored as species move under their parent. Hybrids stay
   SPECIES (`Asplenium × lacei`, ~3.6k plant nothospecies; the
   `nothosubsp.` names stored as species are infraspecific and move).
   Needs:
   - a writer that attaches children under an existing species (fill-only,
     like `applyEnrichment.py`, under `maintenanceLock`);
   - `verifyTree` invariants: an infraspecific taxon sits under the species
     its name starts with; one name is not attached twice;
   - the build: `buildData.ts` only compresses species without children
     into `speciesList[]`, so per-order files would grow. Let the compressed
     entry carry its infraspecifics compactly instead.
   Measure the build growth before writing.

3. **Subfamily / tribe / subtribe as fields on GENUS, for now.** From COL's
   classification; mainly for navigation in very large families
   (Curculionidae). The existing SUBFAMILY/TRIBE nodes stay. Optional.

## Notes

- The coverage report's "described" share (69%) is inflated by template
  descriptions ("... is a apororhynchidae species found in its native
  region"), which these quoted nodes carry too.
- `colCoverageReport.py` strips the subgenus before matching; any other
  COL-name matcher has to as well.
