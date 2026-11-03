#!/usr/bin/env python3
"""Who the tree's content came from, for the portal's Contributors view.

Writes three files:

  data/contributors.json                  -- the registry (tracked): every
      contributing dataset and the institution behind it, with name, link,
      logo, citation, DOI and licence, each taken from an API response or
      from data/contributors-overrides.json, never written here by hand.
  data/licence-crosscheck.json            -- every queue row / manifest entry
      whose recorded licence disagrees with ChecklistBank's current one.
  portal/public/data/contributors-report.json -- the registry plus species
      counts per kingdom, which the Sources modal's Contributors tab loads;
      and contributors-index.json beside it, the slim id -> dataset lookup the
      species panel uses to name a record's sources.

A dataset is credited if species in the tree carry its id (the parquet's
`authorityIds`, or `sourcedFrom` for the text), if its queue row says it
added or merged species, or if the manifest records it as applied / as a
nomenclature or genus-authority source.

Counts come from portal/data/species.parquet (`make species-parquet`), not
from walking the family files. Metadata comes from ChecklistBank
(api.checklistbank.org/dataset/<key>) and GBIF (api.gbif.org/v1/dataset,
/organization), cached under $SN_SOURCES_ROOT/contributors-cache/ so a re-run
is offline unless --refresh.

Institution, in order of preference: an override, the GBIF publishing
organisation (it carries a homepage and a logo), ChecklistBank's `publisher`,
else the dataset stands as its own institution.

    python3 scripts/buildContributors.py [--refresh] [--offline] [--no-logos]
"""
import argparse
import collections
import hashlib
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_ROOT = os.environ.get("SN_SOURCES_ROOT", "/Volumes/MacieExternal/sources")
MANIFEST = os.path.join(SOURCES_ROOT, "manifest.json")
GBIF_MAP = os.path.join(SOURCES_ROOT, "gbif-dataset-map.json")
CACHE = os.path.join(SOURCES_ROOT, "contributors-cache")
QUEUE_DIR = os.path.join(ROOT, "data", "source-queue")
ALIASES = os.path.join(ROOT, "data", "source-aliases.json")
OVERRIDES = os.path.join(ROOT, "data", "contributors-overrides.json")
REGISTRY = os.path.join(ROOT, "data", "contributors.json")
CROSSCHECK = os.path.join(ROOT, "data", "licence-crosscheck.json")
PARQUET = os.path.join(ROOT, "portal", "data", "species.parquet")
KINGDOM_CONFIG = os.path.join(ROOT, "portal", "data", "kingdom-config.json")
PUBLIC = os.path.join(ROOT, "portal", "public", "data")
REPORT = os.path.join(PUBLIC, "contributors-report.json")
INDEX = os.path.join(PUBLIC, "contributors-index.json")
LOGO_DIR = os.path.join(PUBLIC, "logos")

UA = "Mozilla/5.0 (compatible; systema-naturae contributors)"
try:  # python.org builds on macOS ship without a CA bundle
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()
CLB_RE = re.compile(r"checklistbank-(\d+)$")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
# Not sources: no provenance recorded, or text generated from the lineage.
NOT_SOURCES = {"", "none", "generated", "ollama"}
CREDIT_STATUSES = {"applied", "genus-authority", "nomenclatural track"}
NOMENCLATURE_STATUSES = {"genus-authority", "nomenclatural track"}
MAX_LOGO_BYTES = 1_000_000


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _read(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path, doc) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


class Fetcher:
    """GET a JSON document through a file cache. 404 is cached too (as
    {"_status": 404}) so a missing dataset isn't re-asked every run."""

    def __init__(self, refresh: bool, offline: bool):
        self.refresh, self.offline = refresh, offline
        self.fetched = 0

    def get(self, kind: str, key: str, url: str):
        path = os.path.join(CACHE, kind, f"{key}.json")
        if os.path.exists(path) and not self.refresh:
            doc = _read(path)
        elif self.offline:
            return None
        else:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
                    doc = json.load(r)
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    print(f"  WARN  {url}: HTTP {e.code}", file=sys.stderr)
                    return None
                doc = {"_status": 404}
            except (OSError, json.JSONDecodeError) as e:
                print(f"  WARN  {url}: {e}", file=sys.stderr)
                return None
            doc["_fetched"] = _now()
            _write(path, doc)
            self.fetched += 1
            time.sleep(0.1)
        return None if doc.get("_status") == 404 else doc

    def clb(self, key):
        return self.get("clb", str(key), f"https://api.checklistbank.org/dataset/{key}")

    def gbif_dataset(self, uuid):
        return self.get("gbif-dataset", uuid, f"https://api.gbif.org/v1/dataset/{uuid}")

    def gbif_org(self, uuid):
        return self.get("gbif-org", uuid, f"https://api.gbif.org/v1/organization/{uuid}")


