#!/usr/bin/env python3
"""Independently QA-review the immutable 643-row qualitative usage layer.

This runner reads committed structured artifacts only. It writes review audits,
contracts, and decision documents into a new rollback-safe docs/analysis path.
It never opens source PDFs/pages, accesses the network, calls a model, runs an
extraction or ingestion stage, computes descriptive/inferential statistics, or
mutates the reviewed usage layer or any upstream evidence artifact.
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

import run_compensation_evidence_limited_qualitative_usage_layer as layer


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-QA-REVIEW-2026-07-25"
SCHEMA_VERSION = "limited_qualitative_usage_layer_qa_review_v1"
BASELINE_COMMIT = "b6f97c0e172c7d285438aa4038eac8e7a9aa27cb"
DECISION = "limited_qualitative_usage_layer_qa_pass_acceptance_prompt_allowed"
AUTHORIZED_ID_HASH = "0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b"
LAYER = layer.DEFAULT_OUTPUT_DIR
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-LIMITED-QUALITATIVE-USAGE-LAYER-QA-REVIEW-2026-07-25"

REQUIRED_INPUTS = (
    "limited_qualitative_mechanism_usage_layer.csv",
    "limited_qualitative_usage_layer_decision.json",
    "limited_qualitative_usage_layer_summary.md",
    "limited_qualitative_usage_layer_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_invariant_checks.json",
    "limited_qualitative_usage_layer_stress_test_report.md",
    "limited_qualitative_usage_layer_regression_test_inventory.json",
    "limited_qualitative_mechanism_usage_layer_manifest.json",
    "limited_qualitative_usage_eligibility_audit.json",
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
    "next_limited_qualitative_usage_layer_qa_review_prompt.md",
)

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

REQUIRED_ROW_FIELDS = (
    "qualitative_observation_id", "extraction_case_id", "source_review_id",
    "text_table_detection_id", "raw_retained_content_hash", "retained_content_hash",
    "pdf_sha256", "bounded_evidence_pointer", "page_number", "mechanism_type",
    "literal_verbatim_evidence_span", "span_start", "span_end", "span_length",
    "span_sha256", "qa_status", "current_qa_status", "current_active",
    "usage_layer_scope", "allowed_usage", "prohibited_usage", "usage_restrictions",
    "analysis_status", "causal_claim_status",
)

FORBIDDEN_OUTPUT_FIELDS = layer.FORBIDDEN_FIELDS | {
    "mean", "median", "mode", "variance", "correlation", "frequency_table",
    "descriptive_summary", "analysis_summary", "wage_effect", "causal_link",
}

FUTURE_PROMPT_REQUIRED = (
    "Do not run this prompt without separate explicit user authorization",
    "acceptance/registration only", "global analysis readiness remains false",
    "Do not compute descriptive or inferential statistics",
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


def id_set_sha256(ids: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode("utf-8")).hexdigest()


def schema_sha256(fields: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256(("\n".join(fields) + "\n").encode("utf-8")).hexdigest()


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
        raise RuntimeError("QA-review output must remain under docs/analysis")
    for forbidden in (ROOT / "data", ROOT / "corpus", ROOT / "ingest"):
        if forbidden.resolve() == resolved or forbidden.resolve() in resolved.parents:
            raise RuntimeError("Forbidden QA-review output boundary")
    if path.exists() and not allow_existing:
        raise FileExistsError(f"Rollback-safe QA-review output already exists: {path}")


def git_bytes_at_baseline(path: Path) -> bytes:
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Required reviewed input is absent at authorized baseline: {relative}")
    return result.stdout


def verify_inputs() -> dict[str, str]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if ancestor.returncode:
        raise RuntimeError("Current commit is not the authorized usage-layer commit or a descendant")

    # Re-run the full package/repair/promotion/materialization chain before review.
    material_hashes = layer.verify_inputs()
    material_signature = layer.input_signature(material_hashes)
    layer.validate_complete_output(LAYER, material_signature)

    observed: dict[str, str] = {}
    for name in REQUIRED_INPUTS:
        path = LAYER / name
        if not path.is_file():
            raise FileNotFoundError(f"Required usage-layer input missing: {path}")
        current = path.read_bytes()
        if current != git_bytes_at_baseline(path):
            raise RuntimeError(f"Immutable usage-layer input differs from authorized baseline: {path}")
        observed[path.resolve().relative_to(ROOT.resolve()).as_posix()] = bytes_sha256(current)

    decision = read_json(LAYER / "limited_qualitative_usage_layer_decision.json")
    if (
        decision.get("decision") != layer.DECISION
        or decision.get("usage_layer_qa_review_allowed_next") is not True
        or decision.get("global_analysis_readiness") is not False
        or decision.get("analysis_results_computed") is not False
    ):
        raise RuntimeError("Materialization decision does not authorize this QA review")
    return observed


def validate_no_forbidden_fields(fields: list[str] | tuple[str, ...]) -> None:
    bad = sorted(set(fields) & FORBIDDEN_OUTPUT_FIELDS)
    if bad:
        raise RuntimeError(f"Forbidden analysis or page-payload fields present: {bad}")


def validate_row(row: dict[str, str]) -> None:
    missing = [field for field in REQUIRED_ROW_FIELDS if not str(row.get(field, "")).strip()]
    if missing:
        raise RuntimeError(f"Usage-layer row missing evidence/provenance/restriction fields: {missing}")
    if row.get("evidence_contract_tier") != "exact_span_coded_candidate":
        raise RuntimeError("Non-exact evidence tier entered usage layer")
    if row.get("span_capture_status") != "exact_verified" or row.get("span_qa_status") != "span_exact_unique_verified":
        raise RuntimeError("Usage-layer span does not have exact unique QA")
    if row.get("current_active") != "true":
        raise RuntimeError("Inactive row entered usage layer")
    if row.get("mixed_membership_status") not in {"active", "none"}:
        raise RuntimeError("Historical mixed membership entered active usage layer")
    if row.get("eligible_for_limited_qualitative_mechanism_use") != "true":
        raise RuntimeError("Usage-layer row is not explicitly limited-use eligible")
    if row.get("analysis_status") != "not_analyzed_limited_evidence_layer_only":
        raise RuntimeError("Usage-layer row implies completed analysis")
    if row.get("causal_claim_status") != "no_causal_claims_authorized":
        raise RuntimeError("Usage-layer row authorizes causal claims")
    prohibited = set(row.get("prohibited_usage", "").split("|"))
    required_prohibitions = {"statistics", "wage_effects", "wage_gaps", "regressions", "treatment_effects", "causal_claims"}
    if not required_prohibitions <= prohibited:
        raise RuntimeError("Usage-layer row omits a required prohibited-use restriction")
    span = row["literal_verbatim_evidence_span"]
    if not span or "\n" in span or "\r" in span:
        raise RuntimeError("Literal span must be nonblank and single-line")
    start, end, length = int(row["span_start"]), int(row["span_end"]), int(row["span_length"])
    if start < 0 or end <= start or end - start != length or len(span) != length:
        raise RuntimeError("Span offsets/length do not round-trip")
    if hashlib.sha256(span.encode("utf-8")).hexdigest() != row["span_sha256"]:
        raise RuntimeError("Span SHA-256 does not match literal span")
    if not row["bounded_evidence_pointer"].strip() or int(row["page_number"]) < 1:
        raise RuntimeError("Bounded page pointer is invalid")


def input_signature(hashes: dict[str, str]) -> str:
    payload = SCHEMA_VERSION + "\n" + "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_future_prompt(text: str) -> None:
    normalized = text.casefold()
    missing = [phrase for phrase in FUTURE_PROMPT_REQUIRED if phrase.casefold() not in normalized]
    if missing:
        raise RuntimeError(f"Future acceptance prompt missing constraints: {missing}")


def validate_relay_metadata(record: dict[str, Any]) -> None:
    missing = sorted(RELAY_REQUIRED - set(record))
    if missing:
        raise RuntimeError(f"Relay metadata missing required inspection fields: {missing}")


def validate_dashboard_state(record: dict[str, Any]) -> None:
    if record.get("global_analysis_readiness") is not False:
        raise RuntimeError("QA review cannot mark global analysis readiness true")
    if record.get("analysis_facing_promotion_allowed") is not False:
        raise RuntimeError("QA review cannot authorize global analysis-facing promotion")


def validate_checkpoint(record: dict[str, Any]) -> None:
    if record.get("status") != "complete" or record.get("processed") != 643 or record.get("expected") != 643:
        raise RuntimeError("Partial QA review cannot masquerade as complete")


def build_review_material() -> dict[str, Any]:
    fields, rows = read_csv(LAYER / "limited_qualitative_mechanism_usage_layer.csv")
    validate_no_forbidden_fields(fields)
    if fields != list(layer.OUTPUT_FIELDS):
        raise RuntimeError("Usage-layer schema differs from approved materialization schema")
    if len(fields) != len(set(fields)):
        raise RuntimeError("Duplicate usage-layer header detected")
    if len(rows) != 643:
        raise RuntimeError(f"Usage-layer row count is not 643: {len(rows)}")
    ids = [row.get("qualitative_observation_id", "") for row in rows]
    id_set = set(ids)
    if len(id_set) != 643 or "" in id_set:
        raise RuntimeError("Usage-layer qualitative observation IDs are duplicate or blank")
    observed_id_hash = id_set_sha256(id_set)
    if observed_id_hash != AUTHORIZED_ID_HASH:
        raise RuntimeError("Candidate ID-set SHA-256 does not match authorization")

    for row in rows:
        validate_row(row)

    manifest = read_json(LAYER / "limited_qualitative_mechanism_usage_layer_manifest.json")
    decision = read_json(LAYER / "limited_qualitative_usage_layer_decision.json")
    prior_audit = read_json(LAYER / "limited_qualitative_usage_eligibility_audit.json")
    prior_invariants = read_json(LAYER / "limited_qualitative_usage_layer_invariant_checks.json")
    primary = read_json(LAYER / "strict_primary_matched_city_cycle_usage_manifest.json")
    restricted = read_json(LAYER / "restricted_exact_span_usage_quarantine_manifest.json")
    navigation = read_json(LAYER / "navigation_only_qualitative_usage_manifest.json")
    carried = {
        "quantitative_candidates": read_json(LAYER / "quantitative_candidates_carried_forward_manifest.json"),
        "quantitative_exceptions": read_json(LAYER / "quantitative_exceptions_carried_forward_manifest.json"),
        "non_base_companion": read_json(LAYER / "non_base_companion_carried_forward_manifest.json"),
        "reference_control": read_json(LAYER / "reference_control_carried_forward_manifest.json"),
        "unresolved_conflicts": read_json(LAYER / "unresolved_conflict_quarantine_carried_forward_manifest.json"),
    }
    if manifest.get("output_sha256") != sha256(LAYER / "limited_qualitative_mechanism_usage_layer.csv"):
        raise RuntimeError("Materialized CSV hash drift")
    if manifest.get("schema_sha256") != schema_sha256(fields):
        raise RuntimeError("Materialized schema hash drift")
    if manifest.get("authorized_candidate_id_set_sha256") != observed_id_hash or manifest.get("materialized_id_set_sha256") != observed_id_hash:
        raise RuntimeError("Manifest authorization/materialized ID hashes do not reconcile")
    if decision.get("counts") != EXPECTED_COUNTS or prior_audit.get("counts") != EXPECTED_COUNTS or prior_invariants.get("counts") != EXPECTED_COUNTS:
        raise RuntimeError("Materialization count contract drift")
    if prior_invariants.get("all_invariants_passed") is not True or prior_audit.get("all_checks_passed") is not True:
        raise RuntimeError("Materialization did not preserve a passing audit/invariant state")

    primary_ids = {row["qualitative_observation_id"] for row in rows if row.get("eligible_for_strict_primary_matched_city_cycle_manifest") == "true"}
    cycle_ids = {row["qualitative_observation_id"] for row in rows if row.get("eligible_for_cycle_aware_review") == "true"}
    occupation_ids = {row["qualitative_observation_id"] for row in rows if row.get("eligible_for_occupation_aware_review") == "true"}
    matched_ids = {row["qualitative_observation_id"] for row in rows if row.get("eligible_for_exact_period_matched_set_review") == "true"}
    if (len(primary_ids), len(cycle_ids), len(occupation_ids), len(matched_ids)) != (56, 453, 438, 77):
        raise RuntimeError("Usage-layer eligibility subset count drift")
    if primary.get("row_count") != 56 or primary.get("qualitative_observation_id_set_sha256") != id_set_sha256(primary_ids):
        raise RuntimeError("Strict primary manifest does not reconcile to the layer")
    if primary.get("analysis_results_computed") is not False or primary.get("global_analysis_readiness") is not False:
        raise RuntimeError("Strict primary manifest incorrectly claims analysis/readiness")
    if restricted.get("row_count") != 116 or navigation.get("row_count") != 1195:
        raise RuntimeError("Restricted/navigation manifest count drift")
    if navigation.get("ambiguous_rows") != 614 or navigation.get("unavailable_rows") != 581:
        raise RuntimeError("Navigation tier count drift")

    upstream = layer.validate_material_inputs()
    restricted_overlap = len(id_set & upstream["restricted_ids"])
    navigation_overlap = len(id_set & upstream["navigation_ids"])
    if restricted_overlap or navigation_overlap:
        raise RuntimeError("Restricted or navigation identity contaminates usage layer")
    if id_set != upstream["authorized_ids"]:
        raise RuntimeError("Reviewed layer identities differ from authorized upstream identities")

    carried_expected = {
        "quantitative_candidates": 862,
        "quantitative_exceptions": 1045,
        "non_base_companion": 4733,
        "reference_control": 345,
        "unresolved_conflicts": 5,
    }
    for name, expected in carried_expected.items():
        record = carried[name]
        if record.get("row_count") != expected or record.get("separate_from_qualitative_usage_layer") is not True or record.get("contains_observation_rows") is not False:
            raise RuntimeError(f"Carried-forward lane contract drift: {name}")
    if carried["unresolved_conflicts"].get("group_count") != 2:
        raise RuntimeError("Unresolved conflict group count drift")

    provenance_counts = {field: sum(bool(row.get(field, "").strip()) for row in rows) for field in REQUIRED_ROW_FIELDS}
    if any(value != 643 for value in provenance_counts.values()):
        raise RuntimeError("Required evidence/provenance/restriction coverage is incomplete")

    return {
        "fields": fields, "rows": rows, "ids": id_set, "id_hash": observed_id_hash,
        "manifest": manifest, "decision": decision, "prior_audit": prior_audit,
        "primary": primary, "restricted": restricted, "navigation": navigation,
        "carried": carried, "upstream": upstream, "provenance_counts": provenance_counts,
        "primary_ids": primary_ids, "cycle_ids": cycle_ids,
        "occupation_ids": occupation_ids, "matched_ids": matched_ids,
        "restricted_overlap": restricted_overlap, "navigation_overlap": navigation_overlap,
    }


def build_reports(output_dir: Path, hashes: dict[str, str], signature: str, material: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows = material["rows"]
    manifest = material["manifest"]
    layer_path = LAYER / "limited_qualitative_mechanism_usage_layer.csv"

    hash_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "input_signature": signature, "immutable_inputs_verified": len(hashes),
        "authorized_candidate_id_set_sha256": AUTHORIZED_ID_HASH,
        "observed_candidate_id_set_sha256": material["id_hash"],
        "candidate_id_set_hash_match": material["id_hash"] == AUTHORIZED_ID_HASH,
        "recorded_layer_sha256": manifest["output_sha256"],
        "observed_layer_sha256": sha256(layer_path),
        "layer_sha256_match": manifest["output_sha256"] == sha256(layer_path),
        "recorded_schema_sha256": manifest["schema_sha256"],
        "observed_schema_sha256": schema_sha256(material["fields"]),
        "schema_sha256_match": manifest["schema_sha256"] == schema_sha256(material["fields"]),
        "all_hash_checks_passed": True, "input_sha256": hashes,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_hash_audit.json", hash_audit)

    schema_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "row_count": len(rows), "column_count": len(material["fields"]),
        "exact_approved_schema_match": material["fields"] == list(layer.OUTPUT_FIELDS),
        "duplicate_header_count": len(material["fields"]) - len(set(material["fields"])),
        "missing_required_row_fields": sorted(set(REQUIRED_ROW_FIELDS) - set(material["fields"])),
        "forbidden_analysis_or_page_payload_fields": sorted(set(material["fields"]) & FORBIDDEN_OUTPUT_FIELDS),
        "unique_qualitative_observation_ids": len(material["ids"]),
        "all_schema_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_schema_audit.json", schema_audit)

    provenance_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "rows_reviewed": len(rows), "required_field_nonblank_counts": material["provenance_counts"],
        "literal_span_hash_pass_count": 643, "literal_span_offset_roundtrip_pass_count": 643,
        "bounded_page_pointer_pass_count": 643, "identity_provenance_complete_count": 643,
        "historical_qa_preserved_count": 643, "current_active_true_count": 643,
        "all_provenance_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_provenance_audit.json", provenance_audit)

    restriction_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "rows_reviewed": 643, "limited_use_eligible_count": 643,
        "analysis_status_not_analyzed_count": sum(row["analysis_status"] == "not_analyzed_limited_evidence_layer_only" for row in rows),
        "causal_claims_closed_count": sum(row["causal_claim_status"] == "no_causal_claims_authorized" for row in rows),
        "required_prohibited_use_contract_count": 643,
        "strict_primary_manifest_rows": len(material["primary_ids"]),
        "exact_cycle_eligible_rows": len(material["cycle_ids"]),
        "controlled_occupation_eligible_rows": len(material["occupation_ids"]),
        "exact_period_matched_set_eligible_rows": len(material["matched_ids"]),
        "analysis_results_computed": False, "global_analysis_readiness": False,
        "all_restriction_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_restriction_audit.json", restriction_audit)

    contamination_audit = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "restricted_exact_span_contamination_count": material["restricted_overlap"],
        "ambiguous_or_unavailable_contamination_count": material["navigation_overlap"],
        "quantitative_contamination_count": 0, "non_base_contamination_count": 0,
        "reference_control_contamination_count": 0, "unresolved_conflict_contamination_count": 0,
        "quantitative_manifest_rows": 862, "quantitative_exception_manifest_rows": 1045,
        "non_base_manifest_rows": 4733, "reference_control_manifest_rows": 345,
        "unresolved_conflict_manifest_groups": 2, "unresolved_conflict_manifest_rows": 5,
        "all_external_lanes_manifest_only": True, "all_contamination_checks_passed": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_contamination_audit.json", contamination_audit)

    scope_rows = [
        ("usage_layer", 643, len(rows), "limited qualitative evidence only"),
        ("restricted_exact_span", 116, material["restricted"]["row_count"], "quarantine metadata only"),
        ("ambiguous_navigation", 614, material["navigation"]["ambiguous_rows"], "navigation only"),
        ("unavailable_navigation", 581, material["navigation"]["unavailable_rows"], "navigation only"),
        ("navigation_total", 1195, material["navigation"]["row_count"], "navigation only"),
        ("strict_primary_manifest", 56, len(material["primary_ids"]), "narrow non-analytic manifest"),
        ("exact_cycle_eligible", 453, len(material["cycle_ids"]), "cycle-aware evidence review only"),
        ("controlled_occupation_eligible", 438, len(material["occupation_ids"]), "occupation-aware evidence review only"),
        ("exact_period_matched_set_eligible", 77, len(material["matched_ids"]), "matched-set evidence review only"),
        ("quantitative_candidates", 862, material["carried"]["quantitative_candidates"]["row_count"], "separate manifest"),
        ("quantitative_exceptions", 1045, material["carried"]["quantitative_exceptions"]["row_count"], "separate manifest"),
        ("non_base_companion", 4733, material["carried"]["non_base_companion"]["row_count"], "companion-only manifest"),
        ("reference_control", 345, material["carried"]["reference_control"]["row_count"], "control-only manifest"),
        ("unresolved_conflict_observations", 5, material["carried"]["unresolved_conflicts"]["row_count"], "quarantined manifest"),
    ]
    write_csv(output_dir / "limited_qualitative_usage_layer_scope_reconciliation.csv",
              ["scope", "expected_count", "observed_count", "reconciliation_status", "treatment"],
              [{"scope": scope, "expected_count": expected, "observed_count": observed,
                "reconciliation_status": "pass" if expected == observed else "fail", "treatment": treatment}
               for scope, expected, observed, treatment in scope_rows])

    blockers = [
        {"blocker_id": "ULQA-B01", "lane": "restricted_exact_span", "row_count": 116, "severity": "major", "qa_result": "correctly_excluded", "residual_status": "quarantined", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "retain_quarantine"},
        {"blocker_id": "ULQA-B02", "lane": "ambiguous_navigation", "row_count": 614, "severity": "critical", "qa_result": "correctly_excluded", "residual_status": "navigation_only", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "retain_navigation_only"},
        {"blocker_id": "ULQA-B03", "lane": "unavailable_navigation", "row_count": 581, "severity": "critical", "qa_result": "correctly_excluded", "residual_status": "navigation_only", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "retain_navigation_only"},
        {"blocker_id": "ULQA-B04", "lane": "strict_primary_design", "row_count": 56, "severity": "scope_limit", "qa_result": "narrow_manifest_verified", "residual_status": "non_analytic", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "do_not_infer_power_or_effects"},
        {"blocker_id": "ULQA-B05", "lane": "quantitative_exceptions", "row_count": 1045, "severity": "critical", "qa_result": "separate_manifest_verified", "residual_status": "exception_lane", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "retain_separate"},
        {"blocker_id": "ULQA-B06", "lane": "unresolved_conflicts", "row_count": 5, "severity": "critical", "qa_result": "two_groups_preserved", "residual_status": "quarantined", "blocks_acceptance_registration": "false", "blocks_global_readiness": "true", "next_action": "retain_explicit_quarantine"},
    ]
    write_csv(output_dir / "limited_qualitative_usage_layer_qa_blocker_matrix.csv", list(blockers[0]), blockers)

    (output_dir / "limited_qualitative_usage_layer_allowed_and_prohibited_use_report.md").write_text(
        "# Limited qualitative usage-layer allowed and prohibited use\n\n"
        "The reviewed layer is a literal mechanism-language evidence registry. It may be used only for evidence navigation, traceability, and separately authorized qualitative evidence workflows that honor every row-level restriction. Its 56-row strict primary subset is a narrow manifest, not an analysis sample result.\n\n"
        "Prohibited uses include descriptive or inferential statistics, wage effects or gaps, regressions, treatment effects, causal claims, global analysis-facing promotion, and treating mechanism language as proof of wage effects. Restricted, ambiguous, unavailable, quantitative, non-base, reference/control, and conflict lanes remain outside coded layer evidence.\n\n"
        "This QA pass supports only a future acceptance/registration prompt. Global and full qualitative analysis readiness remain false.\n",
        encoding="utf-8",
    )

    checks = {
        "materialization_decision_authorizes_review": True,
        "twenty_immutable_review_inputs_match_baseline": len(hashes) == 20,
        "five_package_hash_checks_inherited": True,
        "candidate_id_set_hash_matches": hash_audit["candidate_id_set_hash_match"],
        "layer_file_hash_matches": hash_audit["layer_sha256_match"],
        "schema_hash_matches": hash_audit["schema_sha256_match"],
        "exactly_643_unique_rows_reviewed": len(rows) == len(material["ids"]) == 643,
        "all_exact_spans_hash_and_offset_valid": provenance_audit["literal_span_hash_pass_count"] == 643,
        "all_required_provenance_complete": provenance_audit["identity_provenance_complete_count"] == 643,
        "historical_qa_and_current_active_preserved": provenance_audit["historical_qa_preserved_count"] == 643,
        "all_causal_claim_statuses_closed": restriction_audit["causal_claims_closed_count"] == 643,
        "no_analysis_status_implies_completion": restriction_audit["analysis_status_not_analyzed_count"] == 643,
        "restricted_and_navigation_contamination_zero": material["restricted_overlap"] == material["navigation_overlap"] == 0,
        "external_lanes_manifest_only_and_stable": contamination_audit["all_external_lanes_manifest_only"],
        "strict_primary_manifest_56_and_non_analytic": len(material["primary_ids"]) == 56,
        "no_forbidden_analysis_or_page_payload_fields": not schema_audit["forbidden_analysis_or_page_payload_fields"],
        "no_pdf_network_ocr_model_or_pipeline_action": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_claim_complete": True,
        "future_prompt_preserves_phase_boundaries": True,
    }
    write_json(output_dir / "limited_qualitative_usage_layer_qa_invariant_checks.json", {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION,
        "all_invariants_passed": all(checks.values()), "checks": checks,
        "scope_counts": EXPECTED_COUNTS,
    })

    failure_modes = [
        "materialization_decision_not_authorized", "immutable_usage_layer_hash_drift",
        "layer_file_hash_mismatch", "schema_hash_mismatch", "candidate_id_set_hash_mismatch",
        "row_count_not_643", "duplicate_or_blank_observation_id", "missing_literal_span",
        "span_hash_corruption", "span_offset_length_corruption", "invalid_page_pointer",
        "missing_case_source_detection_identity", "missing_source_provenance",
        "missing_historical_qa", "inactive_row", "historical_mixed_membership",
        "usage_restrictions_missing", "causal_claim_status_open", "analysis_status_claims_completion",
        "restricted_identity_contamination", "ambiguous_identity_contamination",
        "unavailable_identity_contamination", "quantitative_lane_contamination",
        "non_base_lane_contamination", "reference_control_contamination",
        "unresolved_conflict_contamination_or_loss", "strict_primary_count_drift",
        "strict_primary_hash_drift", "strict_primary_manifest_claims_analysis",
        "carried_lane_count_drift", "carried_lane_contains_observation_rows",
        "forbidden_analysis_field", "full_page_text_payload", "global_readiness_true",
        "global_analysis_promotion_true", "future_prompt_missing_constraint",
        "relay_missing_inspection_field", "partial_checkpoint_claims_complete",
        "rerun_changes_complete_review", "output_outside_docs_analysis",
    ]
    write_json(output_dir / "limited_qualitative_usage_layer_qa_regression_test_inventory.json", {
        "schema_version": SCHEMA_VERSION, "failure_modes": len(failure_modes),
        "failure_mode_ids": failure_modes,
        "new_test_script": "scripts/test_compensation_evidence_limited_qualitative_usage_layer_qa_review.py",
        "predecessor_test_scripts": [
            "scripts/test_compensation_evidence_limited_qualitative_usage_layer.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_usage_review.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_promotion.py",
            "scripts/test_compensation_evidence_pipeline_hardening_readiness_accelerator.py",
            "scripts/test_compensation_evidence_limited_exact_span_qualitative_readiness_review.py",
            "scripts/test_compensation_evidence_qualitative_evidence_contract_followup.py",
        ],
    })
    (output_dir / "limited_qualitative_usage_layer_qa_stress_test_report.md").write_text(
        "# Limited qualitative usage-layer QA stress test\n\n"
        f"The QA system registers {len(failure_modes)} adversarial failure modes covering authorization, immutable hashes, schema and identity drift, exact-span evidence, provenance, historical/current QA, restrictions, contamination, lane separation, conflict preservation, readiness, prompts, relays, checkpoints, reruns, and output boundaries. Final executed test totals are recorded in the validation report.\n",
        encoding="utf-8",
    )
    (output_dir / "limited_qualitative_usage_layer_qa_validation_2026-07-25.md").write_text(
        "# Limited qualitative usage-layer QA validation\n\n"
        "- Twenty committed review inputs: present and byte-identical to the authorized baseline.\n"
        "- Inherited five-package SHA-256 contract: passed.\n"
        f"- Authorized/reviewed observation-ID SHA-256: `{material['id_hash']}`; passed.\n"
        "- Exactly 643 unique rows: passed.\n"
        "- Literal span hash/offset/pointer, identity, provenance, historical QA, current-active, restriction, and causal-status checks: 643/643 passed.\n"
        "- Restricted/navigation/external-lane contamination: zero.\n"
        "- Strict primary 56-row non-analytic manifest and all carried-lane counts: passed.\n"
        "- Analysis results computed: false. Global analysis readiness: false.\n\n"
        "Focused and repository validation results are appended after execution.\n",
        encoding="utf-8",
    )

    prompt = """# Next task: limited qualitative usage-layer acceptance and registration

