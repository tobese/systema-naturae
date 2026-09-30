#!/usr/bin/env node
// Verify that a built dist/ actually carries the data tiers the app fetches.
//
// Why this exists
// ---------------
// `docker build` replays cached layers. If `COPY . .` comes back "Using cache"
// for a tree that has changed, the build re-runs an OLDER buildData.ts, writes
// an OLDER manifest, and reports success. The image then serves a tree whose
// manifest has no `namesFile`, so the graph falls back or breaks, and the only
// symptom is that the deploy "worked".
//
// That is not hypothetical: it is what happened on 2026-09-29, and the image
// looked fine. Nothing in the build noticed. This script is the thing that
// notices, and the Dockerfile runs it as a build step so a stale-source image
// FAILS the build instead of shipping.
//
// Checks, per kingdom, from kingdom-config.json so this cannot drift from the
// build's own notion of what the six kingdoms are:
//   - skeleton and order manifest exist
//   - orders/, orders-names/, orders-prose/ exist and are non-empty
//   - every manifest entry resolves: file, namesFile, proseDir all exist
//   - orders-nav/ is ABSENT (dropped from the image on purpose)
//   - the manifest carries the tier fields at all - this is the stale-source
//     tell, since a pre-tier manifest has none of them
//
// Usage: node scripts/verifyDist.mjs [distDir]     (default: portal/dist)

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "..");
const dist = resolve(process.argv[2] ?? join(repo, "portal", "dist"));

const config = JSON.parse(readFileSync(join(repo, "portal/data/kingdom-config.json"), "utf8"));

const failures = [];
const warnings = [];
const fail = (msg) => failures.push(msg);
const warn = (msg) => warnings.push(msg);

