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

const MUSTELIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Badgers":           "#c8c0a0",
    "Honey Badger":      "#d0c8b0",
    "Wolverine":         "#6a4828",
    "Martens":           "#8a5c28",
    "Weasels & Polecats": "#c8a060",
    "Otters":            "#4a6858",
  },
  breedGroupColor: "#8a7048",
  hybridColor:     "#a08858",
};

const TESTUDINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Mediterranean Tortoises": "#c8a030",
    "Central Asian Tortoises":  "#a07830",
    "Hinged-back Tortoises":    "#8a6828",
    "Star Tortoises":           "#c8b840",
  },
  breedGroupColor: "#a08828",
  hybridColor:     "#b89838",
};

const GEOEMYDIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "European Pond Turtles": "#4a7848",
    "Asian Pond Turtles":    "#3a6858",
    "Asian Box Turtles":     "#6a8838",
  },
  breedGroupColor: "#4a6840",
  hybridColor:     "#6a8850",
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

const URSIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Brown & Black Bears": "#8a5c28",
    "Polar Bear":          "#d0cfc8",
    "Giant Panda":         "#1a1a1a",
    "Sun Bear":            "#4a3018",
    "Sloth Bear":          "#3a2818",
    "Spectacled Bear":     "#5a3820",
  },
  breedGroupColor: "#7a5030",
  hybridColor:     "#a07848",
};

const PHOCIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Northern Seals":  "#607888",
    "Elephant Seals":  "#8a7070",
    "Antarctic Seals": "#3a6088",
    "Monk Seals":      "#a07858",
  },
  breedGroupColor: "#5a7080",
  hybridColor:     "#7a9098",
};

const FRINGILLIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Chaffinches":  "#c89040",
    "Goldfinches":  "#e8b820",
    "Siskins":      "#8ab830",
    "Greenfinches": "#5a9830",
    "Bullfinches":  "#c84040",
    "Crossbills":   "#c83030",
    "Hawfinches":   "#c87840",
    "Linnets":      "#c06050",
    "Redpolls":     "#a03030",
  },
  breedGroupColor: "#a09030",
  hybridColor:     "#c0a840",
};

const MUSCICAPIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Robins & Chats": "#c85030",
    "Nightingales":   "#8a6840",
    "Redstarts":      "#c87030",
    "Flycatchers":    "#5a7898",
    "Wheatears":      "#a09870",
  },
  breedGroupColor: "#8a7050",
  hybridColor:     "#b09060",
};

const STRIGIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Eagle-owls":  "#c89030",
    "Wood Owls":   "#8a6030",
    "Eared Owls":  "#a08040",
    "Pygmy Owls":  "#7a6838",
    "Scops Owls":  "#9a8858",
    "Hawk Owls":   "#c0a060",
  },
  breedGroupColor: "#987840",
  hybridColor:     "#b09850",
};

const TYTONIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Barn Owls":  "#d4a574",
    "Grass Owls": "#7a9860",
    "Masked Owls": "#a08050",
    "Sooty Owls": "#3a4a58",
    "Bay Owls":   "#c07848",
  },
  breedGroupColor: "#b89060",
  hybridColor:     "#d0a888",
};

const ACCIPITRIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Goshawks & Sparrowhawks": "#5a7840",
    "Buzzards":                "#a07830",
    "Eagles":                  "#c89830",
    "Sea Eagles":              "#5a8898",
    "Harriers":                "#8a7098",
    "Kites":                   "#c85030",
    "Vultures":                "#6a5838",
  },
  breedGroupColor: "#8a6830",
  hybridColor:     "#a08840",
};

const VIPERIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "True Vipers":  "#6a7840",
    "Rattlesnakes": "#c89030",
    "Pit Vipers":   "#8a6030",
  },
  breedGroupColor: "#7a7038",
  hybridColor:     "#9a8848",
};

const CHAMAELEONIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "True Chameleons":         "#5aab70",
    "Furcifer Chameleons":     "#c85898",
    "Three-horned Chameleons": "#3a8858",
    "Leaf Chameleons":         "#8aac30",
    "Pygmy Chameleons":        "#5a9848",
  },
  breedGroupColor: "#5a9860",
  hybridColor:     "#7ab870",
};

const SALAMANDRIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Fire Salamanders": "#e89020",
    "Crested Newts":    "#2a6830",
    "Smooth Newts":     "#5a9848",
    "Asian Salamanders": "#c03828",
  },
  breedGroupColor: "#5a7838",
  hybridColor:     "#7a9850",
};

const RANIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "European Frogs": "#5a8840",
    "Water Frogs":    "#3a7830",
    "American Frogs": "#7a9838",
  },
  breedGroupColor: "#4a7838",
  hybridColor:     "#6a9848",
};

const APIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Honey Bees":     "#e8b820",
    "Bumblebees":     "#e87820",
    "Carpenter Bees": "#5a48a0",
    "Orchid Bees":    "#30a870",
  },
  breedGroupColor: "#c09020",
  hybridColor:     "#d0a830",
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

const CLUPEIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Herrings": "#8aaabb",
    "Sprats":   "#6888a0",
    "Shads":    "#4a7888",
  },
  breedGroupColor: "#7898a8",
  hybridColor:     "#9ab8c8",
};

const SALMONIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Atlantic Salmon & Trout": "#e07830",
    "Char":          "#c84848",
    "Grayling":      "#8a6898",
    "Pacific Salmon": "#e05828",
  },
  breedGroupColor: "#c06030",
  hybridColor:     "#d88040",
};

const ESOCIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Pike": "#5a7838",
  },
  breedGroupColor: "#4a6830",
  hybridColor:     "#6a9848",
};

const PERCIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Perch":  "#c87828",
    "Zander": "#5a7898",
    "Ruffe":  "#8a8850",
  },
  breedGroupColor: "#8a7040",
  hybridColor:     "#a89060",
};

const GADIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Cod":     "#6888a8",
    "Haddock": "#8898b8",
    "Whiting": "#9aaac8",
  },
  breedGroupColor: "#7888a0",
  hybridColor:     "#9aaabb",
};

const CYPRINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Roach":   "#c8a060",
    "Bream":   "#a07840",
    "Ide & Dace": "#d0b870",
    "Rudd":    "#e0b030",
    "Carp":    "#b88840",
  },
  breedGroupColor: "#b09050",
  hybridColor:     "#c8a860",
};

const MOTACILLIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Wagtails": "#d0c830",
    "Pipits":   "#b0a860",
  },
  breedGroupColor: "#c0b840",
  hybridColor:     "#d8cc50",
};

const HIRUNDINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Swallows": "#1a3888",
    "Martins":  "#3a5898",
  },
  breedGroupColor: "#2a4878",
  hybridColor:     "#4a68a8",
};

const PHYLLOSCOPIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Leaf Warblers":  "#7ab840",
    "Sylvia Warblers": "#5a9830",
  },
  breedGroupColor: "#6aa838",
  hybridColor:     "#8ac850",
};

const LARIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Large Gulls":  "#d0d0c8",
    "Hooded Gulls": "#b0b8c8",
    "Sea Terns":    "#c0c8d8",
  },
  breedGroupColor: "#b8c0c8",
  hybridColor:     "#d0d8e0",
};

const ARDEIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Grey Herons & Egrets": "#9ab0b8",
    "Bitterns":             "#8a7840",
    "Little Bitterns":      "#a09050",
  },
  breedGroupColor: "#8898a0",
  hybridColor:     "#a0b0b8",
};

const MURIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Mice":                "#c8a060",
    "Rats":                "#8a6040",
    "Gerbils":             "#d0b870",
    "Multimammate mice":   "#a07848",
  },
  breedGroupColor: "#b09050",
  hybridColor:     "#c8b060",
};

const SCIURIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Tree Squirrels":   "#c87830",
    "Ground Squirrels": "#a07840",
    "Chipmunks":        "#e09030",
    "Marmots":          "#8a6830",
    "Flying Squirrels": "#4a7898",
  },
  breedGroupColor: "#b08040",
  hybridColor:     "#c89050",
};

const CRICETIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Hamsters":      "#e0a030",
    "Voles":         "#7a9040",
    "Lemmings":      "#c84030",
    "New World mice": "#6a8858",
  },
  breedGroupColor: "#a08040",
  hybridColor:     "#c0a050",
};

const CASTORIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Beavers": "#8a6030",
  },
  breedGroupColor: "#7a5828",
  hybridColor:     "#9a7040",
};

const CAVIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Capybara":   "#c89040",
    "Guinea Pigs": "#d0a860",
    "Maras":      "#b87038",
    "Rock Cavies": "#8a7050",
  },
  breedGroupColor: "#b08848",
  hybridColor:     "#c8a060",
};

const PTEROPODIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Flying Foxes": "#8a5030",
    "Fruit Bats":   "#c87838",
    "Blossom Bats": "#e09848",
  },
  breedGroupColor: "#a06830",
  hybridColor:     "#c08848",
};

const VESPERTILIONIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Pipistrelles":     "#4a5888",
    "Long-eared Bats":  "#3a4878",
    "Noctules":         "#6a5898",
    "Myotis Bats":      "#2a3868",
  },
  breedGroupColor: "#4a5070",
  hybridColor:     "#6a7098",
};

const RHINOLOPHIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Horseshoe Bats": "#8a3850",
  },
  breedGroupColor: "#7a3048",
  hybridColor:     "#a05068",
};

const PHYLLOSTOMIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Vampire Bats":      "#8a1a1a",
    "Nectar Bats":       "#e8b020",
    "Fruit Bats":        "#c87030",
    "Spear-nosed Bats":  "#5a7038",
  },
  breedGroupColor: "#8a5028",
  hybridColor:     "#b07040",
};

const ERINACEIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Hedgehogs": "#c8a870",
    "Moonrats":  "#6a7850",
  },
  breedGroupColor: "#b09060",
  hybridColor:     "#c8b078",
};

const SORICIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Red-toothed Shrews":   "#c04030",
    "White-toothed Shrews": "#c8a860",
    "Water Shrews":         "#2a6878",
  },
  breedGroupColor: "#9a6040",
  hybridColor:     "#b07848",
};

const TALPIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "True Moles": "#4a3828",
    "Desmans":    "#2a5878",
  },
  breedGroupColor: "#3a3030",
  hybridColor:     "#5a5048",
};

const ELEPHANTIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "African Elephants": "#7a6040",
    "Asian Elephants":   "#8a7050",
  },
  breedGroupColor: "#7a6848",
  hybridColor:     "#9a8060",
};

const MANIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Asian Pangolins":   "#c8a030",
    "African Pangolins": "#8a7028",
  },
  breedGroupColor: "#a89030",
  hybridColor:     "#c0a840",
};

const BRADYPODIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Three-toed Sloths": "#8a9858",
  },
  breedGroupColor: "#7a8848",
  hybridColor:     "#9ab060",
};

const MYRMECOPHAGIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Giant Anteater": "#c8a060",
    "Tamanduas":      "#e0c080",
    "Silky Anteater": "#f0d8a0",
  },
  breedGroupColor: "#c0a058",
  hybridColor:     "#d8b870",
};

const DASYPODIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Nine-banded Armadillos":   "#b09050",
    "Three-banded Armadillos":  "#c8a868",
    "Giant Armadillo":          "#8a7038",
    "Pichi":                    "#d0c090",
  },
  breedGroupColor: "#a89050",
  hybridColor:     "#c0a860",
};

const DASYURIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Tasmanian Devil": "#1a1a1a",
    "Quolls":          "#c87830",
    "Dunnarts":        "#8a9070",
    "Antechinuses":    "#7a6848",
  },
  breedGroupColor: "#6a5838",
  hybridColor:     "#8a7850",
};

const VOMBATIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Wombats": "#9a8858",
  },
  breedGroupColor: "#8a7848",
  hybridColor:     "#b0a068",
};

const DIDELPHIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Large Opossums":        "#c8a878",
    "Mouse Opossums":        "#a08858",
    "Short-tailed Opossums": "#8a7848",
    "Water Opossums":        "#2a6878",
  },
  breedGroupColor: "#a09060",
  hybridColor:     "#c0b070",
};

const RALLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rails": "#6a9870", "Moorhens & Coots": "#3a6858" }, breedGroupColor: "#5a8868", hybridColor: "#8ab898" };
const GRUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Palearctic Cranes": "#8898a8", "Steppe Cranes": "#c8b888" }, breedGroupColor: "#9898a0", hybridColor: "#b8b8c8" };
const PODICIPEDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Large Grebes": "#c87838", "Small Grebes": "#a85828" }, breedGroupColor: "#b87030", hybridColor: "#d89860" };
const SCOLOPACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Curlews & Godwits": "#c8a068", "Snipe & Woodcock": "#a07840", "Shanks & Tattlers": "#8a9870", "Small Waders": "#b89868" }, breedGroupColor: "#b89058", hybridColor: "#d0b888" };
const ALCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Razorbills": "#3a4858", "Guillemots": "#283848", "Small Auks": "#4a6080", "Puffins": "#e87828" }, breedGroupColor: "#3a5068", hybridColor: "#6a8098" };
const PHALACROCORACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cormorants": "#2a4838", "Pygmy Cormorants": "#4a6848" }, breedGroupColor: "#3a5840", hybridColor: "#5a7858" };
const STURNIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "European Starlings": "#6858a8", "Rosy Starlings": "#d888a8" }, breedGroupColor: "#7868b8", hybridColor: "#9888c8" };
const ACROCEPHALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Reed Warblers": "#c89848", "Grasshopper Warblers": "#a87838", "Hippolais Warblers": "#d8b048" }, breedGroupColor: "#c09040", hybridColor: "#d8b868" };
const REGULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Kinglets": "#d8c040" }, breedGroupColor: "#c8b030", hybridColor: "#e8d060" };
const GAVIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Northern Divers": "#4a6888" }, breedGroupColor: "#3a5878", hybridColor: "#6a88a8" };
const FALCONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Kestrels": "#7a8898", "True Falcons": "#4a6080" }, breedGroupColor: "#5a7090", hybridColor: "#8a9aaa" };
const APODIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Typical Swifts": "#3a3848", "Alpine Swifts": "#5a5870" }, breedGroupColor: "#4a4858", hybridColor: "#6a6880" };
const CUCULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Old World Cuckoos": "#7a8868", "Coucals": "#5a6848" }, breedGroupColor: "#6a7858", hybridColor: "#9a9878" };
const CAPRIMULGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Old World Nightjars": "#a87848", "New World Nightjars": "#7a5838" }, breedGroupColor: "#906840", hybridColor: "#c09868" };
const ALCEDINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "River Kingfishers": "#00909a", "Tree Kingfishers": "#e87028" }, breedGroupColor: "#007888", hybridColor: "#30a8b8" };
const UPUPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hoopoes": "#c87838" }, breedGroupColor: "#b86828", hybridColor: "#d89858" };
const CHARADRIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Golden Plovers": "#c8a848", "Lapwings": "#6a7858", "Ringed Plovers": "#b88840" }, breedGroupColor: "#b89040", hybridColor: "#d8c060" };
const HAEMATOPODIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Oystercatchers": "#c04820" }, breedGroupColor: "#a03810", hybridColor: "#d06840" };
const RECURVIROSTRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Avocets": "#7a9ab8", "Stilts": "#202030" }, breedGroupColor: "#204860", hybridColor: "#9ab8d0" };
const STERCORARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Large Skuas": "#585848", "Small Skuas": "#3a3828" }, breedGroupColor: "#4a4838", hybridColor: "#706858" };
const THRESKIORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Spoonbills": "#e8d8c8", "Ibises": "#7a6848" }, breedGroupColor: "#c8b8a0", hybridColor: "#f0e8d8" };
const CICONIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "White Storks": "#e83020", "Black Storks": "#202838" }, breedGroupColor: "#a02010", hybridColor: "#d05040" };
const SULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Gannets": "#f0e858", "Tropical Boobies": "#206090" }, breedGroupColor: "#d0c840", hybridColor: "#f8f0a0" };
const PANDIONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Osprey": "#8a7040" }, breedGroupColor: "#786030", hybridColor: "#c0a860" };
const SYLVIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sylvia Warblers": "#8a9870" }, breedGroupColor: "#7a8860", hybridColor: "#aab890" };
const AEGITHALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Long-tailed Tits": "#e8b8b0" }, breedGroupColor: "#d0a098", hybridColor: "#f0d0c8" };
const SITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nuthatches": "#6888a8" }, breedGroupColor: "#587898", hybridColor: "#88a8c8" };
const CERTHIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Treecreepers": "#a87848" }, breedGroupColor: "#986838", hybridColor: "#c09868" };
const TROGLODYTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurasian Wrens": "#a85830", "New World Wrens": "#784020" }, breedGroupColor: "#986040", hybridColor: "#c08060" };
const BOMBYCILLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Waxwings": "#c89050" }, breedGroupColor: "#b88040", hybridColor: "#e8c080" };
const EMBERIZIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurasian Buntings": "#d8b820", "Arctic Buntings": "#e8e8e0" }, breedGroupColor: "#c0a010", hybridColor: "#e8d040" };
const PASSERIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Old World Sparrows": "#b89060" }, breedGroupColor: "#a88050", hybridColor: "#d0b080" };
const PRUNELLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Accentors": "#7a8898" }, breedGroupColor: "#6a7888", hybridColor: "#9aaab8" };
const ALAUDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Skylarks": "#d8b870", "Wood Larks": "#b89858", "Horned Larks": "#9a8040" }, breedGroupColor: "#c0a058", hybridColor: "#e8c888" };
const LOCUSTELLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Grasshopper Warblers": "#8a9868", "River Warblers": "#6a7848" }, breedGroupColor: "#7a8858", hybridColor: "#aab880" };

const LANIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Grey Shrikes": "#a09888", "Red-backed Shrikes": "#c87840", "Masked Shrikes": "#d0a050", "Brown Shrikes": "#8a7050", "Long-tailed Shrikes": "#a08858" }, breedGroupColor: "#b09870", hybridColor: "#d0b890" };

const ORIOLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurasian Orioles": "#e8c830", "Asian Orioles": "#e8b820", "African Orioles": "#d8a828", "Australasian Orioles": "#90a840", "Figbirds": "#78a058" }, breedGroupColor: "#d0b030", hybridColor: "#e8d060" };

const REMIZIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurasian Penduline Tits": "#c8a050", "African Penduline Tits": "#889870" }, breedGroupColor: "#b09848", hybridColor: "#d0b870" };

const CINCLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dippers": "#4a6070" }, breedGroupColor: "#3a5060", hybridColor: "#6a8098" };

const PANURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bearded Reedling": "#c87838" }, breedGroupColor: "#b06828", hybridColor: "#e09858" };

const CISTICOLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cetti's Warblers": "#a06848", "Cisticolas": "#8a8870", "Prinias": "#a89860", "Bush Warblers": "#a08868" }, breedGroupColor: "#a08058", hybridColor: "#c8a878" };

const SPHENISCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Great Penguins": "#607888", "Brush-tailed Penguins": "#4a7080", "Crested Penguins": "#c88838", "Yellow-eyed Penguins": "#c8a840", "Little Penguins": "#5888a0", "Banded Penguins": "#3a6070" }, breedGroupColor: "#4a6878", hybridColor: "#7898a8" };

const TROCHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bee Hummingbirds": "#30a060", "Hermits": "#a08850", "Giants & Topazes": "#c85828", "Mountain Gems": "#2870a0", "Brilliants": "#6848a8", "Emeralds": "#20a050", "Mangos & Caribs": "#c82038", "Trainbearers": "#d858a8", "Sunbeams": "#d8a830", "Incas": "#287088", "Violet-ears": "#3860a8", "JacobinS": "#40a0b8" }, breedGroupColor: "#40a060", hybridColor: "#70c888" };

const PHOENICOPTERIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Greater Flamingos": "#e87868", "Lesser Flamingos": "#e86050", "Andean Flamingos": "#e8a080" }, breedGroupColor: "#e87060", hybridColor: "#f0a898" };

const PROCELLARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Fulmars & Giant Petrels": "#a0a0a0", "Shearwaters": "#588098", "Gadfly Petrels": "#7898a8", "Prions & Blue Petrels": "#6890a8" }, breedGroupColor: "#789098", hybridColor: "#98b0b8" };

const HYDROBATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Storm Petrels": "#3a4048" }, breedGroupColor: "#303840", hybridColor: "#5a6870" };

const POLIOPTILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Gnatcatchers": "#6888a8", "Gnatwrens": "#8a7858" }, breedGroupColor: "#6888a8", hybridColor: "#90a8c0" };

const PELECANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pelicans": "#e8d8a8" }, breedGroupColor: "#d8c898", hybridColor: "#f0e8c8" };

const OTIDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Great Bustards": "#c8a060", "Houbara Bustards": "#d0b080", "Little Bustards": "#a89870" }, breedGroupColor: "#c0a070", hybridColor: "#d8c098" };

const MEROPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bee-eaters": "#30b870" }, breedGroupColor: "#30a860", hybridColor: "#60d090" };

const CORACIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Rollers": "#2088c8", "Broad-billed Rollers": "#6870a8" }, breedGroupColor: "#2880b8", hybridColor: "#60a8d8" };

const PTEROCLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sandgrouse": "#c8a870" }, breedGroupColor: "#b89860", hybridColor: "#e0c898" };

const BURHINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Thick-knees": "#b09870" }, breedGroupColor: "#a08860", hybridColor: "#c8b090" };

const GLAREOLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pratincoles": "#c8a060", "Coursers": "#d0b880" }, breedGroupColor: "#c0a870", hybridColor: "#d8c8a0" };

const NUMIDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Guineafowl": "#607888" }, breedGroupColor: "#506878", hybridColor: "#8098a8" };
const RAMPHASTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Large Toucans": "#e8a020", "Green Toucanets": "#30a860", "Aracaris": "#d86828" }, breedGroupColor: "#c89030", hybridColor: "#e8b860" };
const MEGALAIMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Asian Barbets": "#40a860" }, breedGroupColor: "#309850", hybridColor: "#60c880" };
const CACATUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "White Cockatoos": "#e8e8e0", "Galahs": "#e8a0a0", "Gang-gangs": "#8890a0", "Cockatiels": "#c0b080" }, breedGroupColor: "#d0d0c8", hybridColor: "#e8e8d8" };
const DIOMEDEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Great Albatrosses": "#d0d8e0", "Mollymawks": "#a0b8c8", "Sooty Albatrosses": "#586878" }, breedGroupColor: "#b0c0d0", hybridColor: "#d0d8e8" };
const MENURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lyrebirds": "#7a6850" }, breedGroupColor: "#6a5840", hybridColor: "#9a8870" };
const MIMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mockingbirds": "#889098", "Thrashers": "#a08860" }, breedGroupColor: "#889098", hybridColor: "#a8b0b8" };
const NECTARINIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sunbirds": "#3880b8", "Spiderhunters": "#789860" }, breedGroupColor: "#3880b8", hybridColor: "#70b0d8" };
const PARADISAEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Paradisaea": "#e8a020", "Cicinnurus": "#d82838", "Lophorina": "#202838", "Seleucidis": "#d8a808" }, breedGroupColor: "#c88828", hybridColor: "#e8c060" };
const PTILONORHYNCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bowerbirds": "#6878a0" }, breedGroupColor: "#586890", hybridColor: "#8898b8" };
const PYCNONOTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bulbuls": "#886070" }, breedGroupColor: "#785060", hybridColor: "#a88898" };
const ESTRILDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Waxbills & Munias": "#c87058" }, breedGroupColor: "#b06048", hybridColor: "#e09880" };
const ICTERIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "New World Blackbirds": "#283840" }, breedGroupColor: "#202830", hybridColor: "#485868" };
const CARDINALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cardinals & Grosbeaks": "#c82028", "Buntings": "#2860a8" }, breedGroupColor: "#c02028", hybridColor: "#e06068" };
const PARULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "New World Warblers": "#d8a820" }, breedGroupColor: "#c89810", hybridColor: "#e8c850" };
const THRAUPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tangara Tanagers": "#2088c8", "Mountain Tanagers": "#c85828", "Thraupis Tanagers": "#3890a8" }, breedGroupColor: "#2078b0", hybridColor: "#60b0d8" };
const TYRANNIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Kingbirds": "#385878", "Phoebes": "#788898", "Empidonax Flycatchers": "#90a068", "Kiskadees": "#d8a020", "Vermilion Flycatchers": "#d82828", "Myiarchus Flycatchers": "#c89040", "Pewees": "#688898", "Kiskadees & Allies": "#d8a020" }, breedGroupColor: "#486888", hybridColor: "#7898b0" };
const VIREONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Vireos": "#789860", "Peppershrikes": "#a89848" }, breedGroupColor: "#789860", hybridColor: "#a0b880" };
const FREGATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Frigatebirds": "#202838" }, breedGroupColor: "#181828", hybridColor: "#384860" };
const ANHINGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Darters": "#485848" }, breedGroupColor: "#384838", hybridColor: "#687868" };
const SAGITTARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Secretarybirds": "#888888" }, breedGroupColor: "#787878", hybridColor: "#a8a8a8" };
const CATHARTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "New World Vultures": "#403838" }, breedGroupColor: "#302828", hybridColor: "#605858" };
const JACANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Jacanas": "#886848" }, breedGroupColor: "#785838", hybridColor: "#a88868" };

const ACANTHISITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Acanthisittidae": "#889098" }, breedGroupColor: "#889098", hybridColor: "#a8b0b8" };
const ACANTHIZIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Acanthizidae": "#90a060" }, breedGroupColor: "#90a060", hybridColor: "#a8b0b8" };
const AEGITHINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Aegithinidae": "#c8a820" }, breedGroupColor: "#c8a820", hybridColor: "#a8b0b8" };
const AEGOTHELIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Aegothelidae": "#889078" }, breedGroupColor: "#889078", hybridColor: "#a8b0b8" };
const ALCIPPEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Alcippeidae": "#989068" }, breedGroupColor: "#989068", hybridColor: "#a8b0b8" };
const ANHIMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Anhimidae": "#687870" }, breedGroupColor: "#687870", hybridColor: "#a8b0b8" };
const ANSERANATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Anseranatidae": "#c0b8a0" }, breedGroupColor: "#c0b8a0", hybridColor: "#a8b0b8" };
const APTERYGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Apterygidae": "#8a7a58" }, breedGroupColor: "#8a7a58", hybridColor: "#a8b0b8" };
const ARAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Aramidae": "#788878" }, breedGroupColor: "#788878", hybridColor: "#a8b0b8" };
const ARTAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Artamidae": "#406090" }, breedGroupColor: "#406090", hybridColor: "#a8b0b8" };
const ATRICHORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Atrichornithidae": "#8a7860" }, breedGroupColor: "#8a7860", hybridColor: "#a8b0b8" };
const BALAENICIPITIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Balaenicipitidae": "#788088" }, breedGroupColor: "#788088", hybridColor: "#a8b0b8" };
const BERNIERIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bernieriidae": "#a0a068" }, breedGroupColor: "#a0a068", hybridColor: "#a8b0b8" };
const BRACHYPTERACIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Brachypteraciidae": "#60a888" }, breedGroupColor: "#60a888", hybridColor: "#a8b0b8" };
const BUCCONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bucconidae": "#887058" }, breedGroupColor: "#887058", hybridColor: "#a8b0b8" };
const BUCEROTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bucerotidae": "#e8a820" }, breedGroupColor: "#e8a820", hybridColor: "#a8b0b8" };
const BUCORVIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bucorvidae": "#484848" }, breedGroupColor: "#484848", hybridColor: "#a8b0b8" };
const BUPHAGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Buphagidae": "#c87030" }, breedGroupColor: "#c87030", hybridColor: "#a8b0b8" };
const CALCARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Calcariidae": "#a09870" }, breedGroupColor: "#a09870", hybridColor: "#a8b0b8" };
const CALLAEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Callaeidae": "#486868" }, breedGroupColor: "#486868", hybridColor: "#a8b0b8" };
const CALYPTOMENIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Calyptomenidae": "#30a840" }, breedGroupColor: "#30a840", hybridColor: "#a8b0b8" };
const CALYPTOPHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Calyptophilidae": "#989068" }, breedGroupColor: "#989068", hybridColor: "#a8b0b8" };
const CAMPEPHAGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Campephagidae": "#689098" }, breedGroupColor: "#689098", hybridColor: "#a8b0b8" };
const CAPITONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Capitonidae": "#d86828" }, breedGroupColor: "#d86828", hybridColor: "#a8b0b8" };
const CARIAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cariamidae": "#a09878" }, breedGroupColor: "#a09878", hybridColor: "#a8b0b8" };
const CASUARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Casuariidae": "#5a6850" }, breedGroupColor: "#5a6850", hybridColor: "#a8b0b8" };
const CETTIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cettiidae": "#a08858" }, breedGroupColor: "#a08858", hybridColor: "#a8b0b8" };
const CHAETOPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Chaetopidae": "#789080" }, breedGroupColor: "#789080", hybridColor: "#a8b0b8" };
const CHIONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Chionidae": "#d0d0d8" }, breedGroupColor: "#d0d0d8", hybridColor: "#a8b0b8" };
const CHLOROPSEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Chloropseidae": "#40a858" }, breedGroupColor: "#40a858", hybridColor: "#a8b0b8" };
const CINCLOSOMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cinclosomatidae": "#7888a0" }, breedGroupColor: "#7888a0", hybridColor: "#a8b0b8" };
const CLIMACTERIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Climacteridae": "#a07048" }, breedGroupColor: "#a07048", hybridColor: "#a8b0b8" };
const CNEMOPHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cnemophilidae": "#88a040" }, breedGroupColor: "#88a040", hybridColor: "#a8b0b8" };
const COLIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Coliidae": "#a09070" }, breedGroupColor: "#a09070", hybridColor: "#a8b0b8" };
const CONOPOPHAGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Conopophagidae": "#b09868" }, breedGroupColor: "#b09868", hybridColor: "#a8b0b8" };
const CORCORACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Corcoracidae": "#585850" }, breedGroupColor: "#585850", hybridColor: "#a8b0b8" };
const COTINGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cotingidae": "#c04840" }, breedGroupColor: "#c04840", hybridColor: "#a8b0b8" };
const CRACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cracidae": "#5a6840" }, breedGroupColor: "#5a6840", hybridColor: "#a8b0b8" };
const DASYORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dasyornithidae": "#a08058" }, breedGroupColor: "#a08058", hybridColor: "#a8b0b8" };
const DICAEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dicaeidae": "#c06048" }, breedGroupColor: "#c06048", hybridColor: "#a8b0b8" };
const DICRURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dicruridae": "#283848" }, breedGroupColor: "#283848", hybridColor: "#a8b0b8" };
const DONACOBIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Donacobiidae": "#706850" }, breedGroupColor: "#706850", hybridColor: "#a8b0b8" };
const DROMADIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dromadidae": "#d0c8b0" }, breedGroupColor: "#d0c8b0", hybridColor: "#a8b0b8" };
const DULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dulidae": "#a08838" }, breedGroupColor: "#a08838", hybridColor: "#a8b0b8" };
const ELACHURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Elachuridae": "#8a7868" }, breedGroupColor: "#8a7868", hybridColor: "#a8b0b8" };
const ERYTHROCERCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Erythrocercidae": "#d89838" }, breedGroupColor: "#d89838", hybridColor: "#a8b0b8" };
const EULACESTOMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eulacestomatidae": "#a08048" }, breedGroupColor: "#a08048", hybridColor: "#a8b0b8" };
const EUPETIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eupetidae": "#5a6840" }, breedGroupColor: "#5a6840", hybridColor: "#a8b0b8" };
const EURYLAIMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurylaimidae": "#889098" }, breedGroupColor: "#889098", hybridColor: "#a8b0b8" };
const EURYPYGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eurypygidae": "#a09848" }, breedGroupColor: "#a09848", hybridColor: "#a8b0b8" };
const FALCUNCULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Falcunculidae": "#a8a030" }, breedGroupColor: "#a8a030", hybridColor: "#a8b0b8" };
const FORMICARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Formicariidae": "#7a6850" }, breedGroupColor: "#7a6850", hybridColor: "#a8b0b8" };
const FURNARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Horneros": "#c09050", "Woodcreepers": "#886840", "Spinetails": "#a08058", "Xenops": "#989068", "Treehunters": "#788060" }, breedGroupColor: "#a07848", hybridColor: "#a8b0b8" };
const GALBULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Galbulidae": "#30a888" }, breedGroupColor: "#30a888", hybridColor: "#a8b0b8" };
const GRALLARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Grallariidae": "#887050" }, breedGroupColor: "#887050", hybridColor: "#a8b0b8" };
const HELIORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Heliornithidae": "#687860" }, breedGroupColor: "#687860", hybridColor: "#a8b0b8" };
const HEMIPROCNIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hemiprocnidae": "#6878a0" }, breedGroupColor: "#6878a0", hybridColor: "#a8b0b8" };
const HYLIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hyliidae": "#68a058" }, breedGroupColor: "#68a058", hybridColor: "#a8b0b8" };
const HYLIOTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hyliotidae": "#7088a0" }, breedGroupColor: "#7088a0", hybridColor: "#a8b0b8" };
const HYLOCITREIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hylocitreidae": "#789068" }, breedGroupColor: "#789068", hybridColor: "#a8b0b8" };
const HYPOCOLIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Hypocoliidae": "#a8a080" }, breedGroupColor: "#a8a080", hybridColor: "#a8b0b8" };
const IBIDORHYNCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ibidorhynchidae": "#b0a090" }, breedGroupColor: "#b0a090", hybridColor: "#a8b0b8" };
const ICTERIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Icteriidae": "#c8a820" }, breedGroupColor: "#c8a820", hybridColor: "#a8b0b8" };
const IFRITIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ifritidae": "#3868a8" }, breedGroupColor: "#3868a8", hybridColor: "#a8b0b8" };
const INDICATORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Indicatoridae": "#889868" }, breedGroupColor: "#889868", hybridColor: "#a8b0b8" };
const IRENIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Irenidae": "#2868a8" }, breedGroupColor: "#2868a8", hybridColor: "#a8b0b8" };
const LEIOTHRICHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Leiothrichidae": "#d8a030" }, breedGroupColor: "#d8a030", hybridColor: "#a8b0b8" };
const LEPTOSOMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Leptosomidae": "#7090a0" }, breedGroupColor: "#7090a0", hybridColor: "#a8b0b8" };
const LYBIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lybiidae": "#c87020" }, breedGroupColor: "#c87020", hybridColor: "#a8b0b8" };
const MACHAERIRHYNCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Machaerirhynchidae": "#c8a848" }, breedGroupColor: "#c8a848", hybridColor: "#a8b0b8" };
const MACROSPHENIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Macrosphenidae": "#98a068" }, breedGroupColor: "#98a068", hybridColor: "#a8b0b8" };
const MALACONOTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Malaconotidae": "#c87038" }, breedGroupColor: "#c87038", hybridColor: "#a8b0b8" };
const MALURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Maluridae": "#3880c0" }, breedGroupColor: "#3880c0", hybridColor: "#a8b0b8" };
const MEGAPODIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Megapodiidae": "#786050" }, breedGroupColor: "#786050", hybridColor: "#a8b0b8" };
const MELAMPITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Melampittidae": "#484040" }, breedGroupColor: "#484040", hybridColor: "#a8b0b8" };
const MELANOCHARITIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Melanocharitidae": "#687050" }, breedGroupColor: "#687050", hybridColor: "#a8b0b8" };
const MELANOPAREIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Melanopareiidae": "#a09060" }, breedGroupColor: "#a09060", hybridColor: "#a8b0b8" };
const MELIPHAGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Meliphagidae": "#789048" }, breedGroupColor: "#789048", hybridColor: "#a8b0b8" };
const MESITORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mesitornithidae": "#b09868" }, breedGroupColor: "#b09868", hybridColor: "#a8b0b8" };
const MITROSPINGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mitrospingidae": "#689868" }, breedGroupColor: "#689868", hybridColor: "#a8b0b8" };
const MODULATRICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Modulatricidae": "#908070" }, breedGroupColor: "#908070", hybridColor: "#a8b0b8" };
const MOHOIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mohoidae": "#887860" }, breedGroupColor: "#887860", hybridColor: "#a8b0b8" };
const MOHOUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mohouidae": "#a09068" }, breedGroupColor: "#a09068", hybridColor: "#a8b0b8" };
const MOMOTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Momotidae": "#40a868" }, breedGroupColor: "#40a868", hybridColor: "#a8b0b8" };
const MONARCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Monarchidae": "#3878a8" }, breedGroupColor: "#3878a8", hybridColor: "#a8b0b8" };
const MUSOPHAGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Musophagidae": "#30a860" }, breedGroupColor: "#30a860", hybridColor: "#a8b0b8" };
const NEOSITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Neosittidae": "#788878" }, breedGroupColor: "#788878", hybridColor: "#a8b0b8" };
const NESOSPINGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nesospingidae": "#787860" }, breedGroupColor: "#787860", hybridColor: "#a8b0b8" };
const NICATORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nicatoridae": "#789048" }, breedGroupColor: "#789048", hybridColor: "#a8b0b8" };
const NOTIOMYSTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Notiomystidae": "#689898" }, breedGroupColor: "#689898", hybridColor: "#a8b0b8" };
const NYCTIBIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nyctibiidae": "#a09878" }, breedGroupColor: "#a09878", hybridColor: "#a8b0b8" };
const OCEANITIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Oceanitidae": "#485868" }, breedGroupColor: "#485868", hybridColor: "#a8b0b8" };
const ODONTOPHORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Odontophoridae": "#a09860" }, breedGroupColor: "#a09860", hybridColor: "#a8b0b8" };
const OPISTHOCOMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Opisthocomidae": "#a08848" }, breedGroupColor: "#a08848", hybridColor: "#a8b0b8" };
const OREOICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Oreoicidae": "#888860" }, breedGroupColor: "#888860", hybridColor: "#a8b0b8" };
const ORTHONYCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Orthonychidae": "#786850" }, breedGroupColor: "#786850", hybridColor: "#a8b0b8" };
const PACHYCEPHALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pachycephalidae": "#c89840" }, breedGroupColor: "#c89840", hybridColor: "#a8b0b8" };
const PARADOXORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Paradoxornithidae": "#a08058" }, breedGroupColor: "#a08058", hybridColor: "#a8b0b8" };
const PARAMYTHIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Paramythiidae": "#6090a8" }, breedGroupColor: "#6090a8", hybridColor: "#a8b0b8" };
const PARDALOTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pardalotidae": "#a8a050" }, breedGroupColor: "#a8a050", hybridColor: "#a8b0b8" };
const PASSERELLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Passerellidae": "#889070" }, breedGroupColor: "#889070", hybridColor: "#a8b0b8" };
const PEDIONOMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pedionomidae": "#c0a870" }, breedGroupColor: "#c0a870", hybridColor: "#a8b0b8" };
const PELLORNEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pellorneidae": "#887058" }, breedGroupColor: "#887058", hybridColor: "#a8b0b8" };
const PETROICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Petroicidae": "#d04828" }, breedGroupColor: "#d04828", hybridColor: "#a8b0b8" };
const PEUCEDRAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Peucedramidae": "#c8a828" }, breedGroupColor: "#c8a828", hybridColor: "#a8b0b8" };
const PHAENICOPHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Phaenicophilidae": "#68a058" }, breedGroupColor: "#68a058", hybridColor: "#a8b0b8" };
const PHAETHONTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Phaethontidae": "#e8e8e0" }, breedGroupColor: "#e8e8e0", hybridColor: "#a8b0b8" };
const PHILEPITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Philepittidae": "#60a028" }, breedGroupColor: "#60a028", hybridColor: "#a8b0b8" };
const PHOENICULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Phoeniculidae": "#2888a0" }, breedGroupColor: "#2888a0", hybridColor: "#a8b0b8" };
const PICATHARTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Picathartidae": "#d8c8a0" }, breedGroupColor: "#d8c8a0", hybridColor: "#a8b0b8" };
const PIPRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pipridae": "#3858a0" }, breedGroupColor: "#3858a0", hybridColor: "#a8b0b8" };
const PITTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pittidae": "#c84848" }, breedGroupColor: "#c84848", hybridColor: "#a8b0b8" };
const PITYRIASIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pityriasidae": "#483830" }, breedGroupColor: "#483830", hybridColor: "#a8b0b8" };
const PLATYLOPHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Platylophidae": "#506880" }, breedGroupColor: "#506880", hybridColor: "#a8b0b8" };
const PLATYSTEIRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Platysteiridae": "#5880a0" }, breedGroupColor: "#5880a0", hybridColor: "#a8b0b8" };
const PLOCEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ploceidae": "#c0a020" }, breedGroupColor: "#c0a020", hybridColor: "#a8b0b8" };
const PLUVIANELLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pluvianellidae": "#a0a8a0" }, breedGroupColor: "#a0a8a0", hybridColor: "#a8b0b8" };
const PLUVIANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pluvianidae": "#b0b8a0" }, breedGroupColor: "#b0b8a0", hybridColor: "#a8b0b8" };
const PNOEPYGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pnoepygidae": "#a88860" }, breedGroupColor: "#a88860", hybridColor: "#a8b0b8" };
const PODARGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Podargidae": "#a08868" }, breedGroupColor: "#a08868", hybridColor: "#a8b0b8" };
const POMATOSTOMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pomatostomidae": "#887060" }, breedGroupColor: "#887060", hybridColor: "#a8b0b8" };
const PROMEROPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Promeropidae": "#a09848" }, breedGroupColor: "#a09848", hybridColor: "#a8b0b8" };
const PSITTACULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Psittaculidae": "#20a060" }, breedGroupColor: "#20a060", hybridColor: "#a8b0b8" };
const PSOPHIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Psophiidae": "#688898" }, breedGroupColor: "#688898", hybridColor: "#a8b0b8" };
const PSOPHODIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Psophodidae": "#a09868" }, breedGroupColor: "#a09868", hybridColor: "#a8b0b8" };
const PTILIOGONATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ptiliogonatidae": "#6070a0" }, breedGroupColor: "#6070a0", hybridColor: "#a8b0b8" };
const RHAGOLOGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhagologidae": "#a08860" }, breedGroupColor: "#a08860", hybridColor: "#a8b0b8" };
const RHEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rheidae": "#a09878" }, breedGroupColor: "#a09878", hybridColor: "#a8b0b8" };
const RHINOCRYPTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhinocryptidae": "#686058" }, breedGroupColor: "#686058", hybridColor: "#a8b0b8" };
const RHIPIDURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhipiduridae": "#688898" }, breedGroupColor: "#688898", hybridColor: "#a8b0b8" };
const RHODINOCICHLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhodinocichlidae": "#d07050" }, breedGroupColor: "#d07050", hybridColor: "#a8b0b8" };
const RHYNOCHETIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhynochetidae": "#789098" }, breedGroupColor: "#789098", hybridColor: "#a8b0b8" };
const ROSTRATULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rostratulidae": "#b09870" }, breedGroupColor: "#b09870", hybridColor: "#a8b0b8" };
const SALPORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Salpornithidae": "#8a7860" }, breedGroupColor: "#8a7860", hybridColor: "#a8b0b8" };
const SAPAYOIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sapayoidae": "#50a060" }, breedGroupColor: "#50a060", hybridColor: "#a8b0b8" };
const SAROTHRURIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sarothruridae": "#a07858" }, breedGroupColor: "#a07858", hybridColor: "#a8b0b8" };
const SCOPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Scopidae": "#8a7850" }, breedGroupColor: "#8a7850", hybridColor: "#a8b0b8" };
const SCOTOCERCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Scotocercidae": "#a89878" }, breedGroupColor: "#a89878", hybridColor: "#a8b0b8" };
const SEMNORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Semnornithidae": "#c89830" }, breedGroupColor: "#c89830", hybridColor: "#a8b0b8" };
const SPINDALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Spindalidae": "#c8a028" }, breedGroupColor: "#c8a028", hybridColor: "#a8b0b8" };
const STEATORNITHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Steatornithidae": "#d8c8a0" }, breedGroupColor: "#d8c8a0", hybridColor: "#a8b0b8" };
const STENOSTIRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Stenostiridae": "#6090c0" }, breedGroupColor: "#6090c0", hybridColor: "#a8b0b8" };
const STRIGOPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Strigopidae": "#688868" }, breedGroupColor: "#688868", hybridColor: "#a8b0b8" };
const STRUTHIONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Struthionidae": "#807060" }, breedGroupColor: "#807060", hybridColor: "#a8b0b8" };
const TERETISTRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Teretistridae": "#c8a020" }, breedGroupColor: "#c8a020", hybridColor: "#a8b0b8" };
const THAMNOPHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Thamnophilidae": "#586060" }, breedGroupColor: "#586060", hybridColor: "#a8b0b8" };
const THINOCORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Thinocoridae": "#a0a878" }, breedGroupColor: "#a0a878", hybridColor: "#a8b0b8" };
const TICHODROMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tichodromidae": "#a09070" }, breedGroupColor: "#a09070", hybridColor: "#a8b0b8" };
const TIMALIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Timaliidae": "#a07048" }, breedGroupColor: "#a07048", hybridColor: "#a8b0b8" };
const TINAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tinamidae": "#a09070" }, breedGroupColor: "#a09070", hybridColor: "#a8b0b8" };
const TITYRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tityridae": "#688898" }, breedGroupColor: "#688898", hybridColor: "#a8b0b8" };
const TODIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Todidae": "#50b060" }, breedGroupColor: "#50b060", hybridColor: "#a8b0b8" };
const TROGONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Trogonidae": "#20a060" }, breedGroupColor: "#20a060", hybridColor: "#a8b0b8" };
const TURNICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Turnicidae": "#a09060" }, breedGroupColor: "#a09060", hybridColor: "#a8b0b8" };
const UROCYNCHRAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Urocynchramidae": "#a08868" }, breedGroupColor: "#a08868", hybridColor: "#a8b0b8" };
const VANGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Vangidae": "#60a088" }, breedGroupColor: "#60a088", hybridColor: "#a8b0b8" };
const VIDUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Viduidae": "#384848" }, breedGroupColor: "#384848", hybridColor: "#a8b0b8" };
const ZELEDONIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Zeledoniidae": "#687050" }, breedGroupColor: "#687050", hybridColor: "#a8b0b8" };
const ZOSTEROPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Zosteropidae": "#68a058" }, breedGroupColor: "#68a058", hybridColor: "#a8b0b8" };


const TACHYGLOSSIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Echidnas": "#a08050" }, breedGroupColor: "#907040", hybridColor: "#c0a070" };
const CORDYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Girdled Lizards": "#688848" }, breedGroupColor: "#587838", hybridColor: "#88a868" };
const LIBELLULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Skimmers": "#48a0b0" }, breedGroupColor: "#3890a0", hybridColor: "#68c0d0" };
const NOTHOBRANCHIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "African Killifishes": "#e88848" }, breedGroupColor: "#d07838", hybridColor: "#f0a868" };

const OCTOPODIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Octopuses": "#c86040" }, breedGroupColor: "#b05030", hybridColor: "#e08060" };
const LOLIGINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Inshore Squids": "#7090b0" }, breedGroupColor: "#6080a0", hybridColor: "#90b0d0" };
const OMMASTREPHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Flying Squids": "#b07090" }, breedGroupColor: "#a06080", hybridColor: "#d090b0" };
const ARCHITEUTHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Giant Squids": "#d0c8b0" }, breedGroupColor: "#c0b8a0", hybridColor: "#e8e0d0" };
const SEPIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cuttlefish": "#60b0a0" }, breedGroupColor: "#50a090", hybridColor: "#80d0c0" };
const NAUTILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nautiluses": "#d0b080" }, breedGroupColor: "#c0a070", hybridColor: "#e8d0b0" };
const VAMPYROTEUTHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Vampire Squid": "#a03040" }, breedGroupColor: "#802030", hybridColor: "#c05060" };
const SPIRULIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ram\'s Horn Squid": "#a09888" }, breedGroupColor: "#908878", hybridColor: "#c0b8a8" };

const SCYLORHINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Catsharks": "#6880a8" }, breedGroupColor: "#587098", hybridColor: "#88a0c8" };
const DASYATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Whiptail Stingrays": "#887868" }, breedGroupColor: "#786858", hybridColor: "#a89878" };
const LABRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Wrasses": "#60b0c8", "Parrotfish": "#c8e060" }, breedGroupColor: "#50a0b8", hybridColor: "#80d0e0" };
const SYNGNATHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Seahorses": "#d0a860", "Pipefish": "#88b8a0", "Seadragons": "#c08050" }, breedGroupColor: "#b89850", hybridColor: "#e0c880" };
const CARABIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ground Beetles": "#3a3a3a" }, breedGroupColor: "#2a2a2a", hybridColor: "#5a5a5a" };
const CHRYSOMELIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Leaf Beetles": "#c8a840" }, breedGroupColor: "#b89830", hybridColor: "#e0c860" };
const AGELENIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Funnel Weavers": "#786048" }, breedGroupColor: "#685038", hybridColor: "#988068" };
const PHOLCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cellar Spiders": "#c8b8a8" }, breedGroupColor: "#b8a898", hybridColor: "#e0d0c0" };
const AMPHISBAENIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Worm Lizards": "#c0a090" }, breedGroupColor: "#b09080", hybridColor: "#d8c0b0" };
const EUBLEPHARIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Eyelid Geckos": "#d8b848" }, breedGroupColor: "#c8a838", hybridColor: "#e8d068" };

const COLUBRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Typical Snakes": "#788860" }, breedGroupColor: "#687850", hybridColor: "#98a880" };
const LACERTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Lizards": "#90a868" }, breedGroupColor: "#809858", hybridColor: "#b0c888" };
const ANGUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Glass Lizards": "#b09878" }, breedGroupColor: "#a08868", hybridColor: "#c8b898" };
const VARANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Monitor Lizards": "#788878" }, breedGroupColor: "#687868", hybridColor: "#98a898" };
const GEKKONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Geckos": "#c0b050" }, breedGroupColor: "#b0a040", hybridColor: "#d8c870" };
const SCINCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Skinks": "#b0a888" }, breedGroupColor: "#a09878", hybridColor: "#c8c0a8" };
const AGAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Dragon Lizards": "#c09858" }, breedGroupColor: "#b08848", hybridColor: "#d8b878" };
const IGUANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Iguanas": "#78a868" }, breedGroupColor: "#689858", hybridColor: "#98c888" };
const ELAPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Elapid Snakes": "#d0a030" }, breedGroupColor: "#c09020", hybridColor: "#e8c050" };
const PYTHONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pythons": "#a08050" }, breedGroupColor: "#907040", hybridColor: "#c0a070" };
const CHELONIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sea Turtles": "#508088" }, breedGroupColor: "#407078", hybridColor: "#70a0a8" };
const DERMOCHELYIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Leatherback Turtles": "#484848" }, breedGroupColor: "#383838", hybridColor: "#686868" };
const CROCODYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Crocodiles": "#687848" }, breedGroupColor: "#586838", hybridColor: "#889868" };
const ALLIGATORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Alligators & Caimans": "#506838" }, breedGroupColor: "#405828", hybridColor: "#708858" };
const SPHENODONTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tuatara": "#809070" }, breedGroupColor: "#708060", hybridColor: "#a0b090" };

const FORMICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Ants": "#8a4828" }, breedGroupColor: "#6a3818", hybridColor: "#aa6848" };
const VESPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Social Wasps": "#c8a028", "Solitary Wasps": "#a08018" }, breedGroupColor: "#b89020", hybridColor: "#e0c048" };
const NYMPHALIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Brush-foots": "#e87830", "Admirals & Relatives": "#c85820" }, breedGroupColor: "#d06828", hybridColor: "#f09850" };
const CICHLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "African Cichlids": "#2090c0", "American Cichlids": "#30b080" }, breedGroupColor: "#2880a0", hybridColor: "#50b0d8" };
const SCOMBRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Tunas": "#2848a0", "Mackerels": "#4070b8" }, breedGroupColor: "#3858a8", hybridColor: "#6888c8" };
const CHARACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Characins": "#c0c0d8" }, breedGroupColor: "#b0b0c8", hybridColor: "#d8d8f0" };
const BOIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Boas": "#a07050" }, breedGroupColor: "#906040", hybridColor: "#c09070" };
const LAMNIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mackerel Sharks": "#486878" }, breedGroupColor: "#385868", hybridColor: "#688898" };
const PIPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Clawed Frogs": "#808060" }, breedGroupColor: "#707050", hybridColor: "#a0a080" };
const PELOBATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Spadefoot Toads": "#a09858" }, breedGroupColor: "#908848", hybridColor: "#c0b878" };


const BUFONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "European Toads": "#6a7858", "New World Toads": "#8a7040", "Tropical Toads": "#a08050" }, breedGroupColor: "#7a7848", hybridColor: "#9a9868" };
const HYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "European Tree Frogs": "#5a9050", "New World Tree Frogs": "#78b048", "Australian Tree Frogs": "#98c068" }, breedGroupColor: "#6aaa58", hybridColor: "#90c878" };
const DENDROBATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Poison Dart Frogs": "#2870b8", "Thumbnail Frogs": "#e8b820" }, breedGroupColor: "#4878a8", hybridColor: "#70a8d8" };
const MICROHYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Old World Narrow-mouthed Frogs": "#8a8850", "New World Narrow-mouthed Frogs": "#7a7840", "Malagasy Narrow-mouthed Frogs": "#a89858" }, breedGroupColor: "#888048", hybridColor: "#a8a868" };
const PLETHODONTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Woodland Salamanders": "#9a4830", "Cave Salamanders": "#d89858", "Brook Salamanders": "#7a3820" }, breedGroupColor: "#8a4028", hybridColor: "#c07848" };
const AMBYSTOMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mole Salamanders": "#486880", "Axolotl": "#d8a868" }, breedGroupColor: "#5a7888", hybridColor: "#78a0b8" };
const CRYPTOBRANCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Giant Salamanders": "#6a5040", "Hellbender": "#8a7050" }, breedGroupColor: "#7a6048", hybridColor: "#9a8060" };
const PROTEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cave Salamanders": "#e8d8c8", "Mudpuppies": "#a89080" }, breedGroupColor: "#c8b8a8", hybridColor: "#e8e0d8" };
const CAECILIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tropical Caecilians": "#a87848", "Aquatic Caecilians": "#5a7888" }, breedGroupColor: "#987040", hybridColor: "#c89860" };

const THERAPHOSIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Old World Tarantulas": "#4a3050", "New World Tarantulas": "#c87030", "Australian Tarantulas": "#8a5028" }, breedGroupColor: "#7a5030", hybridColor: "#a07848" };
const SALTICIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Peacock Spiders": "#e84898", "Portia": "#4a5838", "Phidippus": "#c84030", "Hyllus": "#7a6848" }, breedGroupColor: "#905040", hybridColor: "#b87060" };
const ARANEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Garden Spiders": "#8a9030", "Banded Spiders": "#c8a820", "Tropical Orb-weavers": "#6a7820" }, breedGroupColor: "#808030", hybridColor: "#a0a840" };
const THERIDIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Widow Spiders": "#8a1a1a", "False Widows": "#583858", "House Spiders": "#5a5040" }, breedGroupColor: "#6a2828", hybridColor: "#9a4848" };
const LYCOSIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "European Wolf Spiders": "#8a7040", "New World Wolf Spiders": "#a08050", "Semiaquatic Wolf Spiders": "#3a6858" }, breedGroupColor: "#806038", hybridColor: "#b08850" };
const SICARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Brown Recluses": "#7a4020", "Six-eyed Sand Spiders": "#c8b068" }, breedGroupColor: "#7a5030", hybridColor: "#a07848" };
const ATRACIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sydney Funnel-webs": "#1a1a28", "Tree Funnel-webs": "#2a3840" }, breedGroupColor: "#1a2030", hybridColor: "#3a4858" };
const BUTHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "North African Scorpions": "#c8a020", "Middle Eastern Scorpions": "#e8c030", "American Scorpions": "#d89820", "African Forest Scorpions": "#7a6030" }, breedGroupColor: "#c09820", hybridColor: "#e8d040" };
const SCORPIONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "African Giant Scorpions": "#3a5828", "Asian Forest Scorpions": "#2a4820" }, breedGroupColor: "#3a5020", hybridColor: "#5a7840" };

const ASTERIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Asterias": "#E87040",
    "Pisaster": "#E85020",
    "Leptasterias": "#C06030",
    "Henricia": "#F09060",
    "Coscinasterias": "#D07050",
  },
  breedGroupColor: "#E87040",
  hybridColor: "#F0A080",
};

const ECHINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Echinus": "#40A888",
    "Strongylocentrotus": "#309878",
    "Psammechinus": "#50B898",
    "Paracentrotus": "#60C8A8",
  },
  breedGroupColor: "#40A888",
  hybridColor: "#80D0B8",
};

const HOLOTHURIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Holothuria": "#A070C8",
    "Actinopyga": "#9060B8",
    "Bohadschia": "#B080D8",
    "Pearsonothuria": "#C090E0",
  },
  breedGroupColor: "#A070C8",
  hybridColor: "#C0A0E0",
};

const PSITTACIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Ara":     "#D04030",
    "Amazona": "#30A040",
    "Anodorhynchus": "#2850A0",
    "Aratinga": "#E8B030",
    "Pyrrhura": "#60B048",
    "Pionus":   "#6090A0",
    "Forpus":   "#80C868",
    "Psittacus":   "#B0A898",
    "Poicephalus": "#C0A858",
    "Eupsittula":  "#D8A020",
    "Brotogeris":  "#50C070",
    "Psittacara":  "#C89030",
  },
  breedGroupColor: "#30A040",
  hybridColor: "#60C060",
};

const PAPILIONIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Swallowtails":              "#E89030",
    "Apollos":                   "#D8C8C0",
    "Scarce swallowtails":       "#E8C830",
    "Festoons":                  "#E8A020",
    "Swordtails":                "#30A070",
    "Birdwings":                 "#E84838",
    "Birdwings & cattlehearts":  "#D06030",
    "Pipevine swallowtails":     "#8840A8",
    "Kite swallowtails":         "#88B8C8",
    "Mimic swallowtails":        "#C88040",
    "Dragontails":               "#40A0B8",
    "Kaiser-i-Hind":             "#30A060",
    "Bhutan swallowtails":       "#888838",
    "Luehdorfia":                "#C8A060",
    "Sericinus":                 "#A88848",
    "Hook-tip swallowtails":     "#B08030",
  },
  breedGroupColor: "#C87830",
  hybridColor: "#E8A860",
};

const COTTIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Freshwater sculpins": "#788850",
    "Marine sculpins":     "#488090",
    "Arctic sculpins":     "#6898B8",
    "Tidepool sculpins":   "#A8A068",
  },
  breedGroupColor: "#688060",
  hybridColor: "#88A880",
};

const PLEURONECTIDAE_THEME: ColorTheme = {
  subfamilyColors: {
    "Pleuronectinae":   "#6B8FA8",
    "Poecilopsettinae": "#8BA88B",
    "Rhombosoleinae":   "#A8986B",
  },
  lineageColors: {
    "Plaice & flounders": "#7A9AB8",
    "Dabs & witches":     "#5A8878",
    "Long rough dabs":    "#889068",
    "Halibut":            "#4A7898",
    "Soles & flounders":  "#C8A878",
  },
  breedGroupColor: "#6B8FA8",
  hybridColor: "#8AA8C8",
};

const ANGUILLIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Freshwater eels": "#3A8878",
  },
  breedGroupColor: "#3A8878",
  hybridColor: "#5AA898",
};

const GASTEROSTEIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Typical sticklebacks":  "#7898B8",
    "Ninespine sticklebacks": "#C87850",
    "Sea sticklebacks":      "#68A0A0",
    "Fourspine sticklebacks": "#A8B068",
    "Brook sticklebacks":    "#887858",
  },
  breedGroupColor: "#7898B8",
  hybridColor: "#8AA8C8",
};

const PLEUROBRACHIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Pleurobrachia": "#33C1B1",
    "Hormiphora": "#269BB0",
    "Tinerfe": "#1D7B8C",
  },
  breedGroupColor: "#33C1B1",
  hybridColor: "#8AA8C8",
};

const MERTENSIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Mertensia": "#52D1DC",
    "Callianira": "#0D5C75",
    "Charistephane": "#08A4BD",
  },
  breedGroupColor: "#52D1DC",
  hybridColor: "#8AA8C8",
};

const BOLINOPSIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Bolinopsis": "#4EA8DE",
    "Mnemiopsis": "#560BAD",
    "Lesueuria": "#4895EF",
  },
  breedGroupColor: "#4EA8DE",
  hybridColor: "#8AA8C8",
};

const CESTIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Cestum": "#B5179E",
    "Velamen": "#7209B7",
  },
  breedGroupColor: "#B5179E",
  hybridColor: "#8AA8C8",
};

const COELOPLANIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Coeloplana": "#3F37C9",
    "Vallicula": "#4CC9F0",
  },
  breedGroupColor: "#3F37C9",
  hybridColor: "#8AA8C8",
};

const BEROIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: {
    "Beroe": "#F72585",
    "Neis": "#7209B7",
    "Maotianoascus": "#3F37C9",
  },
  breedGroupColor: "#F72585",
  hybridColor: "#8AA8C8",
};

// ── Cubozoa (Box jellyfish) ──
const ALATINIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Alatina: "#28A0C8", Manokia: "#1A7898", Keesingia: "#3AB8D8" },
  breedGroupColor: "#28A0C8",
  hybridColor: "#58C8E8",
};
const CARUKIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Carukia: "#E84078", Malo: "#C82858", Gerongia: "#F05890", Morbakka: "#D83868" },
  breedGroupColor: "#E84078",
  hybridColor: "#F078A8",
};
const CARYBDEIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Carybdea: "#3848A8" },
  breedGroupColor: "#3848A8",
  hybridColor: "#6878C8",
};
const TAMOYIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Tamoya: "#E8A828" },
  breedGroupColor: "#E8A828",
  hybridColor: "#F0C858",
};
const TRIPEDALIIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Tripedalia: "#40B868", Copula: "#68D890" },
  breedGroupColor: "#40B868",
  hybridColor: "#78E0A0",
};
const CHIRODROPIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Chirodropus: "#C82820", Chironex: "#E04030", Chirodectes: "#A81810" },
  breedGroupColor: "#C82820",
  hybridColor: "#E86050",
};
const CHIROPSALMIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Chiropsalmus: "#E89828", Chiropsoides: "#C88018" },
  breedGroupColor: "#E89828",
  hybridColor: "#F0B858",
};
const CHIROPSELIDAE_THEME: ColorTheme = {
  subfamilyColors: {},
  lineageColors: { Chiropsella: "#8830B8", Meteorona: "#A048D8" },
  breedGroupColor: "#8830B8",
  hybridColor: "#B870E0",
};

// ── Scyphozoa (True jellyfish) ──
const ATOLLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Atollidae": "#C83040" }, breedGroupColor: "#C83040", hybridColor: "#E06070" };
const LINUCHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Linuchidae": "#5030A0" }, breedGroupColor: "#5030A0", hybridColor: "#8060C0" };
const NAUSITHOIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Nausithoidae": "#882040" }, breedGroupColor: "#882040", hybridColor: "#B85070" };
const PARAPHYLLINIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Paraphyllinidae": "#A02868" }, breedGroupColor: "#A02868", hybridColor: "#C85888" };
const PERIPHYLLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Periphyllidae": "#701830" }, breedGroupColor: "#701830", hybridColor: "#A04860" };
const CYANEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cyaneidae": "#E84028" }, breedGroupColor: "#E84028", hybridColor: "#F07058" };
const DRYMONEMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Drymonematidae": "#20A090" }, breedGroupColor: "#20A090", hybridColor: "#50C0B0" };
const PELAGIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pelagiidae": "#A840A8" }, breedGroupColor: "#A840A8", hybridColor: "#C870C8" };
const PHACELLOPHORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Phacellophoridae": "#E87050" }, breedGroupColor: "#E87050", hybridColor: "#F09878" };
const ULMARIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Ulmaridae": "#4890C0" }, breedGroupColor: "#4890C0", hybridColor: "#78B8D8" };
const ARCHIRHIZIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Archirhizidae": "#B89868" }, breedGroupColor: "#B89868", hybridColor: "#D0B890" };
const CASSIOPEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cassiopeidae": "#88A828" }, breedGroupColor: "#88A828", hybridColor: "#B0D058" };
const CATOSTYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Catostylidae": "#789048" }, breedGroupColor: "#789048", hybridColor: "#98B868" };
const CEPHEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cepheidae": "#C0A070" }, breedGroupColor: "#C0A070", hybridColor: "#D8C098" };
const LOBONEMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lobonematidae": "#E8A0A8" }, breedGroupColor: "#E8A0A8", hybridColor: "#F0C0C8" };
const LYCHNORHIZIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lychnorhizidae": "#4878A0" }, breedGroupColor: "#4878A0", hybridColor: "#78A0C0" };
const MASTIGIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Mastigiidae": "#E88828" }, breedGroupColor: "#E88828", hybridColor: "#F0B058" };
const RHIZOSTOMATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Rhizostomatidae": "#5878A0" }, breedGroupColor: "#5878A0", hybridColor: "#80A0C0" };
const STOMOLOPHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Stomolophidae": "#C09840" }, breedGroupColor: "#C09840", hybridColor: "#D8B870" };
const VERSURIGIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Versurigidae": "#9890C8" }, breedGroupColor: "#9890C8", hybridColor: "#B8B0E0" };

// ── Staurozoa (Stalked jellyfish) ──
const CRATEROLOPHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Craterolophidae": "#48A060" }, breedGroupColor: "#48A060", hybridColor: "#78C090" };
const HALICLYSTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Haliclystidae": "#A08040" }, breedGroupColor: "#A08040", hybridColor: "#C8A868" };
const KISHINOUYEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Kishinouyeidae": "#D8A830" }, breedGroupColor: "#D8A830", hybridColor: "#E8C860" };
const KYOPODIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Kyopodiidae": "#B89868" }, breedGroupColor: "#B89868", hybridColor: "#D0B890" };
const LIPKEIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lipkeidae": "#B86838" }, breedGroupColor: "#B86838", hybridColor: "#D08858" };
const LUCERNARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Lucernariidae": "#78A880" }, breedGroupColor: "#78A880", hybridColor: "#98C8A0" };
const TESSERANTHIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tesseranthidae": "#A09078" }, breedGroupColor: "#A09078", hybridColor: "#C0B098" };

export const IUCN_COLORS: Record<string, string> = {
  EX: "#6B6B6B",
  EW: "#9C9C9C",
  CR: "#D82E2E",
  EN: "#E87030",
  VU: "#E8B820",
  NT: "#B8B820",
  LC: "#60B060",
  DD: "#8888A8",
  NE: "#AAAAAA",
};


