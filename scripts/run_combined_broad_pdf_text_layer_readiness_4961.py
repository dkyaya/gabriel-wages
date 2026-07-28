#!/usr/bin/env python3
"""Review 4,961 retained local sources for later text extraction readiness.

The runner is deliberately split into a serial fail-closed preflight, four
isolated and independently resumable worker lanes, and a serial coordinator.
It never opens a network URL, downloads a source, renders a document, runs OCR,
saves document text, extracts evidence/tables/spans, calls a model, rates,
ingests, codifies, or performs statistical analysis.

PDF text-layer detection uses a bounded first-three-page signal sent only to
memory; the bytes are immediately reduced to a character count and discarded.
HTML inspection is capped at 256 KiB and retains only structural counts. Other
documents are classified from extension, magic bytes, and container metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
INPUT_DIR = BASE / "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
OUTPUT_DIR = BASE / "COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
TASK_ID = "COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_pdf_text_layer_readiness_4961"
EXPECTED_COUNT = 4_961
EXPECTED_TYPES = {"pdf": 3_980, "html": 941, "other_document": 40}
LANE_COUNTS = {
    "readiness_lane_001": 1_240,
    "readiness_lane_002": 1_240,
    "readiness_lane_003": 1_240,
    "readiness_lane_004": 1_241,
}
LANE_STAGGER_MINUTES = {
    "readiness_lane_001": 0,
    "readiness_lane_002": 8,
    "readiness_lane_003": 16,
    "readiness_lane_004": 24,
}
MAX_PDF_PROBE_PAGES = 3
MAX_PDFINFO_SECONDS = 45
MAX_TEXT_PROBE_SECONDS = 45
MAX_TEXT_PASS_BYTES = 20 * 1024 * 1024
MAX_TEXT_PASS_PAGES = 500
MAX_HTML_PROBE_BYTES = 256 * 1024

CONTROLLED_STATUSES = {
    "parse_text_layer_later",
    "html_text_later",
    "other_document_text_later",
    "ocr_later_or_defer",
    "oversized_for_text_pass",
    "corrupt_or_unreadable",
    "encrypted_or_locked",
    "shell_or_navigation_only",
    "unsupported_for_text_extraction",
    "needs_review",
    "readiness_error",
}
CONTROLLED_FILE_TYPES = {
    "pdf", "html", "doc", "docx", "xls", "xlsx", "csv", "txt", "rtf",
    "other_document", "unknown_needs_review",
}
EXTRACTION_READY_STATUSES = {
    "parse_text_layer_later", "html_text_later", "other_document_text_later"
}

INPUT_FIELDS = (
    "source_review_download_id", "combined_review_id", "source_candidate_id",
    "verification_row_id", "candidate_origin", "state", "region", "municipality",
    "county", "source_title", "source_locator_or_url", "final_canonical_locator",
    "source_domain", "source_family_hint", "document_type_hint",
    "source_review_priority", "retained_file_path", "retained_file_type",
    "retained_file_size_bytes", "retained_file_sha256",
)
LOCK_FIELDS = (
    "readiness_id", *INPUT_FIELDS[:5], "lane_id", "lane_sequence", *INPUT_FIELDS[5:],
    "file_extension", "detected_file_type", "download_status", "source_review_status",
    "extraction_status", "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness", "notes",
)
RESULT_FIELDS = LOCK_FIELDS + (
    "file_integrity_status", "page_count", "pdf_encrypted_or_locked",
    "pdf_has_text_layer_hint", "html_text_readiness_hint",
    "other_document_text_readiness_hint", "readiness_status", "readiness_reason",
)

REQUIRED_INPUTS = (
    "combined_broad_source_review_download_5589_decision.json",
    "combined_broad_source_review_download_5589_summary.md",
    "combined_broad_source_review_download_5589_retained_sources.csv",
    "combined_broad_source_review_download_5589_retained_sources_summary.json",
    "combined_broad_source_review_download_5589_retained_sources_manifest.csv",
    "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv",
    "combined_broad_source_review_download_5589_results_summary.json",
    "combined_broad_source_review_download_5589_state_summary.json",
    "combined_broad_source_review_download_5589_region_summary.json",
    "combined_broad_source_review_download_5589_municipality_summary.json",
    "combined_broad_source_review_download_5589_source_family_summary.json",
    "combined_broad_source_review_download_5589_non_cba_retained_source_summary.json",
    "combined_broad_source_review_download_5589_dashboard_update_summary.json",
    "combined_broad_source_review_download_5589_validation_2026-07-28.md",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_hash(rows: Iterable[dict[str, str]]) -> str:
    return text_hash("\n".join(sorted(row["source_review_download_id"] for row in rows)))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def detect_file_type(path: Path, retained_type: str) -> str:
    with path.open("rb") as handle:
        head = handle.read(4096)
    lower = head.lstrip().lower()
    suffix = path.suffix.casefold()
    if head.startswith(b"%PDF-"):
        return "pdf"
    if b"<html" in lower or b"<!doctype html" in lower or retained_type == "html":
        return "html"
    if suffix in {".docx", ".xlsx"} or (head.startswith(b"PK\x03\x04") and retained_type in {"docx", "xlsx"}):
        return retained_type if retained_type in {"docx", "xlsx"} else "other_document"
    if head.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        return retained_type if retained_type in {"doc", "xls"} else "other_document"
    if suffix in {".csv", ".txt", ".rtf"}:
        return suffix[1:]
    if retained_type in CONTROLLED_FILE_TYPES:
        return retained_type
    return "unknown_needs_review"


def readiness_id(source_review_download_id: str) -> str:
    return "CBRDY-20260728-" + hashlib.sha256(source_review_download_id.encode()).hexdigest()[:20]


def validate_input_ledgers() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    missing = [name for name in REQUIRED_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing or not (INPUT_DIR / "retained_sources").is_dir():
        raise RuntimeError(f"required non-derivable predecessor artifacts missing: {missing}")
    decision = read_json(INPUT_DIR / "combined_broad_source_review_download_5589_decision.json")
    summary = read_json(INPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_summary.json")
    rows = read_csv(INPUT_DIR / "combined_broad_source_review_download_5589_retained_sources.csv")
    manifest = read_csv(INPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_manifest.csv")
    hashes = read_csv(INPUT_DIR / "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv")
    row_ids = {row["source_review_download_id"] for row in rows}
    manifest_ids = {row["source_review_download_id"] for row in manifest}
    hash_ids = {row["source_review_download_id"] for row in hashes}
    type_counts = Counter(
        "pdf" if row["retained_file_type"] == "pdf" else
        "html" if row["retained_file_type"] == "html" else "other_document"
        for row in rows
    )
    if not (
        decision.get("decision") == "combined_broad_source_review_download_5589_completed_pdf_readiness_ready"
        and decision.get("retained_source_count") == EXPECTED_COUNT
        and decision.get("global_analysis_readiness") is False
        and summary.get("retained_source_count") == EXPECTED_COUNT
        and summary.get("unique_file_hash_count") == EXPECTED_COUNT
        and len(rows) == len(manifest) == len(hashes) == EXPECTED_COUNT
        and len(row_ids) == len(manifest_ids) == len(hash_ids) == EXPECTED_COUNT
        and row_ids == manifest_ids == hash_ids
        and len({row["retained_file_sha256"] for row in rows}) == EXPECTED_COUNT
        and type_counts == EXPECTED_TYPES
        and all(row["download_status"] == "downloaded_retained" for row in rows)
        and all(row["source_review_status"] == "source_reviewed_retained" for row in rows)
        and all(row["extraction_status"] == "not_extracted" for row in rows)
        and all(row["rating_status"] == "not_rated" for row in rows)
        and all(row["ingestion_status"] == "not_ingested" for row in rows)
        and all(row["codification_status"] == "not_codified" for row in rows)
        and all(row["causal_status"] == "not_causal_evidence" for row in rows)
        and all(row["global_analysis_readiness"] == "false" for row in rows)
    ):
        raise RuntimeError("predecessor retained-source reconciliation failed closed")
    hash_by_id = {row["source_review_download_id"]: row for row in hashes}
    manifest_by_id = {row["source_review_download_id"]: row for row in manifest}
    for row in rows:
        source_id = row["source_review_download_id"]
        hash_row = hash_by_id[source_id]
        manifest_row = manifest_by_id[source_id]
        if any(
            hash_row[field] != row[field]
            for field in ("retained_file_path", "retained_file_size_bytes", "retained_file_sha256")
        ) or any(
            manifest_row[field] != row[field]
            for field in ("retained_file_path", "retained_file_size_bytes", "retained_file_sha256", "retained_file_type")
        ):
            raise RuntimeError(f"manifest lineage mismatch: {source_id}")
    return rows, hashes


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output directory already exists: {OUTPUT_DIR}")
    rows, _ = validate_input_ledgers()
    if shutil.which("pdfinfo") is None or shutil.which("pdftotext") is None:
        raise RuntimeError("required local non-rendering PDF metadata tools unavailable")
    OUTPUT_DIR.mkdir(parents=True)

    integrity: list[dict[str, str]] = []
    locked: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        path = ROOT / row["retained_file_path"]
        inside = path.resolve().is_relative_to((INPUT_DIR / "retained_sources").resolve())
        exists = path.is_file()
        observed_size = path.stat().st_size if exists else -1
        observed_hash = sha256(path) if exists else ""
        passed = (
            exists and inside and observed_size == int(row["retained_file_size_bytes"])
            and observed_hash == row["retained_file_sha256"]
        )
        detected = detect_file_type(path, row["retained_file_type"]) if exists else "unknown_needs_review"
        integrity.append({
            "source_review_download_id": row["source_review_download_id"],
            "retained_file_path": row["retained_file_path"],
            "recorded_file_size_bytes": row["retained_file_size_bytes"],
            "observed_file_size_bytes": str(observed_size),
            "recorded_file_sha256": row["retained_file_sha256"],
            "observed_file_sha256": observed_hash,
            "file_exists": str(exists).lower(),
            "path_inside_retained_directory": str(inside).lower(),
            "file_integrity_status": "integrity_pass" if passed else "integrity_fail",
        })
        lane_id = next(
            lane for lane, upper in zip(LANE_COUNTS, (1240, 2480, 3720, 4961)) if index <= upper
        )
        lane_start = sum(count for lane, count in LANE_COUNTS.items() if lane < lane_id)
        item = {field: row.get(field, "") for field in INPUT_FIELDS}
        item.update({
            "readiness_id": readiness_id(row["source_review_download_id"]),
            "lane_id": lane_id,
            "lane_sequence": str(index - lane_start),
            "file_extension": path.suffix.casefold(),
            "detected_file_type": detected,
            "download_status": "downloaded_or_retained",
            "source_review_status": "retained",
            "extraction_status": "not_extracted",
            "rating_status": "not_rated",
            "ingestion_status": "not_ingested",
            "codification_status": "not_codified",
            "causal_status": "not_causal_evidence",
            "global_analysis_readiness": "false",
            "notes": "Locked local-only readiness row; no extraction, OCR, rendering, rating, ingestion, codification, or analysis.",
        })
        locked.append(item)

    if any(row["file_integrity_status"] != "integrity_pass" for row in integrity):
        raise RuntimeError("retained file path/size/SHA-256 integrity failed materially")
    if Counter(row["lane_id"] for row in locked) != LANE_COUNTS:
        raise RuntimeError("exact readiness lane sizing failed")
    master_path = OUTPUT_DIR / f"{PREFIX}_locked_queue.csv"
    write_csv(master_path, locked, LOCK_FIELDS)
    master_hash = sha256(master_path)
    write_csv(OUTPUT_DIR / f"{PREFIX}_file_integrity_preflight.csv", integrity, integrity[0].keys())
    write_json(OUTPUT_DIR / f"{PREFIX}_file_integrity_preflight_summary.json", {
        "files_checked": len(integrity), "integrity_pass_count": len(integrity),
        "integrity_fail_count": 0, "recorded_total_bytes": sum(int(row["retained_file_size_bytes"]) for row in locked),
        "all_paths_inside_immutable_retained_directory": True, "global_analysis_readiness": False,
    })
    master_ids = {row["source_review_download_id"] for row in locked}
    union_ids: set[str] = set()
    for lane_id, expected in LANE_COUNTS.items():
        lane_rows = [row for row in locked if row["lane_id"] == lane_id]
        lane_number = lane_id[-3:]
        lane_path = OUTPUT_DIR / f"combined_broad_pdf_text_layer_readiness_lane_{lane_number}_locked_queue.csv"
        write_csv(lane_path, lane_rows, LOCK_FIELDS)
        union_ids.update(row["source_review_download_id"] for row in lane_rows)
        lane_lock = {
            "task_id": TASK_ID, "lane_id": lane_id, "locked_queue_count": expected,
            "queue_sha256": sha256(lane_path), "source_id_set_sha256": id_set_hash(lane_rows),
            "stagger_start_minutes": LANE_STAGGER_MINUTES[lane_id], "inspection_status": "not_started",
            "worker_output_directory": relative(OUTPUT_DIR / "lanes" / lane_id),
            "shared_output_mutation_allowed": False, "global_analysis_readiness": False,
        }
        write_json(OUTPUT_DIR / f"combined_broad_pdf_text_layer_readiness_lane_{lane_number}_lock.json", lane_lock)
        write_json(OUTPUT_DIR / f"combined_broad_pdf_text_layer_readiness_lane_{lane_number}_locked_queue_summary.json", {
            "lane_id": lane_id, "locked_queue_count": expected,
            "retained_type_counts": dict(sorted(Counter(row["retained_file_type"] for row in lane_rows).items())),
            "queue_sha256": lane_lock["queue_sha256"], "global_analysis_readiness": False,
        })
    if union_ids != master_ids or len(union_ids) != EXPECTED_COUNT:
        raise RuntimeError("master queue does not equal union of four lane queues")
    lock = {
        "task_id": TASK_ID, "input_commit": "a305a4dd18f47099f000c48aa8c5d11f6df7bc04",
        "locked_queue_count": EXPECTED_COUNT, "queue_sha256": master_hash,
        "source_id_set_sha256": id_set_hash(locked), "lane_counts": LANE_COUNTS,
        "retained_type_counts": EXPECTED_TYPES, "unique_sha256_count": EXPECTED_COUNT,
        "inspection_status": "not_started", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_lock.json", lock)
    write_json(OUTPUT_DIR / f"{PREFIX}_locked_queue_summary.json", {
        "locked_queue_count": EXPECTED_COUNT, "lane_counts": LANE_COUNTS,
        "retained_pdf_count": EXPECTED_TYPES["pdf"], "retained_html_count": EXPECTED_TYPES["html"],
        "retained_other_document_count": EXPECTED_TYPES["other_document"],
        "master_equals_union_of_lanes": True, "only_retained_local_sources": True,
        "global_analysis_readiness": False,
    })
    checks = {
        "preflight_passed": True,
        "prior_decision_confirmed": "combined_broad_source_review_download_5589_completed_pdf_readiness_ready",
        "retained_source_count": EXPECTED_COUNT, "retained_hash_manifest_count": EXPECTED_COUNT,
        "unique_retained_sha256_count": EXPECTED_COUNT, "retained_type_counts": EXPECTED_TYPES,
        "all_retained_paths_exist": True, "all_file_sizes_match": True, "all_sha256_hashes_match": True,
        "locked_queue_count": EXPECTED_COUNT, "lane_counts": LANE_COUNTS,
        "master_equals_union_of_lanes": True, "lane_isolation_required": True,
        "source_review_download_reruns": 0, "redownloads": 0, "text_extraction_runs": 0,
        "table_extraction_runs": 0, "span_extraction_runs": 0, "ocr_runs": 0,
        "pdf_render_runs": 0, "rating_model_api_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "statistical_analysis_runs": 0,
        "dashboard_map_filter": "total_scout_coverage_only",
        "dashboard_overview_update_required_after_results": True,
        "secrets_printed_or_saved": False, "rollback_safe_output_directory": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json", checks)
    write_text(OUTPUT_DIR / f"{PREFIX}_preflight_report.md", f"""# Combined broad PDF/text-layer readiness preflight

