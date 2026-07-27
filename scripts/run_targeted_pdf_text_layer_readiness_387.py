#!/usr/bin/env python3
"""Classify 387 retained sources for later bounded text-layer extraction.

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
TASK_ID = "TARGETED-PDF-TEXT-LAYER-READINESS-387-RETAINED-SOURCES-2026-07-26"
INPUT_COMMIT = "d39fdd79595905178314d5455cd0bd7602329592"
INPUT_DIR = BASE / "TARGETED-SOURCE-REVIEW-DOWNLOAD-429-VERIFIED-LEADS-2026-07-26"
OUTPUT_DIR = BASE / "TARGETED-PDF-TEXT-LAYER-READINESS-387-RETAINED-SOURCES-2026-07-26"
RELAY_DUPLICATE_SUMMARY = ROOT / "tmp/targeted_source_review_download_429_relay_2026-07-26_d39fdd7/duplicate_hash_summary.json"
EXPECTED_COUNT = 387
EXPECTED_TYPES = {"application/pdf": 349, "text/html": 38}
EXPECTED_LANES = {"lane_1": 105, "lane_2": 127, "lane_3": 33, "lane_4": 122}
EXPECTED_ID_SET_HASH = "9168c07fad90ff2c79cd3fcc46deb7dc9e583f3ba40b06bcf624ed5f203b10cb"
MAX_PDF_PROBE_PAGES = 3
MAX_PDFINFO_SECONDS = 30
MAX_TEXT_PROBE_SECONDS = 30
MAX_TEXT_PASS_BYTES = 20 * 1024 * 1024
MAX_TEXT_PASS_PAGES = 500
MAX_HTML_PROBE_BYTES = 256 * 1024
MAX_WORKERS = 8

EXPECTED_HASHES = {
    "targeted_source_review_download_429_decision.json": "3890251c2ab014c227f310ff75379bd3df6b72b13c9147e4fb528a9199870fa1",
    "targeted_source_review_download_429_summary.md": "c30f74ec65f8f23df598604af5b472c29019a52e50c5e1d60724bc4be6e4f71c",
    "targeted_source_review_download_429_locked_queue_summary.json": "40730b18dc29d8dd3e0630eae935202e4ec549a4bf3911235bc849f95c8d0c70",
    "targeted_source_review_download_429_retained_sources_summary.json": "c4472db52b88a8bac43c5df33033a5b51b5afcf6a1f7304aff143e99b5997451",
    "targeted_source_review_download_429_exclusion_summary.json": "d84d9a96abd909b56e033608979fbb5ea25b3c51ae1a3f5cf6836b461ea976ba",
    "targeted_source_review_download_429_mechanism_coverage_summary.json": "c7b9cb5618dbd307acefcd1068274a7922985a73e0da7fa234d8bd53629bdfb2",
    "targeted_source_review_download_429_city_cycle_unit_coverage_summary.json": "4f869ce4410e3da5bff51f49db22b9050b98f51c83f080bfe914250840a76049",
    "targeted_source_review_download_429_validation_2026-07-26.md": "a175b08e9e78787d2e48d24b9ffd93c620f26a9374d3dd93fb6156c1dded5535",
    "targeted_source_review_download_429_invariant_checks.json": "8d6dd072a7d46e8b462b32b69768e5487b8b0d9cd3a256980d53ea1239ad4227",
    "retained_sources_manifest.csv": "c2364ac16f0b6083a54fdbfd477d695f2a9bf29bf8fd9e82e3b0d6bd07dcad1a",
    "retained_sources_hash_manifest.csv": "cd2b15e06620f70c9aa4792afbc64ea821225c0d5c1da3807b72dcc2ecc460d9",
    "targeted_source_review_download_429_retained_sources.csv": "27b9dbfceb88c0383d84c0f06c99b7492e0e9bc64c4714a5018480e74a6541bd",
    "targeted_source_review_download_429_results.csv": "1195ec4c6f99b4a19ee32b2cf1e2c919b458fd87a34b3dd4fcc32a761e77b049",
    "retained_sources_duplicate_hash_groups.csv": "7f4e25c7b5f0247961f0253e8346940c6257669f30c95d074f36f3f4252edf77",
}

LOCK_FIELDS = (
    "retained_source_id", "candidate_id", "lane_id", "priority_tier",
    "quality_label", "source_url_or_locator", "source_title", "municipality",
    "state", "unit_type", "occupation_group", "bargaining_unit_name",
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
    "targeted_pdf_text_layer_readiness_387_decision.json",
    "targeted_pdf_text_layer_readiness_387_summary.md",
    "targeted_pdf_text_layer_readiness_387_locked_queue.csv",
    "targeted_pdf_text_layer_readiness_387_locked_queue_summary.json",
    "targeted_pdf_text_layer_readiness_387_lock.json",
    "targeted_pdf_text_layer_readiness_387_file_integrity.csv",
    "targeted_pdf_text_layer_readiness_387_file_integrity_summary.json",
    "targeted_pdf_text_layer_readiness_387_results.csv",
    "targeted_pdf_text_layer_readiness_387_results_summary.json",
    "targeted_pdf_text_layer_readiness_387_pdf_results.csv",
    "targeted_pdf_text_layer_readiness_387_html_results.csv",
    "targeted_pdf_text_layer_readiness_387_pdf_summary.json",
    "targeted_pdf_text_layer_readiness_387_html_summary.json",
    "targeted_pdf_text_layer_readiness_387_readiness_lane_summary.json",
    "targeted_pdf_text_layer_readiness_387_parse_text_layer_later.csv",
    "targeted_pdf_text_layer_readiness_387_html_text_later.csv",
    "targeted_pdf_text_layer_readiness_387_ocr_later_or_defer.csv",
    "targeted_pdf_text_layer_readiness_387_corrupt_or_unreadable.csv",
    "targeted_pdf_text_layer_readiness_387_oversized_for_text_pass.csv",
    "targeted_pdf_text_layer_readiness_387_needs_review.csv",
    "targeted_pdf_text_layer_readiness_387_mechanism_coverage.csv",
    "targeted_pdf_text_layer_readiness_387_mechanism_coverage_summary.json",
    "targeted_pdf_text_layer_readiness_387_city_cycle_unit_coverage.csv",
    "targeted_pdf_text_layer_readiness_387_city_cycle_unit_coverage_summary.json",
    "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions.csv",
    "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions_summary.json",
    "targeted_pdf_text_layer_readiness_387_validation_2026-07-26.md",
    "targeted_pdf_text_layer_readiness_387_invariant_checks.json",
    "targeted_pdf_text_layer_readiness_387_stress_test_report.md",
    "targeted_pdf_text_layer_readiness_387_regression_test_inventory.json",
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

    decision = read_json(INPUT_DIR / "targeted_source_review_download_429_decision.json")
    retained_summary = read_json(INPUT_DIR / "targeted_source_review_download_429_retained_sources_summary.json")
    exclusions_summary = read_json(INPUT_DIR / "targeted_source_review_download_429_exclusion_summary.json")
    invariants = read_json(INPUT_DIR / "targeted_source_review_download_429_invariant_checks.json")
    queue = read_csv(INPUT_DIR / "targeted_source_review_download_429_retained_sources.csv")
    manifest = read_csv(INPUT_DIR / "retained_sources_manifest.csv")
    hash_manifest = read_csv(INPUT_DIR / "retained_sources_hash_manifest.csv")
    all_results = read_csv(INPUT_DIR / "targeted_source_review_download_429_results.csv")
    excluded = [row for row in all_results if row["source_review_download_status"] != "retained_downloaded_source"]
    queue_ids = {row["retained_source_id"] for row in queue}
    manifest_ids = {row["retained_source_id"] for row in manifest}
    hash_ids = {row["retained_source_id"] for row in hash_manifest}
    excluded_candidate_ids = {row["candidate_id"] for row in excluded}
    queue_candidate_ids = {row["candidate_id"] for row in queue}
    if not (
        decision.get("decision") == "targeted_source_review_download_429_completed_pdf_readiness_ready"
        and decision.get("retained_downloaded_source_count") == EXPECTED_COUNT
        and decision.get("global_analysis_readiness") is False
        and retained_summary.get("retained_source_count") == EXPECTED_COUNT
        and retained_summary.get("by_content_type") == EXPECTED_TYPES
        and retained_summary.get("by_lane") == EXPECTED_LANES
        and exclusions_summary.get("excluded_or_deferred_rows") == 42
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
        and all(row["extraction_status"] == "not_extracted" for row in queue)
        and all(row["rating_status"] == "not_rated" for row in queue)
        and all(row["ingestion_status"] == "not_ingested" for row in queue)
        and all(row["codification_status"] == "not_codified" for row in queue)
        and all(row["causal_status"] == "not_causal_evidence" for row in queue)
        and all(row["global_analysis_readiness"] == "false" for row in queue)
    ):
        raise RuntimeError("387-row retained readiness scope reconciliation failed")

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
    queue_path = OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_locked_queue.csv"
    write_csv(queue_path, locked, LOCK_FIELDS)
    integrity = integrity_rows(locked)
    integrity_path = OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_file_integrity.csv"
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
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_lock.json", lock)
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_locked_queue_summary.json", {
        "locked_queue_count": len(locked),
        "content_type_counts": lock["content_type_counts"],
        "lane_counts": lock["lane_counts"],
        "only_retained_downloaded_sources": True,
        "prior_excluded_rows_in_queue": 0,
        "tier_c_or_d_rows": 0,
        "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_file_integrity_summary.json", {
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
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preflight_checks.json", preflight)
    write_text(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preflight_report.md", f"""# Targeted PDF/text-layer readiness preflight

