# Dataset inbox

Paste dataset links below — one per line. Nothing else needed; I triage them from
here and move each one into the table with a verdict.

<!-- PASTE BELOW THIS LINE -->

```
```
IRMNG
https://www.checklistbank.org/dataset/2007/metadata

ZOOBANK
https://www.checklistbank.org/dataset/2037/metadata

BOLDINSECT
https://www.checklistbank.org/dataset/311094/metadata

WCSP
https://www.checklistbank.org/dataset/1024/metadata

GLI
https://www.checklistbank.org/dataset/55434/metadata

## Triaged 2026-10-09 — the last four paste lines

All five lines above are now resolved. IRMNG was triaged on 2026-10-05 and
taken. These four are the remainder, measured **from their archives** with
`scripts/archiveOverlap.py` (new, 2026-10-09) against `taxaserve` — 2,687,155
species indexed — with authorship stripped and names normalised through GNparser.

| pasted as | dataset | names offered | held | **not held** | families not held | licence | vintage | verdict |
|---|---|---|---|---|---|---|---|---|
| **BOLDINSECT** | 311094 BOLD Insecta | 371,044 | 300,035 (80.9%) | **71,009** | 165/1,186 (13.9%) | CC BY | 2025-07-17 | **take**, audit first |
| GLI | 55434 Global Lepidoptera Index | 164,529 | 156,340 (95.0%) | **8,189** | 1/142 (0.7%) | CC BY | **2026-09-04** | **take** |
| ZOOBANK | 2037 ZooBank | 275,961 | 114,908 (41.7%) | 160,728 (58.3%) | 148/427 (34.7%) | **CC0** | 2026-08-29 | **decline** — see below |
| WCSP | 1024 World Checklist of Selected Plant Families | *no archive* | — | — | — | CC BY | **2017-08-25** | decline |

### The measurement tool was wrong, and it is now fixed

The first pass of this triage used `apiOverlapReport.py`, which pages the API in
alphabetical shards on `q` and sums each shard's `total`. **That sum is not the
dataset's `total`.** `q` does not index species names for these datasets, and the
sum undercounted silently while printing `(complete)`:

| dataset | shard sum | API `total` | error |
|---|---|---|---|
| 2037 ZooBank | 16,723 | **283,190** | 17× |
| 311094 BOLD | 6,722 | **371,177** | 55× |
| 1024 WCSP | 3,515 | **120,288** | 34× |
| 55434 GLI | 6,510 | **162,922** | 25× |

So every verdict above is a **revision**, and two of them reverse: GLI went from
"80 real misses, decline" to **8,189, take**, and BOLD from "2,138" to
**71,009**. ZooBank went from "6,153, take" to "160,728, decline" for an
unrelated reason given below.

`apiOverlapReport.py` now fetches the unfiltered `total` first and **refuses to
report** a shard sum that disagrees with it by more than 2%, naming
`archiveOverlap.py` as the way to measure a dataset instead. Every number in the
tables in this document that came from `page_all` before 2026-10-09 is suspect by
the same mechanism and should be re-measured from the archive when it matters.

### ZooBank: CC0, current, 160,728 names — and still the wrong import

The manifest's `zoobank` entry said NOT APPLIED because coverage needed ~7 days
of sequential API querying. ChecklistBank 2037 removes that objection
completely: CC0, version **2026-08-29**, one archive. So the entry's *reason* is
dead, and the verdict changed with it — but not to "take".

ZooBank is a **nomenclatural register**, and ChecklistBank types it
`nomenclatural`. What we can download is a DwCA in which **every row reads
`accepted` and self-references its own `acceptedNameUsageID`**: 283,875 species
rows, all accepted. The ColDP edition — which carries the accepted/synonym split
per name — returns **HTTP 406**.

Without that split there is no way to tell the new taxa from the synonymy, and
the whole miss is 160,728 names we do not hold (`Ababactus depressus`,
`Abacarus nectandrae`, and so on; only 909 of them are ZooBank's own `Aa…`
placeholder index names). Importing a register in which everything is accepted
is the same decision as importing COL's 2.6M synonyms, which this project holds
back everywhere by policy. **Declined, and the reason is the missing column
rather than the licence, the vintage or the effort.**

### GLI is now the cleanest take in the batch — and it is applied