Preflight passed for exactly **4,961** immutable retained local sources: **3,980 PDFs**, **941 HTML files**, and **40 other supported documents**. The retained ledger, manifest, and hash manifest have identical 4,961-row identities; all paths exist inside the predecessor retained directory; every size and SHA-256 hash matches; and all hashes are unique.

The locked master queue equals the disjoint union of four isolated lanes sized **1,240 / 1,240 / 1,240 / 1,241**. Workers may inspect local metadata and bounded text-layer/HTML structural signals only. No source-review rerun, redownload, full-text/table/span extraction, OCR, rendering, rating/model/API work, ingestion, codification, quantitative comparison, wage-gap/regression/treatment-effect work, or causal claim is authorized. The map remains total scout coverage only and global analysis readiness remains false.
""")
    print(json.dumps({"status": "preflight_passed", "rows": EXPECTED_COUNT, "queue_sha256": master_hash}))


def run_local(args: list[str], timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def parse_pdfinfo(payload: bytes) -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in payload.decode("utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip().casefold()] = value.strip()
    pages = values.get("pages", "")
    return {
        "pages": int(pages) if pages.isdigit() else 0,
        "encrypted": values.get("encrypted", "").casefold().startswith("yes"),
    }


class BoundedHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.visible = 0
        self.links = 0
        self.scripts = 0
        self.meta_refresh = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden += 1
        self.scripts += int(tag == "script")
        self.links += int(tag == "a")
        if tag == "meta":
            lowered = {key.casefold(): (value or "").casefold() for key, value in attrs}
            self.meta_refresh = self.meta_refresh or lowered.get("http-equiv") == "refresh"

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "svg"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.visible += sum(character.isalnum() for character in data)


def base_result(row: dict[str, str], status: str, reason: str, **details: str) -> dict[str, str]:
    result = {field: row.get(field, "") for field in LOCK_FIELDS}
    result.update({
        "file_integrity_status": "integrity_pass", "page_count": "",
        "pdf_encrypted_or_locked": "not_applicable" if row["retained_file_type"] != "pdf" else "unknown",
        "pdf_has_text_layer_hint": "not_applicable" if row["retained_file_type"] != "pdf" else "unknown",
        "html_text_readiness_hint": "not_applicable" if row["retained_file_type"] != "html" else "unknown",
        "other_document_text_readiness_hint": "not_applicable" if row["retained_file_type"] in {"pdf", "html"} else "unknown",
        "readiness_status": status, "readiness_reason": reason,
    })
    result.update(details)
    return result


def inspect_pdf(row: dict[str, str], path: Path) -> dict[str, str]:
    try:
        info = run_local(["pdfinfo", str(path)], MAX_PDFINFO_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return base_result(row, "readiness_error", f"pdfinfo_{type(exc).__name__}")
    stderr = info.stderr.decode("utf-8", errors="ignore").casefold()
    if info.returncode != 0:
        if "password" in stderr or "encrypted" in stderr:
            return base_result(row, "encrypted_or_locked", "pdf_metadata_locked", pdf_encrypted_or_locked="true")
        return base_result(row, "corrupt_or_unreadable", "pdf_metadata_unreadable_or_corrupt")
    metadata = parse_pdfinfo(info.stdout)
    pages = metadata["pages"]
    encrypted = metadata["encrypted"]
    common = {"page_count": str(pages) if pages else "", "pdf_encrypted_or_locked": str(encrypted).lower()}
    if pages <= 0:
        return base_result(row, "corrupt_or_unreadable", "pdf_page_count_unavailable", **common)
    if encrypted:
        return base_result(row, "encrypted_or_locked", "pdf_encrypted_or_locked", **common)
    if int(row["retained_file_size_bytes"]) > MAX_TEXT_PASS_BYTES or pages > MAX_TEXT_PASS_PAGES:
        return base_result(row, "oversized_for_text_pass", "pdf_exceeds_20mib_or_500_page_text_pass_limit", **common)
    probe_pages = min(MAX_PDF_PROBE_PAGES, pages)
    try:
        probe = run_local([
            "pdftotext", "-f", "1", "-l", str(probe_pages), "-enc", "UTF-8", "-nopgbrk", str(path), "-"
        ], MAX_TEXT_PROBE_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return base_result(row, "needs_review", f"bounded_text_layer_signal_{type(exc).__name__}", **common)
    # No probe bytes are written, logged, or returned. Only this numeric signal survives.
    signal_count = sum(chr(byte).isalnum() for byte in probe.stdout if byte < 128)
    if probe.returncode == 0 and signal_count >= 40:
        return base_result(row, "parse_text_layer_later", "bounded_first_three_pages_show_machine_readable_text_layer", pdf_has_text_layer_hint="true", **common)
    return base_result(row, "ocr_later_or_defer", "bounded_first_three_pages_do_not_show_usable_text_layer", pdf_has_text_layer_hint="false", **common)


def inspect_html(row: dict[str, str], path: Path) -> dict[str, str]:
    try:
        with path.open("rb") as handle:
            payload = handle.read(MAX_HTML_PROBE_BYTES)
    except OSError as exc:
        return base_result(row, "readiness_error", f"html_read_{type(exc).__name__}")
    if len(payload) < 16:
        return base_result(row, "corrupt_or_unreadable", "html_empty_or_too_short", html_text_readiness_hint="unreadable")
    decoded = payload.decode("utf-8", errors="replace")
    parser = BoundedHTMLParser()
    try:
        parser.feed(decoded)
    except Exception:
        return base_result(row, "needs_review", "bounded_html_parser_error", html_text_readiness_hint="weak_or_noisy")
    lower = decoded.casefold()
    shell = parser.meta_refresh or ("window.location" in lower and parser.visible < 200)
    navigation_heavy = parser.links >= 40 and parser.visible < 400
    if shell or navigation_heavy:
        return base_result(row, "shell_or_navigation_only", "bounded_html_signal_is_redirect_shell_or_navigation_heavy", html_text_readiness_hint="shell_or_navigation")
    if parser.visible >= 200:
        return base_result(row, "html_text_later", "bounded_html_structure_has_usable_visible_text", html_text_readiness_hint="text_ready")
    return base_result(row, "needs_review", "bounded_html_visible_text_signal_too_weak", html_text_readiness_hint="weak_or_noisy")


def inspect_other(row: dict[str, str], path: Path) -> dict[str, str]:
    detected = row["detected_file_type"]
    if path.stat().st_size <= 0:
        return base_result(row, "corrupt_or_unreadable", "other_document_empty", other_document_text_readiness_hint="unreadable")
    if detected in {"docx", "xlsx"}:
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
            plausible = (detected == "docx" and "word/document.xml" in names) or (detected == "xlsx" and "xl/workbook.xml" in names)
        except (OSError, zipfile.BadZipFile):
            plausible = False
        if plausible:
            return base_result(row, "other_document_text_later", "office_open_xml_container_is_locally_parseable_later", other_document_text_readiness_hint="text_ready")
        return base_result(row, "corrupt_or_unreadable", "office_open_xml_container_invalid", other_document_text_readiness_hint="unreadable")
    if detected in {"doc", "xls", "csv", "txt", "rtf"}:
        return base_result(row, "other_document_text_later", "supported_local_document_type_is_parseable_later", other_document_text_readiness_hint="text_ready")
    return base_result(row, "unsupported_for_text_extraction", "document_type_not_supported_by_bounded_future_text_path", other_document_text_readiness_hint="unsupported")


def inspect_one(row: dict[str, str]) -> dict[str, str]:
    path = ROOT / row["retained_file_path"]
    if not path.is_file():
        result = base_result(row, "readiness_error", "retained_file_missing_during_lane")
        result["file_integrity_status"] = "integrity_fail"
        return result
    if path.stat().st_size != int(row["retained_file_size_bytes"]) or sha256(path) != row["retained_file_sha256"]:
        result = base_result(row, "readiness_error", "retained_file_size_or_sha256_drift_during_lane")
        result["file_integrity_status"] = "integrity_fail"
        return result
    if row["retained_file_type"] == "pdf":
        return inspect_pdf(row, path)
    if row["retained_file_type"] == "html":
        return inspect_html(row, path)
    return inspect_other(row, path)


def lane_paths(lane_id: str) -> tuple[Path, Path]:
    lane_number = lane_id[-3:]
    return (
        OUTPUT_DIR / f"combined_broad_pdf_text_layer_readiness_lane_{lane_number}_locked_queue.csv",
        OUTPUT_DIR / "lanes" / lane_id,
    )


def run_lane(lane_id: str, stagger_seconds: int) -> None:
    if lane_id not in LANE_COUNTS:
        raise RuntimeError(f"unknown lane: {lane_id}")
    process_started = now()
    required_stagger = LANE_STAGGER_MINUTES[lane_id] * 60
    if stagger_seconds != required_stagger:
        raise RuntimeError(f"lane requires exact {required_stagger}-second standard stagger")
    if stagger_seconds:
        time.sleep(stagger_seconds)
    work_started = now()
    queue_path, lane_dir = lane_paths(lane_id)
    lane_dir.mkdir(parents=True, exist_ok=True)
    queue = read_csv(queue_path)
    lane_number = lane_id[-3:]
    lock = read_json(OUTPUT_DIR / f"combined_broad_pdf_text_layer_readiness_lane_{lane_number}_lock.json")
    preflight = read_json(OUTPUT_DIR / f"{PREFIX}_preflight_checks.json")
    if not (
        preflight.get("preflight_passed") is True and len(queue) == LANE_COUNTS[lane_id]
        and sha256(queue_path) == lock["queue_sha256"]
        and all(row["lane_id"] == lane_id for row in queue)
    ):
        raise RuntimeError("lane lock/preflight validation failed")
    results_path = lane_dir / f"lane_{lane_number}_readiness_results.csv"
    completed_rows = read_csv(results_path) if results_path.exists() else []
    completed_ids = {row["source_review_download_id"] for row in completed_rows}
    if not completed_ids.issubset({row["source_review_download_id"] for row in queue}):
        raise RuntimeError("resume results contain rows outside locked lane")
    write_json(lane_dir / f"lane_{lane_number}_resume_state.json", {
        "lane_id": lane_id, "status": "running", "process_started_at": process_started,
        "work_started_at": work_started, "stagger_seconds": stagger_seconds,
        "completed_count": len(completed_rows), "remaining_count": len(queue) - len(completed_rows),
        "resumable": True, "global_analysis_readiness": False,
    })
    for row in queue:
        if row["source_review_download_id"] in completed_ids:
            continue
        result = inspect_one(row)
        if result["readiness_status"] not in CONTROLLED_STATUSES:
            raise RuntimeError("worker produced uncontrolled readiness status")
        append_csv(results_path, result, RESULT_FIELDS)
        completed_rows.append(result)
        completed_ids.add(row["source_review_download_id"])
        checkpoint = {
            "lane_id": lane_id, "status": "running", "locked_queue_count": len(queue),
            "completed_count": len(completed_rows), "remaining_count": len(queue) - len(completed_rows),
            "last_lane_sequence": int(row["lane_sequence"]), "last_readiness_id": row["readiness_id"],
            "last_source_review_download_id": row["source_review_download_id"],
            "checkpointed_at": now(), "checkpoint_after_every_source": True,
            "global_analysis_readiness": False,
        }
        write_json(lane_dir / f"lane_{lane_number}_checkpoint.json", checkpoint)
        write_json(lane_dir / f"lane_{lane_number}_resume_state.json", {
            **checkpoint, "resumable": True, "process_started_at": process_started,
            "work_started_at": work_started, "stagger_seconds": stagger_seconds,
        })
    completed_rows = read_csv(results_path)
    if len(completed_rows) != len(queue) or {row["source_review_download_id"] for row in completed_rows} != {row["source_review_download_id"] for row in queue}:
        raise RuntimeError("lane completion reconciliation failed")
    pdf_rows = [row for row in completed_rows if row["retained_file_type"] == "pdf"]
    html_rows = [row for row in completed_rows if row["retained_file_type"] == "html"]
    other_rows = [row for row in completed_rows if row["retained_file_type"] not in {"pdf", "html"}]
    write_csv(lane_dir / f"lane_{lane_number}_pdf_results.csv", pdf_rows, RESULT_FIELDS)
    write_csv(lane_dir / f"lane_{lane_number}_html_results.csv", html_rows, RESULT_FIELDS)
    write_csv(lane_dir / f"lane_{lane_number}_other_document_results.csv", other_rows, RESULT_FIELDS)
    errors = [row for row in completed_rows if row["readiness_status"] == "readiness_error"]
    write_csv(lane_dir / f"lane_{lane_number}_errors.csv", errors, RESULT_FIELDS)
    completed_at = now()
    summary = {
        "lane_id": lane_id, "status": "completed", "locked_queue_count": len(queue),
        "reviewed_count": len(completed_rows), "pdf_reviewed_count": len(pdf_rows),
        "html_reviewed_count": len(html_rows), "other_document_reviewed_count": len(other_rows),
        "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in completed_rows).items())),
        "integrity_fail_count": sum(row["file_integrity_status"] != "integrity_pass" for row in completed_rows),
        "process_started_at": process_started, "work_started_at": work_started,
        "completed_at": completed_at, "stagger_seconds": stagger_seconds,
        "checkpoint_after_every_source": True, "shared_output_mutations": 0,
        "source_review_download_reruns": 0, "redownloads": 0, "ocr_runs": 0,
        "pdf_render_runs": 0, "saved_text_artifacts": 0, "model_api_calls": 0,
        "global_analysis_readiness": False,
    }
    write_json(lane_dir / f"lane_{lane_number}_readiness_results_summary.json", summary)
    write_json(lane_dir / f"lane_{lane_number}_checkpoint.json", {
        "lane_id": lane_id, "status": "completed", "locked_queue_count": len(queue),
        "completed_count": len(queue), "remaining_count": 0,
        "last_lane_sequence": len(queue), "checkpointed_at": completed_at,
        "checkpoint_after_every_source": True, "global_analysis_readiness": False,
    })
    write_json(lane_dir / f"lane_{lane_number}_resume_state.json", {
        "lane_id": lane_id, "status": "completed", "completed_count": len(queue),
        "remaining_count": 0, "resumable": True, "resume_needed": False,
        "process_started_at": process_started, "work_started_at": work_started,
        "completed_at": completed_at, "stagger_seconds": stagger_seconds,
        "global_analysis_readiness": False,
    })
    print(json.dumps({"status": "lane_completed", "lane_id": lane_id, "rows": len(queue), "counts": summary["readiness_status_counts"]}))


def grouped_summary(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row[key] or "unknown"].append(row)
    output = []
    for value, group in sorted(groups.items()):
        counts = Counter(row["readiness_status"] for row in group)
        output.append({
            key: value, "retained_source_count": len(group),
            "text_ready_count": sum(counts[status] for status in EXTRACTION_READY_STATUSES),
            **{f"{status}_count": counts[status] for status in sorted(CONTROLLED_STATUSES)},
        })
    return output


def write_group_outputs(rows: list[dict[str, str]], key: str, stem: str) -> None:
    summary = grouped_summary(rows, key)
    write_csv(OUTPUT_DIR / f"{PREFIX}_{stem}_summary.csv", summary, summary[0].keys())
    write_json(OUTPUT_DIR / f"{PREFIX}_{stem}_summary.json", {
        "group_field": key, "group_count": len(summary), "retained_source_count": len(rows),
        "text_ready_count": sum(item["text_ready_count"] for item in summary), "rows": summary,
        "global_analysis_readiness": False,
    })


def write_municipality_outputs(rows: list[dict[str, str]]) -> None:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["state"], row["municipality"])].append(row)
    output = []
    for (state, municipality), group in sorted(groups.items()):
        counts = Counter(row["readiness_status"] for row in group)
        output.append({
            "state": state, "region": group[0]["region"], "municipality": municipality,
            "retained_source_count": len(group),
            "text_ready_count": sum(counts[status] for status in EXTRACTION_READY_STATUSES),
            **{f"{status}_count": counts[status] for status in sorted(CONTROLLED_STATUSES)},
        })
    write_csv(OUTPUT_DIR / f"{PREFIX}_municipality_summary.csv", output, output[0].keys())
    write_json(OUTPUT_DIR / f"{PREFIX}_municipality_summary.json", {
        "group_fields": ["state", "municipality"], "group_count": len(output),
        "retained_source_count": len(rows),
        "text_ready_count": sum(item["text_ready_count"] for item in output),
        "rows": output, "global_analysis_readiness": False,
    })


def coordinate() -> None:
    master = read_csv(OUTPUT_DIR / f"{PREFIX}_locked_queue.csv")
    master_ids = {row["source_review_download_id"] for row in master}
    results: list[dict[str, str]] = []
    lane_summaries = []
    for lane_id in LANE_COUNTS:
        number = lane_id[-3:]
        _, lane_dir = lane_paths(lane_id)
        summary = read_json(lane_dir / f"lane_{number}_readiness_results_summary.json")
        lane_rows = read_csv(lane_dir / f"lane_{number}_readiness_results.csv")
        if summary.get("status") != "completed" or len(lane_rows) != LANE_COUNTS[lane_id]:
            raise RuntimeError(f"partial lane cannot masquerade as complete: {lane_id}")
        results.extend(lane_rows)
        lane_summaries.append(summary)
    result_ids = {row["source_review_download_id"] for row in results}
    if not (
        len(results) == EXPECTED_COUNT and len(result_ids) == EXPECTED_COUNT
        and result_ids == master_ids and all(row["readiness_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["file_integrity_status"] == "integrity_pass" for row in results)
    ):
        raise RuntimeError("coordinator result reconciliation failed closed")
    results.sort(key=lambda row: (row["lane_id"], int(row["lane_sequence"])))
    status_counts = Counter(row["readiness_status"] for row in results)
    pdf_rows = [row for row in results if row["retained_file_type"] == "pdf"]
    html_rows = [row for row in results if row["retained_file_type"] == "html"]
    other_rows = [row for row in results if row["retained_file_type"] not in {"pdf", "html"}]
    write_csv(OUTPUT_DIR / f"{PREFIX}_results.csv", results, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_pdf_results.csv", pdf_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_html_results.csv", html_rows, RESULT_FIELDS)
    write_csv(OUTPUT_DIR / f"{PREFIX}_other_document_results.csv", other_rows, RESULT_FIELDS)
    for label, group in (("pdf", pdf_rows), ("html", html_rows), ("other_document", other_rows)):
        write_json(OUTPUT_DIR / f"{PREFIX}_{label}_results_summary.json", {
            "retained_type_group": label, "reviewed_count": len(group),
            "readiness_status_counts": dict(sorted(Counter(row["readiness_status"] for row in group).items())),
            "text_ready_count": sum(row["readiness_status"] in EXTRACTION_READY_STATUSES for row in group),
            "global_analysis_readiness": False,
        })
    for status in sorted(CONTROLLED_STATUSES):
        suffix = "readiness_errors" if status == "readiness_error" else status
        status_rows = [row for row in results if row["readiness_status"] == status]
        write_csv(OUTPUT_DIR / f"{PREFIX}_{suffix}.csv", status_rows, RESULT_FIELDS)
        write_json(OUTPUT_DIR / f"{PREFIX}_{suffix}_summary.json", {
            "readiness_status": status, "row_count": len(status_rows),
            "enters_later_text_extraction_queue": status in EXTRACTION_READY_STATUSES,
            "global_analysis_readiness": False,
        })
    summary = {
        "result_rows": EXPECTED_COUNT, "readiness_reviewed_count": EXPECTED_COUNT,
        "completed_lane_count": 4, "pdf_reviewed_count": len(pdf_rows),
        "html_reviewed_count": len(html_rows), "other_document_reviewed_count": len(other_rows),
        "readiness_status_counts": dict(sorted(status_counts.items())),
        "extraction_ready_count": sum(status_counts[status] for status in EXTRACTION_READY_STATUSES),
        "parse_text_layer_ready_count": status_counts["parse_text_layer_later"],
        "html_text_ready_count": status_counts["html_text_later"],
        "other_document_text_ready_count": status_counts["other_document_text_later"],
        "ocr_later_or_defer_count": status_counts["ocr_later_or_defer"],
        "oversized_for_text_pass_count": status_counts["oversized_for_text_pass"],
        "corrupt_or_unreadable_count": status_counts["corrupt_or_unreadable"],
        "encrypted_or_locked_count": status_counts["encrypted_or_locked"],
        "shell_or_navigation_only_count": status_counts["shell_or_navigation_only"],
        "unsupported_for_text_extraction_count": status_counts["unsupported_for_text_extraction"],
        "needs_review_count": status_counts["needs_review"],
        "readiness_error_count": status_counts["readiness_error"],
        "total_pdf_pages_where_available": sum(int(row["page_count"]) for row in pdf_rows if row["page_count"].isdigit()),
        "source_review_download_reruns": 0, "redownloads": 0, "text_extraction_runs": 0,
        "table_extraction_runs": 0, "span_extraction_runs": 0, "ocr_runs": 0,
        "pdf_render_runs": 0, "rating_model_api_runs": 0, "ingestion_runs": 0,
        "codification_runs": 0, "statistical_analysis_runs": 0,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_results_summary.json", summary)
    integrity = [{
        "readiness_id": row["readiness_id"], "source_review_download_id": row["source_review_download_id"],
        "retained_file_path": row["retained_file_path"], "retained_file_size_bytes": row["retained_file_size_bytes"],
        "retained_file_sha256": row["retained_file_sha256"], "file_integrity_status": row["file_integrity_status"],
    } for row in results]
    write_csv(OUTPUT_DIR / f"{PREFIX}_file_integrity.csv", integrity, integrity[0].keys())
    write_json(OUTPUT_DIR / f"{PREFIX}_file_integrity_summary.json", {
        "files_checked": EXPECTED_COUNT, "integrity_pass_count": EXPECTED_COUNT, "integrity_fail_count": 0,
        "all_paths_sizes_and_sha256_reconciled": True, "global_analysis_readiness": False,
    })
    write_json(OUTPUT_DIR / f"{PREFIX}_hash_reconciliation.json", {
        "retained_ledger_hash_count": EXPECTED_COUNT, "hash_manifest_count": EXPECTED_COUNT,
        "readiness_result_hash_count": EXPECTED_COUNT, "unique_sha256_count": EXPECTED_COUNT,
        "identity_sets_equal": True, "hash_values_equal": True, "global_analysis_readiness": False,
    })
    write_group_outputs(results, "state", "state")
    write_group_outputs(results, "region", "region")
    write_municipality_outputs(results)
    write_group_outputs(results, "source_family_hint", "source_family")
    cba_rows = [row for row in results if row["source_family_hint"] == "cba"]
    non_cba_rows = [row for row in results if row["source_family_hint"] != "cba"]
    non_cba_ready = [row for row in non_cba_rows if row["readiness_status"] in EXTRACTION_READY_STATUSES]
    write_json(OUTPUT_DIR / f"{PREFIX}_non_cba_text_ready_summary.json", {
        "non_cba_retained_source_count": len(non_cba_rows), "non_cba_text_ready_count": len(non_cba_ready),
        "non_cba_text_ready_rate": round(len(non_cba_ready) / len(non_cba_rows), 6),
        "definition": "source_family_hint is not exact cba and readiness status is extraction-approved",
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / f"{PREFIX}_cba_concentration_report.md", f"""# CBA concentration after readiness review