const bytes = (n) => (n >= 1e9 ? `${(n / 1e9).toFixed(2)} GB` : n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${(n / 1e3).toFixed(1)} kB`);

function dirBytes(path) {
  let total = 0;
  let count = 0;
  const stack = [path];
  while (stack.length) {
    const dir = stack.pop();
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const e of entries) {
      const p = join(dir, e.name);
      if (e.isDirectory()) {
        stack.push(p);
        continue;
      }
      // statSync, not readFileSync: this walks ~30k prose files and reading
      // their contents just to add up bytes would pull gigabytes through the
      // page cache for a number the filesystem already knows.
      try {
        total += statSync(p).size;
        count++;
      } catch {
        /* vanished between readdir and stat; not counted */
      }
    }
  }
  return { total, count };
}

if (!existsSync(dist)) {
  console.error(`dist not found: ${dist}\nRun a build first (npm run build:all).`);
  process.exit(2);
}

const rows = [];
for (const [kingdom, cfg] of Object.entries(config.kingdoms)) {
  const suffix = cfg.dataSuffix ?? "";
  const root = join(dist, "data", "kingdoms", kingdom);

  if (!existsSync(root)) {
    fail(`${kingdom}: no directory ${root}`);
    continue;
  }

  // Build state in a shipped image. It only ever appears in dist/ via the
  // Dockerfile's rsync, because a plain `npm run build:all` never copies
  // portal/data/ - so finding it here means the rsync's exclude is missing.
  // 458MB across the six kingdoms when it last leaked.
  if (existsSync(join(root, ".build-cache"))) {
    const { total } = dirBytes(join(root, ".build-cache"));
    fail(`${kingdom}: .build-cache/ is in dist (${bytes(total)}) - build state, read by nothing at runtime; add --exclude='.build-cache/' to the Dockerfile rsync`);
  }

  const skeleton = join(root, "unified-taxonomy-skeleton.json");
  const manifestPath = join(root, "order-manifest.json");
  if (!existsSync(skeleton)) fail(`${kingdom}: skeleton missing`);
  if (!existsSync(manifestPath)) {
    fail(`${kingdom}: order-manifest.json missing`);
    continue;
  }

  // The stale-source tell: a pre-tier manifest has none of these fields.
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  } catch (err) {
    fail(`${kingdom}: order-manifest.json is not valid JSON (${err.message})`);
    continue;
  }
  // The manifest is { orders: {ID: entry}, familyToOrder: {...} }; only the
  // orders map describes files, and familyToOrder entries legitimately have no
  // "file" - iterating the whole document is what made this report them missing.
  const orders = manifest.orders;
  if (!orders || typeof orders !== "object") {
    fail(`${kingdom}: order manifest has no "orders" map - the source is probably stale (see header)`);
    continue;
  }
  const entries = Object.entries(orders);
  if (entries.length === 0) fail(`${kingdom}: order manifest is empty`);

  let checked = 0;
  let missingNames = 0;
  let noProseDir = 0;
  for (const [id, entry] of entries) {
    if (!entry.file) {
      fail(`${kingdom}/${id}: manifest entry has no "file"`);
      continue;
    }
    if (!existsSync(join(dist, entry.file))) fail(`${kingdom}/${id}: file missing - ${entry.file}`);
    if (!entry.namesFile) missingNames++;
    else if (!existsSync(join(dist, entry.namesFile))) fail(`${kingdom}/${id}: namesFile missing - ${entry.namesFile}`);
    // A per-order proseDir is legitimately absent when the order has no GENUS
    // node to write prose for: 67 of animalia's 383 orders, 57 of them with
    // species, all of it sitting on FAMILY or ORDER because nothing resolved to
    // genus. The client only fetches prose for a genus, so there is nothing to
    // 404. Counted, not failed. That the genus->prose mapping is complete is
    // asserted by scripts/testDataContract.ts, not here.
    if (entry.proseDir && !existsSync(join(dist, entry.proseDir))) noProseDir++;
    checked++;
  }
  if (missingNames) fail(`${kingdom}: ${missingNames}/${entries.length} manifest entries have no namesFile - the source is probably stale (see header)`);

  const tiers = {};
  for (const [name, rel] of [
    ["orders", `orders${suffix}`],
    ["orders-names", `orders-names${suffix}`],
    ["orders-prose", `orders-prose${suffix}`],
    ["orders-nav", `orders-nav${suffix}`],
  ]) {
    const p = join(root, rel);
    if (!existsSync(p)) {
      tiers[name] = null;
      if (name !== "orders-nav") fail(`${kingdom}: tier dir missing - ${rel}/`);
      continue;
    }
    const { total, count } = dirBytes(p);
    tiers[name] = { total, count };
    if (count === 0) fail(`${kingdom}: tier dir empty - ${rel}/`);
    // orders-nav is dropped from the image on purpose, so its absence is the
    // correct state; its presence means the Dockerfile step was skipped.
    if (name === "orders-nav") warn(`${kingdom}: orders-nav${suffix}/ is present in dist (${bytes(total)}) - the Dockerfile drops it; harmless but it bloats the image`);
  }

  rows.push({ kingdom, orders: entries.length, checked, noProseDir, tiers });
}

const pad = (s, n) => String(s).padEnd(n);
console.log(`dist: ${dist}\n`);
console.log(`  ${pad("kingdom", 11)}${pad("orders", 8)}${pad("orders/", 11)}${pad("names/", 11)}${pad("prose/", 11)}${pad("no prose dir", 14)}nav/`);
for (const r of rows) {
  const cell = (t) => (t ? `${bytes(t.total)}` : "-");
  console.log(
    `  ${pad(r.kingdom, 11)}${pad(r.orders, 8)}${pad(cell(r.tiers["orders"]), 11)}${pad(cell(r.tiers["orders-names"]), 11)}${pad(cell(r.tiers["orders-prose"]), 11)}${pad(r.noProseDir, 14)}${cell(r.tiers["orders-nav"])}`,
  );
}
const totalOrders = rows.reduce((a, r) => a + r.orders, 0);
const noProse = rows.reduce((a, r) => a + r.noProseDir, 0);
console.log(`\n  ${totalOrders} order files, all referenced files resolve. ${noProse} orders have no genus and so no per-order prose dir.`);

if (warnings.length) {
  console.log(`\n${warnings.length} warning(s):`);
  for (const w of warnings) console.log(`  ! ${w}`);
}

if (failures.length) {
  console.error(`\nFAILED - ${failures.length} problem(s):`);
  for (const f of failures.slice(0, 25)) console.error(`  x ${f}`);
  if (failures.length > 25) console.error(`  ... and ${failures.length - 25} more`);
  process.exit(1);
}

console.log(`\nOK - ${rows.length} kingdoms, all tiers present and every manifest entry resolves.`);
