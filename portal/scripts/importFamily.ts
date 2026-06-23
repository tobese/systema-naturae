import { readFileSync, writeFileSync, rmSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");
const portalRoot = resolve(__dirname, "..");

const OLLAMA_URL = "http://localhost:11434/api/chat";
const MODEL = process.env.OLLAMA_MODEL || "qwen2.5:3b";
const OLLAMA_TIMEOUT = 900_000;

interface Species {
  id: string;
  name: string;
  rank: string;
  commonName: string;
  lineage: string;
  continents: string[];
  subspeciesCount: number;
  description: string;
}

interface FamilyNode {
  id: string;
  name: string;
  rank: string;
  commonName: string;
  appSlug: string;
  speciesCount: number;
  className?: string;
  orderName?: string;
}

interface GenusNode {
  id: string;
  name: string;
  rank: string;
  description?: string;
  lineage: string;
  children: Species[];
}

// ---------- helpers ----------

function findFamily(slug: string): FamilyNode | null {
  const tax = JSON.parse(readFileSync(resolve(portalRoot, "data/taxonomy.json"), "utf-8"));
  let cls = "", ord = "";
  function walk(n: Record<string, unknown>): FamilyNode | null {
    if (n.rank === "CLASS") cls = (n.name as string).toLowerCase();
    if (n.rank === "ORDER" && n.name) ord = (n.name as string).toLowerCase();
    if (n.rank === "FAMILY" && (n as Record<string, string>).appSlug === slug) {
      return { ...n as unknown as FamilyNode, className: cls, orderName: ord };
    }
    for (const c of (n.children ?? []) as Record<string, unknown>[]) {
      const r = walk(c);
      if (r) return r;
    }
    return null;
  }
  return walk(tax);
}

function readDataFile(family: FamilyNode): { data: Record<string, unknown>; species: Species[]; existingNames: Set<string>; existingLineages: Set<string>; genera: GenusNode[] } {
  const path = resolve(root, family.className!, family.orderName!, family.appSlug, "src/data", `${family.appSlug}.json`);
  if (!existsSync(path)) return { data: {}, species: [], existingNames: new Set(), existingLineages: new Set(), genera: [] };
  const data = JSON.parse(readFileSync(path, "utf-8")) as Record<string, unknown>;
  const genera: GenusNode[] = [];
  const existingNames = new Set<string>();
  const existingLineages = new Set<string>();

  for (const g of (data.children ?? []) as GenusNode[]) {
    genera.push(g);
    if (g.lineage) existingLineages.add(g.lineage);
    for (const s of (g.children ?? [])) {
      existingNames.add(s.name);
      if (s.lineage) existingLineages.add(s.lineage);
    }
  }

  return { data, species: genera.flatMap(g => g.children ?? []), existingNames, existingLineages, genera };
}

function getColorRegistryLineages(slug: string): Set<string> {
  const reg = readFileSync(resolve(portalRoot, "src/colorRegistry.ts"), "utf-8");
  const slugUpper = slug.toUpperCase();
  const match = reg.match(new RegExp(`const ${slugUpper}_THEME[^;]+lineageColors:\\s*\\{([^}]+)\\}`, "s"));
  if (!match) return new Set();
  const lines: Set<string> = new Set();
  // Extract keys from lineageColors object
  const keyRegex = /"([^"]+)"\s*:/g;
  let m;
  while ((m = keyRegex.exec(match[1])) !== null) lines.add(m[1]);
  return lines;
}

function callOllama(prompt: string, _count: number, temperature = 0.5): string {
  const systemMsg = "You are a taxonomy data generator. Output ONLY a valid JSON array of species objects. No markdown, no explanation, no code fences. Just the raw JSON array.";

  const body = JSON.stringify({
    model: MODEL,
    messages: [
      { role: "system", content: systemMsg },
      { role: "user", content: prompt },
    ],
    stream: false,
    temperature,
  });

  // Write prompt to temp file to avoid shell escaping issues
  const tmpFile = resolve(process.env.HOME ?? "/tmp", ".ollama_prompt.json");
  writeFileSync(tmpFile, body, "utf-8");

  try {
    const result = execSync(
      `curl -s --max-time ${Math.floor(OLLAMA_TIMEOUT / 1000)} -X POST ${OLLAMA_URL} -d @${tmpFile}`,
      { encoding: "utf-8", timeout: OLLAMA_TIMEOUT + 10000 },
    );
    const parsed = JSON.parse(result);
    return parsed.message?.content ?? "";
  } finally {
    try { rmSync(tmpFile); } catch { /* ok */ }
  }
}

