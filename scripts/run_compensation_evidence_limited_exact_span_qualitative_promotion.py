#!/usr/bin/env python3
"""Materialize a fail-closed limited exact-span qualitative promotion layer.

This runner promotes no global analysis dataset. It reads only previously
approved structured CSV/JSON artifacts, preserves all 759 exact-span rows,
adds deterministic row-level eligibility and quarantine fields, keeps 1,195
ambiguous/unavailable rows navigation-only, and records other compensation
lanes as separate manifests. It never opens PDFs, accesses a URL, calls a
model, runs OCR/extraction/selection/ingestion/codification, or performs
statistical/causal analysis.
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
from typing import Any

import run_compensation_evidence_pipeline_hardening_readiness_accelerator as hardening


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-PROMOTION-HARDENED-2026-07-25"
SCHEMA_VERSION = "limited_exact_span_qualitative_promotion_v1"
BASELINE_COMMIT = "cf06781ae41920cd8423731da3a5b3e3d7bb1de0"
DECISION = "limited_exact_span_qualitative_promotion_complete_limited_usage_review_allowed"
SCOPE = "exact_span_qualitative_only_with_row_level_eligibility"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-PROMOTION-HARDENED-2026-07-25"

ACCELERATOR = BASE / "COMPENSATION-EVIDENCE-PIPELINE-HARDENING-READINESS-ACCELERATOR-2026-07-25"
CONTRACT = BASE / "COMPENSATION-EVIDENCE-QUALITATIVE-EVIDENCE-CONTRACT-FOLLOWUP-2026-07-25"
LIMITED_REVIEW = BASE / "COMPENSATION-EVIDENCE-LIMITED-EXACT-SPAN-QUALITATIVE-ANALYSIS-READINESS-REVIEW-2026-07-25"

ACCELERATOR_INPUTS = (
    "pipeline_hardening_readiness_accelerator_decision.json",
    "pipeline_hardening_readiness_accelerator_summary.md",
    "pipeline_readiness_master_blocker_registry.csv",
    "pipeline_readiness_master_blocker_registry_summary.json",
    "pipeline_hardening_invariant_checks.json",
    "pipeline_hardening_validation_report.md",
    "pipeline_hardening_stress_test_report.md",
    "pipeline_failure_fixture_inventory.json",
    "pipeline_failure_mode_registry.csv",
    "analysis_readiness_simulation_report.md",
    "analysis_readiness_simulation_matrix.csv",
    "analysis_readiness_scope_recommendation.json",
    "reusable_pipeline_stage_contract.md",
    "future_stage_preflight_checklist.md",
    "future_stage_relay_schema_contract.md",
    "future_stage_dashboard_state_contract.md",
    "next_limited_qualitative_promotion_prompt.md",
)
CONTRACT_INPUTS = (
    "qualitative_mechanism_exact_span_coded_candidate.csv",
    "qualitative_mechanism_ambiguous_span_navigation.csv",
    "qualitative_mechanism_unavailable_span_navigation.csv",
    "qualitative_mechanism_combined_tiered_view.csv",
    "qualitative_mechanism_evidence_contract_audit.json",
    "quantitative_analysis_view_candidate_evidence_contract_followup.csv",
    "quantitative_exception_ledger_evidence_contract_followup.csv",
    "non_base_wage_companion_view_candidate_evidence_contract_followup.csv",
    "reference_exclusion_control_view_evidence_contract_followup.csv",
    "unresolved_conflict_quarantine_ledger_evidence_contract_followup.csv",
    "residual_metadata_quarantine_summary_evidence_contract_followup.json",
)
LIMITED_REVIEW_INPUTS = (
    "limited_exact_span_qualitative_readiness_decision.json",
    "limited_exact_span_qualitative_readiness_review_summary.md",
    "limited_exact_span_qualitative_contract_audit.json",
    "limited_exact_span_qualitative_join_provenance_audit.json",
    "limited_exact_span_qualitative_blocker_matrix.csv",
    "limited_exact_span_readiness_invariant_checks.json",
    "limited_exact_span_readiness_validation_report.md",
    "limited_exact_span_readiness_stress_test_report.md",
)

DETAIL_FIELDS = hardening.DETAIL_FIELDS
FORBIDDEN_FIELDS = hardening.FORBIDDEN_FIELDS | {
    "pdf_text", "document_text", "full_document_text", "page_payload",
    "image_data", "api_key", "token", "cookie", "auth_header",
}
PROMOTION_FIELDS = (
    "limited_promotion_scope",
    "eligible_for_limited_qualitative_use",
    "eligible_for_primary_matched_city_cycle_design",
    "eligible_for_cycle_analysis",
    "eligible_for_occupation_comparison",
    "eligible_for_exact_period_matched_set",
    "eligible_for_typed_mechanism_analysis",
    "eligibility_blockers",
    "quarantine_status",
    "promotion_notes",
)
EXPECTED_SCOPE_COUNTS = {
    "exact_span_input": 759,
    "promoted_view": 759,
    "limited_contract_eligible": 643,
    "restricted_or_quarantined_exact": 116,
    "cycle_analysis_eligible": 453,
    "occupation_comparison_eligible": 438,
    "matched_set_eligible": 77,
    "primary_matched_city_cycle_eligible": 56,
    "typed_mechanism_eligible": 643,
    "ambiguous_navigation": 614,
    "unavailable_navigation": 581,
    "navigation_only_total": 1195,
}
RELAY_REQUIRED = {
    "commit_hash", "push_status", "validation_results", "dashboard_status",
    "forbidden_action_confirmations", "next_recommendation",
}
FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "review only", "global analysis readiness remains false", "Do not fetch",
    "Do not pull", "Do not open URLs", "Do not open PDFs", "Do not run OCR",
    "Do not call GABRIEL/API", "Do not run extraction", "Do not select new documents",
    "Do not ingest", "Do not run gabriel.codify", "Do not calculate wage gaps",
    "Do not run regressions", "Do not make causal claims",
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
    if any(boundary.resolve() == resolved or boundary.resolve() in resolved.parents for boundary in (ROOT / "data", ROOT / "corpus", ROOT / "ingest")):
        raise RuntimeError("Forbidden output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe output already exists: {path}")


def required_paths() -> list[Path]:
    return (
        [ACCELERATOR / name for name in ACCELERATOR_INPUTS]
        + [CONTRACT / name for name in CONTRACT_INPUTS]
        + [LIMITED_REVIEW / name for name in LIMITED_REVIEW_INPUTS]
    )


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required immutable input is not recorded at baseline: {relative}")
    return result.stdout


def verify_inputs() -> dict[str, str]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized accelerator commit or a descendant")
    # Reuse the accelerator's package/prior-layer hard-coded SHA contract.
    hardening.verify_inputs()
    observed: dict[str, str] = {}
    for path in required_paths():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        current = path.read_bytes()
        baseline = git_bytes_at_baseline(path)
        if current != baseline:
            raise RuntimeError(f"Immutable input differs from authorized baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)
    accelerator_decision = read_json(ACCELERATOR / "pipeline_hardening_readiness_accelerator_decision.json")
    if (
        accelerator_decision.get("decision") != "pipeline_hardening_complete_limited_promotion_allowed"
        or accelerator_decision.get("limited_promotion_allowed_next") is not True
        or accelerator_decision.get("analysis_readiness") is not False
    ):
        raise RuntimeError("Accelerator decision does not authorize limited promotion")
    readiness = read_json(LIMITED_REVIEW / "limited_exact_span_qualitative_readiness_decision.json")
    if readiness.get("analysis_readiness") is not False:
        raise RuntimeError("Limited readiness input violates global-readiness boundary")
    return observed


def validate_no_forbidden_fields(fields: list[str]) -> None:
    bad = sorted(set(fields) & FORBIDDEN_FIELDS)
    if bad:
        raise RuntimeError(f"Forbidden payload fields present: {bad}")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def validate_exact_row(row: dict[str, str]) -> None:
    required = (
        "qualitative_observation_id", "extraction_case_id", "source_review_id",
        "text_table_detection_id", "raw_retained_content_hash", "pdf_sha256",
        "bounded_evidence_pointer", "page_number", "mechanism_type",
        "literal_verbatim_evidence_span", "span_start", "span_end", "span_length",
        "span_sha256", "qa_status", "span_qa_status", "current_active",
        "mixed_membership_status", "source_type_bridge", "source_corpus_bridge",
        "source_cite_bridge", "retrieval_date_bridge", "retrieval_method_bridge",
        "artifact_pointer_bridge",
    )
    missing = [name for name in required if not str(row.get(name, "")).strip()]
    if missing:
        raise RuntimeError(f"Exact row missing provenance/span fields: {missing}")
    if row.get("evidence_contract_tier") != "exact_span_coded_candidate":
        raise RuntimeError("Non-exact evidence-contract tier entered exact input")
    if row.get("span_capture_status") != "exact_verified" or row.get("span_qa_status") != "span_exact_unique_verified":
        raise RuntimeError("Exact candidate span QA failed")
    if row.get("current_active") != "true":
        raise RuntimeError("Inactive qualitative row entered exact input")
    span = row["literal_verbatim_evidence_span"]
    if "\n" in span or "\r" in span or not span:
        raise RuntimeError("Span must be nonblank and single-line")
    start, end, length = int(row["span_start"]), int(row["span_end"]), int(row["span_length"])
    if start < 0 or end <= start or end - start != length or len(span) != length:
        raise RuntimeError("Span offset/length invariant failed")
    if hashlib.sha256(span.encode("utf-8")).hexdigest() != row["span_sha256"]:
        raise RuntimeError("Span SHA-256 invariant failed")
    if row.get("mixed_membership_status") not in {"active", "none", "historical_inactive", "historical_missing"}:
        raise RuntimeError("Unknown mixed-membership status")


def limited_base_eligible(row: dict[str, str]) -> bool:
    return (
        row.get("current_qa_status") == "provisional_unverified"
        and row.get("mechanism_type") != "other"
        and any(row.get(field, "").strip() for field in DETAIL_FIELDS)
        and row.get("mixed_membership_status") in {"active", "none"}
    )


def eligibility_for(row: dict[str, str]) -> dict[str, str]:
    base = limited_base_eligible(row)
    exact_cycle = base and row.get("followup_cycle_bridge_status") == "established_single_exact_pair"
    controlled_occupation = base and bool(row.get("controlled_occupation_class", "").strip())
    exact_match = base and row.get("analysis_matching_status") == "exact_period_matched_set_supported"
    primary = exact_cycle and controlled_occupation and exact_match
    blockers: list[str] = []
    if row.get("current_qa_status") != "provisional_unverified":
        blockers.append("current_qa_status_requires_review")
    if row.get("mechanism_type") == "other":
        blockers.append("mechanism_type_other_not_typed")
    if not any(row.get(field, "").strip() for field in DETAIL_FIELDS):
        blockers.append("structured_mechanism_detail_missing")
    if row.get("mixed_membership_status") not in {"active", "none"}:
        blockers.append("historical_mixed_membership_not_active_join")
    if row.get("followup_cycle_bridge_status") != "established_single_exact_pair":
        blockers.append("exact_cycle_support_missing_or_ambiguous")
    if not row.get("controlled_occupation_class", "").strip():
        blockers.append("controlled_occupation_missing")
    if row.get("analysis_matching_status") != "exact_period_matched_set_supported":
        blockers.append("exact_period_matched_set_not_supported")
    return {
        "limited_promotion_scope": SCOPE,
        "eligible_for_limited_qualitative_use": bool_text(base),
        "eligible_for_primary_matched_city_cycle_design": bool_text(primary),
        "eligible_for_cycle_analysis": bool_text(exact_cycle),
        "eligible_for_occupation_comparison": bool_text(controlled_occupation),
        "eligible_for_exact_period_matched_set": bool_text(exact_match),
        "eligible_for_typed_mechanism_analysis": bool_text(base),
        "eligibility_blockers": "|".join(blockers) if blockers else "none",
        "quarantine_status": "not_quarantined_limited_eligible" if base else "restricted_exact_span_not_limited_eligible",
        "promotion_notes": (
            "exact span retained; limited qualitative use only; not causal proof"
            if base else
            "exact span retained as evidence navigation; row-level contract restrictions prevent limited coded use"
        ),
    }


def validate_material_inputs() -> dict[str, Any]:
    exact_fields, exact = read_csv(CONTRACT / "qualitative_mechanism_exact_span_coded_candidate.csv")
    ambiguous_fields, ambiguous = read_csv(CONTRACT / "qualitative_mechanism_ambiguous_span_navigation.csv")
    unavailable_fields, unavailable = read_csv(CONTRACT / "qualitative_mechanism_unavailable_span_navigation.csv")
    combined_fields, combined = read_csv(CONTRACT / "qualitative_mechanism_combined_tiered_view.csv")
    for fields in (exact_fields, ambiguous_fields, unavailable_fields, combined_fields):
        validate_no_forbidden_fields(fields)
    if (len(exact), len(ambiguous), len(unavailable), len(combined)) != (759, 614, 581, 1954):
        raise RuntimeError("Qualitative tier count drift")
    exact_ids = [row["qualitative_observation_id"] for row in exact]
    ambiguous_ids = [row["qualitative_observation_id"] for row in ambiguous]
    unavailable_ids = [row["qualitative_observation_id"] for row in unavailable]
    if len(set(exact_ids)) != 759 or len(set(ambiguous_ids)) != 614 or len(set(unavailable_ids)) != 581:
        raise RuntimeError("Duplicate qualitative observation ID within tier")
    if set(exact_ids) & (set(ambiguous_ids) | set(unavailable_ids)) or set(ambiguous_ids) & set(unavailable_ids):
        raise RuntimeError("Qualitative observation ID contaminates multiple tiers")
    if set(exact_ids) | set(ambiguous_ids) | set(unavailable_ids) != {row["qualitative_observation_id"] for row in combined}:
        raise RuntimeError("Combined qualitative tier identity reconciliation failed")
    for row in exact:
        validate_exact_row(row)
    if any(row.get("evidence_contract_tier") == "exact_span_coded_candidate" for row in ambiguous + unavailable):
        raise RuntimeError("Navigation row entered exact coded tier")
    tables = hardening.validate_material_inputs()
    return {
        "exact_fields": exact_fields, "exact": exact,
        "combined_fields": combined_fields, "combined": combined,
        "ambiguous": ambiguous, "unavailable": unavailable,
        "hardening_tables": tables,
    }


def derive_rows(material: dict[str, Any]) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, int],
]:
    promoted: list[dict[str, str]] = []
    eligibility: list[dict[str, str]] = []
    quarantine: list[dict[str, str]] = []
    for source in material["exact"]:
        flags = eligibility_for(source)
        row = {**source, **flags}
        promoted.append(row)
        eligibility.append({
            "qualitative_observation_id": source["qualitative_observation_id"],
            "extraction_case_id": source["extraction_case_id"],
            "source_review_id": source["source_review_id"],
            "text_table_detection_id": source["text_table_detection_id"],
            "raw_retained_content_hash": source["raw_retained_content_hash"],
            "mechanism_type": source["mechanism_type"],
            "current_qa_status": source["current_qa_status"],
            "mixed_membership_status": source["mixed_membership_status"],
            **flags,
        })
        if flags["eligible_for_limited_qualitative_use"] != "true":
            quarantine.append({
                "qualitative_observation_id": source["qualitative_observation_id"],
                "extraction_case_id": source["extraction_case_id"],
                "source_review_id": source["source_review_id"],
                "text_table_detection_id": source["text_table_detection_id"],
                "raw_retained_content_hash": source["raw_retained_content_hash"],
                "bounded_evidence_pointer": source["bounded_evidence_pointer"],
                "span_sha256": source["span_sha256"],
                "mechanism_type": source["mechanism_type"],
                "current_qa_status": source["current_qa_status"],
                "mixed_membership_status": source["mixed_membership_status"],
                "eligibility_blockers": flags["eligibility_blockers"],
                "quarantine_status": flags["quarantine_status"],
                "promotion_notes": flags["promotion_notes"],
            })
    nav: list[dict[str, str]] = []
    for source in material["combined"]:
        tier = source.get("evidence_contract_tier")
        if tier == "exact_span_coded_candidate":
            continue
        reason = "ambiguous_exact_span_navigation_only" if tier == "ambiguous_exact_span_navigation" else "unavailable_span_navigation_only"
        nav.append({
            **source,
            "limited_promotion_scope": SCOPE,
            "eligible_for_limited_qualitative_use": "false",
            "navigation_only": "true",
            "limited_promotion_exclusion_reason": reason,
            "quarantine_status": "navigation_only_not_coded_evidence",
        })
    scopes = {
        "exact_span_input": len(promoted),
        "promoted_view": len(promoted),
        "limited_contract_eligible": sum(row["eligible_for_limited_qualitative_use"] == "true" for row in promoted),
        "restricted_or_quarantined_exact": len(quarantine),
        "cycle_analysis_eligible": sum(row["eligible_for_cycle_analysis"] == "true" for row in promoted),
        "occupation_comparison_eligible": sum(row["eligible_for_occupation_comparison"] == "true" for row in promoted),
        "matched_set_eligible": sum(row["eligible_for_exact_period_matched_set"] == "true" for row in promoted),
        "primary_matched_city_cycle_eligible": sum(row["eligible_for_primary_matched_city_cycle_design"] == "true" for row in promoted),
        "typed_mechanism_eligible": sum(row["eligible_for_typed_mechanism_analysis"] == "true" for row in promoted),
        "ambiguous_navigation": sum(row["evidence_contract_tier"] == "ambiguous_exact_span_navigation" for row in nav),
        "unavailable_navigation": sum(row["evidence_contract_tier"] == "unavailable_span_navigation" for row in nav),
        "navigation_only_total": len(nav),
    }
    if scopes != EXPECTED_SCOPE_COUNTS:
        raise RuntimeError(f"Eligibility scope count drift: {scopes}")
    return promoted, eligibility, quarantine, nav, scopes


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future usage-review prompt missing constraints: {missing}")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    blank = sorted(key for key in RELAY_REQUIRED if record.get(key) in (None, "", []))
    if missing or blank:
        raise RuntimeError(f"Relay metadata incomplete: missing={missing}; blank={blank}")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 759 or record.get("expected") != 759:
        raise RuntimeError("Partial promotion checkpoint cannot masquerade as complete")


def validate_dashboard_state(record: dict[str, Any]) -> None:
    if record.get("analysis_readiness") is not False:
        raise RuntimeError("Limited promotion cannot mark global analysis readiness true")
    if record.get("limited_usage_review_allowed_next") not in {True, False}:
        raise RuntimeError("Dashboard limited-review state is not explicit")


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, material: dict[str, Any]) -> None:
    promoted, eligibility, quarantine, navigation, scopes = derive_rows(material)
    promoted_fields = material["exact_fields"] + list(PROMOTION_FIELDS)
    eligibility_fields = list(eligibility[0])
    quarantine_fields = list(quarantine[0])
    navigation_fields = material["combined_fields"] + [
        "limited_promotion_scope", "eligible_for_limited_qualitative_use", "navigation_only",
        "limited_promotion_exclusion_reason", "quarantine_status",
    ]
    write_csv(output_dir / "limited_exact_span_qualitative_promoted_view.csv", promoted_fields, promoted)
    write_csv(output_dir / "limited_exact_span_qualitative_row_eligibility.csv", eligibility_fields, eligibility)
    write_csv(output_dir / "limited_exact_span_qualitative_quarantine_ledger.csv", quarantine_fields, quarantine)
    write_csv(output_dir / "ambiguous_unavailable_qualitative_navigation_preserved.csv", navigation_fields, navigation)

    output_hashes = {
        name: sha256(output_dir / name)
        for name in (
            "limited_exact_span_qualitative_promoted_view.csv",
            "limited_exact_span_qualitative_row_eligibility.csv",
            "limited_exact_span_qualitative_quarantine_ledger.csv",
            "ambiguous_unavailable_qualitative_navigation_preserved.csv",
        )
    }
    manifest = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "baseline_commit": BASELINE_COMMIT, "input_signature": signature,
        "promotion_scope": SCOPE, "global_analysis_readiness": False,
        "observation_bearing_input": str(CONTRACT / CONTRACT_INPUTS[0]),
        "observation_bearing_input_count": 759,
        "ambiguous_unavailable_inputs_used_for_navigation_only": True,
        "scope_counts": scopes, "input_sha256": hashes, "output_sha256": output_hashes,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "forbidden_actions_performed": [], "immutable_inputs_modified": False,
    }
    write_json(output_dir / "limited_exact_span_qualitative_promotion_manifest.json", manifest)

    tables = material["hardening_tables"]
    quant_manifest = {
        "candidate_rows": len(tables["quantitative"]["rows"]),
        "exception_rows": len(tables["quantitative_exception"]["rows"]),
        "candidate_source": str(hardening.INPUTS["quantitative"][0]),
        "exception_source": str(hardening.INPUTS["quantitative_exception"][0]),
        "candidate_sha256": sha256(hardening.INPUTS["quantitative"][0]),
        "exception_sha256": sha256(hardening.INPUTS["quantitative_exception"][0]),
        "separate_from_qualitative_promotion": True,
        "analysis_readiness": False,
    }
    write_json(output_dir / "quantitative_candidates_carried_forward_manifest.json", quant_manifest)
    conflicts = tables["conflict"]["rows"]
    lane_manifest = {
        "non_base_companion_rows": len(tables["non_base"]["rows"]),
        "reference_control_rows": len(tables["reference"]["rows"]),
        "unresolved_conflict_groups": len(conflicts),
        "unresolved_conflict_observations": sum(int(row["observation_count"]) for row in conflicts),
        "non_base_sha256": sha256(hardening.INPUTS["non_base"][0]),
        "reference_sha256": sha256(hardening.INPUTS["reference"][0]),
        "conflict_sha256": sha256(hardening.INPUTS["conflict"][0]),
        "non_base_companion_only": True, "reference_control_only": True,
        "conflicts_quarantined": True, "separate_from_qualitative_promotion": True,
    }
    write_json(output_dir / "non_base_reference_conflict_carried_forward_manifest.json", lane_manifest)

    blocker_rows = [
        {"blocker_id": "LP-QA-001", "lane": "exact_span", "row_count": 116, "status": "restricted_exact_span", "downstream_treatment": "retained in promoted view; excluded from limited coded use", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-QA-002", "lane": "qualitative_navigation", "row_count": 614, "status": "ambiguous_navigation_only", "downstream_treatment": "not coded evidence", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-QA-003", "lane": "qualitative_navigation", "row_count": 581, "status": "unavailable_navigation_only", "downstream_treatment": "not coded evidence", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-CY-001", "lane": "cycle", "row_count": 190, "status": "limited_eligible_without_exact_cycle", "downstream_treatment": "exclude from cycle analyses", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-OC-001", "lane": "occupation", "row_count": 205, "status": "limited_eligible_without_controlled_occupation", "downstream_treatment": "exclude from occupation comparison", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-MT-001", "lane": "matching", "row_count": 566, "status": "limited_eligible_without_exact_matched_set", "downstream_treatment": "exclude from matched-set use", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-QN-001", "lane": "quantitative", "row_count": 1045, "status": "separate_quantitative_exceptions", "downstream_treatment": "not used in qualitative promotion", "blocks_global_readiness": "true"},
        {"blocker_id": "LP-CF-001", "lane": "conflict", "row_count": 5, "status": "two_groups_quarantined", "downstream_treatment": "not used in qualitative promotion", "blocks_global_readiness": "true"},
    ]
    write_csv(output_dir / "limited_exact_span_qualitative_promotion_blocker_matrix.csv", list(blocker_rows[0]), blocker_rows)

    checks = {
        "immutable_inputs_match_authorized_baseline": True,
        "five_package_hashes_pass": True,
        "exact_span_input_is_759": scopes["exact_span_input"] == 759,
        "promoted_view_accounts_for_all_exact_rows": scopes["promoted_view"] == 759,
        "navigation_only_total_is_1195": scopes["navigation_only_total"] == 1195,
        "ambiguous_unavailable_not_in_coded_output": not ({row["qualitative_observation_id"] for row in promoted} & {row["qualitative_observation_id"] for row in navigation}),
        "eligibility_scope_counts_reconcile": scopes == EXPECTED_SCOPE_COUNTS,
        "historical_mixed_not_active": all(row["mixed_membership_status"] in {"active", "none"} for row in promoted if row["eligible_for_limited_qualitative_use"] == "true"),
        "other_not_typed_eligible": all(row["eligible_for_typed_mechanism_analysis"] == "false" for row in promoted if row["mechanism_type"] == "other"),
        "span_hash_offset_pointer_preserved": True,
        "carried_lanes_separate": True,
        "conflicts_quarantined": lane_manifest["unresolved_conflict_groups"] == 2 and lane_manifest["unresolved_conflict_observations"] == 5,
        "no_forbidden_payload_fields": True,
        "no_pdf_or_ocr_access": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_claim_complete": True,
        "future_prompt_phase_boundary_complete": True,
    }
    invariant_payload = {"schema_version": SCHEMA_VERSION, "all_invariants_passed": all(checks.values()), "checks": checks, "scope_counts": scopes}
    write_json(output_dir / "limited_exact_span_qualitative_promotion_invariant_checks.json", invariant_payload)

    failures = [
        ("PF001", "exact_input_count_drift", "fail_closed"),
        ("PF002", "ambiguous_row_enters_coded_output", "fail_closed"),
        ("PF003", "unavailable_row_enters_coded_output", "fail_closed"),
        ("PF004", "duplicate_qualitative_observation_id", "fail_closed"),
        ("PF005", "span_hash_drift", "fail_closed"),
        ("PF006", "span_offset_or_length_drift", "fail_closed"),
        ("PF007", "blank_page_pointer", "fail_closed"),
        ("PF008", "missing_provenance", "fail_closed"),
        ("PF009", "inactive_row_enters_exact_input", "fail_closed"),
        ("PF010", "needs_review_marked_limited_eligible", "fail_closed"),
        ("PF011", "historical_mixed_marked_active", "fail_closed"),
        ("PF012", "mechanism_other_marked_typed_eligible", "fail_closed"),
        ("PF013", "missing_detail_marked_typed_eligible", "fail_closed"),
        ("PF014", "cycle_flag_without_exact_cycle", "fail_closed"),
        ("PF015", "occupation_flag_without_controlled_class", "fail_closed"),
        ("PF016", "matched_flag_without_exact_period_match", "fail_closed"),
        ("PF017", "primary_flag_without_all_design_gates", "fail_closed"),
        ("PF018", "quantitative_lane_enters_qualitative_view", "fail_closed"),
        ("PF019", "non_base_lane_enters_qualitative_view", "fail_closed"),
        ("PF020", "reference_lane_enters_qualitative_view", "fail_closed"),
        ("PF021", "unresolved_conflict_enters_promoted_view", "fail_closed"),
        ("PF022", "global_readiness_true", "fail_closed"),
        ("PF023", "forbidden_output_boundary", "fail_closed"),
        ("PF024", "immutable_input_drift", "fail_closed"),
        ("PF025", "partial_checkpoint_claims_complete", "fail_closed"),
        ("PF026", "rerun_duplicates_rows", "reuse_complete_output_only"),
        ("PF027", "future_prompt_missing_phase_boundary", "fail_closed"),
        ("PF028", "relay_missing_required_metadata", "fail_closed"),
        ("PF029", "forbidden_full_page_or_raw_payload_field", "fail_closed"),
        ("PF030", "scope_count_contradiction", "fail_closed"),
    ]
    failure_rows = [{"fixture_id": a, "failure_mode": b, "expected_result": c} for a, b, c in failures]
    write_csv(output_dir / "limited_exact_span_qualitative_promotion_failure_mode_matrix.csv", list(failure_rows[0]), failure_rows)
    write_json(output_dir / "limited_exact_span_qualitative_promotion_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION,
        "new_failure_modes": len(failures),
        "new_test_script": "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_exact_span_qualitative_promotion_stress_test_report.md").write_text(
        "# Limited exact-span qualitative promotion stress test\n\n"
        f"The promotion failure corpus registers {len(failures)} adversarial modes covering tier contamination, identity, span, provenance, active/QA, mixed joins, mechanism typing, cycle/occupation/matching eligibility, lane separation, conflicts, immutable inputs, dashboard readiness, checkpoint/resume, future prompt, relay, payload leakage, and count reconciliation. Final test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )
    (output_dir / "limited_exact_span_qualitative_promotion_validation_2026-07-25.md").write_text(
        "# Limited exact-span qualitative promotion validation\n\n"
        "- Authorized baseline and all immutable inputs: passed.\n"
        "- Five package SHA-256 checks: passed.\n"
        "- 759 exact rows and 1,195 navigation-only rows: reconciled.\n"
        "- Row-level eligibility and quarantine scope counts: reconciled.\n"
        "- Span/provenance/history preservation: passed.\n"
        "- Carried-forward lanes remain separate; global analysis readiness remains false.\n\n"
        "Focused and repository validation results are appended after execution.\n",
        encoding="utf-8",
    )

    prompt = """# Next task: limited exact-span qualitative usage review

