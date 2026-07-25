#!/usr/bin/env python3
"""Merge audited local text/table-detection lanes into one durable ledger.

This module is deliberately offline. It reads CSV/JSON/Markdown inputs only;
it never opens source PDFs, performs text extraction, calls a network service,
or mutates any upstream authority ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from text_table_detection_sources import TABLE_METHOD, TERMINAL_STATUSES


MERGE_FIELDS = [
    "text_table_detection_merge_id",
    "text_table_detection_merged_at",
    "text_table_detection_stage",
]
STAGE = "heuristic_text_table_detection_not_extracted"
OUTPUT_NAMES = {
    "ledger": "text_table_detection_ledger_cumulative.csv",
    "summary": "text_table_detection_summary_cumulative.json",
    "audit": "text_table_detection_merge_audit_cumulative.md",
    "latest_ledger": "text_table_detection_ledger_latest.csv",
    "latest_summary": "text_table_detection_summary_latest.json",
}
AUTHORITY_MATCH_FIELDS = (
    "source_review_id",
    "candidate_queue_row_id",
    "triage_id",
    "verification_id",
    "source_review_pilot_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "priority_for_content_review",
    "source_officialness_rating",
    "source_relevance_rating",
    "document_type_rating",
    "extraction_readiness_rating",
    "content_artifact_path",
    "content_hash",
    "content_byte_size",
    "content_type_observed",
    "pdf_page_count",
    "text_layer_status",
)
IDENTITY_FIELDS = (
    "text_table_detection_id",
    "pdf_readiness_id",
    "source_review_id",
    "candidate_queue_row_id",
)
AUDIT_ZERO_FIELDS = (
    "cross_lane_duplicate_text_table_detection_ids",
    "cross_lane_duplicate_pdf_readiness_ids",
    "cross_lane_duplicate_source_review_ids",
    "cross_lane_duplicate_candidate_queue_ids",
    "hash_failures",
    "missing_artifacts",
    "parser_errors",
    "heuristic_mismatches",
    "hint_overruns",
    "candidate_page_errors",
    "full_text_artifacts_found",
)
FORBIDDEN_AUDIT_FIELDS = (
    "urls_opened",
    "network_calls",
    "downloads",
    "redownloads",
    "ocr_runs",
    "full_text_artifacts_written",
    "final_wage_values_extracted",
    "ingestion_actions",
    "codify_actions",
    "durable_text_table_merges",
)


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def csv_bytes(fieldnames: list[str], rows: list[dict[str, str]]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def json_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distribution(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") for row in rows).items()))


def require_unique(rows: list[dict[str, str]], field: str) -> None:
    values = [row.get(field, "") for row in rows]
    if any(not value for value in values):
        raise ValueError(f"blank identity: {field}")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate identity: {field}")


def require_nonnegative_integer(row: dict[str, str], field: str) -> int:
    raw = row.get(field, "")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"invalid integer field {field}: {raw!r}") from exc
    if value < 0:
        raise ValueError(f"negative integer field {field}: {value}")
    return value


def require_audit_gate(
    manifest_path: Path,
    manifest: dict[str, object],
    audit_path: Path,
    audit: dict[str, object],
) -> None:
    pilot_id = str(manifest["pilot_id"])
    lanes = list(manifest["lanes"])
    expected = int(manifest["selected_rows"])
    if not audit_path.is_file():
        raise ValueError(f"audit summary missing: {audit_path}")
    if audit.get("pilot_id") != pilot_id:
        raise ValueError("audit pilot mismatch")
    if Path(str(audit.get("manifest", ""))).resolve() != manifest_path.resolve():
        raise ValueError("audit manifest mismatch")
    if audit.get("merge_recommendation") != (
        "merge_all_text_table_detection_lanes"
    ):
        raise ValueError("audit is not merge eligible")
    if audit.get("lane_classification_counts") != {
        "completed_merge_eligible": len(lanes)
    }:
        raise ValueError("lane classifications are not merge eligible")
    for field in ("planned_rows", "ledger_rows", "terminal_rows"):
        if int(audit.get(field, -1)) != expected:
            raise ValueError(f"audit {field} mismatch")
    if audit.get("detection_status_counts") != {
        "detection_checked": expected
    }:
        raise ValueError("audit detection-status gate failed")
    for field in AUDIT_ZERO_FIELDS:
        if int(audit.get(field, -1)) != 0:
            raise ValueError(f"audit gate {field} failed")
    for field in FORBIDDEN_AUDIT_FIELDS:
        if int(audit.get(field, -1)) != 0:
            raise ValueError(f"forbidden audit counter {field}")
    expected_heuristic = str(
        manifest.get("frozen_heuristic_version", TABLE_METHOD)
    )
    if expected_heuristic != TABLE_METHOD:
        raise ValueError("manifest does not use the supported frozen heuristic")
    if audit.get("frozen_heuristic_version") != expected_heuristic:
        raise ValueError("audit frozen-heuristic mismatch")
    audit_lanes = {
        str(item["lane_id"]): item for item in audit.get("lanes", [])
    }
    for lane in lanes:
        lane_id = str(lane["lane_id"])
        lane_audit = audit_lanes.get(lane_id)
        if not lane_audit:
            raise ValueError(f"audit lane missing: {lane_id}")
        if lane_audit.get("classification") != "completed_merge_eligible":
            raise ValueError(f"audit lane is not merge eligible: {lane_id}")
        if lane_audit.get("mode") != "local":
            raise ValueError(f"audit lane is not local: {lane_id}")
        if lane_audit.get("no_forbidden_activity") is not True:
            raise ValueError(f"audit lane has forbidden activity: {lane_id}")
        if int(lane_audit.get("terminal_rows", -1)) != int(
            lane["expected_rows"]
        ):
            raise ValueError(f"audit lane terminal mismatch: {lane_id}")


def validate_detection_row(
    row: dict[str, str],
    *,
    pilot_id: str,
    lane_id: str,
    heuristic: str,
) -> None:
    if row.get("text_table_detection_pilot_id") != pilot_id:
        raise ValueError(f"row run mismatch: {lane_id}")
    if row.get("text_table_detection_lane_id") != lane_id:
        raise ValueError(f"row lane mismatch: {lane_id}")
    if row.get("detection_status") not in TERMINAL_STATUSES:
        raise ValueError(f"nonterminal detection row: {lane_id}")
    if row.get("detection_status") != "detection_checked":
        raise ValueError(f"unexpected terminal detection status: {lane_id}")
    if row.get("table_detection_method") != heuristic:
        raise ValueError(f"frozen-heuristic mismatch: {lane_id}")
    page_count = require_nonnegative_integer(row, "pdf_page_count")
    require_nonnegative_integer(row, "pages_scanned")
    require_nonnegative_integer(row, "pages_with_text")
    require_nonnegative_integer(row, "total_text_chars_scanned")
    hint_count = require_nonnegative_integer(row, "candidate_wage_page_count")
    if len(row.get("candidate_contract_period_text", "")) > 300:
        raise ValueError(f"bounded contract hint overrun: {lane_id}")
    raw_pages = row.get("candidate_wage_pages", "")
    pages: list[int] = []
    if raw_pages:
        try:
            pages = [int(value) for value in raw_pages.split(",")]
        except ValueError as exc:
            raise ValueError(f"invalid candidate page hint: {lane_id}") from exc
        if len(pages) != len(set(pages)):
            raise ValueError(f"duplicate candidate page hint: {lane_id}")
        if any(page < 1 or page > page_count for page in pages):
            raise ValueError(f"out-of-range candidate page hint: {lane_id}")
    if len(pages) != hint_count:
        raise ValueError(f"candidate page-count mismatch: {lane_id}")


def collect_lane_rows(
    manifest: dict[str, object],
) -> tuple[list[str], list[dict[str, str]]]:
    pilot_id = str(manifest["pilot_id"])
    expected = int(manifest["selected_rows"])
    heuristic = str(manifest.get("frozen_heuristic_version", TABLE_METHOD))
    combined: list[dict[str, str]] = []
    fields: list[str] | None = None
    for lane in manifest["lanes"]:
        lane_id = str(lane["lane_id"])
        ledger_path = (
            Path(str(lane["future_local_output_dir"]))
            / "text_table_detection_ledger.csv"
        )
        if not ledger_path.is_file():
            raise ValueError(f"local detection ledger missing: {ledger_path}")
        lane_fields, lane_rows = read_csv(ledger_path)
        if fields is None:
            fields = lane_fields
        elif lane_fields != fields:
            raise ValueError(f"lane schema mismatch: {lane_id}")
        if len(lane_rows) != int(lane["expected_rows"]):
            raise ValueError(f"lane row-count mismatch: {lane_id}")
        for row in lane_rows:
            validate_detection_row(
                row,
                pilot_id=pilot_id,
                lane_id=lane_id,
                heuristic=heuristic,
            )
        combined.extend(lane_rows)
    if len(combined) != expected:
        raise ValueError("full-run row-count mismatch")
    for field in IDENTITY_FIELDS:
        require_unique(combined, field)
    return fields or [], combined


def parse_text_authority(
    readiness_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    authority = [
        row
        for row in readiness_rows
        if (
            row.get("recommended_next_action") == "parse_text_layer_later"
            and row.get("text_layer_status") in {"present", "partial"}
            and row.get("content_artifact_path")
            and row.get("content_hash")
        )
    ]
    for field in (
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        require_unique(authority, field)
    return authority


def verify_authority(
    detection_rows: list[dict[str, str]],
    readiness_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, object]]:
    authority = parse_text_authority(readiness_rows)
    detection_by_readiness = {
        row["pdf_readiness_id"]: row for row in detection_rows
    }
    authority_by_readiness = {
        row["pdf_readiness_id"]: row for row in authority
    }
    if set(detection_by_readiness) != set(authority_by_readiness):
        raise ValueError("detection/PDF-readiness identity mismatch")
    if {
        row["source_review_id"] for row in detection_rows
    } != {row["source_review_id"] for row in authority}:
        raise ValueError("detection/source-review identity mismatch")
    if {
        row["candidate_queue_row_id"] for row in detection_rows
    } != {row["candidate_queue_row_id"] for row in authority}:
        raise ValueError("detection/candidate identity mismatch")
    mismatch_counts: Counter[str] = Counter()
    for readiness_id, detection in detection_by_readiness.items():
        authority_row = authority_by_readiness[readiness_id]
        for field in AUTHORITY_MATCH_FIELDS:
            if detection.get(field, "") != authority_row.get(field, ""):
                mismatch_counts[field] += 1
    if mismatch_counts:
        raise ValueError(
            "detection/PDF-readiness authority field mismatch: "
            + json.dumps(dict(sorted(mismatch_counts.items())))
        )
    return authority, {
        "pdf_readiness_id_set_equal": True,
        "source_review_id_set_equal": True,
        "candidate_queue_row_id_set_equal": True,
        "authority_field_mismatch_counts": {},
        "authority_fields_checked": list(AUTHORITY_MATCH_FIELDS),
    }


def build_summary(
    *,
    rows: list[dict[str, str]],
    readiness_rows: list[dict[str, str]],
    authority_rows: list[dict[str, str]],
    readiness_path: Path,
    manifest_path: Path,
    audit_path: Path,
    merge_id: str,
    merged_at: str,
    authority: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "status": "text_table_detection_full_parse_text_merged",
        "text_table_detection_merge_id": merge_id,
        "text_table_detection_merged_at": merged_at,
        "text_table_detection_stage": STAGE,
        "full_run_id": rows[0]["text_table_detection_pilot_id"] if rows else "",
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "audit_summary_path": audit_path.as_posix(),
        "audit_summary_sha256": sha256_file(audit_path),
        "pdf_readiness_ledger_csv": readiness_path.as_posix(),
        "pdf_readiness_ledger_sha256": sha256_file(readiness_path),
        "pdf_readiness_rows": len(readiness_rows),
        "parse_text_layer_later_rows_available": len(authority_rows),
        "ocr_later_rows": sum(
            row.get("recommended_next_action") == "ocr_later"
            for row in readiness_rows
        ),
        "full_parse_text_rows_merged": len(rows),
        "parse_text_coverage_rate": (
            len(rows) / len(authority_rows) if authority_rows else 0.0
        ),
        "unique_text_table_detection_ids": len(
            {row["text_table_detection_id"] for row in rows}
        ),
        "unique_pdf_readiness_ids": len(
            {row["pdf_readiness_id"] for row in rows}
        ),
        "unique_source_review_ids": len(
            {row["source_review_id"] for row in rows}
        ),
        "unique_candidate_queue_row_ids": len(
            {row["candidate_queue_row_id"] for row in rows}
        ),
        "duplicate_text_table_detection_ids": 0,
        "duplicate_pdf_readiness_ids": 0,
        "duplicate_source_review_ids": 0,
        "duplicate_candidate_queue_row_ids": 0,
        "exact_parse_text_authority_equality": authority,
        "detection_status_counts": distribution(rows, "detection_status"),
        "wage_table_signal_counts": distribution(rows, "wage_table_signal"),
        "wage_table_signal_confidence_counts": distribution(
            rows, "wage_table_signal_confidence"
        ),
        "contract_period_signal_counts": distribution(
            rows, "contract_period_signal"
        ),
        "contract_period_confidence_counts": distribution(
            rows, "contract_period_confidence"
        ),
        "table_like_structure_signal_counts": distribution(
            rows, "table_like_structure_signal"
        ),
        "extraction_pilot_priority_counts": distribution(
            rows, "extraction_pilot_priority"
        ),
        "recommended_next_action_counts": distribution(
            rows, "recommended_next_action"
        ),
        "pages_scanned": sum(int(row["pages_scanned"]) for row in rows),
        "pages_with_text": sum(int(row["pages_with_text"]) for row in rows),
        "total_text_chars_scanned": sum(
            int(row["total_text_chars_scanned"]) for row in rows
        ),
        "candidate_wage_page_hints": sum(
            int(row["candidate_wage_page_count"]) for row in rows
        ),
        "maximum_contract_hint_characters": max(
            (
                len(row.get("candidate_contract_period_text", ""))
                for row in rows
            ),
            default=0,
        ),
        "parser_library_counts": distribution(rows, "parser_library"),
        "parser_version_counts": distribution(rows, "parser_version"),
        "heuristic_version_counts": distribution(
            rows, "table_detection_method"
        ),
        "source_review_batch_distribution": distribution(
            rows, "source_review_pilot_id"
        ),
        "priority_distribution": distribution(
            rows, "priority_for_content_review"
        ),
        "unit_type_distribution": distribution(rows, "unit_type"),
        "state_distribution": distribution(rows, "state"),
        "candidate_source_type_distribution": distribution(
            rows, "candidate_source_type"
        ),
        "officialness_distribution": distribution(
            rows, "source_officialness_rating"
        ),
        "page_count_bin_distribution": distribution(rows, "page_count_bin"),
        "text_layer_status_counts": distribution(rows, "text_layer_status"),
        "pilot1_supersession": {
            "pilot_id": "TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24",
            "pilot_rows_concatenated": 0,
            "status": "preserved_as_superseded_diagnostic_provenance",
            "reason": (
                "the full run reran all pilot identities under the same "
                "frozen heuristic"
            ),
        },
        "hash_failures": 0,
        "missing_artifacts": 0,
        "parser_errors": 0,
        "invalid_candidate_page_hints": 0,
        "bounded_hint_overruns": 0,
        "heuristic_mismatches": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "redownloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "final_wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "scout_accounting_mutations": 0,
        "routing_ledger_mutations": 0,
        "metadata_triage_ledger_mutations": 0,
        "source_review_ledger_mutations": 0,
        "pdf_readiness_ledger_mutations": 0,
        "durable_text_table_merges": 1,
        "next_recommendation": "manual_calibration_subset_before_extraction",
        "caveats": [
            "Table detection is heuristic and preliminary.",
            "Candidate pages are hints, not wage observations.",
            "No final wage values were extracted.",
            "No OCR or ingestion was run.",
            "Manual calibration is required before extraction.",
        ],
    }


def build_audit_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Cumulative Text/Table-Detection Merge Audit",
        "",
        f"- merge ID: `{summary['text_table_detection_merge_id']}`",
        f"- merged at: `{summary['text_table_detection_merged_at']}`",
        f"- stage: `{summary['text_table_detection_stage']}`",
        f"- full-run rows / authority rows: "
        f"{summary['full_parse_text_rows_merged']} / "
        f"{summary['parse_text_layer_later_rows_available']}",
        "- exact PDF-readiness/source-review/candidate identity equality: yes",
        "- artifact path/hash/size/type/page-count/text-layer equality: yes",
        f"- detection status: `{summary['detection_status_counts']}`",
        f"- wage-table signals: `{summary['wage_table_signal_counts']}`",
        f"- contract-period signals: `{summary['contract_period_signal_counts']}`",
        f"- table-like structure: `{summary['table_like_structure_signal_counts']}`",
        f"- extraction priority: `{summary['extraction_pilot_priority_counts']}`",
        f"- next actions: `{summary['recommended_next_action_counts']}`",
        f"- candidate page hints: {summary['candidate_wage_page_hints']}",
        f"- pages scanned / with text: {summary['pages_scanned']} / "
        f"{summary['pages_with_text']}",
        "- duplicate detection/readiness/source/candidate identities: 0 / 0 / 0 / 0",
        "- missing/hash/parser/heuristic/page-hint/bounded-hint failures: "
        "0 / 0 / 0 / 0 / 0 / 0",
        "- URLs/network/downloads/OCR/full text/final wage values: "
        "0 / 0 / 0 / 0 / 0 / 0",
        "- ingestion/codify/scout/routing/triage/source-review/PDF-readiness "
        "mutations: 0 / 0 / 0 / 0 / 0 / 0 / 0",
        "- Pilot 1 rows concatenated: 0; preserved as superseded provenance",
        "",
        "The merged layer contains deterministic heuristic signals and "
        "bounded candidate-page/contract-period hints only. These are not "
        "final wage observations, ingested or codified evidence, wage-gap "
        "findings, or causal findings.",
        "",
    ]
    return "\n".join(lines)


def merge(args: argparse.Namespace) -> dict[str, object]:
    manifest_path = Path(args.manifest)
    audit_path = Path(args.audit_summary)
    readiness_path = Path(args.pdf_readiness_ledger_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(
            f"durable output directory already exists: {output_dir}"
        )
    manifest = read_json(manifest_path)
    audit = read_json(audit_path)
    require_audit_gate(
        manifest_path,
        manifest,
        audit_path,
        audit,
    )
    fields, rows = collect_lane_rows(manifest)
    _, readiness_rows = read_csv(readiness_path)
    authority_rows, authority = verify_authority(rows, readiness_rows)
    if len(rows) != len(authority_rows):
        raise ValueError("detection row count does not equal authority count")

    merged_at = now_utc()
    output_fields = list(fields)
    for field in MERGE_FIELDS:
        if field in output_fields:
            raise ValueError(f"input already contains merge field: {field}")
        output_fields.append(field)
    merged_rows: list[dict[str, str]] = []
    for row in rows:
        merged = dict(row)
        merged.update(
            {
                "text_table_detection_merge_id": args.merge_id,
                "text_table_detection_merged_at": merged_at,
                "text_table_detection_stage": STAGE,
            }
        )
        merged_rows.append(merged)
    merged_rows.sort(
        key=lambda row: (
            row["source_review_id"],
            row["candidate_queue_row_id"],
            row["pdf_readiness_id"],
            row["text_table_detection_id"],
        )
    )
    summary = build_summary(
        rows=merged_rows,
        readiness_rows=readiness_rows,
        authority_rows=authority_rows,
        readiness_path=readiness_path,
        manifest_path=manifest_path,
        audit_path=audit_path,
        merge_id=args.merge_id,
        merged_at=merged_at,
        authority=authority,
    )
    ledger_content = csv_bytes(output_fields, merged_rows)
    summary_content = json_bytes(summary)
    audit_content = build_audit_markdown(summary).encode("utf-8")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}.staging.",
            dir=output_dir.parent,
        )
    )
    try:
        (staging / OUTPUT_NAMES["ledger"]).write_bytes(ledger_content)
        (staging / OUTPUT_NAMES["summary"]).write_bytes(summary_content)
        (staging / OUTPUT_NAMES["audit"]).write_bytes(audit_content)
        (staging / OUTPUT_NAMES["latest_ledger"]).write_bytes(ledger_content)
        (staging / OUTPUT_NAMES["latest_summary"]).write_bytes(
            summary_content
        )
        if output_dir.exists():
            raise FileExistsError(
                f"durable output directory appeared during merge: {output_dir}"
            )
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--audit-summary", required=True)
    parser.add_argument("--pdf-readiness-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merge-id", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = merge(args)
    print(
        "Text/table-detection merge complete: "
        f"{summary['full_parse_text_rows_merged']} rows; "
        f"{summary['text_table_detection_merge_id']}."
    )


if __name__ == "__main__":
    main()
