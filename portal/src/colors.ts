import type { TaxonNode, ColorTheme, ClassPalette } from "@shared/types";
import type { PortalNode } from "./types";

// CLASS-level base colors — used as edge/fill for all nodes at/below each class.
// Order colors are derived by shifting lightness/saturation within the class hue.
export const CLASS_PALETTE: Record<string, string> = {
  mammalia:       "#C87941",
  aves:           "#3A8090",
  reptilia:       "#4A8C5C",
  chondrichthyes: "#5A78A0",
  amphibia:       "#7CB84A",
  actinopterygii: "#3A8FA8",
  insecta:        "#C8A830",
  arachnida:      "#A84868",
  asteroidea:     "#E87040",
  echinoidea:     "#40A888",
  holothuroidea:  "#A070C8",
};

// Tardigrada has no CLASS — use a neutral slate.
export const TARDIGRADA_COLOR = "#7A7050";

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function rgbToHex(r: number, g: number, b: number): string {
  const clamp = (n: number) => Math.max(0, Math.min(255, Math.round(n)));
  return "#" + [r, g, b].map(n => clamp(n).toString(16).padStart(2, "0")).join("");
}

// Generate an ORDER color by darkening/desaturating the CLASS base.
// Each order gets a unique offset based on its name hash.
function orderColorFromClass(classColor: string, orderName: string): string {
  const [r, g, b] = hexToRgb(classColor);
  const hash = orderName.split("").reduce((s, c) => s + c.charCodeAt(0), 0);
  const shift = (hash % 40) - 20; // -20..+19
  const factor = 1 + shift / 100; // 0.8..1.19
  return rgbToHex(r * factor, g * factor, b * factor);
}

const orderColorCache: Record<string, string> = {};

export function buildClassPalette(): ClassPalette {
  const base: Record<string, string> = { ...CLASS_PALETTE };
  return { base, orders: orderColorCache };
}

export function getClassColor(className?: string): string {
  if (!className) return TARDIGRADA_COLOR;
  return CLASS_PALETTE[className.toLowerCase()] ?? TARDIGRADA_COLOR;
}

export function getOrderColor(className: string, orderName: string): string {
  const key = `${className.toLowerCase()}/${orderName.toLowerCase()}`;
  if (orderColorCache[key]) return orderColorCache[key];
  const cls = className.toLowerCase();
  const classColor = CLASS_PALETTE[cls] ?? TARDIGRADA_COLOR;
  const color = orderColorFromClass(classColor, orderName);
  orderColorCache[key] = color;
  return color;
}

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

// Legacy version used by old portal (propagates through all descendants).
export function annotatePortalTree(node: PortalNode, className?: string, orderName?: string): PortalNode {
  const nextClass = node.rank === "CLASS" ? node.name : className;
  const nextOrder = node.rank === "ORDER" ? node.name : orderName;
  return {
    ...node,
    lineage: nextOrder ?? nextClass,
    children: node.children?.map(c => annotatePortalTree(c, nextClass, nextOrder)),
  };
}

// Family-level-aware version: stamps lineage on CLASS/ORDER/FAMILY nodes only.
// Nodes at SUBFAMILY rank and below already carry their own lineage from the family JSON.
const SPECIES_LEVEL_RANKS = new Set([
  "SUBFAMILY", "TRIBE", "GENUS", "SPECIES", "SUBSPECIES",
  "BREED_GROUP", "BREED", "HYBRID_GROUP", "HYBRID",
]);

export function annotatePortalLevels(node: TaxonNode, className?: string, orderName?: string): TaxonNode {
  const nextClass = node.rank === "CLASS" ? node.name : className;
  const nextOrder = node.rank === "ORDER" ? node.name : orderName;
  const lineage = SPECIES_LEVEL_RANKS.has(node.rank) ? node.lineage : (nextOrder ?? nextClass);
  return {
    ...node,
    lineage,
    children: node.children?.map(c => annotatePortalLevels(c, nextClass, nextOrder)),
  };
}
