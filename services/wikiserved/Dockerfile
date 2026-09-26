# wikiserved — Wikipedia text lookup service
#
# Deliberately NOT part of the portal image: it needs the Postgres wikitext
# mirror, which is data, not build input. Runs as its own service in the deploy
# compose so Caddy can route it (the browser is a client, and debbie has no
# public ingress) and so it survives reboots with everything else.
#
# The DSN points at the `snedtankt` database published on the host's port 5433
# by the separate postgres_snedtankt_debbie container; host-gateway is how the
# service reaches the host from inside a container. Override at build/run time
# for a different layout.
FROM node:22-bookworm-slim AS build
WORKDIR /srv
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY server.ts ./
RUN npm run build

FROM node:22-bookworm-slim
WORKDIR /srv
COPY --from=build /srv/node_modules ./node_modules
COPY --from=build /srv/dist ./dist
ENV NODE_ENV=production
EXPOSE 9881
CMD ["node", "dist/server.cjs", "--port", "9881"]
