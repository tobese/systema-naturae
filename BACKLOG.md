# Backlog


- How is deployment done today? The needed artifacts as I see it is the portal and the built files only?

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

Still open: **4 hybrids** (none have any text) and the long tail of ~808k
species, which is the same job `scripts/enrichFromWikipedia.ts` already does for
the SQLite mirror — so the work is extending that pass to the ranks it skips,
not anything new. Once storage covers a rank, drop the live fallback for it.
Portraits for hybrids are absent from `wiki-images.json`, as they are for
subspecies (trinomials), so those panels rely on the live lookup for images.

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
from it via `VITE_WIKI_SUMMARY_BASE` in `portal/.env.local`. Not routed through
Caddy and not used by deployed builds — the primary deployment is GitHub Pages,
where it is unreachable. Remaining: point the batch enrichment scripts at it
(§ below), and if the tree's hover portraits are ever wanted from the mirror,
extract the infobox image from wikitext.

What is left:

- Point the batch enrichment scripts at it. Measured cold on that box it does
  ~17 keys/s (0.26 s for one key, 12.4 s for 200, ~0 s for anything already
  served), so a full 809k-species backfill over HTTP would be ~13 hours — fine
  for incremental passes, too slow for the initial one, which should keep
  hitting Postgres directly.
- The 809k-species / 4,182-family / 849-subspecies / 4-hybrid backfill itself
  (see the item above).
- If the browser should ever use it: `useWikipediaSummary` plus the three direct
  fetches in `shared/src/components/FamilyTree.tsx` (the real volume — it fires
  on node hover) and `EponymModal`'s `action=query` all need to move behind one
  base-URL-configurable helper, *and* that needs a Caddy route and a decision
  about public exposure. Note the mirror is a 2026-06-01 snapshot, so the browser
  would get older text than the live API — a rate-limit win, not a freshness one.

Plan, including why running MediaWiki for enwiki is the wrong answer on that box
and why svwiki is the one case where it is not:
`docs/wiki-on-debbie-plan.md`.
