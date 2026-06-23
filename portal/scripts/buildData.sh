#!/bin/sh
# Cross-runtime launcher: uses bun (cloud agents) or npx tsx (local Node.js)
script_dir="$(cd "$(dirname "$0")" && pwd)"
if command -v bun >/dev/null 2>&1; then
  bun "$script_dir/buildData.ts"
  bun "$script_dir/buildImportLog.ts"
else
  npx tsx "$script_dir/buildData.ts"
  npx tsx "$script_dir/buildImportLog.ts"
fi
