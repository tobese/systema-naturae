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
# ColDP rank values are not uniform across datasets. Catalogue of Life's own
# exports use the English ranks; other ChecklistBank sources use the
# ziological/Latin ones, which is what Wikispecies (314570) does:
# Hominidae is rank "familia", Homininae "subfamilia", Hominini "tribus",
# Hominoidea has no rank at all. Left untranslated, every one of the 78,731 new
# Wikispecies species came back with no family, because chain() was looking for
# "family" in a vocabulary that spells it "familia".
RANK_ALIASES = {
    "familia": "family", "subfamilia": "subfamily", "superfamilia": "superfamily",
    "tribus": "tribe", "subtribus": "subtribe", "ordo": "order",
    "varietas": "variety", "sectio": "section", "subsectio": "subsection",
    "series": "series zoology", "subseries": "subseries",
    "divisio": "division", "subdivisio": "subdivision",
    "cohortus": "cohort", "legio": "legion", "ordo_": "order",
    "uninomial": "genus", "species_": "species",
    "morphospecies": "species", "nodospecies": "species",
}


def norm_rank(r):
    if not r:
        return r
    return RANK_ALIASES.get(r.strip().lower(), r)
# same set the DwCA importers accept
ACCEPTED = {"accepted", "provisionally accepted"}


def _columns(header):
    """index -> column name, with DwCA/ColDP namespaces resolved.

    Species Fungorum (dataset 2073) is a DwCA whose columns are all `dwc:`,
    not `col:`, so without the second prefix every lookup for ID / parentID /
    scientificName failed and the import refused the whole source. Strip
    whichever DwCA namespace prefix is present.

    The DwCA term names also differ from the ColDP names load_core looks up:
    dwc:taxonID -> ID, dwc:parentNameUsageID -> parentID, dwc:taxonomicStatus
    -> status, dwc:taxonRank -> rank. Map those too, because the importers
    index by the ColDP names and would otherwise refuse the source.
    """
    DWCA = {
        "taxonID": "ID",
        "parentNameUsageID": "parentID",
        "acceptedNameUsageID": "acceptedID",
        "taxonomicStatus": "status",
        "taxonRank": "rank",
        "scientificName": "scientificName",
        "scientificNameAuthorship": "authorship",
    }
    out = {}
    for i, h in enumerate(header):
        bare = h[4:] if h.startswith(("col:", "dwc:")) else h
        out[DWCA.get(bare, bare)] = i
    return out


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
                    # Strip the ColDP/DwCA namespace prefix. load_core used to
                    # strip only `col:`, which is what ChecklistBank's own
                    # exports carry -- but Species Fungorum (dataset 2073) is a
                    # DwCA whose columns are all `dwc:`, so every lookup for
                    # ID / parentID / scientificName failed and the import
                    # refused the whole source. Strip whichever prefix is
                    # present, leaving the bare column name.
                    yield n, {
                        (k[4:] if k and k.startswith(("col:", "dwc:")) else k): v
                        for k, v in row.items()
                    }


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
            if any(m.lower().endswith("taxon.csv") for m in z.namelist()):
                # ColDP's CSV flavour; read by load_core_csv() below.
                return load_core_csv(path, accepted, want_authorship)
            raise KeyError(f"{CORE} not in {os.path.basename(path)}; "
                           f"members: {sorted(z.namelist())[:8]}")
        with z.open(CORE) as f:
            # NCBI Taxonomy (2169) has a stray literal `"` in a free-text
            # remarks field. csv's default QUOTE_MINIMAL treats that as the
            # start of a quoted field and keeps consuming subsequent physical
            # lines looking for the matching close-quote, merging real rows
            # together until it either finds one or blows the field-size
            # limit -- 154,774 rows silently vanished this way before the
            # limit was even hit. These are plain tab-separated files with no
            # CSV-style quoting convention of their own; QUOTE_NONE reads each
            # physical line as its own row, which is what every source here
            # actually is.
            rd = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                delimiter="\t", quoting=csv.QUOTE_NONE)
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
            # The World Spider Catalog (56185) leaves col:scientificName empty
            # on every row and expects the reader to build it from the parts
            # instead -- genericName (which it also overloads for the bare
            # name at ranks above genus, e.g. a family row's genericName is
            # "Bemmeridae") plus specificEpithet/infraspecificEpithet for
            # species and below. uninomial exists in the header but was empty
            # on every row sampled; included anyway since it's the term ColDP
            # actually defines for this.
            i_uni = ix.get("uninomial")
            i_gen = ix.get("genericName")
            i_sp = ix.get("specificEpithet")
            i_isp = ix.get("infraspecificEpithet")
            # The Mammal Diversity Database (9802) leaves col:parentID blank on
            # every row -- there is no hierarchy to walk at all -- and gives the
            # full classification as flat columns per row instead, same idea as
            # genericName/specificEpithet above but one rank up. Kept alongside
            # link/reference/status below, keyed to match colChecklist.py's
            # CHAIN_COL names (`{rank}_name`) so chain()'s denormalised-column
            # fallback reads them with no extra translation.
            i_rankcol = {rnk: ix.get(rnk) for rnk in
                         ("kingdom", "phylum", "class", "order", "family")}
            for row in rd:
                if len(row) <= i_nm or row[i_st] not in accepted:
                    continue
                t = row[i_id]
                par[t] = row[i_par]
                rank[t] = norm_rank(row[i_rank])
                nm = row[i_nm]
                if not nm:
                    parts = [row[i] for i in (i_uni, i_gen, i_sp, i_isp)
                             if i is not None and len(row) > i and row[i]]
                    nm = " ".join(parts)
                name[t] = nm
                if want_authorship:
                    e = {}
                    if i_auth is not None and len(row) > i_auth:
                        e["authorship"] = row[i_auth].strip()
                    if i_link is not None and len(row) > i_link:
                        e["link"] = row[i_link]
                    if i_ref is not None and len(row) > i_ref:
                        e["reference"] = row[i_ref]
                    if i_st is not None:
                        e["status"] = row[i_st]
                    for rnk, i_rc in i_rankcol.items():
                        if i_rc is not None and len(row) > i_rc and row[i_rc]:
                            e[f"{rnk}_name"] = row[i_rc]
                    extra[t] = e
    return par, rank, name, extra


