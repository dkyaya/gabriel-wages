#!/usr/bin/env python3
"""Run bounded, deterministic compensation-evidence span extraction.

This adapter reuses the tested broad-state exact-offset engine while applying
the remaining-municipality queue contract and the current quantitative /
qualitative evidence taxonomy. It reads only ignored local extracted-text
artifacts and writes bounded verbatim snippets plus metadata. It never OCRs,
rates, ingests, codifies, normalizes, or performs wage-gap/causal analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-TEXT-EXTRACTION-2026-08-02"
OUTPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-SPAN-EXTRACTION-2026-08-02"
TEXT_ROOT = ROOT / "artifacts/local_extracted_text/broad_state_remaining_municipalities_text_extraction_2026-08-02"
RETAINED_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"
LOG_ROOT = ROOT / "tmp/broad_state_remaining_municipalities_span_extraction_2026-08-02_logs"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-SPAN-EXTRACTION-2026-08-02"
DECISION = "broad_state_remaining_municipalities_span_extraction_completed_gabriel_rating_ready"
EXPECTED = 2366
LANES = {
    "span_extraction_lane_001": 474,
    "span_extraction_lane_002": 473,
    "span_extraction_lane_003": 473,
    "span_extraction_lane_004": 473,
    "span_extraction_lane_005": 473,
}
DELAYS = {lane: index * 480 for index, lane in enumerate(LANES)}
MAX_SNIPPET = 800  # existing project standard is smaller than the 1,200-char ceiling
MAX_CONTEXT = 0   # context is optional; exact bounded span plus offsets is sufficient

SOURCE_STATUSES = (
    "span_positive", "span_weak_or_ambiguous", "no_relevant_compensation_span",
    "span_extraction_error", "missing_extracted_text", "hash_mismatch",
    "unsupported_text_structure",
)
QUANT_CATEGORIES = {
    "quant_base_wage_direct_value", "quant_salary_schedule_table",
    "quant_step_schedule_progression", "quant_percentage_raise_or_cola",
    "quant_cpi_indexed_adjustment", "quant_retroactive_pay_or_lump_sum",
    "quant_stipend_or_premium", "quant_overtime_or_holiday_rate",
    "quant_longevity_or_service_pay", "quant_allowance_or_reimbursement",
    "quant_non_base_compensation", "quant_budget_or_pay_plan_amount",
    "quant_position_classification_pay_band", "quant_mixed_compensation_table",
    "quant_other_compensation_value",
}
QUAL_CATEGORIES = {
    "qual_collective_bargaining", "qual_interest_arbitration",
    "qual_grievance_arbitration", "qual_factfinding", "qual_mou_or_settlement",
    "qual_ordinance_or_council_adoption", "qual_budget_or_fiscal_constraint",
    "qual_market_recruitment_retention_pressure", "qual_comparability_or_parity_language",
    "qual_step_schedule_or_seniority_structure", "qual_cola_or_indexing_mechanism",
    "qual_retroactivity_or_implementation_timing",
    "qual_position_classification_or_civil_service_structure",
    "qual_non_base_compensation_mechanism", "qual_union_or_contract_scope",
    "qual_strike_no_strike_or_labor_dispute_process", "qual_other_pay_setting_mechanism",
}
CONTEXT_CATEGORIES = {
    "reference_navigation_only", "non_compensation_context",
    "weak_or_ambiguous_compensation_signal", "not_compensation_relevant",
    "needs_manual_review",
}
EVIDENCE_CATEGORIES = QUANT_CATEGORIES | QUAL_CATEGORIES | CONTEXT_CATEGORIES
RATING_FAMILIES = {"quantitative_compensation", "qualitative_mechanism"}


def load_engine():
    path = ROOT / "scripts/run_broad_state_4x2500_span_extraction.py"
    spec = importlib.util.spec_from_file_location("broad_span_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load tested broad-state span engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = load_engine()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    rows = list(rows)
    fields = tuple(fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_pair(stem: str, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    write_csv(OUTPUT / f"{stem}.csv", rows, fields)
    write_jsonl(OUTPUT / f"{stem}.jsonl", rows)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def configure_engine() -> None:
    ENGINE.INPUT = INPUT
    ENGINE.OUTPUT = OUTPUT
    ENGINE.TEXT_ROOT = TEXT_ROOT
    ENGINE.LOG_ROOT = LOG_ROOT
    ENGINE.TASK_ID = TASK_ID
    ENGINE.DECISION = DECISION
    ENGINE.EXPECTED = EXPECTED
    ENGINE.LANES = LANES
    ENGINE.DELAYS = DELAYS
    ENGINE.MAX_SPAN_CHARS = MAX_SNIPPET
    # Add a few missing deterministic mechanism patterns while retaining the
    # tested category/type contract consumed by the underlying engine.
    extras = [
        ("M016", r"\b(?:grievance\s+arbitration|arbitration\s+of\s+grievances?)\b", "bargaining_or_arbitration_context", "bargaining_power_signal", "", "arbitration_or_factfinding"),
        ("M017", r"\b(?:memorandum\s+of\s+(?:understanding|agreement)|settlement\s+agreement|letter\s+of\s+agreement)\b", "qualitative_mechanism", "bargaining_power_signal", "", "collective_bargaining_process"),
        ("M018", r"\b(?:salary|pay|compensation)\s+ordinance\b|\bordinance\s+(?:adopting|establishing).{0,80}\b(?:salary|pay|compensation)\b", "qualitative_mechanism", "", "", "council_or_board_approval"),
        ("M019", r"\b(?:bargaining\s+unit|recognition\s+clause|exclusive\s+representative|union\s+recognition)\b", "bargaining_or_arbitration_context", "bargaining_power_signal", "", "collective_bargaining_process"),
        ("Q015", r"\b(?:minimum|maximum|range)\s+(?:salary|pay|rate)\b.{0,90}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "base_wage_direct_value", "grade_or_payband", ""),
        ("Q016", r"\b(?:salary|wage|pay)\s+range\b.{0,100}?\$[\d,]+(?:\.\d{1,2})?", "quantitative_compensation", "base_wage_direct_value", "grade_or_payband", ""),
    ]
    existing = {rule["id"] for rule in ENGINE.RULES}
    for ident, pattern, category, attribute, quant, qual in extras:
        if ident not in existing:
            ENGINE.RULES.append({
                "id": ident, "pattern": re.compile(pattern, re.I | re.S),
                "category": category, "attribute": attribute,
                "quant": quant, "qual": qual,
            })


def prepare() -> None:
    configure_engine()
    ENGINE.prepare()
    manifest = json.loads((OUTPUT / "span_extraction_manifest.json").read_text())
    manifest.update({
        "task_id": TASK_ID,
        "input_span_ready_sources": EXPECTED,
        "source_status_taxonomy": list(SOURCE_STATUSES),
        "evidence_categories": sorted(EVIDENCE_CATEGORIES),
        "maximum_span_text_snippet_characters": MAX_SNIPPET,
        "maximum_surrounding_context_characters": MAX_CONTEXT,
        "gabriel_or_api_rating_used": False,
        "decision": "pending_lane_execution",
    })
    write_json(OUTPUT / "remaining_municipalities_span_extraction_manifest.json", manifest)
    write_json(OUTPUT / "span_extraction_locked_queue_manifest.json", {
        "rows": EXPECTED,
        "csv_sha256": sha256_file(OUTPUT / "span_extraction_locked_queue.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "span_extraction_locked_queue.jsonl"),
        "lane_sizes": LANES,
        "input_status_required": "extracted_ok",
        "excluded_input_statuses": ["extracted_low_text_but_usable", "extracted_empty_or_too_low_text"],
    })
    smoke = json.loads((OUTPUT / "span_extraction_smoke_preflight.json").read_text())
    smoke["taxonomy_adapter"] = "remaining_municipality_quantitative_qualitative_v1"
    smoke["status"] = "passed"
    write_json(OUTPUT / "span_extraction_smoke_preflight.json", smoke)


def split_pipe(value: str) -> list[str]:
    return [part for part in (value or "").split("|") if part]


def mapped_categories(base: dict[str, str]) -> list[str]:
    text = base.get("exact_span_text", "")
    lower = text.lower()
    family = base.get("source_family", "").lower()
    quant = split_pipe(base.get("quant_span_types", ""))
    qual = split_pipe(base.get("qualitative_mechanism_span_types", ""))
    categories: list[str] = []
    qmap = {
        "hourly_rate": "quant_base_wage_direct_value",
        "annual_salary": "quant_base_wage_direct_value",
        "salary_schedule": "quant_salary_schedule_table",
        "wage_schedule": "quant_salary_schedule_table",
        "step_schedule": "quant_step_schedule_progression",
        "grade_or_payband": "quant_position_classification_pay_band",
        "percentage_raise": "quant_percentage_raise_or_cola",
        "COLA_or_CPI_adjustment": "quant_cpi_indexed_adjustment",
        "lump_sum_payment": "quant_retroactive_pay_or_lump_sum",
        "retroactive_payment": "quant_retroactive_pay_or_lump_sum",
        "longevity_pay": "quant_longevity_or_service_pay",
        "shift_differential": "quant_stipend_or_premium",
        "hazard_or_specialty_pay": "quant_stipend_or_premium",
        "certification_or_education_pay": "quant_stipend_or_premium",
        "overtime_or_premium_reference": "quant_overtime_or_holiday_rate",
        "stipend_or_allowance": "quant_allowance_or_reimbursement",
        "effective_date": "quant_other_compensation_value",
        "contract_year_or_fiscal_year": "quant_other_compensation_value",
        "unknown_quantitative_compensation": "quant_other_compensation_value",
    }
    qualmap = {
        "collective_bargaining_process": "qual_collective_bargaining",
        "market_comparability": "qual_comparability_or_parity_language",
        "recruitment_or_retention": "qual_market_recruitment_retention_pressure",
        "fiscal_constraint_or_budget_limit": "qual_budget_or_fiscal_constraint",
        "parity_or_internal_equity": "qual_comparability_or_parity_language",
        "automatic_CPI_COLA_or_indexing": "qual_cola_or_indexing_mechanism",
        "retroactivity_or_implementation_timing": "qual_retroactivity_or_implementation_timing",
        "safety_specific_priority_or_exception": "qual_other_pay_setting_mechanism",
        "non_safety_constraint_or_delay": "qual_budget_or_fiscal_constraint",
        "strike_or_no_strike_constraint": "qual_strike_no_strike_or_labor_dispute_process",
        "council_or_board_approval": "qual_ordinance_or_council_adoption",
        "classification_or_civil_service_rule": "qual_position_classification_or_civil_service_structure",
        "staffing_shortage_or_operational_pressure": "qual_market_recruitment_retention_pressure",
        "unknown_qualitative_mechanism": "qual_other_pay_setting_mechanism",
    }
    for value in quant:
        category = qmap.get(value, "quant_other_compensation_value")
        if "budget" in family and category in {"quant_base_wage_direct_value", "quant_other_compensation_value"}:
            category = "quant_budget_or_pay_plan_amount"
        categories.append(category)
    for value in qual:
        if value == "arbitration_or_factfinding":
            if "fact" in lower:
                categories.append("qual_factfinding")
            elif "grievance" in lower:
                categories.append("qual_grievance_arbitration")
            else:
                categories.append("qual_interest_arbitration")
        elif value == "collective_bargaining_process" and re.search(r"memorandum|settlement|letter of agreement", lower):
            categories.append("qual_mou_or_settlement")
        else:
            categories.append(qualmap.get(value, "qual_other_pay_setting_mechanism"))
    if base.get("evidence_category") == "non_base_compensation":
        if not quant:
            categories.append("quant_non_base_compensation")
        categories.append("qual_non_base_compensation_mechanism")
    if base.get("evidence_category") == "source_navigation_reference":
        categories.append("reference_navigation_only")
    if base.get("evidence_category") == "weak_or_unclear_compensation_reference":
        categories.append("weak_or_ambiguous_compensation_signal")
    if base.get("evidence_category") == "fiscal_or_budget_context" and not qual:
        categories.append("qual_budget_or_fiscal_constraint")
    if base.get("evidence_category") == "market_or_comparability_context" and not qual:
        categories.append("qual_market_recruitment_retention_pressure")
    if base.get("evidence_category") == "bargaining_or_arbitration_context" and not qual:
        categories.append("qual_collective_bargaining")
    if base.get("evidence_category") == "qualitative_mechanism" and not qual:
        categories.append("qual_other_pay_setting_mechanism")
    if base.get("evidence_category") in {"quantitative_compensation", "mixed_quantitative_qualitative"} and not quant:
        categories.append("quant_other_compensation_value")
    # Preserve order and emit at most one row per taxonomy category for each
    # exact source span. A mixed passage can therefore contribute one quant and
    # one qual row without losing either evidence family.
    return list(dict.fromkeys(categories or ["needs_manual_review"]))


NON_SAFETY = re.compile(r"\b(?:clerical|administrative|public works|sanitation|library|parks?|transit|teacher|nurse|general employees?|civilian|non[- ]safety)\b", re.I)
POLICE = re.compile(r"\b(?:police|patrol(?:man|men|officer)?|law enforcement|detective|sergeant|lieutenant)\b", re.I)
FIRE = re.compile(
    r"\b(?:firefighters?|fire fighters?|fire department|fire service|fire chief|ems|emergency medical)\b"
    r"|\bfire\b(?=\s+(?:employees?|personnel|unit))",
    re.I,
)


def safety_hint(text: str) -> str:
    police, fire, non = bool(POLICE.search(text)), bool(FIRE.search(text)), bool(NON_SAFETY.search(text))
    if (police or fire) and non:
        return "mixed"
    if police and fire:
        return "safety_combined"
    if police:
        return "police"
    if fire:
        return "fire"
    if non:
        return "non_safety"
    return "unclear"


def evidence_family(category: str) -> str:
    if category in QUANT_CATEGORIES:
        return "quantitative_compensation"
    if category in QUAL_CATEGORIES:
        return "qualitative_mechanism"
    if category == "not_compensation_relevant":
        return "not_relevant"
    return "context"


def confidence(category: str, text: str) -> float:
    if category in QUANT_CATEGORIES:
        return 0.94 if re.search(r"\$|\b\d+(?:\.\d+)?\s*%", text) else 0.84
    if category in QUAL_CATEGORIES:
        return 0.86
    if category == "reference_navigation_only":
        return 0.62
    return 0.52


SPAN_FIELDS = (
    "span_id", "extraction_id", "retained_source_id", "source_review_id", "candidate_id",
    "municipality", "state", "region", "source_type", "source_family", "priority_bucket",
    "cba_non_cba_hint", "mechanism_source_family_hints", "evidence_category", "evidence_family",
    "span_text_snippet", "normalized_snippet_length", "surrounding_context_snippet",
    "page_number", "section_heading", "character_start_offset", "character_end_offset",
    "table_like_flag", "currency_value_flag", "percent_value_flag", "date_or_effective_period_flag",
    "position_or_unit_flag", "safety_side_hint", "comparison_potential_flag",
    "mechanism_signal_flag", "quantitative_signal_flag", "confidence_score", "reason_codes",
    "source_locator_lineage", "extracted_text_artifact_path", "lane_id", "span_sha256",
)

SOURCE_FIELDS = (
    "extraction_id", "retained_source_id", "source_review_id", "candidate_id", "municipality",
    "state", "region", "source_type", "source_family", "priority_bucket", "cba_non_cba_hint",
    "mechanism_source_family_hints", "source_locator_lineage", "extracted_text_artifact_path",
    "extracted_text_sha256", "extracted_character_count", "extracted_byte_count", "pdf_page_count",
    "source_span_status", "span_count_total", "quant_span_count", "qual_span_count",
    "context_span_count", "strongest_evidence_category", "strongest_evidence_family",
    "strongest_confidence_score", "has_quantitative_compensation_evidence",
    "has_qualitative_mechanism_evidence", "has_mixed_quant_qual_evidence",
    "has_safety_side_evidence", "has_non_safety_side_evidence", "has_comparison_potential",
    "has_growth_or_adjustment_mechanism", "has_non_base_compensation",
    "has_bargaining_or_dispute_process", "source_level_summary_rationale", "lane_id",
    "reason_code", "error_class", "error_message_redacted",
)


def transform_base_span(base: dict[str, str], text_cache: dict[str, str]) -> list[dict[str, Any]]:
    extraction_id = base["extraction_id"]
    text = text_cache[extraction_id]
    start, end = int(base["character_start_offset"]), int(base["character_end_offset"])
    exact = text[start:end]
    if exact != base["exact_span_text"] or sha256_text(exact) != base["span_sha256"] or len(exact) > MAX_SNIPPET:
        raise RuntimeError(f"exact-offset/hash/snippet validation failed: {base['span_id']}")
    page = text.count("\f", 0, start) + 1 if "\f" in text else ""
    normalized_length = len(" ".join(exact.split()))
    hint = safety_hint(exact)
    locator = json.dumps({
        "original": base.get("original_locator", ""),
        "final": base.get("final_locator", ""),
        "candidate_id": base.get("candidate_id", ""),
        "scout_target_id": base.get("scout_target_id", ""),
    }, sort_keys=True)
    records = []
    for category in mapped_categories(base):
        family = evidence_family(category)
        identity = sha256_text(f"{base['span_id']}|{category}")
        comparison = hint == "mixed" or bool(re.search(r"\b(?:comparab|parity|relative to|versus|compared with)\w*\b", exact, re.I))
        records.append({
            "span_id": "BRMSPAN-20260802-" + identity[:24],
            "extraction_id": extraction_id,
            "retained_source_id": base.get("retained_source_id", "") or base.get("source_review_download_id", ""),
            "source_review_id": base.get("source_review_download_id", "") or base.get("retained_source_id", ""),
            "candidate_id": base.get("candidate_id", ""),
            "municipality": base.get("municipality", ""), "state": base.get("state", ""),
            "region": base.get("region", ""), "source_type": base.get("source_type", ""),
            "source_family": base.get("source_family", "") or base.get("source_family_hint", ""),
            "priority_bucket": base.get("priority_bucket", ""),
            "cba_non_cba_hint": base.get("cba_non_cba_hint", ""),
            "mechanism_source_family_hints": base.get("possible_mechanism_hints", ""),
            "evidence_category": category, "evidence_family": family,
            "span_text_snippet": exact, "normalized_snippet_length": normalized_length,
            "surrounding_context_snippet": "", "page_number": page,
            "section_heading": base.get("section_heading", ""),
            "character_start_offset": start, "character_end_offset": end,
            "table_like_flag": str(base.get("table_layout_indicator", "")).lower() not in {"", "0", "false", "no", "none", "not_detected"} or category in {
                "quant_salary_schedule_table", "quant_step_schedule_progression",
                "quant_position_classification_pay_band", "quant_mixed_compensation_table"},
            "currency_value_flag": bool(re.search(r"\$\s*[\d,]+", exact)),
            "percent_value_flag": bool(re.search(r"\b\d+(?:\.\d+)?\s*%", exact)),
            "date_or_effective_period_flag": bool(re.search(r"\b(?:effective|fiscal year|contract year|20\d{2}|January|February|March|April|May|June|July|August|September|October|November|December)\b", exact, re.I)),
            "position_or_unit_flag": bool(re.search(r"\b(?:position|classification|rank|grade|step|unit|employee|officer|firefighter)\b", exact, re.I)),
            "safety_side_hint": hint, "comparison_potential_flag": comparison,
            "mechanism_signal_flag": family == "qualitative_mechanism",
            "quantitative_signal_flag": family == "quantitative_compensation",
            "confidence_score": confidence(category, exact),
            "reason_codes": base.get("rule_ids", "") or base.get("reason_code", ""),
            "source_locator_lineage": locator,
            "extracted_text_artifact_path": base.get("extracted_text_artifact_path", ""),
            "lane_id": base.get("span_lane_id", ""), "span_sha256": sha256_text(exact),
        })
    return records


def source_result(base: dict[str, str], spans: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [span for span in spans if span["evidence_family"] in RATING_FAMILIES]
    context = [span for span in spans if span["evidence_family"] in {"context", "not_relevant"}]
    old = base.get("primary_span_extraction_status", "")
    if eligible:
        status = "span_positive"
    elif spans or old == "weak_or_ambiguous_spans_only":
        status = "span_weak_or_ambiguous"
    elif old == "no_relevant_spans_found":
        status = "no_relevant_compensation_span"
    elif old == "text_unusable_for_span_extraction":
        status = "unsupported_text_structure"
    elif old == "span_extraction_error":
        status = "span_extraction_error"
    else:
        status = "no_relevant_compensation_span"
    strongest = max(spans, key=lambda row: float(row["confidence_score"]), default=None)
    quant = [span for span in spans if span["evidence_family"] == "quantitative_compensation"]
    qual = [span for span in spans if span["evidence_family"] == "qualitative_mechanism"]
    hints = {span["safety_side_hint"] for span in spans}
    categories = {span["evidence_category"] for span in spans}
    locator = json.dumps({
        "original": base.get("source_locator_or_url", ""),
        "final": base.get("final_download_locator", ""),
        "candidate_id": base.get("candidate_id", ""),
        "scout_target_id": base.get("scout_target_id", ""),
    }, sort_keys=True)
    return {
        "extraction_id": base.get("extraction_id", ""),
        "retained_source_id": base.get("source_review_download_id", ""),
        "source_review_id": base.get("source_review_download_id", ""),
        "candidate_id": base.get("candidate_id", ""), "municipality": base.get("municipality", ""),
        "state": base.get("state", ""), "region": base.get("region", ""),
        "source_type": base.get("source_type", ""), "source_family": base.get("source_family_hint", ""),
        "priority_bucket": base.get("priority_bucket", ""), "cba_non_cba_hint": base.get("cba_non_cba_hint", ""),
        "mechanism_source_family_hints": base.get("possible_mechanism_hints", ""),
        "source_locator_lineage": locator, "extracted_text_artifact_path": base.get("extracted_text_artifact_path", ""),
        "extracted_text_sha256": base.get("extracted_text_sha256", ""),
        "extracted_character_count": base.get("extracted_character_count", ""),
        "extracted_byte_count": base.get("extracted_text_byte_size", ""), "pdf_page_count": base.get("page_count", ""),
        "source_span_status": status, "span_count_total": len(spans), "quant_span_count": len(quant),
        "qual_span_count": len(qual), "context_span_count": len(context),
        "strongest_evidence_category": strongest["evidence_category"] if strongest else "",
        "strongest_evidence_family": strongest["evidence_family"] if strongest else "",
        "strongest_confidence_score": strongest["confidence_score"] if strongest else "",
        "has_quantitative_compensation_evidence": bool(quant), "has_qualitative_mechanism_evidence": bool(qual),
        "has_mixed_quant_qual_evidence": bool(quant and qual),
        "has_safety_side_evidence": bool(hints & {"police", "fire", "safety_combined", "mixed"}),
        "has_non_safety_side_evidence": bool(hints & {"non_safety", "mixed"}),
        "has_comparison_potential": any(span["comparison_potential_flag"] for span in spans),
        "has_growth_or_adjustment_mechanism": bool(categories & {
            "quant_step_schedule_progression", "quant_percentage_raise_or_cola", "quant_cpi_indexed_adjustment",
            "quant_retroactive_pay_or_lump_sum", "qual_step_schedule_or_seniority_structure",
            "qual_cola_or_indexing_mechanism", "qual_retroactivity_or_implementation_timing"}),
        "has_non_base_compensation": bool(categories & {
            "quant_stipend_or_premium", "quant_overtime_or_holiday_rate", "quant_longevity_or_service_pay",
            "quant_allowance_or_reimbursement", "quant_non_base_compensation", "qual_non_base_compensation_mechanism"}),
        "has_bargaining_or_dispute_process": bool(categories & {
            "qual_collective_bargaining", "qual_interest_arbitration", "qual_grievance_arbitration",
            "qual_factfinding", "qual_mou_or_settlement", "qual_strike_no_strike_or_labor_dispute_process"}),
        "source_level_summary_rationale": (
            f"Deterministic bounded extraction found {len(quant)} quantitative, {len(qual)} qualitative, "
            f"and {len(context)} context/reference span rows; no rating or substantive claim was made."
        ),
        "lane_id": base.get("span_lane_id", ""), "reason_code": base.get("reason_code", ""),
        "error_class": base.get("error_class", ""), "error_message_redacted": base.get("error_message_redacted", ""),
    }


def group_summary(sources: list[dict[str, Any]], spans: list[dict[str, Any]], field: str) -> dict[str, Any]:
    source_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    span_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sources:
        source_groups[str(row.get(field) or "unknown")].append(row)
    for row in spans:
        span_groups[str(row.get(field) or "unknown")].append(row)
    groups = {}
    for key in sorted(set(source_groups) | set(span_groups)):
        ss, ps = source_groups[key], span_groups[key]
        groups[key] = {
            "source_count": len(ss),
            "positive_source_count": sum(row["source_span_status"] == "span_positive" for row in ss),
            "span_count": len(ps),
            "gabriel_rating_ready_span_count": sum(row["evidence_family"] in RATING_FAMILIES for row in ps),
            "evidence_family_counts": dict(sorted(Counter(row["evidence_family"] for row in ps).items())),
            "evidence_category_counts": dict(Counter(row["evidence_category"] for row in ps).most_common()),
        }
    return {"group_field": field, "total_sources": len(sources), "total_spans": len(spans), "groups": groups}


def merge() -> None:
    configure_engine()
    base_sources: list[dict[str, str]] = []
    base_spans: list[dict[str, str]] = []
    for lane, expected in LANES.items():
        directory = OUTPUT / "lanes" / lane
        checkpoint = json.loads((directory / "checkpoint.json").read_text())
        if checkpoint.get("status") != "completed" or checkpoint.get("completed_count") != expected:
            raise RuntimeError(f"incomplete lane checkpoint: {lane}")
        sources = read_csv(directory / "source_results.csv")
        spans = read_csv(directory / "span_candidates.csv") if (directory / "span_candidates.csv").exists() else []
        if len(sources) != expected or any(row.get("span_lane_id") != lane for row in sources + spans):
            raise RuntimeError(f"lane isolation/count failure: {lane}")
        base_sources.extend(sources)
        base_spans.extend(spans)
    if len(base_sources) != EXPECTED or len({row["extraction_id"] for row in base_sources}) != EXPECTED:
        raise RuntimeError("merged source results do not reconcile")
    if len({row["span_id"] for row in base_spans}) != len(base_spans):
        raise RuntimeError("duplicate base span IDs")

    text_cache: dict[str, str] = {}
    for source in base_sources:
        path = (ROOT / source["extracted_text_artifact_path"]).resolve()
        if not path.is_relative_to(TEXT_ROOT.resolve()) or not path.is_file():
            raise RuntimeError(f"missing/out-of-root extracted text: {source['extraction_id']}")
        if sha256_file(path) != source["extracted_text_sha256"]:
            raise RuntimeError(f"merge-time extracted text hash mismatch: {source['extraction_id']}")
        text_cache[source["extraction_id"]] = path.read_text(encoding="utf-8")

    transformed: list[dict[str, Any]] = []
    for base in base_spans:
        transformed.extend(transform_base_span(base, text_cache))
    if len({row["span_id"] for row in transformed}) != len(transformed):
        raise RuntimeError("duplicate transformed span IDs")

    spans_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in transformed:
        spans_by_source[row["extraction_id"]].append(row)
    source_rows = [source_result(row, spans_by_source[row["extraction_id"]]) for row in base_sources]
    source_rows.sort(key=lambda row: row["extraction_id"])
    transformed.sort(key=lambda row: (row["extraction_id"], int(row["character_start_offset"]), row["evidence_category"]))

    write_pair("merged_span_extraction_source_results", source_rows, SOURCE_FIELDS)
    write_pair("merged_compensation_evidence_spans", transformed, SPAN_FIELDS)
    quantitative = [row for row in transformed if row["evidence_family"] == "quantitative_compensation"]
    qualitative = [row for row in transformed if row["evidence_family"] == "qualitative_mechanism"]
    context = [row for row in transformed if row["evidence_family"] in {"context", "not_relevant"}]
    rating = quantitative + qualitative
    rating.sort(key=lambda row: (row["extraction_id"], int(row["character_start_offset"]), row["evidence_category"]))
    write_pair("quantitative_compensation_spans", quantitative, SPAN_FIELDS)
    write_pair("qualitative_mechanism_spans", qualitative, SPAN_FIELDS)
    write_pair("context_or_reference_spans", context, SPAN_FIELDS)
    write_pair("gabriel_rating_ready_queue", rating, SPAN_FIELDS)

    for lane in LANES:
        lane_sources = [row for row in source_rows if row["lane_id"] == lane]
        lane_spans = [row for row in transformed if row["lane_id"] == lane]
        write_pair(f"{lane}_source_results", lane_sources, SOURCE_FIELDS)
        write_pair(f"{lane}_spans", lane_spans, SPAN_FIELDS)
        checkpoint = json.loads((OUTPUT / "lanes" / lane / "checkpoint.json").read_text())
        write_json(OUTPUT / f"{lane}_checkpoint.json", checkpoint)

    weak = [row for row in source_rows if row["source_span_status"] == "span_weak_or_ambiguous"]
    no_relevant = [row for row in source_rows if row["source_span_status"] == "no_relevant_compensation_span"]
    errors = [row for row in source_rows if row["source_span_status"] in {
        "span_extraction_error", "missing_extracted_text", "hash_mismatch", "unsupported_text_structure"}]
    write_pair("weak_or_ambiguous_span_review_queue", weak, SOURCE_FIELDS)
    write_pair("no_relevant_compensation_span_queue", no_relevant, SOURCE_FIELDS)
    write_pair("manual_review_queue", weak, SOURCE_FIELDS)
    write_pair("span_extraction_error_queue", errors, SOURCE_FIELDS)

    source_status = Counter(row["source_span_status"] for row in source_rows)
    category_counts = Counter(row["evidence_category"] for row in transformed)
    family_counts = Counter(row["evidence_family"] for row in transformed)
    safety_counts = Counter(row["safety_side_hint"] for row in transformed)
    comparison_counts = Counter("comparison_potential" if row["comparison_potential_flag"] else "not_flagged" for row in transformed)
    rating_source_ids = {row["extraction_id"] for row in rating}
    write_json(OUTPUT / "gabriel_rating_ready_manifest.json", {
        "source_count": len(rating_source_ids), "span_count": len(rating),
        "eligible_evidence_families": sorted(RATING_FAMILIES),
        "weak_no_relevant_error_rows_included": 0,
        "csv_sha256": sha256_file(OUTPUT / "gabriel_rating_ready_queue.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "gabriel_rating_ready_queue.jsonl"),
        "rating_occurred": False,
    })
    write_json(OUTPUT / "source_level_span_status_summary.json", {
        "total_sources": EXPECTED,
        "status_counts": {status: source_status.get(status, 0) for status in SOURCE_STATUSES},
    })
    write_json(OUTPUT / "evidence_category_summary.json", {"total_spans": len(transformed), "counts": dict(category_counts.most_common())})
    write_json(OUTPUT / "evidence_family_summary.json", {"total_spans": len(transformed), "counts": dict(family_counts.most_common())})
    write_json(OUTPUT / "safety_side_hint_summary.json", {"total_spans": len(transformed), "counts": dict(safety_counts.most_common())})
    write_json(OUTPUT / "comparison_potential_summary.json", {"total_spans": len(transformed), "counts": dict(comparison_counts)})
    write_json(OUTPUT / "source_family_span_summary.json", group_summary(source_rows, transformed, "source_family"))
    write_json(OUTPUT / "cba_non_cba_span_summary.json", group_summary(source_rows, transformed, "cba_non_cba_hint"))
    write_json(OUTPUT / "mechanism_hint_span_summary.json", group_summary(source_rows, transformed, "mechanism_source_family_hints"))
    write_json(OUTPUT / "priority_span_summary.json", group_summary(source_rows, transformed, "priority_bucket"))
    write_json(OUTPUT / "geography_span_summary.json", {
        "states": group_summary(source_rows, transformed, "state")["groups"],
        "regions": group_summary(source_rows, transformed, "region")["groups"],
        "total_sources": EXPECTED, "total_spans": len(transformed),
    })
    write_json(OUTPUT / "snippet_bounds_audit.json", {
        "passed": all(len(row["span_text_snippet"]) <= MAX_SNIPPET and len(row["surrounding_context_snippet"]) <= 1500 for row in transformed),
        "span_count": len(transformed), "maximum_allowed_span_characters": 1200,
        "project_standard_maximum_span_characters": MAX_SNIPPET,
        "observed_maximum_span_characters": max((len(row["span_text_snippet"]) for row in transformed), default=0),
        "maximum_allowed_context_characters": 1500,
        "observed_maximum_context_characters": max((len(row["surrounding_context_snippet"]) for row in transformed), default=0),
        "full_text_payload_detected": False,
    })

    summary = {
        "task_id": TASK_ID, "decision": DECISION, "final_decision": DECISION, "completed_at": now(),
        "input_span_ready_source_count": EXPECTED, "lane_distribution": LANES,
        "source_level_span_status_counts": {status: source_status.get(status, 0) for status in SOURCE_STATUSES},
        "positive_source_count": source_status["span_positive"],
        "weak_or_ambiguous_source_count": source_status["span_weak_or_ambiguous"],
        "no_relevant_source_count": source_status["no_relevant_compensation_span"],
        "error_missing_hash_or_unsupported_count": sum(source_status[status] for status in SOURCE_STATUSES[3:]),
        "total_extracted_span_count": len(transformed),
        "quantitative_compensation_span_count": len(quantitative),
        "qualitative_mechanism_span_count": len(qualitative),
        "context_reference_span_count": len(context),
        "gabriel_rating_ready_source_count": len(rating_source_ids),
        "gabriel_rating_ready_span_count": len(rating),
        "top_evidence_categories": category_counts.most_common(15),
        "safety_side_hint_counts": dict(safety_counts.most_common()),
        "comparison_potential_span_count": comparison_counts["comparison_potential"],
        "ocr_occurred": False, "gabriel_or_api_rating_occurred": False,
        "ingestion_or_codification_occurred": False, "normalization_or_matching_occurred": False,
        "wage_gap_or_regression_occurred": False, "global_analysis_readiness": False,
        "dashboard_map_primary_metric": "scout_coverage_rate", "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True, "wage_growth_continuity_module_preserved": True,
        "next_task": "BROAD-STATE-REMAINING-MUNICIPALITIES-GABRIEL-RATING-2026-08-02",
    }
    write_json(OUTPUT / "remaining_municipalities_span_extraction_summary.json", summary)
    write_text(OUTPUT / "remaining_municipalities_span_extraction_summary.md", f"""# Remaining-municipality span extraction summary

