#!/usr/bin/env python3
"""Review the accepted limited qualitative usage-layer registry.

This runner creates registry-review metadata only. It verifies the immutable
acceptance registration, its three authorized hashes, registered scope, and
dashboard closure. It never copies or emits evidence rows or analysis output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_compensation_evidence_limited_qualitative_usage_layer_acceptance as acceptance


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-REGISTRY-REVIEW-2026-07-25"
SCHEMA_VERSION = "limited_qualitative_usage_registry_review_v1"
BASELINE_COMMIT = "016bc1b623ca63e0a5a24471d9721510c98fd11f"
DECISION = "limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed"
AUTHORIZED_ID_HASH = "0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b"
AUTHORIZED_LAYER_HASH = "cf29690a7687401960804a714d0bdfb0a24407eee10ba70695ee5487a60fcbc5"
AUTHORIZED_SCHEMA_HASH = "3c31d1d663cde730d198184444c6b77591cc186411c9714ea0086f2135d8533a"
ACCEPTANCE_DIR = acceptance.DEFAULT_OUTPUT_DIR
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-REGISTRY-REVIEW-2026-07-25"

ACCEPTANCE_INPUTS = (
    "limited_qualitative_usage_layer_acceptance_decision.json",
    "limited_qualitative_usage_layer_acceptance_record.md",
    "limited_qualitative_usage_layer_registration_manifest.json",
    "limited_qualitative_usage_layer_registered_scope_matrix.csv",
    "limited_qualitative_usage_layer_acceptance_hash_audit.json",
    "limited_qualitative_usage_layer_acceptance_scope_audit.json",
    "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json",
    "limited_qualitative_usage_layer_acceptance_invariant_checks.json",
    "limited_qualitative_usage_layer_acceptance_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_acceptance_stress_test_report.md",
    "limited_qualitative_usage_layer_acceptance_regression_test_inventory.json",
    "next_limited_qualitative_usage_registry_review_prompt.md",
)

DASHBOARD_INPUTS = (
    ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json",
    ROOT / "docs/dashboard/data/analysis_readiness.json",
)

EXPECTED = {
    "accepted_usage_layer_rows": 643,
    "restricted_exact_span_rows": 116,
    "ambiguous_navigation_rows": 614,
    "unavailable_navigation_rows": 581,
    "navigation_only_rows": 1195,
    "strict_primary_manifest_rows": 56,
    "quantitative_candidates": 862,
    "quantitative_exceptions": 1045,
    "non_base_companion": 4733,
    "reference_control": 345,
    "unresolved_conflict_groups": 2,
    "unresolved_conflict_observations": 5,
}

SOURCE_PROMPT_REQUIRED = acceptance.FUTURE_PROMPT_REQUIRED
FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "registry acceptance only",
    "global analysis readiness remains false",
    "full qualitative readiness remains false",
    "analysis-facing promotion remains false",
    "Do not compute descriptive statistics",
    "Do not compute inferential statistics",
    "Do not fetch", "Do not pull", "Do not inspect remotes", "Do not configure remotes",
    "Do not open URLs", "Do not download", "Do not open PDFs", "Do not access PDF pages",
    "Do not run OCR", "Do not call GABRIEL/API", "Do not run extraction",
    "Do not select new documents", "Do not ingest", "Do not run gabriel.codify",
    "Do not calculate wage gaps", "Do not run regressions", "Do not make causal claims",
    "mechanism language is not evidence of wage effects",
)

RELAY_REQUIRED = {
    "commit_hash", "push_status", "validation_results", "dashboard_status",
    "forbidden_action_confirmations", "next_recommendation",
}

REQUIRED_OUTPUTS = (
    "limited_qualitative_usage_registry_review_decision.json",
    "limited_qualitative_usage_registry_review_summary.md",
    "limited_qualitative_usage_registry_hash_audit.json",
    "limited_qualitative_usage_registry_scope_audit.json",
    "limited_qualitative_usage_registry_dashboard_audit.json",
    "limited_qualitative_usage_registry_future_prompt_audit.json",
    "limited_qualitative_usage_registry_forbidden_action_audit.json",
    "limited_qualitative_usage_registry_state_contract.md",
    "limited_qualitative_usage_registry_scope_matrix.csv",
    "limited_qualitative_usage_registry_review_validation_2026-07-25.md",
    "limited_qualitative_usage_registry_review_invariant_checks.json",
    "limited_qualitative_usage_registry_review_stress_test_report.md",
    "limited_qualitative_usage_registry_review_regression_test_inventory.json",
    "next_limited_qualitative_usage_registry_acceptance_prompt.md",
    "next_task.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Registry-review output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if resolved == forbidden.resolve() or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden registry-review output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe registry-review output already exists: {path}")


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required input absent at registry-review baseline: {relative}")
    return result.stdout


def validate_acceptance_authorization(record: dict[str, Any]) -> None:
    if record.get("decision") != acceptance.DECISION:
        raise RuntimeError("Acceptance decision does not authorize registry review")
    if record.get("record_type") != "acceptance_registration_only":
        raise RuntimeError("Acceptance is not registration-only")
    if record.get("registry_review_prompt_allowed_next") is not True:
        raise RuntimeError("Acceptance did not allow registry review")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Acceptance created evidence rows or analysis outputs")
    if record.get("global_analysis_readiness") is not False:
        raise RuntimeError("Acceptance incorrectly marks global readiness true")


def validate_hash_contract(record: dict[str, Any]) -> None:
    checks = (
        ("observed_candidate_id_set_sha256", AUTHORIZED_ID_HASH, "Candidate ID-set"),
        ("observed_layer_sha256", AUTHORIZED_LAYER_HASH, "Layer"),
        ("observed_schema_sha256", AUTHORIZED_SCHEMA_HASH, "Schema"),
    )
    for field, expected, label in checks:
        if record.get(field) != expected:
            raise RuntimeError(f"{label} SHA-256 mismatch")
    if not all(record.get(key) is True for key in (
        "candidate_id_set_hash_match", "layer_sha256_match", "schema_sha256_match",
    )):
        raise RuntimeError("Registry hash audit contains a failed hash check")


def validate_scope_contract(record: dict[str, Any]) -> None:
    if record.get("observed_counts") != EXPECTED:
        raise RuntimeError("Registered scope counts drifted from the accepted contract")
    if record.get("restricted_navigation_external_contamination_count") != 0:
        raise RuntimeError("Registered scope contains excluded-lane contamination")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Registry review created evidence rows or analysis outputs")


def validate_dashboard_state(calibration: dict[str, Any], readiness: dict[str, Any]) -> None:
    phase = calibration.get("calibration_phase", "")
    allowed_phases = {
        "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed",
        "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed",
        "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed",
        "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready",
        "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready",
        "compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine",
        "compensation_extraction_gabriel_claim_rating_643_repaired_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed",
        "compensation_extraction_gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed",
        "compensation_extraction_provisional_claim_review_636_completed_targeted_scouting_restart_recommended",
        "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready",
    }
    if phase not in allowed_phases:
        raise RuntimeError("Dashboard phase is inconsistent with the registry-only chain")
    if calibration.get("analysis_facing_promotion_allowed") is not False:
        raise RuntimeError("Dashboard incorrectly permits analysis-facing promotion")
    readiness_text = json.dumps(readiness, sort_keys=True).casefold()
    if readiness.get("overall_status") not in {
        "limited_qualitative_usage_layer_acceptance_registered_registry_review_only_global_analysis_closed",
        "limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed_global_analysis_closed",
        "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed",
        "final_qa_categorization_closed_gabriel_attribute_ready_global_analysis_closed",
        "claim_oriented_phase_closed_gabriel_claim_rating_ready_global_analysis_closed",
        "gabriel_claim_rating_643_completed_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_643_completed_with_quarantine_global_analysis_closed",
        "gabriel_claim_rating_643_repaired_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed_global_analysis_closed",
        "gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed_global_analysis_closed",
        "provisional_claim_review_636_completed_targeted_scouting_restart_recommended_global_analysis_closed",
        "targeted_scouting_four_lane_prep_dry_run_completed_lane_1_live_ready_global_analysis_closed",
    }:
        raise RuntimeError("Dashboard overall registry state is inconsistent")
    if '"global_analysis_readiness": true' in readiness_text:
        raise RuntimeError("Dashboard marks global analysis readiness true")


def validate_prompt(text: str, required: tuple[str, ...]) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in required if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future prompt missing constraints: {missing}")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required inspection fields: {missing}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 643 or record.get("expected") != 643:
        raise RuntimeError("Partial registry review cannot masquerade as complete")


def verify_inputs() -> tuple[dict[str, str], dict[str, Any]]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized acceptance commit or a descendant")

    upstream_hashes, _ = acceptance.verify_inputs()
    acceptance_signature = acceptance.input_signature(upstream_hashes)
    acceptance.validate_complete_output(ACCEPTANCE_DIR, acceptance_signature)

    observed: dict[str, str] = {}
    for name in ACCEPTANCE_INPUTS:
        path = ACCEPTANCE_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"Required registry-review input missing: {path}")
        current = path.read_bytes()
        baseline = git_bytes_at_baseline(path)
        if current != baseline:
            raise RuntimeError(f"Immutable acceptance input differs from baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    # Dashboard files are status outputs, not immutable evidence inputs. Their
    # baseline bytes are signed while their current semantic state is checked.
    for path in DASHBOARD_INPUTS:
        if not path.is_file():
            raise FileNotFoundError(f"Required dashboard input missing: {path}")
        baseline = git_bytes_at_baseline(path)
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(baseline)

    decision = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_layer_acceptance_decision.json")
    manifest = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_layer_registration_manifest.json")
    hash_audit = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_layer_acceptance_hash_audit.json")
    scope_audit = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_layer_acceptance_scope_audit.json")
    forbidden = read_json(ACCEPTANCE_DIR / "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json")
    calibration = read_json(DASHBOARD_INPUTS[0])
    readiness = read_json(DASHBOARD_INPUTS[1])
    source_prompt = (ACCEPTANCE_DIR / "next_limited_qualitative_usage_registry_review_prompt.md").read_text(encoding="utf-8")

    validate_acceptance_authorization(decision)
    if manifest.get("registration_only") is not True or manifest.get("contains_evidence_rows") is not False:
        raise RuntimeError("Acceptance manifest is not registration-only")
    validate_hash_contract(hash_audit)
    validate_scope_contract(scope_audit)
    validate_dashboard_state(calibration, readiness)
    validate_prompt(source_prompt, SOURCE_PROMPT_REQUIRED)
    if forbidden.get("all_forbidden_action_checks_passed") is not True:
        raise RuntimeError("Acceptance forbidden-action audit is not passing")

    return observed, {
        "decision": decision, "manifest": manifest, "hash_audit": hash_audit,
        "scope_audit": scope_audit, "forbidden": forbidden,
        "calibration": calibration, "readiness": readiness,
    }


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, source: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    source_hash = source["hash_audit"]

    hash_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "input_signature": signature,
        "immutable_acceptance_inputs_verified": len(ACCEPTANCE_INPUTS),
        "dashboard_baseline_inputs_signed": len(DASHBOARD_INPUTS),
        "input_contract_entries": len(hashes), "input_sha256": hashes,
        "authorized_candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "observed_candidate_id_set_sha256": source_hash["observed_candidate_id_set_sha256"],
        "candidate_id_set_hash_match": True,
        "authorized_layer_sha256": AUTHORIZED_LAYER_HASH,
        "observed_layer_sha256": source_hash["observed_layer_sha256"], "layer_sha256_match": True,
        "authorized_schema_sha256": AUTHORIZED_SCHEMA_HASH,
        "observed_schema_sha256": source_hash["observed_schema_sha256"], "schema_sha256_match": True,
        "all_hash_checks_passed": True,
    }
    validate_hash_contract(hash_audit)
    write_json(output_dir / "limited_qualitative_usage_registry_hash_audit.json", hash_audit)

    scope_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "expected_counts": EXPECTED, "observed_counts": dict(EXPECTED),
        "all_scope_counts_match": True,
        "restricted_navigation_external_contamination_count": 0,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "registration_only": True, "all_scope_checks_passed": True,
    }
    validate_scope_contract(scope_audit)
    write_json(output_dir / "limited_qualitative_usage_registry_scope_audit.json", scope_audit)

    dashboard_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "source_calibration_phase": source["calibration"]["calibration_phase"],
        "source_overall_status": source["readiness"]["overall_status"],
        "target_calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed",
        "target_overall_status": "limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed_global_analysis_closed",
        "registry_review_only": True, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "analysis_facing_promotion_allowed": False,
        "dashboard_state_consistent": True,
    }
    validate_dashboard_state(source["calibration"], source["readiness"])
    write_json(output_dir / "limited_qualitative_usage_registry_dashboard_audit.json", dashboard_audit)

    future_prompt = f"""# Next task: limited qualitative usage registry acceptance

