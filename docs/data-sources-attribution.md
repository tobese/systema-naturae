# Data Sources — Attribution & Licensing

Last gathered: **2026-10-02**. Companion registry: [`data-sources.md`](data-sources.md).

This project reuses **text descriptions**, **names**, **distribution data** and
**images** from external biodiversity databases. Each species node records its
provenance in `sourcedFrom`; images carry their own fields in
`shared/data/wiki-images.json` (`image`, `imageUrl`, `imageArtist`,
`imageLicense`), because they are a runtime sidecar rather than part of the built
tree. This doc lists every source we pull from, its licence, and the attribution
we owe. **Read the "Licensing risk" section before publishing.**

What changed on 2026-10-02: nine Species File checklists were imported --
Orthoptera (28,081 species) and eight further orders totalling 12,522 species, all
CC BY 4.0, each with its own row below because each is a separately citable
dataset;  35,035 portraits were added from Smithsonian NMNH and
Wikimedia Commons; and 184,542 images gained an author and a licence that they
previously did not have. None of that was covered by the previous gathering.

> Note: licences below were read from each source's official terms/FAQ/footer on
> 2026-07-06. Where a source has no formal licence page (footer/FAQ only) it is
> flagged. Nothing here is legal advice.

---

## Sources currently in the data (`sourcedFrom` values)

| `sourcedFrom` | Source | Licence | Attribution | Species (plants) |
|---|---|---|---|---|
| `wikipedia` | Wikipedia article text | **CC BY-SA 4.0** (share-alike) | Required | 125,504 |
| `gbif` | GBIF species descriptions & vernacular | Per-dataset: CC0 / CC BY / CC BY-NC | Required (BY/BY-NC) | 200,677 |
| `powo` | Plants of the World Online (RBG Kew) | **CC BY** | Required | 208,513 |
| `orthoptera species file` | **Orthoptera Species File** (GBIF `af66d4cf-…`, DOI 10.15468/nn7jhc) | **CC BY 4.0** | Required | 35,761 |
| `plecoptera species file` | **Plecoptera Species File (stoneflies)** | **CC BY 4.0** | Required | 3,910 |
| `phasmida species file` | **Phasmida Species File (stick insects)** | **CC BY 4.0** | Required | 3,286 |
| `mantodea species file` | **Mantodea Species File (mantises)** | **CC BY 4.0** | Required | 2,510 |
| `dermaptera species file` | **Dermaptera Species File (earwigs)** | **CC BY 4.0** | Required | 1,923 |
| `grylloblattodea species file` | **Grylloblattodea Species File (rock crawlers)** | **CC BY 4.0** | Required | 545 |
| `chrysididae species file` | **Chrysididae Species File (cuckoo wasps)** | **CC BY 4.0** | Required | 197 |
| `coleorrhyncha species file` | **Coleorrhyncha Species File (twisted-wing parasites)** | **CC BY 4.0** | Required | 99 |
| `zoraptera species file` | **Zoraptera Species File (angel insects)** | **CC BY 4.0** | Required | 52 |
| `generated` | Template-generated from lineage | ours | n/a | 832 |
| `nzpcn` | NZ Plant Conservation Network | **Permission-based** (no CC) | Required | 1 (test shot) |
| `websearch` | Mixed (see below) | **Mixed / some non-open** | Required | 58 |
| *(none)* | no provenance recorded | — | — | 669,002 |

The `gbif` figure is the number of nodes tagged `gbif`, not the number of distinct
datasets behind them — **no per-dataset DOI is stored**, so the licence of any
individual record cannot be stated. That is the single largest attribution gap and
it is not fixable retrospectively without re-deriving provenance from the family
files.

The `websearch` tier (46 species) drew from heterogeneous sources — some open,
some **not**. Per-source breakdown of what the research used:

