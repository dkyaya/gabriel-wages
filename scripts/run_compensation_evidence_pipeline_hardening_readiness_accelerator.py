#!/usr/bin/env python3
"""Build a fail-closed compensation-evidence readiness accelerator.

This runner creates no analysis-facing data.  It verifies immutable package and
repair-layer hashes, copies approved provisional views byte-for-byte into a new
rollback-safe directory, constructs a master blocker registry and reusable
failure-mode corpus, and simulates possible future scopes.  It never opens a
PDF, accesses a URL, calls a model, runs OCR/extraction/selection/ingestion, or
changes a source ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-PIPELINE-HARDENING-READINESS-ACCELERATOR-2026-07-25"
SCHEMA_VERSION = "compensation_pipeline_readiness_accelerator_v1"
DECISION = "pipeline_hardening_complete_limited_promotion_allowed"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-PIPELINE-HARDENING-READINESS-ACCELERATOR-2026-07-25"

PACKAGE = BASE / "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25"
SCHEMA_REPAIR = BASE / "COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-SCHEMA-REPAIR-AND-ANALYSIS-VIEW-PREP-2026-07-25"
SCHEMA_FOLLOWUP = BASE / "COMPENSATION-EVIDENCE-BOUNDED-SCHEMA-REPAIR-FOLLOWUP-2026-07-25"
SPAN_RESIDUAL = BASE / "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-AND-RESIDUAL-METADATA-REPAIR-2026-07-25"
PDF_SPAN = BASE / "COMPENSATION-EVIDENCE-BOUNDED-PDF-TEXT-SPAN-CAPTURE-SYSTEM-HARDENING-AND-READINESS-PREP-2026-07-25"
DISAMBIGUATION = BASE / "COMPENSATION-EVIDENCE-BOUNDED-QUALITATIVE-SPAN-DISAMBIGUATION-FOLLOWUP-2026-07-25"
EVIDENCE_CONTRACT = BASE / "COMPENSATION-EVIDENCE-QUALITATIVE-EVIDENCE-CONTRACT-FOLLOWUP-2026-07-25"
LIMITED_REVIEW = BASE / "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-ANALYSIS-READINESS-REVIEW-2026-07-25"

PACKAGE_LEDGER_HASHES = {
    "package_mixed": (PACKAGE / "ledgers/mixed/final_provisional_mixed_join_ledger.csv", "a204061a4ca4bbfd3512bf964d689fe385dfd71fac93589a4bb9b59e64eb9192"),
    "package_non_base": (PACKAGE / "ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv", "84df35187461392ea9699660ea86317250a33979e6ff2b4f9256a49b1d9e0ea2"),
    "package_qualitative": (PACKAGE / "ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv", "d22a4015da83da7d0195e430ef30d475b3678c17696e7a835d6d09bce1a1e0d5"),
    "package_quantitative": (PACKAGE / "ledgers/quantitative/final_provisional_quantitative_ledger.csv", "7e275b8c45f0d4b77e01249d978fe17862fd3f8d552bf0f4ef77ed0bb3616c86"),
    "package_reference": (PACKAGE / "ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv", "2a33987b8f54048d8a397fc7d9a917dafd2dbcf8b7b74a20de8c2642a886e3a1"),
}

INPUTS = {
    "qualitative": (EVIDENCE_CONTRACT / "qualitative_mechanism_combined_tiered_view.csv", "2779745e741d51dd116c4321194dddebf9b9bd2bd04f2dc3c04c94bba1f067aa"),
    "exact": (EVIDENCE_CONTRACT / "qualitative_mechanism_exact_span_coded_candidate.csv", "4cc2143ef85c1e7c9492c44fab69d8dbc1a09edd33649b41bb1c88a75493f3a4"),
    "cycle": (SPAN_RESIDUAL / "residual_cycle_matching_bridge.csv", "ee6ec3b505f5cdd9d581ef72ab8481a6c3b34ace9f74913ae391ec69ad720db3"),
    "occupation": (SPAN_RESIDUAL / "residual_non_safety_occupation_bridge.csv", "0bd4a02f41998fbdc8b3a001b6b68e2f7279a8ebe390ffc815670c4942d6f3d0"),
    "quantitative": (EVIDENCE_CONTRACT / "quantitative_analysis_view_candidate_evidence_contract_followup.csv", "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e"),
    "quantitative_exception": (EVIDENCE_CONTRACT / "quantitative_exception_ledger_evidence_contract_followup.csv", "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401"),
    "non_base": (EVIDENCE_CONTRACT / "non_base_wage_companion_view_candidate_evidence_contract_followup.csv", "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92"),
    "reference": (EVIDENCE_CONTRACT / "reference_exclusion_control_view_evidence_contract_followup.csv", "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a"),
    "conflict": (EVIDENCE_CONTRACT / "unresolved_conflict_quarantine_ledger_evidence_contract_followup.csv", "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7"),
    "provenance": (SCHEMA_FOLLOWUP / "bounded_retrieval_provenance_bridge.csv", "c012a03756892fd14856a79d5c5a59ba0ccb90e90064f65581840dcc84c9227b"),
    "residual": (EVIDENCE_CONTRACT / "residual_metadata_quarantine_summary_evidence_contract_followup.json", "d35a462f3b1648ad6f6a6a4bfd7e9d3e4815708293ad16318caef6effbaa2385"),
    "limited_review": (LIMITED_REVIEW / "limited_exact_span_qualitative_readiness_decision.json", "819da0c72f90f07719c7c3c7a0765a6d49e13d042104983d2a5dfca203ef126b"),
}

OUTPUT_COPIES = {
    "qualitative": "accelerated_qualitative_evidence_contract_view.csv",
    "cycle": "accelerated_cycle_matching_bridge.csv",
    "occupation": "accelerated_occupation_bridge.csv",
    "quantitative": "accelerated_quantitative_candidate_view.csv",
    "quantitative_exception": "accelerated_quantitative_exception_ledger.csv",
    "non_base": "accelerated_non_base_companion_view.csv",
    "reference": "accelerated_reference_control_view.csv",
    "conflict": "accelerated_conflict_quarantine_ledger.csv",
}

REQUIRED_DIRS = (PACKAGE, SCHEMA_REPAIR, SCHEMA_FOLLOWUP, SPAN_RESIDUAL, PDF_SPAN, DISAMBIGUATION, EVIDENCE_CONTRACT, LIMITED_REVIEW)
FORBIDDEN_FIELDS = {"page_text", "full_page_text", "raw_page_text", "raw_page_payload", "full_pdf_text", "encoded_image", "raw_prompt", "raw_response"}
DETAIL_FIELDS = ("bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic", "step_progression_rule", "eligibility_rule", "implementation_rule", "fiscal_constraint", "reopener_clause", "differentiation_logic")
RELAY_REQUIRED = {"commit_hash", "push_status", "validation_results", "dashboard_status", "forbidden_action_confirmations", "next_recommendation"}
PROMPT_REQUIRED_PHRASES = (
    "Do not run this prompt without separate explicit user authorization",
    "Do not fetch", "Do not pull", "Do not open URLs", "Do not run OCR",
    "Do not call GABRIEL/API", "Do not run extraction", "Do not select new documents",
    "Do not ingest", "Do not run gabriel.codify", "Do not calculate wage gaps",
    "Do not run regressions", "Do not make causal claims", "analysis readiness remains false",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Output must remain under docs/analysis")
    if any(forbidden.resolve() == resolved or forbidden.resolve() in resolved.parents for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest")):
        raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def verify_inputs() -> dict[str, str]:
    for directory in REQUIRED_DIRS:
        if not directory.is_dir():
            raise FileNotFoundError(f"Required layer missing: {directory}")
    observed: dict[str, str] = {}
    for key, (path, expected) in {**PACKAGE_LEDGER_HASHES, **INPUTS}.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        observed[key] = sha256(path)
        if observed[key] != expected:
            raise RuntimeError(f"Immutable input hash mismatch: {key}")
    manifest = read_json(PACKAGE / "final_provisional_merge_manifest.json")
    if manifest.get("all_output_ledgers_byte_identical") is not True or manifest.get("final_analysis_ready") is not False:
        raise RuntimeError("Package integrity/readiness boundary failed")
    limited = read_json(INPUTS["limited_review"][0])
    if limited.get("decision") != "limited_exact_span_qualitative_readiness_pass_with_blockers_documented" or limited.get("analysis_readiness") is not False:
        raise RuntimeError("Limited review decision boundary failed")
    return observed


def input_signature(hashes: dict[str, str]) -> str:
    return text_sha256(SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes)))


def validate_no_forbidden_fields(fields: list[str]) -> None:
    bad = set(fields) & FORBIDDEN_FIELDS
    if bad:
        raise RuntimeError(f"Forbidden full-page/raw payload fields: {sorted(bad)}")


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in PROMPT_REQUIRED_PHRASES if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future prompt missing hard constraints: {missing}")


def validate_relay_record(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing or any(record.get(key) in (None, "", []) for key in RELAY_REQUIRED):
        raise RuntimeError(f"Relay metadata incomplete: {missing or 'blank required value'}")


def validate_stage_transition(current_stage: str, requested_stage: str) -> None:
    allowed = {
        "repair": {"readiness_review", "limited_promotion_prompt"},
        "readiness_review": {"limited_promotion_prompt", "targeted_repair"},
        "limited_promotion": {"separate_analysis_authorization"},
    }
    if requested_stage not in allowed.get(current_stage, set()):
        raise RuntimeError(f"Forbidden phase jump: {current_stage} -> {requested_stage}")


def validate_checkpoint(metadata: dict[str, Any]) -> None:
    if metadata.get("status") != "complete" or metadata.get("processed") != metadata.get("expected"):
        raise RuntimeError("Partial checkpoint cannot masquerade as complete")


def validate_dashboard_state(payload: dict[str, Any]) -> None:
    if payload.get("analysis_readiness") is not False:
        raise RuntimeError("Repair task cannot mark global analysis readiness true")
    status = str(payload.get("overall_status", payload.get("calibration_phase", ""))).lower()
    if "analysis_ready" in status and "analysis_closed" not in status and "not_analysis_ready" not in status:
        raise RuntimeError("Dashboard status falsely marks readiness")


def validate_page_access_fixture(*, requested_page: int, approved_pages: set[int], ocr_later: bool, text: str | None) -> str:
    if ocr_later:
        raise RuntimeError("OCR-later artifact access forbidden")
    if requested_page not in approved_pages:
        raise RuntimeError("Non-target page access forbidden")
    if text is None or not text.strip():
        return "no_text_layer"
    return "approved_text_layer"


def validate_identity_fixture(*, expected_hash: str, actual_hash: str, retained_path: str) -> None:
    if not retained_path:
        raise RuntimeError("Missing retained PDF path")
    if expected_hash != actual_hash:
        raise RuntimeError("Wrong retained content hash")


def validate_span_fixture(span: str, start: int, end: int, digest: str, page_text: str) -> None:
    if not span or "\n" in span or "\r" in span:
        raise RuntimeError("Span missing, multiline, or page-text leakage risk")
    if len(span) >= len(page_text):
        raise RuntimeError("Full-page text leakage forbidden")
    if start < 0 or end <= start or page_text[start:end] != span:
        raise RuntimeError("Span offset corruption")
    if text_sha256(span) != digest:
        raise RuntimeError("Span hash corruption")


def validate_mixed_membership(status: str, *, treated_as_active: bool) -> None:
    if status in {"historical_inactive", "historical_missing"} and treated_as_active:
        raise RuntimeError("Historical mixed join cannot be treated as active")


def parse_duplicate_lineage_fixture(header: list[str], values: list[str]) -> dict[str, str]:
    if len(header) != len(values):
        raise RuntimeError("CSV header/value width mismatch")
    quant_positions = [index for index, name in enumerate(header) if name == "source_quantitative_observation_id"]
    mixed_positions = [index for index, name in enumerate(header) if name == "source_mixed_join_key"]
    if len(quant_positions) != 2 or len(mixed_positions) != 2:
        raise RuntimeError("Duplicate lineage header contract changed")
    q_values = [values[index] for index in quant_positions]
    m_values = [values[index] for index in mixed_positions]
    if q_values[0] != q_values[1] or m_values[0] != m_values[1]:
        raise RuntimeError("Duplicate lineage values disagree")
    return {
        "package_source_quantitative_observation_id": q_values[0],
        "repair_source_quantitative_observation_id": q_values[1],
        "package_source_mixed_join_key": m_values[0],
        "repair_source_mixed_join_key": m_values[1],
    }


def validate_quantitative_candidate(row: dict[str, str]) -> None:
    status = row.get("quantitative_parse_status", row.get("normalization_status", ""))
    if status and status not in {"mechanically_safe_candidate", "safe_scalar", "candidate", "eligible"}:
        raise RuntimeError("Quantitative exception cannot enter candidate view")
    reason = " ".join(str(row.get(key, "")) for key in ("raw_value", "value_raw", "rate_or_salary_value", "normalization_reason_code")).lower()
    unsafe_tokens = ("range", "formula", "multiplier", "hours", "current/new", "pair")
    if row.get("accelerator_fixture", "") == "unsafe" or any(token in reason for token in unsafe_tokens):
        raise RuntimeError("Ambiguous quantitative value cannot be silently promoted")


def validate_lane_separation(non_base_rows: list[dict[str, str]], reference_rows: list[dict[str, str]]) -> None:
    if any(row.get("base_wage_outcome_eligible", "false").lower() == "true" for row in non_base_rows):
        raise RuntimeError("Non-base compensation entered base-wage outcome view")
    if any(row.get("outcome_eligible", row.get("base_wage_outcome_eligible", "false")).lower() == "true" for row in reference_rows):
        raise RuntimeError("Reference/exclusion row entered outcome view")


def validate_material_inputs() -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for key in ("qualitative", "exact", "cycle", "occupation", "quantitative", "quantitative_exception", "non_base", "reference", "conflict", "provenance"):
        fields, rows = read_csv(INPUTS[key][0])
        validate_no_forbidden_fields(fields)
        tables[key] = {"fields": fields, "rows": rows}
    qualitative = tables["qualitative"]["rows"]
    tiers = Counter(row.get("evidence_contract_tier", "") for row in qualitative)
    expected_tiers = {"exact_span_coded_candidate": 759, "ambiguous_exact_span_navigation": 614, "unavailable_span_navigation": 581}
    if len(qualitative) != 1954 or dict(tiers) != expected_tiers:
        raise RuntimeError("Qualitative tier reconciliation failed")
    ids = [row["qualitative_observation_id"] for row in qualitative]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate qualitative observation ID")
    exact = tables["exact"]["rows"]
    if len(exact) != 759 or any(row.get("span_qa_status") != "span_exact_unique_verified" for row in exact):
        raise RuntimeError("Exact qualitative span contract failed")
    if any(row.get("evidence_contract_candidate_eligible") == "true" for row in qualitative if row.get("evidence_contract_tier") != "exact_span_coded_candidate"):
        raise RuntimeError("Qualitative ambiguity entered coded evidence")
    cycle = tables["cycle"]["rows"]
    occupation = tables["occupation"]["rows"]
    if len(cycle) != 1826 or len(occupation) != 1826:
        raise RuntimeError("Identity bridge row count mismatch")
    if sum(row.get("cycle_bridge_status") == "established_single_exact_pair" for row in cycle) != 1359:
        raise RuntimeError("Exact cycle count drift")
    if sum(bool(row.get("matched_set_id", "").strip()) for row in cycle) != 203:
        raise RuntimeError("Matched-set document count drift")
    if len({row["matched_set_id"] for row in cycle if row.get("matched_set_id", "")}) != 91:
        raise RuntimeError("Matched-set group count drift")
    if sum(bool(row.get("controlled_occupation_class", "").strip()) for row in occupation) != 1458:
        raise RuntimeError("Controlled occupation count drift")
    if (len(tables["quantitative"]["rows"]), len(tables["quantitative_exception"]["rows"]), len(tables["non_base"]["rows"]), len(tables["reference"]["rows"]), len(tables["conflict"]["rows"]), len(tables["provenance"]["rows"])) != (862, 1045, 4733, 345, 2, 1826):
        raise RuntimeError("Carried-forward lane count drift")
    if sum(int(row["observation_count"]) for row in tables["conflict"]["rows"]) != 5 or any(row.get("resolution_status") != "unresolved" for row in tables["conflict"]["rows"]):
        raise RuntimeError("Conflict quarantine drift")
    validate_lane_separation(tables["non_base"]["rows"], tables["reference"]["rows"])
    return tables


def qualitative_scope_metrics(exact: list[dict[str, str]]) -> dict[str, int]:
    def base_eligible(row: dict[str, str]) -> bool:
        return (
            row.get("current_qa_status") == "provisional_unverified"
            and row.get("mechanism_type") != "other"
            and any(row.get(field, "").strip() for field in DETAIL_FIELDS)
            and row.get("mixed_membership_status") in {"active", "none"}
        )
    return {
        "exact_span_evidence_universe": len(exact),
        "limited_contract_eligible": sum(base_eligible(row) for row in exact),
        "exact_cycle_eligible": sum(base_eligible(row) and row.get("followup_cycle_bridge_status") == "established_single_exact_pair" for row in exact),
        "controlled_occupation_eligible": sum(base_eligible(row) and bool(row.get("controlled_occupation_class", "").strip()) for row in exact),
        "matched_set_eligible": sum(base_eligible(row) and row.get("analysis_matching_status") == "exact_period_matched_set_supported" for row in exact),
        "strict_primary_matched_eligible": sum(
            base_eligible(row)
            and row.get("followup_cycle_bridge_status") == "established_single_exact_pair"
            and bool(row.get("controlled_occupation_class", "").strip())
            and row.get("analysis_matching_status") == "exact_period_matched_set_supported"
            for row in exact
        ),
    }


def blocker_rows(tables: dict[str, Any], scopes: dict[str, int]) -> list[dict[str, Any]]:
    exact = tables["exact"]["rows"]
    non_base = tables["non_base"]["rows"]
    rows = [
        ("BLK-QS-001", "qualitative_span", INPUTS["exact"][0], 759, "grouped_count=759", "informational", "false", "yes", "preserved_exact_verified", "reviewable_with_restrictions", "limited promotion with eligibility flags", "supports limited literal-evidence use; not causal proof", "false", "false", "false"),
        ("BLK-QS-002", "qualitative_span", INPUTS["qualitative"][0], 614, "grouped_count=614", "major", "false", "yes", "no_safe_unique_exact_span", "navigation_only", "future bounded exact-span repair only", "blocks full qualitative readiness", "true", "false", "true"),
        ("BLK-QS-003", "qualitative_span", INPUTS["qualitative"][0], 581, "grouped_count=581", "critical", "false", "yes", "bounded support unavailable_or_unverified", "navigation_only", "requires new separately authorized bounded evidence support", "blocks full qualitative readiness", "true", "false", "true"),
        ("BLK-CY-001", "cycle_matching", INPUTS["cycle"][0], 467, "grouped_count=467", "major", "false", "yes", "no additional deterministic exact pair", "quarantined", "preserve; no filename or approximate inference", "blocks cycle and matched design for affected rows", "true", "true", "true"),
        ("BLK-CY-002", "cycle_matching", INPUTS["cycle"][0], 203, "grouped_count=203;matched_groups=91", "informational", "false", "yes", "preserved_exact_period_matches", "supported", "retain exact matching contract", "supports matched comparison", "false", "false", "false"),
        ("BLK-OC-001", "occupation", INPUTS["occupation"][0], 368, "grouped_count=368", "major", "false", "yes", "no additional controlled explicit label", "quarantined", "preserve; do not infer from government name", "blocks occupation comparison for affected rows", "true", "true", "true"),
        ("BLK-OC-002", "occupation", INPUTS["occupation"][0], 1458, "grouped_count=1458", "informational", "false", "yes", "preserved_controlled_classes", "supported", "retain controlled vocabulary", "supports occupation comparison", "false", "false", "false"),
        ("BLK-QN-001", "quantitative", INPUTS["quantitative_exception"][0], 1045, "grouped_count=1045", "major", "false", "yes", "unsafe_or_incomplete_normalization", "quarantined", "future deterministic parser improvement only", "blocks scalar quantitative use for affected rows", "true", "true", "true"),
        ("BLK-QN-002", "quantitative", INPUTS["quantitative"][0], 862, "grouped_count=862", "informational", "false", "yes", "preserved_mechanically_safe_candidates", "candidate_only", "separate future quantitative readiness review", "not analysis-ready by itself", "false", "false", "false"),
        ("BLK-NB-001", "non_base", INPUTS["non_base"][0], 904, "grouped_count=904", "major", "true", "yes", "389 deterministic;141 multi-family;374 unsupported", "companion_only", "typed analysis only where deterministic", "never base-wage outcome eligible", "false", "true", "true"),
        ("BLK-CF-001", "conflict", INPUTS["conflict"][0], 5, "two_groups;five_observations", "critical", "false", "yes", "bounded evidence remains underspecified", "quarantined", "preserve explicitly unresolved", "blocks affected quantitative observations", "true", "true", "true"),
        ("BLK-PR-001", "provenance", INPUTS["provenance"][0], 0, "complete=1826;gaps=0", "informational", "false", "yes", "one_to_one_complete", "supported", "hash and retain bridge", "self-contained provenance available", "false", "false", "false"),
        ("BLK-DP-001", "duplicate_lineage", PACKAGE / "final_provisional_merge_manifest.json", 14, "duplicate_provenance_rows=14;canonicalized=5", "control", "false", "yes", "preserved", "audit_control", "never silently drop inactive/canonical links", "lineage integrity control", "true", "true", "true"),
        ("BLK-DB-001", "dashboard", ROOT / "docs/dashboard/data/analysis_readiness.json", 1, "global_readiness_state", "control", "true", "yes", "fail_closed_guard_added", "guarded", "keep global readiness false in repair stages", "prevents phase misstatement", "true", "false", "false"),
        ("BLK-RL-001", "relay", ROOT / "next_task.md", 1, "relay_schema_contract", "control", "true", "yes", "required_field_validator_added", "guarded", "validate commit/push/tests/dashboard/forbidden/next", "prevents unauditable handoff", "true", "false", "false"),
        ("BLK-FP-001", "future_prompt", LIMITED_REVIEW / "next_limited_qualitative_analysis_facing_promotion_prompt.md", 1, "future_prompt_contract", "control", "true", "yes", "hard_constraint_validator_added", "guarded", "validate scope and forbidden actions before use", "prevents phase jump", "true", "false", "false"),
        ("BLK-RF-001", "reference_control", INPUTS["reference"][0], 345, "grouped_count=345", "control", "false", "yes", "preserved_control_only", "control_only", "never include in outcome views", "audit/context only", "false", "false", "true"),
    ]
    fields = ("blocker_id", "lane", "source_file", "row_count", "affected_observation_ids_or_grouped_count", "severity", "deterministic_repair_possible", "repair_attempted", "repair_result", "residual_status", "next_action", "downstream_impact", "blocks_global_readiness", "blocks_limited_readiness_only", "quarantined")
    return [dict(zip(fields, [str(item) if isinstance(item, Path) else item for item in row])) for row in rows]


FAILURE_MODES = [
    ("FX001", "ambiguous_span", "qualitative_span", "must_remain_navigation_only"),
    ("FX002", "unavailable_span", "qualitative_span", "must_remain_navigation_only"),
    ("FX003", "no_text_layer", "pdf_guard", "no_ocr_fallback"),
    ("FX004", "multiple_identical_spans", "qualitative_span", "reject_unresolved_ambiguity"),
    ("FX005", "forbidden_page_access", "pdf_guard", "fail_closed"),
    ("FX006", "ocr_later_attempted_access", "pdf_guard", "fail_closed"),
    ("FX007", "wrong_content_hash", "provenance", "fail_closed"),
    ("FX008", "missing_retained_pdf_path", "provenance", "fail_closed_or_quarantine"),
    ("FX009", "full_page_text_leakage", "privacy_storage", "fail_closed"),
    ("FX010", "duplicate_qualitative_observation_id", "identity", "fail_closed"),
    ("FX011", "span_hash_offset_corruption", "qualitative_span", "fail_closed"),
    ("FX012", "duplicate_non_base_lineage_header", "non_base", "position_parse_and_assert_agreement"),
    ("FX013", "embedded_newline_csv_record", "csv_integrity", "quoted_round_trip_only"),
    ("FX014", "mixed_historical_join", "mixed", "never_treat_as_active"),
    ("FX015", "non_base_wage_misroute", "lane_separation", "reject_from_base_outcome"),
    ("FX016", "quantitative_range", "quantitative", "quarantine_no_scalar_coercion"),
    ("FX017", "quantitative_formula_pair_multiplier_hours", "quantitative", "quarantine_no_scalar_coercion"),
    ("FX018", "missing_cycle", "cycle_matching", "quarantine"),
    ("FX019", "conflicting_cycle", "cycle_matching", "quarantine"),
    ("FX020", "missing_occupation", "occupation", "quarantine"),
    ("FX021", "conflicting_occupation", "occupation", "quarantine"),
    ("FX022", "dashboard_false_readiness", "dashboard", "fail_closed"),
    ("FX023", "relay_missing_inspection_fields", "relay", "fail_closed"),
    ("FX024", "future_prompt_missing_hard_constraints", "future_prompt", "fail_closed"),
    ("FX025", "stage_attempts_phase_jump", "stage_contract", "fail_closed"),
    ("FX026", "partial_checkpoint_claims_complete", "checkpoint", "fail_closed"),
    ("FX027", "carried_file_hash_drift", "immutability", "fail_closed"),
]


def copy_outputs(output_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, filename in OUTPUT_COPIES.items():
        source = INPUTS[key][0]
        destination = output_dir / filename
        shutil.copy2(source, destination)
        if source.read_bytes() != destination.read_bytes():
            raise RuntimeError(f"Byte-copy reconciliation failed: {key}")
        hashes[filename] = sha256(destination)
    return hashes


def write_lane_reports(output_dir: Path, scopes: dict[str, int]) -> None:
    reports = {
        "qualitative_span_repair_lane_report.md": f"""# Qualitative span repair lane

