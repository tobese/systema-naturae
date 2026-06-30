import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "../..")

interface FamilyReport {
  path: string;
  slug: string;
  className: string;
  orderName: string;
  totalSpecies: number;
  wikiReal: number;
  wikiStuck: number;
  wikiShort: number;
  generated: number;
  sampleStuck: string[];
  sampleWiki: string[];
}

function findAllDataFiles(): string[] {
  const out = execSync(
    `find ${root} -path "*/src/data/*.json" -not -path "*/node_modules/*" -type f`,
    { encoding: "utf-8" }
  ).trim();
  return out.split("\n").filter(Boolean);
}

function getClassOrderFromPath(fp: string): [string, string] {
  const rel = fp.replace(root + "/", "");
  const parts = rel.split("/");
  // aves/passeriformes/corvidae/src/data/corvidae.json -> class=aves, order=passeriformes
  return [parts[0] || "?", parts[1] || "?"];
}

function main() {
  const files = findAllDataFiles();
  console.log(`Scanning ${files.length} data files for stuck species...\n`);

  const reports: FamilyReport[] = [];
  let totalWikiStuck = 0;
  let totalWikiReal = 0;
  let totalWikiShort = 0;
  let totalGenerated = 0;
  let totalSpecies = 0;

  for (const fp of files) {
    const [className, orderName] = getClassOrderFromPath(fp);
    const slug = fp.match(/\/([^/]+)\.json$/)?.[1] || "?";
    if (slug === "continents") continue;

    const data = JSON.parse(readFileSync(fp, "utf-8"));

    const report: FamilyReport = {
      path: fp,
      slug,
      className,
      orderName,
      totalSpecies: 0,
      wikiReal: 0,
      wikiStuck: 0,
      wikiShort: 0,
      generated: 0,
      sampleStuck: [],
      sampleWiki: [],
    };

    function walk(n: Record<string, unknown>) {
      if (n.rank === "SPECIES") {
        report.totalSpecies++;
        const src = (n.sourcedFrom as string) || "";
        const desc = (n.description as string) || "";
        const name = (n.name as string) || "";

        if (src === "wikipedia" && desc.length > 20) {
          report.wikiReal++;
          if (report.sampleWiki.length < 3) report.sampleWiki.push(name);
        } else if (src === "wikipedia" && desc.length === 0) {
          report.wikiStuck++;
          if (report.sampleStuck.length < 5) report.sampleStuck.push(name);
        } else if (src === "wikipedia") {
          report.wikiShort++;
          if (report.sampleStuck.length < 5) report.sampleStuck.push(`${name} [len=${desc.length}]`);
        } else {
          report.generated++;
        }
      }
      for (const c of (n.children || []) as Record<string, unknown>[]) walk(c);
    }

    walk(data);

    // Only keep families with issues
    if (report.wikiStuck > 0 || report.wikiShort > 0) {
      reports.push(report);
    }

    totalWikiStuck += report.wikiStuck;
    totalWikiReal += report.wikiReal;
    totalWikiShort += report.wikiShort;
    totalGenerated += report.generated;
    totalSpecies += report.totalSpecies;
  }

  // Sort by most stuck species
  reports.sort((a, b) => b.wikiStuck - b.wikiStuck);

  console.log("=".repeat(90));
  console.log("STUCK SPECIES REPORT");
  console.log("=".repeat(90));
  console.log();
  console.log(`Total species scanned: ${totalSpecies}`);
  console.log(`Wikipedia real (>20 chars): ${totalWikiReal}`);
  console.log(`Wikipedia stuck (empty desc): ${totalWikiStuck}`);
  console.log(`Wikipedia short (1-20 chars): ${totalWikiShort}`);
  console.log(`Generated (no Wikipedia): ${totalGenerated}`);
  console.log();

  console.log("=".repeat(90));
  console.log(`TOP FAMILIES WITH STUCK SPECIES (${reports.length} families with issues)`);
  console.log("=".repeat(90));
  console.log();
  console.log("Family".padEnd(30) + "Class".padEnd(15) + "Total".padStart(6) + "Real".padStart(6) + "Stuck".padStart(6) + "Short".padStart(6) + "Gen".padStart(8) + "  Stuck%");
  console.log("-".repeat(90));

  for (const r of reports.slice(0, 40)) {
    const pct = r.totalSpecies > 0 ? ((r.wikiStuck / r.totalSpecies) * 100).toFixed(1) : "0.0";
    console.log(
      `${r.slug.padEnd(30)} ${r.className.padEnd(15)} ${r.totalSpecies.toString().padStart(6)} ${r.wikiReal.toString().padStart(6)} ${r.wikiStuck.toString().padStart(6)} ${r.wikiShort.toString().padStart(6)} ${r.generated.toString().padStart(8)} ${pct}%`
    );
  }

  // By class summary
  console.log();
  console.log("=".repeat(90));
  console.log("SUMMARY BY CLASS");
  console.log("=".repeat(90));
  console.log();
  const classMap = new Map<string, { families: number; stuck: number; real: number; short: number; gen: number; total: number }>();
  for (const r of reports) {
    const c = r.className;
    if (!classMap.has(c)) classMap.set(c, { families: 0, stuck: 0, real: 0, short: 0, gen: 0, total: 0 });
    const entry = classMap.get(c)!;
    entry.families++;
    entry.stuck += r.wikiStuck;
    entry.real += r.wikiReal;
    entry.short += r.wikiShort;
    entry.gen += r.generated;
    entry.total += r.totalSpecies;
  }

  console.log("Class".padEnd(20) + "Families".padStart(9) + "Total".padStart(8) + "Real".padStart(6) + "Stuck".padStart(6) + "Short".padStart(6) + "Gen".padStart(8) + "  Enrich%");
  console.log("-".repeat(80));
  for (const [cls, data] of [...classMap.entries()].sort((a, b) => b[1].stuck - a[1].stuck)) {
    const e = data.real / data.total * 100;
    console.log(`${cls.padEnd(20)} ${data.families.toString().padStart(9)} ${data.total.toString().padStart(8)} ${data.real.toString().padStart(6)} ${data.stuck.toString().padStart(6)} ${data.short.toString().padStart(6)} ${data.gen.toString().padStart(8)} ${e.toFixed(1)}%`);
  }

  // Save detailed report to file
  const outPath = resolve(root, "portal", "data", "stuck-species-report.json");
  const dataDir = resolve(outPath, "..");
  writeFileSync(outPath, JSON.stringify(
    {
      scannedAt: new Date().toISOString(),
      totalSpecies,
      totalWikiReal,
      totalWikiStuck,
      totalWikiShort,
      totalGenerated,
      families: reports.map((r) => ({
        slug: r.slug,
        class: r.className,
        order: r.orderName,
        total: r.totalSpecies,
        real: r.wikiReal,
        stuck: r.wikiStuck,
        short: r.wikiShort,
        gen: r.generated,
        stuckPct: r.totalSpecies > 0 ? +(r.wikiStuck / r.totalSpecies * 100).toFixed(1) : 0,
        samples: r.sampleStuck,
      })),
    },
    null,
    2
  ) + "\n");
  console.log(`\n✅ Full report saved to portal/data/stuck-species-report.json`);
}

main();