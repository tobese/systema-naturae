# Web-Search Enrichment — Test Shot & Targeted Tier (2026-07-06)

## Test shot

**Target:** Hydatellaceae — highest-% *partial* family (92.9% filled; 14 species, 1 gap).

**Gap species:** *Trithuria brevistyla* de Lange & Mosyakin (`sourcedFrom: none`).

**Why the 3-source pipeline missed it:** POWO/GBIF treat the name as a **synonym**
of *Trithuria inconspicua* subsp. *brevistyla*, so the binomial returned no
description. The enrichment gaps are disproportionately **synonyms, recently
described taxa, regional endemics, and fossils.**

**Web-search yield:** immediate rich hit from the **New Zealand Plant Conservation
Network (NZPCN)** factsheet (CC-BY), plus Flora of NZ and Biota of NZ. Data the
pipeline lacked: full morphology, distribution, habitat, conservation status,
flowering/fruiting periods.

**Applied:** wrote a concise sourced description, `sourcedFrom: "nzpcn"`.
Hydatellaceae is now **full (14/14)**; `enrichmentStatus` auto-flipped
`partial → full`. Commit `402ca310`.

## Targeted tier — near-complete partial families

Rather than a blanket web-search over the ~296k gap species (mostly obscure, low
yield-per-effort), the highest-value action is to **finish off families that are
one or two species short of complete.**

- **36 families** are 1–2 species short → **47 gap species** to research.
- Completing them flips **25 families straight to `full`** and advances 11 more.
- Some gaps are **fossil/extinct taxa** (e.g. *Archaefructus sinensis*,
  *Butomites cretaceus*, *Akania americana*, *Tetrameleoxylon prenudiflora*) —
  these may only have paleobotanical descriptions or none.

### Provenance / licensing
Each new source gets its own `sourcedFrom` value (e.g. `nzpcn`), consistent with
the `powo` pattern, to keep provenance and licensing clean (NZPCN is CC-BY).

## Implications
- Web search is **high per-hit value but heterogeneous** (NZPCN, regional floras,
  herbaria) — best applied *targeted*, not bulk.
- Good future sweeps: **regional-endemic clusters** (NZ/AU against NZPCN & Flora
  of NZ/AU) and the **near-complete family** long tail.
