#!/usr/bin/env python3
"""Bounded four-lane extraction of machine-readable local text.

This runner has three fail-closed phases: prepare, isolated lane workers, and
coordinate. It never opens a URL, renders a PDF, invokes OCR, extracts evidence
spans, calls a model, rates evidence, ingests, codifies, or performs analysis.
Full text is written only beneath the Git-ignored local artifact root.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/analysis/compensation_extraction"
READINESS = BASE / "COMBINED-BROAD-PDF-TEXT-LAYER-READINESS-4961-PARALLEL-LANES-2026-07-28"
SOURCE = BASE / "COMBINED-BROAD-SOURCE-REVIEW-DOWNLOAD-5589-PARALLEL-LANES-2026-07-28"
STORAGE = BASE / "RETAINED-SOURCE-STORAGE-HISTORY-REPAIR-OPTION1-2026-07-28"
OUTPUT = BASE / "COMBINED-BROAD-TEXT-EXTRACTION-4051-PARALLEL-LANES-2026-07-28"
ARTIFACT_ROOT = ROOT / "artifacts/local_extracted_text/combined_broad_text_extraction_4051_2026-07-28"
TASK_ID = "COMBINED-BROAD-TEXT-EXTRACTION-4051-PARALLEL-LANES-2026-07-28"
PREFIX = "combined_broad_text_extraction_4051"
EXPECTED = 4051
APPROVED = {
    "parse_text_layer_later": 3177,
    "html_text_later": 834,
    "other_document_text_later": 40,
}
LANES = {
    "extraction_lane_001": 1013,
    "extraction_lane_002": 1013,
    "extraction_lane_003": 1013,
    "extraction_lane_004": 1012,
}
DELAYS = {
    "extraction_lane_001": 0,
    "extraction_lane_002": 480,
    "extraction_lane_003": 960,
    "extraction_lane_004": 1440,
}
CONTROLLED = {
    "extracted_ok",
    "empty_or_too_short",
    "low_text_density",
    "suspected_bad_text_layer",
    "html_noisy_or_shell",
    "other_document_extraction_unsupported",
    "extraction_error",
    "skipped_not_in_queue",
}
EXCLUDED = {
    "ocr_later_or_defer",
    "oversized_for_text_pass",
    "encrypted_or_locked",
    "needs_review",
    "shell_or_navigation_only",
    "corrupt_or_unreadable",
    "unsupported_for_text_extraction",
    "readiness_error",
}
MIN_ROW_SECONDS = 0.52

LINEAGE = (
    "readiness_id", "source_review_download_id", "combined_review_id",
    "source_candidate_id", "verification_row_id", "candidate_origin",
    "state", "region", "municipality", "county", "source_title",
    "source_locator_or_url", "final_canonical_locator", "source_domain",
    "source_family_hint", "document_type_hint", "source_review_priority",
    "retained_file_type", "retained_file_size_bytes", "retained_file_sha256",
    "readiness_status", "page_count",
)
LOCK_FIELDS = (
    "extraction_id", *LINEAGE[:6], "lane_id", "lane_sequence", *LINEAGE[6:],
    "retained_file_path_resolved", "retained_file_path_source",
    "original_retained_file_path", "local_artifact_file_path",
    "artifact_root_lineage", "source_review_status", "download_status",
    "rating_status", "ingestion_status", "codification_status",
    "causal_status", "global_analysis_readiness", "notes",
)
RESULT_FIELDS = LOCK_FIELDS + (
    "extraction_status", "extraction_method", "text_artifact_group",
    "extracted_text_artifact_path", "extracted_text_size_bytes",
    "extracted_text_sha256", "char_count", "line_count", "chars_per_page",
    "low_text_density_flag", "repeated_garbage_flag", "encoding_issue_flag",
    "suspected_scanned_pdf_flag", "html_shell_flag",
    "extraction_warning_flag", "extraction_error_type", "extraction_reason",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


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
        handle.flush()
        os.fsync(handle.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extraction_id(readiness_id: str) -> str:
    return "CBTXT-20260728-" + hashlib.sha256(readiness_id.encode()).hexdigest()[:20]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def assert_ignored(path: Path) -> None:
    probe = path / ".git-ignore-probe.txt"
    result = subprocess.run(
        ["git", "check-ignore", "-q", rel(probe)], cwd=ROOT
    )
    if result.returncode != 0:
        raise RuntimeError("extracted text artifact root is not ignored by Git")


def manifest_paths() -> dict[str, Path]:
    return {
        "parse_text_layer_later": READINESS / "combined_broad_pdf_text_layer_readiness_4961_parse_text_layer_later.csv",
        "html_text_later": READINESS / "combined_broad_pdf_text_layer_readiness_4961_html_text_later.csv",
        "other_document_text_later": READINESS / "combined_broad_pdf_text_layer_readiness_4961_other_document_text_later.csv",
    }


def load_inputs() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    readiness_decision = read_json(READINESS / "combined_broad_pdf_text_layer_readiness_4961_decision.json")
    storage_decision = read_json(STORAGE / "retained_source_storage_history_repair_decision.json")
    if readiness_decision.get("decision") != "combined_broad_pdf_text_layer_readiness_4961_completed_extraction_ready":
        raise RuntimeError("readiness decision does not authorize extraction")
    if storage_decision.get("decision") != "retained_source_storage_history_repair_completed_extraction_ready":
        raise RuntimeError("storage repair decision does not authorize extraction")
    rows: list[dict[str, str]] = []
    for status, path in manifest_paths().items():
        part = read_csv(path)
        if len(part) != APPROVED[status] or any(row["readiness_status"] != status for row in part):
            raise RuntimeError(f"approved manifest count/status mismatch: {status}")
        rows.extend(part)
    if len(rows) != EXPECTED or len({row["readiness_id"] for row in rows}) != EXPECTED:
        raise RuntimeError("extraction-ready manifest union does not reconcile to 4,051")
    if any(row["readiness_status"] in EXCLUDED for row in rows):
        raise RuntimeError("excluded readiness status entered extraction queue")
    combined = read_csv(READINESS / "combined_broad_pdf_text_layer_readiness_4961_results.csv")
    combined_map = {row["readiness_id"]: row for row in combined}
    if set(combined_map).intersection({row["readiness_id"] for row in rows}) != {row["readiness_id"] for row in rows}:
        raise RuntimeError("approved rows are not a subset of readiness results")
    storage_rows = read_csv(STORAGE / "retained_source_storage_history_repair_local_artifact_manifest.csv")
    storage_map = {row["source_review_download_id"]: row for row in storage_rows}
    if len(storage_map) != 4961:
        raise RuntimeError("local artifact mapping does not contain 4,961 unique sources")
    return rows, storage_map


def prepare() -> None:
    if OUTPUT.exists() or ARTIFACT_ROOT.exists():
        raise RuntimeError("output or artifact root already exists; use resume/validate rather than unsafe overwrite")
    required = [
        READINESS / "combined_broad_pdf_text_layer_readiness_4961_results_summary.json",
        READINESS / "combined_broad_pdf_text_layer_readiness_4961_file_integrity_summary.json",
        READINESS / "combined_broad_pdf_text_layer_readiness_4961_hash_reconciliation.json",
        SOURCE / "combined_broad_source_review_download_5589_retained_sources_manifest.csv",
        SOURCE / "combined_broad_source_review_download_5589_retained_sources_hash_manifest.csv",
        SOURCE / "combined_broad_source_review_download_5589_retained_sources_summary.json",
        STORAGE / "retained_source_storage_history_repair_local_artifact_root.json",
        STORAGE / "retained_source_storage_history_repair_hash_validation_after_summary.json",
    ]
    missing = [rel(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"required non-derivable artifacts missing: {missing}")
    assert_ignored(ARTIFACT_ROOT)
    tracked_retained = git_output("ls-files", "artifacts/local_retained_sources")
    tracked_extracted = git_output("ls-files", "artifacts/local_extracted_text")
    if tracked_retained or tracked_extracted:
        raise RuntimeError("retained or extracted artifacts are tracked in normal Git")
    rows, storage_map = load_inputs()
    OUTPUT.mkdir(parents=True)
    ARTIFACT_ROOT.mkdir(parents=True)
    integrity: list[dict[str, Any]] = []
    locked: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        mapping = storage_map.get(row["source_review_download_id"])
        if not mapping:
            raise RuntimeError(f"missing artifact mapping: {row['source_review_download_id']}")
        original = ROOT / mapping["original_retained_file_path"]
        artifact = ROOT / mapping["local_artifact_file_path"]
        expected_hash = row["retained_file_sha256"]
        expected_size = int(row["retained_file_size_bytes"])
        original_ok = original.is_file() and original.stat().st_size == expected_size
        original_hash = sha256_file(original) if original_ok else ""
        if original_hash != expected_hash:
            original_ok = False
        artifact_ok = artifact.is_file() and artifact.stat().st_size == expected_size
        artifact_hash = sha256_file(artifact) if artifact_ok else ""
        if artifact_hash != expected_hash:
            artifact_ok = False
        if not original_ok and not artifact_ok:
            raise RuntimeError(f"no hash-valid retained path: {row['source_review_download_id']}")
        resolved = original if original_ok else artifact
        path_source = "original_operational_path" if original_ok else "local_artifact_copy"
        integrity.append({
            "readiness_id": row["readiness_id"],
            "source_review_download_id": row["source_review_download_id"],
            "original_path_exists_hash_valid": str(original_ok).lower(),
            "artifact_copy_exists_hash_valid": str(artifact_ok).lower(),
            "resolved_path": rel(resolved),
            "resolved_path_source": path_source,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": resolved.stat().st_size,
            "expected_sha256": expected_hash,
            "actual_sha256": expected_hash,
            "integrity_status": "integrity_pass",
        })
        lane_id = next(
            lane for lane, upper in zip(LANES, (1013, 2026, 3039, 4051))
            if index <= upper
        )
        prior = sum(LANES[lane] for lane in LANES if lane < lane_id)
        lock = {
            "extraction_id": extraction_id(row["readiness_id"]),
            **{field: row.get(field, "") for field in LINEAGE},
            "lane_id": lane_id,
            "lane_sequence": index - prior,
            "retained_file_path_resolved": rel(resolved),
            "retained_file_path_source": path_source,
            "original_retained_file_path": mapping["original_retained_file_path"],
            "local_artifact_file_path": mapping["local_artifact_file_path"],
            "artifact_root_lineage": rel(ARTIFACT_ROOT),
            "source_review_status": "retained",
            "download_status": "downloaded_or_retained",
            "rating_status": "not_rated",
            "ingestion_status": "not_ingested",
            "codification_status": "not_codified",
            "causal_status": "not_causal_evidence",
            "global_analysis_readiness": "false",
            "notes": "Locked machine-readable text-only extraction row; no OCR, rendering, span extraction, rating, ingestion, codification, or analysis.",
        }
        locked.append(lock)
    if len(locked) != EXPECTED or len({row["extraction_id"] for row in locked}) != EXPECTED:
        raise RuntimeError("locked queue uniqueness failure")
    lock_hash = hashlib.sha256(
        "\n".join(row["extraction_id"] for row in locked).encode()
    ).hexdigest()
    write_csv(OUTPUT / f"{PREFIX}_file_integrity_preflight.csv", integrity, integrity[0].keys())
    write_json(OUTPUT / f"{PREFIX}_file_integrity_preflight_summary.json", {
        "checked_count": EXPECTED,
        "integrity_pass_count": EXPECTED,
        "original_path_selected_count": sum(row["resolved_path_source"] == "original_operational_path" for row in integrity),
        "artifact_copy_selected_count": sum(row["resolved_path_source"] == "local_artifact_copy" for row in integrity),
        "hash_mismatch_count": 0,
    })
    write_csv(OUTPUT / f"{PREFIX}_locked_queue.csv", locked, LOCK_FIELDS)
    write_json(OUTPUT / f"{PREFIX}_locked_queue_summary.json", {
        "queue_count": EXPECTED, "lane_counts": LANES, "approved_status_counts": APPROVED,
        "queue_sha256": lock_hash, "excluded_status_count": 0,
    })
    write_json(OUTPUT / f"{PREFIX}_lock.json", {
        "task_id": TASK_ID, "locked_at": utc_now(), "queue_count": EXPECTED,
        "queue_sha256": lock_hash, "immutable_predecessors": True,
    })
    offset = 0
    for lane, count in LANES.items():
        lane_rows = locked[offset:offset + count]
        offset += count
        lane_no = lane[-3:]
        write_csv(OUTPUT / f"combined_broad_text_extraction_lane_{lane_no}_locked_queue.csv", lane_rows, LOCK_FIELDS)
        write_json(OUTPUT / f"combined_broad_text_extraction_lane_{lane_no}_locked_queue_summary.json", {
            "lane_id": lane, "queue_count": count, "sequence_min": 1,
            "sequence_max": count, "delay_seconds": DELAYS[lane],
        })
        write_json(OUTPUT / f"combined_broad_text_extraction_lane_{lane_no}_lock.json", {
            "lane_id": lane, "queue_count": count,
            "queue_sha256": hashlib.sha256("\n".join(row["extraction_id"] for row in lane_rows).encode()).hexdigest(),
            "writes_are_lane_isolated": True,
        })
        (OUTPUT / "lanes" / lane).mkdir(parents=True)
        (ARTIFACT_ROOT / lane).mkdir(parents=True)
    preflight = {
        "preflight_passed": True,
        "readiness_decision_confirmed": True,
        "storage_repair_decision_confirmed": True,
        "queue_count": EXPECTED,
        "lane_counts": LANES,
        "approved_status_counts": APPROVED,
        "excluded_readiness_rows_in_queue": 0,
        "retained_hashes_match": True,
        "artifact_root_ignored": True,
        "tracked_retained_source_count": 0,
        "tracked_extracted_text_count": 0,
        "no_source_review_rerun": True,
        "no_redownload": True,
        "no_readiness_rerun": True,
        "no_ocr_or_rendering": True,
        "no_span_rating_ingestion_or_analysis": True,
        "dashboard_map_contract": "total_scout_coverage_only",
        "global_analysis_readiness": False,
        "rollback_safe": True,
    }
    write_json(OUTPUT / f"{PREFIX}_preflight_checks.json", preflight)
    write_json(OUTPUT / f"{PREFIX}_artifact_storage_preflight.json", {
        "artifact_root": rel(ARTIFACT_ROOT), "git_ignored": True,
        "tracked_before_extraction": False, "full_text_normal_git_policy": "prohibited",
    })
    write_text(OUTPUT / f"{PREFIX}_preflight_report.md",
        "# Combined broad text-extraction preflight\n\n"
        "PASS. The exact 4,051 readiness-approved rows reconcile to 3,177 PDF, "
        "834 HTML, and 40 other-document rows. All retained paths and hashes "
        "passed; the four locked queues are 1,013 / 1,013 / 1,013 / 1,012. "
        "Full text is restricted to ignored artifact storage. OCR, rendering, "
        "span extraction, rating, ingestion, codification, and analysis are prohibited.")
    write_json(OUTPUT / f"{PREFIX}_extracted_text_artifact_root.json", {
        "artifact_root": rel(ARTIFACT_ROOT), "storage_scope": "local_only_git_ignored",
        "full_text_tracked_in_git": False,
    })
    write_text(OUTPUT / f"{PREFIX}_extracted_text_artifact_root.md",
        "# Extracted-text artifact root\n\n"
        f"Full extracted text is stored locally at {rel(ARTIFACT_ROOT)}. "
        "The directory is ignored by Git; only hashes, pointers, lineage, and summaries are tracked.")
    print(json.dumps({"status": "preflight_passed", "queue": EXPECTED, "lanes": LANES}))


class VisibleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []
        self.shell_chars = 0
        self.total_chars = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "canvas", "template"}:
            self.skip += 1
        if tag in {"nav", "header", "footer", "aside"}:
            self.shell_chars -= self.total_chars

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "canvas", "template"} and self.skip:
            self.skip -= 1
        if tag in {"nav", "header", "footer", "aside"}:
            self.shell_chars += self.total_chars

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)
            self.total_chars += len(cleaned)


def normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    value = "\n".join(line.rstrip() for line in value.splitlines())
    return value.strip() + ("\n" if value.strip() else "")


def extract_pdf(source: Path, temporary: Path) -> tuple[str, str, bool]:
    command = ["/opt/homebrew/bin/pdftotext", "-layout", "-enc", "UTF-8", str(source), str(temporary)]
    proc = subprocess.run(command, capture_output=True, timeout=180)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    value = temporary.read_text(encoding="utf-8", errors="replace")
    return value, "pdftotext_text_layer", False


def extract_html(source: Path) -> tuple[str, str, bool]:
    raw = source.read_bytes()
    decoded = raw.decode("utf-8", errors="replace")
    parser = VisibleHTML()
    parser.feed(decoded)
    text = "\n".join(parser.parts)
    ratio = parser.shell_chars / max(parser.total_chars, 1)
    return text, "stdlib_html_visible_text", ratio > 0.75


def extract_other(source: Path) -> tuple[str, str, bool]:
    suffix = source.suffix.casefold()
    if suffix in {".txt", ".csv"}:
        return source.read_text(encoding="utf-8", errors="replace"), "local_plain_text_decode", False
    if suffix in {".doc", ".docx", ".rtf"}:
        proc = subprocess.run(
            ["/usr/bin/textutil", "-convert", "txt", "-stdout", str(source)],
            capture_output=True, timeout=180
        )
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
        return proc.stdout.decode("utf-8", errors="replace"), "macos_textutil", False
    raise NotImplementedError(f"unsupported local other-document extension: {suffix}")


def quality(text: str, row: dict[str, str], html_shell: bool) -> tuple[str, dict[str, Any], str]:
    char_count = len(text)
    line_count = len(text.splitlines()) if text else 0
    replacement = text.count("\ufffd")
    printable = sum(ch.isprintable() or ch in "\n\t" for ch in text)
    encoding_issue = replacement > max(5, char_count // 1000)
    repeated = bool(re.search(r"([A-Za-z0-9])\1{79,}", text)) or printable < max(1, int(char_count * 0.85))
    pages = int(row.get("page_count") or 0)
    density = char_count / pages if pages else None
    scanned = row["retained_file_type"] == "pdf" and pages > 0 and density is not None and density < 100
    if char_count < 200:
        status, reason = "empty_or_too_short", "machine-readable extraction produced fewer than 200 characters"
    elif encoding_issue or repeated:
        status, reason = "suspected_bad_text_layer", "replacement/control/repeated-character quality checks failed"
    elif html_shell or (row["retained_file_type"] == "html" and len(text.split()) < 50):
        status, reason = "html_noisy_or_shell", "bounded structural/text checks indicate shell-dominant HTML"
    elif scanned:
        status, reason = "low_text_density", "PDF text density is below 100 characters per page"
    else:
        status, reason = "extracted_ok", "machine-readable text extracted and passed bounded quality checks"
    return status, {
        "char_count": char_count, "line_count": line_count,
        "chars_per_page": "" if density is None else f"{density:.2f}",
        "low_text_density_flag": str(status == "low_text_density").lower(),
        "repeated_garbage_flag": str(repeated).lower(),
        "encoding_issue_flag": str(encoding_issue).lower(),
        "suspected_scanned_pdf_flag": str(scanned).lower(),
        "html_shell_flag": str(html_shell).lower(),
        "extraction_warning_flag": str(status != "extracted_ok").lower(),
    }, reason


def bounded_delay(seconds: int) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        time.sleep(min(30, max(0, deadline - time.monotonic())))


def lane_paths(lane: str) -> tuple[Path, Path]:
    number = lane[-3:]
    queue = OUTPUT / f"combined_broad_text_extraction_lane_{number}_locked_queue.csv"
    directory = OUTPUT / "lanes" / lane
    return queue, directory


def run_lane(lane: str, delay_seconds: int) -> None:
    if delay_seconds < 0 or delay_seconds > DELAYS[lane]:
        raise RuntimeError("lane resume delay cannot exceed its exact standard stagger")
    bounded_delay(delay_seconds)
    queue_path, directory = lane_paths(lane)
    queue = read_csv(queue_path)
    if len(queue) != LANES[lane]:
        raise RuntimeError("lane queue size mismatch")
    results_path = directory / f"lane_{lane[-3:]}_text_extraction_results.csv"
    prior = read_csv(results_path) if results_path.exists() else []
    completed_ids = {row["extraction_id"] for row in prior}
    if not completed_ids.issubset({row["extraction_id"] for row in queue}):
        raise RuntimeError("resume results contain rows outside locked lane")
    prior_checkpoint_path = directory / f"lane_{lane[-3:]}_checkpoint.json"
    prior_checkpoint = read_json(prior_checkpoint_path) if prior_checkpoint_path.exists() else {}
    started_at = prior_checkpoint.get("started_at") or utc_now()
    write_json(directory / f"lane_{lane[-3:]}_checkpoint.json", {
        "lane_id": lane, "status": "running", "started_at": started_at,
        "completed_count": len(prior), "queue_count": len(queue),
        "standard_delay_seconds": DELAYS[lane],
        "resume_relative_delay_seconds": delay_seconds,
    })
    consecutive_errors = 0
    for row in queue:
        if row["extraction_id"] in completed_ids:
            continue
        row_started = time.monotonic()
        result: dict[str, Any] = {field: row.get(field, "") for field in LOCK_FIELDS}
        source = ROOT / row["retained_file_path_resolved"]
        artifact = ARTIFACT_ROOT / lane / f"{row['extraction_id']}.txt"
        temporary = artifact.with_suffix(".tmp")
        try:
            if not source.is_file() or source.stat().st_size != int(row["retained_file_size_bytes"]):
                raise RuntimeError("retained source path/size mismatch")
            if sha256_file(source) != row["retained_file_sha256"]:
                raise RuntimeError("retained source SHA-256 mismatch")
            file_type = row["retained_file_type"]
            if file_type == "pdf":
                raw, method, shell = extract_pdf(source, temporary)
                group = "pdf_text_layer"
            elif file_type == "html":
                raw, method, shell = extract_html(source)
                group = "html_text"
            else:
                raw, method, shell = extract_other(source)
                group = "other_document_text"
            text_value = normalize_text(raw)
            status, flags, reason = quality(text_value, row, shell)
            encoded = text_value.encode("utf-8")
            if encoded:
                artifact.parent.mkdir(parents=True, exist_ok=True)
                temporary.write_bytes(encoded)
                temporary.replace(artifact)
                artifact_path = rel(artifact)
                artifact_size = len(encoded)
                artifact_hash = hashlib.sha256(encoded).hexdigest()
            else:
                temporary.unlink(missing_ok=True)
                artifact_path, artifact_size, artifact_hash = "", "", ""
            result.update({
                "extraction_status": status, "extraction_method": method,
                "text_artifact_group": group if encoded else "none",
                "extracted_text_artifact_path": artifact_path,
                "extracted_text_size_bytes": artifact_size,
                "extracted_text_sha256": artifact_hash,
                **flags, "extraction_error_type": "", "extraction_reason": reason,
            })
            consecutive_errors = 0
        except NotImplementedError as exc:
            temporary.unlink(missing_ok=True)
            result.update({
                "extraction_status": "other_document_extraction_unsupported",
                "extraction_method": "none", "text_artifact_group": "none",
                "extracted_text_artifact_path": "", "extracted_text_size_bytes": "",
                "extracted_text_sha256": "", "char_count": 0, "line_count": 0,
                "chars_per_page": "", "low_text_density_flag": "false",
                "repeated_garbage_flag": "false", "encoding_issue_flag": "false",
                "suspected_scanned_pdf_flag": "false", "html_shell_flag": "false",
                "extraction_warning_flag": "true", "extraction_error_type": type(exc).__name__,
                "extraction_reason": str(exc),
            })
            consecutive_errors = 0
        except Exception as exc:
            temporary.unlink(missing_ok=True)
            result.update({
                "extraction_status": "extraction_error", "extraction_method": "none",
                "text_artifact_group": "none", "extracted_text_artifact_path": "",
                "extracted_text_size_bytes": "", "extracted_text_sha256": "",
                "char_count": 0, "line_count": 0, "chars_per_page": "",
                "low_text_density_flag": "false", "repeated_garbage_flag": "false",
                "encoding_issue_flag": "false", "suspected_scanned_pdf_flag": "false",
                "html_shell_flag": "false", "extraction_warning_flag": "true",
                "extraction_error_type": type(exc).__name__, "extraction_reason": str(exc)[:500],
            })
            consecutive_errors += 1
        append_csv(results_path, result, RESULT_FIELDS)
        prior.append(result)
        write_json(directory / f"lane_{lane[-3:]}_checkpoint.json", {
            "lane_id": lane, "status": "running", "started_at": started_at,
            "updated_at": utc_now(), "completed_count": len(prior),
            "queue_count": len(queue), "last_extraction_id": row["extraction_id"],
            "standard_delay_seconds": DELAYS[lane],
            "resume_relative_delay_seconds": delay_seconds,
        })
        remaining = MIN_ROW_SECONDS - (time.monotonic() - row_started)
        if remaining > 0:
            time.sleep(remaining)
        if consecutive_errors >= 25:
            break
    statuses = Counter(row["extraction_status"] for row in prior)
    complete = len(prior) == len(queue)
    ended_at = utc_now()
    write_csv(directory / f"lane_{lane[-3:]}_extracted_ok.csv",
              [row for row in prior if row["extraction_status"] == "extracted_ok"], RESULT_FIELDS)
    write_csv(directory / f"lane_{lane[-3:]}_quality_flags.csv",
              [row for row in prior if row["extraction_status"] != "extracted_ok"], RESULT_FIELDS)
    write_csv(directory / f"lane_{lane[-3:]}_errors.csv",
              [row for row in prior if row["extraction_status"] == "extraction_error"], RESULT_FIELDS)
    summary = {
        "lane_id": lane, "queue_count": len(queue), "completed_count": len(prior),
        "complete": complete, "status_counts": dict(statuses),
        "started_at": started_at, "ended_at": ended_at,
        "standard_delay_seconds": DELAYS[lane],
        "resume_relative_delay_seconds": delay_seconds,
    }
    write_json(directory / f"lane_{lane[-3:]}_text_extraction_results_summary.json", summary)
    write_json(directory / f"lane_{lane[-3:]}_resume_state.json", {
        "lane_id": lane, "resume_required": not complete,
        "completed_count": len(prior), "remaining_count": len(queue) - len(prior),
        "next_lane_sequence": len(prior) + 1 if not complete else None,
    })
    write_json(directory / f"lane_{lane[-3:]}_checkpoint.json", {
        **summary, "status": "completed" if complete else "partial_stop",
    })
    if not complete:
        raise RuntimeError(f"{lane} stopped partial after repeated errors")
    print(json.dumps(summary))


def launch(resume: bool = False) -> None:
    log_dir = ROOT / "tmp/combined_broad_text_extraction_4051_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    processes: list[tuple[str, subprocess.Popen[bytes], Any]] = []
    delays = dict(DELAYS)
    if resume:
        checkpoint = read_json(
            OUTPUT / "lanes/extraction_lane_001/lane_001_checkpoint.json"
        )
        base = datetime.fromisoformat(checkpoint["started_at"].replace("Z", "+00:00")).timestamp()
        current = time.time()
        delays = {
            lane: max(0, int(base + DELAYS[lane] - current))
            for lane in LANES
        }
    for lane in LANES:
        handle = (log_dir / f"{lane}.log").open("wb")
        proc = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), str(Path(__file__).resolve()),
             "--lane", lane, "--stagger-seconds", str(delays[lane])],
            cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
        )
        processes.append((lane, proc, handle))
    failures = []
    for lane, proc, handle in processes:
        code = proc.wait()
        handle.close()
        if code:
            failures.append((lane, code))
    if failures:
        raise RuntimeError(f"lane process failures: {failures}")
    print(json.dumps({
        "status": "all_lane_processes_completed", "lanes": list(LANES),
        "resume_launch": resume, "relative_delays_used": delays,
    }))


def repair_quality_flags() -> None:
    """Deterministically repair quality flags from already-saved local text.

    This bounded repair performs no source extraction and creates no new full
    text. It exists so a checkpointed lane can resume after a quality-rule bug.
    """
    repaired = 0
    for lane in LANES:
        _, directory = lane_paths(lane)
        results_path = directory / f"lane_{lane[-3:]}_text_extraction_results.csv"
        if not results_path.exists():
            continue
        rows = read_csv(results_path)
        for row in rows:
            artifact_value = row["extracted_text_artifact_path"]
            if not artifact_value:
                continue
            artifact = ROOT / artifact_value
            value = artifact.read_text(encoding="utf-8")
            html_shell = row.get("html_shell_flag") == "true"
            status, flags, reason = quality(value, row, html_shell)
            row["extraction_status"] = status
            row.update({key: str(item).lower() if isinstance(item, bool) else item for key, item in flags.items()})
            row["extraction_reason"] = reason
            repaired += 1
        write_csv(results_path, rows, RESULT_FIELDS)
        write_json(directory / f"lane_{lane[-3:]}_quality_repair.json", {
            "lane_id": lane, "repaired_row_count": len(rows),
            "repair_scope": "quality_flags_only_no_source_extraction",
            "completed_at": utc_now(),
        })
    print(json.dumps({"status": "quality_flags_repaired", "artifact_rows_checked": repaired}))


def grouped_summary(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "") or "unknown"].append(row)
    output = []
    for name in sorted(groups):
        part = groups[name]
        counts = Counter(row["extraction_status"] for row in part)
        output.append({
            field: name,
            "attempted_count": len(part),
            "extracted_ok_count": counts["extracted_ok"],
            "empty_or_too_short_count": counts["empty_or_too_short"],
            "low_text_density_count": counts["low_text_density"],
            "suspected_bad_text_layer_count": counts["suspected_bad_text_layer"],
            "html_noisy_or_shell_count": counts["html_noisy_or_shell"],
            "other_document_extraction_unsupported_count": counts["other_document_extraction_unsupported"],
            "extraction_error_count": counts["extraction_error"],
        })
    return output


def artifact_rows(results: list[dict[str, str]]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for row in results:
        path_value = row["extracted_text_artifact_path"]
        if not path_value:
            continue
        path = ROOT / path_value
        if not path.is_file():
            raise RuntimeError(f"missing extracted text artifact: {path_value}")
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if actual_size != int(row["extracted_text_size_bytes"]) or actual_hash != row["extracted_text_sha256"]:
            raise RuntimeError(f"extracted text artifact integrity failure: {path_value}")
        artifacts.append({
            "extraction_id": row["extraction_id"],
            "readiness_id": row["readiness_id"],
            "source_review_download_id": row["source_review_download_id"],
            "lane_id": row["lane_id"],
            "extraction_status": row["extraction_status"],
            "text_artifact_group": row["text_artifact_group"],
            "extracted_text_artifact_path": path_value,
            "extracted_text_size_bytes": actual_size,
            "extracted_text_sha256": actual_hash,
            "artifact_storage_status": "local_only_git_ignored",
        })
    return artifacts


def write_status_manifest(results: list[dict[str, str]], status: str, filename: str) -> None:
    write_csv(OUTPUT / filename, [row for row in results if row["extraction_status"] == status], RESULT_FIELDS)


def coordinate() -> None:
    locked = read_csv(OUTPUT / f"{PREFIX}_locked_queue.csv")
    if len(locked) != EXPECTED:
        raise RuntimeError("master locked queue is incomplete")
    results: list[dict[str, str]] = []
    lane_summaries: list[dict[str, Any]] = []
    for lane, count in LANES.items():
        _, directory = lane_paths(lane)
        lane_results = read_csv(directory / f"lane_{lane[-3:]}_text_extraction_results.csv")
        summary = read_json(directory / f"lane_{lane[-3:]}_text_extraction_results_summary.json")
        if len(lane_results) != count or not summary.get("complete"):
            raise RuntimeError(f"lane incomplete: {lane}")
        if any(row["lane_id"] != lane for row in lane_results):
            raise RuntimeError(f"lane isolation failure: {lane}")
        results.extend(lane_results)
        lane_summaries.append(summary)
    locked_ids = {row["extraction_id"] for row in locked}
    result_ids = {row["extraction_id"] for row in results}
    if len(results) != EXPECTED or len(result_ids) != EXPECTED or result_ids != locked_ids:
        raise RuntimeError("coordinator union differs from locked queue")
    if any(row["extraction_status"] not in CONTROLLED for row in results):
        raise RuntimeError("uncontrolled extraction status")
    if any(row["global_analysis_readiness"] != "false" for row in results):
        raise RuntimeError("global analysis readiness boundary failed")
    artifacts = artifact_rows(results)
    assert_ignored(ARTIFACT_ROOT)
    if git_output("ls-files", "artifacts/local_extracted_text") or git_output("ls-files", "artifacts/local_retained_sources"):
        raise RuntimeError("normal Git tracks retained or extracted full-text artifacts")

    status_counts = Counter(row["extraction_status"] for row in results)
    attempted_types = Counter(
        "pdf" if row["retained_file_type"] == "pdf"
        else "html" if row["retained_file_type"] == "html"
        else "other_document"
        for row in results
    )
    ok_types = Counter(
        "pdf" if row["retained_file_type"] == "pdf"
        else "html" if row["retained_file_type"] == "html"
        else "other_document"
        for row in results if row["extraction_status"] == "extracted_ok"
    )
    total_bytes = sum(int(row["extracted_text_size_bytes"]) for row in artifacts)
    quality_repair_rows = 0
    quality_repair_files = []
    for lane in LANES:
        repair_path = OUTPUT / "lanes" / lane / f"lane_{lane[-3:]}_quality_repair.json"
        if repair_path.exists():
            repair = read_json(repair_path)
            quality_repair_rows += int(repair["repaired_row_count"])
            quality_repair_files.append(rel(repair_path))
    summary = {
        "task_id": TASK_ID,
        "extraction_queue_count": EXPECTED,
        "extraction_attempted_count": len(results),
        "completed_lane_count": 4,
        "lane_counts": LANES,
        "pdf_extraction_attempted_count": attempted_types["pdf"],
        "html_extraction_attempted_count": attempted_types["html"],
        "other_document_extraction_attempted_count": attempted_types["other_document"],
        "extraction_status_counts": dict(sorted(status_counts.items())),
        "extracted_ok_count": status_counts["extracted_ok"],
        "pdf_extracted_ok_count": ok_types["pdf"],
        "html_extracted_ok_count": ok_types["html"],
        "other_document_extracted_ok_count": ok_types["other_document"],
        "empty_or_too_short_count": status_counts["empty_or_too_short"],
        "low_text_density_count": status_counts["low_text_density"],
        "suspected_bad_text_layer_count": status_counts["suspected_bad_text_layer"],
        "html_noisy_or_shell_count": status_counts["html_noisy_or_shell"],
        "other_document_extraction_unsupported_count": status_counts["other_document_extraction_unsupported"],
        "extraction_error_count": status_counts["extraction_error"],
        "extracted_text_artifact_count": len(artifacts),
        "extracted_text_byte_total": total_bytes,
        "extracted_text_hash_manifest_count": len(artifacts),
        "checkpointed_quality_reclassification_count": quality_repair_rows,
        "quality_repair_source_reextraction_count": 0,
        "artifact_root": rel(ARTIFACT_ROOT),
        "artifact_root_git_ignored": True,
        "full_extracted_text_tracked_in_git": False,
        "retained_source_binaries_tracked_in_git": False,
        "source_review_download_reruns": 0,
        "redownloads": 0,
        "readiness_reruns": 0,
        "ocr_runs": 0,
        "pdf_render_runs": 0,
        "page_image_artifacts_saved": 0,
        "span_extraction_runs": 0,
        "evidence_rating_model_api_runs": 0,
        "ingestion_runs": 0,
        "codification_runs": 0,
        "quantitative_normalization_or_comparison_runs": 0,
        "wage_gap_regression_treatment_effect_runs": 0,
        "national_prevalence_or_final_causal_claims": 0,
        "global_analysis_readiness": False,
    }
    write_csv(OUTPUT / f"{PREFIX}_results.csv", results, RESULT_FIELDS)
    write_json(OUTPUT / f"{PREFIX}_results_summary.json", summary)
    write_csv(OUTPUT / f"{PREFIX}_pdf_results.csv",
              [row for row in results if row["retained_file_type"] == "pdf"], RESULT_FIELDS)
    write_csv(OUTPUT / f"{PREFIX}_html_results.csv",
              [row for row in results if row["retained_file_type"] == "html"], RESULT_FIELDS)
    write_csv(OUTPUT / f"{PREFIX}_other_document_results.csv",
              [row for row in results if row["retained_file_type"] not in {"pdf", "html"}], RESULT_FIELDS)
    extracted_ok = [row for row in results if row["extraction_status"] == "extracted_ok"]
    write_csv(OUTPUT / f"{PREFIX}_extracted_ok.csv", extracted_ok, RESULT_FIELDS)
    write_json(OUTPUT / f"{PREFIX}_extracted_ok_summary.json", {
        "extracted_ok_count": len(extracted_ok),
        "pdf_count": ok_types["pdf"], "html_count": ok_types["html"],
        "other_document_count": ok_types["other_document"],
        "all_rows_have_artifact_path_size_and_hash": all(
            row["extracted_text_artifact_path"] and row["extracted_text_size_bytes"]
            and len(row["extracted_text_sha256"]) == 64 for row in extracted_ok
        ),
        "deterministic_span_extraction_queue_count": len(extracted_ok),
    })
    categories = [
        ("empty_or_too_short", f"{PREFIX}_empty_or_too_short.csv"),
        ("low_text_density", f"{PREFIX}_low_text_density.csv"),
        ("suspected_bad_text_layer", f"{PREFIX}_suspected_bad_text_layer.csv"),
        ("html_noisy_or_shell", f"{PREFIX}_html_noisy_or_shell.csv"),
        ("other_document_extraction_unsupported", f"{PREFIX}_other_document_extraction_unsupported.csv"),
        ("extraction_error", f"{PREFIX}_extraction_errors.csv"),
    ]
    for status, filename in categories:
        write_status_manifest(results, status, filename)

    artifact_fields = (
        "extraction_id", "readiness_id", "source_review_download_id", "lane_id",
        "extraction_status", "text_artifact_group", "extracted_text_artifact_path",
        "extracted_text_size_bytes", "extracted_text_sha256", "artifact_storage_status",
    )
    write_csv(OUTPUT / f"{PREFIX}_extracted_text_manifest.csv", artifacts, artifact_fields)
    write_csv(OUTPUT / f"{PREFIX}_extracted_text_hash_manifest.csv", artifacts, artifact_fields)
    manifest_summary = {
        "artifact_count": len(artifacts), "unique_hash_count": len({row["extracted_text_sha256"] for row in artifacts}),
        "byte_total": total_bytes, "integrity_verified_count": len(artifacts),
        "artifact_root": rel(ARTIFACT_ROOT), "tracked_in_git_count": 0,
    }
    write_json(OUTPUT / f"{PREFIX}_extracted_text_manifest_summary.json", manifest_summary)
    write_json(OUTPUT / f"{PREFIX}_extracted_text_hash_manifest_summary.json", manifest_summary)
    no_tracked = {
        "checked_at": utc_now(), "artifact_root_git_ignored": True,
        "tracked_extracted_text_artifact_count": 0,
        "tracked_retained_source_binary_count": 0,
        "validation_passed": True,
    }
    write_json(OUTPUT / f"{PREFIX}_no_tracked_text_artifacts_validation.json", no_tracked)

    char_counts = [int(row["char_count"]) for row in results]
    buckets = [
        ("0-199", 0, 199), ("200-999", 200, 999), ("1,000-9,999", 1000, 9999),
        ("10,000-49,999", 10000, 49999), ("50,000-199,999", 50000, 199999),
        ("200,000+", 200000, 10**30),
    ]
    distribution = [{
        "char_count_bucket": name,
        "row_count": sum(lower <= value <= upper for value in char_counts),
    } for name, lower, upper in buckets]
    write_csv(OUTPUT / f"{PREFIX}_char_count_distribution.csv", distribution, ("char_count_bucket", "row_count"))
    write_json(OUTPUT / f"{PREFIX}_char_count_distribution_summary.json", {
        "row_count": len(char_counts), "minimum": min(char_counts),
        "median": median(char_counts), "maximum": max(char_counts),
        "total_characters": sum(char_counts),
    })
    write_json(OUTPUT / f"{PREFIX}_quality_summary.json", {
        "status_counts": dict(status_counts),
        "warning_count": sum(row["extraction_warning_flag"] == "true" for row in results),
        "repeated_garbage_flag_count": sum(row["repeated_garbage_flag"] == "true" for row in results),
        "encoding_issue_flag_count": sum(row["encoding_issue_flag"] == "true" for row in results),
        "suspected_scanned_pdf_flag_count": sum(row["suspected_scanned_pdf_flag"] == "true" for row in results),
        "html_shell_flag_count": sum(row["html_shell_flag"] == "true" for row in results),
        "checkpointed_quality_reclassification_count": quality_repair_rows,
        "quality_repair_source_reextraction_count": 0,
    })
    write_json(OUTPUT / f"{PREFIX}_quality_rule_repair.json", {
        "repair_reason": "fixed-width PDF spacing initially triggered an over-broad repeated-character rule",
        "reclassified_saved_artifact_count": quality_repair_rows,
        "source_reextraction_count": 0,
        "repair_files": quality_repair_files,
        "final_repeated_character_rule": "80 or more identical alphanumeric characters",
    })
    write_text(OUTPUT / f"{PREFIX}_quality_rule_repair.md",
        "# Bounded quality-rule repair\n\n"
        f"A live checkpoint audit detected an over-broad spacing heuristic. The workers were "
        f"stopped, {quality_repair_rows:,} already-saved ignored text artifacts were deterministically "
        "reclassified, and the original absolute stagger schedule was resumed. No retained source "
        "was redownloaded, OCRed, rendered, or re-extracted by the repair.")
    for name, key in (
        ("low_density", "low_text_density"), ("bad_text_layer", "suspected_bad_text_layer"),
        ("html_noise", "html_noisy_or_shell"),
    ):
        write_json(OUTPUT / f"{PREFIX}_{name}_summary.json", {
            "status": key, "count": status_counts[key],
            "excluded_from_span_extraction_ready": True,
        })
    write_json(OUTPUT / f"{PREFIX}_empty_or_too_short_summary.json", {
        "count": status_counts["empty_or_too_short"], "excluded_from_span_extraction_ready": True,
    })
    write_json(OUTPUT / f"{PREFIX}_other_document_extraction_unsupported_summary.json", {
        "count": status_counts["other_document_extraction_unsupported"], "excluded_from_span_extraction_ready": True,
    })
    write_json(OUTPUT / f"{PREFIX}_extraction_errors_summary.json", {
        "count": status_counts["extraction_error"], "excluded_from_span_extraction_ready": True,
    })

    for field in ("state", "region", "municipality", "source_family_hint"):
        grouped = grouped_summary(results, field)
        stem = "source_family" if field == "source_family_hint" else field
        write_csv(OUTPUT / f"{PREFIX}_{stem}_summary.csv", grouped, grouped[0].keys())
        write_json(OUTPUT / f"{PREFIX}_{stem}_summary.json", {
            "group_field": field, "group_count": len(grouped),
            "attempted_count": sum(row["attempted_count"] for row in grouped),
            "extracted_ok_count": sum(row["extracted_ok_count"] for row in grouped),
            "rows": grouped,
        })
    exact_cba = [row for row in results if row["source_family_hint"] == "cba"]
    non_cba_ok = [
        row for row in extracted_ok
        if row["source_family_hint"] != "cba"
    ]
    cba_rate = len(exact_cba) / len(results) * 100
    write_json(OUTPUT / f"{PREFIX}_non_cba_extracted_ok_summary.json", {
        "non_cba_or_mixed_extracted_ok_count": len(non_cba_ok),
        "definition": "source_family_hint is not exact cba",
    })
    write_text(OUTPUT / f"{PREFIX}_cba_concentration_report.md",
        "# CBA concentration\n\n"
        f"Exact CBA rows in the locked extraction queue: {len(exact_cba):,} of {len(results):,} "
        f"({cba_rate:.2f}%). This is a source-family distribution only, not an evidence rating or claim.")

    lane_matrix = [{
        "lane_id": item["lane_id"], "queue_count": item["queue_count"],
        "completed_count": item["completed_count"], "complete": str(item["complete"]).lower(),
        "standard_delay_seconds": item["standard_delay_seconds"],
        "started_at": item["started_at"], "ended_at": item["ended_at"],
        "extracted_ok_count": item["status_counts"].get("extracted_ok", 0),
        "error_count": item["status_counts"].get("extraction_error", 0),
    } for item in lane_summaries]
    write_csv(OUTPUT / f"{PREFIX}_lane_status_matrix.csv", lane_matrix, lane_matrix[0].keys())
    starts = [datetime.fromisoformat(item["started_at"].replace("Z", "+00:00")) for item in lane_summaries]
    ends = [datetime.fromisoformat(item["ended_at"].replace("Z", "+00:00")) for item in lane_summaries]
    adjacent_overlap = [ends[index] > starts[index + 1] for index in range(3)]
    start_offsets = [(starts[index] - starts[0]).total_seconds() for index in range(4)]
    overlap_ok = all(adjacent_overlap)
    stagger_offsets_ok = all(
        abs(observed - expected) <= 2
        for observed, expected in zip(start_offsets, (0, 480, 960, 1440))
    )
    if not overlap_ok or not stagger_offsets_ok:
        raise RuntimeError("required standard stagger and controlled lane overlap were not achieved")
    write_text(OUTPUT / f"{PREFIX}_parallel_execution_report.md",
        "# Parallel execution report\n\n"
        "Four independent worker processes were launched together and used the required bounded "
        "T+0 / T+8 / T+16 / T+24 start delays. Each adjacent pair overlapped in execution. "
        f"Observed start offsets in seconds: {', '.join(str(int(value)) for value in start_offsets)}. "
        "UTC checkpoint timestamps have one-second resolution and all offsets are within two seconds "
        "of the exact standard. "
        "A bounded quality-rule restart preserved the original lane-001 start and absolute standard "
        "start gates; already checkpointed artifacts were reclassified without source re-extraction.")
    write_text(OUTPUT / f"{PREFIX}_resumability_report.md",
        "# Resumability report\n\n"
        "Every lane appended one lightweight result and atomically rewrote its checkpoint after "
        "each source. All four lanes completed; no resume is currently required.")
    lane_standard = {
        "independent_lane_count": 4, "standard_stagger_seconds": [0, 480, 960, 1440],
        "checkpoint_after_each_row": True, "lane_output_isolation": True,
        "coordinator_only_shared_outputs": True, "controlled_overlap_required": True,
        "full_text_storage": "ignored_artifact_storage_only",
    }
    write_json(OUTPUT / "future_text_extraction_parallel_lane_execution_standard.json", lane_standard)
    write_text(OUTPUT / "future_text_extraction_parallel_lane_execution_standard.md",
        "# Future text-extraction parallel-lane standard\n\n"
        "Large local text passes use four isolated, resumable workers at T+0, T+8, T+16, and "
        "T+24 minutes with controlled overlap. Workers may write full text only to ignored "
        "artifact storage and never mutate shared dashboard or summary outputs.")

    dashboard_summary = {
        "dashboard_update_required": True, "current_operation_updated": True,
        "next_authorized_stage": "deterministic span/evidence extraction over extracted-ok text only",
        **summary, "map_filter": "total_scout_coverage_only", "map_data_date": "2026-07-27",
    }
    write_json(OUTPUT / f"{PREFIX}_dashboard_update_summary.json", dashboard_summary)
    write_text(OUTPUT / f"{PREFIX}_dashboard_update_summary.md",
        "# Dashboard update summary\n\n"
        f"The completed extraction summary records {len(results):,} attempts and "
        f"{len(extracted_ok):,} extracted-ok artifacts. The current operation advances to "
        "text extraction complete and the next authorized stage is deterministic span extraction. "
        "The map remains total scout coverage only and global analysis readiness remains false.")
    overview = {
        "sync_required": True, "sync_source": rel(OUTPUT / f"{PREFIX}_results_summary.json"),
        "required_extraction_metrics_present": True, "current_operation_updated": True,
        "next_authorized_stage_updated": True, "map_metric_unchanged": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "dashboard_overview_metric_sync_after_text_extraction.json", overview)
    write_text(OUTPUT / "dashboard_overview_metric_sync_after_text_extraction.md",
        "# Dashboard overview metric sync\n\n"
        "The dashboard builder consumes the merged extraction summary and exposes attempted, "
        "extracted-ok, file-type, quality, error, and ignored-storage metrics.")
    stale = {
        "stale_readiness_complete_current_operation_blocked": True,
        "completed_text_extraction_is_current_operation": True,
        "map_filter_guard": "total_scout_coverage_only",
        "global_analysis_readiness": False,
    }
    write_json(OUTPUT / "dashboard_stale_overview_guard_after_text_extraction.json", stale)
    write_text(OUTPUT / "dashboard_stale_overview_guard_after_text_extraction.md",
        "# Dashboard stale-overview guard\n\n"
        "Text extraction complete supersedes PDF/text-layer readiness complete as the current "
        "operation. Tests guard the map contract and false global readiness.")

    write_text(OUTPUT / f"{PREFIX}_span_extraction_planning_note.md",
        "# Deterministic span-extraction planning\n\n"
        f"The next bounded queue contains only the {len(extracted_ok):,} extracted-ok rows with "
        "hash-valid ignored full-text artifacts. Empty, low-density, bad-layer, noisy, unsupported, "
        "and error rows are excluded. The next stage may capture exact verbatim evidence spans but "
        "must not rate, ingest, codify, normalize wages, or make causal or prevalence claims.")
    write_text(OUTPUT / f"{PREFIX}_next_queue_recommendation.md",
        "# Next queue recommendation\n\n"
        f"Authorize a four-lane deterministic span/evidence extraction pass over {len(extracted_ok):,} "
        "extracted-ok artifacts. Lock and split that queue only after artifact hash validation.")
    span_base, span_remainder = divmod(len(extracted_ok), 4)
    span_lane_counts = [
        span_base + (1 if index < span_remainder else 0) for index in range(4)
    ]
    future_prompt = f"""PROJECT: Gabriel Wages

