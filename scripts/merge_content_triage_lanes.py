#!/usr/bin/env python3
"""Merge audited metadata-only content-triage lanes into a durable ledger.

This script is deliberately offline. It reads committed plans, local lane
ledgers, audit summaries, and a cumulative routing ledger. It never opens a
candidate URL, downloads or parses content, mutates scout/routing accounting,
or performs ingestion, codification, extraction, or analysis.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_TRIAGE_STATUSES = {
    "high_priority_content_review",
    "medium_priority_content_review",
    "low_priority_content_review",
    "duplicate_defer_to_canonical",
    "oversized_needs_separate_pass",
    "blocked_or_unreachable_defer",
    "not_relevant_on_metadata",
    "needs_manual_review",
    "already_canonical_context",
    "excluded_from_content_review",
}

ACCESS_FIELDS = (
    "urls_opened",
    "network_calls",
    "documents_downloaded",
    "documents_parsed",
    "pdfs_parsed",
    "ocr_runs",
    "content_artifacts_written",
)

IMMUTABLE_INPUT_FIELDS = (
    "triage_id",
    "candidate_queue_row_id",
    "verification_id",
    "verification_round_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "final_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_status_before_verification",
    "verification_status",
    "content_type",
    "source_locator",
    "triage_bucket",
    "candidate_priority",
    "duplicate_source_group_id",
)

MERGE_FIELDS = (
    "content_triage_round_id",
    "content_triage_merge_id",
    "content_triage_merged_at",
    "content_triage_lane_id",
    "content_triage_stage",
)

LEDGER_NAME = "content_triage_metadata_ledger_cumulative.csv"
SUMMARY_NAME = "content_triage_metadata_summary_cumulative.json"
AUDIT_NAME = "content_triage_metadata_merge_audit_cumulative.md"
LATEST_LEDGER_NAME = "content_triage_ledger_latest.csv"
LATEST_SUMMARY_NAME = "content_triage_summary_latest.json"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def zero_access_counts() -> dict[str, int]:
    return {field: 0 for field in ACCESS_FIELDS}


def cross_tab(
    rows: list[dict[str, str]], row_field: str, column_field: str
) -> dict[str, dict[str, int]]:
    values: dict[str, Counter[str]] = {}
    for row in rows:
        values.setdefault(row.get(row_field, ""), Counter())[
            row.get(column_field, "")
        ] += 1
    return {
        key: dict(sorted(counts.items()))
        for key, counts in sorted(values.items())
    }


def count_field(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") for row in rows).items()))


def lane_output_dir(
    manifest: dict[str, Any], lane: dict[str, Any]
) -> Path:
    configured = lane.get("metadata_only_output_dir")
    if configured:
        return Path(str(configured))
    return (
        Path("tmp/content_triage_rounds")
        / str(manifest["round_id"])
        / f"{lane['lane_id']}_metadata_only_attempt1"
    )


def validate_audit(
    manifest: dict[str, Any],
    audit: dict[str, Any],
    audit_path: Path,
) -> None:
    round_id = str(manifest["round_id"])
    if audit.get("round_id") != round_id:
        raise ValueError(
            f"Audit round mismatch for {round_id}: {audit.get('round_id')}"
        )
    if audit.get("merge_recommendation") != "merge_all_content_triage_lanes":
        raise ValueError(f"Audit is not merge-eligible for {round_id}")
    lanes = list(manifest["lanes"])
    if audit.get("classification_counts") != {
        "completed_merge_eligible": len(lanes)
    }:
        raise ValueError(f"Not every lane is merge-eligible for {round_id}")
    if int(audit.get("planned_rows", -1)) != int(manifest["selected_rows"]):
        raise ValueError(f"Audit planned-row mismatch for {round_id}")
    if int(audit.get("ledger_rows", -1)) != int(manifest["selected_rows"]):
        raise ValueError(f"Audit ledger-row mismatch for {round_id}")
    if int(audit.get("terminal_rows", -1)) != int(manifest["selected_rows"]):
        raise ValueError(f"Audit terminal-row mismatch for {round_id}")
    if int(audit.get("cross_lane_duplicate_triage_ids", -1)) != 0:
        raise ValueError(f"Audit contains duplicate triage IDs for {round_id}")
    if int(audit.get("cross_lane_duplicate_candidate_queue_ids", -1)) != 0:
        raise ValueError(
            f"Audit contains duplicate candidate IDs for {round_id}"
        )
    for field in ACCESS_FIELDS:
        if int(audit.get(field, 0)) != 0:
            raise ValueError(
                f"Unsafe nonzero {field} in {audit_path} for {round_id}"
            )


def validate_lane(
    manifest: dict[str, Any],
    lane: dict[str, Any],
) -> tuple[list[str], list[dict[str, str]], dict[str, Any]]:
    round_id = str(manifest["round_id"])
    lane_id = str(lane["lane_id"])
    expected_rows = int(lane["expected_rows"])
    input_path = Path(str(lane["input_csv"]))
    if sha256_file(input_path) != str(lane["input_sha256"]):
        raise ValueError(f"Input hash mismatch: {round_id}/{lane_id}")
    _, input_rows = read_csv(input_path)
    if len(input_rows) != expected_rows:
        raise ValueError(f"Input row mismatch: {round_id}/{lane_id}")

    output_dir = lane_output_dir(manifest, lane)
    ledger_path = output_dir / "triage_ledger.csv"
    summary_path = output_dir / "triage_summary.json"
    timing_path = output_dir / "triage_timing.csv"
    for required in (ledger_path, summary_path, timing_path):
        if not required.exists():
            raise ValueError(f"Required lane artifact missing: {required}")

    fieldnames, rows = read_csv(ledger_path)
    summary = read_json(summary_path)
    if len(rows) != expected_rows:
        raise ValueError(f"Lane ledger row mismatch: {round_id}/{lane_id}")
    if summary.get("status") != "metadata_only_completed":
        raise ValueError(f"Lane is not metadata-only complete: {round_id}/{lane_id}")
    for field in ACCESS_FIELDS:
        if int(summary.get(field, 0)) != 0:
            raise ValueError(
                f"Unsafe nonzero {field}: {round_id}/{lane_id}"
            )

    input_by_triage = {row["triage_id"]: row for row in input_rows}
    if len(input_by_triage) != expected_rows:
        raise ValueError(f"Duplicate input triage ID: {round_id}/{lane_id}")
    input_queue_ids = {
        row["candidate_queue_row_id"] for row in input_rows
    }
    if len(input_queue_ids) != expected_rows:
        raise ValueError(f"Duplicate input candidate ID: {round_id}/{lane_id}")

    triage_ids = [row.get("triage_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if len(set(triage_ids)) != expected_rows or "" in triage_ids:
        raise ValueError(f"Duplicate/blank ledger triage ID: {round_id}/{lane_id}")
    if len(set(queue_ids)) != expected_rows or "" in queue_ids:
        raise ValueError(
            f"Duplicate/blank ledger candidate ID: {round_id}/{lane_id}"
        )
    if set(triage_ids) != set(input_by_triage):
        raise ValueError(f"Input/ledger triage identity mismatch: {round_id}/{lane_id}")
    if set(queue_ids) != input_queue_ids:
        raise ValueError(
            f"Input/ledger candidate identity mismatch: {round_id}/{lane_id}"
        )

    for row in rows:
        if row.get("triage_status") not in TERMINAL_TRIAGE_STATUSES:
            raise ValueError(
                f"Nonterminal triage status in {round_id}/{lane_id}: "
                f"{row.get('triage_status')}"
            )
        input_row = input_by_triage[row["triage_id"]]
        for field in IMMUTABLE_INPUT_FIELDS:
            if row.get(field, "") != input_row.get(field, ""):
                raise ValueError(
                    f"Input metadata changed in {round_id}/{lane_id}: {field}"
                )
        if row.get("triage_stage") != (
            "metadata_only_triaged_not_content_reviewed"
        ):
            raise ValueError(
                f"Unexpected triage stage in {round_id}/{lane_id}"
            )
        if row.get("reviewer") != "script_metadata_only":
            raise ValueError(f"Unexpected reviewer in {round_id}/{lane_id}")

    return fieldnames, rows, {
        "lane_id": lane_id,
        "ledger_path": ledger_path.as_posix(),
        "ledger_sha256": sha256_file(ledger_path),
        "summary_path": summary_path.as_posix(),
        "summary_sha256": sha256_file(summary_path),
        "timing_path": timing_path.as_posix(),
        "timing_sha256": sha256_file(timing_path),
        "rows": len(rows),
        **zero_access_counts(),
    }


def write_csv_atomic(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def format_counts(counts: dict[str, int]) -> list[str]:
    return [f"- `{key}`: {value:,}" for key, value in counts.items()]


def merge(
    *,
    manifest_paths: list[Path],
    audit_paths: list[Path],
    routing_ledger_path: Path,
    output_dir: Path,
    merge_id: str,
    merged_at: str | None = None,
) -> dict[str, Any]:
    if not manifest_paths:
        raise ValueError("At least one manifest is required")
    if len(manifest_paths) != len(audit_paths):
        raise ValueError("Each manifest requires one matching audit summary")
    if not merge_id.strip():
        raise ValueError("A nonblank merge ID is required")

    output_paths = {
        "ledger": output_dir / LEDGER_NAME,
        "summary": output_dir / SUMMARY_NAME,
        "audit": output_dir / AUDIT_NAME,
        "latest_ledger": output_dir / LATEST_LEDGER_NAME,
        "latest_summary": output_dir / LATEST_SUMMARY_NAME,
    }
    existing = [path for path in output_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing durable content-triage outputs: "
            + ", ".join(path.as_posix() for path in existing)
        )

    routing_fields, routing_rows = read_csv(routing_ledger_path)
    if "candidate_queue_row_id" not in routing_fields:
        raise ValueError("Routing ledger lacks candidate_queue_row_id")
    routing_ids = [
        row.get("candidate_queue_row_id", "") for row in routing_rows
    ]
    if "" in routing_ids or len(routing_ids) != len(set(routing_ids)):
        raise ValueError("Routing ledger candidate identities are blank/duplicate")

    timestamp = merged_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    merged_rows: list[dict[str, str]] = []
    source_rounds: list[dict[str, Any]] = []
    base_fieldnames: list[str] | None = None

    for manifest_path, audit_path in zip(manifest_paths, audit_paths):
        manifest = read_json(manifest_path)
        audit = read_json(audit_path)
        validate_audit(manifest, audit, audit_path)
        round_id = str(manifest["round_id"])
        round_rows = 0
        lane_sources: list[dict[str, Any]] = []
        for lane in manifest["lanes"]:
            fieldnames, rows, lane_source = validate_lane(manifest, lane)
            if base_fieldnames is None:
                base_fieldnames = fieldnames
            elif fieldnames != base_fieldnames:
                raise ValueError(
                    f"Lane ledger schema mismatch in {round_id}/{lane['lane_id']}"
                )
            for row in rows:
                enriched = dict(row)
                enriched.update(zero_access_counts())
                enriched.update(
                    {
                        "content_triage_round_id": round_id,
                        "content_triage_merge_id": merge_id,
                        "content_triage_merged_at": timestamp,
                        "content_triage_lane_id": str(lane["lane_id"]),
                        "content_triage_stage": (
                            "metadata_only_triaged_not_content_reviewed"
                        ),
                    }
                )
                merged_rows.append(enriched)
            round_rows += len(rows)
            lane_sources.append(lane_source)
        if round_rows != int(manifest["selected_rows"]):
            raise ValueError(f"Round row mismatch after validation: {round_id}")
        source_rounds.append(
            {
                "round_id": round_id,
                "manifest_path": manifest_path.as_posix(),
                "manifest_sha256": sha256_file(manifest_path),
                "audit_summary_path": audit_path.as_posix(),
                "audit_summary_sha256": sha256_file(audit_path),
                "rows": round_rows,
                "lane_count": len(manifest["lanes"]),
                "merge_recommendation": audit["merge_recommendation"],
                "lanes": lane_sources,
            }
        )

    if base_fieldnames is None:
        raise ValueError("No lane ledger schema was found")
    triage_ids = [row["triage_id"] for row in merged_rows]
    queue_ids = [row["candidate_queue_row_id"] for row in merged_rows]
    if len(triage_ids) != len(set(triage_ids)):
        raise ValueError("Duplicate triage IDs across rounds")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Duplicate candidate queue IDs across rounds")
    if set(queue_ids) != set(routing_ids):
        missing = len(set(routing_ids) - set(queue_ids))
        extra = len(set(queue_ids) - set(routing_ids))
        raise ValueError(
            "Merged/routing candidate identity mismatch: "
            f"missing={missing}, extra={extra}"
        )

    merged_rows.sort(
        key=lambda row: (row["candidate_queue_row_id"], row["triage_id"])
    )
    fieldnames = list(base_fieldnames)
    for field in (*ACCESS_FIELDS, *MERGE_FIELDS):
        if field not in fieldnames:
            fieldnames.append(field)

    summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "metadata_only_full_universe_merged",
        "content_triage_merge_id": merge_id,
        "content_triage_merged_at": timestamp,
        "content_triage_stage": (
            "metadata_only_triaged_not_content_reviewed"
        ),
        "ledger_rows": len(merged_rows),
        "terminal_rows": len(merged_rows),
        "unique_triage_ids": len(set(triage_ids)),
        "unique_candidate_queue_row_ids": len(set(queue_ids)),
        "routing_ledger_rows": len(routing_rows),
        "routing_identity_equality": True,
        "routing_ledger_path": routing_ledger_path.as_posix(),
        "routing_ledger_sha256": sha256_file(routing_ledger_path),
        "round_count": len(source_rounds),
        "lane_count": sum(item["lane_count"] for item in source_rounds),
        "source_rounds": source_rounds,
        "triage_status_counts": count_field(merged_rows, "triage_status"),
        "recommended_next_action_counts": count_field(
            merged_rows, "recommended_next_action"
        ),
        "extraction_readiness_prelim_counts": count_field(
            merged_rows, "extraction_readiness_prelim"
        ),
        "source_relevance_prelim_counts": count_field(
            merged_rows, "source_relevance_prelim"
        ),
        "priority_for_content_review_counts": count_field(
            merged_rows, "priority_for_content_review"
        ),
        "candidate_disposition_counts": count_field(
            merged_rows, "candidate_status_before_verification"
        ),
        "verification_status_counts": count_field(
            merged_rows, "verification_status"
        ),
        "source_type_counts": count_field(
            merged_rows, "candidate_source_type"
        ),
        "content_type_counts": count_field(merged_rows, "content_type"),
        "state_counts": count_field(merged_rows, "state"),
        "disposition_to_priority": cross_tab(
            merged_rows,
            "candidate_status_before_verification",
            "priority_for_content_review",
        ),
        "routing_status_to_triage_status": cross_tab(
            merged_rows, "verification_status", "triage_status"
        ),
        **zero_access_counts(),
        "content_download_status": "not_started",
        "source_rating_status": "not_started",
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "caveats": [
            "Metadata-only triage did not inspect source content.",
            "All relevance, match, document, wage, mechanism, and extraction-readiness fields remain preliminary scheduling signals.",
            "A content-review download recommendation is not evidence that a source is relevant or contains wage data.",
            "No URL was opened and no source was downloaded, parsed, OCRed, ingested, codified, or used for wage analysis.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        write_csv_atomic(output_paths["ledger"], fieldnames, merged_rows)
        summary["ledger_path"] = output_paths["ledger"].as_posix()
        summary["ledger_sha256"] = sha256_file(output_paths["ledger"])
        write_json_atomic(output_paths["summary"], summary)
        shutil.copyfile(output_paths["ledger"], output_paths["latest_ledger"])
        shutil.copyfile(output_paths["summary"], output_paths["latest_summary"])

        audit_lines = [
            "# Cumulative Metadata-Only Content-Triage Merge Audit",
            "",
            f"- Merge ID: `{merge_id}`",
            f"- Merged at: `{timestamp}`",
            f"- Source rounds: {len(source_rounds):,}",
            f"- Source lanes: {summary['lane_count']:,}",
            f"- Ledger/terminal rows: {len(merged_rows):,}",
            f"- Unique triage IDs: {len(set(triage_ids)):,}",
            f"- Unique candidate-queue IDs: {len(set(queue_ids)):,}",
            f"- Exact identity equality with routing ledger: `{summary['routing_identity_equality']}`",
            f"- URLs/network/downloads/parses/PDF parses/OCR/artifacts: `0/0/0/0/0/0/0`",
            "",
            "## Preliminary triage status counts",
            "",
            *format_counts(summary["triage_status_counts"]),
            "",
            "## Recommended next-action counts",
            "",
            *format_counts(summary["recommended_next_action_counts"]),
            "",
            "## Stage boundary",
            "",
            "This durable ledger records metadata-only scheduling outcomes. It",
            "does not establish source relevance, officialness, employer/unit",
            "match, content, extractability, wage data, wage gaps, or causal",
            "effects. No URL or document was accessed during this serial merge.",
            "",
        ]
        output_paths["audit"].write_text(
            "\n".join(audit_lines), encoding="utf-8"
        )
    except Exception:
        for path in output_paths.values():
            path.unlink(missing_ok=True)
        if output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--audit-summary", action="append", required=True)
    parser.add_argument("--routing-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merge-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = merge(
        manifest_paths=[Path(value) for value in args.manifest],
        audit_paths=[Path(value) for value in args.audit_summary],
        routing_ledger_path=Path(args.routing_ledger_csv),
        output_dir=Path(args.output_dir),
        merge_id=args.merge_id,
    )
    print(
        "Content-triage cumulative merge complete: "
        f"rows={summary['ledger_rows']}; "
        f"routing_identity_equality={summary['routing_identity_equality']}; "
        f"URLs opened={summary['urls_opened']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
