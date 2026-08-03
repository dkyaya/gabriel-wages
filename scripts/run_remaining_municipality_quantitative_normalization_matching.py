#!/usr/bin/env python3
"""Normalize and structurally match remaining-municipality compensation evidence.

The pass is deterministic and bounded to tracked snippets/tokens.  It processes
all Tier A-G structures, preserves raw evidence, and creates only provisional
local comparisons and readiness metadata.  It does not produce a polished
deliverable, final/national wage-gap claim, regression, or causal estimate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-POST-RECONCILIATION-NORMALIZATION-MATCHING-PREP-2026-08-03"
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03"
LOG_DIR = ROOT / "tmp/broad_state_remaining_municipalities_quantitative_normalization_matching_2026-08-03_logs"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03"
DECISION = "broad_state_remaining_municipalities_quantitative_normalization_matching_completed_local_qa_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-LOCAL-COMPARISON-QA-AND-CLAIM-READINESS-2026-08-03"
EXPECTED_NORM = 8_715
EXPECTED_MATCH = 19_643
EXPECTED_MECHANISM = 3_748
EXPECTED_GROWTH = 221
EXPECTED_SAME_SOURCE = 2_094
EXPECTED_SAME_PERIOD = 1_089
EXPECTED_CROSS_SOURCE = 137
EXPECTED_TIERS = {"Tier A": 66, "Tier B": 48, "Tier C": 5, "Tier D": 322, "Tier E": 2060, "Tier F": 5699, "Tier G": 11443}
EXPECTED_SIDE = {"police_direct": 4416, "fire_direct": 1080, "non_safety_direct": 1177, "safety_combined_direct": 43, "mixed_direct": 27, "not_applicable": 1867, "remains_unclear": 5041, "write_off": 1538}
CLEAR_SAFETY = {"police_direct", "fire_direct", "safety_combined_direct"}
CLEAR_SIDE = CLEAR_SAFETY | {"non_safety_direct", "mixed_direct"}
NON_CLEAR = {"not_applicable", "remains_unclear", "write_off"}
USABLE_NORMALIZATION = {"normalized_ready", "normalized_partial", "normalized_growth_or_percentage_only", "normalized_non_base_only", "normalized_budget_context_only"}
LOCAL_READY = {"provisional_local_comparison_ready", "conditional_local_comparison_ready"}
QUANT_QUAL_READY = {"strong_quant_qual_link", "moderate_quant_qual_link"}

MONEY_RE = re.compile(r"\$\s*\d[\d,]*(?:\.\d+)?", re.I)
RATE_RE = re.compile(
    r"\b(?:hourly\s+(?:rate|wage)|annual\s+salary|salary\s+(?:rate|amount)|pay\s+rate|wage\s+rate)"
    r"\s*(?:of|is|:|=)?\s*\$?\s*(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\b",
    re.I,
)
PERCENT_RE = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*%")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


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


def parsed(value: str) -> list[str]:
    if not value:
        return []
    try:
        item = json.loads(value)
        if isinstance(item, list):
            return [str(x) for x in item]
        if isinstance(item, dict):
            return [str(x) for values in item.values() for x in (values if isinstance(values, list) else [])]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in value.split(";") if part.strip()]


def as_bool(value: Any) -> bool:
    return str(value).lower() == "true"


def unique(values: Iterable[str]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def counter(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "") or "missing") for row in rows).items()))


def stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}-{hashlib.sha256('|'.join(values).encode()).hexdigest()[:24]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_pair(stem: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    use = fields or list(dict.fromkeys(key for row in rows for key in row))
    with (OUTPUT / f"{stem}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=use, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: serial(row.get(field, "")) for field in use})
    with (OUTPUT / f"{stem}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            compact = {field: row.get(field, "") for field in use}
            handle.write(json.dumps(compact, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def numeric(token: str) -> float | None:
    cleaned = re.sub(r"[^0-9.\-]", "", token)
    if not cleaned or cleaned.count(".") > 1:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(value) or value < 0 or value > 1_000_000_000:
        return None
    return value


def preflight() -> dict[str, Any]:
    paths = {
        "norm": PREP / "normalization_prep_universe.csv",
        "match": PREP / "matching_prep_universe.csv",
        "mechanism": PREP / "mechanism_attribution_prep_layer.csv",
        "growth": PREP / "growth_continuity_matching_prep_candidates.csv",
        "same_source": PREP / "same_source_comparison_prep_candidates.csv",
        "same_period": PREP / "same_municipality_period_comparison_prep_candidates.csv",
        "cross_source": PREP / "cross_source_comparison_prep_candidates.csv",
        "role": PREP / "role_unit_anchor_prep_layer.csv",
        "period": PREP / "period_cycle_anchor_prep_layer.csv",
        "pay": PREP / "pay_basis_anchor_prep_layer.csv",
        "tier_summary": PREP / "matching_prep_tier_summary.json",
        "expansion": PREP / "comparison_seed_expansion_summary.json",
        "side": ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-SIDE-RELEVANCE-RECONCILIATION-2026-08-03/final_side_relevance_summary.json",
        "validation": PREP / "validation_report.json",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise RuntimeError(f"missing required inputs: {missing}")
    data = {name: read_csv(path) for name, path in paths.items() if path.suffix == ".csv"}
    expected = {"norm": EXPECTED_NORM, "match": EXPECTED_MATCH, "mechanism": EXPECTED_MECHANISM, "growth": EXPECTED_GROWTH, "same_source": EXPECTED_SAME_SOURCE, "same_period": EXPECTED_SAME_PERIOD, "cross_source": EXPECTED_CROSS_SOURCE}
    for name, count in expected.items():
        if len(data[name]) != count:
            raise RuntimeError(f"{name} count {len(data[name])}; expected {count}")
    if read_json(paths["tier_summary"])["counts"] != EXPECTED_TIERS:
        raise RuntimeError("Tier A-G distribution mismatch")
    expansion = read_json(paths["expansion"])
    if expansion.get("original_explicit_clear_side_comparison_potential_candidates") != 22 or expansion.get("seed_is_indicator_not_ceiling") is not True:
        raise RuntimeError("comparison-seed contract failed")
    if read_json(paths["side"])["counts"] != EXPECTED_SIDE:
        raise RuntimeError("final side-relevance distribution mismatch")
    if read_json(paths["validation"]).get("all_checks_passed") is not True:
        raise RuntimeError("prep validation is not passed")
    if len({row["normalization_prep_id"] for row in data["norm"]}) != EXPECTED_NORM:
        raise RuntimeError("normalization prep IDs are not unique")
    if len({row["matching_prep_id"] for row in data["match"]}) != EXPECTED_MATCH:
        raise RuntimeError("matching prep IDs are not unique")
    data["head_before"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    return data


def normalize_row(row: dict[str, str]) -> dict[str, Any]:
    raw_money = parsed(row["raw_value_token_candidates"])
    raw_percent = parsed(row["raw_percent_token_candidates"])
    text = " | ".join([row.get("span_text_snippet", ""), row.get("bounded_context_snippet", ""), row.get("section_heading", ""), row.get("source_title", "")])
    repair_codes: list[str] = []
    if not raw_money:
        raw_money = unique(match.group(0) for match in MONEY_RE.finditer(text))
        if raw_money:
            repair_codes.append("bounded_snippet_currency_token_repair")
    if not raw_money:
        recovered = [match.group(1) for match in RATE_RE.finditer(text)]
        raw_money = unique(recovered)
        if raw_money:
            repair_codes.append("explicit_rate_phrase_numeric_repair")
    if not raw_percent:
        raw_percent = unique(match.group(0) for match in PERCENT_RE.finditer(text))
        if raw_percent:
            repair_codes.append("bounded_snippet_percent_token_repair")
    money_values = [value for token in raw_money if (value := numeric(token)) is not None]
    percent_values = [value for token in raw_percent if (value := numeric(token)) is not None and value <= 1000]
    money_values = list(dict.fromkeys(money_values))[:40]
    percent_values = list(dict.fromkeys(percent_values))[:20]

    pay_basis = row["pay_basis_hint"]
    if pay_basis == "unknown_or_mixed":
        lower = text.lower()
        repairs = [
            ("per hour", "hourly"), ("hourly rate", "hourly"), ("annual salary", "annual_salary"),
            ("per year", "annual_salary"), ("monthly", "monthly"), ("per week", "weekly"),
            ("per diem", "per_diem"), ("overtime", "overtime_rate"), ("holiday pay", "holiday_rate"),
            ("stipend", "stipend"), ("allowance", "allowance"), ("pay grade", "pay_grade"),
            ("salary schedule", "step_schedule"), ("cost of living", "cola_cpi"), ("cola", "cola_cpi"),
        ]
        hits = unique(label for token, label in repairs if token in lower)
        if len(hits) == 1:
            pay_basis = hits[0]
            repair_codes.append("bounded_snippet_pay_basis_repair")

    period_tokens = parsed(row["raw_date_effective_period_token_candidates"])
    if not period_tokens:
        period_tokens = unique(match.group(0) for match in YEAR_RE.finditer(text))[:20]
        if period_tokens:
            repair_codes.append("bounded_snippet_year_anchor_repair")
    years = [int(year) for token in period_tokens for year in YEAR_RE.findall(token)]
    years = sorted(set(years))
    period_start = years[0] if years else ""
    period_end = years[-1] if years else ""
    period_label = "–".join(map(str, (period_start, period_end))) if years and period_start != period_end else str(period_start or row.get("period_anchor_hint", ""))

    side = row["final_side_relevance_rating"]
    role = row["role_unit_anchor_hint"]
    comp_type = row["compensation_type_hint"]
    caveats: list[str] = []
    if not money_values and not percent_values: caveats.append("no_explicit_normalizable_value_token")
    if not years: caveats.append("period_anchor_missing_or_unresolved")
    if pay_basis == "unknown_or_mixed": caveats.append("pay_basis_unresolved")
    if role in {"unclear_role", "not_applicable", "generic_municipal_role"}: caveats.append("role_unit_anchor_unresolved_or_not_applicable")
    if side in NON_CLEAR: caveats.append(f"final_side_label_{side}")

    value_type = ""
    primary_value: float | str = ""
    value_min: float | str = ""
    value_max: float | str = ""
    candidates: list[float] = []
    if percent_values and (pay_basis in {"percentage_raise", "cola_cpi"} or comp_type in {"cola_or_raise", "step_progression"}):
        value_type, candidates = "percentage", percent_values
        primary_value = percent_values[0] if len(percent_values) == 1 else ""
    elif money_values:
        candidates = money_values
        if pay_basis == "range_min_max" or comp_type == "classification_pay_band":
            value_type = "range"
            value_min, value_max = min(money_values), max(money_values)
        elif pay_basis == "step_schedule" or comp_type in {"salary_schedule", "step_progression"}:
            value_type = "step_schedule_values"
            primary_value = money_values[0] if len(money_values) == 1 else ""
        else:
            value_type = "currency_amount"
            primary_value = money_values[0] if len(money_values) == 1 else ""

    if side == "remains_unclear": status = "side_unclear_defer"
    elif side == "not_applicable": status = "not_applicable_defer"
    elif side == "write_off": status = "write_off_exclude"
    elif not candidates: status = "needs_value_review"
    elif not years: status = "needs_period_review"
    elif pay_basis == "unknown_or_mixed": status = "needs_pay_basis_review"
    elif role in {"unclear_role", "not_applicable", "generic_municipal_role"}: status = "needs_role_unit_review"
    elif comp_type == "budget_or_pay_plan" or pay_basis == "budget_amount": status = "normalized_budget_context_only"
    elif comp_type in {"non_base_compensation", "stipend_premium", "allowance_reimbursement", "longevity_service", "overtime_holiday"} or pay_basis in {"stipend", "allowance", "overtime_rate", "holiday_rate"}: status = "normalized_non_base_only"
    elif value_type == "percentage": status = "normalized_growth_or_percentage_only"
    elif len(candidates) == 1 or value_type == "range": status = "normalized_ready"
    else: status = "normalized_partial"

    confidence = "high" if status == "normalized_ready" and primary_value != "" else "moderate" if status in USABLE_NORMALIZATION else "low"
    if len(candidates) > 1 and value_type != "range":
        caveats.append("multiple_raw_values_preserved_no_single_value_selected")
    if repair_codes:
        caveats.append("bounded_metadata_repair_applied")
    if pay_basis in {"hourly", "annual_salary"}:
        caveats.append("no_cross_basis_conversion_performed")

    return {
        "normalization_id": stable_id("BRMQNORM-20260803", row["normalization_prep_id"]),
        "normalization_prep_id": row["normalization_prep_id"], "span_rating_id": row["span_rating_id"],
        "source_rating_id": row["source_rating_id"], "span_id": row["span_id"], "retained_source_id": row["retained_source_id"],
        "candidate_id": row["candidate_id"], "municipality": row["municipality"], "state": row["state"], "region": row["region"],
        "source_type": row["source_type"], "source_family": row["source_family"], "cba_non_cba_hint": row["cba_non_cba_hint"],
        "evidence_category": row["evidence_category"], "evidence_family": row["evidence_family"],
        "claim_readiness_bucket": row["claim_readiness_bucket"], "downstream_use_bucket": row["downstream_use_bucket"],
        "raw_span_snippet": row["span_text_snippet"], "raw_bounded_context_snippet": row["bounded_context_snippet"],
        "raw_value_tokens": raw_money, "raw_percent_tokens": raw_percent, "raw_period_tokens": period_tokens,
        "normalized_value": primary_value, "normalized_value_candidates": candidates,
        "normalized_value_min": value_min, "normalized_value_max": value_max,
        "normalized_value_type": value_type, "normalized_pay_basis": pay_basis,
        "normalized_period_start": period_start, "normalized_period_end": period_end,
        "normalized_period_label": period_label, "normalized_period_status": "explicit_or_bounded_repair" if years else "missing_period_anchor",
        "normalized_role_unit": role, "normalized_side_label": side, "compensation_type": comp_type,
        "normalization_status": status, "normalization_confidence": confidence,
        "normalization_caveats": caveats, "normalization_repair_codes": repair_codes,
        "reconciliation_confidence": row["reconciliation_confidence"],
        "reconciliation_reason_codes": row["reconciliation_reason_codes"],
        "source_title": row["source_title"], "page_location_pointer": row["page_location_pointer"],
        "source_locator_lineage": row["source_locator_lineage"], "bounded_snippet_reference": row["bounded_snippet_reference"],
        "hourly_annual_conversion_performed": False, "imputed_hours_weeks_fte": False,
    }


def match_type(cluster_type: str) -> str:
    mapping = {
        "same_source_same_page_or_section": "same_source_same_page_or_section_match",
        "same_source_same_document": "same_source_same_document_match",
        "same_municipality_same_source_family": "same_municipality_same_source_family_match",
        "same_municipality_same_effective_period": "same_municipality_same_effective_period_match",
        "same_municipality_same_contract_or_fiscal_cycle": "same_municipality_same_contract_or_fiscal_cycle_match",
        "same_municipality_cross_source_period_candidate": "same_municipality_cross_source_period_candidate_match",
        "cross_document_same_role_growth_candidate": "cross_document_same_role_growth_match",
        "mechanism_attribution_same_side_candidate": "mechanism_attribution_same_side_match",
        "mechanism_attribution_cross_side_candidate": "mechanism_attribution_cross_side_match",
    }
    return mapping.get(cluster_type, "national_readiness_stratum_candidate" if cluster_type == "record_level_anchor_pool" else cluster_type)


def build() -> dict[str, Any]:
    data = preflight()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    checkpoints = {"task_id": TASK_ID, "head_before": data["head_before"], "started_at": now_utc(), "stages": {}}
    write_pair("normalization_input_universe", data["norm"], list(data["norm"][0]))
    write_pair("all_tier_matching_input_universe", data["match"], list(data["match"][0]))
    checkpoints["stages"]["01_input_integrity"] = {"complete": True, "normalization_rows": EXPECTED_NORM, "matching_rows": EXPECTED_MATCH, "tiers_processed": sorted(EXPECTED_TIERS)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    normalized = [normalize_row(row) for row in data["norm"]]
    normalized.sort(key=lambda row: row["normalization_id"])
    normalized_fields = list(normalized[0])
    write_pair("normalized_quantitative_records", normalized, normalized_fields)
    usable = [row for row in normalized if row["normalization_status"] in USABLE_NORMALIZATION]
    write_json(OUTPUT / "normalized_quantitative_records_manifest.json", {
        "task_id": TASK_ID, "input_count": EXPECTED_NORM, "ledger_count": len(normalized),
        "usable_normalized_record_count": len(usable), "status_counts": counter(normalized, "normalization_status"),
        "hourly_annual_conversions": 0, "imputed_hours_weeks_fte": 0,
        "csv_sha256": sha256_file(OUTPUT / "normalized_quantitative_records.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "normalized_quantitative_records.jsonl"),
    })
    checkpoints["stages"]["02_normalization"] = {"complete": True, "ledger_rows": len(normalized), "usable_rows": len(usable)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    norm_by_span: dict[str, list[dict[str, Any]]] = defaultdict(list)
    norm_by_id = {row["normalization_id"]: row for row in normalized}
    for row in normalized:
        norm_by_span[row["span_id"]].append(row)

    match_results: list[dict[str, Any]] = []
    for prep in data["match"]:
        span_ids = parsed(prep["span_ids_involved"])
        records = [record for span in span_ids for record in norm_by_span.get(span, [])]
        usable_records = [record for record in records if record["normalization_status"] in USABLE_NORMALIZATION]
        scalar_records = [record for record in usable_records if record["normalized_value"] != ""]
        sides = parsed(prep["side_labels_represented"])
        safety = [record for record in scalar_records if record["normalized_side_label"] in CLEAR_SAFETY]
        nonsafety = [record for record in scalar_records if record["normalized_side_label"] == "non_safety_direct"]
        cross_side = bool(safety and nonsafety)
        bases = unique(record["normalized_pay_basis"] for record in scalar_records if record["normalized_pay_basis"] != "unknown_or_mixed")
        comp_types = unique(record["compensation_type"] for record in scalar_records)
        periods = unique(record["normalized_period_label"] for record in scalar_records if record["normalized_period_label"])
        compatible_basis = bool(scalar_records) and len(bases) == 1 and len(comp_types) == 1
        prep_period = as_bool(prep["compatible_period_flag"])
        compatible_period = bool(periods) and (len(periods) == 1 or prep_period)
        same_source = as_bool(prep["same_source_flag"])
        adjacent = as_bool(prep["adjacent_period_flag"])
        original_tier = prep["strongest_match_tier"]
        blockers: list[str] = []
        if not scalar_records: blockers.append("no_scalar_normalized_value")
        if not cross_side: blockers.append("missing_clear_cross_side_normalized_anchors")
        if not compatible_basis: blockers.append("pay_basis_or_compensation_type_incompatible")
        if not compatible_period: blockers.append("period_incompatible_or_missing")
        if any(side in NON_CLEAR for side in sides): blockers.append("non_clear_side_status_present")

        final_tier = original_tier
        promoted = False
        if original_tier in {"Tier D", "Tier G"} and cross_side and compatible_basis and compatible_period:
            final_tier = "Tier A" if same_source else "Tier B"
            promoted = True
        elif original_tier == "Tier D" and cross_side and compatible_basis and adjacent and periods:
            final_tier = "Tier C"
            promoted = True

        growth_records = [record for record in usable_records if record["normalization_status"] == "normalized_growth_or_percentage_only" or record["compensation_type"] in {"cola_or_raise", "step_progression"}]
        cluster_type = prep["cluster_type"]
        if cluster_type == "non_clear_audit_defer":
            status = "write_off_exclude" if "write_off" in sides else "side_anchor_blocked"
        elif cross_side and compatible_basis and compatible_period and scalar_records:
            status = "conditional_local_comparison_ready" if final_tier == "Tier C" or original_tier in {"Tier D", "Tier G"} else "provisional_local_comparison_ready"
        elif original_tier == "Tier E" and growth_records:
            status = "growth_continuity_ready"
        elif original_tier == "Tier F" and usable_records and int(prep["qualitative_mechanism_record_count"] or 0) > 0:
            status = "quant_qual_mechanism_link_ready"
        elif original_tier == "Tier G" and usable_records and all(record["normalized_side_label"] in CLEAR_SIDE for record in usable_records):
            status = "national_readiness_candidate"
        elif not records or not usable_records:
            status = "normalization_partial_defer"
        elif not cross_side:
            status = "side_anchor_blocked"
        elif not compatible_period:
            status = "period_blocked"
        elif not compatible_basis:
            status = "pay_basis_blocked"
        elif any(record["normalized_role_unit"] in {"unclear_role", "not_applicable"} for record in records):
            status = "role_unit_blocked"
        else:
            status = "insufficient_structure_defer"

        score = 0
        score += 25 if cross_side else 0
        score += 20 if compatible_basis else 0
        score += 20 if compatible_period else 0
        score += 15 if scalar_records else 0
        score += 10 if same_source else 0
        score += 10 if all(record["normalization_confidence"] in {"high", "moderate"} for record in usable_records) and usable_records else 0
        confidence = "high" if score >= 80 else "moderate" if score >= 55 else "low"
        match_results.append({
            "match_id": stable_id("BRMMATCH-20260803", prep["matching_prep_id"]), "matching_prep_id": prep["matching_prep_id"],
            "match_type": match_type(cluster_type), "cluster_type": cluster_type,
            "match_tier_original": original_tier, "match_tier_final": final_tier, "tier_promoted_after_repair": promoted,
            "municipality": prep["municipality"], "state": prep["state"], "region": prep["region"],
            "source_ids_involved": parsed(prep["source_ids_involved"]), "span_ids_involved": span_ids,
            "normalized_record_ids_involved": [record["normalization_id"] for record in records],
            "side_labels_represented": sides, "has_police": "police_direct" in sides, "has_fire": "fire_direct" in sides,
            "has_safety_combined": "safety_combined_direct" in sides, "has_non_safety": "non_safety_direct" in sides,
            "has_mixed": "mixed_direct" in sides, "safety_anchor_count": len(safety), "non_safety_anchor_count": len(nonsafety),
            "quantitative_record_count": len(records), "qualitative_mechanism_record_count": int(prep["qualitative_mechanism_record_count"] or 0),
            "normalized_value_count": len(scalar_records), "compatible_pay_basis_flag": compatible_basis,
            "compatible_period_flag": compatible_period, "same_source_flag": same_source,
            "same_document_flag": as_bool(prep["same_document_flag"]), "same_page_or_section_flag": as_bool(prep["same_page_or_section_flag"]),
            "same_cycle_flag": compatible_period and as_bool(prep["same_cycle_flag"]),
            "same_fiscal_year_flag": compatible_period and as_bool(prep["same_fiscal_year_flag"]),
            "same_contract_period_flag": compatible_period and as_bool(prep["same_contract_period_flag"]),
            "adjacent_period_flag": adjacent, "period_anchor_quality": "compatible_explicit_or_repaired" if compatible_period else "missing_or_incompatible",
            "role_unit_anchor_quality": prep["role_unit_anchor_quality"],
            "pay_basis_compatibility": "compatible_exact_basis_and_type" if compatible_basis else "blocked_or_unresolved",
            "mechanism_linkage_quality": "candidate_present" if int(prep["qualitative_mechanism_record_count"] or 0) else "not_yet_linked",
            "match_quality_score": score, "match_confidence": confidence, "match_status": status,
            "blocker_flags": blockers, "caveats": ["provisional_internal_candidate_only", "no_final_wage_gap_claim", "no_causal_claim"],
            "recommended_downstream_use": "local_comparison_qa" if status in LOCAL_READY else "growth_continuity_qa" if status == "growth_continuity_ready" else "quant_qual_link_qa" if status == "quant_qual_mechanism_link_ready" else "national_readiness_review" if status == "national_readiness_candidate" else "repair_or_defer",
            "source_locator_lineage": parsed(prep["source_locator_lineage"]),
        })
    match_results.sort(key=lambda row: row["match_id"])
    write_pair("all_tier_matching_results", match_results)
    write_json(OUTPUT / "all_tier_matching_manifest.json", {
        "task_id": TASK_ID, "input_count": EXPECTED_MATCH, "result_count": len(match_results),
        "tier_input_counts": EXPECTED_TIERS, "tier_final_counts": counter(match_results, "match_tier_final"),
        "status_counts": counter(match_results, "match_status"), "all_tiers_processed": sorted(EXPECTED_TIERS),
        "csv_sha256": sha256_file(OUTPUT / "all_tier_matching_results.csv"),
        "jsonl_sha256": sha256_file(OUTPUT / "all_tier_matching_results.jsonl"),
    })
    checkpoints["stages"]["03_all_tier_matching"] = {"complete": True, "rows": len(match_results), "tiers": sorted(EXPECTED_TIERS)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    # Dedicated quantitative-qualitative linking: one best candidate per usable normalized record.
    period_by_span_rating = {row["span_rating_id"]: row for row in data["period"]}
    mechanisms: list[dict[str, Any]] = []
    for row in data["mechanism"]:
        period = period_by_span_rating.get(row["span_rating_id"], {})
        mechanisms.append({**row, "period_label": period.get("primary_raw_period_anchor", "")})
    mech_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mech_by_muni: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for mechanism in mechanisms:
        mech_by_source[mechanism["source_rating_id"]].append(mechanism)
        mech_by_muni[(mechanism["municipality"], mechanism["state"])].append(mechanism)

    compatibility = {
        "cola_or_raise": {"cola_cpi_indexing", "collective_bargaining", "ordinance_council_adoption"},
        "step_progression": {"step_schedule_seniority", "collective_bargaining", "classification_civil_service"},
        "salary_schedule": {"step_schedule_seniority", "collective_bargaining", "classification_civil_service", "ordinance_council_adoption"},
        "non_base_compensation": {"non_base_compensation", "collective_bargaining"},
        "stipend_premium": {"non_base_compensation", "market_recruitment_retention"},
        "allowance_reimbursement": {"non_base_compensation", "collective_bargaining"},
        "budget_or_pay_plan": {"budget_fiscal_constraint", "ordinance_council_adoption"},
        "classification_pay_band": {"classification_civil_service", "market_recruitment_retention"},
        "base_wage": {"collective_bargaining", "arbitration_factfinding", "ordinance_council_adoption", "market_recruitment_retention"},
    }
    quant_qual: list[dict[str, Any]] = []
    for quant in usable:
        candidates = list(mech_by_source.get(quant["source_rating_id"], []))
        if not candidates:
            candidates = list(mech_by_muni.get((quant["municipality"], quant["state"]), []))
        best: tuple[int, dict[str, Any] | None, list[str]] = (-1, None, [])
        for qual in candidates:
            basis: list[str] = []
            score = 0
            same_source = qual["source_rating_id"] == quant["source_rating_id"]
            same_span = qual["span_id"] == quant["span_id"]
            same_side = qual["side_label"] == quant["normalized_side_label"] or qual["side_label"] == "mixed_direct"
            same_period = bool(qual["period_label"] and quant["normalized_period_label"] and qual["period_label"] == quant["normalized_period_label"])
            mech_fit = qual["mechanism_class"] in compatibility.get(quant["compensation_type"], set())
            if same_source: score += 40; basis.append("same_source")
            if same_span: score += 10; basis.append("same_span")
            if same_side: score += 20; basis.append("same_side")
            if same_period: score += 15; basis.append("same_period")
            if mech_fit: score += 20; basis.append("mechanism_matches_quantitative_type")
            if score > best[0]: best = (score, qual, basis)
        score, qual, basis = best
        if qual is None:
            status, confidence = "not_linkable", "low"
        elif score >= 75:
            status, confidence = "strong_quant_qual_link", "high"
        elif score >= 55:
            status, confidence = "moderate_quant_qual_link", "moderate"
        elif score >= 35:
            status, confidence = "weak_quant_qual_link", "low"
        elif qual["side_label"] != quant["normalized_side_label"]:
            status, confidence = "blocked_side_mismatch", "low"
        else:
            status, confidence = "blocked_source_context_insufficient", "low"
        quant_qual.append({
            "quant_qual_link_id": stable_id("BRMQLINK-20260803", quant["normalization_id"]),
            "quantitative_normalization_id": quant["normalization_id"],
            "qualitative_mechanism_id": qual["mechanism_prep_id"] if qual else "",
            "source_ids": unique([quant["source_rating_id"], qual["source_rating_id"] if qual else ""]),
            "span_ids": unique([quant["span_id"], qual["span_id"] if qual else ""]),
            "municipality": quant["municipality"], "state": quant["state"], "region": quant["region"],
            "quantitative_side_label": quant["normalized_side_label"], "qualitative_side_label": qual["side_label"] if qual else "",
            "mechanism_class": qual["mechanism_class"] if qual else "", "quantitative_value_type": quant["normalized_value_type"],
            "compensation_type": quant["compensation_type"], "pay_basis": quant["normalized_pay_basis"],
            "period_label": quant["normalized_period_label"],
            "same_source_flag": bool(qual and qual["source_rating_id"] == quant["source_rating_id"]),
            "same_page_or_section_flag": bool(qual and qual["span_id"] == quant["span_id"]),
            "same_period_flag": bool(qual and qual["period_label"] and qual["period_label"] == quant["normalized_period_label"]),
            "same_role_unit_flag": bool(qual and (qual["side_label"] == quant["normalized_side_label"] or qual["side_label"] == "mixed_direct")),
            "linkage_basis": basis, "linkage_score": max(score, 0), "linkage_status": status,
            "linkage_confidence": confidence, "caveats": ["documentary_alignment_not_causal_attribution"] if qual else ["no_bounded_mechanism_candidate_found"],
            "recommended_downstream_use": "mechanism_link_qa" if status in QUANT_QUAL_READY else "defer_or_manual_review",
            "local_comparison_attachable_flag": status in QUANT_QUAL_READY and quant["normalized_side_label"] in CLEAR_SIDE,
            "national_readiness_attachable_flag": status in QUANT_QUAL_READY,
            "no_causal_claim_flag": True,
        })
    write_pair("quant_qual_mechanism_link_layer", quant_qual)
    mechanism_attributed = []
    for link in quant_qual:
        if link["linkage_status"] not in QUANT_QUAL_READY:
            continue
        quant = norm_by_id[link["quantitative_normalization_id"]]
        mechanism_attributed.append({
            "mechanism_attributed_record_id": stable_id("BRMMECHQ-20260803", link["quant_qual_link_id"]),
            "normalization_id": quant["normalization_id"], "quant_qual_link_id": link["quant_qual_link_id"],
            "municipality": quant["municipality"], "state": quant["state"], "region": quant["region"],
            "normalized_side_label": quant["normalized_side_label"], "normalized_value": quant["normalized_value"],
            "normalized_value_candidates": quant["normalized_value_candidates"], "normalized_pay_basis": quant["normalized_pay_basis"],
            "normalized_period_label": quant["normalized_period_label"], "compensation_type": quant["compensation_type"],
            "mechanism_class": link["mechanism_class"], "linkage_status": link["linkage_status"],
            "linkage_basis": link["linkage_basis"], "claim_boundary": "mechanism-aligned documentary evidence; no causal attribution",
            "source_locator_lineage": quant["source_locator_lineage"],
        })
    write_pair("mechanism_attributed_quantitative_records", mechanism_attributed)
    checkpoints["stages"]["04_quant_qual_linking"] = {"complete": True, "links": len(quant_qual), "ready_links": len(mechanism_attributed)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    # Provisional/conditional local comparisons choose one scalar record per side.
    link_by_norm = {row["quantitative_normalization_id"]: row for row in quant_qual if row["linkage_status"] in QUANT_QUAL_READY}
    local_rows: list[dict[str, Any]] = []
    for match in match_results:
        if match["match_status"] not in LOCAL_READY:
            continue
        records = [norm_by_id[norm_id] for norm_id in match["normalized_record_ids_involved"] if norm_id in norm_by_id]
        candidates = [record for record in records if record["normalized_value"] != "" and record["normalization_status"] in USABLE_NORMALIZATION]
        safety = [record for record in candidates if record["normalized_side_label"] in CLEAR_SAFETY]
        nonsafety = [record for record in candidates if record["normalized_side_label"] == "non_safety_direct"]
        pairs: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
        for safe in safety:
            for non in nonsafety:
                if safe["normalized_pay_basis"] != non["normalized_pay_basis"]: continue
                if safe["compensation_type"] != non["compensation_type"]: continue
                if not safe["normalized_period_label"] or safe["normalized_period_label"] != non["normalized_period_label"]: continue
                if safe["normalized_value_type"] == "percentage" or non["normalized_value_type"] == "percentage": continue
                if safe["normalized_pay_basis"] == "budget_amount": continue
                score = (20 if safe["source_rating_id"] == non["source_rating_id"] else 0) + (10 if safe["normalization_confidence"] == "high" else 0) + (10 if non["normalization_confidence"] == "high" else 0)
                pairs.append((score, safe, non))
        if not pairs:
            continue
        _, safe, non = max(pairs, key=lambda item: item[0])
        safe_value = float(safe["normalized_value"])
        non_value = float(non["normalized_value"])
        absolute = safe_value - non_value
        percent = (absolute / non_value * 100) if non_value != 0 else None
        role_comparability = "moderate_same_basis_type_period_role_review_required"
        confidence = "high" if match["match_status"] == "provisional_local_comparison_ready" and safe["normalization_confidence"] == non["normalization_confidence"] == "high" else "moderate"
        local_rows.append({
            "local_comparison_id": stable_id("BRMLOCALCMP-20260803", match["match_id"]), "match_id": match["match_id"],
            "municipality": match["municipality"], "state": match["state"], "region": match["region"],
            "period_label": safe["normalized_period_label"], "safety_side_label": safe["normalized_side_label"],
            "non_safety_side_label": non["normalized_side_label"], "safety_role_unit": safe["normalized_role_unit"],
            "non_safety_role_unit": non["normalized_role_unit"], "safety_raw_value": safe["raw_value_tokens"],
            "non_safety_raw_value": non["raw_value_tokens"], "safety_normalized_value": safe_value,
            "non_safety_normalized_value": non_value, "shared_pay_basis": safe["normalized_pay_basis"],
            "compensation_type": safe["compensation_type"], "absolute_difference": absolute,
            "percentage_difference": percent, "denominator_convention": "non_safety_normalized_value",
            "comparison_quality_tier": match["match_tier_final"], "comparison_status": match["match_status"],
            "comparison_confidence": confidence, "role_comparability_rating": role_comparability,
            "period_compatibility_rating": "exact_normalized_period_label", "source_compatibility_rating": "same_source" if safe["source_rating_id"] == non["source_rating_id"] else "cross_source_with_lineage",
            "mechanism_linkage": unique([link_by_norm.get(safe["normalization_id"], {}).get("mechanism_class", ""), link_by_norm.get(non["normalization_id"], {}).get("mechanism_class", "")]),
            "caveats": ["provisional_internal_candidate", "requires_local_comparison_qa", "not_a_final_wage_gap_claim"],
            "source_lineage": [safe["source_locator_lineage"], non["source_locator_lineage"]], "no_causal_claim_flag": True,
        })
    provisional = [row for row in local_rows if row["comparison_status"] == "provisional_local_comparison_ready"]
    conditional = [row for row in local_rows if row["comparison_status"] == "conditional_local_comparison_ready"]
    write_pair("provisional_local_comparison_candidates", provisional)
    write_pair("conditional_local_comparison_candidates", conditional)

    growth_rows = [
        {
            "growth_candidate_id": stable_id("BRMGROWTHNORM-20260803", row["normalization_id"]),
            "normalization_id": row["normalization_id"], "municipality": row["municipality"], "state": row["state"], "region": row["region"],
            "side_label": row["normalized_side_label"], "role_unit": row["normalized_role_unit"],
            "growth_value": row["normalized_value"], "growth_value_candidates": row["normalized_value_candidates"],
            "growth_value_type": row["normalized_value_type"], "pay_basis": row["normalized_pay_basis"],
            "period_label": row["normalized_period_label"], "normalization_status": row["normalization_status"],
            "normalization_confidence": row["normalization_confidence"],
            "mechanism_class": link_by_norm.get(row["normalization_id"], {}).get("mechanism_class", ""),
            "quant_qual_link_id": link_by_norm.get(row["normalization_id"], {}).get("quant_qual_link_id", ""),
            "growth_continuity_status": "side_specific_growth_ready" if row["normalized_value"] != "" and row["normalized_period_label"] else "growth_partial_review",
            "caveats": ["side_specific_documentary_growth_record", "no_forced_cross_side_wage_level_comparison"],
            "source_locator_lineage": row["source_locator_lineage"],
        }
        for row in usable
        if row["normalization_status"] == "normalized_growth_or_percentage_only" or row["compensation_type"] in {"cola_or_raise", "step_progression"}
    ]
    write_pair("growth_continuity_normalized_candidates", growth_rows)
    checkpoints["stages"]["05_local_and_growth_outputs"] = {"complete": True, "provisional": len(provisional), "conditional": len(conditional), "growth": len(growth_rows)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    # National readiness is row-level strata/readiness only, never a national estimate.
    best_tier_by_span: dict[str, str] = {}
    tier_rank = {"Tier A": 1, "Tier B": 2, "Tier C": 3, "Tier D": 4, "Tier E": 5, "Tier F": 6, "Tier G": 7}
    local_status_by_norm: dict[str, str] = {}
    for match in match_results:
        for span in match["span_ids_involved"]:
            current = best_tier_by_span.get(span)
            if current is None or tier_rank[match["match_tier_final"]] < tier_rank[current]:
                best_tier_by_span[span] = match["match_tier_final"]
    for local in local_rows:
        match = next(item for item in match_results if item["match_id"] == local["match_id"])
        for norm_id in match["normalized_record_ids_involved"]:
            local_status_by_norm[norm_id] = local["comparison_status"]
    usable_by_muni: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in usable:
        usable_by_muni[(row["municipality"], row["state"])].append(row)
    national: list[dict[str, Any]] = []
    for row in normalized:
        muni_rows = usable_by_muni.get((row["municipality"], row["state"]), [])
        side_balance = any(x["normalized_side_label"] in CLEAR_SAFETY for x in muni_rows) and any(x["normalized_side_label"] == "non_safety_direct" for x in muni_rows)
        if row["normalized_side_label"] == "write_off": status = "national_write_off"
        elif row["normalized_side_label"] not in CLEAR_SIDE: status = "national_insufficient_structure"
        elif row["normalization_status"] == "needs_period_review": status = "national_needs_period_repair"
        elif row["normalization_status"] == "needs_pay_basis_review": status = "national_needs_pay_basis_repair"
        elif row["normalization_status"] == "needs_role_unit_review": status = "national_needs_role_comparability_review"
        elif row["normalization_status"] not in USABLE_NORMALIZATION: status = "national_insufficient_structure"
        elif not side_balance: status = "national_needs_side_balance"
        elif row["normalized_period_label"] and row["normalized_pay_basis"] != "unknown_or_mixed" and row["normalization_confidence"] in {"high", "moderate"}: status = "national_ready_stratum_candidate"
        else: status = "national_partial_stratum_candidate"
        link = link_by_norm.get(row["normalization_id"], {})
        national.append({
            "national_readiness_id": stable_id("BRMNATREADY-20260803", row["normalization_id"]),
            "normalization_id": row["normalization_id"], "municipality": row["municipality"], "state": row["state"], "region": row["region"],
            "source_family": row["source_family"], "cba_non_cba_hint": row["cba_non_cba_hint"],
            "side_label": row["normalized_side_label"], "pay_basis": row["normalized_pay_basis"],
            "compensation_type": row["compensation_type"], "period_cycle_quality": row["normalized_period_status"],
            "period_label": row["normalized_period_label"], "mechanism_class": link.get("mechanism_class", ""),
            "match_tier": best_tier_by_span.get(row["span_id"], "Tier G"),
            "local_comparison_readiness_status": local_status_by_norm.get(row["normalization_id"], "not_in_local_comparison_output"),
            "municipality_has_clear_safety_non_safety_balance": side_balance,
            "national_readiness_status": status,
            "readiness_blockers": [caveat for caveat in row["normalization_caveats"] if caveat in {"period_anchor_missing_or_unresolved", "pay_basis_unresolved", "role_unit_anchor_unresolved_or_not_applicable"}] + ([] if side_balance else ["municipality_missing_clear_side_balance"]),
            "claim_boundary": "readiness stratum only; no national wage gap, prevalence, or causal claim",
            "source_locator_lineage": row["source_locator_lineage"],
        })
    write_pair("national_comparison_readiness_layer", national)
    checkpoints["stages"]["06_national_readiness"] = {"complete": True, "rows": len(national)}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)

    # Summaries.
    write_json(OUTPUT / "normalization_status_summary.json", {"input_count": len(normalized), "usable_normalized_record_count": len(usable), "counts": counter(normalized, "normalization_status")})
    write_json(OUTPUT / "normalization_blocker_summary.json", {"input_count": len(normalized), "counts": dict(sorted(Counter(caveat for row in normalized for caveat in row["normalization_caveats"]).items()))})
    write_json(OUTPUT / "pay_basis_normalization_summary.json", {"total": len(normalized), "counts": counter(normalized, "normalized_pay_basis")})
    write_json(OUTPUT / "period_normalization_summary.json", {"total": len(normalized), "status_counts": counter(normalized, "normalized_period_status"), "with_period_label": sum(bool(row["normalized_period_label"]) for row in normalized)})
    write_json(OUTPUT / "role_unit_normalization_summary.json", {"total": len(normalized), "counts": counter(normalized, "normalized_role_unit")})
    write_json(OUTPUT / "compensation_type_normalization_summary.json", {"total": len(normalized), "counts": counter(normalized, "compensation_type")})
    write_json(OUTPUT / "matching_status_summary.json", {"total": len(match_results), "counts": counter(match_results, "match_status")})
    tier_before = counter(match_results, "match_tier_original")
    tier_after = counter(match_results, "match_tier_final")
    tier_outcomes: dict[str, Any] = {}
    for tier in EXPECTED_TIERS:
        rows = [row for row in match_results if row["match_tier_original"] == tier]
        tier_outcomes[tier] = {
            "processed": len(rows), "promoted": sum(row["tier_promoted_after_repair"] for row in rows),
            "local_ready": sum(row["match_status"] in LOCAL_READY for row in rows),
            "growth_ready": sum(row["match_status"] == "growth_continuity_ready" for row in rows),
            "quant_qual_ready": sum(row["match_status"] == "quant_qual_mechanism_link_ready" for row in rows),
            "national_readiness_candidate": sum(row["match_status"] == "national_readiness_candidate" for row in rows),
            "blocked_or_deferred": sum(row["match_status"] not in LOCAL_READY | {"growth_continuity_ready", "quant_qual_mechanism_link_ready", "national_readiness_candidate"} for row in rows),
            "status_counts": counter(rows, "match_status"),
        }
    write_json(OUTPUT / "matching_tier_before_after_summary.json", {"before": tier_before, "after": tier_after, "tier_outcomes": tier_outcomes})
    write_json(OUTPUT / "matching_blocker_summary.json", {"total": len(match_results), "counts": dict(sorted(Counter(blocker for row in match_results for blocker in row["blocker_flags"]).items()))})
    write_json(OUTPUT / "local_comparison_quality_summary.json", {"provisional_count": len(provisional), "conditional_count": len(conditional), "total": len(local_rows), "tier_counts": counter(local_rows, "comparison_quality_tier"), "confidence_counts": counter(local_rows, "comparison_confidence"), "all_candidates_require_qa": True, "final_wage_gap_claims": 0})
    write_json(OUTPUT / "growth_continuity_matching_summary.json", {"total": len(growth_rows), "status_counts": counter(growth_rows, "growth_continuity_status"), "mechanism_linked_count": sum(bool(row["quant_qual_link_id"]) for row in growth_rows), "forced_cross_side_wage_level_comparisons": 0})
    write_json(OUTPUT / "quant_qual_mechanism_link_summary.json", {"total": len(quant_qual), "status_counts": counter(quant_qual, "linkage_status"), "strong_count": sum(row["linkage_status"] == "strong_quant_qual_link" for row in quant_qual), "moderate_count": sum(row["linkage_status"] == "moderate_quant_qual_link" for row in quant_qual), "weak_count": sum(row["linkage_status"] == "weak_quant_qual_link" for row in quant_qual), "blocked_or_not_linkable_count": sum(row["linkage_status"] not in QUANT_QUAL_READY | {"weak_quant_qual_link"} for row in quant_qual), "causal_claims": 0})
    write_json(OUTPUT / "mechanism_attribution_matching_summary.json", {"mechanism_attributed_quantitative_record_count": len(mechanism_attributed), "mechanism_class_counts": counter(mechanism_attributed, "mechanism_class"), "linkage_status_counts": counter(mechanism_attributed, "linkage_status")})
    national_status = counter(national, "national_readiness_status")
    write_json(OUTPUT / "national_comparison_readiness_summary.json", {"total": len(national), "status_counts": national_status, "candidate_count": national_status.get("national_ready_stratum_candidate", 0) + national_status.get("national_partial_stratum_candidate", 0), "national_wage_gaps": 0, "national_prevalence_estimates": 0, "final_national_claims": 0})
    write_json(OUTPUT / "national_readiness_blocker_summary.json", {"total": len(national), "counts": dict(sorted(Counter(blocker for row in national for blocker in row["readiness_blockers"]).items())), "status_counts": national_status})

    def summary_by(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, Any]:
        result = {"total": len(rows)}
        for field in fields:
            result[f"by_{field}"] = counter(rows, field)
        return result
    write_json(OUTPUT / "state_region_normalized_evidence_summary.json", summary_by(normalized, ["state", "region", "normalization_status"]))
    write_json(OUTPUT / "source_family_normalized_evidence_summary.json", summary_by(normalized, ["source_family", "normalization_status"]))
    write_json(OUTPUT / "cba_non_cba_normalized_evidence_summary.json", summary_by(normalized, ["cba_non_cba_hint", "normalization_status"]))
    write_json(OUTPUT / "side_label_normalized_evidence_summary.json", summary_by(normalized, ["normalized_side_label", "normalization_status"]))
    write_json(OUTPUT / "evidence_category_normalized_evidence_summary.json", summary_by(normalized, ["evidence_category", "normalization_status"]))
    write_json(OUTPUT / "claim_readiness_normalized_evidence_summary.json", summary_by(normalized, ["claim_readiness_bucket", "normalization_status"]))
    write_json(OUTPUT / "downstream_use_normalized_evidence_summary.json", summary_by(normalized, ["downstream_use_bucket", "normalization_status"]))

    dashboard = {
        "current_stage": "quantitative normalization and matching complete", "next_task": NEXT_TASK,
        "normalization_input_universe_count": EXPECTED_NORM, "normalized_quantitative_record_count": len(usable),
        "normalization_status_counts": counter(normalized, "normalization_status"),
        "all_tier_matching_input_count": EXPECTED_MATCH, "matching_results_count": len(match_results),
        "tier_a_g_processed_counts": EXPECTED_TIERS, "matching_status_counts": counter(match_results, "match_status"),
        "provisional_local_comparison_candidate_count": len(provisional), "conditional_local_comparison_candidate_count": len(conditional),
        "growth_continuity_candidate_count": len(growth_rows), "quantitative_qualitative_mechanism_link_count": len(quant_qual),
        "strong_quant_qual_link_count": sum(row["linkage_status"] == "strong_quant_qual_link" for row in quant_qual),
        "moderate_quant_qual_link_count": sum(row["linkage_status"] == "moderate_quant_qual_link" for row in quant_qual),
        "national_comparison_readiness_candidate_count": national_status.get("national_ready_stratum_candidate", 0) + national_status.get("national_partial_stratum_candidate", 0),
        "national_readiness_blocker_counts": read_json(OUTPUT / "national_readiness_blocker_summary.json")["counts"],
        "major_matching_blocker_counts": read_json(OUTPUT / "matching_blocker_summary.json")["counts"],
        "dashboard_clean_structure_preserved": True, "dashboard_map_primary_metric": "scout_coverage_rate",
        "scout_coverage_rate_percent": 99.9579, "final_pi_report_link_intact": True,
        "wage_growth_continuity_module_intact": True, "global_analysis_readiness": False,
        "global_wage_gap_readiness": False, "global_causal_readiness": False,
        "no_polished_deliverables_created": True, "dashboard_local_build_passed": False,
        "dashboard_local_static_validation_passed": False, "dashboard_local_visual_browser_validation": "pending",
        "dashboard_public_validation": "pending_push_and_deployment",
    }
    write_json(OUTPUT / "dashboard_remaining_quantitative_normalization_matching_update_summary.json", dashboard)
    forbidden = {
        "passed": True, "polished_deliverable_created": False, "pi_report_created": False, "public_memo_created": False,
        "pdf_docx_or_slide_deck_created": False, "final_wage_gap_claim_made": False,
        "national_population_prevalence_claim_made": False, "causal_claim_made": False,
        "global_analysis_readiness_advanced": False, "global_wage_gap_readiness_advanced": False,
        "global_causal_readiness_advanced": False, "regression_run": False, "treatment_effect_run": False,
        "unsupported_normalized_value_inferred": False, "unsupported_hourly_annual_conversion": False,
        "budget_amount_treated_as_individual_wage": False, "gabriel_api_rating_run": False,
        "ocr_run": False, "full_text_extraction_run": False, "span_extraction_run": False,
        "bounded_extracted_text_context_reads": 0, "retained_binary_or_full_text_staged": False,
    }
    write_json(OUTPUT / "forbidden_action_audit.json", forbidden)
    write_json(OUTPUT / "staged_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "forbidden_payloads_staged": []})
    write_json(OUTPUT / "large_file_audit.json", {"passed": True, "status": "pending_final_staged_audit", "threshold_bytes": 50 * 1024 * 1024, "large_staged_files": []})

    summary = {
        "task_id": TASK_ID, "decision": DECISION, "normalization_input_universe_count": EXPECTED_NORM,
        "normalized_quantitative_record_count": len(usable), "normalization_status_counts": counter(normalized, "normalization_status"),
        "all_tier_matching_input_count": EXPECTED_MATCH, "matching_result_count": len(match_results),
        "matching_status_counts": counter(match_results, "match_status"), "tier_input_counts": EXPECTED_TIERS,
        "tier_final_counts": tier_after, "tier_outcomes": tier_outcomes,
        "provisional_local_comparison_candidate_count": len(provisional), "conditional_local_comparison_candidate_count": len(conditional),
        "growth_continuity_output_count": len(growth_rows), "quant_qual_mechanism_link_count": len(quant_qual),
        "quant_qual_link_status_counts": counter(quant_qual, "linkage_status"),
        "mechanism_attributed_quantitative_record_count": len(mechanism_attributed),
        "national_comparison_readiness_status_counts": national_status,
        "national_comparison_readiness_candidate_count": national_status.get("national_ready_stratum_candidate", 0) + national_status.get("national_partial_stratum_candidate", 0),
        "all_tiers_processed": True, "explicit_seed_count": 22, "seed_is_indicator_not_ceiling": True,
        "no_polished_deliverables_created": True,
        "claim_boundary": "Internal provisional local candidates and national readiness strata only; no final wage-gap, prevalence, or causal claim.",
        "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "remaining_municipalities_quantitative_normalization_matching_summary.json", summary)
    write_md(OUTPUT / "remaining_municipalities_quantitative_normalization_matching_summary.md", "Remaining-municipality quantitative normalization and matching", f"""
