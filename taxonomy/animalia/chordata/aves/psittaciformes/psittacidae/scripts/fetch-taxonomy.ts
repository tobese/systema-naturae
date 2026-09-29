import { writeFileSync } from "fs";
import { join } from "path";

const COL_API = "https://api.checklistbank.org";
const DATASET = "3LR";

const COMMON_NAMES: Record<string, string> = {
  "Psittacus erithacus":        "Grey Parrot",
  "Psittacus timneh":           "Timneh Parrot",
  "Ara ararauna":               "Blue-and-yellow Macaw",
  "Ara macao":                  "Scarlet Macaw",
  "Ara chloropterus":           "Red-and-green Macaw",
  "Ara severus":                "Chestnut-fronted Macaw",
  "Ara militaris":              "Military Macaw",
  "Ara ambiguus":               "Great Green Macaw",
  "Amazona aestiva":            "Blue-fronted Amazon",
  "Amazona ochrocephala":       "Yellow-crowned Amazon",
  "Amazona amazonica":          "Orange-winged Amazon",
  "Amazona autumnalis":         "Red-lored Amazon",
  "Amazona farinosa":           "Mealy Amazon",
  "Amazona ventralis":          "Hispaniolan Amazon",
  "Amazona leucocephala":       "Cuban Amazon",
  "Amazona viridigenalis":      "Red-crowned Amazon",
  "Aratinga nenday":            "Nanday Parakeet",
  "Aratinga solstitialis":      "Sun Parakeet",
  "Aratinga jandaya":           "Jandaya Parakeet",
  "Aratinga auricapillus":      "Golden-capped Parakeet",
  "Aratinga weddellii":         "Dusky-headed Parakeet",
  "Pyrrhura molinae":           "Green-cheeked Parakeet",
  "Pyrrhura frontalis":         "Maroon-bellied Parakeet",
  "Pyrrhura perlata":           "Crimson-bellied Parakeet",
  "Pyrrhura leucotis":          "White-eared Parakeet",
  "Pyrrhura picta":             "Painted Parakeet",
  "Myiopsitta monachus":        "Monk Parakeet",
  "Melopsittacus undulatus":    "Budgerigar",
  "Agapornis roseicollis":      "Rosy-faced Lovebird",
  "Agapornis personatus":       "Yellow-collared Lovebird",
  "Agapornis fischeri":         "Fischer's Lovebird",
  "Agapornis pullarius":        "Red-headed Lovebird",
  "Agapornis lilianae":         "Lilian's Lovebird",
  "Agapornis nigrigenis":       "Black-cheeked Lovebird",
  "Forpus passerinus":          "Green-rumped Parrotlet",
  "Forpus coelestis":           "Pacific Parrotlet",
  "Forpus xanthops":            "Yellow-faced Parrotlet",
  "Forpus conspicillatus":      "Spectacled Parrotlet",
  "Poicephalus senegalus":      "Senegal Parrot",
  "Poicephalus meyeri":         "Meyer's Parrot",
  "Poicephalus rufiventris":    "Red-bellied Parrot",
  "Poicephalus gulielmi":       "Jardine's Parrot",
  "Poicephalus robustus":       "Cape Parrot",
  "Eclectus roratus":           "Eclectus Parrot",
  "Deroptyus accipitrinus":     "Hawk-headed Parrot",
  "Pionus menstruus":           "Blue-headed Parrot",
  "Pionus maximiliani":         "Scaly-headed Parrot",
  "Pionus senilis":             "White-crowned Parrot",
  "Pionus sordidus":            "Red-billed Parrot",
  "Pionites leucogaster":       "White-bellied Caique",
  "Pionites melanocephalus":    "Black-headed Caique",
  "Brotogeris chiriri":         "Yellow-chevroned Parakeet",
  "Brotogeris versicolurus":    "White-winged Parakeet",
  "Brotogeris jugularis":       "Orange-chinned Parakeet",
  "Graydidascalus brachyurus":  "Short-tailed Parrot",
  "Hapalopsittaca amazonina":   "Rusty-faced Parrot",
  "Hapalopsittaca pyrrhops":    "Red-faced Parrot",
  "Touit batavicus":            "Lilac-tailed Parrotlet",
  "Nannopsittaca panychlora":   "Tepui Parrotlet",
  "Bolborhynchus lineola":       "Barred Parakeet",
  "Bolborhynchus ferrugineifrons": "Rusty-fronted Parakeet",
  "Psilopsiagon aymara":        "Grey-hooded Parakeet",
  "Enicognathus ferrugineus":   "Austral Parakeet",
  "Enicognathus leptorhynchus": "Slender-billed Parakeet",
  "Alipiopsitta xanthops":      "Yellow-faced Parrot",
  "Leptosittaca branickii":     "Golden-plumed Parakeet",
  "Ognorhynchus icterotis":     "Yellow-eared Parrot",
  "Guarouba guarouba":          "Golden Parakeet",
  "Diopsittaca nobilis":        "Red-shouldered Macaw",
  "Orthopsittaca manilatus":    "Red-bellied Macaw",
  "Primolius maracana":         "Blue-winged Macaw",
  "Primolius couloni":          "Blue-headed Macaw",
  "Primolius auricollis":       "Yellow-collared Macaw",
  "Anodorhynchus hyacinthinus": "Hyacinth Macaw",
  "Anodorhynchus leari":        "Indigo Macaw",
  "Anodorhynchus glaucus":      "Glaucous Macaw",
  "Cyanopsitta spixii":         "Spix's Macaw",
  "Rhynchopsitta pachyrhyncha": "Thick-billed Parrot",
  "Rhynchopsitta terrisi":      "Maroon-fronted Parrot",
};

