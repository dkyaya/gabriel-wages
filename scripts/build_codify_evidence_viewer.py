"""
build_codify_evidence_viewer.py — build/append the durable GABRIEL codify
evidence layer and regenerate the local HTML excerpt browser.

Purpose: a safe, repeatable, offline transform. Reads an already-produced
codify pilot output CSV (e.g. docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv,
produced by scripts/gabriel_codify_pilot.py's --live run and audited in
docs/analysis/gabriel_codify_full_codebook_audit_2026-07-09.md) and:

1. Writes/appends a durable, append-friendly evidence table
   (docs/analysis/gabriel_codify_evidence_layer.csv) with a stable
   evidence_id per row, suitable for accumulating across future codify runs.
2. Regenerates a self-contained, static local HTML excerpt browser
   (docs/analysis/gabriel_codify_excerpt_browser_2026-07-09.html) with no
   external CDN/JS/CSS dependencies -- opens directly in a browser, no
   server required.

SAFETY MODEL:
  - No network calls of any kind. No gabriel import. No credential read.
  - Never edits data/contracts.csv, data/city_coverage.csv, or corpus/.
  - Only reads the codify output CSV given by --input and writes the two
    output files given by --evidence-out / --html-out.

Usage:
  python scripts/build_codify_evidence_viewer.py
  python scripts/build_codify_evidence_viewer.py --input <csv> --evidence-out <csv> --html-out <html>
"""

from __future__ import annotations

import argparse
import csv
import html as html_module
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "docs" / "analysis" / "gabriel_codify_full_codebook_outputs_2026-07-09.csv"
DEFAULT_EVIDENCE_OUT = ROOT / "docs" / "analysis" / "gabriel_codify_evidence_layer.csv"
DEFAULT_HTML_OUT = ROOT / "docs" / "analysis" / "gabriel_codify_excerpt_browser_2026-07-09.html"

EVIDENCE_FIELDNAMES = [
    "evidence_id", "run_id", "run_date", "source_output_file", "contract_id", "state",
    "city", "occupation_class", "source_role", "attribute", "evidence_status", "excerpt",
    "excerpt_location", "source_file", "source_grounding_status", "raw_output_ref", "notes",
]

ALLOWED_EVIDENCE_STATUS = {"present", "not_found"}
ALLOWED_GROUNDING_STATUS = {"grounded", "unsupported", "unclear", "not_applicable"}

RUN_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                    help="Codify pilot output CSV to read (contract_id x attribute rows).")
    p.add_argument("--evidence-out", type=Path, default=DEFAULT_EVIDENCE_OUT,
                    help="Durable evidence-layer CSV to write/append.")
    p.add_argument("--html-out", type=Path, default=DEFAULT_HTML_OUT,
                    help="Static HTML excerpt browser to write.")
    return p.parse_args()


def _read_input_rows(path: Path) -> list[dict]:
    if not path.exists():
        print(f"ERROR: input CSV not found: {path}")
        sys.exit(1)
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _run_date_from_run_id(run_id: str) -> str:
    m = RUN_DATE_RE.match(run_id or "")
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return "unknown-date"


def _source_file_for_contract(contract_id: str, evidence_windows_csvs: list[Path]) -> str:
    """Best-effort lookup of the underlying corpus source_file for a contract_id,
    by checking any evidence-window CSVs already present in docs/analysis/."""
    for path in evidence_windows_csvs:
        if not path.exists():
            continue
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if row.get("contract_id") == contract_id and row.get("source_file"):
                    return row["source_file"]
    return ""


