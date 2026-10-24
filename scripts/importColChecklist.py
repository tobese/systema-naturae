#!/usr/bin/env python3
"""Import a ChecklistBank per-checklist export into family files we already hold.

Scaffolding is deliberately not implemented. Both datasets this was written for
turn out to land entirely inside families the tree already has -- Craneflies adds
376 species to Limoniidae and 2 to Tipulidae, ReptileDB adds 1 to Scincidae --
so the only operation needed is part A of `importColStage2.py`: hand
`merge_family` a synthetic genus/species root and let it add what is missing.
Rather than implement placement and guess it untested, anything that would need a
new family is counted and refused, and the run says so.

**A refused species is dropped, not placed.** It gets no family of its own, no
`Incertae sedis` placeholder, and no node anywhere in the tree. That is a
deliberate difference from `importColStage2.py`, whose part C does exactly that:
COL offers enough family-less species (23,536 of them in Animalia) that a
placeholder is the least-wrong answer, and an explicitly unplaced family asserts
only that we could not place it. Here the counts do not justify it -- 21 species
in FLOW, 207 in Moss TROPICOS, 4 in ReptileDB -- so a placeholder family would be
a directory and a colour theme per handful of names, and the families are real
and findable in the source. They stay out until someone decides to scaffold them,
which is a taxonomy decision rather than a data one.

The overlap is the headline, and it was measured against the tree rather than
against the canonical index, which is a snapshot taken before the Stage 2
import and reports 15,563 "new" Cranefly species that are in fact already on disk:

    Craneflies   16,061 species -> 15,683 already held, 378 new
    ReptileDB    15,612 species -> 15,611 already held,   1 new

Nothing here filters on `status`: in this export shape Name.tsv carries no
usable status (all 34,366 ReptileDB rows have it empty) and the accepted/synonym
split lives in Synonym.tsv, which `colChecklist.load()` already applies.

Ids are minted with `importSpeciesFile.node_id`, so a species added here gets
the same id the other importers would give it and cannot collide with one added
by COL.

    python3 scripts/importColChecklist.py <archive.zip>            # dry run
    python3 scripts/importColChecklist.py <archive.zip> --apply
"""
import argparse
import collections
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import colChecklist as K  # noqa: E402
import importSpeciesFile as SF  # noqa: E402
import sources as _sources  # noqa: E402
import taxamatch  # noqa: E402

KINGDOM_CONFIG = "portal/data/kingdom-config.json"
# Fallback only. A source's own kingdom comes from its rank chain, because
# portal/data/taxonomy.json is animalia alone -- looking for Fabaceae in it
# refuses all 3,024 of ILDIS' legume species as needing a new family when the
# tree already holds Fabaceae with 24,496 species.
FALLBACK_KINGDOM = "animalia"
SOURCE = "checklistbank"
FORMS = ("{g} \u00d7{s}", "{g} {s}", "{g} \u00d7{s}", "{g} \u00d7 {s}")

# Data, not code -- same convention as verifyTree.py's allowlists
# (data/known-same-kingdom-duplicates.json etc.): a flat {usageKey: reason}
# map of GBIF Backbone taxa whose OWN parent chain resolves to the wrong
# kingdom/family -- a homonymous genus in a different kingdom than the one
# this species actually belongs to (Fallacia fawensis is a diatom; GBIF's
# own chain for usageKey 11466599 walks up through the beetle genus
# Fallacia in Cerambycidae instead). route_species() only cross-checks a
# conflicting placement against what we already hold (the `r.diffs` path);
# a species with nothing to hold -- because the wrong copy was deleted --
# gets staged fresh under whatever GBIF's chain says, with no diff logged
# at all. Found 2026-10-23 when the same 3 species kept reappearing every
# gbif-backbone re-import; see BACKLOG.md. Load failure is fatal, same
# reasoning as verifyTree.py's loader: a missing file is not the same as
# an empty one.
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "known-bad-gbif-backbone-placements.json"),
          encoding="utf-8") as _f:
    KNOWN_BAD_GBIF_BACKBONE_PLACEMENTS = set(json.load(_f).keys())


def _routing_cache_path(archive):
    base, _ = os.path.splitext(archive)
    return base + ".routing-cache.parquet"


def _load_routing_cache(archive, default_k):
    """-> {taxon_id: row}, or {} if missing/stale/wrong default_k.

    Caches the EXPENSIVE, archive-derived part of route_species()'s
    per-candidate work (name parsing + K.chain()'s parent-walk) so a
    re-import of an unchanged archive -- which is what the pending-family
    watcher does every cycle -- doesn't pay it again for candidates whose
    archive-side routing can't have changed. What DOES need to stay fresh
    every run (not cached): whether we currently hold that species
    (ON_DISK) and whether we currently hold that family (KINDS) -- those
    are exactly what a re-run exists to notice.

    Valid only when newer than the archive (same convention as
    colChecklist.py's taxa cache) AND built under the same `default_k`:
    a few candidates per archive route through the `elif DEFAULT_K`
    fallback, so a cache built under one --kingdom override (or none)
    isn't safe to reuse under a different one -- rather than track that
    per-row, the whole cache is invalidated if it doesn't match."""
    path = _routing_cache_path(archive)
    if not (os.path.exists(path) and os.path.getsize(path) > 0
            and os.path.getmtime(path) >= os.path.getmtime(archive)):
        return {}
    try:
        import duckdb
    except ImportError:
        return {}
    try:
        con = duckdb.connect()
        rel = con.sql(f"SELECT * FROM read_parquet({path!r})")
        cols = rel.columns
        rows = rel.fetchall()
    except Exception as e:
        print(f"  (routing cache unreadable, ignoring: {e})")
        return {}
    if "default_k" not in cols or "id" not in cols:
        return {}
    out = {}
    default_k_idx = cols.index("default_k")
    for row in rows:
        if row[default_k_idx] != default_k:
            return {}  # built under a different --kingdom; whole cache invalid
        d = dict(zip(cols, row))
        out[d["id"]] = d
    return out


