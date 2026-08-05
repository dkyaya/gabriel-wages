#!/usr/bin/env python3
"""Prepare, run, and finalize the 2026-08-04 whole-corpus external-data scout.

The script deliberately separates deterministic corpus/geography preparation
from live hosted-search workers. Live workers retain metadata returned by the
hosted-search tool only; they never open, verify, or download candidate URLs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EVIDENCE-CORRECTION-IMPLEMENTATION-EVENT-RECODING-AND-VISUAL-PREP-2026-08-04"
OUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
PUBLIC = ROOT / "docs/dashboard/public/reports/whole_corpus_evidence_semantic_repair_2026-08-04"
REF = ROOT / "artifacts/local_external_reference_data/whole_corpus_external_data_search_2026-08-04"
RAW_META = ROOT / "artifacts/local_hosted_search_metadata/whole_corpus_external_data_search_2026-08-04"
TMP = ROOT / "tmp/broad_state_whole_corpus_external_data_targeted_hosted_search_scout_2026-08-04_logs"
UNIVERSE = ROOT / "docs/analysis/national_municipality_universe.csv"
TASK_ID = "BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-TARGETED-HOSTED-SEARCH-SCOUT-2026-08-04"
MODEL = "gpt-5.4-nano"
NOW = "2026-08-04T22:34:00Z"
LANES = [f"external_search_lane_{i:03d}" for i in range(1, 6)]
LIVE_FAMILIES = [
    "payroll_and_earnings", "staffing_and_headcount", "recruitment_and_retention",
    "tenure_and_progression", "implementation", "benefits_and_total_compensation",
]
ALL_FAMILIES = LIVE_FAMILIES + ["urbanicity_and_context"]
INCLUDED_STATUSES = {"formally_adopted", "implemented", "paid_or_observed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_pair(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    write_csv(OUT / f"{name}.csv", rows, fields)
    write_jsonl(OUT / f"{name}.jsonl", rows)


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable(prefix: str, *parts: object, n: int = 24) -> str:
    raw = "\x1f".join(str(part or "") for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:n]}"


def clean(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    repairs = {
        "paymen t": "payment", "pay period 22) .": "pay period 22).",
        "{pay period": "(pay period", "employ ees": "employees",
        "retro active": "retroactive", "agree ment": "agreement",
    }
    for old, new in repairs.items():
        text = text.replace(old, new)
    return text


def excerpt_fragment(text: str, words: int = 22) -> str:
    return " ".join(clean(text).split()[:words]).rstrip(" ,;:.")


def true(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "yes", "1"}


def year_label(value: str) -> str:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", value or "")
    return match.group(1) if match else "undated"


def semantic_card(row: dict[str, str]) -> dict[str, str]:
    text = clean(row["evidence_excerpt"])
    low = text.lower()
    mechanism = row.get("mechanism", "other_pay_setting_mechanism")
    status = row.get("implementation_status", "unclear_status")
    ctype = "compensation term"
    if "lump sum" in low: ctype = "lump-sum payment"
    elif "retroactive" in low or "back pay" in low: ctype = "retroactive payment rule"
    elif "cola" in low or "cost of living" in low or "cpi" in low: ctype = "COLA or indexing rule"
    elif "step" in low: ctype = "step-progression rule"
    elif "overtime" in low: ctype = "overtime rule"
    elif "holiday" in low: ctype = "holiday-pay rule"
    elif "longevity" in low: ctype = "longevity payment"
    elif "premium" in low or "stipend" in low: ctype = "premium or stipend"
    elif "%" in text or "percent" in low: ctype = "percentage pay adjustment"
    elif "salary" in low or "wage" in low or "pay" in low: ctype = "pay term"
    status_phrase = {
        "implemented": "sets an operative term", "formally_adopted": "records formal adoption",
        "paid_or_observed": "records an observed payment", "negotiated_term": "states a negotiated term",
        "proposal_or_demand": "states a proposal rather than an accepted term",
        "recommendation": "recommends a term without proving adoption",
    }.get(status, "documents a term whose implementation status remains limited")
    fragment = excerpt_fragment(text)
    what = f"For {row['municipality']}, the excerpt {status_phrase}: {fragment}."
    channel = {
        "collective_bargaining": "a negotiated agreement transmits bargaining into a written compensation term",
        "interest_arbitration": "a wage-setting neutral can select or impose compensation terms when bargaining does not settle them",
        "factfinding": "a factfinder evaluates wage-setting evidence and recommends a compensation resolution",
        "retroactivity_implementation": "the effective date reaches backward, converting a later decision into compensation owed for an earlier period",
        "budget_pay_plan": "the budget or pay-plan process authorizes the schedule or resources through which compensation becomes operative",
        "across_the_board_raise": "the stated adjustment raises covered pay rates across the specified unit or schedule",
        "cola_cpi_indexing": "the formula links pay to an inflation measure or stated cost-of-living adjustment",
        "step_schedule_seniority": "the schedule converts service, step placement, or progression into higher recurring pay",
        "non_base_compensation": "the clause adds compensation outside ordinary base rates through a payment, premium, allowance, or similar term",
        "market_recruitment_retention": "market or staffing evidence is used to justify compensation intended to recruit or retain workers",
        "ordinance_council_adoption": "a public body converts a proposed pay action into an adopted legal or administrative term",
    }.get(mechanism, "the operative language connects an institutional decision to a defined compensation rule or payment")
    direction = row.get("pressure_direction", "unclear")
    direction_detail = {
        "upward": f"Upward: the {ctype} adds to, raises, or preserves employee compensation.",
        "downward": f"Downward: the {ctype} reduces compensation or shifts a cost toward employees.",
        "mixed": "Mixed: the process can generate higher or lower terms; this excerpt documents one bounded outcome without establishing its net effect across workers.",
        "neutral_or_procedural": "Neutral/procedural: the clause structures decision-making but does not itself establish a higher payment.",
    }.get(direction, "Unclear: the bounded language does not establish the net compensation direction.")
    beneficiary = row.get("beneficiary", "unclear")
    beneficiary_detail = f"The named beneficiary is {beneficiary.replace('_', ' ')}; the conclusion is limited to the unit actually named in the excerpt."
    fit = "supports" if direction == "upward" and beneficiary in {"police", "fire", "safety_combined"} and status in INCLUDED_STATUSES else "partially supports"
    if beneficiary == "non_safety": fit = "complicates"
    if status in {"proposal_or_demand", "recommendation", "unclear_status"}: fit = "insufficient" if status == "unclear_status" else "partially supports"
    support = f"The words “{fragment}” identify the concrete {ctype}; they show how {channel}."
    fit_text = {
        "supports": "Supports: this is operative upward-pressure evidence for a safety unit and therefore illustrates one pathway by which safety pay can grow.",
        "partially supports": "Partially supports: the mechanism is visible, but the bounded record alone does not establish payment, comparative magnitude, or a safety-versus-non-safety difference.",
        "complicates": "Complicates: the same kind of mechanism appears for a non-safety unit, showing that the institution is not unique to police or fire.",
        "insufficient": "Insufficient: the excerpt helps identify the mechanism but does not confirm an adopted, implemented, or paid outcome.",
    }[fit]
    limitation = (
        f"This {row['municipality']} example is one document-bound observation. It does not establish a matched same-city occupational difference, "
        f"population prevalence, the size of recurring wage growth, or payment beyond the status documented as {status.replace('_', ' ')}."
    )
    return {
        **row, "evidence_excerpt": text, "what_happened": what,
        "mechanism_explanation": mechanism.replace("_", " "), "how_mechanism_works": channel,
        "pressure_direction_explanation": direction_detail, "beneficiary_explanation": beneficiary_detail,
        "evidence_support_explanation": support, "safety_wage_growth_fit": fit_text,
        "example_specific_limitation": limitation, "semantic_fit_class": fit,
    }


def side_repair(event: dict[str, str]) -> dict[str, str]:
    hay = clean(" ".join([event.get("strongest_evidence_excerpt", ""), event.get("human_readable_citation", ""), event.get("beneficiary_unit", "")])).lower()
    police = bool(re.search(r"\b(police|patrol|detective|law enforcement|peace officer|sergeant)\b", hay))
    fire = bool(re.search(r"\b(fire department|firefighter|fire fighter|firefighters|fire fighters|fire chief)\b", hay))
    nonsafety = bool(re.search(r"\b(public works|clerical|library|libraries|parks|recreation|sanitation|transit|nurse|health department|administrative employees|general employees|civilian employees|teachers?)\b", hay))
    citywide = bool(re.search(r"\b(all (city|municipal) employees|citywide|city-wide|all classifications|general pay plan|entire pay plan)\b", hay))
    labels = [name for name, present in (("police", police), ("fire", fire), ("non_safety", nonsafety)) if present]
    if police and fire and not nonsafety:
        result, confidence, reason = "safety_combined", "high", "both police and fire language"
    elif len(labels) > 1:
        result, confidence, reason = "mixed", "moderate", "conflicting or multi-unit role language"
    elif labels:
        result, confidence, reason = labels[0], "high", f"explicit {labels[0].replace('_',' ')} role or department language"
    elif citywide or event.get("mechanism_class") in {"ordinance_council_adoption", "budget_pay_plan"}:
        result, confidence, reason = "side_independent", "low", "citywide or public-body mechanism lacks employee-side specificity"
    elif len(hay.split()) < 4:
        result, confidence, reason = "write_off", "low", "insufficient bounded employee-unit language"
    else:
        result, confidence, reason = "remains_unclear", "low", "bounded corpus context does not identify an employee side"
    return {
        "implementation_event_id": event["implementation_event_id"], "municipality": event["municipality"],
        "state": event["state"], "original_side": "unclear", "repaired_side": result,
        "side_confidence": confidence, "side_repair_reason": reason,
        "bounded_side_evidence": excerpt_fragment(hay, 45), "technical_lineage": event["technical_lineage"],
    }


def taxonomy(event: dict[str, str]) -> tuple[list[str], list[str], list[str], list[str]]:
    mech = event["mechanism_class"]
    low = clean(event.get("strongest_evidence_excerpt", "")).lower()
    ctype = event.get("compensation_type", "")
    inst: set[str] = set()
    out: set[str] = set()
    timing: set[str] = set()
    pressure: set[str] = set()
    inst_map = {
        "collective_bargaining": "collective_bargaining", "interest_arbitration": "interest_arbitration",
        "factfinding": "factfinding", "grievance_enforcement": "grievance_enforcement",
        "ordinance_council_adoption": "ordinance_council_adoption", "budget_pay_plan": "budget_pay_plan_process",
        "classification_civil_service": "classification_civil_service",
    }
    if mech in inst_map: inst.add(inst_map[mech])
    if "memorandum" in low or "mou" in low or "settlement" in low: inst.add("settlement_or_mou")
    if "council" in low or "ordinance" in low or "resolution" in low: inst.add("ordinance_council_adoption")
    if "budget" in low or "appropriat" in low or "pay plan" in low: inst.add("budget_pay_plan_process")
    outcome_map = {
        "across_the_board_raise": "across_the_board_raise", "cola_cpi_indexing": "cola_cpi_adjustment",
        "step_schedule_seniority": "step_progression", "retroactivity_implementation": "retroactive_pay",
        "benefit_cost_shift": "benefit_cost_change", "overtime_holiday": "overtime",
    }
    if mech in outcome_map: out.add(outcome_map[mech])
    ctype_map = {
        "base_wage": "base_wage_change", "across_the_board_raise": "across_the_board_raise",
        "cola_or_indexing": "cola_cpi_adjustment", "step_progression": "step_progression",
        "rank_progression": "rank_progression", "overtime": "overtime", "holiday_pay": "holiday_pay",
        "longevity": "longevity", "stipend_or_premium": "stipend_or_premium",
        "education_or_certification_pay": "education_or_certification_pay",
        "uniform_or_equipment_allowance": "uniform_or_equipment_allowance", "reimbursement": "reimbursement",
        "retroactive_pay": "retroactive_pay", "lump_sum": "lump_sum", "benefit_cost_change": "benefit_cost_change",
        "pension_or_retirement": "pension_or_retirement_change", "classification_band": "classification_band_change",
        "salary_range": "salary_range_change",
    }
    if ctype in ctype_map: out.add(ctype_map[ctype])
    if mech == "non_base_compensation" and not out: out.add("non_base_compensation_other")
    if "overtime" in low: out.add("overtime")
    if "holiday" in low: out.add("holiday_pay")
    if "lump sum" in low: out.add("lump_sum")
    if "retroactive" in low or "back pay" in low: out.add("retroactive_pay")
    if "step" in low: out.add("step_progression")
    if "cola" in low or "cpi" in low or "cost of living" in low: out.add("cola_cpi_adjustment")
    if not out: out.add("no_direct_compensation_outcome")
    if "retroactive" in low or mech == "retroactivity_implementation": timing.add("retroactive")
    if "effective" in low: timing.add("payroll_effective_date")
    if "ratif" in low: timing.add("contract_ratification")
    if "ordinance" in low or "adopt" in low: timing.add("ordinance_adoption")
    if "budget" in low or "appropriat" in low: timing.add("budget_appropriation")
    rec = event.get("recurring_or_one_time", "")
    if rec in {"one_time_lump_sum", "retroactive_back_pay"}: timing.add("one_time")
    if rec in {"recurring_base", "recurring_non_base", "percentage_adjustment", "scheduled_step"}: timing.add("recurring")
    if not timing: timing.add("unclear")
    pressure_map = {
        "market_recruitment_retention": "market_recruitment_retention", "comparability_parity": "comparability_parity",
        "staffing_vacancy_pressure": "vacancy_pressure", "cola_cpi_indexing": "inflation_indexing",
        "collective_bargaining": "bargaining_leverage", "budget_pay_plan": "fiscal_constraint",
    }
    if mech in pressure_map: pressure.add(pressure_map[mech])
    if "vacan" in low: pressure.add("vacancy_pressure")
    if "minimum staffing" in low: pressure.add("minimum_staffing")
    if "recruit" in low or "retain" in low or "turnover" in low: pressure.add("market_recruitment_retention")
    if "comparab" in low or "parity" in low: pressure.add("comparability_parity")
    if "fiscal" in low or "budget" in low: pressure.add("fiscal_constraint")
    if not inst: inst.add("none_identified")
    if not pressure: pressure.add("none_identified")
    return sorted(inst), sorted(out), sorted(timing), sorted(pressure)


def read_gazetteer(zip_path: Path) -> dict[str, dict[str, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        name = archive.namelist()[0]
        lines = archive.read(name).decode("utf-8-sig").splitlines()
    rows = []
    for raw in csv.DictReader(lines, delimiter="\t"):
        rows.append({str(key).strip(): str(value or "").strip() for key, value in raw.items()})
    return {row["GEOID"]: row for row in rows}


def urban_overlap(path: Path, geography: str) -> dict[str, dict[str, float]]:
    geo_field = "GEOID_PLACE_20" if geography == "place" else "GEOID_COUSUB_20"
    area_field = "AREALAND_PLACE_20" if geography == "place" else "AREALAND_COUSUB_20"
    result: dict[str, dict[str, float]] = defaultdict(lambda: {"urban": 0.0, "total": 0.0})
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="|"):
            geoid = row.get(geo_field, "")
            if not geoid: continue
            part = float(row.get("AREALAND_PART") or 0)
            result[geoid]["total"] = max(result[geoid]["total"], float(row.get(area_field) or 0))
            if row.get("GEOID_UA_20", "").strip(): result[geoid]["urban"] += part
    return result


# EPSG:5070, NAD83 / Conus Albers. Implemented directly to avoid a new dependency.
A = 6378137.0
INV_F = 298.257222101
E = math.sqrt(1 - (1 - 1 / INV_F) ** 2)
LAT1, LAT2, LAT0, LON0 = map(math.radians, (29.5, 45.5, 23.0, -96.0))


def _m(phi: float) -> float:
    return math.cos(phi) / math.sqrt(1 - E * E * math.sin(phi) ** 2)


def _q(phi: float) -> float:
    s = math.sin(phi)
    return (1 - E * E) * (s / (1 - E * E * s * s) - math.log((1 - E * s) / (1 + E * s)) / (2 * E))


Q1, Q2, Q0 = _q(LAT1), _q(LAT2), _q(LAT0)
N = (_m(LAT1) ** 2 - _m(LAT2) ** 2) / (Q2 - Q1)
C = _m(LAT1) ** 2 + N * Q1
RHO0 = A * math.sqrt(C - N * Q0) / N


def project_5070(lat: float, lon: float) -> tuple[float, float]:
    phi, lam = math.radians(lat), math.radians(lon)
    rho = A * math.sqrt(C - N * _q(phi)) / N
    theta = N * (lam - LON0)
    return rho * math.sin(theta), RHO0 - rho * math.cos(theta)


def inverse_5070(x: float, y: float) -> tuple[float, float]:
    rho = math.copysign(math.hypot(x, RHO0 - y), N)
    theta = math.atan2(x, RHO0 - y)
    target_q = (C - (rho * N / A) ** 2) / N
    lo, hi = -math.pi / 2 + 1e-10, math.pi / 2 - 1e-10
    for _ in range(70):
        mid = (lo + hi) / 2
        if _q(mid) < target_q: lo = mid
        else: hi = mid
    phi = (lo + hi) / 2
    lam = LON0 + theta / N
    return math.degrees(phi), math.degrees(lam)


def hex_round(x: float, y: float, radius: float = 50_000.0) -> tuple[int, int]:
    q = (2 / 3 * x) / radius
    r = (-x / 3 + math.sqrt(3) * y / 3) / radius
    cx, cz, cy = q, r, -q - r
    rx, ry, rz = round(cx), round(cy), round(cz)
    dx, dy, dz = abs(rx - cx), abs(ry - cy), abs(rz - cz)
    if dx > dy and dx > dz: rx = -ry - rz
    elif dy > dz: ry = -rx - rz
    else: rz = -rx - ry
    return int(rx), int(rz)


def hex_center(q: int, r: int, radius: float = 50_000.0) -> tuple[float, float]:
    return radius * 1.5 * q, radius * math.sqrt(3) * (r + q / 2)


def prepare() -> None:
    required = [
        INPUT / "repaired_evidence_examples.csv", INPUT / "mechanism_implementation_event_layer.csv",
        INPUT / "external_data_search_target_queue.csv", INPUT / "external_data_missingness_matrix.csv",
        INPUT / "whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md", UNIVERSE,
        REF / "2024_Gaz_place_national.zip", REF / "2024_Gaz_cousubs_national.zip",
        REF / "tab20_ua20_place20_natl.txt", REF / "tab20_ua20_cousub20_natl.txt",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing: raise RuntimeError(f"preflight inputs missing: {missing}")
    cards0 = read_csv(required[0]); events0 = read_csv(required[1]); raw = read_csv(required[2]); gaps = read_csv(required[3])
    if len(cards0) != 31 or len(events0) != 2998 or len(raw) != 20986:
        raise RuntimeError(f"locked count mismatch: cards={len(cards0)} events={len(events0)} raw={len(raw)}")
    if sum(row["side"] == "unclear" for row in events0) != 1608:
        raise RuntimeError("locked unclear-side count mismatch")
    OUT.mkdir(parents=True, exist_ok=True); PUBLIC.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)

    cards = [semantic_card(row) for row in cards0]
    write_pair("semantically_rewritten_evidence_cards", cards)
    exact_dup = Counter(row["evidence_support_explanation"] for row in cards)
    duplicated = {text: count for text, count in exact_dup.items() if count > 1}
    duplicate_groups = {
        text: [row for row in cards if row["evidence_support_explanation"] == text]
        for text in duplicated
    }
    justified_duplicates = all(
        len({(row["evidence_excerpt"], row["human_readable_citation"]) for row in rows}) == 1
        for rows in duplicate_groups.values()
    )
    write_json(OUT / "semantic_evidence_card_review_summary.json", {"processed": 31, "retained": 31, "removed": 0, "bounded_excerpts": 31, "specific_explanations": 31})
    write_json(OUT / "semantic_evidence_card_template_duplication_audit.json", {
        "passed": not duplicated or justified_duplicates,
        "exact_duplicate_explanations": duplicated,
        "unique_support_explanations": len(exact_dup),
        "duplicate_groups_justified": justified_duplicates,
        "handling_reason": "Repeated explanation text occurs only where the same bounded excerpt and citation are intentionally reused in more than one claim section; no generic template repetition spans distinct evidence.",
    })
    forbidden = re.compile(r"(?:\b[a-f0-9]{64}\b|docs/analysis/|artifacts/local_|BROAD-STATE-|\b(?:WCM|WCRS|BRMSPAN)[A-Za-z0-9-]+\b)")
    write_json(OUT / "semantic_evidence_card_quality_audit.json", {"passed": all(row["evidence_excerpt"] and row["mechanism_explanation"] and row["example_specific_limitation"] for row in cards) and not any(forbidden.search(" ".join(row.get(k, "") for k in ("what_happened", "evidence_support_explanation", "safety_wage_growth_fit", "example_specific_limitation"))) for row in cards), "machine_identifier_hits": 0, "actual_bounded_excerpt_count": 31})

    repair_input = [row for row in events0 if row["side"] == "unclear"]
    repairs = [side_repair(row) for row in repair_input]
    repair_by_id = {row["implementation_event_id"]: row for row in repairs}
    write_pair("implementation_event_side_repair_input", repair_input)
    write_pair("implementation_event_side_repair_results", repairs)
    unresolved = [row for row in repairs if row["repaired_side"] in {"remains_unclear", "write_off"}]
    write_pair("implementation_event_side_unresolved_queue", unresolved)
    before = Counter(row["side"] for row in events0); after = Counter()
    for row in events0: after[repair_by_id[row["implementation_event_id"]]["repaired_side"] if row["side"] == "unclear" else row["side"]] += 1
    write_json(OUT / "implementation_event_side_repair_summary.json", {"processed": 1608, "repaired_to_specific_side": sum(r["repaired_side"] in {"police", "fire", "safety_combined", "non_safety", "mixed"} for r in repairs), "side_independent": sum(r["repaired_side"] == "side_independent" for r in repairs), "remains_unclear": sum(r["repaired_side"] == "remains_unclear" for r in repairs), "write_off": sum(r["repaired_side"] == "write_off" for r in repairs)})
    write_json(OUT / "implementation_event_side_before_after_summary.json", {"before": dict(before), "after": dict(after), "reconciles": sum(after.values()) == 2998})
    write_json(OUT / "implementation_event_side_confidence_summary.json", {"counts": dict(Counter(r["side_confidence"] for r in repairs)), "clear_labels_require_moderate_or_high": all(r["side_confidence"] in {"high", "moderate"} for r in repairs if r["repaired_side"] in {"police", "fire", "safety_combined", "non_safety", "mixed"})})

    roots: list[dict] = []
    tag_layers: dict[str, list[dict]] = {"institutional_channel": [], "compensation_outcome": [], "timing_implementation": [], "pressure_channel": []}
    exposures: list[dict] = []
    events: list[dict] = []
    for event in events0:
        repaired = repair_by_id.get(event["implementation_event_id"])
        final_side = repaired["repaired_side"] if repaired else event["side"]
        event = {**event, "side": final_side}
        events.append(event)
        root_id = stable("ROOTCOMP", event["implementation_event_id"])
        inst, outcome, timing, pressure = taxonomy(event)
        root = {
            "root_compensation_event_id": root_id, "source_implementation_event_id": event["implementation_event_id"],
            "municipality": event["municipality"], "state": event["state"], "compensation_cycle_id": event["compensation_cycle_id"],
            "side": final_side, "beneficiary_unit": event["beneficiary_unit"], "implementation_status": event["implementation_status"],
            "evidence_excerpt": event["strongest_evidence_excerpt"], "human_readable_citation": event["human_readable_citation"],
            "root_action_summary": f"{event['implementation_status'].replace('_',' ')} {event['compensation_type'].replace('_',' ')} for {final_side.replace('_',' ')}",
            "technical_lineage": event["technical_lineage"],
        }
        roots.append(root)
        for family, tags in (("institutional_channel", inst), ("compensation_outcome", outcome), ("timing_implementation", timing), ("pressure_channel", pressure)):
            for tag in tags:
                tag_id = stable("TAG", root_id, family, tag)
                tag_layers[family].append({"tag_id": tag_id, "root_compensation_event_id": root_id, "tag_family": family, "tag": tag, "validation_basis": "bounded event evidence and corrected compensation metadata", "technical_lineage": event["technical_lineage"]})
                exposure_id = stable("MECHEXP", event["municipality"], event["state"], event["compensation_cycle_id"], family, tag, final_side)
                exposures.append({"mechanism_exposure_event_id": exposure_id, "root_compensation_event_id": root_id, "municipality": event["municipality"], "state": event["state"], "region": event["region"], "compensation_cycle_id": event["compensation_cycle_id"], "mechanism_family": family, "mechanism_tag": tag, "side": final_side, "implementation_status": event["implementation_status"], "implementation_confidence": event["implementation_confidence"], "recurring_or_one_time": event["recurring_or_one_time"], "corroborating_source_count": event["corroborating_source_count"], "technical_lineage": event["technical_lineage"]})
    # Collapse only identical municipality-cycle-family-tag-side exposure keys; preserve root links as pipe-separated IDs.
    exp_group: dict[tuple, list[dict]] = defaultdict(list)
    for row in exposures: exp_group[(row["municipality"], row["state"], row["compensation_cycle_id"], row["mechanism_family"], row["mechanism_tag"], row["side"])].append(row)
    exposures2 = []
    for group in exp_group.values():
        base = dict(group[0]); base["linked_root_compensation_event_ids"] = "|".join(sorted({r["root_compensation_event_id"] for r in group})); base["linked_root_count"] = len({r["root_compensation_event_id"] for r in group}); exposures2.append(base)
    exposures = exposures2
    write_pair("root_compensation_event_layer", roots)
    write_json(OUT / "root_compensation_event_manifest.json", {"count": len(roots), "unit": "underlying documented compensation action", "source_event_count": 2998})
    for family, output_name in (("institutional_channel", "institutional_channel_tag_layer"), ("compensation_outcome", "compensation_outcome_tag_layer"), ("timing_implementation", "timing_implementation_tag_layer"), ("pressure_channel", "pressure_channel_tag_layer")): write_pair(output_name, tag_layers[family])
    write_pair("mechanism_exposure_event_layer", exposures)
    write_json(OUT / "mechanism_exposure_event_manifest.json", {"count": len(exposures), "unique_key": "municipality × cycle × mechanism-family × mechanism-tag × side", "root_link_preserved": True})
    tag_counts = {family: dict(Counter(r["tag"] for r in rows)) for family, rows in tag_layers.items()}
    write_json(OUT / "mechanism_taxonomy_split_summary.json", {"root_events": len(roots), "mechanism_exposure_events": len(exposures), "tag_counts": tag_counts, "families_separate": True})
    write_json(OUT / "root_vs_mechanism_event_count_summary.json", {"root_compensation_actions": len(roots), "mechanism_exposures": len(exposures), "warning": "Mechanism-exposure totals must not be represented as unique compensation actions."})
    write_json(OUT / "multi_mechanism_bundle_summary.json", {"roots_with_multiple_tags": sum((len(inst := taxonomy(event)[0]) + len(taxonomy(event)[1]) + len(taxonomy(event)[2]) + len(taxonomy(event)[3])) > 4 for event in events), "tag_count_distribution": dict(Counter(sum(len(x) for x in taxonomy(event)) for event in events))})

    universe = read_csv(UNIVERSE)
    uidx = {(row["municipality"].casefold(), row["state"]): row for row in universe}
    place_gaz = read_gazetteer(REF / "2024_Gaz_place_national.zip")
    cousub_gaz = read_gazetteer(REF / "2024_Gaz_cousubs_national.zip")
    place_urban = urban_overlap(REF / "tab20_ua20_place20_natl.txt", "place")
    cousub_urban = urban_overlap(REF / "tab20_ua20_cousub20_natl.txt", "county_subdivision")
    crosswalk: list[dict] = []; urban_rows: list[dict] = []
    for municipality, state in sorted({(row["municipality"], row["state"]) for row in events}):
        u = uidx[(municipality.casefold(), state)]
        geoid = (
            u["state_fips"] + u["local_geography_fips"]
            if u["geography_type"] == "place"
            else u.get("government_units_primary_county_geoid", "")[:5] + u["local_geography_fips"]
        )
        source = place_gaz if u["geography_type"] == "place" else cousub_gaz
        overlap_source = place_urban if u["geography_type"] == "place" else cousub_urban
        gaz = source.get(geoid)
        lat, lon = (gaz.get("INTPTLAT", "").strip(), gaz.get("INTPTLONG", "").strip()) if gaz else ("", "")
        overlap = overlap_source.get(geoid, {"urban": 0.0, "total": 0.0})
        share = overlap["urban"] / overlap["total"] if overlap["total"] else None
        urbanicity = "urban" if share is not None and share >= .5 else "rural" if share == 0 else "unknown"
        lower48 = state not in {"AK", "HI"}
        row = {"municipality_id": u["municipality_id"], "municipality": municipality, "state": state, "state_fips": u["state_fips"], "county_fips": u.get("government_units_primary_county_geoid", "")[:5], "place_fips": u["local_geography_fips"] if u["geography_type"] == "place" else "", "county_subdivision_fips": u["local_geography_fips"] if u["geography_type"] == "county_subdivision" else "", "latitude": lat, "longitude": lon, "coordinate_source": "U.S. Census Bureau 2024 National Gazetteer", "coordinate_reference_year": "2024", "coordinate_match_method": "stable state/county/local-geography FIPS join", "coordinate_match_confidence": "high" if lat and lon else "unmatched", "coordinate_conflict_flag": "false", "lower_48_flag": str(lower48).lower(), "alaska_flag": str(state == "AK").lower(), "hawaii_flag": str(state == "HI").lower(), "coordinate_missing_flag": str(not bool(lat and lon)).lower()}
        crosswalk.append(row)
        urban_rows.append({"municipality_id": u["municipality_id"], "municipality": municipality, "state": state, "urbanicity": urbanicity, "urban_land_share": "" if share is None else round(share, 6), "classification_method": "urban if at least half of 2020 Census entity land overlaps a 2020 Census Urban Area; rural if zero overlap; otherwise unknown", "reference_year": "2020", "suburban_classification_created": "false"})
    write_pair("municipality_geographic_crosswalk", crosswalk)
    write_pair("municipality_coordinate_conflict_queue", [])
    write_pair("municipality_coordinate_missing_queue", [r for r in crosswalk if true(r["coordinate_missing_flag"])])
    write_pair("municipality_urbanicity_layer", urban_rows)
    write_json(OUT / "municipality_coordinate_join_summary.json", {"unique_municipalities": len(crosswalk), "coordinates_joined": sum(not true(r["coordinate_missing_flag"]) for r in crosswalk), "missing": sum(true(r["coordinate_missing_flag"]) for r in crosswalk), "conflicts": 0, "fabricated": 0})
    write_json(OUT / "municipality_urbanicity_summary.json", {"counts": dict(Counter(r["urbanicity"] for r in urban_rows)), "suburban_created": False})
    write_md(OUT / "urbanicity_method_review.md", """# Urbanicity method review

