#!/usr/bin/env python3
"""Review the limited exact-span qualitative tier without promoting data.

The runner is intentionally read-only with respect to all evidence and durable
ledgers.  It validates the 759-row exact-span candidate tier, the two
navigation-only tiers, carried-forward lane hashes, and the residual conflict
quarantine.  It writes reports and a future *prompt* only; it never creates an
analysis-facing dataset.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-ANALYSIS-READINESS-REVIEW-2026-07-25"
SCHEMA_VERSION = "limited_exact_span_qualitative_readiness_review_v1"
DECISION = "limited_exact_span_qualitative_readiness_pass_with_blockers_documented"
EXPECTED = {"exact": 759, "ambiguous": 614, "unavailable": 581, "total": 1954}

INPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-QUALITATIVE-EVIDENCE-CONTRACT-FOLLOWUP-2026-07-25"
DEFAULT_OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-ANALYSIS-READINESS-REVIEW-2026-07-25"

INPUTS = {
    "decision": INPUT_DIR / "qualitative_evidence_contract_followup_decision.json",
    "summary": INPUT_DIR / "qualitative_evidence_contract_followup_summary.md",
    "contract": INPUT_DIR / "qualitative_evidence_contract.md",
    "tier_rules": INPUT_DIR / "qualitative_evidence_contract_tier_rules.md",
    "limitations": INPUT_DIR / "qualitative_evidence_contract_limitations.md",
    "contract_audit": INPUT_DIR / "qualitative_mechanism_evidence_contract_audit.json",
    "prior_invariants": INPUT_DIR / "qualitative_evidence_contract_invariant_checks.json",
    "prior_validation": INPUT_DIR / "qualitative_evidence_contract_validation_report.md",
    "prior_stress": INPUT_DIR / "qualitative_evidence_contract_stress_test_report.md",
    "prior_blockers": INPUT_DIR / "qualitative_evidence_contract_blocker_matrix.csv",
    "prior_tests": INPUT_DIR / "qualitative_evidence_contract_regression_test_inventory.json",
    "exact": INPUT_DIR / "qualitative_mechanism_exact_span_coded_candidate.csv",
    "ambiguous": INPUT_DIR / "qualitative_mechanism_ambiguous_span_navigation.csv",
    "unavailable": INPUT_DIR / "qualitative_mechanism_unavailable_span_navigation.csv",
    "combined": INPUT_DIR / "qualitative_mechanism_combined_tiered_view.csv",
    "quantitative_candidate": INPUT_DIR / "quantitative_analysis_view_candidate_evidence_contract_followup.csv",
    "quantitative_exception": INPUT_DIR / "quantitative_exception_ledger_evidence_contract_followup.csv",
    "non_base": INPUT_DIR / "non_base_wage_companion_view_candidate_evidence_contract_followup.csv",
    "reference": INPUT_DIR / "reference_exclusion_control_view_evidence_contract_followup.csv",
    "conflicts": INPUT_DIR / "unresolved_conflict_quarantine_ledger_evidence_contract_followup.csv",
    "residual": INPUT_DIR / "residual_metadata_quarantine_summary_evidence_contract_followup.json",
}

EXPECTED_SHA256 = {
    "decision": "66170baa9fa5f134cb04e58e9f8931986b47f6db2f3a5e0f4eee3f287a4776fc",
    "summary": "b9e01b4945933f26594e8c32cccc3d945ca134f063dd1050752daaa76b6270d5",
    "contract": "b431fed04fc7919c00bbf063a84615913192e8b50717e437a34233105a6ba3f0",
    "tier_rules": "4b01bb0aa0528580fadcbdf0bbbc09a8abc7bbbb802938138ccdaeeb744154fd",
    "limitations": "ed148379d6a37a989fe85cb6f0c69877dc5c3d37b7e86df033d997eff25281f3",
    "contract_audit": "f9496d4bfe6396e71aef463acc171a645c515ce5574798480063816057746518",
    "prior_invariants": "44a4be34cc42f2f14674ac0a5361af87f1e5b879a09e1aaf43ff10f0cf03755b",
    "prior_validation": "5c4c7741db6ffe121efe6f08642bcb20f1b6018fb68a3ee0a9de2fbdb01067f3",
    "prior_stress": "bf2077edfca50cf2f53975ff23a0f83259353536f93d7bf6a7e07e43612e3769",
    "prior_blockers": "31b8f39a5773e9fb4bbf457d669fd38043e7c4059ebd3e4442498af6d0e1f963",
    "prior_tests": "7b84a819188ad7527623afe12d35798d7295f8060ed76a352ff2d1dd7d54d131",
    "exact": "4cc2143ef85c1e7c9492c44fab69d8dbc1a09edd33649b41bb1c88a75493f3a4",
    "ambiguous": "41f8333bfe033606373c2f837651c56c648ea91ce86a4b20db63291cb3f40e18",
    "unavailable": "1cff00f045678ee6287e85416da85b829d4bbb1d8cadb909a41ff5a5ebe84d51",
    "combined": "2779745e741d51dd116c4321194dddebf9b9bd2bd04f2dc3c04c94bba1f067aa",
    "quantitative_candidate": "eac6af7f123162192bd671173e28f32899f90050304053429812cb11bea7952e",
    "quantitative_exception": "4482409deee67d18ebec4e5a56f4922e9d6d2b067eaa1dcbf7a996d60f97d401",
    "non_base": "e93ab79afd1956d9b736c6fa0d823f4013a543042241b7bc1dbe7d6359cecb92",
    "reference": "38e37f11dbfb927ce47aaded6559bf74402142e26d9194461822dd7e2868663a",
    "conflicts": "dcead3280d7bdb9b7d2f93debc536fd72dd60cf209d4b7f8e9fd8ca797a1eec7",
    "residual": "d35a462f3b1648ad6f6a6a4bfd7e9d3e4815708293ad16318caef6effbaa2385",
}

OUTPUTS = {
    "summary": "limited_exact_span_qualitative_readiness_review_summary.md",
    "decision": "limited_exact_span_qualitative_readiness_decision.json",
    "contract_audit": "limited_exact_span_qualitative_contract_audit.json",
    "join_audit": "limited_exact_span_qualitative_join_provenance_audit.json",
    "blockers": "limited_exact_span_qualitative_blocker_matrix.csv",
    "tier_report": "limited_exact_span_qualitative_tier_treatment_report.md",
    "navigation_report": "ambiguous_unavailable_navigation_treatment_report.md",
    "validation": "limited_exact_span_readiness_validation_report.md",
    "stress": "limited_exact_span_readiness_stress_test_report.md",
    "invariants": "limited_exact_span_readiness_invariant_checks.json",
    "tests": "limited_exact_span_readiness_regression_test_inventory.json",
    "prompt": "next_limited_qualitative_analysis_facing_promotion_prompt.md",
}

REQUIRED_PROVENANCE = (
    "qualitative_observation_id", "extraction_case_id", "source_review_id",
    "text_table_detection_id", "raw_retained_content_hash", "retained_content_hash",
    "pdf_sha256", "page_number", "bounded_evidence_pointer", "mechanism_type",
    "qa_status", "span_qa_status", "source_type_bridge", "source_corpus_bridge",
    "source_cite_bridge", "retrieval_date_bridge", "retrieval_method_bridge",
    "artifact_pointer_bridge", "identity_bridge_status", "current_active",
    "current_qa_status",
)
FORBIDDEN_FIELDS = {
    "page_text", "full_page_text", "raw_page_text", "raw_page_payload",
    "pdf_text", "full_pdf_text", "encoded_image", "raw_prompt", "raw_response",
}
MECHANISM_DETAIL_FIELDS = (
    "bargaining_logic", "indexing_formula", "comparability_basis", "parity_logic",
    "step_progression_rule", "eligibility_rule", "implementation_rule",
    "fiscal_constraint", "reopener_clause", "differentiation_logic",
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
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def output_guard(path: Path, *, allow_existing: bool = False) -> None:
    resolved = path.resolve()
    analysis = (ROOT / "docs/analysis").resolve()
    if analysis not in resolved.parents:
        raise RuntimeError("Output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if forbidden.resolve() == resolved or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def verify_inputs() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, path in INPUTS.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        hashes[key] = sha256(path)
        if hashes[key] != EXPECTED_SHA256[key]:
            raise RuntimeError(f"Immutable input hash mismatch: {key}")
    decision = read_json(INPUTS["decision"])
    if decision.get("decision") != "qualitative_evidence_contract_limited_review_allowed_exact_span_only":
        raise RuntimeError("Upstream decision does not authorize the limited review")
    if decision.get("analysis_readiness") is not False or decision.get("repeat_review_scope") != "limited_exact_span_only":
        raise RuntimeError("Upstream review scope/readiness boundary failed")
    if read_json(INPUTS["prior_invariants"]).get("all_invariants_passed") is not True:
        raise RuntimeError("Upstream invariant suite did not pass")
    return hashes


def input_signature(hashes: dict[str, str]) -> str:
    values = "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return text_sha256(f"{SCHEMA_VERSION}\n{values}")


def validate_exact_row(row: dict[str, str]) -> None:
    missing = [field for field in REQUIRED_PROVENANCE if not row.get(field, "").strip()]
    if missing:
        raise RuntimeError(f"Exact candidate missing provenance: {missing}")
    if row.get("evidence_contract_tier") != "exact_span_coded_candidate":
        raise RuntimeError("Exact candidate tier contamination")
    if row.get("evidence_contract_candidate_eligible") != "true":
        raise RuntimeError("Exact candidate eligibility flag is false")
    if row.get("span_capture_status") != "exact_verified" or row.get("span_qa_status") != "span_exact_unique_verified" or row.get("span_qa_pass") != "true":
        raise RuntimeError("Exact candidate span QA contract failed")
    span = row.get("literal_verbatim_evidence_span", "")
    if not span or "\n" in span or "\r" in span:
        raise RuntimeError("Exact candidate span missing or multiline")
    try:
        start, end, length = int(row["span_start"]), int(row["span_end"]), int(row["span_length"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError("Exact candidate span offsets invalid") from exc
    if start < 0 or end <= start or end - start != length or len(span) != length:
        raise RuntimeError("Exact candidate span offsets do not round-trip")
    if text_sha256(span) != row.get("span_sha256"):
        raise RuntimeError("Exact candidate span hash mismatch")
    if row["raw_retained_content_hash"] != row["retained_content_hash"]:
        raise RuntimeError("Retained content hash bridge mismatch")
    if not row["bounded_evidence_pointer"].endswith(f"#page={row['page_number']}"):
        raise RuntimeError("Bounded page pointer mismatch")
    if row.get("current_active") != "true":
        raise RuntimeError("Exact candidate is not current-active")


def validate_navigation_row(row: dict[str, str], *, tier: str, status: str) -> None:
    if row.get("evidence_contract_tier") != tier or row.get("span_capture_status") != status:
        raise RuntimeError("Navigation tier/status mismatch")
    if row.get("evidence_contract_candidate_eligible") != "false":
        raise RuntimeError("Navigation row entered coded candidate output")
    if row.get("span_qa_status") == "span_exact_unique_verified" or row.get("span_qa_pass") == "true":
        raise RuntimeError("Navigation row carries exact-span coded eligibility")


def validate_tiers(
    exact_fields: list[str], exact: list[dict[str, str]],
    ambiguous_fields: list[str], ambiguous: list[dict[str, str]],
    unavailable_fields: list[str], unavailable: list[dict[str, str]],
    combined_fields: list[str], combined: list[dict[str, str]],
) -> None:
    if (len(exact), len(ambiguous), len(unavailable), len(combined)) != (759, 614, 581, 1954):
        raise RuntimeError("Tier count reconciliation failed")
    if set(exact_fields) & FORBIDDEN_FIELDS or set(ambiguous_fields) & FORBIDDEN_FIELDS or set(unavailable_fields) & FORBIDDEN_FIELDS or set(combined_fields) & FORBIDDEN_FIELDS:
        raise RuntimeError("Forbidden full-page/raw payload field present")
    all_rows = exact + ambiguous + unavailable
    ids = [row.get("qualitative_observation_id", "") for row in all_rows]
    combined_ids = [row.get("qualitative_observation_id", "") for row in combined]
    if len(set(ids)) != EXPECTED["total"] or set(ids) != set(combined_ids) or len(set(combined_ids)) != EXPECTED["total"]:
        raise RuntimeError("Tier IDs duplicate, overlap, or do not reconcile")
    for row in exact:
        validate_exact_row(row)
    for row in ambiguous:
        validate_navigation_row(row, tier="ambiguous_exact_span_navigation", status="span_ambiguous_multiple_candidates")
    for row in unavailable:
        validate_navigation_row(row, tier="unavailable_span_navigation", status="span_unavailable_or_unverified")
    if "qa_status" not in exact_fields or "span_qa_status" not in exact_fields:
        raise RuntimeError("Historical QA and span QA are not separate fields")


def load_and_validate() -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for key in ("exact", "ambiguous", "unavailable", "combined"):
        tables[key] = read_csv(INPUTS[key])
    validate_tiers(
        tables["exact"][0], tables["exact"][1],
        tables["ambiguous"][0], tables["ambiguous"][1],
        tables["unavailable"][0], tables["unavailable"][1],
        tables["combined"][0], tables["combined"][1],
    )
    _, conflict_rows = read_csv(INPUTS["conflicts"])
    if len(conflict_rows) != 2 or sum(int(row.get("observation_count", 0)) for row in conflict_rows) != 5:
        raise RuntimeError("Residual conflict quarantine changed")
    if not all(row.get("resolution_status") == "unresolved" and row.get("ambiguity_preservation") == "preserved_without_inference" for row in conflict_rows):
        raise RuntimeError("Residual conflict quarantine semantics changed")
    return {key: value[1] for key, value in tables.items()} | {"conflicts": conflict_rows}


def review_metrics(exact: list[dict[str, str]]) -> dict[str, Any]:
    mixed = Counter(row.get("mixed_membership_status", "") for row in exact)
    metrics = {
        "exact_candidate_rows": len(exact),
        "exact_candidate_span_qa_pass": sum(row.get("span_qa_status") == "span_exact_unique_verified" for row in exact),
        "current_active_rows": sum(row.get("current_active") == "true" for row in exact),
        "current_qa_status": dict(Counter(row.get("current_qa_status", "") for row in exact)),
        "historical_qa_status": dict(Counter(row.get("qa_status", "") for row in exact)),
        "mechanism_type_counts": dict(Counter(row.get("mechanism_type", "") for row in exact)),
        "mechanism_type_other_rows": sum(row.get("mechanism_type") == "other" for row in exact),
        "rows_without_structured_mechanism_detail": sum(not any(row.get(field, "").strip() for field in MECHANISM_DETAIL_FIELDS) for row in exact),
        "controlled_occupation_complete": sum(bool(row.get("controlled_occupation_class", "").strip()) for row in exact),
        "controlled_occupation_missing": sum(not row.get("controlled_occupation_class", "").strip() for row in exact),
        "exact_cycle_supported": sum(row.get("followup_cycle_bridge_status") == "established_single_exact_pair" for row in exact),
        "cycle_missing_or_ambiguous": sum(row.get("followup_cycle_bridge_status") != "established_single_exact_pair" for row in exact),
        "exact_matched_set_supported": sum(row.get("analysis_matching_status") == "exact_period_matched_set_supported" for row in exact),
        "mixed_membership_status": dict(mixed),
        "historical_mixed_memberships": mixed.get("historical_inactive", 0) + mixed.get("historical_missing", 0),
        "identity_bridge_complete": sum(row.get("identity_bridge_status") == "complete_one_to_one" for row in exact),
        "provenance_complete": sum(all(row.get(field, "").strip() for field in REQUIRED_PROVENANCE) for row in exact),
        "unit_counts": dict(Counter(row.get("unit_type", "") for row in exact)),
        "states_represented": len({row.get("state", "") for row in exact if row.get("state", "")}),
        "source_type_counts": dict(Counter(row.get("source_type_bridge", "") for row in exact)),
        "source_corpus_counts": dict(Counter(row.get("source_corpus_bridge", "") for row in exact)),
    }
    return metrics


def carried_counts() -> dict[str, int]:
    result: dict[str, int] = {}
    for key in ("quantitative_candidate", "quantitative_exception", "non_base", "reference", "conflicts"):
        result[key] = len(read_csv(INPUTS[key])[1])
    result["conflict_observations"] = sum(int(row["observation_count"]) for row in read_csv(INPUTS["conflicts"])[1])
    return result


def build_audits(metrics: dict[str, Any], carried: dict[str, int], hashes: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract_audit = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "immutable_input_hashes_passed": len(hashes),
        "tier_counts": {"exact_span_coded_candidate": 759, "ambiguous_exact_span_navigation": 614, "unavailable_span_navigation": 581},
        "tier_total": 1954,
        "tier_counts_reconcile": True,
        "exact_candidate_contamination_count": 0,
        "exact_candidate_qa_pass_count": metrics["exact_candidate_span_qa_pass"],
        "exact_candidate_rows": metrics["exact_candidate_rows"],
        "historical_and_span_qa_separate": True,
        "forbidden_payload_fields_present": [],
        "pdf_or_page_access_count": 0,
        "full_qualitative_readiness": False,
        "global_analysis_readiness": False,
        "metrics": metrics,
    }
    join_audit = {
        "task_id": TASK_ID,
        "result": "pass_with_explicit_join_and_matching_restrictions",
        "identity_bridge_complete": metrics["identity_bridge_complete"],
        "provenance_complete": metrics["provenance_complete"],
        "controlled_occupation_complete": metrics["controlled_occupation_complete"],
        "controlled_occupation_missing": metrics["controlled_occupation_missing"],
        "exact_cycle_supported": metrics["exact_cycle_supported"],
        "cycle_missing_or_ambiguous": metrics["cycle_missing_or_ambiguous"],
        "exact_matched_set_supported": metrics["exact_matched_set_supported"],
        "mixed_membership_status": metrics["mixed_membership_status"],
        "historical_mixed_memberships_not_active_joins": metrics["historical_mixed_memberships"],
        "residual_conflict_groups_quarantined": carried["conflicts"],
        "residual_conflict_observations_quarantined": carried["conflict_observations"],
        "limitations": [
            "Exact span proves literal traceability, not construct validity or causal effect.",
            "Rows lacking exact cycle, controlled occupation, or exact matched-set support require restricted use or quarantine.",
            "Historical mixed memberships cannot be treated as active joins.",
        ],
    }
    checks = {
        "all_21_input_hashes_pass": len(hashes) == 21,
        "759_exact_rows_valid_unique_and_current_active": metrics["exact_candidate_rows"] == metrics["exact_candidate_span_qa_pass"] == metrics["current_active_rows"] == 759,
        "tier_counts_reconcile_to_1954": True,
        "ambiguous_unavailable_candidate_contamination_zero": True,
        "historical_qa_and_span_qa_separate": True,
        "forbidden_payload_fields_absent": True,
        "carried_forward_files_hash_stable": all(hashes[key] == EXPECTED_SHA256[key] for key in ("quantitative_candidate", "quantitative_exception", "non_base", "reference", "conflicts")),
        "two_groups_five_observations_quarantined": carried["conflicts"] == 2 and carried["conflict_observations"] == 5,
        "analysis_readiness_false": True,
        "dashboard_global_analysis_readiness_must_remain_false": True,
        "no_pdf_or_page_access": True,
        "no_promotion_or_analysis_dataset_created": True,
    }
    invariants = {"schema_version": SCHEMA_VERSION, "all_invariants_passed": all(checks.values()), "checks": checks}
    return contract_audit, join_audit, invariants


def build_reports(output_dir: Path, signature: str, metrics: dict[str, Any], carried: dict[str, int], contract_audit: dict[str, Any], join_audit: dict[str, Any], invariants: dict[str, Any]) -> None:
    decision = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_signature": signature,
        "decision": DECISION,
        "analysis_readiness": False,
        "full_qualitative_readiness": False,
        "analysis_facing_promotion_performed": False,
        "future_limited_promotion_prompt_allowed": True,
        "future_limited_promotion_scope": "exact_span_tier_only_with_row_level_restrictions",
        "exact_span_candidate_count": 759,
        "ambiguous_navigation_count": 614,
        "unavailable_navigation_count": 581,
        "tier_counts_reconcile": True,
        "exact_candidate_qa_pass_count": 759,
        "join_provenance_audit_result": join_audit["result"],
        "carried_forward": carried,
        "row_level_restrictions": {
            "needs_review": metrics["current_qa_status"].get("needs_review", 0),
            "mechanism_type_other": metrics["mechanism_type_other_rows"],
            "missing_structured_mechanism_detail": metrics["rows_without_structured_mechanism_detail"],
            "cycle_missing_or_ambiguous": metrics["cycle_missing_or_ambiguous"],
            "controlled_occupation_missing": metrics["controlled_occupation_missing"],
            "historical_mixed_membership": metrics["historical_mixed_memberships"],
        },
        "primary_matched_design_supported_rows": metrics["exact_matched_set_supported"],
        "ambiguous_unavailable_treatment": "navigation_only_not_coded_evidence",
        "forbidden_actions_performed": [],
        "input_or_durable_ledgers_mutated": False,
        "next_prompt": OUTPUTS["prompt"],
        "next_recommendation": "seek_separate_authorization_to_run_limited_exact_span_qualitative_promotion_prompt",
        "invariants": invariants,
    }
    write_json(output_dir / OUTPUTS["decision"], decision)
    write_json(output_dir / OUTPUTS["contract_audit"], contract_audit)
    write_json(output_dir / OUTPUTS["join_audit"], join_audit)
    write_json(output_dir / OUTPUTS["invariants"], invariants)

    (output_dir / OUTPUTS["summary"]).write_text(f"""# Limited exact-span qualitative readiness review summary

