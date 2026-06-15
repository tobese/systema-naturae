import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#A08050";

export const LINEAGE_COLORS: Record<string, string> = {
  "Cattle":  "#C8973A",
  "Zebu":    "#B07840",
  "Buffalo": "#607858",
  "Bison":   "#704830",
};

export const BOVIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#C09060",
};