def _write_routing_cache(cache_rows, archive, default_k):
    """cache_rows: {taxon_id: row_dict (no 'id'/'default_k' keys -- added
    here)}. Same .tmp-then-rename pattern as colChecklist.py's taxa
    cache, for the same reason (found 2026-10-23: a kill mid-write
    truncated a different file outright when it wasn't atomic)."""
    if not cache_rows:
        return
    try:
        import duckdb
        import tempfile
    except ImportError:
        return
    path = _routing_cache_path(archive)
    fd, tmp = tempfile.mkstemp(suffix=".jsonl", dir=os.path.dirname(path) or ".")
    tmp_out = path + ".tmp"
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for tid, row in cache_rows.items():
                rec = dict(row)
                rec["id"] = tid
                rec["default_k"] = default_k
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        con = duckdb.connect()
        con.execute(
            f"COPY (SELECT * FROM read_json_auto({tmp!r}, sample_size=500000)) "
            f"TO {tmp_out!r} (FORMAT PARQUET)")
        os.replace(tmp_out, path)
    except Exception as e:
        print(f"  (routing cache write skipped: {e})")
    finally:
        os.unlink(tmp)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)


def _ondisk_cache_path(kingdom):
    """Outside the repo, on the sources volume -- same convention as
    pendingFamilies.py's store, derived/local, never committed."""
    d = os.path.join(_sources.ROOT, "ondisk-species-index")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{kingdom}.parquet")


def _load_ondisk_cache(kingdom):
    """-> {family_slug: {'mtime', 'size', 'ids'}}, or {} if missing/unreadable.

    Per-family-file granularity, keyed by (mtime, size) on that one
    file -- same two-factor freshness check buildData.ts's own
    per-family `.build-cache/families/<slug>.json` already uses, applied
    here to the species-id extraction `route_species()`'s ON_DISK scan
    does instead of the grafted-subtree extraction buildData.ts does.
    Measured 2026-10-24: scanning+parsing all 24,148 family files across
    six kingdoms took 88s by itself, the dominant cost of a repeat
    archive import (ON_DISK is rebuilt from scratch on every single
    route_species() call, archive-independent) -- this is what actually
    needs caching, not (only) the archive-side routing work."""
    path = _ondisk_cache_path(kingdom)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    try:
        import duckdb
        con = duckdb.connect()
        rel = con.sql(f"SELECT * FROM read_parquet({path!r})")
        cols = rel.columns
        rows = rel.fetchall()
    except Exception as e:
        print(f"  (on-disk species cache unreadable, ignoring: {e})")
        return {}
    out = {}
    for row in rows:
        d = dict(zip(cols, row))
        out[d["slug"]] = {"mtime": d.get("mtime"), "size": d.get("size"),
                           "ids": list(d.get("ids") or [])}
    return out


def _write_ondisk_cache(kingdom, entries):
    """entries: {family_slug: {'mtime', 'size', 'ids'}} -- every family
    slug currently on disk for this kingdom, one way or another (cache
    hit or freshly re-parsed); a slug that no longer exists on disk is
    never in `entries` to begin with, so it naturally drops out of the
    cache rather than needing an explicit removal step. Same
    .tmp-then-rename pattern as the other caches."""
    if not entries:
        return
    try:
        import duckdb
        import tempfile
    except ImportError:
        return
    path = _ondisk_cache_path(kingdom)
    fd, tmp = tempfile.mkstemp(suffix=".jsonl", dir=os.path.dirname(path) or ".")
    tmp_out = path + ".tmp"
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for slug, e in entries.items():
                rec = {"slug": slug, "mtime": e["mtime"], "size": e["size"],
                       "ids": e["ids"]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        con = duckdb.connect()
        con.execute(
            f"COPY (SELECT * FROM read_json_auto({tmp!r}, sample_size=500000)) "
            f"TO {tmp_out!r} (FORMAT PARQUET)")
        os.replace(tmp_out, path)
    except Exception as e:
        print(f"  (on-disk species cache write skipped: {e})")
    finally:
        os.unlink(tmp)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)


