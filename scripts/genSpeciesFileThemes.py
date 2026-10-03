#!/usr/bin/env python3
"""Generate ColorTheme entries for newly imported Species File families.

There are 133 new families across the eight checklists, and hand-picking 133 hex
triples is how you end up with a family that is indistinguishable from its
neighbour and no way to tell afterwards which were deliberate. So this derives
them instead: a golden-angle hue sweep within each order, from a fixed starting
hue per order, at muted saturation in the style of the existing registry.

Deterministic by construction -- the same taxonomy always produces the same
colours -- so re-running after a re-import is a no-op rather than a reshuffle.
Only families absent from the registry are added, so existing hand-curated themes
are never overwritten.

Usage:
    python3 scripts/genSpeciesFileThemes.py --dry-run
    python3 scripts/genSpeciesFileThemes.py --apply
"""
import argparse
import colorsys
import json
import re
import sys

REGISTRY = "portal/src/colorRegistry.ts"
TAXONOMY = "portal/data/taxonomy.json"
GOLDEN = 137.508  # degrees; maximally spread successive hues

# Starting hue per order, so the eight new orders read as distinct blocks rather
# than one long rainbow. Chosen to sit apart from Orthoptera's purple-heavy run
# and from the older families' blues and greens.
ORDER_HUE = {
    "Plecoptera": 205,    # stone blues
    "Phasmida": 95,       # leaf greens
    "Mantodea": 340,      # pink-magenta
    "Dermaptera": 25,     # rust
    "Grylloblattodea": 265,
    "Zoraptera": 175,
    "Coleorrhyncha": 55,
    "Hemiptera": 145,      # aphid greens
    "Hymenoptera": 315,
}

# The existing themes use one fixed channel near 0x51 with the other two carrying
# the hue, and derive lineage/hybrid as lightened tints of the same hue. Same
# structure here so the new families sit alongside the old ones.
MAIN_L, LINEAGE_L, HYBRID_L, GROUP_L = 0.40, 0.72, 0.56, 0.31
MAIN_S, LINEAGE_S, HYBRID_S, GROUP_S = 0.40, 0.28, 0.26, 0.44


def hexify(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l, s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def theme_for(name: str, slug: str, order: str, class_name: str, index: int):
    hue = ORDER_HUE.get(order, 210) + index * GOLDEN
    main = hexify(hue, MAIN_S, MAIN_L)
    return {
        "const": f"insecta_{slug}",
        "line": ('const insecta_%s: ColorTheme = { subfamilyColors: {}, '
                 'lineageColors: { "%s": "%s" }, breedGroupColor: "%s", '
                 'hybridColor: "%s", appSlug: "%s", className: "%s", '
                 'orderName: "%s", name: "%s", mainColor: "%s" };'
                 % (slug, name, hexify(hue, LINEAGE_S, LINEAGE_L),
                    hexify(hue, GROUP_S, GROUP_L),
                    hexify(hue, HYBRID_S, HYBRID_L),
                    slug, class_name, order, name, main)),
        "entry": f'"{slug}": insecta_{slug}',
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--taxonomy", default=TAXONOMY)
    args = ap.parse_args()

    reg = open(args.registry, encoding="utf-8").read()
    # Two independent signals, because neither alone is complete. Some theme
    # consts predate the appSlug field, so appSlug alone misses apidae, formicidae
    # and vespidae; and registry keys are a mix of quoted ("x": T) and unquoted
    # (x: T), so a quoted-only regex misses most of the file. Generating a theme
    # that already exists redeclares the const and duplicates the registry key,
    # which typecheck catches -- but only after a 11k-line rewrite.
    already = set(re.findall(r'appSlug: "([a-z0-9]+)"', reg))
    m = re.search(r"export const COLOR_REGISTRY[^=]*= \{", reg)
    body = reg[m.end():reg.index("};", m.end())] if m else ""
    already |= set(re.findall(r'"([a-z0-9]+)"\s*:', body))
    already |= set(re.findall(r'(?:^|[,{\s])([a-z][a-z0-9]+)\s*:\s*[A-Za-z_]', body))

    tax = json.load(open(args.taxonomy, encoding="utf-8"))
    wanted = []
    insecta = None
    for phylum in tax.get("children") or []:
        for klass in phylum.get("children") or []:
            if klass.get("name") == "Insecta":
                insecta = klass
    if insecta is None:
        sys.exit("FATAL: Insecta not found")
    for order in insecta.get("children") or []:
        if order.get("name") not in ORDER_HUE:
            continue
        # Largest family first, so the visually prominent families in each order
        # are adjacent in the sweep and differ from one another.
        fams = sorted((f for f in order.get("children") or []
                       if f.get("rank") == "FAMILY"),
                      key=lambda f: -f.get("speciesCount", 0))
        for i, f in enumerate(fams):
            wanted.append((f["name"], f["appSlug"], order["name"], "Insecta", i))

    new = [w for w in wanted if w[1] not in already]
    print(f"families in the new orders: {len(wanted)}")
    print(f"already themed:             {len(wanted) - len(new)}")
    print(f"to generate:                {len(new)}")

    themes = [theme_for(*w) for w in new]
    mains = [re.search(r'mainColor: "(#[0-9A-F]{6})"', t["line"]).group(1) for t in themes]
    print(f"distinct main colours:      {len(set(mains))}")
    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    marker = "export const COLOR_REGISTRY: Record<string, ColorTheme> = {"
    if marker not in reg:
        sys.exit("FATAL: COLOR_REGISTRY declaration not found")
    block = "\n".join("  " + t["line"] for t in themes)
    reg = reg.replace(marker, block + "\n\n" + marker, 1)

    # Append entries just inside the registry object. It closes as "...,};" on
    # one line rather than a bare "};", so find the brace rather than assuming a
    # newline. Entries are emitted unquoted to match the surrounding block, which
    # mixes unquoted and quoted keys.
    start = reg.index(marker)
    close = reg.index("};", start)
    entries = ",\n  ".join(t["const"].replace("const insecta_", "") for t in [])
    body = "".join(f"\n  {t['entry']}," for t in themes)
    reg = reg[:close] + body + reg[close:]
    open(args.registry, "w", encoding="utf-8").write(reg)
    print(f"\nwrote {len(themes)} themes to {args.registry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
