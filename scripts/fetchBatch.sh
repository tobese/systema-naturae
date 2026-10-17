#!/usr/bin/env bash
# Fetch a batch of ChecklistBank DwCA archives onto the sources volume.
#
#   scripts/fetchBatch.sh 1193 1128 2302 ...
#
# Each lands at $SN_SOURCES_ROOT/archives/checklistbank-<key>/<key>.zip, the
# layout `scripts/sourcesManifest.py` indexes, so a manifest regen picks them up
# without a hand edit. Sizes and sha256 are printed for the manifest entry.
set -uo pipefail

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
  code=$(caffeinate -dimsu curl -sL -m 3600 --retry 3 --retry-delay 5 \
    -A "$UA" -o "$out.part" -w "%{http_code}" "$url")

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
  unzip -l "$out" 2>/dev/null | tail -n +4 | head -12 | sed 's/^/     /'
done