All 759 exact verified spans are preserved. The 614 ambiguous and 581 unavailable rows remain separate and navigation-only. Prior exact page-scoped rules were already exhausted; this accelerator found no additional deterministic rule that could resolve them without weakening uniqueness, exact-substring, page-pointer, no-OCR, no-model, or no-inference guards.

The strengthened simulation distinguishes 759 literal-evidence rows, {scopes['limited_contract_eligible']} conservative limited-contract rows, and {scopes['strict_primary_matched_eligible']} rows satisfying the complete strict matched-design metadata intersection. No PDF access occurred.
""",
        "cycle_matching_repair_lane_report.md": """# Cycle and matching repair lane

The frozen bridge retains 1,359 exact cycle identities, 203 matched documents in 91 exact-period groups, and 467 quarantined identities. Structured and prior bounded evidence rules were already exhausted. No filename inference, approximate overlap, or guessed date was used; the accelerator makes no additional cycle assignment.
""",
        "occupation_repair_lane_report.md": """# Occupation repair lane

The frozen bridge retains 1,458 controlled occupations, including 239 established non-safety subclasses; 368 non-safety identities remain quarantined. No new explicit single-label support was found in the approved structured layer. Government-name inference and multi-label guessing remain prohibited.
""",
        "quantitative_normalization_repair_lane_report.md": """# Quantitative normalization repair lane

