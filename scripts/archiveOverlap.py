"""Measure a ChecklistBank DwCA archive against the tree, offline.

Why this exists: `apiOverlapReport.py` pages the ChecklistBank API through
`page_all`, which shards alphabetically on `q` and sums each shard's `total`.
That sum is only valid when `q` actually indexes that rank. It does not, for
these datasets:

    dataset   page_all said   API `total` says
    2037           16,723              283,190
    311094           6,722              371,177
    1024             3,515              120,288
    55434            6,510              162,922

The unfiltered `total` field is the truth; the shard sum is not. So scope is
measured from the archive, which needs no paging and no assumption about what
the API indexes.

Two further normalisation rules, both of which have changed a verdict before:

  * authorship is stripped -- ZooBank writes `Stenus torrenticola Mainda 2025`,
    and we store `Stenus torrenticola`;
  * names go through GNparser -- ZooBank and GLI write subgenus trinomials
    (`Cyana (Strigivulpecula) naumanni`), which are spelling differences, not
    missing taxa.

    TAXASERVE=http://localhost:9882 python3 scripts/archiveOverlap.py 2037 311094
"""
import collections
import csv
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taxamatch as T  # noqa: E402

ARCHIVES = "/Volumes/MacieExternal/sources/archives"
TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")
ACCEPTED = {"accepted", "provisionally accepted", ""}
SPECIES_RANKS = {"species", "subspecies"}


_AUTH_TAIL = re.compile(r"\s+[A-Z][\w.'\-]*(?:\s*(?:,|&|and|in|ex|et)\s*[\w.'\-]*)*"
                        r"(?:\s*\d{4}[a-z]?)?\s*$")


def strip_authorship(n):
    """`Stenus torrenticola Mainda 2025` -> `Stenus torrenticola`.

    Regex only, deliberately. This runs once per offered name, and
    `taxamatch.parse_names` spawns a GNparser subprocess per call -- 371,000 of
    them for BOLD, which is a 45-minute run instead of a 45-second one. The
    parser is applied once to the whole set further down, where it belongs.
    """
    n = re.sub(r"\s*\([^)]*\)\s*", " ", n).strip()
    parts = n.split()
    if len(parts) > 2 and _AUTH_TAIL.search(" " + " ".join(parts[2:])):
        n = " ".join(parts[:2])
    return n


def _read_table(z, member, delim):
    """-> (header index, row iterator) for one table in an archive."""
    f = z.open(member)
    rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                    delimiter=delim)
    hdr = next(rd)
    # ColDP prefixes its columns `col:`; a DwCA does not and spells them
    # `taxonID`/`scientificName` in lower camel. Index the stripped form and the
    # lower-cased form both, so one reader serves either container -- a DwCA
    # whose first column is `id` used to raise KeyError on its own header.
    ix = {}
    for i, h in enumerate(hdr):
        k = h[4:] if h.startswith("col:") else h
        ix[k.lstrip("\ufeff")] = i
        ix.setdefault(k.lstrip("\ufeff").lower(), i)
    return ix, rd


def _family(ix, row, par, rank, name):  # noqa: C901
    """The row's own family column, else the nearest ancestor at family rank."""
    fc = col(ix, "family")
    if fc is not None and len(row) > fc and row[fc]:
        return row[fc].strip()
    ic = col(ix, "ID")
    tid = row[ic] if ic is not None and len(row) > ic else ""
    for _ in range(50):
        p = par.get(tid)
        if not p:
            return ""
        if (rank.get(p) or "").lower() == "family":
            return name.get(p) or ""
        tid = p
    return ""


def col(ix, *names):
    """First column index matching any of `names`, case-insensitively.

    ColDP writes `col:ID`; the DwCA export writes `id`, `taxonID`,
    `scientificName`. One reader serves both only if lookups fold case.
    """
    for n in names:
        if n in ix:
            return ix[n]
        if n.lower() in ix:
            return ix[n.lower()]
    return None


def _collect(par, rank, name, rowof, ix):
    """(names, families, stats) from a parent/name/rank triple."""
    names, fams = [], set()
    stats = collections.Counter()
    for t, r in rank.items():
        if (r or "").lower() not in SPECIES_RANKS:
            continue
        stats[(r or "").lower()] += 1
        if " " in name[t]:
            names.append(name[t])
        fam = _family(ix, rowof.get(t, []), par, rank, name)
        if fam:
            fams.add(fam)
    return names, fams, stats


