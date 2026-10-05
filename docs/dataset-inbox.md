# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
```

## Triaged 2026-10-05 (fifth batch) — the global sets, measured not sampled

Five datasets, and the opposite of the fourth batch: this is the top of
ChecklistBank by size, not a pile of group-specific checklists. WFO Plant List
1,663,770 name usages, ITIS 993,349, Tropicos 1,368,229, Species Fungorum
541,761, IRMNG 567,549.

So nothing here was decided on a 600-name sample. `scripts/apiOverlapReport.py`
pages each dataset's whole accepted list through the API — no download — and
tests it against `taxaserve`. Measured, spread across the alphabet:

| pasted as | dataset | rank measured | measured | **already held** | families held | licence | vintage | verdict |
|---|---|---|---|---|---|---|---|---|
| World Flora | 2004 WFO Plant List 2026-06 | SPECIES | 14,154 | **43.8%** | **97.4%** (719/738) | CC0 | **2026-06** | **take** |
| ITIS | 2144 ITIS | SPECIES | 59,183 | **71.5%** | 81.6% (7,215/8,843) | CC0 | **2026-08** | **taken, +68,813** |
| Tropicos | 310868 Tropicos | SPECIES | 20,580 | 19.4% | 44.0% | CC BY | 2021 | **decline** |
| Fungurum | 1028 Species Fungorum | SPECIES | 70,961 | 69.9% | 85.3% | **none stated** | 2026-09 | **blocked on licence** |
| IMRNG | 2007 IRMNG | GENUS | 33,773 | 59.9% | 56.0% | CC BY | 2026-09 | **decline** |

**WFO Plant List is the one that matters, and it is not close.** CC0, issued
2026-06-21, four months old, and 97.4% of its families are ones we already hold
— which is the whole point of the pending-family work. A source whose families
we mostly have is a source that extends the tree instead of manufacturing
placeholders: the import refused **1,071 species out of 408,939, or 0.26%**.
Under the Wikispecies importer the same shape produced 191,866 refusals, because
that source names families we do not have. The difference is not the importer,
it is the source.

Import measured at **158,701 species added** into 719 families, by the
importer's own held/new test rather than a string comparison.

**Tropicos is declined on vintage, and it is the one I expected to take.** 19.4%
held reads like the largest opening in the batch, and it is 2021 data being
offered in the same breath as a 2026 WFO list covering the same ground. Taking
it would mean importing older nomenclatural data over newer, and its family
coverage of 44.0% says most of its families are ones WFO handles and we do not.

**Species Fungorum is blocked, not declined.** 30.1% of its species are new to
us and it is three months old, which is the second-best source in the batch on
the numbers. ChecklistBank records **no licence** for it, which is the same
position as 1023 and 1025 in the batch above: a dataset with no stated terms is
not a dataset with permissive terms. It is worth one email to Index Fungorum.

**IRMNG is a different kind of thing.** It holds 269,528 genera and 2 species,
so it is a register of genus names rather than a species source, and "59.9% of
its genera are held" is not comparable to the other rows. Its value is
nomenclatural availability, which this tree does not model.

### ITIS, taken — and the risk that produced

**68,813 species added** across 4,776 families in all six kingdoms. 582,013
offered, 259,037 already held, 31,760 refused (5.5%, recorded in the pending
store, taking it to 12,121 families and 154 of them now *present in the tree* —
the first time `pendingFamilies.py report --scaffoldable` has had anything to
say).

The naive estimate was ~150,000 new from the 71.5% held figure. The importer's
own test found 68,813, because the held-check undercounts on authorship
differences and `merge_family` then finds another 167,074 already present. This
is the third time the API estimate and the importer's test have disagreed
materially — 150k against 69k — and it is the reason the verdict numbers in this
table are described as measurements of the *sample*, not predictions of the
import.

**The risk I flagged arrived inside the first hour, in a useful shape.** ITIS
filed the nudibranch *Actinocyclus bifrons* Karsten, 1905 into the **diatom**
family Hemidiscaceae. We already hold it correctly, as a nudibranch in
Actinocyclidae (329 *Actinocyclus* species under
`Mollusca/Gastropoda/Nudibranchia`). `verifyTree.py` caught it as a new
cross-kingdom homonym — and it is not one of the seven documented homonyms,
because it is not a homonym at all: it is one species that ITIS's synoptic
backbone filed under the wrong kingdom. Its copy came out, ours stayed, and the
judgement call is now written down rather than left implicit.

**Two acquisition notes.** The export endpoint returns a
`multipart/form-data` wrapper containing `coldp.zip` rather than a bare archive,
so the DwCA has to be unwrapped from the first `PK` signature — and the ColDP
edition *is* available for this dataset even though `/coldp.zip` returns 406.
ITIS also contains bacteria, and its refusal list is where that shows:
Streptomycetaceae, Oscillatoriaceae, Microcystaceae and Microcoleaceae, none of
which we can place while bacteria are on hold.

**The refused families are the interesting output.** Geoplanidae (872 species) is
a planarian flatworm family — the worm gap from below — and Leuciscidae (674) is
a major freshwater fish family. Both are families we should have and do not, and
1,213 families went to the pending store as a result.

### What the worms question turned up

Asked whether the marine worms are already covered: **the families are, the
species are not.** Lineidae, Polynoidae, Sabellidae, Serpulidae, Syllidae,
Spionidae, Terebellidae and Ampharetidae are all in the tree under
`Animalia/Annelida/Polychaeta` — several of them under an `Unknown` order — and
Nemertea is present as a phylum with Lineidae under it. But of 69 nemertean
species sampled from GBIF's WoRMS checklist, **3 are held (4.3%)**.

So the shape is the inverse of the usual gap: the skeleton exists and is
species-empty. Neither WFO nor ITIS fixes that, since both are weak on marine
invertebrates relative to their size. WoRMS is 1,219,588 species in GBIF and is
the source that would, and it is not in this batch.

### Two measurements worth not trusting

The sampling bias was worth **23 points**. WFO measured 66.2% held on its first
600 names, which were all `Aa…`, and 43.8% held spread across the alphabet. The
first number came from offset-paging an alphabetical list and should never have
been quoted at that precision — which is why the exact tool exists now.

And IRMNG at species rank reported a confident **100% already-held** from a
two-name sample. That was not a good result, it was a register of genera being
asked about species. `sampleDatasetOverlap.py` took `--rank` after that, and
`taxaserve` learned to answer genus and family lookups.

## Triaged 2026-10-05 (fourth batch) — six offered, none worth taking

Seven paste lines, six datasets. "Scarabs" arrived with no URL, and "Phylla"
(1023) and "Ryth" (1025) are the abbreviated paste labels rather than the
dataset's own names — both resolve, so both were triaged on their merits.

| pasted as | dataset | what | vintage | name usages | **already held** | licence | verdict |
|---|---|---|---|---|---|---|---|
| SF Ortho | 1021 | Orthoptera Species File | **Oct 2026** | 30,890 | **88.3%** | CC BY | **do not take** |
| Fleas | 1022 | Parhost World Database of Fleas | 2005-11 | 2,047 | **96.7%** | *other* | **do not take** |
| Phylla | 1023 | Phyllachorales | Oct 2017 | 1,311 | **95.8%** | **none stated** | **do not take** |
| Ryth | 1025 | Rhytismatales | Oct 2017 | 769 | **96.7%** | **none stated** | **do not take** |
| Scales | 1026 | ScaleNet, World Database of Scale Insects | Dec 2004 | 7,074 | **83.7%** | CC BY | **do not take** |
| Ticks | 1030 | TicksBase | Jun 2005 | 796 | **100%** | CC BY | **do not take** |

**None of the six clears the bar, and three of them are blocked on licensing
before coverage even matters.** 1022 declares `other`, and 1023 and 1025 declare
no licence at all, so they are not usable on evidence — a dataset with no stated
terms is not a dataset with permissive terms. That is the same question as 1012
in the batch below, and it is a question about permission, not about data.

**Orthoptera is the strongest of a weak field, and it is the current edition of a
source we already hold.** 88.3% is the lowest overlap figure in the batch, which
sounds like an opening, and the vintage explains it: issued **2026-10-01**, four
days ago, and our `orthoptera species file` rows were imported from an earlier
release. 27,194 species already carry that provenance. The ~3,580 names it would
add are new *to this year's* circumscription — taxonomic churn in one taxonomic
group over one release cycle — not names we are missing. The clean way to take
it would be to re-import OSF as a replacement and diff, not to merge a second
copy on top, and that is a decision about whether OSF's newer arrangement is
better than what we hold. Not obviously worth it for a group this well covered.

**TicksBase is 100% and the sample is not small enough to be lucky.** 600 of 600,
and the whole dataset is 796 name usages. There is nothing there for us.

**ScaleNet's 16.3% is the largest miss in the batch and I am still declining it.**
That is 2004 data on scale insects, and the names it would add are the ones a
twenty-year-old circumscription and a current one disagree about. The earlier
LepIndex verdict in the batch below applies verbatim: a good share of such a
source's novelty is obsolete names rather than missing taxa, and importing those
is a taxonomy decision, not a data one. If we decide we want synonym coverage
rather than only accepted taxa, ScaleNet becomes worth revisiting alongside
LepIndex — that is a policy question, and this batch is not the place to settle it.

So: **zero taken, six declined, no downloads.** That is the cheapest possible
outcome for six datasets and it is the point of sampling rather than fetching.

**One tooling bug found while doing this**, worth recording because it made the
first attempt look like a hang. `scripts/sampleDatasetOverlap.py` called
`held_names()` five times for animalia alone — three inside an f-string and two
by assignment — and each call re-reads all 10,601 animalia family files. Five
full passes over 14,085 files happened before a single API request, with
animalia at 1.68M species; triaging three datasets did not finish in 30 minutes.
Now each kingdom is walked once into a single set. Same six datasets in 59
seconds.

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
