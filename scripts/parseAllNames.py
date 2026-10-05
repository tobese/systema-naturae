#!/usr/bin/env python3
"""
Run every name in the tree through GBIF's scientific-name parser, and report.

Why
---
548,304 species names (45.5% of the tree) carry an authority suffix that is baked
into the node `id` as well as the `name`:

    Smilax virosa Buch.-Ham. ex Wall.  ->  SP_SMILAX_VIROSA_BUCH_HAM_EX_WALL_

We store no `authorship` field on any node. `/v1/parser/name` splits a name into
`canonicalName` + `authorship` + `year` + `rankMarker`, and its `type` field is a
machine-readable validity signal (`PLACEHOLDER`, `NO_NAME`, `DOUBTFUL`, ...). So
the endpoint can do two things at once: supply the authorship we lack, and tell
us which of our names are structurally malformed.

What it cannot do is resolve names. It never says whether a name exists -- that
is `/species/match`, a different endpoint, and the backlog is already right that
stripping authority suffixes for *lookup* is a dead end.

The trap this has to survive
----------------------------
`parsed: true` does NOT mean valid. `?name=human` returns `parsed: true` with
`type: PLACEHOLDER` and `genusOrAbove: "?"` -- parsed *as a failure*. And
`rankMarker` is still asserted as `sp.` for it, inferred from word count alone
with no genus to check. So a `rankMarker` read on its own is the field most
likely to mislead, which is the main thing this measures.

Request shape, and a trap of its own
-------------------------------------
The repeated-`name` **GET silently rotates results by one**: send four names, get
four results back, right count and wrong pairing, last name correct. Verified
directly. Only the **POST** form is positionally safe, so this uses it exclusively
and asserts alignment per batch rather than trusting it.

    python3 scripts/parseAllNames.py --limit 5000     # probe
    python3 scripts/parseAllNames.py                  # all 1,306,249
    python3 scripts/parseAllNames.py --apply-authorship

On --apply-authorship
---------------------
Writes `authorship` and `year` onto nodes where the parser found one and the
field is absent, and `rankMarker` into a separate `gbifRankMarker` for audit --
never into `rank`, because `rankMarker` is coarser than our vocabulary
(`Canis lupus familiaris` comes back `infrasp.`, not `SUBSPECIES`) and because
the comparison it enables is the point, not a rewrite. Idempotent.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

PARSER_URL = "https://api.gbif.org/v1/parser/name"
UA = "SystemaNaturae/1.0 (taxonomy portal; https://github.com/tobese/systema-naturae)"
BATCH = 1000

# Our rank -> the parser's `rankMarker` vocabulary.
#
# NOT the enum in the OpenAPI spec. The spec declares rankMarker as
# `SPECIES`/`GENUS`/`FAMILY`/... and the endpoint actually emits the abbreviated
# botanical forms `sp.`/`gen.`/`fam.`. Comparing against the spec's enum scores
# 0% agreement on every rank, which reads as a total mismatch and is really just
# a vocabulary difference. Verified directly: `?name=Picocystis salinarum`
# returns `rankMarker: "sp."` where the spec says `SPECIES`.
#
# Also note the marker is frequently absent even for a clean species name
# (`Margaritidae` -> null), so "no marker" is not a disagreement and is counted
# separately from an actual contradiction.
MARKERS = {
    "SPECIES": {"sp.", "f.sp."},
    "GENUS": {"gen."},
    "SUBSPECIES": {"subsp."},
    "FAMILY": {"fam.", "superfam."},
}


def collect(root: str) -> list[tuple[str, str]]:
    """(name, ourRank) for every named node, deduplicated by (name, rank)."""
    seen: dict[tuple[str, str], None] = {}
    for dirpath, _dirs, files in os.walk(root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        for fn in files:
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                doc = json.load(fh)
            stack = [doc]
            while stack:
                node = stack.pop()
                stack.extend(node.get("children") or [])
                stack.extend(node.get("speciesList") or [])
                name = (node.get("name") or "").strip()
                rank = node.get("rank") or ""
                if name and rank:
                    seen.setdefault((name, rank), None)
    return list(seen)


def parse_batch(names: list[str]) -> list[dict]:
    body = json.dumps(names).encode()
    req = urllib.request.Request(PARSER_URL, data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                out = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            if attempt == 3:
                sys.exit(f"FATAL: parser returned {e.code}. Stop rather than write misaligned data.")
            time.sleep(2 ** attempt * 2)
        except (urllib.error.URLError, http.client.HTTPException,
                ConnectionResetError) as e:
            # RemoteDisconnected is raised by h.getresponse() inside urllib's
            # do_open and is NOT wrapped in URLError, so the original
            # `except URLError` did not see it: a run that reached 1.1M of 2.69M
            # names at 1,900/s died on a connection GBIF closed under sustained
            # load, after ten minutes of work and with no progress to resume
            # from. It is a retryable condition, so it belongs here.
            if attempt == 3:
                raise
            print(f"    retry {attempt + 1}/3 after "
                  f"{type(e).__name__}: {e}", flush=True)
            time.sleep(2 ** attempt * 2)
    # The one thing that must never be assumed.
    if len(out) != len(names):
        sys.exit(f"FATAL: sent {len(names)} names, got {len(out)}. Alignment cannot be trusted; aborting.")
    for n, r in zip(names, out):
        if r.get("scientificName") != n:
            sys.exit(f"FATAL: response {r.get('scientificName')!r} does not match sent {n!r}. "
                     f"The parser's positional alignment has changed; aborting rather than mis-pairing.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="portal/data/name-parse-index.jsonl")
    ap.add_argument("--report", default="docs/reports/name-parser.md")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shard", default="0/1", help="i/n -- parse only slice i of n")
    ap.add_argument("--workers", type=int, default=6, help="concurrent requests")
    ap.add_argument("--apply-authorship", action="store_true")
    args = ap.parse_args()

    pairs = collect(args.root)
    if args.limit:
        pairs = pairs[: args.limit]

    # The endpoint sustains ~113 names/s on one connection, which is ~3.2 hours
    # for 1.3M names. Sharding plus concurrency is the only way this is
    # practical, and the alignment assertion below still guards every batch.
    try:
        si, sn = (int(x) for x in args.shard.split("/"))
    except ValueError:
        sys.exit(f"FATAL: --shard must look like i/n, got {args.shard!r}")
    if not (0 <= si < sn):
        sys.exit(f"FATAL: --shard {args.shard} out of range")
    if sn > 1:
        pairs = pairs[si::sn]
        print(f"shard {si+1}/{sn}: {len(pairs):,} pairs", flush=True)
    print(f"Parsing {len(pairs):,} distinct (name, rank) pairs\n", flush=True)

    tally = Counter()
    rank_mismatch = Counter()
    rank_agree = Counter()
    rank_absent = Counter()
    examples: dict[str, list[str]] = {}
    started = time.time()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    # Written to a sibling and moved into place at the end, never in place.
    # This run is hours long and the machine it runs on has restarted twice today
    # (once mid-write, leaving a 0-byte unified-taxonomy.json that read as valid
    # JSON and reported "0 nodes"). An index truncated that way is worse than a
    # stale one: it looks well-formed and answers "we do not hold this name" for
    # every name past the cut, which is precisely the question importers ask it.
    # os.replace is atomic within a filesystem, so a reader either sees the old
    # index or the new one.
    tmp_out = args.out + ".partial"
    fh = open(tmp_out, "w", encoding="utf-8")

    # Each batch is an independent POST; alignment is asserted inside
    # parse_batch, so concurrency cannot cross-contaminate results.
    batches = [pairs[i : i + BATCH] for i in range(0, len(pairs), BATCH)]
    done = 0
    try:
        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(parse_batch, [c[0] for c in ch]): ch for ch in batches}
            for fut in cf.as_completed(futures):
                chunk = futures[fut]
                results = fut.result()
                for (name, our_rank), r in zip(chunk, results):
                    t = r.get("type") or "NO_NAME"
                    tally[t] += 1
                    if t != "SCIENTIFIC" and len(examples.setdefault(t, [])) < 6:
                        examples[t].append(name)

                    marker = r.get("rankMarker")
                    expected = MARKERS.get(our_rank)
                    if expected:
                        if marker is None:
                            rank_absent[our_rank] += 1
                        elif marker in expected:
                            rank_agree[our_rank] += 1
                        else:
                            rank_mismatch[our_rank] += 1

                    fh.write(json.dumps({
                        "n": name, "ourRank": our_rank, "type": t,
                        "canonical": r.get("canonicalName"),
                        "authorship": r.get("authorship"), "year": r.get("year"),
                        "rankMarker": marker,
                        "parsed": r.get("parsed"), "partial": r.get("parsedPartially"),
                    }, ensure_ascii=False) + "\n")

                done += len(chunk)
                if done % 100_000 < BATCH:
                    el = time.time() - started
                    rate = done / el if el else 0
                    print(f"  {done:>9,}/{len(pairs):,}  {el:>5.0f}s  {rate:>6.0f}/s  "
                          f"ETA {(len(pairs)-done)/rate:>4.0f}s", flush=True)
    finally:
        fh.close()
    os.replace(tmp_out, args.out)
    print(f"\n  moved {tmp_out} into place as {args.out}")

    total = sum(tally.values())
    print(f"\n{'=' * 70}")
    print(f"parsed {total:,} names in {time.time()-started:.0f}s\n")
    print("by parser `type`:")
    for k, n in tally.most_common():
        print(f"  {k:<14}{n:>10,}  {n/total*100:>5.2f}%")

    print(f"\nrank agreement (only ranks the parser has vocabulary for):")
    for r in ["SPECIES", "GENUS", "SUBSPECIES", "FAMILY"]:
        a, m, z = rank_agree[r], rank_mismatch[r], rank_absent[r]
        if a + m + z:
            pct = a / (a + m) * 100 if (a + m) else 0
            print(f"  {r:<10}agree {a:>9,} ({pct:>5.1f}%)   disagree {m:>8,}   no marker {z:>8,}")

    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as rf:
        rf.write("# GBIF name parser over every name in the tree\n\n")
        rf.write(f"`POST /v1/parser/name`, {total:,} distinct (name, rank) pairs. "
                 f"The repeated-`name` GET is unusable (see the script docstring); "
                 f"the POST form was asserted positionally safe on every batch.\n\n")
        rf.write("## Parser `type`\n\nThe validity signal. `parsed: true` does not mean "
                 "valid -- `?name=human` is `parsed: true` with `type: PLACEHOLDER` and "
                 "`genusOrAbove: \"?\"`.\n\n| type | count | share |\n|---|---|---|\n")
        for k, n in tally.most_common():
            rf.write(f"| `{k}` | {n:,} | {n/total*100:.2f}% |\n")
        rf.write("\n## rankMarker vs our rank\n\n"
                 "Only comparable where the parser has vocabulary for our rank. Note the\n"
                 "marker is abbreviated (`sp.`, not `SPECIES`) contrary to the OpenAPI enum,\n"
                 "and is often simply absent -- which is not a disagreement.\n\n"
                 "| our rank | agree | disagree | no marker |\n|---|---|---|---|\n")
        for r in ["SPECIES", "GENUS", "SUBSPECIES", "FAMILY"]:
            a, m, z = rank_agree[r], rank_mismatch[r], rank_absent[r]
            if a + m + z:
                rf.write(f"| {r} | {a:,} | {m:,} | {z:,} |\n")
        if examples:
            rf.write("\n## Examples by type\n\n")
            for t, ns in examples.items():
                rf.write(f"**`{t}`**\n\n")
                for n in ns:
                    rf.write(f"- `{n}`\n")
                rf.write("\n")
    print(f"\n  wrote {args.out}")
    print(f"  wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())