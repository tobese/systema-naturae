#!/usr/bin/env python3
"""LPSN's download (lpsn_gss_<date>.csv) as a ColDP names index, for the
nomenclatural track (nomenclatureTransform.py, code "LPSN").

LPSN (lpsn.dsmz.de, CC BY-SA 4.0) is the register of prokaryote names: per
name the authorship ("Tahon et al. 2018"), whether it is validly published
under the ICNP, whether it is the correct name or a synonym (with the
record of the correct name), type strains and the publication. Its download
is one CSV, which this writes as Name.tsv + NameRelation.tsv + metadata.yaml
(alias LPSN) in a zip beside it.

Taken: validly published species (VP/VL), correct names and synonyms.
Left out: subspecies (the track is species-level), genera, and names LPSN
flags as inaccurate spellings. Attribution: CC BY-SA 4.0, cite LPSN's latest
reference with the access date, and link each record's LPSN page -- which
`link` (the record's address) keeps.

    python3 scripts/lpsnToColdp.py <sources>/archives/lpsn/lpsn_gss_2026-11-01.csv
"""
import csv
import io
import os
import re
import sys
import zipfile

YEAR = re.compile(r"(\d{4})\s*$")


def main() -> int:
    src = sys.argv[1]
    out = os.path.join(os.path.dirname(src), "lpsn-coldp.zip")
    issued = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(src))
    with open(src, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    names, rels, kept, skipped = [], [], set(), 0
    for r in rows:
        status = r.get("status") or ""
        if not r.get("sp_epithet") or r.get("subsp_epithet"):
            continue
        if "validly published under the ICNP" not in status or "inaccurate spelling" in status:
            skipped += 1
            continue
        nid = r["record_no"]
        auth = (r.get("authors") or "").strip()
        y = YEAR.search(auth)
        names.append({"ID": nid, "rank": "species",
                      "scientificName": f"{r['genus_name']} {r['sp_epithet']}",
                      "authorship": auth, "publishedInYear": y.group(1) if y else "",
                      "status": status, "link": r.get("address") or ""})
        kept.add(nid)
        if "synonym" in status and r.get("record_lnk"):
            rels.append({"nameID": nid, "relatedNameID": r["record_lnk"], "type": "SYNONYM"})
    rels = [x for x in rels if x["relatedNameID"] in kept]

    def tsv(rows, cols):
        buf = io.StringIO()
        w = csv.DictWriter(buf, cols, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE,
                           escapechar="\\")
        w.writeheader()
        for row in rows:
            w.writerow({c: (row.get(c) or "").replace("\t", " ") for c in cols})
        return buf.getvalue()

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("metadata.yaml",
                   "alias: LPSN\ntitle: List of Prokaryotic names with Standing in Nomenclature\n"
                   f"issued: {issued.group(1) if issued else ''}\nlicense: CC BY-SA 4.0\n"
                   "url: https://lpsn.dsmz.de\n")
        z.writestr("Name.tsv", tsv(names, ["ID", "rank", "scientificName", "authorship",
                                           "publishedInYear", "status", "link"]))
        z.writestr("NameRelation.tsv", tsv(rels, ["nameID", "relatedNameID", "type"]))
    print(f"  {len(names):,} species names, {len(rels):,} synonym relations, "
          f"{skipped:,} not validly published or misspelt -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
