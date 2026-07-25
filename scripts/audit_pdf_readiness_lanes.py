#!/usr/bin/env python3
"""Audit local PDF-readiness lane outputs without mutating durable layers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from pdf_readiness_sources import DRY_STATUS, TERMINAL_STATUSES


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    return {
        "count": len(values),
        "minimum": min(values) if values else None,
        "median": percentile(values, 0.5),
        "p90": percentile(values, 0.9),
        "maximum": max(values) if values else None,
        "total_pages": sum(values),
        "buckets": dict(sorted(buckets.items())),
    }


def classify_lane(lane: dict[str, object]) -> dict[str, object]:
    input_path = Path(str(lane["input_csv"]))
    dry_dir = Path(str(lane["dry_run_output_dir"]))
    local_dir = Path(str(lane["future_local_output_dir"]))
    expected = int(lane["expected_rows"])
    base: dict[str, object] = {
        "lane_id": lane["lane_id"],
        "expected_rows": expected,
        "classification": "not_started",
        "mode": "",
        "ledger_rows": 0,
        "terminal_rows": 0,
        "duplicate_pdf_readiness_ids": 0,
        "duplicate_source_review_ids": 0,
        "duplicate_candidate_queue_ids": 0,
        "missing_rows": expected,
        "unexpected_rows": 0,
        "readiness_status_counts": {},
        "text_layer_status_counts": {},
        "technical_parseability_rating_counts": {},
        "recommended_next_action_counts": {},
        "page_count_summary": page_summary([]),
        "hash_failures": 0,
        "missing_artifacts": 0,
        "parser_errors": 0,
    }
    if not input_path.exists():
        return {
            **base,
            "classification": "missing_artifacts",
            "detail": "input_missing",
        }
    if sha256_file(input_path) != lane["input_sha256"]:
        return {
            **base,
            "classification": "failed",
            "detail": "input_hash_mismatch",
        }
    inputs = read_csv(input_path)
    if len(inputs) != expected:
        return {
            **base,
            "classification": "failed",
            "detail": "input_row_count_mismatch",
        }
    input_ids = [row["pdf_readiness_id"] for row in inputs]
    if len(input_ids) != len(set(input_ids)):
        return {
            **base,
            "classification": "failed",
            "detail": "duplicate_input_identity",
        }
    output_dir: Path | None = None
    mode = ""
    if local_dir.exists():
        output_dir, mode = local_dir, "local"
    elif dry_dir.exists():
        output_dir, mode = dry_dir, "dry_run"
    if output_dir is None:
        return base
    ledger_path = output_dir / "pdf_readiness_ledger.csv"
    summary_path = output_dir / "pdf_readiness_summary.json"
    timing_path = output_dir / "pdf_readiness_timing.csv"
    if not all(path.exists() for path in (ledger_path, summary_path, timing_path)):
        return {
            **base,
            "classification": "missing_artifacts",
            "detail": "ledger_summary_or_timing_missing",
            "mode": mode,
        }
    rows = read_csv(ledger_path)
    summary = read_json(summary_path)
    ids = [row.get("pdf_readiness_id", "") for row in rows]
    review_ids = [row.get("source_review_id", "") for row in rows]
    candidate_ids = [row.get("candidate_queue_row_id", "") for row in rows]
    missing = len(set(input_ids) - set(ids))
    unexpected = len(set(ids) - set(input_ids))
    status_counts = Counter(row.get("readiness_status", "") for row in rows)
    terminal = (
        status_counts[DRY_STATUS]
        if mode == "dry_run"
        else sum(status_counts[status] for status in TERMINAL_STATUSES)
    )
    hash_failures = sum(
        row.get("artifact_hash_verified") == "no" for row in rows
    )
    missing_artifacts = status_counts["artifact_missing"]
    parser_errors = status_counts["parser_error"]
    no_forbidden_activity = all(
        int(summary.get(field, -1)) == 0
        for field in (
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
            "durable_readiness_merges",
        )
    )
    complete = (
        len(rows) == expected
        and terminal == expected
        and missing == 0
        and unexpected == 0
        and len(ids) == len(set(ids))
        and len(review_ids) == len(set(review_ids))
        and len(candidate_ids) == len(set(candidate_ids))
        and no_forbidden_activity
    )
    if mode == "dry_run":
        classification = "dry_run_passed" if complete else "failed"
    elif complete and missing_artifacts:
        classification = "missing_artifacts"
    elif complete and hash_failures:
        classification = "failed"
    elif complete:
        classification = "completed_merge_eligible"
    elif rows and terminal:
        classification = "partial"
    else:
        classification = "failed"
    base.update(
        {
            "classification": classification,
            "detail": "complete" if complete else "coverage_or_safety_failure",
            "mode": mode,
            "output_dir": output_dir.as_posix(),
            "ledger_rows": len(rows),
            "terminal_rows": terminal,
            "duplicate_pdf_readiness_ids": len(ids) - len(set(ids)),
            "duplicate_source_review_ids": len(review_ids)
            - len(set(review_ids)),
            "duplicate_candidate_queue_ids": len(candidate_ids)
            - len(set(candidate_ids)),
            "missing_rows": missing,
            "unexpected_rows": unexpected,
            "readiness_status_counts": dict(sorted(status_counts.items())),
            "text_layer_status_counts": distribution(
                rows, "text_layer_status"
            ),
            "technical_parseability_rating_counts": distribution(
                rows, "technical_parseability_rating"
            ),
            "recommended_next_action_counts": distribution(
                rows, "recommended_next_action"
            ),
            "page_count_summary": page_summary(rows),
            "sampled_pages_checked": sum(
                int(row.get("sampled_pages_checked") or 0) for row in rows
            ),
            "sampled_pages_with_text": sum(
                int(row.get("sampled_pages_with_text") or 0) for row in rows
            ),
            "text_chars_sampled_total": sum(
                int(row.get("text_chars_sampled_total") or 0) for row in rows
            ),
            "hash_failures": hash_failures,
            "missing_artifacts": missing_artifacts,
            "parser_errors": parser_errors,
            "no_forbidden_activity": no_forbidden_activity,
            "summary_status": summary.get("status", ""),
        }
    )
    return base


def combine_distributions(
    lanes: list[dict[str, object]], field: str
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for lane in lanes:
        counts.update(lane.get(field, {}))
    return dict(sorted(counts.items()))


def audit(manifest_path: Path, output_dir: Path) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    manifest = read_json(manifest_path)
    lanes = [classify_lane(lane) for lane in manifest["lanes"]]
    output_dir.mkdir(parents=True)
    planned = int(manifest["selected_rows"])
    ledger_rows = sum(int(lane["ledger_rows"]) for lane in lanes)
    terminal_rows = sum(int(lane["terminal_rows"]) for lane in lanes)
    classifications = Counter(
        str(lane["classification"]) for lane in lanes
    )
    all_dry = classifications == Counter({"dry_run_passed": len(lanes)})
    all_complete = classifications == Counter(
        {"completed_merge_eligible": len(lanes)}
    )
    recommendation = (
        "dry_run_complete_no_local_readiness_merge"
        if all_dry
        else "merge_all_pdf_readiness_lanes"
        if all_complete
        else "do_not_merge_until_resume_or_review"
    )
    all_rows: list[dict[str, str]] = []
    for lane in lanes:
        output = lane.get("output_dir")
        if output:
            all_rows.extend(
                read_csv(Path(str(output)) / "pdf_readiness_ledger.csv")
            )
    readiness_ids = [row.get("pdf_readiness_id", "") for row in all_rows]
    review_ids = [row.get("source_review_id", "") for row in all_rows]
    candidate_ids = [
        row.get("candidate_queue_row_id", "") for row in all_rows
    ]
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "pilot_id": manifest["pilot_id"],
        "manifest": manifest_path.as_posix(),
        "planned_rows": planned,
        "ledger_rows": ledger_rows,
        "terminal_rows": terminal_rows,
        "lane_classification_counts": dict(sorted(classifications.items())),
        "lanes": lanes,
        "cross_lane_duplicate_pdf_readiness_ids": len(readiness_ids)
        - len(set(readiness_ids)),
        "cross_lane_duplicate_source_review_ids": len(review_ids)
        - len(set(review_ids)),
        "cross_lane_duplicate_candidate_queue_ids": len(candidate_ids)
        - len(set(candidate_ids)),
        "readiness_status_counts": combine_distributions(
            lanes, "readiness_status_counts"
        ),
        "text_layer_status_counts": combine_distributions(
            lanes, "text_layer_status_counts"
        ),
        "technical_parseability_rating_counts": combine_distributions(
            lanes, "technical_parseability_rating_counts"
        ),
        "recommended_next_action_counts": combine_distributions(
            lanes, "recommended_next_action_counts"
        ),
        "page_count_summary": page_summary(all_rows),
        "sampled_pages_checked": sum(
            int(lane.get("sampled_pages_checked", 0)) for lane in lanes
        ),
        "sampled_pages_with_text": sum(
            int(lane.get("sampled_pages_with_text", 0)) for lane in lanes
        ),
        "text_chars_sampled_total": sum(
            int(lane.get("text_chars_sampled_total", 0)) for lane in lanes
        ),
        "hash_failures": sum(
            int(lane.get("hash_failures", 0)) for lane in lanes
        ),
        "missing_artifacts": sum(
            int(lane.get("missing_artifacts", 0)) for lane in lanes
        ),
        "parser_errors": sum(
            int(lane.get("parser_errors", 0)) for lane in lanes
        ),
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_readiness_merges": 0,
        "merge_recommendation": recommendation,
    }
    with (output_dir / "pdf_readiness_lane_audit_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    report_lines = [
        "# PDF-Readiness Lane Audit",
        "",
        f"- pilot: `{manifest['pilot_id']}`",
        f"- planned / ledger / terminal: {planned} / {ledger_rows} / {terminal_rows}",
        f"- classifications: `{dict(sorted(classifications.items()))}`",
        f"- readiness statuses: `{payload['readiness_status_counts']}`",
        f"- text-layer statuses: `{payload['text_layer_status_counts']}`",
        f"- parseability: `{payload['technical_parseability_rating_counts']}`",
        f"- page count: `{payload['page_count_summary']}`",
        f"- parser errors: {payload['parser_errors']}",
        f"- hash failures / missing artifacts: {payload['hash_failures']} / {payload['missing_artifacts']}",
        "- URLs / network / downloads / OCR / text artifacts: 0 / 0 / 0 / 0 / 0",
        f"- recommendation: `{recommendation}`",
        "",
        "Technical readiness does not establish document relevance, wage-table "
        "presence, wage values, ingestion readiness, or empirical findings.",
        "",
    ]
    (output_dir / "pdf_readiness_lane_audit_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    (output_dir / "pdf_readiness_merge_recommendation.md").write_text(
        "\n".join(
            [
                "# PDF-Readiness Merge Recommendation",
                "",
                f"`{recommendation}`",
                "",
                "This recommendation concerns structural readiness-ledger "
                "mergeability only. It does not authorize a durable merge, "
                "OCR, wage extraction, ingestion, codification, or analysis.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = audit(Path(args.manifest), Path(args.output_dir))
    print(
        "PDF-readiness lane audit: "
        f"{result['terminal_rows']}/{result['planned_rows']} rows; "
        f"{result['merge_recommendation']}."
    )


if __name__ == "__main__":
    main()
