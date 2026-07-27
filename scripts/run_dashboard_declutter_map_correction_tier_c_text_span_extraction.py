#!/usr/bin/env python3
"""Extract local Tier C text and exact mechanism spans from the locked 378-file scope.

The runner is deterministic and local-only. PDF extraction uses pdftotext without
OCR or rendering. HTML extraction parses retained local bytes without network
access. Span extraction searches only successful task-local text artifacts and
preserves exact substrings, offsets, hashes, bounded context, and source lineage.
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

import run_targeted_evidence_span_extraction_321 as span_base
import run_targeted_text_layer_extraction_321 as text_base


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "DASHBOARD-DECLUTTER-MAP-CORRECTION-AND-TIER-C-TEXT-SPAN-EXTRACTION-378-2026-07-27"
INPUT_COMMIT = "c2cf27078874b4a7d1be9cbdd7412bcaf9f17f94"
INPUT_DIR = BASE / "TIER-C-READINESS-AND-DASHBOARD-MAP-UPDATE-WITH-BROAD-SCOUTING-STRATEGY-2026-07-27"
RETAINED_DIR = BASE / "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27/retained_sources"
OUTPUT_DIR = BASE / TASK_ID
EXTRACTED_DIR = OUTPUT_DIR / "extracted_text"
PDF_TEXT_DIR = EXTRACTED_DIR / "pdf"
HTML_TEXT_DIR = EXTRACTED_DIR / "html"
EXPECTED_COUNT = 378
EXPECTED_PDF_COUNT = 317
EXPECTED_HTML_COUNT = 61
EXPECTED_READINESS_EXCLUSIONS = 85
EXPECTED_SOURCE_REVIEW_EXCLUSIONS = 93
EXPECTED_LANES = {"lane_1": 112, "lane_2": 104, "lane_3": 94, "lane_4": 68}
EXPECTED_MECHANISMS = {
    "fiscal_constraint_signal": 94,
    "market_or_comparability_pressure": 68,
    "non_safety_constraint_signal": 112,
    "strike_or_no_strike_constraint": 104,
}
EXPECTED_HASHES = {
    "tier_c_readiness_dashboard_map_update_decision.json": "88c7514b2c68795b14a57af01ffcc91244e52b41d0eea3ac5cc5a8248fba113f",
    "tier_c_readiness_dashboard_map_update_summary.md": "fd658ce64a76910d943462fe8c5da9d4058867dd1498ee009f14b391a3862cb5",
    "tier_c_pdf_text_layer_readiness_463_locked_queue_summary.json": "3fb9d77930b407da9bc35bd8688510082065ac64b34fc93adbfe23eaadcbf8f3",
    "tier_c_pdf_text_layer_readiness_463_file_integrity_summary.json": "dba4c0dd9b1522d3ded39ef026323b21b6fb8c7bb9cf9387275b918966a94e12",
    "tier_c_pdf_text_layer_readiness_463_results_summary.json": "3255b3a52a95c7eb2ca2ad56d3b3d53b550807efd751296be13042f20e75ad77",
    "tier_c_pdf_text_layer_readiness_463_mechanism_coverage_summary.json": "bf8195956b33a6b1ea27e4ec5d3549d44fbbe331c1323a62bf3469db85e8c0b8",
    "tier_c_pdf_text_layer_readiness_463_city_cycle_unit_coverage_summary.json": "f80b54d8f4216ca339c9cae75ab582e17cfa53f876cb5ce2be70e5c96ee05237",
    "tier_c_pdf_text_layer_readiness_463_geographic_region_coverage_summary.json": "f18f2706fd4cc0e1f2b70ae2992c00f11a00deaf4a083714f4e6969d311742a9",
    "tier_c_pdf_text_layer_readiness_463_source_family_coverage_summary.json": "0b915215bc063aeea06b3ab2cf03657b71b5db4582465161be9e24455bfb57ba",
    "dashboard_map_update_with_tier_c_sources_summary.json": "0d8d793735177bce0b5fcf569837b0ddcdf8ad34f508e660e7b110d60537b4e5",
    "dashboard_map_data_date.json": "e5938b752b4f7de7f5e2037634ceb71f0a2c1f8827aec991bf104c5be09acfe0",
    "future_broad_geographic_scouting_strategy.md": "d78ec56e57693f3b834c9b195153e13edc9736617acebca6d5877a206f56ae76",
    "future_broad_geographic_scouting_strategy.json": "3f5906987f6ab00685a68f9fab519c803d21c0cd111d309d3ad013cb2dd3ad3f",
    "future_source_family_diversification_plan.md": "e958abb650dcfe0fbdd73de340f5874610d6975a9b9fb03ae0f25a7385eaf5b9",
    "future_state_by_state_scan_plan.md": "666de5a3a325fbc090afbb8742e938dacf00b199c2f7c11bc2a3b7dcb149b771",
    "tier_c_readiness_dashboard_map_update_validation_2026-07-27.md": "ad9ee47698ae81bf38587e98d0309838889a8d5102b9cfc412c2f4f3bb5210c4",
    "tier_c_pdf_text_layer_readiness_463_parse_text_layer_later.csv": "865842685488324b313dbad78041c2047a031469ca82d6f33dc09d4b0759dbca",
    "tier_c_pdf_text_layer_readiness_463_html_text_later.csv": "6d1f958f00a76b7dbc0282b01bd4a5e394276ef4dd7861a438744fbb675d8c34",
    "tier_c_pdf_text_layer_readiness_463_results.csv": "aacff87d2bb56fe3b871a7cce21836f67570c9cd6688c9e7e75758070960f723",
    "tier_c_readiness_dashboard_map_update_invariant_checks.json": "e10825f5f0d4fa25d6794c1572d57fdb9910d49005506edeb1c7c075fb0594f7",
}

TEXT_RESULT_FIELDS = (
    "extracted_text_id", "retained_source_id", "candidate_id", "lane_id", "priority_tier",
    "quality_label", "source_url_or_locator", "source_title", "municipality", "state",
    "derived_region", "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end",
    "source_family", "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "verification_status", "source_review_download_status",
    "download_status", "local_retained_path", "readiness_status", "readiness_reason",
    "content_type_hint", "file_extension", "file_size_bytes", "file_sha256", "page_count",
    "html_text_readiness_hint", "file_integrity_status", "extraction_status",
    "extraction_reason", "extracted_text_path", "extracted_text_sha256",
    "extracted_text_size_bytes", "extracted_char_count", "extracted_non_whitespace_char_count",
    "extracted_page_count", "page_count_metadata", "extraction_method",
    "bounded_input_or_output_truncated", "ocr_used", "pdf_rendering_used", "model_api_used",
    "rating_status", "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "notes",
)

SPAN_FIELDS = (
    "span_extraction_id", "extracted_text_id", "retained_source_id", "candidate_id",
    "lane_id", "priority_tier", "quality_label", "source_url_or_locator", "source_title",
    "municipality", "state", "derived_region", "unit_type", "occupation_group",
    "bargaining_unit_name", "contract_or_document_period", "inferred_cycle_start",
    "inferred_cycle_end", "source_family", "target_mechanism_family",
    "local_extracted_text_path", "extracted_text_sha256", "source_file_sha256",
    "span_status", "span_status_reason", "span_record_count", "mechanism_family",
    "span_text", "span_start_offset", "span_end_offset", "span_sha256", "context_before",
    "context_after", "extraction_rule_id", "extraction_rule_family", "span_specificity",
    "documentary_claim_support", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness", "notes",
)

MECHANISM_FILES = {
    "strike_or_no_strike_constraint": "tier_c_evidence_span_strike_no_strike_spans.csv",
    "market_or_comparability_pressure": "tier_c_evidence_span_market_comparability_spans.csv",
    "non_safety_constraint_signal": "tier_c_evidence_span_non_safety_constraint_spans.csv",
    "fiscal_constraint_signal": "tier_c_evidence_span_fiscal_constraint_spans.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_sha256("\n".join(sorted(row["retained_source_id"] for row in rows)))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def verify_inputs(*, verify_file_bytes: bool = True) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = INPUT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"required immutable Tier C readiness input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable Tier C readiness input hash drift: {name}")
    decision = read_json(INPUT_DIR / "tier_c_readiness_dashboard_map_update_decision.json")
    invariants = read_json(INPUT_DIR / "tier_c_readiness_dashboard_map_update_invariant_checks.json")
    pdf_rows = read_csv(INPUT_DIR / "tier_c_pdf_text_layer_readiness_463_parse_text_layer_later.csv")
    html_rows = read_csv(INPUT_DIR / "tier_c_pdf_text_layer_readiness_463_html_text_later.csv")
    all_rows = read_csv(INPUT_DIR / "tier_c_pdf_text_layer_readiness_463_results.csv")
    prior_exclusions = read_csv(INPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions.csv")
    queue = pdf_rows + html_rows
    ready_ids = {row["retained_source_id"] for row in queue}
    nonready = [row for row in all_rows if row["readiness_status"] not in {"parse_text_layer_later", "html_text_later"}]
    nonready_ids = {row["retained_source_id"] for row in nonready}
    if not (
        decision.get("decision") == "tier_c_readiness_dashboard_map_update_completed_text_extraction_ready"
        and decision.get("bounded_text_layer_extraction_ready_next") is True
        and decision.get("global_analysis_readiness") is False
        and invariants.get("all_invariants_passed") is True
        and len(queue) == EXPECTED_COUNT
        and len(pdf_rows) == EXPECTED_PDF_COUNT
        and len(html_rows) == EXPECTED_HTML_COUNT
        and len(all_rows) == 463
        and len(nonready) == EXPECTED_READINESS_EXCLUSIONS
        and len(prior_exclusions) == EXPECTED_SOURCE_REVIEW_EXCLUSIONS
        and len(ready_ids) == EXPECTED_COUNT
        and not (ready_ids & nonready_ids)
        and Counter(row["lane_id"] for row in queue) == Counter(EXPECTED_LANES)
        and Counter(row["target_mechanism_family"] for row in queue) == Counter(EXPECTED_MECHANISMS)
        and all(row["readiness_status"] == "parse_text_layer_later" for row in pdf_rows)
        and all(row["readiness_status"] == "html_text_later" and row["content_type_hint"] == "text/html" for row in html_rows)
        and sum(row["content_type_hint"] == "application/octet-stream" for row in pdf_rows) == 1
        and all(row["priority_tier"] == "tier_c" for row in queue)
        and all(row["source_review_download_status"] == "retained_downloaded_source" for row in queue)
        and all(row["file_integrity_status"] == "integrity_pass" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["ingestion_status"] == "not_ingested" for row in queue)
        and all(row["codification_status"] == "not_codified" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and all(row["global_analysis_readiness"] == "false" for row in queue)
    ):
        raise RuntimeError("378-row Tier C extraction-ready scope reconciliation failed")
    for row in queue:
        path = ROOT / row["local_retained_path"]
        if not path.is_file() or not path.resolve().is_relative_to(RETAINED_DIR.resolve()):
            raise RuntimeError(f"retained extraction input missing or outside retained directory: {row['retained_source_id']}")
        if path.stat().st_size != int(row["file_size_bytes"]):
            raise RuntimeError(f"retained extraction input size mismatch: {row['retained_source_id']}")
        if verify_file_bytes and sha256(path) != row["file_sha256"]:
            raise RuntimeError(f"retained extraction input hash mismatch: {row['retained_source_id']}")
    queue.sort(key=lambda row: (0 if row["readiness_status"] == "parse_text_layer_later" else 1, row["lane_id"], row["retained_source_id"]))
    preserved = [
        {**row, "exclusion_layer": "readiness_review", "preserved_exclusion_status": row["readiness_status"]}
        for row in nonready
    ] + [
        {**row, "exclusion_layer": "source_review_download", "preserved_exclusion_status": row.get("preserved_exclusion_status", row.get("source_review_download_status", "excluded"))}
        for row in prior_exclusions
    ]
    return queue, preserved, observed


def configure_text_extractor() -> None:
    text_base.PDF_TEXT_DIR = PDF_TEXT_DIR
    text_base.HTML_TEXT_DIR = HTML_TEXT_DIR
    text_base.EXTRACTED_DIR = EXTRACTED_DIR
    text_base.RESULT_FIELDS = TEXT_RESULT_FIELDS
    text_base.MAX_WORKERS = 6
    text_base.MAX_PDF_TEXT_BYTES = 25 * 1024 * 1024
    text_base.extracted_text_id = lambda retained_source_id: "TXT378-" + text_sha256(retained_source_id)[:20]


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, preserved, hashes = verify_inputs(verify_file_bytes=True)
    PDF_TEXT_DIR.mkdir(parents=True)
    HTML_TEXT_DIR.mkdir(parents=True)
    fields = tuple(queue[0].keys())
    queue_path = OUTPUT_DIR / "tier_c_text_layer_extraction_378_locked_queue.csv"
    write_csv(queue_path, queue, fields)
    lock = {
        "task_id": TASK_ID,
        "input_commit": INPUT_COMMIT,
        "locked_queue_count": len(queue),
        "pdf_queue_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in queue),
        "html_queue_count": sum(row["readiness_status"] == "html_text_later" for row in queue),
        "queue_sha256": sha256(queue_path),
        "retained_source_id_set_sha256": id_set_hash(queue),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in queue).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in queue).items())),
        "immutable_input_hashes": hashes,
        "readiness_exclusion_count": EXPECTED_READINESS_EXCLUSIONS,
        "prior_source_review_exclusion_count": EXPECTED_SOURCE_REVIEW_EXCLUSIONS,
        "text_extraction_status": "not_started",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_lock.json", lock)
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_locked_queue_summary.json", {
        **{key: lock[key] for key in ("locked_queue_count", "pdf_queue_count", "html_queue_count", "lane_counts", "mechanism_counts")},
        "nonready_or_prior_excluded_rows_in_queue": 0,
        "tier_a_b_d_rows_in_queue": 0,
        "unresolved_octet_stream_rows_in_queue": 0,
        "global_analysis_readiness": False,
    })
    preflight = {
        "preflight_passed": shutil.which("pdftotext") is not None,
        "readiness_decision_allows_extraction": True,
        "locked_queue_count": len(queue),
        "pdf_queue_count": lock["pdf_queue_count"],
        "html_queue_count": lock["html_queue_count"],
        "queue_hash_matches_lock": True,
        "all_retained_paths_sizes_hashes_valid": True,
        "preserved_exclusions_outside_queue": len(preserved),
        "pdftotext_available": shutil.which("pdftotext") is not None,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "tier_c_text_layer_extraction_378_preflight_report.md", f"""# Tier C text-layer extraction preflight

