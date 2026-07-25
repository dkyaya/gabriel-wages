#!/usr/bin/env python3
"""Run bounded assisted local review of a prepared calibration packet.

The helper opens only artifact paths locked in the input calibration CSV,
verifies them against the durable text/table-detection ledger, inspects a
bounded candidate-page window, and writes controlled adjudication labels.
It has no network or OCR client and never saves page or document text.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pypdf import PdfReader

from text_table_detection_sources import (
    AGREEMENT_RE,
    ANNUAL_RE,
    BARGAINING_RE,
    COMPENSATION_RE,
    EFFECTIVE_RE,
    HOURLY_RE,
    MONEY_RE,
    PAY_SCHEDULE_RE,
    PERCENT_RE,
    RANK_POSITION_RE,
    SALARY_RE,
    STEP_GRADE_RE,
    WAGE_RE,
    YEAR_RE,
    analyze_page,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTHORITY = (
    ROOT
    / "docs/analysis/text_table_detection_ledgers"
    / "text_table_detection_ledger_cumulative.csv"
)
REVIEWER = "codex_assisted_local_review"
REVIEW_METHOD = "codex_assisted_local_adjudication"
REFINED_REVIEWER = "codex_refined_visual_gate_review"
REFINED_REVIEW_METHOD = "codex_refined_visual_table_gate_v1"
LEGACY_REVIEW_MODE = "legacy_assisted_local_v1"
REFINED_REVIEW_MODE = "refined_visual_gate_v1"
MAX_INTERNAL_PAGE_CHARS = 20_000

MANUAL_FIELDS = (
    "reviewer",
    "reviewed_at",
    "calibration_status",
    "page_hint_precision_label",
    "wage_table_present_label",
    "wage_table_page_match_label",
    "contract_period_present_label",
    "contract_period_hint_match_label",
    "table_layout_type",
    "extraction_complexity_label",
    "false_positive_family",
    "extraction_schema_notes",
    "recommended_extraction_action",
    "reviewer_confidence",
    "reviewer_notes",
)
AUDIT_FIELDS = (
    "review_id",
    "review_method",
    "review_status_detail",
    "artifact_exists_review",
    "artifact_hash_verified_review",
    "artifact_size_verified_review",
    "pdf_opened_review",
    "candidate_pages_requested",
    "candidate_pages_inspected",
    "adjacent_pages_inspected",
    "context_pages_inspected",
    "pages_inspected",
    "pages_with_text_review",
    "bounded_text_chars_inspected",
    "review_elapsed_seconds",
)
REFINED_FIELDS = (
    "wage_language_present_label",
    "pay_numeric_language_present_label",
    "visual_table_structure_label",
    "wage_schedule_table_confirmed_label",
    "candidate_page_relationship_label",
    "table_navigation_signal",
    "visual_confirmation_method",
    "extraction_gate_label",
    "extraction_gate_reason",
    "refined_review_mode",
    "navigation_pages_requested",
    "navigation_pages_inspected",
    "navigation_references_found",
    "rendered_pages_review",
    "rendered_page_count",
    "render_failures",
    "table_row_like_line_count",
    "table_column_evidence_count",
    "benefit_term_count",
    "wage_term_count_refined",
    "pay_numeric_token_count",
)
ALLOWED = {
    "calibration_status": {
        "not_reviewed",
        "reviewed",
        "needs_second_review",
        "exclude_from_calibration",
    },
    "page_hint_precision_label": {
        "correct",
        "partially_correct",
        "incorrect",
        "not_applicable",
        "unknown",
    },
    "wage_table_present_label": {"yes", "maybe", "no", "unknown"},
    "wage_table_page_match_label": {
        "exact",
        "nearby",
        "wrong_page",
        "no_wage_table",
        "unknown",
    },
    "contract_period_present_label": {"yes", "maybe", "no", "unknown"},
    "contract_period_hint_match_label": {
        "correct",
        "partially_correct",
        "incorrect",
        "no_period_found",
        "unknown",
    },
    "table_layout_type": {
        "step_grade",
        "rank_step",
        "classification_table",
        "hourly_schedule",
        "annual_salary_schedule",
        "percent_increase_schedule",
        "appendix_table",
        "prose_only",
        "no_wage_table",
        "other",
        "unknown",
    },
    "extraction_complexity_label": {
        "easy",
        "moderate",
        "hard",
        "not_extractable",
        "unknown",
    },
    "recommended_extraction_action": {
        "include_in_wage_extraction_pilot",
        "include_after_schema_update",
        "manual_review_only",
        "exclude_for_now",
        "OCR_later",
        "unknown",
    },
    "reviewer_confidence": {"high", "medium", "low", "unknown"},
    "wage_language_present_label": {"yes", "maybe", "no", "unknown"},
    "pay_numeric_language_present_label": {
        "yes",
        "maybe",
        "no",
        "unknown",
    },
    "visual_table_structure_label": {
        "confirmed_table",
        "possible_table",
        "prose_only",
        "index_or_contents",
        "benefits_table",
        "classification_only",
        "non_wage_table",
        "front_matter",
        "unknown",
    },
    "wage_schedule_table_confirmed_label": {
        "yes",
        "maybe",
        "no",
        "unknown",
    },
    "candidate_page_relationship_label": {
        "exact_table_page",
        "adjacent_to_table",
        "points_to_later_table",
        "wrong_page",
        "no_candidate_page",
        "unknown",
    },
    "table_navigation_signal": {
        "direct",
        "nearby",
        "index_or_contents",
        "appendix_reference",
        "none",
        "unknown",
    },
    "visual_confirmation_method": {
        "rendered_page",
        "text_structure_plus_rendered_check",
        "text_structure_only",
        "human_manual",
        "unknown",
    },
    "extraction_gate_label": {
        "pass_high_confidence",
        "pass_with_schema_update",
        "second_review_required",
        "fail_exclude",
        "unknown",
    },
}
SENSITIVE_ERROR = re.compile(
    r"(?i)(https?://|token|cookie|authorization|api[_-]?key|password)"
)
BENEFIT_RE = re.compile(
    r"\b(?:health|dental|insurance|pension|retirement|deductible|"
    r"premium contribution)\b",
    re.IGNORECASE,
)
INDEX_RE = re.compile(
    r"\b(?:table of contents|contents|index)\b", re.IGNORECASE
)
CLASSIFICATION_RE = re.compile(
    r"\b(?:classification|job title|position title|class title)\b",
    re.IGNORECASE,
)
INCREASE_RE = re.compile(
    r"\b(?:increase|adjustment|cost of living|cola)\b", re.IGNORECASE
)
APPENDIX_RE = re.compile(
    r"\b(?:appendix|schedule\s+[a-z])\b", re.IGNORECASE
)
FRONT_MATTER_RE = re.compile(
    r"\b(?:memorandum|recommendation|synopsis|transmittal|"
    r"agreement\s+between|execution copy)\b",
    re.IGNORECASE,
)
WAGE_LANGUAGE_RE = re.compile(
    r"\b(?:wage|wages|salary|salaries|pay\s+(?:rate|schedule|plan)|"
    r"compensation|hourly\s+rate|annual\s+salary|step\s+\d+|"
    r"grade\s+\d+)\b",
    re.IGNORECASE,
)
PAY_NUMERIC_RE = re.compile(
    r"(?<!\w)(?:\$\s*)?(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d{1,4})?%?(?!\w)"
)
TABLE_HEADER_RE = re.compile(
    r"\b(?:step|grade|range|rank|classification|class(?:ification)?|"
    r"position|hourly|annual|salary|wage|rate|effective)\b",
    re.IGNORECASE,
)
NAVIGATION_TARGET_RE = re.compile(
    r"\b(?:salary|wage|pay|compensation)\s+"
    r"(?:table|schedule|plan|appendix)|"
    r"\b(?:table|schedule|appendix)\s+[a-z]?\s*"
    r"(?:salary|wage|pay|compensation)\b",
    re.IGNORECASE,
)
PAGE_NUMBER_AT_END_RE = re.compile(r"\b(\d{1,4})\s*$")


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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
    path: Path, rows: list[dict[str, str]], fields: list[str]
) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def resolve_local_artifact(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def sanitize_error(exc: BaseException) -> str:
    message = re.sub(r"\s+", " ", str(exc)).strip()
    if SENSITIVE_ERROR.search(message):
        return "parser_error_details_redacted"
    message = re.sub(r"[/\\\\][^\s]+", "[path]", message)
    return (message or type(exc).__name__)[:200]


def parse_page_numbers(raw: str, page_count: int) -> list[int]:
    if not raw.strip():
        return []
    result: list[int] = []
    for token in raw.split(","):
        number = int(token.strip())
        if number < 1 or number > page_count:
            raise ValueError("candidate wage-page hint is out of bounds")
        if number not in result:
            result.append(number)
    return result


def bounded_page_plan(
    candidate_pages: list[int],
    page_count: int,
    window: int,
    maximum: int,
) -> tuple[list[int], set[int], set[int], set[int]]:
    if maximum < 1:
        raise ValueError("max pages per document must be positive")
    if window < 0:
        raise ValueError("candidate page window must be nonnegative")
    candidates: list[int] = []
    if candidate_pages:
        if len(candidate_pages) <= maximum:
            candidates = list(candidate_pages)
        else:
            positions = {
                round(index * (len(candidate_pages) - 1) / (maximum - 1))
                for index in range(maximum)
            } if maximum > 1 else {0}
            candidates = [
                candidate_pages[index] for index in sorted(positions)
            ][:maximum]
    adjacent: list[int] = []
    for candidate in candidates:
        for offset in range(1, window + 1):
            for number in (candidate - offset, candidate + offset):
                if (
                    1 <= number <= page_count
                    and number not in candidates
                    and number not in adjacent
                ):
                    adjacent.append(number)
    context = [number for number in (1, 2) if number <= page_count]
    ordered: list[int] = []
    for number in [*candidates, *adjacent, *context]:
        if number not in ordered:
            ordered.append(number)
        if len(ordered) == maximum:
            break
    if not ordered:
        ordered = list(range(1, min(page_count, maximum) + 1))
        context = list(ordered)
    selected = set(ordered)
    return (
        ordered,
        selected.intersection(candidates),
        selected.intersection(adjacent),
        selected.intersection(context),
    )


def validate_input(
    input_fields: list[str],
    rows: list[dict[str, str]],
    authority_rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    required = {
        "calibration_id",
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
        "content_artifact_path",
        "pdf_page_count",
        "text_layer_status",
        "candidate_wage_pages",
        "candidate_wage_page_count",
        "candidate_contract_period_text",
        "wage_table_signal",
        "contract_period_signal",
        "page_count_bin",
        *MANUAL_FIELDS,
    }
    missing = sorted(required - set(input_fields))
    if missing:
        raise ValueError(f"input CSV missing fields: {missing}")
    if not rows:
        raise ValueError("input CSV is empty")
    for identity in (
        "calibration_id",
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        values = [row[identity] for row in rows]
        if any(not value for value in values):
            raise ValueError(f"blank identity: {identity}")
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate identity: {identity}")
    for row in rows:
        if (
            row["calibration_status"] != "not_reviewed"
            or row["reviewer"]
            or row["reviewed_at"]
        ):
            raise ValueError("input calibration packet is not pristine")
        if any(
            row[field] != "unknown"
            for field in MANUAL_FIELDS
            if field
            not in {
                "reviewer",
                "reviewed_at",
                "calibration_status",
                "extraction_schema_notes",
                "reviewer_notes",
            }
        ):
            raise ValueError("input manual labels are not initialized")
    authority = {
        row["text_table_detection_id"]: row for row in authority_rows
    }
    for row in rows:
        durable = authority.get(row["text_table_detection_id"])
        if durable is None:
            raise ValueError("calibration identity absent from authority")
        for field in (
            "pdf_readiness_id",
            "source_review_id",
            "candidate_queue_row_id",
            "content_artifact_path",
            "pdf_page_count",
            "text_layer_status",
            "wage_table_signal",
            "candidate_wage_pages",
            "candidate_wage_page_count",
        ):
            if row[field] != durable[field]:
                raise ValueError(f"calibration/authority mismatch: {field}")
        if (
            not durable.get("content_hash")
            or int(durable.get("content_byte_size", "0")) <= 0
            or durable.get("content_type_observed") != "application/pdf"
        ):
            raise ValueError("authority lacks retained-PDF integrity fields")
    return authority


def initial_result(
    row: dict[str, str],
    input_fields: list[str],
    review_id: str,
    method: str,
    review_mode: str = LEGACY_REVIEW_MODE,
) -> dict[str, str]:
    reviewer = (
        REFINED_REVIEWER
        if review_mode == REFINED_REVIEW_MODE
        else REVIEWER
    )
    review_method = (
        REFINED_REVIEW_METHOD
        if review_mode == REFINED_REVIEW_MODE
        else REVIEW_METHOD
    )
    result = {field: row.get(field, "") for field in input_fields}
    result.update(
        {
            "reviewer": "" if method == "dry_run" else reviewer,
            "reviewed_at": "" if method == "dry_run" else now_utc(),
            "calibration_status": "not_reviewed",
            "page_hint_precision_label": "unknown",
            "wage_table_present_label": "unknown",
            "wage_table_page_match_label": "unknown",
            "contract_period_present_label": "unknown",
            "contract_period_hint_match_label": "unknown",
            "table_layout_type": "unknown",
            "extraction_complexity_label": "unknown",
            "false_positive_family": "unknown",
            "extraction_schema_notes": "",
            "recommended_extraction_action": "unknown",
            "reviewer_confidence": "unknown",
            "reviewer_notes": "",
            "review_id": review_id,
            "review_method": (
                f"planned_no_pdf_open_{review_mode}"
                if method == "dry_run"
                else review_method
            ),
            "review_status_detail": (
                "dry-run input validation only"
                if method == "dry_run"
                else ""
            ),
            "artifact_exists_review": "not_checked",
            "artifact_hash_verified_review": "not_checked",
            "artifact_size_verified_review": "not_checked",
            "pdf_opened_review": "0",
            "candidate_pages_requested": row["candidate_wage_pages"],
            "candidate_pages_inspected": "",
            "adjacent_pages_inspected": "",
            "context_pages_inspected": "",
            "pages_inspected": "",
            "pages_with_text_review": "0",
            "bounded_text_chars_inspected": "0",
            "review_elapsed_seconds": "0.000000",
            "wage_language_present_label": "unknown",
            "pay_numeric_language_present_label": "unknown",
            "visual_table_structure_label": "unknown",
            "wage_schedule_table_confirmed_label": "unknown",
            "candidate_page_relationship_label": "unknown",
            "table_navigation_signal": "unknown",
            "visual_confirmation_method": "unknown",
            "extraction_gate_label": "unknown",
            "extraction_gate_reason": "",
            "refined_review_mode": review_mode,
            "navigation_pages_requested": "",
            "navigation_pages_inspected": "",
            "navigation_references_found": "",
            "rendered_pages_review": "",
            "rendered_page_count": "0",
            "render_failures": "0",
            "table_row_like_line_count": "0",
            "table_column_evidence_count": "0",
            "benefit_term_count": "0",
            "wage_term_count_refined": "0",
            "pay_numeric_token_count": "0",
        }
    )
    return result


def wage_page_level(analysis: dict[str, object]) -> str:
    wage_terms = int(analysis["wage_terms"])
    numeric = int(analysis["numeric_tokens"])
    money = int(analysis["money_tokens"])
    table = str(analysis["table_signal"])
    if (
        wage_terms >= 2
        and table == "likely"
        and (money >= 2 or numeric >= 12)
    ):
        return "strong"
    if (
        wage_terms >= 1
        and table in {"likely", "possible"}
        and (money >= 1 or numeric >= 6)
    ):
        return "possible"
    return "none"


def layout_from_text(text: str, wage_presence: str) -> str:
    if wage_presence == "no":
        return "no_wage_table"
    if STEP_GRADE_RE.search(text) and re.search(
        r"\b(?:grade|range)\b", text, re.IGNORECASE
    ):
        return "step_grade"
    if STEP_GRADE_RE.search(text) and RANK_POSITION_RE.search(text):
        return "rank_step"
    if CLASSIFICATION_RE.search(text):
        return "classification_table"
    if HOURLY_RE.search(text):
        return "hourly_schedule"
    if ANNUAL_RE.search(text) or SALARY_RE.search(text):
        return "annual_salary_schedule"
    if PERCENT_RE.search(text) and INCREASE_RE.search(text):
        return "percent_increase_schedule"
    if APPENDIX_RE.search(text):
        return "appendix_table"
    if wage_presence == "maybe":
        return "prose_only"
    return "other"


def false_positive_from_text(
    text: str, wage_presence: str, table_layout: str
) -> str:
    if wage_presence == "yes":
        return "not_applicable"
    if BENEFIT_RE.search(text):
        return "benefit_table"
    if INDEX_RE.search(text):
        return "index_or_contents"
    if PERCENT_RE.search(text) and not MONEY_RE.search(text):
        return "percentage_prose"
    if CLASSIFICATION_RE.search(text) and not MONEY_RE.search(text):
        return "classification_without_pay"
    if APPENDIX_RE.search(text):
        return "numeric_appendix"
    if table_layout == "prose_only":
        return "non_wage_schedule"
    return "other:bounded_signal_without_confirmed_table"


def compare_contract_hint(
    inherited_hint: str, text: str
) -> tuple[str, str]:
    years_text = set(YEAR_RE.findall(text))
    period_context = bool(
        (AGREEMENT_RE.search(text) or EFFECTIVE_RE.search(text))
        and years_text
    )
    if period_context and len(years_text) >= 2:
        present = "yes"
    elif period_context or len(years_text) >= 2:
        present = "maybe"
    else:
        return "no", "no_period_found"
    hint_years = set(YEAR_RE.findall(inherited_hint))
    if not inherited_hint.strip():
        return present, "unknown"
    if hint_years and hint_years.issubset(years_text):
        return present, "correct"
    if hint_years.intersection(years_text):
        return present, "partially_correct"
    if not hint_years and (
        AGREEMENT_RE.search(inherited_hint)
        or EFFECTIVE_RE.search(inherited_hint)
    ):
        return present, "partially_correct"
    return present, "incorrect"


def bounded_refined_page_plan(
    candidate_pages: list[int],
    page_count: int,
    window: int,
    maximum: int,
) -> tuple[list[int], set[int], set[int], set[int]]:
    """Reserve context pages before sampling candidates and neighbors."""

    if maximum < 1:
        raise ValueError("max pages per document must be positive")
    if window < 0:
        raise ValueError("candidate page window must be nonnegative")
    context = [number for number in (1, 2) if number <= page_count]
    ordered = list(context[:maximum])
    remaining = maximum - len(ordered)
    candidates: list[int] = []
    if candidate_pages and remaining:
        if len(candidate_pages) <= remaining:
            candidates = list(candidate_pages)
        else:
            positions = (
                {
                    round(
                        index
                        * (len(candidate_pages) - 1)
                        / (remaining - 1)
                    )
                    for index in range(remaining)
                }
                if remaining > 1
                else {0}
            )
            candidates = [
                candidate_pages[index] for index in sorted(positions)
            ][:remaining]
    for number in candidates:
        if number not in ordered and len(ordered) < maximum:
            ordered.append(number)
    adjacent: list[int] = []
    for candidate in candidates:
        for offset in range(1, window + 1):
            for number in (candidate - offset, candidate + offset):
                if (
                    1 <= number <= page_count
                    and number not in ordered
                    and number not in adjacent
                ):
                    adjacent.append(number)
    for number in adjacent:
        if len(ordered) == maximum:
            break
        ordered.append(number)
    if not ordered:
        ordered = list(range(1, min(page_count, maximum) + 1))
        context = list(ordered)
    selected = set(ordered)
    return (
        ordered,
        selected.intersection(candidates),
        selected.intersection(adjacent),
        selected.intersection(context),
    )


def find_navigation_references(
    page_text: dict[int, str],
    *,
    page_count: int,
) -> tuple[list[int], str]:
    """Find bounded contents/appendix page references without following URLs."""

    references: list[int] = []
    signal = "none"
    for text in page_text.values():
        is_index = bool(INDEX_RE.search(text))
        for line in text.splitlines():
            bounded = re.sub(r"\s+", " ", line).strip()[:240]
            if not bounded or not NAVIGATION_TARGET_RE.search(bounded):
                continue
            if APPENDIX_RE.search(bounded):
                signal = "appendix_reference"
            elif is_index and signal == "none":
                signal = "index_or_contents"
            match = PAGE_NUMBER_AT_END_RE.search(bounded)
            if match:
                number = int(match.group(1))
                if 1 <= number <= page_count and number not in references:
                    references.append(number)
    return references, signal


def bounded_navigation_plan(
    references: list[int],
    *,
    page_count: int,
    budget: int,
    already_selected: set[int],
) -> list[int]:
    if budget < 0:
        raise ValueError("navigation page budget must be nonnegative")
    plan: list[int] = []
    for reference in references:
        for number in (reference, reference - 1, reference + 1):
            if (
                1 <= number <= page_count
                and number not in already_selected
                and number not in plan
            ):
                plan.append(number)
            if len(plan) == budget:
                return plan
    return plan


def refined_page_features(text: str) -> dict[str, object]:
    """Derive conservative language and row/column signals from bounded text."""

    lines = [
        re.sub(r"\s+$", "", line)
        for line in text.splitlines()
        if line.strip()
    ]
    wage_terms = len(WAGE_LANGUAGE_RE.findall(text))
    benefit_terms = len(BENEFIT_RE.findall(text))
    pay_numeric_tokens = len(PAY_NUMERIC_RE.findall(text))
    row_like = 0
    column_evidence = 0
    header_lines = 0
    for line in lines:
        numeric = PAY_NUMERIC_RE.findall(line)
        columns = [
            value
            for value in re.split(r"\s{2,}|\t+", line.strip())
            if value
        ]
        words = re.findall(r"[A-Za-z][A-Za-z/-]*", line)
        if TABLE_HEADER_RE.search(line):
            header_lines += 1
        compact_row = (
            len(numeric) >= 3
            and len(words) <= 20
            and len(line) <= 180
            and not line.rstrip().endswith((".", ";"))
        )
        aligned_row = (
            len(numeric) >= 2
            and len(columns) >= 3
            and bool(words)
            and len(line) <= 220
        )
        if compact_row or aligned_row:
            row_like += 1
        if len(columns) >= 3 and len(words) >= 2:
            column_evidence += 1
    index_page = bool(INDEX_RE.search(text))
    front_matter = bool(FRONT_MATTER_RE.search("\n".join(lines[:12])))
    classification = bool(CLASSIFICATION_RE.search(text))
    wage_language = (
        "yes" if wage_terms >= 2 else "maybe" if wage_terms == 1 else "no"
    )
    if wage_terms and pay_numeric_tokens >= 2:
        pay_numeric = "yes"
    elif wage_terms and pay_numeric_tokens == 1:
        pay_numeric = "maybe"
    else:
        pay_numeric = "no"

    confirmed = (
        wage_terms >= 1
        and pay_numeric_tokens >= 2
        and row_like >= 2
        and (column_evidence >= 1 or header_lines >= 1)
    )
    possible = (
        wage_terms >= 1
        and pay_numeric_tokens >= 1
        and row_like >= 1
        and header_lines >= 1
    )
    benefit_dominant = (
        benefit_terms >= 2
        and benefit_terms > wage_terms
        and row_like >= 1
    )
    if index_page:
        structure = "index_or_contents"
    elif benefit_dominant:
        structure = "benefits_table"
    elif confirmed:
        structure = "confirmed_table"
    elif possible:
        structure = "possible_table"
    elif (
        classification
        and pay_numeric == "no"
        and (row_like or column_evidence >= 2)
    ):
        structure = "classification_only"
    elif row_like:
        structure = "non_wage_table"
    elif front_matter and row_like == 0:
        structure = "front_matter"
    elif wage_language in {"yes", "maybe"}:
        structure = "prose_only"
    else:
        structure = "unknown"
    wage_schedule = (
        "yes"
        if structure == "confirmed_table" and pay_numeric == "yes"
        else "maybe"
        if structure == "possible_table"
        else "no"
    )
    return {
        "wage_language": wage_language,
        "pay_numeric_language": pay_numeric,
        "structure": structure,
        "wage_schedule": wage_schedule,
        "row_like_lines": row_like,
        "column_evidence": column_evidence,
        "benefit_terms": benefit_terms,
        "wage_terms": wage_terms,
        "pay_numeric_tokens": pay_numeric_tokens,
    }


def render_pdf_page(
    artifact: Path,
    page_number: int,
    output_prefix: Path,
) -> bool:
    """Render one page locally; output is temporary and never retained."""

    command = [
        "pdftoppm",
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-singlefile",
        "-r",
        "96",
        "-png",
        str(artifact),
        str(output_prefix),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    rendered = output_prefix.with_suffix(".png")
    return (
        completed.returncode == 0
        and rendered.is_file()
        and rendered.stat().st_size > 100
    )


def refined_layout_from_text(
    text: str,
    structure: str,
) -> str:
    if structure not in {"confirmed_table", "possible_table"}:
        if structure == "prose_only":
            return "prose_only"
        if structure in {
            "benefits_table",
            "classification_only",
            "non_wage_table",
            "front_matter",
            "index_or_contents",
        }:
            return "no_wage_table"
        return "unknown"
    if STEP_GRADE_RE.search(text) and re.search(
        r"\b(?:grade|range)\b", text, re.IGNORECASE
    ):
        return "step_grade"
    if STEP_GRADE_RE.search(text) and RANK_POSITION_RE.search(text):
        return "rank_step"
    if CLASSIFICATION_RE.search(text):
        return "classification_table"
    if HOURLY_RE.search(text):
        return "hourly_schedule"
    if ANNUAL_RE.search(text) or SALARY_RE.search(text):
        return "annual_salary_schedule"
    if PERCENT_RE.search(text) and INCREASE_RE.search(text):
        return "percent_increase_schedule"
    if APPENDIX_RE.search(text):
        return "appendix_table"
    return "other"


def adjudicate(
    result: dict[str, str],
    page_text: dict[int, str],
    page_analyses: dict[int, dict[str, object]],
    requested: list[int],
    candidate_selected: set[int],
    adjacent_selected: set[int],
    authority: dict[str, str],
) -> None:
    levels = {
        number: wage_page_level(analysis)
        for number, analysis in page_analyses.items()
    }
    exact_levels = [
        levels.get(number, "none") for number in candidate_selected
    ]
    adjacent_levels = [
        levels.get(number, "none") for number in adjacent_selected
    ]
    exact_useful = sum(level in {"strong", "possible"} for level in exact_levels)
    exact_strong = sum(level == "strong" for level in exact_levels)
    adjacent_useful = sum(
        level in {"strong", "possible"} for level in adjacent_levels
    )
    any_strong = any(level == "strong" for level in levels.values())
    any_possible = any(
        level in {"strong", "possible"} for level in levels.values()
    )
    if requested:
        if exact_useful == len(exact_levels) and exact_useful:
            page_precision = "correct"
        elif exact_useful:
            page_precision = "partially_correct"
        else:
            page_precision = "incorrect"
    else:
        page_precision = "not_applicable"
    if any_strong:
        wage_presence = "yes"
    elif any_possible:
        wage_presence = "maybe"
    else:
        wage_presence = "no"
    if exact_useful:
        page_match = "exact"
    elif adjacent_useful:
        page_match = "nearby"
    elif wage_presence in {"yes", "maybe"}:
        page_match = "wrong_page"
    else:
        page_match = "no_wage_table"

    combined_text = "\n".join(page_text.values())
    contract_present, contract_match = compare_contract_hint(
        result["candidate_contract_period_text"], combined_text
    )
    layout = layout_from_text(combined_text, wage_presence)
    false_positive = false_positive_from_text(
        combined_text, wage_presence, layout
    )
    partial_text = result["text_layer_status"] == "partial"
    incomplete_candidate_review = len(candidate_selected) < len(requested)
    if wage_presence == "no":
        complexity = "not_extractable"
    elif (
        wage_presence == "yes"
        and page_match == "exact"
        and not partial_text
        and not incomplete_candidate_review
        and len(page_text) <= 3
    ):
        complexity = "easy"
    elif (
        wage_presence == "yes"
        and page_match in {"exact", "nearby"}
        and not partial_text
    ):
        complexity = "moderate"
    else:
        complexity = "hard"

    if (
        wage_presence == "yes"
        and page_precision in {"correct", "partially_correct"}
        and complexity in {"easy", "moderate"}
    ):
        action = "include_in_wage_extraction_pilot"
    elif wage_presence == "yes":
        action = "include_after_schema_update"
    elif wage_presence == "maybe":
        action = "manual_review_only"
    else:
        action = "exclude_for_now"

    if (
        wage_presence == "yes"
        and page_match == "exact"
        and contract_match in {"correct", "partially_correct"}
        and not incomplete_candidate_review
    ):
        confidence = "high"
    elif wage_presence in {"yes", "maybe"} and page_match in {
        "exact",
        "nearby",
        "wrong_page",
    }:
        confidence = "medium"
    else:
        confidence = "low"

    if confidence == "low" or incomplete_candidate_review:
        status = "needs_second_review"
    else:
        status = "reviewed"
    schema_note = {
        "step_grade": "preserve step and grade/range headers",
        "rank_step": "preserve rank, step, and effective-date columns",
        "classification_table": "normalize classification labels before QA",
        "hourly_schedule": "retain rate basis and effective-date columns",
        "annual_salary_schedule": "retain annual basis and schedule dates",
        "percent_increase_schedule": "separate percent terms from rate tables",
        "appendix_table": "link appendix label and continuation pages",
        "prose_only": "requires manual structure review before extraction",
        "no_wage_table": "no extraction schema proposed",
        "other": "manual schema mapping required",
    }[layout]
    structural_note = (
        f"Assisted review inspected {len(page_text)} bounded pages; "
        f"{exact_strong} strong exact-hint pages and {adjacent_useful} useful "
        "adjacent pages. No page text or wage values retained."
    )[:300]
    result.update(
        {
            "calibration_status": status,
            "page_hint_precision_label": page_precision,
            "wage_table_present_label": wage_presence,
            "wage_table_page_match_label": page_match,
            "contract_period_present_label": contract_present,
            "contract_period_hint_match_label": contract_match,
            "table_layout_type": layout,
            "extraction_complexity_label": complexity,
            "false_positive_family": false_positive,
            "extraction_schema_notes": schema_note[:300],
            "recommended_extraction_action": action,
            "reviewer_confidence": confidence,
            "reviewer_notes": structural_note,
            "review_status_detail": (
                "bounded assisted local adjudication completed; "
                "human validation remains recommended"
            ),
        }
    )


def refined_adjudicate(
    result: dict[str, str],
    *,
    page_text: dict[int, str],
    page_features: dict[int, dict[str, object]],
    requested: list[int],
    candidate_selected: set[int],
    adjacent_selected: set[int],
    navigation_references: list[int],
    navigation_pages: set[int],
    navigation_signal: str,
    rendered_pages: set[int],
    require_visual_table_confirmation: bool,
) -> None:
    """Apply the conservative visual/table gate without extracting cells."""

    confirmed_pages = {
        number
        for number, features in page_features.items()
        if features["structure"] == "confirmed_table"
        and features["wage_schedule"] == "yes"
    }
    possible_pages = {
        number
        for number, features in page_features.items()
        if features["structure"] == "possible_table"
    }
    qualifying_pages = confirmed_pages | possible_pages
    exact_pages = qualifying_pages.intersection(candidate_selected)
    nearby_pages = qualifying_pages.intersection(adjacent_selected)
    navigated_table_pages = qualifying_pages.intersection(navigation_pages)

    if exact_pages:
        relationship = "exact_table_page"
        effective_navigation = "direct"
    elif nearby_pages:
        relationship = "adjacent_to_table"
        effective_navigation = "nearby"
    elif navigation_references:
        relationship = "points_to_later_table"
        effective_navigation = (
            navigation_signal
            if navigation_signal in {
                "index_or_contents",
                "appendix_reference",
            }
            else "index_or_contents"
        )
    elif requested:
        relationship = "wrong_page"
        effective_navigation = "none"
    else:
        relationship = "no_candidate_page"
        effective_navigation = "none"

    structures = [
        str(features["structure"]) for features in page_features.values()
    ]
    if confirmed_pages:
        structure = "confirmed_table"
    elif possible_pages:
        structure = "possible_table"
    else:
        structure = next(
            (
                value
                for value in (
                    "index_or_contents",
                    "benefits_table",
                    "classification_only",
                    "non_wage_table",
                    "front_matter",
                    "prose_only",
                )
                if value in structures
            ),
            "unknown",
        )

    wage_labels = {
        str(features["wage_language"]) for features in page_features.values()
    }
    pay_numeric_labels = {
        str(features["pay_numeric_language"])
        for features in page_features.values()
    }
    wage_language = (
        "yes"
        if "yes" in wage_labels
        else "maybe"
        if "maybe" in wage_labels
        else "no"
    )
    pay_numeric = (
        "yes"
        if "yes" in pay_numeric_labels
        else "maybe"
        if "maybe" in pay_numeric_labels
        else "no"
    )
    if confirmed_pages:
        wage_schedule = "yes"
    elif possible_pages or navigation_references:
        wage_schedule = "maybe"
    else:
        wage_schedule = "no"

    rendered_relevant = qualifying_pages.intersection(rendered_pages)
    visual_method = (
        "text_structure_plus_rendered_check"
        if rendered_pages
        else "text_structure_only"
    )
    visual_gate_met = (
        not require_visual_table_confirmation or bool(rendered_relevant)
    )

    if (
        confirmed_pages
        and relationship in {
            "exact_table_page",
            "adjacent_to_table",
            "points_to_later_table",
        }
        and visual_gate_met
    ):
        gate = "pass_high_confidence"
        gate_reason = (
            "Confirmed repeated wage/pay rows and columns on a bounded "
            "candidate-related page with the configured render check."
        )
    elif (
        possible_pages
        and relationship in {"exact_table_page", "adjacent_to_table"}
        and visual_gate_met
    ):
        gate = "pass_with_schema_update"
        gate_reason = (
            "Possible wage table has bounded row/column evidence but needs "
            "schema or layout adjudication."
        )
    elif relationship == "points_to_later_table":
        gate = "second_review_required"
        gate_reason = (
            "Contents/index/appendix language points to a later wage table; "
            "the reference requires independent confirmation."
        )
    elif wage_language in {"yes", "maybe"} and structure in {
        "prose_only",
        "front_matter",
        "index_or_contents",
        "possible_table",
    }:
        gate = "second_review_required"
        gate_reason = (
            "Wage/pay language is present without a visually gated confirmed "
            "table."
        )
    elif confirmed_pages and not visual_gate_met:
        gate = "second_review_required"
        gate_reason = (
            "Strong text-structure evidence exists, but the required bounded "
            "render confirmation is unavailable."
        )
    elif structure in {
        "benefits_table",
        "classification_only",
        "non_wage_table",
        "front_matter",
    }:
        gate = "fail_exclude"
        gate_reason = (
            "Bounded evidence is benefits/non-wage/classification/front "
            "matter rather than a usable wage schedule."
        )
    else:
        gate = "fail_exclude"
        gate_reason = "No bounded wage-table structure was confirmed."

    if relationship == "exact_table_page":
        page_precision = "correct"
        page_match = "exact"
    elif relationship in {"adjacent_to_table", "points_to_later_table"}:
        page_precision = "partially_correct"
        page_match = "nearby"
    elif relationship == "wrong_page":
        page_precision = "incorrect"
        page_match = (
            "no_wage_table" if wage_schedule == "no" else "wrong_page"
        )
    elif relationship == "no_candidate_page":
        page_precision = "not_applicable"
        page_match = (
            "no_wage_table" if wage_schedule == "no" else "wrong_page"
        )
    else:
        page_precision = "unknown"
        page_match = "unknown"

    if wage_schedule == "yes":
        wage_presence = "yes"
    elif wage_schedule == "maybe":
        wage_presence = "maybe"
    else:
        wage_presence = "no"
    combined_text = "\n".join(page_text.values())
    contract_present, contract_match = compare_contract_hint(
        result["candidate_contract_period_text"], combined_text
    )
    layout = refined_layout_from_text(combined_text, structure)
    false_positive = {
        "benefits_table": "benefit_table",
        "classification_only": "classification_without_pay",
        "index_or_contents": "index_or_contents",
        "non_wage_table": "non_wage_schedule",
        "front_matter": "other:bounded_signal_without_confirmed_table",
        "prose_only": "other:bounded_signal_without_confirmed_table",
    }.get(structure, "not_applicable")
    if gate == "pass_high_confidence":
        complexity = "easy" if len(qualifying_pages) == 1 else "moderate"
        action = "include_in_wage_extraction_pilot"
        confidence = "high"
        status = "reviewed"
    elif gate == "pass_with_schema_update":
        complexity = "hard"
        action = "include_after_schema_update"
        confidence = "medium"
        status = "reviewed"
    elif gate == "second_review_required":
        complexity = "hard"
        action = "manual_review_only"
        confidence = "low"
        status = "needs_second_review"
    else:
        complexity = "not_extractable"
        action = "exclude_for_now"
        confidence = "medium" if structure != "unknown" else "low"
        status = "reviewed" if structure != "unknown" else "needs_second_review"

    row_like = sum(
        int(features["row_like_lines"]) for features in page_features.values()
    )
    columns = sum(
        int(features["column_evidence"]) for features in page_features.values()
    )
    benefit_terms = sum(
        int(features["benefit_terms"]) for features in page_features.values()
    )
    wage_terms = sum(
        int(features["wage_terms"]) for features in page_features.values()
    )
    pay_tokens = sum(
        int(features["pay_numeric_tokens"])
        for features in page_features.values()
    )
    result.update(
        {
            "calibration_status": status,
            "page_hint_precision_label": page_precision,
            "wage_table_present_label": wage_presence,
            "wage_table_page_match_label": page_match,
            "contract_period_present_label": contract_present,
            "contract_period_hint_match_label": contract_match,
            "table_layout_type": layout,
            "extraction_complexity_label": complexity,
            "false_positive_family": false_positive,
            "extraction_schema_notes": (
                "Preserve page/table identity and require independently "
                "confirmed row/column headers before extraction."
            ),
            "recommended_extraction_action": action,
            "reviewer_confidence": confidence,
            "reviewer_notes": (
                f"Refined bounded gate inspected {len(page_text)} pages; "
                f"row-like lines={row_like}; column evidence={columns}; "
                "no page text, table cells, or wage values retained."
            ),
            "review_status_detail": (
                "refined visual/table gate completed; this remains assisted "
                "and requires independent calibration"
            ),
            "wage_language_present_label": wage_language,
            "pay_numeric_language_present_label": pay_numeric,
            "visual_table_structure_label": structure,
            "wage_schedule_table_confirmed_label": wage_schedule,
            "candidate_page_relationship_label": relationship,
            "table_navigation_signal": effective_navigation,
            "visual_confirmation_method": visual_method,
            "extraction_gate_label": gate,
            "extraction_gate_reason": gate_reason,
            "table_row_like_line_count": str(row_like),
            "table_column_evidence_count": str(columns),
            "benefit_term_count": str(benefit_terms),
            "wage_term_count_refined": str(wage_terms),
            "pay_numeric_token_count": str(pay_tokens),
        }
    )


def review_row(
    row: dict[str, str],
    *,
    input_fields: list[str],
    review_id: str,
    authority: dict[str, str],
    candidate_page_window: int,
    max_pages_per_document: int,
    max_snippet_chars: int,
    review_mode: str = LEGACY_REVIEW_MODE,
    render_pages: bool = False,
    max_rendered_pages_per_document: int = 3,
    navigation_page_budget: int = 4,
    require_visual_table_confirmation: bool = True,
    reader_factory: Callable[..., object] = PdfReader,
) -> dict[str, str]:
    result = initial_result(
        row,
        input_fields,
        review_id,
        "local",
        review_mode,
    )
    started = time.monotonic()
    artifact = resolve_local_artifact(row["content_artifact_path"])
    if not artifact.is_file():
        result.update(
            {
                "calibration_status": "needs_second_review",
                "review_status_detail": "retained artifact is missing",
                "artifact_exists_review": "0",
                "artifact_hash_verified_review": "0",
                "artifact_size_verified_review": "0",
                "recommended_extraction_action": "manual_review_only",
                "reviewer_confidence": "low",
                "reviewer_notes": "Artifact missing; no PDF opened.",
                "extraction_gate_label": "second_review_required",
                "extraction_gate_reason": (
                    "Retained artifact is missing; no review was possible."
                ),
            }
        )
        result["review_elapsed_seconds"] = (
            f"{time.monotonic() - started:.6f}"
        )
        return result
    result["artifact_exists_review"] = "1"
    actual_size = artifact.stat().st_size
    actual_hash = sha256_file(artifact)
    expected_hash = authority["content_hash"]
    expected_size = int(authority["content_byte_size"])
    result["artifact_hash_verified_review"] = (
        "1" if actual_hash == expected_hash else "0"
    )
    result["artifact_size_verified_review"] = (
        "1" if actual_size == expected_size else "0"
    )
    if actual_hash != expected_hash or actual_size != expected_size:
        result.update(
            {
                "calibration_status": "needs_second_review",
                "review_status_detail": (
                    "artifact hash or byte size differs from durable authority"
                ),
                "recommended_extraction_action": "manual_review_only",
                "reviewer_confidence": "low",
                "reviewer_notes": (
                    "Integrity mismatch; PDF content was not opened."
                ),
                "extraction_gate_label": "second_review_required",
                "extraction_gate_reason": (
                    "Artifact integrity differs from the durable authority."
                ),
            }
        )
        result["review_elapsed_seconds"] = (
            f"{time.monotonic() - started:.6f}"
        )
        return result
    try:
        reader = reader_factory(artifact, strict=False)
        pages = getattr(reader, "pages")
        page_count = len(pages)
        if page_count != int(row["pdf_page_count"]):
            raise ValueError("page count differs from durable authority")
        requested = parse_page_numbers(
            row["candidate_wage_pages"], page_count
        )
        if review_mode == REFINED_REVIEW_MODE:
            plan, candidates, adjacent, context = (
                bounded_refined_page_plan(
                    requested,
                    page_count,
                    candidate_page_window,
                    max_pages_per_document,
                )
            )
        else:
            plan, candidates, adjacent, context = bounded_page_plan(
                requested,
                page_count,
                candidate_page_window,
                max_pages_per_document,
            )
        result.update(
            {
                "pdf_opened_review": "1",
                "candidate_pages_inspected": ",".join(
                    map(str, sorted(candidates))
                ),
                "adjacent_pages_inspected": ",".join(
                    map(str, sorted(adjacent))
                ),
                "context_pages_inspected": ",".join(
                    map(str, sorted(context))
                ),
                "pages_inspected": ",".join(map(str, plan)),
            }
        )
        page_text: dict[int, str] = {}
        analyses: dict[int, dict[str, object]] = {}
        chars = 0
        for number in plan:
            extracted = pages[number - 1].extract_text() or ""
            bounded = extracted[:MAX_INTERNAL_PAGE_CHARS]
            del extracted
            if bounded.strip():
                page_text[number] = bounded
                analyses[number] = analyze_page(bounded)
                chars += len(bounded)
            del bounded
        navigation_references: list[int] = []
        navigation_signal = "none"
        navigation_plan: list[int] = []
        if review_mode == REFINED_REVIEW_MODE:
            navigation_references, navigation_signal = (
                find_navigation_references(
                    page_text,
                    page_count=page_count,
                )
            )
            navigation_plan = bounded_navigation_plan(
                navigation_references,
                page_count=page_count,
                budget=navigation_page_budget,
                already_selected=set(plan),
            )
            for number in navigation_plan:
                extracted = pages[number - 1].extract_text() or ""
                bounded = extracted[:MAX_INTERNAL_PAGE_CHARS]
                del extracted
                if bounded.strip():
                    page_text[number] = bounded
                    analyses[number] = analyze_page(bounded)
                    chars += len(bounded)
                del bounded
            if navigation_plan:
                plan.extend(navigation_plan)
            result.update(
                {
                    "navigation_pages_requested": ",".join(
                        map(str, navigation_references)
                    ),
                    "navigation_pages_inspected": ",".join(
                        map(str, navigation_plan)
                    ),
                    "navigation_references_found": ",".join(
                        map(str, navigation_references)
                    ),
                    "pages_inspected": ",".join(map(str, plan)),
                }
            )
        result["pages_with_text_review"] = str(len(page_text))
        result["bounded_text_chars_inspected"] = str(chars)
        if not page_text:
            result.update(
                {
                    "calibration_status": "needs_second_review",
                    "review_status_detail": (
                        "bounded pages yielded no text; OCR was not run"
                    ),
                    "wage_table_present_label": "unknown",
                    "page_hint_precision_label": "unknown",
                    "wage_table_page_match_label": "unknown",
                    "contract_period_present_label": "unknown",
                    "contract_period_hint_match_label": "unknown",
                    "table_layout_type": "unknown",
                    "extraction_complexity_label": "hard",
                    "false_positive_family": "unknown",
                    "recommended_extraction_action": "manual_review_only",
                    "reviewer_confidence": "low",
                    "reviewer_notes": (
                        "No text on bounded reviewed pages; no OCR run."
                    ),
                    "extraction_gate_label": "second_review_required",
                    "extraction_gate_reason": (
                        "Bounded reviewed pages returned no text; OCR was not "
                        "run."
                    ),
                    "visual_confirmation_method": (
                        "text_structure_only"
                        if review_mode == REFINED_REVIEW_MODE
                        else "unknown"
                    ),
                }
            )
        elif review_mode == REFINED_REVIEW_MODE:
            features = {
                number: refined_page_features(text)
                for number, text in page_text.items()
            }
            qualifying = [
                number
                for number, values in features.items()
                if values["structure"]
                in {"confirmed_table", "possible_table"}
            ]
            render_candidates = [
                *qualifying,
                *[number for number in plan if number not in qualifying],
            ][:max_rendered_pages_per_document]
            rendered_pages: set[int] = set()
            render_failures = 0
            if render_pages and render_candidates:
                scratch_root = ROOT / "tmp"
                scratch_root.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(
                    prefix="text_table_refined_render_",
                    dir=scratch_root,
                ) as temporary:
                    temporary_path = Path(temporary)
                    for number in render_candidates:
                        try:
                            if render_pdf_page(
                                artifact,
                                number,
                                temporary_path / f"page_{number}",
                            ):
                                rendered_pages.add(number)
                            else:
                                render_failures += 1
                        except Exception:
                            render_failures += 1
            result.update(
                {
                    "rendered_pages_review": ",".join(
                        map(str, sorted(rendered_pages))
                    ),
                    "rendered_page_count": str(len(rendered_pages)),
                    "render_failures": str(render_failures),
                }
            )
            refined_adjudicate(
                result,
                page_text=page_text,
                page_features=features,
                requested=requested,
                candidate_selected=candidates,
                adjacent_selected=adjacent,
                navigation_references=navigation_references,
                navigation_pages=set(navigation_plan),
                navigation_signal=navigation_signal,
                rendered_pages=rendered_pages,
                require_visual_table_confirmation=(
                    require_visual_table_confirmation
                ),
            )
        else:
            adjudicate(
                result,
                page_text,
                analyses,
                requested,
                candidates,
                adjacent,
                authority,
            )
        del page_text
        del analyses
    except Exception as exc:
        result.update(
            {
                "calibration_status": "needs_second_review",
                "review_status_detail": (
                    "bounded local parser/review error: "
                    f"{sanitize_error(exc)}"
                )[:300],
                "recommended_extraction_action": "manual_review_only",
                "reviewer_confidence": "low",
                "reviewer_notes": (
                    "Parser/review error; no adjudication claim made."
                ),
                "extraction_gate_label": "second_review_required",
                "extraction_gate_reason": (
                    "Parser/review error prevented refined confirmation."
                ),
            }
        )
    for field, values in ALLOWED.items():
        if result[field] not in values:
            raise ValueError(f"invalid output label {field}={result[field]}")
    for field in (
        "reviewer_notes",
        "extraction_schema_notes",
        "review_status_detail",
        "extraction_gate_reason",
    ):
        result[field] = result[field][:max_snippet_chars]
    result["review_elapsed_seconds"] = f"{time.monotonic() - started:.6f}"
    return result


def distribution(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in rows).items()))


def useful(row: dict[str, str]) -> bool:
    return (
        row["wage_table_present_label"] in {"yes", "maybe"}
        or row["page_hint_precision_label"] in {
            "correct",
            "partially_correct",
        }
    )


def group_metrics(
    rows: list[dict[str, str]], field: str
) -> dict[str, dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row[field]].append(row)
    output: dict[str, dict[str, object]] = {}
    for value, group in sorted(groups.items()):
        useful_count = sum(useful(row) for row in group)
        page_useful = sum(
            row["page_hint_precision_label"]
            in {"correct", "partially_correct"}
            for row in group
        )
        output[value] = {
            "rows": len(group),
            "useful_rows": useful_count,
            "useful_rate": round(useful_count / len(group), 6),
            "correct_or_partial_page_hint_rows": page_useful,
            "correct_or_partial_page_hint_rate": round(
                page_useful / len(group), 6
            ),
            "wage_table_yes_or_maybe_rows": sum(
                row["wage_table_present_label"] in {"yes", "maybe"}
                for row in group
            ),
        }
    return output


def summary_payload(
    rows: list[dict[str, str]],
    *,
    args: argparse.Namespace,
    mode: str,
    elapsed: float,
    input_hash_before: str,
    input_hash_after: str,
    parser_version: str,
) -> dict[str, object]:
    distributions = {
        field: distribution(rows, field)
        for field in (
            "calibration_status",
            "page_hint_precision_label",
            "wage_table_present_label",
            "wage_table_page_match_label",
            "contract_period_present_label",
            "contract_period_hint_match_label",
            "table_layout_type",
            "extraction_complexity_label",
            "false_positive_family",
            "recommended_extraction_action",
            "reviewer_confidence",
            "wage_language_present_label",
            "pay_numeric_language_present_label",
            "visual_table_structure_label",
            "wage_schedule_table_confirmed_label",
            "candidate_page_relationship_label",
            "table_navigation_signal",
            "visual_confirmation_method",
            "extraction_gate_label",
        )
    }
    likely = [
        row for row in rows if row["wage_table_signal"] == "likely"
    ]
    likely_useful = sum(useful(row) for row in likely)
    likely_rate = likely_useful / len(likely) if likely else 0.0
    included = sum(
        row["recommended_extraction_action"]
        == "include_in_wage_extraction_pilot"
        for row in rows
    )
    second_review = sum(
        row["calibration_status"] == "needs_second_review"
        for row in rows
    )
    review_mode = getattr(args, "review_mode", LEGACY_REVIEW_MODE)
    if mode == "dry_run":
        pass_status = "not_evaluated"
        next_recommendation = (
            "run_refined_re_review"
            if review_mode == REFINED_REVIEW_MODE
            else "run_bounded_assisted_local_review"
        )
    elif review_mode == REFINED_REVIEW_MODE:
        pass_status = "requires_independent_adjudication"
        next_recommendation = "independent_refined_calibration_decision"
    elif (
        likely_rate >= 0.8
        and included >= 50
        and second_review <= max(15, round(0.1 * len(rows)))
    ):
        pass_status = "pass"
        next_recommendation = "500_doc_extraction_run"
    elif likely_rate >= 0.8 and included >= 50:
        pass_status = "caution"
        next_recommendation = "500_doc_extraction_run"
    else:
        pass_status = "fail"
        next_recommendation = "refine_detector_or_schema"
    return {
        "schema_version": "1.0.0",
        "status": (
            "calibration_review_dry_run_passed"
            if mode == "dry_run"
            else "calibration_review_complete_assisted_local"
        ),
        "review_id": args.review_id,
        "review_method": (
            f"planned_no_pdf_open_{review_mode}"
            if mode == "dry_run"
            else REFINED_REVIEW_METHOD
            if review_mode == REFINED_REVIEW_MODE
            else REVIEW_METHOD
        ),
        "review_mode": review_mode,
        "input_csv": args.input_csv,
        "input_sha256_before": input_hash_before,
        "input_sha256_after": input_hash_after,
        "original_input_preserved": input_hash_before == input_hash_after,
        "rows": len(rows),
        "reviewed_rows": (
            sum(
                row["calibration_status"]
                in {"reviewed", "needs_second_review"}
                for row in rows
            )
            if mode == "local"
            else 0
        ),
        **distributions,
        "group_metrics": {
            field: group_metrics(rows, field)
            for field in (
                "wage_table_signal",
                "extraction_pilot_priority",
                "unit_type",
                "candidate_source_type",
                "source_officialness_rating",
                "page_count_bin",
                "contract_period_signal",
            )
        },
        "likely_useful_rows": likely_useful if mode == "local" else 0,
        "likely_useful_rate": (
            round(likely_rate, 6) if mode == "local" else None
        ),
        "calibration_pass_status": pass_status,
        "next_recommendation": next_recommendation,
        "parser_library": "pypdf",
        "parser_version": parser_version,
        "elapsed_seconds": round(elapsed, 6),
        "pdfs_opened": sum(int(row["pdf_opened_review"]) for row in rows),
        "pages_inspected": sum(
            len([value for value in row["pages_inspected"].split(",") if value])
            for row in rows
        ),
        "pages_with_text": sum(
            int(row["pages_with_text_review"]) for row in rows
        ),
        "bounded_text_chars_inspected_in_memory": sum(
            int(row["bounded_text_chars_inspected"]) for row in rows
        ),
        "rendered_pages": sum(
            int(row["rendered_page_count"]) for row in rows
        ),
        "render_failures": sum(
            int(row["render_failures"]) for row in rows
        ),
        "navigation_pages_inspected": sum(
            len(
                [
                    value
                    for value in row["navigation_pages_inspected"].split(",")
                    if value
                ]
            )
            for row in rows
        ),
        "full_text_artifacts_written": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "downloads_or_redownloads": 0,
        "ocr_runs": 0,
        "final_wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_ledger_mutations": 0,
        "caveats": [
            (
                "Review used the refined deterministic visual/table gate, "
                "not an independent human reviewer."
                if review_mode == REFINED_REVIEW_MODE
                else "Review used deterministic Codex-assisted local "
                "adjudication, not a human reviewer."
            ),
            "Assisted results are not independent ground-truth precision estimates.",
            "Only bounded candidate, adjacent, context, and navigation pages were eligible.",
            "Rendered-page checks are temporary and save no PNG, page text, table cells, or wage values.",
            "Independent human/visual validation remains required before extraction.",
        ],
    }


def report_markdown(summary: dict[str, object]) -> str:
    def lines_for(field: str) -> list[str]:
        return [
            f"- {key}: {value}"
            for key, value in summary[field].items()  # type: ignore[union-attr]
        ]

    lines = [
        "# Text/Table Calibration Review Report",
        "",
        f"- review ID: `{summary['review_id']}`",
        f"- method: `{summary['review_method']}`",
        f"- rows: {summary['rows']}",
        f"- reviewed/adjudicated rows: {summary['reviewed_rows']}",
        f"- calibration status: `{summary['calibration_pass_status']}`",
        f"- next recommendation: `{summary['next_recommendation']}`",
        "",
        "This is deterministic assisted local adjudication, not human manual "
        "review. It inspected bounded candidate/adjacent/context pages and "
        "retained controlled labels only.",
        "",
        "## Page-hint precision",
        "",
        *lines_for("page_hint_precision_label"),
        "",
        "## Wage-table presence",
        "",
        *lines_for("wage_table_present_label"),
        "",
        "## Contract-period hint match",
        "",
        *lines_for("contract_period_hint_match_label"),
        "",
        "## Extraction complexity",
        "",
        *lines_for("extraction_complexity_label"),
        "",
        "## Recommended action",
        "",
        *lines_for("recommended_extraction_action"),
        "",
        "## Boundaries",
        "",
        "- no URLs, downloads, network calls, or OCR",
        "- no full page/document text or complete tables saved",
        "- no final wage values, ingestion, or codification",
        "- original prepared calibration CSV preserved",
        "",
    ]
    return "\n".join(lines)


def false_positive_markdown(summary: dict[str, object]) -> str:
    counts = summary["false_positive_family"]
    lines = [
        "# Calibration False-Positive Families",
        "",
        "These are assisted bounded-review labels, not human-adjudicated final "
        "error codes.",
        "",
    ]
    lines.extend(
        f"- `{key}`: {value}"
        for key, value in counts.items()  # type: ignore[union-attr]
    )
    lines.extend(
        [
            "",
            "Common families guide classifier/schema refinement only. No "
            "wage values or page text are retained here.",
            "",
        ]
    )
    return "\n".join(lines)


def layout_markdown(summary: dict[str, object]) -> str:
    layouts = summary["table_layout_type"]
    complexity = summary["extraction_complexity_label"]
    lines = [
        "# Calibration Extraction Layout Notes",
        "",
        "## Layout counts",
        "",
    ]
    lines.extend(
        f"- `{key}`: {value}"
        for key, value in layouts.items()  # type: ignore[union-attr]
    )
    lines.extend(["", "## Complexity counts", ""])
    lines.extend(
        f"- `{key}`: {value}"
        for key, value in complexity.items()  # type: ignore[union-attr]
    )
    lines.extend(
        [
            "",
            "A later extraction schema should preserve effective dates, rate "
            "basis, unit/rank/classification labels, step/grade headers, and "
            "continuation-page relationships. These notes authorize no "
            "extraction run.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, object]:
    review_mode = getattr(args, "review_mode", LEGACY_REVIEW_MODE)
    if review_mode not in {LEGACY_REVIEW_MODE, REFINED_REVIEW_MODE}:
        raise ValueError(f"unsupported review mode: {review_mode}")
    render_pages = bool(getattr(args, "render_pages", False))
    max_rendered_pages = int(
        getattr(args, "max_rendered_pages_per_document", 3)
    )
    navigation_budget = int(getattr(args, "navigation_page_budget", 4))
    require_visual = bool(
        getattr(args, "require_visual_table_confirmation", True)
    )
    max_pages_per_document = getattr(
        args,
        "max_pages_per_document",
        None,
    )
    if max_pages_per_document is None:
        max_pages_per_document = (
            6 if review_mode == REFINED_REVIEW_MODE else 5
        )
    max_pages_per_document = int(max_pages_per_document)
    if max_rendered_pages < 0:
        raise ValueError("max rendered pages must be nonnegative")
    if navigation_budget < 0:
        raise ValueError("navigation page budget must be nonnegative")
    input_path = Path(args.input_csv)
    authority_path = Path(args.text_table_ledger_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if not args.no_save_full_text:
        raise ValueError("--no-save-full-text is mandatory")
    if args.max_snippet_chars < 1 or args.max_snippet_chars > 300:
        raise ValueError("max snippet chars must be between 1 and 300")
    input_hash_before = sha256_file(input_path)
    input_fields, input_rows = read_csv(input_path)
    _, authority_rows = read_csv(authority_path)
    authority = validate_input(input_fields, input_rows, authority_rows)
    selected = (
        input_rows
        if args.max_rows is None
        else input_rows[: args.max_rows]
    )
    if not selected:
        raise ValueError("max rows selected zero rows")
    output_dir.mkdir(parents=True)
    parser_version = importlib.metadata.version("pypdf")
    started = time.monotonic()
    if args.dry_run:
        reviewed = [
            initial_result(
                row,
                input_fields,
                args.review_id,
                "dry_run",
                review_mode,
            )
            for row in selected
        ]
        mode = "dry_run"
    else:
        reviewed = [
            review_row(
                row,
                input_fields=input_fields,
                review_id=args.review_id,
                authority=authority[row["text_table_detection_id"]],
                candidate_page_window=args.candidate_page_window,
                max_pages_per_document=max_pages_per_document,
                max_snippet_chars=args.max_snippet_chars,
                review_mode=review_mode,
                render_pages=render_pages,
                max_rendered_pages_per_document=max_rendered_pages,
                navigation_page_budget=navigation_budget,
                require_visual_table_confirmation=require_visual,
            )
            for row in selected
        ]
        mode = "local"
    input_hash_after = sha256_file(input_path)
    if input_hash_before != input_hash_after:
        raise RuntimeError("original calibration input changed during review")
    elapsed = time.monotonic() - started
    output_fields = [*input_fields]
    for field in (*AUDIT_FIELDS, *REFINED_FIELDS):
        if field not in output_fields:
            output_fields.append(field)
    write_csv(
        output_dir / "calibration_reviewed.csv",
        reviewed,
        output_fields,
    )
    timing_rows = [
        {
            "calibration_id": row["calibration_id"],
            "text_table_detection_id": row["text_table_detection_id"],
            "review_status": row["calibration_status"],
            "elapsed_seconds": row["review_elapsed_seconds"],
            "pdf_opened": row["pdf_opened_review"],
            "pages_inspected": row["pages_inspected"],
            "pages_with_text": row["pages_with_text_review"],
        }
        for row in reviewed
    ]
    write_csv(
        output_dir / "calibration_review_timing.csv",
        timing_rows,
        [
            "calibration_id",
            "text_table_detection_id",
            "review_status",
            "elapsed_seconds",
            "pdf_opened",
            "pages_inspected",
            "pages_with_text",
        ],
    )
    summary = summary_payload(
        reviewed,
        args=args,
        mode=mode,
        elapsed=elapsed,
        input_hash_before=input_hash_before,
        input_hash_after=input_hash_after,
        parser_version=parser_version,
    )
    write_json(output_dir / "calibration_review_summary.json", summary)
    (output_dir / "calibration_review_report.md").write_text(
        report_markdown(summary), encoding="utf-8"
    )
    (output_dir / "calibration_false_positive_families.md").write_text(
        false_positive_markdown(summary), encoding="utf-8"
    )
    (output_dir / "calibration_extraction_layout_notes.md").write_text(
        layout_markdown(summary), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded assisted local calibration review"
    )
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--review-id", required=True)
    parser.add_argument(
        "--text-table-ledger-csv",
        default=str(
            DEFAULT_AUTHORITY.relative_to(ROOT)
        ),
    )
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--candidate-page-window", type=int, default=1)
    parser.add_argument("--max-pages-per-document", type=int)
    parser.add_argument("--max-snippet-chars", type=int, default=300)
    parser.add_argument(
        "--review-mode",
        choices=(LEGACY_REVIEW_MODE, REFINED_REVIEW_MODE),
        default=LEGACY_REVIEW_MODE,
    )
    parser.add_argument("--render-pages", action="store_true")
    parser.add_argument(
        "--max-rendered-pages-per-document",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--navigation-page-budget",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--require-visual-table-confirmation",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--no-save-full-text",
        action="store_true",
        default=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"Calibration review complete: mode={summary['review_method']}; "
        f"rows={summary['rows']}; reviewed={summary['reviewed_rows']}; "
        f"status={summary['calibration_pass_status']}; "
        f"PDFs opened={summary['pdfs_opened']}; OCR=0; "
        "full text saved=0; final wage values=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
