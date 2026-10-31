#!/usr/bin/env python3
"""Inventory: for every source we hold, how old is our copy, and is there a
later version on ChecklistBank? Read-only: fetches nothing, declines nothing.

Found 2026-10-31: the Species Files held outside ChecklistBank were GBIF
exports from May 2011, and the family-pair review had been letting them vote
against COL -- the Cockroach Species File "backed" Ectobiidae over Blattellidae
only because it predates the split. ChecklistBank now has the same list as the
"Blattodea Species File" (key 315660, issued 2026-10-01). Rule from the user:
later is later -- keep the latest version of each list and decline earlier
ones. This is the measuring half of that.

Per source in the sources manifest:

  held       the date of our copy: the archive's own metadata (issued /
             version), else its EML dateStamp, else the date we fetched the
             archive ("fetched:" -- a version cannot be newer than the day we
             downloaded it, so a later ChecklistBank `issued` still means
             a later version)
  sameKey    for a checklistbank-N source, the dataset's current `issued` on
             ChecklistBank (a later import under the same key)
  candidates ChecklistBank datasets found by searching the title (and alias),
             COL releases and annual checklists excluded, each with a title
             similarity and its date
  verdict    current / newer-same-key / newer-elsewhere (best candidate with
             a close title and a later date) / check-by-hand / no-date

Renames happen (Cockroach -> Blattodea Species File), so newer-elsewhere is a
proposal for a human, not a match this script trusts.

    python3 scripts/sourceVersions.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colChecklist as CC  # noqa: E402
import sources  # noqa: E402

API = "https://api.checklistbank.org"
UA = "systema-naturae-source-versions/0.1"
STOP = {"the", "of", "and", "a", "an", "for", "in", "on", "to", "de", "la", "del",
        "world", "database", "list", "checklist", "catalogue", "catalog",
        "online", "dataset", "taxonomic", "names", "edition", "version"}
SIMILAR = 0.5


def get(path, **params):
    url = f"{API}{path}" + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                return None
            time.sleep(3 * (attempt + 1))


def words(title):
    return {w for w in re.findall(r"[a-z0-9]+", (title or "").lower())
            if w not in STOP and len(w) > 2}


def similarity(a, b):
    wa, wb = words(a), words(b)
    return len(wa & wb) / max(1, len(wa | wb))


def archive_of(key):
    d = os.path.join(sources.ROOT, "archives", key)
    if not os.path.isdir(d):
        return None
    if os.path.exists(os.path.join(d, "archive.zip")):
        return os.path.join(d, "archive.zip")
    for f in sorted(os.listdir(d)):
        if f.endswith((".zip", ".tgz", ".tar.gz")) and not f.startswith("."):
            return os.path.join(d, f)
    return None


def held_date(path):
    if not path:
        return ""
    try:
        m = CC.metadata(path)
    except Exception:
        m = {}
    for k in ("issued", "version"):
        v = str(m.get(k) or "")
        hit = re.search(r"(19|20)\d\d(-\d\d(-\d\d)?)?", v)
        if hit:
            return hit.group(0)
    try:
        with zipfile.ZipFile(path) as z:
            n = next((x for x in z.namelist() if x.lower().endswith("eml.xml")), None)
            if n:
                t = z.read(n).decode("utf-8", "replace")
                hit = (re.search(r"<pubDate>\s*((19|20)\d\d[-\d]*)", t)
                       or re.search(r"<dateStamp>((19|20)\d\d-\d\d-\d\d)", t))
                if hit:
                    return hit.group(1)
    except Exception:
        pass
    return ""


def is_col_release(d):
    t = (d.get("title") or "").lower()
    return (d.get("origin") == "release" or t.startswith("catalogue of life")
            or t.startswith("species 2000") or "annual checklist" in t)


def main() -> int:
    manifest = json.load(open(os.path.join(sources.ROOT, "manifest.json")))["sources"]
    out = []
    for key, rec in sorted(manifest.items()):
        title = rec.get("title") or key
        path = archive_of(key)
        held = held_date(path)
        if not held and path:
            held = "fetched:" + time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))
        row = {"source": key, "title": title, "status": rec.get("status"),
               "held": held, "archive": bool(path)}
        own = None
        m = re.match(r"checklistbank-(\d+)$", key)
        if m:
            own = int(m.group(1))
            d = get(f"/dataset/{own}") or {}
            row["sameKey"] = {"key": own, "issued": d.get("issued"), "version": d.get("version"),
                              "deleted": bool(d.get("deleted"))}
        cands = {}
        for q in {re.sub(r"\s*\(.*?\)", "", title).strip(), rec.get("alias") or ""} - {""}:
            res = get("/dataset", q=q, limit=20) or {}
            for d in res.get("result", []):
                if d["key"] == own or is_col_release(d) or d.get("type") not in (None, "taxonomic", "nomenclatural"):
                    continue
                s = similarity(title, d.get("title"))
                if s >= 0.25:
                    cands[d["key"]] = {"key": d["key"], "title": d.get("title"), "alias": d.get("alias"),
                                       "issued": d.get("issued"), "version": d.get("version"),
                                       "similarity": round(s, 2)}
            time.sleep(0.3)
        row["candidates"] = sorted(cands.values(), key=lambda c: (-c["similarity"], c["issued"] or ""))[:5]

        same = (row.get("sameKey") or {}).get("issued") or ""
        best = max((c for c in row["candidates"] if c["similarity"] >= SIMILAR and c["issued"]),
                   key=lambda c: c["issued"], default=None)
        hd = held.replace("fetched:", "")[:10]
        if not held:
            verdict = "no-date"
        elif same and same[:10] > hd:
            verdict = "newer-same-key"
        elif best and best["issued"][:10] > hd:
            verdict = "newer-elsewhere"
        elif any(c["issued"] and c["issued"][:10] > hd for c in row["candidates"]):
            verdict = "check-by-hand"
        else:
            verdict = "current"
        row["verdict"] = verdict
        if best:
            row["best"] = best
        out.append(row)
        print(f"  {verdict:16s} {held[:18]:18s} {key:28s} {title[:50]}", flush=True)

    os.makedirs("data", exist_ok=True)
    with open("data/source-versions.json", "w", encoding="utf-8") as fh:
        json.dump({"checked": time.strftime("%Y-%m-%d"), "sources": out}, fh,
                  indent=1, ensure_ascii=False)
        fh.write("\n")
    order = ["newer-elsewhere", "newer-same-key", "check-by-hand", "no-date", "current"]
    lines = ["# Source versions", "",
             "Generated by `scripts/sourceVersions.py` (read-only). Rule: later is "
             "later -- keep the latest version of each list, decline earlier ones. "
             "`newer-elsewhere` is a proposal (renames happen), confirm it by hand.", "",
             "| verdict | source | title | held | latest found |", "|---|---|---|---|---|"]
    for r in sorted(out, key=lambda r: (order.index(r["verdict"]), r["source"])):
        latest = ""
        if r["verdict"] == "newer-same-key":
            latest = f"same key, {r['sameKey']['issued']}"
        elif r.get("best"):
            b = r["best"]
            latest = f"{b['key']} {b['title'][:45]} ({b['issued']}, sim {b['similarity']})"
        elif r["candidates"]:
            c = r["candidates"][0]
            latest = f"? {c['key']} {c['title'][:45]} ({c['issued']}, sim {c['similarity']})"
        lines.append(f"| {r['verdict']} | {r['source']} | {r['title'][:45]} | "
                     f"{r['held'][:18] or '?'} | {latest} |")
    os.makedirs("docs", exist_ok=True)
    with open("docs/source-versions.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    tally = {}
    for r in out:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("\n  " + ", ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda x: -x[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