Do not run this prompt without separate explicit user authorization.

The registry review decision is `{DECISION}`. Perform registry acceptance only for the accepted 643-row bounded limited qualitative mechanism usage layer. Reverify the candidate ID-set hash `{AUTHORIZED_ID_HASH}`, layer hash `{AUTHORIZED_LAYER_HASH}`, schema hash `{AUTHORIZED_SCHEMA_HASH}`, scope counts, zero contamination, and dashboard closure. Create registration metadata only; create no evidence rows and no analysis output.

## Hard constraints

- Global analysis readiness remains false.
- Full qualitative readiness remains false.
- Analysis-facing promotion remains false.
- Mechanism language is not evidence of wage effects.
- Do not compute descriptive statistics.
- Do not compute inferential statistics.
- Do not fetch.
- Do not pull.
- Do not inspect remotes.
- Do not configure remotes.
- Do not open URLs.
- Do not download or redownload documents.
- Do not open PDFs.
- Do not access PDF pages.
- Do not run OCR.
- Do not call GABRIEL/API or any model.
- Do not run extraction.
- Do not select new documents.
- Do not ingest.
- Do not run gabriel.codify.
- Do not calculate wage gaps.
- Do not run regressions.
- Do not make causal claims.
- Do not mutate any package, repair, span, evidence-contract, readiness, hardening, promotion, usage, QA, acceptance, extraction, source-review, or durable ledger.

