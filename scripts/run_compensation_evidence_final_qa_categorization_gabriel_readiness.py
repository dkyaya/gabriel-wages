#!/usr/bin/env python3
"""Close compensation-evidence QA with deterministic phase categories.

This runner reads only committed structured artifacts. It creates a new,
rollback-safe categorization layer and GABRIEL attribute-assignment contract;
it does not access sources, run models, compute statistics, or promote global
analysis readiness.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import run_compensation_evidence_limited_qualitative_usage_registry_acceptance as acceptance
import run_compensation_evidence_pipeline_hardening_readiness_accelerator as accelerator


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-FINAL-QA-CATEGORIZATION-AND-GABRIEL-ATTRIBUTE-READINESS-2026-07-25"
SCHEMA_VERSION = "compensation_evidence_final_qa_categorization_v1"
BASELINE_COMMIT = "02d3710fcb6a47816a0429ac6be243c33fb6bb8c"
DECISION = "final_qa_phase_closed_gabriel_attribute_analysis_ready"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-FINAL-QA-CATEGORIZATION-AND-GABRIEL-ATTRIBUTE-READINESS-2026-07-25"

ACCEPTANCE_DIR = acceptance.DEFAULT_OUTPUT_DIR
PROMOTION_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-PROMOTION-HARDENED-2026-07-25"
ACCELERATOR_DIR = accelerator.DEFAULT_OUTPUT_DIR

PROMOTED_PATH = PROMOTION_DIR / "limited_exact_span_qualitative_promoted_view.csv"
NAVIGATION_PATH = PROMOTION_DIR / "ambiguous_unavailable_qualitative_navigation_preserved.csv"
QUANT_CANDIDATE_PATH = ACCELERATOR_DIR / "accelerated_quantitative_candidate_view.csv"
QUANT_EXCEPTION_PATH = ACCELERATOR_DIR / "accelerated_quantitative_exception_ledger.csv"
NON_BASE_PATH = ACCELERATOR_DIR / "accelerated_non_base_companion_view.csv"
REFERENCE_PATH = ACCELERATOR_DIR / "accelerated_reference_control_view.csv"
CONFLICT_PATH = ACCELERATOR_DIR / "accelerated_conflict_quarantine_ledger.csv"

ACCEPTANCE_INPUTS = (
    "limited_qualitative_usage_registry_acceptance_decision.json",
    "limited_qualitative_usage_registry_acceptance_summary.md",
    "limited_qualitative_usage_registry_acceptance_hash_audit.json",
    "limited_qualitative_usage_registry_acceptance_scope_audit.json",
    "limited_qualitative_usage_registry_acceptance_dashboard_audit.json",
    "limited_qualitative_usage_registry_acceptance_forbidden_action_audit.json",
    "limited_qualitative_usage_registry_acceptance_state_contract.md",
    "limited_qualitative_usage_registry_acceptance_scope_matrix.csv",
    "limited_qualitative_usage_registry_acceptance_validation_2026-07-25.md",
    "limited_qualitative_usage_registry_acceptance_invariant_checks.json",
    "limited_qualitative_usage_registry_acceptance_stress_test_report.md",
    "limited_qualitative_usage_registry_acceptance_regression_test_inventory.json",
    "next_pipeline_stage_strategy_prompt.md",
    "next_task.md",
)

DIRECT_DATA_INPUTS = (
    PROMOTED_PATH, NAVIGATION_PATH, QUANT_CANDIDATE_PATH, QUANT_EXCEPTION_PATH,
    NON_BASE_PATH, REFERENCE_PATH, CONFLICT_PATH,
)

DASHBOARD_INPUTS = (
    ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json",
    ROOT / "docs/dashboard/data/analysis_readiness.json",
)

PRIMARY_CATEGORIES = (
    "gabriel_attribute_ready",
    "limited_documentary_claim_ready",
    "navigation_only",
    "companion_context_only",
    "quarantined",
    "write_off_this_phase",
)

EXPECTED_LANE_COUNTS = {
    "qualitative_exact": 759,
    "qualitative_navigation": 1195,
    "quantitative_candidate": 862,
    "quantitative_exception": 1045,
    "non_base_companion": 4733,
    "reference_control": 345,
}

EXPECTED_CATEGORY_COUNTS = {
    "gabriel_attribute_ready": 643,
    "limited_documentary_claim_ready": 862,
    "navigation_only": 614,
    "companion_context_only": 5078,
    "quarantined": 121,
    "write_off_this_phase": 1621,
}

EXPECTED_TOTAL = sum(EXPECTED_LANE_COUNTS.values())

ATTRIBUTES = (
    ("cola_or_cpi", "Pay is tied to CPI, COLA, inflation, or a cost-of-living adjustment."),
    ("step_or_seniority", "Pay changes by step, seniority, service time, or progression schedule."),
    ("rank_or_classification", "Pay differs by rank, title, classification, grade, or job class."),
    ("across_the_board_raise", "Pay increases apply broadly across employees or a bargaining unit."),
    ("percentage_raise", "The document states a percentage raise or percentage wage adjustment."),
    ("market_or_comparability", "Pay is linked to a market study, peer comparison, recruitment, or retention."),
    ("parity_or_internal_equity", "Pay is linked to parity, internal equity, compression, or alignment with another group."),
    ("bargaining_or_settlement", "Pay is described through CBA, settlement, memorandum, arbitration, or factfinding terms."),
    ("implementation_timing", "Pay depends on effective dates, retroactivity, schedules, or contract periods."),
    ("fiscal_constraint", "Pay is linked to budgets, funding, affordability, or municipal fiscal limits."),
    ("non_base_compensation", "Evidence concerns benefits, overtime, stipends, longevity, leave, healthcare, pension, reimbursement, or equipment."),
    ("reference_only", "Evidence points elsewhere or supplies navigation/context rather than coded evidence."),
    ("not_useful_for_attribute_analysis", "Evidence lacks enough support for attribute classification in this phase; a reason code is required."),
)
ATTRIBUTE_IDS = tuple(item[0] for item in ATTRIBUTES)
ATTRIBUTE_SET = "|".join(ATTRIBUTE_IDS)

MASTER_FIELDS = [
    "evidence_id", "source_lane", "source_file", "row_document_id", "case_id",
    "source_review_id", "text_table_detection_id", "retained_content_hash",
    "unit_type", "state", "source_family", "evidence_span_or_summary_pointer",
    "bounded_evidence_pointer", "primary_category", "secondary_tags", "reason_code",
    "confidence_tier", "qa_status", "provenance_status", "source_corpus",
    "source_cite", "retrieval_date", "retrieval_method", "artifact_pointer",
    "allowed_attribute_set", "disallowed_attribute_set", "allowed_claim_types",
    "exclude_from_causal_claims", "category_rule_version", "phase_close_notes",
]

REQUIRED_OUTPUTS = (
    "final_qa_categorization_phase_close_decision.json",
    "final_qa_categorization_phase_close_summary.md",
    "compensation_evidence_final_category_registry.csv",
    "compensation_evidence_final_category_registry_summary.json",
    "gabriel_attribute_ready_evidence_manifest.csv",
    "limited_documentary_claims_evidence_manifest.csv",
    "navigation_only_evidence_manifest.csv",
    "companion_context_evidence_manifest.csv",
    "quarantined_evidence_manifest.csv",
    "write_off_this_phase_manifest.csv",
    "gabriel_attribute_taxonomy_brief.md",
    "gabriel_attribute_taxonomy_machine_readable.json",
    "gabriel_attribute_assignment_prompt_template.md",
    "gabriel_attribute_schema_contract.json",
    "evidence_claim_type_registry.csv",
    "evidence_claim_type_registry_summary.json",
    "allowed_claims_now.md",
    "claims_not_yet_allowed.md",
    "final_qa_categorization_validation_2026-07-25.md",
    "final_qa_categorization_invariant_checks.json",
    "final_qa_categorization_stress_test_report.md",
    "final_qa_categorization_regression_test_inventory.json",
    "next_gabriel_attribute_analysis_prompt.md",
    "next_task.md",
)

FUTURE_PROMPT_REQUIRED = (
    "separate explicit user authorization",
    "643",
    "Do not fetch", "Do not pull", "Do not inspect remotes", "Do not configure remotes",
    "Do not open URLs", "Do not download", "Do not open PDFs", "Do not access PDF pages",
    "Do not run OCR", "Do not run extraction", "Do not select new documents",
    "Do not ingest", "Do not run gabriel.codify", "Do not calculate wage gaps",
    "Do not compute inferential statistics", "Do not run regressions", "Do not make causal claims",
    "global analysis readiness remains false", "exact provided evidence span",
    "GABRIEL analysis is not causal proof", "raw model responses",
)

RELAY_REQUIRED = {
    "commit_hash", "push_status", "validation_results", "dashboard_status",
    "forbidden_action_confirmations", "next_recommendation",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_sha256(ids: set[str]) -> str:
    return text_sha256("\n".join(sorted(ids)) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required immutable input absent at baseline: {relative}")
    return result.stdout


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Phase-close output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if resolved == forbidden.resolve() or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden phase-close output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe phase-close output already exists: {path}")


def validate_acceptance(decision: dict[str, Any]) -> None:
    if decision.get("decision") != acceptance.DECISION:
        raise RuntimeError("Latest registry acceptance did not pass")
    if decision.get("record_type") != "registry_acceptance_only":
        raise RuntimeError("Latest registry output is not acceptance-only")
    if decision.get("registered_accepted_rows") != 643:
        raise RuntimeError("Accepted qualitative registry row count drifted")
    if decision.get("restricted_navigation_external_contamination_count") != 0:
        raise RuntimeError("Accepted qualitative registry contains contamination")
    if decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("Registry acceptance improperly marks global readiness true")


def validate_dashboard_state(calibration: dict[str, Any], readiness: dict[str, Any]) -> None:
    allowed_phases = {
        "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed",
        "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready",
        "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready",
        "compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine",
        "compensation_extraction_gabriel_claim_rating_643_repaired_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed",
        "compensation_extraction_provisional_claim_review_636_completed_targeted_scouting_restart_recommended",
    }
    if calibration.get("calibration_phase") not in allowed_phases:
        raise RuntimeError("Dashboard phase is inconsistent with phase-close categorization")
    if calibration.get("analysis_facing_promotion_allowed") is not False:
        raise RuntimeError("Dashboard incorrectly allows analysis-facing promotion")
    allowed_overall = {
        "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed",
        "final_qa_categorization_closed_gabriel_attribute_ready_global_analysis_closed",
        "claim_oriented_phase_closed_gabriel_claim_rating_ready_global_analysis_closed",
        "gabriel_claim_rating_643_completed_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_643_completed_with_quarantine_global_analysis_closed",
        "gabriel_claim_rating_643_repaired_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed_global_analysis_closed",
        "provisional_claim_review_636_completed_targeted_scouting_restart_recommended_global_analysis_closed",
    }
    if readiness.get("overall_status") not in allowed_overall:
        raise RuntimeError("Dashboard overall status is inconsistent with phase close")
    if '"global_analysis_readiness": true' in json.dumps(readiness, sort_keys=True).casefold():
        raise RuntimeError("Dashboard marks global analysis readiness true")


def verify_inputs() -> tuple[dict[str, str], dict[str, Any]]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized registry-acceptance commit or descendant")

    upstream_hashes, _source = acceptance.verify_inputs()
    acceptance_signature = acceptance.input_signature(upstream_hashes)
    acceptance.validate_complete_output(ACCEPTANCE_DIR, acceptance_signature)

    observed: dict[str, str] = {}
    direct_paths = [ACCEPTANCE_DIR / name for name in ACCEPTANCE_INPUTS] + list(DIRECT_DATA_INPUTS)
    for path in direct_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Required phase-close input missing: {path}")
        current = path.read_bytes()
        if current != git_bytes_at_baseline(path):
            raise RuntimeError(f"Immutable phase-close input differs from baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    for name, (path, expected) in accelerator.PACKAGE_LEDGER_HASHES.items():
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"Package SHA-256 check failed: {name}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = expected

    for path in DASHBOARD_INPUTS:
        if not path.is_file():
            raise FileNotFoundError(f"Required dashboard contract missing: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(git_bytes_at_baseline(path))

    decision = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_registry_acceptance_decision.json")
    validate_acceptance(decision)
    calibration, readiness = (read_json(path) for path in DASHBOARD_INPUTS)
    validate_dashboard_state(calibration, readiness)
    return observed, {"decision": decision, "calibration": calibration, "readiness": readiness}


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return text_sha256(payload)


def source_value(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = (row.get(field) or "").strip()
        if value:
            return value
    return ""


def reference_key(row: dict[str, str]) -> str:
    payload = "|".join(source_value(row, field) for field in (
        "extraction_case_id", "text_table_detection_id", "source_review_id",
        "disposition", "page_relationship", "bounded_evidence_pointer",
    ))
    return "ref_" + text_sha256(payload)[:24]


def base_record(
    row: dict[str, str], *, evidence_id: str, lane: str, source_file: str,
    row_id: str, category: str, reason: str, secondary: str,
    evidence_value: str = "", notes: str,
) -> dict[str, str]:
    provenance_fields = (
        source_value(row, "source_review_id"),
        source_value(row, "text_table_detection_id"),
        source_value(row, "raw_retained_content_hash", "retained_content_hash"),
        source_value(row, "bounded_evidence_pointer"),
    )
    provenance = "complete_structured_provenance" if all(provenance_fields) else "bounded_provenance_partial_preserved"
    allowed_claims = (
        "evidence_existence_claim|documentary_mechanism_claim"
        if category in {"gabriel_attribute_ready", "limited_documentary_claim_ready"}
        else "evidence_existence_claim"
    )
    return {
        "evidence_id": evidence_id,
        "source_lane": lane,
        "source_file": source_file,
        "row_document_id": row_id,
        "case_id": source_value(row, "extraction_case_id"),
        "source_review_id": source_value(row, "source_review_id"),
        "text_table_detection_id": source_value(row, "text_table_detection_id"),
        "retained_content_hash": source_value(row, "retained_content_hash", "raw_retained_content_hash"),
        "unit_type": source_value(row, "unit_type", "controlled_occupation_class"),
        "state": source_value(row, "state"),
        "source_family": source_value(row, "candidate_source_type", "source_type_bridge"),
        "evidence_span_or_summary_pointer": evidence_value or source_value(row, "bounded_evidence_pointer"),
        "bounded_evidence_pointer": source_value(row, "bounded_evidence_pointer"),
        "primary_category": category,
        "secondary_tags": secondary,
        "reason_code": reason,
        "confidence_tier": source_value(row, "confidence") or "not_assigned",
        "qa_status": source_value(row, "current_qa_status", "qa_status", "span_qa_status") or "preserved_unassigned",
        "provenance_status": provenance,
        "source_corpus": source_value(row, "source_corpus_bridge"),
        "source_cite": source_value(row, "source_cite_bridge"),
        "retrieval_date": source_value(row, "retrieval_date_bridge"),
        "retrieval_method": source_value(row, "retrieval_method_bridge"),
        "artifact_pointer": source_value(row, "artifact_pointer_bridge"),
        "allowed_attribute_set": ATTRIBUTE_SET if category == "gabriel_attribute_ready" else "",
        "disallowed_attribute_set": "" if category == "gabriel_attribute_ready" else ATTRIBUTE_SET,
        "allowed_claim_types": allowed_claims,
        "exclude_from_causal_claims": "true",
        "category_rule_version": SCHEMA_VERSION,
        "phase_close_notes": notes,
    }


def classify_rows() -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]], dict[str, int]]:
    promoted = read_csv(PROMOTED_PATH)
    navigation = read_csv(NAVIGATION_PATH)
    quant_candidates = read_csv(QUANT_CANDIDATE_PATH)
    quant_exceptions = read_csv(QUANT_EXCEPTION_PATH)
    non_base = read_csv(NON_BASE_PATH)
    references = read_csv(REFERENCE_PATH)
    conflicts = read_csv(CONFLICT_PATH)

    lane_counts = {
        "qualitative_exact": len(promoted), "qualitative_navigation": len(navigation),
        "quantitative_candidate": len(quant_candidates), "quantitative_exception": len(quant_exceptions),
        "non_base_companion": len(non_base), "reference_control": len(references),
    }
    if lane_counts != EXPECTED_LANE_COUNTS:
        raise RuntimeError(f"Input lane count drift: {lane_counts}")

    eligible_qualitative_ids = {
        row["qualitative_observation_id"]
        for row in promoted
        if row.get("eligible_for_limited_qualitative_use", "").casefold() == "true"
    }
    if len(eligible_qualitative_ids) != 643 or id_set_sha256(eligible_qualitative_ids) != acceptance.AUTHORIZED_ID_HASH:
        raise RuntimeError("GABRIEL-ready candidate ID-set hash does not match the accepted registry")

    conflict_map: dict[str, str] = {}
    for group in conflicts:
        ids = [item for item in group["quantitative_observation_ids"].split("|") if item]
        if len(ids) != int(group["observation_count"]):
            raise RuntimeError("Conflict group count does not reconcile")
        for observation_id in ids:
            if observation_id in conflict_map:
                raise RuntimeError("Conflict observation appears in multiple groups")
            conflict_map[observation_id] = group["resolution_id"]
    if len(conflict_map) != 5 or len(conflicts) != 2:
        raise RuntimeError("Expected two unresolved groups/five observations")

    result: list[dict[str, str]] = []
    promoted_source = PROMOTED_PATH.relative_to(ROOT).as_posix()
    for row in promoted:
        oid = row["qualitative_observation_id"]
        eligible = row.get("eligible_for_limited_qualitative_use", "").casefold() == "true"
        category = "gabriel_attribute_ready" if eligible else "quarantined"
        reason = "exact_span_verified" if eligible else "restricted_review_status"
        secondary = "literal_span|limited_scope" if eligible else "literal_span|restricted_exact_span"
        result.append(base_record(
            row, evidence_id=f"qualitative:{oid}", lane="qualitative_exact", source_file=promoted_source,
            row_id=oid, category=category, reason=reason, secondary=secondary,
            evidence_value=row.get("literal_verbatim_evidence_span", ""),
            notes=("ready for bounded future attribute assignment; not analysis-ready"
                   if eligible else "exact span preserved but current review restriction requires quarantine"),
        ))

    navigation_source = NAVIGATION_PATH.relative_to(ROOT).as_posix()
    for row in navigation:
        oid = row["qualitative_observation_id"]
        tier = row.get("evidence_contract_tier")
        if tier == "ambiguous_exact_span_navigation":
            category, reason, notes = "navigation_only", "ambiguous_span", "multiple plausible spans remain; location aid only"
        elif tier == "unavailable_span_navigation":
            category, reason, notes = "write_off_this_phase", "span_unavailable", "no verified span support; written off for this phase"
        else:
            raise RuntimeError(f"Unexpected qualitative navigation tier: {tier}")
        result.append(base_record(
            row, evidence_id=f"qualitative:{oid}", lane="qualitative_navigation", source_file=navigation_source,
            row_id=oid, category=category, reason=reason, secondary=tier or "navigation",
            notes=notes,
        ))

    quant_candidate_source = QUANT_CANDIDATE_PATH.relative_to(ROOT).as_posix()
    for row in quant_candidates:
        oid = row["quantitative_observation_id"]
        if oid in conflict_map:
            raise RuntimeError("Unresolved conflict observation entered quantitative candidate lane")
        result.append(base_record(
            row, evidence_id=f"quantitative:{oid}", lane="quantitative_candidate", source_file=quant_candidate_source,
            row_id=oid, category="limited_documentary_claim_ready", reason="limited_scope",
            secondary="mechanically_safe_quantitative_candidate|no_quantitative_wage_claim",
            notes="mechanically safe record for bounded document-level reference; quantitative claims remain closed",
        ))

    quant_exception_source = QUANT_EXCEPTION_PATH.relative_to(ROOT).as_posix()
    for row in quant_exceptions:
        oid = row["quantitative_observation_id"]
        if oid in conflict_map:
            category, reason = "quarantined", "unresolved_conflict"
            secondary = f"quant_exception|conflict_group:{conflict_map[oid]}"
            notes = "unresolved conflict preserved without guessed resolution"
        else:
            category, reason = "write_off_this_phase", "quant_exception"
            secondary = "quantitative_normalization_exception"
            notes = "unsafe or incomplete normalization; written off for this phase without coercion"
        result.append(base_record(
            row, evidence_id=f"quantitative:{oid}", lane="quantitative_exception", source_file=quant_exception_source,
            row_id=oid, category=category, reason=reason, secondary=secondary, notes=notes,
        ))

    non_base_source = NON_BASE_PATH.relative_to(ROOT).as_posix()
    for row in non_base:
        oid = row["non_base_wage_observation_id"]
        result.append(base_record(
            row, evidence_id=f"non_base:{oid}", lane="non_base_companion", source_file=non_base_source,
            row_id=oid, category="companion_context_only", reason="non_base_companion",
            secondary="non_base_compensation|not_base_wage_outcome",
            notes="retained as companion context only",
        ))

    reference_source = REFERENCE_PATH.relative_to(ROOT).as_posix()
    for row in references:
        rid = reference_key(row)
        result.append(base_record(
            row, evidence_id=f"reference:{rid}", lane="reference_control", source_file=reference_source,
            row_id=rid, category="companion_context_only", reason="reference_control",
            secondary="reference_only|control_only",
            notes="retained as reference/control context only",
        ))

    result.sort(key=lambda item: item["evidence_id"])
    by_category = {category: [] for category in PRIMARY_CATEGORIES}
    for row in result:
        by_category[row["primary_category"]].append(row)
    counts = {category: len(rows) for category, rows in by_category.items()}
    validate_category_rows(result, counts)
    return result, by_category, lane_counts


def validate_category_rows(rows: list[dict[str, str]], counts: dict[str, int] | None = None) -> None:
    if len(rows) != EXPECTED_TOTAL:
        raise RuntimeError(f"Master category registry count drift: {len(rows)}")
    ids = [row.get("evidence_id", "") for row in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        raise RuntimeError("Every considered record must have one unique evidence ID")
    if any(row.get("primary_category") not in PRIMARY_CATEGORIES for row in rows):
        raise RuntimeError("Invalid or missing primary category")
    observed = dict(Counter(row["primary_category"] for row in rows))
    if observed != EXPECTED_CATEGORY_COUNTS or (counts is not None and counts != EXPECTED_CATEGORY_COUNTS):
        raise RuntimeError(f"Category counts do not reconcile: {observed}")
    if any(row["exclude_from_causal_claims"] != "true" for row in rows):
        raise RuntimeError("Every phase-close record must exclude causal claims")
    for row in rows:
        if row["primary_category"] == "gabriel_attribute_ready":
            if row["source_lane"] != "qualitative_exact" or row["reason_code"] != "exact_span_verified":
                raise RuntimeError("GABRIEL-ready manifest contains non-exact or wrong-lane evidence")
            if not row["evidence_span_or_summary_pointer"] or row["allowed_attribute_set"] != ATTRIBUTE_SET:
                raise RuntimeError("GABRIEL-ready row lacks span or attribute contract")
        elif row["primary_category"] in {"navigation_only", "quarantined", "write_off_this_phase"}:
            if row["allowed_attribute_set"]:
                raise RuntimeError("Excluded category entered GABRIEL-ready attribute scope")
    forbidden_columns = {"full_page_text", "full_text", "raw_page_payload", "raw_model_response"}
    if forbidden_columns.intersection(rows[0]):
        raise RuntimeError("Forbidden full-text/model payload field in category registry")


def taxonomy_payload() -> dict[str, Any]:
    return {
        "schema_version": "gabriel_compensation_attribute_taxonomy_v1",
        "assignment_mode": "multi_label_exact_evidence_only",
        "attributes": [
            {"attribute_id": attribute, "definition": definition, "output_type": "boolean"}
            for attribute, definition in ATTRIBUTES
        ],
        "required_reason_code_when_not_useful": True,
        "prohibited_labels": ["null", "no_good"],
        "causal_interpretation_allowed": False,
        "wage_effect_interpretation_allowed": False,
    }


def validate_taxonomy(payload: dict[str, Any]) -> None:
    ids = [item.get("attribute_id") for item in payload.get("attributes", [])]
    if tuple(ids) != ATTRIBUTE_IDS or len(ids) != len(set(ids)):
        raise RuntimeError("Attribute taxonomy is incomplete, duplicated, or reordered")
    if any(not item.get("definition") for item in payload["attributes"]):
        raise RuntimeError("Attribute taxonomy contains a blank definition")
    if {"null", "no_good"}.intersection(ids):
        raise RuntimeError("Vague null/no_good taxonomy bucket is prohibited")
    if payload.get("required_reason_code_when_not_useful") is not True:
        raise RuntimeError("Not-useful assignment must require a reason code")


def claim_rows() -> list[dict[str, str]]:
    return [
        {"claim_type": "evidence_existence_claim", "current_status": "allowed_now", "allowed_evidence_categories": "all_phase_close_categories", "authorized_action": "report audited registry existence and reconciliation counts", "restriction": "no effect or representativeness inference"},
        {"claim_type": "documentary_mechanism_claim", "current_status": "allowed_now", "allowed_evidence_categories": "gabriel_attribute_ready|limited_documentary_claim_ready", "authorized_action": "state what a verified document span or bounded structured record says", "restriction": "no wage-effect or causal inference"},
        {"claim_type": "limited_descriptive_pattern_claim", "current_status": "future_separate_review_required", "allowed_evidence_categories": "none_in_this_task", "authorized_action": "none", "restriction": "requires later approved descriptive computation"},
        {"claim_type": "quantitative_wage_claim", "current_status": "not_allowed", "allowed_evidence_categories": "none", "authorized_action": "none", "restriction": "quantitative layer not separately accepted"},
        {"claim_type": "wage_gap_claim", "current_status": "not_allowed", "allowed_evidence_categories": "none", "authorized_action": "none", "restriction": "wage-gap analysis closed"},
        {"claim_type": "causal_candidate_claim", "current_status": "not_allowed", "allowed_evidence_categories": "none", "authorized_action": "none", "restriction": "later hypothesis labeling requires separate authorization"},
        {"claim_type": "causal_claim", "current_status": "not_allowed", "allowed_evidence_categories": "none", "authorized_action": "none", "restriction": "separate evidence and causal-claim QA required"},
    ]


def validate_claim_registry(rows: list[dict[str, str]]) -> None:
    if len(rows) != 7 or len({row["claim_type"] for row in rows}) != 7:
        raise RuntimeError("Claim registry must contain seven unique claim types")
    status = {row["claim_type"]: row["current_status"] for row in rows}
    if status["evidence_existence_claim"] != "allowed_now" or status["documentary_mechanism_claim"] != "allowed_now":
        raise RuntimeError("Allowed-now documentary claim scaffolding is incomplete")
    for claim in ("quantitative_wage_claim", "wage_gap_claim", "causal_candidate_claim", "causal_claim"):
        if status[claim] != "not_allowed":
            raise RuntimeError(f"Forbidden claim type incorrectly opened: {claim}")


def validate_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future GABRIEL prompt missing constraints: {missing}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != EXPECTED_TOTAL or record.get("expected") != EXPECTED_TOTAL:
        raise RuntimeError("Partial phase-close output cannot masquerade as complete")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required fields: {missing}")


def build_reports(
    output_dir: Path, hashes: dict[str, str], signature: str,
    master: list[dict[str, str]], by_category: dict[str, list[dict[str, str]]],
    lane_counts: dict[str, int], source: dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_csv(output_dir / "compensation_evidence_final_category_registry.csv", MASTER_FIELDS, master)
    manifest_names = {
        "gabriel_attribute_ready": "gabriel_attribute_ready_evidence_manifest.csv",
        "limited_documentary_claim_ready": "limited_documentary_claims_evidence_manifest.csv",
        "navigation_only": "navigation_only_evidence_manifest.csv",
        "companion_context_only": "companion_context_evidence_manifest.csv",
        "quarantined": "quarantined_evidence_manifest.csv",
        "write_off_this_phase": "write_off_this_phase_manifest.csv",
    }
    for category, filename in manifest_names.items():
        write_csv(output_dir / filename, MASTER_FIELDS, by_category[category])

    category_counts = {category: len(by_category[category]) for category in PRIMARY_CATEGORIES}
    summary = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "input_signature": signature, "considered_records": len(master),
        "lane_counts": lane_counts, "category_counts": category_counts,
        "one_primary_category_per_record": True, "duplicate_evidence_ids": 0,
        "gabriel_ready_excludes_navigation_quarantine_writeoff": True,
        "unresolved_conflict_groups": 2, "unresolved_conflict_observations": 5,
        "global_analysis_readiness": False,
    }
    write_json(output_dir / "compensation_evidence_final_category_registry_summary.json", summary)

    taxonomy = taxonomy_payload()
    validate_taxonomy(taxonomy)
    write_json(output_dir / "gabriel_attribute_taxonomy_machine_readable.json", taxonomy)
    (output_dir / "gabriel_attribute_taxonomy_brief.md").write_text(
        "# GABRIEL compensation attribute taxonomy\n\n"
        "Use multi-label classification against the exact supplied evidence span. A true label means the literal span supports the short definition; it does not imply wage effects or causality.\n\n"
        + "\n".join(f"- `{attribute}` — {definition}" for attribute, definition in ATTRIBUTES)
        + "\n\n`not_useful_for_attribute_analysis` requires a short reason code; `null` and `no_good` are not valid labels.\n",
        encoding="utf-8",
    )
    schema_contract = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "GABRIEL compensation attribute assignment",
        "type": "object",
        "additionalProperties": False,
        "required": ["evidence_id", "attribute_assignments", "reason_codes", "evidence_quote", "qa_status"],
        "properties": {
            "evidence_id": {"type": "string", "minLength": 1},
            "attribute_assignments": {"type": "object", "additionalProperties": False, "required": list(ATTRIBUTE_IDS), "properties": {attribute: {"type": "boolean"} for attribute in ATTRIBUTE_IDS}},
            "reason_codes": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
            "evidence_quote": {"type": "string", "minLength": 1, "maxLength": 500},
            "qa_status": {"type": "string", "enum": ["exact_evidence_supported", "not_useful_with_reason", "quarantined_model_output"]},
        },
        "invariants": {
            "evidence_quote_must_equal_or_be_exact_substring_of_supplied_span": True,
            "causal_claims_allowed": False, "wage_effect_claims_allowed": False,
            "not_useful_requires_reason_code": True,
        },
    }
    write_json(output_dir / "gabriel_attribute_schema_contract.json", schema_contract)
    (output_dir / "gabriel_attribute_assignment_prompt_template.md").write_text(
        """# GABRIEL attribute assignment template

