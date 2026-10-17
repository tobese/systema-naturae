#!/usr/bin/env python3
"""Resolve merge conflicts by unioning species arrays from both sides."""
import json
import os
import subprocess
import sys

ROOT = "/home/agent/src/systema-naturae"

result = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=U"],
    cwd=ROOT, capture_output=True, text=True,
)
conflicted = [f for f in result.stdout.strip().split("\n") if f]
print(f"{len(conflicted)} conflicted files")

resolved = 0
failed = 0

for fpath in conflicted:
    full = os.path.join(ROOT, fpath)
    ours = subprocess.run(
        ["git", "show", f"HEAD:{fpath}"],
        cwd=ROOT, capture_output=True,
    )
    theirs = subprocess.run(
        ["git", "show", f"origin/main:{fpath}"],
        cwd=ROOT, capture_output=True,
    )
    if ours.returncode != 0 or theirs.returncode != 0:
        print(f"  SKIP: {fpath}")
        failed += 1
        continue

    try:
        d_ours = json.loads(ours.stdout)
        d_theirs = json.loads(theirs.stdout)
    except json.JSONDecodeError as e:
        print(f"  SKIP (JSON): {fpath}: {e}")
        failed += 1
        continue

    children_ours = d_ours.get("children") or []
    children_theirs = d_theirs.get("children") or []

    seen = {}
    for child in children_ours:
        cid = child.get("id")
        if cid:
            seen[cid] = child
    for child in children_theirs:
        cid = child.get("id")
        if cid:
            seen[cid] = child

    merged_children = list(seen.values())

    merged = dict(d_ours)
    merged["children"] = merged_children

    def count_species(node):
        count = 0
        stack = [node]
        while stack:
            n = stack.pop()
            if n.get("rank") == "SPECIES":
                count += 1
            stack.extend(n.get("children") or [])
        return count

    merged["speciesCount"] = count_species(merged)
    merged["genusCount"] = sum(1 for n in merged_children if n.get("rank") == "GENUS")

    with open(full, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    resolved += 1

print(f"Resolved: {resolved}, Failed: {failed}")
