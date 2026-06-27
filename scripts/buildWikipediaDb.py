#!/usr/bin/env python3
import bz2
import json
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INDEX = "/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream-index.txt.bz2"
DEFAULT_DUMP_DIR = "/Volumes/MacieExternal/enwiki"
DEFAULT_NAMES = "/Volumes/WikiDump/work/species-names.json"
DEFAULT_DB = "/Volumes/WikiDump/wiki-pages.sqlite"

TITLE_RE = re.compile(r"^([^:]+):(\d+):(.*)$")

# Infobox templates we care about. Match opens "{{Speciesbox" / "{{Taxobox" etc.
INFOBOX_START_RE = re.compile(
    r"\{\{\s*(Speciesbox|Subspeciesbox|Taxobox|Automatic[\s_]+taxobox|Infobox\s+(?:bird|fish|insect|reptile|amphibian))\b",
    re.IGNORECASE,
)
# Fields we extract from infoboxes.
INFOBOX_FIELDS = (
    "image", "image_caption", "image2", "image2_caption",
    "range_map", "range_map_caption", "range_map2", "range_map2_caption",
    "status", "status_system", "status_ref",
    "binomial", "binomial2", "trinomial",
)


def load_candidates(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return set(data["candidates"])


def stream_index(path: str):
    with bz2.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":", 2)
            if len(parts) != 3:
                continue
            offset, page_id, title = parts
            try:
                yield int(offset), int(page_id), title
            except ValueError:
                continue


