// One place that decides where a Wikipedia summary comes from.
//
// Default is the public REST API, which is what any deployed build must use —
// the primary deployment is GitHub Pages, where nothing internal is reachable.
// Set VITE_WIKI_SUMMARY_BASE to point at a self-hosted mirror during
// development:
//
//   portal/.env.local   ->   VITE_WIKI_SUMMARY_BASE=http://192.168.0.100:9881
//
// That is what `services/wikiserved` is: the enwiki wikitext mirror already in
// Postgres on debbie, served over HTTP. It exists so that iterating on the app
// does not spend the public API's rate limit on hover-and-click lookups, and so
// development does not depend on en.wikipedia.org being up. It is not a
// production dependency and is not routed publicly.
//
// Text only — the mirror has no image store, so `thumbnail` is never populated
// from it. Anything that needs a picture (the tree's hover tooltips in
// FamilyTree.tsx) stays on the public API regardless, and a miss or a failure
// falls back there too, so behaviour degrades to exactly what it was.

const WIKI_BASE = "https://en.wikipedia.org";

export interface WikiSummary {
  extract: string;
  thumbnail?: { source: string };
  content_urls?: { desktop: { page: string } };
}

function mirrorBase(): string | null {
  const base = import.meta.env?.VITE_WIKI_SUMMARY_BASE;
  return typeof base === "string" && base.length ? base.replace(/\/+$/, "") : null;
}

const wikiSlug = (title: string) => title.replace(/ /g, "_");

/** The public REST summary — the fallback, and the only path in production. */
async function fromRestApi(title: string): Promise<WikiSummary | null> {
  try {
    const res = await fetch(`${WIKI_BASE}/api/rest_v1/page/summary/${encodeURIComponent(wikiSlug(title))}`);
    return res.ok ? ((await res.json()) as WikiSummary) : null;
  } catch {
    return null;
  }
}

/** The local mirror: text only, and the title it actually resolved to. */
async function fromMirror(base: string, title: string): Promise<WikiSummary | null> {
  try {
    const res = await fetch(`${base}/lookup`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ keys: [title] }),
    });
    if (!res.ok) return null;
    const body = (await res.json()) as Record<string, { title: string; lead: string[] }>;
    const hit = body[title];
    if (!hit?.lead?.length) return null;
    return {
      extract: hit.lead.join("\n"),
      // No portrait from here — see the note at the top of this file.
      content_urls: { desktop: { page: `${WIKI_BASE}/wiki/${encodeURIComponent(wikiSlug(hit.title))}` } },
    };
  } catch {
    return null;
  }
}

export async function fetchWikiSummary(title: string): Promise<WikiSummary | null> {
  const base = mirrorBase();
  if (base) {
    const mirrored = await fromMirror(base, title);
    if (mirrored) return mirrored;
  }
  return fromRestApi(title);
}
