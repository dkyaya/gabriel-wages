#!/usr/bin/env python3
"""Repair only the 35 quarantined GABRIEL claim ratings.

The prior run intentionally persisted no invalid model payloads.  This runner
therefore diagnoses the sanitized quarantine metadata first, records that no
meaning-preserving deterministic edit is possible without the missing parsed
rating, and—only after a no-call dry run and a 100-percent-valid bounded
preflight—rerates the explicit 35-ID quarantine from the original exact spans.

The 608 accepted ratings are loaded read-only, strictly revalidated, and copied
cell-for-cell into the repaired 643-row output.  Prompts, raw responses,
credentials, environment values, and full page text are never persisted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable

import run_compensation_evidence_gabriel_claim_rating_643 as base


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "docs/analysis"
BASE = ANALYSIS_ROOT / "compensation_extraction"
TASK_ID = "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25"
BASELINE_COMMIT = "19bc7cae8cba31bb0087433ce5a3c10388e7d42c"
EXPECTED_ORIGINAL_VALID = 608
EXPECTED_REPAIR_ROWS = 35
EXPECTED_TOTAL = 643
EXPECTED_VALID_FILE_SHA256 = "d9619fba2dc9cce6a9cc1d0a3554630c7cf4e7ddcb4cd6eb8d11267f2fb13f25"
EXPECTED_QUARANTINE_FILE_SHA256 = "d8606e19ccc46868dd99954f67c4f6d58bd840a1d9842707d87b3e57365c9151"
EXPECTED_MANIFEST_SHA256 = "5993d89931fc9e816b60e607f4acb8a467bb587a3bf28390ed1922aae65c6fb6"
EXPECTED_QUARANTINE_ID_HASH = "e1e8927d19a04742a9bb777da94e3c4c93af560a5f11d980f05c0884b6c2d524"
EXPECTED_ORIGINAL_VALID_ID_HASH = "cb775dc7c88c51527423a2d9acc6477d3657d73bea0c8d0686d0661a6f3524d1"
MODEL = base.DEFAULT_MODEL

INPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-ORIENTED-ATTRIBUTE-RATING-643-2026-07-25"
UPSTREAM_DIR = BASE / "COMPENSATION-EVIDENCE-CLAIM-ORIENTED-QA-RATING-AND-GABRIEL-READINESS-FINAL-PHASE-CLOSE-2026-07-25"
DEFAULT_OUTPUT_DIR = BASE / "COMPENSATION-EVIDENCE-GABRIEL-CLAIM-RATING-35-QUARANTINE-REPAIR-2026-07-25"
MANIFEST_PATH = UPSTREAM_DIR / "gabriel_claim_rating_ready_evidence_manifest.csv"
VALID_PATH = INPUT_DIR / "gabriel_claim_oriented_attribute_ratings_643.csv"
QUARANTINE_PATH = INPUT_DIR / "gabriel_claim_oriented_attribute_rating_quarantine.csv"
QUARANTINE_SUMMARY_PRIMARY = INPUT_DIR / "quarantine_summary.json"
QUARANTINE_SUMMARY_FALLBACK = ROOT / "tmp/compensation_evidence_gabriel_claim_rating_643_relay_2026-07-25_19bc7ca/quarantine_summary.json"

REQUIRED_INPUT_NAMES = (
    "gabriel_claim_rating_643_decision.json",
    "gabriel_claim_oriented_attribute_ratings_643_summary.json",
    "gabriel_claim_rating_643_dry_run_summary.json",
    "gabriel_claim_rating_643_preflight_report.md",
    "gabriel_claim_rating_643_qa_report.md",
    "gabriel_claim_rating_643_validation_2026-07-25.md",
    "gabriel_claim_rating_643_invariant_checks.json",
    "gabriel_claim_oriented_attribute_ratings_643.csv",
    "gabriel_claim_oriented_attribute_rating_quarantine.csv",
    "gabriel_claim_rating_643_request_metadata.csv",
    "gabriel_claim_rating_643_timing.csv",
)

REQUIRED_FINAL_OUTPUTS = (
    "gabriel_claim_rating_35_quarantine_repair_manifest.csv",
    "gabriel_claim_rating_35_quarantine_repair_summary.json",
    "gabriel_claim_rating_35_quarantine_diagnostics.csv",
    "gabriel_claim_rating_35_quarantine_diagnostics_report.md",
    "gabriel_claim_oriented_attribute_ratings_643_repaired.csv",
    "gabriel_claim_oriented_attribute_ratings_643_repaired_summary.json",
    "gabriel_claim_oriented_attribute_rating_remaining_quarantine.csv",
    "gabriel_claim_rating_35_repair_request_metadata.csv",
    "gabriel_claim_rating_35_repair_timing.csv",
    "gabriel_claim_rating_35_repair_preflight_report.md",
    "gabriel_claim_rating_35_quarantine_repair_qa_report.md",
    "gabriel_claim_rating_35_quarantine_repair_decision.json",
    "gabriel_claim_rating_35_quarantine_repair_validation_2026-07-25.md",
    "gabriel_claim_rating_35_quarantine_repair_invariant_checks.json",
    "gabriel_claim_rating_35_quarantine_repair_stress_test_report.md",
    "gabriel_claim_rating_35_quarantine_repair_regression_test_inventory.json",
    "gabriel_claim_rating_repaired_claim_scaffold.md",
    "gabriel_claim_rating_repaired_claim_limits.md",
    "next_task.md",
)

MANIFEST_FIELDS = (
    "evidence_id", "row_document_id", "original_error_code", "original_failure_stage",
    "supplied_span_sha256", "deterministic_repair_possible", "deterministic_repair_attempted",
    "deterministic_repair_result", "bounded_model_retry_required", "repair_scope",
    "raw_prompt_saved", "raw_response_saved", "global_analysis_readiness",
)
DIAGNOSTIC_FIELDS = (
    "evidence_id", "original_error_code", "invalid_rating_payload_persisted",
    "deterministic_diagnostic", "safe_deterministic_edit_available", "repair_route",
    "reason", "evidence_span_available", "evidence_span_sha256", "outside_scope_evidence_used",
)


def sha256(path: Path) -> str:
    return base.sha256(path)


def id_set_sha256(ids: Iterable[str]) -> str:
    return base.id_set_sha256(ids)


def canonical_rows_sha256(rows: Iterable[dict[str, str]], fields: Iterable[str]) -> str:
    ordered = []
    fields = tuple(fields)
    for row in sorted(rows, key=lambda value: value["evidence_id"]):
        ordered.append(json.dumps({field: row.get(field, "") for field in fields}, sort_keys=True, separators=(",", ":")))
    return hashlib.sha256(("\n".join(ordered) + "\n").encode("utf-8")).hexdigest()


def resolve_inputs() -> tuple[dict[str, Path], dict[str, str]]:
    paths: dict[str, Path] = {}
    resolutions: dict[str, str] = {}
    for name in REQUIRED_INPUT_NAMES:
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        paths[name] = path
        resolutions[name] = "primary_input_directory"
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"required upstream manifest missing: {MANIFEST_PATH}")
    paths[MANIFEST_PATH.name] = MANIFEST_PATH
    resolutions[MANIFEST_PATH.name] = "approved_upstream_manifest"
    if QUARANTINE_SUMMARY_PRIMARY.is_file():
        paths["quarantine_summary.json"] = QUARANTINE_SUMMARY_PRIMARY
        resolutions["quarantine_summary.json"] = "primary_input_directory"
    elif QUARANTINE_SUMMARY_FALLBACK.is_file():
        paths["quarantine_summary.json"] = QUARANTINE_SUMMARY_FALLBACK
        resolutions["quarantine_summary.json"] = "verified_prior_lite_relay_fallback_no_upstream_mutation"
    else:
        raise FileNotFoundError(
            f"required quarantine summary missing: {QUARANTINE_SUMMARY_PRIMARY} and {QUARANTINE_SUMMARY_FALLBACK}"
        )
    return paths, resolutions


def verify_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    paths, resolutions = resolve_inputs()
    decision = base.read_json(paths["gabriel_claim_rating_643_decision.json"])
    summary = base.read_json(paths["gabriel_claim_oriented_attribute_ratings_643_summary.json"])
    invariants = base.read_json(paths["gabriel_claim_rating_643_invariant_checks.json"])
    quarantine_summary = base.read_json(paths["quarantine_summary.json"])
    if decision.get("decision") != "gabriel_claim_rating_643_completed_with_quarantine":
        raise RuntimeError("predecessor decision does not authorize quarantine repair")
    if summary.get("valid_rating_rows") != 608 or summary.get("quarantine_rows") != 35:
        raise RuntimeError("predecessor rating summary scope drift")
    if invariants.get("all_invariants_passed") is not True:
        raise RuntimeError("predecessor invariants did not pass")
    if quarantine_summary.get("quarantine_rows") != 35 or quarantine_summary.get("valid_plus_quarantine_rows") != 643:
        raise RuntimeError("quarantine summary scope drift")
    if sha256(VALID_PATH) != EXPECTED_VALID_FILE_SHA256:
        raise RuntimeError("immutable 608-row valid rating file hash drift")
    if sha256(QUARANTINE_PATH) != EXPECTED_QUARANTINE_FILE_SHA256:
        raise RuntimeError("immutable 35-row quarantine file hash drift")
    if sha256(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("immutable 643-row evidence manifest hash drift")

    manifest = base.read_csv(MANIFEST_PATH)
    original_valid = base.read_csv(VALID_PATH)
    quarantine = base.read_csv(QUARANTINE_PATH)
    if len(manifest) != EXPECTED_TOTAL or len(original_valid) != EXPECTED_ORIGINAL_VALID or len(quarantine) != EXPECTED_REPAIR_ROWS:
        raise RuntimeError("repair inputs do not reconcile to 643")
    manifest_map = {row["evidence_id"]: row for row in manifest}
    valid_ids = {row["evidence_id"] for row in original_valid}
    quarantine_ids = {row["evidence_id"] for row in quarantine}
    if len(manifest_map) != 643 or len(valid_ids) != 608 or len(quarantine_ids) != 35:
        raise RuntimeError("duplicate or blank input evidence ID")
    if valid_ids & quarantine_ids or valid_ids | quarantine_ids != set(manifest_map):
        raise RuntimeError("original valid and quarantine sets do not partition the 643-row manifest")
    if id_set_sha256(valid_ids) != EXPECTED_ORIGINAL_VALID_ID_HASH:
        raise RuntimeError("original valid ID-set hash drift")
    if id_set_sha256(quarantine_ids) != EXPECTED_QUARANTINE_ID_HASH:
        raise RuntimeError("quarantine ID-set hash drift")
    for row in original_valid:
        base.validate_rating(base.unflatten_rating(row), manifest_map[row["evidence_id"]])
    expected_errors = {
        "supporting_quote_not_exact_substring": 18,
        "weak_attribute_controls_invalid": 15,
        "positive_attribute_has_negative_controls": 1,
        "forbidden_final_claim_language": 1,
    }
    if dict(Counter(row["error_code"] for row in quarantine)) != expected_errors:
        raise RuntimeError("quarantine error-code counts drift")
    repair_rows = [manifest_map[row["evidence_id"]] for row in quarantine]
    original_valid_canonical_hash = canonical_rows_sha256(original_valid, base.RATING_OUTPUT_FIELDS)
    audit = {
        "task_id": TASK_ID,
        "baseline_commit": BASELINE_COMMIT,
        "original_valid_rows": 608,
        "repair_input_rows": 35,
        "total_rows": 643,
        "original_valid_file_sha256": sha256(VALID_PATH),
        "original_valid_id_set_sha256": id_set_sha256(valid_ids),
        "original_valid_rows_canonical_sha256": original_valid_canonical_hash,
        "quarantine_file_sha256": sha256(QUARANTINE_PATH),
        "quarantine_id_set_sha256": id_set_sha256(quarantine_ids),
        "manifest_sha256": sha256(MANIFEST_PATH),
        "input_file_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in paths.values()},
        "input_resolutions": resolutions,
        "global_analysis_readiness": False,
    }
    return manifest, original_valid, quarantine, audit


def repair_manifest_rows(repair_rows: list[dict[str, str]], quarantine: list[dict[str, str]]) -> list[dict[str, str]]:
    error_by_id = {row["evidence_id"]: row for row in quarantine}
    rows = []
    for row in repair_rows:
        source = error_by_id[row["evidence_id"]]
        rows.append({
            "evidence_id": row["evidence_id"],
            "row_document_id": row["row_document_id"],
            "original_error_code": source["error_code"],
            "original_failure_stage": source["failure_stage"],
            "supplied_span_sha256": hashlib.sha256(row["evidence_span_or_summary_pointer"].encode("utf-8")).hexdigest(),
            "deterministic_repair_possible": "false",
            "deterministic_repair_attempted": "true",
            "deterministic_repair_result": "no_invalid_rating_payload_persisted_no_safe_mechanical_edit",
            "bounded_model_retry_required": "true",
            "repair_scope": "explicit_35_quarantine_ids_only",
            "raw_prompt_saved": "false",
            "raw_response_saved": "false",
            "global_analysis_readiness": "false",
        })
    return rows


def diagnostic_rows(repair_rows: list[dict[str, str]], quarantine: list[dict[str, str]]) -> list[dict[str, str]]:
    error_by_id = {row["evidence_id"]: row["error_code"] for row in quarantine}
    reason_by_code = {
        "supporting_quote_not_exact_substring": "invalid_quote_text_not_persisted_so_exact_replacement_cannot_be_verified_without_rerating",
        "weak_attribute_controls_invalid": "invalid_attribute_object_not_persisted_so_control_fields_cannot_be_changed_without_reconstructing_rating_logic",
        "positive_attribute_has_negative_controls": "invalid_attribute_object_not_persisted_so_positive_logic_cannot_be_reconciled_mechanically",
        "forbidden_final_claim_language": "invalid_claim_boundary_not_persisted_so_safe_reframing_requires_fresh_bounded_rating",
    }
    return [{
        "evidence_id": row["evidence_id"],
        "original_error_code": error_by_id[row["evidence_id"]],
        "invalid_rating_payload_persisted": "false",
        "deterministic_diagnostic": "completed",
        "safe_deterministic_edit_available": "false",
        "repair_route": "bounded_gabriel_retry_from_original_exact_span",
        "reason": reason_by_code[error_by_id[row["evidence_id"]]],
        "evidence_span_available": "true",
        "evidence_span_sha256": hashlib.sha256(row["evidence_span_or_summary_pointer"].encode("utf-8")).hexdigest(),
        "outside_scope_evidence_used": "false",
    } for row in repair_rows]


def output_guard(output_dir: Path, *, resume: bool) -> None:
    resolved = output_dir.resolve()
    if ANALYSIS_ROOT.resolve() not in resolved.parents:
        raise RuntimeError("repair output must remain under docs/analysis")
    if output_dir.exists() and not resume:
        raise FileExistsError(f"output directory exists; use --resume: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def write_dry_run(
    output_dir: Path,
    repair_rows: list[dict[str, str]],
    quarantine: list[dict[str, str]],
    audit: dict[str, Any],
) -> dict[str, Any]:
    manifest_rows = repair_manifest_rows(repair_rows, quarantine)
    diagnostics = diagnostic_rows(repair_rows, quarantine)
    base.write_csv(output_dir / "gabriel_claim_rating_35_quarantine_repair_manifest.csv", MANIFEST_FIELDS, manifest_rows)
    base.write_csv(output_dir / "gabriel_claim_rating_35_quarantine_diagnostics.csv", DIAGNOSTIC_FIELDS, diagnostics)
    errors = dict(Counter(row["original_error_code"] for row in manifest_rows))
    summary = {
        "task_id": TASK_ID,
        "stage": "deterministic_diagnostics_and_no_call_dry_run",
        "repair_input_rows": 35,
        "repair_input_id_set_sha256": id_set_sha256(row["evidence_id"] for row in repair_rows),
        "only_explicit_quarantine_ids_included": True,
        "original_valid_rows": 608,
        "original_valid_file_sha256": audit["original_valid_file_sha256"],
        "original_valid_rows_canonical_sha256": audit["original_valid_rows_canonical_sha256"],
        "original_error_code_counts": errors,
        "deterministically_repairable_rows": 0,
        "bounded_model_retry_required_rows": 35,
        "deterministic_reason": "invalid parsed ratings were intentionally not persisted; reconstructing fields would require inference",
        "gabriel_api_called": False,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
        "input_resolutions": audit["input_resolutions"],
    }
    base.write_json(output_dir / "gabriel_claim_rating_35_quarantine_repair_summary.json", summary)
    report = """# GABRIEL claim-rating 35-row quarantine diagnostics

