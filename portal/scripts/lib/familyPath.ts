import { existsSync, statSync } from "fs";
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
