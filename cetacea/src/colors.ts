import type { ColorTheme } from "@shared/types";

export const LINEAGE_COLORS: Record<string, string> = {
  "Right whales":  "#2196a6",
  "Rorquals":      "#1565c0",
  "Gray whale":    "#546e7a",
  "Sperm whales":  "#6a1b9a",
  "Beaked whales": "#37474f",
  "Dolphins":      "#0288d1",
  "Porpoises":     "#00838f",
  "Monodontidae":  "#00acc1",
  "River dolphins": "#2e7d32",
};

export const SUBFAMILY_COLORS: Record<string, string> = {
  Mysticeti:  "#1a6b8a",
  Odontoceti: "#0d4f6e",
};

export const CETACEA_THEME: ColorTheme = {
  subfamilyColors: SUBFAMILY_COLORS,
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: "#607d8b",
  hybridColor: "#90a4ae",
};