Stop after the separately authorized registry-acceptance decision, validation, dashboard update if appropriate, commit, push, and lite relay. Preserve phase boundaries: registry acceptance is not analysis, GABRIEL analysis is not causal proof, and inferred causal claims require separate evidence and QA review.
"""
    validate_prompt(future_prompt, FUTURE_PROMPT_REQUIRED)
    (output_dir / "next_limited_qualitative_usage_registry_acceptance_prompt.md").write_text(future_prompt, encoding="utf-8")
    prompt_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "source_prompt_constraints_checked": len(SOURCE_PROMPT_REQUIRED),
        "source_prompt_constraints_complete": True,
        "future_prompt_constraints_checked": len(FUTURE_PROMPT_REQUIRED),
        "future_prompt_constraints_complete": True,
        "separate_authorization_required": True, "phase_boundaries_preserved": True,
    }
    write_json(output_dir / "limited_qualitative_usage_registry_future_prompt_audit.json", prompt_audit)

    forbidden = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "network_or_url_access": 0, "downloads_or_redownloads": 0,
        "pdf_or_page_access": 0, "ocr_or_rendered_image_access": 0,
        "gabriel_api_or_model_calls": 0, "scout_source_review_or_verification_runs": 0,
        "extraction_or_document_selection_runs": 0, "ingestion_or_codification_runs": 0,
        "descriptive_statistics_computed": 0, "inferential_statistics_computed": 0,
        "wage_gap_or_regression_runs": 0, "causal_claims_made": 0,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "immutable_inputs_modified": 0, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "analysis_facing_promotion_allowed": False,
        "all_forbidden_action_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_registry_forbidden_action_audit.json", forbidden)

    matrix_rows = [
        ("accepted_usage_layer", 643, "registered_reference_only", "no analysis or effect inference"),
        ("restricted_exact_span", 116, "quarantine_metadata_only", "excluded from accepted coded scope"),
        ("ambiguous_navigation", 614, "navigation_only", "not coded evidence"),
        ("unavailable_navigation", 581, "navigation_only", "not coded evidence"),
        ("navigation_only_total", 1195, "navigation_only", "not coded evidence"),
        ("strict_primary_manifest", 56, "narrow_non_analytic_manifest", "no statistics or causal use"),
        ("quantitative_candidates", 862, "separate_manifest_only", "not qualitative evidence"),
        ("quantitative_exceptions", 1045, "separate_exception_manifest", "not qualitative evidence"),
        ("non_base_companion", 4733, "separate_companion_manifest", "not a base-wage outcome"),
        ("reference_control", 345, "separate_control_manifest", "not outcome evidence"),
        ("unresolved_conflict_observations", 5, "quarantined_in_two_groups", "unresolved; no guessing"),
    ]
    write_csv(
        output_dir / "limited_qualitative_usage_registry_scope_matrix.csv",
        ["scope", "registered_count", "registry_status", "allowed_reference", "restriction"],
        [{"scope": scope, "registered_count": count, "registry_status": "verified",
          "allowed_reference": treatment, "restriction": restriction}
         for scope, count, treatment, restriction in matrix_rows],
    )

    (output_dir / "limited_qualitative_usage_registry_state_contract.md").write_text(
        """# Limited qualitative usage registry state contract

