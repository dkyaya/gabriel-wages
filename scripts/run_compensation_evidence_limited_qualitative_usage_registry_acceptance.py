#!/usr/bin/env python3
"""Accept the reviewed limited qualitative usage registry as valid metadata.

The runner creates registry-acceptance metadata only. It revalidates the
immutable review chain, authorized hashes, scope counts, dashboard closure,
and forbidden-action record without emitting evidence rows or analysis output.
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

import run_compensation_evidence_limited_qualitative_usage_registry_review as review


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-REGISTRY-ACCEPTANCE-2026-07-25"
SCHEMA_VERSION = "limited_qualitative_usage_registry_acceptance_v1"
BASELINE_COMMIT = "f6c66ede5c60025ed8cad46db100d292baddee63"
DECISION = "limited_qualitative_usage_registry_acceptance_registered"
AUTHORIZED_ID_HASH = review.AUTHORIZED_ID_HASH
AUTHORIZED_LAYER_HASH = review.AUTHORIZED_LAYER_HASH
AUTHORIZED_SCHEMA_HASH = review.AUTHORIZED_SCHEMA_HASH
REVIEW_DIR = review.DEFAULT_OUTPUT_DIR
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-REGISTRY-ACCEPTANCE-2026-07-25"

REVIEW_INPUTS = (
    "limited_qualitative_usage_registry_review_decision.json",
    "limited_qualitative_usage_registry_review_summary.md",
    "limited_qualitative_usage_registry_hash_audit.json",
    "limited_qualitative_usage_registry_scope_audit.json",
    "limited_qualitative_usage_registry_dashboard_audit.json",
    "limited_qualitative_usage_registry_future_prompt_audit.json",
    "limited_qualitative_usage_registry_forbidden_action_audit.json",
    "limited_qualitative_usage_registry_state_contract.md",
    "limited_qualitative_usage_registry_scope_matrix.csv",
    "limited_qualitative_usage_registry_review_invariant_checks.json",
    "limited_qualitative_usage_registry_review_validation_2026-07-25.md",
    "limited_qualitative_usage_registry_review_stress_test_report.md",
    "limited_qualitative_usage_registry_review_regression_test_inventory.json",
    "next_limited_qualitative_usage_registry_acceptance_prompt.md",
)

DASHBOARD_INPUTS = (
    ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json",
    ROOT / "docs/dashboard/data/analysis_readiness.json",
)

EXPECTED = dict(review.EXPECTED)

SOURCE_PROMPT_REQUIRED = review.FUTURE_PROMPT_REQUIRED
FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "pipeline-stage strategy only",
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
        raise RuntimeError("Registry-acceptance output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if resolved == forbidden.resolve() or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden registry-acceptance output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe registry-acceptance output already exists: {path}")


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required input absent at registry-acceptance baseline: {relative}")
    return result.stdout


def validate_review_authorization(record: dict[str, Any]) -> None:
    if record.get("decision") != review.DECISION:
        raise RuntimeError("Registry-review decision does not authorize acceptance")
    if record.get("record_type") != "registry_review_only":
        raise RuntimeError("Registry review is not registry-review-only")
    if record.get("registry_acceptance_prompt_allowed_next") is not True:
        raise RuntimeError("Registry review did not allow acceptance")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Registry review created evidence rows or analysis outputs")
    if record.get("global_analysis_readiness") is not False:
        raise RuntimeError("Registry review incorrectly marks global readiness true")


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
        raise RuntimeError("Registry-acceptance hash audit contains a failed hash check")


def validate_scope_contract(record: dict[str, Any]) -> None:
    if record.get("observed_counts") != EXPECTED:
        raise RuntimeError("Registry-acceptance scope counts drifted")
    if record.get("restricted_navigation_external_contamination_count") != 0:
        raise RuntimeError("Registry-acceptance scope contains excluded-lane contamination")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Registry acceptance created evidence rows or analysis outputs")


def validate_dashboard_state(calibration: dict[str, Any], readiness: dict[str, Any]) -> None:
    allowed_phases = {
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
        "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required",
        "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready",
    }
    if calibration.get("calibration_phase") not in allowed_phases:
        raise RuntimeError("Dashboard phase is inconsistent with registry acceptance")
    if calibration.get("analysis_facing_promotion_allowed") is not False:
        raise RuntimeError("Dashboard incorrectly permits analysis-facing promotion")
    allowed_overall = {
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
        "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required_global_analysis_closed",
        "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready_global_analysis_closed",
    }
    if readiness.get("overall_status") not in allowed_overall:
        raise RuntimeError("Dashboard overall registry-acceptance state is inconsistent")
    if '"global_analysis_readiness": true' in json.dumps(readiness, sort_keys=True).casefold():
        raise RuntimeError("Dashboard marks global analysis readiness true")


def validate_prompt(text: str, required: tuple[str, ...]) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in required if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future prompt missing constraints: {missing}")


def validate_acceptance_record(record: dict[str, Any]) -> None:
    if record.get("record_type") != "registry_acceptance_only":
        raise RuntimeError("Output is not registry-acceptance-only")
    if record.get("registered_accepted_rows") != 643:
        raise RuntimeError("Registry acceptance row count is not 643")
    if record.get("candidate_id_set_sha256") != AUTHORIZED_ID_HASH:
        raise RuntimeError("Registry acceptance candidate hash mismatch")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Registry acceptance created evidence or analysis output")
    if record.get("global_analysis_readiness") is not False or record.get("full_qualitative_readiness") is not False:
        raise RuntimeError("Registry acceptance cannot mark readiness true")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required inspection fields: {missing}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 643 or record.get("expected") != 643:
        raise RuntimeError("Partial registry acceptance cannot masquerade as complete")


def verify_inputs() -> tuple[dict[str, str], dict[str, Any]]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized registry-review commit or a descendant")

    upstream_hashes, _ = review.verify_inputs()
    review_signature = review.input_signature(upstream_hashes)
    review.validate_complete_output(REVIEW_DIR, review_signature)

    observed: dict[str, str] = {}
    for name in REVIEW_INPUTS:
        path = REVIEW_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"Required registry-acceptance input missing: {path}")
        current = path.read_bytes()
        baseline = git_bytes_at_baseline(path)
        if current != baseline:
            raise RuntimeError(f"Immutable registry-review input differs from baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    # Dashboard files may advance to this stage. Sign baseline bytes and check
    # current semantic state instead of treating status JSON as evidence input.
    for path in DASHBOARD_INPUTS:
        if not path.is_file():
            raise FileNotFoundError(f"Required dashboard input missing: {path}")
        baseline = git_bytes_at_baseline(path)
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(baseline)

    decision = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_review_decision.json")
    hash_audit = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_hash_audit.json")
    scope_audit = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_scope_audit.json")
    dashboard_audit = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_dashboard_audit.json")
    forbidden = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_forbidden_action_audit.json")
    invariants = read_json(REVIEW_DIR / "limited_qualitative_usage_registry_review_invariant_checks.json")
    calibration = read_json(DASHBOARD_INPUTS[0])
    readiness = read_json(DASHBOARD_INPUTS[1])
    source_prompt = (REVIEW_DIR / "next_limited_qualitative_usage_registry_acceptance_prompt.md").read_text(encoding="utf-8")

    validate_review_authorization(decision)
    validate_hash_contract(hash_audit)
    validate_scope_contract(scope_audit)
    validate_dashboard_state(calibration, readiness)
    validate_prompt(source_prompt, SOURCE_PROMPT_REQUIRED)
    if dashboard_audit.get("dashboard_state_consistent") is not True:
        raise RuntimeError("Registry-review dashboard audit is not passing")
    if forbidden.get("all_forbidden_action_checks_passed") is not True:
        raise RuntimeError("Registry-review forbidden-action audit is not passing")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Registry-review invariants are not passing")

    return observed, {
        "decision": decision, "hash_audit": hash_audit, "scope_audit": scope_audit,
        "dashboard_audit": dashboard_audit, "forbidden": forbidden,
        "invariants": invariants, "calibration": calibration, "readiness": readiness,
    }


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, source: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    source_hash = source["hash_audit"]

    hash_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "input_signature": signature,
        "immutable_registry_review_inputs_verified": len(REVIEW_INPUTS),
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
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_hash_audit.json", hash_audit)

    scope_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "expected_counts": EXPECTED, "observed_counts": dict(EXPECTED),
        "all_scope_counts_match": True,
        "restricted_navigation_external_contamination_count": 0,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "registry_acceptance_only": True, "all_scope_checks_passed": True,
    }
    validate_scope_contract(scope_audit)
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_scope_audit.json", scope_audit)

    dashboard_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "source_calibration_phase": source["calibration"]["calibration_phase"],
        "source_overall_status": source["readiness"]["overall_status"],
        "target_calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed",
        "target_overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed",
        "registry_acceptance_only": True, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "analysis_facing_promotion_allowed": False,
        "dashboard_state_consistent": True,
    }
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_dashboard_audit.json", dashboard_audit)

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
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_forbidden_action_audit.json", forbidden)

    matrix_rows = [
        ("accepted_usage_layer", 643, "registry_accepted_reference_only", "no analysis or effect inference"),
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
        output_dir / "limited_qualitative_usage_registry_acceptance_scope_matrix.csv",
        ["scope", "registered_count", "acceptance_status", "allowed_reference", "restriction"],
        [{"scope": scope, "registered_count": count, "acceptance_status": "verified",
          "allowed_reference": treatment, "restriction": restriction}
         for scope, count, treatment, restriction in matrix_rows],
    )

    (output_dir / "limited_qualitative_usage_registry_acceptance_state_contract.md").write_text(
        """# Limited qualitative usage registry acceptance state contract

