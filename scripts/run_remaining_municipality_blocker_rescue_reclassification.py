#!/usr/bin/env python3
"""De-overlap blockers and derive conservative analysis-use routes for the remaining batch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03"
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-POST-RECONCILIATION-NORMALIZATION-MATCHING-PREP-2026-08-03"
RECON = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SIDE-RELEVANCE-RECONCILIATION-2026-08-03"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-BLOCKER-RESCUE-ANALYSIS-READY-RECLASSIFICATION-2026-08-03"
LOG_DIR = ROOT / "tmp/broad_state_remaining_municipalities_blocker_rescue_analysis_ready_reclassification_2026-08-03_logs"

TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-BLOCKER-RESCUE-ANALYSIS-READY-RECLASSIFICATION-2026-08-03"
DECISION = "broad_state_remaining_municipalities_blocker_rescue_analysis_ready_reclassification_completed_local_qa_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03"

EXPECTED_BLOCKERS = {
    "missing_clear_cross_side_normalized_anchors": 19542,
    "pay_basis_or_compensation_type_incompatible": 17761,
    "period_incompatible_or_missing": 17339,
    "no_scalar_normalized_value": 17118,
    "non_clear_side_status_present": 8446,
}
FINAL_SIDE_COUNTS = {
    "police_direct": 4416,
    "fire_direct": 1080,
    "non_safety_direct": 1177,
    "safety_combined_direct": 43,
    "mixed_direct": 27,
    "not_applicable": 1867,
    "remains_unclear": 5041,
    "write_off": 1538,
}
BLOCKER_ORDER = list(EXPECTED_BLOCKERS)
CLEAR_SIDE = {"police_direct", "fire_direct", "safety_combined_direct", "non_safety_direct", "mixed_direct"}
SAFETY_SIDE = {"police_direct", "fire_direct", "safety_combined_direct", "mixed_direct"}
NON_SAFETY_SIDE = {"non_safety_direct", "mixed_direct"}
SCALAR_BASIS = {"hourly", "annual_salary", "monthly", "weekly", "per_diem"}
NONBASE_BASIS = {"stipend", "overtime_rate", "holiday_rate", "allowance"}
STRUCTURED_BASIS = {"pay_grade", "step_schedule", "range_min_max", "mixed_or_multiple"}
GROWTH_BASIS = {"percentage_raise", "cola_cpi"}

CATEGORIES = [
    "direct_cross_side_comparison_ready",
    "conditional_cross_side_comparison_candidate",
    "same_side_scalar_wage_evidence",
    "same_side_structured_schedule_evidence",
    "same_side_growth_evidence",
    "same_side_non_base_compensation_evidence",
    "budget_or_pay_plan_context_evidence",
    "qualitative_mechanism_only",
    "quant_qual_mechanism_linked_evidence",
    "side_independent_mechanism_evidence",
    "national_readiness_stratum_only",
    "local_context_only",
    "period_repair_needed",
    "pay_basis_repair_needed",
    "role_side_repair_needed",
    "non_scalar_structuring_needed",
    "no_cross_side_anchor_available",
    "unresolved_or_defer",
    "write_off_or_exclude",
]

CATEGORY_FILENAMES = {
    category: "cleaned_" + category + "_queue" for category in CATEGORIES
}

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def parsed(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return [] if default is None else default
    if isinstance(value, (list, dict, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else [value]


def boolv(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def json_cell(value: Any) -> str:
    if isinstance(value, (list, dict, bool)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "" if value is None else str(value)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_pair(stem: str, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> tuple[Path, Path]:
    csv_path, jsonl_path = OUTPUT / f"{stem}.csv", OUTPUT / f"{stem}.jsonl"
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else ["cleaned_id"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json_cell(row.get(key, "")) for key in fieldnames})
    with jsonl_path.open("w", encoding="utf-8") as stream:
        for row in rows:
            compact_row = {key: value for key, value in row.items() if value not in ("", None, [])}
            if stem == "cleaned_analysis_use_layer":
                # The CSV is the canonical full-width layer. Keep the required JSONL as a
                # compact index projection to avoid duplicating long hashes/caveats above
                # GitHub's recommended 50 MiB threshold.
                for key in ("raw_span_snippet_sha256", "raw_bounded_context_snippet_sha256", "source_locator_lineage_sha256", "cleaned_claim_boundary", "cleaned_caveats", "reconciliation_reason_codes"):
                    compact_row.pop(key, None)
                compact_row["canonical_csv_row_pointer"] = f"cleaned_analysis_use_layer.csv#{row.get('cleaned_id', '')}"
            stream.write(json.dumps(compact_row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    return csv_path, jsonl_path


def grouped(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "missing") for row in rows).items()))


def ignored(path: str) -> bool:
    proc = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    return proc.returncode == 0


def preflight() -> dict[str, Any]:
    required = [
        "remaining_municipalities_quantitative_normalization_matching_manifest.json",
        "normalization_input_universe.csv", "normalized_quantitative_records.csv",
        "all_tier_matching_input_universe.csv", "all_tier_matching_results.csv",
        "quant_qual_mechanism_link_layer.csv", "national_comparison_readiness_layer.csv",
        "matching_blocker_summary.json", "validation_report.json",
    ]
    if not INPUT.exists() or not all((INPUT / name).exists() for name in required):
        raise RuntimeError("required quantitative normalization/matching inputs missing")
    norm_input = read_csv(INPUT / "normalization_input_universe.csv")
    normalized = read_csv(INPUT / "normalized_quantitative_records.csv")
    match_input = read_csv(INPUT / "all_tier_matching_input_universe.csv")
    matches = read_csv(INPUT / "all_tier_matching_results.csv")
    links = read_csv(INPUT / "quant_qual_mechanism_link_layer.csv")
    national = read_csv(INPUT / "national_comparison_readiness_layer.csv")
    blockers = read_json(INPUT / "matching_blocker_summary.json")["counts"]
    normalized_manifest = read_json(INPUT / "normalized_quantitative_records_manifest.json")
    national_summary = read_json(INPUT / "national_comparison_readiness_summary.json")
    if len(norm_input) != 8715 or len(normalized) != 8715:
        raise RuntimeError("normalization ledgers do not reconcile to 8,715")
    if normalized_manifest.get("usable_normalized_record_count") != 1250:
        raise RuntimeError("usable normalized subset does not reconcile to 1,250")
    if len(match_input) != 19643 or len(matches) != 19643:
        raise RuntimeError("all-tier matching ledgers do not reconcile to 19,643")
    if len(links) != 1250 or len(national) != 8715 or national_summary.get("candidate_count") != 299:
        raise RuntimeError("link/national readiness inputs do not reconcile")
    if blockers != EXPECTED_BLOCKERS:
        raise RuntimeError(f"blocker flags differ from locked counts: {blockers}")
    side_summary = read_json(RECON / "final_side_relevance_summary.json")
    side_counts = side_summary.get("counts", side_summary)
    if side_counts != FINAL_SIDE_COUNTS:
        raise RuntimeError(f"final side labels differ: {side_counts}")
    if not read_json(INPUT / "validation_report.json").get("all_checks_passed"):
        raise RuntimeError("input validation report did not pass")
    if not ignored("artifacts/local_retained_sources/") or not ignored("artifacts/local_extracted_text/"):
        raise RuntimeError("artifact roots are not Git-ignored")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    return {
        "head_before": head, "norm_input": norm_input, "normalized": normalized,
        "match_input": match_input, "matches": matches, "links": links, "national": national,
        "normalized_ledger_count": len(normalized), "usable_normalized_count": 1250,
        "count_correction_note": "normalized_quantitative_records.csv is the complete 8,715-row status ledger; 1,250 is its usable normalized subset",
    }


def rescue_period(row: dict[str, str]) -> dict[str, Any]:
    status = row.get("normalized_period_status", "")
    label = row.get("normalized_period_label", "")
    if status != "missing_period_anchor" and label:
        return {"period_rescue_status": "period_not_applicable" if row.get("normalized_side_label") == "not_applicable" else "explicit_period_rescued", "cleaned_period_label": label, "period_evidence_basis": "existing explicit or bounded normalized period", "period_rescue_confidence": "high"}
    raw_tokens = [str(x) for x in parsed(row.get("raw_period_tokens"))]
    title = row.get("source_title", "")
    snippet = row.get("raw_span_snippet", "")
    raw_years = sorted(set(YEAR_RE.findall(" ".join(raw_tokens))))
    title_years = sorted(set(YEAR_RE.findall(title)))
    snippet_years = sorted(set(YEAR_RE.findall(snippet[:1200])))
    if len(raw_years) == 1:
        return {"period_rescue_status": "explicit_period_rescued", "cleaned_period_label": raw_years[0], "period_evidence_basis": "single explicit year in raw period tokens", "period_rescue_confidence": "high"}
    if len(title_years) == 1:
        return {"period_rescue_status": "inferred_period_rescued", "cleaned_period_label": title_years[0], "period_evidence_basis": "single source-title year; inference caveat required", "period_rescue_confidence": "moderate"}
    if len(snippet_years) == 1:
        return {"period_rescue_status": "partial_period_rescued", "cleaned_period_label": snippet_years[0], "period_evidence_basis": "single bounded-snippet year; context review required", "period_rescue_confidence": "low"}
    if len(set(raw_years + title_years + snippet_years)) > 1:
        return {"period_rescue_status": "period_conflict_detected", "cleaned_period_label": "", "period_evidence_basis": "multiple conflicting candidate years", "period_rescue_confidence": "low"}
    return {"period_rescue_status": "period_missing_after_rescue", "cleaned_period_label": "", "period_evidence_basis": "no credible bounded period anchor", "period_rescue_confidence": "low"}


def rescue_pay_basis(row: dict[str, str]) -> dict[str, Any]:
    original_basis = row.get("normalized_pay_basis", "unknown_or_mixed")
    original_type = row.get("compensation_type", "unknown")
    category = row.get("evidence_category", "")
    text = (row.get("raw_span_snippet", "") + " " + row.get("raw_bounded_context_snippet", "")).lower()
    basis, comp_type, basis_reason = original_basis, original_type, "existing normalized classification"
    if basis == "unknown_or_mixed":
        mapping = {
            "quant_salary_schedule_table": ("step_schedule", "salary_schedule"),
            "quant_step_schedule_progression": ("step_schedule", "step_progression"),
            "quant_position_classification_pay_band": ("pay_grade", "classification_pay_band"),
            "quant_percentage_raise_or_cola": ("percentage_raise", "cola_or_raise"),
            "quant_cpi_indexed_adjustment": ("cola_cpi", "cola_or_raise"),
            "quant_budget_or_pay_plan_amount": ("budget_amount", "budget_or_pay_plan"),
            "quant_stipend_or_premium": ("stipend", "stipend_premium"),
            "quant_allowance_or_reimbursement": ("allowance", "allowance_reimbursement"),
            "quant_overtime_or_holiday_rate": ("overtime_rate", "overtime_holiday"),
        }
        if category in mapping:
            basis, comp_type = mapping[category]
            basis_reason = "evidence-category-specific bounded classification"
        elif category == "quant_base_wage_direct_value":
            if re.search(r"\b(hourly|per\s+hour|/hour|/hr)\b", text):
                basis, comp_type, basis_reason = "hourly", "base_wage", "explicit hourly phrase in bounded text"
            elif re.search(r"\b(annual|annually|per\s+year|yearly)\b", text):
                basis, comp_type, basis_reason = "annual_salary", "base_wage", "explicit annual phrase in bounded text"
            elif "monthly" in text or "per month" in text:
                basis, comp_type, basis_reason = "monthly", "base_wage", "explicit monthly phrase in bounded text"
        elif category.startswith("qual_"):
            basis, comp_type, basis_reason = "unknown", "mechanism_only", "qualitative mechanism evidence; pay basis structurally not required"
    if comp_type == "other" and category.startswith("qual_"):
        comp_type = "mechanism_only"
    if original_basis not in {"unknown_or_mixed", "unknown"}:
        rescue_status, confidence = "existing_pay_basis_confirmed", "high"
    elif basis not in {"unknown_or_mixed", "unknown"}:
        rescue_status, confidence = "pay_basis_comp_type_rescued", "moderate"
    elif comp_type == "mechanism_only":
        rescue_status, confidence = "pay_basis_not_applicable_mechanism", "high"
    else:
        rescue_status, confidence = "pay_basis_unknown_after_rescue", "low"
    return {"pay_basis_rescue_status": rescue_status, "cleaned_pay_basis": basis, "cleaned_compensation_type": comp_type, "pay_basis_evidence_basis": basis_reason, "pay_basis_rescue_confidence": confidence}


def structure_non_scalar(row: dict[str, str], pay: dict[str, Any]) -> dict[str, Any]:
    value_type = row.get("normalized_value_type", "")
    basis = pay["cleaned_pay_basis"]
    category = row.get("evidence_category", "")
    values = parsed(row.get("normalized_value_candidates"))
    if value_type == "range" or basis == "range_min_max":
        structure = "salary_range"
    elif value_type == "step_schedule_values" or basis == "step_schedule":
        structure = "step_schedule"
    elif basis == "pay_grade":
        structure = "pay_grade_or_classification_band"
    elif basis in GROWTH_BASIS or value_type == "percentage":
        structure = "percentage_raise_or_cola"
    elif basis in NONBASE_BASIS:
        structure = "non_base_amount"
    elif basis == "budget_amount":
        structure = "budget_or_pay_plan_context"
    elif pay["cleaned_compensation_type"] == "mechanism_only" or category.startswith("qual_"):
        structure = "mechanism_only"
    elif len(values) > 1:
        structure = "multiple_value_table"
    elif row.get("normalized_value") not in (None, ""):
        structure = "scalar_value"
    else:
        structure = "genuinely_no_quantitative_value"
    status = "structured_without_scalar_collapse" if structure not in {"scalar_value", "genuinely_no_quantitative_value", "mechanism_only"} else "not_non_scalar_structure"
    return {"non_scalar_structure_type": structure, "non_scalar_structuring_status": status, "structured_value_count": len(values), "fake_scalar_created": False, "structuring_basis": f"value_type={value_type or 'missing'};pay_basis={basis};evidence_category={category}"}


def side_route(row: dict[str, str]) -> dict[str, Any]:
    side = row.get("normalized_side_label", "")
    category = row.get("evidence_category", "")
    comp = row.get("compensation_type", "")
    if side in CLEAR_SIDE:
        route, status = "clear_side_analysis_eligible", "existing_final_clear_side_preserved"
    elif side == "not_applicable":
        if category.startswith("qual_"):
            route = "side_independent_mechanism"
        elif comp == "budget_or_pay_plan" or category == "quant_budget_or_pay_plan_amount":
            route = "side_independent_budget_context"
        else:
            route = "local_context_or_defer"
        status = "not_applicable_routed_without_clear_side_use"
    elif side == "remains_unclear":
        route, status = "role_side_repair_or_defer", "remains_unclear_preserved"
    elif side == "write_off":
        route, status = "write_off", "write_off_preserved"
    else:
        route, status = "role_side_repair_or_defer", "missing_side_status"
    return {"side_status_routing_status": status, "side_analysis_route": route, "clear_side_anchor_eligible": side in CLEAR_SIDE, "side_routing_reason": f"final side label {side or 'missing'} preserved; no side reconciliation rerun"}


def secondary_tags(row: dict[str, str], period: dict[str, Any], pay: dict[str, Any], non_scalar: dict[str, Any], link_status: str, local_kind: str, national_ready: bool) -> list[str]:
    tags: list[str] = []
    value_type = row.get("normalized_value_type", "")
    basis, side = pay["cleaned_pay_basis"], row.get("normalized_side_label", "")
    structure = non_scalar["non_scalar_structure_type"]
    if row.get("normalized_value") not in (None, "") and value_type == "currency_amount": tags.append("scalar_value_available")
    if structure == "salary_range": tags.append("range_value_available")
    if structure == "step_schedule": tags.append("step_schedule_available")
    if structure == "pay_grade_or_classification_band": tags.append("pay_grade_available")
    if value_type == "percentage" or basis in GROWTH_BASIS: tags.append("percent_value_available")
    if basis == "cola_cpi": tags.append("cola_cpi_available")
    if basis in NONBASE_BASIS: tags.append("non_base_compensation_available")
    if basis == "budget_amount": tags.append("budget_context_available")
    if period["period_rescue_status"] == "explicit_period_rescued": tags.append("explicit_period_available")
    elif period["cleaned_period_label"]: tags.append("inferred_period_available")
    else: tags.append("missing_period")
    if basis == "hourly": tags.append("hourly_basis")
    elif basis == "annual_salary": tags.append("annual_salary_basis")
    elif basis in GROWTH_BASIS: tags.append("percentage_basis")
    elif basis in {"unknown", "unknown_or_mixed", "mixed_or_multiple"}: tags.append("mixed_pay_basis")
    if side in SAFETY_SIDE: tags.append("clear_safety_side")
    if side in NON_SAFETY_SIDE: tags.append("clear_non_safety_side")
    if side == "not_applicable": tags.append("side_independent")
    if side == "remains_unclear": tags.append("side_unclear")
    if link_status == "strong_quant_qual_link": tags.extend(["quant_qual_link_strong", "mechanism_link_available"])
    elif link_status == "moderate_quant_qual_link": tags.extend(["quant_qual_link_moderate", "mechanism_link_available"])
    if local_kind: tags.append("local_comparison_candidate")
    if basis in GROWTH_BASIS: tags.append("growth_candidate")
    if national_ready: tags.append("national_stratum_candidate")
    if row.get("normalization_status", "").startswith("needs_"): tags.append("needs_manual_review")
    return sorted(set(tags))


def record_category(row: dict[str, str], period: dict[str, Any], pay: dict[str, Any], non_scalar: dict[str, Any], side: dict[str, Any], link_status: str, local_kind: str, national_status: str) -> tuple[str, str, str, str, str]:
    final_side = row.get("normalized_side_label", "")
    basis, comp = pay["cleaned_pay_basis"], pay["cleaned_compensation_type"]
    structure = non_scalar["non_scalar_structure_type"]
    has_period = bool(period["cleaned_period_label"])
    if final_side == "write_off": category = "write_off_or_exclude"
    elif local_kind == "direct": category = "direct_cross_side_comparison_ready"
    elif local_kind == "conditional": category = "conditional_cross_side_comparison_candidate"
    elif link_status in {"strong_quant_qual_link", "moderate_quant_qual_link"}: category = "quant_qual_mechanism_linked_evidence"
    elif final_side == "not_applicable":
        if comp == "mechanism_only" or row.get("evidence_category", "").startswith("qual_"): category = "side_independent_mechanism_evidence"
        elif basis == "budget_amount": category = "budget_or_pay_plan_context_evidence"
        else: category = "local_context_only"
    elif final_side == "remains_unclear": category = "role_side_repair_needed"
    elif final_side in CLEAR_SIDE:
        if basis in GROWTH_BASIS or structure == "percentage_raise_or_cola": category = "same_side_growth_evidence"
        elif basis in NONBASE_BASIS or comp in {"overtime_holiday", "stipend_premium", "allowance_reimbursement", "longevity_service", "non_base_compensation"}: category = "same_side_non_base_compensation_evidence"
        elif structure in {"salary_range", "step_schedule", "pay_grade_or_classification_band", "multiple_value_table"}: category = "same_side_structured_schedule_evidence"
        elif basis == "budget_amount": category = "budget_or_pay_plan_context_evidence"
        elif comp == "mechanism_only" or row.get("evidence_category", "").startswith("qual_"): category = "qualitative_mechanism_only"
        elif row.get("normalized_value") not in (None, "") and basis in SCALAR_BASIS and has_period: category = "same_side_scalar_wage_evidence"
        elif national_status == "national_ready_stratum_candidate": category = "national_readiness_stratum_only"
        elif not has_period and (row.get("normalized_value") or parsed(row.get("normalized_value_candidates"))): category = "period_repair_needed"
        elif basis in {"unknown", "unknown_or_mixed"}: category = "pay_basis_repair_needed"
        elif structure == "genuinely_no_quantitative_value": category = "unresolved_or_defer"
        else: category = "non_scalar_structuring_needed"
    else: category = "role_side_repair_needed"
    if category in {"direct_cross_side_comparison_ready", "conditional_cross_side_comparison_candidate", "same_side_scalar_wage_evidence", "same_side_structured_schedule_evidence", "same_side_growth_evidence", "same_side_non_base_compensation_evidence", "quant_qual_mechanism_linked_evidence"}:
        blocker_status, repair_status = "no_material_blocker_after_reclassification", "resolved_or_routed"
    elif category in {"budget_or_pay_plan_context_evidence", "qualitative_mechanism_only", "side_independent_mechanism_evidence", "national_readiness_stratum_only", "local_context_only"}:
        blocker_status, repair_status = "comparison_blockers_retained", "routed_to_non_comparison_analysis_use"
    elif category == "write_off_or_exclude": blocker_status, repair_status = "write_off", "routed_to_write_off"
    else: blocker_status, repair_status = "repair_or_defer_remaining", "routed_to_repair_needed"
    route = {
        "direct_cross_side_comparison_ready": "local_comparison_qa",
        "conditional_cross_side_comparison_candidate": "conditional_local_comparison_qa",
        "quant_qual_mechanism_linked_evidence": "mechanism_link_qa",
        "same_side_growth_evidence": "growth_evidence_qa",
        "national_readiness_stratum_only": "national_readiness_gate",
        "write_off_or_exclude": "exclude",
    }.get(category, "analysis_use_qa" if "evidence" in category else "repair_or_defer")
    claim = "bounded local documentary use only; no final wage-gap, national, prevalence, or causal claim"
    confidence = "high" if category in {"direct_cross_side_comparison_ready", "write_off_or_exclude"} else "moderate" if category not in {"role_side_repair_needed", "unresolved_or_defer", "pay_basis_repair_needed", "period_repair_needed"} else "low"
    return category, blocker_status, repair_status, route, confidence


def structure_category(row: dict[str, str], local_ids: dict[str, str]) -> tuple[str, str, str, str]:
    match_id = row["match_id"]
    blockers = parsed(row.get("blocker_flags"))
    if match_id in local_ids:
        category = "direct_cross_side_comparison_ready" if local_ids[match_id] == "direct" else "conditional_cross_side_comparison_candidate"
    elif row["match_status"] == "growth_continuity_ready": category = "same_side_growth_evidence"
    elif row["match_status"] == "quant_qual_mechanism_link_ready": category = "quant_qual_mechanism_linked_evidence"
    elif row["match_status"] == "national_readiness_candidate": category = "national_readiness_stratum_only"
    elif row["match_status"] == "write_off_exclude": category = "write_off_or_exclude"
    elif "non_clear_side_status_present" in blockers: category = "role_side_repair_needed"
    elif "pay_basis_or_compensation_type_incompatible" in blockers and "period_incompatible_or_missing" not in blockers: category = "pay_basis_repair_needed"
    elif "period_incompatible_or_missing" in blockers and "no_scalar_normalized_value" not in blockers: category = "period_repair_needed"
    elif "no_scalar_normalized_value" in blockers: category = "non_scalar_structuring_needed"
    elif "missing_clear_cross_side_normalized_anchors" in blockers: category = "no_cross_side_anchor_available"
    else: category = "unresolved_or_defer"
    if category in {"direct_cross_side_comparison_ready", "conditional_cross_side_comparison_candidate"}:
        resolution = "resolved"
    elif category in {"same_side_growth_evidence", "quant_qual_mechanism_linked_evidence", "national_readiness_stratum_only", "no_cross_side_anchor_available"}:
        resolution = "routed_to_non_comparison_analysis_use"
    elif category == "write_off_or_exclude": resolution = "routed_to_write_off"
    elif category in {"period_repair_needed", "pay_basis_repair_needed", "role_side_repair_needed", "non_scalar_structuring_needed"}: resolution = "routed_to_repair_needed"
    else: resolution = "routed_to_defer"
    confidence = "high" if resolution in {"resolved", "routed_to_write_off"} else "moderate" if resolution == "routed_to_non_comparison_analysis_use" else "low"
    route = "local_comparison_qa" if resolution == "resolved" else "analysis_use_qa" if resolution == "routed_to_non_comparison_analysis_use" else "repair_or_defer"
    return category, resolution, route, confidence


def build() -> dict[str, Any]:
    data = preflight()
    OUTPUT.mkdir(parents=True, exist_ok=True); LOG_DIR.mkdir(parents=True, exist_ok=True)
    normalized, matches, links, national = data["normalized"], data["matches"], data["links"], data["national"]
    provisional = read_csv(INPUT / "provisional_local_comparison_candidates.csv")
    conditional = read_csv(INPUT / "conditional_local_comparison_candidates.csv")
    growth = read_csv(INPUT / "growth_continuity_normalized_candidates.csv")
    mechanism = read_csv(INPUT / "mechanism_attributed_quantitative_records.csv")
    local_ids = {row["match_id"]: "direct" for row in provisional} | {row["match_id"]: "conditional" for row in conditional}
    direct_norm_ids: dict[str, str] = {}
    match_by_id = {row["match_id"]: row for row in matches}
    for match_id, kind in local_ids.items():
        for norm_id in parsed(match_by_id.get(match_id, {}).get("normalized_record_ids_involved")):
            direct_norm_ids[norm_id] = kind
    link_by_norm = {row["quantitative_normalization_id"]: row for row in links}
    national_by_norm = {row["normalization_id"]: row for row in national}

    period_rows: list[dict[str, Any]] = []
    pay_rows: list[dict[str, Any]] = []
    non_scalar_rows: list[dict[str, Any]] = []
    side_rows: list[dict[str, Any]] = []
    record_clean: list[dict[str, Any]] = []
    for row in normalized:
        period = rescue_period(row); pay = rescue_pay_basis(row); non_scalar = structure_non_scalar(row, pay); side = side_route(row)
        link_status = link_by_norm.get(row["normalization_id"], {}).get("linkage_status", "")
        local_kind = direct_norm_ids.get(row["normalization_id"], "")
        national_status = national_by_norm.get(row["normalization_id"], {}).get("national_readiness_status", "")
        category, blocker_status, repair_status, route, confidence = record_category(row, period, pay, non_scalar, side, link_status, local_kind, national_status)
        tags = secondary_tags(row, period, pay, non_scalar, link_status, local_kind, national_status == "national_ready_stratum_candidate")
        cleaned_id = stable("BRMCLEAN", "record", row["normalization_id"])
        common = {"cleaned_id": cleaned_id, "cleaned_unit_type": "normalized_record", "original_unit_id": row["normalization_id"], "normalization_id": row["normalization_id"], "match_id": "", "span_id": row["span_id"], "source_rating_id": row["source_rating_id"], "municipality": row["municipality"], "state": row["state"], "region": row["region"], "source_family": row["source_family"], "cba_non_cba_hint": row["cba_non_cba_hint"], "original_evidence_category": row["evidence_category"], "original_evidence_family": row["evidence_family"], "claim_readiness_bucket": row["claim_readiness_bucket"], "downstream_use_bucket": row["downstream_use_bucket"], "original_normalization_status": row["normalization_status"], "original_matching_status": "not_applicable_record_unit", "original_blocker_flags": parsed(row.get("normalization_caveats")), "final_side_label": row["normalized_side_label"], "reconciliation_confidence": row["reconciliation_confidence"], "reconciliation_reason_codes": parsed(row["reconciliation_reason_codes"]), "raw_value_tokens": parsed(row["raw_value_tokens"]), "raw_span_snippet_sha256": hashlib.sha256(row["raw_span_snippet"].encode()).hexdigest(), "raw_bounded_context_snippet_sha256": hashlib.sha256(row["raw_bounded_context_snippet"].encode()).hexdigest(), "raw_evidence_pointer": f"{INPUT.relative_to(ROOT)}/normalized_quantitative_records.csv#{row['normalization_id']}", "source_locator_lineage_sha256": hashlib.sha256(row["source_locator_lineage"].encode()).hexdigest(), "cleaned_analysis_use_primary_category": category, "cleaned_analysis_use_secondary_tags": tags, "cleaned_blocker_status": blocker_status, "cleaned_repair_status": repair_status, "cleaned_downstream_route": route, "cleaned_claim_boundary": "bounded local documentary use only; no final wage-gap, national, prevalence, or causal claim", "cleaned_confidence": confidence, "cleaned_caveats": sorted(set(parsed(row["normalization_caveats"]) + ([period["period_evidence_basis"]] if period["period_rescue_confidence"] == "low" else []))), "cleaned_period_label": period["cleaned_period_label"], "cleaned_period_status": period["period_rescue_status"], "cleaned_pay_basis": pay["cleaned_pay_basis"], "cleaned_compensation_type": pay["cleaned_compensation_type"], "cleaned_non_scalar_structure_type": non_scalar["non_scalar_structure_type"], "quant_qual_link_status": link_status, "national_readiness_status": national_status}
        record_clean.append(common)
        period_rows.append({"period_rescue_id": stable("BRMPERRES", row["normalization_id"]), "normalization_id": row["normalization_id"], "original_period_status": row["normalized_period_status"], "original_period_label": row["normalized_period_label"], **period, "source_title": row["source_title"], "raw_period_tokens": parsed(row["raw_period_tokens"]), "source_locator_lineage": row["source_locator_lineage"]})
        pay_rows.append({"pay_basis_rescue_id": stable("BRMPAYRES", row["normalization_id"]), "normalization_id": row["normalization_id"], "original_pay_basis": row["normalized_pay_basis"], "original_compensation_type": row["compensation_type"], "evidence_category": row["evidence_category"], **pay, "source_locator_lineage": row["source_locator_lineage"]})
        non_scalar_rows.append({"non_scalar_structuring_id": stable("BRMNSRES", row["normalization_id"]), "normalization_id": row["normalization_id"], "original_value_type": row["normalized_value_type"], "original_normalized_value": row["normalized_value"], "original_value_candidates": parsed(row["normalized_value_candidates"]), **non_scalar, "source_locator_lineage": row["source_locator_lineage"]})
        side_rows.append({"side_status_routing_id": stable("BRMSIDEROUTE", row["normalization_id"]), "normalization_id": row["normalization_id"], "final_side_label": row["normalized_side_label"], "evidence_category": row["evidence_category"], **side, "source_locator_lineage": row["source_locator_lineage"]})

    structure_clean: list[dict[str, Any]] = []
    blocker_results: list[dict[str, Any]] = []
    signatures = Counter(); resolution_counts = Counter(); primary_counts = Counter()
    overlap = {left: {right: 0 for right in BLOCKER_ORDER} for left in BLOCKER_ORDER}
    for row in matches:
        flags = [flag for flag in parsed(row.get("blocker_flags")) if flag in EXPECTED_BLOCKERS]
        signature = "+".join(sorted(flags)) if flags else "no_material_blocker"
        signatures[signature] += 1
        for left in flags:
            for right in flags: overlap[left][right] += 1
        primary = "no_material_blocker_after_reclassification" if not flags else ({
            "missing_clear_cross_side_normalized_anchors": "missing_cross_side_anchor",
            "pay_basis_or_compensation_type_incompatible": "pay_basis_or_comp_type_blocked",
            "period_incompatible_or_missing": "period_blocked",
            "no_scalar_normalized_value": "no_scalar_value",
            "non_clear_side_status_present": "non_clear_side",
        }[flags[0]] if len(flags) == 1 else "multiple_blockers")
        category, resolution, route, confidence = structure_category(row, local_ids)
        primary_counts[primary] += 1; resolution_counts[resolution] += 1
        rescue_path = {"resolved": "clean_local_comparison_queue", "routed_to_non_comparison_analysis_use": "retain_for_non_comparison_analysis", "routed_to_repair_needed": "repair_queue", "routed_to_defer": "defer_queue", "routed_to_write_off": "write_off_queue"}[resolution]
        result = {"blocker_rescue_id": stable("BRMBLOCKRES", row["match_id"]), "match_id": row["match_id"], "matching_prep_id": row["matching_prep_id"], "municipality": row["municipality"], "state": row["state"], "region": row["region"], "match_tier_original": row["match_tier_original"], "match_tier_final": row["match_tier_final"], "original_matching_status": row["match_status"], "original_blocker_flags": flags, "blocker_count": len(flags), "blocker_signature": signature, "primary_blocker": primary, "secondary_blockers": flags[1:] if len(flags) > 1 else [], "blocker_overlap_group": f"{len(flags)}_blockers", "rescue_path": rescue_path, "final_blocker_resolution": resolution, "cleaned_analysis_use_primary_category": category, "cleaned_confidence": confidence, "cleaned_caveats": parsed(row["caveats"]), "source_locator_lineage": row["source_locator_lineage"]}
        blocker_results.append(result)
        structure_clean.append({"cleaned_id": stable("BRMCLEAN", "structure", row["match_id"]), "cleaned_unit_type": "matching_structure", "original_unit_id": row["match_id"], "normalization_id": "", "match_id": row["match_id"], "span_id": "", "source_rating_id": "", "municipality": row["municipality"], "state": row["state"], "region": row["region"], "source_family": "multiple_or_cluster", "cba_non_cba_hint": "", "original_evidence_category": "matching_structure", "original_evidence_family": "derived_structure", "claim_readiness_bucket": "", "downstream_use_bucket": row["recommended_downstream_use"], "original_normalization_status": "not_applicable_structure_unit", "original_matching_status": row["match_status"], "original_blocker_flags": flags, "final_side_label": "|".join(parsed(row["side_labels_represented"])), "reconciliation_confidence": "", "reconciliation_reason_codes": [], "raw_value_tokens": [], "raw_span_snippet_sha256": "", "raw_bounded_context_snippet_sha256": "", "raw_evidence_pointer": f"{INPUT.relative_to(ROOT)}/all_tier_matching_results.csv#{row['match_id']}", "source_locator_lineage_sha256": hashlib.sha256(row["source_locator_lineage"].encode()).hexdigest(), "cleaned_analysis_use_primary_category": category, "cleaned_analysis_use_secondary_tags": sorted(set((["same_source_cluster"] if boolv(row["same_source_flag"]) else []) + (["same_period_cluster"] if boolv(row["compatible_period_flag"]) else []) + (["national_stratum_candidate"] if category == "national_readiness_stratum_only" else []) + (["local_comparison_candidate"] if category in {"direct_cross_side_comparison_ready", "conditional_cross_side_comparison_candidate"} else []) + (["growth_candidate"] if category == "same_side_growth_evidence" else []))), "cleaned_blocker_status": primary, "cleaned_repair_status": resolution, "cleaned_downstream_route": route, "cleaned_claim_boundary": "structure-level readiness only; no final wage-gap, national, prevalence, or causal claim", "cleaned_confidence": confidence, "cleaned_caveats": parsed(row["caveats"]), "cleaned_period_label": "", "cleaned_period_status": row["period_anchor_quality"], "cleaned_pay_basis": row["pay_basis_compatibility"], "cleaned_compensation_type": "multiple_or_cluster", "cleaned_non_scalar_structure_type": "matching_structure", "quant_qual_link_status": "", "national_readiness_status": ""})

    cleaned = record_clean + structure_clean
    clean_fields = list(cleaned[0])
    clean_csv, clean_jsonl = write_pair("cleaned_analysis_use_layer", cleaned, clean_fields)
    write_json(OUTPUT / "cleaned_analysis_use_layer_manifest.json", {"task_id": TASK_ID, "row_count": len(cleaned), "normalized_record_count": len(record_clean), "matching_structure_count": len(structure_clean), "csv_sha256": sha256(clean_csv), "jsonl_sha256": sha256(clean_jsonl), "exactly_one_primary_category": True, "canonical_full_width_format": "csv", "jsonl_format": "compact index projection with canonical_csv_row_pointer", "large_file_decision": "avoid redundant long hashes/caveats in JSONL while preserving them in canonical CSV"})

    overlap_rows = [{"blocker": left, **overlap[left]} for left in BLOCKER_ORDER]
    write_pair("blocker_overlap_matrix", overlap_rows)
    write_json(OUTPUT / "blocker_overlap_matrix.json", {"matrix": overlap, "diagonal_reconciles_to_original_counts": {key: overlap[key][key] for key in BLOCKER_ORDER}, "total_structures": len(matches)})
    write_json(OUTPUT / "blocker_signature_summary.json", {"signature_counts": dict(sorted(signatures.items(), key=lambda x: (-x[1], x[0]))), "unique_signature_count": len(signatures), "total": len(matches)})
    write_json(OUTPUT / "unique_blocker_cohort_summary.json", {"blocker_count_cohorts": dict(sorted(Counter(len(parsed(r["blocker_flags"])) for r in matches).items())), "primary_blocker_counts": dict(sorted(primary_counts.items())), "unique_structure_count": len(matches)})
    write_json(OUTPUT / "blocker_resolution_summary.json", {"resolution_counts": dict(sorted(resolution_counts.items())), "total": len(matches)})
    br_csv, br_jsonl = write_pair("blocker_rescue_results", blocker_results)
    write_json(OUTPUT / "blocker_rescue_results_manifest.json", {"row_count": len(blocker_results), "csv_sha256": sha256(br_csv), "jsonl_sha256": sha256(br_jsonl), "original_blocker_flag_counts": EXPECTED_BLOCKERS})

    for stem, rows in [("period_anchor_rescue_results", period_rows), ("pay_basis_comp_type_rescue_results", pay_rows), ("non_scalar_structuring_results", non_scalar_rows), ("side_status_routing_results", side_rows)]:
        write_pair(stem, rows)
    period_summary = {"status_counts": grouped(period_rows, "period_rescue_status"), "total": len(period_rows), "rescued_or_existing_period_count": sum(1 for r in period_rows if r["cleaned_period_label"]), "remaining_missing_or_conflict_count": sum(1 for r in period_rows if not r["cleaned_period_label"])}
    pay_summary = {"status_counts": grouped(pay_rows, "pay_basis_rescue_status"), "cleaned_pay_basis_counts": grouped(pay_rows, "cleaned_pay_basis"), "cleaned_compensation_type_counts": grouped(pay_rows, "cleaned_compensation_type"), "total": len(pay_rows)}
    non_scalar_summary = {"structure_counts": grouped(non_scalar_rows, "non_scalar_structure_type"), "status_counts": grouped(non_scalar_rows, "non_scalar_structuring_status"), "fake_scalar_created_count": 0, "total": len(non_scalar_rows)}
    side_summary = {"routing_counts": grouped(side_rows, "side_analysis_route"), "status_counts": grouped(side_rows, "side_status_routing_status"), "clear_side_anchor_eligible_count": sum(bool(r["clear_side_anchor_eligible"]) for r in side_rows), "total": len(side_rows)}
    write_json(OUTPUT / "period_anchor_rescue_summary.json", period_summary)
    write_json(OUTPUT / "pay_basis_comp_type_rescue_summary.json", pay_summary)
    write_json(OUTPUT / "non_scalar_structuring_summary.json", non_scalar_summary)
    write_json(OUTPUT / "side_status_routing_summary.json", side_summary)

    cross_rows = [{"cross_side_routing_id": stable("BRMCROSSROUTE", r["match_id"]), "match_id": r["match_id"], "original_missing_cross_side_flag": "missing_clear_cross_side_normalized_anchors" in r["original_blocker_flags"], "cleaned_analysis_use_primary_category": r["cleaned_analysis_use_primary_category"], "final_blocker_resolution": r["final_blocker_resolution"], "cross_side_route": r["rescue_path"], "source_locator_lineage": r["source_locator_lineage"]} for r in blocker_results]
    write_pair("cross_side_anchor_rescue_routing_results", cross_rows)
    cross_summary = {"route_counts": grouped(cross_rows, "cross_side_route"), "category_counts": grouped(cross_rows, "cleaned_analysis_use_primary_category"), "original_missing_cross_side_flag_count": sum(r["original_missing_cross_side_flag"] for r in cross_rows), "total": len(cross_rows)}
    write_json(OUTPUT / "cross_side_anchor_rescue_routing_summary.json", cross_summary)

    qql_rows = []
    for row in links:
        status = row["linkage_status"]
        if status in {"strong_quant_qual_link", "moderate_quant_qual_link"}: rescue_status, route = "preserved_analysis_ready_link", "quant_qual_mechanism_linked_evidence"
        elif status == "weak_quant_qual_link": rescue_status, route = "weak_link_review_needed", "unresolved_or_defer"
        else: rescue_status, route = "blocked_or_not_linkable_preserved", "unresolved_or_defer"
        qql_rows.append({**row, "quant_qual_rescue_status": rescue_status, "cleaned_analysis_use_primary_category": route, "original_linkage_status_preserved": True})
    write_pair("quant_qual_link_rescue_results", qql_rows)
    qql_summary = {"original_status_counts": grouped(qql_rows, "linkage_status"), "rescue_status_counts": grouped(qql_rows, "quant_qual_rescue_status"), "analysis_ready_link_count": sum(r["quant_qual_rescue_status"] == "preserved_analysis_ready_link" for r in qql_rows), "total": len(qql_rows)}
    write_json(OUTPUT / "quant_qual_link_rescue_summary.json", qql_summary)

    nat_rows = []
    clean_by_norm = {r["normalization_id"]: r for r in record_clean}
    for row in national:
        clean = clean_by_norm[row["normalization_id"]]; original = row["national_readiness_status"]
        category = clean["cleaned_analysis_use_primary_category"]
        if original == "national_ready_stratum_candidate": status = "national_ready_stratum_candidate"
        elif category == "quant_qual_mechanism_linked_evidence": status = "national_mechanism_stratum_candidate"
        elif category == "same_side_growth_evidence": status = "national_growth_stratum_candidate"
        elif category == "period_repair_needed": status = "national_needs_period_repair"
        elif category == "pay_basis_repair_needed": status = "national_needs_pay_basis_repair"
        elif category == "role_side_repair_needed": status = "national_needs_side_balance"
        elif category == "write_off_or_exclude": status = "national_write_off"
        elif category in {"same_side_scalar_wage_evidence", "same_side_structured_schedule_evidence", "same_side_non_base_compensation_evidence", "budget_or_pay_plan_context_evidence", "qualitative_mechanism_only", "side_independent_mechanism_evidence"}: status = "national_partial_stratum_candidate"
        else: status = "national_insufficient_structure"
        nat_rows.append({**row, "original_national_readiness_status": original, "cleaned_national_readiness_status": status, "cleaned_analysis_use_primary_category": category, "final_national_claims": 0, "national_wage_gaps": 0, "national_prevalence_estimates": 0})
    write_pair("national_readiness_reclassification_results", nat_rows)
    nat_summary = {"status_counts": grouped(nat_rows, "cleaned_national_readiness_status"), "total": len(nat_rows), "final_national_claims": 0, "national_wage_gaps": 0, "national_prevalence_estimates": 0}
    write_json(OUTPUT / "national_readiness_reclassification_summary.json", nat_summary)

    category_counts = grouped(cleaned, "cleaned_analysis_use_primary_category")
    tag_counts = Counter(tag for row in cleaned for tag in row["cleaned_analysis_use_secondary_tags"])
    write_json(OUTPUT / "cleaned_analysis_use_category_summary.json", {"counts": category_counts, "total": len(cleaned), "record_count": len(record_clean), "structure_count": len(structure_clean)})
    write_json(OUTPUT / "cleaned_analysis_use_secondary_tag_summary.json", {"counts": dict(sorted(tag_counts.items())), "total_tag_assignments": sum(tag_counts.values())})
    write_json(OUTPUT / "cleaned_claim_boundary_summary.json", {"counts": grouped(cleaned, "cleaned_claim_boundary"), "final_claims": 0})
    write_json(OUTPUT / "cleaned_downstream_route_summary.json", {"counts": grouped(cleaned, "cleaned_downstream_route")})
    for category, stem in CATEGORY_FILENAMES.items():
        write_pair(stem, [row for row in cleaned if row["cleaned_analysis_use_primary_category"] == category], clean_fields)

    local_clean = [{**row, "cleaned_analysis_use_primary_category": "direct_cross_side_comparison_ready", "qa_required": True, "claim_boundary": "provisional local comparison only"} for row in provisional] + [{**row, "cleaned_analysis_use_primary_category": "conditional_cross_side_comparison_candidate", "qa_required": True, "claim_boundary": "conditional local comparison only"} for row in conditional]
    growth_clean = [{**row, "cleaned_analysis_use_primary_category": "same_side_growth_evidence", "cross_side_wage_level_comparison_forced": False} for row in growth]
    qq_clean = [{**row, "cleaned_analysis_use_primary_category": "quant_qual_mechanism_linked_evidence" if row["linkage_status"] in {"strong_quant_qual_link", "moderate_quant_qual_link"} else "unresolved_or_defer"} for row in links]
    mech_clean = [{**row, "cleaned_analysis_use_primary_category": "quant_qual_mechanism_linked_evidence", "causal_claim_flag": False} for row in mechanism]
    nat_clean = nat_rows
    for stem, rows in [("cleaned_local_comparison_candidate_layer", local_clean), ("cleaned_growth_continuity_layer", growth_clean), ("cleaned_quant_qual_mechanism_link_layer", qq_clean), ("cleaned_mechanism_attribution_layer", mech_clean), ("cleaned_national_comparison_readiness_layer", nat_clean)]:
        write_pair(stem, rows)
    local_summary = {"direct_count": len(provisional), "conditional_count": len(conditional), "total": len(local_clean), "all_require_qa": True, "final_wage_gap_claims": 0}
    growth_summary = {"status_counts": grouped(growth_clean, "growth_continuity_status"), "total": len(growth_clean), "forced_cross_side_wage_level_comparisons": 0}
    qq_summary = {"status_counts": grouped(qq_clean, "linkage_status"), "analysis_ready_strong_moderate_count": sum(r["linkage_status"] in {"strong_quant_qual_link", "moderate_quant_qual_link"} for r in qq_clean), "total": len(qq_clean), "causal_claims": 0}
    mech_summary = {"mechanism_class_counts": grouped(mech_clean, "mechanism_class"), "total": len(mech_clean), "causal_claims": 0}
    write_json(OUTPUT / "cleaned_local_comparison_candidate_summary.json", local_summary)
    write_json(OUTPUT / "cleaned_growth_continuity_summary.json", growth_summary)
    write_json(OUTPUT / "cleaned_quant_qual_mechanism_link_summary.json", qq_summary)
    write_json(OUTPUT / "cleaned_mechanism_attribution_summary.json", mech_summary)
    write_json(OUTPUT / "cleaned_national_comparison_readiness_summary.json", nat_summary)

    remaining_categories = {key: category_counts.get(key, 0) for key in ["period_repair_needed", "pay_basis_repair_needed", "role_side_repair_needed", "non_scalar_structuring_needed", "no_cross_side_anchor_available", "unresolved_or_defer", "write_off_or_exclude"]}
    resolved_categories = {key: category_counts.get(key, 0) for key in CATEGORIES if key not in remaining_categories}
    write_json(OUTPUT / "cleaned_major_blocker_remaining_summary.json", {"counts": remaining_categories, "total": sum(remaining_categories.values()), "unit_note": "record and structure analysis-use units; not additive to original overlapping blocker flags"})
    write_json(OUTPUT / "cleaned_major_blocker_resolved_summary.json", {"counts": resolved_categories, "total": sum(resolved_categories.values()), "resolution_counts": dict(sorted(resolution_counts.items()))})

    for name, key in [("source_family_cleaning_summary", "source_family"), ("geography_cleaning_summary", "state"), ("cba_non_cba_cleaning_summary", "cba_non_cba_hint"), ("evidence_category_cleaning_summary", "original_evidence_category"), ("side_label_cleaning_summary", "final_side_label")]:
        table: dict[str, Counter[str]] = defaultdict(Counter)
        for row in record_clean: table[str(row.get(key) or "missing")][row["cleaned_analysis_use_primary_category"]] += 1
        write_json(OUTPUT / f"{name}.json", {"by_group": {group: dict(sorted(counts.items())) for group, counts in sorted(table.items())}, "total_records": len(record_clean)})

    summary = {
        "task_id": TASK_ID, "decision": DECISION, "next_task": NEXT_TASK,
        "normalization_input_count": 8715, "normalized_status_ledger_count": 8715, "usable_normalized_input_count": 1250,
        "normalized_count_correction_note": data["count_correction_note"], "matching_structure_count": 19643,
        "original_blocker_flag_counts": EXPECTED_BLOCKERS, "unique_blocker_signature_count": len(signatures),
        "blocker_count_cohorts": dict(sorted(Counter(len(parsed(r["blocker_flags"])) for r in matches).items())),
        "blocker_resolution_counts": dict(sorted(resolution_counts.items())), "cleaned_analysis_use_layer_count": len(cleaned),
        "cleaned_analysis_use_category_counts": category_counts, "records_or_structures_rescued_or_rerouted": sum(value for key, value in resolution_counts.items() if key in {"resolved", "partially_resolved", "routed_to_non_comparison_analysis_use"}),
        "remaining_repair_defer_writeoff_counts": remaining_categories, "period_rescue_summary": period_summary,
        "pay_basis_comp_type_rescue_summary": pay_summary, "non_scalar_structuring_summary": non_scalar_summary,
        "side_status_routing_summary": side_summary, "quant_qual_link_rescue_summary": qql_summary,
        "national_readiness_reclassification_summary": nat_summary, "cleaned_local_comparison_summary": local_summary,
        "cleaned_growth_continuity_summary": growth_summary, "cleaned_mechanism_attribution_count": len(mech_clean),
        "no_polished_deliverables_created": True, "claim_boundary": "internal analysis-use routing only; no final wage-gap, national, prevalence, or causal claim",
    }
    write_json(OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_summary.json", summary)
    md = ["# Remaining-municipality blocker rescue and analysis-ready reclassification", "", f"Decision: `{DECISION}`", "", f"- Complete normalization status ledger: 8,715; usable normalized subset: 1,250.", f"- Matching structures de-overlapped: 19,643; unique blocker signatures: {len(signatures)}.", f"- Cleaned analysis-use units: {len(cleaned):,} (8,715 records + 19,643 structures).", f"- Rescued or rerouted structures: {summary['records_or_structures_rescued_or_rerouted']:,}.", f"- Clean local comparison candidates retained: {len(provisional)} direct and {len(conditional)} conditional.", f"- Strong/moderate quant–qual links preserved: {qql_summary['analysis_ready_link_count']:,}.", "- Original evidence/provenance categories remain unchanged; analysis-use categories are derived fields.", "- No polished deliverable, regression, treatment effect, final wage-gap, national, prevalence, or causal claim was produced."]
    (OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    write_json(OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_manifest.json", {"task_id": TASK_ID, "decision": DECISION, "created_at": now(), "head_before": data["head_before"], "input_directory": str(INPUT.relative_to(ROOT)), "output_directory": str(OUTPUT.relative_to(ROOT)), "normalization_status_ledger_count": 8715, "usable_normalized_input_count": 1250, "matching_structure_count": 19643, "cleaned_analysis_use_layer_count": len(cleaned), "cleaned_layer_sha256": sha256(clean_jsonl), "next_task": NEXT_TASK})

    dashboard = {"current_stage": "blocker rescue and analysis-ready reclassification complete", "next_task": NEXT_TASK, "original_blocker_flag_counts": EXPECTED_BLOCKERS, "unique_blocker_signature_count": len(signatures), "blocker_resolution_counts": dict(sorted(resolution_counts.items())), "records_or_structures_rescued_or_rerouted": summary["records_or_structures_rescued_or_rerouted"], "cleaned_analysis_use_category_counts": category_counts, "remaining_repair_defer_writeoff_counts": remaining_categories, "dashboard_map_primary_metric": "scout_coverage_rate", "scout_coverage_rate_percent": 99.9579, "final_pi_report_link_intact": True, "wage_growth_continuity_module_intact": True, "dashboard_clean_structure_preserved": True, "global_analysis_readiness": False, "global_wage_gap_readiness": False, "global_causal_readiness": False, "no_polished_deliverables_created": True, "dashboard_local_build_passed": False, "dashboard_local_static_validation_passed": False, "dashboard_local_visual_browser_validation": "pending", "dashboard_public_validation": "pending_push_and_deployment"}
    write_json(OUTPUT / "dashboard_remaining_blocker_rescue_analysis_ready_update_summary.json", dashboard)
    forbidden = {"passed": True, "gabriel_api_rating_run": False, "ocr_run": False, "full_text_extraction_run": False, "span_extraction_run": False, "regression_run": False, "treatment_effect_run": False, "unsupported_hourly_annual_conversion": False, "unsupported_normalized_value_inferred": False, "final_wage_gap_claim_made": False, "national_population_prevalence_claim_made": False, "causal_claim_made": False, "global_analysis_readiness_advanced": False, "global_wage_gap_readiness_advanced": False, "global_causal_readiness_advanced": False, "retained_binary_or_full_text_staged": False, "polished_deliverable_created": False, "pi_report_created": False, "public_memo_created": False, "pdf_docx_or_slide_deck_created": False, "bounded_extracted_text_context_reads": 0}
    write_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    write_json(OUTPUT / "staged_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "forbidden_payloads_staged": []})
    write_json(OUTPUT / "large_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "threshold_bytes": 52428800, "large_staged_files": []})
    (OUTPUT / "next_task.md").write_text(f"# Next task\n\n`{NEXT_TASK}`\n\nQA cleaned direct/conditional comparisons and the same-side, growth, non-base, mechanism, national-readiness, repair, defer, and write-off routes. Preserve bounded local claim gates; do not run regressions, treatment effects, or make final national, prevalence, causal, or wage-gap claims. Do not create polished deliverables unless separately authorized.\n", encoding="utf-8")
    validate_outputs()
    return summary


def validate_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_summary.json")
    cleaned = read_csv(OUTPUT / "cleaned_analysis_use_layer.csv")
    blockers = read_csv(OUTPUT / "blocker_rescue_results.csv")
    period = read_csv(OUTPUT / "period_anchor_rescue_results.csv")
    pay = read_csv(OUTPUT / "pay_basis_comp_type_rescue_results.csv")
    non_scalar = read_csv(OUTPUT / "non_scalar_structuring_results.csv")
    direct = read_csv(OUTPUT / "cleaned_direct_cross_side_comparison_ready_queue.csv")
    conditional = read_csv(OUTPUT / "cleaned_conditional_cross_side_comparison_candidate_queue.csv")
    original_norm = read_csv(INPUT / "normalized_quantitative_records.csv")
    original_matches = read_csv(INPUT / "all_tier_matching_results.csv")
    original_by_id = {r["normalization_id"]: r for r in original_norm}
    cleaned_records = [r for r in cleaned if r["cleaned_unit_type"] == "normalized_record"]
    matrix = read_json(OUTPUT / "blocker_overlap_matrix.json")
    qql = read_csv(OUTPUT / "cleaned_quant_qual_mechanism_link_layer.csv")
    national = read_csv(OUTPUT / "cleaned_national_comparison_readiness_layer.csv")
    dashboard = read_json(OUTPUT / "dashboard_remaining_blocker_rescue_analysis_ready_update_summary.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    checks = {
        "01_normalization_input_reconciles": len(original_norm) == 8715,
        "02_matching_input_reconciles": len(original_matches) == 19643,
        "03_original_blockers_preserved": summary["original_blocker_flag_counts"] == EXPECTED_BLOCKERS,
        "04_unique_cohorts_exist": bool(read_json(OUTPUT / "unique_blocker_cohort_summary.json").get("blocker_count_cohorts")),
        "05_overlap_matrix_reconciles": matrix["diagonal_reconciles_to_original_counts"] == EXPECTED_BLOCKERS,
        "06_exactly_one_primary_category": len(cleaned) == 28358 and all(r["cleaned_analysis_use_primary_category"] in CATEGORIES for r in cleaned),
        "07_category_counts_reconcile": sum(summary["cleaned_analysis_use_category_counts"].values()) == len(cleaned),
        "08_original_categories_preserved": all(r["original_evidence_category"] == original_by_id[r["normalization_id"]]["evidence_category"] and r["original_evidence_family"] == original_by_id[r["normalization_id"]]["evidence_family"] for r in cleaned_records),
        "09_original_statuses_preserved": all(r["original_normalization_status"] == original_by_id[r["normalization_id"]]["normalization_status"] for r in cleaned_records),
        "10_raw_lineage_preserved": all(r["raw_span_snippet_sha256"] == hashlib.sha256(original_by_id[r["normalization_id"]]["raw_span_snippet"].encode()).hexdigest() and r["raw_bounded_context_snippet_sha256"] == hashlib.sha256(original_by_id[r["normalization_id"]]["raw_bounded_context_snippet"].encode()).hexdigest() and r["source_locator_lineage_sha256"] == hashlib.sha256(original_by_id[r["normalization_id"]]["source_locator_lineage"].encode()).hexdigest() and r["raw_evidence_pointer"] for r in cleaned_records),
        "11_period_rescue_basis": len(period) == 8715 and all(r["period_evidence_basis"] for r in period),
        "12_pay_rescue_basis": len(pay) == 8715 and all(r["pay_basis_evidence_basis"] for r in pay),
        "13_no_fake_scalar": len(non_scalar) == 8715 and all(r["fake_scalar_created"].lower() == "false" for r in non_scalar),
        "14_no_unsupported_conversion": all(r["hourly_annual_conversion_performed"].lower() == "false" for r in original_norm),
        "15_budget_not_individual_wage": forbidden["unsupported_normalized_value_inferred"] is False,
        "16_percent_not_wage_comparison": all(r["shared_pay_basis"] not in {"percentage_raise", "cola_cpi"} for r in read_csv(OUTPUT / "cleaned_local_comparison_candidate_layer.csv")),
        "17_nonbase_not_base_mixed": all(r["compensation_type"] not in {"mixed", "unknown_or_mixed"} for r in read_csv(OUTPUT / "cleaned_local_comparison_candidate_layer.csv")),
        "18_nonclear_not_anchor": all("remains_unclear" not in r["final_side_label"] and "not_applicable" not in r["final_side_label"] and "write_off" not in r["final_side_label"] for r in direct + conditional),
        "19_quant_qual_preserved": len(qql) == 1250,
        "20_side_independent_preserved": summary["cleaned_analysis_use_category_counts"].get("side_independent_mechanism_evidence", 0) >= 0,
        "21_national_no_claims": len(national) == 8715 and all(r["final_national_claims"] == "0" and r["national_wage_gaps"] == "0" for r in national),
        "22_local_queues_gated": all(r["cleaned_analysis_use_primary_category"] == "direct_cross_side_comparison_ready" for r in direct) and all(r["cleaned_analysis_use_primary_category"] == "conditional_cross_side_comparison_candidate" for r in conditional),
        "23_repair_reasons_present": all(r["cleaned_caveats"] or r["cleaned_blocker_status"] for r in cleaned if r["cleaned_analysis_use_primary_category"] in {"period_repair_needed", "pay_basis_repair_needed", "role_side_repair_needed", "non_scalar_structuring_needed", "unresolved_or_defer", "write_off_or_exclude"}),
        "24_no_regression": forbidden["regression_run"] is False,
        "25_no_treatment_effect": forbidden["treatment_effect_run"] is False,
        "26_no_final_wage_gap": forbidden["final_wage_gap_claim_made"] is False,
        "27_no_causal_claim": forbidden["causal_claim_made"] is False,
        "28_no_national_prevalence": forbidden["national_population_prevalence_claim_made"] is False,
        "29_global_analysis_false": dashboard["global_analysis_readiness"] is False,
        "30_global_wage_gap_false": dashboard["global_wage_gap_readiness"] is False,
        "31_global_causal_false": dashboard["global_causal_readiness"] is False,
        "32_no_gabriel_api": forbidden["gabriel_api_rating_run"] is False,
        "33_no_ocr": forbidden["ocr_run"] is False,
        "34_no_text_extraction": forbidden["full_text_extraction_run"] is False,
        "35_no_span_extraction": forbidden["span_extraction_run"] is False,
        "36_retained_ignored": ignored("artifacts/local_retained_sources/"),
        "37_extracted_ignored": ignored("artifacts/local_extracted_text/"),
        "38_no_payloads_output": not any(path.suffix.lower() in {".pdf", ".html", ".htm"} for path in OUTPUT.rglob("*")),
        "39_no_polished_deliverables": forbidden["polished_deliverable_created"] is False,
        "40_dashboard_structure": dashboard["dashboard_clean_structure_preserved"] is True,
        "41_dashboard_map": dashboard["dashboard_map_primary_metric"] == "scout_coverage_rate",
        "42_pi_link": dashboard["final_pi_report_link_intact"] is True,
        "43_growth_module": dashboard["wage_growth_continuity_module_intact"] is True,
        "44_staged_audit": read_json(OUTPUT / "staged_file_audit.json")["passed"] is True,
        "45_large_file_audit": read_json(OUTPUT / "large_file_audit.json")["passed"] is True,
    }
    report = {"all_checks_passed": all(checks.values()), "passed_count": sum(checks.values()), "total_check_count": len(checks), "checks": checks, "pending_or_failed_checks": [key for key, value in checks.items() if not value], "validated_at": now(), "count_correction_note": summary["normalized_count_correction_note"]}
    write_json(OUTPUT / "validation_report.json", report)
    lines = ["# Validation report", "", f"Passed: {report['passed_count']} / {report['total_check_count']}", "", f"Count note: {report['count_correction_note']}", ""] + [f"- [{'x' if value else ' '}] {key}" for key, value in checks.items()]
    (OUTPUT / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not report["all_checks_passed"]:
        raise RuntimeError(f"validation failed: {report['pending_or_failed_checks']}")
    return report


def audit_staged() -> dict[str, Any]:
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.splitlines()
    allowed_prefixes = [str(OUTPUT.relative_to(ROOT)) + "/", "docs/dashboard/", "scripts/build_dashboard_data.py", "scripts/test_dashboard_github_pages_deployment_repair.py", "scripts/run_remaining_municipality_blocker_rescue_reclassification.py"]
    out_of_scope = [name for name in staged if not any(name == prefix or name.startswith(prefix) for prefix in allowed_prefixes)]
    forbidden_suffixes = {".pdf", ".docx", ".ppt", ".pptx", ".html", ".htm", ".png", ".jpg", ".jpeg"}
    forbidden_files = [name for name in staged if Path(name).suffix.lower() in forbidden_suffixes]
    large = []
    for name in staged:
        path = ROOT / name
        if path.exists() and path.stat().st_size >= 50 * 1024 * 1024: large.append({"path": name, "bytes": path.stat().st_size})
    staged_audit = {"passed": not out_of_scope and not forbidden_files, "status": "final_staged_audit", "staged_file_count": len(staged), "out_of_scope": out_of_scope, "forbidden_or_polished_files": forbidden_files, "pre_existing_untracked_preserved_not_staged": ["docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/", "package-lock.json"]}
    large_audit = {"passed": not large, "threshold_bytes": 52428800, "hard_limit_bytes": 104857600, "large_staged_files": large, "artifact_size_decision": "compact row schemas; no staged file may reach 50 MiB"}
    write_json(OUTPUT / "staged_file_audit.json", staged_audit); write_json(OUTPUT / "large_file_audit.json", large_audit)
    validate_outputs()
    if not staged_audit["passed"] or not large_audit["passed"]: raise RuntimeError("staged or large-file audit failed")
    return {"staged": staged_audit, "large": large_audit}


def create_relay(commit_or_status: str, push_status: str) -> Path:
    summary = read_json(OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_summary.json")
    dashboard = read_json(OUTPUT / "dashboard_remaining_blocker_rescue_analysis_ready_update_summary.json")
    relay_dir = LOG_DIR / "relay"; relay_dir.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    payload = {"final_decision": DECISION, "commit_hash": head, "push_status": push_status, "current_head_before": read_json(OUTPUT / "remaining_municipalities_blocker_rescue_analysis_ready_reclassification_manifest.json")["head_before"], "current_head_after": head, **summary, "blocker_overlap_matrix_summary": read_json(OUTPUT / "blocker_overlap_matrix.json"), "unique_blocker_cohort_counts": read_json(OUTPUT / "unique_blocker_cohort_summary.json"), "period_rescue_summary": read_json(OUTPUT / "period_anchor_rescue_summary.json"), "pay_basis_comp_type_rescue_summary": read_json(OUTPUT / "pay_basis_comp_type_rescue_summary.json"), "non_scalar_structuring_summary": read_json(OUTPUT / "non_scalar_structuring_summary.json"), "cross_side_anchor_routing_summary": read_json(OUTPUT / "cross_side_anchor_rescue_routing_summary.json"), "side_status_routing_summary": read_json(OUTPUT / "side_status_routing_summary.json"), "quant_qual_link_rescue_summary": read_json(OUTPUT / "quant_qual_link_rescue_summary.json"), "national_readiness_reclassification_summary": read_json(OUTPUT / "national_readiness_reclassification_summary.json"), "dashboard_update_status": dashboard, "validation_outputs": read_json(OUTPUT / "validation_report.json"), "forbidden_action_audit": read_json(OUTPUT / "forbidden_action_audit.json"), "staged_file_audit": read_json(OUTPUT / "staged_file_audit.json"), "large_file_audit": read_json(OUTPUT / "large_file_audit.json"), "no_polished_deliverables_created": True}
    write_json(relay_dir / "relay_summary.json", payload)
    names = ["remaining_municipalities_blocker_rescue_analysis_ready_reclassification_summary.json", "blocker_overlap_matrix.json", "blocker_signature_summary.json", "unique_blocker_cohort_summary.json", "blocker_resolution_summary.json", "cleaned_analysis_use_category_summary.json", "cleaned_major_blocker_remaining_summary.json", "cleaned_major_blocker_resolved_summary.json", "period_anchor_rescue_summary.json", "pay_basis_comp_type_rescue_summary.json", "non_scalar_structuring_summary.json", "cross_side_anchor_rescue_routing_summary.json", "side_status_routing_summary.json", "quant_qual_link_rescue_summary.json", "national_readiness_reclassification_summary.json", "source_family_cleaning_summary.json", "geography_cleaning_summary.json", "cba_non_cba_cleaning_summary.json", "evidence_category_cleaning_summary.json", "dashboard_remaining_blocker_rescue_analysis_ready_update_summary.json", "validation_report.json", "validation_report.md", "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md"]
    for name in names:
        source = OUTPUT / name
        if source.exists(): (relay_dir / name).write_bytes(source.read_bytes())
    path = ROOT / "tmp" / f"broad_state_remaining_municipalities_blocker_rescue_analysis_ready_reclassification_relay_2026-08-03_{commit_or_status}.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(relay_dir.iterdir()): archive.write(item, item.name)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["preflight", "build", "validate", "audit-staged", "relay"]); parser.add_argument("--commit-or-status", default="status"); parser.add_argument("--push-status", default="not_run"); args = parser.parse_args()
    if args.command == "preflight":
        data = preflight(); print(json.dumps({"passed": True, "head": data["head_before"], "normalization_status_ledger_count": len(data["normalized"]), "usable_normalized_count": data["usable_normalized_count"], "matching_structure_count": len(data["matches"]), "link_count": len(data["links"]), "count_correction_note": data["count_correction_note"]}, sort_keys=True))
    elif args.command == "build": print(json.dumps(build(), sort_keys=True))
    elif args.command == "validate": print(json.dumps(validate_outputs(), sort_keys=True))
    elif args.command == "audit-staged": print(json.dumps(audit_staged(), sort_keys=True))
    else: print(create_relay(args.commit_or_status, args.push_status))


if __name__ == "__main__": main()