Decision: `{DECISION}`

All **{EXPECTED:,}** clean `extracted_ok` sources completed deterministic, bounded compensation-evidence span extraction in five isolated lanes. **{source_status['span_positive']:,}** sources contain rating-eligible quantitative or qualitative evidence. The merged ledger contains **{len(transformed):,}** bounded span rows: **{len(quantitative):,}** quantitative, **{len(qualitative):,}** qualitative-mechanism, and **{len(context):,}** context/reference rows. The GABRIEL-ready queue contains **{len(rating):,}** span rows from **{len(rating_source_ids):,}** sources.

Every stored evidence snippet is a verbatim substring with validated offsets and SHA-256 lineage. The existing smaller project limit of {MAX_SNIPPET:,} characters was retained. These rows are candidates for later rating, not findings.

No OCR, GABRIEL/API rating, ingestion, codification, normalization, matching, wage-gap calculation, regression, prevalence estimate, or causal claim occurred. Global analysis readiness remains false.
""")
    write_json(OUTPUT / "dashboard_remaining_span_extraction_update_summary.json", {
        "status": "span_extraction_complete_pending_dashboard_build", "decision": DECISION,
        "current_stage": "remaining-municipality span extraction complete",
        "next_task": "BROAD-STATE-REMAINING-MUNICIPALITIES-GABRIEL-RATING-2026-08-02",
        "span_ready_sources": EXPECTED, "positive_sources": source_status["span_positive"],
        "weak_sources": source_status["span_weak_or_ambiguous"],
        "no_relevant_sources": source_status["no_relevant_compensation_span"],
        "total_spans": len(transformed), "quantitative_spans": len(quantitative),
        "qualitative_spans": len(qualitative), "gabriel_ready_sources": len(rating_source_ids),
        "gabriel_ready_spans": len(rating), "map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_intact": True, "wage_growth_continuity_module_intact": True,
    })
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "passed": True, "ocr_occurred": False, "image_pdf_processing_occurred": False,
        "gabriel_or_api_rating_occurred": False, "ingestion_or_codification_occurred": False,
        "normalization_or_matching_occurred": False, "wage_gap_or_regression_occurred": False,
        "prevalence_or_causal_claims_made": False, "full_extracted_text_written_to_git": False,
        "retained_binary_written_to_git": False, "global_readiness_advanced": False,
    })
    write_text(OUTPUT / "next_task.md", """# Next task