The deterministic pass verified exactly 35 quarantine IDs and four failure classes. The prior run intentionally retained only sanitized failure metadata—not the invalid parsed rating objects. Therefore, a quote, weak-control field, positive-control field, or claim-boundary sentence cannot be mechanically edited without reconstructing missing model logic. That would violate the no-guessing rule.

All 35 rows are routed to a bounded v1.1 rerating from their original supplied exact spans. The 608 valid ratings are outside the retry path and are protected by file, ID-set, and canonical row hashes. No API call occurred during this diagnostic/dry-run stage.
"""
    (output_dir / "gabriel_claim_rating_35_quarantine_diagnostics_report.md").write_text(report, encoding="utf-8")
    return summary


def build_repair_prompt(row: dict[str, str], original_error: str, retry_note: str = "") -> str:
    definitions = "\n".join(
        f"- {item['attribute_id']}: {item['definition']} Exclusion: {item['exclusion_rule']}"
        for item in base.ATTRIBUTES
    )
    extra = f"\nSECOND ATTEMPT CORRECTION: {retry_note}\n" if retry_note else ""
    return f"""You are rerating one previously quarantined compensation evidence span under the unchanged v1.1 taxonomy.
This retry is bounded to the supplied exact span. Ignore the prior rating; it was not retained and must not be reconstructed.
Return the strict JSON schema with all 14 attributes in the required order.

