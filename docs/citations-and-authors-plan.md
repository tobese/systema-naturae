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
the author viewer (a person's publications). Not held today; needs an import
pass that keeps it.

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
