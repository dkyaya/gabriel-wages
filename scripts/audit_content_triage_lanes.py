#!/usr/bin/env python3
"""Audit offline dry-run and metadata-only content-triage lane outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


FUTURE_TERMINAL_STATUSES = {
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross_tab(
    rows: list[dict[str, str]], row_field: str, column_field: str
) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = {}
    for row in rows:
        key = row.get(row_field, "")
        nested.setdefault(key, Counter())[row.get(column_field, "")] += 1
    return {
        key: dict(sorted(values.items()))
        for key, values in sorted(nested.items())
    }


def combine_cross_tabs(
    tables: list[dict[str, dict[str, int]]],
) -> dict[str, dict[str, int]]:
    combined: dict[str, Counter[str]] = {}
    for table in tables:
        for row_key, columns in table.items():
            combined.setdefault(row_key, Counter()).update(columns)
    return {
        key: dict(sorted(values.items()))
        for key, values in sorted(combined.items())
    }


def classify_lane(
    lane: dict[str, object], round_id: str
) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(str(lane["dry_run_output_dir"]))
    live_dir = Path(str(lane["future_live_output_dir"]))
    metadata_dir = Path(
        str(
            lane.get(
                "metadata_only_output_dir",
                Path("tmp/content_triage_rounds")
                / round_id
                / f"{lane['lane_id']}_metadata_only_attempt1",
            )
        )
    )
    result: dict[str, object] = {
        "lane_id": lane["lane_id"],
        "expected_rows": int(lane["expected_rows"]),
        "classification": "not_started",
        "mode": "",
        "ledger_rows": 0,
        "terminal_rows": 0,
        "duplicate_triage_ids": 0,
        "duplicate_candidate_queue_ids": 0,
        "missing_rows": int(lane["expected_rows"]),
        "unexpected_rows": 0,
        "triage_status_counts": {},
        "priority_for_content_review_counts": {},
        "recommended_next_action_counts": {},
        "extraction_readiness_prelim_counts": {},
        "source_relevance_prelim_counts": {},
        "routing_status_to_triage_status": {},
        "disposition_to_priority": {},
    }
    if not input_path.exists():
        result.update(classification="missing_artifacts", detail="input_missing")
        return result
    if sha256_file(input_path) != lane["input_sha256"]:
        result.update(classification="failed", detail="input_hash_mismatch")
        return result
    input_rows = read_csv(input_path)
    if len(input_rows) != int(lane["expected_rows"]):
        result.update(classification="failed", detail="input_row_count_mismatch")
        return result
    input_ids = [row["triage_id"] for row in input_rows]
    input_queue_ids = [row["candidate_queue_row_id"] for row in input_rows]
    if len(input_ids) != len(set(input_ids)) or len(input_queue_ids) != len(
        set(input_queue_ids)
    ):
        result.update(classification="failed", detail="duplicate_input_identity")
        return result
    output_dir: Path | None = None
    mode = ""
    if metadata_dir.exists():
        output_dir, mode = metadata_dir, "metadata_only"
    elif live_dir.exists():
        output_dir, mode = live_dir, "live"
    elif dry_dir.exists():
        output_dir, mode = dry_dir, "dry_run"
    if output_dir is None:
        return result
    ledger_path = output_dir / "triage_ledger.csv"
    summary_path = output_dir / "triage_summary.json"
    timing_path = output_dir / "triage_timing.csv"
    if not ledger_path.exists() or not summary_path.exists() or not timing_path.exists():
        result.update(
            classification="missing_artifacts",
            detail="ledger_summary_or_timing_missing",
            mode=mode,
        )
        return result
    ledger = read_csv(ledger_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ledger_ids = [row.get("triage_id", "") for row in ledger]
    ledger_queue_ids = [row.get("candidate_queue_row_id", "") for row in ledger]
    statuses = Counter(row.get("triage_status", "") for row in ledger)
    priorities = Counter(
        row.get("priority_for_content_review", "") for row in ledger
    )
    actions = Counter(row.get("recommended_next_action", "") for row in ledger)
    readiness = Counter(
        row.get("extraction_readiness_prelim", "") for row in ledger
    )
    relevance = Counter(row.get("source_relevance_prelim", "") for row in ledger)
    terminal = (
        statuses["triage_planned"]
        if mode == "dry_run"
        else sum(statuses[status] for status in FUTURE_TERMINAL_STATUSES)
    )
    missing = len(set(input_ids) - set(ledger_ids))
    unexpected = len(set(ledger_ids) - set(input_ids))
    result.update(
        {
            "mode": mode,
            "ledger_rows": len(ledger),
            "terminal_rows": terminal,
            "duplicate_triage_ids": len(ledger_ids) - len(set(ledger_ids)),
            "duplicate_candidate_queue_ids": len(ledger_queue_ids)
            - len(set(ledger_queue_ids)),
            "missing_rows": missing,
            "unexpected_rows": unexpected,
            "triage_status_counts": dict(sorted(statuses.items())),
            "priority_for_content_review_counts": dict(sorted(priorities.items())),
            "recommended_next_action_counts": dict(sorted(actions.items())),
            "extraction_readiness_prelim_counts": dict(sorted(readiness.items())),
            "source_relevance_prelim_counts": dict(sorted(relevance.items())),
            "routing_status_to_triage_status": cross_tab(
                ledger, "verification_status", "triage_status"
            ),
            "disposition_to_priority": cross_tab(
                ledger,
                "candidate_status_before_verification",
                "priority_for_content_review",
            ),
            "urls_opened": int(summary.get("urls_opened", 0)),
            "network_calls": int(summary.get("network_calls", 0)),
            "documents_downloaded": int(summary.get("documents_downloaded", 0)),
            "documents_parsed": int(summary.get("documents_parsed", 0)),
            "content_artifacts_written": int(
                summary.get("content_artifacts_written", 0)
            ),
            "pdfs_parsed": int(summary.get("pdfs_parsed", 0)),
            "ocr_runs": int(summary.get("ocr_runs", 0)),
        }
    )
    identity_failure = (
        result["duplicate_triage_ids"]
        or result["duplicate_candidate_queue_ids"]
        or missing
        or unexpected
    )
    if identity_failure:
        result.update(classification="failed", detail="identity_coverage_failure")
    elif (
        mode == "dry_run"
        and summary.get("status") == "dry_run_passed"
        and terminal == len(input_rows)
        and not any(
            int(summary.get(field, 0))
            for field in (
                "urls_opened",
                "network_calls",
                "documents_downloaded",
                "documents_parsed",
                "content_artifacts_written",
            )
        )
    ):
        result.update(
            classification="dry_run_passed",
            detail="complete_offline_schema_plan",
        )
    elif (
        mode in {"metadata_only", "live"}
        and summary.get("status")
        in {"metadata_only_completed", "live_completed"}
        and terminal == len(input_rows)
        and not any(
            int(summary.get(field, 0))
            for field in (
                "urls_opened",
                "network_calls",
                "documents_downloaded",
                "documents_parsed",
                "pdfs_parsed",
                "ocr_runs",
                "content_artifacts_written",
            )
        )
    ):
        result.update(
            classification="completed_merge_eligible",
            detail="all_rows_terminal_offline_metadata_only",
        )
    elif mode in {"metadata_only", "live"} and terminal:
        result.update(classification="partial", detail="some_terminal_rows")
    else:
        result.update(classification="failed", detail="incomplete_or_unsafe_output")
    return result


def audit(manifest_path: Path, output_dir: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lanes = [
        classify_lane(lane, str(manifest["round_id"]))
        for lane in manifest["lanes"]
    ]
    all_input_triage_ids: list[str] = []
    all_input_queue_ids: list[str] = []
    for lane in manifest["lanes"]:
        rows = read_csv(Path(str(lane["input_csv"])))
        all_input_triage_ids.extend(row["triage_id"] for row in rows)
        all_input_queue_ids.extend(row["candidate_queue_row_id"] for row in rows)
    cross_lane_duplicate_triage_ids = len(all_input_triage_ids) - len(
        set(all_input_triage_ids)
    )
    cross_lane_duplicate_queue_ids = len(all_input_queue_ids) - len(
        set(all_input_queue_ids)
    )
    classifications = Counter(str(lane["classification"]) for lane in lanes)
    if lanes and classifications["completed_merge_eligible"] == len(lanes):
        recommendation = "merge_all_content_triage_lanes"
    elif classifications["completed_merge_eligible"]:
        recommendation = "merge_completed_lanes_only_with_user_approval"
    elif lanes and classifications["dry_run_passed"] == len(lanes):
        recommendation = "dry_run_complete_do_not_merge_live_triage"
    else:
        recommendation = "do_not_merge_until_resume_or_review"
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "round_id": manifest["round_id"],
        "manifest": manifest_path.as_posix(),
        "planned_rows": int(manifest["selected_rows"]),
        "lane_count": len(lanes),
        "ledger_rows": sum(int(lane["ledger_rows"]) for lane in lanes),
        "terminal_rows": sum(int(lane["terminal_rows"]) for lane in lanes),
        "cross_lane_duplicate_triage_ids": cross_lane_duplicate_triage_ids,
        "cross_lane_duplicate_candidate_queue_ids": cross_lane_duplicate_queue_ids,
        "classification_counts": dict(sorted(classifications.items())),
        "triage_status_counts": dict(
            sorted(
                sum(
                    (
                        Counter(lane["triage_status_counts"])
                        for lane in lanes
                    ),
                    Counter(),
                ).items()
            )
        ),
        "priority_for_content_review_counts": dict(
            sorted(
                sum(
                    (
                        Counter(lane["priority_for_content_review_counts"])
                        for lane in lanes
                    ),
                    Counter(),
                ).items()
            )
        ),
        "recommended_next_action_counts": dict(
            sorted(
                sum(
                    (
                        Counter(lane["recommended_next_action_counts"])
                        for lane in lanes
                    ),
                    Counter(),
                ).items()
            )
        ),
        "extraction_readiness_prelim_counts": dict(
            sorted(
                sum(
                    (
                        Counter(lane["extraction_readiness_prelim_counts"])
                        for lane in lanes
                    ),
                    Counter(),
                ).items()
            )
        ),
        "source_relevance_prelim_counts": dict(
            sorted(
                sum(
                    (
                        Counter(lane["source_relevance_prelim_counts"])
                        for lane in lanes
                    ),
                    Counter(),
                ).items()
            )
        ),
        "routing_status_to_triage_status": combine_cross_tabs(
            [
                lane["routing_status_to_triage_status"]
                for lane in lanes
            ]
        ),
        "disposition_to_priority": combine_cross_tabs(
            [lane["disposition_to_priority"] for lane in lanes]
        ),
        "urls_opened": sum(int(lane.get("urls_opened", 0)) for lane in lanes),
        "network_calls": sum(
            int(lane.get("network_calls", 0)) for lane in lanes
        ),
        "documents_downloaded": sum(
            int(lane.get("documents_downloaded", 0)) for lane in lanes
        ),
        "documents_parsed": sum(
            int(lane.get("documents_parsed", 0)) for lane in lanes
        ),
        "content_artifacts_written": sum(
            int(lane.get("content_artifacts_written", 0)) for lane in lanes
        ),
        "pdfs_parsed": sum(int(lane.get("pdfs_parsed", 0)) for lane in lanes),
        "ocr_runs": sum(int(lane.get("ocr_runs", 0)) for lane in lanes),
        "merge_recommendation": recommendation,
        "lanes": lanes,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "content_triage_lane_audit_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    report = [
        f"# Content-Triage Lane Audit — {manifest['round_id']}",
        "",
        f"- Planned rows: {payload['planned_rows']:,}",
        f"- Ledger rows: {payload['ledger_rows']:,}",
        f"- Terminal rows: {payload['terminal_rows']:,}",
        f"- Cross-lane duplicate triage IDs: {cross_lane_duplicate_triage_ids:,}",
        f"- Cross-lane duplicate candidate queue IDs: {cross_lane_duplicate_queue_ids:,}",
        f"- URLs opened: {payload['urls_opened']:,}",
        f"- Documents downloaded: {payload['documents_downloaded']:,}",
        f"- Documents parsed: {payload['documents_parsed']:,}",
        f"- Content artifacts written: {payload['content_artifacts_written']:,}",
        f"- Recommendation: `{recommendation}`",
        "",
        "| Lane | Classification | Expected | Ledger | Terminal |",
        "|---|---|---:|---:|---:|",
    ]
    for lane in lanes:
        report.append(
            f"| {lane['lane_id']} | `{lane['classification']}` | "
            f"{lane['expected_rows']} | {lane['ledger_rows']} | "
            f"{lane['terminal_rows']} |"
        )
    report.extend(
        [
            "",
            "## Combined preliminary distributions",
            "",
            f"- Triage statuses: `{json.dumps(payload['triage_status_counts'], sort_keys=True)}`",
            f"- Recommended next actions: `{json.dumps(payload['recommended_next_action_counts'], sort_keys=True)}`",
            f"- Extraction readiness: `{json.dumps(payload['extraction_readiness_prelim_counts'], sort_keys=True)}`",
            f"- Source relevance: `{json.dumps(payload['source_relevance_prelim_counts'], sort_keys=True)}`",
            f"- Content-review priorities: `{json.dumps(payload['priority_for_content_review_counts'], sort_keys=True)}`",
            f"- Routing status → triage status: `{json.dumps(payload['routing_status_to_triage_status'], sort_keys=True)}`",
            f"- Candidate disposition → priority: `{json.dumps(payload['disposition_to_priority'], sort_keys=True)}`",
            "",
            "The auditor does not update routing, scout accounting, contracts,",
            "ingestion, codification, extraction, or analytical evidence.",
            "",
        ]
    )
    (output_dir / "content_triage_lane_audit_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    (output_dir / "content_triage_merge_recommendation.md").write_text(
        f"# Content-Triage Merge Recommendation\n\n`{recommendation}`\n\n"
        "This audit recommendation does not authorize opening URLs, downloading "
        "or parsing content, or merging a durable triage ledger. Any merge "
        "requires a separate serial task.\n",
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = audit(Path(args.manifest), Path(args.output_dir))
    print(
        f"Content-triage lane audit: {payload['merge_recommendation']}; "
        f"rows={payload['ledger_rows']}; URLs opened={payload['urls_opened']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
