# Remaining Gap Source Analysis

Last updated: 28 June 2026 — after `fillFamilyGap.ts` batch closed 334 species from GBIF cache.

**Total outstanding:** 34,081 species across 20 families (dominated by `chrysomelidae` at 33,690).

Every remaining gap shares the same root cause: **the GBIF cache does not contain the missing species**. These gaps cannot be closed by re-running `fillFamilyGap.ts` — they need a different data source.

---

## Why the GBIF cache can't help

`fillFamilyGap.ts` loads a GBIF class cache (`gbif-cache-<class>.json[.gz]`), deduplicates by scientific name, and compares against the existing data file. If the cache has ≤ what we already have, there's nothing to add.

The remaining gaps fall into five categories:

---

## 1. Chrysomelidae — 33,690 (the elephant)

| Field | Value |
|---|---|
| Class | Insecta |
| Have | 1,310 |
| Target | 35,000 |
| Cache | 1,310 (deduped) |

**Root cause:** The GBIF cache for Insecta is labelled `gbif-cache-insecta-old.json.gz` — it was a partial/early cache built before the current pipeline matured. It only contains ~1,300 species for Chrysomelidae, which is <4% of the known 35,000.

**To close:** Rebuild the GBIF cache for Insecta (or just Chrysomelidae) via `scripts/cacheGbifClass.ts`, then re-run `fillFamilyGap.ts chrysomelidae`. Cache rebuild will take a long time (GBIF API rate limits) and the resulting cache may be too large for git (consider `.json.gz` only).

---

## 2. Amphibia targets — 287 (hylidae 234, pelobatidae 50, pipidae 3)

| Family | Have | Target | Cache | Source mismatch |
|---|---|---|---|---|
| hylidae | 766 | 1,000 | 766 | AmphibiaWeb → ~1,000 spp |
| pelobatidae | 50 | 100 | 18 | AmphibiaWeb → ~100 spp |
| pipidae | 52 | 55 | 52 | AmphibiaWeb → ~55 spp |

**Root cause:** The `speciesCount` targets in `taxonomy.json` were set from **AmphibiaWeb** (the standard amphibian taxonomy authority), but GBIF's taxonomic backbone splits several traditional families:
- **Phyllomedusidae** (leaf frogs, ~65 spp) was split from Hylidae in GBIF
- **Batrachylidae** (~15 spp) was also split from Hylidae
- **Megophryidae** (~200 spp) was split from Pelobatidae

Our targets include these split-off species; GBIF doesn't list them under the parent family.

**To close:** Either (a) lower `speciesCount` in taxonomy.json to match GBIF counts, (b) import the split families (Phyllomedusidae, Batrachylidae, Megophryidae) as separate entries, or (c) use the AmphibiaWeb API directly to fetch species lists then enrich from Wikipedia.

---

## 3. Actinopterygii targets — 47 (pleuronectidae 29, nothobranchiidae 14, characidae 4)

| Family | Have | Target | Cache | Notes |
|---|---|---|---|---|
| pleuronectidae | 72 | 101 | 72 | FishBase target > GBIF |
| nothobranchiidae | 326 | 340 | 326 | FishBase target > GBIF |
| characidae | 1,196 | 1,200 | 1,196 | FishBase target > GBIF |

**Root cause:** `speciesCount` targets were set from **FishBase** / Catalog of Fishes, which recognises more species than GBIF's current taxonomy for these families.

**To close:** Either (a) lower targets to match GBIF, (b) use the FishBase API or Catalog of Fishes to fetch the missing species, or (c) use the Wikipedia REST API (via `fillFamilyGap.ts --no-cache`) to search for missing species by genus.

---

## 4. Aves IOC-specific families — 51 across 10 families

| Family | Have | Target | Gap | Cache | Issue |
|---|---|---|---|---|---|
| tityridae | 28 | 45 | 17 | 0 | Not in GBIF cache |
| vangidae | 28 | 40 | 12 | 22 | Cache < our count |
| paradoxornithidae | 30 | 37 | 7 | 0 | Not in GBIF cache |
| artamidae | 19 | 24 | 5 | 17 | Cache < our count |
| cacatuidae | 17 | 21 | 4 | 4 | Cache < our count |
| cinclosomatidae | 10 | 12 | 2 | 0 | Not in GBIF cache |
| bernieriidae | 10 | 11 | 1 | 0 | Not in GBIF cache |
| alcippeidae | 9 | 10 | 1 | 0 | Not in GBIF cache |
| chloropseidae | 12 | 13 | 1 | 12 | Cache = our count |
| pteroclidae | 15 | 16 | 1 | 1 | Cache < our count |

**Root cause:** These families follow the **IOC World Bird List** taxonomy, which splits certain groups differently from GBIF. GBIF either (a) doesn't recognise the family at all (cache returns 0) or (b) lumps species under a broader family, so the cache has fewer than IOC recognises.

**To close:** The IOC checklist is the authoritative source. Options:
- Use the IOC spreadsheet directly (download from worldbirdnames.org) to get the full species list, then use `fillFamilyGap.ts` with `NO_WIKI=1` to add minimal entries, then run a Wikipedia enrichment pass.
- Or run a targeted Wikipedia REST API search per genus to find missing species names.

---

## 5. Tiny gaps — 10 across 5 families

| Family | Gap | Notes |
|---|---|---|
| viperidae | 3 | Cache = 367, our count = 367 |
| ommastrephidae | 2 | Cache = 28, our count = 28 |
| architeuthidae | 1 | Cache = 1, our count = 1 |
| pipidae | 3 | (covered in Amphibia section above) |
| characidae | 4 | (covered in FishBase section above) |

**Root cause:** SpeciesCount targets slightly exceed what GBIF recognises. Likely reflects lag between species description and GBIF indexing.

**To close:** Manually add via `fillFamilyGap.ts` with live GBIF API (`--live` flag not yet implemented), or accept these as GBIF lag and close the gap in a future cache refresh.

---

## Summary

| Category | Families | Gap | Recommended approach |
|---|---|---|---|
| Chrysomelidae (Insecta cache) | 1 | 33,690 | Rebuild GBIF cache; multi-pass import |
| Amphibia source mismatch | 3 | 287 | AmphibiaWeb API or import split families |
| FishBase source mismatch | 3 | 47 | FishBase API or Catalog of Fishes |
| IOC-specific Aves | 10 | 51 | IOC checklist directly |
| Tiny GBIF lag | 5 | 10 | Accept or manual Wikipedia batch |

**Total: 20 families, 34,081 gap.**  
Note that 33,690 (99%) of this is chrysomelidae — the rest (391) are all sub-300-per-family gaps caused by taxonomic authority mismatches, not missing data.
