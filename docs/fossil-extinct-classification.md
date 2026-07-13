# Fossil & Extinct Classification — Higher Ranks

**Status:** complete · **Date:** 2026-07-13 · **Scope:** PHYLUM / CLASS / ORDER across all 6 kingdoms

## Goal

Surface genuinely fossil / extinct higher-rank taxa (phyla, classes, orders) in the
portal so they are visually distinguishable from extant groups — without ever
fabricating a "fossil" or "extinct" label for a group that is still alive.

## Method

No text generation. Every decision is sourced from the curated taxonomy's own
`description` field (populated from Wikipedia REST summaries during enrichment) plus
the `†` prefix convention already used in the data.

Classified by `portal/scripts/classifyFossils.ts`, hardened and resumable:

- **Atomic writes** — flushes to `unified-taxonomy-<kingdom>.json` via a temp file +
  rename, so an interrupted run never leaves a half-written tree.
- **Per-node try/catch** — one bad node can't kill the whole pass.
- **Resume** — re-running skips nodes already explicitly marked `false`, but
  re-evaluates any node still `true`, `undefined`, or whose description mentions
  "fossil", so corrections propagate.
- **Conservative decision** — a node is flagged only on a *precise* signal:
  - the `†` prefix, or
  - a description whose subject is the rank itself and says it is "an extinct
    order/class/phylum of …", "known only from fossils", "entirely fossil", etc.
- **Guards reject ambiguity** — phrases like "extinct relatives", "fossil record",
  "fossil specimens", "fossil evidence" do **not** trigger a flag (those describe
  relatives or the rock record, not the group itself).
- **Higher-rank rule** — an `extinct` higher rank is also marked `fossil`
  (`extinct ⇒ fossil`); species-level extinct stays `extinct` only.

`buildData.ts` honors any explicit `extinct` / `fossil` it finds on a source node and
spreads the stamp to the whole subtree.

## Results

**13 higher-rank fossil/extinct groups — 0 false positives.**

| Kingdom | Rank | Name |
|---|---|---|
| animalia | ORDER | Cyrtonellida |
| animalia | ORDER | Kirengellida |
| animalia | ORDER | Hippuritida |
| animalia | ORDER | Modiomorphida |
| animalia | ORDER | Megalodontida |
| animalia | ORDER | Fordillida |
| animalia | ORDER | Tuarangiida |
| animalia | ORDER | Siphonotretida |
| animalia | ORDER | Trepostomatida |
| animalia | ORDER | Fenestrida |
| animalia | ORDER | Cryptostomida |
| animalia | ORDER | Cystoporida |
| plantae | ORDER | Sycidiales |

fungi / chromista / protozoa / archaea: none flagged.

All 13 are both `fossil` and `extinct` (extinct higher ranks are always also fossil).

## UI feature (this change)

Fossil / extinct status is now surfaced in the portal:

- **Tree marker** (`shared/src/components/FamilyTree.tsx`) — a `fossil-ring` stroke
  around any node with `fossil` or `extinct`: solid red (`#C95B6B`) for extinct,
  dashed amber (`#C89860`) for fossil-only.
- **Detail panel badge** (`portal/src/components/UnifiedInfoPanel.tsx`) — a
  `FOSSIL` / `EXTINCT` pill on Kingdom/Phylum/Class/Order/Genus panels.
- **Highlight toggle** — new "Highlight fossil / extinct" checkbox in the ⚙
  OptionsPanel (mirrors "Highlight Wikipedia species"); builds a `highlightedNodeIds`
  set in `useUnifiedTree` so fossil/extinct nodes pop when a family is focused.
- **Visible by default** — `showExtinct` / `showFossil` now default to **true** in
  `App.tsx` and `AppBare.tsx`, so the 13 fossil orders render with their rings out of
  the box; the toggles still hide them on demand.

## Files

- `portal/scripts/classifyFossils.ts` — classifier
- `portal/scripts/buildData.ts` — honors / spreads `extinct` / `fossil`
- `portal/data/kingdoms/<kingdom>/unified-taxonomy*.json` — stamped trees
- `portal/data/fossil-gap-report-<kingdom>.json` — coverage reports
- `shared/src/components/FamilyTree.tsx` — `fossil-ring`
- `portal/src/components/UnifiedInfoPanel.tsx` — `StatusBadges`
- `portal/src/components/OptionsPanel.tsx` — toggle + `highlightFossilExtinct` option
- `portal/src/hooks/useUnifiedTree.ts` — highlight set
- `portal/src/App.tsx` / `portal/src/AppBare.tsx` — defaults + wiring
