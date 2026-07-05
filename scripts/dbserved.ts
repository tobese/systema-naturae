/**
 * dbserved — Wikipedia plant DB lookup service (runs on Macie only).
 *
 * Loads /Volumes/WikiDump/wiki-pages-plants.sqlite fully into memory once,
 * then serves batched binomial lookups over HTTP so distributed enrich
 * workers (any OS) can hit Tier-1 without their own copy of the 294MB DB.
 *
 * Usage: npx tsx scripts/dbserved.ts [--port 9877] [--db <path>]
 *
 *   POST /lookup   { "keys": ["quercus robur", ...] }   (lowercased binomials)
 *        → { "quercus robur": { extract, description }, ... }  (only hits)
 *   GET  /health   → { ok: true, size: <#pages> }
 */
import { existsSync } from "fs";
import { spawnSync } from "child_process";
import { createServer } from "http";

const argv = process.argv.slice(2);
const arg = (flag: string, def: string) => {
  const i = argv.indexOf(flag);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : def;
};
const PORT = Number(arg("--port", "9880")); // 9877 is taken by ocd modelsd
const SQLITE_DB = arg("--db", "/Volumes/WikiDump/wiki-pages-plants.sqlite");

interface Page { extract: string; description?: string }

/** Load the entire DB into memory, keyed by lowercased title. */
function loadDb(): Map<string, Page> {
  if (!existsSync(SQLITE_DB)) {
    console.error(`DB not found: ${SQLITE_DB}`);
    process.exit(1);
  }
  const script = `
import json, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
rows = db.execute("SELECT title, description, extract FROM pages").fetchall()
print(json.dumps({r[0]: {'description': r[1], 'extract': r[2].strip()} for r in rows if r[2] and len(r[2].strip()) > 20}))
`;
  const r = spawnSync("python3", ["-c", script, SQLITE_DB], {
    encoding: "utf-8",
    timeout: 120000,
    maxBuffer: 1024 * 1024 * 1024,
  });
  if (r.status !== 0 || !r.stdout.trim()) {
    console.error("DB load failed:", r.stderr?.slice(0, 500));
    process.exit(1);
  }
  const raw = JSON.parse(r.stdout.trim()) as Record<string, Page>;
  const map = new Map<string, Page>();
  for (const [title, val] of Object.entries(raw)) map.set(title.toLowerCase(), val);
  return map;
}

console.log(`Loading ${SQLITE_DB} into memory…`);
const t0 = Date.now();
const db = loadDb();
console.log(`Loaded ${db.size.toLocaleString()} pages in ${((Date.now() - t0) / 1000).toFixed(1)}s`);

const server = createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true, size: db.size }));
    return;
  }
  if (req.method === "POST" && req.url === "/lookup") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      let keys: string[] = [];
      try {
        keys = JSON.parse(body).keys ?? [];
      } catch {
        res.writeHead(400).end('{"error":"bad json"}');
        return;
      }
      const out: Record<string, Page> = {};
      for (const k of keys) {
        const hit = db.get(k);
        if (hit) out[k] = hit;
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(out));
    });
    return;
  }
  res.writeHead(404).end('{"error":"not found"}');
});

server.listen(PORT, () => console.log(`dbserved listening on :${PORT}  (POST /lookup, GET /health)`));