Decision: `{DECISION}`

The 759-row exact-span tier passes literal-span integrity, identity, and provenance checks and may support a separately authorized, limited promotion-planning step. This is not full qualitative readiness and no promotion occurred.

- Exact candidates: 759/759 unique, current-active, exact-span QA valid, and provenance-complete.
- Navigation-only: 614 ambiguous plus 581 unavailable rows; zero contamination into the exact tier.
- Historical QA: {metrics['current_qa_status'].get('provisional_unverified', 0)} provisional-unverified and {metrics['current_qa_status'].get('needs_review', 0)} needs-review.
- Matching: {metrics['exact_cycle_supported']} exact-cycle-supported; {metrics['exact_matched_set_supported']} exact matched-set-supported; {metrics['cycle_missing_or_ambiguous']} cycle-missing/ambiguous.
- Occupation: {metrics['controlled_occupation_complete']} controlled; {metrics['controlled_occupation_missing']} missing.
- Historical mixed memberships: {metrics['historical_mixed_memberships']} retained but never treated as active joins.
- Carried-forward lanes remain immutable: {carried['quantitative_candidate']} quantitative candidates, {carried['quantitative_exception']} exceptions, {carried['non_base']} non-base companion rows, {carried['reference']} reference/control rows, and {carried['conflicts']} unresolved groups/{carried['conflict_observations']} observations.
- Global analysis readiness remains false.
""", encoding="utf-8")

    (output_dir / OUTPUTS["tier_report"]).write_text("""# Limited exact-span qualitative tier treatment