def strip_wikitext(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<ref[^>]*>.*?</ref>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<ref[^/]*/>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\{\{[^{}]*\}\}", " ", text)
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"''+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_lead(text: str) -> str | None:
    if not text:
        return None
    text = re.split(r"\n==[^=]", text, maxsplit=1)[0]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for para in paragraphs:
        cleaned = strip_wikitext(para)
        if len(cleaned) > 40 and re.search(r"[A-Za-z]", cleaned):
            sentence = re.split(r"(?<=[.!?])\s+", cleaned)[0].strip()
            if sentence and not sentence.endswith((".", "!", "?")):
                sentence += "."
            return sentence
    return None


def find_infobox_span(text: str):
    """Locate the first species/taxon infobox in `text`. Returns (start, end)
    indices spanning from the opening `{{` to the matching `}}`, or None.
    Uses brace counting so nested templates inside values don't break us."""
    m = INFOBOX_START_RE.search(text)
    if not m:
        return None
    start = m.start()
    depth = 0
    i = start
    n = len(text)
    while i < n:
        if text[i] == "{" and i + 1 < n and text[i + 1] == "{":
            depth += 1
            i += 2
            continue
        if text[i] == "}" and i + 1 < n and text[i + 1] == "}":
            depth -= 1
            i += 2
            if depth == 0:
                return start, i
            continue
        i += 1
    return None


def split_infobox_args(body: str):
    """Split infobox body on top-level `|` (ignoring those inside [[]] and {{}})."""
    args = []
    buf = []
    depth_brace = 0
    depth_link = 0
    for ch in body:
        if ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace = max(0, depth_brace - 1)
        elif ch == "[":
            depth_link += 1
        elif ch == "]":
            depth_link = max(0, depth_link - 1)
        elif ch == "|" and depth_brace == 0 and depth_link == 0:
            args.append("".join(buf))
            buf.clear()
            continue
        buf.append(ch)
    args.append("".join(buf))
    return args


def clean_value(v: str) -> str:
    """Lightly clean an infobox value: strip wikilinks but keep their display
    text, drop refs/comments, collapse whitespace. For File:/Image: links we
    keep just the bare filename."""
    v = re.sub(r"<ref[^>]*>.*?</ref>", "", v, flags=re.S | re.I)
    v = re.sub(r"<ref[^/]*/>", "", v, flags=re.I)
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    # [[File:Foo.jpg|thumb|caption]] -> Foo.jpg
    v = re.sub(r"\[\[(?:File|Image):([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", v, flags=re.I)
    # Regular wikilinks -> display text
    v = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"''+", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    # Strip leading File:/Image: prefix if value was just "File:foo.jpg"
    v = re.sub(r"^(?:File|Image):\s*", "", v, flags=re.I)
    return v


def parse_infobox(text: str):
    """Extract a small set of fields from the first species/taxon infobox.
    Returns None if no infobox is found or no recognised fields present."""
    span = find_infobox_span(text)
    if span is None:
        return None
    start, end = span
    body = text[start + 2 : end - 2]
    args = split_infobox_args(body)
    if not args:
        return None
    args = args[1:]  # skip the template name
    out = {}
    for arg in args:
        if "=" not in arg:
            continue
        k, _, v = arg.partition("=")
        k = k.strip().lower()
        if k in INFOBOX_FIELDS:
            cleaned = clean_value(v)
            if cleaned:
                out[k] = cleaned
    return out or None


def build_targets(index_path: str, candidates: set[str]):
    titles = {}
    for offset, page_id, title in stream_index(index_path):
        if title in candidates:
            titles[title] = offset
    return titles


def parse_dump(dump_path: str, wanted: set[str], conn: sqlite3.Connection):
    seen = 0
    matched = 0
    with_infobox = 0
    with_range = 0
    batch = []

    with bz2.open(dump_path, "rb") as fh:
        context = ET.iterparse(fh, events=("end",))
        for _, elem in context:
            if elem.tag.endswith("page"):
                seen += 1
                title_el = elem.find("./{*}title")
                rev_el = elem.find("./{*}revision/{*}text")
                title = title_el.text if title_el is not None and title_el.text else None
                text = rev_el.text if rev_el is not None and rev_el.text else None
                if title and title in wanted and text:
                    matched += 1
                    info = parse_infobox(text)
                    if info:
                        with_infobox += 1
                        if "range_map" in info:
                            with_range += 1
                    info_json = json.dumps(info, ensure_ascii=False) if info else None
                    batch.append((title, None, extract_lead(text), info_json, text))
                    if len(batch) >= 200:
                        conn.executemany(
                            "INSERT OR REPLACE INTO pages(title, description, extract, infobox_json, content) VALUES(?, ?, ?, ?, ?)",
                            batch,
                        )
                        conn.commit()
                        batch.clear()
                elem.clear()
                if seen % 50000 == 0:
                    print(
                        f"seen={seen} matched={matched} infobox={with_infobox} range={with_range}",
                        flush=True,
                    )

    if batch:
        conn.executemany(
            "INSERT OR REPLACE INTO pages(title, description, extract, infobox_json, content) VALUES(?, ?, ?, ?, ?)",
            batch,
        )
        conn.commit()

    print(f"Done. seen={seen} matched={matched} infobox={with_infobox} range={with_range}")


def main() -> int:
    index_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INDEX
    dump_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DUMP_DIR
    names_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_NAMES
    db_path = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_DB

    candidates = load_candidates(names_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pages ("
        "title TEXT PRIMARY KEY, description TEXT, extract TEXT, "
        "infobox_json TEXT, content TEXT"
        ")"
    )
    # Allow re-running over an older DB that lacks the new column.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(pages)").fetchall()}
    if "infobox_json" not in cols:
        conn.execute("ALTER TABLE pages ADD COLUMN infobox_json TEXT")
    conn.execute("DELETE FROM pages")

    print(f"Indexing candidates from {index_path}...", flush=True)
    wanted = build_targets(index_path, candidates)
    print(f"Matched {len(wanted)} titles in dump index.", flush=True)

    dump_path = os.path.join(dump_dir, "enwiki-20260601-pages-articles-multistream.xml.bz2")
    if not os.path.exists(dump_path):
        print(f"Missing dump file: {dump_path}", file=sys.stderr)
        return 1

    parse_dump(dump_path, set(wanted), conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_title ON pages(title)")
    conn.commit()
    print(f"DB written to {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
