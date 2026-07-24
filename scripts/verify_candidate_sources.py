#!/usr/bin/env python3
"""Validate a verification lane and create an offline dry-run ledger.

Live URL verification is intentionally fail-closed in this framework version.
The dry-run path performs schema and URL-syntax checks only; it never resolves,
opens, fetches, or otherwise contacts a candidate URL.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


REQUIRED_INPUT_FIELDS = {
    "verification_id",
    "candidate_queue_row_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "duplicate_source_group_id",
}

LEDGER_FIELDS = [
    "verification_id",
    "candidate_queue_row_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "verification_status",
    "verification_status_detail",
    "url_reachable",
    "http_status_code",
    "final_url",
    "redirect_detected",
    "content_type",
    "source_officialness",
    "employer_match_status",
    "municipality_match_status",
    "source_document_type_verified",
    "source_year_or_period",
    "safety_unit_signal",
    "non_safety_unit_signal",
    "wage_data_signal",
    "wage_growth_extractability",
    "mechanism_language_signal",
    "duplicate_source_group_id",
    "canonical_source_candidate",
    "verification_notes",
    "reviewer",
    "verified_at",
    "artifact_path",
]


def timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def read_input(path: Path, max_rows: int | None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_INPUT_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
        rows = list(reader)
    if max_rows is not None:
        rows = rows[:max_rows]
    ids = [row["verification_id"].strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError("Input contains blank verification IDs")
    if len(ids) != len(set(ids)):
        raise ValueError("Input contains duplicate verification IDs")
    for row in rows:
        for field in REQUIRED_INPUT_FIELDS - {"candidate_title"}:
            if not row.get(field, "").strip():
                raise ValueError(
                    f"{row.get('verification_id', '<unknown>')} has blank {field}"
                )
        if not valid_http_url(row["candidate_url"]):
            raise ValueError(f"Invalid HTTP(S) URL for {row['verification_id']}")
    return rows


def run_dry(args: argparse.Namespace) -> dict[str, object]:
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_input(input_path, args.max_rows)

    ledger_rows: list[dict[str, str]] = []
    timing_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        started = time.monotonic()
        ledger = {field: "" for field in LEDGER_FIELDS}
        for field in REQUIRED_INPUT_FIELDS:
            if field in ledger:
                ledger[field] = row.get(field, "")
        ledger.update(
            {
                "verification_status": "planned_not_verified",
                "verification_status_detail": "dry_run_schema_validated_no_url_opened",
                "url_reachable": "not_checked",
                "redirect_detected": "not_checked",
                "source_officialness": "unknown",
                "employer_match_status": "not_checked",
                "municipality_match_status": "not_checked",
                "source_document_type_verified": "not_checked",
                "safety_unit_signal": "unknown",
                "non_safety_unit_signal": "unknown",
                "wage_data_signal": "unknown",
                "wage_growth_extractability": "unknown",
                "mechanism_language_signal": "unknown",
                "canonical_source_candidate": "not_checked",
                "verification_notes": (
                    "Offline dry run only. URL syntax and identity schema passed; "
                    "the URL was not opened."
                ),
            }
        )
        ledger_rows.append(ledger)
        timing_rows.append(
            {
                "row_number": index,
                "verification_id": row["verification_id"],
                "plan_status": "dry_run_planned",
                "url_syntax_valid": "yes",
                "url_opened": "no",
                "network_call_attempted": "no",
                "elapsed_seconds": f"{time.monotonic() - started:.6f}",
            }
        )

    with (output_dir / "verification_ledger.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=LEDGER_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(ledger_rows)
    timing_fields = [
        "row_number",
        "verification_id",
        "plan_status",
        "url_syntax_valid",
        "url_opened",
        "network_call_attempted",
        "elapsed_seconds",
    ]
    with (output_dir / "plan_timing.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=timing_fields, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(timing_rows)

    summary: dict[str, object] = {
        "schema_version": "1.0.0",
        "mode": "dry_run",
        "status": "dry_run_passed",
        "generated_at": timestamp(),
        "input_csv": input_path.as_posix(),
        "output_dir": output_dir.as_posix(),
        "planned_rows": len(rows),
        "valid_identity_rows": len(rows),
        "valid_http_url_syntax_rows": len(rows),
        "urls_opened": 0,
        "network_calls": 0,
        "live_verification_performed": False,
        "verification_stage": "planned_not_verified",
        "timeout_seconds_recorded_for_future_live_mode": args.timeout,
        "concurrency_recorded_for_future_live_mode": args.concurrency,
        "respect_robots_note": bool(args.respect_robots_note),
        "stage_boundary": (
            "Dry-run rows are candidate leads only, not verified sources, ingested "
            "sources, codified evidence, or analysis-ready wage observations."
        ),
    }
    with (output_dir / "verification_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--respect-robots-note", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.timeout <= 0 or args.concurrency <= 0:
        raise SystemExit("--timeout and --concurrency must be positive")
    if not args.dry_run:
        raise SystemExit(
            "Live verification is intentionally not implemented in this offline "
            "framework. Use --dry-run; implement and authorize live fetching separately."
        )
    summary = run_dry(args)
    print(
        f"Verification dry run passed: {summary['planned_rows']} planned rows; "
        "URLs opened=0; network calls=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
