import { createContext } from "react";

export interface BookOptions {
  showExtinct: boolean;
  toggleShowExtinct: () => void;
  // Reveals unenriched ("stub") species - the plain "Also in this genus:
  // ..." name list that otherwise never gets its own SpeciesEntry.
  showStubs: boolean;
  toggleShowStubs: () => void;
  // Reveals families with zero enriched species (chapterStats.enrichedCount
  // === 0) - otherwise they're hidden from both the chapter body and the
  // Contents page entirely, rather than showing an empty-looking section.
  showEmptyFamilies: boolean;
  toggleShowEmptyFamilies: () => void;
  // Hides stored descriptions shorter than minDescriptionLength. Wikipedia's
  // long tail is mostly stub leads - "Acronia gloriosa is a species of beetle in
  // the family Cerambycidae" restates the family the chapter header already
  // says. The import gate (validateNamesWithCol.py, MIN_LEAD) stops new ones
  // arriving; this hides the ones already stored, in the surface where they are
  // most visible because it is where they appear in sequence.
  hideThinDescriptions: boolean;
  toggleHideThinDescriptions: () => void;
  minDescriptionLength: number;
  setMinDescriptionLength: (n: number) => void;
}

export const BookOptionsContext = createContext<BookOptions | null>(null);
