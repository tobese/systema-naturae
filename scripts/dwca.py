#!/usr/bin/env python3
"""Reader for the standard ChecklistBank DwCA export.

Not COL's DwCA, which is a single flat `Taxon.tsv` with Darwin Core headers and
is read by `importColStage2.load_col()`. This is the other shape, the one every
other external ChecklistBank dataset arrives in:

    taxon.tsv    ID, nameID, parentID, ...          the accepted tree
    name.tsv     ID, scientificName, authorship, rank, genus, specificEpithet
    synonym.tsv  ID, taxonID, nameID, ...           names that are NOT accepted

and it matters that those are three files. There is no status column anywhere:
a name is accepted because it appears in taxon.tsv, and a synonym is a row in
synonym.tsv pointing at the accepted taxon. Reading name.tsv alone treats all
1,026,323 WFO synonyms as species, which is how a 382,437-species list would
look like a 1.4M one.

`name.tsv` also carries `genus` and `specificEpithet` already split out, so
nothing here needs GNparser -- which matters because WFO writes subgenus
trinomials (`Aloconota (Aloconota) tenerrima` is the case that made two rounds
of scope measurement wrong for COL, and a source that hands us the parse is a
source that cannot cause it).

    import dwca
    par, rank, name, auth, parsed = dwca.load("archive.zip")
"""
import collections
import csv
import io
import sys
import zipfile

ACCEPTED_RANKS = ("species", "subspecies")


def load(path, rank_filter=ACCEPTED_RANKS):
    """-> (parent, rank, name, authorship, parsed, stats)

    `parent`, `rank`, `name`, `authorship` are keyed by the taxon's own ID and
    cover only accepted taxa, matching what `importColStage2.load_col()` returns
    so the two are interchangeable downstream.

    `parsed` maps taxon ID -> (genus, species, canonical), taken from name.tsv's
    own genus/specificEpithet columns where present and derived otherwise.
    """
    z = zipfile.ZipFile(path)
    taxon_file = _find(z, "taxon.tsv")
    name_file = _find(z, "name.tsv")
    if not taxon_file or not name_file:
        raise SystemExit(f"  {path}: expected taxon.tsv and name.tsv, got "
                         f"{[n for n in z.namelist() if n.endswith('.tsv')]}")

    # names first: taxon rows only carry a nameID
    names = {}
    with z.open(name_file) as f:
        rd = csv.reader(_text(f), delimiter="\t")
        hdr = next(rd)
        ci = {h: i for i, h in enumerate(hdr)}
        need = ("ID", "scientificName", "authorship", "rank", "genus",
                "specificEpithet", "infraspecificEpithet")
        missing = [c for c in need if c not in ci]
        if missing:
            raise SystemExit(f"  {name_file}: missing column(s) {missing}; "
                             f"has {hdr}")
        for row in rd:
            if len(row) <= ci["rank"]:
                continue
            names[row[ci["ID"]]] = (
                (row[ci["scientificName"]] or "").strip(),
                (row[ci["authorship"]] or "").strip(),
                (row[ci["rank"]] or "").strip().lower(),
                (row[ci["genus"]] or "").strip(),
                (row[ci["specificEpithet"]] or "").strip(),
                (row[ci["infraspecificEpithet"]] or "").strip(),
            )

    par, rank, nm, auth, parsed = {}, {}, {}, {}, {}
    stats = collections.Counter()
    with z.open(taxon_file) as f:
        rd = csv.reader(_text(f), delimiter="\t")
        hdr = next(rd)
        ci = {h: i for i, h in enumerate(hdr)}
        for row in rd:
            if len(row) <= ci["ID"]:
                continue
            tid = row[ci["ID"]]
            nid = row[ci["nameID"]] if "nameID" in ci else tid
            rec = names.get(nid)
            if rec is None:
                stats["taxon with no name row"] += 1
                continue
            sci, au, rk, genus, spec, infra = rec
            if rank_filter and rk not in rank_filter:
                stats[f"skipped rank {rk or '(blank)'}"] += 1
                continue
            par[tid] = (row[ci["parentID"]] if "parentID" in ci else "") or ""
            rank[tid] = rk
            nm[tid] = sci
            auth[tid] = au
            # canonical binomial from name.tsv's own columns where it has them
            g, s = genus, spec
            if not (g and s):
                g, s = _derive(sci)
            canonical = f"{g} {s}".strip() if (g and s) else sci
            parsed[tid] = (g, s, canonical)
            stats["accepted " + (rk or "?")] += 1

    with z.open(_find(z, "synonym.tsv")) if _find(z, "synonym.tsv") else _null() as f:
        if f is not None:
            rd = csv.reader(_text(f), delimiter="\t")
            next(rd, None)
            stats["synonym names (excluded)"] = sum(1 for _ in rd)
    return par, rank, nm, auth, parsed, stats


def _derive(sci):
    """(genus, species) from a scientific name string.

    Only a fallback: name.tsv supplies genus/specificEpithet directly in this
    export. Subgenus parentheses are dropped the way `importColStage2` does, so
    a trinomial does not read as a species we do not have.
    """
    s = (sci or "").replace("×", " ").split()
    s = [x for x in s if x.lower() != "x" and x not in ("subsp.", "var.")]
    s = [x.strip("()") for x in s]
    s = [x for x in s if x and not x.endswith(")") and "(" not in x]
    if len(s) >= 2:
        return s[0], s[1]
    return (s[0] if s else ""), ""


def _find(z, name):
    for n in z.namelist():
        if n.rsplit("/", 1)[-1] == name:
            return n
    return None


def _text(f):
    return io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline="")


class _null:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "archive.zip"
    par, rank, nm, auth, parsed, stats = load(p)
    print(f"  {p}")
    for k, v in stats.most_common(12):
        print(f"      {v:>9,}  {k}")
    ks = list(parsed)[:5]
    for k in ks:
        print(f"    {nm[k]!r:44s} rank={rank[k]:10s} parsed={parsed[k]}")