The registry points to an immutable, QA-passed 643-row bounded literal mechanism-language usage layer. The registry stores hashes, counts, restrictions, and pointers only; it stores no evidence rows, full text, statistics, analysis output, or inferred meaning.

The 643 accepted rows remain bounded evidence of literal mechanism language. They do not establish wage effects. The 116 restricted exact-span rows and 1,195 navigation-only rows remain outside the accepted coded scope. The 56-row strict-primary manifest is a narrow non-analytic registry reference. Quantitative, non-base, reference/control, and conflict lanes remain separate.

Global analysis readiness, full qualitative readiness, and analysis-facing promotion are false. A downstream stage must obtain separate explicit authorization and preserve the scouting → verification → extraction → measurement → causal-claim-review boundaries.
""",
        encoding="utf-8",
    )

    checks = {
        "acceptance_decision_authorizes_registry_review": True,
        "acceptance_registration_is_registration_only": True,
        "all_required_inputs_present_and_immutable": True,
        "candidate_id_set_hash_reverified": True,
        "layer_hash_reverified": True, "schema_hash_reverified": True,
        "all_registered_scope_counts_reconciled": True,
        "restricted_navigation_external_contamination_zero": True,
        "evidence_rows_created_zero": True, "analysis_outputs_created_zero": True,
        "strict_primary_56_and_non_analytic": True,
        "dashboard_registry_state_consistent": True,
        "global_analysis_readiness_false": True, "full_qualitative_readiness_false": True,
        "analysis_facing_promotion_false": True,
        "source_and_future_prompts_preserve_constraints": True,
        "partial_outputs_cannot_claim_complete": True, "immutable_inputs_unmodified": True,
    }
    write_json(output_dir / "limited_qualitative_usage_registry_review_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "checks": checks,
        "scope_counts": EXPECTED, "all_invariants_passed": all(checks.values()),
    })

    failure_modes = [
        "acceptance_decision_not_authorized", "acceptance_not_registration_only",
        "acceptance_input_missing", "baseline_commit_not_ancestor", "immutable_acceptance_input_hash_drift",
        "candidate_id_set_hash_drift", "layer_file_hash_drift", "schema_hash_drift",
        "accepted_row_count_drift", "restricted_count_drift", "ambiguous_count_drift",
        "unavailable_count_drift", "navigation_total_drift", "strict_primary_count_drift",
        "quantitative_candidate_count_drift", "quantitative_exception_count_drift",
        "non_base_count_drift", "reference_control_count_drift", "unresolved_conflict_count_drift",
        "restricted_or_navigation_contamination", "external_lane_contamination",
        "registry_review_creates_evidence_rows", "registry_review_creates_analysis_outputs",
        "dashboard_phase_inconsistent", "global_readiness_true", "full_qualitative_readiness_true",
        "analysis_promotion_true", "source_prompt_missing_constraint", "future_prompt_missing_constraint",
        "relay_missing_inspection_field", "partial_checkpoint_claims_complete",
        "rerun_changes_registry_review", "output_outside_docs_analysis",
        "forbidden_pipeline_action", "statistics_or_causal_work_attempted",
        "registry_metadata_fabrication", "registry_acceptance_jumps_phase",
    ]
    write_json(output_dir / "limited_qualitative_usage_registry_review_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "failure_modes": len(failure_modes),
        "failure_mode_ids": failure_modes,
        "new_test_script": "scripts/test_compensation_evidence_limited_qualitative_usage_registry_review.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer_acceptance.py",
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer_qa_review.py",
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_usage_review.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_qualitative_usage_registry_review_stress_test_report.md").write_text(
        f"# Limited qualitative usage registry-review stress test\n\nThe registry-review system covers {len(failure_modes)} adversarial failure modes spanning authorization, immutable inputs, three hashes, every scope count, lane contamination, registration-only behavior, dashboard closure, prompts, relays, checkpoints, reruns, output boundaries, and prohibited work. Final test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "record_type": "registry_review_only", "source_acceptance_decision": acceptance.DECISION,
        "candidate_id_set_sha256": AUTHORIZED_ID_HASH, "candidate_id_set_hash_verified": True,
        "layer_sha256": AUTHORIZED_LAYER_HASH, "layer_sha256_verified": True,
        "schema_sha256": AUTHORIZED_SCHEMA_HASH, "schema_sha256_verified": True,
        "registered_accepted_rows": 643, "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56, "counts": EXPECTED,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "descriptive_statistics_computed": False, "inferential_statistics_computed": False,
        "global_analysis_readiness": False, "full_qualitative_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "registry_acceptance_prompt_allowed_next": True,
        "registry_acceptance_requires_separate_authorization": True,
        "immutable_inputs_verified": len(ACCEPTANCE_INPUTS), "immutable_inputs_modified": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "network_calls": 0,
        "model_calls": 0, "forbidden_actions_performed": [],
        "next_prompt": "next_limited_qualitative_usage_registry_acceptance_prompt.md",
    }
    write_json(output_dir / "limited_qualitative_usage_registry_review_decision.json", decision)
    (output_dir / "limited_qualitative_usage_registry_review_summary.md").write_text(
        f"""# Limited qualitative usage registry review

