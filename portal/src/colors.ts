import type { ColorTheme } from "@shared/types";
import type { PortalNode } from "./types";

export const PORTAL_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    Mammalia:       "#C87941",
    Aves:           "#3A8090",
    Carnivora:      "#D4873A",
    Perissodactyla: "#C89050",
    Artiodactyla:   "#8B7340",
    Galliformes:    "#2E9E8C",
    Anseriformes:   "#3A6090",
  },
  breedGroupColor: "#888",
  hybridColor: "#888",
};

export function annotatePortalTree(node: PortalNode, className?: string, orderName?: string): PortalNode {
  const nextClass = node.rank === "CLASS" ? node.name : className;
  const nextOrder = node.rank === "ORDER" ? node.name : orderName;
  return {
    ...node,
    lineage: nextOrder ?? nextClass,
    children: node.children?.map(c => annotatePortalTree(c, nextClass, nextOrder)),
  };
}
