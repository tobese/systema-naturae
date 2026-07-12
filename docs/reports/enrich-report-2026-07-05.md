# Enrichment Report — 2026-07-05

## Final Plant Stats (Magnoliopsida + Liliopsida)

| sourcedFrom | Count |
|---|---|
| wikipedia | 75,360 |
| gbif | 13,675 |
| none | 292,691 |
| missing | 9,304 |
| **Total** | **391,030** |

## What Happened

- Stripped `sourcedFrom: "generated"` and auto-generated placeholder descriptions from **9,304** plant species across 167 files.
- Ran enrichServe with **2,811** new pool candidates (stripped entries with binomial-compliant names).
- **137** matched Wikipedia (SQLite pass).
- **2,674** processed by local GBIF workers → **2,655** got GBIF descriptions ("gbif"), **19** got none ("none").
- Queue fully drained (0 queued, 0 leased).

## Remaining Issues

- **6,493** stripped entries never entered the pool — the pool-building regex `/^[A-Z][a-z]+ [a-z-]+/` (`BINOMIAL_RE`) rejects hybrid names containing `×` (e.g., "Escallonia ×bracteata Phil.").
- These ~6.5k species have no `sourcedFrom` and no description, and were silently excluded from both enrichment runs. Fix `BINOMIAL_RE` to accommodate hybrid markers and re-run if GBIF coverage is desired.
