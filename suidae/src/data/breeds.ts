export interface PigBreed {
  id: string;
  name: string;
  group: string;
  origin: string;
}

export const PIG_GROUPS = ["Meat", "Lard", "Heritage", "Miniature"] as const;

export const PIG_BREEDS: PigBreed[] = [
  // Meat
  { id: "large-white",    name: "Large White",             group: "Meat",     origin: "England" },
  { id: "landrace",       name: "Landrace",                group: "Meat",     origin: "Denmark" },
  { id: "duroc",          name: "Duroc",                   group: "Meat",     origin: "United States" },
  { id: "hampshire",      name: "Hampshire",               group: "Meat",     origin: "England" },
  { id: "pietrain",       name: "Pietrain",                group: "Meat",     origin: "Belgium" },
  { id: "berkshire",      name: "Berkshire",               group: "Meat",     origin: "England" },
  { id: "camborough",     name: "Camborough",              group: "Meat",     origin: "United Kingdom" },
  // Lard
  { id: "poland-china",   name: "Poland China",            group: "Lard",     origin: "United States" },
  { id: "chester-white",  name: "Chester White",           group: "Lard",     origin: "United States" },
  { id: "mangalica",      name: "Mangalica",               group: "Lard",     origin: "Hungary" },
  { id: "meishan",        name: "Meishan",                 group: "Lard",     origin: "China" },
  // Heritage
  { id: "tamworth",       name: "Tamworth",                group: "Heritage", origin: "England" },
  { id: "gos",            name: "Gloucestershire Old Spots", group: "Heritage", origin: "England" },
  { id: "iberian",        name: "Iberian",                 group: "Heritage", origin: "Spain / Portugal" },
  { id: "oxford-sandy",   name: "Oxford Sandy and Black",  group: "Heritage", origin: "England" },
  { id: "red-wattle",     name: "Red Wattle",              group: "Heritage", origin: "United States" },
  { id: "ossabaw",        name: "Ossabaw Island",          group: "Heritage", origin: "United States" },
  { id: "hereford",       name: "Hereford",                group: "Heritage", origin: "United States" },
  // Miniature
  { id: "kunekune",       name: "KuneKune",                group: "Miniature", origin: "New Zealand" },
  { id: "vietnamese",     name: "Vietnamese Potbelly",     group: "Miniature", origin: "Vietnam" },
  { id: "juliana",        name: "Juliana",                 group: "Miniature", origin: "Europe" },
  { id: "american-mini",  name: "American Mini",           group: "Miniature", origin: "United States" },
];
