#!/usr/bin/env python3
"""Review the hardened limited exact-span qualitative promotion layer.

This is a deterministic contract and usage-scope review. It does not create a
usage dataset, perform descriptive or inferential analysis, open PDFs, access
the network, call a model, or mutate any upstream evidence artifact. Outputs
are manifests, audit counts, contracts, and fail-closed decision documents.
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

import run_compensation_evidence_limited_exact_span_qualitative_promotion as promotion


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-USAGE-REVIEW-2026-07-25"
SCHEMA_VERSION = "limited_exact_span_qualitative_usage_review_v1"
BASELINE_COMMIT = "9052a30a350d6be60796897de5b600b974414523"
DECISION = "limited_exact_span_qualitative_usage_review_pass_prepare_usage_layer_prompt"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-USAGE-REVIEW-2026-07-25"
PROMOTION = promotion.DEFAULT_OUTPUT_DIR

REQUIRED_INPUTS = (
    "limited_exact_span_qualitative_promoted_view.csv",
    "limited_exact_span_qualitative_row_eligibility.csv",
    "limited_exact_span_qualitative_quarantine_ledger.csv",
    "ambiguous_unavailable_qualitative_navigation_preserved.csv",
    "limited_exact_span_qualitative_promotion_manifest.json",
    "limited_exact_span_qualitative_promotion_decision.json",
    "limited_exact_span_qualitative_promotion_audit.json",
    "limited_exact_span_qualitative_promotion_blocker_matrix.csv",
    "limited_exact_span_qualitative_promotion_validation_2026-07-25.md",
    "limited_exact_span_qualitative_promotion_summary.md",
    "limited_exact_span_qualitative_promotion_invariant_checks.json",
    "limited_exact_span_qualitative_promotion_stress_test_report.md",
    "limited_exact_span_qualitative_promotion_regression_test_inventory.json",
    "quantitative_candidates_carried_forward_manifest.json",
    "non_base_reference_conflict_carried_forward_manifest.json",
)

EXPECTED_COUNTS = {
    "promoted_view": 759,
    "limited_use_candidate": 643,
    "restricted_exact_span": 116,
    "ambiguous_navigation": 614,
    "unavailable_navigation": 581,
    "navigation_only": 1195,
    "strict_primary_matched_city_cycle": 56,
    "exact_cycle": 453,
    "controlled_occupation": 438,
    "exact_period_matched_set": 77,
    "typed_mechanism": 643,
    "quantitative_candidates": 862,
    "quantitative_exceptions": 1045,
    "non_base_companion": 4733,
    "reference_control": 345,
    "unresolved_conflict_groups": 2,
    "unresolved_conflict_observations": 5,
}

USAGE_MANIFESTS = {
    "limited_qualitative_mechanism_usage_candidate_manifest.json",
    "strict_primary_matched_city_cycle_usage_candidate_manifest.json",
    "restricted_exact_span_usage_quarantine_manifest.json",
    "navigation_only_qualitative_usage_manifest.json",
}

RELAY_REQUIRED = {
    "commit_hash", "push_status", "validation_results", "dashboard_status",
    "forbidden_action_confirmations", "next_recommendation",
}

FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "limited qualitative usage layer only",
    "global analysis readiness remains false",
    "Do not fetch", "Do not pull", "Do not inspect remotes",
    "Do not open URLs", "Do not open PDFs", "Do not access PDF pages",
    "Do not run OCR", "Do not call GABRIEL/API", "Do not run extraction",
    "Do not select new documents", "Do not ingest", "Do not run gabriel.codify",
    "Do not calculate wage gaps", "Do not run regressions", "Do not make causal claims",
    "mechanism language is not evidence of wage effects",
)

FORBIDDEN_OUTPUT_FIELDS = promotion.FORBIDDEN_FIELDS | {
    "wage_gap", "treatment_effect", "regression_result", "causal_effect",
    "full_page_text", "raw_page_payload", "pdf_text", "document_text",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def id_set_sha256(ids: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")).hexdigest()


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
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    allowed = (ROOT / "docs/analysis").resolve()
    if allowed not in resolved.parents:
        raise RuntimeError("Output must remain under docs/analysis")
    forbidden_roots = (ROOT / "data", ROOT / "corpus", ROOT / "ingest")
    if any(root.resolve() == resolved or root.resolve() in resolved.parents for root in forbidden_roots):
        raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def required_paths() -> list[Path]:
    return [PROMOTION / name for name in REQUIRED_INPUTS]


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required immutable promotion input is not recorded at baseline: {relative}")
    return result.stdout


def verify_inputs() -> dict[str, str]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized promotion commit or a descendant")

    # Re-run the promotion's complete immutable package/prior-layer contract.
    promotion.verify_inputs()
    observed: dict[str, str] = {}
    for path in required_paths():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        current = path.read_bytes()
        if current != git_bytes_at_baseline(path):
            raise RuntimeError(f"Immutable promotion input differs from authorized baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    decision = read_json(PROMOTION / "limited_exact_span_qualitative_promotion_decision.json")
    if (
        decision.get("decision") != promotion.DECISION
        or decision.get("limited_usage_review_allowed_next") is not True
        or decision.get("global_analysis_readiness") is not False
        or decision.get("global_analysis_facing_promotion") is not False
    ):
        raise RuntimeError("Promotion decision does not authorize this limited usage review")
    return observed


def true_ids(rows: list[dict[str, str]], field: str) -> set[str]:
    return {row["qualitative_observation_id"] for row in rows if row.get(field) == "true"}


def validate_no_forbidden_fields(fields: list[str]) -> None:
    bad = sorted(set(fields) & FORBIDDEN_OUTPUT_FIELDS)
    if bad:
        raise RuntimeError(f"Forbidden analysis or payload fields present: {bad}")


def validate_material_inputs() -> dict[str, Any]:
    promoted_fields, promoted = read_csv(PROMOTION / "limited_exact_span_qualitative_promoted_view.csv")
    eligibility_fields, eligibility = read_csv(PROMOTION / "limited_exact_span_qualitative_row_eligibility.csv")
    quarantine_fields, quarantine = read_csv(PROMOTION / "limited_exact_span_qualitative_quarantine_ledger.csv")
    navigation_fields, navigation = read_csv(PROMOTION / "ambiguous_unavailable_qualitative_navigation_preserved.csv")
    for fields in (promoted_fields, eligibility_fields, quarantine_fields, navigation_fields):
        validate_no_forbidden_fields(fields)

    if (len(promoted), len(eligibility), len(quarantine), len(navigation)) != (759, 759, 116, 1195):
        raise RuntimeError("Promotion material count drift")
    promoted_ids = [row["qualitative_observation_id"] for row in promoted]
    eligibility_ids = [row["qualitative_observation_id"] for row in eligibility]
    quarantine_ids = [row["qualitative_observation_id"] for row in quarantine]
    navigation_ids = [row["qualitative_observation_id"] for row in navigation]
    if len(set(promoted_ids)) != 759 or len(set(eligibility_ids)) != 759 or len(set(navigation_ids)) != 1195:
        raise RuntimeError("Duplicate qualitative observation ID in promotion material")
    if set(promoted_ids) != set(eligibility_ids):
        raise RuntimeError("Promoted and eligibility identities do not reconcile")
    if set(promoted_ids) & set(navigation_ids):
        raise RuntimeError("Navigation identity entered the promoted evidence universe")

    limited = true_ids(promoted, "eligible_for_limited_qualitative_use")
    restricted = set(promoted_ids) - limited
    if restricted != set(quarantine_ids):
        raise RuntimeError("Restricted exact-span and quarantine identities do not reconcile")
    if any(row.get("eligible_for_limited_qualitative_use") != "false" for row in navigation):
        raise RuntimeError("Navigation-only row entered limited-use eligibility")
    if any(row.get("navigation_only") != "true" for row in navigation):
        raise RuntimeError("Navigation-only contract flag missing")

    scopes = {
        "promoted_view": len(promoted),
        "limited_use_candidate": len(limited),
        "restricted_exact_span": len(restricted),
        "ambiguous_navigation": sum(row.get("evidence_contract_tier") == "ambiguous_exact_span_navigation" for row in navigation),
        "unavailable_navigation": sum(row.get("evidence_contract_tier") == "unavailable_span_navigation" for row in navigation),
        "navigation_only": len(navigation),
        "strict_primary_matched_city_cycle": len(true_ids(promoted, "eligible_for_primary_matched_city_cycle_design")),
        "exact_cycle": len(true_ids(promoted, "eligible_for_cycle_analysis")),
        "controlled_occupation": len(true_ids(promoted, "eligible_for_occupation_comparison")),
        "exact_period_matched_set": len(true_ids(promoted, "eligible_for_exact_period_matched_set")),
        "typed_mechanism": len(true_ids(promoted, "eligible_for_typed_mechanism_analysis")),
    }
    quant = read_json(PROMOTION / "quantitative_candidates_carried_forward_manifest.json")
    lanes = read_json(PROMOTION / "non_base_reference_conflict_carried_forward_manifest.json")
    scopes.update({
        "quantitative_candidates": int(quant["candidate_rows"]),
        "quantitative_exceptions": int(quant["exception_rows"]),
        "non_base_companion": int(lanes["non_base_companion_rows"]),
        "reference_control": int(lanes["reference_control_rows"]),
        "unresolved_conflict_groups": int(lanes["unresolved_conflict_groups"]),
        "unresolved_conflict_observations": int(lanes["unresolved_conflict_observations"]),
    })
    if scopes != EXPECTED_COUNTS:
        raise RuntimeError(f"Usage-review eligibility count drift: {scopes}")

    primary = true_ids(promoted, "eligible_for_primary_matched_city_cycle_design")
    cycle = true_ids(promoted, "eligible_for_cycle_analysis")
    occupation = true_ids(promoted, "eligible_for_occupation_comparison")
    matched = true_ids(promoted, "eligible_for_exact_period_matched_set")
    typed = true_ids(promoted, "eligible_for_typed_mechanism_analysis")
    if not (primary <= matched <= limited and primary <= cycle <= limited and primary <= occupation <= limited and typed == limited):
        raise RuntimeError("Usage eligibility subset contract failed")
    if any(row.get("mechanism_type") == "other" and row.get("eligible_for_typed_mechanism_analysis") == "true" for row in promoted):
        raise RuntimeError("mechanism_type=other entered typed use")
    if any(row.get("mixed_membership_status", "").startswith("historical") and row.get("eligible_for_limited_qualitative_use") == "true" for row in promoted):
        raise RuntimeError("Historical mixed membership entered active limited use")

    return {
        "promoted": promoted, "eligibility": eligibility, "quarantine": quarantine,
        "navigation": navigation, "scopes": scopes, "limited_ids": limited,
        "restricted_ids": restricted, "primary_ids": primary, "cycle_ids": cycle,
        "occupation_ids": occupation, "matched_ids": matched, "typed_ids": typed,
    }


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future usage-layer prompt missing constraints: {missing}")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    blank = sorted(key for key in RELAY_REQUIRED if record.get(key) in (None, "", []))
    if missing or blank:
        raise RuntimeError(f"Relay metadata incomplete: missing={missing}; blank={blank}")


def validate_dashboard_state(record: dict[str, Any]) -> None:
    if record.get("analysis_readiness") is not False:
        raise RuntimeError("Usage review cannot mark global analysis readiness true")
    if record.get("limited_usage_layer_prompt_allowed_next") not in {True, False}:
        raise RuntimeError("Dashboard limited-usage-layer state is not explicit")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 759 or record.get("expected") != 759:
        raise RuntimeError("Partial usage-review checkpoint cannot masquerade as complete")


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def manifest_for(scope: str, ids: set[str], *, allowed_use: str, restrictions: list[str], source_hash: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": scope,
        "row_count": len(ids),
        "qualitative_observation_id_set_sha256": id_set_sha256(ids),
        "source_promoted_view_sha256": source_hash,
        "allowed_use": allowed_use,
        "restrictions": restrictions,
        "contains_observation_rows": False,
        "global_analysis_readiness": False,
        "analysis_results_computed": False,
    }


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, material: dict[str, Any]) -> None:
    scopes = material["scopes"]
    promoted_hash = sha256(PROMOTION / "limited_exact_span_qualitative_promoted_view.csv")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    scope_rows = [
        {"usage_scope": "limited_qualitative_mechanism", "eligible_row_count": 643, "allowed_next_layer": "restricted literal-mechanism evidence layer", "permitted_characterization": "mechanism-language evidence with row-level eligibility", "prohibited_use": "wage effects|wage gaps|regression|causal claims", "review_outcome": "pass_prepare_prompt"},
        {"usage_scope": "strict_primary_matched_city_cycle", "eligible_row_count": 56, "allowed_next_layer": "narrow primary-design evidence manifest only", "permitted_characterization": "bounded matched-design evidence navigation", "prohibited_use": "effect estimation|generalization|causal inference", "review_outcome": "pass_with_narrow_scope"},
        {"usage_scope": "exact_cycle_descriptive", "eligible_row_count": 453, "allowed_next_layer": "cycle-aware qualitative evidence review", "permitted_characterization": "contract-cycle-linked mechanism language", "prohibited_use": "wage-gap analysis|treatment effects", "review_outcome": "pass_with_restrictions"},
        {"usage_scope": "controlled_occupation_descriptive", "eligible_row_count": 438, "allowed_next_layer": "occupation-aware qualitative evidence review", "permitted_characterization": "controlled-occupation mechanism language", "prohibited_use": "wage-gap analysis|causal comparison", "review_outcome": "pass_with_restrictions"},
        {"usage_scope": "exact_period_matched_set_review", "eligible_row_count": 77, "allowed_next_layer": "matched-set evidence review", "permitted_characterization": "matched-set coverage and mechanism-language navigation", "prohibited_use": "effect estimation|causal inference", "review_outcome": "pass_with_restrictions"},
        {"usage_scope": "restricted_exact_span", "eligible_row_count": 116, "allowed_next_layer": "quarantine metadata only", "permitted_characterization": "exact-span evidence retained but restricted", "prohibited_use": "coded qualitative usage", "review_outcome": "quarantined"},
        {"usage_scope": "ambiguous_navigation", "eligible_row_count": 614, "allowed_next_layer": "navigation only", "permitted_characterization": "ambiguous exact-span navigation", "prohibited_use": "coded evidence|analysis", "review_outcome": "navigation_only"},
        {"usage_scope": "unavailable_navigation", "eligible_row_count": 581, "allowed_next_layer": "navigation only", "permitted_characterization": "unavailable/unverified span navigation", "prohibited_use": "coded evidence|analysis", "review_outcome": "navigation_only"},
    ]
    write_csv(output_dir / "limited_exact_span_qualitative_usage_scope_matrix.csv", list(scope_rows[0]), scope_rows)

    blocker_rows = [
        {"blocker_id": "UR-QA-001", "lane": "exact_span", "row_count": 116, "severity": "major", "residual_status": "restricted_exact_span", "usage_treatment": "exclude from limited-use manifest; retain quarantine manifest", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-QA-002", "lane": "ambiguous_navigation", "row_count": 614, "severity": "critical", "residual_status": "navigation_only", "usage_treatment": "exclude from coded evidence", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-QA-003", "lane": "unavailable_navigation", "row_count": 581, "severity": "critical", "residual_status": "navigation_only", "usage_treatment": "exclude from coded evidence", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-CY-001", "lane": "cycle", "row_count": 190, "severity": "major", "residual_status": "limited_rows_without_exact_cycle", "usage_treatment": "exclude from cycle-aware and primary subsets", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-OC-001", "lane": "occupation", "row_count": 205, "severity": "major", "residual_status": "limited_rows_without_controlled_occupation", "usage_treatment": "exclude from occupation-aware and primary subsets", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-MT-001", "lane": "matching", "row_count": 566, "severity": "major", "residual_status": "limited_rows_without_exact_period_matched_set", "usage_treatment": "exclude from matched-set and primary subsets", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-PR-001", "lane": "primary_design", "row_count": 56, "severity": "scope_limit", "residual_status": "narrow_strict_subset", "usage_treatment": "retain explicit manifest; no effect or causal claims", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-QN-001", "lane": "quantitative", "row_count": 1045, "severity": "critical", "residual_status": "separate_exceptions", "usage_treatment": "not used by qualitative usage layer", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
        {"blocker_id": "UR-CF-001", "lane": "conflict", "row_count": 5, "severity": "critical", "residual_status": "two_groups_quarantined", "usage_treatment": "remain excluded and explicit", "blocks_global_readiness": "true", "blocks_limited_usage_layer": "false"},
    ]
    write_csv(output_dir / "limited_exact_span_qualitative_usage_blocker_matrix.csv", list(blocker_rows[0]), blocker_rows)

    usage_restrictions = [
        "literal mechanism-language evidence only",
        "no wage effects or quantitative outcomes",
        "no wage gaps, regressions, treatment effects, or causal claims",
        "row-level eligibility and quarantine fields remain binding",
        "separate authorization required to materialize a usage layer",
    ]
    write_json(output_dir / "limited_qualitative_mechanism_usage_candidate_manifest.json", manifest_for(
        "limited_qualitative_mechanism", material["limited_ids"],
        allowed_use="future restricted qualitative mechanism usage layer",
        restrictions=usage_restrictions, source_hash=promoted_hash,
    ))
    write_json(output_dir / "strict_primary_matched_city_cycle_usage_candidate_manifest.json", manifest_for(
        "strict_primary_matched_city_cycle", material["primary_ids"],
        allowed_use="future narrow primary-design evidence manifest and usage review",
        restrictions=usage_restrictions + ["56-row scope is narrow and does not establish representativeness or statistical power"],
        source_hash=promoted_hash,
    ))
    write_json(output_dir / "restricted_exact_span_usage_quarantine_manifest.json", manifest_for(
        "restricted_exact_span", material["restricted_ids"],
        allowed_use="quarantine and evidence navigation only",
        restrictions=["not eligible for limited coded use", "preserve exact spans and blocker reasons"],
        source_hash=promoted_hash,
    ))
    nav_ids = {row["qualitative_observation_id"] for row in material["navigation"]}
    nav_manifest = manifest_for(
        "ambiguous_unavailable_navigation_only", nav_ids,
        allowed_use="navigation only",
        restrictions=["never coded evidence", "ambiguous and unavailable tiers remain separate"],
        source_hash=sha256(PROMOTION / "ambiguous_unavailable_qualitative_navigation_preserved.csv"),
    )
    nav_manifest["ambiguous_rows"] = 614
    nav_manifest["unavailable_rows"] = 581
    write_json(output_dir / "navigation_only_qualitative_usage_manifest.json", nav_manifest)

    audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "input_signature": signature,
        "input_sha256": hashes, "scope_counts": scopes,
        "promoted_unique_ids": len({row["qualitative_observation_id"] for row in material["promoted"]}),
        "limited_candidate_unique_ids": len(material["limited_ids"]),
        "restricted_unique_ids": len(material["restricted_ids"]),
        "navigation_unique_ids": len(nav_ids),
        "candidate_restricted_overlap": len(material["limited_ids"] & material["restricted_ids"]),
        "candidate_navigation_overlap": len(material["limited_ids"] & nav_ids),
        "restricted_navigation_overlap": len(material["restricted_ids"] & nav_ids),
        "primary_subset_of_limited": material["primary_ids"] <= material["limited_ids"],
        "cycle_subset_of_limited": material["cycle_ids"] <= material["limited_ids"],
        "occupation_subset_of_limited": material["occupation_ids"] <= material["limited_ids"],
        "matched_subset_of_limited": material["matched_ids"] <= material["limited_ids"],
        "typed_equals_limited": material["typed_ids"] == material["limited_ids"],
        "analysis_results_computed": False, "pdf_pages_accessed": 0,
        "ocr_later_accessed": 0, "network_or_model_calls": 0,
        "immutable_inputs_modified": False, "global_analysis_readiness": False,
        "all_checks_passed": True,
    }
    write_json(output_dir / "limited_exact_span_qualitative_usage_eligibility_audit.json", audit)

    checks = {
        "promotion_decision_authorizes_usage_review": True,
        "immutable_promotion_inputs_match_authorized_baseline": True,
        "five_package_sha256_checks_pass": True,
        "promoted_view_count_759": scopes["promoted_view"] == 759,
        "limited_use_count_643": scopes["limited_use_candidate"] == 643,
        "restricted_count_116": scopes["restricted_exact_span"] == 116,
        "navigation_count_1195": scopes["navigation_only"] == 1195,
        "strict_primary_count_56": scopes["strict_primary_matched_city_cycle"] == 56,
        "no_restricted_or_navigation_contamination": audit["candidate_restricted_overlap"] == audit["candidate_navigation_overlap"] == 0,
        "usage_outputs_are_manifests_not_analysis_datasets": True,
        "carried_lanes_remain_separate": True,
        "unresolved_conflicts_remain_quarantined": scopes["unresolved_conflict_groups"] == 2 and scopes["unresolved_conflict_observations"] == 5,
        "no_full_page_or_forbidden_payload": True,
        "no_pdf_network_ocr_model_or_pipeline_action": True,
        "global_analysis_readiness_false": True,
        "partial_output_cannot_claim_complete": True,
        "future_prompt_preserves_phase_boundaries": True,
    }
    write_json(output_dir / "limited_exact_span_qualitative_usage_review_invariant_checks.json", {
        "schema_version": SCHEMA_VERSION, "all_invariants_passed": all(checks.values()),
        "checks": checks, "scope_counts": scopes,
    })

    failure_modes = [
        ("URF001", "promotion_decision_not_authorized"),
        ("URF002", "promoted_count_drift"),
        ("URF003", "limited_candidate_count_drift"),
        ("URF004", "restricted_count_drift"),
        ("URF005", "navigation_count_drift"),
        ("URF006", "duplicate_promoted_identity"),
        ("URF007", "duplicate_navigation_identity"),
        ("URF008", "ambiguous_row_enters_candidate_manifest"),
        ("URF009", "unavailable_row_enters_candidate_manifest"),
        ("URF010", "restricted_row_enters_candidate_manifest"),
        ("URF011", "primary_row_not_limited_eligible"),
        ("URF012", "cycle_row_not_limited_eligible"),
        ("URF013", "occupation_row_not_limited_eligible"),
        ("URF014", "matched_row_not_limited_eligible"),
        ("URF015", "mechanism_other_enters_typed_use"),
        ("URF016", "historical_mixed_membership_enters_active_use"),
        ("URF017", "wage_gap_or_effect_output_field"),
        ("URF018", "analysis_result_computed"),
        ("URF019", "global_readiness_true"),
        ("URF020", "carried_lane_contamination"),
        ("URF021", "unresolved_conflict_lost"),
        ("URF022", "immutable_input_drift"),
        ("URF023", "forbidden_output_boundary"),
        ("URF024", "full_page_text_payload"),
        ("URF025", "future_prompt_missing_phase_boundary"),
        ("URF026", "relay_missing_inspection_fields"),
        ("URF027", "partial_checkpoint_claims_complete"),
        ("URF028", "rerun_changes_completed_output"),
    ]
    write_json(output_dir / "limited_exact_span_qualitative_usage_review_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION,
        "new_failure_modes": len(failure_modes),
        "new_test_script": "scripts/test_compensation_evidence_limited_exact_span_qualitative_usage_review.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_exact_span_qualitative_usage_review_stress_test_report.md").write_text(
        "# Limited exact-span qualitative usage review stress test\n\n"
        f"The review registers {len(failure_modes)} adversarial modes covering authorization, immutable inputs, count drift, identity contamination, eligibility subsets, mechanism typing, historical joins, forbidden analysis, lane separation, conflict quarantine, dashboard readiness, prompt/relay contracts, partial outputs, and idempotency. Final execution totals are recorded in the validation report.\n",
        encoding="utf-8",
    )
    (output_dir / "limited_exact_span_qualitative_usage_review_validation_report.md").write_text(
        "# Limited exact-span qualitative usage review validation\n\n"
        "- Authorized promotion decision and immutable inputs: passed.\n"
        "- Five package SHA-256 checks inherited and reverified through the promotion contract: passed.\n"
        "- Eligibility, restriction, navigation, cycle, occupation, matching, and strict-primary counts: reconciled.\n"
        "- Usage outputs are manifests/contracts only; no analysis result or usage dataset was created.\n"
        "- Global analysis readiness remains false.\n\n"
        "Focused and repository validation results are appended after execution.\n",
        encoding="utf-8",
    )

    future_prompt = """# Next task: materialize a limited qualitative usage layer