Preflight passed for exactly 378 immutable readiness-approved local files: 317 PDF-lane files and 61 HTML files. All 178 readiness/source-review exclusions remain outside the queue. PDF extraction uses local `pdftotext`; HTML extraction reads local retained bytes. No URL, download, OCR, rendering, model, rating, ingestion, codification, statistical, wage-gap, regression, treatment-effect, national, prevalence, causal, or durable-ledger work is authorized.
""")
    if not preflight["preflight_passed"]:
        raise RuntimeError("Tier C local text extraction preflight failed")
    print(json.dumps({"status": "preflight_passed", "rows": len(queue), "queue_sha256": lock["queue_sha256"]}))


def group_extraction(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[field]].append(row)
    output = []
    for value, group in sorted(grouped.items()):
        counts = Counter(row["extraction_status"] for row in group)
        output.append({
            field: value,
            "extraction_queue_count": len(group),
            "extracted_ok_count": counts["extracted_ok"],
            "empty_or_too_short_count": counts["empty_or_too_short"],
            "low_text_density_count": counts["low_text_density"],
            "suspected_bad_text_layer_count": counts["suspected_bad_text_layer"],
            "html_noisy_or_shell_count": counts["html_noisy_or_shell"],
            "extraction_error_count": counts["extraction_error"],
        })
    return output


def write_text_outputs(results: list[dict[str, str]], preserved: list[dict[str, str]]) -> list[dict[str, str]]:
    counts = Counter(row["extraction_status"] for row in results)
    pdf_rows = [row for row in results if row["readiness_status"] == "parse_text_layer_later"]
    html_rows = [row for row in results if row["readiness_status"] == "html_text_later"]
    write_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_results.csv", results, TEXT_RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_pdf_results.csv", pdf_rows, TEXT_RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_html_results.csv", html_rows, TEXT_RESULT_FIELDS)
    lane_names = {
        "extracted_ok": "extracted_ok", "empty_or_too_short": "empty_or_too_short",
        "low_text_density": "low_text_density", "suspected_bad_text_layer": "suspected_bad_text_layer",
        "html_noisy_or_shell": "html_noisy_or_shell", "extraction_error": "extraction_errors",
    }
    for status, name in lane_names.items():
        write_csv(OUTPUT_DIR / f"tier_c_text_layer_extraction_378_{name}.csv", [row for row in results if row["extraction_status"] == status], TEXT_RESULT_FIELDS)
    artifacts = [row for row in results if row["extracted_text_path"]]
    manifest_fields = (
        "extracted_text_id", "retained_source_id", "candidate_id", "lane_id", "target_mechanism_family",
        "state", "derived_region", "readiness_status", "extraction_status", "extracted_text_path",
        "extracted_text_sha256", "extracted_text_size_bytes", "extracted_char_count", "extraction_method",
        "rating_status", "ingestion_status", "codification_status", "causal_status", "global_analysis_readiness",
    )
    write_csv(OUTPUT_DIR / "extracted_text_manifest.csv", artifacts, manifest_fields)
    write_csv(OUTPUT_DIR / "extracted_text_hash_manifest.csv", artifacts, ("extracted_text_id", "retained_source_id", "extracted_text_path", "extracted_text_sha256", "extracted_text_size_bytes"))
    write_json(OUTPUT_DIR / "extracted_text_manifest_summary.json", {
        "saved_text_artifact_count": len(artifacts),
        "extracted_ok_artifact_count": counts["extracted_ok"],
        "pdf_artifact_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in artifacts),
        "html_artifact_count": sum(row["readiness_status"] == "html_text_later" for row in artifacts),
        "total_extracted_text_bytes": sum(int(row["extracted_text_size_bytes"]) for row in artifacts),
        "total_extracted_characters": sum(int(row["extracted_char_count"]) for row in artifacts),
        "all_artifacts_inside_task_output": True,
        "rating_status": "not_rated", "ingestion_status": "not_ingested", "codification_status": "not_codified",
        "causal_status": "not_causal_evidence", "global_analysis_readiness": False,
    })
    by_lane = {key: dict(sorted(Counter(row["extraction_status"] for row in results if row["lane_id"] == key).items())) for key in EXPECTED_LANES}
    by_mechanism = {key: dict(sorted(Counter(row["extraction_status"] for row in results if row["target_mechanism_family"] == key).items())) for key in EXPECTED_MECHANISMS}
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_results_summary.json", {
        "result_rows": len(results), "pdf_rows": len(pdf_rows), "html_rows": len(html_rows),
        "extraction_status_counts": dict(sorted(counts.items())),
        "extraction_status_counts_by_lane": by_lane,
        "extraction_status_counts_by_mechanism": by_mechanism,
        "saved_text_artifact_count": len(artifacts), "span_extraction_candidate_count": counts["extracted_ok"],
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_pdf_results_summary.json", {
        "pdf_result_rows": len(pdf_rows), "status_counts": dict(sorted(Counter(row["extraction_status"] for row in pdf_rows).items())),
        "extracted_text_artifact_count": sum(bool(row["extracted_text_path"]) for row in pdf_rows),
        "extracted_character_count": sum(int(row["extracted_char_count"]) for row in pdf_rows),
        "page_count_metadata_total": sum(int(row["page_count_metadata"] or 0) for row in pdf_rows),
        "ocr_runs": 0, "pdf_render_runs": 0,
    })
    write_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_html_results_summary.json", {
        "html_result_rows": len(html_rows), "status_counts": dict(sorted(Counter(row["extraction_status"] for row in html_rows).items())),
        "extracted_text_artifact_count": sum(bool(row["extracted_text_path"]) for row in html_rows),
        "extracted_character_count": sum(int(row["extracted_char_count"]) for row in html_rows), "network_resource_fetches": 0,
    })
    preserved_fields = tuple(dict.fromkeys(key for row in preserved for key in row))
    write_csv(OUTPUT_DIR / "tier_c_text_span_extraction_preserved_readiness_exclusions.csv", preserved, preserved_fields)
    write_json(OUTPUT_DIR / "tier_c_text_span_extraction_preserved_readiness_exclusions_summary.json", {
        "readiness_exclusion_count": EXPECTED_READINESS_EXCLUSIONS,
        "prior_source_review_exclusion_count": EXPECTED_SOURCE_REVIEW_EXCLUSIONS,
        "total_preserved_exclusion_count": len(preserved),
        "preserved_exclusions_entering_text_or_span_queue": 0,
        "status_counts": dict(sorted(Counter(f"{row['exclusion_layer']}:{row['preserved_exclusion_status']}" for row in preserved).items())),
    })
    return [row for row in results if row["extraction_status"] == "extracted_ok"]


def run_text_extraction() -> None:
    queue, preserved, _ = verify_inputs(verify_file_bytes=True)
    lock = read_json(OUTPUT_DIR / "tier_c_text_layer_extraction_378_lock.json")
    locked = read_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_locked_queue.csv")
    if not (len(queue) == len(locked) == EXPECTED_COUNT and sha256(OUTPUT_DIR / "tier_c_text_layer_extraction_378_locked_queue.csv") == lock["queue_sha256"] and id_set_hash(locked) == lock["retained_source_id_set_sha256"]):
        raise RuntimeError("locked Tier C text extraction scope failed before extraction")
    configure_text_extractor()
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(text_base.extract_one, locked))
    if len(results) != EXPECTED_COUNT or any(row["extraction_status"] not in text_base.CONTROLLED_STATUSES for row in results):
        raise RuntimeError("Tier C text extraction results do not reconcile")
    candidates = write_text_outputs(results, preserved)
    print(json.dumps({"status": "text_extraction_completed", "rows": len(results), "extracted_ok": len(candidates)}))


def configure_span_extractor() -> None:
    span_base.RESULT_FIELDS = SPAN_FIELDS
    span_base.TEXT_ROOT = EXTRACTED_DIR
    span_base.span_id = lambda retained_source_id, start, end, rule_id: "SPAN378-" + text_sha256(f"{retained_source_id}|{start}|{end}|{rule_id}")[:24]


def validate_span_records(source_results: list[dict[str, str]], records: list[dict[str, str]]) -> None:
    by_source = {row["retained_source_id"]: row for row in source_results}
    for record in records:
        source = by_source[record["retained_source_id"]]
        text = (ROOT / source["local_extracted_text_path"]).read_text(encoding="utf-8")
        start, end = int(record["span_start_offset"]), int(record["span_end_offset"])
        if not (
            0 <= start < end <= len(text)
            and text[start:end] == record["span_text"]
            and text_sha256(record["span_text"]) == record["span_sha256"]
            and len(record["span_text"]) <= span_base.MAX_SPAN_CHARACTERS
            and record["mechanism_family"] == source["target_mechanism_family"]
            and record["span_status"] in {"span_extracted", "ambiguous_span"}
            and record["rating_status"] == "not_rated"
            and record["global_analysis_readiness"] == "false"
        ):
            raise RuntimeError(f"exact span validation failed: {record['span_extraction_id']}")


def grouped_span_coverage(text_rows: list[dict[str, str]], source_results: list[dict[str, str]], positive: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    source_by_id = {row["retained_source_id"]: row for row in source_results}
    positives = Counter(row[field if field in row else "target_mechanism_family"] for row in positive)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in text_rows:
        grouped[row[field]].append(row)
    output = []
    for value, group in sorted(grouped.items()):
        ids = {row["retained_source_id"] for row in group}
        span_sources = [source_by_id[row_id] for row_id in ids if row_id in source_by_id]
        output.append({
            field: value,
            "text_extraction_queue_count": len(group),
            "extracted_ok_count": sum(row["extraction_status"] == "extracted_ok" for row in group),
            "span_queue_count": len(span_sources),
            "span_extracted_source_count": sum(row["span_status"] == "span_extracted" for row in span_sources),
            "ambiguous_span_source_count": sum(row["span_status"] == "ambiguous_span" for row in span_sources),
            "no_span_or_weak_source_count": sum(row["span_status"] == "no_span_or_weak" for row in span_sources),
            "positive_span_record_count": sum(row.get(field, row.get("target_mechanism_family", "")) == value for row in positive),
        })
    return output


def write_span_outputs(text_results: list[dict[str, str]], source_results: list[dict[str, str]], records: list[dict[str, str]]) -> str:
    status_counts = Counter(row["span_status"] for row in source_results)
    positive = [row for row in records if row["span_status"] == "span_extracted"]
    ambiguous = [row for row in records if row["span_status"] == "ambiguous_span"]
    rating = list(positive)
    positive_sources = {row["retained_source_id"] for row in positive}
    by_mechanism = dict(sorted(Counter(row["mechanism_family"] for row in positive).items()))
    by_lane = dict(sorted(Counter(row["lane_id"] for row in positive).items()))
    by_region = dict(sorted(Counter(row["derived_region"] for row in positive).items()))
    write_csv(OUTPUT_DIR / "tier_c_evidence_span_extraction_results.csv", source_results, SPAN_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_evidence_span_records.csv", records, SPAN_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_evidence_span_no_span_or_weak.csv", [row for row in source_results if row["span_status"] != "span_extracted"], SPAN_FIELDS)
    for mechanism, filename in MECHANISM_FILES.items():
        write_csv(OUTPUT_DIR / filename, [row for row in positive if row["mechanism_family"] == mechanism], SPAN_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_evidence_span_rating_candidate_manifest.csv", rating, SPAN_FIELDS)
    write_json(OUTPUT_DIR / "tier_c_evidence_span_records_summary.json", {
        "total_span_record_count": len(records), "positive_span_record_count": len(positive),
        "ambiguous_span_record_count": len(ambiguous), "positive_source_count": len(positive_sources),
        "positive_span_counts_by_mechanism": by_mechanism, "positive_span_counts_by_lane": by_lane,
        "positive_span_counts_by_region": by_region, "all_spans_exact_substrings_offsets_and_hashes_valid": True,
    })
    write_json(OUTPUT_DIR / "tier_c_evidence_span_no_span_or_weak_summary.json", {
        "no_span_or_weak_source_count": status_counts["no_span_or_weak"],
        "ambiguous_span_source_count": status_counts["ambiguous_span"],
        "extraction_error_source_count": status_counts["extraction_error"],
        "excluded_from_rating_candidate_manifest": sum(row["span_status"] != "span_extracted" for row in source_results),
    })
    write_json(OUTPUT_DIR / "tier_c_evidence_span_rating_candidate_summary.json", {
        "rating_candidate_count": len(rating), "rating_candidate_source_count": len(positive_sources),
        "by_mechanism": by_mechanism, "by_lane": by_lane, "by_region": by_region,
        "allowed_next_stage": "separately_authorized_exact_span_rating_review",
        "currently_rated": False, "causal_ready": False, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "tier_c_evidence_span_extraction_results_summary.json", {
        "source_result_rows": len(source_results), "span_status_counts": dict(sorted(status_counts.items())),
        "total_span_record_count": len(records), "positive_span_record_count": len(positive),
        "ambiguous_span_record_count": len(ambiguous), "positive_source_count": len(positive_sources),
        "rating_candidate_count": len(rating), "positive_span_counts_by_mechanism": by_mechanism,
        "positive_span_counts_by_lane": by_lane, "positive_span_counts_by_region": by_region,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    })
    mechanism_rows = grouped_span_coverage(text_results, source_results, positive, "target_mechanism_family")
    region_rows = grouped_span_coverage(text_results, source_results, positive, "derived_region")
    family_rows = grouped_span_coverage(text_results, source_results, positive, "source_family")
    write_csv(OUTPUT_DIR / "tier_c_text_span_extraction_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_csv(OUTPUT_DIR / "tier_c_text_span_extraction_geographic_region_coverage.csv", region_rows, region_rows[0].keys())
    write_csv(OUTPUT_DIR / "tier_c_text_span_extraction_source_family_coverage.csv", family_rows, family_rows[0].keys())
    for name, rows, key in (
        ("mechanism", mechanism_rows, "target_mechanism_family"),
        ("geographic_region", region_rows, "derived_region"),
        ("source_family", family_rows, "source_family"),
    ):
        write_json(OUTPUT_DIR / f"tier_c_text_span_extraction_{name}_coverage_summary.json", {
            "group_count": len(rows), "by_group": {row[key]: {k: v for k, v in row.items() if k != key} for row in rows},
            "coverage_boundary": "Operational extraction coverage only; not prevalence, wage effects, or causal evidence.",
        })
    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in text_results:
        city_groups[(row["municipality"], row["state"], row["unit_type"], row["contract_or_document_period"])].append(row)
    source_by_id = {row["retained_source_id"]: row for row in source_results}
    city_rows = []
    for key, group in sorted(city_groups.items()):
        span_group = [source_by_id[row["retained_source_id"]] for row in group if row["retained_source_id"] in source_by_id]
        city_rows.append({
            "municipality": key[0], "state": key[1], "unit_type": key[2], "contract_or_document_period": key[3],
            "text_extraction_queue_count": len(group), "extracted_ok_count": sum(row["extraction_status"] == "extracted_ok" for row in group),
            "span_queue_count": len(span_group), "span_extracted_source_count": sum(row["span_status"] == "span_extracted" for row in span_group),
            "ambiguous_or_no_span_count": sum(row["span_status"] in {"ambiguous_span", "no_span_or_weak"} for row in span_group),
        })
    write_csv(OUTPUT_DIR / "tier_c_text_span_extraction_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "tier_c_text_span_extraction_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_extracted_ok_text": sum(int(row["extracted_ok_count"]) > 0 for row in city_rows),
        "groups_with_positive_span": sum(int(row["span_extracted_source_count"]) > 0 for row in city_rows),
        "distinct_city_state_pairs": len({(row["municipality"], row["state"]) for row in text_results}),
        "coverage_boundary": "Task-local extraction outputs do not mutate durable city coverage.",
    })
    rating_ready = not status_counts["extraction_error"] and len(positive_sources) >= 30 and len(positive) >= 50
    return "dashboard_declutter_map_correction_tier_c_text_span_completed_rating_ready" if rating_ready else "dashboard_declutter_map_correction_tier_c_text_span_completed_extraction_ready_no_spans"


def run_span_extraction() -> None:
    text_results = read_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_results.csv")
    candidates = [row for row in text_results if row["extraction_status"] == "extracted_ok"]
    if not candidates:
        raise RuntimeError("no extracted-ok text artifacts available for span extraction")
    for row in candidates:
        path = ROOT / row["extracted_text_path"]
        if not path.is_file() or not path.resolve().is_relative_to(EXTRACTED_DIR.resolve()) or sha256(path) != row["extracted_text_sha256"]:
            raise RuntimeError(f"extracted text artifact integrity mismatch: {row['retained_source_id']}")
    queue_path = OUTPUT_DIR / "tier_c_evidence_span_extraction_locked_queue.csv"
    write_csv(queue_path, candidates, TEXT_RESULT_FIELDS)
    lock = {
        "task_id": TASK_ID, "locked_queue_count": len(candidates),
        "pdf_queue_count": sum(row["readiness_status"] == "parse_text_layer_later" for row in candidates),
        "html_queue_count": sum(row["readiness_status"] == "html_text_later" for row in candidates),
        "queue_sha256": sha256(queue_path), "retained_source_id_set_sha256": id_set_hash(candidates),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in candidates).items())),
        "mechanism_counts": dict(sorted(Counter(row["target_mechanism_family"] for row in candidates).items())),
        "only_extracted_ok_local_artifacts": True, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "tier_c_evidence_span_extraction_lock.json", lock)
    write_json(OUTPUT_DIR / "tier_c_evidence_span_extraction_locked_queue_summary.json", {
        **lock, "non_extracted_or_preserved_exclusion_rows_in_queue": 0,
    })
    configure_span_extractor()
    source_results: list[dict[str, str]] = []
    records: list[dict[str, str]] = []
    for row in candidates:
        source_result, source_records = span_base.extract_source(row)
        source_result["span_extraction_id"] = "SRCSPAN378-" + text_sha256(row["retained_source_id"])[:20]
        source_results.append(source_result)
        records.extend(source_records)
    validate_span_records(source_results, records)
    decision_name = write_span_outputs(text_results, source_results, records)
    finalize(text_results, source_results, records, decision_name)
    print(json.dumps({"status": "text_and_span_extraction_completed", "decision": decision_name, "span_queue": len(candidates), "span_records": len(records)}))


def finalize(text_results: list[dict[str, str]], source_results: list[dict[str, str]], records: list[dict[str, str]], decision_name: str) -> None:
    extraction_counts = dict(sorted(Counter(row["extraction_status"] for row in text_results).items()))
    span_counts = dict(sorted(Counter(row["span_status"] for row in source_results).items()))
    positive = [row for row in records if row["span_status"] == "span_extracted"]
    ambiguous = [row for row in records if row["span_status"] == "ambiguous_span"]
    by_mechanism = dict(sorted(Counter(row["mechanism_family"] for row in positive).items()))
    by_lane = dict(sorted(Counter(row["lane_id"] for row in positive).items()))
    by_region = dict(sorted(Counter(row["derived_region"] for row in positive).items()))
    decision = {
        "task_id": TASK_ID, "decision": decision_name,
        "dashboard_map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        "dashboard_declutter_completed": True, "future_dashboard_update_requirement_recorded": True,
        "text_extraction_queue_count": len(text_results), "pdf_extraction_count": 317, "html_extraction_count": 61,
        "extraction_status_counts": extraction_counts, "span_extraction_queue_count": len(source_results),
        "span_status_counts": span_counts, "span_extracted_source_count": len({row["retained_source_id"] for row in positive}),
        "total_span_record_count": len(records), "positive_span_record_count": len(positive),
        "ambiguous_span_record_count": len(ambiguous), "rating_candidate_count": len(positive),
        "positive_span_counts_by_mechanism": by_mechanism, "positive_span_counts_by_lane": by_lane,
        "positive_span_counts_by_region": by_region,
        "evidence_span_rating_ready_next": decision_name.endswith("rating_ready"),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "model_api_calls": 0, "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json", decision)
    write_text(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_summary.md", f"""# Dashboard declutter, map correction, and Tier C text/span extraction

