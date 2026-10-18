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
# Spellings of the single core table seen in the wild beyond COL's own
# "NameUsage.tsv": lowercase (nameusage.csv/.txt), an underscore
# (name_usage.txt), and any extension -- the content is the deciding
# factor, not the name. One archive (1051) also has the inverse problem,
# a .csv extension on an actually tab-delimited file, which is why the
# delimiter is sniffed from content too (see find_delimiter below) rather
# than inferred from whichever extension the table happens to carry.
CORE_STEMS = ("nameusage", "name_usage")


def find_core_table(names):
    """First member whose basename (any case, any extension) is a known
    spelling of the single-table core, or None.

    Used both to decide whether an archive is ColDP-single-table shaped
    (colChecklist.py's dispatcher) and to find the actual member to open
    (load_core below) -- one place names the spellings, not two
    independently-maintained lists that can drift apart the way the
    family-path resolution logic once did across six different scripts.
    """
    for m in names:
        base = m.rsplit("/", 1)[-1]
        if "." in base and base[:base.rindex(".")].lower() in CORE_STEMS:
            return m
    return None


def find_delimiter(first_line):
    """Tab, comma, or pipe -- whichever splits `first_line` into the most
    fields.

    A file's extension is not proof of its delimiter: ChecklistBank
    dataset 1051 ships "Name.csv"/"Taxon.csv" that are actually
    tab-delimited, so trusting ".csv" split every row on the wrong
    character and the header lookup raised KeyError 'id' downstream --
    a parse failure blamed on the wrong layer entirely. Pipe is WCVP's
    (2232) own delimiter, declared in its meta.xml as fieldsTerminatedBy="|"
    -- real DwC-A archives are not limited to tab/comma, so neither is this.
    """
    return max(("\t", ",", "|"), key=first_line.count)
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
#
# "established" is ICZN nomenclatural vocabulary, not COL's taxonomic-status
# vocabulary -- found on the GLI-shaped name.csv/taxon.csv/synonym.csv split
# (see load_core_csv's docstring) when the exporting tool is Species File
# Group software rather than ChecklistBank's own COL pipeline. Confirmed on
# two independent real checklists (Sesiidae.net/309267, a Lepidoptera site's
# own export/55353): every row in taxon.csv carries status="established" and
# nothing else, with the real accepted/synonym split already decided by file
# membership -- exactly GLI's own "accepted is decided by file membership"
# design. Without this, load_core_csv's status filter drops every row in the
# table, which reads as "this dataset is empty" rather than "this reader
# doesn't know this vocabulary".
ACCEPTED = {"accepted", "provisionally accepted", "established"}


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

    "id"/"parentId" are a third kind of drift, not a DwCA/ColDP vocabulary
    difference at all: Species File Group's own export tooling (1164)
    writes col:id and col:parentId where COL's own pipeline writes col:ID
    and col:parentID -- same field, just lower-cased by whichever tool
    produced it. load_core()'s column lookup is case-sensitive, so the
    export was otherwise correct ColDP, carrying every field this reader
    needs, and still failed with "no column col:ID" over a one-letter
    casing difference.
    """
    DWCA = {
        "taxonID": "ID",
        "parentNameUsageID": "parentID",
        "acceptedNameUsageID": "acceptedID",
        "taxonomicStatus": "status",
        "taxonRank": "rank",
        "scientificName": "scientificName",
        "scientificNameAuthorship": "authorship",
        "id": "ID",
        "parentId": "parentID",
    }
    out = {}
    for i, h in enumerate(header):
        bare = h[4:] if h.startswith(("col:", "dwc:")) else h
        bare = bare.strip('"')
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
        names = z.namelist()
        core = CORE if CORE in names else find_core_table(names)
        if core is None:
            if any(m.lower().endswith("taxon.csv") for m in names):
                # ColDP's CSV flavour; read by load_core_csv() below.
                return load_core_csv(path, accepted, want_authorship)
            raise KeyError(f"{CORE} not in {os.path.basename(path)}; "
                           f"members: {sorted(names)[:8]}")
        # Delimiter and BOM are sniffed from a short-lived peek rather than
        # a full read: NCBI Taxonomy (2169) decompresses to 418MB, and this
        # path has to stay streaming-safe for it. Opening the member twice
        # costs one extra decompression of its first line, not its whole
        # contents.
        # utf-8-sig, not plain utf-8: a UTF-8 byte-order-mark on the header
        # (seen on two of the newly-recognized core-table variants, 290628
        # and 313711) decodes under plain utf-8 as an invisible extra
        # character glued onto the first column name, so every lookup for
        # that column fails. utf-8-sig strips a leading BOM if present and
        # is identical to utf-8 otherwise.
        with z.open(core) as probe:
            first_line = probe.readline().decode("utf-8-sig", errors="replace")
        delim = find_delimiter(first_line)
        # NCBI Taxonomy (2169) has a stray literal `"` in a free-text
        # remarks field. csv's default QUOTE_MINIMAL treats that as the
        # start of a quoted field and keeps consuming subsequent physical
        # lines looking for the matching close-quote, merging real rows
        # together until it either finds one or blows the field-size
        # limit -- 154,774 rows silently vanished this way before the
        # limit was even hit. Tab-delimited exports here have no
        # CSV-style quoting convention of their own, so QUOTE_NONE reads
        # each physical line as its own row, which is what every
        # tab-shaped source turned out to actually be. A genuinely
        # comma-delimited export (1049, 290628, 313711) is ordinary CSV
        # and is expected to follow CSV's own quoting rules instead, so
        # QUOTE_NONE only applies to the tab case.
        quoting = csv.QUOTE_NONE if delim == "\t" else csv.QUOTE_MINIMAL
        with z.open(core) as f:
            rd = csv.reader(
                io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace"),
                delimiter=delim, quoting=quoting)
            ix = _columns(next(rd))
            for col in ("ID", "parentID", "status", "rank", "scientificName"):
                if col not in ix:
                    raise KeyError(f"{core} has no column col:{col} "
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
                row = [v.strip('"') if v else v for v in row]
                if len(row) <= i_nm or (row[i_st] or "").strip().lower() not in accepted:
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
            # The extension lies on some exports -- see find_delimiter's
            # docstring. Delimiter and BOM are sniffed from a short-lived
            # peek rather than a full read: the largest name/taxon table
            # seen on the shelf (GLI, 55434) is ~75MB, and reading that much
            # into memory just to find a delimiter is needless. Opening the
            # member twice costs one extra decompression of its first
            # line, not its whole contents.
            # utf-8-sig rather than plain utf-8, same reasoning as
            # load_core()'s own BOM comment above: a UTF-8 byte-order-mark
            # on the header otherwise decodes as an invisible extra
            # character glued onto the first column name, so every lookup
            # for that column fails. utf-8-sig strips a leading BOM if
            # present and is identical to utf-8 otherwise.
            with z.open(nxt) as probe:
                first_line = probe.readline().decode("utf-8-sig", errors="replace")
            delim = find_delimiter(first_line)
            rd = csv.reader(
                io.TextIOWrapper(z.open(nxt), encoding="utf-8-sig", errors="replace"),
                delimiter=delim)
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