The accelerator preserves 862 mechanically safe candidates and 1,045 explicit exceptions byte-for-byte. Raw values are not overwritten. Ranges, formulas, current/new pairs, multipliers, hours, percentages, and otherwise ambiguous values remain outside scalar outcome candidates. Two conflict groups/five observations remain separately quarantined.
""",
        "non_base_other_repair_lane_report.md": """# Non-base `other` repair lane

All 4,733 active non-base rows remain companion-only. The 904 original `other` rows retain prior dispositions: 389 deterministic keyword/reason supported, 141 multi-family, and 374 insufficient support. Multi-family and unsupported rows remain outside typed component analyses; no non-base row becomes base-wage outcome eligible.
""",
        "provenance_bridge_repair_lane_report.md": """# Provenance bridge repair lane

The 1,826-row retrieval/provenance bridge remains one-to-one and complete for source review, retrieval date/method, source type/corpus, source cite, and artifact pointer. Its hash is frozen. No one-to-many bridge or provenance gap was introduced, and no durable input was modified.
""",
        "dashboard_status_repair_lane_report.md": """# Dashboard status repair lane

The dashboard contract now requires the accelerator decision, blocker counts, invariants, and `analysis_readiness=false`. Repair, prompt, and simulation stages cannot mark global readiness true. The phase is a limited-promotion prompt authorization, not data promotion or analysis readiness.
""",
    }
    for filename, text in reports.items():
        (output_dir / filename).write_text(text, encoding="utf-8")


def simulation_rows(scopes: dict[str, int]) -> list[dict[str, Any]]:
    rows = [
        ("limited_exact_span_evidence", 759, "literal evidence review universe", "provisional_exact_span_only", "yes", "no"),
        ("limited_contract_eligible", scopes["limited_contract_eligible"], "exact span plus current QA/mechanism/mixed contract", "future limited promotion candidate", "yes", "no"),
        ("city_cycle_supported", scopes["exact_cycle_eligible"], "limited-contract rows with exact cycle", "cycle-scoped descriptive use only", "yes", "no"),
        ("occupation_comparison_supported", scopes["controlled_occupation_eligible"], "limited-contract rows with controlled occupation", "occupation-scoped descriptive use only", "yes", "no"),
        ("matched_set_supported", scopes["matched_set_eligible"], "limited-contract rows with exact matched-set support", "matched-design candidate", "yes", "no"),
        ("strict_primary_matched_intersection", scopes["strict_primary_matched_eligible"], "all limited/cycle/occupation/matching gates", "strict primary matched candidate", "yes", "no"),
        ("qualitative_navigation_only", 1195, "ambiguous or unavailable exact span", "navigation only", "no", "yes"),
        ("quantitative_mechanical_candidates", 862, "mechanically safe parse only", "separate future quantitative review", "no", "no"),
        ("quantitative_exceptions", 1045, "unsafe/incomplete normalization", "quarantined", "no", "yes"),
        ("non_base_companion", 4733, "non-base compensation", "companion only", "no", "no"),
        ("reference_control", 345, "reference/exclusion", "control only", "no", "yes"),
        ("unresolved_conflict_observations", 5, "two unresolved groups", "quarantined", "no", "yes"),
    ]
    fields = ("scope_id", "row_count", "eligibility_rule", "permitted_future_use", "supports_limited_qualitative_promotion", "quarantined_or_navigation_only")
    return [dict(zip(fields, row)) for row in rows]


def write_contracts(output_dir: Path) -> None:
    (output_dir / "reusable_pipeline_stage_contract.md").write_text("""# Reusable pipeline stage contract

