import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#7A9878";

export const LINEAGE_COLORS: Record<string, string> = {
  "Swan":          "#B0C0D0",
  "Goose":         "#8A9870",
  "Dabbling Duck": "#3A8090",
  "Diving Duck":   "#3A5080",
  "Eider":         "#607888",
  "Merganser":     "#4A7060",
  "Perching Duck": "#4A7840",
  "Stifftail":     "#706040",
  "Shelduck":      "#A07840",
  "Teal/Other":    "#507070",
};

export const ANATIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: "#608878",
};
