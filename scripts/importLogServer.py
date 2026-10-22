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
import re
import subprocess
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importLogView as ilv  # noqa: E402
import sourceQueue as sq  # noqa: E402

CB_API = "https://api.checklistbank.org/dataset"
CB_UA = "systema-naturae-dashboard/1.0 (+https://github.com/tobese/systema-naturae)"
_publisher_cache: dict[str, str] = {}
_publisher_cache_at: dict[str, float] = {}


def cb_publisher(key: str) -> str | None:
    """Publisher entity for a ChecklistBank dataset key — contact.organisation
    or creator[0].organisation — cached for 10 minutes so the 3s tick doesn't
    hammer the API. Returns None when the API has nothing usable."""
    now = time.time()
    if key in _publisher_cache and now - _publisher_cache_at.get(key, 0) < 600:
        return _publisher_cache[key]
    try:
        # ChecklistBank API expects the bare numeric key, not the "checklistbank-" prefix.
        api_key = key[len("checklistbank-"):] if key.startswith("checklistbank-") else key
        req = urllib.request.Request(
            f"{CB_API}/{api_key}",
            headers={"User-Agent": CB_UA},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            doc = json.load(r)
    except Exception:
        _publisher_cache[key] = None
        _publisher_cache_at[key] = now
        return None
    contact = doc.get("contact") or {}
    org = contact.get("organisation") or ""
    creators = doc.get("creator") or []
    if not org and creators:
        org = creators[0].get("organisation") or ""
    _publisher_cache[key] = org or None
    _publisher_cache_at[key] = now
    return _publisher_cache[key]


def cb_key_from_slughint(slughint: str | None) -> str | None:
    """Extract a source-queue key from an import log row's slugHint, when it
    looks like a ChecklistBank dataset key ("55434" or "checklistbank-55434").
    Returns the queue-key form ("checklistbank-55434") or None."""
    if not slughint:
        return None
    s = str(slughint).strip()
    m = re.fullmatch(r"checklistbank-(\d+)", s)
    if m:
        return f"checklistbank-{m.group(1)}"
    m = re.fullmatch(r"(\d+)", s)
    if m:
        return f"checklistbank-{m.group(1)}"
    return None


def pending_summary() -> dict:
    """Summary of the pending-family worklist — families imports could not
    place because the tree lacks them. Reads the external-volume store
    (symlinked at portal/data/pending-families.jsonl) and returns counts
    plus a per-source breakdown."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pendingFamilies as PF  # noqa: E402

    rows = PF.read_store()
    total = len(rows)
    species_total = sum(int(r.get("species") or 0) for r in rows)

    held = PF.held_families()
    still, ready = [], []
    for r in rows:
        (ready if (r.get("family") or "").lower() in held else still).append(r)

    by_src: dict[str, dict] = {}
    for r in ready:
        src = r.get("source") or "?"
        s = by_src.setdefault(src, {"families": 0, "species": 0})
        s["families"] += 1
        s["species"] += int(r.get("species") or 0)

    return {
        "total": total,
        "stillMissing": len(still),
        "ready": len(ready),
        "speciesTotal": species_total,
        "readySpeciesTotal": sum(int(r.get("species") or 0) for r in ready),
        "bySource": dict(sorted(by_src.items(), key=lambda kv: -kv[1]["species"])),
    }

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
  table { width: 100%; border-collapse: collapse; max-width: 1100px; table-layout: fixed; }
  th, td {
    text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
  }
  th.num, td.num { text-align: right; white-space: nowrap; }
  td.source { overflow: hidden; text-overflow: ellipsis; }
  th {
    color: var(--dim); font-size: 11px; text-transform: uppercase;
    letter-spacing: .03em; font-weight: 600; position: sticky; top: 0; background: var(--bg);
  }
  th.source { width: 32%; }
  th.num { width: 9%; }
  th:first-child { width: 16%; }
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
  .status-triaging { background: rgba(245, 196, 94, 0.15); color: var(--note); }
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
  .pending {
    max-width: 1100px; margin-top: 22px; background: var(--panel);
    border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px;
  }
  .pending h2 {
    font-size: 13px; margin: 0 0 10px; color: var(--dim);
    text-transform: uppercase; letter-spacing: .04em; font-weight: 600;
  }
  .pending-cards {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px; margin-bottom: 12px;
  }
  .pending-card {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px;
  }
  .pending-card .num { font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }
  .pending-card .label { color: var(--dim); font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }
  .pending-list { list-style: none; margin: 0; padding: 0; font-size: 12.5px; }
  .pending-list li {
    display: flex; justify-content: space-between; gap: 10px;
    padding: 4px 0; border-bottom: 1px solid var(--border);
  }
  .pending-list li:last-child { border-bottom: none; }
  .pending-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  .pending-table th, .pending-table td {
    text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
  }
  .pending-table th { color: var(--dim); text-transform: uppercase; font-size: 11px; letter-spacing: .03em; }
  .pending-table td.source { max-width: none; }
  .pending-table td.num { text-align: right; white-space: nowrap; }
  .pending-empty { color: var(--dim); font-size: 12.5px; }
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
        downloads ChecklistBank &bull; refill below 5 &middot; downloaded: 0
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

  <div class="pending" id="pendingPanel" style="display:none;">
    <h2 id="pendingHeading">missing families &mdash; loading&hellip;</h2>
    <div class="pending-cards" id="pendingCards"></div>
    <ul class="pending-list" id="pendingBySource"></ul>
  </div>

  <div class="cards" id="cards"></div>
  <div class="wrap"><table id="tbl">
    <thead><tr>
      <th>When</th><th class="source">Source</th><th class="num">Offered</th><th class="num">Held</th><th class="num">Staged</th>
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
    const name = r.publisher ? `${r.publisher} ${r.key ? '('+r.key+')' : ''}` : (r.title || r.slugHint || r.source || '?');
    return `<tr class="${r.issues.length ? 'flagged' : ''}">
      <td>${(r.at || '').replace('T', ' ').slice(0, 19)}</td>
      <td class="source"><span class="slug">${name}</span>${extra}</td>
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

const UP_NEXT_STAGES = ['candidate', 'downloaded', 'triaging', 'triaged', 'queued', 'applying', 'needs-rerun'];
const ACTIVE_STAGES = ['triaging', 'applying'];

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

  document.getElementById('queueUpNext').innerHTML = upNext.length
    ? '<ul class="queue-list" style="font-size:11.5px; list-style:none; padding:0; margin:0;">'
        + '<li style="color:#8a909c; font-size:10px; text-transform:uppercase; letter-spacing:.03em; padding:4px 0; border-bottom:1px solid #262b35; font-weight:600;">'
        + '<span style="float:left;">Source</span><span style="float:right;">State · Size</span><span style="clear:both;"></span>'
        + '</li>'
        + upNext.map(r => {
        const badge = r.stage === 'triaging'
            ? '<span class="status-badge status-triaging"><span class="status-dot"></span>triaging</span>'
          : r.stage === 'applying'
            ? '<span class="status-badge status-applying"><span class="status-dot"></span>importing</span>'
          : '';
        const cleanTitle2 = (r.title || r.key || '').replace(/^Batch [iI]mport[ -]?/, '').trim();
        const displayName2 = cleanTitle2 || r.key;
        return `<li style="display:flex; justify-content:space-between; align-items:baseline; gap:10px; padding:4px 0; border-bottom:1px solid #262b35;">`
          + `<span style="min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escape(displayName2)}${r.publisher ? ' — ' + escape(r.publisher) : ''}</span>`
          + `<span style="white-space:nowrap; text-align:right; font-variant-numeric:tabular-nums;">`
          + `${badge ? badge + ' ' : ''}${r.stage}<span style="color:#5b9dff;"> · ${fmt(r.size)}</span></span>`
          + `</li>`;
      }).join('')
        + '</ul>'
    : '<li class="queue-empty">Nothing queued.</li>';

  document.getElementById('queueOpen').innerHTML = open.length
    ? '<ul class="open-list" style="font-size:11.5px; list-style:none; padding:0; margin:0;">'
        + '<li style="color:#8a909c; font-size:10px; text-transform:uppercase; letter-spacing:.03em; padding:4px 0; border-bottom:1px solid #262b35; font-weight:600;">'
        + '<span style="float:left;">Source</span><span style="float:right;">State · Size</span><span style="clear:both;"></span></li>'
        + open.map(r => {
        const cleanTitle3 = (r.title || r.key || '').replace(/^Batch [iI]mport[ -]?/, '').trim();
        const displayName3 = cleanTitle3 || r.key;
        return `<li style="display:flex; justify-content:space-between; align-items:baseline; gap:10px; padding:4px 0; border-bottom:1px solid #262b35;">`
          + `<span style="min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escape(displayName3)}${r.publisher ? ' — ' + escape(r.publisher) : ''}</span>`
          + `<span style="white-space:nowrap; text-align:right; font-variant-numeric:tabular-nums;">${r.stage} · ${fmt(r.size || 0)}</span>`
          + `</li>`;
      }).join('')
        + '</ul>'
    : '<li class="queue-empty">Nothing open.</li>';
}

function escape(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

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
      status.textContent = 'driver: running — downloads ChecklistBank';
      dot.style.display = 'inline-block';
      detail.innerHTML = `downloads ChecklistBank &bull; refill below ${d.refillThreshold ?? 5} &middot; downloaded: ${d.downloadedCount ?? 0}`;
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

async function renderPending() {
  try {
    const res = await fetch('/api/pending');
    const p = await res.json();
    const panel = document.getElementById('pendingPanel');
    if (p.total === 0) {
      panel.style.display = 'none';
      return;
    }
    panel.style.display = 'block';
    document.getElementById('pendingHeading').textContent =
      `missing families (${p.ready} now scaffoldable / ${p.stillMissing} still missing)`;

    document.getElementById('pendingCards').innerHTML = `
      <div class="pending-card"><div class="num">${fmt(p.total)}</div><div class="label">Pending families</div></div>
      <div class="pending-card"><div class="num">${fmt(p.speciesTotal)}</div><div class="label">Species they would add</div></div>
      <div class="pending-card"><div class="num">${fmt(p.ready)}</div><div class="label">Now scaffoldable</div></div>
      <div class="pending-card"><div class="num">${fmt(p.readySpeciesTotal)}</div><div class="label">Species ready adds</div></div>
    `;

    const list = document.getElementById('pendingBySource');
    const entries = Object.entries(p.bySource || {});
    list.innerHTML = entries.length
      ? `<table class="pending-table">
           <thead><tr>
             <th class="source">Source</th>
             <th class="num">Families</th>
             <th class="num">Species</th>
           </tr></thead>
           <tbody>
             ${entries.map(([src, s]) =>
               `<tr>
                 <td class="source">${escape(src)}</td>
                 <td class="num">${fmt(s.families)}</td>
                 <td class="num">${fmt(s.species)}</td>
               </tr>`
             ).join('')}
           </tbody>
         </table>`
      : '<p class="pending-empty">No sources with ready families.</p>';
  } catch (e) {
    document.getElementById('pendingHeading').textContent = 'missing families — connection lost';
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
  try {
    await renderPending();
  } catch (e) {
    document.getElementById('pendingHeading').textContent = 'missing families — connection lost';
  }
}
tick();
setupQueueToggle();
renderDriver();
renderPending();
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
                key = cb_key_from_slughint(row.get("slugHint"))
                if key:
                    row["key"] = key
                    row["publisher"] = cb_publisher(key)
                out.append(row)
            body = json.dumps({"rows": out, "ceiling": ceiling}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/queue":
            q = sq.read_store()
            out = {}
            for key, entry in q.items():
                e = dict(entry)
                e["publisher"] = cb_publisher(key)
                out[key] = e
            body = json.dumps(out).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/pending":
            pending = pending_summary()
            body = json.dumps(pending).encode("utf-8")
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
