#!/usr/bin/env python3
"""Reconcile curated family intros with the family JSONs.

`experiments/book-view/src/familyIntros.ts` is a book-side sidecar that
*overwrites* a family's description at render time. Its own header says a family
the portal has already enriched must not be listed there, "or this sidecar
would overwrite the longer prose" - but 19 entries did exactly that, so those
families showed two different descriptions depending on whether you were in the
graph or the book.

The curated prose is the better writing, so rather than delete it, promote it:
write it into the family JSON (the single source both surfaces read) and drop
the now-redundant override. The 10 families that have no description at all keep
their intro, which is the fallback the file exists for.

Run from the repo root:
    python3 scripts/reconcileFamilyIntros.py [--apply]
"""
import json
import os
import re
import sys
from glob import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTROS = os.path.join(ROOT, "experiments/book-view/src/familyIntros.ts")
ORDER_GLOB = os.path.join(ROOT, "portal/public/data/kingdoms/*/orders*/*.json")
# FAMILY-rank prose lives on the FAMILY node in portal/data/taxonomy*.json
# (keyed by `appSlug`, which buildData stamps onto the node as `familySlug`),
# not in the per-family data JSONs - patching the wrong file is a silent no-op.
TAXONOMY_GLOB = os.path.join(ROOT, "portal/data/taxonomy*.json")


def parse_intros(path):
    """slug -> (text, start_line, end_line) over the uniform 2-line entries."""
    lines = open(path, encoding="utf-8").read().split("\n")
    out = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^  ([a-z0-9-]+):$", lines[i])
        if m and i + 1 < len(lines) and lines[i + 1].lstrip().startswith('"'):
            out[m.group(1)] = (lines[i + 1].strip().rstrip(","), i, i + 1)
            i += 2
            continue
        i += 1
    return out, lines


def families_with_description():
    """familySlug -> (built order file, family node) for slugs that have prose."""
    hits = {}
    for p in glob(ORDER_GLOB):
        tree = json.load(open(p, encoding="utf-8"))

        def walk(n):
            if n.get("rank") == "FAMILY" and n.get("familySlug") and n.get("description"):
                hits.setdefault(n["familySlug"], p)
            for c in n.get("children") or []:
                walk(c)

        walk(tree)
    return hits


def main():
    apply = "--apply" in sys.argv
    intros, lines = parse_intros(INTROS)
    described = families_with_description()

    clash = sorted(s for s in intros if s in described)
    fallback = sorted(s for s in intros if s not in described)
    print(f"familyIntros.ts: {len(intros)} entries "
          f"-> {len(clash)} clash with a JSON description, {len(fallback)} are true fallbacks")
    for s in clash:
        print(f"  clash    {s:20s} json={len(described[s]) and ''}{s}")
    for s in fallback:
        print(f"  fallback {s}")

    if not apply:
        print("\n(dry run - pass --apply)")
        return

    # 1. write the curated prose onto the FAMILY node in taxonomy*.json
    patched_json = 0
    for p in glob(TAXONOMY_GLOB):
        tree = json.load(open(p, encoding="utf-8"))
        dirty = False

        def walk(n):
            nonlocal dirty
            if n.get("rank") == "FAMILY":
                slug = n.get("appSlug")
                if slug in intros and n.get("description") and intros[slug][0] != n["description"]:
                    n["description"] = json.loads(intros[slug][0])
                    dirty = True
                    print(f"  taxonomy  {os.path.basename(p)}: {slug}")
            for c in n.get("children") or []:
                walk(c)

        walk(tree)
        if dirty:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(tree, indent=2, ensure_ascii=False) + "\n")
            patched_json += 1
    if not patched_json:
        sys.exit("no taxonomy file patched - refusing to drop the overrides")

    # 2. drop the redundant overrides, keeping the fallbacks
    drop = set()
    for slug in clash:
        drop.update(range(intros[slug][1], intros[slug][2] + 1))
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    with open(INTROS, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kept))

    print(f"\npatched {patched_json} taxonomy file(s); familyIntros.ts now holds "
          f"{len(fallback)} fallback entries (was {len(intros)})")
    print("rebuild the order files (portal: sh scripts/buildData.sh) and the book "
          "sidecars (portal: sh scripts/ensureBookData.sh --force) to pick this up")


if __name__ == "__main__":
    main()