def build_evidence_rows(input_rows: list[dict]) -> list[dict]:
    docs_dir = ROOT / "docs" / "analysis"
    evidence_window_csvs = sorted(docs_dir.glob("*evidence_windows*.csv"))
    source_file_cache: dict[str, str] = {}

    sequence_counters: dict[tuple[str, str], int] = {}
    evidence_rows: list[dict] = []

    for row in input_rows:
        evidence_status = (row.get("evidence_status") or "").strip()
        if evidence_status not in ALLOWED_EVIDENCE_STATUS:
            # Task B keeps only binary present/not_found semantics; anything
            # else (e.g. a legacy "unclear" from an older pilot format) is
            # coerced to not_found rather than silently dropped or invented.
            evidence_status = "not_found"

        contract_id = row.get("contract_id", "")
        attribute = row.get("attribute", "")
        run_id = row.get("run_id", "")
        run_date = _run_date_from_run_id(run_id)

        key = (contract_id, attribute)
        seq = sequence_counters.get(key, 0)
        sequence_counters[key] = seq + 1
        evidence_id = f"codify_{run_date.replace('-', '')}_{contract_id}_{attribute}_{seq}"

        if contract_id not in source_file_cache:
            source_file_cache[contract_id] = _source_file_for_contract(contract_id, evidence_window_csvs)

        grounding = (row.get("source_grounding_status") or "").strip()
        if grounding not in ALLOWED_GROUNDING_STATUS:
            grounding = "not_applicable"

        excerpt = row.get("excerpt", "") if evidence_status == "present" else ""
        if excerpt is None:
            excerpt = ""

        evidence_rows.append({
            "evidence_id": evidence_id,
            "run_id": run_id,
            "run_date": run_date,
            "source_output_file": str(Path("docs/analysis") / DEFAULT_INPUT.name) if True else "",
            "contract_id": contract_id,
            "state": row.get("state", ""),
            "city": row.get("city", ""),
            "occupation_class": row.get("occupation_class", ""),
            "source_role": row.get("source_role", ""),
            "attribute": attribute,
            "evidence_status": evidence_status,
            "excerpt": excerpt,
            "excerpt_location": row.get("excerpt_location", "") or "",
            "source_file": source_file_cache.get(contract_id, ""),
            "source_grounding_status": grounding,
            "raw_output_ref": row.get("raw_output_ref", "") or "",
            "notes": row.get("notes", "") or "",
        })
    return evidence_rows


def write_evidence_csv(rows: list[dict], out_path: Path, input_path: Path) -> list[dict]:
    # source_output_file is recorded relative to the repo root for portability.
    try:
        rel_input = str(input_path.resolve().relative_to(ROOT))
    except ValueError:
        rel_input = str(input_path)
    for r in rows:
        r["source_output_file"] = rel_input

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EVIDENCE_FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Parse back immediately and validate.
    with out_path.open(newline="") as f:
        parsed = list(csv.DictReader(f))

    assert len(parsed) == len(rows), "row count mismatch after write/reparse"
    seen_ids = set()
    for i, row in enumerate(parsed):
        if set(row.keys()) != set(EVIDENCE_FIELDNAMES):
            raise ValueError(f"row {i} column mismatch: {set(row.keys())}")
        if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
            raise ValueError(f"row {i} bad evidence_status: {row['evidence_status']!r}")
        if row["source_grounding_status"] not in ALLOWED_GROUNDING_STATUS:
            raise ValueError(f"row {i} bad source_grounding_status: {row['source_grounding_status']!r}")
        if row["evidence_status"] == "present" and not row["excerpt"].strip():
            raise ValueError(f"row {i} ({row['evidence_id']}) is present but has a blank excerpt")
        eid = row["evidence_id"]
        if eid in seen_ids:
            raise ValueError(f"duplicate evidence_id: {eid!r}")
        seen_ids.add(eid)

    return parsed


# ---------------------------------------------------------------------------
# HTML browser generation
# ---------------------------------------------------------------------------

def _esc(value) -> str:
    return html_module.escape(str(value) if value is not None else "")


