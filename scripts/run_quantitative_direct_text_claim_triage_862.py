#!/usr/bin/env python3
"""Deterministically triage 862 preserved quantitative direct-text rows.

Only committed manifest-level CSV/JSON/Markdown artifacts are read. Source URLs
are retained as inert provenance strings and are never opened. No source file,
PDF, page, retained artifact, or full extracted-text artifact is accessed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
ACCELERATOR_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-PIPELINE-HARDENING-READINESS-ACCELERATOR-2026-07-25"
CONTEXT_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-EVIDENCE-SPAN-RATING-SUMMARY-173-VALID-RATINGS-2026-07-26"
RATING_DIR = ROOT / "docs/analysis/compensation_extraction/TARGETED-EVIDENCE-SPAN-RATING-201-EXACT-SPANS-2026-07-26"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/QUANTITATIVE-DIRECT-TEXT-CLAIM-TRIAGE-862-PRESERVED-ROWS-2026-07-26"
RESULT_DOC = ROOT / "docs/analysis/quantitative_direct_text_claim_triage_862_result_2026-07-26.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/quantitative_direct_text_claim_triage_862_dashboard_status_note_2026-07-26.md"
TASK_ID = "QUANTITATIVE-DIRECT-TEXT-CLAIM-TRIAGE-862-PRESERVED-ROWS-2026-07-26"
DECISION = "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready"
EXPECTED_ROWS = 862

INPUTS = {
    PHASE_DIR / "quantitative_direct_text_claim_ready_manifest.csv": "eeb7d2f10a337d5958f9b0fc897d28eef69a9fffcfccc4f58f36ca388a4e9c8c",
    PHASE_DIR / "claim_oriented_phase_close_decision.json": "30ac4a135bf05399cccc95ccc0d9c7b763f5b41459a6703d76f5aca985e28f89",
    PHASE_DIR / "claim_oriented_evidence_category_registry_summary.json": "0683dc1991c435c48e4042a08a6a0de36282c04fe19723afb0fad0f2a7bf4363",
    PHASE_DIR / "evidence_to_claim_bridge_registry.csv": "5333d72a5a3adf33e88412a1dddcd2a34593b851746c6fa818611ec4dbd1cd79",
    PHASE_DIR / "evidence_to_claim_bridge_summary.json": "605a534d1b569597ab371f4cbf45e2559837660ab3972ad2e3df9fbf7b7cf015",
    ACCELERATOR_DIR / "accelerated_quantitative_candidate_view.csv": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_decision.json": "0d2e60f7b9267d3959cc2d3220739ab652ee63a7f5adcaa08bb48ec350c959fd",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_summary.md": "c1108dcdbb79bce2eed4f1cb9069ff9d68feb87bfd71ff915d285bc609c4134c",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_mechanism_summary.json": "a5b98914de51a1dfa8985a36721ab9a28094ab033efaed71cc8b3e26679817af",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_claims_requiring_more_data.md": "298da4be78624de565a20334cb4829498cf98c46960196b730686ce3d26bd1fa",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_quantitative_triage_considerations.md": "dd999d2dd5d96aa7f4efc8ee590a45da3e3a732a5ecd5a51ad2b579784ec0a83",
    CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_validation_2026-07-26.md": "9a92ff1fd7ca70b22e915c4c0e1191ed7868abfa5c7eca6b95ba44a7059a9dde",
    RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv": "e90d4b0e46eb303660c84b7a15b5b293cd16e5c74bda7abacecd861af03377e3",
}

VALUE_KINDS = [
    "base_wage_value", "hourly_rate_value", "annual_salary_value", "salary_schedule_value",
    "step_rank_grade_value", "percentage_raise_value", "cola_cpi_value", "effective_date_value",
    "retroactivity_implementation_value", "premium_stipend_non_base_value",
    "ambiguous_quantitative_text", "not_quantitative_claim_ready",
]
VALUE_UNITS = [
    "dollars_per_hour", "dollars_per_year", "dollars_per_period", "percentage", "date",
    "step_or_grade_label", "schedule_cell", "mixed_or_compound", "unknown_or_ambiguous",
]
READINESS = [
    "direct_text_quantitative_claim_ready", "needs_normalization_later",
    "non_base_or_premium_context", "ambiguous_or_not_claim_ready",
]
BASE_CLASSES = ["base_wage", "non_base_compensation", "mixed_base_and_non_base", "unclear"]

VALUE_FIELDS = [
    "rate_value", "salary_value", "hourly_rate", "annual_salary", "pay_band", "step", "grade",
    "percentage_increase", "effective_date", "currency_or_unit",
]
QUEUE_FIELDS = [
    "evidence_id", "row_document_id", "case_id", "source_review_id", "text_table_detection_id",
    "retained_content_hash", "source_file", "source_lane", "state", "municipality", "government_name",
    "unit_type", "controlled_occupation_class", "source_family", "source_type", "source_corpus",
    "source_cite", "retrieval_date", "retrieval_method", "artifact_pointer", "contract_period_start",
    "contract_period_end", "negotiation_cycle_id", "city_unit_negotiation_cycle_key", "matched_set_id",
    "analysis_matching_status", "identity_bridge_status", "bounded_evidence_pointer", "page_number",
    "compensation_type", "occupation_unit_classification_rank", "raw_rate_value", "raw_salary_value",
    "raw_hourly_rate", "raw_annual_salary", "raw_pay_band", "raw_step", "raw_grade",
    "raw_percentage_increase", "raw_effective_date", "raw_currency_or_unit", "raw_value_string",
    "direct_text_support_type", "claim_reason_code", "qa_status", "provenance_status",
    "claim_scope", "evidence_strength", "supported_claim_types", "claim_oriented_primary_category",
    "quantitative_direct_text_claim_eligible", "exclude_from_causal_claims", "analysis_candidate_eligible",
    "analysis_promotion_eligible", "prior_normalized_scalar_value", "prior_normalized_range_minimum",
    "prior_normalized_range_maximum", "prior_normalized_currency", "prior_normalized_frequency",
    "prior_normalized_wage_concept", "prior_annualization_status", "prior_normalized_effective_date",
]
RESULT_FIELDS = QUEUE_FIELDS + [
    "triage_id", "value_kind", "value_kind_flags", "value_unit", "value_shape", "base_vs_non_base",
    "claim_readiness", "direct_text_claim_ready", "needs_normalization_later",
    "mechanism_linkage_candidate", "mechanism_linkage_basis", "ambiguity_reason",
    "raw_value_preserved_exactly", "imputation_used", "destructive_normalization_used",
    "annualization_performed", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness", "notes",
]

OUTPUTS = [
    "quantitative_direct_text_claim_triage_862_decision.json",
    "quantitative_direct_text_claim_triage_862_summary.md",
    "quantitative_direct_text_claim_triage_862_locked_queue.csv",
    "quantitative_direct_text_claim_triage_862_locked_queue_summary.json",
    "quantitative_direct_text_claim_triage_862_lock.json",
    "quantitative_direct_text_claim_triage_862_results.csv",
    "quantitative_direct_text_claim_triage_862_results_summary.json",
    "quantitative_direct_text_claim_triage_862_direct_text_claim_ready.csv",
    "quantitative_direct_text_claim_triage_862_direct_text_claim_ready_summary.json",
    "quantitative_direct_text_claim_triage_862_needs_normalization_later.csv",
    "quantitative_direct_text_claim_triage_862_non_base_or_premium.csv",
    "quantitative_direct_text_claim_triage_862_ambiguous_or_not_claim_ready.csv",
    "quantitative_direct_text_claim_triage_862_base_wage_values.csv",
    "quantitative_direct_text_claim_triage_862_hourly_rate_values.csv",
    "quantitative_direct_text_claim_triage_862_annual_salary_values.csv",
    "quantitative_direct_text_claim_triage_862_salary_schedule_values.csv",
    "quantitative_direct_text_claim_triage_862_step_rank_grade_values.csv",
    "quantitative_direct_text_claim_triage_862_percentage_raise_values.csv",
    "quantitative_direct_text_claim_triage_862_cola_cpi_values.csv",
    "quantitative_direct_text_claim_triage_862_effective_date_values.csv",
    "quantitative_direct_text_claim_triage_862_retroactivity_implementation_values.csv",
    "quantitative_direct_text_claim_triage_862_premium_stipend_non_base_values.csv",
    "quantitative_direct_text_claim_triage_862_value_kind_summary.json",
    "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidates.csv",
    "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidate_summary.json",
    "quantitative_direct_text_claim_triage_862_linkage_to_qualitative_mechanisms_plan.md",
    "quantitative_direct_text_claim_triage_862_quantitative_claim_boundaries.md",
    "quantitative_direct_text_claim_triage_862_unit_cycle_coverage.csv",
    "quantitative_direct_text_claim_triage_862_unit_cycle_coverage_summary.json",
    "quantitative_direct_text_claim_triage_862_source_family_coverage.csv",
    "quantitative_direct_text_claim_triage_862_source_family_coverage_summary.json",
    "quantitative_direct_text_claim_triage_862_validation_2026-07-26.md",
    "quantitative_direct_text_claim_triage_862_invariant_checks.json",
    "quantitative_direct_text_claim_triage_862_stress_test_report.md",
    "quantitative_direct_text_claim_triage_862_regression_test_inventory.json",
    "next_quantitative_mechanism_linkage_prompt.md",
    "next_task.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_value_string(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for piece in raw.split("|"):
        if "=" not in piece:
            continue
        key, value = piece.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def build_queue() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    for path, expected in INPUTS.items():
        if not path.is_file():
            raise RuntimeError(f"required input missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"immutable input hash mismatch: {path.name}: {actual}")
    phase_decision = read_json(PHASE_DIR / "claim_oriented_phase_close_decision.json")
    category_summary = read_json(PHASE_DIR / "claim_oriented_evidence_category_registry_summary.json")
    context_decision = read_json(CONTEXT_DIR / "targeted_evidence_span_rating_summary_173_decision.json")
    if phase_decision.get("quantitative_direct_text_claim_ready_count") != EXPECTED_ROWS:
        raise RuntimeError("phase-close quantitative count is not 862")
    if category_summary.get("manifest_counts", {}).get("quantitative_direct_text_claim_ready_manifest.csv") != EXPECTED_ROWS:
        raise RuntimeError("registry quantitative count is not 862")
    if context_decision.get("decision") != "targeted_evidence_span_rating_summary_173_completed_quantitative_triage_recommended":
        raise RuntimeError("preceding summary does not recommend quantitative triage")
    manifest = read_csv(PHASE_DIR / "quantitative_direct_text_claim_ready_manifest.csv")
    upstream = read_csv(ACCELERATOR_DIR / "accelerated_quantitative_candidate_view.csv")
    quarantines = read_csv(RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv")
    if len(manifest) != EXPECTED_ROWS or len(upstream) != EXPECTED_ROWS:
        raise RuntimeError("quantitative triage queue count reconciliation failure")
    if len({row["evidence_id"] for row in manifest}) != EXPECTED_ROWS:
        raise RuntimeError("duplicate evidence_id in preserved lane")
    upstream_index = {row["quantitative_observation_id"]: row for row in upstream}
    if len(upstream_index) != EXPECTED_ROWS:
        raise RuntimeError("duplicate upstream quantitative observation identity")
    quarantine_ids = {row["span_extraction_id"] for row in quarantines}
    queue: list[dict[str, str]] = []
    for row in manifest:
        if row.get("claim_oriented_primary_category") != "quantitative_direct_text_claim_ready":
            raise RuntimeError("row outside preserved quantitative direct-text lane")
        if row.get("quantitative_direct_text_claim_eligible") != "true":
            raise RuntimeError("ineligible row in quantitative manifest")
        if row.get("evidence_id") in quarantine_ids or row.get("row_document_id") in quarantine_ids:
            raise RuntimeError("targeted exact-span quarantine entered quantitative queue")
        source = upstream_index.get(row.get("row_document_id", ""))
        if source is None:
            raise RuntimeError(f"required row lineage missing: {row.get('evidence_id')}")
        if source.get("current_active") != "true" or source.get("identity_bridge_status") != "complete_one_to_one":
            raise RuntimeError("inactive or non-one-to-one quantitative lineage")
        raw_value = row.get("direct_text_value_fields", "")
        if not raw_value.strip():
            raise RuntimeError("preserved raw value string missing")
        queue.append({
            "evidence_id": row["evidence_id"],
            "row_document_id": row["row_document_id"],
            "case_id": row["case_id"],
            "source_review_id": row["source_review_id"],
            "text_table_detection_id": row["text_table_detection_id"],
            "retained_content_hash": row["retained_content_hash"],
            "source_file": row["source_file"],
            "source_lane": row["source_lane"],
            "state": source["state"],
            "municipality": source["municipality"],
            "government_name": source["government_name"],
            "unit_type": source["unit_type"],
            "controlled_occupation_class": source["controlled_occupation_class"],
            "source_family": row["source_family"],
            "source_type": source["source_type_bridge"],
            "source_corpus": source["source_corpus_bridge"],
            "source_cite": row["source_cite"],
            "retrieval_date": row["retrieval_date"],
            "retrieval_method": row["retrieval_method"],
            "artifact_pointer": row["artifact_pointer"],
            "contract_period_start": source["contract_period_start_bridge"],
            "contract_period_end": source["contract_period_end_bridge"],
            "negotiation_cycle_id": source["negotiation_cycle_id"],
            "city_unit_negotiation_cycle_key": source["city_unit_negotiation_cycle_key"],
            "matched_set_id": source["matched_set_id"],
            "analysis_matching_status": source["analysis_matching_status"],
            "identity_bridge_status": source["identity_bridge_status"],
            "bounded_evidence_pointer": row["bounded_evidence_pointer"],
            "page_number": source["page_number"],
            "compensation_type": source["compensation_type"],
            "occupation_unit_classification_rank": source["occupation_unit_classification_rank"],
            "raw_rate_value": source["rate_value"],
            "raw_salary_value": source["salary_value"],
            "raw_hourly_rate": source["hourly_rate"],
            "raw_annual_salary": source["annual_salary"],
            "raw_pay_band": source["pay_band"],
            "raw_step": source["step"],
            "raw_grade": source["grade"],
            "raw_percentage_increase": source["percentage_increase"],
            "raw_effective_date": source["effective_date"],
            "raw_currency_or_unit": source["currency_or_unit"],
            "raw_value_string": raw_value,
            "direct_text_support_type": row["direct_text_support_type"],
            "claim_reason_code": row["claim_reason_code"],
            "qa_status": row["qa_status"],
            "provenance_status": row["provenance_status"],
            "claim_scope": row["claim_scope"],
            "evidence_strength": row["evidence_strength"],
            "supported_claim_types": row["supported_claim_types"],
            "claim_oriented_primary_category": row["claim_oriented_primary_category"],
            "quantitative_direct_text_claim_eligible": row["quantitative_direct_text_claim_eligible"],
            "exclude_from_causal_claims": row["exclude_from_causal_claims"],
            "analysis_candidate_eligible": source["analysis_candidate_eligible"],
            "analysis_promotion_eligible": source["analysis_promotion_eligible"],
            "prior_normalized_scalar_value": source["normalized_scalar_value"],
            "prior_normalized_range_minimum": source["normalized_range_minimum"],
            "prior_normalized_range_maximum": source["normalized_range_maximum"],
            "prior_normalized_currency": source["normalized_currency"],
            "prior_normalized_frequency": source["normalized_frequency"],
            "prior_normalized_wage_concept": source["normalized_wage_concept"],
            "prior_annualization_status": source["annualization_status"],
            "prior_normalized_effective_date": source["normalized_effective_date"],
        })
    queue.sort(key=lambda item: item["evidence_id"])
    return queue, manifest


NON_BASE_TERMS = re.compile(r"premium|stipend|incentive|overtime|longevity|assignment|bilingual|certificate|educational|holiday pay|differential|specialty pay|additional base pay")
BASE_TERMS = re.compile(r"base wage|base salary|base pay|hourly rate|annual salary|salary schedule|wage increase|salary increase|general wage|across.the.board")


def classify(row: dict[str, str]) -> dict[str, str]:
    raw = row["raw_value_string"]
    parsed = parse_value_string(raw)
    lower = " ".join([raw, row["raw_currency_or_unit"], row["compensation_type"]]).casefold()
    has_money = any(parsed.get(key) or row.get("raw_" + key, "") for key in ["rate_value", "salary_value", "hourly_rate", "annual_salary"])
    has_hour = bool(parsed.get("hourly_rate") or row["raw_hourly_rate"] or re.search(r"per\s*hour|/hr|/hour|hourly", lower))
    has_annual = bool(parsed.get("annual_salary") or row["raw_annual_salary"] or re.search(r"annual|per\s*year|/year", lower))
    has_period = bool(re.search(r"monthly|bi.?weekly|weekly|per\s*month|per\s*pay\s*period", lower))
    has_percent = bool(parsed.get("percentage_increase") or row["raw_percentage_increase"])
    has_date = bool(parsed.get("effective_date") or row["raw_effective_date"])
    has_step = bool(parsed.get("step") or parsed.get("grade") or parsed.get("pay_band") or row["raw_step"] or row["raw_grade"] or row["raw_pay_band"])
    is_cola = bool(re.search(r"\bcola\b|consumer price|\bcpi\b", lower))
    is_retro = bool(re.search(r"retroactive|retroactivity|implementation|implemented|staged|delayed", lower))
    non_base = bool(NON_BASE_TERMS.search(lower))
    explicit_base = bool(BASE_TERMS.search(lower))

    flags: list[str] = []
    if has_money and not non_base:
        flags.append("base_wage_value")
    if has_hour:
        flags.append("hourly_rate_value")
    if has_annual:
        flags.append("annual_salary_value")
    if has_money and (row["source_type"] == "wage_schedule_or_compensation_plan" or has_step):
        flags.append("salary_schedule_value")
    if has_step:
        flags.append("step_rank_grade_value")
    if has_percent:
        flags.append("percentage_raise_value")
    if is_cola:
        flags.append("cola_cpi_value")
    if has_date:
        flags.append("effective_date_value")
    if is_retro:
        flags.append("retroactivity_implementation_value")
    if non_base:
        flags.append("premium_stipend_non_base_value")
    if not flags:
        flags.append("ambiguous_quantitative_text")

    if non_base:
        primary_kind = "premium_stipend_non_base_value"
    elif is_cola:
        primary_kind = "cola_cpi_value"
    elif has_percent:
        primary_kind = "percentage_raise_value"
    elif has_hour:
        primary_kind = "hourly_rate_value"
    elif has_annual:
        primary_kind = "annual_salary_value"
    elif has_step:
        primary_kind = "step_rank_grade_value"
    elif has_money and row["source_type"] == "wage_schedule_or_compensation_plan":
        primary_kind = "salary_schedule_value"
    elif has_money:
        primary_kind = "base_wage_value"
    elif has_date:
        primary_kind = "effective_date_value"
    else:
        primary_kind = "ambiguous_quantitative_text"

    if has_percent:
        value_unit = "percentage"
    elif has_hour:
        value_unit = "dollars_per_hour"
    elif has_annual:
        value_unit = "dollars_per_year"
    elif has_period and has_money:
        value_unit = "dollars_per_period"
    elif has_money and has_step:
        value_unit = "schedule_cell"
    elif has_date and not has_money:
        value_unit = "date"
    elif has_step and not has_money:
        value_unit = "step_or_grade_label"
    elif has_money:
        value_unit = "unknown_or_ambiguous"
    else:
        value_unit = "unknown_or_ambiguous"

    scalar_keys = sum(bool(parsed.get(key) or row.get("raw_" + key, "")) for key in ["rate_value", "salary_value", "hourly_rate", "annual_salary", "percentage_increase"])
    if row["prior_normalized_range_minimum"] or row["prior_normalized_range_maximum"] or re.search(r"\bto\b|\brange\b", raw.casefold()):
        shape = "range"
    elif scalar_keys > 1:
        shape = "compound_structured_value"
    elif has_step and has_money:
        shape = "schedule_cell_with_label"
    elif has_date and scalar_keys:
        shape = "scalar_with_effective_date"
    elif scalar_keys == 1:
        shape = "single_stated_value"
    elif has_date:
        shape = "date_only"
    else:
        shape = "ambiguous_shape"

    if non_base and explicit_base:
        base_class = "mixed_base_and_non_base"
    elif non_base:
        base_class = "non_base_compensation"
    elif has_money or has_percent:
        base_class = "base_wage" if explicit_base or row["compensation_type"] in {"annual_salary", "salary", "hourly_rate", "rate", "percentage_increase"} else "unclear"
    else:
        base_class = "unclear"

    ambiguity: list[str] = []
    if row["qa_status"] == "needs_review":
        ambiguity.append("upstream_qa_needs_review")
    if value_unit == "unknown_or_ambiguous":
        ambiguity.append("unit_not_explicitly_determinable")
    if shape in {"range", "compound_structured_value", "ambiguous_shape"}:
        ambiguity.append("value_shape_requires_later_normalization")
    if not row["negotiation_cycle_id"]:
        ambiguity.append("cycle_lineage_incomplete_for_linkage")

    if row["qa_status"] == "needs_review" or primary_kind == "ambiguous_quantitative_text":
        readiness = "ambiguous_or_not_claim_ready"
    elif non_base:
        readiness = "non_base_or_premium_context"
    elif value_unit == "unknown_or_ambiguous" or shape in {"range", "compound_structured_value", "ambiguous_shape"}:
        readiness = "needs_normalization_later"
    else:
        readiness = "direct_text_quantitative_claim_ready"

    linkage_fields = ["municipality", "state", "unit_type", "source_review_id", "negotiation_cycle_id", "city_unit_negotiation_cycle_key"]
    linkage = readiness != "ambiguous_or_not_claim_ready" and all(row.get(field, "").strip() for field in linkage_fields)
    linkage_basis = "exact_city_unit_cycle_and_source_lineage_present" if linkage else "not_linkable_without_missing_or_ambiguous_lineage_repair"
    triage_id = "QDTT862-" + hashlib.sha256(row["evidence_id"].encode()).hexdigest()[:20]
    return {
        **row,
        "triage_id": triage_id,
        "value_kind": primary_kind,
        "value_kind_flags": "|".join(flags),
        "value_unit": value_unit,
        "value_shape": shape,
        "base_vs_non_base": base_class,
        "claim_readiness": readiness,
        "direct_text_claim_ready": str(readiness == "direct_text_quantitative_claim_ready").lower(),
        "needs_normalization_later": str(readiness == "needs_normalization_later").lower(),
        "mechanism_linkage_candidate": str(linkage).lower(),
        "mechanism_linkage_basis": linkage_basis,
        "ambiguity_reason": "|".join(ambiguity),
        "raw_value_preserved_exactly": "true",
        "imputation_used": "false",
        "destructive_normalization_used": "false",
        "annualization_performed": "false",
        "rating_status": "not_rated",
        "ingestion_status": "not_ingested",
        "codification_status": "not_codified",
        "causal_status": "not_causal_evidence",
        "global_analysis_readiness": "false",
        "notes": "deterministic manifest-only triage; direct text is not comparative or causal evidence",
    }


def aggregate_rows(results: list[dict[str, str]]) -> dict[str, Any]:
    readiness = Counter(row["claim_readiness"] for row in results)
    value_kind = Counter(row["value_kind"] for row in results)
    units = Counter(row["value_unit"] for row in results)
    shapes = Counter(row["value_shape"] for row in results)
    base = Counter(row["base_vs_non_base"] for row in results)
    flags = Counter(flag for row in results for flag in row["value_kind_flags"].split("|") if flag)
    linkage = sum(row["mechanism_linkage_candidate"] == "true" for row in results)
    return {
        "input_rows": len(results),
        "claim_readiness_counts": {category: readiness[category] for category in READINESS},
        "value_kind_counts": {category: value_kind[category] for category in VALUE_KINDS},
        "value_kind_flag_counts": {category: flags[category] for category in VALUE_KINDS},
        "value_unit_counts": {category: units[category] for category in VALUE_UNITS},
        "value_shape_counts": dict(sorted(shapes.items())),
        "base_vs_non_base_counts": {category: base[category] for category in BASE_CLASSES},
        "mechanism_linkage_candidate_count": linkage,
        "rows_with_complete_cycle_lineage": sum(bool(row["negotiation_cycle_id"]) for row in results),
        "rows_with_incomplete_cycle_lineage": sum(not bool(row["negotiation_cycle_id"]) for row in results),
    }


def write_coverage(target: Path, results: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    unit_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        key = (row["state"], row["municipality"], row["unit_type"], row["negotiation_cycle_id"] or "missing_cycle")
        unit_groups[key].append(row)
    unit_rows = []
    for key, rows in sorted(unit_groups.items()):
        unit_rows.append({
            "state": key[0], "municipality": key[1], "unit_type": key[2], "negotiation_cycle_id": key[3],
            "row_count": len(rows),
            "direct_text_claim_ready_count": sum(row["direct_text_claim_ready"] == "true" for row in rows),
            "mechanism_linkage_candidate_count": sum(row["mechanism_linkage_candidate"] == "true" for row in rows),
            "source_family_count": len({row["source_family"] for row in rows}),
        })
    write_csv(target / "quantitative_direct_text_claim_triage_862_unit_cycle_coverage.csv", unit_rows, list(unit_rows[0].keys()))
    unit_summary = {
        "unit_cycle_groups": len(unit_rows),
        "groups_with_complete_cycle": sum(row["negotiation_cycle_id"] != "missing_cycle" for row in unit_rows),
        "groups_with_missing_cycle": sum(row["negotiation_cycle_id"] == "missing_cycle" for row in unit_rows),
        "distinct_city_state_pairs": len({(row["state"], row["municipality"]) for row in unit_rows}),
        "distinct_unit_types": len({row["unit_type"] for row in unit_rows}),
        "boundary": "coverage counts describe the preserved 862-row lane only",
    }
    write_json(target / "quantitative_direct_text_claim_triage_862_unit_cycle_coverage_summary.json", unit_summary)

    source_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        source_groups[(row["source_family"], row["source_type"])].append(row)
    source_rows = []
    for key, rows in sorted(source_groups.items()):
        source_rows.append({
            "source_family": key[0], "source_type": key[1], "row_count": len(rows),
            "direct_text_claim_ready_count": sum(row["direct_text_claim_ready"] == "true" for row in rows),
            "needs_normalization_count": sum(row["needs_normalization_later"] == "true" for row in rows),
            "mechanism_linkage_candidate_count": sum(row["mechanism_linkage_candidate"] == "true" for row in rows),
            "distinct_city_state_pairs": len({(row["state"], row["municipality"]) for row in rows}),
        })
    write_csv(target / "quantitative_direct_text_claim_triage_862_source_family_coverage.csv", source_rows, list(source_rows[0].keys()))
    source_summary = {
        "source_family_type_groups": len(source_rows),
        "source_family_counts": dict(sorted(Counter(row["source_family"] for row in results).items())),
        "source_type_counts": dict(sorted(Counter(row["source_type"] for row in results).items())),
        "source_corpus_counts": dict(sorted(Counter(row["source_corpus"] for row in results).items())),
    }
    write_json(target / "quantitative_direct_text_claim_triage_862_source_family_coverage_summary.json", source_summary)
    return unit_summary, source_summary


def build_outputs(queue: list[dict[str, str]], manifest: list[dict[str, str]], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    queue_path = target / "quantitative_direct_text_claim_triage_862_locked_queue.csv"
    write_csv(queue_path, queue, QUEUE_FIELDS)
    queue_hash = sha256_file(queue_path)
    ids_hash = hashlib.sha256("\n".join(row["evidence_id"] for row in queue).encode()).hexdigest()
    write_json(target / "quantitative_direct_text_claim_triage_862_lock.json", {
        "task_id": TASK_ID,
        "queue_count": EXPECTED_ROWS,
        "queue_sha256": queue_hash,
        "evidence_ids_sha256": ids_hash,
        "input_hashes": {str(path.relative_to(ROOT)): digest for path, digest in INPUTS.items()},
    })
    write_json(target / "quantitative_direct_text_claim_triage_862_locked_queue_summary.json", {
        "queue_count": EXPECTED_ROWS,
        "unique_evidence_ids": len({row["evidence_id"] for row in queue}),
        "joined_lineage_rows": len(queue),
        "rows_outside_preserved_lane": 0,
        "targeted_span_quarantines_in_queue": 0,
        "queue_sha256": queue_hash,
    })
    results = [classify(row) for row in queue]
    for source, result in zip(queue, results):
        if source["raw_value_string"] != result["raw_value_string"]:
            raise RuntimeError("raw value overwritten")
    write_csv(target / "quantitative_direct_text_claim_triage_862_results.csv", results, RESULT_FIELDS)
    summary = aggregate_rows(results)
    write_json(target / "quantitative_direct_text_claim_triage_862_results_summary.json", summary)

    output_map = {
        "quantitative_direct_text_claim_triage_862_direct_text_claim_ready.csv": [row for row in results if row["claim_readiness"] == "direct_text_quantitative_claim_ready"],
        "quantitative_direct_text_claim_triage_862_needs_normalization_later.csv": [row for row in results if row["claim_readiness"] == "needs_normalization_later"],
        "quantitative_direct_text_claim_triage_862_non_base_or_premium.csv": [row for row in results if row["claim_readiness"] == "non_base_or_premium_context"],
        "quantitative_direct_text_claim_triage_862_ambiguous_or_not_claim_ready.csv": [row for row in results if row["claim_readiness"] == "ambiguous_or_not_claim_ready"],
    }
    for name, rows in output_map.items():
        write_csv(target / name, rows, RESULT_FIELDS)
    write_json(target / "quantitative_direct_text_claim_triage_862_direct_text_claim_ready_summary.json", {
        "direct_text_quantitative_claim_ready_count": len(output_map["quantitative_direct_text_claim_triage_862_direct_text_claim_ready.csv"]),
        "boundary": "directly stated values only; not normalized, comparative, population, or causal claims",
    })

    flag_files = {
        "base_wage_value": "quantitative_direct_text_claim_triage_862_base_wage_values.csv",
        "hourly_rate_value": "quantitative_direct_text_claim_triage_862_hourly_rate_values.csv",
        "annual_salary_value": "quantitative_direct_text_claim_triage_862_annual_salary_values.csv",
        "salary_schedule_value": "quantitative_direct_text_claim_triage_862_salary_schedule_values.csv",
        "step_rank_grade_value": "quantitative_direct_text_claim_triage_862_step_rank_grade_values.csv",
        "percentage_raise_value": "quantitative_direct_text_claim_triage_862_percentage_raise_values.csv",
        "cola_cpi_value": "quantitative_direct_text_claim_triage_862_cola_cpi_values.csv",
        "effective_date_value": "quantitative_direct_text_claim_triage_862_effective_date_values.csv",
        "retroactivity_implementation_value": "quantitative_direct_text_claim_triage_862_retroactivity_implementation_values.csv",
        "premium_stipend_non_base_value": "quantitative_direct_text_claim_triage_862_premium_stipend_non_base_values.csv",
    }
    for flag, name in flag_files.items():
        write_csv(target / name, [row for row in results if flag in row["value_kind_flags"].split("|")], RESULT_FIELDS)
    write_json(target / "quantitative_direct_text_claim_triage_862_value_kind_summary.json", {
        "primary_value_kind_counts": summary["value_kind_counts"],
        "overlapping_value_kind_flag_counts": summary["value_kind_flag_counts"],
        "value_unit_counts": summary["value_unit_counts"],
        "value_shape_counts": summary["value_shape_counts"],
        "base_vs_non_base_counts": summary["base_vs_non_base_counts"],
    })

    linkage = [row for row in results if row["mechanism_linkage_candidate"] == "true"]
    write_csv(target / "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidates.csv", linkage, RESULT_FIELDS)
    linkage_summary = {
        "mechanism_linkage_candidate_count": len(linkage),
        "candidate_count_by_unit_type": dict(sorted(Counter(row["unit_type"] for row in linkage).items())),
        "candidate_count_by_source_family": dict(sorted(Counter(row["source_family"] for row in linkage).items())),
        "candidate_count_by_claim_readiness": dict(sorted(Counter(row["claim_readiness"] for row in linkage).items())),
        "exact_linkage_performed": 0,
        "boundary": "candidate status only; a separately authorized linkage stage is required",
    }
    write_json(target / "quantitative_direct_text_claim_triage_862_mechanism_linkage_candidate_summary.json", linkage_summary)
    unit_summary, source_summary = write_coverage(target, results)

    (target / "quantitative_direct_text_claim_triage_862_linkage_to_qualitative_mechanisms_plan.md").write_text(
        "# Later linkage to qualitative mechanisms\n\n"
        f"This triage identifies {len(linkage)} quantitative rows with complete city, unit, cycle, and source lineage as later mechanism-linkage candidates. No substantive linkage is made here. A separately authorized stage should join only exact same-source or exact city-unit-cycle keys to bounded qualitative ratings, preserve unmatched rows, and report linkage quality before any comparison. It must not calculate a wage gap, normalize missing units, infer direction, or treat co-location as causation.\n",
        encoding="utf-8",
    )
    (target / "quantitative_direct_text_claim_triage_862_quantitative_claim_boundaries.md").write_text(
        "# Quantitative claim boundaries\n\n"
        "A claim-ready row may support only a statement that its preserved text directly reports the recorded wage, rate, raise, premium, schedule, step, grade, or effective-date value. Prior normalized helper fields are retained as lineage but are not generated, modified, or promoted here. This task performs no imputation, destructive normalization, annualization, comparison, wage-gap calculation, regression, treatment-effect estimate, population-prevalence inference, national generalization, or causal analysis.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID,
        "decision": DECISION,
        "completion_status": "completed_bounded_quantitative_direct_text_triage",
        **summary,
        "mechanism_linkage_ready_next": True,
        "normalization_recommended_next": False,
        "repair_needed": False,
        "tier_c_verification_recommended_next": False,
        "repo_cleanup_recommended_next": False,
        "exact_mechanism_linkages_created": 0,
        "gabriel_api_model_calls": 0,
        "url_opens": 0,
        "downloads": 0,
        "pdf_page_accesses": 0,
        "retained_file_accesses": 0,
        "full_extracted_text_accesses": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "wage_gap_calculations": 0,
        "regressions": 0,
        "treatment_effect_estimates": 0,
        "population_prevalence_claims": 0,
        "national_claims": 0,
        "final_causal_claims": 0,
        "imputed_values": 0,
        "destructively_normalized_values": 0,
        "annualized_values": 0,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    }
    write_json(target / "quantitative_direct_text_claim_triage_862_decision.json", decision)
    (target / "quantitative_direct_text_claim_triage_862_summary.md").write_text(
        "# Quantitative direct-text claim triage — 862 preserved rows\n\n"
        f"Decision: `{DECISION}`. Exactly 862 preserved quantitative direct-text rows were deterministically classified with raw value strings unchanged. Direct-text quantitative claim-ready: {summary['claim_readiness_counts']['direct_text_quantitative_claim_ready']}; needs normalization later: {summary['claim_readiness_counts']['needs_normalization_later']}; non-base/premium context: {summary['claim_readiness_counts']['non_base_or_premium_context']}; ambiguous/not ready: {summary['claim_readiness_counts']['ambiguous_or_not_claim_ready']}. Later mechanism-linkage candidates with complete city-unit-cycle-source lineage: {len(linkage)}. No linkage, comparison, normalization, imputation, wage-gap, regression, treatment-effect, population, national, or causal analysis was performed. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )

    invariants = {
        "all_invariants_passed": True,
        "exactly_862_preserved_quantitative_rows_triaged": True,
        "rows_outside_preserved_lane_excluded": True,
        "targeted_span_quarantines_excluded": True,
        "raw_values_preserved_exactly": True,
        "no_imputation_destructive_normalization_or_annualization": True,
        "no_gabriel_api_model_calls": True,
        "no_url_pdf_page_retained_file_or_full_text_access": True,
        "no_download_ocr_or_rendering": True,
        "no_ingestion_or_codification": True,
        "no_wage_gap_regression_treatment_effect_population_national_or_final_causal_work": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(target / "quantitative_direct_text_claim_triage_862_invariant_checks.json", invariants)
    write_json(target / "quantitative_direct_text_claim_triage_862_regression_test_inventory.json", {
        "suite": "scripts/test_quantitative_direct_text_claim_triage_862.py",
        "required_cases": [
            "exact 862-row scope", "one-to-one lineage join", "pinned hashes", "raw value identity",
            "controlled value classifications", "exclusive readiness reconciliation", "quarantine exclusion",
            "no forbidden dependencies", "closed downstream statuses", "dashboard global closure",
            "future prompt boundaries", "idempotent resume", "partial-package failure",
        ],
    })
    (target / "quantitative_direct_text_claim_triage_862_stress_test_report.md").write_text(
        "# Stress-test report\n\n"
        "- Missing, duplicate, inactive, non-lane, non-one-to-one, or hash-drifted rows fail before outputs.\n"
        "- Raw value strings are copied byte-for-byte at the field level and checked after triage.\n"
        "- Missing units and compound/range values route to later normalization; upstream QA needs-review rows remain ambiguous.\n"
        "- Missing cycles prevent mechanism-linkage candidacy and are never imputed.\n"
        "- The runner has no network, PDF, retained-file, full-text, OCR, rendering, model, ingestion, or codification dependency.\n"
        "- Partial outputs fail closed; a complete package resumes with zero writes.\n",
        encoding="utf-8",
    )
    (target / "quantitative_direct_text_claim_triage_862_validation_2026-07-26.md").write_text(
        "# Quantitative direct-text claim triage validation — 2026-07-26\n\nInternal deterministic gates passed for exactly 862 preserved rows. Required repository command results are appended after the full suite completes.\n",
        encoding="utf-8",
    )

    future = (
        "# Next task: bounded quantitative-to-qualitative mechanism linkage\n\n"
        f"Use only the {len(linkage)} triage rows marked `mechanism_linkage_candidate = true` and the already bounded qualitative mechanism summaries/valid ratings under separate authorization. Lock both sides, link only exact same-source or exact city-unit-cycle keys, preserve unmatched rows, and report linkage quality without estimating an effect.\n\n"
        "Do not fetch, search, open URLs, download, access PDFs/pages/retained files/full extracted text, OCR, render, call a model unless separately authorized, impute or destructively normalize values, annualize values, ingest, codify, calculate a wage gap, run a regression, estimate a treatment effect, make a population or national claim, make a final causal claim, use targeted quarantines, or set global analysis readiness true. Co-location is not causation.\n"
    )
    (target / "next_quantitative_mechanism_linkage_prompt.md").write_text(future, encoding="utf-8")
    (target / "next_task.md").write_text(future, encoding="utf-8")


def validate_complete(path: Path) -> None:
    missing = [name for name in OUTPUTS if not (path / name).is_file()]
    if missing:
        raise RuntimeError(f"partial output package: missing {missing}")
    decision = read_json(path / "quantitative_direct_text_claim_triage_862_decision.json")
    queue = read_csv(path / "quantitative_direct_text_claim_triage_862_locked_queue.csv")
    results = read_csv(path / "quantitative_direct_text_claim_triage_862_results.csv")
    lock = read_json(path / "quantitative_direct_text_claim_triage_862_lock.json")
    if decision.get("decision") != DECISION or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("completed decision invalid")
    if len(queue) != EXPECTED_ROWS or len(results) != EXPECTED_ROWS:
        raise RuntimeError("completed count mismatch")
    if sha256_file(path / "quantitative_direct_text_claim_triage_862_locked_queue.csv") != lock.get("queue_sha256"):
        raise RuntimeError("completed queue lock mismatch")
    queue_raw = {row["evidence_id"]: row["raw_value_string"] for row in queue}
    if any(queue_raw.get(row["evidence_id"]) != row["raw_value_string"] for row in results):
        raise RuntimeError("completed raw value mismatch")
    if sum(decision.get("claim_readiness_counts", {}).values()) != EXPECTED_ROWS:
        raise RuntimeError("completed readiness reconciliation failure")


def install_dashboard_docs(decision: dict[str, Any]) -> None:
    counts = decision["claim_readiness_counts"]
    RESULT_DOC.write_text(
        "# Quantitative direct-text claim triage result — 2026-07-26\n\n"
        f"Decision: `{DECISION}`. Exactly 862 preserved rows were triaged. Direct-text claim-ready: {counts['direct_text_quantitative_claim_ready']}; needs normalization later: {counts['needs_normalization_later']}; non-base/premium context: {counts['non_base_or_premium_context']}; ambiguous/not ready: {counts['ambiguous_or_not_claim_ready']}. Mechanism-linkage candidates: {decision['mechanism_linkage_candidate_count']}. No model or source-material access occurred; no comparative or causal analysis was performed; global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    DASHBOARD_NOTE.write_text(
        "# Dashboard status note — quantitative direct-text triage\n\n"
        f"Status: `{DECISION}`. Queue: 862. Direct-text claim-ready: {counts['direct_text_quantitative_claim_ready']}. Mechanism-linkage candidates: {decision['mechanism_linkage_candidate_count']}. Mechanism linkage ready next: true. Normalization recommended as immediate next phase: false. Global analysis readiness: false.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    queue, manifest = build_queue()
    if OUTPUT_DIR.exists():
        validate_complete(OUTPUT_DIR)
        if args.resume:
            print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_ROWS}))
            return 0
        raise RuntimeError(f"output directory already exists: {OUTPUT_DIR}")
    staging = OUTPUT_DIR.with_name(OUTPUT_DIR.name + ".staging")
    if staging.exists():
        raise RuntimeError(f"staging directory already exists: {staging}")
    try:
        build_outputs(queue, manifest, staging)
        validate_complete(staging)
        staging.rename(OUTPUT_DIR)
        decision = read_json(OUTPUT_DIR / "quantitative_direct_text_claim_triage_862_decision.json")
        install_dashboard_docs(decision)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(json.dumps({"status": "completed", "decision": DECISION, "rows": EXPECTED_ROWS}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
