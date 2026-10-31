#!/usr/bin/env python3
"""Turn dedupeNamesAgainstCol.py's plan into a per-family-pair review list,
with every authority we hold voting on each pair.

The dedupe follows COL: a binomial in two families of one kingdom is kept in
the family COL accepts it in. Where COL is current that cleans up a superseded
family (Arctiidae -> Erebidae); where COL lags it would undo current usage
(Ectobiidae -> Blattellidae: the Cockroach Species File files 2,441 species in
Ectobiidae and none in Blattellidae). So the plan is not applied wholesale:
it is grouped by (kingdom, family removed from, family kept in), and each pair
gets three kinds of vote --

  COL      the family it keeps (by construction of the plan)
  ALF      All Living Families 2019 (checklistbank-294066): is each family an
           accepted family? Ruggiero's family-level continuation of COL's own
           2015 management hierarchy, so a check on COL rather than an
           independent authority, and frozen at 2019.
  experts  the group databases we hold (Species Files, Global Lepidoptera
           Index, Systema Dipterorum, WoRMS, WFO, Species Fungorum, ...): where
           they file the pair's species. An expert votes only if it places at
           least 3 of them and at least a tenth.

and a consensus: "follow COL" when experts back COL's family and none back the
other (or, with no expert, ALF knows only COL's family); "conflict" when any
expert backs the family COL would empty (or ALF knows only that one); "both
valid" when ALF accepts both and no expert speaks -- a genus-allocation
question, not a superseded family; "COL only" otherwise.

The `decision` field of each pair is left empty for a human: "follow-col",
"keep" or "skip". Nothing here writes to the tree.

    python3 scripts/familyPairReview.py --plan <plan-full.jsonl>
"""
import argparse
import collections
import csv
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colChecklist as CC  # noqa: E402
import sources  # noqa: E402

ARCH = os.path.join(sources.ROOT, "archives")
ALF = os.path.join(ARCH, "checklistbank-294066", "archive.zip")
# Group databases, by the directory their archive sits in. Missing ones are
# skipped and reported, so the list can name more than is on disk.
# LepIndex (checklistbank-1018) is deliberately absent: a names index frozen
# around 2012, it still holds Arctiidae and the old Noctuidae, and voted
# "conflict" on Noctuidae/Arctiidae -> Erebidae where the current Global
# Lepidoptera Index backs COL.
EXPERTS = {
    "Global Lepidoptera Index": "checklistbank-55434",
    "World Scarabaeidae Database": "checklistbank-1027",
    "WTaxa (weevils)": "checklistbank-1039",
    "Carabcat": "checklistbank-1146",
    "Cerambycidae database": "checklistbank-1032",
    "Orthoptera Species File": "checklistbank-1021",
    "Cockroach Species File": "species-file-cockroach",
    "Lygaeoidea Species File": "species-file-lygaeoidea",
    "Psocodea Species File": "checklistbank-1133",
    "Systema Dipterorum": "checklistbank-1101",
    "World Spider Catalog": "checklistbank-56185",
    "Ants of the World": "checklistbank-54937",
    "MolluscaBase": "checklistbank-1130",
    "WoRMS": "checklistbank-2011",
    "World Flora Online": "wfo-plant-list",
    "WCVP": "checklistbank-2000",
    "Species Fungorum": "checklistbank-2073",
}


def archive_in(dirname):
    d = os.path.join(ARCH, dirname)
    if not os.path.isdir(d):
        return None
    if os.path.exists(os.path.join(d, "archive.zip")):
        return os.path.join(d, "archive.zip")
    for f in sorted(os.listdir(d)):
        if f.endswith((".zip", ".tgz")):
            return os.path.join(d, f)
    return None


def alf_families():
    """Accepted family names in ALF, lowercase."""
    with zipfile.ZipFile(ALF) as z:
        member = next(n for n in z.namelist() if n.endswith("NameUsage.csv"))
        rows = csv.DictReader(io.TextIOWrapper(z.open(member), encoding="utf-8"))
        return {r["scientificName"].strip().lower() for r in rows
                if r["rank"] == "family" and r["status"] == "accepted"}


SPECIES_RANKS = {"species", "sp.", "sp"}  # Species Fungorum writes "sp."


def _binomial(name):
    """Genus + epithet, lowercase, from a name that may carry a subgenus in
    parentheses or its authorship inline ("Crassiungula lawrencei Li, Huang &
    Cai, 2025", as the Scarabaeidae and ant databases give it)."""
    words = [w for w in (name or "").split() if not w.startswith("(")]
    if len(words) >= 2 and words[1][:1].islower():
        return f"{words[0]} {words[1]}".lower()
    return ""


