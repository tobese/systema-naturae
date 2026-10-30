# Holding bacteria and viruses

> **ONLY THE PORTAL IS ON HOLD, as of 2026-10-30.** Importing *and
> scaffolding new families* are both in scope now; building and deploying
> either kingdom stay on hold, and `kingdom-config.json` still declares six.
> `scripts/scaffoldFamilies.py --kingdom bacteria|viruses` works like any
> other kingdom, writing `portal/data/taxonomy-{bacteria,viruses}.json`.
> The virus tree keeps the Kingdom > Phylum > Class > Order > Family shape
> it already has (no ICTV realm level), so scaffolding fits it as it is.
>
> **The two kingdoms are filled on q-bert, not Macie.** The writer
> partition (`scripts/writerKingdoms.py`, `SN_WRITE_KINGDOMS`) gives each
> machine its own kingdoms: unset means the six portal kingdoms, so Macie
> never writes these two; q-bert runs with
> `SN_WRITE_KINGDOMS=bacteria,viruses`. Enforced in every writer:
> importwrite (403 `foreignKingdom`), `importTransformed.py`,
> `importColChecklist.py`'s direct writes, and `scaffoldFamilies.py`. Mixed
> sources (NCBI, ENA, Wikidata, COL XR, the Backbone) are applied on both
> machines, each taking its own kingdoms.
>
> q-bert's setup:
>
>     # its own importwrite on the q-bert checkout
>     SN_WRITE_KINGDOMS=bacteria,viruses IMPORTWRITE_ROOT=~/src/systema-naturae \
>         services/importwrite/importwrite
>     # its own ordinator: own queue, no downloads, no side tasks
>     SN_WRITE_KINGDOMS=bacteria,viruses SN_QUEUE_DIR=data/source-queue-bv \
>         SN_SOURCES_ROOT=~/src/sources IMPORTWRITE_URL=http://localhost:8089 \
>         services/import-ordinator/import-ordinator --loop --no-download --no-side-tasks
>
> Archives are copied to q-bert by hand (`--no-download`). q-bert commits
> only `taxonomy/{bacteria,viruses}/`, `portal/data/taxonomy-{bacteria,viruses}.json`,
> `data/source-queue-bv/` and the append-only logs, which `.gitattributes`
> merges with `merge=union`. Quality checks for these kingdoms are run by
> name, since every default walk stays the six:
> `dedupeSpeciesAcrossFamilies.py --kingdom bacteria` (and `viruses`),
> `resyncFamilyCounts.py --kingdom bacteria --kingdom viruses`.
>
> Measured 2026-10-30, dry runs on Macie's tree: the pending store lists 873
> bacteria families (521k species) and 259 virus families (168k); of the 259,
> 224 are already held and 35 would be scaffolded from the GBIF Backbone.
> Dedupe finds 8 duplicate bacteria species and 10 virus; resync finds 34
> family counts behind their files.

