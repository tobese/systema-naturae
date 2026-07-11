import { readFileSync, writeFileSync, readdirSync, statSync } from "fs";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..");

const DRY_RUN = process.argv.includes("--dry-run");

// ── Junk classifier ──────────────────────────────────────────────────────────
function isJunk(name: string, desc: string): boolean {
  if (!desc || desc.trim() === "") return true;
  const d = desc.trim();

  // Template placement: "X — a species in the genus Y, family Z"
  if (/[-—]\s*a[n]?\b[^.]*\bspecies\b[^.]*(genus|family)/i.test(d)) return true;

  // LLM hallucinated filler
  if (/^This species (is|adds|brings|contributes|represents|belongs)/i.test(d)) return true;

  // Name-only: "Abirus fortuneii" or "Abirus fortuneii (Linnaeus, 1758)." or "Abirus fortuneii A."
  // Must start with the scientific name and have nothing meaningful after
  if (name && d.startsWith(name)) {
    const after = d.slice(name.length).trim();
    // Empty, period only: junk
    if (after === "" || after === ".") return true;
    // Authority text only (author, year, period): junk
    // Must match PURE authority: (Author, Year). or Author, Year. — nothing else
    if (/^[(][A-Z][a-z]+(\s+[A-Z][a-z]+)*,\s*\d{4}[).]?$/.test(after) ||
        /^[A-Z][a-z]+(\s+[A-Z][a-z]+)*,\s*\d{4}\.?$/.test(after)) return true;
    // Short capitalized fragment without meaningful biology words: junk
    if (/^[A-Z][a-z]+/.test(after) && after.length < 40 && !/\b(species|genus|family|frog|snail|fish|bird|spider|beetle|moth|crab|worm|shrimp|sponge|coral|plant|herb|tree|shrub|moss|fern|alg|lichen|orchid|orchids|orchidaceae|cichlid|tilapia|herring|sardinella)\b/i.test(after)) return true;
  }

  return false;
}

function isFakeCommonName(name: string, commonName: string): boolean {
  if (!commonName || commonName.trim() === "") return false;
  const cn = commonName.trim();
  // Equals the binomial: "Abirus fortuneii"
  if (cn === name) return true;
  // Title-cased binomial: "Abutiloneus Idoneus"
  if (cn.replace(/\s+/g, " ").toLowerCase() === name.replace(/\s+/g, " ").toLowerCase()) return true;
  // Just a title-cased version of the binomial with no extra info
  if (cn.split(" ").length <= 3 && cn.toLowerCase().startsWith(name.split(" ")[0]?.toLowerCase() || "__")) return true;
  return false;
}

// ── Scan & collect changes ───────────────────────────────────────────────────
interface Change {
  file: string;
  name: string;
  oldDesc: string;
  oldCommon: string;
  oldSource: string;
}

const changes: Change[] = [];
let totalSpecies = 0;
let totalJunk = 0;
let totalReal = 0;
const bySource: Record<string, { junk: number; real: number; total: number }> = {};

function processFile(fullPath: string) {
  try {
    const data = JSON.parse(readFileSync(fullPath, "utf-8"));
    let modified = false;

    function walk(n: Record<string, unknown>) {
      if (n.rank === "SPECIES") {
        totalSpecies++;
        const src = (n.sourcedFrom as string) || "none";
        const name = (n.name as string) || "";
        const desc = (n.description as string) || "";
        const common = (n.commonName as string) || "";

        if (!bySource[src]) bySource[src] = { junk: 0, real: 0, total: 0 };
        bySource[src].total++;

        if (isJunk(name, desc)) {
          totalJunk++;
          bySource[src].junk++;
          changes.push({
            file: fullPath,
            name,
            oldDesc: desc,
            oldCommon: common,
            oldSource: src,
          });
          if (!DRY_RUN) {
            n.description = "";
            if (isFakeCommonName(name, common)) n.commonName = "";
            n.sourcedFrom = "none";
            modified = true;
          }
        } else {
          totalReal++;
          bySource[src].real++;
        }
      }
      for (const c of (n.children ?? []) as Record<string, unknown>[]) walk(c);
    }
    walk(data);

    if (modified && !DRY_RUN) {
      writeFileSync(fullPath, JSON.stringify(data, null, 2) + "\n");
    }
  } catch {}
}

// ── Walk all class directories ───────────────────────────────────────────────
const skip = new Set([
  "portal", "scripts", "docs", "node_modules", ".git", ".github",
  ".claude", ".opencode", ".playwright-mcp", ".vscode",
]);
function walkDir(dir: string) {
  for (const e of readdirSync(dir)) {
    if (skip.has(e)) continue;
    const p = join(dir, e);
    let st;
    try { st = statSync(p); } catch { continue; }
    if (st.isDirectory()) walkDir(p);
    else if (e.endsWith(".json") && p.includes("/src/data/")) processFile(p);
  }
}

console.log(DRY_RUN ? "🔍 DRY RUN — no files modified\n" : "🗑️  STRIPPING junk descriptions...\n");
walkDir(root);

// ── Results ──────────────────────────────────────────────────────────────────
const tot = totalJunk + totalReal;
console.log(`=== ${DRY_RUN ? "DRY RUN" : "DONE"} — Global totals ===`);
console.log(`Total species: ${tot}`);
console.log(`  real:    ${totalReal}  (${(totalReal / tot * 100).toFixed(1)}%)`);
console.log(`  junk:    ${totalJunk}  (${(totalJunk / tot * 100).toFixed(1)}%)`);
if (!DRY_RUN) console.log(`  stripped: ${totalJunk}`);
console.log();

console.log("=== By sourcedFrom ===");
Object.entries(bySource)
  .sort((a, b) => (b[1].total) - (a[1].total))
  .forEach(([src, s]) => {
    console.log(
      `  ${src.padEnd(12)}total:${String(s.total).padStart(7)}  junk:${String(s.junk).padStart(7)}  real:${String(s.real).padStart(7)}`
    );
  });

// ── Samples ──────────────────────────────────────────────────────────────────
if (changes.length > 0) {
  console.log(`\n=== Sample stripped (first 30) ===`);
  changes.slice(0, 30).forEach((c, i) => {
    console.log(`  ${(i + 1).toString().padStart(2)}. [${c.oldSource}] ${c.name}`);
    console.log(`      desc: ${c.oldDesc.slice(0, 90)}${c.oldDesc.length > 90 ? "…" : ""}`);
  });

  const wikiSamples = changes.filter(c => c.oldSource === "wikipedia").slice(0, 20);
  if (wikiSamples.length > 0) {
    console.log(`\n=== Wikipedia entries flagged as junk (${changes.filter(c => c.oldSource === "wikipedia").length} total, first 20) ===`);
    wikiSamples.forEach((c, i) => {
      console.log(`  ${(i + 1).toString().padStart(2)}. ${c.name}`);
      console.log(`      desc: "${c.oldDesc.slice(0, 120)}${c.oldDesc.length > 120 ? "…" : ""}"`);
    });
  }

  for (const src of ["powo", "none"]) {
    const samples = changes.filter(c => c.oldSource === src).slice(0, 10);
    if (samples.length > 0) {
      console.log(`\n=== ${src} entries flagged as junk (${changes.filter(c => c.oldSource === src).length} total, first 10) ===`);
      samples.forEach((c, i) => {
        console.log(`  ${(i + 1).toString().padStart(2)}. ${c.name}`);
        console.log(`      desc: "${c.oldDesc.slice(0, 120)}${c.oldDesc.length > 120 ? "…" : ""}"`);
      });
    }
  }
}
