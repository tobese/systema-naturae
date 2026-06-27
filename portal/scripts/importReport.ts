import { readFileSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "../..");
const portalRoot = join(__dirname, "..");

interface FamilyStat {
  className: string;
  orderName: string;
  appSlug: string;
  name: string;
  speciesCount: number;
  portalCount: number;
  minimalCount: number;
  enrichedCount: number;
  gap: number;
  trueGap: number;
}

interface ImportEvent {
  date: string;
  commit: string;
  message: string;
  families: string[];
  speciesAdded: number;
  speciesRunning: number;
  nodes: number;
}

interface Snapshot {
  phyla: { name: string; classes: number; families: number; species: number; portal: number; enriched: number; }[];
  totals: { phyla: number; classes: number; orders: number; families: number; species: number; portal: number; enriched: number; nodes: number; compressed: number; totalNodes: number; };
  families: { appSlug: string; className: string; orderName: string; name: string; speciesCount: number; portalCount: number; enrichedCount: number; gap: number; }[];
  takenAt: string;
}

// ── helpers ──

function box(title: string, lines: string[], width: number): string {
  const top = "╔" + "═".repeat(width - 2) + "╗";
  const sep = "╠" + "═".repeat(width - 2) + "╣";
  const bot = "╚" + "═".repeat(width - 2) + "╝";
  const titleLine = title ? `║  ${title.padEnd(width - 5)}║` : "";
  const body = lines.map(l => {
    const clean = l.replace(/\033\[[0-9;]*m/g, "");
    const pad = width - 2 - clean.length;
    return pad >= 0 ? `║ ${l}${" ".repeat(pad)}║` : `║ ${clean.slice(0, width - 5)} ║`;
  });
  const parts = [top];
  if (titleLine) parts.push(titleLine, sep);
  parts.push(...body, bot);
  return parts.join("\n");
}

function table(headers: string[], rows: string[][], widths: number[]): string {
  const sepLine = "├" + widths.map(w => "─".repeat(w + 2)).join("┼") + "┤";
  const botLine = "└" + widths.map(w => "─".repeat(w + 2)).join("┴") + "┘";
  const topLine = "┌" + widths.map(w => "─".repeat(w + 2)).join("┬") + "┐";
  function fmtRow(cells: string[], sep: string): string {
    return sep + cells.map((c, i) => " " + c.padEnd(widths[i]) + " ").join("│") + sep;
  }
  const headerLine = fmtRow(headers, "│");
  const body = rows.map(r => fmtRow(r, "│"));
  return [topLine, headerLine, sepLine, ...body, botLine].join("\n");
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n !== 1 ? "s" : ""}`;
}

// ── snapshot logic ──

function takeSnapshot(): Snapshot {
  const tax = JSON.parse(readFileSync(join(portalRoot, "data/taxonomy.json"), "utf-8"));
  const families: FamilyStat[] = JSON.parse(readFileSync(join(portalRoot, "data/gap-report.json"), "utf-8"));

  const buildLogPath = join(portalRoot, "data/build-log.json");
  let nodes = 0, compressed = 0, totalNodes = 0;
  if (existsSync(buildLogPath)) {
    const log = JSON.parse(readFileSync(buildLogPath, "utf-8"));
    nodes = log.physicalNodes ?? 0;
    compressed = log.compressedSpecies ?? 0;
    totalNodes = log.totalNodes ?? 0;
  }

  // Aggregate by phylum via taxonomy tree
  const classToPhylum: Record<string, string> = {};
  function walk(node: any, currentPhylum?: string) {
    if (!node || typeof node !== "object") return;
    if (node.rank === "PHYLUM") currentPhylum = node.name;
    if (node.rank === "CLASS" && currentPhylum) classToPhylum[node.name] = currentPhylum;
    for (const c of (node.children ?? [])) walk(c, currentPhylum);
  }
  walk(tax);

  const phylaMap: Record<string, { name: string; classes: Set<string>; families: Set<string>; species: number; portal: number; enriched: number; }> = {};
  const totalOrders = new Set<string>();

  for (const f of families) {
    const phyName = classToPhylum[f.className] || f.className || "Unknown";
    if (!phylaMap[phyName]) phylaMap[phyName] = { name: phyName, classes: new Set(), families: new Set(), species: 0, portal: 0, enriched: 0 };
    const p = phylaMap[phyName];
    p.classes.add(f.className);
    p.families.add(f.appSlug);
    p.species += f.speciesCount;
    p.portal += f.portalCount;
    p.enriched += f.enrichedCount;
    totalOrders.add(f.orderName);
  }

  const phyla = Object.values(phylaMap).sort((a, b) => b.species - a.species).map(p => ({
    name: p.name,
    classes: p.classes.size,
    families: p.families.size,
    species: p.species,
    portal: p.portal,
    enriched: p.enriched,
  }));

  const totalSpecies = families.reduce((s, f) => s + f.speciesCount, 0);
  const totalPortal = families.reduce((s, f) => s + f.portalCount, 0);
  const totalEnriched = families.reduce((s, f) => s + f.enrichedCount, 0);

  const familySnap = families.map(f => ({
    appSlug: f.appSlug,
    className: f.className,
    orderName: f.orderName,
    name: f.name,
    speciesCount: f.speciesCount,
    portalCount: f.portalCount,
    enrichedCount: f.enrichedCount,
    gap: f.gap,
  }));

  return {
    phyla,
    totals: {
      phyla: phyla.length,
      classes: Object.keys(classToPhylum).length,
      orders: totalOrders.size,
      families: families.length,
      species: totalSpecies,
      portal: totalPortal,
      enriched: totalEnriched,
      nodes,
      compressed,
      totalNodes,
    },
    families: familySnap,
    takenAt: new Date().toISOString(),
  };
}

function delta(a: number, b: number): string {
  const diff = b - a;
  if (diff === 0) return "——";
  const sign = diff > 0 ? "+" : "";
  return `${sign}${diff}`;
}

function printReport(before: Snapshot | null, after: Snapshot) {
  const w = 64;

  // ── Overview box ──
  const current = after;
  const overview = [
    `  ${current.takenAt.slice(0, 10)} ${current.takenAt.slice(11, 19)}`,
    ``,
    `  Phyla:    ${current.totals.phyla}   Classes:   ${current.totals.classes}`,
    `  Orders:   ${current.totals.orders}   Families:  ${current.totals.families}`,
    ``,
    `  Species:  ${current.totals.species.toLocaleString()} known`,
    `  Portal:   ${current.totals.portal.toLocaleString()} imported`,
    `  Enriched: ${current.totals.enriched.toLocaleString()}`,
    `  Gaps:     ${(current.totals.species - current.totals.portal).toLocaleString()}`,
    ``,
    current.totals.totalNodes > 0
      ? `  Nodes:    ${current.totals.nodes.toLocaleString()} phys + ${current.totals.compressed.toLocaleString()} flat`
      : "",
  ].filter(Boolean);

  if (before) {
    const d = (v: keyof typeof before.totals) => delta(before.totals[v], after.totals[v]);
    overview.push(
      ``,
      `  ── Delta ──`,
      `  Phyla:    ${before.totals.phyla} → ${after.totals.phyla} (${d("phyla")})`,
      `  Classes:  ${before.totals.classes} → ${after.totals.classes} (${d("classes")})`,
      `  Orders:   ${before.totals.orders} → ${after.totals.orders} (${d("orders")})`,
      `  Families: ${before.totals.families} → ${after.totals.families} (${d("families")})`,
      `  Species:  ${before.totals.species.toLocaleString()} → ${after.totals.species.toLocaleString()} (${delta(before.totals.species, after.totals.species)})`,
      `  Portal:   ${before.totals.portal.toLocaleString()} → ${after.totals.portal.toLocaleString()} (${delta(before.totals.portal, after.totals.portal)})`,
    );
  }

  console.log("\n" + box("", overview, w) + "\n");

  // ── Per-phylum table ──
  const phylaHeader = ["Phylum", "Cl", "Fa", "Known", "Portal", "Enr", "Gaps", "%"];
  const phylaWidths = [16, 3, 4, 8, 8, 6, 6, 6];
  const phylaRows = current.phyla.map(p => {
    const gaps = p.species - p.portal;
    const pct = p.species === 0 ? 100 : Math.round((p.portal / p.species) * 100);
    return [p.name, String(p.classes), String(p.families), p.species.toLocaleString(), p.portal.toLocaleString(), p.enriched.toLocaleString(), gaps.toLocaleString(), pct + "%"];
  });
  console.log(table(phylaHeader, phylaRows, phylaWidths) + "\n");

  // ── New families detail ──
  if (before) {
    const beforeSet = new Set(before.families.map(f => f.appSlug));
    const newFams = current.families.filter(f => !beforeSet.has(f.appSlug));
    if (newFams.length > 0) {
      const famHeader = ["Family", "Class", "Order", "Known", "Portal", "Gap"];
      const famWidths = [18, 14, 18, 7, 7, 5];
      const famRows = newFams.map(f => [f.name, f.className, f.orderName, String(f.speciesCount), String(f.portalCount), String(f.gap)]);
      console.log("  New families imported:\n");
      console.log(table(famHeader, famRows, famWidths) + "\n");
    }

    // Families where gap changed (informational print, delta handled by --update-log)
    const beforeMap = new Map(before.families.map(f => [f.appSlug, f]));
    const changed = current.families.filter(f => {
      const b = beforeMap.get(f.appSlug);
      return b && (b.speciesCount !== f.speciesCount || b.portalCount !== f.portalCount || b.enrichedCount !== f.enrichedCount);
    });
    if (changed.length > 0) {
      // delta is written to import-log.json via --update-log flag
    }
  }

  // ── Save to build-log for node counts ──
  const buildLog = {
    physicalNodes: current.totals.nodes || 23518,
    compressedSpecies: current.totals.compressed || 133614,
    totalNodes: current.totals.totalNodes || (current.totals.nodes + current.totals.compressed),
  };
  writeFileSync(join(portalRoot, "data/build-log.json"), JSON.stringify(buildLog, null, 2) + "\n");
}

// ── import-log delta writer ──

function updateImportLog(before: Snapshot | null, after: Snapshot) {
  const logPath = join(portalRoot, "data/import-log.json");
  const today = new Date().toISOString().slice(0, 10);

  // Determine delta families: new + changed
  let deltaSlugs: string[] = [];
  if (before) {
    const beforeSet = new Set(before.families.map(f => f.appSlug));
    const beforeMap = new Map(before.families.map(f => [f.appSlug, f]));
    const newFams = after.families.filter(f => !beforeSet.has(f.appSlug)).map(f => f.appSlug);
    const changedFams = after.families.filter(f => {
      const b = beforeMap.get(f.appSlug);
      return b && (b.speciesCount !== f.speciesCount || b.portalCount !== f.portalCount || b.enrichedCount !== f.enrichedCount);
    }).map(f => f.appSlug);
    deltaSlugs = [...new Set([...newFams, ...changedFams])].sort();
  } else {
    // No baseline: treat all families as delta
    deltaSlugs = after.families.map(f => f.appSlug).sort();
  }

  if (deltaSlugs.length === 0) {
    console.log("  No changes to log.\n");
    return;
  }

  // Compute speciesAdded = sum of portalCount for delta families
  const deltaPortal = after.families
    .filter(f => deltaSlugs.includes(f.appSlug))
    .reduce((sum, f) => sum + f.portalCount, 0);

  // Read existing log
  let log: ImportEvent[] = [];
  if (existsSync(logPath)) {
    try {
      log = JSON.parse(readFileSync(logPath, "utf-8"));
    } catch { /* start fresh */ }
  }

  // Find or create today's entry
  const existingIdx = log.findIndex(e => e.date === today);
  if (existingIdx >= 0) {
    // Merge families (dedupe) and recompute speciesAdded for today
    const existing = log[existingIdx];
    const merged = [...new Set([...existing.families, ...deltaSlugs])].sort();
    log[existingIdx].families = merged;
    log[existingIdx].speciesAdded = deltaPortal;
    log[existingIdx].speciesRunning = after.totals.portal;
    log[existingIdx].nodes = after.totals.nodes;
  } else {
    log.push({
      date: today,
      commit: "",
      message: "",
      families: deltaSlugs,
      speciesAdded: deltaPortal,
      speciesRunning: after.totals.portal,
      nodes: after.totals.nodes,
    });
  }

  writeFileSync(logPath, JSON.stringify(log, null, 2) + "\n");
  console.log(`  Updated import-log.json: ${deltaSlugs.length} families on ${today}\n`);
}

// ── main ──

function main() {
  const args = process.argv.slice(2);
  let prevPath = "";
  let savePath = "";
  let updateLog = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--prev" && args[i + 1]) { prevPath = args[i + 1]; i++; }
    if (args[i] === "--save" && args[i + 1]) { savePath = args[i + 1]; i++; }
    if (args[i] === "--update-log") { updateLog = true; }
  }

  const after = takeSnapshot();

  let before: Snapshot | null = null;
  if (prevPath && existsSync(prevPath)) {
    before = JSON.parse(readFileSync(prevPath, "utf-8"));
  }

  printReport(before, after);

  if (savePath) {
    writeFileSync(savePath, JSON.stringify(after, null, 2) + "\n");
    console.log(`  Snapshot saved to ${savePath}\n`);
  }

  if (updateLog) {
    updateImportLog(before, after);
  }
}

main();
