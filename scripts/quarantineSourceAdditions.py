#!/usr/bin/env python3
"""Remove additions that only one source supports, keeping enrichments and
additions corroborated by any other source.

The specific case this was written for is the 2026-10-25 Wikidata Species
import (ChecklistBank dataset 314569, source id
``ac5f72cf-172d-4eb4-ad8c-db66ea1c78e5``), which was applied while the source
was still on hold.  A species is removed only when it is absent from HEAD and
its ``sourceIds`` contains that source and nothing else.  A species that
already existed at HEAD is never removed, even if the import enriched it with
the same source id.  Additions that also carry another source's id stay.

The transform is intentionally conservative:

* it compares against ``HEAD``, not against a remembered list of ids;
* it removes a genus only when the genus itself is absent from HEAD and is
  empty after the species removal;
* it restores a modified file that is not valid JSON from HEAD only when
  ``--restore-corrupt`` is passed (the 2026-10-25 run left exactly one:
  Roccellaceae);
* it updates family root ``speciesCount``/``genusCount`` and the portal
  skeleton's family ``speciesCount`` for every changed family, because the
  importer writes those fields from the live file count;
* every write is atomic (temp file + ``os.replace``), and the whole run holds
  ``maintenanceLock.hold_exclusive()`` so no pipeline pass can interleave.

Dry run by default.  ``--apply`` writes.  A per-family JSONL report and a JSON
summary are written when ``--report`` / ``--summary`` are passed; the report is
also useful in dry-run mode.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree as T  # noqa: E402
from maintenanceLock import hold_exclusive  # noqa: E402

DEFAULT_SOURCE_ID = "ac5f72cf-172d-4eb4-ad8c-db66ea1c78e5"
SPECIES = "SPECIES"
GENUS = "GENUS"
FAMILY = "FAMILY"


def log(msg: str) -> None:
    print(msg, flush=True)


def norm(value: str | None) -> str:
    return (value or "").strip().lower()


def walk_with_parent(root):
    stack = [(None, root)]
    while stack:
        parent, node = stack.pop()
        yield parent, node
        for child in reversed(node.get("children") or []):
            stack.append((node, child))
        for child in reversed(node.get("speciesList") or []):
            stack.append((node, child))


def count_species(node) -> int:
    return T.count_species(node)


def count_genera(node) -> int:
    return T.count_rank(node, GENUS)


class CatFile:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def get(self, sha: str) -> bytes:
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.proc.stdin.write(sha.encode() + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3:
            raise RuntimeError(f"git cat-file failed for {sha}: {header!r}")
        size = int(header[2])
        data = self.proc.stdout.read(size)
        self.proc.stdout.read(1)
        return data

    def close(self):
        if self.proc.stdin:
            self.proc.stdin.close()
        self.proc.wait()


def git_modified_family_files(base: str = "") -> list[str]:
    if base:
        raw = subprocess.check_output(
            ["git", "diff", "--name-only", "-z", base, "--", "taxonomy"]
        )
        return sorted({
            p for p in raw.decode().split("\0")
            if p.endswith(".json") and "/src/data/" in p and os.path.exists(p)
        })
    raw = subprocess.check_output(
        ["git", "status", "--porcelain", "-z", "--", "taxonomy"]
    )
    paths = []
    for entry in raw.split(b"\0"):
        if len(entry) < 4:
            continue
        text = entry.decode()
        if text[1] != "M":
            continue
        path = text[3:]
        if path.startswith("taxonomy/") and path.endswith(".json") and "/src/data/" in path:
            paths.append(path)
    return sorted(set(paths))


def git_head_blobs(base: str = "") -> dict[str, str]:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "-z", base, "--", "taxonomy"] if base
        else ["git", "ls-files", "-s", "-z", "--", "taxonomy"]
    )
    blobs = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        # ls-tree: "<mode> blob <sha>"; ls-files -s: "<mode> <sha> <stage>"
        fields = meta.split()
        blobs[path.decode()] = (fields[2] if base else fields[1]).decode()
    return blobs


def atomic_write(path: str, data: bytes) -> None:
    directory = os.path.dirname(path)
    mode = os.stat(path).st_mode if os.path.exists(path) else 0o644
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".quarantine-", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def json_bytes(doc) -> bytes:
    return (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def remove_nodes(parents, remove: set[int]) -> None:
    if not remove:
        return
    for node in parents:
        if node.get("children"):
            node["children"] = [c for c in node["children"] if id(c) not in remove]
        if node.get("speciesList"):
            node["speciesList"] = [c for c in node["speciesList"] if id(c) not in remove]


def prune_new_empty_genera(root, old_genus_ids: set[str], removed: list[str]) -> None:
    def visit(node):
        if "children" not in node:
            return
        for child in list(node.get("children") or []):
            visit(child)
        kept = []
        for child in node.get("children") or []:
            is_new = child.get("rank") == GENUS and child.get("id") not in old_genus_ids
            empty = count_species(child) == 0 and not (
                child.get("children") or child.get("speciesList")
            )
            if is_new and empty:
                removed.append(child.get("id") or child.get("name") or "?")
                continue
            kept.append(child)
        node["children"] = kept

    visit(root)


def portal_index(kingdom: str) -> tuple[dict | None, dict | None]:
    try:
        root = T.load_kingdom_taxonomy(kingdom)
    except (FileNotFoundError, KeyError):
        return None, None
    by_id = {}
    by_key = {}

    def visit(node, ancestors):
        if node.get("rank") == FAMILY:
            for label in (node.get("name"), node.get("appSlug")):
                if label:
                    by_key.setdefault((ancestors, norm(label)), node)
            if node.get("id"):
                by_id.setdefault(node["id"], node)
        for child in node.get("children") or []:
            visit(child, ancestors + (norm(node.get("name")),))

    visit(root, ())
    return root, {"by_id": by_id, "by_key": by_key}


def source_key_for(path: str, doc) -> tuple[str, tuple[str, ...]]:
    parts = path.split("/")
    kingdom = parts[1]
    # Include the kingdom: portal_index() keys ancestors from the kingdom
    # root down, so dropping it here made the name fallback never match.
    ancestors = tuple(norm(x) for x in parts[1:-4])
    return kingdom, ancestors


def find_portal_node(indexes, ancestors, root_ids, name, slug):
    by_id = indexes.get("by_id", {})
    by_key = indexes.get("by_key", {})
    for root_id in root_ids:
        if root_id and root_id in by_id:
            return by_id[root_id]
    for label in (name, slug):
        if label:
            node = by_key.get((ancestors, norm(label)))
            if node is not None:
                return node
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore-corrupt", action="store_true",
                    help="restore a modified family file that is not valid JSON from HEAD")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--base", default="",
                    help="compare against this commit instead of HEAD -- needed when "
                         "the source's additions were already committed (2026-10-26)")
    ap.add_argument("--report", default="")
    ap.add_argument("--summary", default="")
    args = ap.parse_args()

    t0 = time.time()
    source_id = args.source_id
    paths = git_modified_family_files(args.base)
    if args.limit:
        paths = paths[: args.limit]
    log(f"{len(paths)} modified family files")

    head_blobs = git_head_blobs(args.base)
    cat = CatFile()
    report = open(args.report, "w", encoding="utf-8") if args.report else None

    keysets = collections.Counter()
    overall = collections.Counter()
    changed_files = []
    missing_portal = []
    restored = []
    skipped = []
    affected = []

    log("scanning" if not args.apply else "applying")
    for i, path in enumerate(paths, 1):
        if i % 500 == 0:
            log(f"  {i}/{len(paths)}  {time.time()-t0:.0f}s")

        blob = head_blobs.get(path)
        if not blob:
            skipped.append((path, "no HEAD blob"))
            continue
        old_raw = cat.get(blob)
        try:
            old = json.loads(old_raw)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"HEAD is not valid JSON for {path}: {exc}") from exc

        current = None
        corrupt = False
        try:
            with open(path, "rb") as fh:
                current_raw = fh.read()
            current = json.loads(current_raw)
        except Exception as exc:  # noqa: BLE001
            corrupt = True
            if not args.restore_corrupt:
                skipped.append((path, f"invalid JSON: {exc}"))
                overall["skipped_corrupt"] += 1
                continue
            current = old
            current_raw = old_raw
            restored.append(path)
            overall["restored_corrupt"] += 1

        old_species = {
            n.get("id") for _p, n in walk_with_parent(old)
            if n.get("rank") == SPECIES and n.get("id")
        }
        old_genera = {
            n.get("id") for _p, n in walk_with_parent(old)
            if n.get("rank") == GENUS and n.get("id")
        }

        parents = [n for _p, n in walk_with_parent(current)
                   if n.get("children") or n.get("speciesList")]
        remove = set()
        added = removed = kept_other = kept_mixed = 0
        removed_genera = []

        if not corrupt:
            for _parent, node in walk_with_parent(current):
                if node.get("rank") != SPECIES:
                    continue
                nid = node.get("id")
                if nid and nid in old_species:
                    continue
                added += 1
                src = node.get("sourceIds") or {}
                keys = tuple(sorted(src.keys()))
                keysets[keys] += 1
                if set(src.keys()) == {source_id}:
                    remove.add(id(node))
                    removed += 1
                else:
                    if source_id in src:
                        kept_mixed += 1
                    else:
                        kept_other += 1
            remove_nodes(parents, remove)
            prune_new_empty_genera(current, old_genera, removed_genera)

        old_sc = old.get("speciesCount")
        old_sc_total = count_species(old)
        new_sc_total = count_species(current)
        changed_counts = False
        count_changed = isinstance(old_sc, int) and isinstance(new_sc_total, int) and old_sc != new_sc_total
        if count_changed:
            # Only treat a count difference as a file change when it accompanies
            # removals; a later import that changed counts without removals
            # should not trigger an unnecessary rewrite.
            changed_counts = True
        new_sc = new_sc_total
        genus_changed = bool(removed_genera) and isinstance(current.get("genusCount"), int)
        if not corrupt and remove:
            current["speciesCount"] = new_sc
            if isinstance(old.get("speciesCount"), int) and old["speciesCount"] != new_sc:
                changed_counts = True
            if genus_changed:
                current["genusCount"] = count_genera(current)

        changed = corrupt or bool(remove) or bool(removed_genera) or changed_counts
        if changed:
            changed_files.append(path)
            kingdom, ancestors = source_key_for(path, current)
            affected.append({
                "path": path,
                "kingdom": kingdom,
                "ancestors": ancestors,
                "root_ids": (old.get("id"), current.get("id")),
                "name": current.get("name"),
                "slug": os.path.basename(path)[:-5],
                "new_sc": new_sc,
            })
            if args.apply:
                atomic_write(path, current_raw if corrupt else json_bytes(current))

        overall["files_processed"] += 1
        overall["files_changed"] += int(changed)
        overall["added_species"] += added
        overall["removed_species"] += removed
        overall["kept_other_source"] += kept_other
        overall["kept_mixed_source"] += kept_mixed
        overall["removed_genera"] += len(removed_genera)

        if report:
            report.write(json.dumps({
                "path": path,
                "kingdom": source_key_for(path, current)[0],
                "family": current.get("name"),
                "old_species": len(old_species),
                "new_species": new_sc,
                "added_species": added,
                "removed_species": removed,
                "kept_other_source": kept_other,
                "kept_mixed_source": kept_mixed,
                "removed_genera": len(removed_genera),
                "old_speciesCount": old_sc,
                "new_speciesCount": current.get("speciesCount"),
                "restored": corrupt,
            }, ensure_ascii=False) + "\n")

    if report:
        report.close()
    cat.close()

    portal_updated = 0
    if affected:
        log(f"updating {len(affected)} portal family nodes")
        for kingdom in sorted({a["kingdom"] for a in affected}):
            root, indexes = portal_index(kingdom)
            if root is None:
                missing_portal.extend([item for item in affected if item["kingdom"] == kingdom])
                continue
            kingdom_changed = False
            for item in affected:
                if item["kingdom"] != kingdom:
                    continue
                node = find_portal_node(
                    indexes,
                    item["ancestors"], item["root_ids"],
                    item["name"], item["slug"],
                )
                if node is None:
                    missing_portal.append(item["path"])
                    continue
                if node.get("speciesCount") != item["new_sc"]:
                    node["speciesCount"] = item["new_sc"]
                    kingdom_changed = True
                    portal_updated += 1
            if kingdom_changed and args.apply:
                portal_path = os.path.join(T.ROOT, T.kingdom_input(kingdom))
                atomic_write(portal_path, json_bytes(root))

    elapsed = time.time() - t0
    summary = {
        "source_id": source_id,
        "apply": args.apply,
        "modified_files": len(paths),
        "files_processed": overall["files_processed"],
        "files_changed": overall["files_changed"],
        "restored_corrupt": overall["restored_corrupt"],
        "skipped_corrupt": overall["skipped_corrupt"],
        "skipped": skipped,
        "restored": restored,
        "added_species": overall["added_species"],
        "removed_species": overall["removed_species"],
        "kept_other_source": overall["kept_other_source"],
        "kept_mixed_source": overall["kept_mixed_source"],
        "removed_genera": overall["removed_genera"],
        "portal_nodes_updated": portal_updated,
        "portal_nodes_missing": missing_portal,
        "source_keysets": [
            {"keys": list(k), "count": v}
            for k, v in keysets.most_common()
        ],
        "elapsed_seconds": round(elapsed, 1),
    }
    log(json.dumps(summary, indent=1))
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    with hold_exclusive():
        sys.exit(main())