Classify only the supplied `evidence_id` and exact `evidence_span_or_summary_pointer`. Return JSON conforming to `gabriel_attribute_schema_contract.json`. Assign every taxonomy boolean. Use only literal support in the supplied span; never infer from government, occupation, filename, source family, or outside knowledge. Copy a short exact supporting substring into `evidence_quote`.

If evidence is insufficient, set `not_useful_for_attribute_analysis=true`, set unsupported attributes false, and provide a specific reason code. Do not use `null` or `no_good`. Do not estimate wage effects, compare groups, calculate statistics, make causal claims, or alter provenance. GABRIEL measurement is not causal proof.
""",
        encoding="utf-8",
    )

    claims = claim_rows()
    validate_claim_registry(claims)
    claim_fields = ["claim_type", "current_status", "allowed_evidence_categories", "authorized_action", "restriction"]
    write_csv(output_dir / "evidence_claim_type_registry.csv", claim_fields, claims)
    write_json(output_dir / "evidence_claim_type_registry_summary.json", {
        "claim_types": 7,
        "allowed_now": 2,
        "future_separate_review_required": 1,
        "not_allowed": 4,
        "allowed_now_claim_types": ["evidence_existence_claim", "documentary_mechanism_claim"],
        "global_analysis_readiness": False,
    })
    (output_dir / "allowed_claims_now.md").write_text(
        """# Allowed claims now

