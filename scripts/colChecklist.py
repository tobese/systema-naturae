#!/usr/bin/env python3
"""Reader for the per-checklist exports ChecklistBank serves at /dataset/<key>/archive.zip.

This is not ColDP and not a DwCA, and it is not one shape either. Two datasets
fetched the same afternoon from the same endpoint differ:

    reptile-db   Taxon.tsv columns are bare snake_case: id, parent_id, name_id,
                 name_phrase, ... and its Metadata.json contains YAML
    craneflies   Taxon.tsv columns are col:-prefixed and camelCased: col:id,
                 col:parentId, col:nameId, ... and its Metadata.json is JSON

Both split the COL data model across tables -- Taxon.tsv for the hierarchy,
Name.tsv for the names, Synonym.tsv for the synonyms -- rather than putting
everything in one NameUsage.tsv the way ColDP does. Both carry empty
denormalised chain columns in practice: reptile-db's `family_name` is empty on
every one of its 17,042 rows, so the chain has to come from walking parents
rather than from the columns that look like they hold it.

So the schema is discovered rather than assumed. `load()` maps whatever it is
given onto one set of names, handling the `col:` prefix and snake_case/camelCase
variants, and resolves every field by name -- never by position, which is what
would silently shift a value into the wrong column here.

Accepted taxa are Taxon.tsv rows whose name is not in Synonym.tsv. Note that
Name.tsv carries no usable status: all 34,366 reptile-db rows have `status`
empty, so status cannot be the filter it is in a DwCA. ReptileDB's 34,366 names
resolve to 17,042 accepted taxa plus 17,325 synonyms, which is the only place
the split is recorded.

    python3 scripts/colChecklist.py <archive.zip>
"""
import csv
import io
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile

# COL China's taxon.txt carries a huge denormalised remarks/reference field on
# some rows and overflows the csv module's 128KB default (Nortaxa and the
# Brazilian Fauna catalogue stay under it, so this only bit one of the three).
csv.field_size_limit(10_000_000)

# our name -> the variants seen in the wild
FIELDS = {
    # Dyntaxa (2041) calls its own id column "taxonId", a UTF-8 BOM riding
    # on the first byte of the header line (both normalised away already by
    # `_norm`; what's left is just a column-naming variant like every other
    # one in this dict).
    "id": ("id", "taxonid"),
    "parent": ("parentid", "parentnameusageid"),
    "name_id": ("nameid",),
    "name_phrase": ("namephrase",),
    "scientific_name": ("scientificname",),
    "authorship": ("authorship", "authorshipstring", "scientificnameauthorship"),
    "rank": ("rank", "taxonrank"),
    # a single-table DwCA (no Name.tsv to carry the split) marks synonymy
    # right on the taxon row instead -- LCVP, not reptile-db/craneflies,
    # which is why `is_synonym` below checks this before falling back to
    # `synonym_ids`.
    "status": ("taxonomicstatus",),
    "genus": ("genus",),
    "species_epithet": ("speificepithet",),
    "infraspecific_epithet": ("infrspecificepithet", "infraspepithet",
                              "infraspecificepithet"),
    # Real Darwin Core terms are bare ("kingdom", "family", ...); the
    # "...name" variants are a convention some publishers layer on top
    # (reptile-db's own `family_name` column, empty on all 17,042 rows).
    # COL China (312616) uses the bare DwC terms directly.
    "kingdom_name": ("kingdomname", "kingdom"),
    "phylum_name": ("phylumname", "phylum"),
    "class_name": ("classname", "class"),
    "order_name": ("ordername", "order"),
    "family_name": ("familyname", "family"),
}

# A taxonomicStatus value that means "this is the name to use", not a
# synonym. Nortaxa (2030) writes "valid" where DwC's own vocabulary says
# "accepted" -- same concept, different publisher's word for it.
ACCEPTED_STATUS = {"accepted", "provisionally accepted", "valid", "nome_aceito"}

# Rank vocabularies seen so far that are not the plain English terms both
# the candidate filter (importColChecklist.py: rank in ("species",
# "subspecies")) and `chain()` below expect. Applied once, at the row's own
# rank, rather than only inside `chain()` -- APNI's Latin ranks (Regnum,
# Division, Classis, Ordo, Familia, and crucially "Species"/"Subspecies"
# which happen to already match) got the candidate filter for free because
# Latin species-rank spells the same in English, but Flora e Funga do
# Brasil's Portuguese (ESPECIE, SUBESPECIE, GENERO, FAMILIA, ORDEM, CLASSE)
# does not, and read as zero candidates until normalised here too.
RANK_SYNONYMS = {
    "regnum": "kingdom", "division": "phylum", "divisio": "phylum",
    "classis": "class", "ordo": "order", "familia": "family",
    "especie": "species", "subespecie": "subspecies",
    "sub_especie": "subspecies", "genero": "genus", "ordem": "order",
    "classe": "class", "variedade": "variety", "forma": "form",
    "tribo": "tribe",
}

