# Backlog


- ~~How is deployment done today? The needed artifacts as I see it is the portal
  and the built files only?~~ **Closed 2026-09-29.** The deployable artifact is the
  image alone — `docker build` self-builds from all six kingdoms out of
  git-tracked source, then `docker save | docker load` and
  `docker compose up -d --no-build`. Written up in `docs/deploy-debbie.md`,
  along with the stale-`COPY . .` hazard that made a green build meaningless and
  the reason the build happens on a dev machine rather than on the target.

## Book: no phylum level

The book goes kingdom selector → Part (CLASS) → Chapter (ORDER) → Family → Genus →
Species, so the PHYLUM rank is structurally absent. The graph has a `PhylumPanel`
and all 32 animalia phyla carry a description, so those 32 are visible in the
graph only.

Not a slicing bug: `portal/public/data/kingdoms/*/orders/*.json` is rooted at
ORDER, and `book-skeleton.json` is Parts (one per class) → Chapters (one per
order), so neither source contains a phylum to render.

A design call, not a defect — hence here rather than fixed. Options, roughly in
order of effort: fold phyla into the Part title/intro; make a Part per phylum and
demote classes to chapter groupings; or leave it and accept that the book is
class-first. Audited in `docs/graph-vs-book-parity.md`.

**Now partly unblocked.** Once the source tree is
`taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/` and the book emits
per-kingdom skeletons (see "Emit the book's sidecars per kingdom" below), a
Part per phylum becomes a different change than it looks today: the phylum
would already be a first-class level in both the source and the build output,
rather than something that has to be recovered. Worth revisiting the options
once both land, rather than treating this as settled.

## Backfill descriptions so the graph stops falling back to a live Wikipedia fetch

`UnifiedInfoPanel` now prefers the stored `description` over a live REST summary
at every rank that shows prose — species, subspecies, hybrid, family, breed — so
the graph and the book read the same text, and the graph no longer shows whatever
Wikipedia returns *today* while the book shows the stored copy.

The live fetch is kept as a fallback, so nothing goes blank, but that means most
of the tree still renders a network round-trip and the two surfaces can still
disagree wherever storage is empty. What is missing, counted from the built order
files across all kingdoms:

| Rank | stored / total | falls back to live |
|---|---|---|
| SPECIES | 395,061 / 1,204,338 | 809,277 |
| FAMILY | 3,860 / 8,042 | 4,182 |
| SUBSPECIES | 2 / 851 | 849 |
| GENUS | 92,967 / 93,037 | 70 |
| ORDER | 1,047 / 1,100 | 53 |
| BREED | 317 / 321 | 4 |
| HYBRID | 0 / 4 | 4 |

**Subspecies: done, and the premise was wrong.** This was listed as "a few
hundred articles, not a project". It is not: of the 851 SUBSPECIES nodes, only
**2 have an en.wikipedia article of their own** (132 are redirects, 717 have no
page at all), because Wikipedia documents subspecies inside the *species*
article rather than at the trinomial. There was nothing to fetch per subspecies.

The leverage is one level up, and that is what got done: those 851 subspecies hang
off 229 host species, of which 91 had no stored description.
`scripts/enrichSubspeciesHosts.py` filled exactly those 91 (anatidae 7,
phasianidae 36, psittacidae 48) — all 229 hosts now described, all 91 resolved,
no misses. `SubspeciesPanel` then reads the parent's stored prose through a new
memoized `findNodeByName` in `useUnifiedTree` rather than duplicating it onto
all 851 nodes, which would have put ~1.3MB of identical paragraphs into the
committed family JSONs. Verified in-browser: *Amazona aestiva aestiva* and
*Anas bahamensis galapagensis* both render portrait, habitat and prose.

Still open: **4 hybrids** (none have any text). Portraits for hybrids are absent
from `wiki-images.json`, as they are for subspecies (trinomials), so those panels
rely on the live lookup for images.

### The species long tail: measured, and mostly not Wikipedia's fault

The subspecies item above turned out to generalise. The deployed animalia tree
(383 order files, 527,631 species) had **462,950 species with no description —
87.7%**. Joining every one of them against the 19.1M-page enwiki mirror on
debbie:

