#!/usr/bin/env python3
"""
Strip media captions that were scraped into species descriptions.

The problem
-----------
Some enrichment run wrote image markup straight into `description`, so the field
holds a caption and sometimes a caption *plus* the real prose:

    thumb|Lycopodiella alopecuroides (L.) Cranfill.
    thumb|233x233px|Entamoeba histolytica in peripheral blood
    thumb|right|450px|Life-cycle of Entamoeba histolytica.
    left|thumb|173x173px|Carrot infected with Meloidogyne chitwoodi
      Meloidogyne chitwoodi is a plant pathogenic root-knot nematode ...

1,708 species across five kingdoms: 1,128 plantae, 538 animalia, 27 fungi,
12 chromista, 3 protozoa. A caption is not a description; a caption followed by
the actual lead is a description with a prefix stuck on the front.

The fix
-------
Wikipedia leads open with the scientific name, which gives an unambiguous cut
point: **take everything from the LAST occurrence of the binomial onward.** For
the Meloidogyne example that lands exactly on "Meloidogyne chitwoodi is a plant
pathogenic..." and drops the caption. Taking the first occurrence would keep the
caption too, because the caption usually also names the species.

Where no prose survives the cut - `thumb|Leaf specimen of M.` - the honest move
is to clear the field rather than leave a caption or invent text. There is no
third option that is not fabrication.

Bias
----
When in doubt this clears rather than recovers. A cleared description can be
re-fetched later; a mangled one is silently wrong and nobody notices. One real
case drove that: the Somali Crow's only binomial mention is inside an
appositive, so the cut produced "Corvus edithae), is approximately the size...".
The prose checks passed it - it does contain "is", and it does start with a
capital - so the guard that catches it counts brackets rather than looking for
words.

Deliberately NOT cleaned
-----------------------
`[[wiki links]]` are left alone. 24 of 57,174 plantae descriptions carry them
already, so they are an existing convention of the corpus rather than part of
this defect, and removing them here would be an unrelated change.

Safety
------
Dry run by default. `--apply` writes. Only touches species whose description
actually contains a media marker, only writes to a field that was non-empty,
and is idempotent - a cleared field has no marker to match, and recovered prose
starts at the binomial so it has no marker either.

    python3 scripts/fix_thumb_captions.py taxonomy
    python3 scripts/fix_thumb_captions.py taxonomy --apply
    python3 scripts/fix_thumb_captions.py taxonomy --limit 20
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

# Three observed marker shapes, and nothing looser:
#   thumb|<caption>            thumb|Cicada with extensive fungus on abdomen.
#   alt=<caption>|             alt=Zamia inermis cone|thumb|...
#   [[Link|thumb]]             [[San Francisco Bay|thumb]] Dunaliella salina ...
# "alt" on its own is a word that appears in ordinary prose, so it only counts
# when written as "alt=".
MARKER = re.compile(r"thumb\||\|thumb\b|\balt=")

# Pixel dimensions and alignment survived the scrape too.
SIZE = re.compile(r"\b\d{2,4}\s*[x×]\s*\d{2,4}\s*px\b", re.I)

# A recovered lead has to read like one. Wikipedia's stub lead is
# "<Name> is a species of ...", so a copula or a growth/occurrence verb is the
# cheapest reliable signal that prose survived rather than a caption.
PROSE = re.compile(
    r"\b(is|are|was|were|grows?|grown|occurs?|found|native|endemic|inhabits?|"
    r"lives?|grows?|distributed|characteri[sz]ed|known|described|belong)\b",
    re.I,
)

MIN_RECOVERED = 80


def binomial(name: str) -> str:
    """First two tokens, lowercased. Authority suffixes and infraspecific ranks
    are all past the binomial, which is the point - we want the name the lead
    opens with."""
    parts = name.replace("(", " ").split()
    return " ".join(parts[:2]).lower() if len(parts) >= 2 else ""


def recover(name: str, text: str) -> str:
    """Prose after the last binomial mention, or "" when only a caption remains."""
    bi = binomial(name)
    if not bi:
        return ""
    low = text.lower()
    idx = low.rfind(bi)
    if idx < 0:
        # A hybrid or a synonym may not share our exact binomial; fall back to
        # the genus, which is still a far better cut point than the start.
        genus = bi.split()[0]
        idx = low.rfind(genus)
        if idx < 0:
            return ""
    # The name must not sit inside parentheses. "The Somali crow, or dwarf raven
    # (Corvus edithae), is approximately the size..." mentions the binomial
    # exactly once and only inside an appositive, so cutting at the LAST
    # occurrence yields "Corvus edithae), is approximately the size..." - a
    # fragment that starts mid-parenthetical. PROSE and the capitalisation check
    # both pass it, because it genuinely contains "is" and genuinely starts with
    # a capital. Counting brackets is what catches it.
    if text.count("(", 0, idx) > text.count(")", 0, idx):
        return ""

    tail = text[idx:].strip()
    tail = re.sub(r"\s+", " ", tail)
    if SIZE.search(tail) or MARKER.search(tail):
        return ""                      # more junk after the cut point
    if len(tail) < MIN_RECOVERED:
        return ""
    if not PROSE.search(tail):
        return ""                      # a caption that happened to name the species
    if not re.match(r"^[A-Z]", tail):
        return ""
    # A description ends in a full stop. A cut that lands mid-sentence usually
    # does not, and if it happens to it is still a fragment.
    if not re.search(r"[.!?]\s*$", tail):
        return ""
    return tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--limit", type=int, default=0, help="stop after N changes (0 = all)")
    ap.add_argument("--report", default="docs/reports/thumb-captions.md")
    args = ap.parse_args()

    def walk(node, path):
        stack = [node]
        while stack:
            n = stack.pop()
            yield path, n
            for c in (n.get("children") or []):
                stack.append(c)
            for s in (n.get("speciesList") or []):
                stack.append(s)

    files = []
    for dirpath, _dirs, names in os.walk(args.root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    files.sort()

    tally = Counter()
    per_kingdom = Counter()
    rows = []
    touched = []

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        kingdom = path.split(os.sep)[1] if os.sep in path else "?"
        changed = 0
        for _p, n in walk(doc, path):
            if n.get("rank") != "SPECIES":
                continue
            text = (n.get("description") or "").strip()
            if not text or not MARKER.search(text):
                continue
            tally["marked"] += 1
            per_kingdom[kingdom] += 1
            recovered = recover(n.get("name") or "", text)
            if recovered and recovered != text:
                kind = "recovered"
                new = recovered
            elif recovered:
                kind = "already-clean"
                new = recovered
            else:
                kind = "cleared"
                new = ""
            tally[kind] += 1
            rows.append({"name": n.get("name"), "kind": kind, "before": text, "after": new,
                         "kingdom": kingdom, "path": path})
            if new != text:
                if args.limit and len(touched) >= args.limit:
                    continue
                n["description"] = new
                if new:
                    n["sourcedFrom"] = n.get("sourcedFrom") or "wikipedia"
                changed += 1
        if changed:
            touched.append(path)
            if args.apply:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    print(f"{'Applied' if args.apply else 'Would change'}: {tally['recovered']} recovered, "
          f"{tally['cleared']} cleared, of {tally['marked']} marked species")
    print(f"  by kingdom: {dict(per_kingdom)}")
    print(f"  family files {len(touched)}")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("# Media captions scraped into species descriptions\n\n")
        fh.write(f"*{tally['marked']} species carry a `thumb|` / `alt=` marker. "
                 f"{tally['recovered']} had real prose after the caption and were recovered; "
                 f"{tally['cleared']} were caption only and were cleared.*\n\n")
        fh.write("Generated by `scripts/fix_thumb_captions.py`.\n\n")
        fh.write("| kingdom | species |\n|---|---|\n")
        for k, v in per_kingdom.most_common():
            fh.write(f"| {k} | {v} |\n")
        for kind in ("recovered", "cleared"):
            sel = [r for r in rows if r["kind"] == kind]
            fh.write(f"\n## {kind} — {len(sel)}\n\n")
            for r in sel[:400]:
                fh.write(f"- **{r['name']}** (`{r['kingdom']}`) — `{r['path']}`\n")
                fh.write(f"  - before: {r['before'][:170]}\n")
                fh.write(f"  - after:  {(r['after'][:170] or '(cleared)')}\n")
    print(f"  report → {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