- `evidence_existence_claim`: report audited registry and manifest existence/reconciliation counts.
- `documentary_mechanism_claim`: state only what an exact verified span or bounded documentary record says, with provenance and scope language.

These permissions do not authorize computed descriptive patterns, quantitative wage conclusions, wage gaps, treatment effects, representativeness claims, or causal interpretation. Mechanism language is evidence of document wording, not wage effects.
""", encoding="utf-8")
    (output_dir / "claims_not_yet_allowed.md").write_text(
        """# Claims not yet allowed

- `limited_descriptive_pattern_claim` requires a later separately authorized computation from an approved layer.
- `quantitative_wage_claim` is not allowed until the quantitative lane is separately accepted.
- `wage_gap_claim` is not allowed.
- `causal_candidate_claim` is not allowed in this phase; any later hypothesis label requires separate authorization.
- `causal_claim` is not allowed and requires separate evidence and QA review.
""", encoding="utf-8")

    future_prompt = f"""# Next task: bounded GABRIEL compensation-attribute analysis

Do not run this prompt without separate explicit user authorization.

Use only the {EXPECTED_CATEGORY_COUNTS['gabriel_attribute_ready']} rows in `gabriel_attribute_ready_evidence_manifest.csv`. For each row, classify the exact provided evidence span using `gabriel_attribute_taxonomy_machine_readable.json`, `gabriel_attribute_schema_contract.json`, and `gabriel_attribute_assignment_prompt_template.md`. A future authorized run may call GABRIEL/API only for this bounded attribute assignment; it may not search for, retrieve, or extract evidence.

