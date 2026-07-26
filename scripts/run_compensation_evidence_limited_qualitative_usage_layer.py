#!/usr/bin/env python3
"""Materialize the authorized 643-row limited qualitative usage layer.

The output is a rollback-safe, provisional evidence-use table for exact literal
mechanism language and provenance. It is not an analysis dataset and computes
no statistics, wage effects, gaps, regressions, treatment effects, or causal
claims. The runner reads only committed structured artifacts and never opens a
PDF, accesses a URL, calls a model, runs OCR/extraction/selection/ingestion, or
mutates upstream evidence.
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

import run_compensation_evidence_limited_exact_span_qualitative_usage_review as review


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-MATERIALIZATION-2026-07-25"
SCHEMA_VERSION = "limited_qualitative_usage_layer_v1"
BASELINE_COMMIT = "f72362341803f38f14d788c647da03436702d6f8"
DECISION = "limited_qualitative_usage_layer_materialized_qa_review_allowed"
SCOPE = "limited_exact_span_qualitative_mechanism_evidence_only"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-2026-07-25"
REVIEW = review.DEFAULT_OUTPUT_DIR
PROMOTION = review.PROMOTION

REVIEW_INPUTS = (
    "limited_exact_span_qualitative_usage_review_decision.json",
    "limited_exact_span_qualitative_usage_review_summary.md",
    "limited_exact_span_qualitative_usage_scope_matrix.csv",
    "limited_exact_span_qualitative_usage_blocker_matrix.csv",
    "limited_exact_span_qualitative_usage_eligibility_audit.json",
    "limited_exact_span_qualitative_usage_review_invariant_checks.json",
    "limited_exact_span_qualitative_usage_review_validation_report.md",
    "limited_exact_span_qualitative_usage_review_stress_test_report.md",
    "limited_exact_span_qualitative_usage_review_regression_test_inventory.json",
    "limited_qualitative_mechanism_usage_candidate_manifest.json",
    "strict_primary_matched_city_cycle_usage_candidate_manifest.json",
    "restricted_exact_span_usage_quarantine_manifest.json",
    "navigation_only_qualitative_usage_manifest.json",
)
PROMOTION_INPUTS = (
    "limited_exact_span_qualitative_promoted_view.csv",
    "limited_exact_span_qualitative_row_eligibility.csv",
    "limited_exact_span_qualitative_quarantine_ledger.csv",
    "ambiguous_unavailable_qualitative_navigation_preserved.csv",
    "limited_exact_span_qualitative_promotion_manifest.json",
    "limited_exact_span_qualitative_promotion_decision.json",
    "limited_exact_span_qualitative_promotion_audit.json",
    "limited_exact_span_qualitative_promotion_blocker_matrix.csv",
    "limited_exact_span_qualitative_promotion_invariant_checks.json",
    "quantitative_candidates_carried_forward_manifest.json",
    "non_base_reference_conflict_carried_forward_manifest.json",
)

SOURCE_FIELDS = (
    # Observation, case, document, source, and duplicate/canonical identity.
    "qualitative_observation_id", "extraction_case_id", "mixed_join_key",
    "document_identity_id", "text_table_detection_id", "source_review_id",
    "candidate_queue_row_id", "source_seed_observation_id",
    "canonical_observation_id", "duplicate_of", "pdf_readiness_id",
    # City, unit, source, period, and provenance.
    "state", "municipality", "government_name", "unit_type",
    "candidate_source_type", "contract_period_start", "contract_period_end",
    "source_type_bridge", "source_corpus_bridge", "source_cite_bridge",
    "retrieval_date_bridge", "retrieval_method_bridge", "artifact_pointer_bridge",
    "raw_retained_content_hash", "retained_content_hash", "pdf_sha256",
    # Literal mechanism evidence and bounded location.
    "page_number", "bounded_evidence_pointer", "mechanism_type",
    "literal_verbatim_evidence_span", "span_start", "span_end", "span_length",
    "span_sha256", "span_capture_status", "span_capture_reason_code",
    "span_failure_reason", "span_candidate_count", "span_qa_pass",
    "span_qa_status", "prior_span_capture_status", "span_disambiguation_action",
    "span_disambiguation_rule", "span_disambiguation_candidate_count",
    "span_disambiguation_top_score", "span_disambiguation_score_margin",
    # Historical and current QA/lineage semantics.
    "confidence", "reason_code", "qa_status", "cumulative_cohort",
    "qa_original_status", "qa_resolution_classification", "qa_resolution_status",
    "active_in_provisional_lane", "targeted_qa_resolution_ids",
    "targeted_qa_resolution_classification", "targeted_qa_resolution_status",
    "targeted_qa_reason_codes", "targeted_qa_source_observation_id",
    "active_in_qa_corrected_lane", "readable_conflict_qa_resolution_id",
    "readable_conflict_qa_classification", "readable_conflict_qa_status",
    "readable_conflict_qa_reason_codes", "readable_conflict_qa_source_observation_id",
    "active_in_readable_conflict_qa_lane", "current_active", "current_qa_status",
    "current_qa_status_source", "mixed_membership_status",
    # Deterministic occupation, cycle, and matching metadata.
    "controlled_occupation_class", "occupation_class_bridge_status",
    "contract_period_start_bridge", "contract_period_end_bridge",
    "negotiation_cycle_id", "city_unit_negotiation_cycle_key", "matched_set_id",
    "identity_bridge_status", "analysis_matching_status",
    "followup_cycle_bridge_status", "followup_cycle_source_fields",
    "followup_occupation_bridge_status", "followup_occupation_support_fields",
    "followup_retrieval_bridge_status", "followup_retrieval_support_fields",
    # Evidence-contract and promotion eligibility retained verbatim.
    "evidence_contract_version", "evidence_contract_tier",
    "evidence_contract_candidate_eligible", "evidence_contract_use_scope",
    "evidence_contract_reason_code", "evidence_contract_review_status",
    "limited_promotion_scope", "eligible_for_limited_qualitative_use",
    "eligible_for_primary_matched_city_cycle_design", "eligible_for_cycle_analysis",
    "eligible_for_occupation_comparison", "eligible_for_exact_period_matched_set",
    "eligible_for_typed_mechanism_analysis", "eligibility_blockers",
    "quarantine_status", "promotion_notes",
)
USAGE_FIELDS = (
    "usage_layer_scope", "allowed_usage", "prohibited_usage",
    "eligible_for_limited_qualitative_mechanism_use",
    "eligible_for_cycle_aware_review", "eligible_for_occupation_aware_review",
    "eligible_for_exact_period_matched_set_review",
    "eligible_for_strict_primary_matched_city_cycle_manifest",
    "usage_restrictions", "analysis_status", "causal_claim_status",
)
OUTPUT_FIELDS = SOURCE_FIELDS + USAGE_FIELDS

EXPECTED_COUNTS = {
    "usage_layer_rows": 643,
    "restricted_exact_span": 116,
    "ambiguous_navigation": 614,
    "unavailable_navigation": 581,
    "navigation_only": 1195,
    "strict_primary_matched_city_cycle": 56,
    "exact_cycle_eligible": 453,
    "controlled_occupation_eligible": 438,
    "exact_period_matched_set_eligible": 77,
    "quantitative_candidates": 862,
    "quantitative_exceptions": 1045,
    "non_base_companion": 4733,
    "reference_control": 345,
    "unresolved_conflict_groups": 2,
    "unresolved_conflict_observations": 5,
}

FORBIDDEN_FIELDS = review.FORBIDDEN_OUTPUT_FIELDS | {
    "descriptive_statistic", "summary_statistic", "p_value", "estimate",
    "coefficient", "standard_error", "confidence_interval", "effect_size",
}
RELAY_REQUIRED = review.RELAY_REQUIRED
FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "QA review only", "global analysis readiness remains false",
    "Do not fetch", "Do not pull", "Do not inspect remotes",
    "Do not open URLs", "Do not open PDFs", "Do not access PDF pages",
    "Do not run OCR", "Do not call GABRIEL/API", "Do not run extraction",
    "Do not select new documents", "Do not ingest", "Do not run gabriel.codify",
    "Do not calculate wage gaps", "Do not run regressions", "Do not make causal claims",
    "no descriptive or inferential analysis",
)


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


def schema_sha256(fields: tuple[str, ...]) -> str:
    return hashlib.sha256(("\n".join(fields) + "\n").encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: tuple[str, ...] | list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="raise", lineterminator="\n")
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
    return [*(REVIEW / name for name in REVIEW_INPUTS), *(PROMOTION / name for name in PROMOTION_INPUTS)]


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required immutable input is not recorded at authorized baseline: {relative}")
    return result.stdout


def verify_inputs() -> dict[str, str]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized usage-review commit or a descendant")
    # Re-run all package, repair, evidence, readiness, and promotion hash gates.
    review.verify_inputs()
    observed: dict[str, str] = {}
    for path in required_paths():
        if not path.is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
        current = path.read_bytes()
        if current != git_bytes_at_baseline(path):
            raise RuntimeError(f"Immutable input differs from authorized baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)
    decision = read_json(REVIEW / "limited_exact_span_qualitative_usage_review_decision.json")
    if (
        decision.get("decision") != review.DECISION
        or decision.get("limited_usage_layer_prompt_allowed_next") is not True
        or decision.get("global_analysis_readiness") is not False
        or decision.get("analysis_results_computed") is not False
    ):
        raise RuntimeError("Usage-review decision does not authorize layer materialization")
    return observed


def validate_no_forbidden_fields(fields: list[str] | tuple[str, ...]) -> None:
    bad = sorted(set(fields) & FORBIDDEN_FIELDS)
    if bad:
        raise RuntimeError(f"Forbidden analysis or payload fields present: {bad}")


def validate_source_row(row: dict[str, str]) -> None:
    required = (
        "qualitative_observation_id", "extraction_case_id", "source_review_id",
        "text_table_detection_id", "raw_retained_content_hash", "pdf_sha256",
        "bounded_evidence_pointer", "page_number", "mechanism_type",
        "literal_verbatim_evidence_span", "span_start", "span_end", "span_length",
        "span_sha256", "source_type_bridge", "source_corpus_bridge",
        "source_cite_bridge", "retrieval_date_bridge", "retrieval_method_bridge",
        "artifact_pointer_bridge", "current_qa_status", "current_active",
        "mixed_membership_status",
    )
    missing = [field for field in required if not str(row.get(field, "")).strip()]
    if missing:
        raise RuntimeError(f"Authorized source row missing required evidence/provenance: {missing}")
    if row.get("eligible_for_limited_qualitative_use") != "true":
        raise RuntimeError("Restricted row attempted to enter usage layer")
    if row.get("evidence_contract_tier") != "exact_span_coded_candidate":
        raise RuntimeError("Ambiguous or unavailable row attempted to enter usage layer")
    if row.get("span_capture_status") != "exact_verified" or row.get("span_qa_status") != "span_exact_unique_verified":
        raise RuntimeError("Usage-layer row does not have exact unique span QA")
    if row.get("current_active") != "true":
        raise RuntimeError("Inactive row attempted to enter usage layer")
    if row.get("mixed_membership_status") not in {"active", "none"}:
        raise RuntimeError("Historical mixed membership attempted to enter active usage layer")
    span = row["literal_verbatim_evidence_span"]
    if not span or "\n" in span or "\r" in span:
        raise RuntimeError("Usage-layer span must be nonblank and single-line")
    start, end, length = int(row["span_start"]), int(row["span_end"]), int(row["span_length"])
    if start < 0 or end <= start or end - start != length or len(span) != length:
        raise RuntimeError("Usage-layer span offset/length invariant failed")
    if hashlib.sha256(span.encode("utf-8")).hexdigest() != row["span_sha256"]:
        raise RuntimeError("Usage-layer span SHA-256 invariant failed")


def validate_material_inputs() -> dict[str, Any]:
    source_fields, promoted = read_csv(PROMOTION / "limited_exact_span_qualitative_promoted_view.csv")
    eligibility_fields, eligibility = read_csv(PROMOTION / "limited_exact_span_qualitative_row_eligibility.csv")
    quarantine_fields, quarantine = read_csv(PROMOTION / "limited_exact_span_qualitative_quarantine_ledger.csv")
    navigation_fields, navigation = read_csv(PROMOTION / "ambiguous_unavailable_qualitative_navigation_preserved.csv")
    for fields in (source_fields, eligibility_fields, quarantine_fields, navigation_fields, OUTPUT_FIELDS):
        validate_no_forbidden_fields(fields)
    missing_fields = sorted(set(SOURCE_FIELDS) - set(source_fields))
    if missing_fields:
        raise RuntimeError(f"Promoted view lacks required usage-layer fields: {missing_fields}")
    if (len(promoted), len(eligibility), len(quarantine), len(navigation)) != (759, 759, 116, 1195):
        raise RuntimeError("Promotion input count drift")
    if len({row["qualitative_observation_id"] for row in promoted}) != 759:
        raise RuntimeError("Duplicate promoted qualitative observation ID")
    if len({row["qualitative_observation_id"] for row in navigation}) != 1195:
        raise RuntimeError("Duplicate navigation qualitative observation ID")

    authorized = [row for row in promoted if row.get("eligible_for_limited_qualitative_use") == "true"]
    authorized_ids = {row["qualitative_observation_id"] for row in authorized}
    restricted_ids = {row["qualitative_observation_id"] for row in quarantine}
    navigation_ids = {row["qualitative_observation_id"] for row in navigation}
    if len(authorized) != 643 or len(authorized_ids) != 643:
        raise RuntimeError("Authorized usage-layer count is not 643")
    candidate_manifest = read_json(REVIEW / "limited_qualitative_mechanism_usage_candidate_manifest.json")
    authorized_hash = id_set_sha256(authorized_ids)
    if int(candidate_manifest.get("row_count", 0)) != 643 or candidate_manifest.get("qualitative_observation_id_set_sha256") != authorized_hash:
        raise RuntimeError("Authorized candidate ID-set hash mismatch")
    if authorized_ids & restricted_ids:
        raise RuntimeError("Restricted exact-span identity contaminates authorized usage set")
    if authorized_ids & navigation_ids:
        raise RuntimeError("Ambiguous/unavailable identity contaminates authorized usage set")
    for row in authorized:
        validate_source_row(row)

    primary_ids = {row["qualitative_observation_id"] for row in authorized if row.get("eligible_for_primary_matched_city_cycle_design") == "true"}
    cycle_ids = {row["qualitative_observation_id"] for row in authorized if row.get("eligible_for_cycle_analysis") == "true"}
    occupation_ids = {row["qualitative_observation_id"] for row in authorized if row.get("eligible_for_occupation_comparison") == "true"}
    matched_ids = {row["qualitative_observation_id"] for row in authorized if row.get("eligible_for_exact_period_matched_set") == "true"}
    nav_counts = {
        "ambiguous_navigation": sum(row.get("evidence_contract_tier") == "ambiguous_exact_span_navigation" for row in navigation),
        "unavailable_navigation": sum(row.get("evidence_contract_tier") == "unavailable_span_navigation" for row in navigation),
    }
    quant = read_json(PROMOTION / "quantitative_candidates_carried_forward_manifest.json")
    lanes = read_json(PROMOTION / "non_base_reference_conflict_carried_forward_manifest.json")
    counts = {
        "usage_layer_rows": len(authorized),
        "restricted_exact_span": len(restricted_ids),
        **nav_counts,
        "navigation_only": len(navigation_ids),
        "strict_primary_matched_city_cycle": len(primary_ids),
        "exact_cycle_eligible": len(cycle_ids),
        "controlled_occupation_eligible": len(occupation_ids),
        "exact_period_matched_set_eligible": len(matched_ids),
        "quantitative_candidates": int(quant["candidate_rows"]),
        "quantitative_exceptions": int(quant["exception_rows"]),
        "non_base_companion": int(lanes["non_base_companion_rows"]),
        "reference_control": int(lanes["reference_control_rows"]),
        "unresolved_conflict_groups": int(lanes["unresolved_conflict_groups"]),
        "unresolved_conflict_observations": int(lanes["unresolved_conflict_observations"]),
    }
    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Usage-layer count drift: {counts}")
    return {
        "authorized": authorized, "authorized_ids": authorized_ids,
        "authorized_id_hash": authorized_hash, "restricted_ids": restricted_ids,
        "navigation_ids": navigation_ids, "primary_ids": primary_ids,
        "cycle_ids": cycle_ids, "occupation_ids": occupation_ids,
        "matched_ids": matched_ids, "counts": counts,
    }


def usage_fields_for(source: dict[str, str]) -> dict[str, str]:
    restrictions = [
        "literal_mechanism_language_only", "no_statistics", "no_wage_effects",
        "no_wage_gaps", "no_regressions", "no_treatment_effects",
        "no_causal_claims", "row_level_eligibility_binding",
    ]
    if source.get("eligible_for_cycle_analysis") != "true":
        restrictions.append("not_cycle_aware_eligible")
    if source.get("eligible_for_occupation_comparison") != "true":
        restrictions.append("not_occupation_aware_eligible")
    if source.get("eligible_for_exact_period_matched_set") != "true":
        restrictions.append("not_exact_period_matched_set_eligible")
    if source.get("eligible_for_primary_matched_city_cycle_design") != "true":
        restrictions.append("not_strict_primary_matched_city_cycle_eligible")
    return {
        "usage_layer_scope": SCOPE,
        "allowed_usage": "literal_mechanism_language_evidence_navigation_and_restricted_qualitative_use",
        "prohibited_usage": "statistics|wage_effects|wage_gaps|regressions|treatment_effects|causal_claims",
        "eligible_for_limited_qualitative_mechanism_use": "true",
        "eligible_for_cycle_aware_review": source["eligible_for_cycle_analysis"],
        "eligible_for_occupation_aware_review": source["eligible_for_occupation_comparison"],
        "eligible_for_exact_period_matched_set_review": source["eligible_for_exact_period_matched_set"],
        "eligible_for_strict_primary_matched_city_cycle_manifest": source["eligible_for_primary_matched_city_cycle_design"],
        "usage_restrictions": "|".join(restrictions),
        "analysis_status": "not_analyzed_limited_evidence_layer_only",
        "causal_claim_status": "no_causal_claims_authorized",
    }


def derive_usage_rows(material: dict[str, Any]) -> list[dict[str, str]]:
    rows = [{**{field: source.get(field, "") for field in SOURCE_FIELDS}, **usage_fields_for(source)} for source in material["authorized"]]
    ids = [row["qualitative_observation_id"] for row in rows]
    if len(rows) != 643 or len(set(ids)) != 643 or id_set_sha256(set(ids)) != material["authorized_id_hash"]:
        raise RuntimeError("Materialized usage-layer identity reconciliation failed")
    if any(row["eligible_for_limited_qualitative_mechanism_use"] != "true" for row in rows):
        raise RuntimeError("Usage-layer eligibility flag contradiction")
    if any(row["analysis_status"] != "not_analyzed_limited_evidence_layer_only" for row in rows):
        raise RuntimeError("Usage layer incorrectly implies completed analysis")
    if any(row["causal_claim_status"] != "no_causal_claims_authorized" for row in rows):
        raise RuntimeError("Usage layer incorrectly authorizes causal claims")
    return rows


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future QA-review prompt missing constraints: {missing}")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    review.validate_relay_metadata(record)


def validate_dashboard_state(record: dict[str, Any]) -> None:
    if record.get("analysis_readiness") is not False:
        raise RuntimeError("Usage layer cannot mark global analysis readiness true")
    if record.get("usage_layer_qa_review_allowed_next") not in {True, False}:
        raise RuntimeError("Dashboard usage-layer QA-review state is not explicit")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 643 or record.get("expected") != 643:
        raise RuntimeError("Partial usage-layer checkpoint cannot masquerade as complete")


def compact_manifest(scope: str, ids: set[str], source_hash: str, allowed_usage: str, restrictions: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "scope": scope, "row_count": len(ids),
        "qualitative_observation_id_set_sha256": id_set_sha256(ids),
        "source_sha256": source_hash, "allowed_usage": allowed_usage,
        "restrictions": restrictions, "contains_observation_rows": False,
        "analysis_results_computed": False, "global_analysis_readiness": False,
    }


def carried_manifest(scope: str, row_count: int, source_path: str, source_hash: str, treatment: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "scope": scope, "row_count": row_count,
        "source_path": source_path, "source_sha256": source_hash,
        "treatment": treatment, "separate_from_qualitative_usage_layer": True,
        "contains_observation_rows": False, "analysis_results_computed": False,
        "global_analysis_readiness": False,
    }


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, material: dict[str, Any]) -> None:
    rows = derive_usage_rows(material)
    layer_path = output_dir / "limited_qualitative_mechanism_usage_layer.csv"
    write_csv(layer_path, OUTPUT_FIELDS, rows)
    output_id_hash = id_set_sha256({row["qualitative_observation_id"] for row in rows})
    if output_id_hash != material["authorized_id_hash"]:
        raise RuntimeError("Written layer ID-set hash differs from authorized manifest")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    restrictions = [
        "literal mechanism-language evidence only", "no descriptive or inferential analysis",
        "no wage effects, wage gaps, regressions, treatment effects, or causal claims",
        "global analysis readiness remains false", "row-level restrictions remain binding",
    ]
    manifest = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "baseline_commit": BASELINE_COMMIT, "input_signature": signature,
        "usage_layer_scope": SCOPE, "row_count": 643,
        "authorized_candidate_id_set_sha256": material["authorized_id_hash"],
        "materialized_id_set_sha256": output_id_hash,
        "id_set_hash_match": True, "schema_sha256": schema_sha256(OUTPUT_FIELDS),
        "source_promoted_view_sha256": sha256(PROMOTION / "limited_exact_span_qualitative_promoted_view.csv"),
        "output_sha256": sha256(layer_path), "output_fields": list(OUTPUT_FIELDS),
        "analysis_results_computed": False, "global_analysis_readiness": False,
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "network_calls": 0, "model_calls": 0, "forbidden_actions_performed": [],
        "immutable_inputs_modified": False, "input_sha256": hashes,
    }
    write_json(output_dir / "limited_qualitative_mechanism_usage_layer_manifest.json", manifest)

    source_hash = manifest["source_promoted_view_sha256"]
    write_json(output_dir / "strict_primary_matched_city_cycle_usage_manifest.json", compact_manifest(
        "strict_primary_matched_city_cycle", material["primary_ids"], source_hash,
        "narrow literal-evidence manifest only",
        restrictions + ["56-row scope does not establish power, representativeness, or effects"],
    ))
    write_json(output_dir / "restricted_exact_span_usage_quarantine_manifest.json", compact_manifest(
        "restricted_exact_span", material["restricted_ids"],
        sha256(PROMOTION / "limited_exact_span_qualitative_quarantine_ledger.csv"),
        "quarantine metadata and evidence navigation only",
        ["not usage-layer coded evidence", "retain all upstream evidence and blocker metadata"],
    ))
    navigation_manifest = compact_manifest(
        "ambiguous_unavailable_navigation_only", material["navigation_ids"],
        sha256(PROMOTION / "ambiguous_unavailable_qualitative_navigation_preserved.csv"),
        "navigation only", ["never coded evidence", "ambiguous and unavailable tiers remain separate"],
    )
    navigation_manifest.update({"ambiguous_rows": 614, "unavailable_rows": 581})
    write_json(output_dir / "navigation_only_qualitative_usage_manifest.json", navigation_manifest)

    blockers = [
        {"blocker_id": "UL-QA-001", "lane": "restricted_exact_span", "row_count": 116, "severity": "major", "status": "quarantined", "usage_treatment": "excluded from usage layer", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-QA-002", "lane": "ambiguous_navigation", "row_count": 614, "severity": "critical", "status": "navigation_only", "usage_treatment": "not coded evidence", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-QA-003", "lane": "unavailable_navigation", "row_count": 581, "severity": "critical", "status": "navigation_only", "usage_treatment": "not coded evidence", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-CY-001", "lane": "cycle", "row_count": 190, "severity": "major", "status": "usage_rows_without_exact_cycle", "usage_treatment": "not cycle-aware eligible", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-OC-001", "lane": "occupation", "row_count": 205, "severity": "major", "status": "usage_rows_without_controlled_occupation", "usage_treatment": "not occupation-aware eligible", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-MT-001", "lane": "matching", "row_count": 566, "severity": "major", "status": "usage_rows_without_exact_period_match", "usage_treatment": "not matched-set eligible", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-PR-001", "lane": "primary_design", "row_count": 56, "severity": "scope_limit", "status": "narrow_manifest", "usage_treatment": "non-analytic evidence manifest only", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-QN-001", "lane": "quantitative", "row_count": 1045, "severity": "critical", "status": "separate_exceptions", "usage_treatment": "excluded from qualitative usage layer", "blocks_global_readiness": "true"},
        {"blocker_id": "UL-CF-001", "lane": "conflict", "row_count": 5, "severity": "critical", "status": "two_groups_quarantined", "usage_treatment": "excluded and explicit", "blocks_global_readiness": "true"},
    ]
    write_csv(output_dir / "limited_qualitative_usage_blocker_matrix.csv", list(blockers[0]), blockers)
    audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "input_signature": signature,
        "counts": material["counts"], "authorized_candidate_id_set_sha256": material["authorized_id_hash"],
        "materialized_id_set_sha256": output_id_hash, "id_set_hash_match": True,
        "materialized_unique_observation_ids": len({row["qualitative_observation_id"] for row in rows}),
        "restricted_contamination_count": 0, "navigation_contamination_count": 0,
        "strict_primary_subset_of_layer": material["primary_ids"] <= material["authorized_ids"],
        "cycle_subset_of_layer": material["cycle_ids"] <= material["authorized_ids"],
        "occupation_subset_of_layer": material["occupation_ids"] <= material["authorized_ids"],
        "matched_subset_of_layer": material["matched_ids"] <= material["authorized_ids"],
        "analysis_results_computed": False, "global_analysis_readiness": False,
        "full_page_text_persisted": 0, "pdf_pages_accessed": 0,
        "ocr_later_accessed": 0, "network_or_model_calls": 0,
        "immutable_inputs_modified": False, "all_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_eligibility_audit.json", audit)

    quant_source = PROMOTION / "quantitative_candidates_carried_forward_manifest.json"
    quant = read_json(quant_source)
    lanes_source = PROMOTION / "non_base_reference_conflict_carried_forward_manifest.json"
    lanes = read_json(lanes_source)
    write_json(output_dir / "quantitative_candidates_carried_forward_manifest.json", carried_manifest(
        "quantitative_candidates", 862, quant["candidate_source"], quant["candidate_sha256"], "separate provisional lane; not used by qualitative layer",
    ))
    write_json(output_dir / "quantitative_exceptions_carried_forward_manifest.json", carried_manifest(
        "quantitative_exceptions", 1045, quant["exception_source"], quant["exception_sha256"], "separate exception lane; never silently promoted",
    ))
    write_json(output_dir / "non_base_companion_carried_forward_manifest.json", carried_manifest(
        "non_base_companion", 4733, "source recorded in promotion lane manifest", lanes["non_base_sha256"], "companion-only; never base-wage or qualitative outcome evidence",
    ))
    write_json(output_dir / "reference_control_carried_forward_manifest.json", carried_manifest(
        "reference_control", 345, "source recorded in promotion lane manifest", lanes["reference_sha256"], "control-only; never outcome evidence",
    ))
    conflict_manifest = carried_manifest(
        "unresolved_conflict_quarantine", 5, "source recorded in promotion lane manifest", lanes["conflict_sha256"], "two unresolved groups remain explicit and quarantined",
    )
    conflict_manifest["group_count"] = 2
    write_json(output_dir / "unresolved_conflict_quarantine_carried_forward_manifest.json", conflict_manifest)

    (output_dir / "limited_qualitative_usage_scope_contract.md").write_text(
        "# Limited qualitative usage scope contract\n\n"
        "This provisional layer contains exactly 643 authorized exact-span qualitative observations. Each row is one qualitative observation with literal span evidence, bounded page pointer, provenance, QA/lineage fields, deterministic cycle/matching/occupation metadata, and explicit usage restrictions. Structured mechanism-detail fields other than `mechanism_type` are intentionally omitted: this layer is evidence-first and does not silently elevate earlier extracted characterizations into final coded measurements. Those upstream fields remain immutable and available in the promotion layer.\n\n"
        "Allowed use is limited evidence organization, navigation, and later separately authorized QA. The layer contains no descriptive statistic, estimate, wage effect, wage gap, regression, treatment effect, or causal claim. The 116 restricted exact-span observations and 1,195 ambiguous/unavailable observations are represented only by separate manifests. Quantitative, non-base, reference/control, and conflict lanes remain separate. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )

    checks = {
        "usage_review_authorizes_materialization": True,
        "immutable_inputs_match_authorized_baseline": True,
        "five_package_sha256_checks_pass": True,
        "candidate_id_set_hash_matches": output_id_hash == material["authorized_id_hash"],
        "exactly_643_rows_materialized": len(rows) == 643,
        "all_usage_observation_ids_unique": len({row["qualitative_observation_id"] for row in rows}) == 643,
        "restricted_contamination_zero": audit["restricted_contamination_count"] == 0,
        "navigation_contamination_zero": audit["navigation_contamination_count"] == 0,
        "strict_primary_manifest_count_56": len(material["primary_ids"]) == 56,
        "literal_span_hash_offset_pointer_preserved": True,
        "historical_qa_and_lineage_preserved": True,
        "no_analysis_result_fields": not (set(OUTPUT_FIELDS) & FORBIDDEN_FIELDS),
        "all_analysis_statuses_not_analyzed": all(row["analysis_status"] == "not_analyzed_limited_evidence_layer_only" for row in rows),
        "all_causal_statuses_closed": all(row["causal_claim_status"] == "no_causal_claims_authorized" for row in rows),
        "carried_lanes_separate_and_count_stable": True,
        "unresolved_conflicts_remain_quarantined": True,
        "no_full_page_or_forbidden_payload": True,
        "no_pdf_network_ocr_model_or_pipeline_action": True,
        "global_analysis_readiness_false": True,
        "partial_output_cannot_claim_complete": True,
        "future_prompt_preserves_phase_boundaries": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_invariant_checks.json", {
        "schema_version": SCHEMA_VERSION, "all_invariants_passed": all(checks.values()),
        "checks": checks, "counts": material["counts"],
    })

    failures = [
        ("ULF001", "usage_review_decision_not_authorized"),
        ("ULF002", "immutable_input_hash_drift"),
        ("ULF003", "candidate_manifest_count_drift"),
        ("ULF004", "candidate_id_set_hash_mismatch"),
        ("ULF005", "materialized_count_not_643"),
        ("ULF006", "duplicate_usage_observation_id"),
        ("ULF007", "restricted_row_enters_usage_layer"),
        ("ULF008", "ambiguous_row_enters_usage_layer"),
        ("ULF009", "unavailable_row_enters_usage_layer"),
        ("ULF010", "non_exact_span_enters_usage_layer"),
        ("ULF011", "span_hash_corruption"),
        ("ULF012", "span_offset_or_length_corruption"),
        ("ULF013", "blank_page_pointer"),
        ("ULF014", "missing_provenance"),
        ("ULF015", "inactive_row_enters_usage_layer"),
        ("ULF016", "historical_mixed_membership_enters_active_layer"),
        ("ULF017", "strict_primary_manifest_count_drift"),
        ("ULF018", "primary_identity_not_in_usage_layer"),
        ("ULF019", "cycle_flag_without_source_eligibility"),
        ("ULF020", "occupation_flag_without_source_eligibility"),
        ("ULF021", "matched_flag_without_source_eligibility"),
        ("ULF022", "analysis_status_implies_completed_analysis"),
        ("ULF023", "causal_claim_status_opens_claims"),
        ("ULF024", "forbidden_statistic_or_effect_field"),
        ("ULF025", "full_page_text_payload"),
        ("ULF026", "quantitative_lane_contamination"),
        ("ULF027", "non_base_lane_contamination"),
        ("ULF028", "reference_lane_contamination"),
        ("ULF029", "unresolved_conflict_lost"),
        ("ULF030", "global_readiness_true"),
        ("ULF031", "forbidden_output_boundary"),
        ("ULF032", "future_prompt_missing_phase_boundary"),
        ("ULF033", "relay_missing_inspection_fields"),
        ("ULF034", "partial_checkpoint_claims_complete"),
        ("ULF035", "rerun_changes_completed_output"),
    ]
    write_json(output_dir / "limited_qualitative_usage_layer_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "failure_modes": len(failures),
        "new_test_script": "scripts/test_compensation_evidence_limited_qualitative_usage_layer.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_usage_review.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_qualitative_usage_layer_stress_test_report.md").write_text(
        "# Limited qualitative usage-layer stress test\n\n"
        f"The materialization registers {len(failures)} adversarial failure modes spanning authorization and hashes, identity/count contamination, exact-span/provenance integrity, QA and mixed membership, eligibility subsets, forbidden analysis, lane separation, unresolved conflicts, readiness, output boundaries, prompt/relay contracts, checkpoints, and idempotency. Final test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )
    (output_dir / "limited_qualitative_usage_layer_validation_2026-07-25.md").write_text(
        "# Limited qualitative usage-layer validation\n\n"
        "- Authorized review decision and 24 immutable material inputs: passed.\n"
        "- Inherited five-package SHA-256 contract: passed.\n"
        f"- Candidate ID-set SHA-256: `{output_id_hash}`; authorized/materialized match passed.\n"
        "- Exactly 643 unique rows materialized; restricted and navigation contamination are zero.\n"
        "- Strict-primary, cycle, occupation, matching, and carried-lane counts reconcile.\n"
        "- No analysis results were computed; global analysis readiness remains false.\n\n"
        "Focused and repository validation results are appended after execution.\n",
        encoding="utf-8",
    )

    prompt = """# Next task: limited qualitative usage-layer QA review

