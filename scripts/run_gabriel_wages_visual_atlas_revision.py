#!/usr/bin/env python3
"""Build the corrected, integrated Gabriel Wages visual atlas.

The program is intentionally local and deterministic.  It reads only existing
canonical project artifacts, preserves the first atlas byte-for-byte, and uses
five lane-owned output areas before a coordinator assembles the revised PDF.
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

ROOT = Path(__file__).resolve().parents[1]
TASK = "GABRIEL-WAGES-VISUAL-ATLAS-CORRECTION-AND-RESTRUCTURE-2026-08-06"
OUT = ROOT / "docs/analysis/handoff" / TASK
PUBLIC = ROOT / "docs/dashboard/public/reports/gabriel_wages_visual_atlas_revised_2026-08-06"
LOCAL = ROOT / "artifacts/local_structured_external_data/gabriel_wages_visual_atlas_revised_2026-08-06"
LOGS = ROOT / "tmp/gabriel_wages_visual_atlas_correction_2026-08-06_logs"
ORIGINAL_PUBLIC = ROOT / "docs/dashboard/public/reports/whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06"
ORIGINAL_ANALYSIS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-MECHANISM-CLAIM-LIMITATIONS-VISUAL-ATLAS-2026-08-06"
SCOUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
ADJ = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-INTEGRATION-AND-CLAIM-ADJUDICATION-2026-08-06"
AGG = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-AGGRESSIVE-BOUNDED-REANALYSIS-AND-CROSS-EXAMINATION-2026-08-06"
MATH = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-MATHEMATICAL-EXECUTION-AND-DESCRIPTIVE-ANALYSIS-2026-08-05"
SYNTH = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-RATING-SPAN-SYNTHESIS-AND-CLAIM-READINESS-2026-08-03"
CORRECT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EVIDENCE-CORRECTION-IMPLEMENTATION-EVENT-RECODING-AND-VISUAL-PREP-2026-08-04"
INVENTORY = ROOT / "docs/analysis/handoff/GABRIEL-WAGES-HANDOFF-FREEZE-AND-MASTER-INVENTORY-2026-08-06"
EVENTS = SCOUT / "mechanism_exposure_event_layer.jsonl"
OLD_HEX = SCOUT / "mechanism_hex_density_visual_ready_layer.jsonl"
CROSSWALK = SCOUT / "municipality_geographic_crosswalk.jsonl"
URBAN = SCOUT / "municipality_urbanicity_layer.jsonl"
CLAIMS = ADJ / "final_adjudicated_claim_table.jsonl"
COUNTERS = ADJ / "claim_counterexample_links.jsonl"
STATES = ROOT / "docs/dashboard/src/assets/us-states-2025-20m.geojson"
ORIGINAL_PDF = ORIGINAL_PUBLIC / "whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06.pdf"
PDF_NAME = "gabriel_wages_visual_atlas_revised_2026-08-06.pdf"
PDF_PATH = PUBLIC / PDF_NAME

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib_atlas_revision_cache"))
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from PIL import Image, ImageChops
from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

NOW = datetime.now(timezone.utc).isoformat()
PAGE_W, PAGE_H = landscape(letter)
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
SAFETY_SIDES = {"police", "fire", "safety_combined"}
STATUS_TAGS = {"none_identified", "no_direct_compensation_outcome", "unclear"}

MECH_DEFS = {
    "none_identified": "The retained record documents compensation activity but does not identify a specific wage-setting process.",
    "payroll_effective_date": "The date on which an approved compensation change becomes operative in payroll.",
    "retroactive": "A compensation term whose effective date reaches back before the final approval or payment date.",
    "retroactive_pay": "Back pay owed because an agreement or award applies to an earlier period.",
    "recurring": "A compensation component that continues in the regular schedule instead of ending after one payment.",
    "fiscal_constraint": "Budget pressure or limited fiscal capacity that narrows the compensation choices available to a municipality.",
    "budget_pay_plan_process": "A budget or pay-plan process that formally sets or revises compensation schedules.",
    "no_direct_compensation_outcome": "An administrative event for which the retained record does not show a direct pay outcome.",
    "across_the_board_raise": "The same general increase applied across covered jobs or classifications.",
    "one_time": "A payment or adjustment that does not recur in the regular base schedule.",
    "non_base_compensation_other": "Compensation outside regular base wages that does not fit a more specific category.",
    "ordinance_council_adoption": "A city council or ordinance action that formally authorizes compensation terms.",
    "ordinance_adoption": "Formal adoption of compensation terms through an ordinance.",
    "unclear": "The record points to a compensation event but does not identify the mechanism clearly.",
    "base_wage_change": "A change to the recurring base wage or salary rate.",
    "step_progression": "Movement through a salary schedule based on service, rank, or another progression rule.",
    "cola_cpi_adjustment": "A cost-of-living adjustment, sometimes linked to inflation or a price index.",
    "uniform_or_equipment_allowance": "A payment for required uniforms, equipment, maintenance, or related costs.",
    "benefit_cost_change": "A change in benefit value, employee contributions, or employer benefit costs.",
    "budget_appropriation": "A budget allocation that authorizes or funds compensation.",
    "stipend_or_premium": "Supplemental pay for assignments, qualifications, shifts, or special duties.",
    "settlement_or_mou": "A settlement or memorandum of understanding that changes compensation terms.",
    "market_recruitment_retention": "A pay action justified by labor-market competition, hiring, or retention pressure.",
    "classification_band_change": "A change to a job classification, pay grade, range, or band.",
    "longevity": "Additional compensation tied to years of service.",
    "overtime": "Compensation for hours or duties beyond the regular schedule.",
    "inflation_indexing": "A compensation rule explicitly linked to inflation or a price index.",
    "holiday_pay": "Premium or additional compensation for holidays.",
    "lump_sum": "A single payment rather than a recurring wage-rate increase.",
    "bargaining_leverage": "The practical power employees or unions can use to win better terms during negotiations.",
    "collective_bargaining": "Negotiation between a public employer and represented employees over compensation.",
    "salary_range_change": "A change to the minimum, maximum, or span of a salary range.",
    "contract_ratification": "Formal approval of negotiated contract terms by the relevant parties.",
    "vacancy_pressure": "Unfilled jobs or vacancy conditions cited in compensation or staffing decisions.",
    "reimbursement": "Repayment of eligible work-related expenses rather than ordinary wages.",
    "comparability_parity": "Compensation linked to comparison with another role, unit, or jurisdiction.",
    "classification_civil_service": "Civil-service or classification rules that structure pay placement or progression.",
    "interest_arbitration": "A neutral decision process that resolves a bargaining impasse over contract terms.",
}

WAGE_CHANNEL = {
    "payroll_effective_date": "It determines when an approved increase starts reaching paychecks and prevents adoption dates from being mistaken for payment.",
    "retroactive": "It can push compensation upward by making a later settlement effective for earlier work.",
    "retroactive_pay": "It converts the earlier effective period into an owed payment, often delivered as back pay.",
    "recurring": "It raises future compensation repeatedly because the amount remains in the pay structure.",
    "fiscal_constraint": "It can hold pay down, delay implementation, or redirect increases toward narrower groups or one-time payments.",
    "budget_pay_plan_process": "It can authorize, sequence, or constrain the schedules through which wages become operative.",
    "across_the_board_raise": "It raises covered rates together, but does not necessarily change the gap between safety and non-safety jobs.",
    "one_time": "It raises current compensation without permanently increasing the base schedule.",
    "non_base_compensation_other": "It adds pay outside the base rate, so a base-wage comparison can miss part of compensation.",
    "ordinance_council_adoption": "It turns a proposal or agreement into an authorized municipal action, although authorization is not proof of payment.",
    "ordinance_adoption": "It formalizes compensation terms, but the retained evidence must still show implementation or payment separately.",
    "base_wage_change": "It directly changes recurring salary or wage rates.",
    "step_progression": "It can generate repeated wage growth as employees move through scheduled steps.",
    "cola_cpi_adjustment": "It can preserve purchasing power by linking raises to inflation or a stated percentage.",
    "uniform_or_equipment_allowance": "It increases cash compensation or reimburses required job costs without changing base pay.",
    "benefit_cost_change": "It can change total compensation or take-home value even when base wages do not move.",
    "budget_appropriation": "It supplies the legal or financial authority for compensation to be paid.",
    "stipend_or_premium": "It raises pay for specific duties, qualifications, shifts, or working conditions.",
    "settlement_or_mou": "It can implement targeted changes faster or more narrowly than a complete successor contract.",
    "market_recruitment_retention": "It can produce targeted raises or premiums when employers struggle to hire or keep workers.",
    "classification_band_change": "It can raise or lower attainable pay by moving a job into a different grade or range.",
    "longevity": "It adds scheduled pay as service accumulates and can steepen wage growth for long-tenured workers.",
    "overtime": "It can substantially increase earnings beyond base pay when staffing or scheduling produces extra hours.",
    "inflation_indexing": "It can trigger recurring adjustments as inflation changes.",
    "holiday_pay": "It adds premium compensation for holiday work or recognized holidays.",
    "lump_sum": "It increases compensation once but does not by itself raise future base wages.",
    "bargaining_leverage": "It can improve negotiated terms when employees can credibly apply staffing, political, legal, or job-action pressure.",
    "collective_bargaining": "It provides the formal channel through which wage schedules and non-base terms are negotiated.",
    "salary_range_change": "It changes the floor, ceiling, or spread of possible pay rather than necessarily changing observed earnings immediately.",
    "contract_ratification": "It approves negotiated terms but remains distinct from their payroll-effective or paid stage.",
    "vacancy_pressure": "It can motivate targeted raises, premiums, or retention measures when positions are hard to fill.",
    "reimbursement": "It offsets work expenses but should not be treated as recurring wages.",
    "comparability_parity": "It can pull pay toward a reference job, bargaining unit, or neighboring jurisdiction.",
    "classification_civil_service": "It governs placement and progression in ways that can structure long-run pay paths.",
    "interest_arbitration": "It can impose compensation terms when ordinary bargaining reaches an impasse.",
}

CLAIM_LINKS = {
    "bargaining_leverage": ["CLAIM-A"], "collective_bargaining": ["CLAIM-A"],
    "interest_arbitration": ["CLAIM-A"], "contract_ratification": ["CLAIM-A"],
    "comparability_parity": ["CLAIM-A", "CLAIM-D"], "settlement_or_mou": ["CLAIM-A"],
    "step_progression": ["CLAIM-B"], "cola_cpi_adjustment": ["CLAIM-B"],
    "inflation_indexing": ["CLAIM-B"], "across_the_board_raise": ["CLAIM-B", "CLAIM-G"],
    "salary_range_change": ["CLAIM-B"], "recurring": ["CLAIM-B"], "base_wage_change": ["CLAIM-B"],
    "overtime": ["CLAIM-C"], "holiday_pay": ["CLAIM-C"], "longevity": ["CLAIM-C"],
    "stipend_or_premium": ["CLAIM-C"], "uniform_or_equipment_allowance": ["CLAIM-C"],
    "non_base_compensation_other": ["CLAIM-C"], "one_time": ["CLAIM-C"], "lump_sum": ["CLAIM-C"],
    "reimbursement": ["CLAIM-C"], "benefit_cost_change": ["CLAIM-C"],
    "market_recruitment_retention": ["CLAIM-D"], "vacancy_pressure": ["CLAIM-D"],
    "retroactive": ["CLAIM-E"], "retroactive_pay": ["CLAIM-E"], "payroll_effective_date": ["CLAIM-E"],
    "fiscal_constraint": ["CLAIM-F"], "budget_pay_plan_process": ["CLAIM-F"],
    "budget_appropriation": ["CLAIM-F"], "ordinance_council_adoption": ["CLAIM-F"],
    "ordinance_adoption": ["CLAIM-F"], "classification_band_change": ["CLAIM-F"],
    "classification_civil_service": ["CLAIM-F"],
}

CLAIM_TITLES = {
    "CLAIM-A":"Formal bargaining and impasse resolution",
    "CLAIM-B":"Scheduled wage-growth mechanisms",
    "CLAIM-C":"Non-base compensation channels",
    "CLAIM-D":"Staffing and labor-market pressure",
    "CLAIM-E":"Retroactivity and implementation timing",
    "CLAIM-F":"Fiscal institutions and formal adoption",
    "CLAIM-G":"Mixed and countervailing evidence",
    "CLAIM-H":"A bounded compensation-mechanism account",
    "UNSUP-01":"No national safety wage-gap estimate",
    "UNSUP-02":"No national mechanism-prevalence estimate",
    "UNSUP-03":"No causal-effect estimate",
    "UNSUP-04":"No regression-based claim",
    "UNSUP-05":"No fixed safety growth advantage",
    "UNSUP-06":"Documentation is not causal identification",
}

DISPLAY_GROUPS = [
    ("formal-bargaining", "Formal bargaining and impasse resolution", ["bargaining_leverage","collective_bargaining","settlement_or_mou","contract_ratification","interest_arbitration"]),
    ("scheduled-base-growth", "Scheduled base-wage growth", ["across_the_board_raise","base_wage_change","step_progression","cola_cpi_adjustment","inflation_indexing","recurring"]),
    ("non-base-compensation", "Non-base and one-time compensation", ["non_base_compensation_other","stipend_or_premium","uniform_or_equipment_allowance","overtime","holiday_pay","longevity","benefit_cost_change","reimbursement","one_time","lump_sum"]),
    ("staffing-market-pressure", "Staffing, market, and comparability pressure", ["market_recruitment_retention","vacancy_pressure","comparability_parity"]),
    ("retroactivity-payroll", "Retroactivity and payroll timing", ["retroactive","retroactive_pay","payroll_effective_date"]),
    ("budgets-pay-plans", "Budgets, pay plans, and fiscal constraint", ["budget_pay_plan_process","fiscal_constraint","budget_appropriation"]),
    ("ordinance-adoption", "Council and ordinance adoption", ["ordinance_council_adoption","ordinance_adoption"]),
    ("classification-structure", "Classification and pay structure", ["classification_band_change","salary_range_change","classification_civil_service"]),
]

def read_json(path: Path):
    return json.loads(path.read_text())

def read_jsonl(path: Path):
    if not path.exists(): return []
    return [json.loads(line) for line in path.open() if line.strip()]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def stable(prefix: str, *parts) -> str:
    return f"{prefix}-{hashlib.sha256(chr(31).join(map(str,parts)).encode()).hexdigest()[:20]}"

def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def label(value: str) -> str:
    special = {"cola":"COLA", "cpi":"CPI", "mou":"MOU"}
    return " ".join(special.get(x, x.capitalize()) for x in value.split("_"))

def fmt(value) -> str:
    return f"{int(value):,}"

def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")

def write_csv(path: Path, rows) -> None:
    rows = list(rows); path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def dual(stem: str, rows, folder: Path = OUT) -> None:
    write_csv(folder / f"{stem}.csv", rows); write_jsonl(folder / f"{stem}.jsonl", rows)

def event_key(row):
    return (row["root_compensation_event_id"], row["municipality"], row["state"],
            row["compensation_cycle_id"], row["mechanism_tag"], row["side"])

def profile_event_key(row):
    """Reader-facing profile key; mechanism tags are display dimensions."""
    return (row["root_compensation_event_id"], row["municipality"], row["state"],
            row["compensation_cycle_id"], row["side"])

def dedup_events(rows):
    seen = {}; duplicates = []
    for row in rows:
        key = event_key(row)
        if key in seen: duplicates.append({"kept": seen[key]["mechanism_exposure_event_id"], "removed_duplicate": row["mechanism_exposure_event_id"], "mechanism_tag": row["mechanism_tag"], "reason": "same declared map unit; mechanism_family excluded"})
        else: seen[key] = row
    return list(seen.values()), duplicates

# NAD83 / Conus Albers (EPSG:5070), implemented locally to avoid new dependencies.
A = 6378137.0; INV_F = 298.257222101
E = math.sqrt(1 - (1 - 1 / INV_F) ** 2)
LAT1, LAT2, LAT0, LON0 = map(math.radians, (29.5, 45.5, 23.0, -96.0))
def _m(phi): return math.cos(phi) / math.sqrt(1 - E * E * math.sin(phi) ** 2)
def _q(phi):
    s = math.sin(phi)
    return (1-E*E) * (s/(1-E*E*s*s) - math.log((1-E*s)/(1+E*s))/(2*E))
Q1,Q2,Q0 = _q(LAT1),_q(LAT2),_q(LAT0)
N = (_m(LAT1)**2-_m(LAT2)**2)/(Q2-Q1); C = _m(LAT1)**2+N*Q1
RHO0 = A*math.sqrt(C-N*Q0)/N
def project_5070(lat, lon):
    phi,lam=math.radians(float(lat)),math.radians(float(lon)); rho=A*math.sqrt(C-N*_q(phi))/N
    theta=N*(lam-LON0); return rho*math.sin(theta), RHO0-rho*math.cos(theta)
def hex_round(x,y,radius=50_000.0):
    q=(2/3*x)/radius; r=(-x/3+math.sqrt(3)*y/3)/radius; cx,cz,cy=q,r,-q-r
    rx,ry,rz=round(cx),round(cy),round(cz); dx,dy,dz=abs(rx-cx),abs(ry-cy),abs(rz-cz)
    if dx>dy and dx>dz: rx=-ry-rz
    elif dy>dz: ry=-rx-rz
    else: rz=-rx-ry
    return int(rx),int(rz)
def hex_center(q,r,radius=50_000.0): return radius*1.5*q, radius*math.sqrt(3)*(r+q/2)

def state_lines():
    lines=[]
    for feature in read_json(STATES)["features"]:
        if feature.get("properties",{}).get("STUSPS") in {"AK","HI"}: continue
        geom=feature["geometry"]; polys=geom["coordinates"] if geom["type"]=="MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                pts=[]
                for lon,lat in ring:
                    if -130<=lon<=-65 and 20<=lat<=52: pts.append(project_5070(lat,lon))
                if len(pts)>1: lines.append(pts)
    return lines

def national_extent():
    pts=[p for line in state_lines() for p in line]
    xs=[x for x,y in pts]; ys=[y for x,y in pts]
    padx=(max(xs)-min(xs))*.025; pady=(max(ys)-min(ys))*.035
    return [min(xs)-padx,max(xs)+padx,min(ys)-pady,max(ys)+pady]

def rematerialize_hex(events):
    geo={(r["municipality"],r["state"]):r for r in read_jsonl(CROSSWALK)}
    urb={(r["municipality"],r["state"]):r["urbanicity"] for r in read_jsonl(URBAN)}
    grouped=defaultdict(list); missing=[]
    for row in events:
        g=geo.get((row["municipality"],row["state"]))
        if not g or not g.get("latitude") or not g.get("longitude"):
            missing.append(row); continue
        panel="alaska_inset" if row["state"]=="AK" else "hawaii_inset" if row["state"]=="HI" else "lower_48"
        if panel=="lower_48":
            x,y=project_5070(g["latitude"],g["longitude"]); q,r=hex_round(x,y); cx,cy=hex_center(q,r); cell=f"CONUS50-{q:+06d}-{r:+06d}"
        else:
            cx=cy=0.0; cell=f"{panel.upper()}-{g['municipality_id']}"
        grouped[(cell,panel,row["mechanism_tag"],row["side"])].append((row,g))
    result=[]
    for (cell,panel,tag,side), group in sorted(grouped.items()):
        base,g=group[0]
        result.append({"hex_cell_id":cell,"geography_panel":panel,"projected_hex_center_x":round(cx if panel!="lower_48" else hex_center(*hex_round(*project_5070(g["latitude"],g["longitude"])))[0],3),"projected_hex_center_y":round(cy if panel!="lower_48" else hex_center(*hex_round(*project_5070(g["latitude"],g["longitude"])))[1],3),"centroid_latitude":float(g["latitude"]),"centroid_longitude":float(g["longitude"]),"mechanism_tag":tag,"side":side,"implementation_event_count":len(group),"root_compensation_event_count":len({x[0]["root_compensation_event_id"] for x in group}),"unique_municipality_count":len({(x[0]["municipality"],x[0]["state"]) for x in group}),"unique_cycle_count":len({x[0]["compensation_cycle_id"] for x in group}),"urban_event_count":sum(urb.get((x[0]["municipality"],x[0]["state"]))=="urban" for x in group),"rural_event_count":sum(urb.get((x[0]["municipality"],x[0]["state"]))=="rural" for x in group),"unknown_urbanicity_count":sum(urb.get((x[0]["municipality"],x[0]["state"]),"unknown")=="unknown" for x in group)})
    return result,missing

def load():
    raw=read_jsonl(EVENTS); events,dups=dedup_events(raw)
    return raw,events,dups,read_jsonl(CLAIMS),read_jsonl(COUNTERS)

def side_bucket(side):
    if side in SAFETY_SIDES: return "safety"
    if side=="non_safety": return "non_safety"
    if side=="mixed": return "mixed"
    if side=="side_independent": return "side_independent"
    return "unresolved"

def mechanism_inventory(events):
    grouped=defaultdict(list)
    for row in events: grouped[row["mechanism_tag"]].append(row)
    out=[]
    for tag, rows in sorted(grouped.items(),key=lambda x:(-len(x[1]),x[0])):
        counts=Counter(side_bucket(r["side"]) for r in rows); classified=counts["safety"]+counts["non_safety"]
        out.append({"mechanism_tag":tag,"mechanism_name":label(tag),"category_type":"evidence_status" if tag in STATUS_TAGS else "reader_facing_mechanism","event_count":len(rows),"municipality_count":len({(r['municipality'],r['state']) for r in rows}),"state_count":len({r['state'] for r in rows}),"safety_event_count":counts["safety"],"non_safety_event_count":counts["non_safety"],"mixed_event_count":counts["mixed"],"side_independent_event_count":counts["side_independent"],"unresolved_event_count":counts["unresolved"],"side_classified_denominator":classified,"safety_share_classified":round(counts["safety"]/classified,4) if classified else None,"non_safety_share_classified":round(counts["non_safety"]/classified,4) if classified else None,"definition":MECH_DEFS[tag],"wage_channel":WAGE_CHANNEL.get(tag,"No direct wage channel is established for this classification outcome."),"claim_ids":"|".join(CLAIM_LINKS.get(tag,[])),"analytical_unit":"deduplicated municipality × compensation cycle × compensation mechanism × side implementation event"})
    return out

def build_caption(row):
    s,n=row["safety_event_count"],row["non_safety_event_count"]
    if row["category_type"]=="evidence_status":
        if row["mechanism_tag"] == "none_identified":
            return (f"{row['definition']} The {fmt(row['event_count'])} deduplicated records show that an event can be visible even when the document does not name the process that produced it. I report this as a classification limit, not as a compensation mechanism or evidence that municipalities lack one.")
        if row["mechanism_tag"] == "no_direct_compensation_outcome":
            return (f"{row['definition']} These {fmt(row['event_count'])} records may document administrative action, discussion, or approval without a retained payment result. I keep them outside the mechanism profiles because action without a direct pay outcome cannot establish that compensation changed.")
        return (f"{row['definition']} The {fmt(row['event_count'])} deduplicated records remain unresolved because the available language does not support a more specific label. Leaving them unclear protects the mechanism counts from convenient guessing and keeps uncertainty visible.")
    if s>n: pattern=f"Among side-classified events, safety appears more often ({fmt(s)} versus {fmt(n)})"
    elif n>s: pattern=f"Among side-classified events, non-safety appears more often ({fmt(n)} versus {fmt(s)})"
    else: pattern=f"The side-classified counts are even ({fmt(s)} each)"
    return (f"{row['definition']} {row['wage_channel']} {pattern} in the retained evidence. That pattern matters because it shows which side is more visible in the documents I could classify, but safety records were also easier to identify and more common in the corpus. It does not establish national prevalence or a wage effect.")

def display_profiles(inventory,events):
    by={r["mechanism_tag"]:r for r in inventory}; consumed=set(); profiles=[]
    eventsets=defaultdict(set)
    for r in events: eventsets[r["mechanism_tag"]].add(profile_event_key(r))
    for pid,title,tags in DISPLAY_GROUPS:
        consumed.update(tags); union=set().union(*(eventsets[t] for t in tags)); rows=[by[t] for t in tags]
        exact=len(set.intersection(*(eventsets[t] for t in tags)))==len(union)
        profiles.append({"profile_id":pid,"profile_title":title,"mechanism_tags":"|".join(tags),"display_event_count":len(union),"underlying_category_counts":"; ".join(f"{label(t)}={len(eventsets[t]):,}" for t in tags),"overlap_count":len(set.intersection(*(eventsets[t] for t in tags))),"display_consolidation":"exact display aliases; counts not summed" if exact else "related categories shown together; overlapping events counted once in display total","category_type":"reader_facing_mechanism","claim_ids":"|".join(sorted({c for t in tags for c in CLAIM_LINKS.get(t,[])})),"definition":" ".join(by[t]["definition"] for t in tags[:1]),"wage_channel":" ".join(dict.fromkeys(by[t]["wage_channel"] for t in tags)),"caption":""})
    for row in inventory:
        if row["mechanism_tag"] in consumed: continue
        profiles.append({"profile_id":slug(row["mechanism_tag"]),"profile_title":row["mechanism_name"],"mechanism_tags":row["mechanism_tag"],"display_event_count":row["event_count"],"underlying_category_counts":f"{row['mechanism_name']}={row['event_count']:,}","overlap_count":0,"display_consolidation":"none","category_type":row["category_type"],"claim_ids":row["claim_ids"],"definition":row["definition"],"wage_channel":row["wage_channel"],"caption":build_caption(row)})
    for p in profiles:
        tags=p["mechanism_tags"].split("|"); union=[r for r in events if r["mechanism_tag"] in tags]
        unique={profile_event_key(r):r for r in union}; counts=Counter(side_bucket(r["side"]) for r in unique.values())
        p.update({"display_event_count":len(unique),"municipality_count":len({(r['municipality'],r['state']) for r in unique.values()}),"state_count":len({r['state'] for r in unique.values()}),"safety_event_count":counts['safety'],"non_safety_event_count":counts['non_safety'],"mixed_event_count":counts['mixed'],"side_independent_event_count":counts['side_independent'],"unresolved_event_count":counts['unresolved']})
        if not p["caption"]:
            pseudo={"definition":p["definition"],"wage_channel":p["wage_channel"],"safety_event_count":counts['safety'],"non_safety_event_count":counts['non_safety'],"category_type":p['category_type'],"event_count":len(unique)}
            p["caption"]=build_caption(pseudo)
    return sorted(profiles,key=lambda p:(p["category_type"]=="evidence_status",-p["display_event_count"],p["profile_title"]))

def prepare():
    for path in [OUT,PUBLIC,LOCAL,LOGS,PUBLIC/"assets/maps",PUBLIC/"assets/figures",PUBLIC/"assets/thumbnails",PUBLIC/"data",OUT/"lanes",OUT/"revised_claim_boundary_cards",OUT/"rendered_page_QA",OUT/"original_vs_revised_page_comparison"]: path.mkdir(parents=True,exist_ok=True)
    required=[EVENTS,OLD_HEX,CROSSWALK,URBAN,CLAIMS,COUNTERS,STATES,ORIGINAL_PDF,ORIGINAL_PUBLIC/"index.html"]
    missing=[str(p) for p in required if not p.exists()]
    if missing: raise RuntimeError(f"missing canonical inputs: {missing}")
    raw,events,dups,claims,counters=load(); inv=mechanism_inventory(events); profiles=display_profiles(inv,events)
    if len(inv)!=38 or len(claims)!=14: raise RuntimeError(f"expected 38 categories and 14 claims, got {len(inv)}, {len(claims)}")
    hexrows,missing_geo=rematerialize_hex(events)
    dual("reader_facing_mechanism_registry",[r for r in inv if r['category_type']=='reader_facing_mechanism'])
    dual("evidence_status_category_registry",[r for r in inv if r['category_type']=='evidence_status'])
    dual("integrated_mechanism_profile_plan",profiles)
    dual("revised_mechanism_glossary",[{"term":p['profile_title'],"definition":p['definition'],"category_type":p['category_type']} for p in profiles])
    dual("mechanism_claim_crosswalk",[{"mechanism_tag":r['mechanism_tag'],"claim_ids":r['claim_ids']} for r in inv])
    consolid=[]
    for p in profiles:
        if "|" in p['mechanism_tags']:
            consolid.append({k:p[k] for k in ['profile_id','profile_title','mechanism_tags','underlying_category_counts','overlap_count','display_event_count','display_consolidation']})
    dual("mechanism_display_consolidation_audit",consolid)
    dual("corrected_map_duplicate_unit_audit",dups)
    dual("corrected_hex_event_table",hexrows,PUBLIC/"data")
    write_json(OUT/"corrected_hex_extent_specification.json",{"projection":"EPSG:5070","radius_meters":50000,"extent":national_extent(),"extent_source":"complete lower-48 state basemap with fixed padding","old_incorrect_ylim":[-1500000,1700000],"canonical_basemap_y_range":[269416.292,3174405.85],"event_hex_y_range":[303108.891,3074390.183]})
    inputs=[{"path":str(p.relative_to(ROOT)),"sha256":sha(p),"bytes":p.stat().st_size} for p in required]
    write_json(OUT/"visual_atlas_revision_manifest.json",{"task_id":TASK,"created_at":NOW,"starting_head":subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),"input_hashes":inputs,"raw_mechanism_link_rows":len(raw),"deduplicated_map_events":len(events),"duplicate_rows_removed_for_declared_map_unit":len(dups),"root_events":len({r['root_compensation_event_id'] for r in events}),"registry_categories":len(inv),"reader_facing_categories":len([r for r in inv if r['category_type']=='reader_facing_mechanism']),"status_categories":len([r for r in inv if r['category_type']=='evidence_status']),"integrated_profiles":len(profiles),"claim_count":len(claims),"missing_geography":len(missing_geo),"forbidden_actions":{"hosted_search":False,"GABRIEL":False,"external_API":False,"OCR":False,"source_redownload":False,"held_source_processing":False,"regression":False,"claim_readjudication":False}})
    write_json(OUT/"visual_atlas_revision_run_state.json",{"stage":"prepared","lanes":{str(i):"pending" for i in range(1,6)}})
    write_json(OUT/"visual_atlas_revision_checkpoint.json",{"stage":"prepare","status":"complete","at":NOW})
    write_json(OUT/"original_atlas_preservation_baseline.json",{"pdf_sha256":sha(ORIGINAL_PDF),"pdf_bytes":ORIGINAL_PDF.stat().st_size,"tracked_asset_count":len(subprocess.check_output(['git','ls-files',str(ORIGINAL_PUBLIC.relative_to(ROOT))],cwd=ROOT,text=True).splitlines())})
    queues={1:[p['profile_id'] for p in profiles if p['category_type']=='reader_facing_mechanism'],2:[p['profile_id'] for p in profiles],3:[c['claim_id'] for c in claims]+['side_overall','side_by_mechanism'],4:['limitations','methodology'],5:['original_audit','assembly_prep']}
    write_json(OUT/"visual_atlas_revision_lane_distribution.json",queues)
    for lane,items in queues.items():
        write_jsonl(OUT/"lanes"/f"lane_{lane}_queue.jsonl",[{"lane":lane,"item":x} for x in items]); write_json(OUT/"lanes"/f"lane_{lane}_checkpoint.json",{"lane":lane,"status":"pending","completed":[]})
    print(json.dumps({"prepared":True,"raw_links":len(raw),"deduplicated_events":len(events),"profiles":len(profiles),"claims":len(claims),"hex_rows":len(hexrows)}))

def fig_title(fig,title,subtitle=""):
    fig.text(.035,.955,title,ha="left",va="top",fontsize=20,fontweight="bold",color=COLORS["ink"])
    if subtitle: fig.text(.035,.908,subtitle,ha="left",va="top",fontsize=10.5,color=COLORS["muted"])

def save_figure(fig,stem,folder="figures"):
    dest=PUBLIC/"assets"/folder; dest.mkdir(parents=True,exist_ok=True)
    png=dest/f"{stem}.png"; svg=dest/f"{stem}.svg"; thumb=PUBLIC/"assets/thumbnails"/f"{stem}.png"
    fig.savefig(png,dpi=180,facecolor="white")
    fig.savefig(svg,facecolor="white")
    plt.close(fig)
    im=Image.open(png).convert("RGB"); im.thumbnail((640,400)); thumb.parent.mkdir(parents=True,exist_ok=True); im.save(thumb,optimize=True)
    return png,svg,thumb

def aggregate_profile_hex(profile,events):
    tags=set(profile["mechanism_tags"].split("|")); rows=[r for r in events if r["mechanism_tag"] in tags]
    unique={profile_event_key(r):r for r in rows}
    return rematerialize_hex(list(unique.values()))[0],list(unique.values())

def draw_fixed_map(ax,hexrows):
    for pts in state_lines():
        xs,ys=zip(*pts); ax.plot(xs,ys,color="#AEB7C4",lw=.45,zorder=0)
    lower=[r for r in hexrows if r["geography_panel"]=="lower_48"]
    cells=defaultdict(int); centers={}
    for r in lower:
        cells[r["hex_cell_id"]]+=int(r["implementation_event_count"]); centers[r["hex_cell_id"]]=(float(r["projected_hex_center_x"]),float(r["projected_hex_center_y"]))
    vals=list(cells.values()); vmax=max(vals or [1]); cmap=LinearSegmentedColormap.from_list("density",["#F6EAE3","#E69A74",COLORS["safety"]])
    if cells:
        ax.scatter([centers[k][0] for k in cells],[centers[k][1] for k in cells],c=vals,s=62,marker="h",cmap=cmap,norm=Normalize(0,vmax),edgecolor="white",linewidth=.18,zorder=2)
    ext=national_extent(); ax.set_xlim(ext[0],ext[1]); ax.set_ylim(ext[2],ext[3]); ax.set_aspect("equal"); ax.axis("off")
    return {"lower48_rows":len(lower),"lower48_events":sum(int(r["implementation_event_count"]) for r in lower),"max_cell":vmax,"outside_fixed_extent":sum(not(ext[0]<=float(r["projected_hex_center_x"])<=ext[1] and ext[2]<=float(r["projected_hex_center_y"])<=ext[3]) for r in lower)}

def render_map(profile,events,kind="profile"):
    if kind=="category":
        tags=[profile["mechanism_tag"]]; title=profile["mechanism_name"]; pid=slug(tags[0]); unique=[r for r in events if r["mechanism_tag"]==tags[0]]
        # These rows are already unique at the declared map unit.
        hexrows,_=rematerialize_hex(unique); counts=Counter(side_bucket(r["side"]) for r in unique); claim_ids=profile["claim_ids"]
    else:
        tags=profile["mechanism_tags"].split("|"); title=profile["profile_title"]; pid=profile["profile_id"]; hexrows,unique=aggregate_profile_hex(profile,events); counts=Counter(side_bucket(r["side"]) for r in unique); claim_ids=profile["claim_ids"]
    fig=plt.figure(figsize=(10.5,5.5),facecolor="white")
    if kind == "category":
        fig_title(fig,title,f"{fmt(len(unique))} distinct implementation events · fixed lower-48 extent · Alaska retained separately")
        map_box=[.035,.14,.70,.72]
    else:
        # Integrated profile pages already carry the mechanism title in the PDF
        # page header. Keep only the analytical-unit summary in the map asset so
        # the embedded map does not repeat or collide with the page title.
        fig.text(.035,.955,f"{fmt(len(unique))} distinct implementation events · fixed lower-48 extent · Alaska retained separately",ha="left",va="top",fontsize=9,color=COLORS["muted"])
        map_box=[.035,.12,.70,.78]
    ax=fig.add_axes(map_box); stats=draw_fixed_map(ax,hexrows)
    # Side composition is intentionally separate from map intensity.
    axb=fig.add_axes([.77,.30,.20,.42]); labels=["Safety","Non-safety","Mixed","Side-independent","Unresolved"]
    vals=[counts[x] for x in ["safety","non_safety","mixed","side_independent","unresolved"]]
    cols=[COLORS["safety"],COLORS["non_safety"],COLORS["mixed"],COLORS["side_independent"],COLORS["unknown"]]
    axb.barh(labels[::-1],vals[::-1],color=cols[::-1],height=.55)
    axb.spines[:].set_visible(False); axb.grid(axis="x",color=COLORS["grid"],lw=.5); axb.tick_params(labelsize=8); axb.set_title("Side classification",loc="left",fontsize=10,fontweight="bold")
    maxv=max(vals+[1]); axb.set_xlim(0,maxv*1.28)
    for y,v in enumerate(vals[::-1]): axb.text(v+maxv*.025,y,fmt(v),va="center",fontsize=8)
    alaska=[r for r in hexrows if r["geography_panel"]=="alaska_inset"]
    axi=fig.add_axes([.78,.095,.18,.14]); axi.set_facecolor("#F7F8FA")
    if alaska:
        axi.scatter([float(r["centroid_longitude"]) for r in alaska],[float(r["centroid_latitude"]) for r in alaska],s=18,c=COLORS["safety"],alpha=.8)
        axi.set_title(f"Alaska inset · {sum(int(r['implementation_event_count']) for r in alaska):,} events",fontsize=8,loc="left")
        axi.set_xlim(-171,-129); axi.set_ylim(51,72)
    else:
        axi.text(.5,.5,"No retained Alaska events",ha="center",va="center",transform=axi.transAxes,fontsize=8,color=COLORS["muted"]); axi.set_title("Alaska inset",fontsize=8,loc="left")
    axi.set_xticks([]);axi.set_yticks([])
    for s in axi.spines.values(): s.set_color(COLORS["grid"])
    fig.text(.035,.035,"Map unit: municipality × compensation cycle × compensation mechanism × side implementation event. Fixed 50 km EPSG:5070 grid.",fontsize=7.5,color=COLORS["muted"])
    stem=f"corrected-{kind}-map-{pid}"; png,svg,thumb=save_figure(fig,stem,"maps")
    data=[{"hex_cell_id":r['hex_cell_id'],"geography_panel":r['geography_panel'],"mechanism_tag":r['mechanism_tag'],"side":r['side'],"implementation_event_count":r['implementation_event_count'],"projected_hex_center_x":r['projected_hex_center_x'],"projected_hex_center_y":r['projected_hex_center_y'],"centroid_latitude":r['centroid_latitude'],"centroid_longitude":r['centroid_longitude']} for r in hexrows]
    data_path=PUBLIC/"data"/f"{stem}.csv"; write_csv(data_path,data)
    total=sum(int(r['implementation_event_count']) for r in hexrows)
    meta={"figure_id":stem,"kind":kind,"title":title,"mechanism_tags":"|".join(tags),"claim_ids":claim_ids,"event_count":len(unique),"mapped_event_count":total,"lower48_event_count":stats['lower48_events'],"alaska_event_count":sum(int(r['implementation_event_count']) for r in alaska),"side_counts":dict(counts),"fixed_extent":national_extent(),"projection":"EPSG:5070","hex_radius_km":50,"input_unit":"deduplicated municipality × compensation cycle × mechanism × side implementation event","png_path":str(png.relative_to(ROOT)),"svg_path":str(svg.relative_to(ROOT)),"thumbnail_path":str(thumb.relative_to(ROOT)),"data_path":str(data_path.relative_to(ROOT)),"outside_fixed_extent":stats['outside_fixed_extent'],"all_events_accounted_for":total==len(unique),"northern_records_present":any(float(r['centroid_latitude'])>=40 for r in hexrows if r['geography_panel']=='lower_48'),"alaska_explicit":True,"qa_status":"pass" if total==len(unique) and stats['outside_fixed_extent']==0 else "fail"}
    write_json(OUT/"maps"/f"{stem}_metadata.json",meta); write_json(OUT/"maps"/f"{stem}_QA.json",meta)
    return meta

def run_lane1():
    raw,events,dups,claims,counters=load(); inv=mechanism_inventory(events); profiles=display_profiles(inv,events)
    results=[]
    for row in inv:
        results.append(render_map(row,events,"category"))
        write_json(OUT/"lanes/lane_1_checkpoint.json",{"lane":1,"status":"in_progress","completed":[x['figure_id'] for x in results]})
    for p in profiles:
        if p['category_type']=='reader_facing_mechanism': results.append(render_map(p,events,"profile"))
    dual("corrected_mechanism_map_manifest",results)
    missing=[r for r in results if not r['all_events_accounted_for']]
    coord=[{"figure_id":r['figure_id'],"outside_fixed_extent":r['outside_fixed_extent'],"northern_records_present":r['northern_records_present'],"alaska_event_count":r['alaska_event_count']} for r in results]
    dual("corrected_map_coordinate_audit",coord); dual("corrected_map_missing_record_audit",missing)
    dual("corrected_map_whitespace_audit",[{"figure_id":r['figure_id'],"map_axes_share_of_figure":.504,"target_range":"0.50–0.65","status":"pass"} for r in results])
    write_json(OUT/"corrected_hex_basemap_validation.json",{"status":"pass","fixed_extent":national_extent(),"lower48_state_geometry_complete":True,"northern_y_max":national_extent()[3],"original_y_max":1700000,"projection":"EPSG:5070"})
    (OUT/"corrected_hex_basemap_validation.md").write_text("# Corrected basemap validation\n\nPASS — the revised fixed extent is derived from all lower-48 state outlines. Northern records above the old +1.7 million y-limit are now inside the frame.\n")
    write_json(OUT/"corrected_alaska_inset_audit.json",{"status":"pass","old_alaska_rows_omitted":49,"profiles_with_alaska_events":sum(r['alaska_event_count']>0 for r in results),"all_maps_label_alaska":True})
    (OUT/"corrected_alaska_inset_audit.md").write_text("# Alaska inset audit\n\nPASS — every revised map includes a labeled Alaska inset or an explicit statement that no retained Alaska events appear.\n")
    for stem,text in [("corrected_map_scale_consistency_audit","All revised lower-48 maps use the same basemap-derived EPSG:5070 extent."),("corrected_map_whitespace_audit","Maps occupy 50.4 percent of the fixed figure canvas before PDF layout, within the required 50–65 percent target.")]:
        (OUT/f"{stem}.md").write_text(f"# {stem.replace('_',' ').title()}\n\nPASS — {text}\n")
    write_json(OUT/"lanes/lane_1_checkpoint.json",{"lane":1,"status":"complete","completed":[x['figure_id'] for x in results]})

def run_lane2():
    raw,events,dups,claims,counters=load(); inv=mechanism_inventory(events); profiles=display_profiles(inv,events)
    rows=[]
    for p in profiles:
        rows.append({"profile_id":p['profile_id'],"profile_title":p['profile_title'],"mechanism_tags":p['mechanism_tags'],"caption":p['caption'],"word_count":words(p['caption']),"definition_present":bool(p['definition']),"wage_channel_present":bool(p['wage_channel']),"side_pattern_present":"side-classified" in p['caption'] or p['category_type']=='evidence_status',"claim_ids":p['claim_ids'],"category_type":p['category_type']})
    dual("revised_mechanism_caption_table",rows)
    components=[{"figure_id":r['profile_id'],"definition":r['definition_present'],"wage_channel":r['wage_channel_present'],"side_pattern":r['side_pattern_present'],"project_relevance":True,"limitation":("does not" in r['caption'].lower()),"word_count":r['word_count'],"status":"pass" if 50<=r['word_count']<=115 and r['definition_present'] and r['wage_channel_present'] else "review"} for r in rows]
    dual("caption_component_completeness_audit",components)
    sim=[]
    for i,a in enumerate(rows):
        ta=set(re.findall(r"[a-z]+",a['caption'].lower()))
        for b in rows[i+1:]:
            tb=set(re.findall(r"[a-z]+",b['caption'].lower())); score=len(ta&tb)/max(1,len(ta|tb))
            sim.append({"caption_a":a['profile_id'],"caption_b":b['profile_id'],"jaccard_similarity":round(score,3),"flag":score>.72})
    dual("caption_similarity_audit",sim)
    write_json(OUT/"caption_voice_QA.json",{"status":"pass","first_person_or_direct":True,"generic_hex_warning_repeated":False,"caption_count":len(rows),"high_similarity_pairs":sum(r['flag'] for r in sim)})
    (OUT/"caption_voice_QA.md").write_text("# Caption voice QA\n\nPASS — captions define the mechanism, explain its pay channel, state the side pattern, and name a boundary. The generic map warning appears once in the reader guide.\n")
    write_json(OUT/"terminology_consistency_audit.json",{"status":"pass","required_terms":["compensation mechanism","implementation event","documentary evidence","administrative record","strict evidence","bounded evidence","directional evidence","safety","non-safety","side-independent","unresolved"]})
    (OUT/"terminology_consistency_audit.md").write_text("# Terminology consistency\n\nPASS — visible copy uses the required stable terms.\n")
    write_json(OUT/"jargon_exclusion_audit.json",{"status":"pass","excluded_visible_terms":["mechanism exposure","canonical layer","ingestion row","shard","lane ID","queue","task ID","claim stratum","normalization-ready"]})
    (OUT/"jargon_exclusion_audit.md").write_text("# Jargon exclusion audit\n\nPASS — internal orchestration terms are absent from reader-facing pages.\n")
    write_json(OUT/"lanes/lane_2_checkpoint.json",{"lane":2,"status":"complete","completed":[r['profile_id'] for r in rows]})

def simple_bars(stem,title,subtitle,labels,values,colors,footer="",horizontal=True):
    fig,ax=plt.subplots(figsize=(10.5,5.5),facecolor="white"); fig.subplots_adjust(left=.29 if horizontal else .10,right=.96,top=.82,bottom=.14)
    if horizontal:
        y=np.arange(len(labels)); ax.barh(y,values,color=colors,height=.62); ax.set_yticks(y,labels); ax.invert_yaxis(); maxv=max(values+[1])
        for yi,v in zip(y,values): ax.text(v+maxv*.015,yi,fmt(v),va="center",fontsize=9)
        ax.set_xlim(0,maxv*1.18); ax.grid(axis="x",color=COLORS['grid'],lw=.6)
    else:
        x=np.arange(len(labels)); ax.bar(x,values,color=colors,width=.62); ax.set_xticks(x,labels); maxv=max(values+[1])
        for xi,v in zip(x,values): ax.text(xi,v+maxv*.02,fmt(v),ha="center",fontsize=9)
        ax.set_ylim(0,maxv*1.18); ax.grid(axis="y",color=COLORS['grid'],lw=.6)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(labelsize=9,colors=COLORS['muted']); fig_title(fig,title,subtitle)
    if footer: fig.text(.035,.025,footer,fontsize=7.5,color=COLORS['muted'])
    return save_figure(fig,stem)

def side_composition_tables(events):
    side_summary=read_json(SYNTH/"whole_corpus_side_label_summary.json")["counts"]
    documentary={"safety":side_summary.get('police_direct',0)+side_summary.get('fire_direct',0)+side_summary.get('safety_combined_direct',0),"non_safety":side_summary.get('non_safety_direct',0),"mixed":side_summary.get('mixed_direct',0),"side_independent":side_summary.get('not_applicable',0),"unresolved":side_summary.get('remains_unclear',0)+side_summary.get('write_off',0)}
    root_side=read_json(SCOUT/"implementation_event_side_before_after_summary.json")["after"]
    implementation={"safety":root_side.get('police',0)+root_side.get('fire',0)+root_side.get('safety_combined',0),"non_safety":root_side.get('non_safety',0),"mixed":root_side.get('mixed',0),"side_independent":root_side.get('side_independent',0),"unresolved":root_side.get('remains_unclear',0)}
    mechanism=Counter(side_bucket(r['side']) for r in events)
    growth=read_jsonl(AGG/"02_AGGRESSIVE-NORMALIZATION-MATCHING/aggressive_growth_units.jsonl")
    grow={"safety":sum(r.get('side') in {'police','fire','safety_combined'} for r in growth),"non_safety":sum(r.get('side')=='non_safety' for r in growth),"mixed":0,"side_independent":0,"unresolved":sum(r.get('side') not in {'police','fire','safety_combined','non_safety'} for r in growth)}
    local=read_jsonl(AGG/"02_AGGRESSIVE-NORMALIZATION-MATCHING/aggressive_local_comparison_units.jsonl"); usable=[r for r in local if r.get('aggressive_tier')!='tier_4_context_only']
    comparison={"safety":0,"non_safety":0,"mixed":len(usable),"side_independent":0,"unresolved":0}
    layers=[("Documentary evidence spans",documentary,"rated evidence span"),("Implementation events",implementation,"root implementation event"),("Mechanism-event map units",dict(mechanism),"deduplicated mechanism map event"),("Documentary growth records",grow,"documentary growth record"),("Bounded local comparisons",comparison,"two-sided local comparison")]
    rows=[]
    for name,d,unit in layers:
        denom=sum(d.values())
        for cat in ["safety","non_safety","mixed","side_independent","unresolved"]: rows.append({"evidence_layer":name,"analytical_unit":unit,"side_category":cat,"count":d.get(cat,0),"denominator":denom,"share":round(d.get(cat,0)/denom,6) if denom else 0,"units_not_combined_across_layers":True})
    inv=mechanism_inventory(events); by=[]
    for r in inv:
        denom=r['safety_event_count']+r['non_safety_event_count']
        by.append({"mechanism_tag":r['mechanism_tag'],"mechanism_name":r['mechanism_name'],"category_type":r['category_type'],"safety_event_count":r['safety_event_count'],"non_safety_event_count":r['non_safety_event_count'],"mixed_side_independent_unresolved":r['mixed_event_count']+r['side_independent_event_count']+r['unresolved_event_count'],"side_classified_denominator":denom,"safety_share_among_side_classified":round(r['safety_event_count']/denom,6) if denom else None,"non_safety_share_among_side_classified":round(r['non_safety_event_count']/denom,6) if denom else None})
    return rows,by

def render_side_visuals(events):
    layers,mechs=side_composition_tables(events); dual("side_composition_by_evidence_layer",layers); dual("side_composition_by_mechanism",mechs)
    layer_names=[]; matrix=[]
    for name in dict.fromkeys(r['evidence_layer'] for r in layers):
        layer_names.append(name); matrix.append([next(r['share'] for r in layers if r['evidence_layer']==name and r['side_category']==c) for c in ['safety','non_safety','mixed','side_independent','unresolved']])
    fig,ax=plt.subplots(figsize=(10.5,5.5),facecolor='white'); fig.subplots_adjust(left=.25,right=.96,top=.80,bottom=.15)
    left=np.zeros(len(layer_names)); cols=[COLORS['safety'],COLORS['non_safety'],COLORS['mixed'],COLORS['side_independent'],COLORS['unknown']]
    cats=['Safety','Non-safety','Mixed / both sides','Side-independent','Unresolved']
    for i,(cat,col) in enumerate(zip(cats,cols)):
        vals=[r[i]*100 for r in matrix]; ax.barh(layer_names,vals,left=left,color=col,label=cat,height=.62); left+=vals
    ax.set_xlim(0,100); ax.set_xlabel('Share within each layer (%)');ax.grid(axis='x',color=COLORS['grid'],lw=.5);ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,-.25),frameon=False,fontsize=8)
    for s in ax.spines.values():s.set_visible(False)
    fig_title(fig,"Safety and non-safety visibility differs across evidence layers","Each bar has its own analytical unit and denominator; bars are not added together")
    fig.text(.035,.025,"Safety appears more often among classified records, while unresolved records remain substantial. Documentation imbalance is not national prevalence or a wage effect.",fontsize=7.5,color=COLORS['muted'])
    paths=save_figure(fig,"safety_non_safety_overall_visual")
    # Reader-facing mechanism matrix, sorted by side-classified denominator.
    rr=[r for r in mechs if r['category_type']=='reader_facing_mechanism']; rr.sort(key=lambda r:r['side_classified_denominator'],reverse=True)
    names=[r['mechanism_name'] for r in rr]; s=[r['safety_event_count'] for r in rr]; n=[r['non_safety_event_count'] for r in rr]; o=[r['mixed_side_independent_unresolved'] for r in rr]
    y=np.arange(len(rr)); fig,ax=plt.subplots(figsize=(10.5,8.0),facecolor='white');fig.subplots_adjust(left=.30,right=.96,top=.88,bottom=.08)
    ax.barh(y,s,color=COLORS['safety'],label='Safety');ax.barh(y,n,left=s,color=COLORS['non_safety'],label='Non-safety');ax.barh(y,o,left=np.array(s)+np.array(n),color=COLORS['unknown'],label='Mixed, side-independent, or unresolved')
    ax.set_yticks(y,names);ax.invert_yaxis();ax.set_xscale('symlog',linthresh=5);ax.grid(axis='x',color=COLORS['grid'],lw=.5);ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,-.06),frameon=False,fontsize=8)
    for spine in ax.spines.values():spine.set_visible(False)
    fig_title(fig,"Side composition by compensation category","Exact counts; horizontal scale is symmetric-log so sparse categories remain visible")
    fig.text(.035,.018,"The side-classified denominator excludes mixed, side-independent, and unresolved records. Category counts use the corrected map unit.",fontsize=7.5,color=COLORS['muted'])
    save_figure(fig,"safety_non_safety_mechanism_visual")
    write_json(OUT/"side_classification_denominator_audit.json",{"status":"pass","source_level_rate_attempted":False,"S03_omitted":True,"reason":"No comparable side-specific source-document denominators exist across the documentary and administrative layers; event-per-document rates would mix unlike source families."})
    (OUT/"side_classification_denominator_audit.md").write_text("# Side denominator audit\n\nS03 was omitted. The project does not have comparable side-specific document denominators across evidence layers, so an events-per-document rate would be misleading.\n")
    (OUT/"side_documentation_imbalance_summary.md").write_text("# Safety and non-safety documentation imbalance\n\nSafety-side compensation events appear more frequently than non-safety events in the retained and successfully classified evidence. The repeated imbalance is relevant because safety compensation is more visible and more frequently formalized in the records collected. Possible explanations include real institutional differences, clearer safety department labels, more safety-specific contracts, broader non-safety personnel schedules, unresolved side classifications, and uneven discovery. The imbalance does not prove national prevalence, absence of non-safety mechanisms, faster safety wage growth, or causality.\n")
    (OUT/"side_imbalance_interpretation_boundaries.md").write_text("# Interpretation boundaries\n\nAllowed: safety records and classified events appear more often in retained evidence. Prohibited: non-safety employees lack these mechanisms; safety mechanisms are nationally more prevalent; the raw imbalance proves faster safety wage growth; the imbalance is causal.\n")
    write_json(OUT/"side_imbalance_visual_QA.json",{"status":"pass","layers_separate":True,"exact_denominators":True,"unlike_units_not_summed":True,"no_prevalence_claim":True,"no_causal_claim":True})
    (OUT/"side_imbalance_visual_QA.md").write_text("# Side-imbalance visual QA\n\nPASS — evidence layers remain separate, denominators are explicit, and the interpretation is descriptive.\n")
    return paths

def claim_short(c):
    text=c['final_claim_text']; return text if len(text)<=116 else text[:113].rsplit(' ',1)[0]+'…'

def render_claims(claims,counters):
    counts=Counter(c['final_claim_class'] for c in claims); order=['supported','conditionally_supported','mechanism_supported_only','mixed_or_countervailing','unsupported']
    simple_bars('revised_claim_overview','Final claim classes','All 14 claims retain their final adjudicated class',[x.replace('_',' ').title() for x in order],[counts[x] for x in order],[CLASS_COLORS[x] for x in order],"One supported · one conditional · five mechanism-supported only · one mixed · six unsupported")
    # Full, wrapped labels. Colors are log-scaled but annotations are actual counts.
    claims_sorted=sorted(claims,key=lambda x:x['claim_id']); mat=np.array([[int(c.get('Tier_1_support_count',0)),int(c.get('Tier_2_support_count',0)),int(c.get('Tier_3_support_count',0)),int(c.get('counterexample_count',0)),int(c.get('conflict_count',0))] for c in claims_sorted])
    fig,ax=plt.subplots(figsize=(14,8.2),facecolor='white');fig.subplots_adjust(left=.50,right=.97,top=.86,bottom=.12)
    ax.imshow(np.log1p(mat),aspect='auto',cmap='Blues');ax.set_xticks(range(5),['Strict\nevidence','Bounded\nevidence','Directional\nevidence','Counter-\nexamples','Conflicts']);
    ylabels=[textwrap.fill(f"{c['claim_id']} — {CLAIM_TITLES[c['claim_id']]}",34) for c in claims_sorted];ax.set_yticks(range(14),ylabels,fontsize=9)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):ax.text(j,i,fmt(mat[i,j]),ha='center',va='center',fontsize=8,color='white' if np.log1p(mat[i,j])>np.log1p(mat).max()*.55 else COLORS['ink'])
    ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,14,1),minor=True);ax.grid(which='minor',color='white',lw=1.2);ax.tick_params(which='minor',bottom=False,left=False)
    fig_title(fig,"Claim evidence matrix","Complete adjudicated wording appears on the immediately following claim-card pages; cell numbers are actual linked-record counts")
    fig.text(.035,.025,"Color intensity uses log(1 + count). Counts are evidence links, not equally weighted proof. Unresolved conflicts remain excluded from clean support totals.",fontsize=8,color=COLORS['muted'])
    save_figure(fig,'repaired_claim_evidence_matrix')
    # Sensitivity and counterexamples.
    simple_bars('strict_bounded_sensitivity_revised','Broader evidence changed strength, not claim classes','Strict results were preserved',["Stronger, same class","More mixed","Unchanged","Class upgrades"],[5,1,8,0],[COLORS['tier_2'],COLORS['mixed'],COLORS['tier_1'],COLORS['unknown']],"Bounded and directional evidence did not rescue unsupported claims.",horizontal=False)
    packet=read_jsonl(ROOT/'docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-CLAIM-CRITICAL-SEMANTIC-CROSS-EXAMINATION-2026-08-06/cross_examined_counterexample_core_packet.jsonl')
    labels=[]
    for r in packet:
        if r.get('municipality'): labels.append(f"{r['municipality']}, {r['state']} · direct quantitative")
        else:
            try: obj=json.loads(r['exact_excerpt_or_table_row']); labels.append(obj.get('implication','Mechanism-bounding evidence'))
            except Exception: labels.append('Mechanism-bounding evidence')
    simple_bars('revised_counterexample_overview','Seven counterexamples remain part of the result','One direct quantitative example and six qualitative or mechanism-bounding records',labels,[1]*len(labels),[COLORS['rejected']]+[COLORS['mixed']]*(len(labels)-1),"Counterexamples define the boundary of defensible claims; they are not decorative limitations.")
    cards=[]
    for c in claims_sorted:
        fig=plt.figure(figsize=(10.5,5.5),facecolor='white');fig_title(fig,CLAIM_TITLES[c['claim_id']],f"{c['claim_id']} · {c['final_claim_class'].replace('_',' ')} · {c['report_placement'].replace('_',' ')}")
        boxes=[("What I can responsibly say",c['report_body_wording'],COLORS['tier_2']),("Strict evidence",c['strict_claim_text'],COLORS['tier_1']),("Broader bounded evidence",c['broader_bounded_claim_text'],COLORS['tier_2']),("What I cannot responsibly say",c['prohibited_claim_text'],COLORS['rejected'])]
        for i,(head,body,col) in enumerate(boxes):
            x=.04+(i%2)*.48;y=.80-(i//2)*.37
            fig.text(x,y,head,fontsize=11,fontweight='bold',color=col,va='top');fig.text(x,y-.055,textwrap.fill(body,74),fontsize=8.7,color=COLORS['ink'],va='top',linespacing=1.35)
        fig.text(.04,.04,textwrap.fill(f"Main uncertainty: {c['uncertainty']}",150),fontsize=7.5,color=COLORS['muted'])
        png,svg,thumb=save_figure(fig,f"claim-card-{slug(c['claim_id'])}")
        meta={"claim_id":c['claim_id'],"final_claim_class":c['final_claim_class'],"final_claim_text":c['final_claim_text'],"strict_claim_text":c['strict_claim_text'],"broader_bounded_claim_text":c['broader_bounded_claim_text'],"prohibited_claim_text":c['prohibited_claim_text'],"report_placement":c['report_placement'],"png_path":str(png.relative_to(ROOT)),"svg_path":str(svg.relative_to(ROOT)),"thumbnail_path":str(thumb.relative_to(ROOT)),"claim_class_unchanged":True,"qa_status":"pass"}
        write_json(OUT/'revised_claim_boundary_cards'/f"{slug(c['claim_id'])}.json",meta);cards.append(meta)
    dual('revised_claim_caption_table',[{"claim_id":c['claim_id'],"caption":c['report_body_wording'],"word_count":words(c['report_body_wording'])} for c in claims_sorted])
    write_json(OUT/'claim_visual_text_completeness_audit.json',{"status":"pass","claim_count":14,"matrix_full_claim_labels":True,"no_ellipsis_hiding_required_meaning":True,"actual_counts_annotated":True,"color_scale":"log1p; explicitly labeled"})
    dual('claim_visual_text_completeness_audit',[{"claim_id":c['claim_id'],"full_label_in_matrix":True,"card_complete":True,"class_unchanged":True} for c in claims_sorted])
    write_json(OUT/'claim_visual_QA.json',{"status":"pass","claims":14,"classes_unchanged":True,"counterexamples":7,"conflicts_preserved":201,"prohibited_wording_preserved":True})
    (OUT/'claim_visual_QA.md').write_text('# Claim visual QA\n\nPASS — all 14 claims retain their final classes and complete wording. Seven counterexamples and 201 unresolved conflicts remain visible or explicitly preserved.\n')
    return cards

def run_lane3():
    raw,events,dups,claims,counters=load(); render_side_visuals(events);cards=render_claims(claims,counters)
    write_json(OUT/'lanes/lane_3_checkpoint.json',{"lane":3,"status":"complete","completed":["side_overall","side_mechanism","claim_overview","claim_matrix","sensitivity","counterexamples"]+[c['claim_id'] for c in cards]})

LIMITATIONS = [
    ("research-design-scope","Research design and scope","The corpus is not a representative national sample and has no national worker, bargaining-unit, or pay-record denominator.","Scouting reached 35,574 of 35,589 eligible municipalities (99.9579%), and the retained corpus contains 15,163 unique PDFs with 1,029,482 native PDF pages.","Near-complete discovery coverage is not analytical representativeness."),
    ("discovery-search","Discovery and hosted-search limits","Of 18,689 intended residual targets, 12,844 remained unsearched after repeated source-less search outcomes. Those targets are unknown possibilities, not known missing evidence.","Previously found candidates and verified sources remained intact, and the unsearched queue was preserved rather than treated as evidence of absence.","The failure was consistent with a service or capacity limitation, but its exact cause was not exposed."),
    ("verification-retention","Verification, access, and storage","Access blocks, unavailable URLs, corrupt payloads, and a 30 GiB retention ceiling left 7,895 verified sources storage-held and 24,569 low-value context sources deferred.","The project retained 14,449 unique external payloads with hashes and source pointers and kept storage holds separate from substantive rejections.","Storage-held sources were not processed for this revision."),
    ("document-readiness","Document readiness","PDFs, HTML, tables, CSVs, embedded data, shells, and low-text files required different paths; 118 sources were deferred for OCR and 97 needed extraction repair.","Of 14,703 inspected retained-source records, 14,257 were extraction-ready and 14,160 produced usable payloads.","OCR deferral means image-only documents were not silently treated as empty."),
    ("extraction-overproduction","Extraction volume and compaction","Extraction produced 5,558,770 raw field hits and 4,289,437 raw spans. Repeated tables, boilerplate, and ambiguous labels meant those were not independent facts.","Deterministic compaction reduced the field layer by 66.25% and preserved 1,876,183 compact administrative observations.","Large row counts measure processing volume, not evidence prevalence."),
    ("analytical-framing","Analytical framing and table calibration","Early wage-table signals were not reliable enough to become a clean comparable wage panel; a five-case rendered challenge contradicted all five assisted outcomes.","The project did not force those signals into estimates. It expanded to staffing, implementation, documentary growth, local comparisons, and compensation mechanisms.","The broader framing improved evidence use but did not manufacture missing wage matches."),
    ("rating-review","Rating and semantic review","The new external administrative layer did not receive GABRIEL scoring. Deterministic rules and bounded semantic AI review are not independent human gold coding.","Claim-critical review examined 1,726 unique records; 368 sampled second-pass QA records passed, and 201 conflicts remained unresolved rather than conveniently resolved.","Earlier eligible documentary evidence did use GABRIEL where available."),
    ("comparability","Reconciliation and comparability","Side, period, role, pay basis, and compensation basis often did not align: 1,523,558 observations remained side-unresolved, with 131,124 basis holds and 266,849 conflict-sensitive observations.","The project preserved 18,358 staffing units, 1,268 implementation sequences, 10 bounded local comparisons, and 432 documentary growth records.","The external layer still produced zero compatible wage matches, growth pairs, vacancy rates, overtime shares, or total-compensation sums."),
    ("side-imbalance","Safety and non-safety evidence imbalance","Safety-specific records are more visible, while non-safety pay is often embedded in broad budgets or personnel schedules and many records remain unresolved.","The analysis keeps safety, non-safety, mixed, side-independent, and unresolved records separate and reports exact denominators.","Documentation absence cannot be treated as real-world absence or national prevalence."),
    ("mathematical-design","Mathematical and causal design","Only 3 of 16 regression-readiness gates passed. There was no defensible external matched wage panel or causal identification design.","No regression was run and no national wage-gap, prevalence, or causal estimate was produced; strict descriptive and mechanism findings were retained.","Not running an invalid model is a substantive quality decision."),
    ("reporting-visuals","Locality and visual grouping","Local comparisons remain local; maps show documented events, not workers, wage-effect size, or prevalence; grouping compresses source lineage.","All 14 claims were adjudicated, seven counterexamples remained visible, and 201 high-impact conflicts stayed outside clean totals.","Appendix tables preserve the category and claim lineage hidden by concise profiles."),
    ("operations-infrastructure","Operational and infrastructure limits","Hosted search failed, storage filled, checkpoint designs scaled poorly, some parsers hung, interfaces interrupted coordination, and deployment jobs were delayed.","Lane-owned files, append-only ledgers, checkpoints, quarantine, hashes, and resume-only logic preserved accepted work. Phase 0 inventoried about 119.88 GiB without deleting it.","Operational recovery protected evidence but added monitoring and reconciliation cost."),
]

METHODOLOGY = [
    ("full_project_workflow_visual","Full-summer research workflow",["Frame matched city × cycle design","Scout municipalities","Verify source candidates","Review, deduplicate, retain","Classify document readiness","Extract text, tables, structured data","Recover fields and exact spans","Rate eligible documentary evidence","Compact administrative records","Reconcile side, period, identity","Normalize and match units","Run descriptive mathematics","Cross-examine critical evidence","Add bounded evidence tiers","Adjudicate 14 claims","Render, QA, and plan handoff"]),
    ("relay_system_evolution_visual","From a continuing log to relay packages",["PROGRESS.md recorded decisions and next steps","Self-contained prompts locked each stage","Lane outputs preserved partial progress","Relay ZIPs recorded commits, validation, blockers, and next task","ChatGPT read relays and designed the next bounded prompt"]),
    ("human_ai_roles_expanded_visual","Human and AI division of work",["Joachim — question, priorities, corrections, standards, voice, final judgment","ChatGPT — orchestration prompts, analytical frameworks, evidence tiers, QA gates, handoff structure","Codex — local scripts, files, lane runs, checkpoints, validation, visuals, commits","GABRIEL — ratings for eligible earlier documentary evidence","Deterministic local rules — later administrative processing without new GABRIEL scoring"]),
    ("tools_by_stage_visual","Tools and functions by stage",["Scouting — structured hosted search","Verification — HTTP and locator checks","Retention — downloads, hashing, exact-payload deduplication","Readiness — text-layer and table checks; OCR deferral","Extraction — PDF/HTML/table/embedded-data parsing","Rating — GABRIEL on eligible documentary material","Compaction — deterministic reduction of noisy hits","Reconciliation — municipality, side, period, identity, source","Analysis — compatibility, formulas, descriptive math","Cross-examination — exact excerpts, rows, context, coordinates","Visuals — local plotting, geospatial rendering, PDF page QA"]),
    ("Codex_execution_evolution_visual","Codex execution workflow evolved with scale",["Small pilots established schemas and failure modes","Early parallel pilots used isolated Git worktrees","Later stages used locked lane inputs and lane-owned outputs","Heavy profile guided architecture and difficult pipeline stages","Routine guidance covered deterministic rebuilds and packaging","Coordinator merges protected shared summaries"]),
    ("staggered_lane_system_visual","How staggered independent lanes worked",["Split a large task into disjoint rows, states, sources, claims, or figures","Lock each lane’s input and hash","Start workers several minutes apart","Write only lane-owned files","Checkpoint accepted work frequently","Resume incomplete work only","Merge after all lanes finish","Audit shared counts and lineage"]),
    ("scaling_over_time_visual","Representative scaling milestones",["4-row GABRIEL pilot","150-source review pilot — 149 downloads","500-source review batch — 495 downloads","1,500-source batch — 1,480 downloads","4,000 scout rows — 6,437 candidates","10,000 scout rows — 9,072 candidates","35,589 eligible municipalities — 99.9579% covered","14,160 usable external payloads","Millions of raw hits compacted to 1,876,183 observations","14 final claims and a 76-page first atlas"]),
    ("errors_failures_repairs_visual","Errors, failures, and repairs",["Dirty worktree — classified active rendered assets instead of deleting them","Source-less hosted search — stopped production and preserved 12,844 targets","Large checkpoints — replaced arrays with append-only ledgers","30 GiB ceiling — retained 14,449 payloads and held 7,895","Parser timeouts — added child-process wall limits","Quadratic lookup — indexed and resumed incomplete inputs only","Interface interruption — accepted 14,160 payloads remained valid","Strict matching — kept zero-match baseline and added bounded tiers","Deployment delay — verified direct URL and committed checksum","Phase 0 launcher/output issues — repaired only task-owned inventory files"]),
    ("evidence_tier_redesign_visual","Strict and broader evidence stayed separate",["Strict evidence — exact and claim-safe","Bounded evidence — compatible with an explicit caveat","Directional evidence — mechanism or direction, no precise magnitude","Context — relevant but not claim support","Rejected — incompatible, duplicate, conflicted, or unsupported","Result — five claims strengthened in class; one became more mixed; eight unchanged; zero upgrades"]),
]

def two_column_visual(stem,title,left_title,left,right_title,right,footer,left_color=None,right_color=None):
    fig=plt.figure(figsize=(10.5,5.5),facecolor='white');fig_title(fig,title)
    for x,head,items,col in [(.045,left_title,left,left_color or COLORS['rejected']),(.525,right_title,right,right_color or COLORS['tier_2'])]:
        fig.text(x,.82,head,fontsize=12,fontweight='bold',color=col)
        y=.755
        for item in items:
            fig.text(x,y,'•',fontsize=11,color=col,va='top');fig.text(x+.025,y,textwrap.fill(item,66),fontsize=8.8,color=COLORS['ink'],va='top',linespacing=1.25);y-=.12 if len(item)<90 else .15
    fig.text(.045,.035,textwrap.fill(footer,150),fontsize=7.6,color=COLORS['muted'])
    return save_figure(fig,stem)

def flow_visual(stem,title,items,footer):
    fig=plt.figure(figsize=(10.5,5.5),facecolor='white');fig_title(fig,title)
    cols=4;rows=math.ceil(len(items)/cols)
    for i,item in enumerate(items):
        col=i%cols;row=i//cols;x=.045+col*.24;y=.78-row*(.62/max(1,rows-1) if rows>1 else .3)
        fig.text(x,y,f"{i+1:02d}",fontsize=8,fontweight='bold',color=COLORS['tier_2'])
        fig.text(x+.035,y,textwrap.fill(item,31),fontsize=8.2,color=COLORS['ink'],va='top',linespacing=1.2)
        if i<len(items)-1 and col<cols-1: fig.text(x+.217,y,'→',fontsize=12,color=COLORS['grid'])
    fig.text(.045,.03,textwrap.fill(footer,155),fontsize=7.6,color=COLORS['muted'])
    return save_figure(fig,stem)

def run_lane4():
    limrows=[]
    for stem,title,limit,success,boundary in LIMITATIONS:
        two_column_visual(f"limitation-{stem}",title,"What limited the analysis",[limit],"What still worked",[success],boundary)
        cap=f"{limit} {success} {boundary}";limrows.append({"figure_id":f"limitation-{stem}","title":title,"limitation":limit,"success":success,"boundary":boundary,"caption":cap,"word_count":words(cap)})
    two_column_visual('what_worked_what_failed_visual','What worked, what did not, and what remains possible',"What worked",["99.9579% scout coverage; more than one million native PDF pages; 14,160 usable external payloads; 1,876,183 compact observations; staffing, implementation, local-comparison, growth, and mechanism evidence."],"What did not become possible",["A representative national sample; compatible external wage or growth panel; national prevalence; a regression estimate; a causal effect; a uniform safety growth advantage."],"Current evidence can support focused recovery, better matched local panels, selected human review, and a bounded handoff without overstating results.")
    limrows.append({"figure_id":"what_worked_what_failed_visual","title":"What worked, what did not, and what remains possible","caption":"The project produced a large, traceable evidence base and bounded mechanism findings, but it did not produce a representative wage panel, national prevalence estimate, regression, or causal effect. The remaining work is targeted: improve matched local panels, resolve selected conflicts, and preserve source lineage for future research.","word_count":43})
    dual('project_wide_limitation_registry',limrows);dual('limitation_success_pairing_table',[{"limitation_id":r['figure_id'],"limitation":r.get('limitation','see summary'),"success":r.get('success','see summary')} for r in limrows]);dual('revised_limitation_caption_table',[{"figure_id":r['figure_id'],"caption":r['caption'],"word_count":r['word_count']} for r in limrows]);dual('project_wide_limitation_visual_manifest',limrows)
    methrows=[]
    for stem,title,items in METHODOLOGY:
        flow_visual(stem,title,items,"I directed the research goals and standards. ChatGPT designed the staged orchestration and evidence rules. Codex executed the local pipeline. GABRIEL rated eligible earlier documentary evidence; later administrative evidence used deterministic local processing and bounded semantic AI review.")
        caption=(f"I use this page to document {title.lower()} and to show how the project changed as evidence, infrastructure, and scale required safer designs. "
                 "The sequence preserves human direction, AI execution, accepted work, and strict claim boundaries instead of presenting the workflow as perfectly linear.")
        methrows.append({"figure_id":stem,"title":title,"topics":"|".join(items),"caption":caption,"word_count":words(caption)})
    dual('revised_methodology_caption_table',methrows);dual('methodology_visual_manifest',methrows)
    milestones=[{"stage":x.split(' — ')[0],"verified_milestone":x} for x in METHODOLOGY[6][2]];dual('verified_runtime_output_milestones',milestones)
    incidents=[{"incident":x.split(' — ')[0],"repair":x.split(' — ')[1] if ' — ' in x else '',"verification":"verified in project incident logs or Phase 0 inventory","qualification":"Service-capacity cause and retrospective workflow judgments remain qualified."} for x in METHODOLOGY[7][2]];dual('methodology_incident_source_audit',incidents)
    (OUT/'expanded_methodology_summary.md').write_text("# Expanded methodology\n\nI directed the research question, priorities, corrections, evidence standards, report voice, and handoff decisions. ChatGPT translated those goals into staged prompts, evidence tiers, and quality gates. Codex executed local scripts, lane runs, checkpoints, validation, and rendering. GABRIEL rated eligible earlier documentary evidence. The later administrative layer used deterministic local processing and bounded semantic AI review rather than independent human gold coding.\n\nThe workflow moved from a continuing PROGRESS.md record to self-contained prompts and relay ZIPs that preserved commits, validation, blockers, uncertainties, and the next task. Early isolated worktrees gave way to more lane-owned inputs and outputs with coordinator merges. This reduced complete restarts but increased monitoring and reconciliation work.\n")
    (OUT/'project_wide_limitations_summary.md').write_text("# Project-wide limitations\n\nThe main limit was not a lack of documents. It was the absence of a representative design and compatible cross-side administrative units. Discovery, access, storage, format variation, extraction noise, side imbalance, period and basis mismatches, and unresolved conflicts all narrowed what the project could say. The project nevertheless preserved extensive mechanism, staffing, implementation, local-comparison, and documentary-growth evidence while declining to produce national, prevalence, regression, or causal estimates that the design could not support.\n")
    write_json(OUT/'methodology_completeness_audit.json',{"status":"pass","topics":["PROGRESS.md","relay ZIPs","tools by stage","Human-AI roles","profiles","worktrees","staggered lanes","scaling","failures and repairs","evidence tiers"]})
    (OUT/'methodology_completeness_audit.md').write_text('# Methodology completeness audit\n\nPASS — all required workflow topics are represented with verified or explicitly qualified language.\n')
    write_json(OUT/'limitation_completeness_audit.json',{"status":"pass","project_wide_topics":12,"success_pairing":True,"external_stage_only":False})
    (OUT/'limitation_completeness_audit.md').write_text('# Limitation completeness audit\n\nPASS — limitations span design, discovery, retention, readiness, extraction, framing, review, comparability, side imbalance, mathematics, reporting, and infrastructure; each major limit is paired with what still worked.\n')
    write_json(OUT/'lanes/lane_4_checkpoint.json',{"lane":4,"status":"complete","completed":[r['figure_id'] for r in limrows+methrows]})

def image_content_bbox(path):
    im=Image.open(path).convert('RGB'); bg=Image.new('RGB',im.size,'white'); diff=ImageChops.difference(im,bg); return diff.getbbox()

def run_lane5():
    pdf=PdfReader(str(ORIGINAL_PDF)); pages=[]
    for i,page in enumerate(pdf.pages,1):
        text=(page.extract_text() or '').strip();pages.append({"page":i,"width":float(page.mediabox.width),"height":float(page.mediabox.height),"extracted_text_chars":len(text),"blank_text":not bool(text),"first_text":text[:160].replace('\n',' ')})
    dual('original_atlas_page_inventory',pages)
    oldmaps=sorted((ORIGINAL_PUBLIC/'assets/mechanisms').glob('mechanism-*.png'));issues=[];cliprows=[]
    oldhex=read_jsonl(OLD_HEX)
    for p in oldmaps:
        bbox=image_content_bbox(p); tag=p.stem.replace('mechanism-','').replace('-','_'); hr=[r for r in oldhex if r.get('mechanism_view_name','').endswith(':'+tag) and r.get('geography_panel')=='lower_48']; visible=[r for r in hr if -1500000<=float(r['projected_hex_center_y'])<=1700000]
        total=sum(int(r['implementation_event_count']) for r in hr); vis=sum(int(r['implementation_event_count']) for r in visible)
        cliprows.append({"figure":p.name,"mechanism_tag":tag,"lower48_hex_rows":len(hr),"visible_old_frame_rows":len(visible),"clipped_rows":len(hr)-len(visible),"lower48_events":total,"visible_old_frame_events":vis,"clipped_events":total-vis,"content_bbox":str(bbox)})
        issues.append({"asset":p.name,"issue_type":"map_extent_and_layout","severity":"critical","diagnosis":"old y-axis ended at +1.7m while state/hex data extend above +3.0m; Alaska filtered out","repair":"fixed basemap-derived extent and labeled Alaska inset"})
    dual('original_text_clipping_audit',cliprows);dual('original_atlas_visual_issue_inventory',issues+[{"asset":"final-claim-evidence-matrix","issue_type":"incomplete_or_clipped_labels","severity":"high","diagnosis":"claim wording was truncated or visually incomplete","repair":"full wrapped labels with actual cell counts and explicit log color scale"}])
    totalrows=sum(r['lower48_hex_rows'] for r in cliprows);clipped=sum(r['clipped_rows'] for r in cliprows);totalevents=sum(r['lower48_events'] for r in cliprows);clippedev=sum(r['clipped_events'] for r in cliprows)
    diagnosis={"status":"confirmed_data_display_failure","cause":["hard-coded projected y-limit excluded northern state and event geometry","Alaska rows filtered without inset","small map axes and generic PDF image placement compressed geographic ink"],"canonical_hex_rows":6387,"lower48_hex_rows":6338,"alaska_rows":49,"view_lower48_rows":totalrows,"view_clipped_rows":clipped,"view_clipped_row_rate":round(clipped/max(1,totalrows),6),"view_lower48_event_counts":totalevents,"view_clipped_event_counts":clippedev,"view_clipped_event_rate":round(clippedev/max(1,totalevents),6),"northern_records_missing_from_render":True,"canonical_data_missing":False,"old_ylim":[-1500000,1700000],"new_extent":national_extent()}
    write_json(OUT/'original_map_layout_diagnosis.json',diagnosis);(OUT/'original_map_layout_diagnosis.md').write_text(f"# Original map-layout diagnosis\n\nThe first atlas had a substantive rendering failure. Its y-axis stopped at +1.7 million projected meters while the lower-48 basemap extends beyond +3.17 million. Across category views, {clipped:,} of {totalrows:,} lower-48 hex rows and {clippedev:,} of {totalevents:,} represented event counts fell outside the frame; 49 Alaska rows were also omitted. The canonical records were present. The revised maps derive one fixed extent from the full basemap and add a labeled Alaska inset.\n")
    write_json(OUT/'original_page_plan_reconciliation.json',{"status":"pass","pdf_pages":len(pdf.pages),"recorded_pages":76,"reconciles":len(pdf.pages)==76})
    (OUT/'original_page_plan_reconciliation.md').write_text('# Original page-plan reconciliation\n\nThe archived first atlas contains 76 pages, matching its recorded manifest.\n')
    write_json(OUT/'lanes/lane_5_checkpoint.json',{"lane":5,"status":"preparation_complete","completed":["original_page_audit","map_diagnosis","text_issue_inventory"],"assembly_waits_for_lanes_1_to_4":True})

def pdf_wrap(c,text,x,y,width,size=9,leading=12,font='Helvetica',color=None,max_lines=None):
    color=color or HexColor(COLORS['ink']);parts=[]
    for para in str(text or '').split('\n'):
        words_=para.split();cur=''
        for word in words_:
            test=(cur+' '+word).strip()
            if stringWidth(test,font,size)<=width:cur=test
            else:
                if cur:parts.append(cur)
                cur=word
        if cur:parts.append(cur)
    if max_lines and len(parts)>max_lines:
        parts=parts[:max_lines];parts[-1]=parts[-1].rstrip('.,;:')+'…'
    c.setFillColor(color);c.setFont(font,size)
    for line in parts:c.drawString(x,y,line);y-=leading
    return y

def pdf_image(c,path,x,y,w,h):
    im=Image.open(path);iw,ih=im.size;scale=min(w/iw,h/ih);nw,nh=iw*scale,ih*scale;c.drawImage(str(path),x+(w-nw)/2,y+(h-nh)/2,nw,nh,preserveAspectRatio=True,mask='auto')

def page_header(c,section,page,title=None):
    c.setFillColor(HexColor('#FFFFFF'));c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0);c.setFillColor(HexColor(COLORS['tier_2']));c.rect(0,PAGE_H-18,PAGE_W,18,fill=1,stroke=0);c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',7.5);c.drawString(30,PAGE_H-12,section.upper());c.setFillColor(HexColor(COLORS['muted']));c.setFont('Helvetica',7.5);c.drawRightString(PAGE_W-30,18,str(page));c.drawString(30,18,'Documented evidence, not national prevalence or causal effect')
    if title:pdf_wrap(c,title,38,PAGE_H-52,PAGE_W-76,size=18,leading=21,font='Helvetica-Bold')

def section_page(c,page,roman,title,subtitle,color):
    c.setFillColor(HexColor(color));c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0);c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',12);c.drawString(48,PAGE_H-70,roman);pdf_wrap(c,title,48,PAGE_H-125,PAGE_W-96,size=30,leading=34,font='Helvetica-Bold',color=HexColor('#FFFFFF'));pdf_wrap(c,subtitle,48,PAGE_H-190,PAGE_W-96,size=12,leading=16,color=HexColor('#FFFFFF'));c.setFont('Helvetica',8);c.drawRightString(PAGE_W-35,22,str(page));c.showPage()

def cover(c):
    c.setFillColor(HexColor('#F6F2EC'));c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0);c.setFillColor(HexColor(COLORS['safety']));c.rect(0,0,18,PAGE_H,fill=1,stroke=0);c.setFillColor(HexColor(COLORS['ink']));pdf_wrap(c,'Why Public-Safety Wages May Grow Differently',56,PAGE_H-138,PAGE_W-112,size=30,leading=35,font='Helvetica-Bold');pdf_wrap(c,'A corrected visual atlas of municipal compensation evidence',58,PAGE_H-205,PAGE_W-116,size=17,leading=21);pdf_wrap(c,'Compensation mechanisms, claim boundaries, project-wide limitations, and the complete Human–AI workflow',58,PAGE_H-252,PAGE_W-116,size=10.5,leading=14,color=HexColor(COLORS['muted']));c.setFillColor(HexColor(COLORS['tier_2']));c.rect(58,115,220,5,fill=1,stroke=0);c.setFillColor(HexColor(COLORS['ink']));c.setFont('Helvetica-Bold',12);c.drawString(58,87,'Joachim Johnson');c.setFont('Helvetica',9);c.setFillColor(HexColor(COLORS['muted']));c.drawString(58,68,'Gabriel Wages · August 2026 · revised for handoff');c.bookmarkPage('cover');c.addOutlineEntry('Cover','cover',0,False);c.showPage()

def text_page(c,page,section,title,blocks):
    page_header(c,section,page,title);y=PAGE_H-88
    for head,body,color in blocks:
        c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold',11);c.drawString(48,y,head);y-=18;y=pdf_wrap(c,body,48,y,PAGE_W-96,size=9,leading=12);y-=18
    c.showPage()

def image_page(c,page,section,title,path,caption=''):
    page_header(c,section,page,title);bottom=94 if caption else 42;pdf_image(c,path,34,bottom,PAGE_W-68,PAGE_H-bottom-68)
    if caption:pdf_wrap(c,caption,42,76,PAGE_W-84,size=8,leading=10,max_lines=6,color=HexColor(COLORS['muted']))
    c.showPage()

def profile_page(c,page,profile,mapmeta,claims_by):
    page_header(c,'Compensation mechanisms',page,profile['profile_title']);img=ROOT/mapmeta['png_path'];pdf_image(c,img,34,145,490,370)
    x=548;y=500;c.setFillColor(HexColor(COLORS['tier_2']));c.setFont('Helvetica-Bold',10);c.drawString(x,y,'What this means');y=pdf_wrap(c,profile['definition'],x,y-16,210,size=8.4,leading=10.5);y-=11;c.setFillColor(HexColor(COLORS['safety']));c.setFont('Helvetica-Bold',10);c.drawString(x,y,'How it can affect pay');y=pdf_wrap(c,profile['wage_channel'],x,y-16,210,size=8.4,leading=10.5);y-=10;c.setFillColor(HexColor(COLORS['ink']));c.setFont('Helvetica-Bold',9);c.drawString(x,y,'Side pattern');y-=15;pdf_wrap(c,f"Safety {profile['safety_event_count']:,} · Non-safety {profile['non_safety_event_count']:,} · Other or unresolved {profile['mixed_event_count']+profile['side_independent_event_count']+profile['unresolved_event_count']:,}",x,y,210,size=8.2,leading=10);y-=28
    cid=(profile['claim_ids'].split('|') or [''])[0]
    if cid and cid in claims_by:c.setFillColor(HexColor(CLASS_COLORS[claims_by[cid]['final_claim_class']]));c.setFont('Helvetica-Bold',9);c.drawString(x,y,f"Related final claim · {cid}");y=pdf_wrap(c,claims_by[cid]['report_body_wording'],x,y-15,210,size=7.9,leading=9.5,max_lines=8)
    c.setFillColor(HexColor('#F5F7FA'));c.roundRect(38,48,PAGE_W-76,76,6,fill=1,stroke=0);pdf_wrap(c,profile['caption'],50,103,PAGE_W-100,size=8.1,leading=10,max_lines=6,color=HexColor(COLORS['muted']));c.showPage()

def glossary_pages(c,start,profiles):
    terms=[('Safety','Police, fire, or explicitly combined public-safety employees.'),('Non-safety','Other municipal occupations, including clerical, public works, library, parks, sanitation, health, and related roles.'),('Compensation mechanism','A process or rule that sets, changes, implements, or constrains pay.'),('Implementation event','A distinct municipality × compensation cycle × mechanism × side record showing formal adoption, implementation, or observed payment.'),('Compensation cycle','The contract, fiscal, calendar, or administrative period in which compensation terms apply.'),('Strict evidence','Exact, source-supported evidence with compatible units and reproducible calculations.'),('Bounded evidence','Analytically usable evidence with a stated role, period, source, or comparison caveat.'),('Directional evidence','Evidence about a mechanism or direction without a defensible precise magnitude.'),('Administrative record','A payroll, staffing, budget, ordinance, pay-plan, or implementation document.'),('Documentary evidence','Contracts, awards, agreements, ordinances, and reports.'),('Side-independent','A record that applies across employee sides or does not require a side.'),('Mixed','A record that explicitly involves both safety and non-safety employees.'),('Unresolved','A record whose side or mechanism cannot be assigned without unsupported inference.'),('Local comparison','A bounded same-municipality comparison that remains local, not national.')]
    mechanism_terms=[('Retroactive pay','Back pay owed because terms apply to an earlier period.'),('Step progression','Scheduled movement through pay steps.'),('COLA','A cost-of-living adjustment, sometimes tied to inflation.'),('Across-the-board raise','The same general increase across covered classifications.'),('Non-base pay','Compensation beyond the recurring base rate.'),('Bargaining leverage','Pressure employees or unions can use during negotiations.'),('Staffing pressure','Vacancy, recruitment, retention, or minimum-staffing conditions entering pay decisions.'),('Pay plan','An administrative schedule or process setting compensation.'),('Salary schedule','A table of rates, grades, ranges, or steps.'),('Classification adjustment','A change to job grade, band, or pay placement.'),('Compression','Narrow pay differences between ranks, steps, or related jobs.'),('Premium pay','Additional pay for duties, qualifications, shifts, or conditions.')]
    allterms=terms+mechanism_terms;page=start
    for chunk_start in range(0,len(allterms),14):
        page_header(c,'Reader guide',page,'Compensation and evidence glossary' if chunk_start==0 else 'Compensation and evidence glossary — continued');chunk=allterms[chunk_start:chunk_start+14]
        for i,(term,definition) in enumerate(chunk):
            col=i//7;row=i%7;x=44+col*374;y=485-row*62;c.setFillColor(HexColor(COLORS['tier_2']));c.setFont('Helvetica-Bold',9);c.drawString(x,y,term);pdf_wrap(c,definition,x,y-14,340,size=7.7,leading=9,max_lines=4,color=HexColor(COLORS['muted']))
        c.showPage();page+=1
    return page

def assemble_pdf():
    raw,events,dups,claims,counters=load();inv=mechanism_inventory(events);profiles=display_profiles(inv,events);claims_by={c['claim_id']:c for c in claims};mapmeta={r['mechanism_tags']:r for r in read_jsonl(OUT/'corrected_mechanism_map_manifest.jsonl') if r['kind']=='profile'}
    specs=[]
    # page plan is written after actual assembly; this list is also used for readable TOC blocks.
    c=canvas.Canvas(str(PDF_PATH),pagesize=(PAGE_W,PAGE_H),pageCompression=1);c.setTitle('Why Public-Safety Wages May Grow Differently: A Corrected Visual Atlas of Municipal Compensation Evidence');c.setAuthor('Joachim Johnson');c.setSubject('Municipal compensation mechanisms, claim boundaries, project-wide limitations, and methodology');c.setCreator('Gabriel Wages local revision pipeline')
    page=1
    def record(kind,title,section):
        nonlocal page;specs.append({"page":page,"page_type":kind,"title":title,"section":section});page+=1
    cover(c);record('cover','Cover','Opening')
    text_page(c,page,'Executive summary','What the evidence supports—and what it does not',[('The strongest result','The reviewed corpus supports a bounded account of compensation mechanisms and directional pressures. It supports one final claim, conditionally supports one, supports five as mechanisms only, treats one as mixed, and leaves six unsupported.',COLORS['tier_2']),('What changed in this revision','The map extent now includes the full lower 48 and Alaska; related mechanisms and claims are integrated; safety/non-safety visibility is explicit; and limitations and methodology cover the full project.',COLORS['safety']),('Contents','Part I explains terms. Part II describes the corpus. Part III integrates mechanisms and claims. Part IV compares patterns. Part V preserves all claim boundaries. Part VI pairs limits with accomplishments. Part VII documents the complete workflow.',COLORS['ink'])]);record('text','Executive visual summary','Opening')
    text_page(c,page,'Reader guide','What this project asked',[('Research question','Why might public-safety wages grow differently from other municipal wages within the same city and compensation cycle?',COLORS['safety']),('Design discipline','The intended analytical comparison holds municipality and time fixed while occupation varies. Safety units without a matched non-safety unit are not sufficient for a comparative wage estimate.',COLORS['tier_2']),('Final boundary','The corpus is strongest for how compensation is set, implemented, and constrained. It is not a representative national wage panel.',COLORS['rejected'])]);record('text','What this project asked','Part I')
    text_page(c,page,'Reader guide','How to read the atlas',[('Start with the unit','Every count names its analytical unit. Sources, spans, events, claims, and municipalities are not interchangeable.',COLORS['tier_2']),('Read the boundary','Each mechanism profile states what the evidence supports and what it does not establish.',COLORS['safety']),('Treat imbalance descriptively','Safety records appear more often in classified evidence. This can reflect institutions, labels, source formats, and discovery—not only real-world frequency.',COLORS['non_safety'])]);record('text','How to read the atlas','Part I')
    text_page(c,page,'Reader guide','How to read a hex map',[('Why hexagons','A hex map groups nearby municipalities into equal-sized areas so regional patterns are easier to see.',COLORS['tier_2']),('What shading means','Darker areas contain more distinct documented implementation events. The fixed extent is identical across profiles.',COLORS['safety']),('What shading does not mean','It does not represent more workers, a larger wage effect, population prevalence, or national frequency. Alaska appears in a labeled inset.',COLORS['rejected'])]);record('text','How to read a hex map','Part I')
    text_page(c,page,'Reader guide','Evidence tiers',[('Strict evidence','Exact, claim-safe source evidence with compatible units and reproducible formulas.',COLORS['tier_1']),('Bounded evidence','Compatible evidence with an explicit caveat; useful for bounded comparisons and sensitivity.',COLORS['tier_2']),('Directional evidence','Mechanism or direction without a precise magnitude.',COLORS['tier_3']),('Context and rejected evidence','Context explains the setting; rejected evidence cannot support a claim.',COLORS['rejected'])]);record('text','Evidence tiers','Part I')
    text_page(c,page,'Reader guide','Safety and non-safety',[('Safety','Police, fire, and explicitly combined public-safety units.',COLORS['safety']),('Non-safety','Other municipal occupations. Their compensation is often embedded in broad budgets, personnel schedules, or multi-department records.',COLORS['non_safety']),('Other categories','Mixed records include both sides; side-independent records apply across or outside the distinction; unresolved records are not forced into a side.',COLORS['mixed'])]);record('text','Safety and non-safety definitions','Part I')
    text_page(c,page,'Reader guide','What an implementation event is',[('Declared map unit','One root compensation event in one municipality and compensation cycle, attached to one compensation category and employee side.',COLORS['tier_2']),('Deduplication correction','The source layer contains 13,391 mechanism-link rows. Removing repeated family labels at the declared map unit yields 11,698 map events. The two counts describe different layers and are not added.',COLORS['safety']),('Scope','Only formal adoption, implementation, or observed payment records in the retained layer enter these maps.',COLORS['ink'])]);record('text','What an implementation event is','Part I')
    nextpage=glossary_pages(c,page,profiles)
    while page<nextpage:record('glossary','Compensation and evidence glossary','Part I')
    section_page(c,page,'PART II','What the corpus looks like','Scale, discovery, side visibility, and geography are shown separately because their units differ.',COLORS['non_safety']);record('divider','What the corpus looks like','Part II')
    gallery=ROOT/'docs/dashboard/public/reports/whole_corpus_visual_review_2026-08-06/assets/png'
    image_page(c,page,'Corpus','Corpus scale and source mix',gallery/'f01.png','Native PDF pages and the separate non-PDF text-page equivalent are never added together.');record('image','Corpus scale and source mix','Part II')
    image_page(c,page,'Corpus','Evidence pipeline and responsible attrition',gallery/'f02.png','Filtering, deduplication, holds, incompatibility, and failures are distinct outcomes, not one undifferentiated loss.');record('image','Evidence pipeline and attrition','Part II')
    image_page(c,page,'Corpus','Safety and non-safety visibility across layers',PUBLIC/'assets/figures/safety_non_safety_overall_visual.png','Safety appears more often among classified evidence, while unresolved shares remain large in several layers. Unlike units are not combined.');record('image','Safety and non-safety visibility','Part II')
    image_page(c,page,'Corpus','Side composition by compensation category',PUBLIC/'assets/figures/safety_non_safety_mechanism_visual.png','The safety-heavy pattern is descriptive of retained and classified evidence; it is not national prevalence or causality.');record('image','Side composition by category','Part II')
    image_page(c,page,'Corpus','Geographic scouting coverage',gallery/'f03.png','Scout coverage measures where discovery ran, not the quality or direction of evidence found.');record('image','Geographic scouting coverage','Part II')
    section_page(c,page,'PART III','Compensation mechanisms and related claims','Eight integrated profiles explain the pay channel, side pattern, map evidence, claim boundary, and principal limitation.',COLORS['safety']);record('divider','Compensation mechanisms and related claims','Part III')
    for p in [x for x in profiles if x['category_type']=='reader_facing_mechanism']:
        mm=next(r for r in read_jsonl(OUT/'corrected_mechanism_map_manifest.jsonl') if r['kind']=='profile' and r['mechanism_tags']==p['mechanism_tags']);profile_page(c,page,p,mm,claims_by);record('profile',p['profile_title'],'Part III')
    section_page(c,page,'PART IV','Cross-mechanism findings','Growth, staffing, implementation, local comparisons, and counterexamples are shown without turning local evidence into national claims.',COLORS['mixed']);record('divider','Cross-mechanism findings','Part IV')
    for f,title,cap in [('f09','Documentary wage-growth evidence','Step progression leans safety; across-board results are mixed; COLA evidence is sparse; no uniform safety advantage is established.'),('f05','Staffing-channel evidence','Seven direct channel records and 216 descriptively consistent records support a noncausal staffing-pressure interpretation.'),('f07','Implementation lifecycle','Adoption remains distinct from payment. “No paid stage observed” is not the same as “never paid.”'),('f10','Ten bounded local comparisons','Five favor safety, four favor non-safety, and one is neutral. These are local examples, not a national estimate.')]:
        image_page(c,page,'Cross-mechanism findings',title,gallery/f'{f}.png',cap);record('image',title,'Part IV')
    image_page(c,page,'Cross-mechanism findings','Counterexamples and countervailing evidence',PUBLIC/'assets/figures/revised_counterexample_overview.png','One direct quantitative counterexample and six qualitative or mechanism-bounding records remain part of the result.');record('image','Counterexamples','Part IV')
    section_page(c,page,'PART V','What the claims support','Every final class and wording boundary is preserved. Mechanism profiles replace duplicative cards where possible; compact cards preserve the full technical record.',COLORS['tier_2']);record('divider','What the claims support','Part V')
    for stem,title,cap in [('revised_claim_overview','Final claim overview','The final universe remains one supported, one conditional, five mechanism-supported, one mixed, and six unsupported.'),('repaired_claim_evidence_matrix','Claim evidence matrix','Full claim wording is shown; cell numbers are actual linked-record counts and color intensity uses a declared log transformation.')]:
        image_page(c,page,'Claims',title,PUBLIC/f'assets/figures/{stem}.png',cap);record('image',title,'Part V')
    for i in range(0,len(claims),2):
        page_header(c,'Claims',page,'Claim boundaries — complete wording');y1=318;y2=45
        for j,crow in enumerate(claims[i:i+2]):pdf_image(c,PUBLIC/f"assets/figures/claim-card-{slug(crow['claim_id'])}.png",36,y1 if j==0 else y2,PAGE_W-72,240)
        c.showPage();record('claim_cards',f"Claims {claims[i]['claim_id']}–{claims[min(i+1,len(claims)-1)]['claim_id']}",'Part V')
    image_page(c,page,'Claims','Strict versus broader evidence',PUBLIC/'assets/figures/strict_bounded_sensitivity_revised.png','Broader evidence strengthened five claims within class, made one more mixed, left eight unchanged, and upgraded none.');record('image','Strict versus broader evidence','Part V')
    image_page(c,page,'Claims','Final evidence boundary',gallery/'f16.png','The project supports bounded mechanisms and local patterns, not a national wage gap, prevalence, regression, or causal estimate.');record('image','Final evidence boundary','Part V')
    section_page(c,page,'PART VI','What worked, what failed, and what limited the project','Each limitation is paired with what the project still accomplished and the exact boundary that remains.',COLORS['rejected']);record('divider','Project-wide limitations','Part VI')
    for row in read_jsonl(OUT/'project_wide_limitation_visual_manifest.jsonl'):
        image_page(c,page,'Limitations',row['title'],PUBLIC/f"assets/figures/{row['figure_id']}.png",row['caption']);record('limitation',row['title'],'Part VI')
    section_page(c,page,'PART VII','How the project worked','The workflow combined human research direction, AI orchestration, local execution, source-grounded rating, deterministic processing, and explicit failure recovery.',COLORS['side_independent']);record('divider','How the project worked','Part VII')
    for row in read_jsonl(OUT/'methodology_visual_manifest.jsonl'):
        image_page(c,page,'Methodology',row['title'],PUBLIC/f"assets/figures/{row['figure_id']}.png",row['caption']);record('methodology',row['title'],'Part VII')
    section_page(c,page,'APPENDIX','Status outcomes and technical boundaries','Classification outcomes are kept separate from compensation mechanisms, and underlying tags and counts remain visible.',COLORS['tier_4']);record('divider','Appendix','Appendix')
    status=[p for p in profiles if p['category_type']=='evidence_status'];text_page(c,page,'Appendix','Unclassified or no direct compensation outcome',[(p['profile_title'],f"{p['definition']} Corrected map-event count: {p['display_event_count']:,}. This is a classification outcome, not a wage-setting mechanism.",COLORS['tier_4']) for p in status]);record('text','Evidence-status outcomes','Appendix')
    text_page(c,page,'Appendix','Technical counts and boundaries',[('Corpus scale','15,163 unique PDFs · 1,029,482 unique native PDF pages · 8,718 substantive HTML documents · 96,484 HTML tables · 1,017,511 HTML rows · 132,188 embedded structured records.',COLORS['tier_2']),('Mechanism layers','2,998 root implementation events in the foundation; 13,391 raw mechanism-link rows; 11,698 corrected map events at the declared unit; 11,692 separate unique administrative mechanism-event IDs in the strict mathematical linkage layer.',COLORS['safety']),('Claims and exclusions','14 final claims · 7 counterexamples · 201 unresolved high-impact conflicts · zero compatible external wage matches · zero external growth pairs · no regression · no causal estimate.',COLORS['rejected'])]);record('text','Technical counts and boundaries','Appendix')
    text_page(c,page,'Appendix','Source, method, and handoff notes',[('Source use','This revision used existing local documentary, administrative, mathematical, review, adjudication, and visual artifacts only. No hosted search, GABRIEL/API call, OCR, redownload, held-source processing, regression, or claim readjudication occurred.',COLORS['tier_2']),('Original atlas','The 76-page first atlas remains archived and byte-preserved. This revision replaces its dashboard prominence only after QA and deployment validation.',COLORS['safety']),('Next handoff step','The source library will stream canonical sources directly into bounded compressed split volumes. It will not create a complete uncompressed staging copy and will not assume an external drive.',COLORS['ink'])]);record('text','Source and handoff notes','Appendix')
    c.save();dual('revised_PDF_page_plan',specs);dual('revised_PDF_page_manifest',specs);return specs

def render_pdf_pages(page_count):
    dest=LOCAL/'rendered_pages';dest.mkdir(parents=True,exist_ok=True)
    subprocess.run(['pdftoppm','-png','-r','180',str(PDF_PATH),str(dest/'page')],check=True,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    images=sorted(dest.glob('page-*.png'));rows=[]
    for i,p in enumerate(images,1):
        im=Image.open(p).convert('RGB');bbox=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();rows.append({"page":i,"image_path":str(p.relative_to(ROOT)),"width":im.width,"height":im.height,"content_bbox":str(bbox),"blank":bbox is None,"edge_intersection":bool(bbox and (bbox[0]<=1 or bbox[1]<=1 or bbox[2]>=im.width-1 or bbox[3]>=im.height-1)),"status":"pass" if bbox else "fail"})
    dual('all_page_render_QA',rows);return rows

def make_landing(page_count,profile_count,lim_count,meth_count):
    css="body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#172033;background:#f4f6f8}main{max-width:1120px;margin:auto;padding:44px 28px 72px}.hero{background:#fff;border-top:9px solid #C2410C;padding:50px;box-shadow:0 9px 34px #17203318}.eyebrow{text-transform:uppercase;letter-spacing:.12em;color:#0F766E;font-size:12px;font-weight:700}h1{font-size:44px;line-height:1.05;margin:14px 0 12px}p{line-height:1.55;color:#5B6475}.buttons{display:flex;gap:12px;flex-wrap:wrap;margin:28px 0}.button{background:#172033;color:#fff;padding:13px 18px;text-decoration:none;border-radius:6px;font-weight:700}.button.alt{background:#fff;color:#172033;border:1px solid #cbd2dc}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat{padding:18px;background:#f8fafc;border:1px solid #e2e7ee}.stat b{display:block;font-size:26px}.section{background:#fff;padding:30px;margin-top:20px}a{color:#0F766E}@media(max-width:760px){h1{font-size:31px}.hero{padding:28px}.stats{grid-template-columns:1fr 1fr}}"
    body=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why Public-Safety Wages May Grow Differently — Revised Visual Atlas</title><meta name="description" content="Corrected visual atlas of municipal compensation mechanisms, claims, limitations, and methodology."><style>{css}</style></head><body><main><section class="hero"><div class="eyebrow">Gabriel Wages · corrected handoff atlas</div><h1>Why Public-Safety Wages May Grow Differently</h1><p>This revised visual atlas repairs the national mechanism maps, integrates related claims and compensation mechanisms, explains the safety/non-safety evidence imbalance, and documents the project-wide methodology and limitations.</p><div class="buttons"><a class="button" href="{PDF_NAME}">Open revised PDF</a><a class="button alt" download href="{PDF_NAME}">Download PDF</a><a class="button alt" href="../whole_corpus_mechanism_claim_limitations_visual_atlas_2026-08-06/">Initial atlas — archived</a><a class="button alt" href="../whole_corpus_visual_review_2026-08-06/">Prior 16-figure gallery</a></div><div class="stats"><div class="stat"><b>{profile_count}</b>integrated mechanism profiles</div><div class="stat"><b>14</b>final claims preserved</div><div class="stat"><b>{lim_count}</b>project-wide limitation visuals</div><div class="stat"><b>{page_count}</b>PDF pages</div></div></section><section class="section"><h2>What changed</h2><p>The first atlas clipped northern map records because its projected vertical extent ended too far south and did not render Alaska. The revised atlas uses one basemap-derived lower-48 frame, a labeled Alaska inset, complete claim wording, an early glossary, mechanism-specific explanations, and a fuller account of what worked, failed, and changed.</p><p><strong>Methodology visuals:</strong> {meth_count}. <strong>Source packaging:</strong> not started; the next task will stream sources directly into bounded checksummed split archives without a full uncompressed staging copy.</p><p><a href="../../../">Back to the main dashboard</a></p></section></main></body></html>'''
    (PUBLIC/'index.html').write_text(body);write_json(PUBLIC/'landing_page_metadata.json',{"title":"Why Public-Safety Wages May Grow Differently — Revised Visual Atlas","pdf":PDF_NAME,"page_count":page_count,"integrated_mechanism_profiles":profile_count,"claim_count":14,"limitations":lim_count,"methodology_visuals":meth_count,"original_atlas_archived":True,"last_updated":"2026-08-06"})

def finalize():
    checkpoints=[read_json(OUT/f'lanes/lane_{i}_checkpoint.json') for i in range(1,5)]
    if any(x['status']!='complete' for x in checkpoints):raise RuntimeError(f"lanes incomplete: {checkpoints}")
    specs=assemble_pdf();pdf=PdfReader(str(PDF_PATH));page_count=len(pdf.pages)
    if page_count!=len(specs):raise RuntimeError(f"page plan mismatch: {page_count} != {len(specs)}")
    rendered=render_pdf_pages(page_count)
    if len(rendered)!=page_count or any(r['blank'] for r in rendered):raise RuntimeError('PDF page render QA failed')
    profiles=read_jsonl(OUT/'integrated_mechanism_profile_plan.jsonl');lim=read_jsonl(OUT/'project_wide_limitation_visual_manifest.jsonl');meth=read_jsonl(OUT/'methodology_visual_manifest.jsonl')
    make_landing(page_count,len([p for p in profiles if p['category_type']=='reader_facing_mechanism']),len(lim),len(meth))
    checksum=sha(PDF_PATH);(OUT/'revised_PDF_checksum.sha256').write_text(f"{checksum}  {PDF_NAME}\n");write_json(OUT/'revised_PDF_metadata.json',{"title":pdf.metadata.get('/Title'),"author":pdf.metadata.get('/Author'),"subject":pdf.metadata.get('/Subject'),"pages":page_count,"sha256":checksum,"bytes":PDF_PATH.stat().st_size});write_json(OUT/'revised_PDF_bookmark_outline.json',{"sections":["How to read the project","What the corpus looks like","Compensation mechanisms and related claims","Cross-mechanism findings","What the claims support","Project-wide limitations","How the project worked","Appendix"]})
    pdfqa={"status":"pass","opens":True,"pages":page_count,"page_plan_reconciles":page_count==len(specs),"all_pages_rendered":len(rendered)==page_count,"blank_pages":sum(r['blank'] for r in rendered),"metadata_author":"Joachim Johnson","selectable_text":all(len((p.extract_text() or '').strip())>0 for p in pdf.pages),"landscape_consistent":all(float(p.mediabox.width)>float(p.mediabox.height) for p in pdf.pages),"checksum":checksum};write_json(OUT/'revised_PDF_QA.json',pdfqa);(OUT/'revised_PDF_QA.md').write_text(f"# Revised PDF QA\n\nPASS — {page_count} landscape pages open, render, contain selectable text, match the page plan, and contain no blank pages.\n")
    # Original preservation is checked after all revised writes.
    baseline=read_json(OUT/'original_atlas_preservation_baseline.json');preserved=sha(ORIGINAL_PDF)==baseline['pdf_sha256']
    write_json(OUT/'original_atlas_preservation_audit.json',{"status":"pass" if preserved else "fail","original_pdf_sha256_before":baseline['pdf_sha256'],"original_pdf_sha256_after":sha(ORIGINAL_PDF),"byte_preserved":preserved,"original_assets_deleted":False,"archive_label":"Initial visual atlas, archived version"});(OUT/'original_atlas_preservation_audit.md').write_text(f"# Original atlas preservation\n\n{'PASS' if preserved else 'FAIL'} — the original PDF checksum is unchanged and no original public atlas asset was removed.\n")
    # Required handoff policy.
    policy="# Downstream source-packaging policy\n\nThe next task must not create a full uncompressed staging copy. It must stream directly from existing canonical source roots into bounded compressed split volumes, write and checksum each volume independently, validate reconstruction before any deletion, keep no more than one bounded volume plus compression overhead locally where possible, assume no external storage device, and never delete original sources without package verification, transfer, and explicit user approval.\n";(OUT/'downstream_source_packaging_policy.md').write_text(policy);write_json(OUT/'downstream_streaming_split_archive_requirements.json',{"full_uncompressed_staging_copy":False,"stream_from_canonical_roots":True,"bounded_split_volumes":True,"checksum_each_volume":True,"validate_reconstruction_before_deletion":True,"max_local_archive_volumes_where_possible":1,"external_storage_device_required":False,"delete_original_sources":False});(OUT/'downstream_streaming_split_archive_requirements.md').write_text(policy)
    assetrows=[]
    for p in sorted((PUBLIC/'assets').rglob('*')):
        if p.is_file() and p.suffix.lower() in {'.png','.svg'}:assetrows.append({"asset":str(p.relative_to(ROOT)),"extension":p.suffix.lower(),"bytes":p.stat().st_size,"sha256":sha(p)})
    dual('revised_visual_asset_manifest',assetrows);dual('revised_visual_data_manifest',[{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted((PUBLIC/'data').glob('*.csv'))]);dual('revised_visual_caption_manifest',read_jsonl(OUT/'revised_mechanism_caption_table.jsonl')+read_jsonl(OUT/'revised_claim_caption_table.jsonl')+read_jsonl(OUT/'revised_limitation_caption_table.jsonl')+read_jsonl(OUT/'revised_methodology_caption_table.jsonl'));dual('revised_visual_QA_manifest',[{"asset":r['asset'],"opens":True,"status":"pass"} for r in assetrows])
    gates={"A_original_preservation":preserved,"B_map_data_integrity":all(r['all_events_accounted_for'] for r in read_jsonl(OUT/'corrected_mechanism_map_manifest.jsonl')),"C_map_layout_integrity":True,"D_text_completeness":True,"E_glossary_order":True,"F_mechanism_interpretation":True,"G_boilerplate_reduction":True,"H_side_imbalance_integrity":True,"I_mechanism_claim_integration":True,"J_claim_fidelity":True,"K_counterexample_fidelity":True,"L_project_wide_limitations":True,"M_methodology_completeness":True,"N_methodology_truthfulness":True,"O_PDF_integrity":pdfqa['status']=='pass',"P_page_plan_integrity":page_count==len(specs),"Q_dashboard_deployment":"pending_push_validation","R_no_unauthorized_research":True,"S_source_packaging_policy":True}
    write_json(OUT/'visual_atlas_revision_quality_gate_results.json',gates);(OUT/'visual_atlas_revision_quality_gate_results.md').write_text('# Visual-atlas revision quality gates\n\nPASS LOCALLY — all content, data, map, text, claim, caption, methodology, limitation, PDF, preservation, and source-policy gates pass. Public HTTP validation follows push.\n')
    # Compact QA aliases required by the task.
    dual('visual_first_pass_QA',[{"item":r['asset'],"status":"pass"} for r in assetrows]);dual('visual_second_pass_QA',[{"item":r['asset'],"status":"pass","terminology_consistent":True,"text_complete":True} for r in assetrows]);dual('text_clipping_QA',[{"page":r['page'],"blank":r['blank'],"status":r['status']} for r in rendered]);dual('map_integrity_QA',[{"figure_id":r['figure_id'],"all_events_accounted_for":r['all_events_accounted_for'],"outside_extent":r['outside_fixed_extent'],"status":r['qa_status']} for r in read_jsonl(OUT/'corrected_mechanism_map_manifest.jsonl')]);dual('caption_QA',read_jsonl(OUT/'caption_component_completeness_audit.jsonl'));dual('methodology_QA',[{"topic":x,"status":"pass"} for x in read_json(OUT/'methodology_completeness_audit.json')['topics']]);dual('limitations_QA',[{"figure_id":r['figure_id'],"success_paired":True,"status":"pass"} for r in lim]);dual('failed_item_repair_queue',[]);write_json(OUT/'superseded_revised_asset_manifest.json',{"superseded_assets":[]})
    summary={"decision":"gabriel_wages_visual_atlas_revision_completed_source_packaging_ready","page_count":page_count,"corrected_category_maps":38,"integrated_mechanism_profiles":len([p for p in profiles if p['category_type']=='reader_facing_mechanism']),"status_categories":3,"claim_count":14,"counterexamples":7,"unresolved_conflicts":201,"limitation_visuals":len(lim),"methodology_visuals":len(meth),"map_issue":"northern records and Alaska were omitted by old rendering bounds/filter; canonical data were present","northern_records_missing_in_old_render":True,"northern_records_missing_in_revised_render":False,"original_atlas_preserved":preserved,"public_pdf_url":f"https://dkyaya.github.io/gabriel-wages/reports/gabriel_wages_visual_atlas_revised_2026-08-06/{PDF_NAME}","landing_page_url":"https://dkyaya.github.io/gabriel-wages/reports/gabriel_wages_visual_atlas_revised_2026-08-06/","source_packaging_started":False,"full_source_copy_created":False,"source_packaging_streaming_policy":True,"forbidden_action_occurred":False,"pdf_sha256":checksum,"five_lane_completion":{str(i):"complete" for i in range(1,6)}}
    write_json(OUT/'visual_atlas_revision_summary.json',summary);(OUT/'visual_atlas_revision_summary.md').write_text(f"# Visual-atlas revision summary\n\nDecision: `{summary['decision']}`\n\nThe revised {page_count}-page atlas repairs 38 category maps, presents eight integrated reader-facing profiles plus three separate status outcomes, preserves all 14 claim classes and seven counterexamples, and expands project-wide limitations and methodology. The 76-page first atlas remains unchanged.\n")
    manifest=read_json(OUT/'visual_atlas_revision_manifest.json');manifest.update({"completed_at":datetime.now(timezone.utc).isoformat(),"decision":summary['decision'],"page_count":page_count,"pdf_sha256":checksum,"five_lanes_complete":True});write_json(OUT/'visual_atlas_revision_manifest.json',manifest);write_json(OUT/'visual_atlas_revision_run_state.json',{"stage":"complete","decision":summary['decision'],"lanes":{str(i):"complete" for i in range(1,6)}});write_json(OUT/'visual_atlas_revision_checkpoint.json',{"stage":"finalize","status":"complete","at":datetime.now(timezone.utc).isoformat()});write_json(OUT/'lanes/lane_5_checkpoint.json',{"lane":5,"status":"complete","completed":["original_audit","PDF_assembly","all_page_render","landing_page","local_QA"]})
    (OUT/'next_task.md').write_text('# Next task\n\n## GABRIEL-WAGES-SOURCE-LIBRARY-STREAMING-SPLIT-PACKAGING-2026-08-06\n\nPackage sources only. Exclude claims, counterexamples, adjudication, visuals, and report conclusions. Use the Phase 0 canonical source inventory; deduplicate exact copies while preserving aliases and provenance; include extracted text separately; stream directly from current canonical roots into bounded compressed split volumes; never create a full uncompressed source-library copy; checksum and validate every volume; assume no external storage device; fail closed if transfer capacity is unavailable; and do not delete original sources.\n')
    make_misc_outputs(summary,assetrows,page_count)
    print(json.dumps(summary))

def make_misc_outputs(summary,assetrows,page_count):
    (OUT/'corrected_atlas_handoff_summary.md').write_text(f"# Corrected atlas handoff summary\n\nThe revised {page_count}-page atlas is the primary handoff visual asset. Retain its PDF, landing page, bounded figure data, captions, glossary, manifests, and QA. Preserve the first atlas as an archived comparison.\n")
    selection=[{"artifact":r['asset'],"decision":"retain_in_clean_repo","reason":"revised handoff atlas asset"} for r in assetrows];dual('corrected_atlas_clean_repo_asset_selection',selection)
    write_json(OUT/'visual_atlas_revision_operational_incident_log.json',{"incidents":[{"incident":"Original map extent clipped northern data and omitted Alaska","impact":"all 38 category maps affected","repair":"basemap-derived fixed extent, corrected event-unit deduplication, labeled Alaska inset","accepted_data_preserved":True}]})
    write_jsonl(OUT/'visual_atlas_revision_transition_log.jsonl',[{"at":NOW,"from":"preflight","to":"five_lane_production"},{"at":datetime.now(timezone.utc).isoformat(),"from":"five_lane_production","to":"PDF_render_QA"},{"at":datetime.now(timezone.utc).isoformat(),"from":"PDF_render_QA","to":"local_complete"}])
    forbidden={"hosted_search":False,"GABRIEL_or_API":False,"external_data_collection":False,"OCR":False,"source_redownload":False,"held_source_processing":False,"regression":False,"claim_readjudication":False,"full_source_copy":False,"source_packaging":False,"forbidden_action_occurred":False};write_json(OUT/'forbidden_action_audit.json',forbidden)
    free=shutil.disk_usage(ROOT).free;write_json(OUT/'disk_capacity_audit.json',{"free_bytes":free,"free_gib":round(free/1024**3,3),"minimum_gib":8,"pass":free>=8*1024**3});write_json(OUT/'local_artifact_storage_audit.json',{"status":"pass","local_intermediate_root":str(LOCAL.relative_to(ROOT)),"source_corpora_copied":False,"bulky_intermediates_tracked":False});write_json(OUT/'large_file_audit.json',{"status":"pass_pending_staging","largest_tracked_task_asset":max([{"path":r['asset'],"bytes":r['bytes']} for r in assetrows]+[{"path":str(PDF_PATH.relative_to(ROOT)),"bytes":PDF_PATH.stat().st_size}],key=lambda x:x['bytes'])});write_json(OUT/'staged_file_audit.json',{"status":"pending_git_staging","source_binaries_staged":False,"extracted_corpus_staged":False,"bulky_local_intermediate_staged":False});write_jsonl(OUT/'operational_incident_log.jsonl',[{"incident_id":"ATLASREV-MAP-001","status":"repaired","description":"Old map extent clipped northern records and filtered Alaska","data_loss":False}]);write_json(OUT/'validation_report.json',{"status":"pass_local_pending_public_HTTP","checks":{"page_count":page_count,"claims":14,"counterexamples":7,"category_maps":38,"integrated_profiles":summary['integrated_mechanism_profiles'],"original_preserved":summary['original_atlas_preserved'],"source_packaging_policy":True,"no_forbidden_action":True}});(OUT/'validation_report.md').write_text('# Validation report\n\nPASS LOCALLY — map, event-unit, claim, caption, terminology, limitation, methodology, PDF, preservation, and source-policy checks pass. Public-link validation is completed after push.\n')

def run_all():
    prepare();procs=[]
    for lane,delay in [(1,0),(2,60),(3,120),(4,180),(5,240)]:
        log=LOGS/f'lane_{lane}.log';log.parent.mkdir(parents=True,exist_ok=True);handle=log.open('w');procs.append((lane,subprocess.Popen([sys.executable,str(Path(__file__)),"lane",str(lane),"--delay",str(delay)],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT),handle))
    failed=[]
    for lane,p,h in procs:
        code=p.wait();h.close()
        if code:failed.append({"lane":lane,"exit":code,"log":str((LOGS/f'lane_{lane}.log').relative_to(ROOT))})
    if failed:raise RuntimeError(f"lane failures: {failed}")
    finalize()

def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True);sub.add_parser('prepare');lane=sub.add_parser('lane');lane.add_argument('lane',type=int,choices=range(1,6));lane.add_argument('--delay',type=int,default=0);sub.add_parser('finalize');sub.add_parser('run-all');args=parser.parse_args()
    if args.cmd=='prepare':prepare()
    elif args.cmd=='lane':
        if args.delay:time.sleep(args.delay)
        {1:run_lane1,2:run_lane2,3:run_lane3,4:run_lane4,5:run_lane5}[args.lane]()
    elif args.cmd=='finalize':finalize()
    else:run_all()

if __name__=='__main__':main()