const LINEAGE_BY_GENUS: Record<string, string> = {
  Ara:              "Macaws",
  Anodorhynchus:    "Macaws",
  Cyanopsitta:      "Macaws",
  Primolius:        "Macaws",
  Orthopsittaca:    "Macaws",
  Diopsittaca:      "Macaws",
  Psittacus:        "African grey parrots",
  Poicephalus:      "African parrots",
  Amazona:          "Amazon parrots",
  Alipiopsitta:     "Amazon parrots",
  Aratinga:         "Conures",
  Pyrrhura:         "Conures",
  Enicognathus:     "Conures",
  Leptosittaca:     "Conures",
  Ognorhynchus:     "Conures",
  Guarouba:         "Conures",
  Eupsittula:       "Conures",
  Thectocercus:     "Conures",
  Psittacara:       "Conures",
  Myiopsitta:       "Quaker parrots",
  Melopsittacus:    "Budgerigars",
  Agapornis:        "Lovebirds",
  Forpus:           "Parrotlets",
  Nannopsittaca:    "Parrotlets",
  Touit:            "Parrotlets",
  Bolborhynchus:    "Parrotlets",
  Psilopsiagon:     "Parrotlets",
  Eclectus:         "Eclectus parrots",
  Deroptyus:        "Hawk-headed parrots",
  Pionus:           "Pionus parrots",
  Pionites:         "Caiques",
  Brotogeris:       "Brotogeris parakeets",
  Graydidascalus:   "Short-tailed parrots",
  Hapalopsittaca:   "Hapalopsittaca",
  Rhynchopsitta:    "Rhynchopsitta",
};

