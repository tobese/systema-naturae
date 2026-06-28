# Wheel of Nature

A discovery feature: a **Tivoli-style spinning wheel** that randomly selects a species and opens its detail panel.

**Status:** Shipped — `portal/src/components/WheelOfNature.tsx`.

## What it does

1. Modal overlay with an SVG wheel divided into **12 class-coloured sectors** (one sector per class in the tree). Sector colours come from `CLASS_PALETTE` in `colorRegistry.ts`.
2. Outer rim pins + a "flapper" pointer that bounces against the pins as the wheel decelerates (CSS animation).
3. User clicks **"Spin"** → wheel accelerates, spins, decelerates, and the flapper settles on one sector.
4. A random species from that class is picked.
5. The right-hand `UnifiedInfoPanel` opens for the winning species via a **"View species"** button on the result card.
6. A **"Spin again"** button stays visible to keep the loop going.

## Files

| File | Role |
|---|---|
| `portal/src/components/WheelOfNature.tsx` | The modal + animated SVG wheel + random species picker. |
| `portal/src/components/UnifiedInfoPanel.tsx` | Re-used to display the selected species — no changes needed. |
| `portal/src/colorRegistry.ts` | `CLASS_PALETTE` provides the sector colours. |

## Backlog

- [ ] **Tick audio** — optional ticking/clicking sound while spinning (muted by default).
- [ ] **Avoid immediate repeats** — cache the last winner per session so the same species doesn't immediately come up twice.

## Related

- [`Tooltip.md`](./Tooltip.md) — species preview patterns.
- [`Statistics header.md`](./Statistics%20header.md) — lineage display in the side panel.
