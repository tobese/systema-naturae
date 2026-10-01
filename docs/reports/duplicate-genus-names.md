# One genus name, two families: 1,208 cases, and why almost none can be merged

## Summary

Auditing duplicate ids after the case-variant merge turned up a much larger set,
and the honest answer is that **almost none of it is a bug to fix**.

| | count |
|---|---|
| duplicate ids tree-wide | 1,467 |
| across two kingdoms (homonyms, expected) | 749 |
| same kingdom | 718 |
| — of those, same genus name in more than one family | **466** |
| —— with overlapping species (genuine duplication) | **35** |
| —— with disjoint species (two distinct taxa) | **431** |

The 749 cross-kingdom ones are the 7 already documented in `BACKLOG.md` plus
their genus-level equivalents, and they are correct: ids derive from binomials,
and binomials are not unique across kingdoms. Nothing to do.

The 466 are the interesting ones, and **they are not 466 bugs.**

## Why they cannot be merged

The instinct is "the same genus listed twice, merge them" — which is exactly what
`merge_duplicate_genera.py` does, correctly, for 12 families. It does not
transfer, because these are not duplicate *nodes*. They are two nodes with the
same name in two families, and whether that is a defect depends entirely on
whether one genus has been split across two families or two unrelated taxa
happen to share a name. Both cases look identical in the data.

The examples are unambiguous in both directions:

**Homonyms — two real, unrelated taxa.** `Palmophyllum` is a red alga with 3
species in Palmophyllaceae, and a palm with 2 species in Arecaceae. GBIF returns
`EXACT`/`ACCEPTED` for *both* `Palmophyllum crassum` and `Palmophyllum
dakshinense`, because both are validly published names for different organisms.
Merging them would put a palm inside an algal family.

**One genus split across families — same taxon, wrongly divided.** `Gloeotila`
has 8 species in Chlorellaceae and 2 in Ulotrichaceae; `Willea` has 7 in
Oocystaceae and 2 in Scenedesmaceae. The species are disjoint in both cases, so
this looks exactly like the homonym case — but GBIF resolves all four names
`EXACT`/`ACCEPTED` in Chlorophyceae, and they are one genus.

**Nothing in the local data distinguishes these.** Disjointness is the only
signal, and it is 50/50: it is what a homonym looks like *and* what a
mis-split genus looks like. Deciding needs the external taxonomy the local data
does not contain, which is the same wall the Catalogue of Life ran into for the
1,456 Wikipedia collisions — `Acanthispa lateralis` and `Acanthodes lateralis`
are a beetle and a fish, both accepted, and only COL's `status` field
distinguishes them.

## The 35: resolved, and they were not 35 taxonomy errors

The 35 overlapping-species cases are entirely **one file**.

`taxonomy/animalia/priapulida/halicryptomorpha/halicryptomorpha/halicryptidae/`
holds four scyphozoan **jellyfish** — `Chrysaora` (22 spp), `Pelagia` (9),
`Mawia` (1), `Sanderia` (2) — each duplicated from `Pelagiidae` with identical
`GENUS_*` and species ids. Their own generated descriptions read "a genus of
pelagiid jellyfish", which contradicts the family they sit in. `Halicryptomorpha`
is a class of priapulid **worms**; this directory is where its order belongs.

Removed by `scripts/fixMisfiledOrderFamilies.py`.

**And the same investigation nearly caused a much worse mistake.** Three other
files sit at `<order>/<order>/` with `rank: "FAMILY"` and look identical from the
outside:

| file | genera | species found nowhere else |
|---|---|---|
| `lamniformes.json` | 71 | **193** |
| `orectolobiformes.json` | 47 | **164** |
| `cetacea.json` | 2 | **92** |

A first version of that script classified all four as misfiled order-level
duplicates and would have deleted **449 species**. They are not misfiled: they are
real families that happen to share their order's name —

    Chondrichthyes > Lamniformes      (order)
                    > Lamniformes    (family, "Mackerel sharks", 320 species)
                    > Lamnidae       (family)

— a family named after its order, which is unremarkable. The only reason this was
caught is that the script refuses to delete a file holding species that exist
nowhere else, and all three were refused. The premise was wrong, not the code.

## Recommendation

Do not run a merge across this set. The 35 are done (one file, removed). The 431
are a taxonomy decision per name and would need an external authority per case,
which is the same cost as the MycoBank token request and with a much worse
cost/benefit — the affected species are a few thousand out of 1.2M, whereas the
MycoBank question governs 157,690.

Worth noting the counter-argument: if `Gloeotila` really is one genus split
across two families, that is a *taxonomy* error in the source data, visible to a
reader browsing Chlorellaceae and Ulotrichaceae. It is a real defect, just not
one a script can safely repair.

## Related

- `mergeCaseVariantGenera.py` — handled the 2 (plus 1 all-caps) cases where the
  names differed *only* in case and so were unambiguously the same node. That
  fix is safe precisely because casefolding the name cannot merge two real taxa
  that were never meant to be one.
- `fixMisfiledOrderFamilies.py` — removed the jellyfish file. Read its docstring
  for the three lookalikes it refuses, because that is the useful part.
- The remaining 224 `SPECIES_ID_REPEATED` are the pre-existing cross-family
  species overlaps (`Cincloramphus` in Acanthizidae *and* Locustellidae,
  `Poodytes` in both, 127 in Lamnidae+Lamniformes) — the "301 ids at more than one
  position" class already recorded in `BACKLOG.md`. Not touched here.