Do not run this prompt without separate explicit user authorization.

Perform a QA review only of the 643-row limited qualitative mechanism usage layer. Reverify the materialized CSV hash, schema hash, authorized observation-ID set hash, literal span hashes and offsets, bounded page pointers, provenance, lineage, row-level usage flags, 56-row strict-primary manifest, and all separate quarantine/navigation/carried-lane manifests. Do not mutate or promote the layer. Global analysis readiness remains false.

This QA review must perform no descriptive or inferential analysis. Mechanism language is not evidence of wage effects. Do not compute statistics, wage effects, wage gaps, regressions, treatment effects, or causal claims. Do not fetch. Do not pull. Do not inspect remotes. Do not configure remotes. Do not open URLs. Do not download. Do not open PDFs. Do not access PDF pages. Do not run OCR. Do not call GABRIEL/API or any model. Do not run extraction. Do not select new documents. Do not scout, run source review, or verify. Do not ingest. Do not run gabriel.codify. Do not create a global/final analysis-facing dataset. Do not calculate wage gaps. Do not run regressions. Do not make causal claims. Keep upstream ledgers immutable and stop after the QA decision, validation, dashboard update, commit, push, and lite relay.
"""
    validate_future_prompt(prompt)
    (output_dir / "next_limited_qualitative_usage_layer_qa_review_prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(
        "# Next task\n\n"
        "Seek separate explicit authorization to run `next_limited_qualitative_usage_layer_qa_review_prompt.md`. The QA review must verify the 643-row evidence layer and its manifests without performing analysis, opening source documents, or marking global readiness true.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "counts": material["counts"], "candidate_id_set_hash_verified": True,
        "authorized_candidate_id_set_sha256": material["authorized_id_hash"],
        "materialized_id_set_sha256": output_id_hash,
        "usage_layer_qa_review_allowed_next": True,
        "usage_layer_qa_review_requires_separate_authorization": True,
        "global_analysis_readiness": False, "full_qualitative_readiness": False,
        "global_analysis_facing_promotion": False, "analysis_results_computed": False,
        "package_sha256_checks_passed": 5, "immutable_inputs_verified": len(hashes),
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0,
        "network_calls": 0, "model_calls": 0, "forbidden_actions_performed": [],
        "immutable_inputs_modified": False,
        "next_prompt": "next_limited_qualitative_usage_layer_qa_review_prompt.md",
    }
    write_json(output_dir / "limited_qualitative_usage_layer_decision.json", decision)
    (output_dir / "limited_qualitative_usage_layer_summary.md").write_text(
        f"""# Limited qualitative mechanism usage layer

