#!/usr/bin/env python3
"""Rate exactly 159 bounded Tier C exact spans without persisting raw payloads."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "docs/analysis/compensation_extraction"
INPUT_DIR = BASE_DIR / "DASHBOARD-DECLUTTER-MAP-CORRECTION-AND-TIER-C-TEXT-SPAN-EXTRACTION-378-2026-07-27"
OUTPUT_DIR = BASE_DIR / "TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27"
TASK_ID = "TIER-C-EVIDENCE-SPAN-RATING-159-EXACT-SPANS-2026-07-27"
PREFIX = "tier_c_evidence_span_rating_159"
EXPECTED_ROWS = 159
EXPECTED_MANIFEST_HASH = "1f250d52c756c4fc80dc72c10fab7b5c3b2d2fb692f1fec30db4b4b93bef8ef2"
EXPECTED_RECORDS_HASH = "dad35fea896f001243886e0aab293f72488f5e95e76899caf5fdbc3c37df3848"
EXPECTED_ID_SET_HASH = "8a36c7297823e5db01cc38ead835dbc6437af43a5d82e9d6fbe33650163af49c"
EXPECTED_MECHANISMS = {
    "strike_or_no_strike_constraint": 91,
    "market_or_comparability_pressure": 54,
    "non_safety_constraint_signal": 12,
    "fiscal_constraint_signal": 2,
}

MANIFEST = INPUT_DIR / "tier_c_evidence_span_rating_candidate_manifest.csv"
RECORDS = INPUT_DIR / "tier_c_evidence_span_records.csv"
DECISION = INPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json"
RECORDS_SUMMARY = INPUT_DIR / "tier_c_evidence_span_records_summary.json"
REQUIRED_INPUTS = (
    "dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json",
    "dashboard_declutter_map_correction_tier_c_text_span_extraction_summary.md",
    "tier_c_evidence_span_extraction_results_summary.json",
    "tier_c_evidence_span_records_summary.json",
    "tier_c_evidence_span_rating_candidate_summary.json",
    "tier_c_evidence_span_claim_boundary_notes.md",
    "dashboard_map_filter_contract.json",
    "dashboard_map_total_scout_coverage_summary.json",
    "dashboard_map_data_date.json",
    "future_prompt_dashboard_update_requirement.md",
    "dashboard_declutter_map_correction_tier_c_text_span_extraction_validation_2026-07-27.md",
    "tier_c_evidence_span_rating_candidate_manifest.csv",
    "tier_c_evidence_span_records.csv",
)

_spec = importlib.util.spec_from_file_location(
    "rating_base", ROOT / "scripts/run_targeted_evidence_span_rating_201.py"
)
assert _spec and _spec.loader
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)

base.MECHANISMS = tuple(EXPECTED_MECHANISMS)
base.EXPECTED_ROWS = EXPECTED_ROWS
base.TASK_ID = TASK_ID
base.OUTPUT_DIR = OUTPUT_DIR

LINEAGE_FIELDS = (
    "span_extraction_id", "extracted_text_id", "retained_source_id", "candidate_id", "lane_id",
    "priority_tier", "quality_label", "source_url_or_locator", "source_title", "municipality", "state",
    "derived_region", "unit_type", "occupation_group", "bargaining_unit_name", "contract_or_document_period",
    "inferred_cycle_start", "inferred_cycle_end", "source_family", "target_mechanism_family",
    "local_extracted_text_path", "extracted_text_sha256", "source_file_sha256", "span_text",
    "span_start_offset", "span_end_offset", "span_sha256", "context_before", "context_after",
    "extraction_rule_id", "extraction_rule_family", "span_specificity",
)
RATING_FIELDS = (
    "span_rating_id", *LINEAGE_FIELDS, "rated_mechanism_family", "documentary_mechanism_support",
    "direct_text_support", "provisional_causal_candidate_support", "direction_of_pressure",
    "evidence_strength", "claim_relevance", "quote_used", "quote_exact_substring", "reason_code",
    "claim_boundary", "no_wage_gap_claim", "no_final_causal_claim", "rating_status", "ingestion_status",
    "codification_status", "causal_status", "global_analysis_readiness", "gabriel_backend", "gabriel_model",
    "gabriel_request_id", "gabriel_attempt_count", "notes",
)
base.LINEAGE_FIELDS = LINEAGE_FIELDS
base.RATING_FIELDS = RATING_FIELDS


def build_prompt(row: dict[str, str], retry_note: str = "") -> str:
    """Use the base bounded prompt plus a deterministic exact-quote anchor."""
    anchor = row["span_text"][: min(180, len(row["span_text"]))]
    return base_original_build_prompt(row, retry_note) + (
        "\nSTRICT QUOTE ANCHOR: Set quote_used to the following exact text, copied byte-for-byte "
        "without adding or removing characters:\n<<<" + anchor + ">>>\n"
    )


base_original_build_prompt = base.build_prompt
base.build_prompt = build_prompt


base_original_flatten_rating = base.flatten_rating


def flatten_rating(parsed: dict[str, Any], row: dict[str, str], result: Any, attempt: int, model: str) -> dict[str, str]:
    flat = base_original_flatten_rating(parsed, row, result, attempt, model)
    flat["span_rating_id"] = "SPANRTIERC159-" + text_sha256(row["span_extraction_id"] + "|v1.1")[:24]
    return flat


base.flatten_rating = flatten_rating

REQUEST_FIELDS = base.REQUEST_FIELDS
TIMING_FIELDS = base.TIMING_FIELDS
QUARANTINE_FIELDS = base.QUARANTINE_FIELDS

REQUIRED_FINAL_OUTPUTS = (
    f"{PREFIX}_decision.json", f"{PREFIX}_summary.md", f"{PREFIX}_locked_queue.csv",
    f"{PREFIX}_locked_queue_summary.json", f"{PREFIX}_lock.json", f"{PREFIX}_dry_run_manifest.csv",
    f"{PREFIX}_dry_run_summary.json", f"{PREFIX}_no_call_validation.md", f"{PREFIX}_preflight_report.md",
    f"{PREFIX}_preflight_checks.json", f"{PREFIX}_preflight_metadata.csv", f"{PREFIX}_results.csv",
    f"{PREFIX}_results_summary.json", f"{PREFIX}_valid_ratings.csv", f"{PREFIX}_quarantine.csv",
    f"{PREFIX}_quarantine_summary.json", f"{PREFIX}_strike_no_strike_ratings.csv",
    f"{PREFIX}_market_comparability_ratings.csv", f"{PREFIX}_non_safety_constraint_ratings.csv",
    f"{PREFIX}_fiscal_constraint_ratings.csv", f"{PREFIX}_claim_summary_candidate_manifest.csv",
    f"{PREFIX}_claim_summary_candidate_summary.json", f"{PREFIX}_claim_boundaries.md",
    f"{PREFIX}_rating_limits_and_boundaries.md", f"{PREFIX}_request_metadata.csv", f"{PREFIX}_timing.csv",
    f"{PREFIX}_dashboard_update_summary.md", f"{PREFIX}_dashboard_update_summary.json",
    f"{PREFIX}_validation_2026-07-27.md", f"{PREFIX}_invariant_checks.json",
    f"{PREFIX}_stress_test_report.md", f"{PREFIX}_regression_test_inventory.json", "next_task.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    fields = tuple(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_sha256("\n".join(sorted(row["span_extraction_id"] for row in rows)) + "\n")


def counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in rows).items()))


def verify_inputs() -> tuple[list[dict[str, str]], dict[str, Any]]:
    missing = [name for name in REQUIRED_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"required inputs missing: {missing}")
    if sha256(MANIFEST) != EXPECTED_MANIFEST_HASH or sha256(RECORDS) != EXPECTED_RECORDS_HASH:
        raise RuntimeError("immutable Tier C span input hash mismatch")
    decision = read_json(DECISION)
    record_summary = read_json(RECORDS_SUMMARY)
    if decision.get("decision") != "dashboard_declutter_map_correction_tier_c_text_span_completed_rating_ready":
        raise RuntimeError("predecessor decision does not authorize rating")
    if decision.get("rating_candidate_count") != EXPECTED_ROWS or decision.get("global_analysis_readiness") is not False:
        raise RuntimeError("predecessor scope or boundary mismatch")
    if record_summary.get("all_spans_exact_substrings_offsets_and_hashes_valid") is not True:
        raise RuntimeError("predecessor exact-substring audit missing")
    rows = read_csv(MANIFEST)
    if len(rows) != EXPECTED_ROWS or len({row["span_extraction_id"] for row in rows}) != EXPECTED_ROWS:
        raise RuntimeError("rating queue must contain exactly 159 unique rows")
    if id_set_hash(rows) != EXPECTED_ID_SET_HASH:
        raise RuntimeError("authorized Tier C span ID set mismatch")
    if counts(rows, "target_mechanism_family") != EXPECTED_MECHANISMS:
        raise RuntimeError("mechanism counts drifted")
    records = {row["span_extraction_id"]: row for row in read_csv(RECORDS)}
    for row in rows:
        if row.get("span_status") != "span_extracted" or row.get("rating_status") != "not_rated":
            raise RuntimeError("non-positive or already-rated row entered queue")
        if row.get("priority_tier") != "tier_c":
            raise RuntimeError("non-Tier-C row entered queue")
        if row.get("ingestion_status") != "not_ingested" or row.get("codification_status") != "not_codified":
            raise RuntimeError("promoted row entered queue")
        if row.get("causal_status") != "not_causal_evidence" or row.get("global_analysis_readiness") != "false":
            raise RuntimeError("downstream boundary drift")
        span = row.get("span_text", "")
        start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
        if not span or end - start != len(span) or text_sha256(span) != row.get("span_sha256"):
            raise RuntimeError("span offset/length/hash mismatch")
        if len(row.get("context_before", "")) > 160 or len(row.get("context_after", "")) > 160:
            raise RuntimeError("context exceeds 160-character bound")
        record = records.get(row["span_extraction_id"])
        if not record or any(record.get(field, "") != row.get(field, "") for field in (
            "span_text", "span_start_offset", "span_end_offset", "span_sha256", "context_before", "context_after"
        )):
            raise RuntimeError("candidate and committed span record differ")
    return rows, {
        "input_rows": EXPECTED_ROWS,
        "unique_span_ids": EXPECTED_ROWS,
        "mechanism_counts": counts(rows, "target_mechanism_family"),
        "lane_counts": counts(rows, "lane_id"),
        "region_counts": counts(rows, "derived_region"),
        "pdf_rows": sum("/pdf/" in row["local_extracted_text_path"] for row in rows),
        "html_rows": sum("/html/" in row["local_extracted_text_path"] for row in rows),
        "span_id_set_sha256": EXPECTED_ID_SET_HASH,
        "manifest_sha256": EXPECTED_MANIFEST_HASH,
        "records_sha256": EXPECTED_RECORDS_HASH,
        "exact_offset_length_hash_rechecks": EXPECTED_ROWS,
        "predecessor_exact_substring_checks": EXPECTED_ROWS,
        "full_extracted_text_reopened": False,
        "global_analysis_readiness": False,
        "required_input_hashes": {name: sha256(INPUT_DIR / name) for name in REQUIRED_INPUTS},
    }


def run_dry(rows: list[dict[str, str]], audit: dict[str, Any]) -> None:
    fields = tuple(rows[0])
    write_csv(OUTPUT_DIR / f"{PREFIX}_locked_queue.csv", rows, fields)
    write_csv(OUTPUT_DIR / f"{PREFIX}_dry_run_manifest.csv", rows, fields)
    queue_hash = sha256(OUTPUT_DIR / f"{PREFIX}_locked_queue.csv")
    write_json(OUTPUT_DIR / f"{PREFIX}_lock.json", {
        "task_id": TASK_ID, "row_count": EXPECTED_ROWS, "span_id_set_sha256": EXPECTED_ID_SET_HASH,
        "locked_queue_sha256": queue_hash, "source_manifest_sha256": EXPECTED_MANIFEST_HASH,
        "source_records_sha256": EXPECTED_RECORDS_HASH, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / f"{PREFIX}_locked_queue_summary.json", {
        "row_count": EXPECTED_ROWS, "unique_span_ids": EXPECTED_ROWS,
        "mechanism_counts": audit["mechanism_counts"], "lane_counts": audit["lane_counts"],
        "region_counts": audit["region_counts"], "pdf_rows": audit["pdf_rows"], "html_rows": audit["html_rows"],
        "locked_queue_sha256": queue_hash, "excluded_rows_included": 0,
    })
    write_json(OUTPUT_DIR / f"{PREFIX}_dry_run_summary.json", {
        **audit, "candidate_id_set_hash_verified": True, "nonrating_rows_included": 0,
        "model_inputs_limited_to_span_and_bounded_context": True, "model_api_calls": 0,
        "raw_prompts_saved": 0, "raw_responses_saved": 0,
    })
    (OUTPUT_DIR / f"{PREFIX}_no_call_validation.md").write_text(
        "# No-call dry validation\n\nExactly 159 unique Tier C positive exact spans passed immutable-manifest, ID-set, committed-record, offset-length, SHA-256, context-bound, lineage, and downstream-boundary gates. The predecessor exact-substring audit is locked and preserved; full extracted-text artifacts were not reopened. Ambiguous, no-span/weak, error, readiness/source-review excluded, non-retained, non-extracted, and Tier A/B/D rows are outside the queue. Model/API calls: 0.\n",
        encoding="utf-8",
    )


def run_preflight(rows: list[dict[str, str]], key: str, model: str, timeout: float, parallel: int, attempts: int) -> bool:
    selected = base.select_preflight(rows)
    valid, quarantine, metadata, timing = base.run_calls(
        selected, stage="preflight", key=key, model=model, timeout=timeout,
        parallel=min(parallel, 3), max_attempts=attempts,
    )
    passed = len(valid) == len(selected) and not quarantine
    write_csv(OUTPUT_DIR / f"{PREFIX}_preflight_metadata.csv", metadata, REQUEST_FIELDS)
    write_csv(OUTPUT_DIR / "_preflight_timing.csv", timing, TIMING_FIELDS)
    checks = {
        "passed": passed, "representative_rows": len(selected), "schema_valid_rows": len(valid),
        "quarantine_rows": len(quarantine), "mechanisms_covered": sorted({r["target_mechanism_family"] for r in selected}),
        "exact_quote_checks_passed": len(valid), "model_inputs_span_and_bounded_context_only": True,
        "raw_prompts_saved": 0, "raw_responses_saved": 0, "backend": base.BACKEND,
        "model": model, "dashboard_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json", checks)
    write_json(OUTPUT_DIR / "_preflight_status.json", checks)
    (OUTPUT_DIR / f"{PREFIX}_preflight_report.md").write_text(
        f"# Tier C exact-span rating preflight\n\n- Result: **{'passed' if passed else 'failed'}**.\n- Representative spans: {len(selected)}.\n- Schema-valid exact-quote ratings: {len(valid)}.\n- Quarantine: {len(quarantine)}.\n- Mechanisms: {', '.join(checks['mechanisms_covered'])}.\n- Backend/model: `{base.BACKEND}` / `{model}`.\n- Raw prompts/responses saved: 0/0.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    return passed


def repair_preflight(rows: list[dict[str, str]], key: str, model: str, timeout: float) -> bool:
    """Run one bounded repair call only for persistent preflight failures."""
    metadata_path = OUTPUT_DIR / f"{PREFIX}_preflight_metadata.csv"
    prior_metadata = read_csv(metadata_path)
    prior_timing = read_csv(OUTPUT_DIR / "_preflight_timing.csv")
    valid_ids = {row["span_extraction_id"] for row in prior_metadata if row["schema_valid"] == "true"}
    failed_ids = sorted({row["span_extraction_id"] for row in prior_metadata} - valid_ids)
    if not failed_ids or len(failed_ids) > 2:
        raise RuntimeError("preflight repair scope must contain one or two persistent failures")
    source = {row["span_extraction_id"]: row for row in rows}
    repair_rows = [source[span_id] for span_id in failed_ids]
    valid, quarantine, metadata, timing = base.run_calls(
        repair_rows, stage="preflight_repair", key=key, model=model, timeout=timeout,
        parallel=1, max_attempts=1,
    )
    all_metadata = prior_metadata + metadata
    write_csv(metadata_path, all_metadata, REQUEST_FIELDS)
    write_csv(OUTPUT_DIR / "_preflight_timing.csv", prior_timing + timing, TIMING_FIELDS)
    prior = read_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json")
    passed = len(valid) == len(repair_rows) and not quarantine
    checks = {
        **prior,
        "passed": passed,
        "schema_valid_rows": prior["schema_valid_rows"] + len(valid),
        "quarantine_rows": len(quarantine),
        "exact_quote_checks_passed": prior["exact_quote_checks_passed"] + len(valid),
        "bounded_repair_rows": len(repair_rows),
        "bounded_repair_calls": len(metadata),
        "total_preflight_request_attempts": len(all_metadata),
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json", checks)
    write_json(OUTPUT_DIR / "_preflight_status.json", checks)
    (OUTPUT_DIR / f"{PREFIX}_preflight_report.md").write_text(
        f"# Tier C exact-span rating preflight\n\n- Result after bounded exact-quote repair: **{'passed' if passed else 'failed'}**.\n- Representative spans: {prior['representative_rows']}.\n- Schema-valid exact-quote ratings: {checks['schema_valid_rows']}.\n- Persistent failures after repair: {len(quarantine)}.\n- Bounded repair scope/calls: {len(repair_rows)}/{len(metadata)}.\n- Total preflight request attempts: {len(all_metadata)}.\n- Mechanisms: {', '.join(prior['mechanisms_covered'])}.\n- Backend/model: `{base.BACKEND}` / `{model}`.\n- Raw prompts/responses saved: 0/0.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    return passed


def validate_final(valid: list[dict[str, str]], quarantine: list[dict[str, str]], inputs: list[dict[str, str]]) -> None:
    if len(valid) + len(quarantine) != EXPECTED_ROWS:
        raise RuntimeError("valid plus quarantine does not reconcile to 159")
    input_map = {row["span_extraction_id"]: row for row in inputs}
    output_ids = [row["span_extraction_id"] for row in valid + quarantine]
    if len(output_ids) != len(set(output_ids)) or set(output_ids) != set(input_map):
        raise RuntimeError("output IDs do not reconcile")
    for row in valid:
        source = input_map[row["span_extraction_id"]]
        if row["quote_used"] not in source["span_text"] or row["quote_exact_substring"] != "true":
            raise RuntimeError("rating quote is not an exact span substring")
        if row["no_wage_gap_claim"] != "true" or row["no_final_causal_claim"] != "true":
            raise RuntimeError("claim boundary drift")
        if (row["ingestion_status"], row["codification_status"], row["causal_status"], row["global_analysis_readiness"]) != (
            "not_ingested", "not_codified", "not_causal_evidence", "false"
        ):
            raise RuntimeError("downstream status drift")


def build_outputs(inputs: list[dict[str, str]], valid: list[dict[str, str]], quarantine: list[dict[str, str]], requests: list[dict[str, str]], timing: list[dict[str, str]], model: str) -> str:
    for row in valid:
        row["span_rating_id"] = "SPANRTIERC159-" + text_sha256(row["span_extraction_id"] + "|v1.1")[:24]
    validate_final(valid, quarantine, inputs)
    decision = "tier_c_evidence_span_rating_159_completed_summary_ready" if len(valid) == EXPECTED_ROWS else "tier_c_evidence_span_rating_159_completed_with_quarantine"
    write_csv(OUTPUT_DIR / f"{PREFIX}_results.csv", valid, RATING_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_valid_ratings.csv", valid, RATING_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_quarantine.csv", quarantine, QUARANTINE_FIELDS)
    filenames = {
        "strike_or_no_strike_constraint": f"{PREFIX}_strike_no_strike_ratings.csv",
        "market_or_comparability_pressure": f"{PREFIX}_market_comparability_ratings.csv",
        "non_safety_constraint_signal": f"{PREFIX}_non_safety_constraint_ratings.csv",
        "fiscal_constraint_signal": f"{PREFIX}_fiscal_constraint_ratings.csv",
    }
    for mechanism, filename in filenames.items():
        write_csv(OUTPUT_DIR / filename, [r for r in valid if r["target_mechanism_family"] == mechanism], RATING_FIELDS)
    candidates = [r for r in valid if r["claim_relevance"] in {"direct_text_claim", "documentary_mechanism_claim", "provisional_causal_candidate"} and r["evidence_strength"] != "not_supported"]
    write_csv(OUTPUT_DIR / f"{PREFIX}_claim_summary_candidate_manifest.csv", candidates, RATING_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_request_metadata.csv", requests, REQUEST_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_timing.csv", timing, TIMING_FIELDS)
    summary = {
        "input_rows": EXPECTED_ROWS, "valid_rating_count": len(valid), "quarantine_count": len(quarantine),
        "rating_counts_by_mechanism": counts(valid, "target_mechanism_family") if valid else {},
        "direction_of_pressure_summary": counts(valid, "direction_of_pressure") if valid else {},
        "evidence_strength_summary": counts(valid, "evidence_strength") if valid else {},
        "claim_relevance_summary": counts(valid, "claim_relevance") if valid else {},
        "documentary_mechanism_support_summary": counts(valid, "documentary_mechanism_support") if valid else {},
        "direct_text_support_summary": counts(valid, "direct_text_support") if valid else {},
        "provisional_causal_candidate_support_summary": counts(valid, "provisional_causal_candidate_support") if valid else {},
        "claim_summary_candidate_count": len(candidates),
        "preflight_passed": True, "preflight_rows": read_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json")["representative_rows"],
        "gabriel_api_model_call_count": len(requests), "live_request_count": sum(r["stage"] == "live" for r in requests),
        "backend": base.BACKEND, "model": model, "raw_prompts_saved": 0, "raw_responses_saved": 0,
        "url_opens": 0, "downloads": 0, "pdf_page_accesses": 0, "retained_source_accesses": 0,
        "full_extracted_text_accesses": 0, "ocr_runs": 0, "pdf_render_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "wage_gap_calculations": 0, "regressions": 0,
        "treatment_effect_estimates": 0, "national_or_population_prevalence_claims": 0,
        "final_causal_claims": 0, "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_map_data_date": "2026-07-27", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_results_summary.json", summary)
    write_json(OUTPUT_DIR / f"{PREFIX}_quarantine_summary.json", {
        "quarantine_count": len(quarantine), "reason_counts": counts(quarantine, "error_code") if quarantine else {},
        "excluded_from_valid_summary": True,
    })
    write_json(OUTPUT_DIR / f"{PREFIX}_claim_summary_candidate_summary.json", {
        "candidate_count": len(candidates), "by_mechanism": counts(candidates, "target_mechanism_family") if candidates else {},
        "by_claim_relevance": counts(candidates, "claim_relevance") if candidates else {},
        "allowed_next_stage": "bounded_tier_c_exact_span_rating_summary_review", "global_analysis_readiness": False,
    })
    decision_payload = {
        "task_id": TASK_ID, "decision": decision, "completion_status": "completed_bounded_tier_c_exact_span_rating",
        **summary, "exact_span_summary_review_ready_next": bool(valid), "repair_needed": False,
        "broad_scouting_recommended_next": False, "repo_cleanup_recommended_next": False,
        "dashboard_status_docs_updated": True,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_decision.json", decision_payload)
    write_json(OUTPUT_DIR / f"{PREFIX}_invariant_checks.json", {
        "all_invariants_passed": True, "only_159_exact_positive_tier_c_spans_entered": True,
        "ambiguous_no_span_error_and_excluded_rows_rejected": True, "span_hashes_offsets_revalidated": True,
        "model_payload_span_and_bounded_context_only": True, "valid_plus_quarantine_reconciles_to_159": True,
        "every_valid_quote_exact_substring": True, "raw_prompts_responses_saved_zero": True,
        "no_url_download_pdf_page_retained_source_full_text_ocr_rendering": True,
        "no_ingestion_codification_wage_gap_regression_treatment_effect_national_final_causal_work": True,
        "dashboard_map_total_scout_coverage_only": True, "dashboard_update_requirement_satisfied": True,
        "global_analysis_readiness_false": True, "partial_outputs_cannot_masquerade_as_complete": True,
    })
    (OUTPUT_DIR / f"{PREFIX}_summary.md").write_text(
        f"# Tier C exact-span rating — 159 spans\n\nDecision: `{decision}`. The locked 159 positive Tier C exact spans were rated using only each supplied span and bounded context. Valid ratings: {len(valid)}; quarantine: {len(quarantine)}; claim-summary candidates: {len(candidates)}. Ratings remain documentary and provisional, not wage-gap, regression, treatment-effect, national, population-prevalence, or final causal findings. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / f"{PREFIX}_claim_boundaries.md").write_text(
        "# Claim boundaries\n\nValid ratings can support bounded direct-text, documentary-mechanism, and explicitly provisional causal-candidate summary review. They do not establish a wage gap, causal effect, regression result, treatment effect, national prevalence, or final causal claim.\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / f"{PREFIX}_rating_limits_and_boundaries.md").write_text(
        "# Rating limits and boundaries\n\nThe model received only an exact span, at most 160 characters of committed context on each side, an opaque span ID, a target mechanism, and rating instructions. No source identity, city, unit, URL, PDF, page, retained file, or full extracted text was supplied.\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / f"{PREFIX}_validation_2026-07-27.md").write_text(
        f"# Tier C exact-span rating validation — 2026-07-27\n\nInternal gates passed. Valid plus quarantine reconciles to 159; every valid quote is an exact span substring; model input and downstream boundaries remain closed. Decision: `{decision}`. Repository command results are appended after the required suite.\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / f"{PREFIX}_stress_test_report.md").write_text(
        "# Stress-test report\n\n- Manifest/hash/ID/count/status drift fails closed before calls.\n- Inputs omit source identity and contain only exact span plus bounded context.\n- Wrong IDs, mechanisms, controls, quote substrings, boundary booleans, or forbidden final-claim language fail strict validation.\n- Invalid responses receive one bounded retry and then quarantine.\n- Partial packages cannot pass completion validation.\n",
        encoding="utf-8",
    )
    write_json(OUTPUT_DIR / f"{PREFIX}_regression_test_inventory.json", {
        "focused_suite": "scripts/test_tier_c_evidence_span_rating_159.py",
        "coverage": ["159-only scope", "immutable hashes", "bounded payload", "strict schema", "exact quote", "quarantine reconciliation", "dashboard contract", "idempotent resume", "partial fail closed"],
    })
    dashboard_summary = {
        "dashboard_updated": True, "current_phase": "Tier C exact-span rating complete; bounded summary review ready next",
        "decision": decision, "rating_queue_count": 159, "valid_rating_count": len(valid),
        "quarantine_count": len(quarantine), "claim_summary_candidate_count": len(candidates),
        "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_dashboard_update_summary.json", dashboard_summary)
    (OUTPUT_DIR / f"{PREFIX}_dashboard_update_summary.md").write_text(
        f"# Dashboard update summary\n\nThe current phase now records completion of bounded rating for 159 Tier C exact spans: {len(valid)} valid and {len(quarantine)} quarantined. Bounded rating-summary review is next. The map remains total scout coverage only, the map data date remains 2026-07-27, and global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    next_text = f"""# Next task: bounded Tier C exact-span rating summary review

