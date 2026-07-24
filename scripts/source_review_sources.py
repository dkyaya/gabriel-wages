#!/usr/bin/env python3
"""Validate and materialize an offline source-review dry run.

Live content review is intentionally not implemented. The only supported path
is ``--dry-run`` with ``--review-mode source_rating_planned`` and
``--no-download``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from prepare_source_review_pilot import (
    IDENTITY_FIELDS,
    OUTPUT_FIELDS,
    SAFETY_COUNTER_FIELDS,
)


REQUIRED_INPUT_FIELDS = set(IDENTITY_FIELDS) | {
    "source_review_lane_id",
    "source_review_stage",
}
TIMING_FIELDS = [
    "row_number",
    "source_review_id",
    "candidate_queue_row_id",
    "status",
    "started_at",
    "completed_at",
    "elapsed_seconds",
    "url_opened",
    "document_downloaded",
    "document_parsed",
    "ocr_run",
]


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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


def prepare_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty {path}")
    path.mkdir(parents=True, exist_ok=True)


def validate_input(rows: list[dict[str, str]]) -> None:
    if rows:
        missing = REQUIRED_INPUT_FIELDS - set(rows[0])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
    review_ids = [row.get("source_review_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if any(not value for value in review_ids + queue_ids):
        raise ValueError("Input has blank source-review or candidate identity")
    if len(review_ids) != len(set(review_ids)):
        raise ValueError("Input repeats source-review IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Input repeats candidate-queue IDs")


def run_dry(args: argparse.Namespace) -> dict[str, object]:
    if not args.dry_run:
        raise ValueError(
            "Live/content source review is not implemented; use --dry-run"
        )
    if args.review_mode != "source_rating_planned":
        raise ValueError(
            "Only --review-mode source_rating_planned is supported"
        )
    if not args.no_download or args.download_mode != "none":
        raise ValueError("Dry-run requires --no-download and download-mode none")
    if args.write_content_samples:
        raise ValueError("Content samples are forbidden in this dry-run")
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    rows = read_csv(input_path)
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    validate_input(rows)
    prepare_output_dir(output_dir)
    timestamp = now_utc()
    ledger: list[dict[str, str]] = []
    timing: list[dict[str, str]] = []
    for index, source in enumerate(rows, start=1):
        row = {field: source.get(field, "") for field in OUTPUT_FIELDS}
        row.update(
            {
                "source_review_status": "planned_not_reviewed",
                "source_review_status_detail": (
                    "dry-run schema validated; source content not accessed"
                ),
                "url_access_status": "not_started",
                "download_status": "not_started",
                "content_artifact_path": "",
                "content_hash": "",
                "content_byte_size": "",
                "content_type_observed": "unknown",
                "text_layer_status": "unknown",
                "pdf_page_count": "",
                "source_officialness_rating": "unknown",
                "source_relevance_rating": "unknown",
                "municipality_match_rating": "unknown",
                "employer_match_rating": "unknown",
                "bargaining_unit_match_rating": "unknown",
                "safety_unit_match_signal": "unknown",
                "non_safety_unit_match_signal": "unknown",
                "document_type_rating": "unknown",
                "wage_table_signal": "unknown",
                "wage_growth_signal": "unknown",
                "mechanism_language_signal": "unknown",
                "extraction_readiness_rating": "unknown",
                "extraction_mode_recommended": "manual_review",
                "duplicate_canonical_decision": "not_reviewed",
                "reviewer_notes": (
                    "Dry-run only; no source rating or content review performed."
                ),
                "reviewer": "",
                "reviewed_at": "",
                **{field: "0" for field in SAFETY_COUNTER_FIELDS},
            }
        )
        ledger.append(row)
        timing.append(
            {
                "row_number": str(index),
                "source_review_id": row["source_review_id"],
                "candidate_queue_row_id": row["candidate_queue_row_id"],
                "status": "dry_run_planned",
                "started_at": timestamp,
                "completed_at": timestamp,
                "elapsed_seconds": "0",
                "url_opened": "no",
                "document_downloaded": "no",
                "document_parsed": "no",
                "ocr_run": "no",
            }
        )
    write_csv(output_dir / "source_review_ledger.csv", ledger, OUTPUT_FIELDS)
    write_csv(output_dir / "source_review_timing.csv", timing, TIMING_FIELDS)
    summary: dict[str, object] = {
        "schema_version": "1.0.0",
        "status": "dry_run_passed",
        "review_mode": args.review_mode,
        "input_csv": input_path.as_posix(),
        "planned_rows": len(rows),
        "ledger_rows": len(ledger),
        "terminal_planned_rows": len(ledger),
        "source_review_status_counts": dict(
            sorted(
                Counter(row["source_review_status"] for row in ledger).items()
            )
        ),
        "url_access_status_counts": dict(
            sorted(Counter(row["url_access_status"] for row in ledger).items())
        ),
        "download_status_counts": dict(
            sorted(Counter(row["download_status"] for row in ledger).items())
        ),
        **{field: 0 for field in SAFETY_COUNTER_FIELDS},
        "write_content_samples": False,
        "live_attempted": False,
        "completed_at": timestamp,
    }
    write_json(output_dir / "source_review_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--review-mode", default="source_rating_planned")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--download-mode", default="none")
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument(
        "--write-content-samples",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    return parser.parse_args()


def main() -> int:
    summary = run_dry(parse_args())
    print(
        f"Source-review dry run passed: {summary['ledger_rows']} planned rows; "
        "0 URL opens, downloads, parses, OCR runs, or content artifacts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
