#!/bin/sh
# Cross-runtime launcher: uses bun (cloud agents) or npx tsx (local Node.js)
# Reads SN_KINGDOM env var to select kingdom (default: animalia)
#
# tsx creates IPC sockets in TMPDIR. A *stale* TMPDIR (e.g. pointing at an
# unmounted /Volumes path) breaks the build — that's what the old hard
# TMPDIR=/tmp guarded against. But when TMPDIR points at a valid, mounted
# volume (an APFS scratch disk keeps build temp off a small system disk) it
# works fine, so honour it and only fall back to /tmp when it's missing.
script_dir="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d "${TMPDIR:-/nonexistent}" ]; then
  TMPDIR=/tmp
fi
export TMPDIR
if command -v bun >/dev/null 2>&1; then
  bun "$script_dir/buildData.ts"
else
  npx tsx "$script_dir/buildData.ts"
fi
