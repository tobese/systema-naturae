#!/usr/bin/env python3
"""Apply a transformer's output to the tree via importwrite.

The other half of the split pipeline `record_transformed()` only writes
one side of (sources.py / paths.ts): a transform step writes its output to
`work/<slug>/` without ever talking to importwrite, so transformation and
import can run on different machines, at different times, and the output
can be reviewed or replayed before anything touches the tree. This script
is the "apply" side -- reads that file back, groups it by family and
genus (importwrite wants one POST per genus, within one family), and POSTs
it to the ONE running importwrite instance.

Record shape, one per line (JSONL), written by whatever produced the
file -- this is NOT the same shape `record_transformed()`'s docstring
shows elsewhere (a bare species node); this script needs enough on each
record to route it, because one bulk source archive can span many
families in one run:

    {
      "kingdom": "animalia", "phylum": "...", "class": "...", "order": "...",
      "family": "<appSlug>",
      "genus": "Panthera",
      "species": { ...opaque species node, same shape POSTed to importwrite... }
    }

`genus` may also be an object -- {"name", "id"?, "sourcedFrom"?,
"lineage"?, "description"?} -- when the transformer has more to say about
it than just its name; a bare string is shorthand for {"name": that}.
`kingdom` and `family` are required on every record; `phylum`/`class`/
`order` are optional the same way importwrite's own request is, and
`genus` falls back to the species node's own `lineage` field if omitted
entirely.

Usage:
    IMPORTWRITE_URL=http://localhost:8089 \\
        python3 scripts/importTransformed.py <work-slug> [name]

`work-slug` is the SOURCE's work-dir slug (sources.py's `work_dir`, not a
family slug) -- the same one `record_transformed()` was called with.
`name` defaults to "transformed.jsonl".
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importwriteClient as iw  # noqa: E402
import sources  # noqa: E402


def genus_ref(g) -> dict:
    """Normalize a record's `genus` field to a full genusRef dict."""
    if isinstance(g, str):
        g = {"name": g}
    name = g.get("name", "") if isinstance(g, dict) else ""
    ref = {"id": g.get("id") or f"GENUS_{name.upper()}", "name": name}
    for k in ("sourcedFrom", "lineage", "description"):
        if isinstance(g, dict) and g.get(k):
            ref[k] = g[k]
    return ref


def load_records(path: str) -> list:
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def group_by_family_genus(records: list) -> dict:
    """(kingdom, phylum, class, order, family) -> genus name -> {ref, species[]}."""
    groups: dict = {}
    for r in records:
        family = r.get("family")
        kingdom = r.get("kingdom")
        if not family or not kingdom:
            raise ValueError(f"record missing required kingdom/family: {r!r}")
        fam_key = (kingdom, r.get("phylum", ""), r.get("class", ""), r.get("order", ""), family)
        species = r["species"]
        ref = genus_ref(r.get("genus") or species.get("lineage") or "Unknown")
        fam = groups.setdefault(fam_key, {})
        bucket = fam.setdefault(ref["name"], {"ref": ref, "species": []})
        bucket["species"].append(species)
    return groups


def apply_groups(groups: dict, *, base_url: str = "") -> dict:
    """POST every (family, genus) group to importwrite, flushing each
    family immediately after its own genera are posted. Returns a summary
    dict.

    Flushing inline (rather than batching all flushes after every family's
    POSTs, as a prior version did) closes the window a small family can sit
    idle in server memory while a much bigger one in the same run is still
    being POSTed -- long enough for IMPORTWRITE_IDLE_EVICT to reclaim it --
    and it means one family's POST or flush failure can no longer abort the
    whole run before earlier families get their own flush call at all. Both
    happened in the same run: the 2026-10-19 wtaxa-1039 import evicted
    brachyceridae while curculionidae (85k species) was still being posted,
    then crashed on brachyceridae's end-of-run flush with
    "404 family not loaded" -- which, in the old structure, also skipped the
    flush for every family a plain `set`'s iteration order placed after it,
    silently dropping 252 already-posted species.
    """
    added = merged = cross_family = 0
    touched = set()
    for (kingdom, phylum, cls, order, family), genera in groups.items():
        for _genus_name, bucket in genera.items():
            result = iw.post_genus(
                family, kingdom, bucket["ref"], bucket["species"],
                phylum=phylum, cls=cls, order=order, base_url=base_url)
            added += len(result.get("added", []))
            merged += len(result.get("merged", []))
            for m in result.get("merged", []):
                if m.get("family") and m["family"] != family:
                    cross_family += 1
        iw.flush(family, base_url=base_url)
        touched.add(family)

    return {"added": added, "merged": merged, "crossFamily": cross_family, "families": touched}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/importTransformed.py <work-slug> [name]")
        return 2
    work_slug = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "transformed.jsonl"

    if not iw.IMPORTWRITE_URL:
        print("FATAL: IMPORTWRITE_URL is not set.")
        return 1

    path = sources.work_file(work_slug, name)
    meta_file = sources.meta_path_for(path)
    if os.path.exists(meta_file):
        with open(meta_file, encoding="utf-8") as fh:
            meta = json.load(fh)
        print(f"  run {meta.get('runId', '?')} from {meta.get('source', work_slug)}"
              f" ({meta.get('recordCount', '?')} records, transformed {meta.get('transformedAt', '?')})")

    records = load_records(path)
    print(f"  {len(records)} records in {path}")

    groups = group_by_family_genus(records)
    summary = apply_groups(groups)

    print(f"  importwrite: {summary['added']} added, {summary['merged']} merged"
          f" ({summary['crossFamily']} already existed in a different family)")
    fam_count = len(summary['families'])
    print(f"  flushed {fam_count} famil{'y' if fam_count == 1 else 'ies'}")
    return 0


