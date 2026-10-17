#!/usr/bin/env python3
"""Restore `sourcedFrom` on family files where a merge flattened it to "none".

The unioning merge kept one side's copy of each shared species, and on the ten
files it touched that side's `sourcedFrom` was the empty value. 1,654 nodes lost
their provenance while keeping `sourceIds`, so the species is still traceable in
the tree but no longer in the text/name tally that
`docs/data-sources.md` counts.

Takes the HEAD value whenever HEAD recorded one; keeps the working-tree value
where HEAD had nothing or "none", so genuine enrichment from the merge survives.
"""
import json
import subprocess
import sys

EMPTY = {"", "none", None}


def index_by(node, out):
    key = node.get("id") or node.get("name")
    if key:
        out.setdefault(key, node)
    for child in node.get("children") or []:
        index_by(child, out)
    for sp in node.get("speciesList") or []:
        index_by(sp, out)


def walk(node):
    yield node
    for child in node.get("children") or []:
        yield from walk(child)
    for sp in node.get("speciesList") or []:
        yield from walk(sp)


def main():
    files = [f for f in sys.argv[1:] if f.endswith(".json")]
    if not files:
        files = [f for f in subprocess.run(
            ["git", "diff", "--name-only"], capture_output=True, text=True
        ).stdout.split() if f.endswith(".json")]

    for path in files:
        head = subprocess.run(["git", "show", f"HEAD:{path}"],
                              capture_output=True, text=True)
        if head.returncode != 0:
            print(f"  SKIP (no HEAD version): {path}")
            continue
        try:
            old = json.loads(head.stdout)
        except json.JSONDecodeError as e:
            print(f"  SKIP (HEAD JSON): {path}: {e}")
            continue

        with open(path, encoding="utf-8") as fh:
            new = json.load(fh)

        old_nodes = {}
        index_by(old, old_nodes)

        restored = 0
        for node in walk(new):
            key = node.get("id") or node.get("name")
            prior = old_nodes.get(key)
            if not prior:
                continue
            was, now = prior.get("sourcedFrom"), node.get("sourcedFrom")
            if now in EMPTY and was not in EMPTY:
                node["sourcedFrom"] = was
                restored += 1

        if not restored:
            continue
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(new, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"  restored {restored:5d}  {path}")


if __name__ == "__main__":
    main()