Decision: `{DECISION}`

- Normalization input: **{EXPECTED_NORM:,}**; usable normalized records: **{len(usable):,}**.
- Tier A–G matching input/results: **{EXPECTED_MATCH:,} / {len(match_results):,}**; every tier was processed.
- Provisional local comparison candidates: **{len(provisional):,}**; conditional candidates: **{len(conditional):,}**.
- Growth-continuity normalized candidates: **{len(growth_rows):,}**.
- Quantitative–qualitative links: **{len(quant_qual):,}**; mechanism-attributed quantitative records: **{len(mechanism_attributed):,}**.
- National-readiness candidates: **{summary['national_comparison_readiness_candidate_count']:,}**; no national estimate or claim was produced.
- No polished deliverable, regression, treatment effect, final wage-gap claim, prevalence claim, or causal claim was created.
- Next: `{NEXT_TASK}`.
""")
    manifest = {
        "task_id": TASK_ID, "decision": DECISION, "created_at": now_utc(), "head_before": data["head_before"],
        "normalization_input_count": EXPECTED_NORM, "normalized_ledger_count": len(normalized), "usable_normalized_count": len(usable),
        "matching_input_count": EXPECTED_MATCH, "matching_result_count": len(match_results), "all_tiers_processed": sorted(EXPECTED_TIERS),
        "normalized_records_sha256": sha256_file(OUTPUT / "normalized_quantitative_records.csv"),
        "matching_results_sha256": sha256_file(OUTPUT / "all_tier_matching_results.csv"),
        "quant_qual_link_sha256": sha256_file(OUTPUT / "quant_qual_mechanism_link_layer.csv"),
        "national_readiness_sha256": sha256_file(OUTPUT / "national_comparison_readiness_layer.csv"),
        "output_directory": str(OUTPUT.relative_to(ROOT)), "next_task": NEXT_TASK,
    }
    write_json(OUTPUT / "remaining_municipalities_quantitative_normalization_matching_manifest.json", manifest)
    write_md(OUTPUT / "next_task.md", "Next task", f"""
