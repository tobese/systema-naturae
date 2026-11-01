# The authors track: people as their own kind of source

Status: **plan, 2026-11-01** (the user's idea: a new kind, with its own
transform and import, like the nomenclatural track).

## Why

An authorship today is a string ("Ploeg, Jégu & Ferreira, 1991"). The same
person is written many ways ("L.", "Linnaeus", "von Linné"), so comparing
two sources' authorships needs `taxamatch.same_authorship` plus
`authorNames.py`'s Wikidata lookup, and nothing in the tree says *who* a
name's author is. Sources that know their authors as people already exist:

| source | people | name -> author links |
|---|---|---|
| Wikidata Species (`ac5f72cf-…`, held) | 56,034 (QID; 32,729 botanical abbreviations; 10,322 ORCID etc.) | 1,037,047 species (`combinationAuthorshipID`), 74,221 basionym authors |
| ZooBank (API, not held) | zoological authors, UUIDs | via its name records |
| IPNI authors / Harvard Index of Botanists | standard forms, IPNI author ids | via IPNI names |

None of our other archives has one: ZooBank's ChecklistBank export, IPNI,
Species Fungorum, COL, Nomenclator, AFD, INA, IRMNG carry text only, and
PBDB's `Author.tsv` (1174) lists its data enterers, not name authors.
ChecklistBank has no author registries (searched 2026-11-01).

## Shape

Same three parts as the nomenclatural track (`nomenclatureTransform.py` +
`applyEnrichment.py`):

1. **Recognised at triage.** A source is on the authors track when it has
   an author table *that its names point at* -- a ColDP `Author` table
   referenced by `combinationAuthorshipID` / `basionymAuthorshipID` -- or is
   a registered people source (ZooBank authors, IPNI authors). The pointer
   test is what keeps PBDB's data enterers out. A source can be on several
   tracks: Wikidata Species is a species source (held), a names source and
   an authors source. The transform exits with its own code and the
   ordinator marks the entry `kind: authors`, never draining it, as with
   `nomenclatural`.

2. **Transform** (`authorsTransform.py`) writes two work files:
   - `people.jsonl`: one person per row -- names, abbreviation, life dates,
     and every id the source gives (Wikidata, IPNI, ZooBank, ORCID, VIAF…);
   - `links.jsonl`: species -> author ids, only for species we hold once in
     the kingdom (the unique-hold rule) **and** whose authorship the source
     agrees with (`same_authorship` with `same_person`), so an id is never
     attached to a different person's name. Disagreements go to a review
     file, as with IPNI.

3. **Import** (`applyAuthors.py`):
   - people into a **registry** -- `data/authors/people.jsonl`, in git like
     the source queue, one row per person, keyed by Wikidata QID where there
     is one (the hub that already joins IPNI, ZooBank and ORCID), merging
     rows that share any id; fill-only;
   - links onto species as `authorIds` / `basionymAuthorIds` through
     `applyEnrichment.py`, in a maintenance session.

4. **Checks**: a `verifyTree` invariant that every `authorIds` entry
   resolves in the registry; the coverage report gains an "authored by a
   known person" share.

## Uses

- Authorship compared by person, not spelling: the IPNI (11,457) and Species
  Fungorum (3,776) conflict lists shrink to real disagreements.
- `authorNames.py` reads the registry instead of its own Wikidata pull.
- Portal later: a "described by" view, author pages, eponyms (`namedAfter`)
  linked to the same people.

## Order

1. Wikidata Species: measure people and agreeing links (no writes).
2. Build transform + import + invariant; apply in a maintenance session.
3. Ordinator/orchestrator wiring (`kind: authors`), triage detection.
4. More people sources: ZooBank authors, IPNI authors.
