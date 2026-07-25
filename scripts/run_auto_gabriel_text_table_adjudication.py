#!/usr/bin/env python3
"""Run a bounded local-layout + GABRIEL text/table adjudication gate.

The runner reads only the blinded 150-case packet, opens only bounded local PDF
pages and their existing renders, sends capped/redacted page evidence only
after an explicit live gate, and never saves page text, complete tables, or
wage values.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
DEFAULT_BACKEND = "huit_openai_responses_direct_sdk"
DEFAULT_MODEL = "gpt-5.4-nano"
GATE1_MODE = "auto_gabriel_gate1"
GATE2_MODE = "auto_gabriel_gate2_navigation_table_refine"
GATE_MODES = {GATE1_MODE, GATE2_MODE}
ORIGINAL_CALIBRATION_PATH = (
    ROOT
    / "docs/analysis/text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
    / "calibration_review_input.csv"
)

IDENTITY_FIELDS = [
    "auto_adjudication_id",
    "adjudication_case_id",
    "calibration_id",
    "source_review_id",
    "pdf_readiness_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "pdf_page_count",
    "content_artifact_path",
    "candidate_pages_evaluated",
    "nearby_pages_evaluated",
    "navigation_pages_evaluated",
]
LOCAL_FIELDS = [
    "local_text_signal_summary",
    "local_layout_signal_summary",
    "rendered_page_available",
    "rendered_page_count_used",
    "table_structure_feature_score",
    "wage_language_feature_score",
    "pay_numeric_feature_score",
    "navigation_feature_score",
    "non_wage_false_positive_feature_score",
    "compact_compensation_sheet_feature_score",
]
GABRIEL_FIELDS = [
    "gabriel_request_id",
    "gabriel_backend",
    "gabriel_model",
    "gabriel_status",
    "gabriel_schema_valid",
    "gabriel_wage_schedule_present",
    "gabriel_candidate_page_relationship",
    "gabriel_visual_table_type",
    "gabriel_non_wage_family",
    "gabriel_navigation_needed",
    "gabriel_navigation_target_found",
    "gabriel_extraction_complexity",
    "gabriel_extraction_recommendation",
    "gabriel_confidence",
    "gabriel_reason_codes",
    "gabriel_short_rationale",
    "gabriel_input_page_count",
    "gabriel_input_text_chars",
    "gabriel_elapsed_seconds",
]
FINAL_FIELDS = [
    "auto_gate_label",
    "auto_gate_confidence",
    "auto_gate_reason_codes",
    "auto_gate_rationale",
    "auto_gate_passes_500_doc_criteria_candidate",
]
LEDGER_FIELDS = IDENTITY_FIELDS + LOCAL_FIELDS + GABRIEL_FIELDS + FINAL_FIELDS
GATE2_FIELDS = [
    "gate_mode",
    "gate2_diagnostic_reason_codes",
    "gate2_candidate_discovery_summary",
    "gate2_printed_page_offsets",
]
GATE2_LEDGER_FIELDS = (
    IDENTITY_FIELDS
    + LOCAL_FIELDS
    + GATE2_FIELDS
    + GABRIEL_FIELDS
    + FINAL_FIELDS
)

GABRIEL_RESPONSE_KEYS = {
    "wage_schedule_present",
    "candidate_page_relationship",
    "visual_table_type",
    "non_wage_family",
    "navigation_needed",
    "navigation_target_found",
    "extraction_complexity",
    "extraction_recommendation",
    "confidence",
    "reason_codes",
    "short_rationale",
}
ALLOWED = {
    "wage_schedule_present": {"yes", "maybe", "no", "unknown"},
    "candidate_page_relationship": {
        "exact_table_page",
        "adjacent_to_table",
        "points_to_later_table",
        "wrong_page",
        "no_candidate_page",
        "unknown",
    },
    "visual_table_type": {
        "step_grade",
        "rank_step",
        "classification_pay_table",
        "hourly_schedule",
        "annual_salary_schedule",
        "compact_compensation_sheet",
        "percent_increase_only",
        "prose_only",
        "benefits_table",
        "budget_or_fiscal_table",
        "classification_without_pay",
        "index_or_contents",
        "front_matter",
        "non_wage_table",
        "no_table",
        "other",
        "unknown",
    },
    "non_wage_family": {
        "not_applicable",
        "benefits",
        "budget_or_fiscal",
        "classification_without_pay",
        "incentive_or_bonus_prose",
        "index_or_contents",
        "front_matter",
        "non_wage_appendix",
        "memorandum_without_table",
        "other",
        "unknown",
    },
    "navigation_needed": {"yes", "no", "unknown"},
    "navigation_target_found": {"yes", "no", "not_applicable", "unknown"},
    "extraction_complexity": {
        "easy",
        "moderate",
        "hard",
        "not_extractable",
        "unknown",
    },
    "extraction_recommendation": {
        "extraction_ready",
        "extraction_ready_with_schema_update",
        "second_review_required",
        "exclude_for_now",
        "unknown",
    },
    "confidence": {"high", "medium", "low", "unknown"},
}
AUTO_GATE_LABELS = {
    "extraction_ready_high_confidence",
    "extraction_ready_with_schema_update",
    "second_review_required",
    "exclude_for_now",
    "gabriel_unavailable",
    "error",
}

GABRIEL_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(GABRIEL_RESPONSE_KEYS),
    "properties": {
        **{
            field: {"type": "string", "enum": sorted(values)}
            for field, values in ALLOWED.items()
        },
        "reason_codes": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": {
                "type": "string",
                "pattern": "^[A-Z][A-Z0-9_]{0,39}$",
            },
        },
        "short_rationale": {
            "type": "string",
            "minLength": 1,
            "maxLength": 300,
        },
    },
}

WAGE_RE = re.compile(
    r"\b(?:wage|wages|salary|salaries|pay\s*(?:rate|schedule|plan)?|"
    r"compensation|hourly|annual|step|grade|range)\b",
    re.IGNORECASE,
)
ROLE_RE = re.compile(
    r"\b(?:classification|class|position|rank|officer|firefighter|"
    r"lieutenant|captain|sergeant|employee|title)\b",
    re.IGNORECASE,
)
TABLE_HEADER_RE = re.compile(
    r"\b(?:step|grade|range|rank|classification|position|hourly|"
    r"annual|salary|wage|rate|effective)\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(
    r"(?<!\w)(?:\$\s*)?(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d{1,4})?%?(?!\w)"
)
MONEY_RE = re.compile(
    r"(?:\$\s*\d[\d,]*(?:\.\d{1,4})?|"
    r"\b\d{1,3}(?:,\d{3})+(?:\.\d{1,4})?\b)"
)
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
BENEFIT_RE = re.compile(
    r"\b(?:health|dental|insurance|pension|retirement|deductible|"
    r"premium|medical|vision|leave|vacation|sick)\b",
    re.IGNORECASE,
)
BUDGET_RE = re.compile(
    r"\b(?:budget|fiscal|fund|appropriation|expenditure|revenue|"
    r"department total|payroll total|general fund)\b",
    re.IGNORECASE,
)
CLASSIFICATION_RE = re.compile(
    r"\b(?:classification|class title|position title|job title)\b",
    re.IGNORECASE,
)
INDEX_RE = re.compile(
    r"\b(?:table of contents|contents|index)\b", re.IGNORECASE
)
FRONT_RE = re.compile(
    r"\b(?:memorandum|transmittal|recommendation|agreement between|"
    r"execution copy|signature page|whereas)\b",
    re.IGNORECASE,
)
NAV_TARGET_RE = re.compile(
    r"\b(?:salary|wage|pay|compensation)\s+"
    r"(?:table|schedule|plan|appendix)|"
    r"\b(?:table|schedule|appendix)\s+[a-z]?\s*"
    r"(?:salary|wage|pay|compensation)\b",
    re.IGNORECASE,
)
PAGE_AT_END_RE = re.compile(r"\b(\d{1,4})\s*$")
SECRET_ERROR_RE = re.compile(
    r"(?i)(authorization|bearer|api[_-]?key|subscription[_-]?key|"
    r"cookie|password|token|https?://)"
)
REASON_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,39}$")
GATE2_DIAGNOSTIC_CODES = {
    "no_candidate_detected",
    "candidate_is_prose_only",
    "candidate_is_index_or_contents",
    "target_table_outside_budget",
    "possible_printed_page_offset",
    "compact_compensation_candidate",
    "non_wage_numeric_table",
    "benefits_table",
    "budget_table",
    "classification_without_pay",
    "true_wage_table_evidence",
    "insufficient_role_pay_columns",
}

NEGATIVE_TABLE_TYPES = {
    "percent_increase_only",
    "prose_only",
    "benefits_table",
    "budget_or_fiscal_table",
    "classification_without_pay",
    "index_or_contents",
    "front_matter",
    "non_wage_table",
    "no_table",
}
POSITIVE_TABLE_TYPES = {
    "step_grade",
    "rank_step",
    "classification_pay_table",
    "hourly_schedule",
    "annual_salary_schedule",
    "compact_compensation_sheet",
}
NEGATIVE_FAMILIES = {
    "benefits",
    "budget_or_fiscal",
    "classification_without_pay",
    "incentive_or_bonus_prose",
    "index_or_contents",
    "front_matter",
    "non_wage_appendix",
    "memorandum_without_table",
}


@dataclass
class PageEvidence:
    page_number: int
    role: str
    snippet: str
    snippet_chars: int
    wage_terms: int
    role_terms: int
    numeric_tokens: int
    money_tokens: int
    percent_tokens: int
    row_like_lines: int
    column_lines: int
    header_lines: int
    geometry_rows: int
    geometry_columns: int
    benefit_terms: int
    budget_terms: int
    classification_terms: int
    index_signal: bool
    front_signal: bool
    rendered_available: bool
    image_horizontal_bands: int
    image_vertical_bands: int
    image_dark_density: float
    navigation_targets: list[int]
    printed_page_number: int | None = None
    printed_page_offset: int | None = None
    role_pay_rows: int = 0
    aligned_numeric_columns: int = 0
    compact_role_pay_lines: int = 0


@dataclass
class CaseEvidence:
    source: dict[str, str]
    auto_id: str
    pages: list[PageEvidence]
    candidate_pages: list[int]
    nearby_pages: list[int]
    navigation_pages: list[int]
    text_chars: int
    table_score: float
    wage_score: float
    numeric_score: float
    navigation_score: float
    non_wage_score: float
    compact_score: float
    navigation_targets_found: list[int]
    prompt: str
    gate_mode: str = GATE1_MODE
    diagnostic_reason_codes: list[str] | None = None
    printed_page_offsets: list[int] | None = None
    unresolved_navigation_targets: list[int] | None = None


@dataclass
class LiveResult:
    request_id: str
    status: str
    response_text: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error_type: str
    error_message: str


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def bounded(value: str, maximum: int) -> str:
    return re.sub(r"\s+", " ", value).strip()[:maximum]


def safe_error(exc: BaseException, secret: str | None = None) -> str:
    message = str(exc)
    if secret:
        message = message.replace(secret, "[REDACTED]")
    if SECRET_ERROR_RE.search(message):
        return "sensitive_error_details_redacted"
    message = re.sub(r"[/\\][^\s]+", "[path]", message)
    return bounded(message or type(exc).__name__, 240)


def parse_pages(raw: str, page_count: int) -> list[int]:
    pages: list[int] = []
    for token in (raw or "").split(","):
        token = token.strip()
        if not token:
            continue
        page = int(token)
        if not 1 <= page <= page_count:
            raise ValueError(f"page {page} is outside 1..{page_count}")
        if page not in pages:
            pages.append(page)
    return sorted(pages)


def format_pages(pages: Iterable[int]) -> str:
    return ",".join(str(value) for value in sorted(set(pages)))


def evenly_sample(values: list[int], count: int) -> list[int]:
    if count <= 0 or not values:
        return []
    if len(values) <= count:
        return list(values)
    if count == 1:
        return [values[0]]
    indexes = {
        round(position * (len(values) - 1) / (count - 1))
        for position in range(count)
    }
    return [values[index] for index in sorted(indexes)]


def auto_id(gate_id: str, calibration_id: str) -> str:
    digest = hashlib.sha256(
        f"{gate_id}|{calibration_id}".encode("utf-8")
    ).hexdigest()[:20]
    return f"auto_adj_{digest}"


def validate_blinded_input(
    fields: list[str], rows: list[dict[str, str]]
) -> None:
    required = {
        "adjudication_case_id",
        "calibration_id",
        "source_review_id",
        "pdf_readiness_id",
        "candidate_queue_row_id",
        "state",
        "municipality",
        "government_name",
        "unit_type",
        "candidate_source_type",
        "pdf_page_count",
        "blinded_candidate_pages",
        "blinded_nearby_pages",
        "blinded_navigation_pages",
        "content_artifact_path",
    }
    missing = required - set(fields)
    if missing:
        raise ValueError(f"blinded input missing fields: {sorted(missing)}")
    forbidden = {
        "wage_table_signal",
        "extraction_gate_label",
        "wage_schedule_table_confirmed_label",
        "candidate_page_relationship_label",
        "recommended_extraction_action",
        "recommended_next_action",
        "review_id",
        "review_method",
    }
    if forbidden & set(fields):
        raise ValueError("blinded input contains prior labels/actions")
    if not rows or len(rows) > 150:
        raise ValueError("blinded input must contain 1..150 rows")
    for identity in (
        "adjudication_case_id",
        "calibration_id",
        "source_review_id",
        "pdf_readiness_id",
        "candidate_queue_row_id",
    ):
        values = [row[identity] for row in rows]
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError(f"invalid identity field: {identity}")


def resolve_local_path(raw: str) -> Path:
    if "://" in raw:
        raise ValueError("URL-like artifact path is prohibited")
    path = Path(raw)
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    return resolved


def validate_render_manifest(
    path: Path, blinded_rows: list[dict[str, str]]
) -> dict[str, dict[int, dict[str, str]]]:
    fields, rows = read_csv(path)
    required = {
        "adjudication_case_id",
        "calibration_id",
        "page_number",
        "page_role",
        "rendered_image_path",
        "render_status",
        "rendered_bytes",
        "rendered_sha256",
    }
    if required - set(fields):
        raise ValueError("render manifest missing required fields")
    allowed_cases = {row["adjudication_case_id"] for row in blinded_rows}
    packet_dir = path.parent
    result: dict[str, dict[int, dict[str, str]]] = defaultdict(dict)
    per_case = Counter()
    for row in rows:
        case = row["adjudication_case_id"]
        if case not in allowed_cases:
            raise ValueError("render manifest contains an unknown case")
        page = int(row["page_number"])
        if row["render_status"] != "rendered":
            raise ValueError("render manifest contains a non-rendered row")
        image = packet_dir / row["rendered_image_path"]
        if not image.is_file():
            raise FileNotFoundError(f"missing rendered image: {image}")
        if image.stat().st_size != int(row["rendered_bytes"]):
            raise ValueError("rendered image size mismatch")
        if sha256_file(image) != row["rendered_sha256"]:
            raise ValueError("rendered image hash mismatch")
        if page in result[case]:
            raise ValueError("duplicate rendered case/page")
        result[case][page] = {**row, "_resolved_image": str(image)}
        per_case[case] += 1
    if per_case and max(per_case.values()) > 6:
        raise ValueError("render manifest exceeds six pages per case")
    return result


def redact_numbers(text: str) -> str:
    text = re.sub(r"\$\s*\d[\d,]*(?:\.\d+)?", "[MONEY]", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\s*%", "[PCT]", text)
    text = re.sub(r"\b(?:19|20)\d{2}\b", "[YEAR]", text)
    text = re.sub(r"\b\d[\d,]*(?:\.\d+)?\b", "[NUM]", text)
    return text


def select_snippet(text: str, maximum: int, navigation: bool) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    chosen: set[int] = set()
    if navigation:
        chosen.update(range(min(len(lines), 25)))
    for index, line in enumerate(lines):
        numeric_count = len(NUMBER_RE.findall(line))
        if (
            WAGE_RE.search(line)
            or BENEFIT_RE.search(line)
            or BUDGET_RE.search(line)
            or INDEX_RE.search(line)
            or numeric_count >= 2
        ):
            chosen.update(
                candidate
                for candidate in (index - 1, index, index + 1)
                if 0 <= candidate < len(lines)
            )
    if not chosen:
        chosen.update(range(min(len(lines), 15)))
    output: list[str] = []
    used = 0
    for index in sorted(chosen):
        redacted = redact_numbers(lines[index])
        remaining = maximum - used
        if remaining <= 0:
            break
        value = redacted[:remaining]
        output.append(value)
        used += len(value) + 1
    return "\n".join(output)[:maximum]


def image_features(image_path: Path) -> tuple[int, int, float]:
    with Image.open(image_path) as image:
        grayscale = image.convert("L")
        width = 160
        height = max(40, round(grayscale.height * width / grayscale.width))
        sample = grayscale.resize((width, height))
        pixel_source = (
            sample.get_flattened_data()
            if hasattr(sample, "get_flattened_data")
            else sample.getdata()
        )
        pixels = list(pixel_source)
    dark = [1 if value < 185 else 0 for value in pixels]
    dark_density = sum(dark) / max(1, len(dark))
    horizontal = 0
    for y in range(height):
        density = sum(dark[y * width : (y + 1) * width]) / width
        if density >= 0.34:
            horizontal += 1
    vertical = 0
    for x in range(width):
        density = sum(dark[y * width + x] for y in range(height)) / height
        if density >= 0.28:
            vertical += 1
    return min(horizontal, 20), min(vertical, 20), round(dark_density, 6)


def text_geometry(page: Any) -> tuple[int, int]:
    fragments: list[tuple[float, float, str]] = []

    def visitor(
        text: str,
        _cm: list[float],
        tm: list[float],
        _font: dict[str, Any] | None,
        _size: float,
    ) -> None:
        if text.strip():
            fragments.append((float(tm[4]), float(tm[5]), text.strip()))

    try:
        page.extract_text(visitor_text=visitor)
    except Exception:
        return 0, 0
    rows: dict[int, set[int]] = defaultdict(set)
    columns: Counter[int] = Counter()
    for x, y, value in fragments:
        if len(value) > 80:
            continue
        x_bucket = round(x / 35)
        y_bucket = round(y / 7)
        rows[y_bucket].add(x_bucket)
        columns[x_bucket] += 1
    geometry_rows = sum(1 for values in rows.values() if len(values) >= 3)
    geometry_columns = sum(1 for count in columns.values() if count >= 4)
    return min(geometry_rows, 30), min(geometry_columns, 20)


def find_navigation_targets(text: str, page_count: int) -> list[int]:
    targets: list[int] = []
    for line in text.splitlines():
        compact = re.sub(r"\s+", " ", line).strip()[:300]
        if not NAV_TARGET_RE.search(compact):
            continue
        match = PAGE_AT_END_RE.search(compact)
        if match:
            page = int(match.group(1))
            if 1 <= page <= page_count and page not in targets:
                targets.append(page)
    return targets


def find_gate2_navigation_targets(text: str, page_count: int) -> list[int]:
    """Return printed target page numbers from bounded navigation text."""

    targets = find_navigation_targets(text, page_count)
    for line in text.splitlines():
        compact = re.sub(r"\s+", " ", line).strip()[:300]
        if not compact:
            continue
        has_wage_target = bool(
            re.search(
                r"\b(?:salary|salaries|wage|wages|pay|compensation|"
                r"rate\s+of\s+pay)\b",
                compact,
                re.IGNORECASE,
            )
        )
        has_target_form = bool(
            re.search(
                r"\b(?:schedule|table|plan|appendix|exhibit|attachment|"
                r"pay\s+scale)\b",
                compact,
                re.IGNORECASE,
            )
        )
        if not (has_wage_target and has_target_form):
            continue
        matches = re.findall(r"(?:\.{2,}|\s)(\d{1,4})\s*$", compact)
        if not matches:
            matches = re.findall(r"\bpage\s+(\d{1,4})\b", compact, re.I)
        for value in matches[-1:]:
            page = int(value)
            if 1 <= page <= page_count and page not in targets:
                targets.append(page)
    return targets


def detect_printed_page_number(
    text: str, *, pdf_page_number: int, page_count: int
) -> tuple[int | None, int | None]:
    """Infer one printed page number from an already selected page only."""

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    boundary = lines[:8] + lines[-12:]
    candidates: list[int] = []
    for line in boundary:
        matches = re.findall(r"\bpage\s+([ivxlcdm]+|\d{1,4})\b", line, re.I)
        matches += re.findall(r"^[-–—]?\s*(\d{1,4})\s*[-–—]?$", line)
        for value in matches:
            if not str(value).isdigit():
                continue
            printed = int(value)
            if 1 <= printed <= page_count:
                candidates.append(printed)
    if not candidates:
        return None, None
    printed = min(candidates, key=lambda value: abs(pdf_page_number - value))
    offset = pdf_page_number - printed
    if abs(offset) > 30:
        return None, None
    return printed, offset


def gate2_line_structure(lines: list[str]) -> tuple[int, int, int]:
    """Count direct role/pay rows, stable numeric columns, and compact rows."""

    role_pay_rows = 0
    compact_rows = 0
    numeric_positions: Counter[int] = Counter()
    for line in lines:
        numeric_matches = list(NUMBER_RE.finditer(line))
        words = re.findall(r"[A-Za-z][A-Za-z/-]*", line)
        has_role = bool(ROLE_RE.search(line))
        has_pay_term = bool(WAGE_RE.search(line) or TABLE_HEADER_RE.search(line))
        sentence_like = line.rstrip().endswith((".", ";")) and len(words) > 12
        if numeric_matches and has_role and not sentence_like:
            role_pay_rows += 1
        if (
            numeric_matches
            and (has_role or has_pay_term)
            and len(words) <= 12
            and len(line) <= 180
            and not sentence_like
        ):
            compact_rows += 1
        if len(numeric_matches) >= 1 and len(words) >= 1 and not sentence_like:
            for match in numeric_matches[-4:]:
                numeric_positions[round(match.start() / 8)] += 1
    aligned_columns = sum(1 for count in numeric_positions.values() if count >= 3)
    return min(role_pay_rows, 40), min(aligned_columns, 12), min(compact_rows, 40)


def page_evidence(
    *,
    page: Any,
    page_number: int,
    role: str,
    page_count: int,
    rendered: dict[str, str] | None,
    max_chars: int,
    gate_mode: str = GATE1_MODE,
) -> PageEvidence:
    try:
        text = page.extract_text(extraction_mode="layout") or ""
    except Exception:
        # Some valid PDFs expose zero-width font metrics that make pypdf's
        # layout mode divide by zero. Standard text-layer extraction remains
        # bounded and local; if that also fails, rendered/layout-only evidence
        # is still usable and the gate remains conservative.
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
    lines = [re.sub(r"\s+$", "", line) for line in text.splitlines() if line.strip()]
    wage_terms = len(WAGE_RE.findall(text))
    role_terms = len(ROLE_RE.findall(text))
    numeric_tokens = len(NUMBER_RE.findall(text))
    money_tokens = len(MONEY_RE.findall(text))
    percent_tokens = len(PERCENT_RE.findall(text))
    benefit_terms = len(BENEFIT_RE.findall(text))
    budget_terms = len(BUDGET_RE.findall(text))
    classification_terms = len(CLASSIFICATION_RE.findall(text))
    row_like = 0
    column_lines = 0
    header_lines = 0
    for line in lines:
        numeric = NUMBER_RE.findall(line)
        words = re.findall(r"[A-Za-z][A-Za-z/-]*", line)
        columns = [value for value in re.split(r"\s{2,}|\t+", line.strip()) if value]
        if TABLE_HEADER_RE.search(line):
            header_lines += 1
        if (
            len(line) <= 240
            and len(words) <= 24
            and len(numeric) >= 2
            and not line.rstrip().endswith((".", ";"))
        ):
            row_like += 1
        if len(columns) >= 3 and len(words) >= 1 and len(numeric) >= 1:
            column_lines += 1
    role_pay_rows, aligned_numeric_columns, compact_role_pay_lines = (
        gate2_line_structure(lines)
    )
    printed_page_number, printed_page_offset = detect_printed_page_number(
        text, pdf_page_number=page_number, page_count=page_count
    )
    geometry_rows, geometry_columns = text_geometry(page)
    horizontal = 0
    vertical = 0
    dark_density = 0.0
    rendered_available = False
    if rendered is not None:
        image_path = Path(rendered["_resolved_image"])
        horizontal, vertical, dark_density = image_features(image_path)
        rendered_available = True
    navigation = bool(INDEX_RE.search(text) or role == "navigation")
    snippet = select_snippet(text, max_chars, navigation)
    return PageEvidence(
        page_number=page_number,
        role=role,
        snippet=snippet,
        snippet_chars=len(snippet),
        wage_terms=wage_terms,
        role_terms=role_terms,
        numeric_tokens=numeric_tokens,
        money_tokens=money_tokens,
        percent_tokens=percent_tokens,
        row_like_lines=row_like,
        column_lines=column_lines,
        header_lines=header_lines,
        geometry_rows=geometry_rows,
        geometry_columns=geometry_columns,
        benefit_terms=benefit_terms,
        budget_terms=budget_terms,
        classification_terms=classification_terms,
        index_signal=bool(INDEX_RE.search(text)),
        front_signal=bool(FRONT_RE.search("\n".join(lines[:15]))),
        rendered_available=rendered_available,
        image_horizontal_bands=horizontal,
        image_vertical_bands=vertical,
        image_dark_density=dark_density,
        navigation_targets=(
            find_gate2_navigation_targets(text, page_count)
            if gate_mode == GATE2_MODE
            else find_navigation_targets(text, page_count)
        ),
        printed_page_number=printed_page_number,
        printed_page_offset=printed_page_offset,
        role_pay_rows=role_pay_rows,
        aligned_numeric_columns=aligned_numeric_columns,
        compact_role_pay_lines=compact_role_pay_lines,
    )


def choose_initial_pages(
    source: dict[str, str],
    *,
    max_pages: int,
    navigation_budget: int,
) -> list[tuple[int, str]]:
    page_count = int(source["pdf_page_count"])
    candidates = parse_pages(source["blinded_candidate_pages"], page_count)
    nearby = parse_pages(source["blinded_nearby_pages"], page_count)
    navigation = parse_pages(source["blinded_navigation_pages"], page_count)[
        :navigation_budget
    ]
    selected: list[tuple[int, str]] = []
    used: set[int] = set()
    reserve = 1 if navigation else 0
    base_cap = max(1, max_pages - reserve)

    def add(values: Iterable[int], role: str, limit: int | None = None) -> None:
        added = 0
        for page in values:
            if len(selected) >= base_cap:
                return
            if page in used:
                continue
            selected.append((page, role))
            used.add(page)
            added += 1
            if limit is not None and added >= limit:
                return

    add(evenly_sample(candidates, min(3, base_cap)), "candidate")
    nearby_limit = min(2, max(0, base_cap - len(selected)))
    add(evenly_sample(nearby, nearby_limit), "nearby")
    add(navigation, "navigation")
    if not selected:
        add(range(1, min(page_count, base_cap) + 1), "navigation")
    return selected


def choose_gate2_initial_pages(
    source: dict[str, str],
    *,
    max_pages: int,
    navigation_budget: int,
    candidate_window: int,
) -> list[tuple[int, str]]:
    """Select a bounded candidate/nearby/navigation seed with target reserve."""

    page_count = int(source["pdf_page_count"])
    candidates = parse_pages(source["blinded_candidate_pages"], page_count)
    supplied_nearby = parse_pages(source["blinded_nearby_pages"], page_count)
    navigation = parse_pages(source["blinded_navigation_pages"], page_count)[
        :navigation_budget
    ]
    generated_nearby: list[int] = []
    for candidate in candidates:
        for delta in range(1, candidate_window + 1):
            for page in (candidate - delta, candidate + delta):
                if 1 <= page <= page_count and page not in generated_nearby:
                    generated_nearby.append(page)
    nearby = generated_nearby + [
        page for page in supplied_nearby if page not in generated_nearby
    ]
    # Reserve one page for an included navigation target whenever a pointer
    # page is available. This fixes Gate 1's tendency to spend the full budget
    # before resolving a target.
    initial_cap = max_pages - (1 if navigation and max_pages > 1 else 0)
    selected: list[tuple[int, str]] = []
    used: set[int] = set()
    navigation_used = 0

    def add(
        values: Iterable[int], role: str, limit: int | None = None
    ) -> None:
        nonlocal navigation_used
        added = 0
        for page in values:
            if len(selected) >= initial_cap:
                return
            if page in used:
                continue
            if role == "navigation" and navigation_used >= navigation_budget:
                return
            selected.append((page, role))
            used.add(page)
            added += 1
            if role == "navigation":
                navigation_used += 1
            if limit is not None and added >= limit:
                return

    if candidates:
        candidate_limit = min(3, initial_cap)
        add(evenly_sample(candidates, candidate_limit), "candidate")
        nearby_limit = min(3, max(0, initial_cap - len(selected)))
        add(nearby, "nearby", nearby_limit)
        if navigation and len(selected) < initial_cap:
            add(navigation, "navigation", 1)
    else:
        add(nearby, "nearby", min(2, initial_cap))
        add(navigation, "navigation", min(navigation_budget, initial_cap))
    if not selected:
        add(range(1, min(page_count, initial_cap) + 1), "navigation")
    if navigation and not any(role == "navigation" for _, role in selected):
        # Replace the last nearby page, never a candidate page, when possible.
        replacement_index = next(
            (
                index
                for index in range(len(selected) - 1, -1, -1)
                if selected[index][1] == "nearby"
            ),
            None,
        )
        if replacement_index is not None and navigation[0] not in used:
            used.remove(selected[replacement_index][0])
            selected[replacement_index] = (navigation[0], "navigation")
            used.add(navigation[0])
    return selected


def score_case(pages: list[PageEvidence]) -> tuple[float, float, float, float, float]:
    page_table_scores = []
    wage_terms = sum(page.wage_terms for page in pages)
    numeric_tokens = sum(page.numeric_tokens for page in pages)
    money_tokens = sum(page.money_tokens for page in pages)
    role_terms = sum(page.role_terms for page in pages)
    benefit_terms = sum(page.benefit_terms for page in pages)
    budget_terms = sum(page.budget_terms for page in pages)
    for page in pages:
        score = (
            0.22 * min(1.0, page.row_like_lines / 4)
            + 0.18 * min(1.0, page.column_lines / 4)
            + 0.20 * min(1.0, page.geometry_rows / 6)
            + 0.14 * min(1.0, page.geometry_columns / 4)
            + 0.12 * min(1.0, page.header_lines / 3)
            + 0.07 * min(1.0, page.image_horizontal_bands / 5)
            + 0.07 * min(1.0, page.image_vertical_bands / 4)
        )
        if page.index_signal or page.front_signal:
            score *= 0.55
        page_table_scores.append(score)
    table_score = min(1.0, max(page_table_scores, default=0.0))
    wage_score = min(1.0, 0.12 * wage_terms + 0.04 * role_terms)
    numeric_score = min(1.0, 0.07 * numeric_tokens + 0.05 * money_tokens)
    negative_raw = (
        0.12 * benefit_terms
        + 0.12 * budget_terms
        + 0.25 * sum(page.index_signal for page in pages)
        + 0.18 * sum(page.front_signal for page in pages)
    )
    non_wage_score = min(1.0, negative_raw)
    compact_candidates = [
        page
        for page in pages
        if page.wage_terms >= 1
        and page.role_terms >= 1
        and page.numeric_tokens >= 2
        and page.row_like_lines >= 1
        and page.column_lines <= 2
        and not page.index_signal
    ]
    compact_score = min(
        1.0,
        0.25 * len(compact_candidates)
        + 0.25 * min(1.0, wage_score)
        + 0.25 * min(1.0, numeric_score)
        + 0.25 * min(1.0, role_terms / 4),
    )
    return tuple(
        round(value, 6)
        for value in (
            table_score,
            wage_score,
            numeric_score,
            non_wage_score,
            compact_score,
        )
    )


def score_case_gate2(
    pages: list[PageEvidence],
) -> tuple[float, float, float, float, float]:
    """Refine Gate 1 scores with direct row/column and compact evidence."""

    base_table, wage_score, numeric_score, non_wage_score, _ = score_case(pages)
    page_scores: list[float] = []
    compact_page_scores: list[float] = []
    for page in pages:
        direct = (
            0.34 * min(1.0, page.role_pay_rows / 4)
            + 0.24 * min(1.0, page.aligned_numeric_columns / 3)
            + 0.16 * min(1.0, page.row_like_lines / 4)
            + 0.12 * min(1.0, page.column_lines / 3)
            + 0.08 * min(1.0, page.header_lines / 2)
            + 0.06
            * min(
                1.0,
                (page.image_horizontal_bands + page.image_vertical_bands) / 8,
            )
        )
        if page.index_signal or page.front_signal:
            direct *= 0.45
        page_scores.append(direct)
        compact = (
            0.40 * min(1.0, page.compact_role_pay_lines / 3)
            + 0.25 * min(1.0, page.role_pay_rows / 3)
            + 0.15 * min(1.0, page.aligned_numeric_columns / 2)
            + 0.10 * min(1.0, page.wage_terms / 2)
            + 0.10 * min(1.0, page.numeric_tokens / 4)
        )
        if page.index_signal or page.front_signal or page.benefit_terms >= 4:
            compact *= 0.35
        compact_page_scores.append(compact)
    refined_table = max(base_table * 0.72, max(page_scores, default=0.0))
    compact_score = max(compact_page_scores, default=0.0)
    return tuple(
        round(min(1.0, value), 6)
        for value in (
            refined_table,
            wage_score,
            numeric_score,
            non_wage_score,
            compact_score,
        )
    )


def gate2_diagnostics(
    *,
    source: dict[str, str],
    pages: list[PageEvidence],
    compact_score: float,
    unresolved_targets: list[int],
    printed_offsets: list[int],
) -> list[str]:
    """Produce transparent lowercase diagnostics, never prior answer labels."""

    codes: list[str] = []

    def add(code: str) -> None:
        if code not in codes:
            codes.append(code)

    candidate_pages = [page for page in pages if page.role == "candidate"]
    evidence_pages = [
        page
        for page in pages
        if page.role in {"candidate", "nearby", "navigation_target", "navigation_target_offset"}
    ]
    true_structure = any(
        page.role_pay_rows >= 2
        and (
            page.aligned_numeric_columns >= 1
            or page.row_like_lines >= 2
            or page.column_lines >= 2
        )
        and not page.index_signal
        and page.benefit_terms < 4
        and page.budget_terms < 4
        for page in evidence_pages
    )
    plausible = true_structure or any(
        page.compact_role_pay_lines >= 2
        and page.role_pay_rows >= 1
        and not page.index_signal
        for page in evidence_pages
    )
    if not plausible:
        add("no_candidate_detected")
    if any(
        page.wage_terms >= 1
        and page.role_pay_rows == 0
        and page.row_like_lines == 0
        and not page.index_signal
        for page in candidate_pages or evidence_pages
    ):
        add("candidate_is_prose_only")
    if any(page.index_signal for page in candidate_pages):
        add("candidate_is_index_or_contents")
    if unresolved_targets:
        add("target_table_outside_budget")
    if any(offset != 0 for offset in printed_offsets):
        add("possible_printed_page_offset")
    if compact_score >= 0.62 and any(
        page.compact_role_pay_lines >= 2 and page.role_pay_rows >= 1
        for page in evidence_pages
    ):
        add("compact_compensation_candidate")
    numeric_total = sum(page.numeric_tokens for page in evidence_pages)
    if numeric_total >= 4 and not true_structure and any(
        page.benefit_terms or page.budget_terms or page.index_signal
        for page in evidence_pages
    ):
        add("non_wage_numeric_table")
    if any(page.benefit_terms >= 3 for page in evidence_pages):
        add("benefits_table")
    if any(page.budget_terms >= 3 for page in evidence_pages):
        add("budget_table")
    if any(
        page.classification_terms >= 1
        and page.role_pay_rows == 0
        and page.numeric_tokens <= 1
        for page in evidence_pages
    ):
        add("classification_without_pay")
    if true_structure:
        add("true_wage_table_evidence")
    else:
        add("insufficient_role_pay_columns")
    if not source["blinded_candidate_pages"].strip() and not plausible:
        add("no_candidate_detected")
    if not set(codes) <= GATE2_DIAGNOSTIC_CODES:
        raise AssertionError("unknown Gate 2 diagnostic code")
    return codes


def prompt_for_case(evidence: CaseEvidence) -> str:
    page_payload = []
    for page in evidence.pages:
        page_payload.append(
            {
                "page_number": page.page_number,
                "page_role": page.role,
                "bounded_redacted_snippet": page.snippet,
                "features": {
                    "wage_terms": page.wage_terms,
                    "role_terms": page.role_terms,
                    "numeric_tokens": page.numeric_tokens,
                    "money_tokens": page.money_tokens,
                    "percent_tokens": page.percent_tokens,
                    "row_like_lines": page.row_like_lines,
                    "column_lines": page.column_lines,
                    "header_lines": page.header_lines,
                    "geometry_rows": page.geometry_rows,
                    "geometry_columns": page.geometry_columns,
                    "benefit_terms": page.benefit_terms,
                    "budget_terms": page.budget_terms,
                    "classification_terms": page.classification_terms,
                    "index_signal": page.index_signal,
                    "front_signal": page.front_signal,
                    "rendered_available": page.rendered_available,
                    "image_horizontal_bands": page.image_horizontal_bands,
                    "image_vertical_bands": page.image_vertical_bands,
                    "navigation_targets": page.navigation_targets,
                },
            }
        )
    response_shape = {
        "wage_schedule_present": "yes|maybe|no|unknown",
        "candidate_page_relationship": (
            "exact_table_page|adjacent_to_table|points_to_later_table|"
            "wrong_page|no_candidate_page|unknown"
        ),
        "visual_table_type": (
            "step_grade|rank_step|classification_pay_table|hourly_schedule|"
            "annual_salary_schedule|compact_compensation_sheet|"
            "percent_increase_only|prose_only|benefits_table|"
            "budget_or_fiscal_table|classification_without_pay|"
            "index_or_contents|front_matter|non_wage_table|no_table|other|unknown"
        ),
        "non_wage_family": (
            "not_applicable|benefits|budget_or_fiscal|"
            "classification_without_pay|incentive_or_bonus_prose|"
            "index_or_contents|front_matter|non_wage_appendix|"
            "memorandum_without_table|other|unknown"
        ),
        "navigation_needed": "yes|no|unknown",
        "navigation_target_found": "yes|no|not_applicable|unknown",
        "extraction_complexity": "easy|moderate|hard|not_extractable|unknown",
        "extraction_recommendation": (
            "extraction_ready|extraction_ready_with_schema_update|"
            "second_review_required|exclude_for_now|unknown"
        ),
        "confidence": "high|medium|low|unknown",
        "reason_codes": ["SHORT_CODE"],
        "short_rationale": "max 300 characters; no wage values",
    }
    packet = {
        "case_context": {
            "adjudication_case_id": evidence.source["adjudication_case_id"],
            "state": evidence.source["state"],
            "municipality": evidence.source["municipality"],
            "unit_type": evidence.source["unit_type"],
            "candidate_source_type": evidence.source["candidate_source_type"],
            "candidate_pages_present": bool(
                evidence.source["blinded_candidate_pages"]
            ),
        },
        "case_scores": {
            "table_structure": evidence.table_score,
            "wage_language": evidence.wage_score,
            "pay_numeric": evidence.numeric_score,
            "navigation": evidence.navigation_score,
            "non_wage_false_positive": evidence.non_wage_score,
            "compact_compensation_sheet": evidence.compact_score,
        },
        "pages": page_payload,
    }
    return (
        "You are evaluating a bounded packet of local PDF page evidence. "
        "Decide whether candidate pages show an extractable wage/salary/pay "
        "schedule. Distinguish wage prose, benefits, budgets/fiscal tables, "
        "classification without pay, front matter, contents/index, compact "
        "compensation sheets, and non-wage numeric appendices. Wage/pay "
        "language alone is not enough. Confirmed readiness requires visible "
        "or structural role/classification/rank rows plus wage/rate/salary "
        "columns, or a stable compact role/component-to-pay sheet. Treat "
        "feature scores as fallible evidence. Contents/index is a pointer, "
        "not a table; points_to_later_table requires included target evidence. "
        "Do not extract or repeat wage values. Do not infer unseen pages. "
        "Return one JSON object only, no markdown, using exactly these keys "
        f"and allowed values: {json.dumps(response_shape, separators=(',', ':'))}\n"
        f"BOUNDED_EVIDENCE={json.dumps(packet, separators=(',', ':'))}"
    )


def prompt_for_gate2_case(evidence: CaseEvidence) -> str:
    page_payload = []
    for page in evidence.pages:
        page_payload.append(
            {
                "page_number": page.page_number,
                "page_role": page.role,
                "bounded_redacted_snippet": page.snippet,
                "features": {
                    "wage_terms": page.wage_terms,
                    "role_terms": page.role_terms,
                    "numeric_tokens": page.numeric_tokens,
                    "money_tokens": page.money_tokens,
                    "row_like_lines": page.row_like_lines,
                    "column_lines": page.column_lines,
                    "header_lines": page.header_lines,
                    "geometry_rows": page.geometry_rows,
                    "geometry_columns": page.geometry_columns,
                    "role_pay_rows": page.role_pay_rows,
                    "aligned_numeric_columns": page.aligned_numeric_columns,
                    "compact_role_pay_lines": page.compact_role_pay_lines,
                    "benefit_terms": page.benefit_terms,
                    "budget_terms": page.budget_terms,
                    "classification_terms": page.classification_terms,
                    "index_signal": page.index_signal,
                    "front_signal": page.front_signal,
                    "rendered_available": page.rendered_available,
                    "image_horizontal_bands": page.image_horizontal_bands,
                    "image_vertical_bands": page.image_vertical_bands,
                    "navigation_target_printed_pages": page.navigation_targets,
                    "printed_page_number": page.printed_page_number,
                    "pdf_minus_printed_page_offset": page.printed_page_offset,
                },
            }
        )
    packet = {
        "case_context": {
            "adjudication_case_id": evidence.source["adjudication_case_id"],
            "state": evidence.source["state"],
            "municipality": evidence.source["municipality"],
            "unit_type": evidence.source["unit_type"],
            "candidate_source_type": evidence.source["candidate_source_type"],
            "candidate_pages_supplied": bool(
                evidence.source["blinded_candidate_pages"].strip()
            ),
        },
        "local_diagnostics_not_answer_labels": (
            evidence.diagnostic_reason_codes or []
        ),
        "case_scores": {
            "table_structure": evidence.table_score,
            "wage_language": evidence.wage_score,
            "pay_numeric": evidence.numeric_score,
            "navigation": evidence.navigation_score,
            "non_wage_false_positive": evidence.non_wage_score,
            "compact_compensation_sheet": evidence.compact_score,
        },
        "pages": page_payload,
    }
    response_shape = {
        "wage_schedule_present": "yes|maybe|no|unknown",
        "candidate_page_relationship": (
            "exact_table_page|adjacent_to_table|points_to_later_table|"
            "wrong_page|no_candidate_page|unknown"
        ),
        "visual_table_type": (
            "step_grade|rank_step|classification_pay_table|hourly_schedule|"
            "annual_salary_schedule|compact_compensation_sheet|"
            "percent_increase_only|prose_only|benefits_table|"
            "budget_or_fiscal_table|classification_without_pay|"
            "index_or_contents|front_matter|non_wage_table|no_table|other|unknown"
        ),
        "non_wage_family": (
            "not_applicable|benefits|budget_or_fiscal|"
            "classification_without_pay|incentive_or_bonus_prose|"
            "index_or_contents|front_matter|non_wage_appendix|"
            "memorandum_without_table|other|unknown"
        ),
        "navigation_needed": "yes|no|unknown",
        "navigation_target_found": "yes|no|not_applicable|unknown",
        "extraction_complexity": "easy|moderate|hard|not_extractable|unknown",
        "extraction_recommendation": (
            "extraction_ready|extraction_ready_with_schema_update|"
            "second_review_required|exclude_for_now|unknown"
        ),
        "confidence": "high|medium|low|unknown",
        "reason_codes": ["SHORT_UPPERCASE_CODE"],
        "short_rationale": "max 300 characters; no wage values",
    }
    return (
        "Evaluate only this bounded local PDF-page packet. Wage/pay prose is "
        "not a schedule. A positive schedule requires structured role, "
        "classification, rank, grade, or position evidence plus pay bands, "
        "rates, salaries, or repeated role-to-pay lines. no_candidate_page "
        "means this packet lacks a plausible table target; wrong_page means a "
        "supplied candidate exists but is materially unrelated or a distinct "
        "non-wage family. exact_table_page applies to an included candidate; "
        "adjacent_to_table applies when an included neighbor has the table. "
        "Contents/index is only a pointer. points_to_later_table requires the "
        "referenced target itself in the packet with supporting table evidence. "
        "Do not infer unseen targets. A compact compensation sheet may be "
        "schema-usable only when it structurally maps roles/classifications to "
        "pay bands, rates, or salaries. Benefits, budget/fiscal, classification "
        "without pay, front matter, prose-only, and non-wage numeric tables "
        "cannot be high-confidence wage schedules. Local diagnostics are "
        "fallible transparent features, not answer labels. Do not extract or "
        "repeat wage values. Return one strict JSON object only, no markdown, "
        "using exactly these fields and allowed values: "
        f"{json.dumps(response_shape, separators=(',', ':'))}\n"
        f"BOUNDED_EVIDENCE={json.dumps(packet, separators=(',', ':'))}"
    )


def build_case_evidence(
    source: dict[str, str],
    *,
    gate_id: str,
    render_map: dict[int, dict[str, str]],
    max_pages: int,
    navigation_budget: int,
    max_chars_per_page: int,
    max_chars_per_case: int,
    gate_mode: str = GATE1_MODE,
    candidate_window: int = 1,
) -> CaseEvidence:
    artifact = resolve_local_path(source["content_artifact_path"])
    if artifact.suffix.lower() != ".pdf" or not artifact.is_file():
        raise FileNotFoundError(f"missing local PDF: {artifact}")
    with artifact.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError("artifact does not have a PDF signature")
    reader = PdfReader(str(artifact))
    page_count = int(source["pdf_page_count"])
    if len(reader.pages) != page_count:
        raise ValueError("PDF page count differs from blinded packet")
    initial = (
        choose_gate2_initial_pages(
            source,
            max_pages=max_pages,
            navigation_budget=navigation_budget,
            candidate_window=candidate_window,
        )
        if gate_mode == GATE2_MODE
        else choose_initial_pages(
            source, max_pages=max_pages, navigation_budget=navigation_budget
        )
    )
    pages: list[PageEvidence] = []
    used: set[int] = set()
    remaining_chars = max_chars_per_case
    for page_number, role in initial:
        maximum = min(max_chars_per_page, remaining_chars)
        evidence = page_evidence(
            page=reader.pages[page_number - 1],
            page_number=page_number,
            role=role,
            page_count=page_count,
            rendered=render_map.get(page_number),
            max_chars=maximum,
            gate_mode=gate_mode,
        )
        pages.append(evidence)
        used.add(page_number)
        remaining_chars -= evidence.snippet_chars
    referenced: list[int] = []
    for page in pages:
        for target in page.navigation_targets:
            if target not in referenced:
                referenced.append(target)
    navigation_added = 0
    printed_offsets = sorted(
        {
            page.printed_page_offset
            for page in pages
            if page.printed_page_offset is not None
            and page.printed_page_offset != 0
        }
    )
    unresolved_targets: list[int] = []
    resolved_targets: list[int] = []
    if gate_mode == GATE2_MODE:
        navigation_added = sum(page.role == "navigation" for page in pages)
        for printed_target in referenced:
            proposals: list[tuple[int, str]] = []
            for offset in printed_offsets:
                adjusted = printed_target + offset
                if 1 <= adjusted <= page_count:
                    proposals.append((adjusted, "navigation_target_offset"))
            if 1 <= printed_target <= page_count:
                proposals.append((printed_target, "navigation_target"))
            added_target = False
            for target, role in proposals:
                if target in used:
                    resolved_targets.append(target)
                    added_target = True
                    break
                if (
                    len(pages) >= max_pages
                    or remaining_chars <= 0
                    or navigation_added >= navigation_budget
                ):
                    continue
                evidence = page_evidence(
                    page=reader.pages[target - 1],
                    page_number=target,
                    role=role,
                    page_count=page_count,
                    rendered=render_map.get(target),
                    max_chars=min(max_chars_per_page, remaining_chars),
                    gate_mode=gate_mode,
                )
                pages.append(evidence)
                used.add(target)
                navigation_added += 1
                remaining_chars -= evidence.snippet_chars
                resolved_targets.append(target)
                added_target = True
                break
            if not added_target:
                unresolved_targets.append(printed_target)
    else:
        for target in referenced:
            if len(pages) >= max_pages or remaining_chars <= 0:
                break
            if target in used or navigation_added >= navigation_budget:
                continue
            evidence = page_evidence(
                page=reader.pages[target - 1],
                page_number=target,
                role="navigation_target",
                page_count=page_count,
                rendered=render_map.get(target),
                max_chars=min(max_chars_per_page, remaining_chars),
                gate_mode=gate_mode,
            )
            pages.append(evidence)
            used.add(target)
            navigation_added += 1
            remaining_chars -= evidence.snippet_chars
    if len(pages) < max_pages and remaining_chars > 0:
        fallback_navigation = parse_pages(
            source["blinded_navigation_pages"], page_count
        )[:navigation_budget]
        for page_number in fallback_navigation:
            if len(pages) >= max_pages or remaining_chars <= 0:
                break
            if gate_mode == GATE2_MODE and navigation_added >= navigation_budget:
                break
            if page_number in used:
                continue
            evidence = page_evidence(
                page=reader.pages[page_number - 1],
                page_number=page_number,
                role="navigation",
                page_count=page_count,
                rendered=render_map.get(page_number),
                max_chars=min(max_chars_per_page, remaining_chars),
                gate_mode=gate_mode,
            )
            pages.append(evidence)
            used.add(page_number)
            if gate_mode == GATE2_MODE:
                navigation_added += 1
            remaining_chars -= evidence.snippet_chars
    if len(pages) > max_pages:
        raise AssertionError("page budget exceeded")
    if gate_mode == GATE2_MODE and sum(
        page.role
        in {"navigation", "navigation_target", "navigation_target_offset"}
        for page in pages
    ) > navigation_budget:
        raise AssertionError("Gate 2 navigation-page budget exceeded")
    if any(page.snippet_chars > max_chars_per_page for page in pages):
        raise AssertionError("per-page text cap exceeded")
    text_chars = sum(page.snippet_chars for page in pages)
    if text_chars > max_chars_per_case:
        raise AssertionError("per-case text cap exceeded")
    table_score, wage_score, numeric_score, non_wage_score, compact_score = (
        score_case_gate2(pages)
        if gate_mode == GATE2_MODE
        else score_case(pages)
    )
    targets_evaluated = (
        sorted(set(resolved_targets))
        if gate_mode == GATE2_MODE
        else [
            page.page_number
            for page in pages
            if page.role == "navigation_target"
        ]
    )
    has_reference = any(page.navigation_targets for page in pages)
    navigation_score = (
        1.0
        if targets_evaluated
        else 0.5
        if has_reference
        else 0.2
        if any(page.index_signal for page in pages)
        else 0.0
    )
    diagnostics = (
        gate2_diagnostics(
            source=source,
            pages=pages,
            compact_score=compact_score,
            unresolved_targets=unresolved_targets,
            printed_offsets=printed_offsets,
        )
        if gate_mode == GATE2_MODE
        else []
    )
    case = CaseEvidence(
        source=source,
        auto_id=auto_id(gate_id, source["calibration_id"]),
        pages=pages,
        candidate_pages=[
            page.page_number for page in pages if page.role == "candidate"
        ],
        nearby_pages=[
            page.page_number for page in pages if page.role == "nearby"
        ],
        navigation_pages=[
            page.page_number
            for page in pages
            if page.role
            in {"navigation", "navigation_target", "navigation_target_offset"}
        ],
        text_chars=text_chars,
        table_score=table_score,
        wage_score=wage_score,
        numeric_score=numeric_score,
        navigation_score=round(navigation_score, 6),
        non_wage_score=non_wage_score,
        compact_score=compact_score,
        navigation_targets_found=targets_evaluated,
        prompt="",
        gate_mode=gate_mode,
        diagnostic_reason_codes=diagnostics,
        printed_page_offsets=printed_offsets,
        unresolved_navigation_targets=unresolved_targets,
    )
    case.prompt = (
        prompt_for_gate2_case(case)
        if gate_mode == GATE2_MODE
        else prompt_for_case(case)
    )
    forbidden_prompt_markers = (
        "extraction_gate_label",
        "wage_schedule_table_confirmed_label",
        "REVIEW1",
        "REVIEW2",
        "GATE1",
        "Gate 1",
        "gate1",
        "auto_gate_label",
        "recommended_extraction_action",
    )
    if any(marker in case.prompt for marker in forbidden_prompt_markers):
        raise AssertionError("prior label marker entered the primary prompt")
    return case


def validate_gabriel_response(raw: str) -> dict[str, Any]:
    parsed = json.loads(raw.strip())
    if not isinstance(parsed, dict):
        raise ValueError("GABRIEL response is not a JSON object")
    if set(parsed) != GABRIEL_RESPONSE_KEYS:
        raise ValueError("GABRIEL response keys do not match strict schema")
    for field, allowed in ALLOWED.items():
        if parsed[field] not in allowed:
            raise ValueError(f"invalid {field}: {parsed[field]!r}")
    codes = parsed["reason_codes"]
    if (
        not isinstance(codes, list)
        or not 1 <= len(codes) <= 12
        or any(
            not isinstance(code, str) or not REASON_CODE_RE.fullmatch(code)
            for code in codes
        )
    ):
        raise ValueError("invalid reason_codes")
    rationale = parsed["short_rationale"]
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("short_rationale must be nonempty")
    if len(rationale) > 300:
        raise ValueError("short_rationale exceeds 300 characters")
    return parsed


def empty_gabriel(
    *, backend: str, model: str, status: str = "not_called"
) -> dict[str, str]:
    return {
        "gabriel_request_id": "",
        "gabriel_backend": backend,
        "gabriel_model": model,
        "gabriel_status": status,
        "gabriel_schema_valid": "false",
        "gabriel_wage_schedule_present": "unknown",
        "gabriel_candidate_page_relationship": "unknown",
        "gabriel_visual_table_type": "unknown",
        "gabriel_non_wage_family": "unknown",
        "gabriel_navigation_needed": "unknown",
        "gabriel_navigation_target_found": "unknown",
        "gabriel_extraction_complexity": "unknown",
        "gabriel_extraction_recommendation": "unknown",
        "gabriel_confidence": "unknown",
        "gabriel_reason_codes": "",
        "gabriel_short_rationale": "",
        "gabriel_input_page_count": "0",
        "gabriel_input_text_chars": "0",
        "gabriel_elapsed_seconds": "0.000000",
    }


def combine_gate(
    evidence: CaseEvidence, gabriel: dict[str, str]
) -> dict[str, str]:
    if gabriel["gabriel_status"] in {
        "not_called",
        "credential_unavailable",
        "request_failed",
        "timeout",
    }:
        return {
            "auto_gate_label": "gabriel_unavailable",
            "auto_gate_confidence": "unknown",
            "auto_gate_reason_codes": "GABRIEL_REQUIRED",
            "auto_gate_rationale": (
                "Fail closed: a schema-valid bounded GABRIEL adjudication is "
                "required before an automated extraction gate can be assigned."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    if gabriel["gabriel_schema_valid"] != "true":
        return {
            "auto_gate_label": "error",
            "auto_gate_confidence": "unknown",
            "auto_gate_reason_codes": "GABRIEL_SCHEMA_INVALID",
            "auto_gate_rationale": (
                "Fail closed: the GABRIEL response did not satisfy the strict "
                "adjudication schema."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    table_type = gabriel["gabriel_visual_table_type"]
    non_wage = gabriel["gabriel_non_wage_family"]
    relationship = gabriel["gabriel_candidate_page_relationship"]
    recommendation = gabriel["gabriel_extraction_recommendation"]
    confidence = gabriel["gabriel_confidence"]
    wage_present = gabriel["gabriel_wage_schedule_present"]
    target_found = gabriel["gabriel_navigation_target_found"]
    rendered = any(page.rendered_available for page in evidence.pages)
    local_strong = (
        evidence.table_score >= 0.62
        and evidence.wage_score >= 0.32
        and evidence.numeric_score >= 0.35
        and evidence.non_wage_score <= 0.58
        and rendered
    )
    local_schema_ready = (
        evidence.table_score >= 0.42
        and evidence.wage_score >= 0.25
        and evidence.numeric_score >= 0.25
        and evidence.non_wage_score <= 0.72
    ) or evidence.compact_score >= 0.62
    negative = table_type in NEGATIVE_TABLE_TYPES or non_wage in NEGATIVE_FAMILIES
    relationship_resolved = relationship in {
        "exact_table_page",
        "adjacent_to_table",
    } or (
        relationship == "points_to_later_table"
        and target_found == "yes"
        and bool(evidence.navigation_targets_found)
    )
    model_positive = (
        wage_present == "yes"
        and table_type in POSITIVE_TABLE_TYPES
        and non_wage == "not_applicable"
        and relationship_resolved
        and confidence in {"high", "medium"}
    )
    if (
        model_positive
        and recommendation == "extraction_ready"
        and local_strong
    ):
        codes = [
            "GABRIEL_LOCAL_AGREE",
            "ROW_COLUMN_EVIDENCE",
            "PAGE_RELATIONSHIP_RESOLVED",
        ]
        return {
            "auto_gate_label": "extraction_ready_high_confidence",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "|".join(codes),
            "auto_gate_rationale": (
                "Schema-valid GABRIEL and strong local rendered/text geometry "
                "agree on a bounded wage-schedule page with resolved page identity."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "true",
        }
    if (
        model_positive
        and recommendation
        in {"extraction_ready", "extraction_ready_with_schema_update"}
        and local_schema_ready
    ):
        codes = ["GABRIEL_POSITIVE", "LOCAL_SCHEMA_UPDATE_EVIDENCE"]
        if relationship == "points_to_later_table":
            codes.append("BOUNDED_NAVIGATION_TARGET")
        if table_type == "compact_compensation_sheet":
            codes.append("COMPACT_COMPENSATION_SHEET")
        return {
            "auto_gate_label": "extraction_ready_with_schema_update",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "|".join(codes),
            "auto_gate_rationale": (
                "Bounded evidence supports a wage schedule, but local structure, "
                "compact layout, or navigation requires a schema-specific rule."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": (
                "true" if confidence in {"high", "medium"} else "false"
            ),
        }
    unresolved_navigation = (
        relationship == "points_to_later_table"
        and target_found != "yes"
    ) or (
        gabriel["gabriel_navigation_needed"] == "yes"
        and gabriel["gabriel_navigation_target_found"] != "yes"
    )
    if (
        negative
        and recommendation == "exclude_for_now"
        and confidence in {"high", "medium"}
    ):
        return {
            "auto_gate_label": "exclude_for_now",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "NON_WAGE_OR_PROSE_CONFIRMED",
            "auto_gate_rationale": (
                "GABRIEL identifies prose or a non-wage page family, and the "
                "local evidence does not satisfy the strict positive table gate."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    codes = ["EVIDENCE_NOT_STRONG_ENOUGH"]
    if unresolved_navigation:
        codes.append("NAVIGATION_TARGET_UNRESOLVED")
    if negative:
        codes.append("NEGATIVE_PAGE_FAMILY")
    if not local_schema_ready:
        codes.append("LOCAL_STRUCTURE_WEAK")
    return {
        "auto_gate_label": "second_review_required",
        "auto_gate_confidence": confidence,
        "auto_gate_reason_codes": "|".join(codes),
        "auto_gate_rationale": (
            "The bounded GABRIEL/local evidence is ambiguous, weak, conflicting, "
            "or navigation-dependent and cannot support an extraction-ready label."
        ),
        "auto_gate_passes_500_doc_criteria_candidate": "false",
    }


def combine_gate2(
    evidence: CaseEvidence, gabriel: dict[str, str]
) -> dict[str, str]:
    """Apply Gate 2 direct-structure and navigation refinements fail closed."""

    base = combine_gate(evidence, gabriel)
    if base["auto_gate_label"] in {"gabriel_unavailable", "error"}:
        return base
    diagnostics = set(evidence.diagnostic_reason_codes or [])
    table_type = gabriel["gabriel_visual_table_type"]
    relationship = gabriel["gabriel_candidate_page_relationship"]
    recommendation = gabriel["gabriel_extraction_recommendation"]
    confidence = gabriel["gabriel_confidence"]
    wage_present = gabriel["gabriel_wage_schedule_present"]
    non_wage = gabriel["gabriel_non_wage_family"]
    relationship_resolved = relationship in {
        "exact_table_page",
        "adjacent_to_table",
    } or (
        relationship == "points_to_later_table"
        and gabriel["gabriel_navigation_target_found"] == "yes"
        and bool(evidence.navigation_targets_found)
    )
    negative = table_type in NEGATIVE_TABLE_TYPES or non_wage in NEGATIVE_FAMILIES
    if negative and base["auto_gate_label"].startswith("extraction_ready"):
        return {
            "auto_gate_label": "second_review_required",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "GATE2_NEGATIVE_FAMILY_VETO",
            "auto_gate_rationale": (
                "Gate 2 vetoes an extraction-ready label because the bounded "
                "evidence contains a negative table or non-wage family."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    compact_ready = (
        table_type == "compact_compensation_sheet"
        and "compact_compensation_candidate" in diagnostics
        and wage_present == "yes"
        and non_wage == "not_applicable"
        and relationship_resolved
        and recommendation
        in {"extraction_ready", "extraction_ready_with_schema_update"}
        and confidence in {"high", "medium"}
    )
    if compact_ready:
        return {
            "auto_gate_label": "extraction_ready_with_schema_update",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": (
                "GATE2_COMPACT_ROLE_PAY_EVIDENCE|SCHEMA_UPDATE_REQUIRED"
            ),
            "auto_gate_rationale": (
                "Direct compact role-to-pay evidence and schema-valid GABRIEL "
                "agreement support a separate compact-compensation schema."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "true",
        }
    if "target_table_outside_budget" in diagnostics and relationship in {
        "points_to_later_table",
        "unknown",
    }:
        return {
            "auto_gate_label": "second_review_required",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "GATE2_TARGET_OUTSIDE_BUDGET",
            "auto_gate_rationale": (
                "A bounded navigation reference could not be resolved inside "
                "the six-page/four-navigation-page budget."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    if base["auto_gate_label"] == "extraction_ready_high_confidence" and (
        "true_wage_table_evidence" not in diagnostics
    ):
        return {
            "auto_gate_label": "second_review_required",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "GATE2_ROLE_PAY_STRUCTURE_REQUIRED",
            "auto_gate_rationale": (
                "GABRIEL is positive, but Gate 2 lacks repeated local role/pay "
                "rows or aligned pay columns required for high confidence."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    if base["auto_gate_label"] == "extraction_ready_with_schema_update" and not (
        "true_wage_table_evidence" in diagnostics
        or "compact_compensation_candidate" in diagnostics
    ):
        return {
            "auto_gate_label": "second_review_required",
            "auto_gate_confidence": confidence,
            "auto_gate_reason_codes": "GATE2_INSUFFICIENT_ROLE_PAY_COLUMNS",
            "auto_gate_rationale": (
                "The bounded model judgment is positive, but Gate 2 direct "
                "role/pay-column evidence remains insufficient."
            ),
            "auto_gate_passes_500_doc_criteria_candidate": "false",
        }
    if base["auto_gate_label"] == "extraction_ready_high_confidence":
        base["auto_gate_reason_codes"] += "|GATE2_DIRECT_STRUCTURE_CONFIRMED"
    elif base["auto_gate_label"] == "extraction_ready_with_schema_update":
        base["auto_gate_reason_codes"] += "|GATE2_DIRECT_STRUCTURE_SUPPORTED"
    return base


def load_subscription_key() -> tuple[str | None, str]:
    from dotenv import dotenv_values, load_dotenv

    project_env = ROOT / ".env"
    parent_env = ROOT.parent / ".env"
    selected = (
        project_env
        if project_env.is_file()
        else parent_env
        if parent_env.is_file()
        else None
    )
    values = dotenv_values(selected) if selected else {}
    if selected:
        load_dotenv(selected, override=False)
    key = os.environ.get("HARVARD_SUBSCRIPTION_KEY") or values.get(
        "HARVARD_SUBSCRIPTION_KEY"
    )
    location = (
        "project_root"
        if selected == project_env
        else "parent"
        if selected == parent_env
        else "none"
    )
    return str(key) if key else None, location


async def _run_direct_sdk_batch(
    cases: list[CaseEvidence],
    *,
    key: str,
    model: str,
    timeout: float,
    parallel: int,
) -> list[LiveResult]:
    import httpx
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=key,
        base_url=BASE_URL,
        default_headers={"Ocp-Apim-Subscription-Key": key},
        timeout=httpx.Timeout(timeout),
        max_retries=0,
    )
    semaphore = asyncio.Semaphore(parallel)

    async def run_one(case: CaseEvidence) -> LiveResult:
        started = time.monotonic()
        async with semaphore:
            try:
                response = await asyncio.wait_for(
                    client.responses.create(
                        model=model,
                        input=case.prompt,
                        reasoning={"effort": "low"},
                        text={
                            "format": {
                                "type": "json_schema",
                                "name": "bounded_text_table_adjudication",
                                "strict": True,
                                "schema": GABRIEL_JSON_SCHEMA,
                            }
                        },
                    ),
                    timeout=timeout,
                )
                usage = getattr(response, "usage", None)
                return LiveResult(
                    request_id=str(getattr(response, "id", "") or ""),
                    status="success",
                    response_text=str(
                        getattr(response, "output_text", "") or ""
                    ),
                    elapsed_seconds=time.monotonic() - started,
                    input_tokens=int(
                        getattr(usage, "input_tokens", 0) or 0
                    ),
                    output_tokens=int(
                        getattr(usage, "output_tokens", 0) or 0
                    ),
                    total_tokens=int(
                        getattr(usage, "total_tokens", 0) or 0
                    ),
                    error_type="",
                    error_message="",
                )
            except asyncio.TimeoutError:
                return LiveResult(
                    request_id="",
                    status="timeout",
                    response_text="",
                    elapsed_seconds=time.monotonic() - started,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    error_type="DirectSDKOuterTimeoutError",
                    error_message=f"outer deadline exceeded {timeout:g} seconds",
                )
            except Exception as exc:
                return LiveResult(
                    request_id="",
                    status="request_failed",
                    response_text="",
                    elapsed_seconds=time.monotonic() - started,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    error_type=type(exc).__name__,
                    error_message=safe_error(exc, key),
                )

    try:
        return list(await asyncio.gather(*(run_one(case) for case in cases)))
    finally:
        await client.close()


def run_live_requests(
    cases: list[CaseEvidence],
    *,
    key: str,
    backend: str,
    model: str,
    timeout: float,
    parallel: int,
) -> list[LiveResult]:
    if backend != DEFAULT_BACKEND:
        raise ValueError(f"unsupported GABRIEL backend: {backend}")
    return asyncio.run(
        _run_direct_sdk_batch(
            cases,
            key=key,
            model=model,
            timeout=timeout,
            parallel=parallel,
        )
    )


def local_fields(evidence: CaseEvidence) -> dict[str, str]:
    totals = {
        "wage_terms": sum(page.wage_terms for page in evidence.pages),
        "role_terms": sum(page.role_terms for page in evidence.pages),
        "numeric_tokens": sum(page.numeric_tokens for page in evidence.pages),
        "benefit_terms": sum(page.benefit_terms for page in evidence.pages),
        "budget_terms": sum(page.budget_terms for page in evidence.pages),
        "index_pages": sum(page.index_signal for page in evidence.pages),
    }
    layout = {
        "row_like_lines": sum(page.row_like_lines for page in evidence.pages),
        "column_lines": sum(page.column_lines for page in evidence.pages),
        "geometry_rows": sum(page.geometry_rows for page in evidence.pages),
        "geometry_columns": sum(
            page.geometry_columns for page in evidence.pages
        ),
        "rendered_pages": sum(
            page.rendered_available for page in evidence.pages
        ),
        "navigation_targets_evaluated": len(
            evidence.navigation_targets_found
        ),
    }
    return {
        "local_text_signal_summary": bounded(
            json.dumps(totals, sort_keys=True, separators=(",", ":")), 500
        ),
        "local_layout_signal_summary": bounded(
            json.dumps(layout, sort_keys=True, separators=(",", ":")), 500
        ),
        "rendered_page_available": (
            "true" if layout["rendered_pages"] else "false"
        ),
        "rendered_page_count_used": str(layout["rendered_pages"]),
        "table_structure_feature_score": f"{evidence.table_score:.6f}",
        "wage_language_feature_score": f"{evidence.wage_score:.6f}",
        "pay_numeric_feature_score": f"{evidence.numeric_score:.6f}",
        "navigation_feature_score": f"{evidence.navigation_score:.6f}",
        "non_wage_false_positive_feature_score": (
            f"{evidence.non_wage_score:.6f}"
        ),
        "compact_compensation_sheet_feature_score": (
            f"{evidence.compact_score:.6f}"
        ),
    }


def gate2_fields(evidence: CaseEvidence) -> dict[str, str]:
    summary = {
        "candidate_pages": len(evidence.candidate_pages),
        "nearby_pages": len(evidence.nearby_pages),
        "navigation_pages": len(evidence.navigation_pages),
        "role_pay_rows": sum(page.role_pay_rows for page in evidence.pages),
        "aligned_numeric_columns": sum(
            page.aligned_numeric_columns for page in evidence.pages
        ),
        "compact_role_pay_lines": sum(
            page.compact_role_pay_lines for page in evidence.pages
        ),
        "resolved_navigation_targets": len(evidence.navigation_targets_found),
        "unresolved_navigation_targets": len(
            evidence.unresolved_navigation_targets or []
        ),
    }
    return {
        "gate_mode": evidence.gate_mode,
        "gate2_diagnostic_reason_codes": "|".join(
            evidence.diagnostic_reason_codes or []
        ),
        "gate2_candidate_discovery_summary": bounded(
            json.dumps(summary, sort_keys=True, separators=(",", ":")), 600
        ),
        "gate2_printed_page_offsets": ",".join(
            str(value) for value in evidence.printed_page_offsets or []
        ),
    }


def identity_fields(evidence: CaseEvidence) -> dict[str, str]:
    source = evidence.source
    return {
        "auto_adjudication_id": evidence.auto_id,
        "adjudication_case_id": source["adjudication_case_id"],
        "calibration_id": source["calibration_id"],
        "source_review_id": source["source_review_id"],
        "pdf_readiness_id": source["pdf_readiness_id"],
        "candidate_queue_row_id": source["candidate_queue_row_id"],
        "state": source["state"],
        "municipality": source["municipality"],
        "government_name": source["government_name"],
        "unit_type": source["unit_type"],
        "candidate_source_type": source["candidate_source_type"],
        "pdf_page_count": source["pdf_page_count"],
        "content_artifact_path": source["content_artifact_path"],
        "candidate_pages_evaluated": format_pages(evidence.candidate_pages),
        "nearby_pages_evaluated": format_pages(evidence.nearby_pages),
        "navigation_pages_evaluated": format_pages(
            evidence.navigation_pages
        ),
    }


def gabriel_fields_from_result(
    *,
    evidence: CaseEvidence,
    result: LiveResult,
    backend: str,
    model: str,
) -> tuple[dict[str, str], dict[str, object], dict[str, str] | None]:
    fields = empty_gabriel(backend=backend, model=model, status=result.status)
    fields.update(
        {
            "gabriel_request_id": result.request_id,
            "gabriel_input_page_count": str(len(evidence.pages)),
            "gabriel_input_text_chars": str(evidence.text_chars),
            "gabriel_elapsed_seconds": f"{result.elapsed_seconds:.6f}",
        }
    )
    metadata: dict[str, object] = {
        "auto_adjudication_id": evidence.auto_id,
        "calibration_id": evidence.source["calibration_id"],
        "gabriel_request_id": result.request_id,
        "gabriel_backend": backend,
        "gabriel_model": model,
        "request_status": result.status,
        "prompt_sha256": sha256_bytes(evidence.prompt.encode("utf-8")),
        "prompt_chars": len(evidence.prompt),
        "input_page_count": len(evidence.pages),
        "input_text_chars": evidence.text_chars,
        "prior_labels_in_prompt": False,
        "raw_prompt_saved": False,
        "raw_response_saved": False,
        "response_chars": len(result.response_text),
        "response_sha256": (
            sha256_bytes(result.response_text.encode("utf-8"))
            if result.response_text
            else ""
        ),
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens,
        "elapsed_seconds": round(result.elapsed_seconds, 6),
        "error_type": result.error_type,
        "error_message": result.error_message,
        "credential_value_saved": False,
        "authorization_header_saved": False,
    }
    if result.status != "success":
        failed = {
            "auto_adjudication_id": evidence.auto_id,
            "calibration_id": evidence.source["calibration_id"],
            "gabriel_status": result.status,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }
        return fields, metadata, failed
    try:
        parsed = validate_gabriel_response(result.response_text)
    except (json.JSONDecodeError, ValueError) as exc:
        fields["gabriel_status"] = "schema_invalid"
        metadata["request_status"] = "schema_invalid"
        metadata["error_type"] = type(exc).__name__
        metadata["error_message"] = bounded(str(exc), 240)
        failed = {
            "auto_adjudication_id": evidence.auto_id,
            "calibration_id": evidence.source["calibration_id"],
            "gabriel_status": "schema_invalid",
            "error_type": type(exc).__name__,
            "error_message": bounded(str(exc), 240),
        }
        return fields, metadata, failed
    fields.update(
        {
            "gabriel_status": "success",
            "gabriel_schema_valid": "true",
            "gabriel_wage_schedule_present": parsed[
                "wage_schedule_present"
            ],
            "gabriel_candidate_page_relationship": parsed[
                "candidate_page_relationship"
            ],
            "gabriel_visual_table_type": parsed["visual_table_type"],
            "gabriel_non_wage_family": parsed["non_wage_family"],
            "gabriel_navigation_needed": parsed["navigation_needed"],
            "gabriel_navigation_target_found": parsed[
                "navigation_target_found"
            ],
            "gabriel_extraction_complexity": parsed[
                "extraction_complexity"
            ],
            "gabriel_extraction_recommendation": parsed[
                "extraction_recommendation"
            ],
            "gabriel_confidence": parsed["confidence"],
            "gabriel_reason_codes": "|".join(parsed["reason_codes"]),
            "gabriel_short_rationale": parsed["short_rationale"],
        }
    )
    return fields, metadata, None


def decision_metrics(
    ledger: list[dict[str, str]],
    input_rows: list[dict[str, str]],
    gate_mode: str = GATE1_MODE,
) -> dict[str, Any]:
    original: dict[str, dict[str, str]] = {}
    if ORIGINAL_CALIBRATION_PATH.is_file():
        _, original_rows = read_csv(ORIGINAL_CALIBRATION_PATH)
        original = {row["calibration_id"]: row for row in original_rows}
    schema_valid = sum(
        row["gabriel_schema_valid"] == "true" for row in ledger
    )
    ready_labels = {
        "extraction_ready_high_confidence",
        "extraction_ready_with_schema_update",
    }
    eligible_likely_rows = [
        row
        for row in ledger
        if original.get(row["calibration_id"], {}).get("wage_table_signal")
        == "likely"
        and original.get(row["calibration_id"], {}).get(
            "extraction_pilot_priority"
        )
        == "p1"
    ]
    likely_ready = sum(
        row["auto_gate_label"] in ready_labels
        and row["auto_gate_confidence"] in {"high", "medium"}
        for row in eligible_likely_rows
    )
    candidate_case_ids = {
        row["adjudication_case_id"]
        for row in input_rows
        if row["blinded_candidate_pages"].strip()
    }
    candidate_ledger = [
        row
        for row in ledger
        if row["adjudication_case_id"] in candidate_case_ids
    ]
    wrong_pages = sum(
        row["gabriel_candidate_page_relationship"] == "wrong_page"
        for row in candidate_ledger
    )
    ready_rows = [row for row in ledger if row["auto_gate_label"] in ready_labels]
    non_wage_positive = sum(
        row["gabriel_non_wage_family"] in NEGATIVE_FAMILIES
        for row in ready_rows
    )
    unit_ready = Counter(row["unit_type"] for row in ready_rows)
    source_ready = Counter(row["candidate_source_type"] for row in ready_rows)
    second_review = sum(
        row["auto_gate_label"] == "second_review_required" for row in ledger
    )
    schema_rate = schema_valid / len(ledger) if ledger else 0.0
    likely_rate = (
        likely_ready / len(eligible_likely_rows)
        if eligible_likely_rows
        else 0.0
    )
    wrong_rate = (
        wrong_pages / len(candidate_ledger) if candidate_ledger else 1.0
    )
    representation_pass = (
        len(ready_rows) >= 30
        and all(unit_ready.get(value, 0) >= 5 for value in ("police", "fire", "non_safety"))
        and sum(count > 0 for count in source_ready.values()) >= 3
    )
    ambiguity_pass = (
        non_wage_positive == 0
        and second_review / max(1, len(ledger)) <= 0.20
    )
    full_scope = len(ledger) == 150
    five_hundred = all(
        (
            full_scope,
            schema_rate >= 0.95,
            likely_rate >= 0.80,
            wrong_rate <= 0.15,
            representation_pass,
            ambiguity_pass,
        )
    )
    smaller = (
        full_scope
        and not five_hundred
        and schema_rate >= 0.95
        and likely_rate >= 0.65
        and wrong_rate <= 0.20
        and len(ready_rows) >= 30
        and non_wage_positive <= 2
    )
    decision = (
        "500_doc_extraction_allowed"
        if five_hundred
        else "smaller_extraction_pilot_only"
        if smaller
        else "continue_schema_refinement"
    )
    return {
        "full_150_case_scope": full_scope,
        "case_count": len(ledger),
        "gabriel_schema_valid_count": schema_valid,
        "gabriel_schema_valid_rate": round(schema_rate, 6),
        "original_likely_p1_denominator": len(eligible_likely_rows),
        "original_likely_p1_ready_count": likely_ready,
        "original_likely_p1_ready_rate": round(likely_rate, 6),
        "candidate_bearing_denominator": len(candidate_ledger),
        "wrong_page_count": wrong_pages,
        "wrong_page_rate": round(wrong_rate, 6),
        "ready_count": len(ready_rows),
        "ready_unit_type_counts": dict(sorted(unit_ready.items())),
        "ready_source_type_counts": dict(sorted(source_ready.items())),
        "non_wage_positive_ready_count": non_wage_positive,
        "second_review_count": second_review,
        "representation_pass": representation_pass,
        "systematic_ambiguity_pass": ambiguity_pass,
        "five_hundred_criteria": {
            "likely_p1_rate_at_least_0_80": likely_rate >= 0.80,
            "wrong_page_rate_at_most_0_15": wrong_rate <= 0.15,
            "schema_valid_rate_at_least_0_95": schema_rate >= 0.95,
            "representative_ready_rows": representation_pass,
            "non_wage_false_positives_and_ambiguity_resolved": ambiguity_pass,
        },
        "extraction_decision": decision,
        "five_hundred_doc_extraction_allowed": decision
        == "500_doc_extraction_allowed",
        "smaller_extraction_pilot_allowed": decision
        == "smaller_extraction_pilot_only",
        "next_recommendation": (
            "prepare_500_doc_extraction_prompt"
            if decision == "500_doc_extraction_allowed"
            else "prepare_smaller_extraction_pilot"
            if decision == "smaller_extraction_pilot_only"
            else "refine_auto_gabriel_gate3_candidate_discovery"
            if gate_mode == GATE2_MODE
            else "refine_auto_gabriel_table_and_navigation_gate"
        ),
    }


def counts(ledger: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in ledger).items()))


def delimited_code_counts(
    ledger: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                code
                for row in ledger
                for code in row.get(field, "").split("|")
                if code
            ).items()
        )
    )


def write_outputs(
    *,
    output_dir: Path,
    gate_id: str,
    mode: str,
    backend: str,
    model: str,
    evidence_cases: list[CaseEvidence],
    ledger: list[dict[str, str]],
    metadata_rows: list[dict[str, object]],
    timing_rows: list[dict[str, object]],
    failed_rows: list[dict[str, str]],
    input_rows: list[dict[str, str]],
    input_hash: str,
    render_hash: str,
    started_at: str,
    elapsed: float,
    gate_mode: str = GATE1_MODE,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "auto_gabriel_adjudication_ledger.csv",
        GATE2_LEDGER_FIELDS if gate_mode == GATE2_MODE else LEDGER_FIELDS,
        ledger,
    )
    timing_fields = [
        "auto_adjudication_id",
        "calibration_id",
        "started_at",
        "finished_at",
        "local_evidence_elapsed_seconds",
        "gabriel_elapsed_seconds",
        "total_elapsed_seconds",
        "gabriel_status",
    ]
    write_csv(
        output_dir / "auto_gabriel_adjudication_timing.csv",
        timing_fields,
        timing_rows,
    )
    request_fields = [
        "auto_adjudication_id",
        "calibration_id",
        "gabriel_request_id",
        "gabriel_backend",
        "gabriel_model",
        "request_status",
        "prompt_sha256",
        "prompt_chars",
        "input_page_count",
        "input_text_chars",
        "prior_labels_in_prompt",
        "raw_prompt_saved",
        "raw_response_saved",
        "response_chars",
        "response_sha256",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "elapsed_seconds",
        "error_type",
        "error_message",
        "credential_value_saved",
        "authorization_header_saved",
    ]
    write_csv(
        output_dir / "auto_gabriel_adjudication_request_metadata.csv",
        request_fields,
        metadata_rows,
    )
    failed_path = output_dir / "auto_gabriel_adjudication_failed_cases.csv"
    if failed_rows:
        write_csv(
            failed_path,
            [
                "auto_adjudication_id",
                "calibration_id",
                "gabriel_status",
                "error_type",
                "error_message",
            ],
            failed_rows,
        )
    elif failed_path.exists():
        failed_path.unlink()
    decision = decision_metrics(ledger, input_rows, gate_mode=gate_mode)
    method = (
        "automated_local_visual_layout_navigation_offset_plus_"
        "gabriel_bounded_page_adjudication"
        if gate_mode == GATE2_MODE
        else "automated_local_visual_layout_plus_"
        "gabriel_bounded_page_adjudication"
    )
    decision.update(
        {
            "gate_id": gate_id,
            "method": method,
            "mode": mode,
            "gabriel_backend": backend,
            "gabriel_model": model,
            "generated_at": now_utc(),
        }
    )
    if gate_mode == GATE2_MODE:
        decision["gate_mode"] = gate_mode
    write_json(
        output_dir / "auto_gabriel_adjudication_gate_decision.json",
        decision,
    )
    summary = {
        "gate_id": gate_id,
        "status": (
            "dry_run_completed_no_gabriel_calls"
            if mode == "dry_run"
            else "preflight_passed"
            if mode == "preflight" and not failed_rows
            else "preflight_failed"
            if mode == "preflight"
            else "auto_gabriel_adjudication_completed"
        ),
        "method": method,
        "mode": mode,
        "started_at": started_at,
        "finished_at": now_utc(),
        "elapsed_seconds": round(elapsed, 6),
        "gabriel_backend": backend,
        "gabriel_model": model,
        "cases": len(ledger),
        "local_pages_evaluated": sum(len(case.pages) for case in evidence_cases),
        "bounded_text_chars_in_prompts": sum(
            case.text_chars for case in evidence_cases
        ),
        "rendered_pages_used": sum(
            page.rendered_available
            for case in evidence_cases
            for page in case.pages
        ),
        "gabriel_status_counts": counts(ledger, "gabriel_status"),
        "gabriel_schema_valid_counts": counts(
            ledger, "gabriel_schema_valid"
        ),
        "gabriel_wage_schedule_present_counts": counts(
            ledger, "gabriel_wage_schedule_present"
        ),
        "gabriel_candidate_page_relationship_counts": counts(
            ledger, "gabriel_candidate_page_relationship"
        ),
        "gabriel_visual_table_type_counts": counts(
            ledger, "gabriel_visual_table_type"
        ),
        "gabriel_non_wage_family_counts": counts(
            ledger, "gabriel_non_wage_family"
        ),
        "gabriel_extraction_complexity_counts": counts(
            ledger, "gabriel_extraction_complexity"
        ),
        "auto_gate_label_counts": counts(ledger, "auto_gate_label"),
        "auto_gate_confidence_counts": counts(
            ledger, "auto_gate_confidence"
        ),
        "failed_cases": len(failed_rows),
        "input_sha256_before_after": [input_hash, input_hash],
        "render_manifest_sha256_before_after": [render_hash, render_hash],
        "full_text_saved": False,
        "full_tables_saved": False,
        "structured_wage_values_saved": False,
        "urls_opened": 0,
        "hosted_search_calls": 0,
        "ocr_runs": 0,
        "wage_extraction_runs": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "decision": decision,
    }
    if gate_mode == GATE2_MODE:
        summary["gate_mode"] = gate_mode
        summary["gabriel_reason_code_counts"] = delimited_code_counts(
            ledger, "gabriel_reason_codes"
        )
        summary["auto_gate_reason_code_counts"] = delimited_code_counts(
            ledger, "auto_gate_reason_codes"
        )
        summary["gate2_diagnostic_reason_code_counts"] = (
            delimited_code_counts(ledger, "gate2_diagnostic_reason_codes")
        )
    write_json(
        output_dir / "auto_gabriel_adjudication_summary.json", summary
    )
    gate_mode_line = (
        f"Gate mode: `{gate_mode}`\n" if gate_mode == GATE2_MODE else ""
    )
    report = f"""# Automated visual + GABRIEL adjudication report

