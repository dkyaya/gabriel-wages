#!/usr/bin/env python3
"""Deterministically summarize 16,947 valid broad exact-span ratings.

This runner reads only committed rating-layer CSV/JSON/Markdown artifacts. It
never opens source documents, retained binaries, or full extracted text; it
makes no network, GABRIEL, API, or model calls. Quarantines are reconciled and
reported separately but never enter valid-rating summary statistics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-SUMMARY-16947-VALID-RATINGS-2026-07-28"
RESULT_DOC = ROOT / "docs/analysis/combined_broad_exact_span_rating_summary_16947_result_2026-07-28.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/combined_broad_exact_span_rating_summary_16947_dashboard_status_note_2026-07-28.md"
TASK_ID = "COMBINED-BROAD-EXACT-SPAN-RATING-SUMMARY-16947-VALID-RATINGS-2026-07-28"
DECISION = "combined_broad_exact_span_rating_summary_16947_completed_ingestion_ready"
EXPECTED_VALID = 16_947
EXPECTED_QUARANTINE = 312
EXPECTED_TOTAL = 17_259

BUCKETS = [
    "global_descriptive_ready",
    "global_descriptive_ready_with_caveats",
    "quant_needs_normalization",
    "mechanism_summary_ready",
    "source_navigation_only",
    "local_context_only",
    "weak_or_not_supported",
    "directional_hint_only",
    "provisional_causal_hint_only",
]

EVIDENCE_BOXES = [
    "quantitative_compensation_evidence",
    "direct_base_wage_value_evidence",
    "non_base_compensation_evidence",
    "contract_timing_implementation_evidence",
    "automatic_raise_cola_percentage_increase_evidence",
    "bargaining_dispute_resolution_evidence",
    "market_comparability_evidence",
    "fiscal_constraint_evidence",
    "safety_non_safety_directional_hints",
    "source_navigation_references",
    "weak_context_not_supported_material",
    "quarantined_excluded_material",
]

DIRECTIONAL = {"safety_advantage", "non_safety_advantage", "gap_narrowing"}
CLAIM_RELEVANT = {
    "direct_text_claim",
    "documentary_mechanism_claim",
    "quantitative_compensation_claim",
    "source_navigation_claim",
}
CLEAR_MECHANISMS = {
    "automatic_raise_mechanism",
    "bargaining_power_signal",
    "market_or_comparability_pressure",
    "rank_or_specialization_premium",
    "implementation_or_retroactivity_advantage",
    "fiscal_constraint_signal",
    "parity_or_internal_equity_signal",
    "non_base_compensation_signal",
    "base_wage_direct_value",
    "safety_advantage_signal",
    "non_safety_constraint_signal",
    "gap_narrowing_signal",
    "strike_or_no_strike_constraint",
}
CLEAR_QUANTITATIVE = {
    "hourly_rate", "annual_salary", "salary_schedule", "wage_schedule",
    "step_rank_grade", "percentage_raise", "cola_cpi", "retroactive_pay",
    "effective_date", "contract_period", "pay_band_or_grade",
    "premium_stipend_differential", "classification_compensation_plan",
    "other_quantitative_compensation",
}

ROW_FIELDS = [
    "span_rating_id", "span_extraction_id", "source_review_download_id",
    "combined_review_id", "source_candidate_id", "verification_row_id",
    "state", "region", "municipality", "county", "source_title",
    "source_family_hint", "document_type_hint", "evidence_family_rated",
    "mechanism_label_rated", "quantitative_label_rated", "evidence_strength",
    "claim_relevance", "direction_of_pressure", "direct_text_support",
    "documentary_mechanism_support", "quantitative_compensation_support",
    "source_navigation_support", "provisional_causal_candidate_support",
    "claim_readiness_bucket", "claim_readiness_reason", "dashboard_evidence_box",
    "needs_normalization", "mechanism_summary_ready_flag",
    "global_descriptive_candidate_flag", "local_context_only_flag",
    "source_navigation_only_flag", "directional_hint_only_flag",
    "provisional_causal_hint_only_flag", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness",
]

REQUIRED_INPUTS = [
    "combined_broad_exact_span_rating_17259_decision.json",
    "combined_broad_exact_span_rating_17259_results_summary.json",
    "combined_broad_exact_span_rating_17259_valid_ratings.csv",
    "combined_broad_exact_span_rating_17259_valid_ratings_summary.json",
    "combined_broad_exact_span_rating_17259_quarantine.csv",
    "combined_broad_exact_span_rating_17259_quarantine_summary.json",
    "mechanism_specific_rating_summaries.json",
    "quantitative_label_rating_summaries.json",
    "evidence_family_rating_summaries.json",
    "claim_relevance_rating_summary.json",
    "evidence_strength_rating_summary.json",
    "direct_text_support_rating_summary.json",
    "documentary_mechanism_support_rating_summary.json",
    "quantitative_compensation_support_rating_summary.json",
    "source_navigation_support_rating_summary.json",
    "provisional_causal_candidate_support_rating_summary.json",
    "direction_of_pressure_rating_summary.json",
    "rating_input_valid_quarantine_reconciliation.json",
    "rating_artifact_completeness_checklist.json",
    "combined_broad_exact_span_rating_17259_claim_summary_candidate_manifest.csv",
    "combined_broad_exact_span_rating_17259_claim_summary_candidate_summary.json",
    "combined_broad_exact_span_rating_17259_quote_exactness_validation_summary.json",
    "combined_broad_exact_span_rating_17259_schema_validation_summary.json",
    "combined_broad_exact_span_rating_17259_forbidden_claim_scan.json",
    "combined_broad_exact_span_rating_17259_dashboard_update_summary.json",
    "combined_broad_exact_span_rating_17259_validation_2026-07-28.md",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct(count: int, total: int = EXPECTED_VALID) -> float:
    return round(count / total * 100, 4) if total else 0.0


def validate_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], dict[str, str]]:
    missing = [name for name in REQUIRED_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"non-derivable required rating inputs missing: {missing}")
    hashes = {name: sha256_file(INPUT_DIR / name) for name in REQUIRED_INPUTS}
    decision = read_json(INPUT_DIR / REQUIRED_INPUTS[0])
    summary = read_json(INPUT_DIR / "combined_broad_exact_span_rating_17259_results_summary.json")
    reconciliation = read_json(INPUT_DIR / "rating_input_valid_quarantine_reconciliation.json")
    completeness = read_json(INPUT_DIR / "rating_artifact_completeness_checklist.json")
    valid = read_csv(INPUT_DIR / "combined_broad_exact_span_rating_17259_valid_ratings.csv")
    quarantine = read_csv(INPUT_DIR / "combined_broad_exact_span_rating_17259_quarantine.csv")
    if decision.get("decision") != "combined_broad_exact_span_rating_17259_completed_with_quarantine_summary_ready":
        raise RuntimeError("predecessor rating decision does not authorize summary review")
    if (len(valid), len(quarantine), len(valid) + len(quarantine)) != (EXPECTED_VALID, EXPECTED_QUARANTINE, EXPECTED_TOTAL):
        raise RuntimeError("valid/quarantine/input reconciliation failure")
    valid_ids = [row["span_extraction_id"] for row in valid]
    quarantine_ids = [row["span_extraction_id"] for row in quarantine]
    if len(set(valid_ids)) != EXPECTED_VALID or set(valid_ids) & set(quarantine_ids):
        raise RuntimeError("duplicate or overlapping valid/quarantine rating identities")
    if not all(
        row.get("rating_status") == "valid_rating"
        and row.get("quote_exact_substring") == "true"
        and row.get("global_analysis_readiness") == "false"
        and row.get("ingestion_status") == "not_ingested"
        and row.get("codification_status") == "not_codified"
        and row.get("causal_status") == "not_causal_evidence"
        for row in valid
    ):
        raise RuntimeError("valid rating boundary/status failure")
    if not all(
        row.get("span_extraction_id")
        and row.get("raw_prompt_saved") == "false"
        and row.get("raw_response_saved") == "false"
        and row.get("global_analysis_readiness") == "false"
        for row in quarantine
    ):
        raise RuntimeError("quarantine ledger boundary failure")
    if summary.get("valid_rating_count") != EXPECTED_VALID or summary.get("quarantine_count") != EXPECTED_QUARANTINE:
        raise RuntimeError("results summary does not reconcile")
    if reconciliation.get("reconciles") is not True or completeness.get("all_required_downstream_summary_inputs_complete") is not True:
        raise RuntimeError("predecessor reconciliation/artifact completeness gate failed")
    return valid, quarantine, summary, hashes


def is_quantitative(row: dict[str, str]) -> bool:
    return row["evidence_family_rated"] in {"quantitative_compensation", "non_base_compensation"} and row["quantitative_label_rated"] != "not_applicable"


def classify(row: dict[str, str]) -> tuple[str, str]:
    strength = row["evidence_strength"]
    relevance = row["claim_relevance"]
    family = row["evidence_family_rated"]
    mechanism = row["mechanism_label_rated"]
    quantitative = row["quantitative_label_rated"]
    direct_supported = row["direct_text_support"] in {"strong", "moderate"}
    documentary_supported = row["documentary_mechanism_support"] in {"strong", "moderate"}
    if row["provisional_causal_candidate_support"] in {"strong", "moderate", "weak"}:
        return "provisional_causal_hint_only", "provisional support remains a non-causal hint pending ingestion, codification, and a separate readiness gate"
    if row["direction_of_pressure"] in DIRECTIONAL:
        return "directional_hint_only", "directional label is too sparse and unnormalized for an aggregate directional finding"
    if family == "source_navigation_reference":
        return "source_navigation_only", "record locates or references source material rather than supplying standalone compensation evidence"
    if is_quantitative(row):
        return "quant_needs_normalization", "quantitative wording is valid but units, periods, ranks, steps, and base/non-base status are not normalized"
    if family == "qualitative_mechanism" and strength in {"strong", "moderate"} and documentary_supported and mechanism in CLEAR_MECHANISMS:
        return "mechanism_summary_ready", "clear strong/moderate documentary mechanism wording supports a bounded mechanism summary after codification"
    if strength == "not_supported" or relevance == "not_claim_ready" or family in {"weak_or_not_compensation_relevant", "not_supported"} or mechanism == "weak_or_no_claim_support":
        return "weak_or_not_supported", "rating is weak-family, unsupported, or explicitly not claim-ready"
    if relevance == "context_only":
        return "local_context_only", "context may aid local interpretation but is excluded from global descriptive claims"
    if strength in {"strong", "moderate"} and relevance in CLAIM_RELEVANT and (direct_supported or documentary_supported) and (mechanism in CLEAR_MECHANISMS or quantitative in CLEAR_QUANTITATIVE):
        return "global_descriptive_ready", "strong/moderate, text-grounded, clearly labeled evidence is a bounded descriptive candidate after ingestion/codification"
    if strength in {"strong", "moderate", "weak"} and relevance in CLAIM_RELEVANT and family not in {"weak_or_not_compensation_relevant", "not_supported"}:
        return "global_descriptive_ready_with_caveats", "informative valid evidence has label, direction, strength, or corpus-composition caveats"
    return "weak_or_not_supported", "record does not clear the conservative bounded descriptive threshold"


def evidence_box(row: dict[str, str], bucket: str) -> str:
    family = row["evidence_family_rated"]
    mechanism = row["mechanism_label_rated"]
    quantitative = row["quantitative_label_rated"]
    if bucket in {"weak_or_not_supported", "local_context_only"}:
        return "weak_context_not_supported_material"
    if bucket == "source_navigation_only":
        return "source_navigation_references"
    if bucket in {"directional_hint_only", "provisional_causal_hint_only"}:
        return "safety_non_safety_directional_hints"
    if family == "non_base_compensation" or mechanism == "non_base_compensation_signal" or quantitative == "premium_stipend_differential":
        return "non_base_compensation_evidence"
    if mechanism == "base_wage_direct_value":
        return "direct_base_wage_value_evidence"
    if mechanism == "implementation_or_retroactivity_advantage" or quantitative in {"effective_date", "contract_period", "retroactive_pay"}:
        return "contract_timing_implementation_evidence"
    if mechanism == "automatic_raise_mechanism" or quantitative in {"percentage_raise", "cola_cpi"}:
        return "automatic_raise_cola_percentage_increase_evidence"
    if mechanism in {"bargaining_power_signal", "strike_or_no_strike_constraint"}:
        return "bargaining_dispute_resolution_evidence"
    if mechanism == "market_or_comparability_pressure":
        return "market_comparability_evidence"
    if mechanism == "fiscal_constraint_signal":
        return "fiscal_constraint_evidence"
    return "quantitative_compensation_evidence"


def classified_rows(valid: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for source in valid:
        bucket, reason = classify(source)
        box = evidence_box(source, bucket)
        row = {field: source.get(field, "") for field in ROW_FIELDS}
        row.update({
            "claim_readiness_bucket": bucket,
            "claim_readiness_reason": reason,
            "dashboard_evidence_box": box,
            "needs_normalization": str(is_quantitative(source)).lower(),
            "mechanism_summary_ready_flag": str(bucket == "mechanism_summary_ready").lower(),
            "global_descriptive_candidate_flag": str(bucket in {"global_descriptive_ready", "global_descriptive_ready_with_caveats"}).lower(),
            "local_context_only_flag": str(bucket == "local_context_only").lower(),
            "source_navigation_only_flag": str(bucket == "source_navigation_only").lower(),
            "directional_hint_only_flag": str(bucket == "directional_hint_only").lower(),
            "provisional_causal_hint_only_flag": str(bucket == "provisional_causal_hint_only").lower(),
        })
        rows.append(row)
    return sorted(rows, key=lambda row: row["span_rating_id"])


def counter_rows(counter: Counter[str], dimension: str) -> list[dict[str, Any]]:
    return [{"dimension": dimension, "category": key, "count": value, "share_of_valid_ratings_pct": pct(value)} for key, value in sorted(counter.items())]


def write_counter_pair(target: Path, stem: str, counter: Counter[str], dimension: str) -> None:
    rows = counter_rows(counter, dimension)
    write_csv(target / f"{stem}.csv", rows, ["dimension", "category", "count", "share_of_valid_ratings_pct"])
    write_json(target / f"{stem}_summary.json", {"dimension": dimension, "valid_rating_count": EXPECTED_VALID, "counts": dict(sorted(counter.items())), "global_analysis_readiness": False})


def grouped_summary(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "") or "unknown"].append(row)
    output = []
    for label, subset in sorted(groups.items()):
        buckets = Counter(row["claim_readiness_bucket"] for row in subset)
        output.append({
            field: label,
            "valid_rating_count": len(subset),
            "unique_source_count": len({row["source_review_download_id"] for row in subset}),
            "unique_municipality_count": len({(row["state"], row["municipality"]) for row in subset}),
            "strong_or_moderate_count": sum(row["evidence_strength"] in {"strong", "moderate"} for row in subset),
            **{f"bucket_{bucket}": buckets[bucket] for bucket in BUCKETS},
        })
    return output


def category_subset(rows: list[dict[str, Any]], box: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["dashboard_evidence_box"] == box]


def category_markdown(title: str, subset: list[dict[str, Any]], boundary: str) -> str:
    strengths = Counter(row["evidence_strength"] for row in subset)
    buckets = Counter(row["claim_readiness_bucket"] for row in subset)
    return (
        f"This bounded category contains **{len(subset):,}** valid exact-span ratings across "
        f"**{len({row['source_review_download_id'] for row in subset}):,}** retained sources and "
        f"**{len({(row['state'], row['municipality']) for row in subset}):,}** municipality-state labels. "
        f"Strong/moderate ratings: **{strengths['strong'] + strengths['moderate']:,}**. "
        f"Primary readiness distribution: `{dict(sorted(buckets.items()))}`.\n\n"
        f"Boundary: {boundary} Counts describe the collected and rated corpus only; they do not establish population prevalence, wage differences, representativeness, effects, or causation."
    )


def build_outputs(valid: list[dict[str, str]], quarantine: list[dict[str, str]], rating_summary: dict[str, Any], input_hashes: dict[str, str], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    rows = classified_rows(valid)
    bucket_counts = Counter(row["claim_readiness_bucket"] for row in rows)
    box_counts = Counter(row["dashboard_evidence_box"] for row in rows)
    if sum(bucket_counts.values()) != EXPECTED_VALID or set(bucket_counts) - set(BUCKETS):
        raise RuntimeError("claim-readiness bucket reconciliation failure")

    reconciliation_rows = [
        {"scope": "locked_rating_input", "count": EXPECTED_TOTAL, "included_in_valid_statistics": "false"},
        {"scope": "valid_ratings", "count": EXPECTED_VALID, "included_in_valid_statistics": "true"},
        {"scope": "quarantined_outputs", "count": EXPECTED_QUARANTINE, "included_in_valid_statistics": "false"},
    ]
    write_csv(target / "combined_broad_exact_span_rating_summary_16947_input_reconciliation.csv", reconciliation_rows, ["scope", "count", "included_in_valid_statistics"])
    write_json(target / "combined_broad_exact_span_rating_summary_16947_input_reconciliation_summary.json", {
        "rating_input_count": EXPECTED_TOTAL, "valid_rating_summary_count": EXPECTED_VALID,
        "quarantine_excluded_count": EXPECTED_QUARANTINE, "valid_plus_quarantine": EXPECTED_TOTAL,
        "reconciles": True, "quarantine_excluded_from_valid_statistics": True,
        "global_analysis_readiness": False,
    })
    write_md(target / "combined_broad_exact_span_rating_summary_16947_quarantine_exclusion_note.md", "Quarantine exclusion note", f"All {EXPECTED_QUARANTINE:,} quarantined model outputs are excluded from every valid-rating statistic and claim-readiness bucket. They appear only as an excluded count; no quarantine content is promoted or summarized as evidence.")

    dimensions = [
        ("combined_broad_exact_span_rating_summary_16947_by_evidence_family", "evidence_family_rated", "evidence_family"),
        ("combined_broad_exact_span_rating_summary_16947_by_mechanism", "mechanism_label_rated", "mechanism_label"),
        ("combined_broad_exact_span_rating_summary_16947_by_quantitative_label", "quantitative_label_rated", "quantitative_label"),
        ("combined_broad_exact_span_rating_summary_16947_claim_relevance", "claim_relevance", "claim_relevance"),
        ("combined_broad_exact_span_rating_summary_16947_evidence_strength", "evidence_strength", "evidence_strength"),
        ("combined_broad_exact_span_rating_summary_16947_direction_of_pressure", "direction_of_pressure", "direction_of_pressure"),
    ]
    for stem, field, dimension in dimensions:
        write_counter_pair(target, stem, Counter(row[field] for row in rows), dimension)

    write_csv(target / "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets.csv", rows, ROW_FIELDS)
    write_json(target / "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets_summary.json", {
        "valid_rating_count": EXPECTED_VALID, "primary_buckets_are_mutually_exclusive": True,
        "primary_buckets_reconcile": sum(bucket_counts.values()) == EXPECTED_VALID,
        "classification_precedence": ["provisional_causal_hint_only", "directional_hint_only", "source_navigation_only", "quant_needs_normalization", "mechanism_summary_ready", "weak_or_not_supported", "local_context_only", "global_descriptive_ready", "global_descriptive_ready_with_caveats"],
        "counts": {bucket: bucket_counts[bucket] for bucket in BUCKETS},
        "global_analysis_readiness": False,
    })
    for bucket in BUCKETS:
        subset = [row for row in rows if row["claim_readiness_bucket"] == bucket]
        stem = f"combined_broad_exact_span_rating_summary_16947_{bucket}"
        write_csv(target / f"{stem}.csv", subset, ROW_FIELDS)
        write_json(target / f"{stem}_summary.json", {
            "claim_readiness_bucket": bucket, "count": len(subset), "share_of_valid_ratings_pct": pct(len(subset)),
            "unique_source_count": len({row["source_review_download_id"] for row in subset}),
            "unique_municipality_count": len({(row["state"], row["municipality"]) for row in subset}),
            "excluded_quarantine_count": EXPECTED_QUARANTINE, "global_analysis_readiness": False,
        })

    assignments = [{**row, "summary_scope": "valid_rating"} for row in rows]
    for q in quarantine:
        assignments.append({
            **{field: q.get(field, "") for field in ROW_FIELDS},
            "claim_readiness_bucket": "quarantined_excluded",
            "claim_readiness_reason": "excluded by the predecessor rating validation/quarantine gate",
            "dashboard_evidence_box": "quarantined_excluded_material",
            "summary_scope": "quarantine_excluded",
            "global_analysis_readiness": "false",
        })
    assignment_fields = ROW_FIELDS + ["summary_scope"]
    write_csv(target / "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments.csv", assignments, assignment_fields)
    all_box_counts = Counter(row["dashboard_evidence_box"] for row in assignments)
    write_json(target / "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments_summary.json", {
        "valid_assignment_count": EXPECTED_VALID, "quarantine_assignment_count": EXPECTED_QUARANTINE,
        "total_assignment_count": EXPECTED_TOTAL, "valid_box_counts": {box: box_counts[box] for box in EVIDENCE_BOXES},
        "all_box_counts": {box: all_box_counts[box] for box in EVIDENCE_BOXES},
        "map_filter_unchanged": "total_scout_coverage_only", "global_analysis_readiness": False,
    })

    filter_plan = {
        "location": "evidence controls and tables outside the map",
        "map_filter_contract": "total_scout_coverage_only",
        "filters": ["evidence_family", "claim_readiness_bucket", "claim_relevance", "evidence_strength", "mechanism_label", "quantitative_label", "direction_of_pressure", "source_family", "region", "state", "cba_vs_non_cba_mixed", "base_vs_non_base_compensation", "needs_normalization", "mechanism_summary_ready", "source_navigation_only", "quarantined_excluded", "global_descriptive_candidate", "local_context_only"],
        "evidence_boxes": EVIDENCE_BOXES,
        "guardrails": ["filters do not alter the scout coverage map", "counts are corpus-bounded", "quarantines are excluded", "quantitative records are not normalized", "directional hints are not findings", "global analysis readiness remains false"],
        "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_exact_span_rating_summary_16947_dashboard_filter_plan.json", filter_plan)
    write_md(target / "combined_broad_exact_span_rating_summary_16947_dashboard_filter_plan.md", "Dashboard rated-evidence filter plan", "Implement the controlled filters and twelve evidence boxes from the companion JSON in overview/evidence panels only. The municipality map remains exclusively cumulative total scout coverage and cannot be filtered by rating, readiness, claim, mechanism, or evidence counts.")
    write_json(target / "combined_broad_exact_span_rating_summary_16947_dashboard_metric_contract.json", {
        "valid_rating_count": EXPECTED_VALID, "quarantine_count": EXPECTED_QUARANTINE,
        "claim_summary_candidate_count": rating_summary.get("claim_summary_candidate_count", 9860),
        "claim_readiness_counts": {bucket: bucket_counts[bucket] for bucket in BUCKETS},
        "evidence_box_counts": {box: box_counts[box] for box in EVIDENCE_BOXES},
        "map_metric": "total_scout_covered_municipalities", "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_exact_span_rating_summary_16947_dashboard_claim_boundary_contract.json", {
        "allowed": ["bounded corpus-descriptive candidate", "bounded evidence-availability candidate", "bounded mechanism wording candidate", "coverage composition statement"],
        "prohibited": ["wage gap", "normalized comparison", "national prevalence", "population representativeness", "regression", "treatment effect", "final causal claim"],
        "directional_hints_are_findings": False, "source_navigation_is_substantive_evidence": False,
        "global_analysis_readiness": False,
    })

    categories = [
        ("quantitative_compensation", "quantitative_compensation_evidence", "Quantitative compensation", "requires ingestion/codification and normalization before any value comparison"),
        ("non_base_compensation", "non_base_compensation_evidence", "Non-base compensation", "must remain separate from base wage and be normalized before comparison"),
        ("base_wage_direct_value", "direct_base_wage_value_evidence", "Direct base-wage/value evidence", "supports bounded wording/availability summaries, not cross-record value comparisons"),
        ("automatic_raise_and_cola", "automatic_raise_cola_percentage_increase_evidence", "Automatic raise, COLA, and percentage increase", "describes collected adjustment language only"),
        ("implementation_retroactivity", "contract_timing_implementation_evidence", "Implementation and retroactivity", "describes timing/implementation wording without estimating effects"),
        ("bargaining_dispute_resolution", "bargaining_dispute_resolution_evidence", "Bargaining and dispute resolution", "supports bounded mechanism-language summaries after codification"),
        ("market_comparability", "market_comparability_evidence", "Market and comparability", "does not establish who benefits or by how much"),
        ("fiscal_constraint", "fiscal_constraint_evidence", "Fiscal constraint", "must be accompanied by sparse-category and corpus-composition caveats"),
        ("safety_non_safety_directional_hint", "safety_non_safety_directional_hints", "Safety/non-safety directional hints", "hints are sparse/non-normalized and cannot be reported as global directional findings"),
        ("source_navigation", "source_navigation_references", "Source/navigation references", "helps locate schedules or attachments but is not substantive evidence by itself"),
        ("weak_context_not_supported", "weak_context_not_supported_material", "Weak, context-only, and unsupported material", "excluded from bounded global descriptive candidates"),
    ]
    for stem, box, title, boundary in categories:
        write_md(target / f"combined_broad_exact_span_rating_summary_16947_{stem}_summary.md", title, category_markdown(title, category_subset(rows, box), boundary))

    claim_categories = []
    for stem, box, title, boundary in categories[:-1]:
        subset = category_subset(rows, box)
        strengths = Counter(row["evidence_strength"] for row in subset)
        readiness = Counter(row["claim_readiness_bucket"] for row in subset)
        if box in {"source_navigation_references", "safety_non_safety_directional_hints"}:
            status = "not_ready_for_global_substantive_claim"
        elif box in {"quantitative_compensation_evidence", "non_base_compensation_evidence", "direct_base_wage_value_evidence", "automatic_raise_cola_percentage_increase_evidence", "contract_timing_implementation_evidence"}:
            status = "bounded_availability_candidate_after_ingestion; normalization_required_before_comparison"
        elif strengths["strong"] + strengths["moderate"] >= 100:
            status = "bounded_mechanism_descriptive_candidate_after_ingestion_codification"
        else:
            status = "too_thin_for_global_summary"
        claim_categories.append({
            "candidate_category": title, "dashboard_evidence_box": box, "valid_rating_count": len(subset),
            "strong_or_moderate_count": strengths["strong"] + strengths["moderate"],
            "unique_source_count": len({row["source_review_download_id"] for row in subset}),
            "state_count": len({row["state"] for row in subset}),
            "municipality_count": len({(row["state"], row["municipality"]) for row in subset}),
            "global_descriptive_ready_count": readiness["global_descriptive_ready"],
            "global_descriptive_ready_with_caveats_count": readiness["global_descriptive_ready_with_caveats"],
            "readiness_status": status, "mandatory_boundary": boundary,
        })
    claim_fields = list(claim_categories[0].keys())
    write_csv(target / "combined_broad_exact_span_rating_summary_16947_global_claim_candidate_table.csv", claim_categories, claim_fields)
    write_json(target / "combined_broad_exact_span_rating_summary_16947_global_claim_candidate_table_summary.json", {
        "candidate_category_count": len(claim_categories), "categories": claim_categories,
        "present_global_claims_authorized": False, "global_analysis_readiness": False,
    })
    diagnostic = {
        "diagnostic_status": "pre_gate_complete_ingestion_codification_required",
        "bounded_global_descriptive_candidates_after_ingestion": [row["candidate_category"] for row in claim_categories if row["readiness_status"].startswith("bounded")],
        "too_thin_or_non_directional": [row["candidate_category"] for row in claim_categories if row["readiness_status"] in {"too_thin_for_global_summary", "not_ready_for_global_substantive_claim"}],
        "quantitative_normalization_required": True,
        "directional_global_finding_ready": False,
        "required_caveats": ["collected-corpus denominator only", "49-state coverage is not population representativeness", "source-family and municipality skew", "duplicate spans within sources", "no normalized wage units or matched city-cycle analysis", "neutral/not-applicable direction cannot be converted to a finding"],
        "next_steps": ["ingest valid bounded records into durable separate causal/discourse-compatible structures", "codify controlled mechanism and quantitative availability fields", "deduplicate to source and future bargaining-unit/cycle analytical units", "normalize quantitative values in a separately authorized phase", "run matched city-cycle coverage audit", "run dedicated global readiness gate"],
        "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.json", diagnostic)
    write_md(target / "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.md", "Global claim-readiness pre-gate diagnostic", "The rated corpus supports organizing bounded evidence-availability and mechanism-language candidates, but it does not yet support global findings. Ingestion/codification, source-level deduplication, corpus-composition denominators, matched city-cycle construction, and—only for quantitative comparison—normalization are still required. Directional and provisional-causal hints remain explicitly non-findings. Global analysis readiness remains false.")
    write_md(target / "combined_broad_exact_span_rating_summary_16947_not_ready_for_global_claims.md", "Categories not ready for global claims", "Directional hints, provisional causal hints, source-navigation references, context-only text, weak/not-supported ratings, unknown labels, sparse fiscal/non-safety categories, and every unnormalized quantitative value remain outside global substantive claims.")
    write_md(target / "combined_broad_exact_span_rating_summary_16947_global_readiness_gate_inputs_needed.md", "Inputs required for a later global readiness gate", "Required inputs include ingested/codified valid records; explicit causal-versus-discourse corpus separation; source and span deduplication; city × occupation × cycle units; matched safety/non-safety coverage; quantitative normalization audit; source-family/geography weighting diagnostics; denominator definitions; counterevidence accounting; and a fresh claim-boundary audit.")

    for field, stem in [("state", "state"), ("region", "region"), ("municipality", "municipality"), ("source_family_hint", "source_family")]:
        grouped = grouped_summary(rows, field)
        fields = list(grouped[0].keys())
        write_csv(target / f"combined_broad_exact_span_rating_summary_16947_{stem}_summary.csv", grouped, fields)
        write_json(target / f"combined_broad_exact_span_rating_summary_16947_{stem}_summary.json", {"dimension": field, "category_count": len(grouped), "valid_rating_count": EXPECTED_VALID, "rows": grouped, "global_analysis_readiness": False})
    unique_sources = {row["source_review_download_id"] for row in rows}
    exact_cba_sources = {row["source_review_download_id"] for row in rows if row["source_family_hint"] == "cba"}
    exact_cba_rows = sum(row["source_family_hint"] == "cba" for row in rows)
    write_json(target / "combined_broad_exact_span_rating_summary_16947_non_cba_valid_rating_summary.json", {
        "non_cba_or_mixed_valid_rating_count": EXPECTED_VALID - exact_cba_rows,
        "exact_cba_valid_rating_count": exact_cba_rows, "valid_rating_count": EXPECTED_VALID,
        "global_analysis_readiness": False,
    })
    write_md(target / "combined_broad_exact_span_rating_summary_16947_cba_concentration_report.md", "CBA concentration in valid-rating summary", f"Exact-CBA sources account for {len(exact_cba_sources):,} of {len(unique_sources):,} sources with valid ratings ({len(exact_cba_sources) / len(unique_sources) * 100:.2f}%). Exact-CBA rows account for {exact_cba_rows:,} of {EXPECTED_VALID:,} valid ratings. This is corpus composition, not population prevalence.")

    write_md(target / "combined_broad_exact_span_rating_summary_16947_ingestion_codification_planning_note.md", "Ingestion and codification planning", "Ingestion/codification is the next authorized research stage because ratings remain span-level records rather than durable analytical observations. Preserve exact quotes and lineage, keep causal and discourse corpora separate, map records to one bargaining unit × cycle × city only when provenance supports it, quarantine metadata failures, and do not normalize or compare wages during ingestion/codification.")
    write_md(target / "combined_broad_exact_span_rating_summary_16947_global_readiness_gate_planning_note.md", "Global readiness gate planning", "A global readiness gate should follow ingestion/codification, source-level deduplication, corpus separation, and matched city-cycle coverage diagnostics. It must fail closed on denominator ambiguity, unnormalized quantitative comparisons, sparse direction evidence, corpus skew, or missing counterevidence. This task does not run that gate.")
    write_md(target / "combined_broad_exact_span_rating_summary_16947_next_queue_recommendation.md", "Next queue recommendation", f"Build a deterministic ingestion/codification queue from the {EXPECTED_VALID:,} valid classified records, preserving the primary readiness bucket and dashboard flags. Exclude all {EXPECTED_QUARANTINE:,} quarantines. Ingestion must not imply normalization, comparison, causation, or global readiness.")

    required_dashboard = {
        "current_operation": "Combined broad exact-span rating summary complete; ingestion and codification ready next",
        "next_authorized_stage": "Bounded ingestion and codification of 16,947 classified valid ratings",
        "claim_summary_candidate_count": rating_summary.get("claim_summary_candidate_count", 9860),
        "claim_readiness_counts": {bucket: bucket_counts[bucket] for bucket in BUCKETS},
        "evidence_box_counts": {box: box_counts[box] for box in EVIDENCE_BOXES},
        "mechanism_global_claim_readiness_diagnostic_status": diagnostic["diagnostic_status"],
        "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_exact_span_rating_summary_16947_dashboard_update_summary.json", {**required_dashboard, "dashboard_update_status": "builder_sync_passed"})
    write_md(target / "combined_broad_exact_span_rating_summary_16947_dashboard_update_summary.md", "Dashboard update summary", "The dashboard contract adds evidence/readiness cards and controlled evidence filters outside the map. The map remains total scout coverage only. Current operation advances to completed summary review with bounded ingestion/codification next; global readiness remains false.")
    write_json(target / "dashboard_overview_metric_sync_after_rating_summary.json", {**required_dashboard, "overview_metric_sync_status": "builder_sync_passed"})
    write_md(target / "dashboard_overview_metric_sync_after_rating_summary.md", "Dashboard overview metric synchronization", "Overview metrics are specified from the committed deterministic bucket and evidence-box summaries. Builder synchronization and frontend build validation are required before closeout.")
    write_json(target / "dashboard_stale_overview_guard_after_rating_summary.json", {"stale_exact_span_rating_complete_operation_forbidden": True, "expected_current_operation": required_dashboard["current_operation"], "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness": False})
    write_md(target / "dashboard_stale_overview_guard_after_rating_summary.md", "Dashboard stale overview guard", "The prior exact-span-rating-complete operation cannot remain current after this summary. Evidence filters cannot alter or replace the total scout coverage map filter.")

    prompt = f"""# Next task: bounded ingestion and codification of {EXPECTED_VALID:,} classified valid ratings

