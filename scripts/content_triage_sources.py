#!/usr/bin/env python3
"""Validate and materialize offline content-triage dry-run ledgers.

The content-access path is intentionally not implemented. This command only
accepts ``--dry-run`` and performs no network, download, parsing, OCR,
extraction, ingestion, or codification work.
"""

from __future__ import annotations

import argparse
import csv
import json
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def dry_run(args: argparse.Namespace) -> dict[str, object]:
    if not args.dry_run:
        raise ValueError(
            "Live content triage is not implemented. Re-run with --dry-run; "
            "do not open or download content in this task."
        )
    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty {output_dir}")
    rows = read_csv(input_path)
    if rows:
        missing = REQUIRED_INPUT_FIELDS - set(rows[0])
        if missing:
            raise ValueError(f"Input is missing required fields: {sorted(missing)}")
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    triage_ids = [row.get("triage_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if any(not value for value in triage_ids + queue_ids):
        raise ValueError("Input contains blank triage or candidate queue identity")
    if len(triage_ids) != len(set(triage_ids)):
        raise ValueError("Input contains duplicate triage IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Input contains duplicate candidate queue IDs")
    output_dir.mkdir(parents=True, exist_ok=True)
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
                "planned_at": planned_at,
                "elapsed_seconds": "0",
                "url_opened": "no",
                "document_downloaded": "no",
                "content_parsed": "no",
            }
        )
    write_csv(output_dir / "triage_ledger.csv", ledger, OUTPUT_FIELDS)
    write_csv(
        output_dir / "triage_timing.csv",
        timing,
        [
            "row_number",
            "triage_id",
            "candidate_queue_row_id",
            "status",
            "planned_at",
            "elapsed_seconds",
            "url_opened",
            "document_downloaded",
            "content_parsed",
        ],
    )
    summary: dict[str, object] = {
        "schema_version": "1.0.0",
        "status": "dry_run_passed",
        "review_mode": args.review_mode,
        "input_csv": input_path.as_posix(),
        "planned_rows": len(ledger),
        "terminal_planned_rows": len(ledger),
        "triage_status_counts": dict(
            sorted(Counter(row["triage_status"] for row in ledger).items())
        ),
        "priority_for_content_review_counts": dict(
            sorted(
                Counter(
                    row["priority_for_content_review"] for row in ledger
                ).items()
            )
        ),
        "content_artifacts_written": 0,
        "write_content_samples": False,
        "urls_opened": 0,
        "network_calls": 0,
        "documents_downloaded": 0,
        "documents_parsed": 0,
        "pdfs_parsed": 0,
        "ocr_runs": 0,
        "live_attempted": False,
        "completed_at": planned_at,
    }
    with (output_dir / "triage_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
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


def main() -> int:
    args = parse_args()
    if args.write_content_samples:
        raise ValueError("Content samples are prohibited in the offline dry-run")
    summary = dry_run(args)
    print(
        "Content-triage dry run passed: "
        f"{summary['planned_rows']} rows; URLs opened=0; downloads=0; parses=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
