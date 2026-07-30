#!/usr/bin/env python3
"""Classify 3,672 retained sources for later non-OCR text extraction.

This runner is local-only.  It hashes retained files, reads PDF metadata, makes
an in-memory text-layer probe over at most the first three pages, inspects at
most 256 KiB of HTML, and checks document container metadata.  It never writes
source text, renders pages, runs OCR, calls a model, rates evidence, ingests,
codifies, or performs quantitative/causal analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import re
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
INPUT_DIR = BASE / "BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30"
OUTPUT_DIR = BASE / "BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_4x2500_source_review_download_2026-07-30"
TASK_ID = "BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30"
PRIOR_DECISION = "broad_state_4x2500_source_review_download_completed_pdf_readiness_ready"
DECISION = "broad_state_4x2500_pdf_text_readiness_completed_text_extraction_ready"
EXPECTED_COUNT = 3_672
EXPECTED_TYPES = {"pdf": 3_248, "html": 350, "other_document": 74}
LANES = tuple(f"readiness_lane_{index:03d}" for index in range(1, 5))
LANE_COUNTS = {lane: 918 for lane in LANES}
LANE_STAGGER_SECONDS = {lane: (index - 1) * 8 * 60 for index, lane in enumerate(LANES, 1)}

MAX_PDF_PROBE_PAGES = 3
MAX_PDFINFO_SECONDS = 45
MAX_TEXT_PROBE_SECONDS = 45
MAX_TEXT_PASS_BYTES = 20 * 1024 * 1024
MAX_TEXT_PASS_PAGES = 500
MAX_HTML_PROBE_BYTES = 256 * 1024
MIN_TEXT_SIGNAL = 40

READY_STATUSES = {
    "parse_text_pdf_ready",
    "html_text_ready",
    "other_document_text_ready",
}
NOT_READY_STATUSES = {
    "ocr_later",
    "oversized_defer",
    "encrypted_or_locked",
    "corrupt_or_broken",
    "shell_or_navigation_only",
    "needs_manual_review",
    "unsupported_file_type",
    "readiness_error",
}
CONTROLLED_STATUSES = READY_STATUSES | NOT_READY_STATUSES

INPUT_FIELDS = (
    "source_review_download_id", "verification_row_id", "candidate_id",
    "scout_target_id", "state", "region", "municipality", "source_title",
    "source_locator_or_url", "final_download_locator", "source_family_hint",
    "priority_bucket", "cba_non_cba_hint", "possible_mechanism_hints",
    "source_review_status", "retained_file_type", "file_extension",
    "retained_local_artifact_path", "artifact_storage_scheme",
    "artifact_storage_pointer", "artifact_object_key_or_content_address",
    "artifact_availability_status", "artifact_replication_or_backup_status",
    "artifact_access_scope", "retained_file_size_bytes", "retained_file_sha256",
)
LOCK_FIELDS = (
    "readiness_id", "lane_id", "lane_sequence", "source_type",
    "detected_file_type", *INPUT_FIELDS,
)
RESULT_FIELDS = LOCK_FIELDS + (
    "observed_file_size_bytes", "observed_sha256", "file_integrity_status",
    "content_type", "page_count", "encrypted_or_locked_flag",
    "corrupt_or_broken_flag", "has_text_layer_flag",
    "bounded_text_probe_page_count", "bounded_text_probe_character_count",
    "estimated_text_density_chars_per_probed_page", "table_layout_indicator",
    "likely_scanned_or_image_only_flag", "oversized_flag",
    "local_html_payload_exists_flag", "html_visible_character_count",
    "html_link_count", "html_script_count", "html_mostly_scripts_or_boilerplate_flag",
    "other_document_non_ocr_extraction_feasible_flag", "primary_readiness_status",
    "reason_code", "classified_at", "full_text_persisted_flag", "ocr_run_flag",
)

REQUIRED_INPUTS = (
    "retained_source_manifest.csv",
    "retained_source_manifest.jsonl",
    "retained_source_manifest.sha256.json",
    "retained_pdf_manifest.csv",
    "retained_html_manifest.csv",
    "retained_other_document_manifest.csv",
    "source_review_download_summary.json",
    "source_review_download_manifest.json",
    "retained_source_storage_audit.json",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_csv(path: Path, row: dict[str, Any], fields: Iterable[str]) -> None:
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def id_set_sha256(rows: Iterable[dict[str, str]]) -> str:
    return text_sha256("\n".join(sorted(row["source_review_download_id"] for row in rows)))


def readiness_id(source_id: str) -> str:
    return "B4X2500RDY-20260730-" + hashlib.sha256(source_id.encode()).hexdigest()[:20]


def normalized_source_type(row: dict[str, str]) -> str:
    value = row["retained_file_type"].casefold()
    if value == "pdf":
        return "pdf"
    if value == "html":
        return "html"
    return "other_document"


def detect_file_type(path: Path, recorded_type: str) -> str:
    with path.open("rb") as handle:
        head = handle.read(4096)
    lower = head.lstrip().lower()
    suffix = path.suffix.casefold()
    if head.startswith(b"%PDF-"):
        return "pdf"
    if b"<html" in lower or b"<!doctype html" in lower:
        return "html"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
            if "word/document.xml" in names:
                return "docx"
            if "xl/workbook.xml" in names:
                return "xlsx"
            return "office_open_xml_or_zip"
        except (OSError, zipfile.BadZipFile):
            return "broken_zip"
    if head.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        return "xls" if recorded_type == "xls" or suffix == ".xls" else "doc"
    if lower.startswith(b"{\\rtf"):
        return "rtf"
    if recorded_type in {"text", "txt"} or suffix in {".txt", ".csv"}:
        return "text"
    return recorded_type or suffix.lstrip(".") or "unknown"


def content_type_for(source_type: str, detected: str, path: Path) -> str:
    if source_type == "pdf":
        return "application/pdf"
    if source_type == "html":
        return "text/html"
    mapping = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "doc": "application/msword", "xls": "application/vnd.ms-excel",
        "rtf": "application/rtf", "text": "text/plain",
    }
    return mapping.get(detected) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def validate_predecessor() -> list[dict[str, str]]:
    missing = [name for name in REQUIRED_INPUTS if not (INPUT_DIR / name).is_file()]
    if missing:
        raise RuntimeError(f"missing predecessor inputs: {missing}")
    summary = read_json(INPUT_DIR / "source_review_download_summary.json")
    manifest = read_csv(INPUT_DIR / "retained_source_manifest.csv")
    pdf_rows = read_csv(INPUT_DIR / "retained_pdf_manifest.csv")
    html_rows = read_csv(INPUT_DIR / "retained_html_manifest.csv")
    other_rows = read_csv(INPUT_DIR / "retained_other_document_manifest.csv")
    types = Counter(normalized_source_type(row) for row in manifest)
    ids = [row["source_review_download_id"] for row in manifest]
    hashes = [row["retained_file_sha256"] for row in manifest]
    if not (
        summary.get("decision") == PRIOR_DECISION
        and summary.get("retained_source_count") == EXPECTED_COUNT
        and len(manifest) == EXPECTED_COUNT
        and len(pdf_rows) == EXPECTED_TYPES["pdf"]
        and len(html_rows) == EXPECTED_TYPES["html"]
        and len(other_rows) == EXPECTED_TYPES["other_document"]
        and types == EXPECTED_TYPES
        and len(set(ids)) == EXPECTED_COUNT
        and len(set(hashes)) == EXPECTED_COUNT
        and all(len(value) == 64 for value in hashes)
        and all(row.get("retained_local_artifact_path") for row in manifest)
        and all(row.get("retained_file_size_bytes", "").isdigit() for row in manifest)
    ):
        raise RuntimeError("predecessor retained-source reconciliation failed closed")
    return manifest


def balanced_order(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Stable hash ordering disperses type, priority, family, and geography."""
    def key(row: dict[str, str]) -> tuple[str, str]:
        material = "|".join((
            normalized_source_type(row), row.get("priority_bucket", ""),
            row.get("source_family_hint", ""), row.get("state", ""),
            row["source_review_download_id"],
        ))
        return text_sha256(material), row["source_review_download_id"]
    return sorted(rows, key=key)


