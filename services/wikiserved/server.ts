/**
 * wikiserved — English Wikipedia text lookup, served from debbie.
 *
 * The enwiki wikitext is already mirrored in Postgres on debbie (the
 * `EnWikiPages` table in the `snedtankt` database, 19M mainspace rows, ~7M
 * articles). This puts a small HTTP service in front of it so the portal stops
 * calling en.wikipedia.org per node.
 *
 * Why not just run MediaWiki on that box: the text is the part we already
 * have. MediaWiki would add parsed HTML (3-5x the wikitext) plus CirrusSearch
 * indices (another 2-3x) — 150-250 GB on a machine with 206 GB free — to gain
 * an API and a search index over text we hold. See docs/wiki-on-debbie-plan.md.
 *
 * Runs in the deploy compose (routed by Caddy) rather than standalone because
 * the primary client is the *browser*: the graph's live-summary fallback is
 * fetched client-side, and debbie has no public ingress except the Cloudflare
 * tunnel, so a bare process on a port would be unreachable from a visitor.
 * Being in the compose network also makes it reachable to the enrichment
 * workers over the LAN/Tailscale, which is its second client.
 *
 * Endpoints
 *   POST /lookup  { "keys": ["Felis catus", "Pekin"] }
 *        -> { "Felis catus": { "title": "Felis catus", "lead": ["para", ...] },
 *             "Pekin": { "title": "American Pekin", "lead": [...] } }  (hits only)
 *        Redirects are followed one hop, so a bare breed name resolves to its
 *        article — "Pekin" -> "American Pekin", which is what the breed
 *        resolver in scripts/enrichBreedsFromWikipedia.py needs.
 *   GET  /lead?title=Felis%20catus   -> single entry, or 404
 *   GET  /health -> { ok, rows, db }
 *
 * Text only. Portraits are not served from here — there is no image store — so
 * images stay on Wikidata P18 / the REST API.
 *
 * Usage:
 *   node dist/server.js --port 9881
 *   WIKI_PG_DSN=postgres://... node dist/server.js
 */
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { Pool } from "pg";

const argv = process.argv.slice(2);
const arg = (flag: string, def: string) => {
  const i = argv.indexOf(flag);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : def;
};

const PORT = Number(arg("--port", "9881")); // 9880 is dbserved, 9876 progressd, 9877 modelsd
// Passwordless on purpose: libpq takes the password from PGPASSWORD or
// ~/.pgpass, so no credential has to live in this repository. The real value
// lives in ~/gcloud-vm/.env on debbie as WIKI_PG_DSN. An earlier version of
// this file (and of scripts/enrichBreedsFromWikipedia.py) inlined the
// password, and because the repository is public it had to be rotated.
const DSN = process.env.WIKI_PG_DSN ??
  arg("--dsn", "postgres://snedtankt@host.docker.internal:5433/snedtankt");
const MAX_KEYS = 500;
const MAX_PARAS = Number(arg("--paras", "2"));
// Only the lead is ever wanted, and the lead lives in the first few KB after
// the infobox. Selecting the whole Wikitext means dragging megabytes of taxobox
// and navigation templates out of TOAST for every request - 38 GB across 19M
// rows, so the random reads dominate and a 5-key batch took 8s where 1 key took
// 0.3s. A bounded prefix is ~12x the average article and all the prose needs.
const WIKITEXT_PREFIX = Number(arg("--prefix", "24000"));
// The graph asks for the same titles over and over as you browse a subtree.
const CACHE_MAX = Number(arg("--cache", "20000"));
const cache = new Map<string, Lead | null>();

export interface Lead {
  title: string;
  lead: string[];
}

// ----------------------------------------------------------- wikitext -> lead
//
// A direct port of the extraction in scripts/enrichBreedsFromWikipedia.py
// (render_templates / strip_wikilinks / clean_markup / lead_paragraphs). The two
// must stay in step: that script stamps this same text onto the breed nodes the
// book reads, so a divergence would mean the book and the live fallback format
// the same article differently. Change both together.

const DISPLAY_ARG0 = new Set([
  "nihongo", "nowrap", "nobr", "nsp", "transliteration", "respell",
  "ipa", "audio", "wikispecies", "wiktionary", "wikiquote", "sic", "h:title", "vern",
]);

