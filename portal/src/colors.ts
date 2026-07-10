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
  
  // Cnidaria
  scyphozoa:      "#9D4EDD",
  cubozoa:        "#00B4D8",
  staurozoa:      "#1B4D3E",
  anthozoa:       "#F26419",
  hydrozoa:       "#4361EE",

  // Ctenophora
  tentaculata:    "#30A0B0",
  nuda:           "#2C82C9"
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

function hslToHex(h: number, s: number, l: number): string {
  const a = s * Math.min(l, 100 - l) / 100;
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color / 100).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(4)}${f(8)}`;
}

// Generate a class palette dynamically from the taxonomy tree.
// Known animal classes keep their hardcoded colors; unknown classes get
// a golden-angle hue distribution for visual separation.
// Always produces hex colors so downstream orderColor parsing works.
export function buildClassPaletteFromTree(root: TaxonNode): ClassPalette {
  const base: Record<string, string> = { ...CLASS_PALETTE };
  const seen = new Set<string>();
  let idx = 0;
  function walk(node: TaxonNode) {
    if (node.rank === "CLASS") {
      const key = node.name.toLowerCase();
      seen.add(key);
      if (!base[key]) {
        const hue = Math.round((idx * 137.508) % 360);
        base[key] = hslToHex(hue, 55, 45);
        idx++;
      }
    }
    for (const child of node.children ?? []) walk(child);
  }
  walk(root);
  return { base, orders: orderColorCache };
}

export function getClassColor(className?: string, palette?: Record<string, string>): string {
  if (!className) return TARDIGRADA_COLOR;
  const key = className.toLowerCase();
  if (palette) return palette[key] ?? TARDIGRADA_COLOR;
  return CLASS_PALETTE[key] ?? TARDIGRADA_COLOR;
}

export function getOrderColor(className: string, orderName: string, palette?: Record<string, string>): string {
  const key = `${className.toLowerCase()}/${orderName.toLowerCase()}`;
  if (orderColorCache[key]) return orderColorCache[key];
  const cls = className.toLowerCase();
  const classColor = (palette ? palette[cls] : undefined) ?? CLASS_PALETTE[cls] ?? TARDIGRADA_COLOR;
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
