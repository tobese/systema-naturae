#!/usr/bin/env python3
"""Reader for ColDP archives -- Catalogue of Life Data Package.

A ColDP archive is a zip of TSVs whose columns are prefixed `col:`, with
`metadata.yaml` describing the dataset. This reads the core table,
`NameUsage.tsv`, into the same four dictionaries `importColStage2.load_col()`
builds from a DwCA, so everything downstream of that -- the A/B/C bucketing, the
GNparser normalisation, `canonical()`, the placement logic -- works unchanged on
either container.

That equivalence is the whole point, and it is close to exact. COL's DwCA export
has seven columns; six map one-to-one onto ColDP's core:

    DwCA taxonID                -> col:ID
    DwCA parentNameUsageID      -> col:parentID
    DwCA taxonomicStatus        -> col:status
    DwCA taxonRank              -> col:rank
    DwCA scientificName         -> col:scientificName
    DwCA scientificNameAuthorship -> col:authorship

The seventh, `acceptedNameUsageID`, is absent: ColDP puts the accepted name in
the *status* column and the link in `col:nameStatus`/`col:basionymID` instead,
so a synonym row here names its own accepted counterpart only via the status
value. The other 19 columns are what DwCA cannot express -- basionym and
combination authorship with years, `col:temporalRangeStart`/`End`,
`col:publishedIn*`, `col:link` (the source's own identifier), and
`col:referenceID`, which is the per-name provenance the DwCA export has no
column for. Those are what make ColDP worth preferring, and this reader
deliberately does not throw them away: `load_core()` keeps `link`, `reference`
and `authorship`, and `aux_tables()` will hand back the rest.

Only `status` is treated as a filter, matching the DwCA importers: `accepted`
and `provisionally accepted` are the names worth offering. `nameStatus` is *not*
used as a second filter -- in ColDP it distinguishes a doubtful name
(`ambiguous synonym`), which is a property of a synonym, not of an accepted
taxon, and filtering on both would silently drop names.

Nothing here trusts a column position: the header is read and columns are looked
up by name with the `col:` prefix stripped, so a producer that reorders or adds
columns does not shift every value into the wrong field.
"""
import csv
import io
import json
import os
import zipfile

CORE = "NameUsage.tsv"
# same set the DwCA importers accept
ACCEPTED = {"accepted", "provisionally accepted"}


def _columns(header):
    """col:-stripped name -> index."""
    return {(h[4:] if h.startswith("col:") else h): i
            for i, h in enumerate(header)}


def metadata(path):
    """The archive's metadata.yaml, parsed as far as YAML without a YAML lib.

    ChecklistBank writes a flat-ish document; only the scalar keys are read,
    which is all `metadata()` needs and avoids taking a PyYAML dependency for
    six fields. Nested lists (contact:, creator:) are returned as their raw
    lines so nothing is silently dropped.
    """
    with zipfile.ZipFile(path) as z:
        try:
            raw = z.read("metadata.yaml").decode("utf-8", "replace")
        except KeyError:
            return {}
    out, block = {}, None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if block:
                out[block].append(line.strip())
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        block = None
        if val in ("", "|-", "|"):
            out[key] = []
            block = key
        else:
            out[key] = val
    return out


def aux_tables(path, names=("VernacularName", "Distribution", "Media",
                             "Reference", "TaxonProperty", "Author",
                             "SpeciesInteraction", "NameRelation")):
    """Yield (table, dict) for the non-core tables that exist in the archive."""
    with zipfile.ZipFile(path) as z:
        have = set(z.namelist())
        for n in names:
            fn = f"{n}.tsv"
            if fn not in have:
                continue
            with z.open(fn) as f:
                rd = csv.DictReader(
                    io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                    delimiter="\t")
                for row in rd:
                    yield n, {(k[4:] if k and k.startswith("col:") else k): v
                              for k, v in row.items()}


def load_core(path, accepted=ACCEPTED, want_authorship=True):
    """Read NameUsage.tsv into the dictionaries the DwCA importers expect.

    Returns (par, rank, name, extra) where the first three match `load_col()`'s
    signature -- id -> parent id, id -> rank, id -> scientific name -- and
    `extra` is id -> dict of the provenance columns (`link`, `reference`,
    `authorship`), or id -> {} when `want_authorship` is False.

    Authorship is kept only for accepted taxa, which is all the importers ever
    read it for; a DwCA of the same size stores it for everything and that is
    most of why these dicts get large.
    """
    par, rank, name, extra = {}, {}, {}, {}
    with zipfile.ZipFile(path) as z:
        if CORE not in z.namelist():
            raise KeyError(f"{CORE} not in {os.path.basename(path)}; "
                           f"members: {sorted(z.namelist())[:8]}")
        with z.open(CORE) as f:
            rd = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                delimiter="\t")
            ix = _columns(next(rd))
            for col in ("ID", "parentID", "status", "rank", "scientificName"):
                if col not in ix:
                    raise KeyError(f"{CORE} has no column col:{col} "
                                   f"(found: {sorted(ix)[:12]})")
            i_id, i_par = ix["ID"], ix["parentID"]
            i_st, i_rank, i_nm = ix["status"], ix["rank"], ix["scientificName"]
            i_auth = ix.get("authorship")
            i_link = ix.get("link")
            i_ref = ix.get("referenceID")
            for row in rd:
                if len(row) <= i_nm or row[i_st] not in accepted:
                    continue
                t = row[i_id]
                par[t] = row[i_par]
                rank[t] = row[i_rank]
                name[t] = row[i_nm]
                if want_authorship:
                    e = {}
                    if i_auth is not None and len(row) > i_auth:
                        e["authorship"] = row[i_auth].strip()
                    if i_link is not None and len(row) > i_link:
                        e["link"] = row[i_link]
                    if i_ref is not None and len(row) > i_ref:
                        e["reference"] = row[i_ref]
                    extra[t] = e
    return par, rank, name, extra


def chain(tid, par, rank, name, ranks=("kingdom", "superkingdom", "domain",
                                       "phylum", "class", "order", "family")):
    """tid -> {rank: name} for the first ancestor (inclusive) at each rank.

    Same contract as `importColStage2.chain()`: first match walking upward wins,
    so a taxon is described by the nearest ancestor carrying each rank.
    """
    out = {}
    c, n = tid, 0
    seen = set()
    while c and n < 200 and c not in seen:
        seen.add(c)
        r = rank.get(c)
        if r in ranks and r not in out:
            out[r] = name.get(c)
        c = par.get(c)
        n += 1
    return out


def root_of(tid, par):
    c, n, seen = tid, 0, set()
    while c and n < 200 and c not in seen:
        seen.add(c)
        p = par.get(c)
        if not p or p == c:
            break
        c = p
        n += 1
    return c


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: coldp.py <archive.zip>   # prints metadata + core size")
    p = sys.argv[1]
    md = metadata(p)
    print(json.dumps({k: v for k, v in md.items()
                      if k in ("alias", "title", "issued", "version", "license",
                               "taxonomicScope", "geographicScope", "url",
                               "notes")}, indent=1, ensure_ascii=False))
    par, rank, name, _ = load_core(p, want_authorship=False)
    print(f"accepted name usages: {len(par):,}")