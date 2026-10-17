#!/usr/bin/env python3
"""Sync per-family name-parse-index sidecars between Macie and q-bert.

The monolith `portal/data/name-parse-index.jsonl` (559MB) is gitignored and
per-machine, so after any import each machine's copy drifts. Instead of
scp-ing the whole 559MB blob, this diffs the two machines' manifests and
transfers only changed sidecars.

Usage:
    # Run on Macie, push changed sidecars to q-bert:
    sh scripts/syncNameIndex.py --to q-bert

    # Run on q-bert, pull changed sidecars from Macie:
    sh scripts/syncNameIndex.py --from macie

    # Dry run to see what would transfer:
    sh scripts/syncNameIndex.py --to q-bert --dry-run

The remote machine is reached over SSH/Tailscale. SSH must already work
(tailnet policy permitting). The manifest on each machine lists each sidecar's
mtime_ns + size, so only actually-changed files are copied.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nameIndexCache  # noqa: E402

REMOTES = {
    "q-bert": "agent@q-bert.local",
    "qbert": "agent@q-bert.local",
    "macie": "tb@localhost",  # reverse direction, rarely used
}


def remote_cmd(host: str, cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
         host] + cmd,
        capture_output=True, text=True)


def remote_manifest(host: str) -> dict:
    cp = remote_cmd(host, ["cat", nameIndexCache.MANIFEST_PATH])
    if cp.returncode != 0:
        return {}
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError:
        return {}


def remote_sidecar(host: str, slug: str) -> bytes | None:
    path = nameIndexCache.family_sidecar_path(slug)
    cp = remote_cmd(host, ["cat", path])
    if cp.returncode != 0:
        return None
    return cp.stdout.encode()


def local_sidecar(slug: str) -> bytes | None:
    path = nameIndexCache.family_sidecar_path(slug)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def write_local_sidecar(slug: str, data: bytes) -> None:
    path = nameIndexCache.family_sidecar_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def diff_manifests(local: dict, remote: dict) -> tuple[list, list, list]:
    """(to_upload, to_download, to_delete) — slugs that differ between machines."""
    upload, download, delete = [], [], []
    local_slugs = set(local)
    remote_slugs = set(remote)

    # Families present locally but missing or different remotely -> upload
    for slug in local_slugs - remote_slugs:
        upload.append(slug)
    for slug in local_slugs & remote_slugs:
        le, re_ = local[slug], remote[slug]
        if (le.get("mtime_ns"), le.get("size")) != (re_.get("mtime_ns"), re_.get("size")):
            upload.append(slug)

    # Families present remotely but missing locally -> download
    for slug in remote_slugs - local_slugs:
        download.append(slug)

    return upload, download, delete


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", choices=list(REMOTES), help="push changed sidecars to this remote")
    ap.add_argument("--from", choices=list(REMOTES), dest="frm",
                    help="pull changed sidecars from this remote")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would transfer without doing it")
    args = ap.parse_args()

    if not args.to and not args.frm:
        print("FATAL: specify --to <remote> or --from <remote>")
        return 2

    local_manifest = nameIndexCache.load_manifest()

    if args.to:
        host = REMOTES[args.to]
        remote_manifest_data = remote_manifest(host)
        upload, _, _ = diff_manifests(local_manifest, remote_manifest_data)
        if not upload:
            print(f"  all sidecars already in sync with {args.to}")
            return 0
        print(f"  {len(upload)} sidecar(s) differ; {'dry run: ' if args.dry_run else ''}uploading to {args.to}")
        for slug in upload:
            data = local_sidecar(slug)
            if data is None:
                print(f"    SKIP {slug}: local sidecar missing")
                continue
            if args.dry_run:
                print(f"    would scp {slug} ({len(data):,} bytes)")
                continue
            cp = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no",
                 "-o", "ConnectTimeout=15",
                 nameIndexCache.family_sidecar_path(slug),
                 f"{host}:{nameIndexCache.family_sidecar_path(slug)}"],
                capture_output=True, text=True)
            if cp.returncode != 0:
                print(f"    FAIL {slug}: {cp.stderr.strip()[:200]}")
            else:
                print(f"    ok   {slug} ({len(data):,} bytes)")
        # Also sync manifest
        if not args.dry_run:
            subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no",
                 "-o", "ConnectTimeout=15",
                 nameIndexCache.MANIFEST_PATH,
                 f"{host}:{nameIndexCache.MANIFEST_PATH}"],
                capture_output=True)
        return 0

    if args.frm:
        host = REMOTES[args.frm]
        remote_manifest_data = remote_manifest(host)
        _, download, _ = diff_manifests(local_manifest, remote_manifest_data)
        if not download:
            print(f"  all sidecars already in sync with {args.frm}")
            return 0
        print(f"  {len(download)} sidecar(s) differ; {'dry run: ' if args.dry_run else ''}downloading from {args.frm}")
        for slug in download:
            data = remote_sidecar(host, slug)
            if data is None:
                print(f"    SKIP {slug}: remote sidecar missing")
                continue
            if args.dry_run:
                print(f"    would scp {slug} ({len(data):,} bytes)")
                continue
            write_local_sidecar(slug, data)
            print(f"    ok   {slug} ({len(data):,} bytes)")
        # Also sync manifest
        if not args.dry_run:
            cp = remote_cmd(host, ["cat", nameIndexCache.MANIFEST_PATH])
            if cp.returncode == 0:
                tmp = nameIndexCache.MANIFEST_PATH + ".tmp"
                with open(tmp, "wb") as fh:
                    fh.write(cp.stdout.encode())
                os.replace(tmp, nameIndexCache.MANIFEST_PATH)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