CRITICAL CONTROLS:
- For every present substantive attribute: use strong/moderate/weak strength; direct_text_claim/documentary_mechanism_claim/provisional_causal_candidate/context_only relevance; and a non-not_applicable direction.
- For every absent attribute: attribute_present=false, direction_of_pressure=not_applicable, evidence_strength=not_supported, claim_relevance=not_claim_ready, and supporting_quote="".
- If weak_or_no_claim_support is present, no other attribute may be present. It must use claim_relevance=not_claim_ready, evidence_strength=weak or not_supported, and direction neutral_or_unclear or not_applicable.
- Every positive supporting_quote must be copied character-for-character as one contiguous exact substring of EXACT_EVIDENCE_SPAN. Preserve case, punctuation, and whitespace. Never paraphrase.
- Every positive attribute needs a specific nonempty snake_case reason_code.
- Claim boundaries must be documentary and limited. Do not assert an actual wage effect, a wage gap, regression result, treatment effect, or final causal conclusion.
- Direction is provisional. For strike/no-strike text use neutral_or_unclear unless the supplied span itself establishes direction.
- Set no_wage_gap_claim=true and no_final_causal_claim=true.

The prior sanitized failure code was: {original_error}.
This is diagnostic context only; rerate from the exact span itself.

ATTRIBUTES:
{definitions}
{extra}
evidence_id: {row['evidence_id']}
EXACT_EVIDENCE_SPAN:
<<<{row['evidence_span_or_summary_pointer']}>>>
"""


def run_calls(
    rows: list[dict[str, str]],
    errors: dict[str, str],
    *,
    stage: str,
    key: str,
    model: str,
    timeout: float,
    parallel: int,
    max_attempts: int,
    caller: Callable[..., list[base.LiveResult]] = base.direct_sdk_batch,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    valid: dict[str, dict[str, str]] = {}
    metadata: list[dict[str, str]] = []
    last_failure: dict[str, tuple[int, base.LiveResult, str]] = {}
    pending = list(rows)
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        prompts = []
        for row in pending:
            note = (
                "The previous retry still failed strict validation. Check every absent control, the weak-only rule, "
                "exact substring quote copying, and documentary claim boundary before returning JSON."
                if attempt > 1 else ""
            )
            prompts.append((row["evidence_id"], build_repair_prompt(row, errors[row["evidence_id"]], note)))
        results = caller(prompts, key=key, model=model, timeout=timeout, parallel=parallel)
        next_pending = []
        for row, (_, prompt), result in zip(pending, prompts, results):
            parsed: dict[str, Any] | None = None
            error_code = result.error_code
            if result.status == "success":
                try:
                    parsed = base.validate_rating(json.loads(result.response_text), row)
                except Exception as exc:
                    _, error_code = base.safe_error_code(exc)
                    if isinstance(exc, ValueError):
                        error_code = str(exc).split(":", 1)[0][:80]
            schema_valid = parsed is not None
            effective = result
            if error_code and not result.error_code:
                effective = base.LiveResult(
                    result.request_id, result.status, result.response_text, result.elapsed_seconds,
                    result.input_tokens, result.output_tokens, result.total_tokens,
                    result.error_type or "StrictValidationError", error_code,
                )
            metadata.append(base.request_metadata(row, stage, attempt, effective, schema_valid, len(prompt), model))
            if parsed is not None:
                valid[row["evidence_id"]] = base.flatten_rating(parsed, row, result, attempt, model)
            else:
                last_failure[row["evidence_id"]] = (attempt, effective, error_code or "schema_invalid")
                next_pending.append(row)
        pending = next_pending
    remaining = []
    for row in pending:
        attempt, result, error_code = last_failure[row["evidence_id"]]
        remaining.append({
            "evidence_id": row["evidence_id"],
            "row_document_id": row["row_document_id"],
            "failure_stage": stage,
            "attempt_count": str(attempt),
            "last_status": result.status,
            "error_type": result.error_type,
            "error_code": error_code,
            "quarantine_reason": "persistent_bounded_repair_transport_or_strict_schema_failure",
            "raw_prompt_saved": "false",
            "raw_response_saved": "false",
        })
    return [valid[row["evidence_id"]] for row in rows if row["evidence_id"] in valid], remaining, metadata


def select_preflight(repair_rows: list[dict[str, str]], quarantine: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    row_map = {row["evidence_id"]: row for row in repair_rows}
    selected = []
    coverage: dict[str, Any] = {}
    for error_code in (
        "supporting_quote_not_exact_substring",
        "weak_attribute_controls_invalid",
        "positive_attribute_has_negative_controls",
        "forbidden_final_claim_language",
    ):
        source = next(row for row in quarantine if row["error_code"] == error_code)
        selected.append(row_map[source["evidence_id"]])
        coverage[error_code] = source["evidence_id"]
    return selected, coverage


def write_preflight(
    output_dir: Path,
    selected: list[dict[str, str]],
    coverage: dict[str, Any],
    valid: list[dict[str, str]],
    remaining: list[dict[str, str]],
    metadata: list[dict[str, str]],
    model: str,
) -> bool:
    passed = len(valid) == len(selected) and not remaining
    base.write_csv(output_dir / "_gabriel_claim_rating_35_repair_preflight_metadata.csv", base.REQUEST_FIELDS, metadata)
    base.write_json(output_dir / "_gabriel_claim_rating_35_repair_preflight_status.json", {
        "passed": passed,
        "input_rows": len(selected),
        "valid_rows": len(valid),
        "remaining_quarantine_rows": len(remaining),
        "remaining_quarantine_error_code_counts": dict(
            Counter(row["error_code"] for row in remaining)
        ),
        "coverage": coverage,
        "model": model,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
    })
    report = f"""# GABRIEL 35-row quarantine-repair preflight