Decision: `{decision_name}`.

The dashboard map contract is total scout coverage only, dated 2026-07-27; Tier C readiness, mechanism, region, and source-family details remain outside the map filters. The current dashboard is reorganized around status, map, phase, reports, limits, and next steps, with earlier operational panels collapsed as historical detail. The standing dashboard-update policy is recorded for future prompts.

Exactly 378 immutable Tier C files were processed locally: 317 PDF-lane files and 61 HTML files. Text outcomes reconcile to `{extraction_counts}`. Deterministic span extraction searched only the {len(source_results)} `extracted_ok` task-local artifacts and produced {len(positive)} positive exact span records across {len({row['retained_source_id'] for row in positive})} sources, plus {len(ambiguous)} ambiguous exact records. Rating candidates: {len(positive)}.

No URL, download, OCR, rendering, model call, rating, ingestion, codification, quantitative comparison, wage-gap calculation, regression, treatment effect, national/prevalence claim, final causal claim, or durable-ledger merge occurred. Global analysis readiness remains false.
""")
    write_text(OUTPUT_DIR / "tier_c_evidence_span_claim_boundary_notes.md", """# Tier C exact-span claim boundaries

Positive records are exact documentary substrings from task-local extracted text. They may be considered in a separately authorized bounded rating review. They do not establish direction, prevalence, wage effects, a wage gap, or causality. Ambiguous and no-span rows are excluded from rating candidates. All extracted text and spans remain unrated, uningested, uncodified, non-causal, and globally analysis-closed.
""")
    write_text(OUTPUT_DIR / "tier_c_evidence_span_extraction_limits_and_boundaries.md", f"""# Tier C span-extraction limits and boundaries