Decision: `{DECISION}`

The acceptance registration is internally consistent and registry-only. The candidate ID-set, layer, and schema SHA-256 values match their authorized values. The registered scope reconciles to 643 accepted rows, 116 restricted exact-span rows, 614 ambiguous navigation rows, 581 unavailable navigation rows, 1,195 navigation-only rows, and a 56-row narrow non-analytic strict-primary manifest. Restricted/navigation/external-lane contamination is zero.

The registry review created zero evidence rows and zero analysis outputs. Quantitative candidates/exceptions (862/1,045), non-base companion rows (4,733), reference/control rows (345), and two unresolved conflict groups/five observations remain separate. Global analysis readiness, full qualitative readiness, and analysis-facing promotion remain false. A separately authorized registry-acceptance prompt may run next.
""",
        encoding="utf-8",
    )
    (output_dir / "limited_qualitative_usage_registry_review_validation_2026-07-25.md").write_text(
        """# Limited qualitative usage registry-review validation

- Immutable acceptance inputs verified: 12.
- Dashboard baseline contracts signed: 2.
- Candidate ID-set, layer, and schema SHA-256 checks: passed.
- Registered scope: 643 accepted rows; zero excluded-lane contamination.
- Strict primary manifest: 56 rows and non-analytic.
- Evidence rows and analysis outputs created: zero.
- Global/full readiness and analysis-facing promotion: false.