| | |
|---|---|
| have a real article | 26,937 |
| are redirects that resolve | 11,592 |
| **reachable total** | **~38,500** |
| **no en.wikipedia page at all** | **421,748 (91.2%)** |

So the "run the Wikipedia pass over the long tail" plan has a hard ceiling at
about 8%. `scripts/enrichEmptySpecies.py` takes that ceiling, and what it
actually closed:

| | before | after |
|---|---|---|
| species with a description | 64,681 (12.3%) | **103,193 (19.6%)** |
| species without | 462,950 (87.7%) | 424,438 (80.4%) |

**38,512 species described** across 938 family files, in 13 minutes of fetching.
The lead is validated before it is written, which matters at this volume: a lead
that never mentions the genus is a title collision and is rejected, as is a
lead that opens "is a genus of". That check also caught a real class of trap —
`Abaraeus hamifer` redirects to `Temnosceloides hamifer` and `Abbottina
obusirostris` to `Platysmacheilus obtusirostris`. Those are **genus
reclassifications, not synonyms**, and pasting the new genus's description onto
the old node would quietly put the wrong animal in the tree.

### `portal/data/description-lookup.jsonl` — every name we looked up, including the misses

`scripts/enrichEmptySpecies.py` now writes a ledger, one JSON record per name:

```json
{"src":"enwiki","generatedAt":"...","counts":{...}}      <- header
{"n":"Abaraeus hamifer","s":"rejected","r":"collision","t":"Temnosceloides hamifer"}
{"n":"Some other name","s":"no-article"}
```

424,222 records, of which **421,749 have no en.wikipedia page at all** and
**2,473 have one but failed validation** (1,456 collision, 949 genus-page,
35 stub, 33 no-lead). Those two numbers are the whole story of the remaining
gap, and the 2,473 are a revisit list: they have a real article, so a better
validator, or a human, can cheaply recover them.

The point of the ledger is that `sourcedFrom` cannot carry this. `"none"` is
overwritten by the next successful pass (`tools/powo_enrich.py:190` turns it
into `"powo"`), and every enricher's candidate filter re-selects `none`, so
misses get retried on every run instead of being parked. The same idea, already
proven in this repo, is the `{qid: "", fetchedAt}` stub in
`shared/data/wiki-images.json` — record every name you asked about so a miss is
never re-queried. `description-gap-report*.json` does it for higher ranks via
`unresolvableIds[]`, but only for PHYLUM/CLASS/ORDER and only when run with
`--write`.

Re-running the script now skips names already in the ledger, so a future pass
over a second source does not repeat the 13 minutes for names enwiki never had.
A cold fetch is ~13 min; ~21s once the page cache is warm.

**Tried and dead: stripping authority suffixes.** 169,206 of the 421,749
`no-article` names carry one - `"Aaadonta angaurana Solem, 1976"`,
`"Aaptochiton pustulosus Hoare & Karasawa, 2008"` - and no Wikipedia title will
ever contain one, so they look like a free win. They are not. Sampled 3,000 and
looked up the bare binomial: 2 resolved, projecting to ~112 across all 169,206,
and one of those two was a *wrong* match (`Torellia vestita` resolves to
`Torellia delicata`). The suffix is a symptom of obscurity, not the cause of
the gap - the underlying taxa are simply undocumented everywhere. Worth knowing
because `stripAuthority` already exists at `shared/src/hooks/useWikiImages.ts:82`
and it is tempting to reach for it. Do not.

Note the mirror is `EnWikiPages` in Postgres on debbie, **not**
`/Volumes/WikiDump/wiki-pages.sqlite`, which holds only 208k pages and is a
subset left over from earlier runs. Anything assuming the SQLite file is the
full dump is silently under-covering.

## Enrichment: where the remaining 745,500 descriptions can and cannot come from

**Measured 2026-09-30** from the committed family JSONs (7,807 files), not from
a built tier:

