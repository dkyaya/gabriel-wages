#!/usr/bin/env python3
"""Prepare an offline stratified manual text/table calibration packet.

The planner reads durable CSV ledgers only. It does not inspect artifact
existence, open PDFs or URLs, extract text, call a network service, run OCR,
or make manual calibration judgments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ("likely", "possible", "unlikely")
DIMENSIONS = (
    "candidate_source_type",
    "source_officialness_rating",
    "source_review_pilot_id",
    "page_count_bin",
    "unit_type",
    "extraction_pilot_priority",
    "recommended_next_action",
    "text_layer_status",
    "state",
    "municipality",
)
DIMENSION_WEIGHTS = {
    "candidate_source_type": 12,
    "source_officialness_rating": 8,
    "source_review_pilot_id": 7,
    "page_count_bin": 8,
    "unit_type": 8,
    "extraction_pilot_priority": 10,
    "recommended_next_action": 8,
    "text_layer_status": 5,
    "state": 6,
    "municipality": 2,
}
REQUIRED_DETECTION_FIELDS = {
    "text_table_detection_id",
    "pdf_readiness_id",
    "source_review_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "priority_for_content_review",
    "source_officialness_rating",
    "source_relevance_rating",
    "document_type_rating",
    "pdf_page_count",
    "content_artifact_path",
    "wage_table_signal",
    "wage_table_signal_confidence",
    "contract_period_signal",
    "contract_period_confidence",
    "table_like_structure_signal",
    "candidate_wage_pages",
    "candidate_wage_page_count",
    "candidate_contract_period_text",
    "detection_notes",
    "source_review_pilot_id",
    "page_count_bin",
    "text_layer_status",
    "extraction_pilot_priority",
    "recommended_next_action",
    "table_detection_method",
    "detection_status",
}
INHERITED_FIELDS = [
    "text_table_detection_id",
    "pdf_readiness_id",
    "source_review_id",
    "candidate_queue_row_id",
    "state",
    "municipality",
    "government_name",
    "unit_type",
    "candidate_source_type",
    "priority_for_content_review",
    "source_officialness_rating",
    "source_relevance_rating",
    "document_type_rating",
    "pdf_page_count",
    "content_artifact_path",
    "wage_table_signal",
    "contract_period_signal",
    "table_like_structure_signal",
    "candidate_wage_pages",
    "candidate_wage_page_count",
    "detection_notes",
]
PROVENANCE_FIELDS = [
    "calibration_round_id",
    "calibration_selection_rank",
    "calibration_selection_reason",
    "source_review_pilot_id",
    "page_count_bin",
    "text_layer_status",
    "wage_table_signal_confidence",
    "contract_period_confidence",
    "candidate_contract_period_text",
    "extraction_pilot_priority",
    "recommended_next_action",
    "table_detection_method",
]
MANUAL_FIELDS = [
    "reviewer",
    "reviewed_at",
    "calibration_status",
    "page_hint_precision_label",
    "wage_table_present_label",
    "wage_table_page_match_label",
    "contract_period_present_label",
    "contract_period_hint_match_label",
    "table_layout_type",
    "extraction_complexity_label",
    "false_positive_family",
    "extraction_schema_notes",
    "recommended_extraction_action",
    "reviewer_confidence",
    "reviewer_notes",
]
OUTPUT_FIELDS = [
    "calibration_id",
    *INHERITED_FIELDS,
    *PROVENANCE_FIELDS,
    *MANUAL_FIELDS,
]
FORBIDDEN_OUTPUT_FIELD_PARTS = (
    "full_text",
    "complete_page_text",
    "complete_document_text",
    "final_wage_value",
    "extracted_wage_value",
)


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(
    path: Path, rows: list[dict[str, str]], fields: list[str]
) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hex(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


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


def validate_detection_rows(
    fields: list[str], rows: list[dict[str, str]]
) -> None:
    missing = sorted(REQUIRED_DETECTION_FIELDS - set(fields))
    if missing:
        raise ValueError(f"detection ledger missing fields: {missing}")
    if any(
        part in field.lower()
        for field in fields
        for part in FORBIDDEN_OUTPUT_FIELD_PARTS
    ):
        raise ValueError("detection ledger contains prohibited full/final field")
    if not rows:
        raise ValueError("detection ledger is empty")
    for field in (
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        require_unique(rows, field)
    for row in rows:
        if row["detection_status"] != "detection_checked":
            raise ValueError("calibration authority contains nonterminal row")
        if row["wage_table_signal"] not in SIGNALS:
            raise ValueError("unsupported wage-table signal")
        if len(row["candidate_contract_period_text"]) > 300:
            raise ValueError("bounded contract-period hint exceeds 300 chars")
        try:
            count = int(row["candidate_wage_page_count"])
            pages = (
                [int(value) for value in row["candidate_wage_pages"].split(",")]
                if row["candidate_wage_pages"]
                else []
            )
        except ValueError as exc:
            raise ValueError("invalid candidate wage-page hint") from exc
        if count != len(pages):
            raise ValueError("candidate wage-page count mismatch")


def signal_targets(
    rows: list[dict[str, str]],
    sample_size: int,
    include_unlikely: bool,
) -> dict[str, int]:
    available = Counter(row["wage_table_signal"] for row in rows)
    unlikely = available["unlikely"] if include_unlikely else 0
    if unlikely > sample_size:
        raise ValueError("all unlikely rows exceed requested sample size")
    likely = min(
        available["likely"],
        round(sample_size * 80 / 150),
        sample_size - unlikely,
    )
    possible = sample_size - unlikely - likely
    if possible > available["possible"]:
        transfer = possible - available["possible"]
        possible = available["possible"]
        likely += transfer
    if likely > available["likely"]:
        raise ValueError("insufficient likely/possible rows for sample")
    targets = {"likely": likely, "possible": possible, "unlikely": unlikely}
    if sum(targets.values()) != sample_size:
        raise ValueError("signal allocation does not equal requested sample")
    return targets


def greedy_select(
    pool: list[dict[str, str]],
    count: int,
    *,
    calibration_round_id: str,
    selected: list[dict[str, str]],
    frequencies: dict[str, Counter[str]],
) -> list[dict[str, str]]:
    chosen: list[dict[str, str]] = []
    remaining = {
        row["text_table_detection_id"]: row
        for row in pool
        if row["text_table_detection_id"]
        not in {item["text_table_detection_id"] for item in selected}
    }
    seen: dict[str, Counter[str]] = {
        field: Counter(row.get(field, "") for row in selected)
        for field in DIMENSIONS
    }
    while len(chosen) < count:
        if not remaining:
            raise ValueError("stratified selection pool exhausted")

        def score(row: dict[str, str]) -> tuple[int, int]:
            total = 0
            for field in DIMENSIONS:
                value = row.get(field, "")
                weight = DIMENSION_WEIGHTS[field]
                if seen[field][value] == 0:
                    total += weight * 1_000_000
                total += weight * 100_000 // max(
                    1, frequencies[field][value]
                )
                total -= weight * 1_000 * seen[field][value]
            if row.get("recommended_next_action") == "manual_review":
                total += 3_000_000
            if row.get("extraction_pilot_priority") == "p3":
                total += 3_000_000
            tie = -int(
                stable_hex(
                    calibration_round_id,
                    row["text_table_detection_id"],
                ),
                16,
            )
            return total, tie

        best = max(remaining.values(), key=score)
        chosen.append(best)
        selected.append(best)
        remaining.pop(best["text_table_detection_id"])
        for field in DIMENSIONS:
            seen[field][best.get(field, "")] += 1
    return chosen


def select_rows(
    rows: list[dict[str, str]],
    *,
    sample_size: int,
    include_unlikely: bool,
    calibration_round_id: str,
) -> tuple[list[dict[str, str]], dict[str, int], dict[str, str]]:
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    if sample_size > len(rows):
        raise ValueError("sample size exceeds durable detection rows")
    targets = signal_targets(rows, sample_size, include_unlikely)
    frequencies = {
        field: Counter(row.get(field, "") for row in rows)
        for field in DIMENSIONS
    }
    reasons: dict[str, str] = {}
    selected: list[dict[str, str]] = []

    unlikely_rows = sorted(
        (row for row in rows if row["wage_table_signal"] == "unlikely"),
        key=lambda row: stable_hex(
            calibration_round_id, row["text_table_detection_id"]
        ),
    )
    for row in unlikely_rows[: targets["unlikely"]]:
        selected.append(row)
        reasons[row["text_table_detection_id"]] = (
            "all_unlikely_boundary_case"
        )

    possible_pool = [
        row for row in rows if row["wage_table_signal"] == "possible"
    ]
    possible_preselected = sorted(
        (
            row
            for row in possible_pool
            if row["extraction_pilot_priority"] == "p3"
            or row["recommended_next_action"] == "manual_review"
        ),
        key=lambda row: stable_hex(
            calibration_round_id, row["text_table_detection_id"]
        ),
    )
    for row in possible_preselected:
        if len(
            [
                item
                for item in selected
                if item["wage_table_signal"] == "possible"
            ]
        ) >= targets["possible"]:
            break
        selected.append(row)
        reasons[row["text_table_detection_id"]] = "manual_review_p3_edge"

    edge_candidates = sorted(
        (
            row
            for row in possible_pool
            if row["text_table_detection_id"]
            not in {item["text_table_detection_id"] for item in selected}
            and row["text_layer_status"] == "partial"
            and row["page_count_bin"] == "over_100"
        ),
        key=lambda row: stable_hex(
            calibration_round_id, row["text_table_detection_id"]
        ),
    )
    if edge_candidates and targets["possible"] > len(possible_preselected):
        edge = edge_candidates[0]
        selected.append(edge)
        reasons[edge["text_table_detection_id"]] = (
            "partial_text_over_100_edge"
        )

    possible_have = sum(
        row["wage_table_signal"] == "possible" for row in selected
    )
    added_possible = greedy_select(
        possible_pool,
        targets["possible"] - possible_have,
        calibration_round_id=calibration_round_id,
        selected=selected,
        frequencies=frequencies,
    )
    for row in added_possible:
        reasons[row["text_table_detection_id"]] = "stratified_possible"

    likely_pool = [
        row for row in rows if row["wage_table_signal"] == "likely"
    ]
    added_likely = greedy_select(
        likely_pool,
        targets["likely"],
        calibration_round_id=calibration_round_id,
        selected=selected,
        frequencies=frequencies,
    )
    for row in added_likely:
        reasons[row["text_table_detection_id"]] = "stratified_likely"

    selected.sort(
        key=lambda row: (
            SIGNALS.index(row["wage_table_signal"]),
            stable_hex(calibration_round_id, row["text_table_detection_id"]),
        )
    )
    if len(selected) != sample_size:
        raise ValueError("selected row count mismatch")
    for field in (
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        require_unique(selected, field)
    if distribution(selected, "wage_table_signal") != targets:
        raise ValueError("selected signal allocation mismatch")
    return selected, targets, reasons


def verify_supporting_ledgers(
    selected: list[dict[str, str]],
    pdf_path: Path,
    source_path: Path,
) -> dict[str, object]:
    _, pdf_rows = read_csv(pdf_path)
    _, source_rows = read_csv(source_path)
    pdf_by_id = {row["pdf_readiness_id"]: row for row in pdf_rows}
    source_by_id = {row["source_review_id"]: row for row in source_rows}
    missing_pdf = [
        row["pdf_readiness_id"]
        for row in selected
        if row["pdf_readiness_id"] not in pdf_by_id
    ]
    missing_source = [
        row["source_review_id"]
        for row in selected
        if row["source_review_id"] not in source_by_id
    ]
    if missing_pdf or missing_source:
        raise ValueError("selected identities missing from supporting ledgers")
    mismatch_counts: Counter[str] = Counter()
    for row in selected:
        pdf = pdf_by_id[row["pdf_readiness_id"]]
        source = source_by_id[row["source_review_id"]]
        for field in (
            "source_review_id",
            "candidate_queue_row_id",
            "content_artifact_path",
            "pdf_page_count",
            "text_layer_status",
        ):
            if row.get(field, "") != pdf.get(field, ""):
                mismatch_counts[f"pdf:{field}"] += 1
        for field in (
            "candidate_queue_row_id",
            "content_artifact_path",
        ):
            if row.get(field, "") != source.get(field, ""):
                mismatch_counts[f"source:{field}"] += 1
    if mismatch_counts:
        raise ValueError(
            "supporting-ledger mismatch: "
            + json.dumps(dict(sorted(mismatch_counts.items())))
        )
    return {
        "selected_pdf_readiness_identity_coverage": len(selected),
        "selected_source_review_identity_coverage": len(selected),
        "supporting_field_mismatch_counts": {},
    }


def output_row(
    row: dict[str, str],
    *,
    calibration_round_id: str,
    rank: int,
    reason: str,
) -> dict[str, str]:
    values = {
        "calibration_id": "cal_"
        + stable_hex(
            calibration_round_id, row["text_table_detection_id"]
        )[:24],
        **{field: row.get(field, "") for field in INHERITED_FIELDS},
        "calibration_round_id": calibration_round_id,
        "calibration_selection_rank": str(rank),
        "calibration_selection_reason": reason,
        **{
            field: row.get(field, "")
            for field in PROVENANCE_FIELDS
            if field
            not in {
                "calibration_round_id",
                "calibration_selection_rank",
                "calibration_selection_reason",
            }
        },
        "reviewer": "",
        "reviewed_at": "",
        "calibration_status": "not_reviewed",
        "page_hint_precision_label": "unknown",
        "wage_table_present_label": "unknown",
        "wage_table_page_match_label": "unknown",
        "contract_period_present_label": "unknown",
        "contract_period_hint_match_label": "unknown",
        "table_layout_type": "unknown",
        "extraction_complexity_label": "unknown",
        "false_positive_family": "unknown",
        "extraction_schema_notes": "",
        "recommended_extraction_action": "unknown",
        "reviewer_confidence": "unknown",
        "reviewer_notes": "",
    }
    return {field: values.get(field, "") for field in OUTPUT_FIELDS}


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def workbook_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Calibration Review Workbook",
        "",
        "Status: `prepared_not_reviewed`",
        "",
        "This is an index into `calibration_review_input.csv`. During the "
        "future manual-review task, work from a copy or separately named "
        "reviewed output. Do not modify durable ledgers and do not paste full "
        "page/document text or final wage values.",
        "",
        "Recommended review sequence:",
        "",
        "1. Review all unlikely and p3/manual-review edge rows.",
        "2. Review possible rows across source/layout strata.",
        "3. Review likely rows across the same strata.",
        "4. Send ambiguous or identity-problem rows to second review.",
        "",
    ]
    for start in range(0, len(rows), 50):
        packet = rows[start : start + 50]
        lines.extend(
            [
                f"## Review block {start // 50 + 1}: rows "
                f"{start + 1}–{start + len(packet)}",
                "",
                "| Rank | Calibration ID | Signal | Priority | State / municipality | Unit | Source | Candidate pages | Artifact path |",
                "|---:|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in packet:
            location = f"{row['state']} / {row['municipality']}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        row["calibration_selection_rank"],
                        f"`{row['calibration_id']}`",
                        row["wage_table_signal"],
                        row["extraction_pilot_priority"],
                        markdown_escape(location),
                        markdown_escape(row["unit_type"]),
                        markdown_escape(row["candidate_source_type"]),
                        markdown_escape(
                            row["candidate_wage_pages"] or "none"
                        ),
                        f"`{markdown_escape(row['content_artifact_path'])}`",
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def rubric_markdown() -> str:
    return """# Calibration Review Rubric