Task: Run bounded deterministic verbatim span/evidence extraction over exactly {len(extracted_ok):,}
extracted-ok local text artifacts from task {TASK_ID}.

Use exactly four simultaneous independently checkpointed lanes with standard T+0, T+8, T+16,
and T+24 starts and controlled overlap. Exact lane sizes:
{span_lane_counts[0]:,} / {span_lane_counts[1]:,} / {span_lane_counts[2]:,} / {span_lane_counts[3]:,}.
Build the queue only
from {PREFIX}_extracted_ok.csv,
revalidate each ignored text artifact path/size/SHA-256, and keep full text out of Git.

Capture exact verbatim spans only. Do not paraphrase, rate evidence, call model/API systems,
ingest, codify, normalize or compare wages, calculate wage gaps, run regressions, estimate
treatment effects, make prevalence/final causal claims, run OCR, render PDFs, redownload, or
rerun readiness/text extraction. Keep causal and discourse corpora separate. Update dashboard
overview/status once from merged outcomes; the map remains total scout coverage only and global
analysis readiness remains false.

No OCR or rendering is authorized. Global analysis readiness remains false.

Before any future rating task closes, verify downstream summary inputs exist. Reconstruct only
fully derivable missing summaries from committed valid/quarantine/results ledgers, validate,
commit/push, and continue; fail closed for non-derivable artifacts.
"""
    write_text(OUTPUT / "next_combined_broad_span_extraction_prompt.md", future_prompt)
    write_text(OUTPUT / "next_task.md",
        "# Next task\n\n"
        f"Run the prompt in next_combined_broad_span_extraction_prompt.md over the "
        f"{len(extracted_ok):,} extracted-ok ignored text artifacts in exact lanes "
        f"{span_lane_counts[0]:,} / {span_lane_counts[1]:,} / {span_lane_counts[2]:,} / "
        f"{span_lane_counts[3]:,}. Do not rerun downloading, "
        "readiness, or text extraction.")
    invariants = {
        "queue_count_exact": len(results) == EXPECTED,
        "lane_counts_exact": all(item["completed_count"] == LANES[item["lane_id"]] for item in lane_summaries),
        "master_equals_lane_union": result_ids == locked_ids,
        "approved_readiness_only": all(row["readiness_status"] in APPROVED for row in results),
        "excluded_readiness_status_count": sum(row["readiness_status"] in EXCLUDED for row in results),
        "controlled_extraction_statuses": all(row["extraction_status"] in CONTROLLED for row in results),
        "extracted_ok_has_hashes": all(row["extracted_text_artifact_path"] and len(row["extracted_text_sha256"]) == 64 for row in extracted_ok),
        "full_text_tracked_count": 0, "retained_binary_tracked_count": 0,
        "four_lanes_completed": True, "staggered_overlap_achieved": overlap_ok,
        "standard_stagger_offsets_achieved": stagger_offsets_ok,
        "global_analysis_readiness": False,
        "forbidden_actions_performed": [],
    }
    write_json(OUTPUT / f"{PREFIX}_invariant_checks.json", invariants)
    write_text(OUTPUT / f"{PREFIX}_stress_test_report.md",
        "# Stress-test report\n\n"
        "Fail-closed checks cover wrong queue/lane cardinality, rows outside the lock, excluded "
        "readiness states, path/size/hash mismatch, uncontrolled statuses, missing or changed text "
        "artifacts, tracked artifact roots, incomplete lanes, and absent controlled overlap.")
    write_json(OUTPUT / f"{PREFIX}_regression_test_inventory.json", {
        "new_suite": "scripts/test_combined_broad_text_extraction_4051.py",
        "predecessor_suites": [
            "scripts/test_retained_source_storage_history_repair.py",
            "scripts/test_combined_broad_pdf_text_layer_readiness_4961.py",
            "scripts/test_combined_broad_source_review_download_5589.py",
            "scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py",
        ],
        "dashboard_map_guard": True, "artifact_storage_guard": True,
    })
    write_text(OUTPUT / f"{PREFIX}_validation_2026-07-28.md",
        "# Validation report\n\n"
        "Coordinator invariants passed for the locked queue, four completed lanes, artifact "
        "integrity, controlled statuses, ignored storage, controlled overlap, and prohibited-action "
        "boundaries. Repository test/build command results are added after execution.")

    decision_value = "combined_broad_text_extraction_4051_completed_span_extraction_ready"
    decision = {
        "task_id": TASK_ID, "decision": decision_value, **summary,
        "all_four_lanes_complete": True, "staggered_overlap_achieved": True,
        "dashboard_updated": True, "dashboard_map_filter": "total_scout_coverage_only",
        "deterministic_span_extraction_ready_next": True,
    }
    write_json(OUTPUT / f"{PREFIX}_decision.json", decision)
    write_text(OUTPUT / f"{PREFIX}_summary.md",
        "# Combined broad text extraction — 4,051 readiness-approved sources\n\n"
        f"All four isolated staggered lanes completed the locked queue. Extracted OK: "
        f"{status_counts['extracted_ok']:,}; empty/too short: {status_counts['empty_or_too_short']:,}; "
        f"low density: {status_counts['low_text_density']:,}; suspected bad layer: "
        f"{status_counts['suspected_bad_text_layer']:,}; HTML noisy/shell: "
        f"{status_counts['html_noisy_or_shell']:,}; other unsupported: "
        f"{status_counts['other_document_extraction_unsupported']:,}; errors: "
        f"{status_counts['extraction_error']:,}.\n\nDecision: {decision_value}. Full text remains "
        "in ignored local artifact storage. No OCR, rendering, span extraction, rating/model work, "
        "ingestion, codification, quantitative analysis, prevalence claim, or causal claim occurred. "
        "Global analysis readiness remains false.")
    result_note = ROOT / "docs/analysis/combined_broad_text_extraction_4051_result_2026-07-28.md"
    status_note = ROOT / "docs/analysis/combined_broad_text_extraction_4051_dashboard_status_note_2026-07-28.md"
    write_text(result_note,
        "# Combined broad text-extraction result\n\n"
        f"Four isolated staggered lanes attempted {len(results):,} readiness-approved local sources; "
        f"{len(extracted_ok):,} passed extraction quality gates for later deterministic span extraction. "
        f"Full text is local and Git-ignored at {rel(ARTIFACT_ROOT)}. Global analysis readiness is false.")
    write_text(status_note,
        "# Dashboard status note\n\n"
        "Current operation: combined broad text extraction complete. Next authorized stage: "
        "deterministic verbatim span/evidence extraction over extracted-ok artifacts only. "
        "The national map remains cumulative total scout coverage only (data date 2026-07-27). "
        "Global analysis readiness remains false.")
    print(json.dumps({"status": "coordinator_completed", "decision": decision_value, **summary}))


def validate_complete() -> None:
    decision = read_json(OUTPUT / f"{PREFIX}_decision.json")
    summary = read_json(OUTPUT / f"{PREFIX}_results_summary.json")
    queue = read_csv(OUTPUT / f"{PREFIX}_locked_queue.csv")
    results = read_csv(OUTPUT / f"{PREFIX}_results.csv")
    ok_rows = read_csv(OUTPUT / f"{PREFIX}_extracted_ok.csv")
    if not (
        decision.get("decision") == "combined_broad_text_extraction_4051_completed_span_extraction_ready"
        and len(queue) == len(results) == EXPECTED
        and len({row["extraction_id"] for row in queue}) == EXPECTED
        and {row["extraction_id"] for row in queue} == {row["extraction_id"] for row in results}
        and len(ok_rows) == summary.get("extracted_ok_count")
        and all(row["extraction_status"] == "extracted_ok" for row in ok_rows)
        and decision.get("global_analysis_readiness") is False
    ):
        raise RuntimeError("completed extraction outputs fail closed validation")
    assert_ignored(ARTIFACT_ROOT)
    if git_output("ls-files", "artifacts/local_extracted_text"):
        raise RuntimeError("extracted full text is tracked")
    print(json.dumps({"status": "completed_outputs_valid_zero_writes", "rows": EXPECTED}))


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--lane", choices=tuple(LANES))
    action.add_argument("--launch", action="store_true")
    action.add_argument("--resume-launch", action="store_true")
    action.add_argument("--coordinate", action="store_true")
    action.add_argument("--validate", action="store_true")
    action.add_argument("--repair-quality-flags", action="store_true")
    parser.add_argument("--stagger-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.lane:
        run_lane(args.lane, args.stagger_seconds)
    elif args.launch:
        launch()
    elif args.resume_launch:
        launch(resume=True)
    elif args.coordinate:
        coordinate()
    elif args.validate:
        validate_complete()
    else:
        repair_quality_flags()


if __name__ == "__main__":
    main()
