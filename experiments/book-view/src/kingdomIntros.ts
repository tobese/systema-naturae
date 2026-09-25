import type { Kingdom } from "@shared/book/types";

// Hand-written framing prose for each of the six kingdoms, shown once on a
// dedicated intro page before a reader descends into that kingdom's Parts —
// the kingdom-level counterpart to curatedParts.ts's PART_INTROS (which
// frame a single Class). Each entry is an array of paragraphs rather than
// one string, since this page is meant to read as a short opening essay,
// not a single caption-length line.
export const KINGDOM_INTROS: Record<Kingdom, string[]> = {
  Animalia: [
    "The animal kingdom is the branch of life that moves, hunts, and is hunted — multicellular organisms that eat rather than photosynthesize, built around some capacity to sense the world and respond to it. It is the best-studied of the six kingdoms by a wide margin, if only because we are members of it ourselves, and its more than a million described species outnumber every other kingdom in this book combined.",
    "This Part begins, as Linnaeus's own taxonomy loosely did, with the vertebrates most familiar to a human reader — mammals, birds, reptiles — before descending into arthropods, mollusks, and the sprawling, still poorly cataloged invertebrate phyla that make up the true bulk of animal diversity. Coverage here is deliberately uneven: a beetle family with forty thousand species and a single well-studied primate family receive the same structural treatment, even where one is described down to nearly every species and the other barely at all — the shape of what we know, and don't, is part of the story this book tells.",
  ],
  Plantae: [
    "The plant kingdom is life that feeds itself on sunlight — rooted, largely immobile organisms built around chloroplasts inherited from an ancient cyanobacterium a plant cell's ancestor once engulfed and never let go. From towering conifers to the ferns and mosses that carpeted a forest floor before any tree existed to shade them, this Part follows a lineage that reshaped the planet's atmosphere long before animals had lungs to breathe it.",
    "Where the animal Part leans on centuries of naturalist prose, botanical description here draws more heavily on distribution and habitat — a plant's native range and growth form are, for most of the species in this book, the most complete record that exists of it. It is a thinner kind of prose, but no less real for that.",
  ],
  Fungi: [
    "Fungi are neither plant nor animal, closer on the tree of life to the latter than the former despite every outward appearance to the contrary — organisms that digest their food outside their own bodies, releasing enzymes into whatever they're growing on or through and absorbing the results. This Part covers a kingdom mostly hidden from view: what we call a mushroom is only the fruiting body of an organism whose real bulk, a mycelial network threading through soil or wood, is rarely seen at all.",
    "Fungi are also the least completely known kingdom in this book relative to what almost certainly exists — mycologists estimate the true number of fungal species at several million, against a few hundred thousand formally described. What follows is a record of that described fraction: real and verifiable, but still a small window onto a much larger dark.",
  ],
  Chromista: [
    "Chromista is the kingdom this book gives least readily to intuition — grouped less by shared ancestry in the animal or plant sense than by a shared evolutionary origin story: cells built around a chloroplast acquired secondhand, engulfed from a red alga rather than grown from within. It gathers organisms as different as the diatoms that produce a fifth of the oxygen humans breathe, the kelp forests off temperate coastlines, and the oomycetes better known to a gardener as water molds and blights.",
    "Much of this Part exists at a scale invisible to the naked eye — single-celled and often glassy-shelled, known more from a microscope slide or a sediment core than from a field guide. Where earlier Parts follow a familiar naturalist's instinct — describe what you can see — this one follows a more recent one: describe what a micrograph or a gene sequence reveals instead.",
  ],
  Protozoa: [
    "Protozoa is the kingdom of the single cell doing everything an organism needs to do without ever dividing the labor across two: hunting, digesting, sensing, reproducing, all within one membrane. Amoebae that engulf their prey whole, flagellates that power themselves through water with a single whip-like tail, slime molds that spend part of their life as solitary cells and part as a single crawling, decision-making mass — this Part follows organisms that blur, more than any other kingdom in this book, the line between \"one\" and \"many.\"",
    "Much of what's known about this kingdom comes from freshwater ponds, soil samples, and the guts of other animals rather than from open habitat surveys, and the record reflects it: patchy and often decades old, thinner than any other kingdom's here by simple neglect rather than any real scarcity in the wild.",
  ],
  Archaea: [
    "Archaea is the newest kingdom by discovery, not by age — organisms that look like bacteria under a microscope but diverged from them so long ago, and build their cell membranes so differently, that they were only recognized as a separate domain of life in 1977. Many of the species in this Part were first found in places almost nothing else survives: boiling hydrothermal vents, saturated brine pools, the near-frozen dark of the deep seafloor, giving the kingdom an early reputation — since revised — as purely a chemistry of extremes.",
    "Taxonomy here looks different from every other Part in this book. Most Archaea have never been cultured in a lab at all; what's known of them comes from DNA sequenced directly out of an environmental sample, assembled into a genome, and given a placeholder name — which is why so many of the \"families\" and \"genera\" that follow read as alphanumeric codes rather than Latin binomials. It is taxonomy built from sequence data before it had a name to give the organism behind it.",
  ],
};