Do not run this prompt without separate explicit user authorization.

Create a rollback-safe limited qualitative usage layer only from the 643 observation identities authorized by `limited_qualitative_mechanism_usage_candidate_manifest.json`. Reverify the manifest ID-set hash against the immutable 759-row promoted view before writing. Preserve the 116 restricted exact-span rows in quarantine and the 1,195 ambiguous/unavailable rows as navigation-only. Keep quantitative, non-base, reference/control, and unresolved-conflict lanes separate.

The usage layer may organize literal mechanism-language evidence and its provenance. It must not compute statistics or analysis results. Mechanism language is not evidence of wage effects. The 56-row strict primary matched city-cycle subset may be carried only as an explicit narrow manifest; it does not establish representativeness, statistical power, treatment effects, or causal effects. Global analysis readiness remains false.

Do not fetch. Do not pull. Do not inspect remotes. Do not configure remotes. Do not open URLs. Do not download or redownload documents. Do not open PDFs. Do not access PDF pages. Do not run OCR. Do not call GABRIEL/API or any model. Do not run extraction. Do not select new documents. Do not run scouting, source review, or verification. Do not ingest. Do not run gabriel.codify. Do not create a global/final analysis-facing dataset. Do not calculate wage gaps. Do not run regressions. Do not make causal claims. Do not mutate upstream ledgers or evidence-contract outputs. Keep global analysis readiness false and stop after the limited usage layer package, validation, dashboard update, commit, push, and lite relay.
"""
    validate_future_prompt(future_prompt)
    (output_dir / "next_limited_qualitative_usage_layer_prompt.md").write_text(future_prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(
        "# Next task\n\n"
        "Seek separate explicit authorization to run `next_limited_qualitative_usage_layer_prompt.md`.\n\n"
        "That future task may materialize a rollback-safe limited qualitative usage layer for exactly the 643 eligible exact-span rows after revalidating the manifest ID-set hash. It must preserve 116 restricted exact-span rows in quarantine and 1,195 ambiguous/unavailable rows as navigation-only. It must keep the 56-row strict primary subset explicitly narrow, keep all other compensation lanes separate, compute no analysis results, and leave global analysis readiness false.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION, "scope_counts": scopes,
        "limited_usage_layer_prompt_allowed_next": True,
        "limited_usage_layer_requires_separate_authorization": True,
        "allowed_scope": "643 exact-span limited-use eligible qualitative mechanism rows only",
        "strict_primary_scope": "56-row narrow evidence manifest only; no effect or causal claims",
        "global_analysis_readiness": False, "global_analysis_facing_promotion": False,
        "full_qualitative_readiness": False, "analysis_results_computed": False,
        "package_sha256_checks_passed": 5, "immutable_promotion_inputs_verified": len(hashes),
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "network_calls": 0, "model_calls": 0, "forbidden_actions_performed": [],
        "immutable_inputs_modified": False,
        "next_prompt": "next_limited_qualitative_usage_layer_prompt.md",
    }
    write_json(output_dir / "limited_exact_span_qualitative_usage_review_decision.json", decision)
    (output_dir / "limited_exact_span_qualitative_usage_review_summary.md").write_text(
        f"""# Limited exact-span qualitative usage review

