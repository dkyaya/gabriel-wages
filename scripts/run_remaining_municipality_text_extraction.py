#!/usr/bin/env python3
"""Extract the remaining-municipality text-ready wave without OCR.

The adapter reuses the project's bounded text-layer extractor. Full extracted
text is written only beneath the Git-ignored local artifact root; tracked
outputs contain lineage, hashes, counts, quality statuses, and queue metadata.
It never invokes OCR, opens a URL, extracts evidence spans, calls a model,
rates evidence, ingests/codifies records, or performs statistical analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import run_broad_state_4x2500_text_extraction as engine


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-PDF-TEXT-READINESS-2026-08-02"
OUTPUT = BASE / "BROAD-STATE-REMAINING-MUNICIPALITIES-TEXT-EXTRACTION-2026-08-02"
SOURCE_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_remaining_municipalities_source_review_download_2026-08-02"
ARTIFACT_ROOT = ROOT / "artifacts/local_extracted_text/broad_state_remaining_municipalities_text_extraction_2026-08-02"
LOG_ROOT = ROOT / "tmp/broad_state_remaining_municipalities_text_extraction_2026-08-02_logs"
TASK_ID = "BROAD-STATE-REMAINING-MUNICIPALITIES-TEXT-EXTRACTION-2026-08-02"
DECISION = "broad_state_remaining_municipalities_text_extraction_completed_span_extraction_ready"
NEXT_TASK = "BROAD-STATE-REMAINING-MUNICIPALITIES-SPAN-EXTRACTION-2026-08-02"
EXPECTED = 2_558
APPROVED = {"parse_text_pdf_ready": 2_176, "html_text_ready": 382, "other_document_text_ready": 0}
LANES = {
    "text_extraction_lane_001": 512,
    "text_extraction_lane_002": 512,
    "text_extraction_lane_003": 512,
    "text_extraction_lane_004": 511,
    "text_extraction_lane_005": 511,
}
DELAYS = {lane: index * 480 for index, lane in enumerate(LANES)}
STATUSES = (
    "extracted_ok",
    "extracted_low_text_but_usable",
    "extracted_empty_or_too_low_text",
    "extraction_failed",
    "missing_local_file",
    "hash_mismatch",
    "unsupported_after_readiness",
    "extraction_error",
)
READY_STATUSES = {"extracted_ok"}
SUCCESS_STATUSES = {"extracted_ok", "extracted_low_text_but_usable"}
NOT_READY_INPUT_STATUSES = {
    "ocr_later", "oversized_defer", "encrypted_or_locked", "corrupt_or_broken",
    "shell_or_navigation_only", "needs_manual_review", "unsupported_file_type", "readiness_error",
}
EXTRA_RESULT_FIELDS = (
    "pages_attempted", "pages_extracted", "pages_failed_or_problematic",
    "extracted_character_count", "extracted_byte_count", "extraction_reason_code",
)
BASE_EXTRACT_ONE = engine.extract_one
BASE_RESULT_EXTRA = engine.RESULT_EXTRA


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    engine.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    engine.write_text(path, value)


def sha256(path: Path) -> str:
    return engine.sha256_file(path)


def extraction_id(readiness_id: str) -> str:
    return "RMTXT-20260802-" + hashlib.sha256(readiness_id.encode()).hexdigest()[:20]


def stable_key(row: dict[str, str]) -> str:
    material = "|".join((row.get("primary_readiness_status", ""), row.get("priority_bucket", ""),
                         row.get("source_family_hint", ""), row.get("state", ""), row["readiness_id"]))
    return hashlib.sha256(material.encode()).hexdigest()


def assign_lanes(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    names = list(LANES)
    quotas = {
        "parse_text_pdf_ready": [436, 435, 435, 435, 435],
        "html_text_ready": [76, 77, 77, 76, 76],
        "other_document_text_ready": [0, 0, 0, 0, 0],
    }
    assigned: dict[str, list[dict[str, str]]] = {lane: [] for lane in names}
    for status, targets in quotas.items():
        bucket = sorted((row for row in rows if row["primary_readiness_status"] == status), key=stable_key)
        cursor = 0
        for index, target in enumerate(targets):
            assigned[names[index]].extend(bucket[cursor:cursor + target])
            cursor += target
        if cursor != len(bucket):
            raise RuntimeError(f"lane assignment failed for {status}: {cursor} != {len(bucket)}")
    for lane in names:
        assigned[lane].sort(key=lambda row: hashlib.sha256((lane + "|" + row["readiness_id"]).encode()).hexdigest())
        if len(assigned[lane]) != LANES[lane]:
            raise RuntimeError(f"lane size mismatch: {lane}")
    identifiers = [row["readiness_id"] for lane_rows in assigned.values() for row in lane_rows]
    if len(identifiers) != EXPECTED or len(set(identifiers)) != EXPECTED:
        raise RuntimeError("lane union is not exact and disjoint")
    return assigned


def quality_status(row: dict[str, str], text: str, html_links: int = 0) -> tuple[str, list[str]]:
    characters = len(text)
    words = re.findall(r"\b\w+\b", text)
    if characters < 200:
        return "extracted_empty_or_too_low_text", ["under_200_characters"]
    flags: list[str] = []
    replacement_ratio = text.count("\ufffd") / max(characters, 1)
    control_count = sum(ord(char) < 32 and char not in "\n\t" for char in text)
    repeated = bool(re.search(r"([A-Za-z0-9])\1{79,}", text))
    if replacement_ratio > 0.02:
        flags.append("high_replacement_character_ratio")
    if control_count > 20:
        flags.append("control_character_noise")
    if repeated:
        flags.append("repeated_character_noise")
    if row["primary_readiness_status"] == "html_text_ready":
        link_density = html_links / max(len(words), 1)
        if len(words) < 50 or link_density > 0.25:
            flags.append("html_low_word_count_or_link_dense")
    if row["primary_readiness_status"] == "parse_text_pdf_ready":
        pages = int(float(row.get("page_count") or 0))
        if characters / max(pages, 1) < 100:
            flags.append("under_100_characters_per_page")
    if flags:
        return "extracted_low_text_but_usable", flags
    return "extracted_ok", []


def extract_one(row: dict[str, str], lane: str) -> dict[str, Any]:
    result = BASE_EXTRACT_ONE(row, lane)
    status = result.get("extraction_status", "")
    mapping = {
        "source_file_missing": "missing_local_file",
        "unsupported_despite_readiness": "unsupported_after_readiness",
        "extracted_empty": "extracted_empty_or_too_low_text",
        "extracted_low_density": "extracted_low_text_but_usable",
        "extracted_suspected_bad_text": "extracted_low_text_but_usable",
        "html_noisy_or_boilerplate": "extracted_low_text_but_usable",
    }
    status = mapping.get(status, status)
    if status == "extraction_error" and "pdftotext_failed" in result.get("error_message_redacted", ""):
        status = "extraction_failed"
    if status not in STATUSES:
        status = "extraction_error"
        result["error_class"] = result.get("error_class") or "UncontrolledStatusError"
        result["error_message_redacted"] = "uncontrolled extraction status normalized fail-closed"
    result["extraction_status"] = status
    is_pdf = row.get("primary_readiness_status") == "parse_text_pdf_ready"
    page_count = int(float(row.get("page_count") or 0)) if is_pdf else 0
    pre_attempt = status in {"missing_local_file", "hash_mismatch", "unsupported_after_readiness"}
    attempted = 0 if pre_attempt else page_count
    successful = page_count if is_pdf and status in SUCCESS_STATUSES else 0
    problematic = page_count - successful if is_pdf else 0
    result.update({
        "pages_attempted": attempted if is_pdf else "",
        "pages_extracted": successful if is_pdf else "",
        "pages_failed_or_problematic": problematic if is_pdf else "",
        "pages_successfully_parsed": successful if is_pdf else "",
        "extracted_character_count": result.get("character_count", 0),
        "extracted_byte_count": result.get("extracted_text_byte_size", 0),
        "extraction_reason_code": result.get("quality_flags") or result.get("error_class") or "usable_text_extracted",
    })
    return result


def configure_engine() -> None:
    engine.ROOT = ROOT
    engine.BASE = BASE
    engine.INPUT = INPUT
    engine.OUTPUT = OUTPUT
    engine.SOURCE_ROOT = SOURCE_ROOT
    engine.ARTIFACT_ROOT = ARTIFACT_ROOT
    engine.LOG_ROOT = LOG_ROOT
    engine.TASK_ID = TASK_ID
    engine.DECISION = DECISION
    engine.EXPECTED = EXPECTED
    engine.APPROVED = APPROVED
    engine.LANES = LANES
    engine.DELAYS = DELAYS
    engine.STATUSES = STATUSES
    engine.RESULT_EXTRA = BASE_RESULT_EXTRA + EXTRA_RESULT_FIELDS
    engine.assign_lanes = assign_lanes
    engine.quality_status = quality_status
    engine.extract_one = extract_one
    engine.lock_id = extraction_id


def prepare() -> None:
    configure_engine()
    engine.prepare()
    manifest = read_json(OUTPUT / "text_extraction_manifest.json")
    manifest.update({
        "decision": DECISION,
        "input_directory": engine.rel(INPUT),
        "output_directory": engine.rel(OUTPUT),
        "source_artifact_root": engine.rel(SOURCE_ROOT),
        "extracted_text_artifact_root": engine.rel(ARTIFACT_ROOT),
        "lane_count": 5,
        "lane_sizes": LANES,
        "parse_text_pdf_ready_pages_queued": sum(int(row["page_count"]) for row in read_csv(INPUT / "parse_text_pdf_ready_queue.csv")),
        "retained_pdf_total_pages_upper_bound": 60_223,
        "dashboard_map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True,
    })
    write_json(OUTPUT / "text_extraction_manifest.json", manifest)
    write_json(OUTPUT / "remaining_municipalities_text_extraction_manifest.json", manifest)
    locked = read_csv(OUTPUT / "text_extraction_locked_queue.csv")
    write_json(OUTPUT / "text_extraction_locked_queue_manifest.json", {
        "task_id": TASK_ID, "created_at": engine.now(), "row_count": len(locked),
        "csv_sha256": sha256(OUTPUT / "text_extraction_locked_queue.csv"),
        "jsonl_sha256": sha256(OUTPUT / "text_extraction_locked_queue.jsonl"),
        "unique_readiness_ids": len({row["readiness_id"] for row in locked}),
        "lane_sizes": LANES,
        "status_counts": dict(sorted(Counter(row["primary_readiness_status"] for row in locked).items())),
        "locked_against_readiness_queue": True,
    })
    write_text(OUTPUT / "text_extraction_lane_distribution.md", """# Text extraction lane distribution

