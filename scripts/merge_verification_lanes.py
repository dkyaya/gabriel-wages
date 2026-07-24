#!/usr/bin/env python3
"""Serially merge audited verification lanes into a routing-only ledger.

This command is deliberately offline. It reads committed round inputs,
lane-local terminal ledgers, and an explicit eligible audit summary. It does
not open URLs, update scout accounting, ingest documents, extract wages, or
create analysis-ready evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_verification_lanes import TERMINAL_LIVE_STATUSES, byte_bucket


MERGE_FIELDS = [
    "verification_round_id",
    "verification_merge_id",
    "verification_merged_at",
    "verification_lane_id",
    "verification_stage",
]
VERIFICATION_STAGE = "url_reachability_metadata_verified"
REACHABLE_OR_REUSED_STATUSES = {
    "reachable_http",
    "reachable_html",
    "reachable_pdf_or_document",
    "duplicate_of_verified_source",
}
NON_REACHABLE_STATUSES = TERMINAL_LIVE_STATUSES - REACHABLE_OR_REUSED_STATUSES


class MergeValidationError(ValueError):
    """Raised when the serial verification merge gates do not pass."""


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise MergeValidationError(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MergeValidationError(f"Expected JSON object: {path}")
    return value


def require_audit_eligible(
    *,
    manifest: dict[str, Any],
    audit: dict[str, Any],
    round_id: str,
) -> None:
    if manifest.get("round_id") != round_id:
        raise MergeValidationError("Manifest round ID does not match --round-id")
    if audit.get("round_id") != round_id:
        raise MergeValidationError("Audit round ID does not match --round-id")
    if audit.get("merge_recommendation") != "merge_all_verification_lanes":
        raise MergeValidationError(
            "Audit does not recommend merge_all_verification_lanes"
        )
    lanes = manifest.get("lanes")
    audit_lanes = audit.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise MergeValidationError("Manifest contains no lanes")
    if not isinstance(audit_lanes, list) or len(audit_lanes) != len(lanes):
        raise MergeValidationError("Audit lane count does not match manifest")
    audit_by_lane = {
        str(lane.get("lane_id")): lane
        for lane in audit_lanes
        if isinstance(lane, dict)
    }
    for lane in lanes:
        lane_id = str(lane.get("lane_id"))
        lane_audit = audit_by_lane.get(lane_id)
        if not lane_audit:
            raise MergeValidationError(f"Audit is missing {lane_id}")
        if lane_audit.get("classification") != "completed_merge_eligible":
            raise MergeValidationError(f"{lane_id} is not completed_merge_eligible")
        expected = int(lane.get("expected_rows", 0))
        if int(lane_audit.get("ledger_rows", -1)) != expected:
            raise MergeValidationError(f"{lane_id} audit ledger count mismatch")
        if int(lane_audit.get("terminal_rows", -1)) != expected:
            raise MergeValidationError(f"{lane_id} audit terminal count mismatch")
    expected_total = sum(int(lane.get("expected_rows", 0)) for lane in lanes)
    for field in ("planned_candidate_rows", "ledger_rows", "terminal_rows"):
        if int(audit.get(field, -1)) != expected_total:
            raise MergeValidationError(f"Audit {field} does not equal expected rows")
    if int(audit.get("cross_lane_duplicate_verification_ids", -1)) != 0:
        raise MergeValidationError("Audit reports cross-lane duplicate IDs")
    if int(audit.get("accounting_mutations", -1)) != 0:
        raise MergeValidationError("Audit reports accounting mutations")


def validate_artifact_path(row: dict[str, str], live_dir: Path) -> None:
    value = row.get("artifact_path", "").strip()
    if not value:
        return
    artifact = Path(value)
    if not artifact.is_absolute():
        artifact = Path.cwd() / artifact
    live_resolved = live_dir.resolve()
    artifact_resolved = artifact.resolve()
    try:
        artifact_resolved.relative_to(live_resolved)
    except ValueError as exc:
        raise MergeValidationError(
            f"Artifact escapes lane output: {row.get('verification_id', '')}"
        ) from exc
    if not artifact_resolved.is_file():
        raise MergeValidationError(
            f"Artifact is missing: {row.get('verification_id', '')}"
        )


def load_lane_rows(
    lane: dict[str, Any],
    *,
    round_id: str,
    merge_id: str,
    merged_at: str,
) -> tuple[list[str], list[dict[str, str]]]:
    lane_id = str(lane["lane_id"])
    input_path = Path(str(lane["input_csv"]))
    if sha256_file(input_path) != str(lane["input_sha256"]):
        raise MergeValidationError(f"{lane_id} input hash mismatch")
    _, input_rows = read_csv(input_path)
    expected = int(lane["expected_rows"])
    if len(input_rows) != expected:
        raise MergeValidationError(f"{lane_id} input row count mismatch")
    input_ids = [row.get("verification_id", "") for row in input_rows]
    if not all(input_ids) or len(input_ids) != len(set(input_ids)):
        raise MergeValidationError(f"{lane_id} input verification IDs are invalid")

    live_dir = Path(str(lane["live_output_dir"]))
    ledger_path = live_dir / "verification_ledger.csv"
    if not ledger_path.is_file():
        raise MergeValidationError(f"{lane_id} live ledger is missing")
    fieldnames, ledger_rows = read_csv(ledger_path)
    if len(ledger_rows) != expected:
        raise MergeValidationError(f"{lane_id} live ledger row count mismatch")
    by_id: dict[str, dict[str, str]] = {}
    for row in ledger_rows:
        verification_id = row.get("verification_id", "")
        if not verification_id or verification_id in by_id:
            raise MergeValidationError(
                f"{lane_id} contains duplicate or blank verification IDs"
            )
        if row.get("verification_status", "") not in TERMINAL_LIVE_STATUSES:
            raise MergeValidationError(
                f"{lane_id} contains non-terminal verification status"
            )
        validate_artifact_path(row, live_dir)
        by_id[verification_id] = row
    if set(by_id) != set(input_ids):
        raise MergeValidationError(f"{lane_id} input/ledger identity mismatch")

    ordered: list[dict[str, str]] = []
    for input_row in input_rows:
        verification_id = input_row["verification_id"]
        row = dict(by_id[verification_id])
        for identity_field in (
            "candidate_queue_row_id",
            "municipality_id",
            "census_gov_id",
            "duplicate_source_group_id",
        ):
            if row.get(identity_field, "") != input_row.get(identity_field, ""):
                raise MergeValidationError(
                    f"{lane_id} {identity_field} mismatch for {verification_id}"
                )
        row.update(
            {
                "verification_round_id": round_id,
                "verification_merge_id": merge_id,
                "verification_merged_at": merged_at,
                "verification_lane_id": lane_id,
                "verification_stage": VERIFICATION_STAGE,
            }
        )
        ordered.append(row)
    return fieldnames, ordered


def summarize(
    *,
    rows: list[dict[str, str]],
    manifest_path: Path,
    audit_summary_path: Path,
    audit: dict[str, Any],
    round_id: str,
    merge_id: str,
    merged_at: str,
    ledger_path: Path,
) -> dict[str, Any]:
    statuses = Counter(row["verification_status"] for row in rows)
    content_types = Counter(
        row.get("content_type", "").split(";", 1)[0].strip().lower() or "unknown"
        for row in rows
    )
    byte_sizes = Counter(byte_bucket(row.get("bytes_read", "")) for row in rows)
    state_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        state = row.get("state", "") or "unknown"
        status = row["verification_status"]
        bucket = (
            "reachable_or_reused"
            if status in REACHABLE_OR_REUSED_STATUSES
            else "other_terminal"
        )
        state_counts[state][bucket] += 1
    reachable_or_reused = sum(statuses[s] for s in REACHABLE_OR_REUSED_STATUSES)
    artifact_rows = sum(bool(row.get("artifact_path", "").strip()) for row in rows)
    duplicate_link_rows = (
        statuses["duplicate_of_verified_source"]
        + statuses["duplicate_same_url_pending"]
    )
    return {
        "schema_version": "1.0.0",
        "verification_round_id": round_id,
        "verification_merge_id": merge_id,
        "verification_merged_at": merged_at,
        "verification_stage": VERIFICATION_STAGE,
        "manifest": manifest_path.as_posix(),
        "audit_summary": audit_summary_path.as_posix(),
        "durable_ledger": ledger_path.as_posix(),
        "ledger_sha256": sha256_file(ledger_path),
        "ledger_rows": len(rows),
        "terminal_rows": len(rows),
        "unique_verification_ids": len({row["verification_id"] for row in rows}),
        "unique_candidate_queue_row_ids": len(
            {row["candidate_queue_row_id"] for row in rows}
        ),
        "verification_status_counts": dict(sorted(statuses.items())),
        "reachable_or_reused_total": reachable_or_reused,
        "reachable_or_reused_rate": round(reachable_or_reused / len(rows), 6),
        "url_opens_total": int(audit["urls_opened"]),
        "network_calls_total": int(audit["network_calls"]),
        "duplicate_reuse_rows": int(audit["duplicate_reuse_rows"]),
        "successfully_reused_rows": statuses["duplicate_of_verified_source"],
        "duplicate_same_url_pending_rows": statuses["duplicate_same_url_pending"],
        "duplicate_link_rows": duplicate_link_rows,
        "content_type_distribution": dict(sorted(content_types.items())),
        "bytes_read_distribution": dict(sorted(byte_sizes.items())),
        "state_routing_counts": {
            state: dict(sorted(counts.items()))
            for state, counts in sorted(state_counts.items())
        },
        "artifact_rows": artifact_rows,
        "blank_artifact_rows": len(rows) - artifact_rows,
        "artifact_paths_validated": True,
        "input_audit_recommendation": audit["merge_recommendation"],
        "stage_boundary": (
            "URL reachability and response-metadata routing only; not ingestion, "
            "codification, wage extraction, or analysis-ready evidence."
        ),
        "scout_accounting_mutations": 0,
        "network_calls_during_merge": 0,
    }


def write_csv_atomic(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_audit_note(path: Path, summary: dict[str, Any]) -> None:
    statuses = summary["verification_status_counts"]
    content = summary["content_type_distribution"]
    lines = [
        f"# Verified-Source Routing Merge Audit — {summary['verification_round_id']}",
        "",
        f"- Merge ID: `{summary['verification_merge_id']}`",
        f"- Merged at: `{summary['verification_merged_at']}`",
        f"- Durable ledger: `{summary['durable_ledger']}`",
        f"- Ledger rows / terminal rows: {summary['ledger_rows']} / {summary['terminal_rows']}",
        f"- Unique verification IDs: {summary['unique_verification_ids']}",
        f"- Unique queue identities: {summary['unique_candidate_queue_row_ids']}",
        f"- URL opens recorded by the completed live round: {summary['url_opens_total']}",
        f"- Reachable or successfully reused: {summary['reachable_or_reused_total']} "
        f"({summary['reachable_or_reused_rate']:.3%})",
        f"- Duplicate-linked rows: {summary['duplicate_reuse_rows']}",
        f"- Status counts: `{json.dumps(statuses, sort_keys=True)}`",
        f"- Content types: `{json.dumps(content, sort_keys=True)}`",
        f"- Bytes read: `{json.dumps(summary['bytes_read_distribution'], sort_keys=True)}`",
        f"- Artifact paths validated: {str(summary['artifact_paths_validated']).lower()}",
        "",
        "This is a serial routing-ledger merge. It made zero network calls and",
        "did not update scout queue/coverage accounting, ingest or codify a",
        "source, extract a wage, calculate a wage gap, or create claim evidence.",
        "Reachability is not proof of relevance, extractability, or employer/unit",
        "match.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def merge(
    *,
    manifest_path: Path,
    audit_summary_path: Path,
    output_dir: Path,
    round_id: str,
    merge_id: str,
    merged_at: str | None = None,
    write_latest: bool = True,
) -> dict[str, Any]:
    if output_dir.exists():
        raise MergeValidationError(
            f"Refusing to reuse existing merge output directory: {output_dir}"
        )
    manifest = load_json(manifest_path)
    audit = load_json(audit_summary_path)
    require_audit_eligible(manifest=manifest, audit=audit, round_id=round_id)
    merged_at = merged_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")

    output_dir.mkdir(parents=True)
    try:
        all_rows: list[dict[str, str]] = []
        source_fields: list[str] | None = None
        for lane in sorted(
            manifest["lanes"], key=lambda value: int(value.get("lane_number", 0))
        ):
            fields, rows = load_lane_rows(
                lane,
                round_id=round_id,
                merge_id=merge_id,
                merged_at=merged_at,
            )
            if source_fields is None:
                source_fields = fields
            elif fields != source_fields:
                raise MergeValidationError("Lane ledger schemas do not match")
            all_rows.extend(rows)
        verification_ids = [row["verification_id"] for row in all_rows]
        queue_ids = [row["candidate_queue_row_id"] for row in all_rows]
        if len(verification_ids) != len(set(verification_ids)):
            raise MergeValidationError("Merged lanes contain duplicate verification IDs")
        if len(queue_ids) != len(set(queue_ids)):
            raise MergeValidationError("Merged lanes contain duplicate queue identities")

        ledger_path = output_dir / "verified_source_routing_ledger.csv"
        summary_path = output_dir / "verified_source_routing_summary.json"
        audit_note_path = output_dir / "verified_source_routing_merge_audit.md"
        fieldnames = list(source_fields or []) + MERGE_FIELDS
        write_csv_atomic(ledger_path, fieldnames, all_rows)
        summary = summarize(
            rows=all_rows,
            manifest_path=manifest_path,
            audit_summary_path=audit_summary_path,
            audit=audit,
            round_id=round_id,
            merge_id=merge_id,
            merged_at=merged_at,
            ledger_path=ledger_path,
        )
        write_json_atomic(summary_path, summary)
        write_audit_note(audit_note_path, summary)
        if write_latest:
            latest_ledger = output_dir.parent / "verified_source_routing_ledger_latest.csv"
            latest_summary = (
                output_dir.parent / "verified_source_routing_summary_latest.json"
            )
            shutil.copyfile(ledger_path, latest_ledger)
            shutil.copyfile(summary_path, latest_summary)
        return summary
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--audit-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--merge-id", required=True)
    parser.add_argument(
        "--no-write-latest",
        action="store_true",
        help="Do not update the latest routing-ledger copies.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = merge(
        manifest_path=Path(args.manifest),
        audit_summary_path=Path(args.audit_summary),
        output_dir=Path(args.output_dir),
        round_id=args.round_id,
        merge_id=args.merge_id,
        write_latest=not args.no_write_latest,
    )
    print(
        "Verification routing ledger merged: "
        f"{summary['ledger_rows']} rows; "
        f"{summary['reachable_or_reused_total']} reachable/reused; "
        f"merge_id={summary['verification_merge_id']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
