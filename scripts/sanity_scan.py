#!/usr/bin/env python3
"""
Sanity scan over the committed family JSONs.

Why this had to be rewritten
----------------------------
`sanity-issues.json` records a kingdom-wide scan from 2026-06-21 that found
4,057 issues across 66 families. `sanity-queue.json` is now `[]` because they
were all fixed. But commit 71fd8e01f added *only the two JSON files* - no
scanner was ever committed, and nothing in the repo produces the queue. So the
check that guarded those 4,057 issues could not be re-run, and a great deal of
data has changed since: descriptions added and cleared, duplicate genera merged,
fixture nodes removed, genus splits resolved.

The nine legacy checks are reconstructed from the recorded issue vocabulary and
from the `fix_*.py` scripts that resolved them, so the scan and the fixes agree
on what a problem is rather than drifting apart.

The three structural checks are new
-----------------------------------
Every defect found in the 2026-09-30 session would have sailed past the legacy
vocabulary, which is entirely field-completeness:

  DUPLICATE_GENUS   a family lists the same genus twice, so its species are
                    copied with it. 22 redundant genus nodes across 12 families,
                    and 14 of the 20 pairs held DIFFERENT subsets - so a naive
                    dedupe deletes species.
  SPECIES_ID_REPEATED  one species id at more than one position in the tree.
                    Caught the genus-split duplicates and the seven cross-kingdom
                    homonyms.
  SYNTHETIC_NAME     fixture-shaped names that leaked into real data
                    ("Genus1 SpeciesA" in Echinidae, with a *generated*
                    description, which is why it survived).

Usage
-----
    python3 scripts/sanity_scan.py                 # scan, print, do not write
    python3 scripts/sanity_scan.py --write         # also refresh sanity-queue.json
    python3 scripts/sanity_scan.py --write --archive  # and snapshot to sanity-issues.json
    python3 scripts/sanity_scan.py --issues DUPLICATE_GENUS,SYNTHETIC_NAME

Idempotent and read-only unless --write. Never modifies family JSONs; fixing
things is what the `fix_*.py` scripts are for, and a scan that edits its own
input cannot be trusted to report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textLanguage import foreign_language  # noqa: E402

# ── vocabulary, matching the fix scripts that resolved each one ───────────────

CONTINENT_MAP = {
    "EU": "Europe", "AS": "Asia", "NA": "North America", "SA": "South America",
    "AF": "Africa", "AU": "Australia", "OC": "Oceania", "AN": "Antarctica",
    "CENTRAL AMERICA": "North America", "Central America": "North America",
}
VALID_CONTINENTS = {
    "Europe", "Asia", "Africa", "North America",
    "South America", "Australia", "Oceania", "Antarctica",
}
# fix_all_descriptions.py treats under 30 as too short to render.
MIN_DESCRIPTION = 30

# Anchored on both sides on purpose: a looser "genus then digit" pattern would
# eventually match a real name like "Genusia".
SYNTHETIC_ID = re.compile(r"^GENUS\d+SPECIES[A-Z]$|^GENUS_GENUS\d+$")
SYNTHETIC_NAME = re.compile(r"^Genus\s?\d+(\s+Species\s?[A-Z])?$", re.I)

# Id shape. Only these three prefixes are rank prefixes in this tree -- see
# fixMalformedIds.py for why short rank-looking strings cannot be added here.
# `PHY` would match every species in Phyllosticta, Phyllachora, Phycomyces...
# The trailing-underscore case is deliberately NOT flagged: 145,484 ids end in
# one because the name ends in an authority abbreviation (`L.`, `Merr.`), which
# is the faithful slug.
PREFIXED_ID = re.compile(r"^(SP_|GENUS_|FAM)")
MALFORMED_ID = re.compile(r"__|[ \-]")

# A hybrid name the tree files as a plain species. Under the ICN a `Genus x
# epithet` name IS named at species rank, so those are correct and must not be
# flagged -- there are 9,749 of them, mostly ferns and grasses.
#
# The discriminator is whether the element AFTER the marker is a genus or an
# epithet, not whether spaces surround the marker. `Lycopodium × zeilleri` has
# spaced markers and is same-genus; `Anacamptis × Dactylorhiza` is intergeneric
# and capitalised after. A first version of this matched on spacing and
# reported 1,951 hybrids, every one of them a correctly-ranked same-genus name.
HYBRID_MARKER = re.compile(r"[×✕╳]|\bx(?=\s+[A-Z])")
# Capitalised after an INTERNAL marker => a second genus => intergeneric, a real
# rank error. A *leading* marker is a different convention entirely: `× Dryostichum
# mirabile` is a nothogen, one genus, and the marker sits before the genus rather
# than between two. Ignoring leading markers is what keeps those 423 out -- and
# they are already visible as MALFORMED_ID, which is their actual defect.
INTERGENERIC = re.compile(r"(?<!^)[×✕╳]\s*[A-Z]|\bx\s+[A-Z]")

ALL_CHECKS = [
    "UNKNOWN_CONTINENT", "SHORT_DESCRIPTION", "MISSING_SUBSPECIES_COUNT",
    "MISSING_CONTINENTS", "MISSING_COMMON_NAME", "MISSING_LINEAGE",
    "DUPLICATE_SPECIES", "EMPTY_GENUS",
    "DUPLICATE_GENUS", "SPECIES_ID_REPEATED", "SYNTHETIC_NAME",
    "MALFORMED_ID", "HYBRID_RANK", "UNRESOLVED_TAXON", "ACCESSION_NAME",
    "NON_ENGLISH_DESCRIPTION",
]
# The three added later, so --legacy can reproduce the original scope.
LEGACY_ONLY = ALL_CHECKS[:8]


# Names that do not denote a taxon, from GBIF's name parser
# (`portal/data/name-parse-index.jsonl`, built by scripts/parseAllNamesSliced.sh).
#
# A regex was tried first and is not good enough: `spec.` catches 40% of the
# INFORMAL cases and `BOLD:` only 7% of the OTU ones, because the rest carry a
# real-looking binomial plus an authority (`Acorus spec Linnaeus, 1753`) or a
# `cf.` qualifier (`Hippocampus cf. fuscus BOLD:AAC0510`). So this reads the
# parser's verdict rather than re-deriving it.
#
# NOT included: HYBRID, which is a real name type (2,446 nodes) and is handled by
# HYBRID_RANK. Also not VIRUS (5) - `Bolivina prion` and `Neoaemula vector` are
# foraminifera whose epithets merely read like virus words, so flagging the
# parser's type there would be wrong.
UNRESOLVED_TYPES = {"INFORMAL", "OTU", "NO_NAME", "PLACEHOLDER", "BLACKLISTED"}

# NCBI genome-assembly accession standing in for a taxon name.
#
# Archaea are scaffolded from sequence data rather than a nomenclatural source,
# so 1,213 of its nodes are named `UBA10200`, `JAGWAF01`, `ARS49`, `M3-22` - the
# assembly, not the organism. That is 9% of archaeal species, 11% of genera and
# 15% of families, and it is a scope statement about the kingdom rather than a
# defect: there is no taxonomic name for these to carry. Counting them as
# UNRESOLVED_TAXON alongside `Lactarius spec` conflated an editorial gap with a
# design decision, so they get their own informational check.
ASSEMBLY_ACCESSION = re.compile(
    r"^(?:"
    r"UBA\d+"                          # UBA10200
    r"|JAG[A-Z0-9]+"                   # JAGWAF01
    r"|(?:GCA|GCF)_\d+"                # GCA_000001405
    r"|ARS\d+"                         # ARS49
    r"|SAMN\d+"
    r"|NZ_[A-Z]{2}\d+"
    r"|[A-Z0-9]+(?:-[A-Za-z0-9]+)+"    # M3-22, SW-4-43-9, B1-Br10-U2g21, CG07-land
    r"|(?:BM|KM|CP|JA[A-Z]{2}|PWVO|PWWA|JACQMU|JAAOYF|SKIS)\d*"  # BM511, JAAB01, PWVO01
    r")(?: sp\d+)?$"                   # "PWWA01 sp007131205"
)
# Narrow on purpose. An earlier version ended with `[A-Za-z][A-Za-z0-9]{1,9}`,
# which matches every binomial in the tree and reported 45,939 "accessions" --
# more than three times the number of unresolved names it was supposed to
# separate out. A pattern this permissive is worse than no check, because a
# number that cannot be wrong is a number nobody checks.
#
# Deliberately NOT matched, each an earlier false positive: `Nanosalinarum spec.`
# and `Lactarius spec` are placeholders, `Salmo sp. BOLD:AAD0897` is a barcode
# BIN. All three are UNRESOLVED_TAXON instead.
PARSE_INDEX = os.path.join("portal", "data", "name-parse-index.jsonl")


def load_parse_verdicts(path: str) -> dict:
    """(name, rank) -> parser type, from the merged parser index."""
    if not os.path.exists(path):
        sys.exit(
            f"FATAL: UNRESOLVED_TAXON needs the parser index at {path}, which is absent.\n"
            f"       Build it with:  sh scripts/parseAllNamesSliced.sh\n"
            f"       Or drop the check:  --issues <everything else>\n"
            f"       A regex alternative exists but catches only ~40% of the cases."
        )
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("{"):
                continue
            d = json.loads(line)
            if d.get("type") in UNRESOLVED_TYPES:
                out[(d["n"], d["ourRank"])] = d["type"]
    return out


def family_files(root: str) -> list[str]:
    out = []
    for dirpath, _d, names in os.walk(root):
        if os.path.join("src", "data") not in dirpath.replace(os.sep, "/"):
            continue
        out += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    out.sort()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="taxonomy")
    ap.add_argument("--write", action="store_true", help="refresh sanity-queue.json")
    ap.add_argument("--archive", action="store_true", help="also snapshot sanity-issues.json")
    ap.add_argument("--legacy", action="store_true", help="only the original nine checks")
    ap.add_argument("--issues", default="", help="comma-separated subset of checks")
    ap.add_argument("--queue", default="portal/data/sanity-queue.json")
    ap.add_argument("--archive-path", default="portal/data/sanity-issues.json")
    ap.add_argument("--no-parse-index", action="store_true",
                    help="do not read portal/data/name-parse-index.jsonl. The "
                         "index is 2,989 files stale after the WFO and ITIS "
                         "imports, so any check reading it is scoring against "
                         "a snapshot of an older tree.")
    ap.add_argument("--parse-index", default=PARSE_INDEX,
                    help="GBIF parser index, required by UNRESOLVED_TAXON")
    args = ap.parse_args()

    checks = set(LEGACY_ONLY if args.legacy else ALL_CHECKS)
    if args.issues:
        wanted = {c.strip() for c in args.issues.split(",") if c.strip()}
        unknown = wanted - set(ALL_CHECKS)
        if unknown:
            print(f"  unknown check(s): {sorted(unknown)}", file=sys.stderr)
            return 2
        checks = wanted

    # Only loaded when the check is on, so every other subset stays runnable
    # without the 259 MB index.
    skipped = {}
    needs_index = "UNRESOLVED_TAXON" in checks and not args.no_parse_index
    if needs_index:
        verdicts = load_parse_verdicts(args.parse_index)
    else:
        verdicts = {}
        if "UNRESOLVED_TAXON" in checks:
            skipped["UNRESOLVED_TAXON"] = ("parse index is a stale snapshot; "
                                           "rebuild it or accept the gap")
            print("  UNRESOLVED_TAXON skipped (--no-parse-index): the index is a "
                  "stale snapshot, so its verdicts describe an older tree. The "
                  "check is the one thing the index is still needed for.")
    if verdicts:
        print(f"  parser index: {len(verdicts):,} unresolved names")

    files = family_files(args.root)
    print(f"Scanning {len(files):,} family files · {len(checks)} checks")
    if args.legacy:
        print("  (--legacy: reproducing the original nine checks only)")

    issues: list[dict] = []
    seen_ids: dict[str, list] = defaultdict(list)
    started = time.time()

    for i, path in enumerate(files, 1):
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError) as exc:
            issues.append({"family": path, "issue": "UNPARSEABLE", "detail": str(exc)[:120]})
            continue
        family = doc.get("name") or os.path.basename(path)

        # per-family duplicate genus names
        if "DUPLICATE_GENUS" in checks:
            counts = Counter(c.get("name") for c in (doc.get("children") or []) if c.get("name"))
            for name, n in counts.items():
                if n > 1:
                    issues.append({"family": family, "issue": "DUPLICATE_GENUS",
                                   "detail": f"{name} listed {n} times"})

        def walk(node, genus_seen: dict):
            rank = node.get("rank")
            name = node.get("name") or ""
            sid = node.get("id")

            if rank == "GENUS":
                genus_seen.setdefault("all", []).append(name)

            if "ACCESSION_NAME" in checks and name and ASSEMBLY_ACCESSION.match(name):
                issues.append({"family": family, "issue": "ACCESSION_NAME",
                               "detail": f"{name} filed as {rank} - genome assembly, not a taxon name"})

            if "UNRESOLVED_TAXON" in checks and name:
                t = verdicts.get((name, rank))
                if t:
                    issues.append({"family": family, "issue": "UNRESOLVED_TAXON",
                                   "detail": f"{name} [{t}] filed as {rank}"})

            if "MALFORMED_ID" in checks and sid and PREFIXED_ID.match(sid) and MALFORMED_ID.search(sid):
                issues.append({"family": family, "issue": "MALFORMED_ID", "detail": f"{name}: {sid}"})

            if "HYBRID_RANK" in checks and name and HYBRID_MARKER.search(name):
                if INTERGENERIC.search(name):
                    issues.append({"family": family, "issue": "HYBRID_RANK",
                                   "detail": f"{name} filed as {rank}"})

            if rank == "SPECIES":
                if "SPECIES_ID_REPEATED" in checks and sid:
                    seen_ids[sid].append((family, name, " > ".join(genus_seen.get("all", [])[-1:])))
                if "UNKNOWN_CONTINENT" in checks:
                    for c in (node.get("continents") or []):
                        if c in CONTINENT_MAP or (isinstance(c, str) and c not in VALID_CONTINENTS):
                            issues.append({"family": family, "issue": "UNKNOWN_CONTINENT",
                                           "detail": f"{name}: '{c}'"})
                desc = (node.get("description") or "").strip()
                if "SHORT_DESCRIPTION" in checks and desc and len(desc) < MIN_DESCRIPTION:
                    issues.append({"family": family, "issue": "SHORT_DESCRIPTION", "detail": name})
                if "NON_ENGLISH_DESCRIPTION" in checks and desc:
                    code = foreign_language(desc)
                    if code:
                        issues.append({"family": family, "issue": "NON_ENGLISH_DESCRIPTION",
                                       "detail": f"{name} ({code}, {len(desc)} chars)"})
                if "MISSING_SUBSPECIES_COUNT" in checks and "subspeciesCount" not in node:
                    issues.append({"family": family, "issue": "MISSING_SUBSPECIES_COUNT", "detail": name})
                if "MISSING_CONTINENTS" in checks and not node.get("continents"):
                    issues.append({"family": family, "issue": "MISSING_CONTINENTS", "detail": name})
                if "MISSING_COMMON_NAME" in checks and not node.get("commonName"):
                    issues.append({"family": family, "issue": "MISSING_COMMON_NAME", "detail": name})
                if "MISSING_LINEAGE" in checks and not node.get("lineage"):
                    issues.append({"family": family, "issue": "MISSING_LINEAGE", "detail": name})
                if "SYNTHETIC_NAME" in checks and (SYNTHETIC_ID.match(sid or "") or
                                                    SYNTHETIC_NAME.match(name.strip())):
                    issues.append({"family": family, "issue": "SYNTHETIC_NAME",
                                   "detail": f"{name} (id={sid})"})

            elif rank in ("FAMILY", "ORDER", "CLASS", "PHYLUM") and "EMPTY_GENUS" in checks:
                pass

            for c in (node.get("children") or []):
                walk(c, genus_seen)
            for s in (node.get("speciesList") or []):
                walk(s, genus_seen)

        # EMPTY_GENUS + DUPLICATE_SPECIES need the family subtree in hand
        def subtree(node):
            st = [node]
            while st:
                x = st.pop()
                yield x
                st.extend(x.get("children") or [])
                st.extend(x.get("speciesList") or [])

        if "EMPTY_GENUS" in checks:
            for n in subtree(doc):
                if n.get("rank") == "GENUS":
                    kids = (n.get("children") or []) + (n.get("speciesList") or [])
                    if not kids:
                        issues.append({"family": family, "issue": "EMPTY_GENUS",
                                       "detail": n.get("name") or ""})
        if "DUPLICATE_SPECIES" in checks:
            for genus in (doc.get("children") or []):
                names = [s.get("name") for s in ((genus.get("children") or []) + (genus.get("speciesList") or []))
                         if s.get("rank") == "SPECIES"]
                for n, c in Counter(names).items():
                    if n and c > 1:
                        issues.append({"family": family, "issue": "DUPLICATE_SPECIES", "detail": n})

        walk(doc, {"all": []})

        if i % 500 == 0:
            el = time.time() - started
            rate = i / el if el else 0
            eta = (len(files) - i) / rate if rate else 0
            print(f"  {i}/{len(files)} files  {len(issues):,} issues  "
                  f"{el/60:.1f}m elapsed  ETA {eta/60:.1f}m")

    if "SPECIES_ID_REPEATED" in checks:
        for sid, where in seen_ids.items():
            if len(where) > 1:
                fams = sorted({w[0] for w in where})
                issues.append({"family": fams[0] if len(fams) == 1 else " + ".join(fams[:2]),
                               "issue": "SPECIES_ID_REPEATED",
                               "detail": f"{sid} at {len(where)} positions ({where[0][1]})"})

    issues.sort(key=lambda x: (x["issue"], str(x["family"]), str(x["detail"])))
    tally = Counter(x["issue"] for x in issues)
    families = len({x["family"] for x in issues})

    print(f"\n{len(issues):,} issues across {families:,} families  "
          f"({(time.time()-started)/60:.1f}m)\n")
    for k, n in tally.most_common():
        print(f"  {k:<26}{n:>8,}")
    # A check that was not run must never print as clean. UNRESOLVED_TAXON was
    # skipped here because the parse index is a stale snapshot, and the summary
    # reported it as "0 clean" -- the exact failure mode this project keeps
    # hitting, where a number that means "not measured" reads as "measured and
    # fine". It is now reported as SKIPPED, with the reason.
    for k in ALL_CHECKS:
        if k not in checks:
            continue
        if tally.get(k):
            continue
        if k in skipped:
            print(f"  {k:<26}{'-':>8}  SKIPPED ({skipped[k]})")
        else:
            print(f"  {k:<26}{'0':>8}  clean")

    if args.write:
        with open(args.queue, "w", encoding="utf-8") as fh:
            json.dump(issues, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"\n  wrote {args.queue}")
    if args.archive:
        with open(args.archive_path, "w", encoding="utf-8") as fh:
            json.dump(issues, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"  wrote {args.archive_path}")
    if not args.write:
        print("\n  (dry run - pass --write to refresh the queue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