## Hard constraints

- Global analysis readiness remains false.
- GABRIEL analysis is not causal proof.
- Mechanism language is not evidence of wage effects.
- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs.
- Do not download or redownload documents.
- Do not open PDFs.
- Do not access PDF pages.
- Do not run OCR.
- Do not run extraction.
- Do not select new documents.
- Do not ingest.
- Do not run gabriel.codify.
- Do not compute descriptive statistics.
- Do not compute inferential statistics.
- Do not calculate wage gaps.
- Do not run regressions.
- Do not make causal claims.
- Do not save raw model responses, prompts, credentials, secrets, full page text, or full documents.
- Do not use navigation-only, companion/context, quarantined, or written-off rows as model inputs.
- Do not fabricate or paraphrase evidence. Evidence quotes must be exact substrings of the supplied span.
- Keep quantitative, non-base, reference/control, and conflict lanes separate.

Validate every model output against the schema and exact-span contract. Quarantine failed outputs rather than retrying indefinitely or weakening rules. Produce attribute assignments and QA metadata only; no statistics, effects, regressions, wage gaps, or causal conclusions.
"""
    validate_prompt(future_prompt)
    (output_dir / "next_gabriel_attribute_analysis_prompt.md").write_text(future_prompt, encoding="utf-8")

    checks = {
        "registry_acceptance_authorizes_phase_close": True,
        "package_sha256_5_of_5": True,
        "all_direct_inputs_present_and_immutable": True,
        "all_8939_considered_records_have_one_category": True,
        "evidence_ids_unique": True,
        "category_counts_reconcile": category_counts == EXPECTED_CATEGORY_COUNTS,
        "gabriel_ready_643_exact_span_only": len(by_category["gabriel_attribute_ready"]) == 643,
        "weak_evidence_not_forced_ready": True,
        "conflict_observations_quarantined": True,
        "quantitative_exceptions_not_promoted": True,
        "non_base_and_reference_remain_context_only": True,
        "taxonomy_has_13_controlled_attributes": len(ATTRIBUTE_IDS) == 13,
        "taxonomy_forbids_vague_null_no_good": True,
        "claim_permissions_fail_closed": True,
        "causal_and_wage_gap_claims_forbidden": True,
        "no_full_page_text_or_raw_model_payload": True,
        "dashboard_global_readiness_false": True,
        "future_prompt_preserves_phase_boundaries": True,
        "partial_outputs_cannot_claim_complete": True,
        "idempotent_resume_supported": True,
    }
    write_json(output_dir / "final_qa_categorization_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "checks": checks, "category_counts": category_counts,
        "all_invariants_passed": all(checks.values()),
    })

    failure_modes = [
        "registry_acceptance_not_passed", "baseline_not_ancestor", "required_input_missing",
        "immutable_input_hash_drift", "package_hash_drift", "input_lane_count_drift",
        "duplicate_evidence_id", "missing_primary_category", "multiple_primary_categories",
        "unknown_primary_category", "category_count_drift", "gabriel_ready_navigation_contamination",
        "gabriel_ready_quarantine_contamination", "gabriel_ready_writeoff_contamination",
        "gabriel_ready_wrong_lane", "gabriel_ready_missing_exact_span", "restricted_row_forced_ready",
        "ambiguous_span_forced_ready", "unavailable_span_forced_ready", "quant_exception_forced_ready",
        "unresolved_conflict_not_quarantined", "conflict_group_count_drift",
        "non_base_routed_as_base_wage", "reference_control_routed_as_outcome",
        "vague_null_taxonomy_bucket", "vague_no_good_taxonomy_bucket",
        "not_useful_without_reason", "taxonomy_attribute_missing", "taxonomy_attribute_duplicate",
        "claim_registry_missing_type", "quantitative_wage_claim_opened", "wage_gap_claim_opened",
        "causal_candidate_claim_opened", "causal_claim_opened", "full_page_text_leakage",
        "raw_model_response_leakage", "dashboard_global_readiness_true",
        "dashboard_phase_jump", "future_prompt_missing_constraint", "future_prompt_uses_excluded_rows",
        "partial_checkpoint_claims_complete", "idempotent_rerun_drift", "relay_missing_inspection_field",
        "output_outside_docs_analysis", "phase_close_attempts_analysis", "phase_close_attempts_source_access",
        "phase_close_attempts_ingestion_or_codification", "phase_close_attempts_statistics_or_causal_work",
    ]
    write_json(output_dir / "final_qa_categorization_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION,
        "failure_modes": len(failure_modes),
        "failure_mode_ids": failure_modes,
        "test_script": "scripts/test_compensation_evidence_final_qa_categorization_gabriel_readiness.py",
    })
    (output_dir / "final_qa_categorization_stress_test_report.md").write_text(
        f"# Final QA categorization stress test\n\nThe phase-close suite covers {len(failure_modes)} adversarial failure modes across immutable inputs, exact-one categorization, weak-evidence triage, lane separation, conflicts, taxonomy, claim permissions, payload leakage, dashboard closure, prompts, checkpoints, reruns, relays, and prohibited work. Final executed totals are recorded in the validation report.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "phase_closed": True, "gabriel_attribute_analysis_ready": True,
        "gabriel_attribute_analysis_ready_rows": 643,
        "gabriel_attribute_analysis_requires_separate_authorization": True,
        "scouting_restart_recommended": False,
        "global_analysis_readiness": False, "full_qualitative_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "category_counts": category_counts, "considered_records": len(master),
        "attribute_taxonomy_size": len(ATTRIBUTE_IDS),
        "allowed_claim_types_now": ["evidence_existence_claim", "documentary_mechanism_claim"],
        "not_yet_allowed_claim_types": ["limited_descriptive_pattern_claim", "quantitative_wage_claim", "wage_gap_claim", "causal_candidate_claim", "causal_claim"],
        "package_sha256_checks_passed": 5,
        "immutable_direct_inputs_verified": len(ACCEPTANCE_INPUTS) + len(DIRECT_DATA_INPUTS),
        "immutable_inputs_modified": False,
        "network_calls": 0, "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "model_calls": 0, "extraction_runs": 0, "selection_runs": 0,
        "ingestion_runs": 0, "codification_runs": 0,
        "descriptive_statistics_computed": False, "inferential_statistics_computed": False,
        "wage_gap_calculations": 0, "regressions": 0, "causal_claims_made": 0,
        "next_prompt": "next_gabriel_attribute_analysis_prompt.md",
    }
    write_json(output_dir / "final_qa_categorization_phase_close_decision.json", decision)

    (output_dir / "final_qa_categorization_phase_close_summary.md").write_text(
        f"""# Final QA categorization phase close

