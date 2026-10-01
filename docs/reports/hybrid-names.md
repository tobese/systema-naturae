# Hybrid names: 11,377 of them, all filed as SPECIES

## Summary

Asked whether GBIF's name parser was worth wiring in, the answer for one of its
`type` values turned out to be yes, and the finding is larger than the parse run
that surfaced it.

The tree declares **5** hybrid nodes: one `HYBRID_GROUP` (`Hybrids`) and four
`HYBRID` (`Zedonk`, `Zorse`, `Hinny`, `Mule`) — all in animalia, all familiar
domestic crosses.

Meanwhile **11,377 names carry a hybrid marker and every one of them is filed as
`SPECIES`**:

| kingdom | names |
|---|---|
| plantae | 11,376 |
| chromista | 1 |
| animalia | 0 |

Concentrated in Orchidaceae (1,386), Asteraceae (902), Rosaceae (722),
Cyperaceae (540), Salicaceae (512), Poaceae (446).

This is the botanical convention, not an error of fact: under the ICN a name
marked `×` **is** named at species rank. `Lycopodium × zeilleri` is a species.
So the rank is defensible and I am not proposing to change 11,377 nodes. What
follows is what is actually wrong.

## Four distinct conventions, and they need different handling

| pattern | count | example |
|---|---|---|
| `Genus×epithet`, no spaces | 8,830 | `Lycopodiella×shortii` |
| `Genus × epithet` | 1,949 | `Lycopodium × zeilleri` |
| `Genus species × species` (both parents named) | 1,045 | `Colchicum cilicicum × speciosum` |
| **leading** `×Genus epithet` (nothogens) | 423 | `× Dryostichum mirabile` |
| intergeneric `Genus × Genus` | 173 | `Anacamptis × Dactylorhiza` |

The first three are same-genus hybrids and are **correctly placed** — verified:
10,953 of 11,377 sit under the genus they name. (The 424 that appeared misplaced
in a first pass were my own genus-extraction failing to strip the leading `×`;
their placement is right.)

## What is genuinely broken: 423 ids have a double underscore

The leading-`×` nothogens derive ids like this:

```
× Asplenicystopteris blindii   ->   SP__ASPLENICYSTOPTERIS_BLINDII
× Cystocarpium roskamianum     ->   SP__CYSTOCARPIUM_ROSKAMIANUM
```

`SP__` — a doubled underscore, because the marker becomes an empty token between
two separators. Every one of the 423 is affected. It is cosmetic on its own, but
the schema note in `BACKLOG.md` already records that ids derive from names and so
collide across kingdoms; a malformed prefix makes that class of bug harder to spot
when it happens.

There is a latent collision behind it. `×Holcosia pseudotaiwaniana` and
`Holcosia pseudotaiwaniana` would both want the same id once the marker is
stripped. No such pair exists today — stripping `×` and whitespace from all
11,377 names produces **zero** collapses — so this is a trap not yet sprung, not
a live bug.

## Why the parser matters here

`/v1/parser/name` returns `type: HYBRID` and an explicit `notho` field saying
*which* part is the hybrid (`GENERIC` / `INFRAGENERIC` / `SPECIFIC` /
`INFRASPECIFIC`). That is a structured statement about hybridity that we do not
have anywhere, and it is the one thing in this whole GBIF investigation that the
tree cannot currently express.

A partial run confirmed it: of 64,478 names parsed, 210 came back `HYBRID` —
against 5 declared hybrid nodes in the tree. The parser is finding real
hybrid names we carry as ordinary species.

**Do not read that 210 as a count of misfiled nodes.** It is 210 from 4.9% of the
names, and the parser's `HYBRID` type clearly requires both parents to be present
in a recognisable arrangement, so it under-reports the `Genus × epithet` form
entirely — the 11,377-name bulk uses a marker the parser does not treat as a
`HYBRID` type at all. The 210 are the *intergeneric* and named-parent forms, which
are the ~1,045 + 173 cases. Those are the ones worth a `HYBRID` rank; the rest are
correctly species.

## Recommended

1. **Fix the 423 ids** — a mechanical, contained fix in whatever derives
   `SP_` prefixes, plus a check that no id contains `__`.
2. **Add a `HYBRID`-rank check to the sanity scanner** for the two forms that are
   genuinely not species: intergeneric (173) and named-parent (1,045). That is
   ~1,218 nodes, not 11,377.
3. **Do not touch** the 10,779 same-genus hybrids. `×` names are species under
   the ICN, and re-ranking them would be wrong.

## Note on the 2.4% and the parse run

Measured separately, over 64,478 of 1,306,268 names before GBIF throttled us:

| `type` | count | share |
|---|---|---|
| `SCIENTIFIC` | 64,202 | 99.57% |
| `HYBRID` | 210 | 0.33% |
| `INFORMAL` | 66 | 0.10% |

`INFORMAL` is the second finding: 66 unresolved `… spec.` names (`Volvox spec`,
`Ulothrix spec`) sitting as SPECIES nodes. Smaller, but the same class of defect
— a node whose name does not denote a real taxon.

Rank agreement with the parser was **100%** on every rank it has vocabulary for
(SPECIES 5,076/5,076, FAMILY 130/130, zero disagreements), so `rankMarker` is an
audit that found nothing. Note the OpenAPI spec's `rankMarker` enum is wrong —
it declares `SPECIES`/`GENUS`/`FAMILY` where the endpoint emits `sp.`/`gen.`/`fam.`;
comparing against the spec scores 0% on every rank.

Full run continues in 8 shards; `portal/data/name-parse-index.jsonl` accumulates.