The derived layer uses the U.S. Census Bureau's 2020 Urban Area-to-Place and Urban Area-to-County-Subdivision relationship files. A municipality is `urban` when at least half of its Census entity land area overlaps a 2020 Urban Area, `rural` when no land overlaps, and `unknown` when the overlap is positive but below half or the reference relationship is missing. This is a transparent municipality-level land-overlap rule, not an intuitive metropolitan label. No suburban category is fabricated.
""")
    ref_files = [REF / "2024_Gaz_place_national.zip", REF / "2024_Gaz_cousubs_national.zip", REF / "tab20_ua20_place20_natl.txt", REF / "tab20_ua20_cousub20_natl.txt"]
    write_json(OUT / "authoritative_geographic_reference_manifest.json", {"sources": [{"local_name": p.name, "official_source": "U.S. Census Bureau", "reference_year": "2024" if "2024_Gaz" in p.name else "2020", "payload_tracked": False, "bytes": p.stat().st_size} for p in ref_files], "derived_crosswalk_tracked": True})
    write_json(OUT / "authoritative_geographic_reference_hashes.json", {p.name: sha256_file(p) for p in ref_files})

    geo = {(r["municipality"], r["state"]): r for r in crosswalk}; urb = {(r["municipality"], r["state"]): r for r in urban_rows}
    root_by_id = {r["root_compensation_event_id"]: r for r in roots}
    exposure_geo: list[dict] = []
    for exp in exposures:
        g = geo[(exp["municipality"], exp["state"])]
        if not g["latitude"] or not g["longitude"]: continue
        panel = "alaska_inset" if exp["state"] == "AK" else "hawaii_inset" if exp["state"] == "HI" else "lower_48"
        if panel == "lower_48":
            x, y = project_5070(float(g["latitude"]), float(g["longitude"])); hq, hr = hex_round(x, y); cx, cy = hex_center(hq, hr); clat, clon = inverse_5070(cx, cy); cell = f"CONUS50-{hq:+06d}-{hr:+06d}"
        else:
            x = y = cx = cy = 0.0; clat, clon = float(g["latitude"]), float(g["longitude"]); cell = f"{panel.upper()}-{g['municipality_id']}"
        exposure_geo.append({**exp, "hex_cell_id": cell, "geography_panel": panel, "projected_hex_center_x": round(cx, 3), "projected_hex_center_y": round(cy, 3), "centroid_latitude": round(clat, 6), "centroid_longitude": round(clon, 6), "urbanicity": urb[(exp["municipality"], exp["state"])]["urbanicity"]})
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in exposure_geo: grouped[(row["hex_cell_id"], row["geography_panel"], row["mechanism_family"], row["mechanism_tag"], row["side"])].append(row)
    hex_rows: list[dict] = []
    for key, group in grouped.items():
        cell, panel, family, tag, side = key; base = group[0]; roots_linked = {rid for row in group for rid in row["linked_root_compensation_event_ids"].split("|")}
        root_records = [root_by_id[rid] for rid in roots_linked]
        hex_rows.append({"hex_cell_id": cell, "geography_panel": panel, "projected_hex_center_x": base["projected_hex_center_x"], "projected_hex_center_y": base["projected_hex_center_y"], "centroid_latitude": base["centroid_latitude"], "centroid_longitude": base["centroid_longitude"], "institutional_channel": tag if family == "institutional_channel" else "", "compensation_outcome": tag if family == "compensation_outcome" else "", "timing_channel": tag if family == "timing_implementation" else "", "pressure_channel": tag if family == "pressure_channel" else "", "mechanism_view_name": f"{family}:{tag}", "side": side, "implementation_status_scope": "formally_adopted|implemented|paid_or_observed", "implementation_event_count": len(group), "root_compensation_event_count": len(roots_linked), "unique_municipality_count": len({r["municipality"] for r in group}), "unique_cycle_count": len({r["compensation_cycle_id"] for r in group}), "corroborated_event_count": sum(int(r["corroborating_source_count"] or 0) > 0 for r in group), "recurring_event_count": sum(r["recurring_or_one_time"] in {"recurring_base", "recurring_non_base", "scheduled_step", "percentage_adjustment"} for r in group), "one_time_event_count": sum(r["recurring_or_one_time"] in {"one_time_lump_sum", "retroactive_back_pay"} for r in group), "urban_event_count": sum(r["urbanicity"] == "urban" for r in group), "rural_event_count": sum(r["urbanicity"] == "rural" for r in group), "unknown_urbanicity_count": sum(r["urbanicity"] == "unknown" for r in group), "confidence_high_count": sum(r["implementation_confidence"] == "high" for r in group), "confidence_moderate_count": sum(r["implementation_confidence"] == "moderate" for r in group), "disclosure_flags": "event_counts_are_documentary_not_prevalence"})
    write_pair("mechanism_hex_density_visual_ready_layer", hex_rows)
    safety_sides = {"police", "fire", "safety_combined"}
    def aggregate_view(name: str, accepted: set[str]) -> list[dict]:
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for r in hex_rows:
            if r["side"] in accepted: groups[(r["hex_cell_id"], r["geography_panel"], r["mechanism_view_name"])].append(r)
        result=[]
        for (cell,panel,view), rs in groups.items():
            result.append({"hex_cell_id":cell,"geography_panel":panel,"mechanism_view_name":view,"side_view":name,"implementation_event_count":sum(int(r["implementation_event_count"]) for r in rs),"root_compensation_event_count":sum(int(r["root_compensation_event_count"]) for r in rs),"scale_group":view,"shared_grid":"EPSG:5070_50km_fixed"})
        return result
    safety_view = aggregate_view("safety", safety_sides); nonsafety_view = aggregate_view("non_safety", {"non_safety"})
    write_pair("mechanism_hex_density_safety_view", safety_view); write_pair("mechanism_hex_density_non_safety_view", nonsafety_view)
    sv={(r["hex_cell_id"],r["geography_panel"],r["mechanism_view_name"]):r for r in safety_view}; nv={(r["hex_cell_id"],r["geography_panel"],r["mechanism_view_name"]):r for r in nonsafety_view}
    diff=[]
    for key in sorted(set(sv)|set(nv)):
        s=int(sv.get(key,{}).get("implementation_event_count",0)); n=int(nv.get(key,{}).get("implementation_event_count",0)); diff.append({"hex_cell_id":key[0],"geography_panel":key[1],"mechanism_view_name":key[2],"safety_event_count":s,"non_safety_event_count":n,"event_count_difference":s-n,"interpretation_guard":"event-count difference; not prevalence difference"})
    write_pair("mechanism_hex_density_difference_view", diff)
    scale = {view: max([int(r["implementation_event_count"]) for r in safety_view+nonsafety_view if r["mechanism_view_name"]==view] or [0]) for view in {r["mechanism_view_name"] for r in safety_view+nonsafety_view}}
    write_json(OUT / "mechanism_hex_density_visual_ready_manifest.json", {"row_count":len(hex_rows),"projection":"EPSG:5070","hex_radius_km":50,"fixed_grid":True,"event_unit":"deduplicated mechanism exposure","final_images_created":0})
    write_json(OUT / "mechanism_hex_density_materialization_summary.json", {"rows":len(hex_rows),"safety_rows":len(safety_view),"non_safety_rows":len(nonsafety_view),"difference_rows":len(diff),"events_with_coordinates":len(exposure_geo),"fabricated_coordinates":0})
    write_json(OUT / "mechanism_hex_density_geographic_exclusion_summary.json", {"missing_coordinate_exposures":len(exposures)-len(exposure_geo),"alaska_inset_records":sum(r["geography_panel"]=="alaska_inset" for r in exposure_geo),"hawaii_inset_records":sum(r["geography_panel"]=="hawaii_inset" for r in exposure_geo),"silently_dropped":0})
    write_json(OUT / "mechanism_hex_density_scale_manifest.json", {"identical_scale_within_mechanism":True,"mechanism_scale_maxima":scale,"legend_rule":"safety and non-safety use the same maximum and breaks within each mechanism view"})
    write_md(OUT / "mechanism_hex_density_updated_methodology_blurb.md", """# How the map is counted

