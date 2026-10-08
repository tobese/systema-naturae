# ID Backfill Plan

Goal: attach external authority IDs (GBIF, Wikidata, COL, WoRMS, ITIS, WFO) to every species in the tree.

## Architecture

```
SOURCES (read-only, versioned)
├── GBIF cache (191 files, per class)
│   ├── Full: 141 classes, ~17.5K species, has nubKey/speciesKey
│   └── Minimal: 49 classes, ~16K species, name-only
├── wiki-images.json: 340K entries, 283K with Wikidata QID
├── COL (future): ~2M taxa, UUID inside LSID
├── WoRMS (future): ~500K marine, AphiaID
├── ITIS (future): ~800K, TSN
└── WFO (future): ~1.4M plants, WFO ID
         │
         ▼
STAGING: DuckDB / Parquet (analytical, rebuildable)
Table: species_id_map
├── uuid (PK part 1) ← from species.parquet
├── source (PK part 2)  ── 'gbif' | 'wikidata' | 'col' | 'worms' | 'itis' | 'wfo'
├── external_id         ── the actual ID value
├── matched_on          ── 'exact' | 'fuzzy' | 'genus'
├── confidence          ── 0.0–1.0
├── source_version      ── GBIF release, dump date, etc.
└── loaded_at           ── timestamp
         │
         ▼
MERGE / DEDUP
- One row per (uuid, source)
- Conflicts: keep highest confidence, log for review
         │
         ▼
PATCH FAMILY JSONs (source of truth)
- Walk taxonomy/<kingdom>/.../src/data/*.json
- For each species: lookup in consolidated mapping
- Build authorityIds = "gbif:123,wikidata:Q456,col:789"
- Write back (atomic, with backup)
         │
         ▼
REBUILD
sh scripts/buildData.sh && make species-parquet
```

## Implementation Order

1. `scripts/buildIdMap.py` — builds `species_id_map` from current sources (GBIF cache + wiki-images)
2. `scripts/patchFamilyIds.py` — applies consolidated mapping to family JSONs
3. `make idmap` and `make patch-ids` targets in Makefile
4. Later: plug in COL/ITIS/WoRMS/WFO as new extractors writing to same `species_id_map`

## Sources

| Source | Records | Key Field | Match Strategy | Coverage |
|--------|---------|-----------|----------------|----------|
| GBIF cache (full) | ~17.5K species (141 classes) | nubKey / speciesKey | Exact scientific name | Animalia vertebrates, many fungi, some chromista |
| GBIF cache (minimal) | ~16K species (49 classes) | scientificName only | Exact name + genus fallback | Amphibia, Magnoliopsida, Gastropoda, etc. |
| wiki-images.json | 283K QIDs | qid | Exact scientific name | All kingdoms (Wikipedia-linked) |
| COL (future) | ~2M taxa | UUID (in LSID) | Exact name + authorship | Future |
| WoRMS (future) | ~500K marine | AphiaID | Exact name | Future |
| ITIS (future) | ~800K | TSN | Exact name | Future |
| WFO (future) | ~1.4M plants | WFO ID | Exact name | Future |

## Current Gap

2.7M species, only 15.7% have authorityIds (422k, mostly GBIF). Two rich sources exist:
- GBIF cache: speciesKey (nub key) per species per class
- wiki-images.json: 283k Wikidata QIDs

## UUIDs

UUID v5 (SHA-1 + namespace) from taxonomy path: `kingdom|phylum|class|order|family|genus|species|authorship`
Fixed namespace: `6ba7b810-9dad-11d1-80b4-00c04fd430c8`
Generated in buildData.ts during graft/compress, written back to source family JSONs.