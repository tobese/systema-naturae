# Session 2026-07-11 — KingdomSwitcher + build fixes

## What shipped

`portal/src/components/KingdomSwitcher.tsx` — a pill-row nav (Animals / Plants / Fungi /
Chromista / Protozoa / Archaea) wired into `App.tsx`'s header, one per-hue accent color per
kingdom. Links to each kingdom's static entry point (`<kingdom>.html`), highlighting the
active one. Verified live in Chrome for Animalia, Archaea, Protozoa, and (nav-only) Plantae.

## Bugs found and fixed

All four were pre-existing, introduced by the Archaea/Protozoa kingdom imports
(`398666db2`, `4fc9a76b3` and earlier) — not caused by the KingdomSwitcher work, but they
blocked verifying it since Archaea/Protozoa wouldn't build or load at all.

1. **Invalid JS identifiers in `colorRegistryArchaea.ts`.** Two GTDB-style family slugs start
   with digits (`1-14-0-10-31-34`, `21-14-0-10-32-9`), and the registry generator turned them
   into `const 1_14_0_10_31_34_THEME = ...`, which is a syntax error — `tsc -b` failed for the
   whole portal. Fixed `portal/scripts/genColorRegistry.ts` to prefix digit-leading identifiers
   with `F_`, then regenerated the file (`npx tsx scripts/genColorRegistry.ts --kingdom Archaea
   --base 340`).

2. **Typo'd color-registry import.** `main-archaea.tsx`, `main-bare-archaea.tsx` imported
   `./colorRegistryUarchaea.ts` (stray "U"); `main-protozoa.tsx`, `main-bare-protozoa.tsx`
   imported `./colorRegistryUprotozoa.ts`. Neither file exists — the actual files are
   `colorRegistryArchaea.ts` / `colorRegistryProtozoa.ts`. These two kingdom entry points were
   completely broken (blank page, no error surfaced). Fixed all four imports.

3. **Same typo in `<title>` tags.** `archaea.html`, `bare-archaea.html`, `protozoa.html`,
   `bare-protozoa.html` all had `Uarchaea` / `Uprotozoa` in the page title. Fixed to match the
   other kingdoms' `<title>Systema Naturae — <Kingdom></title>` pattern.

Confirmed no other kingdom's color registry has the digit-identifier bug
(`grep -ln "^const [0-9]" src/colorRegistry*.ts` → empty).

## Verification

- `npm run typecheck` — clean (was failing with 12 syntax errors before the fix).
- `NODE_OPTIONS=--max-old-space-size=8192 npx vite build` — all 6 kingdom entry points +
  5 bare variants build cleanly.
- Live in Chrome (dev server, port 5175): clicked through the KingdomSwitcher pills for
  Animalia → Archaea → Protozoa → Plantae; each correctly navigated, rendered its own tree,
  and highlighted the active pill in its kingdom-specific accent hue.

## Non-blocking observation: slow dev-mode first paint