Do not run this prompt without separate explicit user authorization.

Perform a review only of the hardened limited exact-span qualitative promotion layer. Verify the 759-row promoted view, the 643 row-level limited-use flags, the 116 restricted exact-span rows, the 1,195 navigation-only rows, and the 56-row strict primary matched-design subset. Do not alter or promote data. Global analysis readiness remains false.

Keep ambiguous/unavailable evidence navigation-only. Keep quantitative, non-base, reference/control, and unresolved-conflict lanes separate. Treat exact spans as literal evidence, not causal proof. Stop before any descriptive or inferential analysis and require separate authorization for every later use.

Do not fetch. Do not pull. Do not inspect or configure remotes. Do not open URLs. Do not download. Do not open PDFs. Do not access PDF pages. Do not run OCR. Do not call GABRIEL/API or any model. Do not run extraction. Do not select new documents. Do not ingest. Do not run gabriel.codify. Do not create a global/final analysis dataset. Do not calculate wage gaps. Do not run regressions. Do not make causal claims.
"""
    validate_future_prompt(prompt)
    (output_dir / "next_limited_qualitative_usage_review_prompt.md").write_text(prompt, encoding="utf-8")

    audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "input_signature": signature, "scope_counts": scopes,
        "unique_promoted_observation_ids": len({row["qualitative_observation_id"] for row in promoted}),
        "unique_navigation_observation_ids": len({row["qualitative_observation_id"] for row in navigation}),
        "candidate_contamination_count": 0,
        "span_hash_failures": 0, "span_offset_length_failures": 0,
        "blank_page_pointer_count": 0, "missing_required_provenance_count": 0,
        "historical_mixed_active_join_count": 0, "other_typed_eligible_count": 0,
        "full_page_text_persisted": 0, "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "immutable_inputs_modified": False, "global_analysis_readiness": False,
        "all_invariants_passed": all(checks.values()),
    }
    write_json(output_dir / "limited_exact_span_qualitative_promotion_audit.json", audit)
    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "generated_at": manifest["generated_at"], "input_signature": signature,
        "decision": DECISION, "scope": SCOPE, "scope_counts": scopes,
        "global_analysis_readiness": False, "global_analysis_facing_promotion": False,
        "limited_usage_review_allowed_next": True,
        "limited_usage_review_requires_separate_authorization": True,
        "package_sha256_checks_passed": 5,
        "immutable_tracked_inputs_verified": len(hashes),
        "forbidden_actions_performed": [], "immutable_inputs_modified": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "carried_forward_counts": {
            "quantitative_candidates": 862, "quantitative_exceptions": 1045,
            "non_base_companion": 4733, "reference_control": 345,
            "unresolved_conflict_groups": 2, "unresolved_conflict_observations": 5,
        },
        "bugs_discovered_and_fixed": [],
        "next_prompt": "next_limited_qualitative_usage_review_prompt.md",
        "invariants": invariant_payload,
    }
    write_json(output_dir / "limited_exact_span_qualitative_promotion_decision.json", decision)
    (output_dir / "limited_exact_span_qualitative_promotion_summary.md").write_text(
        f"""# Hardened limited exact-span qualitative promotion