/** Index just past the `}}`/`|}` matching the `{{`/`{|` at `start`, or -1. */
function blockEnd(text: string, start: number): number {
  let depth = 0;
  let j = start;
  while (j < text.length - 1) {
    const two = text.slice(j, j + 2);
    if (two === "{{" || two === "{|") { depth++; j += 2; continue; }
    if (two === "}}" || two === "|}") {
      depth--; j += 2;
      if (depth === 0) return j;
      continue;
    }
    j++;
  }
  return -1;
}

/** Split a template body on top-level `|`, ignoring nested braces. */
function splitArgs(body: string): string[] {
  const parts: string[] = [];
  let buf = "";
  let depth = 0;
  for (let i = 0; i < body.length; ) {
    const two = body.slice(i, i + 2);
    if (two === "{{" || two === "{|") { depth++; buf += two; i += 2; continue; }
    if (two === "}}" || two === "|}") { depth--; buf += two; i += 2; continue; }
    if (body[i] === "|" && depth === 0) { parts.push(buf); buf = ""; i++; continue; }
    buf += body[i++];
  }
  parts.push(buf);
  return parts;
}

/** Replace every `{{...}}`: display templates keep their argument, rest vanish. */
function renderTemplates(input: string): string {
  let text = input;
  for (let pass = 0; pass < 8; pass++) {
    let out = "";
    let i = 0;
    let changed = false;
    while (i < text.length) {
      if (text.startsWith("{{", i)) {
        const end = blockEnd(text, i);
        if (end === -1) { out += text.slice(i); break; }
        changed = true;
        const args = splitArgs(text.slice(i + 2, end - 2));
        const name = args[0].trim().toLowerCase();
        let disp = "";
        if (DISPLAY_ARG0.has(name) && args.length > 1) disp = args[1];
        else if ((name === "lang" || name === "llang") && args.length > 2) disp = args[2];
        else if (name.startsWith("lang-") && args.length > 1) disp = args[1];
        out += disp ? renderTemplates(disp) : " ";
        i = end;
        continue;
      }
      out += text[i++];
    }
    text = out;
    if (!changed) break;
  }
  return text;
}

/**
 * Resolve `[[...]]` links, honouring nesting. A regex cannot: a captioned image
 * is `[[File:X.jpg|thumb|a flock in [[Sernur]] ]]` and the caption's own link
 * closes the `]]` early, leaving the caption tail behind as debris.
 */
function stripWikilinks(s: string): string {
  let out = "";
  let i = 0;
  while (i < s.length) {
    if (s.startsWith("[[", i)) {
      let depth = 0;
      let j = i;
      let closed = false;
      while (j < s.length - 1) {
        if (s.startsWith("[[", j)) { depth++; j += 2; continue; }
        if (s.startsWith("]]", j)) {
          depth--; j += 2;
          if (depth === 0) { closed = true; break; }
          continue;
        }
        j++;
      }
      if (!closed) { out += s.slice(i); break; }
      const body = s.slice(i + 2, j - 2);
      const target = body.split("|")[0].trim();
      if (!/^(file|image|media|category)\s*:/i.test(target)) {
        out += body.includes("|") ? body.split("|").pop()!.trim() : target;
      }
      i = j;
      continue;
    }
    out += s[i++];
  }
  return out;
}

const ENTITIES: [RegExp, string][] = [
  [/&nbsp;/g, " "], [/&ndash;/g, "-"], [/&mdash;/g, "-"], [/&amp;/g, "&"],
  [/&quot;/g, '"'], [/&deg;/g, " degrees"], [/&minus;/g, "-"], [/&times;/g, "x"],
];