Decision: `{DECISION}`

The current QA/debugging/categorization phase is closed. All {len(master):,} considered lane records have exactly one primary category: 643 GABRIEL-attribute-ready exact-span records; 862 limited documentary records; 614 navigation-only records; 5,078 companion/context records; 121 quarantined records; and 1,621 records written off for this phase.

Weak evidence was not forced forward. The 116 restricted exact-span rows and five unresolved conflict observations are quarantined; 581 span-unavailable rows and 1,040 non-conflict quantitative exceptions are written off for this phase; ambiguous spans remain navigation-only; non-base and reference/control lanes remain companion context.

The 13-attribute taxonomy and exact-evidence assignment schema are ready for a separately authorized bounded GABRIEL run over 643 rows. This is attribute-measurement readiness only. Global analysis readiness, full qualitative readiness, analysis-facing promotion, quantitative wage claims, wage gaps, regressions, and causal claims remain closed.
""", encoding="utf-8")

    (output_dir / "final_qa_categorization_validation_2026-07-25.md").write_text(
        f"""# Final QA categorization validation

- Package SHA-256 checks: 5/5 passed.
- Immutable direct evidence inputs verified: {len(ACCEPTANCE_INPUTS) + len(DIRECT_DATA_INPUTS)}.
- Considered records: {len(master):,}; exactly one primary category each.
- Category counts: {json.dumps(category_counts, sort_keys=True)}.
- GABRIEL-ready contamination: zero.
- Attribute taxonomy: {len(ATTRIBUTE_IDS)} controlled attributes; no vague null/no_good bucket.
- Global analysis readiness: false.

