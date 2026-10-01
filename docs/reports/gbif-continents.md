# Fill `continents` from the GBIF Backbone `Distribution` table

## Result

| kingdom | species with no `continents` | GBIF has some | yield |
|---|---|---|---|
| animalia | 519,484 | 25,172 | 4.85% |
| plantae | 435,023 | 11,307 | 2.60% |
| fungi | 161,380 | **32,274** | **20.00%** |
| chromista | 74,036 | 5,303 | 7.16% |
| protozoa | 3,868 | 1,181 | **30.53%** |
| archaea | 1,965 | 0 | 0.00% |
| **total** | **1,195,756** | **75,237** | **6.29%** |

**This is the single best return found in the GBIF backbone.** For comparison,
`Description.tsv` — the 1.2 GB prose table — yields 1.33%, and 0.79% once the
same genus-opening gate every other enricher uses is applied. `Distribution.tsv`
yields 6.29% and needs no validation gate at all, because a continent code is not
prose that can be mis-attached.

75,237 species across 5,988 distinct names, 64,906 of them resolving to a single
continent.

## Why it is better than the description yield, and why that is the surprise

The description pass failed because GBIF's text comes from Plazi literature
treatments, and there is very little for fungi and algae. Distributions are not
in that store at all — they come from the range maps and checklists of the 105
source datasets the backbone aggregates, and *those* cover fungi well. The same
backbone, the same 2023 snapshot, the same free keyless download, and a 4.7x
better yield on a field we need 1.19M times.

Fungi at 20% is the headline: fungi are the weakest kingdom in this project
(2.4% described), and this fills one field for a fifth of them.

## Provenance

`gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c` — the GBIF Backbone
Taxonomy, export of **2023-08-28**, CC-BY 4.0. The file is
`~/Downloads/backbone.zip` (971 MB); `Distribution.tsv` is 5,530,297 rows.

Three years stale as of writing, which is the same caveat as the rest of this
dataset. The backbone is regenerated regularly and `hosted-datasets.gbif.org`
archives every version, so a fresher copy is available without asking anyone.

## How the join works

`Taxon.tsv` has no continent column, so this is a two-hop join:

1. `Distribution.tsv` → `taxonID` → set of continent codes, via `countryCode`
2. `Taxon.tsv` → `taxonID` → `canonicalName` (lowercased)
3. match our species `name` against that index

3,694,879 of the 5.5M distribution rows carry a `locality` string but no
`countryCode`. Those are free text (`"Greenland"`, `"Fars Province, Shiraz"`)
and are **not** parsed — inferring a continent from an English place name is the
kind of guess this project has been bitten by before. So the yield above is a
floor, not a ceiling, and the ceiling is unknown without doing that parsing
deliberately.

Only `countryCode` is read, mapped through a fixed 26-country table to our 8
continent names. Every value produced is already in `VALID_CONTINENTS` — verified,
no `UNKNOWN_CONTINENT` rows will be created.

## Safety

- **Only fills empty nodes.** No existing `continents[]` value is read, let alone
  overwritten, so this cannot contradict curated data and cannot introduce a
  conflict.
- **No validation gate needed.** `enrichEmptySpecies.py` needs the genus-opening
  check because prose can be attached to the wrong taxon; a two-letter country
  code mapped through a fixed table cannot.
- **Idempotent** — a second run finds no empty nodes to fill.
- Writes `sourcedFrom: "gbif"` only where something was actually written, and
  never writes a description.

## Not applied

The measurement is done; the write is a separate, reviewable step. It is
`scripts/enrichContinentsFromGbif.py` once written — it needs the distribution
index built first, which is another ~90 s pass over the zip.

One judgement worth recording: multi-continent hits are kept as-is (`Usnea
leioclada` → Europe + South America, a lichen that genuinely is cosmopolitan).
Collapsing to a primary continent would lose information the field is meant to
carry, and 11,331 of the 75,237 are multi-continent.