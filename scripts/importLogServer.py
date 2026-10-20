#!/usr/bin/env python3
"""Web dashboard for data/import-log.jsonl -- the human-friendly sibling of
importLogView.py's terminal table, for watching a run of several imports in
a row without squinting at a monospace table.

Reuses importLogView.py's row-loading and problem/note logic directly
rather than re-deriving it -- the same reason scripts/taxaserve.py exists:
one place answers the question, everything else asks it.

The "up next / open items" panel reads data/source-queue.json live (see
scripts/sourceQueue.py) rather than embedding a hand-written list in this
page's HTML -- the first version of this panel (2026-10-19) hardcoded
both the completed-today list and the open-items list, and was already
wrong by the time the next candidate batch finished triaging. The panel
re-fetches it on the same 3s tick as the run table, so it reflects
whatever `sourceQueue.py set` last recorded without this file changing.

Usage:
    python3 scripts/importLogServer.py                 # serve on :9883
    python3 scripts/importLogServer.py --port 9883
    open http://localhost:9883/
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importLogView as ilv  # noqa: E402
import sourceQueue as sq  # noqa: E402

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
  th.num, td.num { text-align: right; }
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
  .queue-list { list-style: none; margin: 0; padding: 0; font-size: 12.5px; }
  .queue-list li {
    display: flex; justify-content: space-between; gap: 10px;
    padding: 4px 0; border-bottom: 1px solid var(--border);
  }
  .queue-list li:last-child { border-bottom: none; }
  .qn { font-variant-numeric: tabular-nums; color: var(--dim); white-space: nowrap; }
  .queue-list li { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
  .queue-list .qi-title { min-width: 0; }
  .status-badge {
    display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px;
    border-radius: 999px; font-size: 10.5px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .03em; white-space: nowrap;
  }
  .status-measuring { background: rgba(245, 196, 94, 0.15); color: var(--note); }
  .status-applying { background: rgba(91, 157, 255, 0.18); color: var(--accent); }
  .status-dot {
    width: 6px; height: 6px; border-radius: 50%; background: currentColor;
    animation: pulse 1.2s ease-in-out infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
  .open-list { margin: 0; padding: 0 0 0 16px; font-size: 12.5px; color: var(--text); }
  .open-list li { padding: 3px 0; }
  .open-list b { color: var(--text); }
  .queue-footer {
    margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border);
    color: var(--dim); font-size: 11.5px;
  }
  .queue-footer code { color: var(--text); }
  .queue-empty { color: var(--dim); font-size: 12.5px; }
  .driver-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 2px 8px; border-radius: 999px; font-size: 10.5px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .03em; white-space: nowrap;
  }
  .driver-running { background: rgba(61, 220, 132, 0.15); color: var(--ok); }
  .driver-stopped { background: rgba(255, 92, 92, 0.15); color: var(--warn); }
  .driver-dot {
    width: 6px; height: 6px; border-radius: 50%; background: currentColor;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .open-block {
    border: 1px solid var(--border); border-radius: 10px;
    background: var(--panel); margin-top: 12px; overflow: hidden;
  }
  .open-toggle {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 10px 14px; cursor: pointer; background: var(--bg);
    font-size: 12.5px; color: var(--dim); font-weight: 600;
    text-transform: uppercase; letter-spacing: .03em;
  }
  .open-toggle[aria-expanded="true"] { background: var(--panel); border-bottom: 1px solid var(--border); }
  .open-toggle::after { content: "▾"; font-size: 10px; color: var(--dim); }
  .open-toggle[aria-expanded="true"]::after { content: "▴"; }
  .open-body { max-height: 0; overflow: hidden; transition: max-height .22s ease; }
  .open-body.open { max-height: 1000px; }
</style>
</head>
<body>
  <h1>Import Log</h1>
  <div class="sub" id="asof">loading&hellip;</div>

  <div class="queue">
    <h2 id="queueHeading">source queue &mdash; loading&hellip;</h2>
    <div class="driver-line" id="driverLine" style="margin-bottom:8px;">
      <span class="driver-badge driver-stopped" id="driverBadge">
        <span class="driver-dot" id="driverDot"></span><span id="driverStatus">driver: loading&hellip;</span>
      </span>
      <span id="driverDetail" style="color:var(--dim); font-size:11px; margin-left:8px;">
        downloaded: <span id="downloadedCount">0</span> / <span id="downloadedThreshold">5</span> refill threshold
      </span>
    </div>
    <ul class="queue-list" id="queueUpNext"></ul>
    <div class="open-block" id="openBlock">
      <div class="open-toggle" id="openToggle" role="button" tabindex="0" aria-expanded="false">
        Open items &mdash; <span id="openCount">0</span>
      </div>
      <div class="open-body" id="openBody">
        <ul class="open-list" id="queueOpen"></ul>
      </div>
    </div>
    <div class="queue-footer">
      Cross-cutting, not per-source, so not in this list: the
      <code>pendingFamilies.py</code> worklist (861 families ready but with
      no archive recorded, 15,642 still genuinely absent, mostly
      bacteria/GTDB on hold) and two tree-wide audits logged in
      <code>BACKLOG.md</code> (WoRMS name-quoting, historical sourceIds
      collisions). See docs/dataset-inbox.md for the full narrative.
    </div>
  </div>

  <div class="cards" id="cards"></div>
  <div class="wrap"><table id="tbl">
    <thead><tr>
      <th>When</th><th>Source</th><th class="num">Offered</th><th class="num">Held</th><th class="num">Staged</th>
      <th class="num">Added</th><th class="num">Refused</th><th class="num">Rate</th><th>Kingdoms</th>
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
      <td class="num">${fmt(r.offered)}</td>
      <td class="num">${fmt(r.alreadyHeld)}</td>
      <td class="num">${fmt(r.staged)}</td>
      <td class="num">${fmt(r.added)}</td>
      <td class="num">${fmt(r.refused)}</td>
      <td class="num ${pctClass}">${(rate * 100).toFixed(1)}%</td>
      <td class="kingdoms">${(r.kingdoms || []).join(', ')}</td>
    </tr>`;
  }).join('');

  document.getElementById('rows').innerHTML = rows ||
    '<tr><td colspan="9" class="empty">No runs recorded yet.</td></tr>';
}

const UP_NEXT_STAGES = ['candidate', 'downloaded', 'measuring', 'measured', 'queued', 'applying', 'needs-rerun'];
const ACTIVE_STAGES = ['measuring', 'applying'];

function renderQueue(sources) {
  const byKey = Object.values(sources);
  const upNext = byKey.filter(r => UP_NEXT_STAGES.includes(r.stage))
    .sort((a, b) => {
      const aActive = ACTIVE_STAGES.includes(a.stage), bActive = ACTIVE_STAGES.includes(b.stage);
      if (aActive !== bActive) return aActive ? -1 : 1;
      return (b.size || 0) - (a.size || 0);
    });
  const open = byKey.filter(r => r.stage === 'declined' || r.stage === 'blocked');
  const activeCount = upNext.filter(r => ACTIVE_STAGES.includes(r.stage)).length;

  document.getElementById('queueHeading').textContent =
    `Up next (${upNext.length}${activeCount ? `, ${activeCount} running now` : ''}) & open items (${open.length}) — today's completed runs are in the table below`;

  document.getElementById('openCount').textContent = String(open.length);

  const downloadedCount = byKey.filter(r => r.stage === 'downloaded').length;
  document.getElementById('downloadedCount').textContent = String(downloadedCount);
  document.getElementById('downloadedThreshold').textContent = '5';

  document.getElementById('queueUpNext').innerHTML = upNext.length
    ? upNext.map(r => {
        const badge = r.stage === 'measuring'
            ? '<span class="status-badge status-measuring"><span class="status-dot"></span>measuring</span>'
          : r.stage === 'applying'
            ? '<span class="status-badge status-applying"><span class="status-dot"></span>importing</span>'
          : '';
        const stage = r.stage === 'candidate' ? 'not yet downloaded'
          : r.stage === 'downloaded' ? 'downloaded'
          : r.stage === 'measured' ? 'measured'
          : r.stage === 'queued' ? 'queued to apply'
          : r.stage === 'needs-rerun' ? 'needs re-run'
          : '';
        return `<li>
          <span class="qi-title">${r.title || r.key}</span>
          <span class="qn">${badge}${stage}${stage ? ' &middot; ' : ''}${r.key} &middot; ${fmt(r.size)}</span>
        </li>`;
      }).join('')
    : '<li class="queue-empty">Nothing queued.</li>';

  document.getElementById('queueOpen').innerHTML = open.length
    ? open.map(r =>
        `<li><b>${r.title || r.key}</b> (${r.stage}) &mdash; ${r.reason || 'no reason recorded'}</li>`
      ).join('')
    : '<li class="queue-empty">Nothing open.</li>';
}

async function renderDriver() {
  try {
    const res = await fetch('/api/driver');
    const d = await res.json();
    const badge = document.getElementById('driverBadge');
    const status = document.getElementById('driverStatus');
    const dot = document.getElementById('driverDot');
    const detail = document.getElementById('driverDetail');
    if (d.running) {
      badge.className = 'driver-badge driver-running';
      status.textContent = 'driver: running';
      dot.style.display = 'inline-block';
      detail.textContent = `downloaded: ${d.downloadedCount ?? 0} / ${d.refillThreshold ?? 5} refill threshold`;
    } else {
      badge.className = 'driver-badge driver-stopped';
      status.textContent = 'driver: stopped';
      dot.style.display = 'none';
      detail.textContent = 'auto-refill disabled — queue will not refill below 5';
    }
  } catch (e) {
    document.getElementById('driverStatus').textContent = 'driver: connection lost';
  }
}

function setupQueueToggle() {
  const toggle = document.getElementById('openToggle');
  const body = document.getElementById('openBody');
  const expand = () => {
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!expanded));
    body.classList.toggle('open', !expanded);
  };
  toggle.addEventListener('click', expand);
  toggle.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); expand(); }
  });
}

async function tick() {
  try {
    const res = await fetch('/api/log');
    render(await res.json());
  } catch (e) {
    document.getElementById('asof').textContent = 'connection lost, retrying…';
  }
  try {
    const res = await fetch('/api/queue');
    renderQueue(await res.json());
  } catch (e) {
    document.getElementById('queueHeading').textContent = 'source queue — connection lost';
  }
  try {
    await renderDriver();
  } catch (e) {
    document.getElementById('driverStatus').textContent = 'driver: connection lost';
  }
}
tick();
setupQueueToggle();
renderDriver();
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
        if self.path == "/api/queue":
            body = json.dumps(sq.read_store()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/driver":
            rc = subprocess.run(
                ["pgrep", "-f", "importQueueDriver.py"],
                capture_output=True,
            ).returncode
            q = sq.read_store()
            downloaded = [v for v in q.values() if v.get("stage") == "downloaded"]
            body = json.dumps({
                "running": rc == 0,
                "downloadedCount": len(downloaded),
                "refillThreshold": 5,
            }).encode("utf-8")
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
