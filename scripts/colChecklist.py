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
import zipfile

# accepted-name handling: synonyms are named here, not flagged on the name
SYN_TABLES = ("Synonym.tsv", "synonym.tsv")
NAME_TABLES = ("Name.tsv", "name.tsv")
TAXON_TABLES = ("Taxon.tsv", "taxon.tsv")

# our name -> the variants seen in the wild
FIELDS = {
    "id": ("id",),
    "parent": ("parentid",),
    "name_id": ("nameid",),
    "name_phrase": ("namephrase",),
    "scientific_name": ("scientificname",),
    "authorship": ("authorship", "authorshipstring"),
    "rank": ("rank",),
    "genus": ("genus",),
    "species_epithet": ("speificepithet",),
    "infraspecific_epithet": ("infrspecificepithet", "infraspepithet",
                              "infraspecificepithet"),
    "kingdom_name": ("kingdomname",),
    "phylum_name": ("phylumname",),
    "class_name": ("classname",),
    "order_name": ("ordername",),
    "family_name": ("familyname",),
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
    "taxon": ("id", "parent", "name_id"),
}


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


def _rows(z, table, kind):
    try:
        fh = z.open(table)
    except KeyError:
        return None
    with fh as f:
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                        delimiter="\t")
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
        path, accepted=_C.ACCEPTED | {"synonym", "ambiguous synonym",
                                     "misapplied", "unplaced", "excluded"},
        want_authorship=True)
    by_id = {}
    for t, r in rank.items():
        e = extra.get(t) or {}
        by_id[t] = {"id": t, "parent": par.get(t), "name_id": t,
                    "name": name.get(t), "authorship": e.get("authorship"),
                    "rank": r, "is_synonym": (e.get("status") or "") not in _C.ACCEPTED,
                    "status": e.get("status")}
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
        if "NameUsage.tsv" in c.names():
            return _coldp(path)
        names = {}
        for t in NAME_TABLES:
            if t in c.namelist():
                for r in _rows(c, t, "name"):
                    names[r["id"]] = {"name": r.get("scientific_name"),
                                      "authorship": r.get("authorship"),
                                      "rank": r.get("rank")}
                break
        synonym_ids = set()
        for t in SYN_TABLES:
            if t in c.namelist():
                for r in _rows(c, t, "synonym"):
                    if r.get("name_id"):
                        synonym_ids.add(r["name_id"])
                break
        taxa = []
        for t in TAXON_TABLES:
            if t in c.namelist():
                for r in _rows(c, t, "taxon"):
                    n = names.get(r["name_id"], {})
                    row = {
                        "id": r["id"],
                        "parent": r.get("parent"),
                        "name_id": r.get("name_id"),
                        "name": r.get("name_phrase") or n.get("name"),
                        "authorship": n.get("authorship"),
                        "rank": r.get("rank") or n.get("rank"),
                        "is_synonym": r.get("name_id") in synonym_ids,
                    }
                    for rnk, col in CHAIN_COL.items():
                        v = r.get(col)
                        if v:
                            row[col] = v
                    taxa.append(row)
                break
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
    """
    out = {}
    cur, n = tax, 0
    while cur is not None and n < limit:
        crank = (cur.get("rank") or "").lower()
        for rnk in ranks:
            if rnk in out:
                continue
            # the taxon row's own denormalised column first, then its name when
            # its rank is the one we want. reptile-db leaves family_name empty on
            # all 17,042 rows, so the second path is the one that does the work.
            v = cur.get(CHAIN_COL[rnk])
            if not v and crank in (rnk, f"{rnk}group"):
                v = cur.get("name")
            if v:
                out[rnk] = re.sub(r"\s+", " ", str(v)).strip()
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