function cleanMarkup(input: string): string {
  let s = input;
  s = s.replace(/<!--[\s\S]*?-->/g, " ");
  s = s.replace(/<ref[^>]*?\/>/g, "");
  s = s.replace(/<ref[^>]*?>[\s\S]*?<\/ref>/g, "");
  s = s.replace(/<[^>]+>/g, "");
  s = renderTemplates(s);
  s = s.replace(/'{2,5}/g, "");
  s = stripWikilinks(s);
  s = s.replace(/\[https?:\/\/\S+\s+([^\]]*)\]/g, "$1");
  s = s.replace(/\[https?:\/\/\S+\]/g, "");
  for (const [re, to] of ENTITIES) s = s.replace(re, to);
  s = s.split(/\n?\s*==[^=]/)[0];
  // Parentheticals that only carried a non-Latin or templated gloss.
  s = s.replace(/\([^()]*[^\x00-\x7f][^()]*\)/g, "");
  s = s.replace(/\(\s*(?:,\s*)+[^()]*\)/g, "");
  s = s.replace(/\(\s*\)/g, "");
  s = s.replace(/\(\s*[a-z]{2}\s*\)/g, "");
  s = s.replace(/\[\s*\]/g, "");
  s = s.replace(/;\s*\(/g, " (");
  s = s.replace(/([.,])\s*,\s*(though|although|but|and|while|which)\b/g, "$1 $2");
  s = s.replace(/\s(?:at|from|in|of|to|by|with|weighing|measuring|reaching)\s*([.,])/g, "$1");
  s = s.replace(/([.!?])\s+([a-z])/g, (_m, p, c) => `${p} ${c.toUpperCase()}`);
  s = s.replace(/\s+([,;:.])/g, "$1").replace(/[,;:]{2,}/g, ",");
  s = s.replace(/\(\s+/g, "(").replace(/\s+\)/g, ")");
  s = s.replace(/\s+/g, " ");
  // Leftover table/template scaffolding is never prose.
  s = s.replace(/[{}|]|\[\[|\]\]/g, " ").replace(/\s+/g, " ");
  // Trim debris from the edges but keep a real closing full stop.
  return s.trim().replace(/^[.,;:]+/, "").replace(/[,;:]+$/, "").trim();
}

/** First `maxParas` prose paragraphs, skipping the infobox and headings. */
export function leadParagraphs(text: string, maxParas = MAX_PARAS): string[] {
  const body = renderTemplates(text.replace(/<!--[\s\S]*?-->/g, " "));
  const paras: string[] = [];
  for (const chunk of body.split(/\n\s*\n/)) {
    let c = chunk.trim();
    if (!c) continue;
    if (c.startsWith("=")) { if (paras.length) break; continue; }
    if (/^[*:#|!{]/.test(c) || c.startsWith("__")) continue;
    c = cleanMarkup(c);
    if (c.length < 40) continue;
    // A paragraph that does not start like a sentence is a fragment left by a
    // table or an unbalanced template, not prose.
    if (!/^[A-Z0-9"'“‘(]/.test(c)) continue;
    paras.push(c);
    if (paras.length >= maxParas) break;
  }
  return paras;
}

// -------------------------------------------------------------------- db ----

// `pg` is CommonJS and reaches for node builtins with a dynamic require, so the
// bundle is emitted as CJS (see package.json) and nothing may sit at the top
// level awaiting - startup goes through main() instead.
// A pool, not a single Client: a cold batch is TOAST-I/O bound on the mirror's
// disk, so splitting the key list across a few connections is close to a
// free 3-4x. Single-key lookups (what the browser does) are unaffected.
const POOL_SIZE = Number(arg("--pool", "6"));
const pool = new Pool({ connectionString: DSN, max: POOL_SIZE });

/** Rows whose Title matches any of `keys` (case-insensitive), redirects included. */
async function fetchPages(lowerKeys: string[]): Promise<Map<string, { title: string; redirect?: string; text?: string }>> {
  const found = new Map<string, { title: string; redirect?: string; text?: string }>();
  const seen = new Set<string>();
  let frontier = lowerKeys;
  while (frontier.length) {
    const keys = frontier.filter((k) => !seen.has(k));
    keys.forEach((k) => seen.add(k));
    if (!keys.length) break;
    const chunks: string[][] = [];
    const size = Math.max(1, Math.ceil(keys.length / POOL_SIZE));
    for (let i = 0; i < keys.length; i += size) chunks.push(keys.slice(i, i + size));
    const results = await Promise.all(chunks.map((chunk) => pool.query<{
      Title: string; IsRedirect: boolean; RedirectTarget: string | null; Wikitext: string | null;
    }>(
      `SELECT DISTINCT ON (lower("Title")) "Title", "IsRedirect", "RedirectTarget",
              LEFT("Wikitext", $2) AS "Wikitext"
         FROM "EnWikiPages" WHERE lower("Title") = ANY($1)
        ORDER BY lower("Title"), "IsRedirect" ASC`,
      [chunk, WIKITEXT_PREFIX],
    )));
    const rows = results.flatMap((r) => r.rows);
    const next: string[] = [];
    for (const r of rows) {
      const rec = found.get(r.Title.toLowerCase()) ?? { title: r.Title };
      found.set(r.Title.toLowerCase(), rec);
      if (r.IsRedirect && r.RedirectTarget && r.RedirectTarget.toLowerCase() !== r.Title.toLowerCase()) {
        rec.redirect = r.RedirectTarget;
        next.push(r.RedirectTarget.toLowerCase());
      } else if (r.Wikitext != null) {
        rec.text = r.Wikitext;
      }
    }
    frontier = next;
  }
  // Resolve each requested key through its redirect chain to the real article.
  const resolved = new Map<string, { title: string; text?: string }>();
  for (const [key, rec] of found) {
    let cur: { title: string; redirect?: string; text?: string } | undefined = rec;
    for (let hop = 0; hop < 5 && cur && !cur.text && cur.redirect; hop++) {
      cur = found.get(cur.redirect.toLowerCase());
    }
    if (cur?.text) resolved.set(key, { title: cur.title, text: cur.text });
  }
  return resolved;
}

async function lookup(rawKeys: string[]): Promise<Record<string, Lead>> {
  const out: Record<string, Lead> = {};
  const misses: string[] = [];
  for (const key of rawKeys) {
    const hit = cache.get(key.toLowerCase());
    if (hit === undefined) { misses.push(key); continue; }
    if (hit) out[key] = hit;
  }
  if (!misses.length) return out;

  const pages = await fetchPages(misses.map((k) => k.toLowerCase()));
  for (const key of misses) {
    const page = pages.get(key.toLowerCase());
    const lead = page ? leadParagraphs(page.text!) : [];
    const value: Lead | null = lead.length ? { title: page!.title, lead } : null;
    if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value as string);
    cache.set(key.toLowerCase(), value);
    if (value) out[key] = value;
  }
  return out;
}

// ----------------------------------------------------------------- server ---

const json = (res: ServerResponse, code: number, body: unknown) => {
  const payload = JSON.stringify(body);
  res.writeHead(code, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
    "access-control-allow-origin": "*",
    "cache-control": "public, max-age=86400",
  });
  res.end(payload);
};

const readBody = (req: IncomingMessage): Promise<string> =>
  new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (c) => {
      data += c;
      if (data.length > 4_000_000) reject(new Error("body too large"));
    });
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });

const server = createServer((req, res) => {
  void (async () => {
    try {
      const url = new URL(req.url ?? "/", "http://localhost");

      if (req.method === "OPTIONS") {
        res.writeHead(204, {
          "access-control-allow-origin": "*",
          "access-control-allow-methods": "GET,POST,OPTIONS",
          "access-control-allow-headers": "content-type",
        });
        return res.end();
      }

      if (url.pathname === "/health") {
        const { rows } = await pool.query<{ n: string }>('SELECT count(*)::text AS n FROM "EnWikiPages"');
        return json(res, 200, { ok: true, rows: Number(rows[0].n), paras: MAX_PARAS });
      }

      if (url.pathname === "/lead") {
        const title = url.searchParams.get("title");
        if (!title) return json(res, 400, { error: "title required" });
        const hit = await lookup([title]);
        return hit[title] ? json(res, 200, hit[title]) : json(res, 404, { error: "not found" });
      }

      if (url.pathname === "/lookup" && req.method === "POST") {
        const body = JSON.parse((await readBody(req)) || "{}");
        const keys: string[] = Array.isArray(body.keys) ? body.keys.filter((k) => typeof k === "string") : [];
        if (!keys.length) return json(res, 400, { error: "keys required" });
        if (keys.length > MAX_KEYS) return json(res, 413, { error: `max ${MAX_KEYS} keys` });
        return json(res, 200, await lookup(keys));
      }

      return json(res, 404, { error: "not found" });
    } catch (err) {
      json(res, 500, { error: String(err) });
    }
  })();
});

async function main(): Promise<void> {
  await pool.connect();
  server.listen(PORT, () => {
    console.log(`wikiserved listening on :${PORT} (max ${MAX_KEYS} keys/batch, ${MAX_PARAS} paras)`);
  });
  for (const sig of ["SIGINT", "SIGTERM"] as const) {
    process.on(sig, () => {
      server.close();
      void pool.end().then(() => process.exit(0));
    });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