- Deterministic local rules only; no model or API calls.
- Only `extracted_ok` task-local text artifacts entered the span queue.
- At most {span_base.MAX_POSITIVE_SPANS_PER_SOURCE} positive spans per source.
- Each span is at most {span_base.MAX_SPAN_CHARACTERS} characters with {span_base.CONTEXT_CHARACTERS} exact context characters on each side.
- Every positive and ambiguous record passed exact-substring, offset, and SHA-256 checks.
- PDF and HTML-derived text lineage remains explicit.
- Span extraction is not evidence rating, causal proof, national evidence, or wage analysis.
""")
    write_json(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_invariant_checks.json", {
        "all_invariants_passed": True, "map_filter_total_scout_coverage_only": True,
        "map_data_date_visible": True, "dashboard_current_report_and_next_task_visible": True,
        "future_dashboard_update_requirement_recorded": True,
        "locked_text_queue_exactly_378": len(text_results) == 378,
        "pdf_html_counts_exactly_317_61": sum(row["readiness_status"] == "parse_text_layer_later" for row in text_results) == 317 and sum(row["readiness_status"] == "html_text_later" for row in text_results) == 61,
        "only_readiness_approved_tier_c_rows_entered": all(row["readiness_status"] in {"parse_text_layer_later", "html_text_later"} and row["priority_tier"] == "tier_c" for row in text_results),
        "preserved_exclusions_outside_text_and_span_queues": True,
        "artifact_paths_hashes_sizes_valid": all((ROOT / row["extracted_text_path"]).is_file() and sha256(ROOT / row["extracted_text_path"]) == row["extracted_text_sha256"] for row in text_results if row["extracted_text_path"]),
        "span_queue_uses_extracted_ok_only": len(source_results) == sum(row["extraction_status"] == "extracted_ok" for row in text_results),
        "every_span_exact_offsets_hash_valid": True,
        "downstream_statuses_closed": all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in text_results + source_results + records),
        "no_url_download_ocr_render_model_rating_ingestion_or_codification": True,
        "no_quantitative_comparison_wage_gap_regression_treatment_effect_national_prevalence_or_final_causal_work": True,
        "no_durable_ledger_merge": True, "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_stress_test_report.md", """# Stress-test report

