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
import time
import uuid as _uuid

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


def meta_path_for(data_path: str) -> str:
    if data_path.endswith(".jsonl"):
        return data_path[: -len(".jsonl")] + ".meta.json"
    return data_path + ".meta.json"


def record_transformed(slug: str, name: str, records, *,
                        source: str = "",
                        source_dataset_id: str = "",
                        source_url: str = "",
                        archive_path: str = "",
                        archive_sha256: str = "",
                        fetched_at: str = "",
                        transformer: str = "") -> str:
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

    Passing any of the metadata keywords also writes a sidecar next to it
    (`transformed.jsonl` -> `transformed.meta.json`):

      - `source` / `source_dataset_id` / `source_url`: the ORIGIN's own
        identifiers, not ours -- `source_dataset_id` is e.g. a
        ChecklistBank dataset key or a GBIF `datasetKey`, distinct from
        `slug`, which is our naming for it.
      - `archive_path` / `archive_sha256`: where the original download
        this batch was transformed from lives, when there is one -- omit
        both for a live-REST source with no archive file to point at.
      - `fetched_at`: when the underlying data was retrieved. Kept
        separate from the sidecar's own `transformedAt` (set here,
        always, to now) on purpose: a transform can be re-run against an
        already-downloaded archive days later, and conflating the two
        timestamps would lose that.

    Always written by this function, not the caller: `runId` (a fresh
    uuid4 -- identifies THIS batch, not any one species; a species gets
    its own uuid from importwrite at merge time, not here),
    `transformedAt`, and `recordCount`.

    No metadata keywords given -> no sidecar, so existing callers are
    unaffected.
    """
    path = os.path.join(work_dir(slug), name)
    count = 0
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    if any([source, source_dataset_id, source_url, archive_path, archive_sha256, fetched_at, transformer]):
        doc: dict = {}
        if source:
            doc["source"] = source
        if source_dataset_id:
            doc["sourceDatasetId"] = source_dataset_id
        if source_url:
            doc["sourceUrl"] = source_url
        if archive_path or archive_sha256:
            archive: dict = {}
            if archive_path:
                archive["path"] = archive_path
            if archive_sha256:
                archive["sha256"] = archive_sha256
            doc["archive"] = archive
        if fetched_at:
            doc["fetchedAt"] = fetched_at
        if transformer:
            doc["transformer"] = transformer
        doc["runId"] = str(_uuid.uuid4())
        doc["transformedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        doc["recordCount"] = count
        with open(meta_path_for(path), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    return path


def source_url(slug: str) -> str:
    return _manifest()["sources"][slug]["url"]


def licence_of(slug: str) -> str:
    return _manifest()["sources"][slug]["licence"]