Every kingdom page takes roughly 60–90s to first paint in `npm run dev` (not `build`).
Root cause: `shared/data/wiki-images.json` (~40MB, ~148k entries) is imported directly as an
ES module (`import wikiImages from ".../wiki-images.json"` → Vite's JSON-to-ESM transform).
Vite re-serializes it into a ~198MB JS module on every request — confirmed via
`curl .../wiki-images.json?import` taking ~60s to return 198,231,696 bytes, consistently, not
just on cold cache. This blocks first render since the import sits in the module graph above
`App`.

Not touched in this session — it's orthogonal to the KingdomSwitcher, affects every kingdom
equally (including the pre-existing Animalia page), and production builds aren't affected the
same way since Vite bundles the sidecar once at build time rather than transforming it
per-request. Worth a future fix if dev-mode iteration speed becomes painful — likely candidates:
switch to `fetch()`-at-runtime instead of a static import, or split `wiki-images.json` per
kingdom/class the way `unified-taxonomy.json` already is (see `data/kingdoms/<kingdom>/orders/`).

## Deploy pipeline audit (`.github/workflows/deploy.yml`)

Traced every runtime `fetch()` in `src/` against what the `build` job actually publishes.

**How it works:** builds Felidae/Canidae standalone sub-apps, then the portal via
`npm run build:all` (`buildAllKingdoms.sh` runs `buildData.ts` per kingdom into
`portal/data/kingdoms/<kingdom>/`, then one `vite build` bundles all 6 kingdom entry points).
Because the taxonomy tree is fetched at runtime rather than bundled, a separate
`rsync -a --exclude='*cache*.json*' data/ dist/data/` step copies the data directory into the
build output. The app only ever fetches `data/kingdoms/<kingdom>/{unified-taxonomy-skeleton.json,
order-manifest.json, coverage-summary.json, orders*/<order>.json}` and
`data/international-days-<kingdom>.json`; `wiki-images.json` and the base
`international-days.json` are statically imported so Vite bundles them into JS instead.

**CI is currently fully blocked**, unrelated to any of the below:
```
gh run view 29121970560
→ "The job was not started because your account is locked due to a billing issue."
```
Every recent `Deploy to GitHub Pages` run (including push-triggered ones from before the
trigger was commented out) failed in 5–56s without running the actual build. Nothing below is
live-breaking production right now — it will surface the first time the workflow runs after
billing is resolved.

### Bug: two hardcoded absolute `/data/...` fetches will 404 on the real subpath deploy

Both introduced 2026-07-08 ("kingdom-aware data layer"), both skip
`import.meta.env.BASE_URL` unlike the rest of the codebase (`useTaxonomyLoader.ts`,
`KingdomSwitcher.tsx`). Since the site deploys under `/systema-naturae/`
(`VITE_BASE: /${{ github.event.repository.name }}/`), these resolve to the wrong origin path:

- `src/components/CoverageModal.tsx:149` — `fetch(\`/data/kingdoms/${kingdom}/coverage-summary.json\`)`
  → Coverage modal will show nothing, for every kingdom, on the real site.
- `src/hooks/useInternationalDays.ts:28` — `fetch(\`/data/international-days${suffix}.json\`)`
  → silently falls back to Animalia's days on non-animalia kingdoms (wrapped in `.catch`, so no
  visible error). Also currently moot: only `data/international-days.json` (the base file)
  exists — no per-kingdom variants have been generated yet.

**Fixed**: both now build the fetch URL from `import.meta.env.BASE_URL`, matching
`useTaxonomyLoader.ts`'s pattern.

### Finding: the rsync step ships ~2.7GB, of which ~2.1GB is dead weight

| What | Size | Needed at runtime? |
|---|---|---|
| `data/kingdoms/*/orders*/` (actual per-order data) | 668M | **Yes** |
| skeletons / manifests / coverage summaries | small | **Yes** |
| `data/unified-taxonomy.json` + `data/unified-taxonomy-plantae.json` (legacy flat monoliths, pre-`data/kingdoms/` restructure) | 639M | No — unreferenced in `src/`; only read by local `testBuild.ts`/`testDataContract.ts` |
| `data/kingdoms/*/unified-taxonomy.json` ("backward-compat" monolith `buildData.ts` still writes per kingdom) | 875M | No — same, test-only |
| `data/orders/` + `data/orders-plantae/` (stale duplicates from before the `data/kingdoms/` split, last touched Jul 4 vs. Jul 11 for the current ones) | 500M | No — unreferenced |
| `data/wcvp_dwca.zip` (raw WCVP Darwin Core Archive from Kew — the plant-import source dump `scripts/cacheWcvp.py` parses into `wcvp-cache.json`) | 84M | No — raw import-time input, only read by `cacheWcvp.py` |

Confirmed each "No" by grepping `src/` and `scripts/` for every path — none of the five are
fetched by the deployed app.

**Fixed**: `.github/workflows/deploy.yml`'s rsync step now also excludes
`unified-taxonomy.json`, `unified-taxonomy-plantae.json`, `/orders/`, and `/orders-plantae/`.
Cuts the published `data/` payload from ~2.7GB to ~700MB with no functional change — faster
artifact upload, faster Pages deploy.

`data/wcvp_dwca.zip` no longer needs an exclude — it's been moved out of the repo entirely, to
`/Volumes/MacieExternal/tmp/opencode/wcvp_dwca.zip` (same external-volume convention
`cacheWcvp.py` already used for its derived `wcvp-cache.json` cache). `cacheWcvp.py`'s
`LOCAL_ZIP` constant now points there so it still finds the cached zip instead of re-downloading
it from Kew's SFTP.

Left alone: `gap-report*.json`, `sanity-*.json`, `snapshots/`, `namedafter-backup.json`,
`build-log.json`, `insect-wikipedia-coverage.json`, `worms-candidates.json`,
`gbif-scout-*.json` — all dev-tooling artifacts too, but only ~5.8MB combined, not worth the
added exclude-list complexity.
