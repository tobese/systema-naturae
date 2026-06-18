export interface HorseBreed {
  id: string;
  name: string;
  group: string;
  origin: string;
}

export const DISCIPLINE_GROUPS = [
  "Racing",
  "Warmblood",
  "Draft",
  "Gaited",
  "Pony",
  "Baroque",
] as const;

export const BREEDS: HorseBreed[] = [
  // Racing
  { id: "thoroughbred",        name: "Thoroughbred",        group: "Racing",    origin: "England" },
  { id: "quarter-horse",       name: "Quarter Horse",       group: "Racing",    origin: "United States" },
  { id: "arabian",             name: "Arabian",             group: "Racing",    origin: "Arabian Peninsula" },
  { id: "standardbred",        name: "Standardbred",        group: "Racing",    origin: "United States" },
  { id: "akhal-teke",          name: "Akhal-Teke",          group: "Racing",    origin: "Turkmenistan" },
  // Warmblood
  { id: "hanoverian",          name: "Hanoverian",          group: "Warmblood", origin: "Germany" },
  { id: "kwpn",                name: "KWPN",                group: "Warmblood", origin: "Netherlands" },
  { id: "trakehner",           name: "Trakehner",           group: "Warmblood", origin: "Germany" },
  { id: "oldenburg",           name: "Oldenburg",           group: "Warmblood", origin: "Germany" },
  { id: "swedish-warmblood",   name: "Swedish Warmblood",   group: "Warmblood", origin: "Sweden" },
  // Draft
  { id: "clydesdale",          name: "Clydesdale",          group: "Draft",     origin: "Scotland" },
  { id: "shire",               name: "Shire",               group: "Draft",     origin: "England" },
  { id: "percheron",           name: "Percheron",           group: "Draft",     origin: "France" },
  { id: "belgian-draft",       name: "Belgian Draft",       group: "Draft",     origin: "Belgium" },
  { id: "suffolk-punch",       name: "Suffolk Punch",       group: "Draft",     origin: "England" },
  // Gaited
  { id: "tennessee-walker",    name: "Tennessee Walker",    group: "Gaited",    origin: "United States" },
  { id: "paso-fino",           name: "Paso Fino",           group: "Gaited",    origin: "Spain / Caribbean" },
  { id: "icelandic",           name: "Icelandic Horse",     group: "Gaited",    origin: "Iceland" },
  { id: "missouri-fox-trotter",name: "Missouri Fox Trotter",group: "Gaited",    origin: "United States" },
  { id: "peruvian-paso",       name: "Peruvian Paso",       group: "Gaited",    origin: "Peru" },
  // Pony
  { id: "shetland-pony",       name: "Shetland Pony",       group: "Pony",      origin: "Scotland" },
  { id: "welsh-pony",          name: "Welsh Pony",          group: "Pony",      origin: "Wales" },
  { id: "connemara",           name: "Connemara Pony",      group: "Pony",      origin: "Ireland" },
  { id: "haflinger",           name: "Haflinger",           group: "Pony",      origin: "Austria / Italy" },
  { id: "new-forest",          name: "New Forest Pony",     group: "Pony",      origin: "England" },
  // Baroque
  { id: "lipizzaner",          name: "Lipizzaner",          group: "Baroque",   origin: "Slovenia / Austria" },
  { id: "friesian",            name: "Friesian",            group: "Baroque",   origin: "Netherlands" },
  { id: "andalusian",          name: "Andalusian (PRE)",    group: "Baroque",   origin: "Spain" },
  { id: "lusitano",            name: "Lusitano",            group: "Baroque",   origin: "Portugal" },
  { id: "knabstrupper",        name: "Knabstrupper",        group: "Baroque",   origin: "Denmark" },
];