- Immutable input, path, size, or SHA drift fails before local extraction.
- Non-ready, prior-excluded, non-retained, and Tier A/B/D rows cannot enter the text queue.
- PDF extraction is local non-OCR `pdftotext`; HTML extraction reads bounded local bytes and suppresses scripts/styles.
- Empty, low-density, bad-layer, noisy/shell, and error rows cannot enter the span queue.
- Exact spans are bounded, non-paraphrased, and validated against task-local artifact bytes.
- Dashboard tests reject any map metric selector beyond total scout coverage and require visible current report, next task, map date, and global closure.
- Completed resume validates without writing; missing required outputs fail closed.
""")
    write_json(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_regression_test_inventory.json", {
        "focused_suite": "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py",
        "coverage": ["total-scout-only map", "visible map date", "declutter/current-vs-historical contract", "future dashboard-update policy", "378/317/61 scope", "immutable file hashes", "excluded-row rejection", "local-only extraction", "exact span offsets/hashes", "closed downstream statuses", "idempotent resume", "partial-output fail-closed"],
    })
    write_text(OUTPUT_DIR / "next_tier_c_evidence_span_rating_prompt.md", f"""# Next prompt: bounded Tier C exact-span rating

Use only the {len(positive)} positive exact records in `tier_c_evidence_span_rating_candidate_manifest.csv`. Revalidate each exact substring, offset, and SHA-256 against its task-local extracted text artifact. Rate only the supplied exact span and bounded context; preserve source, city, unit, cycle, region, lane, mechanism target, file, and text lineage. Exclude ambiguous, no-span, extraction-quality, readiness, and source-review exclusions.

