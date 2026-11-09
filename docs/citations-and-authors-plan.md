# Citations, sources and authors in the portal — plan

Drafted 2026-11-03. Not started.

Goal: every species in the portal shows **where it comes from** (its sources,
with their citations), **who named it** (its authors, linked to a person), and
can be **cited** in a form that leads back to the same record later. Authors
and sources each get a viewer with back-references into the tree and the book.

Everything here comes from data the tree already holds — `sourceIds`, the
contributors registry, the authors registry — so it stays within the
no-LLM-content rule: nothing is inferred, only linked.

## What exists

- **Sources per species:** the species panel's *Sources* list (dataset title,
  institution, licence, link to the record in each ChecklistBank dataset),
  from `contributors-index.json`. The registry (`data/contributors.json`) also
  holds each dataset's citation, DOI, version DOI and licence as taken.
- **Authors:** `data/authors/people.jsonl`, 40,239 people from Wikidata
  (`Q…` ids; ORCID for some, birth/death for ~half, the standard botanical
  abbreviation for 23,498). 960,794 species carry `authorIds` (and some
  `basionymAuthorIds`) inline, e.g. *Apargidium boreale* "Torrey & Gray,
  1843" -> `["Q1346660", "Q347356"]`. The portal uses none of it yet.
- **The book view** (`BookReadingPane.tsx`), whose chapters map to the tree.

## Steps

### 1. Citations on the species panel (small)

- Each source in the panel shows its **citation** and **DOI** (already in the
  registry; add them to `contributors-index.json`).
- **"Cite this record"**: copies a citation in two parts — the portal record
  (*Systema Naturae (data version), Corvus corax, CC BY 4.0, link*) and the
  citations of the sources behind it.

### 2. A data version (needed before citations mean anything)

- The build stamps a **data version** (date + commit) into the manifest the
  app loads; the portal shows it and every citation includes it.
- Node ids are already stable. Release notes per version can come later.

### 3. Authors in sidecar files keyed by species id, not on every species

- Author links move out of the species nodes into **sidecar files keyed by
  species id**: `data/authors/links/<kingdom>/<shard>.json` (sharded by id
  prefix so no file grows large) = `{ speciesId: { a: [ids], b: [basionym ids], src } }`.
  Species nodes are not rewritten, and the big family files stop carrying the
  id lists (Asteraceae: 59,531 species with ids, ~1.7 MB before indentation,
  of a 76 MB file near the 100 MiB limit).
- **Why keyed by id rather than one file per family:** species move between
  families -- the dedupe, the family-pair pass, importwrite's cross-family
  merges, the homonym and placeholder clean-ups all do it. A species keeps
  its id when it moves, so an id-keyed link needs no handling; a per-family
  file would have to be moved by every one of those writers, and the one
  that forgets leaves the author behind.
- **What still needs handling: merges.** When a copy is removed in favour of
  a twin with a different id, its links go to the twin, fill-only -- the
  same transfer the writers already do for `sourceIds`
  (`resolveWeakHomonyms.carry_authors`, `fixQuotedNames`, the dedupe's
  `merge_into`). Every writer that removes a species in favour of another
  must call one shared helper for it.
- **Guard in verifyTree:** every link's species id exists in the tree
  (orphans are a failure, with the writer that left them findable from the
  logs), and every author id resolves in `people.jsonl` (as today).
- `applyAuthors.py` writes the sidecars instead of the species; a one-off
  migration moves the 960,794 existing inline links out.
- **Fallback:** where a species has no link, the portal shows its
  `authorship` string exactly as today. Linking only ever adds; nothing is
  hidden when an id is missing.
