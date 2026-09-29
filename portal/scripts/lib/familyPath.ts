import { existsSync, statSync, readFileSync } from "fs";
import { join } from "path";

/**
 * Where a family's data file lives.
 *
 *     taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json
 *
 * This is the only layout. The source tree was moved on 2026-09-28 from a flat
 * 258 top-level directories - a mix of six kingdoms, so which kingdom a family
 * belonged to was recorded nowhere in the filesystem and resolved only at build
 * time from kingdom-config.json. That is why "do not graft plant nodes into the
 * animal tree" was a rule kept by discipline. The path now says it.
 *
 * Every rank is optional because the tree decides, not because this is
 * permissive. Tardigrada is KINGDOM > PHYLUM > FAMILY with no CLASS and no
 * ORDER, and it lives at taxonomy/animalia/tardigrada/. Inventing a class to
 * make the path look uniform would fabricate taxonomy. The candidates below are
 * the shapes the tree can actually produce, and testDataContract.ts asserts
 * that every family's directory matches its rank path exactly.
 *
 * This module exists because the rule was implemented independently in at
 * least six places (buildData.ts, findGaps.ts, importFamily.ts,
 * fetchSpeciesFromApi.ts, bootstrapAnimalPhyla.ts, bootstrapClass.ts) and the
 * Tardigrada case twice and differently. Divergent copies fail silently: a glob
 * that matches nothing returns [], the loop body never runs, and the script
 * reports success having done nothing.
 */

export type FamilyLayout = "kingdom";

export interface FamilyLocation {
  kingdom: string;
  phylum?: string;
  cls?: string;
  ord?: string;
  slug: string;
}

export interface ResolvedFamily {
  file: string;
  dir: string;
  layout: FamilyLayout;
}

/** Directory names in the source tree are lower-case with underscores. */
export function dirName(rankName: string | undefined | null): string {
  return (rankName || "").toLowerCase().replace(/\s+/g, "_");
}

/**
 * Candidate relative paths, most-specific first. Absent ranks are omitted
 * rather than defaulted, so a family without a class or an order still resolves.
 */
export function candidatePaths(loc: FamilyLocation): { rel: string; layout: FamilyLayout }[] {
  const k = dirName(loc.kingdom);
  const p = dirName(loc.phylum);
  const c = dirName(loc.cls);
  const o = dirName(loc.ord);
  const tails: string[][] = [
    [p, c, o, loc.slug],
    [c, o, loc.slug],
    [p, o, loc.slug],
    [p, c, loc.slug],
    [p, loc.slug],
    [c, loc.slug],
    [loc.slug],
  ];
  const seen = new Set<string>();
  const out: { rel: string; layout: FamilyLayout }[] = [];
  for (const t of tails) {
    const segs = t.filter(Boolean);
    if (!segs.length) continue;
    const rel = join("taxonomy", k, ...segs, "src", "data", `${loc.slug}.json`);
    if (!seen.has(rel)) {
      seen.add(rel);
      out.push({ rel, layout: "kingdom" });
    }
  }
  return out;
}

/** Resolve to an existing file, or the most-preferred path when none exists. */
export function resolveFamilyFile(root: string, loc: FamilyLocation): ResolvedFamily {
  for (const c of candidatePaths(loc)) {
    const file = join(root, c.rel);
    if (existsSync(file)) {
      const cut = file.length - `${loc.slug}.json`.length - 1;
      return { file, dir: file.slice(0, cut), layout: c.layout };
    }
  }
  const file = join(root, candidatePaths(loc)[0].rel);
  const cut = file.length - `${loc.slug}.json`.length - 1;
  return { file, dir: file.slice(0, cut), layout: "kingdom" };
}

export function familyFileExists(root: string, loc: FamilyLocation): boolean {
  return candidatePaths(loc).some((c) => existsSync(join(root, c.rel)));
}

/**
 * Identity of a family's source file, for cache invalidation.
 *
 * Layout and phylum are part of this deliberately. The build's family cache is
 * keyed on mtime, size, class and order; when the tree moved, a family that kept
 * a matching key would have silently reused a stale graft - wrong species in
 * the tree, with no error anywhere.
 */
export function familySourceStamp(root: string, loc: FamilyLocation) {
  const r = resolveFamilyFile(root, loc);
  let mtimeMs = 0;
  let size = -1;
  try {
    const st = statSync(r.file);
    mtimeMs = st.mtimeMs;
    size = st.size;
  } catch {
    /* missing; the caller reports it */
  }
  return { mtimeMs, size, layout: r.layout, phylum: dirName(loc.phylum), cls: dirName(loc.cls), ord: dirName(loc.ord) };
}

/**
 * Class-level directory names for a kingdom, read from its taxonomy.
 *
 * Several scripts walked a hard-coded list of class directories wrapped in an
 * `existsSync` guard - ["aves", "mammalia", ..., "tardigrada"] and similar. A
 * guard like that fails in the worst direction: the directory does not exist, so
 * the script skips it, and then reports success having enriched nothing. Under
 * taxonomy/<kingdom>/<phylum>/<class>/ every one of those paths was gone, so
 * those scripts had become no-ops that still exited 0.
 *
 * Reading the list from the taxonomy means it cannot drift again, and it
 * includes the awkward cases for free: a phylum with no CLASS (Tardigrada), and
 * a class that is not a direct child of the kingdom root.
 */
export function classDirsForKingdom(root: string, kingdom: string): string[] {
  const cfgPath = join(root, "portal", "data", "kingdom-config.json");
  if (!existsSync(cfgPath)) return [];
  const cfg = JSON.parse(readFileSync(cfgPath, "utf-8")) as {
    kingdoms?: Record<string, { input?: string }>;
  };
  const input = cfg.kingdoms?.[kingdom]?.input;
  if (!input) return [];
  const treePath = join(root, "portal", input);
  if (!existsSync(treePath)) return [];
  const tree = JSON.parse(readFileSync(treePath, "utf-8")) as {
    children?: { rank?: string; name?: string; children?: unknown[] }[];
  };
  const out = new Set<string>();
  const walk = (n: { rank?: string; name?: string; children?: unknown[] }, parentHasClass: boolean) => {
    if (n?.rank === "CLASS" && n.name) {
      out.add(dirName(n.name));
      for (const c of (n.children ?? []) as typeof n[]) walk(c, true);
    } else if (n?.rank === "PHYLUM" && n.name) {
      // A phylum with a class beneath it contributes the class; one without
      // (Tardigrada) contributes itself.
      const hasClass = containsRank(n.children, "CLASS");
      if (!hasClass) out.add(dirName(n.name));
      for (const c of (n.children ?? []) as typeof n[]) walk(c, parentHasClass || hasClass);
    } else {
      for (const c of (n?.children ?? []) as typeof n[]) walk(c, parentHasClass);
    }
  };
  for (const c of tree.children ?? []) walk(c, false);
  return [...out].sort();
}

function containsRank(nodes: unknown[] | undefined, rank: string): boolean {
  for (const n of (nodes ?? []) as { rank?: string; children?: unknown[] }[]) {
    if (n?.rank === rank) return true;
    if (containsRank(n?.children, rank)) return true;
  }
  return false;
}

/** Every kingdom key declared in kingdom-config.json. */
export function kingdomNames(root: string): string[] {
  const cfgPath = join(root, "portal", "data", "kingdom-config.json");
  if (!existsSync(cfgPath)) return [];
  const cfg = JSON.parse(readFileSync(cfgPath, "utf-8")) as { kingdoms?: Record<string, unknown> };
  return Object.keys(cfg.kingdoms ?? {}).sort();
}
