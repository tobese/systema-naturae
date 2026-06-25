# Wheel of Nature

A fun discovery feature: a **Tivoli-style spinning wheel** that randomly selects a species and opens its detail panel.

## Visual Design

- **12 sectors** arranged in a circle, each representing a different taxonomic class (or a broad category like Mammals, Birds, Reptiles, etc.).
- **Outer rim pins** — physical-looking pegs that create a ticking sensation.
- **Flexible flapper / pin** — a rubbery pointer that bounces against the pins as the wheel spins.
- **Sound** — a subtle clicking/ticking audio loop while spinning (optional, muted by default).

## Mechanics

1. User clicks **"Spin"**.
2. Wheel accelerates, spins for a few seconds, then decelerates.
3. The flapper settles on one sector.
4. The system picks a **random species** from that class (or from the whole tree weighted by class).
5. The **side panel opens** for the winning species, showing its image and summary.
6. A **"Spin again"** button appears.

## Win Condition Details

| Aspect | Proposal |
|--------|----------|
| Randomisation | Uniform across all species, or weighted by class size |
| Image | Wikipedia thumbnail via `useWikipediaSummary` (same as `UnifiedInfoPanel`) |
| Panel | Re-use `UnifiedInfoPanel` with the selected species node |
| Re-spin | Button at the bottom of the panel or floating action button |

## Files to Touch

| File | Change |
|------|--------|
| `portal/src/App.tsx` | Add wheel state, spin handler, open panel on result |
| `portal/src/components/WheelOfNature.tsx` | New component — canvas or SVG wheel animation |
| `portal/src/components/UnifiedInfoPanel.tsx` | No changes needed if fed a species node |
| `portal/public/sounds/` | Optional — tick audio asset |

## Open Questions

- Should the wheel be a modal overlay or a floating widget?
- Should we cache the "last win" per session so the same species doesn't repeat immediately?
- Is the sound essential, or can it be MVP'd without audio?

## Related

- [`Tooltip.md`](./Tooltip.md) — species preview patterns.
- [`Statistics header.md`](./Statistics%20header.md) — lineage display in side panel.
