#!/usr/bin/env python3
"""Serially merge audited bounded source-review lanes into a durable ledger.

This command is deliberately offline. It reads a locked pilot manifest, an
explicit merge-eligible audit summary, and lane-local terminal ledgers. It
does not open URLs, download or parse documents, run OCR, update scout or
routing/triage accounting, ingest, codify, extract wages, or perform analysis.
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

from audit_source_review_lanes import LIVE_TERMINAL_STATUSES


MERGE_FIELDS = (
    "source_review_pilot_id",
    "source_review_merge_id",
    "source_review_merged_at",
    "source_review_lane_id",
    "source_review_stage",
)
MERGED_STAGE = "bounded_artifact_review_not_parsed"
ROUND_LEDGER_NAME = "source_review_ledger.csv"
ROUND_SUMMARY_NAME = "source_review_summary.json"
ROUND_AUDIT_NAME = "source_review_merge_audit.md"
LATEST_LEDGER_NAME = "source_review_ledger_latest.csv"
LATEST_SUMMARY_NAME = "source_review_summary_latest.json"
FORBIDDEN_COLLECTION_COUNTERS = (
    "documents_parsed",
    "pdfs_parsed",
    "ocr_runs",
)
IMMUTABLE_INPUT_FIELDS = (
    "source_review_id",
    "triage_id",
    "candidate_queue_row_id",
    "verification_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "final_url",
    "source_locator",
    "candidate_title",
    "candidate_source_type",
    "candidate_status_before_verification",
    "verification_status",
    "content_type",
    "triage_status",
    "priority_for_content_review",
    "recommended_next_action",
    "candidate_priority",
    "verification_round_id",
    "content_triage_round_id",
    "source_owner_type",
    "unit_type_scouted",
    "population",
    "matched_set_potential",
    "official_domain_signal",
    "duplicate_source_group_id",
    "duplicate_group_size",
    "duplicate_group_role_for_triage",
    "pilot_selection_rank",
    "source_review_lane_id",
    "pilot_selection_reason",
)


class SourceReviewMergeError(ValueError):
    """Raised when an offline serial merge gate does not pass."""


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SourceReviewMergeError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceReviewMergeError(f"Expected JSON object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def count_field(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(
        sorted(Counter(row.get(field, "") for row in rows).items())
    )


def cross_tab(
    rows: list[dict[str, str]], row_field: str, column_field: str
) -> dict[str, dict[str, int]]:
    result: dict[str, Counter[str]] = {}
    for row in rows:
        result.setdefault(row.get(row_field, ""), Counter())[
            row.get(column_field, "")
        ] += 1
    return {
        key: dict(sorted(counts.items()))
        for key, counts in sorted(result.items())
    }


def byte_distribution(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        try:
            value = int(row.get("content_byte_size") or 0)
        except ValueError as exc:
            raise SourceReviewMergeError(
                "Invalid content_byte_size in lane ledger"
            ) from exc
        if value == 0:
            bucket = "0"
        elif value <= 64 * 1024:
            bucket = "1_to_64_kib"
        elif value <= 1024 * 1024:
            bucket = "64_kib_to_1_mib"
        elif value <= 10 * 1024 * 1024:
            bucket = "1_to_10_mib"
        elif value <= 25 * 1024 * 1024:
            bucket = "10_to_25_mib"
        else:
            bucket = "over_25_mib"
        counts[bucket] += 1
    return dict(sorted(counts.items()))


def validate_unique_identities(rows: list[dict[str, str]]) -> None:
    review_ids = [row.get("source_review_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if "" in review_ids or len(review_ids) != len(set(review_ids)):
        raise SourceReviewMergeError(
            "Duplicate or blank source_review IDs across lanes"
        )
    if "" in queue_ids or len(queue_ids) != len(set(queue_ids)):
        raise SourceReviewMergeError(
            "Duplicate or blank candidate queue IDs across lanes"
        )


def validate_audit(
    *,
    manifest: dict[str, Any],
    audit: dict[str, Any],
    manifest_path: Path,
) -> None:
    pilot_id = str(manifest.get("pilot_id", ""))
    lanes = manifest.get("lanes")
    if not pilot_id or not isinstance(lanes, list) or not lanes:
        raise SourceReviewMergeError("Manifest lacks pilot identity or lanes")
    if audit.get("pilot_id") != pilot_id:
        raise SourceReviewMergeError("Audit pilot ID does not match manifest")
    if audit.get("manifest") != manifest_path.as_posix():
        raise SourceReviewMergeError(
            "Audit was not produced from the supplied manifest"
        )
    if audit.get("merge_recommendation") != "merge_all_source_review_lanes":
        raise SourceReviewMergeError(
            "Audit does not recommend merge_all_source_review_lanes"
        )
    if audit.get("classification_counts") != {
        "completed_merge_eligible": len(lanes)
    }:
        raise SourceReviewMergeError("Not every source-review lane is eligible")
    expected = sum(int(lane.get("expected_rows", 0)) for lane in lanes)
    for field in ("planned_rows", "ledger_rows", "terminal_rows"):
        if int(audit.get(field, -1)) != expected:
            raise SourceReviewMergeError(
                f"Audit {field} does not equal expected rows"
            )
    if int(audit.get("cross_lane_duplicate_source_review_ids", -1)) != 0:
        raise SourceReviewMergeError(
            "Audit reports duplicate source-review IDs"
        )
    if int(audit.get("cross_lane_duplicate_candidate_queue_ids", -1)) != 0:
        raise SourceReviewMergeError(
            "Audit reports duplicate candidate-queue IDs"
        )
    if not bool(audit.get("artifact_integrity_passed")):
        raise SourceReviewMergeError("Audit artifact integrity did not pass")
    for field in FORBIDDEN_COLLECTION_COUNTERS:
        if int(audit.get(field, -1)) != 0:
            raise SourceReviewMergeError(
                f"Audit records prohibited {field}"
            )
    if int(audit.get("content_sample_files", -1)) != 0:
        raise SourceReviewMergeError("Audit records content samples")
    if int(
        audit.get("source_review_status_counts", {}).get(
            "download_connection_error", 0
        )
    ):
        raise SourceReviewMergeError(
            "Operative retry audit contains connection errors"
        )
    audit_by_lane = {
        str(lane.get("lane_id")): lane
        for lane in audit.get("lanes", [])
        if isinstance(lane, dict)
    }
    for lane in lanes:
        lane_id = str(lane.get("lane_id", ""))
        lane_audit = audit_by_lane.get(lane_id)
        if not lane_audit:
            raise SourceReviewMergeError(f"Audit is missing {lane_id}")
        if lane_audit.get("classification") != "completed_merge_eligible":
            raise SourceReviewMergeError(f"{lane_id} is not merge-eligible")
        lane_expected = int(lane.get("expected_rows", 0))
        for field in ("ledger_rows", "terminal_rows"):
            if int(lane_audit.get(field, -1)) != lane_expected:
                raise SourceReviewMergeError(
                    f"{lane_id} audit {field} mismatch"
                )


def validate_lane(
    *,
    manifest: dict[str, Any],
    lane: dict[str, Any],
) -> tuple[list[str], list[dict[str, str]], dict[str, Any]]:
    pilot_id = str(manifest["pilot_id"])
    lane_id = str(lane["lane_id"])
    expected = int(lane["expected_rows"])
    input_path = Path(str(lane["input_csv"]))
    if sha256_file(input_path) != str(lane["input_sha256"]):
        raise SourceReviewMergeError(f"Input hash mismatch for {lane_id}")
    _, input_rows = read_csv(input_path)
    if len(input_rows) != expected:
        raise SourceReviewMergeError(f"Input row mismatch for {lane_id}")

    output_dir = Path(str(lane["future_live_output_dir"]))
    ledger_path = output_dir / "source_review_ledger.csv"
    summary_path = output_dir / "source_review_summary.json"
    timing_path = output_dir / "source_review_timing.csv"
    for path in (ledger_path, summary_path, timing_path):
        if not path.is_file():
            raise SourceReviewMergeError(
                f"Required lane artifact missing: {path}"
            )
    fieldnames, rows = read_csv(ledger_path)
    summary = read_json(summary_path)
    if len(rows) != expected:
        raise SourceReviewMergeError(f"Ledger row mismatch for {lane_id}")
    if summary.get("status") != "completed":
        raise SourceReviewMergeError(f"Lane summary is incomplete: {lane_id}")
    for field in FORBIDDEN_COLLECTION_COUNTERS:
        if int(summary.get(field, -1)) != 0:
            raise SourceReviewMergeError(
                f"{lane_id} summary records prohibited {field}"
            )
    for flag in (
        "ingestion_attempted",
        "codify_attempted",
        "wage_extraction_attempted",
    ):
        if bool(summary.get(flag)):
            raise SourceReviewMergeError(
                f"{lane_id} summary records prohibited {flag}"
            )

    input_by_id = {
        row["source_review_id"]: row for row in input_rows
    }
    if len(input_by_id) != expected:
        raise SourceReviewMergeError(
            f"Duplicate input source-review ID in {lane_id}"
        )
    input_queue_ids = {
        row["candidate_queue_row_id"] for row in input_rows
    }
    if len(input_queue_ids) != expected:
        raise SourceReviewMergeError(
            f"Duplicate input candidate ID in {lane_id}"
        )
    review_ids = [row.get("source_review_id", "") for row in rows]
    queue_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    if set(review_ids) != set(input_by_id) or len(set(review_ids)) != expected:
        raise SourceReviewMergeError(
            f"Input/ledger source-review identity mismatch in {lane_id}"
        )
    if set(queue_ids) != input_queue_ids or len(set(queue_ids)) != expected:
        raise SourceReviewMergeError(
            f"Input/ledger candidate identity mismatch in {lane_id}"
        )

    content_artifacts = 0
    metadata_artifacts = 0
    content_bytes = 0
    maximum_content_bytes = 0
    rows_with_hash = 0
    for row in rows:
        status = row.get("source_review_status", "")
        if status not in LIVE_TERMINAL_STATUSES:
            raise SourceReviewMergeError(
                f"Nonterminal source-review status in {lane_id}: {status}"
            )
        input_row = input_by_id[row["source_review_id"]]
        for field in IMMUTABLE_INPUT_FIELDS:
            if row.get(field, "") != input_row.get(field, ""):
                raise SourceReviewMergeError(
                    f"Input metadata changed in {lane_id}: {field}"
                )
        if row.get("source_review_lane_id") != lane_id:
            raise SourceReviewMergeError(
                f"Lane identity changed in {lane_id}"
            )
        if row.get("source_review_stage") != (
            "source_reviewed_artifact_metadata_only"
        ):
            raise SourceReviewMergeError(
                f"Unexpected live source-review stage in {lane_id}"
            )
        for field in FORBIDDEN_COLLECTION_COUNTERS:
            if int(row.get(field) or 0) != 0:
                raise SourceReviewMergeError(
                    f"Row records prohibited {field} in {lane_id}"
                )
        if row.get("content_sample_path"):
            raise SourceReviewMergeError(
                f"Content sample path present in {lane_id}"
            )

        metadata_path = Path(row.get("response_metadata_path", ""))
        if not metadata_path.is_file() or not is_within(
            metadata_path, output_dir
        ):
            raise SourceReviewMergeError(
                f"Missing or nonlocal metadata artifact in {lane_id}"
            )
        metadata_artifacts += 1

        raw_content_path = row.get("content_artifact_path", "")
        if raw_content_path:
            content_path = Path(raw_content_path)
            if not content_path.is_file() or not is_within(
                content_path, output_dir
            ):
                raise SourceReviewMergeError(
                    f"Missing or nonlocal content artifact in {lane_id}"
                )
            expected_hash = row.get("content_hash", "")
            if not expected_hash or sha256_file(content_path) != expected_hash:
                raise SourceReviewMergeError(
                    f"Content hash mismatch in {lane_id}"
                )
            try:
                expected_size = int(row.get("content_byte_size") or -1)
            except ValueError as exc:
                raise SourceReviewMergeError(
                    f"Invalid content size in {lane_id}"
                ) from exc
            if expected_size != content_path.stat().st_size:
                raise SourceReviewMergeError(
                    f"Content size mismatch in {lane_id}"
                )
            content_artifacts += 1
            rows_with_hash += 1
            content_bytes += expected_size
            maximum_content_bytes = max(
                maximum_content_bytes, expected_size
            )
        elif row.get("content_hash"):
            raise SourceReviewMergeError(
                f"Hash without content artifact in {lane_id}"
            )
        if status == "reviewed_metadata_and_artifact_saved" and not (
            raw_content_path and row.get("content_hash")
        ):
            raise SourceReviewMergeError(
                f"Successful row lacks artifact/hash in {lane_id}"
            )

    return fieldnames, rows, {
        "lane_id": lane_id,
        "input_path": input_path.as_posix(),
        "input_sha256": sha256_file(input_path),
        "output_dir": output_dir.as_posix(),
        "ledger_path": ledger_path.as_posix(),
        "ledger_sha256": sha256_file(ledger_path),
        "summary_path": summary_path.as_posix(),
        "summary_sha256": sha256_file(summary_path),
        "timing_path": timing_path.as_posix(),
        "timing_sha256": sha256_file(timing_path),
        "rows": len(rows),
        "content_artifacts": content_artifacts,
        "metadata_artifacts": metadata_artifacts,
        "content_bytes": content_bytes,
        "maximum_content_bytes": maximum_content_bytes,
        "rows_with_content_hash": rows_with_hash,
        "documents_parsed": 0,
        "pdfs_parsed": 0,
        "ocr_runs": 0,
        "content_samples": 0,
        "pilot_id": pilot_id,
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
    manifest_path: Path,
    audit_path: Path,
    output_dir: Path,
    pilot_id: str,
    merge_id: str,
    merged_at: str | None = None,
) -> dict[str, Any]:
    if not pilot_id.strip() or not merge_id.strip():
        raise SourceReviewMergeError(
            "Nonblank pilot and merge IDs are required"
        )
    parent_dir = output_dir.parent
    output_paths = {
        "ledger": output_dir / ROUND_LEDGER_NAME,
        "summary": output_dir / ROUND_SUMMARY_NAME,
        "audit": output_dir / ROUND_AUDIT_NAME,
        "latest_ledger": parent_dir / LATEST_LEDGER_NAME,
        "latest_summary": parent_dir / LATEST_SUMMARY_NAME,
    }
    existing = [path for path in output_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing durable source-review outputs: "
            + ", ".join(path.as_posix() for path in existing)
        )

    manifest = read_json(manifest_path)
    audit = read_json(audit_path)
    if manifest.get("pilot_id") != pilot_id:
        raise SourceReviewMergeError(
            "Manifest pilot ID does not match --pilot-id"
        )
    validate_audit(
        manifest=manifest,
        audit=audit,
        manifest_path=manifest_path,
    )

    timestamp = merged_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    merged_rows: list[dict[str, str]] = []
    sources: list[dict[str, Any]] = []
    base_fields: list[str] | None = None
    for lane in manifest["lanes"]:
        fieldnames, rows, source = validate_lane(
            manifest=manifest,
            lane=lane,
        )
        if base_fields is None:
            base_fields = fieldnames
        elif fieldnames != base_fields:
            raise SourceReviewMergeError("Lane ledger schemas do not match")
        for row in rows:
            enriched = dict(row)
            enriched.update(
                {
                    "source_review_pilot_id": pilot_id,
                    "source_review_merge_id": merge_id,
                    "source_review_merged_at": timestamp,
                    "source_review_lane_id": str(lane["lane_id"]),
                    "source_review_stage": MERGED_STAGE,
                }
            )
            merged_rows.append(enriched)
        sources.append(source)

    if base_fields is None:
        raise SourceReviewMergeError("No source-review ledger schema found")
    expected_rows = int(manifest["selected_rows"])
    if len(merged_rows) != expected_rows:
        raise SourceReviewMergeError(
            "Merged ledger row count does not equal manifest selection"
        )
    validate_unique_identities(merged_rows)
    merged_rows.sort(
        key=lambda row: (
            row.get("source_review_lane_id", ""),
            int(row.get("pilot_selection_rank") or 0),
            row.get("source_review_id", ""),
        )
    )

    fields = list(base_fields)
    for field in MERGE_FIELDS:
        if field not in fields:
            fields.append(field)

    content_sizes = [
        int(row.get("content_byte_size") or 0) for row in merged_rows
    ]
    content_artifact_count = sum(
        bool(row.get("content_artifact_path")) for row in merged_rows
    )
    metadata_artifact_count = sum(
        bool(row.get("response_metadata_path")) for row in merged_rows
    )
    rows_with_hash = sum(
        bool(row.get("content_hash")) for row in merged_rows
    )
    content_bytes = sum(content_sizes)
    maximum_content_bytes = max(content_sizes, default=0)
    summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "pilot1_httpx_merged",
        "source_review_pilot_id": pilot_id,
        "source_review_merge_id": merge_id,
        "source_review_merged_at": timestamp,
        "source_review_stage": MERGED_STAGE,
        "ledger_rows": len(merged_rows),
        "terminal_rows": len(merged_rows),
        "unique_source_review_ids": len(
            {row["source_review_id"] for row in merged_rows}
        ),
        "unique_candidate_queue_row_ids": len(
            {row["candidate_queue_row_id"] for row in merged_rows}
        ),
        "lane_count": len(manifest["lanes"]),
        "lane_rows": {
            source["lane_id"]: source["rows"] for source in sources
        },
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "audit_summary_path": audit_path.as_posix(),
        "audit_summary_sha256": sha256_file(audit_path),
        "audit_merge_recommendation": audit["merge_recommendation"],
        "sources": sources,
        "source_review_status_counts": count_field(
            merged_rows, "source_review_status"
        ),
        "url_access_status_counts": count_field(
            merged_rows, "url_access_status"
        ),
        "download_status_counts": count_field(
            merged_rows, "download_status"
        ),
        "content_type_observed_counts": count_field(
            merged_rows, "content_type_observed"
        ),
        "content_byte_size_distribution": byte_distribution(merged_rows),
        "content_artifact_count": content_artifact_count,
        "metadata_artifact_count": metadata_artifact_count,
        "rows_with_content_hash": rows_with_hash,
        "rows_with_matching_content_hash": rows_with_hash,
        "content_artifact_bytes": content_bytes,
        "maximum_content_artifact_bytes": maximum_content_bytes,
        "content_sample_count": sum(
            bool(row.get("content_sample_path")) for row in merged_rows
        ),
        "source_officialness_rating_counts": count_field(
            merged_rows, "source_officialness_rating"
        ),
        "source_relevance_rating_counts": count_field(
            merged_rows, "source_relevance_rating"
        ),
        "municipality_match_rating_counts": count_field(
            merged_rows, "municipality_match_rating"
        ),
        "employer_match_rating_counts": count_field(
            merged_rows, "employer_match_rating"
        ),
        "bargaining_unit_match_rating_counts": count_field(
            merged_rows, "bargaining_unit_match_rating"
        ),
        "safety_unit_match_signal_counts": count_field(
            merged_rows, "safety_unit_match_signal"
        ),
        "non_safety_unit_match_signal_counts": count_field(
            merged_rows, "non_safety_unit_match_signal"
        ),
        "document_type_rating_counts": count_field(
            merged_rows, "document_type_rating"
        ),
        "extraction_readiness_rating_counts": count_field(
            merged_rows, "extraction_readiness_rating"
        ),
        "wage_table_signal_counts": count_field(
            merged_rows, "wage_table_signal"
        ),
        "wage_growth_signal_counts": count_field(
            merged_rows, "wage_growth_signal"
        ),
        "mechanism_language_signal_counts": count_field(
            merged_rows, "mechanism_language_signal"
        ),
        "candidate_disposition_counts": count_field(
            merged_rows, "candidate_status_before_verification"
        ),
        "state_counts": count_field(merged_rows, "state"),
        "source_type_counts": count_field(
            merged_rows, "candidate_source_type"
        ),
        "unit_type_counts": count_field(
            merged_rows, "unit_type_scouted"
        ),
        "disposition_to_extraction_readiness": cross_tab(
            merged_rows,
            "candidate_status_before_verification",
            "extraction_readiness_rating",
        ),
        "routing_status_to_review_status": cross_tab(
            merged_rows, "verification_status", "source_review_status"
        ),
        "collection_urls_opened": sum(
            int(row.get("urls_opened") or 0) for row in merged_rows
        ),
        "collection_network_calls": sum(
            int(row.get("network_calls") or 0) for row in merged_rows
        ),
        "collection_documents_downloaded": sum(
            int(row.get("documents_downloaded") or 0)
            for row in merged_rows
        ),
        "collection_documents_parsed": 0,
        "collection_pdfs_parsed": 0,
        "collection_ocr_runs": 0,
        "merge_urls_opened": 0,
        "merge_network_calls": 0,
        "merge_documents_downloaded": 0,
        "merge_documents_parsed": 0,
        "merge_pdfs_parsed": 0,
        "merge_ocr_runs": 0,
        "original_failed_attempt_status": (
            "preserved_unmerged_superseded_transport"
        ),
        "diagnostic_probe_status": "preserved_excluded_from_merge",
        "source_rating_status": "pilot1_preliminary_artifact_review_merged",
        "content_download_status": "pilot1_bounded_artifacts_merged",
        "extraction_readiness_status": (
            "pilot1_preliminary_artifact_metadata_only"
        ),
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "next_scaling_recommendation": "plan_500_after_relay_review",
        "caveats": [
            "Source-review ratings are preliminary access/artifact signals.",
            "PDFs were not parsed or OCRed.",
            "No wage tables or wage values were extracted.",
            "The original transport-failed attempt is superseded and excluded from operative results.",
            "The diagnostic probe is preserved and excluded from the durable ledger.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        write_csv_atomic(output_paths["ledger"], fields, merged_rows)
        summary["ledger_path"] = output_paths["ledger"].as_posix()
        summary["ledger_sha256"] = sha256_file(output_paths["ledger"])
        write_json_atomic(output_paths["summary"], summary)
        shutil.copyfile(
            output_paths["ledger"], output_paths["latest_ledger"]
        )
        shutil.copyfile(
            output_paths["summary"], output_paths["latest_summary"]
        )
        audit_lines = [
            "# Source-Review Pilot 1 HTTPX Merge Audit",
            "",
            f"- Pilot ID: `{pilot_id}`",
            f"- Merge ID: `{merge_id}`",
            f"- Merged at: `{timestamp}`",
            f"- Durable rows / terminal rows: {len(merged_rows):,} / {len(merged_rows):,}",
            f"- Unique source-review IDs: {summary['unique_source_review_ids']:,}",
            f"- Unique candidate-queue IDs: {summary['unique_candidate_queue_row_ids']:,}",
            f"- Content artifacts / hashes: {content_artifact_count:,} / {rows_with_hash:,}",
            f"- Content bytes / maximum: {content_bytes:,} / {maximum_content_bytes:,}",
            f"- Audit recommendation: `{audit['merge_recommendation']}`",
            "- Merge URL/network/download/parse/PDF/OCR counts: `0/0/0/0/0/0`",
            "",
            "## Source-review status counts",
            "",
            *format_counts(summary["source_review_status_counts"]),
            "",
            "## Preliminary extraction-readiness counts",
            "",
            *format_counts(summary["extraction_readiness_rating_counts"]),
            "",
            "## Operative provenance",
            "",
            "Only the repaired HTTPX retry lane ledgers listed in the source",
            "summary were merged. The original transport-failed attempt remains",
            "preserved as superseded diagnostic provenance. The ten-row probe",
            "also remains preserved and is not part of this durable ledger.",
            "",
            "## Stage boundary",
            "",
            "This ledger records bounded artifact access and preliminary ratings.",
            "It does not establish final relevance, officialness, employer/unit",
            "match, document identity, wage content, wage gaps, or causal effects.",
            "No URL or document was accessed during this offline serial merge.",
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
        if parent_dir.exists() and not any(parent_dir.iterdir()):
            parent_dir.rmdir()
        raise
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--audit-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pilot-id", required=True)
    parser.add_argument("--merge-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = merge(
        manifest_path=Path(args.manifest),
        audit_path=Path(args.audit_summary),
        output_dir=Path(args.output_dir),
        pilot_id=args.pilot_id,
        merge_id=args.merge_id,
    )
    print(
        "Source-review serial merge complete: "
        f"rows={summary['ledger_rows']}; "
        f"artifacts={summary['content_artifact_count']}; "
        f"merge URLs opened={summary['merge_urls_opened']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
