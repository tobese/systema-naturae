export interface ChickenBreed {
  id: string;
  name: string;
  group: string;
  species: "chicken" | "turkey";
  origin: string;
}

export const CHICKEN_GROUPS = ["Egg", "Meat", "Dual-purpose", "Ornamental"] as const;
export const TURKEY_GROUPS = ["Standard"] as const;

export const CHICKEN_BREEDS: ChickenBreed[] = [
  // Egg
  { id: "white-leghorn",   name: "White Leghorn",   group: "Egg",          species: "chicken", origin: "Italy" },
  { id: "rhode-island-red",name: "Rhode Island Red", group: "Egg",          species: "chicken", origin: "United States" },
  { id: "sussex",          name: "Sussex",           group: "Egg",          species: "chicken", origin: "England" },
  { id: "australorp",      name: "Australorp",       group: "Egg",          species: "chicken", origin: "Australia" },
  { id: "isa-brown",       name: "ISA Brown",        group: "Egg",          species: "chicken", origin: "France" },
  { id: "araucana",        name: "Araucana",         group: "Egg",          species: "chicken", origin: "Chile" },
  // Meat
  { id: "cornish-cross",   name: "Cornish Cross",    group: "Meat",         species: "chicken", origin: "United Kingdom" },
  { id: "jersey-giant",    name: "Jersey Giant",     group: "Meat",         species: "chicken", origin: "United States" },
  { id: "bresse",          name: "Bresse",           group: "Meat",         species: "chicken", origin: "France" },
  { id: "delaware",        name: "Delaware",         group: "Meat",         species: "chicken", origin: "United States" },
  // Dual-purpose
  { id: "plymouth-rock",   name: "Plymouth Rock",    group: "Dual-purpose", species: "chicken", origin: "United States" },
  { id: "wyandotte",       name: "Wyandotte",        group: "Dual-purpose", species: "chicken", origin: "United States" },
  { id: "orpington",       name: "Orpington",        group: "Dual-purpose", species: "chicken", origin: "England" },
  { id: "dominique",       name: "Dominique",        group: "Dual-purpose", species: "chicken", origin: "United States" },
  // Ornamental
  { id: "silkie",          name: "Silkie",           group: "Ornamental",   species: "chicken", origin: "China" },
  { id: "polish",          name: "Polish",           group: "Ornamental",   species: "chicken", origin: "Netherlands" },
  { id: "cochin",          name: "Cochin",           group: "Ornamental",   species: "chicken", origin: "China" },
  { id: "sebright",        name: "Sebright",         group: "Ornamental",   species: "chicken", origin: "England" },
  { id: "frizzle",         name: "Frizzle",          group: "Ornamental",   species: "chicken", origin: "Asia" },
];

export const TURKEY_BREEDS: ChickenBreed[] = [
  { id: "broad-breasted-white",  name: "Broad Breasted White",  group: "Standard", species: "turkey", origin: "United States" },
  { id: "broad-breasted-bronze", name: "Broad Breasted Bronze", group: "Standard", species: "turkey", origin: "United States" },
  { id: "narragansett",          name: "Narragansett",          group: "Standard", species: "turkey", origin: "United States" },
  { id: "bourbon-red",           name: "Bourbon Red",           group: "Standard", species: "turkey", origin: "United States" },
  { id: "royal-palm",            name: "Royal Palm",            group: "Standard", species: "turkey", origin: "United States" },
  { id: "slate",                 name: "Slate",                 group: "Standard", species: "turkey", origin: "United States" },
];