// ── Hydrozoa (141 families) ──
const hydrozoa_sertulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "sertulariidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Sertulariidae", mainColor: "#EF4444", lineageColors: { "sertulariidae": "#14B8A6" } };
const hydrozoa_aglaopheniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "aglaopheniidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Aglaopheniidae", mainColor: "#10B981", lineageColors: { "aglaopheniidae": "#F97316" } };
const hydrozoa_plumulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "plumulariidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Plumulariidae", mainColor: "#F59E0B", lineageColors: { "plumulariidae": "#6366F1" } };
const hydrozoa_campanulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "campanulariidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Campanulariidae", mainColor: "#8B5CF6", lineageColors: { "campanulariidae": "#84CC16" } };
const hydrozoa_sertularellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "sertularellidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Sertularellidae", mainColor: "#EC4899", lineageColors: { "sertularellidae": "#06B6D4" } };
const hydrozoa_haleciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "haleciidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Haleciidae", mainColor: "#14B8A6", lineageColors: { "haleciidae": "#D946EF" } };
const hydrozoa_halopterididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "halopterididae", className: "Hydrozoa", orderName: "Leptothecata", name: "Halopterididae", mainColor: "#F97316", lineageColors: { "halopterididae": "#0EA5E9" } };
const hydrozoa_symplectoscyphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "symplectoscyphidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Symplectoscyphidae", mainColor: "#6366F1", lineageColors: { "symplectoscyphidae": "#22C55E" } };
const hydrozoa_eirenidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "eirenidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Eirenidae", mainColor: "#84CC16", lineageColors: { "eirenidae": "#EAB308" } };
const hydrozoa_lafoeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "lafoeidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Lafoeidae", mainColor: "#06B6D4", lineageColors: { "lafoeidae": "#A855F7" } };
const hydrozoa_zygophylacidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "zygophylacidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Zygophylacidae", mainColor: "#D946EF", lineageColors: { "zygophylacidae": "#FB923C" } };
const hydrozoa_hebellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "hebellidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Hebellidae", mainColor: "#0EA5E9", lineageColors: { "hebellidae": "#2DD4BF" } };
const hydrozoa_kirchenpaueriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "kirchenpaueriidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Kirchenpaueriidae", mainColor: "#22C55E", lineageColors: { "kirchenpaueriidae": "#A3E635" } };
const hydrozoa_aequoreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "aequoreidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Aequoreidae", mainColor: "#EAB308", lineageColors: { "aequoreidae": "#38BDF8" } };
const hydrozoa_lovenellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "lovenellidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Lovenellidae", mainColor: "#A855F7", lineageColors: { "lovenellidae": "#3B82F6" } };
const hydrozoa_campanulinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "campanulinidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Campanulinidae", mainColor: "#FB923C", lineageColors: { "campanulinidae": "#EF4444" } };
const hydrozoa_syntheciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "syntheciidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Syntheciidae", mainColor: "#2DD4BF", lineageColors: { "syntheciidae": "#10B981" } };
const hydrozoa_laodiceidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "laodiceidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Laodiceidae", mainColor: "#A3E635", lineageColors: { "laodiceidae": "#F59E0B" } };
const hydrozoa_gonaxiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "gonaxiidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Gonaxiidae", mainColor: "#38BDF8", lineageColors: { "gonaxiidae": "#8B5CF6" } };
const hydrozoa_schizotrichidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "schizotrichidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Schizotrichidae", mainColor: "#3B82F6", lineageColors: { "schizotrichidae": "#EC4899" } };
const hydrozoa_phylactothecidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "phylactothecidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Phylactothecidae", mainColor: "#EF4444", lineageColors: { "phylactothecidae": "#14B8A6" } };
const hydrozoa_staurothecidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "staurothecidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Staurothecidae", mainColor: "#10B981", lineageColors: { "staurothecidae": "#F97316" } };
const hydrozoa_mitrocomidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "mitrocomidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Mitrocomidae", mainColor: "#F59E0B", lineageColors: { "mitrocomidae": "#6366F1" } };
const hydrozoa_malagazziidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "malagazziidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Malagazziidae", mainColor: "#8B5CF6", lineageColors: { "malagazziidae": "#84CC16" } };
const hydrozoa_thyroscyphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "thyroscyphidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Thyroscyphidae", mainColor: "#EC4899", lineageColors: { "thyroscyphidae": "#06B6D4" } };
const hydrozoa_tiarannidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "tiarannidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Tiarannidae", mainColor: "#14B8A6", lineageColors: { "tiarannidae": "#D946EF" } };
const hydrozoa_phialellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "phialellidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Phialellidae", mainColor: "#F97316", lineageColors: { "phialellidae": "#0EA5E9" } };
const hydrozoa_bonneviellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "bonneviellidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Bonneviellidae", mainColor: "#6366F1", lineageColors: { "bonneviellidae": "#22C55E" } };
const hydrozoa_tiaropsidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "tiaropsidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Tiaropsidae", mainColor: "#84CC16", lineageColors: { "tiaropsidae": "#EAB308" } };
const hydrozoa_melicertidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "melicertidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Melicertidae", mainColor: "#06B6D4", lineageColors: { "melicertidae": "#A855F7" } };
const hydrozoa_dipleurosomatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "dipleurosomatidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Dipleurosomatidae", mainColor: "#D946EF", lineageColors: { "dipleurosomatidae": "#FB923C" } };
const hydrozoa_cirrholoveniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "cirrholoveniidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Cirrholoveniidae", mainColor: "#0EA5E9", lineageColors: { "cirrholoveniidae": "#2DD4BF" } };
const hydrozoa_octocannoididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "octocannoididae", className: "Hydrozoa", orderName: "Leptothecata", name: "Octocannoididae", mainColor: "#22C55E", lineageColors: { "octocannoididae": "#A3E635" } };
const hydrozoa_lineolariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "lineolariidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Lineolariidae", mainColor: "#EAB308", lineageColors: { "lineolariidae": "#38BDF8" } };
const hydrozoa_orchistomatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "orchistomatidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Orchistomatidae", mainColor: "#A855F7", lineageColors: { "orchistomatidae": "#3B82F6" } };
const hydrozoa_sugiuridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "sugiuridae", className: "Hydrozoa", orderName: "Leptothecata", name: "Sugiuridae", mainColor: "#FB923C", lineageColors: { "sugiuridae": "#EF4444" } };
const hydrozoa_teclaiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "teclaiidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Teclaiidae", mainColor: "#2DD4BF", lineageColors: { "teclaiidae": "#10B981" } };
const hydrozoa_clathrozoidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "clathrozoidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Clathrozoidae", mainColor: "#A3E635", lineageColors: { "clathrozoidae": "#F59E0B" } };
const hydrozoa_wuvulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "wuvulidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Wuvulidae", mainColor: "#38BDF8", lineageColors: { "wuvulidae": "#8B5CF6" } };
const hydrozoa_blackfordiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "blackfordiidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Blackfordiidae", mainColor: "#3B82F6", lineageColors: { "blackfordiidae": "#EC4899" } };
const hydrozoa_barcinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "barcinidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Barcinidae", mainColor: "#EF4444", lineageColors: { "barcinidae": "#14B8A6" } };
const hydrozoa_palaequoreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "palaequoreidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Palaequoreidae", mainColor: "#10B981", lineageColors: { "palaequoreidae": "#F97316" } };
const hydrozoa_phialuciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "phialuciidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Phialuciidae", mainColor: "#F59E0B", lineageColors: { "phialuciidae": "#6366F1" } };
const hydrozoa_plumaleciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "plumaleciidae", className: "Hydrozoa", orderName: "Leptothecata", name: "Plumaleciidae", mainColor: "#8B5CF6", lineageColors: { "plumaleciidae": "#84CC16" } };
const hydrozoa_stylasteridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "stylasteridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Stylasteridae", mainColor: "#EC4899", lineageColors: { "stylasteridae": "#06B6D4" } };
const hydrozoa_hydractiniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "hydractiniidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Hydractiniidae", mainColor: "#14B8A6", lineageColors: { "hydractiniidae": "#D946EF" } };
const hydrozoa_bougainvilliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "bougainvilliidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Bougainvilliidae", mainColor: "#F97316", lineageColors: { "bougainvilliidae": "#0EA5E9" } };
const hydrozoa_pandeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "pandeidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Pandeidae", mainColor: "#6366F1", lineageColors: { "pandeidae": "#22C55E" } };
const hydrozoa_corynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "corynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Corynidae", mainColor: "#84CC16", lineageColors: { "corynidae": "#EAB308" } };
const hydrozoa_corymorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "corymorphidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Corymorphidae", mainColor: "#06B6D4", lineageColors: { "corymorphidae": "#A855F7" } };
const hydrozoa_eudendriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "eudendriidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Eudendriidae", mainColor: "#D946EF", lineageColors: { "eudendriidae": "#FB923C" } };
const hydrozoa_tubulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "tubulariidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Tubulariidae", mainColor: "#0EA5E9", lineageColors: { "tubulariidae": "#2DD4BF" } };
const hydrozoa_hydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "hydridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Hydridae", mainColor: "#22C55E", lineageColors: { "hydridae": "#A3E635" } };
const hydrozoa_zancleidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "zancleidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Zancleidae", mainColor: "#EAB308", lineageColors: { "zancleidae": "#38BDF8" } };
const hydrozoa_bythotiaridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "bythotiaridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Bythotiaridae", mainColor: "#A855F7", lineageColors: { "bythotiaridae": "#3B82F6" } };
const hydrozoa_oceaniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "oceaniidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Oceaniidae", mainColor: "#FB923C", lineageColors: { "oceaniidae": "#EF4444" } };
const hydrozoa_milleporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "milleporidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Milleporidae", mainColor: "#2DD4BF", lineageColors: { "milleporidae": "#10B981" } };
const hydrozoa_cytaeididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "cytaeididae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Cytaeididae", mainColor: "#A3E635", lineageColors: { "cytaeididae": "#F59E0B" } };
const hydrozoa_candelabridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "candelabridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Candelabridae", mainColor: "#38BDF8", lineageColors: { "candelabridae": "#8B5CF6" } };
const hydrozoa_cladonematidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "cladonematidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Cladonematidae", mainColor: "#3B82F6", lineageColors: { "cladonematidae": "#EC4899" } };
const hydrozoa_rathkeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "rathkeidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Rathkeidae", mainColor: "#EF4444", lineageColors: { "rathkeidae": "#14B8A6" } };
const hydrozoa_protiaridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "protiaridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Protiaridae", mainColor: "#10B981", lineageColors: { "protiaridae": "#F97316" } };
const hydrozoa_proboscidactylidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "proboscidactylidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Proboscidactylidae", mainColor: "#F59E0B", lineageColors: { "proboscidactylidae": "#6366F1" } };
const hydrozoa_ptilocodiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "ptilocodiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Ptilocodiidae", mainColor: "#8B5CF6", lineageColors: { "ptilocodiidae": "#84CC16" } };
const hydrozoa_moerisiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "moerisiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Moerisiidae", mainColor: "#EC4899", lineageColors: { "moerisiidae": "#06B6D4" } };
const hydrozoa_sphaerocorynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "sphaerocorynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Sphaerocorynidae", mainColor: "#14B8A6", lineageColors: { "sphaerocorynidae": "#D946EF" } };
const hydrozoa_solanderiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "solanderiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Solanderiidae", mainColor: "#F97316", lineageColors: { "solanderiidae": "#0EA5E9" } };
const hydrozoa_cladocorynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "cladocorynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Cladocorynidae", mainColor: "#6366F1", lineageColors: { "cladocorynidae": "#22C55E" } };
const hydrozoa_zancleopsidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "zancleopsidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Zancleopsidae", mainColor: "#84CC16", lineageColors: { "zancleopsidae": "#EAB308" } };
const hydrozoa_hydrocorynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "hydrocorynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Hydrocorynidae", mainColor: "#06B6D4", lineageColors: { "hydrocorynidae": "#A855F7" } };
const hydrozoa_australomedusidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "australomedusidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Australomedusidae", mainColor: "#D946EF", lineageColors: { "australomedusidae": "#FB923C" } };
const hydrozoa_axoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "axoporidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Axoporidae", mainColor: "#0EA5E9", lineageColors: { "axoporidae": "#2DD4BF" } };
const hydrozoa_pennariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "pennariidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Pennariidae", mainColor: "#22C55E", lineageColors: { "pennariidae": "#A3E635" } };
const hydrozoa_rosalindidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "rosalindidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Rosalindidae", mainColor: "#EAB308", lineageColors: { "rosalindidae": "#38BDF8" } };
const hydrozoa_teissieridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "teissieridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Teissieridae", mainColor: "#A855F7", lineageColors: { "teissieridae": "#3B82F6" } };
const hydrozoa_hydrichthyidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "hydrichthyidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Hydrichthyidae", mainColor: "#FB923C", lineageColors: { "hydrichthyidae": "#EF4444" } };
const hydrozoa_magapiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "magapiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Magapiidae", mainColor: "#2DD4BF", lineageColors: { "magapiidae": "#10B981" } };
const hydrozoa_margelopsidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "margelopsidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Margelopsidae", mainColor: "#A3E635", lineageColors: { "margelopsidae": "#F59E0B" } };
const hydrozoa_eucodoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "eucodoniidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Eucodoniidae", mainColor: "#38BDF8", lineageColors: { "eucodoniidae": "#8B5CF6" } };
const hydrozoa_porpitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "porpitidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Porpitidae", mainColor: "#3B82F6", lineageColors: { "porpitidae": "#EC4899" } };
const hydrozoa_halimedusidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "halimedusidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Halimedusidae", mainColor: "#EF4444", lineageColors: { "halimedusidae": "#14B8A6" } };
const hydrozoa_acaulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "acaulidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Acaulidae", mainColor: "#10B981", lineageColors: { "acaulidae": "#F97316" } };
const hydrozoa_protohydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "protohydridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Protohydridae", mainColor: "#F59E0B", lineageColors: { "protohydridae": "#6366F1" } };
const hydrozoa_clathrozoellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "clathrozoellidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Clathrozoellidae", mainColor: "#8B5CF6", lineageColors: { "clathrozoellidae": "#84CC16" } };
const hydrozoa_rhysiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "rhysiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Rhysiidae", mainColor: "#EC4899", lineageColors: { "rhysiidae": "#06B6D4" } };
const hydrozoa_boreohydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "boreohydridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Boreohydridae", mainColor: "#14B8A6", lineageColors: { "boreohydridae": "#D946EF" } };
const hydrozoa_asyncorynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "asyncorynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Asyncorynidae", mainColor: "#F97316", lineageColors: { "asyncorynidae": "#0EA5E9" } };
const hydrozoa_cordylophoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "cordylophoridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Cordylophoridae", mainColor: "#6366F1", lineageColors: { "cordylophoridae": "#22C55E" } };
const hydrozoa_pteronemidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "pteronemidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Pteronemidae", mainColor: "#84CC16", lineageColors: { "pteronemidae": "#EAB308" } };
const hydrozoa_tricyclusidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "tricyclusidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Tricyclusidae", mainColor: "#06B6D4", lineageColors: { "tricyclusidae": "#A855F7" } };
const hydrozoa_niobiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "niobiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Niobiidae", mainColor: "#D946EF", lineageColors: { "niobiidae": "#FB923C" } };
const hydrozoa_boeromedusidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "boeromedusidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Boeromedusidae", mainColor: "#0EA5E9", lineageColors: { "boeromedusidae": "#2DD4BF" } };
const hydrozoa_trichydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "trichydridae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Trichydridae", mainColor: "#22C55E", lineageColors: { "trichydridae": "#A3E635" } };
const hydrozoa_paracorynidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "paracorynidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Paracorynidae", mainColor: "#EAB308", lineageColors: { "paracorynidae": "#38BDF8" } };
const hydrozoa_balellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "balellidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Balellidae", mainColor: "#A855F7", lineageColors: { "balellidae": "#3B82F6" } };
const hydrozoa_tubiclavoididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "tubiclavoididae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Tubiclavoididae", mainColor: "#FB923C", lineageColors: { "tubiclavoididae": "#EF4444" } };
const hydrozoa_jeanbouilloniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "jeanbouilloniidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Jeanbouilloniidae", mainColor: "#2DD4BF", lineageColors: { "jeanbouilloniidae": "#10B981" } };
const hydrozoa_heterastridiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "heterastridiidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Heterastridiidae", mainColor: "#A3E635", lineageColors: { "heterastridiidae": "#F59E0B" } };
const hydrozoa_heterotentaculidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "heterotentaculidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Heterotentaculidae", mainColor: "#38BDF8", lineageColors: { "heterotentaculidae": "#8B5CF6" } };
const hydrozoa_similiclavidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "similiclavidae", className: "Hydrozoa", orderName: "Anthoathecata", name: "Similiclavidae", mainColor: "#3B82F6", lineageColors: { "similiclavidae": "#EC4899" } };
const hydrozoa_diphyidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "diphyidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Diphyidae", mainColor: "#EF4444", lineageColors: { "diphyidae": "#14B8A6" } };
const hydrozoa_prayidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "prayidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Prayidae", mainColor: "#10B981", lineageColors: { "prayidae": "#F97316" } };
const hydrozoa_agalmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "agalmatidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Agalmatidae", mainColor: "#F59E0B", lineageColors: { "agalmatidae": "#6366F1" } };
const hydrozoa_rhodaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "rhodaliidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Rhodaliidae", mainColor: "#8B5CF6", lineageColors: { "rhodaliidae": "#84CC16" } };
const hydrozoa_abylidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "abylidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Abylidae", mainColor: "#EC4899", lineageColors: { "abylidae": "#06B6D4" } };
const hydrozoa_sphaeronectidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "sphaeronectidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Sphaeronectidae", mainColor: "#14B8A6", lineageColors: { "sphaeronectidae": "#D946EF" } };
const hydrozoa_clausophyidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "clausophyidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Clausophyidae", mainColor: "#F97316", lineageColors: { "clausophyidae": "#0EA5E9" } };
const hydrozoa_stephanomiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "stephanomiidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Stephanomiidae", mainColor: "#6366F1", lineageColors: { "stephanomiidae": "#22C55E" } };
const hydrozoa_cordagalmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "cordagalmatidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Cordagalmatidae", mainColor: "#84CC16", lineageColors: { "cordagalmatidae": "#EAB308" } };
const hydrozoa_rhizophysidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "rhizophysidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Rhizophysidae", mainColor: "#06B6D4", lineageColors: { "rhizophysidae": "#A855F7" } };
const hydrozoa_pyrostephidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "pyrostephidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Pyrostephidae", mainColor: "#D946EF", lineageColors: { "pyrostephidae": "#FB923C" } };
const hydrozoa_forskaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "forskaliidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Forskaliidae", mainColor: "#0EA5E9", lineageColors: { "forskaliidae": "#2DD4BF" } };
const hydrozoa_erennidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "erennidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Erennidae", mainColor: "#22C55E", lineageColors: { "erennidae": "#A3E635" } };
const hydrozoa_hippopodiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "hippopodiidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Hippopodiidae", mainColor: "#EAB308", lineageColors: { "hippopodiidae": "#38BDF8" } };
const hydrozoa_resomiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "resomiidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Resomiidae", mainColor: "#A855F7", lineageColors: { "resomiidae": "#3B82F6" } };
const hydrozoa_apolemiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "apolemiidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Apolemiidae", mainColor: "#FB923C", lineageColors: { "apolemiidae": "#EF4444" } };
const hydrozoa_physophoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "physophoridae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Physophoridae", mainColor: "#2DD4BF", lineageColors: { "physophoridae": "#10B981" } };
const hydrozoa_physaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "physaliidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Physaliidae", mainColor: "#A3E635", lineageColors: { "physaliidae": "#F59E0B" } };
const hydrozoa_tottonophyidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "tottonophyidae", className: "Hydrozoa", orderName: "Siphonophorae", name: "Tottonophyidae", mainColor: "#38BDF8", lineageColors: { "tottonophyidae": "#8B5CF6" } };
const hydrozoa_cuninidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "cuninidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Cuninidae", mainColor: "#3B82F6", lineageColors: { "cuninidae": "#EC4899" } };
const hydrozoa_solmarisidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "solmarisidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Solmarisidae", mainColor: "#EF4444", lineageColors: { "solmarisidae": "#14B8A6" } };
const hydrozoa_aeginidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "aeginidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Aeginidae", mainColor: "#10B981", lineageColors: { "aeginidae": "#F97316" } };
const hydrozoa_solmundaeginidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "solmundaeginidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Solmundaeginidae", mainColor: "#F59E0B", lineageColors: { "solmundaeginidae": "#6366F1" } };
const hydrozoa_tetraplatiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "tetraplatiidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Tetraplatiidae", mainColor: "#8B5CF6", lineageColors: { "tetraplatiidae": "#84CC16" } };
const hydrozoa_pseudaeginidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "pseudaeginidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Pseudaeginidae", mainColor: "#EC4899", lineageColors: { "pseudaeginidae": "#06B6D4" } };
const hydrozoa_polypodiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "polypodiidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Polypodiidae", mainColor: "#14B8A6", lineageColors: { "polypodiidae": "#D946EF" } };
const hydrozoa_csiromedusidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "csiromedusidae", className: "Hydrozoa", orderName: "Narcomedusae", name: "Csiromedusidae", mainColor: "#F97316", lineageColors: { "csiromedusidae": "#0EA5E9" } };
const hydrozoa_rhopalonematidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "rhopalonematidae", className: "Hydrozoa", orderName: "Trachymedusae", name: "Rhopalonematidae", mainColor: "#6366F1", lineageColors: { "rhopalonematidae": "#22C55E" } };
const hydrozoa_halicreatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "halicreatidae", className: "Hydrozoa", orderName: "Trachymedusae", name: "Halicreatidae", mainColor: "#84CC16", lineageColors: { "halicreatidae": "#EAB308" } };
const hydrozoa_petasidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "petasidae", className: "Hydrozoa", orderName: "Trachymedusae", name: "Petasidae", mainColor: "#06B6D4", lineageColors: { "petasidae": "#A855F7" } };
const hydrozoa_ptychogastriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "ptychogastriidae", className: "Hydrozoa", orderName: "Trachymedusae", name: "Ptychogastriidae", mainColor: "#D946EF", lineageColors: { "ptychogastriidae": "#FB923C" } };
const hydrozoa_olindiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "olindiidae", className: "Hydrozoa", orderName: "Limnomedusae", name: "Olindiidae", mainColor: "#0EA5E9", lineageColors: { "olindiidae": "#2DD4BF" } };
const hydrozoa_geryoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "geryoniidae", className: "Hydrozoa", orderName: "Limnomedusae", name: "Geryoniidae", mainColor: "#22C55E", lineageColors: { "geryoniidae": "#A3E635" } };
const hydrozoa_monobrachiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "monobrachiidae", className: "Hydrozoa", orderName: "Limnomedusae", name: "Monobrachiidae", mainColor: "#EAB308", lineageColors: { "monobrachiidae": "#38BDF8" } };
const hydrozoa_microhydrulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "microhydrulidae", className: "Hydrozoa", orderName: "Limnomedusae", name: "Microhydrulidae", mainColor: "#A855F7", lineageColors: { "microhydrulidae": "#3B82F6" } };
const hydrozoa_armorhydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "armorhydridae", className: "Hydrozoa", orderName: "Limnomedusae", name: "Armorhydridae", mainColor: "#FB923C", lineageColors: { "armorhydridae": "#EF4444" } };
const hydrozoa_halammohydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "halammohydridae", className: "Hydrozoa", orderName: "Actinulida", name: "Halammohydridae", mainColor: "#2DD4BF", lineageColors: { "halammohydridae": "#10B981" } };
const hydrozoa_otohydridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "otohydridae", className: "Hydrozoa", orderName: "Actinulida", name: "Otohydridae", mainColor: "#A3E635", lineageColors: { "otohydridae": "#F59E0B" } };
const hydrozoa_pentasmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "pentasmiliidae", className: "Hydrozoa", orderName: "Unknown", name: "Pentasmiliidae", mainColor: "#38BDF8", lineageColors: { "pentasmiliidae": "#8B5CF6" } };
const hydrozoa_chondroplidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "chondroplidae", className: "Hydrozoa", orderName: "Unknown", name: "Chondroplidae", mainColor: "#3B82F6", lineageColors: { "chondroplidae": "#EC4899" } };
const hydrozoa_inocaulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "inocaulidae", className: "Hydrozoa", orderName: "Unknown", name: "Inocaulidae", mainColor: "#EF4444", lineageColors: { "inocaulidae": "#14B8A6" } };