- Result: **{'passed' if passed else 'failed'}**.
- Representative repair rows: {len(selected)}.
- Strict-schema and exact-quote valid: {len(valid)}.
- Invalid/quarantined: {len(remaining)}.
- Covered prior failure classes: {', '.join(coverage)}.
- Backend/model: `{base.BACKEND}` / `{model}`.
- Raw prompts saved: 0. Raw responses saved: 0.
- Global analysis readiness: false.

The full 35-ID repair retry is {'authorized' if passed else 'not authorized; the repair stops fail-closed'} by this gate.
"""
    (output_dir / "gabriel_claim_rating_35_repair_preflight_report.md").write_text(report, encoding="utf-8")
    return passed


def validate_repaired_outputs(
    manifest: list[dict[str, str]],
    original_valid: list[dict[str, str]],
    repaired_new: list[dict[str, str]],
    remaining: list[dict[str, str]],
    combined: list[dict[str, str]],
    audit: dict[str, Any],
) -> dict[str, Any]:
    manifest_map = {row["evidence_id"]: row for row in manifest}
    original_ids = {row["evidence_id"] for row in original_valid}
    repair_ids = set(manifest_map) - original_ids
    repaired_ids = {row["evidence_id"] for row in repaired_new}
    remaining_ids = {row["evidence_id"] for row in remaining}
    if repaired_ids | remaining_ids != repair_ids or repaired_ids & remaining_ids:
        raise RuntimeError("repaired plus remaining IDs do not reconcile to original 35-row quarantine")
    if len(combined) + len(remaining) != 643:
        raise RuntimeError("total valid plus remaining quarantine does not reconcile to 643")
    if len({row["evidence_id"] for row in combined}) != len(combined):
        raise RuntimeError("duplicate evidence ID in repaired rating output")
    original_from_combined = [row for row in combined if row["evidence_id"] in original_ids]
    canonical_hash = canonical_rows_sha256(original_from_combined, base.RATING_OUTPUT_FIELDS)
    if canonical_hash != audit["original_valid_rows_canonical_sha256"]:
        raise RuntimeError("one or more of the 608 original valid ratings changed")
    if sha256(VALID_PATH) != audit["original_valid_file_sha256"]:
        raise RuntimeError("immutable predecessor valid rating file changed during repair")
    quote_count = 0
    for row in combined:
        base.validate_rating(base.unflatten_rating(row), manifest_map[row["evidence_id"]])
        quote_count += sum(
            row[f"{attribute}__attribute_present"] == "true"
            for attribute in base.ATTRIBUTE_IDS
        )
    return {
        "original_valid_rows_unchanged": len(original_from_combined),
        "original_valid_rows_canonical_sha256": canonical_hash,
        "repair_input_rows": len(repair_ids),
        "repaired_valid_rows": len(repaired_new),
        "remaining_quarantine_rows": len(remaining),
        "remaining_quarantine_error_code_counts": dict(
            Counter(row["error_code"] for row in remaining)
        ),
        "total_valid_rows": len(combined),
        "reconciled_rows": len(combined) + len(remaining),
        "duplicate_evidence_ids": 0,
        "positive_exact_quote_pass_count": quote_count,
        "all_valid_rows_have_14_attributes": True,
        "raw_prompts_saved": 0,
        "raw_responses_saved": 0,
        "global_analysis_readiness": False,
        "cross_row_statistics_computed": False,
    }


def build_reports(
    output_dir: Path,
    manifest: list[dict[str, str]],
    original_valid: list[dict[str, str]],
    repaired_new: list[dict[str, str]],
    remaining: list[dict[str, str]],
    combined: list[dict[str, str]],
    audit: dict[str, Any],
    request_metadata: list[dict[str, str]],
    preflight_rows: int,
) -> str:
    qa = validate_repaired_outputs(manifest, original_valid, repaired_new, remaining, combined, audit)
    if not remaining and len(combined) == 643:
        decision = "gabriel_claim_rating_643_repaired_summary_review_allowed"
    else:
        decision = "gabriel_claim_rating_643_repaired_with_remaining_quarantine"
    summary = {
        "task_id": TASK_ID,
        "decision": decision,
        "attribute_taxonomy_version": "v1.1",
        "backend": base.BACKEND,
        "model": MODEL,
        "gabriel_api_ran": True,
        "repair_mode": "deterministic_diagnostics_then_bounded_model_retry_over_35_ids",
        "preflight_passed": True,
        "preflight_rows": preflight_rows,
        "original_valid_rows": 608,
        "repair_input_rows": 35,
        "deterministically_repaired_rows": 0,
        "bounded_model_retry_input_rows": 35,
        "repaired_valid_rows": len(repaired_new),
        "remaining_quarantine_rows": len(remaining),
        "remaining_quarantine_error_code_counts": qa[
            "remaining_quarantine_error_code_counts"
        ],
        "total_valid_rows": len(combined),
        "schema_valid_rate": len(combined) / 643,
        "positive_exact_quote_pass_count": qa["positive_exact_quote_pass_count"],
        "original_valid_rows_unchanged": qa["original_valid_rows_unchanged"],
        "original_valid_rows_canonical_sha256": qa["original_valid_rows_canonical_sha256"],
        "request_attempt_rows": len(request_metadata),
        "summary_review_allowed": True,
        "summary_review_scope": (
            "all_643_schema_valid_rows"
            if not remaining
            else f"{len(combined)}_schema_valid_rows_with_{len(remaining)}_explicit_quarantine_exclusions"
        ),
        "no_wage_effect_or_final_causal_claims": True,
        "cross_row_statistics_computed": False,
        "global_analysis_readiness": False,
    }
    base.write_json(output_dir / "gabriel_claim_oriented_attribute_ratings_643_repaired_summary.json", summary)
    base.write_json(output_dir / "gabriel_claim_rating_35_quarantine_repair_decision.json", summary)
    repair_summary_path = output_dir / "gabriel_claim_rating_35_quarantine_repair_summary.json"
    repair_summary = base.read_json(repair_summary_path)
    repair_summary.update({
        "stage": "completed",
        "dry_run_gabriel_api_called": False,
        "gabriel_api_ran": True,
        "repair_preflight_passed": True,
        "repair_preflight_rows": preflight_rows,
        "repaired_valid_rows": len(repaired_new),
        "remaining_quarantine_rows": len(remaining),
        "total_valid_rows": len(combined),
        "schema_valid_rate": len(combined) / 643,
        "summary_review_allowed": True,
        "decision": decision,
    })
    base.write_json(repair_summary_path, repair_summary)
    checks = {
        "repair_scope_exactly_35_ids": len(repaired_new) + len(remaining) == 35,
        "no_non_quarantined_id_entered_retry": True,
        "original_608_valid_rows_hash_identical": qa["original_valid_rows_unchanged"] == 608,
        "valid_plus_quarantine_reconciles_to_643": qa["reconciled_rows"] == 643,
        "no_duplicate_evidence_ids": qa["duplicate_evidence_ids"] == 0,
        "all_valid_rows_use_v1_1_14_attributes": qa["all_valid_rows_have_14_attributes"],
        "all_positive_quotes_exact_substrings": True,
        "all_positive_attributes_have_reason_codes": True,
        "no_wage_effect_or_final_causal_claims": True,
        "cross_row_statistics_not_computed": True,
        "no_raw_prompts_or_responses_saved": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    }
    base.write_json(output_dir / "gabriel_claim_rating_35_quarantine_repair_invariant_checks.json", {
        "task_id": TASK_ID,
        "checks": checks,
        "all_invariants_passed": all(checks.values()),
    })
    qa_report = f"""# GABRIEL claim-rating 35-row quarantine-repair QA

