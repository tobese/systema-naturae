import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";

const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";
const DELAY_MS = 2000;

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

async function fetchSummary(sciName: string): Promise<{ commonName: string; description: string; continents: string[]; title: string } | null> {
  const enc = encodeURIComponent(sciName.replace(/ /g, "_"));
  for (let retry = 0; retry < 3; retry++) {
    try {
      const res = await fetch(`${WIKI_SUMMARY}/${enc}`, { signal: AbortSignal.timeout(15000) });
      if (!res.ok) {
        if (res.status === 429) { await sleep(10000); continue; }
        return null;
      }
      const data: any = await res.json();
      if (!data.extract) return null;

      const sentences = data.extract.split(/(?<=\.)\s+/).filter((s: string) => s.length > 10);
      const description = sentences.slice(0, 3).join(" ");
      const extract = data.extract || "";
      const continents: string[] = [];
      const patterns: [RegExp, string][] = [
        [/\bEurope\b/i, "Europe"], [/\b(eurasian|palearctic)\b/i, "Europe"],
        [/\b(Asia|Asian|Siberia|Himalayas?)\b/i, "Asia"],
        [/\b(Africa|African|sub-Saharan|Sahara)\b/i, "Africa"],
        [/\bNorth America|North American|United States|Canada|Mexico\b/i, "North America"],
        [/\bSouth America|South American|Amazon|Andes|Brazil|Argentina\b/i, "South America"],
        [/\bAustralia|Australian|Tasmania\b/i, "Australia"],
        [/\bAntarctic(a|tic)?\b/i, "Antarctica"],
      ];
      for (const [re, continent] of patterns) {
        if (re.test(extract) && !continents.includes(continent)) continents.push(continent);
      }
      return { commonName: data.title !== sciName ? data.title : sciName, description, continents, title: data.title };
    } catch {
      await sleep(5000);
    }
  }
  return null;
}

function nameToId(name: string): string { return name.replace(/ /g, "_").toUpperCase(); }