> **PARTIALLY LIFTED 2026-10-25.** On hold as of 2026-10-04, reaffirmed
> 2026-10-17: import, scaffolding, build and deploy all blocked. As of
> 2026-10-25, **importing is back in scope** — not a bug-fix, a decision,
> made because the two kingdoms kept arriving inside normal source imports
> anyway (NCBI's checklistbank-2169 and ENA's checklistbank-2265 runs the
> same week bucketed roughly 200k bacteria/virus taxa as UNRESOLVED KINGDOM
> between them) and refusing data already in hand stopped making sense.
> **Scaffolding a brand-new bacteria/virus family, building either kingdom,
> and deploying either kingdom are all still on hold** — only merging new
> species into the 3,784 bacteria + 393 viruses families already on disk is
> back in scope. Sources: `ncbi-taxonomy`, `ictv-msl`, `gtdb` and
> `wikidata-species` are all on the record. Everything below the line is
> retained because the measurement is expensive to redo and because the rest
> of the hold may also be lifted eventually; none of it is a task list. The
> rank question is settled for bacteria (see *Settled* below) and still open
> for viruses — it no longer blocks *import* (merging into an existing
> family doesn't require re-deriving its rank), only new-family scaffolding
> and the build/deploy decision.
>
> **What "import yes, portal no" means mechanically.**
> `portal/data/kingdom-config.json` still declares six kingdoms and must
> keep declaring six. It is what `buildAllKingdoms.sh`,
> `tree.kingdom_names()`, `verifyTree` and `sanity_scan` all read, so the
> six-kingdom list is still the enforcement for everything build/deploy/
> verify-side. `scripts/importColChecklist.py` instead resolves bacteria/
> viruses through a hardcoded `BACTERIA_VIRUSES_INPUT` side-channel (added
> 2026-10-25) that never touches that file — the same asymmetry
> `post-import.sh`'s `SN_INPUT` override already has for the build side,
> just run the other direction for import.
>
> **The family files on disk are a known artefact, not an oversight — and
> now a live import target.** An import ran on q-bert (`Import NCBI
> bacteria/viruses + GTDB`, commits `d75d600cd1`, `efc0c5f72b`) and left
> **3,784 bacteria and 393 viruses** families committed under `taxonomy/`.
> They are still unreachable from the portal — not in `kingdom-config.json`,
> so not grafted, not built, not deployed, and invisible to `make check` —
> which is why `tree.family_data_files()` undercounts the true family-file
> total on disk. What changed 2026-10-25: a normal source import (ENA)
> merged 19,360 more species into this same set via the import-side fix
> above. A source offering a genuinely new bacteria/virus family still gets
> refused, same as any other kingdom's missing-family case — scaffolding one
> is still a taxonomy decision this hold defers, same as it always was.
>
> One place names these kingdoms outside this paragraph, on purpose:
> `scripts/post-import.sh` appends `bacteria viruses` to the config kingdom list
> so a uuid backfill does not silently skip work already on disk. That is a
> correctness fix for the backfill, not a build of the kingdoms. Read it before
> "correcting" it.

The decision this document was written to inform: **the project should hold
viruses and bacteria** — they are a fifth of the tree's potential and no amount
of waiting makes COL supply them in a form the importer can use. What was open
is *at what rank*, because COL and Wikidata both decline to say, and the answer
determines whether an import is a clean extension or 17 new kingdoms.

Measured against the DwCA (2026-08 COL Base Release) and Wikidata Species
(2026-08-02, DOI [10.48580/dgx38](https://doi.org/10.48580/dgx38)), both CC BY 4.0
and CC0 respectively. Every count here is reproducible with
`scripts/overlapReport.py`.

## Why this is a decision and not a bug

COL's DwCA has four roots: `Eukaryota` (2,652,500 taxa), `Bacteria` (33,365),
`Viruses` (22,669), `Archaea` (1,076). Walking every taxon to its root looks
like the answer — two clean kingdoms, 44,077 species between them.

It is not, because of *how the ranks are labelled*. `importColStage2.chain()`
resolves a kingdom by looking for rank `kingdom`, then `superkingdom`, then
`domain`, first match walking upward. Under Bacteria:

| COL clade | accepted species | families |
|---|---|---|
| Bacillati | 13,873 | 252 |
| Pseudomonadati | 12,368 | 406 |
| Thermotogati | 297 | 12 |
| Fusobacteriati | 79 | 3 |
| `Bacteria` (the domain itself) | **2** | 0 |

So `--kingdom Bacteria` imports **two species**. `--kingdom Viruses` imports
**none**: the virus root has rank `unranked`, which `chain()` does not look for,
so nothing resolves and every taxon is filtered out — and the run prints its
normal summary and exits 0. That silent success is the failure mode to avoid;
it is why this is written down rather than left to whoever runs it next.

Wikidata does not help. It carries the same 17 clades at `kingdom` rank —
Bacillati, Pseudomonadati, Methanobacteriati, Thermoproteati, Thermotogati,
Fusobacteriati, Nanobdellati, Promethearchaeati, Orthornavirae, Heunggongvirae,
Shotokuvirae, Bamfordvirae, Pararnavirae, Sangervirae, Loebvirae, Zilligvirae,
Trapavirae, Helvetiavirae — because it is generated from the same upstream. It
also has `Bacteria` as both a domain and a kingdom, plus `Virus`, `Prokaryota`
and `Monera` as competing roots. Adopting Wikidata does not dodge the question.

## What is actually there

Two kingdoms' worth of species, and Wikidata adds more:

| | COL DwCA | Wikidata Species |
|---|---|---|
| bacterial species | 26,525 | not separable — same 17 clades |
| viral species | 17,552 | includes *Hepatitis B virus* → Hepadnaviridae, *Human herpesvirus 6* → Herpesviridae |
| new against our tree | — | 1,811,989 species overall, 56.5% of the archive |

**Settled, by GTDB r232 (fetched 2026-10-04, `scripts/coldp.py` reads it):**
COL's names are not GTDB's names, and COL's rank is not GTDB's rank.

| | COL | GTDB r232 |
|---|---|---|
| the group COL calls `Bacillati` | **not a GTDB name at all** | `Bacillota`, rank **phylum**, domain Bacteria |
| the group COL calls `Pseudomonadati` | **not a GTDB name at all** | `Pseudomonadota`, rank **phylum**, domain Bacteria |
| rank used for that level | `kingdom` | `phylum` |
| top of the hierarchy | 4 roots, ranks `kingdom`/`superkingdom`/`domain`/`unranked` | **2 domains**, Bacteria and Archaea |
| ranks present anywhere | kingdom, phylum, class, order, family… | species, genus, family, order, class, phylum, domain — **no kingdom rank exists** |

All eight of COL's prokaryote clade names (`Bacillati`, `Pseudomonadati`,
`Thermotogati`, `Fusobacteriati`, `Methanobacteriati`, `Thermoproteati`,
`Nanobdellati`, `Promethearchaeati`) return **zero hits** in GTDB at any rank.
They are not older or newer spellings of GTDB names; they are a different
naming convention (`-ati` where GTDB writes `-ota`) applied to the same
organisms, and COL then ranks them one level too high.

So the claim option A rested on is now a citation rather than an assertion:
treating those groups as **phyla** is what the authority says, and it is what
this tree already does for Archaea — Methanobacteriota, Microcaldota,
Nanobdellota, Promethearchaeota, Thermoproteota are GTDB phyla and are already
kingdom-rank nodes here. GTDB holds 199,923 species (189,801 bacterial, 10,122
archaeal) in 3,967 families, so it is also a better source than COL for these
kingdoms outright.

What GTDB does **not** settle is viruses: its scope is `Bacteria and Archaea`
and it contains no viral taxa at all. Option B's half — hold viruses back until
ICTV is ingested — survives this evidence intact.

## The options

**A. Two kingdoms, 17 phyla inside each.** Add `bacteria` and `viruses` to
`kingdom-config.json`; teach `chain()` to fall back to the root taxon when no
kingdom-ish rank is found; the clades become phyla. *For:* two new
`kingdom-config.json` entries, one new input file and colour registry each, and
a tree shape matching Archaea's. *Against:* asserts Bacteria and Viruses are
equivalent in rank when GTDB and ICTV treat them differently; needs the rank
fallback, which is a behaviour change in a script every kingdom runs through.
*Cost:* the plumbing is small; the taxonomy claim is the real decision.

**B. Bacteria as a seventh kingdom, viruses held back.** Same treatment for
Bacteria; leave viruses out until ICTV is taken properly. *For:* viruses are the
harder half — ICTV's MSL is a spreadsheet with 50+ realms and no parent
hierarchy our tree can hold, and a virus placed in the wrong realm is worse than
one absent. *Against:* leaves ~17,552 species out for a reason that is about our
ingestion, not about the data.

**C. 17 kingdoms, one per clade.** What `--kingdom Bacillati` gives you today,
essentially for free. *For:* needs no code change and no judgement. *Against:*
seventeen peer kingdoms in the switcher, and Bacillati is not a kingdom — this
reproduces the source's mislabelling as our structure. **Not recommended**;
listed because it is the path of least resistance and should be ruled out
explicitly.

**D. Do not hold them.** *For:* no work, no new kingdoms, no rank debate. *Against:*
the tree claims 1.7M species across six kingdoms and silently omits an entire
domain of life. This is the current state and it is the thing being changed.

## What each option needs

| | rank fallback in `chain()` | new kingdoms in config | new input files | new colour registries | taxonomy decision |
|---|---|---|---|---|---|
| A | yes | 2 | 2 | 2 | asserts Bacteria ≡ Viruses |
| B | yes | 1 | 1 | 1 | asserts Bacteria is a kingdom |
| C | no | 17 | 17 | 17 | none, which is the problem |
| D | no | — | — | — | asserts they are out of scope |

Every option is plumbing except the last column. The code is not the expensive
part of this decision.

## Reference datasets, in the order they bear on it

1. **GTDB** (DOI [10.15468/dpzg84](https://doi.org/10.15468/dpzg84), CC BY 4.0) —
   the authority for the rank Bacillati and Pseudomonadati actually sit at.
   Registered as `gtdb`, not downloaded. Fetch this **before** deciding, not
   after: it is what converts option A's taxonomy claim from an assertion into a
   citation.
2. **ICTV MSL** (DOI
   [10.5281/zenodo.19154110](https://doi.org/10.5281/zenodo.19154110), ratified
   February 2026) — the virus authority. An xlsx, not a DwCA and not a NEWICK,
   so it needs its own reader either way. `sources/archives/ictv-msl/` is an
   empty directory waiting for it.
3. **NCBI Taxonomy** (DOI [10.15468/rhydar](https://doi.org/10.15468/rhydar),
   CC0) — carries Bacteria and Viruses as real divisions with real authorities,
   which is the one thing neither COL nor Wikidata does. Registered as
   `ncbi-taxonomy`, not downloaded.

## What the hold does not stop

Registering sources is unaffected and continues. Both remaining sources are now
on the record without being fetched:

| source | state | why it matters when the hold lifts |
|---|---|---|
| `gtdb` | **downloaded**, 21.6 MB ColDP, sha256 recorded | settles the bacterial rank (above) |
| `ncbi-taxonomy` | registered, **not downloaded** | the only candidate carrying Bacteria and Viruses as real divisions with real authorities |
| `ictv-msl` | registered, **not downloaded** | the virus authority; xlsx, and nothing here reads xlsx yet |
| `wikidata-species` | downloaded and assessed | 1,811,989 new species overall, but the same 17 clades, so it does not help the rank question |

**`wikidata-species`'s sidecar tables are not held by this hold either.**
Measured against the held tree 2026-10-10 (joined, not just counted):

| sidecar | archive taxa | held in tree | already covered | **gap** |
|---|---|---|---|---|
| Media.tsv → image | 340,025 | 192,847 | 110,224 | 82,623 (but 99.75% of rows carry no licence string) |
| VernacularName.tsv → commonName (en/blank) | 95,067 | 70,935 | 36,620 | **APPLIED 2026-10-10: 39,322 filled** (scripts/enrichCommonNamesFromWikidata.py; bigger than the 23,287 the GBIF Backbone pass filled) |
| Distribution.tsv → continents | 103,213 | 66,815 | 35,043 | 31,772 (84% free text needing resolution, 16% ISO-mappable now) |

Enrichment only needs species we already hold, which is orthogonal to the
bacteria-and-viruses rank question, so none of this needs to wait for the
hold to lift. See the `wikidata-species` entry in
`scripts/sourcesManifest.py` for the full breakdown and caveats.
**Vernacular names are now applied** (2026-10-10,
`scripts/enrichCommonNamesFromWikidata.py`, 39,322 filled) — it was the
clear first pick: the largest clean gap, no licence problem, and the same
safety pattern as the already-applied GBIF Backbone importer carried over
directly, plus one filter it didn't need (31 candidates that were just the
binomial re-capitalised, not a translation). Media and Distribution remain
unapplied -- the first needs a per-image Commons licence lookup, the
second needs free-text place-name resolution for 84% of its rows.

## Related

- [`archive-formats.md`](archive-formats.md) — the formats, and which have a
  reader (ColDP does as of `scripts/coldp.py`; xlsx and NEWICK do not)
- [`dataset-inbox.md`](dataset-inbox.md) — where these were triaged
- `scripts/importColStage2.py` — `chain()` and the `--kingdom` filter
- `docs/data-sources.md` — the registry