| kingdom | species | described | gap | covered |
|---|---|---|---|---|
| animalia | 529,125 | 130,445 | 398,680 | 24.7% |
| plantae | 435,113 | 325,699 | 109,414 | 74.9% |
| fungi | 161,716 | 3,896 | 157,820 | **2.4%** |
| chromista | 74,044 | 214 | 73,830 | **0.3%** |
| protozoa | 3,871 | 57 | 3,814 | 1.5% |
| archaea | 1,965 | 23 | 1,942 | 1.2% |
| **total** | **1,205,834** | **460,334** | **745,500** | **38.2%** |

Where the stored text came from is the whole story:

| kingdom | sources actually used |
|---|---|
| animalia | wikipedia 102,175 · gbif 27,424 · generated 843 |
| plantae | powo 248,499 · wikipedia 63,870 · gbif 13,238 |
| fungi | wikipedia 3,896 |
| chromista | wikipedia 214 |
| archaea | wikipedia 23 |
| protozoa | wikipedia 57 |

Only plantae and animalia ever got a domain source. **Fungi, chromista, archaea
and protozoa have had exactly one enrichment pass each — Wikipedia — and it is
the worst possible source for them.** Fungal nomenclature is documented in
MycoBank and Index Fungorum, algal names in AlgaeBase and WoRMS; en.wikipedia
has articles for a few thousand of ~145,000 named fungi. The 2.4% and 0.3% are
not a backfill that ran badly, they are the ceiling.

### 346,820 species are reachable, and it is worth about 3%

`portal/data/` holds **191 GBIF class caches** — several hundred MB, including
`gbif-cache-agaricomycetes.json` at 83 MB — and every non-animalia kingdom's
classes already have one, so the mechanical side is done:

| kingdom | gap | GBIF class cache present? |
|---|---|---|
| fungi | 157,820 | yes |
| plantae | 109,414 | yes |
| chromista | 73,830 | yes |
| protozoa | 3,814 | yes |
| archaea | 1,942 | yes |
| **total** | **346,820** | |

And `portal/scripts/enrichFromGbifDescriptions.ts` needs **no code change**: its
walker recurses `taxonomy/*/*/…/src/data/*.json` and is already
kingdom-agnostic, it is idempotent (empty descriptions only), it sets
`sourcedFrom="gbif"`, and it takes `--class <name>` / `--all`. Nobody has run it
outside animalia.

So the reach is there. The yield is not — see immediately below.

```bash
cd portal
npx tsx scripts/enrichFromGbifDescriptions.ts --class agaricomycetes
# …then the other cached non-animalia classes; --all walks every family
```

Expect it to be slow and rate-limited (the script already backs off on HTTP 429
and resumes via `/tmp/gbif-desc-cache.json`).

**Measured first, because the premise was wrong. Then measured properly.**
A 20-species probe suggested 8% on fungi and 12% on chromista. A full run over
one class says otherwise:

| | count |
|---|---|
| `agaricomycetes` binomials checked | 40,278 |
| with any GBIF description at all | **151** |
| **measured yield** | **0.37%** |

The 20-species probe was off by more than 20x. It ran in 8.7 minutes, not hours
— the class cache makes key resolution ~1 call per 100 species — so this cost
almost nothing to find out, and it should have been the first thing measured
rather than the last.

The run also turned out to be a **no-op on the tree**: the 151 binomials with
text had already been enriched by an earlier run and are in `HEAD`, so
rewriting them produced byte-identical files (43 files touched, zero git diff).
Nothing was lost and nothing was gained. Which is the point — GBIF descriptions
for fungi are effectively absent, and re-running the pass will keep producing
nothing.

GBIF *matched* all 20 at confidence 99 — it knows every one of these names. It
just does not hold prose for them. GBIF's description store is built from Plazi
literature treatments, and there is very little Plazi treatment literature for
fungi or algae. At 0.37% the realistic yield across the whole 346,820 is ~1,300
species, which is 0.2% of the 745,500 gap. **Do not run this on the other
kingdoms.** The same gate is
why the pass is safe, and `fix_misattached_descriptions.py` should be run
afterwards as a check rather than assumed.

### What the specialist sources actually offer

Checked live on 2026-09-30, because the docs and the reality differ:

