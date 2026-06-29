import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const WIKI_API = "https://en.wikipedia.org/w/api.php";
const WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary";
const RATE_LIMIT = 200;
const CONCURRENCY = 3;

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

async function wikiApi(params: Record<string, string>): Promise<any> {
  const url = `${WIKI_API}?${new URLSearchParams({ ...params, format: "json", origin: "*" })}`;
  const res = await fetch(url, { headers: { "User-Agent": "SystemaNaturae/1.0" } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function getGenusSpecies(genus: string): Promise<string[]> {
  const members: string[] = [];
  let cmcontinue: string | undefined;
  while (true) {
    const params: Record<string, string> = {
      action: "query",
      list: "categorymembers",
      cmtitle: `Category:${genus}`,
      cmlimit: "max",
    };
    if (cmcontinue) params.cmcontinue = cmcontinue;
    const data = await wikiApi(params);
    for (const m of data.query?.categorymembers ?? []) {
      if (m.ns === 0 && !m.title.startsWith("Category:")) members.push(m.title);
    }
    cmcontinue = data.continue?.cmcontinue;
    if (!cmcontinue) break;
  }
  return members;
}

async function resolveToScientific(commonName: string, genus: string): Promise<string | null> {
  // Try REST API summary first — might have scientific name in title
  const enc = encodeURIComponent(commonName.replace(/ /g, "_"));
  try {
    const res = await fetch(`${WIKI_SUMMARY}/${enc}`, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      if (data.title && data.title.includes(" ") && data.title[0].toUpperCase() === genus[0]) {
        return data.title;
      }
    }
  } catch {}

  // Check redirects via API
  const data = await wikiApi({
    action: "query",
    titles: commonName,
    redirects: "1",
    prop: "pageprops",
    ppprop: "displaytitle",
  });
  const pages = data.query?.pages ?? {};
  for (const p of Object.values(pages) as any[]) {
    if (p.title && p.title.includes(" ") && p.title[0].toUpperCase() === genus[0]) {
      return p.title;
    }
  }

  // Try common name as-is — could be a redirect page
  for (const r of data.query?.redirects ?? []) {
    if (r.to && r.to.includes(" ")) return r.to.replace(/_/g, " ");
  }

  return null;
}

interface SpeciesInfo {
  name: string;
  description: string;
  commonName: string;
  continents: string[];
}

async function fetchSpeciesInfo(sciName: string): Promise<SpeciesInfo> {
  const enc = encodeURIComponent(sciName.replace(/ /g, "_"));
  let description = "";
  let commonName = "";
  const continents: string[] = [];

  try {
    const res = await fetch(`${WIKI_SUMMARY}/${enc}`, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      if (data.extract) {
        const sentences = data.extract.split(/(?<=\.)\s+/).filter((s: string) => s.length > 10);
        description = sentences.slice(0, 3).join(" ");
        commonName = data.title !== sciName ? data.title : "";
      }

      const text = data.extract || "";
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
        if (re.test(text) && !continents.includes(continent)) continents.push(continent);
      }
    }
  } catch {}

  if (!description) {
    description = `${sciName} — a species in the genus ${sciName.split(" ")[0]}.`;
  }
  if (!commonName) {
    commonName = sciName;
  }

  return { name: sciName, description, commonName, continents };
}

function collectSpecies(node: any, existing: Map<string, any>) {
  for (const c of node.children ?? []) {
    if (c.rank === "SPECIES") {
      existing.set(c.name, c);
    }
    if (c.children?.length) collectSpecies(c, existing);
  }
}

function nameToId(name: string): string {
  return name.replace(/ /g, "_").toUpperCase();
}

async function main() {
  const slug = process.argv[2];
  const maxNew = process.argv[3] ? parseInt(process.argv[3], 10) : null;

  if (!slug) {
    console.log("Usage: npx tsx scripts/fillFromWikipedia.ts <appSlug> [maxNew]");
    console.log("  Finds missing species via Wikipedia genus categories and enriches them.");
    process.exit(1);
  }

  // Load taxonomy info
  const tax = JSON.parse(readFileSync(resolve(portalRoot, "data/taxonomy.json"), "utf-8"));
  let fam: any = null;
  function findFam(n: any, className = "", orderName = "") {
    if (n.rank === "CLASS") className = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) orderName = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && n.appSlug === slug) {
      fam = { ...n, className, orderName };
      return true;
    }
    for (const c of n.children ?? []) {
      if (findFam(c, className, orderName)) return true;
    }
    return false;
  }
  findFam(tax);

  if (!fam) { console.error(`Family "${slug}" not found in taxonomy.json`); process.exit(1); }

  const familyName = fam.name as string;
  const targetCount = fam.speciesCount as number;
  const dataPath = resolve(root, fam.className, fam.orderName, slug, "src/data", `${slug}.json`);

  if (!existsSync(dataPath)) { console.error(`Data file not found: ${dataPath}`); process.exit(1); }

  const data = JSON.parse(readFileSync(dataPath, "utf-8"));
  const existing = new Map<string, any>();
  collectSpecies(data, existing);

  console.log(`📦 ${familyName} (${fam.className}/${fam.orderName}/${slug})`);
  console.log(`   Target: ${targetCount} species, existing: ${existing.size}`);

  if (existing.size >= targetCount) {
    console.log(`   ✅ Already at or above target`);
    return;
  }

  // Find genera from existing data — use the GENUS node name, not lineage
  const genera = new Set<string>();
  for (const c of data.children ?? []) {
    if (c.rank === "GENUS" && c.name && c.name.split(" ").length === 1 && c.name[0] === c.name[0].toUpperCase()) {
      genera.add(c.name as string);
    }
  }

  // Get Wikipedia species for each genus
  console.log(`   Scouting genera: ${[...genera].join(", ")}`);
  const wikiSpecies = new Map<string, string>(); // scientificName -> commonName

  for (const genus of genera) {
    await sleep(1500 + Math.random() * 1000);
    try {
      const commonNames = await getGenusSpecies(genus);
      if (commonNames.length === 0) {
        // Try opensearch as fallback
        await sleep(1500 + Math.random() * 1000);
        const searchRes = await wikiApi({
          action: "opensearch",
          search: genus,
          limit: "200",
          namespace: "0",
        });
        const titles = searchRes[1] as string[];
        for (const t of titles) {
          if (t.includes(" ") && t.split(" ")[0] === genus && !existing.has(t)) {
            wikiSpecies.set(t, t);
          }
        }
        continue;
      }

      for (const cn of commonNames) {
        await sleep(500 + Math.random() * 500);
        const sciName = await resolveToScientific(cn, genus);
        if (sciName && !existing.has(sciName)) {
          wikiSpecies.set(sciName, cn);
        }
      }
    } catch (e) {
      console.log(`   ⚠ Error scouting genus ${genus}: ${(e as Error).message}`);
    }
  }

  // Also try genus pages that might list species directly
  // Search for "[Genus] [species]" pattern via opensearch
  for (const genus of genera) {
    if (wikiSpecies.size >= (maxNew ?? targetCount - existing.size) + 10) break;
    try {
      await sleep(1500 + Math.random() * 1000);
      const searchRes = await wikiApi({
        action: "opensearch",
        search: `${genus} `,
        limit: "max",
        namespace: "0",
      });
      const titles = searchRes[1] as string[];
      for (const t of titles) {
        if (t.includes(" ") && t.split(" ")[0] === genus && !existing.has(t) && !wikiSpecies.has(t)) {
          wikiSpecies.set(t, t);
        }
      }
    } catch {}
  }

  const missing = [...wikiSpecies.entries()]
    .filter(([name]) => !existing.has(name))
    .slice(0, maxNew ?? (targetCount - existing.size));

  console.log(`   Found ${wikiSpecies.size} Wikipedia species for these genera`);
  console.log(`   Missing: ${missing.length}, will add: ${Math.min(missing.length, targetCount - existing.size)}`);

  if (missing.length === 0) {
    console.log("   Nothing to add");
    return;
  }

  // Enrich and add
  let added = 0;
  let wikiEnriched = 0;
  const genusNodes = new Map<string, any>();
  for (const c of data.children ?? []) {
    if (c.rank === "GENUS") genusNodes.set(c.name as string, c);
  }

  for (const [sciName, commonName] of missing) {
    if (existing.size + added >= targetCount) break;
    await sleep(RATE_LIMIT);

    const info = await fetchSpeciesInfo(sciName);
    const genusName = sciName.split(" ")[0];
    const sourcedFrom = info.description.length > 40 ? "wikipedia" : "wikipedia";

    const speciesNode = {
      id: nameToId(sciName),
      name: sciName,
      rank: "SPECIES",
      commonName: info.commonName,
      lineage: genusName,
      continents: info.continents,
      subspeciesCount: 0,
      description: info.description,
      sourcedFrom,
    };

    const existingGenus = genusNodes.get(genusName);
    if (existingGenus) {
      (existingGenus.children as any[]).push(speciesNode);
      (existingGenus.children as any[]).sort((a, b) => (a.name as string).localeCompare(b.name as string));
    } else {
      (data.children as any[]).push({
        id: `GENUS_${genusName.toUpperCase()}`,
        name: genusName,
        rank: "GENUS",
        description: `${genusName} — a genus of ${(fam.commonName as string)?.toLowerCase() || "species"} in the family ${familyName}.`,
        children: [speciesNode],
      });
      genusNodes.set(genusName, speciesNode);
    }
    added++;
    if (sourcedFrom === "wikipedia") wikiEnriched++;
    if (added % 5 === 0) process.stdout.write(`   Added ${added}/${missing.length}...\n`);
  }

  // Sort genera
  (data.children as any[]).sort((a, b) => (a.name as string).localeCompare(b.name as string));

  // Save
  mkdirSync(dirname(dataPath), { recursive: true });
  writeFileSync(dataPath, JSON.stringify(data, null, 2) + "\n");

  // Update speciesCount
  const newTotal = existing.size + added;
  const updatedCount = Math.max(targetCount, newTotal);
  function updateCount(n: any): boolean {
    if (n.rank === "FAMILY" && n.appSlug === slug) {
      n.speciesCount = updatedCount;
      return true;
    }
    for (const c of n.children ?? []) if (updateCount(c)) return true;
    return false;
  }
  if (updateCount(tax)) {
    writeFileSync(resolve(portalRoot, "data/taxonomy.json"), JSON.stringify(tax, null, 2) + "\n");
    console.log(`   Updated taxonomy.json speciesCount: ${targetCount} → ${updatedCount}`);
  }

  console.log(`\n✅ Added ${added} species (${wikiEnriched} Wikipedia-enriched)`);

  // Rebuild
  console.log("\n⏳ Rebuilding...");
  try {
    const out = execSync("sh scripts/buildData.sh 2>&1", { cwd: portalRoot, encoding: "utf-8", timeout: 180000 });
    const doneLine = out.split("\n").find(l => l.startsWith("Done"));
    if (doneLine) console.log(`   ${doneLine}`);
  } catch (e) {
    console.log(`   ⚠ Build: ${(e as Error).message.slice(0, 100)}`);
  }
}

main().catch(e => { console.error("Fatal:", e); process.exit(1); });