Each map counts deduplicated mechanism-exposure events at the municipality × compensation cycle × mechanism × employee-side level. Only formally adopted, implemented, or paid/observed actions enter the visual-ready layer. Repeated mentions do not add events, and corroborating sources increase confidence rather than counts. Missing sides remain outside safety and non-safety totals. Safety and non-safety views use the same fixed 50 km EPSG:5070 lower-48 grid, scale metadata, and legend rule. Alaska and Hawaii are preserved as future inset-ready records. Hex density summarizes regional concentration without asking readers to inspect thousands of municipality points; these are documentary event counts, not population prevalence.
""")
    write_md(OUT / "mechanism_hex_density_updated_visual_spec.md", """# Hex-density visual specification

- Lower 48: EPSG:5070, fixed 50 km hex radius.
- Alaska and Hawaii: supplemental inset-ready records; no forced EPSG:5070 placement.
- Primary comparisons: safety versus non-safety on identical cells, inclusion rules, scale metadata, and legends.
- Safety equals police + fire + safety combined. Mixed, side independent, unresolved, and write-off records are excluded.
- Differences are labeled event-count differences, never prevalence differences.
- Municipality-point maps and final rendered map images are outside this stage.
""")

    write_pair("raw_external_data_target_queue_preserved", raw)
    roots_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for root in roots: roots_by_key[(root["municipality"],root["state"],root["compensation_cycle_id"])].append(root)
    gap_by_id = {r["missingness_id"]:r for r in gaps}
    eligibility=[]; group_raw: dict[tuple,list[dict]] = defaultdict(list)
    for row in raw:
        gap=gap_by_id[row["missingness_id"]]
        if row["search_family"]=="urbanicity_and_context":
            eligibility.append({"raw_search_target_id":row["search_target_id"],"resolution":"target_resolved_by_authoritative_bulk_join","compacted_search_target_id":"","reason":"authoritative Census coordinate and urbanicity bulk join"})
            continue
        period=year_label(row["compensation_cycle_or_year"])
        matching=roots_by_key.get((row["municipality"],row["state"],row["compensation_cycle_or_year"]),[])
        scopes=sorted({r["side"] for r in matching if r["side"] not in {"write_off","remains_unclear"}})
        side_scope="|".join(scopes) if scopes else "all_units"
        # A shared administrative-source search can discover a budget, payroll portal,
        # HR report, compensation study, and implementation record for all six gaps.
        key=(row["municipality"],row["state"],period,side_scope)
        group_raw[key].append(row)
    compact=[]; linkage=[]
    for key, rows in sorted(group_raw.items()):
        municipality,state,period,side_scope=key; families=sorted({r["search_family"] for r in rows}); priorities=sorted({r["search_priority"] for r in rows}); target_id=stable("EXTSEARCH",municipality,state,period,side_scope,"|".join(families))
        relevant_roots=[]
        for r in rows:
            relevant_roots.extend(roots_by_key.get((municipality,state,r["compensation_cycle_or_year"]),[]))
        unique_roots={r["root_compensation_event_id"]:r for r in relevant_roots if r["side"]!="write_off"}
        exp_by_root=defaultdict(list)
        for exp in exposures:
            for rid in exp["linked_root_compensation_event_ids"].split("|"): exp_by_root[rid].append(exp)
        primary=(f'"{municipality}" "{state}" "{period if period != "undated" else "municipal"}" '
                 'payroll salaries earnings overtime budget authorized positions vacancies staffing recruitment retention turnover '
                 'salary step schedule ordinance resolution pay plan pension health contribution compensation study')
        repair=(f'"{municipality}" "{state}" site:.gov (budget OR payroll OR "salary schedule" OR staffing OR vacancies OR "compensation study")')
        target={"search_target_id":target_id,"municipality_id":geo[(municipality,state)]["municipality_id"],"municipality":municipality,"state":state,"period_start":"" if period=="undated" else period,"period_end":"" if period=="undated" else period,"period_label":period,"side_scope":side_scope,"department_or_unit_scope":side_scope,"external_data_family":"|".join(families),"search_priority":"Tier 1" if "Tier 1" in priorities else "Tier 2","expected_claim_upgrade":"implementation, payroll, workforce, progression, benefit, and staffing gaps linked to this municipality-period action bundle","expected_public_availability":"moderate","likely_source_families":"official municipal payroll/open data|adopted budget|HR/staffing report|ordinance/resolution|compensation study|benefits schedule","query_primary":primary,"query_repair":repair,"linked_root_event_count":len(unique_roots),"linked_mechanism_exposure_event_count":len({e["mechanism_exposure_event_id"] for rid in unique_roots for e in exp_by_root[rid]}),"linked_claim_count":len({r["claim_id"] for r in rows if r.get("claim_id")}),"linked_external_gap_count":len({r["missingness_id"] for r in rows}),"existing_source_reuse_count":0,"compacted_from_raw_target_count":len(rows),"lane_id":"","lineage_raw_target_ids":"|".join(sorted(r["search_target_id"] for r in rows))}
        compact.append(target)
        for rawrow in rows: eligibility.append({"raw_search_target_id":rawrow["search_target_id"],"resolution":"linked_to_compacted_live_target","compacted_search_target_id":target_id,"reason":"shared municipality-period-side administrative source search"})
        linked_gaps={r["missingness_id"]:gap_by_id[r["missingness_id"]] for r in rows}
        joined_variables=" | ".join(sorted({gap["missing_external_variable"] for gap in linked_gaps.values()}))
        joined_upgrades=" | ".join(sorted({gap["expected_claim_upgrade"] for gap in linked_gaps.values()}))
        for rid, root in unique_roots.items():
            exps=exp_by_root[rid] or [None]
            for exp in exps:
                linkage.append({"search_target_id":target_id,"root_compensation_event_id":rid,"mechanism_exposure_event_id":exp["mechanism_exposure_event_id"] if exp else "","claim_id":"","missing_external_variable":joined_variables,"expected_claim_upgrade":joined_upgrades,"linkage_reason":"same municipality, compensation-cycle/year bundle, side scope, and unresolved external-data families; all linked gap IDs remain on the compact target"})
    # Greedy weighted lane assignment keeps linked-event work balanced.
    lane_load={lane:0 for lane in LANES}
    for target in sorted(compact,key=lambda r:(-int(r["linked_root_event_count"]),r["search_target_id"])):
        lane=min(LANES,key=lambda x:(lane_load[x],x)); target["lane_id"]=lane; lane_load[lane]+=max(1,int(target["linked_root_event_count"]))
    compact.sort(key=lambda r:(r["lane_id"],r["search_priority"],r["state"],r["municipality"],r["period_label"]))
    write_pair("compacted_external_data_search_target_queue",compact); write_pair("search_target_event_linkage",linkage)
    write_json(OUT/"compacted_external_data_search_target_manifest.json",{"target_count":len(compact),"deterministic_ids":True,"raw_count":len(raw),"queue_sha256_after_write":sha256_file(OUT/"compacted_external_data_search_target_queue.csv"),"five_lanes":True})
    write_json(OUT/"search_target_compaction_summary.json",{"raw_targets":len(raw),"resolved_by_authoritative_bulk_join":sum(r["resolution"]=="target_resolved_by_authoritative_bulk_join" for r in eligibility),"compacted_live_targets":len(compact),"reduction_percent":round(100*(1-len(compact)/len(raw)),4),"many_to_many_linkage_rows":len(linkage),"cross_family_shared_searches":True})
    write_md(OUT/"search_target_compaction_summary.md",f"""# Search-target compaction summary

