import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#C8B896";

export const LINEAGE_COLORS: Record<string, string> = {
  "Sheep":          "#C4A882",
  "Goat":           "#C8A030",
  "Blue Sheep":     "#6B8FA8",
  "Chamois":        "#A0522D",
  "Musk Ox":        "#6A5040",
  "Mountain Goat":  "#9EA8A0",
  "Tahr":           "#8B7030",
  "Goral":          "#6B7C4A",
  "Serow":          "#607B8B",
  "Takin":          "#C8963C",
  "Chiru":          "#9B82BB",
  "Barbary Sheep":  "#B8794A",
};

export const CAPRINAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#B8A060",
};