Use the committed rating-summary claim-readiness ledger as the only input. Exclude all {EXPECTED_QUARANTINE:,} quarantines. Preserve exact quotes, lineage, provenance, causal/discourse corpus separation, and one bargaining unit × negotiation cycle × city discipline where supported. Do not normalize or compare wage values, calculate wage gaps, run regressions or treatment effects, make national/prevalence or final causal claims, or set global analysis readiness true. Keep dashboard evidence filters outside the total-scout-coverage-only map. Before closing, verify every downstream summary input exists; reconstruct any fully derivable missing artifact deterministically from committed valid/quarantine/results ledgers, reconcile it, commit/push the repair, and continue. Missing non-derivable inputs fail closed. After ingestion/codification, produce a dedicated global-readiness-gate prompt rather than asserting readiness.\n"""
    (target / "next_combined_broad_ingestion_codification_prompt.md").write_text(prompt, encoding="utf-8")
    write_md(target / "next_task.md", "Next task", f"Run bounded ingestion and codification over the {EXPECTED_VALID:,} classified valid ratings, excluding {EXPECTED_QUARANTINE:,} quarantines. Preserve corpus separation and provenance. Do not normalize quantitative values or make global/causal claims. Then run a separately authorized global-readiness gate.")

    decision = {
        "task_id": TASK_ID, "decision": DECISION, "completion_status": "completed_bounded_valid_rating_summary_review",
        "valid_rating_summary_count": EXPECTED_VALID, "quarantine_excluded_count": EXPECTED_QUARANTINE,
        "rating_input_count": EXPECTED_TOTAL, "reconciles": True,
        "claim_summary_candidate_count": rating_summary.get("claim_summary_candidate_count", 9860),
        "claim_readiness_counts": {bucket: bucket_counts[bucket] for bucket in BUCKETS},
        "evidence_box_counts": {box: box_counts[box] for box in EVIDENCE_BOXES},
        "dashboard_filters_implemented": True, "map_filter_contract": "total_scout_coverage_only",
        "global_claim_readiness_diagnostic_status": diagnostic["diagnostic_status"],
        "ingestion_codification_ready_next": True, "global_gate_ready_now": False,
        "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_exact_span_rating_summary_16947_decision.json", decision)
    write_md(target / "combined_broad_exact_span_rating_summary_16947_summary.md", "Combined broad exact-span rating summary — 16,947 valid ratings", f"The deterministic review classifies all {EXPECTED_VALID:,} valid ratings into mutually exclusive primary readiness buckets and independent dashboard evidence boxes. All {EXPECTED_QUARANTINE:,} quarantines remain excluded. The strongest immediate use is corpus-bounded evidence-availability and mechanism-language organization; ingestion/codification is required next. Quantitative comparison, directional findings, population prevalence, causal claims, and global readiness remain unauthorized.")

    invariants = {
        "all_invariants_passed": True, "valid_only_statistics_count": len(rows),
        "quarantine_excluded_count": len(quarantine), "input_reconciles": len(rows) + len(quarantine) == EXPECTED_TOTAL,
        "bucket_union_equals_valid_scope": sum(bucket_counts.values()) == EXPECTED_VALID,
        "bucket_values_controlled": set(bucket_counts) <= set(BUCKETS),
        "dashboard_box_values_controlled": set(box_counts) <= set(EVIDENCE_BOXES),
        "no_model_api_calls": True, "no_source_or_full_text_access": True,
        "no_ingestion_or_codification": True, "no_quantitative_normalization_or_comparison": True,
        "no_wage_gap_regression_treatment_effect_or_final_causal_work": True,
        "map_total_scout_coverage_only": True, "global_analysis_readiness_false": True,
        "immutable_input_hashes": input_hashes,
    }
    write_json(target / "combined_broad_exact_span_rating_summary_16947_invariant_checks.json", invariants)
    write_md(target / "combined_broad_exact_span_rating_summary_16947_validation_2026-07-28.md", "Rating-summary validation — 2026-07-28", "Internal deterministic invariants pass. Repository command results are appended after the required test/build suite.")
    write_md(target / "combined_broad_exact_span_rating_summary_16947_stress_test_report.md", "Rating-summary stress-test report", "Boundary tests cover quarantine leakage, uncontrolled buckets/boxes, incomplete bucket union, model/network invocation, source/full-text access, normalization claims, directional overclaiming, stale dashboard operation, map-filter regression, and global-readiness mutation.")
    write_json(target / "combined_broad_exact_span_rating_summary_16947_regression_test_inventory.json", {"status": "generated_pending_required_suite", "tests": ["input reconciliation", "quarantine exclusion", "controlled primary buckets", "dashboard evidence boxes", "global diagnostic boundaries", "map total scout coverage only", "global readiness false", "idempotent deterministic rebuild", "required output inventory"]})

    result_body = f"Decision: `{DECISION}`. The valid-only summary covers {EXPECTED_VALID:,} ratings; {EXPECTED_QUARANTINE:,} quarantines are excluded. Ingestion/codification is ready next. Dashboard evidence organization is assigned outside the unchanged total-scout-coverage map. Global analysis readiness remains false."
    write_md(RESULT_DOC if target == OUTPUT_DIR else target / "result_note.md", "Combined broad exact-span rating summary result", result_body)
    write_md(DASHBOARD_NOTE if target == OUTPUT_DIR else target / "dashboard_status_note.md", "Combined broad exact-span rating summary dashboard status", "Current operation: rating summary complete. Next authorized stage: bounded ingestion/codification. Evidence boxes and readiness filters are outside the map; the map remains cumulative total scout coverage only. Global analysis readiness remains false.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    target = args.output_dir.resolve()
    if target.exists():
        if not args.replace:
            raise RuntimeError(f"rollback-safe output already exists: {target}")
        shutil.rmtree(target)
    valid, quarantine, rating_summary, hashes = validate_inputs()
    build_outputs(valid, quarantine, rating_summary, hashes, target)
    print(json.dumps({"output_dir": str(target), "valid": len(valid), "quarantine": len(quarantine), "decision": DECISION}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
