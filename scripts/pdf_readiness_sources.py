#!/usr/bin/env python3
"""Run bounded local-only PDF page-count and text-layer readiness checks.

No URL or network client exists in this module. The runner verifies the
locked local artifact, hash, size, and PDF signature before opening it with
``pypdf``. It samples at most a configured number of pages, retains only
counts and status fields, saves no extracted text, and never performs OCR,
wage extraction, ingestion, or codification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import re
import signal
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from pypdf import PdfReader

from prepare_pdf_readiness_pilot import INPUT_FIELDS, ROOT


READINESS_FIELDS = [
    "readiness_status",
    "readiness_status_detail",
    "artifact_exists",
    "artifact_hash_verified",
    "pdf_signature_valid",
    "parser_library",
    "parser_version",
    "parser_elapsed_seconds",
    "pdf_page_count",
    "text_layer_status",
    "sampled_pages_checked",
    "sampled_pages_with_text",
    "text_chars_sampled_total",
    "text_extraction_error_type",
    "text_extraction_error_sanitized",
    "technical_parseability_rating",
    "recommended_next_action",
    "ocr_needed_signal",
    "reviewer",
    "reviewed_at",
]
LEDGER_FIELDS = INPUT_FIELDS + READINESS_FIELDS
TIMING_FIELDS = [
    "row_number",
    "pdf_readiness_id",
    "source_review_id",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "local_artifact_opened",
    "hash_verified",
    "pdf_opened",
    "pages_sampled",
    "ocr_run",
]
TERMINAL_STATUSES = {
    "readiness_checked",
    "artifact_missing",
    "hash_mismatch",
    "artifact_problem",
    "parser_error",
}
DRY_STATUS = "planned_not_checked"
SENSITIVE_ERROR_PATTERN = re.compile(
    r"(?i)(https?://|token|cookie|authorization|api[_-]?key|password)"
)


class FileTimeoutError(TimeoutError):
    """A per-file local parser deadline was exceeded."""


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(
    path: Path, rows: list[dict[str, str]], fields: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_artifact(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def sanitized_exception_type(exc: BaseException) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", type(exc).__name__)
    return (clean or "unknown")[:80]


def sanitized_error(exc: BaseException) -> str:
    message = re.sub(r"\s+", " ", str(exc)).strip()
    if SENSITIVE_ERROR_PATTERN.search(message):
        return "parser_error_details_redacted"
    message = re.sub(r"[/\\\\][^\s]+", "[path]", message)
    return message[:240] or sanitized_exception_type(exc)


@contextmanager
def file_deadline(seconds: float) -> Iterator[None]:
    if seconds <= 0:
        raise ValueError("timeout per file must be positive")
    if not hasattr(signal, "setitimer"):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def handle_timeout(_signum: int, _frame: object) -> None:
        raise FileTimeoutError("bounded local PDF parser timeout")

    signal.signal(signal.SIGALRM, handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def page_sample_indexes(page_count: int, maximum: int) -> list[int]:
    if page_count <= 0 or maximum <= 0:
        return []
    if page_count <= maximum:
        return list(range(page_count))
    if maximum == 1:
        return [0]
    candidates = [0, page_count // 2, page_count - 1]
    if maximum > 3:
        step = (page_count - 1) / (maximum - 1)
        candidates = [round(index * step) for index in range(maximum)]
    result: list[int] = []
    for index in candidates:
        if index not in result:
            result.append(index)
        if len(result) == maximum:
            break
    return result


def classify_text_layer(
    checked: int, with_text: int
) -> tuple[str, str, str]:
    if checked <= 0:
        return "unknown", "unknown", "manual_review"
    if with_text == checked:
        return "present", "high", "parse_text_layer_later"
    if with_text > 0:
        return "partial", "medium", "parse_text_layer_later"
    return "absent", "low", "ocr_later"


def base_result(row: dict[str, str]) -> dict[str, str]:
    result = {field: row.get(field, "") for field in INPUT_FIELDS}
    result.update(
        {
            "readiness_status": "",
            "readiness_status_detail": "",
            "artifact_exists": "unknown",
            "artifact_hash_verified": "unknown",
            "pdf_signature_valid": "unknown",
            "parser_library": "pypdf",
            "parser_version": importlib.metadata.version("pypdf"),
            "parser_elapsed_seconds": "0.000000",
            "pdf_page_count": "unknown",
            "text_layer_status": "unknown",
            "sampled_pages_checked": "0",
            "sampled_pages_with_text": "0",
            "text_chars_sampled_total": "0",
            "text_extraction_error_type": "",
            "text_extraction_error_sanitized": "",
            "technical_parseability_rating": "unknown",
            "recommended_next_action": "manual_review",
            "ocr_needed_signal": "unknown",
            "reviewer": "script_local_pdf_readiness",
            "reviewed_at": now_utc(),
        }
    )
    return result


def inspect_artifact(
    row: dict[str, str],
    *,
    max_pages_to_sample: int,
    max_text_chars_per_page: int,
    timeout_per_file: float,
    reader_factory: Callable[..., object] = PdfReader,
) -> tuple[dict[str, str], dict[str, int]]:
    result = base_result(row)
    counters = {
        "local_artifact_opened": 0,
        "hash_verified": 0,
        "pdf_opened": 0,
        "pages_sampled": 0,
    }
    started = time.monotonic()
    artifact = resolve_artifact(row["content_artifact_path"])
    if not artifact.is_file():
        result.update(
            {
                "readiness_status": "artifact_missing",
                "readiness_status_detail": "retained artifact path is missing",
                "artifact_exists": "no",
                "artifact_hash_verified": "no",
                "pdf_signature_valid": "unknown",
                "technical_parseability_rating": "not_ready",
                "recommended_next_action": "inspect_artifact_problem",
                "ocr_needed_signal": "unknown",
            }
        )
        result["parser_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
        return result, counters

    result["artifact_exists"] = "yes"
    counters["local_artifact_opened"] = 1
    actual_size = artifact.stat().st_size
    try:
        expected_size = int(row["content_byte_size"])
    except ValueError:
        expected_size = -1
    actual_hash = sha256_file(artifact)
    if actual_hash != row["content_hash"] or actual_size != expected_size:
        result.update(
            {
                "readiness_status": "hash_mismatch",
                "readiness_status_detail": (
                    "retained artifact hash or byte size does not match "
                    "the durable source-review record"
                ),
                "artifact_hash_verified": "no",
                "pdf_signature_valid": "unknown",
                "technical_parseability_rating": "not_ready",
                "recommended_next_action": "inspect_artifact_problem",
                "ocr_needed_signal": "unknown",
            }
        )
        result["parser_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
        return result, counters
    result["artifact_hash_verified"] = "yes"
    counters["hash_verified"] = 1

    with artifact.open("rb") as handle:
        signature = handle.read(5)
    if signature != b"%PDF-":
        result.update(
            {
                "readiness_status": "artifact_problem",
                "readiness_status_detail": "retained artifact lacks PDF signature",
                "pdf_signature_valid": "no",
                "technical_parseability_rating": "not_ready",
                "recommended_next_action": "inspect_artifact_problem",
                "ocr_needed_signal": "unknown",
            }
        )
        result["parser_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
        return result, counters
    result["pdf_signature_valid"] = "yes"

    try:
        with file_deadline(timeout_per_file):
            reader = reader_factory(artifact, strict=False)
            pages = getattr(reader, "pages")
            page_count = len(pages)
            counters["pdf_opened"] = 1
            indexes = page_sample_indexes(page_count, max_pages_to_sample)
            pages_with_text = 0
            chars_total = 0
            extraction_errors: list[BaseException] = []
            for page_index in indexes:
                try:
                    text = pages[page_index].extract_text() or ""
                    bounded = text[:max_text_chars_per_page]
                    chars = len(bounded.strip())
                    chars_total += chars
                    if chars > 0:
                        pages_with_text += 1
                except Exception as exc:  # parser-specific page failure
                    extraction_errors.append(exc)
            checked = len(indexes)
            counters["pages_sampled"] = checked
            text_status, parseability, next_action = classify_text_layer(
                checked, pages_with_text
            )
            if extraction_errors and pages_with_text:
                text_status, parseability = "partial", "medium"
            elif extraction_errors and not pages_with_text:
                text_status, parseability = "parser_error", "low"
                next_action = "retry_with_different_parser"
            result.update(
                {
                    "readiness_status": "readiness_checked",
                    "readiness_status_detail": (
                        "bounded local page-count and sampled text-layer "
                        "check completed; no text retained"
                    ),
                    "pdf_page_count": str(page_count),
                    "text_layer_status": text_status,
                    "sampled_pages_checked": str(checked),
                    "sampled_pages_with_text": str(pages_with_text),
                    "text_chars_sampled_total": str(chars_total),
                    "technical_parseability_rating": parseability,
                    "recommended_next_action": next_action,
                    "ocr_needed_signal": (
                        "yes" if text_status == "absent" else "no"
                        if text_status in {"present", "partial"}
                        else "unknown"
                    ),
                }
            )
            if extraction_errors:
                first = extraction_errors[0]
                result["text_extraction_error_type"] = (
                    sanitized_exception_type(first)
                )
                result["text_extraction_error_sanitized"] = sanitized_error(
                    first
                )
    except Exception as exc:
        result.update(
            {
                "readiness_status": "parser_error",
                "readiness_status_detail": (
                    "bounded local PDF parser could not complete"
                ),
                "text_layer_status": "parser_error",
                "text_extraction_error_type": sanitized_exception_type(exc),
                "text_extraction_error_sanitized": sanitized_error(exc),
                "technical_parseability_rating": "not_ready",
                "recommended_next_action": "retry_with_different_parser",
                "ocr_needed_signal": "unknown",
            }
        )
    result["parser_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
    return result, counters


def validate_inputs(
    fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    missing = sorted(set(INPUT_FIELDS) - set(fieldnames))
    if missing:
        raise ValueError(f"input CSV missing fields: {missing}")
    if not rows:
        raise ValueError("input CSV is empty")
    for field in (
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        values = [row.get(field, "") for row in rows]
        if any(not value for value in values):
            raise ValueError(f"blank required identity: {field}")
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate identity: {field}")
    for row in rows:
        if (
            not row.get("content_artifact_path")
            or not row.get("content_hash")
            or row.get("content_type_observed") != "application/pdf"
        ):
            raise ValueError("input contains a non-retained-PDF row")


def summary_payload(
    *,
    rows: list[dict[str, str]],
    mode: str,
    elapsed: float,
    counters: Counter[str],
    args: argparse.Namespace,
) -> dict[str, object]:
    distributions = {
        field: dict(sorted(Counter(row[field] for row in rows).items()))
        for field in (
            "readiness_status",
            "text_layer_status",
            "technical_parseability_rating",
            "recommended_next_action",
        )
    }
    page_counts = [
        int(row["pdf_page_count"])
        for row in rows
        if row["pdf_page_count"].isdigit()
    ]
    return {
        "schema_version": "1.0.0",
        "status": (
            "pdf_readiness_dry_run_complete"
            if mode == "dry_run"
            else "pdf_readiness_local_collection_complete"
        ),
        "mode": mode,
        "input_csv": args.input_csv,
        "output_dir": args.output_dir,
        "rows": len(rows),
        "terminal_rows": (
            sum(row["readiness_status"] in TERMINAL_STATUSES for row in rows)
            if mode == "local"
            else sum(row["readiness_status"] == DRY_STATUS for row in rows)
        ),
        **distributions,
        "page_count_summary": {
            "count": len(page_counts),
            "minimum": min(page_counts) if page_counts else None,
            "maximum": max(page_counts) if page_counts else None,
            "total": sum(page_counts),
        },
        "sampled_pages_checked": sum(
            int(row["sampled_pages_checked"]) for row in rows
        ),
        "sampled_pages_with_text": sum(
            int(row["sampled_pages_with_text"]) for row in rows
        ),
        "text_chars_sampled_total": sum(
            int(row["text_chars_sampled_total"]) for row in rows
        ),
        "parser_library": "pypdf",
        "parser_version": importlib.metadata.version("pypdf"),
        "elapsed_seconds": round(elapsed, 6),
        "local_artifacts_opened": counters["local_artifact_opened"],
        "artifact_hashes_verified": counters["hash_verified"],
        "pdfs_opened_for_readiness": counters["pdf_opened"],
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "redownloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "wage_tables_extracted": 0,
        "wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_readiness_merges": 0,
        "completed_at": now_utc(),
    }


def run(
    args: argparse.Namespace,
    *,
    inspector: Callable[..., tuple[dict[str, str], dict[str, int]]] = (
        inspect_artifact
    ),
) -> dict[str, object]:
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if args.max_pages_to_sample <= 0 or args.max_text_chars_per_page <= 0:
        raise ValueError("page and text sample limits must be positive")
    if not args.no_save_text:
        raise ValueError("--no-save-text is mandatory")
    fieldnames, rows = read_csv(input_path)
    validate_inputs(fieldnames, rows)
    if args.max_rows is not None:
        if args.max_rows <= 0:
            raise ValueError("max rows must be positive")
        rows = rows[: args.max_rows]
    output_dir.mkdir(parents=True)
    started = time.monotonic()
    counters: Counter[str] = Counter()
    output_rows: list[dict[str, str]] = []
    timing_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        row_started = now_utc()
        row_clock = time.monotonic()
        if args.dry_run:
            result = base_result(row)
            result.update(
                {
                    "readiness_status": DRY_STATUS,
                    "readiness_status_detail": (
                        "dry-run schema validation only; artifact not opened"
                    ),
                    "artifact_exists": "not_checked",
                    "artifact_hash_verified": "not_checked",
                    "pdf_signature_valid": "not_checked",
                    "parser_library": "not_invoked",
                    "parser_version": "",
                    "reviewer": "script_pdf_readiness_dry_run",
                }
            )
            row_counters = {
                "local_artifact_opened": 0,
                "hash_verified": 0,
                "pdf_opened": 0,
                "pages_sampled": 0,
            }
        else:
            result, row_counters = inspector(
                row,
                max_pages_to_sample=args.max_pages_to_sample,
                max_text_chars_per_page=args.max_text_chars_per_page,
                timeout_per_file=args.timeout_per_file,
            )
        counters.update(row_counters)
        output_rows.append(result)
        timing_rows.append(
            {
                "row_number": str(index),
                "pdf_readiness_id": row["pdf_readiness_id"],
                "source_review_id": row["source_review_id"],
                "status": result["readiness_status"],
                "started_at": row_started,
                "completed_at": now_utc(),
                "elapsed_seconds": f"{time.monotonic() - row_clock:.6f}",
                "local_artifact_opened": str(
                    row_counters["local_artifact_opened"]
                ),
                "hash_verified": str(row_counters["hash_verified"]),
                "pdf_opened": str(row_counters["pdf_opened"]),
                "pages_sampled": str(row_counters["pages_sampled"]),
                "ocr_run": "0",
            }
        )
        # Checkpoint without ever persisting extracted text.
        write_csv(
            output_dir / "pdf_readiness_ledger.csv",
            output_rows,
            LEDGER_FIELDS,
        )
        write_csv(
            output_dir / "pdf_readiness_timing.csv",
            timing_rows,
            TIMING_FIELDS,
        )
    mode = "dry_run" if args.dry_run else "local"
    summary = summary_payload(
        rows=output_rows,
        mode=mode,
        elapsed=time.monotonic() - started,
        counters=counters,
        args=args,
    )
    write_json(output_dir / "pdf_readiness_summary.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--max-pages-to-sample", type=int, default=3)
    parser.add_argument("--max-text-chars-per-page", type=int, default=500)
    parser.add_argument("--timeout-per-file", type=float, default=20.0)
    parser.add_argument(
        "--no-save-text",
        dest="no_save_text",
        action="store_true",
        default=True,
        help="Mandatory safety flag; full extracted text is never written.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run(args)
    print(
        "PDF readiness "
        f"{summary['mode']}: {summary['terminal_rows']}/"
        f"{summary['rows']} terminal; URLs=0 OCR=0 text artifacts=0."
    )


if __name__ == "__main__":
    main()
