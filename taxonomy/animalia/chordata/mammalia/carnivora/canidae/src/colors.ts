import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#8B7BA0";
export const HYBRID_COLOR = "#C8A050";

export const SUBFAMILY_COLORS: Record<string, string> = {
  Caninae: "#D4873A",
};

export const LINEAGE_COLORS: Record<string, string> = {
  "Wolf":           "#C87941",
  "Fox":            "#E05C5C",
  "South American": "#2E9E8C",
  "Raccoon dog":    "#5B8DD9",
};

export const CANIDAE_THEME: ColorTheme = {
  subfamilyColors: SUBFAMILY_COLORS,
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#C8A050",
};
