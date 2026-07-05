# Phyla Gap Report — Kingdoms & Phyla With No Data

*Generated 2026-07-04*

Phyla we have zero data for: not in taxonomy, not scouted, no GBIF cache, no species.

---

## Entire kingdoms with no data at all

| Kingdom | Est. phyla | Notes |
|---------|:----------:|-------|
| **Fungi** | ~8–10 | Mushrooms, yeasts, molds. GBIF key 5. |
| **Chromista** | ~8–12 | Brown algae, diatoms, oomycetes. GBIF key 4. |
| **Protozoa** | ~10–15 | Amoebae, ciliates, flagellates. GBIF key 7. |
| **Bacteria** | ~30+ | Eubacteria (genuine bacteria). GBIF key 3. |
| **Archaea** | ~5–8 | Extremophiles. GBIF key 2. |
| **Viruses** | — | Non-cellular; not typically phylum-classified. GBIF key 8. |

Six entire kingdoms with ~70+ phyla — zero data across the board.

---

## Animalia — phyla missing from both taxonomy and scouts

| Phylum | GBIF key | Common name | Notes |
|--------|:--------:|-------------|-------|
| **Placozoa** | 76 | Placozoans | The simplest known animal; only ~3 described species (*Trichoplax adhaerens*). Not scouted. |

Of ~33 recognized living animal phyla, only **Placozoa** is completely absent.

---

## Animalia — phyla scouted but not integrated into taxonomy

| Phylum | GBIF key | Common name |
|--------|:--------:|-------------|
| Entoprocta | 8173593 | Goblet worms |
| Gastrotricha | 22 | Hairy-bellied worms |
| Gnathostomulida | 77 | Jaw worms |
| Loricifera | 7457457 | Brush heads |
| Onychophora | 62 | Velvet worms |
| Phoronida | 19 | Horseshoe worms |
| Priapulida | 5963150 | Penis worms |
| Xenacoelomorpha | 7190138 | Xenacoelomorphs |

These 8 phyla have been scouted (GBIF tree files exist in `portal/data/gbif-scout-*.json`) but have no taxonomy entry, no family data, and no species in the portal.

---

## Animalia — phyla in taxonomy but not scouted

| Phylum | GBIF key | Common name |
|--------|:--------:|-------------|
| Arthropoda | 54 | Arthropods |
| Chordata | 44 | Chordates |
| Ctenophora | 51 | Comb jellies |
| Echinodermata | 50 | Echinoderms |
| Tardigrada | 14 | Tardigrades |

These 5 phyla exist in `taxonomy.json` and thus appear in the portal tree, but have no GBIF scout file (the tree data comes from other sources).

---

## Animalia — phyla with data (23 in taxonomy + 8 scouted)

For the complete list of 31 covered animal phyla, see [`docs/kingdoms-phyla-report.md`](kingdoms-phyla-report.md).

---

## Plantae — scouted, no taxonomy entry

7 phyla scouted (GBIF trees exist) but not added to `taxonomy.json`.

| Phylum | GBIF key | Common name |
|--------|:--------:|-------------|
| Anthocerotophyta | 13 | Hornworts |
| Bryophyta | 35 | Mosses |
| Charophyta | 7819616 | Stoneworts |
| Chlorophyta | 36 | Green algae |
| Marchantiophyta | 9 | Liverworts |
| Rhodophyta | 106 | Red algae |
| Tracheophyta | 7707728 | Vascular plants |

Currently being set up — GBIF caches downloading, Wikipedia SQLite DB building.

---

## Summary

| Category | Count |
|----------|:-----:|
| Kingdoms with zero data | **6** (Fungi, Chromista, Protozoa, Bacteria, Archaea, Viruses) |
| Kingdom Plantae — scouted, not integrated | **7** phyla |
| Animalia phyla — missing entirely | **1** (Placozoa) |
| Animalia phyla — scouted, not integrated | **8** phyla |
| Animalia phyla — in taxonomy, not scouted | **5** phyla |
| Animalia phyla — in taxonomy or scouted | **31** phyla |
| **Total phyla with zero portal data** | **~70–80+** (6 kingdoms × their phyla) |
