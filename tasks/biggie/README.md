# Biggie — Task Runner

**Host:** `Biggie.local` (IP TBD)
**OS:** Windows 10
**User:** TBD
**Specs:** 32G RAM + 3G GPU
**Ollama:** `qwen2.5:7b` or `llama3.2` (pull if not present)

## Setup

```powershell
# Clone repo (if not already done)
git clone https://github.com/anomalyco/systema-naturae.git
cd systema-naturae

# Install Node.js dependencies
cd portal && npm install && cd ..

# Pull Ollama model
ollama pull qwen2.5:7b
# Or if 3G GPU is tight:
# ollama pull llama3.2
```

## Tasks

### 1. Rebuild Insecta GBIF Cache

The current Insecta cache is stale. This will download all insect species from GBIF (~1M+ species):

```powershell
cd portal
npx tsx scripts/cacheGbifData.ts Insecta
```

**Expected output:** `data/gbif-cache-insecta.json` (~200-500MB) with all insect families. Takes 30-60 minutes due to GBIF rate limits.

### 2. Insect Wikipedia Coverage Scan

Scan remaining 4 families that returned 0% coverage (likely API errors):

```powershell
cd portal
npx tsx scripts/scanInsectWikipediaCoverage.ts
```

**Families to re-scan:** `nymphalidae`, `libellulidae`, `carabidae`, `chrysomelidae`

**Expected output:** `data/insect-wikipedia-coverage.json` with coverage percentages.

### 3. Optional: Wikipedia Import for High-Coverage Families

After scan completes, if any family shows >15% Wikipedia coverage:

```powershell
# Example for apidae (9.8% coverage, ~640 wiki species)
cd portal
npx tsx scripts/importPapilionidaeWikipedia.ts  # adapt script for other families
```

### 4. Commit & Push

After tasks complete:

```powershell
cd ..\..
git status
git add .
git commit -m "feat: rebuild Insecta GBIF cache + Wikipedia coverage scan"
git push
```

## Notes

- 32GB RAM is ample for large cache files and scans
- 3G GPU may be tight for 7B models — use `llama3.2` (smaller) if Ollama runs out of VRAM
- GBIF API has rate limits — expect 250ms+ between requests
- Insecta cache rebuild may take 30-60 minutes
