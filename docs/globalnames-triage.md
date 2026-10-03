# GlobalNames triage

[globalnames.org/apps/](https://globalnames.org/apps/) is a toolkit rather than a
dataset, so this is an assessment of the individual applications against problems
this project actually has. Two were adopted, one is unusable, and the rest do not
apply.

## Adopted

### GNparser — `scripts/taxamatch.py` uses it to atomize names

A Go parser that splits a scientific name into canonical form, authorship, year,
rank marker and **cardinality** (1 = genus, 2 = binomial, 3 = trinomial), with a
quality flag. It handles three things our own `parseAllNames.py` does not:
subgenus parentheses (`Lasioglossum (Ctenonomia) ernesti Pauly, 1990` →
`Lasioglossum ernesti`), the `†` fossil marker, and rank cardinality. It parses
about 50,000 names a second.

Install: `go install github.com/gnames/gnparser/gnparser@latest`. It lands in
`$GOPATH/bin`, which is usually not on `PATH`; `taxamatch.py` looks there.

### Taxamatch + Damerau-Levenshtein — `scripts/taxamatch.py`

Tony Rees' Taxamatch decides whether two name strings denote the same taxon. Its
distance function is not the ordinary Damerau variant: it allows a **block** of
up to `block_size` characters to transpose with its neighbour at a cost of 1,
after Boehmer & Rees 2008. That suits taxonomic names, where a misspelling is
often a multi-character transposition — `Pseudorhynchus` against
`Pseudoryhnchus` scores 1 rather than the 2 plain Levenshtein gives.

Ported to Python rather than called from Ruby, because this is a Python codebase
and a subprocess per name pair is not viable at 1.3M names.

`scripts/validateTaxamatch.py` checks the port against the gems
(`gem install taxamatch_rb damerau-levenshtein`) on real names from the tree:

```
  distance agreement: 1,500/1,500 (100.00%)
  decision agreement: 1,495/1,500 (99.67%)
```

Distances are exact. The five decision differences are all cases where an
insertion lands immediately before the authorship, and they come from the
**atomizer**, not the port: the gems use the `biodiversity` gem's Treetop grammar
while this uses GNparser, and the two disagree about where a name ends and its
authorship begins. Every one is a corrupted pair, where the verdict is a
judgement call anyway.

Two deliberate deviations, both in the C's disfavour: the extension reads outside
its arrays near the ends of the matrix and relies on a later guard to discard the
result, and the port bounds those reads instead. Distances are unaffected.

**Use it to propose, not to merge.** Fuzzy species matching is for finding
*candidates* — a near-duplicate worth a human look, or a synonym candidate for
the reconciliation backlogs. It should not silently collapse two names, because
near-identical spellings sometimes denote genuinely distinct taxa.

## Not usable

### ZooBank

The ICZN Official Register, and the most valuable thing on the page: a
nomenclatural authority for animal names, which we have no equivalent for. It is
behind a human-verification wall, asking callers to confirm they are not a robot
because of "extremely high demand" and volume from automated traffic.

Not workable for bulk lookup against ~1M animal names, and hammering a service
that has asked not to be hammered is not the trade. Revisit if ZooBank publishes
a bulk dump.

## Not applicable

**GNRD / GNITE / BioGUID / GN UUID / BiblioSpotter** — OCR name discovery, a stalled
community editor, an identifier registry, deterministic name UUIDs, and a citation
browser extension. None bears on name matching, coverage or import.

## What this turned up instead

Cross-checking against GNparser exposed a live bug in `scripts/canonicalNames.py`.
Its index is keyed `name.lower()`, but `lookup()` probed that table with the
caller's string unchanged — and every scientific name is mixed case, so **no
caller ever got a hit**. The failure is silent: no exception, no warning, just a
lookup that never matches. It is why the iNaturalist import first filled zero
names, and why Mammal Species of the World measured as 100% new when 3,762 of our
7,900 mammal species are in it. Both probes are lowercased now.
