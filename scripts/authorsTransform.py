#!/usr/bin/env python3
"""Authors track, transform: people and species -> author links from a source
whose names point at its own author table (docs/authors-track-plan.md).

A ColDP archive is on the track when it has an `Author` table *and* its
names reference it through `combinationAuthorshipID` / `basionymAuthorshipID`.
The pointer is the test: PBDB (1174) ships an `Author.tsv` that lists its
data enterers, and no name points at it. Today one source passes: Wikidata
Species (ChecklistBank 314569, `ac5f72cf-…`), 56,034 people and 1,037,047
species with author ids.

Writes to <sources>/work/<slug>-authors/:

  people.jsonl          one person per row: the source's id, names,
                        botanical abbreviation, life dates, country, and
                        every alternative id (orcid:, ipni:, zoobank: …).
                        Only people a written link points at.
  links.jsonl           applyEnrichment.py records: `authorIds` (and
                        `basionymAuthorIds`) on a held species. Written only
                        when the species is held once in its kingdom and the
                        source's authorship names the same authors as ours
                        (taxamatch.same_authorship with authorNames'
                        same_person), so an id never lands on another
                        person's name. Where we hold no authorship, the
                        source's is filled with the ids.
  review-authors.jsonl  authorships that disagree; nothing written.
  summary.json

    python3 scripts/authorsTransform.py <archive.zip> <slug>            # measure
    python3 scripts/authorsTransform.py <archive.zip> <slug> --apply    # write work files
"""
import argparse
import collections
import csv
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import authorNames  # noqa: E402
import sources  # noqa: E402
import taxamatch  # noqa: E402
from nomenclatureTransform import held  # noqa: E402
from tree import kingdom_names  # noqa: E402

csv.field_size_limit(10 ** 9)
SPECIES = {"species", "spec.", "sp."}


def _member(z, name):
    for m in z.namelist():
        if os.path.basename(m).lower() in (f"{name.lower()}.tsv", f"{name.lower()}.txt"):
            return m
    return None


def _rows(z, member):
    with z.open(member) as fh:
        r = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t",
                           quoting=csv.QUOTE_NONE)
        for row in r:
            yield {k.split(":", 1)[-1]: (v or "").strip() for k, v in row.items() if k}


def _ids(v):
    return [x for x in (v or "").split(",") if x]


def is_authors_source(archive):
    """An Author table that the names point at."""
    with zipfile.ZipFile(archive) as z:
        if not _member(z, "Author"):
            return False
        m = _member(z, "NameUsage") or _member(z, "Name")
        if not m:
            return False
        for i, row in enumerate(_rows(z, m)):
            if row.get("combinationAuthorshipID") or row.get("basionymAuthorshipID"):
                return True
            if i > 200000:
                return False
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("slug")
    ap.add_argument("--apply", action="store_true", help="write the work files")
    args = ap.parse_args()
    if not is_authors_source(args.archive):
        print("  not an authors source: no Author table that the names point at")
        return 4

    by_name = collections.defaultdict(list)
    with zipfile.ZipFile(args.archive) as z:
        for row in _rows(z, _member(z, "NameUsage") or _member(z, "Name")):
            if row.get("rank", "").lower() not in SPECIES:
                continue
            if row.get("status") and row["status"] not in ("accepted", "provisionally accepted"):
                continue
            comb = _ids(row.get("combinationAuthorshipID"))
            if not comb:
                continue
            by_name[row["scientificName"].lower()].append(
                (row.get("authorship", ""), tuple(comb), tuple(_ids(row.get("basionymAuthorshipID")))))
        people = {row["ID"]: row for row in _rows(z, _member(z, "Author"))}
    print(f"  {len(by_name):,} species names with author ids, {len(people):,} people", flush=True)

    stat = collections.Counter()
    links, review, used = [], [], set()
    for kingdom in kingdom_names():
        idx = authorNames.load(code="zoo" if kingdom == "animalia" else "bot")
        same_person = lambda a, b: authorNames.same_person(a, b, idx)  # noqa: E731
        ours = held(kingdom)
        compare = []
        for canon, nodes in ours.items():
            cands = by_name.get(canon)
            if not cands:
                continue
            if len(nodes) > 1:
                stat[f"{kingdom}: held more than once, skipped"] += len(nodes)
                continue
            if len({(c[1], c[2]) for c in cands}) > 1:
                stat[f"{kingdom}: source ambiguous, skipped"] += 1
                continue
            path, nid, auth = nodes[0][0], nodes[0][1], nodes[0][2]
            theirs, comb, bas = cands[0]
            compare.append((path, nid, canon, auth, theirs, comb, bas))
        parsed = taxamatch.parse_authorships(sorted({x for c in compare for x in c[3:5] if x}))
        for path, nid, canon, auth, theirs, comb, bas in compare:
            rec = {"file": path, "id": nid, "set": {"authorIds": list(comb)}, "source": args.slug}
            if bas:
                rec["set"]["basionymAuthorIds"] = list(bas)
            if not auth:
                if not theirs:
                    stat[f"{kingdom}: neither side has an authorship"] += 1
                    continue
                rec["set"]["authorship"] = theirs
                stat[f"{kingdom}: authorship filled with ids"] += 1
            else:
                same = (True if auth.replace(" ", "") == theirs.replace(" ", "")
                        else taxamatch.same_authorship(auth, theirs, parsed, same_person))
                if not same:
                    stat[f"{kingdom}: {'conflicts' if same is False else 'not comparable'}"] += 1
                    review.append({"kingdom": kingdom, "file": path, "id": nid, "name": canon,
                                   "ours": auth, "theirs": theirs, "authorIds": list(comb)})
                    continue
                stat[f"{kingdom}: agrees, linked"] += 1
            links.append(rec)
            used.update(comb)
            used.update(bas)
        print(f"  {kingdom} done", flush=True)

    out_people = []
    for pid in sorted(used):
        p = people.get(pid)
        if not p:
            stat["link to a person missing from the Author table"] += 1
            continue
        out_people.append({k: v for k, v in {
            "id": pid, "given": p.get("given"), "family": p.get("family"),
            "abbreviationBotany": p.get("abbreviationBotany"),
            "alternativeIds": _ids(p.get("alternativeID")),
            "birth": p.get("birth"), "death": p.get("death"), "country": p.get("country"),
            "link": p.get("link"), "source": args.slug}.items() if v})
    stat["people linked"] = len(out_people)

    for k, v in sorted(stat.items()):
        print(f"  {v:>10,}  {k}")
    if args.apply:
        work = os.path.join(sources.ROOT, "work", f"{args.slug}-authors")
        os.makedirs(work, exist_ok=True)
        for name, rows in (("people.jsonl", out_people), ("links.jsonl", links),
                           ("review-authors.jsonl", review)):
            with open(os.path.join(work, name), "w", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(os.path.join(work, "summary.json"), "w", encoding="utf-8") as fh:
            json.dump({"archive": args.archive, "counts": dict(stat)}, fh, indent=1)
        print(f"  wrote {work}/ (people {len(out_people):,}, links {len(links):,}, review {len(review):,})")
    else:
        print("\n  (measure only -- pass --apply to write the work files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
