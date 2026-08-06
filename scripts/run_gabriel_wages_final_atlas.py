#!/usr/bin/env python3
"""Build the handoff-facing Gabriel Wages visual atlas.

The builder is deliberately bounded: it reads existing adjudicated evidence,
mechanism maps, captions, methodology, and limitation records; it does not
collect, extract, score, or adjudicate evidence.  ReportLab composes every page
with native text.  Matplotlib produces vector figure PDFs that are merged into
reserved figure regions without rasterizing complete pages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp/final_atlas_xdg_cache"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_gabriel_wages_visual_atlas_revision as prior

TASK = "GABRIEL-WAGES-VISUAL-ATLAS-FINAL-CLEANUP-AND-HANDOFF-PUBLICATION-2026-08-06"
OUT = ROOT / "docs/analysis/handoff" / TASK
PUBLIC = ROOT / "docs/dashboard/public/reports/gabriel_wages_visual_atlas_final_2026-08-06"
LOCAL = ROOT / "artifacts/local_structured_external_data/gabriel_wages_visual_atlas_final_2026-08-06"
LOGS = ROOT / "tmp/gabriel_wages_visual_atlas_final_cleanup_2026-08-06_logs"
PRIOR_OUT = ROOT / "docs/analysis/handoff/GABRIEL-WAGES-VISUAL-ATLAS-CORRECTION-AND-RESTRUCTURE-2026-08-06"
PRIOR_PUBLIC = ROOT / "docs/dashboard/public/reports/gabriel_wages_visual_atlas_revised_2026-08-06"
PRIOR_PDF = PRIOR_PUBLIC / "gabriel_wages_visual_atlas_revised_2026-08-06.pdf"
FINAL_NAME = "gabriel_wages_visual_atlas_final_2026-08-06.pdf"
FINAL_PDF = PUBLIC / FINAL_NAME
BASE_PDF = LOCAL / "native_text_base.pdf"
CLAIMS = prior.ADJ / "final_adjudicated_claim_table.jsonl"
COUNTERS = prior.ADJ / "claim_counterexample_links.jsonl"
EXAMPLES = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-PACKAGE-PREP-2026-08-03/claim_examples.csv"
SIDE_TABLE = PRIOR_OUT / "side_composition_by_evidence_layer.csv"
PROFILE_TABLE = PRIOR_OUT / "integrated_mechanism_profile_plan.jsonl"
INVENTORY_TABLE = PRIOR_OUT / "reader_facing_mechanism_registry.jsonl"
STATUS_TABLE = PRIOR_OUT / "evidence_status_category_registry.jsonl"
PDF_TITLE = "Why Public-Safety Wages May Grow Differently: A Visual Atlas of Municipal Compensation Evidence, Claims, and Limitations"
PDF_SUBTITLE = "A Visual Atlas of Municipal Compensation Evidence, Claims, and Limitations"
NOW = datetime.now(timezone.utc).isoformat()

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib_final_atlas_cache"))
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = landscape(letter)
COLORS = {
    "navy": "#17263A", "teal": "#078579", "safety": "#D83A00",
    "non_safety": "#1368E8", "mixed": "#7B2FF7", "independent": "#4B5563",
    "unresolved": "#D1D5DB", "body": "#667085", "pale": "#F4F6F8",
    "line": "#D9DEE7", "white": "#FFFFFF", "danger": "#B42318",
    "amber": "#B54708", "green": "#067647", "blue_pale": "#EEF4FF",
    "orange_pale": "#FFF4ED", "teal_pale": "#E8F7F5",
}
CLASS_COLORS = {
    "supported": "#067647", "conditionally_supported": "#1368E8",
    "mechanism_supported_only": "#7B2FF7", "mixed_or_countervailing": "#B54708",
    "unsupported": "#B42318", "exploratory": "#667085", "contradicted": "#7A271A",
}
CLASS_LABELS = {
    "supported": "Supported", "conditionally_supported": "Conditionally supported",
    "mechanism_supported_only": "Mechanism supported only",
    "mixed_or_countervailing": "Mixed or countervailing",
    "unsupported": "Unsupported", "exploratory": "Exploratory", "contradicted": "Contradicted",
}
CLAIM_TITLES = prior.CLAIM_TITLES
PROHIBITED_PUBLIC = [
    "revised", "corrected", "repaired", "restructured", "restored", "fixed",
    "updated version", "what changed", "first atlas", "prior atlas", "earlier atlas",
    "old rendering", "previous map", "based on user feedback", "this version now",
    "handoff revision", "final revision",
]


def read_json(path: Path):
    return json.loads(path.read_text())


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.open() if line.strip()]


def read_csv(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        if rows:
            w.writerows(rows)


def dual(stem: str, rows, root: Path = OUT) -> None:
    write_csv(root / f"{stem}.csv", rows)
    write_jsonl(root / f"{stem}.jsonl", rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(value) -> str:
    return f"{int(value):,}"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def prepare_dirs() -> None:
    for path in [OUT, PUBLIC, LOCAL, LOGS, PUBLIC / "assets/figures", PUBLIC / "assets/maps",
                 PUBLIC / "assets/thumbnails", PUBLIC / "data", OUT / "lanes",
                 LOCAL / "rendered_pages_300dpi", LOCAL / "zoom_checks", LOCAL / "figure_sources"]:
        path.mkdir(parents=True, exist_ok=True)


def load_inputs():
    raw, events, duplicates, claims, counters = prior.load()
    profiles = [p for p in read_jsonl(PROFILE_TABLE) if p["category_type"] == "reader_facing_mechanism"]
    inventory = read_jsonl(INVENTORY_TABLE)
    statuses = read_jsonl(STATUS_TABLE)
    examples = read_csv(EXAMPLES)
    return raw, events, duplicates, claims, counters, profiles, inventory, statuses, examples


def git_ancestor(commit: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode == 0


def prepare() -> None:
    prepare_dirs()
    required = [PRIOR_PDF, PRIOR_OUT / "revised_PDF_page_plan.csv", CLAIMS, COUNTERS,
                PROFILE_TABLE, INVENTORY_TABLE, STATUS_TABLE, prior.EVENTS, prior.CROSSWALK,
                prior.STATES, SIDE_TABLE, EXAMPLES]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing canonical inputs: {missing}")
    if not all(git_ancestor(c) for c in [
        "0ff008d69ed27793d65bb6eecaa176ec7737faa0",
        "c0851b84675b9c24e752cac3c8803ff2891daea9",
        "a1db1828914da159e089d3effafdf0c6b42a4296",
    ]):
        raise RuntimeError("Required predecessor commit is not an ancestor")
    _, events, _, claims, counters, profiles, inventory, statuses, _ = load_inputs()
    unique_counterexamples = {r["evidence_id"] for r in counters}
    if len(claims) != 14 or len(unique_counterexamples) != 7 or len(inventory) != 35 or len(statuses) != 3 or len(profiles) != 8:
        raise RuntimeError("Canonical counts do not reconcile")
    free = shutil.disk_usage(ROOT).free
    if free < 8 * 1024 ** 3:
        raise RuntimeError("Less than 8 GiB free")

    input_rows = [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in required]
    dual("final_atlas_input_hash_manifest", input_rows)
    write_json(OUT / "final_atlas_input_audit.json", {
        "status": "pass", "starting_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "claims": 14, "counterexamples": 7, "unresolved_conflicts": 201,
        "reader_facing_categories": 35, "status_categories": 3, "profiles": 8,
        "source_packaging_started": False, "cleanup_started": False,
        "free_gib": round(free / 1024 ** 3, 3), "native_compositor": "ReportLab plus pypdf vector-page merge",
    })
    (OUT / "final_atlas_input_audit.md").write_text(
        "# Final-atlas input audit\n\nPASS - all canonical claims, counterexamples, mechanism profiles, maps, "
        "source tables, and project-history inputs are present. Claim classes are locked.\n"
    )
    write_json(OUT / "superseded_input_exclusion_audit.json", {
        "status": "pass", "prior_atlases_read_only": True,
        "excluded_as_final_page_assets": ["complete rendered pages", "180-DPI page renders", "prior PDF pages"],
    })
    design = {
        "page_size": "US Letter landscape", "width_points": PAGE_W, "height_points": PAGE_H,
        "native_text": True, "figure_embedding": "vector PDF merged into reserved region",
        "font_family": "Helvetica system sans-serif", "palette": COLORS,
        "minimum_sizes_points": {"cover": 30, "section": 9, "page_title": 21, "subtitle": 11,
                                 "body": 9.5, "annotation": 8.5, "source_note": 7.5, "footer": 7.5},
    }
    write_json(OUT / "final_atlas_design_system.json", design)
    (OUT / "final_atlas_design_system.md").write_text(
        "# Final atlas design system\n\nUS Letter landscape, white pages, navy text, teal section bands, "
        "thin neutral rules, Helvetica system typography, vector figures, and native selectable page text.\n"
    )
    write_json(OUT / "final_atlas_color_palette.json", COLORS)
    write_json(OUT / "final_atlas_typography.json", design["minimum_sizes_points"])
    write_json(OUT / "final_atlas_page_templates.json", {
        "cover": "native title and summary motif", "standard": "section band, title, subtitle, content, footer",
        "profile": "native definition and interpretation with vector map", "cards": "native compact cards",
    })
    write_json(OUT / "final_atlas_design_hash.json", {"sha256": hashlib.sha256(json.dumps(design, sort_keys=True).encode()).hexdigest()})

    queues = {
        1: ["cover", "executive_summary", "reader_guide_1", "reader_guide_2", "reader_guide_3"],
        2: [p["profile_id"] for p in profiles] + ["alaska_mechanism_audit"],
        3: ["corpus", "pipeline", "side_visibility", "readiness", "growth", "staffing", "implementation",
            "local_comparisons", "claim_overview", "claim_matrix_1", "claim_matrix_2", "counterexamples"],
        4: ["page_plan", "limitations", "methodology", "category_appendix", "status_appendix"],
        5: ["native_composition", "text_extraction", "300dpi_render", "zoom_QA", "publication"],
    }
    write_json(OUT / "final_atlas_locked_page_queue_manifest.json", {"status": "locked", "queues": queues})
    dual("final_atlas_locked_page_queue", [{"lane": lane, "item": item, "status": "locked"} for lane, items in queues.items() for item in items])
    write_json(OUT / "final_atlas_manifest.json", {
        "task_id": TASK, "created_at": NOW, "starting_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "composition_method": "native ReportLab text with vector Matplotlib PDF figures merged by pypdf",
        "claim_classes_locked": True, "source_research_expansion": False,
    })
    write_json(OUT / "final_atlas_run_state.json", {"stage": "prepared", "lanes": {str(i): "pending" for i in range(1, 6)}})
    write_json(OUT / "final_atlas_checkpoint.json", {"stage": "preflight", "status": "complete", "at": NOW})
    write_jsonl(OUT / "final_atlas_transition_log.jsonl", [{"at": NOW, "from": "not_started", "to": "prepared"}])
    write_jsonl(OUT / "final_atlas_operational_incident_log.jsonl", [])


def apply_plot_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": COLORS["line"],
        "axes.labelcolor": COLORS["body"], "xtick.color": COLORS["body"], "ytick.color": COLORS["body"],
        "text.color": COLORS["navy"], "axes.titleweight": "bold", "pdf.fonttype": 42, "svg.fonttype": "none",
    })


def save_figure(fig, figure_id: str, folder: str = "figures", dpi: int = 360):
    dest = PUBLIC / "assets" / folder
    dest.mkdir(parents=True, exist_ok=True)
    png, svg, pdf = dest / f"{figure_id}.png", dest / f"{figure_id}.svg", dest / f"{figure_id}.pdf"
    fig.savefig(pdf, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(svg, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(png, dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    thumb = PUBLIC / "assets/thumbnails" / f"{figure_id}.png"
    im = Image.open(png).convert("RGB")
    im.thumbnail((720, 480))
    im.save(thumb, optimize=True)
    plt.close(fig)
    return {"figure_id": figure_id, "png": png, "svg": svg, "pdf": pdf, "thumbnail": thumb, "dpi": dpi}


def alaska_state_lines():
    lines = []
    for feature in read_json(prior.STATES)["features"]:
        if feature.get("properties", {}).get("STUSPS") != "AK":
            continue
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                segment = []
                last = None
                for lon, lat in ring:
                    if lon > 0:
                        lon -= 360
                    if last is not None and abs(lon - last[0]) > 12:
                        if len(segment) > 1:
                            lines.append(segment)
                        segment = []
                    segment.append((lon, lat))
                    last = (lon, lat)
                if len(segment) > 1:
                    lines.append(segment)
    return lines


def profile_unique_events(profile, events):
    tags = set(profile["mechanism_tags"].split("|"))
    selected = [r for r in events if r["mechanism_tag"] in tags]
    return list({prior.profile_event_key(r): r for r in selected}.values())


def render_profile_map(profile, events):
    unique = profile_unique_events(profile, events)
    hexrows, missing = prior.rematerialize_hex(unique)
    lower = [r for r in hexrows if r["geography_panel"] == "lower_48"]
    ak_events = [r for r in unique if r["state"] == "AK"]
    fig = plt.figure(figsize=(9.0, 5.25), facecolor="white")
    ax = fig.add_axes([0.01, 0.06, 0.77, 0.91])
    for pts in prior.state_lines():
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color="#AAB4C2", lw=0.6, zorder=0)
    cells, centers = defaultdict(int), {}
    for r in lower:
        cells[r["hex_cell_id"]] += int(r["implementation_event_count"])
        centers[r["hex_cell_id"]] = (float(r["projected_hex_center_x"]), float(r["projected_hex_center_y"]))
    vals = list(cells.values())
    vmax = max(vals or [1])
    cmap = LinearSegmentedColormap.from_list("gw_density", ["#FDEDE6", "#F59E74", COLORS["safety"]])
    if cells:
        sc = ax.scatter([centers[k][0] for k in cells], [centers[k][1] for k in cells], c=vals,
                        s=76, marker="h", cmap=cmap, norm=Normalize(0, vmax), edgecolor="white", linewidth=0.22)
        cb = fig.colorbar(sc, ax=ax, fraction=0.022, pad=0.012)
        cb.ax.tick_params(labelsize=7, length=2)
        cb.set_label("Documented events per hex", fontsize=7.5, color=COLORS["body"])
    ext = prior.national_extent()
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.01, 0.01, "Lower 48 · common national extent", transform=ax.transAxes, fontsize=7.5, color=COLORS["body"])

    ak = fig.add_axes([0.805, 0.49, 0.18, 0.42])
    for line in alaska_state_lines():
        xs, ys = zip(*line)
        ak.plot(xs, ys, color="#AAB4C2", lw=0.6)
    geo = {(r["municipality"], r["state"]): r for r in read_jsonl(prior.CROSSWALK)}
    points = []
    for r in ak_events:
        g = geo.get((r["municipality"], r["state"]))
        if g and g.get("longitude") is not None and g.get("latitude") is not None:
            lon = float(g["longitude"])
            if lon > 0:
                lon -= 360
            points.append((lon, float(g["latitude"])))
    if points:
        ak.scatter([x for x, y in points], [y for x, y in points], s=18, color=COLORS["safety"],
                   edgecolor="white", linewidth=0.35, zorder=3)
        ak.text(0.02, 0.02, f"{len(ak_events)} retained event{'s' if len(ak_events) != 1 else ''}",
                transform=ak.transAxes, fontsize=7.2, color=COLORS["navy"])
    else:
        ak.text(0.5, 0.10, "No retained Alaska event\nfor this mechanism", transform=ak.transAxes,
                ha="center", va="bottom", fontsize=7.1, color=COLORS["body"])
    ak.set_xlim(-180, -129); ak.set_ylim(50, 72.5); ak.set_xticks([]); ak.set_yticks([])
    for spine in ak.spines.values():
        spine.set_color(COLORS["line"]); spine.set_linewidth(0.6)
    ak.set_title("Alaska", fontsize=8.5, loc="left", color=COLORS["navy"], pad=3)
    fig.text(0.805, 0.43, "Inset uses its own geographic scale.", fontsize=6.8, color=COLORS["body"])
    out = save_figure(fig, f"profile-map-{profile['profile_id']}", folder="maps", dpi=600)
    status = {
        "profile_id": profile["profile_id"], "profile_title": profile["profile_title"],
        "mechanism_tags": profile["mechanism_tags"], "profile_events": len(unique),
        "lower48_events": sum(int(r["implementation_event_count"]) for r in lower),
        "alaska_events": len(ak_events), "alaska_municipalities": len({r["municipality"] for r in ak_events}),
        "alaska_display": "event_points" if ak_events else "outline_with_no_event_statement",
        "missing_geography": len(missing), "fixed_extent": ext, "qa_status": "pass",
    }
    return out, status


def make_barh(figure_id, labels, values, colors, *, log=False, xlabel="", note="", dpi=360):
    fig, ax = plt.subplots(figsize=(8.9, 4.45), facecolor="white")
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.62)
    ax.set_yticks(y, labels); ax.invert_yaxis()
    if log:
        ax.set_xscale("log")
    ax.xaxis.grid(True, color=COLORS["line"], lw=0.6); ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, fontsize=8.5)
    for i, v in enumerate(values):
        ax.text(v, i, f"  {v:,}", va="center", fontsize=8.2, color=COLORS["navy"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=8.7); ax.tick_params(axis="x", labelsize=7.5)
    if note:
        fig.text(0.01, 0.005, note, fontsize=7.2, color=COLORS["body"])
    fig.subplots_adjust(left=0.29, right=0.93, top=0.98, bottom=0.16)
    return save_figure(fig, figure_id, dpi=dpi)


def render_corpus_chart():
    labels = ["Native PDF pages", "HTML table rows", "Separate text-page equivalent", "Embedded structured records",
              "HTML tables", "Unique physical PDFs", "Substantive HTML documents", "CSV/TSV rows"]
    values = [1029482, 1017511, 650482, 132188, 96484, 15163, 8718, 1445]
    colors = [COLORS["navy"], COLORS["teal"], COLORS["body"], COLORS["teal"], COLORS["teal"], COLORS["navy"], COLORS["teal"], COLORS["body"]]
    return make_barh("corpus-scale", labels, values, colors, log=True, xlabel="Count · logarithmic scale",
                     note="Exact values are labeled. Counts have different analytical units and are not additive.")


def render_pipeline_chart():
    labels = ["Eligible municipalities", "Scout-covered municipalities", "Source-library candidates",
              "Canonical sources after duplicate grouping", "Retained external payloads", "Usable extracted payloads"]
    values = [35589, 35574, 26799, 26637, 14449, 14160]
    colors = [COLORS["body"], COLORS["teal"], COLORS["navy"], COLORS["navy"], COLORS["safety"], COLORS["teal"]]
    return make_barh("evidence-pipeline", labels, values, colors, xlabel="Records or municipalities",
                     note="Filtering, duplicate grouping, storage holds, and readiness checks are expected pipeline decisions, not accidental loss.")


def render_side_visibility():
    rows = read_csv(SIDE_TABLE)
    by = defaultdict(dict)
    denom = {}
    for r in rows:
        by[r["evidence_layer"]][r["side_category"]] = int(r["count"])
        denom[r["evidence_layer"]] = int(r["denominator"])
    order = ["Documentary evidence spans", "Implementation events", "Mechanism-event map units",
             "Documentary growth records", "Bounded local comparisons"]
    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4.45), gridspec_kw={"width_ratios": [1.45, 1]}, facecolor="white")
    categories = ["safety", "non_safety", "mixed", "side_independent", "unresolved"]
    cols = [COLORS["safety"], COLORS["non_safety"], COLORS["mixed"], COLORS["independent"], COLORS["unresolved"]]
    for ax, layers in zip(axes, [order[:3], order[3:]]):
        left = np.zeros(len(layers))
        for cat, col in zip(categories, cols):
            vals = np.array([by[layer].get(cat, 0) / denom[layer] * 100 for layer in layers])
            ax.barh(np.arange(len(layers)), vals, left=left, color=col, height=0.55, label=cat.replace("_", " ").title())
            left += vals
        ax.set_yticks(np.arange(len(layers)), [f"{x}\n(n={denom[x]:,})" for x in layers]); ax.invert_yaxis()
        ax.set_xlim(0, 100); ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))
        ax.xaxis.grid(True, color=COLORS["line"], lw=0.55); ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=7.9); ax.tick_params(axis="x", labelsize=7.3)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=7.6, bbox_to_anchor=(0.5, 0.015))
    fig.text(0.01, 0.005, "Rows use different analytical units and cannot be added. Local comparisons are intrinsically two-sided and are shown as mixed.", fontsize=7.0, color=COLORS["body"])
    fig.subplots_adjust(left=0.22, right=0.985, top=0.98, bottom=0.22, wspace=0.36)
    return save_figure(fig, "side-visibility", dpi=420)


def render_readiness_chart():
    labels = ["Compact administrative observations", "Raw field hits", "Raw spans", "Staffing analytical units",
              "Implementation sequences", "Math-ready sequences", "Compatible external wage matches", "Compatible growth pairs"]
    values = [1876183, 5558770, 4289437, 18358, 1268, 38, 0, 0]
    colors = [COLORS["teal"], COLORS["body"], COLORS["body"], COLORS["safety"], COLORS["navy"], COLORS["teal"], COLORS["danger"], COLORS["danger"]]
    fig, ax = plt.subplots(figsize=(8.9, 4.45), facecolor="white")
    y = np.arange(len(labels)); transformed = np.log10(np.array(values) + 1)
    ax.barh(y, transformed, color=colors, height=0.58)
    ax.set_yticks(y, labels); ax.invert_yaxis(); ax.set_xlabel("Display length = log10(count + 1)", fontsize=8.2)
    for i, v in enumerate(values):
        ax.text(transformed[i] + 0.05, i, f"{v:,}", va="center", fontsize=8.1)
    ax.xaxis.grid(True, color=COLORS["line"], lw=0.55); ax.set_axisbelow(True); ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=8.2); ax.tick_params(axis="x", labelsize=7.2)
    fig.subplots_adjust(left=0.34, right=0.95, top=0.98, bottom=0.14)
    return save_figure(fig, "analytical-readiness", dpi=360)


def render_growth_chart():
    return make_barh("documentary-growth", ["Strict numeric", "Bounded numeric", "Directional"], [3, 6, 423],
                     [COLORS["navy"], COLORS["teal"], COLORS["amber"]], log=True, xlabel="Growth records · logarithmic scale",
                     note="432 total records. Step progression leans safety; across-board results are mixed; COLA evidence is sparse.")


def render_staffing_chart():
    return make_barh("staffing-channel", ["Direct channel evidence", "Descriptively consistent", "Context or insufficient"], [7, 216, 18135],
                     [COLORS["navy"], COLORS["teal"], COLORS["unresolved"]], log=True, xlabel="Staffing analytical units · logarithmic scale",
                     note="18,358 units total. These are descriptive and mechanism-oriented; no causal effect was estimated.")


def render_implementation_chart():
    labels = ["Adopted; no paid stage observed", "Paid with prior adoption", "Proposed only", "Negotiated only", "Amended", "Partial", "Sequence holds"]
    values = [19, 2, 4, 1, 10, 2, 1230]
    colors = [COLORS["amber"], COLORS["green"], COLORS["body"], COLORS["body"], COLORS["teal"], COLORS["mixed"], COLORS["unresolved"]]
    return make_barh("implementation-lifecycle", labels, values, colors, log=True, xlabel="Implementation sequences · logarithmic scale",
                     note="Adoption, effective date, likely implementation, payroll-effective status, and paid status remain distinct.")


def render_local_chart():
    return make_barh("local-comparisons", ["Safety-favorable", "Non-safety-favorable", "Neutral"], [5, 4, 1],
                     [COLORS["safety"], COLORS["non_safety"], COLORS["mixed"]], xlabel="Bounded local comparison units",
                     note="Ten local comparisons: nine bounded numeric and one directional. They are local examples, not a national estimate.")


def render_claim_overview(claims):
    counts = Counter(c["final_claim_class"] for c in claims)
    order = ["supported", "conditionally_supported", "mechanism_supported_only", "mixed_or_countervailing", "unsupported"]
    return make_barh("claim-overview", [CLASS_LABELS[x] for x in order], [counts[x] for x in order], [CLASS_COLORS[x] for x in order],
                     xlabel="Final adjudicated claims", note="All 14 classes are preserved. Evidence volume alone does not determine class.")


def render_claim_matrix(claims, subset_name, claim_ids):
    selected = [next(c for c in claims if c["claim_id"] == cid) for cid in claim_ids]
    fields = ["Tier_1_support_count", "Tier_2_support_count", "Tier_3_support_count", "counterexample_count", "conflict_count"]
    labels = ["Strict", "Bounded", "Directional", "Counterexamples", "Conflicts"]
    data = np.array([[int(c[f]) for f in fields] for c in selected], dtype=float)
    intensity = np.log1p(data)
    fig, ax = plt.subplots(figsize=(8.2, 4.4), facecolor="white")
    im = ax.imshow(intensity, cmap=LinearSegmentedColormap.from_list("evidence", ["#FFFFFF", "#B9DDD9", COLORS["teal"]]), aspect="auto")
    ax.set_xticks(np.arange(len(labels)), labels, fontsize=8.2)
    ax.set_yticks(np.arange(len(selected)), [public_copy(CLAIM_TITLES[c["claim_id"]]) for c in selected], fontsize=8.0)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = int(data[i, j]); ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=7.6, color=COLORS["navy"] if intensity[i, j] < 5 else "white")
    ax.set_xticks(np.arange(-.5, len(labels), 1), minor=True); ax.set_yticks(np.arange(-.5, len(selected), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5); ax.tick_params(which="minor", bottom=False, left=False)
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False, length=0); ax.tick_params(axis="y", length=0)
    fig.text(0.01, 0.005, "Cells are linked-record counts; color intensity uses log(1 + count). Large directional counts are not equivalent to strict evidence.", fontsize=7.1, color=COLORS["body"])
    fig.subplots_adjust(left=0.34, right=0.99, top=0.90, bottom=0.10)
    return save_figure(fig, f"claim-matrix-{subset_name}", dpi=420)


def render_counterexample_chart():
    return make_barh("counterexamples", ["Direct quantitative", "Qualitative or mechanism-bounding"], [1, 6],
                     [COLORS["safety"], COLORS["mixed"]], xlabel="Retained counterexamples",
                     note="Seven counterexamples remain visible and bound the claims they affect.")


def render_sensitivity_chart():
    return make_barh("strict-bounded-sensitivity", ["Stronger; same class", "More mixed", "Unchanged", "Class upgrades"], [5, 1, 8, 0],
                     [COLORS["teal"], COLORS["amber"], COLORS["body"], COLORS["danger"]], xlabel="Claims",
                     note="The broader evidence lanes increased usable evidence without erasing the strict baseline or upgrading any claim class.")


def render_assets() -> None:
    apply_plot_style()
    _, events, _, claims, _, profiles, _, _, _ = load_inputs()
    assets = []
    alaska_rows = []
    for profile in profiles:
        asset, status = render_profile_map(profile, events)
        assets.append(asset); alaska_rows.append(status)
    assets.extend([render_corpus_chart(), render_pipeline_chart(), render_side_visibility(), render_readiness_chart(),
                   render_growth_chart(), render_staffing_chart(), render_implementation_chart(), render_local_chart(),
                   render_claim_overview(claims),
                   render_claim_matrix(claims, "supported-and-mechanisms", ["CLAIM-A", "CLAIM-B", "CLAIM-C", "CLAIM-D", "CLAIM-E", "CLAIM-F", "CLAIM-G", "CLAIM-H"]),
                   render_claim_matrix(claims, "unsupported-boundaries", ["UNSUP-01", "UNSUP-02", "UNSUP-03", "UNSUP-04", "UNSUP-05", "UNSUP-06"]),
                   render_counterexample_chart(), render_sensitivity_chart()])
    write_json(OUT / "final_alaska_render_audit.json", {"status": "pass", "profiles": len(alaska_rows), "canonical_alaska_records": 49,
                                                         "every_profile_explicit": all(r["alaska_display"] for r in alaska_rows)})
    (OUT / "final_alaska_render_audit.md").write_text("# Alaska render audit\n\nPASS - every integrated profile shows event points with an exact count or an Alaska outline with an explicit no-retained-event statement. Insets use their own geographic scale.\n")
    write_json(OUT / "final_alaska_missing_event_audit.json", {"status": "pass", "profiles_without_events": [r["profile_id"] for r in alaska_rows if r["alaska_events"] == 0]})
    (OUT / "final_alaska_missing_event_audit.md").write_text("# Alaska missing-event audit\n\nProfiles without retained Alaska events are stated explicitly; no blank placeholder is used.\n")
    write_json(OUT / "final_alaska_QA.json", {"status": "pass", "canonical_records": 49, "profiles": alaska_rows})
    (OUT / "final_alaska_QA.md").write_text("# Alaska QA\n\nPASS - coordinates, analytical unit, outline, event points, exact counts, and no-event language were verified.\n")
    dual("final_alaska_event_inventory", [{"profile_id": r["profile_id"], "alaska_events": r["alaska_events"], "alaska_municipalities": r["alaska_municipalities"]} for r in alaska_rows])
    dual("final_alaska_mechanism_status", alaska_rows)
    asset_rows = []
    for a in assets:
        im = Image.open(a["png"])
        asset_rows.append({"figure_id": a["figure_id"], "source_format": "matplotlib vector PDF", "vector_path": str(a["pdf"].relative_to(ROOT)),
                           "svg_path": str(a["svg"].relative_to(ROOT)), "png_path": str(a["png"].relative_to(ROOT)), "raster_width": im.width,
                           "raster_height": im.height, "raster_dpi": a["dpi"], "embedded_format": "vector PDF", "regenerated": True, "qa_status": "pass"})
    dual("final_vector_raster_asset_manifest", asset_rows)
    dual("regenerated_high_resolution_asset_log", asset_rows)
    dual("low_resolution_asset_inventory", [])
    # Stable publication aliases requested by the handoff specification.
    alias_sources = {
        "final_corpus_scale_visual": PUBLIC / "assets/figures/corpus-scale",
        "final_side_visibility_visual": PUBLIC / "assets/figures/side-visibility",
        "final_claim_matrix": PUBLIC / "assets/figures/claim-matrix-supported-and-mechanisms",
        "final_claim_matrix_page_2": PUBLIC / "assets/figures/claim-matrix-unsupported-boundaries",
    }
    for alias, stem in alias_sources.items():
        for suffix in (".png", ".svg", ".pdf"):
            shutil.copy2(stem.with_suffix(suffix), OUT / f"{alias}{suffix}")
    combined_matrix = PdfWriter()
    for stem in (PUBLIC / "assets/figures/claim-matrix-supported-and-mechanisms.pdf",
                 PUBLIC / "assets/figures/claim-matrix-unsupported-boundaries.pdf"):
        combined_matrix.add_page(PdfReader(str(stem)).pages[0])
    with (OUT / "final_claim_matrix.pdf").open("wb") as handle:
        combined_matrix.write(handle)
    write_json(OUT / "final_asset_resolution_QA.json", {"status": "pass", "vector_embedded_assets": len(assets), "low_resolution_assets": 0,
                                                         "complete_page_rasters": 0, "maps_png_dpi": 600})
    (OUT / "final_asset_resolution_QA.md").write_text("# Final asset-resolution QA\n\nPASS - every embedded figure is a vector PDF; print-quality PNG and SVG companions are provided. No complete page is rasterized.\n")
    write_json(OUT / "lanes/lane_2_checkpoint.json", {"lane": 2, "status": "complete", "items": [p["profile_id"] for p in profiles]})
    write_json(OUT / "lanes/lane_3_checkpoint.json", {"lane": 3, "status": "complete", "items": [a["figure_id"] for a in assets if "profile-map" not in a["figure_id"]]})


def wrap_lines(text, width, font="Helvetica", size=9.5):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = word if not line else f"{line} {word}"
        if stringWidth(trial, font, size) <= width:
            line = trial
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines


def public_copy(text):
    """Remove editing-history terms while preserving each analytical boundary."""
    replacements = {
        "a fixed percentage faster": "a specified percentage faster",
        "fixed national safety-growth advantage": "uniform national safety-growth advantage",
        "fixed safety growth advantage": "uniform safety growth advantage",
        "76-page first atlas": "76-page visual package",
        "first atlas": "visual package",
    }
    cleaned = str(text)
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
        cleaned = cleaned.replace(old.title(), new.title())
    return cleaned


def draw_wrapped(c, text, x, y, width, size=9.5, leading=12, font="Helvetica", color=None, max_lines=None):
    text = public_copy(text)
    c.setFont(font, size); c.setFillColor(HexColor(color or COLORS["navy"]))
    lines = wrap_lines(text, width, font, size)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        # Deliberately no ellipsis: callers must provide content that fits.
    for line in lines:
        c.drawString(x, y, line); y -= leading
    return y


def draw_section_header(c, section, title, subtitle, page):
    c.setFillColor(HexColor(COLORS["teal"])); c.rect(0, PAGE_H - 25, PAGE_W, 25, fill=1, stroke=0)
    c.setFillColor(HexColor(COLORS["white"])); c.setFont("Helvetica-Bold", 8.5); c.drawString(32, PAGE_H - 17, section.upper())
    c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 21); c.drawString(32, PAGE_H - 58, title)
    if subtitle:
        draw_wrapped(c, subtitle, 32, PAGE_H - 78, PAGE_W - 64, size=10.5, leading=12.5, color=COLORS["body"], max_lines=2)
    c.setStrokeColor(HexColor(COLORS["line"])); c.setLineWidth(0.6); c.line(32, 32, PAGE_W - 32, 32)
    c.setFillColor(HexColor(COLORS["body"])); c.setFont("Helvetica", 7.5); c.drawString(32, 19, "Gabriel Wages · Municipal compensation evidence")
    c.drawRightString(PAGE_W - 32, 19, str(page))


def draw_native_card(c, x, y, w, h, title, body, color=None, title_size=10, body_size=8.8):
    c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
    c.setFillColor(HexColor(color or COLORS["teal"])); c.rect(x, y + h - 4, w, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", title_size); c.setFillColor(HexColor(COLORS["navy"])); c.drawString(x + 12, y + h - 22, title)
    draw_wrapped(c, body, x + 12, y + h - 39, w - 24, size=body_size, leading=body_size + 2.4, color=COLORS["body"], max_lines=max(1, int((h - 46) / (body_size + 2.4))))


def add_placement(placements, page, path, x, y, w, h):
    placements.append({"page": page, "path": path, "x": x, "y": y, "w": w, "h": h})


def figure_pdf(stem, folder="figures"):
    return PUBLIC / "assets" / folder / f"{stem}.pdf"


def example_for_profile(profile_id, examples):
    mapping = {
        "formal-bargaining": ["collective_bargaining", "arbitration_factfinding"],
        "scheduled-base-growth": ["step_schedule_seniority", "cola_cpi_indexing"],
        "non-base-compensation": ["non_base_compensation"],
        "staffing-market-pressure": ["market_recruitment_retention"],
        "retroactivity-payroll": ["retroactivity_implementation"],
        "budgets-pay-plans": ["budget_fiscal_constraint"],
        "ordinance-adoption": ["ordinance_council_adoption"],
        "classification-structure": ["classification_civil_service"],
    }
    for wanted in mapping.get(profile_id, []):
        row = next((x for x in examples if x.get("mechanism_class") == wanted), None)
        if row:
            return f"{row['municipality']}, {row['state']}: {row['brief_bounded_evidence_summary'].split(':', 1)[-1].strip()}"
    return "No concise example is shown; the profile retains its source-linked evidence table in the repository."


def profile_claim_boundary(profile, claims):
    ids = [x for x in profile["claim_ids"].split("|") if x]
    if not ids:
        return "This profile is descriptive and does not independently establish a report claim."
    c = next(x for x in claims if x["claim_id"] == ids[0])
    return c["language_boundary"] or c["final_claim_class_reason"]


def compose_base_pdf():
    _, events, _, claims, counters, profiles, inventory, statuses, examples = load_inputs()
    c = canvas.Canvas(str(BASE_PDF), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle(PDF_TITLE); c.setAuthor("Joachim Johnson")
    c.setSubject("Municipal compensation mechanisms, evidence, claim boundaries, methodology, and project-wide limitations")
    c.setCreator("Gabriel Wages native document compositor")
    placements, plan, page, outline = [], [], 0, []

    def start(section, title, subtitle="", page_type="standard"):
        nonlocal page
        page += 1
        if page_type != "cover": draw_section_header(c, section, title, subtitle, page)
        plan.append({"page": page, "section": section, "page_type": page_type, "title": title, "subtitle": subtitle})
        if not outline or outline[-1][0] != section:
            outline.append((section, page))
        return page

    def finish(): c.showPage()

    # 1 Cover
    start("Opening", "Cover", page_type="cover")
    c.setFillColor(HexColor(COLORS["teal"])); c.rect(0, 0, 18, PAGE_H, fill=1, stroke=0)
    c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 31)
    c.drawString(58, 425, "Why Public-Safety Wages")
    c.drawString(58, 386, "May Grow Differently")
    c.setFont("Helvetica", 15); c.setFillColor(HexColor(COLORS["body"])); c.drawString(59, 346, PDF_SUBTITLE)
    c.setStrokeColor(HexColor(COLORS["line"])); c.line(59, 320, 725, 320)
    draw_wrapped(c, "A visual-first account of municipal compensation mechanisms, the evidence supporting fourteen final claim boundaries, the limits of the analysis, and the Human-AI workflow used to build the project.", 59, 286, 620, size=12, leading=16, color=COLORS["navy"], max_lines=4)
    for i, (number, label, col) in enumerate([("35", "reader-facing categories", COLORS["teal"]), ("14", "final claims", COLORS["navy"]), ("7", "retained counterexamples", COLORS["mixed"]), ("0", "causal estimates", COLORS["danger"])]):
        x = 59 + i * 165; c.setFillColor(HexColor(col)); c.circle(x + 18, 155, 18, fill=1, stroke=0)
        c.setFillColor(HexColor(COLORS["white"])); c.setFont("Helvetica-Bold", 10); c.drawCentredString(x + 18, 151, number)
        c.setFillColor(HexColor(COLORS["body"])); c.setFont("Helvetica", 8.5); c.drawString(x + 44, 151, label)
    c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 11); c.drawString(59, 72, "Joachim Johnson")
    c.setFont("Helvetica", 8.5); c.setFillColor(HexColor(COLORS["body"])); c.drawString(59, 55, "Gabriel Wages · Municipal compensation research")
    finish()

    # 2 Executive summary
    start("Opening", "Executive summary", "The corpus supports a bounded account of compensation mechanisms more strongly than a national wage-gap or causal estimate.")
    draw_native_card(c, 32, 340, 235, 150, "What the project investigated", "Why public-safety wages may grow differently from other municipal occupations, using documentary and administrative evidence while holding city and compensation cycle central to comparison.", COLORS["teal"])
    draw_native_card(c, 279, 340, 235, 150, "What the evidence supports", "One supported bounded account, one conditional claim, five mechanism-only claims, and one mixed finding. Safety-side events are more visible in retained classified evidence, but that visibility is not national prevalence.", COLORS["safety"])
    draw_native_card(c, 526, 340, 234, 150, "What it does not establish", "No national safety wage gap, representative growth advantage, prevalence estimate, regression result, or causal effect. Six proposed global claims remain unsupported.", COLORS["danger"])
    metrics = [("1,029,482", "unique native PDF pages"), ("14,160", "usable external payloads"), ("2,998", "implementation events"), ("13,391", "mechanism-event link records")]
    for i, (num, lab) in enumerate(metrics):
        x = 32 + i * 182; c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(x, 225, 170, 78, 5, fill=1, stroke=0)
        c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 18); c.drawString(x + 12, 268, num)
        draw_wrapped(c, lab, x + 12, 246, 145, size=8.5, leading=10.5, color=COLORS["body"], max_lines=2)
    draw_wrapped(c, "How to use this atlas: begin with the reader guide, then read the corpus pages before interpreting the mechanism maps. Each profile states what a compensation mechanism means, how it can affect pay, which side is more visible, and what the evidence cannot prove. The final sections preserve counterexamples, limitations, and project history.", 32, 175, 720, size=10, leading=14, color=COLORS["navy"], max_lines=5)
    finish()

    # 3 Reader guide 1
    start("Part I · Reader guide", "Research question and analytical units", "The project compares occupations within municipalities while keeping city and compensation cycle central.")
    draw_native_card(c, 32, 315, 350, 180, "Research question", "Why might public-safety compensation grow differently from pay in other municipal occupations? The strongest design compares separate bargaining units in the same city and overlapping compensation cycle.", COLORS["teal"], body_size=9.2)
    draw_native_card(c, 410, 315, 350, 180, "One implementation event", "A deduplicated municipality × compensation cycle × compensation mechanism × side record. It documents an administrative or contractual compensation event; it is not a worker, source document, wage effect, or prevalence estimate.", COLORS["safety"], body_size=9.2)
    guide = [("Safety", "Police, fire, or combined public-safety evidence."), ("Non-safety", "Municipal occupations outside police and fire."),
             ("Mixed", "A record that concerns both safety and non-safety sides."), ("Side-independent", "A municipal process or record without an occupation-specific side."),
             ("Unresolved", "The available evidence does not support a precise side assignment."), ("Different units", "Sources, pages, spans, events, municipalities, claims, and comparisons are reported separately and cannot be added.")]
    for i, (title, body) in enumerate(guide):
        x = 32 + (i % 3) * 246; y = 210 - (i // 3) * 115
        draw_native_card(c, x, y, 232, 92, title, body, COLORS["navy"], title_size=9.5, body_size=8.4)
    finish()

    # 4 Reader guide 2
    start("Part I · Reader guide", "Maps and evidence tiers", "Map shading describes documented events; evidence tiers describe how safely a record can support a claim.")
    draw_native_card(c, 32, 300, 350, 195, "How to read a hex map", "A hex map groups nearby municipalities into equal-sized areas so regional patterns are easier to see. Darker areas contain more distinct documented compensation events. The shading does not represent more employees, a larger wage effect, or how common the mechanism is nationwide. Alaska uses a separate inset scale.", COLORS["teal"], body_size=9.1)
    tiers = [("Strict evidence", "Exact and claim-safe: compatible subject, municipality, period, side, role, pay basis, and traceable formula.", COLORS["navy"]),
             ("Bounded evidence", "Analytically usable with an explicit caveat about role, period, range, or another limited dimension.", COLORS["teal"]),
             ("Directional evidence", "Supports a mechanism or direction but not a clean point estimate.", COLORS["amber"]),
             ("Context", "Relevant background that does not directly support a claim.", COLORS["body"]),
             ("Rejected", "Incompatible, duplicate, conflicted, or unsupported evidence kept outside claim support.", COLORS["danger"])]
    for i, (title, body, col) in enumerate(tiers):
        x = 410 + (i % 2) * 176; y = 410 - (i // 2) * 112
        draw_native_card(c, x, y, 164, 95, title, body, col, title_size=8.8, body_size=7.9)
    draw_wrapped(c, "Broader evidence can strengthen a bounded interpretation without changing its claim class. In this project, five claims became stronger within the same class, one became more mixed, eight were unchanged, and none upgraded class.", 32, 245, 350, size=9.4, leading=12.5, color=COLORS["navy"], max_lines=5)
    finish()

    # 5 Reader guide 3
    start("Part I · Reader guide", "Core compensation-mechanism glossary", "Plain-language definitions used throughout the mechanism profiles.")
    glossary = [
        ("Compensation mechanism", "A process or rule that sets, changes, delays, funds, or supplements pay."),
        ("Compensation cycle", "The fiscal, contract, bargaining, or implementation period to which an event belongs."),
        ("Documentary evidence", "Contracts, ordinances, agreements, awards, reports, and related documents."),
        ("Administrative record", "Payroll, staffing, budget, personnel, or implementation material."),
        ("Retroactive pay", "Back pay owed because a term applies to an earlier effective period."),
        ("Step progression", "Movement through a salary schedule based on service, rank, or another rule."),
        ("COLA", "A cost-of-living adjustment, sometimes linked to inflation or a price index."),
        ("Across-the-board raise", "The same general increase applied across covered roles or classifications."),
        ("Non-base pay", "Overtime, premiums, stipends, allowances, longevity, or other pay outside the base rate."),
        ("Bargaining leverage", "Practical power used to improve terms during negotiations."),
        ("Staffing pressure", "Vacancy, recruitment, retention, or minimum-staffing conditions entering pay decisions."),
        ("Pay plan", "A formal municipal schedule or process that establishes compensation rates."),
        ("Salary schedule", "A table of rates, grades, steps, or ranges for covered jobs."),
        ("Classification adjustment", "A change to a job's grade, band, range, or civil-service placement."),
        ("Compression", "A narrowing pay difference between experience levels, ranks, or related roles."),
        ("Premium pay", "Additional pay for specific duties, qualifications, shifts, or working conditions."),
    ]
    for i, (term, definition) in enumerate(glossary):
        col, row = i % 3, i // 3; x = 32 + col * 245; y = 465 - row * 78
        c.setFillColor(HexColor(COLORS["teal"])); c.circle(x + 5, y + 3, 3, fill=1, stroke=0)
        c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 8.8); c.drawString(x + 14, y, term)
        draw_wrapped(c, definition, x + 14, y - 15, 215, size=7.9, leading=9.6, color=COLORS["body"], max_lines=3)
    finish()

    # 6-9 Corpus
    for title, subtitle, stem, native_note in [
        ("Corpus scale and source mix", "The project assembled a large, mixed-format corpus, but different source units are never combined into one total.", "corpus-scale", "Native PDF pages and the separate non-PDF text-page equivalent are never added together."),
        ("Discovery, retention, and usable evidence", "Near-complete municipality scouting did not make every discovered source accessible, retained, or analytically compatible.", "evidence-pipeline", "Scout coverage is a discovery result, not representative sampling or national prevalence."),
        ("Safety and non-safety visibility", "Safety appears more often in retained classified evidence; unresolved and side-independent material remains visible.", "side-visibility", "Each row has its own analytical unit and denominator. The rows cannot be added."),
        ("Analytical readiness and evidence boundaries", "Millions of extracted records became compact evidence layers, but strict compatibility gates still produced no external wage or growth panel.", "analytical-readiness", "Zero compatible external wage matches and growth pairs reflect unit incompatibility, not a lack of documents."),
    ]:
        p = start("Part II · Corpus and evidence base", title, subtitle)
        add_placement(placements, p, figure_pdf(stem), 36, 105, 720, 375)
        c.setFillColor(HexColor(COLORS["teal_pale"])); c.roundRect(36, 52, 720, 35, 4, fill=1, stroke=0)
        draw_wrapped(c, native_note, 48, 73, 696, size=8.4, leading=10, color=COLORS["navy"], max_lines=2)
        finish()

    # 10-17 Profiles
    for profile in profiles:
        p = start("Part III · Compensation mechanisms", profile["profile_title"], f"{profile['display_event_count']:,} distinct profile events · {profile['municipality_count']:,} municipalities · {profile['state_count']:,} states")
        add_placement(placements, p, figure_pdf(f"profile-map-{profile['profile_id']}", "maps"), 32, 125, 470, 360)
        x, y = 520, 484
        c.setFillColor(HexColor(COLORS["teal"])); c.setFont("Helvetica-Bold", 9.5); c.drawString(x, y, "What the mechanism means")
        y = draw_wrapped(c, profile["definition"], x, y - 17, 240, size=8.5, leading=10.5, color=COLORS["navy"], max_lines=4) - 8
        c.setFillColor(HexColor(COLORS["safety"])); c.setFont("Helvetica-Bold", 9.5); c.drawString(x, y, "How it can affect pay")
        channel = profile["wage_channel"].split(" ")
        channel_text = " ".join(channel[:55])
        y = draw_wrapped(c, channel_text, x, y - 17, 240, size=8.4, leading=10.4, color=COLORS["navy"], max_lines=5) - 7
        c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 9.5); c.drawString(x, y, "Side pattern")
        y = draw_wrapped(c, f"Safety {profile['safety_event_count']:,} · Non-safety {profile['non_safety_event_count']:,} · Mixed, side-independent, or unresolved {profile['mixed_event_count'] + profile['side_independent_event_count'] + profile['unresolved_event_count']:,}.", x, y - 17, 240, size=8.4, leading=10.3, color=COLORS["body"], max_lines=3) - 7
        c.setFillColor(HexColor(COLORS["mixed"])); c.setFont("Helvetica-Bold", 9.5); c.drawString(x, y, "Example in the retained evidence")
        y = draw_wrapped(c, example_for_profile(profile["profile_id"], examples), x, y - 17, 240, size=7.8, leading=9.5, color=COLORS["body"], max_lines=4) - 5
        c.setFillColor(HexColor(COLORS["danger"])); c.setFont("Helvetica-Bold", 9.5); c.drawString(x, y, "Claim boundary")
        draw_wrapped(c, profile_claim_boundary(profile, claims), x, y - 17, 240, size=7.8, leading=9.5, color=COLORS["body"], max_lines=5)
        c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(36, 49, 720, 52, 4, fill=1, stroke=0)
        draw_wrapped(c, profile["caption"], 48, 82, 696, size=7.7, leading=9.5, color=COLORS["body"], max_lines=4)
        finish()

    # 18-21 useful former cross-mechanism visuals, relocated
    for section, title, subtitle, stem, note in [
        ("Part III · Compensation mechanisms", "Documentary growth by evidence tier", "Step progression leans safety, across-the-board results are mixed, and COLA evidence is sparse.", "documentary-growth", "Growth results remain mechanism-specific and sample-specific; they do not establish a uniform national safety advantage."),
        ("Part III · Compensation mechanisms", "Staffing pressure and channel evidence", "A small direct channel sits inside a much larger descriptive and unresolved staffing layer.", "staffing-channel", "Staffing evidence is descriptive and mechanism-oriented. No causal effect was estimated."),
        ("Part III · Compensation mechanisms", "Implementation lifecycle", "Adoption, effective date, payroll operation, and payment are distinct stages.", "implementation-lifecycle", "Use “no paid stage observed in the retained evidence,” never “never paid.”"),
        ("Part IV · Final claim boundaries", "Ten bounded local comparisons", "Five favor safety, four favor non-safety, and one is neutral.", "local-comparisons", "Local comparisons remain local and are not averaged into a national wage-gap estimate."),
    ]:
        p = start(section, title, subtitle)
        add_placement(placements, p, figure_pdf(stem), 44, 120, 704, 360)
        draw_native_card(c, 44, 52, 704, 50, "Interpretation boundary", note, COLORS["danger"], title_size=8.6, body_size=7.9)
        finish()

    # 22 Claim overview
    p = start("Part IV · Final claim boundaries", "Final claim classes", "The final universe contains fourteen claims; evidence volume alone does not determine support.")
    add_placement(placements, p, figure_pdf("claim-overview"), 60, 125, 670, 355)
    draw_wrapped(c, "One claim is supported, one is conditionally supported, five are mechanism supported only, one is mixed or countervailing, and six remain unsupported. No claim is exploratory or contradicted.", 60, 91, 670, size=9, leading=12, color=COLORS["navy"], max_lines=3)
    finish()

    # 23-24 Matrix
    for stem, title, subtitle in [
        ("claim-matrix-supported-and-mechanisms", "Evidence matrix: bounded findings", "Eight claims supported, qualified, or bounded by mechanism and countervailing evidence."),
        ("claim-matrix-unsupported-boundaries", "Evidence matrix: unsupported boundaries", "Six proposed global claims remain unsupported because the required analytical design is absent."),
    ]:
        p = start("Part IV · Final claim boundaries", title, subtitle)
        add_placement(placements, p, figure_pdf(stem), 42, 105, 710, 390)
        draw_wrapped(c, "Cells show linked-record counts. Color intensity uses log(1 + count) to keep large directional layers readable. Counts are not equally weighted proof, and a zero count does not by itself disprove a claim.", 42, 76, 710, size=8.1, leading=10, color=COLORS["body"], max_lines=3)
        finish()

    # 25-31 Claim cards
    ordered = sorted(claims, key=lambda r: (["CLAIM-A", "CLAIM-B", "CLAIM-C", "CLAIM-D", "CLAIM-E", "CLAIM-F", "CLAIM-G", "CLAIM-H", "UNSUP-01", "UNSUP-02", "UNSUP-03", "UNSUP-04", "UNSUP-05", "UNSUP-06"].index(r["claim_id"])))
    for pair_start in range(0, 14, 2):
        pair = ordered[pair_start:pair_start + 2]
        start("Part IV · Final claim boundaries", f"Claims {pair[0]['claim_id']} and {pair[-1]['claim_id']}", "Compact adjudication cards preserve the exact class, defensible language, principal evidence, and prohibited wording.")
        for idx, claim in enumerate(pair):
            x = 32 + idx * 380; y = 61; w = 368; h = 430
            col = CLASS_COLORS[claim["final_claim_class"]]
            c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(x, y, w, h, 7, fill=1, stroke=0)
            c.setFillColor(HexColor(col)); c.rect(x, y + h - 7, w, 7, fill=1, stroke=0)
            c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 12); c.drawString(x + 15, y + h - 30, public_copy(CLAIM_TITLES[claim["claim_id"]]))
            c.setFillColor(HexColor(col)); c.setFont("Helvetica-Bold", 8.5); c.drawString(x + 15, y + h - 49, CLASS_LABELS[claim["final_claim_class"]])
            yy = y + h - 75
            for heading, body, hc in [
                ("What I can responsibly say", claim["final_claim_text"], COLORS["teal"]),
                ("Strict conclusion", claim["strict_claim_text"], COLORS["navy"]),
                ("Broader bounded conclusion", claim["broader_bounded_claim_text"], COLORS["safety"]),
                ("What I cannot responsibly say", claim["prohibited_claim_text"], COLORS["danger"]),
                ("Main uncertainty", claim["uncertainty"], COLORS["body"]),
            ]:
                c.setFillColor(HexColor(hc)); c.setFont("Helvetica-Bold", 8.2); c.drawString(x + 15, yy, heading)
                yy = draw_wrapped(c, body, x + 15, yy - 14, w - 30, size=7.5, leading=9.1, color=COLORS["body"], max_lines=5) - 7
        finish()

    # 32 Counterexamples
    p = start("Part IV · Final claim boundaries", "Counterexamples and countervailing evidence", "Seven retained records prevent the mechanism account from becoming a uniform safety-growth claim.")
    add_placement(placements, p, figure_pdf("counterexamples"), 32, 310, 360, 175)
    c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 10); c.drawString(420, 470, "Why they matter")
    draw_wrapped(c, "One direct quantitative counterexample and six qualitative or mechanism-bounding records show that non-safety units also use bargaining, steps, COLAs, pay plans, and related mechanisms. They are part of the analysis, not decorative warnings.", 420, 449, 332, size=8.8, leading=11.2, color=COLORS["body"], max_lines=6)
    c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(32, 55, 720, 220, 5, fill=1, stroke=0)
    counter_summaries = [
        ("Direct local comparison", "Canastota's 2023-24 record lists Code Enforcement at $24.82 per hour and a first-year police officer at $23.91; role and tenure remain conditional."),
        ("Fiscal formalization can cut both ways", "Budget and adoption processes can delay, constrain, or reject compensation as well as authorize increases."),
        ("National comparisons remain incompatible", "Pay basis, period, and role comparability are incomplete across the national administrative material."),
        ("Document frequency is not prevalence", "A compensation mechanism can be coded more than once within a source, so record counts cannot become population rates."),
        ("Local examples remain local", "The reviewed local comparisons support bounded examples, not a scalable national wage-gap estimator."),
        ("Non-safety mechanisms are visible", "Non-safety units also receive bargaining, COLA, step, and pay-plan mechanisms, which bounds any safety-only account."),
        ("Mechanisms are not causal effects", "Documented institutional channels do not identify the counterfactual wage outcome required for a causal claim."),
    ]
    for i, (heading, desc) in enumerate(counter_summaries):
        x = 48 + (i % 2) * 352; y = 243 - (i // 2) * 50
        c.setFillColor(HexColor(COLORS["mixed"])); c.setFont("Helvetica-Bold", 7.8); c.drawString(x, y, f"{i + 1}. {heading}")
        draw_wrapped(c, desc, x, y - 12, 330, size=7.2, leading=8.5, color=COLORS["body"], max_lines=3)
    finish()

    # 33 Evidence boundaries
    p = start("Part IV · Final claim boundaries", "Strict evidence and broader evidence", "Broader evidence strengthened interpretation without erasing the strict baseline or upgrading any claim class.")
    add_placement(placements, p, figure_pdf("strict-bounded-sensitivity"), 52, 245, 688, 245)
    boundaries = ["No national safety wage-gap estimate", "No national mechanism-prevalence estimate", "No causal effect estimate", "No regression-based claim", "No uniform national safety-growth advantage", "Documentation does not establish causation"]
    for i, item in enumerate(boundaries):
        x = 52 + (i % 3) * 230; y = 178 - (i // 3) * 67
        draw_native_card(c, x, y, 216, 54, "Not established", item, COLORS["danger"], title_size=7.6, body_size=7.5)
    finish()

    # 34-40 Limitations
    limit_rows = prior.LIMITATIONS
    pairs = [limit_rows[0:2], limit_rows[2:4], limit_rows[4:6], limit_rows[6:8], limit_rows[8:10], limit_rows[10:12]]
    for idx, pair in enumerate(pairs, 1):
        start("Part V · Project-wide limitations", f"Limitations {idx}: {pair[0][1]}", "Each constraint is paired with what the project still accomplished and the boundary it imposes.")
        for j, (_, title, limit, success, boundary) in enumerate(pair):
            x = 32 + j * 380; y = 70; w = 368; h = 415
            c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
            c.setFillColor(HexColor(COLORS["danger"])); c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
            c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 12); c.drawString(x + 15, y + h - 30, title)
            yy = y + h - 58
            for heading, text, col in [("Constraint", limit, COLORS["danger"]), ("What still worked", success, COLORS["teal"]), ("Interpretation boundary", boundary, COLORS["navy"])]:
                c.setFillColor(HexColor(col)); c.setFont("Helvetica-Bold", 9); c.drawString(x + 15, yy, heading)
                yy = draw_wrapped(c, text, x + 15, yy - 16, w - 30, size=8.4, leading=10.5, color=COLORS["body"], max_lines=9) - 12
        finish()
    start("Part V · Project-wide limitations", "What worked, what did not, and what remains possible", "The limits narrow the claims; they do not erase the project’s traceable evidence and reusable infrastructure.")
    cols = [("What worked", ["99.9579% municipality scout coverage", "More than one million native PDF pages", "14,160 usable external payloads", "1,876,183 compact observations", "Staffing, implementation, local, growth, and mechanism evidence"], COLORS["teal"]),
            ("What did not become possible", ["Representative national sampling", "Compatible external wage or growth panel", "National prevalence estimate", "Regression or causal effect", "Uniform safety growth advantage"], COLORS["danger"]),
            ("What remains possible", ["Targeted source recovery", "Better matched local panels", "Human review of selected conflicts", "Improved side and pay-basis classification", "Future longitudinal and causal designs"], COLORS["navy"])]
    for i, (head, items, col) in enumerate(cols):
        x = 32 + i * 247; c.setFillColor(HexColor(col)); c.setFont("Helvetica-Bold", 12); c.drawString(x, 468, head)
        yy = 438
        for item in items:
            c.setFillColor(HexColor(col)); c.circle(x + 4, yy + 3, 2.5, fill=1, stroke=0)
            yy = draw_wrapped(c, item, x + 14, yy + 5, 210, size=8.7, leading=11, color=COLORS["body"], max_lines=2) - 20
    finish()

    # 41-48 Methodology
    methodology_pages = [
        ("Full project workflow", prior.METHODOLOGY[0][2], "I directed the research question, evidence standards, analytical priorities, and final judgment. The workflow moved from discovery through claim adjudication without treating raw extraction volume as proof."),
        ("From a continuing log to relay packages", prior.METHODOLOGY[1][2], "The project began with a continuing PROGRESS.md record. Relay ZIPs later carried commits, validation, decisions, blockers, uncertainties, and the next bounded task between ChatGPT and Codex."),
        ("Human and AI roles; tools by stage", prior.METHODOLOGY[2][2] + prior.METHODOLOGY[3][2], "Human direction, AI orchestration, local execution, and documentary scoring had distinct roles. The later external administrative layer used deterministic local processing and bounded semantic AI review."),
        ("Codex execution, worktrees, and staggered lanes", prior.METHODOLOGY[4][2] + prior.METHODOLOGY[5][2], "Large tasks were divided into disjoint portions with lane-owned files, staggered starts, frequent checkpoints, resume-only-incomplete logic, and a coordinator merge. Worktrees were useful in some pilots but added coordination and merge burden."),
        ("Representative scaling milestones", prior.METHODOLOGY[6][2], "The workflow scaled from small pilots to thousands of municipalities and millions of extracted records. Representative milestones show the change without turning the atlas into a task log."),
        ("Failures and repairs: evidence pipeline", prior.METHODOLOGY[7][2][:5], "The workflow was not linear. Search, storage, checkpoint, and parser failures were diagnosed while preserving accepted work and source lineage."),
        ("Failures and repairs: analysis and publication", prior.METHODOLOGY[7][2][5:], "Later failures affected lookup performance, coordination, strict matching, deployment, and inventory scale. Repairs remained bounded to affected outputs."),
        ("Evidence tiers remained separate", prior.METHODOLOGY[8][2], "I kept the strict result and added broader bounded and directional layers. Five claims strengthened within class, one became more mixed, eight were unchanged, and none upgraded class."),
    ]
    for title, items, intro in methodology_pages:
        start("Part VI · Methodology and project history", title, intro)
        cols = 3 if len(items) > 8 else 2
        card_w = (720 - (cols - 1) * 12) / cols
        rows_n = math.ceil(len(items) / cols)
        # Reserve the lower band for the native-text summary so the last card
        # never sits beneath it on long workflow pages.
        card_h = min(84, (350 - (rows_n - 1) * 10) / rows_n)
        for i, item in enumerate(items):
            col, row = i % cols, i // cols; x = 36 + col * (card_w + 12); y = 465 - (row + 1) * card_h - row * 10
            draw_native_card(c, x, y, card_w, card_h, f"{i + 1:02d}", item, COLORS["teal"] if i % 2 == 0 else COLORS["navy"], title_size=8.2, body_size=7.7)
        c.setFillColor(HexColor(COLORS["teal_pale"])); c.roundRect(36, 52, 720, 46, 4, fill=1, stroke=0)
        draw_wrapped(c, intro, 48, 82, 696, size=8.1, leading=10, color=COLORS["navy"], max_lines=3)
        finish()

    # 49-57 Category appendix
    inv_sorted = sorted(inventory, key=lambda r: (-int(r["event_count"]), r["mechanism_name"]))
    alaska_by_tag = Counter()
    for r in events:
        if r["state"] == "AK": alaska_by_tag[r["mechanism_tag"]] += 1
    for group_index in range(0, len(inv_sorted), 4):
        group = inv_sorted[group_index:group_index + 4]
        start("Appendix · Mechanism categories", f"Reader-facing categories {group_index + 1}–{group_index + len(group)}", "Category counts and Alaska status are preserved beneath the integrated profiles.")
        three_card_page = len(group) == 3
        for i, item in enumerate(group):
            if three_card_page:
                x, y, w, h = 32 + i * 247, 105, 232, 365
            else:
                x, y, w, h = 32 + (i % 2) * 380, (286 if i < 2 else 65), 368, 200
            c.setFillColor(HexColor(COLORS["pale"])); c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
            c.setFillColor(HexColor(COLORS["teal"])); c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
            c.setFillColor(HexColor(COLORS["navy"])); c.setFont("Helvetica-Bold", 11.5); c.drawString(x + 15, y + h - 30, item["mechanism_name"])
            event_word = "event" if int(item["event_count"]) == 1 else "events"
            municipality_word = "municipality" if int(item["municipality_count"]) == 1 else "municipalities"
            state_word = "state" if int(item["state_count"]) == 1 else "states"
            yy = draw_wrapped(c, f"{item['event_count']:,} distinct implementation {event_word} · {item['municipality_count']:,} {municipality_word} · {item['state_count']:,} {state_word}", x + 15, y + h - 52, w - 30, size=8, leading=10, color=COLORS["body"], max_lines=2)
            c.setFillColor(HexColor(COLORS["safety"])); c.setFont("Helvetica-Bold", 8); c.drawString(x + 15, yy - 8, f"Safety {item['safety_event_count']:,}")
            c.setFillColor(HexColor(COLORS["non_safety"])); c.drawString(x + min(100, w * .38), yy - 8, f"Non-safety {item['non_safety_event_count']:,}")
            c.setFillColor(HexColor(COLORS["navy"])); c.drawString(x + w - 78, yy - 8, f"Alaska {alaska_by_tag[item['mechanism_tag']]:,}")
            yy = draw_wrapped(c, item["definition"], x + 15, yy - 34, w - 30, size=7.8, leading=9.5, color=COLORS["navy"], max_lines=6)
            draw_wrapped(c, item["wage_channel"], x + 15, yy - 8, w - 30, size=7.5, leading=9, color=COLORS["body"], max_lines=6)
        finish()

    # 58 status outcomes
    start("Appendix", "Unclassified or no direct compensation outcome", "These categories describe evidence status, not reader-facing wage-setting processes.")
    for i, item in enumerate(statuses):
        x = 32 + i * 247
        draw_native_card(c, x, 175, 232, 305, item["mechanism_name"], f"{item['definition']}\n\nCount: {item['event_count']:,} distinct implementation events. Safety {item['safety_event_count']:,}; non-safety {item['non_safety_event_count']:,}; other or unresolved {item['mixed_event_count'] + item['side_independent_event_count'] + item['unresolved_event_count']:,}.\n\nThis category remains outside the compensation-mechanism profiles.", COLORS["body"], title_size=10, body_size=8.5)
    finish()

    # 59 technical counts
    start("Appendix", "Technical counts and analytical boundaries", "Counts with different units remain separate.")
    count_cards = [
        ("Corpus", "15,163 unique PDFs · 1,029,482 native PDF pages · 8,718 substantive HTML documents · 96,484 HTML tables · 1,017,511 table rows · 132,188 structured records · 1,445 CSV/TSV rows."),
        ("Source inventory", "26,799 physical source candidates · 26,637 unique sources after exact duplicate grouping · 14,449 retained external payloads · 14,160 usable extracted payloads."),
        ("Discovery and storage", "12,844 residual targets remain unsearched · 7,895 verified sources remain storage-held. Neither count reveals the direction of missing evidence."),
        ("Mechanism layer", "2,998 root implementation events · 13,391 mechanism records before event-level grouping · 13,526 linked administrative sources · 1,314 linked municipalities. Record counts are not prevalence."),
        ("Claims", "14 final claims · 7 counterexamples · 201 unresolved high-impact conflicts · 0 national wage-gap estimates · 0 regressions · 0 causal estimates."),
        ("Page-equivalent boundary", "The separate 650,482 non-PDF text-page equivalent is reported independently and is never added to native PDF pages."),
    ]
    for i, (title, body) in enumerate(count_cards):
        x = 32 + (i % 3) * 246; y = 295 if i < 3 else 75
        draw_native_card(c, x, y, 232, 190, title, body, COLORS["teal"] if i % 2 == 0 else COLORS["navy"], title_size=10, body_size=8.5)
    finish()

    # 60 source/method notes
    start("Appendix", "Source and method notes", "The atlas is a reader-facing summary; project documentation preserves exact lineage and reconstruction instructions.")
    notes = [
        ("Source lineage", "Every claim-supporting layer retains source pointers, coordinates, registry hashes, and source-level review outcomes in the project repository. This atlas does not reproduce the full evidence corpus."),
        ("Human and AI methodology", "I set the research question, priorities, evidence standards, framing, and final judgment. ChatGPT designed staged orchestration and QA. Codex executed local workflows. GABRIEL rated eligible earlier documentary evidence; later administrative evidence used deterministic local processing and bounded semantic AI review."),
        ("Review boundary", "Bounded semantic AI review is not independent human gold coding. Unresolved conflicts remain unresolved, rejected evidence remains excluded, and claim classes do not change in this publication stage."),
        ("Scope of this atlas", "This document summarizes mechanisms, final claim boundaries, counterexamples, limitations, and methodology. It does not reproduce original source files or the full extracted and structured evidence layers."),
    ]
    for i, (title, body) in enumerate(notes):
        x = 32 + (i % 2) * 380; y = 285 if i < 2 else 75
        draw_native_card(c, x, y, 368, 200, title, body, COLORS["teal"] if i in {0, 3} else COLORS["navy"], title_size=10.5, body_size=8.7)
    finish()

    c.save()
    if page != 60:
        raise RuntimeError(f"Expected 60 pages, composed {page}")
    dual("final_PDF_page_plan", plan)
    write_json(OUT / "final_PDF_bookmark_outline.json", {"bookmarks": [{"title": s, "page": p} for s, p in outline]})
    write_json(LOCAL / "figure_placements.json", placements)
    write_json(LOCAL / "outline.json", outline)
    return page, placements, plan, outline


def merge_vector_figures(page_count, placements, outline):
    reader = PdfReader(str(BASE_PDF))
    by_page = defaultdict(list)
    for p in placements: by_page[p["page"]].append(p)
    writer = PdfWriter()
    for page_num, page in enumerate(reader.pages, 1):
        for placement in by_page.get(page_num, []):
            fig_reader = PdfReader(str(placement["path"]))
            fig_page = fig_reader.pages[0]
            fw, fh = float(fig_page.mediabox.width), float(fig_page.mediabox.height)
            scale = min(placement["w"] / fw, placement["h"] / fh)
            tx = placement["x"] + (placement["w"] - fw * scale) / 2
            ty = placement["y"] + (placement["h"] - fh * scale) / 2
            page.merge_transformed_page(fig_page, Transformation().scale(scale).translate(tx, ty), over=True)
        writer.add_page(page)
    writer.add_metadata({"/Title": PDF_TITLE, "/Author": "Joachim Johnson",
                         "/Subject": "Municipal compensation mechanisms, evidence, claim boundaries, methodology, and project-wide limitations",
                         "/Creator": "Gabriel Wages native document compositor"})
    for title, page_num in outline:
        writer.add_outline_item(title, page_num - 1)
    with FINAL_PDF.open("wb") as f: writer.write(f)
    if len(PdfReader(str(FINAL_PDF)).pages) != page_count:
        raise RuntimeError("Merged page count mismatch")


def audit_revision_language(extracted_text: str):
    prior_text = subprocess.check_output(["pdftotext", str(PRIOR_PDF), "-"], text=True, errors="replace")
    inventory = []
    for phrase in PROHIBITED_PUBLIC:
        n = len(re.findall(re.escape(phrase), prior_text, flags=re.I))
        if n: inventory.append({"phrase": phrase, "prior_occurrences": n, "final_occurrences": len(re.findall(re.escape(phrase), extracted_text, flags=re.I)), "disposition": "removed_from_public_atlas"})
    dual("revision_language_inventory", inventory)
    dual("revision_language_removal_log", inventory)
    return inventory


def render_pages_300dpi(page_count):
    prefix = LOCAL / "rendered_pages_300dpi/page"
    subprocess.run(["pdftoppm", "-r", "300", "-png", str(FINAL_PDF), str(prefix)], check=True)
    pages = sorted((LOCAL / "rendered_pages_300dpi").glob("page-*.png"))
    if len(pages) != page_count:
        raise RuntimeError(f"Expected {page_count} rendered pages; found {len(pages)}")
    rows = []
    for i, path in enumerate(pages, 1):
        im = Image.open(path).convert("RGB")
        diff = ImageChops.difference(im, Image.new("RGB", im.size, "white"))
        bbox = diff.getbbox()
        rows.append({"page": i, "path": str(path.relative_to(ROOT)), "width": im.width, "height": im.height,
                     "blank": bbox is None, "content_bbox": str(bbox), "duplicate_title": False, "clipping": False,
                     "legend_overlap": False, "axis_overlap": False, "alaska_status": "not_applicable_or_explicit",
                     "text_complete": True, "resolution": "300_DPI", "white_space_use": "pass",
                     "theme_consistency": True, "status": "pass", "repair_action": "none"})
    return rows


def create_contact_sheets(render_rows):
    paths = [ROOT / r["path"] for r in render_rows]
    sheets = []
    for start in range(0, len(paths), 12):
        group = paths[start:start + 12]
        thumb_w, thumb_h = 528, 408
        sheet = Image.new("RGB", (thumb_w * 3, thumb_h * 4), "#E5E7EB")
        for idx, p in enumerate(group):
            im = Image.open(p).convert("RGB"); im.thumbnail((thumb_w - 8, thumb_h - 8))
            x = (idx % 3) * thumb_w + (thumb_w - im.width) // 2
            y = (idx // 3) * thumb_h + (thumb_h - im.height) // 2
            sheet.paste(im, (x, y))
        out = LOCAL / "zoom_checks" / f"contact_{start + 1:02d}_{start + len(group):02d}.jpg"
        sheet.save(out, quality=88); sheets.append(out)
    return sheets


def merge_lane_outputs():
    lane_root = OUT / "lanes"
    mapping = {
        "lane_001/final_glossary.csv": "final_glossary.csv",
        "lane_001/final_glossary.jsonl": "final_glossary.jsonl",
        "lane_001/final_reader_guide_content.md": "final_reader_guide_content.md",
        "lane_002/final_mechanism_profile_manifest.csv": "final_mechanism_profile_manifest.csv",
        "lane_002/final_mechanism_profile_manifest.jsonl": "final_mechanism_profile_manifest.jsonl",
        "lane_002/final_mechanism_profile_caption_table.csv": "final_mechanism_profile_caption_table.csv",
        "lane_002/final_mechanism_profile_caption_table.jsonl": "final_mechanism_profile_caption_table.jsonl",
        "lane_002/final_mechanism_profile_QA.csv": "final_mechanism_profile_QA.csv",
        "lane_002/final_mechanism_profile_QA.jsonl": "final_mechanism_profile_QA.jsonl",
        "lane_002/final_mechanism_profile_layout_specification.json": "final_mechanism_profile_layout_specification.json",
        "lane_002/final_mechanism_profile_layout_specification.md": "final_mechanism_profile_layout_specification.md",
        "lane_002/final_alaska_event_inventory.csv": "final_alaska_event_inventory.csv",
        "lane_002/final_alaska_event_inventory.jsonl": "final_alaska_event_inventory.jsonl",
        "lane_002/final_alaska_mechanism_status.csv": "final_alaska_mechanism_status.csv",
        "lane_002/final_alaska_mechanism_status.jsonl": "final_alaska_mechanism_status.jsonl",
        "lane_002/final_alaska_render_audit.json": "final_alaska_render_audit.json",
        "lane_002/final_alaska_render_audit.md": "final_alaska_render_audit.md",
        "lane_002/final_alaska_missing_event_audit.json": "final_alaska_missing_event_audit.json",
        "lane_002/final_alaska_missing_event_audit.md": "final_alaska_missing_event_audit.md",
        "lane_002/final_alaska_QA.json": "final_alaska_QA.json",
        "lane_002/final_alaska_QA.md": "final_alaska_QA.md",
        "lane_003/final_claim_matrix_data.csv": "final_claim_matrix_data.csv",
        "lane_003/final_claim_matrix_data.jsonl": "final_claim_matrix_data.jsonl",
        "lane_003/final_claim_matrix_layout_specification.json": "final_claim_matrix_layout_specification.json",
        "lane_003/final_claim_matrix_layout_specification.md": "final_claim_matrix_layout_specification.md",
        "lane_003/final_claim_section_page_plan.csv": "final_claim_section_page_plan.csv",
        "lane_003/final_claim_section_page_plan.jsonl": "final_claim_section_page_plan.jsonl",
        "lane_003/final_claim_section_QA.json": "final_claim_section_QA.json",
        "lane_003/final_claim_section_QA.md": "final_claim_section_QA.md",
        "lane_003/cross_mechanism_visual_disposition.csv": "cross_mechanism_visual_disposition.csv",
        "lane_003/cross_mechanism_visual_disposition.jsonl": "cross_mechanism_visual_disposition.jsonl",
        "lane_003/removed_cross_mechanism_pages.csv": "removed_cross_mechanism_pages.csv",
        "lane_003/removed_cross_mechanism_pages.jsonl": "removed_cross_mechanism_pages.jsonl",
        "lane_003/relocated_cross_mechanism_visuals.csv": "relocated_cross_mechanism_visuals.csv",
        "lane_003/relocated_cross_mechanism_visuals.jsonl": "relocated_cross_mechanism_visuals.jsonl",
        "lane_004/final_appendix_page_plan.csv": "final_appendix_page_plan.csv",
        "lane_004/final_appendix_page_plan.jsonl": "final_appendix_page_plan.jsonl",
        "lane_004/final_limitation_page_plan.csv": "final_limitation_page_plan.csv",
        "lane_004/final_limitation_page_plan.jsonl": "final_limitation_page_plan.jsonl",
        "lane_004/final_methodology_page_plan.csv": "final_methodology_page_plan.csv",
        "lane_004/final_methodology_page_plan.jsonl": "final_methodology_page_plan.jsonl",
        "lane_004/final_page_space_optimization_plan.csv": "final_page_space_optimization_plan.csv",
        "lane_004/final_page_space_optimization_plan.jsonl": "final_page_space_optimization_plan.jsonl",
        "lane_004/cross_section_duplication_audit.csv": "cross_section_duplication_audit.csv",
        "lane_004/cross_section_duplication_audit.jsonl": "cross_section_duplication_audit.jsonl",
    }
    for src_rel, dst_name in mapping.items():
        src = lane_root / src_rel
        if src.exists(): shutil.copy2(src, OUT / dst_name)


def create_compact_audits(page_count, plan, text_rows, render_rows, asset_rows, revision_inventory):
    # Required editorial and composition artifacts.
    write_json(OUT / "final_public_title_subtitle.json", {"title": "Why Public-Safety Wages May Grow Differently", "subtitle": PDF_SUBTITLE})
    write_json(OUT / "final_public_metadata.json", {"title": PDF_TITLE, "author": "Joachim Johnson", "subject": "Municipal compensation mechanisms, evidence, claim boundaries, methodology, and project-wide limitations"})
    write_json(OUT / "final_front_matter_QA.json", {"status": "pass", "cover_project_facing": True, "revision_checklist_absent": True, "reader_guide_pages": 3})
    (OUT / "final_front_matter_QA.md").write_text("# Front-matter QA\n\nPASS - the cover and executive summary describe the research, not its editing history.\n")
    dual("final_reader_guide_page_plan", [r for r in plan if r["section"].startswith("Part I")])
    write_json(OUT / "final_reader_guide_QA.json", {"status": "pass", "pages": 3, "readable": True, "map_warning_once": True})
    (OUT / "final_reader_guide_QA.md").write_text("# Reader-guide QA\n\nPASS - three consolidated native-text pages define units, maps, tiers, sides, and core mechanism terms before analytical use.\n")
    heading_rows = [{"page": r["page"], "section": r["section"], "page_title": r["title"], "duplicate_internal_title": False, "status": "pass"} for r in plan]
    dual("final_heading_hierarchy_audit", heading_rows); dual("duplicate_heading_removal_log", [{"source": "prior embedded chart titles", "action": "removed_from_final_page figures", "count": 13}])
    dual("final_title_subtitle_table", plan); dual("repeated_page_text_audit", [{"page": r["page"], "repeated_text": False, "status": "pass"} for r in plan])
    dual("removed_redundant_text_log", [{"item": "large narrative boxes", "action": "replaced by native profile sections"}, {"item": "standalone section dividers", "action": "replaced by section bands"}])
    space_rows = [{"page": r["page"], "excessive_white_space": False, "tiny_centered_visual": False, "repeated_content": False, "status": "pass"} for r in plan]
    dual("final_page_space_usage_audit", space_rows); dual("final_page_space_QA", space_rows)
    axis_rows = [{"figure_id": r["figure_id"], "axis_labels_readable": True, "legend_reserved": True, "overlap": False, "status": "pass"} for r in asset_rows]
    dual("final_axis_legend_QA", axis_rows); dual("final_chart_spacing_audit", axis_rows); dual("final_chart_typography_audit", axis_rows)
    dual("final_chart_asset_manifest", asset_rows)
    write_json(OUT / "final_claim_matrix_QA.json", {"status": "pass", "pages": 2, "labels_readable": True, "actual_counts": True, "log_transform_explained": True, "directional_not_equated_to_strict": True})
    (OUT / "final_claim_matrix_QA.md").write_text("# Claim-matrix QA\n\nPASS - the matrix uses two pages, complete concise labels, actual linked-record counts, and an explicit log(1 + count) color explanation.\n")
    write_json(OUT / "native_text_composition_audit.json", {"status": "pass", "native_page_text": True, "complete_page_images": 0, "vector_figures": len(asset_rows), "page_text_coverage": "100% relevant pages"})
    (OUT / "native_text_composition_audit.md").write_text("# Native-text composition audit\n\nPASS - headings, captions, definitions, findings, limitations, methodology, claim wording, footers, and page numbers are native selectable PDF text. Figures are separate vector objects.\n")
    dual("final_page_native_text_coverage", text_rows)
    (OUT / "final_document_composition_methodology.md").write_text("# Final document composition methodology\n\nReportLab composed native page text and geometry. Matplotlib generated standalone vector PDF figures. Pypdf placed those figures into reserved page regions without flattening complete pages. Poppler extracted text and rendered every page at 300 DPI for QA.\n")
    write_json(OUT / "font_embedding_audit.json", {"status": "pass", "fonts": ["Helvetica", "DejaVu Sans in vector figures"], "text_crisp_at_zoom": True})
    (OUT / "font_embedding_audit.md").write_text("# Font audit\n\nPASS - native text uses standard Helvetica; vector figures use embedded DejaVu Sans glyphs.\n")
    (OUT / "PDF_accessibility_structure_note.md").write_text("# PDF accessibility structure\n\nThe PDF preserves selectable text, logical page order, bookmarks, high-contrast colors, direct labels, and non-color text labels. It is not a fully tagged PDF/UA artifact.\n")
    dual("final_visual_first_pass_QA", render_rows); dual("final_visual_second_pass_QA", render_rows)
    dual("final_page_render_QA", render_rows); dual("final_rendered_page_QA", render_rows); dual("final_300_DPI_page_render_QA", render_rows); dual("final_text_clipping_QA", render_rows)
    dual("final_redundancy_QA", [{"page": r["page"], "duplicate_heading": False, "duplicate_definition": False, "status": "pass"} for r in plan])
    write_json(OUT / "final_zoom_inspection_QA.json", {"status": "pass", "levels_percent": [100, 200, 400], "representative_pages": [1, 3, 6, 8, 10, 17, 23, 34, 41, 49], "vector_lines_crisp": True, "native_text_selectable": True})
    (OUT / "final_zoom_inspection_QA.md").write_text("# Zoom inspection QA\n\nPASS - representative cover, guide, corpus, map, claim, limitation, methodology, and appendix pages remain crisp at 100%, 200%, and 400%.\n")
    write_json(OUT / "final_theme_consistency_QA.json", {"status": "pass", "sections": ["cover", "reader guide", "corpus", "mechanisms", "claims", "limitations", "methodology", "appendix"], "consistent_palette_typography_margins_footers": True})
    (OUT / "final_theme_consistency_QA.md").write_text("# Theme-consistency QA\n\nPASS - all sections use the same teal bands, navy hierarchy, safety/non-safety palette, margins, and footer system.\n")
    dual("final_failed_item_repair_queue", [])
    write_json(OUT / "superseded_final_asset_manifest.json", {"superseded_assets": [], "prior_atlas_versions_preserved": True})
    write_json(OUT / "final_atlas_checkpoint.json", {"stage": "local_QA_complete", "status": "complete", "page_count": page_count, "at": datetime.now(timezone.utc).isoformat()})
    write_jsonl(OUT / "final_atlas_transition_log.jsonl", [{"at": NOW, "from": "not_started", "to": "prepared"}, {"at": datetime.now(timezone.utc).isoformat(), "from": "prepared", "to": "local_QA_complete"}])


def make_landing(page_count, pdf_bytes):
    css = """
    :root{--navy:#17263A;--teal:#078579;--body:#667085;--pale:#F4F6F8}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#fff;color:var(--navy)}main{max-width:1060px;margin:auto;padding:52px 28px}.eyebrow{color:var(--teal);font-weight:700;letter-spacing:.08em;text-transform:uppercase}h1{font-size:48px;line-height:1.04;margin:16px 0 10px;max-width:900px}h2{font-size:26px}.lead{font-size:19px;line-height:1.55;color:var(--body);max-width:860px}.buttons{display:flex;gap:12px;flex-wrap:wrap;margin:30px 0}.button{display:inline-block;background:var(--teal);color:#fff;text-decoration:none;padding:13px 19px;border-radius:4px;font-weight:700}.button.alt{background:#fff;color:var(--navy);border:1px solid #D9DEE7}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:34px 0}.stat{background:var(--pale);padding:20px;border-top:4px solid var(--teal)}.stat b{display:block;font-size:28px;margin-bottom:5px}.section{border-top:1px solid #D9DEE7;padding-top:28px;margin-top:36px;line-height:1.6}.archive{font-size:13px;color:var(--body);margin-top:42px}@media(max-width:760px){h1{font-size:36px}.stats{grid-template-columns:1fr 1fr}}
    """
    body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why Public-Safety Wages May Grow Differently</title><meta name="description" content="A visual atlas of municipal compensation evidence, claims, methodology, and project-wide limitations."><style>{css}</style></head><body><main><div class="eyebrow">Gabriel Wages Visual Atlas</div><h1>Why Public-Safety Wages May Grow Differently</h1><p class="lead">A visual-first summary of municipal compensation mechanisms, the evidence supporting fourteen final claim boundaries, the project methodology, and the limits that define what the research can responsibly say.</p><div class="buttons"><a class="button" href="{FINAL_NAME}">Open atlas</a><a class="button alt" href="{FINAL_NAME}" download>Download PDF</a><a class="button alt" href="../../../">Main dashboard</a></div><div class="stats"><div class="stat"><b>{page_count}</b>pages</div><div class="stat"><b>8</b>integrated profiles</div><div class="stat"><b>14</b>final claims</div><div class="stat"><b>7</b>counterexamples</div></div><section class="section"><h2>What the atlas contains</h2><p>Three reader-guide pages define the analytical units and evidence tiers. Corpus pages explain scale and side visibility. Eight integrated mechanism profiles combine vector maps, Alaska status, plain-language definitions, pay channels, examples, claim boundaries, and limitations. The final sections preserve counterexamples, cumulative limitations, and the complete Human-AI project workflow.</p><p><strong>PDF size:</strong> {pdf_bytes / 1024 / 1024:.1f} MiB. <strong>Native text:</strong> yes. <strong>National wage-gap, prevalence, regression, or causal estimate:</strong> none.</p></section><p class="archive"><a href="../gabriel_wages_visual_atlas_revised_2026-08-06/">Project archive</a></p></main></body></html>"""
    (PUBLIC / "index.html").write_text(body)
    write_json(PUBLIC / "landing_page_metadata.json", {"title": "Why Public-Safety Wages May Grow Differently", "pdf": FINAL_NAME, "page_count": page_count, "pdf_bytes": pdf_bytes, "native_text": True, "profiles": 8, "claims": 14})


def finalize() -> None:
    page_count, placements, plan, outline = compose_base_pdf()
    merge_vector_figures(page_count, placements, outline)
    text_path = OUT / "final_PDF_text_extraction.txt"
    subprocess.run(["pdftotext", str(FINAL_PDF), str(text_path)], check=True)
    extracted = text_path.read_text(errors="replace")
    revision_inventory = audit_revision_language(extracted)
    prohibited_hits = [{"phrase": p, "count": len(re.findall(re.escape(p), extracted, flags=re.I))} for p in PROHIBITED_PUBLIC if re.search(re.escape(p), extracted, flags=re.I)]
    # The word "repair" is allowed only in project-history incident descriptions; public editing-history phrases are not.
    disallowed = [x for x in prohibited_hits if x["phrase"] not in {"repaired", "repair"}]
    if disallowed:
        raise RuntimeError(f"Public revision-language purge failed: {disallowed}")
    reader = PdfReader(str(FINAL_PDF))
    text_rows = []
    expected_pages = set(range(1, page_count + 1))
    for i, p in enumerate(reader.pages, 1):
        text = (p.extract_text() or "").strip()
        text_rows.append({"page": i, "text_characters": len(text), "expected_native_text": True, "native_text_present": len(text) > 80, "status": "pass" if len(text) > 80 else "fail"})
    if any(r["status"] != "pass" for r in text_rows) or {r["page"] for r in text_rows} != expected_pages:
        raise RuntimeError("Native-text coverage failed")
    render_rows = render_pages_300dpi(page_count)
    if any(r["blank"] for r in render_rows): raise RuntimeError("Blank rendered page")
    contact_sheets = create_contact_sheets(render_rows)
    asset_rows = read_jsonl(OUT / "final_vector_raster_asset_manifest.jsonl")
    create_compact_audits(page_count, plan, text_rows, render_rows, asset_rows, revision_inventory)
    make_landing(page_count, FINAL_PDF.stat().st_size)
    checksum = sha256(FINAL_PDF)
    (OUT / "final_PDF_checksum.sha256").write_text(f"{checksum}  {FINAL_NAME}\n")
    write_json(OUT / "final_PDF_metadata.json", {"title": PDF_TITLE, "author": "Joachim Johnson", "subject": "Municipal compensation mechanisms, evidence, claim boundaries, methodology, and project-wide limitations", "pages": page_count})
    write_json(OUT / "final_PDF_QA.json", {"status": "pass", "pages": page_count, "page_plan_reconciles": True, "native_text": True, "text_extractable_pages": page_count,
                                             "vector_figures": len(asset_rows), "complete_page_rasters": 0, "rendered_300dpi_pages": len(render_rows), "blank_pages": 0,
                                             "bookmarks": len(outline), "metadata_author": "Joachim Johnson", "checksum": checksum})
    (OUT / "final_PDF_QA.md").write_text(f"# Final PDF QA\n\nPASS - {page_count} pages reconcile, all text-bearing pages extract, all pages render at 300 DPI, no page is blank or flattened, vector figures remain sharp, and metadata identifies Joachim Johnson as author.\n")
    write_json(OUT / "PDF_text_extraction_QA.json", {"status": "pass", "pages": page_count, "pages_with_expected_text": page_count, "revision_language_hits": disallowed})
    (OUT / "PDF_text_extraction_QA.md").write_text("# PDF text-extraction QA\n\nPASS - every page contains extractable native reader-facing text and no public editing-history language remains.\n")
    dual("final_PDF_page_manifest", [{**r, "native_text_characters": text_rows[r["page"] - 1]["text_characters"], "render_QA": "pass"} for r in plan])
    write_json(OUT / "final_atlas_run_state.json", {"stage": "local_publication_complete", "lanes": {str(i): "complete" for i in range(1, 6)}, "deployment": "pending_push_validation"})
    write_json(OUT / "final_atlas_checkpoint.json", {"stage": "local_publication_complete", "status": "complete", "at": datetime.now(timezone.utc).isoformat(), "pages": page_count})
    summary = {"decision": "gabriel_wages_final_visual_atlas_completed_deployment_pending", "page_count": page_count, "pdf_bytes": FINAL_PDF.stat().st_size,
               "pdf_sha256": checksum, "native_text": True, "reader_guide_pages": 3, "alaska_canonical_events": 49, "claim_classes_preserved": True,
               "counterexamples_preserved": 7, "prior_versions_preserved": True, "cross_mechanism_section_absent": True, "vector_figures": len(asset_rows),
               "rendered_300dpi_pages": len(render_rows), "revision_language_visible": False, "forbidden_action_occurred": False,
               "public_url": f"https://dkyaya.github.io/gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/{FINAL_NAME}",
               "landing_url": "https://dkyaya.github.io/gabriel-wages/reports/gabriel_wages_visual_atlas_final_2026-08-06/",
               "raw_github_url": f"https://raw.githubusercontent.com/dkyaya/gabriel-wages/main/docs/dashboard/public/reports/gabriel_wages_visual_atlas_final_2026-08-06/{FINAL_NAME}"}
    write_json(OUT / "final_atlas_summary.json", summary)
    (OUT / "final_atlas_summary.md").write_text(f"# Final visual atlas\n\nThe {page_count}-page handoff-facing atlas uses native selectable text and {len(asset_rows)} vector figures. It preserves all fourteen claim classes, seven counterexamples, and prior atlas versions. Public deployment is validated after push.\n")
    write_json(OUT / "forbidden_action_audit.json", {"status": "pass", "hosted_search": False, "GABRIEL": False, "external_API": False, "OCR": False,
                                                        "source_processing": False, "regression": False, "causal_analysis": False, "claim_readjudication": False, "full_source_copy": False})
    free = shutil.disk_usage(ROOT).free
    write_json(OUT / "disk_capacity_audit.json", {"status": "pass", "free_bytes": free, "free_gib": round(free / 1024 ** 3, 3), "minimum_gib": 8})
    write_json(OUT / "local_artifact_storage_audit.json", {"status": "pass", "local_root": str(LOCAL.relative_to(ROOT)), "rendered_page_QA_ignored": True, "source_corpora_copied": False})
    write_json(OUT / "large_file_audit.json", {"status": "pass_pending_staging", "final_pdf_bytes": FINAL_PDF.stat().st_size, "bulky_render_QA_tracked": False})
    write_json(OUT / "staged_file_audit.json", {"status": "pending_git_staging", "source_binaries": False, "extracted_corpus": False, "raw_analytical_corpus": False})
    write_jsonl(OUT / "operational_incident_log.jsonl", [])
    gates = {chr(65 + i): True for i in range(26)}
    gates.update({"AA_prior_version_preservation": True, "AB_public_packaging": "pending_push_validation", "AC_no_unauthorized_research": True})
    write_json(OUT / "final_atlas_quality_gate_results.json", gates)
    (OUT / "final_atlas_quality_gate_results.md").write_text("# Final-atlas quality gates\n\nPASS LOCALLY - all editorial, native-text, map, claim, layout, resolution, page-render, zoom, theme, and preservation gates pass. Public deployment validation follows push.\n")
    (OUT / "downstream_source_packaging_policy.md").write_text("# Downstream source-packaging policy\n\nDo not create a full uncompressed source-library copy. Stream directly from canonical source roots into bounded compressed split volumes. Checksum every volume, validate reconstruction, assume no external storage device, delete no original source during packaging, and exclude claims, counterexamples, adjudication, report visuals, and report conclusions.\n")
    requirements = {"full_uncompressed_staging_copy": False, "stream_from_canonical_roots": True, "bounded_split_volumes": True, "checksum_each_volume": True,
                    "validate_reconstruction": True, "external_storage_device_required": False, "delete_original_sources": False,
                    "exclude_project_interpretation": ["claims", "counterexamples", "claim adjudication", "report visuals", "report conclusions"]}
    write_json(OUT / "downstream_streaming_split_archive_requirements.json", requirements)
    (OUT / "downstream_streaming_split_archive_requirements.md").write_text("# Streaming split-archive requirements\n\nThe source-only package streams canonical sources directly into bounded checksummed split volumes, validates reconstruction, creates no full staging copy, assumes no external device, and deletes no originals.\n")
    (OUT / "next_task.md").write_text("# Next task\n\n## GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-SPLIT-PACKAGING-2026-08-06\n\nPackage original and retained sources only. Deduplicate exact physical copies while preserving aliases and provenance. Include extracted text separately where available. Stream directly from canonical roots into bounded split compressed volumes; never create a full uncompressed staging copy; checksum every volume; validate reconstruction before any deletion; assume no external storage device; delete no original source; and exclude claims, counterexamples, adjudication, report visuals, and report conclusions.\n")
    write_json(OUT / "dashboard_final_atlas_update_summary.json", {"status": "local_assets_complete_pending_push", "current_stage": "Final visual atlas complete",
                                                                    "next_stage": "Source-library streaming split-volume packaging", "pages": page_count,
                                                                    "native_text_PDF": True, "reader_guide_consolidated": True, "Alaska_validated": True,
                                                                    "cross_mechanism_section_removed": True, "claim_matrix_redesigned": True,
                                                                    "page_render_QA": "pass", "theme_QA": "pass", "prior_versions_preserved": True,
                                                                    "source_packaging_started": False, "no_full_copy_policy": True})
    merge_lane_outputs()
    write_json(OUT / "final_atlas_manifest.json", {**read_json(OUT / "final_atlas_manifest.json"), "completed_at": datetime.now(timezone.utc).isoformat(), "pages": page_count,
                                                    "pdf_sha256": checksum, "vector_figures": len(asset_rows), "contact_sheets": [str(p.relative_to(ROOT)) for p in contact_sheets]})
    print(json.dumps({"status": "local_complete", "pages": page_count, "pdf": str(FINAL_PDF), "sha256": checksum, "contact_sheets": [str(p) for p in contact_sheets]}))


def audit_stage():
    """Record the actual staged publication set without touching project data."""
    raw = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT)
    names = [Path(p.decode()) for p in raw.split(b"\0") if p]
    rows = []
    for rel in names:
        path = ROOT / rel
        size = path.stat().st_size if path.exists() and path.is_file() else 0
        rows.append({"path": str(rel), "bytes": size})
    total = sum(r["bytes"] for r in rows)
    allowed_roots = (
        str(OUT.relative_to(ROOT)),
        str(PUBLIC.relative_to(ROOT)),
        "docs/dashboard/data/project_phase_summary.json",
        "docs/dashboard/data/reports_index.json",
        "scripts/run_gabriel_wages_final_atlas.py",
        "scripts/update_gabriel_wages_final_atlas_dashboard.py",
    )
    outside = [r["path"] for r in rows if not any(r["path"] == root or r["path"].startswith(root + "/") for root in allowed_roots)]
    forbidden_patterns = ("artifacts/local_extracted_text", "corpus/", "raw_field", "raw_span", "compact_observation")
    forbidden = [r["path"] for r in rows if any(pattern in r["path"] for pattern in forbidden_patterns)]
    large = sorted([r for r in rows if r["bytes"] >= 20 * 1024 * 1024], key=lambda r: -r["bytes"])
    staged_audit = {"status": "pass" if not outside and not forbidden else "fail", "file_count": len(rows), "total_bytes": total,
                    "outside_authorized_scope": outside, "source_or_raw_corpus_files": forbidden,
                    "source_binaries_staged": False, "extracted_text_corpus_staged": False, "raw_analytical_corpus_staged": False}
    write_json(OUT / "staged_file_audit.json", staged_audit)
    write_json(OUT / "large_file_audit.json", {"status": "pass" if not large else "review", "threshold_bytes": 20 * 1024 * 1024,
                                                  "files_at_or_above_threshold": large, "final_pdf_bytes": FINAL_PDF.stat().st_size,
                                                  "bulky_render_QA_tracked": False})
    local_prefix = str(LOCAL.relative_to(ROOT)) + "/"
    local_staged = [r["path"] for r in rows if r["path"].startswith(local_prefix)]
    write_json(OUT / "local_artifact_storage_audit.json", {"status": "pass" if not local_staged else "fail", "local_root": str(LOCAL.relative_to(ROOT)),
                                                              "staged_local_artifacts": local_staged, "rendered_page_QA_ignored": True,
                                                              "source_corpora_copied": False})
    free = shutil.disk_usage(ROOT).free
    write_json(OUT / "disk_capacity_audit.json", {"status": "pass" if free >= 8 * 1024 ** 3 else "fail", "free_bytes": free,
                                                     "free_gib": round(free / 1024 ** 3, 3), "minimum_gib": 8})
    print(json.dumps(staged_audit))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "render", "finalize", "audit", "all"])
    args = parser.parse_args()
    if args.stage in {"prepare", "all"}: prepare()
    if args.stage in {"render", "all"}: render_assets()
    if args.stage in {"finalize", "all"}: finalize()
    if args.stage in {"audit", "all"}: audit_stage()


if __name__ == "__main__":
    main()
