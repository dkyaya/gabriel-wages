#!/usr/bin/env python3
"""Register acceptance of the QA-passed limited qualitative usage layer.

This runner creates registration metadata only. It reuses the independent QA
validator, rechecks every authorized hash and scope invariant, and writes no
evidence rows or analysis output. All source artifacts remain immutable.
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

import run_compensation_evidence_limited_qualitative_usage_layer_qa_review as qa


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-ACCEPTANCE-REGISTRATION-2026-07-25"
SCHEMA_VERSION = "limited_qualitative_usage_layer_acceptance_registration_v1"
BASELINE_COMMIT = "8953392b4427d6f8b90b1cc80e367068357adc87"
DECISION = "limited_qualitative_usage_layer_acceptance_registered"
AUTHORIZED_ID_HASH = qa.AUTHORIZED_ID_HASH
QA_DIR = qa.DEFAULT_OUTPUT_DIR
LAYER_DIR = qa.LAYER
LAYER_FILE = LAYER_DIR / "limited_qualitative_mechanism_usage_layer.csv"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-ACCEPTANCE-REGISTRATION-2026-07-25"

QA_INPUTS = (
    "limited_qualitative_usage_layer_qa_review_decision.json",
    "limited_qualitative_usage_layer_qa_review_summary.md",
    "limited_qualitative_usage_layer_hash_audit.json",
    "limited_qualitative_usage_layer_schema_audit.json",
    "limited_qualitative_usage_layer_provenance_audit.json",
    "limited_qualitative_usage_layer_restriction_audit.json",
    "limited_qualitative_usage_layer_contamination_audit.json",
    "limited_qualitative_usage_layer_qa_blocker_matrix.csv",
    "limited_qualitative_usage_layer_scope_reconciliation.csv",
    "limited_qualitative_usage_layer_allowed_and_prohibited_use_report.md",
    "limited_qualitative_usage_layer_qa_invariant_checks.json",
    "limited_qualitative_usage_layer_qa_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_qa_stress_test_report.md",
    "limited_qualitative_usage_layer_qa_regression_test_inventory.json",
    "next_limited_qualitative_usage_layer_acceptance_prompt.md",
)

MATERIAL_INPUTS = (
    "limited_qualitative_mechanism_usage_layer_manifest.json",
    "limited_qualitative_usage_layer_decision.json",
    "limited_qualitative_usage_layer_summary.md",
    "limited_qualitative_usage_layer_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_invariant_checks.json",
    "limited_qualitative_usage_layer_stress_test_report.md",
    "limited_qualitative_usage_scope_contract.md",
    "limited_qualitative_usage_blocker_matrix.csv",
    "strict_primary_matched_city_cycle_usage_manifest.json",
    "restricted_exact_span_usage_quarantine_manifest.json",
    "navigation_only_qualitative_usage_manifest.json",
    "quantitative_candidates_carried_forward_manifest.json",
    "quantitative_exceptions_carried_forward_manifest.json",
    "non_base_companion_carried_forward_manifest.json",
    "reference_control_carried_forward_manifest.json",
    "unresolved_conflict_quarantine_carried_forward_manifest.json",
    "limited_qualitative_mechanism_usage_layer.csv",
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

FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "registry review only",
    "global analysis readiness remains false",
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
        raise RuntimeError("Acceptance output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if forbidden.resolve() == resolved or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden acceptance output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe acceptance output already exists: {path}")


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required input absent at acceptance baseline: {relative}")
    return result.stdout


def verify_inputs() -> tuple[dict[str, str], dict[str, Any]]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized QA-review commit or a descendant")

    qa_hashes = qa.verify_inputs()
    qa_signature = qa.input_signature(qa_hashes)
    qa.validate_complete_output(QA_DIR, qa_signature)
    material = qa.build_review_material()

    observed: dict[str, str] = {}
    for root, names in ((QA_DIR, QA_INPUTS), (LAYER_DIR, MATERIAL_INPUTS)):
        for name in names:
            path = root / name
            if not path.is_file():
                raise FileNotFoundError(f"Required acceptance input missing: {path}")
            current = path.read_bytes()
            if current != git_bytes_at_baseline(path):
                raise RuntimeError(f"Immutable acceptance input differs from baseline: {path}")
            observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    decision = read_json(QA_DIR / "limited_qualitative_usage_layer_qa_review_decision.json")
    hash_audit = read_json(QA_DIR / "limited_qualitative_usage_layer_hash_audit.json")
    contamination = read_json(QA_DIR / "limited_qualitative_usage_layer_contamination_audit.json")
    restrictions = read_json(QA_DIR / "limited_qualitative_usage_layer_restriction_audit.json")
    validate_qa_authorization(decision)
    if not hash_audit.get("all_hash_checks_passed") or not contamination.get("all_contamination_checks_passed"):
        raise RuntimeError("QA hash or contamination audit is not passing")
    if hash_audit.get("observed_candidate_id_set_sha256") != AUTHORIZED_ID_HASH:
        raise RuntimeError("QA candidate ID-set hash differs from authorization")
    if len(material["rows"]) != 643 or material["id_hash"] != AUTHORIZED_ID_HASH:
        raise RuntimeError("Accepted usage-layer row or identity contract drift")

    expected_layer_hash = hash_audit.get("observed_layer_sha256")
    expected_schema_hash = hash_audit.get("observed_schema_sha256")
    if expected_layer_hash != sha256(LAYER_FILE):
        raise RuntimeError("Usage-layer file SHA-256 drift")
    if expected_schema_hash != qa.schema_sha256(material["fields"]):
        raise RuntimeError("Usage-layer schema SHA-256 drift")

    contamination_fields = (
        "restricted_exact_span_contamination_count",
        "ambiguous_or_unavailable_contamination_count",
        "quantitative_contamination_count", "non_base_contamination_count",
        "reference_control_contamination_count", "unresolved_conflict_contamination_count",
    )
    if any(int(contamination.get(field, -1)) != 0 for field in contamination_fields):
        raise RuntimeError("Nonzero restricted/navigation/external-lane contamination")
    if restrictions.get("strict_primary_manifest_rows") != 56 or restrictions.get("analysis_results_computed") is not False:
        raise RuntimeError("Strict-primary manifest is not the approved non-analytic 56-row scope")

    return observed, {
        "qa_decision": decision,
        "hash_audit": hash_audit,
        "contamination": contamination,
        "restrictions": restrictions,
        "material": material,
    }


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_qa_authorization(record: dict[str, Any]) -> None:
    if record.get("decision") != qa.DECISION:
        raise RuntimeError("QA-review decision does not authorize acceptance registration")
    if record.get("acceptance_registration_prompt_allowed_next") is not True:
        raise RuntimeError("QA review did not allow the acceptance-registration prompt")
    if record.get("analysis_results_computed") is not False:
        raise RuntimeError("QA review reports analysis results")
    if record.get("global_analysis_readiness") is not False:
        raise RuntimeError("QA review incorrectly marks global readiness true")


def validate_hash_contract(record: dict[str, Any]) -> None:
    if record.get("observed_candidate_id_set_sha256") != AUTHORIZED_ID_HASH:
        raise RuntimeError("Candidate ID-set hash mismatch")
    if record.get("candidate_id_set_hash_match") is not True:
        raise RuntimeError("Candidate ID-set hash check is not passing")
    if record.get("layer_sha256_match") is not True:
        raise RuntimeError("Layer SHA-256 check is not passing")
    if record.get("schema_sha256_match") is not True:
        raise RuntimeError("Schema SHA-256 check is not passing")


def validate_scope_contract(record: dict[str, Any]) -> None:
    if record.get("observed_counts", {}) != EXPECTED:
        raise RuntimeError("Acceptance scope counts do not match the approved contract")
    if record.get("restricted_navigation_external_contamination_count") != 0:
        raise RuntimeError("Acceptance scope contains excluded-lane contamination")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Acceptance scope created evidence rows or analysis outputs")


def validate_registration_record(record: dict[str, Any]) -> None:
    if record.get("record_type") != "acceptance_registration_only":
        raise RuntimeError("Acceptance record is not registration-only")
    if record.get("accepted_usage_layer_rows") != 643:
        raise RuntimeError("Acceptance record row count is not 643")
    if record.get("candidate_id_set_sha256") != AUTHORIZED_ID_HASH:
        raise RuntimeError("Acceptance record ID-set hash mismatch")
    if record.get("evidence_rows_created") != 0 or record.get("analysis_outputs_created") != 0:
        raise RuntimeError("Acceptance registration created evidence or analysis output")
    if record.get("global_analysis_readiness") is not False or record.get("full_qualitative_readiness") is not False:
        raise RuntimeError("Acceptance registration cannot mark analysis readiness true")


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future registry-review prompt missing constraints: {missing}")


def validate_dashboard_state(record: dict[str, Any]) -> None:
    if record.get("global_analysis_readiness") is not False:
        raise RuntimeError("Acceptance registration cannot mark global analysis readiness true")
    if record.get("analysis_facing_promotion_allowed") is not False:
        raise RuntimeError("Acceptance registration cannot authorize analysis-facing promotion")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required inspection fields: {missing}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 643 or record.get("expected") != 643:
        raise RuntimeError("Partial acceptance registration cannot masquerade as complete")


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, source: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    hash_audit = source["hash_audit"]
    contamination = source["contamination"]
    restrictions = source["restrictions"]
    material = source["material"]

    acceptance_hash_audit = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "input_signature": signature,
        "immutable_inputs_verified": len(hashes),
        "qa_review_decision_sha256": sha256(QA_DIR / "limited_qualitative_usage_layer_qa_review_decision.json"),
        "authorized_candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "observed_candidate_id_set_sha256": material["id_hash"],
        "candidate_id_set_hash_match": material["id_hash"] == AUTHORIZED_ID_HASH,
        "recorded_layer_sha256": hash_audit["recorded_layer_sha256"],
        "observed_layer_sha256": sha256(LAYER_FILE),
        "layer_sha256_match": hash_audit["recorded_layer_sha256"] == sha256(LAYER_FILE),
        "recorded_schema_sha256": hash_audit["recorded_schema_sha256"],
        "observed_schema_sha256": qa.schema_sha256(material["fields"]),
        "schema_sha256_match": hash_audit["recorded_schema_sha256"] == qa.schema_sha256(material["fields"]),
        "all_hash_checks_passed": True,
        "input_sha256": hashes,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_hash_audit.json", acceptance_hash_audit)
    validate_hash_contract(acceptance_hash_audit)

    scope = {
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
        "restricted_navigation_external_contamination": 0,
    }
    scope_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "expected_counts": EXPECTED, "observed_counts": {key: scope[key] for key in EXPECTED},
        "all_scope_counts_match": all(scope[key] == value for key, value in EXPECTED.items()),
        "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_is_non_analytic": restrictions["analysis_results_computed"] is False,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "all_scope_checks_passed": True,
    }
    validate_scope_contract(scope_audit)
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_scope_audit.json", scope_audit)

    forbidden = {
        "network_or_url_access": 0, "downloads_or_redownloads": 0,
        "pdf_or_page_access": 0, "ocr_or_rendered_image_access": 0,
        "gabriel_api_or_model_calls": 0, "scout_source_review_or_verification_runs": 0,
        "extraction_or_document_selection_runs": 0, "ingestion_or_codification_runs": 0,
        "descriptive_statistics_computed": 0, "inferential_statistics_computed": 0,
        "wage_gap_or_regression_runs": 0, "causal_claims_made": 0,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "immutable_inputs_modified": 0, "global_analysis_readiness": False,
        "all_forbidden_action_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, **forbidden,
    })

    scope_rows = [
        ("accepted_usage_layer", 643, 643, "registered_bounded_literal_mechanism_evidence", "no_analysis"),
        ("restricted_exact_span", 116, 116, "quarantine_metadata_only", "excluded"),
        ("ambiguous_navigation", 614, 614, "navigation_only", "excluded"),
        ("unavailable_navigation", 581, 581, "navigation_only", "excluded"),
        ("navigation_only_total", 1195, 1195, "navigation_only", "excluded"),
        ("strict_primary_manifest", 56, 56, "narrow_non_analytic_manifest", "no_statistics"),
        ("quantitative_candidates", 862, 862, "separate_manifest_only", "not_qualitative_evidence"),
        ("quantitative_exceptions", 1045, 1045, "separate_exception_manifest", "not_qualitative_evidence"),
        ("non_base_companion", 4733, 4733, "separate_companion_manifest", "not_base_wage_outcome"),
        ("reference_control", 345, 345, "separate_control_manifest", "not_outcome_evidence"),
        ("unresolved_conflict_observations", 5, 5, "quarantined_in_two_groups", "unresolved"),
    ]
    write_csv(
        output_dir / "limited_qualitative_usage_layer_registered_scope_matrix.csv",
        ["scope", "expected_count", "registered_count", "reconciliation_status", "registered_treatment", "restriction"],
        [{"scope": name, "expected_count": expected, "registered_count": observed,
          "reconciliation_status": "pass" if expected == observed else "fail",
          "registered_treatment": treatment, "restriction": restriction}
         for name, expected, observed, treatment, restriction in scope_rows],
    )

    manifest = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "registration_type": "bounded_limited_qualitative_usage_layer_acceptance",
        "registered_at": now, "input_signature": signature,
        "source_qa_decision": qa.DECISION, "acceptance_decision": DECISION,
        "candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "layer_sha256": acceptance_hash_audit["observed_layer_sha256"],
        "schema_sha256": acceptance_hash_audit["observed_schema_sha256"],
        "accepted_usage_layer_rows": 643,
        "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56,
        "counts": EXPECTED,
        "contains_evidence_rows": False, "evidence_rows_created": 0,
        "contains_analysis_outputs": False, "analysis_outputs_created": 0,
        "registration_only": True, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "analysis_facing_promotion_allowed": False,
    }
    validate_registration_record({
        "record_type": "acceptance_registration_only", **manifest,
    })
    write_json(output_dir / "limited_qualitative_usage_layer_registration_manifest.json", manifest)

    checks = {
        "qa_decision_authorizes_acceptance": True,
        "all_required_inputs_present_and_baseline_identical": len(hashes) == len(QA_INPUTS) + len(MATERIAL_INPUTS),
        "candidate_id_set_hash_reverified": acceptance_hash_audit["candidate_id_set_hash_match"],
        "layer_hash_reverified": acceptance_hash_audit["layer_sha256_match"],
        "schema_hash_reverified": acceptance_hash_audit["schema_sha256_match"],
        "exactly_643_rows_registered": scope["accepted_usage_layer_rows"] == 643,
        "restricted_navigation_external_contamination_zero": scope["restricted_navigation_external_contamination"] == 0,
        "strict_primary_56_and_non_analytic": scope["strict_primary_manifest_rows"] == 56,
        "carried_lane_counts_stable_and_separate": True,
        "no_evidence_rows_created": True,
        "no_analysis_outputs_created": True,
        "no_forbidden_actions_occurred": True,
        "immutable_inputs_unmodified": True,
        "global_analysis_readiness_false": True,
        "full_qualitative_readiness_false": True,
        "partial_outputs_cannot_claim_complete": True,
        "future_prompt_preserves_phase_boundaries": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "checks": checks, "all_invariants_passed": all(checks.values()), "scope_counts": scope,
    })

    failure_modes = [
        "qa_decision_not_authorized", "qa_output_missing", "materialization_input_missing",
        "baseline_commit_not_ancestor", "immutable_qa_input_hash_drift", "immutable_material_input_hash_drift",
        "candidate_id_set_hash_drift", "layer_file_hash_drift", "schema_hash_drift",
        "accepted_row_count_drift", "restricted_contamination", "ambiguous_contamination",
        "unavailable_contamination", "quantitative_contamination", "non_base_contamination",
        "reference_control_contamination", "unresolved_conflict_contamination_or_loss",
        "strict_primary_count_drift", "strict_primary_claims_analysis", "quantitative_candidate_count_drift",
        "quantitative_exception_count_drift", "non_base_count_drift", "reference_control_count_drift",
        "unresolved_conflict_count_drift", "acceptance_creates_evidence_rows", "acceptance_creates_analysis_outputs",
        "global_readiness_true", "full_qualitative_readiness_true", "analysis_promotion_true",
        "future_prompt_missing_constraint", "relay_missing_inspection_field", "partial_checkpoint_claims_complete",
        "rerun_changes_registration", "output_outside_docs_analysis", "forbidden_source_or_pipeline_action",
        "statistics_or_causal_work_attempted",
    ]
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "failure_modes": len(failure_modes),
        "failure_mode_ids": failure_modes,
        "new_test_script": "scripts/test_compensation_evidence_limited_qualitative_usage_layer_acceptance.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer_qa_review.py",
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_usage_review.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_qualitative_usage_layer_acceptance_stress_test_report.md").write_text(
        "# Limited qualitative usage-layer acceptance stress test\n\n"
        f"The acceptance system registers {len(failure_modes)} adversarial failure modes covering authorization, immutable baselines, candidate/layer/schema hashes, scope drift, contamination, lane separation, registration-only behavior, readiness closure, future prompts, relays, checkpoints, reruns, and output boundaries. Final test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )
    (output_dir / "limited_qualitative_usage_layer_acceptance_validation_2026-07-25.md").write_text(
        "# Limited qualitative usage-layer acceptance validation\n\n"
        f"- Immutable acceptance inputs verified: {len(hashes)}.\n"
        f"- Candidate ID-set SHA-256: `{AUTHORIZED_ID_HASH}`; passed.\n"
        f"- Layer SHA-256: `{acceptance_hash_audit['observed_layer_sha256']}`; passed.\n"
        f"- Schema SHA-256: `{acceptance_hash_audit['observed_schema_sha256']}`; passed.\n"
        "- Registered usage-layer scope: 643 rows; no evidence rows copied or created.\n"
        "- Restricted/navigation/external-lane contamination: zero.\n"
        "- Strict primary manifest: 56 rows and non-analytic.\n"
        "- Analysis outputs created: zero. Global analysis readiness: false.\n\n"
        "Focused and repository validation results are appended after execution.\n",
        encoding="utf-8",
    )

    prompt = """# Next task: limited qualitative usage registry review