def build_html(rows: list[dict], html_out: Path) -> None:
    data_json = json.dumps(rows, ensure_ascii=False)
    total = len(rows)
    present = sum(1 for r in rows if r["evidence_status"] == "present")
    not_found = total - present
    grounded_present = sum(
        1 for r in rows if r["evidence_status"] == "present" and r["source_grounding_status"] == "grounded"
    )

    html_doc = HTML_TEMPLATE.format(
        data_json=data_json,
        total=total,
        present=present,
        not_found=not_found,
        grounded_present=grounded_present,
    )
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.write_text(html_doc, encoding="utf-8")


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>GABRIEL Codify Excerpt Browser</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg: #0f1216; --panel: #171b21; --panel2: #1e2430; --text: #e8ecf1; --muted: #9aa5b1;
    --accent: #4fc3f7; --present: #2e7d32; --present-bg: #163a1a; --absent: #6b7280;
    --border: #2a3140; --mark: #ffd54f; --mark-text: #241c00;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f5f7fa; --panel: #ffffff; --panel2: #eef1f6; --text: #1a1f27; --muted: #5b6472;
      --accent: #0277bd; --present: #2e7d32; --present-bg: #e3f4e5; --absent: #9aa5b1;
      --border: #d7dde5; --mark: #ffe082; --mark-text: #241c00;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.45;
  }}
  header {{ padding: 16px 20px; border-bottom: 1px solid var(--border); background: var(--panel); }}
  header h1 {{ margin: 0 0 4px 0; font-size: 20px; }}
  header p {{ margin: 0; color: var(--muted); font-size: 13px; }}
  details.howto {{ margin-top: 10px; background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; }}
  details.howto summary {{ cursor: pointer; font-weight: 600; font-size: 13px; }}
  details.howto ul {{ margin: 8px 0 4px 18px; font-size: 13px; color: var(--muted); }}

  .layout {{ display: flex; gap: 0; min-height: calc(100vh - 110px); }}
  .sidebar {{
    width: 280px; flex-shrink: 0; padding: 16px; border-right: 1px solid var(--border);
    background: var(--panel); overflow-y: auto; max-height: calc(100vh - 110px);
  }}
  .sidebar h2 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 14px 0 6px; }}
  .sidebar h2:first-child {{ margin-top: 0; }}
  .sidebar label {{ display: block; font-size: 13px; margin-bottom: 8px; }}
  .sidebar select, .sidebar input[type="text"] {{
    width: 100%; padding: 6px 8px; margin-top: 3px; background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px; font-size: 13px;
  }}
  .sidebar .checkbox-row {{ display: flex; align-items: center; gap: 6px; font-size: 13px; margin-bottom: 8px; }}
  .sidebar .checkbox-row input {{ margin: 0; }}
  .counts {{ background: var(--panel2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 13px; }}
  .counts div {{ display: flex; justify-content: space-between; padding: 2px 0; }}
  .counts .num {{ font-weight: 700; }}
  button.reset {{ margin-top: 10px; width: 100%; padding: 7px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--panel2); color: var(--text); cursor: pointer; font-size: 12px; }}
  button.reset:hover {{ border-color: var(--accent); }}

  .main {{ flex: 1; padding: 16px 20px; overflow-y: auto; max-height: calc(100vh - 110px); }}
  .viewmode-tabs {{ display: flex; gap: 8px; margin-bottom: 14px; }}
  .viewmode-tabs button {{
    padding: 6px 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel);
    color: var(--text); cursor: pointer; font-size: 13px;
  }}
  .viewmode-tabs button.active {{ background: var(--accent); color: #001018; border-color: var(--accent); font-weight: 700; }}

  .nav-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
  .nav-row button {{
    padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: var(--panel);
    color: var(--text); cursor: pointer; font-size: 13px;
  }}
  .nav-row button:disabled {{ opacity: .4; cursor: default; }}
  .nav-row .position {{ font-size: 13px; color: var(--muted); }}

  .card {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px;
    margin-bottom: 14px;
  }}
  .card .attr-badge {{
    display: inline-block; background: var(--accent); color: #001018; font-weight: 700; font-size: 12px;
    padding: 3px 10px; border-radius: 999px; margin-bottom: 10px; letter-spacing: .02em;
  }}
  .card .status-badge {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; margin-left: 8px; font-weight: 600; }}
  .card .status-present {{ background: var(--present-bg); color: var(--present); }}
  .card .status-not_found {{ background: transparent; color: var(--absent); border: 1px solid var(--border); }}
  .card .ground-badge {{ display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; margin-left: 6px; border: 1px solid var(--border); color: var(--muted); }}
  .card .excerpt {{ font-size: 15px; margin: 10px 0; }}
  .card .excerpt mark {{ background: var(--mark); color: var(--mark-text); padding: 1px 3px; border-radius: 3px; }}
  .card .excerpt.empty {{ color: var(--muted); font-style: italic; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 6px 16px; font-size: 12.5px; color: var(--muted); margin-top: 10px; border-top: 1px solid var(--border); padding-top: 10px; }}
  .meta-grid b {{ color: var(--text); }}
  .card .notes {{ margin-top: 8px; font-size: 12.5px; color: var(--muted); }}

  table.evidence-table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
  table.evidence-table th, table.evidence-table td {{ border: 1px solid var(--border); padding: 6px 8px; text-align: left; vertical-align: top; }}
  table.evidence-table th {{ background: var(--panel2); position: sticky; top: 0; }}
  table.evidence-table tr:hover {{ background: var(--panel2); }}
  .pill {{ display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 999px; }}
  .pill.present {{ background: var(--present-bg); color: var(--present); }}
  .pill.not_found {{ background: transparent; color: var(--absent); border: 1px solid var(--border); }}

  .empty-state {{ color: var(--muted); padding: 40px; text-align: center; }}
  ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 6px; }}
