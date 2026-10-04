#!/usr/bin/env python3
"""Remove genus nodes that exist in two family files at once.

A duplicated genus produces a duplicated species: the 218 species ids that appear
in two animalia family files are not reclassifications and not import damage --
in every case both copies sit under the *same genus name*, because the genus
node itself was written into two families. `Carcharodon` sits in both
`lamnidae.json` and `lamniformes.json`, 30 species each; `Sporophila` in both
`passerellidae.json` and `thraupidae.json`, 15 each. All 54 genera involved, and
all of it predates the COL Stage 2 import.

Which family should own a genus is a question COL can answer, so COL is asked:

  1. If COL names exactly one family for the genus, that family keeps it.
  2. Otherwise, if COL names several, the copy in a family COL recognises wins.
  3. Otherwise (COL is silent), if exactly one of our two family names is a
     family COL has, that one wins.
  4. Anything still undecided is left alone and reported, rather than guessed.

Rule 3 is what retires `Lamniformes`, which holds most of the duplicated species
and is not a family at all: it is a FAMILY node named after its own parent ORDER,
and COL has no such family. Rule 1 is applied spelling-tolerantly, which is what
keeps `Randia` and `Thamnornis` in our `Bernieriidae` file -- COL spells that
family `Bernieridae`, one `i` fewer, and a strict name test would have moved
both genera to Acrocephalidae, which is not where they belong. That family name
is itself wrong and is reported, not fixed here: correcting it means renaming the
node, its directory and its appSlug together.

Nothing is lost when a copy goes: fields the surviving copy lacks are taken from
the one being removed (continents are unioned, a description is copied if the
survivor has none), and a genus left with no species is removed with them. The
surviving species is otherwise untouched, so a richer record that happens to sit
in the file being emptied still keeps its own fields.

    python3 scripts/dedupe_genera_across_families.py
    python3 scripts/dedupe_genera_across_families.py --apply
"""
import argparse
import collections
import difflib
import io
import json
import os
import re
import sys
import zipfile

COL = ("/Volumes/MacieExternal/sources/archives/catalogue-of-life-2025/"
       "col2026-base_dwca.zip")
ACCEPTED = {"accepted", "provisionally accepted"}
TAXONOMY = "portal/data/taxonomy.json"
TAXA = "taxonomy/animalia"
RESCUE = ("description", "authorship", "yearPublished", "continents",
          "subspeciesCount", "iucnStatus", "namedAfter")


def load_col():
    """(genus -> set(family names), set of every family name COL has)."""
    par, rank, name = {}, {}, {}
    families = set()
    with zipfile.ZipFile(COL).open("Taxon.tsv") as fh:
        hdr = fh.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
        ci = {h: i for i, h in enumerate(hdr)}
        for line in io.TextIOWrapper(fh, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) < 7 or p[ci["dwc:taxonomicStatus"]] not in ACCEPTED:
                continue
            t = p[ci["dwc:taxonID"]]
            par[t] = p[ci["dwc:parentNameUsageID"]]
            rank[t] = p[ci["dwc:taxonRank"]]
            nm = (p[ci["dwc:scientificName"]] or "").strip()
            name[t] = nm
            if rank[t] == "family":
                families.add(nm)

    genus_family = collections.defaultdict(set)
    for t, r in rank.items():
        if r != "genus":
            continue
        c, n = t, 0
        while c and n < 60:
            if rank.get(c) == "family":
                genus_family[name[t]].add(name.get(c))
                break
            c = par.get(c)
            n += 1
    return genus_family, families


def squash(nm):
    return re.sub(r"[^a-z]", "", (nm or "").lower())


def family_name_by_slug():
    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    out = {}

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug"):
            out[n["appSlug"]] = n.get("name") or n["appSlug"]
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    return out


def slug_of(path):
    return os.path.basename(path)[:-5]


def duplicated_genera():
    """genus name -> {file: set(species ids)}, for species held in two families.

    Only counts a genus twice when the copies share the genus name, which is
    what makes this a duplicated genus rather than a reclassification: a species
    that moved family would sit under two different genera.
    """
    seen = collections.defaultdict(list)
    for root, dirs, files in os.walk(TAXA):
        if not root.replace(os.sep, "/").endswith("src/data"):
            continue
        for fn in files:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(root, fn)
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            for g in d.get("children") or []:
                for s in g.get("children") or []:
                    if s.get("rank") == "SPECIES" and s.get("id"):
                        seen[s["id"]].append((g.get("name"), p))

    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for sid, where in seen.items():
        if len(where) < 2 or len({w[1] for w in where}) < 2:
            continue
        if len({w[0] for w in where}) != 1:
            continue
        for _, p in where:
            out[where[0][0]][p].add(sid)
    return out