| Source (websearch) | Licence | Reuse status |
|---|---|---|
| POWO, IPNI | CC BY | OK with attribution |
| IFPNI (fossil names) | CC BY 4.0 | OK with attribution |
| Atlas of Living Australia / Flora of Australia | CC BY 3.0 AU (per-dataset) | OK with attribution (check page) |
| World Flora Online | CC0 (backbone) / CC BY 4.0 | OK with attribution |
| Wikipedia | CC BY-SA 4.0 | OK, share-alike |
| Paleobiology Database | CC BY / CC0 (contradictory) | Attribute to be safe |
| **FloraBase (WA Herbarium)** | **All rights reserved; "fair use" forbids web reuse** | **Needs written permission** |
| **Flora of China (efloras)** | **All rights reserved** | **Needs permission** |
| **NZPCN** | **Permission-based** | **Needs acknowledgement/permission** |
| **SANBI Red List** | **© SANBI, no CC** | **Permission-based** |

---

## Required citations (per source)

**Orthoptera Species File** — CC BY 4.0; cite the dataset DOI:
> Orthoptera Species File (2026). OSF. Species File Group, University of
> Illinois. https://doi.org/10.15468/nn7jhc. Retrieved 2026-10-02.

**Smithsonian NMNH** — every media row is CC0, so no attribution is required. The
Zenodo record itself is CC BY 4.0 and worth citing anyway:
> Smithsonian National Museum of Natural History (2026). NMNH images from GBIF
> export. Zenodo. https://doi.org/10.5281/zenodo.20174554.

**Wikimedia Commons / Wikidata P18** — per-file licence, which the sidecar records
on each entry and the species panel prints as
`Wikimedia Commons · <author> · CC BY-SA 4.0`. For bulk reuse, cite:
> Wikimedia Commons contributors (2026). Files retrieved via the MediaWiki API.

**Wikipedia** — CC BY-SA 4.0, share-alike + attribution:
> Text from the Wikipedia article "[Title]" (https://en.wikipedia.org/wiki/[Title]),
> released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).

**GBIF** — cite by DOI; licence varies per dataset (a mixed pull inherits the most
restrictive terms; CC BY-NC can propagate):
> GBIF.org (YYYY) GBIF Occurrence/Species Download https://doi.org/[DOI]

**POWO (Plants of the World Online)** — CC BY; cite POWO + WCVP for names/distribution:
> POWO (2024). Plants of the World Online. Facilitated by the Royal Botanic
> Gardens, Kew. https://powo.science.kew.org/ Retrieved [date].
> Govaerts R (ed.). WCVP: World Checklist of Vascular Plants. RBG Kew.

**IPNI** — CC BY:
> IPNI (2026). International Plant Names Index. http://www.ipni.org — RBG Kew,
> Harvard University Herbaria & Libraries and Australian National Herbarium.

**IFPNI** — CC BY 4.0:
> IFPNI: The International Fossil Plant Names Index. https://www.ifpni.org [accessed date].

**Atlas of Living Australia / Flora of Australia** — CC BY 3.0 AU (per-dataset):
> Atlas of Living Australia. Species page: [URL]. Accessed [date].

**World Flora Online** — CC0 backbone / CC BY 4.0 content:
> WFO (2026): World Flora Online. http://www.worldfloraonline.org. Accessed [date].

**Paleobiology Database** — attribute to be safe:
> Data downloaded from the Paleobiology Database on [date].

**FloraBase (WA Herbarium, DBCA)** — text used with permission only:
> Descriptions by the Western Australian Herbarium, Department of Biodiversity,
> Conservation and Attractions. https://florabase.dbca.wa.gov.au/help/copyright.
> Accessed [date].

**Flora of China (eFloras)** — © MBG Press & Science Press; permission for reuse:
> Wu, Z.Y., P.H. Raven & D.Y. Hong (eds.). Flora of China. Science Press, Beijing
> & Missouri Botanical Garden Press, St. Louis. eFloras (2008). http://www.efloras.org.

**NZPCN** — reproduce the fact-sheet byline; acknowledge the Network:
> de Lange, P.J. (YYYY): [Taxon] Fact Sheet. New Zealand Plant Conservation
> Network. https://www.nzpcn.org.nz/flora/species/[slug]/

