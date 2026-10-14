#!/usr/bin/env python3
"""Convert COL China 2025 Annual Checklist (ChecklistBank 312616) into a ColDP
NameUsage.tsv that importColChecklist can ingest.

Why a converter: this export is a plain DwCA (taxon.txt + meta.xml + eml.xml,
no Name.tsv), which is a shape colChecklist._col() reads -- but it has no rank
column at all. Every row came back rank=None through colChecklist.py, which is
why the source was marked "not importable through the normal path yet" in
scripts/sourcesManifest.py.

So this infers rank from the shape of the name, which is what the data
actually carries:

  * name == genus (or a single word)        -> genus
  * binomial whose first word is the genus -> species
  * anything else (family/order/etc.)      -> the rank implied by which chain
    column is populated, falling back to "unranked"

That last bucket is the one that matters. The source's own chain columns
(kingdom, phylum, class, order, family) are filled on every row, so a family
name is identifiable by `name == family` and an order by `name == order`. The
manifest's hand-rolled check against taxaserve found 148,081 distinct names;
this does the same job structurally so the importer can place them.

Status is honoured: only `Accepted` rows are candidates, synonyms are carried
through as-is so chain() can walk through them (same reasoning as
colChecklist._col()).

    python3 scripts/colchinaToColDP.py            # dry run, prints summary
    python3 scripts/colchinaToColDP.py --apply    # writes archives/colchina/NameUsage.tsv
"""
import argparse
import csv
import io
import os
import sys
import tarfile
import zipfile

ARCHIVE = "/Volumes/MacieExternal/sources/archives/checklistbank-312616/archive.zip"
OUT = "archives/colchina/NameUsage.tsv"

CHAIN = ("kingdom", "phylum", "class", "order", "family")


def open_archive(path):
    """zip or gzip'd tar; the endpoint is named archive.zip and GloBIS/ILDIS
    answer with a tar, so the magic decides rather than the extension."""
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic == b"PK":
        return zipfile.ZipFile(path)
    if magic == b"\x1f\x8b":
        return tarfile.open(path, "r:gz")
    raise ValueError(f"{path}: not a zip or gzip (magic {magic!r})")


def read_tsv(z, member):
    raw = z.open(member) if hasattr(z, "open") else z.extractfile(member)
    f = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
    rd = csv.reader(f, delimiter="\t")
    hdr = [h.strip() for h in next(rd)]
    return hdr, rd


def cell(row, ix, k):
    i = ix.get(k, -1)
    return (row[i] or "").strip() if i >= 0 and len(row) > i else ""


def infer_rank(row, ix):
    name = (row[ix["scientificName"]] or "").strip()
    genus = (row[ix["genus"]] or "").strip()
    parts = name.split()
    if len(parts) == 1 or (genus and name == genus):
        return "genus"
    if len(parts) == 2 and genus and parts[0] == genus:
        return "species"
    for r in ("family", "order", "class", "phylum"):
        v = cell(row, ix, r)
        if v and name == v:
            return r
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    z = open_archive(args.archive)
    hdr, rd = read_tsv(z, "taxon.txt")
    ix = {h: i for i, h in enumerate(hdr)}

    cols = ["ID", "parentID", "scientificName", "rank", "status"] + list(CHAIN)
    rows = []
    from collections import Counter
    ranks = Counter()
    n = 0
    for row in rd:
        if len(row) <= ix["scientificName"]:
            continue
        name = (row[ix["scientificName"]] or "").strip()
        if not name:
            continue
        tid = cell(row, ix, "id") or cell(row, ix, "taxonID")
        parent = cell(row, ix, "acceptedNameUsageID")
        status = cell(row, ix, "taxonomicStatus")
        rank = infer_rank(row, ix)
        ranks[rank or "unranked"] += 1
        chain = {r: cell(row, ix, r) for r in CHAIN if r in ix}
        rows.append({
            "ID": tid, "parentID": parent, "scientificName": name,
            "rank": rank, "status": status, **chain,
        })
        n += 1

    print(f"rows            {n:,}")
    for r, c in ranks.most_common():
        print(f"  {r or 'unranked':<12}{c:>10,}")

    if not args.apply:
        print("\n  (dry run -- pass --apply to write)")
        return 0

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])
    print(f"\n  wrote {args.out} ({os.path.getsize(args.out)/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())