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
    h = h[4:] if h.startswith("col:") else h
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
    """Field positions for `table` from meta.xml, when the file has no header row.

    WCVP (2000) declares `ignoreHeaderLines="0"` in meta.xml: taxon.txt starts
    with data, not a header, so the header-text matching `_index` normally
    does finds nothing and raises on a row it mistook for column names. A DwCA
    with ignoreHeaderLines="0" has no header to match -- its field order is
    only ever recoverable from meta.xml's own <field index="N" term="..."/>
    declarations, so that is the one shape this reads positionally; every
    other archive keeps using the proven header-text path unchanged.
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


def _rows(z, table, kind):
    try:
        fh = z.open(table)
    except KeyError:
        return None
    with fh as f:
        # iNaturalist (139831) names its taxon table `taxa.csv` -- an actual
        # comma-delimited CSV, not the tab-delimited .txt/.tsv every other
        # DwCA/ColDP source here uses regardless of its own extension. Reading
        # it as tab-delimited put the whole header in one cell, so `_index`
        # found no column named "id" and raised on a file that plainly has one.
        delimiter = "," if table.lower().endswith(".csv") else "\t"
        # Tab-delimited sources here carry no CSV-style quoting convention of
        # their own (NCBI Taxonomy, 2169, has a stray literal `"` in a
        # free-text remarks field that QUOTE_MINIMAL reads as an opening
        # quote, silently merging every following physical line into one
        # field until it finds a closing `"` -- 154,774 rows gone before the
        # field-size limit even caught it). An actual comma CSV may rely on
        # quoting to escape a comma inside a field, so only disable it for
        # tab.
        quoting = csv.QUOTE_NONE if delimiter == "\t" else csv.QUOTE_MINIMAL
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                        delimiter=delimiter, quoting=quoting)
        meta = _meta_positions(z, table)
        if meta and meta[0] == 0:
            # No header line to read or skip -- meta.xml's own field positions
            # are the only source of the column mapping (see _meta_positions).
            ix = meta[1]
            missing = [k for k in REQUIRED[kind] if k not in ix]
            if missing:
                raise KeyError(f"no column for {missing} in {table}'s meta.xml")
        else:
            try:
                header = next(rd)
            except StopIteration:
                return None
            ix = _index(header, REQUIRED[kind])
        for row in rd:
            if len(row) > max(ix.values()):
                yield {k: (row[i] if row[i] else None) for k, i in ix.items()}


def metadata(path):
    """Metadata.json or metadata.yaml, whichever exists, as a dict of scalars.

    ChecklistBank serves YAML inside a file called Metadata.json for some
    datasets, so this does not trust the extension: it tries json first and
    falls back to a flat `key: value` scan.
    """
    c = _Container(path)
    try:
        raw = None
        for cand in ("Metadata.json", "metadata.yaml", "metadata.json"):
            if cand in c.names():
                raw = c.read(cand).decode("utf-8", "replace")
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
               "is_synonym": e.get("status") not in _C.ACCEPTED and
                             e.get("status") != "",
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
        if "NameUsage.tsv" in c.names() or (has_taxon_csv and has_name_csv):
            # ColDP arrives in two serialisations: one NameUsage.tsv, or a
            # name/taxon/synonym CSV split (GLI). Both go through coldp.py,
            # which reads each; dispatching only on the TSV made the CSV flavour
            # fall through to the DwCA path, find no `name.tsv`, and report an
            # empty dataset. `has_name_csv` is required alongside
            # `has_taxon_csv` because a `taxon.csv` alone is not proof of the
            # split -- Dyntaxa (2041) ships a single-table DwCA that happens to
            # use `.csv` instead of `.txt`/`.tsv`, no name table in sight, and
            # matching on taxon.csv alone sent it into `_coldp`, which failed
            # outright looking for a name table that was never going to exist.
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
        t = _find(c, "taxon", "taxa")
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