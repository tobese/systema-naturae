# Docker deploy to Debbie

The live-ish secondary deployment (outside GitHub Pages) runs as a Docker
container on Debbie, reverse-proxied by Caddy alongside a few unrelated
sites (`debbie-web`, `periodic-table`, Ghost).

## The repo's root `Dockerfile` — multi-stage, builds itself

`/Dockerfile` (repo root, tracked) is a multi-stage build: a `node` stage
runs `npm ci` + `npm run build:all` (all 6 kingdoms, from git-tracked source
only — no external volumes/Ollama needed, since those only feed the offline
enrichment pipeline whose *output* is already committed as family JSON),
then a slim `nginx:alpine` stage copies just the built `dist/` output plus
`/nginx.conf` (gzip + long-cache headers for the immutable taxonomy JSON).

**`docker build .` alone now produces a deployable image** — there's no
separate "build `portal/dist` on a dev machine, then ship it over" step
first, unlike the old two-line `FROM nginx:alpine; COPY portal/dist ...`
version. `VITE_BASE` defaults to `/systema-naturae/` (Debbie's Caddy path);
override with `--build-arg VITE_BASE=/` for a standalone/root-domain host.

Companion files at repo root: `.dockerignore` (excludes `.git`,
`node_modules`, build-time-only data like the GBIF/WCVP/POWO caches and
`unified-taxonomy*.json`), `nginx.conf`, and a `docker-compose.yml` for local
testing (`docker compose up --build`, served at `localhost:8080`).

## Layout on Debbie

Owned by the `agent` user (`/home/agent`, mode `700` — `tommy` needs `sudo`
to reach it):

```
/home/agent/gcloud-vm/            ← docker-compose.yml + Caddyfile (routes /systema-naturae/* etc.)
/home/agent/systema-naturae/      ← full repo source (whatever the Dockerfile's build stage needs)
```

`gcloud-vm/docker-compose.yml`'s `systema-naturae` service builds from
`../systema-naturae` (i.e. the directory above) and is exposed at
`https://debbie.bearded-panga.ts.net/systema-naturae/`.

Since the image now builds itself from source, `/home/agent/systema-naturae/`
needs the full buildable source tree (not just `Dockerfile` + a prebuilt
`dist/` as before) — in practice, a real git checkout kept in sync with this
repo's `main`, rather than a one-off copy pushed over per deploy.

## Redeploying

With a checkout on Debbie tracking `main`:

```bash
ssh tommy@debbie.bearded-panga.ts.net \
  "sudo bash -c 'cd /home/agent/systema-naturae && git pull \
    && DOCKER_BUILDKIT=0 docker build -t debbie-systema-naturae:latest .'"
ssh tommy@debbie.bearded-panga.ts.net \
  "sudo bash -c 'cd /home/agent/gcloud-vm && docker compose up -d --no-build systema-naturae'"
```

Notes:
- `docker compose build` fails here (`compose build requires buildx 0.17.0
  or later` — Debbie has 0.13.1). Build with plain `docker build
  DOCKER_BUILDKIT=0 ...` instead — multi-stage builds work fine with the
  legacy builder, buildx just isn't required for that — then
  `docker compose up -d --no-build` picks up the already-tagged image
  (`debbie-systema-naturae:latest`, matching what `docker compose config
  --images` expects).
- Verify: `curl -sk -o /dev/null -w '%{http_code}\n'
  https://debbie.bearded-panga.ts.net/systema-naturae/data/kingdoms/<kingdom>/unified-taxonomy-skeleton.json`
  for each kingdom.

## Access

- SSH as `tommy` — reach Debbie over **Tailscale**
  (`debbie` / `debbie.bearded-panga.ts.net`) even when `.local` mDNS
  routing on the LAN is down (`no route to host`); see the Network section
  in the root `CLAUDE.md`.
- `tommy` has passwordless `sudo ALL` on Debbie — needed for every
  filesystem write under `/home/agent` and all `docker`/`docker compose`
  commands (`tommy` is not in the `docker` group).
- Credentials aren't stored in this repo. See `~/docker-multi-machine/README.md`
  on Macie.