## Review unit

One row represents one retained PDF and its frozen candidate-page hints.
Reviewers later open the local artifact, inspect the hinted pages and nearby
pages when necessary, and label the row. Preparation does not open PDFs.

## Required review order

1. Confirm the artifact identity corresponds to the municipality, unit, and
   source metadata. Do not revise durable metadata in this file.
2. Inspect each candidate wage page, plus an immediately adjacent page only
   when needed to understand a split table.
3. Determine whether a genuine wage/pay schedule is present.
4. Compare the bounded contract-period hint with the document.
5. Record layout, difficulty, false-positive family, recommended action, and
   confidence.

## Core labels

- `page_hint_precision_label=correct`: all or substantively all hinted pages
  identify the wage table.
- `partially_correct`: at least one hint is useful but one or more hints are
  irrelevant, incomplete, or adjacent.
- `incorrect`: hints do not identify a wage table.
- `wage_table_present_label=yes`: a structured wage/pay schedule is visible.
- `maybe`: compensation information exists but table identity or scope is
  ambiguous.
- `no`: no wage table is found under the bounded review protocol.
- `wage_table_page_match_label=exact`: hinted page contains the relevant
  table; `nearby`: table is immediately adjacent; `wrong_page`: table exists
  elsewhere; `no_wage_table`: none is present.

