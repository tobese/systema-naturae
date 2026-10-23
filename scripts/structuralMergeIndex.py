#!/usr/bin/env python3
"""Structural JSON merge for the Macie/q-bert two-machine sync, operating
purely on git's object store + a GIT_INDEX_FILE -- no working tree needed
(the external volume holding worktrees proved unreliable this session).

Git's line-based merge loses legitimate additions when both sides edit the
same large taxonomy JSON file differently (one side adds species via import,
the other edits counts/removes duplicates via dedupe). This unions children
by `id` recursively instead, so both sides' additions survive.
"""
from __future__ import annotations
import json
import subprocess
import sys

REPO = "/Users/tb/Dev/systema-naturae"


def git_show(rev: str, path: str):
    r = subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, text=True
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def hash_object(content: str) -> str:
    r = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=REPO,
        input=content,
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def update_index(index_file: str, sha: str, path: str) -> None:
    subprocess.run(
        ["git", "update-index", "--add", "--cacheinfo", f"100644,{sha},{path}"],
        cwd=REPO,
        env={"GIT_INDEX_FILE": index_file, "PATH": "/usr/bin:/bin:/usr/local/bin"},
        check=True,
    )


def merge_node(base, ours, theirs):
    """base/ours/theirs are dicts for the *same id* node, or None if absent."""
    if ours is None:
        return theirs
    if theirs is None:
        return ours

    base_children = {c["id"]: c for c in (base or {}).get("children", []) if "id" in c}
    ours_children = {c["id"]: c for c in ours.get("children", []) if "id" in c}
    theirs_children = {c["id"]: c for c in theirs.get("children", []) if "id" in c}

    all_ids = []
    seen = set()
    for src in (ours.get("children", []), theirs.get("children", [])):
        for c in src:
            cid = c.get("id")
            if cid and cid not in seen:
                seen.add(cid)
                all_ids.append(cid)

    merged_children = []
    for cid in all_ids:
        b = base_children.get(cid)
        o = ours_children.get(cid)
        t = theirs_children.get(cid)
        if o is not None and t is not None:
            merged_children.append(merge_node(b, o, t))
        elif o is not None:
            merged_children.append(o)
        else:
            merged_children.append(t)

    # scalar fields: prefer theirs (origin/main carries the resync/dedupe-corrected
    # counts and allowlist-driven fixes); speciesCount gets re-synced post-merge anyway.
    merged = dict(theirs)
    if merged_children or ours.get("children") or theirs.get("children"):
        merged["children"] = merged_children
    return merged


def merge_file(path: str, base_rev: str, ours_rev: str, theirs_rev: str):
    base = git_show(base_rev, path)
    ours = git_show(ours_rev, path)
    theirs = git_show(theirs_rev, path)

    if ours is None and theirs is None:
        return None
    if ours is None:
        result = theirs
    elif theirs is None:
        result = ours
    else:
        result = merge_node(base, ours, theirs)

    return json.dumps(result, indent=2, ensure_ascii=False) + "\n"


def main():
    base_rev, ours_rev, theirs_rev, list_file, index_file = sys.argv[1:6]
    with open(list_file) as f:
        paths = [l.strip() for l in f if l.strip()]
    failures = []
    for i, path in enumerate(paths):
        try:
            content = merge_file(path, base_rev, ours_rev, theirs_rev)
            if content is None:
                failures.append((path, "both sides deleted or missing"))
                continue
            sha = hash_object(content)
            update_index(index_file, sha, path)
        except Exception as e:
            failures.append((path, str(e)))
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(paths)} merged", flush=True)
    print(f"done: {len(paths) - len(failures)}/{len(paths)} merged")
    for path, reason in failures:
        print(f"  FAILED {path}: {reason}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