- New links only from a source that states them (Wikidata's taxon author,
  IPNI's standard abbreviations matched exactly) -- never by guessing a person
  from a string.

### 4. Author viewer

A page per person (`?author=Q…`):
- name, life dates, country, botanical abbreviation; links to Wikidata,
  ORCID, IPNI / ZooBank where held
- names authored: counts per kingdom and family
- the list of taxa, paged, each with a back-link into the tree (`?node=…`)
  and into the book chapter it sits in
- Authorship strings in the species panel become links to it (step 3 data).

Data: a per-author index generated at build time **split into small files**
(by id prefix), so the viewer fetches only the person it shows — 960k links
are too many to load at once.

### 5. Source viewer

A page per dataset (`?source=checklistbank-2144`): institution, citation,
DOI, licence as taken (and today, if different), version taken, the
families it supplies and how many species, with back-links into the tree and
the book. The Contributors cards link to it. Same split-index approach.

### 6. Later: where each name was first published

COL and several sources carry `namePublishedIn` (the reference behind
"Linnaeus, 1758": *Systema Naturae*, 10th edition). Kept per species, it would
be a third citation level — the original publication — and a natural fit for
the author viewer (a person's publications).

**Started 2026-11-08 from COL XR** (checklistbank-316441).
`scripts/buildCitations.py` joins the COL ids our species already carry
(`sourceIds.col`, `sourceIds.checklistbank-316441`) to COL's
`nameReferenceID` / `namePublishedInPage` and its Reference table, and writes
two sidecars sharded like the authors' ones:

    data/citations/species/<kingdom>/<xx>.json   speciesId → {r, p, pl}
    data/citations/references/<xx>.json          col:<id>  → {citation, doi, link, year, via}

`citation` is COL's text verbatim and `via` the dataset COL took it from.
First run: 1,539,253 species linked to 720,615 references — plantae 99%,
fungi 94%, chromista 71%, animalia 70%, protozoa 43%, archaea ~0% of the
species that have a COL id. The files are rebuilt from scratch on every run
and land with `landTree.py`'s shared paths; `verifyTree` fails on a link to a
missing reference or to a species no longer in the tree.

WoRMS (checklistbank-2011) fills in for species COL leaves without a
reference, joined on the WoRMS taxonID in `sourceIds`: its `namePublishedIn`
is text on the name, so a WoRMS reference is keyed `worms:<md5 of the
text>[:12]` and the same text is one reference. It adds 22,800 species
(animalia 14,039, chromista 8,504) and ~10,800 references.

Next: WCVP (2000) and IPNI (2006), which carry a referenceID and page — though
plantae is at 99% from COL already, so the gap that matters is animalia's
~430,000 species with a COL id and no reference.

Measured 2026-11-09 for the rest of animalia's gap (2,079,296 species with no
citation, most of them without a COL XR id at all): nothing else we hold
closes much of it.

- **Wikidata Species** (GBIF ac5f72cf…, 1.7M of the uncited carry its QID):
  links only ~26,000 species to a reference, and its Reference.tsv rows are
  bare item links (`Q102105754` → wikidata.org) with no title, author or
  year. Usable only by fetching each item from Wikidata — not done.
- **ITIS** (`publishedInID`): ~2,400 species, and the referenced rows carry no
  citation text.
- **uBio** carries referenceIDs for 245,000 but was reverted (2026-11-05).
- The rest of the top sources by count (GBIF Backbone, 139831, 2265, 2169,
  2008) carry no publication field.

The next real source for animals is outside what we hold: the Reptile
Database with literature (223917, registered 2026-11-09; reptiles are 26%
cited). Nomenclator Zoologicus is already held as Rod Page's ColDP (126539),
so 316817, an older edition, was not registered.

A third pass (2026-11-09) matches by name what has neither id: a species with
no COL or WoRMS link whose canonical name, in its kingdom, is exactly one
accepted COL XR species takes that species' reference, marked `"by": "name"`.
A name COL holds twice as accepted (homonyms, split placements) is left alone.
It adds 492,061 links (animalia 277,113, plantae 171,393, fungi 39,850,
chromista 4,347, protozoa 358), for 2,055,048 links to 777,116 references.

## Order

1 → 2 → 3 → 4 → 5 → 6. Step 1 is quick and useful on its own; 2 is what
makes a citation worth copying; 3 is the data change the author viewer needs,
and it also shrinks the largest family files; 4 and 5 share the split-index
build; 6 is new data.

## Open questions

- Sidecar location: decided against one file per family (2026-11-03): moves
  would have to carry the links. Keyed by species id under `data/authors/links/`
  instead; `landTree.py` already lands `data/authors`.
- Should the inline `authorIds` be removed after the migration, or kept until
  the portal reads the sidecars? Suggest: migrate, switch the readers, then
  remove, in one maintenance session.
- Book back-links: link to the chapter (order/family) or to the exact page
  position? Chapter first.