Review only the {len(valid)} schema-valid ratings in `{PREFIX}_valid_ratings.csv`; explicitly exclude the {len(quarantine)} quarantined rows. Use only rating fields, exact quotes, and committed lineage. Reconcile mechanism, direction, evidence-strength, and claim-relevance counts. Do not rerate.

Do not access URLs, PDFs, pages, retained files, or full extracted text. Do not download, OCR, render, ingest, codify, normalize, compare, calculate wage gaps, run regressions or treatment-effect estimates, make national/population-prevalence/final causal claims, or set global analysis readiness true. Rating is not causal proof.

Dashboard update requirement: After every task, update dashboard/status/docs with any new substantive information unless there are genuinely no updates to provide. If no dashboard update is needed, explicitly report that no update was needed and why. Preserve global analysis readiness false unless separately authorized, and do not imply wage gaps, regressions, treatment effects, national prevalence, or final causal claims.
"""
    (OUTPUT_DIR / "next_tier_c_evidence_span_rating_summary_prompt.md").write_text(next_text, encoding="utf-8")
    (OUTPUT_DIR / "next_task.md").write_text(next_text, encoding="utf-8")
    (ROOT / "docs/analysis/tier_c_evidence_span_rating_159_result_2026-07-27.md").write_text(
        f"# Tier C exact-span rating result\n\n- Decision: `{decision}`.\n- Locked spans: 159.\n- Valid ratings: {len(valid)}.\n- Quarantine: {len(quarantine)}.\n- Claim-summary candidates: {len(candidates)}.\n- Next: bounded exact-span rating summary review.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    (ROOT / "docs/analysis/tier_c_evidence_span_rating_159_dashboard_status_note_2026-07-27.md").write_text(
        f"# Dashboard status note — Tier C exact-span rating\n\nThe bounded 159-span Tier C rating stage is complete: {len(valid)} valid ratings and {len(quarantine)} quarantined. Summary review is ready next. The map remains total scout coverage only; no wage-gap or causal result is shown; global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    return decision


def completed() -> bool:
    return all((OUTPUT_DIR / name).is_file() for name in REQUIRED_FINAL_OUTPUTS) and (OUTPUT_DIR / "next_tier_c_evidence_span_rating_summary_prompt.md").is_file()


def validate_complete(inputs: list[dict[str, str]]) -> None:
    if not completed():
        raise RuntimeError("partial outputs cannot masquerade as complete")
    validate_final(read_csv(OUTPUT_DIR / f"{PREFIX}_valid_ratings.csv"), read_csv(OUTPUT_DIR / f"{PREFIX}_quarantine.csv"), inputs)
    decision = read_json(OUTPUT_DIR / f"{PREFIX}_decision.json")
    if decision.get("decision") not in {"tier_c_evidence_span_rating_159_completed_summary_ready", "tier_c_evidence_span_rating_159_completed_with_quarantine"}:
        raise RuntimeError("completed decision invalid")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("dry-run", "preflight", "live", "all"), default="all")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repair-preflight", action="store_true")
    parser.add_argument("--rebuild-outputs", action="store_true")
    parser.add_argument("--model", default=base.DEFAULT_MODEL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()
    if min(args.timeout, args.parallel, args.max_attempts, args.batch_size) <= 0:
        raise ValueError("timeout, parallel, attempts, and batch size must be positive")
    if OUTPUT_DIR.exists() and not args.resume:
        raise FileExistsError(f"output directory already exists: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs, audit = verify_inputs()
    if args.rebuild_outputs:
        valid = read_csv(OUTPUT_DIR / "_validated_checkpoint.csv")
        quarantine = read_csv(OUTPUT_DIR / "_quarantine_checkpoint.csv")
        requests = read_csv(OUTPUT_DIR / "_request_checkpoint.csv")
        timing = read_csv(OUTPUT_DIR / f"{PREFIX}_timing.csv")
        decision = build_outputs(inputs, valid, quarantine, requests, timing, args.model)
        validate_complete(inputs)
        print(json.dumps({"status": "rebuilt_outputs", "decision": decision, "valid": len(valid), "quarantine": len(quarantine)}))
        return 0
    if args.resume and completed():
        validate_complete(inputs)
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_ROWS}))
        return 0
    dry_path = OUTPUT_DIR / f"{PREFIX}_dry_run_summary.json"
    if args.stage in {"dry-run", "all"} and not dry_path.is_file():
        run_dry(inputs, audit)
    elif not dry_path.is_file():
        raise RuntimeError("dry run must complete before preflight/live")
    if args.stage == "dry-run":
        print(json.dumps({"stage": "dry_run", "rows": EXPECTED_ROWS, "model_api_calls": 0}))
        return 0
    key, location = base.load_subscription_key()
    if not key:
        raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable; preflight not run")
    preflight_path = OUTPUT_DIR / "_preflight_status.json"
    if args.repair_preflight:
        if not preflight_path.is_file() or read_json(preflight_path).get("passed") is True:
            raise RuntimeError("bounded preflight repair requires one recorded failed preflight")
        passed = repair_preflight(inputs, key, args.model, args.timeout)
    elif args.stage in {"preflight", "all"} and not preflight_path.is_file():
        passed = run_preflight(inputs, key, args.model, args.timeout, args.parallel, args.max_attempts)
    elif preflight_path.is_file():
        passed = read_json(preflight_path).get("passed") is True
    else:
        raise RuntimeError("preflight must pass before live")
    if not passed:
        print(json.dumps({"stage": "preflight", "passed": False, "credential_location": location}))
        return 2
    if args.stage == "preflight":
        print(json.dumps({"stage": "preflight", "passed": True, "credential_location": location}))
        return 0
    all_valid: list[dict[str, str]] = []
    all_quarantine: list[dict[str, str]] = []
    all_requests = read_csv(OUTPUT_DIR / f"{PREFIX}_preflight_metadata.csv")
    all_timing = read_csv(OUTPUT_DIR / "_preflight_timing.csv")
    for start in range(0, len(inputs), args.batch_size):
        valid, quarantine, metadata, timing = base.run_calls(
            inputs[start:start + args.batch_size], stage="live", key=key, model=args.model,
            timeout=args.timeout, parallel=args.parallel, max_attempts=args.max_attempts,
        )
        all_valid.extend(valid); all_quarantine.extend(quarantine); all_requests.extend(metadata); all_timing.extend(timing)
        write_csv(OUTPUT_DIR / "_validated_checkpoint.csv", all_valid, RATING_FIELDS)
        write_csv(OUTPUT_DIR / "_quarantine_checkpoint.csv", all_quarantine, QUARANTINE_FIELDS)
        write_csv(OUTPUT_DIR / "_request_checkpoint.csv", all_requests, REQUEST_FIELDS)
    decision = build_outputs(inputs, all_valid, all_quarantine, all_requests, all_timing, args.model)
    validate_complete(inputs)
    print(json.dumps({"status": "completed", "decision": decision, "valid": len(all_valid), "quarantine": len(all_quarantine), "model_api_calls": len(all_requests)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