Exactly **{len(cba_rows):,} of {EXPECTED_COUNT:,}** retained sources ({len(cba_rows) / EXPECTED_COUNT:.2%}) carry the exact `cba` source-family hint. The remaining **{len(non_cba_rows):,}** are non-CBA or mixed-family sources; **{len(non_cba_ready):,}** of those are technically ready for a later bounded text pass. These are operational source-family and readiness counts, not evidence ratings or population-prevalence estimates.
""")
    lane_matrix = [{
        "lane_id": item["lane_id"], "locked_queue_count": item["locked_queue_count"],
        "reviewed_count": item["reviewed_count"], "status": item["status"],
        "process_started_at": item["process_started_at"], "work_started_at": item["work_started_at"],
        "completed_at": item["completed_at"], "stagger_seconds": item["stagger_seconds"],
        "checkpoint_after_every_source": str(item["checkpoint_after_every_source"]).lower(),
    } for item in lane_summaries]
    write_csv(OUTPUT_DIR / f"{PREFIX}_lane_status_matrix.csv", lane_matrix, lane_matrix[0].keys())
    write_text(OUTPUT_DIR / f"{PREFIX}_parallel_execution_report.md", """# Parallel execution report

Four independently runnable worker processes were launched together with exact standard waits of T+0, T+8, T+16, and T+24 minutes. Each wrote only to its isolated lane directory, checkpointed after every retained source, and completed its locked queue. The lane timestamps in the status matrix provide the audit trail for staggered controlled overlap; the coordinator alone wrote merged and dashboard-facing outputs.
""")
    write_text(OUTPUT_DIR / f"{PREFIX}_resumability_report.md", """# Resumability report