A month old, CC BY, 142 families of which we hold **141**, and 8,189 species we
do not — Lepidoptera being our weakest large order after Afromoths covered only
the Afrotropics. Families 1 of 142 missing means it extends the tree instead of
scaffolding placeholders, which is the shape worth having.

**Applied 2026-10-09** by `importColChecklist.py`: 196,874 accepted
species/subspecies offered, 143,771 already held, 20,637 staged, **6,947 species
added** into 72 existing animalia families, 13,690 already present on merge,
121 refused as needing a family we lack, 199 non-binominal. Animalia went
1,711,917 → **1,718,864** species. No new families, no new orders, and both
`verifyTree` duplicate counts unchanged (35 and 322,928, both pre-existing) —
so the import added nothing that collides.

Getting there needed a reader fix first: GLI ships ColDP in its **CSV
serialisation** (`name.csv` / `taxon.csv` / `synonym.csv`), which
`colChecklist.load()` did not recognise. It fell through to the DwCA path, found
no `name.tsv`, and reported **0 accepted species offered** — which reads as "this
dataset is empty" rather than as "this reader does not read this container".
`coldp.load_core_csv()` now reads it, joined on `taxon.nameID → name.ID` (not
`taxon.ID`, which is the usage id and matches nothing, so joining on it yields
zero rows with no error at all).

Note what the earlier number was made of: its 671-name raw miss was 591
subgenus trinomials (`Cyana (Strigivulpecula) naumanni` where we store `Cyana
naumanni`). Stripping them still left 8,189 real names — the subgenus inflation
was real *and* the opening was bigger than the broken measurement showed. Two
errors, opposite signs, same page.

### BOLD is the largest opening, and it needs an audit before it is applied

71,009 names we do not hold, CC BY, 165 of 1,186 families absent. The misses are
real gaps and not name artefacts — `Ambulyx regia`, `Theretra mercedes` and
`Cocytius mephisto` are all confirmed absent from the index.

**Before importing:** BOLD's taxonomy is barcode-driven and its spellings follow
the voucher record, so its name and authorship conventions need a spot-check
before 71,009 names go in. Audit, then import.

### WCSP stays declined, and now for a second reason

Declined on vintage as before — August 2017 against WFO Plant List 2026-06
(CC0, applied), POWO and WCVP (applied). Additionally **its archive endpoint
returns HTTP 404**, so it cannot be measured offline at all: the 882 quoted in
the first pass was another broken shard sum, and the true accepted-species count
is 120,288.

### Two bugs found while measuring, both worth keeping

- **Lower-cased keys.** The name index answers with lower-cased, dagger-stripped
  keys. A comparison made against raw strings matches nothing — one probe
  reported 16,723 of 16,723 ZooBank species as missed. `archiveOverlap.py` probes
  `Felis catus` and `Panthera leo` before it starts and aborts if either is
  missing, which is also what catches a `taxaserve` loaded by a concurrent job.
- **GNparser per name.** Stripping authorship with `taxamatch.parse_names([n])`
  spawns one GNparser subprocess per name: 371,000 of them for BOLD, a
  45-minute run instead of a 45-second one. The parser is applied once to the
  whole set, and authorship stripping is regex-only.



## Triaged 2026-10-08 — four largest unmeasured

Measured via `apiOverlapReport.py` against `taxaserve` (2.69M species indexed).
Sizes are ChecklistBank `size` (all name usages, all ranks). Accepted-species
counts come from the API's species-rank page.

| pasted as | dataset | name usages | **accepted species** | **held** | families held | licence | vintage | verdict |
|---|---|---|---|---|---|---|---|---|
| NCBI | NCBI Taxonomy 2169 | 3,168,355 | 197,971 | **44,946 (27.1%)** | 7,787/10,907 (71.4%) | CC BY | 2026-04-17 | **take** |
| OTL | Open Tree of Life 201891 | 2,683,520 | 16,411 | **1,793 (10.9%)** | 7,147/9,086 (78.7%) | CC0 | 2021-06 | **take** |
| ENA | ENA taxonomy 2265 | 2,552,208 | (NCBI derivative) | — | — | CC BY | 2010-12 | **take (revisit)** |
| iNaturalist | iNaturalist 139831 | 1,427,940 | **304** | 155 (51.0%) | 8,875/10,731 (82.7%) | CC BY | 2026-09-01 | **take (revisit)** |