def load_core_csv(path, accepted=ACCEPTED, want_authorship=True):
    """`load_core()` for ColDP's CSV flavour, which splits name from usage.

    GLI (ChecklistBank 55434) ships `name.csv`, `taxon.csv` and `synonym.csv`
    rather than one `NameUsage.tsv`, so `load_core()` found no core table and
    the importer reported **0 accepted species offered** -- which reads as "this
    dataset has nothing in it" rather than as "this reader does not read this
    container".

    The join is `taxon.nameID -> name.ID`, and it is worth being explicit about
    why: `taxon.ID` is the *usage* id and matches nothing in the name table, so
    joining on it yields zero rows with no error at all. The split is also the
    point of the flavour -- taxon.csv holds only the accepted usages and
    synonym.csv the rest -- so "accepted" is decided by file membership here
    rather than by a status string.
    """
    par, rank, name, extra = {}, {}, {}, {}
    with zipfile.ZipFile(path) as z:
        members = z.namelist()

        def table(base):
            nxt = next((m for m in members
                        if m.lower().split("/")[-1].startswith(base + ".")), None)
            if nxt is None:
                return None, None
            delim = "," if nxt.lower().endswith(".csv") else "\t"
            f = z.open(nxt)
            rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8",
                                             errors="replace"), delimiter=delim)
            hdr = next(rd)
            ix = {(h[4:] if h.startswith(("col:", "dwc:")) else h): i
                  for i, h in enumerate(hdr)}
            ix.update({k.lower(): v for k, v in list(ix.items())})
            return rd, ix

        nrd, nix = table("name")
        if nrd is None:
            raise KeyError(f"{os.path.basename(path)} has no name table; "
                           f"members: {sorted(members)[:8]}")
        nametab = {}
        for row in nrd:
            if len(row) <= max(nix["id"], nix["scientificname"]):
                continue
            nametab[row[nix["id"]]] = (
                row[nix["scientificname"]],
                row[nix["rank"]] if "rank" in nix and len(row) > nix["rank"] else "",
                row[nix["authorship"]] if "authorship" in nix
                and len(row) > nix["authorship"] else "")

        trd, tix = table("taxon")
        if trd is None:
            raise KeyError(f"{os.path.basename(path)} has no taxon table; "
                           f"members: {sorted(members)[:8]}")
        st = tix.get("taxonomicstatus") or tix.get("status")
        for row in trd:
            if len(row) <= max(tix["id"], tix["parentid"], tix["nameid"]):
                continue
            if st is not None and len(row) > st and row[st] not in accepted:
                continue
            nid = row[tix["nameid"]]
            if nid not in nametab:
                continue
            t = row[tix["id"]]
            nm, rk, au = nametab[nid]
            par[t] = row[tix["parentid"]]
            rank[t] = norm_rank(rk)
            name[t] = nm
            # Membership in taxon.csv *is* the accepted set in this flavour, and
            # saying so matters downstream: colChecklist._coldp() derives
            # `is_synonym` from the absence of an accepted status, so leaving
            # the key out marks every accepted taxon a synonym.
            extra[t] = {"authorship": au, "status": "accepted"}
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