# rank -> the column that may carry it directly on the taxon row
CHAIN_COL = {r: f"{r}_name" for r in
             ("kingdom", "phylum", "class", "order", "family")}


class _Container:
    """zipfile or tarfile, same three methods.

    The endpoint is named archive.zip and answers with content-type
    application/zip, but ILDIS (1015) returns a gzip'd tar whose members are
    its own tables. Trusting the name is how a reader ends up raising
    BadZipFile on a valid download, so the magic decides.
    """

    def __init__(self, path):
        with open(path, "rb") as fh:
            magic = fh.read(2)
        if magic == b"PK":
            import zipfile
            self._z = zipfile.ZipFile(path)
            self._t = None
        elif magic == b"\x1f\x8b":
            import tarfile
            self._t = tarfile.open(path, "r:gz")
            self._z = None
        else:
            raise ValueError(f"{path}: not a zip or gzip (magic {magic!r})")

    def names(self):
        return self.namelist()

    def namelist(self):
        return sorted(self._z.namelist()) if self._z else self._t.getnames()

    def read(self, name):
        if self._z:
            return self._z.read(name)
        return self._t.extractfile(name).read()

    def open(self, name):
        if self._z:
            return self._z.open(name)
        import io as _io
        return _io.BytesIO(self.read(name))

    def close(self):
        if self._z:
            self._z.close()
        if self._t:
            self._t.close()


def _norm(h):
    """Column name -> comparison key: strip col:, lowercase, drop underscores."""
    h = h[4:] if h.startswith(("col:", "dwc:")) else h
    return re.sub(r"[^a-z0-9]", "", h.lower())


# What each table must have. They differ: Name.tsv is names, so it has no
# parent or name_id, and Taxon.tsv has no scientific_name either -- it carries
# name_phrase plus the denormalised species_name/genus_name/... columns. Asking
# all three for the union of every field is what made the first version reject
# reptile-db outright.
REQUIRED = {
    "name": ("id", "scientific_name", "rank"),
    "synonym": ("name_id",),
    # Neither name_id nor parent is required here. LCVP (no Name.tsv) carries
    # scientific_name/rank/authorship/status directly on the taxon row
    # instead of joining to a name table. COL China goes further and has no
    # parent column at all -- kingdom/phylum/class/order/family/genus are
    # flat columns on every row, like ILDIS and EUNIS, just denormalised
    # alongside a parent-walk-shaped table instead of a single-purpose one.
    # `chain()` already treats a missing parent as "stop after this row's
    # own columns", which is exactly right for that shape.
    "taxon": ("id",),
}


def _find(c, *stems):
    """First member whose basename matches one of `stems`, any case, extension.

    ChecklistBank native DwCA exports (COL China, Nortaxa, the Brazilian
    Fauna catalogue) name their tables `taxon.txt`/`name.txt`, not the
    `.tsv` this reader's TAXON_TABLES/NAME_TABLES/SYN_TABLES tuples list --
    those matched ColDP's own convention (craneflies, reptile-db) and the
    `.txt` DwCA shape silently read as zero taxa, no error, the same "looks
    empty" failure GLI's CSV flavour produced before `_coldp` learned to
    read it. One stem-matching lookup handles every extension at once.
    Multiple stems because APNI (133813) calls its taxon table `taxa.tsv`,
    plural, a fourth spelling of the same table.
    """
    for m in c.namelist():
        base = m.rsplit("/", 1)[-1]
        if "." in base and base[:base.rindex(".")].lower() in stems:
            return m
    return None


def _find_taxon_table(c):
    """The core taxon table, by filename stem first, by meta.xml's own
    rowType declaration otherwise.

    WCVP (2232, 507MB) and MSW3 (2019) are both well-formed, standard DwC-A
    archives -- meta.xml fully and correctly describes every column -- but
    each names its single core table after the dataset itself
    ("wcvp_taxon.csv", "msw3-dwc.txt"), which `_find()`'s stem match can't
    see past: neither basename-minus-extension equals "taxon" or "taxa", so
    the table was never located at all and `_rows()`/`_meta_positions()`
    never got a chance to run on it, which is why "this is a header-less
    DwC-A, read it positionally" looked like a bigger problem than it was --
    the positional reader already existed and worked, it just never got
    called. A `<core>` block's own `rowType` ending in ".../Taxon" is
    unambiguous regardless of what the exporter chose to call the file, so
    it's checked second, only when the plain stem match already failed
    (every other archive keeps using that proven path unchanged).
    """
    found = _find(c, "taxon", "taxa")
    if found:
        return found
    meta_name = next((n for n in c.names() if n.rsplit("/", 1)[-1] == "meta.xml"), None)
    if not meta_name:
        return None
    try:
        root = ET.fromstring(c.read(meta_name))
    except ET.ParseError:
        return None
    for block in root:
        tag = block.tag.rsplit("}", 1)[-1]
        if tag != "core":
            continue
        if not (block.get("rowType") or "").endswith("/Taxon"):
            continue
        loc = block.find(".//{*}location")
        if loc is None or not (loc.text or "").strip():
            continue
        # meta.xml's <location> is a bare filename (MSW3: "msw3-dwc.txt"),
        # but the real archive member carries a directory prefix the
        # exporter put every file under (MSW3: "msw3/msw3-dwc.txt") --
        # the same mismatch meta.xml's own lookup above already has to
        # resolve for meta.xml itself. Resolved against the real member
        # list the same way, rather than opening the bare name and
        # getting a KeyError from the zip/tar layer.
        want = loc.text.strip().lower()
        return next((n for n in c.names() if n.rsplit("/", 1)[-1].lower() == want), None)
    return None