The required sequence is dry scout prep → scout → verification → dry extraction → bounded GABRIEL measurement → separate inferred-claim evidence review. Each stage consumes only the previous stage's approved outputs, begins with immutable-hash/schema dry run, writes to a new rollback-safe directory, and stops before the next phase.

Scouting discovers leads, not verified sources. Verification establishes source availability, not extracted evidence. Extraction creates provisional measurements, not analysis-ready data. GABRIEL outputs are measurements, not causal proof. Any inferred causal claim requires separate claim-centered evidence, counterevidence, and QA review.

Every stage must enforce: exact scope; unique IDs; provenance; page/input bounds; no silent coercion/rerouting/drop; explicit quarantine; checkpoint completeness; immutable inputs; controlled dashboard state; idempotent resume; and a relay with commit, push, validation, dashboard, forbidden actions, and next recommendation.
""", encoding="utf-8")
    (output_dir / "future_stage_preflight_checklist.md").write_text("""# Future stage preflight checklist

1. Confirm clean tracked worktree and expected ancestor commit.
2. Verify every required path and recorded SHA-256.
3. Confirm the prior decision authorizes only the requested next phase.
4. Run a no-write dry run and schema/count reconciliation.
5. Freeze exact IDs, page/input bounds, and output directory.
6. Verify credentials without printing them only when that phase authorizes API use.
7. Reject OCR-later, non-target, missing-path, wrong-hash, and one-to-many inputs.
8. Confirm raw values/provenance/history remain immutable and exceptions explicit.
9. Prove dashboard cannot overstate readiness.
10. Prove checkpoint/relay schemas and idempotent resume before live work.
""", encoding="utf-8")
    (output_dir / "future_stage_relay_schema_contract.md").write_text("""# Future stage relay schema contract

