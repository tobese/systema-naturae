// Hand-written Family-level prose for the curated Parts (Mammalia,
// Chondrichthyes, Reptilia). The portal's taxonomy.json now carries `description`
// at FAMILY rank for families covered by the local-wiki enrichment pass
// (felidae, canidae, ...) - those flow straight through the order files and
// must NOT be listed here, or this sidecar would overwrite the longer prose.
// This map is the fallback for families the portal hasn't enriched yet.
// Aves is out of scope here: 254 families is a data-enrichment project, not
// something to hand-write - see experiments/book-view/README.md "Data architecture".
export const FAMILY_INTROS: Record<string, string> = {
  ursidae:
    "Bears - large, plantigrade omnivores found on every continent but Africa and Australia, united by a stocky build, small eyes, and (in most species) a period of winter dormancy.",
  cercopithecidae:
    "The Old World monkeys - baboons, macaques, colobus, and langurs, found across Africa and Asia, distinguished from apes by their tails and from New World monkeys by non-prehensile tails and closely-set nostrils.",
  cebidae:
    "New World monkeys of Central and South America, many with prehensile tails capable of grasping branches like a fifth limb - a trait no Old World primate has.",
  cetacea:
    "Whales, dolphins, and porpoises - fully aquatic mammals descended from land-dwelling artiodactyls, including the blue whale, the largest animal ever known to have existed.",
  vombatidae:
    "Wombats - burrowing Australian marsupials with backward-facing pouches (so digging doesn't bury their joeys) and cube-shaped droppings, unique among mammals.",
  bradypodidae:
    "Three-toed sloths - slow-moving Central and South American tree-dwellers whose low metabolism and algae-tinted fur make them nearly invisible to predators overhead.",
  didelphidae:
    "Opossums - the only marsupials native to the Americas, and the most taxonomically diverse: over 100 species from the familiar Virginia opossum to tiny mouse-sized forest species.",
  carcharhinidae:
    "Requiem sharks - the most species-rich shark family, including the bull, tiger, and reef sharks; most are active, open-water predators found in warm seas worldwide.",
  sphyrnidae:
    "Hammerhead sharks - instantly recognizable for their flattened, laterally-expanded head, which spreads their electroreceptors wide for more precise prey detection.",
  testudinidae:
    "Tortoises - the land-dwelling turtles, with heavy domed shells and elephantine feet built for walking rather than swimming; includes the longest-lived land vertebrates known.",
};