const CONTINENTS: Record<string, string[]> = {
  "Psittacus erithacus":        ["Africa"],
  "Psittacus timneh":           ["Africa"],
  "Ara ararauna":               ["South America"],
  "Ara macao":                  ["South America", "North America"],
  "Ara chloropterus":           ["South America"],
  "Ara severus":                ["South America"],
  "Ara militaris":              ["South America"],
  "Ara ambiguus":               ["South America", "North America"],
  "Amazona aestiva":            ["South America"],
  "Amazona ochrocephala":       ["South America", "North America"],
  "Amazona amazonica":          ["South America"],
  "Amazona autumnalis":         ["South America", "North America"],
  "Amazona farinosa":           ["South America", "North America"],
  "Amazona ventralis":          ["North America"],
  "Amazona leucocephala":       ["North America"],
  "Amazona viridigenalis":      ["North America"],
  "Aratinga nenday":            ["South America"],
  "Aratinga solstitialis":      ["South America"],
  "Aratinga jandaya":           ["South America"],
  "Aratinga auricapillus":      ["South America"],
  "Aratinga weddellii":         ["South America"],
  "Pyrrhura molinae":           ["South America"],
  "Pyrrhura frontalis":         ["South America"],
  "Pyrrhura perlata":           ["South America"],
  "Pyrrhura leucotis":          ["South America"],
  "Pyrrhura picta":             ["South America"],
  "Myiopsitta monachus":        ["South America"],
  "Melopsittacus undulatus":    ["Australia"],
  "Agapornis roseicollis":      ["Africa"],
  "Agapornis personatus":       ["Africa"],
  "Agapornis fischeri":         ["Africa"],
  "Agapornis pullarius":        ["Africa"],
  "Agapornis lilianae":         ["Africa"],
  "Agapornis nigrigenis":       ["Africa"],
  "Forpus passerinus":          ["South America"],
  "Forpus coelestis":           ["South America"],
  "Forpus xanthops":            ["South America"],
  "Forpus conspicillatus":      ["South America"],
  "Poicephalus senegalus":      ["Africa"],
  "Poicephalus meyeri":         ["Africa"],
  "Poicephalus rufiventris":    ["Africa"],
  "Poicephalus gulielmi":       ["Africa"],
  "Poicephalus robustus":       ["Africa"],
  "Eclectus roratus":           ["Asia", "Australia", "Oceania"],
  "Deroptyus accipitrinus":     ["South America"],
  "Pionus menstruus":           ["South America"],
  "Pionus maximiliani":         ["South America"],
  "Pionus senilis":             ["South America"],
  "Pionus sordidus":            ["South America"],
  "Pionites leucogaster":       ["South America"],
  "Pionites melanocephalus":    ["South America"],
  "Brotogeris chiriri":         ["South America"],
  "Brotogeris versicolurus":    ["South America"],
  "Brotogeris jugularis":       ["South America", "North America"],
  "Graydidascalus brachyurus":  ["South America"],
  "Hapalopsittaca amazonina":   ["South America"],
  "Hapalopsittaca pyrrhops":    ["South America"],
  "Touit batavicus":            ["South America"],
  "Nannopsittaca panychlora":   ["South America"],
  "Bolborhynchus lineola":       ["South America"],
  "Bolborhynchus ferrugineifrons": ["South America"],
  "Psilopsiagon aymara":        ["South America"],
  "Enicognathus ferrugineus":   ["South America"],
  "Enicognathus leptorhynchus": ["South America"],
  "Alipiopsitta xanthops":      ["South America"],
  "Leptosittaca branickii":     ["South America"],
  "Ognorhynchus icterotis":     ["South America"],
  "Guarouba guarouba":          ["South America"],
  "Diopsittaca nobilis":        ["South America"],
  "Orthopsittaca manilatus":    ["South America"],
  "Primolius maracana":         ["South America"],
  "Primolius couloni":          ["South America"],
  "Primolius auricollis":       ["South America"],
  "Anodorhynchus hyacinthinus": ["South America"],
  "Anodorhynchus leari":        ["South America"],
  "Anodorhynchus glaucus":      ["South America"],
  "Cyanopsitta spixii":         ["South America"],
  "Rhynchopsitta pachyrhyncha": ["North America"],
  "Rhynchopsitta terrisi":      ["North America"],
};

interface ApiRecord {
  id: string;
  usage: {
    id: string;
    parentId?: string;
    status: string;
    extinct: boolean;
    name: {
      scientificName: string;
      rank: string;
    };
  };
}

interface TreeNode {
  id: string;
  name: string;
  rank: string;
  commonName?: string;
  lineage?: string;
  subspeciesCount?: number;
  continents?: string[];
  description?: string;
  children?: TreeNode[];
}

