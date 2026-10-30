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
# SN_QUEUE_DIR (relative to the repo root, or absolute) points at another
# queue -- q-bert's bacteria/viruses ordinator uses data/source-queue-bv, the
# same variable services/import-ordinator reads.
STORE = os.path.join(os.path.dirname(SCRIPT_DIR),
                     os.environ.get("SN_QUEUE_DIR") or os.path.join("data", "source-queue"))
EVENTS_LOG = os.path.join(DATA_DIR, "pipeline-events.jsonl")

STAGES = ("candidate", "downloaded", "triaging", "transforming", "triaged", "queued",
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


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


STOPWORDS = {"the", "a", "an", "of", "and", "or", "dataset", "checklist",
             "catalogue", "catalog", "database", "register", "online", "list",
             # Prepositions: without these, two titles sharing only a common
             # template -- "Taxon list of Hymenoptera from Germany" vs. an
             # already-held "Taxon list of fungi... from Germany compiled by
             # the DGfM", both real, different, genuinely complementary
             # datasets in the same German-monitoring series -- hit 75%
             # overlap on "taxon"+"from"+"germany" alone and got wrongly
             # blocked as a duplicate (found 2026-10-25, --all-types sweep).
             "from", "by", "in", "with", "for", "at", "on", "to", "as"}


def _title_tokens(title: str) -> set[str]:
    """Words in a title, lowercased, with stopwords and bare numbers/years
    dropped -- "ITIS, The Integrated Taxonomic Information System (dataset
    2144)" and "Integrated Taxonomic Information System (ITIS)" share no
    normalised *string* (different word order, one has a dataset id, one
    has the acronym in parens) but share almost every meaningful *token*,
    which is what title matching across catalogs actually needs to catch."""
    words = re.findall(r"[a-z0-9]+", (title or "").lower())
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def _manifest_resolved() -> tuple[set[str], set[str], list[tuple[str, set[str]]]]:
    """Every way the manifest can claim a dataset already has a verdict:
    its slug key, any DOI in its identifier/url/title, and its title's
    token set -- the same three checks triageNext.py's held_keys() does for
    ChecklistBank, kept here too so `add` refuses a bypass regardless of
    which catalog or script presented the "new" key. A GBIF dataset UUID
    for a dataset we already hold under a checklistbank-<N> slug (or any
    other registered slug) will not match on key, but should still match
    on DOI or title -- which a bare `re.match(r"checklistbank-\\d+$", slug)`
    (the previous implementation here) could never catch, since it only
    ever compared a candidate's own key against itself. That gap let
    scripts/triageGbif.py --add re-queue 16 already-held/already-decided
    sources (ITIS, WoRMS, WCVP, ZooBank, IRMNG, Wikidata Species, and
    others) under fresh GBIF keys on 2026-10-25 -- see docs/import.md
    section 11's note on the 2026-10-22 incident this was meant to guard
    against in the first place."""
    manifest = os.path.join(
        os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources"),
        "manifest.json")
    keys, dois, titles = set(), set(), []
    try:
        src = json.load(open(manifest, encoding="utf-8")).get("sources", {})
    except (OSError, ValueError):
        return keys, dois, titles
    for slug, rec in src.items():
        keys.add(slug)
        blob = " ".join(str(rec.get(f) or "") for f in ("identifier", "url", "title"))
        for doi in re.findall(r"10\.\d{4,9}/\S+", blob):
            dois.add(_norm(doi.rstrip(".,;)")))
        if rec.get("title"):
            titles.append((rec["title"], _title_tokens(rec["title"])))
    return keys, dois, titles


def _title_overlap_match(candidate_tokens, titles, threshold=0.7):
    """The manifest title (and the ratio) with the strongest token overlap
    against `candidate_tokens`, or None if nothing clears `threshold` of
    the SMALLER title's tokens -- asymmetric on purpose, since one side is
    often a bare name ("Wikidata Species") and the other a fuller citation
    ("Wikidata Species (ChecklistBank dataset 314569)")."""
    if not candidate_tokens:
        return None
    best = None
    for title, tokens in titles:
        if not tokens:
            continue
        shared = candidate_tokens & tokens
        ratio = len(shared) / min(len(candidate_tokens), len(tokens))
        if ratio >= threshold and (best is None or ratio > best[1]):
            best = (title, ratio)
    return best


def cmd_add(args) -> None:
    row = read_entry(args.key)
    if row is None and not args.force:
        keys, dois, titles = _manifest_resolved()
        doi_match = next((d for d in re.findall(r"10\.\d{4,9}/\S+", args.title or "")
                           if _norm(d.rstrip(".,;)")) in dois), None)
        title_match = _title_overlap_match(_title_tokens(args.title), titles)
        if args.key in keys or doi_match or title_match:
            reason = (f"title overlaps {title_match[0]!r} ({title_match[1]:.0%} of "
                       f"the shorter title's words)" if title_match
                       else f"DOI {doi_match}" if doi_match
                       else "key")
            sys.exit(
                f"FATAL: {args.key!r} ({args.title!r}) already has a verdict in "
                f"the manifest -- matched on {reason}. Check docs/dataset-inbox.md "
                f"and scripts/triageNext.py before re-adding it under a new key "
                f"(a different catalog, e.g. GBIF vs. ChecklistBank, often "
                f"republishes the same dataset under its own key/DOI). If this "
                f"is genuinely a different dataset that happens to share words "
                f"with one we hold, re-run with --force. If you mean to "
                f"deliberately re-triage the same dataset (something downstream "
                f"changed), use `set --stage needs-rerun` instead of `add`."
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
    # Any stage can carry a reason (a re-take, a reset, a requeue) -- it
    # used to be kept only for declined/blocked/queued/needs-rerun and
    # silently dropped otherwise.
    if args.reason:
        row["reason"] = args.reason
    if args.stage == "needs-rerun":
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
                extra = f"  {row['reason']}"
            if stage == "applied" and row.get("applied"):
                added = row["applied"].get("added")
                if added is None:
                    extra = "  (no metrics recorded)"
                else:
                    extra = f"  +{added}"
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
    p.add_argument("--force", action="store_true",
                    help="skip the manifest key/DOI/title overlap check "
                         "(use only once you've confirmed by hand this is "
                         "not the dataset the overlap check thinks it is)")

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
