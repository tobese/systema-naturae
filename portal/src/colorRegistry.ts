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

const LAMNIFORMES_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Great white": "#c8d0d8",
    "Mako":        "#4a7090",
    "Thresher":    "#5a8898",
    "Basking":     "#8aaabb",
    "Deepwater":   "#2a3858",
  },
  breedGroupColor: "#607888",
  hybridColor:     "#8098b0",
};

const CARCHARHINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Bull":    "#8a6040",
    "Tiger":   "#c8a030",
    "Blue":    "#1a5898",
    "Reef":    "#2a8870",
    "Pelagic": "#1a6888",
  },
  breedGroupColor: "#507870",
  hybridColor:     "#708898",
};

const SPHYRNIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Hammerhead": "#3a5898",
    "Bonnethead": "#6878b8",
  },
  breedGroupColor: "#4a6898",
  hybridColor:     "#8898c8",
};

const ORECTOLOBIFORMES_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Whale shark": "#1a5878",
    "Nurse":       "#c8a060",
    "Zebra":       "#8a7848",
    "Wobbegong":   "#6a6840",
    "Bamboo":      "#7a9860",
  },
  breedGroupColor: "#607848",
  hybridColor:     "#9a9868",
};

const HOMINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Gorillas":          "#5a3a20",
    "Chimpanzees":       "#8a6030",
    "Orangutans":        "#c87830",
    "Human":             "#c8b090",
    "Archaic humans":    "#7a7060",
    "Australopithecines": "#4a3828",
  },
  breedGroupColor: "#a08060",
  hybridColor:     "#c0a070",
};

const CERCOPITHECIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Macaques": "#7a8a40",
    "Baboons":  "#b09040",
    "Colobus":  "#3a5840",
    "Guenons":  "#4a8870",
    "Langurs":  "#8a6848",
  },
  breedGroupColor: "#6a7850",
  hybridColor:     "#9aaa60",
};

const CEBIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Capuchins":       "#c87830",
    "Squirrel monkeys": "#e0b040",
    "Howler monkeys":  "#8a4030",
    "Spider monkeys":  "#4a6830",
    "Marmosets":       "#6a9860",
    "Tamarins":        "#c05828",
  },
  breedGroupColor: "#6a8848",
  hybridColor:     "#a0b860",
};

const LEMURIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "True lemurs":    "#c85838",
    "Ruffed lemurs":  "#283858",
    "Bamboo lemurs":  "#4a7840",
  },
  breedGroupColor: "#806040",
  hybridColor:     "#b07858",
};

const MACROPODIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Great kangaroos": "#c87828",
    "Wallabies":       "#8b6914",
    "Rock-wallabies":  "#a05820",
    "Tree-kangaroos":  "#4a6838",
    "Pademelons":      "#7a5030",
  },
  breedGroupColor: "#906030",
  hybridColor:     "#b08040",
};

const PICIDAE_THEME: ColorTheme = {
  subfamilyColors: {
    "Jynginae": "#8b6914",
    "Picinae":  "#c0392b",
  },
  lineageColors: {
    "Wrynecks":             "#8b6914",
    "Green Woodpeckers":    "#5d8233",
    "Black Woodpeckers":    "#2c3e50",
    "Spotted Woodpeckers":  "#c0392b",
    "Three-toed Woodpeckers": "#7f8c8d",
    "True Woodpeckers":     "#a03020",
  },
  breedGroupColor: "#a04030",
  hybridColor:     "#b05040",
};

const COLUMBIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Pigeons":       "#7d6e83",
    "Doves":         "#c4a882",
    "Green Pigeons": "#6b8e5e",
  },
  breedGroupColor: "#9b8ea0",
  hybridColor:     "#b0a0b5",
};

const CORVIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Magpies":       "#3a5a7a",
    "Crows & Ravens": "#1a1a2e",
    "Jackdaws":      "#5a6878",
    "Jays":          "#4a6ea8",
    "Azure Magpies": "#5aace8",
    "Nutcrackers":   "#6a5840",
    "Choughs":       "#c03020",
    "Siberian Jays": "#a07848",
    "Blue Magpies":  "#1a78c8",
    "Treepies":      "#b86830",
  },
  breedGroupColor: "#3a4a5a",
  hybridColor:     "#5a6a7a",
};

const PARIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Great Tits":   "#c8b820",
    "Blue Tits":    "#2a7ab8",
    "Coal Tits":    "#3a3a3a",
    "Marsh Tits":   "#8a7050",
    "Crested Tits": "#6a5c8a",
    "Ground Tit":   "#8a7848",
  },
  breedGroupColor: "#7a8898",
  hybridColor:     "#9aaa68",
};

const TURDIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Blackbirds":     "#1a1a1a",
    "Thrushes":       "#c8823a",
    "Winter Thrushes": "#7a9858",
    "Asian Thrushes": "#a06838",
    "Forest Thrushes": "#5a7848",
  },
  breedGroupColor: "#8a6030",
  hybridColor:     "#a07840",
};

const TARDIGRADA_THEME: ColorTheme = {
  subfamilyColors: {
    "Eutardigrada":    "#c8a830",
    "Heterotardigrada": "#c05820",
  },
  lineageColors: {
    "Eutardigrada":    "#c8a830",
    "Heterotardigrada": "#c05820",
  },
  breedGroupColor: "#a08030",
  hybridColor:     "#b09040",
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
  leporidae:       LEPORIDAE_THEME,
  lamniformes:     LAMNIFORMES_THEME,
  carcharhinidae:  CARCHARHINIDAE_THEME,
  sphyrnidae:      SPHYRNIDAE_THEME,
  orectolobiformes: ORECTOLOBIFORMES_THEME,
  hominidae:       HOMINIDAE_THEME,
  cercopithecidae: CERCOPITHECIDAE_THEME,
  cebidae:         CEBIDAE_THEME,
  lemuridae:       LEMURIDAE_THEME,
  macropodidae:    MACROPODIDAE_THEME,
  picidae:         PICIDAE_THEME,
  columbidae:      COLUMBIDAE_THEME,
  corvidae:        CORVIDAE_THEME,
  paridae:         PARIDAE_THEME,
  turdidae:        TURDIDAE_THEME,
  tardigrada:      TARDIGRADA_THEME,
};

export function getThemeForNode(node: TaxonNode): ColorTheme {
  if (node.familySlug && COLOR_REGISTRY[node.familySlug]) {
    return COLOR_REGISTRY[node.familySlug];
  }
  return PORTAL_THEME;
}

export { PORTAL_THEME };