LOGO_FAILURES = os.path.join(CACHE, "logo-failures.json")


def fetch_logo(url: str, offline: bool, refresh: bool = False):
    """Download a logo once into portal/public/data/logos/; never hotlinked.
    Returns the path relative to public/data, or None. A URL that failed is
    remembered and not retried until --refresh."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    failures = _read(LOGO_FAILURES, {})
    stem = hashlib.sha1(url.encode()).hexdigest()[:12]
    os.makedirs(LOGO_DIR, exist_ok=True)
    for name in os.listdir(LOGO_DIR):
        if name.startswith(stem + "."):
            return f"logos/{name}"
    if offline or (url in failures and not refresh):
        return None

    def failed(why):
        print(f"  WARN  logo {url}: {why}", file=sys.stderr)
        failures[url] = {"why": str(why)[:200], "at": _now()}
        _write(LOGO_FAILURES, failures)
        return None

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            body = r.read(MAX_LOGO_BYTES + 1)
    except (OSError, ValueError) as e:  # URLError, resets, timeouts
        return failed(e)
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif",
           "image/svg+xml": "svg", "image/webp": "webp"}.get(ctype) or sniff_image(body)
    if ext is None or len(body) > MAX_LOGO_BYTES:
        return failed(f"{ctype or 'no content type'}, {len(body)} bytes")
    if ext != "svg":
        body, ext = shrink(body, ext)
    with open(os.path.join(LOGO_DIR, f"{stem}.{ext}"), "wb") as f:
        f.write(body)
    return f"logos/{stem}.{ext}"


LOGO_PX = 128


def shrink(body: bytes, ext: str):
    """Scale a raster logo down to LOGO_PX on its long side (the card shows
    it at 36px). Without Pillow the original is kept."""
    try:
        from io import BytesIO
        from PIL import Image
    except ImportError:
        return body, ext
    try:
        im = Image.open(BytesIO(body))
        if max(im.size) <= LOGO_PX and len(body) < 40_000:
            return body, ext
        im.thumbnail((LOGO_PX, LOGO_PX))
        out = BytesIO()
        if im.mode not in ("RGB", "RGBA", "L", "LA"):
            im = im.convert("RGBA")
        im.save(out, "PNG", optimize=True)
        return out.getvalue(), "png"
    except Exception as e:  # a corrupt or exotic image: keep the original
        print(f"  WARN  could not shrink logo: {e}", file=sys.stderr)
        return body, ext


SITE_ICONS = os.path.join(CACHE, "site-icons.json")


def site_icon(homepage: str, offline: bool, refresh: bool):
    """The icon a site publishes for itself (apple-touch-icon, else the
    largest <link rel=icon>), as a fallback logo. Cached per homepage,
    misses included."""
    if not homepage or not homepage.startswith(("http://", "https://")):
        return None
    cache = _read(SITE_ICONS, {})
    if homepage in cache and not refresh:
        return cache[homepage]
    if offline:
        return None
    found = None
    try:
        req = urllib.request.Request(homepage, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
            page = r.read(400_000).decode("utf-8", "replace")
            base = r.geturl()
        best = (-1, None)
        for tag in re.findall(r"<link\b[^>]*>", page, re.I):
            rel = (re.search(r'rel=["\']([^"\']+)', tag, re.I) or [None, ""])[1].lower()
            href = (re.search(r'href=["\']([^"\']+)', tag, re.I) or [None, None])[1]
            if not href or "icon" not in rel.split() and "apple-touch-icon" not in rel:
                continue
            sizes = re.search(r'sizes=["\'](\d+)', tag, re.I)
            score = (1000 if "apple-touch-icon" in rel else 0) + (int(sizes.group(1)) if sizes else 16)
            if href.lower().endswith(".svg"):
                score += 500
            if score > best[0]:
                best = (score, urllib.parse.urljoin(base, html.unescape(href)))
        found = best[1]
    except (OSError, ValueError) as e:
        print(f"  WARN  site icon {homepage}: {e}", file=sys.stderr)
    cache[homepage] = found
    _write(SITE_ICONS, cache)
    return found


def sniff_image(body: bytes):
    """Image type from the first bytes, for servers that send no (or a
    generic) content type."""
    head = body[:256].lstrip()
    if head.startswith(b"\x89PNG"):
        return "png"
    if head.startswith(b"\xff\xd8"):
        return "jpg"
    if head.startswith(b"GIF8"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in body[:2048]):
        return "svg"
    return None


def strip_html(s):
    if not s:
        return None
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip() or None


def norm_licence(s):
    """Reduce a licence statement to its family ("cc by-nc", "cc0", ...), so
    'CC BY 4.0 (stated in the eml)' and ChecklistBank's 'cc by' compare equal.
    None for anything that isn't a recognisable CC/PD statement."""
    if not s:
        return None
    t = s.lower().replace("_", " ").replace("–", "-")
    # A licence URL (creativecommons.org/licenses/by-nc/4.0) or an SPDX-style
    # id (CC-BY-NC-4.0) says the same thing as the words.
    t = re.sub(r"creativecommons\.org/licenses/([a-z-]+)", lambda m: " cc " + m.group(1).replace("-", " "), t)
    t = re.sub(r"\bcc-by", "cc by", t).replace("by-nc", "by nc").replace("by-sa", "by sa").replace("by-nd", "by nd")
    if re.search(r"\bcc0\b|cc zero|publicdomain/zero|public ?domain|\bpd\b", t):
        return "cc0"
    m = re.search(r"\bcc[ -]?by((?:[ -](?:nc|sa|nd))*)", t)
    if not m:
        return None
    parts = re.findall(r"nc|sa|nd", m.group(1))
    return "cc by" + "".join("-" + p for p in parts)