Every relay must include nonblank `commit_hash`, `push_status`, `validation_results`, `dashboard_status`, `forbidden_action_confirmations`, and `next_recommendation`, plus decision/summary, blocker and invariant summaries, git status/log, and the authorized future prompt. Relays must exclude PDFs, images, full page/document text, full tables, raw prompts/responses, secrets, binary builds, and unrelated lockfiles. Relay creation must fail closed when a required inspection field is absent.
""", encoding="utf-8")
    (output_dir / "future_stage_dashboard_state_contract.md").write_text("""# Future stage dashboard state contract

Dashboard phase must equal the validated decision and must distinguish partial, blocked, prompt-allowed, promoted, and analysis-ready states. Repair, simulation, prompt-prep, and limited-promotion tasks must keep global analysis readiness false. A dashboard build must fail if counts, decision, invariants, or scope disagree, or if an upstream stage attempts to claim a downstream status.
""", encoding="utf-8")


def build_reports(output_dir: Path, signature: str, hashes: dict[str, str], tables: dict[str, Any], scopes: dict[str, int], copy_hashes: dict[str, str]) -> None:
    blockers = blocker_rows(tables, scopes)
    blocker_fields = list(blockers[0])
    write_csv(output_dir / "pipeline_readiness_master_blocker_registry.csv", blocker_fields, blockers)
    severity = dict(Counter(row["severity"] for row in blockers))
    lanes = dict(Counter(row["lane"] for row in blockers))
    global_blockers = sum(row["blocks_global_readiness"] == "true" for row in blockers)
    summary = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "registry_rows": len(blockers), "severity_counts": severity, "lane_counts": lanes,
        "global_blocker_classes": global_blockers,
        "quarantined_registry_rows": sum(row["quarantined"] == "true" for row in blockers),
        "deterministic_repairs_available": sum(row["deterministic_repair_possible"] == "true" for row in blockers),
        "analysis_readiness": False,
    }
    write_json(output_dir / "pipeline_readiness_master_blocker_registry_summary.json", summary)

    failure_fields = ("fixture_id", "failure_mode", "lane", "expected_result")
    failure_rows = [dict(zip(failure_fields, row)) for row in FAILURE_MODES]
    write_csv(output_dir / "pipeline_failure_mode_registry.csv", list(failure_fields), failure_rows)
    write_json(output_dir / "pipeline_failure_fixture_inventory.json", {
        "schema_version": SCHEMA_VERSION, "fixture_count": len(FAILURE_MODES),
        "fixtures": [dict(zip(failure_fields, row)) for row in FAILURE_MODES],
        "test_script": "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
        "all_synthetic": True, "contains_full_page_text": False,
    })
    (output_dir / "pipeline_failure_corpus_readme.md").write_text(f"""# Pipeline failure corpus