// ── Anthozoa (549 families) ──
const anthozoa_caryophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "caryophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Caryophylliidae", mainColor: "#EF4444", lineageColors: { "caryophylliidae": "#14B8A6" } };
const anthozoa_merulinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "merulinidae", className: "Anthozoa", orderName: "Scleractinia", name: "Merulinidae", mainColor: "#10B981", lineageColors: { "merulinidae": "#F97316" } };
const anthozoa_acroporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "acroporidae", className: "Anthozoa", orderName: "Scleractinia", name: "Acroporidae", mainColor: "#F59E0B", lineageColors: { "acroporidae": "#6366F1" } };
const anthozoa_thecosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "thecosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Thecosmiliidae", mainColor: "#8B5CF6", lineageColors: { "thecosmiliidae": "#84CC16" } };
const anthozoa_dendrophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "dendrophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Dendrophylliidae", mainColor: "#EC4899", lineageColors: { "dendrophylliidae": "#06B6D4" } };
const anthozoa_poritidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "poritidae", className: "Anthozoa", orderName: "Scleractinia", name: "Poritidae", mainColor: "#14B8A6", lineageColors: { "poritidae": "#D946EF" } };
const anthozoa_latomeandridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "latomeandridae", className: "Anthozoa", orderName: "Scleractinia", name: "Latomeandridae", mainColor: "#F97316", lineageColors: { "latomeandridae": "#0EA5E9" } };
const anthozoa_faviidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "faviidae", className: "Anthozoa", orderName: "Scleractinia", name: "Faviidae", mainColor: "#6366F1", lineageColors: { "faviidae": "#22C55E" } };
const anthozoa_stylinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "stylinidae", className: "Anthozoa", orderName: "Scleractinia", name: "Stylinidae", mainColor: "#84CC16", lineageColors: { "stylinidae": "#EAB308" } };
const anthozoa_flabellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "flabellidae", className: "Anthozoa", orderName: "Scleractinia", name: "Flabellidae", mainColor: "#06B6D4", lineageColors: { "flabellidae": "#A855F7" } };
const anthozoa_comoseridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "comoseridae", className: "Anthozoa", orderName: "Scleractinia", name: "Comoseridae", mainColor: "#D946EF", lineageColors: { "comoseridae": "#FB923C" } };
const anthozoa_turbinoliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "turbinoliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Turbinoliidae", mainColor: "#0EA5E9", lineageColors: { "turbinoliidae": "#2DD4BF" } };
const anthozoa_pocilloporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "pocilloporidae", className: "Anthozoa", orderName: "Scleractinia", name: "Pocilloporidae", mainColor: "#22C55E", lineageColors: { "pocilloporidae": "#A3E635" } };
const anthozoa_oculinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "oculinidae", className: "Anthozoa", orderName: "Scleractinia", name: "Oculinidae", mainColor: "#EAB308", lineageColors: { "oculinidae": "#38BDF8" } };
const anthozoa_agariciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "agariciidae", className: "Anthozoa", orderName: "Scleractinia", name: "Agariciidae", mainColor: "#A855F7", lineageColors: { "agariciidae": "#3B82F6" } };
const anthozoa_meandrinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "meandrinidae", className: "Anthozoa", orderName: "Scleractinia", name: "Meandrinidae", mainColor: "#FB923C", lineageColors: { "meandrinidae": "#EF4444" } };
const anthozoa_astrocoeniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "astrocoeniidae", className: "Anthozoa", orderName: "Scleractinia", name: "Astrocoeniidae", mainColor: "#2DD4BF", lineageColors: { "astrocoeniidae": "#10B981" } };
const anthozoa_thamnasteriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "thamnasteriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Thamnasteriidae", mainColor: "#A3E635", lineageColors: { "thamnasteriidae": "#F59E0B" } };
const anthozoa_rhizangiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "rhizangiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Rhizangiidae", mainColor: "#38BDF8", lineageColors: { "rhizangiidae": "#8B5CF6" } };
const anthozoa_rhipidogyridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "rhipidogyridae", className: "Anthozoa", orderName: "Scleractinia", name: "Rhipidogyridae", mainColor: "#3B82F6", lineageColors: { "rhipidogyridae": "#EC4899" } };
const anthozoa_actinastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "actinastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Actinastreidae", mainColor: "#EF4444", lineageColors: { "actinastreidae": "#14B8A6" } };
const anthozoa_lobophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "lobophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Lobophylliidae", mainColor: "#10B981", lineageColors: { "lobophylliidae": "#F97316" } };
const anthozoa_heterocoeniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "heterocoeniidae", className: "Anthozoa", orderName: "Scleractinia", name: "Heterocoeniidae", mainColor: "#F59E0B", lineageColors: { "heterocoeniidae": "#6366F1" } };
const anthozoa_cunnolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "cunnolitidae", className: "Anthozoa", orderName: "Scleractinia", name: "Cunnolitidae", mainColor: "#8B5CF6", lineageColors: { "cunnolitidae": "#84CC16" } };
const anthozoa_fungiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "fungiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Fungiidae", mainColor: "#EC4899", lineageColors: { "fungiidae": "#06B6D4" } };
const anthozoa_stylophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "stylophyllidae", className: "Anthozoa", orderName: "Scleractinia", name: "Stylophyllidae", mainColor: "#14B8A6", lineageColors: { "stylophyllidae": "#D946EF" } };
const anthozoa_montlivaltiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "montlivaltiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Montlivaltiidae", mainColor: "#F97316", lineageColors: { "montlivaltiidae": "#0EA5E9" } };
const anthozoa_euphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "euphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Euphylliidae", mainColor: "#6366F1", lineageColors: { "euphylliidae": "#22C55E" } };
const anthozoa_haplaraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "haplaraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Haplaraeidae", mainColor: "#84CC16", lineageColors: { "haplaraeidae": "#EAB308" } };
const anthozoa_montastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "montastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Montastraeidae", mainColor: "#06B6D4", lineageColors: { "montastraeidae": "#A855F7" } };
const anthozoa_amphiastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "amphiastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Amphiastreidae", mainColor: "#D946EF", lineageColors: { "amphiastreidae": "#FB923C" } };
const anthozoa_dermosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "dermosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Dermosmiliidae", mainColor: "#0EA5E9", lineageColors: { "dermosmiliidae": "#2DD4BF" } };
const anthozoa_columastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "columastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Columastreidae", mainColor: "#22C55E", lineageColors: { "columastreidae": "#A3E635" } };
const anthozoa_reimaniphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "reimaniphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Reimaniphylliidae", mainColor: "#EAB308", lineageColors: { "reimaniphylliidae": "#38BDF8" } };
const anthozoa_axosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "axosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Axosmiliidae", mainColor: "#A855F7", lineageColors: { "axosmiliidae": "#3B82F6" } };
const anthozoa_cyathophoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "cyathophoridae", className: "Anthozoa", orderName: "Scleractinia", name: "Cyathophoridae", mainColor: "#FB923C", lineageColors: { "cyathophoridae": "#EF4444" } };
const anthozoa_acrosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "acrosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Acrosmiliidae", mainColor: "#2DD4BF", lineageColors: { "acrosmiliidae": "#10B981" } };
const anthozoa_micrabaciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "micrabaciidae", className: "Anthozoa", orderName: "Scleractinia", name: "Micrabaciidae", mainColor: "#A3E635", lineageColors: { "micrabaciidae": "#F59E0B" } };
const anthozoa_placosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "placosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Placosmiliidae", mainColor: "#38BDF8", lineageColors: { "placosmiliidae": "#8B5CF6" } };
const anthozoa_actinacididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "actinacididae", className: "Anthozoa", orderName: "Scleractinia", name: "Actinacididae", mainColor: "#3B82F6", lineageColors: { "actinacididae": "#EC4899" } };
const anthozoa_astrangiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "astrangiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Astrangiidae", mainColor: "#EF4444", lineageColors: { "astrangiidae": "#14B8A6" } };
const anthozoa_deltocyathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "deltocyathidae", className: "Anthozoa", orderName: "Scleractinia", name: "Deltocyathidae", mainColor: "#10B981", lineageColors: { "deltocyathidae": "#F97316" } };
const anthozoa_cladophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "cladophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Cladophylliidae", mainColor: "#F59E0B", lineageColors: { "cladophylliidae": "#6366F1" } };
const anthozoa_synastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "synastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Synastraeidae", mainColor: "#8B5CF6", lineageColors: { "synastraeidae": "#84CC16" } };
const anthozoa_tropiastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "tropiastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Tropiastraeidae", mainColor: "#EC4899", lineageColors: { "tropiastraeidae": "#06B6D4" } };
const anthozoa_calamophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "calamophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Calamophylliidae", mainColor: "#14B8A6", lineageColors: { "calamophylliidae": "#D946EF" } };
const anthozoa_coryphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "coryphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Coryphylliidae", mainColor: "#F97316", lineageColors: { "coryphylliidae": "#0EA5E9" } };
const anthozoa_fungiacyathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "fungiacyathidae", className: "Anthozoa", orderName: "Scleractinia", name: "Fungiacyathidae", mainColor: "#6366F1", lineageColors: { "fungiacyathidae": "#22C55E" } };
const anthozoa_margarophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "margarophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Margarophylliidae", mainColor: "#84CC16", lineageColors: { "margarophylliidae": "#EAB308" } };
const anthozoa_cladocoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "cladocoridae", className: "Anthozoa", orderName: "Scleractinia", name: "Cladocoridae", mainColor: "#06B6D4", lineageColors: { "cladocoridae": "#A855F7" } };
const anthozoa_diploastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "diploastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Diploastraeidae", mainColor: "#D946EF", lineageColors: { "diploastraeidae": "#FB923C" } };
const anthozoa_plesiastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "plesiastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Plesiastreidae", mainColor: "#0EA5E9", lineageColors: { "plesiastreidae": "#2DD4BF" } };
const anthozoa_pamiroseriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "pamiroseriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Pamiroseriidae", mainColor: "#22C55E", lineageColors: { "pamiroseriidae": "#A3E635" } };
const anthozoa_plerogyridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "plerogyridae", className: "Anthozoa", orderName: "Scleractinia", name: "Plerogyridae", mainColor: "#EAB308", lineageColors: { "plerogyridae": "#38BDF8" } };
const anthozoa_epismiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "epismiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Epismiliidae", mainColor: "#A855F7", lineageColors: { "epismiliidae": "#3B82F6" } };
const anthozoa_pachyseridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "pachyseridae", className: "Anthozoa", orderName: "Scleractinia", name: "Pachyseridae", mainColor: "#FB923C", lineageColors: { "pachyseridae": "#EF4444" } };
const anthozoa_psammocoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "psammocoridae", className: "Anthozoa", orderName: "Scleractinia", name: "Psammocoridae", mainColor: "#2DD4BF", lineageColors: { "psammocoridae": "#10B981" } };
const anthozoa_pachyphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "pachyphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Pachyphylliidae", mainColor: "#A3E635", lineageColors: { "pachyphylliidae": "#F59E0B" } };
const anthozoa_procyclolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "procyclolitidae", className: "Anthozoa", orderName: "Scleractinia", name: "Procyclolitidae", mainColor: "#38BDF8", lineageColors: { "procyclolitidae": "#8B5CF6" } };
const anthozoa_felixaraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "felixaraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Felixaraeidae", mainColor: "#3B82F6", lineageColors: { "felixaraeidae": "#EC4899" } };
const anthozoa_amphiastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "amphiastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Amphiastraeidae", mainColor: "#EF4444", lineageColors: { "amphiastraeidae": "#14B8A6" } };
const anthozoa_agathiphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "agathiphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Agathiphylliidae", mainColor: "#10B981", lineageColors: { "agathiphylliidae": "#F97316" } };
const anthozoa_placophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "placophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Placophylliidae", mainColor: "#F59E0B", lineageColors: { "placophylliidae": "#6366F1" } };
const anthozoa_conophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "conophylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Conophylliidae", mainColor: "#8B5CF6", lineageColors: { "conophylliidae": "#84CC16" } };
const anthozoa_eugyridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "eugyridae", className: "Anthozoa", orderName: "Scleractinia", name: "Eugyridae", mainColor: "#EC4899", lineageColors: { "eugyridae": "#06B6D4" } };
const anthozoa_zardinophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "zardinophyllidae", className: "Anthozoa", orderName: "Scleractinia", name: "Zardinophyllidae", mainColor: "#14B8A6", lineageColors: { "zardinophyllidae": "#D946EF" } };
const anthozoa_astraraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "astraraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Astraraeidae", mainColor: "#F97316", lineageColors: { "astraraeidae": "#0EA5E9" } };
const anthozoa_astraeomorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "astraeomorphidae", className: "Anthozoa", orderName: "Scleractinia", name: "Astraeomorphidae", mainColor: "#6366F1", lineageColors: { "astraeomorphidae": "#22C55E" } };
const anthozoa_agatheliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "agatheliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Agatheliidae", mainColor: "#84CC16", lineageColors: { "agatheliidae": "#EAB308" } };
const anthozoa_coscinaraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "coscinaraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Coscinaraeidae", mainColor: "#06B6D4", lineageColors: { "coscinaraeidae": "#A855F7" } };
const anthozoa_asteroseriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "asteroseriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Asteroseriidae", mainColor: "#D946EF", lineageColors: { "asteroseriidae": "#FB923C" } };
const anthozoa_gardineriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "gardineriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Gardineriidae", mainColor: "#0EA5E9", lineageColors: { "gardineriidae": "#2DD4BF" } };
const anthozoa_leptastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "leptastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Leptastreidae", mainColor: "#22C55E", lineageColors: { "leptastreidae": "#A3E635" } };
const anthozoa_oppelismiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "oppelismiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Oppelismiliidae", mainColor: "#EAB308", lineageColors: { "oppelismiliidae": "#38BDF8" } };
const anthozoa_donacosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "donacosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Donacosmiliidae", mainColor: "#A855F7", lineageColors: { "donacosmiliidae": "#3B82F6" } };
const anthozoa_guyniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "guyniidae", className: "Anthozoa", orderName: "Scleractinia", name: "Guyniidae", mainColor: "#FB923C", lineageColors: { "guyniidae": "#EF4444" } };
const anthozoa_anthemiphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "anthemiphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Anthemiphylliidae", mainColor: "#2DD4BF", lineageColors: { "anthemiphylliidae": "#10B981" } };
const anthozoa_protoheterastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "protoheterastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Protoheterastraeidae", mainColor: "#A3E635", lineageColors: { "protoheterastraeidae": "#F59E0B" } };
const anthozoa_trochoidomeandridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "trochoidomeandridae", className: "Anthozoa", orderName: "Scleractinia", name: "Trochoidomeandridae", mainColor: "#38BDF8", lineageColors: { "trochoidomeandridae": "#8B5CF6" } };
const anthozoa_solenocoeniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "solenocoeniidae", className: "Anthozoa", orderName: "Scleractinia", name: "Solenocoeniidae", mainColor: "#3B82F6", lineageColors: { "solenocoeniidae": "#EC4899" } };
const anthozoa_smilotrochiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "smilotrochiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Smilotrochiidae", mainColor: "#EF4444", lineageColors: { "smilotrochiidae": "#14B8A6" } };
const anthozoa_phyllosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "phyllosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Phyllosmiliidae", mainColor: "#10B981", lineageColors: { "phyllosmiliidae": "#F97316" } };
const anthozoa_negoporitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "negoporitidae", className: "Anthozoa", orderName: "Scleractinia", name: "Negoporitidae", mainColor: "#F59E0B", lineageColors: { "negoporitidae": "#6366F1" } };
const anthozoa_intersmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "intersmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Intersmiliidae", mainColor: "#8B5CF6", lineageColors: { "intersmiliidae": "#84CC16" } };
const anthozoa_schizocyathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "schizocyathidae", className: "Anthozoa", orderName: "Scleractinia", name: "Schizocyathidae", mainColor: "#EC4899", lineageColors: { "schizocyathidae": "#06B6D4" } };
const anthozoa_archaeosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "archaeosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Archaeosmiliidae", mainColor: "#14B8A6", lineageColors: { "archaeosmiliidae": "#D946EF" } };
const anthozoa_kobyastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "kobyastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Kobyastraeidae", mainColor: "#F97316", lineageColors: { "kobyastraeidae": "#0EA5E9" } };
const anthozoa_cuifastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "cuifastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Cuifastraeidae", mainColor: "#6366F1", lineageColors: { "cuifastraeidae": "#22C55E" } };
const anthozoa_carolastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "carolastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Carolastraeidae", mainColor: "#84CC16", lineageColors: { "carolastraeidae": "#EAB308" } };
const anthozoa_oulastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "oulastreidae", className: "Anthozoa", orderName: "Scleractinia", name: "Oulastreidae", mainColor: "#06B6D4", lineageColors: { "oulastreidae": "#A855F7" } };
const anthozoa_volzeiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "volzeiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Volzeiidae", mainColor: "#D946EF", lineageColors: { "volzeiidae": "#FB923C" } };
const anthozoa_opisthophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "opisthophyllidae", className: "Anthozoa", orderName: "Scleractinia", name: "Opisthophyllidae", mainColor: "#0EA5E9", lineageColors: { "opisthophyllidae": "#2DD4BF" } };
const anthozoa_sylviellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "sylviellidae", className: "Anthozoa", orderName: "Scleractinia", name: "Sylviellidae", mainColor: "#22C55E", lineageColors: { "sylviellidae": "#A3E635" } };
const anthozoa_stenocyathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "stenocyathidae", className: "Anthozoa", orderName: "Scleractinia", name: "Stenocyathidae", mainColor: "#EAB308", lineageColors: { "stenocyathidae": "#38BDF8" } };
const anthozoa_misistellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "misistellidae", className: "Anthozoa", orderName: "Scleractinia", name: "Misistellidae", mainColor: "#A855F7", lineageColors: { "misistellidae": "#3B82F6" } };
const anthozoa_hemiporitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "hemiporitidae", className: "Anthozoa", orderName: "Scleractinia", name: "Hemiporitidae", mainColor: "#FB923C", lineageColors: { "hemiporitidae": "#EF4444" } };
const anthozoa_cycliphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "cycliphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Cycliphylliidae", mainColor: "#2DD4BF", lineageColors: { "cycliphylliidae": "#10B981" } };
const anthozoa_andemantastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "andemantastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Andemantastraeidae", mainColor: "#A3E635", lineageColors: { "andemantastraeidae": "#F59E0B" } };
const anthozoa_mussidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "mussidae", className: "Anthozoa", orderName: "Scleractinia", name: "Mussidae", mainColor: "#38BDF8", lineageColors: { "mussidae": "#8B5CF6" } };
const anthozoa_parepismiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "parepismiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Parepismiliidae", mainColor: "#3B82F6", lineageColors: { "parepismiliidae": "#EC4899" } };
const anthozoa_guembelastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "guembelastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Guembelastraeidae", mainColor: "#EF4444", lineageColors: { "guembelastraeidae": "#14B8A6" } };
const anthozoa_pseudoturbinolidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "pseudoturbinolidae", className: "Anthozoa", orderName: "Scleractinia", name: "Pseudoturbinolidae", mainColor: "#10B981", lineageColors: { "pseudoturbinolidae": "#F97316" } };
const anthozoa_microsolenidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "microsolenidae", className: "Anthozoa", orderName: "Scleractinia", name: "Microsolenidae", mainColor: "#F59E0B", lineageColors: { "microsolenidae": "#6366F1" } };
const anthozoa_hexapetalidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "hexapetalidae", className: "Anthozoa", orderName: "Scleractinia", name: "Hexapetalidae", mainColor: "#8B5CF6", lineageColors: { "hexapetalidae": "#84CC16" } };
const anthozoa_rayasmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "rayasmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Rayasmiliidae", mainColor: "#EC4899", lineageColors: { "rayasmiliidae": "#06B6D4" } };
const anthozoa_smilostyliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "smilostyliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Smilostyliidae", mainColor: "#14B8A6", lineageColors: { "smilostyliidae": "#D946EF" } };
const anthozoa_parasmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "parasmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Parasmiliidae", mainColor: "#F97316", lineageColors: { "parasmiliidae": "#0EA5E9" } };
const anthozoa_rhipidastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "rhipidastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Rhipidastraeidae", mainColor: "#6366F1", lineageColors: { "rhipidastraeidae": "#22C55E" } };
const anthozoa_eckastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "eckastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Eckastraeidae", mainColor: "#84CC16", lineageColors: { "eckastraeidae": "#EAB308" } };
const anthozoa_gablonzeriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "gablonzeriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Gablonzeriidae", mainColor: "#06B6D4", lineageColors: { "gablonzeriidae": "#A855F7" } };
const anthozoa_polystylidiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "polystylidiidae", className: "Anthozoa", orderName: "Scleractinia", name: "Polystylidiidae", mainColor: "#D946EF", lineageColors: { "polystylidiidae": "#FB923C" } };
const anthozoa_numidiaphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "numidiaphylliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Numidiaphylliidae", mainColor: "#0EA5E9", lineageColors: { "numidiaphylliidae": "#2DD4BF" } };
const anthozoa_gigantostyliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "gigantostyliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Gigantostyliidae", mainColor: "#22C55E", lineageColors: { "gigantostyliidae": "#A3E635" } };
const anthozoa_ellipsosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "ellipsosmiliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Ellipsosmiliidae", mainColor: "#EAB308", lineageColors: { "ellipsosmiliidae": "#38BDF8" } };
const anthozoa_distichoflabellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "distichoflabellidae", className: "Anthozoa", orderName: "Scleractinia", name: "Distichoflabellidae", mainColor: "#A855F7", lineageColors: { "distichoflabellidae": "#3B82F6" } };
const anthozoa_curtoseriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "curtoseriidae", className: "Anthozoa", orderName: "Scleractinia", name: "Curtoseriidae", mainColor: "#FB923C", lineageColors: { "curtoseriidae": "#EF4444" } };
const anthozoa_pachyphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "pachyphyllidae", className: "Anthozoa", orderName: "Scleractinia", name: "Pachyphyllidae", mainColor: "#2DD4BF", lineageColors: { "pachyphyllidae": "#10B981" } };
const anthozoa_andrazelliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "andrazelliidae", className: "Anthozoa", orderName: "Scleractinia", name: "Andrazelliidae", mainColor: "#A3E635", lineageColors: { "andrazelliidae": "#F59E0B" } };
const anthozoa_corbariastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "corbariastraeidae", className: "Anthozoa", orderName: "Scleractinia", name: "Corbariastraeidae", mainColor: "#38BDF8", lineageColors: { "corbariastraeidae": "#8B5CF6" } };
const anthozoa_anabaciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "anabaciidae", className: "Anthozoa", orderName: "Scleractinia", name: "Anabaciidae", mainColor: "#3B82F6", lineageColors: { "anabaciidae": "#EC4899" } };
const anthozoa_archeoanthophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "archeoanthophyllidae", className: "Anthozoa", orderName: "Scleractinia", name: "Archeoanthophyllidae", mainColor: "#EF4444", lineageColors: { "archeoanthophyllidae": "#14B8A6" } };
const anthozoa_nephtheidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "nephtheidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Nephtheidae", mainColor: "#10B981", lineageColors: { "nephtheidae": "#F97316" } };
const anthozoa_paramuriceidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "paramuriceidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Paramuriceidae", mainColor: "#F59E0B", lineageColors: { "paramuriceidae": "#6366F1" } };
const anthozoa_sarcophytidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "sarcophytidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Sarcophytidae", mainColor: "#8B5CF6", lineageColors: { "sarcophytidae": "#84CC16" } };
const anthozoa_gorgoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "gorgoniidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Gorgoniidae", mainColor: "#EC4899", lineageColors: { "gorgoniidae": "#06B6D4" } };
const anthozoa_xeniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "xeniidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Xeniidae", mainColor: "#14B8A6", lineageColors: { "xeniidae": "#D946EF" } };
const anthozoa_alcyoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "alcyoniidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Alcyoniidae", mainColor: "#F97316", lineageColors: { "alcyoniidae": "#0EA5E9" } };
const anthozoa_plexauridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "plexauridae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Plexauridae", mainColor: "#6366F1", lineageColors: { "plexauridae": "#22C55E" } };
const anthozoa_melithaeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "melithaeidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Melithaeidae", mainColor: "#84CC16", lineageColors: { "melithaeidae": "#EAB308" } };
const anthozoa_clavulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "clavulariidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Clavulariidae", mainColor: "#06B6D4", lineageColors: { "clavulariidae": "#A855F7" } };
const anthozoa_cladiellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "cladiellidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Cladiellidae", mainColor: "#D946EF", lineageColors: { "cladiellidae": "#FB923C" } };
const anthozoa_siphonogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "siphonogorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Siphonogorgiidae", mainColor: "#0EA5E9", lineageColors: { "siphonogorgiidae": "#2DD4BF" } };
const anthozoa_lemnaliadae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "lemnaliadae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Lemnaliadae", mainColor: "#22C55E", lineageColors: { "lemnaliadae": "#A3E635" } };
const anthozoa_astrogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "astrogorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Astrogorgiidae", mainColor: "#EAB308", lineageColors: { "astrogorgiidae": "#38BDF8" } };
const anthozoa_euplexauridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "euplexauridae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Euplexauridae", mainColor: "#A855F7", lineageColors: { "euplexauridae": "#3B82F6" } };
const anthozoa_tubiporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "tubiporidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Tubiporidae", mainColor: "#FB923C", lineageColors: { "tubiporidae": "#EF4444" } };
const anthozoa_anthogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "anthogorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Anthogorgiidae", mainColor: "#2DD4BF", lineageColors: { "anthogorgiidae": "#10B981" } };
const anthozoa_capnellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "capnellidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Capnellidae", mainColor: "#A3E635", lineageColors: { "capnellidae": "#F59E0B" } };
const anthozoa_eunicellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "eunicellidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Eunicellidae", mainColor: "#38BDF8", lineageColors: { "eunicellidae": "#8B5CF6" } };
const anthozoa_pterogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "pterogorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Pterogorgiidae", mainColor: "#3B82F6", lineageColors: { "pterogorgiidae": "#EC4899" } };
const anthozoa_isididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "isididae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Isididae", mainColor: "#EF4444", lineageColors: { "isididae": "#14B8A6" } };
const anthozoa_nidaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "nidaliidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Nidaliidae", mainColor: "#10B981", lineageColors: { "nidaliidae": "#F97316" } };
const anthozoa_paralcyoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "paralcyoniidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Paralcyoniidae", mainColor: "#F59E0B", lineageColors: { "paralcyoniidae": "#6366F1" } };
const anthozoa_plexaurellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "plexaurellidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Plexaurellidae", mainColor: "#8B5CF6", lineageColors: { "plexaurellidae": "#84CC16" } };
const anthozoa_subergorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "subergorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Subergorgiidae", mainColor: "#EC4899", lineageColors: { "subergorgiidae": "#06B6D4" } };
const anthozoa_keroeididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "keroeididae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Keroeididae", mainColor: "#14B8A6", lineageColors: { "keroeididae": "#D946EF" } };
const anthozoa_victorgorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "victorgorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Victorgorgiidae", mainColor: "#F97316", lineageColors: { "victorgorgiidae": "#0EA5E9" } };
const anthozoa_sinulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "sinulariidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Sinulariidae", mainColor: "#6366F1", lineageColors: { "sinulariidae": "#22C55E" } };
const anthozoa_acrophytidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "acrophytidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Acrophytidae", mainColor: "#84CC16", lineageColors: { "acrophytidae": "#EAB308" } };
const anthozoa_cerveridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "cerveridae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Cerveridae", mainColor: "#06B6D4", lineageColors: { "cerveridae": "#A855F7" } };
const anthozoa_leptophytidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "leptophytidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Leptophytidae", mainColor: "#D946EF", lineageColors: { "leptophytidae": "#FB923C" } };
const anthozoa_incrustatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "incrustatidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Incrustatidae", mainColor: "#0EA5E9", lineageColors: { "incrustatidae": "#2DD4BF" } };
const anthozoa_acrossotidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "acrossotidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Acrossotidae", mainColor: "#22C55E", lineageColors: { "acrossotidae": "#A3E635" } };
const anthozoa_carijoidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "carijoidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Carijoidae", mainColor: "#EAB308", lineageColors: { "carijoidae": "#38BDF8" } };
const anthozoa_arulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "arulidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Arulidae", mainColor: "#A855F7", lineageColors: { "arulidae": "#3B82F6" } };
const anthozoa_nephthyigorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "nephthyigorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Nephthyigorgiidae", mainColor: "#FB923C", lineageColors: { "nephthyigorgiidae": "#EF4444" } };
const anthozoa_aquaumbridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "aquaumbridae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Aquaumbridae", mainColor: "#2DD4BF", lineageColors: { "aquaumbridae": "#10B981" } };
const anthozoa_scleracidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "scleracidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Scleracidae", mainColor: "#A3E635", lineageColors: { "scleracidae": "#F59E0B" } };
const anthozoa_acanthoaxiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "acanthoaxiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Acanthoaxiidae", mainColor: "#38BDF8", lineageColors: { "acanthoaxiidae": "#8B5CF6" } };
const anthozoa_malacacanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "malacacanthidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Malacacanthidae", mainColor: "#3B82F6", lineageColors: { "malacacanthidae": "#EC4899" } };
const anthozoa_rosgorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "rosgorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Rosgorgiidae", mainColor: "#EF4444", lineageColors: { "rosgorgiidae": "#14B8A6" } };
const anthozoa_taiaroidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "taiaroidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Taiaroidae", mainColor: "#10B981", lineageColors: { "taiaroidae": "#F97316" } };
const anthozoa_discophytidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "discophytidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Discophytidae", mainColor: "#F59E0B", lineageColors: { "discophytidae": "#6366F1" } };
const anthozoa_skamnariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "skamnariidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Skamnariidae", mainColor: "#8B5CF6", lineageColors: { "skamnariidae": "#84CC16" } };
const anthozoa_coelogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "coelogorgiidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Coelogorgiidae", mainColor: "#EC4899", lineageColors: { "coelogorgiidae": "#06B6D4" } };
const anthozoa_corymbophytidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "corymbophytidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Corymbophytidae", mainColor: "#14B8A6", lineageColors: { "corymbophytidae": "#D946EF" } };
const anthozoa_pseudonephtheidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "pseudonephtheidae", className: "Anthozoa", orderName: "Malacalcyonacea", name: "Pseudonephtheidae", mainColor: "#F97316", lineageColors: { "pseudonephtheidae": "#0EA5E9" } };
const anthozoa_waagenophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "waagenophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Waagenophyllidae", mainColor: "#6366F1", lineageColors: { "waagenophyllidae": "#22C55E" } };
const anthozoa_favositidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "favositidae", className: "Anthozoa", orderName: "Unknown", name: "Favositidae", mainColor: "#84CC16", lineageColors: { "favositidae": "#EAB308" } };
const anthozoa_petalaxidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "petalaxidae", className: "Anthozoa", orderName: "Unknown", name: "Petalaxidae", mainColor: "#06B6D4", lineageColors: { "petalaxidae": "#A855F7" } };
const anthozoa_streptelasmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "streptelasmatidae", className: "Anthozoa", orderName: "Unknown", name: "Streptelasmatidae", mainColor: "#D946EF", lineageColors: { "streptelasmatidae": "#FB923C" } };
const anthozoa_durhaminidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "durhaminidae", className: "Anthozoa", orderName: "Unknown", name: "Durhaminidae", mainColor: "#0EA5E9", lineageColors: { "durhaminidae": "#2DD4BF" } };
const anthozoa_cerianthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "cerianthidae", className: "Anthozoa", orderName: "Unknown", name: "Cerianthidae", mainColor: "#22C55E", lineageColors: { "cerianthidae": "#A3E635" } };
const anthozoa_lithostrotionidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "lithostrotionidae", className: "Anthozoa", orderName: "Unknown", name: "Lithostrotionidae", mainColor: "#EAB308", lineageColors: { "lithostrotionidae": "#38BDF8" } };
const anthozoa_micheliniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "micheliniidae", className: "Anthozoa", orderName: "Unknown", name: "Micheliniidae", mainColor: "#A855F7", lineageColors: { "micheliniidae": "#3B82F6" } };
const anthozoa_aulophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "aulophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Aulophyllidae", mainColor: "#FB923C", lineageColors: { "aulophyllidae": "#EF4444" } };
const anthozoa_pachyporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "pachyporidae", className: "Anthozoa", orderName: "Unknown", name: "Pachyporidae", mainColor: "#2DD4BF", lineageColors: { "pachyporidae": "#10B981" } };
const anthozoa_phillipsastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "phillipsastreidae", className: "Anthozoa", orderName: "Unknown", name: "Phillipsastreidae", mainColor: "#A3E635", lineageColors: { "phillipsastreidae": "#F59E0B" } };
const anthozoa_hapsiphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "hapsiphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Hapsiphyllidae", mainColor: "#38BDF8", lineageColors: { "hapsiphyllidae": "#8B5CF6" } };
const anthozoa_plerophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "plerophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Plerophyllidae", mainColor: "#3B82F6", lineageColors: { "plerophyllidae": "#EC4899" } };
const anthozoa_lophophyllidiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "lophophyllidiidae", className: "Anthozoa", orderName: "Unknown", name: "Lophophyllidiidae", mainColor: "#EF4444", lineageColors: { "lophophyllidiidae": "#14B8A6" } };
const anthozoa_cyathopsidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "cyathopsidae", className: "Anthozoa", orderName: "Unknown", name: "Cyathopsidae", mainColor: "#10B981", lineageColors: { "cyathopsidae": "#F97316" } };
const anthozoa_disphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "disphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Disphyllidae", mainColor: "#F59E0B", lineageColors: { "disphyllidae": "#6366F1" } };
const anthozoa_kleopatrinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "kleopatrinidae", className: "Anthozoa", orderName: "Unknown", name: "Kleopatrinidae", mainColor: "#8B5CF6", lineageColors: { "kleopatrinidae": "#84CC16" } };
const anthozoa_arachnactidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "arachnactidae", className: "Anthozoa", orderName: "Unknown", name: "Arachnactidae", mainColor: "#EC4899", lineageColors: { "arachnactidae": "#06B6D4" } };
const anthozoa_auloporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "auloporidae", className: "Anthozoa", orderName: "Unknown", name: "Auloporidae", mainColor: "#14B8A6", lineageColors: { "auloporidae": "#D946EF" } };
const anthozoa_laccophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "laccophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Laccophyllidae", mainColor: "#F97316", lineageColors: { "laccophyllidae": "#0EA5E9" } };
const anthozoa_alveolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "alveolitidae", className: "Anthozoa", orderName: "Unknown", name: "Alveolitidae", mainColor: "#6366F1", lineageColors: { "alveolitidae": "#22C55E" } };
const anthozoa_cyathophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "cyathophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Cyathophyllidae", mainColor: "#84CC16", lineageColors: { "cyathophyllidae": "#EAB308" } };
const anthozoa_polycoeliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "polycoeliidae", className: "Anthozoa", orderName: "Unknown", name: "Polycoeliidae", mainColor: "#06B6D4", lineageColors: { "polycoeliidae": "#A855F7" } };
const anthozoa_botrucnidiferidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "botrucnidiferidae", className: "Anthozoa", orderName: "Unknown", name: "Botrucnidiferidae", mainColor: "#D946EF", lineageColors: { "botrucnidiferidae": "#FB923C" } };
const anthozoa_tetraporellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "tetraporellidae", className: "Anthozoa", orderName: "Unknown", name: "Tetraporellidae", mainColor: "#0EA5E9", lineageColors: { "tetraporellidae": "#2DD4BF" } };
const anthozoa_pentaphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "pentaphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Pentaphyllidae", mainColor: "#22C55E", lineageColors: { "pentaphyllidae": "#A3E635" } };
const anthozoa_ptenophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "ptenophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Ptenophyllidae", mainColor: "#EAB308", lineageColors: { "ptenophyllidae": "#38BDF8" } };
const anthozoa_syringoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "syringoporidae", className: "Anthozoa", orderName: "Unknown", name: "Syringoporidae", mainColor: "#A855F7", lineageColors: { "syringoporidae": "#3B82F6" } };
const anthozoa_cateniporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "cateniporidae", className: "Anthozoa", orderName: "Unknown", name: "Cateniporidae", mainColor: "#FB923C", lineageColors: { "cateniporidae": "#EF4444" } };
const anthozoa_hadrophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "hadrophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Hadrophyllidae", mainColor: "#2DD4BF", lineageColors: { "hadrophyllidae": "#10B981" } };
const anthozoa_antiphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "antiphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Antiphyllidae", mainColor: "#A3E635", lineageColors: { "antiphyllidae": "#F59E0B" } };
const anthozoa_arachnophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "arachnophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Arachnophyllidae", mainColor: "#38BDF8", lineageColors: { "arachnophyllidae": "#8B5CF6" } };
const anthozoa_endophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "endophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Endophyllidae", mainColor: "#3B82F6", lineageColors: { "endophyllidae": "#EC4899" } };
const anthozoa_tryplasmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "tryplasmatidae", className: "Anthozoa", orderName: "Unknown", name: "Tryplasmatidae", mainColor: "#EF4444", lineageColors: { "tryplasmatidae": "#14B8A6" } };
const anthozoa_bothrophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "bothrophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Bothrophyllidae", mainColor: "#10B981", lineageColors: { "bothrophyllidae": "#F97316" } };
const anthozoa_geyerophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "geyerophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Geyerophyllidae", mainColor: "#F59E0B", lineageColors: { "geyerophyllidae": "#6366F1" } };
const anthozoa_kyphophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "kyphophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Kyphophyllidae", mainColor: "#8B5CF6", lineageColors: { "kyphophyllidae": "#84CC16" } };
const anthozoa_lophotichiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "lophotichiidae", className: "Anthozoa", orderName: "Unknown", name: "Lophotichiidae", mainColor: "#EC4899", lineageColors: { "lophotichiidae": "#06B6D4" } };
const anthozoa_syringophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "syringophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Syringophyllidae", mainColor: "#14B8A6", lineageColors: { "syringophyllidae": "#D946EF" } };
const anthozoa_lophophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "lophophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Lophophyllidae", mainColor: "#F97316", lineageColors: { "lophophyllidae": "#0EA5E9" } };
const anthozoa_multithecoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "multithecoporidae", className: "Anthozoa", orderName: "Unknown", name: "Multithecoporidae", mainColor: "#6366F1", lineageColors: { "multithecoporidae": "#22C55E" } };
const anthozoa_metriophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "metriophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Metriophyllidae", mainColor: "#84CC16", lineageColors: { "metriophyllidae": "#EAB308" } };
const anthozoa_axophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "axophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Axophyllidae", mainColor: "#06B6D4", lineageColors: { "axophyllidae": "#A855F7" } };
const anthozoa_spongiomorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "spongiomorphidae", className: "Anthozoa", orderName: "Unknown", name: "Spongiomorphidae", mainColor: "#D946EF", lineageColors: { "spongiomorphidae": "#FB923C" } };
const anthozoa_verbeekiellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "verbeekiellidae", className: "Anthozoa", orderName: "Unknown", name: "Verbeekiellidae", mainColor: "#0EA5E9", lineageColors: { "verbeekiellidae": "#2DD4BF" } };
const anthozoa_sinoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "sinoporidae", className: "Anthozoa", orderName: "Unknown", name: "Sinoporidae", mainColor: "#22C55E", lineageColors: { "sinoporidae": "#A3E635" } };
const anthozoa_cyathaxoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "cyathaxoniidae", className: "Anthozoa", orderName: "Unknown", name: "Cyathaxoniidae", mainColor: "#EAB308", lineageColors: { "cyathaxoniidae": "#38BDF8" } };
const anthozoa_kepingophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "kepingophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Kepingophyllidae", mainColor: "#A855F7", lineageColors: { "kepingophyllidae": "#3B82F6" } };
const anthozoa_heterophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "heterophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Heterophylliidae", mainColor: "#FB923C", lineageColors: { "heterophylliidae": "#EF4444" } };
const anthozoa_halysitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "halysitidae", className: "Anthozoa", orderName: "Unknown", name: "Halysitidae", mainColor: "#2DD4BF", lineageColors: { "halysitidae": "#10B981" } };
const anthozoa_entelophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "entelophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Entelophyllidae", mainColor: "#A3E635", lineageColors: { "entelophyllidae": "#F59E0B" } };
const anthozoa_diffingiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "diffingiidae", className: "Anthozoa", orderName: "Unknown", name: "Diffingiidae", mainColor: "#38BDF8", lineageColors: { "diffingiidae": "#8B5CF6" } };
const anthozoa_agetolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "agetolitidae", className: "Anthozoa", orderName: "Unknown", name: "Agetolitidae", mainColor: "#3B82F6", lineageColors: { "agetolitidae": "#EC4899" } };
const anthozoa_amplexidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "amplexidae", className: "Anthozoa", orderName: "Unknown", name: "Amplexidae", mainColor: "#EF4444", lineageColors: { "amplexidae": "#14B8A6" } };
const anthozoa_zaphrentidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "zaphrentidae", className: "Anthozoa", orderName: "Unknown", name: "Zaphrentidae", mainColor: "#10B981", lineageColors: { "zaphrentidae": "#F97316" } };
const anthozoa_chonophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "chonophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Chonophyllidae", mainColor: "#F59E0B", lineageColors: { "chonophyllidae": "#6366F1" } };
const anthozoa_expressophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "expressophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Expressophyllidae", mainColor: "#8B5CF6", lineageColors: { "expressophyllidae": "#84CC16" } };
const anthozoa_theciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "theciidae", className: "Anthozoa", orderName: "Unknown", name: "Theciidae", mainColor: "#EC4899", lineageColors: { "theciidae": "#06B6D4" } };
const anthozoa_cystiphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "cystiphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Cystiphyllidae", mainColor: "#14B8A6", lineageColors: { "cystiphyllidae": "#D946EF" } };
const anthozoa_timorphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "timorphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Timorphyllidae", mainColor: "#F97316", lineageColors: { "timorphyllidae": "#0EA5E9" } };
const anthozoa_roemeriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "roemeriidae", className: "Anthozoa", orderName: "Unknown", name: "Roemeriidae", mainColor: "#6366F1", lineageColors: { "roemeriidae": "#22C55E" } };
const anthozoa_haimeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "haimeidae", className: "Anthozoa", orderName: "Unknown", name: "Haimeidae", mainColor: "#84CC16", lineageColors: { "haimeidae": "#EAB308" } };
const anthozoa_spongophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "spongophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Spongophyllidae", mainColor: "#06B6D4", lineageColors: { "spongophyllidae": "#A855F7" } };
const anthozoa_goniophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "goniophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Goniophyllidae", mainColor: "#D946EF", lineageColors: { "goniophyllidae": "#FB923C" } };
const anthozoa_pseudopavonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "pseudopavonidae", className: "Anthozoa", orderName: "Unknown", name: "Pseudopavonidae", mainColor: "#0EA5E9", lineageColors: { "pseudopavonidae": "#2DD4BF" } };
const anthozoa_gorskyitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "gorskyitidae", className: "Anthozoa", orderName: "Unknown", name: "Gorskyitidae", mainColor: "#22C55E", lineageColors: { "gorskyitidae": "#A3E635" } };
const anthozoa_stauriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "stauriidae", className: "Anthozoa", orderName: "Unknown", name: "Stauriidae", mainColor: "#EAB308", lineageColors: { "stauriidae": "#38BDF8" } };
const anthozoa_stringophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "stringophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Stringophyllidae", mainColor: "#A855F7", lineageColors: { "stringophyllidae": "#3B82F6" } };
const anthozoa_lykophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "lykophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Lykophyllidae", mainColor: "#FB923C", lineageColors: { "lykophyllidae": "#EF4444" } };
const anthozoa_coenitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "coenitidae", className: "Anthozoa", orderName: "Unknown", name: "Coenitidae", mainColor: "#2DD4BF", lineageColors: { "coenitidae": "#10B981" } };
const anthozoa_palaeocyclidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "palaeocyclidae", className: "Anthozoa", orderName: "Unknown", name: "Palaeocyclidae", mainColor: "#A3E635", lineageColors: { "palaeocyclidae": "#F59E0B" } };
const anthozoa_columnariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "columnariidae", className: "Anthozoa", orderName: "Unknown", name: "Columnariidae", mainColor: "#38BDF8", lineageColors: { "columnariidae": "#8B5CF6" } };
const anthozoa_lonsdaleiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "lonsdaleiidae", className: "Anthozoa", orderName: "Unknown", name: "Lonsdaleiidae", mainColor: "#3B82F6", lineageColors: { "lonsdaleiidae": "#EC4899" } };
const anthozoa_zaphrentoididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "zaphrentoididae", className: "Anthozoa", orderName: "Unknown", name: "Zaphrentoididae", mainColor: "#EF4444", lineageColors: { "zaphrentoididae": "#14B8A6" } };
const anthozoa_mucophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "mucophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Mucophyllidae", mainColor: "#10B981", lineageColors: { "mucophyllidae": "#F97316" } };
const anthozoa_kodonophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "kodonophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Kodonophyllidae", mainColor: "#F59E0B", lineageColors: { "kodonophyllidae": "#6366F1" } };
const anthozoa_protozaphrentidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "protozaphrentidae", className: "Anthozoa", orderName: "Unknown", name: "Protozaphrentidae", mainColor: "#8B5CF6", lineageColors: { "protozaphrentidae": "#84CC16" } };
const anthozoa_palaeacidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "palaeacidae", className: "Anthozoa", orderName: "Unknown", name: "Palaeacidae", mainColor: "#EC4899", lineageColors: { "palaeacidae": "#06B6D4" } };
const anthozoa_cleistoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "cleistoporidae", className: "Anthozoa", orderName: "Unknown", name: "Cleistoporidae", mainColor: "#14B8A6", lineageColors: { "cleistoporidae": "#D946EF" } };
const anthozoa_tetradiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "tetradiidae", className: "Anthozoa", orderName: "Unknown", name: "Tetradiidae", mainColor: "#F97316", lineageColors: { "tetradiidae": "#0EA5E9" } };
const anthozoa_endamplexidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "endamplexidae", className: "Anthozoa", orderName: "Unknown", name: "Endamplexidae", mainColor: "#6366F1", lineageColors: { "endamplexidae": "#22C55E" } };
const anthozoa_paliphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "paliphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Paliphyllidae", mainColor: "#84CC16", lineageColors: { "paliphyllidae": "#EAB308" } };
const anthozoa_calostylidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "calostylidae", className: "Anthozoa", orderName: "Unknown", name: "Calostylidae", mainColor: "#06B6D4", lineageColors: { "calostylidae": "#A855F7" } };
const anthozoa_ekvasophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "ekvasophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Ekvasophyllidae", mainColor: "#D946EF", lineageColors: { "ekvasophyllidae": "#FB923C" } };
const anthozoa_tabulaconidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "tabulaconidae", className: "Anthozoa", orderName: "Unknown", name: "Tabulaconidae", mainColor: "#0EA5E9", lineageColors: { "tabulaconidae": "#2DD4BF" } };
const anthozoa_trachypsammidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "trachypsammidae", className: "Anthozoa", orderName: "Unknown", name: "Trachypsammidae", mainColor: "#22C55E", lineageColors: { "trachypsammidae": "#A3E635" } };
const anthozoa_lichenariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "lichenariidae", className: "Anthozoa", orderName: "Unknown", name: "Lichenariidae", mainColor: "#EAB308", lineageColors: { "lichenariidae": "#38BDF8" } };
const anthozoa_lambelasmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "lambelasmatidae", className: "Anthozoa", orderName: "Unknown", name: "Lambelasmatidae", mainColor: "#A855F7", lineageColors: { "lambelasmatidae": "#3B82F6" } };
const anthozoa_paiutitubulitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "paiutitubulitidae", className: "Anthozoa", orderName: "Unknown", name: "Paiutitubulitidae", mainColor: "#FB923C", lineageColors: { "paiutitubulitidae": "#EF4444" } };
const anthozoa_ketophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "ketophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Ketophyllidae", mainColor: "#2DD4BF", lineageColors: { "ketophyllidae": "#10B981" } };
const anthozoa_pycnostylidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "pycnostylidae", className: "Anthozoa", orderName: "Unknown", name: "Pycnostylidae", mainColor: "#A3E635", lineageColors: { "pycnostylidae": "#F59E0B" } };
const anthozoa_ptychophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "ptychophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Ptychophyllidae", mainColor: "#38BDF8", lineageColors: { "ptychophyllidae": "#8B5CF6" } };
const anthozoa_paleocyclidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "paleocyclidae", className: "Anthozoa", orderName: "Unknown", name: "Paleocyclidae", mainColor: "#3B82F6", lineageColors: { "paleocyclidae": "#EC4899" } };
const anthozoa_huadianophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "huadianophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Huadianophyllidae", mainColor: "#EF4444", lineageColors: { "huadianophyllidae": "#14B8A6" } };
const anthozoa_mirandellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "mirandellidae", className: "Anthozoa", orderName: "Unknown", name: "Mirandellidae", mainColor: "#10B981", lineageColors: { "mirandellidae": "#F97316" } };
const anthozoa_petraphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "petraphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Petraphyllidae", mainColor: "#F59E0B", lineageColors: { "petraphyllidae": "#6366F1" } };
const anthozoa_koninckocariniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "koninckocariniidae", className: "Anthozoa", orderName: "Unknown", name: "Koninckocariniidae", mainColor: "#8B5CF6", lineageColors: { "koninckocariniidae": "#84CC16" } };
const anthozoa_palaeosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "palaeosmiliidae", className: "Anthozoa", orderName: "Unknown", name: "Palaeosmiliidae", mainColor: "#EC4899", lineageColors: { "palaeosmiliidae": "#06B6D4" } };
const anthozoa_auloheliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "auloheliidae", className: "Anthozoa", orderName: "Unknown", name: "Auloheliidae", mainColor: "#14B8A6", lineageColors: { "auloheliidae": "#D946EF" } };
const anthozoa_kilbuchophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "kilbuchophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Kilbuchophyllidae", mainColor: "#F97316", lineageColors: { "kilbuchophyllidae": "#0EA5E9" } };
const anthozoa_kielcephyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "kielcephyllidae", className: "Anthozoa", orderName: "Unknown", name: "Kielcephyllidae", mainColor: "#6366F1", lineageColors: { "kielcephyllidae": "#22C55E" } };
const anthozoa_lindstroemiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "lindstroemiidae", className: "Anthozoa", orderName: "Unknown", name: "Lindstroemiidae", mainColor: "#84CC16", lineageColors: { "lindstroemiidae": "#EAB308" } };
const anthozoa_schizophoritidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "schizophoritidae", className: "Anthozoa", orderName: "Unknown", name: "Schizophoritidae", mainColor: "#06B6D4", lineageColors: { "schizophoritidae": "#A855F7" } };
const anthozoa_petraiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "petraiidae", className: "Anthozoa", orderName: "Unknown", name: "Petraiidae", mainColor: "#D946EF", lineageColors: { "petraiidae": "#FB923C" } };
const anthozoa_syringolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "syringolitidae", className: "Anthozoa", orderName: "Unknown", name: "Syringolitidae", mainColor: "#0EA5E9", lineageColors: { "syringolitidae": "#2DD4BF" } };
const anthozoa_romingeriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "romingeriidae", className: "Anthozoa", orderName: "Unknown", name: "Romingeriidae", mainColor: "#22C55E", lineageColors: { "romingeriidae": "#A3E635" } };
const anthozoa_uraliniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "uraliniidae", className: "Anthozoa", orderName: "Unknown", name: "Uraliniidae", mainColor: "#EAB308", lineageColors: { "uraliniidae": "#38BDF8" } };
const anthozoa_dorlodotidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "dorlodotidae", className: "Anthozoa", orderName: "Unknown", name: "Dorlodotidae", mainColor: "#A855F7", lineageColors: { "dorlodotidae": "#3B82F6" } };
const anthozoa_pseudogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "pseudogorgiidae", className: "Anthozoa", orderName: "Unknown", name: "Pseudogorgiidae", mainColor: "#FB923C", lineageColors: { "pseudogorgiidae": "#EF4444" } };
const anthozoa_calceolidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "calceolidae", className: "Anthozoa", orderName: "Unknown", name: "Calceolidae", mainColor: "#2DD4BF", lineageColors: { "calceolidae": "#10B981" } };
const anthozoa_fasciphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "fasciphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Fasciphyllidae", mainColor: "#A3E635", lineageColors: { "fasciphyllidae": "#F59E0B" } };
const anthozoa_stereolasmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "stereolasmatidae", className: "Anthozoa", orderName: "Unknown", name: "Stereolasmatidae", mainColor: "#38BDF8", lineageColors: { "stereolasmatidae": "#8B5CF6" } };
const anthozoa_parastriatoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "parastriatoporidae", className: "Anthozoa", orderName: "Unknown", name: "Parastriatoporidae", mainColor: "#3B82F6", lineageColors: { "parastriatoporidae": "#EC4899" } };
const anthozoa_fletcheriellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "fletcheriellidae", className: "Anthozoa", orderName: "Unknown", name: "Fletcheriellidae", mainColor: "#EF4444", lineageColors: { "fletcheriellidae": "#14B8A6" } };
const anthozoa_holmophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "holmophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Holmophyllidae", mainColor: "#10B981", lineageColors: { "holmophyllidae": "#F97316" } };
const anthozoa_lyoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "lyoporidae", className: "Anthozoa", orderName: "Unknown", name: "Lyoporidae", mainColor: "#F59E0B", lineageColors: { "lyoporidae": "#6366F1" } };
const anthozoa_neoroemeriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "neoroemeriidae", className: "Anthozoa", orderName: "Unknown", name: "Neoroemeriidae", mainColor: "#8B5CF6", lineageColors: { "neoroemeriidae": "#84CC16" } };
const anthozoa_trachypsammiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "trachypsammiidae", className: "Anthozoa", orderName: "Unknown", name: "Trachypsammiidae", mainColor: "#EC4899", lineageColors: { "trachypsammiidae": "#06B6D4" } };
const anthozoa_pseudofavositidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "pseudofavositidae", className: "Anthozoa", orderName: "Unknown", name: "Pseudofavositidae", mainColor: "#14B8A6", lineageColors: { "pseudofavositidae": "#D946EF" } };
const anthozoa_lamottiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "lamottiidae", className: "Anthozoa", orderName: "Unknown", name: "Lamottiidae", mainColor: "#F97316", lineageColors: { "lamottiidae": "#0EA5E9" } };
const anthozoa_plerodiffiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "plerodiffiidae", className: "Anthozoa", orderName: "Unknown", name: "Plerodiffiidae", mainColor: "#6366F1", lineageColors: { "plerodiffiidae": "#22C55E" } };
const anthozoa_craspedophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "craspedophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Craspedophyllidae", mainColor: "#84CC16", lineageColors: { "craspedophyllidae": "#EAB308" } };
const anthozoa_halliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "halliidae", className: "Anthozoa", orderName: "Unknown", name: "Halliidae", mainColor: "#06B6D4", lineageColors: { "halliidae": "#A855F7" } };
const anthozoa_trachyporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "trachyporidae", className: "Anthozoa", orderName: "Unknown", name: "Trachyporidae", mainColor: "#D946EF", lineageColors: { "trachyporidae": "#FB923C" } };
const anthozoa_digonophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "digonophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Digonophyllidae", mainColor: "#0EA5E9", lineageColors: { "digonophyllidae": "#2DD4BF" } };
const anthozoa_proheliolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "proheliolitidae", className: "Anthozoa", orderName: "Unknown", name: "Proheliolitidae", mainColor: "#22C55E", lineageColors: { "proheliolitidae": "#A3E635" } };
const anthozoa_ricordiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "ricordiidae", className: "Anthozoa", orderName: "Unknown", name: "Ricordiidae", mainColor: "#EAB308", lineageColors: { "ricordiidae": "#38BDF8" } };
const anthozoa_aurelianidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "aurelianidae", className: "Anthozoa", orderName: "Unknown", name: "Aurelianidae", mainColor: "#A855F7", lineageColors: { "aurelianidae": "#3B82F6" } };
const anthozoa_exocoelactiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "exocoelactiidae", className: "Anthozoa", orderName: "Unknown", name: "Exocoelactiidae", mainColor: "#FB923C", lineageColors: { "exocoelactiidae": "#EF4444" } };
const anthozoa_pennautlidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "pennautlidae", className: "Anthozoa", orderName: "Unknown", name: "Pennautlidae", mainColor: "#2DD4BF", lineageColors: { "pennautlidae": "#10B981" } };
const anthozoa_cyclastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "cyclastraeidae", className: "Anthozoa", orderName: "Unknown", name: "Cyclastraeidae", mainColor: "#A3E635", lineageColors: { "cyclastraeidae": "#F59E0B" } };
const anthozoa_palaeofavosiporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "palaeofavosiporidae", className: "Anthozoa", orderName: "Unknown", name: "Palaeofavosiporidae", mainColor: "#38BDF8", lineageColors: { "palaeofavosiporidae": "#8B5CF6" } };
const anthozoa_kozlowskiocystiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "kozlowskiocystiidae", className: "Anthozoa", orderName: "Unknown", name: "Kozlowskiocystiidae", mainColor: "#3B82F6", lineageColors: { "kozlowskiocystiidae": "#EC4899" } };
const anthozoa_actinodiscidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "actinodiscidae", className: "Anthozoa", orderName: "Unknown", name: "Actinodiscidae", mainColor: "#EF4444", lineageColors: { "actinodiscidae": "#14B8A6" } };
const anthozoa_anisophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "anisophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Anisophyllidae", mainColor: "#10B981", lineageColors: { "anisophyllidae": "#F97316" } };
const anthozoa_acervulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "acervulariidae", className: "Anthozoa", orderName: "Unknown", name: "Acervulariidae", mainColor: "#F59E0B", lineageColors: { "acervulariidae": "#6366F1" } };
const anthozoa_vaughaniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "vaughaniidae", className: "Anthozoa", orderName: "Unknown", name: "Vaughaniidae", mainColor: "#8B5CF6", lineageColors: { "vaughaniidae": "#84CC16" } };
const anthozoa_taeniolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "taeniolitidae", className: "Anthozoa", orderName: "Unknown", name: "Taeniolitidae", mainColor: "#EC4899", lineageColors: { "taeniolitidae": "#06B6D4" } };
const anthozoa_eridophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "eridophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Eridophyllidae", mainColor: "#14B8A6", lineageColors: { "eridophyllidae": "#D946EF" } };
const anthozoa_pachythecalidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "pachythecalidae", className: "Anthozoa", orderName: "Unknown", name: "Pachythecalidae", mainColor: "#F97316", lineageColors: { "pachythecalidae": "#0EA5E9" } };
const anthozoa_acrophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "acrophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Acrophyllidae", mainColor: "#6366F1", lineageColors: { "acrophyllidae": "#22C55E" } };
const anthozoa_gerardiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "gerardiidae", className: "Anthozoa", orderName: "Unknown", name: "Gerardiidae", mainColor: "#84CC16", lineageColors: { "gerardiidae": "#EAB308" } };
const anthozoa_ptychodactidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "ptychodactidae", className: "Anthozoa", orderName: "Unknown", name: "Ptychodactidae", mainColor: "#06B6D4", lineageColors: { "ptychodactidae": "#A855F7" } };
const anthozoa_paractidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "paractidae", className: "Anthozoa", orderName: "Unknown", name: "Paractidae", mainColor: "#D946EF", lineageColors: { "paractidae": "#FB923C" } };
const anthozoa_ilyanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "ilyanthidae", className: "Anthozoa", orderName: "Unknown", name: "Ilyanthidae", mainColor: "#0EA5E9", lineageColors: { "ilyanthidae": "#2DD4BF" } };
const anthozoa_trochosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "trochosmiliidae", className: "Anthozoa", orderName: "Unknown", name: "Trochosmiliidae", mainColor: "#22C55E", lineageColors: { "trochosmiliidae": "#A3E635" } };
const anthozoa_pteroeididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "pteroeididae", className: "Anthozoa", orderName: "Unknown", name: "Pteroeididae", mainColor: "#EAB308", lineageColors: { "pteroeididae": "#38BDF8" } };
const anthozoa_telestidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "telestidae", className: "Anthozoa", orderName: "Unknown", name: "Telestidae", mainColor: "#A855F7", lineageColors: { "telestidae": "#3B82F6" } };
const anthozoa_pseudocladochomidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "pseudocladochomidae", className: "Anthozoa", orderName: "Unknown", name: "Pseudocladochomidae", mainColor: "#FB923C", lineageColors: { "pseudocladochomidae": "#EF4444" } };
const anthozoa_astrospiculariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "astrospiculariidae", className: "Anthozoa", orderName: "Unknown", name: "Astrospiculariidae", mainColor: "#2DD4BF", lineageColors: { "astrospiculariidae": "#10B981" } };
const anthozoa_briaridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "briaridae", className: "Anthozoa", orderName: "Unknown", name: "Briaridae", mainColor: "#A3E635", lineageColors: { "briaridae": "#F59E0B" } };
const anthozoa_ainigmaptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "ainigmaptilidae", className: "Anthozoa", orderName: "Unknown", name: "Ainigmaptilidae", mainColor: "#38BDF8", lineageColors: { "ainigmaptilidae": "#8B5CF6" } };
const anthozoa_plasmoporellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "plasmoporellidae", className: "Anthozoa", orderName: "Unknown", name: "Plasmoporellidae", mainColor: "#3B82F6", lineageColors: { "plasmoporellidae": "#EC4899" } };
const anthozoa_bethanyphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "bethanyphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Bethanyphyllidae", mainColor: "#EF4444", lineageColors: { "bethanyphyllidae": "#14B8A6" } };
const anthozoa_pycnolithidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "pycnolithidae", className: "Anthozoa", orderName: "Unknown", name: "Pycnolithidae", mainColor: "#10B981", lineageColors: { "pycnolithidae": "#F97316" } };
const anthozoa_campophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "campophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Campophyllidae", mainColor: "#F59E0B", lineageColors: { "campophyllidae": "#6366F1" } };
const anthozoa_distichophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "distichophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Distichophyllidae", mainColor: "#8B5CF6", lineageColors: { "distichophyllidae": "#84CC16" } };
const anthozoa_numidiaphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "numidiaphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Numidiaphyllidae", mainColor: "#EC4899", lineageColors: { "numidiaphyllidae": "#06B6D4" } };
const anthozoa_amsdenoididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "amsdenoididae", className: "Anthozoa", orderName: "Unknown", name: "Amsdenoididae", mainColor: "#14B8A6", lineageColors: { "amsdenoididae": "#D946EF" } };
const anthozoa_combophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "combophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Combophyllidae", mainColor: "#F97316", lineageColors: { "combophyllidae": "#0EA5E9" } };
const anthozoa_tropiastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "tropiastreidae", className: "Anthozoa", orderName: "Unknown", name: "Tropiastreidae", mainColor: "#6366F1", lineageColors: { "tropiastreidae": "#22C55E" } };
const anthozoa_funginellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "funginellidae", className: "Anthozoa", orderName: "Unknown", name: "Funginellidae", mainColor: "#84CC16", lineageColors: { "funginellidae": "#EAB308" } };
const anthozoa_heliastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "heliastraeidae", className: "Anthozoa", orderName: "Unknown", name: "Heliastraeidae", mainColor: "#06B6D4", lineageColors: { "heliastraeidae": "#A855F7" } };
const anthozoa_gardinariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "gardinariidae", className: "Anthozoa", orderName: "Unknown", name: "Gardinariidae", mainColor: "#D946EF", lineageColors: { "gardinariidae": "#FB923C" } };
const anthozoa_eusmilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "eusmilidae", className: "Anthozoa", orderName: "Unknown", name: "Eusmilidae", mainColor: "#0EA5E9", lineageColors: { "eusmilidae": "#2DD4BF" } };
const anthozoa_siderasteridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "siderasteridae", className: "Anthozoa", orderName: "Unknown", name: "Siderasteridae", mainColor: "#22C55E", lineageColors: { "siderasteridae": "#A3E635" } };
const anthozoa_alpinophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "alpinophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Alpinophylliidae", mainColor: "#EAB308", lineageColors: { "alpinophylliidae": "#38BDF8" } };
const anthozoa_cyclophyllopsiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "cyclophyllopsiidae", className: "Anthozoa", orderName: "Unknown", name: "Cyclophyllopsiidae", mainColor: "#A855F7", lineageColors: { "cyclophyllopsiidae": "#3B82F6" } };
const anthozoa_carolastaeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "carolastaeidae", className: "Anthozoa", orderName: "Unknown", name: "Carolastaeidae", mainColor: "#FB923C", lineageColors: { "carolastaeidae": "#EF4444" } };
const anthozoa_caryophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "caryophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Caryophyllidae", mainColor: "#2DD4BF", lineageColors: { "caryophyllidae": "#10B981" } };
const anthozoa_lithophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "lithophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Lithophylliidae", mainColor: "#A3E635", lineageColors: { "lithophylliidae": "#F59E0B" } };
const anthozoa_waiparaconidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "waiparaconidae", className: "Anthozoa", orderName: "Unknown", name: "Waiparaconidae", mainColor: "#38BDF8", lineageColors: { "waiparaconidae": "#8B5CF6" } };
const anthozoa_pseudocladochonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "pseudocladochonidae", className: "Anthozoa", orderName: "Unknown", name: "Pseudocladochonidae", mainColor: "#3B82F6", lineageColors: { "pseudocladochonidae": "#EC4899" } };
const anthozoa_arachnanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "arachnanthidae", className: "Anthozoa", orderName: "Unknown", name: "Arachnanthidae", mainColor: "#EF4444", lineageColors: { "arachnanthidae": "#14B8A6" } };
const anthozoa_mycophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "mycophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Mycophyllidae", mainColor: "#10B981", lineageColors: { "mycophyllidae": "#F97316" } };
const anthozoa_sterictophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "sterictophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Sterictophyllidae", mainColor: "#F59E0B", lineageColors: { "sterictophyllidae": "#6366F1" } };
const anthozoa_muriceidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "muriceidae", className: "Anthozoa", orderName: "Unknown", name: "Muriceidae", mainColor: "#8B5CF6", lineageColors: { "muriceidae": "#84CC16" } };
const anthozoa_pteroididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "pteroididae", className: "Anthozoa", orderName: "Unknown", name: "Pteroididae", mainColor: "#EC4899", lineageColors: { "pteroididae": "#06B6D4" } };
const anthozoa_pyrgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "pyrgiidae", className: "Anthozoa", orderName: "Unknown", name: "Pyrgiidae", mainColor: "#14B8A6", lineageColors: { "pyrgiidae": "#D946EF" } };
const anthozoa_periphaceloporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "periphaceloporidae", className: "Anthozoa", orderName: "Unknown", name: "Periphaceloporidae", mainColor: "#F97316", lineageColors: { "periphaceloporidae": "#0EA5E9" } };
const anthozoa_maasellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "maasellidae", className: "Anthozoa", orderName: "Unknown", name: "Maasellidae", mainColor: "#6366F1", lineageColors: { "maasellidae": "#22C55E" } };
const anthozoa_coccoserididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "coccoserididae", className: "Anthozoa", orderName: "Unknown", name: "Coccoserididae", mainColor: "#84CC16", lineageColors: { "coccoserididae": "#EAB308" } };
const anthozoa_thecostegitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "thecostegitidae", className: "Anthozoa", orderName: "Unknown", name: "Thecostegitidae", mainColor: "#06B6D4", lineageColors: { "thecostegitidae": "#A855F7" } };
const anthozoa_porastriatoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "porastriatoporidae", className: "Anthozoa", orderName: "Unknown", name: "Porastriatoporidae", mainColor: "#D946EF", lineageColors: { "porastriatoporidae": "#FB923C" } };
const anthozoa_pyrigiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "pyrigiidae", className: "Anthozoa", orderName: "Unknown", name: "Pyrigiidae", mainColor: "#0EA5E9", lineageColors: { "pyrigiidae": "#2DD4BF" } };
const anthozoa_billingsariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "billingsariidae", className: "Anthozoa", orderName: "Unknown", name: "Billingsariidae", mainColor: "#22C55E", lineageColors: { "billingsariidae": "#A3E635" } };
const anthozoa_centristelidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "centristelidae", className: "Anthozoa", orderName: "Unknown", name: "Centristelidae", mainColor: "#EAB308", lineageColors: { "centristelidae": "#38BDF8" } };
const anthozoa_paleoalveolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "paleoalveolitidae", className: "Anthozoa", orderName: "Unknown", name: "Paleoalveolitidae", mainColor: "#A855F7", lineageColors: { "paleoalveolitidae": "#3B82F6" } };
const anthozoa_cyrtophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "cyrtophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Cyrtophyllidae", mainColor: "#FB923C", lineageColors: { "cyrtophyllidae": "#EF4444" } };
const anthozoa_endotheciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "endotheciidae", className: "Anthozoa", orderName: "Unknown", name: "Endotheciidae", mainColor: "#2DD4BF", lineageColors: { "endotheciidae": "#10B981" } };
const anthozoa_cothoniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "cothoniidae", className: "Anthozoa", orderName: "Unknown", name: "Cothoniidae", mainColor: "#A3E635", lineageColors: { "cothoniidae": "#F59E0B" } };
const anthozoa_kiziliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "kiziliidae", className: "Anthozoa", orderName: "Unknown", name: "Kiziliidae", mainColor: "#38BDF8", lineageColors: { "kiziliidae": "#8B5CF6" } };
const anthozoa_adamanophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "adamanophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Adamanophyllidae", mainColor: "#3B82F6", lineageColors: { "adamanophyllidae": "#EC4899" } };
const anthozoa_multisoleniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "multisoleniidae", className: "Anthozoa", orderName: "Unknown", name: "Multisoleniidae", mainColor: "#EF4444", lineageColors: { "multisoleniidae": "#14B8A6" } };
const anthozoa_chonostegitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "chonostegitidae", className: "Anthozoa", orderName: "Unknown", name: "Chonostegitidae", mainColor: "#10B981", lineageColors: { "chonostegitidae": "#F97316" } };
const anthozoa_lipoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "lipoporidae", className: "Anthozoa", orderName: "Unknown", name: "Lipoporidae", mainColor: "#F59E0B", lineageColors: { "lipoporidae": "#6366F1" } };
const anthozoa_septodaeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "septodaeidae", className: "Anthozoa", orderName: "Unknown", name: "Septodaeidae", mainColor: "#8B5CF6", lineageColors: { "septodaeidae": "#84CC16" } };
const anthozoa_neocolumnariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "neocolumnariidae", className: "Anthozoa", orderName: "Unknown", name: "Neocolumnariidae", mainColor: "#EC4899", lineageColors: { "neocolumnariidae": "#06B6D4" } };
const anthozoa_bajgoliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "bajgoliidae", className: "Anthozoa", orderName: "Unknown", name: "Bajgoliidae", mainColor: "#14B8A6", lineageColors: { "bajgoliidae": "#D946EF" } };
const anthozoa_fletcheriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "fletcheriidae", className: "Anthozoa", orderName: "Unknown", name: "Fletcheriidae", mainColor: "#F97316", lineageColors: { "fletcheriidae": "#0EA5E9" } };
const anthozoa_ditoecholasmatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "ditoecholasmatidae", className: "Anthozoa", orderName: "Unknown", name: "Ditoecholasmatidae", mainColor: "#6366F1", lineageColors: { "ditoecholasmatidae": "#22C55E" } };
const anthozoa_aphrophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "aphrophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Aphrophyllidae", mainColor: "#84CC16", lineageColors: { "aphrophyllidae": "#EAB308" } };
const anthozoa_eupsammidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "eupsammidae", className: "Anthozoa", orderName: "Unknown", name: "Eupsammidae", mainColor: "#06B6D4", lineageColors: { "eupsammidae": "#A855F7" } };
const anthozoa_pinacophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "pinacophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Pinacophyllidae", mainColor: "#D946EF", lineageColors: { "pinacophyllidae": "#FB923C" } };
const anthozoa_haplareidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "haplareidae", className: "Anthozoa", orderName: "Unknown", name: "Haplareidae", mainColor: "#0EA5E9", lineageColors: { "haplareidae": "#2DD4BF" } };
const anthozoa_isastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "isastraeidae", className: "Anthozoa", orderName: "Unknown", name: "Isastraeidae", mainColor: "#22C55E", lineageColors: { "isastraeidae": "#A3E635" } };
const anthozoa_margarophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "margarophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Margarophyllidae", mainColor: "#EAB308", lineageColors: { "margarophyllidae": "#38BDF8" } };
const anthozoa_protoheterstraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "protoheterstraeidae", className: "Anthozoa", orderName: "Unknown", name: "Protoheterstraeidae", mainColor: "#A855F7", lineageColors: { "protoheterstraeidae": "#3B82F6" } };
const anthozoa_phyllocoeniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "phyllocoeniidae", className: "Anthozoa", orderName: "Unknown", name: "Phyllocoeniidae", mainColor: "#FB923C", lineageColors: { "phyllocoeniidae": "#EF4444" } };
const anthozoa_euhellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "euhellidae", className: "Anthozoa", orderName: "Unknown", name: "Euhellidae", mainColor: "#2DD4BF", lineageColors: { "euhellidae": "#10B981" } };
const anthozoa_mitrodendronidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "mitrodendronidae", className: "Anthozoa", orderName: "Unknown", name: "Mitrodendronidae", mainColor: "#A3E635", lineageColors: { "mitrodendronidae": "#F59E0B" } };
const anthozoa_antheidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "antheidae", className: "Anthozoa", orderName: "Unknown", name: "Antheidae", mainColor: "#38BDF8", lineageColors: { "antheidae": "#8B5CF6" } };
const anthozoa_diploastreidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "diploastreidae", className: "Anthozoa", orderName: "Unknown", name: "Diploastreidae", mainColor: "#3B82F6", lineageColors: { "diploastreidae": "#EC4899" } };
const anthozoa_semperinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "semperinidae", className: "Anthozoa", orderName: "Unknown", name: "Semperinidae", mainColor: "#EF4444", lineageColors: { "semperinidae": "#14B8A6" } };
const anthozoa_kophobelemnonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "kophobelemnonidae", className: "Anthozoa", orderName: "Unknown", name: "Kophobelemnonidae", mainColor: "#10B981", lineageColors: { "kophobelemnonidae": "#F97316" } };
const anthozoa_evenkiellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "evenkiellidae", className: "Anthozoa", orderName: "Unknown", name: "Evenkiellidae", mainColor: "#F59E0B", lineageColors: { "evenkiellidae": "#6366F1" } };
const anthozoa_microbaciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "microbaciidae", className: "Anthozoa", orderName: "Unknown", name: "Microbaciidae", mainColor: "#8B5CF6", lineageColors: { "microbaciidae": "#84CC16" } };
const anthozoa_cyathactidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "cyathactidae", className: "Anthozoa", orderName: "Unknown", name: "Cyathactidae", mainColor: "#EC4899", lineageColors: { "cyathactidae": "#06B6D4" } };
const anthozoa_tropiphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "tropiphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Tropiphyllidae", mainColor: "#14B8A6", lineageColors: { "tropiphyllidae": "#D946EF" } };
const anthozoa_tryplasmidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "tryplasmidae", className: "Anthozoa", orderName: "Unknown", name: "Tryplasmidae", mainColor: "#F97316", lineageColors: { "tryplasmidae": "#0EA5E9" } };
const anthozoa_thamnoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "thamnoporidae", className: "Anthozoa", orderName: "Unknown", name: "Thamnoporidae", mainColor: "#6366F1", lineageColors: { "thamnoporidae": "#22C55E" } };
const anthozoa_kophobelemnoidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "kophobelemnoidae", className: "Anthozoa", orderName: "Unknown", name: "Kophobelemnoidae", mainColor: "#84CC16", lineageColors: { "kophobelemnoidae": "#EAB308" } };
const anthozoa_chrysogorgidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "chrysogorgidae", className: "Anthozoa", orderName: "Unknown", name: "Chrysogorgidae", mainColor: "#06B6D4", lineageColors: { "chrysogorgidae": "#A855F7" } };
const anthozoa_dendrogyriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "dendrogyriidae", className: "Anthozoa", orderName: "Unknown", name: "Dendrogyriidae", mainColor: "#D946EF", lineageColors: { "dendrogyriidae": "#FB923C" } };
const anthozoa_distichophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "distichophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Distichophylliidae", mainColor: "#0EA5E9", lineageColors: { "distichophylliidae": "#2DD4BF" } };
const anthozoa_clisiophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "clisiophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Clisiophyllidae", mainColor: "#22C55E", lineageColors: { "clisiophyllidae": "#A3E635" } };
const anthozoa_romanophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "romanophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Romanophyllidae", mainColor: "#EAB308", lineageColors: { "romanophyllidae": "#38BDF8" } };
const anthozoa_bogambirolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "bogambirolitidae", className: "Anthozoa", orderName: "Unknown", name: "Bogambirolitidae", mainColor: "#A855F7", lineageColors: { "bogambirolitidae": "#3B82F6" } };
const anthozoa_vojnovskytesidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "vojnovskytesidae", className: "Anthozoa", orderName: "Unknown", name: "Vojnovskytesidae", mainColor: "#FB923C", lineageColors: { "vojnovskytesidae": "#EF4444" } };
const anthozoa_hawaidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "hawaidae", className: "Anthozoa", orderName: "Unknown", name: "Hawaidae", mainColor: "#2DD4BF", lineageColors: { "hawaidae": "#10B981" } };
const anthozoa_madreporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "madreporidae", className: "Anthozoa", orderName: "Unknown", name: "Madreporidae", mainColor: "#A3E635", lineageColors: { "madreporidae": "#F59E0B" } };
const anthozoa_gerardidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "gerardidae", className: "Anthozoa", orderName: "Unknown", name: "Gerardidae", mainColor: "#38BDF8", lineageColors: { "gerardidae": "#8B5CF6" } };
const anthozoa_primnozoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "primnozoanthidae", className: "Anthozoa", orderName: "Unknown", name: "Primnozoanthidae", mainColor: "#3B82F6", lineageColors: { "primnozoanthidae": "#EC4899" } };
const anthozoa_parasitozoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "parasitozoanthidae", className: "Anthozoa", orderName: "Unknown", name: "Parasitozoanthidae", mainColor: "#EF4444", lineageColors: { "parasitozoanthidae": "#14B8A6" } };
const anthozoa_dasmiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "dasmiidae", className: "Anthozoa", orderName: "Unknown", name: "Dasmiidae", mainColor: "#10B981", lineageColors: { "dasmiidae": "#F97316" } };
const anthozoa_pruvostastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "pruvostastraeidae", className: "Anthozoa", orderName: "Unknown", name: "Pruvostastraeidae", mainColor: "#F59E0B", lineageColors: { "pruvostastraeidae": "#6366F1" } };
const anthozoa_cyclophyllopsidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "cyclophyllopsidae", className: "Anthozoa", orderName: "Unknown", name: "Cyclophyllopsidae", mainColor: "#8B5CF6", lineageColors: { "cyclophyllopsidae": "#84CC16" } };
const anthozoa_thamnasterioidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "thamnasterioidae", className: "Anthozoa", orderName: "Unknown", name: "Thamnasterioidae", mainColor: "#EC4899", lineageColors: { "thamnasterioidae": "#06B6D4" } };
const anthozoa_innaporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "innaporidae", className: "Anthozoa", orderName: "Unknown", name: "Innaporidae", mainColor: "#14B8A6", lineageColors: { "innaporidae": "#D946EF" } };
const anthozoa_angoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "angoporidae", className: "Anthozoa", orderName: "Unknown", name: "Angoporidae", mainColor: "#F97316", lineageColors: { "angoporidae": "#0EA5E9" } };
const anthozoa_dimorphophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "dimorphophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Dimorphophylliidae", mainColor: "#6366F1", lineageColors: { "dimorphophylliidae": "#22C55E" } };
const anthozoa_sinopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "sinopathidae", className: "Anthozoa", orderName: "Unknown", name: "Sinopathidae", mainColor: "#84CC16", lineageColors: { "sinopathidae": "#EAB308" } };
const anthozoa_latomaeandridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "latomaeandridae", className: "Anthozoa", orderName: "Unknown", name: "Latomaeandridae", mainColor: "#06B6D4", lineageColors: { "latomaeandridae": "#A855F7" } };
const anthozoa_pleurosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "pleurosmiliidae", className: "Anthozoa", orderName: "Unknown", name: "Pleurosmiliidae", mainColor: "#D946EF", lineageColors: { "pleurosmiliidae": "#FB923C" } };
const anthozoa_aplosmiliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "aplosmiliidae", className: "Anthozoa", orderName: "Unknown", name: "Aplosmiliidae", mainColor: "#0EA5E9", lineageColors: { "aplosmiliidae": "#2DD4BF" } };
const anthozoa_ellisitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "ellisitidae", className: "Anthozoa", orderName: "Unknown", name: "Ellisitidae", mainColor: "#22C55E", lineageColors: { "ellisitidae": "#A3E635" } };
const anthozoa_acrocyathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "acrocyathidae", className: "Anthozoa", orderName: "Unknown", name: "Acrocyathidae", mainColor: "#EAB308", lineageColors: { "acrocyathidae": "#38BDF8" } };
const anthozoa_flosmarinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "flosmarinidae", className: "Anthozoa", orderName: "Unknown", name: "Flosmarinidae", mainColor: "#A855F7", lineageColors: { "flosmarinidae": "#3B82F6" } };
const anthozoa_brachiphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "brachiphylliidae", className: "Anthozoa", orderName: "Unknown", name: "Brachiphylliidae", mainColor: "#FB923C", lineageColors: { "brachiphylliidae": "#EF4444" } };
const anthozoa_retiophylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "retiophylliidae", className: "Anthozoa", orderName: "Unknown", name: "Retiophylliidae", mainColor: "#2DD4BF", lineageColors: { "retiophylliidae": "#10B981" } };
const anthozoa_thamnastraeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "thamnastraeidae", className: "Anthozoa", orderName: "Unknown", name: "Thamnastraeidae", mainColor: "#A3E635", lineageColors: { "thamnastraeidae": "#F59E0B" } };
const anthozoa_reimaniphyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "reimaniphyllidae", className: "Anthozoa", orderName: "Unknown", name: "Reimaniphyllidae", mainColor: "#38BDF8", lineageColors: { "reimaniphyllidae": "#8B5CF6" } };
const anthozoa_symphylliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "symphylliidae", className: "Anthozoa", orderName: "Unknown", name: "Symphylliidae", mainColor: "#3B82F6", lineageColors: { "symphylliidae": "#EC4899" } };
const anthozoa_ceratocorallia: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "ceratocorallia", className: "Anthozoa", orderName: "Unknown", name: "Ceratocorallia", mainColor: "#EF4444", lineageColors: { "ceratocorallia": "#14B8A6" } };
const anthozoa_gyrophyllidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "gyrophyllidae", className: "Anthozoa", orderName: "Unknown", name: "Gyrophyllidae", mainColor: "#10B981", lineageColors: { "gyrophyllidae": "#F97316" } };
const anthozoa_primnoidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "primnoidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Primnoidae", mainColor: "#F59E0B", lineageColors: { "primnoidae": "#6366F1" } };
const anthozoa_ellisellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "ellisellidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Ellisellidae", mainColor: "#8B5CF6", lineageColors: { "ellisellidae": "#84CC16" } };
const anthozoa_pennatulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "pennatulidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Pennatulidae", mainColor: "#EC4899", lineageColors: { "pennatulidae": "#06B6D4" } };
const anthozoa_chrysogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "chrysogorgiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Chrysogorgiidae", mainColor: "#14B8A6", lineageColors: { "chrysogorgiidae": "#D946EF" } };
const anthozoa_coralliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "coralliidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Coralliidae", mainColor: "#F97316", lineageColors: { "coralliidae": "#0EA5E9" } };
const anthozoa_mopseidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "mopseidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Mopseidae", mainColor: "#6366F1", lineageColors: { "mopseidae": "#22C55E" } };
const anthozoa_virgulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "virgulariidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Virgulariidae", mainColor: "#84CC16", lineageColors: { "virgulariidae": "#EAB308" } };
const anthozoa_keratoisididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "keratoisididae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Keratoisididae", mainColor: "#06B6D4", lineageColors: { "keratoisididae": "#A855F7" } };
const anthozoa_veretillidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "veretillidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Veretillidae", mainColor: "#D946EF", lineageColors: { "veretillidae": "#FB923C" } };
const anthozoa_helioporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "helioporidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Helioporidae", mainColor: "#0EA5E9", lineageColors: { "helioporidae": "#2DD4BF" } };
const anthozoa_umbellulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "umbellulidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Umbellulidae", mainColor: "#22C55E", lineageColors: { "umbellulidae": "#A3E635" } };
const anthozoa_kophobelemnidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "kophobelemnidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Kophobelemnidae", mainColor: "#EAB308", lineageColors: { "kophobelemnidae": "#38BDF8" } };
const anthozoa_sarcodictyonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "sarcodictyonidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Sarcodictyonidae", mainColor: "#A855F7", lineageColors: { "sarcodictyonidae": "#3B82F6" } };
const anthozoa_renillidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "renillidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Renillidae", mainColor: "#FB923C", lineageColors: { "renillidae": "#EF4444" } };
const anthozoa_ifalukellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "ifalukellidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Ifalukellidae", mainColor: "#2DD4BF", lineageColors: { "ifalukellidae": "#10B981" } };
const anthozoa_spongiodermidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "spongiodermidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Spongiodermidae", mainColor: "#A3E635", lineageColors: { "spongiodermidae": "#F59E0B" } };
const anthozoa_briareidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "briareidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Briareidae", mainColor: "#38BDF8", lineageColors: { "briareidae": "#8B5CF6" } };
const anthozoa_parisididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "parisididae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Parisididae", mainColor: "#3B82F6", lineageColors: { "parisididae": "#EC4899" } };
const anthozoa_aulopsammiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "aulopsammiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Aulopsammiidae", mainColor: "#EF4444", lineageColors: { "aulopsammiidae": "#14B8A6" } };
const anthozoa_parasphaerascleridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "parasphaerascleridae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Parasphaerascleridae", mainColor: "#10B981", lineageColors: { "parasphaerascleridae": "#F97316" } };
const anthozoa_scleroptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "scleroptilidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Scleroptilidae", mainColor: "#F59E0B", lineageColors: { "scleroptilidae": "#6366F1" } };
const anthozoa_protoptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "protoptilidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Protoptilidae", mainColor: "#8B5CF6", lineageColors: { "protoptilidae": "#84CC16" } };
const anthozoa_echinoptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "echinoptilidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Echinoptilidae", mainColor: "#EC4899", lineageColors: { "echinoptilidae": "#06B6D4" } };
const anthozoa_anthoptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "anthoptilidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Anthoptilidae", mainColor: "#14B8A6", lineageColors: { "anthoptilidae": "#D946EF" } };
const anthozoa_balticinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "balticinidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Balticinidae", mainColor: "#F97316", lineageColors: { "balticinidae": "#0EA5E9" } };
const anthozoa_stachyptilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "stachyptilidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Stachyptilidae", mainColor: "#6366F1", lineageColors: { "stachyptilidae": "#22C55E" } };
const anthozoa_erythropodiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "erythropodiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Erythropodiidae", mainColor: "#84CC16", lineageColors: { "erythropodiidae": "#EAB308" } };
const anthozoa_funiculinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "funiculinidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Funiculinidae", mainColor: "#06B6D4", lineageColors: { "funiculinidae": "#A855F7" } };
const anthozoa_dendrobrachiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "dendrobrachiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Dendrobrachiidae", mainColor: "#D946EF", lineageColors: { "dendrobrachiidae": "#FB923C" } };
const anthozoa_cornulariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "cornulariidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Cornulariidae", mainColor: "#0EA5E9", lineageColors: { "cornulariidae": "#2DD4BF" } };
const anthozoa_chunellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "chunellidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Chunellidae", mainColor: "#22C55E", lineageColors: { "chunellidae": "#A3E635" } };
const anthozoa_chelidonisididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "chelidonisididae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Chelidonisididae", mainColor: "#EAB308", lineageColors: { "chelidonisididae": "#38BDF8" } };
const anthozoa_pleurogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "pleurogorgiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Pleurogorgiidae", mainColor: "#A855F7", lineageColors: { "pleurogorgiidae": "#3B82F6" } };
const anthozoa_ideogorgiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "ideogorgiidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Ideogorgiidae", mainColor: "#FB923C", lineageColors: { "ideogorgiidae": "#EF4444" } };
const anthozoa_pseudumbellulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "pseudumbellulidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Pseudumbellulidae", mainColor: "#2DD4BF", lineageColors: { "pseudumbellulidae": "#10B981" } };
const anthozoa_isidoidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "isidoidae", className: "Anthozoa", orderName: "Scleralcyonacea", name: "Isidoidae", mainColor: "#A3E635", lineageColors: { "isidoidae": "#F59E0B" } };
const anthozoa_actiniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "actiniidae", className: "Anthozoa", orderName: "Actiniaria", name: "Actiniidae", mainColor: "#38BDF8", lineageColors: { "actiniidae": "#8B5CF6" } };
const anthozoa_hormathiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "hormathiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Hormathiidae", mainColor: "#3B82F6", lineageColors: { "hormathiidae": "#EC4899" } };
const anthozoa_edwardsiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "edwardsiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Edwardsiidae", mainColor: "#EF4444", lineageColors: { "edwardsiidae": "#14B8A6" } };
const anthozoa_sagartiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "sagartiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Sagartiidae", mainColor: "#10B981", lineageColors: { "sagartiidae": "#F97316" } };
const anthozoa_andvakiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "andvakiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Andvakiidae", mainColor: "#F59E0B", lineageColors: { "andvakiidae": "#6366F1" } };
const anthozoa_actinostolidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "actinostolidae", className: "Anthozoa", orderName: "Actiniaria", name: "Actinostolidae", mainColor: "#8B5CF6", lineageColors: { "actinostolidae": "#84CC16" } };
const anthozoa_amphianthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "amphianthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Amphianthidae", mainColor: "#EC4899", lineageColors: { "amphianthidae": "#06B6D4" } };
const anthozoa_halcampidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "halcampidae", className: "Anthozoa", orderName: "Actiniaria", name: "Halcampidae", mainColor: "#14B8A6", lineageColors: { "halcampidae": "#D946EF" } };
const anthozoa_aiptasiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "aiptasiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Aiptasiidae", mainColor: "#F97316", lineageColors: { "aiptasiidae": "#0EA5E9" } };
const anthozoa_sicyonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "sicyonidae", className: "Anthozoa", orderName: "Actiniaria", name: "Sicyonidae", mainColor: "#6366F1", lineageColors: { "sicyonidae": "#22C55E" } };
const anthozoa_peachiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "peachiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Peachiidae", mainColor: "#84CC16", lineageColors: { "peachiidae": "#EAB308" } };
const anthozoa_haloclavidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "haloclavidae", className: "Anthozoa", orderName: "Actiniaria", name: "Haloclavidae", mainColor: "#06B6D4", lineageColors: { "haloclavidae": "#A855F7" } };
const anthozoa_halcampoididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "halcampoididae", className: "Anthozoa", orderName: "Actiniaria", name: "Halcampoididae", mainColor: "#D946EF", lineageColors: { "halcampoididae": "#FB923C" } };
const anthozoa_kadosactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "kadosactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Kadosactinidae", mainColor: "#0EA5E9", lineageColors: { "kadosactinidae": "#2DD4BF" } };
const anthozoa_isanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "isanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Isanthidae", mainColor: "#22C55E", lineageColors: { "isanthidae": "#A3E635" } };
const anthozoa_halcuriidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "halcuriidae", className: "Anthozoa", orderName: "Actiniaria", name: "Halcuriidae", mainColor: "#EAB308", lineageColors: { "halcuriidae": "#38BDF8" } };
const anthozoa_phymanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "phymanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Phymanthidae", mainColor: "#A855F7", lineageColors: { "phymanthidae": "#3B82F6" } };
const anthozoa_diadumenidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "diadumenidae", className: "Anthozoa", orderName: "Actiniaria", name: "Diadumenidae", mainColor: "#FB923C", lineageColors: { "diadumenidae": "#EF4444" } };
const anthozoa_condylanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "condylanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Condylanthidae", mainColor: "#2DD4BF", lineageColors: { "condylanthidae": "#10B981" } };
const anthozoa_aliciidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "aliciidae", className: "Anthozoa", orderName: "Actiniaria", name: "Aliciidae", mainColor: "#A3E635", lineageColors: { "aliciidae": "#F59E0B" } };
const anthozoa_minyadidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "minyadidae", className: "Anthozoa", orderName: "Actiniaria", name: "Minyadidae", mainColor: "#38BDF8", lineageColors: { "minyadidae": "#8B5CF6" } };
const anthozoa_stichodactylidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "stichodactylidae", className: "Anthozoa", orderName: "Actiniaria", name: "Stichodactylidae", mainColor: "#3B82F6", lineageColors: { "stichodactylidae": "#EC4899" } };
const anthozoa_actinodendridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "actinodendridae", className: "Anthozoa", orderName: "Actiniaria", name: "Actinodendridae", mainColor: "#EF4444", lineageColors: { "actinodendridae": "#14B8A6" } };
const anthozoa_haliactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "haliactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Haliactinidae", mainColor: "#10B981", lineageColors: { "haliactinidae": "#F97316" } };
const anthozoa_phelliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "phelliidae", className: "Anthozoa", orderName: "Actiniaria", name: "Phelliidae", mainColor: "#F59E0B", lineageColors: { "phelliidae": "#6366F1" } };
const anthozoa_actinernidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "actinernidae", className: "Anthozoa", orderName: "Actiniaria", name: "Actinernidae", mainColor: "#8B5CF6", lineageColors: { "actinernidae": "#84CC16" } };
const anthozoa_boloceroididae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "boloceroididae", className: "Anthozoa", orderName: "Actiniaria", name: "Boloceroididae", mainColor: "#EC4899", lineageColors: { "boloceroididae": "#06B6D4" } };
const anthozoa_thalassianthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "thalassianthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Thalassianthidae", mainColor: "#14B8A6", lineageColors: { "thalassianthidae": "#D946EF" } };
const anthozoa_bathyphelliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "bathyphelliidae", className: "Anthozoa", orderName: "Actiniaria", name: "Bathyphelliidae", mainColor: "#F97316", lineageColors: { "bathyphelliidae": "#0EA5E9" } };
const anthozoa_actinoscyphiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "actinoscyphiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Actinoscyphiidae", mainColor: "#6366F1", lineageColors: { "actinoscyphiidae": "#22C55E" } };
const anthozoa_capneidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "capneidae", className: "Anthozoa", orderName: "Actiniaria", name: "Capneidae", mainColor: "#84CC16", lineageColors: { "capneidae": "#EAB308" } };
const anthozoa_acontiophoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "acontiophoridae", className: "Anthozoa", orderName: "Actiniaria", name: "Acontiophoridae", mainColor: "#06B6D4", lineageColors: { "acontiophoridae": "#A855F7" } };
const anthozoa_metridiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "metridiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Metridiidae", mainColor: "#D946EF", lineageColors: { "metridiidae": "#FB923C" } };
const anthozoa_aiptasiomorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "aiptasiomorphidae", className: "Anthozoa", orderName: "Actiniaria", name: "Aiptasiomorphidae", mainColor: "#0EA5E9", lineageColors: { "aiptasiomorphidae": "#2DD4BF" } };
const anthozoa_octineonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "octineonidae", className: "Anthozoa", orderName: "Actiniaria", name: "Octineonidae", mainColor: "#22C55E", lineageColors: { "octineonidae": "#A3E635" } };
const anthozoa_anthosactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "anthosactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Anthosactinidae", mainColor: "#EAB308", lineageColors: { "anthosactinidae": "#38BDF8" } };
const anthozoa_liponematidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "liponematidae", className: "Anthozoa", orderName: "Actiniaria", name: "Liponematidae", mainColor: "#A855F7", lineageColors: { "liponematidae": "#3B82F6" } };
const anthozoa_isactinernidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "isactinernidae", className: "Anthozoa", orderName: "Actiniaria", name: "Isactinernidae", mainColor: "#FB923C", lineageColors: { "isactinernidae": "#EF4444" } };
const anthozoa_harenactidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "harenactidae", className: "Anthozoa", orderName: "Actiniaria", name: "Harenactidae", mainColor: "#2DD4BF", lineageColors: { "harenactidae": "#10B981" } };
const anthozoa_nemanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "nemanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Nemanthidae", mainColor: "#A3E635", lineageColors: { "nemanthidae": "#F59E0B" } };
const anthozoa_oractiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "oractiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Oractiidae", mainColor: "#38BDF8", lineageColors: { "oractiidae": "#8B5CF6" } };
const anthozoa_iosactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "iosactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Iosactinidae", mainColor: "#3B82F6", lineageColors: { "iosactinidae": "#EC4899" } };
const anthozoa_galatheanthemidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "galatheanthemidae", className: "Anthozoa", orderName: "Actiniaria", name: "Galatheanthemidae", mainColor: "#EF4444", lineageColors: { "galatheanthemidae": "#14B8A6" } };
const anthozoa_preactiniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "preactiniidae", className: "Anthozoa", orderName: "Actiniaria", name: "Preactiniidae", mainColor: "#10B981", lineageColors: { "preactiniidae": "#F97316" } };
const anthozoa_limnactiniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "limnactiniidae", className: "Anthozoa", orderName: "Actiniaria", name: "Limnactiniidae", mainColor: "#F59E0B", lineageColors: { "limnactiniidae": "#6366F1" } };
const anthozoa_homostichanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "homostichanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Homostichanthidae", mainColor: "#8B5CF6", lineageColors: { "homostichanthidae": "#84CC16" } };
const anthozoa_gonactiniidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "gonactiniidae", className: "Anthozoa", orderName: "Actiniaria", name: "Gonactiniidae", mainColor: "#EC4899", lineageColors: { "gonactiniidae": "#06B6D4" } };
const anthozoa_ptychodactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "ptychodactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Ptychodactinidae", mainColor: "#14B8A6", lineageColors: { "ptychodactinidae": "#D946EF" } };
const anthozoa_exocoelactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "exocoelactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Exocoelactinidae", mainColor: "#F97316", lineageColors: { "exocoelactinidae": "#0EA5E9" } };
const anthozoa_polyopidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "polyopidae", className: "Anthozoa", orderName: "Actiniaria", name: "Polyopidae", mainColor: "#6366F1", lineageColors: { "polyopidae": "#22C55E" } };
const anthozoa_haliplanellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "haliplanellidae", className: "Anthozoa", orderName: "Actiniaria", name: "Haliplanellidae", mainColor: "#84CC16", lineageColors: { "haliplanellidae": "#EAB308" } };
const anthozoa_sagartiomorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "sagartiomorphidae", className: "Anthozoa", orderName: "Actiniaria", name: "Sagartiomorphidae", mainColor: "#06B6D4", lineageColors: { "sagartiomorphidae": "#A855F7" } };
const anthozoa_nevadneidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "nevadneidae", className: "Anthozoa", orderName: "Actiniaria", name: "Nevadneidae", mainColor: "#D946EF", lineageColors: { "nevadneidae": "#FB923C" } };
const anthozoa_andresiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "andresiidae", className: "Anthozoa", orderName: "Actiniaria", name: "Andresiidae", mainColor: "#0EA5E9", lineageColors: { "andresiidae": "#2DD4BF" } };
const anthozoa_heteractidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "heteractidae", className: "Anthozoa", orderName: "Actiniaria", name: "Heteractidae", mainColor: "#22C55E", lineageColors: { "heteractidae": "#A3E635" } };
const anthozoa_heteranthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "heteranthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Heteranthidae", mainColor: "#EAB308", lineageColors: { "heteranthidae": "#38BDF8" } };
const anthozoa_sarcophinanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "sarcophinanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Sarcophinanthidae", mainColor: "#A855F7", lineageColors: { "sarcophinanthidae": "#3B82F6" } };
const anthozoa_antheomorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "antheomorphidae", className: "Anthozoa", orderName: "Actiniaria", name: "Antheomorphidae", mainColor: "#FB923C", lineageColors: { "antheomorphidae": "#EF4444" } };
const anthozoa_ostiactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "ostiactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Ostiactinidae", mainColor: "#2DD4BF", lineageColors: { "ostiactinidae": "#10B981" } };
const anthozoa_acricoactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "acricoactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Acricoactinidae", mainColor: "#A3E635", lineageColors: { "acricoactinidae": "#F59E0B" } };
const anthozoa_spongiactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "spongiactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Spongiactinidae", mainColor: "#38BDF8", lineageColors: { "spongiactinidae": "#8B5CF6" } };
const anthozoa_relicanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "relicanthidae", className: "Anthozoa", orderName: "Actiniaria", name: "Relicanthidae", mainColor: "#3B82F6", lineageColors: { "relicanthidae": "#EC4899" } };
const anthozoa_halcampulactidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "halcampulactidae", className: "Anthozoa", orderName: "Actiniaria", name: "Halcampulactidae", mainColor: "#EF4444", lineageColors: { "halcampulactidae": "#14B8A6" } };
const anthozoa_tetracoelactinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "tetracoelactinidae", className: "Anthozoa", orderName: "Actiniaria", name: "Tetracoelactinidae", mainColor: "#10B981", lineageColors: { "tetracoelactinidae": "#F97316" } };
const anthozoa_mackenziidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "mackenziidae", className: "Anthozoa", orderName: "Actiniaria", name: "Mackenziidae", mainColor: "#F59E0B", lineageColors: { "mackenziidae": "#6366F1" } };
const anthozoa_sphenopidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "sphenopidae", className: "Anthozoa", orderName: "Zoantharia", name: "Sphenopidae", mainColor: "#8B5CF6", lineageColors: { "sphenopidae": "#84CC16" } };
const anthozoa_zoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "zoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Zoanthidae", mainColor: "#EC4899", lineageColors: { "zoanthidae": "#06B6D4" } };
const anthozoa_parazoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "parazoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Parazoanthidae", mainColor: "#14B8A6", lineageColors: { "parazoanthidae": "#D946EF" } };
const anthozoa_epizoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "epizoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Epizoanthidae", mainColor: "#F97316", lineageColors: { "epizoanthidae": "#0EA5E9" } };
const anthozoa_hydrozoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "hydrozoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Hydrozoanthidae", mainColor: "#6366F1", lineageColors: { "hydrozoanthidae": "#22C55E" } };
const anthozoa_neozoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "neozoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Neozoanthidae", mainColor: "#84CC16", lineageColors: { "neozoanthidae": "#EAB308" } };
const anthozoa_abyssoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "abyssoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Abyssoanthidae", mainColor: "#06B6D4", lineageColors: { "abyssoanthidae": "#A855F7" } };
const anthozoa_microzoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "microzoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Microzoanthidae", mainColor: "#D946EF", lineageColors: { "microzoanthidae": "#FB923C" } };
const anthozoa_nanozoanthidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "nanozoanthidae", className: "Anthozoa", orderName: "Zoantharia", name: "Nanozoanthidae", mainColor: "#0EA5E9", lineageColors: { "nanozoanthidae": "#2DD4BF" } };
const anthozoa_antipathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "antipathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Antipathidae", mainColor: "#22C55E", lineageColors: { "antipathidae": "#A3E635" } };
const anthozoa_schizopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "schizopathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Schizopathidae", mainColor: "#EAB308", lineageColors: { "schizopathidae": "#38BDF8" } };
const anthozoa_aphanipathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "aphanipathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Aphanipathidae", mainColor: "#A855F7", lineageColors: { "aphanipathidae": "#3B82F6" } };
const anthozoa_myriopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "myriopathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Myriopathidae", mainColor: "#FB923C", lineageColors: { "myriopathidae": "#EF4444" } };
const anthozoa_cladopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "cladopathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Cladopathidae", mainColor: "#2DD4BF", lineageColors: { "cladopathidae": "#10B981" } };
const anthozoa_stylopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A3E635", hybridColor: "#F59E0B", appSlug: "stylopathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Stylopathidae", mainColor: "#A3E635", lineageColors: { "stylopathidae": "#F59E0B" } };
const anthozoa_leiopathidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#38BDF8", hybridColor: "#8B5CF6", appSlug: "leiopathidae", className: "Anthozoa", orderName: "Antipatharia", name: "Leiopathidae", mainColor: "#38BDF8", lineageColors: { "leiopathidae": "#8B5CF6" } };
const anthozoa_corallimorphidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#3B82F6", hybridColor: "#EC4899", appSlug: "corallimorphidae", className: "Anthozoa", orderName: "Corallimorpharia", name: "Corallimorphidae", mainColor: "#3B82F6", lineageColors: { "corallimorphidae": "#EC4899" } };
const anthozoa_discosomidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "discosomidae", className: "Anthozoa", orderName: "Corallimorpharia", name: "Discosomidae", mainColor: "#EF4444", lineageColors: { "discosomidae": "#14B8A6" } };
const anthozoa_sideractinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "sideractinidae", className: "Anthozoa", orderName: "Corallimorpharia", name: "Sideractinidae", mainColor: "#10B981", lineageColors: { "sideractinidae": "#F97316" } };
const anthozoa_ricordeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "ricordeidae", className: "Anthozoa", orderName: "Corallimorpharia", name: "Ricordeidae", mainColor: "#F59E0B", lineageColors: { "ricordeidae": "#6366F1" } };
const anthozoa_heliolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "heliolitidae", className: "Anthozoa", orderName: "Heliolitina", name: "Heliolitidae", mainColor: "#8B5CF6", lineageColors: { "heliolitidae": "#84CC16" } };
const anthozoa_stelliporellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "stelliporellidae", className: "Anthozoa", orderName: "Heliolitina", name: "Stelliporellidae", mainColor: "#EC4899", lineageColors: { "stelliporellidae": "#06B6D4" } };
const anthozoa_palaeoporitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "palaeoporitidae", className: "Anthozoa", orderName: "Heliolitina", name: "Palaeoporitidae", mainColor: "#14B8A6", lineageColors: { "palaeoporitidae": "#D946EF" } };
const anthozoa_plasmoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "plasmoporidae", className: "Anthozoa", orderName: "Heliolitina", name: "Plasmoporidae", mainColor: "#F97316", lineageColors: { "plasmoporidae": "#0EA5E9" } };
const anthozoa_sibiriolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "sibiriolitidae", className: "Anthozoa", orderName: "Heliolitina", name: "Sibiriolitidae", mainColor: "#6366F1", lineageColors: { "sibiriolitidae": "#22C55E" } };
const anthozoa_pseudoplasmoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "pseudoplasmoporidae", className: "Anthozoa", orderName: "Heliolitina", name: "Pseudoplasmoporidae", mainColor: "#84CC16", lineageColors: { "pseudoplasmoporidae": "#EAB308" } };