ARCHIVES = os.path.join(SOURCES_ROOT, "archives")
META_NAMES = ("eml.xml", "metadata.yaml", "metadata.yml", "metadata.json")


def archive_meta(slug):
    """Licence and version as the archive we hold states them -- what we
    actually took, as opposed to what ChecklistBank says today. Reads the
    first of eml.xml / metadata.yaml / metadata.yml / Metadata.json found in
    the archive's zips (archive.zip first). None when there is none."""
    d = os.path.join(ARCHIVES, slug)
    if not os.path.isdir(d):
        return None
    zips = sorted((f for f in os.listdir(d) if f.endswith(".zip")), key=lambda f: (f != "archive.zip", f))
    for z in zips:
        path = os.path.join(d, z)
        try:
            with zipfile.ZipFile(path) as zf:
                cands = [n for n in zf.namelist() if os.path.basename(n).lower() in META_NAMES]
                if not cands:
                    continue
                name = min(cands, key=lambda n: (META_NAMES.index(os.path.basename(n).lower()), len(n)))
                text = zf.read(name)[:2_000_000].decode("utf-8", "replace")
        except (zipfile.BadZipFile, OSError, KeyError):
            continue
        out = {"archive": f"{slug}/{z}", "file": name,
               "taken": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))}
        low = os.path.basename(name).lower()
        if low == "eml.xml":
            ir = re.search(r"<intellectualRights>(.*?)</intellectualRights>", text, re.S | re.I)
            if ir:
                url = re.search(r'url="([^"]+)"', ir.group(1))
                out["licence"] = strip_html(ir.group(1))
                out["licenceUrl"] = url.group(1) if url else None
            pd = re.search(r"<pubDate>\s*([^<\s]+)", text)
            out["version"] = pd.group(1) if pd else None
        elif low == "metadata.json":
            try:
                j = json.loads(text)
            except ValueError:
                j = {}
            out["licence"] = j.get("license")
            out["version"] = j.get("version") or j.get("issued")
        else:
            for field, key in (("license", "licence"), ("version", "version"), ("issued", "issued")):
                m = re.search(rf"^{field}:\s*['\"]?([^'\"\n]+)", text, re.M)
                if m:
                    out[key] = m.group(1).strip()
            out["version"] = out.get("version") or out.get("issued")
        return out
    return None