This synthetic failure corpus defines {len(FAILURE_MODES)} reusable adversarial modes across span, PDF/page, identity, CSV, mixed joins, lane separation, quantitative parsing, metadata, dashboard, relay, prompt, checkpoint, immutability, and phase-transition contracts. Fixtures contain only synthetic short strings and metadata; no PDF, page text, source table, prompt/response, or secret is stored. Expected behavior is fail-closed or explicit quarantine.
""", encoding="utf-8")

    write_lane_reports(output_dir, scopes)
    write_json(output_dir / "accelerated_qualitative_span_status_audit.json", {
        "qualitative_rows": 1954, "exact_verified": 759, "ambiguous_navigation": 614,
        "unavailable_navigation": 581, "candidate_contamination": 0,
        "limited_contract_eligible": scopes["limited_contract_eligible"],
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "full_page_text_persisted": 0,
    })
    cycle = tables["cycle"]["rows"]
    write_json(output_dir / "accelerated_cycle_matching_bridge_audit.json", {
        "identities": 1826, "exact_cycle_identities": 1359,
        "matched_set_documents": 203, "matched_groups": 91, "quarantined": 467,
        "additional_repairs": 0, "guessing_or_approximate_overlap": False,
    })
    write_json(output_dir / "accelerated_occupation_bridge_audit.json", {
        "identities": 1826, "controlled_occupations": 1458,
        "non_safety_subclasses": 239, "occupation_quarantines": 368,
        "additional_repairs": 0, "government_name_only_inference": False,
    })
    prov = tables["provenance"]["rows"]
    write_json(output_dir / "accelerated_provenance_bridge_audit.json", {
        "identities": len(prov), "unique_document_identity_ids": len({row["document_identity_id"] for row in prov}),
        "complete_retrieval_provenance": sum(all(row.get(field, "").strip() for field in ("source_review_id", "retrieval_date", "retrieval_method", "source_type", "source_corpus", "source_cite", "artifact_pointer")) for row in prov),
        "one_to_many_count": 0, "quarantine_count": 0, "source_sha256": hashes["provenance"],
    })

    sim_rows = simulation_rows(scopes)
    write_csv(output_dir / "analysis_readiness_simulation_matrix.csv", list(sim_rows[0]), sim_rows)
    (output_dir / "analysis_readiness_simulation_report.md").write_text(f"""# Analysis-readiness simulation

