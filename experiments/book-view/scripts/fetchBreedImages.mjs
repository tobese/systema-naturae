// One-shot: resolves a Wikidata portrait image (P18) for every BREED node in the
// animal kingdom's portal order files, writing a small sidecar
// `shared/data/breed-images.json` keyed by breed display name (e.g. "Persian",
// "Labrador Retriever"). Breeds are common-name based, so they don't belong in
// the scientific-name-keyed wiki-images.json; this file keeps that concern
// separate. The book's extractSlice.ts reads it and merges breed portraits into
// the same per-chapter `images` map as species portraits.
//
// Run (re-runnable - skips names already resolved):
//   node experiments/book-view/scripts/fetchBreedImages.mjs
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "../../..");
const ORDERS_DIR = join(REPO_ROOT, "portal/public/data/kingdoms/animalia/orders");
const OUT_PATH = join(REPO_ROOT, "shared/data/breed-images.json");

const UA = {
  "User-Agent": "SystemaNaturaeDev/1.0 (https://github.com/tobese/systema-naturae; breed-image backfill)",
};

// Single-word breed names collide with languages/cultures in Wikidata label
// search ("Bengal" -> Bengali language). These pin the canonical search query
// that lands on the actual breed item.
const OVERRIDES = {
  Bengal: "Bengal cat",
  "Andalusian (PRE)": "Andalusian horse",
  Cayuga: "Cayuga duck",
  "Doberman Pinscher": "Dobermann",
  Oldenburg: "Oldenburg horse",
  KWPN: "Dutch Warmblood",
  Mondain: "French Mondain",
  Baldwin: "Baldwin guinea pig",
  "Red Wattle": "Red Wattle Hog",
};

// Short breed names ("Boer", "Delaware", "Slate", "King") are hopeless without
// the host species: a breed lives under a domestic species node, so tag the
// search with that species' common name to disambiguate.
const SPECIES_HINTS = ["cattle", "cow", "sheep", "goat", "pig", "horse", "chicken", "duck", "goose", "pigeon", "rabbit"];

function hintOf(speciesCommon) {
  if (!speciesCommon) return null;
  const c = speciesCommon.toLowerCase().replace(/\b(domestic|wild|european|american)\b/g, " ").trim();
  if (c === "cow") return "cattle";
  return SPECIES_HINTS.find((h) => c.includes(h)) ?? null;
}

function searchQuery(name, ctx) {
  if (OVERRIDES[name]) return OVERRIDES[name];
  const base = name.replace(/\s*\(.*\)\s*$/, "").trim();
  if (base.split(/\s+/).length <= 2) {
    const h = hintOf(ctx.speciesCommon);
    if (h) return `${base} ${h}`;
  }
  return base;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function wikidata(path, params, retries = 3) {
  const url = `https://www.wikidata.org/w/api.php?${new URLSearchParams({ format: "json", ...params })}`;
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, { headers: UA, signal: AbortSignal.timeout(20000) });
      if (res.status === 200) return await res.json();
      if (res.status === 429 || res.status >= 500) {
        if (attempt >= retries) throw new Error(`HTTP ${res.status} after retries`);
        await sleep(800 * (attempt + 1));
        continue;
      }
      throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      if (attempt >= retries) throw err;
      await sleep(500 * (attempt + 1));
    }
  }
}

function collectBreeds(out = new Set()) {
  for (const file of readdirSync(ORDERS_DIR)) {
    if (!file.endsWith(".json")) continue;
    const root = JSON.parse(readFileSync(join(ORDERS_DIR, file), "utf-8"));
    const walk = (node, species) => {
      if (node.rank === "SPECIES") species = node;
      if (node.rank === "BREED" && typeof node.name === "string") {
        out.add({ name: node.name, speciesName: species?.name, speciesCommon: species?.commonName });
      }
      for (const c of node.children ?? []) walk(c, species);
      for (const s of node.speciesList ?? []) walk(s, species);
    };
    walk(root, null);
  }
  return out;
}

// Wikidata's entity search is lossy for short breed names ("Delaware chicken"
// -> nothing; "Suffolk sheep" -> a local society). The English Wikipedia REST
// summary is a better fallback: it follows redirects, and for breed articles
// returns the same lead image + wikibase qid the project already uses for
// species portraits. Queries run hint-qualified candidate titles first so
// "Delaware" resolves to the chicken, never the US state.
async function wikipediaImage(title) {
  const res = await fetch(
    `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/ /g, "_"))}`,
    { headers: UA, signal: AbortSignal.timeout(15000), redirect: "follow" },
  );
  if (!res.ok) return null;
  const j = await res.json();
  const img = j.thumbnail?.source ?? j.originalimage?.source;
  const qid = j.wikibase_item ?? null;
  if (!img) return null;
  return { qid, image: img };
}

