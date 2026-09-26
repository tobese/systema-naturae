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