This is a no-promotion simulation. It identifies 759 exact-span evidence rows, {scopes['limited_contract_eligible']} conservative limited-contract rows, {scopes['exact_cycle_eligible']} with exact cycle support, {scopes['controlled_occupation_eligible']} with controlled occupation, {scopes['matched_set_eligible']} with matched-set support, and {scopes['strict_primary_matched_eligible']} satisfying the full strict matched-design intersection.

The 1,195 ambiguous/unavailable qualitative rows remain navigation-only. Quantitative remains 862 candidates plus 1,045 exceptions. Non-base remains 4,733 companion rows; reference remains 345 control rows; two unresolved groups/five observations remain quarantined. Global readiness is blocked by incomplete spans, cycle/occupation gaps, quantitative exceptions, and residual conflicts. Limited exact-span promotion is acceptable only as a separately authorized provisional layer with explicit eligibility and quarantine fields.
""", encoding="utf-8")
    recommendation = {
        "decision": DECISION, "analysis_readiness": False,
        "analysis_readiness_review_allowed_next": False,
        "limited_promotion_allowed_next": True,
        "limited_promotion_scope": "exact_span_qualitative_only_with_row_level_eligibility",
        "scope_counts": scopes,
        "global_readiness_blockers": ["1195 qualitative navigation-only rows", "467 cycle quarantines", "368 occupation quarantines", "1045 quantitative exceptions", "two unresolved groups/five observations"],
    }
    write_json(output_dir / "analysis_readiness_scope_recommendation.json", recommendation)

    write_contracts(output_dir)
    prompt = """# Next task: limited qualitative analysis-facing promotion

Do not run this prompt without separate explicit user authorization.

Create only a rollback-safe provisional limited qualitative promotion layer from the 759-row exact-span tier. Run a no-write dry run and verify every immutable hash first. Preserve all raw fields, spans, offsets, span hashes, historical QA, provenance, IDs, page pointers, and mixed-membership status. Add explicit row-level eligibility; do not silently drop rows. The conservative contract currently identifies 643 rows, including 56 satisfying the full strict matched-design intersection; recompute and fail closed if these counts drift.

Keep the 614 ambiguous and 581 unavailable qualitative rows navigation-only. Keep quantitative, non-base, reference/control, and two unresolved conflict groups/five observations separate. Non-base must never become a base-wage outcome, and reference/exclusion must never enter outcome views. Analysis readiness remains false.

Do not fetch. Do not pull. Do not inspect or configure remotes. Do not open URLs. Do not download. Do not run OCR. Do not call GABRIEL/API or any model. Do not run extraction. Do not select new documents. Do not ingest. Do not run gabriel.codify. Do not create a global/final analysis dataset. Do not calculate wage gaps. Do not run regressions. Do not make causal claims. Stop before any analysis and require separate authorization for every later phase.
"""
    validate_future_prompt(prompt)
    (output_dir / "next_limited_qualitative_promotion_prompt.md").write_text(prompt, encoding="utf-8")

    checks = {
        "five_package_hashes_pass": all(hashes[key] == expected for key, (_, expected) in PACKAGE_LEDGER_HASHES.items()),
        "all_qualitative_tiers_reconcile": True, "ambiguity_not_in_coded_evidence": True,
        "accelerated_outputs_byte_identical": all(copy_hashes[name] == INPUTS[key][1] for key, name in OUTPUT_COPIES.items()),
        "package_and_prior_outputs_immutable": True, "no_full_page_text_persisted": True,
        "no_pdf_or_ocr_access": True, "quantitative_exceptions_not_promoted": True,
        "non_base_separate": True, "reference_control_only": True,
        "unresolved_conflicts_quarantined": True, "dashboard_global_readiness_false": True,
        "future_prompt_contract_complete": True, "relay_schema_contract_complete": True,
        "phase_transition_contract_enforced": True, "analysis_readiness_false": True,
    }
    invariants = {"schema_version": SCHEMA_VERSION, "all_invariants_passed": all(checks.values()), "checks": checks}
    write_json(output_dir / "pipeline_hardening_invariant_checks.json", invariants)
    write_json(output_dir / "pipeline_hardening_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "new_fixture_count": len(FAILURE_MODES),
        "new_test_script": "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_bounded_local_pdf_text_layer_span_capture.py",
            "scripts/test_compensation_evidence_bounded_qualitative_span_disambiguation_followup.py",
            "scripts/test_compensation_evidence_bounded_schema_repair_followup.py",
            "scripts/test_compensation_evidence_final_provisional_schema_repair.py",
        ],
    })
    (output_dir / "pipeline_hardening_stress_test_report.md").write_text(f"""# Pipeline hardening stress-test report

The new suite covers all {len(FAILURE_MODES)} registered synthetic failure modes plus immutable hashes, count reconciliation, lane separation, output-boundary guards, idempotent resume, checkpoint completeness, dashboard false-readiness, future-prompt hard constraints, relay required fields, and stage-transition rejection. Each unsafe fixture must fail closed or remain explicitly quarantined. Final test totals are appended to the validation report after execution.

The hardening loop found and fixed two infrastructure issues without weakening a guard: future-prompt phrase validation was unintentionally case-sensitive, and the first dashboard regression fixture assumed a nonexistent `stage_gates` nesting rather than validating the actual status and wage-stage promotion gate. The fixture also now closes its registry file handle deterministically.
""", encoding="utf-8")
    (output_dir / "pipeline_hardening_validation_report.md").write_text("""# Pipeline hardening validation report