// ── Caudofoveata (3 families) ──
const caudofoveata_chaetodermatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "chaetodermatidae", className: "Caudofoveata", orderName: "Chaetodermatida", name: "Chaetodermatidae", mainColor: "#EF4444", lineageColors: { "chaetodermatidae": "#14B8A6" } };
const caudofoveata_prochaetodermatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "prochaetodermatidae", className: "Caudofoveata", orderName: "Chaetodermatida", name: "Prochaetodermatidae", mainColor: "#10B981", lineageColors: { "prochaetodermatidae": "#F97316" } };
const caudofoveata_limifossoridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "limifossoridae", className: "Caudofoveata", orderName: "Chaetodermatida", name: "Limifossoridae", mainColor: "#F59E0B", lineageColors: { "limifossoridae": "#6366F1" } };


// ── Monoplacophora (15 families) ──
const monoplacophora_tryblidiidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "tryblidiidae", className: "Monoplacophora", orderName: "Tryblidiida", name: "Tryblidiidae", mainColor: "#EF4444", lineageColors: { "tryblidiidae": "#14B8A6" } };
const monoplacophora_proplinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "proplinidae", className: "Monoplacophora", orderName: "Tryblidiida", name: "Proplinidae", mainColor: "#10B981", lineageColors: { "proplinidae": "#F97316" } };
const monoplacophora_archaeophialidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "archaeophialidae", className: "Monoplacophora", orderName: "Tryblidiida", name: "Archaeophialidae", mainColor: "#F59E0B", lineageColors: { "archaeophialidae": "#6366F1" } };
const monoplacophora_peelipilinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "peelipilinidae", className: "Monoplacophora", orderName: "Tryblidiida", name: "Peelipilinidae", mainColor: "#8B5CF6", lineageColors: { "peelipilinidae": "#84CC16" } };
const monoplacophora_cyrtolitidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "cyrtolitidae", className: "Monoplacophora", orderName: "Cyrtonellida", name: "Cyrtolitidae", mainColor: "#EC4899", lineageColors: { "cyrtolitidae": "#06B6D4" } };
const monoplacophora_carcassonnellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "carcassonnellidae", className: "Monoplacophora", orderName: "Cyrtonellida", name: "Carcassonnellidae", mainColor: "#14B8A6", lineageColors: { "carcassonnellidae": "#D946EF" } };
const monoplacophora_cyrtonellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "cyrtonellidae", className: "Monoplacophora", orderName: "Cyrtonellida", name: "Cyrtonellidae", mainColor: "#F97316", lineageColors: { "cyrtonellidae": "#0EA5E9" } };
const monoplacophora_hypseloconidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "hypseloconidae", className: "Monoplacophora", orderName: "Kirengellida", name: "Hypseloconidae", mainColor: "#6366F1", lineageColors: { "hypseloconidae": "#22C55E" } };
const monoplacophora_kirengellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "kirengellidae", className: "Monoplacophora", orderName: "Kirengellida", name: "Kirengellidae", mainColor: "#84CC16", lineageColors: { "kirengellidae": "#EAB308" } };
const monoplacophora_metoptomatidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "metoptomatidae", className: "Monoplacophora", orderName: "Unknown", name: "Metoptomatidae", mainColor: "#06B6D4", lineageColors: { "metoptomatidae": "#A855F7" } };
const monoplacophora_palaeacmaeidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "palaeacmaeidae", className: "Monoplacophora", orderName: "Unknown", name: "Palaeacmaeidae", mainColor: "#D946EF", lineageColors: { "palaeacmaeidae": "#FB923C" } };
const monoplacophora_shelbyoceridae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "shelbyoceridae", className: "Monoplacophora", orderName: "Unknown", name: "Shelbyoceridae", mainColor: "#0EA5E9", lineageColors: { "shelbyoceridae": "#2DD4BF" } };
const monoplacophora_cyclocyrtonellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "cyclocyrtonellidae", className: "Monoplacophora", orderName: "Unknown", name: "Cyclocyrtonellidae", mainColor: "#22C55E", lineageColors: { "cyclocyrtonellidae": "#A3E635" } };
const monoplacophora_multifariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "multifariidae", className: "Monoplacophora", orderName: "Unknown", name: "Multifariidae", mainColor: "#EAB308", lineageColors: { "multifariidae": "#38BDF8" } };
const monoplacophora_neopilinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "neopilinidae", className: "Monoplacophora", orderName: "Neopilinida", name: "Neopilinidae", mainColor: "#A855F7", lineageColors: { "neopilinidae": "#3B82F6" } };