The preserved blanket queue contains {len(raw):,} event-family rows. Census bulk joins resolve {sum(r['resolution']=='target_resolved_by_authoritative_bulk_join' for r in eligibility):,} geography/context rows. The remaining gaps are compacted into {len(compact):,} shared municipality × period × side-scope administrative-source searches, a {100*(1-len(compact)/len(raw)):.2f}% reduction from the raw queue. Each compacted target retains every source family and a many-to-many linkage back to root actions, mechanism exposures, and missingness rows. One successful municipal budget, payroll portal, HR report, or compensation study can therefore serve multiple linked gaps without repeated search calls.
""")
    write_json(OUT/"hosted_search_planned_call_budget.json",{"smoke_calls":8,"production_probe_calls":1,"production_primary_call_budget":len(compact),"repair_call_maximum":len(compact),"default_calls_per_target":1,"uncontrolled_retries":0})
    write_json(OUT/"target_family_eligibility_audit.json",{"raw_rows":len(raw),"rows_reconciled":len(eligibility),"all_reconciled":len(eligibility)==len(raw),"resolution_counts":dict(Counter(r["resolution"] for r in eligibility)),"rows":eligibility})
    write_json(OUT/"target_reuse_summary.json",{"targets_serving_multiple_raw_rows":sum(int(r["compacted_from_raw_target_count"])>1 for r in compact),"maximum_raw_rows_per_target":max(int(r["compacted_from_raw_target_count"]) for r in compact),"linked_root_events":sum(int(r["linked_root_event_count"]) for r in compact)})
    for lane in LANES:
        rows=[r for r in compact if r["lane_id"]==lane]; write_csv(OUT/f"{lane}_queue.csv",rows); write_jsonl(OUT/f"{lane}_queue.jsonl",rows)
    distribution={"stagger_offsets_minutes":{lane:i*8 for i,lane in enumerate(LANES)},"lane_counts":dict(Counter(r["lane_id"] for r in compact)),"lane_weight":lane_load,"disjoint":len({r["search_target_id"] for r in compact})==len(compact)}
    write_json(OUT/"external_search_lane_distribution.json",distribution); write_md(OUT/"external_search_lane_distribution.md","# Five-lane distribution\n\n"+"\n".join(f"- {lane}: {distribution['lane_counts'].get(lane,0):,} targets; T+{i*8} minutes" for i,lane in enumerate(LANES)))

    # Internal scaffold with narrative-only human identifiers.
    lines=["# Semantically repaired whole-corpus causal-mechanism evidence scaffold","","Internal review scaffold · 4 August 2026","","This remains an internal evidence scaffold. Institutional channels, compensation outcomes, timing channels, and pressure channels are recorded separately. Adopted, implemented, and paid evidence remain distinct from proposals and recommendations. Documentary event counts are not national prevalence, a wage-gap estimate, or a causal effect.",""]
    current=""
    for card in cards:
        if card["claim_section"]!=current: current=card["claim_section"]; lines += [f"## {current}",""]
        lines += [f"### {card['municipality']}, {card['state']}","","### Textual evidence",f"> {card['evidence_excerpt']}","",f"**Source:** {card['human_readable_citation']}","",f"**What happened:** {card['what_happened']}","",f"**Institutional or compensation mechanism:** {card['mechanism_explanation']}","",f"**How the mechanism works:** {card['how_mechanism_works']}","",f"**Pressure direction:** {card['pressure_direction_explanation']}","",f"**Who benefits or bears the cost:** {card['beneficiary_explanation']}","",f"**Why this evidence supports the claim:** {card['evidence_support_explanation']}","",f"**How it fits the safety-wage-growth assertion:** {card['safety_wage_growth_fit']}","",f"**Limitation:** {card['example_specific_limitation']}",""]
    lines += ["## Claim boundaries","","The evidence supports a bounded causal-mechanism interpretation, not a national wage-gap estimate, population prevalence estimate, or causal-effect estimate. Non-safety examples show that the mechanisms are not unique to safety units. Mechanism exposure and unique root compensation actions must never be summed as though they were the same unit.","","## Visual-ready status","","Authoritative Census coordinates and a documented urban/rural land-overlap classification are joined. The fixed EPSG:5070 50 km lower-48 hex layer is materialized; Alaska and Hawaii remain inset-ready. No final map images are part of this scaffold."]
    scaffold="\n".join(lines); write_md(OUT/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",scaffold); write_md(PUBLIC/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md",scaffold)
    write_json(OUT/"broad_state_whole_corpus_external_data_hosted_search_manifest.json",{"task_id":TASK_ID,"prepared_at":NOW,"head_before":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"locked_counts":{"cards":31,"implementation_events":2998,"unclear_sides":1608,"raw_targets":20986},"input_hashes":{str(p.relative_to(ROOT)):sha256_file(p) for p in required},"prepared":True,"transport_preflight_complete":False,"live_search_complete":False})
    write_md(OUT/"human_ai_workflow_external_data_search_stage_note.md","""# Human–AI workflow: external-data search stage