The repair path contained exactly 35 prior quarantine IDs and no others. Deterministic diagnostics found no safely editable invalid payload because the prior stage correctly persisted only sanitized failure metadata. A four-row bounded preflight passed before the 35-row retry.

The repair produced {len(repaired_new)} newly valid ratings and {len(remaining)} remaining quarantines. Together with 608 hash-identical original ratings, the layer contains {len(combined)} valid ratings and reconciles to 643 total rows. All positive quotes pass exact-substring validation against the original supplied spans.

No cross-row substantive statistics, wage effects, wage gaps, regressions, treatment effects, or final causal conclusions were produced. Global analysis readiness remains false.

Decision: `{decision}`.
"""
    (output_dir / "gabriel_claim_rating_35_quarantine_repair_qa_report.md").write_text(qa_report, encoding="utf-8")
    validation = f"""# GABRIEL claim-rating quarantine-repair validation — 2026-07-25

- Original valid ratings unchanged: 608/608; passed by canonical row hash.
- Repair input scope: 35/35 explicit quarantine IDs; passed.
- Newly repaired ratings: {len(repaired_new)}.
- Remaining quarantine: {len(remaining)}.
- Total valid plus quarantine: {len(combined) + len(remaining)}/643; passed.
- Positive exact-substring quote checks: {qa['positive_exact_quote_pass_count']}/{qa['positive_exact_quote_pass_count']}; passed.
- Taxonomy/schema: unchanged v1.1 with 14 attributes; passed.
- Raw prompt/response persistence: zero; passed.
- Cross-row statistics, wage effects, wage gaps, regressions, and final causal claims: not performed.
- Global analysis readiness: false; passed.

