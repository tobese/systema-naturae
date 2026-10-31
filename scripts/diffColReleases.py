#!/usr/bin/env python3
"""What changed between two Catalogue of Life releases, by COL taxon id.

ChecklistBank's own diff lists names removed and added, but caps the added
list (exactly 25,000 for COL26.9 -> 26.10) and cannot say that a removed name
is the same taxon moved: "Atheta (Datomicra) sordidula" removed, "Datomicra
sordidula" added. COL keeps its taxon ids stable across releases, so comparing
the two Taxon.tsv files id by id answers it completely:

  renamed        same id, different scientificName: moved to another genus,
                 rank or spelling change
  moved family   same id, a different family above it
  status         same id, accepted <-> synonym
  removed / new  ids in only one release; a removed id whose binomial is
                 present under a new id is id churn, not a lost taxon

Read-only. Heavy (two ~5M-row tables), so run it where there is room -- q-bert.

    python3 scripts/diffColReleases.py OLD_dwca.zip NEW_dwca.zip [--out diff.jsonl]
"""
import argparse
import collections
import csv
import io
import json
import sys
import zipfile


def load(path):
    """id -> (parent, accepted, status, rank, name, authorship)."""
    csv.field_size_limit(10 ** 8)
    out = {}
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.split("/")[-1].lower() in ("taxon.tsv", "taxon.txt"))
        with z.open(member) as fh:
            rd = csv.reader(io.TextIOWrapper(fh, encoding="utf-8"), delimiter="\t",
                            quoting=csv.QUOTE_NONE)
            ix = {h.split(":")[-1]: i for i, h in enumerate(next(rd))}
            g = lambda r, c: r[ix[c]] if c in ix and ix[c] < len(r) else ""
            for r in rd:
                name, auth = g(r, "scientificName"), g(r, "scientificNameAuthorship")
                # The monthly DwCA (26.10) writes the authorship into
                # scientificName; the base release (26.9) did not. Compared
                # as they come, every name looked renamed.
                if auth and name.endswith(auth):
                    name = name[: -len(auth)].rstrip()
                out[g(r, "taxonID")] = (g(r, "parentNameUsageID"), g(r, "acceptedNameUsageID"),
                                        g(r, "taxonomicStatus"), g(r, "taxonRank"), name, auth)
    return out


def families(rows):
    """id -> family name, memoised walk; a synonym takes its accepted taxon's."""
    memo = {}

    def fam(tid):
        path, cur, found = [], tid, None
        while cur and cur in rows:
            if cur in memo:
                found = memo[cur]
                break
            path.append(cur)
            parent, acc, status, rank, name, _ = rows[cur]
            if rank == "family":
                # the word only: "Chaetonotidae Gosse, 1864 sensu Leasi &
                # Todaro, 2008" is Chaetonotidae
                found = name.split()[0] if name else name
                break
            cur = acc if status not in ("accepted", "provisionally accepted") and acc else parent
        for t in path:
            memo[t] = found
        return found
    return fam


def name_words(name):
    """Genus, subgenus (in brackets) and epithets: the name without whatever
    remark the monthly format appends ("junior homonym", "auct. non", "[sic]")."""
    out = []
    for w in name.split():
        if not out:
            out.append(w)
        elif w.startswith("(") and w.endswith(")") and w[1:2].isupper():
            out.append(w)
        elif w[:1].islower() and w.replace("-", "").isalpha() and w not in ("auct.", "non", "sensu", "sic"):
            out.append(w)
        else:
            break
    return out


def rename_kind(old, new):
    a, b = name_words(old), name_words(new)
    if a == b:
        return "renamed: remark only (format, not a change)"
    strip = lambda ws: [w for w in ws if not w.startswith("(")]
    if strip(a) == strip(b):
        return "renamed: subgenus added/removed"
    if a and b and a[0] != b[0]:
        return "renamed: other genus"
    return "renamed: epithet spelling/rank"


def binomial(name):
    w = [x for x in name.split() if not (x.startswith("(") and x.endswith(")"))]
    return " ".join(w[:2]) if len(w) >= 2 and w[1][:1].islower() else (w[0] if w else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    print("  loading old", flush=True)
    a = load(args.old)
    print(f"    {len(a):,} usages\n  loading new", flush=True)
    b = load(args.new)
    print(f"    {len(b):,} usages", flush=True)
    fa, fb = families(a), families(b)

    stat = collections.Counter()
    by_rank = collections.defaultdict(collections.Counter)
    fam_moves = collections.Counter()
    out = open(args.out, "w", encoding="utf-8") if args.out else None

    def emit(kind, tid, **kw):
        stat[kind] += 1
        if out:
            out.write(json.dumps({"kind": kind, "id": tid, **kw}, ensure_ascii=False) + "\n")

    for tid in a.keys() & b.keys():
        oa, ob = a[tid], b[tid]
        rank = ob[3]
        if oa[4] != ob[4]:
            kind = rename_kind(oa[4], ob[4])
            by_rank[kind][rank] += 1
            emit(kind, tid, old=oa[4], new=ob[4], rank=rank)
        if (oa[2] in ("accepted", "provisionally accepted")) != (ob[2] in ("accepted", "provisionally accepted")):
            by_rank["status changed"][rank] += 1
            emit("status changed", tid, name=ob[4], old=oa[2], new=ob[2], rank=rank)
        f1, f2 = fa(tid), fb(tid)
        if f1 and f2 and f1 != f2 and rank in ("species", "subspecies", "genus"):
            fam_moves[(f1, f2)] += 1
            by_rank["moved family"][rank] += 1
            emit("moved family", tid, name=ob[4], old=f1, new=f2, rank=rank)

    new_names = collections.Counter(binomial(b[t][4]) for t in b.keys() - a.keys())
    for tid in a.keys() - b.keys():
        bn = binomial(a[tid][4])
        kind = "removed id, name present under a new id" if new_names.get(bn) else "removed"
        by_rank[kind][a[tid][3]] += 1
        emit(kind, tid, name=a[tid][4], rank=a[tid][3])
    old_names = collections.Counter(binomial(a[t][4]) for t in a.keys() - b.keys())
    for tid in b.keys() - a.keys():
        bn = binomial(b[tid][4])
        kind = "new id, name was present under an old id" if old_names.get(bn) else "new"
        by_rank[kind][b[tid][3]] += 1
        emit(kind, tid, name=b[tid][4], rank=b[tid][3])
    if out:
        out.close()

    print(f"\n  ids in both: {len(a.keys() & b.keys()):,}")
    for kind, n in stat.most_common():
        top = ", ".join(f"{r or '?'} {c:,}" for r, c in by_rank[kind].most_common(4))
        print(f"  {n:9,}  {kind}   ({top})")
    if fam_moves:
        print("\n  most common family moves (species/genus/subspecies):")
        for (f1, f2), n in fam_moves.most_common(20):
            print(f"  {n:7,}  {f1} -> {f2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