def slug_hint(archive):
    """A stable short identifier for the source, for the pending store.

    The ChecklistBank dataset key when the container carries one, else the
    archive filename. Two runs of the same archive must produce the same string
    or the pending store accumulates duplicate rows for one source.
    """
    try:
        m = K.metadata(archive)
    except Exception:
        m = {}
    key = m.get("key") or m.get("alias") or m.get("title")
    if not key:
        key = os.path.basename(archive).rsplit(".", 1)[0]
    return re.sub(r"[^a-z0-9]+", "-", str(key).lower()).strip("-")[:40]


def taxonomy_input(kingdom):
    """Path to a kingdom's taxonomy file, from kingdom-config.json.

    Not derived from the kingdom's name: Plantae's input is
    taxonomy-plantae-snippet.json and Animalia's is plain taxonomy.json.
    """
    cfg = json.load(open(KINGDOM_CONFIG, encoding="utf-8"))["kingdoms"]
    k = (kingdom or FALLBACK_KINGDOM).lower()
    if k not in cfg:
        sys.exit(f"FATAL: kingdom {k!r} is not in kingdom-config.json. "
                 f"Declared: {', '.join(sorted(cfg))}")
    return os.path.join("portal", cfg[k]["input"]), k


def our_families(kingdom=None, quiet=False):
    """lower-cased family name -> (appSlug, node)"""
    path, k = taxonomy_input(kingdom)
    if not quiet:
        print(f"  taxonomy input: {path}  (kingdom {k})")
    tax = json.load(open(path, encoding="utf-8"))
    out = {}

    def walk(n):
        if n.get("rank") == "FAMILY" and n.get("appSlug"):
            out[(n.get("name") or n["appSlug"]).lower()] = (n["appSlug"], n)
        for c in n.get("children") or []:
            walk(c)
    walk(tax)
    return tax, out


class RoutedSpecies:
    """Everything route_species() decided, shared by every caller that
    reads a ColDP/DwC-A archive -- the direct-write importer below and
    transformColChecklist.py's split-pipeline transform step. Neither
    re-derives kingdom routing, family matching, or refusal detection;
    both get it from here, so the two paths cannot quietly disagree
    about where a species belongs."""

    def __init__(self):
        self.meta = {}
        self.source_key = SOURCE
        self.staged = collections.defaultdict(list)  # (kingdom, slug) -> [(genus, bare, authorship, source_id, family_name)]
        self.missed = collections.Counter()           # (kingdom, family) -> count
        self.fam_source_ids = collections.defaultdict(set)
        self.cand_count = 0
        self.held = self.refused = self.nonb = self.unresolved = 0
        self.known_bad_skipped = 0
        self.no_family = collections.Counter()
        self.diffs = []                               # (kingdom, id, name, our_slug, source_slug, source_family, source_id)
        self.routed = collections.Counter()
        self.routed_by_kingdom = self.routed_by_family = self.routed_unknown = 0
        self.src_kingdom = None
        self.default_k = ""
        self.kinds = {}
        # Taxa whose kingdom AND family both failed to resolve (the honest
        # UNRESOLVED KINGDOM bucket) -- grouped by family name, since that is
        # the one thing we do know about them and the one thing worth
        # searching other datasets for later. {fam_raw: {"owners": set(),
        # "count": int, "samples": [(name, tid), ...]}}. See
        # record_unresolved() for the on-disk form.
        self.unresolved_detail = {}


