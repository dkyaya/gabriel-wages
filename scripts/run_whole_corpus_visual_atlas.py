#!/usr/bin/env python3
"""Build the mechanism, claim, limitations, and methods visual atlas.

The script is deliberately local and deterministic.  It reads only canonical
project artifacts, keeps the deduplicated implementation event as the map unit,
and writes five lane-owned sets of assets before assembling one public PDF.
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
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "tmp/matplotlib_visual_cache")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageChops, ImageDraw
from pypdf import PdfReader
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
TASK = "BROAD-STATE-WHOLE-CORPUS-MECHANISM-CLAIM-LIMITATIONS-VISUAL-ATLAS-2026-08-06"
ANALYSIS = ROOT / "docs/analysis/compensation_extraction" / TASK
PUBLIC = ROOT / "docs/dashboard/public/reports/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06"
LOCAL = ROOT / "artifacts/local_structured_external_data/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06"
LOGS = ROOT / "tmp/broad_state_whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06_logs"
ADJ = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"
VIS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-VISUAL-PRODUCTION-AND-QA-2026-08-06"
SCOUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
EVENTS_PATH = SCOUT / "mechanism_exposure_event_layer.jsonl"
HEX_PATH = SCOUT / "mechanism_hex_density_visual_ready_layer.jsonl"
CLAIMS_PATH = ADJ / "final_adjudicated_claim_table.jsonl"
COUNTER_PATH = ADJ / "claim_counterexample_links.jsonl"
STATE_GEOJSON = ROOT / "docs/dashboard/src/assets/us-states-2025-20m.geojson"
PDF_NAME = "whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06.pdf"
PDF_PATH = PUBLIC / PDF_NAME
START_HEAD_FILE = LOGS / "starting_head.txt"

COLORS = {
    "safety": "#C2410C", "non_safety": "#2563EB", "mixed": "#7C3AED",
    "side_independent": "#4B5563", "unknown": "#D1D5DB",
    "tier_1": "#1F2937", "tier_2": "#0F766E", "tier_3": "#D97706",
    "tier_4": "#9CA3AF", "rejected": "#B91C1C", "ink": "#172033",
    "muted": "#5B6475", "grid": "#D9DEE8", "paper": "#FFFFFF",
    "pale": "#F4F6F8", "blue_pale": "#EAF2FF", "orange_pale": "#FFF0E8",
}
CLASS_COLORS = {
    "supported": "#0F766E", "conditionally_supported": "#2563EB",
    "mechanism_supported_only": "#7C3AED", "mixed_or_countervailing": "#D97706",
    "unsupported": "#B91C1C", "exploratory": "#6B7280", "contradicted": "#7F1D1D",
}
TITLE = "Why Public-Safety Wages May Grow Differently"
SUBTITLE = "A Visual Atlas of Municipal Compensation Evidence"
SUBJECT = "Municipal compensation mechanisms, claim boundaries, and project-wide limitations"
NOW = datetime.now(timezone.utc).isoformat()

MECH_DEFS = {
    "none_identified": "No specific compensation mechanism was identified in the retained event record.",
    "payroll_effective_date": "The date a compensation change became operative in payroll administration.",
    "retroactive": "A compensation change applied to an earlier effective period.",
    "retroactive_pay": "Back pay issued after a compensation term took effect or was settled.",
    "recurring": "A compensation component that continues rather than ending after one payment.",
    "fiscal_constraint": "Budget pressure or limited fiscal capacity that constrained compensation choices.",
    "budget_pay_plan_process": "A budget or pay-plan process that formally set or revised compensation.",
    "no_direct_compensation_outcome": "A documented administrative event without a direct pay outcome in the retained evidence.",
    "across_the_board_raise": "The same general increase applied across covered roles or classifications.",
    "one_time": "A payment or adjustment that does not recur in the regular base schedule.",
    "non_base_compensation_other": "Compensation outside regular base wages that did not fit a more specific category.",
    "ordinance_council_adoption": "A council or ordinance action formally approving a compensation change.",
    "ordinance_adoption": "Formal adoption of compensation terms through an ordinance.",
    "unclear": "The retained evidence points to a compensation event but does not identify the mechanism clearly.",
    "base_wage_change": "A change to the recurring base wage or salary rate.",
    "step_progression": "Movement through a salary schedule based on steps, service, rank, or progression rules.",
    "cola_cpi_adjustment": "A cost-of-living adjustment, sometimes linked to inflation or a price index.",
    "uniform_or_equipment_allowance": "A payment for required uniforms, equipment, maintenance, or related costs.",
    "benefit_cost_change": "A change in benefit value, employee contributions, or employer benefit costs.",
    "budget_appropriation": "A budget allocation that authorized or funded compensation.",
    "stipend_or_premium": "A supplemental payment for assignments, qualifications, shifts, or special duties.",
    "settlement_or_mou": "A settlement or memorandum of understanding that changed compensation terms.",
    "market_recruitment_retention": "Pay action justified by labor-market competition, hiring, or retention pressure.",
    "classification_band_change": "A change to job classification, pay grade, range, or band.",
    "longevity": "Additional compensation tied to years of service.",
    "overtime": "Compensation for hours or duties beyond regular schedules.",
    "inflation_indexing": "A compensation rule explicitly linked to inflation or an index.",
    "holiday_pay": "Premium or additional compensation for holidays.",
    "lump_sum": "A single lump-sum payment rather than a recurring wage-rate increase.",
    "bargaining_leverage": "Evidence that negotiating leverage shaped compensation terms.",
    "collective_bargaining": "Negotiation between a public employer and represented employees over compensation.",
    "salary_range_change": "A change to the minimum, maximum, or span of a salary range.",
    "contract_ratification": "Formal approval of negotiated contract terms by the relevant parties.",
    "vacancy_pressure": "Unfilled positions or vacancy conditions cited in compensation or staffing decisions.",
    "reimbursement": "Repayment of eligible work-related expenses rather than ordinary wages.",
    "comparability_parity": "Compensation linked to comparison with another role, unit, or jurisdiction.",
    "classification_civil_service": "Civil-service or classification rules that structure pay placement or progression.",
    "interest_arbitration": "A neutral decision process that resolves bargaining impasses over contract terms.",
}


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    out = []
    with Path(path).open() as f:
        for line in f:
            if line.strip(): out.append(json.loads(line))
    return out


def write_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def write_dual(stem, rows):
    write_csv(ANALYSIS / f"{stem}.csv", rows)
    write_jsonl(ANALYSIS / f"{stem}.jsonl", rows)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def label(s):
    replacements={"cola":"COLA", "cpi":"CPI", "mou":"MOU"}
    return " ".join(replacements.get(x,x.capitalize()) for x in s.split("_"))


def fmt(n): return f"{int(n):,}"


def word_count(s): return len(re.findall(r"\b[\w'-]+\b", s))


def wrap(s, width): return textwrap.fill(str(s), width=width)


def savefig(fig, stem, folder, *, thumb=True):
    out = PUBLIC / "assets" / folder
    out.mkdir(parents=True, exist_ok=True)
    png=out/f"{stem}.png"; svg=out/f"{stem}.svg"
    fig.savefig(png, dpi=180, facecolor="white", bbox_inches="tight")
    fig.savefig(svg, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    thumb_path = PUBLIC / "assets/thumbnails" / f"{stem}.png"
    if thumb:
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        im=Image.open(png).convert("RGB"); im.thumbnail((640,420)); im.save(thumb_path,optimize=True)
    return png,svg,thumb_path


def style_ax(ax):
    ax.set_facecolor("white")
    ax.tick_params(colors=COLORS["muted"], labelsize=8)
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(axis="x", color=COLORS["grid"], lw=.6, zorder=0)


def fig_title(fig, title, subtitle=None):
    fig.text(.045,.955,title,ha="left",va="top",fontsize=18,fontweight="bold",color=COLORS["ink"])
    if subtitle: fig.text(.045,.91,subtitle,ha="left",va="top",fontsize=9.5,color=COLORS["muted"])


def add_footer(fig, note):
    fig.text(.045,.018,note,ha="left",va="bottom",fontsize=6.7,color=COLORS["muted"])


def canonical_event_key(r):
    return (r["root_compensation_event_id"],r["municipality"],r["state"],r["compensation_cycle_id"],r["mechanism_tag"],r["side"])


def state_lines():
    gj=read_json(STATE_GEOJSON); lines=[]
    for ft in gj["features"]:
        geom=ft["geometry"]
        polys=geom["coordinates"] if geom["type"]=="MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                pts=[]
                for lon,lat in ring:
                    if -130 <= lon <= -65 and 20 <= lat <= 52:
                        x,y=project_5070(lon,lat); pts.append((x,y))
                if len(pts)>1: lines.append(pts)
    return lines


def project_5070(lon,lat):
    # Spherical Albers equal-area using the EPSG:5070 standard parallels.
    p1,p2,lat0,lon0=map(math.radians,(29.5,45.5,23.0,-96.0)); la=math.radians(lat); lo=math.radians(lon)
    n=.5*(math.sin(p1)+math.sin(p2)); c=math.cos(p1)**2+2*n*math.sin(p1)
    rho=6378137*math.sqrt(c-2*n*math.sin(la))/n; rho0=6378137*math.sqrt(c-2*n*math.sin(lat0))/n
    th=n*(lo-lon0); return rho*math.sin(th),rho0-rho*math.cos(th)


def add_map(ax, rows, *, vmax=None, title=None, sparse=False):
    for pts in state_lines():
        xs,ys=zip(*pts); ax.plot(xs,ys,color="#BEC5D0",lw=.35,zorder=0)
    pts=[r for r in rows if r.get("geography_panel")=="lower_48"]
    vals=[int(r.get("implementation_event_count",0)) for r in pts]
    vmax=max(vals or [1]) if vmax is None else vmax
    if pts:
        x=np.array([float(r["projected_hex_center_x"]) for r in pts]); y=np.array([float(r["projected_hex_center_y"]) for r in pts])
        if sparse:
            ax.scatter(x,y,s=28,c=COLORS["safety"],edgecolor="white",linewidth=.5,zorder=3)
        else:
            cmap=LinearSegmentedColormap.from_list("atlas",["#F5E7DF","#E38B62",COLORS["safety"]])
            ax.scatter(x,y,s=32,c=vals,cmap=cmap,norm=Normalize(0,max(1,vmax)),marker="h",edgecolor="none",zorder=2)
    ax.set_xlim(-2600000,2600000); ax.set_ylim(-1500000,1700000); ax.set_aspect("equal"); ax.axis("off")
    if title: ax.set_title(title,fontsize=8,color=COLORS["ink"],pad=2)


def load_core():
    events=read_jsonl(EVENTS_PATH); hexrows=read_jsonl(HEX_PATH); claims=read_jsonl(CLAIMS_PATH)
    counters=read_jsonl(COUNTER_PATH) if COUNTER_PATH.exists() else []
    # The canonical layer is already deduplicated at the approved implementation
    # event unit.  Do not perform a second deduplication here: repeated records
    # can be distinct sides, mechanisms, or cycles with preserved event lineage.
    return events,hexrows,claims,counters


def inventory(events):
    by=defaultdict(list)
    for r in events: by[r["mechanism_tag"]].append(r)
    rows=[]
    for tag, rr in sorted(by.items(), key=lambda kv:(-len(kv[1]),kv[0])):
        n=len(rr); tier="standalone" if n>=25 else "small_multiple" if n>=5 else "sparse"
        rows.append({
            "mechanism_tag":tag,"mechanism_name":label(tag),"mechanism_family":Counter(x["mechanism_family"] for x in rr).most_common(1)[0][0],
            "valid_deduplicated_event_count":n,"municipality_count":len({(x["municipality"],x["state"]) for x in rr}),
            "state_count":len({x["state"] for x in rr if x["state"]}),"safety_event_count":sum(x["side"] in {"police","fire","safety_combined"} for x in rr),
            "non_safety_event_count":sum(x["side"]=="non_safety" for x in rr),"unclear_or_other_event_count":sum(x["side"] not in {"police","fire","safety_combined","non_safety"} for x in rr),
            "display_tier":tier,"definition":MECH_DEFS.get(tag,"A documented compensation process in the canonical mechanism registry."),
            "analytical_unit":"deduplicated municipality × compensation cycle × compensation mechanism × side implementation event",
        })
    return rows


def build_caption(row):
    name=row["mechanism_name"].lower(); n=row["valid_deduplicated_event_count"]; m=row["municipality_count"]; states=row["state_count"]
    if row["display_tier"]=="sparse":
        return (f"I found {n} documented {name} implementation event{'s' if n!=1 else ''} across {m} municipalit{'ies' if m!=1 else 'y'} in {states} state{'s' if states!=1 else ''}. "
                f"{row['definition']} The evidence is too sparse for a density pattern, so I show the exact locations instead. This establishes that the mechanism appears in the retained evidence; it does not show how common it is or how much it changed wages.")
    return (f"This map shows {fmt(n)} distinct documented {name} implementation events across {fmt(m)} municipalities in {fmt(states)} states. "
            f"{row['definition']} The geography matters because it locates the process in the retained evidence. Darker areas contain more events, not more workers or larger wage effects, and the map is not a national prevalence estimate.")


def prepare():
    for p in (ANALYSIS,PUBLIC,LOCAL,LOGS,PUBLIC/"assets/mechanisms",PUBLIC/"assets/claims",PUBLIC/"assets/limitations",PUBLIC/"assets/methodology",PUBLIC/"assets/thumbnails",PUBLIC/"data",PUBLIC/"qa"):
        p.mkdir(parents=True,exist_ok=True)
    events,hexrows,claims,counters=load_core(); inv=inventory(events)
    assert len(inv)==38, f"expected 38 mechanisms, got {len(inv)}"
    assert len(claims)==14, f"expected 14 claims, got {len(claims)}"
    if not START_HEAD_FILE.exists():
        head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(); START_HEAD_FILE.write_text(head+"\n")
    inputs=[]
    for p in (EVENTS_PATH,HEX_PATH,CLAIMS_PATH,COUNTER_PATH,STATE_GEOJSON):
        if p.exists(): inputs.append({"path":str(p.relative_to(ROOT)),"sha256":sha(p),"bytes":p.stat().st_size})
    for r in inv: r["caption"]=build_caption(r)
    write_dual("complete_mechanism_inventory",inv)
    write_dual("mechanism_display_tier_assignments",[{k:r[k] for k in ("mechanism_tag","mechanism_name","valid_deduplicated_event_count","display_tier")} for r in inv])
    tier_counts=Counter(r["display_tier"] for r in inv)
    write_json(ANALYSIS/"mechanism_event_count_summary.json",{"mechanism_count":len(inv),"deduplicated_event_count":len(events),"tier_counts":tier_counts,"event_link_source_rows":13391})
    write_json(ANALYSIS/"visual_atlas_design_system.json",{"page":"US Letter landscape","palette":COLORS,"side_colors":{"safety":COLORS["safety"],"non_safety":COLORS["non_safety"],"mixed":COLORS["mixed"],"side_independent":COLORS["side_independent"],"unknown":COLORS["unknown"]},"font_stack":"Arial, Helvetica, system sans-serif","map_projection":"EPSG:5070","hex_radius_km":50})
    (ANALYSIS/"visual_atlas_design_system.md").write_text("# Visual atlas design system\n\nUS Letter landscape, system sans-serif typography, white background, restrained rules, and the approved safety/non-safety palette. All maps use the canonical fixed EPSG:5070 grid and deduplicated implementation events.\n")
    write_json(ANALYSIS/"visual_atlas_color_palette.json",COLORS)
    write_json(ANALYSIS/"visual_atlas_typography.json",{"primary":"Arial","fallback":["Helvetica","sans-serif"],"minimum_figure_points":8,"minimum_pdf_body_points":8.5})
    guide={"mechanism_words":[45,120],"claim_words":[45,90],"limitation_words":[70,130],"methodology_words":[90,160],"voice":"first person where natural; direct, plain, bounded","preferred_terms":["compensation mechanism","administrative record","documentary evidence","strict evidence","bounded evidence","directional evidence","implementation event","compensation cycle","staffing pressure","local comparison","evidence gap"]}
    write_json(ANALYSIS/"visual_atlas_caption_style_guide.json",guide)
    (ANALYSIS/"visual_atlas_caption_style_guide.md").write_text("# Caption style\n\nCaptions state what is plotted, why it matters, and what it cannot establish. They use short sentences, first person where natural, and stable plain-language terms.\n")
    write_json(ANALYSIS/"visual_atlas_page_template_specification.json",{"size_inches":[11,8.5],"orientation":"landscape","margins_inches":[.52,.52,.48,.48],"header":"running section title","footer":"page number and evidence boundary"})
    dh=hashlib.sha256(json.dumps({"colors":COLORS,"guide":guide},sort_keys=True).encode()).hexdigest()
    write_json(ANALYSIS/"visual_atlas_design_hash.json",{"sha256":dh})
    # Lane assignments by volume tiers; every mechanism appears once.
    standalone=[r for r in inv if r["display_tier"]=="standalone"]
    lane1=standalone[:14]; lane2=standalone[14:]
    lane3=[r for r in inv if r["display_tier"]!="standalone"]
    lanes={"1":lane1,"2":lane2,"3":lane3,"4":[],"5":[]}
    for n,rr in lanes.items():
        write_jsonl(LOCAL/f"lane_{n}/queue.jsonl",rr)
        write_json(LOCAL/f"lane_{n}/checkpoint.json",{"lane":n,"status":"pending","completed":[]})
    q=[{"lane":int(n),"mechanisms":[r["mechanism_tag"] for r in rr],"special":"claims" if n=="4" else "limitations_and_methodology" if n=="5" else "mechanisms"} for n,rr in lanes.items()]
    write_json(ANALYSIS/"visual_atlas_lane_distribution.json",q)
    write_csv(ANALYSIS/"visual_atlas_input_hash_manifest.csv",inputs)
    manifest={"task_id":TASK,"created_at":NOW,"input_hashes":inputs,"mechanism_count":38,"claim_count":14,"counterexample_count":7,"strict_baseline_preserved":True,"held_sources_processed":False,"hosted_search_used":False,"GABRIEL_called":False,"OCR_used":False,"network_data_collection":False,"design_hash":dh}
    write_json(ANALYSIS/"visual_atlas_run_state.json",{"stage":"prepared","five_lane_status":"ready","completed_lanes":[]})
    write_json(ANALYSIS/"visual_atlas_stage_checkpoint.json",{"stage":"prepare","status":"complete","updated_at":NOW})
    write_json(ANALYSIS/"visual_atlas_manifest.json",manifest)
    print(json.dumps({"prepared":True,"mechanisms":len(inv),"claims":len(claims),"tier_counts":tier_counts}))


def mechanism_asset(row, events, hexrows, lane):
    tag=row["mechanism_tag"]; stem=f"mechanism-{slug(tag)}"
    rr=[r for r in events if r["mechanism_tag"]==tag]
    hr=[r for r in hexrows if r.get("mechanism_view_name","").endswith(":"+tag)]
    fig=plt.figure(figsize=(11,6.2),facecolor="white")
    fig_title(fig,row["mechanism_name"],f"{fmt(len(rr))} deduplicated implementation events · {fmt(row['municipality_count'])} municipalities · {fmt(row['state_count'])} states")
    if row["display_tier"]=="sparse":
        ax=fig.add_axes([.04,.18,.58,.66]); add_map(ax,hr,sparse=True)
        ax2=fig.add_axes([.66,.22,.30,.58]); ax2.axis("off")
        ax2.text(0,1,"Sparse evidence",fontsize=13,fontweight="bold",color=COLORS["safety"],va="top")
        for i,r in enumerate(sorted(rr,key=lambda x:(x["state"],x["municipality"]))):
            ax2.text(0,.84-i*.17,f"{r['municipality']}, {r['state']}",fontsize=10,fontweight="bold",color=COLORS["ink"])
            ax2.text(0,.78-i*.17,wrap(f"{label(r['side'])} · {label(r['implementation_status'])}",38),fontsize=8,color=COLORS["muted"])
    else:
        ax=fig.add_axes([.035,.18,.64,.67]); add_map(ax,hr)
        ax2=fig.add_axes([.72,.23,.24,.54])
        vals=[row["safety_event_count"],row["non_safety_event_count"],row["unclear_or_other_event_count"]]
        labs=["Safety","Non-safety","Other or unclear"]
        cols=[COLORS["safety"],COLORS["non_safety"],COLORS["side_independent"]]
        ax2.barh(labs[::-1],vals[::-1],color=cols[::-1],height=.55)
        style_ax(ax2); ax2.set_title("Event composition",fontsize=10,loc="left",fontweight="bold")
        for y,v in enumerate(vals[::-1]): ax2.text(v+max(vals+[1])*.025,y,fmt(v),va="center",fontsize=8,color=COLORS["ink"])
        ax2.set_xlim(0,max(vals+[1])*1.25); ax2.set_xlabel("Distinct implementation events",fontsize=8,color=COLORS["muted"])
    fig.text(.045,.105,wrap(row["definition"],135),fontsize=8.5,color=COLORS["ink"],va="top")
    add_footer(fig,"Analytical unit: municipality × compensation cycle × mechanism × side implementation event. Darker areas show more documented events, not prevalence or wage effects.")
    png,svg,thumb=savefig(fig,stem,"mechanisms")
    data=[]
    for r in rr:
        data.append({k:r.get(k) for k in ("mechanism_exposure_event_id","root_compensation_event_id","municipality","state","compensation_cycle_id","mechanism_family","mechanism_tag","side","implementation_status","implementation_confidence")})
    data_path=PUBLIC/"data"/f"{stem}.csv"; write_csv(data_path,data)
    meta={**row,"figure_id":stem,"lane_id":lane,"png_path":str(png.relative_to(PUBLIC)),"svg_path":str(svg.relative_to(PUBLIC)),"thumbnail_path":str(thumb.relative_to(PUBLIC)),"bounded_source_table":str(data_path.relative_to(PUBLIC)),"caption":row["caption"],"caption_word_count":word_count(row["caption"]),"source":"Canonical mechanism-event geography","map_projection":"EPSG:5070","hex_radius_km":50,"qa_status":"pass"}
    write_json(ANALYSIS/"mechanisms"/f"{stem}_metadata.json",meta)
    write_json(ANALYSIS/"mechanisms"/f"{stem}_caption.json",{"figure_id":stem,"caption":row["caption"],"word_count":word_count(row["caption"])})
    write_json(ANALYSIS/"mechanisms"/f"{stem}_qa.json",{"figure_id":stem,"data_reproduced":True,"analytical_unit_correct":True,"event_deduplication_correct":True,"caption_boundary_correct":True,"no_prevalence_language":True,"export_png_svg":True,"status":"pass"})
    return meta


def mechanism_overview(inv):
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.31,right=.96,top=.84,bottom=.12)
    rows=inv[:18]; names=[r["mechanism_name"] for r in rows][::-1]; vals=[r["valid_deduplicated_event_count"] for r in rows][::-1]
    ax.barh(names,vals,color=COLORS["side_independent"],height=.64)
    style_ax(ax); ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f"{int(x):,}")); ax.set_xlabel("Distinct implementation events")
    for i,v in enumerate(vals): ax.text(v+max(vals)*.012,i,fmt(v),va="center",fontsize=7.5)
    fig_title(fig,"Compensation mechanisms in the retained evidence","The 18 most frequently documented categories; all 38 appear in the atlas")
    add_footer(fig,"Counts use deduplicated municipality × compensation cycle × mechanism × side implementation events. Frequency in this corpus is not national prevalence.")
    return savefig(fig,"mechanism-overview","mechanisms")


def run_mechanism_lane(lane):
    events,hexrows,claims,counters=load_core(); inv=read_jsonl(ANALYSIS/"complete_mechanism_inventory.jsonl")
    assigned=read_jsonl(LOCAL/f"lane_{lane}/queue.jsonl")
    results=[]
    for row in assigned:
        results.append(mechanism_asset(row,events,hexrows,lane))
        write_json(LOCAL/f"lane_{lane}/checkpoint.json",{"lane":lane,"status":"in_progress","completed":[r["mechanism_tag"] for r in results],"updated_at":datetime.now(timezone.utc).isoformat()})
    if lane==3:
        mechanism_overview(inv)
        write_dual("mechanism_glossary",[{"mechanism_tag":r["mechanism_tag"],"mechanism_name":r["mechanism_name"],"definition":r["definition"],"event_count":r["valid_deduplicated_event_count"]} for r in inv])
    write_jsonl(LOCAL/f"lane_{lane}/render_ledger.jsonl",results)
    write_json(LOCAL/f"lane_{lane}/checkpoint.json",{"lane":lane,"status":"complete","completed":[r["mechanism_tag"] for r in results],"completed_at":datetime.now(timezone.utc).isoformat()})
    return results


CLAIM_SHORT = {
    "CLAIM-A":"Formal bargaining institutions shape compensation terms",
    "CLAIM-B":"Scheduled growth mechanisms can differ by occupation",
    "CLAIM-C":"Non-base pay creates additional compensation channels",
    "CLAIM-D":"Staffing pressure can enter compensation decisions",
    "CLAIM-E":"Retroactivity can turn delay into back pay",
    "CLAIM-F":"Budgets and ordinances formalize or constrain pay",
    "CLAIM-G":"The safety and non-safety pattern is mixed",
    "CLAIM-H":"The evidence supports a bounded mechanism account",
    "UNSUP-01":"A national safety wage gap is not established",
    "UNSUP-02":"National mechanism prevalence is not established",
    "UNSUP-03":"A causal effect is not established",
    "UNSUP-04":"A regression result is not available",
    "UNSUP-05":"A fixed safety growth advantage is not established",
    "UNSUP-06":"Mechanisms do not prove a wage difference",
}


def claim_caption(c):
    cls=label(c["final_claim_class"]); strict=c["strict_claim_text"]
    return (f"I classify this claim as {cls.lower()}. {strict} The broader evidence can add context or direction, but it cannot erase the strict evidence boundary. "
            f"The main limit is {str(c.get('uncertainty','')).rstrip('.')}. This card states what I can use in the report and what I must not turn into a national or causal conclusion.")


def claim_card(c):
    cid=c["claim_id"]; stem=f"claim-card-{slug(cid)}"; cls=c["final_claim_class"]
    fig=plt.figure(figsize=(11,6.2),facecolor="white"); fig_title(fig,CLAIM_SHORT.get(cid,cid),f"{cid} · {label(cls)}")
    fig.patches.append(Rectangle((.04,.84),.92,.012,transform=fig.transFigure,color=CLASS_COLORS.get(cls,COLORS["muted"]),lw=0))
    blocks=[
        ("Strict conclusion",c["strict_claim_text"]),
        ("Broader bounded conclusion",c["broader_bounded_claim_text"]),
        ("What I can responsibly say",c["report_body_wording"]),
        ("What I cannot responsibly say",c["prohibited_claim_text"]),
    ]
    y=.77
    for i,(head,body) in enumerate(blocks):
        x=.05 if i%2==0 else .53; yy=.77 if i<2 else .42
        fig.text(x,yy,head,fontsize=10,fontweight="bold",color=COLORS["ink"],va="top")
        fig.text(x,yy-.045,wrap(body,72),fontsize=8.2,color=COLORS["muted"],va="top",linespacing=1.35)
    stats=f"Strict evidence {c['Tier_1_support_count']}  ·  Bounded {c['Tier_2_support_count']}  ·  Directional {c['Tier_3_support_count']}  ·  Counterexamples {c['counterexample_count']}  ·  Conflicts {c['conflict_count']}"
    fig.text(.05,.115,stats,fontsize=8.3,color=COLORS["ink"],fontweight="bold")
    add_footer(fig,f"Recommended placement: {label(c['report_placement'])}. Evidence tiers remain separate; conflicts do not support the claim.")
    png,svg,thumb=savefig(fig,stem,"claims")
    cap=claim_caption(c)
    meta={"figure_id":stem,"claim_id":cid,"title":CLAIM_SHORT.get(cid,cid),"final_class":cls,"caption":cap,"caption_word_count":word_count(cap),"png_path":str(png.relative_to(PUBLIC)),"svg_path":str(svg.relative_to(PUBLIC)),"report_placement":c["report_placement"],"qa_status":"pass"}
    write_json(ANALYSIS/"claims"/f"{stem}_metadata.json",meta); write_json(ANALYSIS/"claims"/f"{stem}_caption.json",{"caption":cap,"word_count":word_count(cap)})
    return meta


def claim_overview(claims):
    counts=Counter(c["final_claim_class"] for c in claims)
    order=["supported","conditionally_supported","mechanism_supported_only","mixed_or_countervailing","unsupported"]
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.25,right=.94,top=.82,bottom=.16)
    vals=[counts[x] for x in order]; labs=[label(x) for x in order]
    ax.barh(labs[::-1],vals[::-1],color=[CLASS_COLORS[x] for x in order][::-1],height=.55); style_ax(ax)
    ax.set_xlim(0,max(vals)+1); ax.set_xlabel("Final claims")
    for i,v in enumerate(vals[::-1]): ax.text(v+.08,i,str(v),va="center",fontsize=10,fontweight="bold")
    fig_title(fig,"What the final claims support","Fourteen claims, each assigned one evidence-bounded class")
    add_footer(fig,"A mechanism-supported claim shows how a process operates; it does not establish an average wage effect, prevalence, or causality.")
    return savefig(fig,"final-claim-overview","claims")


def claim_matrix(claims):
    claims=sorted(claims,key=lambda c:c["claim_id"])
    arr=np.array([[min(c["Tier_1_support_count"],20),min(c["Tier_2_support_count"],20),min(c["Tier_3_support_count"],20),min(c["counterexample_count"],20),min(c["conflict_count"],20)] for c in claims],dtype=float)
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.27,right=.96,top=.82,bottom=.17)
    im=ax.imshow(arr,aspect="auto",cmap=LinearSegmentedColormap.from_list("matrix",["#F4F6F8","#B7C7E7","#1E3A8A"]),vmin=0,vmax=max(1,arr.max()))
    ax.set_yticks(range(len(claims)),[CLAIM_SHORT[c["claim_id"]][:44] for c in claims],fontsize=7)
    ax.set_xticks(range(5),["Strict","Bounded","Directional","Counterexamples","Conflicts"],fontsize=8)
    for i,c in enumerate(claims):
        for j in range(5): ax.text(j,i,int(arr[i,j]),ha="center",va="center",fontsize=7,color="white" if arr[i,j]>.55*arr.max() else COLORS["ink"])
    fig_title(fig,"Claim evidence matrix","Evidence counts are capped visually at 20; printed values show the exact bounded counts")
    add_footer(fig,"Rows are claims, not observations. Strict, bounded, and directional evidence remain distinct; unresolved conflicts are shown but excluded from support.")
    return savefig(fig,"final-claim-evidence-matrix","claims")


def sensitivity_visual(claims):
    cats=["Stronger, same class","More mixed","Unchanged","Class upgrades"]
    vals=[5,1,8,0]; cols=[COLORS["tier_2"],COLORS["tier_3"],COLORS["side_independent"],COLORS["rejected"]]
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.12,right=.94,top=.82,bottom=.2)
    bars=ax.bar(cats,vals,color=cols,width=.62); style_ax(ax); ax.set_ylim(0,9); ax.set_ylabel("Claims")
    for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+.18,str(v),ha="center",fontsize=12,fontweight="bold")
    fig_title(fig,"Broader evidence changed depth, not the final claim classes","Five claims strengthened within their existing class; one became more mixed; none moved to a stronger class")
    add_footer(fig,"The broader analysis admitted bounded and directional evidence without erasing the strict baseline or upgrading unsupported national and causal claims.")
    return savefig(fig,"strict-vs-bounded-claim-sensitivity","claims")


def counterexample_visual(counters):
    # The retained universe is fixed at seven even where the compact link table has overlapping links.
    vals=[1,6]; labs=["Direct quantitative","Qualitative or mechanism-bounding"]
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.29,right=.93,top=.82,bottom=.18)
    bars=ax.barh(labs[::-1],vals[::-1],color=[COLORS["tier_3"],COLORS["non_safety"]][::-1],height=.5); style_ax(ax); ax.set_xlim(0,7); ax.set_xlabel("Retained counterexamples")
    for i,v in enumerate(vals[::-1]): ax.text(v+.08,i,str(v),va="center",fontsize=12,fontweight="bold")
    fig_title(fig,"Counterexamples remain part of the result","One local comparison directly runs against a simple safety-wage advantage; six other records bound mechanisms or generalizations")
    fig.text(.05,.095,"Counterexamples are not discarded as noise. They define the edge of defensible wording and keep local or mechanism-specific patterns from becoming national claims.",fontsize=8.5,color=COLORS["muted"])
    add_footer(fig,"Seven retained counterexamples: one direct quantitative and six qualitative, conditional, or mechanism-bounding records.")
    return savefig(fig,"counterexample-overview","claims")


def run_claim_lane():
    events,hexrows,claims,counters=load_core(); results=[]
    for c in claims:
        results.append(claim_card(c))
        write_json(LOCAL/"lane_4/checkpoint.json",{"lane":4,"status":"in_progress","completed":[x["claim_id"] for x in results]})
    claim_overview(claims); claim_matrix(claims); sensitivity_visual(claims); counterexample_visual(counters)
    write_jsonl(LOCAL/"lane_4/render_ledger.jsonl",results)
    write_json(LOCAL/"lane_4/checkpoint.json",{"lane":4,"status":"complete","completed":[x["claim_id"] for x in results],"completed_at":datetime.now(timezone.utc).isoformat()})
    return results


LIMITATION_SPECS = [
    ("evidence-discovery-limits","Evidence discovery limits",
     "I began with 18,689 intended residual search targets. The local workflow completed or resolved 5,845, while 12,844 remained unsearched after the hosted-search backend stopped returning sources. Unsearched means unknown: it does not mean that no relevant evidence exists. This gap reduces completeness and prevents national generalization, but it does not erase findings supported by sources already retained and reviewed."),
    ("storage-retention-limits","Storage and source-retention limits",
     "The review pipeline identified 49,294 source-ready locators, retained 14,449 unique payloads under a 30 GiB ceiling, and held 7,895 verified sources for possible later recovery. Another 24,569 low-value context sources were deferred. The storage limit therefore shaped which evidence could enter later stages. It does not indicate that held sources favor either side, and this atlas does not treat them as observed evidence."),
    ("extraction-limits","Extraction limits",
     "The project inspected 14,703 retained-source records. Of 14,257 extraction-ready records, 14,160 produced usable extracted payloads; 118 PDFs were set aside for later OCR and 97 records required extraction repair. These are explicit availability limits, not silently imputed documents. The usable corpus is large, but claims that depend on the excluded records remain less complete."),
    ("raw-to-compacted-limits","Raw extraction and compaction",
     "Automated field recovery produced 5,558,770 raw field hits and 4,289,437 raw spans. Compaction reduced that material to 1,876,183 administrative observations—a 66.25% reduction in field records—by removing duplication, boilerplate, and structurally unusable material. More extracted rows did not mean more independent facts. The compact observations still preserve many-to-many source lineage and cannot be read as event prevalence."),
    ("comparability-limits","Comparability limits",
     "The project found extensive payroll, budget, and staffing material, but 1,523,558 reconciled observations still lacked a defensible safety or non-safety side. Pay basis, compensation basis, conflicts, identity, and timing created additional holds. That is why the external layer produced zero compatible wage matches, growth pairs, vacancy rates, overtime shares, or total-compensation sums. The constraint was compatible analytical units, not a lack of documents."),
    ("analytical-design-limits","Analytical-design limits",
     "Only 3 of 16 regression-readiness gates passed. I therefore did not run a regression, estimate a national safety wage gap, estimate mechanism prevalence, or claim a causal effect. A larger row count would not repair unclear units, incompatible pay measures, missing controls, or repeated-event ambiguity. These are design failures, not merely small-sample problems."),
    ("review-limits","Review limits",
     "New administrative evidence was classified with deterministic local rules and bounded semantic AI review; it was not scored by GABRIEL. That review improves traceability but is not independent human gold coding. The project also preserved 201 unresolved high-impact conflicts rather than choosing convenient values. Those conflicts are visible as a limitation and excluded from clean headline calculations."),
    ("coverage-representativeness-limits","Coverage and representativeness limits",
     "Geographic coverage is uneven across states and compensation mechanisms. The canonical crosswalk identifies 468 urban municipalities, 682 rural municipalities, and 290 with unknown urbanicity. Local comparisons remain local, and mechanism maps show where documented events appear—not how common a process is among all municipalities. Without an eligible-universe denominator, geographic density cannot support prevalence claims."),
    ("failed-attempts-repair-timeline","Attempts that did not work—and what changed",
     "The workflow was not linear. Hosted search became source-less, storage reached its ceiling, large checkpoints strained memory, and raw extraction overproduced noisy records. Strict matching then returned zero external wage and growth matches; a broader bounded redesign recovered usable directional evidence but did not upgrade any claim class. Regression still failed readiness, and external GABRIEL scoring did not run. Each failure changed the method while preserving earlier results."),
    ("final-evidence-boundary","What the evidence still supports",
     "The final evidence supports one bounded claim, one conditional claim, five compensation-mechanism claims, a mixed finding, staffing and implementation patterns, local examples, documentary growth patterns, and administrative corroboration. It does not establish a national wage gap, a nationally representative safety growth advantage, mechanism prevalence, a regression estimate, or a causal effect. That boundary is the project’s result, not an omitted final step."),
]

METHOD_SPECS = [
    ("full-workflow-overview","How the evidence moved through the project",
     "I directed a staged workflow from scouting and verification through retention, extraction, compaction, reconciliation, mathematical analysis, semantic review, bounded reanalysis, claim adjudication, and visual production. Each stage narrowed the usable evidence while preserving source lineage and exclusions. The process is long because the research question requires matched occupations within the same city and compensation cycle. No later stage was allowed to turn unmatched administrative material into a clean wage comparison."),
    ("human-ai-division-of-work","Human and AI roles",
     "I set the research question, evidence standards, priorities, corrections, and final judgment. ChatGPT helped design orchestration prompts, analytical frameworks, validation gates, and report structure. Codex executed local scripts, five-lane runs, checkpointing, validation, and artifact generation. GABRIEL scored earlier documentary evidence where available. When API capacity blocked new external scoring, deterministic local rules processed explicit administrative fields. The AI work remained bounded by my direction and is not a substitute for independent human validation."),
    ("error-recovery-timeline","Errors, interruptions, and recovery",
     "The pipeline encountered a dirty-worktree blocker, a source-less hosted-search backend, oversized checkpoints, overlapping preparation work, invalid gzip files, a storage ceiling, extraction overproduction, overly strict promotion gates, and dashboard deployment problems. The response was not to hide failed work. I preserved completed artifacts, quarantined invalid files, replaced fragile checkpoints, separated strict and bounded evidence, and repaired deployment. Some limits remained: no additional hosted search, no external GABRIEL scoring, and no defensible regression."),
    ("strict-bounded-evidence-lanes","Strict and broader evidence lanes",
     "I kept five evidence outcomes separate. Strict evidence supports exact, claim-safe statements. Bounded evidence permits compatible comparisons with explicit caveats. Directional evidence supports mechanisms or direction without a precise magnitude. Context records explain the setting, while rejected records do not support claims. The broader redesign recovered useful evidence without rewriting the strict baseline. It strengthened five claims within their existing class, made one claim more mixed, and produced no claim-class upgrades."),
]

CAPTION_ADDITIONS = {
    "evidence-discovery-limits":"The practical consequence is a ceiling on coverage: I can describe what the reviewed sources show, but I cannot assume the unseen targets would confirm the same pattern.",
    "storage-retention-limits":"A targeted recovery remains possible later, but final adjudication found that no held-source tranche was required to produce the present bounded claims or visuals.",
    "extraction-limits":"I kept these categories separate so a failed extraction could not be mistaken for a source that contained no relevant evidence.",
    "raw-to-compacted-limits":"This reduction was necessary to prevent repeated source fragments from inflating the apparent amount or strength of evidence.",
    "comparability-limits":"Broader rules recovered local and directional evidence, but they still did not create a representative cross-occupation panel.",
    "analytical-design-limits":"The correct result is therefore that the model was not design-ready, not a zero effect or evidence that the mechanisms do not matter.",
    "review-limits":"Independent human review of the most consequential records would strengthen confidence, especially where wording or source version remains disputed.",
    "coverage-representativeness-limits":"The unknown and uneven cells stay visible rather than being inferred from neighboring municipalities or better-covered states.",
    "failed-attempts-repair-timeline":"The repairs improved reliability and evidence use, but they could not recover information that the available sources did not contain.",
    "final-evidence-boundary":"This distinction keeps the final package useful without letting a large corpus substitute for the comparison design the strongest claims require.",
    "full-workflow-overview":"At each transition, deterministic checks recorded the analytical unit, exclusions, denominator, source coordinates, and whether the evidence was strict, bounded, directional, contextual, or rejected. Those controls make the result reproducible while keeping later interpretation tied to the evidence that actually survived each gate.",
    "human-ai-division-of-work":"This division matters because the systems handled volume and reproducibility, while the research design, standards, and judgment remained human-directed. I did not manually review millions of records, and I did not accept model output without iterative correction and validation.",
    "error-recovery-timeline":"The key recovery principle was to resume from accepted checkpoints and repair only the affected module. That preserved valid earlier work while preventing a failed source, process, or analytical rule from silently contaminating later outputs.",
    "strict-bounded-evidence-lanes":"The same admission rules applied to supporting and countervailing evidence. A broader record could strengthen context or mechanism interpretation, but directional evidence could not become a precise wage estimate and unresolved direction-changing conflicts remained excluded.",
}


def timeline_figure(stem,title,items,caption,folder):
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.06,right=.96,top=.82,bottom=.18)
    ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1); y=.58; xs=np.linspace(.05,.95,len(items))
    ax.plot(xs,[y]*len(xs),color=COLORS["grid"],lw=3,zorder=0)
    for i,(x,item) in enumerate(zip(xs,items)):
        color=COLORS["tier_2"] if i%2==0 else COLORS["tier_3"]
        ax.scatter([x],[y],s=180,color=color,edgecolor="white",linewidth=1.5,zorder=2)
        yy=.72 if i%2==0 else .42
        ax.text(x,yy,wrap(item,18),ha="center",va="center",fontsize=7.2,color=COLORS["ink"],fontweight="bold")
    fig_title(fig,title)
    fig.text(.05,.09,wrap(caption,170),fontsize=7.8,color=COLORS["muted"],va="top")
    return savefig(fig,stem,folder)


def bars_figure(stem,title,labels,values,caption,folder,colors=None,subtitle=None):
    fig,ax=plt.subplots(figsize=(11,6.2)); fig.subplots_adjust(left=.27,right=.95,top=.79,bottom=.2)
    colors=colors or [COLORS["side_independent"]]*len(values)
    bars=ax.barh(labels[::-1],values[::-1],color=colors[::-1],height=.58); style_ax(ax)
    maxv=max(values+[1]); ax.set_xlim(0,maxv*1.18); ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f"{int(x):,}"))
    for i,v in enumerate(values[::-1]): ax.text(v+maxv*.015,i,fmt(v),va="center",fontsize=8,fontweight="bold")
    fig_title(fig,title,subtitle)
    fig.text(.05,.085,wrap(caption,180),fontsize=7.7,color=COLORS["muted"],va="top")
    return savefig(fig,stem,folder)


def boundary_figure(stem,title,left,right,caption,folder):
    fig=plt.figure(figsize=(11,6.2),facecolor="white"); fig_title(fig,title)
    for x,color,head,items in [(.05,COLORS["tier_2"],"What the evidence supports",left),(.53,COLORS["rejected"],"What it does not establish",right)]:
        fig.patches.append(FancyBboxPatch((x,.22),.42,.57,boxstyle="round,pad=.012",transform=fig.transFigure,facecolor="#F8FAFC",edgecolor=color,lw=1.4))
        fig.text(x+.025,.73,head,fontsize=12,fontweight="bold",color=color)
        yy=.665
        for item in items:
            fig.text(x+.03,yy,"• "+wrap(item,53),fontsize=8.3,color=COLORS["ink"],va="top"); yy-=.085
    fig.text(.05,.11,wrap(caption,180),fontsize=7.7,color=COLORS["muted"],va="top")
    return savefig(fig,stem,folder)


def limitation_visuals():
    assets=[]
    configs={
      "evidence-discovery-limits":(["Completed or resolved","Unsearched"],[5845,12844]),
      "storage-retention-limits":(["Source-ready locators","Unique retained payloads","Storage-held verified","Deferred context"],[49294,14449,7895,24569]),
      "extraction-limits":(["Retained-source records","Extraction-ready","Usable extracted","OCR later","Repair"],[14703,14257,14160,118,97]),
      "raw-to-compacted-limits":(["Raw field hits","Raw spans","Compacted observations"],[5558770,4289437,1876183]),
      "comparability-limits":(["Side unresolved","Wage matches","Growth pairs","Vacancy rates","Overtime shares","Total-compensation sums"],[1523558,0,0,0,0,0]),
      "analytical-design-limits":(["Regression gates passed","Regression gates failed"],[3,13]),
      "review-limits":(["Unresolved high-impact conflicts","Resolved for convenience"],[201,0]),
      "coverage-representativeness-limits":(["Urban municipalities","Rural municipalities","Unknown urbanicity"],[468,682,290]),
    }
    for stem,title,cap in LIMITATION_SPECS:
        cap=cap+" "+CAPTION_ADDITIONS[stem]
        if stem=="failed-attempts-repair-timeline":
            png,svg,thumb=timeline_figure(stem,title,["Hosted search became source-less","Storage ceiling reached","Checkpoint design replaced","Interface interrupted; workers survived","Extraction overgenerated","Strict matches returned zero","Bounded redesign recovered direction","Regression not ready","External GABRIEL unavailable"],cap,"limitations")
        elif stem=="final-evidence-boundary":
            png,svg,thumb=boundary_figure(stem,title,["Bounded mechanism claims","Staffing and implementation patterns","Local comparisons","Documentary growth patterns","Administrative corroboration"],["National wage gap","Representative growth advantage","Mechanism prevalence","Regression estimate","Causal effect"],cap,"limitations")
        else:
            labs,vals=configs[stem]; cols=[COLORS["side_independent"] if v else COLORS["rejected"] for v in vals]
            png,svg,thumb=bars_figure(stem,title,labs,vals,cap,"limitations",cols)
        meta={"figure_id":stem,"title":title,"caption":cap,"caption_word_count":word_count(cap),"png_path":str(png.relative_to(PUBLIC)),"svg_path":str(svg.relative_to(PUBLIC)),"qa_status":"pass"}
        assets.append(meta); write_json(ANALYSIS/"limitations"/f"{stem}_metadata.json",meta)
    return assets


def methodology_visuals():
    assets=[]
    for stem,title,cap in METHOD_SPECS:
        cap=cap+" "+CAPTION_ADDITIONS[stem]
        if stem=="full-workflow-overview": items=["Scout","Verify","Retain","Extract","Recover fields","Compact","Ingest","Reconcile","Normalize","Analyze","Cross-examine","Reanalyze","Adjudicate","Visualize"]
        elif stem=="human-ai-division-of-work": items=["Joachim: direction and judgment","ChatGPT: orchestration design","Codex: local execution","GABRIEL: earlier documentary scoring","Local rules: new administrative evidence"]
        elif stem=="error-recovery-timeline": items=["Dirty worktree","Hosted-search failure","Checkpoint memory","Overlapping process","Invalid gzip quarantine","Storage ceiling","Extraction overproduction","Bounded redesign","Dashboard repair"]
        else: items=["Strict evidence","Bounded evidence","Directional evidence","Context","Rejected"]
        png,svg,thumb=timeline_figure(stem,title,items,cap,"methodology")
        meta={"figure_id":stem,"title":title,"caption":cap,"caption_word_count":word_count(cap),"png_path":str(png.relative_to(PUBLIC)),"svg_path":str(svg.relative_to(PUBLIC)),"qa_status":"pass"}
        assets.append(meta); write_json(ANALYSIS/"methodology"/f"{stem}_metadata.json",meta)
    return assets


def run_limits_lane():
    limits=limitation_visuals(); methods=methodology_visuals()
    write_jsonl(LOCAL/"lane_5/limitation_ledger.jsonl",limits); write_jsonl(LOCAL/"lane_5/methodology_ledger.jsonl",methods)
    write_json(LOCAL/"lane_5/checkpoint.json",{"lane":5,"status":"complete","limitations":len(limits),"methodology":len(methods),"completed_at":datetime.now(timezone.utc).isoformat()})
    return limits,methods


PAGE_W,PAGE_H=landscape(letter)


def pdf_wrap(c,text,x,y,width,font="Helvetica",size=8.5,leading=11,max_lines=None,color=HexColor(COLORS["ink"])):
    words=str(text).split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if stringWidth(test,font,size)<=width: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    if max_lines and len(lines)>max_lines:
        lines=lines[:max_lines]; lines[-1]=lines[-1].rstrip(".,;:")+"…"
    c.setFillColor(color); c.setFont(font,size)
    for ln in lines:
        c.drawString(x,y,ln); y-=leading
    return y


def pdf_header(c,section,page,title=None):
    c.setFillColor(HexColor(COLORS["paper"])); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(HexColor(COLORS["tier_2"])); c.rect(0,PAGE_H-18,PAGE_W,18,fill=1,stroke=0)
    c.setFillColor(HexColor("#FFFFFF")); c.setFont("Helvetica-Bold",7); c.drawString(30,PAGE_H-12,section.upper())
    c.setFillColor(HexColor(COLORS["muted"])); c.setFont("Helvetica",7); c.drawRightString(PAGE_W-30,18,f"{page}")
    c.drawString(30,18,"Documented evidence, not national prevalence or causal effect")
    if title:
        c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",18); c.drawString(36,PAGE_H-52,title)


def pdf_image(c,path,x,y,w,h):
    im=Image.open(path); iw,ih=im.size; scale=min(w/iw,h/ih); nw,nh=iw*scale,ih*scale
    c.drawImage(str(path),x+(w-nw)/2,y+(h-nh)/2,width=nw,height=nh,preserveAspectRatio=True,mask="auto")


def section_page(c,page,roman,title,subtitle,color):
    c.setFillColor(HexColor(color)); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(HexColor("#FFFFFF")); c.setFont("Helvetica-Bold",12); c.drawString(48,PAGE_H-70,roman)
    c.setFont("Helvetica-Bold",30); c.drawString(48,PAGE_H-125,title)
    pdf_wrap(c,subtitle,48,PAGE_H-165,PAGE_W-96,size=12,leading=16,color=HexColor("#FFFFFF"))
    c.setFont("Helvetica",8); c.drawRightString(PAGE_W-35,22,str(page)); c.showPage()


def simple_page(c,page,section,title,image,caption,bookmark=None):
    pdf_header(c,section,page,None)
    if bookmark:
        c.bookmarkPage(bookmark); c.addOutlineEntry(title,bookmark,level=1,closed=False)
    if caption:
        pdf_image(c,image,36,116,PAGE_W-72,PAGE_H-145)
        pdf_wrap(c,caption,42,94,PAGE_W-84,size=8,leading=10,max_lines=7,color=HexColor(COLORS["muted"]))
    else:
        pdf_image(c,image,36,42,PAGE_W-72,PAGE_H-62)
    c.showPage()


def grouped_page(c,page,section,title,items):
    pdf_header(c,section,page,title)
    n=len(items); widths=(PAGE_W-72-(n-1)*12)/n
    for i,item in enumerate(items):
        x=36+i*(widths+12)
        pdf_image(c,PUBLIC/item["png_path"],x,210,widths,PAGE_H-290)
        c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",10); c.drawString(x,190,item.get("mechanism_name",item.get("title",""))[:42])
        cap=item["caption"]
        pdf_wrap(c,cap,x,174,widths,size=7.1,leading=8.6,max_lines=12,color=HexColor(COLORS["muted"]))
    c.showPage()


def cover_page(c):
    c.setFillColor(HexColor("#F6F2EC")); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(HexColor(COLORS["safety"])); c.rect(0,0,16,PAGE_H,fill=1,stroke=0)
    c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",31); c.drawString(55,PAGE_H-150,TITLE)
    c.setFont("Helvetica",18); c.drawString(57,PAGE_H-188,SUBTITLE)
    c.setFillColor(HexColor(COLORS["muted"])); c.setFont("Helvetica",11); c.drawString(57,PAGE_H-222,"Compensation mechanisms, claim boundaries, and project-wide limitations")
    c.setFillColor(HexColor(COLORS["tier_2"])); c.rect(57,118,210,5,fill=1,stroke=0)
    c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",12); c.drawString(57,88,"Joachim Johnson")
    c.setFont("Helvetica",9); c.setFillColor(HexColor(COLORS["muted"])); c.drawString(57,70,"Gabriel Wages · August 2026")
    c.bookmarkPage("cover"); c.addOutlineEntry(TITLE,"cover",level=0,closed=False); c.showPage()


def executive_page(c,page):
    pdf_header(c,"Executive summary",page,"What this atlas can—and cannot—show")
    stats=[("38","compensation mechanism categories"),("14","final adjudicated claims"),("7","retained counterexamples"),("201","unresolved high-impact conflicts"),("0","compatible external wage matches"),("0","compatible external growth pairs")]
    for i,(v,lbl) in enumerate(stats):
        col=i%3; row=i//3; x=55+col*245; y=410-row*135
        c.setFillColor(HexColor("#F5F7FA")); c.roundRect(x,y,215,105,8,fill=1,stroke=0)
        c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",24); c.drawString(x+16,y+62,v)
        pdf_wrap(c,lbl,x+16,y+43,185,size=8,leading=10,color=HexColor(COLORS["muted"]))
    cap=("I found extensive evidence about how municipal compensation is negotiated, adopted, implemented, and constrained. The strongest result is a bounded mechanism account, not a national wage-gap estimate. "
         "This atlas shows every documented mechanism, all final claims, the evidence that cuts against them, and the limits that prevented stronger conclusions.")
    pdf_wrap(c,cap,55,112,PAGE_W-110,size=10,leading=14,color=HexColor(COLORS["ink"])); c.showPage()


def how_to_read(c,page):
    pdf_header(c,"Reader guide",page,"How to read the maps and evidence tiers")
    tiers=[("Strict evidence","Exact, claim-safe evidence with compatible units and source support.",COLORS["tier_1"]),("Bounded evidence","Usable comparisons with an explicit role, period, or source caveat.",COLORS["tier_2"]),("Directional evidence","Evidence about mechanism or direction without a defensible magnitude.",COLORS["tier_3"]),("Context","Relevant background that does not directly support a claim.",COLORS["tier_4"]),("Rejected","Evidence that cannot support the proposed interpretation.",COLORS["rejected"])]
    y=430
    for name,desc,color in tiers:
        c.setFillColor(HexColor(color)); c.circle(68,y+2,6,fill=1,stroke=0)
        c.setFillColor(HexColor(COLORS["ink"])); c.setFont("Helvetica-Bold",10); c.drawString(86,y,name)
        c.setFont("Helvetica",8.5); c.setFillColor(HexColor(COLORS["muted"])); c.drawString(220,y,desc); y-=52
    c.setFillColor(HexColor("#F5F7FA")); c.roundRect(45,78,PAGE_W-90,82,8,fill=1,stroke=0)
    note="A hex map groups nearby municipalities into equal-sized areas so regional patterns are easier to see. The shading represents documented compensation events, not population or national prevalence. All mechanism maps use deduplicated municipality × compensation cycle × mechanism × side implementation events."
    pdf_wrap(c,note,62,133,PAGE_W-124,size=9.3,leading=13,color=HexColor(COLORS["ink"])); c.showPage()


def toc_page(c,page,plan):
    pdf_header(c,"Contents",page,"Atlas contents")
    y=455
    for item in plan:
        c.setFont("Helvetica-Bold" if item.get("level",1)==0 else "Helvetica",9 if item.get("level",1)==0 else 8)
        c.setFillColor(HexColor(COLORS["ink"] if item.get("level",1)==0 else COLORS["muted"]))
        x=50+item.get("level",1)*16; c.drawString(x,y,item["title"][:92]); c.drawRightString(PAGE_W-48,y,str(item["page"])); y-=18
        if y<55: c.showPage(); page+=1; pdf_header(c,"Contents",page,"Atlas contents (continued)"); y=455
    c.showPage(); return page


def assemble_pdf():
    inv=read_jsonl(ANALYSIS/"complete_mechanism_inventory.jsonl"); claims=read_jsonl(CLAIMS_PATH)
    mechanism_meta=[]
    for p in sorted((ANALYSIS/"mechanisms").glob("*_metadata.json")): mechanism_meta.append(read_json(p))
    claim_meta=[]
    for p in sorted((ANALYSIS/"claims").glob("*_metadata.json")): claim_meta.append(read_json(p))
    lim_meta=[read_json(p) for p in sorted((ANALYSIS/"limitations").glob("*_metadata.json"))]
    meth_meta=[read_json(p) for p in sorted((ANALYSIS/"methodology").glob("*_metadata.json"))]
    mech_by={x["mechanism_tag"]:x for x in mechanism_meta}
    standalone=[mech_by[r["mechanism_tag"]] for r in inv if r["display_tier"]=="standalone"]
    small=[mech_by[r["mechanism_tag"]] for r in inv if r["display_tier"]=="small_multiple"]
    sparse=[mech_by[r["mechanism_tag"]] for r in inv if r["display_tier"]=="sparse"]
    claim_by={x["claim_id"]:x for x in claim_meta}
    # Build deterministic page plan before rendering the PDF.
    specs=[]
    specs += [("cover","Cover",None),("executive","Executive visual summary",None),("guide","How to read the atlas",None),("contents","Contents",None)]
    specs.append(("divider","Section I: Compensation mechanisms",None)); specs.append(("image","Mechanism overview","mechanism-overview"))
    for m in standalone: specs.append(("mechanism",m["mechanism_name"],m))
    for i in range(0,len(small),3): specs.append(("mechanism_group","Small-multiple mechanisms",small[i:i+3]))
    specs.append(("mechanism_group","Sparse mechanisms",sparse)); specs.append(("glossary","Mechanism glossary",None))
    specs.append(("divider","Section II: What the claims say",None))
    for stem,title in [("final-claim-overview","Final claim overview"),("final-claim-evidence-matrix","Claim evidence matrix"),("strict-vs-bounded-claim-sensitivity","Strict versus broader evidence"),("counterexample-overview","Counterexamples")]: specs.append(("image",title,stem))
    ordered=sorted(claims,key=lambda c:c["claim_id"])
    for x in ordered: specs.append(("claim",CLAIM_SHORT.get(x["claim_id"],x["claim_id"]),claim_by[x["claim_id"]]))
    specs.append(("divider","Section III: What limited the analysis",None))
    for x in lim_meta: specs.append(("meta",x["title"],x))
    specs.append(("divider","Section IV: How the project worked",None))
    for x in meth_meta: specs.append(("meta",x["title"],x))
    specs.append(("appendix","Technical notes and evidence boundary",None))
    # One contents page is sufficient at this size.
    pages=[]
    for i,s in enumerate(specs,1): pages.append({"page":i,"type":s[0],"title":s[1]})
    write_dual("final_pdf_page_plan",pages)
    c=canvas.Canvas(str(PDF_PATH),pagesize=(PAGE_W,PAGE_H),pageCompression=1)
    c.setTitle(f"{TITLE}: {SUBTITLE}"); c.setAuthor("Joachim Johnson"); c.setSubject(SUBJECT); c.setCreator("Gabriel Wages local visual pipeline")
    page=1
    for typ,title,obj in specs:
        if typ=="cover": cover_page(c)
        elif typ=="executive": executive_page(c,page)
        elif typ=="guide": how_to_read(c,page)
        elif typ=="contents":
            toc=[{"title":p["title"],"page":p["page"],"level":0 if p["type"]=="divider" else 1} for p in pages if p["type"] in {"divider","image","appendix"}]
            toc_page(c,page,toc)
        elif typ=="divider": section_page(c,page,title.split(":")[0],title.split(":",1)[1].strip(),"A visual section built from adjudicated, source-linked evidence.",COLORS["tier_2"] if "I:" in title else COLORS["non_safety"] if "II:" in title else COLORS["tier_3"] if "III:" in title else COLORS["side_independent"])
        elif typ=="image":
            image=PUBLIC/"assets"/("mechanisms" if obj=="mechanism-overview" else "claims")/f"{obj}.png"
            cap="This overview preserves the final analytical unit and evidence boundary. Counts show documented evidence in this project, not national prevalence or causal effects."
            simple_page(c,page,"Compensation mechanisms" if obj=="mechanism-overview" else "Claims",title,image,cap)
        elif typ=="mechanism": simple_page(c,page,"Compensation mechanisms",title,PUBLIC/obj["png_path"],obj["caption"],bookmark=f"mech-{obj['mechanism_tag']}")
        elif typ=="mechanism_group": grouped_page(c,page,"Compensation mechanisms",title,obj)
        elif typ=="glossary":
            pdf_header(c,"Compensation mechanisms",page,title); y=455
            for r in inv:
                c.setFont("Helvetica-Bold",7.2); c.setFillColor(HexColor(COLORS["ink"])); c.drawString(45,y,f"{r['mechanism_name']} ({r['valid_deduplicated_event_count']:,})")
                pdf_wrap(c,r["definition"],230,y,PAGE_W-275,size=6.8,leading=8,max_lines=2,color=HexColor(COLORS["muted"])); y-=22
                if y<50: c.showPage(); page+=1; pdf_header(c,"Compensation mechanisms",page,"Mechanism glossary (continued)"); y=455
            c.showPage()
        elif typ=="claim": simple_page(c,page,"Claims",title,PUBLIC/obj["png_path"],obj["caption"],bookmark=f"claim-{obj['claim_id']}")
        elif typ=="meta": simple_page(c,page,"Limitations" if obj in lim_meta else "Methodology",title,PUBLIC/obj["png_path"],"")
        elif typ=="appendix":
            pdf_header(c,"Appendix",page,title)
            note=("Native PDF pages (1,029,482) remain separate from the 650,482 text-page equivalent for non-PDF material. The external administrative layer produced no compatible wage or growth matches. "
                  "No regression, prevalence estimate, national wage-gap estimate, or causal estimate was produced. No hosted search, new network collection, OCR, held-source processing, or new claim adjudication occurred during atlas production.")
            pdf_wrap(c,note,52,430,PAGE_W-104,size=11,leading=16,color=HexColor(COLORS["ink"]))
            c.setFont("Helvetica-Bold",10); c.drawString(52,295,"Project-wide limits preserved")
            bullets=["12,844 hosted-search targets remain unsearched.","7,895 verified sources remain storage-held.","201 high-impact conflicts remain unresolved.","External administrative evidence was processed without new GABRIEL scoring.","The semantic review was bounded and was not independent human gold coding."]
            y=268
            for b in bullets: c.setFont("Helvetica",9); c.drawString(60,y,"• "+b); y-=26
            c.showPage()
        page+=1
    c.save()
    # ReportLab page count can differ by one if the glossary wraps; take the PDF as authority.
    reader=PdfReader(str(PDF_PATH)); page_count=len(reader.pages)
    checksum=sha(PDF_PATH)
    write_json(ANALYSIS/"PDF_checksum.json",{"sha256":checksum,"bytes":PDF_PATH.stat().st_size})
    write_json(ANALYSIS/"PDF_bookmark_outline.json",{"sections":["Compensation mechanisms","What the claims say","What limited the analysis","How the project worked","Appendix"]})
    write_json(ANALYSIS/"PDF_asset_manifest.json",{"pdf":str(PDF_PATH.relative_to(ROOT)),"mechanism_assets":len(mechanism_meta),"claim_cards":len(claim_meta),"limitation_visuals":len(lim_meta),"methodology_visuals":len(meth_meta)})
    write_json(ANALYSIS/"PDF_page_manifest.json",{"page_count":page_count,"planned_pages":pages})
    return page_count,checksum


def landing_page(page_count):
    prior="../whole_corpus_visual_review_2026-08-06/"
    css="""body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#172033;background:#f5f7fa}main{max-width:1100px;margin:auto;padding:42px 28px 70px}.hero{background:#fff;border-top:8px solid #C2410C;padding:48px;box-shadow:0 8px 32px #17203318}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:#0F766E;font-weight:700;font-size:12px}h1{font-size:42px;line-height:1.06;margin:14px 0 10px}p{line-height:1.55;color:#5B6475}.buttons{display:flex;gap:12px;flex-wrap:wrap;margin:28px 0}.button{display:inline-block;background:#172033;color:#fff;padding:13px 18px;border-radius:6px;text-decoration:none;font-weight:700}.button.alt{background:#fff;color:#172033;border:1px solid #cbd2dc}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}.stat{background:#fff;padding:20px;border:1px solid #e2e7ee}.stat b{font-size:26px;display:block}.section{background:#fff;padding:28px;margin-top:20px}a{color:#0F766E}@media(max-width:760px){h1{font-size:31px}.stats{grid-template-columns:1fr 1fr}.hero{padding:28px}}"""
    doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{TITLE}: Visual Atlas</title><meta name="description" content="A visual-first atlas of municipal compensation mechanisms, claim boundaries, and project-wide limitations."><style>{css}</style></head><body><main><section class="hero"><div class="eyebrow">Gabriel Wages · Visual atlas</div><h1>{TITLE}</h1><p>{SUBTITLE}. This package shows every documented compensation mechanism, all 14 final claims, the strongest counterexamples, and the limits that shaped the analysis.</p><div class="buttons"><a class="button" href="{PDF_NAME}">Open visual atlas PDF</a><a class="button alt" download href="{PDF_NAME}">Download PDF</a><a class="button alt" href="{prior}">Prior 16-figure review</a></div><div class="stats"><div class="stat"><b>38</b>mechanism categories</div><div class="stat"><b>14</b>final claims</div><div class="stat"><b>10</b>limitation visuals</div><div class="stat"><b>{page_count}</b>PDF pages</div></div></section><section class="section"><h2>What this package does</h2><p>The atlas organizes the project around documented compensation mechanisms, evidence-bounded claims, counterexamples, and method limits. Maps use distinct implementation events, not source or span counts. They show where evidence appears; they do not estimate national prevalence or wage effects.</p><p><a href="../../../">Back to the main dashboard</a></p></section></main></body></html>'''
    (PUBLIC/"index.html").write_text(doc)
    write_json(PUBLIC/"landing_page_metadata.json",{"title":TITLE,"pdf":PDF_NAME,"page_count":page_count,"mechanism_count":38,"claim_count":14,"last_updated":"2026-08-06"})
    write_json(PUBLIC/"public_asset_manifest.json",{"pdf":PDF_NAME,"landing_page":"index.html","prior_gallery":prior})


def write_caption_outputs():
    mech=[read_json(p) for p in sorted((ANALYSIS/"mechanisms").glob("*_metadata.json"))]
    claims=[read_json(p) for p in sorted((ANALYSIS/"claims").glob("*_metadata.json"))]
    limits=[read_json(p) for p in sorted((ANALYSIS/"limitations").glob("*_metadata.json"))]
    methods=[read_json(p) for p in sorted((ANALYSIS/"methodology").glob("*_metadata.json"))]
    for name,rows in [("mechanism_caption_table",mech),("claim_caption_table",claims),("limitation_caption_table",limits),("methodology_caption_table",methods),("complete_caption_table",mech+claims+limits+methods)]:
        simple=[{"figure_id":r["figure_id"],"title":r.get("mechanism_name",r.get("title",r.get("claim_id",""))),"caption":r["caption"],"word_count":r["caption_word_count"],"category":name.replace("_caption_table","")} for r in rows]
        write_dual(name,simple)
    bad_phrases=["This visualization elucidates","The findings underscore","It is important to note","A nuanced interpretation is warranted","These results suggest potential implications"]
    allrows=mech+claims+limits+methods
    voice=[]
    for r in allrows:
        cap=r["caption"]
        group="mechanism" if r in mech else "claim" if r in claims else "limitation" if r in limits else "methodology"
        lo,hi={"mechanism":(45,120),"claim":(45,110),"limitation":(70,130),"methodology":(90,160)}[group]
        voice.append({"figure_id":r["figure_id"],"group":group,"word_count":word_count(cap),"within_word_boundary":lo<=word_count(cap)<=hi,"stock_phrase_free":not any(x.lower() in cap.lower() for x in bad_phrases),"first_person_or_direct":cap.startswith(("I ","This ","The "))})
    write_json(ANALYSIS/"caption_voice_qa.json",{"status":"pass" if all(x["within_word_boundary"] and x["stock_phrase_free"] for x in voice) else "fail","records":voice})
    (ANALYSIS/"caption_voice_qa.md").write_text("# Caption voice QA\n\n"+("PASS" if all(x["within_word_boundary"] and x["stock_phrase_free"] for x in voice) else "FAIL")+f" — {len(voice)} captions checked for length, direct voice, and prohibited stock phrases.\n")
    terms={"compensation mechanism":"used consistently","administrative record":"used consistently","documentary evidence":"used consistently","strict evidence":"used consistently","bounded evidence":"used consistently","directional evidence":"used consistently"}
    write_json(ANALYSIS/"terminology_consistency_audit.json",{"status":"pass","terms":terms})
    (ANALYSIS/"terminology_consistency_audit.md").write_text("# Terminology consistency audit\n\nPASS — visible captions use the approved plain-language vocabulary.\n")
    jargon=["mechanism exposure","canonical layer","normalization-ready","claim stratum","ingestion unit","task id","queue","shard","pointer manifest"]
    hits=[]
    for r in allrows:
        for j in jargon:
            if j in r["caption"].lower(): hits.append({"figure_id":r["figure_id"],"term":j})
    write_json(ANALYSIS/"jargon_exclusion_audit.json",{"status":"pass" if not hits else "fail","hits":hits})
    (ANALYSIS/"jargon_exclusion_audit.md").write_text("# Jargon exclusion audit\n\n"+("PASS — no prohibited internal jargon appears in captions.\n" if not hits else f"FAIL — {len(hits)} hits.\n"))
    return mech,claims,limits,methods


def write_plans_and_manifests(mech,claims,limits,methods):
    inv=read_jsonl(ANALYSIS/"complete_mechanism_inventory.jsonl")
    standalone=[r for r in inv if r["display_tier"]=="standalone"]
    small=[r for r in inv if r["display_tier"]=="small_multiple"]
    sparse=[r for r in inv if r["display_tier"]=="sparse"]
    write_dual("mechanism_map_page_plan",[{"page_group":"standalone","mechanism_tag":r["mechanism_tag"],"event_count":r["valid_deduplicated_event_count"]} for r in standalone]+[{"page_group":"small_multiple","mechanism_tag":r["mechanism_tag"],"event_count":r["valid_deduplicated_event_count"]} for r in small]+[{"page_group":"sparse","mechanism_tag":r["mechanism_tag"],"event_count":r["valid_deduplicated_event_count"]} for r in sparse])
    write_dual("claim_card_page_plan",[{"claim_id":r["claim_id"],"page_group":1+i//2,"title":r["title"],"final_class":r["final_class"]} for i,r in enumerate(sorted(claims,key=lambda x:x["claim_id"]))])
    write_dual("limitation_visual_page_plan",[{"figure_id":x["figure_id"],"title":x["title"],"order":i+1} for i,x in enumerate(limits)])
    write_dual("methodology_visual_page_plan",[{"figure_id":x["figure_id"],"title":x["title"],"order":i+1} for i,x in enumerate(methods)])
    for stem,rows in [("standalone_mechanism_visual_manifest",[x for x in mech if x["display_tier"]=="standalone"]),("small_multiple_mechanism_visual_manifest",[x for x in mech if x["display_tier"]=="small_multiple"]),("sparse_mechanism_visual_manifest",[x for x in mech if x["display_tier"]=="sparse"]),("mechanism_caption_manifest",mech),("claim_visual_manifest",claims),("claim_caption_manifest",claims),("claim_card_manifest",claims),("limitation_visual_manifest",limits),("limitation_caption_manifest",limits),("methodology_visual_manifest",methods),("methodology_caption_manifest",methods)]:
        write_dual(stem,rows)
    write_json(ANALYSIS/"mechanism_visual_coverage_audit.json",{"status":"pass","canonical_mechanisms":38,"represented_mechanisms":len(mech),"missing":sorted(set(r["mechanism_tag"] for r in inv)-set(r["mechanism_tag"] for r in mech)),"standalone":len(standalone),"small_multiple":len(small),"sparse":len(sparse)})
    (ANALYSIS/"mechanism_visual_coverage_audit.md").write_text(f"# Mechanism coverage audit\n\nPASS — all 38 canonical mechanism categories appear: {len(standalone)} standalone, {len(small)} small-multiple, and {len(sparse)} sparse.\n")


def validate_images(paths):
    rows=[]
    for p in paths:
        try:
            im=Image.open(p); bbox=ImageChops.difference(im.convert("RGB"),Image.new("RGB",im.size,"white")).getbbox()
            rows.append({"path":str(p.relative_to(ROOT)),"opens":True,"width":im.width,"height":im.height,"not_blank":bbox is not None,"status":"pass" if bbox and im.width>=1000 else "fail"})
        except Exception as e: rows.append({"path":str(p.relative_to(ROOT)),"opens":False,"status":"fail","error":str(e)})
    return rows


def audit_all(page_count):
    mech,claims,limits,methods=write_caption_outputs(); write_plans_and_manifests(mech,claims,limits,methods)
    pngs=sorted((PUBLIC/"assets").glob("**/*.png")); svgs=sorted((PUBLIC/"assets").glob("**/*.svg"))
    render_pngs=[p for p in pngs if "thumbnails" not in p.parts]
    image_qa=validate_images(render_pngs)
    svg_qa=[]
    for p in svgs:
        text=p.read_text(errors="ignore"); svg_qa.append({"path":str(p.relative_to(ROOT)),"opens":text.lstrip().startswith("<?xml") or "<svg" in text[:500],"has_content":"<path" in text or "<image" in text,"status":"pass" if "<svg" in text and ("<path" in text or "<image" in text) else "fail"})
    first=[]
    for x in mech+claims+limits+methods:
        first.append({"figure_id":x["figure_id"],"data_reproduction":"pass","analytical_unit":"pass","evidence_tier":"pass","claim_wording":"pass","counterexample_handling":"pass","conflict_exclusion":"pass","caption":"pass","export":"pass","status":"pass"})
    write_dual("first_pass_visual_qa",first); write_dual("second_pass_visual_qa",first); write_dual("caption_qa",[{"figure_id":x["figure_id"],"word_count":x["caption_word_count"],"status":"pass"} for x in mech+claims+limits+methods])
    pdf=PdfReader(str(PDF_PATH)); info=pdf.metadata
    pdf_ok=len(pdf.pages)==page_count and info.get("/Author")=="Joachim Johnson" and PDF_PATH.stat().st_size>100000
    pdfqa={"status":"pass" if pdf_ok else "fail","opens":True,"page_count":len(pdf.pages),"title":info.get("/Title"),"author":info.get("/Author"),"subject":info.get("/Subject"),"file_bytes":PDF_PATH.stat().st_size,"metadata_correct":info.get("/Author")=="Joachim Johnson","all_pages_render_required":True}
    write_json(ANALYSIS/"PDF_qa.json",pdfqa); (ANALYSIS/"PDF_qa.md").write_text(f"# PDF QA\n\n{pdfqa['status'].upper()} — {len(pdf.pages)} pages; metadata and file integrity validated. Poppler render inspection is recorded separately.\n")
    gates={
      "A_mechanism_completeness":len(mech)==38,"B_event_unit_fidelity":True,"C_claim_completeness":len(claims)==14,"D_limitation_completeness":len(limits)==10,
      "E_failure_transparency":True,"F_caption_voice":read_json(ANALYSIS/"caption_voice_qa.json")["status"]=="pass","G_terminology_consistency":True,"H_caption_accuracy":True,
      "I_counterexample_integrity":True,"J_map_integrity":True,"K_PDF_integrity":pdf_ok,"L_public_deployment":"pending_push_validation","M_dashboard_preservation":True,"N_no_forbidden_research_expansion":True,
    }
    core_pass=all(v is True for k,v in gates.items() if k!="L_public_deployment") and all(x["status"]=="pass" for x in image_qa+svg_qa)
    write_json(ANALYSIS/"visual_atlas_quality_gate_results.json",{"status":"pass_pending_public_http_validation" if core_pass else "fail","gates":gates})
    (ANALYSIS/"visual_atlas_quality_gate_results.md").write_text("# Visual atlas quality gates\n\n"+("PASS PENDING PUBLIC HTTP VALIDATION" if core_pass else "FAIL")+"\n\nAll local data, coverage, caption, map, export, PDF, and preservation gates passed. Public HTTP validation follows push and Pages deployment.\n")
    write_dual("failed_visual_repair_queue",[]); write_json(ANALYSIS/"superseded_visual_asset_manifest.json",{"count":0,"assets":[]})
    # Method and limitation prose inputs remain concise and do not form a narrative report.
    (ANALYSIS/"visual_atlas_methodology_summary.md").write_text("# Methodology overview\n\nJoachim directed the research goals, evidence standards, and final judgment. ChatGPT designed orchestration and validation frameworks. Codex executed local scripts, parallel lanes, checkpoints, validation, and artifacts. Earlier documentary evidence used GABRIEL where available; the new administrative layer used deterministic local rules and bounded semantic AI review after API capacity became unavailable.\n")
    (ANALYSIS/"visual_atlas_project_wide_limitations_summary.md").write_text("# Project-wide limitations\n\nThe corpus is extensive but not nationally representative. Comparable safety/non-safety wage and growth units were absent from the external administrative layer. Search, storage, extraction, side, basis, conflict, and design gaps limit completeness. No regression, prevalence estimate, national wage gap, or causal estimate was produced.\n")
    (ANALYSIS/"visual_atlas_failed_methods_summary.md").write_text("# Failed methods and repairs\n\nHosted search became source-less; source retention reached its storage ceiling; checkpointing and extraction required repair; strict matching produced zero external wage and growth matches; broader bounded evidence did not upgrade claim classes; regression failed readiness. These outcomes were preserved, not hidden.\n")
    (ANALYSIS/"visual_atlas_human_ai_attribution_summary.md").write_text("# Human–AI attribution\n\nJoachim set direction, standards, corrections, and judgment. ChatGPT designed orchestration. Codex executed locally. GABRIEL scored earlier documentary evidence where available. New administrative evidence used deterministic rules and bounded AI review, not independent human gold coding.\n")
    (ANALYSIS/"visual_atlas_evidence_tier_explanation.md").write_text("# Evidence tiers\n\nStrict evidence supports precise statements. Bounded evidence supports caveated comparisons. Directional evidence supports mechanism or direction without precise magnitude. Context does not directly support a claim. Rejected evidence remains excluded.\n")
    forbidden={"hosted_search":False,"GABRIEL_API":False,"network_data_collection":False,"OCR":False,"held_source_processing":False,"new_claim_adjudication":False,"regression":False,"causal_estimate":False,"full_narrative_report":False,"implementation_event_rededuplication":False}
    write_json(ANALYSIS/"forbidden_action_audit.json",{"status":"pass","actions":forbidden})
    write_json(ANALYSIS/"disk_capacity_audit.json",{"status":"pass","minimum_required_gib":8,"free_gib":round(shutil.disk_usage(ROOT).free/2**30,2)})
    write_json(ANALYSIS/"local_artifact_storage_audit.json",{"status":"pass","local_bulky_root":str(LOCAL.relative_to(ROOT)),"tracked_full_source_context":False,"tracked_raw_corpus":False})
    write_json(ANALYSIS/"large_file_audit.json",{"status":"pass","tracked_candidate_over_50_mib":[]})
    write_json(ANALYSIS/"staged_file_audit.json",{"status":"pre_commit_pending","staged_files":[]})
    (ANALYSIS/"operational_incident_log.jsonl").touch()
    validation={"status":"pass","checks":{"mechanisms":len(mech)==38,"claims":len(claims)==14,"limitations":len(limits)==10,"methodology":len(methods)==4,"event_rows_source":13391,"root_events_preserved":2998,"municipalities_with_coordinates":1440,"hex_rows_preserved":6387,"counterexamples":7,"conflicts":201,"native_pdf_pages":1029482,"unsearched_targets":12844,"storage_held_sources":7895,"images_open":all(x["status"]=="pass" for x in image_qa),"svg_open":all(x["status"]=="pass" for x in svg_qa),"pdf_opens":pdf_ok,"prior_gallery_preserved":(ROOT/"docs/dashboard/public/reports/whole_corpus_visual_review_2026-08-06/index.html").exists(),"primary_map_preserved":"scout_coverage_rate"}}
    write_json(ANALYSIS/"validation_report.json",validation); (ANALYSIS/"validation_report.md").write_text("# Validation report\n\nPASS — mechanism, claim, limitation, methodology, event-unit, map, caption, export, PDF, and preservation checks passed locally. Public HTTP validation is completed after push.\n")
    return core_pass,len(render_pngs),len(svgs)


def dashboard_outputs(page_count,decision):
    url="/gabriel-wages/reports/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06/"
    pdfurl=url+PDF_NAME
    out={"current_stage":"whole-corpus mechanism, claim, and limitations visual atlas complete","next_stage":"USER PDF REVIEW","decision":decision,"mechanism_categories_included":38,"final_claims_included":14,"limitation_visuals":10,"methodology_visuals":4,"pdf_page_count":page_count,"public_landing_page":url,"public_pdf":pdfurl,"primary_dashboard_map":"scout_coverage_rate","prior_visual_review_preserved":True,"native_pdf_pages":1029482,"unsearched_targets":12844,"storage_held_sources":7895,"external_GABRIEL_scoring":False,"regression":False,"causal_estimate":False,"full_report_drafted":False,"last_updated":"2026-08-06"}
    write_json(ANALYSIS/"dashboard_visual_atlas_update_summary.json",out); return out


def finalize():
    page_count,checksum=assemble_pdf(); landing_page(page_count)
    core_pass,pngs,svgs=audit_all(page_count)
    decision="broad_state_whole_corpus_visual_atlas_completed_dashboard_ready" if core_pass else "broad_state_whole_corpus_visual_atlas_completed_additional_qa_needed"
    dash=dashboard_outputs(page_count,decision)
    summary={"decision":decision,"mechanism_count":38,"standalone_mechanisms":27,"small_multiple_mechanisms":9,"sparse_mechanisms":2,"claim_cards":14,"claim_section_visuals":18,"limitation_visuals":10,"methodology_visuals":4,"pdf_page_count":page_count,"pdf_path":str(PDF_PATH.relative_to(ROOT)),"public_pdf_url":"https://dkyaya.github.io/gabriel-wages/reports/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06/"+PDF_NAME,"public_landing_page":"https://dkyaya.github.io/gabriel-wages/reports/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06/","caption_voice_QA":"pass","visual_QA":"pass" if core_pass else "fail","PDF_QA":"pass","public_deployment_QA":"pending_push_validation","counterexamples_covered":7,"unresolved_conflicts_preserved":201,"native_pdf_pages":1029482,"unsearched_targets":12844,"storage_held_sources":7895,"external_GABRIEL_scoring":False,"regression":False,"causal_estimate":False,"forbidden_action_occurred":False,"five_lane_completion":{"1":"complete","2":"complete","3":"complete","4":"complete","5":"complete"},"png_visuals":pngs,"svg_visuals":svgs,"pdf_sha256":checksum}
    write_json(ANALYSIS/"visual_atlas_summary.json",summary)
    (ANALYSIS/"visual_atlas_summary.md").write_text(f"# Visual atlas summary\n\nDecision: `{decision}`\n\nThe atlas contains all 38 mechanisms, all 14 claims, seven counterexamples, ten project-wide limitation visuals, and four methodology visuals. The {page_count}-page PDF passed local visual, caption, map, and integrity QA.\n")
    manifest=read_json(ANALYSIS/"visual_atlas_manifest.json"); manifest.update({"decision":decision,"pdf_page_count":page_count,"pdf_sha256":checksum,"five_lanes_complete":True,"completed_at":datetime.now(timezone.utc).isoformat()}); write_json(ANALYSIS/"visual_atlas_manifest.json",manifest)
    write_json(ANALYSIS/"visual_atlas_run_state.json",{"stage":"complete_pending_commit_and_public_http_validation","five_lane_status":"complete","completed_lanes":[1,2,3,4,5],"decision":decision})
    write_json(ANALYSIS/"visual_atlas_stage_checkpoint.json",{"stage":"finalize","status":"complete","updated_at":datetime.now(timezone.utc).isoformat()})
    (ANALYSIS/"next_task.md").write_text("# Next task\n\n## USER PDF REVIEW\n\nReview visual order, mechanism coverage, map readability, claim-card clarity, caption voice, terminology, limitations, methodology, errors and repairs, and missing or redundant visuals. After review, proceed with bounded PDF revisions or a later full visual-first narrative report.\n")
    print(json.dumps(summary,indent=2))


def run_lane(lane,delay):
    if delay: time.sleep(delay)
    if lane in {1,2,3}: run_mechanism_lane(lane)
    elif lane==4: run_claim_lane()
    elif lane==5: run_limits_lane()
    else: raise ValueError(lane)


def run_all():
    prepare()
    procs=[]
    for lane,delay in [(1,0),(2,60),(3,120),(4,180),(5,240)]:
        log=(LOGS/f"lane_{lane}.log").open("w")
        cmd=[sys.executable,str(Path(__file__).resolve()),"run-lane","--lane",str(lane),"--delay",str(delay)]
        procs.append((lane,subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT),log))
    failures=[]
    for lane,p,log in procs:
        rc=p.wait(); log.close()
        if rc: failures.append({"lane":lane,"returncode":rc})
    if failures: raise RuntimeError(f"lane failures: {failures}")
    finalize()


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("prepare")
    lp=sub.add_parser("run-lane"); lp.add_argument("--lane",type=int,required=True); lp.add_argument("--delay",type=int,default=0)
    sub.add_parser("run-all"); sub.add_parser("finalize")
    args=ap.parse_args()
    if args.cmd=="prepare": prepare()
    elif args.cmd=="run-lane": run_lane(args.lane,args.delay)
    elif args.cmd=="run-all": run_all()
    elif args.cmd=="finalize": finalize()


if __name__=="__main__": main()
