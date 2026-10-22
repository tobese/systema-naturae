#!/usr/bin/env python3
"""The source pipeline's own state, so the dashboard shows what's actually
next instead of a hand-maintained list that goes stale the moment anything
moves (see docs/dataset-inbox.md's 2026-10-19 top section and
scripts/importLogServer.py's queue panel, both hand-edited and both wrong
within the same session that wrote them).

One file per source under data/source-queue/, named <key>.json (a
ChecklistBank key, or whatever slug a non-ChecklistBank source uses
elsewhere in this repo) -- moved off a single data/source-queue.json
(2026-10-22) because a process holding a stale in-memory copy of the
WHOLE queue clobbered every other source's concurrent update when it
saved its own. Small and factual -- same footing as data/import-log.jsonl,
data/dedupe-log.jsonl -- so it is tracked in git, not pushed out to the
external volume the way pending/families.jsonl is.

A source moves through `stage` in roughly this order, though any stage can
be set directly (a source already known to be blocked never needs to pass
through "triaged"):

    candidate   -- known (scripts/triageNext.py), not yet downloaded
    downloaded  -- archive on disk, not yet triaged
    triaging    -- a dry run is actively running right now (set this
                   *before* launching it, not after -- the whole point is
                   a viewer mid-tick sees "running", not a stale
                   "downloaded" that silently became "triaged" minutes
                   later with no step in between)
    triaged     -- dry run done; `triaged` holds the numbers. This is where
                   the pipeline stops and waits: `add()` below refuses to
                   register a key the manifest already has a verdict for,
                   but it can't catch a source that is simply *new* and
                   risky (bacteria-heavy, a synthetic tree, NC-licensed) --
                   that judgement call is what "triaged" is for.
    queued      -- verdict is "take", not yet applied
    applying    -- the split pipeline is actively running right now, same
                   reasoning as "triaging"
    applied     -- split pipeline finished; `applied` holds the result
    declined    -- verdict is "decline"; `reason` says why
    blocked     -- can't proceed yet (no archive, needs a decision); `reason` says why
    needs-rerun -- applied before, but something downstream changed (a
                   family got scaffolded, an importer bug got fixed) and
                   re-running would likely pick up more. `rerunCommand`
                   (a JSON argv list, see `set --rerun-command`) says
                   exactly what scripts/pipelineOrchestrator.py should
                   run -- a source may need a different tool than the
                   standard transform/apply pipeline (TAXREF needed
                   importColStage2.py --kingdom for each kingdom, not a
                   plain re-run)

`history` is append-only -- every `set` call adds one entry with the stage
and a timestamp, even if the stage itself didn't change (an updated
`triaged` block still gets a history row) -- so "when did this last
move" is answerable without re-deriving it from git blame.

Usage:
    python3 scripts/sourceQueue.py add --key 311726 \\
        --title "ASEAN KBA Trigger Species Checklist" --size 19723 --licence "cc by"
    python3 scripts/sourceQueue.py set --key 311726 --stage downloaded
    python3 scripts/sourceQueue.py set --key 311726 --stage triaged \\
        --offered 19723 --already-held 12000 --staged 500 --refused 200 \\
        --families 12 --missed-families 1
    python3 scripts/sourceQueue.py set --key 311726 --stage declined --reason "..."
    python3 scripts/sourceQueue.py set --key 311726 --stage applied \\
        --added 480 --merged 20 --cross-family 0
    python3 scripts/sourceQueue.py report

`add` is the one gate every path into this queue has to pass through --
the manual CLI, a bulk script, and scripts/importQueueDriver.py's own
refill all call it. It cross-checks data/manifest.json (the same
held_keys() scripts/triageNext.py uses) and refuses to (re-)register a key
the manifest already has a verdict for, instead of silently resetting it
to "candidate". Found 2026-10-22: a bulk add that bypassed triageNext.py's
own filtering re-queued six already-taken sources (Dyntaxa, Nortaxa, eunis,
taicol, IRMNG, the Brazilian Fauna catalogue) and three explicitly-declined
ones (OTL, ZooBank, INA), plus GTDB -- on hold by policy, not a triage
question at all. triageNext.py's filter is only as good as the paths that
actually call it; this makes the bypass impossible instead of relying on
every future caller to remember.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR) + "/data"
STORE = os.path.join(DATA_DIR, "source-queue")
EVENTS_LOG = os.path.join(DATA_DIR, "pipeline-events.jsonl")

STAGES = ("candidate", "downloaded", "triaging", "triaged", "queued",
          "applying", "applied", "declined", "blocked", "needs-rerun")


def _entry_path(key: str) -> str:
    return os.path.join(STORE, f"{key}.json")


def read_entry(key: str) -> dict | None:
    path = _entry_path(key)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def log_event(key: str, stage: str, **extra) -> None:
    """Append one line to data/pipeline-events.jsonl -- NOT the source of
    truth (that's each source's own file in data/source-queue/, including
    its own `history` list), just a flat chronological feed so "what
    happened across the whole pipeline, in order" doesn't mean scanning
    every one of those files and interleaving their `history` entries by
    hand. Same append-only shape as data/import-log.jsonl, which already
    tolerates concurrent writers (a single `write()` of one line is
    atomic on a local filesystem at this size)."""
    row = {"at": _now(), "key": key, "stage": stage}
    row.update({k: v for k, v in extra.items() if v is not None and v != ""})
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EVENTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_entry(key: str, row: dict) -> None:
    """Atomic write of exactly one source's own file -- the whole point of
    moving off a single data/source-queue.json (2026-10-22): a process
    holding a stale in-memory copy of the WHOLE queue used to overwrite
    every other source's concurrent update when it saved, which is what
    silently reverted manual `set` calls made while the driver was still
    running mid-pass on a stale snapshot. A write here can only ever
    clobber this one source's own file."""
    os.makedirs(STORE, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=STORE, prefix=f"{key}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(row, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, _entry_path(key))
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def read_store() -> dict:
    """Every source, keyed by its own id -- for callers that want the
    whole picture (the dashboard, `report`, refill's dedup check) rather
    than one entry. Each file is read independently, so one source's
    update is never visible mid-write to a concurrent reader of another."""
    if not os.path.isdir(STORE):
        return {}
    out = {}
    for name in sorted(os.listdir(STORE)):
        if name.endswith(".json"):
            key = name[: -len(".json")]
            row = read_entry(key)
            if row is not None:
                out[key] = row
    return out


def write_store(doc: dict) -> None:
    """Write every entry in `doc` to its own file. Only for migrating an
    old single-file store or bulk-seeding from a script -- `set`/`add`
    below call `write_entry` for the one key they touched, not this."""
    for key, row in doc.items():
        write_entry(key, row)


def _manifest_resolved_keys() -> set[str]:
    """ChecklistBank slugs the manifest already has a verdict for -- the
    same key/DOI/title matching triageNext.py's held_keys() does, kept here
    too so `add` can refuse a bypass regardless of which script called it."""
    manifest = os.path.join(
        os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources"),
        "manifest.json")
    try:
        src = json.load(open(manifest, encoding="utf-8")).get("sources", {})
    except (OSError, ValueError):
        return set()
    return {slug for slug in src if re.match(r"checklistbank-\d+$", slug)}


def cmd_add(args) -> None:
    row = read_entry(args.key)
    if row is None and args.key in _manifest_resolved_keys():
        sys.exit(
            f"FATAL: {args.key} already has a verdict in the manifest -- "
            f"check docs/dataset-inbox.md and scripts/triageNext.py before "
            f"re-adding it. If you mean to deliberately re-triage it (something "
            f"downstream changed), use `set --stage needs-rerun` instead of `add`."
        )
    row = row or {"key": args.key, "history": []}
    row["title"] = args.title or row.get("title", "")
    row["size"] = args.size if args.size is not None else row.get("size")
    row["licence"] = args.licence or row.get("licence", "")
    if args.archive_path:
        row["archivePath"] = args.archive_path
    row.setdefault("stage", "candidate")
    row["history"].append({"stage": row["stage"], "at": _now()})
    write_entry(args.key, row)
    log_event(args.key, row["stage"], action="add", title=row["title"])
    print(f"  {args.key}: {row['stage']} ({row['title']})")


def cmd_set(args) -> None:
    row = read_entry(args.key)
    if row is None:
        sys.exit(f"FATAL: {args.key} not in {STORE} -- run `add` first")
    row["stage"] = args.stage
    if args.archive_path:
        row["archivePath"] = args.archive_path
    if args.kingdom_override:
        row["kingdomOverride"] = args.kingdom_override

    if args.stage == "triaged":
        row["triaged"] = {
            "offered": args.offered, "alreadyHeld": args.already_held,
            "staged": args.staged, "refused": args.refused,
            "refusalRate": (round(args.refused / args.offered, 4)
                            if args.refused is not None and args.offered else None),
            "families": args.families, "missedFamilies": args.missed_families,
        }
    if args.stage in ("declined", "blocked", "queued") and args.reason:
        row["reason"] = args.reason
    if args.stage == "needs-rerun":
        if args.reason:
            row["reason"] = args.reason
        if args.rerun_command:
            row["rerunCommand"] = json.loads(args.rerun_command)
    if args.stage == "applied":
        row["applied"] = {
            "added": args.added, "merged": args.merged,
            "crossFamily": args.cross_family, "at": _now(),
        }

    row.setdefault("history", []).append({"stage": args.stage, "at": _now()})
    write_entry(args.key, row)
    log_event(args.key, args.stage, action="set", reason=row.get("reason"))
    print(f"  {args.key}: -> {args.stage}")


def cmd_report(_args) -> None:
    doc = read_store()
    if not doc:
        print("  source queue is empty")
        return
    by_stage: dict = {}
    for row in doc.values():
        by_stage.setdefault(row.get("stage", "?"), []).append(row)
    for stage in STAGES:
        rows = by_stage.pop(stage, [])
        if not rows:
            continue
        print(f"\n  {stage} ({len(rows)})")
        for row in sorted(rows, key=lambda r: -(r.get("size") or 0)):
            extra = ""
            if stage == "triaged" and row.get("triaged"):
                m = row["triaged"]
                extra = f"  staged {m.get('staged', '?')}"
            if stage in ("declined", "blocked") and row.get("reason"):
                extra = f"  {row['reason'][:60]}"
            if stage == "applied" and row.get("applied"):
                extra = f"  +{row['applied'].get('added', '?')}"
            print(f"      {row['key']:>8}  {row.get('title', '')[:50]:<50}{extra}")
    for stage, rows in by_stage.items():
        print(f"\n  {stage} ({len(rows)}, unrecognized stage)")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", help="register a new candidate source")
    p.add_argument("--key", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--size", type=int, default=None)
    p.add_argument("--licence", default="")
    p.add_argument("--archive-path", default="")

    p = sub.add_parser("set", help="move a source to a new stage")
    p.add_argument("--key", required=True)
    p.add_argument("--stage", required=True, choices=STAGES)
    p.add_argument("--archive-path", default="")
    p.add_argument("--kingdom-override", default="")
    p.add_argument("--offered", type=int, default=None)
    p.add_argument("--already-held", type=int, default=None)
    p.add_argument("--staged", type=int, default=None)
    p.add_argument("--refused", type=int, default=None)
    p.add_argument("--families", type=int, default=None)
    p.add_argument("--missed-families", type=int, default=None)
    p.add_argument("--reason", default="")
    p.add_argument("--added", type=int, default=None)
    p.add_argument("--merged", type=int, default=None)
    p.add_argument("--cross-family", type=int, default=None)
    p.add_argument("--rerun-command", default="",
                    help="only with --stage needs-rerun: a JSON-encoded "
                         "argv list, e.g. '[\"python3\", \"scripts/"
                         "importColStage2.py\", \"--archive\", \"...\", "
                         "\"--kingdom\", \"Animalia\", \"--apply\"]' -- "
                         "scripts/pipelineOrchestrator.py runs this "
                         "verbatim when it picks the source up, so store "
                         "exactly the command you'd run by hand")

    sub.add_parser("report", help="print every source grouped by stage")

    args = ap.parse_args()
    {"add": cmd_add, "set": cmd_set, "report": cmd_report}[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