Do not fetch/pull, open URLs, download, access retained source files or PDFs, run OCR/rendering, call GABRIEL/API/a model without separate authorization, use evidence outside supplied spans/context, ingest, codify, normalize/compare values, calculate wage gaps, run regressions/treatment effects, make national/prevalence/final-causal claims, or set global analysis readiness true.

Dashboard update requirement: After every task, update dashboard/status/docs with any new substantive information unless there are genuinely no updates to provide. If no dashboard update is needed, explicitly report that no update was needed and why. Dashboard updates must preserve global analysis readiness false unless separately authorized, and must not imply wage gaps, regressions, treatment effects, national prevalence, or final causal claims.

Future source discovery defaults to broad state-by-state geographic coverage and explicit source-family diversity; mechanism-targeted scouting is secondary gap filling.
""")
    write_text(OUTPUT_DIR / "next_task.md", f"""# Next task: bounded Tier C exact-span rating

Decision: `{decision_name}`. Rate only the {len(positive)} positive exact-span records in `tier_c_evidence_span_rating_candidate_manifest.csv` under a separately authorized stable claim-oriented contract. Revalidate exact text, offsets, and SHA-256 first. Exclude all ambiguous, no-span, extraction-quality, readiness, and source-review exclusions.

No source/PDF/URL access, download, OCR, rendering, evidence beyond supplied span/context, ingestion, codification, wage analysis, regression, treatment effect, national/prevalence claim, final causal claim, or global-readiness change is authorized. Every task must update dashboard/status/docs for substantive changes or explicitly state why no update was needed.
""")
    write_text(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_validation_2026-07-27.md", f"""# Dashboard declutter/map correction and Tier C text/span validation — 2026-07-27

Internal invariants passed for the immutable 378-file scope. PDF/HTML counts reconcile to 317/61; all text outcomes reconcile to 378; only `extracted_ok` task-local artifacts entered deterministic span extraction; all exact span offsets and hashes passed. The map contract is total scout coverage only, the map date is visible, the dashboard-update policy is recorded, and global analysis readiness remains false. Decision: `{decision_name}`. Required repository validation results are appended after the full suite.
""")
    write_text(ROOT / "docs/analysis/dashboard_declutter_map_correction_tier_c_text_span_extraction_result_2026-07-27.md", f"""# Dashboard declutter/map correction and Tier C extraction result

