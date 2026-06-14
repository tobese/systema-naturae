export interface WaterfowlBreed {
  id: string;
  name: string;
  group: string;
  species: "duck" | "goose";
  origin: string;
}

export const DUCK_GROUPS = ["Meat", "Egg", "Dual-purpose", "Ornamental"] as const;
export const GOOSE_GROUPS = ["Standard"] as const;

export const DUCK_BREEDS: WaterfowlBreed[] = [
  // Meat
  { id: "pekin",           name: "Pekin",            group: "Meat",        species: "duck", origin: "China" },
  { id: "rouen",           name: "Rouen",            group: "Meat",        species: "duck", origin: "France" },
  { id: "aylesbury",       name: "Aylesbury",        group: "Meat",        species: "duck", origin: "England" },
  { id: "muscovy-d",       name: "Muscovy",          group: "Meat",        species: "duck", origin: "South America" },
  // Egg
  { id: "khaki-campbell",  name: "Khaki Campbell",   group: "Egg",         species: "duck", origin: "England" },
  { id: "indian-runner",   name: "Indian Runner",    group: "Egg",         species: "duck", origin: "Indonesia" },
  { id: "welsh-harlequin", name: "Welsh Harlequin",  group: "Egg",         species: "duck", origin: "Wales" },
  // Dual-purpose
  { id: "swedish-blue",    name: "Swedish Blue",     group: "Dual-purpose",species: "duck", origin: "Sweden" },
  { id: "cayuga",          name: "Cayuga",           group: "Dual-purpose",species: "duck", origin: "United States" },
  { id: "magpie",          name: "Magpie",           group: "Dual-purpose",species: "duck", origin: "Wales" },
  // Ornamental
  { id: "call-duck",       name: "Call Duck",        group: "Ornamental",  species: "duck", origin: "Netherlands" },
  { id: "east-indie",      name: "East Indie",       group: "Ornamental",  species: "duck", origin: "United States" },
  { id: "silver-appleyard",name: "Silver Appleyard", group: "Ornamental",  species: "duck", origin: "England" },
];

export const GOOSE_BREEDS: WaterfowlBreed[] = [
  { id: "embden",         name: "Embden",        group: "Standard", species: "goose", origin: "Germany" },
  { id: "toulouse",       name: "Toulouse",      group: "Standard", species: "goose", origin: "France" },
  { id: "american-buff",  name: "American Buff", group: "Standard", species: "goose", origin: "United States" },
  { id: "pilgrim",        name: "Pilgrim",       group: "Standard", species: "goose", origin: "United States" },
  { id: "sebastopol",     name: "Sebastopol",    group: "Standard", species: "goose", origin: "Eastern Europe" },
  { id: "chinese",        name: "Chinese",       group: "Standard", species: "goose", origin: "China" },
  { id: "african",        name: "African",       group: "Standard", species: "goose", origin: "China" },
];