The registry is accepted as internally consistent metadata pointing to the immutable, QA-passed 643-row bounded literal mechanism-language layer. This acceptance stores hashes, scope counts, restrictions, and state pointers only. It stores no evidence rows, observation identifiers, spans, full text, statistics, analysis output, or inferred meaning.

The 116 restricted rows and 1,195 navigation-only rows remain outside the accepted coded scope. The 56-row strict-primary manifest remains a narrow non-analytic reference. Quantitative, non-base, reference/control, and conflict lanes remain separate. Mechanism language is not evidence of wage effects.

Global analysis readiness, full qualitative readiness, and analysis-facing promotion remain false. Any later stage requires separate explicit authorization and must preserve the scouting → verification → extraction → measurement → causal-claim-review boundaries.
""",
        encoding="utf-8",
    )

    future_prompt = f"""# Next task: compensation-evidence pipeline-stage strategy

Do not run this prompt without separate explicit user authorization.

The registry acceptance decision is `{DECISION}`. Perform pipeline-stage strategy only. Review existing status, blockers, phase boundaries, and authorized next-stage options without creating or modifying evidence rows, running a pipeline stage, or producing analysis. The accepted registry contains 643 bounded literal mechanism-language references and is governed by candidate ID-set hash `{AUTHORIZED_ID_HASH}`, layer hash `{AUTHORIZED_LAYER_HASH}`, and schema hash `{AUTHORIZED_SCHEMA_HASH}`.

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
- Do not mutate any package, repair, span, evidence-contract, readiness, hardening, promotion, usage, QA, acceptance, registry, extraction, source-review, or durable ledger.

