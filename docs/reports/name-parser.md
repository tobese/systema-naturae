# GBIF name parser over every name in the tree

Complete: **1,306,268** (name, rank) pairs, 8 shards, no gaps. Merged index at
`portal/data/name-parse-index.jsonl`.

## What the endpoint is

`POST /v1/parser/name` — a *structural* parser, not a resolver. It splits a name
into `canonicalName` + `authorship` + `year` + `rankMarker` and assigns a
`type`. It never says whether a name exists; that is `/species/match`.

**The repeated-`name` GET is unusable.** Sending four names returns four results
in the wrong order — `Smilax virosa Buch.-Ham. ex Wall.` came back as
`Amanita muscaria`, with the last name returning itself. Right count, wrong
pairing, no error. Only the POST form is positionally safe, and `parseAllNames.py`
asserts alignment per batch rather than trusting it.

**The OpenAPI spec's `rankMarker` enum is wrong.** It declares
`SPECIES`/`GENUS`/`FAMILY`; the endpoint emits `sp.`/`gen.`/`fam.`. Comparing
against the spec scores 0% agreement on every rank, which reads as total mismatch
and is purely vocabulary. This cost an entire measurement pass.

## `type` distribution

| type | count | share |
|---|---|---|
| `SCIENTIFIC` | 1,297,747 | 99.35% |
| `INFORMAL` | 4,114 | 0.31% |
| `HYBRID` | 2,446 | 0.19% |
| `OTU` | 1,528 | 0.12% |
| `NO_NAME` | 334 | 0.03% |
| `CULTIVAR` | 87 | 0.01% |
| `VIRUS` | 5 | — |
| `BLACKLISTED` | 5 | — |
| `PLACEHOLDER` | 2 | — |

### The four that matter

**`INFORMAL` — 4,114 names that do not denote a species.** Almost all are
`… spec.` unresolved-taxon placeholders filed as `SPECIES`: `Droopiella spec`,
`Acorus spec Linnaeus, 1753`, `Orchis spec Sauter, 1830`. A node whose name is
not a real taxon. This is the same class of defect as the synthetic fixtures
removed on 2026-09-30, and no existing check looks for it.

**`HYBRID` — 2,446.** Covered separately in
[`hybrid-names.md`](hybrid-names.md), which has the full breakdown of the 11,377
hybrid-marked names by convention.

**`OTU` — 1,528 barcode BINs filed as species.** `Scarus sp. BOLD:AAD0897`,
`Salmo sp. BOLD:AAB3872`. These are iBOL/UNITE operational taxonomic units, not
named species; the `BOLD:` accession is a sequence-barcode ID. Every one should
be an `INFORMAL` node at most.

**`NO_NAME` — 334.** Placeholder codes that parse as nothing: `YT-029`, `LC-2`,
`TA-21 sp014523595`, `UBA9949 sp10516u`. These are the archaeal and protist
sequence-code placeholders, and they are filed as real genus and species names.

### Also worth knowing

- **`VIRUS` (5)** — `Bolivina prion Lindenberg, 1965` and `Neoaemula vector` are
  **foraminifera**, named with `vector`/`prion` in the epithet. Not viruses. A
  reminder that the parser's type can be wrong, not just ours.
- **`BLACKLISTED` (5)** — `Pungitius type sp.Omono` appears twice, and
  `Stipa ladakhensis …, nothosp. nov.`
- **`PLACEHOLDER` (2)** — `Actinocyclus polyradiatus`, `Actinocyclus calix`.
- **`partial` parses: 18.** Essentially zero; names parse whole.

## Rank agreement — clean, and the disagreements are all vocabulary

| our rank | agree | disagree | no marker |
|---|---|---|---|
| SPECIES | 1,201,654 (100.0%) | 153 | 3,759 |
| GENUS | — | 93 | 91,558 |
| SUBSPECIES | — | 861 | 0 |
| FAMILY | 2,115 (97.7%) | 49 | 5,645 |

Every "disagreement" is a marker our vocabulary does not have, not a wrong rank:

- **SUBSPECIES 861** — all `infrasp.`. The parser's marker is *coarser* than ours;
  a trinomial is `infrasp.`, not specifically `subsp.`
- **FAMILY 49** — all `supragen.`, i.e. superfamily-level
- **SPECIES 153** — 87 `cv.` (cultivars, correctly `CULTIVAR` type),
  53 `infrasp.`, plus a few `sect.`/`subgen.`/`agg.` — so **section names and
  cultivars filed as `SPECIES`**
- **GENUS 93 disagree + 91,558 no marker** — a monomial gives the parser nothing
  to infer rank from, so absence is not disagreement. The 93 are `supragen.`-type
  genus-level names

So: **no rank in the tree is wrong.** `rankMarker` is an audit that found nothing.
That is a real result — it means the rank assignment work is sound, and it cost
one vocabulary mistake to establish.

## The one thing this endpoint gives us that nothing else does

**562,378 authorship values and 198,613 years** recovered. The tree stores no
`authorship` field on any node today, and 45.5% of species (548,304) carry an
authority baked into both `name` and `id`:

    Smilax zeylanica L.   ->  SP_SMILAX_ZEYLANICA_L_

`enrichFromMycobank.py` adds `authorship` for fungi from MycoBank; this covers
all six kingdoms. The parser is the fallback for every other name, and it is
free and keyless.

The parser does **not** resolve names, so this cannot be used to widen lookup —
the backlog's finding that stripping authority suffixes for *lookup* yields 2
matches per 3,000 stands untouched, and `stripAuthority` should still not be
reached for.

## Recommendation

1. **4,114 `INFORMAL` + 1,528 `OTU` + 334 `NO_NAME` = 5,976 nodes whose names do
   not denote taxa.** Worth a sanity check and a review list; none should be
   silently re-ranked, but a reader currently sees `Salmo sp. BOLD:AAB3872` as a
   species.
2. **Write `authorship`/`year`** from this index, once the `INFORMAL` nodes are
   decided (writing authorship onto a `spec.` placeholder is noise).
3. **Add `UNRESOLVED_TAXON` to `sanity_scan.py`** — the check is cheap and the
   legacy vocabulary never had one.

## Run details

Throughput was ~113 names/s on one connection and ~250/s at 8 workers, but GBIF
throttled without an error: throughput went to zero with the process still alive,
and a request that took 7.5s for 1,000 names later took 11s for **50**. Checked
across two IPs (Macie and gctb) — 11.3s and 12.1s for the same two-name request —
so it is **endpoint-wide backpressure, not per-IP**, and a second machine does not
help. `scripts/parseAllNamesSliced.sh` runs 8 shards with 10-minute gaps
(~2h20m total), each to its own file so an interruption never leaves a
half-overwritten index, then merges with a completeness check.