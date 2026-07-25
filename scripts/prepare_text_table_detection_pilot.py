#!/usr/bin/env python3
"""Prepare a deterministic offline text/table-detection pilot.

The planner reads durable CSV metadata only. It never opens a retained PDF,
URL, or network connection and never mutates a durable ledger.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PILOT_ID = "TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24"
DEFAULT_SAMPLE_SIZE = 150
DEFAULT_NUM_LANES = 3
FROZEN_HEURISTIC_VERSION = "bounded_keyword_numeric_structure_v1"

IDENTITY_FIELDS = [
    "text_table_detection_id",
    "pdf_readiness_id",
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
]

PLANNING_FIELDS = [
    "text_table_detection_pilot_id",
    "text_table_detection_lane_id",
    "pilot_selection_rank",
    "page_count_bin",
    "artifact_byte_size_bin",
    "sample_selection_reason",
]

INPUT_FIELDS = IDENTITY_FIELDS + PLANNING_FIELDS

REQUIRED_READINESS_FIELDS = {
    "pdf_readiness_id",
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
    "readiness_status",
    "recommended_next_action",
}

DIVERSITY_FIELDS = [
    "source_review_pilot_id",
    "priority_for_content_review",
    "unit_type",
    "state",
    "source_officialness_rating",
    "candidate_source_type",
    "document_type_rating",
    "page_count_bin",
    "text_layer_status",
]


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


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=INPUT_FIELDS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_token(*values: str, length: int = 24) -> str:
    material = "\x1f".join(values).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:length]


def page_count_bin(raw: str) -> str:
    pages = int(raw)
    if pages <= 10:
        return "1_to_10"
    if pages <= 25:
        return "11_to_25"
    if pages <= 50:
        return "26_to_50"
    if pages <= 100:
        return "51_to_100"
    return "over_100"


def artifact_size_bin(raw: str) -> str:
    size = int(raw)
    if size <= 512 * 1024:
        return "small_le_512_kib"
    if size <= 2 * 1024 * 1024:
        return "medium_512_kib_to_2_mib"
    if size <= 5 * 1024 * 1024:
        return "large_2_to_5_mib"
    return "very_large_gt_5_mib"


def distribution(
    rows: list[dict[str, str]], field: str
) -> dict[str, int]:
    return dict(
        sorted(Counter(row.get(field, "") for row in rows).items())
    )


def validate_authority(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    *,
    include_partial: bool,
    exclude_ocr_later: bool,
) -> list[dict[str, str]]:
    missing = sorted(REQUIRED_READINESS_FIELDS - set(fieldnames))
    if missing:
        raise ValueError(f"PDF-readiness ledger missing fields: {missing}")
    if not rows:
        raise ValueError("PDF-readiness ledger is empty")

    eligible: list[dict[str, str]] = []
    for row in rows:
        if row.get("readiness_status") != "readiness_checked":
            continue
        action = row.get("recommended_next_action", "")
        if action != "parse_text_layer_later":
            if exclude_ocr_later or action != "ocr_later":
                continue
            raise ValueError("OCR-later row cannot enter parse-text pilot")
        allowed_text = {"present", "partial"} if include_partial else {"present"}
        if row.get("text_layer_status") not in allowed_text:
            continue
        if (
            row.get("content_type_observed") != "application/pdf"
            or not row.get("content_artifact_path")
            or not row.get("content_hash")
        ):
            raise ValueError("parse-text candidate lacks retained PDF metadata")
        try:
            size = int(row.get("content_byte_size", ""))
            pages = int(row.get("pdf_page_count", ""))
        except ValueError as exc:
            raise ValueError(
                "parse-text candidate has invalid size or page count"
            ) from exc
        if size <= 0 or pages <= 0:
            raise ValueError(
                "parse-text candidate has nonpositive size or page count"
            )
        prepared = dict(row)
        prepared["page_count_bin"] = page_count_bin(str(pages))
        prepared["artifact_byte_size_bin"] = artifact_size_bin(str(size))
        eligible.append(prepared)

    if not eligible:
        raise ValueError("no parse-text-layer candidates are eligible")
    for field in (
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        values = [row[field] for row in eligible]
        if any(not value for value in values):
            raise ValueError(f"blank eligible identity: {field}")
        if len(values) != len(set(values)):
            raise ValueError(f"eligible rows contain duplicate {field}")
    return eligible


def validate_supporting_ledger(
    path: Path,
    *,
    identity_field: str,
    selected_values: set[str],
) -> dict[str, object]:
    fieldnames, rows = read_csv(path)
    if identity_field not in fieldnames:
        raise ValueError(
            f"supporting ledger {path} lacks {identity_field}"
        )
    values = {row.get(identity_field, "") for row in rows}
    missing = selected_values - values
    if missing:
        raise ValueError(
            f"supporting ledger {path} misses selected identities: "
            f"{sorted(missing)[:5]}"
        )
    return {
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "rows": len(rows),
        "identity_field": identity_field,
        "selected_identity_coverage": len(selected_values),
    }


def select_diverse(
    eligible: list[dict[str, str]],
    sample_size: int,
    *,
    pilot_id: str,
    state_diversity: bool,
) -> list[dict[str, str]]:
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    if sample_size > len(eligible):
        raise ValueError(
            f"requested {sample_size} rows but only {len(eligible)} qualify"
        )
    dimensions = [
        field
        for field in DIVERSITY_FIELDS
        if state_diversity or field != "state"
    ]
    stable_order = {
        row["pdf_readiness_id"]: stable_token(
            pilot_id,
            row["pdf_readiness_id"],
            row["source_review_id"],
            length=64,
        )
        for row in eligible
    }
    availability = {
        field: Counter(row.get(field, "") for row in eligible)
        for field in dimensions
    }
    counts = {field: Counter() for field in dimensions}
    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()

    # Cover each observed category at least once where sample capacity allows.
    for field in dimensions:
        values = sorted(
            availability[field],
            key=lambda value: (availability[field][value], value),
        )
        for value in values:
            if len(selected) >= sample_size:
                break
            candidates = [
                row
                for row in eligible
                if row["pdf_readiness_id"] not in selected_ids
                and row.get(field, "") == value
            ]
            if not candidates:
                continue
            chosen = min(
                candidates,
                key=lambda row: (
                    sum(
                        counts[dimension][row.get(dimension, "")]
                        for dimension in dimensions
                    ),
                    stable_order[row["pdf_readiness_id"]],
                ),
            )
            selected.append(chosen)
            selected_ids.add(chosen["pdf_readiness_id"])
            for dimension in dimensions:
                counts[dimension][chosen.get(dimension, "")] += 1

    while len(selected) < sample_size:
        candidates = [
            row
            for row in eligible
            if row["pdf_readiness_id"] not in selected_ids
        ]

        def candidate_key(row: dict[str, str]) -> tuple[float, str]:
            score = 0.0
            for field in dimensions:
                value = row.get(field, "")
                score += 1.0 / (counts[field][value] + 1)
                score += 0.25 / max(availability[field][value], 1)
            return (-score, stable_order[row["pdf_readiness_id"]])

        chosen = min(candidates, key=candidate_key)
        selected.append(chosen)
        selected_ids.add(chosen["pdf_readiness_id"])
        for dimension in dimensions:
            counts[dimension][chosen.get(dimension, "")] += 1
    return selected


def balance_lanes(
    selected: list[dict[str, str]], num_lanes: int
) -> list[list[dict[str, str]]]:
    if num_lanes <= 0:
        raise ValueError("lane count must be positive")
    if num_lanes > len(selected):
        raise ValueError("lane count exceeds selected rows")
    ordered = sorted(
        selected,
        key=lambda row: (
            row["source_review_pilot_id"],
            row["priority_for_content_review"],
            row["unit_type"],
            row["page_count_bin"],
            row["state"],
            row["text_layer_status"],
            row["pdf_readiness_id"],
        ),
    )
    lanes: list[list[dict[str, str]]] = [[] for _ in range(num_lanes)]
    for index, row in enumerate(ordered):
        lanes[index % num_lanes].append(row)
    return lanes


def markdown_distribution(
    rows: list[dict[str, str]], fields: list[str]
) -> str:
    sections: list[str] = []
    for field in fields:
        sections.extend([f"### `{field}`", ""])
        for value, count in distribution(rows, field).items():
            sections.append(f"- `{value or '(blank)'}`: {count}")
        sections.append("")
    return "\n".join(sections).rstrip()


def create_plan(args: argparse.Namespace) -> dict[str, object]:
    readiness_path = Path(args.pdf_readiness_ledger_csv)
    source_path = Path(args.source_review_ledger_csv)
    triage_path = Path(args.triage_ledger_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if args.sample_size <= 0 or args.num_lanes <= 0:
        raise ValueError("sample size and lane count must be positive")
    if not args.exclude_ocr_later:
        raise ValueError("--exclude-ocr-later is mandatory for this pilot")
    if not args.balance_lanes:
        raise ValueError("--balance-lanes is mandatory")
    if args.freeze_heuristic_version != FROZEN_HEURISTIC_VERSION:
        raise ValueError(
            "unsupported heuristic version; expected "
            f"{FROZEN_HEURISTIC_VERSION}"
        )

    fieldnames, all_rows = read_csv(readiness_path)
    eligible = validate_authority(
        fieldnames,
        all_rows,
        include_partial=args.include_partial_text_layer,
        exclude_ocr_later=args.exclude_ocr_later,
    )
    if args.all_parse_text:
        selected = list(eligible)
        effective_size = len(selected)
    else:
        selected = select_diverse(
            eligible,
            args.sample_size,
            pilot_id=args.pilot_id,
            state_diversity=args.state_diversity,
        )
        effective_size = args.sample_size
    selected_review_ids = {row["source_review_id"] for row in selected}
    selected_triage_ids = {row["triage_id"] for row in selected}
    supporting_sources = [
        validate_supporting_ledger(
            source_path,
            identity_field="source_review_id",
            selected_values=selected_review_ids,
        ),
        validate_supporting_ledger(
            triage_path,
            identity_field="triage_id",
            selected_values=selected_triage_ids,
        ),
    ]

    lanes = balance_lanes(selected, args.num_lanes)
    expected_sizes = [
        effective_size // args.num_lanes
        + (1 if index < effective_size % args.num_lanes else 0)
        for index in range(args.num_lanes)
    ]
    if [len(lane) for lane in lanes] != expected_sizes:
        raise AssertionError("lane balancing failed")

    output_dir.mkdir(parents=True)
    manifest_lanes: list[dict[str, object]] = []
    flattened: list[dict[str, str]] = []
    rank = 0
    for lane_number, lane in enumerate(lanes, start=1):
        prepared: list[dict[str, str]] = []
        for source in lane:
            rank += 1
            row = {
                field: source.get(field, "") for field in IDENTITY_FIELDS
            }
            row["text_table_detection_id"] = (
                "ttd_"
                + stable_token(
                    args.pilot_id,
                    source["pdf_readiness_id"],
                    source["content_hash"],
                )
            )
            row.update(
                {
                    "text_table_detection_pilot_id": args.pilot_id,
                    "text_table_detection_lane_id": f"lane_{lane_number}",
                    "pilot_selection_rank": str(rank),
                    "page_count_bin": source["page_count_bin"],
                    "artifact_byte_size_bin": source[
                        "artifact_byte_size_bin"
                    ],
                    "sample_selection_reason": (
                        (
                            "complete durable parse_text_layer_later "
                            "universe under frozen heuristic"
                        )
                        if args.all_parse_text
                        else (
                            "deterministic diversity sample from durable "
                            "parse_text_layer_later retained PDFs"
                        )
                    ),
                }
            )
            prepared.append(row)
            flattened.append(row)

        lane_path = (
            output_dir
            / f"lane_{lane_number}_text_table_detection_input.csv"
        )
        write_csv(lane_path, prepared)
        lane_hash = sha256_file(lane_path)
        audit_path = output_dir / f"lane_{lane_number}_input_audit.md"
        audit_path.write_text(
            "\n".join(
                [
                    f"# Text/Table Detection Lane {lane_number} Input Audit",
                    "",
                    f"- pilot: `{args.pilot_id}`",
                    f"- rows: {len(prepared)}",
                    f"- input SHA-256: `{lane_hash}`",
                    "- all rows parse-text-layer candidates: yes",
                    "- OCR-later rows: 0",
                    "- duplicate detection/readiness/source-review/"
                    "candidate IDs: 0 / 0 / 0 / 0",
                    "- nonblank artifact paths/hashes: "
                    f"{len(prepared)} / {len(prepared)}",
                    "- URLs opened: 0",
                    "- PDFs opened during planning: 0",
                    "",
                    markdown_distribution(prepared, DIVERSITY_FIELDS),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_lanes.append(
            {
                "lane_id": f"lane_{lane_number}",
                "expected_rows": len(prepared),
                "frozen_heuristic_version": (
                    args.freeze_heuristic_version
                ),
                "input_csv": lane_path.as_posix(),
                "input_sha256": lane_hash,
                "input_audit": audit_path.as_posix(),
                "dry_run_output_dir": (
                    ROOT
                    / "tmp"
                    / "text_table_detection_pilots"
                    / args.pilot_id
                    / f"lane_{lane_number}_dry_run"
                ).as_posix(),
                "future_local_output_dir": (
                    ROOT
                    / "tmp"
                    / "text_table_detection_pilots"
                    / args.pilot_id
                    / f"lane_{lane_number}_local_attempt1"
                ).as_posix(),
            }
        )

    for field in (
        "text_table_detection_id",
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        values = [row[field] for row in flattened]
        if len(values) != len(set(values)):
            raise ValueError(f"planner produced duplicate {field}")
    if any(
        row["text_layer_status"] not in {"present", "partial"}
        for row in flattened
    ):
        raise ValueError("planner selected unsupported text-layer status")

    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "pilot_id": args.pilot_id,
        "created_at": now_utc(),
        "mode": "local_text_table_detection_plan_only",
        "pdf_readiness_ledger_csv": readiness_path.as_posix(),
        "pdf_readiness_ledger_sha256": sha256_file(readiness_path),
        "pdf_readiness_ledger_rows": len(all_rows),
        "parse_text_layer_candidate_rows": len(eligible),
        "ocr_later_rows_excluded": sum(
            row.get("recommended_next_action") == "ocr_later"
            for row in all_rows
        ),
        "supporting_ledger_sources": supporting_sources,
        "selected_rows": len(flattened),
        "num_lanes": len(lanes),
        "lane_rows": [len(lane) for lane in lanes],
        "selection": {
            "sample_size": effective_size,
            "all_parse_text": args.all_parse_text,
            "balance_lanes": args.balance_lanes,
            "state_diversity": args.state_diversity,
            "include_partial_text_layer": (
                args.include_partial_text_layer
            ),
            "exclude_ocr_later": args.exclude_ocr_later,
            "network_access": False,
            "pdfs_opened_during_planning": 0,
            "ocr": False,
            "full_text_saved": False,
            "final_wage_extraction": False,
        },
        "frozen_heuristic_version": args.freeze_heuristic_version,
        "selected_distributions": {
            field: distribution(flattened, field)
            for field in DIVERSITY_FIELDS
        },
        "selected_artifact_bytes": sum(
            int(row["content_byte_size"]) for row in flattened
        ),
        "selected_pages": sum(
            int(row["pdf_page_count"]) for row in flattened
        ),
        "lanes": manifest_lanes,
    }
    write_json(
        output_dir / "text_table_detection_pilot_manifest.json",
        manifest,
    )

    (output_dir / "text_table_detection_input_audit.md").write_text(
        "\n".join(
            [
                "# Text/Table Detection Pilot Input Audit",
                "",
                "## Result",
                "",
                "**PASS.** The offline planner selected exactly "
                f"{len(flattened)} unique parse-text-layer candidates from "
                f"{len(eligible)} eligible durable readiness rows.",
                "",
                f"- durable readiness rows: {len(all_rows)}",
                f"- parse-text candidates: {len(eligible)}",
                "- OCR-later candidates excluded: "
                f"{manifest['ocr_later_rows_excluded']}",
                f"- selected rows: {len(flattened)}",
                "- lane rows: "
                f"{' / '.join(map(str, manifest['lane_rows']))}",
                f"- represented pages: {manifest['selected_pages']}",
                "- duplicate detection/readiness/source-review/"
                "candidate IDs: 0 / 0 / 0 / 0",
                "- URLs opened: 0",
                "- PDFs opened during planning: 0",
                "",
                "## Selected distributions",
                "",
                markdown_distribution(flattened, DIVERSITY_FIELDS),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "text_table_detection_operating_handoff.md").write_text(
        "\n".join(
            [
                "# Text/Table Detection Operating Handoff",
                "",
                f"Pilot: `{args.pilot_id}`",
                "",
                f"Run all {len(lanes)} dry-run lanes before opening a "
                "retained PDF. "
                "The local runner may open only the paths locked in these "
                "inputs, must verify hash and size first, scan at most 10 "
                "deterministic pages and 1,500 characters per page, save no "
                "page or document text, run no OCR, and extract no final "
                "wage values.",
                "",
                "Candidate wage pages and confidence categories are "
                "heuristic planning signals only.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "text_table_detection_merge_prompt_stub.md").write_text(
        "\n".join(
            [
                "# Future Text/Table Detection Merge Prompt Stub",
                "",
                "Audit every locked local lane. A future serial merge may "
                "be planned only if coverage, identity, hash, terminal "
                "status, bounded-snippet, no-network, no-OCR, no-full-text, "
                "and no-final-wage gates pass. This stub does not authorize "
                "a merge, extraction, ingestion, codification, or analysis.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-readiness-ledger-csv", required=True)
    parser.add_argument("--source-review-ledger-csv", required=True)
    parser.add_argument("--triage-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument(
        "--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE
    )
    parser.add_argument(
        "--all-parse-text",
        action="store_true",
        help="Select the complete eligible parse_text_layer_later universe.",
    )
    parser.add_argument("--num-lanes", type=int, default=DEFAULT_NUM_LANES)
    parser.add_argument(
        "--balance-lanes",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--state-diversity",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--include-partial-text-layer",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--exclude-ocr-later",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--freeze-heuristic-version",
        default=FROZEN_HEURISTIC_VERSION,
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.plan_only:
        raise SystemExit("planner is offline plan-only; pass --plan-only")
    manifest = create_plan(args)
    print(
        "Text/table detection plan prepared: "
        f"{manifest['selected_rows']} rows across "
        f"{manifest['num_lanes']} lanes; URLs=0 PDFs opened=0."
    )


if __name__ == "__main__":
    main()
