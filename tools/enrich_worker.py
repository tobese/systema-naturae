#!/usr/bin/env python3
"""
enrich_worker — pull-queue plant enrichment worker (GBIF API).

Mirrors snedtankt's remote_transcribe.py: claim a batch from Macie's
enrichServe, fetch GBIF species descriptions from THIS machine's IP, submit
results back. Macie writes the JSONs. Stdlib only — no pip install, no repo, no node.

Self-serve launch (nothing to clone):
    curl -s http://100.116.174.3:9881/worker.py -o enrich_worker.py
    python enrich_worker.py --server http://100.116.174.3:9881 --worker steamie
"""
import argparse, json, socket, sys, time, urllib.parse, urllib.request
import threading, concurrent.futures

GBIF_MATCH = "https://api.gbif.org/v1/species/match"
GBIF_DESCR = "https://api.gbif.org/v1/species"
UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; distributed enrich worker)"


def binomial(name):
    return " ".join(name.split()[:2])


def http_json(method, url, payload=None, timeout=20):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, (json.loads(r.read() or b"{}") if r.status != 204 else {})


def gbif_match(name):
    url = f"{GBIF_MATCH}?name={urllib.parse.quote(name)}&strict=true"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("usageKey")
    except Exception:
        return None


def gbif_description(key):
    url = f"{GBIF_DESCR}/{key}/descriptions"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except Exception:
        return None
    results = data.get("results") or []
    if not results:
        return None
    en = next((r for r in results if r.get("language", "").startswith("en")), None)
    any_lang = next((r for r in results if len(r.get("description", "")) > 20), None)
    best = en or any_lang
    if not best or not best.get("description"):
        return None
    clean = " ".join(best["description"].split())
    return clean[:500] if len(clean) > 30 else None


def lookup_one(name):
    try:
        key = gbif_match(name)
        if key:
            return gbif_description(key)
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="e.g. http://100.116.174.3:9881")
    ap.add_argument("--worker", default=socket.gethostname().split(".")[0].lower())
    ap.add_argument("--concurrency", type=int, default=6, help="concurrent GBIF lookups")
    ap.add_argument("--idle-exit", type=int, default=3, help="exit after N consecutive empty claims")
    ap.add_argument("--max-batches", type=int, default=0, help="stop after N batches (0=unlimited)")
    args = ap.parse_args()
    server = args.server.rstrip("/")
    print(f"[{args.worker}] polling {server} via GBIF API", flush=True)

    total, empties, batches = 0, 0, 0
    while True:
        if args.max_batches and batches >= args.max_batches:
            print(f"[{args.worker}] reached max-batches={args.max_batches}, exiting ({total} enriched)", flush=True)
            return
        try:
            status, data = http_json("POST", f"{server}/claim", {"worker": args.worker, "n": 100})
        except Exception as e:
            print(f"  claim failed ({e}); retrying in 5s", flush=True)
            time.sleep(5)
            continue
        if status == 204 or not data.get("items"):
            empties += 1
            if empties >= args.idle_exit:
                print(f"[{args.worker}] queue empty — done, {total} enriched", flush=True)
                return
            time.sleep(3)
            continue
        empties = 0
        batches += 1
        items = data["items"]

        # Concurrent GBIF lookups
        results = [None] * len(items)
        hits = [0]
        def do_lookup(i):
            name = binomial(items[i]["name"])
            desc = lookup_one(name)
            if desc:
                hits[0] += 1
            results[i] = {"id": items[i]["id"]} if desc is None else {"id": items[i]["id"], "description": desc, "sourcedFrom": "gbif"}

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            pool.map(do_lookup, range(len(items)))

        try:
            _, resp = http_json("POST", f"{server}/submit", {"worker": args.worker, "results": results})
            w = resp.get("written", 0)
            total += w
            print(f"[{args.worker}] batch {len(items)} → {hits[0]} hits, +{w} written (total {total}, batch {batches})", flush=True)
        except Exception as e:
            print(f"  submit failed ({e}); batch will re-lease", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
