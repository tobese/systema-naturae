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

async function scout(name: string): Promise<ScoutNode> {
  console.log(`\n🔍 Scouting phylum: ${name}`);
  const phylumKey = await getKey(name, "PHYLUM");
  console.log(`   GBIF key: ${phylumKey}`);

  const rootNode: ScoutNode = { name, rank: "PHYLUM", gbifKey: phylumKey, speciesCount: 0, children: [] };

  const classes = await getChildren(phylumKey, "CLASS");
  console.log(`   Found ${classes.length} classes\n`);

  for (const cls of classes) {
    process.stdout.write(`   ${cls.name} (${cls.speciesCount} spp)...`);
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
    process.stdout.write(` ${orders.length} orders\n`);
  }

  return rootNode;
}

async function main() {
  const args = process.argv.slice(2);
  const name = args[0] || "Cnidaria";

  const result = await scout(name);
  const outPath = resolve(root, "portal", "data", `gbif-scout-${name.toLowerCase()}.json`);
  writeFileSync(outPath, JSON.stringify(result, null, 2) + "\n");
  console.log(`\n✅ Scout report saved to data/gbif-scout-${name.toLowerCase()}.json`);

  // Summary
  console.log(`\n📊 ${name} scout summary:\n`);
  let totalFamilies = 0;
  for (const cls of result.children!) {
    let orders = cls.children?.length ?? 0;
    let fams = cls.children?.reduce((s, o) => s + (o.children?.length ?? 0), 0) ?? 0;
    totalFamilies += fams;
    console.log(`  ${cls.name}: ${orders} orders, ${fams} families, ${cls.speciesCount.toLocaleString()} spp`);
  }
  console.log(`\n  Total: ${result.children!.length} classes, ${totalFamilies} families, ${result.speciesCount.toLocaleString()} spp`);
}

main();
