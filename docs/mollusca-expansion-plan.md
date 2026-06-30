# Mollusca Expansion Plan

**Goal:** Add all major mollusk classes beyond Cephalopoda to the portal.

**Current state:** Cephalopoda only (8 families, ~800 spp).
**Target state:** 7 classes, ~1,219 families, ~92,000+ species.

## Pipeline

For each class:
1. `cacheGbifData.ts` — cache GBIF species data (fast bulk import)
2. `bootstrapClass.ts` — scaffold directory + data files
3. `fetchSpeciesFromApi.ts` — import species (GBIF + Wikipedia)
4. `enrichFromWikipedia.ts` — enrich with Wikipedia descriptions (SQLite)
5. Register in `taxonomy.json`, `colorRegistry.ts`
6. `buildData.sh` + gap reports

## Phases

### Phase 1 — small classes (prove pipeline)
| Class | Orders | Families | Est. species | Complexity |
|---|---|---|---|---|
| Caudofoveata | 1 | 3 | ~100 | Tiny — warm-up |
| Monoplacophora | 3 | 5 | ~30 | Tiny |
| Scaphopoda | 2 | 15 | ~500 | Small |
| Polyplacophora | 4 | 39 | ~1,000 | Small |
| **Subtotal** | **10** | **62** | **~1,630** | |

### Phase 2 — Bivalvia
| Class | Orders | Families | Est. species | Complexity |
|---|---|---|---|---|
| Bivalvia | 27 | 339 | ~20,000 | Large |
| **Subtotal** | **27** | **339** | **~20,000** | |

### Phase 3 — expand Cephalopoda
| Class | Orders | Families | Est. species | Notes |
|---|---|---|---|---|
| Cephalopoda | 13 | 184 | ~800 | Currently 8 families, expand to cover all |
| **Subtotal** | **13** | **184** | **~800** | |

### Phase 4 — Gastropoda (major effort)
| Class | Orders | Families | Est. species | Complexity |
|---|---|---|---|---|
| Gastropoda | 23 | 634 | ~70,000 | Massive — split by order |
| **Subtotal** | **23** | **634** | **~70,000** | |

## Totals

| | Families | Species |
|---|---|---|
| New | 1,219 | ~92,000 |
| Current portal | 1,114 | ~180,000 |
| **Total** | **2,333** | **~272,000** |

## Excluded (fossil-only)

- Rostroconchia (5 families, all extinct)
- Cricoconarida (11 families, all extinct)
- Solenogastres (0 orders/families from GBIF — need manual treatment)

## Tracking

Tracked via progressd session `mollusca-expansion-2026-06-30`.
Web UI: http://127.0.0.1:9876/
