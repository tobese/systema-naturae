// Hand-curated collage placements for flagship Parts, keyed by className.
// `center` is pinned to the exact middle of the 9x9 grid (index 40 of 81,
// row-major); `pinned` fills other slots before the remaining grid is
// auto-filled from real, image-bearing enriched species (see
// extractSlice.ts's buildCollage()). All picks are verifiable real-world
// facts, not fabricated - see README.md for the source check against the
// actual portal data (every name below was confirmed to exist with a real
// portrait image before being added here).
export const COLLAGE_OVERRIDES: Record<string, { center?: string; pinned?: string[] }> = {
  Mammalia: {
    center: "Homo sapiens",
    pinned: [
      "Gorilla gorilla", // largest living primate
      "Balaenoptera musculus", // blue whale - largest animal ever known
      "Suncus etruscus", // Etruscan shrew - smallest mammal by mass
      "Giraffa camelopardalis", // tallest living animal
      "Acinonyx jubatus", // cheetah - fastest land mammal
      "Loxodonta africana", // African bush elephant - largest land animal
      "Physeter macrocephalus", // sperm whale - deepest-diving mammal
    ],
  },
  Aves: {
    // No natural "center" analog for birds the way Homo sapiens centers
    // Mammalia - pinned record-holders only, rest auto-filled.
    pinned: [
      "Struthio camelus", // ostrich - largest/heaviest living bird
      "Mellisuga minima", // vervain hummingbird - among the smallest living birds
      "Falco peregrinus", // peregrine falcon - fastest animal alive (diving)
      "Diomedea exulans", // wandering albatross - largest wingspan of any living bird
      "Haliaeetus leucocephalus", // bald eagle - iconic raptor
      "Corvus corax", // common raven - most intelligent bird
      "Sterna paradisaea", // Arctic tern - longest migration of any animal
      "Pavo cristatus", // Indian peafowl - iconic display
      "Aptenodytes forsteri", // emperor penguin - deepest-diving bird
      "Apteryx australis", // kiwi - flightless, unusual
    ],
  },
};
