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

## Custom domain: systema-naturae.se (Cloudflare Tunnel)

Set up 2026-09-11. The domain is registered at one.com but delegated to
Cloudflare (nameservers `gerald.ns.cloudflare.com` / `lilith.ns.cloudflare.com`)
under the `tommy.bergstrand@gmail.com` Cloudflare account (Zero Trust Free
plan, zone on the Free plan).

- **No port-forwarding** — Debbie isn't publicly exposed. A Cloudflare
  Tunnel (`cloudflared` service in `gcloud-vm/docker-compose.yml`, already
  present in the compose file before this) makes an outbound-only
  connection to Cloudflare's edge.
- **Tunnel**: named `debbie-systema-naturae` in the Cloudflare Zero Trust
  dashboard (Networks → Tunnels & Mesh). Its **published application
  routes** (public hostnames) point both `systema-naturae.se` and
  `www.systema-naturae.se` at service `http://caddy:80` — this auto-created
  the proxied CNAME DNS records (`<tunnel-id>.cfargotunnel.com`).
- **SSL/TLS mode**: `Flexible` on the zone (dashboard → SSL/TLS →
  Overview/Configure) — Cloudflare terminates TLS for visitors and speaks
  plain HTTP to the origin, since the existing Caddyfile already has an
  HTTP-only server block for `systema-naturae.se`/`www` that redirects `/`
  → `/systema-naturae/` and reverse-proxies to `systema-naturae:80`. No
  Caddyfile changes were needed.
- **Token**: stored as `CLOUDFLARE_TUNNEL_TOKEN` in
  `/home/agent/gcloud-vm/.env` on Debbie (not in git). The `cloudflared`
  container reads it via `tunnel run --token ${CLOUDFLARE_TUNNEL_TOKEN}`.
  Start/restart it with:
  ```bash
  ssh tommy@debbie.bearded-panga.ts.net \
    "sudo bash -c 'cd /home/agent/gcloud-vm && docker compose up -d cloudflared'"
  ```
- **Rotating the token**: Cloudflare dashboard → Zero Trust → Networks →
  Tunnels & Mesh → `debbie-systema-naturae` → get a new token from the
  connector install page, update `.env`, then `docker compose up -d
  --force-recreate cloudflared`.
- **Verify**: `curl -sk --resolve systema-naturae.se:443:188.114.96.1
  https://systema-naturae.se/systema-naturae/` should return `200` (root
  `/` returns a `302` redirect into `/systema-naturae/`).
