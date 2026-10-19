#!/usr/bin/env python3
"""Transform step for a ColDP/DwC-A archive -- the split-pipeline sibling
of importColChecklist.py.

Shares importColChecklist.route_species() with the direct-write importer,
so kingdom inference, family matching and refusal detection are identical
between the two paths -- this script only differs in what happens with a
species once it is staged. Instead of writing family files directly, it
writes a transformed.jsonl sidecar (scripts/sources.py's
record_transformed()) for importTransformed.py to apply later, possibly on
a different machine, against a running importwrite instance. That is the
whole point of the split: the machine with the archive (Macie, where the
external volume lives) does not have to be the machine that holds the git
checkout and runs importwrite (q-bert).

Usage:
    python3 scripts/transformColChecklist.py <archive.zip> <work-slug>
    python3 scripts/transformColChecklist.py <archive.zip> <work-slug> --apply
    python3 scripts/transformColChecklist.py <archive.zip> <work-slug> --apply --kingdom plantae

<work-slug> is the slug record_transformed() files this run's output
under (sources.py's work_dir) -- a name you choose for this batch, not a
ChecklistBank dataset id -- and becomes the first argument to
importTransformed.py when applying it:

    IMPORTWRITE_URL=http://q-bert:8089 python3 scripts/importTransformed.py <work-slug>

Without --apply this only prints the same routing stats
importColChecklist.py's own dry run would (nothing is written, including
to the pending-family store) -- run it bare first to see the numbers
before committing to a transform.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importColChecklist as ICC  # noqa: E402
import sources  # noqa: E402


def transform_records(r: "ICC.RoutedSpecies"):
    """Yield one importTransformed.py-shaped record per staged species.

    route_species() stages by (kingdom, slug) once it has matched a family
    NAME to one of our known slugs -- it never checks that slug actually
    has a data file on disk. importColChecklist.py's own direct-write tail
    does that check itself (see its "one index, built once" comment) before
    writing; this path has no such tail, so a slug with no file would reach
    importwrite instead, which has nowhere to apply it and errors the whole
    run -- found 2026-10-19 on WoRMS 2011, which routes single species into
    three families (petiveriaceae, umbellinaceae, vermiporellaceae) that
    exist as names in our family-matching data but were never scaffolded.
    Skip those here, the same way main() does, rather than crash a run that
    may have thousands of other species to apply first.
    """
    import glob as _glob
    files = {}
    for f in _glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
        files.setdefault(os.path.basename(f)[:-5], []).append(f)

    for (kingdom, slug), rows in sorted(r.staged.items()):
        if not files.get(slug):
            print(f"  ! {slug}: no family data file, skipping "
                  f"{len(rows)} staged species")
            continue
        for g, bare, authorship, source_id, fam_name in rows:
            species = {
                "id": ICC.SF.node_id(ICC.SF.PREFIX["SPECIES"], bare, authorship or ""),
                "name": bare,
                "rank": "SPECIES",
                "subspeciesCount": 0,
                "sourcedFrom": ICC.SOURCE,
                "lineage": g,
            }
            if authorship:
                species["authorship"] = authorship
            if source_id:
                species["sourceIds"] = {r.source_key: source_id}
            yield {
                "kingdom": kingdom,
                "family": slug,
                # lineage here is the FAMILY name, matching the convention
                # importColChecklist.py's direct-write path uses for the
                # genus node (fname, not slug) -- see its comment on why
                # stamping family onto species instead was a 72,270-node bug.
                "genus": {"name": g, "sourcedFrom": ICC.SOURCE, "lineage": fam_name},
                "species": species,
            }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("work_slug")
    ap.add_argument("--apply", action="store_true",
                     help="write the transform sidecar and record refusals "
                          "in the pending-family store; without it, only "
                          "the routing stats print")
    ap.add_argument("--kingdom", default="",
                     help="same override as importColChecklist.py -- see "
                          "its --help for why this exists")
    args = ap.parse_args()

    r = ICC.route_species(args.archive, kingdom_override=args.kingdom)
    ICC.record_misses(r, args.archive, args.apply)

    if not r.staged:
        print("\n  nothing to do")
        return 0

    if not args.apply:
        print("\n  (dry run -- pass --apply to write the transform sidecar)")
        return 0

    meta = r.meta
    path = sources.record_transformed(
        args.work_slug, "transformed.jsonl", transform_records(r),
        source=ICC.SOURCE,
        source_dataset_id=meta.get("key") or meta.get("alias") or "",
        source_url=meta.get("url") or "",
        archive_path=args.archive,
        transformer="importColChecklist.route_species",
    )
    staged_total = sum(len(v) for v in r.staged.values())
    print(f"\n  wrote {path}  ({staged_total:,} species staged, "
          f"not yet applied to the tree)")
    print(f"  apply with: IMPORTWRITE_URL=<url> "
          f"python3 scripts/importTransformed.py {args.work_slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
