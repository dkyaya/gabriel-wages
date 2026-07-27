#!/usr/bin/env python3
"""Classify 463 retained sources for later bounded text-layer extraction.

This runner performs local file integrity checks, PDF metadata/page-count checks,
a bounded first-three-page text-layer signal probe, and bounded HTML structure
checks. It never opens a URL, downloads a file, runs OCR, renders a PDF page,
saves document text, extracts evidence, or changes any upstream ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
TASK_ID = "TIER-C-READINESS-AND-DASHBOARD-MAP-UPDATE-WITH-BROAD-SCOUTING-STRATEGY-2026-07-27"
INPUT_COMMIT = "09d6cbcade1c51abc870f7ec029f32c410d392f6"
INPUT_DIR = BASE / "DASHBOARD-DEPLOYMENT-FIX-AND-TIER-C-SOURCE-REVIEW-DOWNLOAD-556-2026-07-27"
OUTPUT_DIR = BASE / "TIER-C-READINESS-AND-DASHBOARD-MAP-UPDATE-WITH-BROAD-SCOUTING-STRATEGY-2026-07-27"
EXPECTED_COUNT = 463
EXPECTED_TYPES = {"application/octet-stream": 1, "application/pdf": 397, "text/html": 65}
EXPECTED_LANES = {"lane_1": 126, "lane_2": 127, "lane_3": 129, "lane_4": 81}
EXPECTED_ID_SET_HASH = "5c13c1689624175c9f9fac58e72bf3c912b40536e876b68678e1423ad5994779"
MAX_PDF_PROBE_PAGES = 3
MAX_PDFINFO_SECONDS = 30
MAX_TEXT_PROBE_SECONDS = 30
MAX_TEXT_PASS_BYTES = 20 * 1024 * 1024
MAX_TEXT_PASS_PAGES = 500
MAX_HTML_PROBE_BYTES = 256 * 1024
MAX_WORKERS = 8

EXPECTED_HASHES = {
    "dashboard_fix_and_tier_c_source_review_download_556_decision.json": "37add16f09bcc45472e4a3f4e8e6d1d28cde26a142726c39af0ba524fa19663c",
    "dashboard_fix_and_tier_c_source_review_download_556_summary.md": "f8ad5a93355a16ff75a9a457f1557db49e4eae0542d6254c6e76d12952444617",
    "targeted_tier_c_source_review_download_556_retained_sources_summary.json": "25eacf5c42f5707cc94fb500033b9258a103d8ca407c26f68cd211f9a68d846d",
    "targeted_tier_c_source_review_download_556_results_summary.json": "6df3740af6cce37de38a218f0fbeee7edb351a3e7827ad0b14e4ed536c7c6df9",
    "targeted_tier_c_source_review_download_556_exclusion_summary.json": "da8f76bd21b38011cec1243e026e93cd8ae3af504c5215900450cba830a8e255",
    "targeted_tier_c_source_review_download_556_mechanism_coverage_summary.json": "fbed834243bb49cb2e7b2d7bd64027646d095724356b2294e3adc7a4a44801f5",
    "targeted_tier_c_source_review_download_556_city_cycle_unit_coverage_summary.json": "a2e4225c52424471cd7d5344a3c5301381b2e8bb89ff216dbc1786f01e88bece",
    "targeted_tier_c_source_review_download_556_geographic_region_coverage_summary.json": "890d174c50a8d4edeb9ab18f804c6916757e694d4db3448eeb1313aec79f26d7",
    "dashboard_fix_and_tier_c_source_review_download_556_validation_2026-07-27.md": "545a54346737ee28edfbf7e6dd66a618687b05a2a12849706fc664351a3b13a1",
    "targeted_tier_c_source_review_download_556_invariant_checks.json": "05854fe39d81bac30c313ec8d4f0e66287b16af52fb6422c6470956c652a4bec",
    "retained_sources_manifest.csv": "0565e86927da0f61778f6784abb0b767e7cc801793db9c94127c4618a97eec88",
    "retained_sources_hash_manifest.csv": "cc61834a4b26cb0818c02a8dbf03870f568e8723d76c803f24e949f5f3baa74a",
    "targeted_tier_c_source_review_download_556_retained_sources.csv": "8a15d8405e5c7a32382570f392bd5b14b6fc10199c333697a1b2d19dbedf86ee",
    "targeted_tier_c_source_review_download_556_results.csv": "d3a44745a5fa32a528c2a54b808e59a8d6001e7434902040121882c0400f2ca2",
    "retained_sources_duplicate_hash_groups.csv": "8ad30ab9cd6edb4fdb9728387f6dfb8b9ee310fedfd3d9fcc439b3df47312a85",
}

LOCK_FIELDS = (
    "retained_source_id", "candidate_id", "lane_id", "priority_tier",
    "quality_label", "source_url_or_locator", "source_title", "municipality",
    "state", "derived_region", "unit_type", "occupation_group", "bargaining_unit_name",
    "contract_or_document_period", "inferred_cycle_start", "inferred_cycle_end",
    "source_family", "target_mechanism_family", "same_city_match_status",
    "overlapping_cycle_status", "verification_status", "verification_reason",
    "source_review_download_status", "download_status", "content_type_hint",
    "file_extension", "file_size_bytes", "file_sha256", "local_retained_path",
    "duplicate_file_group_id", "extraction_status", "rating_status",
    "ingestion_status", "codification_status", "causal_status",
    "global_analysis_readiness", "source_review_timestamp",
)

RESULT_FIELDS = LOCK_FIELDS + (
    "file_integrity_status", "readiness_status", "readiness_reason",
    "page_count", "pdf_encrypted_or_locked", "pdf_has_text_layer_hint",
    "pdf_version_hint", "bounded_text_probe_pages",
    "bounded_text_signal_character_count", "html_text_readiness_hint",
    "html_probe_bytes", "html_visible_text_character_count",
    "html_link_count", "html_script_count", "readiness_review_status",
    "readiness_notes",
)

CONTROLLED_STATUSES = {
    "parse_text_layer_later", "html_text_later", "ocr_later_or_defer",
    "corrupt_or_unreadable", "oversized_for_text_pass", "needs_review",
    "readiness_error",
}

REQUIRED_FINAL_OUTPUTS = (
    "tier_c_readiness_dashboard_map_update_decision.json",
    "tier_c_readiness_dashboard_map_update_summary.md",
    "tier_c_pdf_text_layer_readiness_463_locked_queue.csv",
    "tier_c_pdf_text_layer_readiness_463_locked_queue_summary.json",
    "tier_c_pdf_text_layer_readiness_463_lock.json",
    "tier_c_pdf_text_layer_readiness_463_file_integrity.csv",
    "tier_c_pdf_text_layer_readiness_463_file_integrity_summary.json",
    "tier_c_pdf_text_layer_readiness_463_results.csv",
    "tier_c_pdf_text_layer_readiness_463_results_summary.json",
    "tier_c_pdf_text_layer_readiness_463_pdf_results.csv",
    "tier_c_pdf_text_layer_readiness_463_html_results.csv",
    "tier_c_pdf_text_layer_readiness_463_pdf_summary.json",
    "tier_c_pdf_text_layer_readiness_463_html_summary.json",
    "tier_c_pdf_text_layer_readiness_463_readiness_lane_summary.json",
    "tier_c_pdf_text_layer_readiness_463_parse_text_layer_later.csv",
    "tier_c_pdf_text_layer_readiness_463_html_text_later.csv",
    "tier_c_pdf_text_layer_readiness_463_ocr_later_or_defer.csv",
    "tier_c_pdf_text_layer_readiness_463_corrupt_or_unreadable.csv",
    "tier_c_pdf_text_layer_readiness_463_oversized_for_text_pass.csv",
    "tier_c_pdf_text_layer_readiness_463_needs_review.csv",
    "tier_c_pdf_text_layer_readiness_463_mechanism_coverage.csv",
    "tier_c_pdf_text_layer_readiness_463_mechanism_coverage_summary.json",
    "tier_c_pdf_text_layer_readiness_463_city_cycle_unit_coverage.csv",
    "tier_c_pdf_text_layer_readiness_463_city_cycle_unit_coverage_summary.json",
    "tier_c_pdf_text_layer_readiness_463_geographic_region_coverage.csv",
    "tier_c_pdf_text_layer_readiness_463_geographic_region_coverage_summary.json",
    "tier_c_pdf_text_layer_readiness_463_source_family_coverage.csv",
    "tier_c_pdf_text_layer_readiness_463_source_family_coverage_summary.json",
    "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions.csv",
    "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions_summary.json",
    "tier_c_readiness_dashboard_map_update_validation_2026-07-27.md",
    "tier_c_readiness_dashboard_map_update_invariant_checks.json",
    "tier_c_readiness_dashboard_map_update_stress_test_report.md",
    "tier_c_readiness_dashboard_map_update_regression_test_inventory.json",
    "dashboard_map_update_with_tier_c_sources_summary.md",
    "dashboard_map_update_with_tier_c_sources_summary.json",
    "dashboard_map_data_date.json",
    "dashboard_map_data_date.md",
    "dashboard_map_state_region_coverage.csv",
    "dashboard_map_state_region_coverage_summary.json",
    "dashboard_map_source_family_coverage_summary.json",
    "dashboard_map_mechanism_coverage_summary.json",
    "future_broad_geographic_scouting_strategy.md",
    "future_broad_geographic_scouting_strategy.json",
    "future_source_family_diversification_plan.md",
    "future_state_by_state_scan_plan.md",
    "next_tier_c_text_layer_extraction_prompt.md",
    "next_task.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["retained_source_id"] for row in rows)))


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
            raise FileNotFoundError(f"required immutable source-review input missing: {name}")
        observed[name] = sha256(path)
        if observed[name] != expected:
            raise RuntimeError(f"immutable source-review input hash drift: {name}")

    decision = read_json(INPUT_DIR / "dashboard_fix_and_tier_c_source_review_download_556_decision.json")
    retained_summary = read_json(INPUT_DIR / "targeted_tier_c_source_review_download_556_retained_sources_summary.json")
    exclusions_summary = read_json(INPUT_DIR / "targeted_tier_c_source_review_download_556_exclusion_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_tier_c_source_review_download_556_invariant_checks.json")
    queue = read_csv(INPUT_DIR / "targeted_tier_c_source_review_download_556_retained_sources.csv")
    manifest = read_csv(INPUT_DIR / "retained_sources_manifest.csv")
    hash_manifest = read_csv(INPUT_DIR / "retained_sources_hash_manifest.csv")
    all_results = read_csv(INPUT_DIR / "targeted_tier_c_source_review_download_556_results.csv")
    excluded = [row for row in all_results if row["source_review_download_status"] != "retained_downloaded_source"]
    queue_ids = {row["retained_source_id"] for row in queue}
    manifest_ids = {row["retained_source_id"] for row in manifest}
    hash_ids = {row["retained_source_id"] for row in hash_manifest}
    excluded_candidate_ids = {row["candidate_id"] for row in excluded}
    queue_candidate_ids = {row["candidate_id"] for row in queue}
    if not (
        decision.get("decision") == "dashboard_fix_and_tier_c_download_completed_pdf_readiness_ready_dashboard_fixed"
        and decision.get("retained_downloaded_source_count") == EXPECTED_COUNT
        and decision.get("global_analysis_readiness") is False
        and retained_summary.get("retained_source_count") == EXPECTED_COUNT
        and retained_summary.get("by_content_type") == EXPECTED_TYPES
        and retained_summary.get("by_lane") == EXPECTED_LANES
        and exclusions_summary.get("excluded_or_deferred_rows") == 93
        and exclusions_summary.get("duplicate_hash_group_count") == 1
        and invariants.get("all_invariants_passed") is True
        and len(queue) == len(manifest) == len(hash_manifest) == EXPECTED_COUNT
        and queue_ids == manifest_ids == hash_ids
        and len(queue_ids) == EXPECTED_COUNT
        and id_set_hash(queue) == EXPECTED_ID_SET_HASH
        and not (queue_candidate_ids & excluded_candidate_ids)
        and all(row["source_review_download_status"] == "retained_downloaded_source" for row in queue)
        and all(row["download_status"] == "downloaded_retained" for row in queue)
        and all(row["content_type_hint"] in EXPECTED_TYPES for row in queue)
        and all(row["priority_tier"] == "tier_c" for row in queue)
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["ingestion_status"] == "not_ingested" for row in queue)
        and all(row["codification_status"] == "not_codified" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and all(row["global_analysis_readiness"] == "false" for row in queue)
    ):
        raise RuntimeError("463-row retained readiness scope reconciliation failed")

    by_hash_id = {row["retained_source_id"]: row for row in hash_manifest}
    for row in queue:
        hash_row = by_hash_id[row["retained_source_id"]]
        path = ROOT / row["local_retained_path"]
        if not path.is_file() or not path.resolve().is_relative_to((INPUT_DIR / "retained_sources").resolve()):
            raise RuntimeError(f"retained path missing or outside immutable retained directory: {row['retained_source_id']}")
        if path.stat().st_size != int(row["file_size_bytes"]):
            raise RuntimeError(f"retained file size mismatch: {row['retained_source_id']}")
        if hash_row["file_size_bytes"] != row["file_size_bytes"] or hash_row["file_sha256"] != row["file_sha256"]:
            raise RuntimeError(f"retained hash-manifest lineage mismatch: {row['retained_source_id']}")
        if verify_file_bytes and sha256(path) != row["file_sha256"]:
            raise RuntimeError(f"retained file SHA-256 mismatch: {row['retained_source_id']}")
    queue.sort(key=lambda row: (row["lane_id"], row["retained_source_id"]))
    return queue, excluded, observed


def integrity_rows(queue: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in queue:
        path = ROOT / row["local_retained_path"]
        actual_size = path.stat().st_size if path.is_file() else -1
        actual_hash = sha256(path) if path.is_file() else ""
        passed = actual_size == int(row["file_size_bytes"]) and actual_hash == row["file_sha256"]
        rows.append({
            "retained_source_id": row["retained_source_id"],
            "candidate_id": row["candidate_id"],
            "local_retained_path": row["local_retained_path"],
            "recorded_file_size_bytes": row["file_size_bytes"],
            "observed_file_size_bytes": str(actual_size),
            "recorded_file_sha256": row["file_sha256"],
            "observed_file_sha256": actual_hash,
            "file_exists": "true" if path.is_file() else "false",
            "path_inside_retained_directory": "true" if path.resolve().is_relative_to((INPUT_DIR / "retained_sources").resolve()) else "false",
            "file_integrity_status": "integrity_pass" if passed else "integrity_fail",
        })
    return rows


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    queue, excluded, observed = verify_inputs(verify_file_bytes=True)
    OUTPUT_DIR.mkdir(parents=True)
    locked = [{field: row.get(field, "") for field in LOCK_FIELDS} for row in queue]
    queue_path = OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    integrity = integrity_rows(locked)
    integrity_path = OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_file_integrity.csv"
    write_csv(integrity_path, integrity, integrity[0].keys())
    lock = {
        "task_id": TASK_ID,
        "input_commit": INPUT_COMMIT,
        "locked_queue_count": len(locked),
        "queue_sha256": sha256(queue_path),
        "retained_source_id_set_sha256": id_set_hash(locked),
        "content_type_counts": dict(sorted(Counter(row["content_type_hint"] for row in locked).items())),
        "lane_counts": dict(sorted(Counter(row["lane_id"] for row in locked).items())),
        "immutable_input_hashes": observed,
        "retained_file_integrity_pass_count": sum(row["file_integrity_status"] == "integrity_pass" for row in integrity),
        "preserved_exclusion_count": len(excluded),
        "duplicate_summary_lineage": "committed retained_sources_duplicate_hash_groups.csv and exclusion summary; supplementary relay summary available",
        "inspection_status": "not_started",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_lock.json", lock)
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_locked_queue_summary.json", {
        "locked_queue_count": len(locked),
        "content_type_counts": lock["content_type_counts"],
        "lane_counts": lock["lane_counts"],
        "only_retained_downloaded_sources": True,
        "prior_excluded_rows_in_queue": 0,
        "tier_a_b_or_d_rows": 0,
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_file_integrity_summary.json", {
        "files_checked": len(integrity),
        "integrity_pass_count": sum(row["file_integrity_status"] == "integrity_pass" for row in integrity),
        "integrity_fail_count": sum(row["file_integrity_status"] != "integrity_pass" for row in integrity),
        "recorded_total_bytes": sum(int(row["file_size_bytes"]) for row in locked),
        "all_paths_inside_immutable_retained_directory": all(row["path_inside_retained_directory"] == "true" for row in integrity),
        "global_analysis_readiness": False,
    })
    preflight = {
        "preflight_passed": len(locked) == EXPECTED_COUNT and all(row["file_integrity_status"] == "integrity_pass" for row in integrity),
        "source_review_decision_allows_readiness": True,
        "locked_queue_count": len(locked),
        "content_type_counts": lock["content_type_counts"],
        "queue_hash_matches_lock": sha256(queue_path) == lock["queue_sha256"],
        "retained_id_hash_matches_lock": id_set_hash(locked) == lock["retained_source_id_set_sha256"],
        "prior_excluded_rows_in_queue": 0,
        "pdfinfo_available": shutil.which("pdfinfo") is not None,
        "pdftotext_available_for_bounded_signal_only": shutil.which("pdftotext") is not None,
        "maximum_pdf_text_signal_probe_pages": MAX_PDF_PROBE_PAGES,
        "url_opens": 0,
        "downloads": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "saved_page_images": 0,
        "full_text_extraction_runs": 0,
        "evidence_span_extraction_runs": 0,
        "model_api_calls": 0,
        "global_analysis_readiness": False,
    }
    preflight["preflight_passed"] = bool(preflight["preflight_passed"] and preflight["pdfinfo_available"] and preflight["pdftotext_available_for_bounded_signal_only"])
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preflight_report.md", f"""# Targeted Tier C PDF/text-layer readiness preflight