| source | cost | prose? | verdict |
|---|---|---|---|
| **Catalogue of Life** | free, **no key** | no — names, status, classification, synonyms | **use it**, see below |
| GBIF descriptions | free, no key | sparse outside animals (measured 8–12%) | not worth a bulk pass |
| WoRMS REST (`marinespecies.org/rest`) | free, no key | no — nomenclatural + distributions + attributes + references | good for marine name validation |
| Index Fungorum SOAP | free, no key | no — `NameSearchDs`, `NameByKeyDs`, `NamesByCurrentKey`, authors, ranks | names only |
| **EOL classic API** | free, key optional | has text, but see below | **no help for the long tail** — measured, not guessed |
| **MycoBank** | free after registration | **yes** — legacy SOAP exposed a `summary` field; modern REST at `webservices.bio-aware.com` needs a **bearer token** | the real fungal source, if the token is obtainable |
| **AlgaeBase** | **paid, €500–1000/yr** | taxonomic data | not free; key by emailing `pier.kuipers@algaebase.org` |

### EOL, measured properly

First report of this said EOL's classic API returns HTTP 520 and is unusable.
That was one sample of a transient Cloudflare error — it is up, and serves 200.
The conclusion survives, but the reason was wrong, and the real one matters more:

| species | EOL page | `dataObject` | text |
|---|---|---|---|
| `Nectria confluens` | found | **0** | 0 chars |
| `Cytospora coryli` | found | **0** | 0 chars |
| `Pseudopeziza loti` | found | **0** | 0 chars |
| `Navicula knysnensis` | found | **0** | 0 chars |
| `Pseudonitzschia heimii` | found | **0** | 0 chars |
| `Cantharellus mikemboensis` | found | **0** | 0 chars |

EOL **has a page for all six** — correct `scientificName`, taxon concept and all
— and **no content attached to any of them**.

The control matters here. `Pinus contorta`, which certainly has an en.wikipedia
article and therefore certainly has text in EOL, returns `dataObject: 0` as well.
So the empty result is not "these obscure species have no articles" — the
endpoint is returning no content objects at all:

| request variant | HTTP | top-level keys | `dataObject` |
|---|---|---|---|
| no `key` | 200 | `taxonConcept` | 0 |
| `key=` (empty) | 200 | `taxonConcept` | 0 |
| `key=garbage123` | 200 | `taxonConcept` | 0 |
| `key=<uuid-shaped>` | 200 | `taxonConcept` | 0 |

The `key` parameter is ignored in every variant, so the earlier HTTP 520 was
plainly transient rather than a missing key — the same request returns 200 with
and without `key=`. What comes back is `taxonConcept` with a `taxonConcepts`
list naming the hierarchy providers (wikipedia NO, NCBI, …) and
`richness_score: null`: identity and classification, no content.

So either the classic content endpoints have stopped serving text, or they now
require a genuinely registered key and an invalid one degrades silently to
hierarchy-only instead of erroring. EOL's own terms say "you must register with
the Site", so the second is plausible. **That cannot be settled without a key,
and it is the one thing worth re-testing if someone gets one** — it would move
EOL from "no help" to "unmeasured".

Either way: **the free sources are nomenclatural, not descriptive.**

EOL's *other* API (`EOL/publishing`, the traits service) is a different thing
entirely: Cypher over a neo4j traits graph, `/service/cypher`, `Authorization:
JWT <token>`. The token is not self-service — "an EOL administrator needs to
create a token for you, please contact hammockj AT si.edu" — the endpoint
returns 403 without one, and the doc describes it as "in its infancy" with
`/service/cypher` as the only service, written in November 2018. It returns
structured traits (body size, habitat, and so on), not prose. There is no field
in our schema for structured traits, so that is a different feature, not this
gap.

So: **the free sources are nomenclatural, not descriptive.** Getting real prose
for fungi means MycoBank (ask for a token) and for algae means paying AlgaeBase.
Both are decisions to make deliberately, not costs to discover later. Neither is
worth doing before the GBIF yield is accepted as the realistic alternative.

### MycoBank is on Zenodo, free and keyless — 84% of our fungi

