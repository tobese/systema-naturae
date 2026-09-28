import type { ColorTheme } from "@shared/types";

export const BREED_GROUP_COLOR = "#7B6FA0";
export const HYBRID_COLOR = "#C8A050";
export const COAT_TYPE_COLOR = "#5DB8C4";

export const SUBFAMILY_COLORS: Record<string, string> = {
  Pantherinae: "#E8A030",
  Felinae: "#2E9E8C",
};

export const LINEAGE_COLORS: Record<string, string> = {
  "Bay cat":        "#5B8DD9",
  "Caracal":        "#C45AB3",
  "Ocelot":         "#E05C5C",
  "Lynx":           "#4CB8C4",
  "Puma":           "#E0963C",
  "Leopard cat":    "#7CB87C",
  "Domestic cat":   "#A09CDC",
};

export const FELIDAE_THEME: ColorTheme = {
  subfamilyColors: SUBFAMILY_COLORS,
  lineageColors: LINEAGE_COLORS,
  breedGroupColor: BREED_GROUP_COLOR,
  hybridColor: HYBRID_COLOR,
  coatTypeColor: COAT_TYPE_COLOR,
};

export function nodeColor(name: string, rank: string, lineage?: string): string {
  if (rank === "FAMILY") return "#F0F0F0";
  if (name === "Pantherinae" || rank === "SUBFAMILY" && name.includes("Panther")) return SUBFAMILY_COLORS.Pantherinae;
  if (name === "Felinae") return SUBFAMILY_COLORS.Felinae;
  if (lineage && LINEAGE_COLORS[lineage]) return LINEAGE_COLORS[lineage];
  if (rank === "GENUS") return "#A0B8D0";
  return "#D0D0D0";
}

export function subfamilyColorForNode(ancestorSubfamily?: string): string {
  if (!ancestorSubfamily) return "#888";
  return SUBFAMILY_COLORS[ancestorSubfamily] ?? "#888";
}
