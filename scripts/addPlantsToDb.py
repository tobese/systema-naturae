#!/usr/bin/env python3
"""
Append Wikipedia species articles to wiki-pages.sqlite.

One sequential pass over the multistream bz2 dump.  Uses regex instead
of XML parser to extract pages by title — much faster than ET.iterparse.

Inserts ANY page with a species infobox that isn't already in the DB,
serving all kingdoms (plants, fungi, protists, missing animals, …).

Usage:
  python3 scripts/addPlantsToDb.py
"""
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time


DUMP = "/Volumes/MacieExternal/enwiki/enwiki-20260601-pages-articles-multistream.xml.bz2"
LBZIP2 = "/usr/local/bin/lbzip2"
DB_PATH = "/Volumes/WikiDump/wiki-pages.sqlite"

INFOBOX_START_RE = re.compile(
    r"\{\{\s*(Speciesbox|Subspeciesbox|Taxobox|Automatic[\s_]+taxobox|Infobox\s+(?:bird|fish|insect|reptile|amphibian))\b",
    re.IGNORECASE,
)
INFOBOX_FIELDS = frozenset({
    "image", "image_caption", "image2", "image2_caption",
    "range_map", "range_map_caption", "range_map2", "range_map2_caption",
    "status", "status_system", "status_ref",
    "binomial", "binomial2", "trinomial",
})
# Pre-filter: only process pages whose title looks like a binomial.
BINOMIAL_RE = re.compile(r"^[A-Z][a-z]+ [a-z][a-z]+$")
# Extract the title from a <page> chunk.
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
# Extract wikitext from <revision>/<text>.
TEXT_RE = re.compile(r"<revision>.*?<text[^>]*>(.*?)</text>", re.S)

MAX_PAGE_LEN = 2 * 1024 * 1024  # Skip pages > 2 MB (lists/disambiguation pages)
PAGE_TIMEOUT_S = 5               # Kill process if a single page takes > 5 s
WATCHDOG_INTERVAL_S = 30         # Kill process if no progress for 30 s


class TimeoutException(Exception):
    pass


def _alarm_handler(signum, frame):
    raise TimeoutException("page processing timeout")


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
    m = INFOBOX_START_RE.search(text)
    if not m:
        return None
    start = m.start()
    i = start
    n = len(text)
    depth = 0
    while i < n:
        if text[i] == "{" and i + 1 < n and text[i + 1] == "{":
            depth += 1
            i += 2
        elif text[i] == "}" and i + 1 < n and text[i + 1] == "}":
            depth -= 1
            i += 2
            if depth == 0:
                return start, i
        else:
            i += 1
    return None