The token request drafted in `docs/drafts/mycobank-token-request.md` is worth
keeping for *prose*, but not for names. EOL republishes source datasets as Zenodo
deposits, and `13321883 "MycoBank: MycoBank (671) DwCA"` (2024-08-14, 8.04 MB,
CC-BY) is the lot:

```
taxonID · acceptedNameUsageID · parentNameUsageID · scientificName
        · taxonRank · scientificNameAuthorship · taxonomicStatus
```

**436,157 fungal names, no key, no registration, no rate limit.** Against our
own undescribed species:

| | |
|---|---|
| undescribed fungal species | 157,669 |
| found in MycoBank | **132,962 (84.3%)** |
| of those, synonyms | 5,842 |
| synonym → accepted resolvable | 5,448 |

Real examples: `Karlingia lobata → karlingiomyces lobatus`,
`Neokarlingia chitinophila → rhizophlyctis chitinophila`.

**There are no descriptions in it.** It is nomenclature — authorship, status and
the synonym→accepted link. So it does not close the description gap, and a
Postgres import of it would not either. What it does buy is the same
authoritative synonym resolution COL provided, for fungi specifically and
without COL's coverage gaps (`Acanthispa` is absent from COL but MycoBank has
441k names), plus `scientificNameAuthorship`, which nothing in our tree records
today.

EOL's other useful deposits, for the record: `22129810` "All trait data"
(592 MB, `pages/traits/metadata/inferred/terms.csv` — structured), `15549295`
"AmphibiaWeb text w/traits" (4.4 MB, prose, but amphibians only), `14583614`
Wikipedia-de dump (325 MB), `4062537` Plazi Treatment RDF Archive (507 MB, 2020
— treatments are the prose GBIF already mirrors, hence 0.37%). The GBIF national
node summaries (`22823470` Sweden, 49 MB) are occurrence and measurement tables:
`measurementType` is a URI, `measurementValue` a catalogue number.

Zenodo's API caps `size` at 25 and rejects any `page>1`, so a full sweep of the
1,880 EOL records needs date slicing; sampling 2019–2026 by year and month
surfaced no fungal or algal deposit carrying prose.

### Media captions scraped into descriptions — done, `fix_thumb_captions.py`

Found while measuring what the display gate would hide. An enrichment run wrote
image markup into `description`, so the field held a caption, or a caption plus
the real lead:

```
thumb|Lycopodiella alopecuroides (L.) Cranfill.
thumb|233x233px|Entamoeba histolytica in peripheral blood
thumb|right|450px|Life-cycle of Entamoeba histolytica.
left|thumb|173x173px|Carrot infected with Meloidogyne chitwoodi
  Meloidogyne chitwoodi is a plant pathogenic root-knot nematode …
```

**1,708 species** across five kingdoms — 1,128 plantae, 538 animalia, 27 fungi,
12 chromista, 3 protozoa. Note the marker also appears as `[[Link|thumb]]` and
with inline pixel dimensions, so a `^thumb\|` match finds only a fraction of
them; and a loose `alt` pattern matches ordinary prose.

`scripts/fix_thumb_captions.py` cuts at the **last occurrence of the binomial**,
because a Wikipedia lead opens with the name and the caption usually names the
species too, so the *first* occurrence keeps the caption. Result: **468
recovered, 1,239 cleared**, in 388 family files, idempotent, 0 media markers left.
Coverage moves 460,802 → 459,563 described species: the loss is intended, because
`thumb|Leaf specimen of M.` is a caption and the honest options are prose or
nothing.

The rule clears rather than recovers whenever it is unsure, and one case forced
that. The Somali Crow mentions its binomial exactly once and only inside an
appositive:

```
thumb|Somali Crow The Somali crow, or dwarf raven (Corvus edithae), is approximately the size…
```

Cutting at the last occurrence yields `Corvus edithae), is approximately the size…`
— mid-parenthetical. Both existing guards passed it, because it does contain "is"
and does start with a capital. Counting brackets at the cut point is what catches
it, and requiring the tail to end in terminal punctuation catches the rest. That
moved 59 species from "recovered" to "cleared", which is the correct direction.