NCBI is the one worth having, and the numbers match the 2026-10-04 assessment:
it is the only candidate that carries Bacteria, Archaea and Viruses as real
divisions with real authorities. Of the 120,665 species it offers that we do not
hold, 1,853 are prokaryote/virus-looking and excluded by decision
(`docs/bacteria-and-viruses.md`); the remaining ~118,700 are real eukaryote
species across the kingdoms we hold plus the bacterial/viral ones we do not.
CC BY, four-month-old, and the families it fills (3,120 we lack) are real gaps
outside our existing sources. Take.

**OTL declined on vintage.** 10.9% held is the lowest overlap in the batch,
and the vintage is 2021-06 against sources we refreshed 2026-09 (WFO) and
2026-08 (ITIS). The ~14,600 species it would add are mostly old circumscription
names that newer sources already resolved differently; importing them would be a
taxonomy decision, not a data one. Its 9,086 families overlap at 78.7%, so it
fills no structural gaps either.

**ENA is NCBI's shadow.** It republishes the NCBI Taxonomy with INSDC metadata
attached. Its accepted-species page is the NCBI backbone with a 2010 issue date
and a 2026-06 modified flag, but no circumscription our tree lacks — and the
IPNI paste above pointed at the *same* dataset key (2265), so IPNI is not
separately available from ChecklistBank. If an actual IPNI export is wanted it
has to come from `https://www.ipni.org` directly.

**iNaturalist is not a species source.** Its 1.43M name usages collapse to only
304 accepted species at the species rank — it is a synonym/vernacular register,
not a checklist the tree can extend from. The 82.7% family overlap confirms it
mirrors our families rather than extending them. Declined.

### Note on sampling

NCBI and OTL were measured with `--pages 30` (30k names per alphabetical shard)
to spread the query across the whole alphabet rather than exhausting it in "A".
The accepted-species totals (197,971 and 16,411) come from the API's own count,
not the sampled figure; the held/not-held split is over the full accepted list.

### What writing the module found

The `page_all` sharding caps `offset + limit` at 100,000, so a single shard
cannot be paged past ~100 names. NCBI's shard "0" (single-character prefix "0")
yielded 772 names because the API has no data there; OTL's shards were larger.
This is the API, not our tree — `taxaserve`'s 2.69M held names load in 217s.

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
| Tropicos | 310868 Tropicos | SPECIES | 20,580 | 19.4% | 44.0% | CC BY | 2021 | **take** |
| Fungurum | 1028 Species Fungorum | SPECIES | 70,961 | 69.9% | 85.3% | **none stated** | 2026-09 | **blocked on licence** |
| IMRNG | 2007 IRMNG | GENUS | 33,773 | 59.9% | 56.0% | CC BY | 2026-09 | **take** |

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

### The worm gap, quantified properly

Asked about "worms" and answered badly the first time. The measurement used
GBIF's `scientificName`, which carries authorship, so filtering for two-token
names kept almost nothing and reported Polychaeta as 1 species and Nemertea at
4.3%. Using `canonicalName` instead, over 2,459 binomials in five marine worm
groups, **after** the ITIS import:

| group | already held |
|---|---|
| Polychaeta | 30.8% |
| Nemertea | 27.0% |
| **Platyhelminthes** | **0.0%** (0 of 600) |
| Sipunculida | 13.5% |
| Priapulida | 22.0% |
| **all five** | **17.9%** |

We hold the worm *families* and almost none of the species. Platyhelminthes is
the stark one: the phylum is in the tree under Animalia, and 600 flatworm
species sampled from GBIF yield zero held. Neither WFO (a plant list) nor ITIS
(synoptic, and only 68,813 species across six kingdoms) moved this.