def _index(header, require):
    key = {}
    for i, h in enumerate(header):
        k = _norm(h)
        if k and k not in key:
            key[k] = i
    out = {}
    for ours, variants in FIELDS.items():
        for v in variants:
            if v in key:
                out[ours] = key[v]
                break
    missing = [k for k in require if k not in out]
    if missing:
        raise KeyError(f"no column for {missing}; header was {header[:14]}")
    return out


# DwC-A `meta.xml` terms are full URIs (e.g.
# "http://rs.tdwg.org/dwc/terms/taxonID"); this maps the term's last path
# segment onto our own field names, parallel to FIELDS' column-text variants.
TERM_TO_FIELD = {
    "taxonID": "id",
    "parentNameUsageID": "parent",
    "scientificName": "scientific_name",
    "scientificNameAuthorship": "authorship",
    "taxonRank": "rank",
    "taxonomicStatus": "status",
    "genus": "genus",
    "specificEpithet": "species_epithet",
    "infraspecificEpithet": "infraspecific_epithet",
    "kingdom": "kingdom_name",
    "phylum": "phylum_name",
    "class": "class_name",
    "order": "order_name",
    "family": "family_name",
}


def _meta_positions(z, table):
    """Field positions for `table` from meta.xml, when meta.xml declares them.

    Two different reasons an archive needs this instead of header-text
    matching, both via the same mechanism:

    - No header row at all. A different WCVP release (2000) declares
      `ignoreHeaderLines="0"`: taxon.txt starts with data, not a header, so
      `_index`'s header-text matching finds nothing and raises on a row it
      mistook for column names. meta.xml's own `<field index="N"
      term="..."/>` declarations are the only source of the column mapping
      left.
    - A header row that's there but wrong. The 2232 WCVP release has a real
      header line (`ignoreHeaderLines="1"`) whose own text misspells the
      scientific-name column "scientfiicname" -- a typo in the archive
      itself, not a column `_index` failed to recognize. Every row still
      parsed (id, rank, classification all matched fine), so this didn't
      raise or come back empty; it silently returned a name-less taxon for
      100% of 1.4M rows, the kind of wrong answer that reads as success.
      meta.xml's own field declarations name each column by position, so
      they're correct regardless of what the header text says.

    `_rows()` therefore prefers this over header-text matching whenever
    meta.xml declares a mapping for the table at all, not only when
    `ignoreHeaderLines` is 0 -- the return value's first element tells the
    caller how many physical lines are still a header to skip, for the
    archives (like 2232) that have one on disk even though it isn't the
    column-name source. Returns None when meta.xml has no block naming
    this table, so every archive without a usable declaration keeps using
    the header-text path exactly as before.
    """
    names = z.names()
    meta_name = next((n for n in names if n.rsplit("/", 1)[-1] == "meta.xml"), None)
    if not meta_name:
        return None
    try:
        root = ET.fromstring(z.read(meta_name))
    except ET.ParseError:
        return None
    base = table.rsplit("/", 1)[-1].lower()
    for block in root:
        tag = block.tag.rsplit("}", 1)[-1]
        if tag not in ("core", "extension"):
            continue
        loc = block.find(".//{*}location")
        if loc is None or (loc.text or "").strip().lower() != base:
            continue
        try:
            ignore = int(block.get("ignoreHeaderLines", "1"))
        except ValueError:
            ignore = 1
        positions = {}
        for field in block:
            ftag = field.tag.rsplit("}", 1)[-1]
            idx = field.get("index")
            if idx is None:
                continue
            if ftag == "id":
                positions["id"] = int(idx)
            elif ftag == "field":
                term = (field.get("term") or "").rsplit("/", 1)[-1]
                if term in TERM_TO_FIELD:
                    positions.setdefault(TERM_TO_FIELD[term], int(idx))
        return ignore, positions
    return None


def _unq(v):
    """Drop one matched pair of surrounding double quotes.

    The tab-delimited sources are read with `QUOTE_NONE` above, for a real
    reason: NCBI Taxonomy (2169) has a stray literal `"` in a free-text remarks
    field, and QUOTE_MINIMAL treats it as an opening quote and merges every
    following physical line into one field until it finds a closing one.

    But the WoRMS family of ColDP exports (1039 WTaxa, 1128 Trematoda, 1193
    Turbellarians, 2302 Nemys, 1108 Brachyura, 315880 ScaleNet) *are* quoted
    TSVs -- RFC4180 quoting on a tab delimiter -- so every field arrives wrapped
    in literal quotes. That made `rank` read as `"species"` rather than
    `species`, and since nothing downstream compares ranks by equality, the
    importer reported "accepted species offered: 0" for all six and looked, to
    every reading of it, like an empty source rather than a parsing failure.

    Stripping a *matched pair* keeps the NCBI case working: its stray quote is
    not balanced, so nothing is stripped.
    """
    if len(v) > 1 and v[0] == '"' and v[-1] == '"':
        return v[1:-1].replace('""', '"')
    return v


