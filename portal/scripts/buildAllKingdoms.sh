#!/bin/sh
# Build all kingdoms defined in kingdom-config.json
# Usage: sh scripts/buildAllKingdoms.sh
script_dir="$(cd "$(dirname "$0")" && pwd)"
portal_dir="$(cd "$script_dir/.." && pwd)"

# Parse kingdom names from config
kingdoms=$(node -e "
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync('$portal_dir/data/kingdom-config.json', 'utf-8'));
console.log(Object.keys(cfg.kingdoms).join(' '));
")

for kingdom in $kingdoms; do
  echo "=== Building kingdom: $kingdom ==="
  # Match the heap size used by the individual build:/dev: npm scripts so a
  # combined build:all doesn't OOM on large kingdoms.
  SN_KINGDOM="$kingdom" NODE_OPTIONS="--max-old-space-size=8192" "$script_dir/buildData.sh"
done

echo "=== All kingdoms built ==="
