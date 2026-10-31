#!/usr/bin/env python3
"""Commit Macie's tree changes on top of origin/main without touching the live
checkout's HEAD, index or working tree.

The live checkout is where the ordinator writes, and its own branch trails
origin (code lands through scratch worktrees and is copied in), so a plain
commit there would be built on a stale base and could not be stashed or
rebased under a running pipeline. This builds the commit in a temporary index
instead, holding maintenanceLock so the snapshot is consistent:

  1. resyncFamilyCounts.py --apply, inside the same lock. Run beforehand in
     its own session, it left a window for the ordinator's next import to
     add species, and the 2026-10-31 landing failed CI on understated counts
     it had just fixed.
  2. a temporary index from origin/main; `git add -A` of what Macie owns:
     taxonomy/{the six portal kingdoms}, their skeleton files in portal/data,
     data/source-queue.
  3. data/import-log.jsonl and data/pipeline-events.jsonl: both machines
     append to them, so origin's lines plus Macie's, never Macie's file.
  4. refuse if the result touches q-bert's paths (bacteria, viruses,
     data/source-queue-bv) or code -- Macie's copies of those are stale and
     committing them would revert q-bert's work.
  5. commit-tree on origin/main; push with --push.

    python3 scripts/landTree.py -F message.txt           # build, print, don't push
    python3 scripts/landTree.py -F message.txt --push
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintenanceLock  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINGDOMS = ["animalia", "plantae", "fungi", "chromista", "protozoa", "archaea"]
SKELETONS = ["portal/data/taxonomy.json", "portal/data/taxonomy-plantae-snippet.json",
             "portal/data/taxonomy-fungi.json", "portal/data/taxonomy-chromista.json",
             "portal/data/taxonomy-protozoa.json", "portal/data/taxonomy-archaea.json"]
LOGS = ["data/import-log.jsonl", "data/pipeline-events.jsonl"]
NOT_OURS = ("taxonomy/bacteria", "taxonomy/viruses", "data/source-queue-bv",
            "portal/data/taxonomy-bacteria", "portal/data/taxonomy-viruses",
            "scripts/", "services/", "portal/src/", "shared/")


def git(*args, env=None, input=None):
    r = subprocess.run(["git", *args], cwd=ROOT, env=env, input=input,
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-F", "--message-file", required=True)
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--no-resync", action="store_true",
                    help="skip the count resync (it runs by default)")
    args = ap.parse_args()
    with open(args.message_file, encoding="utf-8") as fh:
        message = fh.read()

    with maintenanceLock.hold_exclusive():
        if not args.no_resync:
            print("  resyncFamilyCounts.py --apply (inside the lock)", flush=True)
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "resyncFamilyCounts.py"),
                            "--apply"], cwd=ROOT, check=True)
        git("fetch", "-q", "origin")
        base = git("rev-parse", "origin/main").strip()
        fd, idx = tempfile.mkstemp(prefix="land-index-")
        os.close(fd)
        os.unlink(idx)
        env = dict(os.environ, GIT_INDEX_FILE=idx)
        try:
            git("read-tree", base, env=env)
            git("add", "-A", "--", *[f"taxonomy/{k}" for k in KINGDOMS], *SKELETONS,
                "data/source-queue", env=env)
            for log in LOGS:
                theirs = git("show", f"{base}:{log}").splitlines()
                with open(os.path.join(ROOT, log), encoding="utf-8") as fh:
                    ours = fh.read().splitlines()
                seen = set(theirs)
                merged = theirs + [l for l in ours if l not in seen]
                blob = git("hash-object", "-w", "--stdin",
                           input="\n".join(merged) + "\n").strip()
                git("update-index", "--cacheinfo", f"100644,{blob},{log}", env=env)
                print(f"  {log}: origin {len(theirs):,} + "
                      f"{len(merged) - len(theirs):,} Macie-only lines")
            changed = git("diff", "--cached", "--name-only", base, env=env).splitlines()
            if not changed:
                print("  nothing to land")
                return 0
            bad = [p for p in changed if p.startswith(NOT_OURS)]
            if bad:
                raise SystemExit(f"refusing: would touch paths Macie does not own: {bad[:5]}")
            print("  " + git("diff", "--cached", "--shortstat", base, env=env).strip())
            tree = git("write-tree", env=env).strip()
            commit = git("commit-tree", tree, "-p", base, "-F", "-", input=message).strip()
        finally:
            if os.path.exists(idx):
                os.unlink(idx)
    print(f"  commit {commit[:11]} on {base[:11]}")
    if args.push:
        git("push", "-q", "origin", f"{commit}:refs/heads/main")
        print("  pushed")
    else:
        print(f"  not pushed; to push: git push origin {commit}:refs/heads/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
