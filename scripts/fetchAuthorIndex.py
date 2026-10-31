#!/usr/bin/env python3
"""Fetch a taxonomic-author index from Wikidata: one record per person who
has an IPNI author id (P586), a botanist author abbreviation (P428), a
ZooBank author id (P2006) or a zoological author citation (P835), with their
label, family name and aliases.

Why: two copies of one species often cite the same author differently --
"DC." / "de Candolle", "Maxim." / "Maksimovich", "Walsingham" / "de Grey"
(one man, Thomas de Grey, 6th Baron Walsingham). String comparison
(taxamatch.same_authorship) settles formatting; only an identifier settles
abbreviations and names. Wikidata is where IPNI's standard forms (Brummitt &
Powell) meet ZooBank's author ids, and IPNI itself offers no bulk author
download.

Derived and re-fetchable, so it lives on the sources volume, not in git:

    python3 scripts/fetchAuthorIndex.py      # -> <sources>/author-index/wikidata-authors.json

Every record keeps its QID, so any match it produces can be traced back.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources  # noqa: E402

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "systema-naturae-author-index/0.1 (https://github.com/; taxonomy portal)"
OUT = os.path.join(sources.ROOT, "author-index", "wikidata-authors.json")
# P835 is zoology's counterpart of P428: the citation form a zoological name
# uses ("Walsingham" for Thomas de Grey, 6th Baron Walsingham), held by
# historical zoologists that have no ZooBank id.
PROPS = {"P586": "ipni", "P428": "abbr", "P2006": "zoobank", "P835": "zoo"}
BATCH = 2000


def sparql(query, tries=4):
    # POST: a VALUES batch of 2,000 QIDs is far past the GET URI limit (414).
    req = urllib.request.Request(
        ENDPOINT, data=urllib.parse.urlencode({"query": query}).encode(),
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA,
                 "Content-Type": "application/x-www-form-urlencoded"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:  # 429/5xx/timeouts: back off and retry
            if attempt == tries - 1 or getattr(e, "code", 0) in (400, 414):
                raise
            wait = 10 * (attempt + 1)
            print(f"    retry in {wait}s ({e})", flush=True)
            time.sleep(wait)


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def main() -> int:
    people = {}
    for prop, field in PROPS.items():
        rows = sparql(f"SELECT ?p ?v WHERE {{ ?p wdt:{prop} ?v }}")
        for r in rows:
            rec = people.setdefault(qid(r["p"]["value"]), {})
            rec.setdefault(field, []).append(r["v"]["value"])
        print(f"  {prop} ({field}): {len(rows):,} statements", flush=True)
    print(f"  {len(people):,} people", flush=True)

    ids = sorted(people)
    for i in range(0, len(ids), BATCH):
        values = " ".join(f"wd:{q}" for q in ids[i:i + BATCH])
        rows = sparql(f"""
            SELECT ?p ?label ?fam ?alias WHERE {{
              VALUES ?p {{ {values} }}
              OPTIONAL {{ ?p rdfs:label ?label FILTER(LANG(?label) = "en") }}
              OPTIONAL {{ ?p wdt:P734 ?f . ?f rdfs:label ?fam FILTER(LANG(?fam) = "en") }}
              OPTIONAL {{ ?p skos:altLabel ?alias FILTER(LANG(?alias) = "en") }}
            }}""")
        for r in rows:
            rec = people[qid(r["p"]["value"])]
            if "label" in r:
                rec["label"] = r["label"]["value"]
            for key, field in (("fam", "family"), ("alias", "aliases")):
                if key in r and r[key]["value"] not in rec.setdefault(field, []):
                    rec[field].append(r[key]["value"])
        print(f"  labels {min(i + BATCH, len(ids)):,}/{len(ids):,}", flush=True)
        time.sleep(1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"source": "Wikidata SPARQL (P586, P428, P2006, P835)",
                   "fetched": time.strftime("%Y-%m-%d"), "people": people},
                  fh, ensure_ascii=False)
    os.replace(tmp, OUT)
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
