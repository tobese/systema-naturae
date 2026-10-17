#!/usr/bin/env python3
"""taxaserve — an in-memory taxonomy lookup service, for triage and imports.

Every script that needs to know "do we already hold this name?" rebuilds the
answer from scratch. scripts/sampleDatasetOverlap.py read all 10,601 animalia
family files five times before making a single API call; importColChecklist.py
walks a kingdom's files to build a held-set before it can stage anything.
2.5GB of family JSON, and the same question asked from scratch each time.

So hold the answer once and serve it. Modeled on scripts/dbserved.ts, which
already does this for the Wikipedia plant DB, and deliberately similar in shape:
stdlib http.server, no dependencies, JSONL on disk.

    python3 scripts/taxaserve.py                  # serve on :9882
    python3 scripts/taxaserve.py --port 9882 --build-only

What it holds
-------------
Three indexes, each built once at startup and reported on:

  names   species name -> where it lives (kingdom, family, genus), for every
          kingdom. ~2.5M entries, ~1.2GB. This is the one that answers triage.
  parse   name -> parsed canonical form, from portal/data/name-parse-index.jsonl
          (2.7M lines, 815MB). Served rather than recomputed because GNparser is
          an external binary and parse_names() shells out to it per batch --
          ~50k names a second is fine once and pointless to repeat.
  pending the pending-family store, so a triage run can ask what is missing
          without reading the external volume itself.

Endpoints
---------
  GET  /health                     liveness, index sizes, build seconds
  POST /held        {names}        which are held, and where
  GET  /held?name=A&name=B         same, GET form for curl
  POST /parse       {names}        canonical form from the parse index
  GET  /stats                      per-kingdom counts, families, genera
  GET  /pending?scaffoldable=1     the pending-family store
  POST /reload                     rebuild the indexes after a write

Staleness is the whole risk of a cache like this, and it is why /held answers
"where" rather than just "yes". An importer that trusts a boolean gets a wrong
answer with no way to notice; one that gets a family back can see immediately
that the family is not the one it expected. Every response carries an `indexed`
field, the mtime the index was built from, so a caller can compare against its
own idea of the tree. `held_names` in the importer used to be a bare set, and
that is exactly what made the Craneflies ILDIS confusion expensive.

Never write taxonomy data from here. This is a read cache over files that
importers own.
"""
import argparse
import collections
import http.server
import json
import os
import socketserver
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import KINGDOMS, iter_family_files  # noqa: E402
PARSE_INDEX = os.path.join(ROOT, "portal/data/name-parse-index.jsonl")
PENDING = "/Volumes/MacieExternal/sources/pending/families.jsonl"

# Interned so 2.5M species can share ~14k family strings instead of one each.
# Without this the index is 1.2GB of mostly repeated text.
_strings = {"k": [], "f": [], "fdisp": [], "g": []}
_pool = {}


def _intern(kind, s):
    """Intern a string, returning an index into _strings[kind].

    Families are interned twice: lowercased for matching, original for display.
    Returning the lowercase form made every answer unusable in a report without
    anyone noticing, because "hominidae" looks right next to "homo sapiens".
    """
    if not s:
        return -1
    pool = _pool.setdefault(kind, {})
    i = pool.get(s)
    if i is None:
        i = pool[s] = len(_strings[kind])
        _strings[kind].append(s)
    return i


FAMILY_DISPLAY = {}


def _intern_family(name):
    """(match index, display index) for a family name."""
    disp = _intern("fdisp", name)
    low = name.strip().lower()
    i = _intern("f", low)
    FAMILY_DISPLAY[i] = disp
    return i, disp