def read_archive(path):
    """-> (species names, families, stats) for accepted species/subspecies.

    Three archive shapes are in circulation and this reads all three:

      DwCA, one table    taxon.txt -- the standard one-file export (ZooBank)
      ColDP, TSV core    NameUsage.tsv -- one row per name usage, accepted in
                         `status` (BOLD)
      ColDP, CSV tables  taxon.csv + name.csv -- the CSV flavour, where
                         taxon.csv says *which usages are accepted* and
                         name.csv says what they are called. The join is on
                         `taxon.nameID -> name.ID`, NOT on taxon.ID: the taxon
                         table's own ID is the usage id and matches nothing in
                         the name table, so joining on it silently yields zero
                         names rather than an error (GLI)

    The DwCA reader is the one that matters for interpretation: for a
    nomenclatural dataset ChecklistBank writes `accepted` on every row and
    self-references every `acceptedNameUsageID`, so a DwCA offers the register's
    whole content. That is what the source says; whether a nomenclatural
    register's "accepted" is a taxonomic claim is a separate question this
    script does not answer.
    """
    z = zipfile.ZipFile(path)
    members = z.namelist()

    if "NameUsage.tsv" in members:
        ix, rd = _read_table(z, "NameUsage.tsv", "\t")
        par, rank, name, rowof = {}, {}, {}, {}
        for row in rd:
            if len(row) <= ix["scientificName"]:
                continue
            if row[ix["status"]] not in ("accepted", "provisionally accepted"):
                continue
            t = row[ix["ID"]]
            par[t] = row[ix["parentID"]]
            rank[t] = row[ix["rank"]]
            name[t] = row[ix["scientificName"]]
            rowof[t] = row
        return _collect(par, rank, name, rowof, ix)

    taxon = next((m for m in members
                  if m.lower().split("/")[-1].startswith("taxon.")), None)
    if taxon is None:
        sys.exit(f"{path}: no taxon table (members: {members[:6]})")
    delim = "," if taxon.lower().endswith(".csv") else "\t"
    ix, rd = _read_table(z, taxon, delim)

    namefile = next((m for m in members
                     if m.lower().split("/")[-1].startswith("name.")), None)
    nametab = {}
    if namefile:
        nix, nrd = _read_table(z, namefile, ",")
        nid, nn, nr = col(nix, "ID"), col(nix, "scientificName"), col(nix, "rank")
        for row in nrd:
            if None in (nid, nn) or len(row) <= max(nid, nn):
                continue
            nametab[row[nid]] = (row[nn],
                                 row[nr] if nr is not None and len(row) > nr else "")
        join = col(ix, "nameID")

    par, rank, name, rowof = {}, {}, {}, {}
    idcol = col(ix, "ID")
    if idcol is None:
        sys.exit(f"{taxon}: no ID column ({sorted(ix)[:10]})")
    for row in rd:
        if len(row) <= idcol:
            continue
        stcol = col(ix, "taxonomicStatus")
        if stcol is not None and len(row) > stcol \
                and row[stcol] not in ACCEPTED:
            continue
        t = row[idcol]
        pc = col(ix, "parentID", "parentNameUsageID")
        par[t] = row[pc] if pc is not None and len(row) > pc else ""
        if nametab:
            if join is None or len(row) <= join or row[join] not in nametab:
                continue
            name[t], rank[t] = nametab[row[join]]
        else:
            namecol = col(ix, "scientificName", "name")
            if namecol is None or len(row) <= namecol:
                sys.exit(f"{taxon}: no scientificName/name column "
                         f"({sorted(ix)[:10]})")
            name[t] = row[namecol]
            rc = col(ix, "rank", "taxonRank")
            rank[t] = row[rc] if rc is not None and len(row) > rc else ""
        rowof[t] = row
    return _collect(par, rank, name, rowof, ix)


def held_lookup(names, batch=4000):
    out = set()
    for i in range(0, len(names), batch):
        ch = names[i:i + batch]
        req = urllib.request.Request(
            TAXASERVE + "/held", data=json.dumps({"names": ch}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            res = json.load(r)
        out |= set(res.get("held") or {})
    return out


def main():
    if not TAXASERVE:
        sys.exit("set TAXASERVE=http://localhost:9882")
    if len(held_lookup(["Felis catus", "Panthera leo"])) != 2:
        sys.exit("taxaserve is not answering -- another job is probably "
                 "loading it; retry when idle")
    for arg in sys.argv[1:]:
        key, _, slug = arg.partition("=")
        slug = slug or f"checklistbank-{key}"
        path = os.path.join(ARCHIVES, slug, "archive.zip")
        if not os.path.exists(path):
            sys.exit(f"no archive at {path}")
        names, fams, stats = read_archive(path)
        bare = sorted({strip_authorship(n) for n in names})
        parsed = T.parse_names(bare)
        forms = sorted({T.bare_name(n, parsed) or n for n in bare})
        have = held_lookup(forms)
        miss = [n for n in forms if n.lower() not in have]
        # Family coverage cannot be read off `have`: a family name is never a
        # species name, so every family would score 0% held.
        fam_have = held_lookup(sorted(fams))
        fam_miss = sorted(f for f in fams if f.lower() not in fam_have)
        numeric = [n for n in miss if re.search(r"\s\d", n)]
        subgen = [n for n in miss if "(" in n]
        print(f"\n=== {slug}")
        print(f"    accepted species/subspecies rows {stats['species']:,} species"
              f" + {stats['subspecies']:,} subspecies")
        print(f"    distinct names offered          {len(forms):,}")
        print(f"    held {len(forms) - len(miss):,}"
              f"   NOT held {len(miss):,}"
              f"   ({100 * len(miss) / max(1, len(forms)):.1f}%)")
        print(f"      of the miss, numeric epithet    {len(numeric):,}")
        print(f"      of the miss, parentheses form   {len(subgen):,}")
        print(f"    families offered {len(fams):,}   not held {len(fam_miss):,}"
              f"   ({100 * len(fam_miss) / max(1, len(fams)):.1f}%)")
        for n in miss[:10]:
            print(f"        {n}")


if __name__ == "__main__":
    main()