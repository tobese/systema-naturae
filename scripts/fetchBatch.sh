#!/usr/bin/env bash
# Fetch a batch of ChecklistBank DwCA archives onto the sources volume.
#
#   scripts/fetchBatch.sh 1193 1128 2302 ...
#
# Each lands at $SN_SOURCES_ROOT/archives/checklistbank-<key>/<key>.zip, the
# layout `scripts/sourcesManifest.py` indexes, so a manifest regen picks them up
# without a hand edit. Sizes and sha256 are printed for the manifest entry.
set -uo pipefail
# caffeinate is macOS-only; q-bert is Linux. Detected, not assumed:
# a bare "caffeinate -dimsu" there is `command not found` (rc=127).
#
# An array, not a string: `HOLD="caffeinate -dimsu"` + `"$HOLD" curl` asks the
# shell for a command whose name is literally "caffeinate -dimsu", so every
# fetch failed with `command not found` before curl ran at all (and unquoted
# `$HOLD` would instead break the empty-HOLD case on Linux). An empty array
# expands to nothing, so both hosts work.
HOLD=()
command -v caffeinate >/dev/null 2>&1 && HOLD=(caffeinate -dimsu)

ROOT="${SN_SOURCES_ROOT:-/Volumes/MacieExternal/sources}"
UA="systema-naturae-triage/1.0 (+https://github.com/tobese/systema-naturae)"

if [ ! -d "$ROOT/archives" ]; then
  echo "FATAL: $ROOT/archives not found — is the external volume mounted?" >&2
  exit 1
fi

for key in "$@"; do
  dest="$ROOT/archives/checklistbank-$key"
  mkdir -p "$dest"
  # archive.zip is the name scripts/archiveOverlap.py reads; the <key>.zip copy
  # matches what earlier batches left behind (checklistbank-1027 has both).
  out="$dest/archive.zip"

  if [ -s "$out" ]; then
    echo "== $key  already on disk ($(du -h "$out" | cut -f1))"
    continue
  fi

  url="https://api.checklistbank.org/dataset/$key/archive.zip"
  echo "== $key  fetching $url"
  code=$("${HOLD[@]}" curl -sL -m 3600 --retry 3 --retry-delay 5 \
    -A "$UA" -o "$out.part" -w "%{http_code}" "$url")

  # ChecklistBank answers some keys with HTTP 200 and a JSON error body
  # ({"code":404,"message":"Archive for dataset 9818 not found"}), which an
  # http-code check alone accepts and stores as archive.zip. The reader then
  # fails much later with "not a zip or gzip", attributed to the wrong thing.
  # "PK" is the zip magic; \x1f\x8b covers the gzip'd-tar datasets (ILDIS).
  magic=$(head -c 2 "$out.part" 2>/dev/null | xxd -p 2>/dev/null)
  if [ "$magic" != "504b" ] && [ "$magic" != "1f8b" ]; then
    echo "   FAILED not an archive (magic=$magic http=$code) — $(head -c 160 "$out.part" 2>/dev/null)"
    rm -f "$out.part"
    continue
  fi

  if [ "$code" != "200" ] || [ ! -s "$out.part" ]; then
    echo "   FAILED http=$code — $(head -c 200 "$out.part" 2>/dev/null)"
    rm -f "$out.part"
    continue
  fi

  mv "$out.part" "$out"
  cp "$out" "$dest/$key.zip"
  bytes=$(stat -f%z "$out")
  sha=$(shasum -a 256 "$out" | cut -d' ' -f1)
  printf '   ok  %.1f MB  sha256:%s\n' "$(python3 -c "print($bytes/1048576)")" "$sha"
  # Informational only. Under pipefail, head closing the pipe on a listing of
  # thousands of members (Plazi's treatments/*.html) kills unzip with SIGPIPE
  # and this script exits non-zero after a good download, which
  # importQueueDriver.py read as "archive missing after fetch" (2026-10-31).
  unzip -l "$out" 2>/dev/null | tail -n +4 | head -12 | sed 's/^/     /' || true
done