Verified ID-agnostically with a multiset of `(name, description)` pairs, because
the first check keyed on `id` and reported three phantom edits: the touched files
contain **25 duplicate species names** (`Cyanocorax mystacalis`,
`Aphelocoma insularis`, `Parotia sefilata` … each twice), so ID-keyed comparison
matched them against each other. `fix_duplicates.py` exists for that and is worth
running separately — it is not this script's business.

### The one genuinely valuable free source: Catalogue of Life

COL aggregates Index Fungorum, AlgaeBase and other specialist checklists under
one keyless API (`api.checklistbank.org`, dataset `3LR` for the current release,
`COL{year}` for the permanent annual). It carries no prose — but it carries
`status: accepted | synonym` per name, which is exactly what the collision
problem needs, authoritatively and for all six kingdoms at once:

| name | COL status |
|---|---|
| `Abaraeus hamifer` | **synonym** |
| `Temnosceloides hamifer` | **accepted** |
| `Acanthodes lateralis` | **accepted** |
| `Acanthispa lateralis` | **accepted** |
| `Cytospora coryli` | accepted |

The rule needs no graph traversal and no epithet matching: for a candidate pair
(A = our name, B = the Wikipedia redirect target), **A synonym + B accepted means
same taxon, accept it; A accepted + B accepted means two distinct names, reject
it.**

Run complete over all 1,456 cases — `docs/reports/name-attribution-col.md`:

| verdict | count | meaning |
|---|---|---|
| `safe` | **352** | ours is a COL synonym, target accepted — the description may be applied |
| `distinct` | **80** | both names accepted in COL — genuinely different taxa, correctly rejected |
| `unknown` | 1,024 | COL has no usable answer — left alone |

The epithet heuristic proposed 409 safe. COL confirms **352** of them and rejects
some of the rest as distinct, so it is doing real work rather than
reproducing the guess. The `unknown` bucket is 70% and that is mostly COL's own
coverage: `Acanthispa` is not in COL at all, and one ledger target is a
vernacular name ("Khanka spiny bitterling"), so those cases need a human or the
acceptedId link. Erring toward `unknown` is the right default here — the failure
this replaces pasted a beetle description onto a fish.

Not yet applied: `validateNamesWithCol.py --apply` is deliberately unwired, so
the 352 are a reviewed list rather than a silent edit.

And it settles the open question from the section below, which the epithet
heuristic got wrong. `Acanthodes lateralis` and `Acanthispa lateralis` are
*both* accepted — a fish genus and a beetle genus — so epithet matching would
have pasted a beetle description onto a fish. COL rejects it for free.

### A smaller, fully safe win: 409 reclassified species

The 1,456 `collision` rejections in `description-lookup.jsonl` were species whose
Wikipedia lead never mentions our genus. 694 of those are redirect targets that
share our **species epithet** while differing in genus — under ICZN a change of
generic assignment does not change the species, so the target's text is about
the same animal. Splitting those 694 against our own taxonomy:

| | count | disposition |
|---|---|---|
| both genera in our tree, **same ORDER** | **409** | safe to accept |
| both genera in our tree, cross ORDER | 3 | genuine homonyms, keep rejected |
| target genus absent from our tree | 282 | needs an external genus check |

The 3 cross-order cases are exactly the trap: `Duplicaria nadinae →
Terebra nadinae` is a fungus matched against a gastropod, and the two genera
even swap back (`Terebra duplicata → Duplicaria duplicata`). Note the 282 are
**not** safe by default — `Acanthodes lateralis → Acanthispa lateralis` is a
fish genus pointed at a beetle genus, and it is only catchable because the
target is missing from our 91,728-genus index. Do not widen the rule to
"epithet matches".

409 out of 745,500 is 0.05%, so this is a tidy-up, not a lever. The GBIF pass
above is the lever.

### Not worth doing

- **More Wikipedia work on the animalia long tail.** Already at its ceiling —
  421,749 of the undescribed have no en.wikipedia page at all (91.2%). More
  passes over the same 8% is done.