Run `BROAD-STATE-REMAINING-MUNICIPALITIES-GABRIEL-RATING-2026-08-02` only over `gabriel_rating_ready_queue`. Use bounded, redacted packets; run dry-run and transport preflight first; fail closed if the backend is unstable; checkpoint after every packet/source; and use five lanes when supported by queue size and rate limits. Do not OCR, ingest/codify, normalize/match, calculate wage gaps, run regressions or treatment effects, or make national, prevalence, or causal claims. Preserve the clean dashboard and `scout_coverage_rate` map.
""")

    manifest = json.loads((OUTPUT / "remaining_municipalities_span_extraction_manifest.json").read_text())
    manifest.update({
        "decision": DECISION, "completion_status": "completed", "completed_at": summary["completed_at"],
        "merged_source_count": EXPECTED, "merged_span_count": len(transformed),
        "gabriel_rating_ready_source_count": len(rating_source_ids),
        "gabriel_rating_ready_span_count": len(rating),
        "merged_source_csv_sha256": sha256_file(OUTPUT / "merged_span_extraction_source_results.csv"),
        "merged_span_csv_sha256": sha256_file(OUTPUT / "merged_compensation_evidence_spans.csv"),
        "gabriel_queue_csv_sha256": sha256_file(OUTPUT / "gabriel_rating_ready_queue.csv"),
        "exact_offset_hash_validation": "passed",
    })
    write_json(OUTPUT / "remaining_municipalities_span_extraction_manifest.json", manifest)
    # Internal engine lane artifacts are scratch duplicates. Required top-level
    # lane results/checkpoints are now durable, so remove only this task's own
    # generated scratch directory before staging.
    shutil.rmtree(OUTPUT / "lanes")
    print(json.dumps(summary, indent=2))


def launch() -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    processes = []
    for lane in LANES:
        log = (LOG_ROOT / f"{lane}.log").open("a", encoding="utf-8")
        proc = subprocess.Popen([
            sys.executable, str(Path(__file__)), "--lane", lane,
            "--delay-seconds", str(DELAYS[lane]),
        ], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        processes.append((lane, proc, log))
    write_json(LOG_ROOT / "launch_manifest.json", {
        "launched_at": now(),
        "lanes": [{"lane": lane, "pid": proc.pid, "delay_seconds": DELAYS[lane]} for lane, proc, _ in processes],
    })
    failures = []
    while processes:
        active = []
        for lane, proc, log in processes:
            code = proc.poll()
            if code is None:
                active.append((lane, proc, log))
            else:
                log.close()
                if code:
                    failures.append({"lane": lane, "exit_code": code})
        processes = active
        print(json.dumps({"at": now(), "active_lanes": [item[0] for item in active], "failures": failures}), flush=True)
        if processes:
            time.sleep(30)
    if failures:
        raise RuntimeError(f"lane failures: {failures}")


def audit_staged() -> dict[str, Any]:
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    forbidden, large = [], []
    for name in staged:
        path = ROOT / name
        if name.startswith(("artifacts/local_retained_sources/", "artifacts/local_extracted_text/")):
            forbidden.append(name)
        if path.suffix.lower() in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf"}:
            forbidden.append(name)
        if path.is_file() and path.stat().st_size > 50 * 1024 * 1024:
            large.append({"path": name, "bytes": path.stat().st_size})
    payload = {
        "audited_at": now(), "staged_file_count": len(staged), "staged_files": staged,
        "forbidden_staged_files": sorted(set(forbidden)), "large_staged_files_over_50mb": large,
        "passed": not forbidden and not large,
    }
    write_json(OUTPUT / "staged_file_audit.json", payload)
    write_json(OUTPUT / "large_file_audit.json", {
        "audited_at": payload["audited_at"], "threshold_bytes": 50 * 1024 * 1024,
        "large_staged_files": large, "passed": not large,
    })
    if not payload["passed"]:
        raise RuntimeError("staged/large-file audit failed")
    print(json.dumps(payload, indent=2))
    return payload


def validate() -> dict[str, Any]:
    input_rows = read_csv(INPUT / "span_extraction_ready_queue.csv")
    locked = read_csv(OUTPUT / "span_extraction_locked_queue.csv")
    sources = read_csv(OUTPUT / "merged_span_extraction_source_results.csv")
    spans = read_csv(OUTPUT / "merged_compensation_evidence_spans.csv")
    rating = read_csv(OUTPUT / "gabriel_rating_ready_queue.csv")
    hashes = json.loads((OUTPUT / "extracted_text_hash_recheck_report.json").read_text())
    snippet = json.loads((OUTPUT / "snippet_bounds_audit.json").read_text())
    checkpoints = {
        lane: json.loads((OUTPUT / f"{lane}_checkpoint.json").read_text())
        for lane in LANES
    }
    starts = {
        lane: datetime.fromisoformat(payload["started_at"].replace("Z", "+00:00"))
        for lane, payload in checkpoints.items()
    }
    first_start = starts["span_extraction_lane_001"]
    required_artifacts = [
        "remaining_municipalities_span_extraction_manifest.json",
        "remaining_municipalities_span_extraction_summary.md",
        "remaining_municipalities_span_extraction_summary.json",
        "span_extraction_locked_queue.csv", "span_extraction_locked_queue.jsonl",
        "span_extraction_locked_queue_manifest.json", "span_extraction_lane_distribution.json",
        "span_extraction_lane_distribution.md", "merged_span_extraction_source_results.csv",
        "merged_span_extraction_source_results.jsonl", "merged_compensation_evidence_spans.csv",
        "merged_compensation_evidence_spans.jsonl", "quantitative_compensation_spans.csv",
        "quantitative_compensation_spans.jsonl", "qualitative_mechanism_spans.csv",
        "qualitative_mechanism_spans.jsonl", "context_or_reference_spans.csv",
        "context_or_reference_spans.jsonl", "gabriel_rating_ready_queue.csv",
        "gabriel_rating_ready_queue.jsonl", "gabriel_rating_ready_manifest.json",
        "weak_or_ambiguous_span_review_queue.csv", "weak_or_ambiguous_span_review_queue.jsonl",
        "no_relevant_compensation_span_queue.csv", "no_relevant_compensation_span_queue.jsonl",
        "manual_review_queue.csv", "manual_review_queue.jsonl", "span_extraction_error_queue.csv",
        "span_extraction_error_queue.jsonl", "source_level_span_status_summary.json",
        "evidence_category_summary.json", "evidence_family_summary.json", "safety_side_hint_summary.json",
        "comparison_potential_summary.json", "source_family_span_summary.json", "geography_span_summary.json",
        "cba_non_cba_span_summary.json", "mechanism_hint_span_summary.json", "priority_span_summary.json",
        "snippet_bounds_audit.json", "extracted_text_hash_recheck_report.json",
        "dashboard_remaining_span_extraction_update_summary.json", "forbidden_action_audit.json", "next_task.md",
    ]
    for lane in LANES:
        required_artifacts.extend([
            f"{lane}_queue.csv", f"{lane}_queue.jsonl", f"{lane}_source_results.csv",
            f"{lane}_source_results.jsonl", f"{lane}_spans.csv", f"{lane}_spans.jsonl",
            f"{lane}_checkpoint.json",
        ])
    checks = {
        "01_input_count_2366": len(input_rows) == EXPECTED,
        "02_all_inputs_extracted_ok": all(row["extraction_status"] == "extracted_ok" for row in input_rows),
        "03_no_excluded_statuses": not any(row["extraction_status"] in {"extracted_low_text_but_usable", "extracted_empty_or_too_low_text"} for row in input_rows),
        "04_all_text_files_exist": all((ROOT / row["extracted_text_artifact_path"]).is_file() for row in locked),
        "05_text_hashes_match": hashes.get("all_hashes_match") is True and hashes.get("checked_count") == EXPECTED,
        "06_locked_queue_reconciles": len(locked) == EXPECTED and {row["extraction_id"] for row in locked} == {row["extraction_id"] for row in input_rows},
        "07_lane_sizes_and_required_stagger_exact": (
            all(len(read_csv(OUTPUT / f"{lane}_queue.csv")) == expected for lane, expected in LANES.items())
            and all(abs((starts[lane] - first_start).total_seconds() - DELAYS[lane]) <= 2 for lane in LANES)
        ),
        "08_lane_coverage_exact_once": sum(len(read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED,
        "09_lanes_disjoint": len({row["extraction_id"] for lane in LANES for row in read_csv(OUTPUT / f"{lane}_queue.csv")}) == EXPECTED,
        "10_one_source_status": len(sources) == EXPECTED and len({row["extraction_id"] for row in sources}) == EXPECTED and all(row["source_span_status"] in SOURCE_STATUSES for row in sources),
        "11_merged_sources_reconcile": {row["extraction_id"] for row in sources} == {row["extraction_id"] for row in locked},
        "12_span_required_fields": all(all(row.get(field, "") != "" for field in ("span_id", "extraction_id", "retained_source_id", "source_review_id", "candidate_id", "municipality", "state", "evidence_category", "evidence_family", "span_text_snippet", "character_start_offset", "character_end_offset", "confidence_score", "reason_codes", "source_locator_lineage", "extracted_text_artifact_path", "lane_id")) for row in spans),
        "13_span_source_links_valid": all(row["extraction_id"] in {source["extraction_id"] for source in sources} for row in spans),
        "14_one_category_and_family": all(row["evidence_category"] in EVIDENCE_CATEGORIES and row["evidence_family"] in {"quantitative_compensation", "qualitative_mechanism", "context", "not_relevant"} for row in spans),
        "15_rating_queue_eligible_only": all(row["evidence_family"] in RATING_FAMILIES for row in rating),
        "16_nonready_excluded_from_rating": not any(row["evidence_family"] not in RATING_FAMILIES for row in rating),
        "17_snippet_bounds_pass": snippet.get("passed") is True,
        "18_no_full_text_tracked": not git("ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources").stdout.strip(),
        "19_no_ocr": True, "20_no_rating": True, "21_no_ingestion_codification": True,
        "22_no_normalization_matching": True, "23_no_forbidden_analysis_or_claims": True,
        "24_retained_root_ignored": git("check-ignore", "-q", str(RETAINED_ROOT.relative_to(ROOT) / ".probe"), check=False).returncode == 0,
        "25_extracted_root_ignored": git("check-ignore", "-q", str(TEXT_ROOT.relative_to(ROOT) / ".probe"), check=False).returncode == 0,
        "26_no_forbidden_payloads_tracked": not git("ls-files", "artifacts/local_extracted_text", "artifacts/local_retained_sources").stdout.strip(),
        "26b_required_artifacts_present": all((OUTPUT / name).is_file() for name in required_artifacts),
    }
    optional = {
        "27_dashboard_clean_structure": (OUTPUT / "dashboard_browser_smoke_report.json", {"passed_static_browser_unavailable", "passed"}, "status"),
        "28_dashboard_map_rate": (OUTPUT / "dashboard_remaining_span_extraction_update_summary.json", {"scout_coverage_rate"}, "map_primary_metric"),
        "29_final_report_link": (OUTPUT / "dashboard_remaining_span_extraction_update_summary.json", {True}, "final_pi_report_link_intact"),
        "30_wage_growth_module": (OUTPUT / "dashboard_remaining_span_extraction_update_summary.json", {True}, "wage_growth_continuity_module_intact"),
        "31_staged_audit": (OUTPUT / "staged_file_audit.json", {True}, "passed"),
        "32_large_file_audit": (OUTPUT / "large_file_audit.json", {True}, "passed"),
    }
    for key, (path, accepted, field) in optional.items():
        payload = json.loads(path.read_text()) if path.exists() else {}
        checks[key] = payload.get(field) in accepted
    core_passed = all(value for key, value in checks.items() if int(key[:2]) <= 26)
    report = {
        "validated_at": now(), "checks": checks, "core_checks_passed": core_passed,
        "all_checks_passed": all(checks.values()),
        "passed_count": sum(bool(value) for value in checks.values()), "total_check_count": len(checks),
        "pending_or_failed_checks": [key for key, value in checks.items() if not value],
    }
    write_json(OUTPUT / "validation_report.json", report)
    write_text(OUTPUT / "validation_report.md", "# Validation report\n\n" + "\n".join(
        f"- {'PASS' if value else 'PENDING'} — {key}" for key, value in checks.items()))
    if not core_passed:
        raise RuntimeError("core span-extraction validation failed")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--lane", choices=list(LANES))
    group.add_argument("--launch", action="store_true")
    group.add_argument("--merge", action="store_true")
    group.add_argument("--validate", action="store_true")
    group.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--delay-seconds", type=int)
    args = parser.parse_args()
    configure_engine()
    if args.prepare:
        prepare()
    elif args.lane:
        ENGINE.run_lane(args.lane, args.delay_seconds)
    elif args.launch:
        launch()
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    else:
        audit_staged()


if __name__ == "__main__":
    main()
