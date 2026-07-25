#!/usr/bin/env python3
"""Merge audited local PDF-readiness lanes into one durable offline ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pdf_readiness_sources import TERMINAL_STATUSES


MERGE_FIELDS = [
    "pdf_readiness_merge_id",
    "pdf_readiness_merged_at",
    "pdf_readiness_stage",
]
STAGE = "technical_readiness_checked_not_extracted"
OUTPUT_NAMES = {
    "ledger": "pdf_readiness_ledger_cumulative.csv",
    "summary": "pdf_readiness_summary_cumulative.json",
    "audit": "pdf_readiness_merge_audit_cumulative.md",
    "latest_ledger": "pdf_readiness_ledger_latest.csv",
    "latest_summary": "pdf_readiness_summary_latest.json",
}
FORBIDDEN_COUNTER_FIELDS = (
    "urls_opened",
    "network_calls",
    "downloads",
    "redownloads",
    "ocr_runs",
    "full_text_artifacts_written",
    "wage_tables_extracted",
    "wage_values_extracted",
    "ingestion_actions",
    "codify_actions",
)
AUTHORITY_MATCH_FIELDS = {
    "candidate_queue_row_id": "candidate_queue_row_id",
    "triage_id": "triage_id",
    "verification_id": "verification_id",
    "source_review_pilot_id": "source_review_pilot_id",
    "state": "state",
    "municipality": "municipality",
    "government_name": "government_name",
    "unit_type": "unit_type_scouted",
    "candidate_source_type": "candidate_source_type",
    "priority_for_content_review": "priority_for_content_review",
    "source_officialness_rating": "source_officialness_rating",
    "source_relevance_rating": "source_relevance_rating",
    "document_type_rating": "document_type_rating",
    "extraction_readiness_rating": "extraction_readiness_rating",
    "content_artifact_path": "content_artifact_path",
    "content_hash": "content_hash",
    "content_byte_size": "content_byte_size",
    "content_type_observed": "content_type_observed",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
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


def duplicate_count(values: list[str]) -> int:
    return len(values) - len(set(values))


def distribution(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") for row in rows).items()))


def percentile(values: list[int], quantile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(quantile * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def page_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    values = [
        int(row["pdf_page_count"])
        for row in rows
        if row.get("pdf_page_count", "").isdigit()
    ]
    buckets: Counter[str] = Counter()
    for value in values:
        if value <= 10:
            bucket = "1_to_10"
        elif value <= 25:
            bucket = "11_to_25"
        elif value <= 50:
            bucket = "26_to_50"
        elif value <= 100:
            bucket = "51_to_100"
        else:
            bucket = "over_100"
        buckets[bucket] += 1
    if values:
        ordered = sorted(values)
        middle = len(ordered) // 2
        median_value = (
            ordered[middle]
            if len(ordered) % 2
            else (ordered[middle - 1] + ordered[middle]) / 2
        )
        if isinstance(median_value, float) and median_value.is_integer():
            median_value = int(median_value)
    else:
        median_value = None
    return {
        "count": len(values),
        "minimum": min(values) if values else None,
        "median": median_value,
        "mean": round(sum(values) / len(values), 6) if values else None,
        "p90": percentile(values, 0.9),
        "maximum": max(values) if values else None,
        "total_pages": sum(values),
        "buckets": dict(sorted(buckets.items())),
    }


def retained_pdf_rows(
    source_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    retained: list[dict[str, str]] = []
    for row in source_rows:
        try:
            byte_size = int(row.get("content_byte_size", ""))
        except ValueError:
            byte_size = 0
        if (
            row.get("source_review_status")
            == "reviewed_metadata_and_artifact_saved"
            and row.get("content_type_observed") == "application/pdf"
            and row.get("content_artifact_path")
            and row.get("content_hash")
            and byte_size > 0
        ):
            retained.append(row)
    return retained


def require_audit_gate(
    manifest_path: Path,
    manifest: dict[str, object],
    audit_path: Path,
    audit: dict[str, object],
) -> None:
    pilot_id = str(manifest["pilot_id"])
    lanes = list(manifest["lanes"])
    expected = int(manifest["selected_rows"])
    if audit.get("pilot_id") != pilot_id:
        raise ValueError(f"audit pilot mismatch for {pilot_id}")
    if Path(str(audit.get("manifest", ""))).resolve() != manifest_path.resolve():
        raise ValueError(f"audit manifest mismatch for {pilot_id}")
    if audit.get("merge_recommendation") != "merge_all_pdf_readiness_lanes":
        raise ValueError(f"audit is not merge eligible for {pilot_id}")
    if audit.get("lane_classification_counts") != {
        "completed_merge_eligible": len(lanes)
    }:
        raise ValueError(f"lane classifications are not merge eligible: {pilot_id}")
    for field in ("planned_rows", "ledger_rows", "terminal_rows"):
        if int(audit.get(field, -1)) != expected:
            raise ValueError(f"audit {field} mismatch for {pilot_id}")
    for field in (
        "cross_lane_duplicate_pdf_readiness_ids",
        "cross_lane_duplicate_source_review_ids",
        "cross_lane_duplicate_candidate_queue_ids",
        "hash_failures",
        "missing_artifacts",
        "parser_errors",
    ):
        if int(audit.get(field, -1)) != 0:
            raise ValueError(f"audit gate {field} failed for {pilot_id}")
    for field in (
        "urls_opened",
        "network_calls",
        "downloads",
        "ocr_runs",
        "full_text_artifacts_written",
        "wage_values_extracted",
        "ingestion_actions",
        "codify_actions",
        "durable_readiness_merges",
    ):
        if int(audit.get(field, -1)) != 0:
            raise ValueError(f"forbidden audit counter {field}: {pilot_id}")
    audit_lanes = {
        str(item["lane_id"]): item for item in audit.get("lanes", [])
    }
    for lane in lanes:
        lane_id = str(lane["lane_id"])
        lane_audit = audit_lanes.get(lane_id)
        if not lane_audit:
            raise ValueError(f"audit lane missing: {pilot_id}/{lane_id}")
        if lane_audit.get("classification") != "completed_merge_eligible":
            raise ValueError(f"audit lane not merge eligible: {pilot_id}/{lane_id}")
        if lane_audit.get("mode") != "local":
            raise ValueError(f"audit lane is not local: {pilot_id}/{lane_id}")
        if lane_audit.get("no_forbidden_activity") is not True:
            raise ValueError(f"audit lane has forbidden activity: {pilot_id}/{lane_id}")
        if int(lane_audit.get("terminal_rows", -1)) != int(
            lane["expected_rows"]
        ):
            raise ValueError(f"audit lane terminal mismatch: {pilot_id}/{lane_id}")
    if not audit_path.is_file():
        raise ValueError(f"audit summary missing: {audit_path}")


def collect_round_rows(
    manifest: dict[str, object],
) -> tuple[list[str], list[dict[str, str]]]:
    pilot_id = str(manifest["pilot_id"])
    expected = int(manifest["selected_rows"])
    combined: list[dict[str, str]] = []
    fields: list[str] | None = None
    for lane in manifest["lanes"]:
        lane_id = str(lane["lane_id"])
        ledger_path = (
            Path(str(lane["future_local_output_dir"]))
            / "pdf_readiness_ledger.csv"
        )
        if not ledger_path.is_file():
            raise ValueError(f"local readiness ledger missing: {ledger_path}")
        lane_fields, lane_rows = read_csv(ledger_path)
        if fields is None:
            fields = lane_fields
        elif lane_fields != fields:
            raise ValueError(f"lane schema mismatch: {pilot_id}/{lane_id}")
        if len(lane_rows) != int(lane["expected_rows"]):
            raise ValueError(f"lane row-count mismatch: {pilot_id}/{lane_id}")
        for row in lane_rows:
            if row.get("pdf_readiness_pilot_id") != pilot_id:
                raise ValueError(f"row round mismatch: {pilot_id}/{lane_id}")
            if row.get("pdf_readiness_lane_id") != lane_id:
                raise ValueError(f"row lane mismatch: {pilot_id}/{lane_id}")
            if row.get("readiness_status") not in TERMINAL_STATUSES:
                raise ValueError(f"nonterminal readiness row: {pilot_id}/{lane_id}")
            if not row.get("pdf_page_count", "").isdigit():
                raise ValueError(f"missing page count: {pilot_id}/{lane_id}")
            if row.get("text_layer_status") not in {
                "present",
                "partial",
                "absent",
                "parser_error",
            }:
                raise ValueError(f"nonterminal text-layer status: {pilot_id}/{lane_id}")
            if row.get("artifact_exists") != "yes":
                raise ValueError(f"artifact existence gate failed: {pilot_id}/{lane_id}")
            if row.get("artifact_hash_verified") != "yes":
                raise ValueError(f"artifact hash gate failed: {pilot_id}/{lane_id}")
            if row.get("pdf_signature_valid") != "yes":
                raise ValueError(f"PDF signature gate failed: {pilot_id}/{lane_id}")
            if row.get("readiness_status") != "readiness_checked":
                raise ValueError(f"unexpected terminal status: {pilot_id}/{lane_id}")
        combined.extend(lane_rows)
    if len(combined) != expected:
        raise ValueError(f"round row-count mismatch: {pilot_id}")
    return fields or [], combined


def require_unique(rows: list[dict[str, str]], field: str) -> None:
    values = [row.get(field, "") for row in rows]
    if any(not value for value in values):
        raise ValueError(f"blank identity: {field}")
    if duplicate_count(values):
        raise ValueError(f"duplicate identity: {field}")


def verify_authority(
    readiness_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, object]]:
    retained = retained_pdf_rows(source_rows)
    for field in ("source_review_id", "candidate_queue_row_id"):
        require_unique(retained, field)
        require_unique(readiness_rows, field)
    readiness_by_source = {
        row["source_review_id"]: row for row in readiness_rows
    }
    retained_by_source = {row["source_review_id"]: row for row in retained}
    readiness_source_ids = set(readiness_by_source)
    retained_source_ids = set(retained_by_source)
    if readiness_source_ids != retained_source_ids:
        raise ValueError("readiness/source-review retained source identity mismatch")
    readiness_candidate_ids = {
        row["candidate_queue_row_id"] for row in readiness_rows
    }
    retained_candidate_ids = {
        row["candidate_queue_row_id"] for row in retained
    }
    if readiness_candidate_ids != retained_candidate_ids:
        raise ValueError("readiness/source-review retained candidate identity mismatch")
    mismatch_counts: Counter[str] = Counter()
    for source_id, readiness in readiness_by_source.items():
        authority = retained_by_source[source_id]
        for readiness_field, source_field in AUTHORITY_MATCH_FIELDS.items():
            if readiness.get(readiness_field, "") != authority.get(
                source_field, ""
            ):
                mismatch_counts[readiness_field] += 1
    if mismatch_counts:
        raise ValueError(
            "readiness/source-review authority field mismatch: "
            + json.dumps(dict(sorted(mismatch_counts.items())))
        )
    return retained, {
        "source_review_id_set_equal": True,
        "candidate_queue_row_id_set_equal": True,
        "authority_field_mismatch_counts": {},
        "authority_fields_checked": dict(AUTHORITY_MATCH_FIELDS),
    }


def build_summary(
    *,
    rows: list[dict[str, str]],
    retained_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    source_path: Path,
    manifest_paths: list[Path],
    audit_paths: list[Path],
    round_counts: dict[str, int],
    merge_id: str,
    merged_at: str,
    authority: dict[str, object],
) -> dict[str, object]:
    pages = page_summary(rows)
    total_bytes = sum(int(row["content_byte_size"]) for row in rows)
    return {
        "schema_version": "1.0.0",
        "status": "pdf_readiness_full_retained_merged",
        "pdf_readiness_merge_id": merge_id,
        "pdf_readiness_merged_at": merged_at,
        "pdf_readiness_stage": STAGE,
        "round_ids": list(round_counts),
        "round_row_counts": round_counts,
        "manifest_paths": [path.as_posix() for path in manifest_paths],
        "audit_summary_paths": [path.as_posix() for path in audit_paths],
        "source_review_ledger_csv": source_path.as_posix(),
        "source_review_ledger_sha256": sha256_file(source_path),
        "source_review_rows": len(source_rows),
        "retained_pdf_artifacts_available": len(retained_rows),
        "pdf_readiness_rows_merged": len(rows),
        "retained_pdf_readiness_coverage_rate": (
            len(rows) / len(retained_rows) if retained_rows else 0.0
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
        "duplicate_pdf_readiness_ids": 0,
        "duplicate_source_review_ids": 0,
        "duplicate_candidate_queue_row_ids": 0,
        "exact_retained_pdf_identity_equality": authority,
        "readiness_status_counts": distribution(rows, "readiness_status"),
        "text_layer_status_counts": distribution(rows, "text_layer_status"),
        "technical_parseability_rating_counts": distribution(
            rows, "technical_parseability_rating"
        ),
        "recommended_next_action_counts": distribution(
            rows, "recommended_next_action"
        ),
        "page_count_summary": pages,
        "sampled_pages_checked": sum(
            int(row["sampled_pages_checked"]) for row in rows
        ),
        "sampled_pages_with_text": sum(
            int(row["sampled_pages_with_text"]) for row in rows
        ),
        "text_chars_sampled_total": sum(
            int(row["text_chars_sampled_total"]) for row in rows
        ),
        "parser_library_counts": distribution(rows, "parser_library"),
        "parser_version_counts": distribution(rows, "parser_version"),
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
        "document_type_distribution": distribution(
            rows, "document_type_rating"
        ),
        "content_artifact_bytes": total_bytes,
        "missing_artifacts": 0,
        "hash_failures": 0,
        "invalid_pdf_signatures": 0,
        "parser_errors": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "redownloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "wage_tables_extracted": 0,
        "wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "scout_accounting_mutations": 0,
        "routing_ledger_mutations": 0,
        "metadata_triage_ledger_mutations": 0,
        "source_review_ledger_mutations": 0,
        "durable_readiness_merges": 1,
        "next_recommendation": "text_layer_table_detection_pilot",
        "caveats": [
            "PDF-readiness is technical parseability only.",
            "Text-layer presence does not prove wage data exists.",
            "OCR has not run.",
            "Wage extraction has not started.",
            "No ingestion or codification has occurred.",
        ],
    }


def build_audit_markdown(summary: dict[str, object]) -> str:
    pages = summary["page_count_summary"]
    lines = [
        "# Cumulative PDF-Readiness Merge Audit",
        "",
        f"- merge ID: `{summary['pdf_readiness_merge_id']}`",
        f"- merged at: `{summary['pdf_readiness_merged_at']}`",
        f"- stage: `{summary['pdf_readiness_stage']}`",
        f"- rounds: `{summary['round_row_counts']}`",
        f"- source-review / retained PDF / readiness rows: "
        f"{summary['source_review_rows']} / "
        f"{summary['retained_pdf_artifacts_available']} / "
        f"{summary['pdf_readiness_rows_merged']}",
        "- exact retained source-review and candidate identity equality: yes",
        "- authority path/hash/size/content-type and inherited-field equality: yes",
        f"- readiness statuses: `{summary['readiness_status_counts']}`",
        f"- text-layer statuses: `{summary['text_layer_status_counts']}`",
        f"- technical parseability: "
        f"`{summary['technical_parseability_rating_counts']}`",
        f"- recommended next actions: "
        f"`{summary['recommended_next_action_counts']}`",
        f"- page count summary: `{pages}`",
        "- duplicate PDF-readiness/source-review/candidate identities: 0 / 0 / 0",
        "- missing/hash/signature/parser failures: 0 / 0 / 0 / 0",
        "- URLs/network/downloads/OCR/full-text/wage extraction: 0 / 0 / 0 / 0 / 0 / 0",
        "- ingestion/codify/scout/routing/triage/source-review mutations: "
        "0 / 0 / 0 / 0 / 0 / 0",
        "",
        "The merged layer records technical page-count and bounded sampled "
        "text-layer readiness only. It does not establish wage-table "
        "presence, wage values, source relevance, employer or unit match, "
        "ingested evidence, codified evidence, or analysis-ready observations.",
        "",
    ]
    return "\n".join(lines)


def merge(args: argparse.Namespace) -> dict[str, object]:
    manifest_paths = [Path(path) for path in args.manifest]
    audit_paths = [Path(path) for path in args.audit_summary]
    if len(manifest_paths) != len(audit_paths):
        raise ValueError("manifest and audit-summary counts must match")
    if len(manifest_paths) < 2:
        raise ValueError("at least two readiness rounds are required")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(
            f"durable output directory already exists: {output_dir}"
        )
    manifests: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for manifest_path, audit_path in zip(manifest_paths, audit_paths):
        manifest = read_json(manifest_path)
        audit = read_json(audit_path)
        require_audit_gate(
            manifest_path, manifest, audit_path, audit
        )
        manifests.append(manifest)
        audits.append(audit)
    round_ids = [str(manifest["pilot_id"]) for manifest in manifests]
    if len(round_ids) != len(set(round_ids)):
        raise ValueError("duplicate readiness round manifest")

    all_rows: list[dict[str, str]] = []
    fields: list[str] | None = None
    round_counts: dict[str, int] = {}
    for manifest in manifests:
        round_fields, round_rows = collect_round_rows(manifest)
        if fields is None:
            fields = round_fields
        elif round_fields != fields:
            raise ValueError("readiness round schemas differ")
        round_id = str(manifest["pilot_id"])
        round_counts[round_id] = len(round_rows)
        all_rows.extend(round_rows)
    for field in (
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        require_unique(all_rows, field)

    source_path = Path(args.source_review_ledger_csv)
    _, source_rows = read_csv(source_path)
    retained_rows, authority = verify_authority(all_rows, source_rows)
    if len(all_rows) != len(retained_rows):
        raise ValueError("readiness row count does not equal retained PDF count")

    merged_at = now_utc()
    output_fields = list(fields or [])
    for field in MERGE_FIELDS:
        if field in output_fields:
            raise ValueError(f"input already contains merge field: {field}")
        output_fields.append(field)
    merged_rows: list[dict[str, str]] = []
    for row in all_rows:
        merged = dict(row)
        merged.update(
            {
                "pdf_readiness_merge_id": args.merge_id,
                "pdf_readiness_merged_at": merged_at,
                "pdf_readiness_stage": STAGE,
            }
        )
        merged_rows.append(merged)
    merged_rows.sort(
        key=lambda row: (
            row["source_review_id"],
            row["candidate_queue_row_id"],
            row["pdf_readiness_id"],
        )
    )
    summary = build_summary(
        rows=merged_rows,
        retained_rows=retained_rows,
        source_rows=source_rows,
        source_path=source_path,
        manifest_paths=manifest_paths,
        audit_paths=audit_paths,
        round_counts=round_counts,
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
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--audit-summary", action="append", required=True)
    parser.add_argument("--source-review-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--merge-id", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = merge(args)
    print(
        "Cumulative PDF-readiness merge complete: "
        f"{summary['pdf_readiness_rows_merged']} rows; "
        f"{summary['pdf_readiness_merge_id']}."
    )


if __name__ == "__main__":
    main()