function extractJson(text: string): string {
  // Try to find a JSON array with a more flexible approach
  // First: look for ```json or ``` blocks
  let m = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (m) return m[1].trim();

  // Second: find outer [...] bracket pair
  const start = text.indexOf("[");
  const end = text.lastIndexOf("]");
  if (start >= 0 && end > start) return text.slice(start, end + 1);

  // Third: find outer {...} — maybe a single object was returned
  const objStart = text.indexOf('{');
  const objEnd = text.lastIndexOf('}');
  if (objStart >= 0 && objEnd > objStart) return `[${text.slice(objStart, objEnd + 1)}]`;

  return text.trim();
}

function parseSpecies(jsonText: string, existingNames: Set<string>): Species[] {
  const extracted = extractJson(jsonText);
  if (extracted !== jsonText.trim()) {
    console.log(`  📝 Extracted JSON from ${jsonText.length} to ${extracted.length} chars`);
  }

  let arr: Species[];
  try {
    arr = JSON.parse(extracted);
  } catch (e) {
    // Log first 300 chars for debugging
    console.log(`  ⚠  Raw output (first 300 chars): ${jsonText.slice(0, 300)}`);
    throw new Error(`Failed to parse LLM output as JSON: ${(e as Error).message}`);
  }
  if (!Array.isArray(arr)) throw new Error("LLM output is not an array");

  // Filter out duplicates
  const filtered = arr.filter((s, i) => s && s.name && !existingNames.has(s.name));
  console.log(`  📊 ${arr.length} items from LLM, ${arr.length - filtered.length} duplicates filtered`);
  return filtered;
}

function formatId(name: string): string {
  return name.replace(/ /g, "_").toUpperCase();
}

function appendSpecies(data: Record<string, unknown>, newSpecies: Species[], family: FamilyNode) {
  const children = data.children as GenusNode[];
  // Group new species by lineage → genus
  // For simplicity, create a new genus per distinct lineage if it doesn't exist
  const lineageMap = new Map<string, Species[]>();
  for (const s of newSpecies) {
    const gen = s.name.split(" ")[0];
    const key = s.lineage || gen;
    if (!lineageMap.has(key)) lineageMap.set(key, []);
    lineageMap.get(key)!.push(s);
  }

  for (const [lineage, spp] of lineageMap) {
    // Check if a genus with this lineage already exists
    const gen = spp[0].name.split(" ")[0];
    let genus = children.find(g => g.lineage === lineage || g.name === gen);
    if (!genus) {
      const genusId = `GENUS_${gen.toUpperCase()}`;
      genus = {
        id: genusId,
        name: gen,
        rank: "GENUS",
        description: `${gen} — a genus of ${family.commonName.toLowerCase()}.`,
        lineage,
        children: [],
      };
      children.push(genus);
    }
    // Ensure each species has a proper id
    for (const s of spp) {
      if (!s.id) s.id = formatId(s.name);
      s.rank = "SPECIES";
      // Check if name already exists in this genus
      if (!genus.children.some(ex => ex.name === s.name)) {
        genus.children.push(s);
      }
    }
  }
}

function checkColorRegistry(slug: string, newLineages: Set<string>): string[] {
  if (newLineages.size === 0) return [];
  const regLineages = getColorRegistryLineages(slug);
  const warnings: string[] = [];
  for (const lin of newLineages) {
    if (!regLineages.has(lin)) {
      warnings.push(`  ⚠  New lineage "${lin}" not found in colorRegistry for ${slug}
     Add to ${slug.toUpperCase()}_THEME: "${lin}": "#889098"`);
    }
  }
  // Check if the family even has a registry entry
  if (regLineages.size === 0) {
    warnings.push(`  ❌  No ColorTheme found for "${slug}" at all!
     Create const ${slug.toUpperCase()}_THEME and register in COLOR_REGISTRY.`);
  }
  return warnings;
}

// ---------- main ----------

