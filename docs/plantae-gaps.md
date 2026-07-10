# Plantae — empty family coverage gap

**Status:** identified — no viable source found yet
**Candidate list:** [`portal/data/gap-report-plantae.json`](../portal/data/gap-report-plantae.json) — 790 families
**Written after:** GBIF phylum scouts confirmed all empty families have 0 species in the GBIF backbone.

---

## TL;DR

790 Plantae families (across 43 classes, 7 phyla) are scaffolded in the portal — they have an
`appSlug`, a color theme, and a spot in `taxonomy-plantae-snippet.json` — but hold **0 species**
and their `speciesCount` is `0`. This is **correct**, not a bug — GBIF cannot supply their
species:

- **GBIF phylum scouts** (`gbif-scout-tracheophyta.json`, `gbif-scout-bryophyta.json`,
  `gbif-scout-marchantiophyta.json`, `gbif-scout-anthocerotophyta.json`,
  `gbif-scout-charophyta.json`, `gbif-scout-chlorophyta.json`,
  `gbif-scout-rhodophyta.json`) were run. Every empty family returned `speciesCount: 0`
  from the GBIF backbone match API.
- **GBIF class caches** exist only for `magnoliopsida` and `liliopsida` — the two classes that
  already have species. No caches were built for the other classes because the scouts
  confirmed there's nothing to cache.

These families are almost entirely **non-flowering plants** — conifers, cycads, ferns,
mosses, liverworts, hornworts, algae (green, red, stoneworts) — and many are **fossil
groups**. This is analogous to the animal-side WoRMS candidates
([`docs/worms-integration.md`](./worms-integration.md)), where marine/fossil families also
fall outside GBIF's coverage.

## What was populated (and how)

The **477 populated families** (all at or above their `speciesCount` target) cover only
two classes within phylum Tracheophyta:

| Class | Families | Species | Source |
|---|---|---|---|
| Magnoliopsida (dicots) | 443 | 298,297 | Bootstrap + GBIF cache + Wikipedia |
| Liliopsida (monocots) | 104 | 92,734 | Bootstrap + GBIF cache + Wikipedia |

These were imported via the standard pipeline: GBIF class cache → import from cache →
Wikipedia enrichment.

## The 790 empty families — by phylum

| Phylum | Classes | Empty families | Notes |
|---|---|---|---|
| **Tracheophyta** (vascular plants) | 6 | 179 | Pinopsida (conifers), Polypodiopsida (ferns), Lycopodiopsida (clubmosses), Cycadopsida, Ginkgoopsida, Gnetopsida |
| **Chlorophyta** (green algae) | 11 | 177 | Ulvophyceae, Chlorophyceae, Trebouxiophyceae, Prasinophyceae, etc. |
| **Rhodophyta** (red algae) | 7 | 152 | Florideophyceae, Bangiophyceae, Cyanidiophyceae, etc. |
| **Bryophyta** (mosses) | 6 | 146 | Bryopsida, Sphagnopsida, Polytrichopsida, Andreaeopsida, etc. |
| **Marchantiophyta** (liverworts) | 3 | 98 | Jungermanniopsida, Marchantiopsida, Haplomitriopsida |
| **Charophyta** (stoneworts) | 6 | 31 | Charophyceae, Zygnematophyceae, Klebsormidiophyceae, etc. |
| **Anthocerotophyta** (hornworts) | 2 | 6 | Anthocerotopsida, Leiosporocerotopsida |

The full breakdown lives in `docs/gap-tasks-phyla.md` (plant section, once generated).

## Next steps

The GBIF backbone, Wikipedia, and WoRMS are all ruled out. Likely candidates:

1. **POWO** (Plants of the World Online, `https://powo.science.kew.org/`) — authoritative
   source for vascular plants (conifers, ferns, cycads, etc.). Has a REST API.
2. **WFO** (World Flora Online, `https://www.worldfloraonline.org/`) — open-access global
   flora. Provides taxonomic data + species descriptions.
3. **AlgaeBase** (`https://www.algaebase.org/`) — authoritative for algae (Chlorophyta,
   Rhodophyta, Charophyta).
4. **Tropicos** (`https://www.tropicos.org/`) — Missouri Botanical Garden; good for
   bryophytes and vascular plants.
5. **GBIF species/search** at the genus level (not family level) — some families may have
   species that GBIF assigns under different family keys. This was tried for the animal
   WoRMS candidates and yielded negligible results.

Before committing to a source, a small sample (e.g. 5 representative families from
different phyla) should be manually verified to confirm species availability.