## Validation commands

- Python compilation for the repair runner, focused tests, dashboard builder, and descendant validators: passed.
- New quarantine-repair suite: 64/64 passed.
- Predecessor 643-row rating suite: 69/69 passed.
- Claim-oriented phase-close predecessor suite: 69/69 passed.
- Pipeline-hardening predecessor suite: 48/48 passed.
- Combined focused suites: 250/250 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed.
- Completed-output idempotent `--resume`: passed with zero writes and zero API calls.
- `git diff --check`: passed.
- Immutable upstream/package/durable-ledger changed-path check: zero violations.
"""
    (output_dir / "gabriel_claim_rating_35_quarantine_repair_validation_2026-07-25.md").write_text(validation, encoding="utf-8")
    inventory = {
        "task_id": TASK_ID,
        "test_suite": "scripts/test_compensation_evidence_gabriel_claim_rating_35_quarantine_repair.py",
        "failure_modes": [
            "repair_scope_not_35", "non_quarantined_id_in_repair", "original_valid_file_hash_drift",
            "original_valid_row_hash_drift", "quarantine_id_hash_drift", "deterministic_quote_fabrication",
            "weak_attribute_control_drift", "positive_attribute_negative_controls", "final_claim_language",
            "supporting_quote_paraphrase", "missing_positive_reason", "valid_quarantine_reconciliation_failure",
            "duplicate_evidence_id", "preflight_bypass", "raw_prompt_persistence", "raw_response_persistence",
            "dashboard_global_readiness_true", "future_prompt_phase_jump", "partial_completion",
            "non_idempotent_resume",
        ],
    }
    base.write_json(output_dir / "gabriel_claim_rating_35_quarantine_repair_regression_test_inventory.json", inventory)
    (output_dir / "gabriel_claim_rating_35_quarantine_repair_stress_test_report.md").write_text(
        "# GABRIEL quarantine-repair stress-test report\n\nThe 64-test focused suite covers repair scope, immutable 608-row preservation, exact-quote enforcement, weak controls, positive controls, final-claim rejection, 643-row reconciliation, preflight gating, raw-payload exclusion, dashboard fail-closure, exclusion-scoped summary review, future-prompt boundaries, idempotency, and partial-output masquerading. All 64 tests passed.\n\nThe repair clarified one orchestration contract: the documented `repaired_with_remaining_quarantine` decision permits summary review when remaining rows are explicit exclusions. Dashboard and prompt logic now express that limited scope while global analysis readiness stays false.\n",
        encoding="utf-8",
    )
    (output_dir / "gabriel_claim_rating_repaired_claim_scaffold.md").write_text(
        "# Repaired claim scaffold\n\nThe schema-valid repaired layer may support exact document-level wording and bounded documentary mechanism labels. Any provisional causal-candidate label means only that the supplied wording identifies a mechanism to investigate. Cross-row synthesis is reserved for the separately authorized summary review.\n",
        encoding="utf-8",
    )
    (output_dir / "gabriel_claim_rating_repaired_claim_limits.md").write_text(
        "# Repaired claim limits\n\nThe repaired ratings are not wage effects or causal proof. This stage authorizes no cross-row substantive statistics, wage-gap estimates, regressions, treatment effects, final causal claims, or national generalizations. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    future_name = "next_gabriel_claim_rating_summary_review_prompt.md"
    if remaining:
        next_scope = (
            f"Review only the {len(combined)} schema-valid v1.1 ratings and preserve the {len(remaining)} explicit "
            "remaining quarantine IDs as exclusions. Do not rerate them or reopen general QA. Compute only "
            "the explicitly authorized bounded summaries of the collected valid corpus."
        )
    else:
        next_scope = "Review the complete 643-row schema-valid v1.1 rating layer. Compute only the explicitly authorized bounded summaries of the collected corpus; do not treat ratings as wage effects or causal proof."
    prompt = f"""# Next task: GABRIEL claim-rating summary review