def _rows(z, table, kind):
    try:
        probe = z.open(table)
    except KeyError:
        return None
    # Extension alone is not proof of delimiter -- Dyntaxa (2041) names its
    # single DwCA table "Taxon.csv" and it is genuinely comma-shaped per
    # iNaturalist's own precedent below, EXCEPT its header line doesn't
    # split that way: it's actually tab-delimited despite the name, the
    # same mislabelling coldp.py's load_core_csv hit on a different archive
    # (1051). Trusting ".csv" read the whole header as one cell, `_index`
    # found no column named "id", and the failure read as "this reader
    # doesn't understand this table" rather than "the extension lied".
    # Sniffed from the first physical line instead via coldp.find_delimiter
    # -- shared rather than a second copy of "count tab vs comma vs pipe",
    # so a dataset with a delimiter neither copy expected (WCVP, 2232,
    # uses pipe, declared in its own meta.xml) needs teaching only once.
    # Opened as a short-lived probe rather than sniffing off the real
    # stream, so a large file (NCBI Taxonomy, 2169, is 417MB) is
    # decompressed only as far as its first line twice, not read fully
    # into memory once.
    import coldp as _C
    with probe as f:
        first_line = f.readline().decode("utf-8-sig", "replace")
    delimiter = _C.find_delimiter(first_line)
    with z.open(table) as f:
        # Tab-delimited sources here carry no CSV-style quoting convention of
        # their own (NCBI Taxonomy, 2169, has a stray literal `"` in a
        # free-text remarks field that QUOTE_MINIMAL reads as an opening
        # quote, silently merging every following physical line into one
        # field until it finds a closing `"` -- 154,774 rows gone before the
        # field-size limit even caught it). An actual comma CSV may rely on
        # quoting to escape a comma inside a field, so only disable it for
        # tab.
        quoting = csv.QUOTE_NONE if delimiter == "\t" else csv.QUOTE_MINIMAL
        # utf-8-sig, not plain utf-8: a UTF-8 byte-order-mark on the header
        # would decode under plain utf-8 as an invisible extra character
        # glued onto the first column name. _index()/_norm() already strip
        # it via their own regex (not what originally blocked Dyntaxa --
        # the delimiter above was), but stripping it here too is strictly
        # safer and costs nothing.
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace"),
                        delimiter=delimiter, quoting=quoting)
        meta = _meta_positions(z, table)
        if meta:
            # meta.xml's own field positions win whenever meta.xml declares
            # them for this table, whether or not the file also carries a
            # header line to skip (ignoreHeaderLines count, read either
            # way) -- not only when there's no header line at all. WCVP
            # (2232) has a real header row (ignoreHeaderLines="1") whose
            # own text spells the scientific-name column "scientfiicname",
            # a typo in the archive itself that no header-text matching
            # could ever recognize; meta.xml's <field term="...
            # scientificName"/> declaration is unaffected by it, because
            # it names the column by position, not by re-reading that same
            # unreliable text. Trusting the header text here produced
            # 1.4M taxa that all parsed as real rows with a real id, rank,
            # and classification -- so every structural check downstream
            # passed -- but a silently empty name on 100% of them, the
            # kind of wrong answer that looks like success rather than
            # failure.
            ix = meta[1]
            missing = [k for k in REQUIRED[kind] if k not in ix]
            if missing:
                raise KeyError(f"no column for {missing} in {table}'s meta.xml")
            for _ in range(meta[0]):
                try:
                    next(rd)
                except StopIteration:
                    return None
        else:
            try:
                header = next(rd)
            except StopIteration:
                return None
            ix = _index(header, REQUIRED[kind])
        for row in rd:
            if len(row) > max(ix.values()):
                yield {k: _unq(row[i]) if row[i] else None for k, i in ix.items()}


def metadata(path):
    """Metadata.json or metadata.yaml, whichever exists, as a dict of scalars.

    ChecklistBank serves YAML inside a file called Metadata.json for some
    datasets, so this does not trust the extension: it tries json first and
    falls back to a flat `key: value` scan.

    Matched by basename, not full path: the GitHub-repo-style archives
    (INA/2003, ALF/294066, BioLib Coccinellidae/54592) nest every file
    under a `data-<repo>-main/` directory, so the exact name
    "metadata.yaml" is never in `c.names()` even though
    "data-ina-master/metadata.yaml" plainly is -- the same directory-
    prefix mismatch meta.xml's own location lookup and
    `_find_taxon_table()` already had to resolve.
    """
    c = _Container(path)
    try:
        raw = None
        candidates = {"metadata.json", "metadata.yaml"}
        for n in c.names():
            if n.rsplit("/", 1)[-1].lower() in candidates:
                raw = c.read(n).decode("utf-8", "replace")
                break
    finally:
        c.close()
    if raw is None:
        return {}
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return d
    except ValueError:
        pass
    out = {}
    for line in raw.splitlines():
        if not line.strip() or line[0] in " \t#-":
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip("'\"")
        if v and k.strip():
            out[k.strip()] = v
    return out