async function resolveImage(name, ctx) {
  // "Andalusian (PRE)" - parenthetical qualifiers are curated book flavor, not
  // part of the Wikidata label; search on the bare name (or the pinned
  // override / species-hinted query).
  const searchName = searchQuery(name, ctx);
  const search = await wikidata("wbsearchentities", {
    action: "wbsearchentities",
    search: searchName,
    language: "en",
    limit: "10",
  });
  const results = search?.search ?? [];
  const exact = (lbl) => lbl.toLowerCase() === searchName.toLowerCase() || lbl.toLowerCase() === name.toLowerCase();
  const partial = (lbl) => lbl.toLowerCase().includes(searchName.toLowerCase()) || lbl.toLowerCase().includes(name.toLowerCase());
  const hits = results.filter((r) => exact(r.label) || partial(r.label));
  // Deliberately *no* early return here: an empty search result is common for
  // short breed names, and the Wikipedia REST fallback below is exactly the
  // path that resolves those.
  // Short names ("Persian", "American") resolve first to a language or
  // country. Rank candidates by label exactness then by a description that
  // reads like a breed, and take the first one that actually carries an
  // image - the top hit may be a disambiguation page whose neighbour is the
  // breed item with a real portrait.
  const score = (r) =>
    (exact(r.label) ? 2 : 0) + (/breed|domestic|variety/i.test(r.description ?? "") ? 1 : 0);
  const ordered = [...hits].sort((a, b) => score(b) - score(a));
  for (const r of ordered.slice(0, 5)) {
    const entities = await wikidata("wbgetentities", {
      action: "wbgetentities",
      ids: r.id,
      props: "claims",
      languages: "en",
    });
    const claims = entities?.entities?.[r.id]?.claims ?? {};
    const image = claims.P18?.[0]?.mainsnak?.datavalue?.value ?? null;
    if (image) return { qid: r.id, image };
    await sleep(110);
  }
  // API search exhausted or throttled - fall back to the Wikipedia REST
  // summary on hint-qualified titles, then the bare name.
  if (OVERRIDES[name]) {
    const w = await wikipediaImage(OVERRIDES[name]);
    if (w) return w;
  }
  const base = name.replace(/\s*\(.*\)\s*$/, "").trim();
  const h = hintOf(ctx.speciesCommon);
  if (h) {
    for (const t of [`${base} ${h}`, `${base} (${h})`]) {
      const w = await wikipediaImage(t);
      if (w) return w;
      await sleep(120);
    }
    const w = await wikipediaImage(base);
    if (w) return w;
  }
  return { qid: results[0]?.id ?? ordered[0]?.id ?? null, image: null };
}

async function main() {
  const distinct = new Map();
  for (const entry of collectBreeds()) {
    if (!distinct.has(entry.name)) distinct.set(entry.name, entry);
  }
  const names = [...distinct.entries()].sort(([a], [b]) => (a < b ? -1 : 1));
  let knownEntries = {};
  try {
    knownEntries = JSON.parse(readFileSync(OUT_PATH, "utf-8"));
  } catch {}
  const known = new Map(Object.entries(knownEntries));
  const writeSidecar = () =>
    writeFileSync(OUT_PATH, JSON.stringify(Object.fromEntries(known), null, 2) + "\n");
  const todo = names.filter(([n]) => !known.has(n) || !known.get(n).image);
  console.log(`Total breeds: ${names.length}; already-resolved: ${names.length - todo.length}; to fetch: ${todo.length}`);

  mkdirSync(dirname(OUT_PATH), { recursive: true });
  const start = Date.now();
  let i = 0;
  for (const [name, ctx] of todo) {
    i++;
    const entry = await resolveImage(name, ctx);
    if (entry.image) known.set(name, { qid: entry.qid, image: entry.image });
    else known.set(name, { qid: entry.qid }); // remember the miss to avoid re-hitting it
    if (i % 15 === 0 || i === todo.length) {
      const elapsed = ((Date.now() - start) / 1000);
      const eta = (elapsed / i) * (todo.length - i);
      console.log(`  ${i}/${todo.length} ${(100 * i / todo.length).toFixed(0)}% elapsed ${elapsed.toFixed(0)}s eta ${eta.toFixed(0)}s`);
    }
    await sleep(260);
    if (i % 50 === 0) writeSidecar();
  }
  writeSidecar();
  const withImage = [...known.values()].filter((e) => e.image).length;
  console.log(`Done. ${withImage}/${names.length} breeds have images -> ${OUT_PATH}`);
}
main().catch((err) => {
  console.error(err);
  process.exit(1);
});