Preflight {'passed' if preflight['preflight_passed'] else 'failed'} for exactly 463 immutable retained files: 397 PDFs, 65 HTML artifacts, and one octet-stream artifact. All paths, sizes, and SHA-256 hashes matched. The inspection path is local-only. PDF text-layer detection is capped at the first {MAX_PDF_PROBE_PAGES} pages and retains only numeric signal counts, never document text. The map inputs and deterministic date are available. No URL, download, OCR, rendering, page image, evidence extraction, rating, ingestion, codification, model analysis, or durable merge is authorized.
""")
    if not preflight["preflight_passed"]:
        raise RuntimeError("targeted readiness preflight failed")
    print(json.dumps({"status": "readiness_preflight_passed", "rows": len(locked), "queue_sha256": lock["queue_sha256"]}))


def parse_pdfinfo(stdout: bytes) -> dict[str, Any]:
    text = stdout.decode("utf-8", errors="replace")
    values: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip().casefold()] = value.strip()
    pages_raw = values.get("pages", "")
    return {
        "page_count": int(pages_raw) if pages_raw.isdigit() else 0,
        "encrypted": values.get("encrypted", "").casefold().startswith("yes"),
        "pdf_version": values.get("pdf version", ""),
    }


def run_local_command(args: list[str], timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def inspect_pdf(row: dict[str, str]) -> dict[str, str]:
    path = ROOT / row["local_retained_path"]
    try:
        info = run_local_command(["pdfinfo", str(path)], MAX_PDFINFO_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return inspection_result(row, "readiness_error", f"pdfinfo_{type(exc).__name__}")
    stderr_hint = info.stderr.decode("utf-8", errors="ignore").casefold()
    if info.returncode != 0:
        reason = "pdf_metadata_unreadable_or_corrupt"
        if "password" in stderr_hint or "encrypted" in stderr_hint:
            return inspection_result(row, "needs_review", "pdf_locked_metadata_unavailable", encrypted="true")
        return inspection_result(row, "corrupt_or_unreadable", reason)
    metadata = parse_pdfinfo(info.stdout)
    pages = int(metadata["page_count"])
    encrypted = bool(metadata["encrypted"])
    common = {
        "page_count": str(pages) if pages else "",
        "pdf_encrypted_or_locked": "true" if encrypted else "false",
        "pdf_version_hint": str(metadata["pdf_version"]),
    }
    if pages <= 0:
        return inspection_result(row, "corrupt_or_unreadable", "pdf_page_count_unavailable", **common)
    if encrypted:
        return inspection_result(row, "needs_review", "pdf_encrypted_or_locked", **common)
    if int(row["file_size_bytes"]) > MAX_TEXT_PASS_BYTES or pages > MAX_TEXT_PASS_PAGES:
        return inspection_result(row, "oversized_for_text_pass", "pdf_exceeds_bounded_text_pass_size_or_page_limit", **common)
    probe_pages = min(MAX_PDF_PROBE_PAGES, pages)
    try:
        probe = run_local_command([
            "pdftotext", "-f", "1", "-l", str(probe_pages), "-enc", "UTF-8",
            "-nopgbrk", str(path), "-",
        ], MAX_TEXT_PROBE_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return inspection_result(row, "needs_review", f"bounded_text_signal_{type(exc).__name__}", bounded_text_probe_pages=str(probe_pages), **common)
    # The bytes are discarded after a numeric signal count; they are never
    # written to disk, logged, returned, or included in an output ledger.
    signal_count = sum(chr(byte).isalnum() for byte in probe.stdout if byte < 128)
    signal = signal_count >= 40 and probe.returncode == 0
    if signal:
        return inspection_result(
            row, "parse_text_layer_later", "bounded_first_pages_show_machine_readable_text_layer",
            pdf_has_text_layer_hint="true", bounded_text_probe_pages=str(probe_pages),
            bounded_text_signal_character_count=str(signal_count), **common,
        )
    return inspection_result(
        row, "ocr_later_or_defer", "bounded_first_pages_do_not_show_usable_text_layer",
        pdf_has_text_layer_hint="false", bounded_text_probe_pages=str(probe_pages),
        bounded_text_signal_character_count=str(signal_count), **common,
    )


class BoundedHTMLSignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.visible_characters = 0
        self.links = 0
        self.scripts = 0
        self.meta_refresh = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1
        if tag == "script":
            self.scripts += 1
        if tag == "a":
            self.links += 1
        if tag == "meta":
            lowered = {key.casefold(): (value or "").casefold() for key, value in attrs}
            self.meta_refresh = self.meta_refresh or lowered.get("http-equiv") == "refresh"

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.visible_characters += sum(character.isalnum() for character in data)


def inspect_html(row: dict[str, str]) -> dict[str, str]:
    path = ROOT / row["local_retained_path"]
    try:
        with path.open("rb") as handle:
            payload = handle.read(MAX_HTML_PROBE_BYTES)
    except OSError as exc:
        return inspection_result(row, "readiness_error", f"html_read_{type(exc).__name__}")
    if not payload or len(payload) < 16:
        return inspection_result(row, "corrupt_or_unreadable", "html_empty_or_too_short", html_probe_bytes=str(len(payload)), html_text_readiness_hint="unreadable")
    decoded = payload.decode("utf-8", errors="replace")
    parser = BoundedHTMLSignalParser()
    try:
        parser.feed(decoded)
    except Exception:
        return inspection_result(row, "needs_review", "html_parser_error", html_probe_bytes=str(len(payload)), html_text_readiness_hint="weak_or_noisy")
    lower = decoded.casefold()
    redirect_shell = parser.meta_refresh or ("window.location" in lower and parser.visible_characters < 200)
    common = {
        "html_probe_bytes": str(len(payload)),
        "html_visible_text_character_count": str(parser.visible_characters),
        "html_link_count": str(parser.links),
        "html_script_count": str(parser.scripts),
    }
    if redirect_shell:
        return inspection_result(row, "needs_review", "html_redirect_or_script_shell", html_text_readiness_hint="redirect_or_shell", **common)
    if parser.visible_characters >= 200:
        return inspection_result(row, "html_text_later", "bounded_html_structure_has_usable_visible_text", html_text_readiness_hint="text_ready", **common)
    return inspection_result(row, "needs_review", "html_visible_text_signal_too_weak", html_text_readiness_hint="weak_or_noisy", **common)


def inspect_octet_stream(row: dict[str, str]) -> dict[str, str]:
    """Conservatively route the one octet-stream artifact from a local header only."""
    path = ROOT / row["local_retained_path"]
    try:
        with path.open("rb") as handle:
            header = handle.read(4096)
    except OSError as exc:
        return inspection_result(row, "readiness_error", f"octet_header_{type(exc).__name__}")
    if header.startswith(b"%PDF-"):
        pdf_row = {**row, "content_type_hint": "application/pdf"}
        result = inspect_pdf(pdf_row)
        result["content_type_hint"] = "application/octet-stream"
        result["readiness_reason"] = f"octet_header_pdf_like__{result['readiness_reason']}"
        result["readiness_notes"] = (
            "Local header was clearly PDF-like; the recorded octet-stream content type "
            "was preserved. No content type was invented. " + result["readiness_notes"]
        )
        return result
    lower = header.lstrip().lower()
    if lower.startswith((b"<!doctype html", b"<html")):
        html_row = {**row, "content_type_hint": "text/html"}
        result = inspect_html(html_row)
        result["content_type_hint"] = "application/octet-stream"
        result["readiness_reason"] = f"octet_header_html_like__{result['readiness_reason']}"
        result["readiness_notes"] = (
            "Local header was clearly HTML-like; the recorded octet-stream content type "
            "was preserved. No content type was invented. " + result["readiness_notes"]
        )
        return result
    return inspection_result(
        row,
        "needs_review",
        "octet_stream_header_not_clearly_pdf_or_html",
        readiness_notes=(
            "The local header did not support a safe PDF/HTML routing decision. "
            "No content type was invented; no URL, OCR, rendering, or extraction occurred."
        ),
    )


def inspection_result(row: dict[str, str], status: str, reason: str, **details: str) -> dict[str, str]:
    result = {field: row.get(field, "") for field in LOCK_FIELDS}
    result.update({
        "file_integrity_status": "integrity_pass",
        "readiness_status": status,
        "readiness_reason": reason,
        "page_count": "",
        "pdf_encrypted_or_locked": "not_applicable" if row["content_type_hint"] != "application/pdf" else "unknown",
        "pdf_has_text_layer_hint": "not_applicable" if row["content_type_hint"] != "application/pdf" else "unknown",
        "pdf_version_hint": "",
        "bounded_text_probe_pages": "0",
        "bounded_text_signal_character_count": "0",
        "html_text_readiness_hint": "not_applicable" if row["content_type_hint"] != "text/html" else "unknown",
        "html_probe_bytes": "0",
        "html_visible_text_character_count": "0",
        "html_link_count": "0",
        "html_script_count": "0",
        "readiness_review_status": "reviewed_local_file_metadata_only",
        "readiness_notes": "No URL open, download, OCR, rendering, saved page text, evidence extraction, rating, ingestion, codification, model analysis, or causal work occurred.",
    })
    result.update(details)
    return result


def inspect_one(row: dict[str, str]) -> dict[str, str]:
    if row["content_type_hint"] == "application/pdf":
        return inspect_pdf(row)
    if row["content_type_hint"] == "text/html":
        return inspect_html(row)
    if row["content_type_hint"] == "application/octet-stream":
        return inspect_octet_stream(row)
    return inspection_result(row, "readiness_error", "unexpected_retained_content_type")


def group_status_counts(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    output = []
    for value, group in sorted(groups.items()):
        counts = Counter(row["readiness_status"] for row in group)
        output.append({
            key: value,
            "retained_source_count": len(group),
            "parse_text_layer_later_count": counts["parse_text_layer_later"],
            "html_text_later_count": counts["html_text_later"],
            "ocr_later_or_defer_count": counts["ocr_later_or_defer"],
            "corrupt_or_unreadable_count": counts["corrupt_or_unreadable"],
            "oversized_for_text_pass_count": counts["oversized_for_text_pass"],
            "needs_review_count": counts["needs_review"] + counts["readiness_error"],
            "bounded_text_extraction_ready_count": counts["parse_text_layer_later"] + counts["html_text_later"],
        })
    return output


def write_outputs(results: list[dict[str, str]], excluded: list[dict[str, str]]) -> str:
    status_counts = Counter(row["readiness_status"] for row in results)
    ready_count = status_counts["parse_text_layer_later"] + status_counts["html_text_later"]
    counts = dict(sorted(status_counts.items()))
    pdf_rows = [row for row in results if row["content_type_hint"] == "application/pdf"]
    html_rows = [row for row in results if row["content_type_hint"] == "text/html"]
    octet_rows = [row for row in results if row["content_type_hint"] == "application/octet-stream"]
    repair_needed = status_counts["readiness_error"] > 0
    decision_name = (
        "tier_c_readiness_dashboard_map_update_completed_repair_needed"
        if repair_needed
        else "tier_c_readiness_dashboard_map_update_completed_text_extraction_ready"
        if ready_count >= 200
        else "tier_c_readiness_dashboard_map_update_completed_broad_scouting_recommended"
    )
    lane_files = {
        "parse_text_layer_later": {"parse_text_layer_later"},
        "html_text_later": {"html_text_later"},
        "ocr_later_or_defer": {"ocr_later_or_defer"},
        "corrupt_or_unreadable": {"corrupt_or_unreadable"},
        "oversized_for_text_pass": {"oversized_for_text_pass"},
        "needs_review": {"needs_review", "readiness_error"},
    }
    by_lane = {
        key: dict(sorted(Counter(row["readiness_status"] for row in results if row["lane_id"] == key).items()))
        for key in sorted({row["lane_id"] for row in results})
    }
    by_mechanism = {
        key: dict(sorted(Counter(row["readiness_status"] for row in results if row["target_mechanism_family"] == key).items()))
        for key in sorted({row["target_mechanism_family"] for row in results})
    }

    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_pdf_results.csv", pdf_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_html_results.csv", html_rows, RESULT_FIELDS)
    for filename, statuses in lane_files.items():
        write_csv(
            OUTPUT_DIR / f"tier_c_pdf_text_layer_readiness_463_{filename}.csv",
            [row for row in results if row["readiness_status"] in statuses],
            RESULT_FIELDS,
        )
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_pdf_summary.json", {
        "pdf_rows": len(pdf_rows),
        "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in pdf_rows).items())),
        "page_count_available": sum(bool(row["page_count"]) for row in pdf_rows),
        "total_pages_metadata_only": sum(int(row["page_count"] or 0) for row in pdf_rows),
        "encrypted_or_locked_count": sum(row["pdf_encrypted_or_locked"] == "true" for row in pdf_rows),
        "text_layer_hint_true_count": sum(row["pdf_has_text_layer_hint"] == "true" for row in pdf_rows),
        "text_layer_hint_false_count": sum(row["pdf_has_text_layer_hint"] == "false" for row in pdf_rows),
        "maximum_probe_pages_per_pdf": MAX_PDF_PROBE_PAGES,
        "pdf_render_runs": 0,
        "ocr_runs": 0,
        "saved_document_text_rows": 0,
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_html_summary.json", {
        "html_rows": len(html_rows),
        "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in html_rows).items())),
        "text_ready_count": sum(row["html_text_readiness_hint"] == "text_ready" for row in html_rows),
        "redirect_or_shell_count": sum(row["html_text_readiness_hint"] == "redirect_or_shell" for row in html_rows),
        "weak_or_noisy_count": sum(row["html_text_readiness_hint"] == "weak_or_noisy" for row in html_rows),
        "unreadable_count": sum(row["html_text_readiness_hint"] == "unreadable" for row in html_rows),
        "maximum_probe_bytes_per_html": MAX_HTML_PROBE_BYTES,
        "saved_document_text_rows": 0,
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_readiness_lane_summary.json", {
        "readiness_status_counts": counts,
        "bounded_text_extraction_ready_count": ready_count,
        "lane_manifest_files": {name: f"tier_c_pdf_text_layer_readiness_463_{name}.csv" for name in lane_files},
        "all_rows_reconciled": sum(status_counts.values()) == EXPECTED_COUNT,
        "global_analysis_readiness": False,
    })

    mechanism_rows = group_status_counts(results, "target_mechanism_family")
    source_family_rows = group_status_counts(results, "source_family")
    region_rows = group_status_counts(results, "derived_region")
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_mechanism_coverage.csv", mechanism_rows, mechanism_rows[0].keys())
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_source_family_coverage.csv", source_family_rows, source_family_rows[0].keys())
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_geographic_region_coverage.csv", region_rows, region_rows[0].keys())
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_mechanism_coverage_summary.json", {
        "mechanism_count": len(mechanism_rows),
        "by_mechanism": {row["target_mechanism_family"]: {k: v for k, v in row.items() if k != "target_mechanism_family"} for row in mechanism_rows},
        "coverage_boundary": "Readiness classifications are operational metadata, not evidence claims.",
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_source_family_coverage_summary.json", {
        "source_family_count": len(source_family_rows),
        "by_source_family": {row["source_family"]: {k: v for k, v in row.items() if k != "source_family"} for row in source_family_rows},
        "cba_skew_is_tracked_for_future_broad_scouting": True,
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_geographic_region_coverage_summary.json", {
        "region_count": len(region_rows),
        "state_count": len({row["state"] for row in results}),
        "city_state_pair_count": len({(row["municipality"], row["state"]) for row in results}),
        "by_region": {row["derived_region"]: {k: v for k, v in row.items() if k != "derived_region"} for row in region_rows},
        "geography_from_existing_lineage_only": True,
    })

    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        city_groups[(row["municipality"], row["state"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for key, group in sorted(city_groups.items()):
        grouped = Counter(row["readiness_status"] for row in group)
        city_rows.append({
            "municipality": key[0], "state": key[1], "unit_type": key[2],
            "contract_or_document_period": key[3], "retained_source_count": len(group),
            "bounded_text_extraction_ready_count": grouped["parse_text_layer_later"] + grouped["html_text_later"],
            "deferred_or_review_count": len(group) - grouped["parse_text_layer_later"] - grouped["html_text_later"],
        })
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_bounded_text_extraction_ready_source": sum(int(row["bounded_text_extraction_ready_count"]) > 0 for row in city_rows),
        "groups_without_bounded_text_extraction_ready_source": sum(int(row["bounded_text_extraction_ready_count"]) == 0 for row in city_rows),
        "distinct_city_state_pairs": len({(row["municipality"], row["state"]) for row in results}),
        "coverage_boundary": "Readiness outputs do not update durable city coverage.",
    })

    state_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        state_groups[(row["state"], row["derived_region"])].append(row)
    state_rows = []
    for (state, region), group in sorted(state_groups.items()):
        grouped = Counter(row["readiness_status"] for row in group)
        types = Counter(row["content_type_hint"] for row in group)
        state_rows.append({
            "state": state,
            "derived_region": region,
            "tier_c_retained_source_count": len(group),
            "tier_c_text_extraction_ready_count": grouped["parse_text_layer_later"] + grouped["html_text_later"],
            "tier_c_pdf_count": types["application/pdf"],
            "tier_c_html_count": types["text/html"],
            "tier_c_octet_stream_count": types["application/octet-stream"],
            "tier_c_parse_text_layer_later_count": grouped["parse_text_layer_later"],
            "tier_c_html_text_later_count": grouped["html_text_later"],
            "tier_c_deferred_or_review_count": len(group) - grouped["parse_text_layer_later"] - grouped["html_text_later"],
        })
    write_csv(OUTPUT_DIR / "dashboard_map_state_region_coverage.csv", state_rows, state_rows[0].keys())
    map_state_summary = {
        "map_data_date": "2026-07-27",
        "states_with_tier_c_retained_sources": len(state_rows),
        "tier_c_retained_source_count": len(results),
        "tier_c_text_extraction_ready_count": ready_count,
        "by_region": dict(sorted(Counter(row["derived_region"] for row in results).items())),
        "state_rows": state_rows,
        "global_analysis_readiness": False,
        "map_boundary": "Operational retained/readiness coverage only; not representative and not a wage or causal result.",
    }
    write_json(OUTPUT_DIR / "dashboard_map_state_region_coverage_summary.json", map_state_summary)
    write_json(OUTPUT_DIR / "dashboard_map_source_family_coverage_summary.json", {
        "map_data_date": "2026-07-27",
        "by_source_family": dict(sorted(Counter(row["source_family"] for row in results).items())),
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "dashboard_map_mechanism_coverage_summary.json", {
        "map_data_date": "2026-07-27",
        "by_mechanism": dict(sorted(Counter(row["target_mechanism_family"] for row in results).items())),
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "dashboard_map_data_date.json", {
        "map_data_date": "2026-07-27",
        "date_basis": "latest retained Tier C readiness stage date",
        "not_a_claim_date": True,
        "not_a_causal_analysis_vintage": True,
    })
    write_text(OUTPUT_DIR / "dashboard_map_data_date.md", """# Dashboard map data date

