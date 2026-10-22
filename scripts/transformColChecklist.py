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
import zipfile
import importColChecklist as ICC  # noqa: E402
import authorityIndex  # noqa: E402
import sources  # noqa: E402


def _is_txtree(path):
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            for n in names:
                if n.lower().endswith(".txtree"):
                    return True
                # A non-DwC-A archive with no .txtree and no expected
                # DwCA members (taxon.txt / .tsv / name.tsv etc.)
                # is an unsupported format; skip gracefully rather than crash.
            # No .txtree and no standard DwCA members either
            base_names = [m.rsplit("/", 1)[-1].lower() for m in names if not m.startswith("__MACOSX")]
            has_dwc = any("taxon" in b or "name" in b for b in base_names)
            return False if has_dwc else "unsupported"
    except zipfile.BadZipFile:
        return "unsupported"
    return False


def transform_records(r: "ICC.RoutedSpecies", diverted: list):
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

    Before yielding, each candidate is checked against authorityIndex --
    the same tree-wide (kingdom, authority, key) index merge_family's
    direct-write path already consults, but only as a warning there
    (importSpeciesFile.py's own docstring: "a false positive here would
    silently drop good data"). importwrite's own duplicate gate
    (crossfamily.go) is session-local, not tree-wide -- "a species in a
    family this process has never loaded is invisible to it until that
    family is loaded" -- so this split pipeline had no tree-wide check at
    all until now. A hit here means a candidate's external id already
    belongs to a species in a DIFFERENT family: diverted into `diverted`
    instead of yielded, so it lands in needs-validation.jsonl rather than
    silently creating (or racing to create) a second copy. Found
    2026-10-22: 24 of the ~59 cross-kingdom duplicates and homonym-bugs
    cleaned up by hand this session came in exactly this way.
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

            if source_id:
                try:
                    hits = authorityIndex.conflicts_for(
                        kingdom, slug, bare, {r.source_key: source_id})
                except Exception as e:
                    hits = []
                    print(f"  ! authorityIndex lookup failed for {bare!r}, "
                          f"letting it through unchecked: {e}")
                if hits:
                    auth, akey, other_name, other_slug, other_id = hits[0]
                    diverted.append({
                        "kingdom": kingdom, "intendedFamily": slug,
                        "species": species, "genusName": g,
                        "conflict": {"authority": auth, "key": akey,
                                     "existingName": other_name,
                                     "existingFamily": other_slug,
                                     "existingId": other_id},
                    })
                    continue

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

    # Exit codes 3 and 4 are distinct from 0 (handled) and 1 (crashed) so
    # importQueueDriver.py can tell "this archive needs different handling"
    # from "nothing new to stage" -- both print and return 0 would otherwise
    # look identical to the driver, which then tries to apply a
    # transformed.jsonl that was never written and fails every loop
    # (found 2026-10-22: checklistbank-1046/1118/1190 stuck retrying).
    txtree_check = _is_txtree(args.archive)
    if txtree_check is True:
        print(f"\n  archive uses .txtree format (txtree.py handles separately); "
              f"skipping ColDP pipeline. See docs/import.md for the .txtree path.")
        return 3
    if txtree_check == "unsupported":
        print(f"\n  archive at {args.archive} has no .txtree member and no "
              f"recognised DwCA/ColDP table; skipping (unsupported format).")
        return 4

    r = ICC.route_species(args.archive, kingdom_override=args.kingdom)
    ICC.record_misses(r, args.archive, args.apply)

    if not r.staged:
        print("\n  nothing to do")
        return 0

    if not args.apply:
        print("\n  (dry run -- pass --apply to write the transform sidecar)")
        return 0

    meta = r.meta
    diverted = []
    path = sources.record_transformed(
        args.work_slug, "transformed.jsonl", transform_records(r, diverted),
        source=ICC.SOURCE,
        source_dataset_id=meta.get("key") or meta.get("alias") or "",
        source_url=meta.get("url") or "",
        archive_path=args.archive,
        transformer="importColChecklist.route_species",
        routing_stats={
            "offered": r.cand_count,
            "alreadyHeld": r.held,
            "nonBinominal": r.nonb,
            "refused": r.refused,
            "refusalRate": round(r.refused / max(1, r.cand_count), 4),
            "missedFamilies": len({f for _kk, f in r.missed if f}),
        },
    )
    staged_total = sum(len(v) for v in r.staged.values())
    print(f"\n  wrote {path}  ({staged_total:,} species staged, "
          f"not yet applied to the tree)")

    if diverted:
        vpath = sources.record_transformed(
            args.work_slug, "needs-validation.jsonl", diverted,
            source=ICC.SOURCE,
            source_dataset_id=meta.get("key") or meta.get("alias") or "",
            source_url=meta.get("url") or "",
            archive_path=args.archive,
            transformer="transformColChecklist.transform_records (authority conflict)",
        )
        print(f"  wrote {vpath}  ({len(diverted):,} species held back -- "
              f"external id already belongs to a species in a different "
              f"family, see the conflict field in each row for where)")

    print(f"  apply with: IMPORTWRITE_URL=<url> "
          f"python3 scripts/importTransformed.py {args.work_slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