def _selftest() -> int:
    import http.server
    import tempfile
    import threading

    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else None
            requests.append((self.path, body))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if self.path.endswith("/species"):
                genus_name = body["genus"]["name"]
                payload = {
                    "added": [{"name": s["name"], "id": s.get("id", ""), "uuid": "11111111-1111-4111-8111-111111111111"}
                              for s in body["species"]],
                    "merged": [],
                    "genusCreated": genus_name != "Already",
                }
            else:
                payload = {"wrote": True}
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        # Three records: two different genera in one family (miraciidae),
        # one in a different family (diosaccidae) -- exactly the shape a
        # bulk ChecklistBank run spanning multiple families would produce.
        # The second record's genus is given as a bare string, the fallback
        # shorthand for {"name": that}.
        records = [
            {"kingdom": "animalia", "phylum": "arthropoda", "class": "copepoda",
             "order": "harpacticoida", "family": "miraciidae",
             "genus": {"name": "Amonardia", "id": "GENUS_AMONARDIA"},
             "species": {"name": "Amonardia similis", "rank": "SPECIES"}},
            {"kingdom": "animalia", "phylum": "arthropoda", "class": "copepoda",
             "order": "harpacticoida", "family": "miraciidae",
             "genus": "Diosaccus",
             "species": {"name": "Diosaccus borborocoetus", "rank": "SPECIES"}},
            {"kingdom": "animalia", "phylum": "arthropoda", "class": "copepoda",
             "order": "incertae_sedis", "family": "diosaccidae",
             "genus": "Diosaccus",
             "species": {"name": "Diosaccus other", "rank": "SPECIES"}},
        ]

        groups = group_by_family_genus(records)
        assert len(groups) == 2, f"expected 2 family groups, got {len(groups)}"
        mirac_key = ("animalia", "arthropoda", "copepoda", "harpacticoida", "miraciidae")
        assert set(groups[mirac_key].keys()) == {"Amonardia", "Diosaccus"}
        assert groups[mirac_key]["Amonardia"]["ref"]["id"] == "GENUS_AMONARDIA"
        assert groups[mirac_key]["Diosaccus"]["ref"]["id"] == "GENUS_DIOSACCUS"  # derived, not given

        base = f"http://127.0.0.1:{port}"
        summary = apply_groups(groups, base_url=base)
        assert summary["added"] == 3, summary
        assert summary["families"] == {"miraciidae", "diosaccidae"}

        paths = [p for p, _ in requests]
        assert paths.count("/family/miraciidae/species") == 2  # one per genus
        assert paths.count("/family/diosaccidae/species") == 1
        assert paths.count("/family/miraciidae/flush") == 1  # once per family, not per genus
        assert paths.count("/family/diosaccidae/flush") == 1

        # A record missing kingdom/family must fail loudly, not silently
        # drop into some default placement.
        try:
            group_by_family_genus([{"species": {"name": "x"}}])
            assert False, "expected ValueError for a record missing kingdom/family"
        except ValueError:
            pass

        # load_records / meta sidecar round-trip through the real
        # sources.py work-dir resolution, not just the in-memory functions
        # above.
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SN_SOURCES_ROOT"] = tmp
            with open(os.path.join(tmp, "manifest.json"), "w", encoding="utf-8") as fh:
                fh.write('{"sources":{}}')
            import importlib
            importlib.reload(sources)
            written = sources.record_transformed(
                "selftest-source", "transformed.jsonl", records, source="selftest-source")
            loaded = load_records(sources.work_file("selftest-source", "transformed.jsonl"))
            assert loaded == records
            assert written == sources.work_file("selftest-source", "transformed.jsonl")
            del os.environ["SN_SOURCES_ROOT"]
            importlib.reload(sources)
    finally:
        server.shutdown()

    print("importTransformed.py selftest ok")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    sys.exit(main())