async function findFamilyId(familyName: string): Promise<string> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?q=${encodeURIComponent(familyName)}&rank=family&limit=20`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[] };
  const match = json.result.find(r =>
    r.usage.name.scientificName === familyName &&
    r.usage.status === "accepted"
  );
  if (!match) throw new Error(`${familyName} not found in COL dataset ${DATASET}`);
  console.log(`Found ${familyName} → ID: ${match.id}`);
  return match.id;
}

async function fetchPage(rootId: string, offset: number, limit = 500): Promise<{ records: ApiRecord[]; total: number }> {
  const url = `${COL_API}/dataset/${DATASET}/nameusage/search?TAXON_ID=${rootId}&limit=${limit}&offset=${offset}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  const json = await res.json() as { result: ApiRecord[]; total: number };
  return { records: json.result, total: json.total };
}

async function fetchAll(rootId: string): Promise<ApiRecord[]> {
  const records: ApiRecord[] = [];
  const { records: first, total } = await fetchPage(rootId, 0);
  records.push(...first);
  console.log(`Total: ${total} taxa, batch 1: ${first.length}`);
  for (let offset = first.length; offset < total; offset += 500) {
    const { records: page } = await fetchPage(rootId, offset);
    records.push(...page);
    console.log(`  fetched ${records.length}/${total}`);
  }
  return records;
}

function buildTree(records: ApiRecord[], rootId: string): TreeNode {
  const byId = new Map<string, TreeNode>();

  for (const r of records) {
    const u = r.usage;
    if (u.extinct) continue;
    if (u.status !== "accepted") continue;
    const sciName = u.name.scientificName;
    const rank = u.name.rank.toUpperCase();
    const genus = sciName.split(" ")[0];
    const node: TreeNode = {
      id: r.id,
      name: sciName,
      rank,
      ...(COMMON_NAMES[sciName] && { commonName: COMMON_NAMES[sciName] }),
      ...(LINEAGE_BY_GENUS[genus] && { lineage: LINEAGE_BY_GENUS[genus] }),
      ...(CONTINENTS[sciName] && { continents: [...CONTINENTS[sciName]] }),
    };
    byId.set(r.id, node);
  }

  const subspeciesCounts = new Map<string, number>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (u.name.rank.toUpperCase() === "SUBSPECIES" && u.parentId) {
      subspeciesCounts.set(u.parentId, (subspeciesCounts.get(u.parentId) ?? 0) + 1);
    }
  }
  for (const [id, count] of subspeciesCounts) {
    const node = byId.get(id);
    if (node) node.subspeciesCount = count;
  }

  const childrenMap = new Map<string, TreeNode[]>();
  for (const r of records) {
    const u = r.usage;
    if (u.extinct || u.status !== "accepted") continue;
    if (!u.parentId) continue;
    const node = byId.get(r.id);
    if (!node) continue;
    const siblings = childrenMap.get(u.parentId) ?? [];
    siblings.push(node);
    childrenMap.set(u.parentId, siblings);
  }

  function attach(node: TreeNode): TreeNode {
    const kids = childrenMap.get(node.id);
    if (kids && kids.length > 0) {
      node.children = kids.map(attach).sort((a, b) => a.name.localeCompare(b.name));
    }
    if (node.rank === "SPECIES" && !node.description) {
      const parts = node.name.split(" ");
      const genus = parts[0];
      const epithet = parts.slice(1).join(" ");
      const lineage = node.lineage ?? "parrot";
      node.description = `${genus} ${epithet} is a ${lineage} species native to ${(node.continents ?? ["its native range"]).join(", ")} regions.`;
    }
    return node;
  }

  const root = byId.get(rootId);
  if (!root) throw new Error(`Psittacidae root not found: ${rootId}`);
  return attach(root);
}

function countLeaves(node: TreeNode): number {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

async function main() {
  console.log("Fetching Psittacidae taxonomy from COL ChecklistBank...");
  const FAMILY_ID = await findFamilyId("Psittacidae");
  const records = await fetchAll(FAMILY_ID);
  console.log(`Fetched ${records.length} records total`);

  const tree = buildTree(records, FAMILY_ID);
  const leaves = countLeaves(tree);
  console.log(`Total leaves: ${leaves}`);

  const genera = tree.children?.map(c => `${c.name} (${countLeaves(c)} leaves)`).join(", ");
  console.log(`Genera: ${genera}`);

  const outPath = join(import.meta.dirname, "../src/data/psittacidae.json");
  writeFileSync(outPath, JSON.stringify(tree, null, 2));
  console.log(`Written → ${outPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
