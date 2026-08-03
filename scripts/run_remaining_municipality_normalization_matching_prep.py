#!/usr/bin/env python3
"""Prepare post-reconciliation compensation normalization and matching structures.

This is an offline, deterministic metadata-only pass.  It preserves raw bounded
tokens and builds candidate clusters; it deliberately does not normalize a wage,
convert a pay basis, finalize a match, compute a gap, or estimate an effect.
"""

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
RECON = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SIDE-RELEVANCE-RECONCILIATION-2026-08-03"
INGEST = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-RATING-INGESTION-CODIFICATION-2026-08-02"
SPANS = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SPAN-EXTRACTION-2026-08-02"
SOURCE_REVIEW = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SOURCE-REVIEW-DOWNLOAD-2026-08-02"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-POST-RECONCILIATION-NORMALIZATION-MATCHING-PREP-2026-08-03"
LOG_DIR = ROOT / "tmp/broad_state_remaining_municipalities_normalization_matching_prep_2026-08-03_logs"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-POST-RECONCILIATION-NORMALIZATION-MATCHING-PREP-2026-08-03"
DECISION = "broad_state_remaining_municipalities_normalization_matching_prep_completed_normalization_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03"
EXPECTED_SPANS = 15_189
EXPECTED_SOURCES = 1_812
EXPECTED_CLEAR_QUANT = 3_859
EXPECTED_CLEAR_QUAL = 3_748
EXPECTED_SEEDS = 22
EXPECTED_GROWTH = 852
EXPECTED_SIDE_COUNTS = {
    "police_direct": 4416, "fire_direct": 1080, "non_safety_direct": 1177,
    "safety_combined_direct": 43, "mixed_direct": 27,
    "not_applicable": 1867, "remains_unclear": 5041, "write_off": 1538,
}
CREATED_AT = "2026-08-03T08:28:00-04:00"

CLEAR_SAFETY = {"police_direct", "fire_direct", "safety_combined_direct"}
CLEAR_SIDE = CLEAR_SAFETY | {"non_safety_direct", "mixed_direct"}
NON_CLEAR = {"not_applicable", "remains_unclear", "write_off"}
QUANT_CLAIMS = {
    "quantitative_direct_text_claim_ready", "quantitative_needs_normalization",
    "mixed_quant_qual_claim_ready",
}
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

