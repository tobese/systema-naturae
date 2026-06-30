import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE = JSON.parse(readFileSync(resolve(root, "portal", "data", "gbif-cache-cephalopoda.json"), "utf-8"));
const TAX = JSON.parse(readFileSync(resolve(root, "portal", "data", "taxonomy.json"), "utf-8"));

const FOSSIL_ORDERS = new Set([
  "Belemnitida","Orthocerida","Ceratitida","Goniatitida","Agoniatitida",
  "Clymeniida","Prolecanitida","Diplobelida","Phylloceratida","Lytoceratida",
  "Ammonitida","Phragmoteuthida","Plectronocerida","Endocerida","Tarphycerida",
  "Oncocerida","Discosorida","Actinocerida","Pseudorthocerida","Ascocerida",
  "Bactritida","Ellesmerocerida","Coleoidea",
]);

function findClass(node: any, id: string): any {
  if (node.id === id) return node;
  for (const c of node.children ?? []) {
    const found = findClass(c, id);
    if (found) return found;
  }
  return null;
}

function makeId(label: string, prefix: string): string {
  return `${prefix}_${label.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase()}`;
}

function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

const existing = findClass(TAX, "CEPHALOPODA");
const existingSlugs = new Set<string>();
function collectSlugs(n: any) {
  if (n.rank === "FAMILY" && n.appSlug) existingSlugs.add(n.appSlug);
  for (const c of n.children ?? []) collectSlugs(c);
}
collectSlugs(existing);

// Group cache by order
const orderMap = new Map<string, Map<string, { name: string; species: any[] }>>();
for (const [famName, info] of Object.entries(CACHE.speciesByFamily)) {
  const first = (info as any).species?.[0];
  const order = first?.order || "";
  if (!order || FOSSIL_ORDERS.has(order)) continue;
  if (!orderMap.has(order)) orderMap.set(order, new Map());
  orderMap.get(order)!.set(famName, { name: famName, species: (info as any).species || [] });
}

const LIVING_ORDERS = ["Bathyteuthida","Idiosepida","Myopsida","Nautilida","Octopoda","Oegopsida","Sepiida","Spirulida","Vampyromorpha"];
const ORDER_DESC: Record<string, string> = {
  Bathyteuthida: "Bathyteuthida — deep-sea squid with small fins and photophores.",
  Idiosepida: "Idiosepida — pygmy squid, the smallest known cephalopods.",
  Myopsida: "Myopsida — inshore squid with eyes covered by a corneal membrane.",
  Nautilida: "Nautilida — shelled cephalopods, the only living externally-shelled cephalopods.",
  Octopoda: "Octopuses — eight-armed cephalopods with no shell.",
  Oegopsida: "Oegopsida — open-ocean squid with exposed eyes.",
  Sepiida: "Sepiida — cuttlefish and bobtail squid.",
  Spirulida: "Spirulida — the ram's horn squid, with an internal coiled shell.",
  Vampyromorpha: "Vampyromorpha — the vampire squid, a deep-sea relic.",
};

let newFamilies = 0;
let newSpecies = 0;

for (const orderName of LIVING_ORDERS) {
  const families = orderMap.get(orderName);
  if (!families) continue;

  // Find or create order in taxonomy
  let orderNode = existing.children.find((c: any) => c.name === orderName);
  if (!orderNode) {
    orderNode = {
      id: makeId(orderName, "CEPHALOPODA"),
      name: orderName,
      rank: "ORDER",
      commonName: orderName,
      description: ORDER_DESC[orderName] || `${orderName} — an order of cephalopods.`,
      children: [],
    };
    existing.children.push(orderNode);
    console.log(`  [NEW ORDER] ${orderName}`);
  }

  for (const [famName, fam] of families) {
    const slug = famName.toLowerCase();
    if (existingSlugs.has(slug)) {
      console.log(`  [SKIP] ${orderName}/${famName} (already exists)`);
      continue;
    }

    // Create data file
    const dirPath = resolve(root, "cephalopoda", orderName.toLowerCase(), slug, "src", "data");
    mkdirSync(dirPath, { recursive: true });

    const genusMap = new Map<string, any[]>();
    for (const sp of fam.species) {
      const sciName = (sp.scientificName || sp.species || "").replace(/\([^)]*\)/g, "").trim();
      const genusName = sp.genus || sciName.split(" ")[0] || "Unknown";
      if (!sciName || !sciName.includes(" ")) continue;
      if (!genusMap.has(genusName)) genusMap.set(genusName, []);
      genusMap.get(genusName)!.push(sp);
    }

    const children: any[] = [];
    for (const [genusName, spp] of genusMap) {
      const speciesChildren = spp
        .map((sp: any) => {
          const sciName = (sp.scientificName || sp.species || "").replace(/\([^)]*\)/g, "").trim();
          if (!sciName || !sciName.includes(" ")) return null;
          const epithet = sciName.split(" ").slice(1).join("_") || "sp";
          return {
            id: nameToId(sciName),
            name: sciName,
            rank: "SPECIES",
            commonName: `${genusName} ${epithet}`.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
            lineage: genusName,
            subspeciesCount: 0,
            description: `${sciName} — a cephalopod species in the genus ${genusName}.`,
            sourcedFrom: "generated",
          };
        })
        .filter(Boolean);
      if (speciesChildren.length === 0) continue;
      speciesChildren.sort((a: any, b: any) => a.name.localeCompare(b.name));
      children.push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of cephalopods.`,
        lineage: genusName,
        children: speciesChildren,
      });
    }

    writeFileSync(
      resolve(dirPath, `${slug}.json`),
      JSON.stringify({
        id: makeId(slug, "FAM"),
        name: famName,
        rank: "FAMILY",
        commonName: famName,
        children,
      }, null, 2) + "\n"
    );

    // Add to taxonomy
    orderNode.children.push({
      id: makeId(famName, "FAM"),
      name: famName,
      rank: "FAMILY",
      commonName: famName,
      appSlug: slug,
      speciesCount: fam.species.length,
    });

    newFamilies++;
    newSpecies += fam.species.length;
    console.log(`  [ADD] ${orderName}/${famName}: ${fam.species.length} spp`);
  }
}

// Save taxonomy
writeFileSync(resolve(root, "portal", "data", "taxonomy.json"), JSON.stringify(TAX, null, 2) + "\n");

console.log(`\n✅ Done: ${newFamilies} new families, ${newSpecies} new species added`);
