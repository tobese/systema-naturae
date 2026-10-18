#!/usr/bin/env python3
"""Resolve a downloaded dataset to its path on the external volume.

Scripts used to hardcode `/Volumes/MacieExternal/tmp/opencode/...`, which is
both a `tmp` directory and the wrong place for something that took twenty
minutes to fetch. Paths now come from the manifest written by
`scripts/sourcesManifest.py`, so a source can be relocated without touching every
script, and an unmounted volume produces a sentence rather than a
`FileNotFoundError` on a path that no longer means anything.
"""
import json
import os
import sys

# The root is overridable so the tree's tools can run off Macie. This file
# exists so that *dataset* paths are not hardcoded -- leaving the volume itself
# hardcoded meant `importColChecklist.py` refused to run anywhere else with
#
#     FATAL: /Volumes/MacieExternal/sources/manifest.json not found.
#
# ...which reads as "the dataset is unavailable" and is in fact "this machine has
# a different disk". q-bert (WSL2, 22 cores) indexes the tree and runs importers
# with SN_SOURCES_ROOT pointing at its own copy.
ROOT = os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources")
MANIFEST = os.path.join(ROOT, "manifest.json")


def _manifest():
    if not os.path.exists(MANIFEST):
        sys.exit(
            f"FATAL: {MANIFEST} not found.\n"
            f"       The external volume (/Volumes/MacieExternal) looks absent or\n"
            f"       unmounted. Nothing that reads a downloaded dataset can run\n"
            f"       until it is back; the repo itself is unaffected.\n"
            f"       Once mounted, regenerate the index with:\n"
            f"         python3 scripts/sourcesManifest.py --verify")
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def archive_dir(slug: str) -> str:
    """The immutable download directory for `slug`."""
    _manifest()
    path = os.path.join(ROOT, "archives", slug)
    if not os.path.isdir(path):
        sys.exit(f"FATAL: no archive on disk for '{slug}' at {path}\n"
                 f"       See manifest.json for its source URL.")
    return path


def work_dir(slug: str) -> str:
    """The derived-artifact directory for `slug`, created if absent."""
    _manifest()
    path = os.path.join(ROOT, "work", slug)
    os.makedirs(path, exist_ok=True)
    return path


def work_file(slug: str, name: str) -> str:
    """A single derived artifact, erroring clearly if it has not been produced."""
    path = os.path.join(work_dir(slug), name)
    if not os.path.exists(path):
        sys.exit(f"FATAL: {path} does not exist.\n"
                 f"       It is a derived artifact of the '{slug}' download and is\n"
                 f"       not kept in git. Re-run the script that produces it.")
    return path


def record_transformed(slug: str, name: str, records) -> str:
    """Write a transformer's output as JSONL into `slug`'s work dir, return
    the path.

    This is the materialized output of a transform step -- the species/taxon
    records produced from the archive, captured before any merge/dedupe
    decision -- so a bulk import can be reviewed or replayed without
    re-fetching or re-parsing the source. `sourcesManifest.py` already scans
    work/ recursively, so rebuilding the manifest after this picks it up
    with no further registration. Overwritten on each run, same as every
    other file under work/: regenerable, not an audit trail -- name the file
    something stable (e.g. "transformed.jsonl"), not timestamped, unless the
    caller genuinely wants to keep every past run.
    """
    path = os.path.join(work_dir(slug), name)
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def source_url(slug: str) -> str:
    return _manifest()["sources"][slug]["url"]


def licence_of(slug: str) -> str:
    return _manifest()["sources"][slug]["licence"]
