# Import Workflow and Scripts

This document details the tools, cache files, and procedures used to import, enrich, and maintain species taxonomy data inside the Systema Naturae portal.

---

## Import Tools

### 1. `fetchSpeciesFromApi.ts` — Authoritative GBIF Data + Wikipedia Enrichment
Downloads authoritative, real-world species data from GBIF's taxonomic database, then enriches them with Wikipedia descriptions, common names, and geographical ranges.

**Usage:**
```bash
# Run from portal folder
npx tsx scripts/fetchSpeciesFromApi.ts <slug> [limit]
```
- **Description:** Scans GBIF, downloads species, fetches matching Wikipedia REST API entries, and writes the output directly to `<class>/<order>/<appSlug>/src/data/<appSlug>.json`.
- **Note:** Automatically updates the `speciesCount` in `taxonomy.json` to match GBIF's count.

---

### 2. `importFamily.ts` — LLM-Based Gap Filling
Uses local Ollama models to intelligently generate descriptions and missing species for gaps between currently imported portal data and real-world GBIF totals.

**Usage:**
```bash
# Run from portal folder
OLLAMA_MODEL="qwen2.5:7b" npx tsx scripts/importFamily.ts <slug> [count]
```
- **Recommended Model:** `qwen2.5:7b` (or `llama3.2` as a smaller fallback). The `qwen2.5:3b` model is too small to handle families with complex existing genus structures.
- **Environment Variables:**
  - `OLLAMA_HOST`: Set to point to external GPU rigs (e.g., `Steamie.local` or `Biggie.local`) if local resources are constrained.
  - `OLLAMA_MODEL`: Specifies the target LLM.

---

## Cache Management

To avoid rate-limiting and accelerate taxonomic resolution during imports, classes are cached locally under `portal/data/`:

| Class/Phylum Cache | Purpose / Generation Command |
|---|---|
| `gbif-cache-aves.json.gz` | Birds Cache |
| `gbif-cache-mammalia.json.gz` | Mammals Cache |
| `gbif-cache-reptilia.json.gz` | Reptiles Cache |
| `gbif-cache-amphibia.json.gz` | Amphibians Cache |
| `gbif-cache-insecta.json.gz` | Insects Cache |
| `gbif-cache-arachnida.json.gz` | Arachnids Cache |
| `gbif-cache-actinopterygii.json.gz` | Ray-finned Fish Cache |

**To rebuild or generate a class cache:**
```bash
cd portal
npx tsx scripts/cacheGbifData.ts <ClassName>
```

---

## Secondary Helpers

- **`enrichFromWikipedia.ts`**: Batch enriches existing database species with Wikipedia descriptions/data in a throttled, rate-limit safe loop.
- **`scanInsectWikipediaCoverage.ts`**: Scans multiple insect families to determine their Wikipedia REST API coverage density before starting an import.
