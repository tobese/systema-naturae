# Data Sources — Attribution & Licensing

Last gathered: 2026-07-06.

This project reuses **text descriptions** and **distribution data** from external
biodiversity databases. Each species node records its provenance in the
`sourcedFrom` field. This doc lists every source we pull from, its licence, and
the attribution we owe. **Read the "Licensing risk" section before publishing.**

> Note: licences below were read from each source's official terms/FAQ/footer on
> 2026-07-06. Where a source has no formal licence page (footer/FAQ only) it is
> flagged. Nothing here is legal advice.

---

## Sources currently in the data (`sourcedFrom` values)

| `sourcedFrom` | Source | Licence | Attribution | Species (plants) |
|---|---|---|---|---|
| `wikipedia` | Wikipedia article text | **CC BY-SA 4.0** (share-alike) | Required | ~75,360 |
| `gbif` | GBIF species descriptions | Per-dataset: CC0 / CC BY / CC BY-NC | Required (BY/BY-NC) | ~13,675 |
| `powo` | Plants of the World Online (RBG Kew) | **CC BY** | Required | ~5,083 |
| `nzpcn` | NZ Plant Conservation Network | **Permission-based** (no CC) | Required | 1 (test shot) |
| `websearch` | Mixed (see below) | **Mixed / some non-open** | Required | ~46 |

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

## Attribution surface

Wherever descriptions are shown in the portal, surface a data-attribution
notice that covers at minimum: **Wikipedia (CC BY-SA), Plants of the World Online
(Kew, CC BY), GBIF, IPNI/IFPNI, and Atlas of Living Australia.** A site-wide
"Data sources & licences" page linking each source's terms is the cleanest way to
satisfy the attribution requirements above.
