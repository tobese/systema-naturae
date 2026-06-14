import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#C0A060";

export const LINEAGE_COLORS: Record<string, string> = {
  "Junglefowl": "#C89040",
  "Turkey":     "#A06030",
  "Peacock":    "#3A8080",
  "Pheasant":   "#B06030",
  "Quail":      "#A09060",
  "Partridge":  "#806040",
  "Grouse":     "#607060",
  "Spurfowl":   "#805050",
};

export const PHASIANIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#B09050",
};