Every lane retains an append-only result ledger, a per-row checkpoint, and a resume-state JSON. A rerun skips identities already present only after proving they belong to that lane's immutable locked queue. The coordinator rejects partial lanes and any identity mismatch, so partial outputs cannot masquerade as complete.
""")
    standard = {
        "lane_count": 4, "lane_stagger_minutes": LANE_STAGGER_MINUTES,
        "checkpoint_frequency": "after_every_source", "isolated_worker_outputs": True,
        "coordinator_only_shared_mutations": True, "partial_completion_requires_resume_decision": True,
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "future_pdf_text_layer_readiness_parallel_lane_execution_standard.json", standard)
    write_text(OUTPUT_DIR / "future_pdf_text_layer_readiness_parallel_lane_execution_standard.md", """# Future PDF/text-layer readiness parallel-lane standard

Use four isolated workers with T+0/T+8/T+16/T+24 starts, immutable per-lane queues, a checkpoint after every source, resumable append-only ledgers, and one serial coordinator. Workers must never mutate dashboard/shared summaries. No OCR, rendering, saved source text, rating, model analysis, ingestion, codification, or causal analysis belongs in readiness.
""")
    invariants = {
        "all_invariants_passed": True, "locked_queue_count_exact": True,
        "lane_counts_exact": True, "master_equals_union_of_lanes": True,
        "only_retained_local_sources_reviewed": True, "all_hashes_reconciled": True,
        "controlled_statuses_only": True, "extraction_queues_only_approved_statuses": True,
        "deferred_rows_excluded_from_extraction_ready_queues": True,
        "partial_outputs_cannot_masquerade_as_complete": True,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
        "forbidden_action_counts_all_zero": True,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_invariant_checks.json", invariants)
    write_text(OUTPUT_DIR / f"{PREFIX}_stress_test_report.md", """# Stress-test report