def route_species(archive, kingdom_override="") -> RoutedSpecies:
    """Read `archive`, resolve each accepted species/subspecies to a
    (kingdom, family slug) in our taxonomy or a refusal, same logic for
    every caller. Pure routing -- no file writes, no pendingFamilies
    recording (callers decide when a decision is final enough for that:
    importColChecklist.py's main() only records on --apply, and
    transformColChecklist.py follows the same rule)."""
    r = RoutedSpecies()
    r.meta = K.metadata(archive)
    print(f"  {r.meta.get('title') or os.path.basename(archive)}  "
          f"({r.meta.get('version') or 'no version'}, {r.meta.get('license') or 'no licence'})")

    # ChecklistBank's own taxon ids are only unique WITHIN one dataset --
    # small sequential integers that two unrelated datasets routinely
    # reuse. A bare "checklistbank" sourceIds key let importwrite's
    # cross-identity matching (by (source, id) pair, see services/
    # importwrite/identity.go) treat two different species from different
    # datasets as the same one whenever their dataset-local ids collided --
    # found 2026-10-19 when a WTaxa (1039) id collided with an unrelated
    # species already in curculionidae, silently absorbing the new one
    # into the old one's node instead of adding it. Scoping the key by
    # dataset closes that; it only affects the sourceIds identity key, not
    # the sourcedFrom display field, so it does not change which species we
    # already consider "held" (that check hashes name+authorship, not this).
    #
    # r.meta (the archive's own metadata.yaml/eml.xml, when it has one) is
    # NOT used for this -- WTaxa's own archive carries none, metadata() just
    # returns {}. The archive's containing directory is manifest.json's own
    # key for this source (every "archive" entry there is "archives/<key>",
    # confirmed across the whole manifest), on disk whether or not the
    # archive embeds metadata, so it's the one dataset identifier this
    # function can always derive.
    dataset_key = os.path.basename(os.path.dirname(os.path.abspath(archive)))
    r.source_key = dataset_key or SOURCE

    taxa, _names, _ = K.load_cached(archive)
    by_id = {t["id"]: t for t in taxa}
    # .get(), not bracket access: a cached taxon dict is reconstructed from
    # a parquet sidecar and isn't guaranteed to carry every core key the
    # same way a freshly-parsed one does (found 2026-10-23 -- checklistbank-
    # 2011 had 103 taxa lose their `rank` key through an earlier version of
    # that round-trip and crashed the whole archive's import outright).
    cand = [t for t in taxa
            if (t.get("rank") or "").lower() in ("species", "subspecies")
            and t.get("name") and not t.get("is_synonym")]
    r.cand_count = len(cand)
    print(f"  accepted species/subspecies offered: {len(cand):,}")

    placed = set()

    # Diagnostic only -- "the first candidate (of up to 200) that happens to
    # carry a kingdom in its own chain". Do NOT feed this into DEFAULT_K: for
    # a multi-kingdom archive (GBIF Backbone, Wikispecies) it is one archive-
    # order accident, not a property of the archive, and using it as the
    # fallback kingdom for every taxon whose OWN kingdom and family name both
    # fail to resolve mislabels the refusal's true kingdom. Found 2026-10-24:
    # both backbone.zip and wikispecies/archive.zip happened to probe
    # "Plantae" first, so every such refusal -- even unambiguously
    # non-plant ones (Cicindelidae/Animalia, Pseudomonadaceae/Bacteria,
    # Diploschistaceae/Fungi) -- got filed as "[plantae] <family>" in
    # pendingFamilies.py's store. No species was ever mis-imported by this
    # (a refusal stays a refusal either way), but it corrupted the
    # bookkeeping of what is actually missing from which kingdom. The
    # UNRESOLVED KINGDOM path below already exists and already reports this
    # honestly -- the fix is to let taxa reach it instead of papering over
    # them with this probe's guess.
    src_kingdom = None
    probe = {t["id"]: t for t in taxa}
    for t in cand[:200]:
        c = K.chain(t, probe)
        if c.get("kingdom"):
            src_kingdom = c["kingdom"]
            break
    r.src_kingdom = src_kingdom

    KINDS = {}
    for k in ("animalia", "plantae", "fungi", "chromista", "protozoa", "archaea"):
        KINDS[k] = our_families(k, quiet=True)
    r.kinds = KINDS

    # Only an explicit --kingdom override asserts "treat this whole archive
    # as kingdom X" -- that is a human's informed claim about a source (e.g.
    # LCVP, which is plant-only and carries no kingdom field at all). The
    # auto-probed src_kingdom above is not that; see the comment above it.
    DEFAULT_K = (kingdom_override or "").lower()
    if DEFAULT_K and DEFAULT_K not in KINDS:
        sys.exit(f"FATAL: --kingdom {DEFAULT_K!r} is not one of "
                  f"{', '.join(sorted(KINDS))}")
    r.default_k = DEFAULT_K

    import glob as _glob
    ON_DISK = {}
    for k in KINDS:
        ondisk_cache = _load_ondisk_cache(k)
        new_ondisk_cache = {}
        ids = {}
        on_cache_hits = on_cache_misses = 0
        for f in _glob.glob(f"taxonomy/{k}/**/src/data/*.json", recursive=True):
            slug = os.path.basename(f)[:-5]
            try:
                st = os.stat(f)
            except OSError:
                continue
            cached = ondisk_cache.get(slug)
            if (cached is not None and cached.get("mtime") == st.st_mtime
                    and cached.get("size") == st.st_size):
                on_cache_hits += 1
                file_ids = cached["ids"]
            else:
                on_cache_misses += 1
                try:
                    d = json.load(open(f, encoding="utf-8"))
                except Exception:
                    continue
                file_ids = []
                stack = list(d.get("children") or [])
                while stack:
                    nd = stack.pop()
                    if nd.get("rank") == "SPECIES" and nd.get("id"):
                        file_ids.append(nd["id"])
                    stack.extend(nd.get("children") or [])
            new_ondisk_cache[slug] = {"mtime": st.st_mtime, "size": st.st_size,
                                       "ids": file_ids}
            for sid in file_ids:
                ids[sid] = slug
        ON_DISK[k] = ids
        _write_ondisk_cache(k, new_ondisk_cache)
        print(f"  {k:10s} families {len(KINDS[k][1]):>7,}   species on disk {len(ids):>9,}"
              f"   (file cache: {on_cache_hits:,} hits, {on_cache_misses:,} misses)")
    print(f"  source kingdom (first taxon with one): {src_kingdom or '(none)'}")

    parsed = taxamatch.parse_names(sorted({t["name"] for t in cand}))

    FAM2K = collections.defaultdict(set)
    for k, (_t, fams_k) in KINDS.items():
        for fam in fams_k:
            FAM2K[fam].add(k)

    # Caches the expensive, archive-derived half of this loop (name
    # parsing + K.chain()'s parent-walk) across repeated runs of an
    # unchanged archive -- see _load_routing_cache()'s docstring. What is
    # NOT cached, and must stay fresh every run: ON_DISK (do we currently
    # hold this species) and KINDS (do we currently hold this family) --
    # that is exactly what re-running an archive exists to notice.
    routing_cache = _load_routing_cache(archive, DEFAULT_K)
    new_cache_rows = {}
    cache_hits = 0

    for t in cand:
        tid = t.get("id") or ""
        if tid in KNOWN_BAD_GBIF_BACKBONE_PLACEMENTS:
            r.known_bad_skipped += 1
            continue

        cached = routing_cache.get(tid)
        if cached is not None:
            cache_hits += 1
            routed_via = cached.get("routed_via")
            if routed_via == "nonbinomial":
                r.nonb += 1
                continue
            bare, g, sid = cached.get("bare"), cached.get("g"), cached.get("sid")
            fam_raw, fam, k = cached.get("fam_raw"), cached.get("fam"), cached.get("k")
            fid = cached.get("fid")
        else:
            nm = t["name"]
            g, s = taxamatch.bare_binomial(nm, parsed)
            if not g or not s:
                r.nonb += 1
                new_cache_rows[tid] = {"routed_via": "nonbinomial"}
                continue
            bare = taxamatch.bare_name(nm, parsed)
            sid = SF.node_id(SF.PREFIX["SPECIES"], bare, (t.get("authorship") or "").strip() or "")
            ch = K.chain(t, by_id)
            fam_raw = (ch.get("family") or "").strip()
            fam = fam_raw.lower()
            k = (ch.get("kingdom") or "").strip().lower()
            fid = ch.get("family_id")
            if k not in KINDS:
                k = ""
                owners = FAM2K.get(fam) or set()
                if len(owners) == 1:
                    k = next(iter(owners))
                    routed_via = "family"
                elif DEFAULT_K:
                    k = DEFAULT_K
                    routed_via = "default"
                else:
                    routed_via = "unresolved"
            else:
                routed_via = "kingdom"
            new_cache_rows[tid] = {"routed_via": routed_via, "bare": bare, "g": g,
                                    "sid": sid, "fam_raw": fam_raw, "fam": fam,
                                    "k": k, "fid": fid}

        if bare.lower() in placed:
            continue
        placed.add(bare.lower())

        if routed_via == "kingdom":
            r.routed_by_kingdom += 1
        elif routed_via == "family":
            r.routed_by_family += 1
        elif routed_via == "default":
            r.routed_unknown += 1
        elif routed_via == "unresolved":
            r.unresolved += 1
            # Recomputed from FAM2K rather than cached per-row: cheap (FAM2K
            # is a dict already built once per run) and it's grouped by
            # family here, not per-taxon, so this is the one extra lookup
            # for the whole family, not one per taxon.
            owners = FAM2K.get(fam) or set()
            fkey = fam_raw or "(no family)"
            d = r.unresolved_detail.setdefault(
                fkey, {"owners": set(), "count": 0, "samples": []})
            d["owners"] |= owners
            d["count"] += 1
            if len(d["samples"]) < 5:
                d["samples"].append((t.get("name") or bare, tid))
            continue
        r.routed[k] += 1
        fams_k = KINDS[k][1]
        ours = ON_DISK[k].get(sid)
        if ours is not None:
            r.held += 1
            theirs = (fams_k.get(fam) or (None,))[0] if fam else None
            if theirs and ours != theirs:
                r.diffs.append((k, sid, bare, ours, theirs, fam_raw, tid))
            continue
        if fam not in fams_k:
            r.no_family[(k, fam or "(no family)")] += 1
            r.missed[(k, fam)] += 1
            r.refused += 1
            continue
        slug = fams_k[fam][0]
        r.staged[(k, slug)].append((g, bare,
                                    (t.get("authorship") or "").strip() or None,
                                    tid, fam))
        if fid:
            r.fam_source_ids[(k, slug)].add(fid)

    _write_routing_cache(new_cache_rows, archive, DEFAULT_K)
    if routing_cache:
        print(f"  routing cache: {cache_hits:,} of {len(cand):,} candidates "
              f"skipped the archive-side routing work (already known)")

    print("  routed per taxon: " + ", ".join(f"{k} {v:,}" for k, v in r.routed.most_common()))
    print(f"      kingdom from the taxon: {r.routed_by_kingdom:,}"
          f"   from the family name: {r.routed_by_family:,}"
          f"   fell back to {DEFAULT_K or '(none given)'}: {r.routed_unknown:,}")
    if r.unresolved:
        print(f"  UNRESOLVED KINGDOM: {r.unresolved:,} -- no --kingdom given, "
              f"the source carries none, and the family name is unknown or "
              f"ambiguous across kingdoms. Not attributed to one and not "
              f"refused under a specific kingdom either; re-run with "
              f"--kingdom <name> if you know what this source is.")
        print(f"      (recorded in the unresolved-taxa store on --apply; "
              f"see scripts/pendingFamilies.py's sibling store)")
        for fam, d in sorted(r.unresolved_detail.items(),
                              key=lambda kv: -kv[1]["count"])[:10]:
            owners = ",".join(sorted(d["owners"])) or "none held"
            print(f"      {d['count']:>6,}  {fam}  (held under: {owners})")
    print(f"\n  already held (skipped): {r.held:,}")
    print(f"  staged:              {sum(len(v) for v in r.staged.values()):,}")
    print(f"  non-binominal:       {r.nonb:,}")
    if r.known_bad_skipped:
        print(f"  known-bad placements skipped: {r.known_bad_skipped:,}"
              f"  (see data/known-bad-gbif-backbone-placements.json)")
    print(f"  new, into a family we hold: {sum(len(v) for v in r.staged.values()):,}"
          f"  across {len(r.staged)} families in {len({k for k, _ in r.staged})} kingdoms")
    print(f"  REFUSED (would need a new family): {r.refused:,}"
          f"  -- dropped, not placed: no placeholder family, no orphan node")
    print(f"      (these are recorded in the pending-family store; "
          f"see scripts/pendingFamilies.py)")
    for (k, fam), v in r.no_family.most_common(10):
        print(f"      {v:>6,}  [{k}] {fam}")
    return r