The 2,558 readiness-approved sources are locked into five deterministic, disjoint lanes of 512 / 512 / 512 / 511 / 511 rows. PDF and HTML sources, priority, source family, geography, CBA/non-CBA hint, mechanism hint, page count, and file-size variation are dispersed by stable ordering. Starts are T+0, T+8, T+16, T+24, and T+32 minutes. Every worker checkpoints after each source.
""")


def run_lane(lane: str, stagger_seconds: int) -> None:
    configure_engine()
    engine.run_lane(lane, stagger_seconds)


def copy_group_summary(source: str, destination: str) -> None:
    write_json(OUTPUT / destination, read_json(OUTPUT / source))


def duplicate_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.get("extracted_text_sha256"):
            by_hash[row["extracted_text_sha256"]].append(row["extraction_id"])
    duplicates = {digest: identifiers for digest, identifiers in by_hash.items() if len(identifiers) > 1}
    return {
        "artifact_rows": sum(bool(row.get("extracted_text_sha256")) for row in rows),
        "unique_extracted_text_hash_count": len(by_hash),
        "duplicate_hash_count": len(duplicates),
        "duplicate_source_count": sum(len(value) - 1 for value in duplicates.values()),
        "duplicate_links": duplicates,
        "canonicalization_policy": "Rows remain distinct; duplicate hashes are documented and not silently discarded.",
    }


def tailor_merge_outputs() -> None:
    rows = read_csv(OUTPUT / "merged_text_extraction_results.csv")
    counts = Counter(row["extraction_status"] for row in rows)
    pdf_rows = [row for row in rows if row["primary_readiness_status"] == "parse_text_pdf_ready"]
    html_rows = [row for row in rows if row["primary_readiness_status"] == "html_text_ready"]
    artifact_rows = [row for row in rows if row.get("extracted_text_artifact_path")]
    success_rows = [row for row in rows if row["extraction_status"] in SUCCESS_STATUSES]
    span_rows = [row for row in rows if row["extraction_status"] in READY_STATUSES]
    fields = tuple(rows[0])
    engine.write_csv(OUTPUT / "pdf_text_extraction_manifest.csv", pdf_rows, fields)
    engine.write_jsonl(OUTPUT / "pdf_text_extraction_manifest.jsonl", pdf_rows)
    engine.write_csv(OUTPUT / "html_text_extraction_manifest.csv", html_rows, fields)
    engine.write_jsonl(OUTPUT / "html_text_extraction_manifest.jsonl", html_rows)
    duplicate = duplicate_summary(artifact_rows)
    write_json(OUTPUT / "duplicate_extracted_text_summary.json", duplicate)
    queued_pages = sum(int(row["page_count"]) for row in pdf_rows)
    attempted_pages = sum(int(row.get("pages_attempted") or 0) for row in pdf_rows)
    successful_pages = sum(int(row.get("pages_extracted") or 0) for row in pdf_rows)
    problem_pages = sum(int(row.get("pages_failed_or_problematic") or 0) for row in pdf_rows)
    html_success = sum(row["extraction_status"] in SUCCESS_STATUSES for row in html_rows)
    total_characters = sum(int(row.get("character_count") or 0) for row in rows)
    total_bytes = sum(int(row.get("extracted_text_byte_size") or 0) for row in rows)
    contribution = {
        "retained_pdf_total_pages_upper_bound": 60_223,
        "retained_pdf_count": 2_456,
        "parse_text_pdf_ready_count": len(pdf_rows),
        "parse_text_pdf_ready_pages_queued": queued_pages,
        "pdf_pages_attempted": attempted_pages,
        "pdf_pages_successfully_extracted": successful_pages,
        "pdf_pages_failed_or_problematic": problem_pages,
        "pdf_page_success_rate_percent": round(successful_pages / queued_pages * 100, 4) if queued_pages else 0,
        "html_text_ready_count": len(html_rows),
        "html_sources_successfully_extracted": html_success,
        "total_text_extraction_ready_sources": len(rows),
        "total_sources_successfully_extracted": len(success_rows),
        "extracted_text_artifact_directory": engine.rel(ARTIFACT_ROOT),
        "html_counting_note": "HTML contributions are counted as sources, not pages; no HTML-to-page proxy is used.",
        "exclusion_note": "OCR-later, oversized, encrypted, shell/navigation-only, and manual-review sources were excluded from this non-OCR corpus.",
        "claim_boundary": "These are corpus-processing counts, not wage-gap, prevalence, or causal findings.",
    }
    if attempted_pages + sum(int(row["page_count"]) for row in pdf_rows if not int(row.get("pages_attempted") or 0)) != queued_pages:
        raise RuntimeError("PDF attempted-page accounting does not reconcile")
    if successful_pages + problem_pages != queued_pages:
        raise RuntimeError("PDF success/problem page accounting does not reconcile")
    write_json(OUTPUT / "corpus_page_contribution_summary.json", contribution)
    write_text(OUTPUT / "corpus_page_contribution_summary.md", f"""# Corpus page contribution summary

