import type { ColorTheme } from "@shared/types";

export const LINEAGE_COLORS: Record<string, string> = {
  "Red deer":     "#C87030",
  "Fallow deer":  "#B09040",
  "Sambar":       "#A07040",
  "Muntjac":      "#906858",
  "Roe deer":     "#5A9060",
  "Moose":        "#3A6890",
  "Reindeer":     "#5878A8",
  "American deer":"#6B8870",
  "Water deer":   "#4A9090",
};

export const SUBFAMILY_COLORS: Record<string, string> = {
  Cervinae:    "#C87030",
  Capreolinae: "#3A6890",
};

export const CERVIDAE_THEME: ColorTheme = {
  subfamilyColors: SUBFAMILY_COLORS,
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: "#888",
  hybridColor: "#888",
};