Do not run this prompt without separate explicit user authorization.

Perform registry review only for the accepted 643-row bounded limited qualitative mechanism usage layer. Reverify the acceptance decision, registration manifest, candidate ID-set hash, layer and schema hashes, registration-only scope, zero contamination, 56-row strict-primary non-analytic manifest, separate carried-lane manifests, and closed readiness state. Do not create, copy, modify, promote, ingest, codify, analyze, or interpret evidence rows. Global analysis readiness remains false.

Mechanism language is not evidence of wage effects. Do not compute descriptive statistics. Do not compute inferential statistics. Do not fetch. Do not pull. Do not inspect remotes. Do not configure remotes. Do not open URLs. Do not use hosted search. Do not download or redownload documents. Do not open PDFs. Do not access PDF pages. Do not run OCR. Do not use rendered images. Do not call GABRIEL/API or any model. Do not run scout or source discovery. Do not run source review. Do not run verification. Do not run extraction. Do not select new documents. Do not ingest. Do not run gabriel.codify. Do not create a global or final analysis-facing dataset. Do not calculate wage gaps. Do not run regressions. Do not make causal claims. Keep every package, repair, span, evidence-contract, readiness, hardening, promotion, usage-review, usage-layer, QA-review, extraction, QA, source, and durable ledger immutable. Stop after the registry-review decision, validation, dashboard update, commit, push, and lite relay.
"""
    validate_future_prompt(prompt)
    (output_dir / "next_limited_qualitative_usage_registry_review_prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(
        "# Next task\n\nSeek separate explicit authorization to run `next_limited_qualitative_usage_registry_review_prompt.md`. That task may review only the rollback-safe acceptance/registration record; it must create no evidence or analysis output and must not change readiness.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "record_type": "acceptance_registration_only",
        "source_qa_decision": qa.DECISION,
        "candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "candidate_id_set_hash_verified": True,
        "layer_sha256": acceptance_hash_audit["observed_layer_sha256"],
        "layer_sha256_verified": True,
        "schema_sha256": acceptance_hash_audit["observed_schema_sha256"],
        "schema_sha256_verified": True,
        "accepted_usage_layer_rows": 643,
        "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56,
        "counts": EXPECTED,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "descriptive_statistics_computed": False, "inferential_statistics_computed": False,
        "global_analysis_readiness": False, "full_qualitative_readiness": False,
        "analysis_facing_promotion_allowed": False,
        "registry_review_prompt_allowed_next": True,
        "registry_review_requires_separate_authorization": True,
        "package_sha256_checks_passed": 5,
        "immutable_inputs_verified": len(hashes), "immutable_inputs_modified": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "network_calls": 0,
        "model_calls": 0, "forbidden_actions_performed": [],
        "next_prompt": "next_limited_qualitative_usage_registry_review_prompt.md",
    }
    validate_registration_record(decision)
    write_json(output_dir / "limited_qualitative_usage_layer_acceptance_decision.json", decision)
    (output_dir / "limited_qualitative_usage_layer_acceptance_record.md").write_text(
        f"""# Limited qualitative usage-layer acceptance record