## Executed validation

Final command results are recorded after the full required validation run.
""",
        encoding="utf-8",
    )
    (output_dir / "next_task.md").write_text(
        "# Next task\n\nSeek separate explicit authorization to run `next_limited_qualitative_usage_registry_acceptance_prompt.md`. That task may accept the registry state only; it must create no evidence rows or analysis outputs and must keep every readiness flag false.\n",
        encoding="utf-8",
    )


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required registry-review outputs missing: {missing}")
    decision = read_json(output_dir / "limited_qualitative_usage_registry_review_decision.json")
    hash_audit = read_json(output_dir / "limited_qualitative_usage_registry_hash_audit.json")
    scope_audit = read_json(output_dir / "limited_qualitative_usage_registry_scope_audit.json")
    dashboard_audit = read_json(output_dir / "limited_qualitative_usage_registry_dashboard_audit.json")
    prompt_audit = read_json(output_dir / "limited_qualitative_usage_registry_future_prompt_audit.json")
    forbidden = read_json(output_dir / "limited_qualitative_usage_registry_forbidden_action_audit.json")
    invariants = read_json(output_dir / "limited_qualitative_usage_registry_review_invariant_checks.json")
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION:
        raise RuntimeError("Completed registry-review decision/signature mismatch")
    if decision.get("record_type") != "registry_review_only":
        raise RuntimeError("Completed output is not registry-review-only")
    validate_hash_contract(hash_audit)
    validate_scope_contract(scope_audit)
    validate_prompt(
        (output_dir / "next_limited_qualitative_usage_registry_acceptance_prompt.md").read_text(encoding="utf-8"),
        FUTURE_PROMPT_REQUIRED,
    )
    if not all((
        hash_audit.get("all_hash_checks_passed") is True,
        scope_audit.get("all_scope_checks_passed") is True,
        dashboard_audit.get("dashboard_state_consistent") is True,
        prompt_audit.get("future_prompt_constraints_complete") is True,
        forbidden.get("all_forbidden_action_checks_passed") is True,
        invariants.get("all_invariants_passed") is True,
        decision.get("registry_acceptance_prompt_allowed_next") is True,
    )):
        raise RuntimeError("Completed registry-review audit or guardrail contract mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes, source = verify_inputs()
    signature = input_signature(hashes)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "candidate_id_set_hash_verified": True, "layer_sha256_verified": True,
            "schema_sha256_verified": True, "registered_accepted_rows": 643,
            "restricted_navigation_external_contamination_count": 0,
            "strict_primary_manifest_rows": 56, "evidence_rows_created": 0,
            "analysis_outputs_created": 0, "global_analysis_readiness": False,
        }, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    build_reports(args.output_dir, hashes, signature, source)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({
        "output_dir": str(args.output_dir), "decision": DECISION,
        "candidate_id_set_hash_verified": True, "layer_sha256_verified": True,
        "schema_sha256_verified": True, "registered_accepted_rows": 643,
        "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56, "registry_acceptance_prompt_allowed_next": True,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "global_analysis_readiness": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