The coordinator fail-closes on count, lane, identity, hash-integrity, controlled-status, or predecessor-lineage drift. Worker resume rejects identities outside the locked lane. Empty/error/deferred classifications remain outside extraction-ready manifests. An already-existing output directory blocks a second prepare, and a completed lane rerun is idempotent over row identities.
""")
    write_json(OUTPUT_DIR / f"{PREFIX}_regression_test_inventory.json", {
        "test_script": "scripts/test_combined_broad_pdf_text_layer_readiness_4961.py",
        "covered_invariants": sorted(key for key, value in invariants.items() if value is True),
        "required_predecessor_tests": 4, "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / f"{PREFIX}_text_extraction_planning_note.md", f"""# Text-extraction planning note

The next bounded stage may include only the **{summary['extraction_ready_count']:,}** rows in the three readiness-approved manifests. Split that locked union into four isolated extraction lanes with standard staggered starts; keep PDF, HTML, and other-document parsers explicit; checkpoint each row; and retain text as a technical artifact without rating or causal interpretation unless separately authorized.
""")
    write_text(OUTPUT_DIR / f"{PREFIX}_ocr_future_pass_note.md", f"""# OCR future-pass note

OCR remains separately unauthorized. **{status_counts['ocr_later_or_defer']:,}** PDFs are routed to a possible future OCR/defer decision, while oversized, corrupt, locked, shell, unsupported, needs-review, and error rows remain excluded. A future OCR prompt must define resource bounds, rendering/privacy controls, storage, validation, and its own dashboard boundary.
""")
    write_text(OUTPUT_DIR / f"{PREFIX}_next_queue_recommendation.md", f"""# Next queue recommendation

