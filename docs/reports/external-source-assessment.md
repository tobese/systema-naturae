# External source assessment — EOL / Zenodo harvests

Assessment of ten Zenodo records supplied for evaluation, measured against the
current tree (1,205,750 species; 1,089,091 missing a common name; 1,047,687
missing continents).

All are **EOL harvests republished as Darwin Core Archives**. That framing
matters: the EOL harvester normalises whatever the upstream project publishes,
and it does not filter by licence. So the licence has to be read per record.

---

## Summary

| Record | Source | Size | Verdict |
|---|---|---|---|
| [20174554](https://zenodo.org/records/20174554) | NMNH Smithsonian | 40 MB | **Applied — 5,628 CC0 images** |
| [17509532](https://zenodo.org/records/17509532) | Wikimedia Commons | 488 MB | **Applied — 29,447 portraits, credited** |
| [22129810](https://zenodo.org/records/22129810) | EOL TraitBank (CSV) | 592 MB | Structured traits only, **not prose** |
| [22927080](https://zenodo.org/records/22927080) | EOL TraitBank (Neo4j) | 15 GB | Skip — same data, needs Java 21 |
| [20646743](https://zenodo.org/records/20646743) | USDA PLANTS | 31 MB | Maybe — 2,657 range records, needs URI resolution |
| [22739608](https://zenodo.org/records/22739608) | FishBase | 37 MB | Low — only 28 marginal common names |
| [21123026](https://zenodo.org/records/21123026) | BioImages UK | 5 MB | **Blocked** — CC BY-NC-SA |
| [20272755](https://zenodo.org/records/20272755) | Flickr EOL group | 40 MB | Mostly blocked — only 9,703 taxa free |
| [19027382](https://zenodo.org/records/19027382) | AntWeb | 27 MB | Blocked — CC BY-NC-SA; text is AntCat citations |
| [15597434](https://zenodo.org/records/15597434) | CalPhotos Moorea | 1 MB | **Blocked** — CC BY-NC-SA |

**The pattern:** of ten image sources, seven are non-commercial. The EOL harvester
does not filter for `NC`, so most of what it republishes cannot go into a public
portal. Two sources are genuinely open, and one of those (NMNH) is the best
image find of the project.

---

## 1. NMNH Smithsonian — the win

270,000+ type specimen records from Botany, Entomology, Invertebrate Zoology and
Vertebrate Zoology. CC-BY 4.0 at the record level; every media row is **CC0**
(`creativecommons.org/publicdomain/zero/1.0/`).

- **453,486** media rows, **65,046** taxa
- **every** row has an `accessURI` — no dead links in the table
- `Owner` is empty on all rows, which is fine under CC0: attribution is waived

Measured against the tree:

```
65,046  of our species have an NMNH image
32     we already had one
5,628  GENUINELY NEW
```

A 99.95% miss rate on our side — we simply did not have this. Concentrated in
the groups a museum actually holds type material for: insects, molluscs,
fungi, plants.

URLs redirect to `ids.si.edu/ids/deliveryService/id/ark:/65665/...` and resolve.

**Recommendation: apply.** Cheapest, cleanest, largest single win on the board.

## 2. Wikimedia Commons — mostly already ours

1,574,122 media rows, 34,724 of our species matched.

- **32,083 already have an image** — because our existing images come from
  Wikidata P18, which resolves to a Commons file
- **29,447 applied** — see the correction below; the naive figure was 2,641

Licences on matched rows are excellent: BY-SA 258,290 / BY 156,514 /
public domain 59,588, with only 50 NC rows.

So the direct answer to "do we already have this?" is **largely yes for the
images**: 32,083 of the matched species already had a portrait, because Wikidata
P18 resolves to a Commons file.

What the first measurement got wrong was the *matching*. It compared raw
names, so the 156,392 species carrying an authorship missed entirely. Joining on
the canonical form lifts the yield from 2,641 to **29,447** — see `16f88ede9`. The more interesting use is
replacing our 32,892 runtime `commonsCat` scrapes in `ImageTabs` with concrete
file URLs, which is a robustness win rather than a coverage win.

## 3. TraitBank — structured, and that is the whole problem

11,394,558 trait rows over 2,516,119 distinct species, each row carrying
`scientific_name` as a join key.

Coverage of our undescribed species is **39,788 (5.33%)** — the highest yield of
anything measured — and fungi are the best at **11.60%**.

But the values are ontology URIs:

```
lichenostigma subradians   EcomorphologicalGuild   .../terms/lichenicole
corollospora portsaidica   RO_0002303 (habitat)    .../ENVO_00000447
hypotrachyna palmarum     FLOPO_0900032           .../PATO_0000402
```

`RO_0002303` alone is 682,293 rows, and only **571** of its values exceed 40
characters. So "39,788 species covered" means *39,788 species with an
ontology-coded classification*. Writing `ENVO_00000446` into a description field
is the GBIF media-caption mistake in a new costume.

**Not a description source.** The genuinely useful part is three predicates that
map onto things we already track:

| predicate | rows | maps to |
|---|---|---|
| `NativeRange` / `IntroducedRange` / `InvasiveRange` | 213,722 + 88,135 + 12 | `continents`, **native vs introduced** |
| `ConservationStatus` | 157,853 | `iucnStatus` |
| `ExtinctionStatus` / `population_trend` | 89,217 + 107,116 | `extinct` (today only detected from `†` or the word "extinct") |

Native-versus-introduced is a real modelling gap and these are coded to a
controlled vocabulary — unlike the GBIF `locality` free text that failed
comparison. It is a **feature, not a backfill**: `nativeContinents` /
`introducedContinents` is a schema decision worth making deliberately.

Note `22927080` is the same content as `22129810` in a 15 GB Neo4j dump needing
Java 21 and a Neo4j server. Use the CSV.

## 4. USDA PLANTS — real, but needs a resolution step

580,161 measurement rows over 64 predicates. `PlantHabit` 46,571,
`NativeRange` 43,352, `IntroducedRange` 13,442.

- **2,657** `NativeRange` and **323** `IntroducedRange` records fill a continent gap

But the values are identifiers, not text:

```
Acer leucoderme Small      http://www.wikidata.org/entity/Q578170
Actaea pachypoda Elliott   http://www.geonames.org/6251999
```

Wikidata QIDs and GeoNames IDs. Usable, but only after resolving them, and
`Q578170` alone covers a large share so the effective geographic resolution is
coarse. `PlantHabit` is URI-valued and yielded nothing usable.

The description said "species abstracts" — there are none in this archive.

## 5. FishBase — already covered by GBIF

101,630 taxa, 175,357 measurement rows (mostly standard length), 19,172 English
vernacular names.

**2,438** of our species have an English name in FishBase, and only **28** of
those are a gap for us — a 1.1% marginal yield. GBIF's VernacularName table
already covers fish common names, which is the lesson from the 23,171 we applied
in `23dd3876b`. FishBase has no `NativeRange` predicate at all. Its images are
110,812/111,348 CC BY-NC.

## 6. The blocked sources

**BioImages (UK), CalPhotos (Moorea), AntWeb** are all uniformly
**CC BY-NC-SA**, every row, no exceptions. NC forbids commercial redistribution
and this is a public portal.

AntWeb additionally looks promising and isn't: 140,143 media rows all carry a
`description`, but the median is 81 characters —
`Closeup profile view of Specimen CASENT0191633 from AntWeb.` — a caption. The
17,042 longer ones are textmined **AntCat catalogue citations** (original
combination, page number, country, biogeographic region), not prose.

**Flickr EOL group** is 77,404 taxa of which only **9,703** are free of NC/ND.
The group exists to collect images "licensed for non-commercial reuse", so this
is by design.

> Correction to something said earlier in this investigation: BioImages was
> described as CC BY on first inspection. That was wrong — it was a truncated
> string. It is `by-nc-sa/3.0` on all 132,528 rows.

---

## Two bugs found while measuring this

Neither is caused by these sources; both were exposed by them.

### A. The English filter does not filter

`scripts/enrichCommonNamesFromGbif.py:94`

```python
ENGLISH = {"en", "eng", ""}
```

The empty string is treated as English. GBIF's `VernacularName` table has many
rows with a blank `language`, and those rows carry vernacular names in *any*
script. So the filter passed Chinese, Japanese and Korean names straight
through.

`23dd3876b` added 23,171 common names of which **2,180 (9.4%) are non-Latin
script** — `沙条`, `巴布亚长尾须鲨`, `項斑長尾鬚鯊`, `청가시덩굴`, `밀나물`.
These are in the tree now, on sharks and rays mostly.

**Fix:** drop `""` from `ENGLISH`, and reject any value matching
`[\u0400-\u04FF\u0590-\u05FF\u0600-\u06FF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]`
as a belt-and-braces script check. Then repair the 2,180.

### B. 156,392 names carry an authorship, and nothing matches them

**156,392 species names (13% of the tree) store the authorship inside `name`** —
`Smilax walteri Pursh`, `Majanthemophyllum pusillum Heer, 1883`. Concentrated in
gastropoda (39,898), bivalvia (14,407), chromadorea (12,374), anthozoa (10,549).

The GBIF parse index already handles this perfectly — 562,378 entries carry an
authorship and **100% parse cleanly** into `canonical` + `authorship`.

But the enrichers do not use it:

- `scripts/enrichCommonNamesFromGbif.py:170` builds the index from GBIF
  **canonical** names
- `scripts/enrichCommonNamesFromGbif.py:236` looks it up with our **raw**
  stored name

So every authorship-carrying species silently misses. Re-running the match with
a canonical fallback recovers:

| field | currently missing | recoverable | share of gap |
|---|---|---|---|
| common names | 1,089,091 | **20,900** | 1.92% |
| continents | 1,047,687 | **69,159** | 6.60% |

Both were applied (`af5669043`). The common-name figure was overstated when
first measured: it counted the non-English entries that the same commit's filter
removed, so the honest number is **20,900** rather than 26,875. That commit also
fixed the language filter itself, which had been writing Chinese, Japanese and
Korean names into the tree as English ones.

---

## Recommended order

1. ~~**Fix the `ENGLISH` filter** and repair the bad names.~~ Done — 1,262
   descriptions were not in English; 1,185 cleared in `402818552` and 77 more in
   `8c007a03c`, with a `NON_ENGLISH_DESCRIPTION` check so it cannot recur.
2. ~~**Fix the canonical-name key** in both GBIF enrichers, then re-run.~~ Done
   — `af5669043`, +20,900 common names and +69,159 continents.
3. ~~**Apply NMNH**~~ Done — 5,628 CC0 images, `c1b84d439`.
4. ~~**Apply Commons**~~ Done — 29,447 portraits with author and licence,
   `16f88ede9`.
5. Still open: decide on `nativeContinents` / `introducedContinents` as a schema
   change, then take TraitBank `NativeRange` (213,722 rows) and USDA range
   (2,657, though its values are Wikidata QIDs and GeoNames IDs needing
   resolution). Neither has been written.
6. BioImages, CalPhotos, AntWeb and the Flickr group remain unused, all NC.

Downloads are unpacked under `/Volumes/MacieExternal/tmp/opencode/`.

Two things in this report were wrong when written and are corrected above: the
recoverable common-name count (26,875 → 20,900, inflated by the non-English
entries) and the Commons yield (2,641 → 29,447, understated because the first
pass matched names without canonicalising).