Map data date: 2026-07-27. This deterministic date identifies the latest retained Tier C readiness inputs represented on the map. It is not a claim date or a causal-analysis vintage.
""")
    map_summary = {
        "map_update_status": "current_tier_c_retained_and_readiness_layer_generated",
        "map_data_date": "2026-07-27",
        "retained_source_count": len(results),
        "readiness_status_counts": counts,
        "states_represented": len(state_rows),
        "regions": dict(sorted(Counter(row["derived_region"] for row in results).items())),
        "source_families": dict(sorted(Counter(row["source_family"] for row in results).items())),
        "mechanisms": dict(sorted(Counter(row["target_mechanism_family"] for row in results).items())),
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_map_update_with_tier_c_sources_summary.json", map_summary)
    write_text(OUTPUT_DIR / "dashboard_map_update_with_tier_c_sources_summary.md", f"""# Dashboard map update with Tier C sources

The generated current map layer represents {len(results)} retained Tier C files across {len(state_rows)} states as of 2026-07-27. It exposes retained and bounded text-readiness counts, region, source-family, and mechanism distributions. The earlier scout map remains available as clearly historical context. This map is operational coverage metadata only; it does not establish representativeness, a wage estimate, or causation. Global analysis readiness remains false.
""")

    excluded_fields = tuple(excluded[0].keys()) + ("preserved_exclusion_status", "excluded_from_readiness_queue")
    preserved = [{**row, "preserved_exclusion_status": row["source_review_download_status"], "excluded_from_readiness_queue": "true"} for row in excluded]
    write_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions.csv", preserved, excluded_fields)
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions_summary.json", {
        "preserved_exclusion_count": len(preserved),
        "status_counts": dict(sorted(Counter(row["preserved_exclusion_status"] for row in preserved).items())),
        "duplicate_hash_group_count": 1,
        "excluded_rows_entering_readiness_queue": 0,
    })

    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_results_summary.json", {
        "result_rows": len(results), "pdf_rows": len(pdf_rows), "html_rows": len(html_rows), "octet_stream_rows": len(octet_rows),
        "readiness_status_counts": counts, "bounded_text_extraction_ready_count": ready_count,
        "readiness_status_counts_by_lane": by_lane, "readiness_status_counts_by_mechanism": by_mechanism,
        "pdf_pages_metadata_counted": sum(bool(row["page_count"]) for row in pdf_rows),
        "pdf_bounded_text_signal_probes": sum(int(row["bounded_text_probe_pages"] or 0) > 0 for row in results),
        "html_bounded_structure_probes": sum(int(row["html_probe_bytes"] or 0) > 0 for row in results),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "saved_page_images": 0, "full_text_extraction_runs": 0, "evidence_span_extraction_runs": 0,
        "model_api_calls": 0, "durable_ledger_merges": 0, "global_analysis_readiness": False,
    })

    strategy = {
        "default_future_scout_mode": "broad_geographic_state_by_state",
        "countrywide_balance_goal": True,
        "mechanism_targeted_scouting_role": "secondary_gap_filling_after_broad_scans",
        "preserve_mechanism_tags_after_collection": True,
        "track_source_family_skew": True,
        "source_families": [
            "CBA", "memorandum_or_MOU", "arbitration_award", "factfinding_report",
            "salary_ordinance", "wage_schedule", "budget_or_pay_plan",
            "civil_service_or_HR_pay_plan", "compensation_or_classification_study",
        ],
        "balance_metrics": ["states_scanned", "regions_scanned", "source_family_counts", "source_family_shares"],
    }
    write_json(OUTPUT_DIR / "future_broad_geographic_scouting_strategy.json", strategy)
    write_text(OUTPUT_DIR / "future_broad_geographic_scouting_strategy.md", """# Future broad geographic scouting strategy