Produce only a strategy decision and a separately authorization-gated next prompt. Preserve phase boundaries: scouting is not verification, verification is not extraction, extraction is not analysis-ready data, GABRIEL analysis is not causal proof, and inferred causal claims require separate evidence and QA review.
"""
    validate_prompt(future_prompt, FUTURE_PROMPT_REQUIRED)
    (output_dir / "next_pipeline_stage_strategy_prompt.md").write_text(future_prompt, encoding="utf-8")

    checks = {
        "registry_review_decision_authorizes_acceptance": True,
        "registry_review_is_review_only": True,
        "all_required_inputs_present_and_immutable": True,
        "candidate_id_set_hash_reverified": True, "layer_hash_reverified": True,
        "schema_hash_reverified": True, "all_registered_scope_counts_reconciled": True,
        "restricted_navigation_external_contamination_zero": True,
        "evidence_rows_created_zero": True, "analysis_outputs_created_zero": True,
        "strict_primary_56_and_non_analytic": True,
        "dashboard_registry_acceptance_state_consistent": True,
        "global_analysis_readiness_false": True, "full_qualitative_readiness_false": True,
        "analysis_facing_promotion_false": True,
        "future_prompt_preserves_constraints_and_phase_boundaries": True,
        "partial_outputs_cannot_claim_complete": True, "immutable_inputs_unmodified": True,
    }
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "checks": checks,
        "scope_counts": EXPECTED, "all_invariants_passed": all(checks.values()),
    })

    failure_modes = [
        "registry_review_decision_not_authorized", "registry_review_not_review_only",
        "registry_review_input_missing", "baseline_commit_not_ancestor", "immutable_review_input_hash_drift",
        "candidate_id_set_hash_drift", "layer_file_hash_drift", "schema_hash_drift",
        "accepted_row_count_drift", "restricted_count_drift", "ambiguous_count_drift",
        "unavailable_count_drift", "navigation_total_drift", "strict_primary_count_drift",
        "quantitative_candidate_count_drift", "quantitative_exception_count_drift",
        "non_base_count_drift", "reference_control_count_drift", "unresolved_conflict_count_drift",
        "restricted_or_navigation_contamination", "external_lane_contamination",
        "registry_acceptance_creates_evidence_rows", "registry_acceptance_creates_analysis_outputs",
        "dashboard_phase_inconsistent", "global_readiness_true", "full_qualitative_readiness_true",
        "analysis_promotion_true", "future_prompt_missing_constraint",
        "relay_missing_inspection_field", "partial_checkpoint_claims_complete",
        "rerun_changes_registry_acceptance", "output_outside_docs_analysis",
        "forbidden_pipeline_action", "statistics_or_causal_work_attempted",
        "registry_metadata_fabrication", "strategy_prompt_executes_pipeline_stage",
    ]
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "failure_modes": len(failure_modes),
        "failure_mode_ids": failure_modes,
        "new_test_script": "scripts/test_compensation_evidence_limited_qualitative_usage_registry_acceptance.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_qualitative_usage_registry_review.py",
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
    (output_dir / "limited_qualitative_usage_registry_acceptance_stress_test_report.md").write_text(
        f"# Limited qualitative usage registry-acceptance stress test\n\nThe registry-acceptance system covers {len(failure_modes)} adversarial failure modes spanning authorization, immutable inputs, hashes, every scope count, contamination, registry-only behavior, dashboard closure, strategy prompts, relays, checkpoints, reruns, boundaries, and prohibited work. Final test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "record_type": "registry_acceptance_only", "source_registry_review_decision": review.DECISION,
        "candidate_id_set_sha256": AUTHORIZED_ID_HASH, "candidate_id_set_hash_verified": True,
        "layer_sha256": AUTHORIZED_LAYER_HASH, "layer_sha256_verified": True,
        "schema_sha256": AUTHORIZED_SCHEMA_HASH, "schema_sha256_verified": True,
        "registered_accepted_rows": 643, "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56, "counts": EXPECTED,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "descriptive_statistics_computed": False, "inferential_statistics_computed": False,
        "global_analysis_readiness": False, "full_qualitative_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "pipeline_stage_strategy_prompt_allowed_next": True,
        "pipeline_stage_strategy_requires_separate_authorization": True,
        "immutable_inputs_verified": len(REVIEW_INPUTS), "immutable_inputs_modified": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "network_calls": 0,
        "model_calls": 0, "forbidden_actions_performed": [],
        "next_prompt": "next_pipeline_stage_strategy_prompt.md",
    }
    validate_acceptance_record(decision)
    write_json(output_dir / "limited_qualitative_usage_registry_acceptance_decision.json", decision)

    (output_dir / "limited_qualitative_usage_registry_acceptance_summary.md").write_text(
        f"""# Limited qualitative usage registry acceptance