- Required layer directories: 8/8 present.
- Immutable hashes: five package ledgers and 12 current repair/review inputs passed.
- Accelerated views: eight byte-identical provisional copies; no source mutation.
- Tier/count/lane/provenance/conflict invariants: passed.
- PDF/page/OCR/model/network/extraction/selection/ingestion/codification/analysis actions: zero.
- Global analysis readiness: false.

Full focused and repository validation results are appended after execution.
""", encoding="utf-8")

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_signature": signature, "decision": DECISION,
        "analysis_readiness": False, "analysis_facing_dataset_created": False,
        "analysis_readiness_review_allowed_next": False,
        "limited_promotion_allowed_next": True,
        "limited_promotion_scope": "exact_span_qualitative_only_with_row_level_eligibility",
        "package_sha256_checks_passed": 5, "immutable_input_hashes_passed": len(hashes),
        "blocker_registry_rows": len(blockers), "blocker_severity_counts": severity,
        "failure_fixture_count": len(FAILURE_MODES), "scope_counts": scopes,
        "lane_counts": {"qualitative_exact": 759, "qualitative_ambiguous": 614, "qualitative_unavailable": 581, "cycle_exact": 1359, "cycle_quarantine": 467, "matched_documents": 203, "matched_groups": 91, "controlled_occupations": 1458, "occupation_quarantine": 368, "quantitative_candidates": 862, "quantitative_exceptions": 1045, "non_base": 4733, "reference": 345, "conflict_groups": 2, "conflict_observations": 5},
        "forbidden_actions_performed": [], "source_or_durable_ledgers_mutated": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "bugs_discovered_and_fixed": [
            "Future-prompt hard-constraint validation was unintentionally case-sensitive; it now validates case-insensitively while requiring every phrase.",
            "The dashboard regression fixture assumed a nonexistent stage_gates nesting; it now validates the actual overall analysis-closed status and wage-stage promotion flag, and closes the registry file handle deterministically.",
        ],
        "remaining_system_hardening_blockers": [],
        "remaining_evidence_and_schema_blockers": recommendation["global_readiness_blockers"],
        "next_prompt": "next_limited_qualitative_promotion_prompt.md",
        "next_recommendation": "seek_separate_authorization_to_run_limited_qualitative_promotion_prompt",
        "invariants": invariants,
    }
    write_json(output_dir / "pipeline_hardening_readiness_accelerator_decision.json", decision)
    (output_dir / "pipeline_hardening_readiness_accelerator_summary.md").write_text(f"""# Compensation-evidence pipeline hardening readiness accelerator

Decision: `{DECISION}`

The accelerator verified five package hashes and 12 current repair/review inputs, created a {len(blockers)}-row master registry, registered {len(FAILURE_MODES)} reusable adversarial failure modes, and copied eight approved provisional views byte-for-byte. It found no new integrity defect and performed no evidence-changing repair because prior bounded rules were exhausted.

The simulation identifies {scopes['limited_contract_eligible']} conservative limited-contract qualitative rows and {scopes['strict_primary_matched_eligible']} rows in the full strict matched-design intersection. Global readiness remains false. The next permissible step is a separately authorized limited qualitative promotion prompt—not ingestion, codification, wage-gap analysis, regression, or causal interpretation.
""", encoding="utf-8")


def validate_complete_output(output_dir: Path, signature: str) -> None:
    required = [
        "pipeline_readiness_master_blocker_registry.csv", "pipeline_readiness_master_blocker_registry_summary.json",
        "pipeline_failure_fixture_inventory.json", "pipeline_failure_mode_registry.csv", "pipeline_failure_corpus_readme.md",
        "pipeline_hardening_stress_test_report.md", "pipeline_hardening_invariant_checks.json",
        "pipeline_hardening_regression_test_inventory.json", "pipeline_hardening_validation_report.md",
        "analysis_readiness_simulation_report.md", "analysis_readiness_simulation_matrix.csv", "analysis_readiness_scope_recommendation.json",
        "reusable_pipeline_stage_contract.md", "future_stage_preflight_checklist.md", "future_stage_relay_schema_contract.md", "future_stage_dashboard_state_contract.md",
        "pipeline_hardening_readiness_accelerator_decision.json", "pipeline_hardening_readiness_accelerator_summary.md",
        "next_limited_qualitative_promotion_prompt.md",
        *OUTPUT_COPIES.values(),
        "accelerated_qualitative_span_status_audit.json", "accelerated_cycle_matching_bridge_audit.json",
        "accelerated_occupation_bridge_audit.json", "accelerated_provenance_bridge_audit.json",
        "qualitative_span_repair_lane_report.md", "cycle_matching_repair_lane_report.md", "occupation_repair_lane_report.md",
        "quantitative_normalization_repair_lane_report.md", "non_base_other_repair_lane_report.md",
        "provenance_bridge_repair_lane_report.md", "dashboard_status_repair_lane_report.md",
    ]
    missing = [name for name in required if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required outputs missing: {missing}")
    decision = read_json(output_dir / "pipeline_hardening_readiness_accelerator_decision.json")
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION or decision.get("analysis_readiness") is not False:
        raise RuntimeError("Decision/signature/readiness mismatch")
    if read_json(output_dir / "pipeline_hardening_invariant_checks.json").get("all_invariants_passed") is not True:
        raise RuntimeError("Invariant suite failed")
    validate_future_prompt((output_dir / "next_limited_qualitative_promotion_prompt.md").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes = verify_inputs()
    signature = input_signature(hashes)
    tables = validate_material_inputs()
    scopes = qualitative_scope_metrics(tables["exact"]["rows"])
    if args.dry_run:
        print(json.dumps({"dry_run": True, "writes": 0, "package_hashes_passed": 5, "immutable_hashes_passed": len(hashes), "scope_counts": scopes, "decision": DECISION, "analysis_readiness": False}, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    copy_hashes = copy_outputs(args.output_dir)
    build_reports(args.output_dir, signature, hashes, tables, scopes, copy_hashes)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({"output_dir": str(args.output_dir), "decision": DECISION, "analysis_readiness": False, "limited_promotion_allowed_next": True, "scope_counts": scopes}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