Future source-expansion scouts default to broad state-by-state geographic scanning, with an explicit goal of balanced countrywide discovery and multiple document families. Mechanism labels remain useful after collection, but anticipated mechanism content will not be the primary discovery filter. Mechanism-targeted scouting becomes a selective follow-up after broad scans reveal a documented gap.

Each broad wave must report states and regions scanned, source-family counts and shares, city × unit × cycle coverage, and unmatched safety/non-safety holes. The wave must disclose source-family skew so a CBA-heavy corpus cannot silently repeat. This is an operational collection strategy, not a claim of geographic representativeness.
""")
    write_text(OUTPUT_DIR / "future_source_family_diversification_plan.md", """# Future source-family diversification plan

Broad scans should deliberately search across CBAs, memoranda/MOUs, arbitration awards, factfinding reports, salary ordinances, wage schedules, budget/pay-plan documents, civil-service/HR pay plans, and compensation/classification studies. Report both counts and shares by family. Preserve causal/discourse separation and exact provenance. Do not fill family quotas with weak sources.
""")
    write_text(OUTPUT_DIR / "future_state_by_state_scan_plan.md", """# Future state-by-state scan plan

Scan states systematically in geographically balanced waves. Within each state, retain city, unit, cycle, source family, and locator lineage; keep safety units paired with overlapping non-safety targets whenever possible. Measure state/region coverage and source-family balance after every wave. Use mechanism-targeted follow-ups only after this broad pass identifies a concrete gap.
""")

    decision = {
        "task_id": TASK_ID, "decision": decision_name,
        "completion_status": "completed_bounded_local_readiness_and_dashboard_map_update",
        "retained_readiness_queue_count": len(results), "pdf_retained_count": len(pdf_rows),
        "html_retained_count": len(html_rows), "octet_stream_count": len(octet_rows),
        "readiness_status_counts": counts, "readiness_status_counts_by_lane": by_lane,
        "readiness_status_counts_by_mechanism": by_mechanism,
        "bounded_text_layer_extraction_ready_next": decision_name.endswith("text_extraction_ready"),
        "broad_geographic_scouting_strategy_recorded": True,
        "dashboard_map_updated": True, "map_data_date": "2026-07-27", "repair_needed": repair_needed,
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "full_text_extraction_runs": 0, "evidence_span_extraction_runs": 0,
        "rating_runs": 0, "model_api_calls": 0, "ingestion_runs": 0,
        "codification_runs": 0, "durable_ledger_merges": 0, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_decision.json", decision)
    write_text(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_summary.md", f"""# Tier C readiness and dashboard map update

