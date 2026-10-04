#!/usr/bin/env python3
"""Add colour themes for animalia families that have none.

The COL Stage 2 import brought in ~5,100 animalia families. `colorRegistry.ts`
had exactly one entry per animalia family before that (5,472), so every new
family needs a theme or it renders unstyled.

This does not regenerate the file. `portal/scripts/genColorRegistry.ts` emits
the compact kingdom format used by colorRegistryFungi/Chromista, while
colorRegistry.ts is the richer hand-curated animalia registry -- 485 explicitly
named themes (FELIDAE_THEME and friends) plus ~4,990 auto-generated
`insecta_*` ones carrying orderName, className and lineageColors. Regenerating
would throw all of that away, so this inserts instead:

  - one `const S2_<SLUG>_THEME` per missing family, just above the registry
  - one `  <slug>: S2_<SLUG>_THEME,` line inside the registry object

The `S2_` prefix cannot collide with the 485 existing `<SLUG>_THEME` consts.
Hue is per order via the golden angle, so families of one order sit together
and a family keeps its colour as long as its order does.

Idempotent: rerunning adds nothing.

Usage:
    python3 scripts/addAnimaliaStage2Themes.py            # dry run
    python3 scripts/addAnimaliaStage2Themes.py --apply
"""
import argparse
import json
import re
import sys

TAXONOMY = "portal/data/taxonomy.json"
REGISTRY = "portal/src/colorRegistry.ts"
GOLDEN = 137.508
BASE_HUE = 210          # same family of blues the animalia registry already uses


def collect():
    """(slug, name, class, order) for every animalia family in the taxonomy."""
    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    out = []

    def walk(n, klass, order):
        r = n.get("rank")
        if r == "CLASS":
            klass = n.get("name")
        elif r == "ORDER":
            order = n.get("name")
        elif r == "FAMILY" and n.get("appSlug"):
            out.append((n["appSlug"], n.get("name") or n["appSlug"],
                        klass or "", order or ""))
        for c in n.get("children") or []:
            walk(c, klass, order)

    walk(tax, "", "")
    return out


def end_of_object(text, start):
    """Index just past the `}` that closes the object literal opening at `start`.

    Not `rindex("};")`: this file ends with `export { PORTAL_THEME };`, and the
    last `};` in it belongs to that export statement rather than to the
    registry. Splicing entries in there compiles into a file that parses as
    neither, which is how the first attempt at this wrote 5,129 themes straight
    through the end of the file.
    """
    depth = 0
    i = start
    quote = None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    sys.exit("FATAL: no closing brace for the registry object")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    families = collect()
    src = open(REGISTRY, encoding="utf-8").read()

    marker = "export const COLOR_REGISTRY"
    if marker not in src:
        sys.exit(f"FATAL: {marker} not found in {REGISTRY}")
    head, tail = src.split(marker, 1)

    # Only the registry object counts; the const declarations above it are
    # `const x: ColorTheme`, which the same pattern would also match. Keys are
    # quoted when they are not bare identifiers -- 4,696 of the 5,472 are -- so
    # the quotes have to be optional here.
    have = set(re.findall(r'^\s*"?([^"\s:]+)"?\s*:', tail, re.M))

    missing = [f for f in families if f[0] not in have]
    print(f"  families in taxonomy: {len(families):,}")
    print(f"  already themed:       {len(families) - len(missing):,}")
    print(f"  missing a theme:      {len(missing):,}")

    if not missing:
        print("\n  nothing to do")
        return 0

    orders = sorted({o for _, _, _, o in missing})
    hue_of = {o: (BASE_HUE + i * GOLDEN) % 360 for i, o in enumerate(orders)}
    print(f"  distinct orders among them: {len(orders):,}")

    taken = set(re.findall(r"^const ([A-Za-z0-9_]+)", head, re.M))
    consts, entries, renamed = [], [], 0
    for slug, name, klass, order in sorted(missing):
        hue = hue_of[order]
        tree = (hue + 30) % 360
        cn = re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_") or "UNKNOWN"
        base = f"S2_{cn}_THEME"
        # Two slugs can upper-case to one identifier (`Ocypode?` aside, think
        # `a-b` and `a_b`), and a duplicate `const` is a SyntaxError that takes
        # the whole portal down rather than one theme missing.
        cn_full = base
        n = 2
        while cn_full in taken:
            cn_full = f"{base}_{n}"
            n += 1
        if cn_full != base:
            renamed += 1
        taken.add(cn_full)
        j = lambda s: json.dumps(s, ensure_ascii=False)
        consts.append(
            f'const {cn_full}: ColorTheme = {{ subfamilyColors: {{}}, '
            f'lineageColors: {{ {j(order)}: "hsl({tree:.3f}, 45%, 62%)" }}, '
            f'breedGroupColor: "hsl({hue:.3f}, 30%, 70%)", '
            f'hybridColor: "hsl({hue:.3f}, 40%, 75%)", '
            f'appSlug: {j(slug)}, className: {j(klass)}, orderName: {j(order)}, '
            f'name: {j(name)}, mainColor: "hsl({hue:.3f}, 55%, 52%)" }};'
        )
        entries.append(f"  {j(slug)}: {cn_full},")

    if renamed:
        print(f"  const names disambiguated: {renamed:,}")
    if not args.apply:
        print(f"\n  would add {len(consts):,} themes "
              f"(dry run -- pass --apply to write)")
        return 0

    brace = tail.index("{", tail.index("="))
    close = end_of_object(tail, brace)
    if not tail[:close].rstrip().endswith("}"):
        sys.exit("FATAL: registry object did not end where brace matching says")
    new = (head + "\n".join(consts) + "\n\n" + marker
           + tail[:close - 1].rstrip() + "\n" + "\n".join(entries) + "\n}"
           + tail[close:])
    with open(REGISTRY, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"\n  wrote {REGISTRY}: +{len(consts):,} themes")
    return 0


if __name__ == "__main__":
    sys.exit(main())