def record_misses(r: RoutedSpecies, archive, apply_: bool):
    """Record refusals into the pending-family store -- shared tail for
    both main() and transformColChecklist.py, same rule: only on a real
    apply, never on a dry run (see route_species's docstring)."""
    if r.missed and apply_:
        try:
            import pendingFamilies as PF
        except ImportError:
            PF = None
        if PF:
            recorded = PF.add_families(
                [(fam, k, n) for (k, fam), n in r.missed.items() if fam],
                source=f"{SOURCE}:{slug_hint(archive)}",
                reason="offered by source, family not in taxonomy",
                archive=archive)
            print(f"  recorded {recorded} families in the pending store")
        else:
            print("  ! pendingFamilies.py not importable, misses NOT recorded")
    elif r.missed:
        print(f"  (dry run: {sum(r.missed.values()):,} refusals across "
              f"{len({f for _, f in r.missed if f}):} families would be recorded "
              f"in the pending store)")


# Sibling to pendingFamilies.py's STORE/LINK pattern, same reasoning: derived
# from the archives, weighs more than belongs in git, so it lives on the
# external volume with a gitignored symlink standing in for it in the repo.
UNRESOLVED_STORE = os.path.join(_sources.ROOT, "pending", "unresolved-taxa.jsonl")
UNRESOLVED_LINK = "portal/data/pending-unresolved-taxa.jsonl"


