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
CUMULATIVE_LEDGER_NAME = "source_review_ledger_cumulative.csv"
CUMULATIVE_SUMMARY_NAME = "source_review_summary_cumulative.json"
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


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    content_sizes = [
        int(row.get("content_byte_size") or 0) for row in rows
    ]
    return {
        "ledger_rows": len(rows),
        "terminal_rows": len(rows),
        "unique_source_review_ids": len(
            {row["source_review_id"] for row in rows}
        ),
        "unique_candidate_queue_row_ids": len(
            {row["candidate_queue_row_id"] for row in rows}
        ),
        "source_review_status_counts": count_field(
            rows, "source_review_status"
        ),
        "url_access_status_counts": count_field(rows, "url_access_status"),
        "download_status_counts": count_field(rows, "download_status"),
        "content_type_observed_counts": count_field(
            rows, "content_type_observed"
        ),
        "content_byte_size_distribution": byte_distribution(rows),
        "content_artifact_count": sum(
            bool(row.get("content_artifact_path")) for row in rows
        ),
        "metadata_artifact_count": sum(
            bool(row.get("response_metadata_path")) for row in rows
        ),
        "rows_with_content_hash": sum(
            bool(row.get("content_hash")) for row in rows
        ),
        "rows_with_matching_content_hash": sum(
            bool(row.get("content_hash")) for row in rows
        ),
        "content_artifact_bytes": sum(content_sizes),
        "maximum_content_artifact_bytes": max(content_sizes, default=0),
        "content_sample_count": sum(
            bool(row.get("content_sample_path")) for row in rows
        ),
        "source_officialness_rating_counts": count_field(
            rows, "source_officialness_rating"
        ),
        "source_relevance_rating_counts": count_field(
            rows, "source_relevance_rating"
        ),
        "municipality_match_rating_counts": count_field(
            rows, "municipality_match_rating"
        ),
        "employer_match_rating_counts": count_field(
            rows, "employer_match_rating"
        ),
        "bargaining_unit_match_rating_counts": count_field(
            rows, "bargaining_unit_match_rating"
        ),
        "safety_unit_match_signal_counts": count_field(
            rows, "safety_unit_match_signal"
        ),
        "non_safety_unit_match_signal_counts": count_field(
            rows, "non_safety_unit_match_signal"
        ),
        "document_type_rating_counts": count_field(
            rows, "document_type_rating"
        ),
        "extraction_readiness_rating_counts": count_field(
            rows, "extraction_readiness_rating"
        ),
        "wage_table_signal_counts": count_field(
            rows, "wage_table_signal"
        ),
        "wage_growth_signal_counts": count_field(
            rows, "wage_growth_signal"
        ),
        "mechanism_language_signal_counts": count_field(
            rows, "mechanism_language_signal"
        ),
        "candidate_disposition_counts": count_field(
            rows, "candidate_status_before_verification"
        ),
        "state_counts": count_field(rows, "state"),
        "source_type_counts": count_field(rows, "candidate_source_type"),
        "unit_type_counts": count_field(rows, "unit_type_scouted"),
        "disposition_to_extraction_readiness": cross_tab(
            rows,
            "candidate_status_before_verification",
            "extraction_readiness_rating",
        ),
        "routing_status_to_review_status": cross_tab(
            rows, "verification_status", "source_review_status"
        ),
        "collection_urls_opened": sum(
            int(row.get("urls_opened") or 0) for row in rows
        ),
        "collection_network_calls": sum(
            int(row.get("network_calls") or 0) for row in rows
        ),
        "collection_documents_downloaded": sum(
            int(row.get("documents_downloaded") or 0) for row in rows
        ),
        "collection_documents_parsed": 0,
        "collection_pdfs_parsed": 0,
        "collection_ocr_runs": 0,
    }


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