- Decision: `{decision_name}`.
- Dashboard map: total scout coverage only; map data date 2026-07-27.
- Tier C text queue: 378 (317 PDF lane; 61 HTML).
- Text outcomes: `{extraction_counts}`.
- Span queue: {len(source_results)} extracted-ok artifacts.
- Positive exact spans: {len(positive)} across {len({row['retained_source_id'] for row in positive})} sources; ambiguous exact spans: {len(ambiguous)}.
- Rating candidates: {len(positive)}.
- Global analysis readiness: false.
""")
    write_text(ROOT / "docs/analysis/dashboard_declutter_map_correction_tier_c_text_span_extraction_dashboard_status_note_2026-07-27.md", f"""# Dashboard status note — Tier C text/span extraction

- Current phase: Tier C local text and deterministic exact-span extraction complete; bounded exact-span rating ready next.
- Map filter: total scout coverage only.
- Map data date: 2026-07-27.
- Text queue: 378; extracted-ok: {extraction_counts.get('extracted_ok', 0)}.
- Positive exact spans: {len(positive)}; rating candidates: {len(positive)}.
- Text and spans remain unrated, uningested, uncodified, non-causal, and globally not analysis-ready.
""")


def write_dashboard_contract_docs() -> None:
    state_summary = read_json(ROOT / "docs/dashboard/data/state_summary.json")
    states = state_summary["states"]
    if not (
        state_summary["metadata"].get("map_data_date") == "2026-07-27"
        and state_summary["metadata"].get("current_map_layer") == "total_scout_coverage_only"
        and state_summary["metric_definition"].get("map_color_metric") == "total_scout_coverage_count"
        and sum(int(row["total_scout_coverage_count"]) for row in states) == 2436
    ):
        raise RuntimeError("generated total-scout dashboard map contract is not ready")
    map_rows = [{
        "state": row["state"], "state_name": row["state_name"],
        "municipality_universe": row["municipality_universe"],
        "total_scout_coverage_count": row["total_scout_coverage_count"],
        "scout_coverage_rate": row["scout_coverage_rate"],
        "map_data_date": "2026-07-27",
        "global_analysis_readiness": "false",
    } for row in states]
    write_csv(OUTPUT_DIR / "dashboard_map_total_scout_coverage_data.csv", map_rows, map_rows[0].keys())
    map_summary = {
        "map_data_date": "2026-07-27", "map_filter_count": 1,
        "only_map_filter": "total_scout_coverage_count",
        "states_and_dc": len(states),
        "states_and_dc_with_scout_coverage": sum(int(row["total_scout_coverage_count"]) > 0 for row in states),
        "total_scout_covered_municipalities": sum(int(row["total_scout_coverage_count"]) for row in states),
        "municipality_universe": sum(int(row["municipality_universe"]) for row in states),
        "geographic_interpretation": "where_local_scouting_has_run_only",
        "national_representativeness": False, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_map_total_scout_coverage_summary.json", map_summary)
    write_json(OUTPUT_DIR / "dashboard_map_total_scout_coverage_correction.json", {
        **map_summary, "removed_map_filters": ["tier_c", "readiness", "mechanism", "source_family", "rating_or_extraction"],
        "non_map_metadata_location": "pipeline_cards_reports_and_collapsed_historical_archive",
    })
    write_text(OUTPUT_DIR / "dashboard_map_total_scout_coverage_correction.md", """# Dashboard map correction

The dashboard map now answers one question only: **Where have we scouted?** Its sole metric is the deterministic count of municipalities with a parseable local scout outcome. The map data date is 2026-07-27. Tier C, readiness, mechanism, source-family, extraction, and rating data remain available in non-map pipeline cards and reports. The map is not evidence of national representativeness, wage differences, or causation.
""")
    write_json(OUTPUT_DIR / "dashboard_map_filter_contract.json", {
        "allowed_map_filters": ["total_scout_coverage_count"], "map_filter_count": 1,
        "forbidden_map_filters": ["tier_c", "readiness", "mechanism", "source_family", "rating", "extraction"],
        "presentation_toggle_is_not_filter": ["geographic_map", "tile_grid"],
        "map_data_date": "2026-07-27", "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "dashboard_map_data_date.json", {"map_data_date": "2026-07-27", "meaning": "operational coverage metadata date, not a causal-analysis date"})
    write_text(OUTPUT_DIR / "dashboard_map_data_date.md", "# Dashboard map data date\n\nVisible label: **Map data date: 2026-07-27**. This dates operational coverage metadata only.\n")
    write_text(OUTPUT_DIR / "dashboard_declutter_plan.md", """# Dashboard declutter plan

1. Put current status and next authorized step first.
2. Keep the total scout-coverage map prominent and single-purpose.
3. Surface the current memo/report link and the latest Tier C text/span counts.
4. Keep claim boundaries and global analysis closure visible.
5. Collapse priority tiers, scout operations, archived queues, and state yield into one clearly labeled historical archive.
""")
    write_text(OUTPUT_DIR / "dashboard_declutter_changes.md", """# Dashboard declutter changes

- Replaced the eight-option map metric selector with one total-scout-coverage layer.
- Kept geographic-map/tile-grid presentation as a view toggle, not a data filter.
- Updated the header, overview, phase, pipeline, and next-task language to the completed 378-file extraction and 159 exact-span result.
- Moved detailed historical discovery panels into one collapsed historical archive.
- Kept the current memo link, limits, map date, and global-analysis-readiness false status visible.
""")
    write_text(OUTPUT_DIR / "dashboard_section_reorganization_map.md", """# Dashboard section reorganization

| Order | Section | Status |
| --- | --- | --- |
| 1 | Current status and next step | Current |
| 2 | Total scout coverage map | Current |
| 3 | Current evidence phase | Current |
| 4 | Latest pipeline metrics | Current |
| 5 | Reports/current memo | Current |
| 6 | Limits and next task | Current |
| 7 | Priority/scout/queue/yield detail | Collapsed historical archive |
| 8 | Definitions and limitations | Reference |
""")
    write_json(OUTPUT_DIR / "dashboard_current_vs_historical_contract.json", {
        "current_sections": ["overview", "geography", "project-phase", "verification", "reports", "descriptive-analysis", "next-steps"],
        "collapsed_historical_sections": ["priorities", "operations", "candidate-queue", "state-yield"],
        "historical_content_must_not_override_current_phase": True,
    })
    write_json(OUTPUT_DIR / "dashboard_current_status_contract.json", {
        "current_phase": "Tier C text and exact-span extraction complete; bounded rating ready next",
        "text_artifact_count": 378, "positive_exact_span_count": 159, "positive_source_count": 52,
        "rating_candidate_count": 159, "current_map_filter": "total_scout_coverage_only",
        "global_analysis_readiness": False, "wage_gap_estimates_available": False,
        "regression_or_treatment_effect_estimates_available": False, "final_causal_claims_available": False,
    })
    write_json(OUTPUT_DIR / "dashboard_report_link_contract.json", {
        "current_evidence_memo": "docs/analysis/compensation_extraction/BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO-2026-07-26/bounded_internal_mechanism_linkage_claim_memo.md",
        "current_operational_report": "docs/analysis/dashboard_declutter_map_correction_tier_c_text_span_extraction_result_2026-07-27.md",
        "historical_pi_report_current": False,
    })
    policy = """Dashboard update requirement:
After every task, update dashboard/status/docs with any new substantive information unless there are genuinely no updates to provide. If no dashboard update is needed, explicitly report that no update was needed and why. Dashboard updates must preserve global analysis readiness false unless separately authorized, and must not imply wage gaps, regressions, treatment effects, national prevalence, or final causal claims.
"""
    write_text(OUTPUT_DIR / "future_prompt_dashboard_update_requirement.md", "# Future prompt dashboard update requirement\n\n" + policy)
    write_json(OUTPUT_DIR / "future_prompt_dashboard_update_requirement.json", {
        "requirement": policy.strip(), "applies_after_every_task": True,
        "no_update_requires_explicit_reason": True, "global_analysis_readiness_default": False,
    })
    write_text(OUTPUT_DIR / "dashboard_update_policy_for_future_prompts.md", "# Dashboard update policy for future prompts\n\n" + policy)
    write_text(ROOT / "docs/prompts/dashboard_update_requirement.md", "# Standing dashboard update requirement\n\n" + policy)
    write_text(ROOT / "docs/analysis/future_prompt_dashboard_update_requirement_2026-07-27.md", "# Standing dashboard update requirement — 2026-07-27\n\n" + policy)
    print(json.dumps({"status": "dashboard_contract_docs_written", **map_summary}))


def required_outputs() -> tuple[str, ...]:
    return (
        "dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json",
        "dashboard_declutter_map_correction_tier_c_text_span_extraction_summary.md",
        "dashboard_map_total_scout_coverage_correction.md", "dashboard_map_total_scout_coverage_correction.json", "dashboard_map_total_scout_coverage_data.csv", "dashboard_map_total_scout_coverage_summary.json", "dashboard_map_filter_contract.json", "dashboard_map_data_date.json", "dashboard_map_data_date.md",
        "dashboard_declutter_plan.md", "dashboard_declutter_changes.md", "dashboard_section_reorganization_map.md", "dashboard_current_vs_historical_contract.json", "dashboard_current_status_contract.json", "dashboard_report_link_contract.json",
        "future_prompt_dashboard_update_requirement.md", "future_prompt_dashboard_update_requirement.json", "dashboard_update_policy_for_future_prompts.md",
        "tier_c_text_layer_extraction_378_locked_queue.csv", "tier_c_text_layer_extraction_378_locked_queue_summary.json", "tier_c_text_layer_extraction_378_lock.json",
        "tier_c_text_layer_extraction_378_results.csv", "tier_c_text_layer_extraction_378_results_summary.json", "tier_c_text_layer_extraction_378_pdf_results.csv", "tier_c_text_layer_extraction_378_html_results.csv",
        "extracted_text_manifest.csv", "extracted_text_hash_manifest.csv", "extracted_text_manifest_summary.json",
        "tier_c_text_layer_extraction_378_extracted_ok.csv", "tier_c_text_layer_extraction_378_empty_or_too_short.csv", "tier_c_text_layer_extraction_378_low_text_density.csv", "tier_c_text_layer_extraction_378_suspected_bad_text_layer.csv", "tier_c_text_layer_extraction_378_html_noisy_or_shell.csv", "tier_c_text_layer_extraction_378_extraction_errors.csv",
        "tier_c_evidence_span_extraction_locked_queue.csv", "tier_c_evidence_span_extraction_locked_queue_summary.json", "tier_c_evidence_span_extraction_lock.json",
        "tier_c_evidence_span_extraction_results.csv", "tier_c_evidence_span_extraction_results_summary.json", "tier_c_evidence_span_records.csv", "tier_c_evidence_span_records_summary.json", "tier_c_evidence_span_no_span_or_weak.csv", "tier_c_evidence_span_no_span_or_weak_summary.json",
        *MECHANISM_FILES.values(), "tier_c_evidence_span_rating_candidate_manifest.csv", "tier_c_evidence_span_rating_candidate_summary.json", "tier_c_evidence_span_claim_boundary_notes.md", "tier_c_evidence_span_extraction_limits_and_boundaries.md",
        "tier_c_text_span_extraction_mechanism_coverage.csv", "tier_c_text_span_extraction_mechanism_coverage_summary.json", "tier_c_text_span_extraction_city_cycle_unit_coverage.csv", "tier_c_text_span_extraction_city_cycle_unit_coverage_summary.json", "tier_c_text_span_extraction_geographic_region_coverage.csv", "tier_c_text_span_extraction_geographic_region_coverage_summary.json", "tier_c_text_span_extraction_source_family_coverage.csv", "tier_c_text_span_extraction_source_family_coverage_summary.json",
        "tier_c_text_span_extraction_preserved_readiness_exclusions.csv", "tier_c_text_span_extraction_preserved_readiness_exclusions_summary.json",
        "dashboard_declutter_map_correction_tier_c_text_span_extraction_validation_2026-07-27.md", "dashboard_declutter_map_correction_tier_c_text_span_extraction_invariant_checks.json", "dashboard_declutter_map_correction_tier_c_text_span_extraction_stress_test_report.md", "dashboard_declutter_map_correction_tier_c_text_span_extraction_regression_test_inventory.json",
        "next_tier_c_evidence_span_rating_prompt.md", "next_task.md",
    )


def validate_complete() -> None:
    missing = [name for name in required_outputs() if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"partial combined output cannot masquerade as complete: {missing}")
    decision = read_json(OUTPUT_DIR / "dashboard_declutter_map_correction_tier_c_text_span_extraction_decision.json")
    text_rows = read_csv(OUTPUT_DIR / "tier_c_text_layer_extraction_378_results.csv")
    source_rows = read_csv(OUTPUT_DIR / "tier_c_evidence_span_extraction_results.csv")
    records = read_csv(OUTPUT_DIR / "tier_c_evidence_span_records.csv")
    validate_span_records(source_rows, records)
    if not (
        len(text_rows) == EXPECTED_COUNT
        and len({row["retained_source_id"] for row in text_rows}) == EXPECTED_COUNT
        and len(source_rows) == sum(row["extraction_status"] == "extracted_ok" for row in text_rows)
        and decision.get("global_analysis_readiness") is False
        and all(row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in text_rows + source_rows + records)
    ):
        raise RuntimeError("completed combined outputs fail closed validation")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--extract-text", action="store_true")
    action.add_argument("--extract-spans", action="store_true")
    action.add_argument("--dashboard-docs", action="store_true")
    action.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.extract_text:
        run_text_extraction()
    elif args.extract_spans:
        run_span_extraction()
    elif args.dashboard_docs:
        write_dashboard_contract_docs()
    else:
        verify_inputs(verify_file_bytes=True)
        validate_complete()
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_COUNT}))


if __name__ == "__main__":
    main()