# ILDIS (ChecklistBank 1015) does not use COL's tables at all. Its export is
# AcceptedSpecies.tsv / Synonyms.tsv / CommonNames.tsv / Distribution.tsv /
# NameReferences.tsv / References.tsv / SourceDatabase.tsv -- no Taxon.tsv, no
# Name.tsv, no meta.xml. And it is the one shape whose denormalised chain columns
# are actually populated: Kingdom, Phylum, Class, Order, Family on every row,
# which is the placement chain for free with no parent walk.
ILDIS_TABLES = ("AcceptedSpecies.tsv", "Synonyms.tsv", "CommonNames.tsv",
                "Distribution.tsv", "NameReferences.tsv", "References.tsv",
                "SourceDatabase.tsv")
ILDIS_CHAIN = ("Kingdom", "Phylum", "Class", "Order", "Family")


def _ildis(z):
    """(taxa, names, meta) for the ILDIS shape, in the same shape as _col()."""
    meta = {}
    taxa = []
    with z.open("AcceptedSpecies.tsv") as f:
        rd = csv.DictReader(
            io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
            delimiter="\t")
        for r in rd:
            genus = (r.get("Genus") or "").strip()
            epithet = (r.get("SpeciesEpithet") or "").strip()
            sub = (r.get("SubGenusName") or "").strip()
            if not genus or not epithet:
                continue
            # ILDIS keeps the subgenus in its own column; COL writes it as a
            # trinomial, and importColStage2 canonical() sees both, so emit the
            # trinomial form rather than dropping the subgenus on the floor.
            name = f"{genus} {sub} {epithet}" if sub else f"{genus} {epithet}"
            t = {
                "id": r.get("AcceptedTaxonID"),
                "parent": None,
                "name_id": r.get("AcceptedTaxonID"),
                "name": name,
                "authorship": (r.get("AuthorString") or "").strip() or None,
                "rank": "species",
                "is_synonym": False,
            }
            for col in ILDIS_CHAIN:
                v = (r.get(col) or "").strip()
                if v:
                    t[f"{col.lower()}_name"] = v
            taxa.append(t)
    for t in taxa:
        meta = meta  # metadata.yaml is absent in this shape; keep the contract
    return taxa, {}, meta


# EUNIS (ChecklistBank 2122) is a third denormalised shape, in the same
# spirit as ILDIS but split across two joined files instead of one:
# taxons.tsv (plural -- not `Taxon.tsv`, so `load()` dispatches on it before
# the generic TAXON_TABLES check ever runs) is the accepted-species register,
# one row per species with family/order/class/phylum/kingdom as flat columns
# rather than parent rows to walk, and nameID joining to names.tsv for the
# scientificName, authorship and rank. No Metadata.json ships in this export.
EUNIS_TABLES = ("taxons.tsv", "names.tsv")
EUNIS_CHAIN = ("family", "order", "class", "phylum", "kingdom")


def _eunis(z):
    """(taxa, names, meta) for the EUNIS shape, in the same shape as _col()."""
    names = {}
    with z.open("names.tsv") as f:
        rd = csv.DictReader(
            io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
            delimiter="\t")
        for r in rd:
            names[r.get("ID")] = {
                "name": (r.get("scientificName") or "").strip(),
                "authorship": (r.get("authorship") or "").strip() or None,
                "rank": (r.get("rank") or "").strip().lower(),
            }
    taxa = []
    with z.open("taxons.tsv") as f:
        rd = csv.DictReader(
            io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
            delimiter="\t")
        for r in rd:
            n = names.get(r.get("nameID")) or {}
            if not n.get("name"):
                continue
            t = {
                "id": r.get("ID"), "parent": None, "name_id": r.get("nameID"),
                "name": n["name"], "authorship": n.get("authorship"),
                "rank": n.get("rank") or "species", "is_synonym": False,
            }
            for col in EUNIS_CHAIN:
                v = (r.get(col) or "").strip()
                if v:
                    t[f"{col}_name"] = v
            taxa.append(t)
    return taxa, {}, {}


def _ancestors(par, tid, limit=200):
    out, c, n, seen = [], tid, 0, set()
    while c and n < limit and c not in seen:
        seen.add(c)
        out.append(c)
        p_ = par.get(c)
        if not p_ or p_ == c:
            break
        c = p_
        n += 1
    return out


