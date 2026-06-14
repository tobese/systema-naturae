import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#9B8868";
export const HYBRID_COLOR = "#C8A050";

export const LINEAGE_COLORS: Record<string, string> = {
  "Horse": "#C8973A",
  "Ass":   "#A07848",
  "Zebra": "#6B92A8",
};

export const EQUIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: HYBRID_COLOR,
};