Do not run this prompt without separate explicit user authorization.

Perform acceptance/registration only for the QA-passed 643-row limited qualitative mechanism evidence layer. Reverify the QA decision, layer hash, schema hash, authorized ID-set hash, row count, exact-span/provenance contracts, 56-row strict-primary non-analytic manifest, excluded tiers, and separate carried-lane manifests. Create only a rollback-safe acceptance/registration record under docs/analysis. Do not mutate, promote, ingest, codify, analyze, or interpret the evidence. Global analysis readiness remains false.

Mechanism language is not evidence of wage effects. Do not compute descriptive or inferential statistics. Do not calculate wage gaps, effects, regressions, treatment effects, or causal claims. Do not fetch. Do not pull. Do not inspect remotes. Do not configure remotes. Do not open URLs. Do not download or redownload documents. Do not open PDFs. Do not access PDF pages. Do not run OCR. Do not call GABRIEL/API or any model. Do not run scout or source discovery. Do not run source review. Do not run verification. Do not run extraction. Do not select new documents. Do not ingest. Do not run gabriel.codify. Do not create a global/final analysis-facing dataset. Do not run regressions. Do not make causal claims. Keep all package, repair, span, evidence-contract, readiness, hardening, promotion, usage-review, usage-layer, extraction, QA, source, and durable ledgers immutable. Stop after the acceptance/registration decision, validation, dashboard update, commit, push, and lite relay.
"""
    validate_future_prompt(prompt)
    (output_dir / "next_limited_qualitative_usage_layer_acceptance_prompt.md").write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(
        "# Next task\n\nSeek separate explicit authorization to run `next_limited_qualitative_usage_layer_acceptance_prompt.md`. That task may create only a rollback-safe acceptance/registration record; it must perform no analysis, source access, promotion, ingestion, codification, or readiness escalation.\n",
        encoding="utf-8",
    )

    decision = {
        "task_id": TASK_ID, "schema_version": SCHEMA_VERSION, "generated_at": now,
        "input_signature": signature, "decision": DECISION,
        "candidate_id_set_sha256": material["id_hash"],
        "candidate_id_set_hash_verified": True, "qa_reviewed_usage_layer_rows": 643,
        "restricted_contamination_count": 0, "navigation_contamination_count": 0,
        "external_lane_contamination_count": 0, "strict_primary_manifest_rows": 56,
        "counts": EXPECTED_COUNTS, "all_hash_checks_passed": True,
        "all_schema_checks_passed": True, "all_provenance_checks_passed": True,
        "all_restriction_checks_passed": True, "all_contamination_checks_passed": True,
        "acceptance_registration_prompt_allowed_next": True,
        "acceptance_registration_requires_separate_authorization": True,
        "analysis_results_computed": False, "descriptive_statistics_computed": False,
        "inferential_statistics_computed": False, "global_analysis_readiness": False,
        "full_qualitative_readiness": False, "global_analysis_facing_promotion": False,
        "package_sha256_checks_passed": 5, "immutable_inputs_verified": len(hashes),
        "pdf_pages_accessed": 0, "ocr_later_accessed": 0, "network_calls": 0,
        "model_calls": 0, "forbidden_actions_performed": [], "immutable_inputs_modified": False,
        "next_prompt": "next_limited_qualitative_usage_layer_acceptance_prompt.md",
    }
    write_json(output_dir / "limited_qualitative_usage_layer_qa_review_decision.json", decision)
    (output_dir / "limited_qualitative_usage_layer_qa_review_summary.md").write_text(
        f"""# Limited qualitative usage-layer QA review

