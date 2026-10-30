"""Which kingdoms this checkout may write -- the writer partition.

Decided 2026-10-30: bacteria and viruses are imported on q-bert, by its own
import-ordinator and importwrite, while Macie keeps the six portal kingdoms.
The two machines share one git history, so the split has to be enforced at
every writer, not assumed: NCBI, ENA, Wikidata, COL XR and the GBIF Backbone
all mix kingdoms, and a q-bert run applying NCBI would otherwise write
animalia family files that Macie also writes, with the clash surfacing only
at merge time.

`SN_WRITE_KINGDOMS` (comma-separated) names the kingdoms a process may write.
Unset means the six in kingdom-config.json -- so a plain run on Macie never
touches bacteria or viruses, and q-bert sets
`SN_WRITE_KINGDOMS=bacteria,viruses` explicitly. services/importwrite reads
the same variable with the same default.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINGDOM_CONFIG = os.path.join(ROOT, "portal", "data", "kingdom-config.json")
BACTERIA_VIRUSES = ("bacteria", "viruses")


def portal_kingdoms() -> list[str]:
    with open(KINGDOM_CONFIG, encoding="utf-8") as fh:
        return list(json.load(fh)["kingdoms"])


def allowed() -> set[str]:
    raw = os.environ.get("SN_WRITE_KINGDOMS", "").strip()
    if not raw:
        return set(portal_kingdoms())
    return {k.strip().lower() for k in raw.split(",") if k.strip()}


def may_write(kingdom: str) -> bool:
    return (kingdom or "").strip().lower() in allowed()
