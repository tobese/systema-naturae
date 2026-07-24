# Multi-stage build: node builds all kingdoms from git-tracked source only —
# no external volumes/Ollama needed (those are only used by the offline
# import/enrichment pipeline; its output is already committed as family JSON).
# `docker build .` alone produces a deployable image — no separate local
# build + copy-the-dist-over step needed first.
FROM node:22-bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends rsync && rm -rf /var/lib/apt/lists/*

WORKDIR /repo
COPY . .

WORKDIR /repo/portal
RUN npm ci
# shared/src imports bare specifiers (e.g. "d3") resolved via a sibling app's
# node_modules on disk, not through Vite's @shared alias — mirrors the local
# dev symlink (same trick deploy.yml's "Link shared node_modules" step uses).
RUN ln -sfn "$(pwd)/node_modules" /repo/shared/node_modules

# Debbie serves this behind Caddy at /systema-naturae/ (see docs/deploy-debbie.md).
# Override at build time (--build-arg VITE_BASE=/) for a standalone/root-domain host.
ARG VITE_BASE=/systema-naturae/
ENV VITE_BASE=${VITE_BASE}
RUN npm run build:all

# portal/data/kingdoms/<kingdom>/{skeleton,manifest,coverage-summary,orders*/*}
# already land in dist/ via Vite's public/ copy. This rsync brings over the
# remaining runtime-fetched files (e.g. international-days.json) while
# excluding build-time-only artifacts (unified-taxonomy.json, per-kingdom
# order dumps, the various GBIF/WCVP/POWO caches) — mirrors deploy.yml's
# "Copy data files to dist" step for GitHub Pages.
RUN rsync -a \
      --exclude='*cache*.json' --exclude='*cache*.json.gz' \
      --exclude='unified-taxonomy.json' --exclude='unified-taxonomy-plantae.json' \
      --exclude='/orders/' --exclude='/orders-plantae/' \
      data/ dist/data/

# ---- Runtime: static nginx ----
FROM nginx:alpine
# Drop the base image's own default welcome page — bare `/` should 404,
# only /systema-naturae/* (what Caddy actually proxies) should serve.
RUN rm -f /usr/share/nginx/html/index.html
COPY --from=build /repo/portal/dist /usr/share/nginx/html/systema-naturae
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