</style>
</head>
<body>

<header>
  <h1>GABRIEL Codify Excerpt Browser</h1>
  <p>Durable evidence layer for this project's wage-mechanism codebook. Local, static, self-contained -- no server, no external libraries, no network calls.</p>
  <details class="howto">
    <summary>How to use this viewer</summary>
    <ul>
      <li>Use the left sidebar to filter by state, city, contract, occupation class, source role, attribute, evidence status, and grounding status.</li>
      <li>Type in the search box to free-text search across excerpt text and notes.</li>
      <li>Switch between <b>Cards</b> (one evidence item at a time, with Prev/Next navigation) and <b>Table</b> (compact, all filtered rows at once) using the tabs above the main panel.</li>
      <li>By default only <b>present</b> evidence is shown; toggle "Show not_found rows" in the sidebar to include absence evidence too.</li>
      <li>Highlighted (<mark>yellow</mark>) text inside a card is the exact verbatim excerpt GABRIEL codify matched for that attribute.</li>
      <li><b>This is a research viewer, not a source of truth by itself</b> -- always check the grounding-status badge (grounded / unsupported / unclear / not_applicable) before citing an excerpt.</li>
    </ul>
  </details>
</header>

<div class="layout">
  <aside class="sidebar">
    <h2>Filters</h2>
    <label>State
      <select id="f-state"><option value="">All</option></select>
    </label>
    <label>City
      <select id="f-city"><option value="">All</option></select>
    </label>
    <label>Contract ID
      <select id="f-contract"><option value="">All</option></select>
    </label>
    <label>Occupation class
      <select id="f-occ"><option value="">All</option></select>
    </label>
    <label>Source role
      <select id="f-role"><option value="">All</option></select>
    </label>
    <label>Attribute
      <select id="f-attr"><option value="">All</option></select>
    </label>
    <label>Evidence status
      <select id="f-status"><option value="">All</option></select>
    </label>
    <label>Grounding status
      <select id="f-ground"><option value="">All</option></select>
    </label>
    <label>Search excerpt / notes
      <input type="text" id="f-search" placeholder="e.g. arbitration, uniform allowance">
    </label>
    <div class="checkbox-row">
      <input type="checkbox" id="f-shownotfound">
      <label for="f-shownotfound" style="margin:0;">Show not_found rows</label>
    </div>
    <button class="reset" id="reset-filters">Reset filters</button>

    <h2>Counts</h2>
    <div class="counts">
      <div><span>Total rows</span><span class="num" id="c-total">{total}</span></div>
      <div><span>Present</span><span class="num" id="c-present">{present}</span></div>
      <div><span>Not found</span><span class="num" id="c-notfound">{not_found}</span></div>
      <div><span>Grounded present</span><span class="num" id="c-grounded">{grounded_present}</span></div>
      <div><span>Selected (filtered)</span><span class="num" id="c-selected">0</span></div>
    </div>
  </aside>

  <main class="main">
    <div class="viewmode-tabs">
      <button id="tab-cards" class="active">Cards</button>
      <button id="tab-table">Table</button>
    </div>

    <div id="cards-view">
      <div class="nav-row">
        <button id="nav-prev">&larr; Prev</button>
        <span class="position" id="nav-position">0 / 0</span>
        <button id="nav-next">Next &rarr;</button>
      </div>
      <div id="card-container"><div class="empty-state">No rows match the current filters.</div></div>
    </div>

    <div id="table-view" style="display:none;">
      <div style="overflow-x:auto;">
        <table class="evidence-table" id="evidence-table">
          <thead>
            <tr>
              <th>Evidence ID</th><th>Contract</th><th>State</th><th>City</th><th>Occ. class</th>
              <th>Attribute</th><th>Status</th><th>Excerpt</th><th>Location</th><th>Grounding</th>
            </tr>
          </thead>
          <tbody id="table-body"></tbody>
        </table>
      </div>
    </div>
  </main>