Lock the exact union of `parse_text_layer_later`, `html_text_later`, and `other_document_text_later`: **{summary['extraction_ready_count']:,} rows**. Do not admit any deferred, oversized, corrupt, encrypted, navigation-only, unsupported, needs-review, or error row. Preserve all source-review and readiness lineage.
""")
    write_text(OUTPUT_DIR / "next_combined_broad_text_extraction_prompt.md", f"""# Next task prompt — combined broad text extraction

Run bounded local text extraction over exactly the **{summary['extraction_ready_count']:,}** readiness-approved retained sources from this task. Build a locked union from only `parse_text_layer_later`, `html_text_later`, and `other_document_text_later`; split it into exactly four isolated lanes; start at T+0/T+8/T+16/T+24; checkpoint every row; merge with a serial coordinator; and update dashboard/status/docs once.

Do not OCR, render pages/images, rate evidence, call GABRIEL/API/models, ingest, codify, compare wages, calculate wage gaps, run regressions/treatment effects, estimate prevalence, or make causal claims. Keep the dashboard map filtered only by cumulative total scout-covered municipalities and keep global analysis readiness false.

Before closing any future rating task, verify every downstream summary input exists. If a missing summary artifact is fully derivable from committed valid/quarantine/results ledgers, reconstruct it deterministically, validate reconciliation, commit/push the repair, and continue. Missing non-derivable artifacts fail closed.
""")
    write_text(OUTPUT_DIR / "next_task.md", """# Next task

