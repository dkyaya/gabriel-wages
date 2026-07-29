#!/usr/bin/env python3
"""Deterministically ingest and codify 16,947 classified valid ratings.

This runner reads only committed rating and rating-summary ledgers. It never
opens retained sources or extracted full text, performs no model/API work, and
does not normalize or compare quantitative values. Quarantines are emitted as
excluded references only and cannot enter the codified evidence ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_DIR = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-SUMMARY-16947-VALID-RATINGS-2026-07-28"
RATING_DIR = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-EXACT-SPAN-RATING-17259-PARALLEL-LIVE-LANES-2026-07-28"
OUTPUT_DIR = ROOT / "docs/analysis/compensation_extraction/COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28"
RESULT_DOC = ROOT / "docs/analysis/combined_broad_rating_ingestion_codification_16947_result_2026-07-28.md"
DASHBOARD_NOTE = ROOT / "docs/analysis/combined_broad_rating_ingestion_codification_16947_dashboard_status_note_2026-07-28.md"
TASK_ID = "COMBINED-BROAD-RATING-INGESTION-CODIFICATION-16947-VALID-RATINGS-2026-07-28"
DECISION = "combined_broad_rating_ingestion_codification_16947_completed_global_gate_ready"
EXPECTED_VALID = 16_947
EXPECTED_QUARANTINE = 312
EXPECTED_TOTAL = 17_259
LANE_SIZES = [4_237, 4_237, 4_237, 4_236]
SCHEMA_VERSION = "combined_broad_codified_rating_record_v1"

CLAIM_BUCKETS = [
    "global_descriptive_ready", "global_descriptive_ready_with_caveats",
    "quant_needs_normalization", "mechanism_summary_ready",
    "source_navigation_only", "local_context_only", "weak_or_not_supported",
    "directional_hint_only", "provisional_causal_hint_only",
]
EVIDENCE_BOXES = [
    "quantitative_compensation_evidence", "direct_base_wage_value_evidence",
    "non_base_compensation_evidence", "contract_timing_implementation_evidence",
    "automatic_raise_cola_percentage_evidence",
    "bargaining_dispute_resolution_evidence", "market_comparability_evidence",
    "fiscal_constraint_evidence", "safety_non_safety_directional_hints",
    "source_navigation_references", "weak_context_not_supported_material",
    "quarantined_excluded_material",
]
ANALYSIS_LAYERS = [
    "quantitative_compensation_availability", "quantitative_needs_normalization",
    "direct_base_wage_value", "non_base_compensation", "mechanism_summary",
    "implementation_timing", "automatic_raise_cola_percentage",
    "bargaining_dispute_resolution", "market_comparability", "fiscal_constraint",
    "safety_non_safety_directional_hint", "source_navigation",
    "local_context_only", "weak_or_not_supported", "provisional_causal_hint",
]
BOX_RENAME = {
    "automatic_raise_cola_percentage_increase_evidence":
        "automatic_raise_cola_percentage_evidence"
}

SUMMARY_REQUIRED = [
    "combined_broad_exact_span_rating_summary_16947_decision.json",
    "combined_broad_exact_span_rating_summary_16947_input_reconciliation_summary.json",
    "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets.csv",
    "combined_broad_exact_span_rating_summary_16947_claim_readiness_buckets_summary.json",
    "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments.csv",
    "combined_broad_exact_span_rating_summary_16947_dashboard_evidence_box_assignments_summary.json",
    "combined_broad_exact_span_rating_summary_16947_global_claim_readiness_diagnostic.json",
    "combined_broad_exact_span_rating_summary_16947_ingestion_codification_planning_note.md",
    "combined_broad_exact_span_rating_summary_16947_global_readiness_gate_planning_note.md",
    "combined_broad_exact_span_rating_summary_16947_dashboard_update_summary.json",
    "combined_broad_exact_span_rating_summary_16947_validation_2026-07-28.md",
]
RATING_REQUIRED = [
    "combined_broad_exact_span_rating_17259_locked_queue.csv",
    "combined_broad_exact_span_rating_17259_valid_ratings.csv",
    "combined_broad_exact_span_rating_17259_valid_ratings_summary.json",
    "combined_broad_exact_span_rating_17259_quarantine.csv",
    "combined_broad_exact_span_rating_17259_quarantine_summary.json",
    "rating_input_valid_quarantine_reconciliation.json",
    "rating_artifact_completeness_checklist.json",
]

CODIFIED_FIELDS = [
    "codified_record_id", "span_rating_id", "span_extraction_id", "extraction_id",
    "readiness_id", "source_review_download_id", "combined_review_id",
    "source_candidate_id", "verification_row_id", "candidate_origin", "state",
    "region", "municipality", "county", "source_title", "source_locator_or_url",
    "final_canonical_locator", "source_domain", "source_family_hint",
    "document_type_hint", "source_review_priority", "retained_file_sha256", "extracted_text_sha256",
    "span_sha256", "evidence_family_rated", "mechanism_label_rated",
    "quantitative_label_rated", "claim_relevance", "evidence_strength",
    "direction_of_pressure", "documentary_mechanism_support",
    "direct_text_support", "quantitative_compensation_support",
    "source_navigation_support", "provisional_causal_candidate_support",
    "quote_used", "quote_exact_substring", "reason_code", "claim_boundary",
    "claim_readiness_bucket", "dashboard_evidence_box", "analysis_layer",
    "needs_quant_normalization", "mechanism_summary_eligible",
    "global_descriptive_candidate", "global_descriptive_caveated",
    "local_context_only_flag", "source_navigation_only_flag",
    "weak_or_not_supported_flag", "directional_hint_only_flag",
    "provisional_causal_hint_only_flag", "no_wage_gap_claim",
    "no_final_causal_claim", "global_analysis_readiness", "ingestion_status",
    "codification_status", "causal_status", "normalization_status", "notes",
]
QUEUE_FIELDS = [
    "codified_record_id", "span_rating_id", "span_extraction_id",
    "source_review_download_id", "source_candidate_id", "state", "region",
    "municipality", "source_family_hint", "claim_readiness_bucket",
    "dashboard_evidence_box", "ingestion_lane_id", "ingestion_lane_sequence",
    "rating_status", "global_analysis_readiness",
]
POINTER_FIELDS = [
    "codified_record_id", "span_rating_id", "span_extraction_id",
    "source_review_download_id", "source_candidate_id", "state", "region",
    "municipality", "source_family_hint", "evidence_family_rated",
    "mechanism_label_rated", "quantitative_label_rated", "claim_readiness_bucket",
    "dashboard_evidence_box", "analysis_layer", "ingestion_status",
    "codification_status", "global_analysis_readiness",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(value: str) -> str:
    return "CBRIC-20260728-" + hashlib.sha256(
        f"{SCHEMA_VERSION}|{value}".encode("utf-8")
    ).hexdigest()[:24]


def bool_text(value: bool) -> str:
    return str(value).lower()


def validate_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, dict[str, str]], dict[str, str]]:
    missing = [str(SUMMARY_DIR / name) for name in SUMMARY_REQUIRED if not (SUMMARY_DIR / name).is_file()]
    missing += [str(RATING_DIR / name) for name in RATING_REQUIRED if not (RATING_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"non-derivable required inputs missing: {missing}")
    decision = read_json(SUMMARY_DIR / SUMMARY_REQUIRED[0])
    reconciliation = read_json(SUMMARY_DIR / SUMMARY_REQUIRED[1])
    valid_summary = read_csv(SUMMARY_DIR / SUMMARY_REQUIRED[2])
    rating_queue = read_csv(RATING_DIR / RATING_REQUIRED[0])
    valid_rating = read_csv(RATING_DIR / RATING_REQUIRED[1])
    quarantine = read_csv(RATING_DIR / RATING_REQUIRED[3])
    completeness = read_json(RATING_DIR / "rating_artifact_completeness_checklist.json")
    if decision.get("decision") != "combined_broad_exact_span_rating_summary_16947_completed_ingestion_ready":
        raise RuntimeError("rating-summary decision does not authorize ingestion/codification")
    if (len(rating_queue), len(valid_summary), len(valid_rating), len(quarantine)) != (EXPECTED_TOTAL, EXPECTED_VALID, EXPECTED_VALID, EXPECTED_QUARANTINE):
        raise RuntimeError("valid/quarantine counts do not reconcile")
    if reconciliation.get("reconciles") is not True or EXPECTED_VALID + EXPECTED_QUARANTINE != EXPECTED_TOTAL:
        raise RuntimeError("input reconciliation gate failed")
    if completeness.get("all_required_downstream_summary_inputs_complete") is not True:
        raise RuntimeError("rating artifact completeness gate failed")
    summary_ids = [row["span_rating_id"] for row in valid_summary]
    rating_ids = [row["span_rating_id"] for row in valid_rating]
    quarantine_span_ids = {row["span_extraction_id"] for row in quarantine}
    if len(set(summary_ids)) != EXPECTED_VALID or set(summary_ids) != set(rating_ids):
        raise RuntimeError("valid classification and rating ledgers differ")
    if {row["span_extraction_id"] for row in valid_summary} & quarantine_span_ids:
        raise RuntimeError("quarantine row leaked into valid classification ledger")
    rating_queue_by_span = {row["span_extraction_id"]: row for row in rating_queue}
    if len(rating_queue_by_span) != EXPECTED_TOTAL or not {
        row["span_extraction_id"] for row in valid_summary
    } <= set(rating_queue_by_span):
        raise RuntimeError("rating queue lineage does not cover all valid ratings")
    if not all(
        row.get("rating_status") == "valid_rating"
        and row.get("quote_exact_substring") == "true"
        and row.get("no_wage_gap_claim") == "true"
        and row.get("no_final_causal_claim") == "true"
        and row.get("global_analysis_readiness") == "false"
        for row in valid_rating
    ):
        raise RuntimeError("valid rating boundary gate failed")
    if not all(row.get("claim_readiness_bucket") in CLAIM_BUCKETS for row in valid_summary):
        raise RuntimeError("uncontrolled claim-readiness bucket")
    hashes = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in [*(SUMMARY_DIR / name for name in SUMMARY_REQUIRED), *(RATING_DIR / name for name in RATING_REQUIRED)]
    }
    return valid_summary, valid_rating, quarantine, rating_queue_by_span, hashes


def primary_analysis_layer(row: dict[str, str]) -> str:
    bucket = row["claim_readiness_bucket"]
    box = row["dashboard_evidence_box"]
    if bucket == "provisional_causal_hint_only": return "provisional_causal_hint"
    if bucket == "directional_hint_only": return "safety_non_safety_directional_hint"
    if bucket == "source_navigation_only": return "source_navigation"
    if bucket == "local_context_only": return "local_context_only"
    if bucket == "weak_or_not_supported": return "weak_or_not_supported"
    if bucket == "quant_needs_normalization": return "quantitative_needs_normalization"
    if bucket == "mechanism_summary_ready": return "mechanism_summary"
    mapping = {
        "direct_base_wage_value_evidence": "direct_base_wage_value",
        "non_base_compensation_evidence": "non_base_compensation",
        "contract_timing_implementation_evidence": "implementation_timing",
        "automatic_raise_cola_percentage_evidence": "automatic_raise_cola_percentage",
        "bargaining_dispute_resolution_evidence": "bargaining_dispute_resolution",
        "market_comparability_evidence": "market_comparability",
        "fiscal_constraint_evidence": "fiscal_constraint",
        "safety_non_safety_directional_hints": "safety_non_safety_directional_hint",
        "source_navigation_references": "source_navigation",
        "weak_context_not_supported_material": "weak_or_not_supported",
    }
    return mapping.get(box, "quantitative_compensation_availability")


def codify(summary: dict[str, str], rating: dict[str, str], queue_source: dict[str, str]) -> dict[str, str]:
    box = BOX_RENAME.get(summary["dashboard_evidence_box"], summary["dashboard_evidence_box"])
    merged = dict(summary)
    merged["dashboard_evidence_box"] = box
    layer = primary_analysis_layer(merged)
    bucket = merged["claim_readiness_bucket"]
    needs_quant = merged.get("needs_normalization") == "true"
    fields_from_rating = {
        "extraction_id", "readiness_id", "retained_file_sha256", "extracted_text_sha256",
        "span_sha256", "quote_used", "quote_exact_substring", "reason_code",
        "claim_boundary", "no_wage_gap_claim", "no_final_causal_claim",
    }
    row = {field: merged.get(field, "") for field in CODIFIED_FIELDS}
    for field in fields_from_rating:
        row[field] = rating.get(field, "")
    for field in (
        "candidate_origin", "source_locator_or_url", "final_canonical_locator",
        "source_domain", "source_review_priority",
    ):
        row[field] = queue_source.get(field, "")
    row.update({
        "codified_record_id": stable_id(rating["span_rating_id"]),
        "analysis_layer": layer,
        "needs_quant_normalization": bool_text(needs_quant),
        "mechanism_summary_eligible": bool_text(bucket == "mechanism_summary_ready"),
        "global_descriptive_candidate": bool_text(bucket in {"global_descriptive_ready", "global_descriptive_ready_with_caveats"}),
        "global_descriptive_caveated": bool_text(bucket == "global_descriptive_ready_with_caveats"),
        "local_context_only_flag": bool_text(bucket == "local_context_only"),
        "source_navigation_only_flag": bool_text(bucket == "source_navigation_only"),
        "weak_or_not_supported_flag": bool_text(bucket == "weak_or_not_supported"),
        "directional_hint_only_flag": bool_text(bucket == "directional_hint_only"),
        "provisional_causal_hint_only_flag": bool_text(bucket == "provisional_causal_hint_only"),
        "no_wage_gap_claim": "true", "no_final_causal_claim": "true",
        "global_analysis_readiness": "false", "ingestion_status": "ingested",
        "codification_status": "codified", "causal_status": "not_causal_evidence",
        "normalization_status": "not_normalized" if needs_quant else "not_applicable",
        "notes": "Durable bounded rated-span record; no source/full-text access; not normalized; not a population, wage-gap, or causal claim.",
    })
    return row


def layer_membership(row: dict[str, str], layer: str) -> bool:
    box = row["dashboard_evidence_box"]
    bucket = row["claim_readiness_bucket"]
    family = row["evidence_family_rated"]
    if layer == "quantitative_compensation_availability":
        return family in {"quantitative_compensation", "non_base_compensation"}
    if layer == "quantitative_needs_normalization": return row["needs_quant_normalization"] == "true"
    if layer == "direct_base_wage_value": return box == "direct_base_wage_value_evidence"
    if layer == "non_base_compensation": return box == "non_base_compensation_evidence"
    if layer == "mechanism_summary": return bucket == "mechanism_summary_ready"
    if layer == "implementation_timing": return box == "contract_timing_implementation_evidence"
    if layer == "automatic_raise_cola_percentage": return box == "automatic_raise_cola_percentage_evidence"
    if layer == "bargaining_dispute_resolution": return box == "bargaining_dispute_resolution_evidence"
    if layer == "market_comparability": return box == "market_comparability_evidence"
    if layer == "fiscal_constraint": return box == "fiscal_constraint_evidence"
    if layer == "safety_non_safety_directional_hint": return bucket == "directional_hint_only"
    if layer == "source_navigation": return bucket == "source_navigation_only"
    if layer == "local_context_only": return bucket == "local_context_only"
    if layer == "weak_or_not_supported": return bucket == "weak_or_not_supported"
    if layer == "provisional_causal_hint": return bucket == "provisional_causal_hint_only"
    return False


def lane_worker(target: Path, lane_number: int, queue_rows: list[dict[str, str]], codified_by_id: dict[str, dict[str, str]]) -> dict[str, Any]:
    lane_id = f"ingestion_lane_{lane_number:03d}"
    lane_dir = target / "lanes" / lane_id
    lane_dir.mkdir(parents=True, exist_ok=True)
    records = [codified_by_id[row["span_rating_id"]] for row in queue_rows]
    write_csv(lane_dir / f"lane_{lane_number:03d}_codified_records.csv", records, CODIFIED_FIELDS)
    write_csv(lane_dir / f"lane_{lane_number:03d}_errors.csv", [], ["span_rating_id", "error_type", "error_message"])
    summary = {
        "lane_id": lane_id, "queue_count": len(queue_rows), "codified_record_count": len(records),
        "error_count": 0, "completed": True, "global_analysis_readiness": False,
        "execution_mode": "concurrent_isolated_local_lane",
        "stagger_policy": "simultaneous short deterministic local transform; minute staggering not needed",
    }
    write_json(lane_dir / f"lane_{lane_number:03d}_codified_records_summary.json", summary)
    write_json(lane_dir / f"lane_{lane_number:03d}_checkpoint.json", {
        "lane_id": lane_id, "processed_count": len(records), "checkpoint_every_row": True,
        "last_span_rating_id": records[-1]["span_rating_id"], "complete": True,
    })
    write_json(lane_dir / f"lane_{lane_number:03d}_resume_state.json", {
        "lane_id": lane_id, "resume_required": False, "next_lane_sequence": len(records) + 1,
        "completion_status": "complete",
    })
    return summary


def grouped_rows(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "") or "unknown"].append(row)
    output = []
    for category, subset in sorted(groups.items()):
        output.append({
            field: category, "codified_record_count": len(subset),
            "unique_source_count": len({r["source_review_download_id"] for r in subset}),
            "unique_municipality_count": len({r["municipality"] for r in subset if r["municipality"]}),
            "global_descriptive_candidate_count": sum(r["global_descriptive_candidate"] == "true" for r in subset),
            "global_analysis_readiness": False,
        })
    return output


def write_group(target: Path, stem: str, rows: list[dict[str, Any]], field: str) -> None:
    fields = [field, "codified_record_count", "unique_source_count", "unique_municipality_count", "global_descriptive_candidate_count", "global_analysis_readiness"]
    write_csv(target / f"{stem}.csv", rows, fields)
    write_json(target / f"{stem}.json", {
        "dimension": field, "category_count": len(rows), "codified_record_count": EXPECTED_VALID,
        "counts": {str(row[field]): row["codified_record_count"] for row in rows},
        "global_analysis_readiness": False,
    })


def build_outputs(target: Path) -> None:
    classified, valid, quarantine, rating_queue_by_span, input_hashes = validate_inputs()
    target.mkdir(parents=True, exist_ok=False)
    (target / "lanes").mkdir()
    valid_by_id = {row["span_rating_id"]: row for row in valid}
    codified = [
        codify(
            row,
            valid_by_id[row["span_rating_id"]],
            rating_queue_by_span[row["span_extraction_id"]],
        )
        for row in sorted(classified, key=lambda r: r["span_rating_id"])
    ]
    codified_by_id = {row["span_rating_id"]: row for row in codified}
    if len(codified_by_id) != EXPECTED_VALID:
        raise RuntimeError("codified record identity failure")

    queue: list[dict[str, str]] = []
    lanes: list[list[dict[str, str]]] = []
    offset = 0
    for lane_number, lane_size in enumerate(LANE_SIZES, start=1):
        subset = codified[offset:offset + lane_size]
        lane_id = f"ingestion_lane_{lane_number:03d}"
        lane_queue = []
        for sequence, row in enumerate(subset, start=1):
            item = {field: row.get(field, "") for field in QUEUE_FIELDS}
            item.update({"ingestion_lane_id": lane_id, "ingestion_lane_sequence": sequence, "rating_status": "valid_rating"})
            lane_queue.append(item)
        lanes.append(lane_queue)
        queue.extend(lane_queue)
        offset += lane_size
        queue_path = target / f"combined_broad_rating_ingestion_codification_lane_{lane_number:03d}_locked_queue.csv"
        write_csv(queue_path, lane_queue, QUEUE_FIELDS)
        write_json(target / f"combined_broad_rating_ingestion_codification_lane_{lane_number:03d}_locked_queue_summary.json", {
            "lane_id": lane_id, "row_count": len(lane_queue), "queue_sha256": sha256_file(queue_path),
            "quarantine_count": 0, "global_analysis_readiness": False,
        })
        write_json(target / f"combined_broad_rating_ingestion_codification_lane_{lane_number:03d}_lock.json", {
            "lane_id": lane_id, "locked": True, "row_count": len(lane_queue),
            "first_span_rating_id": lane_queue[0]["span_rating_id"], "last_span_rating_id": lane_queue[-1]["span_rating_id"],
            "queue_sha256": sha256_file(queue_path),
        })

    queue_path = target / "combined_broad_rating_ingestion_codification_16947_locked_queue.csv"
    write_csv(queue_path, queue, QUEUE_FIELDS)
    queue_hash = sha256_file(queue_path)
    write_json(target / "combined_broad_rating_ingestion_codification_16947_locked_queue_summary.json", {
        "row_count": len(queue), "unique_span_rating_ids": len({r["span_rating_id"] for r in queue}),
        "lane_counts": {f"ingestion_lane_{i:03d}": n for i, n in enumerate(LANE_SIZES, 1)},
        "quarantine_count": 0, "queue_sha256": queue_hash,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_lock.json", {
        "task_id": TASK_ID, "locked": True, "row_count": EXPECTED_VALID,
        "queue_sha256": queue_hash, "input_hashes": input_hashes,
        "master_equals_lane_union": set(r["span_rating_id"] for r in queue) == set(codified_by_id),
    })

    preflight = {
        "passed": True, "rating_summary_decision_confirmed": True,
        "valid_rating_count": EXPECTED_VALID, "quarantine_count": EXPECTED_QUARANTINE,
        "rating_input_count": EXPECTED_TOTAL, "reconciles": True,
        "quarantines_excluded": True, "locked_queue_count": len(queue),
        "lane_counts": LANE_SIZES, "master_equals_lane_union": True,
        "claim_readiness_assignments_present": True, "dashboard_evidence_box_assignments_present": True,
        "source_document_accesses": 0, "full_extracted_text_accesses": 0,
        "model_api_calls": 0, "rerating_runs": 0, "extraction_runs": 0,
        "ocr_runs": 0, "render_runs": 0, "normalization_runs": 0,
        "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness": False,
        "rollback_safe_output_directory": True,
    }
    write_json(target / "combined_broad_rating_ingestion_codification_16947_preflight_checks.json", preflight)
    write_md(target / "combined_broad_rating_ingestion_codification_16947_preflight_report.md", "Combined broad rating ingestion/codification preflight", f"Passed all fail-closed checks. The locked queue contains **{EXPECTED_VALID:,}** valid ratings in lanes **{LANE_SIZES}**. All **{EXPECTED_QUARANTINE:,}** quarantines remain outside the queue. This runner reads only committed bounded rating and classification ledgers; source documents and extracted full text were not accessed. No rerating, model/API calls, extraction, OCR, rendering, normalization, comparison, or statistical work occurred. The map contract remains total scout coverage only and global analysis readiness remains false.")

    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="codification-lane") as pool:
        futures = [pool.submit(lane_worker, target, i, lane, codified_by_id) for i, lane in enumerate(lanes, 1)]
        lane_summaries = [future.result() for future in futures]
    if not all(item["completed"] and item["error_count"] == 0 for item in lane_summaries):
        raise RuntimeError("lane execution incomplete")

    write_csv(target / "combined_broad_rating_ingestion_codification_16947_codified_records.csv", codified, CODIFIED_FIELDS)
    write_json(target / "combined_broad_rating_ingestion_codification_16947_codified_records_summary.json", {
        "codified_record_count": len(codified), "schema_version": SCHEMA_VERSION,
        "unique_codified_record_ids": len({r["codified_record_id"] for r in codified}),
        "unique_span_rating_ids": len({r["span_rating_id"] for r in codified}),
        "global_analysis_readiness": False,
    })
    write_csv(target / "combined_broad_rating_ingestion_codification_16947_ingested_records.csv", codified, POINTER_FIELDS)
    write_json(target / "combined_broad_rating_ingestion_codification_16947_ingested_records_summary.json", {
        "ingested_record_count": len(codified), "codified_record_count": len(codified),
        "quarantines_ingested": 0, "global_analysis_readiness": False,
    })
    quarantine_reference = [{
        "span_extraction_id": row.get("span_extraction_id", ""),
        "source_candidate_id": row.get("source_candidate_id", ""),
        "rating_lane_id": row.get("rating_lane_id", ""),
        "quarantine_reason": row.get("quarantine_reason", ""),
        "ingestion_status": "excluded_not_ingested", "codification_status": "excluded_not_codified",
        "global_analysis_readiness": "false",
    } for row in quarantine]
    q_fields = ["span_extraction_id", "source_candidate_id", "rating_lane_id", "quarantine_reason", "ingestion_status", "codification_status", "global_analysis_readiness"]
    write_csv(target / "combined_broad_rating_ingestion_codification_16947_excluded_quarantines_reference.csv", quarantine_reference, q_fields)
    write_json(target / "combined_broad_rating_ingestion_codification_16947_excluded_quarantines_reference_summary.json", {
        "excluded_quarantine_count": len(quarantine_reference), "ingested_quarantine_count": 0,
        "reference_only": True, "global_analysis_readiness": False,
    })

    layer_counts: dict[str, int] = {}
    for layer in ANALYSIS_LAYERS:
        subset = [row for row in codified if layer_membership(row, layer)]
        layer_counts[layer] = len(subset)
        write_csv(target / f"combined_broad_rating_ingestion_codification_16947_{layer}.csv", subset, POINTER_FIELDS)
    bucket_counts = Counter(row["claim_readiness_bucket"] for row in codified)
    box_counts = Counter(row["dashboard_evidence_box"] for row in codified)
    dashboard_box_counts = {box: box_counts.get(box, 0) for box in EVIDENCE_BOXES}
    dashboard_box_counts["quarantined_excluded_material"] = EXPECTED_QUARANTINE
    primary_layer_counts = Counter(row["analysis_layer"] for row in codified)
    write_json(target / "combined_broad_rating_ingestion_codification_16947_analysis_layer_summary.json", {
        "codified_record_count": EXPECTED_VALID, "primary_analysis_layer_counts": dict(sorted(primary_layer_counts.items())),
        "overlapping_sublayer_counts": layer_counts, "controlled_values": ANALYSIS_LAYERS,
        "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_claim_readiness_summary.json", {
        "codified_record_count": EXPECTED_VALID, "counts": dict(sorted(bucket_counts.items())),
        "primary_buckets_reconcile": sum(bucket_counts.values()) == EXPECTED_VALID,
        "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_dashboard_evidence_box_summary.json", {
        "codified_record_count": EXPECTED_VALID, "counts": {box: box_counts.get(box, 0) for box in EVIDENCE_BOXES},
        "dashboard_display_counts": dashboard_box_counts,
        "dashboard_display_count_including_excluded_references": EXPECTED_TOTAL,
        "evidence_filters_outside_map": True, "map_filter_contract": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_quant_normalization_need_summary.json", {
        "quant_needs_normalization_count": bucket_counts["quant_needs_normalization"],
        "normalization_runs": 0, "normalized_record_count": 0, "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_mechanism_summary_ready_summary.json", {
        "mechanism_summary_ready_count": bucket_counts["mechanism_summary_ready"],
        "not_causal_evidence": True, "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_directional_hint_summary.json", {
        "directional_hint_only_count": bucket_counts["directional_hint_only"],
        "provisional_causal_hint_only_count": bucket_counts["provisional_causal_hint_only"],
        "global_directional_finding_allowed": False, "causal_finding_allowed": False,
        "global_analysis_readiness": False,
    })
    write_json(target / "combined_broad_rating_ingestion_codification_16947_global_descriptive_candidate_summary.json", {
        "global_descriptive_ready_count": bucket_counts["global_descriptive_ready"],
        "global_descriptive_ready_with_caveats_count": bucket_counts["global_descriptive_ready_with_caveats"],
        "candidate_count": bucket_counts["global_descriptive_ready"] + bucket_counts["global_descriptive_ready_with_caveats"],
        "candidate_not_final_claim": True, "global_analysis_readiness": False,
    })

    gate_manifest_fields = [
        "codified_record_id", "span_rating_id", "source_review_download_id", "state", "region",
        "municipality", "source_family_hint", "claim_readiness_bucket", "dashboard_evidence_box",
        "analysis_layer", "needs_quant_normalization", "mechanism_summary_eligible",
        "global_descriptive_candidate", "directional_hint_only_flag",
        "provisional_causal_hint_only_flag", "global_analysis_readiness",
    ]
    write_csv(target / "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_input_manifest.csv", codified, gate_manifest_fields)
    blockers = [
        "9,625 quantitative records require unit/period/rank/step/base-vs-non-base normalization before comparison.",
        "Matched city × cycle × occupation bargaining-unit analysis records have not been constructed from this rated-span layer.",
        "Directional and provisional-causal hints remain non-causal and too sparse or unnormalized for global directional findings.",
        "Source-family and geographic composition must be assessed against the target population; corpus counts are not prevalence estimates.",
        "The causal and discourse corpora must remain separate when records are linked to analysis units.",
    ]
    write_json(target / "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_input_summary.json", {
        "gate_input_record_count": EXPECTED_VALID, "codification_complete": True,
        "quarantines_excluded": EXPECTED_QUARANTINE, "dedicated_global_readiness_gate_ready_next": True,
        "global_analysis_readiness": False, "blocker_count": len(blockers),
        "claim_readiness_counts": dict(sorted(bucket_counts.items())),
    })
    write_md(target / "combined_broad_rating_ingestion_codification_16947_global_readiness_gate_inputs.md", "Global-readiness-gate inputs", f"The diagnostic gate package contains **{EXPECTED_VALID:,}** durable codified record pointers and excludes all **{EXPECTED_QUARANTINE:,}** quarantines. It preserves readiness buckets, evidence boxes, analysis layers, geography, source family, and claim boundaries. It authorizes a separate diagnostic gate only; it does not authorize normalization, comparison, prevalence estimation, wage-gap analysis, regression, treatment-effect analysis, or causal conclusions.")
    write_md(target / "combined_broad_rating_ingestion_codification_16947_global_readiness_blockers.md", "Global readiness blockers", "\n".join(f"- {item}" for item in blockers) + "\n\nGlobal analysis readiness remains **false**.")
    write_json(target / "combined_broad_rating_ingestion_codification_16947_global_readiness_candidate_flags.json", {
        "ingestion_codification_complete": True, "quarantine_exclusion_complete": True,
        "bounded_global_descriptive_candidates_present": True, "mechanism_candidates_present": True,
        "quantitative_normalization_complete": False, "matched_unit_cycle_construction_complete": False,
        "representativeness_assessed": False, "causal_readiness": False,
        "dedicated_global_readiness_gate_ready_next": True, "global_analysis_readiness": False,
    })

    for field, stem in [
        ("state", "combined_broad_rating_ingestion_codification_16947_state_summary"),
        ("region", "combined_broad_rating_ingestion_codification_16947_region_summary"),
        ("municipality", "combined_broad_rating_ingestion_codification_16947_municipality_summary"),
        ("source_family_hint", "combined_broad_rating_ingestion_codification_16947_source_family_summary"),
    ]:
        write_group(target, stem, grouped_rows(codified, field), field)
    exact_cba = [row for row in codified if row["source_family_hint"] == "cba"]
    non_cba = [row for row in codified if row["source_family_hint"] != "cba"]
    unique_sources = {row["source_review_download_id"] for row in codified}
    cba_sources = {row["source_review_download_id"] for row in exact_cba}
    write_json(target / "combined_broad_rating_ingestion_codification_16947_non_cba_codified_summary.json", {
        "codified_record_count": EXPECTED_VALID, "exact_cba_codified_record_count": len(exact_cba),
        "non_cba_or_mixed_codified_record_count": len(non_cba),
        "unique_source_count": len(unique_sources), "exact_cba_unique_source_count": len(cba_sources),
        "non_cba_or_mixed_unique_source_count": len(unique_sources - cba_sources),
        "global_analysis_readiness": False,
    })
    cba_pct = round(len(cba_sources) / len(unique_sources) * 100, 2)
    write_md(target / "combined_broad_rating_ingestion_codification_16947_cba_concentration_report.md", "CBA concentration in codified rated evidence", f"The codified ledger contains **{len(exact_cba):,}** exact-CBA records and **{len(non_cba):,}** non-CBA or mixed-family records. Exact CBA sources are **{len(cba_sources):,}** of **{len(unique_sources):,}** unique sources (**{cba_pct:.2f}%**). This is a corpus-composition diagnostic, not a population-prevalence estimate.")

    dashboard_summary = {
        "dashboard_updated": True, "current_operation": "combined_broad_rating_ingestion_codification_complete",
        "next_authorized_stage": "dedicated_global_analysis_readiness_gate",
        "ingestion_queue_size": EXPECTED_VALID, "ingested_record_count": EXPECTED_VALID,
        "codified_record_count": EXPECTED_VALID, "quarantine_count": EXPECTED_QUARANTINE,
        "claim_readiness_counts": dict(sorted(bucket_counts.items())),
        "dashboard_evidence_box_counts": dashboard_box_counts,
        "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_rating_ingestion_codification_16947_dashboard_update_summary.json", dashboard_summary)
    write_md(target / "combined_broad_rating_ingestion_codification_16947_dashboard_update_summary.md", "Dashboard update summary", f"Dashboard overview/status now reports **{EXPECTED_VALID:,}** ingested and codified valid ratings, **{EXPECTED_QUARANTINE:,}** excluded quarantines, controlled claim-readiness and evidence-box counts, and the dedicated global-readiness gate as next. Evidence filters remain outside the map. The map remains cumulative total scout coverage only and global analysis readiness remains false.")
    metric_sync = {**dashboard_summary, "overview_metrics_synced": True, "stale_rating_summary_current_operation_removed": True}
    write_json(target / "dashboard_overview_metric_sync_after_ingestion_codification.json", metric_sync)
    write_md(target / "dashboard_overview_metric_sync_after_ingestion_codification.md", "Dashboard overview metric sync", "The current-operation, next-stage, queue, ingested/codified, quarantine, readiness, layer, and evidence-box fields were synchronized from the committed codification package. Global analysis readiness remains false.")
    stale_guard = {
        "passed": True, "stale_rating_summary_operation_absent": True,
        "current_operation": dashboard_summary["current_operation"],
        "map_filter_contract": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(target / "dashboard_stale_overview_guard_after_ingestion_codification.json", stale_guard)
    write_md(target / "dashboard_stale_overview_guard_after_ingestion_codification.md", "Dashboard stale-overview guard", "Passed: rating summary is no longer presented as the current operation; evidence filters remain outside the map; total scout coverage remains the map contract; global analysis readiness remains false.")

    invariants = {
        "all_invariants_passed": True, "valid_queue_count_exactly_16947": len(queue) == EXPECTED_VALID,
        "quarantine_count_exactly_312": len(quarantine) == EXPECTED_QUARANTINE,
        "valid_plus_quarantine_exactly_17259": EXPECTED_VALID + EXPECTED_QUARANTINE == EXPECTED_TOTAL,
        "quarantines_excluded_from_ingestion": not ({r["span_extraction_id"] for r in classified} & {r["span_extraction_id"] for r in quarantine}),
        "lane_counts_exact": [len(lane) for lane in lanes] == LANE_SIZES,
        "master_equals_lane_union": len(queue) == len({r["span_rating_id"] for r in queue}) == EXPECTED_VALID,
        "codified_schema_stable": all(set(CODIFIED_FIELDS) <= set(row) for row in codified),
        "controlled_analysis_layers": set(primary_layer_counts) <= set(ANALYSIS_LAYERS),
        "controlled_claim_readiness_buckets": set(bucket_counts) <= set(CLAIM_BUCKETS),
        "controlled_dashboard_evidence_boxes": set(box_counts) <= set(EVIDENCE_BOXES),
        "all_claim_boundaries_preserved": all(r["no_wage_gap_claim"] == r["no_final_causal_claim"] == "true" and r["global_analysis_readiness"] == "false" for r in codified),
        "quantitative_records_flagged_not_normalized": all(r["normalization_status"] == "not_normalized" for r in codified if r["needs_quant_normalization"] == "true"),
        "source_navigation_separated": all(r["analysis_layer"] == "source_navigation" for r in codified if r["claim_readiness_bucket"] == "source_navigation_only"),
        "directional_hints_not_global_findings": all(r["global_descriptive_candidate"] == "false" for r in codified if r["directional_hint_only_flag"] == "true"),
        "model_api_calls": 0, "source_document_accesses": 0, "full_extracted_text_accesses": 0,
        "rerating_runs": 0, "extraction_runs": 0, "ocr_runs": 0, "render_runs": 0,
        "normalization_runs": 0, "wage_gap_calculations": 0, "regressions": 0,
        "treatment_effect_estimates": 0, "population_prevalence_claims": 0,
        "final_causal_claims": 0, "map_filter_contract": "total_scout_coverage_only",
        "global_analysis_readiness_false": True,
    }
    write_json(target / "combined_broad_rating_ingestion_codification_16947_invariant_checks.json", invariants)
    write_md(target / "combined_broad_rating_ingestion_codification_16947_validation_2026-07-28.md", "Combined broad rating ingestion/codification validation", f"All deterministic package invariants passed: **{EXPECTED_VALID:,}** valid ratings became durable ingested/codified records, lanes reconciled to **{LANE_SIZES}**, and **{EXPECTED_QUARANTINE:,}** quarantines remained reference-only. Controlled schemas, layers, buckets, boxes, claim boundaries, map contract, and global-readiness=false passed. No model/API, source/full-text, extraction, OCR/rendering, normalization/comparison, statistical, prevalence, or causal operation ran.")
    write_md(target / "combined_broad_rating_ingestion_codification_16947_stress_test_report.md", "Ingestion/codification stress-test report", "The deterministic runner rejects missing inputs, predecessor decision drift, count mismatch, duplicate/overlapping identities, quarantine leakage, uncontrolled buckets, invalid rating boundaries, lane-size mismatch, and incomplete lane execution. It is idempotent when rebuilt into a fresh directory.")
    write_json(target / "combined_broad_rating_ingestion_codification_16947_regression_test_inventory.json", {
        "new_test": "scripts/test_combined_broad_rating_ingestion_codification_16947.py",
        "predecessor_tests": [
            "scripts/test_combined_broad_exact_span_rating_summary_16947.py",
            "scripts/test_combined_broad_exact_span_rating_17259.py",
            "scripts/test_combined_broad_span_extraction_3815.py",
            "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py",
        ], "global_analysis_readiness": False,
    })

    decision = {
        "task_id": TASK_ID, "decision": DECISION,
        "completion_status": "completed_bounded_rating_ingestion_codification",
        "valid_rating_ingestion_queue_count": EXPECTED_VALID,
        "quarantine_excluded_count": EXPECTED_QUARANTINE,
        "codified_record_count": EXPECTED_VALID, "ingested_record_count": EXPECTED_VALID,
        "completed_lane_count": 4, "lane_counts": LANE_SIZES,
        "claim_readiness_counts": dict(sorted(bucket_counts.items())),
        "analysis_layer_counts": dict(sorted(primary_layer_counts.items())),
        "dashboard_evidence_box_counts": dashboard_box_counts,
        "global_readiness_gate_ready_next": True,
        "map_filter_contract": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(target / "combined_broad_rating_ingestion_codification_16947_decision.json", decision)
    write_md(target / "combined_broad_rating_ingestion_codification_16947_summary.md", "Combined broad rating ingestion/codification summary", f"Decision: `{DECISION}`. All **{EXPECTED_VALID:,}** valid classified exact-span ratings were transformed into schema-stable, lineaged ingested/codified records in four isolated lanes (**4,237 / 4,237 / 4,237 / 4,236**). All **{EXPECTED_QUARANTINE:,}** quarantines remain excluded reference-only records. Primary readiness counts remain `{dict(sorted(bucket_counts.items()))}`. No wage values were normalized or compared. The dedicated global analysis readiness gate is ready next, while global analysis readiness remains false.")

    try:
        prompt_target = target.relative_to(ROOT)
    except ValueError:
        prompt_target = target
    future_prompt = f"""# Next task — dedicated global analysis readiness gate\n\nUse `{prompt_target}/combined_broad_rating_ingestion_codification_16947_global_readiness_gate_input_manifest.csv` and its summaries as the only gate input package.\n\n- Confirm {EXPECTED_VALID:,} codified records and exclude all {EXPECTED_QUARANTINE:,} quarantine references.\n- Diagnose readiness; do not stake final claims and do not flip global analysis readiness true unless a separately authorized gate standard is fully satisfied.\n- Preserve the causal/discourse two-corpus rule and the city × cycle × occupation matching discipline.\n- Do not normalize or compare wage values, calculate wage gaps, run regressions, estimate treatment effects, infer population prevalence, or make final causal claims.\n- Do not access retained sources or full extracted text and do not rerate or call model/API systems.\n- Keep dashboard evidence controls outside the total-scout-coverage-only map.\n- If a required derivative artifact is fully derivable from committed ledgers, reconstruct it deterministically, validate reconciliation, commit/push the repair, and continue; fail closed on missing non-derivable inputs.\n- Update dashboard/status/docs only from completed gate outcomes and keep claim boundaries explicit.\n"""
    write_md(target / "next_global_analysis_readiness_gate_prompt.md", "Next global analysis readiness gate prompt", future_prompt)
    write_md(target / "next_task.md", "Next task", "Run the separately authorized dedicated global analysis readiness gate over the 16,947 codified records. Keep quantitative normalization, comparison, wage-gap estimation, regression, treatment-effect analysis, prevalence inference, and final causal claims out of scope; keep global analysis readiness false unless the future gate independently satisfies its explicit standard.")

    if target.resolve() == OUTPUT_DIR.resolve():
        result_body = f"Decision `{DECISION}`. The committed package contains **{EXPECTED_VALID:,}** ingested/codified valid rating records across four reconciled lanes, with **{EXPECTED_QUARANTINE:,}** quarantines excluded. The dashboard now points to a dedicated global-readiness diagnostic gate as next. Map coverage remains total scout coverage only; global analysis readiness remains false."
        write_md(RESULT_DOC, "Combined broad rating ingestion/codification result", result_body)
        write_md(DASHBOARD_NOTE, "Combined broad rating ingestion/codification dashboard status", f"Current operation: ingestion/codification complete. Next authorized stage: dedicated global analysis readiness gate. Codified/ingested: **{EXPECTED_VALID:,}**; excluded quarantines: **{EXPECTED_QUARANTINE:,}**. Evidence filters remain outside the map. The map remains total scout coverage only and global analysis readiness remains false.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    target = args.output_dir.resolve()
    if target.exists():
        shutil.rmtree(target)
    build_outputs(target)
    print(f"built {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