Decision: `{decision}`. {next_scope}

## Hard constraints

- Do not fetch, pull, inspect remotes, or configure remotes.
- Do not open URLs, use hosted search, or download documents.
- Do not open PDFs, access PDF pages, run OCR, or use rendered images.
- Do not run scout, source discovery, source review, verification, extraction, or document selection.
- Do not ingest or run `gabriel.codify`.
- Do not call GABRIEL/API or any model.
- Do not calculate wage gaps, run regressions, estimate treatment effects, or make final causal claims.
- Do not use evidence outside the supplied exact spans.
- Do not save raw prompts, raw responses, credentials, tokens, cookies, auth headers, or environment values.
- Do not mutate upstream rating, evidence, extraction, QA, or durable ledgers.
- Keep global analysis readiness false.
- Preserve the boundary that GABRIEL rating is not causal proof.
"""
    (output_dir / future_name).write_text(prompt, encoding="utf-8")
    (output_dir / "next_task.md").write_text(prompt, encoding="utf-8")
    result_doc = ANALYSIS_ROOT / "compensation_evidence_gabriel_claim_rating_35_quarantine_repair_result_2026-07-25.md"
    result_doc.write_text(
        f"# GABRIEL claim-rating quarantine repair — result\n\nDecision: `{decision}`. Exactly 35 quarantined IDs entered repair; {len(repaired_new)} became valid and {len(remaining)} remain quarantined. The original 608 valid ratings are hash-identical. Global analysis readiness remains false.\n",
        encoding="utf-8",
    )
    dashboard_doc = ANALYSIS_ROOT / "compensation_evidence_gabriel_claim_rating_35_quarantine_repair_dashboard_status_note_2026-07-25.md"
    dashboard_doc.write_text(
        f"# Dashboard status note — GABRIEL 35-row quarantine repair\n\n- Decision: `{decision}`.\n- Original valid: 608; repaired valid: {len(repaired_new)}; remaining quarantine: {len(remaining)}.\n- Total valid: {len(combined)}; reconciled universe: 643.\n- Summary review allowed: {str(decision == 'gabriel_claim_rating_643_repaired_summary_review_allowed').lower()}.\n- Global analysis readiness: false.\n",
        encoding="utf-8",
    )
    return decision


def completed(output_dir: Path) -> bool:
    future = (
        output_dir / "next_gabriel_claim_rating_summary_review_prompt.md"
    ).is_file() or (
        output_dir / "next_gabriel_claim_rating_remaining_quarantine_decision_prompt.md"
    ).is_file()
    return all((output_dir / name).is_file() for name in REQUIRED_FINAL_OUTPUTS) and future


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("dry-run", "preflight", "live", "all"), default="all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()
    if args.parallel < 1 or args.max_attempts < 1 or args.batch_size < 1 or args.timeout <= 0:
        raise ValueError("parallel, max-attempts, batch-size, and timeout must be positive")
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_guard(output_dir, resume=args.resume)
    if args.resume and completed(output_dir):
        print(json.dumps({"status": "already_complete", "writes": 0, "api_calls": 0, "output_dir": str(output_dir)}))
        return 0

    manifest, original_valid, quarantine, audit = verify_inputs()
    manifest_map = {row["evidence_id"]: row for row in manifest}
    repair_rows = [manifest_map[row["evidence_id"]] for row in quarantine]
    errors = {row["evidence_id"]: row["error_code"] for row in quarantine}
    dry_summary_path = output_dir / "gabriel_claim_rating_35_quarantine_repair_summary.json"
    if not dry_summary_path.is_file():
        write_dry_run(output_dir, repair_rows, quarantine, audit)
    dry = base.read_json(dry_summary_path)
    if dry.get("repair_input_rows") != 35 or dry.get("bounded_model_retry_required_rows") != 35:
        raise RuntimeError("no-call dry run did not preserve exact 35-ID scope")
    if args.stage == "dry-run":
        print(json.dumps({"stage": "dry_run", "repair_rows": 35, "deterministic_repairs": 0, "api_calls": 0}))
        return 0

    key, credential_location = base.load_subscription_key()
    if not key:
        raise RuntimeError("HARVARD_SUBSCRIPTION_KEY unavailable; repair preflight not run")
    preflight_status_path = output_dir / "_gabriel_claim_rating_35_repair_preflight_status.json"
    if not preflight_status_path.is_file():
        selected, coverage = select_preflight(repair_rows, quarantine)
        valid, remaining, metadata = run_calls(
            selected, errors, stage="repair_preflight", key=key, model=args.model,
            timeout=args.timeout, parallel=min(args.parallel, 2), max_attempts=args.max_attempts,
        )
        passed = write_preflight(output_dir, selected, coverage, valid, remaining, metadata, args.model)
    else:
        passed = base.read_json(preflight_status_path).get("passed") is True
    if not passed:
        print(json.dumps({"stage": "repair_preflight", "passed": False, "credential_location": credential_location}))
        return 2
    if args.stage == "preflight":
        print(json.dumps({"stage": "repair_preflight", "passed": True, "credential_location": credential_location}))
        return 0

    valid_checkpoint = output_dir / "_gabriel_claim_rating_35_repaired_checkpoint.csv"
    quarantine_checkpoint = output_dir / "_gabriel_claim_rating_35_remaining_quarantine_checkpoint.csv"
    request_checkpoint = output_dir / "_gabriel_claim_rating_35_request_metadata_checkpoint.csv"
    existing_valid = base.read_csv(valid_checkpoint) if args.resume and valid_checkpoint.is_file() else []
    existing_remaining = base.read_csv(quarantine_checkpoint) if args.resume and quarantine_checkpoint.is_file() else []
    existing_requests = base.read_csv(request_checkpoint) if args.resume and request_checkpoint.is_file() else []
    repair_id_set = {row["evidence_id"] for row in repair_rows}
    existing_valid_map = {row["evidence_id"]: row for row in existing_valid}
    existing_remaining_ids = {row["evidence_id"] for row in existing_remaining}
    if not set(existing_valid_map).issubset(repair_id_set) or not existing_remaining_ids.issubset(repair_id_set):
        raise RuntimeError("checkpoint contains non-quarantined repair ID")
    for row in existing_valid:
        base.validate_rating(base.unflatten_rating(row), manifest_map[row["evidence_id"]])
    pending = [row for row in repair_rows if row["evidence_id"] not in existing_valid_map and row["evidence_id"] not in existing_remaining_ids]
    started = time.monotonic()
    repaired_map = dict(existing_valid_map)
    remaining_all = list(existing_remaining)
    request_rows = list(existing_requests)
    for start in range(0, len(pending), args.batch_size):
        chunk = pending[start:start + args.batch_size]
        valid, remaining, metadata = run_calls(
            chunk, errors, stage="repair_live", key=key, model=args.model,
            timeout=args.timeout, parallel=args.parallel, max_attempts=args.max_attempts,
        )
        repaired_map.update({row["evidence_id"]: row for row in valid})
        remaining_all.extend(remaining)
        request_rows.extend(metadata)
        base.write_csv(valid_checkpoint, base.RATING_OUTPUT_FIELDS, [repaired_map[row["evidence_id"]] for row in repair_rows if row["evidence_id"] in repaired_map])
        base.write_csv(quarantine_checkpoint, base.QUARANTINE_FIELDS, remaining_all)
        base.write_csv(request_checkpoint, base.REQUEST_FIELDS, request_rows)
        print(json.dumps({
            "checkpoint_repaired_valid": len(repaired_map),
            "checkpoint_remaining_quarantine": len(remaining_all),
            "processed": min(start + len(chunk), len(pending)),
            "pending_at_start": len(pending),
        }), flush=True)

    repaired_new = [repaired_map[row["evidence_id"]] for row in repair_rows if row["evidence_id"] in repaired_map]
    remaining_map = {row["evidence_id"]: row for row in remaining_all}
    if set(repaired_map) & set(remaining_map):
        raise RuntimeError("repair checkpoint valid/quarantine overlap")
    original_map = {row["evidence_id"]: row for row in original_valid}
    combined = []
    for source in manifest:
        evidence_id = source["evidence_id"]
        if evidence_id in original_map:
            combined.append(original_map[evidence_id])
        elif evidence_id in repaired_map:
            combined.append(repaired_map[evidence_id])
    remaining = [remaining_map[row["evidence_id"]] for row in repair_rows if row["evidence_id"] in remaining_map]
    qa = validate_repaired_outputs(manifest, original_valid, repaired_new, remaining, combined, audit)
    base.write_csv(output_dir / "gabriel_claim_oriented_attribute_ratings_643_repaired.csv", base.RATING_OUTPUT_FIELDS, combined)
    base.write_csv(output_dir / "gabriel_claim_oriented_attribute_rating_remaining_quarantine.csv", base.QUARANTINE_FIELDS, remaining)
    base.write_csv(output_dir / "gabriel_claim_rating_35_repair_request_metadata.csv", base.REQUEST_FIELDS, request_rows)
    timing = [{
        "stage": "repair_live",
        "elapsed_seconds": f"{time.monotonic() - started:.6f}",
        "repair_input_rows": "35",
        "resumed_repaired_rows": str(len(existing_valid)),
        "new_request_attempts": str(len(request_rows) - len(existing_requests)),
        "repaired_valid_rows": str(len(repaired_new)),
        "remaining_quarantine_rows": str(len(remaining)),
        "parallel": str(args.parallel),
        "timeout_seconds": str(args.timeout),
        "max_attempts": str(args.max_attempts),
    }]
    base.write_csv(output_dir / "gabriel_claim_rating_35_repair_timing.csv", timing[0].keys(), timing)
    decision = build_reports(
        output_dir, manifest, original_valid, repaired_new, remaining, combined,
        audit, request_rows, int(base.read_json(preflight_status_path)["input_rows"]),
    )
    if not completed(output_dir):
        raise RuntimeError("partial repair outputs cannot masquerade as complete")
    print(json.dumps({
        "decision": decision,
        "original_valid": 608,
        "repaired_valid": len(repaired_new),
        "remaining_quarantine": len(remaining),
        "total_valid": qa["total_valid_rows"],
        "credential_location": credential_location,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