## Contract-period labels

Use `correct` only when the bounded hint corresponds to the operative
agreement/contract period. Use `partially_correct` for a real but incomplete
or secondary date range, `incorrect` for unrelated dates, and
`no_period_found` when no period can be located under bounded review.

## False-positive families

Use short consistent labels such as `benefit_table`, `premium_or_allowance`,
`percentage_prose`, `classification_without_pay`, `numeric_appendix`,
`index_or_contents`, `date_table`, `non_wage_schedule`, or `other:<short>`.
Do not paste full text.

## Extraction boundary

Do not transcribe full tables or final wage values during calibration. Record
only structural labels and short notes necessary to design a later extraction
schema. Mark ambiguous cases `needs_second_review`.
"""


def build_summary(
    selected: list[dict[str, str]],
    *,
    calibration_round_id: str,
    source_rows: list[dict[str, str]],
    targets: dict[str, int],
    ledger_path: Path,
    pdf_path: Path,
    source_path: Path,
    support: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "status": "text_table_calibration_subset1_prepared_not_reviewed",
        "calibration_id": calibration_round_id,
        "created_at": now_utc(),
        "durable_detection_ledger_csv": ledger_path.as_posix(),
        "durable_detection_ledger_sha256": sha256_file(ledger_path),
        "durable_detection_rows": len(source_rows),
        "pdf_readiness_ledger_csv": pdf_path.as_posix(),
        "pdf_readiness_ledger_sha256": sha256_file(pdf_path),
        "source_review_ledger_csv": source_path.as_posix(),
        "source_review_ledger_sha256": sha256_file(source_path),
        "calibration_subset_rows": len(selected),
        "signal_targets": targets,
        "wage_table_signal_counts": distribution(
            selected, "wage_table_signal"
        ),
        "extraction_pilot_priority_counts": distribution(
            selected, "extraction_pilot_priority"
        ),
        "priority_for_content_review_counts": distribution(
            selected, "priority_for_content_review"
        ),
        "unit_type_counts": distribution(selected, "unit_type"),
        "candidate_source_type_counts": distribution(
            selected, "candidate_source_type"
        ),
        "source_officialness_rating_counts": distribution(
            selected, "source_officialness_rating"
        ),
        "source_review_batch_counts": distribution(
            selected, "source_review_pilot_id"
        ),
        "page_count_bin_counts": distribution(selected, "page_count_bin"),
        "text_layer_status_counts": distribution(
            selected, "text_layer_status"
        ),
        "recommended_next_action_counts": distribution(
            selected, "recommended_next_action"
        ),
        "state_counts": distribution(selected, "state"),
        "unique_states": len({row["state"] for row in selected}),
        "unique_municipalities": len(
            {(row["state"], row["municipality"]) for row in selected}
        ),
        "candidate_wage_page_hints": sum(
            int(row["candidate_wage_page_count"]) for row in selected
        ),
        "rows_without_candidate_wage_pages": sum(
            int(row["candidate_wage_page_count"]) == 0 for row in selected
        ),
        "manual_review_status": "not_started",
        "manual_fields_initialized_not_reviewed": len(selected),
        **support,
        "pdfs_opened": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "additional_text_extractions": 0,
        "ocr_runs": 0,
        "full_text_artifacts_written": 0,
        "final_wage_values_extracted": 0,
        "ingestion_actions": 0,
        "codify_actions": 0,
        "durable_ledger_mutations": 0,
        "caveats": [
            "The calibration subset has not been manually reviewed.",
            "Detection signals and candidate pages remain heuristic.",
            "No final wage values were extracted.",
            "No PDF, URL, OCR, ingestion, or codification action occurred.",
        ],
    }


def create_plan(args: argparse.Namespace) -> dict[str, object]:
    ledger_path = Path(args.text_table_ledger_csv)
    pdf_path = Path(args.pdf_readiness_ledger_csv)
    source_path = Path(args.source_review_ledger_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    fields, rows = read_csv(ledger_path)
    validate_detection_rows(fields, rows)
    selected, targets, reasons = select_rows(
        rows,
        sample_size=args.sample_size,
        include_unlikely=args.include_unlikely,
        calibration_round_id=args.calibration_id,
    )
    support = verify_supporting_ledgers(selected, pdf_path, source_path)
    packet_rows = [
        output_row(
            row,
            calibration_round_id=args.calibration_id,
            rank=index,
            reason=reasons[row["text_table_detection_id"]],
        )
        for index, row in enumerate(selected, start=1)
    ]
    for field in ("calibration_id", *INHERITED_FIELDS[:4]):
        require_unique(packet_rows, field)
    if any(
        part in field.lower()
        for field in OUTPUT_FIELDS
        for part in FORBIDDEN_OUTPUT_FIELD_PARTS
    ):
        raise ValueError("review packet includes prohibited text/value field")
    output_dir.mkdir(parents=True)
    review_path = output_dir / "calibration_review_input.csv"
    workbook_path = output_dir / "calibration_review_workbook.md"
    rubric_path = output_dir / "calibration_review_rubric.md"
    summary_path = output_dir / "calibration_sampling_summary.json"
    audit_path = output_dir / "calibration_subset_input_audit.md"
    manifest_path = output_dir / "calibration_subset_manifest.json"
    write_csv(review_path, packet_rows, OUTPUT_FIELDS)
    workbook_path.write_text(workbook_markdown(packet_rows), encoding="utf-8")
    rubric_path.write_text(rubric_markdown(), encoding="utf-8")
    summary = build_summary(
        selected,
        calibration_round_id=args.calibration_id,
        source_rows=rows,
        targets=targets,
        ledger_path=ledger_path,
        pdf_path=pdf_path,
        source_path=source_path,
        support=support,
    )
    write_json(summary_path, summary)
    audit_lines = [
        "# Calibration Subset Input Audit",
        "",
        f"- calibration ID: `{args.calibration_id}`",
        f"- durable detection rows: {len(rows)}",
        f"- selected rows: {len(packet_rows)}",
        f"- signal allocation: `{summary['wage_table_signal_counts']}`",
        f"- extraction priorities: "
        f"`{summary['extraction_pilot_priority_counts']}`",
        f"- units: `{summary['unit_type_counts']}`",
        f"- source types: `{summary['candidate_source_type_counts']}`",
        f"- officialness: "
        f"`{summary['source_officialness_rating_counts']}`",
        f"- source-review batches: `{summary['source_review_batch_counts']}`",
        f"- page bins: `{summary['page_count_bin_counts']}`",
        f"- unique states / municipalities: "
        f"{summary['unique_states']} / {summary['unique_municipalities']}",
        f"- candidate page hints: {summary['candidate_wage_page_hints']}",
        "- unique calibration/detection/readiness/source/candidate IDs: "
        f"{len(packet_rows)} each",
        "- manual status: `not_reviewed` for every row",
        "- PDFs / URLs opened: 0 / 0",
        "- additional text extraction / OCR / wage extraction: 0 / 0 / 0",
        "- durable ledger mutations: 0",
        "",
        "The packet is a review plan. No manual calibration judgment has "
        "been made.",
        "",
    ]
    audit_path.write_text("\n".join(audit_lines), encoding="utf-8")
    output_hashes = {
        path.name: sha256_file(path)
        for path in (
            audit_path,
            review_path,
            workbook_path,
            rubric_path,
            summary_path,
        )
    }
    manifest = {
        "schema_version": "1.0.0",
        "calibration_id": args.calibration_id,
        "created_at": summary["created_at"],
        "mode": "offline_calibration_plan_only",
        "sample_size": args.sample_size,
        "selected_rows": len(packet_rows),
        "stratify": bool(args.stratify),
        "include_unlikely": bool(args.include_unlikely),
        "signal_allocation": summary["wage_table_signal_counts"],
        "manual_review_status": "not_started",
        "inputs": [
            {
                "path": ledger_path.as_posix(),
                "sha256": sha256_file(ledger_path),
                "rows": len(rows),
            },
            {
                "path": pdf_path.as_posix(),
                "sha256": sha256_file(pdf_path),
            },
            {
                "path": source_path.as_posix(),
                "sha256": sha256_file(source_path),
            },
        ],
        "outputs": output_hashes,
        "pdfs_opened": 0,
        "urls_opened": 0,
        "network_calls": 0,
        "additional_text_extractions": 0,
        "ocr_runs": 0,
        "final_wage_values_extracted": 0,
        "manual_reviews_completed": 0,
        "durable_ledger_mutations": 0,
    }
    write_json(manifest_path, manifest)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text-table-ledger-csv", required=True)
    parser.add_argument("--pdf-readiness-ledger-csv", required=True)
    parser.add_argument("--source-review-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--calibration-id", required=True)
    parser.add_argument("--sample-size", type=int, default=150)
    parser.add_argument("--stratify", action="store_true", default=True)
    parser.add_argument("--include-unlikely", action="store_true", default=True)
    parser.add_argument("--plan-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = create_plan(args)
    print(
        "Text/table calibration packet prepared: "
        f"{summary['calibration_subset_rows']} rows; "
        f"{summary['calibration_id']}."
    )


if __name__ == "__main__":
    main()
