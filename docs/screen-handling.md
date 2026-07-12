# Screen Handling

Interaction patterns for touch screens and desktop (mouse/keyboard) in the D3 tree visualisation.

## Touch Screen

- **Pinch zoom** — handled by D3 zoom behaviour.
- **Two-finger rotate** — radial layout rotates with a twist gesture.
- **Long-press tooltip** — 500ms hold on a node opens its tooltip (see [`Tooltip.md`](./Tooltip.md)).

## Desktop / Computer Screen

| Action | Trigger | Where |
|---|---|---|
| Zoom in / out | Mouse wheel | D3 zoom in [`FamilyTree.tsx`](../../shared/src/components/FamilyTree.tsx) |
| Center on selected node | `C` or `Home` | `App.tsx:311` — sets `pendingZoomId` to the selected node |
| Rotate radial tree CCW | `Q` | `App.tsx:319` — `setTreeRotation(r => r - 15°)` |
| Rotate radial tree CW | `E` | `App.tsx:324` — `setTreeRotation(r => r + 15°)` |
| Sibling nav | `ArrowLeft` / `ArrowRight` | `App.tsx` keyboard handler |
| Parent nav | `ArrowUp` | `App.tsx` keyboard handler |
| Collapse family / class | `Escape` | `App.tsx` keyboard handler |

`treeRotation` is passed into `FamilyTree.tsx`, which offsets `rotationRad` on link paths, node positions, text anchors, click anchors, and zoom targets — so every interaction stays consistent with the rotated layout.

## Backlog

- [ ] **Improve genus-centering zoom** — refine zoom scale/level when `C`-centering on genus nodes (currently can be too tight).

## Related

- [`navigation.md`](./navigation.md) — zoom anchor and stay-in-place behaviour.
- [`Tooltip.md`](./Tooltip.md) — long-press and keyboard tooltip details.