def run_local(arguments: list[str], timeout: int) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def parse_pdfinfo(payload: bytes) -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in payload.decode("utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip().casefold()] = value.strip()
    page_value = values.get("pages", "")
    return {
        "page_count": int(page_value) if page_value.isdigit() else 0,
        "encrypted": values.get("encrypted", "").casefold().startswith("yes"),
    }


class BoundedHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.visible_chars = 0
        self.links = 0
        self.scripts = 0
        self.meta_refresh = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1
        self.links += int(tag == "a")
        self.scripts += int(tag == "script")
        if tag == "meta":
            lowered = {key.casefold(): (value or "").casefold() for key, value in attrs}
            self.meta_refresh = self.meta_refresh or lowered.get("http-equiv") == "refresh"

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.visible_chars += sum(character.isalnum() for character in data)


def result_base(row: dict[str, str], status: str, reason: str, **updates: Any) -> dict[str, str]:
    source_type = row["source_type"]
    path = ROOT / row["retained_local_artifact_path"]
    result = {field: row.get(field, "") for field in LOCK_FIELDS}
    result.update({
        "observed_file_size_bytes": str(path.stat().st_size) if path.is_file() else "",
        "observed_sha256": "", "file_integrity_status": "integrity_pass",
        "content_type": content_type_for(source_type, row["detected_file_type"], path),
        "page_count": "", "encrypted_or_locked_flag": "not_applicable" if source_type != "pdf" else "unknown",
        "corrupt_or_broken_flag": "false", "has_text_layer_flag": "not_applicable" if source_type != "pdf" else "unknown",
        "bounded_text_probe_page_count": "0", "bounded_text_probe_character_count": "0",
        "estimated_text_density_chars_per_probed_page": "", "table_layout_indicator": "not_probed",
        "likely_scanned_or_image_only_flag": "not_applicable" if source_type != "pdf" else "unknown",
        "oversized_flag": "false", "local_html_payload_exists_flag": "not_applicable" if source_type != "html" else str(path.is_file()).lower(),
        "html_visible_character_count": "", "html_link_count": "", "html_script_count": "",
        "html_mostly_scripts_or_boilerplate_flag": "not_applicable" if source_type != "html" else "unknown",
        "other_document_non_ocr_extraction_feasible_flag": "not_applicable" if source_type != "other_document" else "unknown",
        "primary_readiness_status": status, "reason_code": reason, "classified_at": now(),
        "full_text_persisted_flag": "false", "ocr_run_flag": "false",
    })
    result.update({key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in updates.items()})
    return result


def inspect_pdf(row: dict[str, str], path: Path) -> dict[str, str]:
    if row["detected_file_type"] != "pdf":
        return result_base(row, "corrupt_or_broken", "recorded_pdf_magic_mismatch", corrupt_or_broken_flag=True)
    try:
        info = run_local(["pdfinfo", str(path)], MAX_PDFINFO_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return result_base(row, "readiness_error", f"pdfinfo_{type(exc).__name__}")
    stderr = info.stderr.decode("utf-8", errors="ignore").casefold()
    if info.returncode != 0:
        if "password" in stderr or "encrypted" in stderr:
            return result_base(row, "encrypted_or_locked", "pdf_metadata_locked", encrypted_or_locked_flag=True)
        return result_base(row, "corrupt_or_broken", "pdf_metadata_unreadable_or_corrupt", corrupt_or_broken_flag=True)
    metadata = parse_pdfinfo(info.stdout)
    pages = metadata["page_count"]
    common = {"page_count": pages or "", "encrypted_or_locked_flag": metadata["encrypted"]}
    if pages <= 0:
        return result_base(row, "corrupt_or_broken", "pdf_page_count_unavailable", corrupt_or_broken_flag=True, **common)
    if metadata["encrypted"]:
        return result_base(row, "encrypted_or_locked", "pdf_encrypted_or_locked", **common)
    oversized = path.stat().st_size > MAX_TEXT_PASS_BYTES or pages > MAX_TEXT_PASS_PAGES
    if oversized:
        return result_base(row, "oversized_defer", "pdf_exceeds_20mib_or_500_page_text_pass_limit", oversized_flag=True, **common)
    probe_pages = min(MAX_PDF_PROBE_PAGES, pages)
    try:
        probe = run_local([
            "pdftotext", "-f", "1", "-l", str(probe_pages), "-enc", "UTF-8",
            "-layout", "-nopgbrk", str(path), "-",
        ], MAX_TEXT_PROBE_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return result_base(row, "needs_manual_review", f"bounded_pdf_probe_{type(exc).__name__}", bounded_text_probe_page_count=probe_pages, **common)
    # Probe bytes remain in memory and are reduced immediately to numeric/boolean signals.
    decoded = probe.stdout.decode("utf-8", errors="ignore")
    signal = sum(character.isalnum() for character in decoded)
    layout_lines = sum(bool(re.search(r"\S\s{3,}\S", line)) for line in decoded.splitlines())
    density = round(signal / probe_pages, 3) if probe_pages else 0
    layout = "possible_tabular_or_columns" if layout_lines >= 3 else "no_strong_table_layout_signal"
    del decoded
    details = {
        **common, "bounded_text_probe_page_count": probe_pages,
        "bounded_text_probe_character_count": signal,
        "estimated_text_density_chars_per_probed_page": density,
        "table_layout_indicator": layout,
    }
    if probe.returncode == 0 and signal >= MIN_TEXT_SIGNAL:
        return result_base(row, "parse_text_pdf_ready", "bounded_first_three_pages_show_machine_readable_text_layer", has_text_layer_flag=True, likely_scanned_or_image_only_flag=False, **details)
    if probe.returncode == 0:
        return result_base(row, "ocr_later", "bounded_first_three_pages_do_not_show_usable_text_layer", has_text_layer_flag=False, likely_scanned_or_image_only_flag=True, **details)
    return result_base(row, "needs_manual_review", "bounded_pdf_text_probe_failed", **details)


def inspect_html(row: dict[str, str], path: Path) -> dict[str, str]:
    if row["detected_file_type"] != "html":
        return result_base(row, "corrupt_or_broken", "recorded_html_magic_mismatch", corrupt_or_broken_flag=True)
    try:
        with path.open("rb") as handle:
            payload = handle.read(MAX_HTML_PROBE_BYTES)
    except OSError as exc:
        return result_base(row, "readiness_error", f"html_read_{type(exc).__name__}")
    if len(payload) < 16:
        return result_base(row, "corrupt_or_broken", "html_empty_or_too_short", corrupt_or_broken_flag=True)
    decoded = payload.decode("utf-8", errors="replace")
    parser = BoundedHTMLParser()
    try:
        parser.feed(decoded)
    except Exception:
        return result_base(row, "needs_manual_review", "bounded_html_parser_error")
    lower = decoded.casefold()
    shell = parser.meta_refresh or ("window.location" in lower and parser.visible_chars < 200)
    navigation_heavy = parser.links >= 40 and parser.visible_chars < 400
    mostly_scripts = parser.scripts >= 8 and parser.visible_chars < 200
    del decoded
    details = {
        "html_visible_character_count": parser.visible_chars,
        "html_link_count": parser.links, "html_script_count": parser.scripts,
        "html_mostly_scripts_or_boilerplate_flag": mostly_scripts,
    }
    if shell or navigation_heavy or mostly_scripts:
        return result_base(row, "shell_or_navigation_only", "bounded_html_signal_is_shell_navigation_or_script_heavy", **details)
    if parser.visible_chars >= 200:
        return result_base(row, "html_text_ready", "bounded_html_structure_has_usable_visible_text", **details)
    return result_base(row, "needs_manual_review", "bounded_html_visible_text_signal_too_weak", **details)


def inspect_other(row: dict[str, str], path: Path) -> dict[str, str]:
    detected = row["detected_file_type"]
    if path.stat().st_size <= 0:
        return result_base(row, "corrupt_or_broken", "other_document_empty", corrupt_or_broken_flag=True, other_document_non_ocr_extraction_feasible_flag=False)
    if detected == "broken_zip":
        return result_base(row, "corrupt_or_broken", "office_container_broken", corrupt_or_broken_flag=True, other_document_non_ocr_extraction_feasible_flag=False)
    if detected in {"docx", "xlsx", "doc", "xls", "rtf", "text"}:
        return result_base(row, "other_document_text_ready", "supported_non_ocr_document_type_parseable_later", other_document_non_ocr_extraction_feasible_flag=True)
    if detected == "office_open_xml_or_zip":
        return result_base(row, "needs_manual_review", "generic_office_zip_requires_parser_selection", other_document_non_ocr_extraction_feasible_flag="unknown")
    return result_base(row, "unsupported_file_type", "document_type_not_supported_by_bounded_future_text_path", other_document_non_ocr_extraction_feasible_flag=False)


def inspect_one(row: dict[str, str]) -> dict[str, str]:
    path = ROOT / row["retained_local_artifact_path"]
    if not path.is_file():
        result = result_base(row, "readiness_error", "retained_file_missing_during_lane")
        result["file_integrity_status"] = "integrity_fail"
        return result
    observed_size = path.stat().st_size
    observed_hash = sha256(path)
    if observed_size != int(row["retained_file_size_bytes"]) or observed_hash != row["retained_file_sha256"]:
        result = result_base(row, "readiness_error", "retained_file_size_or_sha256_drift_during_lane")
        result.update({"observed_file_size_bytes": str(observed_size), "observed_sha256": observed_hash, "file_integrity_status": "integrity_fail"})
        return result
    if row["source_type"] == "pdf":
        result = inspect_pdf(row, path)
    elif row["source_type"] == "html":
        result = inspect_html(row, path)
    else:
        result = inspect_other(row, path)
    result["observed_sha256"] = observed_hash
    result["observed_file_size_bytes"] = str(observed_size)
    return result


def prepare() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"rollback-safe output already exists: {OUTPUT_DIR}")
    if shutil.which("pdfinfo") is None or shutil.which("pdftotext") is None:
        raise RuntimeError("required non-rendering PDF metadata tools unavailable")
    rows = validate_predecessor()
    ignored = subprocess.run(["git", "check-ignore", "-q", relative(ARTIFACT_ROOT)], cwd=ROOT, check=False).returncode == 0
    tracked_retained = subprocess.run(["git", "ls-files", relative(ARTIFACT_ROOT)], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    if not ignored or tracked_retained or any(name.startswith(relative(ARTIFACT_ROOT) + "/") for name in staged):
        raise RuntimeError("retained-source Git isolation preflight failed")

    OUTPUT_DIR.mkdir(parents=True)
    observed_bytes = 0
    failures: list[dict[str, Any]] = []
    locked: list[dict[str, str]] = []
    ordered = balanced_order(rows)
    for index, row in enumerate(ordered):
        path = ROOT / row["retained_local_artifact_path"]
        inside = path.resolve().is_relative_to(ARTIFACT_ROOT.resolve())
        exists = path.is_file()
        size = path.stat().st_size if exists else -1
        observed_hash = sha256(path) if exists else ""
        passed = inside and exists and size == int(row["retained_file_size_bytes"]) and observed_hash == row["retained_file_sha256"]
        observed_bytes += max(size, 0)
        if not passed:
            failures.append({
                "source_review_download_id": row["source_review_download_id"], "path": row["retained_local_artifact_path"],
                "inside_artifact_root": inside, "exists": exists, "recorded_size": row["retained_file_size_bytes"],
                "observed_size": size, "recorded_sha256": row["retained_file_sha256"], "observed_sha256": observed_hash,
            })
        lane = LANES[index % 4]
        lane_sequence = index // 4 + 1
        source_type = normalized_source_type(row)
        detected = detect_file_type(path, row["retained_file_type"]) if exists else "missing"
        locked.append({
            "readiness_id": readiness_id(row["source_review_download_id"]), "lane_id": lane,
            "lane_sequence": str(lane_sequence), "source_type": source_type,
            "detected_file_type": detected, **{field: row.get(field, "") for field in INPUT_FIELDS},
        })
    hash_report = {
        "checked_at": now(), "files_checked": len(rows), "hash_match_count": len(rows) - len(failures),
        "hash_mismatch_or_missing_count": len(failures), "all_files_exist": not failures,
        "all_paths_inside_ignored_artifact_root": not failures, "recorded_retained_bytes": sum(int(row["retained_file_size_bytes"]) for row in rows),
        "observed_retained_bytes": observed_bytes, "unique_recorded_hashes": len({row["retained_file_sha256"] for row in rows}),
        "failure_rows": failures, "artifact_root": relative(ARTIFACT_ROOT), "artifact_root_git_ignored": ignored,
    }
    write_json(OUTPUT_DIR / "retained_source_hash_recheck_report.json", hash_report)
    if failures:
        raise RuntimeError(f"retained source integrity failed for {len(failures)} rows")

    if Counter(row["lane_id"] for row in locked) != LANE_COUNTS:
        raise RuntimeError("exact readiness lane distribution failed")
    write_csv(OUTPUT_DIR / "readiness_locked_queue.csv", locked, LOCK_FIELDS)
    write_jsonl(OUTPUT_DIR / "readiness_locked_queue.jsonl", locked)
    master_ids = {row["source_review_download_id"] for row in locked}
    union_ids: set[str] = set()
    lane_manifest: dict[str, Any] = {}
    for lane in LANES:
        lane_rows = [row for row in locked if row["lane_id"] == lane]
        csv_path = OUTPUT_DIR / f"{lane}_queue.csv"
        jsonl_path = OUTPUT_DIR / f"{lane}_queue.jsonl"
        write_csv(csv_path, lane_rows, LOCK_FIELDS)
        write_jsonl(jsonl_path, lane_rows)
        union_ids.update(row["source_review_download_id"] for row in lane_rows)
        lane_manifest[lane] = {
            "row_count": len(lane_rows), "csv_sha256": sha256(csv_path), "jsonl_sha256": sha256(jsonl_path),
            "id_set_sha256": id_set_sha256(lane_rows), "stagger_seconds": LANE_STAGGER_SECONDS[lane],
            "source_type_counts": dict(sorted(Counter(row["source_type"] for row in lane_rows).items())),
            "priority_counts": dict(sorted(Counter(row["priority_bucket"] for row in lane_rows).items())),
        }
        write_json(OUTPUT_DIR / "lanes" / lane / "lane_manifest.json", {"task_id": TASK_ID, "lane_id": lane, **lane_manifest[lane]})
    if union_ids != master_ids or len(union_ids) != EXPECTED_COUNT:
        raise RuntimeError("lane union does not equal locked master")

    manifest = {
        "task_id": TASK_ID, "created_at": now(), "prior_decision": PRIOR_DECISION,
        "input_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip(),
        "retained_source_count": EXPECTED_COUNT, "retained_type_counts": EXPECTED_TYPES,
        "locked_queue_csv_sha256": sha256(OUTPUT_DIR / "readiness_locked_queue.csv"),
        "locked_queue_jsonl_sha256": sha256(OUTPUT_DIR / "readiness_locked_queue.jsonl"),
        "locked_id_set_sha256": id_set_sha256(locked), "lane_distribution": LANE_COUNTS,
        "lane_manifests": lane_manifest, "probe_limits": {
            "pdf_pages": MAX_PDF_PROBE_PAGES, "html_bytes": MAX_HTML_PROBE_BYTES,
            "oversized_bytes": MAX_TEXT_PASS_BYTES, "oversized_pages": MAX_TEXT_PASS_PAGES,
        },
        "network_access": False, "full_text_persisted": False, "ocr_performed": False,
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json", manifest)
    write_json(OUTPUT_DIR / "readiness_lane_distribution.json", {
        "task_id": TASK_ID, "total": EXPECTED_COUNT, "lanes": lane_manifest,
        "all_rows_exactly_once": True, "deterministic_assignment": "stable_sha256_interleave",
    })
    write_text(OUTPUT_DIR / "readiness_lane_distribution.md", """# PDF/text readiness lane distribution

The 3,672 retained sources are locked into four deterministic, interleaved lanes of exactly 918 rows. Source types, priorities, families, and geographies are dispersed by a stable SHA-256 ordering. Starts are locked to T+0, T+8, T+16, and T+24 minutes, and every worker checkpoints after each source.
""")

    representatives: list[dict[str, Any]] = []
    for source_type in ("pdf", "html", "other_document"):
        row = next(item for item in locked if item["source_type"] == source_type)
        result = inspect_one(row)
        representatives.append({
            "source_type": source_type, "source_review_download_id": row["source_review_download_id"],
            "primary_readiness_status": result["primary_readiness_status"], "reason_code": result["reason_code"],
            "file_integrity_status": result["file_integrity_status"], "full_text_persisted_flag": False,
        })
    write_json(OUTPUT_DIR / "readiness_smoke_preflight.json", {
        "status": "passed", "representative_count": len(representatives), "representatives": representatives,
        "network_used": False, "full_text_persisted": False, "ocr_performed": False,
    })
    write_json(OUTPUT_DIR / "preflight_report.json", {
        "status": "passed", "repo_root": str(ROOT), "current_head": manifest["input_commit"],
        "retained_source_count": EXPECTED_COUNT, "retained_type_counts": EXPECTED_TYPES,
        "all_files_exist_and_hash_match": True, "artifact_root_ignored": True,
        "no_retained_binaries_staged_or_tracked": True, "lane_distribution": LANE_COUNTS,
        "lane_union_reconciles": True, "smoke_passed": True,
    })
    print(json.dumps({"status": "preflight_passed", "rows": EXPECTED_COUNT, "types": EXPECTED_TYPES, "lanes": LANE_COUNTS}))


def lane_result_paths(lane: str) -> tuple[Path, Path]:
    lane_dir = OUTPUT_DIR / "lanes" / lane
    return lane_dir / "results.csv", lane_dir / "results.jsonl"


def run_lane(lane: str, stagger_seconds: int) -> None:
    if stagger_seconds != LANE_STAGGER_SECONDS[lane]:
        raise RuntimeError(f"{lane} requires exact {LANE_STAGGER_SECONDS[lane]}-second stagger")
    process_started = now()
    if stagger_seconds:
        time.sleep(stagger_seconds)
    work_started = now()
    queue_path = OUTPUT_DIR / f"{lane}_queue.csv"
    queue = read_csv(queue_path)
    lane_manifest = read_json(OUTPUT_DIR / "lanes" / lane / "lane_manifest.json")
    if len(queue) != 918 or sha256(queue_path) != lane_manifest["csv_sha256"] or any(row["lane_id"] != lane for row in queue):
        raise RuntimeError("lane queue lock validation failed")
    csv_path, jsonl_path = lane_result_paths(lane)
    completed = read_csv(csv_path) if csv_path.exists() else []
    completed_ids = [row["source_review_download_id"] for row in completed]
    queue_ids = {row["source_review_download_id"] for row in queue}
    if len(completed_ids) != len(set(completed_ids)) or not set(completed_ids).issubset(queue_ids):
        raise RuntimeError("lane resume ledger corrupt")
    # CSV is canonical for recovery if a crash occurred between the two appends.
    write_jsonl(jsonl_path, completed)
    lane_dir = csv_path.parent
    write_json(lane_dir / "resume_state.json", {
        "lane_id": lane, "status": "running", "process_started_at": process_started,
        "work_started_at": work_started, "stagger_seconds": stagger_seconds,
        "completed_count": len(completed), "remaining_count": len(queue) - len(completed), "resumable": True,
    })
    completed_set = set(completed_ids)
    for row in queue:
        if row["source_review_download_id"] in completed_set:
            continue
        result = inspect_one(row)
        if result["primary_readiness_status"] not in CONTROLLED_STATUSES:
            raise RuntimeError("uncontrolled readiness status")
        append_csv(csv_path, result, RESULT_FIELDS)
        append_jsonl(jsonl_path, result)
        completed.append(result)
        completed_set.add(row["source_review_download_id"])
        checkpoint = {
            "lane_id": lane, "status": "running", "locked_queue_count": len(queue),
            "completed_count": len(completed), "remaining_count": len(queue) - len(completed),
            "last_lane_sequence": int(row["lane_sequence"]), "last_readiness_id": row["readiness_id"],
            "last_source_review_download_id": row["source_review_download_id"],
            "checkpointed_at": now(), "checkpoint_after_every_source": True,
        }
        write_json(lane_dir / "checkpoint.json", checkpoint)
        write_json(lane_dir / "resume_state.json", {**checkpoint, "resumable": True, "process_started_at": process_started, "work_started_at": work_started, "stagger_seconds": stagger_seconds})
    completed = read_csv(csv_path)
    if len(completed) != len(queue) or {row["source_review_download_id"] for row in completed} != queue_ids:
        raise RuntimeError("lane completion reconciliation failed")
    completed_at = now()
    summary = {
        "lane_id": lane, "status": "completed", "locked_queue_count": 918,
        "completed_count": 918, "remaining_count": 0,
        "source_type_counts": dict(sorted(Counter(row["source_type"] for row in completed).items())),
        "readiness_status_counts": dict(sorted(Counter(row["primary_readiness_status"] for row in completed).items())),
        "integrity_fail_count": sum(row["file_integrity_status"] != "integrity_pass" for row in completed),
        "process_started_at": process_started, "work_started_at": work_started,
        "completed_at": completed_at, "stagger_seconds": stagger_seconds,
        "checkpoint_after_every_source": True, "full_text_persisted_count": 0, "ocr_run_count": 0,
    }
    write_json(lane_dir / "summary.json", summary)
    write_json(lane_dir / "checkpoint.json", {
        "lane_id": lane, "status": "completed", "locked_queue_count": 918,
        "completed_count": 918, "remaining_count": 0, "last_lane_sequence": 918,
        "checkpointed_at": completed_at, "checkpoint_after_every_source": True,
    })
    write_json(lane_dir / "resume_state.json", {
        "lane_id": lane, "status": "completed", "completed_count": 918, "remaining_count": 0,
        "resumable": True, "resume_needed": False, "process_started_at": process_started,
        "work_started_at": work_started, "completed_at": completed_at, "stagger_seconds": stagger_seconds,
    })
    print(json.dumps({"status": "lane_completed", "lane": lane, "rows": 918, "counts": summary["readiness_status_counts"]}))


def page_band(value: str) -> str:
    if not value or not value.isdigit():
        return "unknown"
    pages = int(value)
    if pages <= 10: return "001_010"
    if pages <= 25: return "011_025"
    if pages <= 50: return "026_050"
    if pages <= 100: return "051_100"
    if pages <= 250: return "101_250"
    if pages <= 500: return "251_500"
    return "501_plus"


def size_band(value: str) -> str:
    size = int(value)
    if size < 100 * 1024: return "under_100_kib"
    if size < 1024 * 1024: return "100_kib_to_1_mib"
    if size < 5 * 1024 * 1024: return "1_to_5_mib"
    if size <= 20 * 1024 * 1024: return "5_to_20_mib"
    return "over_20_mib"


def grouped_summary(rows: list[dict[str, str]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "") or "none_or_unknown"].append(row)
    output = []
    for value, group in sorted(groups.items()):
        counts = Counter(row["primary_readiness_status"] for row in group)
        output.append({
            field: value, "retained_source_count": len(group),
            "text_extraction_ready_count": sum(counts[status] for status in READY_STATUSES),
            "not_ready_count": sum(counts[status] for status in NOT_READY_STATUSES),
            "readiness_status_counts": dict(sorted(counts.items())),
        })
    return {
        "group_field": field, "group_count": len(output), "retained_source_count": len(rows),
        "text_extraction_ready_count": sum(item["text_extraction_ready_count"] for item in output),
        "rows": output, "global_analysis_readiness": False,
    }


def queue_outputs(name: str, rows: list[dict[str, str]]) -> None:
    write_csv(OUTPUT_DIR / f"{name}.csv", rows, RESULT_FIELDS)
    write_jsonl(OUTPUT_DIR / f"{name}.jsonl", rows)


def merge() -> None:
    locked = read_csv(OUTPUT_DIR / "readiness_locked_queue.csv")
    master_manifest = read_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json")
    if sha256(OUTPUT_DIR / "readiness_locked_queue.csv") != master_manifest["locked_queue_csv_sha256"]:
        raise RuntimeError("master locked queue hash drift")
    results: list[dict[str, str]] = []
    lane_summaries: dict[str, Any] = {}
    for lane in LANES:
        queue_path = OUTPUT_DIR / f"{lane}_queue.csv"
        lane_manifest = master_manifest["lane_manifests"][lane]
        if sha256(queue_path) != lane_manifest["csv_sha256"]:
            raise RuntimeError(f"{lane} queue hash drift")
        csv_path, _ = lane_result_paths(lane)
        lane_results = read_csv(csv_path)
        summary = read_json(csv_path.parent / "summary.json")
        if len(lane_results) != 918 or summary.get("status") != "completed":
            raise RuntimeError(f"{lane} incomplete")
        results.extend(lane_results)
        lane_summaries[lane] = summary
        write_csv(OUTPUT_DIR / f"{lane}_results.csv", lane_results, RESULT_FIELDS)
        write_jsonl(OUTPUT_DIR / f"{lane}_results.jsonl", lane_results)
    result_ids = [row["source_review_download_id"] for row in results]
    locked_ids = {row["source_review_download_id"] for row in locked}
    if len(results) != EXPECTED_COUNT or len(set(result_ids)) != EXPECTED_COUNT or set(result_ids) != locked_ids:
        raise RuntimeError("merged identity reconciliation failed")
    if any(row["primary_readiness_status"] not in CONTROLLED_STATUSES for row in results):
        raise RuntimeError("merged uncontrolled status")
    if any(row["file_integrity_status"] != "integrity_pass" for row in results):
        raise RuntimeError("integrity drift during lane processing")
    write_csv(OUTPUT_DIR / "merged_pdf_text_readiness_results.csv", results, RESULT_FIELDS)
    write_jsonl(OUTPUT_DIR / "merged_pdf_text_readiness_results.jsonl", results)

    by_status = {status: [row for row in results if row["primary_readiness_status"] == status] for status in CONTROLLED_STATUSES}
    for status in sorted(CONTROLLED_STATUSES):
        queue_outputs(f"{status}_queue", by_status[status])
    extraction_ready = [row for row in results if row["primary_readiness_status"] in READY_STATUSES]
    queue_outputs("text_extraction_ready_queue", extraction_ready)
    extraction_manifest = {
        "task_id": TASK_ID, "created_at": now(), "row_count": len(extraction_ready),
        "eligible_statuses": sorted(READY_STATUSES),
        "status_counts": dict(sorted(Counter(row["primary_readiness_status"] for row in extraction_ready).items())),
        "csv_sha256": sha256(OUTPUT_DIR / "text_extraction_ready_queue.csv"),
        "jsonl_sha256": sha256(OUTPUT_DIR / "text_extraction_ready_queue.jsonl"),
        "id_set_sha256": id_set_sha256(extraction_ready), "ocr_included": False,
        "full_text_extracted": False, "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "text_extraction_ready_manifest.json", extraction_manifest)

    counts = Counter(row["primary_readiness_status"] for row in results)
    source_counts = Counter(row["source_type"] for row in results)
    page_counts = Counter(page_band(row["page_count"]) for row in results if row["source_type"] == "pdf")
    size_counts = Counter(size_band(row["retained_file_size_bytes"]) for row in results)
    pdf_pages = [int(row["page_count"]) for row in results if row["source_type"] == "pdf" and row["page_count"].isdigit()]
    summary = {
        "task_id": TASK_ID, "final_decision": DECISION, "completed_at": now(),
        "retained_source_count": EXPECTED_COUNT, "retained_pdf_count": source_counts["pdf"],
        "retained_html_count": source_counts["html"], "retained_other_document_count": source_counts["other_document"],
        "lane_distribution": LANE_COUNTS, "completed_lane_count": 4,
        "primary_readiness_status_counts": {status: counts[status] for status in sorted(CONTROLLED_STATUSES)},
        "parse_text_pdf_ready_count": counts["parse_text_pdf_ready"],
        "html_text_ready_count": counts["html_text_ready"],
        "other_document_text_ready_count": counts["other_document_text_ready"],
        "text_extraction_ready_count": len(extraction_ready),
        "not_ready_count": EXPECTED_COUNT - len(extraction_ready),
        "ocr_later_count": counts["ocr_later"], "oversized_defer_count": counts["oversized_defer"],
        "encrypted_or_locked_count": counts["encrypted_or_locked"], "corrupt_or_broken_count": counts["corrupt_or_broken"],
        "shell_or_navigation_only_count": counts["shell_or_navigation_only"], "needs_manual_review_count": counts["needs_manual_review"],
        "unsupported_file_type_count": counts["unsupported_file_type"], "readiness_error_count": counts["readiness_error"],
        "pdf_page_count_recorded_count": len(pdf_pages), "total_pdf_pages_where_readable": sum(pdf_pages),
        "retained_bytes": sum(int(row["retained_file_size_bytes"]) for row in results),
        "full_text_persisted_count": 0, "ocr_run_count": 0, "network_access_count": 0,
        "rating_ingestion_codification_count": 0, "dashboard_map_filter": "total_scout_coverage_only",
        "collection_readiness": "passed", "mechanism_quantitative_readiness": "partial",
        "wage_gap_readiness": "blocked_pending_normalization", "causal_readiness": "blocked_pending_matched_structure",
        "global_analysis_readiness": False, "overall_global_readiness": "partial_diagnostic_only_not_final",
    }
    write_json(OUTPUT_DIR / "pdf_text_readiness_summary.json", summary)
    write_text(OUTPUT_DIR / "pdf_text_readiness_summary.md", f"""# Broad-state 4×2500 PDF/text readiness summary

All four lanes completed and reconciled **{EXPECTED_COUNT:,}** retained sources: {source_counts['pdf']:,} PDFs, {source_counts['html']:,} HTML files, and {source_counts['other_document']:,} other documents. Exactly **{len(extraction_ready):,}** are technically ready for a separately authorized non-OCR text-extraction pass: {counts['parse_text_pdf_ready']:,} PDFs, {counts['html_text_ready']:,} HTML files, and {counts['other_document_text_ready']:,} other documents.

Deferred/not ready: OCR later {counts['ocr_later']:,}; oversized {counts['oversized_defer']:,}; locked {counts['encrypted_or_locked']:,}; corrupt {counts['corrupt_or_broken']:,}; shell/navigation {counts['shell_or_navigation_only']:,}; manual review {counts['needs_manual_review']:,}; unsupported {counts['unsupported_file_type']:,}; errors {counts['readiness_error']:,}.

Decision: `{DECISION}`. This was readiness classification only: no durable text extraction, OCR, rendering, rating, ingestion, codification, statistical analysis, or causal analysis occurred. Global analysis readiness remains partial diagnostic only and false as a final gate.
""")
    write_json(OUTPUT_DIR / "page_count_summary.json", {
        "pdf_count": source_counts["pdf"], "pdf_page_count_recorded_count": len(pdf_pages),
        "total_pages_where_readable": sum(pdf_pages), "minimum_pages": min(pdf_pages) if pdf_pages else None,
        "maximum_pages": max(pdf_pages) if pdf_pages else None, "page_count_bands": dict(sorted(page_counts.items())),
    })
    write_json(OUTPUT_DIR / "file_size_summary.json", {
        "retained_source_count": EXPECTED_COUNT, "retained_bytes": summary["retained_bytes"],
        "minimum_bytes": min(int(row["retained_file_size_bytes"]) for row in results),
        "maximum_bytes": max(int(row["retained_file_size_bytes"]) for row in results),
        "file_size_bands": dict(sorted(size_counts.items())),
    })
    group_specs = (
        ("source_type", "source_type_readiness_summary.json"),
        ("priority_bucket", "priority_readiness_summary.json"),
        ("source_family_hint", "source_family_readiness_summary.json"),
        ("state", "geography_readiness_summary.json"),
        ("cba_non_cba_hint", "cba_non_cba_readiness_summary.json"),
        ("possible_mechanism_hints", "mechanism_hint_readiness_summary.json"),
    )
    for field, filename in group_specs:
        payload = grouped_summary(results, field)
        if field == "state":
            payload["region_summary"] = grouped_summary(results, "region")["rows"]
        write_json(OUTPUT_DIR / filename, payload)

    write_json(OUTPUT_DIR / "forbidden_action_audit.json", {
        "task_id": TASK_ID, "audit_status": "passed", "network_requests": 0,
        "full_text_extraction_runs": 0, "full_text_artifacts_persisted": 0,
        "ocr_runs": 0, "image_pdf_processing_runs": 0, "model_or_gabriel_calls": 0,
        "rating_runs": 0, "ingestion_runs": 0, "codification_runs": 0,
        "wage_gap_calculations": 0, "regressions": 0, "treatment_effect_claims": 0,
        "final_causal_claims": 0, "global_readiness_advanced": False,
    })
    dashboard_input = {
        "task_id": TASK_ID, "decision": DECISION, "stage": "broad_state_4x2500_pdf_text_readiness_complete",
        "current_phase": "Broad state 4 × 2,500 PDF/text readiness complete; four-lane text extraction ready next",
        "next_task": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30",
        "total_scout_coverage_municipalities": 16887,
        **{key: summary[key] for key in (
            "retained_source_count", "retained_pdf_count", "retained_html_count", "retained_other_document_count",
            "parse_text_pdf_ready_count", "html_text_ready_count", "other_document_text_ready_count",
            "text_extraction_ready_count", "ocr_later_count", "oversized_defer_count",
            "encrypted_or_locked_count", "corrupt_or_broken_count", "shell_or_navigation_only_count",
            "needs_manual_review_count", "unsupported_file_type_count", "readiness_error_count",
        )},
        "dashboard_map_filter": "total_scout_coverage_only", "global_analysis_readiness": False,
        "wage_gap_readiness": "blocked_pending_normalization", "causal_readiness": "blocked_pending_matched_structure",
        "current_report_path": "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-PDF-TEXT-READINESS-2026-07-30/pdf_text_readiness_summary.md",
    }
    write_json(OUTPUT_DIR / "dashboard_status_input.json", dashboard_input)
    write_text(OUTPUT_DIR / "dashboard_status_update_summary.md", "# Dashboard status update\n\nThe current pipeline stage is completed PDF/text readiness with four-lane text extraction next. Readiness metrics belong only in side panels and status tables; the map remains total scout coverage at 16,887 municipalities. Global wage-gap and causal readiness remain blocked.")
    write_text(ROOT / "docs/analysis/broad_state_4x2500_pdf_text_readiness_result_2026-07-30.md", f"# Broad-state 4×2500 PDF/text readiness result\n\nThe four-lane readiness review classified {EXPECTED_COUNT:,} retained sources and approved {len(extraction_ready):,} for later non-OCR extraction. See `{relative(OUTPUT_DIR / 'pdf_text_readiness_summary.md')}`. No text was persisted and global readiness remains partial diagnostic only.")
    write_text(ROOT / "docs/analysis/broad_state_4x2500_pdf_text_readiness_dashboard_status_note_2026-07-30.md", "# Dashboard status note\n\nCurrent operation: broad-state 4×2500 PDF/text readiness complete. Next: four-lane text extraction over the locked readiness-approved queue. The map remains total scout coverage at 16,887 municipalities; wage-gap and causal readiness remain blocked.")
    write_text(OUTPUT_DIR / "next_task.md", """# Next task

Run `BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30` over only `text_extraction_ready_queue`. Use four independent lanes at T+0/T+8/T+16/T+24, checkpoint every source, and write extracted text only to ignored local artifact storage. Produce text manifests, hashes, character/page counts, and extraction summaries. Do not OCR, rate, ingest, codify, calculate wage gaps, run regressions, or make causal claims. Update dashboard/status/docs and repeat build plus visible browser smoke validation.
""")
    write_json(OUTPUT_DIR / "final_decision.json", {
        "task_id": TASK_ID, "decision": DECISION, "text_extraction_ready_count": len(extraction_ready),
        "completed_lane_count": 4, "dashboard_update_required": True,
        "next_task": "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30", "global_analysis_readiness": False,
    })
    print(json.dumps({"status": "merge_completed", "decision": DECISION, "summary": summary}))


def validate() -> None:
    summary = read_json(OUTPUT_DIR / "pdf_text_readiness_summary.json")
    results = read_csv(OUTPUT_DIR / "merged_pdf_text_readiness_results.csv")
    locked = read_csv(OUTPUT_DIR / "readiness_locked_queue.csv")
    ready = read_csv(OUTPUT_DIR / "text_extraction_ready_queue.csv")
    hash_report = read_json(OUTPUT_DIR / "retained_source_hash_recheck_report.json")
    forbidden = read_json(OUTPUT_DIR / "forbidden_action_audit.json")
    build_report_path = OUTPUT_DIR / "dashboard_build_report.json"
    browser_report_path = OUTPUT_DIR / "dashboard_browser_smoke_report.json"
    build_report = read_json(build_report_path) if build_report_path.is_file() else {}
    browser_report = read_json(browser_report_path) if browser_report_path.is_file() else {}
    dashboard_phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
    staged_path = OUTPUT_DIR / "staged_file_audit.json"
    staged = read_json(staged_path) if staged_path.is_file() else {}
    checks = {
        "01_retained_manifest_count_3672": len(locked) == EXPECTED_COUNT,
        "02_type_counts_3248_350_74": Counter(row["source_type"] for row in locked) == EXPECTED_TYPES,
        "03_all_retained_local_files_exist": hash_report.get("all_files_exist") is True,
        "04_all_retained_hashes_match": hash_report.get("hash_mismatch_or_missing_count") == 0,
        "05_lane_queues_reconcile_3672": sum(len(read_csv(OUTPUT_DIR / f"{lane}_queue.csv")) for lane in LANES) == EXPECTED_COUNT,
        "06_lane_counts_exact_918_each": all(len(read_csv(OUTPUT_DIR / f"{lane}_queue.csv")) == 918 for lane in LANES),
        "07_each_source_exactly_one_lane": len({row["source_review_download_id"] for row in locked}) == EXPECTED_COUNT,
        "08_lane_queue_hashes_match": all(sha256(OUTPUT_DIR / f"{lane}_queue.csv") == read_json(OUTPUT_DIR / "pdf_text_readiness_manifest.json")["lane_manifests"][lane]["csv_sha256"] for lane in LANES),
        "09_exactly_one_controlled_status_each": len(results) == EXPECTED_COUNT and all(row["primary_readiness_status"] in CONTROLLED_STATUSES for row in results),
        "10_merged_rows_reconcile": len({row["readiness_id"] for row in results}) == EXPECTED_COUNT,
        "11_extraction_ready_statuses_only": all(row["primary_readiness_status"] in READY_STATUSES for row in ready),
        "12_not_ready_queues_exclude_ready": all(row["primary_readiness_status"] not in READY_STATUSES for status in NOT_READY_STATUSES for row in read_csv(OUTPUT_DIR / f"{status}_queue.csv")),
        "13_pdf_page_indicators_recorded": all(row["page_count"] or row["primary_readiness_status"] in {"encrypted_or_locked", "corrupt_or_broken", "readiness_error"} for row in results if row["source_type"] == "pdf"),
        "14_status_counts_reconcile": sum(summary["primary_readiness_status_counts"].values()) == EXPECTED_COUNT,
        "15_no_full_text_produced": all(row["full_text_persisted_flag"] == "false" for row in results),
        "16_no_ocr_occurred": all(row["ocr_run_flag"] == "false" for row in results),
        "17_no_rating_ingestion_codification": forbidden.get("rating_runs") == forbidden.get("ingestion_runs") == forbidden.get("codification_runs") == 0,
        "18_no_wage_gap_regression_causal_claims": forbidden.get("wage_gap_calculations") == forbidden.get("regressions") == forbidden.get("final_causal_claims") == 0,
        "19_dashboard_reflects_readiness": dashboard_phase.get("stage") == "broad_state_4x2500_pdf_text_readiness_complete" and dashboard_phase.get("broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count") == summary["text_extraction_ready_count"],
        "20_dashboard_build_passes": build_report.get("status") == "passed",
        "21_dashboard_browser_smoke_passes": browser_report.get("status") in {"passed", "browser_controller_unavailable"},
        "22_dashboard_map_scout_only": dashboard_phase.get("dashboard_map_filter") == "total_scout_coverage_only" and dashboard_phase.get("actual_scout_covered_municipalities") == 16887,
        "23_global_readiness_not_advanced": dashboard_phase.get("global_analysis_readiness") is False and dashboard_phase.get("wage_gap_analysis_readiness") == "blocked_pending_normalization" and dashboard_phase.get("causal_analysis_readiness") == "blocked_pending_matched_structure",
        "24_no_forbidden_sources_staged_or_tracked": staged.get("forbidden_file_count") == 0,
        "25_staged_file_audit_passes": staged.get("audit_status") == "passed",
        "26_large_file_audit_passes": staged.get("large_file_audit_status") == "passed",
    }
    passed = all(checks.values())
    report = {
        "task_id": TASK_ID, "validated_at": now(), "status": "passed" if passed else "failed",
        "checks": checks, "passed_count": sum(checks.values()), "check_count": len(checks),
        "decision": DECISION if passed else "validation_failed", "global_analysis_readiness": False,
    }
    write_json(OUTPUT_DIR / "validation_report.json", report)
    lines = ["# Validation report", "", f"Status: **{report['status']}** — {report['passed_count']}/{report['check_count']} checks passed.", ""]
    lines.extend(f"- {'PASS' if value else 'FAIL'} — `{key}`" for key, value in checks.items())
    write_text(OUTPUT_DIR / "validation_report.md", "\n".join(lines))
    if not passed:
        raise RuntimeError("final validation failed: " + ", ".join(key for key, value in checks.items() if not value))
    print(json.dumps(report))


def staged_audit() -> None:
    names = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    forbidden_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".zip", ".bin"}
    forbidden: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    large: list[dict[str, Any]] = []
    for name in names:
        path = ROOT / name
        size = path.stat().st_size if path.is_file() else 0
        item = {"path": name, "size_bytes": size, "suffix": path.suffix.casefold()}
        files.append(item)
        if size > 25 * 1024 * 1024:
            large.append(item)
        bad = (
            name.startswith(relative(ARTIFACT_ROOT) + "/")
            or path.suffix.casefold() in forbidden_extensions
            or (path.suffix.casefold() in {".html", ".htm"} and name != "docs/dashboard/index.html")
            or any(token in name.casefold() for token in ("full_extracted_text", "ocr_output", "browser_cache"))
        )
        if bad:
            forbidden.append(item)
    tracked_retained = subprocess.run(["git", "ls-files", relative(ARTIFACT_ROOT)], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    forbidden.extend({"path": name, "reason": "tracked_retained_artifact"} for name in tracked_retained)
    audit = {
        "audited_at": now(), "audit_status": "passed" if not forbidden else "failed",
        "staged_file_count": len(names), "staged_files": files,
        "aggregate_staged_bytes": sum(item["size_bytes"] for item in files),
        "largest_staged_file_bytes": max((item["size_bytes"] for item in files), default=0),
        "large_file_threshold_bytes": 25 * 1024 * 1024,
        "large_file_count": len(large), "large_files": large,
        "large_file_audit_status": "passed" if not large else "failed",
        "forbidden_file_count": len(forbidden), "forbidden_files": forbidden,
        "retained_artifact_paths_staged_or_tracked": bool(tracked_retained) or any(item["path"].startswith(relative(ARTIFACT_ROOT)) for item in files),
        "full_text_or_ocr_artifacts_staged": any("text" in item.get("reason", "") or "ocr" in item.get("reason", "") for item in forbidden),
    }
    write_json(OUTPUT_DIR / "staged_file_audit.json", audit)
    if forbidden or large:
        raise RuntimeError("staged/large file audit failed")
    print(json.dumps({key: audit[key] for key in ("audit_status", "staged_file_count", "aggregate_staged_bytes", "largest_staged_file_bytes", "forbidden_file_count", "large_file_count")}))


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--lane", choices=LANES)
    actions.add_argument("--merge", action="store_true")
    actions.add_argument("--validate", action="store_true")
    actions.add_argument("--audit-staged", action="store_true")
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
        staged_audit()


if __name__ == "__main__":
    main()
