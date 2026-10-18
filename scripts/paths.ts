// Where downloaded datasets live on the external volume.
//
// The Python side resolves these through scripts/sources.py; this is the same
// index for the TypeScript scripts, which cannot import it. Both read the
// manifest written by scripts/sourcesManifest.py, so relocating a dataset means
// editing the manifest rather than every script that reads it.
//
// `/Volumes/MacieExternal` is a separate disk. If it is not mounted these paths
// do not exist, and a script reading one should say so rather than fail with a
// bare ENOENT on a path that no longer means anything.

import { existsSync, mkdirSync, writeFileSync } from "fs";
import { resolve } from "path";

export const SOURCES_ROOT = "/Volumes/MacieExternal/sources";
const MANIFEST = resolve(SOURCES_ROOT, "manifest.json");

export interface SourceEntry {
  title: string;
  identifier: string;
  url: string;
  licence: string;
  status: "applied" | "partial" | "ready" | "assessed" | "refused";
  took: string;
  archive: { path: string; bytes: number; files: { name: string; bytes: number }[] };
  work: { path: string; bytes: number; files: { name: string; bytes: number }[] };
}

let cache: Record<string, SourceEntry> | null = null;

/** The manifest, or a fatal error naming the likely cause. */
export function sources(): Record<string, SourceEntry> {
  if (cache) return cache;
  if (!existsSync(MANIFEST)) {
    console.error(
      `FATAL: ${MANIFEST} not found.\n` +
      `       The external volume (/Volumes/MacieExternal) looks absent or unmounted.\n` +
      `       Nothing that reads a downloaded dataset can run until it is back.\n` +
      `       Once mounted, regenerate the index with:\n` +
      `         python3 scripts/sourcesManifest.py --verify`,
    );
    process.exit(1);
  }
  cache = JSON.parse(readFileSyncUtf8(MANIFEST)).sources;
  return cache!;
}

function readFileSyncUtf8(p: string): string {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require("fs").readFileSync(p, "utf-8") as string;
}

/** The immutable download directory for `slug`. */
export function archiveDir(slug: string): string {
  const p = resolve(SOURCES_ROOT, "archives", slug);
  if (!existsSync(p)) {
    console.error(`FATAL: no archive on disk for '${slug}' at ${p}\n` +
      `       See manifest.json for its source URL.`);
    process.exit(1);
  }
  return p;
}

/** The derived-artifact directory for `slug`, created if absent. */
export function workDir(slug: string): string {
  sources();
  const p = resolve(SOURCES_ROOT, "work", slug);
  if (!existsSync(p)) mkdirSync(p, { recursive: true });
  return p;
}

/**
 * Write a transformer's output as JSONL into `slug`'s work dir, return the
 * path. See sources.py's `record_transformed` for the full rationale (same
 * function, mirrored for the TypeScript side) -- overwritten on each run,
 * not an audit trail, and picked up automatically next time
 * sourcesManifest.py rescans work/.
 */
export function recordTransformed(slug: string, name: string, records: unknown[]): string {
  const path = resolve(workDir(slug), name);
  const body = records.map((r) => JSON.stringify(r)).join("\n");
  writeFileSync(path, records.length ? body + "\n" : "", "utf-8");
  return path;
}

/** A single derived artifact, erroring clearly if it has not been produced. */
export function workFile(slug: string, name: string): string {
  const p = resolve(workDir(slug), name);
  if (!existsSync(p)) {
    console.error(`FATAL: ${p} does not exist.\n` +
      `       It is a derived artifact of the '${slug}' download and is not kept\n` +
      `       in git. Re-run the script that produces it.`);
    process.exit(1);
  }
  return p;
}
