// Hand-written Family-level prose for the curated Parts (Mammalia,
// Chondrichthyes, Reptilia). The portal's data has no `description` field
// at FAMILY rank at all (confirmed empty across every family sampled) -
// unlike Order and Genus, which the portal already enriches. Aves is out of
// scope here: 254 families is a data-enrichment project, not something to
// hand-write - see experiments/book-view/README.md "Data architecture".
export const FAMILY_INTROS: Record<string, string> = {
  felidae:
    "The cat family - obligate carnivores built around retractable claws, acute night vision, and a stalk-and-ambush hunting style, ranging from the domestic cat to the tiger, the largest living cat.",
  ursidae:
    "Bears - large, plantigrade omnivores found on every continent but Africa and Australia, united by a stocky build, small eyes, and (in most species) a period of winter dormancy.",
  hominidae:
    "The great apes - humans, chimpanzees, bonobos, gorillas, and orangutans, the largest-brained primates, sharing tool use, complex social structures, and no external tail.",
  cercopithecidae:
    "The Old World monkeys - baboons, macaques, colobus, and langurs, found across Africa and Asia, distinguished from apes by their tails and from New World monkeys by non-prehensile tails and closely-set nostrils.",
  cebidae:
    "New World monkeys of Central and South America, many with prehensile tails capable of grasping branches like a fifth limb - a trait no Old World primate has.",
  lemuridae:
    "True lemurs, found only on Madagascar and the Comoro Islands - the island's isolation let them radiate into a huge range of forms after arriving with no competition from monkeys or apes.",
  cetacea:
    "Whales, dolphins, and porpoises - fully aquatic mammals descended from land-dwelling artiodactyls, including the blue whale, the largest animal ever known to have existed.",
  elephantidae:
    "Elephants - the largest living land animals, defined by their trunk, tusks, and among the largest brains of any land mammal, organized into complex matriarchal herds.",
  equidae:
    "Horses, zebras, and asses - odd-toed ungulates built for sustained running on a single hoofed toe per foot, among the last wild megafauna to persist in open grassland and steppe.",
  macropodidae:
    "Kangaroos and wallabies - Australia and New Guinea's hopping marsupials, propelled by powerful hind legs and a thick tail used for balance and, at rest, as a fifth limb.",
  vombatidae:
    "Wombats - burrowing Australian marsupials with backward-facing pouches (so digging doesn't bury their joeys) and cube-shaped droppings, unique among mammals.",
  leporidae:
    "Rabbits and hares - fast-breeding, long-eared lagomorphs found on every continent but Antarctica, distinguished from rodents by a second, smaller pair of upper incisors.",
  dasyuridae:
    "The carnivorous marsupials of Australia and New Guinea - quolls, the Tasmanian devil, and many small insectivorous species, filling the ecological niches cats and weasels hold elsewhere.",
  giraffidae:
    "Giraffes and the okapi - the tallest living land animals and their reclusive, striped-legged forest relative, both browsers with long prehensile tongues built for reaching high foliage.",
  caprinae:
    "Wild goats, sheep, and their bovid relatives - sure-footed mountain and steppe grazers, most bearing permanent horns in both sexes, used in ritualized combat over mates and territory.",
  erinaceidae:
    "Hedgehogs and their smooth-furred relatives the gymnures - small insectivorous mammals; only the true hedgehogs have the family's namesake coat of defensive spines.",
  talpidae:
    "Moles, desmans, and shrew moles - burrowing insectivores with broad, spade-like forefeet built for digging, many nearly blind and relying instead on touch and smell underground.",
  dasypodidae:
    "Armadillos - the only mammals with a hard, bony armor shell, native to the Americas; some species can roll into a near-complete ball when threatened.",
  caviidae:
    "Guinea pigs, capybaras, and their South American relatives - the family includes the capybara, the largest living rodent, alongside much smaller cavies domesticated for food and companionship.",
  castoridae:
    "Beavers - large semi-aquatic rodents and the animal world's most prolific engineers, felling trees and damming streams to create the wetland habitat they depend on.",
  manidae:
    "Pangolins - the only mammals entirely covered in overlapping keratin scales, curling into an armored ball for defense; among the most heavily trafficked mammals in the world.",
  bradypodidae:
    "Three-toed sloths - slow-moving Central and South American tree-dwellers whose low metabolism and algae-tinted fur make them nearly invisible to predators overhead.",
  myrmecophagidae:
    "Anteaters - toothless, long-snouted insectivores that use a sticky, rapid-fire tongue to feed almost exclusively on ants and termites, from giant ground-dwelling to small arboreal species.",
  didelphidae:
    "Opossums - the only marsupials native to the Americas, and the most taxonomically diverse: over 100 species from the familiar Virginia opossum to tiny mouse-sized forest species.",
  lamnidae:
    "Mackerel sharks - large, powerful, largely warm-bodied predators including the great white and the mako sharks, the fastest of all sharks.",
  carcharhinidae:
    "Requiem sharks - the most species-rich shark family, including the bull, tiger, and reef sharks; most are active, open-water predators found in warm seas worldwide.",
  sphyrnidae:
    "Hammerhead sharks - instantly recognizable for their flattened, laterally-expanded head, which spreads their electroreceptors wide for more precise prey detection.",
  testudinidae:
    "Tortoises - the land-dwelling turtles, with heavy domed shells and elephantine feet built for walking rather than swimming; includes the longest-lived land vertebrates known.",
  cheloniidae:
    "Sea turtles - ocean-going turtles with flattened, paddle-like limbs, all species migratory and, apart from nesting females coming ashore to lay eggs, entirely marine.",
  dermochelyidae:
    "The leatherback sea turtle - the sole living member of its family, and the largest turtle on Earth, with a flexible, leathery carapace instead of the bony shell of every other turtle.",
};