</div>

<script>
const EVIDENCE = {data_json};

let filtered = [];
let cardIndex = 0;

function uniqueSorted(key) {{
  return Array.from(new Set(EVIDENCE.map(r => r[key]).filter(v => v !== undefined && v !== null && v !== ""))).sort();
}}

function populateSelect(id, key) {{
  const sel = document.getElementById(id);
  uniqueSorted(key).forEach(v => {{
    const opt = document.createElement("option");
    opt.value = v; opt.textContent = v;
    sel.appendChild(opt);
  }});
}}

populateSelect("f-state", "state");
populateSelect("f-city", "city");
populateSelect("f-contract", "contract_id");
populateSelect("f-occ", "occupation_class");
populateSelect("f-role", "source_role");
populateSelect("f-attr", "attribute");
populateSelect("f-status", "evidence_status");
populateSelect("f-ground", "source_grounding_status");

function escapeRegExp(s) {{ return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, "\\\\$&"); }}

function highlightExcerpt(text) {{
  if (!text) return "";
  // The excerpt IS the matched span; show it fully highlighted (it is already
  // the exact verbatim match GABRIEL codify identified, not a larger window).
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return "<mark>" + esc + "</mark>";
}}

function esc(s) {{
  if (s === undefined || s === null) return "";
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}}

function applyFilters() {{
  const state = document.getElementById("f-state").value;
  const city = document.getElementById("f-city").value;
  const contract = document.getElementById("f-contract").value;
  const occ = document.getElementById("f-occ").value;
  const role = document.getElementById("f-role").value;
  const attr = document.getElementById("f-attr").value;
  const status = document.getElementById("f-status").value;
  const ground = document.getElementById("f-ground").value;
  const search = document.getElementById("f-search").value.trim().toLowerCase();
  const showNotFound = document.getElementById("f-shownotfound").checked;

  filtered = EVIDENCE.filter(r => {{
    if (state && r.state !== state) return false;
    if (city && r.city !== city) return false;
    if (contract && r.contract_id !== contract) return false;
    if (occ && r.occupation_class !== occ) return false;
    if (role && r.source_role !== role) return false;
    if (attr && r.attribute !== attr) return false;
    if (status && r.evidence_status !== status) return false;
    if (ground && r.source_grounding_status !== ground) return false;
    if (!status && !showNotFound && r.evidence_status === "not_found") return false;
    if (search) {{
      const hay = ((r.excerpt || "") + " " + (r.notes || "")).toLowerCase();
      if (!hay.includes(search)) return false;
    }}
    return true;
  }});

  document.getElementById("c-selected").textContent = filtered.length;
  cardIndex = 0;
  renderCards();
  renderTable();
}}

function renderCards() {{
  const container = document.getElementById("card-container");
  const posEl = document.getElementById("nav-position");
  if (!filtered.length) {{
    container.innerHTML = "<div class='empty-state'>No rows match the current filters.</div>";
    posEl.textContent = "0 / 0";
    document.getElementById("nav-prev").disabled = true;
    document.getElementById("nav-next").disabled = true;
    return;
  }}
  if (cardIndex < 0) cardIndex = filtered.length - 1;
  if (cardIndex >= filtered.length) cardIndex = 0;
  const r = filtered[cardIndex];
  posEl.textContent = (cardIndex + 1) + " / " + filtered.length;
  document.getElementById("nav-prev").disabled = filtered.length <= 1;
  document.getElementById("nav-next").disabled = filtered.length <= 1;

  const excerptHtml = r.evidence_status === "present" && r.excerpt
    ? "<div class='excerpt'>" + highlightExcerpt(r.excerpt) + "</div>"
    : "<div class='excerpt empty'>No excerpt (not_found).</div>";

  container.innerHTML = `
    <div class="card">
      <span class="attr-badge">${{esc(r.attribute)}}</span>
      <span class="status-badge status-${{esc(r.evidence_status)}}">${{esc(r.evidence_status)}}</span>
      <span class="ground-badge">grounding: ${{esc(r.source_grounding_status)}}</span>
      ${{excerptHtml}}
      <div class="meta-grid">
        <div><b>Contract</b><br>${{esc(r.contract_id)}}</div>
        <div><b>State</b><br>${{esc(r.state)}}</div>
        <div><b>City</b><br>${{esc(r.city)}}</div>
        <div><b>Occupation class</b><br>${{esc(r.occupation_class)}}</div>
        <div><b>Source role</b><br>${{esc(r.source_role)}}</div>
        <div><b>Source file</b><br>${{esc(r.source_file)}}</div>
        <div><b>Excerpt location</b><br>${{esc(r.excerpt_location) || "&mdash;"}}</div>
        <div><b>Evidence ID</b><br>${{esc(r.evidence_id)}}</div>
        <div><b>Run</b><br>${{esc(r.run_id)}} (${{esc(r.run_date)}})</div>
      </div>
      ${{r.notes ? "<div class='notes'><b>Notes:</b> " + esc(r.notes) + "</div>" : ""}}
    </div>
  `;
}}