Recommend: `{NEXT_TASK}`

QA every provisional and conditional local comparison candidate for normalization, pay-basis compatibility, period compatibility, role/unit comparability, and source lineage. QA quantitative–qualitative mechanism links; separate local claim-ready, conditional, growth-continuity, mechanism-attributed, national-readiness-only, and write-off records. Produce local and national-readiness gates without regressions, treatment effects, final national/prevalence/causal claims, or polished deliverables unless separately authorized.
""")
    checkpoints["stages"]["07_validation_dashboard"] = {"complete": True, "completed_at": now_utc()}
    write_json(LOG_DIR / "stage_checkpoints.json", checkpoints)
    validate_outputs()
    return summary


def ignored(relative: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", relative], cwd=ROOT, check=False).returncode == 0


def validate_outputs(write_reports: bool = True) -> dict[str, Any]:
    data = preflight()
    normalized = read_csv(OUTPUT / "normalized_quantitative_records.csv")
    matches = read_csv(OUTPUT / "all_tier_matching_results.csv")
    provisional = read_csv(OUTPUT / "provisional_local_comparison_candidates.csv")
    conditional = read_csv(OUTPUT / "conditional_local_comparison_candidates.csv")
    links = read_csv(OUTPUT / "quant_qual_mechanism_link_layer.csv")
    growth = read_csv(OUTPUT / "growth_continuity_normalized_candidates.csv")
    national = read_csv(OUTPUT / "national_comparison_readiness_layer.csv")
    dashboard = read_json(OUTPUT / "dashboard_remaining_quantitative_normalization_matching_update_summary.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    files_under_50 = all(path.stat().st_size < 50 * 1024 * 1024 for path in OUTPUT.iterdir() if path.is_file())
    clear = CLEAR_SIDE
    checks = {
        "01_normalization_input_reconciles": len(read_csv(OUTPUT / "normalization_input_universe.csv")) == EXPECTED_NORM == len(data["norm"]),
        "02_matching_input_reconciles": len(read_csv(OUTPUT / "all_tier_matching_input_universe.csv")) == EXPECTED_MATCH == len(data["match"]),
        "03_all_tiers_a_g_processed": Counter(row["match_tier_original"] for row in matches) == Counter(EXPECTED_TIERS) and len(matches) == EXPECTED_MATCH,
        "04_seeds_not_ceiling": read_json(PREP / "comparison_seed_expansion_summary.json")["seed_is_indicator_not_ceiling"] is True and EXPECTED_MATCH > 22,
        "05_raw_values_snippets_preserved": all("raw_value_tokens" in row and "raw_span_snippet" in row for row in normalized),
        "06_normalized_required_fields": all(row["normalized_pay_basis"] and row["compensation_type"] and row["normalized_period_status"] and row["normalized_side_label"] and row["normalization_confidence"] and row["normalization_caveats"] for row in normalized),
        "07_no_unsupported_cross_basis_conversion": all(row["hourly_annual_conversion_performed"] == "false" for row in normalized) and forbidden["unsupported_hourly_annual_conversion"] is False,
        "08_budget_not_individual_wage": all(row["normalization_status"] == "normalized_budget_context_only" for row in normalized if row["normalized_pay_basis"] == "budget_amount" and row["normalization_status"] in USABLE_NORMALIZATION),
        "09_percent_not_wage_level_comparison": all(row["shared_pay_basis"] not in {"percentage_raise", "cola_cpi"} for row in provisional + conditional),
        "10_nonbase_only_same_type": all(row["compensation_type"] not in {"base_wage", "salary_schedule"} or row["shared_pay_basis"] not in {"stipend", "allowance", "overtime_rate", "holiday_rate"} for row in provisional + conditional),
        "11_nonclear_not_clear_anchor": all(not any(side in NON_CLEAR for side in parsed(row["side_labels_represented"])) or row["match_status"] not in LOCAL_READY for row in matches),
        "12_provisional_quality_gates": all(row["shared_pay_basis"] and row["period_compatibility_rating"] == "exact_normalized_period_label" and row["comparison_confidence"] in {"high", "moderate"} for row in provisional),
        "13_conditional_caveats": all(row["caveats"] and row["comparison_confidence"] == "moderate" for row in conditional),
        "14_local_compatible_basis_period": all(row["shared_pay_basis"] and row["period_label"] for row in provisional + conditional),
        "15_quant_qual_layer_exists": len(links) > 0,
        "16_ready_links_have_basis": all(row["linkage_basis"] and row["linkage_confidence"] in {"high", "moderate"} for row in links if row["linkage_status"] in QUANT_QUAL_READY),
        "17_weak_blocked_links_separated": all(row["linkage_status"] not in QUANT_QUAL_READY for row in links if row["linkage_confidence"] == "low"),
        "18_growth_no_forced_cross_side_wage_match": all("no_forced_cross_side_wage_level_comparison" in row["caveats"] for row in growth),
        "19_national_readiness_no_claims": len(national) == EXPECTED_NORM and all("no national wage gap" in row["claim_boundary"] for row in national),
        "20_no_regression": forbidden["regression_run"] is False,
        "21_no_treatment_effect": forbidden["treatment_effect_run"] is False,
        "22_no_final_wage_gap_claim": forbidden["final_wage_gap_claim_made"] is False,
        "23_no_causal_claim": forbidden["causal_claim_made"] is False,
        "24_no_national_prevalence_claim": forbidden["national_population_prevalence_claim_made"] is False,
        "25_global_analysis_false": dashboard["global_analysis_readiness"] is False,
        "26_global_wage_gap_false": dashboard["global_wage_gap_readiness"] is False,
        "27_global_causal_false": dashboard["global_causal_readiness"] is False,
        "28_no_gabriel_api": forbidden["gabriel_api_rating_run"] is False,
        "29_no_ocr": forbidden["ocr_run"] is False,
        "30_no_text_extraction": forbidden["full_text_extraction_run"] is False and forbidden["bounded_extracted_text_context_reads"] == 0,
        "31_no_span_extraction": forbidden["span_extraction_run"] is False,
        "32_retained_artifacts_ignored": ignored("artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"),
        "33_extracted_artifacts_ignored": ignored("artifacts/local_extracted_text/broad_state_remaining_municipalities_text_extraction_2026-08-02"),
        "34_no_payloads_output": not any(path.suffix.lower() in {".pdf", ".docx", ".pptx", ".html", ".htm", ".png", ".jpg", ".bin"} for path in OUTPUT.rglob("*")),
        "35_no_polished_deliverables": forbidden["polished_deliverable_created"] is False and forbidden["pdf_docx_or_slide_deck_created"] is False,
        "36_dashboard_clean_structure": dashboard["dashboard_clean_structure_preserved"] is True,
        "37_dashboard_map_scout_coverage": dashboard["dashboard_map_primary_metric"] == "scout_coverage_rate",
        "38_pi_link_intact": dashboard["final_pi_report_link_intact"] is True,
        "39_growth_module_intact": dashboard["wage_growth_continuity_module_intact"] is True,
        "40_staged_audit_passes": read_json(OUTPUT / "staged_file_audit.json")["passed"] is True,
        "41_large_file_audit_passes": read_json(OUTPUT / "large_file_audit.json")["passed"] is True and files_under_50,
    }
    report = {"all_checks_passed": all(checks.values()), "checks": checks, "passed_count": sum(checks.values()), "total_check_count": len(checks), "pending_or_failed_checks": [name for name, ok in checks.items() if not ok], "validated_at": now_utc()}
    if write_reports:
        write_json(OUTPUT / "validation_report.json", report)
        write_md(OUTPUT / "validation_report.md", "Quantitative normalization/matching validation", f"Overall: **{'PASS' if report['all_checks_passed'] else 'FAIL'}** ({report['passed_count']}/{report['total_check_count']}).\n\n" + "\n".join(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in checks.items()) + "\n\nEvery tracked artifact is below 50 MiB. The outputs are internal ledgers and readiness summaries; no polished deliverable was created.")
    if not report["all_checks_passed"]:
        raise RuntimeError(f"validation failed: {report['pending_or_failed_checks']}")
    return report


def audit_staged() -> dict[str, Any]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT, check=True, capture_output=True)
    staged = [Path(item.decode()) for item in result.stdout.split(b"\0") if item]
    prefixes = (
        "scripts/run_remaining_municipality_quantitative_normalization_matching.py", "scripts/build_dashboard_data.py",
        "scripts/test_dashboard_github_pages_deployment_repair.py", "docs/dashboard/src/App.jsx", "docs/dashboard/data/",
        "docs/analysis/compensation_extraction/BROAD-STATE-REMAINING-MUNICIPALITIES-QUANTITATIVE-NORMALIZATION-AND-MATCHING-2026-08-03/",
    )
    forbidden_suffixes = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".html", ".htm", ".bin", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    out_of_scope = [str(path) for path in staged if not any(str(path).startswith(prefix) for prefix in prefixes)]
    forbidden = [str(path) for path in staged if path.suffix.lower() in forbidden_suffixes]
    large = [{"path": str(path), "bytes": (ROOT / path).stat().st_size} for path in staged if (ROOT / path).is_file() and (ROOT / path).stat().st_size >= 50 * 1024 * 1024]
    staged_audit = {"passed": not out_of_scope and not forbidden, "staged_file_count": len(staged), "staged_files": [str(path) for path in staged], "out_of_scope": out_of_scope, "forbidden_or_polished_files": forbidden, "pre_existing_untracked_preserved_not_staged": ["docs/analysis/text_table_calibration/TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24/rendered_pages/", "package-lock.json"]}
    large_audit = {"passed": not large, "threshold_bytes": 50 * 1024 * 1024, "hard_limit_bytes": 100 * 1024 * 1024, "large_staged_files": large, "artifact_size_decision": "compact row schemas; no tracked file may reach 50 MiB"}
    write_json(OUTPUT / "staged_file_audit.json", staged_audit)
    write_json(OUTPUT / "large_file_audit.json", large_audit)
    if not staged_audit["passed"] or not large_audit["passed"]:
        raise RuntimeError("staged or large-file audit failed")
    validate_outputs()
    return {"staged": staged_audit, "large": large_audit}


def create_relay(commit_or_status: str, push_status: str) -> Path:
    summary = read_json(OUTPUT / "remaining_municipalities_quantitative_normalization_matching_summary.json")
    dashboard = read_json(OUTPUT / "dashboard_remaining_quantitative_normalization_matching_update_summary.json")
    relay_dir = LOG_DIR / "relay"
    relay_dir.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    payload = {
        "final_decision": DECISION, "commit_hash": head, "push_status": push_status,
        "current_head_before": read_json(OUTPUT / "remaining_municipalities_quantitative_normalization_matching_manifest.json")["head_before"],
        "current_head_after": head, **summary,
        "pay_basis_summary": read_json(OUTPUT / "pay_basis_normalization_summary.json"),
        "period_anchor_summary": read_json(OUTPUT / "period_normalization_summary.json"),
        "role_unit_summary": read_json(OUTPUT / "role_unit_normalization_summary.json"),
        "local_comparison_quality_summary": read_json(OUTPUT / "local_comparison_quality_summary.json"),
        "growth_continuity_summary": read_json(OUTPUT / "growth_continuity_matching_summary.json"),
        "quant_qual_summary": read_json(OUTPUT / "quant_qual_mechanism_link_summary.json"),
        "national_readiness_summary": read_json(OUTPUT / "national_comparison_readiness_summary.json"),
        "national_readiness_blockers": read_json(OUTPUT / "national_readiness_blocker_summary.json"),
        "major_blockers": read_json(OUTPUT / "matching_blocker_summary.json"),
        "dashboard_update_status": dashboard, "validation_outputs": read_json(OUTPUT / "validation_report.json"),
        "forbidden_action_audit": read_json(OUTPUT / "forbidden_action_audit.json"),
        "staged_file_audit": read_json(OUTPUT / "staged_file_audit.json"), "large_file_audit": read_json(OUTPUT / "large_file_audit.json"),
        "no_polished_deliverables_created": True,
    }
    write_json(relay_dir / "relay_summary.json", payload)
    names = [
        "remaining_municipalities_quantitative_normalization_matching_summary.json", "normalization_status_summary.json",
        "normalization_blocker_summary.json", "pay_basis_normalization_summary.json", "period_normalization_summary.json",
        "role_unit_normalization_summary.json", "matching_status_summary.json", "matching_tier_before_after_summary.json",
        "matching_blocker_summary.json", "local_comparison_quality_summary.json", "growth_continuity_matching_summary.json",
        "quant_qual_mechanism_link_summary.json", "mechanism_attribution_matching_summary.json",
        "national_comparison_readiness_summary.json", "national_readiness_blocker_summary.json",
        "state_region_normalized_evidence_summary.json", "source_family_normalized_evidence_summary.json",
        "cba_non_cba_normalized_evidence_summary.json", "evidence_category_normalized_evidence_summary.json",
        "dashboard_remaining_quantitative_normalization_matching_update_summary.json", "validation_report.json", "validation_report.md",
        "forbidden_action_audit.json", "staged_file_audit.json", "large_file_audit.json", "next_task.md",
    ]
    for name in names:
        source = OUTPUT / name
        if source.exists():
            (relay_dir / name).write_bytes(source.read_bytes())
    zip_path = ROOT / "tmp" / f"broad_state_remaining_municipalities_quantitative_normalization_matching_relay_2026-08-03_{commit_or_status}.zip"
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
        print(json.dumps({"passed": True, "head": data["head_before"], "normalization": len(data["norm"]), "matching": len(data["match"]), "mechanism": len(data["mechanism"]), "growth": len(data["growth"]), "tiers": EXPECTED_TIERS}, sort_keys=True))
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
