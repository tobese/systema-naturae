/**
 * Enrich plant species with Wikipedia data via SQLite DB + live API fallback.
 * Usage: npx tsx scripts/enrichPlantae.ts [--live]
 *
 * Pre-loads the entire Wikipedia plant DB into memory at startup to avoid
 * thousands of per-batch Python subprocess calls.
 */
import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const SQLITE_DB = "/Volumes/WikiDump/wiki-pages-plants.sqlite";
const WIKI_API = "https://en.wikipedia.org/w/api.php";
const BATCH_SIZE = 50;
const DELAY_MS = 1500;

function binomial(n: string): string {
  return n.split(/\s+/).slice(0, 2).join(" ");
}

/** Load entire DB into memory as Map<binomial, {extract, description?}> */
function loadDb(): Map<string, { extract: string; description?: string }> {
  if (!existsSync(SQLITE_DB)) return new Map();
  const script = `
import json, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
rows = db.execute("SELECT title, description, extract FROM pages").fetchall()
print(json.dumps({r[0]: {'description': r[1], 'extract': r[2].strip()} for r in rows if r[2] and len(r[2].strip()) > 20}))
`;
  const r = spawnSync("python3", ["-c", script, SQLITE_DB], { encoding: "utf-8", timeout: 60000 });
  if (r.status !== 0 || !r.stdout.trim()) return new Map();
  const raw = JSON.parse(r.stdout.trim()) as Record<string, { extract: string; description?: string }>;
  const map = new Map<string, { extract: string; description?: string }>();
  for (const [title, val] of Object.entries(raw)) map.set(title.toLowerCase(), val);
  return map;
}

async function fetchLive(names: string[]): Promise<Map<string, { extract: string; description?: string }>> {
  const bins = [...new Set(names.map(binomial).filter(Boolean))];
  const params = new URLSearchParams({
    action: "query", titles: bins.join("|"),
    prop: "extracts", exintro: "1", explaintext: "1",
    exlimit: String(Math.min(bins.length, BATCH_SIZE)),
    redirects: "1", format: "json", origin: "*",
  });
  const res = await fetch(`${WIKI_API}?${params}`, {
    headers: { "User-Agent": "SystemaNaturae/1.0" },
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) return new Map();
  const data: any = await res.json();
  const pages = data.query?.pages ?? {};
  const redirects = new Map<string, string>();
  for (const r of data.query?.redirects ?? []) redirects.set(r.from, r.to);
  for (const r of data.query?.normalized ?? []) if (!redirects.has(r.from)) redirects.set(r.from, r.to);
  const lookup = new Map<string, number>();
  for (const [id, page] of Object.entries(pages)) { const p = page as any; if (!p.missing) lookup.set(p.title, Number(id)); }
  const result = new Map<string, { extract: string; description?: string }>();
  for (const name of names) {
    const bin = binomial(name);
    const resolved = redirects.get(bin) ?? bin;
    const id = lookup.get(resolved);
    if (id == null) continue;
    const p = pages[id] as any;
    if (!p.extract) continue;
    const extract = p.extract.replace(/<[^>]+>/g, "").trim();
    const first = extract.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ");
    result.set(name, {
      extract: first.length > 50 ? first : extract,
      description: p.description?.length < 80 ? p.description : undefined,
    });
  }
  return result;
}

function countSpecies(n: any): number {
  let c = 0;
  if (n.rank === "SPECIES") c++;
  for (const ch of n.children ?? []) c += countSpecies(ch);
  return c;
}

const CLASSES = ["liliopsida", "magnoliopsida"];

function collectFamilyFiles(): string[] {
  const files: string[] = [];
  for (const cls of CLASSES) {
    const d = resolve(root, cls);
    if (!existsSync(d)) continue;
    const r = spawnSync("find", [d, "-name", "*.json", "-path", "*/src/data/*", "-type", "f"], { encoding: "utf-8", timeout: 10000 });
    if (r.status === 0 && r.stdout.trim()) files.push(...r.stdout.trim().split("\n").filter(Boolean));
  }
  return files;
}

async function postProgress(msg: string, pct?: number) {
  try {
    await fetch("http://localhost:9876/progress", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: "plant-enrich-2026-07-05", m: msg, ...(pct !== undefined ? { p: pct } : {}) }),
    });
  } catch {}
}