def validate_prior_durable_rows(
    *,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    if not rows:
        raise SourceReviewMergeError("Prior durable source-review ledger is empty")
    validate_unique_identities(rows)
    for row in rows:
        if row.get("source_review_stage") != MERGED_STAGE:
            raise SourceReviewMergeError(
                "Prior durable row has an unexpected source-review stage"
            )
        if row.get("source_review_status", "") not in LIVE_TERMINAL_STATUSES:
            raise SourceReviewMergeError(
                "Prior durable row has a nonterminal status"
            )
        for field in FORBIDDEN_COLLECTION_COUNTERS:
            if int(row.get(field) or 0) != 0:
                raise SourceReviewMergeError(
                    f"Prior durable row records prohibited {field}"
                )
        if row.get("content_sample_path"):
            raise SourceReviewMergeError(
                "Prior durable row contains a content sample"
            )
        raw_content_path = row.get("content_artifact_path", "")
        if raw_content_path:
            content_path = Path(raw_content_path)
            if not content_path.is_file():
                raise SourceReviewMergeError(
                    "Prior durable content artifact is missing"
                )
            expected_hash = row.get("content_hash", "")
            if not expected_hash or sha256_file(content_path) != expected_hash:
                raise SourceReviewMergeError(
                    "Prior durable content hash does not match"
                )
            if content_path.stat().st_size != int(
                row.get("content_byte_size") or -1
            ):
                raise SourceReviewMergeError(
                    "Prior durable content size does not match"
                )
        elif row.get("content_hash"):
            raise SourceReviewMergeError(
                "Prior durable hash lacks an artifact path"
            )
    required = set(MERGE_FIELDS)
    if not required.issubset(fields):
        raise SourceReviewMergeError(
            "Prior durable ledger lacks merge metadata fields"
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


def copy_file_atomic(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def format_counts(counts: dict[str, int]) -> list[str]:
    return [f"- `{key}`: {value:,}" for key, value in counts.items()]


def merge(
    *,
    manifest_path: Path,
    audit_path: Path,
    output_dir: Path,
    pilot_id: str,
    merge_id: str,
    prior_ledger_path: Path | None = None,
    prior_summary_path: Path | None = None,
    merged_at: str | None = None,
) -> dict[str, Any]:
    if not pilot_id.strip() or not merge_id.strip():
        raise SourceReviewMergeError(
            "Nonblank pilot and merge IDs are required"
        )
    if (prior_ledger_path is None) != (prior_summary_path is None):
        raise SourceReviewMergeError(
            "Prior durable ledger and summary must be supplied together"
        )
    parent_dir = output_dir.parent
    output_paths = {
        "ledger": output_dir / ROUND_LEDGER_NAME,
        "summary": output_dir / ROUND_SUMMARY_NAME,
        "audit": output_dir / ROUND_AUDIT_NAME,
        "cumulative_ledger": parent_dir / CUMULATIVE_LEDGER_NAME,
        "cumulative_summary": parent_dir / CUMULATIVE_SUMMARY_NAME,
        "latest_ledger": parent_dir / LATEST_LEDGER_NAME,
        "latest_summary": parent_dir / LATEST_SUMMARY_NAME,
    }
    round_or_cumulative = (
        output_paths["ledger"],
        output_paths["summary"],
        output_paths["audit"],
        output_paths["cumulative_ledger"],
        output_paths["cumulative_summary"],
    )
    existing = [path for path in round_or_cumulative if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing durable source-review outputs: "
            + ", ".join(path.as_posix() for path in existing)
        )
    latest_paths = (
        output_paths["latest_ledger"],
        output_paths["latest_summary"],
    )
    prior_latest_bytes: dict[Path, bytes] = {}
    prior_fields: list[str] | None = None
    prior_rows: list[dict[str, str]] = []
    if prior_ledger_path is None:
        existing_latest = [path for path in latest_paths if path.exists()]
        if existing_latest:
            raise FileExistsError(
                "Existing latest source-review pointers require explicit "
                "--prior-ledger-csv and --prior-summary-json: "
                + ", ".join(path.as_posix() for path in existing_latest)
            )
    else:
        assert prior_summary_path is not None
        for path in (
            prior_ledger_path,
            prior_summary_path,
            *latest_paths,
        ):
            if not path.is_file():
                raise SourceReviewMergeError(
                    f"Required prior durable source-review file is missing: {path}"
                )
        if (
            prior_ledger_path.read_bytes()
            != output_paths["latest_ledger"].read_bytes()
        ):
            raise SourceReviewMergeError(
                "Existing latest ledger does not equal the explicit prior ledger"
            )
        if (
            prior_summary_path.read_bytes()
            != output_paths["latest_summary"].read_bytes()
        ):
            raise SourceReviewMergeError(
                "Existing latest summary does not equal the explicit prior summary"
            )
        prior_fields, prior_rows = read_csv(prior_ledger_path)
        validate_prior_durable_rows(fields=prior_fields, rows=prior_rows)
        prior_latest_bytes = {
            path: path.read_bytes() for path in latest_paths
        }

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
    if prior_fields is not None and prior_fields != fields:
        raise SourceReviewMergeError(
            "Prior and current durable source-review schemas do not match"
        )
    cumulative_rows = [dict(row) for row in prior_rows] + [
        dict(row) for row in merged_rows
    ]
    validate_unique_identities(cumulative_rows)
    cumulative_rows.sort(
        key=lambda row: (
            row.get("source_review_pilot_id", ""),
            row.get("source_review_lane_id", ""),
            int(row.get("pilot_selection_rank") or 0),
            row.get("source_review_id", ""),
        )
    )

    is_batch2 = (
        pilot_id == "SOURCE-REVIEW-BATCH2-500-2026-07-24"
        and merge_id == "SOURCE-REVIEW-BATCH2-500-MERGE-2026-07-24"
    )
    round_metrics = summarize_rows(merged_rows)
    cumulative_metrics = summarize_rows(cumulative_rows)
    summary: dict[str, Any] = {
        "schema_version": "1.1.0",
        "status": "batch2_500_merged" if is_batch2 else "source_review_batch_merged",
        "source_review_pilot_id": pilot_id,
        "source_review_merge_id": merge_id,
        "source_review_merged_at": timestamp,
        "source_review_stage": MERGED_STAGE,
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
        **round_metrics,
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
        "source_rating_status": (
            "batch2_preliminary_artifact_review_merged"
            if is_batch2
            else "preliminary_artifact_review_merged"
        ),
        "content_download_status": (
            "batch2_bounded_artifacts_merged"
            if is_batch2
            else "bounded_artifacts_merged"
        ),
        "extraction_readiness_status": "preliminary_artifact_metadata_only",
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "next_scaling_recommendation": (
            "prepare_batch3_1000"
            if is_batch2
            else "review_before_next_scale"
        ),
        "caveats": [
            "Source-review ratings are preliminary access/artifact signals.",
            "PDFs were not parsed or OCRed.",
            "No wage tables or wage values were extracted.",
            "This round ledger contains only the audited lane outputs named in its manifest.",
        ],
    }
    cumulative_summary: dict[str, Any] = {
        "schema_version": "1.1.0",
        "status": "source_review_cumulative_merged",
        "latest_source_review_pilot_id": pilot_id,
        "latest_source_review_merge_id": merge_id,
        "source_review_merged_at": timestamp,
        "source_review_stage": MERGED_STAGE,
        "merged_batch_count": len(
            {row["source_review_pilot_id"] for row in cumulative_rows}
        ),
        "merged_batch_rows": count_field(
            cumulative_rows, "source_review_pilot_id"
        ),
        "merged_merge_ids": count_field(
            cumulative_rows, "source_review_merge_id"
        ),
        "prior_ledger_path": (
            prior_ledger_path.as_posix()
            if prior_ledger_path is not None
            else None
        ),
        "prior_ledger_sha256": (
            sha256_file(prior_ledger_path)
            if prior_ledger_path is not None
            else None
        ),
        "latest_round_ledger_path": output_paths["ledger"].as_posix(),
        "latest_round_summary_path": output_paths["summary"].as_posix(),
        **cumulative_metrics,
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
        "source_rating_status": "batch2_preliminary_artifact_review_merged",
        "content_download_status": "batch2_bounded_artifacts_merged",
        "extraction_readiness_status": "preliminary_artifact_metadata_only",
        "ingestion_status": "not_started",
        "codify_status": "not_started",
        "wage_extraction_status": "not_started",
        "wage_gap_analysis_status": "not_started",
        "next_scaling_recommendation": (
            "prepare_batch3_1000"
            if is_batch2
            else "review_before_next_scale"
        ),
        "caveats": [
            "Source-review ratings are preliminary access/artifact signals.",
            "PDFs were not parsed or OCRed.",
            "No wage tables or wage values were extracted.",
            "Latest pointers represent the full cumulative durable layer.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        write_csv_atomic(output_paths["ledger"], fields, merged_rows)
        summary["ledger_path"] = output_paths["ledger"].as_posix()
        summary["ledger_sha256"] = sha256_file(output_paths["ledger"])
        write_json_atomic(output_paths["summary"], summary)
        write_csv_atomic(
            output_paths["cumulative_ledger"], fields, cumulative_rows
        )
        cumulative_summary["ledger_path"] = output_paths[
            "cumulative_ledger"
        ].as_posix()
        cumulative_summary["ledger_sha256"] = sha256_file(
            output_paths["cumulative_ledger"]
        )
        cumulative_summary["latest_ledger_path"] = output_paths[
            "latest_ledger"
        ].as_posix()
        cumulative_summary["latest_summary_path"] = output_paths[
            "latest_summary"
        ].as_posix()
        write_json_atomic(
            output_paths["cumulative_summary"], cumulative_summary
        )
        copy_file_atomic(
            output_paths["cumulative_ledger"],
            output_paths["latest_ledger"],
        )
        copy_file_atomic(
            output_paths["cumulative_summary"],
            output_paths["latest_summary"],
        )
        audit_lines = [
            f"# Source-Review Merge Audit: {pilot_id}",
            "",
            f"- Pilot ID: `{pilot_id}`",
            f"- Merge ID: `{merge_id}`",
            f"- Merged at: `{timestamp}`",
            f"- Durable rows / terminal rows: {len(merged_rows):,} / {len(merged_rows):,}",
            f"- Unique source-review IDs: {summary['unique_source_review_ids']:,}",
            f"- Unique candidate-queue IDs: {summary['unique_candidate_queue_row_ids']:,}",
            f"- Content artifacts / hashes: {summary['content_artifact_count']:,} / {summary['rows_with_content_hash']:,}",
            f"- Content bytes / maximum: {summary['content_artifact_bytes']:,} / {summary['maximum_content_artifact_bytes']:,}",
            f"- Cumulative durable rows: {cumulative_summary['ledger_rows']:,}",
            f"- Cumulative content artifacts: {cumulative_summary['content_artifact_count']:,}",
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
            "Only the audited lane ledgers listed in the round summary were",
            "merged into this round. Any explicit prior durable ledger was",
            "validated, kept unchanged, and combined only in the cumulative",
            "ledger. No diagnostic or superseded attempt was read as a merge",
            "input.",
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
        for key, path in output_paths.items():
            if key in ("latest_ledger", "latest_summary"):
                if path in prior_latest_bytes:
                    path.write_bytes(prior_latest_bytes[path])
                else:
                    path.unlink(missing_ok=True)
            else:
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
    parser.add_argument(
        "--prior-ledger-csv",
        help=(
            "Explicit prior durable ledger; required when latest pointers "
            "already exist"
        ),
    )
    parser.add_argument(
        "--prior-summary-json",
        help=(
            "Explicit prior durable summary paired with --prior-ledger-csv"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = merge(
        manifest_path=Path(args.manifest),
        audit_path=Path(args.audit_summary),
        output_dir=Path(args.output_dir),
        pilot_id=args.pilot_id,
        merge_id=args.merge_id,
        prior_ledger_path=(
            Path(args.prior_ledger_csv)
            if args.prior_ledger_csv
            else None
        ),
        prior_summary_path=(
            Path(args.prior_summary_json)
            if args.prior_summary_json
            else None
        ),
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
