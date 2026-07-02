# Biggie — Task Runner

**Host:** `Biggie.local` / Tailscale `100.95.246.65`
**OS:** Windows 10
**User:** TBD
**Specs:** 32G RAM + 3G GPU
**Ollama:** `qwen2.5-coder:3b` (import path), `qwen3.6:latest`

## Setup

```powershell
# Clone repo (if not already done)
git clone https://github.com/anomalyco/systema-naturae.git
cd systema-naturae

# Install Node.js dependencies
cd portal && npm install && cd ..

# Biggie currently serves qwen2.5-coder:3b and qwen3.6:latest
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
- For importer calls, use `OLLAMA_NUM_GPU=0` against Biggie if needed
- GBIF API has rate limits — expect 250ms+ between requests
- Insecta cache rebuild may take 30-60 minutes
