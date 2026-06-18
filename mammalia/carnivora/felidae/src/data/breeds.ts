export type CoatType = "longhair" | "shorthair" | "rex" | "wirehair" | "hairless";

export interface Breed {
  id: string;
  name: string;
  origin: string;
  region: "Americas" | "Europe" | "Asia" | "Africa & Middle East";
  coatType: CoatType;
  wildParentId?: string;
  wildParentName?: string;
}

export const BREEDS: Breed[] = [
  // Americas
  { id: "breed-american-bobtail",    name: "American Bobtail",    origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-american-curl",       name: "American Curl",       origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-american-shorthair",  name: "American Shorthair",  origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-american-wirehair",   name: "American Wirehair",   origin: "United States",      region: "Americas",             coatType: "wirehair"  },
  { id: "breed-bengal",              name: "Bengal",              origin: "United States",      region: "Americas",             coatType: "shorthair", wildParentId: "4MF7C", wildParentName: "Leopard cat" },
  { id: "breed-bombay",              name: "Bombay",              origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-chausie",             name: "Chausie",             origin: "United States",      region: "Americas",             coatType: "shorthair", wildParentId: "3DXV4", wildParentName: "Jungle cat" },
  { id: "breed-exotic-shorthair",    name: "Exotic Shorthair",    origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-havana-brown",        name: "Havana Brown",        origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-laperm",              name: "LaPerm",              origin: "United States",      region: "Americas",             coatType: "rex"       },
  { id: "breed-maine-coon",          name: "Maine Coon",          origin: "United States",      region: "Americas",             coatType: "longhair"  },
  { id: "breed-munchkin",            name: "Munchkin",            origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-ocicat",              name: "Ocicat",              origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-ragamuffin",          name: "Ragamuffin",          origin: "United States",      region: "Americas",             coatType: "longhair"  },
  { id: "breed-ragdoll",             name: "Ragdoll",             origin: "United States",      region: "Americas",             coatType: "longhair"  },
  { id: "breed-savannah",            name: "Savannah",            origin: "United States",      region: "Americas",             coatType: "shorthair", wildParentId: "3THH7", wildParentName: "Serval" },
  { id: "breed-selkirk-rex",         name: "Selkirk Rex",         origin: "United States",      region: "Americas",             coatType: "rex"       },
  { id: "breed-snowshoe",            name: "Snowshoe",            origin: "United States",      region: "Americas",             coatType: "shorthair" },
  { id: "breed-sphynx",              name: "Sphynx",              origin: "Canada",             region: "Americas",             coatType: "hairless"  },
  { id: "breed-tonkinese",           name: "Tonkinese",           origin: "Canada",             region: "Americas",             coatType: "shorthair" },
  { id: "breed-toyger",              name: "Toyger",              origin: "United States",      region: "Americas",             coatType: "shorthair" },

  // Europe
  { id: "breed-birman",              name: "Birman",              origin: "France",             region: "Europe",               coatType: "longhair"  },
  { id: "breed-british-longhair",    name: "British Longhair",    origin: "United Kingdom",     region: "Europe",               coatType: "longhair"  },
  { id: "breed-british-shorthair",   name: "British Shorthair",   origin: "United Kingdom",     region: "Europe",               coatType: "shorthair" },
  { id: "breed-chartreux",           name: "Chartreux",           origin: "France",             region: "Europe",               coatType: "shorthair" },
  { id: "breed-cornish-rex",         name: "Cornish Rex",         origin: "United Kingdom",     region: "Europe",               coatType: "rex"       },
  { id: "breed-cymric",              name: "Cymric",              origin: "Canada/Wales",       region: "Europe",               coatType: "longhair"  },
  { id: "breed-devon-rex",           name: "Devon Rex",           origin: "United Kingdom",     region: "Europe",               coatType: "rex"       },
  { id: "breed-european-shorthair",  name: "European Shorthair",  origin: "Sweden",             region: "Europe",               coatType: "shorthair" },
  { id: "breed-manx",               name: "Manx",               origin: "Isle of Man",        region: "Europe",               coatType: "shorthair" },
  { id: "breed-norwegian-forest",    name: "Norwegian Forest",    origin: "Norway",             region: "Europe",               coatType: "longhair"  },
  { id: "breed-persian",             name: "Persian",             origin: "Iran/United Kingdom",region: "Europe",               coatType: "longhair"  },
  { id: "breed-russian-blue",        name: "Russian Blue",        origin: "Russia",             region: "Europe",               coatType: "shorthair" },
  { id: "breed-scottish-fold",       name: "Scottish Fold",       origin: "Scotland",           region: "Europe",               coatType: "shorthair" },
  { id: "breed-siberian",            name: "Siberian",            origin: "Russia",             region: "Europe",               coatType: "longhair"  },
  { id: "breed-turkish-angora",      name: "Turkish Angora",      origin: "Turkey",             region: "Europe",               coatType: "longhair"  },
  { id: "breed-turkish-van",         name: "Turkish Van",         origin: "Turkey",             region: "Europe",               coatType: "longhair"  },

  // Asia
  { id: "breed-balinese",            name: "Balinese",            origin: "United States",      region: "Asia",                 coatType: "longhair"  },
  { id: "breed-burmese",             name: "Burmese",             origin: "Myanmar",            region: "Asia",                 coatType: "shorthair" },
  { id: "breed-burmilla",            name: "Burmilla",            origin: "United Kingdom",     region: "Asia",                 coatType: "shorthair" },
  { id: "breed-chinese-li-hua",      name: "Chinese Li Hua",      origin: "China",              region: "Asia",                 coatType: "shorthair" },
  { id: "breed-japanese-bobtail",    name: "Japanese Bobtail",    origin: "Japan",              region: "Asia",                 coatType: "shorthair" },
  { id: "breed-javanese",            name: "Javanese",            origin: "United States",      region: "Asia",                 coatType: "longhair"  },
  { id: "breed-khao-manee",          name: "Khao Manee",          origin: "Thailand",           region: "Asia",                 coatType: "shorthair" },
  { id: "breed-korat",               name: "Korat",               origin: "Thailand",           region: "Asia",                 coatType: "shorthair" },
  { id: "breed-oriental-shorthair",  name: "Oriental Shorthair",  origin: "United Kingdom",     region: "Asia",                 coatType: "shorthair" },
  { id: "breed-siamese",             name: "Siamese",             origin: "Thailand",           region: "Asia",                 coatType: "shorthair" },
  { id: "breed-singapore",           name: "Singapura",           origin: "Singapore",          region: "Asia",                 coatType: "shorthair" },
  { id: "breed-thai",                name: "Thai",                origin: "Thailand",           region: "Asia",                 coatType: "shorthair" },

  // Africa & Middle East
  { id: "breed-abyssinian",          name: "Abyssinian",          origin: "Ethiopia",           region: "Africa & Middle East", coatType: "shorthair" },
  { id: "breed-arabian-mau",         name: "Arabian Mau",         origin: "Arabian Peninsula",  region: "Africa & Middle East", coatType: "shorthair" },
  { id: "breed-egyptian-mau",        name: "Egyptian Mau",        origin: "Egypt",              region: "Africa & Middle East", coatType: "shorthair" },
  { id: "breed-somali",              name: "Somali",              origin: "United States",      region: "Africa & Middle East", coatType: "longhair"  },
];

export const REGIONS = ["Americas", "Europe", "Asia", "Africa & Middle East"] as const;
export type Region = typeof REGIONS[number];
