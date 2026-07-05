#!/usr/bin/env python3
"""
enrich_worker — pull-queue plant enrichment worker (Tier-2 Wikipedia REST).

Mirrors snedtankt's remote_transcribe.py: claim a batch from Macie's
enrichServe, fetch Wikipedia extracts from THIS machine's IP, submit results
back. Macie writes the JSONs. Stdlib only — no pip install, no repo, no node.

Self-serve launch (nothing to clone):
    curl -s http://100.116.174.3:9881/worker.py -o enrich_worker.py
    python enrich_worker.py --server http://100.116.174.3:9881 --worker steamie
"""
import argparse, json, socket, sys, time, urllib.parse, urllib.request

WIKI_API = "https://en.wikipedia.org/w/api.php"
# Wikimedia policy: a descriptive, contactable UA avoids blocks.
UA = "SystemaNaturae/1.0 (https://github.com/tobese/systema-naturae; distributed enrich worker)"


def binomial(name):
    return " ".join(name.split()[:2])


def http_json(method, url, payload=None, timeout=20):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, (json.loads(r.read() or b"{}") if r.status != 204 else {})


def fetch_wikipedia(names):
    """Return (results, rate_limited). results = {name: {description, commonName?}}."""
    bins = list(dict.fromkeys(b for b in (binomial(n) for n in names) if b))
    if not bins:
        return {}, False
    params = {"action": "query", "titles": "|".join(bins), "prop": "extracts",
              "exintro": "1", "explaintext": "1", "exlimit": str(min(len(bins), 50)),
              "redirects": "1", "format": "json"}
    url = WIKI_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            wait = int(e.headers.get("Retry-After") or 0)
            print(f"  429 rate-limited (Retry-After={wait or '?'})", flush=True)
            return {}, True
        print(f"  wiki fetch failed: HTTP {e.code}", flush=True)
        return {}, False
    except Exception as e:
        print(f"  wiki fetch failed: {e}", flush=True)
        return {}, False
    q = data.get("query", {})
    pages = q.get("pages", {})
    redirects = {}
    for rd in q.get("redirects", []):
        redirects[rd["from"]] = rd["to"]
    for nm in q.get("normalized", []):
        redirects.setdefault(nm["from"], nm["to"])
    title_to_id = {p["title"]: pid for pid, p in pages.items() if not p.get("missing")}
    out = {}
    for name in names:
        b = binomial(name)
        pid = title_to_id.get(redirects.get(b, b))
        if pid is None:
            continue
        p = pages.get(pid, {})
        extract = (p.get("extract") or "").strip()
        if not extract:
            continue
        # first two sentences, else whole intro
        import re
        parts = re.split(r"(?<=[.!?])\s+", extract)
        first = " ".join(parts[:2])
        res = {"description": first if len(first) > 50 else extract}
        desc = p.get("description")
        if desc and len(desc) < 80:
            res["commonName"] = desc
        out[name] = res
    return out, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="e.g. http://100.116.174.3:9881")
    ap.add_argument("--worker", default=socket.gethostname().split(".")[0].lower())
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between REST batches (rate limit)")
    ap.add_argument("--idle-exit", type=int, default=3, help="exit after N consecutive empty claims")
    ap.add_argument("--max-batches", type=int, default=0, help="stop after N batches (0=unlimited; for test runs)")
    args = ap.parse_args()
    server = args.server.rstrip("/")
    print(f"[{args.worker}] polling {server}", flush=True)

    total, empties, backoff, batches = 0, 0, 0, 0
    while True:
        if args.max_batches and batches >= args.max_batches:
            print(f"[{args.worker}] reached max-batches={args.max_batches}, exiting ({total} enriched)", flush=True)
            return
        try:
            status, data = http_json("POST", f"{server}/claim", {"worker": args.worker})
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
        names = [it["name"] for it in items]
        found, limited = fetch_wikipedia(names)
        if limited:
            # requeue this batch untouched and back off exponentially (cap 5 min)
            http_json("POST", f"{server}/submit", {"worker": args.worker, "results": [{"id": it["id"]} for it in items]})
            backoff = min(backoff * 2, 300) if backoff else 15
            print(f"[{args.worker}] backing off {backoff}s (rate limited)", flush=True)
            time.sleep(backoff)
            continue
        backoff = 0
        results = []
        for it in items:
            r = found.get(it["name"])
            if r:
                results.append({"id": it["id"], "description": r["description"], **({"commonName": r["commonName"]} if "commonName" in r else {})})
            else:
                results.append({"id": it["id"]})  # no result → server requeues
        try:
            _, resp = http_json("POST", f"{server}/submit", {"worker": args.worker, "results": results})
            w = resp.get("written", 0)
            total += w
            print(f"[{args.worker}] batch {len(items)} → +{w} enriched (total {total})", flush=True)
        except Exception as e:
            print(f"  submit failed ({e}); batch will re-lease", flush=True)
            time.sleep(5)
        time.sleep(args.delay)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