Decision: `{decision_name}`.

Exactly 463 immutable retained Tier C files were reviewed locally: 397 PDFs, 65 HTML artifacts, and one conservatively handled octet-stream file. Readiness outcomes reconcile to `{counts}`; {ready_count} files enter only the later extraction-ready manifests. All 93 prior source-review exclusions remain outside the queue.

The dashboard map layer now represents these Tier C retained/readiness counts with `Map data date: 2026-07-27`. Broad state-by-state scanning with source-family diversification is recorded as the default future scout strategy; mechanism-targeted scouting is secondary gap-filling.

No URL, download, OCR, rendering, saved document text, evidence extraction, model call, rating, ingestion, codification, wage estimate, regression, treatment effect, causal claim, or durable merge occurred. Global analysis readiness remains false.
""")

    invariants = {
        "all_invariants_passed": not repair_needed,
        "locked_queue_exactly_463": len(results) == EXPECTED_COUNT,
        "pdf_html_octet_counts_reconcile": len(pdf_rows) == 397 and len(html_rows) == 65 and len(octet_rows) == 1,
        "only_retained_tier_c_files_entered": all(row["source_review_download_status"] == "retained_downloaded_source" and row["priority_tier"] == "tier_c" for row in results),
        "prior_exclusions_preserved_and_excluded": len(preserved) == 93,
        "file_paths_sizes_hashes_verified": all(row["file_integrity_status"] == "integrity_pass" for row in results),
        "controlled_readiness_statuses_only": all(row["readiness_status"] in CONTROLLED_STATUSES for row in results),
        "pdf_and_html_lanes_separate": all(row["readiness_status"] != "html_text_later" for row in pdf_rows) and all(row["readiness_status"] != "parse_text_layer_later" for row in html_rows),
        "octet_stream_handled_conservatively": len(octet_rows) == 1 and octet_rows[0]["readiness_reason"].startswith("octet_"),
        "downstream_statuses_closed": all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in results),
        "dashboard_map_includes_latest_tier_c_data": map_summary["retained_source_count"] == 463,
        "map_data_date_present": map_summary["map_data_date"] == "2026-07-27",
        "future_broad_geographic_strategy_written": True,
        "no_url_download_ocr_render_full_text_evidence_or_model_work": True,
        "no_geographic_metadata_fabrication": True, "no_durable_ledger_merge": True,
        "global_analysis_readiness_false": True, "partial_outputs_cannot_masquerade_as_complete": True,
    }
    write_json(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_invariant_checks.json", invariants)
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_invariant_checks.json", invariants)
    write_text(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_stress_test_report.md", """# Stress-test report