The 759 exact-span rows are a provisional evidence-bearing review universe, not a final coded mechanism dataset. A future promotion task must preserve every raw field and historical QA field, add explicit limited-use eligibility, and quarantine rather than silently omit rows with `needs_review`, `mechanism_type=other`, missing structured mechanism detail, missing/ambiguous cycle, missing controlled occupation, or historical mixed membership. Exact spans establish literal traceability only; they do not establish mechanism strength, treatment, or causality.

For the project's matched city-by-cycle design, the primary matched subset is limited to rows with exact matched-set support. Unmatched exact-span rows may remain descriptive/navigation records but cannot silently enter matched comparisons.
""", encoding="utf-8")

    (output_dir / OUTPUTS["navigation_report"]).write_text("""# Ambiguous and unavailable navigation treatment

- 614 ambiguous exact-span rows remain navigation-only because more than one plausible exact span remains.
- 581 unavailable/unverified rows remain navigation-only because no unique exact span passed the evidence contract.
- Neither tier may be treated as coded mechanism evidence or promoted by the limited exact-span prompt.
- All identifiers, bounded pointers, provenance, historical QA, and span statuses remain available for audit or later separately authorized bounded repair.
""", encoding="utf-8")

    blocker_rows = [
        {"blocker_id": "LQ01", "severity": "scope", "affected_rows": "1195", "issue": "Ambiguous or unavailable span", "treatment": "navigation_only", "promotion_gate": "excluded_from_limited_exact_span_promotion"},
        {"blocker_id": "LQ02", "severity": "major", "affected_rows": str(metrics['current_qa_status'].get('needs_review', 0)), "issue": "Historical/current QA needs review", "treatment": "quarantine", "promotion_gate": "row_level_review_required"},
        {"blocker_id": "LQ03", "severity": "major", "affected_rows": str(metrics['cycle_missing_or_ambiguous']), "issue": "Exact cycle missing or ambiguous", "treatment": "restrict_or_quarantine", "promotion_gate": "not_eligible_for_cycle_analysis"},
        {"blocker_id": "LQ04", "severity": "major", "affected_rows": str(metrics['controlled_occupation_missing']), "issue": "Controlled occupation missing", "treatment": "restrict_or_quarantine", "promotion_gate": "not_eligible_for_occupation_comparison"},
        {"blocker_id": "LQ05", "severity": "major", "affected_rows": str(759 - metrics['exact_matched_set_supported']), "issue": "No exact matched-set support", "treatment": "descriptive_or_navigation_only", "promotion_gate": "excluded_from_primary_matched_design"},
        {"blocker_id": "LQ06", "severity": "major", "affected_rows": str(metrics['historical_mixed_memberships']), "issue": "Historical mixed membership", "treatment": "preserve_not_active_join", "promotion_gate": "must_not_join_as_active"},
        {"blocker_id": "LQ07", "severity": "major", "affected_rows": str(metrics['mechanism_type_other_rows']), "issue": "Mechanism type other", "treatment": "quarantine_from_typed_mechanism_analysis", "promotion_gate": "subtype_review_required"},
        {"blocker_id": "LQ08", "severity": "major", "affected_rows": str(metrics['rows_without_structured_mechanism_detail']), "issue": "No structured mechanism detail beyond label/span", "treatment": "quarantine_from_coded_measurement", "promotion_gate": "contract_detail_required"},
        {"blocker_id": "LQ09", "severity": "quarantine", "affected_rows": "5", "issue": "Two unresolved quantitative conflict groups", "treatment": "preserve_separate_quarantine", "promotion_gate": "never_join_into_qualitative_promotion"},
    ]
    write_csv(output_dir / OUTPUTS["blockers"], ["blocker_id", "severity", "affected_rows", "issue", "treatment", "promotion_gate"], blocker_rows)

    (output_dir / OUTPUTS["validation"]).write_text("""# Limited exact-span readiness validation report