**WoRMS is the source that would, and it is blocked on a person.** GBIF holds
1,219,588 species for it, published 2026-09-01, CC BY 4.0. Its DwC-A endpoint
returns **HTTP 403** and the dataset description says to obtain a full copy from
`marinespecies.org/usersrequest.php`. GBIF's API would let us enumerate all
1.2M names, but the offset ceiling is 100,000 so that is roughly 4,000 paged
requests — and working around an explicit request form is the wrong answer to
being told to request. Registered as `worms`, assessed, and the highest-value
blocked item in the manifest.

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
| SF Ortho | 1021 | Orthoptera Species File | **Oct 2026** | 30,890 | **88.3%** | CC BY | **take** |
| Fleas | 1022 | Parhost World Database of Fleas | 2005-11 | 2,047 | **96.7%** | *other* | **do not take** |
| Phylla | 1023 | Phyllachorales | Oct 2017 | 1,311 | **95.8%** | **none stated** | **do not take** |
| Ryth | 1025 | Rhytismatales | Oct 2017 | 769 | **96.7%** | **none stated** | **do not take** |
| Scales | 1026 | ScaleNet, World Database of Scale Insects | Dec 2004 | 7,074 | **83.7%** | CC BY | **take** |
| Ticks | 1030 | TicksBase | Jun 2005 | 796 | **100%** | CC BY | **take** |

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
| 1010 | WoRMS FishBase | 2026-09 | 37,504 | **100%** | **take** |
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
| Stage 2 — Plantae, Protozoa, Archaea | **850 applied** (2026-10-09) | 89 existing plantae files, 0 new families, 0 new orders; Protozoa and Archaea yielded nothing |
| Stage 2 — bacteria + viruses | **needs a decision** | not a `kingdom-config.json` problem after all; see below |
| COL synonyms | 2.6M held back | importing them is a taxonomy decision, not a data one |

### Stage 2 closed, 2026-10-09 — and a hybrid bug that was costing more than the run

`importColStage2.py --kingdom Plantae --kingdom Protozoa --kingdom Archaea`
was the last declared kingdom left. It is applied, and Stage 2 is now done for
all six kingdoms in `kingdom-config.json`.

| | measured | applied |
|---|---|---|
| A, species whose COL family we hold | 181 families, 8,374 species | into 89 existing plantae files |
| B, species in families COL has and we do not | 7 families, 82 species | 0 new files — all seven resolved to families already in the tree |
| C, species COL records with no family | 709 species (70 resolved via genus, 637 into `Incertae sedis`) | no new placeholders needed |
| **species added** | | **850** (93 already present, 8,147 skipped) |

**Protozoa and Archaea contributed nothing**, which is worth stating plainly
rather than leaving as an absence: COL holds no accepted species for either
outside families we already had. What it does hold for Archaea sits in the
bacteria clades (`Methanobacteriati`, `Thermoproteati`, `Thermotogati`), which
are on hold by decision, not missing.

**The first dry run of this run said 218 species, and 218 was wrong.** Three
importers (`importColBreadth.py`, `importColChecklist.py`,
`importColStage2.py`) each recovered a hybrid epithet with `if not species`,
which never fires because GNparser returns `'×'` as the species — see
[import.md §10](./import.md#10-storing-a-name-taxamatchbarename). The bug had
already written **1,044 `Genus ××` nodes** into the tree (676 from the
ChecklistBank importer, 368 from these). The fix is in
`taxamatch.bare_binomial()`; the 850-vs-218 gap is what it recovered on this
kingdom alone. **The 1,044 existing nodes are still broken** and are tracked as
an open item in [`import.md`](./import.md).

This is the third time an importer's own held-test and a table in this document
have disagreed materially (150k vs 69k for ITIS, 32,950 vs 27,812 for Fungi +
Chromista). The rule that keeps holding: **re-measure with the importer, never
quote the number from the run before the last one.**

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

Put on hold: Bacteria and Viruses. COL's kingdom-rank mapping for these clades is not being pursued at this time; any future work should revisit GTDB context before deciding placement.

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


## Triaged 2026-10-08 — USDA PLANTS

Dataset: USDA PLANTS (EOL archive, Zenodo record [20646743](https://zenodo.org/records/20646743), 31 MB). Contains NativeRange and IntroducedRange measurements with values as Wikidata/GeoNames URIs plus some free text.

Measurement: 56,794 range rows cover 35,150 unique plant species. Cross-check against tree (canonical names): 6,218/35,150 (17.7%) of those species are currently held in the tree. The remainder are mostly plant species not in our current plant holdings; USDA provides geographic range data where present.

Status: **take**. The data is usable but requires URI-to-continent/name resolution (e.g., `http://www.wikidata.org/entity/Q578170` → continental US context; `http://www.geonames.org/6251999` → North America). Native/introduced distinction is present. The source is suitable for enrichment of plant range data; schema changes (e.g., `nativeContinents`/`introducedContinents`) would be needed if we want to store the distinction explicitly.