Decision: `{DECISION}`

The review independently verified all 643 authorized literal exact-span qualitative mechanism rows. The authorized, manifested, and observed observation-ID sets share SHA-256 `{material['id_hash']}`. Layer-file and schema hashes match; all rows have valid span hashes and offsets, bounded pointers, identities, provenance, historical/current QA, current-active state, explicit usage restrictions, and closed causal-claim status.

Restricted exact-span contamination is zero and ambiguous/unavailable contamination is zero. The 56-row strict-primary manifest remains narrow and non-analytic. Quantitative (862 candidates/1,045 exceptions), non-base (4,733), reference/control (345), and two conflict groups/five observations remain separate manifests.

No descriptive or inferential statistics or other analysis results were computed. Global and full qualitative analysis readiness remain false. A separately authorized acceptance/registration prompt is allowed next; it is not an analysis or promotion prompt.
""",
        encoding="utf-8",
    )


REQUIRED_OUTPUTS = (
    "limited_qualitative_usage_layer_qa_review_summary.md",
    "limited_qualitative_usage_layer_qa_review_decision.json",
    "limited_qualitative_usage_layer_hash_audit.json",
    "limited_qualitative_usage_layer_schema_audit.json",
    "limited_qualitative_usage_layer_provenance_audit.json",
    "limited_qualitative_usage_layer_restriction_audit.json",
    "limited_qualitative_usage_layer_contamination_audit.json",
    "limited_qualitative_usage_layer_qa_blocker_matrix.csv",
    "limited_qualitative_usage_layer_scope_reconciliation.csv",
    "limited_qualitative_usage_layer_allowed_and_prohibited_use_report.md",
    "limited_qualitative_usage_layer_qa_validation_2026-07-25.md",
    "limited_qualitative_usage_layer_qa_invariant_checks.json",
    "limited_qualitative_usage_layer_qa_stress_test_report.md",
    "limited_qualitative_usage_layer_qa_regression_test_inventory.json",
    "next_limited_qualitative_usage_layer_acceptance_prompt.md",
    "next_task.md",
)


def validate_complete_output(output_dir: Path, signature: str) -> None:
    missing = [name for name in REQUIRED_OUTPUTS if not (output_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Required QA-review outputs missing: {missing}")
    decision = read_json(output_dir / "limited_qualitative_usage_layer_qa_review_decision.json")
    invariants = read_json(output_dir / "limited_qualitative_usage_layer_qa_invariant_checks.json")
    hash_audit = read_json(output_dir / "limited_qualitative_usage_layer_hash_audit.json")
    contamination = read_json(output_dir / "limited_qualitative_usage_layer_contamination_audit.json")
    if (
        decision.get("decision") != DECISION
        or decision.get("input_signature") != signature
        or decision.get("qa_reviewed_usage_layer_rows") != 643
        or decision.get("candidate_id_set_sha256") != AUTHORIZED_ID_HASH
        or decision.get("candidate_id_set_hash_verified") is not True
        or decision.get("acceptance_registration_prompt_allowed_next") is not True
        or decision.get("analysis_results_computed") is not False
        or decision.get("global_analysis_readiness") is not False
        or invariants.get("all_invariants_passed") is not True
        or hash_audit.get("all_hash_checks_passed") is not True
        or contamination.get("all_contamination_checks_passed") is not True
    ):
        raise RuntimeError("Completed QA-review decision/hash/count/readiness contract mismatch")
    validate_future_prompt((output_dir / "next_limited_qualitative_usage_layer_acceptance_prompt.md").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output_guard(args.output_dir, allow_existing=args.resume)
    hashes = verify_inputs()
    signature = input_signature(hashes)
    material = build_review_material()
    if args.dry_run:
        print(json.dumps({
            "dry_run": True, "writes": 0, "decision": DECISION,
            "candidate_id_set_hash_verified": True,
            "candidate_id_set_sha256": material["id_hash"],
            "qa_reviewed_usage_layer_rows": len(material["rows"]),
            "restricted_contamination_count": material["restricted_overlap"],
            "navigation_contamination_count": material["navigation_overlap"],
            "strict_primary_manifest_rows": len(material["primary_ids"]),
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
        "candidate_id_set_sha256": material["id_hash"],
        "qa_reviewed_usage_layer_rows": 643, "strict_primary_manifest_rows": 56,
        "restricted_contamination_count": 0, "navigation_contamination_count": 0,
        "acceptance_registration_prompt_allowed_next": True,
        "global_analysis_readiness": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
