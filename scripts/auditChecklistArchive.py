"""Audit a ChecklistBank archive before importing it, on the question that
actually decides the verdict: does its taxonomy agree with ours where we already
agree with each other?

Overlap says nothing on its own. A source can offer 71,009 names we lack and
still be wrong for us, because "we lack it" and "we would place it where the
source places it" are different questions. The measurable one is the names both
of us hold: if BOLD puts *X* in Noctuidae and we put it in Erebidae, then its
71,009 new names arrive with a placement rule that disagrees with ours on the
names we can check, and the import scatters placement rather than extending it.

So this reports three things, in the order they should change a decision:

  1. **Family agreement on shared names.** The headline number. Reported as a
     confusion table, not a percentage alone, because a single systematic swap
     (Erebidae/Noctuidae, which really did happen) moves the percentage without
     telling you it is one swap.
  2. **Name form.** How many offered names are binomials, how many are
     subspecies, how many are hybrids or infraspecific, and how many are
     placeholder-shaped.
  3. **Authorship.** Whether the source carries it, because an import that
     writes names without authorship cannot be re-identified against a later
     edition of the same source.

    TAXASERVE=http://localhost:9882 python3 scripts/auditChecklistArchive.py <archive.zip>
"""
import collections
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colChecklist as K          # noqa: E402
import taxamatch as T             # noqa: E402

TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")
AUTH_TAIL = re.compile(r"\s+[A-Z][\w.'\-]*(?:\s*(?:,|&|and|in|ex|et)\s*[\w.'\-]*)*"
                       r"(?:\s*\d{4}[a-z]?)?\s*$")


def strip_authorship(n):
    n = re.sub(r"\s*\([^)]*\)\s*", " ", n).strip()
    parts = n.split()
    if len(parts) > 2 and AUTH_TAIL.search(" " + " ".join(parts[2:])):
        n = " ".join(parts[:2])
    return n


def ask(names, batch=4000):
    """-> {lower name: [records]} from the name index."""
    out = {}
    for i in range(0, len(names), batch):
        ch = names[i:i + batch]
        req = urllib.request.Request(
            TAXASERVE + "/held", data=json.dumps({"names": ch}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            res = json.load(r)
        for k, v in (res.get("held") or {}).items():
            out.setdefault(k.lower(), []).extend(v)
    return out


def family_of(records):
    for r in records:
        f = r.get("family")
        if f:
            return f.strip()
    return ""


def main():
    if not TAXASERVE:
        sys.exit("set TAXASERVE=http://localhost:9882")
    if len(ask(["Felis catus", "Panthera leo"])) != 2:
        sys.exit("taxaserve is not answering -- another job is probably "
                 "loading it; retry when idle")
    path = sys.argv[1]
    taxa, _, meta = K.load(path)
    print(f"== {os.path.basename(path)}: {meta.get('title')}")

    by_id = {t["id"]: t for t in taxa}
    species = [t for t in taxa if (t.get("rank") or "").lower() == "species"]
    subsp = [t for t in taxa if (t.get("rank") or "").lower() == "subspecies"]
    names = sorted({strip_authorship(t["name"]) for t in taxa
                    if t.get("name") and t.get("rank") in ("species", "subspecies")
                    and " " in t["name"]})
    bare = {n: (T.bare_name(n, {}) or n) for n in names}

    # ---- name form -------------------------------------------------------
    parsed = T.parse_names(names)
    shapes = collections.Counter()
    for n in names:
        g, s = T.bare_binomial(n, parsed)
        if not g or not s:
            shapes["not binominal"] += 1
        elif "\u00d7" in n or re.search(r"\bx\b", n):
            shapes["hybrid"] += 1
        elif s[:1].isdigit():
            shapes["numeric epithet"] += 1
        elif len(n.split()) > 2:
            shapes["trinomial or longer"] += 1
        else:
            shapes["plain binomial"] += 1
    print(f"\n  2. name form, {len(names):,} distinct names offered")
    for k, v in shapes.most_common():
        print(f"       {v:>8,}  {k}")
    with_auth = sum(1 for t in taxa if t.get("authorship"))
    print(f"       {with_auth:,} of {len(taxa):,} taxa carry authorship "
          f"({100 * with_auth / max(1, len(taxa)):.1f}%)")
    print(f"       species {len(species):,}  subspecies {len(subsp):,}")

    # ---- family agreement on shared names --------------------------------
    #
    # The family is derived by walking parents, not read off a column. BOLD's
    # ColDP goes through colChecklist._coldp(), which builds rows without the
    # denormalised chain columns, so reading `taxon["family"]` gives None for
    # every taxon and the whole check reports 0 agreements and 0 disagreements
    # -- which looks like a clean bill of health rather than a broken reader.
    def family_via_parents(tid):
        seen = 0
        while tid and seen < 60:
            t = by_id.get(tid)
            if t is None:
                return ""
            if (t.get("rank") or "").lower() == "family":
                return (t.get("name") or "").strip()
            tid = t.get("parent")
            seen += 1
        return ""

    fam_of_src = {}
    for t in taxa:
        n = strip_authorship(t.get("name") or "")
        if " " in n:
            fam_of_src.setdefault(T.bare_name(n, {}) or n,
                                  family_via_parents(t["id"]))

    recs = ask([bare[n] for n in names])
    shared = [n for n in names if bare[n].lower() in recs]
    agree = disagree = unknown = 0
    swaps = collections.Counter()
    for n in shared:
        ours = family_of(recs[bare[n].lower()])
        theirs = fam_of_src.get(bare[n], "")
        if not ours or not theirs:
            unknown += 1
        elif ours.lower() == theirs.lower():
            agree += 1
        else:
            disagree += 1
            swaps[(ours, theirs)] += 1
    print(f"\n  1. family agreement on the {len(shared):,} names both sources hold")
    if shared:
        print(f"       agree    {agree:>8,}  ({100 * agree / len(shared):.1f}%)")
        print(f"       disagree {disagree:>8,}  ({100 * disagree / len(shared):.1f}%)")
        print(f"       no family on one side {unknown:,}")
    print("       largest disagreements (ours -> source):")
    for (ours, theirs), n in swaps.most_common(12):
        print(f"         {n:>7,}  {ours} -> {theirs}")

    # ---- what the import would actually add ------------------------------
    miss = [n for n in names if bare[n].lower() not in recs]
    miss_fams = collections.Counter(fam_of_src.get(bare[n], "") for n in miss)
    print(f"\n  3. the opening: {len(miss):,} names not held")
    print("       families carrying the most of it:")
    for f, n in miss_fams.most_common(10):
        print(f"         {n:>7,}  {f or '(unknown)'}")
    print("\n  Read the disagreement row before the opening row: 71,000 new names")
    print("  are only an extension of the tree if the source places the names we")
    print("  already share where we place them.")


if __name__ == "__main__":
    main()