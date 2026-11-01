# Hosting plan: app and data as separate deliveries (Render + a data bucket)

Status: **saved, not started** (2026-11-01). Open questions at the bottom.

## Why

Today app and data ship as one thing. The Docker build copies the repo, runs
`build:all` (all six kingdoms) and bakes app + data into one ~6.6 GB `dist`;
the app itself (JS/CSS) is a few MB. Fixing a rendering bug rebuilds and
ships all the data, and a data change rebuilds the app.

Goal: a rendering fix needs only the app; a data release needs only the data.

The truth does not move: the family files stay the truth in git (a tree in a
file tree, diffable, per-family history); `species.parquet` stays derived (an
index: 22 columns, no description text, no subspecies, no ranks above
species); the per-order JSON files stay what the portal reads. In-browser
parquet (DuckDB-WASM / hyparquet with range reads) fits search and
statistics, not tree navigation -- an optional later step.

## Shape

```
Render static site (app, a few MB)  --fetch-->  data bucket (e.g. Cloudflare R2, free egress)
  built from git on push                          releases/<id>/kingdoms/<k>/...
  PR previews, instant rollback                   current.json -> <id>
```

Render suits the app but not 6.6 GB of data: in 2026 included bandwidth went
from 100 GB to 5 GB/month (Hobby, free) and 500 GB to 25 GB (Pro, $25/month
flat), overage $0.15/GB; persistent disks are $0.25/GB/month, single-instance,
and cost zero-downtime deploys; Render Object Storage is early access.

## Steps

1. **Data contract.** A release is `releases/<id>/`: the kingdoms' skeleton,
   order manifest and order files as today, plus `release.json`
   (`formatVersion`, source commit, counts). `current.json` (no-cache) names
   the live release; release files are immutable and cached forever.
2. **App.** The loader (`useTaxonomyLoader.ts`) takes its data base from
   `VITE_DATA_BASE`, reads `current.json` first, and refuses to render on a
   `formatVersion` mismatch. A `build:app` script builds the app without
   data. Local dev keeps serving the local build (the symlink to
   `/Volumes/MacieExternal/sn-build/` on Macie).
3. **Publisher** (`scripts/publishData.py`, Macie, after a landing CI
   accepts): build data, `verifyDist.mjs`, upload changed files only
   (rclone or similar), write `release.json`, flip `current.json` last, keep
   the last N releases for rollback.
4. **Render static site** from a `render.yaml` blueprint: build command,
   publish dir, `VITE_DATA_BASE`, headers (`index.html` no-cache, hashed
   assets immutable). PR previews point at the live data, so a rendering fix
   can be checked before merging.
5. **Debbie** becomes a mirror: the Docker image carries the app only and
   mounts the data instead of baking it in.
6. **Optional, later:** a small Render web service for search over the
   parquet (needs a paid instance + disk).

## What Render adds

Builds on every git push; atomic deploys with immediate CDN invalidation;
PR previews; one-click rollback; redirect and header rules; infrastructure
as a blueprint in the repo; managed HTTPS and custom domains (2 Hobby,
15 Pro).

## Cost (estimate)

- App on Render: free, but its traffic counts against plan bandwidth. At a
  couple of MB per first visit, Hobby's 5 GB is ~2,500 visits/month; Pro
  ~10x.
- Data on R2: ~$0.015/GB-month storage, so a few 6.6 GB releases cost well
  under $1/month; egress free.

## Open questions (the user's)

- Render account and plan?
- R2 for the data, or Render's object-storage early access?
- Which domain?

Steps 1-2 do not depend on the answers.

## Sources

- [Render.com in mid-2026: plan change and bandwidth cut](https://jwatte.com/blog/render-com-platform-review/)
- [Render: new bandwidth pricing](https://render.com/blog/new-bandwidth-pricing-on-render)
- [Render docs: Persistent Disks](https://render.com/docs/disks)
- [Render docs: Static Sites](https://render.com/docs/static-sites)
- [Render Object Storage](https://render.com/object-storage)
