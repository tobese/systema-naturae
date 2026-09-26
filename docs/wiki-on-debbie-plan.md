# Running a wiki on debbie — plan

*Written 2026-09-26, after the breed work.* Question: instead of the current
arrangement — a one-off wikitext dump mirrored into Postgres on debbie, plus
live calls to `en.wikipedia.org` for anything the mirror doesn't answer — should
we just run a real wiki there?

**Short answer: not for English, yes for Swedish, and the thing that would
actually help is a ~100-line lookup service in front of the table we already
have.**

## What is on debbie now

The `snedtankt` Postgres (container `postgres_snedtankt_debbie`, port 5433)
already holds a wikitext mirror of both wikis, imported by
`~/enwiki/import_svwiki_dump.py` (mainspace only, `ns == "0"`, one table per
language):

| Table | Rows | Size |
|---|---|---|
| `EnWikiPages` | 19,071,980 (≈7M articles + redirects) | 38 GB (5.9 GB heap, rest TOAST) |
| `EnWikiPagesQid` | 10,269,862 | 957 MB |
| `SvWikiPages` | 4,300,934 | — |

Box: 4 cores, 15 GB RAM, **206 GB free**. No PHP, no web server, no MediaWiki.
There is also an unrelated `~/wikidata-api` (a custom Flask service, not
MediaWiki).

So the full English article text is *already local*. That is the fact the whole
question turns on.

## Why not MediaWiki for enwiki

A MediaWiki install is not just the wikitext. It adds the parsed HTML
(`parsercache`, typically 3–5× the wikitext) and, if you want search,
CirrusSearch's Elasticsearch indices (another 2–3×). For enwiki that lands around
**150–250 GB** and a multi-hour to multi-day import, on a box with 206 GB free
and 15 GB RAM.

For all that we would gain: a REST API and a search index over text we already
hold. Both are far cheaper to serve from the table we have. And the mirror is
only a snapshot (2026-06-01 dump) either way, so MediaWiki would not make it
any fresher — freshness comes from re-running the dump import, not from the
software.

## What to do instead

### 1. `wikiserved` — a lookup service over `EnWikiPages` (the actual win) — **DONE**

Built and deployed: [`services/wikiserved/`](../services/wikiserved/README.md).
Runs in the deploy compose (`gcloud-vm/docker-compose.yml`) rather than
standalone, because debbie's only public ingress is Caddy via the tunnel and
everything reachable from outside is a compose service behind it. It reaches the
mirror through `host.docker.internal:5433` (the `postgres_snedtankt_debbie`
project, published on the host), with the DSN in `.env` alongside
`SWEGOV_DATABASE_URL`. Live at `:9881` on LAN/Tailscale; **no Caddy route, on
purpose** — see below.

The repo already has this pattern for the plant mirror:
`scripts/dbserved.ts` loads a DB once and serves batched lookups over HTTP so
workers on any machine avoid the network. The same shape in front of
`EnWikiPages` removes the last reason the portal calls en.wikipedia.org at all.

```
POST /lookup   { "keys": ["Felis catus", "Pekin", ...] }
     → { "Felis catus": { "title": "Felis catus", "lead": ["para 1", "para 2"] },
         "Pekin": { "title": "American Pekin", "lead": [...] } }   // redirects resolved
GET  /health   → { ok, rows, version }
```

- Runs on debbie, talks to the local Postgres, no dump file to copy.
- Follows redirects one hop, which is what the breed resolver wants
  (`Pekin` → `American Pekin`).
- The wikitext→lead extraction already exists in
  `scripts/enrichBreedsFromWikipedia.py` (`lead_paragraphs`, `render_templates`,
  `strip_wikilinks`). Either port that to the service or write the service in
  Python — debbie already has `~/wiki-venv` with `psycopg2`.
- **Text only.** Portraits are not servable this way: there is no image store,
  so images stay on Wikidata P18 / the REST API. That is fine — it is the long
  prose that the 809k-species fallback is paying network round-trips for.

**Not wired into the browser, deliberately.** The *primary* deployment is GitHub
Pages, where this service is unreachable, so pointing the client hooks at it
would only affect the secondary Debbie build — while putting a 19M-row mirror on
the public domain to get there. So the REST fallback stays where it is and the
service's clients are the enrichment workers.

Worth knowing before that is revisited: the browser's largest live-Wikipedia load
is not the panels but `shared/src/components/FamilyTree.tsx`, which fetches
summaries directly in three places, on node hover. `EponymModal` uses a
different endpoint (`action=query`). All of them would need to move behind one
base-URL-configurable helper for a public route to be worth adding — and the
mirror is a 2026-06-01 snapshot, so the browser would get *older* text than the
live API. A rate-limit win, not a freshness one.

What did pay off immediately: the service made the shape of the client work
obvious, and it is a usable target for the backfill. Measured cold on that box:
0.26 s for one key, 12.4 s for 200 (~17 keys/s), and ~0 s for anything it has
already served. That last number is why a browser client would feel fine while a
809k-species backfill should keep hitting Postgres directly (~13 h over HTTP).

### 2. svwiki MediaWiki, if a real wiki is wanted

svwiki is the case where running the actual software *is* justified: the dump is
1.8 GB, `SvWikiPages` is already imported, and a full MediaWiki + Postgres
import is hours and roughly 40 GB — comfortable on this box.

The payoff is content, not plumbing: **the project has essentially no Swedish
common names.** Every `commonName` in the tree today is English, because every
lookup has been against enwiki. A live svwiki would be the natural source for
`svenska namn`, which is a real gap rather than a technical one.

Order matters: do §1 first. It is small, it unblocks the stored-prose work, and
it does not compete for the disk that svwiki would want.

### 3. Search, if it is ever needed

Do it in the table we have — a derived `lead` column with a Postgres full-text
GIN index, or a trigram index on `lower("Title")` for the disambiguation lookup
the breed resolver does. Neither needs Elasticsearch, and both are incremental
over a table that is already populated.

## Summary

| Idea | Verdict |
|---|---|
| MediaWiki for enwiki on debbie | **No** — 150–250 GB for text we already hold, on 206 GB free |
| `wikiserved` over `EnWikiPages` | **Yes** — small, unblocks stored prose, kills the live fallback |
| MediaWiki for svwiki | **Optional, later** — cheap, and the source of the missing Swedish names |
| Search | **Later** — Postgres indexes on the existing table, not Elasticsearch |

Open question worth settling before §1: the mirror is a 2026-06-01 snapshot, so
"fresh" descriptions are impossible until the dump is refreshed. Is a periodic
re-import wanted (it is a multi-hour `COPY`), or is a 4-month-old snapshot fine
for enrichment purposes with live REST only for genuinely new taxa?