def split_infobox_args(body: str):
    args = []
    buf: list[str] = []
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
    v = re.sub(r"<ref[^>]*>.*?</ref>", "", v, flags=re.S | re.I)
    v = re.sub(r"<ref[^/]*/>", "", v, flags=re.I)
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    v = re.sub(r"\[\[(?:File|Image):([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", v, flags=re.I)
    v = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", v)
    v = re.sub(r"''+", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    v = re.sub(r"^(?:File|Image):\s*", "", v, flags=re.I)
    return v


def parse_infobox(text: str):
    span = find_infobox_span(text)
    if span is None:
        return None
    start, end = span
    body = text[start + 2 : end - 2]
    args = split_infobox_args(body)
    if not args:
        return None
    args = args[1:]
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


def main() -> int:
    if not os.path.exists(DUMP):
        print(f"Missing: {DUMP}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pages ("
        "title TEXT PRIMARY KEY, description TEXT, extract TEXT, "
        "infobox_json TEXT, content TEXT"
        ")"
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(pages)").fetchall()}
    if "infobox_json" not in cols:
        conn.execute("ALTER TABLE pages ADD COLUMN infobox_json TEXT")

    existing = set(
        row[0] for row in conn.execute("SELECT title FROM pages").fetchall()
    )
    print(f"Existing pages: {len(existing)}", flush=True)

    seen = 0
    inserted = 0
    with_infobox = 0
    with_range = 0
    batch = []
    next_progress = 10000
    chunk_size = 4 * 1024 * 1024  # 4 MB decompressed chunks
    leftover = ""

    # Mutable container so the watchdog thread sees live updates
    _state = {"seen": 0, "inserted": 0}

    # Watchdog: kill process if seen hasn't advanced for N seconds
    def watchdog():
        last = _state["seen"]
        while True:
            time.sleep(WATCHDOG_INTERVAL_S)
            if _state["seen"] == last:
                print(
                    f"\n[HANG] No progress for {WATCHDOG_INTERVAL_S}s "
                    f"(seen={_state['seen']}, inserted={_state['inserted']}). Aborting.",
                    flush=True,
                )
                os._exit(1)
            last = _state["seen"]

    threading.Thread(target=watchdog, daemon=True).start()

    # SIGALRM catches slow Python-level work (Unix only)
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _alarm_handler)

    chunk_idx = 0
    t0 = time.time()
    proc = subprocess.Popen(
        [LBZIP2, "-dc", DUMP],
        stdout=subprocess.PIPE,
        bufsize=chunk_size * 2,
    )
    assert proc.stdout is not None
    fh = proc.stdout

    while True:
        raw = fh.read(chunk_size)
        if not raw:
            if leftover:
                text = leftover
                eof = True
            else:
                break  # normal EOF
        else:
            text = raw.decode("utf-8", errors="replace")
            text = leftover + text
            # Find the last </page> boundary to avoid splitting a page
            last_boundary = text.rfind("</page>")
            if last_boundary < 0:
                leftover = text
                continue
            to_process = text[: last_boundary + 7]
            leftover = text[last_boundary + 7:]
            eof = False

        # On EOF, process whatever remains in leftover
        if eof:
            to_process = text

        # Walk through <page>…</page> pairs sequentially.
        pos = 0
        while True:
            page_start = to_process.find("<page>", pos)
            if page_start < 0:
                break
            page_end = to_process.find("</page>", page_start)
            if page_end < 0:
                break
            page_text = to_process[page_start:page_end + 7]
            pos = page_end + 7

            _state["seen"] += 1
            if len(page_text) > MAX_PAGE_LEN:
                continue

            m = TITLE_RE.search(page_text)
            if not m:
                continue
            title = m.group(1).strip()
            if not BINOMIAL_RE.match(title):
                continue
            if title in existing:
                continue

            if hasattr(signal, "SIGALRM"):
                signal.alarm(PAGE_TIMEOUT_S)
            try:
                m2 = TEXT_RE.search(page_text)
                if not m2:
                    if hasattr(signal, "SIGALRM"):
                        signal.alarm(0)
                    continue
                wikitext = m2.group(1)
                wikitext = wikitext.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

                info = parse_infobox(wikitext)
                if info is None:
                    if hasattr(signal, "SIGALRM"):
                        signal.alarm(0)
                    continue
                with_infobox += 1
                if "range_map" in info:
                    with_range += 1
                info_json = json.dumps(info, ensure_ascii=False)
                batch.append((title, None, extract_lead(wikitext), info_json, wikitext))
                existing.add(title)
                _state["inserted"] += 1
            except TimeoutException:
                print(f"  [TIMEOUT] page took >{PAGE_TIMEOUT_S}s: {title}", flush=True)
                continue
            finally:
                if hasattr(signal, "SIGALRM"):
                    signal.alarm(0)

            if len(batch) >= 200:
                conn.executemany(
                    "INSERT OR IGNORE INTO pages(title, description, extract, infobox_json, content) VALUES(?, ?, ?, ?, ?)",
                    batch,
                )
                conn.commit()
                batch.clear()

        chunk_idx += 1
        if eof:
            break

        if _state["seen"] >= next_progress:
            elapsed = time.time() - t0
            rate = _state["seen"] / elapsed if elapsed > 0 else 0
            print(
                f"chunk={chunk_idx} seen={_state['seen']} inserted={_state['inserted']} "
                f"infobox={with_infobox} range={with_range} "
                f"rate={rate:.0f}p/s",
                flush=True,
            )
            next_progress += 10000

    fh.close()
    ret = proc.wait()
    if ret != 0:
        print(f"lbzip2 exited with code {ret}", file=sys.stderr)

    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO pages(title, description, extract, infobox_json, content) VALUES(?, ?, ?, ?, ?)",
            batch,
        )
        conn.commit()

    conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_title ON pages(title)")
    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    conn.close()

    elapsed = time.time() - t0
    print(f"\nDone!  ({elapsed:.0f}s)")
    print(f"  Pages scanned: {_state['seen']}")
    print(f"  Newly inserted: {_state['inserted']}")
    print(f"  With infobox: {with_infobox}")
    print(f"  With range map: {with_range}")
    print(f"  Total DB size: {final_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
