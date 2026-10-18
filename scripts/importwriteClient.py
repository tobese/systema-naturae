#!/usr/bin/env python3
"""HTTP client for the importwrite service (services/importwrite).

Mirrors postGenusToImportWrite/flushImportWrite in
portal/scripts/fetchSpeciesFromApi.ts and fetchFromChecklistBank.ts -- the
Python side of the same wire contract, so a Python importer gets the same
single-writer, cross-family-aware merge behaviour the TypeScript ones
already have (services/importwrite/README.md's "Identity / merge rules").

Not wired into any importer yet. The COL/GTDB/NCBI family
(importColStage2.py, importGtdbBacteria.py, importNcbiBacteriaViruses.py,
...) shares importSpeciesFile.py's own merge_family() -- a sophisticated,
battle-tested, in-memory tree merge with its own id/name matching and
authority-conflict detection. Retrofitting that to delegate per-genus to
importwrite is a bigger, separate piece of work: merge_family operates on
a whole assembled family tree at once, while importwrite wants one genus's
species per request, so the retrofit is a loop restructuring, not a
drop-in swap, and it touches every importer that shares that function.
This module exists so that work has a tested client to call into when it
happens, not to do it.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

IMPORTWRITE_URL = os.environ.get("IMPORTWRITE_URL", "")


class ImportWriteError(RuntimeError):
    pass


def _post(path: str, body: dict | None = None, *, base_url: str = "") -> dict:
    url = (base_url or IMPORTWRITE_URL)
    if not url:
        raise ImportWriteError("IMPORTWRITE_URL is not set")
    data = json.dumps(body).encode("utf-8") if body is not None else b""
    req = urllib.request.Request(
        url.rstrip("/") + path, data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise ImportWriteError(f"POST {path} failed: {e.code} {detail}") from e
    except urllib.error.URLError as e:
        raise ImportWriteError(f"POST {path} failed: {e}") from e


def post_genus(slug: str, kingdom: str, genus: dict, species: list, *,
               phylum: str = "", cls: str = "", order: str = "",
               base_url: str = "") -> dict:
    """POST one genus's species to importwrite.

    `genus` is {"id", "name"} plus optionally "sourcedFrom"/"lineage"/
    "description". `species` is a list of node dicts, passed through
    opaquely except for the handful of fields importwrite's merge logic
    reads (id, name, rank, sourceIds, uuid, ...).

    Returns {"added": [...], "merged": [...], "genusCreated": bool}, each
    list holding {"name", "id", "uuid"?, "family"?} objects. A "family" on
    a merged entry means the species was already found in a DIFFERENT
    family and merged there instead of being added here -- see
    services/importwrite/crossfamily.go.
    """
    return _post(f"/family/{slug}/species", {
        "kingdom": kingdom, "phylum": phylum, "class": cls, "order": order,
        "genus": genus, "species": species,
    }, base_url=base_url)


def flush(slug: str, *, base_url: str = "") -> dict:
    """Force an immediate disk write (+ git commit if the server has that
    enabled) for `slug` instead of waiting for its next flush tick."""
    return _post(f"/family/{slug}/flush", base_url=base_url)


def _selftest() -> int:
    import http.server
    import threading

    received = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 (stdlib's naming, not ours)
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            received.append((self.path, json.loads(body) if body else None))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if self.path.endswith("/species"):
                payload = {
                    "added": [{"name": "Testus novus", "id": "SP_TESTUS_NOVUS", "uuid": "11111111-1111-4111-8111-111111111111"}],
                    "merged": [{"name": "Testus revisus", "id": "SP_TESTUS_REVISUS", "uuid": "22222222-2222-4222-8222-222222222222", "family": "otherfamily"}],
                    "genusCreated": True,
                }
            else:
                payload = {"wrote": True}
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def log_message(self, *a):  # silence
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        result = post_genus(
            "testidae", "animalia",
            {"id": "GENUS_TESTUS", "name": "Testus"},
            [{"name": "Testus novus"}, {"name": "Testus revisus"}],
            phylum="chordata", base_url=base,
        )
        assert result["genusCreated"] is True
        assert len(result["added"]) == 1 and result["added"][0]["uuid"]
        assert len(result["merged"]) == 1 and result["merged"][0]["family"] == "otherfamily"

        path, sent = received[0]
        assert path == "/family/testidae/species"
        assert sent["kingdom"] == "animalia"
        assert sent["phylum"] == "chordata"
        assert sent["genus"]["name"] == "Testus"
        assert len(sent["species"]) == 2

        flush_result = flush("testidae", base_url=base)
        assert flush_result["wrote"] is True
        assert received[1][0] == "/family/testidae/flush"

        try:
            post_genus("x", "animalia", {}, [], base_url="http://127.0.0.1:1")
            assert False, "expected ImportWriteError for an unreachable server"
        except ImportWriteError:
            pass
    finally:
        server.shutdown()

    print("importwriteClient.py selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
