#!/usr/bin/env python3
"""Audit local text/table-detection lane outputs without durable mutation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from text_table_detection_sources import DRY_STATUS, TERMINAL_STATUSES


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
    return dict(
        sorted(Counter(row.get(field, "") for row in rows).items())
    )


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
        "duplicate_text_table_detection_ids": 0,
        "duplicate_pdf_readiness_ids": 0,
        "duplicate_source_review_ids": 0,
        "duplicate_candidate_queue_ids": 0,
        "missing_rows": expected,
        "unexpected_rows": 0,
        "detection_status_counts": {},
        "wage_table_signal_counts": {},
        "wage_table_signal_confidence_counts": {},
        "contract_period_signal_counts": {},
        "contract_period_confidence_counts": {},
        "table_like_structure_signal_counts": {},
        "extraction_pilot_priority_counts": {},
        "recommended_next_action_counts": {},
        "hash_failures": 0,
        "missing_artifacts": 0,
        "parser_errors": 0,
        "full_text_artifacts_found": 0,
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
    input_ids = [row["text_table_detection_id"] for row in inputs]
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

    ledger_path = output_dir / "text_table_detection_ledger.csv"
    summary_path = output_dir / "text_table_detection_summary.json"
    timing_path = output_dir / "text_table_detection_timing.csv"
    if not all(path.exists() for path in (ledger_path, summary_path, timing_path)):
        return {
            **base,
            "classification": "missing_artifacts",
            "detail": "ledger_summary_or_timing_missing",
            "mode": mode,
        }

    rows = read_csv(ledger_path)
    summary = read_json(summary_path)
    ids = [row.get("text_table_detection_id", "") for row in rows]
    readiness_ids = [row.get("pdf_readiness_id", "") for row in rows]
    review_ids = [row.get("source_review_id", "") for row in rows]
    candidate_ids = [
        row.get("candidate_queue_row_id", "") for row in rows
    ]
    missing = len(set(input_ids) - set(ids))
    unexpected = len(set(ids) - set(input_ids))
    status_counts = Counter(row.get("detection_status", "") for row in rows)
    terminal = (
        status_counts[DRY_STATUS]
        if mode == "dry_run"
        else sum(status_counts[status] for status in TERMINAL_STATUSES)
    )
    hash_failures = status_counts["hash_mismatch"]
    missing_artifacts = status_counts["artifact_missing"]
    parser_errors = status_counts["parser_error"]
    hint_overruns = sum(
        len(row.get("candidate_contract_period_text", "")) > 300
        for row in rows
    )
    candidate_page_errors = 0
    for row in rows:
        raw_pages = row.get("candidate_wage_pages", "")
        if not raw_pages:
            continue
        try:
            pages = [int(value) for value in raw_pages.split(",")]
            maximum = int(row["pdf_page_count"])
        except ValueError:
            candidate_page_errors += 1
            continue
        if any(page < 1 or page > maximum for page in pages):
            candidate_page_errors += 1
    full_text_artifacts = [
        path
        for path in output_dir.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in {".txt", ".text"}
            or "extracted_text" in path.name.lower()
            or "full_text" in path.name.lower()
        )
    ]
    forbidden_fields = (
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
    no_forbidden_activity = all(
        int(summary.get(field, -1)) == 0 for field in forbidden_fields
    )
    complete = (
        len(rows) == expected
        and terminal == expected
        and missing == 0
        and unexpected == 0
        and len(ids) == len(set(ids))
        and len(readiness_ids) == len(set(readiness_ids))
        and len(review_ids) == len(set(review_ids))
        and len(candidate_ids) == len(set(candidate_ids))
        and hint_overruns == 0
        and candidate_page_errors == 0
        and not full_text_artifacts
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
            "duplicate_text_table_detection_ids": len(ids) - len(set(ids)),
            "duplicate_pdf_readiness_ids": len(readiness_ids)
            - len(set(readiness_ids)),
            "duplicate_source_review_ids": len(review_ids)
            - len(set(review_ids)),
            "duplicate_candidate_queue_ids": len(candidate_ids)
            - len(set(candidate_ids)),
            "missing_rows": missing,
            "unexpected_rows": unexpected,
            "detection_status_counts": dict(sorted(status_counts.items())),
            "wage_table_signal_counts": distribution(
                rows, "wage_table_signal"
            ),
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
            "pages_scanned": sum(
                int(row.get("pages_scanned") or 0) for row in rows
            ),
            "pages_with_text": sum(
                int(row.get("pages_with_text") or 0) for row in rows
            ),
            "total_text_chars_scanned": sum(
                int(row.get("total_text_chars_scanned") or 0)
                for row in rows
            ),
            "candidate_wage_page_hints": sum(
                int(row.get("candidate_wage_page_count") or 0)
                for row in rows
            ),
            "maximum_contract_hint_characters": max(
                (
                    len(row.get("candidate_contract_period_text", ""))
                    for row in rows
                ),
                default=0,
            ),
            "hash_failures": hash_failures,
            "missing_artifacts": missing_artifacts,
            "parser_errors": parser_errors,
            "hint_overruns": hint_overruns,
            "candidate_page_errors": candidate_page_errors,
            "full_text_artifacts_found": len(full_text_artifacts),
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
        "dry_run_complete_no_text_table_merge"
        if all_dry
        else "merge_all_text_table_detection_lanes"
        if all_complete
        else "do_not_merge_until_resume_or_review"
    )

    all_rows: list[dict[str, str]] = []
    for lane in lanes:
        output = lane.get("output_dir")
        if output:
            all_rows.extend(
                read_csv(
                    Path(str(output))
                    / "text_table_detection_ledger.csv"
                )
            )
    identity_fields = (
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    )
    duplicate_counts = {}
    for field in identity_fields:
        values = [row.get(field, "") for row in all_rows]
        duplicate_counts[field] = len(values) - len(set(values))

    distribution_fields = (
        "detection_status_counts",
        "wage_table_signal_counts",
        "wage_table_signal_confidence_counts",
        "contract_period_signal_counts",
        "contract_period_confidence_counts",
        "table_like_structure_signal_counts",
        "extraction_pilot_priority_counts",
        "recommended_next_action_counts",
    )
    payload: dict[str, object] = {
        "schema_version": "1.0.0",
        "pilot_id": manifest["pilot_id"],
        "manifest": manifest_path.as_posix(),
        "planned_rows": planned,
        "ledger_rows": ledger_rows,
        "terminal_rows": terminal_rows,
        "lane_classification_counts": dict(sorted(classifications.items())),
        "lanes": lanes,
        "cross_lane_duplicate_text_table_detection_ids": duplicate_counts[
            "text_table_detection_id"
        ],
        "cross_lane_duplicate_pdf_readiness_ids": duplicate_counts[
            "pdf_readiness_id"
        ],
        "cross_lane_duplicate_source_review_ids": duplicate_counts[
            "source_review_id"
        ],
        "cross_lane_duplicate_candidate_queue_ids": duplicate_counts[
            "candidate_queue_row_id"
        ],
        **{
            field: combine_distributions(lanes, field)
            for field in distribution_fields
        },
        "pages_scanned": sum(
            int(lane.get("pages_scanned", 0)) for lane in lanes
        ),
        "pages_with_text": sum(
            int(lane.get("pages_with_text", 0)) for lane in lanes
        ),
        "total_text_chars_scanned": sum(
            int(lane.get("total_text_chars_scanned", 0))
            for lane in lanes
        ),
        "candidate_wage_page_hints": sum(
            int(lane.get("candidate_wage_page_hints", 0))
            for lane in lanes
        ),
        "maximum_contract_hint_characters": max(
            (
                int(lane.get("maximum_contract_hint_characters", 0))
                for lane in lanes
            ),
            default=0,
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
        "hint_overruns": sum(
            int(lane.get("hint_overruns", 0)) for lane in lanes
        ),
        "candidate_page_errors": sum(
            int(lane.get("candidate_page_errors", 0)) for lane in lanes
        ),
        "full_text_artifacts_found": sum(
            int(lane.get("full_text_artifacts_found", 0))
            for lane in lanes
        ),
        "urls_opened": 0,
        "network_calls": 0,
        "downloads": 0,
        "redownloads": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "final_wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_text_table_merges": 0,
        "merge_recommendation": recommendation,
    }
    write_json_path = (
        output_dir / "text_table_detection_lane_audit_summary.json"
    )
    with write_json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    report_lines = [
        "# Text/Table Detection Lane Audit",
        "",
        f"- pilot: `{manifest['pilot_id']}`",
        "- planned / ledger / terminal: "
        f"{planned} / {ledger_rows} / {terminal_rows}",
        f"- classifications: `{dict(sorted(classifications.items()))}`",
        f"- detection statuses: `{payload['detection_status_counts']}`",
        f"- wage-table signals: `{payload['wage_table_signal_counts']}`",
        "- contract-period signals: "
        f"`{payload['contract_period_signal_counts']}`",
        "- table-like structure: "
        f"`{payload['table_like_structure_signal_counts']}`",
        "- extraction priorities: "
        f"`{payload['extraction_pilot_priority_counts']}`",
        f"- pages scanned / with text: {payload['pages_scanned']} / "
        f"{payload['pages_with_text']}",
        f"- parser errors: {payload['parser_errors']}",
        "- hash failures / missing artifacts: "
        f"{payload['hash_failures']} / {payload['missing_artifacts']}",
        "- URLs / network / downloads / OCR / full text / wage values: "
        "0 / 0 / 0 / 0 / 0 / 0",
        f"- recommendation: `{recommendation}`",
        "",
        "Signals are preliminary deterministic page hints. They are not "
        "final wage observations, ingested or codified evidence, wage-gap "
        "findings, or causal claims.",
        "",
    ]
    (
        output_dir / "text_table_detection_lane_audit_report.md"
    ).write_text("\n".join(report_lines), encoding="utf-8")
    (
        output_dir / "text_table_detection_merge_recommendation.md"
    ).write_text(
        "\n".join(
            [
                "# Text/Table Detection Merge Recommendation",
                "",
                f"`{recommendation}`",
                "",
                "This recommendation concerns structural lane "
                "mergeability only. It does not authorize a durable merge, "
                "OCR, final wage extraction, ingestion, codification, wage "
                "analysis, or causal inference.",
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
        "Text/table detection lane audit: "
        f"{result['terminal_rows']}/{result['planned_rows']} rows; "
        f"{result['merge_recommendation']}."
    )


if __name__ == "__main__":
    main()