Gate: `{gate_id}`
Mode: `{mode}`
{gate_mode_line}Method: `{method}`

## Status

- Cases: {len(ledger)}
- Local bounded pages evaluated: {summary['local_pages_evaluated']}
- Capped text characters supplied: {summary['bounded_text_chars_in_prompts']}
- Rendered pages used for local features: {summary['rendered_pages_used']}
- GABRIEL backend: `{backend}`
- GABRIEL model: `{model}`
- Schema-valid responses: {decision['gabriel_schema_valid_count']} / {len(ledger)}
- Failed/schema-invalid cases: {len(failed_rows)}
- Auto-gate labels: `{json.dumps(summary['auto_gate_label_counts'], sort_keys=True)}`

## Decision

`{decision['extraction_decision']}`

- 500-document extraction allowed: `{str(decision['five_hundred_doc_extraction_allowed']).lower()}`
- Smaller extraction pilot allowed: `{str(decision['smaller_extraction_pilot_allowed']).lower()}`
- Original likely/p1 ready rate: {decision['original_likely_p1_ready_rate']:.2%}
- Wrong-page rate: {decision['wrong_page_rate']:.2%}
- GABRIEL schema-valid rate: {decision['gabriel_schema_valid_rate']:.2%}

## Boundary

No URL or hosted search was used. No PDF/page text, complete table, or
structured wage value was saved. OCR, wage extraction, ingestion, codification,
wage-gap analysis, and durable-ledger mutation did not occur.
"""
    (output_dir / "auto_gabriel_adjudication_report.md").write_text(
        report, encoding="utf-8"
    )
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blinded-input-csv", type=Path, required=True)
    parser.add_argument("--render-manifest-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gate-id", required=True)
    parser.add_argument(
        "--gate-mode", choices=sorted(GATE_MODES), default=GATE1_MODE
    )
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--candidate-page-window", type=int, default=1)
    parser.add_argument("--navigation-page-budget", type=int, default=4)
    parser.add_argument("--max-pages-per-case", type=int, default=6)
    parser.add_argument("--max-text-chars-per-page", type=int, default=1500)
    parser.add_argument("--max-text-chars-per-case", type=int, default=6000)
    parser.add_argument("--gabriel-backend", default=DEFAULT_BACKEND)
    parser.add_argument("--gabriel-model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-per-case", type=float, default=60.0)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--no-save-full-text", action="store_true", default=True)
    parser.add_argument("--allow-gabriel", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run and args.preflight_only:
        raise ValueError("--dry-run and --preflight-only are mutually exclusive")
    if not args.no_save_full_text:
        raise ValueError("full-text saving is prohibited")
    if args.max_cases is not None and not 1 <= args.max_cases <= 150:
        raise ValueError("--max-cases must be between 1 and 150")
    if args.candidate_page_window < 0:
        raise ValueError("candidate-page-window must be nonnegative")
    if not 0 <= args.navigation_page_budget <= 4:
        raise ValueError("navigation-page-budget must be between 0 and 4")
    if not 1 <= args.max_pages_per_case <= 6:
        raise ValueError("max-pages-per-case must be between 1 and 6")
    if not 1 <= args.max_text_chars_per_page <= 1500:
        raise ValueError("max-text-chars-per-page must be between 1 and 1500")
    if not 1 <= args.max_text_chars_per_case <= 6000:
        raise ValueError("max-text-chars-per-case must be between 1 and 6000")
    if args.timeout_per_case <= 0:
        raise ValueError("timeout-per-case must be positive")
    if args.parallel not in {1, 2}:
        raise ValueError("parallel must be 1 or 2")
    live = not args.dry_run
    if live and not args.allow_gabriel:
        raise ValueError("live GABRIEL calls require --allow-gabriel")

    started_at = now_utc()
    overall_started = time.monotonic()
    input_path = args.blinded_input_csv.resolve()
    render_path = args.render_manifest_csv.resolve()
    output_dir = args.output_dir.resolve()
    input_hash = sha256_file(input_path)
    render_hash = sha256_file(render_path)
    fields, all_rows = read_csv(input_path)
    validate_blinded_input(fields, all_rows)
    rows = all_rows[: args.max_cases] if args.max_cases else all_rows
    if args.preflight_only:
        rows = rows[:1]
    render_map = validate_render_manifest(render_path, all_rows)

    evidence_cases: list[CaseEvidence] = []
    local_elapsed: dict[str, float] = {}
    local_started_at: dict[str, str] = {}
    for source in rows:
        started = time.monotonic()
        local_started_at[source["calibration_id"]] = now_utc()
        evidence = build_case_evidence(
            source,
            gate_id=args.gate_id,
            render_map=render_map.get(source["adjudication_case_id"], {}),
            max_pages=args.max_pages_per_case,
            navigation_budget=args.navigation_page_budget,
            max_chars_per_page=args.max_text_chars_per_page,
            max_chars_per_case=args.max_text_chars_per_case,
            gate_mode=args.gate_mode,
            candidate_window=args.candidate_page_window,
        )
        local_elapsed[source["calibration_id"]] = time.monotonic() - started
        evidence_cases.append(evidence)

    key: str | None = None
    dotenv_location = "not_loaded"
    if live:
        key, dotenv_location = load_subscription_key()
        if not key:
            raise RuntimeError(
                "HARVARD_SUBSCRIPTION_KEY is unavailable; no GABRIEL call executed"
            )
        live_results = run_live_requests(
            evidence_cases,
            key=key,
            backend=args.gabriel_backend,
            model=args.gabriel_model,
            timeout=args.timeout_per_case,
            parallel=args.parallel,
        )
    else:
        live_results = [
            LiveResult(
                request_id="",
                status="not_called",
                response_text="",
                elapsed_seconds=0.0,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                error_type="",
                error_message="",
            )
            for _ in evidence_cases
        ]

    ledger: list[dict[str, str]] = []
    metadata_rows: list[dict[str, object]] = []
    timing_rows: list[dict[str, object]] = []
    failed_rows: list[dict[str, str]] = []
    for evidence, live_result in zip(evidence_cases, live_results):
        if live:
            gabriel, metadata, failed = gabriel_fields_from_result(
                evidence=evidence,
                result=live_result,
                backend=args.gabriel_backend,
                model=args.gabriel_model,
            )
        else:
            gabriel = empty_gabriel(
                backend=args.gabriel_backend,
                model=args.gabriel_model,
                status="not_called",
            )
            gabriel["gabriel_input_page_count"] = str(len(evidence.pages))
            gabriel["gabriel_input_text_chars"] = str(evidence.text_chars)
            metadata = {
                "auto_adjudication_id": evidence.auto_id,
                "calibration_id": evidence.source["calibration_id"],
                "gabriel_request_id": "",
                "gabriel_backend": args.gabriel_backend,
                "gabriel_model": args.gabriel_model,
                "request_status": "not_called",
                "prompt_sha256": sha256_bytes(
                    evidence.prompt.encode("utf-8")
                ),
                "prompt_chars": len(evidence.prompt),
                "input_page_count": len(evidence.pages),
                "input_text_chars": evidence.text_chars,
                "prior_labels_in_prompt": False,
                "raw_prompt_saved": False,
                "raw_response_saved": False,
                "response_chars": 0,
                "response_sha256": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "elapsed_seconds": 0.0,
                "error_type": "",
                "error_message": "",
                "credential_value_saved": False,
                "authorization_header_saved": False,
            }
            failed = None
        final = (
            combine_gate2(evidence, gabriel)
            if args.gate_mode == GATE2_MODE
            else combine_gate(evidence, gabriel)
        )
        row = {
            **identity_fields(evidence),
            **local_fields(evidence),
            **(
                gate2_fields(evidence)
                if args.gate_mode == GATE2_MODE
                else {}
            ),
            **gabriel,
            **final,
        }
        expected_fields = (
            GATE2_LEDGER_FIELDS
            if args.gate_mode == GATE2_MODE
            else LEDGER_FIELDS
        )
        if set(row) != set(expected_fields):
            raise AssertionError("ledger row field set mismatch")
        if row["auto_gate_label"] not in AUTO_GATE_LABELS:
            raise AssertionError("invalid final gate label")
        ledger.append(row)
        metadata["dotenv_location"] = dotenv_location
        metadata_rows.append(metadata)
        if failed:
            failed_rows.append(failed)
        total_elapsed = (
            local_elapsed[evidence.source["calibration_id"]]
            + live_result.elapsed_seconds
        )
        timing_rows.append(
            {
                "auto_adjudication_id": evidence.auto_id,
                "calibration_id": evidence.source["calibration_id"],
                "started_at": local_started_at[
                    evidence.source["calibration_id"]
                ],
                "finished_at": now_utc(),
                "local_evidence_elapsed_seconds": (
                    f"{local_elapsed[evidence.source['calibration_id']]:.6f}"
                ),
                "gabriel_elapsed_seconds": (
                    f"{live_result.elapsed_seconds:.6f}"
                ),
                "total_elapsed_seconds": f"{total_elapsed:.6f}",
                "gabriel_status": gabriel["gabriel_status"],
            }
        )

    # dotenv_location is intentionally not a request-metadata output field.
    for metadata in metadata_rows:
        metadata.pop("dotenv_location", None)
    input_hash_after = sha256_file(input_path)
    render_hash_after = sha256_file(render_path)
    if input_hash != input_hash_after or render_hash != render_hash_after:
        raise RuntimeError("immutable packet input changed during adjudication")
    summary = write_outputs(
        output_dir=output_dir,
        gate_id=args.gate_id,
        mode=(
            "dry_run"
            if args.dry_run
            else "preflight"
            if args.preflight_only
            else "live"
        ),
        backend=args.gabriel_backend,
        model=args.gabriel_model,
        evidence_cases=evidence_cases,
        ledger=ledger,
        metadata_rows=metadata_rows,
        timing_rows=timing_rows,
        failed_rows=failed_rows,
        input_rows=all_rows,
        input_hash=input_hash,
        render_hash=render_hash,
        started_at=started_at,
        elapsed=time.monotonic() - overall_started,
        gate_mode=args.gate_mode,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "cases": summary["cases"],
                "local_pages_evaluated": summary["local_pages_evaluated"],
                "gabriel_status_counts": summary["gabriel_status_counts"],
                "failed_cases": summary["failed_cases"],
                "output_dir": str(output_dir),
            },
            sort_keys=True,
        )
    )
    if args.preflight_only:
        return 0 if not failed_rows and all(
            row["gabriel_schema_valid"] == "true" for row in ledger
        ) else 2
    if live and failed_rows:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {safe_error(exc)}", file=sys.stderr)
        raise SystemExit(1)
