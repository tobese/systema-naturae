# Docker deploy to Debbie

The live-ish secondary deployment (outside GitHub Pages) runs as a Docker
container on Debbie, reverse-proxied by Caddy alongside a few unrelated
sites (`debbie-web`, `periodic-table`, Ghost).

## Layout on Debbie

Owned by the `agent` user (`/home/agent`, mode `700` — `tommy` needs `sudo`
to reach it):

```
/home/agent/gcloud-vm/            ← docker-compose.yml + Caddyfile (routes /systema-naturae/* etc.)
/home/agent/systema-naturae/      ← plain deployed copy, NOT a git checkout
  Dockerfile                      ← FROM nginx:alpine; COPY portal/dist /usr/share/nginx/html/systema-naturae
  portal/dist/                    ← prebuilt Vite output, copied in from a dev machine
```

`gcloud-vm/docker-compose.yml`'s `systema-naturae` service builds from
`../systema-naturae` (i.e. the directory above) and is exposed at
`https://debbie.bearded-panga.ts.net/systema-naturae/`.

## The repo's root `Dockerfile`

`/Dockerfile` (repo root, tracked) is exactly what's deployed on Debbie:

```dockerfile
FROM nginx:alpine
COPY portal/dist /usr/share/nginx/html/systema-naturae
```

It expects `portal/dist` to already exist — there's no build step baked in.

## ⚠️ Build with `build:all`, not `build`

`npm run build` only builds the **animalia** kingdom's data
(`SN_KINGDOM` defaults to `animalia`). The Vite multi-page HTML entries for
every kingdom (`plantae.html`, `fungi.html`, …) get built regardless since
those are static routes, but `portal/dist/data/kingdoms/` will only contain
`animalia/` — every other kingdom 404s on its data fetch at runtime even
though the page loads.

Always build with:

```bash
cd portal && npm run build:all   # loops every kingdom in kingdom-config.json, then one vite build
```

before creating the Docker image, unless you specifically only want
animalia deployed.

## Redeploying after a `portal/dist` change

Debbie has no `rsync` — use tar-over-ssh. From the repo root, with a fresh
`portal/dist` already built:

```bash
# 1. ship the new dist to a scratch dir on Debbie (as tommy)
cd portal && tar czf - dist | ssh tommy@debbie.bearded-panga.ts.net \
  "rm -rf ~/sn-dist-new && mkdir -p ~/sn-dist-new && tar xzf - -C ~/sn-dist-new"

# 2. swap it into place under agent's home (needs sudo — see Access below)
ssh tommy@debbie.bearded-panga.ts.net "sudo rm -rf /home/agent/systema-naturae/portal/dist.old \
  && sudo mv /home/agent/systema-naturae/portal/dist /home/agent/systema-naturae/portal/dist.old \
  && sudo mv /home/tommy/sn-dist-new/dist /home/agent/systema-naturae/portal/dist \
  && sudo chown -R agent:agent /home/agent/systema-naturae/portal/dist \
  && sudo rm -rf /home/tommy/sn-dist-new"

# 3. rebuild the image and recreate the container
ssh tommy@debbie.bearded-panga.ts.net \
  "sudo bash -c 'cd /home/agent/systema-naturae && DOCKER_BUILDKIT=0 docker build -t debbie-systema-naturae:latest .'"
ssh tommy@debbie.bearded-panga.ts.net \
  "sudo bash -c 'cd /home/agent/gcloud-vm && docker compose up -d --no-build systema-naturae'"
```

Notes:
- `docker compose build` fails here (`compose build requires buildx 0.17.0
  or later` — Debbie has 0.13.1). Build with plain `docker build
  DOCKER_BUILDKIT=0 ...` instead, then `docker compose up -d --no-build`
  picks up the already-tagged image (`debbie-systema-naturae:latest`,
  matching what `docker compose config --images` expects).
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
