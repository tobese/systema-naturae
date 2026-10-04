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
    with zipfile.ZipFile(path) as z:
        raw = None
        for cand in ("Metadata.json", "metadata.yaml", "metadata.json"):
            try:
                raw = z.read(cand).decode("utf-8", "replace")
                break
            except KeyError:
                continue
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


def load(path):
    """-> (taxa, names, meta).

    taxa: [{'id','parent','name_id','name','authorship','rank','chain'}]
    names: {name_id: {'name','authorship','rank'}}
    """
    with zipfile.ZipFile(path) as z:
        names = {}
        for t in NAME_TABLES:
            if t in z.namelist():
                for r in _rows(z, t, "name"):
                    names[r["id"]] = {"name": r.get("scientific_name"),
                                      "authorship": r.get("authorship"),
                                      "rank": r.get("rank")}
                break
        synonym_ids = set()
        for t in SYN_TABLES:
            if t in z.namelist():
                for r in _rows(z, t, "synonym"):
                    if r.get("name_id"):
                        synonym_ids.add(r["name_id"])
                break
        taxa = []
        for t in TAXON_TABLES:
            if t in z.namelist():
                for r in _rows(z, t, "taxon"):
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