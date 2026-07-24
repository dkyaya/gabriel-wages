#!/usr/bin/env python3
"""Materialize offline content-triage planning or metadata-only outcomes.

Both supported paths are deliberately network-free. ``--dry-run`` validates
the lane schema and writes planned rows. Non-dry execution is allowed only
with ``--review-mode metadata_only`` and classifies committed input metadata;
it never opens URLs, downloads content, parses documents, runs OCR, ingests,
codifies, extracts wages, or writes content artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from prepare_content_triage_batches import IDENTITY_FIELDS, OUTPUT_FIELDS


REQUIRED_INPUT_FIELDS = set(IDENTITY_FIELDS) | {
    "triage_status",
    "priority_for_content_review",
    "recommended_next_action",
    "duplicate_source_group_id",
    "triage_stage",
}
METADATA_REQUIRED_FOR_CLASSIFICATION = {
    "candidate_queue_row_id",
    "verification_id",
    "municipality_id",
    "state",
    "municipality",
    "candidate_url",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "verification_status",
    "content_type",
    "source_locator",
}
LOWER_DISPOSITIONS = {
    "context_hold",
    "insufficient_hold",
    "duplicate_hold",
    "already_canonical",
    "calibration_rejected",
    "other_hold",
}
TIMING_FIELDS = [
    "row_number",
    "triage_id",
    "candidate_queue_row_id",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "url_opened",
    "document_downloaded",
    "content_parsed",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
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


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def validate_input(rows: list[dict[str, str]]) -> None:
    if rows:
        missing = REQUIRED_INPUT_FIELDS - set(rows[0])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
    triage_ids = [row.get("triage_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if any(not value for value in triage_ids + queue_ids):
        raise ValueError("Input contains blank triage or candidate queue identity")
    if len(triage_ids) != len(set(triage_ids)):
        raise ValueError("Input contains duplicate triage IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Input contains duplicate candidate queue IDs")


def prepare_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty {path}")
    path.mkdir(parents=True, exist_ok=True)


def summarize(
    *,
    status: str,
    review_mode: str,
    input_path: Path,
    ledger: list[dict[str, str]],
    completed_at: str,
) -> dict[str, object]:
    count_fields = {
        "triage_status_counts": "triage_status",
        "recommended_next_action_counts": "recommended_next_action",
        "extraction_readiness_prelim_counts": "extraction_readiness_prelim",
        "source_relevance_prelim_counts": "source_relevance_prelim",
        "priority_for_content_review_counts": "priority_for_content_review",
    }
    payload: dict[str, object] = {
        "schema_version": "1.1.0",
        "status": status,
        "review_mode": review_mode,
        "input_csv": input_path.as_posix(),
        "planned_rows": len(ledger),
        "ledger_rows": len(ledger),
        "terminal_rows": len(ledger),
    }
    for output_name, field in count_fields.items():
        payload[output_name] = dict(
            sorted(Counter(row.get(field, "") for row in ledger).items())
        )
    payload.update(
        {
            "content_artifacts_written": 0,
            "write_content_samples": False,
            "urls_opened": 0,
            "network_calls": 0,
            "documents_downloaded": 0,
            "documents_parsed": 0,
            "pdfs_parsed": 0,
            "ocr_runs": 0,
            "live_attempted": False,
            "completed_at": completed_at,
        }
    )
    if status == "dry_run_passed":
        payload["terminal_planned_rows"] = len(ledger)
    return payload


def dry_run(args: argparse.Namespace) -> dict[str, object]:
    if not args.dry_run:
        raise ValueError("dry_run() requires --dry-run")
    if args.review_mode != "metadata_only":
        raise ValueError("Only --review-mode metadata_only is implemented")
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    rows = read_csv(input_path)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    validate_input(rows)
    prepare_output_dir(output_dir)
    planned_at = now_utc()
    ledger: list[dict[str, str]] = []
    timing: list[dict[str, str]] = []
    for index, source in enumerate(rows, start=1):
        row = {field: source.get(field, "") for field in OUTPUT_FIELDS}
        row.update(
            {
                "triage_status": "triage_planned",
                "triage_status_detail": (
                    "dry-run schema validated; no URL or content access"
                ),
                "triage_stage": "metadata_first_dry_run_planned",
                "reviewer": "",
                "triaged_at": "",
            }
        )
        ledger.append(row)
        timing.append(
            {
                "row_number": str(index),
                "triage_id": row["triage_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "status": "dry_run_planned",
                "started_at": planned_at,
                "completed_at": planned_at,
                "elapsed_seconds": "0",
                "url_opened": "no",
                "document_downloaded": "no",
                "content_parsed": "no",
            }
        )
    write_csv(output_dir / "triage_ledger.csv", ledger, OUTPUT_FIELDS)
    write_csv(output_dir / "triage_timing.csv", timing, TIMING_FIELDS)
    summary = summarize(
        status="dry_run_passed",
        review_mode=args.review_mode,
        input_path=input_path,
        ledger=ledger,
        completed_at=planned_at,
    )
    write_json(output_dir / "triage_summary.json", summary)
    return summary


def classify_metadata(source: dict[str, str], triaged_at: str) -> dict[str, str]:
    row = {field: source.get(field, "") for field in OUTPUT_FIELDS}
    missing = sorted(
        field
        for field in METADATA_REQUIRED_FOR_CLASSIFICATION
        if not source.get(field, "").strip()
    )
    disposition = source.get("candidate_status_before_verification", "").strip()
    verification_status = source.get("verification_status", "").strip()
    source_type = source.get("candidate_source_type", "").strip().lower()
    content_type = source.get("content_type", "").strip().lower()
    duplicate_role = source.get("duplicate_group_role_for_triage", "").strip()
    duplicate_status = source.get("duplicate_handling_status", "").strip()

    common = {
        "source_officialness_prelim": "unknown",
        "employer_match_prelim": "unknown",
        "municipality_match_prelim": "unknown",
        "bargaining_unit_match_prelim": "unknown",
        "safety_unit_signal_prelim": "unknown",
        "non_safety_unit_signal_prelim": "unknown",
        "source_year_or_period_prelim": "unknown",
        "wage_table_signal_prelim": "unknown",
        "wage_growth_signal_prelim": "unknown",
        "mechanism_language_signal_prelim": "unknown",
        "oversized_handling_status": "not_oversized_in_selected_round",
        "reviewer": "script_metadata_only",
        "triaged_at": triaged_at,
        "triage_stage": "metadata_only_triaged_not_content_reviewed",
    }
    row.update(common)

    if duplicate_role in {"canonical_representative", "linked_duplicate"} or (
        verification_status
        in {"duplicate_of_verified_source", "duplicate_same_url_pending"}
    ):
        row["duplicate_handling_status"] = (
            "representative_or_group_review_needed"
        )
    elif not duplicate_status:
        row["duplicate_handling_status"] = "not_in_duplicate_group"

    if missing:
        row.update(
            {
                "triage_status": "needs_manual_review",
                "triage_status_detail": (
                    "metadata-only classification missing required committed fields"
                ),
                "source_relevance_prelim": "unknown",
                "source_document_type_prelim": "unknown",
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "manual_review",
                "manual_review_reason": "missing_metadata:" + ",".join(missing),
                "triage_notes": (
                    "Metadata-only review found missing committed fields; no "
                    "source content was accessed."
                ),
            }
        )
        return row

    candidate_priority = source.get("candidate_priority", "").strip().lower()
    is_scheduled = disposition == "scheduled"
    is_reachable_document = verification_status == "reachable_pdf_or_document"
    is_cba = source_type == "cba"
    is_pdf = content_type == "application/pdf"
    is_html = content_type == "text/html" or verification_status == "reachable_html"
    source_rich_types = {
        "cba",
        "wage_schedule_or_compensation_plan",
        "pay_plan",
        "arbitration_award",
        "factfinding",
        "memorandum_or_settlement",
        "ordinance_or_policy",
    }
    source_document_type = (
        f"{source_type or 'unknown'}_candidate_metadata_only"
    )

    if verification_status in {
        "duplicate_of_verified_source",
        "duplicate_same_url_pending",
    }:
        row.update(
            {
                "triage_status": "duplicate_defer_to_canonical",
                "triage_status_detail": (
                    "duplicate routing outcome requires canonical group review; "
                    "metadata only"
                ),
                "source_relevance_prelim": "possibly_relevant",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "duplicate_group_review",
                "duplicate_handling_status": "duplicate_group_review",
                "manual_review_reason": "duplicate_routing_status",
                "triage_notes": (
                    "Duplicate linkage was preserved for later canonical-group "
                    "review; metadata-only triage did not access source content."
                ),
            }
        )
    elif verification_status == "too_large":
        row.update(
            {
                "triage_status": "oversized_needs_separate_pass",
                "triage_status_detail": (
                    "routing exceeded the ordinary bounded byte limit; metadata only"
                ),
                "source_relevance_prelim": "unknown",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "oversized_strategy_later",
                "oversized_handling_status": "needs_oversized_strategy",
                "manual_review_reason": "routing_outcome_too_large",
                "triage_notes": (
                    "Retained for a separately authorized oversized-source "
                    "strategy; metadata-only triage did not access source content."
                ),
            }
        )
    elif verification_status in {"blocked_or_forbidden", "not_found"}:
        row.update(
            {
                "triage_status": "blocked_or_unreachable_defer",
                "triage_status_detail": (
                    f"{verification_status} routing outcome deferred; metadata only"
                ),
                "source_relevance_prelim": "unknown",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "none",
                "priority_for_content_review": "defer",
                "recommended_next_action": "blocked_status_review_later",
                "manual_review_reason": f"routing_outcome_{verification_status}",
                "triage_notes": (
                    "The URL-routing exception is not a municipality source-"
                    "absence finding; metadata-only triage accessed no content."
                ),
            }
        )
    elif verification_status in {
        "error",
        "ssl_error",
        "timeout",
        "connection_error",
    }:
        row.update(
            {
                "triage_status": "needs_manual_review",
                "triage_status_detail": (
                    f"{verification_status} routing exception requires later "
                    "manual routing review; metadata only"
                ),
                "source_relevance_prelim": "unknown",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "manual_review",
                "manual_review_reason": f"routing_exception_{verification_status}",
                "triage_notes": (
                    "A later routing review may revisit this exception; metadata-"
                    "only triage did not access source content."
                ),
            }
        )
    elif (
        is_scheduled
        and candidate_priority == "high"
        and is_reachable_document
        and is_cba
        and is_pdf
    ):
        row.update(
            {
                "triage_status": "high_priority_content_review",
                "triage_status_detail": (
                    "scheduled CBA-labeled PDF with a reachable-document routing "
                    "outcome; metadata only"
                ),
                "source_relevance_prelim": "likely_relevant",
                "source_document_type_prelim": "cba_candidate_metadata_only",
                "extraction_readiness_prelim": "medium",
                "priority_for_content_review": "p1",
                "recommended_next_action": (
                    "content_review_download_allowed_later"
                ),
                "manual_review_reason": "",
                "triage_notes": (
                    "Prioritize for later authorized content review based only "
                    "on committed candidate and routing metadata; actual CBA "
                    "identity and wage content remain unverified."
                ),
            }
        )
    elif disposition == "duplicate_hold":
        row.update(
            {
                "triage_status": "duplicate_defer_to_canonical",
                "triage_status_detail": (
                    "original duplicate-hold disposition preserved; metadata only"
                ),
                "source_relevance_prelim": "possibly_relevant",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "duplicate_group_review",
                "duplicate_handling_status": "duplicate_group_review",
                "manual_review_reason": "original_duplicate_hold",
                "triage_notes": (
                    "The lower duplicate disposition was preserved; metadata-only "
                    "triage did not access source content."
                ),
            }
        )
    elif disposition == "already_canonical":
        row.update(
            {
                "triage_status": "already_canonical_context",
                "triage_status_detail": (
                    "already-canonical candidate disposition preserved; metadata only"
                ),
                "source_relevance_prelim": "possibly_relevant",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "metadata_review_only",
                "manual_review_reason": "already_canonical_disposition",
                "triage_notes": (
                    "This row remains canonical context and was not upgraded; "
                    "metadata-only triage accessed no source content."
                ),
            }
        )
    elif disposition == "calibration_rejected":
        row.update(
            {
                "triage_status": "excluded_from_content_review",
                "triage_status_detail": (
                    "calibration-rejected disposition preserved; metadata only"
                ),
                "source_relevance_prelim": "unlikely_relevant",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": "none",
                "priority_for_content_review": "exclude",
                "recommended_next_action": "exclude_for_now",
                "manual_review_reason": "calibration_rejected_disposition",
                "triage_notes": (
                    "The rejected disposition was preserved; metadata-only triage "
                    "did not access source content."
                ),
            }
        )
    elif disposition in {"context_hold", "insufficient_hold", "other_hold"}:
        context_row = disposition == "context_hold"
        row.update(
            {
                "triage_status": (
                    "low_priority_content_review"
                    if context_row
                    else "needs_manual_review"
                ),
                "triage_status_detail": (
                    f"original {disposition} disposition preserved; metadata only"
                ),
                "source_relevance_prelim": (
                    "possibly_relevant" if context_row else "unknown"
                ),
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": (
                    "low" if context_row else "unknown"
                ),
                "priority_for_content_review": (
                    "p3" if context_row else "defer"
                ),
                "recommended_next_action": (
                    "metadata_review_only" if context_row else "manual_review"
                ),
                "manual_review_reason": (
                    "lower_original_candidate_disposition"
                ),
                "triage_notes": (
                    "The lower candidate disposition was preserved without "
                    "promotion; metadata-only triage did not access source content."
                ),
            }
        )
    elif verification_status in {
        "reachable_pdf_or_document",
        "reachable_html",
        "reachable_http",
    }:
        document_like = verification_status == "reachable_pdf_or_document"
        source_rich = source_type in source_rich_types
        priority = "p2" if source_rich else "p3"
        readiness = "medium" if document_like and source_rich else "low"
        action = (
            "content_review_download_allowed_later"
            if document_like and source_rich
            else "metadata_review_only"
        )
        row.update(
            {
                "triage_status": (
                    "medium_priority_content_review"
                    if source_rich
                    else "low_priority_content_review"
                ),
                "triage_status_detail": (
                    f"{verification_status} candidate retained for later review; "
                    "metadata only"
                ),
                "source_relevance_prelim": "possibly_relevant",
                "source_document_type_prelim": source_document_type,
                "extraction_readiness_prelim": readiness,
                "priority_for_content_review": priority,
                "recommended_next_action": action,
                "manual_review_reason": "",
                "triage_notes": (
                    "The routing and candidate labels support later review, but "
                    "metadata-only triage did not access or validate source content."
                ),
            }
        )
    else:
        row.update(
            {
                "triage_status": "needs_manual_review",
                "triage_status_detail": (
                    "committed metadata does not meet a deterministic high-"
                    "confidence scheduling rule"
                ),
                "source_relevance_prelim": "unknown",
                "source_document_type_prelim": (
                    f"{source_type or 'unknown'}_candidate_metadata_only"
                ),
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": "defer",
                "recommended_next_action": "manual_review",
                "manual_review_reason": "no_metadata_only_rule_match",
                "triage_notes": (
                    "Manual metadata review is required; no source content was "
                    "accessed."
                ),
            }
        )
    return row


def metadata_only(args: argparse.Namespace) -> dict[str, object]:
    if args.dry_run:
        raise ValueError("metadata_only() is the non-dry metadata-only path")
    if args.review_mode != "metadata_only":
        raise ValueError(
            f"Review mode {args.review_mode!r} is not implemented; only "
            "metadata_only may run without --dry-run"
        )
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    rows = read_csv(input_path)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    validate_input(rows)
    prepare_output_dir(output_dir)
    run_started = now_utc()
    ledger: list[dict[str, str]] = []
    timing: list[dict[str, str]] = []
    for index, source in enumerate(rows, start=1):
        row_started_at = now_utc()
        started = time.monotonic()
        row = classify_metadata(source, row_started_at)
        elapsed = time.monotonic() - started
        ledger.append(row)
        timing.append(
            {
                "row_number": str(index),
                "triage_id": row["triage_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "status": row["triage_status"],
                "started_at": row_started_at,
                "completed_at": now_utc(),
                "elapsed_seconds": f"{elapsed:.6f}",
                "url_opened": "no",
                "document_downloaded": "no",
                "content_parsed": "no",
            }
        )
        if index % 25 == 0:
            write_csv(output_dir / "triage_ledger.csv", ledger, OUTPUT_FIELDS)
            write_csv(output_dir / "triage_timing.csv", timing, TIMING_FIELDS)
            checkpoint = summarize(
                status="metadata_only_running",
                review_mode=args.review_mode,
                input_path=input_path,
                ledger=ledger,
                completed_at=now_utc(),
            )
            checkpoint["input_rows"] = len(rows)
            checkpoint["run_started_at"] = run_started
            write_json(output_dir / "triage_summary.json", checkpoint)
    write_csv(output_dir / "triage_ledger.csv", ledger, OUTPUT_FIELDS)
    write_csv(output_dir / "triage_timing.csv", timing, TIMING_FIELDS)
    summary = summarize(
        status="metadata_only_completed",
        review_mode=args.review_mode,
        input_path=input_path,
        ledger=ledger,
        completed_at=now_utc(),
    )
    summary["input_rows"] = len(rows)
    summary["run_started_at"] = run_started
    write_json(output_dir / "triage_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--review-mode", default="metadata_only")
    samples = parser.add_mutually_exclusive_group()
    samples.add_argument("--write-content-samples", action="store_true")
    samples.add_argument("--no-write-content-samples", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.write_content_samples:
        raise ValueError("Content samples are prohibited in metadata-only triage")
    return dry_run(args) if args.dry_run else metadata_only(args)


def main() -> int:
    args = parse_args()
    summary = run(args)
    label = "dry run" if args.dry_run else "metadata-only triage"
    print(
        f"Content-triage {label} completed: "
        f"{summary['ledger_rows']} rows; URLs opened=0; downloads=0; parses=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