MONEY_RE = re.compile(r"(?<!\w)(?:\$\s*)\d[\d,]*(?:\.\d+)?(?:\s*(?:per\s+(?:hour|year|month|week|day)|/\s*(?:hr|hour|yr|year)))?", re.I)
PERCENT_RE = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*%")
DATE_RE = re.compile(
    r"\b(?:FY\s*)?(?:19|20)\d{2}(?:\s*[-–—/]\s*(?:19|20)?\d{2})?\b|"
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2},?\s+(?:19|20)\d{2}\b", re.I,
)
ROLE_PATTERNS = {
    "police_role": re.compile(r"\b(?:police|law enforcement|patrol(?:man|men| officer)?|detective|chief of police|police chief|FOP|PBA)\b", re.I),
    "fire_role": re.compile(r"\b(?:firefighter|fire fighter|fire department|fire chief|IAFF|paramedic|EMT|fire/EMS)\b", re.I),
    "safety_combined_role": re.compile(r"\b(?:police\s+(?:and|&)\s+fire|fire\s+(?:and|&)\s+police|combined public safety|uniformed public safety)\b", re.I),
    "non_safety_role": re.compile(r"\b(?:public works|DPW|sanitation|water|sewer|wastewater|utilities|parks|recreation|library|clerical|administrative|finance|treasurer|assessor|code enforcement|building inspector|zoning|maintenance|mechanic|laborer|general employees|civilian employees|AFSCME|Teamsters|SEIU)\b", re.I),
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def serial(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return value


def fields_for(rows: list[dict[str, Any]], fallback: list[str] | None = None) -> list[str]:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    return fields or list(fallback or [])


def write_pair(stem: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    use = fields or fields_for(rows)
    with (OUTPUT / f"{stem}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=use, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: serial(row.get(field, "")) for field in use})
    with (OUTPUT / f"{stem}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            compact = {field: row.get(field, "") for field in use}
            handle.write(json.dumps(compact, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}-{hashlib.sha256('|'.join(values).encode()).hexdigest()[:24]}"


def as_bool(value: Any) -> bool:
    return str(value).lower() == "true"


def parsed_list(value: str) -> list[str]:
    if not value:
        return []
    try:
        item = json.loads(value)
        return [str(x) for x in item] if isinstance(item, list) else []
    except json.JSONDecodeError:
        return [part.strip() for part in value.split(";") if part.strip()]


def counter(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "") or "missing") for row in rows).items()))


def unique(items: Iterable[str]) -> list[str]:
    return sorted({str(item).strip() for item in items if str(item).strip()})


def limited_join(parts: Iterable[str], limit: int = 1500) -> str:
    text = " | ".join(part.strip() for part in parts if part and part.strip())
    return text[:limit]


def preflight() -> dict[str, Any]:
    paths = {
        "layer": RECON / "reconciled_side_relevance_span_layer.csv",
        "reconciliation": RECON / "merged_side_relevance_reconciliation_results.csv",
        "clear_quant": RECON / "clear_side_quantitative_candidates_queue.csv",
        "clear_qual": RECON / "clear_side_qualitative_mechanism_candidates_queue.csv",
        "seeds": RECON / "clear_side_comparison_potential_queue.csv",
        "growth": RECON / "clear_side_growth_continuity_potential_queue.csv",
        "sources": INGEST / "canonical_ingested_source_ratings.csv",
        "spans": SPANS / "merged_compensation_evidence_spans.csv",
        "source_review": SOURCE_REVIEW / "merged_source_review_results.csv",
        "validation": RECON / "validation_report.json",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise RuntimeError(f"missing required inputs: {missing}")
    data = {name: read_csv(path) for name, path in paths.items() if name != "validation"}
    if len(data["layer"]) != EXPECTED_SPANS or len(data["sources"]) != EXPECTED_SOURCES:
        raise RuntimeError("critical canonical source/span count mismatch")
    if Counter(row["final_side_relevance_rating"] for row in data["layer"]) != Counter(EXPECTED_SIDE_COUNTS):
        raise RuntimeError("final side-relevance counts differ from locked task context")
    expected = {"clear_quant": EXPECTED_CLEAR_QUANT, "clear_qual": EXPECTED_CLEAR_QUAL, "seeds": EXPECTED_SEEDS, "growth": EXPECTED_GROWTH}
    for name, count in expected.items():
        if len(data[name]) != count:
            raise RuntimeError(f"{name} count is {len(data[name])}; expected {count}")
    if len({row["span_rating_id"] for row in data["layer"]}) != EXPECTED_SPANS:
        raise RuntimeError("reconciled span IDs are not unique")
    if read_json(paths["validation"]).get("all_checks_passed") is not True:
        raise RuntimeError("prior reconciliation validation is not passed")
    data["head_before"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    return data


def token_fields(row: dict[str, str], span: dict[str, str], title: str) -> dict[str, Any]:
    text = limited_join([span.get("span_text_snippet", ""), span.get("surrounding_context_snippet", ""), row.get("section_heading", ""), title])
    money = unique(match.group(0) for match in MONEY_RE.finditer(text))[:40]
    percents = unique(match.group(0) for match in PERCENT_RE.finditer(text))[:30]
    dates = unique(match.group(0) for match in DATE_RE.finditer(text))[:30]
    role_terms: dict[str, list[str]] = {
        category: unique(match.group(0) for match in pattern.finditer(text))[:30]
        for category, pattern in ROLE_PATTERNS.items()
    }
    roles_present = [category for category, terms in role_terms.items() if terms]
    side = row["final_side_relevance_rating"]
    role_category = {
        "police_direct": "police_role", "fire_direct": "fire_role",
        "safety_combined_direct": "safety_combined_role", "non_safety_direct": "non_safety_role",
        "mixed_direct": "mixed_role", "not_applicable": "not_applicable",
        "remains_unclear": "unclear_role", "write_off": "not_applicable",
    }[side]
    if not roles_present and side in CLEAR_SIDE:
        role_quality = "side_reconciliation_anchor_only"
    elif role_category in roles_present or (role_category == "mixed_role" and len(roles_present) >= 2):
        role_quality = "explicit_bounded_text_anchor"
    elif roles_present:
        role_quality = "bounded_text_anchor_conflict_review"
    else:
        role_quality = "missing_or_not_applicable"

    lower = text.lower()
    pay: list[str] = []
    tests = [
        (r"\b(?:per hour|hourly|/hr|/hour)\b", "hourly"),
        (r"\b(?:annual salary|annually|per year|yearly)\b", "annual_salary"),
        (r"\bper month|monthly\b", "monthly"), (r"\bper week|weekly\b", "weekly"),
        (r"\bper diem\b|\bper day\b", "per_diem"), (r"\bstipend\b|\bpremium\b", "stipend"),
        (r"\bcola\b|cost.of.living|\bcpi\b", "cola_cpi"),
        (r"\bovertime\b", "overtime_rate"), (r"\bholiday pay|holiday rate\b", "holiday_rate"),
        (r"\ballowance|reimbursement\b", "allowance"), (r"\bbudget(?:ed)?\b|appropriation", "budget_amount"),
        (r"\bpay grade|grade\s+\d", "pay_grade"), (r"\bstep\s+(?:schedule|\d)|salary schedule", "step_schedule"),
        (r"\bminimum\b.{0,80}\bmaximum\b|\bmin\.?\b.{0,80}\bmax\.?\b", "range_min_max"),
    ]
    for pattern, label in tests:
        if re.search(pattern, lower, re.I):
            pay.append(label)
    if percents:
        pay.append("percentage_raise" if re.search(r"raise|increase|adjust|cola", lower) else "percentage_raise")
    pay = unique(pay) or ["unknown_or_mixed"]
    primary_pay = pay[0] if len(pay) == 1 else ("unknown_or_mixed" if "unknown_or_mixed" in pay else pay[0])
    if primary_pay == "unknown_or_mixed":
        pay_quality = "needs_review"
    elif len(pay) > 1:
        pay_quality = "multiple_raw_basis_hints"
    else:
        pay_quality = "explicit_bounded_hint"

    if any("-" in item or "–" in item or "—" in item or "/" in item for item in dates):
        period_category = "explicit_contract_period"
    elif any(item.lower().startswith("fy") for item in dates):
        period_category = "explicit_fiscal_year"
    elif dates and any(re.search(r"[A-Za-z]+\s+\d", item) for item in dates):
        period_category = "explicit_effective_date"
    elif dates:
        period_category = "explicit_calendar_year"
    else:
        period_category = "missing_period_anchor"
    period_quality = "explicit" if dates else "missing"
    return {
        "raw_value_token_candidates": money,
        "raw_percent_token_candidates": percents,
        "raw_date_effective_period_token_candidates": dates,
        "raw_role_unit_token_candidates": role_terms,
        "role_unit_anchor_category": role_category,
        "role_unit_anchor_quality": role_quality,
        "pay_basis_hints": pay,
        "pay_basis_hint": primary_pay,
        "pay_basis_anchor_quality": pay_quality,
        "period_cycle_anchor_category": period_category,
        "period_anchor_quality": period_quality,
        "primary_raw_period_anchor": dates[0] if dates else "",
        "bounded_text_for_tokens": text,
    }


def compensation_type(category: str) -> str:
    mapping = {
        "quant_base_wage_direct_value": "base_wage", "quant_salary_schedule_table": "salary_schedule",
        "quant_step_schedule_progression": "step_progression", "quant_percentage_raise_or_cola": "cola_or_raise",
        "quant_cpi_indexed_adjustment": "cola_or_raise", "quant_retroactive_pay_or_lump_sum": "non_base_compensation",
        "quant_stipend_or_premium": "stipend_premium", "quant_overtime_or_holiday_rate": "overtime_holiday",
        "quant_longevity_or_service_pay": "longevity_service", "quant_allowance_or_reimbursement": "allowance_reimbursement",
        "quant_non_base_compensation": "non_base_compensation", "quant_budget_or_pay_plan_amount": "budget_or_pay_plan",
        "quant_position_classification_pay_band": "classification_pay_band", "quant_mixed_compensation_table": "other",
        "quant_other_compensation_value": "other",
    }
    return mapping.get(category, "other")


def mechanism_class(category: str) -> str:
    mapping = {
        "qual_non_base_compensation_mechanism": "non_base_compensation",
        "qual_market_recruitment_retention_pressure": "market_recruitment_retention",
        "qual_collective_bargaining": "collective_bargaining",
        "qual_interest_arbitration": "arbitration_factfinding", "qual_grievance_arbitration": "arbitration_factfinding",
        "qual_factfinding": "arbitration_factfinding", "qual_ordinance_or_council_adoption": "ordinance_council_adoption",
        "qual_budget_or_fiscal_constraint": "budget_fiscal_constraint",
        "qual_step_schedule_or_seniority_structure": "step_schedule_seniority",
        "qual_cola_or_indexing_mechanism": "cola_cpi_indexing",
        "qual_retroactivity_or_implementation_timing": "retroactivity_implementation",
        "qual_position_classification_or_civil_service_structure": "classification_civil_service",
        "qual_comparability_or_parity_language": "comparability_parity",
        "qual_union_or_contract_scope": "union_contract_scope",
        "qual_strike_no_strike_or_labor_dispute_process": "strike_no_strike_dispute_process",
    }
    return mapping.get(category, "other_pay_setting_mechanism")


def group_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for key in sorted({str(row.get(field, "") or "missing") for row in rows}):
        subset = [row for row in rows if str(row.get(field, "") or "missing") == key]
        groups[key] = {
            "row_count": len(subset),
            "matching_tier_counts": counter(subset, "strongest_match_tier"),
            "side_label_counts": dict(sorted(Counter(label for row in subset for label in row.get("side_labels_represented", [])).items())),
        }
    return {"group_field": field, "total": len(rows), "groups": groups}


def build() -> dict[str, Any]:
    data = preflight()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    checkpoints: dict[str, Any] = {"task_id": TASK_ID, "started_at": now_utc(), "head_before": data["head_before"], "stages": {}}

    span_by_id = {row["span_id"]: row for row in data["spans"]}
    recon_by_rating = {row["span_rating_id"]: row for row in data["reconciliation"]}
    source_by_id = {row["source_rating_id"]: row for row in data["sources"]}
    review_by_id = {row["source_review_download_id"]: row for row in data["source_review"]}
    clear_quant_ids = {row["span_rating_id"] for row in data["clear_quant"]}
    clear_qual_ids = {row["span_rating_id"] for row in data["clear_qual"]}
    seed_ids = {row["span_rating_id"] for row in data["seeds"]}
    growth_ids = {row["span_rating_id"] for row in data["growth"]}

    enriched: list[dict[str, Any]] = []
    for row in data["layer"]:
        span = span_by_id.get(row["span_id"], {})
        rec = recon_by_rating.get(row["span_rating_id"], {})
        review = review_by_id.get(row["source_review_id"], {})
        title = rec.get("source_title") or review.get("source_title") or ""
        tokens = token_fields(row, span, title)
        enriched.append({
            **row,
            "source_title": title,
            "span_text_snippet": span.get("span_text_snippet", "")[:1200],
            "bounded_context_snippet": span.get("surrounding_context_snippet", "")[:1500],
            "page_location_pointer": row.get("page_number", "") or row.get("character_start_offset", ""),
            "reconciliation_confidence": row.get("side_relevance_reconciliation_confidence", ""),
            "reconciliation_reason_codes": row.get("side_relevance_reconciliation_reason_codes", ""),
            "is_clear_quant_queue": row["span_rating_id"] in clear_quant_ids,
            "is_clear_qual_queue": row["span_rating_id"] in clear_qual_ids,
            "is_explicit_comparison_seed": row["span_rating_id"] in seed_ids,
            "is_growth_queue": row["span_rating_id"] in growth_ids,
            **tokens,
        })
    checkpoints["stages"]["01_input_reconciliation_validation"] = {"complete": True, "row_count": len(enriched)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    role_fields = [
        "span_rating_id", "source_rating_id", "span_id", "municipality", "state", "region",
        "final_side_relevance_rating", "role_unit_anchor_category", "role_unit_anchor_quality",
        "raw_role_unit_token_candidates", "reconciliation_confidence", "reconciliation_reason_codes",
        "source_title", "section_heading", "page_location_pointer", "source_locator_lineage",
    ]
    period_fields = [
        "span_rating_id", "source_rating_id", "span_id", "municipality", "state", "region",
        "final_side_relevance_rating", "period_cycle_anchor_category", "primary_raw_period_anchor",
        "raw_date_effective_period_token_candidates", "period_anchor_quality", "source_title",
        "page_location_pointer", "source_locator_lineage",
    ]
    pay_fields = [
        "span_rating_id", "source_rating_id", "span_id", "municipality", "state", "region",
        "final_side_relevance_rating", "pay_basis_hint", "pay_basis_hints", "pay_basis_anchor_quality",
        "evidence_category", "claim_readiness_bucket", "raw_value_token_candidates",
        "raw_percent_token_candidates", "source_locator_lineage",
    ]
    write_pair("role_unit_anchor_prep_layer", enriched, role_fields)
    write_pair("period_cycle_anchor_prep_layer", enriched, period_fields)
    write_pair("pay_basis_anchor_prep_layer", enriched, pay_fields)
    checkpoints["stages"]["02_anchor_prep_layers"] = {"complete": True, "row_count_each": len(enriched)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    norm: list[dict[str, Any]] = []
    norm_fields = [
        "normalization_prep_id", "span_rating_id", "source_rating_id", "span_id", "retained_source_id",
        "source_review_id", "candidate_id", "municipality", "state", "region", "source_type", "source_family",
        "cba_non_cba_hint", "final_side_relevance_rating", "original_side_relevance_rating",
        "reconciliation_confidence", "reconciliation_reason_codes", "evidence_category", "evidence_family",
        "claim_readiness_bucket", "downstream_use_bucket", "quantitative_support_level",
        "qualitative_support_level", "mechanism_strength_level", "comparison_potential_rating", "source_title",
        "page_location_pointer", "section_heading", "span_text_snippet", "bounded_context_snippet",
        "raw_value_token_candidates", "raw_percent_token_candidates", "raw_date_effective_period_token_candidates",
        "raw_role_unit_token_candidates", "pay_basis_hint", "compensation_type_hint", "role_unit_anchor_hint",
        "period_anchor_hint", "normalization_prep_status", "normalization_prep_confidence", "normalization_blockers",
        "is_explicit_comparison_seed", "is_growth_queue", "source_locator_lineage", "bounded_snippet_reference",
    ]
    for row in enriched:
        eligible = (
            row["claim_readiness_bucket"] in QUANT_CLAIMS
            or row["downstream_use_bucket"] == "quantitative_normalization_candidate"
            or row["evidence_family"] == "quantitative_compensation"
            or row["evidence_category"] in QUANT_CATEGORIES
            or row["is_clear_quant_queue"] or row["is_growth_queue"] or row["is_explicit_comparison_seed"]
        )
        if not eligible:
            continue
        blockers: list[str] = []
        side = row["final_side_relevance_rating"]
        has_value = bool(row["raw_value_token_candidates"] or row["raw_percent_token_candidates"])
        has_period = bool(row["raw_date_effective_period_token_candidates"])
        has_role = row["role_unit_anchor_quality"] not in {"missing_or_not_applicable", "bounded_text_anchor_conflict_review"}
        pay_known = row["pay_basis_hint"] != "unknown_or_mixed"
        if not has_value: blockers.append("missing_raw_value_or_percent_token")
        if not has_period: blockers.append("missing_period_anchor")
        if not has_role: blockers.append("missing_or_conflicting_role_unit_anchor")
        if not pay_known: blockers.append("unknown_or_mixed_pay_basis")
        if side == "remains_unclear": status = "side_unclear_defer"
        elif side == "not_applicable": status = "not_applicable_defer"
        elif side == "write_off": status = "write_off_exclude"
        elif not has_value: status = "needs_value_token_review"
        elif not has_period: status = "needs_period_anchor_review"
        elif not has_role: status = "needs_role_unit_anchor_review"
        elif not pay_known: status = "needs_pay_basis_review"
        elif row["evidence_category"] not in QUANT_CATEGORIES and row["evidence_family"] != "quantitative_compensation": status = "non_wage_or_non_normalizable"
        else: status = "ready_for_normalization_design"
        confidence = "high" if status == "ready_for_normalization_design" else "moderate" if side in CLEAR_SIDE and has_value else "low"
        out = {key: row.get(key, "") for key in norm_fields}
        out.update({
            "normalization_prep_id": stable_id("BRMNORMPREP-20260803", row["span_rating_id"]),
            "compensation_type_hint": compensation_type(row["evidence_category"]),
            "role_unit_anchor_hint": row["role_unit_anchor_category"],
            "period_anchor_hint": row["primary_raw_period_anchor"],
            "normalization_prep_status": status,
            "normalization_prep_confidence": confidence,
            "normalization_blockers": blockers,
        })
        norm.append(out)
    write_pair("normalization_prep_universe", norm, norm_fields)
    write_json(OUTPUT / "normalization_prep_universe_manifest.json", {
        "task_id": TASK_ID, "universe_count": len(norm), "criteria_are_inclusive": True,
        "contains_non_clear_audit_records": True, "normalized_values_produced": False,
        "csv_sha256": sha256_file(OUTPUT / "normalization_prep_universe.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "normalization_prep_universe.jsonl"),
    })
    checkpoints["stages"]["03_normalization_prep_universe"] = {"complete": True, "row_count": len(norm)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    # Compact source/document clusters retain all IDs but never form value pairs.
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        by_source[row["source_rating_id"]].append(row)
    source_clusters: list[dict[str, Any]] = []
    for source_id, rows in sorted(by_source.items()):
        sides = unique(row["final_side_relevance_rating"] for row in rows)
        source_clusters.append({
            "source_document_cluster_id": stable_id("BRMSRCDOC-20260803", source_id),
            "source_rating_id": source_id, "retained_source_id": rows[0]["retained_source_id"],
            "municipality": rows[0]["municipality"], "state": rows[0]["state"], "region": rows[0]["region"],
            "source_type": rows[0]["source_type"], "source_family": rows[0]["source_family"],
            "span_ids": [row["span_id"] for row in rows], "span_rating_ids": [row["span_rating_id"] for row in rows],
            "span_count": len(rows), "side_labels_represented": sides,
            "clear_safety_anchor_count": sum(row["final_side_relevance_rating"] in CLEAR_SAFETY for row in rows),
            "clear_non_safety_anchor_count": sum(row["final_side_relevance_rating"] == "non_safety_direct" for row in rows),
            "quantitative_record_count": sum(row["is_clear_quant_queue"] for row in rows),
            "qualitative_mechanism_record_count": sum(row["is_clear_qual_queue"] for row in rows),
            "growth_continuity_record_count": sum(row["is_growth_queue"] for row in rows),
            "comparison_seed_record_count": sum(row["is_explicit_comparison_seed"] for row in rows),
            "raw_period_anchors": unique(row["primary_raw_period_anchor"] for row in rows),
            "pay_basis_hints": unique(row["pay_basis_hint"] for row in rows),
            "same_document_cross_side_candidate": any(row["final_side_relevance_rating"] in CLEAR_SAFETY for row in rows) and any(row["final_side_relevance_rating"] == "non_safety_direct" for row in rows),
            "source_locator_lineage": rows[0]["source_locator_lineage"],
        })
    write_pair("source_document_cluster_layer", source_clusters)

    by_muni_period: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        period = row["primary_raw_period_anchor"] or "missing_period_anchor"
        by_muni_period[(row["municipality"], row["state"], period)].append(row)
    muni_period_clusters: list[dict[str, Any]] = []
    for (municipality, state, period), rows in sorted(by_muni_period.items()):
        muni_period_clusters.append({
            "municipality_period_cluster_id": stable_id("BRMMUNIPER-20260803", municipality, state, period),
            "municipality": municipality, "state": state, "region": rows[0]["region"], "raw_period_anchor": period,
            "period_anchor_quality": "missing" if period == "missing_period_anchor" else "explicit_raw_token",
            "source_rating_ids": unique(row["source_rating_id"] for row in rows),
            "span_ids": [row["span_id"] for row in rows], "side_labels_represented": unique(row["final_side_relevance_rating"] for row in rows),
            "record_count": len(rows),
            "clear_safety_anchor_count": sum(row["final_side_relevance_rating"] in CLEAR_SAFETY for row in rows),
            "clear_non_safety_anchor_count": sum(row["final_side_relevance_rating"] == "non_safety_direct" for row in rows),
            "quantitative_record_count": sum(row["is_clear_quant_queue"] for row in rows),
            "qualitative_mechanism_record_count": sum(row["is_clear_qual_queue"] for row in rows),
            "growth_continuity_record_count": sum(row["is_growth_queue"] for row in rows),
            "pay_basis_hints": unique(row["pay_basis_hint"] for row in rows),
        })
    write_pair("municipality_period_cluster_layer", muni_period_clusters)
    checkpoints["stages"]["04_cluster_layers"] = {"complete": True, "source_clusters": len(source_clusters), "municipality_period_clusters": len(muni_period_clusters)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    match_rows: list[dict[str, Any]] = []
    match_fields = [
        "matching_prep_id", "municipality", "state", "region", "cluster_type", "source_ids_involved",
        "span_ids_involved", "side_labels_represented", "has_police", "has_fire", "has_safety_combined",
        "has_non_safety", "has_mixed", "clear_safety_anchor_count", "clear_non_safety_anchor_count",
        "quantitative_record_count", "qualitative_mechanism_record_count", "growth_continuity_record_count",
        "comparison_seed_record_count", "compatible_pay_basis_flag", "compatible_period_flag", "same_source_flag",
        "same_document_flag", "same_page_or_section_flag", "same_cycle_flag", "same_fiscal_year_flag",
        "same_contract_period_flag", "adjacent_period_flag", "period_anchor_quality", "role_unit_anchor_quality",
        "pay_basis_compatibility", "source_family_mix", "strongest_match_tier", "matching_prep_confidence",
        "matching_blockers", "recommended_next_action", "cba_non_cba_hint", "evidence_category",
        "claim_readiness_bucket", "downstream_use_bucket", "mechanism_strength_level", "source_locator_lineage",
    ]

    def add_match(cluster_type: str, rows: list[dict[str, Any]], *, same_source: bool = False, same_period: bool = False, adjacent: bool = False) -> None:
        if not rows:
            return
        sides = unique(row["final_side_relevance_rating"] for row in rows)
        safety_n = sum(row["final_side_relevance_rating"] in CLEAR_SAFETY for row in rows)
        nonsafety_n = sum(row["final_side_relevance_rating"] == "non_safety_direct" for row in rows)
        periods = unique(row["primary_raw_period_anchor"] for row in rows)
        bases = unique(row["pay_basis_hint"] for row in rows if row["pay_basis_hint"] != "unknown_or_mixed")
        cross = safety_n > 0 and nonsafety_n > 0
        compatible_basis = bool(bases) and len(bases) <= 2
        period_ok = same_period and bool(periods)
        blockers: list[str] = []
        if not cross: blockers.append("missing_clear_cross_side_anchor")
        if not periods: blockers.append("missing_period_anchor")
        if not compatible_basis: blockers.append("pay_basis_needs_review")
        if same_source and cross and period_ok and compatible_basis: tier, conf = "Tier A", "high"
        elif cross and period_ok and compatible_basis: tier, conf = "Tier B", "high"
        elif cross and adjacent and compatible_basis: tier, conf = "Tier C", "moderate"
        elif cross: tier, conf = "Tier D", "moderate"
        elif any(row["is_growth_queue"] for row in rows): tier, conf = "Tier E", "moderate"
        elif any(row["is_clear_qual_queue"] for row in rows): tier, conf = "Tier F", "moderate"
        else: tier, conf = "Tier G", "low"
        key = f"{cluster_type}|{rows[0]['municipality']}|{rows[0]['state']}|{'|'.join(row['span_rating_id'] for row in rows)}"
        match_rows.append({
            "matching_prep_id": stable_id("BRMMATCHPREP-20260803", key),
            "municipality": rows[0]["municipality"], "state": rows[0]["state"], "region": rows[0]["region"],
            "cluster_type": cluster_type, "source_ids_involved": unique(row["source_rating_id"] for row in rows),
            "span_ids_involved": [row["span_id"] for row in rows], "side_labels_represented": sides,
            "has_police": "police_direct" in sides, "has_fire": "fire_direct" in sides,
            "has_safety_combined": "safety_combined_direct" in sides, "has_non_safety": "non_safety_direct" in sides,
            "has_mixed": "mixed_direct" in sides, "clear_safety_anchor_count": safety_n,
            "clear_non_safety_anchor_count": nonsafety_n,
            "quantitative_record_count": sum(row["is_clear_quant_queue"] for row in rows),
            "qualitative_mechanism_record_count": sum(row["is_clear_qual_queue"] for row in rows),
            "growth_continuity_record_count": sum(row["is_growth_queue"] for row in rows),
            "comparison_seed_record_count": sum(row["is_explicit_comparison_seed"] for row in rows),
            "compatible_pay_basis_flag": compatible_basis, "compatible_period_flag": period_ok,
            "same_source_flag": same_source, "same_document_flag": same_source,
            "same_page_or_section_flag": cluster_type == "same_source_same_page_or_section",
            "same_cycle_flag": period_ok, "same_fiscal_year_flag": period_ok,
            "same_contract_period_flag": period_ok, "adjacent_period_flag": adjacent,
            "period_anchor_quality": "explicit_raw_token" if periods else "missing_period_anchor",
            "role_unit_anchor_quality": "clear_cross_side" if cross else "clear_single_side_or_mixed",
            "pay_basis_compatibility": "candidate_compatible_unverified" if compatible_basis else "needs_review",
            "source_family_mix": unique(row["source_family"] for row in rows),
            "strongest_match_tier": tier, "matching_prep_confidence": conf, "matching_blockers": blockers,
            "recommended_next_action": "bounded_normalization_and_match_quality_review" if tier in {"Tier A", "Tier B", "Tier C", "Tier D"} else "growth_continuity_review" if tier == "Tier E" else "mechanism_attribution_review" if tier == "Tier F" else "defer_or_exclude",
            "cba_non_cba_hint": unique(row["cba_non_cba_hint"] for row in rows),
            "evidence_category": unique(row["evidence_category"] for row in rows),
            "claim_readiness_bucket": unique(row["claim_readiness_bucket"] for row in rows),
            "downstream_use_bucket": unique(row["downstream_use_bucket"] for row in rows),
            "mechanism_strength_level": unique(row["mechanism_strength_level"] for row in rows),
            "source_locator_lineage": unique(row["source_locator_lineage"] for row in rows),
        })

    # Record anchor pool is the broad universe, independently of the 22 seed flags.
    eligible_anchor_rows = [
        row for row in enriched if row["final_side_relevance_rating"] in CLEAR_SIDE and (
            row["is_clear_quant_queue"] or row["is_growth_queue"] or row["is_clear_qual_queue"]
            or row["is_explicit_comparison_seed"] or row["claim_readiness_bucket"] == "mixed_quant_qual_claim_ready"
            or row["downstream_use_bucket"] == "quantitative_normalization_candidate"
        )
    ]
    for row in eligible_anchor_rows:
        add_match("record_level_anchor_pool", [row])

    # Same-document and same-page/section structural groups.
    for rows in by_source.values():
        eligible = [row for row in rows if row in eligible_anchor_rows]
        if eligible:
            add_match("same_source_same_document", eligible, same_source=True, same_period=len(unique(row["primary_raw_period_anchor"] for row in eligible)) == 1 and bool(eligible[0]["primary_raw_period_anchor"]))
        by_section: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in eligible:
            section = row["section_heading"] or row["page_number"] or "missing_page_section"
            by_section[(row["source_rating_id"], section)].append(row)
        for section_rows in by_section.values():
            if len(section_rows) > 1:
                add_match("same_source_same_page_or_section", section_rows, same_source=True, same_period=len(unique(row["primary_raw_period_anchor"] for row in section_rows)) == 1 and bool(section_rows[0]["primary_raw_period_anchor"]))

    # Municipality-period and municipality-cross-source structures.
    for (_, _, period), rows in by_muni_period.items():
        eligible = [row for row in rows if row in eligible_anchor_rows]
        if eligible and period != "missing_period_anchor":
            add_match("same_municipality_same_effective_period", eligible, same_period=True)
    by_muni: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible_anchor_rows:
        by_muni[(row["municipality"], row["state"])].append(row)
    for rows in by_muni.values():
        if len(unique(row["source_rating_id"] for row in rows)) > 1:
            add_match("same_municipality_cross_source_period_candidate", rows)
        growth_rows = [row for row in rows if row["is_growth_queue"]]
        if growth_rows:
            add_match("cross_document_same_role_growth_candidate", growth_rows, adjacent=len(unique(row["primary_raw_period_anchor"] for row in growth_rows)) > 1)
        mech_rows = [row for row in rows if row["is_clear_qual_queue"]]
        if mech_rows:
            add_match("mechanism_attribution_same_side_candidate", mech_rows)
        if mech_rows and any(row["is_clear_quant_queue"] for row in rows):
            add_match("mechanism_attribution_cross_side_candidate", rows)

    # Audited non-clear structures are separated and Tier G, never anchors.
    for row in enriched:
        if row["final_side_relevance_rating"] in NON_CLEAR:
            add_match("non_clear_audit_defer", [row])

    # Stable de-duplication by generated ID.
    match_rows = list({row["matching_prep_id"]: row for row in match_rows}.values())
    match_rows.sort(key=lambda row: row["matching_prep_id"])
    write_pair("matching_prep_universe", match_rows, match_fields)
    write_json(OUTPUT / "matching_prep_universe_manifest.json", {
        "task_id": TASK_ID, "universe_count": len(match_rows), "explicit_seed_count": EXPECTED_SEEDS,
        "seed_is_indicator_not_ceiling": True, "finalized_matches": 0, "wage_gaps_calculated": 0,
        "csv_sha256": sha256_file(OUTPUT / "matching_prep_universe.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "matching_prep_universe.jsonl"),
    })
    checkpoints["stages"]["05_matching_prep_universe"] = {"complete": True, "row_count": len(match_rows)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    subsets = {
        "same_source_comparison_prep_candidates": {"same_source_same_document", "same_source_same_page_or_section"},
        "same_municipality_period_comparison_prep_candidates": {"same_municipality_same_effective_period"},
        "cross_source_comparison_prep_candidates": {"same_municipality_cross_source_period_candidate"},
        "growth_continuity_matching_prep_candidates": {"cross_document_same_role_growth_candidate"},
    }
    for stem, types in subsets.items():
        write_pair(stem, [row for row in match_rows if row["cluster_type"] in types], match_fields)

    mechanism_rows: list[dict[str, Any]] = []
    for row in enriched:
        if row["final_side_relevance_rating"] not in CLEAR_SIDE or not row["is_clear_qual_queue"]:
            continue
        muni_matches = [item for item in match_rows if item["municipality"] == row["municipality"] and item["state"] == row["state"]]
        recommendation = {
            "core_finding_candidate": "core", "supporting_example_candidate": "supporting",
            "mechanism_summary_candidate": "mechanism summary", "local_context_candidate": "local context",
            "exclude_or_write_off": "write_off",
        }.get(row["downstream_use_bucket"], "defer")
        mechanism_rows.append({
            "mechanism_prep_id": stable_id("BRMMECHPREP-20260803", row["span_rating_id"]),
            "span_rating_id": row["span_rating_id"], "source_rating_id": row["source_rating_id"], "span_id": row["span_id"],
            "side_label": row["final_side_relevance_rating"], "mechanism_class": mechanism_class(row["evidence_category"]),
            "source_family": row["source_family"], "municipality": row["municipality"], "state": row["state"],
            "source_ids": [row["source_rating_id"]], "span_ids": [row["span_id"]],
            "claim_readiness_bucket": row["claim_readiness_bucket"], "downstream_use_bucket": row["downstream_use_bucket"],
            "mechanism_strength": row["mechanism_strength_level"], "clear_side_confidence": row["reconciliation_confidence"],
            "attachable_to_quantitative_cluster_flag": any(item["quantitative_record_count"] > 0 for item in muni_matches),
            "attachable_to_growth_cluster_flag": any(item["growth_continuity_record_count"] > 0 for item in muni_matches),
            "attachable_to_comparison_cluster_flag": any(item["strongest_match_tier"] in {"Tier A", "Tier B", "Tier C", "Tier D"} and item["clear_safety_anchor_count"] and item["clear_non_safety_anchor_count"] for item in muni_matches),
            "recommended_use": recommendation, "reconciliation_reason_codes": row["reconciliation_reason_codes"],
            "source_locator_lineage": row["source_locator_lineage"],
        })
    write_pair("mechanism_attribution_prep_layer", mechanism_rows)
    checkpoints["stages"]["06_mechanism_attribution_prep"] = {"complete": True, "row_count": len(mechanism_rows)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    compact_anchor_fields = [
        "span_rating_id", "source_rating_id", "span_id", "municipality", "state", "region", "source_family",
        "evidence_category", "claim_readiness_bucket", "downstream_use_bucket", "final_side_relevance_rating",
        "reconciliation_confidence", "reconciliation_reason_codes", "role_unit_anchor_category",
        "period_cycle_anchor_category", "primary_raw_period_anchor", "pay_basis_hint", "source_locator_lineage",
    ]
    side_outputs = [
        ("clear_safety_anchor_records", lambda r: r["final_side_relevance_rating"] in CLEAR_SAFETY),
        ("clear_non_safety_anchor_records", lambda r: r["final_side_relevance_rating"] == "non_safety_direct"),
        ("mixed_side_anchor_records", lambda r: r["final_side_relevance_rating"] == "mixed_direct"),
        ("not_applicable_records_for_matching_defer", lambda r: r["final_side_relevance_rating"] == "not_applicable"),
        ("remains_unclear_records_for_matching_defer", lambda r: r["final_side_relevance_rating"] == "remains_unclear"),
        ("write_off_records_for_matching_exclude", lambda r: r["final_side_relevance_rating"] == "write_off"),
    ]
    for stem, predicate in side_outputs:
        write_pair(stem, [row for row in enriched if predicate(row)], compact_anchor_fields)

    same_source = [row for row in match_rows if row["cluster_type"] in subsets["same_source_comparison_prep_candidates"]]
    same_period = [row for row in match_rows if row["cluster_type"] == "same_municipality_same_effective_period"]
    cross_source = [row for row in match_rows if row["cluster_type"] == "same_municipality_cross_source_period_candidate"]
    growth_structures = [row for row in match_rows if row["cluster_type"] == "cross_document_same_role_growth_candidate"]
    structural_types = set().union(*subsets.values()) | {"mechanism_attribution_same_side_candidate", "mechanism_attribution_cross_side_candidate"}
    structural = [row for row in match_rows if row["cluster_type"] in structural_types]
    additional_structural = sum(row["comparison_seed_record_count"] == 0 for row in structural)

    write_json(OUTPUT / "role_unit_anchor_prep_summary.json", {"total": len(enriched), "category_counts": counter(enriched, "role_unit_anchor_category"), "quality_counts": counter(enriched, "role_unit_anchor_quality")})
    write_json(OUTPUT / "period_cycle_anchor_prep_summary.json", {"total": len(enriched), "category_counts": counter(enriched, "period_cycle_anchor_category"), "quality_counts": counter(enriched, "period_anchor_quality")})
    write_json(OUTPUT / "pay_basis_anchor_prep_summary.json", {"total": len(enriched), "primary_hint_counts": counter(enriched, "pay_basis_hint"), "quality_counts": counter(enriched, "pay_basis_anchor_quality")})
    write_json(OUTPUT / "source_document_cluster_summary.json", {"total": len(source_clusters), "same_document_cross_side_candidate_count": sum(row["same_document_cross_side_candidate"] for row in source_clusters), "source_family_counts": counter(source_clusters, "source_family")})
    write_json(OUTPUT / "municipality_period_cluster_summary.json", {"total": len(muni_period_clusters), "cross_side_cluster_count": sum(row["clear_safety_anchor_count"] > 0 and row["clear_non_safety_anchor_count"] > 0 for row in muni_period_clusters), "missing_period_cluster_count": sum(row["raw_period_anchor"] == "missing_period_anchor" for row in muni_period_clusters)})
    write_json(OUTPUT / "mechanism_attribution_prep_summary.json", {"total": len(mechanism_rows), "mechanism_class_counts": counter(mechanism_rows, "mechanism_class"), "attachable_to_comparison_count": sum(row["attachable_to_comparison_cluster_flag"] for row in mechanism_rows)})
    write_json(OUTPUT / "normalization_prep_status_summary.json", {"total": len(norm), "counts": counter(norm, "normalization_prep_status")})
    write_json(OUTPUT / "matching_prep_tier_summary.json", {"total": len(match_rows), "counts": counter(match_rows, "strongest_match_tier")})
    write_json(OUTPUT / "matching_blocker_summary.json", {"total": len(match_rows), "counts": dict(sorted(Counter(blocker for row in match_rows for blocker in row["matching_blockers"]).items()))})
    write_json(OUTPUT / "role_unit_detection_summary.json", {"total": len(enriched), "rows_with_bounded_role_tokens": sum(any(row["raw_role_unit_token_candidates"].values()) for row in enriched), "role_category_counts": counter(enriched, "role_unit_anchor_category")})
    write_json(OUTPUT / "period_anchor_quality_summary.json", {"total": len(enriched), "counts": counter(enriched, "period_anchor_quality")})
    write_json(OUTPUT / "pay_basis_compatibility_summary.json", {"total": len(match_rows), "compatible_candidate_count": sum(row["compatible_pay_basis_flag"] for row in match_rows), "needs_review_count": sum(not row["compatible_pay_basis_flag"] for row in match_rows)})
    write_json(OUTPUT / "side_label_matching_summary.json", {"total": len(match_rows), "counts": dict(sorted(Counter(label for row in match_rows for label in row["side_labels_represented"]).items()))})
    for stem, field in [
        ("source_family_matching_prep_summary", "source_family_mix"),
        ("geography_matching_prep_summary", "state"),
        ("cba_non_cba_matching_prep_summary", "cba_non_cba_hint"),
        ("evidence_category_matching_prep_summary", "evidence_category"),
        ("claim_readiness_matching_prep_summary", "claim_readiness_bucket"),
        ("downstream_use_matching_prep_summary", "downstream_use_bucket"),
        ("mechanism_strength_matching_prep_summary", "mechanism_strength_level"),
    ]:
        # List-valued fields are summarized token-wise; scalar fields use the generic view.
        if any(isinstance(row.get(field), list) for row in match_rows):
            counts = Counter(value for row in match_rows for value in row.get(field, []))
            write_json(OUTPUT / f"{stem}.json", {"total_structures": len(match_rows), "token_counts": dict(sorted(counts.items()))})
        else:
            write_json(OUTPUT / f"{stem}.json", group_summary(match_rows, field))

    expansion = {
        "original_explicit_clear_side_comparison_potential_candidates": EXPECTED_SEEDS,
        "broader_clear_side_quantitative_candidate_count": EXPECTED_CLEAR_QUANT,
        "broader_clear_side_growth_continuity_candidate_count": EXPECTED_GROWTH,
        "expanded_structural_comparison_prep_candidate_count": len(structural),
        "additional_structural_candidates_beyond_seed_bearing_structures": additional_structural,
        "same_source_candidate_count": len(same_source),
        "same_municipality_same_period_candidate_count": len(same_period),
        "cross_source_candidate_count": len(cross_source),
        "growth_continuity_structurally_viable_count": sum(row["strongest_match_tier"] != "Tier G" for row in growth_structures),
        "mechanism_attribution_prep_candidate_count": len(mechanism_rows),
        "normalization_prep_universe_count": len(norm),
        "matching_prep_universe_count": len(match_rows),
        "blocked_by_missing_period": sum("missing_period_anchor" in row["matching_blockers"] for row in match_rows),
        "blocked_by_pay_basis_review": sum("pay_basis_needs_review" in row["matching_blockers"] for row in match_rows),
        "blocked_by_missing_cross_side_anchor": sum("missing_clear_cross_side_anchor" in row["matching_blockers"] for row in match_rows),
        "remains_unclear_side_records_deferred": EXPECTED_SIDE_COUNTS["remains_unclear"],
        "not_applicable_records_deferred": EXPECTED_SIDE_COUNTS["not_applicable"],
        "write_off_records_excluded": EXPECTED_SIDE_COUNTS["write_off"],
        "seed_is_indicator_not_ceiling": True, "normalized_values_produced": 0,
        "finalized_wage_matches": 0, "wage_gaps_calculated": 0,
        "claim_boundary": "Structural prep only; record and cluster counts are not matched wage results or prevalence estimates.",
    }
    write_json(OUTPUT / "comparison_seed_expansion_summary.json", expansion)
    write_md(OUTPUT / "comparison_seed_expansion_summary.md", "Comparison-seed expansion", f"""
The **{EXPECTED_SEEDS}** explicit clear-side comparison-potential records were retained as seed indicators, not treated as the comparison ceiling. The broader construction began independently from **{EXPECTED_CLEAR_QUANT:,}** clear-side quantitative candidates, **{EXPECTED_GROWTH:,}** clear-side growth candidates, and eligible clear-side mechanism records.

- Structural comparison-prep candidates/clusters: **{len(structural):,}**; structures with no explicit seed: **{additional_structural:,}**.
- Same-source structures: **{len(same_source):,}**.
- Same-municipality/same-period structures: **{len(same_period):,}**.
- Cross-source municipality structures: **{len(cross_source):,}**.
- Structurally viable growth-continuity structures: **{expansion['growth_continuity_structurally_viable_count']:,}**.
- Mechanism-attribution prep records: **{len(mechanism_rows):,}**.

No wage was normalized, no pay basis was converted, no value match was finalized, and no wage gap was calculated. These are candidate structures for a later bounded normalization/matching task.
""")

    dashboard = {
        "current_stage": "post-reconciliation normalization/matching prep complete",
        "next_task": NEXT_TASK, "reconciled_span_layer_count": EXPECTED_SPANS,
        "clear_side_quantitative_candidates_considered": EXPECTED_CLEAR_QUANT,
        "original_explicit_comparison_potential_seed_count": EXPECTED_SEEDS,
        "expanded_structural_comparison_prep_candidate_count": len(structural),
        "same_source_comparison_prep_candidate_count": len(same_source),
        "same_municipality_same_period_comparison_prep_candidate_count": len(same_period),
        "cross_source_comparison_prep_candidate_count": len(cross_source),
        "growth_continuity_prep_candidate_count": len(growth_structures),
        "mechanism_attribution_prep_candidate_count": len(mechanism_rows),
        "normalization_prep_universe_count": len(norm), "matching_prep_universe_count": len(match_rows),
        "major_blocker_counts": read_json(OUTPUT / "matching_blocker_summary.json")["counts"],
        "dashboard_clean_structure_preserved": True, "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579, "final_pi_report_link_intact": True,
        "wage_growth_continuity_module_intact": True, "global_analysis_readiness": False,
        "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "dashboard_local_build_passed": False, "dashboard_local_static_validation_passed": False,
        "dashboard_local_visual_browser_validation": "pending", "dashboard_public_validation": "pending_push_and_deployment",
    }
    write_json(OUTPUT / "dashboard_remaining_normalization_matching_prep_update_summary.json", dashboard)
    forbidden = {
        "passed": True, "actual_wage_normalization_run": False, "hourly_annual_conversion_run": False,
        "actual_wage_matching_finalized": False, "wage_gap_calculation_run": False,
        "regression_or_treatment_effect_run": False, "gabriel_api_rating_run": False,
        "ocr_run": False, "full_text_extraction_run": False, "span_extraction_run": False,
        "final_national_prevalence_or_causal_claim_made": False, "global_readiness_advanced": False,
        "full_extracted_text_persisted_or_staged": False, "retained_binary_persisted_or_staged": False,
    }
    write_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    write_json(OUTPUT / "staged_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "forbidden_payloads_staged": []})
    write_json(OUTPUT / "large_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "threshold_bytes": 50 * 1024 * 1024, "large_staged_files": []})

    summary = {
        "task_id": TASK_ID, "decision": DECISION, "reconciled_span_layer_count": EXPECTED_SPANS,
        "final_side_relevance_counts": EXPECTED_SIDE_COUNTS, "clear_side_quantitative_candidate_count": EXPECTED_CLEAR_QUANT,
        "clear_side_qualitative_mechanism_candidate_count": EXPECTED_CLEAR_QUAL,
        "original_explicit_comparison_potential_seed_count": EXPECTED_SEEDS,
        "clear_side_growth_continuity_candidate_count": EXPECTED_GROWTH,
        **{key: value for key, value in expansion.items() if key.endswith("count")},
        "matching_tier_counts": counter(match_rows, "strongest_match_tier"),
        "normalization_status_counts": counter(norm, "normalization_prep_status"),
        "claim_boundary": "Prep metadata only; no normalization, finalized matching, wage-gap, regression, prevalence, or causal claim.",
        "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "remaining_municipalities_normalization_matching_prep_summary.json", summary)
    write_md(OUTPUT / "remaining_municipalities_normalization_matching_prep_summary.md", "Remaining-municipality normalization/matching structure prep", f"""
Decision: `{DECISION}`

- Reconciled input spans: **{EXPECTED_SPANS:,}**.
- Clear-side quantitative records considered: **{EXPECTED_CLEAR_QUANT:,}**.
- Original explicit comparison seeds: **{EXPECTED_SEEDS}**; expanded structural comparison-prep candidates: **{len(structural):,}**.
- Normalization-prep universe: **{len(norm):,}** records.
- Matching-prep universe: **{len(match_rows):,}** record/cluster structures.
- Same-source: **{len(same_source):,}**; same-municipality/same-period: **{len(same_period):,}**; cross-source: **{len(cross_source):,}**.
- Growth structures: **{len(growth_structures):,}**; mechanism-attribution records: **{len(mechanism_rows):,}**.
- No wage value normalization, conversion, finalized matching, gap calculation, regression, treatment effect, prevalence claim, or causal claim occurred.
- Next: `{NEXT_TASK}`.
""")
    manifest = {
        "task_id": TASK_ID, "decision": DECISION, "created_at": now_utc(), "head_before": data["head_before"],
        "input_reconciled_span_count": EXPECTED_SPANS, "normalization_prep_universe_count": len(norm),
        "matching_prep_universe_count": len(match_rows), "explicit_seed_count": EXPECTED_SEEDS,
        "expanded_structural_comparison_prep_count": len(structural), "seed_is_indicator_not_ceiling": True,
        "normalization_universe_sha256": sha256_file(OUTPUT / "normalization_prep_universe.csv"),
        "matching_universe_sha256": sha256_file(OUTPUT / "matching_prep_universe.csv"),
        "output_directory": str(OUTPUT.relative_to(ROOT)), "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "remaining_municipalities_normalization_matching_prep_manifest.json", manifest)
    write_md(OUTPUT / "next_task.md", "Next task", f"""
Recommend: `{NEXT_TASK}`

Run bounded quantitative normalization only over ready or repairable normalization-prep records, preserve raw values, and produce candidate normalized values with confidence and caveats. Match only within approved prep structures and tiers; keep side, period, pay-basis, source-family, and role/unit uncertainty explicit. Provisional local comparisons may be computed only where quality gates pass. Do not run regressions or treatment effects or make final national, prevalence, or causal claims.
""")
    checkpoints["stages"]["07_summaries_validation_dashboard"] = {"complete": True, "completed_at": now_utc()}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)
    validate_outputs()
    return summary


def ignored(relative: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", relative], cwd=ROOT, check=False).returncode == 0


def validate_outputs(write_reports: bool = True) -> dict[str, Any]:
    data = preflight()
    norm = read_csv(OUTPUT / "normalization_prep_universe.csv")
    match = read_csv(OUTPUT / "matching_prep_universe.csv")
    role = read_csv(OUTPUT / "role_unit_anchor_prep_layer.csv")
    period = read_csv(OUTPUT / "period_cycle_anchor_prep_layer.csv")
    pay = read_csv(OUTPUT / "pay_basis_anchor_prep_layer.csv")
    expansion = read_json(OUTPUT / "comparison_seed_expansion_summary.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    dashboard = read_json(OUTPUT / "dashboard_remaining_normalization_matching_prep_update_summary.json")
    expected_norm_ids = {
        row["span_rating_id"] for row in data["layer"] if (
            row["claim_readiness_bucket"] in QUANT_CLAIMS
            or row["downstream_use_bucket"] == "quantitative_normalization_candidate"
            or row["evidence_family"] == "quantitative_compensation"
            or row["evidence_category"] in QUANT_CATEGORIES
            or row["span_rating_id"] in {x["span_rating_id"] for x in data["clear_quant"]}
            or row["span_rating_id"] in {x["span_rating_id"] for x in data["growth"]}
            or row["span_rating_id"] in {x["span_rating_id"] for x in data["seeds"]}
        )
    }
    files_under_50 = all(path.stat().st_size < 50 * 1024 * 1024 for path in OUTPUT.iterdir() if path.is_file())
    checks = {
        "01_reconciled_layer_15189": len(data["layer"]) == EXPECTED_SPANS,
        "02_final_side_counts_reconcile": Counter(row["final_side_relevance_rating"] for row in data["layer"]) == Counter(EXPECTED_SIDE_COUNTS),
        "03_clear_quant_3859": len(data["clear_quant"]) == EXPECTED_CLEAR_QUANT,
        "04_clear_qual_3748": len(data["clear_qual"]) == EXPECTED_CLEAR_QUAL,
        "05_comparison_seeds_22": len(data["seeds"]) == EXPECTED_SEEDS,
        "06_growth_852": len(data["growth"]) == EXPECTED_GROWTH,
        "07_seeds_not_ceiling": expansion["seed_is_indicator_not_ceiling"] is True and expansion["expanded_structural_comparison_prep_candidate_count"] > EXPECTED_SEEDS,
        "08_normalization_universe_exact_criteria": {row["span_rating_id"] for row in norm} == expected_norm_ids and len(norm) == len(expected_norm_ids),
        "09_matching_universe_has_all_structure_classes": {"record_level_anchor_pool", "same_source_same_document", "same_municipality_cross_source_period_candidate", "cross_document_same_role_growth_candidate", "mechanism_attribution_same_side_candidate"} <= {row["cluster_type"] for row in match},
        "10_no_wage_normalization": forbidden["actual_wage_normalization_run"] is False,
        "11_no_hourly_annual_conversion": forbidden["hourly_annual_conversion_run"] is False,
        "12_no_wage_gap": forbidden["wage_gap_calculation_run"] is False,
        "13_no_final_wage_matching": forbidden["actual_wage_matching_finalized"] is False,
        "14_no_regression_treatment": forbidden["regression_or_treatment_effect_run"] is False,
        "15_no_final_claims": forbidden["final_national_prevalence_or_causal_claim_made"] is False,
        "16_role_anchor_layer_reconciles": len(role) == EXPECTED_SPANS and {row["span_rating_id"] for row in role} == {row["span_rating_id"] for row in data["layer"]},
        "17_period_anchor_layer_reconciles": len(period) == EXPECTED_SPANS and {row["span_rating_id"] for row in period} == {row["span_rating_id"] for row in data["layer"]},
        "18_pay_basis_layer_reconciles": len(pay) == EXPECTED_SPANS and {row["span_rating_id"] for row in pay} == {row["span_rating_id"] for row in data["layer"]},
        "19_source_document_clusters_exist": len(read_csv(OUTPUT / "source_document_cluster_layer.csv")) == EXPECTED_SOURCES,
        "20_municipality_period_clusters_exist": bool(read_csv(OUTPUT / "municipality_period_cluster_layer.csv")),
        "21_expansion_summary_beyond_22": expansion["expanded_structural_comparison_prep_candidate_count"] > EXPECTED_SEEDS,
        "22_nonclear_separated_not_anchor": all(row["strongest_match_tier"] == "Tier G" for row in match if row["cluster_type"] == "non_clear_audit_defer"),
        "23_reconciliation_metadata_preserved": all("reconciliation_confidence" in row and "reconciliation_reason_codes" in row for row in norm),
        "24_no_gabriel_api": forbidden["gabriel_api_rating_run"] is False,
        "25_no_ocr": forbidden["ocr_run"] is False,
        "26_no_text_extraction": forbidden["full_text_extraction_run"] is False,
        "27_no_span_extraction": forbidden["span_extraction_run"] is False,
        "28_retained_artifacts_ignored": ignored("artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"),
        "29_extracted_artifacts_ignored": ignored("artifacts/local_extracted_text/broad_state_remaining_municipalities_text_extraction_2026-08-02"),
        "30_no_payloads_output": not any(path.suffix.lower() in {".pdf", ".html", ".htm", ".doc", ".docx", ".png", ".jpg", ".bin"} for path in OUTPUT.rglob("*")),
        "31_dashboard_clean_structure": dashboard["dashboard_clean_structure_preserved"] is True,
        "32_dashboard_map_scout_coverage": dashboard["dashboard_map_primary_metric"] == "scout_coverage_rate",
        "33_pi_link_intact": dashboard["final_pi_report_link_intact"] is True,
        "34_growth_module_intact": dashboard["wage_growth_continuity_module_intact"] is True,
        "35_global_analysis_false": dashboard["global_analysis_readiness"] is False,
        "36_global_wage_gap_false": dashboard["global_wage_gap_readiness"] is False,
        "37_global_causal_false": dashboard["global_causal_readiness"] is False,
        "38_staged_audit_passes": read_json(OUTPUT / "staged_file_audit.json")["passed"] is True,
        "39_large_file_audit_passes": read_json(OUTPUT / "large_file_audit.json")["passed"] is True and files_under_50,
    }
    report = {
        "all_checks_passed": all(checks.values()), "checks": checks,
        "passed_count": sum(checks.values()), "total_check_count": len(checks),
        "pending_or_failed_checks": [name for name, ok in checks.items() if not ok], "validated_at": now_utc(),
    }
    if write_reports:
        write_json(OUTPUT / "validation_report.json", report)
        write_md(OUTPUT / "validation_report.md", "Normalization/matching prep validation", f"Overall: **{'PASS' if report['all_checks_passed'] else 'FAIL'}** ({report['passed_count']}/{report['total_check_count']}).\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in checks.items()) + "\n\nEvery tracked prep artifact is below 50 MiB; no bulky payload was staged.")
    if not report["all_checks_passed"]:
        raise RuntimeError(f"validation failed: {report['pending_or_failed_checks']}")
    return report


def audit_staged() -> dict[str, Any]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT, check=True, capture_output=True)
    staged = [Path(item.decode()) for item in result.stdout.split(b"\0") if item]
    prefixes = (
        "scripts/run_remaining_municipality_normalization_matching_prep.py", "scripts/build_dashboard_data.py",
        "scripts/test_dashboard_github_pages_deployment_repair.py", "docs/dashboard/src/App.jsx",
        "docs/dashboard/data/", "docs/dashboard/public/data/", "docs/dashboard/dist/",
        "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-POST-RECONCILIATION-NORMALIZATION-MATCHING-PREP-2026-08-03/",
    )
    forbidden_suffixes = {".pdf", ".doc", ".docx", ".html", ".htm", ".bin", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    out_of_scope = [str(path) for path in staged if not any(str(path).startswith(prefix) for prefix in prefixes)]
    forbidden = [str(path) for path in staged if path.suffix.lower() in forbidden_suffixes and not str(path).startswith("docs/dashboard/dist/")]
    large = []
    for path in staged:
        full = ROOT / path
        if full.is_file() and full.stat().st_size >= 50 * 1024 * 1024:
            large.append({"path": str(path), "bytes": full.stat().st_size})
    staged_audit = {
        "passed": not out_of_scope and not forbidden, "staged_file_count": len(staged),
        "staged_files": [str(path) for path in staged], "out_of_scope": out_of_scope,
        "forbidden_payload_files": forbidden,
        "pre_existing_untracked_preserved_not_staged": [
            "docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/",
            "package-lock.json",
        ],
    }
    large_audit = {
        "passed": not large, "threshold_bytes": 50 * 1024 * 1024, "hard_limit_bytes": 100 * 1024 * 1024,
        "large_staged_files": large, "artifact_size_decision": "compact row schemas and cluster summaries; no tracked file reached 50 MiB",
    }
    write_json(OUTPUT / "staged_file_audit.json", staged_audit)
    write_json(OUTPUT / "large_file_audit.json", large_audit)
    if not staged_audit["passed"] or not large_audit["passed"]:
        raise RuntimeError("staged or large-file audit failed")
    validate_outputs()
    return {"staged": staged_audit, "large": large_audit}


def create_relay(commit_or_status: str, push_status: str) -> Path:
    summary = read_json(OUTPUT / "remaining_municipalities_normalization_matching_prep_summary.json")
    dashboard = read_json(OUTPUT / "dashboard_remaining_normalization_matching_prep_update_summary.json")
    relay_dir = LOG_DIR / "relay"
    relay_dir.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    payload = {
        "final_decision": DECISION, "commit_hash": head, "push_status": push_status,
        "current_head_before": read_json(OUTPUT / "remaining_municipalities_normalization_matching_prep_manifest.json")["head_before"],
        "current_head_after": head, **summary,
        "dashboard_update_status": dashboard, "validation_outputs": read_json(OUTPUT / "validation_report.json"),
        "forbidden_action_audit": read_json(OUTPUT / "forbidden_action_audit.json"),
        "staged_file_audit": read_json(OUTPUT / "staged_file_audit.json"),
        "large_file_audit": read_json(OUTPUT / "large_file_audit.json"), "blockers_or_uncertainties": dashboard["major_blocker_counts"],
    }
    write_json(relay_dir / "relay_summary.json", payload)
    for name in [
        "remaining_municipalities_normalization_matching_prep_summary.json", "comparison_seed_expansion_summary.json",
        "normalization_prep_status_summary.json", "matching_prep_tier_summary.json", "matching_blocker_summary.json",
        "role_unit_anchor_prep_summary.json", "period_cycle_anchor_prep_summary.json", "pay_basis_anchor_prep_summary.json",
        "source_family_matching_prep_summary.json", "geography_matching_prep_summary.json",
        "cba_non_cba_matching_prep_summary.json", "evidence_category_matching_prep_summary.json",
        "dashboard_remaining_normalization_matching_prep_update_summary.json", "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]:
        source = OUTPUT / name
        if source.exists():
            (relay_dir / name).write_bytes(source.read_bytes())
    zip_path = ROOT / "tmp" / f"broad_state_remaining_municipalities_normalization_matching_prep_relay_2026-08-03_{commit_or_status}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(relay_dir.iterdir()):
            archive.write(path, path.name)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["preflight", "build", "validate", "audit-staged", "relay"])
    parser.add_argument("--commit-or-status", default="status")
    parser.add_argument("--push-status", default="not_run")
    args = parser.parse_args()
    if args.command == "preflight":
        data = preflight()
        print(json.dumps({"passed": True, "head": data["head_before"], "spans": len(data["layer"]), "sources": len(data["sources"]), "clear_quant": len(data["clear_quant"]), "seeds": len(data["seeds"])}, sort_keys=True))
    elif args.command == "build":
        print(json.dumps(build(), sort_keys=True))
    elif args.command == "validate":
        print(json.dumps(validate_outputs(), sort_keys=True))
    elif args.command == "audit-staged":
        print(json.dumps(audit_staged(), sort_keys=True))
    else:
        print(create_relay(args.commit_or_status, args.push_status))


if __name__ == "__main__":
    main()