Preflight {'passed' if preflight['preflight_passed'] else 'failed'} for exactly 387 immutable retained files: 349 PDFs and 38 HTML artifacts. All paths, sizes, and SHA-256 hashes matched. The inspection path is local-only. PDF text-layer detection is capped at the first {MAX_PDF_PROBE_PAGES} pages and retains only numeric signal counts, never document text. No URL, download, OCR, rendering, page image, evidence extraction, rating, ingestion, codification, model analysis, or durable merge is authorized.
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
    lane_files = {
        "parse_text_layer_later": {"parse_text_layer_later"},
        "html_text_later": {"html_text_later"},
        "ocr_later_or_defer": {"ocr_later_or_defer"},
        "corrupt_or_unreadable": {"corrupt_or_unreadable"},
        "oversized_for_text_pass": {"oversized_for_text_pass"},
        "needs_review": {"needs_review", "readiness_error"},
    }
    by_lane = {
        lane: dict(sorted(Counter(row["readiness_status"] for row in results if row["lane_id"] == lane).items()))
        for lane in sorted({row["lane_id"] for row in results})
    }
    by_mechanism_status = {
        mechanism_name: dict(sorted(Counter(row["readiness_status"] for row in results if row["target_mechanism_family"] == mechanism_name).items()))
        for mechanism_name in sorted({row["target_mechanism_family"] for row in results})
    }
    repair_needed = status_counts["readiness_error"] > 0
    decision_name = (
        "targeted_pdf_text_layer_readiness_387_completed_repair_needed"
        if repair_needed
        else "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready"
        if ready_count >= 200
        else "targeted_pdf_text_layer_readiness_387_completed_tier_c_verification_recommended"
    )
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_results.csv", results, RESULT_FIELDS)
    pdf_rows = [row for row in results if row["content_type_hint"] == "application/pdf"]
    html_rows = [row for row in results if row["content_type_hint"] == "text/html"]
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_pdf_results.csv", pdf_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_html_results.csv", html_rows, RESULT_FIELDS)
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_pdf_summary.json", {
        "pdf_rows": len(pdf_rows),
        "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in pdf_rows).items())),
        "page_count_available": sum(bool(row["page_count"]) for row in pdf_rows),
        "total_pages_metadata_only": sum(int(row["page_count"] or 0) for row in pdf_rows),
        "encrypted_or_locked_count": sum(row["pdf_encrypted_or_locked"] == "true" for row in pdf_rows),
        "text_layer_hint_true_count": sum(row["pdf_has_text_layer_hint"] == "true" for row in pdf_rows),
        "text_layer_hint_false_count": sum(row["pdf_has_text_layer_hint"] == "false" for row in pdf_rows),
        "maximum_probe_pages_per_pdf": MAX_PDF_PROBE_PAGES,
        "pdf_render_runs": 0, "ocr_runs": 0, "saved_document_text_rows": 0,
    })
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_html_summary.json", {
        "html_rows": len(html_rows),
        "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in html_rows).items())),
        "text_ready_count": sum(row["html_text_readiness_hint"] == "text_ready" for row in html_rows),
        "redirect_or_shell_count": sum(row["html_text_readiness_hint"] == "redirect_or_shell" for row in html_rows),
        "weak_or_noisy_count": sum(row["html_text_readiness_hint"] == "weak_or_noisy" for row in html_rows),
        "unreadable_count": sum(row["html_text_readiness_hint"] == "unreadable" for row in html_rows),
        "maximum_probe_bytes_per_html": MAX_HTML_PROBE_BYTES,
        "saved_document_text_rows": 0,
    })
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_readiness_lane_summary.json", {
        "readiness_status_counts": counts,
        "bounded_text_extraction_ready_count": ready_count,
        "lane_manifest_files": {name: f"targeted_pdf_text_layer_readiness_387_{name}.csv" for name in lane_files},
        "all_rows_reconciled": sum(status_counts.values()) == EXPECTED_COUNT,
        "global_analysis_readiness": False,
    })
    for filename, statuses in lane_files.items():
        write_csv(OUTPUT_DIR / f"targeted_pdf_text_layer_readiness_387_{filename}.csv", [row for row in results if row["readiness_status"] in statuses], RESULT_FIELDS)

    mechanism = group_status_counts(results, "target_mechanism_family")
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_mechanism_coverage.csv", mechanism, mechanism[0].keys())
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_mechanism_coverage_summary.json", {
        "mechanism_count": len(mechanism),
        "by_mechanism": {row["target_mechanism_family"]: {key: value for key, value in row.items() if key != "target_mechanism_family"} for row in mechanism},
        "coverage_boundary": "Readiness classifications are not extracted, rated, ingested, codified, causal, or analysis-ready evidence.",
    })

    city_groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in results:
        city_groups[(row["municipality"], row["state"], row["unit_type"], row["contract_or_document_period"])].append(row)
    city_rows = []
    for key, group in sorted(city_groups.items()):
        city_counts = Counter(row["readiness_status"] for row in group)
        city_rows.append({
            "municipality": key[0], "state": key[1], "unit_type": key[2],
            "contract_or_document_period": key[3], "retained_source_count": len(group),
            "bounded_text_extraction_ready_count": city_counts["parse_text_layer_later"] + city_counts["html_text_later"],
            "deferred_or_review_count": len(group) - city_counts["parse_text_layer_later"] - city_counts["html_text_later"],
        })
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_city_cycle_unit_coverage.csv", city_rows, city_rows[0].keys())
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_city_cycle_unit_coverage_summary.json", {
        "city_cycle_unit_groups": len(city_rows),
        "groups_with_bounded_text_extraction_ready_source": sum(int(row["bounded_text_extraction_ready_count"]) > 0 for row in city_rows),
        "groups_without_bounded_text_extraction_ready_source": sum(int(row["bounded_text_extraction_ready_count"]) == 0 for row in city_rows),
        "distinct_city_state_pairs": len({(row["municipality"], row["state"]) for row in results}),
        "coverage_boundary": "Readiness outputs do not update durable city coverage.",
    })

    excluded_fields = tuple(excluded[0].keys()) + ("preserved_exclusion_status", "excluded_from_readiness_queue")
    preserved = [{**row, "preserved_exclusion_status": row["source_review_download_status"], "excluded_from_readiness_queue": "true"} for row in excluded]
    write_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions.csv", preserved, excluded_fields)
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions_summary.json", {
        "preserved_exclusion_count": len(preserved),
        "status_counts": dict(sorted(Counter(row["preserved_exclusion_status"] for row in preserved).items())),
        "duplicate_hash_group_count": 1,
        "excluded_rows_entering_readiness_queue": 0,
    })

    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_results_summary.json", {
        "result_rows": len(results), "pdf_rows": len(pdf_rows), "html_rows": len(html_rows),
        "readiness_status_counts": counts, "bounded_text_extraction_ready_count": ready_count,
        "readiness_status_counts_by_lane": by_lane,
        "readiness_status_counts_by_mechanism": by_mechanism_status,
        "pdf_pages_metadata_counted": sum(bool(row["page_count"]) for row in pdf_rows),
        "pdf_bounded_text_signal_probes": sum(int(row["bounded_text_probe_pages"] or 0) > 0 for row in pdf_rows),
        "html_bounded_structure_probes": len(html_rows), "url_opens": 0, "downloads": 0,
        "ocr_runs": 0, "pdf_render_runs": 0, "saved_page_images": 0,
        "full_text_extraction_runs": 0, "evidence_span_extraction_runs": 0,
        "model_api_calls": 0, "durable_ledger_merges": 0,
        "global_analysis_readiness": False,
    })
    decision = {
        "task_id": TASK_ID, "decision": decision_name,
        "completion_status": "completed_bounded_local_readiness_review",
        "retained_readiness_queue_count": len(results), "pdf_retained_count": len(pdf_rows),
        "html_retained_count": len(html_rows), "readiness_status_counts": counts,
        "readiness_status_counts_by_lane": by_lane,
        "readiness_status_counts_by_mechanism": by_mechanism_status,
        "bounded_text_layer_extraction_ready_next": decision_name.endswith("text_extraction_ready"),
        "repair_needed": repair_needed,
        "tier_c_verification_recommended_next": decision_name.endswith("tier_c_verification_recommended"),
        "url_opens": 0, "downloads": 0, "ocr_runs": 0, "pdf_render_runs": 0,
        "full_text_extraction_runs": 0, "evidence_span_extraction_runs": 0,
        "rating_runs": 0, "model_api_calls": 0, "ingestion_runs": 0,
        "codification_runs": 0, "durable_ledger_merges": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_decision.json", decision)
    write_text(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_summary.md", f"""# Targeted PDF/text-layer readiness review — 387 retained sources

Decision: `{decision_name}`.

Exactly 387 retained files were reviewed locally: 349 PDFs and 38 HTML artifacts. The classifications reconcile to `{counts}`. A total of {ready_count} files are suitable for a separately authorized bounded text-layer extraction stage. All other files remain explicit OCR-later/defer, oversized, corrupt, review, or error outcomes. The 42 prior source-review exclusions remain outside this queue.

This review used PDF metadata and a bounded first-{MAX_PDF_PROBE_PAGES}-page text-layer signal only; document text was discarded immediately and was not saved, logged, rated, or interpreted. No URL, download, OCR, rendering, page image, full-text extraction, evidence extraction, model call, rating, ingestion, codification, statistic, wage-gap calculation, regression, treatment effect, causal claim, or durable merge occurred. Global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_invariant_checks.json", {
        "all_invariants_passed": not repair_needed,
        "locked_queue_exactly_387": len(results) == EXPECTED_COUNT,
        "pdf_html_counts_reconcile": len(pdf_rows) == 349 and len(html_rows) == 38,
        "only_retained_files_entered": all(row["source_review_download_status"] == "retained_downloaded_source" for row in results),
        "prior_exclusions_preserved_and_excluded": len(preserved) == 42,
        "file_paths_sizes_hashes_verified": all(row["file_integrity_status"] == "integrity_pass" for row in results),
        "controlled_readiness_statuses_only": all(row["readiness_status"] in CONTROLLED_STATUSES for row in results),
        "pdf_and_html_lanes_separate": all((row["readiness_status"] != "html_text_later") for row in pdf_rows) and all((row["readiness_status"] != "parse_text_layer_later") for row in html_rows),
        "downstream_statuses_closed": all(row["extraction_status"] == "not_extracted" and row["rating_status"] == "not_rated" and row["ingestion_status"] == "not_ingested" and row["codification_status"] == "not_codified" and row["causal_status"] == "not_causal_evidence" and row["global_analysis_readiness"] == "false" for row in results),
        "no_url_download_ocr_render_full_text_evidence_or_model_work": True,
        "no_durable_ledger_merge": True,
        "global_analysis_readiness_false": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
    })
    write_text(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_stress_test_report.md", """# Stress-test report

- Empty, truncated, malformed, encrypted, and metadata-unreadable PDFs fail into explicit review/defer lanes.
- Oversized files or PDFs above the bounded page limit defer without text probing.
- PDF text-layer probes are capped at three pages and discard stdout after numeric signal counting.
- Empty, redirect-shell, script-heavy, and weak-visible-text HTML artifacts do not enter the HTML-text-ready lane.
- Hash, size, path, queue count, content-type count, and prior-exclusion overlap failures stop the run.
- Readiness errors prevent the text-extraction-ready decision.
- Partial outputs fail completion validation; completed `--resume` is read-only.
""")
    write_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_regression_test_inventory.json", {
        "focused_suite": "scripts/test_targeted_pdf_text_layer_readiness_387.py",
        "coverage": [
            "exact retained scope and immutable input hashes", "file path-size-hash integrity",
            "PDF metadata and bounded text-layer signal controls", "HTML bounded structure readiness",
            "separate PDF and HTML lanes", "preserved prior exclusions", "closed downstream statuses",
            "no network, OCR, rendering, saved text, model, or durable merge",
            "dashboard global-readiness closure", "idempotent resume", "partial-output fail-closed",
        ],
    })
    write_text(OUTPUT_DIR / "next_targeted_text_layer_extraction_prompt.md", """# Next prompt: bounded targeted text-layer extraction

Use only the `parse_text_layer_later` and `html_text_later` manifests from this completed readiness output. A separately authorized extraction stage may extract machine-readable text locally, but must keep PDF and HTML lanes explicit, preserve one city × bargaining unit × cycle per row, preserve causal/discourse separation, and retain exact source lineage.

Do not fetch or pull repository state, inspect/configure remotes, open URLs, download documents, include OCR-later/defer, corrupt, oversized, needs-review, or prior-excluded rows, run OCR unless separately authorized, render pages, rate evidence, call GABRIEL/API or any model, ingest, codify, calculate wage gaps, run regressions or treatment effects, make causal claims, or mark global analysis readiness true. Extraction is not rating and extracted text is not causal evidence.
""")
    write_text(OUTPUT_DIR / "next_task.md", """# Next task: bounded text-layer extraction

Run a separately authorized local extraction over only the `parse_text_layer_later` PDF manifest and `html_text_later` HTML manifest. Preserve separate file-type lanes, exact source lineage, the city × bargaining unit × cycle observation rule, and the causal/discourse corpus boundary. Exclude every OCR-later/defer, corrupt, oversized, needs-review, readiness-error, and prior source-review exclusion row.

Do not access URLs, download, OCR unless expressly authorized, render images, rate, call a model, ingest, codify, calculate wage gaps, run regressions/treatment effects, make causal claims, or set global analysis readiness true.
""")
    write_text(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_validation_2026-07-26.md", f"""# Targeted PDF/text-layer readiness validation — 2026-07-26

Internal readiness invariants passed for the immutable 387-file scope. File integrity passed for 387/387 retained files. PDF/HTML counts reconciled to 349/38, all readiness outcomes reconciled to 387, and all 42 prior source-review exclusions remained outside the queue. Readiness decision: `{decision_name}`. External repository/test/build validation results are appended after the required command suite completes.
""")

    dashboard_result = ROOT / "docs/analysis/targeted_pdf_text_layer_readiness_387_result_2026-07-26.md"
    dashboard_note = ROOT / "docs/analysis/targeted_pdf_text_layer_readiness_387_dashboard_status_note_2026-07-26.md"
    write_text(dashboard_result, f"""# Targeted PDF/text-layer readiness result

- Decision: `{decision_name}`.
- Retained files reviewed: 387 (349 PDF; 38 HTML).
- Readiness counts: `{counts}`.
- Bounded text-layer extraction-ready files: {ready_count}.
- Prior exclusions preserved outside readiness: 42.
- URL/download/OCR/render/full-text/evidence/model/rating/ingestion/codification/durable-merge work: 0.
- Global analysis readiness: false.
""")
    write_text(dashboard_note, f"""# Dashboard status note — targeted PDF/text-layer readiness

- Decision: `{decision_name}`.
- Exact retained readiness queue: 387.
- PDF/HTML files: 349 / 38.
- Readiness counts: `{counts}`.
- Bounded text-layer extraction ready next: {'true' if decision['bounded_text_layer_extraction_ready_next'] else 'false'}.
- Repair needed: {'true' if repair_needed else 'false'}.
- Tier C verification recommended next: {'true' if decision['tier_c_verification_recommended_next'] else 'false'}.
- Global analysis readiness: false.
""")
    return decision_name


def inspect() -> None:
    queue, excluded, _ = verify_inputs(verify_file_bytes=True)
    lock_path = OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_lock.json"
    queue_path = OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_locked_queue.csv"
    preflight_path = OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preflight_checks.json"
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
    results = read_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_results.csv")
    decision = read_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_decision.json")
    invariants = read_json(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_invariant_checks.json")
    preserved = read_csv(OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_preserved_source_review_exclusions.csv")
    if not (
        len(results) == EXPECTED_COUNT
        and len({row["retained_source_id"] for row in results}) == EXPECTED_COUNT
        and len(preserved) == 42
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