**SANBI Red List** — per-assessment citation including Red List version:
> [Author(s)]. [Year]. [Taxon]. National Assessment: Red List of South African
> Plants version [x]. Accessed [date].

---

## Licensing risk (action needed before publishing)

Most of our bulk data (`wikipedia`, `powo`, `gbif`, IPNI/IFPNI/ALA/WFO in
`websearch`) is **openly licensed** and only needs **attribution** (plus
**share-alike** for the Wikipedia-derived text).

However, four `websearch` sources are **not openly licensed** and their reused
text may require **written permission** or removal:

- **FloraBase** — *Philydrella drummondii*. Fair use explicitly excludes web
  reuse; needs permission or a rewrite from an open source.
- **Flora of China (eFloras)** — *Euptelea pleiosperma*, *Kingdonia uniflora*,
  *Petrosavia sinii*. All-rights-reserved.
- **NZPCN** — *Trithuria brevistyla*, *Tetrachondra hamiltonii*. Permission-based.
- **SANBI** — *Grubbia rourkei*, *Grubbia tomentosa*, *Mystropetalon thomii*.

Options for these ~8 species: (a) obtain permission, (b) rewrite the description
from an openly-licensed source (POWO/WFO/ALA), or (c) drop them back to gap.

**Recommendation:** because the `websearch` descriptions are our own concise
paraphrases (not verbatim copies) synthesised from facts, the copyright exposure
is lower than verbatim reuse — but facts + close paraphrase from all-rights-
reserved floras is still best re-grounded on an open source or permissioned. Track
the specific source per species (see the `websearch` provenance list) if we keep
them.

---

## Images and media (added 2026-10-02)

This section did not exist before the 2026-10-02 image work and covers an
attribution surface that is entirely new.

| Field in `shared/data/wiki-images.json` | Count | Meaning |
|---|---|---|
| `image` | 191,184 | Commons filename, rendered via `Special:FilePath` |
| `imageUrl` | 5,628 | absolute URL on a museum host (NMNH) |
| `imageArtist` | 184,542 | author of the image |
| `imageLicense` | 190,647 | licence URL, or short name where Commons gives none |
| `imageSource` | — | `nmnh` or `commons` |

What is satisfied today:

- **CC0 and public domain** — no attribution owed. This covers all 5,628 NMNH
  photographs and a large share of the Commons portraits.
- **CC BY / BY-SA** — author, licence and source are rendered in the species
  panel: `Wikimedia Commons · April Nobile · CC BY-SA 4.0`, with the licence
  linked. Where the author is unknown, the panel links the Commons `File:` page,
  which is where the author and licence can be read. Constructed from the
  filename, so all 191,184 portraits route to their attribution.
- **NC and ND** — refused at ingest. `applyCommonsImages.py` rejects them and the
  sidecar currently holds **zero**.

What is still missing:

- **BY-SA share-alike is not stated anywhere the user can see it.** Roughly a
  third of the credited portraits are BY-SA, and share-alike binds derivative use.
  The per-image line names the licence but not the obligation.
- **No dataset-level notice.** The per-image credit covers individual files; there
  is still no page listing the datasets and their terms.

## Attribution surface

Two surfaces now, one of them new.

**Per image** — implemented. The species panel prints the source, artist and
licence beneath the portrait, or a link to the Commons file page when the author
is unknown. See `portal/src/components/UnifiedInfoPanel.tsx`.

**Per dataset** — still missing, and recommended since 2026-07-06. A site-wide
"Data sources & licences" page must cover at minimum: **Wikipedia (CC BY-SA),
Plants of the World Online (Kew, CC BY), GBIF (per-dataset, and say which),
IPNI/IFPNI, Atlas of Living Australia, the Orthoptera Species File (CC BY 4.0),
Smithsonian NMNH (CC0) and Wikimedia Commons (per-file)**.
[`data-sources.md`](data-sources.md) is written to be the content of that page;
it still needs a rendering that a reader can actually reach.