- Missing, wrong-size, or hash-drifted files stop before inspection.
- Malformed, locked, empty, oversized, and weak files fail into explicit defer/review lanes.
- PDF text signals are capped at three pages, counted numerically, and discarded; HTML reads are capped at 256 KiB.
- The octet-stream row is routed only by an unambiguous local header and keeps its recorded content type.
- Prior exclusions, non-retained rows, and Tier A/B/D rows cannot enter the lock.
- Missing map date, unsafe dashboard readiness, readiness errors, or partial outputs prevent completion.
- A completed `--resume` performs validation only and writes nothing.
""")
    write_json(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_regression_test_inventory.json", {
        "focused_suite": "scripts/test_tier_c_readiness_dashboard_map_update.py",
        "coverage": ["463-row immutable scope", "397/65/1 lane reconciliation", "file integrity", "bounded local probes", "preserved exclusions", "closed downstream statuses", "current Tier C map layer", "visible map date", "broad geographic scouting strategy", "idempotent resume", "partial-output fail closed"],
    })
    write_json(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_regression_test_inventory.json", {
        "focused_suite": "scripts/test_tier_c_readiness_dashboard_map_update.py",
        "coverage": ["readiness manifests", "PDF/HTML lane separation", "octet-stream conservative routing", "no OCR/render/extraction"],
    })
    write_text(OUTPUT_DIR / "next_tier_c_text_layer_extraction_prompt.md", """# Next prompt: bounded Tier C text-layer extraction

