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

const CISTICOLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cetti's Warblers": "#a06848", "Cisticolas": "#8a8870", "Prinias": "#a89860" }, breedGroupColor: "#a08058", hybridColor: "#c8a878" };

const SPHENISCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Great Penguins": "#607888", "Brush-tailed Penguins": "#4a7080", "Crested Penguins": "#c88838", "Yellow-eyed Penguins": "#c8a840", "Little Penguins": "#5888a0", "Banded Penguins": "#3a6070" }, breedGroupColor: "#4a6878", hybridColor: "#7898a8" };

const TROCHILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bee Hummingbirds": "#30a060", "Hermits": "#a08850", "Giants & Topazes": "#c85828", "Mountain Gems": "#2870a0", "Brilliants": "#6848a8", "Emeralds": "#20a050", "Mangos & Caribs": "#c82038" }, breedGroupColor: "#40a060", hybridColor: "#70c888" };

const PHOENICOPTERIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Greater Flamingos": "#e87868", "Lesser Flamingos": "#e86050", "Andean Flamingos": "#e8a080" }, breedGroupColor: "#e87060", hybridColor: "#f0a898" };

const PROCELLARIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Fulmars & Giant Petrels": "#a0a0a0", "Shearwaters": "#588098", "Gadfly Petrels": "#7898a8", "Prions & Blue Petrels": "#6890a8" }, breedGroupColor: "#789098", hybridColor: "#98b0b8" };

const HYDROBATIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Storm Petrels": "#3a4048" }, breedGroupColor: "#303840", hybridColor: "#5a6870" };

const POLIOPTILIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Gnatcatchers": "#6888a8", "Gnatwrens": "#8a7858" }, breedGroupColor: "#6888a8", hybridColor: "#90a8c0" };

const PELECANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Pelicans": "#e8d8a8" }, breedGroupColor: "#d8c898", hybridColor: "#f0e8c8" };

const OTIDIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Great Bustards": "#c8a060", "Houbara Bustards": "#d0b080", "Little Bustards": "#a89870" }, breedGroupColor: "#c0a070", hybridColor: "#d8c098" };

const MEROPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bee-eaters": "#30b870" }, breedGroupColor: "#30a860", hybridColor: "#60d090" };

const CORACIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Rollers": "#2088c8", "Broad-billed Rollers": "#6870a8" }, breedGroupColor: "#2880b8", hybridColor: "#60a8d8" };

const COLUBRIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "European Colubrids": "#5a8040", "New World Ratsnakes": "#a07030", "Asian Colubrids": "#708850", "King Snakes": "#e83820" }, breedGroupColor: "#6a7040", hybridColor: "#c89030" };
const LACERTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sand Lizards": "#9ab050", "European Wall Lizards": "#78a040", "Green Lizards": "#50a030" }, breedGroupColor: "#88a048", hybridColor: "#b8c870" };
const ANGUIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Slow Worms": "#c87838", "Glass Lizards": "#a86028", "Alligator Lizards": "#8a5020" }, breedGroupColor: "#b86830", hybridColor: "#d89050" };
const VARANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Monitor Lizards": "#5a6840" }, breedGroupColor: "#4a5830", hybridColor: "#7a8858" };
const GEKKONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "House Geckos": "#484838", "Day Geckos": "#389858", "Leaf-tailed Geckos": "#706848", "Ground Geckos": "#a89868" }, breedGroupColor: "#587848", hybridColor: "#88a870" };
const SCINCIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Blue-tongued Skinks": "#5878a0", "Five-lined Skinks": "#4870a8", "Ground Skinks": "#8a7848", "Sandfish": "#d0b870" }, breedGroupColor: "#6880a0", hybridColor: "#90a8c0" };
const AGAMIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Bearded Dragons": "#c88040", "Agamas": "#e86820", "Flying Dragons": "#6898c0", "Thorny Devils": "#c07028" }, breedGroupColor: "#d07030", hybridColor: "#e8a860" };
const IGUANIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Green Iguanas": "#408830", "Marine Iguanas": "#2a3828", "Desert Iguanas": "#c8a850", "Spiny-tailed Iguanas": "#607840" }, breedGroupColor: "#507838", hybridColor: "#80b060" };
const ELAPIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Cobras & Mambas": "#2a2828", "Sea Snakes": "#206080", "Taipans & Brown Snakes": "#e8b820", "Kraits": "#404830" }, breedGroupColor: "#383028", hybridColor: "#807858" };
const PYTHONIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Asian Pythons": "#786040", "African Pythons": "#6a5030", "Australian Pythons": "#907850" }, breedGroupColor: "#806848", hybridColor: "#a09068" };
const CHELONIIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Sea Turtles": "#3a8878" }, breedGroupColor: "#2a7868", hybridColor: "#5aa898" };
const DERMOCHELYIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Leatherback": "#2a3870" }, breedGroupColor: "#1a2860", hybridColor: "#4a5890" };
const CROCODYLIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "True Crocodiles": "#3a5030", "Gharial": "#4a6840" }, breedGroupColor: "#304828", hybridColor: "#5a7848" };
const ALLIGATORIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Alligators": "#4a6038", "Caimans": "#3a5028" }, breedGroupColor: "#405830", hybridColor: "#608050" };
const SPHENODONTIDAE_THEME: ColorTheme = { subfamilyColors: {}, lineageColors: { "Tuatara": "#6a7840" }, breedGroupColor: "#5a6830", hybridColor: "#8a9858" };

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
  colubridae:       COLUBRIDAE_THEME,
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
};

export function getThemeForNode(node: TaxonNode): ColorTheme {
  if (node.familySlug && COLOR_REGISTRY[node.familySlug]) {
    return COLOR_REGISTRY[node.familySlug];
  }
  return PORTAL_THEME;
}

export { PORTAL_THEME };
