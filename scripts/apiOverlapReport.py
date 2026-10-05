#!/usr/bin/env python3
"""Exact held/not-held measurement of a ChecklistBank dataset, via the API.

`sampleDatasetOverlap.py` samples ~600 names, which is the right cost for
deciding whether a 2,000-name dataset is worth downloading and the wrong cost
for a 526,474-name one: at 600 samples a 77.8% estimate carries roughly +/-3
points of noise, and the decision here is whether to add a hundred thousand
species to the tree.

So this pages the whole accepted list. It needs no download, and against a
running `scripts/taxaserve.py` it is fast: WFO's 382,437 species is 96 requests
instead of a 1.6GB archive.

    python3 scripts/apiOverlapReport.py 2004
    python3 scripts/apiOverlapReport.py 2144 --rank SPECIES --limit 100000
    python3 scripts/apiOverlapReport.py 2007 --rank GENUS

Requires TAXASERVE. Falls back to reading the tree if it is not running, which
is slow but correct.

Reports three things a percentage cannot:

  * the miss split by whether we hold the species' FAMILY. A miss in a family we
    have is an import that extends the tree; a miss in a family we do not have
    is a refusal plus a pending-family entry, and those are worth very
    different amounts.
  * names that look like prokaryotes or viruses. Bacteria and viruses are on
    hold by decision, so their genera are a policy gap and not a data gap --
    IRMNG's miss is almost entirely "Candidatus ..." and reading it as an
    opening would be wrong.
  * how many of the dataset's families we do not hold at all.
"""
import argparse
import collections
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API = "https://api.checklistbank.org"
TAXASERVE = os.environ.get("TAXASERVE", "").rstrip("/")
DAGGER = "†"

# Genera that signal a prokaryote or a virus. Bacteria and viruses are on hold
# in this project (docs/bacteria-and-viruses.md), so these are separated out
# rather than counted as an opening.
PROK_PREFIX = ("candidatus ", "uncultured ", "uncultivated ", "unclassified ",
               "metagenome ", "unidentified ")


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as e:            # noqa: BLE001 - retry anything
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


SHARDS = "0123456789abcdefghijklmnopqrstuvwxyz"


def page_all(key, rank, pages_per_shard=None, quiet=False, shard=True):
    """Every accepted name at `rank`, paged.

    The API caps `limit` at 1000 and refuses `offset + limit > 100000`, so a
    382,437-name dataset cannot simply be paged -- offset 101,000 returns HTTP
    400 and there is no cursor. Sharding alphabetically on `q` gets every name
    inside the ceiling: the largest single shard of WFO is well under 20,000.

    `pages_per_shard` caps each shard, which keeps the sample spread across the
    whole alphabet instead of exhausting the budget in "A" and reporting a
    flora sample that is all alyssums.
    """
    names = []
    total = 0
    # `q` does not index family names at all -- it returns total 0 for
    # rank=FAMILY on every shard letter, while the unfiltered query returns 738.
    # Families are small enough to page directly (largest here is IRMNG's
    # 21,735), so shard only what needs it.
    # NB a single empty-string pass iterates ZERO times, which is how families
    # came out as 0 held. One pass with no q is the unfiltered query.
    letters = SHARDS if shard else (None,)
    for sh in letters:
        off = 0
        for _ in range(pages_per_shard or 10_000):
            q = f"&q={urllib.parse.quote(sh)}" if shard else ""
            d = get(f"{API}/dataset/{key}/nameusage/search?limit=1000"
                    f"&offset={off}&rank={rank}&status=ACCEPTED{q}")
            # total is PER SHARD, so it has to be summed, not captured once --
            # reporting shard "0"'s total as the dataset total is how WFO came
            # out as "88 species accepted".
            if off == 0:
                total += d.get("total") or 0
            res = d.get("result") or []
            if not res:
                break
            for r in res:
                nm = (r["usage"].get("name") or {}).get("scientificName")
                if nm:
                    names.append(nm)
            off += 1000
            if off > (d.get("total") or 0):
                break
        if quiet:
            continue
        if shard:
            print(f"      shard {sh!r}: {len(names):,} so far", flush=True)
        else:
            print(f"      paged to {off:,} of {total:,}", flush=True)
    return names, total


