import type { ColorTheme } from "@shared/types";

export const LINEAGE_COLORS: Record<string, string> = {
  "Giraffe": "#C8A040",
  "Okapi":   "#7B5C3A",
};

export const GIRAFFIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: "#888",
  hybridColor: "#C8A050",
};
