#!/usr/bin/env python3
"""Convert a GloBIS (Global Butterfly Information System, ChecklistBank 1046)
archive into a ColDP NameUsage.tsv that importColChecklist can ingest.

Why a converter rather than a reader: GloBIS is not one of the three shapes
archiveOverlap.py reads. It is a flat species table -- AcceptedSpecies.tsv
(Kingdom/Phylum/.../Genus/SpeciesEpithet, no parentID, no status column, every
row accepted by construction) plus AcceptedInfraspecificTaxa.tsv, which links
to it by parentID. That is simpler than a DwCA, not harder; what is missing is
the parent/accepted scaffolding importColChecklist expects.

So this writes the scaffolding. Each AcceptedSpecies row becomes one NameUsage
row at SPECIES rank with its taxonomic chain as parent links, and each
InfraspecificTaxa row becomes one row at the infra rank whose parentID points
at its species. importColChecklist then measures overlap against the tree and
adds what is missing to the families we already hold -- Lycaenidae,
Papilionidae and Pieridae, all three of which it covers and all three of which
we hold.

Columns are quoted in the source; the writer quotes everything, which is what
importColChecklist's reader expects (it strips col: prefixes and folds case,
so quoting is harmless).

    python3 scripts/globisToColDP.py            # dry run, prints summary
    python3 scripts/globisToColDP.py --apply    # writes archives/globis/NameUsage.tsv
"""
import argparse
import csv
import io
import os
import sys
import tarfile

ARCHIVE = "/Volumes/MacieExternal/sources/archives/checklistbank-1046/archive.zip"
OUT = "archives/globis/NameUsage.tsv"

RANKS = ["kingdom", "phylum", "class", "order", "superfamily", "family",
         "genus", "subgenus"]


def read_tsv(z, member):
    import io
    f = io.TextIOWrapper(z.extractfile(member), encoding="utf-8",
                         errors="replace")
    rd = csv.reader(f, delimiter="\t", quotechar='"')
    hdr = [h.strip().strip('"') for h in next(rd)]
    return hdr, rd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    z = tarfile.open(args.archive, "r:gz")
    members = z.getnames()
    sp_hdr, sp_rd = read_tsv(z, "AcceptedSpecies.tsv")
    inf_hdr, inf_rd = read_tsv(z, "AcceptedInfraspecificTaxa.tsv")

    sp = {h: i for i, h in enumerate(sp_hdr)}
    inf = {h: i for i, h in enumerate(inf_hdr)}

    rows = []
    idcol, parentcol = "AcceptedTaxonID", "parentID"
    n_species = n_infra = 0

    species_by_id = {}
    for row in sp_rd:
        if len(row) <= sp["SpeciesEpithet"]:
            continue
        genus = (row[sp["Genus"]] or "").strip().strip('"')
        epi = (row[sp["SpeciesEpithet"]] or "").strip().strip('"')
        if not genus or not epi:
            continue
        chain = {h: (row[sp[h]] or "").strip().strip('"')
                 for h in RANKS if h in sp}
        name = f"{genus} {epi}"
        species_by_id[row[sp[idcol]].strip().strip('"')] = (name, chain.get("family", ""))
        rows.append({
            "ID": row[sp[idcol]].strip().strip('"'),
            "parentID": chain.get("family", ""),
            "scientificName": name,
            "rank": "species",
            "status": "accepted",
            **{h: v for h, v in chain.items() if h != "family"},
        })
        n_species += 1

    for row in inf_rd:
        if len(row) <= inf["InfraSpeciesEpithet"]:
            continue
        epi = (row[inf["InfraSpeciesEpithet"]] or "").strip().strip('"')
        if not epi:
            continue
        parent = row[inf[parentcol]].strip().strip('"')
        sp_name, sp_fam = species_by_id.get(parent, ("", ""))
        if not sp_name:
            continue
        rows.append({
            "ID": row[inf[idcol]].strip().strip('"'),
            "parentID": parent,
            "scientificName": f"{sp_name} {epi}",
            "rank": "subspecies",
            "status": "accepted",
            "family": sp_fam,
        })
        n_infra += 1

    cols = ["ID", "parentID", "scientificName", "rank", "status"] + RANKS
    print(f"species rows   {n_species:,}")
    print(f"infraspecific  {n_infra:,}")
    print(f"total          {len(rows):,}")

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