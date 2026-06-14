export interface CaprineBreed {
  id: string;
  name: string;
  group: string;
  species: "sheep" | "goat";
  origin: string;
}

export const SHEEP_GROUPS = ["Wool", "Meat", "Dairy"] as const;
export const GOAT_GROUPS = ["Dairy", "Meat", "Fiber", "Miniature"] as const;

export const SHEEP_BREEDS: CaprineBreed[] = [
  // Wool
  { id: "merino",              name: "Merino",              group: "Wool",   species: "sheep", origin: "Spain" },
  { id: "corriedale",          name: "Corriedale",          group: "Wool",   species: "sheep", origin: "New Zealand" },
  { id: "lincoln",             name: "Lincoln",             group: "Wool",   species: "sheep", origin: "England" },
  { id: "romney",              name: "Romney",              group: "Wool",   species: "sheep", origin: "England" },
  { id: "rambouillet",         name: "Rambouillet",         group: "Wool",   species: "sheep", origin: "France" },
  { id: "border-leicester",    name: "Border Leicester",    group: "Wool",   species: "sheep", origin: "England" },
  { id: "bluefaced-leicester", name: "Bluefaced Leicester", group: "Wool",   species: "sheep", origin: "England" },
  // Meat
  { id: "suffolk",             name: "Suffolk",             group: "Meat",   species: "sheep", origin: "England" },
  { id: "dorper",              name: "Dorper",              group: "Meat",   species: "sheep", origin: "South Africa" },
  { id: "hampshire",           name: "Hampshire",           group: "Meat",   species: "sheep", origin: "England" },
  { id: "texel",               name: "Texel",               group: "Meat",   species: "sheep", origin: "Netherlands" },
  { id: "cheviot",             name: "Cheviot",             group: "Meat",   species: "sheep", origin: "Scotland" },
  { id: "dorset",              name: "Dorset",              group: "Meat",   species: "sheep", origin: "England" },
  { id: "ile-de-france",       name: "Île-de-France",       group: "Meat",   species: "sheep", origin: "France" },
  // Dairy
  { id: "east-friesian",       name: "East Friesian",       group: "Dairy",  species: "sheep", origin: "Germany" },
  { id: "awassi",              name: "Awassi",              group: "Dairy",  species: "sheep", origin: "Middle East" },
  { id: "lacaune",             name: "Lacaune",             group: "Dairy",  species: "sheep", origin: "France" },
];

export const GOAT_BREEDS: CaprineBreed[] = [
  // Dairy
  { id: "nubian",              name: "Nubian",              group: "Dairy",    species: "goat", origin: "England / Africa" },
  { id: "alpine",              name: "Alpine",              group: "Dairy",    species: "goat", origin: "France" },
  { id: "saanen",              name: "Saanen",              group: "Dairy",    species: "goat", origin: "Switzerland" },
  { id: "toggenburg",         name: "Toggenburg",          group: "Dairy",    species: "goat", origin: "Switzerland" },
  { id: "lamancha",            name: "LaMancha",            group: "Dairy",    species: "goat", origin: "United States" },
  { id: "oberhasli",           name: "Oberhasli",           group: "Dairy",    species: "goat", origin: "Switzerland" },
  // Meat
  { id: "boer",                name: "Boer",                group: "Meat",     species: "goat", origin: "South Africa" },
  { id: "kiko",                name: "Kiko",                group: "Meat",     species: "goat", origin: "New Zealand" },
  { id: "savanna",             name: "Savanna",             group: "Meat",     species: "goat", origin: "South Africa" },
  // Fiber
  { id: "angora",              name: "Angora",              group: "Fiber",    species: "goat", origin: "Turkey" },
  { id: "cashmere",            name: "Cashmere",            group: "Fiber",    species: "goat", origin: "Asia" },
  // Miniature
  { id: "nigerian-dwarf",      name: "Nigerian Dwarf",      group: "Miniature",species: "goat", origin: "West Africa" },
  { id: "pygmy",               name: "Pygmy",               group: "Miniature",species: "goat", origin: "West Africa" },
];
