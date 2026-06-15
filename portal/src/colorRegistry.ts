import type { TaxonNode, ColorTheme } from "@shared/types";
import { PORTAL_THEME } from "./colors";

// Per-family ColorTheme objects — values sourced from each sub-app's colors.ts
const FELIDAE_THEME: ColorTheme = {
  subfamilyColors: { Pantherinae: "#E8A030", Felinae: "#2E9E8C" },
  lineageColors: {
    "Bay cat": "#5B8DD9", "Caracal": "#C45AB3", "Ocelot": "#E05C5C",
    "Lynx": "#4CB8C4", "Puma": "#E0963C", "Leopard cat": "#7CB87C",
    "Domestic cat": "#A09CDC",
  },
  breedGroupColor: "#7B6FA0",
  hybridColor: "#C8A050",
  coatTypeColor: "#5DB8C4",
};

const CANIDAE_THEME: ColorTheme = {
  subfamilyColors: { Caninae: "#D4873A" },
  lineageColors: {
    "Wolf": "#C87941", "Fox": "#E05C5C",
    "South American": "#2E9E8C", "Raccoon dog": "#5B8DD9",
  },
  breedGroupColor: "#8B7BA0",
  hybridColor: "#C8A050",
};

const EQUIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { "Horse": "#C8973A", "Ass": "#A07848", "Zebra": "#6B92A8" },
  breedGroupColor: "#9B8868",
  hybridColor: "#C8A050",
};

const GIRAFFIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { "Giraffe": "#C8A040", "Okapi": "#7B5C3A" },
  breedGroupColor: "#888",
  hybridColor: "#C8A050",
};

const CAPRINAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Sheep": "#C4A882", "Goat": "#C8A030", "Blue Sheep": "#6B8FA8",
    "Chamois": "#A0522D", "Musk Ox": "#6A5040", "Mountain Goat": "#9EA8A0",
    "Tahr": "#8B7030", "Goral": "#6B7C4A", "Serow": "#607B8B",
    "Takin": "#C8963C", "Chiru": "#9B82BB", "Barbary Sheep": "#B8794A",
  },
  breedGroupColor: "#C8B896",
  hybridColor: "#B8A060",
};

const SUIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Pig": "#C87050", "Pygmy Hog": "#A0784A", "Babirusa": "#C89050",
    "Warthog": "#8B7340", "Forest Hog": "#5A7A50", "Bushpig": "#B04040",
  },
  breedGroupColor: "#C49A7A",
  hybridColor: "#B87860",
};

const PHASIANIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Junglefowl": "#C89040", "Turkey": "#A06030", "Peacock": "#3A8080",
    "Pheasant": "#B06030", "Quail": "#A09060", "Partridge": "#806040",
    "Grouse": "#607060", "Spurfowl": "#805050",
  },
  breedGroupColor: "#C0A060",
  hybridColor: "#B09050",
};

const ANATIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Swan": "#B0C0D0", "Goose": "#8A9870", "Dabbling Duck": "#3A8090",
    "Diving Duck": "#3A5080", "Eider": "#607888", "Merganser": "#4A7060",
    "Perching Duck": "#4A7840", "Stifftail": "#706040",
    "Shelduck": "#A07840", "Teal/Other": "#507070",
  },
  breedGroupColor: "#7A9878",
  hybridColor: "#608878",
};

const CERVIDAE_THEME: ColorTheme = {
  subfamilyColors: { Cervinae: "#C87030", Capreolinae: "#3A6890" },
  lineageColors: {
    "Red deer": "#C87030", "Fallow deer": "#B09040", "Sambar": "#A07040",
    "Muntjac": "#906858", "Roe deer": "#5A9060", "Moose": "#3A6890",
    "Reindeer": "#5878A8", "American deer": "#6B8870", "Water deer": "#4A9090",
  },
  breedGroupColor: "#888",
  hybridColor: "#888",
};

const BOVIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Cattle":  "#C8973A",
    "Zebu":    "#B07840",
    "Buffalo": "#607858",
    "Bison":   "#704830",
  },
  breedGroupColor: "#A08050",
  hybridColor: "#C09060",
};

const LEPORIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Rabbit":       "#C8904A",
    "Hare":         "#8BA878",
    "Cottontail":   "#B87848",
    "Amami rabbit": "#7A6090",
  },
  breedGroupColor: "#C0A070",
  hybridColor:     "#B89060",
};

const CETACEA_THEME: ColorTheme = {
  subfamilyColors: { Mysticeti: "#1a6b8a", Odontoceti: "#0d4f6e" },
  lineageColors: {
    "Right whales": "#2196a6", "Rorquals": "#1565c0", "Gray whale": "#546e7a",
    "Sperm whales": "#6a1b9a", "Beaked whales": "#37474f", "Dolphins": "#0288d1",
    "Porpoises": "#00838f", "Monodontidae": "#00acc1", "River dolphins": "#2e7d32",
  },
  breedGroupColor: "#607d8b",
  hybridColor: "#90a4ae",
};

export const COLOR_REGISTRY: Record<string, ColorTheme> = {
  felidae:    FELIDAE_THEME,
  canidae:    CANIDAE_THEME,
  equidae:    EQUIDAE_THEME,
  giraffidae: GIRAFFIDAE_THEME,
  caprinae:   CAPRINAE_THEME,
  suidae:     SUIDAE_THEME,
  phasianidae: PHASIANIDAE_THEME,
  anatidae:   ANATIDAE_THEME,
  cervidae:   CERVIDAE_THEME,
  cetacea:    CETACEA_THEME,
  bovidae:    BOVIDAE_THEME,
  leporidae:  LEPORIDAE_THEME,
};

export function getThemeForNode(node: TaxonNode): ColorTheme {
  if (node.familySlug && COLOR_REGISTRY[node.familySlug]) {
    return COLOR_REGISTRY[node.familySlug];
  }
  return PORTAL_THEME;
}

export { PORTAL_THEME };