- **Stripping authority suffixes to widen name lookups.** Tried and measured:
  3,000 sampled, 2 resolved, one of them a *wrong* match. The suffix is a
  symptom of obscurity. Do not reach for `stripAuthority`.

## Emit the book's sidecars per kingdom, like the graph already does

The graph view reads per kingdom — `data/kingdoms/<k>/unified-taxonomy-skeleton.json`
plus `data/kingdoms/<k>/orders/<ORDER>.json`. The book reads one cross-kingdom
`data/book/book-skeleton.json` (3.4 MB) plus `extensions-<k>/`. The split is
arbitrary: `experiments/book-view/scripts/extractSlice.ts` **already** iterates a
`KINGDOM_DIRS` map and reads each kingdom's `order-manifest.json`, then collapses
the result into a single skeleton. The input side is partitioned; only the output
is monolithic.

And the file is almost entirely partitionable. It is `{parts: [...]}`, one part
per class — 255 of them, each already carrying its own `kingdom` field:

```json
{"title":"Part I — Mammalia","kingdom":"Animalia","className":"Mammalia",
 "description":"...","collage":"...","chapters":[
   {"title":"Chapter 1 — Carnivora","orderFile":"CARNIVORA","families":[...]}]}
```

A chapter is a *pointer* — `orderFile`, `families`, `title`. No species prose is
in this file; the book fetches the order files. So it is a table of contents, and
it groups cleanly by kingdom: Animalia 75 parts, Fungi 51, Plantae 43, Chromista
33, Archaea 30, Protozoa 23.

**Target shape**, matching the graph and the source tree:

```
book/index.json                        kingdom sequence, tiny
book/kingdoms/<kingdom>/skeleton.json  that kingdom's parts and chapters
```

The reading order survives the split because it is already explicit in each
part's title — `"Part I — Mammalia"` — so the Part I/II/III numbering does not
need to be reconstructed; `index.json` only has to carry the kingdom sequence
(`Animalia, Plantae, Fungi, Chromista, Protozoa, Archaea`, which today is the
hardcoded order of the `KINGDOMS` map in `extractSlice.ts` and should become
data rather than a literal).

Do this **after** the `taxonomy/<kingdom>/…` restructure and as its own commit,
not folded in — it is a runtime-facing change and the restructure should stay
independently revertable. Together they make the source tree, the graph output
and the book output all keyed by kingdom, which is the property the 258
top-level directories were missing.

## Serve Wikipedia lookups from debbie instead of en.wikipedia.org

Every node without a stored description currently costs a live REST call, which
is the rate limit and the graph/book disagreement waiting to happen. The
enwiki wikitext is *already* mirrored in Postgres on debbie (19M mainspace rows,
38 GB), so a small HTTP lookup service in front of it — the same shape as the
existing `scripts/dbserved.ts` — would cover it, following redirects so
`Pekin` → `American Pekin` the way the breed resolver needs.

**Built, deployed, and wired into local development.** `wikiserved` runs in the
deploy compose (`services/wikiserved/README.md`), reachable on the
LAN/Tailscale at `debbie:9881`, and the dev server takes Wikipedia summaries
from it via `VITE_WIKI_SUMMARY_BASE` in `portal/.env.local`.

Not used by deployed builds. **Corrected 2026-09-30:** this previously said the
primary deployment is GitHub Pages "where it is unreachable". That is not the
live site — the primary deployment is the Docker image behind Caddy at
`/systema-naturae/` (see `docs/deploy-debbie.md`); GitHub Pages is a separate
workflow. The corrected reading, which points opposite ways on two axes:

- `wikiserved` and `systema-naturae` are services in the **same compose file**
  on debbie, so anything server-side on that network reaches it at
  `http://wikiserved:9881` today. Reachability was never the problem.
- The deployed portal is static nginx serving prebuilt files. It makes no
  server-side Wikipedia calls at runtime, so there is no server-side consumer to
  repoint. The consumer that needs the mirror is the **browser**, which cannot
  resolve a compose service name.

So browser-side use needs a route — a Caddy one, or an `nginx.conf`
`proxy_pass` location — and still needs a decision about public exposure. Note
the mirror is a 2026-06-01 snapshot, so the browser would get older text than
the live API: a rate-limit win, not a freshness one.