def _coldp(path):
    """ColDP, via scripts/coldp.py -- one NameUsage.tsv instead of a table split.

    Wikispecies (314570) arrives this way, as the Wikidata Species dataset beside
    it does, so a reader knowing only the COL export shape would decline the two
    largest sources on the shelf. Accepted-ness comes from col:status, which is
    the field ColDP uses -- the opposite of the COL export shape, where status
    is empty and Synonym.tsv carries the split.

    Blank is also itself a valid accepted-ness value, not just a thing Wikispecies
    and Wikidata Species happen not to do. NameUsage.status "includes ... the
    Taxon.provisional flag" per the ColDP spec, and that flag defaults to false --
    a plain accepted taxon writes nothing, "provisionally accepted" only for the
    exception. The Mammal Diversity Database (9802) does exactly that: 41,686 of
    its rows are blank-status accepted taxa and 1 is literally "provisionally
    accepted"; none of the 50,800 synonym rows are blank. Omitting "" here filtered
    every real taxon out and kept only the synonyms, so the import reported 0
    candidates for a dataset that is nothing but mammals.
    """
    import coldp as _C
    # Load the WHOLE name usage set, not the accepted subset, because a chain
    # legitimately runs through names that are not themselves accepted -- a genus
    # can be a synonym and still be the parent of accepted species. Indexing
    # only accepted taxa (the first attempt) made chain() dead-end and every
    # species came back "no family": all 78,731 of Wikispecies' new species,
    # which would have refused the lot. Status decides who is a *candidate*, not
    # who may appear in a hierarchy.
    par, rank, name, extra = _C.load_core(
        path, accepted=_C.ACCEPTED | {"", "synonym", "ambiguous synonym",
                                     "misapplied", "unplaced", "excluded"},
        want_authorship=True)
    by_id = {}
    for t, r in rank.items():
        e = extra.get(t) or {}
        row = {"id": t, "parent": par.get(t), "name_id": t,
               "name": name.get(t), "authorship": e.get("authorship"),
               "rank": r,
               # Blank is the ordinary accepted case here too, same reason
               # as the load_core() filter above -- not just "not excluded".
               "is_synonym": (e.get("status") or "").strip().lower() not in _C.ACCEPTED and
                             (e.get("status") or "").strip() != "",
               "status": e.get("status")}
        # Flat kingdom_name/.../family_name columns, when load_core() found
        # them (col:parentID blank -- MDD -- or just not walked that far).
        # Named to match CHAIN_COL exactly, so chain()'s own denormalised-
        # column fallback reads them with no extra translation.
        for rnk in ("kingdom", "phylum", "class", "order", "family"):
            v = e.get(f"{rnk}_name")
            if v:
                row[f"{rnk}_name"] = v
        by_id[t] = row
    # The WHOLE hierarchy, not just the species: the importer builds its
    # parent-walk index from this list, so returning only species meant
    # by_id.get("Homo") was None and the walk stopped one step above the species
    # with no family found. Candidates are selected downstream by rank, so
    # carrying genera and families here costs nothing and makes the chain
    # walkable.
    return list(by_id.values()), {}, _C.metadata(path)


def _taxa_cache_path(path):
    """Sidecar parquet next to the archive -- same directory, so it travels
    with the archive rather than living in a separate cache tree."""
    base, _ = os.path.splitext(path)
    return base + ".taxa-cache.parquet"


def _write_taxa_cache(taxa, cache_path):
    """Dump `taxa` (a list of dicts with heterogeneous optional keys -- not
    every row carries every rank's `<rank>_name`) to a parquet sidecar via
    duckdb's read_json_auto, which infers one wide schema from the union of
    keys across all rows. Raises on any failure; the caller decides whether
    a cache write failure should stop the import (it shouldn't).

    Writes to a `.tmp` sibling first and renames onto `cache_path` only on
    success. Found 2026-10-23 on the GBIF Backbone (millions of taxa, far
    bigger than anything this was tested against): the COPY failed
    silently partway through (never diagnosed -- not disk space, the
    archive and its cache share a volume with 1.5TB free; likely a duckdb
    memory ceiling on a JSON file that size) and left a 0-byte file at
    `cache_path` that then passed the next run's "newer than the archive"
    freshness check and would have been trusted as an empty-but-valid
    cache had `load_cached` not also started checking size."""
    import duckdb
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".jsonl", dir=os.path.dirname(cache_path) or ".")
    tmp_out = cache_path + ".tmp"
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for t in taxa:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        con = duckdb.connect()
        con.execute(
            f"COPY (SELECT * FROM read_json_auto({tmp!r})) "
            f"TO {tmp_out!r} (FORMAT PARQUET)")
        os.replace(tmp_out, cache_path)
    finally:
        os.unlink(tmp)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)


def _read_taxa_cache(cache_path):
    """-> taxa, reversing _write_taxa_cache. duckdb pads every row to the
    union schema with NULLs for keys that row didn't have; drop those back
    out so a cached taxon dict looks exactly like a freshly-parsed one (the
    importer's `.get('authorship')` etc. expect a missing key, not a
    present-but-None one -- same contract either way, but this avoids ever
    finding out the hard way that they differ)."""
    import duckdb
    con = duckdb.connect()
    rel = con.sql(f"SELECT * FROM read_parquet({cache_path!r})")
    cols = rel.columns
    return [{c: v for c, v in zip(cols, row) if v is not None}
            for row in rel.fetchall()]