def _ensure_unresolved_link():
    os.makedirs(os.path.dirname(UNRESOLVED_STORE), exist_ok=True)
    if not os.path.exists(UNRESOLVED_STORE):
        open(UNRESOLVED_STORE, "a").close()
    if os.path.islink(UNRESOLVED_LINK):
        if os.readlink(UNRESOLVED_LINK) == UNRESOLVED_STORE:
            return
        os.unlink(UNRESOLVED_LINK)
    elif os.path.exists(UNRESOLVED_LINK):
        raise SystemExit(f"{UNRESOLVED_LINK} exists and is not a symlink -- "
                          f"refusing to replace it; move it aside first")
    os.symlink(UNRESOLVED_STORE, UNRESOLVED_LINK)


def record_unresolved(r: RoutedSpecies, archive, apply_: bool):
    """Persist r.unresolved_detail -- taxa whose kingdom AND family both
    failed to resolve, grouped by family name -- to a sibling of
    pendingFamilies.py's store. A family name is the one fact an unresolved
    taxon still carries, and the one thing worth searching other datasets
    for later: these are orphans that might be adopted by a supporting
    checklist which happens to classify this exact family, not species lost
    for good (see [[project_kingdom_fallback_mislabels_refusals]] in
    project memory for why this bucket exists at all -- it used to be
    silently mislabeled as whatever kingdom the archive's first taxon
    happened to carry, instead of recorded honestly like this).

    Merged across runs the same way pendingFamilies.py merges: keyed by
    family name (lowercased), counts and sample taxa accumulate per
    (family, source) pair rather than overwriting, since different
    archives can each contribute their own stuck taxa under the same
    unresolved family name. Written only on --apply, same rule as
    record_misses()."""
    if not r.unresolved_detail:
        return
    if not apply_:
        print(f"  (dry run: {sum(d['count'] for d in r.unresolved_detail.values()):,} "
              f"unresolved-kingdom taxa across {len(r.unresolved_detail)} "
              f"families would be recorded in the unresolved-taxa store)")
        return
    _ensure_unresolved_link()
    rows = []
    if os.path.getsize(UNRESOLVED_STORE) > 0:
        with open(UNRESOLVED_STORE, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
    index = {row["family"].lower(): row for row in rows}
    source = f"{SOURCE}:{slug_hint(archive)}"
    today = date.today().isoformat()
    added = 0
    for fam, d in r.unresolved_detail.items():
        row = index.get(fam.lower())
        if row is None:
            row = {"family": fam, "owners": [], "bySource": {},
                   "samples": [], "firstSeen": today}
            index[fam.lower()] = row
            added += 1
        row["owners"] = sorted(set(row.get("owners") or []) | d["owners"])
        row["bySource"][source] = d["count"]
        seen = {tuple(s) for s in row.get("samples") or []}
        for s in d["samples"]:
            if s not in seen and len(row["samples"]) < 10:
                row["samples"].append(list(s))
                seen.add(s)
        row["lastSeen"] = today
        row["archive"] = archive
    with open(UNRESOLVED_STORE, "w", encoding="utf-8") as fh:
        for row in index.values():
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  recorded {added} new ({len(index)} total) families in the "
          f"unresolved-taxa store ({UNRESOLVED_STORE})")


