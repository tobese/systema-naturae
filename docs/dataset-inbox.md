# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
```

## Triaged 2026-10-04 (third batch) — six datasets, sampled rather than downloaded

Seven paste lines, six datasets: one entry arrived blank and the next was
LepIndex, both pointing at dataset 1018.

Measured with `scripts/sampleDatasetOverlap.py`, which pages a sample of each
dataset's accepted species through the ChecklistBank API and tests the names
against what is on disk. Downloading six archives to find out whether they were
worth anything is the expensive way to ask, and after the ReptileDB lesson a
name count is not evidence either way.

| dataset | what | vintage | name usages | **already held** | verdict |
|---|---|---|---|---|---|
| 1010 | WoRMS FishBase | 2026-09 | 37,504 | **100%** | **do not take** |
| 1015 | ILDIS — World Database of Legumes | 2014-05 | 16,349 | **0.3%** | **take — the only real gap here** |
| 1018 | LepIndex — Global Lepidoptera Names Index | 2012-01 | 133,948 | ~77% | **take — biggest absolute gain** |
| 1019 | Moss TROPICOS (MOST) | 2004-07 | 13,300 | ~76% | take, small |
| 1011 | FLOW — Fulgoromorpha Lists | 2019-02 | 13,450 | ~85% | take, small |
| 1012 | Glomeromycota (arbuscular mycorrhizal fungi) | 2017-10 | 284 | 83% | **licence is "other" — check before use** |

**FishBase: your guess was right, and then some.** Not "maybe we have them" —
600 of 600 sampled species already on disk, zero new. Our registry already
carries `fishbase` as partial (an EOL harvest with 28 marginal English names
after GBIF vernacular); this ChecklistBank edition at CC BY adds nothing to it.

**ILDIS is the one genuine gap in the batch**: 0 of 150, 0 of 150, 1 of 150 and
0 of 150 at four offsets spread across the dataset. Legumes are a very large
group and we hold almost none of ILDIS's names.

**LepIndex offers the most in absolute terms** — roughly 23% of 133,948 is
around 30,000 names — but it is a 2012 source, so a good share of what it would
add is probably obsolete names rather than missing taxa. That is a taxonomy
question, not a data one, and it is the same question as the COL synonyms we
hold back everywhere else.

Two caveats on the method. The sample is the API's name order, which is
alphabetical, so each figure above was taken at four spread offsets rather than
at one; and a "not held" name is not automatically a species we want, which
matters most for the three pre-2015 sources.

## Triaged 2026-10-04 (second batch) — two good sources, one superseded

| pasted as | resolves to | verdict |
|---|---|---|
| **Craneflies** | Catalogue of Craneflies of the World, ChecklistBank 1005, DOI [10.48580/d37p](https://doi.org/10.48580/d37p), CC0, Apr 2025 | **taken and applied** — 372 of 16,061 species added |
| **Reptiles** | The Reptile Database, ChecklistBank 1008, DOI [10.48580/d37s](https://doi.org/10.48580/d37s), CC BY, 2026-06 | **taken and applied** — 1 of 15,612 species added |
| **COL Hierarchy** | Catalogue of Life Hierarchy (COLH) v1.4, ChecklistBank 1000 | **superseded** — do not take |

> **Both verdicts above were wrong on the evidence, and are corrected here.**
> They were written before anything was downloaded, from comparing name counts
> against name counts, and both overstated the gap. What follows is what the
> import actually found.

**Neither source was a gap. Both were near-duplicates** — which is the user's
guess being right, and the reason checking was worth the download:

| | species offered | already on disk | added |
|---|---|---|---|
| Craneflies | 16,061 | 15,683 | **372** (370 Limoniidae, 2 Tipulidae) |
| ReptileDB | 15,612 | 15,611 | **1** (Scincidae) |

The Reptiles verdict was the worse error: 34,366 name usages against our 16,612
node speciesCount looks like a doubling, but 34,366 includes 17,325 synonyms
and 2,962 subspecies. Reptiles are among the best-documented organisms on earth
and we already hold 15,611 of the 15,612 on offer, which is what being
well-documented means.

Craneflies came with a second lesson attached. The canonical index —
`portal/data/name-parse-index.jsonl`, a snapshot taken **before** the Stage 2
import — scored 15,563 of its species as new. Measured against the family files
it is 378, and `merge_family` settled it at 372 with 15,191 already present.
An index that is a snapshot will disagree with the tree it indexes, and the
direction it errs is toward over-reporting novelty.

Neither is blocked on format: both are external-origin ChecklistBank datasets,
so both arrive as ColDP, and `scripts/coldp.py` reads that as of `dc0726a87`.
That is the opposite of NCBI and GTDB, which are still only registered.

**COL Hierarchy is superseded.** COLH v1.4 was issued **2019-05-06** and
ChecklistBank holds only **2,844 name usages** for it — a legacy remnant of a
source whose live version we already hold. The current Catalogue of Life is
**dataset 3** (alias `COL`, version `project`), which is the 2026 base release
imported in `a268f11c0` and extended by `6ea5a62d5`. Worth recording so nobody
re-triages it: the name still reads like the authoritative backbone and the
dataset key looks authoritative too.

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
