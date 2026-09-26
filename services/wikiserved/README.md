# wikiserved

English Wikipedia **text** lookup, served from the wikitext mirror already in
Postgres on debbie (`EnWikiPages`, 19,071,980 mainspace rows ≈ 7M articles plus
redirects, 38 GB).

## Why

The portal's graph shows a live Wikipedia summary wherever a node has no stored
`description` — 809k species, 4,182 families, 849 subspecies. That is one request
per node opened, against a public API, from a browser.

Meanwhile the full English article text is *already local* on the same machine.
This service puts a small HTTP interface in front of it.

**Not** a MediaWiki install: that would add parsed HTML (3–5× the wikitext) and
CirrusSearch indices (another 2–3×) — 150–250 GB on a box with 206 GB free — to
gain an API and a search index over text we already hold. Reasoning in
[`docs/wiki-on-debbie-plan.md`](../../docs/wiki-on-debbie-plan.md).

## API

```
POST /lookup   { "keys": ["Felis catus", "Peking duck"] }
   → { "Felis catus": { "title": "Cat", "lead": ["para 1", "para 2"] },
       "Peking duck": { "title": "Peking duck", "lead": [...] } }    // hits only
   Redirects are followed one hop, so a bare name resolves to its article.

GET  /lead?title=Felis%20catus   → one entry, or 404
GET  /health                      → { ok, rows, paras }
```

`lead` is the article's first paragraphs, `[[wikitext]]` rendered to prose:
infobox and templates stripped, links flattened, comments and refs dropped.
Max 500 keys per batch, 2 paragraphs by default (`--paras`, `--prefix`).

**Text only.** Portraits are not served here — there is no image store — so
images stay on Wikidata P18 / the REST API.

## Running it

In the deploy compose, not standalone, because the box's only public ingress is
Caddy via the Cloudflare tunnel and everything reachable from the outside is a
compose service behind it. Being in the compose network also puts it on the
LAN/Tailscale for the enrichment workers.

```yaml
# /home/agent/gcloud-vm/docker-compose.yml
  wikiserved:
    build:
      context: ../systema-naturae/services/wikiserved
    image: wikiserved:latest
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      WIKI_PG_DSN: ${WIKI_PG_DSN}     # in .env, not here
    ports:
      - "9881:9881"
```

The mirror lives in the separate `postgres_snedtankt_debbie` project, published
on the host at `:5433`; `host-gateway` is how the container reaches the host.
Joining that project's network instead would couple two unrelated stacks.

```bash
# debbie
cd ~/systema-naturae && DOCKER_BUILDKIT=0 docker build -t wikiserved:latest services/wikiserved
cd ~/gcloud-vm && docker compose up -d wikiserved
curl -s http://192.168.0.100:9881/health
```

## Not on the public domain, deliberately

There is no Caddy route for it. The portal's live-summary fallback stays on the
public REST API, because the **primary** deployment is GitHub Pages, where this
service is unreachable anyway — so routing it through Caddy would expose a
19M-row mirror on `systema-naturae.se` without changing what the primary
deployment does. Its clients today are the enrichment workers on the
LAN/Tailscale.

If the browser should use it, that needs a public route and a decision about
exposure, plus an env-var base URL in the client hooks (see below). Note the
mirror is a **2026-06-01 snapshot**, so the browser would get older text than the
live API — a rate-limit win, not a freshness one.

## Client hooks that would need changing

Live REST callers, all currently going to `en.wikipedia.org`:

| Where | What |
|---|---|
| `shared/src/hooks/useWikipediaSummary.ts` | the panel summaries |
| `shared/src/components/FamilyTree.tsx` ×3 | hover/label fetches — the highest volume, since it fires on node hover |
| `portal/src/components/EponymModal.tsx` | `action=query`, a different endpoint (link resolution) |

All should go through one helper with a configurable base, defaulting to the
public API, so GitHub Pages keeps working unchanged.

## Performance

Measured on debbie (4 cores, 15 GB RAM), cold cache:

| Request | Time |
|---|---|
| 1 key | 0.26 s first, ~0.02 s warm |
| 5 keys | 0.26 s |
| 200 keys | 12.4 s (101 hits) |
| 500 keys | 12.9 s (233 hits) |

Two things got it there, both in `server.ts`:

- **Bounded `LEFT("Wikitext", 24000)`.** Selecting the whole column drags
  megabytes of taxobox out of TOAST per row; a 5-key batch went from 8 s to
  0.26 s.
- **An in-process LRU** (20k entries), because the graph re-asks for the same
  titles constantly while you browse a subtree — repeat batches are ~0 s.

A pool plus per-batch chunking gives the ~4× on cold batches.

Throughput is ~17 keys/s cold, so a full 809k-species backfill over HTTP would
be ~13 hours. For that, keep hitting Postgres directly the way
`scripts/enrichFromWikipedia.ts` already does; this service is for the
interactive path and modest batches.

## Maintenance note

The wikitext→lead extraction here is a direct port of the one in
`scripts/enrichBreedsFromWikipedia.py` (`renderTemplates` / `stripWikilinks` /
`cleanMarkup` / `leadParagraphs`). **They must stay in step** — that script
stamps the same text onto breed nodes the book reads, so a divergence would mean
the book and the live fallback format the same article differently. Change both
together.