def licence_label(clb_licence):
    """'cc by nc' -> 'CC BY-NC'; anything unrecognised ('other') as given."""
    n = norm_licence(clb_licence)
    return n.upper() if n else clb_licence


# ---------------------------------------------------------------------------


def load_counts(kingdoms):
    """{key: {kingdom: n}} for authorityIds and for sourcedFrom."""
    con = duckdb.connect()
    ids = {}
    for kingdom, key, n in con.execute(
        f"""select kingdom, k, count(*) from (
              select kingdom, unnest(string_split(authorityIds, ',')) k
              from '{PARQUET}' where authorityIds <> '') group by all"""
    ).fetchall():
        if kingdom in kingdoms:
            ids.setdefault(key, {})[kingdom] = n
    text = {}
    for kingdom, key, n in con.execute(
        f"select kingdom, coalesce(sourcedFrom, ''), count(*) from '{PARQUET}' group by all"
    ).fetchall():
        if kingdom in kingdoms:
            text.setdefault(key, {})[kingdom] = n
    total = dict(con.execute(f"select kingdom, count(*) from '{PARQUET}' group by 1").fetchall())
    return ids, text, {k: total.get(k, 0) for k in kingdoms}


def resolve_key(key, aliases, gbif_map, manifest):
    """Map an id stamped on a node to a dataset id. Returns (id, kind) where
    kind is "dataset", "unrecorded" (a container naming no one dataset),
    "skip" (not a source) or "unknown"."""
    k = key.strip().lower()
    if k in NOT_SOURCES:
        return None, "skip"
    if CLB_RE.match(k):
        return k, "dataset"
    if UUID_RE.fullmatch(k):
        hit = gbif_map.get(k)
        return (f"checklistbank-{hit['clb']}" if hit else f"gbif-dataset-{k}"), "dataset"
    if k == "checklistbank":
        return "unrecorded:checklistbank", "unrecorded"
    if k in aliases:
        ds = aliases[k]["datasets"]
        if len(ds) == 1:
            return ds[0], "dataset"
        return f"src:{k}", "dataset"
    if k in manifest:
        return k, "dataset"
    return f"unknown:{k}", "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-fetch every cached API document")
    ap.add_argument("--offline", action="store_true", help="cache only; no network")
    ap.add_argument("--no-logos", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        sys.exit(f"FATAL: {MANIFEST} not found -- is the external volume mounted?")
    manifest = _read(MANIFEST)["sources"]
    gbif_map = _read(GBIF_MAP, {})
    aliases = _read(ALIASES)["aliases"]
    overrides = _read(OVERRIDES, {"institutions": {}, "datasets": {}})
    kingdoms = list(_read(KINGDOM_CONFIG)["kingdoms"])
    queue = {}
    for name in os.listdir(QUEUE_DIR):
        if name.endswith(".json"):
            row = _read(os.path.join(QUEUE_DIR, name))
            queue[row["key"]] = row
    fetch = Fetcher(args.refresh, args.offline)

    # -- counts --------------------------------------------------------------
    id_counts, text_counts, totals = load_counts(set(kingdoms))
    species, text, unknown = {}, {}, {}
    unrecorded = {"species": {}, "text": {}}
    key_map = {}  # raw id on a node -> dataset id, for the species panel

    def add(into, key, per_kingdom):
        ds, kind = resolve_key(key, aliases, gbif_map, manifest)
        if kind == "skip":
            return
        if into is species and kind in ("dataset", "unrecorded"):
            key_map[key] = ds
        tally = "species" if into is species else "text"
        target = {"dataset": into, "unrecorded": unrecorded[tally], "unknown": unknown}[kind]
        bucket = target.setdefault(ds, {})
        for kg, n in per_kingdom.items():
            bucket[kg] = bucket.get(kg, 0) + n

    for key, per in id_counts.items():
        add(species, key, per)
    for key, per in text_counts.items():
        add(text, key, per)
    no_provenance = {kg: sum(text_counts.get(k, {}).get(kg, 0) for k in NOT_SOURCES) for kg in kingdoms}

    # -- which datasets are credited -----------------------------------------
    credited = set(species) | set(text)
    for key, row in queue.items():
        a = row.get("applied") or {}
        if row.get("stage") == "applied" and ((a.get("added") or 0) > 0 or (a.get("merged") or 0) > 0):
            credited.add(key)
    for key, v in manifest.items():
        if v.get("status") in CREDIT_STATUSES:
            credited.add(key)
    credited |= set(overrides.get("datasets", {}))

    # -- metadata -------------------------------------------------------------
    institutions, datasets = {}, {}
    aggregators = set(overrides.get("aggregatorPublishers", {}))

    def institution_from_gbif(org_key):
        org = fetch.gbif_org(org_key)
        if not org:
            return None
        iid = f"gbif-org-{org_key}"
        if iid not in institutions:
            institutions[iid] = {
                "name": org.get("title"),
                "url": (org.get("homepage") or [None])[0],
                "logoSource": org.get("logoUrl"),
                "gbifOrganization": org_key,
                "evidence": f"https://api.gbif.org/v1/organization/{org_key}",
            }
        return iid

    def institution_from_name(name, url=None, evidence=None):
        iid = "org-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        institutions.setdefault(iid, {"name": name, "url": url, "logoSource": None, "evidence": evidence})
        return iid

    for ds in sorted(credited):
        entry = {"id": ds, "title": None, "url": None, "doi": None, "citation": None,
                 "licence": None, "licenceNote": None, "logoSource": None,
                 "creators": [], "institution": None, "section": None, "evidence": []}
        m = manifest.get(ds) or {}
        q = queue.get(ds) or {}
        gbif_uuid = None
        clb_match = CLB_RE.match(ds)
        if clb_match:
            key = clb_match.group(1)
            d = fetch.clb(key)
            if d:
                entry.update({
                    "title": d.get("title"), "alias": d.get("alias"),
                    "url": d.get("url") or f"https://www.checklistbank.org/dataset/{key}",
                    "doi": d.get("doi"), "citation": strip_html(d.get("citation")),
                    "licence": licence_label(d.get("license")), "logoSource": d.get("logo"),
                    "version": d.get("version") or d.get("issued"),
                    "versionDoi": d.get("versionDoi"),
                    "identifiers": d.get("identifier") or [],
                    "gbifKey": d.get("gbifKey"),
                    "orcids": sorted({c["orcid"] for c in (d.get("creator") or []) if c.get("orcid")}),
                    "creators": [c.get("name") or " ".join(filter(None, [c.get("given"), c.get("family")]))
                                 for c in (d.get("creator") or [])][:8],
                })
                entry["evidence"].append({"field": "metadata", "url": f"https://api.checklistbank.org/dataset/{key}",
                                          "checked": d.get("_fetched")})
                gbif_uuid = d.get("gbifKey")
                if d.get("gbifPublisherKey") and d["gbifPublisherKey"] not in aggregators:
                    entry["institution"] = institution_from_gbif(d["gbifPublisherKey"])
                elif d.get("publisher") and (d["publisher"].get("organisation") or d["publisher"].get("name")):
                    p = d["publisher"]
                    entry["institution"] = institution_from_name(
                        p.get("organisation") or p.get("name"), p.get("url"),
                        f"https://api.checklistbank.org/dataset/{key}")
            entry["title"] = entry["title"] or q.get("title") or m.get("title")
        elif ds.startswith("gbif-dataset-"):
            gbif_uuid = ds[len("gbif-dataset-"):]
        elif m:
            entry.update({"title": m.get("title"), "url": m.get("url"), "licence": m.get("licence")})
            ident = " ".join(filter(None, [m.get("identifier"), m.get("url")]))
            doi = re.search(r"10\.\d{4,9}/[^\s;,)]+", ident)
            entry["doi"] = doi.group(0) if doi else None
            uu = UUID_RE.search(m.get("url") or "") if "gbif.org/dataset" in (m.get("url") or "") else None
            gbif_uuid = uu.group(0) if uu else None
            entry["evidence"].append({"field": "metadata", "url": "manifest.json", "checked": None})
        elif ds.startswith("src:"):
            name = ds[4:]
            entry["title"] = name[:1].upper() + name[1:]
            entry["licenceNote"] = aliases.get(name, {}).get("note")
        if gbif_uuid:
            g = fetch.gbif_dataset(gbif_uuid)
            if g:
                entry["title"] = entry["title"] or g.get("title")
                entry["doi"] = entry["doi"] or g.get("doi")
                entry["citation"] = entry["citation"] or (g.get("citation") or {}).get("text")
                entry["url"] = entry["url"] or f"https://www.gbif.org/dataset/{gbif_uuid}"
                entry["evidence"].append({"field": "gbif", "url": f"https://api.gbif.org/v1/dataset/{gbif_uuid}",
                                          "checked": g.get("_fetched")})
                if not entry["institution"] and g.get("publishingOrganizationKey") \
                        and g["publishingOrganizationKey"] not in aggregators:
                    entry["institution"] = institution_from_gbif(g["publishingOrganizationKey"])
        if m.get("licence") and norm_licence(m["licence"]) != norm_licence(entry["licence"] or ""):
            entry["licenceNote"] = f"recorded at import: {m['licence']}"
        elif m.get("licence") and len(m["licence"]) > len(entry["licence"] or ""):
            entry["licenceNote"] = m["licence"]

        am = archive_meta(ds)
        if am:
            entry["asTaken"] = am
            # The licence that governs our copy is the one the archive we took
            # states; ChecklistBank's is today's and may have changed since.
            taken = am.get("licenceUrl") or am.get("licence")
            if norm_licence(taken):
                if entry["licence"] and norm_licence(entry["licence"]) != norm_licence(taken):
                    entry["licenceNote"] = (f"licence of the version we took ({am.get('version') or am['taken']}); "
                                            f"ChecklistBank today: {entry['licence']}")
                entry["licence"] = licence_label(taken) + (
                    f" {v.group(1)}" if (v := re.search(r"/(\d\.\d)", taken or "")) else "")
        ov = overrides.get("datasets", {}).get(ds, {})
        entry.update({k: v for k, v in ov.items() if not k.startswith("_") and k != "institution"})
        if not entry["institution"]:
            # The dataset stands as its own institution.
            iid = f"self-{ds}"
            institutions[iid] = {"name": entry["title"] or ds, "url": entry["url"],
                                 "logoSource": entry["logoSource"], "self": True, "evidence": None}
            entry["institution"] = iid
        if not entry["section"]:
            if m.get("status") in NOMENCLATURE_STATUSES or (
                    ds not in species and ds not in text and not ((q.get("applied") or {}).get("added"))):
                entry["section"] = "nomenclature"
            else:
                entry["section"] = "records"
        datasets[ds] = entry

    for iid, ov in overrides.get("institutions", {}).items():
        institutions.setdefault(iid, {}).update({k: v for k, v in ov.items() if not k.startswith("_")})
        institutions[iid]["evidence"] = ov.get("_why") or "data/contributors-overrides.json"
    # Institution overrides last, so they can name any institution the
    # registry knows -- including one only another dataset brought in.
    for ds, ov in overrides.get("datasets", {}).items():
        iid = ov.get("institution")
        if not iid or ds not in datasets:
            continue
        if iid not in institutions and iid.startswith("gbif-org-"):
            institution_from_gbif(iid[len("gbif-org-"):])
        if iid in institutions:
            datasets[ds]["institution"] = iid
        else:
            print(f"  WARN  override for {ds}: no institution {iid!r}", file=sys.stderr)

    # A self-institution card takes its dataset's logo; others their own.
    used = {d["institution"] for d in datasets.values()}
    institutions = {k: v for k, v in institutions.items() if k in used}
    for iid, inst in institutions.items():
        if not inst.get("logoSource"):
            mine = sorted((d for d in datasets.values() if d["institution"] == iid and d.get("logoSource")),
                          key=lambda d: -sum(species.get(d["id"], {}).values()))
            if mine and (inst.get("self") or len({d["institution"] for d in mine}) == 1):
                inst["logoSource"] = mine[0]["logoSource"]
        if args.no_logos:
            inst["logo"] = None
            continue
        inst["logo"] = fetch_logo(inst.get("logoSource"), args.offline, args.refresh)
        if not inst["logo"]:
            icon = site_icon(inst.get("url"), args.offline, args.refresh)
            if icon:
                inst["logo"] = fetch_logo(icon, args.offline, args.refresh)
                if inst["logo"]:
                    inst["logoSource"], inst["logoFrom"] = icon, "the site's own icon"

    # -- licence cross-check --------------------------------------------------
    # Three statements per source: what we recorded (queue row / manifest),
    # what the archive we took says (asTaken), and what ChecklistBank says
    # now. A difference between the last two means the source was relicensed
    # after we took it.
    rows = [(k, "queue", r.get("stage"), r.get("licence")) for k, r in sorted(queue.items())]
    rows += [(k, "manifest", v.get("status"), v.get("licence")) for k, v in sorted(manifest.items())]
    checks = []
    for key, where, stage, recorded in rows:
        mm = CLB_RE.match(key)
        d = fetch.clb(mm.group(1)) if mm else None
        now = d.get("license") if d else None
        am = archive_meta(key)
        taken = am.get("licenceUrl") or am.get("licence") if am else None
        n_rec, n_taken, n_now = norm_licence(recorded), norm_licence(taken), norm_licence(now)
        flags = []
        if n_taken and n_rec != n_taken:
            flags.append("recorded differs from the archive")
        if n_taken and n_now and n_taken != n_now:
            flags.append("relicensed since taken")
        if not n_taken and n_now and n_rec != n_now:
            flags.append("recorded differs from ChecklistBank (archive states none)")
        if any(x and "nc" in x for x in (n_taken, n_now)) and not (n_rec and "nc" in n_rec):
            flags.append("NC not recorded")
        if not (n_rec or n_taken or n_now):
            flags.append("no licence anywhere")
        if flags:
            checks.append({"key": key, "where": where, "stage": stage,
                           "title": (d or {}).get("title"),
                           "url": f"https://www.checklistbank.org/dataset/{mm.group(1)}/about" if mm else None,
                           "recorded": recorded, "asTaken": taken, "asTakenVersion": (am or {}).get("version"),
                           "asTakenFile": f"{am['archive']}:{am['file']}" if am else None,
                           "checklistbank": now, "flags": flags})
    _write(CROSSCHECK, {"generatedAt": _now(),
                        "note": "recorded (queue row / manifest) vs asTaken (the archive's own eml.xml / "
                                "metadata.yaml / Metadata.json) vs checklistbank (its licence today)",
                        "mismatches": checks})

    # -- write ---------------------------------------------------------------
    registry = {"generatedAt": _now(), "institutions": institutions, "datasets": datasets}
    _write(REGISTRY, registry)
    for ds, entry in datasets.items():
        q = queue.get(ds) or {}
        a = q.get("applied") or {}
        entry["counts"] = {"species": species.get(ds, {}), "text": text.get(ds, {})}
        entry["addedAtImport"] = a.get("added") if q.get("stage") == "applied" else None
    _write(REPORT, {"generatedAt": _now(), "kingdoms": kingdoms, "totals": totals,
                    "noProvenance": no_provenance, "unrecorded": unrecorded, "keyMap": key_map,
                    "institutions": institutions, "datasets": datasets})

    # What the species panel needs to name a record's sources, without the
    # full report: raw id -> dataset, and per dataset its title/link/licence.
    _write(INDEX, {"generatedAt": _now(), "keyMap": key_map, "datasets": {
        ds: {"title": e["title"], "url": e["url"], "licence": e["licence"],
             "institution": institutions.get(e["institution"], {}).get("name")}
        for ds, e in datasets.items() if ds in set(key_map.values())}})

    print(f"  {len(datasets)} datasets, {len(institutions)} institutions "
          f"({sum(1 for i in institutions.values() if i.get('logo'))} with a logo); "
          f"{fetch.fetched} API documents fetched")
    flag_counts = collections.Counter(f for c in checks for f in c["flags"])
    print(f"  licence cross-check: {len(checks)} sources flagged: "
          + ", ".join(f"{v} {k}" for k, v in flag_counts.most_common()))
    for c in checks:
        if "NC not recorded" in c["flags"] or "relicensed since taken" in c["flags"]:
            print(f"      {c['key']:<22} {c['where']:<8} {str(c['stage']):<10} rec {c['recorded']!r:<16.16} "
                  f"taken {str(c['asTaken'])!r:<40.40} now {c['checklistbank']!r}  {str(c['title'])[:40]}")
    if unknown:
        print(f"  WARN  ids with no manifest entry or alias: {sorted(unknown)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
