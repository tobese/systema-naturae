# Steamie — Task Runner

**Host:** `Steamie.local` (192.168.0.171)
**OS:** Windows 11
**User:** `opencode`
**Specs:** 16G RAM + 6G GPU
**Ollama:** `qwen2.5:7b` (pull if not present)

## Setup

```powershell
# Clone repo (if not already done)
git clone https://github.com/anomalyco/systema-naturae.git
cd systema-naturae

# Install Node.js dependencies
cd portal && npm install && cd ..

# Pull Ollama model (6GB GPU can handle 7B)
ollama pull qwen2.5:7b
```

## Tasks

### 1. Ollama Gap Filling (10 families, 347 species)

Run each family through `importFamily.ts` using the larger model:

```powershell
cd portal

# Run all 10 gap families
$FAMILIES = "dendrobatidae","pelobatidae","echinidae","sepiidae","colubridae","scincidae","chamaeleonidae","lacertidae","eublepharidae","grallariidae"
foreach ($f in $FAMILIES) {
    Write-Host "=== Importing $f ===" -ForegroundColor Cyan
    $env:OLLAMA_MODEL = "qwen2.5:7b"
    $env:OLLAMA_HOST = "localhost"
    npx tsx scripts/importFamily.ts $f
}
```

**Expected output:** Each family's `src/data/<family>.json` gets updated with new species, `taxonomy.json` speciesCount increases, `unified-taxonomy.json` rebuilds.

### 2. Re-fetch Cyprinidae (if Macie fix didn't work)

```powershell
cd portal
$env:NO_WIKI = "1"
npx tsx scripts/fetchSpeciesFromApi.ts cyprinidae
```

**Expected:** ~3,824 species (GBIF key 7336). Script auto-updates taxonomy and rebuilds.

### 3. Commit & Push

After all tasks complete:

```powershell
cd ..\..
git status
git add .
git commit -m "feat: Ollama gap-fill session — 10 families, ~347 species via qwen2.5:7b"
git push
```

## Notes

- `importFamily.ts` uses Ollama to generate species descriptions for gaps between existing data and GBIF total
- The 7B model can handle prompts with existing genus structures (3B model failed)
- Each family takes ~5-15 minutes depending on gap size
- Total estimated time: 1-2 hours for all 10 families
