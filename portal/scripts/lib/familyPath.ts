import { existsSync, statSync } from "fs";
import { join } from "path";

/**
 * Where a family's data file lives, in whichever layout the checkout uses.
 *
 * The target layout is
 *
 *     taxonomy/<kingdom>/<phylum>/<class>/<order>/<family>/src/data/<family>.json
 *
 * which is what makes the filesystem agree with what the build already knows:
 * the 258 top-level directories were a flat mix of six kingdoms, so "do not
 * graft plant nodes into the animal tree" was a rule maintained by discipline
 * rather than by the shape of the tree.
 *
 * The legacy layout is
 *
 *     <class>/<order>/<family>/src/data/<family>.json
 *
 * with two irregularities that have to keep working until every family has
 * moved: 24 families sit one level deeper, under a phylum directory that
 * shares a name with its class, and Tardigrada has no CLASS ancestor at all so
 * it lives at `<family>/src/data/` directly.
 *
 * This module exists because that rule was implemented independently in at
 * least six places (buildData.ts, findGaps.ts, importFamily.ts,
 * fetchSpeciesFromApi.ts, bootstrapAnimalPhyla.ts, bootstrapClass.ts), and the
 * Tardigrada case was implemented twice and differently - implicitly in
 * buildData.ts via `.filter(Boolean)`, and explicitly in findGaps.ts with a
 * `hasClass` flag. Divergent copies of a path rule fail silently: a glob that
 * finds nothing returns [], the loop body never runs, and the script reports
 * success having done nothing.
 *
 * So: one place decides, and it reports which layout it used. A caller that
 * sees `layout: "legacy"` can count them; when the count reaches zero the
 * legacy branch goes and every call site gets simpler.
 */

export type FamilyLayout = "kingdom" | "legacy" | "legacy-phylum" | "legacy-root";

export interface FamilyLocation {
  kingdom?: string;
  phylum?: string;
  cls?: string;
  ord?: string;
  slug: string;
}

export interface ResolvedFamily {
  /** Absolute path to <family>.json, or to the family directory if you ask for that. */
  file: string;
  dir: string;
  layout: FamilyLayout;
}

/** Directory names in the source tree are lower-case with underscores. */
export function dirName(rankName: string | undefined | null): string {
  return (rankName || "").toLowerCase().replace(/\s+/g, "_");
}

/**
 * Candidate relative paths, most-preferred first. Every rank is optional
 * because the tree decides: Tardigrada is KINGDOM > PHYLUM > FAMILY with no
 * class and no order, and inventing levels to make the path look uniform would
 * be fabricating taxonomy.
 */
export function candidatePaths(loc: FamilyLocation): { rel: string; layout: FamilyLayout }[] {
  const { kingdom, phylum, cls, ord, slug } = loc;
  const k = dirName(kingdom);
  const p = dirName(phylum);
  const c = dirName(cls);
  const o = dirName(ord);
  const out: { rel: string; layout: FamilyLayout }[] = [];

  // Target layout. Include every variant that omits an absent rank, so a
  // family missing its class or order still resolves.
  if (k) {
    const tails: string[][] = [
      [p, c, o, slug].filter(Boolean),
      [c, o, slug].filter(Boolean),
      [p, o, slug].filter(Boolean),
      [p, c, slug].filter(Boolean),
      [p, slug].filter(Boolean),
      [c, slug].filter(Boolean),
      [slug],
    ];
    for (const t of tails) {
      out.push({ rel: join("taxonomy", k, ...t, "src", "data", `${slug}.json`), layout: "kingdom" });
    }
  }
  // Legacy, phylum-nested: <phylum>/<class>/<order>/<family>
  if (p && c) out.push({ rel: join(p, c, o, slug, "src", "data", `${slug}.json`), layout: "legacy-phylum" });
  // Legacy, standard: <class>/<order>/<family>
  if (c) out.push({ rel: join(c, o, slug, "src", "data", `${slug}.json`), layout: "legacy" });
  // Legacy, classless: <family>/ (Tardigrada)
  out.push({ rel: join(slug, "src", "data", `${slug}.json`), layout: "legacy-root" });
  return out;
}

/** Resolve to an existing file, or the most-preferred path with a warning. */
export function resolveFamilyFile(root: string, loc: FamilyLocation): ResolvedFamily {
  const cands = candidatePaths(loc);
  for (const c of cands) {
    const file = join(root, c.rel);
    if (existsSync(file)) {
      return { file, dir: file.slice(0, file.length - `${loc.slug}.json`.length - 1), layout: c.layout };
    }
  }
  const best = cands[0];
  return {
    file: join(root, best.rel),
    dir: join(root, best.rel).slice(0, join(root, best.rel).length - `${loc.slug}.json`.length - 1),
    layout: best.layout,
  };
}

/** True when the file actually exists - callers that can fail loudly should. */
export function familyFileExists(root: string, loc: FamilyLocation): boolean {
  return candidatePaths(loc).some((c) => existsSync(join(root, c.rel)));
}

/**
 * Identity of a family's source file, for cache invalidation.
 *
 * The layout is part of this on purpose. The build's family cache is keyed on
 * the source file's mtime and size plus its class and order; if a file moves
 * and the key does not change with it, a moved family silently reuses a stale
 * graft - wrong species, no error anywhere.
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
    /* missing; the caller warns */
  }
  return {
    mtimeMs,
    size,
    layout: r.layout,
    phylum: dirName(loc.phylum),
    cls: dirName(loc.cls),
    ord: dirName(loc.ord),
  };
}