def load_cached(path):
    """Same contract as load(), except taxa comes from a parquet sidecar
    when one is fresh (newer than the archive itself) rather than re-parsing
    the archive's actual tables every time.

    Built for the pending-family watcher: it re-runs `importColChecklist.py
    <archive> --apply` on every cycle an archive has newly-ready families,
    and for something the size of the GBIF Backbone that means re-walking
    the whole archive again and again to place a shrinking sliver of
    still-unplaceable species -- most of each re-parse is thrown straight
    back out by the importer's own already-held dedup. names/meta are not
    cached: every caller of load() already discards them (`_names`/`_` at
    every call site but one, which calls load() directly instead of this).

    duckdb is optional -- see buildSpeciesParquet.py's own note -- so this
    degrades to a plain load() with no caching, not a hard failure, when
    it's missing."""
    try:
        import duckdb  # noqa: F401
    except ImportError:
        return load(path)
    cache_path = _taxa_cache_path(path)
    if (os.path.exists(cache_path)
            and os.path.getsize(cache_path) > 0
            and os.path.getmtime(cache_path) >= os.path.getmtime(path)):
        try:
            return _read_taxa_cache(cache_path), {}, {}
        except Exception as e:
            print(f"  (taxa cache unreadable, re-parsing: {e})")
    taxa, names, meta = load(path)
    try:
        _write_taxa_cache(taxa, cache_path)
    except Exception as e:
        print(f"  (taxa cache write skipped: {e})")
    return taxa, names, meta


def load(path):
    """-> (taxa, names, meta), whatever serialisation the archive uses.

    taxa: [{'id','parent','name_id','name','authorship','rank','is_synonym',
            '<rank>_name': ...}]
    names: {name_id: {'name','authorship','rank'}}

    Three shapes reach this function and all three come out identical, so the
    importer downstream has one path rather than three.
    """
    c = _Container(path)
    try:
        if "AcceptedSpecies.tsv" in c.names():
            return _ildis(c)
        if all(t in c.names() for t in EUNIS_TABLES):
            return _eunis(c)
        basenames = {m.rsplit("/", 1)[-1].lower() for m in c.namelist()}
        has_taxon_csv = "taxon.csv" in basenames
        has_name_csv = "name.csv" in basenames
        import coldp as _C
        if _C.find_core_table(c.names()) or (has_taxon_csv and has_name_csv):
            # ColDP arrives in two serialisations: one single-table core
            # (COL's own "NameUsage.tsv", or a lowercase/underscore/other-
            # extension spelling of it -- nameusage.csv, name_usage.txt --
            # found via coldp.find_core_table rather than the literal
            # "NameUsage.tsv" string, so the dispatch doesn't drift from
            # coldp.py's own idea of what counts as this table, the same
            # divergence-across-copies failure familyPath.ts's own history
            # warns about), or a name/taxon/synonym CSV split (GLI). All go
            # through coldp.py, which reads each; dispatching only on the
            # exact TSV name made the CSV flavour fall through to the DwCA
            # path, find no `name.tsv`, and report an empty dataset.
            # `has_name_csv` is required alongside `has_taxon_csv` because a
            # `taxon.csv` alone is not proof of the split -- Dyntaxa (2041)
            # ships a single-table DwCA that happens to use `.csv` instead
            # of `.txt`/`.tsv`, no name table in sight, and matching on
            # taxon.csv alone sent it into `_coldp`, which failed outright
            # looking for a name table that was never going to exist (it
            # goes through the generic DwCA path below instead, correctly).
            # Exact basenames, not `endswith` -- Dyntaxa's own
            # `VernacularName.csv` ends with "name.csv" too, which the first
            # version of this fix matched and made no difference at all.
            return _coldp(path)
        names = {}
        t = _find(c, "name")
        if t:
            for r in _rows(c, t, "name"):
                names[r["id"]] = {"name": r.get("scientific_name"),
                                  "authorship": r.get("authorship"),
                                  "rank": r.get("rank")}
        synonym_ids = set()
        t = _find(c, "synonym")
        if t:
            for r in _rows(c, t, "synonym"):
                if r.get("name_id"):
                    synonym_ids.add(r["name_id"])
        taxa = []
        t = _find_taxon_table(c)
        if t:
            for r in _rows(c, t, "taxon"):
                    n = names.get(r.get("name_id"), {}) if r.get("name_id") else {}
                    # LCVP (no Name.tsv, no Synonym.tsv) carries scientificName,
                    # rank, authorship and taxonomicStatus directly on the row
                    # instead -- the `or r.get(...)` fallbacks are that shape;
                    # `n` wins where both exist because that was true already.
                    status = r.get("status")
                    row = {
                        "id": r["id"],
                        "parent": r.get("parent"),
                        "name_id": r.get("name_id"),
                        "name": r.get("name_phrase") or n.get("name")
                                or r.get("scientific_name"),
                        "authorship": n.get("authorship") or r.get("authorship"),
                        "rank": RANK_SYNONYMS.get(
                            ((r.get("rank") or n.get("rank")) or "").lower(),
                            r.get("rank") or n.get("rank")),
                        "is_synonym": (
                            status.strip().lower() not in ACCEPTED_STATUS
                            if status else r.get("name_id") in synonym_ids),
                    }
                    for rnk, col in CHAIN_COL.items():
                        v = r.get(col)
                        if v:
                            row[col] = v
                    taxa.append(row)
        # COL China (312616) carries no rank column anywhere -- not on the
        # taxon row, not on a joined name -- despite its own metadata
        # describing every row as "spp & infraspecific taxa" by scope. Every
        # row coming back rank=None reads as "nothing here is a species"
        # rather than "this export doesn't say", the same kind of silent
        # failure GLI's CSV flavour and the EUNIS/Nortaxa `.txt` tables
        # produced before each got its own fix. Inferred only when NO row in
        # the whole table carries a rank anywhere -- a dataset that states
        # ranks for some taxa and omits them for others is a data gap to
        # leave alone, not a shape to paper over -- and only for rows that
        # already look like a binomial under a family we can place, which is
        # what a species row looks like in this shape.
        if taxa and not any(t.get("rank") for t in taxa):
            for row in taxa:
                nm = row.get("name") or ""
                if " " in nm and row.get("family_name"):
                    row["rank"] = "species"
    finally:
        c.close()
    return taxa, names, metadata(path)