async function main() {
  const live = process.argv.includes("--live");
  console.log("Loading Wikipedia plant DB into memory...");
  const db = loadDb();
  console.log(`Loaded ${db.size} Wikipedia pages\n`);

  const files = collectFamilyFiles();
  console.log(`Found ${files.length} family files\n`);

  // Pre-scan
  const BINOMIAL_RE = /^[A-Z][a-z]+ [a-z-]+/;
  interface Fam { path: string; name: string; cand: any[]; enriched: number; total: number }
  const families: Fam[] = [];
  let totalCand = 0, totalEnr = 0, totalSpp = 0;

  for (const fp of files) {
    const d = JSON.parse(readFileSync(fp, "utf-8"));
    const total = countSpecies(d);
    totalSpp += total;
    const cand: any[] = [];
    let enr = 0;
    (function walk(n: any) {
      if (n.rank !== "SPECIES") { for (const c of n.children ?? []) walk(c); return; }
      if (n.sourcedFrom === "wikipedia" && (n.description?.length ?? 0) > 40) { enr++; return; }
      if (!BINOMIAL_RE.test(n.name as string)) return;
      cand.push(n);
    })(d);
    if (cand.length > 0 || enr > 0) {
      families.push({ path: fp, name: d.name, cand, enriched: enr, total });
      totalCand += cand.length;
      totalEnr += enr;
    }
  }
  console.log(`Families: ${families.length}, candidates: ${totalCand}, already enriched: ${totalEnr}, total spp: ${totalSpp}`);
  await postProgress(`Pre-scan: ${totalCand} candidates, ${totalEnr} already enriched`);

  // Enrichment
  let ok = 0, fail = 0, api = 0;

  for (let fi = 0; fi < families.length; fi++) {
    const fam = families[fi];
    if (fam.cand.length === 0) continue;

    const data = JSON.parse(readFileSync(fam.path, "utf-8"));
    const nameMap = new Map<string, any>();
    (function walk(n: any) {
      if (n.rank === "SPECIES" && n.name) nameMap.set(n.name, n);
      for (const c of n.children ?? []) walk(c);
    })(data);

    let famOk = 0, famFail = 0;

    // DB lookup (fast - in-memory)
    for (const node of fam.cand) {
      const n = nameMap.get(node.name);
      if (!n) continue;
      const key = binomial(node.name).toLowerCase();
      const r = db.get(key);
      if (r && r.extract?.length > 20) {
        n.description = r.extract;
        n.sourcedFrom = "wikipedia";
        if (r.description) n.commonName = r.description;
        famOk++;
      } else {
        famFail++;
      }
    }

    // Live API fallback for remaining unmatched
    if (live && fam.cand.length > famOk) {
      const remaining = fam.cand.filter(node => {
        const n = nameMap.get(node.name);
        return n && n.sourcedFrom !== "wikipedia";
      });
      for (let i = 0; i < remaining.length; i += BATCH_SIZE) {
        const batch = remaining.slice(i, i + BATCH_SIZE);
        await sleep(DELAY_MS);
        api++;
        const names = batch.map(n => n.name);
        const result = await fetchLive(names);
        for (const node of batch) {
          const r = result.get(node.name);
          const n = nameMap.get(node.name);
          if (!n || !r) continue;
          n.description = r.extract;
          n.sourcedFrom = "wikipedia";
          if (r.description) n.commonName = r.description;
          famOk++;
          famFail = Math.max(0, famFail - 1);
        }
      }
      // Recalc fail count after live
      famFail = fam.cand.length - famOk;
    }

    writeFileSync(fam.path, JSON.stringify(data, null, 2) + "\n");
    ok += famOk; fail += famFail;

    const pct = Math.round((ok / totalCand) * 100);
    const line = `[${fi + 1}/${families.length}] ${fam.name}: +${famOk} enriched, ${famFail} missed, ${fam.enriched} existing (${fam.total} spp) — ${ok}/${totalCand} total (${pct}%)`;
    console.log(line);
    await postProgress(`${fam.name}: +${famOk} enriched`, pct);
  }

  const final = `Done. ${ok} enriched (+${api} API calls), ${fail} failed, ${totalEnr} existing, ${totalSpp} total spp`;
  console.log(`\n${final}`);
  await postProgress(final, 100);
}

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
main().catch(console.error);
