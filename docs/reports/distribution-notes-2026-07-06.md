# Distribution Field Notes (2026-07-06)

## What exists

A structured `distribution` field (native geographic range, as curated text) on
plant species nodes. Type: `distribution?: string` on the shared `TaxonNode`.

Example: *Zephyranthes brachyandra* → `"E. Bolivia to WC. Brazil and N. Argentina"`.

### Coverage
- **5,052** POWO-enriched species — backfilled by parsing POWO's curated
  `taxonRemarks` out of the description prose (the reconstruction template
  "The native range of this species is X.").
- **~46** web-search / NZPCN species carry range info inside their prose but were
  not auto-parsed into the field (freeform text, too varied to parse reliably).
- **~89k** Wikipedia / GBIF species have **no** `distribution` field.

## How it's produced going forward
`tools/powo_enrich.py` now returns `{text, distribution}` per taxon and writes
`distribution` structurally (from `taxonRemarks`) alongside the description.
Legacy fields-cache entries (bare strings) are handled for backward compat.

## Why we did NOT store TDWG location codes
POWO's `/api/2/taxon/{ipni}?fields=distribution` returns a raw `locations` array
of TDWG codes. We evaluated storing them as `distributionCodes` and rejected it:

- **Noisy / bloated:** ~277 codes for *Acorus calamus* (97 even after filtering to
  L3 botanical-country `[A-Z]{3}` codes); narrow-range species are small but weedy
  ones explode.
- **Level-mixed:** the array mixes TDWG L1 continents (`AFRICA`), L3 countries
  (`TEX`), and L4 subdivisions (`IND_WB`, `_OO`) in one flat list.
- **Native + introduced conflated:** the list is the full occurrence range, not the
  native range, so it misrepresents "distribution".

Conclusion: the curated native-range **string** is the accurate, compact signal;
the code dump is low-value bloat. Tool `powo_dist_codes.py` was removed.

## Open item — uniform coverage
To give distribution to the ~89k wiki/gbif species (which lack it), POWO's
`taxonRemarks` could be fetched for them via the existing cached IPNI bridge
(binomial → gbif usageKey → IPNI → POWO). This is cheap (IPNI cache already has
~90k entries) and would not change their `sourcedFrom` — `distribution` is
additive metadata, independent of the description source.

If pursued: reuse `tools/powo_enrich.py`'s bridge/caches but target
`sourcedFrom in {wikipedia, gbif}` species with an empty `distribution`, write
only the `distribution` field (leave description/sourcedFrom untouched).
