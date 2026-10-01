# 4,551 unresolved names, and one root cause worth naming

## The count

| kingdom | rank | count | families |
|---|---|---|---|
| animalia | SPECIES | 2,592 | 299 |
| archaea | SPECIES | 976 | 126 |
| plantae | SPECIES | 454 | 94 |
| archaea | GENUS | 399 | 110 |
| chromista | SPECIES | 54 | 39 |
| archaea | FAMILY | 45 | 45 |
| fungi | SPECIES | 24 | 20 |
| animalia | BREED | 1 | 1 |

By parser `type`: 4,114 `INFORMAL`, 1,528 `OTU`, 334 `NO_NAME`.

`UNRESOLVED_TAXON` in `sanity_scan.py` reports these; nothing has been changed.

## Three different things, not one

They look alike in the count and are not alike in kind.

**animalia, 2,592 — `… spec.` placeholders.** `Droopiella spec`, `Orchis spec
Sauter, 1830`. A genus node exists, the species beneath it is a placeholder, and
it is a real editorial gap: the family has genera with unresolved contents.
**454 in plantae** are the same, and **24 in fungi**.

**archaea, 1,420 — not placeholders, a scaffold.** `Halicryptomorpha` was the
worst case in the whole audit, but it is one instance of a pattern:

    archaea > Nanosalinaceae (FAMILY) > M3-22 (GENUS) > 1 species
    archaea > ARS49 (FAMILY) > 16 species

`UBA10200`, `JAGWAF01`, `BM511`, `ARS49` are **NCBI genome assembly
accessions** standing in for genera and families. Archaea are scaffolded from
sequence data, not from a nomenclatural source, so those nodes have no taxonomic
name to carry and never did. 9% of archaeal species, 11% of genera and 15% of
families are named this way.

That is *why* they are unresolved, and it is not a defect to fix by renaming —
it is a scope statement about what this kingdom is. Making them legitimate would
mean deciding that the portal presents assembly-derived genomes as taxonomy, which
is a different product.

**fungi and chromista, 78** — I expected individual mistakes here and was wrong.
They are all `Genus spec` placeholders of exactly the animalia kind: `Uromyces
spec`, `Lactarius spec`, `Amphora spec`, `Vorticella spec`. Not errors, just the
same honest label in smaller numbers. The full list is in
`unresolved-taxa.json`.

## What I would not do

**Re-rank them.** `Salmo sp. BOLD:AAB3872` is not a species and `UBA10200` is
not a genus, so the honest options are to *rename* them or *remove* them, not to
relabel. Relabelling a placeholder as `INFORMAL` puts a rank in the schema that
nothing consumes, and it makes the count look handled.

**Delete them.** A `spec.` placeholder under a real genus is a visible statement
that this genus has contents we have not identified. Removing it makes the family
look complete when it is not, which is the failure mode the sanity scanner exists
to prevent. The archaea scaffolds are different — a removal there would delete
sequence-derived structure that is the only structure there is.

## What is worth doing

1. **Split the check into two** so the count stops being one meaningless
   number: `UNRESOLVED_TAXON` for `spec.`/`cf.` placeholders (3,332), and a
   separate, explicitly informational `ACCESSION_NAME` for archaeal scaffolds
   (1,213) so the archaeal scope statement is visible rather than looking like a
   defect.
2. **Leave the names alone.** They are honest labels: `spec.` says "unresolved",
   `UBA10200` says "this is a genome".
3. **Nothing in the list is an individual mistake.** I went looking for some and
   found none — that check is done, and it is worth recording that it came back
   clean rather than assumed.

## Related

- `docs/reports/name-parser.md` — where these counts come from, and why the
  check reads the parser's verdict rather than a regex.
- `docs/reports/duplicate-genus-names.md` — the jellyfish file, which was the
  one case where an unresolved-looking name *was* a filing error.
- `BACKLOG.md`, "Micro-phyla scaffolding" — the same problem in a different
  place: manual taxonomy treatment for groups with no usable source. Archaea is
  the largest instance of it.