// ── Scaphopoda (17 families) ──
const scaphopoda_dentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EF4444", hybridColor: "#14B8A6", appSlug: "dentaliidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Dentaliidae", mainColor: "#EF4444", lineageColors: { "dentaliidae": "#14B8A6" } };
const scaphopoda_gadilinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#10B981", hybridColor: "#F97316", appSlug: "gadilinidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Gadilinidae", mainColor: "#10B981", lineageColors: { "gadilinidae": "#F97316" } };
const scaphopoda_laevidentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F59E0B", hybridColor: "#6366F1", appSlug: "laevidentaliidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Laevidentaliidae", mainColor: "#F59E0B", lineageColors: { "laevidentaliidae": "#6366F1" } };
const scaphopoda_fustiariidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#8B5CF6", hybridColor: "#84CC16", appSlug: "fustiariidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Fustiariidae", mainColor: "#8B5CF6", lineageColors: { "fustiariidae": "#84CC16" } };
const scaphopoda_prodentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EC4899", hybridColor: "#06B6D4", appSlug: "prodentaliidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Prodentaliidae", mainColor: "#EC4899", lineageColors: { "prodentaliidae": "#06B6D4" } };
const scaphopoda_rhabdidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#14B8A6", hybridColor: "#D946EF", appSlug: "rhabdidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Rhabdidae", mainColor: "#14B8A6", lineageColors: { "rhabdidae": "#D946EF" } };
const scaphopoda_calliodentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#F97316", hybridColor: "#0EA5E9", appSlug: "calliodentaliidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Calliodentaliidae", mainColor: "#F97316", lineageColors: { "calliodentaliidae": "#0EA5E9" } };
const scaphopoda_anulidentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#6366F1", hybridColor: "#22C55E", appSlug: "anulidentaliidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Anulidentaliidae", mainColor: "#6366F1", lineageColors: { "anulidentaliidae": "#22C55E" } };
const scaphopoda_omniglyptidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#84CC16", hybridColor: "#EAB308", appSlug: "omniglyptidae", className: "Scaphopoda", orderName: "Dentaliida", name: "Omniglyptidae", mainColor: "#84CC16", lineageColors: { "omniglyptidae": "#EAB308" } };
const scaphopoda_gadilidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#06B6D4", hybridColor: "#A855F7", appSlug: "gadilidae", className: "Scaphopoda", orderName: "Gadilida", name: "Gadilidae", mainColor: "#06B6D4", lineageColors: { "gadilidae": "#A855F7" } };
const scaphopoda_entalinidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#D946EF", hybridColor: "#FB923C", appSlug: "entalinidae", className: "Scaphopoda", orderName: "Gadilida", name: "Entalinidae", mainColor: "#D946EF", lineageColors: { "entalinidae": "#FB923C" } };
const scaphopoda_pulsellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#0EA5E9", hybridColor: "#2DD4BF", appSlug: "pulsellidae", className: "Scaphopoda", orderName: "Gadilida", name: "Pulsellidae", mainColor: "#0EA5E9", lineageColors: { "pulsellidae": "#2DD4BF" } };
const scaphopoda_wemersoniellidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#22C55E", hybridColor: "#A3E635", appSlug: "wemersoniellidae", className: "Scaphopoda", orderName: "Gadilida", name: "Wemersoniellidae", mainColor: "#22C55E", lineageColors: { "wemersoniellidae": "#A3E635" } };
const scaphopoda_loxoporidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#EAB308", hybridColor: "#38BDF8", appSlug: "loxoporidae", className: "Scaphopoda", orderName: "Unknown", name: "Loxoporidae", mainColor: "#EAB308", lineageColors: { "loxoporidae": "#38BDF8" } };
const scaphopoda_cadulidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#A855F7", hybridColor: "#3B82F6", appSlug: "cadulidae", className: "Scaphopoda", orderName: "Unknown", name: "Cadulidae", mainColor: "#A855F7", lineageColors: { "cadulidae": "#3B82F6" } };
const scaphopoda_baltodentaliidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#FB923C", hybridColor: "#EF4444", appSlug: "baltodentaliidae", className: "Scaphopoda", orderName: "Unknown", name: "Baltodentaliidae", mainColor: "#FB923C", lineageColors: { "baltodentaliidae": "#EF4444" } };
const scaphopoda_episiphonidae: ColorTheme = { subfamilyColors: {}, breedGroupColor: "#2DD4BF", hybridColor: "#10B981", appSlug: "episiphonidae", className: "Scaphopoda", orderName: "Unknown", name: "Episiphonidae", mainColor: "#2DD4BF", lineageColors: { "episiphonidae": "#10B981" } };

