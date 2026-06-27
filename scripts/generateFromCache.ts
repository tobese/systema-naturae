import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const CACHE_PATH = resolve(root, "portal", "data", "gbif-cache-hydrozoa.json");
const TAX_PATH = resolve(root, "portal", "data", "taxonomy.json");
const COLOR_PATH = resolve(root, "portal", "src", "colorRegistry.ts");

interface GbifCache {
  speciesByFamily: Record<string, { gbifKey: number; species: Record<string, unknown>[] }>;
}

const cache: GbifCache = JSON.parse(readFileSync(CACHE_PATH, "utf-8"));

function nameToId(name: string): string {
  return "SP_" + name.replace(/[^a-zA-Z0-9]/g, "_").toUpperCase().replace(/_+/g, "_");
}

function parseScientificName(raw: string): string {
  return raw.replace(/\([^)]*\)/g, "").trim();
}

// Order->family mapping from taxonomy.json
const tax = JSON.parse(readFileSync(TAX_PATH, "utf-8"));
function findHydrozoa(tax: any): [string, string, number][] {
  const result: [string, string, number][] = [];
  function walk(node: any, className?: string, orderName?: string) {
    if (!node) return;
    if (node.rank === "CLASS") className = node.name;
    if (node.rank === "ORDER") orderName = node.name;
    if (node.rank === "FAMILY" && node.appSlug && className === "Hydrozoa") {
      const order = orderName || "Unknown";
      const dataPath = resolve(root, "hydrozoa", order.toLowerCase(), node.appSlug, "src", "data", `${node.appSlug}.json`);
      result.push([node.appSlug, order, node.speciesCount]);
    }
    for (const c of (node.children ?? [])) walk(c, className, orderName);
  }
  walk(tax);
  return result;
}

const families = findHydrozoa(tax);
console.log(`Found ${families.length} Hydrozoa families in taxonomy.json\n`);

let done = 0;
let skipped = 0;

for (const [slug, orderName, speciesCount] of families) {
  const dataPath = resolve(root, "hydrozoa", orderName.toLowerCase(), slug, "src", "data", `${slug}.json`);

  if (existsSync(dataPath)) {
    const existing = JSON.parse(readFileSync(dataPath, "utf-8"));
    if (existing.children?.length > 0 || existing.speciesList?.length > 0) {
      skipped++;
      continue;
    }
  }

  // Find in cache — need to match family by name (case-insensitive)
  const cacheKey = Object.keys(cache.speciesByFamily).find(
    k => k.toLowerCase() === slug.toLowerCase()
  );

  if (!cacheKey) {
    // Write empty family
    const dir = resolve(root, "hydrozoa", orderName.toLowerCase(), slug, "src", "data");
    mkdirSync(dir, { recursive: true });
    writeFileSync(dataPath, JSON.stringify({
      id: `FAM_${slug.toUpperCase()}`,
      name: slug.charAt(0).toUpperCase() + slug.slice(1),
      rank: "FAMILY",
      commonName: slug.charAt(0).toUpperCase() + slug.slice(1),
      children: [],
    }, null, 2) + "\n");
    done++;
    process.stdout.write("e");
    continue;
  }

  const info = cache.speciesByFamily[cacheKey];
  const gbifKey = info.gbifKey;
  const rawSpecies = info.species;

  // Group by genus
  const genusMap = new Map<string, Record<string, unknown>[]>();
  for (const sp of rawSpecies) {
    const sciNameRaw = (sp.scientificName as string) || (sp.species as string) || "";
    const sciName = parseScientificName(sciNameRaw);
    const genusName = (sp.genus as string) || sciName.split(" ")[0] || "Unknown";
    if (!sciName || !sciName.includes(" ")) continue;
    if (!genusMap.has(genusName)) genusMap.set(genusName, []);
    genusMap.get(genusName)!.push(sp);
  }

  if (genusMap.size === 0) {
    // Empty family
    done++;
    process.stdout.write("e");
    continue;
  }

  // Build family data
  const children: Record<string, unknown>[] = [];
  for (const [genusName, spp] of genusMap) {
    const speciesChildren: Record<string, unknown>[] = [];
    for (const sp of spp) {
      const sciNameRaw = (sp.scientificName as string) || (sp.species as string) || "";
      const sciName = parseScientificName(sciNameRaw);
      if (!sciName || !sciName.includes(" ")) continue;
      const speciesEpithet = sciName.split(" ").slice(1).join("_") || "sp";

      speciesChildren.push({
        id: nameToId(sciName),
        name: sciName,
        rank: "SPECIES",
        commonName: `${genusName} ${speciesEpithet}`.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
        lineage: genusName,
        subspeciesCount: 0,
        description: `${sciName} — a hydrozoan species in the genus ${genusName}.`,
        sourcedFrom: "generated",
      });
    }

    speciesChildren.sort((a, b) => (a.name as string).localeCompare(b.name as string));

    children.push({
      id: `GENUS_${genusName.toUpperCase()}`,
      name: genusName,
      rank: "GENUS",
      description: `${genusName} — a genus of hydrozoans.`,
      lineage: genusName,
      children: speciesChildren,
    });
  }

  // Write file
  const dir = resolve(root, "hydrozoa", orderName.toLowerCase(), slug, "src", "data");
  mkdirSync(dir, { recursive: true });
  writeFileSync(dataPath, JSON.stringify({
    id: `FAM_${slug.toUpperCase()}`,
    name: slug.charAt(0).toUpperCase() + slug.slice(1),
    rank: "FAMILY",
    commonName: slug.charAt(0).toUpperCase() + slug.slice(1),
    children,
  }, null, 2) + "\n");

  done++;
  if (done % 20 === 0) process.stdout.write(`${done}/${families.length}\n`);
  else process.stdout.write(".");
}

console.log(`\n\n✅ Done: ${done} families generated, ${skipped} skipped (already exist)`);
