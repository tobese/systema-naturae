# Screen Handling

Interaction patterns for touch screens and desktop (mouse/keyboard) in the D3 tree visualisation.

## Touch Screen

- **Multi-finger zoom** — pinch to zoom in/out of the tree.
- **Two-finger rotate** — rotate the radial layout with a twist gesture.

## Desktop / Computer Screen

- **Zoom** — driven by the mouse wheel (handled by D3 zoom behaviour in [`FamilyTree.tsx`](../../shared/src/components/FamilyTree.tsx)).
- **Center on current node** — *not yet implemented.*
- **Rotate tree** — *not yet implemented.*

> **Open question:** Should rotation be a button in the [OptionsPanel](../../portal/src/components/OptionsPanel.tsx) or a key shortcut (e.g. `R`)?

## Related

- See [`navigation.md`](./navigation.md) for zoom anchor and stay-in-place behaviour.