def chain(tax, by_id, ranks=("kingdom", "phylum", "class", "order", "family"),
          limit=200):
    """taxon -> {rank: name}, first match walking upward.

    Falls back to the taxon row's own denormalised chain columns only if the
    parent walk finds nothing, which for both archives it does -- reptile-db's
    `family_name` is empty on all 17,042 rows, so trusting it would place
    nothing at all.

    Also sets `{rank}_id` to the archive's own id for that ancestor row,
    whenever the match came from walking to a real ancestor taxon rather than
    a denormalised column -- a flat `family_name` string on the species row
    has no taxon of its own to carry an id. This is the source's bare local
    id (whatever `cur["id"]` means in that archive, e.g. a COL/ChecklistBank
    usage id), not a cross-source authority id; nothing has reconciled it
    against any other archive's numbering.
    """
    out = {}
    cur, n = tax, 0
    while cur is not None and n < limit:
        crank = (cur.get("rank") or "").lower()
        crank = RANK_SYNONYMS.get(crank, crank)
        for rnk in ranks:
            if rnk in out:
                continue
            # the taxon row's own denormalised column first, then its name when
            # its rank is the one we want. reptile-db leaves family_name empty on
            # all 17,042 rows, so the second path is the one that does the work.
            v = cur.get(CHAIN_COL[rnk])
            denormalised = bool(v)
            if not v and crank in (rnk, f"{rnk}group"):
                v = cur.get("name")
            if v:
                v = re.sub(r"\s+", " ", str(v)).strip()
                # A rank above species is one word in real nomenclature, so a
                # second word is authorship riding along on `scientificName`
                # per plain Darwin Core convention -- "Curculionidae
                # Latreille, 1802" (the Brazilian Fauna catalogue writes every
                # rank this way) -- not part of the name. Denormalised chain
                # columns (ILDIS, EUNIS) are already bare and skip this.
                if not denormalised and " " in v:
                    v = v.split()[0]
                out[rnk] = v
                if not denormalised and cur.get("id"):
                    out[f"{rnk}_id"] = cur["id"]
        cur = by_id.get(cur.get("parent")) if cur.get("parent") else None
        n += 1
    return out


if __name__ == "__main__":
    import collections
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: colChecklist.py <archive.zip>")
    p = sys.argv[1]
    md = metadata(p)
    print(json.dumps({k: md.get(k) for k in
                      ("key", "title", "alias", "doi", "version", "issued",
                       "license")}, indent=1, ensure_ascii=False))
    taxa, names, _ = load(p)
    by_id = {t["id"]: t for t in taxa}
    ranks = collections.Counter(t["rank"] for t in taxa)
    syn = sum(1 for t in taxa if t["is_synonym"])
    print(f"  taxa: {len(taxa):,}   names: {len(names):,}   "
          f"synonym rows among taxa: {syn:,}")
    print("  ranks: " + ", ".join(f"{k}={v:,}" for k, v in ranks.most_common(9)))
    spp = [t for t in taxa if (t["rank"] or "").lower() in ("species", "subspecies")
           and not t["is_synonym"]]
    print(f"  accepted species+subspecies: {len(spp):,}")
    fam = collections.Counter()
    for t in spp[:20000]:
        c = chain(t, by_id)
        fam[c.get("family") or "(unresolved)"] += 1
    print(f"  families among the first 20,000: {len(fam):,}")
    for k, v in fam.most_common(8):
        print(f"    {v:>6,}  {k}")