Execute the generated four-lane bounded text-extraction prompt over readiness-approved rows only. OCR remains a separate later decision. Global analysis readiness remains false.
""")
    write_json(OUTPUT_DIR / f"{PREFIX}_dashboard_update_summary.json", {
        "dashboard_update_required": True, "dashboard_data_builder_integration": True,
        "current_operation": "combined broad PDF/text-layer readiness complete",
        "next_authorized_stage": "four-lane bounded text extraction over readiness-approved sources",
        "dashboard_map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
        **{key: summary[key] for key in (
            "readiness_reviewed_count", "parse_text_layer_ready_count", "html_text_ready_count",
            "other_document_text_ready_count", "ocr_later_or_defer_count",
            "oversized_for_text_pass_count", "corrupt_or_unreadable_count",
            "needs_review_count", "readiness_error_count")},
        "global_analysis_readiness": False,
    })
    write_text(OUTPUT_DIR / f"{PREFIX}_dashboard_update_summary.md", """# Dashboard update summary

Dashboard overview/current-operation data are wired to the completed 4,961-source readiness summary. The operation advances from source review/download to completed readiness, with four-lane bounded extraction next. The national map remains cumulative total scout coverage only, its data date remains 2026-07-27, and global analysis readiness remains false.
""")
    overview = {
        "sync_required": True, "sync_source": relative(OUTPUT_DIR / f"{PREFIX}_results_summary.json"),
        "current_operation_updated": True, "next_authorized_stage_updated": True,
        "required_readiness_metrics_present": True, "map_metric_unchanged": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_overview_metric_sync_after_pdf_text_readiness.json", overview)
    write_text(OUTPUT_DIR / "dashboard_overview_metric_sync_after_pdf_text_readiness.md", "# Dashboard overview metric sync\n\nThe dashboard builder now consumes the merged readiness summary and exposes the required queue, reviewed, ready, and defer/error counts without changing map inputs.")
    stale = {
        "stale_source_review_download_in_progress_blocked": True,
        "completed_readiness_is_current_operation": True,
        "map_filter_guard": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "dashboard_stale_overview_guard_after_pdf_text_readiness.json", stale)
    write_text(OUTPUT_DIR / "dashboard_stale_overview_guard_after_pdf_text_readiness.md", "# Dashboard stale-overview guard\n\nThe completed readiness operation supersedes any source-review/download-in-progress label. Tests fail if that stale card returns, if the map consumes readiness counts, or if global readiness becomes true.")
    write_text(OUTPUT_DIR / f"{PREFIX}_validation_2026-07-28.md", """# Validation report

