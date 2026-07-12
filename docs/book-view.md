# Book View — alternative taxonomy browser

Toggle alongside the graph for a text-driven, hierarchical reading experience.

## Concept

The tree is rendered as nested expandable sections (think `<details>` or side-nav), not a force-directed graph. Each rank maps to a heading level:

```
KINGDOM Animalia
  Part I — Mammalia
    Chapter 1 — Carnivora
      Felidae (41 species)
        1.1 Felinae
          Felis catus — Domestic cat
          Panthera leo — Lion
          …
      Canidae (37 species)
        …
    Chapter 2 — Artiodactyla
      …
  Part II — Aves
    …
```

## Details per node

- **Class / Order**: a short auto-generated or curated paragraph (origin, diversity, key traits)
- **Family**: species count, geographic range, common name
- **Genus**: number of species, representative species list
- **Species**: common name, description, namedAfter, continents, subspecies count

## Interaction

- Bookmarks / anchor links per section (`#mammalia/carnivora/felidae`)
- Breadcrumb at the top
- Search highlights the section in the book
- Clicking a species opens the same InfoPanel as the graph
- Collapse/expand all toggles

## Implementation sketch

- `BookView.tsx` in `shared/src/components/` — reads the same unified taxonomy data
- Renders recursively using `<details>` + `<summary>` for each non-species node
- Species rendered as compact list items
- Optional: lazy-load deeper levels if performance is an issue (unlikely at 55k nodes)
- Styled with the same CSS variables / ColorTheme as the tree

## Open issues (taxonomy sidebar inspired this)

- **PHYLUM level**: 3 phyla exist (Chordata, Arthropoda, Tardigrada) but CLASS is the more intuitive entry point. Tardigrada has no CLASS, so skipping PHYLUM puts it awkwardly at the KINGDOM level. Decide whether to show/hide/bridge PHYLUM in sidebar and book view.
- **name vs commonName**: Higher ranks (CLASS–FAMILY) inconsistent — some render Latin (`Mammalia`), others English (`Mammals`). Propose: KINGDOM–FAMILY show `commonName` primary with `name` secondary; GENUS–SPECIES show `name` (Latin) only.

## Stretch

- AI-generated chapter summaries per Class / Order (one-time, stored in a JSON)
- Illustrations or range maps inline at the Class / Family level
- Print-friendly stylesheet