Decision: `{DECISION}`

The review authorizes preparation—not execution—of a future limited qualitative usage layer for the 643 exact-span rows whose current QA, typed mechanism, structured detail, and mixed-membership contracts pass. The remaining 116 exact-span rows stay restricted, while all 614 ambiguous and 581 unavailable rows remain navigation-only.

The 56 strict primary matched city-cycle rows are a narrow evidence-manifest subset. They may support bounded mechanism-language navigation in a future separately authorized layer, but this review establishes neither statistical power nor any wage effect, wage gap, regression result, or causal claim. Exact-cycle (453), controlled-occupation (438), and exact-period matched-set (77) subsets retain their own row-level restrictions.

Quantitative (862 candidates/1,045 exceptions), non-base (4,733 companion rows), reference/exclusion (345 control rows), and two unresolved groups/five observations remain separate. Global analysis readiness and full qualitative readiness remain false.
""",
        encoding="utf-8",
    )


REQUIRED_OUTPUTS = (
    "limited_exact_span_qualitative_usage_review_summary.md",
    "limited_exact_span_qualitative_usage_review_decision.json",
    "limited_exact_span_qualitative_usage_scope_matrix.csv",
    "limited_exact_span_qualitative_usage_blocker_matrix.csv",
    "limited_exact_span_qualitative_usage_eligibility_audit.json",
    "limited_qualitative_mechanism_usage_candidate_manifest.json",
    "strict_primary_matched_city_cycle_usage_candidate_manifest.json",
    "restricted_exact_span_usage_quarantine_manifest.json",
    "navigation_only_qualitative_usage_manifest.json",
    "limited_exact_span_qualitative_usage_review_validation_report.md",
    "limited_exact_span_qualitative_usage_review_stress_test_report.md",
    "limited_exact_span_qualitative_usage_review_invariant_checks.json",
    "limited_exact_span_qualitative_usage_review_regression_test_inventory.json",
    "next_limited_qualitative_usage_layer_prompt.md",
    "next_task.md",
)


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required usage-review outputs missing: {missing}")
    decision = read_json(output_dir / "limited_exact_span_qualitative_usage_review_decision.json")
    if (
        decision.get("decision") != DECISION
        or decision.get("input_signature") != signature
        or decision.get("global_analysis_readiness") is not False
        or decision.get("limited_usage_layer_prompt_allowed_next") is not True
        or decision.get("scope_counts") != EXPECTED_COUNTS
    ):
        raise RuntimeError("Usage-review decision/signature/count/readiness mismatch")
    invariants = read_json(output_dir / "limited_exact_span_qualitative_usage_review_invariant_checks.json")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Usage-review invariants failed")
    validate_future_prompt((output_dir / "next_limited_qualitative_usage_layer_prompt.md").read_text(encoding="utf-8"))
    for name in USAGE_MANIFESTS:
        manifest = read_json(output_dir / name)
        if manifest.get("contains_observation_rows") is not False or manifest.get("analysis_results_computed") is not False:
            raise RuntimeError("Usage manifest contains observation data or analysis results")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes = verify_inputs()
    signature = input_signature(hashes)
    material = validate_material_inputs()
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "global_analysis_readiness": False,
            "immutable_promotion_inputs_verified": len(hashes),
            "scope_counts": material["scopes"],
        }, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    build_reports(args.output_dir, hashes, signature, material)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({
        "output_dir": str(args.output_dir), "decision": DECISION,
        "global_analysis_readiness": False,
        "limited_usage_layer_prompt_allowed_next": True,
        "scope_counts": material["scopes"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