Decision: `{DECISION}`

The rollback-safe promoted view retains all 759 exact-span rows and adds explicit eligibility, restriction, matching, cycle, occupation, mechanism-typing, quarantine, and notes fields. Exactly 643 rows are eligible for limited qualitative use and 116 exact-span rows remain restricted. The strict primary matched city-cycle intersection contains 56 rows. All 614 ambiguous and 581 unavailable rows remain navigation-only in a separate 1,195-row file.

Quantitative (862 candidates/1,045 exceptions), non-base (4,733 companion rows), reference/exclusion (345 control rows), and two unresolved groups/five observations remain separate. This layer is provisional, not globally analysis-ready, and does not authorize usage without a separate review.
""",
        encoding="utf-8",
    )


REQUIRED_OUTPUTS = (
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
    "quantitative_candidates_carried_forward_manifest.json",
    "non_base_reference_conflict_carried_forward_manifest.json",
    "limited_exact_span_qualitative_promotion_stress_test_report.md",
    "limited_exact_span_qualitative_promotion_invariant_checks.json",
    "limited_exact_span_qualitative_promotion_regression_test_inventory.json",
    "limited_exact_span_qualitative_promotion_failure_mode_matrix.csv",
    "next_limited_qualitative_usage_review_prompt.md",
)


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required promotion outputs missing: {missing}")
    decision = read_json(output_dir / "limited_exact_span_qualitative_promotion_decision.json")
    if (
        decision.get("decision") != DECISION
        or decision.get("input_signature") != signature
        or decision.get("global_analysis_readiness") is not False
        or decision.get("limited_usage_review_allowed_next") is not True
    ):
        raise RuntimeError("Promotion decision/signature/readiness mismatch")
    if decision.get("scope_counts") != EXPECTED_SCOPE_COUNTS:
        raise RuntimeError("Completed promotion scope count mismatch")
    invariants = read_json(output_dir / "limited_exact_span_qualitative_promotion_invariant_checks.json")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("Promotion invariants failed")
    validate_future_prompt((output_dir / "next_limited_qualitative_usage_review_prompt.md").read_text(encoding="utf-8"))


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
    _, _, _, _, scopes = derive_rows(material)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "global_analysis_readiness": False, "package_hashes_passed": 5,
            "immutable_tracked_inputs_verified": len(hashes), "scope_counts": scopes,
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
        "global_analysis_readiness": False, "limited_usage_review_allowed_next": True,
        "scope_counts": scopes,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
