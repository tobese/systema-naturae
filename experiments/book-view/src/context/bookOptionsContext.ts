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
}

export const BookOptionsContext = createContext<BookOptions | null>(null);
