# Coverage & Import status

## Current portal state
- **20,330 nodes** in unified taxonomy
- **351 families** across all phyla
- **254/254 IOC bird families** represented (100%)
- **All bird gaps filled** with real data from GBIF + Wikipedia
- **106 species** with Wikipedia-enriched descriptions, **8,581** with generated descriptions
- **GBIF caches**: Aves (95MB), Mammalia (96MB), Reptilia (459MB), Amphibia (37MB), Elasmobranchii (13MB), Asteroidea (7MB), Echinoidea (10MB), Holothuroidea (6MB)
- **Cache still needed**: Actinopterygii, Arachnida, Insecta (run `make cache-gbif`)

## Import tools

### `fetchSpeciesFromApi.ts` — authoritative data from GBIF + Wikipedia
```
npm run fetch <slug> [limit]
make fetch ARGS="<slug> [limit]"
```
Downloads real species data from GBIF's taxonomic database, then enriches with Wikipedia descriptions and common names. Updates `speciesCount` in taxonomy.json to match GBIF's count.

### `importFamily.ts` — LLM-based gap filling (fallback)
```
npm run import <slug> [count]
make import ARGS="<slug> [count]"
```
Uses local Ollama to generate missing species. Set `OLLAMA_MODEL` env var: `qwen2.5:3b` (default), `qwen2.5:7b`, `llama3.2:3b`. Warns if new lineages need colorRegistry entries.

## Remaining monster families (documented gaps)
The following are the largest bird families with speciesCounts of 85–383.
All major genera are represented with 30–120 species each.
Full manual curation to the listed total is impractical:

| Family | Have | Listed | Gap |
|---|---|---|---|
| tyrannidae | 54 | 437 | 383 |
| thraupidae | 55 | 384 | 329 |
| trochilidae | 66 | 360 | 294 |
| furnariidae | 50 | 315 | 265 |
| columbidae | 120 | 344 | 224 |
| muscicapidae | 105 | 324 | 219 |
| thamnophilidae | 41 | 250 | 209 |
| psittaculidae | 44 | 200 | 156 |
| meliphagidae | 44 | 190 | 146 |
| pycnonotidae | 50 | 160 | 110 |
| cisticolidae | 55 | 160 | 105 |
| nectariniidae | 47 | 145 | 98 |
| strigidae | 133 | 230 | 97 |
| picidae | 150 | 240 | 90 |
| accipitridae | 175 | 260 | 85 |
