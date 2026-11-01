# q-bert: bacteria and viruses, what is left to take

Status: **steps 1, 2, 3, 5 done 2026-11-01; step 4 measured, not taken.** Measured on Macie against
origin's copy of q-bert's two kingdoms (`c5b0df4ab61`, 2026-10-30) and the
archives' routing caches. Setup and rules: docs/bacteria-and-viruses.md.

## What q-bert holds

| | bacteria | viruses |
|---|---|---|
| families | 3,784 | 393 |
| species | 222,730 | 28,104 |
| with an authorship | 32,284 (14%) | 0 (ICTV names carry none) |

The bacteria are mostly not named species:

| name shape | count | example |
|---|---|---|
| GTDB genome placeholder | 161,743 | `CBDUSG01 sp965602895` |
| GTDB suffixed placeholder | 6,497 | `Onstottus_A frigus` |
| Latin binomial | 50,031 | `Aminicenans sakinawicola` |
| "uncultured X" and other | 3,855 | `uncultured Brevitalea` |
| "Candidatus Genus" as a species | 604 | `Candidatus Koribacter` |

Taken on q-bert's queue (`data/source-queue-bv/`): NCBI 2169 (+2,928),
ENA 2265 (+62), ICTV MSL 1014 (+218), COL 26.9 XR 316441 (+802), GBIF
Backbone (+6,010). GTDB 2214 blocked on its licence.

## Not yet taken

Bacteria/virus names each archive offers that q-bert does not hold
(distinct canonical names, nearly all into families it holds):

| source | bacteria | viruses | note |
|---|---|---|---|
| ENA 2265 | 175 | 1,542 | applied 10-30 before the DwCA fix; re-run |
| OTT 201890 (CC0) | 3,930 | 0 | held for the six kingdoms (provenance); measure its prokaryote sources |
| COL 26.10 | 304 | 0 | parked for Macie; additions-only on q-bert |
| Wikidata 314569 (CC0) | 28 | 232 | held for the six kingdoms |
| 1174 | 138 | 0 | being re-applied on Macie |
| TAXREF 2008 | 61 | 0 | |
| ITIS | 48 | 0 | none into a held family: scaffolding |
| 2041 | 37 | 5 | |
| iNaturalist 139831 | 15 | 18 | |
| COL China 312616 | 21 | 0 | |
| 64 smaller checklists | < 150 together | | |
| GTDB r232 | 891 Latin names | | mostly archaea (Macie's kingdom); its 179k placeholders are what q-bert already holds from the first import |

So the named-species gap is small, ~6,500. The larger work is the quality
of what is held.

## Order

1. **Sync q-bert** to origin/main (nomenclatural track, maintenanceSession,
   writer and DwCA fixes, the waiting marker).
2. **Mixed-source pass**: put the archives above on q-bert's queue
   (`--no-download`, copied by hand) -- ENA re-run, 1174, 2041, TAXREF,
   COL China, iNaturalist, COL 26.10 additions-only. ~2,500 names.
3. **LPSN on the nomenclatural track.** Declined on 2026-10-12 as "a
   nomenclatural register, not a taxonomy" -- which is now exactly what the
   track is for. The prokaryote name authority: authorship for the 50k
   Latin binomials (14% authored today) and the validly-published status.
   Needs a download (LPSN exports after registration) and its licence
   checked; a `KINGDOMS_FOR` entry ("bacteria", "archaea" -- archaea on
   Macie).
4. **OTT for bacteria only**: measure what its 3,930 rest on (NCBI, SILVA,
   GBIF) before deciding.
5. **Wikidata viruses** (232), after 2.

## Decisions for the user

- **GTDB placeholders** (168,240 `sp<accession>` and `_A` names): keep as
  species, keep but mark (a `placeholder` flag the portal can filter), or
  move to the unplaced store. They are genome clusters, not described
  species; inventory-over-volume says mark at least.
- **"uncultured X" and "Candidatus Genus" stored as species** (~4,400):
  not species; remove (or move to the unplaced store).
- **GTDB licence: settled 2026-11-01.** gtdb.ecogenomic.org says CC BY-SA
  4.0 (ShareAlike), not the CC BY 4.0 our manifest had; corrected. The
  user judged it fine. ShareAlike means the bacteria data, once published,
  goes out under BY-SA, credited as GTDB asks in "Cite GTDB" on
  https://gtdb.ecogenomic.org/about (also in docs/data-sources-attribution.md). r232 (2026-04-15) is still the
  latest release and is what we hold; the HTTP mirrors serve it, so no
  torrent client is needed.
- **LPSN**: registration and licence.

## Done (2026-11-01 evening)

| step | result |
|---|---|
| 1 sync | q-bert at origin/main, binaries rebuilt, services restarted |
| 2 mixed sources | COL 26.10, 1174, 2041, TAXREF, COL China, iNaturalist, UKSI, Denmark: +204 species, ~16,800 merged (`6901adc6e39`) |
| 3 LPSN | bacteria: 8,754 authorships filled (8,193 with year), 3,209 LPSN ids; 23,002 agree, 939 conflicts, 4,748 synonym pairs both held (`863eb32b7c4`). Archaea on Macie. LPSN is CC BY-SA 4.0 |
| 4 OTT | measured, **not taken**: of its 3,930 unheld bacteria names 3,188 are environmental/placeholder sequence names ("uncultured methanotroph", "proteobacterium KCB90", "X sp."), 661 Latin binomials -- some misrouted (a brittle star, a Solanum) -- and 81 other. LPSN already covers the validly published names |
| 5 Wikidata | +20 species, 8,386 merged (`f53cfb9bc70`) |
| ENA re-run | left out: its 30 Oct re-run already applied; the 1,542 virus names it still offers were refused then |