def expert_families(path, wanted):
    """binomial (lowercase) -> family (lowercase), for the names in `wanted`."""
    taxa, _n, _m = CC.load_cached(path)
    by = {t["id"]: t for t in taxa}
    out = {}
    for t in taxa:
        if t.get("is_synonym") or (t.get("rank") or "").lower() not in SPECIES_RANKS:
            continue
        name = _binomial(t.get("name"))
        if name not in wanted:
            continue
        fam = (CC.chain(t, by).get("family") or "").strip().lower()
        if fam:
            out[name] = fam
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True,
                    help="dedupeNamesAgainstCol.py's plan (without --weak-only)")
    ap.add_argument("--out", default="data/family-pair-review.json")
    ap.add_argument("--md", default="docs/family-pair-review.md")
    args = ap.parse_args()

    pairs = collections.defaultdict(lambda: {"copies": 0, "names": set(),
                                             "sources": collections.Counter()})
    for line in open(args.plan, encoding="utf-8"):
        g = json.loads(line)
        for r in g["remove"]:
            p = pairs[(g["kingdom"], r["family"], g["colFamily"])]
            p["copies"] += 1
            p["names"].add(g["name"])
            p["sources"].update(sorted(r.get("sourceIds") or {}) or ["(none)"])
    names = set().union(*(p["names"] for p in pairs.values()))
    print(f"  {len(pairs):,} family pairs, {sum(p['copies'] for p in pairs.values()):,} "
          f"copies, {len(names):,} names")

    alf = alf_families()
    print(f"  ALF: {len(alf):,} accepted families")

    experts, used, missing = {}, [], []
    for label, dirname in EXPERTS.items():
        path = archive_in(dirname)
        if not path:
            missing.append(label)
            continue
        try:
            experts[label] = expert_families(path, names)
            used.append(label)
            print(f"  {label}: places {len(experts[label]):,} of the names", flush=True)
        except Exception as e:  # an unreadable archive is reported, not fatal
            missing.append(f"{label} (unreadable: {type(e).__name__})")
    if missing:
        print("  not used: " + ", ".join(missing))

    review = []
    for (k, frm, to), p in pairs.items():
        votes = {}
        for label, fam_of in experts.items():
            placed = [fam_of[n] for n in p["names"] if n in fam_of]
            # A vote needs a real share of the pair: 3 of 540 placed by an
            # expert for another group is noise, not a view.
            if len(placed) < max(3, len(p["names"]) // 10):
                continue
            c = collections.Counter(placed)
            x, y = c.get(frm, 0), c.get(to, 0)
            vote = ("to" if y > x and y * 2 >= len(placed) else
                    "from" if x > y and x * 2 >= len(placed) else "elsewhere")
            votes[label] = {"vote": vote, "inFrom": x, "inTo": y,
                            "elsewhere": len(placed) - x - y,
                            "mostlyIn": c.most_common(1)[0][0]}
        alf_vote = {"fromAccepted": frm in alf, "toAccepted": to in alf}
        backs_to = [v for v in votes.values() if v["vote"] == "to"]
        backs_from = [v for v in votes.values() if v["vote"] == "from"]
        if backs_from or (not votes and alf_vote["fromAccepted"] and not alf_vote["toAccepted"]):
            consensus = "conflict"
        elif backs_to or (not votes and alf_vote["toAccepted"] and not alf_vote["fromAccepted"]):
            consensus = "follow COL"
        elif not votes and alf_vote["fromAccepted"] and alf_vote["toAccepted"]:
            consensus = "both valid"
        else:
            consensus = "COL only"
        review.append({
            "kingdom": k, "removeFrom": frm, "keepIn": to, "copies": p["copies"],
            "sample": sorted(p["names"])[:5],
            "sources": dict(p["sources"].most_common(4)),
            "votes": {"col": to, "alf": alf_vote, "experts": votes},
            "consensus": consensus, "decision": None,
        })
    review.sort(key=lambda r: -r["copies"])

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"plan": os.path.basename(args.plan), "expertsUsed": used,
                   "expertsMissing": missing, "pairs": review},
                  fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    totals = collections.Counter()
    for r in review:
        totals[r["consensus"]] += r["copies"]
    lines = ["# Family-pair review", "",
             "Generated by `scripts/familyPairReview.py` from a "
             "`dedupeNamesAgainstCol.py` dry run. One row per (family the copy "
             "would be removed from -> family COL keeps it in). Decide in "
             "`data/family-pair-review.json` (`decision`: follow-col / keep / "
             "skip); nothing is applied from this file.", "",
             "| consensus | copies |", "|---|---|"]
    lines += [f"| {c} | {n:,} |" for c, n in totals.most_common()]
    lines += ["", f"Experts used: {', '.join(used)}.  ",
              f"Not used: {', '.join(missing) or 'none'}.", "",
              "| kingdom | remove from | keep in (COL) | copies | ALF | experts | consensus |",
              "|---|---|---|---|---|---|---|"]
    for r in review[:300]:
        a = r["votes"]["alf"]
        alf_s = f"{'Y' if a['fromAccepted'] else '-'}/{'Y' if a['toAccepted'] else '-'}"
        ex = "; ".join(f"{n}: {v['vote']} ({v['inFrom']}/{v['inTo']}/{v['elsewhere']})"
                       for n, v in r["votes"]["experts"].items()) or "-"
        lines.append(f"| {r['kingdom']} | {r['removeFrom']} | {r['keepIn']} | "
                     f"{r['copies']:,} | {alf_s} | {ex} | **{r['consensus']}** |")
    lines += ["", "ALF column: is the remove-from / keep-in family an accepted ALF "
              "family. Expert counts: (filed in remove-from / in keep-in / "
              "elsewhere). First 300 pairs by copies; all are in the JSON."]
    os.makedirs(os.path.dirname(args.md) or ".", exist_ok=True)
    with open(args.md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("\n  copies by consensus: " + ", ".join(f"{c} {n:,}" for c, n in totals.most_common()))
    print(f"  wrote {args.out} and {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