def norm(n):
    return (n or "").lstrip(DAGGER).strip().lower()


class Held:
    """taxaserve when it is up, otherwise the tree."""

    def __init__(self):
        self.served = None
        self.tree = None
        if TAXASERVE:
            try:
                with urllib.request.urlopen(TAXASERVE + "/health", timeout=15) as r:
                    h = json.load(r)
                self.served = h
            except Exception:
                print(f"  {TAXASERVE} is not answering; reading the tree "
                      f"(slow)")
        if self.served is None:
            import sampleDatasetOverlap as S
            self.tree = set()
            for k in ("animalia", "plantae", "fungi", "chromista",
                      "protozoa", "archaea"):
                self.tree |= S.held_names(k)

    def ask(self, names):
        """-> {normalised name: [records]}"""
        if self.served is not None:
            out = {}
            B = 4000
            ns = list(names)
            for i in range(0, len(ns), B):
                chunk = ns[i:i + B]
                req = urllib.request.Request(
                    TAXASERVE + "/held",
                    data=json.dumps({"names": chunk}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    res = json.load(r)
                for k, v in (res.get("held") or {}).items():
                    out.setdefault(norm(k), []).extend(v)
            return out
        return {n: [{"rank": "SPECIES"}] for n in (norm(x) for x in names)
                if n in self.tree}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+", type=int)
    ap.add_argument("--rank", default="SPECIES")
    ap.add_argument("--pages", type=int, default=0,
                    help="pages (x1000 names) per alphabetical shard, 0 = all. "
                         "A cap keeps the sample spread across the alphabet "
                         "instead of exhausting it in 'A'.")
    ap.add_argument("--family-pages", type=int, default=0)
    args = ap.parse_args()

    held = Held()
    if held.served:
        print(f"  taxaserve: {held.served['speciesNames']:,} species, "
              f"{held.served.get('genusNames', 0):,} genera")

    for key in args.keys:
        m = get(f"{API}/dataset/{key}")
        if isinstance(m, list):
            m = m[0] if m else {}
        print(f"\n=== {key}  {m.get('alias')} -- {m.get('title')}")
        print(f"    v{m.get('version')} issued {str(m.get('issued'))[:10]}  "
              f"licence {m.get('license')}  doi {m.get('doi')}")

        # families first: cheap, and it frames everything else
        fam_names, _ = page_all(key, "FAMILY",
                               pages_per_shard=args.family_pages or None,
                               quiet=True, shard=False)
        fams = set(fam_names)
        fam_rec = held.ask(sorted(fams)) if fams else {}
        have_fam = len(fam_rec)
        print(f"    families: {len(fams):,}  held: {have_fam:,}  "
              f"({100 * have_fam / max(1, len(fams)):.1f}%)")

        print(f"    paging {args.rank.lower()} names...", flush=True)
        t0 = time.time()
        names, total = page_all(key, args.rank,
                                pages_per_shard=args.pages or None)
        print(f"    {args.rank.lower()} accepted: {total:,}"
              f"   measured: {len(names):,} in {time.time() - t0:.0f}s"
              + ("" if args.pages else "  (complete)"))

        recs = held.ask(names)
        miss = [n for n in names if norm(n) not in recs]
        hit = len(names) - len(miss)
        print(f"    held: {hit:,} ({100 * hit / max(1, len(names)):.1f}%)"
              f"   NOT held: {len(miss):,} "
              f"({100 * len(miss) / max(1, len(names)):.1f}%)")

        prok = [n for n in miss if norm(n).lstrip('"').startswith(PROK_PREFIX)]
        rest = [n for n in miss if n not in set(prok)]
        print(f"      of the miss, prokaryote/virus-looking: {len(prok):,}"
              f"   other: {len(rest):,}")
        if prok:
            print("      (bacteria and viruses are on hold by decision -- "
                  "docs/bacteria-and-viruses.md)")
        for n in rest[:10]:
            print(f"        not held: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
