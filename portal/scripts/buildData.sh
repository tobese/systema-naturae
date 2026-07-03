#!/bin/sh
# Cross-runtime launcher: uses bun (cloud agents) or npx tsx (local Node.js)
# TMPDIR=/tmp avoids IPC socket creation failure when /Volumes is unavailable
script_dir="$(cd "$(dirname "$0")" && pwd)"
if command -v bun >/dev/null 2>&1; then
  bun "$script_dir/buildData.ts"
  bun "$script_dir/buildImportLog.ts"
else
  TMPDIR=/tmp npx tsx "$script_dir/buildData.ts"
  TMPDIR=/tmp npx tsx "$script_dir/buildImportLog.ts"
fi
