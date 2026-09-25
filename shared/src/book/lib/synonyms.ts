import type { BookNode } from "../types";

// Some species in the tree carry an old/regional scientific name whose
// Wikipedia-sourced description was written for the currently-accepted name
// instead (no separate article exists for the synonym) - e.g. Felidae's
// "Felis lanea" describing "the cheetah (Acinonyx jubatus)". Detected from
// the description text since no separate taxon data is stored on the node.
// Restricted to the first 60 characters so a binomial mentioned deeper in
// the prose (a related species, say) isn't mistaken for the entry's own
// accepted name; excludes apostrophes so a restated common name in parens
// - "Lontra weiri (Weir's otter)" - doesn't parse as a fake genus.
const SYNONYM_RE = /^.{0,60}\(([A-Z][a-zà-ÿ-]+)\s+([a-zà-ÿ×-]+)\)/;

export function synonymTarget(species: Pick<BookNode, "description" | "name">): string | null {
  if (!species.description) return null;
  const m = SYNONYM_RE.exec(species.description);
  if (!m) return null;
  const [, genus, epithet] = m;
  const ownGenus = species.name.split(" ")[0];
  if (genus.toLowerCase() === ownGenus.toLowerCase()) return null;
  return `${genus} ${epithet}`;
}