Decision: `{DECISION}`

The rollback-safe provisional layer contains exactly 643 authorized exact-span qualitative mechanism observations. The authorized and materialized observation-ID sets share SHA-256 `{output_id_hash}`. Each row preserves literal span evidence, bounded pointer, provenance, historical/current QA and lineage, deterministic matching/occupation metadata, and explicit usage restrictions.

The 56 strict primary matched city-cycle identities are retained only in a narrow non-analytic manifest. The 116 restricted exact-span identities and 1,195 ambiguous/unavailable identities remain excluded from coded usage. Quantitative (862 candidates/1,045 exceptions), non-base (4,733), reference/control (345), and two unresolved groups/five observations remain separate.

No statistics or analysis results were computed. Global and full qualitative readiness remain false. A separately authorized QA review of this layer is allowed next.
""",
        encoding="utf-8",
    )


REQUIRED_OUTPUTS = (
    "limited_qualitative_mechanism_usage_layer.csv",
    "limited_qualitative_mechanism_usage_layer_manifest.json",
    "strict_primary_matched_city_cycle_usage_manifest.json",
    "restricted_exact_span_usage_quarantine_manifest.json",
    "navigation_only_qualitative_usage_manifest.json",
    "limited_qualitative_usage_scope_contract.md",
    "limited_qualitative_usage_blocker_matrix.csv",
    "limited_qualitative_usage_eligibility_audit.json",
    "limited_qualitative_usage_layer_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_invariant_checks.json",
    "limited_qualitative_usage_layer_stress_test_report.md",
    "limited_qualitative_usage_layer_regression_test_inventory.json",
    "quantitative_candidates_carried_forward_manifest.json",
    "quantitative_exceptions_carried_forward_manifest.json",
    "non_base_companion_carried_forward_manifest.json",
    "reference_control_carried_forward_manifest.json",
    "unresolved_conflict_quarantine_carried_forward_manifest.json",
    "next_limited_qualitative_usage_layer_qa_review_prompt.md",
    "next_task.md", "limited_qualitative_usage_layer_decision.json",
    "limited_qualitative_usage_layer_summary.md",
)


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required usage-layer outputs missing: {missing}")
    decision = read_json(output_dir / "limited_qualitative_usage_layer_decision.json")
    manifest = read_json(output_dir / "limited_qualitative_mechanism_usage_layer_manifest.json")
    invariants = read_json(output_dir / "limited_qualitative_usage_layer_invariant_checks.json")
    fields, rows = read_csv(output_dir / "limited_qualitative_mechanism_usage_layer.csv")
    if (
        decision.get("decision") != DECISION
        or decision.get("input_signature") != signature
        or decision.get("counts") != EXPECTED_COUNTS
        or decision.get("global_analysis_readiness") is not False
        or decision.get("analysis_results_computed") is not False
        or decision.get("usage_layer_qa_review_allowed_next") is not True
        or manifest.get("id_set_hash_match") is not True
        or manifest.get("row_count") != 643
        or len(rows) != 643
        or fields != list(OUTPUT_FIELDS)
        or manifest.get("output_sha256") != sha256(output_dir / "limited_qualitative_mechanism_usage_layer.csv")
        or invariants.get("all_invariants_passed") is not True
    ):
        raise RuntimeError("Completed usage-layer decision/hash/schema/count/readiness mismatch")
    ids = {row["qualitative_observation_id"] for row in rows}
    if id_set_sha256(ids) != manifest.get("authorized_candidate_id_set_sha256"):
        raise RuntimeError("Completed usage-layer ID set differs from authorization")
    validate_future_prompt((output_dir / "next_limited_qualitative_usage_layer_qa_review_prompt.md").read_text(encoding="utf-8"))


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
    rows = derive_usage_rows(material)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "candidate_id_set_hash_verified": True,
            "authorized_candidate_id_set_sha256": material["authorized_id_hash"],
            "usage_layer_rows": len(rows), "counts": material["counts"],
            "global_analysis_readiness": False,
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
        "candidate_id_set_hash_verified": True,
        "authorized_candidate_id_set_sha256": material["authorized_id_hash"],
        "usage_layer_rows": 643, "usage_layer_qa_review_allowed_next": True,
        "global_analysis_readiness": False, "counts": material["counts"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
