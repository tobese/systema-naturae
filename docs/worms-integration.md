# WoRMS integration — filling the empty marine/fossil families

**Status:** proposed (not yet implemented)
**Candidate list:** [`portal/data/worms-candidates.json`](../portal/data/worms-candidates.json) — 758 families
**Author context:** written after GBIF re-fetch and offline-Wikipedia scans both failed to populate these families.

---

## TL;DR

758 Animalia families are scaffolded (they have an `appSlug`, a color theme, and an empty
data file) but hold **0 species**, and their `speciesCount` is `0`. This is **correct**, not a
bug — the two sources the portal already uses cannot supply their species:

- **GBIF backbone** returns 0 accepted species under these family keys (≈2% of a 50-family
  sample had *any* species, and those had 1 each).
- **Offline Wikipedia dump** yields 13 reliably-attributable species across 4 families
  (category-tagged); the higher "mentions" count (366) is unusable — it mislabels plants and
  passing references.

These families are almost entirely **marine invertebrates** and **fossil groups**, which is
exactly the domain of **WoRMS** (World Register of Marine Species). WoRMS is the realistic
path to real completeness for this tail.

---

## Why GBIF and Wikipedia came up empty

| Source | Result | Reason |
|---|---|---|
| GBIF `higherTaxonKey` species search | ~15 species total across 743 families | These families are fossil, monotypic, or **synonymized** in the GBIF backbone — the species are classified under other (valid) family names, so nothing sits under the empty family's key. |
| Wikipedia dump — `[[Category:Xidae]]` | 13 species / 4 families | Most species aren't in Wikipedia; those that are use auto-taxobox templates, so the family isn't stored in the page wikitext. |
| Wikipedia dump — family name in prose | 366 species / 40 families **(rejected)** | Name collisions (e.g. *Caryophyllidae* is also a plant subclass) and contrastive mentions ("differs from family X") produce heavy false positives. |

The emptiness is therefore a *taxonomic* fact: many of these are junior synonyms or extinct
families whose species legitimately live elsewhere (or nowhere in these datasets).

---

## What WoRMS could fill

WoRMS (and its constituent databases — MolluscaBase, World Porifera Database, World List of
Bryozoa, World Polychaeta Database, etc.) authoritatively covers the marine invertebrate
phyla that dominate this list:

| Phylum | Empty families | WoRMS coverage |
|---|---:|---|
| Mollusca | 263 | Excellent (MolluscaBase — marine + non-marine) |
| Cnidaria | 131 | Core (corals, hydroids, jellyfish) |
| Brachiopoda | 125 | Extant: good. **Fossil families: use PBDB instead** |
| Platyhelminthes | 68 | Partial (marine turbellarians / flukes) |
| Nematoda | 40 | Partial (marine — NeMys) |
| Annelida | 39 | Strong (World Polychaeta Database) |
| Porifera | 34 | Core (World Porifera Database) |
| Bryozoa | 28 | Core (World List of Bryozoa) |
| Xenacoelomorpha | 10 | Good (marine) |
| Hemichordata | 6 | Good |
| Nemertea | 4 | Good |
| Chaetognatha | 3 | Good |
| Gnathostomulida | 2 | Good |
| Acanthocephala | 2 | Partial |
| Loricifera · Priapulida · Rotifera | 1 each | Good (meiofauna) |

**Caveat — fossils:** a large share of the Brachiopoda families (and some Mollusca/Cnidaria)
are extinct. WoRMS is extant-focused; those need the **Paleobiology Database (PBDB)**
(`paleobiodb.org`) instead. Expect WoRMS to resolve the extant tail and PBDB the fossil tail.

---

## WoRMS REST API (no key required; be polite — throttle)

Base URL: `https://www.marinespecies.org/rest`

| Need | Endpoint |
|---|---|
| AphiaID for a family name | `GET /AphiaIDByName/{name}?marine_only=false` |
| Full record | `GET /AphiaRecordsByAphiaID/{aphiaID}` |
| Children (genera under a family, species under a genus) | `GET /AphiaChildrenByAphiaID/{aphiaID}?marine_only=false&offset=1` |
| Records by name (fuzzy/exact) | `GET /AphiaRecordsByName/{name}?like=false&marine_only=false` |

Paging: `AphiaChildrenByAphiaID` returns up to 50 per call; page with `offset` (1-based) until
an empty array. Filter results to `rank == "Species"` and `status == "accepted"` (also decide
whether to keep `taxonomicStatus` unaccepted/alternate representations — usually skip).

### Suggested fetch flow (mirrors `scripts/importInsectScaffolds.py`)

```
for each family in worms-candidates.json:
    aphiaID = GET /AphiaIDByName/{family.family}          # skip if 404 / -999
    genera  = AphiaChildrenByAphiaID(aphiaID)  where rank == Genus
    for each genus:
        species = AphiaChildrenByAphiaID(genus.AphiaID)  where rank == Species, status == accepted
    build genus->species tree (species kept minimal so buildData compresses to speciesList)
    write <class>/<order>/<appSlug>/src/data/<appSlug>.json   # overwrite the empty stub
    set node.speciesCount in taxonomy.json = fetched count
    # appSlug + color theme already exist — no colorRegistry change needed
```

Reuse conventions from the beetle import (`scripts/importInsectScaffolds.py`):
- Species node: `{ id, name, rank:"SPECIES", lineage:<genus>, subspeciesCount:0, sourcedFrom:"worms" }`
  (no `description` → `buildData.ts` compresses into `speciesList[]`).
- Genus node: `{ id:"GENUS_<UPPER>", name, rank:"GENUS", lineage, description, children }`.
- Add `"sourcedFrom": "worms"` so the OptionsPanel highlight toggle can distinguish WoRMS data.
- Store the AphiaID (e.g. on the family node or a sidecar) for reproducible re-fetches.

### Rate limiting / etiquette
WoRMS is a shared academic service. Throttle to a few requests/second, cache responses to a
`portal/data/worms-cache-<phylum>.json` (mirroring the GBIF caches), and make the importer
resumable (skip families whose data file already has species).

---

## After import — standard pipeline

```bash
cd portal && sh scripts/buildData.sh          # graft + compress
npm run typecheck
npx tsx scripts/findGaps.ts
npx tsx scripts/reportPhyla.ts
npx tsx scripts/generateGapTasks.ts
python3 ../scripts/deep-scan.py               # structural: both ways, 0 orphans
python3 ../scripts/round7-audit.py            # cross-kingdom
npx tsx scripts/testDataContract.ts           # refresh snapshot baselines for new counts
```

---

## Current state (this pass)

- All 758 candidate families are confirmed `speciesCount: 0` in `taxonomy.json` — accurate,
  since no data source the portal uses can populate them.
- `portal/data/worms-candidates.json` lists every candidate with `family`, `appSlug`,
  `class`, `phylum`, and `gbifFamilyKey` (present for 743; useful as a name/lineage anchor).
- No WoRMS fetching has been implemented yet — this document is the plan of record.