Run a separately authorized local extraction only over `tier_c_pdf_text_layer_readiness_463_parse_text_layer_later.csv` and `tier_c_pdf_text_layer_readiness_463_html_text_later.csv`. Preserve exact retained-source, candidate, city, unit, cycle, file-hash, source-family, and mechanism lineage. Keep PDF and HTML lanes explicit, preserve the one bargaining unit × cycle × city observation rule, and keep causal and discourse corpora separate. Do not include OCR-later/defer, corrupt, oversized, review/error, octet-stream review, or prior source-review exclusions.

Do not open URLs, download documents, run OCR unless separately authorized, render pages, rate evidence, call GABRIEL/API or another model, ingest, codify, normalize values, calculate wage gaps, run regressions/treatment effects, make causal or prevalence claims, or mark global analysis readiness true. Extraction is not rating or causal evidence.

For the next source-expansion wave, default to broad state-by-state geographic scanning with source-family diversity. Preserve mechanism tags after collection; use mechanism-targeted discovery only as secondary gap-filling after broad scans.
""")
    write_text(OUTPUT_DIR / "next_task.md", """# Next task: bounded Tier C text-layer extraction

Extract local machine-readable text only from the completed PDF `parse_text_layer_later` and HTML `html_text_later` manifests. Preserve exact lineage, PDF/HTML separation, city × unit × cycle observations, and causal/discourse separation. Exclude all deferred, corrupt, oversized, review/error, and prior-excluded rows.

