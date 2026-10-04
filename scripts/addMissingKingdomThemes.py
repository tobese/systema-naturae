#!/usr/bin/env python3
"""Add colour themes for families a kingdom's generated registry is missing.

`genColorRegistry.ts` assigns each family `BASE_HUE + i * GOLDEN`, where `i` is
its index in tree-walk order. That is deterministic and it is also why the
generator cannot be re-run to add a few families: the 13 families an import
brings in land mid-sequence and shift the index of every family after them, so
1,259 existing plantae families would all change colour to accommodate 13 new
ones.

So this inserts instead of regenerating, which is what
`addAnimaliaStage2Themes.py` does for the animalia registry (where the reason is
stronger still -- 485 hand-named themes no generator could reproduce). Hue
continues the same golden-angle sequence from the next free index, so the new
families sit exactly where the generator would have put them had it run against
the larger tree, and no existing family moves.

Idempotent. Dry run by default.

    python3 scripts/addMissingKingdomThemes.py --kingdom Plantae
    python3 scripts/addMissingKingdomThemes.py --kingdom Plantae --apply
"""
import argparse
import json
import os
import re
import sys

GOLDEN = 137.508
TAXA = "taxonomy"


def kingdom_paths(kingdom):
    """Input taxonomy file and registry file, from kingdom-config.json.

    Not constructed from the kingdom's name: Plantae's input is
    `taxonomy-plantae-snippet.json` and Animalia's is plain `taxonomy.json`, so
    a name-derived path finds neither. The config is the authority for both.
    """
    cfg = json.load(open(os.path.join("portal", "data", "kingdom-config.json"),
                        encoding="utf-8"))
    k = kingdom.lower()
    if k not in cfg["kingdoms"]:
        sys.exit(f"FATAL: kingdom {k!r} is not in kingdom-config.json. "
                 f"Declared: {', '.join(sorted(cfg['kingdoms']))}")
    if k == "animalia":
        sys.exit("FATAL: refusing to touch colorRegistry.ts. Animalia's registry "
                 "is hand-curated -- 485 named themes plus orderName/className "
                 "and lineageColors -- and no generator reproduces it. Use "
                 "scripts/addAnimaliaStage2Themes.py, which inserts.")
    entry = cfg["kingdoms"][k]
    return (os.path.join("portal", entry["input"]),
            os.path.join("portal", entry["colorRegistry"]))


def families(tax_path):
    if not os.path.exists(tax_path):
        sys.exit(f"FATAL: {tax_path} not found")
    tax = json.load(open(tax_path, encoding="utf-8"))
    out = []
    seen = set()

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug") and n["appSlug"] not in seen:
            seen.add(n["appSlug"])
            out.append((n["appSlug"], n.get("name") or n["appSlug"]))
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kingdom", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    tax_path, reg_path = kingdom_paths(args.kingdom)
    if not os.path.exists(reg_path):
        sys.exit(f"FATAL: {reg_path} not found")
    fams = families(tax_path)
    src = open(reg_path, encoding="utf-8").read()

    marker = "export const COLOR_REGISTRY"
    if marker not in src:
        sys.exit(f"FATAL: {marker} not found in {reg_path}")
    head, tail = src.split(marker, 1)

    have = set(re.findall(r'^\s*"([^"]+)"\s*:', tail, re.M))
    missing = [f for f in fams if f[0] not in have]
    print(f"  families in {os.path.basename(tax_path)}: {len(fams):,}")
    print(f"  themes in registry:                   {len(have):,}")
    print(f"  missing:                              {len(missing):,}")

    if not missing:
        print("\n  nothing to do")
        return 0

    # the generator numbers families in the order it walks the tree, so the next
    # free index is the count of themes already in the file.
    i = len(have)
    consts, entries = [], []
    for slug, name in missing:
        hue = (200 + i * GOLDEN) % 360          # genColorRegistry's default BASE_HUE
        tree = (hue + 30) % 360
        safe = re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_") or "UNKNOWN"
        const = ("F_" + safe if safe[0].isdigit() else safe) + "_THEME"
        # json.dumps supplies the quotes; slugs contain hyphens, so the key
        # must be quoted -- but only once.
        j = lambda s: json.dumps(s, ensure_ascii=False)
        consts.append(
            f'const {const}: ColorTheme = {{"accent":"hsl({hue}, 55%, 40%)",'
            f'"bg":"hsl({hue}, 25%, 92%)","bgAlt":"hsl({hue}, 20%, 96%)",'
            f'"border":"hsl({hue}, 30%, 70%)","familyTree":"hsl({tree}, 40%, 50%)",'
            f'"nodeFill":"hsl({hue}, 35%, 70%)",'
            f'"nodeStroke":"hsl({hue}, 50%, 35%)", subfamilyColors: {{}}, '
            f'lineageColors: {{}}, breedGroupColor: "#888", hybridColor: "#888" }};'
        )
        entries.append(f'  {j(slug)}: {const},')
        print(f"    + {slug:28s} {const:34s} hue {hue:7.3f}")
        i += 1

    if not args.apply:
        print(f"\n  would add {len(consts)} themes "
              f"(dry run -- pass --apply to write)")
        return 0

    close = tail.rindex("};")
    new = (head + "\n".join(consts) + "\n\n" + marker
           + tail[:close] + "\n".join(entries) + "\n" + tail[close:])
    with open(reg_path, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"\n  wrote {reg_path}: +{len(consts)} themes, "
          f"no existing family recoloured")
    return 0


if __name__ == "__main__":
    sys.exit(main())