async function addToFamily(
  dataPath: string,
  taxPath: string,
  missingSpecies: string[],
  targetCount: number,
  slug: string,
  familyName: string
) {
  const data = JSON.parse(readFileSync(dataPath, "utf-8"));

  // Collect existing species names
  const existingNames = new Set<string>();
  function walk(n: any) {
    if (n.rank === "SPECIES") existingNames.add(n.name);
    for (const c of n.children ?? []) walk(c);
  }
  walk(data);

  // Build genus map
  const genusNodes = new Map<string, any>();
  for (const c of data.children ?? []) {
    if (c.rank === "GENUS") genusNodes.set(c.name as string, c);
  }

  const toAdd = missingSpecies.filter(s => !existingNames.has(s)).slice(0, targetCount - existingNames.size);
  if (toAdd.length === 0) { console.log(`   Nothing missing from the list — all already present`); return; }

  let added = 0;
  let wikiOk = 0;

  for (const sciName of toAdd) {
    if (existingNames.size + added >= targetCount) break;
    await sleep(DELAY_MS);

    process.stdout.write(`   Fetching ${sciName}... `);
    const info = await fetchSummary(sciName);
    if (!info) {
      console.log(`no Wikipedia data`);
      continue;
    }

    const genusName = sciName.split(" ")[0];
    const node = {
      id: nameToId(sciName),
      name: sciName,
      rank: "SPECIES",
      commonName: info.commonName,
      lineage: genusName,
      continents: info.continents,
      subspeciesCount: 0,
      description: info.description,
      sourcedFrom: info.description.length > 40 ? "wikipedia" : "generated",
    };

    if (genusNodes.has(genusName)) {
      const g = genusNodes.get(genusName);
      g.children.push(node);
      g.children.sort((a: any, b: any) => a.name.localeCompare(b.name));
    } else {
      const newGenus = {
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus in the family ${familyName}.`,
        children: [node],
      };
      data.children.push(newGenus);
      genusNodes.set(genusName, newGenus);
    }
    added++;
    wikiOk++;
    console.log(`✓ ${info.commonName}`);
  }

  if (added === 0) { console.log(`   No species added`); return; }

  // Sort genera
  data.children.sort((a: any, b: any) => a.name.localeCompare(b.name));

  // Save
  mkdirSync(dirname(dataPath), { recursive: true });
  writeFileSync(dataPath, JSON.stringify(data, null, 2) + "\n");

  // Update taxonomy.json speciesCount
  const newTotal = existingNames.size + added;
  const tax = JSON.parse(readFileSync(taxPath, "utf-8"));
  function updateTax(n: any): boolean {
    if (n.rank === "FAMILY" && n.appSlug === slug) { n.speciesCount = Math.max(n.speciesCount, newTotal); return true; }
    for (const c of n.children ?? []) if (updateTax(c)) return true;
    return false;
  }
  if (updateTax(tax)) writeFileSync(taxPath, JSON.stringify(tax, null, 2) + "\n");

  console.log(`\n✅ Added ${added} species to ${slug}`);
}

async function main() {
  const ROOT = resolve(import.meta.dirname, "..");
  const TAX = resolve(ROOT, "portal/data/taxonomy.json");

  // === Tityridae ===
  console.log("📦 Tityridae");
  const tityridaeMissing = [
    "Schiffornis major", "Schiffornis turdina", "Schiffornis stenorhyncha",
    "Schiffornis veraepacis", "Schiffornis olivacea", "Schiffornis virescens",
    "Schiffornis aenea",
    "Pachyramphus homochrous", "Pachyramphus polychopterus",
    "Pachyramphus albogriseus", "Pachyramphus minor", "Pachyramphus niger",
    "Pachyramphus salvini",
    "Xenopsaris albinucha",
  ];
  await addToFamily(
    resolve(ROOT, "aves/passeriformes/tityridae/src/data/tityridae.json"),
    TAX, tityridaeMissing, 45, "tityridae", "Tityridae"
  );

  // === Vangidae ===
  console.log("\n📦 Vangidae");
  const vangidaeMissing = [
    "Artamella viridis", "Calicalicus madagascariensis", "Calicalicus rufocarpalis",
    "Cyanolanius madagascarinus", "Euryceros prevostii", "Falculea palliata",
    "Hypositta corallirostris", "Leptopterus chabert", "Mystacornis crossleyi",
    "Newtonia amphichroa", "Newtonia archboldi", "Newtonia brunneicauda",
    "Newtonia fanovanae", "Newtonia lavarambo", "Oriolia bernieri",
    "Pseudobias wardi", "Schetba rufa", "Tylas eduardi",
    "Vanga curvirostris", "Xenopirostris damii", "Xenopirostris xenopirostris",
    "Xenopirostris polleni", "Tephrodornis pondicerianus", "Tephrodornis virgatus",
    "Tephrodornis affinis",
  ];
  await addToFamily(
    resolve(ROOT, "aves/passeriformes/vangidae/src/data/vangidae.json"),
    TAX, vangidaeMissing, 40, "vangidae", "Vangidae"
  );

  // === Paradoxornithidae ===
  console.log("\n📦 Paradoxornithidae");
  const paradoxornithidaeMissing = [
    "Chamaea fasciata",
    "Paradoxornis alphonsianus", "Paradoxornis heudei",
    "Paradoxornis nipalensis", "Paradoxornis paradoxus", "Paradoxornis unicolor",
    "Paradoxornis webbianus",
  ];
  await addToFamily(
    resolve(ROOT, "aves/passeriformes/paradoxornithidae/src/data/paradoxornithidae.json"),
    TAX, paradoxornithidaeMissing, 37, "paradoxornithidae", "Paradoxornithidae"
  );

  // === Cinclosomatidae ===
  console.log("\n📦 Cinclosomatidae");
  const cinclosomatidaeMissing = [
    "Cinclosoma alisteri", "Cinclosoma castaneothorax",
  ];
  await addToFamily(
    resolve(ROOT, "aves/passeriformes/cinclosomatidae/src/data/cinclosomatidae.json"),
    TAX, cinclosomatidaeMissing, 12, "cinclosomatidae", "Cinclosomatidae"
  );

  // === Alcippeidae ===
  console.log("\n📦 Alcippeidae");
  await addToFamily(
    resolve(ROOT, "aves/passeriformes/alcippeidae/src/data/alcippeidae.json"),
    TAX, ["Alcippe brunneicauda"], 10, "alcippeidae", "Alcippeidae"
  );

  // === Ommastrephidae ===
  console.log("\n📦 Ommastrephidae");
  await addToFamily(
    resolve(ROOT, "cephalopoda/teuthida/ommastrephidae/src/data/ommastrephidae.json"),
    TAX, ["Todarodes sagittatus"], 30, "ommastrephidae", "Ommastrephidae"
  );

  // === Architeuthidae ===
  console.log("\n📦 Architeuthidae");
  await addToFamily(
    resolve(ROOT, "cephalopoda/teuthida/architeuthidae/src/data/architeuthidae.json"),
    TAX, ["Architeuthis sanctipauli"], 2, "architeuthidae", "Architeuthidae"
  );
}

main().catch(e => console.error("Fatal:", e));