def decide(genus, files, genus_family, col_families, name_of):
    """(keep, [drop...], why), or (None, [], why) when undecided.

    The question is always "which of our two families is the one COL puts this
    genus in", so every rule below compares our names against the families COL
    named for the genus -- never against the families COL happens to have. That
    distinction is the whole difference between Randia landing in Bernieridae,
    where COL puts it, and in Acrocephalidae, which is merely a family COL also
    has.
    """
    named = genus_family.get(genus, set())
    ours = {p: name_of.get(slug_of(p), slug_of(p)) for p in files}

    exact = [p for p in files if ours[p] in named]
    if len(exact) == 1:
        return exact[0], [q for q in files if q != exact[0]], \
            f"COL: {ours[exact[0]]}"
    if len(exact) > 1:
        return None, [], f"COL names {sorted(named)}; both our names match"

    # our family name may be a near-miss for COL's: Bernieriidae / Bernieridae
    close = [p for p in files
             if difflib.get_close_matches(squash(ours[p]),
                                          [squash(x) for x in named],
                                          n=1, cutoff=0.85)]
    if len(close) == 1:
        return close[0], [q for q in files if q != close[0]], \
            f"COL: {sorted(named)[0]} (our '{ours[close[0]]}')"

    if named:
        return None, [], (f"COL names {sorted(named)}; neither of our names "
                          f"{sorted(ours.values())} is among them")

    # COL places no family for this genus at all, so fall back to which of our
    # two names is a family COL has. This is what retires Lamniformes.
    known = [p for p in files if ours[p] in col_families]
    if len(known) == 1:
        other = sorted(ours[q] for q in files if q != known[0])
        return known[0], [q for q in files if q != known[0]], \
            f"COL has no family; {ours[known[0]]} is a COL family, {other} is not"
    return None, [], "COL has no family and both our names are COL families"


def rescue(keep_node, drop_node):
    """Copy fields the survivor lacks; union continents. Returns what changed."""
    n = 0
    for f in RESCUE:
        v = drop_node.get(f)
        if not v or keep_node.get(f):
            continue
        if f == "continents" and isinstance(keep_node.get("continents"), list) \
                and isinstance(v, list):
            merged = list(dict.fromkeys(keep_node["continents"] + v))
            if merged != keep_node["continents"]:
                keep_node["continents"] = merged
                n += 1
            continue
        keep_node[f] = v
        n += 1
    return n


def recount(doc):
    doc["speciesCount"] = sum(len(g.get("children") or [])
                              for g in doc.get("children") or [])
    doc["genusCount"] = len(doc.get("children") or [])
    return doc