function main() {
  const slug = process.argv[2];
  const requestedCount = process.argv[3] ? parseInt(process.argv[3], 10) : null;

  if (!slug) {
    console.log("Usage: npx tsx scripts/importFamily.ts <appSlug> [count]");
    console.log("  count defaults to the full gap");
    console.log("  Set OLLAMA_MODEL env var to switch model (default: qwen2.5:3b)");
    console.log("  Available: qwen2.5:7b, qwen2.5:3b, llama3.2:3b");
    console.log("  Example: OLLAMA_MODEL=qwen2.5:7b npx tsx scripts/importFamily.ts tyrannidae 30");
    process.exit(1);
  }

  const family = findFamily(slug);
  if (!family) {
    console.error(`❌ Family "${slug}" not found in taxonomy.json`);
    process.exit(1);
  }

  const { data, species, existingNames, existingLineages, genera } = readDataFile(family);
  if (!data.children) data.children = [];

  const currentCount = species.length;
  const gap = family.speciesCount - currentCount;

  if (gap <= 0) {
    console.log(`✅ ${slug}: ${currentCount}/${family.speciesCount} species — no gap to fill`);
    process.exit(0);
  }

  const toGenerate = requestedCount ?? gap;
  console.log(`📦 ${family.name} (${family.className}/${family.orderName}/${family.appSlug})`);
  console.log(`   ${currentCount}/${family.speciesCount} species — gap=${gap}, generating ${Math.min(toGenerate, gap)}`);
  console.log();

  // Build prompt — keep it concise
  const genusSummary = genera.map(g => `${g.name} (${g.children.length} spp)`).join(", ");
  const prompt = `Generate ${Math.min(toGenerate, gap)} new species for ${family.name} (${family.commonName}), Order ${family.orderName}, Class ${family.className}.

Existing genera: ${genusSummary || "none"}
Existing lineages: ${[...existingLineages].join(", ") || "none"}
Target total: ${family.speciesCount}

Return a JSON array where each object has:
- name: scientific name e.g. "Genus epithet"
- commonName: English name
- lineage: one of the existing lineages
- continents: array of full continent names
- subspeciesCount: integer
- description: 2-3 sentence natural history blurb
- id: "GENUS_EPITHET" all caps
- rank: "SPECIES"

${Math.min(toGenerate, gap)} species, valid JSON only. Use genera not yet listed to maximize diversity.`;

  console.log("⏳ Calling Ollama...");
  let jsonText: string;
  try {
    jsonText = callOllama(prompt, Math.min(toGenerate, gap));
  } catch (e) {
    console.error(`❌ Ollama error: ${(e as Error).message}`);
    process.exit(1);
  }

  // Retry with higher temperature if parsing fails
  if (!jsonText.includes("[") || !jsonText.includes("]")) {
    console.log("  ⚠  Response didn't contain a JSON array, retrying with higher temperature...");
    try {
      jsonText = callOllama(prompt, Math.min(toGenerate, gap), 0.9);
    } catch (e) {
      console.error(`❌ Ollama error on retry: ${(e as Error).message}`);
      process.exit(1);
    }
  }

  const newSpecies = parseSpecies(jsonText, existingNames);
  if (newSpecies.length === 0) {
    console.log("⚠  No new species generated (all duplicates?)");
    process.exit(0);
  }

  // Track new lineages for registry check
  const newLineages = new Set<string>();
  for (const s of newSpecies) {
    if (s.lineage && !existingLineages.has(s.lineage)) {
      newLineages.add(s.lineage);
    }
  }

  // Merge into data
  appendSpecies(data, newSpecies, family);

  // Write file
  const outPath = resolve(root, family.className!, family.orderName!, family.appSlug, "src/data", `${family.appSlug}.json`);
  writeFileSync(outPath, JSON.stringify(data, null, 2) + "\n");
  console.log(`✅ Wrote ${newSpecies.length} species to ${outPath}`);

  // Color registry check
  const regWarnings = checkColorRegistry(slug, newLineages);
  if (regWarnings.length > 0) {
    console.log();
    console.log("⚠  ColorRegistry warnings:");
    for (const w of regWarnings) console.log(w);
  }

  // Rebuild
  console.log();
  console.log("⏳ Rebuilding unified taxonomy...");
  try {
    const out = execSync("sh scripts/buildData.sh 2>&1", { cwd: portalRoot, encoding: "utf-8", timeout: 60000 });
    const warnLine = out.split("\n").find(l => l.toLowerCase().includes("warn"));
    if (warnLine) console.log(`  ⚠  ${warnLine}`);
    const doneLine = out.split("\n").find(l => l.startsWith("Done"));
    if (doneLine) console.log(`  ${doneLine}`);
  } catch (e) {
    console.log(`  ⚠  Build issue: ${(e as Error).message.slice(0, 100)}`);
  }

  const newCount = currentCount + newSpecies.length;
  console.log();
  console.log(`📊 ${slug}: ${currentCount} → ${newCount}/${family.speciesCount}`);
  const remaining = family.speciesCount - newCount;
  if (remaining > 0) {
    console.log(`   ${remaining} species still remaining`);
    console.log(`   Run again: npx tsx scripts/importFamily.ts ${slug} ${remaining}`);
  } else {
    console.log(`   ✅ Fully covered!`);
  }
}

main();