export const COLOR_REGISTRY: Record<string, ColorTheme> = {
  alatinidae:    ALATINIDAE_THEME,
  carukiidae:    CARUKIIDAE_THEME,
  carybdeidae:   CARYBDEIDAE_THEME,
  tamoyidae:     TAMOYIDAE_THEME,
  tripedaliidae: TRIPEDALIIDAE_THEME,
  chirodropidae: CHIRODROPIDAE_THEME,
  chiropsalmidae: CHIROPSALMIDAE_THEME,
  chiropsellidae: CHIROPSELIDAE_THEME,

  atollidae:      ATOLLIDAE_THEME,
  linuchidae:     LINUCHIDAE_THEME,
  nausithoidae:   NAUSITHOIDAE_THEME,
  paraphyllinidae: PARAPHYLLINIDAE_THEME,
  periphyllidae:  PERIPHYLLIDAE_THEME,
  cyaneidae:      CYANEIDAE_THEME,
  drymonematidae: DRYMONEMATIDAE_THEME,
  pelagiidae:     PELAGIIDAE_THEME,
  phacellophoridae: PHACELLOPHORIDAE_THEME,
  ulmaridae:      ULMARIDAE_THEME,
  archirhizidae:  ARCHIRHIZIDAE_THEME,
  cassiopeidae:   CASSIOPEIDAE_THEME,
  catostylidae:   CATOSTYLIDAE_THEME,
  cepheidae:      CEPHEIDAE_THEME,
  lobonematidae:  LOBONEMATIDAE_THEME,
  lychnorhizidae: LYCHNORHIZIDAE_THEME,
  mastigiidae:    MASTIGIIDAE_THEME,
  rhizostomatidae: RHIZOSTOMATIDAE_THEME,
  stomolophidae:  STOMOLOPHIDAE_THEME,
  versurigidae:   VERSURIGIDAE_THEME,

  craterolophidae:  CRATEROLOPHIDAE_THEME,
  haliclystidae:    HALICLYSTIDAE_THEME,
  kishinouyeidae:   KISHINOUYEIDAE_THEME,
  kyopodiidae:      KYOPODIIDAE_THEME,
  lipkeidae:        LIPKEIDAE_THEME,
  lucernariidae:    LUCERNARIIDAE_THEME,
  tesseranthidae:   TESSERANTHIDAE_THEME,
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
  mustelidae:      MUSTELIDAE_THEME,
  ursidae:         URSIDAE_THEME,
  phocidae:        PHOCIDAE_THEME,
  testudinidae:    TESTUDINIDAE_THEME,
  geoemydidae:     GEOEMYDIDAE_THEME,
  viperidae:       VIPERIDAE_THEME,
  chamaeleonidae:  CHAMAELEONIDAE_THEME,
  turdidae:        TURDIDAE_THEME,
  fringillidae:    FRINGILLIDAE_THEME,
  muscicapidae:    MUSCICAPIDAE_THEME,
  strigidae:       STRIGIDAE_THEME,
  tytonidae:       TYTONIDAE_THEME,
  accipitridae:    ACCIPITRIDAE_THEME,
  salamandridae:   SALAMANDRIDAE_THEME,
  ranidae:         RANIDAE_THEME,
  apidae:          APIDAE_THEME,
  tardigrada:      TARDIGRADA_THEME,
  muridae:         MURIDAE_THEME,
  sciuridae:       SCIURIDAE_THEME,
  cricetidae:      CRICETIDAE_THEME,
  castoridae:      CASTORIDAE_THEME,
  caviidae:        CAVIIDAE_THEME,
  pteropodidae:    PTEROPODIDAE_THEME,
  vespertilionidae: VESPERTILIONIDAE_THEME,
  rhinolophidae:   RHINOLOPHIDAE_THEME,
  phyllostomidae:  PHYLLOSTOMIDAE_THEME,
  erinaceidae:     ERINACEIDAE_THEME,
  soricidae:       SORICIDAE_THEME,
  talpidae:        TALPIDAE_THEME,
  elephantidae:    ELEPHANTIDAE_THEME,
  manidae:         MANIDAE_THEME,
  bradypodidae:    BRADYPODIDAE_THEME,
  myrmecophagidae: MYRMECOPHAGIDAE_THEME,
  dasypodidae:     DASYPODIDAE_THEME,
  dasyuridae:      DASYURIDAE_THEME,
  vombatidae:      VOMBATIDAE_THEME,
  didelphidae:     DIDELPHIDAE_THEME,
  clupeidae:       CLUPEIDAE_THEME,
  salmonidae:      SALMONIDAE_THEME,
  esocidae:        ESOCIDAE_THEME,
  percidae:        PERCIDAE_THEME,
  gadidae:         GADIDAE_THEME,
  cyprinidae:      CYPRINIDAE_THEME,
  gasterosteidae:  GASTEROSTEIDAE_THEME,
  anguillidae:     ANGUILLIDAE_THEME,
  cottidae:        COTTIDAE_THEME,
  psittacidae:     PSITTACIDAE_THEME,
  papilionidae:    PAPILIONIDAE_THEME,
  pleuronectidae:  PLEURONECTIDAE_THEME,
  motacillidae:    MOTACILLIDAE_THEME,
  hirundinidae:    HIRUNDINIDAE_THEME,
  phylloscopidae:  PHYLLOSCOPIDAE_THEME,
  laridae:         LARIDAE_THEME,
  ardeidae:        ARDEIDAE_THEME,
  rallidae:        RALLIDAE_THEME,
  gruidae:         GRUIDAE_THEME,
  podicipedidae:   PODICIPEDIDAE_THEME,
  scolopacidae:    SCOLOPACIDAE_THEME,
  alcidae:         ALCIDAE_THEME,
  phalacrocoracidae: PHALACROCORACIDAE_THEME,
  sturnidae:       STURNIDAE_THEME,
  acrocephalidae:  ACROCEPHALIDAE_THEME,
  regulidae:       REGULIDAE_THEME,
  gaviidae:        GAVIIDAE_THEME,
  falconidae:      FALCONIDAE_THEME,
  apodidae:        APODIDAE_THEME,
  cuculidae:       CUCULIDAE_THEME,
  caprimulgidae:   CAPRIMULGIDAE_THEME,
  alcedinidae:     ALCEDINIDAE_THEME,
  upupidae:        UPUPIDAE_THEME,
  charadriidae:    CHARADRIIDAE_THEME,
  haematopodidae:  HAEMATOPODIDAE_THEME,
  recurvirostridae: RECURVIROSTRIDAE_THEME,
  stercorariidae:  STERCORARIIDAE_THEME,
  threskiornithidae: THRESKIORNITHIDAE_THEME,
  ciconiidae:      CICONIIDAE_THEME,
  sulidae:         SULIDAE_THEME,
  pandionidae:     PANDIONIDAE_THEME,
  sylviidae:       SYLVIIDAE_THEME,
  aegithalidae:    AEGITHALIDAE_THEME,
  sittidae:        SITTIDAE_THEME,
  certhiidae:      CERTHIIDAE_THEME,
  troglodytidae:   TROGLODYTIDAE_THEME,
  bombycillidae:   BOMBYCILLIDAE_THEME,
  emberizidae:     EMBERIZIDAE_THEME,
  passeridae:      PASSERIDAE_THEME,
  prunellidae:     PRUNELLIDAE_THEME,
  alaudidae:       ALAUDIDAE_THEME,
  locustellidae:   LOCUSTELLIDAE_THEME,
  laniidae:        LANIIDAE_THEME,
  oriolidae:       ORIOLIDAE_THEME,
  remizidae:       REMIZIDAE_THEME,
  cinclidae:       CINCLIDAE_THEME,
  panuridae:       PANURIDAE_THEME,
  cisticolidae:    CISTICOLIDAE_THEME,
  spheniscidae:    SPHENISCIDAE_THEME,
  trochilidae:     TROCHILIDAE_THEME,
  phoenicopteridae: PHOENICOPTERIDAE_THEME,
  procellariidae:   PROCELLARIIDAE_THEME,
  hydrobatidae:     HYDROBATIDAE_THEME,
  polioptilidae:    POLIOPTILIDAE_THEME,
  pelecanidae:      PELECANIDAE_THEME,
  otididae:         OTIDIDAE_THEME,
  meropidae:        MEROPIDAE_THEME,
  coraciidae:       CORACIIDAE_THEME,
  pteroclidae:      PTEROCLIDAE_THEME,
  burhinidae:       BURHINIDAE_THEME,
  glareolidae:      GLAREOLIDAE_THEME,
  jacanidae:        JACANIDAE_THEME,
  numididae:        NUMIDIDAE_THEME,
  ramphastidae:     RAMPHASTIDAE_THEME,
  megalaimidae:     MEGALAIMIDAE_THEME,
  cacatuidae:       CACATUIDAE_THEME,
  diomedeidae:      DIOMEDEIDAE_THEME,
  menuridae:        MENURIDAE_THEME,
  mimidae:          MIMIDAE_THEME,
  nectariniidae:    NECTARINIIDAE_THEME,
  paradisaeidae:    PARADISAEIDAE_THEME,
  ptilonorhynchidae: PTILONORHYNCHIDAE_THEME,
  pycnonotidae:     PYCNONOTIDAE_THEME,
  estrildidae:      ESTRILDIDAE_THEME,
  icteridae:        ICTERIDAE_THEME,
  cardinalidae:     CARDINALIDAE_THEME,
  parulidae:        PARULIDAE_THEME,
  thraupidae:       THRAUPIDAE_THEME,
  tyrannidae:       TYRANNIDAE_THEME,
  vireonidae:       VIREONIDAE_THEME,
  fregatidae:       FREGATIDAE_THEME,
  anhingidae:       ANHINGIDAE_THEME,
  sagittariidae:    SAGITTARIIDAE_THEME,
  cathartidae:      CATHARTIDAE_THEME,
  acanthisittidae:     ACANTHISITTIDAE_THEME,
  acanthizidae:        ACANTHIZIDAE_THEME,
  aegithinidae:        AEGITHINIDAE_THEME,
  aegothelidae:        AEGOTHELIDAE_THEME,
  alcippeidae:         ALCIPPEIDAE_THEME,
  anhimidae:           ANHIMIDAE_THEME,
  anseranatidae:       ANSERANATIDAE_THEME,
  apterygidae:         APTERYGIDAE_THEME,
  aramidae:            ARAMIDAE_THEME,
  artamidae:           ARTAMIDAE_THEME,
  atrichornithidae:    ATRICHORNITHIDAE_THEME,
  balaenicipitidae:    BALAENICIPITIDAE_THEME,
  bernieriidae:        BERNIERIIDAE_THEME,
  brachypteraciidae:   BRACHYPTERACIIDAE_THEME,
  bucconidae:          BUCCONIDAE_THEME,
  bucerotidae:         BUCEROTIDAE_THEME,
  bucorvidae:          BUCORVIDAE_THEME,
  buphagidae:          BUPHAGIDAE_THEME,
  calcariidae:         CALCARIIDAE_THEME,
  callaeidae:          CALLAEIDAE_THEME,
  calyptomenidae:      CALYPTOMENIDAE_THEME,
  calyptophilidae:     CALYPTOPHILIDAE_THEME,
  campephagidae:       CAMPEPHAGIDAE_THEME,
  capitonidae:         CAPITONIDAE_THEME,
  cariamidae:          CARIAMIDAE_THEME,
  casuariidae:         CASUARIIDAE_THEME,
  cettiidae:           CETTIIDAE_THEME,
  chaetopidae:         CHAETOPIDAE_THEME,
  chionidae:           CHIONIDAE_THEME,
  chloropseidae:       CHLOROPSEIDAE_THEME,
  cinclosomatidae:     CINCLOSOMATIDAE_THEME,
  climacteridae:       CLIMACTERIDAE_THEME,
  cnemophilidae:       CNEMOPHILIDAE_THEME,
  coliidae:            COLIIDAE_THEME,
  conopophagidae:      CONOPOPHAGIDAE_THEME,
  corcoracidae:        CORCORACIDAE_THEME,
  cotingidae:          COTINGIDAE_THEME,
  cracidae:            CRACIDAE_THEME,
  dasyornithidae:      DASYORNITHIDAE_THEME,
  dicaeidae:           DICAEIDAE_THEME,
  dicruridae:          DICRURIDAE_THEME,
  donacobiidae:        DONACOBIIDAE_THEME,
  dromadidae:          DROMADIDAE_THEME,
  dulidae:             DULIDAE_THEME,
  elachuridae:         ELACHURIDAE_THEME,
  erythrocercidae:     ERYTHROCERCIDAE_THEME,
  eulacestomatidae:    EULACESTOMATIDAE_THEME,
  eupetidae:           EUPETIDAE_THEME,
  eurylaimidae:        EURYLAIMIDAE_THEME,
  eurypygidae:         EURYPYGIDAE_THEME,
  falcunculidae:       FALCUNCULIDAE_THEME,
  formicariidae:       FORMICARIIDAE_THEME,
  furnariidae:         FURNARIIDAE_THEME,
  galbulidae:          GALBULIDAE_THEME,
  grallariidae:        GRALLARIIDAE_THEME,
  heliornithidae:      HELIORNITHIDAE_THEME,
  hemiprocnidae:       HEMIPROCNIDAE_THEME,
  hyliidae:            HYLIIDAE_THEME,
  hyliotidae:          HYLIOTIDAE_THEME,
  hylocitreidae:       HYLOCITREIDAE_THEME,
  hypocoliidae:        HYPOCOLIIDAE_THEME,
  ibidorhynchidae:     IBIDORHYNCHIDAE_THEME,
  icteriidae:          ICTERIIDAE_THEME,
  ifritidae:           IFRITIDAE_THEME,
  indicatoridae:       INDICATORIDAE_THEME,
  irenidae:            IRENIDAE_THEME,
  leiothrichidae:      LEIOTHRICHIDAE_THEME,
  leptosomidae:        LEPTOSOMIDAE_THEME,
  lybiidae:            LYBIIDAE_THEME,
  machaerirhynchidae:  MACHAERIRHYNCHIDAE_THEME,
  macrosphenidae:      MACROSPHENIDAE_THEME,
  malaconotidae:       MALACONOTIDAE_THEME,
  maluridae:           MALURIDAE_THEME,
  megapodiidae:        MEGAPODIIDAE_THEME,
  melampittidae:       MELAMPITTIDAE_THEME,
  melanocharitidae:    MELANOCHARITIDAE_THEME,
  melanopareiidae:     MELANOPAREIIDAE_THEME,
  meliphagidae:        MELIPHAGIDAE_THEME,
  mesitornithidae:     MESITORNITHIDAE_THEME,
  mitrospingidae:      MITROSPINGIDAE_THEME,
  modulatricidae:      MODULATRICIDAE_THEME,
  mohoidae:            MOHOIDAE_THEME,
  mohouidae:           MOHOUIDAE_THEME,
  momotidae:           MOMOTIDAE_THEME,
  monarchidae:         MONARCHIDAE_THEME,
  musophagidae:        MUSOPHAGIDAE_THEME,
  neosittidae:         NEOSITTIDAE_THEME,
  nesospingidae:       NESOSPINGIDAE_THEME,
  nicatoridae:         NICATORIDAE_THEME,
  notiomystidae:       NOTIOMYSTIDAE_THEME,
  nyctibiidae:         NYCTIBIIDAE_THEME,
  oceanitidae:         OCEANITIDAE_THEME,
  odontophoridae:      ODONTOPHORIDAE_THEME,
  opisthocomidae:      OPISTHOCOMIDAE_THEME,
  oreoicidae:          OREOICIDAE_THEME,
  orthonychidae:       ORTHONYCHIDAE_THEME,
  pachycephalidae:     PACHYCEPHALIDAE_THEME,
  paradoxornithidae:   PARADOXORNITHIDAE_THEME,
  paramythiidae:       PARAMYTHIIDAE_THEME,
  pardalotidae:        PARDALOTIDAE_THEME,
  passerellidae:       PASSERELLIDAE_THEME,
  pedionomidae:        PEDIONOMIDAE_THEME,
  pellorneidae:        PELLORNEIDAE_THEME,
  petroicidae:         PETROICIDAE_THEME,
  peucedramidae:       PEUCEDRAMIDAE_THEME,
  phaenicophilidae:    PHAENICOPHILIDAE_THEME,
  phaethontidae:       PHAETHONTIDAE_THEME,
  philepittidae:       PHILEPITTIDAE_THEME,
  phoeniculidae:       PHOENICULIDAE_THEME,
  picathartidae:       PICATHARTIDAE_THEME,
  pipridae:            PIPRIDAE_THEME,
  pittidae:            PITTIDAE_THEME,
  pityriasidae:        PITYRIASIDAE_THEME,
  platylophidae:       PLATYLOPHIDAE_THEME,
  platysteiridae:      PLATYSTEIRIDAE_THEME,
  ploceidae:           PLOCEIDAE_THEME,
  pluvianellidae:      PLUVIANELLIDAE_THEME,
  pluvianidae:         PLUVIANIDAE_THEME,
  pnoepygidae:         PNOEPYGIDAE_THEME,
  podargidae:          PODARGIDAE_THEME,
  pomatostomidae:      POMATOSTOMIDAE_THEME,
  promeropidae:        PROMEROPIDAE_THEME,
  psittaculidae:       PSITTACULIDAE_THEME,
  psophiidae:          PSOPHIIDAE_THEME,
  psophodidae:         PSOPHODIDAE_THEME,
  ptiliogonatidae:     PTILIOGONATIDAE_THEME,
  rhagologidae:        RHAGOLOGIDAE_THEME,
  rheidae:             RHEIDAE_THEME,
  rhinocryptidae:      RHINOCRYPTIDAE_THEME,
  rhipiduridae:        RHIPIDURIDAE_THEME,
  rhodinocichlidae:    RHODINOCICHLIDAE_THEME,
  rhynochetidae:       RHYNOCHETIDAE_THEME,
  rostratulidae:       ROSTRATULIDAE_THEME,
  salpornithidae:      SALPORNITHIDAE_THEME,
  sapayoidae:          SAPAYOIDAE_THEME,
  sarothruridae:       SAROTHRURIDAE_THEME,
  scopidae:            SCOPIDAE_THEME,
  scotocercidae:       SCOTOCERCIDAE_THEME,
  semnornithidae:      SEMNORNITHIDAE_THEME,
  spindalidae:         SPINDALIDAE_THEME,
  steatornithidae:     STEATORNITHIDAE_THEME,
  stenostiridae:       STENOSTIRIDAE_THEME,
  strigopidae:         STRIGOPIDAE_THEME,
  struthionidae:       STRUTHIONIDAE_THEME,
  teretistridae:       TERETISTRIDAE_THEME,
  thamnophilidae:      THAMNOPHILIDAE_THEME,
  thinocoridae:        THINOCORIDAE_THEME,
  tichodromidae:       TICHODROMIDAE_THEME,
  timaliidae:          TIMALIIDAE_THEME,
  tinamidae:           TINAMIDAE_THEME,
  tityridae:           TITYRIDAE_THEME,
  todidae:             TODIDAE_THEME,
  trogonidae:          TROGONIDAE_THEME,
  turnicidae:          TURNICIDAE_THEME,
  urocynchramidae:     UROCYNCHRAMIDAE_THEME,
  vangidae:            VANGIDAE_THEME,
  viduidae:            VIDUIDAE_THEME,
  zeledoniidae:        ZELEDONIIDAE_THEME,
  zosteropidae:        ZOSTEROPIDAE_THEME,

  octopodidae:      OCTOPODIDAE_THEME,
  loliginidae:      LOLIGINIDAE_THEME,
  ommastrephidae:   OMMASTREPHIDAE_THEME,
  architeuthidae:   ARCHITEUTHIDAE_THEME,
  sepiidae:         SEPIIDAE_THEME,
  nautilidae:       NAUTILIDAE_THEME,
  vampyroteuthidae: VAMPYROTEUTHIDAE_THEME,
  spirulidae:       SPIRULIDAE_THEME,
  tachyglossidae:    TACHYGLOSSIDAE_THEME,
  cordylidae:        CORDYLIDAE_THEME,

  colubridae:       COLUBRIDAE_THEME,
  libellulidae:     LIBELLULIDAE_THEME,
  nothobranchiidae: NOTHOBRANCHIIDAE_THEME,

  lacertidae:       LACERTIDAE_THEME,
  anguidae:         ANGUIDAE_THEME,
  varanidae:        VARANIDAE_THEME,
  gekkonidae:       GEKKONIDAE_THEME,
  scincidae:        SCINCIDAE_THEME,
  agamidae:         AGAMIDAE_THEME,
  iguanidae:        IGUANIDAE_THEME,
  elapidae:         ELAPIDAE_THEME,
  pythonidae:       PYTHONIDAE_THEME,
  cheloniidae:      CHELONIIDAE_THEME,
  dermochelyidae:   DERMOCHELYIDAE_THEME,
  crocodylidae:     CROCODYLIDAE_THEME,
  alligatoridae:    ALLIGATORIDAE_THEME,
  sphenodontidae:   SPHENODONTIDAE_THEME,
  bufonidae:        BUFONIDAE_THEME,
  hylidae:          HYLIDAE_THEME,
  dendrobatidae:    DENDROBATIDAE_THEME,
  microhylidae:     MICROHYLIDAE_THEME,
  plethodontidae:   PLETHODONTIDAE_THEME,
  ambystomatidae:   AMBYSTOMATIDAE_THEME,
  cryptobranchidae: CRYPTOBRANCHIDAE_THEME,
  proteidae:        PROTEIDAE_THEME,
  caeciliidae:      CAECILIIDAE_THEME,
  theraphosidae:  THERAPHOSIDAE_THEME,
  salticidae:     SALTICIDAE_THEME,
  araneidae:      ARANEIDAE_THEME,
  theridiidae:    THERIDIIDAE_THEME,
  lycosidae:      LYCOSIDAE_THEME,
  sicariidae:     SICARIIDAE_THEME,
  atracidae:      ATRACIDAE_THEME,
  buthidae:       BUTHIDAE_THEME,
  scorpionidae:   SCORPIONIDAE_THEME,
  asteriidae:     ASTERIIDAE_THEME,
  echinidae:      ECHINIDAE_THEME,
  holothuriidae:  HOLOTHURIIDAE_THEME,

  scyliorhinidae: SCYLORHINIDAE_THEME,
  dasyatidae:     DASYATIDAE_THEME,
  labridae:       LABRIDAE_THEME,
  syngnathidae:   SYNGNATHIDAE_THEME,
  carabidae:      CARABIDAE_THEME,
  chrysomelidae:  CHRYSOMELIDAE_THEME,
  agelenidae:     AGELENIDAE_THEME,
  pholcidae:      PHOLCIDAE_THEME,
  amphisbaenidae: AMPHISBAENIDAE_THEME,
  eublepharidae:  EUBLEPHARIDAE_THEME,

  formicidae:     FORMICIDAE_THEME,
  vespidae:       VESPIDAE_THEME,
  nymphalidae:    NYMPHALIDAE_THEME,
  cichlidae:      CICHLIDAE_THEME,
  scombridae:     SCOMBRIDAE_THEME,
  characidae:     CHARACIDAE_THEME,
  boidae:         BOIDAE_THEME,
  lamnidae:       LAMNIDAE_THEME,
  pipidae:        PIPIDAE_THEME,
  pelobatidae:    PELOBATIDAE_THEME,
  pleurobrachiidae: PLEUROBRACHIIDAE_THEME,
  mertensiidae:   MERTENSIIDAE_THEME,
  bolinopsidae:   BOLINOPSIDAE_THEME,
  cestidae:       CESTIDAE_THEME,
  coeloplanidae:  COELOPLANIDAE_THEME,
  beroidae:       BEROIDAE_THEME,
  "sertulariidae": hydrozoa_sertulariidae,
  "aglaopheniidae": hydrozoa_aglaopheniidae,
  "plumulariidae": hydrozoa_plumulariidae,
  "campanulariidae": hydrozoa_campanulariidae,
  "sertularellidae": hydrozoa_sertularellidae,
  "haleciidae": hydrozoa_haleciidae,
  "halopterididae": hydrozoa_halopterididae,
  "symplectoscyphidae": hydrozoa_symplectoscyphidae,
  "eirenidae": hydrozoa_eirenidae,
  "lafoeidae": hydrozoa_lafoeidae,
  "zygophylacidae": hydrozoa_zygophylacidae,
  "hebellidae": hydrozoa_hebellidae,
  "kirchenpaueriidae": hydrozoa_kirchenpaueriidae,
  "aequoreidae": hydrozoa_aequoreidae,
  "lovenellidae": hydrozoa_lovenellidae,
  "campanulinidae": hydrozoa_campanulinidae,
  "syntheciidae": hydrozoa_syntheciidae,
  "laodiceidae": hydrozoa_laodiceidae,
  "gonaxiidae": hydrozoa_gonaxiidae,
  "schizotrichidae": hydrozoa_schizotrichidae,
  "phylactothecidae": hydrozoa_phylactothecidae,
  "staurothecidae": hydrozoa_staurothecidae,
  "mitrocomidae": hydrozoa_mitrocomidae,
  "malagazziidae": hydrozoa_malagazziidae,
  "thyroscyphidae": hydrozoa_thyroscyphidae,
  "tiarannidae": hydrozoa_tiarannidae,
  "phialellidae": hydrozoa_phialellidae,
  "bonneviellidae": hydrozoa_bonneviellidae,
  "tiaropsidae": hydrozoa_tiaropsidae,
  "melicertidae": hydrozoa_melicertidae,
  "dipleurosomatidae": hydrozoa_dipleurosomatidae,
  "cirrholoveniidae": hydrozoa_cirrholoveniidae,
  "octocannoididae": hydrozoa_octocannoididae,
  "lineolariidae": hydrozoa_lineolariidae,
  "orchistomatidae": hydrozoa_orchistomatidae,
  "sugiuridae": hydrozoa_sugiuridae,
  "teclaiidae": hydrozoa_teclaiidae,
  "clathrozoidae": hydrozoa_clathrozoidae,
  "wuvulidae": hydrozoa_wuvulidae,
  "blackfordiidae": hydrozoa_blackfordiidae,
  "barcinidae": hydrozoa_barcinidae,
  "palaequoreidae": hydrozoa_palaequoreidae,
  "phialuciidae": hydrozoa_phialuciidae,
  "plumaleciidae": hydrozoa_plumaleciidae,
  "stylasteridae": hydrozoa_stylasteridae,
  "hydractiniidae": hydrozoa_hydractiniidae,
  "bougainvilliidae": hydrozoa_bougainvilliidae,
  "pandeidae": hydrozoa_pandeidae,
  "corynidae": hydrozoa_corynidae,
  "corymorphidae": hydrozoa_corymorphidae,
  "eudendriidae": hydrozoa_eudendriidae,
  "tubulariidae": hydrozoa_tubulariidae,
  "hydridae": hydrozoa_hydridae,
  "zancleidae": hydrozoa_zancleidae,
  "bythotiaridae": hydrozoa_bythotiaridae,
  "oceaniidae": hydrozoa_oceaniidae,
  "milleporidae": hydrozoa_milleporidae,
  "cytaeididae": hydrozoa_cytaeididae,
  "candelabridae": hydrozoa_candelabridae,
  "cladonematidae": hydrozoa_cladonematidae,
  "rathkeidae": hydrozoa_rathkeidae,
  "protiaridae": hydrozoa_protiaridae,
  "proboscidactylidae": hydrozoa_proboscidactylidae,
  "ptilocodiidae": hydrozoa_ptilocodiidae,
  "moerisiidae": hydrozoa_moerisiidae,
  "sphaerocorynidae": hydrozoa_sphaerocorynidae,
  "solanderiidae": hydrozoa_solanderiidae,
  "cladocorynidae": hydrozoa_cladocorynidae,
  "zancleopsidae": hydrozoa_zancleopsidae,
  "hydrocorynidae": hydrozoa_hydrocorynidae,
  "australomedusidae": hydrozoa_australomedusidae,
  "axoporidae": hydrozoa_axoporidae,
  "pennariidae": hydrozoa_pennariidae,
  "rosalindidae": hydrozoa_rosalindidae,
  "teissieridae": hydrozoa_teissieridae,
  "hydrichthyidae": hydrozoa_hydrichthyidae,
  "magapiidae": hydrozoa_magapiidae,
  "margelopsidae": hydrozoa_margelopsidae,
  "eucodoniidae": hydrozoa_eucodoniidae,
  "porpitidae": hydrozoa_porpitidae,
  "halimedusidae": hydrozoa_halimedusidae,
  "acaulidae": hydrozoa_acaulidae,
  "protohydridae": hydrozoa_protohydridae,
  "clathrozoellidae": hydrozoa_clathrozoellidae,
  "rhysiidae": hydrozoa_rhysiidae,
  "boreohydridae": hydrozoa_boreohydridae,
  "asyncorynidae": hydrozoa_asyncorynidae,
  "cordylophoridae": hydrozoa_cordylophoridae,
  "pteronemidae": hydrozoa_pteronemidae,
  "tricyclusidae": hydrozoa_tricyclusidae,
  "niobiidae": hydrozoa_niobiidae,
  "boeromedusidae": hydrozoa_boeromedusidae,
  "trichydridae": hydrozoa_trichydridae,
  "paracorynidae": hydrozoa_paracorynidae,
  "balellidae": hydrozoa_balellidae,
  "tubiclavoididae": hydrozoa_tubiclavoididae,
  "jeanbouilloniidae": hydrozoa_jeanbouilloniidae,
  "heterastridiidae": hydrozoa_heterastridiidae,
  "heterotentaculidae": hydrozoa_heterotentaculidae,
  "similiclavidae": hydrozoa_similiclavidae,
  "diphyidae": hydrozoa_diphyidae,
  "prayidae": hydrozoa_prayidae,
  "agalmatidae": hydrozoa_agalmatidae,
  "rhodaliidae": hydrozoa_rhodaliidae,
  "abylidae": hydrozoa_abylidae,
  "sphaeronectidae": hydrozoa_sphaeronectidae,
  "clausophyidae": hydrozoa_clausophyidae,
  "stephanomiidae": hydrozoa_stephanomiidae,
  "cordagalmatidae": hydrozoa_cordagalmatidae,
  "rhizophysidae": hydrozoa_rhizophysidae,
  "pyrostephidae": hydrozoa_pyrostephidae,
  "forskaliidae": hydrozoa_forskaliidae,
  "erennidae": hydrozoa_erennidae,
  "hippopodiidae": hydrozoa_hippopodiidae,
  "resomiidae": hydrozoa_resomiidae,
  "apolemiidae": hydrozoa_apolemiidae,
  "physophoridae": hydrozoa_physophoridae,
  "physaliidae": hydrozoa_physaliidae,
  "tottonophyidae": hydrozoa_tottonophyidae,
  "cuninidae": hydrozoa_cuninidae,
  "solmarisidae": hydrozoa_solmarisidae,
  "aeginidae": hydrozoa_aeginidae,
  "solmundaeginidae": hydrozoa_solmundaeginidae,
  "tetraplatiidae": hydrozoa_tetraplatiidae,
  "pseudaeginidae": hydrozoa_pseudaeginidae,
  "polypodiidae": hydrozoa_polypodiidae,
  "csiromedusidae": hydrozoa_csiromedusidae,
  "rhopalonematidae": hydrozoa_rhopalonematidae,
  "halicreatidae": hydrozoa_halicreatidae,
  "petasidae": hydrozoa_petasidae,
  "ptychogastriidae": hydrozoa_ptychogastriidae,
  "olindiidae": hydrozoa_olindiidae,
  "geryoniidae": hydrozoa_geryoniidae,
  "monobrachiidae": hydrozoa_monobrachiidae,
  "microhydrulidae": hydrozoa_microhydrulidae,
  "armorhydridae": hydrozoa_armorhydridae,
  "halammohydridae": hydrozoa_halammohydridae,
  "otohydridae": hydrozoa_otohydridae,
  "pentasmiliidae": hydrozoa_pentasmiliidae,
  "chondroplidae": hydrozoa_chondroplidae,
  "inocaulidae": hydrozoa_inocaulidae,
  "caryophylliidae": anthozoa_caryophylliidae,
  "merulinidae": anthozoa_merulinidae,
  "acroporidae": anthozoa_acroporidae,
  "thecosmiliidae": anthozoa_thecosmiliidae,
  "dendrophylliidae": anthozoa_dendrophylliidae,
  "poritidae": anthozoa_poritidae,
  "latomeandridae": anthozoa_latomeandridae,
  "faviidae": anthozoa_faviidae,
  "stylinidae": anthozoa_stylinidae,
  "flabellidae": anthozoa_flabellidae,
  "comoseridae": anthozoa_comoseridae,
  "turbinoliidae": anthozoa_turbinoliidae,
  "pocilloporidae": anthozoa_pocilloporidae,
  "oculinidae": anthozoa_oculinidae,
  "agariciidae": anthozoa_agariciidae,
  "meandrinidae": anthozoa_meandrinidae,
  "astrocoeniidae": anthozoa_astrocoeniidae,
  "thamnasteriidae": anthozoa_thamnasteriidae,
  "rhizangiidae": anthozoa_rhizangiidae,
  "rhipidogyridae": anthozoa_rhipidogyridae,
  "actinastreidae": anthozoa_actinastreidae,
  "lobophylliidae": anthozoa_lobophylliidae,
  "heterocoeniidae": anthozoa_heterocoeniidae,
  "cunnolitidae": anthozoa_cunnolitidae,
  "fungiidae": anthozoa_fungiidae,
  "stylophyllidae": anthozoa_stylophyllidae,
  "montlivaltiidae": anthozoa_montlivaltiidae,
  "euphylliidae": anthozoa_euphylliidae,
  "haplaraeidae": anthozoa_haplaraeidae,
  "montastraeidae": anthozoa_montastraeidae,
  "amphiastreidae": anthozoa_amphiastreidae,
  "dermosmiliidae": anthozoa_dermosmiliidae,
  "columastreidae": anthozoa_columastreidae,
  "reimaniphylliidae": anthozoa_reimaniphylliidae,
  "axosmiliidae": anthozoa_axosmiliidae,
  "cyathophoridae": anthozoa_cyathophoridae,
  "acrosmiliidae": anthozoa_acrosmiliidae,
  "micrabaciidae": anthozoa_micrabaciidae,
  "placosmiliidae": anthozoa_placosmiliidae,
  "actinacididae": anthozoa_actinacididae,
  "astrangiidae": anthozoa_astrangiidae,
  "deltocyathidae": anthozoa_deltocyathidae,
  "cladophylliidae": anthozoa_cladophylliidae,
  "synastraeidae": anthozoa_synastraeidae,
  "tropiastraeidae": anthozoa_tropiastraeidae,
  "calamophylliidae": anthozoa_calamophylliidae,
  "coryphylliidae": anthozoa_coryphylliidae,
  "fungiacyathidae": anthozoa_fungiacyathidae,
  "margarophylliidae": anthozoa_margarophylliidae,
  "cladocoridae": anthozoa_cladocoridae,
  "diploastraeidae": anthozoa_diploastraeidae,
  "plesiastreidae": anthozoa_plesiastreidae,
  "pamiroseriidae": anthozoa_pamiroseriidae,
  "plerogyridae": anthozoa_plerogyridae,
  "epismiliidae": anthozoa_epismiliidae,
  "pachyseridae": anthozoa_pachyseridae,
  "psammocoridae": anthozoa_psammocoridae,
  "pachyphylliidae": anthozoa_pachyphylliidae,
  "procyclolitidae": anthozoa_procyclolitidae,
  "felixaraeidae": anthozoa_felixaraeidae,
  "amphiastraeidae": anthozoa_amphiastraeidae,
  "agathiphylliidae": anthozoa_agathiphylliidae,
  "placophylliidae": anthozoa_placophylliidae,
  "conophylliidae": anthozoa_conophylliidae,
  "eugyridae": anthozoa_eugyridae,
  "zardinophyllidae": anthozoa_zardinophyllidae,
  "astraraeidae": anthozoa_astraraeidae,
  "astraeomorphidae": anthozoa_astraeomorphidae,
  "agatheliidae": anthozoa_agatheliidae,
  "coscinaraeidae": anthozoa_coscinaraeidae,
  "asteroseriidae": anthozoa_asteroseriidae,
  "gardineriidae": anthozoa_gardineriidae,
  "leptastreidae": anthozoa_leptastreidae,
  "oppelismiliidae": anthozoa_oppelismiliidae,
  "donacosmiliidae": anthozoa_donacosmiliidae,
  "guyniidae": anthozoa_guyniidae,
  "anthemiphylliidae": anthozoa_anthemiphylliidae,
  "protoheterastraeidae": anthozoa_protoheterastraeidae,
  "trochoidomeandridae": anthozoa_trochoidomeandridae,
  "solenocoeniidae": anthozoa_solenocoeniidae,
  "smilotrochiidae": anthozoa_smilotrochiidae,
  "phyllosmiliidae": anthozoa_phyllosmiliidae,
  "negoporitidae": anthozoa_negoporitidae,
  "intersmiliidae": anthozoa_intersmiliidae,
  "schizocyathidae": anthozoa_schizocyathidae,
  "archaeosmiliidae": anthozoa_archaeosmiliidae,
  "kobyastraeidae": anthozoa_kobyastraeidae,
  "cuifastraeidae": anthozoa_cuifastraeidae,
  "carolastraeidae": anthozoa_carolastraeidae,
  "oulastreidae": anthozoa_oulastreidae,
  "volzeiidae": anthozoa_volzeiidae,
  "opisthophyllidae": anthozoa_opisthophyllidae,
  "sylviellidae": anthozoa_sylviellidae,
  "stenocyathidae": anthozoa_stenocyathidae,
  "misistellidae": anthozoa_misistellidae,
  "hemiporitidae": anthozoa_hemiporitidae,
  "cycliphylliidae": anthozoa_cycliphylliidae,
  "andemantastraeidae": anthozoa_andemantastraeidae,
  "mussidae": anthozoa_mussidae,
  "parepismiliidae": anthozoa_parepismiliidae,
  "guembelastraeidae": anthozoa_guembelastraeidae,
  "pseudoturbinolidae": anthozoa_pseudoturbinolidae,
  "microsolenidae": anthozoa_microsolenidae,
  "hexapetalidae": anthozoa_hexapetalidae,
  "rayasmiliidae": anthozoa_rayasmiliidae,
  "smilostyliidae": anthozoa_smilostyliidae,
  "parasmiliidae": anthozoa_parasmiliidae,
  "rhipidastraeidae": anthozoa_rhipidastraeidae,
  "eckastraeidae": anthozoa_eckastraeidae,
  "gablonzeriidae": anthozoa_gablonzeriidae,
  "polystylidiidae": anthozoa_polystylidiidae,
  "numidiaphylliidae": anthozoa_numidiaphylliidae,
  "gigantostyliidae": anthozoa_gigantostyliidae,
  "ellipsosmiliidae": anthozoa_ellipsosmiliidae,
  "distichoflabellidae": anthozoa_distichoflabellidae,
  "curtoseriidae": anthozoa_curtoseriidae,
  "pachyphyllidae": anthozoa_pachyphyllidae,
  "andrazelliidae": anthozoa_andrazelliidae,
  "corbariastraeidae": anthozoa_corbariastraeidae,
  "anabaciidae": anthozoa_anabaciidae,
  "archeoanthophyllidae": anthozoa_archeoanthophyllidae,
  "nephtheidae": anthozoa_nephtheidae,
  "paramuriceidae": anthozoa_paramuriceidae,
  "sarcophytidae": anthozoa_sarcophytidae,
  "gorgoniidae": anthozoa_gorgoniidae,
  "xeniidae": anthozoa_xeniidae,
  "alcyoniidae": anthozoa_alcyoniidae,
  "plexauridae": anthozoa_plexauridae,
  "melithaeidae": anthozoa_melithaeidae,
  "clavulariidae": anthozoa_clavulariidae,
  "cladiellidae": anthozoa_cladiellidae,
  "siphonogorgiidae": anthozoa_siphonogorgiidae,
  "lemnaliadae": anthozoa_lemnaliadae,
  "astrogorgiidae": anthozoa_astrogorgiidae,
  "euplexauridae": anthozoa_euplexauridae,
  "tubiporidae": anthozoa_tubiporidae,
  "anthogorgiidae": anthozoa_anthogorgiidae,
  "capnellidae": anthozoa_capnellidae,
  "eunicellidae": anthozoa_eunicellidae,
  "pterogorgiidae": anthozoa_pterogorgiidae,
  "isididae": anthozoa_isididae,
  "nidaliidae": anthozoa_nidaliidae,
  "paralcyoniidae": anthozoa_paralcyoniidae,
  "plexaurellidae": anthozoa_plexaurellidae,
  "subergorgiidae": anthozoa_subergorgiidae,
  "keroeididae": anthozoa_keroeididae,
  "victorgorgiidae": anthozoa_victorgorgiidae,
  "sinulariidae": anthozoa_sinulariidae,
  "acrophytidae": anthozoa_acrophytidae,
  "cerveridae": anthozoa_cerveridae,
  "leptophytidae": anthozoa_leptophytidae,
  "incrustatidae": anthozoa_incrustatidae,
  "acrossotidae": anthozoa_acrossotidae,
  "carijoidae": anthozoa_carijoidae,
  "arulidae": anthozoa_arulidae,
  "nephthyigorgiidae": anthozoa_nephthyigorgiidae,
  "aquaumbridae": anthozoa_aquaumbridae,
  "scleracidae": anthozoa_scleracidae,
  "acanthoaxiidae": anthozoa_acanthoaxiidae,
  "malacacanthidae": anthozoa_malacacanthidae,
  "rosgorgiidae": anthozoa_rosgorgiidae,
  "taiaroidae": anthozoa_taiaroidae,
  "discophytidae": anthozoa_discophytidae,
  "skamnariidae": anthozoa_skamnariidae,
  "coelogorgiidae": anthozoa_coelogorgiidae,
  "corymbophytidae": anthozoa_corymbophytidae,
  "pseudonephtheidae": anthozoa_pseudonephtheidae,
  "waagenophyllidae": anthozoa_waagenophyllidae,
  "favositidae": anthozoa_favositidae,
  "petalaxidae": anthozoa_petalaxidae,
  "streptelasmatidae": anthozoa_streptelasmatidae,
  "durhaminidae": anthozoa_durhaminidae,
  "cerianthidae": anthozoa_cerianthidae,
  "lithostrotionidae": anthozoa_lithostrotionidae,
  "micheliniidae": anthozoa_micheliniidae,
  "aulophyllidae": anthozoa_aulophyllidae,
  "pachyporidae": anthozoa_pachyporidae,
  "phillipsastreidae": anthozoa_phillipsastreidae,
  "hapsiphyllidae": anthozoa_hapsiphyllidae,
  "plerophyllidae": anthozoa_plerophyllidae,
  "lophophyllidiidae": anthozoa_lophophyllidiidae,
  "cyathopsidae": anthozoa_cyathopsidae,
  "disphyllidae": anthozoa_disphyllidae,
  "kleopatrinidae": anthozoa_kleopatrinidae,
  "arachnactidae": anthozoa_arachnactidae,
  "auloporidae": anthozoa_auloporidae,
  "laccophyllidae": anthozoa_laccophyllidae,
  "alveolitidae": anthozoa_alveolitidae,
  "cyathophyllidae": anthozoa_cyathophyllidae,
  "polycoeliidae": anthozoa_polycoeliidae,
  "botrucnidiferidae": anthozoa_botrucnidiferidae,
  "tetraporellidae": anthozoa_tetraporellidae,
  "pentaphyllidae": anthozoa_pentaphyllidae,
  "ptenophyllidae": anthozoa_ptenophyllidae,
  "syringoporidae": anthozoa_syringoporidae,
  "cateniporidae": anthozoa_cateniporidae,
  "hadrophyllidae": anthozoa_hadrophyllidae,
  "antiphyllidae": anthozoa_antiphyllidae,
  "arachnophyllidae": anthozoa_arachnophyllidae,
  "endophyllidae": anthozoa_endophyllidae,
  "tryplasmatidae": anthozoa_tryplasmatidae,
  "bothrophyllidae": anthozoa_bothrophyllidae,
  "geyerophyllidae": anthozoa_geyerophyllidae,
  "kyphophyllidae": anthozoa_kyphophyllidae,
  "lophotichiidae": anthozoa_lophotichiidae,
  "syringophyllidae": anthozoa_syringophyllidae,
  "lophophyllidae": anthozoa_lophophyllidae,
  "multithecoporidae": anthozoa_multithecoporidae,
  "metriophyllidae": anthozoa_metriophyllidae,
  "axophyllidae": anthozoa_axophyllidae,
  "spongiomorphidae": anthozoa_spongiomorphidae,
  "verbeekiellidae": anthozoa_verbeekiellidae,
  "sinoporidae": anthozoa_sinoporidae,
  "cyathaxoniidae": anthozoa_cyathaxoniidae,
  "kepingophyllidae": anthozoa_kepingophyllidae,
  "heterophylliidae": anthozoa_heterophylliidae,
  "halysitidae": anthozoa_halysitidae,
  "entelophyllidae": anthozoa_entelophyllidae,
  "diffingiidae": anthozoa_diffingiidae,
  "agetolitidae": anthozoa_agetolitidae,
  "amplexidae": anthozoa_amplexidae,
  "zaphrentidae": anthozoa_zaphrentidae,
  "chonophyllidae": anthozoa_chonophyllidae,
  "expressophyllidae": anthozoa_expressophyllidae,
  "theciidae": anthozoa_theciidae,
  "cystiphyllidae": anthozoa_cystiphyllidae,
  "timorphyllidae": anthozoa_timorphyllidae,
  "roemeriidae": anthozoa_roemeriidae,
  "haimeidae": anthozoa_haimeidae,
  "spongophyllidae": anthozoa_spongophyllidae,
  "goniophyllidae": anthozoa_goniophyllidae,
  "pseudopavonidae": anthozoa_pseudopavonidae,
  "gorskyitidae": anthozoa_gorskyitidae,
  "stauriidae": anthozoa_stauriidae,
  "stringophyllidae": anthozoa_stringophyllidae,
  "lykophyllidae": anthozoa_lykophyllidae,
  "coenitidae": anthozoa_coenitidae,
  "palaeocyclidae": anthozoa_palaeocyclidae,
  "columnariidae": anthozoa_columnariidae,
  "lonsdaleiidae": anthozoa_lonsdaleiidae,
  "zaphrentoididae": anthozoa_zaphrentoididae,
  "mucophyllidae": anthozoa_mucophyllidae,
  "kodonophyllidae": anthozoa_kodonophyllidae,
  "protozaphrentidae": anthozoa_protozaphrentidae,
  "palaeacidae": anthozoa_palaeacidae,
  "cleistoporidae": anthozoa_cleistoporidae,
  "tetradiidae": anthozoa_tetradiidae,
  "endamplexidae": anthozoa_endamplexidae,
  "paliphyllidae": anthozoa_paliphyllidae,
  "calostylidae": anthozoa_calostylidae,
  "ekvasophyllidae": anthozoa_ekvasophyllidae,
  "tabulaconidae": anthozoa_tabulaconidae,
  "trachypsammidae": anthozoa_trachypsammidae,
  "lichenariidae": anthozoa_lichenariidae,
  "lambelasmatidae": anthozoa_lambelasmatidae,
  "paiutitubulitidae": anthozoa_paiutitubulitidae,
  "ketophyllidae": anthozoa_ketophyllidae,
  "pycnostylidae": anthozoa_pycnostylidae,
  "ptychophyllidae": anthozoa_ptychophyllidae,
  "paleocyclidae": anthozoa_paleocyclidae,
  "huadianophyllidae": anthozoa_huadianophyllidae,
  "mirandellidae": anthozoa_mirandellidae,
  "petraphyllidae": anthozoa_petraphyllidae,
  "koninckocariniidae": anthozoa_koninckocariniidae,
  "palaeosmiliidae": anthozoa_palaeosmiliidae,
  "auloheliidae": anthozoa_auloheliidae,
  "kilbuchophyllidae": anthozoa_kilbuchophyllidae,
  "kielcephyllidae": anthozoa_kielcephyllidae,
  "lindstroemiidae": anthozoa_lindstroemiidae,
  "schizophoritidae": anthozoa_schizophoritidae,
  "petraiidae": anthozoa_petraiidae,
  "syringolitidae": anthozoa_syringolitidae,
  "romingeriidae": anthozoa_romingeriidae,
  "uraliniidae": anthozoa_uraliniidae,
  "dorlodotidae": anthozoa_dorlodotidae,
  "pseudogorgiidae": anthozoa_pseudogorgiidae,
  "calceolidae": anthozoa_calceolidae,
  "fasciphyllidae": anthozoa_fasciphyllidae,
  "stereolasmatidae": anthozoa_stereolasmatidae,
  "parastriatoporidae": anthozoa_parastriatoporidae,
  "fletcheriellidae": anthozoa_fletcheriellidae,
  "holmophyllidae": anthozoa_holmophyllidae,
  "lyoporidae": anthozoa_lyoporidae,
  "neoroemeriidae": anthozoa_neoroemeriidae,
  "trachypsammiidae": anthozoa_trachypsammiidae,
  "pseudofavositidae": anthozoa_pseudofavositidae,
  "lamottiidae": anthozoa_lamottiidae,
  "plerodiffiidae": anthozoa_plerodiffiidae,
  "craspedophyllidae": anthozoa_craspedophyllidae,
  "halliidae": anthozoa_halliidae,
  "trachyporidae": anthozoa_trachyporidae,
  "digonophyllidae": anthozoa_digonophyllidae,
  "proheliolitidae": anthozoa_proheliolitidae,
  "ricordiidae": anthozoa_ricordiidae,
  "aurelianidae": anthozoa_aurelianidae,
  "exocoelactiidae": anthozoa_exocoelactiidae,
  "pennautlidae": anthozoa_pennautlidae,
  "cyclastraeidae": anthozoa_cyclastraeidae,
  "palaeofavosiporidae": anthozoa_palaeofavosiporidae,
  "kozlowskiocystiidae": anthozoa_kozlowskiocystiidae,
  "actinodiscidae": anthozoa_actinodiscidae,
  "anisophyllidae": anthozoa_anisophyllidae,
  "acervulariidae": anthozoa_acervulariidae,
  "vaughaniidae": anthozoa_vaughaniidae,
  "taeniolitidae": anthozoa_taeniolitidae,
  "eridophyllidae": anthozoa_eridophyllidae,
  "pachythecalidae": anthozoa_pachythecalidae,
  "acrophyllidae": anthozoa_acrophyllidae,
  "gerardiidae": anthozoa_gerardiidae,
  "ptychodactidae": anthozoa_ptychodactidae,
  "paractidae": anthozoa_paractidae,
  "ilyanthidae": anthozoa_ilyanthidae,
  "trochosmiliidae": anthozoa_trochosmiliidae,
  "pteroeididae": anthozoa_pteroeididae,
  "telestidae": anthozoa_telestidae,
  "pseudocladochomidae": anthozoa_pseudocladochomidae,
  "astrospiculariidae": anthozoa_astrospiculariidae,
  "briaridae": anthozoa_briaridae,
  "ainigmaptilidae": anthozoa_ainigmaptilidae,
  "plasmoporellidae": anthozoa_plasmoporellidae,
  "bethanyphyllidae": anthozoa_bethanyphyllidae,
  "pycnolithidae": anthozoa_pycnolithidae,
  "campophyllidae": anthozoa_campophyllidae,
  "distichophyllidae": anthozoa_distichophyllidae,
  "numidiaphyllidae": anthozoa_numidiaphyllidae,
  "amsdenoididae": anthozoa_amsdenoididae,
  "combophyllidae": anthozoa_combophyllidae,
  "tropiastreidae": anthozoa_tropiastreidae,
  "funginellidae": anthozoa_funginellidae,
  "heliastraeidae": anthozoa_heliastraeidae,
  "gardinariidae": anthozoa_gardinariidae,
  "eusmilidae": anthozoa_eusmilidae,
  "siderasteridae": anthozoa_siderasteridae,
  "alpinophylliidae": anthozoa_alpinophylliidae,
  "cyclophyllopsiidae": anthozoa_cyclophyllopsiidae,
  "carolastaeidae": anthozoa_carolastaeidae,
  "caryophyllidae": anthozoa_caryophyllidae,
  "lithophylliidae": anthozoa_lithophylliidae,
  "waiparaconidae": anthozoa_waiparaconidae,
  "pseudocladochonidae": anthozoa_pseudocladochonidae,
  "arachnanthidae": anthozoa_arachnanthidae,
  "mycophyllidae": anthozoa_mycophyllidae,
  "sterictophyllidae": anthozoa_sterictophyllidae,
  "muriceidae": anthozoa_muriceidae,
  "pteroididae": anthozoa_pteroididae,
  "pyrgiidae": anthozoa_pyrgiidae,
  "periphaceloporidae": anthozoa_periphaceloporidae,
  "maasellidae": anthozoa_maasellidae,
  "coccoserididae": anthozoa_coccoserididae,
  "thecostegitidae": anthozoa_thecostegitidae,
  "porastriatoporidae": anthozoa_porastriatoporidae,
  "pyrigiidae": anthozoa_pyrigiidae,
  "billingsariidae": anthozoa_billingsariidae,
  "centristelidae": anthozoa_centristelidae,
  "paleoalveolitidae": anthozoa_paleoalveolitidae,
  "cyrtophyllidae": anthozoa_cyrtophyllidae,
  "endotheciidae": anthozoa_endotheciidae,
  "cothoniidae": anthozoa_cothoniidae,
  "kiziliidae": anthozoa_kiziliidae,
  "adamanophyllidae": anthozoa_adamanophyllidae,
  "multisoleniidae": anthozoa_multisoleniidae,
  "chonostegitidae": anthozoa_chonostegitidae,
  "lipoporidae": anthozoa_lipoporidae,
  "septodaeidae": anthozoa_septodaeidae,
  "neocolumnariidae": anthozoa_neocolumnariidae,
  "bajgoliidae": anthozoa_bajgoliidae,
  "fletcheriidae": anthozoa_fletcheriidae,
  "ditoecholasmatidae": anthozoa_ditoecholasmatidae,
  "aphrophyllidae": anthozoa_aphrophyllidae,
  "eupsammidae": anthozoa_eupsammidae,
  "pinacophyllidae": anthozoa_pinacophyllidae,
  "haplareidae": anthozoa_haplareidae,
  "isastraeidae": anthozoa_isastraeidae,
  "margarophyllidae": anthozoa_margarophyllidae,
  "protoheterstraeidae": anthozoa_protoheterstraeidae,
  "phyllocoeniidae": anthozoa_phyllocoeniidae,
  "euhellidae": anthozoa_euhellidae,
  "mitrodendronidae": anthozoa_mitrodendronidae,
  "antheidae": anthozoa_antheidae,
  "diploastreidae": anthozoa_diploastreidae,
  "semperinidae": anthozoa_semperinidae,
  "kophobelemnonidae": anthozoa_kophobelemnonidae,
  "evenkiellidae": anthozoa_evenkiellidae,
  "microbaciidae": anthozoa_microbaciidae,
  "cyathactidae": anthozoa_cyathactidae,
  "tropiphyllidae": anthozoa_tropiphyllidae,
  "tryplasmidae": anthozoa_tryplasmidae,
  "thamnoporidae": anthozoa_thamnoporidae,
  "kophobelemnoidae": anthozoa_kophobelemnoidae,
  "chrysogorgidae": anthozoa_chrysogorgidae,
  "dendrogyriidae": anthozoa_dendrogyriidae,
  "distichophylliidae": anthozoa_distichophylliidae,
  "clisiophyllidae": anthozoa_clisiophyllidae,
  "romanophyllidae": anthozoa_romanophyllidae,
  "bogambirolitidae": anthozoa_bogambirolitidae,
  "vojnovskytesidae": anthozoa_vojnovskytesidae,
  "hawaidae": anthozoa_hawaidae,
  "madreporidae": anthozoa_madreporidae,
  "gerardidae": anthozoa_gerardidae,
  "primnozoanthidae": anthozoa_primnozoanthidae,
  "parasitozoanthidae": anthozoa_parasitozoanthidae,
  "dasmiidae": anthozoa_dasmiidae,
  "pruvostastraeidae": anthozoa_pruvostastraeidae,
  "cyclophyllopsidae": anthozoa_cyclophyllopsidae,
  "thamnasterioidae": anthozoa_thamnasterioidae,
  "innaporidae": anthozoa_innaporidae,
  "angoporidae": anthozoa_angoporidae,
  "dimorphophylliidae": anthozoa_dimorphophylliidae,
  "sinopathidae": anthozoa_sinopathidae,
  "latomaeandridae": anthozoa_latomaeandridae,
  "pleurosmiliidae": anthozoa_pleurosmiliidae,
  "aplosmiliidae": anthozoa_aplosmiliidae,
  "ellisitidae": anthozoa_ellisitidae,
  "acrocyathidae": anthozoa_acrocyathidae,
  "flosmarinidae": anthozoa_flosmarinidae,
  "brachiphylliidae": anthozoa_brachiphylliidae,
  "retiophylliidae": anthozoa_retiophylliidae,
  "thamnastraeidae": anthozoa_thamnastraeidae,
  "reimaniphyllidae": anthozoa_reimaniphyllidae,
  "symphylliidae": anthozoa_symphylliidae,
  "ceratocorallia": anthozoa_ceratocorallia,
  "gyrophyllidae": anthozoa_gyrophyllidae,
  "primnoidae": anthozoa_primnoidae,
  "ellisellidae": anthozoa_ellisellidae,
  "pennatulidae": anthozoa_pennatulidae,
  "chrysogorgiidae": anthozoa_chrysogorgiidae,
  "coralliidae": anthozoa_coralliidae,
  "mopseidae": anthozoa_mopseidae,
  "virgulariidae": anthozoa_virgulariidae,
  "keratoisididae": anthozoa_keratoisididae,
  "veretillidae": anthozoa_veretillidae,
  "helioporidae": anthozoa_helioporidae,
  "umbellulidae": anthozoa_umbellulidae,
  "kophobelemnidae": anthozoa_kophobelemnidae,
  "sarcodictyonidae": anthozoa_sarcodictyonidae,
  "renillidae": anthozoa_renillidae,
  "ifalukellidae": anthozoa_ifalukellidae,
  "spongiodermidae": anthozoa_spongiodermidae,
  "briareidae": anthozoa_briareidae,
  "parisididae": anthozoa_parisididae,
  "aulopsammiidae": anthozoa_aulopsammiidae,
  "parasphaerascleridae": anthozoa_parasphaerascleridae,
  "scleroptilidae": anthozoa_scleroptilidae,
  "protoptilidae": anthozoa_protoptilidae,
  "echinoptilidae": anthozoa_echinoptilidae,
  "anthoptilidae": anthozoa_anthoptilidae,
  "balticinidae": anthozoa_balticinidae,
  "stachyptilidae": anthozoa_stachyptilidae,
  "erythropodiidae": anthozoa_erythropodiidae,
  "funiculinidae": anthozoa_funiculinidae,
  "dendrobrachiidae": anthozoa_dendrobrachiidae,
  "cornulariidae": anthozoa_cornulariidae,
  "chunellidae": anthozoa_chunellidae,
  "chelidonisididae": anthozoa_chelidonisididae,
  "pleurogorgiidae": anthozoa_pleurogorgiidae,
  "ideogorgiidae": anthozoa_ideogorgiidae,
  "pseudumbellulidae": anthozoa_pseudumbellulidae,
  "isidoidae": anthozoa_isidoidae,
  "actiniidae": anthozoa_actiniidae,
  "hormathiidae": anthozoa_hormathiidae,
  "edwardsiidae": anthozoa_edwardsiidae,
  "sagartiidae": anthozoa_sagartiidae,
  "andvakiidae": anthozoa_andvakiidae,
  "actinostolidae": anthozoa_actinostolidae,
  "amphianthidae": anthozoa_amphianthidae,
  "halcampidae": anthozoa_halcampidae,
  "aiptasiidae": anthozoa_aiptasiidae,
  "sicyonidae": anthozoa_sicyonidae,
  "peachiidae": anthozoa_peachiidae,
  "haloclavidae": anthozoa_haloclavidae,
  "halcampoididae": anthozoa_halcampoididae,
  "kadosactinidae": anthozoa_kadosactinidae,
  "isanthidae": anthozoa_isanthidae,
  "halcuriidae": anthozoa_halcuriidae,
  "phymanthidae": anthozoa_phymanthidae,
  "diadumenidae": anthozoa_diadumenidae,
  "condylanthidae": anthozoa_condylanthidae,
  "aliciidae": anthozoa_aliciidae,
  "minyadidae": anthozoa_minyadidae,
  "stichodactylidae": anthozoa_stichodactylidae,
  "actinodendridae": anthozoa_actinodendridae,
  "haliactinidae": anthozoa_haliactinidae,
  "phelliidae": anthozoa_phelliidae,
  "actinernidae": anthozoa_actinernidae,
  "boloceroididae": anthozoa_boloceroididae,
  "thalassianthidae": anthozoa_thalassianthidae,
  "bathyphelliidae": anthozoa_bathyphelliidae,
  "actinoscyphiidae": anthozoa_actinoscyphiidae,
  "capneidae": anthozoa_capneidae,
  "acontiophoridae": anthozoa_acontiophoridae,
  "metridiidae": anthozoa_metridiidae,
  "aiptasiomorphidae": anthozoa_aiptasiomorphidae,
  "octineonidae": anthozoa_octineonidae,
  "anthosactinidae": anthozoa_anthosactinidae,
  "liponematidae": anthozoa_liponematidae,
  "isactinernidae": anthozoa_isactinernidae,
  "harenactidae": anthozoa_harenactidae,
  "nemanthidae": anthozoa_nemanthidae,
  "oractiidae": anthozoa_oractiidae,
  "iosactinidae": anthozoa_iosactinidae,
  "galatheanthemidae": anthozoa_galatheanthemidae,
  "preactiniidae": anthozoa_preactiniidae,
  "limnactiniidae": anthozoa_limnactiniidae,
  "homostichanthidae": anthozoa_homostichanthidae,
  "gonactiniidae": anthozoa_gonactiniidae,
  "ptychodactinidae": anthozoa_ptychodactinidae,
  "exocoelactinidae": anthozoa_exocoelactinidae,
  "polyopidae": anthozoa_polyopidae,
  "haliplanellidae": anthozoa_haliplanellidae,
  "sagartiomorphidae": anthozoa_sagartiomorphidae,
  "nevadneidae": anthozoa_nevadneidae,
  "andresiidae": anthozoa_andresiidae,
  "heteractidae": anthozoa_heteractidae,
  "heteranthidae": anthozoa_heteranthidae,
  "sarcophinanthidae": anthozoa_sarcophinanthidae,
  "antheomorphidae": anthozoa_antheomorphidae,
  "ostiactinidae": anthozoa_ostiactinidae,
  "acricoactinidae": anthozoa_acricoactinidae,
  "spongiactinidae": anthozoa_spongiactinidae,
  "relicanthidae": anthozoa_relicanthidae,
  "halcampulactidae": anthozoa_halcampulactidae,
  "tetracoelactinidae": anthozoa_tetracoelactinidae,
  "mackenziidae": anthozoa_mackenziidae,
  "sphenopidae": anthozoa_sphenopidae,
  "zoanthidae": anthozoa_zoanthidae,
  "parazoanthidae": anthozoa_parazoanthidae,
  "epizoanthidae": anthozoa_epizoanthidae,
  "hydrozoanthidae": anthozoa_hydrozoanthidae,
  "neozoanthidae": anthozoa_neozoanthidae,
  "abyssoanthidae": anthozoa_abyssoanthidae,
  "microzoanthidae": anthozoa_microzoanthidae,
  "nanozoanthidae": anthozoa_nanozoanthidae,
  "antipathidae": anthozoa_antipathidae,
  "schizopathidae": anthozoa_schizopathidae,
  "aphanipathidae": anthozoa_aphanipathidae,
  "myriopathidae": anthozoa_myriopathidae,
  "cladopathidae": anthozoa_cladopathidae,
  "stylopathidae": anthozoa_stylopathidae,
  "leiopathidae": anthozoa_leiopathidae,
  "corallimorphidae": anthozoa_corallimorphidae,
  "discosomidae": anthozoa_discosomidae,
  "sideractinidae": anthozoa_sideractinidae,
  "ricordeidae": anthozoa_ricordeidae,
  "heliolitidae": anthozoa_heliolitidae,
  "stelliporellidae": anthozoa_stelliporellidae,
  "palaeoporitidae": anthozoa_palaeoporitidae,
  "plasmoporidae": anthozoa_plasmoporidae,
  "sibiriolitidae": anthozoa_sibiriolitidae,
  "pseudoplasmoporidae": anthozoa_pseudoplasmoporidae,

  "chaetodermatidae": caudofoveata_chaetodermatidae,
  "prochaetodermatidae": caudofoveata_prochaetodermatidae,
  "limifossoridae": caudofoveata_limifossoridae,
  "tryblidiidae": monoplacophora_tryblidiidae,
  "proplinidae": monoplacophora_proplinidae,
  "archaeophialidae": monoplacophora_archaeophialidae,
  "peelipilinidae": monoplacophora_peelipilinidae,
  "cyrtolitidae": monoplacophora_cyrtolitidae,
  "carcassonnellidae": monoplacophora_carcassonnellidae,
  "cyrtonellidae": monoplacophora_cyrtonellidae,
  "hypseloconidae": monoplacophora_hypseloconidae,
  "kirengellidae": monoplacophora_kirengellidae,
  "metoptomatidae": monoplacophora_metoptomatidae,
  "palaeacmaeidae": monoplacophora_palaeacmaeidae,
  "shelbyoceridae": monoplacophora_shelbyoceridae,
  "cyclocyrtonellidae": monoplacophora_cyclocyrtonellidae,
  "multifariidae": monoplacophora_multifariidae,
  "neopilinidae": monoplacophora_neopilinidae,
  "dentaliidae": scaphopoda_dentaliidae,
  "gadilinidae": scaphopoda_gadilinidae,
  "laevidentaliidae": scaphopoda_laevidentaliidae,
  "fustiariidae": scaphopoda_fustiariidae,
  "prodentaliidae": scaphopoda_prodentaliidae,
  "rhabdidae": scaphopoda_rhabdidae,
  "calliodentaliidae": scaphopoda_calliodentaliidae,
  "anulidentaliidae": scaphopoda_anulidentaliidae,
  "omniglyptidae": scaphopoda_omniglyptidae,
  "gadilidae": scaphopoda_gadilidae,
  "entalinidae": scaphopoda_entalinidae,
  "pulsellidae": scaphopoda_pulsellidae,
  "wemersoniellidae": scaphopoda_wemersoniellidae,
  "loxoporidae": scaphopoda_loxoporidae,
  "cadulidae": scaphopoda_cadulidae,
  "baltodentaliidae": scaphopoda_baltodentaliidae,
  "episiphonidae": scaphopoda_episiphonidae,};

export function getThemeForNode(node: TaxonNode): ColorTheme {
  if (node.familySlug && COLOR_REGISTRY[node.familySlug]) {
    return COLOR_REGISTRY[node.familySlug];
  }
  return PORTAL_THEME;
}

export { PORTAL_THEME };