function renderTable() {{
  const tbody = document.getElementById("table-body");
  if (!filtered.length) {{
    tbody.innerHTML = "<tr><td colspan='10' class='empty-state'>No rows match the current filters.</td></tr>";
    return;
  }}
  tbody.innerHTML = filtered.map(r => `
    <tr>
      <td>${{esc(r.evidence_id)}}</td>
      <td>${{esc(r.contract_id)}}</td>
      <td>${{esc(r.state)}}</td>
      <td>${{esc(r.city)}}</td>
      <td>${{esc(r.occupation_class)}}</td>
      <td>${{esc(r.attribute)}}</td>
      <td><span class="pill ${{esc(r.evidence_status)}}">${{esc(r.evidence_status)}}</span></td>
      <td>${{esc((r.excerpt || "").slice(0, 160))}}${{(r.excerpt || "").length > 160 ? "&hellip;" : ""}}</td>
      <td>${{esc(r.excerpt_location)}}</td>
      <td>${{esc(r.source_grounding_status)}}</td>
    </tr>
  `).join("");
}}

document.querySelectorAll(".sidebar select, #f-search, #f-shownotfound").forEach(el => {{
  el.addEventListener("input", applyFilters);
  el.addEventListener("change", applyFilters);
}});

document.getElementById("reset-filters").addEventListener("click", () => {{
  document.querySelectorAll(".sidebar select").forEach(s => s.value = "");
  document.getElementById("f-search").value = "";
  document.getElementById("f-shownotfound").checked = false;
  applyFilters();
}});

document.getElementById("nav-prev").addEventListener("click", () => {{ cardIndex--; renderCards(); }});
document.getElementById("nav-next").addEventListener("click", () => {{ cardIndex++; renderCards(); }});

document.getElementById("tab-cards").addEventListener("click", () => {{
  document.getElementById("tab-cards").classList.add("active");
  document.getElementById("tab-table").classList.remove("active");
  document.getElementById("cards-view").style.display = "";
  document.getElementById("table-view").style.display = "none";
}});
document.getElementById("tab-table").addEventListener("click", () => {{
  document.getElementById("tab-table").classList.add("active");
  document.getElementById("tab-cards").classList.remove("active");
  document.getElementById("table-view").style.display = "";
  document.getElementById("cards-view").style.display = "none";
}});

applyFilters();
</script>
</body>
</html>
"""


def main() -> None:
    args = _parse_args()
    input_rows = _read_input_rows(args.input)
    evidence_rows_raw = build_evidence_rows(input_rows)
    parsed = write_evidence_csv(evidence_rows_raw, args.evidence_out, args.input)
    build_html(parsed, args.html_out)

    present = sum(1 for r in parsed if r["evidence_status"] == "present")
    not_found = len(parsed) - present
    grounded_present = sum(
        1 for r in parsed if r["evidence_status"] == "present" and r["source_grounding_status"] == "grounded"
    )

    print("Codify evidence layer + viewer build summary")
    print(f"  input rows read:        {len(input_rows)}")
    print(f"  evidence rows written:  {len(parsed)}")
    print(f"  present:                {present}")
    print(f"  not_found:              {not_found}")
    print(f"  grounded present:       {grounded_present}")
    print(f"  evidence CSV:           {args.evidence_out}")
    print(f"  html browser:           {args.html_out}")


if __name__ == "__main__":
    main()