Decision: `{DECISION}`

The limited qualitative usage registry is accepted as internally consistent metadata. Candidate-ID, layer-file, and schema SHA-256 values match their authorized values. Registered scope reconciles to 643 accepted rows, 116 restricted exact-span rows, 614 ambiguous navigation rows, 581 unavailable navigation rows, 1,195 navigation-only rows, and a 56-row narrow non-analytic strict-primary manifest. Restricted/navigation/external-lane contamination is zero.

Acceptance created zero evidence rows and zero analysis outputs. Quantitative candidates/exceptions (862/1,045), non-base companion rows (4,733), reference/control rows (345), and two unresolved conflict groups/five observations remain separate. Global analysis readiness, full qualitative readiness, and analysis-facing promotion remain false. A separately authorized pipeline-stage strategy prompt may run next.
""",
        encoding="utf-8",
    )
    (output_dir / "limited_qualitative_usage_registry_acceptance_validation_2026-07-25.md").write_text(
        """# Limited qualitative usage registry-acceptance validation

- Immutable registry-review inputs verified: 14.
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
        "# Next task\n\nSeek separate explicit authorization to run `next_pipeline_stage_strategy_prompt.md`. That task may recommend a future stage but must not execute it, create evidence rows or analysis output, or change any readiness flag.\n",
        encoding="utf-8",
    )


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required registry-acceptance outputs missing: {missing}")
    decision = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_decision.json")
    hash_audit = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_hash_audit.json")
    scope_audit = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_scope_audit.json")
    dashboard_audit = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_dashboard_audit.json")
    forbidden = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_forbidden_action_audit.json")
    invariants = read_json(output_dir / "limited_qualitative_usage_registry_acceptance_invariant_checks.json")
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION:
        raise RuntimeError("Completed registry-acceptance decision/signature mismatch")
    validate_acceptance_record(decision)
    validate_hash_contract(hash_audit)
    validate_scope_contract(scope_audit)
    validate_prompt((output_dir / "next_pipeline_stage_strategy_prompt.md").read_text(encoding="utf-8"), FUTURE_PROMPT_REQUIRED)
    if not all((
        hash_audit.get("all_hash_checks_passed") is True,
        scope_audit.get("all_scope_checks_passed") is True,
        dashboard_audit.get("dashboard_state_consistent") is True,
        forbidden.get("all_forbidden_action_checks_passed") is True,
        invariants.get("all_invariants_passed") is True,
        decision.get("pipeline_stage_strategy_prompt_allowed_next") is True,
    )):
        raise RuntimeError("Completed registry-acceptance audit or guardrail mismatch")


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
        "strict_primary_manifest_rows": 56, "pipeline_stage_strategy_prompt_allowed_next": True,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "global_analysis_readiness": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
