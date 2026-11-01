# Wikipedia enrichment, version 2

Status: **plan, 2026-11-01; nothing built beyond the measurement.** English
only (the user, 2026-11-01).

## Why a new version

Today's path (`scripts/enrichFromWikipedia.ts`) looks a species up **by its
title**: the local `wiki-pages.sqlite` first, the Wikipedia API second.
That misses most of what exists:

- `wiki-pages.sqlite` holds 208k pages picked from our species list as it
  was in June-August; the tree has doubled since (2.4M -> 4.9M).
- ~45k species articles are titled by a common name ("Monarch butterfly"),
  which a title lookup never finds.
- It overwrites `description` and sets `commonName` from the API's short
  description, one family at a time, outside `maintenanceLock`.

Measured 2026-11-01 by joining Wikidata QIDs (below): held species with an
English article, 419k rows; **177,380 distinct names** whose article is not
in the local database, of which 27,459 were already filled through the API --
so **~150k species can gain article text**, and ~45k a common name from the
article title.

## Sources we hold

| source | what it gives | where |
|---|---|---|
| Debbie `EnWikiPages` | full wikitext of every article, revision id, 2026-06-01 dump, 19M rows | Postgres on debbie (`postgres_snedtankt_debbie`) |
| Debbie `EnWikiPagesQid` | page -> Wikidata QID, 10.3M | same |
| Wikidata Species (ChecklistBank 314569, CC0) | QID -> scientific name, rank, classification; VernacularName, Distribution, Media (P18), TaxonProperty | `archives/ac5f72cf-…/` |
| `wiki-taxa.parquet` | QID -> name -> enwiki page/title: 368k species, 104k genera, 9k families | built 2026-11-01 (scratch); to become a script |
| `shared/data/wiki-images.json` | image, commonsCat, iucnStatus, rangeMaps, by name | sidecar, read at runtime |
| Commons categorylinks | range maps | `/Volumes/WikiDump/commons/` |
| `wiki-pages.sqlite`, enwiki multistream dump | the old path | superseded; kept as fallback |

## Steps

1. **The index as a script** (`scripts/buildWikiTaxaIndex.py`): exports
   page/QID/title/revision from Debbie (one `COPY`, ~150 MB, minutes) and
   joins the Wikidata Species archive. Output `<sources>/work/wiki/wiki-taxa.parquet`.
   Rebuilt when either side is refreshed.

2. **Match to our species**, strongest first:
   - the species already carries the Wikidata Species id (sourceIds key
     `ac5f72cf-…`, the QID) -- exact;
   - else the canonical name equals Wikidata's name, in the same kingdom
     (Wikidata's classification), and the name is held once in that kingdom
     -- the unique-hold rule of the nomenclatural track;
   - skipped and counted otherwise (homonyms, names held twice).
   The QID join also removes the old genus-article problem
   (`fix_redirect_descriptions.py`): redirects carry no QID of their own.

3. **Extract on Debbie**, next to the data: read the matched pages by
   PageId (batched SQL) and reduce each to plain fields with the parser
   already written for breeds (`enrichBreedsFromWikipedia.py`:
   `render_templates`, `strip_wikilinks`, `lead_paragraphs`) moved into a
   shared module:
   - lead text (first paragraphs, plain);
   - `{{Short description}}`;
   - taxobox: image, status + status_system (IUCN), range map, authority;
   - title, and the bold names of the first sentence ("..., commonly known
     as the *X*").
   Output one jsonl/parquet, copied to Macie. Deterministic parsing only --
   no generated text (CLAUDE.md).

4. **Apply fill-only**, through `applyEnrichment.py` (new fields) in a
   maintenance session, per kingdom, dry run first:
   - **no stubs** (decided 2026-11-01: an empty description is something to
     compare against; stub text only looks like coverage). A page is a stub
     when its wikitext carries a `{{…-stub}}` template -- Wikipedia's own
     marking, not a length guess. Its lead is not written; the page is still
     used for the other fields (common name, QID, title, taxobox), and the
     skip is recorded in the run's ledger with the page id, so the stubs can
     be counted and revisited when an article grows;
   - `description` + `sourcedFrom: "wikipedia"`: where the node has none, or
     only a template description ("… is a X species found in its native
     region", "a species in the genus …" -- the same test `buildData.ts`
     uses for minimal species);
   - `commonName`: from the article title when it is not the scientific
     name, else a bold name in the lead; only where empty;
   - `wikipediaTitle` + `wikipediaRevision`: for attribution (CC BY-SA 4.0
     needs a link to the article and its history) and to diff on refresh;
   - the QID under the `ac5f72cf-…` key where missing;
   - image / IUCN / range map into `wiki-images.json`, not the tree, as
     today.

5. **Higher ranks**: the same index has 104k genera and 9k families with
   articles; genus/family descriptions replace `enrichHigherRanks.ts`'s API
   calls.

6. **Retire** the bulk API path of `enrichFromWikipedia.ts`; the portal's
   runtime fallback (`wikiSummary.ts` / `wikiserved`) is untouched.

## Open questions

- ~~Stubs~~: skipped (above). Measure their share in step 3.
- **Template descriptions** are the same thing as a stub, only ours: if
  stubs stay empty, the existing template descriptions ("… is a X species
  found in its native region") arguably should be cleared too, so empty
  means empty everywhere.
- **Freshness**: the dump is 2026-06-01. Refresh Debbie's import before
  this, or take June now and diff by revision later?
- **Coverage report**: count template descriptions as not described, so the
  "described" share means something (it reads 69% today).
