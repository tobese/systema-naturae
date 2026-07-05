import { writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const GBIF_MATCH = "https://api.gbif.org/v1/species/match";
const GBIF_SEARCH = "https://api.gbif.org/v1/species/search";
const RATE_MS = 250;

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

interface ScoutNode {
  name: string;
  rank: string;
  gbifKey: number;
  speciesCount: number;
  children?: ScoutNode[];
}

const PLANT_PHYLA: { name: string; rank: string }[] = [
  { name: "Tracheophyta", rank: "PHYLUM" },
  { name: "Bryophyta", rank: "PHYLUM" },
  { name: "Marchantiophyta", rank: "PHYLUM" },
  { name: "Anthocerotophyta", rank: "PHYLUM" },
  { name: "Chlorophyta", rank: "PHYLUM" },
  { name: "Charophyta", rank: "PHYLUM" },
  { name: "Rhodophyta", rank: "PHYLUM" },
];

async function getKey(name: string, rank: string): Promise<number> {
  const url = `${GBIF_MATCH}?name=${encodeURIComponent(name)}&rank=${rank}&strict=true`;
  const res = await fetch(url);
  const data = await res.json();
  if (data.usageKey && data.matchType !== "HIGHERRANK") return data.usageKey;
  const searchRes = await fetch(`${GBIF_SEARCH}?q=${encodeURIComponent(name)}&rank=${rank}&limit=5`);
  const searchData = await searchRes.json();
  for (const r of (searchData.results ?? [])) {
    if (r.canonicalName?.toLowerCase() === name.toLowerCase() && r.nubKey) return r.nubKey;
  }
  throw new Error(`Could not find ${rank} "${name}"`);
}

async function getChildren(parentKey: number, childRank: string): Promise<{ name: string; key: number; speciesCount: number }[]> {
  const results: { name: string; key: number; speciesCount: number }[] = [];
  let offset = 0;
  const limit = 200;

  while (true) {
    const url = `${GBIF_SEARCH}?higherTaxonKey=${parentKey}&rank=${childRank}&status=ACCEPTED&limit=${limit}&offset=${offset}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.results?.length) break;
    for (const r of data.results) {
      if (r.canonicalName) {
        results.push({ name: r.canonicalName, key: r.nubKey || r.key, speciesCount: r.speciesCount ?? 0 });
      }
    }
    offset += limit;
    if (offset >= (data.count ?? 0)) break;
    await sleep(RATE_MS);
  }

  return results;
}

async function scoutPhylum(name: string): Promise<ScoutNode> {
  console.log(`\n  🔍 Scouting phylum: ${name}`);
  const phylumKey = await getKey(name, "PHYLUM");
  console.log(`     GBIF key: ${phylumKey}`);

  const rootNode: ScoutNode = { name, rank: "PHYLUM", gbifKey: phylumKey, speciesCount: 0, children: [] };

  const classes = await getChildren(phylumKey, "CLASS");
  console.log(`     Found ${classes.length} classes`);

  for (const cls of classes) {
    process.stdout.write(`     ${cls.name} (${cls.speciesCount} spp)...`);
    const orders = await getChildren(cls.key, "ORDER");
    const clsNode: ScoutNode = { name: cls.name, rank: "CLASS", gbifKey: cls.key, speciesCount: cls.speciesCount, children: [] };

    for (const ord of orders) {
      await sleep(RATE_MS);
      const families = await getChildren(ord.key, "FAMILY");
      const ordNode: ScoutNode = { name: ord.name, rank: "ORDER", gbifKey: ord.key, speciesCount: ord.speciesCount, children: [] };

      for (const fam of families) {
        ordNode.children!.push({ name: fam.name, rank: "FAMILY", gbifKey: fam.key, speciesCount: fam.speciesCount });
      }

      ordNode.children!.sort((a, b) => b.speciesCount - a.speciesCount);
      clsNode.children!.push(ordNode);
    }

    clsNode.children!.sort((a, b) => b.speciesCount - a.speciesCount);
    rootNode.children!.push(clsNode);
    console.log(` ${orders.length} orders`);
  }

  return rootNode;
}

async function main() {
  console.log("🌿 Plantae Scout — mapping all plant phyla from GBIF");

  const results: ScoutNode[] = [];

  for (const phylum of PLANT_PHYLA) {
    try {
      const result = await scoutPhylum(phylum.name);

      const outPath = resolve(root, "portal", "data", `gbif-scout-${phylum.name.toLowerCase()}.json`);
      writeFileSync(outPath, JSON.stringify(result, null, 2) + "\n");
      console.log(`     ✅ Saved to data/gbif-scout-${phylum.name.toLowerCase()}.json`);

      results.push(result);
    } catch (err) {
      console.error(`     ❌ Failed to scout ${phylum.name}:`, (err as Error).message);
    }
  }

  // Summary
  console.log("\n\n📊 Plantae scout summary:\n");
  let totalFamilies = 0;
  let totalSpecies = 0;
  for (const result of results) {
    let orders = 0;
    let fams = 0;
    let spp = 0;
    for (const cls of result.children!) {
      orders += cls.children?.length ?? 0;
      fams += cls.children?.reduce((s, o) => s + (o.children?.length ?? 0), 0) ?? 0;
      spp += cls.speciesCount ?? 0;
    }
    totalFamilies += fams;
    totalSpecies += spp;
    console.log(`  ${result.name}: ${result.children!.length} classes, ${orders} orders, ${fams} families, ${spp.toLocaleString()} spp`);
  }
  console.log(`\n  Total: ${results.length} phyla, ${totalFamilies} families, ${totalSpecies.toLocaleString()} spp`);
}

main();
