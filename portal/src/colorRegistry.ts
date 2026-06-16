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
  motacillidae:    MOTACILLIDAE_THEME,
  hirundinidae:    HIRUNDINIDAE_THEME,
  phylloscopidae:  PHYLLOSCOPIDAE_THEME,
  laridae:         LARIDAE_THEME,
  ardeidae:        ARDEIDAE_THEME,
};

export function getThemeForNode(node: TaxonNode): ColorTheme {
  if (node.familySlug && COLOR_REGISTRY[node.familySlug]) {
    return COLOR_REGISTRY[node.familySlug];
  }
  return PORTAL_THEME;
}

export { PORTAL_THEME };