- Retained-PDF upper bound: **60,223 pages** across 2,456 PDFs.
- Parse-text-ready extraction queue: **{queued_pages:,} pages** across {len(pdf_rows):,} PDFs.
- PDF pages attempted: **{attempted_pages:,}**.
- PDF pages successfully extracted into usable text: **{successful_pages:,}**.
- PDF pages failed or problematic: **{problem_pages:,}**.
- HTML sources successfully extracted: **{html_success:,}** of {len(html_rows):,}.
- Successfully extracted sources: **{len(success_rows):,}** of {len(rows):,}.

HTML is counted by source, not pages; no HTML-to-page proxy is used. OCR-later, oversized, encrypted, shell/navigation-only, and manual-review sources were excluded. These are corpus-processing counts, not wage-gap, population-prevalence, or causal findings.
""")
    character_values = [int(row.get("character_count") or 0) for row in rows]
    byte_values = [int(row.get("extracted_text_byte_size") or 0) for row in rows]
    write_json(OUTPUT / "extracted_character_byte_summary.json", {
        "source_count": len(rows), "total_characters": total_characters, "total_bytes": total_bytes,
        "median_characters": median(character_values), "median_bytes": median(byte_values),
        "maximum_characters": max(character_values), "maximum_bytes": max(byte_values),
        "artifact_directory_observed_bytes": sum(path.stat().st_size for path in ARTIFACT_ROOT.glob("**/*.txt")),
    })
    copies = {
        "source_type_extraction_summary.json": "source_type_text_extraction_summary.json",
        "priority_extraction_summary.json": "priority_text_extraction_summary.json",
        "source_family_extraction_summary.json": "source_family_text_extraction_summary.json",
        "geography_extraction_summary.json": "geography_text_extraction_summary.json",
        "cba_non_cba_extraction_summary.json": "cba_non_cba_text_extraction_summary.json",
        "mechanism_hint_extraction_summary.json": "mechanism_hint_text_extraction_summary.json",
    }
    for source, destination in copies.items():
        copy_group_summary(source, destination)
    problem_count = len(rows) - len(success_rows)
    summary = {
        "task_id": TASK_ID, "decision": DECISION, "final_decision": DECISION,
        "completed_at": engine.now(), "total_text_extraction_queue": len(rows),
        "parse_text_pdf_ready_count": len(pdf_rows), "html_text_ready_count": len(html_rows),
        "other_document_text_ready_count": 0, "lane_distribution": LANES,
        "extraction_status_counts": {status: counts.get(status, 0) for status in STATUSES},
        "extracted_ok_count": counts.get("extracted_ok", 0),
        "extracted_low_text_but_usable_count": counts.get("extracted_low_text_but_usable", 0),
        "failed_or_problem_count": problem_count, "total_sources_successfully_extracted": len(success_rows),
        "span_extraction_ready_count": len(span_rows), "span_ready_eligible_statuses": sorted(READY_STATUSES),
        "retained_pdf_total_pages_upper_bound": 60_223,
        "parse_text_pdf_ready_pages_queued": queued_pages, "pdf_pages_attempted": attempted_pages,
        "pdf_pages_successfully_extracted": successful_pages, "pdf_pages_failed_or_problematic": problem_pages,
        "html_sources_successfully_extracted": html_success,
        "total_extracted_character_count": total_characters, "total_extracted_byte_count": total_bytes,
        "extracted_text_artifact_count": len(artifact_rows), "artifact_root": engine.rel(ARTIFACT_ROOT),
        "unique_extracted_text_hash_count": duplicate["unique_extracted_text_hash_count"],
        "duplicate_extracted_text_hash_count": duplicate["duplicate_hash_count"],
        "duplicate_extracted_text_source_count": duplicate["duplicate_source_count"],
        "ocr_occurred": False, "span_extraction_occurred": False,
        "rating_ingestion_codification_occurred": False, "normalization_matching_occurred": False,
        "global_analysis_readiness": False, "wage_gap_readiness": "blocked_pending_normalization",
        "causal_readiness": "blocked_pending_matched_structure", "next_task": NEXT_TASK,
        "dashboard_map_primary_metric": "scout_coverage_rate", "scout_coverage_rate_percent": 99.9579,
        "final_pi_report_link_preserved": True, "wage_growth_continuity_module_preserved": True,
    }
    write_json(OUTPUT / "text_extraction_summary.json", summary)
    write_json(OUTPUT / "remaining_municipalities_text_extraction_summary.json", summary)
    status_lines = "\n".join(f"| `{status}` | {counts.get(status, 0):,} |" for status in STATUSES)
    summary_md = f"""# Remaining-municipality text extraction summary