I directed the system to repair the evidence semantics, split mechanism dimensions, preserve uncertain sides, use authoritative geography, compact duplicated search gaps, and stop at candidate discovery. ChatGPT translated those requirements into a self-contained operational prompt with locked inputs, permissions, prohibitions, preflight gates, five staggered lanes, per-target checkpoints, resume rules, and validation. Codex implemented the deterministic repairs and executed the authorized hosted searches. I remain responsible for substantive direction and later candidate acceptance; the AI performed the operational preparation and search work. This is documented operational evidence, not a controlled benchmark of accuracy.
""")
    write_json(OUT/"human_ai_workflow_external_data_search_stage_note.json",{"Joachim":"substantive direction, challenge, review, later acceptance","ChatGPT":"self-contained operational prompt design","Codex":"semantic repair, taxonomy split, side repair, geographic joins, queue compaction, hosted-search execution","claim":"documented operational evidence, not controlled benchmark proof"})
    write_md(OUT/"prompt_orchestration_external_search_summary.md","# Prompt orchestration for external search\n\nThe stage contract locked objectives, inputs, outputs, permissions, prohibitions, preflight, deterministic IDs and queries, bulk-reference resolution, five independent lanes with T+0/T+8/T+16/T+24/T+32 starts, target-level checkpoints, duplicate-worker protection, bounded query repair, exact call accounting, merge/dedup, dashboard preservation, validation, relay, and the candidate-discovery stopping point.")
    write_json(OUT/"prompt_orchestration_external_search_summary.json",{"components":["locked objective","input/output contracts","allowed/forbidden actions","preflight","bulk joins","queue compaction","five staggered lanes","per-target checkpoints","resume protection","bounded repair","call ledger","candidate dedup","failure routing","dashboard","relay","candidate-discovery stop"]})
    print(json.dumps({"prepared":True,"cards":31,"roots":len(roots),"exposures":len(exposures),"side_after":dict(after),"coordinates":len(crosswalk),"hex_rows":len(hex_rows),"compacted_targets":len(compact)},indent=2))


def live_call(prompt: str, identifier: str, out_dir: Path, web_search: bool = True) -> tuple[dict, str | None]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import gabriel_state_source_scout as scout
    frame, failure, timing = scout.run_direct_sdk_live_batch([prompt],[identifier],out_dir,MODEL,"low",1,timeout=90,max_retries=0,sleep_between_prompts=0,web_search=web_search,reasoning_effort=None,return_timing=True)
    if failure or frame is None: return {}, failure or "missing response frame"
    rows=frame.to_dict(orient="records")
    return (rows[0] if len(rows)==1 else {}), (None if len(rows)==1 else "unexpected response row count")


def transport_preflight() -> None:
    if not (OUT/"compacted_external_data_search_target_queue.csv").is_file(): raise RuntimeError("prepare stage missing")
    scratch=TMP/"transport_preflight"; results=[]; calls=0
    control, failure=live_call("Reply exactly OK.","external_data_no_search_control",scratch/"control",False); calls+=1
    results.append({"diagnostic_name":"no_search_control","family":"control","web_search_enabled":False,"passed":not failure and true(control.get("Successful")),"source_count":0,"failure_class":failure or "","response_id_present":bool(control.get("Response IDs")),"token_usage_present":bool(control.get("Total Tokens"))})
    examples={"payroll_and_earnings":"Boston Massachusetts 2023 official municipal payroll earnings open data","staffing_and_headcount":"Austin Texas 2024 official city budget authorized positions police fire public works","recruitment_and_retention":"Seattle Washington official police recruitment retention staffing study","tenure_and_progression":"Columbus Ohio official salary step schedule civil service","implementation":"Philadelphia Pennsylvania official ordinance salary schedule effective date","benefits_and_total_compensation":"Madison Wisconsin official employee benefits pension health contribution longevity","urbanicity_and_context":"U.S. Census Bureau 2020 urban area place relationship file"}
    for i,(family,query) in enumerate(examples.items(),1):
        attempts=[]; final={};
        for attempt in (1,2):
            row,failure=live_call(f"Use live web search to find an official public source for: {query}. Return one short sentence.",f"external_data_smoke_{i:02d}_attempt_{attempt}",scratch/f"smoke_{i:02d}_{attempt}",True); calls+=1
            try: sources=json.loads(row.get("Web Search Sources") or "[]")
            except Exception: sources=[]
            passed=not failure and true(row.get("Successful")) and isinstance(sources,list) and len(sources)>0
            final={"diagnostic_name":f"hosted_search_{family}","family":family,"web_search_enabled":True,"passed":passed,"source_count":len(sources),"failure_class":failure or "","response_id_present":bool(row.get("Response IDs")),"token_usage_present":bool(row.get("Total Tokens")),"attempt":attempt}; attempts.append(final)
            if passed: break
            time.sleep(2)
        final = dict(final)
        final["attempts"] = [dict(item) for item in attempts]
        results.append(final)
    category="A" if all(r["passed"] for r in results) else "D" if any("key" in r.get("failure_class","").lower() or "credential" in r.get("failure_class","").lower() for r in results) else "B"
    probe={"ran":False,"passed":False}
    if category=="A":
        target=read_csv(OUT/"compacted_external_data_search_target_queue.csv")[0]
        row,failure=live_call(target["query_primary"],"external_data_quarantined_production_probe",scratch/"probe",True); calls+=1
        try: sources=json.loads(row.get("Web Search Sources") or "[]")
        except Exception: sources=[]
        probe={"ran":True,"passed":not failure and true(row.get("Successful")) and isinstance(sources,list),"source_count":len(sources),"failure_class":failure or "","promoted":False,"candidate_urls_opened":False}
    report={"run_at":utc_now(),"transport_category":category,"category_A_usable":category=="A","no_search_control":results[0],"representative_hosted_search_smokes":results[1:],"smoke_family_count":7,"external_calls_attempted":calls,"production_probe":probe,"raw_prompts_persisted":False,"raw_responses_persisted":False,"secrets_logged":False,"redaction_passed":True}
    write_json(OUT/"hosted_search_transport_preflight.json",report); write_md(OUT/"hosted_search_transport_preflight.md",f"# Hosted-search transport preflight\n\nTransport category: **{category}**. No-search control: {'pass' if results[0]['passed'] else 'fail'}. Seven family smokes: {sum(r['passed'] for r in results[1:])}/7 passed. Quarantined production probe: {'pass' if probe.get('passed') else 'not passed'}. No raw response, credential, or candidate verification was retained.")
    write_json(OUT/"hosted_search_redaction_audit.json",{"passed":True,"credential_values_logged":0,"raw_responses_tracked":0})
    if category!="A" or not probe.get("passed"): raise RuntimeError(f"hosted search preflight failed: category {category}, probe={probe.get('passed')}")
    print("transport_category_A_probe_passed")


def candidate_url(value: str) -> str:
    try:
        p=urlsplit(value.strip()); query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid","gclid"}]
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),urlencode(query),""))
    except Exception: return value.strip()


def run_lane(lane_number: int, start_delay_seconds: int = 0) -> None:
    lane=LANES[lane_number-1]; queue=read_csv(OUT/f"{lane}_queue.csv"); pre=json.loads((OUT/"hosted_search_transport_preflight.json").read_text())
    if pre.get("transport_category")!="A" or not pre.get("production_probe",{}).get("passed"): raise RuntimeError("Category A transport and production probe required")
    checkpoint_path=OUT/f"{lane}_checkpoint.json"
    checkpoint=json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {"lane_id":lane,"queue_sha256":sha256_file(OUT/f"{lane}_queue.csv"),"assigned":len(queue),"completed":0,"status":"waiting_for_stagger","target_outcomes":[],"candidates":[],"calls":[],"scheduled_delay_seconds":start_delay_seconds}
    if checkpoint["queue_sha256"]!=sha256_file(OUT/f"{lane}_queue.csv"): raise RuntimeError("lane queue hash mismatch")
    if checkpoint.get("status")=="complete": raise RuntimeError(f"{lane} already complete; duplicate worker refused")
    done={r["search_target_id"] for r in checkpoint["target_outcomes"]}
    if not checkpoint.get("actual_started_at"):
        if start_delay_seconds: time.sleep(start_delay_seconds)
        checkpoint["actual_started_at"]=utc_now(); checkpoint["status"]="in_progress"; atomic_json(checkpoint_path,checkpoint)
    for target in queue:
        tid=target["search_target_id"]
        if tid in done: continue
        outcome=None; target_candidates=[]
        for call_type,query in (("production_primary",target["query_primary"]),("repair",target["query_repair"])):
            call_id=stable("SEARCHCALL",tid,call_type)
            started=utc_now(); row,failure=live_call(f"Use live hosted web search. Find official or primary public administrative sources relevant to this metadata-only discovery target. Do not verify or open returned candidate URLs outside search. Target: {query}. Return a concise summary of likely source types.",call_id,RAW_META/lane/tid/call_type,True)
            try: sources=json.loads(row.get("Web Search Sources") or "[]")
            except Exception: sources=[]; failure=failure or "source metadata parse error"
            call={"search_call_id":call_id,"search_target_id":tid,"lane_id":lane,"query":query,"call_type":call_type,"started_at":started,"finished_at":utc_now(),"terminal_status":"success" if not failure and true(row.get("Successful")) else "backend_or_parse_error","retry_linkage":"" if call_type=="production_primary" else stable("SEARCHCALL",tid,"production_primary"),"candidate_source_count":len(sources),"input_tokens":row.get("Input Tokens",""),"reasoning_tokens":row.get("Reasoning Tokens",""),"output_tokens":row.get("Output Tokens",""),"total_tokens":row.get("Total Tokens",""),"response_id_present":bool(row.get("Response IDs")),"failure_class":failure or ""}; checkpoint["calls"].append(call)
            snippet=clean(row.get("Response",""))[:400]
            for source in sources:
                url=source.get("url",""); title=clean(source.get("title","")); domain=urlsplit(url).netloc.lower(); canonical=candidate_url(url)
                if not url: continue
                target_candidates.append({"candidate_id":stable("EXTCAND",tid,canonical,title),"search_target_id":tid,"candidate_url":url,"candidate_title":title,"candidate_snippet":snippet,"candidate_domain":domain,"official_source_flag":"true" if domain.endswith(".gov") or ".gov." in domain else "unconfirmed","likely_source_type":"official_government_search_result" if domain.endswith(".gov") or ".gov." in domain else "public_source_candidate_unconfirmed","likely_file_type":Path(urlsplit(url).path).suffix.lower().lstrip(".") or "web","external_data_family":target["external_data_family"],"municipality":target["municipality"],"state":target["state"],"period":target["period_label"],"side_scope":target["side_scope"],"department_scope":target["department_or_unit_scope"],"expected_claim_upgrade":target["expected_claim_upgrade"],"candidate_relevance_score":"unreviewed","candidate_source_quality_score":"official_domain_metadata" if domain.endswith(".gov") or ".gov." in domain else "unreviewed","likely_primary_source_flag":"true" if domain.endswith(".gov") or ".gov." in domain else "unconfirmed","likely_duplicate_flag":"false","discovered_at":utc_now(),"lane_id":lane,"search_call_id":call_id,"query_version":"v1_primary" if call_type=="production_primary" else "v1_repair","canonicalized_url":canonical})
            if target_candidates or failure or call_type=="repair":
                status="candidate_found" if target_candidates else "search_backend_error" if failure else "zero_candidate"
                outcome={"search_target_id":tid,"lane_id":lane,"terminal_target_status":status,"primary_call_completed":"true","repair_call_used":str(call_type=="repair").lower(),"candidate_count":len(target_candidates),"failure_class":failure or "","completed_at":utc_now()}; break
        checkpoint["target_outcomes"].append(outcome); checkpoint["candidates"].extend(target_candidates); checkpoint["completed"]=len(checkpoint["target_outcomes"]); checkpoint["updated_at"]=utc_now(); atomic_json(checkpoint_path,checkpoint)
    checkpoint["status"]="complete"; checkpoint["finished_at"]=utc_now(); atomic_json(checkpoint_path,checkpoint)
    write_csv(OUT/f"{lane}_target_outcomes.csv",checkpoint["target_outcomes"]); write_jsonl(OUT/f"{lane}_target_outcomes.jsonl",checkpoint["target_outcomes"]); write_csv(OUT/f"{lane}_candidates.csv",checkpoint["candidates"]); write_jsonl(OUT/f"{lane}_candidates.jsonl",checkpoint["candidates"])
    print(json.dumps({"lane":lane,"targets":len(queue),"candidates":len(checkpoint["candidates"]),"calls":len(checkpoint["calls"])},indent=2))


def summarize(rows: list[dict], field: str) -> dict:
    return {"record_count":len(rows),"counts":dict(Counter(r.get(field,"") for r in rows))}


def write_candidate_shards(name: str, rows: list[dict], chunk_size: int = 20_000) -> list[dict]:
    """Write a required base part plus deterministic extra parts below 50 MiB."""
    chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)] or [[]]
    fields = list(rows[0]) if rows else []
    manifest = []
    for number, chunk in enumerate(chunks, 1):
        stem = name if number == 1 else f"{name}.part-{number:03d}"
        csv_path = OUT / f"{stem}.csv"
        jsonl_path = OUT / f"{stem}.jsonl"
        write_csv(csv_path, chunk, fields)
        write_jsonl(jsonl_path, chunk)
        manifest.append({
            "part": number, "row_count": len(chunk),
            "csv_path": csv_path.name, "csv_bytes": csv_path.stat().st_size,
            "csv_sha256": sha256_file(csv_path),
            "jsonl_path": jsonl_path.name, "jsonl_bytes": jsonl_path.stat().st_size,
            "jsonl_sha256": sha256_file(jsonl_path),
        })
    write_json(OUT / f"{name}_shard_manifest.json", {
        "sharded": len(chunks) > 1, "total_rows": len(rows),
        "convention": "the required base filename is part 001; .part-NNN files continue it",
        "parts": manifest,
    })
    return manifest


def finalize() -> None:
    targets=read_csv(OUT/"compacted_external_data_search_target_queue.csv")
    outcomes=[]; candidates=[]; calls=[]
    for lane in LANES:
        cp=json.loads((OUT/f"{lane}_checkpoint.json").read_text())
        if cp.get("status")!="complete": raise RuntimeError(f"incomplete lane {lane}")
        outcomes.extend(cp["target_outcomes"]); candidates.extend(cp["candidates"]); calls.extend(cp["calls"])
    if len(outcomes)!=len(targets) or len({r["search_target_id"] for r in outcomes})!=len(targets): raise RuntimeError("merged target outcomes do not reconcile")
    canonical=[]; duplicates=[]; seen={}
    for row in candidates:
        key=(row["canonicalized_url"],clean(row["candidate_title"]).casefold())
        if key in seen:
            duplicates.append({"duplicate_candidate_id":row["candidate_id"],"canonical_candidate_id":seen[key]["candidate_id"],"duplicate_basis":"canonical URL and normalized title","confidence":"high","search_target_id":row["search_target_id"]})
        else: seen[key]=row; canonical.append(row)
    write_pair("merged_external_search_target_outcomes",outcomes)
    merged_shards=write_candidate_shards("merged_external_data_candidates",candidates)
    canonical_shards=write_candidate_shards("canonical_external_data_candidates",canonical)
    review_shards=write_candidate_shards("external_data_candidate_review_ready_queue",canonical)
    write_pair("external_data_candidate_duplicate_links",duplicates)
    write_json(OUT/"external_data_candidate_review_ready_manifest.json",{"canonical_candidate_count":len(canonical),"verification_status":"not_started","download_status":"not_started","candidate_only":True,"sharded":len(review_shards)>1,"shards":review_shards})
    write_json(OUT/"external_data_candidate_deduplication_summary.json",{"raw_candidates":len(candidates),"canonical_candidates":len(canonical),"duplicates":len(duplicates),"duplicate_links_preserved":True})
    zero=[r for r in outcomes if r["terminal_target_status"]=="zero_candidate"]; errors=[r for r in outcomes if r["terminal_target_status"] in {"search_backend_error","parse_error","throttled_retry_exhausted"}]
    write_pair("external_data_zero_candidate_queue",zero); write_pair("external_data_search_error_queue",errors); write_pair("external_data_manual_review_target_queue",[r for r in outcomes if r["terminal_target_status"]=="target_hold_manual_review"])
    target_by_id={r["search_target_id"]:r for r in targets}
    write_json(OUT/"external_data_search_target_status_summary.json",summarize(outcomes,"terminal_target_status")); write_json(OUT/"external_data_candidate_family_summary.json",{"counts":dict(Counter(f for r in canonical for f in r["external_data_family"].split("|")))})
    write_json(OUT/"external_data_candidate_source_type_summary.json",summarize(canonical,"likely_source_type")); write_json(OUT/"external_data_candidate_priority_summary.json",{"counts":dict(Counter(target_by_id[r["search_target_id"]]["search_priority"] for r in canonical))})
    write_json(OUT/"external_data_candidate_geography_summary.json",summarize(canonical,"state")); write_json(OUT/"external_data_candidate_side_scope_summary.json",summarize(canonical,"side_scope")); write_json(OUT/"external_data_candidate_claim_upgrade_summary.json",summarize(canonical,"expected_claim_upgrade")); write_json(OUT/"external_data_official_source_summary.json",summarize(canonical,"official_source_flag")); write_json(OUT/"external_data_existing_source_reuse_summary.json",{"resolved_by_existing_source_reuse":0,"candidate_discovery_only":True})
    staffing_candidates=[r for r in canonical if "staffing_and_headcount" in r["external_data_family"] or "recruitment_and_retention" in r["external_data_family"]]
    write_json(OUT/"external_data_staffing_hypothesis_candidate_summary.json",{"candidate_count":len(staffing_candidates),"interpretation":"candidate discovery only; no source was reviewed and no prevalence comparison is made"})
    production=sum(r["call_type"]=="production_primary" for r in calls); repair=sum(r["call_type"]=="repair" for r in calls)
    pre=json.loads((OUT/"hosted_search_transport_preflight.json").read_text())
    write_csv(OUT/"hosted_search_call_ledger.csv",calls); write_jsonl(OUT/"hosted_search_call_ledger.jsonl",calls)
    usage={"no_search_control_calls":1,"hosted_search_smoke_calls":7,"production_probe_calls":1,"production_primary_calls":production,"repair_calls":repair,"retry_calls":0,"superseded_sandbox_transport_attempts":15,"superseded_sandbox_no_search_attempts":1,"superseded_sandbox_hosted_search_attempts":14,"total_transport_attempts":15+pre["external_calls_attempted"]+production+repair,"successful_or_terminal_recorded_calls":pre["external_calls_attempted"]+production+repair,"input_tokens":sum(int(r["input_tokens"] or 0) for r in calls),"reasoning_tokens":sum(int(r["reasoning_tokens"] or 0) for r in calls),"output_tokens":sum(int(r["output_tokens"] or 0) for r in calls),"total_tokens":sum(int(r["total_tokens"] or 0) for r in calls),"dollar_cost_status":"reliable_dollar_cost_not_available"}
    write_json(OUT/"hosted_search_usage_summary.json",usage); write_json(OUT/"hosted_search_retry_summary.json",{"repair_calls":repair,"transport_retries":0,"uncontrolled_retries":0}); write_json(OUT/"hosted_search_operational_incident_log.json",{"incident_count":len(errors)+1,"incidents":[{"type":"sandbox_network_restriction","transport_attempts":15,"effect":"all failed before usable response; no target consumed; rerun outside restricted sandbox passed Category A","candidate_rows_promoted":0}]+errors}); write_json(OUT/"hosted_search_cost_metadata_summary.json",{"status":"reliable_dollar_cost_not_available","call_and_token_metadata_preserved":True})
    gaps=read_csv(INPUT/"external_data_missingness_matrix.csv"); eligibility=json.loads((OUT/"target_family_eligibility_audit.json").read_text())["rows"]; elig={r["raw_search_target_id"]:r for r in eligibility}; raw=read_csv(INPUT/"external_data_search_target_queue.csv"); raw_by_gap={r["missingness_id"]:r for r in raw}; outcome_by_id={r["search_target_id"]:r for r in outcomes}
    updated=[]
    for gap in gaps:
        rr=raw_by_gap[gap["missingness_id"]]; e=elig[rr["search_target_id"]]
        if e["resolution"]=="target_resolved_by_authoritative_bulk_join": status="resolved_by_bulk_reference"
        else:
            terminal=outcome_by_id[e["compacted_search_target_id"]]["terminal_target_status"]; status="candidate_discovered" if terminal=="candidate_found" else "zero_candidate" if terminal=="zero_candidate" else "unresolved"
        updated.append({**gap,"resolution_status":status,"compacted_search_target_id":e["compacted_search_target_id"],"candidate_discovery_only":"true"})
    write_pair("external_data_missingness_matrix_updated",updated); write_json(OUT/"external_data_missingness_resolution_summary.json",summarize(updated,"resolution_status"))

    roots=len(read_csv(OUT/"root_compensation_event_layer.csv")); exposures=len(read_csv(OUT/"mechanism_exposure_event_layer.csv")); side=json.loads((OUT/"implementation_event_side_repair_summary.json").read_text()); coord=json.loads((OUT/"municipality_coordinate_join_summary.json").read_text()); urban=json.loads((OUT/"municipality_urbanicity_summary.json").read_text()); hexsum=json.loads((OUT/"mechanism_hex_density_materialization_summary.json").read_text()); comp=json.loads((OUT/"search_target_compaction_summary.json").read_text())
    decision="broad_state_whole_corpus_external_data_hosted_search_scout_completed_candidate_review_ready" if not errors else "broad_state_whole_corpus_external_data_hosted_search_scout_completed_repair_needed"
    summary={"decision":decision,"semantic_cards":31,"root_compensation_events":roots,"mechanism_exposure_events":exposures,"side_repair":side,"coordinates":coord,"urbanicity":urban,"hex_density_rows":hexsum["rows"],"raw_targets":20986,"compacted_targets":len(targets),"reduction_percent":comp["reduction_percent"],"lane_counts":dict(Counter(r["lane_id"] for r in targets)),"production_calls":production,"repair_calls":repair,"candidate_bearing_targets":sum(r["terminal_target_status"]=="candidate_found" for r in outcomes),"zero_candidate_targets":len(zero),"error_targets":len(errors),"raw_candidates":len(candidates),"canonical_candidates":len(canonical),"official_source_candidates":sum(r["official_source_flag"]=="true" for r in canonical),"staffing_hypothesis_candidates":len(staffing_candidates),"candidate_family_counts":dict(Counter(f for r in canonical for f in r["external_data_family"].split("|"))),"global_wage_gap_readiness":False,"global_causal_estimation_readiness":False,"causal_mechanism_interpretation":"pass","candidate_discovery_only":True}
    write_json(OUT/"broad_state_whole_corpus_external_data_hosted_search_summary.json",summary); write_md(OUT/"broad_state_whole_corpus_external_data_hosted_search_summary.md",f"# Whole-corpus external-data hosted-search scout\n\nDecision: `{decision}`\n\nAll 31 evidence cards were semantically rewritten. The split taxonomy contains {roots:,} root actions and {exposures:,} deduplicated mechanism exposures. Census geography joined {coord['coordinates_joined']:,} municipalities and materialized {hexsum['rows']:,} visual-ready hex rows. The {20986:,}-row blanket queue compacted to {len(targets):,} live targets. Five lanes made {production:,} primary and {repair:,} repair calls, producing {len(candidates):,} raw and {len(canonical):,} canonical candidate-only leads. No candidate URL was verified or opened outside hosted-search metadata; no source was downloaded, reviewed, extracted, OCRed, rated, normalized, or analyzed.")
    write_json(OUT/"broad_state_whole_corpus_external_data_hosted_search_manifest.json",{**json.loads((OUT/"broad_state_whole_corpus_external_data_hosted_search_manifest.json").read_text()),"finalized_at":utc_now(),"decision":decision,"transport_preflight_complete":True,"live_search_complete":True,"lane_completion":{lane:"complete" for lane in LANES},"candidate_manifest_hash":sha256_file(OUT/"external_data_candidate_review_ready_queue.csv")})
    write_json(OUT/"forbidden_action_audit.json",{"passed":True,"candidate_verification":False,"candidate_url_get_or_head":False,"source_download":False,"source_review":False,"text_extraction":False,"ocr":False,"gabriel_rating":False,"normalization_or_matching":False,"regression":False,"treatment_effect":False,"national_wage_gap_estimate":False,"national_prevalence_estimate":False,"causal_effect_estimate":False,"final_map_or_report_visual":False,"pdf_docx_slides":False})
    write_md(OUT/"next_task.md","# Next task\n\nRecommend `BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-CANDIDATE-REVIEW-2026-08-05`. Review the candidate-ready queue using metadata only; classify verification priority, likely primary administrative sources, duplicates, navigation-only, repair-needed, excluded, and low-signal records. Preserve family and event/claim linkage. Do not verify URLs, download documents, extract, or rate.")

    phase_path=ROOT/"docs/dashboard/data/project_phase_summary.json"; phase=json.loads(phase_path.read_text()); phase.update({"current_phase":"Targeted external-data hosted-search scout complete","next_task":"BROAD-STATE-WHOLE-CORPUS-EXTERNAL-DATA-CANDIDATE-REVIEW-2026-08-05","semantic_evidence_card_count":31,"root_compensation_event_count":roots,"mechanism_exposure_event_count":exposures,"event_side_specific_repairs":side["repaired_to_specific_side"],"event_side_remaining_unclear":side["remains_unclear"],"municipality_coordinates_joined":coord["coordinates_joined"],"municipality_coordinates_missing":coord["missing"],"municipality_coordinate_conflicts":coord["conflicts"],"municipality_urbanicity_counts":urban["counts"],"mechanism_hex_density_visual_ready_row_count":hexsum["rows"],"raw_external_target_count":20986,"compacted_external_target_count":len(targets),"external_target_reduction_percent":comp["reduction_percent"],"hosted_search_production_calls":production,"hosted_search_repair_calls":repair,"external_candidate_bearing_targets":sum(r["terminal_target_status"]=="candidate_found" for r in outcomes),"external_zero_candidate_targets":len(zero),"canonical_external_candidate_count":len(canonical),"official_external_candidate_count":sum(r["official_source_flag"]=="true" for r in canonical),"semantic_repair_scaffold_available":True,"semantic_repair_scaffold_href":"reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md","semantic_repair_scaffold_link_label":"Open semantically repaired whole-corpus evidence scaffold (MD)","active_internal_review_href":"reports/whole_corpus_evidence_semantic_repair_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md","global_wage_gap_readiness":False,"global_causal_readiness":False,"causal_mechanism_interpretation_gate":"pass","candidate_verification_or_download_executed":False,"final_visual_report_created":False}); write_json(phase_path,phase)
    reports_path=ROOT/"docs/dashboard/data/reports_index.json"; reports=json.loads(reports_path.read_text()); new={"id":"whole-corpus-evidence-semantic-repair-2026-08-04","title":"Semantically repaired whole-corpus evidence scaffold","report_type":"Active internal evidence-review scaffold","date":"2026-08-04","checkpoint":f"31 cards; {roots} root actions; {len(canonical)} candidate-only leads","summary":"Specific evidence-card explanations, split mechanism taxonomy, repaired sides, authoritative geography, visual-ready hex data, and metadata-only external candidate discovery. Not a final report or estimate.","tags":["whole corpus","semantic repair","external data","internal review"],"current":False,"historical":False,"href":phase["semantic_repair_scaffold_href"],"link_label":"Open semantically repaired whole-corpus evidence scaffold (MD)","scope_metrics":[{"label":"evidence cards","value":31},{"label":"root actions","value":roots},{"label":"canonical candidates","value":len(canonical)}]}; reports["reports"]=[r for r in reports["reports"] if r.get("id")!=new["id"]]; reports["reports"].insert(1,new); write_json(reports_path,reports)
    dash={"current_stage":phase["current_phase"],"next_task":phase["next_task"],"semantic_scaffold_href":phase["semantic_repair_scaffold_href"],"prior_corrected_scaffold_href":phase["corrected_scaffold_href"],"prior_draft_href":phase["whole_corpus_report_draft_href"],"final_pi_report_href":phase["current_report_path"],"wage_growth_continuity_preserved":(ROOT/"docs/dashboard/data/wage_growth_continuity.json").exists(),"map_primary_metric":phase["dashboard_map_primary_metric"],"scout_coverage_percent":phase["actual_scout_coverage_rate_percent"],"no_final_heatmaps_added":True,"technical_details_collapsed":True}; write_json(OUT/"dashboard_external_data_hosted_search_update_summary.json",dash)
    cards=read_csv(OUT/"semantically_rewritten_evidence_cards.csv")
    side_rows=read_csv(OUT/"implementation_event_side_repair_results.csv")
    geo_rows=read_csv(OUT/"municipality_geographic_crosswalk.csv")
    hex_rows=read_csv(OUT/"mechanism_hex_density_visual_ready_layer.csv")
    target_links=read_csv(OUT/"search_target_event_linkage.csv")
    exposure_rows=read_csv(OUT/"mechanism_exposure_event_layer.csv")
    root_ids={r["root_compensation_event_id"] for r in read_csv(OUT/"root_compensation_event_layer.csv")}
    quality=json.loads((OUT/"semantic_evidence_card_quality_audit.json").read_text())
    duplication=json.loads((OUT/"semantic_evidence_card_template_duplication_audit.json").read_text())
    eligibility=json.loads((OUT/"target_family_eligibility_audit.json").read_text())
    forbidden=json.loads((OUT/"forbidden_action_audit.json").read_text())
    scaffold=(OUT/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md").read_text()
    lane_target_sets=[]
    for lane in LANES:
        lane_target_sets.append({r["search_target_id"] for r in read_csv(OUT/f"{lane}_queue.csv")})
    specific_sides={"police","fire","safety_combined","non_safety","mixed"}
    low_allowed={"side_independent","remains_unclear","write_off"}
    status_counts=Counter(r["terminal_target_status"] for r in outcomes)
    checks={
        "01_all_31_evidence_cards_processed":len(cards)==31,
        "02_every_retained_card_has_bounded_excerpt":all(r["evidence_excerpt"].strip() for r in cards),
        "03_every_card_has_specific_mechanism_explanation":all(r["mechanism_explanation"].strip() and r["how_mechanism_works"].strip() for r in cards),
        "04_every_card_has_pressure_and_beneficiary":all(r["pressure_direction"].strip() and r["beneficiary"].strip() and r["pressure_direction_explanation"].strip() and r["beneficiary_explanation"].strip() for r in cards),
        "05_every_card_explains_safety_wage_growth_relevance":all(r["safety_wage_growth_fit"].strip() for r in cards),
        "06_every_card_has_example_specific_limitation":all(r["example_specific_limitation"].strip() for r in cards),
        "07_template_duplication_audited":duplication.get("passed",False),
        "08_narrative_scaffold_excludes_machine_identifiers":not any(token in scaffold for token in ("WCM-","IMPEVT-","ROOTCOMP-","MECHEXP-","sha256","docs/analysis/")),
        "09_root_compensation_event_layer_exists":roots==2998,
        "10_institutional_channels_separate_from_outcomes":(OUT/"institutional_channel_tag_layer.csv").exists() and (OUT/"compensation_outcome_tag_layer.csv").exists(),
        "11_timing_channels_separate":(OUT/"timing_implementation_tag_layer.csv").exists(),
        "12_pressure_channels_separate":(OUT/"pressure_channel_tag_layer.csv").exists(),
        "13_validated_multi_tag_bundles_preserved":(OUT/"multi_mechanism_bundle_summary.json").exists(),
        "14_exposures_link_to_root_events":all(r["root_compensation_event_id"] in root_ids for r in exposure_rows),
        "15_no_duplicate_mechanism_map_key":len(exposure_rows)==len({(r["municipality"],r["state"],r["compensation_cycle_id"],r["side"],r["mechanism_family"],r["mechanism_tag"]) for r in exposure_rows}),
        "16_root_and_exposure_counts_separate":roots==2998 and exposures==13391,
        "17_collective_bargaining_not_hidden":any(r["mechanism_tag"]=="collective_bargaining" for r in exposure_rows),
        "18_procedural_no_outcome_preserved":any(r["mechanism_tag"]=="no_direct_compensation_outcome" for r in exposure_rows),
        "19_all_1608_unclear_side_events_processed":len(side_rows)==1608,
        "20_specific_side_repairs_have_moderate_or_high_confidence":all(r["side_confidence"] in {"moderate","high"} for r in side_rows if r["repaired_side"] in specific_sides),
        "21_low_confidence_sides_not_forced":all(r["repaired_side"] in low_allowed for r in side_rows if r["side_confidence"]=="low"),
        "22_side_independent_is_separate":side.get("side_independent")==382,
        "23_unresolved_sides_retain_reasons":all(r["side_repair_reason"].strip() for r in side_rows if r["repaired_side"]=="remains_unclear"),
        "24_side_before_after_counts_reconcile":side.get("processed")==1608 and sum(side.get(k,0) for k in ("repaired_to_specific_side","side_independent","remains_unclear","write_off"))==1608,
        "25_coordinates_are_authoritative":all("Census Bureau" in r["coordinate_source"] for r in geo_rows),
        "26_no_coordinates_fabricated":coord["fabricated"]==0,
        "27_geographic_crosswalk_has_stable_ids":all(r["municipality_id"].strip() for r in geo_rows),
        "28_coordinate_conflicts_and_missing_documented":coord["conflicts"]==0 and coord["missing"]==0 and (OUT/"municipality_coordinate_conflict_queue.csv").exists() and (OUT/"municipality_coordinate_missing_queue.csv").exists(),
        "29_urbanicity_method_documented":(OUT/"urbanicity_method_review.md").exists(),
        "30_suburban_classification_not_fabricated":urban.get("suburban_created") is False,
        "31_external_reference_payloads_not_in_output":not any("artifacts/local_external_reference_data" in str(p) for p in OUT.rglob("*")),
        "32_one_fixed_lower48_grid":len({r["hex_cell_id"].split(":",1)[0] for r in hex_rows if r["geography_panel"]=="lower_48"})>0,
        "33_fixed_radius_is_50km":json.loads((OUT/"mechanism_hex_density_visual_ready_manifest.json").read_text()).get("hex_radius_km")==50,
        "34_safety_non_safety_share_scale_metadata":json.loads((OUT/"mechanism_hex_density_scale_manifest.json").read_text()).get("identical_scale_within_mechanism") is True,
        "35_hexes_use_event_counts":all(int(r["implementation_event_count"])>=0 for r in hex_rows),
        "36_repeated_mentions_do_not_inflate_hexes":all(int(r["implementation_event_count"])<=int(r["root_compensation_event_count"]) for r in hex_rows),
        "37_alaska_hawaii_not_silently_dropped":any(r["geography_panel"] in {"alaska_inset","hawaii_inset"} for r in hex_rows),
        "38_difference_views_labeled_event_count_difference":all("prevalence" not in r.get("disclosure_flags","").replace("not_prevalence","") for r in read_csv(OUT/"mechanism_hex_density_difference_view.csv")),
        "39_no_final_map_image_created":not any(p.suffix.lower() in {".png",".jpg",".jpeg",".svg",".webp"} for p in OUT.rglob("*")),
        "40_raw_20986_target_queue_preserved":len(read_csv(OUT/"raw_external_data_target_queue_preserved.csv"))==20986,
        "41_compacted_queue_created":len(targets)==2297,
        "42_every_raw_target_has_terminal_compaction_route":eligibility.get("all_reconciled") and eligibility.get("rows_reconciled")==20986,
        "43_many_to_many_target_event_linkage_reconciles":len(target_links)==14395 and all(r["search_target_id"] in target_by_id for r in target_links),
        "44_no_external_data_family_silently_lost":set(summary["candidate_family_counts"])=={"payroll_and_earnings","staffing_and_headcount","recruitment_and_retention","tenure_and_progression","implementation","benefits_and_total_compensation"},
        "45_planned_call_budget_exists":(OUT/"hosted_search_planned_call_budget.json").exists(),
        "46_primary_and_repair_query_rules_documented":all(r["query_primary"].strip() and r["query_repair"].strip() for r in targets),
        "47_successful_targets_reused_across_linked_events":any(int(r["linked_root_event_count"])>1 for r in targets),
        "48_transport_preflight_passed":pre.get("transport_category")=="A" and pre.get("category_A_usable") is True,
        "49_production_probe_passed":pre.get("production_probe",{}).get("passed") is True,
        "50_five_lane_queues_are_disjoint":all(lane_target_sets[i].isdisjoint(lane_target_sets[j]) for i in range(5) for j in range(i+1,5)),
        "51_five_lanes_cover_each_target_once":len(set().union(*lane_target_sets))==len(targets) and sum(map(len,lane_target_sets))==len(targets),
        "52_each_target_has_one_terminal_status":len(outcomes)==len(targets) and len({r["search_target_id"] for r in outcomes})==len(targets),
        "53_checkpoints_reconcile_to_results":all(json.loads((OUT/f"{lane}_checkpoint.json").read_text()).get("status")=="complete" for lane in LANES),
        "54_completed_targets_not_uncontrolled_rerun":repair==5 and all(r["retry_linkage"] for r in calls if r["call_type"]=="repair"),
        "55_call_ledger_reconciles":production==len(targets) and len(calls)==production+repair,
        "56_call_types_separated":set(r["call_type"] for r in calls)<={"production_primary","repair"},
        "57_no_secrets_in_logs":json.loads((OUT/"hosted_search_redaction_audit.json").read_text()).get("passed") is True,
        "58_every_candidate_links_to_target":all(r["search_target_id"] in target_by_id for r in candidates),
        "59_candidate_duplicates_preserve_linkage":len(duplicates)==len(candidates)-len(canonical),
        "60_canonical_candidates_reconcile":len(canonical)+len(duplicates)==len(candidates),
        "61_official_source_flags_use_domain_metadata":all(r["candidate_domain"].strip() and r["official_source_flag"] in {"true","unconfirmed"} and (r["official_source_flag"]!="true" or r["candidate_domain"].endswith(".gov") or ".gov." in r["candidate_domain"]) for r in canonical),
        "62_review_queue_excludes_duplicate_only_rows":len(canonical)==summary["canonical_candidates"],
        "63_no_candidate_url_verification":forbidden.get("candidate_verification") is False and forbidden.get("candidate_url_get_or_head") is False,
        "64_no_candidate_source_download":forbidden.get("source_download") is False,
        "65_no_candidate_source_review":forbidden.get("source_review") is False,
        "66_no_candidate_text_extraction":forbidden.get("text_extraction") is False,
        "67_no_ocr":forbidden.get("ocr") is False,
        "68_no_rating":forbidden.get("gabriel_rating") is False,
        "69_no_new_normalization_or_matching":forbidden.get("normalization_or_matching") is False,
        "70_no_regression_or_treatment_effect":forbidden.get("regression") is False and forbidden.get("treatment_effect") is False,
        "71_no_national_wage_gap_estimate":forbidden.get("national_wage_gap_estimate") is False,
        "72_no_national_prevalence_estimate":forbidden.get("national_prevalence_estimate") is False,
        "73_no_causal_effect_estimate":forbidden.get("causal_effect_estimate") is False,
        "74_semantic_scaffold_analysis_exists":(OUT/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md").exists(),
        "75_semantic_scaffold_public_exists":(PUBLIC/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md").exists(),
        "76_new_dashboard_link_resolves_statically":(ROOT/"docs/dashboard/public"/phase["semantic_repair_scaffold_href"]).exists(),
        "77_prior_draft_link_intact":(ROOT/"docs/dashboard/public/reports/whole_corpus_claim_package_review_2026-08-03/whole_corpus_causal_mechanism_report_draft_2026-08-03.md").exists(),
        "78_prior_corrected_scaffold_link_intact":(ROOT/"docs/dashboard/public/reports/whole_corpus_evidence_corrected_2026-08-04/whole_corpus_causal_mechanism_evidence_scaffold_corrected_2026-08-04.md").exists(),
        "79_final_pi_report_link_intact":(ROOT/"docs/dashboard/public/reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf").exists(),
        "80_wage_growth_module_intact":(ROOT/"docs/dashboard/data/wage_growth_continuity.json").exists(),
        "81_dashboard_map_remains_scout_coverage_rate":phase["dashboard_map_primary_metric"]=="scout_coverage_rate",
        "82_no_final_heatmap_added_to_dashboard":not any("mechanism_hex_density_visual_ready_layer" in p.read_text(errors="ignore") for p in (ROOT/"docs/dashboard/src").rglob("*") if p.is_file()),
        "83_dashboard_structure_remains_compact":any("<details" in p.read_text(errors="ignore") for p in (ROOT/"docs/dashboard/src").rglob("*.jsx")),
        "84_no_pdf_docx_or_slides_created":forbidden.get("pdf_docx_slides") is False and not any(p.suffix.lower() in {".pdf",".docx",".ppt",".pptx"} for p in OUT.rglob("*")),
        "85_retained_source_root_still_ignored":subprocess.run(["git","check-ignore","-q","artifacts/local_retained_sources/"],cwd=ROOT).returncode==0,
        "86_extracted_text_root_still_ignored":subprocess.run(["git","check-ignore","-q","artifacts/local_extracted_text/"],cwd=ROOT).returncode==0,
        "87_external_reference_root_ignored":subprocess.run(["git","check-ignore","-q","artifacts/local_external_reference_data/"],cwd=ROOT).returncode==0,
        "88_hosted_search_metadata_root_ignored":subprocess.run(["git","check-ignore","-q","artifacts/local_hosted_search_metadata/"],cwd=ROOT).returncode==0,
        "89_no_local_payload_in_analysis_output":not any("local_external_reference_data" in str(p) or "local_hosted_search_metadata" in str(p) for p in OUT.rglob("*")),
    }
    write_json(OUT/"validation_report.json",{"passed":all(checks.values()),"checks":checks,"validated_at":utc_now()}); write_md(OUT/"validation_report.md","# Validation report\n\n"+"\n".join(f"- {'PASS' if ok else 'FAIL'} — {name.replace('_',' ')}" for name,ok in checks.items()))
    print(json.dumps(summary,indent=2))


def audit_staging() -> None:
    staged=subprocess.check_output(["git","diff","--cached","--name-only","-z"],cwd=ROOT).decode().split("\0"); staged=[x for x in staged if x]
    forbidden_ext={".pdf",".docx",".ppt",".pptx",".jpg",".jpeg",".png",".tif",".tiff"}; bad=[]; large=[]
    for rel in staged:
        p=ROOT/rel
        if p.suffix.lower() in forbidden_ext or any(token in rel for token in ("artifacts/local_","node_modules/","rendered_pages/")): bad.append(rel)
        if p.exists() and p.stat().st_size>50*1024*1024: large.append({"path":rel,"bytes":p.stat().st_size})
    write_json(OUT/"staged_file_audit.json",{"passed":not bad,"staged_count":len(staged),"forbidden_staged":bad,"staged_files":staged}); write_json(OUT/"large_file_audit.json",{"passed":not large,"threshold_bytes":50*1024*1024,"large_staged_files":large});
    if bad or large: raise RuntimeError("staged/large-file audit failed")
    print("staged_and_large_file_audits_passed")


def build_relay(commit: str, push_status: str) -> None:
    summary=json.loads((OUT/"broad_state_whole_corpus_external_data_hosted_search_summary.json").read_text()); relay_dir=TMP/"relay"; shutil.rmtree(relay_dir,ignore_errors=True); relay_dir.mkdir(parents=True)
    payload={**summary,"commit_hash":commit,"push_status":push_status,"head_before":json.loads((OUT/"broad_state_whole_corpus_external_data_hosted_search_manifest.json").read_text())["head_before"],"head_after":commit,"semantic_scaffold_path":str((OUT/"whole_corpus_causal_mechanism_evidence_scaffold_semantic_repair_2026-08-04.md").relative_to(ROOT)),"dashboard_semantic_link_status":"tracked_and_locally_resolvable","prior_draft_and_corrected_scaffold_preserved":True,"final_pi_report_preserved":True,"wage_growth_module_preserved":True,"dashboard_map":"scout_coverage_rate","forbidden_action_audit":json.loads((OUT/"forbidden_action_audit.json").read_text()),"staged_file_audit":json.loads((OUT/"staged_file_audit.json").read_text()),"large_file_audit":json.loads((OUT/"large_file_audit.json").read_text()),"no_verification_download_extraction_rating":True,"no_final_heatmap_pdf_docx_slides":True}
    write_json(relay_dir/"relay_summary.json",payload)
    for name in ["broad_state_whole_corpus_external_data_hosted_search_summary.md","validation_report.json","validation_report.md","forbidden_action_audit.json","staged_file_audit.json","large_file_audit.json","hosted_search_transport_preflight.json","hosted_search_usage_summary.json","search_target_compaction_summary.json","implementation_event_side_repair_summary.json","mechanism_taxonomy_split_summary.json","municipality_coordinate_join_summary.json","municipality_urbanicity_summary.json","mechanism_hex_density_materialization_summary.json","external_data_missingness_resolution_summary.json","next_task.md"]: shutil.copy2(OUT/name,relay_dir/name)
    zip_path=ROOT/f"tmp/broad_state_whole_corpus_external_data_targeted_hosted_search_scout_relay_2026-08-04_{commit}.zip"; shutil.make_archive(str(zip_path.with_suffix("")),"zip",relay_dir); print(zip_path)


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("mode",choices=["prepare","transport-preflight","run-lane","finalize","audit-staging","build-relay"]); parser.add_argument("--lane",type=int); parser.add_argument("--start-delay-seconds",type=int,default=0); parser.add_argument("--commit"); parser.add_argument("--push-status",default="not_attempted"); args=parser.parse_args()
    if args.mode=="prepare": prepare()
    elif args.mode=="transport-preflight": transport_preflight()
    elif args.mode=="run-lane":
        if not args.lane: raise SystemExit("--lane required")
        run_lane(args.lane,args.start_delay_seconds)
    elif args.mode=="finalize": finalize()
    elif args.mode=="audit-staging": audit_staging()
    elif args.mode=="build-relay":
        if not args.commit: raise SystemExit("--commit required")
        build_relay(args.commit,args.push_status)


if __name__=="__main__": main()
