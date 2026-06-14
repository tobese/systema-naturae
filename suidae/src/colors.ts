import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#C49A7A";

export const LINEAGE_COLORS: Record<string, string> = {
  "Pig":        "#C87050",
  "Pygmy Hog":  "#A0784A",
  "Babirusa":   "#C89050",
  "Warthog":    "#8B7340",
  "Forest Hog": "#5A7A50",
  "Bushpig":    "#B04040",
};

export const SUIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#B87860",
};