class Index:
    """The three lookup tables. Rebuilt whole on /reload; never mutated."""

    def __init__(self, quiet=False):
        self.lock = threading.Lock()
        self.held = {}            # lowercased name -> [(kingdom, family, genus)]
        self.genera = set()       # lowercased GENUS names, for genus registers
        self.families = set()     # lowercased FAMILY names
        self.parse = {}           # name -> canonical
        self.pending = []
        self.built_at = 0.0
        self.tree_mtime = 0.0
        self.build_seconds = {}
        if not quiet:
            print("  building indexes...", flush=True)
        self._build_held(quiet)
        self._build_parse(quiet)
        self._load_pending(quiet)

    # ------------------------------------------------------------------ build

    def _build_held(self, quiet):
        t0 = time.time()
        held = self.held
        per = {}
        for k in KINGDOMS:
            n = 0
            for fam in iter_family_files(k):
                f = fam.path
                try:
                    d = fam.load()
                except Exception:
                    continue
                fam_raw = (d.get("name") or "").strip()
                if not fam_raw:
                    continue
                self.families.add(fam_raw.lower())
                ki = _intern("k", k)
                fi, _fdisp = _intern_family(fam_raw)
                st = [(nd, None) for nd in reversed(d.get("children") or [])]
                while st:
                    node, genus = st.pop()
                    if node.get("rank") == "GENUS":
                        genus = (node.get("name") or "").strip()
                        if genus:
                            self.genera.add(genus.lower())
                    if node.get("rank") == "SPECIES" and node.get("name"):
                        # The genus comes from the GENUS node this species hangs
                        # under, which is structural. It does NOT come from
                        # `lineage`: that field holds three different things in
                        # this tree -- the genus for most species, the FAMILY for
                        # the 980,786 an importer wrote that way, and a
                        # superseded genus for 1.17M plantae (Gyroporella
                        # pauciforata under "Physoporella"), so reading it as the
                        # genus makes Homo sapiens report "human", since its
                        # lineage field holds the common name.
                        g = genus or node["name"].split()[0]
                        held.setdefault(_norm(node["name"]), []).append(
                            (ki, fi, _intern("g", g)))
                        n += 1
                    for c in reversed(node.get("children") or []):
                        st.append((c, genus))
                    for sp in node.get("speciesList") or []:
                        if sp.get("name"):
                            held.setdefault(_norm(sp["name"]), []).append(
                                (ki, fi, _intern("g", genus or "")))
                            n += 1
            per[k] = n
        self.per_kingdom = per
        self._fdisp = FAMILY_DISPLAY
        self.build_seconds["held"] = time.time() - t0
        if not quiet:
            print(f"    held:   {len(held):,} species names and "
                  f"{len(self.genera):,} genera across "
                  f"{len(KINGDOMS)} kingdoms in "
                  f"{self.build_seconds['held']:.1f}s", flush=True)
            for k, n in per.items():
                print(f"        {k:10s} {n:>9,}", flush=True)

    def _build_parse(self, quiet):
        t0 = time.time()
        parse = self.parse
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import nameIndexCache  # noqa: E402
        records = nameIndexCache.load_all_records()
        if not records:
            if not quiet:
                print(f"    parse:  no parser index (sidecars or monolith), skipped "
                      f"(run scripts/parseAllNames.py --split)", flush=True)
            self.build_seconds["parse"] = 0.0
            return
        n = 0
        for r in records:
            name = r.get("n")
            if name:
                parse[name] = r.get("canonical") or name
                n += 1
        self.build_seconds["parse"] = time.time() - t0
        if not quiet:
            print(f"    parse:  {n:,} names in "
                  f"{self.build_seconds['parse']:.1f}s", flush=True)

    def _load_pending(self, quiet):
        t0 = time.time()
        rows = []
        if os.path.exists(PENDING):
            with open(PENDING, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        self.pending = rows
        self.build_seconds["pending"] = time.time() - t0
        if not quiet:
            print(f"    pending: {len(rows):,} families in "
                  f"{self.build_seconds['pending']:.1f}s", flush=True)

    _fdisp = {}
    _items = None

    def parse_items(self):
        """name -> canonical as a list, built once.

        Paging this endpoint over 2.7M entries means ~684 requests, and
        rebuilding the list per request turned a 12s load into a 30min run.
        """
        if self._items is None:
            self._items = list(self.parse.items())
        return self._items

    def reload(self):
        with self.lock:
            t0 = time.time()
            fresh = Index(quiet=True)
            self.held = fresh.held
            self.parse = fresh.parse
            self.pending = fresh.pending
            self.per_kingdom = fresh.per_kingdom
            self._fdisp = fresh._fdisp
            self._items = None
            self.built_at = time.time()
            self.tree_mtime = self._tree_mtime()
            return time.time() - t0

    @staticmethod
    def _tree_mtime():
        """Newest mtime across the family files, so a caller can tell whether
        this index reflects the tree it is asking about."""
        newest = 0.0
        for k in KINGDOMS:
            for fam in iter_family_files(k):
                f = fam.path
                try:
                    m = os.path.getmtime(f)
                except OSError:
                    continue
                if m > newest:
                    newest = m
        return newest

    # ----------------------------------------------------------------- lookup

    def where(self, name):
        return self.held.get(_norm(name))

    def summary(self):
        return {
            "indexed": self.built_at,
            "treeMtime": self.tree_mtime,
            "speciesNames": len(self.held),
            "genusNames": len(self.genera),
            "familyNames": len(self.families),
            "parseNames": len(self.parse),
            "pendingFamilies": len(self.pending),
            "families": len(_strings["f"]),
            "genera": len(_strings["g"]),
            "perKingdom": getattr(self, "per_kingdom", {}),
        }


INDEX = None


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if os.environ.get("TAXASERVE_VERBOSE"):
            sys.stderr.write("  %s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _names(self, qs=None):
        if qs is None:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                return json.loads(raw).get("names") or []
            except json.JSONDecodeError:
                return []
        out = []
        for key, vals in qs:
            if key == "name":
                out.extend(vals)
        return out

    def do_GET(self):
        path, _, qs = self.path.partition("?")
        q = _parse_qs(qs)
        if path == "/health":
            self._send({"ok": True, **INDEX.summary()})
        elif path == "/held":
            self._send(self._held(self._names(q)))
        elif path == "/parse":
            # _parse_qs yields lists, so every scalar needs unwrapping
            off = (q.get("offset") or [None])[0]
            lim = (q.get("limit") or ["4000"])[0]
            if off is not None or "limit" in q:
                # paged form: the whole index, for canonicalNames._load_served
                off = int(off or 0)
                lim = min(int(lim or 4000), 20000)
                items = INDEX.parse_items()
                rows = [{"n": n, "canonical": c} for n, c in items[off:off + lim]]
                self._send({"indexed": INDEX.built_at, "total": len(items),
                            "offset": off, "rows": rows})
                return
            names = self._names(q)
            miss = [n for n in names if n not in INDEX.parse]
            self._send({"indexed": INDEX.built_at,
                        "canonical": {n: INDEX.parse[n] for n in names
                                      if n in INDEX.parse},
                        "notIndexed": len(miss),
                        "notIndexedSample": miss[:20]})
        elif path == "/stats":
            self._send(self._stats())
        elif path == "/pending":
            rows = INDEX.pending
            if (q.get("scaffoldable") or [""])[0] in ("1", "true"):
                have = {_strings["f"][i] for lst in INDEX.held.values()
                        for (_, fi, _) in lst}
                rows = [r for r in rows
                        if (r.get("family") or "").lower() in have]
            limit = int((q.get("limit") or ["100"])[0])
            self._send({"indexed": INDEX.built_at,
                        "total": len(rows),
                        "rows": rows[:limit]})
        else:
            self._send({"error": "no such endpoint", "path": path}, 404)

    def do_POST(self):
        path, _, _qs = self.path.partition("?")
        if path == "/held":
            self._send(self._held(self._names()))
        elif path == "/parse":
            names = self._names()
            miss = [n for n in names if n not in INDEX.parse]
            self._send({"indexed": INDEX.built_at,
                        "canonical": {n: INDEX.parse[n] for n in names
                                      if n in INDEX.parse},
                        "notIndexed": len(miss),
                        "notIndexedSample": miss[:20]})
        elif path == "/reload":
            secs = INDEX.reload()
            self._send({"ok": True, "reloadedInSeconds": round(secs, 1),
                        **INDEX.summary()})
        else:
            self._send({"error": "no such endpoint", "path": path}, 404)

    def _held(self, names):
        idx = INDEX
        out = {}
        genera_hit = 0
        family_hit = 0
        for n in names:
            hits = idx.where(n)
            if hits:
                out[_norm(n)] = [
                    {"rank": "SPECIES",
                     "kingdom": _strings["k"][ki],
                     "family": _strings["fdisp"][INDEX._fdisp[fi]],
                     "genus": _strings["g"][gi] if gi >= 0 else None}
                    for (ki, fi, gi) in hits]
                continue
            # A register of genera cannot be measured against a species-only
            # index. IRMNG holds 269,528 genera and 2 species, and asking a
            # species index about genera returns a confident 0-of-600, which
            # the caller is right to refuse as impossible.
            g = _norm(n)
            if g in idx.genera:
                out[g] = [{"rank": "GENUS"}]
                genera_hit += 1
                continue
            if g in idx.families:
                out[g] = [{"rank": "FAMILY"}]
                family_hit += 1
        return {"indexed": idx.built_at, "treeMtime": idx.tree_mtime,
                "held": out, "asked": len(names),
                "notHeld": len(names) - len(out),
                "matchedAsGenus": genera_hit,
                "matchedAsFamily": family_hit}

    def _stats(self):
        fam_by_kingdom = collections.Counter()
        for lst in INDEX.held.values():
            for (ki, _fi, _gi) in lst:
                fam_by_kingdom[_strings["k"][ki]] += 1
        return {"indexed": INDEX.built_at, "treeMtime": INDEX.tree_mtime,
                "speciesNames": len(INDEX.held),
                "parseNames": len(INDEX.parse),
                "pendingFamilies": len(INDEX.pending),
                "families": len(_strings["f"]),
                "perKingdom": getattr(INDEX, "per_kingdom", {}),
                "speciesPerKingdom": dict(fam_by_kingdom),
                "buildSeconds": {k: round(v, 1)
                                 for k, v in INDEX.build_seconds.items()}}


def _parse_qs(qs):
    out = collections.defaultdict(list)
    for part in qs.split("&"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out[_unquote(k)].append(_unquote(v))
    return out


DAGGER = "\u2020"


def _norm(name):
    """Match key for a name.

    A leading dagger marks an extinct taxon and appears in our own family files
    ("\u2020Progonocimicidae"), but not in the name lists the triage tools
    sample. held_names() stripped it, so the service has to as well or the same
    species is held on one path and missing on the other -- which showed up as
    OSF scoring 84.7% through the service against 88.3% from the tree.
    """
    return (name or "").lstrip(DAGGER).strip().lower()


def _unquote(s):
    from urllib.parse import unquote_plus
    return unquote_plus(s)


def main() -> int:
    global INDEX
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9882)
    ap.add_argument("--build-only", action="store_true",
                    help="build the indexes, report, and exit")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    INDEX = Index(quiet=args.quiet)
    INDEX.built_at = time.time()
    INDEX.tree_mtime = INDEX._tree_mtime()
    if not args.quiet:
        print(f"  built in {time.time() - t0:.1f}s; "
              f"{len(INDEX.held):,} species, {len(INDEX.parse):,} parsed, "
              f"{len(_strings['f']):,} families interned")
    if args.build_only:
        return 0

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"  taxaserve on http://127.0.0.1:{args.port}  "
              f"(/health /held /parse /stats /pending /reload)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