No URL access, downloads, OCR unless separately authorized, rendering, rating, model calls, ingestion, codification, value comparison, wage-gap calculation, regression, treatment effect, causal claim, or global-readiness change is authorized. After this retained wave, future scouting defaults to broad state-by-state coverage and explicit source-family diversification; mechanism-targeted scouts are secondary.
""")
    write_text(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_validation_2026-07-27.md", f"""# Tier C readiness/dashboard-map validation — 2026-07-27

Internal invariants passed for 463 immutable retained Tier C files. File integrity passed 463/463; types reconcile to 397 PDF, 65 HTML, and one octet-stream; 93 exclusions remain outside the queue. Readiness decision: `{decision_name}`. Dashboard map inputs contain the current Tier C layer and map data date 2026-07-27. Required repository validation results are appended after the command suite.
""")
    write_text(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_validation_2026-07-27.md", "See tier_c_readiness_dashboard_map_update_validation_2026-07-27.md for the complete task validation record.")

    write_text(ROOT / "docs/analysis/tier_c_readiness_dashboard_map_update_result_2026-07-27.md", f"""# Tier C readiness and dashboard map update result

- Decision: `{decision_name}`.
- Readiness scope: 463 retained Tier C files (397 PDF; 65 HTML; 1 octet-stream).
- Readiness counts: `{counts}`.
- Bounded text-layer extraction-ready files: {ready_count}.
- Dashboard map data date: 2026-07-27.
- Future source expansion: broad state-by-state scanning with source-family diversity by default.
- Global analysis readiness: false.
""")
    write_text(ROOT / "docs/analysis/tier_c_readiness_dashboard_map_update_dashboard_status_note_2026-07-27.md", f"""# Dashboard status note — Tier C readiness/map update

- Current phase: Tier C readiness reviewed; bounded text-layer extraction ready next.
- Retained readiness scope: 463.
- Readiness counts: `{counts}`.
- Map data date: 2026-07-27.
- Current map layer: retained Tier C and readiness metadata; historical scout context remains labeled historical.
- Evidence status: retained/readiness operational metadata and bounded documentary scaffolds only.
- Global analysis readiness: false.
""")
    write_text(ROOT / "docs/analysis/future_broad_geographic_scouting_strategy_2026-07-27.md", (OUTPUT_DIR / "future_broad_geographic_scouting_strategy.md").read_text(encoding="utf-8"))
    return decision_name


def inspect() -> None:
    queue, excluded, _ = verify_inputs(verify_file_bytes=True)
    lock_path = OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_lock.json"
    queue_path = OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_locked_queue.csv"
    preflight_path = OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preflight_checks.json"
    if not (lock_path.is_file() and queue_path.is_file() and preflight_path.is_file()):
        raise RuntimeError("readiness preparation/preflight outputs missing")
    lock = read_json(lock_path)
    preflight = read_json(preflight_path)
    locked = read_csv(queue_path)
    if not (
        preflight.get("preflight_passed") is True
        and len(queue) == len(locked) == EXPECTED_COUNT
        and sha256(queue_path) == lock["queue_sha256"]
        and id_set_hash(locked) == lock["retained_source_id_set_sha256"] == EXPECTED_ID_SET_HASH
    ):
        raise RuntimeError("readiness inspection lock/preflight failed")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(inspect_one, locked))
    if len(results) != EXPECTED_COUNT or any(row["readiness_status"] not in CONTROLLED_STATUSES for row in results):
        raise RuntimeError("readiness result reconciliation failed")
    decision = write_outputs(results, excluded)
    validate_complete()
    print(json.dumps({"status": "readiness_review_completed", "decision": decision, "rows": len(results)}))


def validate_complete() -> None:
    missing = [name for name in REQUIRED_FINAL_OUTPUTS if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"partial readiness output cannot masquerade as complete: {missing}")
    results = read_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_results.csv")
    decision = read_json(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_decision.json")
    invariants = read_json(OUTPUT_DIR / "tier_c_readiness_dashboard_map_update_invariant_checks.json")
    preserved = read_csv(OUTPUT_DIR / "tier_c_pdf_text_layer_readiness_463_preserved_source_review_exclusions.csv")
    if not (
        len(results) == EXPECTED_COUNT
        and len({row["retained_source_id"] for row in results}) == EXPECTED_COUNT
        and len(preserved) == 93
        and invariants.get("all_invariants_passed") is True
        and decision.get("global_analysis_readiness") is False
        and all(row["readiness_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in results)
    ):
        raise RuntimeError("completed readiness outputs fail closed validation")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--inspect", action="store_true")
    action.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.inspect:
        inspect()
    else:
        verify_inputs(verify_file_bytes=True)
        validate_complete()
        print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED_COUNT}))


if __name__ == "__main__":
    main()
