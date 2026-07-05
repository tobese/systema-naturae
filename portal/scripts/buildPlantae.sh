#!/bin/sh
# Build the in-development PLANT mirror: grafts the Plantae snippet + plant
# family data into data/unified-taxonomy-plantae.json (+ orders-plantae/,
# skeleton/manifest/coverage -plantae). Writes ONLY *-plantae outputs — never
# touches the live animal unified-taxonomy.json. See CLAUDE.md (animals vs plants).
script_dir="$(cd "$(dirname "$0")" && pwd)"
export SN_VARIANT=plantae
export SN_INPUT=data/taxonomy-plantae-snippet.json
export NODE_OPTIONS="--max-old-space-size=4096"
if command -v bun >/dev/null 2>&1; then
  bun "$script_dir/buildData.ts"
else
  TMPDIR=/tmp npx tsx "$script_dir/buildData.ts"
fi