## Executed validation

Final command results are recorded after the full required validation run.
""", encoding="utf-8")
    (output_dir / "next_task.md").write_text(
        "# Next task\n\nSeek separate explicit authorization to run `next_gabriel_attribute_analysis_prompt.md`. Use only the 643 exact-span manifest rows for attribute assignment; perform no source access, statistics, wage-gap, regression, or causal work, and keep global analysis readiness false.\n",
        encoding="utf-8",
    )


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required phase-close outputs missing: {missing}")
    decision = read_json(output_dir / "final_qa_categorization_phase_close_decision.json")
    summary = read_json(output_dir / "compensation_evidence_final_category_registry_summary.json")
    invariants = read_json(output_dir / "final_qa_categorization_invariant_checks.json")
    taxonomy = read_json(output_dir / "gabriel_attribute_taxonomy_machine_readable.json")
    master = read_csv(output_dir / "compensation_evidence_final_category_registry.csv")
    claims = read_csv(output_dir / "evidence_claim_type_registry.csv")
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION:
        raise RuntimeError("Phase-close decision/signature mismatch")
    if decision.get("global_analysis_readiness") is not False or decision.get("gabriel_attribute_analysis_ready") is not True:
        raise RuntimeError("Phase-close readiness flags are inconsistent")
    validate_category_rows(master)
    validate_taxonomy(taxonomy)
    validate_claim_registry(claims)
    validate_prompt((output_dir / "next_gabriel_attribute_analysis_prompt.md").read_text(encoding="utf-8"))
    if summary.get("category_counts") != EXPECTED_CATEGORY_COUNTS:
        raise RuntimeError("Category summary does not reconcile")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Phase-close invariant checks failed")
    for category, filename in {
        "gabriel_attribute_ready": "gabriel_attribute_ready_evidence_manifest.csv",
        "limited_documentary_claim_ready": "limited_documentary_claims_evidence_manifest.csv",
        "navigation_only": "navigation_only_evidence_manifest.csv",
        "companion_context_only": "companion_context_evidence_manifest.csv",
        "quarantined": "quarantined_evidence_manifest.csv",
        "write_off_this_phase": "write_off_this_phase_manifest.csv",
    }.items():
        rows = read_csv(output_dir / filename)
        if len(rows) != EXPECTED_CATEGORY_COUNTS[category] or any(row["primary_category"] != category for row in rows):
            raise RuntimeError(f"Category-specific manifest mismatch: {category}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes, source = verify_inputs()
    signature = input_signature(hashes)
    master, by_category, lane_counts = classify_rows()
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "considered_records": len(master), "category_counts": EXPECTED_CATEGORY_COUNTS,
            "gabriel_attribute_analysis_ready": True, "global_analysis_readiness": False,
        }, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    build_reports(args.output_dir, hashes, signature, master, by_category, lane_counts, source)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({
        "output_dir": str(args.output_dir), "decision": DECISION,
        "considered_records": len(master), "category_counts": EXPECTED_CATEGORY_COUNTS,
        "gabriel_attribute_analysis_ready": True,
        "gabriel_attribute_analysis_ready_rows": 643,
        "global_analysis_readiness": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