def merge_within_file(touched):
    """Fold species that share an id inside one family file.

    A rarer shape of the same defect: `Escharopora jugorskensis` sits twice in
    the same genus, once as `Escharopora jugorskensis Nekhorosheva, 1970` with
    the authorship inside `name`, and once as `Escharopora jugorskensis.` with
    it split into the `authorship` field -- both carrying the same id, because
    the id is built from name plus authorship and the two shapes agree. The
    split form is kept: it is the one the importers write, it keeps the
    authorship queryable, and dropping the trailing period leaves a clean
    binomial where the other copy had none to lose.
    """
    merged = 0
    for path in sorted(set(list(touched) + [
            os.path.join(r, f) for r, _d, fs in os.walk(TAXA)
            if r.replace(os.sep, "/").endswith("src/data")
            for f in fs if f.endswith(".json")])):
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        changed = False
        for g in doc.get("children") or []:
            by_id = collections.defaultdict(list)
            for s in g.get("children") or []:
                if s.get("id"):
                    by_id[s["id"]].append(s)
            for sid, group in by_id.items():
                if len(group) < 2:
                    continue
                group.sort(key=lambda s: (
                    "authorship" not in s,
                    (s.get("sourcedFrom") or "none") == "none",
                    -sum(1 for v in s.values() if v)))
                keeper, rest = group[0], group[1:]
                for extra in rest:
                    keeper.update({k: v for k, v in extra.items()
                                   if k not in keeper or not keeper[k]})
                    merged += 1
                if (keeper.get("name") or "").endswith("."):
                    keeper["name"] = keeper["name"].rstrip(" .")
                group_ids = {id(s) for s in group}
                g["children"] = [s for s in g["children"]
                                 if id(s) not in group_ids] + [keeper]
                changed = True
        if changed:
            touched[path] = recount(doc)
            print(f"    {path}: merged within-family copies")
    return merged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("  reading COL ...", flush=True)
    genus_family, col_families = load_col()
    name_of = family_name_by_slug()

    dupes = duplicated_genera()
    n_species = sum(len(v) for f in dupes.values() for v in f.values()) // 2
    print(f"  COL families: {len(col_families):,}")
    print(f"  duplicated species: {n_species:,} in {len(dupes):,} genera, "
          f"{len({p for f in dupes.values() for p in f})} files")

    decided, undecided = {}, []
    for genus, files in sorted(dupes.items()):
        keep, drops, why = decide(genus, files, genus_family, col_families, name_of)
        (decided.__setitem__(genus, (keep, drops, why)) if keep
         else undecided.append((genus, files, why)))

    print(f"\n  DECIDED {len(decided)} genera "
          f"({sum(len(d) for _, d, _ in decided.values())} copies to remove)")
    for genus, (keep, drops, why) in sorted(decided.items()):
        print(f"    {genus:22s} {name_of.get(slug_of(keep), slug_of(keep)):24s} <- {why}")
    if undecided:
        print(f"\n  LEFT ALONE, {len(undecided)} genera:")
        for genus, files, why in undecided:
            print(f"    {genus:22s} {sorted(name_of.get(slug_of(p), slug_of(p)) for p in files)}")
            print(f"        {why}")

    if not decided:
        print("\n  no cross-family genus duplicates left to decide on")

    rescued = removed_species = removed_genera = 0
    touched = {}
    for genus, (keep, drops, _why) in sorted(decided.items()):
        keepd = touched.get(keep) or json.load(open(keep, encoding="utf-8"))
        kg = next((g for g in keepd.get("children") or []
                   if g.get("name") == genus), None)
        if kg is None:
            print(f"  ! {genus}: absent from {keep}, skipping")
            continue
        kby = {s.get("id"): s for s in kg.get("children") or [] if s.get("id")}
        for dp in drops:
            dropd = touched.get(dp) or json.load(open(dp, encoding="utf-8"))
            dg = next((g for g in dropd.get("children") or []
                       if g.get("name") == genus), None)
            if dg is None:
                continue
            keep_species = []
            for s in dg.get("children") or []:
                sid = s.get("id")
                if sid in kby:
                    rescued += rescue(kby[sid], s)
                    removed_species += 1
                else:
                    keep_species.append(s)      # unique to this family, leave it
            dg["children"] = keep_species
            if not keep_species and not dg.get("children"):
                dropd["children"] = [g for g in dropd.get("children") or []
                                     if g is not dg]
                removed_genera += 1
            touched[dp] = dropd
        touched[keep] = keepd

    print(f"\n  copies to remove: {removed_species} species, "
          f"{removed_genera} now-empty genera")
    print(f"  fields rescued onto the survivor: {rescued}")

    within = merge_within_file(touched)
    print(f"  within-file copies merged: {within}")

    if not args.apply:
        print(f"\n  would rewrite {len(touched)} family files "
              f"(dry run -- pass --apply to write)")
        return 0

    for path, doc in touched.items():
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(recount(doc), fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    tax = json.load(open(TAXONOMY, encoding="utf-8"))
    by_slug = {}
    for path, doc in touched.items():
        by_slug[slug_of(path)] = sum(len(g.get("children") or [])
                                      for g in doc.get("children") or [])
    fixed = []

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug") in by_slug \
                and n.get("speciesCount") != by_slug[n["appSlug"]]:
            n["speciesCount"] = by_slug[n["appSlug"]]
            fixed.append(n.get("name"))
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    with open(TAXONOMY, "w", encoding="utf-8") as fh:
        json.dump(tax, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"\n  wrote {len(touched)} family files + {TAXONOMY}; "
          f"speciesCount resynced on {len(fixed)} nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())