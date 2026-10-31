#!/usr/bin/env python3
"""Run maintenance on the tree and keep the pipeline out until it is verified.

A maintenance script holds `maintenanceLock` while it writes, then lets go,
and the pipeline's next pass writes again at once. On 2026-10-31 a dedupe
released the lock, the ordinator's pending-family re-import wrote three new
authority collisions within five minutes, and the verifyTree run meant to
check the dedupe was looking at a tree that had already moved on.

So a session holds the lock across the whole of it:

    START GATE
    1. make species-parquet         a stale parquet makes verifyTree compare
                                    counts it never read (see its
                                    check_parquet_freshness)
    2. verifyTree --json            the baseline. The parquet check must pass
                                    or nothing runs. Other failures are allowed
                                    -- the work may be what fixes them -- but
                                    recorded, and none may get worse.
                                    --require-clean: any failure stops here.
    WORK
    3. each --run command, in order (they may take the lock themselves:
       maintenanceLock lets a holder's children through)
    VERIFY
    4. make species-parquet         again, so the session leaves it current
    5. verifyTree --json            and compare. Nothing got worse -> release,
       the pipeline resumes. Something got worse -> leave
       maintenanceLock.HOLD_PATH and exit 2: the pipeline stays out, even with
       the lock released, until a human has looked and run --release (or
       rolled back).

"Got worse" is per check, and per kingdom where a check reports per kingdom:
a check that passed and now fails, or a failing check whose leading count
went up (3,377 collisions -> 3,380).

    python3 scripts/maintenanceSession.py \\
        --run "python3 scripts/dedupeNamesAgainstCol.py --weak-only --apply"
    python3 scripts/maintenanceSession.py --status
    python3 scripts/maintenanceSession.py --release
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_CHECK = "species.parquet still describes the tree"


def rebuild_parquet():
    print("\n-- make species-parquet --", flush=True)
    return subprocess.run(["make", "species-parquet"], cwd=ROOT).returncode


def verify(label, workdir):
    out = os.path.join(workdir, f"verify-{label}.json")
    print(f"\n-- verifyTree ({label}) --", flush=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verifyTree.py"),
                    "--json", out], cwd=ROOT)
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def _key(check, detail):
    """(check, scope): scope is the leading `kingdom:` some checks report per
    kingdom, so one kingdom improving cannot hide another getting worse."""
    m = re.match(r"([a-z]+):\s", detail or "")
    return (check, m.group(1) if m else "")


def _count(detail):
    """The leading count in a detail ("3,380 collisions, ..."), or None."""
    m = re.search(r"\d[\d,]*", detail.split(":", 1)[-1] if re.match(r"[a-z]+:\s", detail) else detail)
    return int(m.group(0).replace(",", "")) if m else None


def regressions(before, after):
    was = {_key(c, d): d for c, d in before["failures"]}
    out = []
    for c, d in after["failures"]:
        k = _key(c, d)
        if k not in was:
            out.append(f"newly failing: {c}: {d}")
            continue
        b, a = _count(was[k]), _count(d)
        if b is not None and a is not None and a > b:
            out.append(f"worse ({b:,} -> {a:,}): {c}: {d}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", default=[],
                    help="shell command to run inside the session; repeatable")
    ap.add_argument("--release", action="store_true",
                    help="clear a hold after you have checked the tree")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--require-clean", action="store_true",
                    help="start gate: refuse to start unless every invariant "
                         "holds, not just the parquet's")
    args = ap.parse_args()

    if args.status:
        print(maintenanceLock.hold_reason() or "no maintenance hold")
        return 0
    if args.release:
        if maintenanceLock.hold_reason() is None:
            print("no maintenance hold")
        else:
            os.remove(maintenanceLock.HOLD_PATH)
            print("hold released; the pipeline resumes on its next pass")
        return 0
    if not args.run:
        ap.error("nothing to run: pass --run")

    workdir = tempfile.mkdtemp(prefix="maintenance-session-")
    with maintenanceLock.hold_exclusive():
        print(f"holding the maintenance lock (pid {os.getpid()}); "
              f"reports in {workdir}", flush=True)
        if rebuild_parquet() != 0:
            print("\nNOT STARTED: species.parquet did not rebuild; nothing ran")
            return 3
        before = verify("before", workdir)
        stale = [d for c, d in before["failures"] if c == PARQUET_CHECK]
        if stale:
            print(f"\nNOT STARTED: parquet still stale after a rebuild ({stale[0]}); "
                  f"nothing ran")
            return 3
        if args.require_clean and before["failures"]:
            print(f"\nNOT STARTED: --require-clean and {len(before['failures'])} "
                  f"invariants fail already; nothing ran")
            return 3
        if before["failures"]:
            print(f"\n  start gate: {len(before['failures'])} invariants already "
                  f"fail; allowed, but none may get worse")
        failed_cmd = None
        for cmd in args.run:
            print(f"\n-- run: {cmd} --", flush=True)
            rc = subprocess.run(cmd, shell=True, cwd=ROOT).returncode
            if rc != 0:
                failed_cmd = f"{cmd} (exit {rc})"
                print(f"   exited {rc}; verifying before anything else runs")
                break
        if rebuild_parquet() != 0:
            worse_parquet = ["species.parquet did not rebuild after the run"]
        else:
            worse_parquet = []
        after = verify("after", workdir)
        worse = worse_parquet + regressions(before, after)
        if failed_cmd:
            worse.insert(0, f"command failed: {failed_cmd}")
        if worse:
            reason = {
                "at": datetime.datetime.now().isoformat(timespec="seconds"),
                "commands": args.run, "regressions": worse,
                "reports": workdir,
            }
            with open(maintenanceLock.HOLD_PATH, "w", encoding="utf-8") as fh:
                json.dump(reason, fh, indent=1)
            print("\nHELD -- the pipeline stays out until "
                  "`maintenanceSession.py --release`:")
            for w in worse:
                print(f"   {w}")
            return 2
    print(f"\nverified: no invariant got worse ({len(after['failures'])} "
          f"still failing, all pre-existing); lock released")
    return 0


if __name__ == "__main__":
    sys.exit(main())
