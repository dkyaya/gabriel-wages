#!/usr/bin/env python3
"""Run bounded local-only text-layer and table-detection checks.

The runner has no network client. It verifies each locked retained artifact,
opens only local PDFs, scans a bounded deterministic page sample, saves no
page or document text, runs no OCR, and extracts no final wage values.
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

from prepare_text_table_detection_pilot import INPUT_FIELDS, ROOT


DETECTION_FIELDS = [
    "detection_status",
    "detection_status_detail",
    "parser_library",
    "parser_version",
    "parser_elapsed_seconds",
    "pages_scanned",
    "pages_with_text",
    "total_text_chars_scanned",
    "wage_table_signal",
    "wage_table_signal_confidence",
    "candidate_wage_pages",
    "candidate_wage_page_count",
    "contract_period_signal",
    "contract_period_confidence",
    "candidate_contract_period_text",
    "pay_schedule_signal",
    "salary_schedule_signal",
    "hourly_rate_signal",
    "step_grade_signal",
    "rank_position_signal",
    "effective_date_signal",
    "bargaining_unit_signal",
    "public_safety_signal",
    "non_safety_signal",
    "table_like_structure_signal",
    "table_detection_method",
    "extraction_pilot_priority",
    "recommended_next_action",
    "detection_notes",
    "reviewer",
    "reviewed_at",
]

LEDGER_FIELDS = INPUT_FIELDS + DETECTION_FIELDS
TIMING_FIELDS = [
    "row_number",
    "text_table_detection_id",
    "pdf_readiness_id",
    "source_review_id",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "local_artifact_opened",
    "hash_verified",
    "pdf_opened",
    "pages_scanned",
    "ocr_run",
]
TERMINAL_STATUSES = {
    "detection_checked",
    "no_text_available",
    "parser_error",
    "artifact_missing",
    "hash_mismatch",
    "skipped_not_parse_text_candidate",
    "error",
}
DRY_STATUS = "planned_not_detected"
MAX_CONTRACT_HINT_CHARS = 300
TABLE_METHOD = "bounded_keyword_numeric_structure_v1"
SENSITIVE_ERROR_PATTERN = re.compile(
    r"(?i)(https?://|token|cookie|authorization|api[_-]?key|password)"
)

WAGE_RE = re.compile(r"\bwages?\b", re.IGNORECASE)
SALARY_RE = re.compile(r"\bsalar(?:y|ies)\b", re.IGNORECASE)
COMPENSATION_RE = re.compile(r"\bcompensation\b", re.IGNORECASE)
PAY_SCHEDULE_RE = re.compile(
    r"\b(?:pay|wage|salary)\s+(?:schedule|scale|plan|table)\b",
    re.IGNORECASE,
)
HOURLY_RE = re.compile(
    r"\b(?:hourly|per\s+hour|hourly\s+rate)\b", re.IGNORECASE
)
ANNUAL_RE = re.compile(
    r"\b(?:annual|annually|per\s+annum)\b", re.IGNORECASE
)
STEP_GRADE_RE = re.compile(
    r"\b(?:step|grade|range|classification)\b", re.IGNORECASE
)
RANK_POSITION_RE = re.compile(
    r"\b(?:rank|position|title|classification)\b", re.IGNORECASE
)
EFFECTIVE_RE = re.compile(
    r"\b(?:effective|commencing|beginning|expires?|expiration|"
    r"term\s+of\s+agreement)\b",
    re.IGNORECASE,
)
AGREEMENT_RE = re.compile(
    r"\b(?:agreement|contract|collective\s+bargaining|memorandum|"
    r"appendix|schedule\s+[a-z])\b",
    re.IGNORECASE,
)
BARGAINING_RE = re.compile(
    r"\b(?:bargaining\s+unit|union|local\s+\d+)\b", re.IGNORECASE
)
PUBLIC_SAFETY_RE = re.compile(
    r"\b(?:police|fire(?:fighter)?s?|sergeant|lieutenant|captain|"
    r"patrol(?:man|men|officer)?s?)\b",
    re.IGNORECASE,
)
NON_SAFETY_RE = re.compile(
    r"\b(?:clerical|public\s+works|sanitation|library|parks?|"
    r"administrative|maintenance|teacher|nurse|transit)\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
DATE_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s+(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
MONEY_RE = re.compile(
    r"(?:\$\s*\d[\d,]*(?:\.\d+)?|\b\d{2,3},\d{3}(?:\.\d+)?\b)"
)
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
WHITESPACE_ALIGN_RE = re.compile(r"\S+\s{2,}\S+")


class FileTimeoutError(TimeoutError):
    """A bounded local parser deadline was exceeded."""


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
    evenly_spaced = [
        round(index * (page_count - 1) / (maximum - 1))
        for index in range(maximum)
    ]
    preferred = [0, 1, page_count // 2, page_count - 2, page_count - 1]
    result: list[int] = []
    for index in [*preferred, *evenly_spaced]:
        bounded = max(0, min(page_count - 1, index))
        if bounded not in result:
            result.append(bounded)
        if len(result) == maximum:
            break
    return sorted(result)


def detected(pattern: re.Pattern[str], text: str) -> str:
    return "detected" if pattern.search(text) else "not_detected"


def redacted_contract_hint(text: str) -> str:
    """Return at most 300 chars without currency/percent/final wage values."""

    normalized = re.sub(r"\s+", " ", text).strip()
    context_matches = list(EFFECTIVE_RE.finditer(normalized))
    if not context_matches:
        context_matches = list(AGREEMENT_RE.finditer(normalized))
    if not context_matches:
        return ""
    match = context_matches[0]
    start = max(0, match.start() - 70)
    end = min(len(normalized), match.end() + 220)
    hint = normalized[start:end]
    hint = MONEY_RE.sub("[currency redacted]", hint)
    hint = PERCENT_RE.sub("[percent redacted]", hint)

    def redact_number(match_obj: re.Match[str]) -> str:
        token = match_obj.group(0)
        plain = token.replace(",", "")
        if plain.isdigit():
            value = int(plain)
            if 1900 <= value <= 2100 or value <= 31:
                return token
        return "[number redacted]"

    hint = NUMBER_RE.sub(redact_number, hint)
    return hint[:MAX_CONTRACT_HINT_CHARS].strip()


def analyze_page(text: str) -> dict[str, object]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    wage_terms = sum(
        bool(pattern.search(text))
        for pattern in (
            WAGE_RE,
            SALARY_RE,
            COMPENSATION_RE,
            PAY_SCHEDULE_RE,
            HOURLY_RE,
            ANNUAL_RE,
            STEP_GRADE_RE,
            RANK_POSITION_RE,
        )
    )
    numeric_tokens = len(NUMBER_RE.findall(text))
    money_tokens = len(MONEY_RE.findall(text))
    percent_tokens = len(PERCENT_RE.findall(text))
    aligned_lines = sum(bool(WHITESPACE_ALIGN_RE.search(line)) for line in lines)
    numeric_rows = sum(
        len(NUMBER_RE.findall(line)) >= 3 for line in lines
    )
    if (
        numeric_rows >= 2
        or (numeric_tokens >= 12 and aligned_lines >= 2)
        or (money_tokens >= 4 and wage_terms >= 2)
    ):
        table_signal = "likely"
    elif (
        numeric_rows >= 1
        or numeric_tokens >= 6
        or aligned_lines >= 1
        or money_tokens >= 1
    ):
        table_signal = "possible"
    else:
        table_signal = "unlikely"

    years = YEAR_RE.findall(text)
    dates = DATE_RE.findall(text)
    agreement_context = bool(AGREEMENT_RE.search(text))
    effective_context = bool(EFFECTIVE_RE.search(text))
    if (agreement_context or effective_context) and (
        len(set(years)) >= 2 or len(dates) >= 2
    ):
        contract_signal, contract_confidence = "likely", "high"
    elif (
        (agreement_context or effective_context)
        and (years or dates)
    ) or (len(set(years)) >= 2):
        contract_signal, contract_confidence = "possible", "medium"
    else:
        contract_signal, contract_confidence = "unlikely", "low"

    return {
        "wage_terms": wage_terms,
        "numeric_tokens": numeric_tokens,
        "money_tokens": money_tokens,
        "percent_tokens": percent_tokens,
        "table_signal": table_signal,
        "contract_signal": contract_signal,
        "contract_confidence": contract_confidence,
        "contract_hint": (
            redacted_contract_hint(text)
            if contract_signal in {"likely", "possible"}
            else ""
        ),
        "pay_schedule": bool(PAY_SCHEDULE_RE.search(text)),
        "salary_schedule": bool(
            SALARY_RE.search(text) and re.search(
                r"\b(?:schedule|scale|table)\b", text, re.IGNORECASE
            )
        ),
        "hourly": bool(HOURLY_RE.search(text)),
        "step_grade": bool(STEP_GRADE_RE.search(text)),
        "rank_position": bool(RANK_POSITION_RE.search(text)),
        "effective": effective_context,
        "bargaining": bool(BARGAINING_RE.search(text)),
        "public_safety": bool(PUBLIC_SAFETY_RE.search(text)),
        "non_safety": bool(NON_SAFETY_RE.search(text)),
    }


def base_result(row: dict[str, str]) -> dict[str, str]:
    result = {field: row.get(field, "") for field in INPUT_FIELDS}
    result.update(
        {
            "detection_status": "",
            "detection_status_detail": "",
            "parser_library": "pypdf",
            "parser_version": importlib.metadata.version("pypdf"),
            "parser_elapsed_seconds": "0.000000",
            "pages_scanned": "0",
            "pages_with_text": "0",
            "total_text_chars_scanned": "0",
            "wage_table_signal": "unknown",
            "wage_table_signal_confidence": "unknown",
            "candidate_wage_pages": "",
            "candidate_wage_page_count": "0",
            "contract_period_signal": "unknown",
            "contract_period_confidence": "unknown",
            "candidate_contract_period_text": "",
            "pay_schedule_signal": "unknown",
            "salary_schedule_signal": "unknown",
            "hourly_rate_signal": "unknown",
            "step_grade_signal": "unknown",
            "rank_position_signal": "unknown",
            "effective_date_signal": "unknown",
            "bargaining_unit_signal": "unknown",
            "public_safety_signal": "unknown",
            "non_safety_signal": "unknown",
            "table_like_structure_signal": "unknown",
            "table_detection_method": TABLE_METHOD,
            "extraction_pilot_priority": "defer",
            "recommended_next_action": "manual_review",
            "detection_notes": "",
            "reviewer": "script_local_text_table_detection",
            "reviewed_at": now_utc(),
        }
    )
    return result


def set_component_signals(
    result: dict[str, str], analyses: list[dict[str, object]]
) -> None:
    mapping = {
        "pay_schedule_signal": "pay_schedule",
        "salary_schedule_signal": "salary_schedule",
        "hourly_rate_signal": "hourly",
        "step_grade_signal": "step_grade",
        "rank_position_signal": "rank_position",
        "effective_date_signal": "effective",
        "bargaining_unit_signal": "bargaining",
        "public_safety_signal": "public_safety",
        "non_safety_signal": "non_safety",
    }
    for output_field, analysis_field in mapping.items():
        result[output_field] = (
            "detected"
            if any(bool(item[analysis_field]) for item in analyses)
            else "not_detected"
        )


def classify_document(
    result: dict[str, str],
    analyses: list[dict[str, object]],
    page_numbers: list[int],
) -> None:
    candidate_pages: list[int] = []
    for page_number, analysis in zip(page_numbers, analyses):
        if int(analysis["wage_terms"]) >= 1 and analysis[
            "table_signal"
        ] in {"likely", "possible"}:
            candidate_pages.append(page_number)

    likely_page = any(
        int(item["wage_terms"]) >= 2
        and item["table_signal"] == "likely"
        for item in analyses
    )
    possible_page = any(
        int(item["wage_terms"]) >= 1
        or item["table_signal"] == "likely"
        for item in analyses
    )
    if likely_page:
        wage_signal, wage_confidence = "likely", "high"
    elif possible_page:
        wage_signal, wage_confidence = "possible", "medium"
    else:
        wage_signal, wage_confidence = "unlikely", "low"

    table_values = [str(item["table_signal"]) for item in analyses]
    if "likely" in table_values:
        table_signal = "likely"
    elif "possible" in table_values:
        table_signal = "possible"
    else:
        table_signal = "unlikely"

    contract_values = [str(item["contract_signal"]) for item in analyses]
    if "likely" in contract_values:
        contract_signal, contract_confidence = "likely", "high"
    elif "possible" in contract_values:
        contract_signal, contract_confidence = "possible", "medium"
    else:
        contract_signal, contract_confidence = "unlikely", "low"

    hints = [
        str(item["contract_hint"])
        for item in analyses
        if item.get("contract_hint")
    ]
    hint = hints[0][:MAX_CONTRACT_HINT_CHARS] if hints else ""
    set_component_signals(result, analyses)

    if wage_signal == "likely":
        priority = "p1"
        next_action = "wage_table_extraction_pilot"
    elif wage_signal == "possible" and table_signal in {
        "likely",
        "possible",
    }:
        priority = "p2"
        next_action = "larger_text_detection_pass"
    elif contract_signal == "likely":
        priority = "p2"
        next_action = "contract_period_extraction_pilot"
    else:
        priority = "p3"
        next_action = "manual_review"

    result.update(
        {
            "wage_table_signal": wage_signal,
            "wage_table_signal_confidence": wage_confidence,
            "candidate_wage_pages": ",".join(map(str, candidate_pages)),
            "candidate_wage_page_count": str(len(candidate_pages)),
            "contract_period_signal": contract_signal,
            "contract_period_confidence": contract_confidence,
            "candidate_contract_period_text": hint,
            "table_like_structure_signal": table_signal,
            "extraction_pilot_priority": priority,
            "recommended_next_action": next_action,
            "detection_notes": (
                "deterministic bounded keyword/numeric-structure signals; "
                f"{len(candidate_pages)} candidate page hints; no wage "
                "values or page text retained"
            ),
        }
    )


def inspect_artifact(
    row: dict[str, str],
    *,
    max_pages_to_scan: int,
    max_text_chars_per_page: int,
    timeout_per_file: float,
    reader_factory: Callable[..., object] = PdfReader,
) -> tuple[dict[str, str], dict[str, int]]:
    result = base_result(row)
    counters = {
        "local_artifact_opened": 0,
        "hash_verified": 0,
        "pdf_opened": 0,
        "pages_scanned": 0,
    }
    started = time.monotonic()

    if row.get("sample_selection_reason") and row.get(
        "text_layer_status"
    ) not in {"present", "partial"}:
        result.update(
            {
                "detection_status": "skipped_not_parse_text_candidate",
                "detection_status_detail": (
                    "row is not an approved present/partial text candidate"
                ),
                "recommended_next_action": "ocr_later",
            }
        )
        result["parser_elapsed_seconds"] = (
            f"{time.monotonic() - started:.6f}"
        )
        return result, counters

    artifact = resolve_artifact(row["content_artifact_path"])
    if not artifact.is_file():
        result.update(
            {
                "detection_status": "artifact_missing",
                "detection_status_detail": "retained artifact path is missing",
                "recommended_next_action": "manual_review",
            }
        )
        result["parser_elapsed_seconds"] = (
            f"{time.monotonic() - started:.6f}"
        )
        return result, counters

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
                "detection_status": "hash_mismatch",
                "detection_status_detail": (
                    "retained artifact hash or byte size does not match "
                    "the locked readiness record"
                ),
                "recommended_next_action": "manual_review",
            }
        )
        result["parser_elapsed_seconds"] = (
            f"{time.monotonic() - started:.6f}"
        )
        return result, counters
    counters["hash_verified"] = 1

    try:
        with file_deadline(timeout_per_file):
            reader = reader_factory(artifact, strict=False)
            pages = getattr(reader, "pages")
            page_count = len(pages)
            if page_count != int(row["pdf_page_count"]):
                raise ValueError(
                    "current page count differs from durable readiness row"
                )
            counters["pdf_opened"] = 1
            indexes = page_sample_indexes(page_count, max_pages_to_scan)
            analyses: list[dict[str, object]] = []
            page_numbers: list[int] = []
            pages_with_text = 0
            chars_scanned = 0
            for page_index in indexes:
                extracted = pages[page_index].extract_text() or ""
                bounded = extracted[:max_text_chars_per_page]
                del extracted
                normalized = bounded.strip()
                if normalized:
                    pages_with_text += 1
                    chars_scanned += len(normalized)
                    analyses.append(analyze_page(bounded))
                    page_numbers.append(page_index + 1)
                del bounded
            counters["pages_scanned"] = len(indexes)
            result.update(
                {
                    "pages_scanned": str(len(indexes)),
                    "pages_with_text": str(pages_with_text),
                    "total_text_chars_scanned": str(chars_scanned),
                }
            )
            if not analyses:
                result.update(
                    {
                        "detection_status": "no_text_available",
                        "detection_status_detail": (
                            "bounded scanned pages produced no text"
                        ),
                        "recommended_next_action": "ocr_later",
                        "detection_notes": (
                            "no text on bounded scanned pages; no OCR run"
                        ),
                    }
                )
            else:
                classify_document(result, analyses, page_numbers)
                result.update(
                    {
                        "detection_status": "detection_checked",
                        "detection_status_detail": (
                            "bounded local text/table detection completed; "
                            "no full text or final wage values retained"
                        ),
                    }
                )
    except Exception as exc:
        result.update(
            {
                "detection_status": "parser_error",
                "detection_status_detail": (
                    "bounded local PDF parser could not complete"
                ),
                "recommended_next_action": "manual_review",
                "detection_notes": (
                    f"{sanitized_exception_type(exc)}: "
                    f"{sanitized_error(exc)}"
                )[:300],
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
        "text_table_detection_id",
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
            or row.get("text_layer_status") not in {"present", "partial"}
        ):
            raise ValueError("input contains a non-parse-text candidate")


def summary_payload(
    *,
    rows: list[dict[str, str]],
    mode: str,
    elapsed: float,
    counters: Counter[str],
    args: argparse.Namespace,
) -> dict[str, object]:
    distribution_fields = (
        "detection_status",
        "wage_table_signal",
        "wage_table_signal_confidence",
        "contract_period_signal",
        "contract_period_confidence",
        "table_like_structure_signal",
        "extraction_pilot_priority",
        "recommended_next_action",
    )
    payload: dict[str, object] = {
        field: dict(
            sorted(Counter(row[field] for row in rows).items())
        )
        for field in distribution_fields
    }
    return {
        "schema_version": "1.0.0",
        "status": (
            "text_table_detection_dry_run_complete"
            if mode == "dry_run"
            else "text_table_detection_local_collection_complete"
        ),
        "mode": mode,
        "input_csv": args.input_csv,
        "output_dir": args.output_dir,
        "rows": len(rows),
        "terminal_rows": (
            sum(row["detection_status"] in TERMINAL_STATUSES for row in rows)
            if mode == "local"
            else sum(row["detection_status"] == DRY_STATUS for row in rows)
        ),
        **payload,
        "pages_scanned": sum(int(row["pages_scanned"]) for row in rows),
        "pages_with_text": sum(
            int(row["pages_with_text"]) for row in rows
        ),
        "total_text_chars_scanned": sum(
            int(row["total_text_chars_scanned"]) for row in rows
        ),
        "candidate_wage_page_hints": sum(
            int(row["candidate_wage_page_count"]) for row in rows
        ),
        "maximum_contract_hint_characters": max(
            (
                len(row["candidate_contract_period_text"])
                for row in rows
            ),
            default=0,
        ),
        "parser_library": "pypdf",
        "parser_version": importlib.metadata.version("pypdf"),
        "elapsed_seconds": round(elapsed, 6),
        "local_artifacts_opened": counters["local_artifact_opened"],
        "artifact_hashes_verified": counters["hash_verified"],
        "pdfs_opened_for_detection": counters["pdf_opened"],
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "redownloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "final_wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_text_table_merges": 0,
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
    if args.max_pages_to_scan <= 0 or args.max_text_chars_per_page <= 0:
        raise ValueError("page and text limits must be positive")
    if args.max_text_chars_per_page > 1500:
        raise ValueError("max text characters per page cannot exceed 1500")
    if args.max_pages_to_scan > 10:
        raise ValueError("max pages to scan cannot exceed 10")
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
                    "detection_status": DRY_STATUS,
                    "detection_status_detail": (
                        "dry-run schema validation only; PDF not opened"
                    ),
                    "parser_library": "not_invoked",
                    "parser_version": "",
                    "reviewer": "script_text_table_detection_dry_run",
                }
            )
            row_counters = {
                "local_artifact_opened": 0,
                "hash_verified": 0,
                "pdf_opened": 0,
                "pages_scanned": 0,
            }
        else:
            result, row_counters = inspector(
                row,
                max_pages_to_scan=args.max_pages_to_scan,
                max_text_chars_per_page=args.max_text_chars_per_page,
                timeout_per_file=args.timeout_per_file,
            )
        if len(result["candidate_contract_period_text"]) > 300:
            raise AssertionError("contract-period hint exceeds 300 chars")
        counters.update(row_counters)
        output_rows.append(result)
        timing_rows.append(
            {
                "row_number": str(index),
                "text_table_detection_id": row[
                    "text_table_detection_id"
                ],
                "pdf_readiness_id": row["pdf_readiness_id"],
                "source_review_id": row["source_review_id"],
                "status": result["detection_status"],
                "started_at": row_started,
                "completed_at": now_utc(),
                "elapsed_seconds": (
                    f"{time.monotonic() - row_clock:.6f}"
                ),
                "local_artifact_opened": str(
                    row_counters["local_artifact_opened"]
                ),
                "hash_verified": str(row_counters["hash_verified"]),
                "pdf_opened": str(row_counters["pdf_opened"]),
                "pages_scanned": str(row_counters["pages_scanned"]),
                "ocr_run": "0",
            }
        )
        write_csv(
            output_dir / "text_table_detection_ledger.csv",
            output_rows,
            LEDGER_FIELDS,
        )
        write_csv(
            output_dir / "text_table_detection_timing.csv",
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
    write_json(
        output_dir / "text_table_detection_summary.json", summary
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--max-pages-to-scan", type=int, default=10)
    parser.add_argument(
        "--max-text-chars-per-page", type=int, default=1500
    )
    parser.add_argument("--timeout-per-file", type=float, default=30.0)
    parser.add_argument(
        "--no-save-text",
        dest="no_save_text",
        action="store_true",
        default=True,
        help="Mandatory: no page or document text is written.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run(args)
    print(
        "Text/table detection "
        f"{summary['mode']}: {summary['terminal_rows']}/"
        f"{summary['rows']} terminal; URLs=0 OCR=0 wage values=0."
    )


if __name__ == "__main__":
    main()