Remaining: point the batch enrichment scripts at it (§ below), and if the
tree's hover portraits are ever wanted from the mirror, extract the infobox
image from wikitext.

What is left:

- Point the batch enrichment scripts at it. Measured cold on that box it does
  ~17 keys/s (0.26 s for one key, 12.4 s for 200, ~0 s for anything already
  served), so a full 809k-species backfill over HTTP would be ~13 hours — fine
  for incremental passes, too slow for the initial one, which should keep
  hitting Postgres directly.
- The remaining backfill is measured and bounded, not open-ended, and recorded
  per name in `portal/data/description-lookup.jsonl`: 421,749 species have no
  en.wikipedia page and need GBIF/iNaturalist/EOL rather than this mirror;
  2,473 have a page but failed validation and are a revisit list. The 4 hybrids
  are still open.
- If the browser should ever use it: `useWikipediaSummary` plus the three direct
  fetches in `shared/src/components/FamilyTree.tsx` (the real volume — it fires
  on node hover) and `EponymModal`'s `action=query` all need to move behind one
  base-URL-configurable helper, *and* that needs a Caddy route and a decision
  about public exposure. Note the mirror is a 2026-06-01 snapshot, so the browser
  would get older text than the live API — a rate-limit win, not a freshness one.

Plan, including why running MediaWiki for enwiki is the wrong answer on that box
and why svwiki is the one case where it is not:
`docs/wiki-on-debbie-plan.md`.

## Folded in from `docs/backlog.md` (2026-07-03; file deleted 2026-09-29)

`docs/backlog.md` was a second, parallel roadmap, last touched 3 July. Most of
it was superseded, but these items were still open and were tracked nowhere
else, so they are preserved here rather than lost with the file.

### Book: per-family chunks

- Split the order chunks into per-family files for finer-grained lazy loading,
  and teach the manifest/loader to resolve family chunks. **Measured
  2026-09-29, and not recommended as written:** the book already lazy-loads per
  chapter, and per-family would take Coleoptera from 55.1 MB to 15.8 MB — but
  Hymenoptera only 13.1 → 12 MB, because Formicidae is 74% of that order. It
  also needs a new structure tier (the nav tier cannot back it: `navProjection`
  deletes `speciesList`, so it carries no species names), lands in
  `shared/src/book/` that the standalone app consumes by symlink, and adds
  ~63 MB to the shipped payload. Related: *Emit the book's sidecars per kingdom*
  above, which is about sidecars rather than chunk granularity.
  See `docs/data-tiers.md`.

### Data

- Wikipedia enrichment: batch the biggest zero/near-zero coverage classes first
  — Gastropoda, Bivalvia, Annelida, Bryozoa, Porifera, Platyhelminthes,
  Nematoda.
- Wikipedia enrichment: make a pass resumable per class, so long runs can
  stop/start without losing progress.
- Wikipedia enrichment: keep empty or weak extracts out of
  `sourcedFrom=wikipedia` and surface only real descriptions. Partly overtaken —
  the mis-attached-text work on 2026-09-29 cleared 73 records and re-attributed
  18, and `fix_redirect_descriptions.py` clears 913.
- Micro-phyla scaffolding: manual taxonomy treatment for Gastrotricha,
  Phoronida, Priapulida, Loricifera, Gnathostomulida, Entoprocta, Onychophora,
  Xenacoelomorpha.
- Micro-phyla validation: verify how each manual phylum should appear in
  `taxonomy.json`, the gap reports, and the UI tree.

### UI polish

- Bookmarks and anchor links — deep linking per section in the Book view.
- Book view: scroll to and open the relevant section on a search match.
- Pulsing search matches — replace the 10% opacity dimming with a glow.
- Tooltip: fade hover thumbnails in after load instead of popping them, keeping
  the caption visible and avoiding layout shift.
- Improve genus-centering zoom — refine the zoom level when centring on genus
  nodes.
- Wheel of Nature: tick audio while spinning; cache the last winner per session
  to avoid immediate repeats.