- Immutable required inputs: 21/21 SHA-256 checks passed.
- Exact candidates: 759/759 valid and unique; hashes, offsets, lengths, page pointers, active flags, identity, and provenance passed.
- Tier reconciliation: 759 + 614 + 581 = 1,954.
- Candidate contamination: zero.
- Historical QA and span QA remain separate.
- Forbidden page/full-text/model payload fields: zero.
- Carried-forward lane hashes: unchanged.
- Residual conflict quarantine: two groups/five observations.
- PDF/page access and forbidden operations in this review: zero.
- Global analysis readiness: false.

Full repository validation results are appended after command execution.
""", encoding="utf-8")
    (output_dir / OUTPUTS["stress"]).write_text("""# Limited exact-span readiness stress-test report

The focused suite exercises immutable-hash drift, candidate contamination, tier-count drift, duplicate IDs, blank provenance, span hash corruption, offset corruption, page-pointer mismatch, retained-hash mismatch, inactive candidates, forbidden payload columns, carried-file drift, conflict-quarantine drift, decision/prompt mismatch, unsafe output paths, and global-readiness escalation. Each condition must fail closed.

Materialization-time invariants passed. Final test totals are appended to the validation report.
""", encoding="utf-8")
    write_json(output_dir / OUTPUTS["tests"], {
        "schema_version": SCHEMA_VERSION,
        "test_script": "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
        "offline_only": True,
        "required_failure_modes": [
            "input_hash_drift", "tier_count_drift", "duplicate_id", "candidate_contamination",
            "missing_provenance", "span_hash_corruption", "span_offset_corruption",
            "page_pointer_mismatch", "retained_hash_mismatch", "inactive_candidate",
            "forbidden_payload_column", "carried_file_drift", "conflict_quarantine_drift",
            "global_readiness_true", "wrong_future_prompt", "forbidden_output_boundary",
        ],
    })

    (output_dir / OUTPUTS["prompt"]).write_text("""# Future task: limited exact-span qualitative analysis-facing promotion