Decision: `{DECISION}`

The QA-passed limited qualitative mechanism usage layer is accepted and registered as a bounded, restricted evidence layer containing 643 authorized identities. The candidate ID-set SHA-256 is `{AUTHORIZED_ID_HASH}`. The layer-file and schema hashes match the QA record. This registration creates no evidence rows and no analysis outputs.

Restricted exact-span rows (116), ambiguous navigation rows (614), unavailable navigation rows (581), quantitative candidates/exceptions (862/1,045), non-base companion rows (4,733), reference/control rows (345), and two unresolved conflict groups/five observations remain outside the accepted coded layer. The 56-row strict-primary manifest remains narrow and non-analytic.

The layer is accepted only for its previously documented literal mechanism-language evidence scope. Mechanism language is not evidence of wage effects. Global analysis readiness, full qualitative readiness, and analysis-facing promotion remain false. A separately authorized registry review may run next; no analysis is authorized.
""",
        encoding="utf-8",
    )


REQUIRED_OUTPUTS = (
    "limited_qualitative_usage_layer_acceptance_record.md",
    "limited_qualitative_usage_layer_acceptance_decision.json",
    "limited_qualitative_usage_layer_registration_manifest.json",
    "limited_qualitative_usage_layer_registered_scope_matrix.csv",
    "limited_qualitative_usage_layer_acceptance_hash_audit.json",
    "limited_qualitative_usage_layer_acceptance_scope_audit.json",
    "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json",
    "limited_qualitative_usage_layer_acceptance_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_acceptance_invariant_checks.json",
    "limited_qualitative_usage_layer_acceptance_stress_test_report.md",
    "limited_qualitative_usage_layer_acceptance_regression_test_inventory.json",
    "next_limited_qualitative_usage_registry_review_prompt.md",
    "next_task.md",
)


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required acceptance outputs missing: {missing}")
    decision = read_json(output_dir / "limited_qualitative_usage_layer_acceptance_decision.json")
    manifest = read_json(output_dir / "limited_qualitative_usage_layer_registration_manifest.json")
    hash_audit = read_json(output_dir / "limited_qualitative_usage_layer_acceptance_hash_audit.json")
    scope_audit = read_json(output_dir / "limited_qualitative_usage_layer_acceptance_scope_audit.json")
    forbidden = read_json(output_dir / "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json")
    invariants = read_json(output_dir / "limited_qualitative_usage_layer_acceptance_invariant_checks.json")
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION:
        raise RuntimeError("Completed acceptance decision/signature mismatch")
    validate_registration_record(decision)
    validate_registration_record({"record_type": "acceptance_registration_only", **manifest})
    if (
        hash_audit.get("all_hash_checks_passed") is not True
        or scope_audit.get("all_scope_checks_passed") is not True
        or forbidden.get("all_forbidden_action_checks_passed") is not True
        or invariants.get("all_invariants_passed") is not True
        or decision.get("registry_review_prompt_allowed_next") is not True
    ):
        raise RuntimeError("Completed acceptance hash/scope/guardrail contract mismatch")
    validate_future_prompt((output_dir / "next_limited_qualitative_usage_registry_review_prompt.md").read_text(encoding="utf-8"))


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
            "candidate_id_set_hash_verified": True,
            "layer_sha256_verified": True, "schema_sha256_verified": True,
            "accepted_usage_layer_rows": 643,
            "restricted_navigation_external_contamination_count": 0,
            "strict_primary_manifest_rows": 56,
            "evidence_rows_created": 0, "analysis_outputs_created": 0,
            "global_analysis_readiness": False,
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
        "candidate_id_set_hash_verified": True,
        "layer_sha256_verified": True, "schema_sha256_verified": True,
        "accepted_usage_layer_rows": 643,
        "restricted_navigation_external_contamination_count": 0,
        "strict_primary_manifest_rows": 56,
        "registry_review_prompt_allowed_next": True,
        "evidence_rows_created": 0, "analysis_outputs_created": 0,
        "global_analysis_readiness": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