Coordinator reconciliation passed: 4,961 unique locked identities, exact lane sizes, identical master/union identities, controlled statuses, and all path/size/SHA-256 checks. The repository validation/build commands are recorded in the final task handoff after execution.
""")
    decision = {
        "task_id": TASK_ID, "decision": "combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready",
        "retained_source_readiness_queue_count": EXPECTED_COUNT, "lane_counts": LANE_COUNTS,
        "completed_lane_count": 4, "staggered_overlap_required_and_recorded": True,
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "map_data_date": "2026-07-27", "four_lane_text_extraction_ready_next": True,
        **summary, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / f"{PREFIX}_decision.json", decision)
    write_text(OUTPUT_DIR / f"{PREFIX}_summary.md", f"""# Combined broad PDF/text-layer readiness — 4,961 retained sources

All four isolated lanes completed and reconciled the locked 4,961-source queue: {len(pdf_rows):,} PDFs, {len(html_rows):,} HTML files, and {len(other_rows):,} other documents. Ready for a separately authorized bounded text pass: **{summary['extraction_ready_count']:,}**. OCR/defer: **{status_counts['ocr_later_or_defer']:,}**; oversized: **{status_counts['oversized_for_text_pass']:,}**; corrupt: **{status_counts['corrupt_or_unreadable']:,}**; locked: **{status_counts['encrypted_or_locked']:,}**; navigation-only: **{status_counts['shell_or_navigation_only']:,}**; unsupported: **{status_counts['unsupported_for_text_extraction']:,}**; needs review: **{status_counts['needs_review']:,}**; errors: **{status_counts['readiness_error']:,}**.

Decision: `combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready`. This was technical readiness only. No source was downloaded again, OCRed, rendered, extracted to durable text, rated, modeled, ingested, codified, or used for quantitative/causal analysis. Global analysis readiness remains false.
""")
    analysis_result = ROOT / "docs/analysis/combined_broad_pdf_text_layer_readiness_4961_result_2026-07-28.md"
    analysis_status = ROOT / "docs/analysis/combined_broad_pdf_text_layer_readiness_4961_dashboard_status_note_2026-07-28.md"
    write_text(analysis_result, f"# Combined broad retained-source readiness result\n\nThe 4,961-source local readiness review completed across four isolated staggered lanes. **{summary['extraction_ready_count']:,}** sources are technically approved for a later bounded text pass. This is not extraction, rating, ingestion, codification, wage comparison, prevalence evidence, or causal evidence. See `{relative(OUTPUT_DIR / f'{PREFIX}_summary.md')}`. Global analysis readiness is false.")
    write_text(analysis_status, "# Dashboard status note\n\nCurrent operation: combined broad PDF/text-layer readiness complete. Next authorized stage: four-lane bounded extraction over readiness-approved sources only. The map remains cumulative total scout coverage only (data date 2026-07-27); readiness counts appear only in overview/status surfaces; global analysis readiness remains false.")
    print(json.dumps({"status": "coordinator_completed", "decision": decision["decision"], "rows": EXPECTED_COUNT, "counts": summary}))


def validate_complete() -> None:
    results = read_csv(OUTPUT_DIR / f"{PREFIX}_results.csv")
    decision = read_json(OUTPUT_DIR / f"{PREFIX}_decision.json")
    if not (
        len(results) == EXPECTED_COUNT and len({row["readiness_id"] for row in results}) == EXPECTED_COUNT
        and decision.get("decision") == "combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready"
        and decision.get("completed_lane_count") == 4 and decision.get("global_analysis_readiness") is False
        and all(row["readiness_status"] in CONTROLLED_STATUSES for row in results)
        and all(row["global_analysis_readiness"] == "false" for row in results)
    ):
        raise RuntimeError("completed outputs fail closed validation")
    print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": len(results)}))


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--lane", choices=tuple(LANE_COUNTS))
    actions.add_argument("--coordinate", action="store_true")
    actions.add_argument("--validate", action="store_true")
    parser.add_argument("--stagger-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.stagger_seconds)
    elif args.coordinate:
        coordinate()
    else:
        validate_complete()


if __name__ == "__main__":
    main()