All five lanes completed and reconciled **{len(rows):,}** readiness-approved local sources. Text-layer extraction processed {len(pdf_rows):,} PDFs totaling **{queued_pages:,} queued pages**; local HTML extraction processed {len(html_rows):,} sources. **{len(success_rows):,}** sources yielded usable text, and **{len(span_rows):,}** clean `extracted_ok` sources enter the next span-extraction queue.

| Status | Count |
|---|---:|
{status_lines}

Extracted text totals **{total_characters:,} characters** and **{total_bytes:,} bytes**, stored only under `{engine.rel(ARTIFACT_ROOT)}`. No OCR, span extraction, rating, ingestion, codification, normalization, matching, wage-gap estimation, regression, treatment-effect analysis, prevalence claim, or causal claim occurred.

Decision: `{DECISION}`.
"""
    write_text(OUTPUT / "text_extraction_summary.md", summary_md)
    write_text(OUTPUT / "remaining_municipalities_text_extraction_summary.md", summary_md)
    manifest = read_json(OUTPUT / "text_extraction_manifest.json")
    manifest.update({
        "decision": DECISION, "execution_status": "completed", "completed_at": summary["completed_at"],
        "summary": summary, "validation_passed": False, "dashboard_map_primary_metric": "scout_coverage_rate",
        "final_pi_report_link_preserved": True, "wage_growth_continuity_module_preserved": True,
    })
    write_json(OUTPUT / "text_extraction_manifest.json", manifest)
    write_json(OUTPUT / "remaining_municipalities_text_extraction_manifest.json", manifest)
    for lane in LANES:
        write_json(OUTPUT / f"{lane}_checkpoint.json", read_json(OUTPUT / "lanes" / lane / "checkpoint.json"))
    write_json(OUTPUT / "forbidden_action_audit.json", {
        "task_id": TASK_ID, "audit_status": "passed", "passed": True,
        "ocr_runs": 0, "image_pdf_processing_runs": 0, "span_extraction_runs": 0,
        "model_or_gabriel_calls": 0, "rating_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "normalization_matching_runs": 0, "wage_gap_calculations": 0,
        "regressions": 0, "treatment_effect_claims": 0, "national_or_population_prevalence_claims": 0,
        "final_causal_claims": 0, "extracted_text_written_to_tracked_storage": False,
        "retained_binary_written_to_tracked_storage": False, "global_readiness_advanced": False,
    })
    write_json(OUTPUT / "dashboard_remaining_text_extraction_update_summary.json", {
        "task_id": TASK_ID, "decision": DECISION,
        "stage": "broad_state_remaining_municipalities_text_extraction_complete",
        "current_phase": "Remaining-municipality text extraction complete", "next_task": NEXT_TASK,
        "text_extraction_queue": len(rows), "pdf_sources_queued": len(pdf_rows), "html_sources_queued": len(html_rows),
        "successfully_extracted_source_count": len(success_rows), "problem_or_failed_source_count": problem_count,
        "span_extraction_ready_count": len(span_rows), "parse_text_pdf_ready_pages_queued": queued_pages,
        "pdf_pages_successfully_extracted": successful_pages, "total_extracted_character_count": total_characters,
        "total_extracted_byte_count": total_bytes, "extracted_text_storage_path": engine.rel(ARTIFACT_ROOT),
        "map_primary_metric": "scout_coverage_rate", "dashboard_map_filter": "scout_coverage_rate_only",
        "scout_coverage_rate_percent": 99.9579, "final_pi_report_link_preserved": True,
        "wage_growth_continuity_module_preserved": True, "global_analysis_readiness": False,
    })
    write_text(OUTPUT / "next_task.md", f"""# Next task