def write_placement_diffs(r: RoutedSpecies, path, archive):
    """Write the species this source places in a different family than we do.

    A species already in the tree is skipped by the importer, so an archive's
    classification is normally never compared with ours: the 2026-10 GBIF
    backbone run reported 1,815,344 held species and discarded all of their
    placements unread. That hides real disagreements (a specialist checklist
    puts a species in family A, GBIF in family B) behind an aggregate count.

    The log is per species so the disagreements can be reviewed later; it does
    not change the tree. Not written unless `--diff-log PATH` is passed.
    """
    import datetime as _dt
    names = {}
    for k, (_tax, fams) in r.kinds.items():
        names[k] = {slug: (node.get("name") or name)
                    for name, (slug, node) in fams.items()}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    source = f"{SOURCE}:{slug_hint(archive)}"
    at = _dt.datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as fh:
        for k, sid, bare, ours, theirs, fam_raw, fid in r.diffs:
            fh.write(json.dumps({
                "at": at,
                "source": source,
                "archive": os.path.basename(archive),
                "kingdom": k,
                "speciesId": sid,
                "name": bare,
                "ourFamily": ours,
                "ourFamilyName": names.get(k, {}).get(ours, ""),
                "sourceFamily": fam_raw,
                "sourceFamilySlug": theirs,
                "sourceFamilyId": fid,
            }, ensure_ascii=False) + "\n")
    print(f"  placement diffs vs our tree: {len(r.diffs):,} -> {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--kingdom", default="",
                     help="override kingdom inference entirely for sources "
                          "that carry no kingdom in their own rank chain and "
                          "whose family names don't resolve uniquely (e.g. "
                          "LCVP -- an all-plant database with no kingdom "
                          "field at all -- used to default silently to "
                          "animalia for exactly this reason: a hardcoded "
                          "constant written for a different, narrower bug, "
                          "reused here with no actual justification). "
                          "Pass --kingdom plantae when you know the source.")
    ap.add_argument("--diff-log", default="",
                    help="write one JSON line per species already held under a "
                         "different family than this archive classifies it in "
                         "(read-only; works on dry runs too)")
    args = ap.parse_args()

    r = route_species(args.archive, kingdom_override=args.kingdom)
    meta = r.meta
    record_misses(r, args.archive, args.apply)
    record_unresolved(r, args.archive, args.apply)
    if args.diff_log:
        write_placement_diffs(r, args.diff_log, args.archive)
    staged = r.staged
    KINDS = r.kinds

    if not staged:
        print("\n  nothing to do")
        return 0

    print()
    added_total = dedup_total = 0
    files = None
    for (kind, slug), rows in sorted(staged.items()):
        _tax_k, fams_k = KINDS[kind]
        # the family name, needed by the genera loop below for genus lineage
        fname = next((n for n, v in fams_k.items() if v[0] == slug), slug)
        genera = collections.defaultdict(list)
        for g, nm, a, sid, _fam in rows:
            genera[g].append((nm, a, sid))
        new_root = {"id": None, "name": None, "rank": "FAMILY", "children": []}
        touched_path = None
        for g, species in genera.items():
            gnode = {"id": SF.node_id(SF.PREFIX["GENUS"], g), "name": g,
                     "rank": "GENUS", "children": [], "sourcedFrom": SOURCE,
                     "lineage": fname}
            new_root["children"].append(gnode)
            for nm, a, sid in species:
                sp = {"id": SF.node_id(SF.PREFIX["SPECIES"], nm, a or ""),
                      "name": nm, "rank": "SPECIES", "subspeciesCount": 0,
                      "sourcedFrom": SOURCE, "lineage": g}
                if a:
                    sp["authorship"] = a
                if sid:
                    sp["sourceIds"] = {r.source_key: sid}
                gnode["children"].append(sp)
        # One index, built once. A recursive glob per family means a full walk
        # of a 14,085-file tree per family: 34 families took 7 minutes, which
        # puts Wikispecies' 736 at over two hours for what is a dict lookup.
        if files is None:
            import glob
            files = {}
            for f in glob.glob("taxonomy/*/**/src/data/*.json", recursive=True):
                if "node_modules" in f:
                    continue
                slug_ = os.path.basename(f)[:-5]
                files.setdefault(slug_, []).append(f)
            print(f"  indexed {sum(len(v) for v in files.values()):,} family "
                  f"data files across {len(files):,} slugs")
        hits = files.get(slug, [])
        if len(hits) > 1:
            # Same family name validly placed at two different taxonomic
            # placements (Microsporidia under both Fungi and Protozoa,
            # testate amoebae under both Protozoa and Chromista, etc.) rather
            # than a genuinely duplicated file. `kind` is this row's own
            # kingdom -- narrow to the file under it before giving up.
            kingdom_hits = [h for h in hits
                            if h.split("taxonomy/")[1].split("/")[0] == kind]
            if len(kingdom_hits) == 1:
                hits = kingdom_hits
        if len(hits) != 1:
            print(f"  ! {slug}: {len(hits)} files found, skipping")
            continue
        touched_path = hits[0]
        doc = json.load(open(touched_path, encoding="utf-8"))
        new_root["id"] = doc.get("id")
        new_root["name"] = doc.get("name")
        m = SF.merge_family(
            doc, new_root,
            kingdom=touched_path.split("taxonomy/")[1].split("/")[0],
            family_slug=slug)
        added_total += m.get("species_added", 0)
        dedup_total += m.get("species_deduped", 0)

        # Stamp this archive's own family-rank id onto the family's own root
        # node, the same way species already carry sourceIds (colChecklist.
        # chain() now surfaces it). More than one id feeding one slug means
        # the archive itself disagrees with our tree about what "this family"
        # is -- the Actinocyclidae/Hemidiscaceae class of bug, visible here
        # before a single species crosses into the file.
        fids = r.fam_source_ids.get((kind, slug)) or set()
        fam_id_changed = False
        if len(fids) > 1:
            print(f"    ! {slug}: archive feeds {len(fids)} distinct family "
                  f"ids into this one slug -- possible homonym collision: "
                  f"{sorted(fids)[:5]}")
        elif len(fids) == 1:
            fid = next(iter(fids))
            doc_ids = doc.setdefault("sourceIds", {})
            prior = doc_ids.get(r.source_key)
            if prior != fid:
                if prior:
                    print(f"    ! {slug}: {r.source_key} family id changed "
                          f"{prior} -> {fid}")
                doc_ids[r.source_key] = fid
                fam_id_changed = True

        print(f"    {slug:28s} staged {len(rows):>4,}  added {m.get('species_added', 0):>4,}  "
              f"already present {m.get('species_deduped', 0):>4,}")
        if m.get("authority_conflicts"):
            print(f"    ! {m['authority_conflicts']} species share an "
                  f"authority id with a different family already: "
                  f"{m['authority_conflict_examples'][0]}")
        # Only write what actually gained something. Writing unconditionally
        # reformats every family that was merely scanned -- json.dump re-emits
        # each array one item per line -- and the first run rewrote 75 family
        # files to add 373 species to three of them.
        if args.apply and not m.get("species_added") and not fam_id_changed:
            print(f"      unchanged, not rewritten")
        elif args.apply:
            with open(touched_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            # taxonomy.json's speciesCount is what the Coverage modal reads.
            # Use the same iterator merge_family uses rather than counting here:
            # a hand-rolled count of top-level children counts SUBFAMILY nodes
            # as if they were species, so Aphididae -- whose top-level children
            # are subfamilies -- was written as 193 when it holds 5,873, and 61
            # animalia families came out understating by 103,385 species.
            # Three copies of this counter already existed and disagreed; the
            # fix is to have none.
            n = sum(1 for _ in SF.iter_species(doc))
            fam = fams_k[[n for n, v in fams_k.items() if v[0] == slug][0]][1]
            if fam.get("speciesCount") != n:
                fam["speciesCount"] = n
            print(f"      {touched_path}  speciesCount -> {n}")

    print(f"\n  species added: {added_total:,}   already present: {dedup_total:,}")

    # A durable record of what this run did, so the post-import gate reads
    # numbers rather than scraped stdout. Every serious defect in Oct 2026 was a
    # plausible number rather than an error, and the number that would have
    # caught two of them is the refusal rate: WFO refused 0.26% and ITIS 5.5%,
    # both healthy, while a run refusing 60% looks identical at exit 0. Written
    # on --apply only, because a dry run changed nothing.
    if args.apply:
        import datetime as _dt
        row = {
            "at": _dt.datetime.now().isoformat(timespec="seconds"),
            "source": SOURCE,
            "archive": os.path.basename(args.archive),
            "archivePath": args.archive,
            "slugHint": slug_hint(args.archive),
            "title": meta.get("title") or "",
            "offered": r.cand_count,
            "alreadyHeld": r.held,
            "nonBinominal": r.nonb,
            "staged": sum(len(v) for v in staged.values()),
            "refused": r.refused,
            "refusalRate": round(r.refused / max(1, r.cand_count), 4),
            "added": added_total,
            "deduped": dedup_total,
            "families": len(staged),
            "kingdoms": sorted({k for k, _ in staged}),
            "missedFamilies": len({f for _kk, f in r.missed if f}),
        }
        log = os.path.join("data", "import-log.jsonl")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  recorded {log}")

    if args.apply:
        for kind in sorted({k for k, _ in staged}):
            _tax_k, _ = KINDS[kind]
            tp, _kk = taxonomy_input(kind)
            with open(tp, "w", encoding="utf-8") as fh:
                json.dump(_tax_k, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            print(f"  wrote {tp}")
    else:
        print("\n  (dry run -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())