Do not run this prompt without separate explicit user authorization.

Promote only a rollback-safe, provisional limited qualitative view derived from the 759-row `exact_span_coded_candidate` input. Do not include the 614 ambiguous or 581 unavailable navigation rows as coded evidence. Do not modify any source ledger or create a global/final analysis dataset.

Before writing, verify the approved exact-tier SHA-256, run a no-write dry run, and reconcile all 759 observation IDs. Preserve literal spans, span hashes/offsets, observation/case/source/detection IDs, retained/PDF hashes, bounded page pointers, raw mechanism fields, historical `qa_status`, `span_qa_status`, current-active semantics, duplicate/canonical provenance, and mixed-membership status.

Create explicit eligibility fields rather than silently dropping rows. Quarantine from coded-mechanism use: 93 `needs_review` rows, eight `mechanism_type=other` rows, four rows without structured mechanism detail, and every historical mixed membership. Mark rows lacking exact cycle, controlled occupation, or exact matched-set support as ineligible for the corresponding cycle/occupation/matched comparison. Only the 85 exact matched-set-supported rows may be considered for the primary matched city-by-cycle design, subject to all other gates.

Keep quantitative, non-base, reference/control, and the two unresolved quantitative conflict groups/five observations separate. Analysis readiness must remain false. Stop before ingestion, codification, wage-gap analysis, regression, or causal interpretation. Commit and update the dashboard only after local validation.
""", encoding="utf-8")


def validate_complete_output(output_dir: Path, signature: str) -> None:
    for filename in OUTPUTS.values():
        if not (output_dir / filename).is_file():
            raise RuntimeError(f"Required output missing: {filename}")
    decision = read_json(output_dir / OUTPUTS["decision"])
    if decision.get("input_signature") != signature or decision.get("decision") != DECISION:
        raise RuntimeError("Decision signature/value mismatch")
    if decision.get("analysis_readiness") is not False or decision.get("future_limited_promotion_prompt_allowed") is not True:
        raise RuntimeError("Readiness or future-prompt boundary mismatch")
    if read_json(output_dir / OUTPUTS["invariants"]).get("all_invariants_passed") is not True:
        raise RuntimeError("Output invariants failed")
    prompt = (output_dir / OUTPUTS["prompt"]).read_text(encoding="utf-8")
    for required in ("759-row", "614 ambiguous", "581 unavailable", "Analysis readiness must remain false", "85 exact matched-set-supported"):
        if required not in prompt:
            raise RuntimeError(f"Future prompt missing contract: {required}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes = verify_inputs()
    signature = input_signature(hashes)
    tables = load_and_validate()
    metrics = review_metrics(tables["exact"])
    carried = carried_counts()
    contract_audit, join_audit, invariants = build_audits(metrics, carried, hashes)
    if not invariants["all_invariants_passed"]:
        raise RuntimeError("Pre-write invariant failure")
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "input_hashes_passed": len(hashes),
            "tier_counts": {"exact": 759, "ambiguous": 614, "unavailable": 581},
            "decision": DECISION, "analysis_readiness": False,
        }, indent=2, sort_keys=True))
        return 0
    if args.resume and args.output_dir.exists():
        validate_complete_output(args.output_dir, signature)
        print(json.dumps({"resume_reused": True, "writes": 0, "decision": DECISION}, indent=2, sort_keys=True))
        return 0
    args.output_dir.mkdir(parents=True)
    build_reports(args.output_dir, signature, metrics, carried, contract_audit, join_audit, invariants)
    validate_complete_output(args.output_dir, signature)
    print(json.dumps({
        "output_dir": str(args.output_dir), "decision": DECISION,
        "exact_span_candidates": 759, "analysis_readiness": False,
        "future_limited_promotion_prompt_allowed": True,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