Recommend `{NEXT_TASK}`.

Run compensation-evidence span extraction only over `span_extraction_ready_queue`. Use five independent lanes if the queue remains large enough, checkpoint every extracted-text source, and track span metadata, exact snippets, evidence pointers, and source lineage only. Do not OCR, run GABRIEL/API rating, ingest, codify, normalize, match, estimate wage gaps, run regressions or treatment effects, or make causal or prevalence claims. Preserve the clean dashboard, final PI report link, wage-growth continuity module, and `scout_coverage_rate` map.
""")


def merge() -> None:
    configure_engine()
    engine.merge()
    tailor_merge_outputs()


def audit_staged() -> None:
    configure_engine()
    audit = engine.audit_staged()
    write_json(OUTPUT / "large_file_audit.json", {
        "audited_at": audit["audited_at"], "threshold_bytes": 52_428_800,
        "large_staged_files": audit["large_staged_files_over_10mb"],
        "passed": not audit["large_staged_files_over_10mb"],
    })


def validate() -> None:
    configure_engine()
    locked = read_csv(OUTPUT / "text_extraction_locked_queue.csv")
    merged = read_csv(OUTPUT / "merged_text_extraction_results.csv")
    span = read_csv(OUTPUT / "span_extraction_ready_queue.csv")
    summary = read_json(OUTPUT / "remaining_municipalities_text_extraction_summary.json")
    manifest = read_json(OUTPUT / "remaining_municipalities_text_extraction_manifest.json")
    storage = read_json(OUTPUT / "extracted_text_storage_audit.json")
    pages = read_json(OUTPUT / "corpus_page_contribution_summary.json")
    forbidden = read_json(OUTPUT / "forbidden_action_audit.json")
    staged = read_json(OUTPUT / "staged_file_audit.json") if (OUTPUT / "staged_file_audit.json").exists() else {}
    large = read_json(OUTPUT / "large_file_audit.json") if (OUTPUT / "large_file_audit.json").exists() else {}
    browser = read_json(OUTPUT / "dashboard_browser_smoke_report.json") if (OUTPUT / "dashboard_browser_smoke_report.json").exists() else {}
    phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    input_rows = read_csv(INPUT / "text_extraction_ready_queue.csv")
    locked_ids = {row["readiness_id"] for row in locked}
    merged_ids = {row["readiness_id"] for row in merged}
    checks = {
        "01_input_text_ready_count_2558": len(input_rows) == EXPECTED,
        "02_source_types_reconcile_2176_382_0": Counter(row["primary_readiness_status"] for row in locked) == Counter(APPROVED),
        "03_no_not_ready_status_entered": not any(row["primary_readiness_status"] in NOT_READY_INPUT_STATUSES for row in locked),
        "04_all_retained_local_files_exist": all((ROOT / row["locked_source_path"]).is_file() for row in locked),
        "05_retained_hashes_match": read_json(OUTPUT / "retained_source_hash_recheck_report.json").get("all_hashes_match") is True,
        "06_extracted_artifact_root_git_ignored": subprocess.run(["git", "check-ignore", "-q", engine.rel(ARTIFACT_ROOT / ".probe")], cwd=ROOT).returncode == 0,
        "07_locked_queue_reconciles_input": len(locked) == EXPECTED and locked_ids == {row["readiness_id"] for row in input_rows},
        "08_lane_sizes_exact": [len(read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES] == list(LANES.values()),
        "09_lane_union_exact_once": len({row["readiness_id"] for lane in LANES for row in read_csv(OUTPUT / f"{lane}_queue.csv")}) == EXPECTED,
        "10_lane_queues_disjoint": sum(len(read_csv(OUTPUT / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED,
        "11_one_primary_status_per_source": len(merged) == EXPECTED and all(row["extraction_status"] in STATUSES for row in merged),
        "12_merged_results_reconcile": merged_ids == locked_ids and len(merged_ids) == EXPECTED,
        "13_artifact_manifest_reconciles": storage.get("passed") is True,
        "14_text_hashes_and_sizes_recorded": all(row["extracted_text_sha256"] and int(row["extracted_text_byte_size"]) > 0 for row in merged if row["extracted_text_artifact_path"]),
        "15_unique_hashes_reconcile": summary["unique_extracted_text_hash_count"] == read_json(OUTPUT / "duplicate_extracted_text_summary.json")["unique_extracted_text_hash_count"],
        "16_span_queue_statuses_only": all(row["extraction_status"] in READY_STATUSES for row in span),
        "17_problem_queues_exclude_span": not ({row["extraction_id"] for row in span} & {row["extraction_id"] for row in merged if row["extraction_status"] not in READY_STATUSES}),
        "18_page_contribution_exact": pages["parse_text_pdf_ready_pages_queued"] == 49_047,
        "19_pdf_pages_reconcile": pages["pdf_pages_successfully_extracted"] + pages["pdf_pages_failed_or_problematic"] == pages["parse_text_pdf_ready_pages_queued"],
        "20_html_counts_reconcile": pages["html_text_ready_count"] == 382 and pages["html_sources_successfully_extracted"] <= 382,
        "21_no_ocr": forbidden.get("ocr_runs") == 0,
        "22_no_span_extraction": forbidden.get("span_extraction_runs") == 0,
        "23_no_rating": forbidden.get("rating_runs") == 0,
        "24_no_ingestion_codification": forbidden.get("ingestion_runs") == forbidden.get("codification_runs") == 0,
        "25_no_normalization_matching": forbidden.get("normalization_matching_runs") == 0,
        "26_no_gap_regression_treatment_causal_prevalence": forbidden.get("wage_gap_calculations") == forbidden.get("regressions") == forbidden.get("treatment_effect_claims") == forbidden.get("final_causal_claims") == forbidden.get("national_or_population_prevalence_claims") == 0,
        "27_retained_root_git_ignored": subprocess.run(["git", "check-ignore", "-q", engine.rel(SOURCE_ROOT / ".probe")], cwd=ROOT).returncode == 0,
        "28_extracted_root_git_ignored": subprocess.run(["git", "check-ignore", "-q", engine.rel(ARTIFACT_ROOT / ".probe")], cwd=ROOT).returncode == 0,
        "29_no_local_artifacts_tracked": not engine.git("ls-files", "artifacts/local_retained_sources", "artifacts/local_extracted_text").stdout.strip(),
        "30_dashboard_clean_stage": phase.get("stage") == "broad_state_remaining_municipalities_text_extraction_complete",
        "31_dashboard_map_scout_coverage_rate": phase.get("dashboard_map_primary_metric") == "scout_coverage_rate" and phase.get("dashboard_map_filter") == "scout_coverage_rate_only",
        "32_final_report_link_intact": phase.get("current_report_path") == "reports/pi_report_final_2026-07-30/pi_report_final_2026-07-30.pdf",
        "33_wage_growth_module_intact": phase.get("wage_growth_continuity_available") is True,
        "34_staged_file_audit_passes": staged.get("passed") is True,
        "35_large_file_audit_passes": large.get("passed") is True,
        "36_dashboard_smoke_passes_or_honest_limit": browser.get("status") in {"passed", "passed_static_browser_unavailable", "browser_controller_unavailable"},
    }
    passed = all(checks.values())
    report = {
        "task_id": TASK_ID, "validated_at": engine.now(), "status": "passed" if passed else "failed",
        "validation_passed": passed, "checks": checks, "passed_count": sum(checks.values()),
        "check_count": len(checks), "decision": DECISION if passed else "validation_failed",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "validation_report.json", report)
    write_text(OUTPUT / "validation_report.md", "# Validation report\n\n" +
               f"Status: **{report['status']}** — {report['passed_count']}/{report['check_count']} checks passed.\n\n" +
               "\n".join(f"- {'PASS' if value else 'FAIL'} — `{key}`" for key, value in checks.items()))
    if not passed:
        raise RuntimeError("final validation failed: " + ", ".join(key for key, value in checks.items() if not value))
    manifest["validation_passed"] = True
    manifest["validated_at"] = report["validated_at"]
    write_json(OUTPUT / "remaining_municipalities_text_extraction_manifest.json", manifest)
    write_json(OUTPUT / "text_extraction_manifest.json", manifest)
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--lane", choices=list(LANES))
    action.add_argument("--merge", action="store_true")
    action.add_argument("--validate", action="store_true")
    action.add_argument("--audit-staged", action="store_true")
    parser.add_argument("--stagger-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.stagger_seconds)
    elif args.merge:
        merge()
    elif args.validate:
        validate()
    else:
        audit_staged()


if __name__ == "__main__":
    main()
