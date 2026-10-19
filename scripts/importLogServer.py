#!/usr/bin/env python3
"""Web dashboard for data/import-log.jsonl -- the human-friendly sibling of
importLogView.py's terminal table, for watching a run of several imports in
a row without squinting at a monospace table.

Reuses importLogView.py's row-loading and problem/note logic directly
rather than re-deriving it -- the same reason scripts/taxaserve.py exists:
one place answers the question, everything else asks it.

Usage:
    python3 scripts/importLogServer.py                 # serve on :9883
    python3 scripts/importLogServer.py --port 9883
    open http://localhost:9883/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importLogView as ilv  # noqa: E402

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Import Log</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #0f1115; --panel: #171a21; --border: #262b35;
    --text: #e6e8eb; --dim: #8a909c;
    --ok: #3ddc84; --warn: #ff5c5c; --note: #f5c45e; --accent: #5b9dff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 24px 20px 60px;
  }
  h1 { font-size: 18px; margin: 0 0 4px; font-weight: 600; }
  .sub { color: var(--dim); font-size: 12px; margin-bottom: 20px; }
  .cards {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px; margin-bottom: 22px; max-width: 900px;
  }
  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 14px;
  }
  .card .num { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .card .label { color: var(--dim); font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }
  .card.flagged .num { color: var(--warn); }
  table { width: 100%; border-collapse: collapse; max-width: 1100px; }
  th, td {
    text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  th {
    color: var(--dim); font-size: 11px; text-transform: uppercase;
    letter-spacing: .03em; font-weight: 600; position: sticky; top: 0; background: var(--bg);
  }
  tr.flagged td { background: rgba(255, 92, 92, 0.08); }
  tr.flagged td:first-child { border-left: 2px solid var(--warn); }
  .slug { color: var(--accent); font-weight: 600; }
  .pct-ok { color: var(--ok); }
  .pct-bad { color: var(--warn); font-weight: 700; }
  .issue { color: var(--warn); font-size: 12px; }
  .note { color: var(--note); font-size: 12px; }
  .kingdoms { color: var(--dim); font-size: 12px; }
  .empty { color: var(--dim); padding: 30px 0; }
  .wrap { overflow-x: auto; max-width: 1100px; }
  .queue {
    max-width: 1100px; margin-bottom: 26px; background: var(--panel);
    border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px;
  }
  .queue h2 {
    font-size: 13px; margin: 0 0 10px; color: var(--dim);
    text-transform: uppercase; letter-spacing: .04em; font-weight: 600;
  }
  .queue-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 760px) { .queue-grid { grid-template-columns: 1fr; } }
  .queue-list { list-style: none; margin: 0; padding: 0; font-size: 12.5px; }
  .queue-list li {
    display: flex; justify-content: space-between; gap: 10px;
    padding: 4px 0; border-bottom: 1px solid var(--border);
  }
  .queue-list li:last-child { border-bottom: none; }
  .qs-done { color: var(--ok); }
  .qs-running { color: var(--accent); }
  .qn { font-variant-numeric: tabular-nums; color: var(--dim); white-space: nowrap; }
  .open-list { margin: 0; padding: 0 0 0 16px; font-size: 12.5px; color: var(--text); }
  .open-list li { padding: 3px 0; }
  .open-list b { color: var(--text); }
</style>
</head>
<body>
  <h1>Import Log</h1>
  <div class="sub" id="asof">loading&hellip;</div>

  <div class="queue">
    <h2>2026-10-19 import queue &amp; open items &mdash; see docs/dataset-inbox.md for full detail</h2>
    <div class="queue-grid">
      <ul class="queue-list">
        <li><span>WTaxa weevils</span> <span class="qn qs-done">+251 done</span></li>
        <li><span>WoRMS Brachyura</span> <span class="qn qs-done">+7 done</span></li>
        <li><span>WoRMS Trematoda</span> <span class="qn qs-done">+957 done</span></li>
        <li><span>Nymphalidae</span> <span class="qn qs-done">+422 done</span></li>
        <li><span>ScaleNet</span> <span class="qn qs-done">+493 done</span></li>
        <li><span>Nemys nematodes</span> <span class="qn qs-done">+2,127 done</span></li>
        <li><span>WoRMS full (2011)</span> <span class="qn qs-done">+52,294 done</span></li>
        <li><span>FLOW</span> <span class="qn qs-done">+290 done</span></li>
        <li><span>SF Psocodea</span> <span class="qn qs-done">+547 done</span></li>
        <li><span>AusFungi</span> <span class="qn qs-done">+3,395 done</span></li>
        <li><span>LDL Neuropterida</span> <span class="qn qs-done">+287 done</span></li>
        <li><span>MOWD Membracoidea</span> <span class="qn qs-done">+1,904 done</span></li>
        <li><span>WCVP</span> <span class="qn qs-done">+6,173 done</span></li>
        <li><span>Wikispecies, pending round</span> <span class="qn qs-done">+9,972 done</span></li>
      </ul>
      <ul class="open-list">
        <li><b>Japan fungi checklist</b> &mdash; 0 family overlap, needs scaffolding first</li>
        <li><b>WoRMS Scleractinia / Amphipoda</b> &mdash; +4 each, saturated, declined</li>
        <li><b>Banco Taxonômico Brasileiro</b> &mdash; 404, no archive available</li>
        <li><b>LepIndex / FishBase</b> &mdash; old hedged leads, not re-examined</li>
        <li><b>pendingFamilies: 861 families, no archive recorded</b> &mdash; need manual tracing</li>
        <li><b>pendingFamilies: 15,642 families genuinely absent</b> &mdash; mostly bacteria/GTDB, on hold</li>
        <li><b>Two tree-wide audits</b> logged in BACKLOG.md (WoRMS name-quoting, historical id collisions)</li>
      </ul>
    </div>
  </div>

  <div class="cards" id="cards"></div>
  <div class="wrap"><table id="tbl">
    <thead><tr>
      <th>When</th><th>Source</th><th>Offered</th><th>Held</th><th>Staged</th>
      <th>Added</th><th>Refused</th><th>Rate</th><th>Kingdoms</th>
    </tr></thead>
    <tbody id="rows"></tbody>
  </table></div>

<script>
function fmt(n) { return (n ?? 0).toLocaleString(); }

function render(data) {
  document.getElementById('asof').textContent =
    data.rows.length + ' run(s) — refreshed ' + new Date().toLocaleTimeString();

  const totalAdded = data.rows.reduce((s, r) => s + (r.added || 0), 0);
  const totalOffered = data.rows.reduce((s, r) => s + (r.offered || 0), 0);
  const totalRefused = data.rows.reduce((s, r) => s + (r.refused || 0), 0);
  const flagged = data.rows.filter(r => r.issues.length > 0).length;

  document.getElementById('cards').innerHTML = `
    <div class="card"><div class="num">${fmt(data.rows.length)}</div><div class="label">Runs</div></div>
    <div class="card"><div class="num">${fmt(totalAdded)}</div><div class="label">Species added</div></div>
    <div class="card"><div class="num">${fmt(totalOffered)}</div><div class="label">Offered</div></div>
    <div class="card"><div class="num">${fmt(totalRefused)}</div><div class="label">Refused</div></div>
    <div class="card ${flagged ? 'flagged' : ''}"><div class="num">${fmt(flagged)}</div><div class="label">Flagged</div></div>
  `;

  const rows = data.rows.slice().reverse().map(r => {
    const rate = r.refusalRate || 0;
    const pctClass = rate > data.ceiling ? 'pct-bad' : 'pct-ok';
    const extra = [
      ...r.issues.map(i => `<div class="issue">&#9650; ${i}</div>`),
      ...r.notes.map(n => `<div class="note">&middot; ${n}</div>`),
    ].join('');
    const name = r.title || r.slugHint || r.source || '?';
    return `<tr class="${r.issues.length ? 'flagged' : ''}">
      <td>${(r.at || '').replace('T', ' ').slice(0, 19)}</td>
      <td><span class="slug">${name}</span>${extra}</td>
      <td>${fmt(r.offered)}</td>
      <td>${fmt(r.alreadyHeld)}</td>
      <td>${fmt(r.staged)}</td>
      <td>${fmt(r.added)}</td>
      <td>${fmt(r.refused)}</td>
      <td class="${pctClass}">${(rate * 100).toFixed(1)}%</td>
      <td class="kingdoms">${(r.kingdoms || []).join(', ')}</td>
    </tr>`;
  }).join('');

  document.getElementById('rows').innerHTML = rows ||
    '<tr><td colspan="9" class="empty">No runs recorded yet.</td></tr>';
}

async function tick() {
  try {
    const res = await fetch('/api/log');
    render(await res.json());
  } catch (e) {
    document.getElementById('asof').textContent = 'connection lost, retrying…';
  }
}
tick();
setInterval(tick, 3000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # noqa: N802 -- quiet; this runs during active imports
        pass

    def do_GET(self):  # noqa: N802
        if self.path == "/" or self.path == "/index.html":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/log":
            rows = ilv.load_rows(ilv.LOG)
            ceiling = 0.20
            out = []
            for r in rows:
                row = dict(r)
                row["issues"] = ilv.problems(r, ceiling)
                row["notes"] = ilv.notes(r)
                out.append(row)
            body = json.dumps({"rows": out, "ceiling": ceiling}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9883)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"  importLogServer: http://localhost:{args.port}/  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
