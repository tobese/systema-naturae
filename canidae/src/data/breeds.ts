export interface DogBreed {
  id: string;
  name: string;
  group: string;
  origin: string;
}

export const AKC_GROUPS = [
  "Sporting",
  "Hound",
  "Working",
  "Terrier",
  "Toy",
  "Non-Sporting",
  "Herding",
] as const;

export const BREEDS: DogBreed[] = [
  // Sporting
  { id: "labrador-retriever",          name: "Labrador Retriever",          group: "Sporting",      origin: "Canada / England" },
  { id: "golden-retriever",            name: "Golden Retriever",            group: "Sporting",      origin: "Scotland" },
  { id: "german-shorthaired-pointer",  name: "German Shorthaired Pointer",  group: "Sporting",      origin: "Germany" },
  { id: "english-springer-spaniel",    name: "English Springer Spaniel",    group: "Sporting",      origin: "England" },
  { id: "cocker-spaniel",              name: "Cocker Spaniel",              group: "Sporting",      origin: "England" },
  { id: "irish-setter",                name: "Irish Setter",                group: "Sporting",      origin: "Ireland" },
  { id: "weimaraner",                  name: "Weimaraner",                  group: "Sporting",      origin: "Germany" },
  { id: "vizsla",                      name: "Vizsla",                      group: "Sporting",      origin: "Hungary" },
  { id: "brittany",                    name: "Brittany",                    group: "Sporting",      origin: "France" },
  { id: "chesapeake-bay-retriever",    name: "Chesapeake Bay Retriever",    group: "Sporting",      origin: "United States" },
  { id: "flat-coated-retriever",       name: "Flat-Coated Retriever",       group: "Sporting",      origin: "England" },
  { id: "nova-scotia-duck-tolling",    name: "Nova Scotia Duck Tolling Retriever", group: "Sporting", origin: "Canada" },

  // Hound
  { id: "beagle",                      name: "Beagle",                      group: "Hound",         origin: "England" },
  { id: "bloodhound",                  name: "Bloodhound",                  group: "Hound",         origin: "Belgium / England" },
  { id: "greyhound",                   name: "Greyhound",                   group: "Hound",         origin: "Ancient Egypt / England" },
  { id: "whippet",                     name: "Whippet",                     group: "Hound",         origin: "England" },
  { id: "dachshund",                   name: "Dachshund",                   group: "Hound",         origin: "Germany" },
  { id: "basset-hound",                name: "Basset Hound",                group: "Hound",         origin: "France" },
  { id: "afghan-hound",                name: "Afghan Hound",                group: "Hound",         origin: "Afghanistan" },
  { id: "irish-wolfhound",             name: "Irish Wolfhound",             group: "Hound",         origin: "Ireland" },
  { id: "rhodesian-ridgeback",         name: "Rhodesian Ridgeback",         group: "Hound",         origin: "Southern Africa" },
  { id: "borzoi",                      name: "Borzoi",                      group: "Hound",         origin: "Russia" },
  { id: "saluki",                      name: "Saluki",                      group: "Hound",         origin: "Middle East" },
  { id: "norwegian-elkhound",          name: "Norwegian Elkhound",          group: "Hound",         origin: "Norway" },

  // Working
  { id: "siberian-husky",              name: "Siberian Husky",              group: "Working",       origin: "Russia" },
  { id: "alaskan-malamute",            name: "Alaskan Malamute",            group: "Working",       origin: "United States" },
  { id: "rottweiler",                  name: "Rottweiler",                  group: "Working",       origin: "Germany" },
  { id: "doberman-pinscher",           name: "Doberman Pinscher",           group: "Working",       origin: "Germany" },
  { id: "great-dane",                  name: "Great Dane",                  group: "Working",       origin: "Germany" },
  { id: "saint-bernard",               name: "Saint Bernard",               group: "Working",       origin: "Switzerland" },
  { id: "boxer",                       name: "Boxer",                       group: "Working",       origin: "Germany" },
  { id: "bernese-mountain-dog",        name: "Bernese Mountain Dog",        group: "Working",       origin: "Switzerland" },
  { id: "newfoundland",                name: "Newfoundland",                group: "Working",       origin: "Canada" },
  { id: "great-pyrenees",              name: "Great Pyrenees",              group: "Working",       origin: "France / Spain" },
  { id: "akita",                       name: "Akita",                       group: "Working",       origin: "Japan" },
  { id: "samoyed",                     name: "Samoyed",                     group: "Working",       origin: "Russia" },

  // Terrier
  { id: "scottish-terrier",            name: "Scottish Terrier",            group: "Terrier",       origin: "Scotland" },
  { id: "west-highland-white-terrier", name: "West Highland White Terrier", group: "Terrier",       origin: "Scotland" },
  { id: "jack-russell-terrier",        name: "Jack Russell Terrier",        group: "Terrier",       origin: "England" },
  { id: "bull-terrier",                name: "Bull Terrier",                group: "Terrier",       origin: "England" },
  { id: "airedale-terrier",            name: "Airedale Terrier",            group: "Terrier",       origin: "England" },
  { id: "yorkshire-terrier",           name: "Yorkshire Terrier",           group: "Terrier",       origin: "England" },
  { id: "staffordshire-bull-terrier",  name: "Staffordshire Bull Terrier",  group: "Terrier",       origin: "England" },
  { id: "cairn-terrier",               name: "Cairn Terrier",               group: "Terrier",       origin: "Scotland" },
  { id: "border-terrier",              name: "Border Terrier",              group: "Terrier",       origin: "England / Scotland" },
  { id: "miniature-schnauzer",         name: "Miniature Schnauzer",         group: "Terrier",       origin: "Germany" },

  // Toy
  { id: "chihuahua",                   name: "Chihuahua",                   group: "Toy",           origin: "Mexico" },
  { id: "pomeranian",                  name: "Pomeranian",                  group: "Toy",           origin: "Germany / Poland" },
  { id: "maltese",                     name: "Maltese",                     group: "Toy",           origin: "Malta" },
  { id: "shih-tzu",                    name: "Shih Tzu",                    group: "Toy",           origin: "China / Tibet" },
  { id: "pug",                         name: "Pug",                         group: "Toy",           origin: "China" },
  { id: "french-bulldog",              name: "French Bulldog",              group: "Toy",           origin: "France / England" },
  { id: "cavalier-king-charles",       name: "Cavalier King Charles Spaniel", group: "Toy",         origin: "England" },
  { id: "miniature-pinscher",          name: "Miniature Pinscher",          group: "Toy",           origin: "Germany" },
  { id: "italian-greyhound",           name: "Italian Greyhound",           group: "Toy",           origin: "Italy" },
  { id: "papillon",                    name: "Papillon",                    group: "Toy",           origin: "France / Belgium" },
  { id: "toy-poodle",                  name: "Toy Poodle",                  group: "Toy",           origin: "France / Germany" },

  // Non-Sporting
  { id: "dalmatian",                   name: "Dalmatian",                   group: "Non-Sporting",  origin: "Croatia" },
  { id: "bulldog",                     name: "Bulldog",                     group: "Non-Sporting",  origin: "England" },
  { id: "standard-poodle",             name: "Standard Poodle",             group: "Non-Sporting",  origin: "France / Germany" },
  { id: "chow-chow",                   name: "Chow Chow",                   group: "Non-Sporting",  origin: "China" },
  { id: "shar-pei",                    name: "Shar Pei",                    group: "Non-Sporting",  origin: "China" },
  { id: "shiba-inu",                   name: "Shiba Inu",                   group: "Non-Sporting",  origin: "Japan" },
  { id: "bichon-frise",                name: "Bichon Frisé",                group: "Non-Sporting",  origin: "France / Belgium" },
  { id: "lhasa-apso",                  name: "Lhasa Apso",                  group: "Non-Sporting",  origin: "Tibet" },
  { id: "keeshond",                    name: "Keeshond",                    group: "Non-Sporting",  origin: "Netherlands" },
  { id: "tibetan-spaniel",             name: "Tibetan Spaniel",             group: "Non-Sporting",  origin: "Tibet" },

  // Herding
  { id: "border-collie",               name: "Border Collie",               group: "Herding",       origin: "England / Scotland" },
  { id: "australian-shepherd",         name: "Australian Shepherd",         group: "Herding",       origin: "United States" },
  { id: "german-shepherd",             name: "German Shepherd",             group: "Herding",       origin: "Germany" },
  { id: "shetland-sheepdog",           name: "Shetland Sheepdog",           group: "Herding",       origin: "Scotland" },
  { id: "rough-collie",                name: "Rough Collie",                group: "Herding",       origin: "Scotland" },
  { id: "australian-cattle-dog",       name: "Australian Cattle Dog",       group: "Herding",       origin: "Australia" },
  { id: "pembroke-welsh-corgi",        name: "Pembroke Welsh Corgi",        group: "Herding",       origin: "Wales" },
  { id: "cardigan-welsh-corgi",        name: "Cardigan Welsh Corgi",        group: "Herding",       origin: "Wales" },
  { id: "belgian-malinois",            name: "Belgian Malinois",            group: "Herding",       origin: "Belgium" },
  { id: "old-english-sheepdog",        name: "Old English Sheepdog",        group: "Herding",       origin: "England" },
  { id: "bouvier-des-flandres",        name: "Bouvier des Flandres",        group: "Herding",       origin: "Belgium" },
];
