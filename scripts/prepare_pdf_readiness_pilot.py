#!/usr/bin/env python3
"""Prepare a deterministic, offline PDF-readiness pilot.

The planner reads only a durable source-review CSV and local path metadata.
It never opens a URL, parses a PDF, writes extracted text, or mutates any
durable source-review, routing, triage, candidate, ingestion, or corpus layer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PILOT_ID = "PDF-READINESS-PILOT1-150-2026-07-24"
DEFAULT_SAMPLE_SIZE = 150
DEFAULT_NUM_LANES = 3
TERMINAL_READINESS_STATUSES = {
    "readiness_checked",
    "artifact_missing",
    "hash_mismatch",
    "artifact_problem",
    "parser_error",
}

IDENTITY_FIELDS = [
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
]

PLANNING_FIELDS = [
    "pdf_readiness_pilot_id",
    "pdf_readiness_lane_id",
    "pilot_selection_rank",
    "artifact_byte_size_bin",
    "sample_selection_reason",
]

INPUT_FIELDS = IDENTITY_FIELDS + PLANNING_FIELDS

REQUIRED_SOURCE_FIELDS = {
    "source_review_id",
    "candidate_queue_row_id",
    "triage_id",
    "verification_id",
    "source_review_pilot_id",
    "state",
    "municipality",
    "government_name",
    "unit_type_scouted",
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
    "source_review_status",
}

DIVERSITY_FIELDS = [
    "source_review_pilot_id",
    "priority_for_content_review",
    "unit_type",
    "state",
    "source_officialness_rating",
    "artifact_byte_size_bin",
    "candidate_source_type",
    "document_type_rating",
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


def artifact_size_bin(raw: str) -> str:
    size = int(raw)
    if size <= 512 * 1024:
        return "small_le_512_kib"
    if size <= 2 * 1024 * 1024:
        return "medium_512_kib_to_2_mib"
    if size <= 5 * 1024 * 1024:
        return "large_2_to_5_mib"
    return "very_large_gt_5_mib"


def distribution(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") for row in rows).items()))


def resolve_artifact(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def validate_source_rows(
    fieldnames: list[str], rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    missing = sorted(REQUIRED_SOURCE_FIELDS - set(fieldnames))
    if missing:
        raise ValueError(f"source-review ledger missing fields: {missing}")
    if not rows:
        raise ValueError("source-review ledger is empty")
    eligible: list[dict[str, str]] = []
    for row in rows:
        if (
            row.get("source_review_status")
            != "reviewed_metadata_and_artifact_saved"
            or row.get("content_type_observed") != "application/pdf"
            or not row.get("content_artifact_path")
            or not row.get("content_hash")
        ):
            continue
        try:
            size = int(row.get("content_byte_size", ""))
        except ValueError:
            continue
        if size <= 0:
            continue
        artifact = resolve_artifact(row["content_artifact_path"])
        if not artifact.is_file():
            continue
        prepared = dict(row)
        prepared["unit_type"] = row.get("unit_type_scouted", "") or "unknown"
        prepared["artifact_byte_size_bin"] = artifact_size_bin(str(size))
        eligible.append(prepared)
    if not eligible:
        raise ValueError("no retained local PDF artifacts are eligible")
    for field in ("source_review_id", "candidate_queue_row_id"):
        values = [row[field] for row in eligible]
        if len(values) != len(set(values)):
            raise ValueError(f"eligible rows contain duplicate {field}")
    return eligible


def read_excluded_readiness_rows(
    raw_paths: list[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    required = {
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
        "readiness_status",
    }
    rows: list[dict[str, str]] = []
    sources: list[dict[str, str]] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        fieldnames, lane_rows = read_csv(path)
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(
                f"readiness exclusion ledger {path} missing fields: {missing}"
            )
        if not lane_rows:
            raise ValueError(f"readiness exclusion ledger is empty: {path}")
        for row in lane_rows:
            if any(not row.get(field) for field in required):
                raise ValueError(
                    f"readiness exclusion ledger has blank required field: {path}"
                )
            if row["readiness_status"] not in TERMINAL_READINESS_STATUSES:
                raise ValueError(
                    "readiness exclusion row is not terminal: "
                    f"{row['pdf_readiness_id']}"
                )
        rows.extend(lane_rows)
        sources.append(
            {
                "path": path.as_posix(),
                "sha256": sha256_file(path),
                "rows": len(lane_rows),
            }
        )
    for field in (
        "pdf_readiness_id",
        "source_review_id",
        "candidate_queue_row_id",
    ):
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(
                f"readiness exclusion ledgers contain duplicate {field}"
            )
    return rows, sources


def select_diverse(
    eligible: list[dict[str, str]],
    sample_size: int,
    *,
    pilot_id: str,
    state_diversity: bool,
    include_prior_batches: bool,
) -> list[dict[str, str]]:
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    if sample_size > len(eligible):
        raise ValueError(
            f"requested {sample_size} rows but only {len(eligible)} qualify"
        )
    rows = list(eligible)
    if not include_prior_batches:
        latest = max(row["source_review_merged_at"] for row in rows)
        rows = [row for row in rows if row["source_review_merged_at"] == latest]
        if len(rows) < sample_size:
            raise ValueError("latest batch does not contain requested sample")

    dimensions = [
        field
        for field in DIVERSITY_FIELDS
        if state_diversity or field != "state"
    ]
    stable_order = {
        row["source_review_id"]: stable_token(
            pilot_id,
            row["source_review_id"],
            row["candidate_queue_row_id"],
            length=64,
        )
        for row in rows
    }
    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    counts: dict[str, Counter[str]] = {
        field: Counter() for field in dimensions
    }
    availability: dict[str, Counter[str]] = {
        field: Counter(row.get(field, "") for row in rows)
        for field in dimensions
    }

    # Cover every observed value in the central categorical dimensions first.
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
                for row in rows
                if row["source_review_id"] not in selected_ids
                and row.get(field, "") == value
            ]
            if not candidates:
                continue
            chosen = min(
                candidates,
                key=lambda row: (
                    sum(counts[d][row.get(d, "")] for d in dimensions),
                    stable_order[row["source_review_id"]],
                ),
            )
            selected.append(chosen)
            selected_ids.add(chosen["source_review_id"])
            for dimension in dimensions:
                counts[dimension][chosen.get(dimension, "")] += 1

    # Fill by maximizing rarity/underrepresentation across all dimensions.
    while len(selected) < sample_size:
        candidates = [
            row
            for row in rows
            if row["source_review_id"] not in selected_ids
        ]

        def candidate_key(row: dict[str, str]) -> tuple[float, str]:
            score = 0.0
            for field in dimensions:
                value = row.get(field, "")
                available = availability[field][value]
                used = counts[field][value]
                score += 1.0 / (used + 1)
                score += 0.25 / max(available, 1)
            return (-score, stable_order[row["source_review_id"]])

        chosen = min(candidates, key=candidate_key)
        selected.append(chosen)
        selected_ids.add(chosen["source_review_id"])
        for dimension in dimensions:
            counts[dimension][chosen.get(dimension, "")] += 1
    return selected


def balance_lanes(
    selected: list[dict[str, str]], num_lanes: int
) -> list[list[dict[str, str]]]:
    if num_lanes <= 0:
        raise ValueError("number of lanes must be positive")
    if num_lanes > len(selected):
        raise ValueError("number of lanes exceeds selected rows")
    lanes: list[list[dict[str, str]]] = [[] for _ in range(num_lanes)]
    ordered = sorted(
        selected,
        key=lambda row: (
            row["source_review_pilot_id"],
            row["priority_for_content_review"],
            row["unit_type"],
            row["state"],
            row["source_officialness_rating"],
            row["artifact_byte_size_bin"],
            row["source_review_id"],
        ),
    )
    for index, row in enumerate(ordered):
        lanes[index % num_lanes].append(row)
    return lanes


def markdown_distribution(
    rows: list[dict[str, str]], fields: list[str]
) -> str:
    sections: list[str] = []
    for field in fields:
        sections.append(f"### `{field}`")
        sections.append("")
        for value, count in distribution(rows, field).items():
            sections.append(f"- `{value or '(blank)'}`: {count}")
        sections.append("")
    return "\n".join(sections).rstrip()


def create_plan(args: argparse.Namespace) -> dict[str, object]:
    ledger_path = Path(args.source_review_ledger_csv)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    if args.num_lanes <= 0:
        raise ValueError("lane count must be positive")
    if not args.all_remaining and args.sample_size <= 0:
        raise ValueError("sample size must be positive")
    if args.all_remaining and not args.include_prior_batches:
        raise ValueError(
            "--all-remaining requires --include-prior-batches"
        )
    fieldnames, rows = read_csv(ledger_path)
    eligible = validate_source_rows(fieldnames, rows)
    excluded_rows, exclusion_sources = read_excluded_readiness_rows(
        list(args.exclude_readiness_ledger_csv or [])
    )
    eligible_by_review_id = {
        row["source_review_id"]: row for row in eligible
    }
    excluded_review_ids = {
        row["source_review_id"] for row in excluded_rows
    }
    unknown_exclusions = sorted(
        excluded_review_ids - set(eligible_by_review_id)
    )
    if unknown_exclusions:
        raise ValueError(
            "readiness exclusions are not retained-PDF source-review rows: "
            f"{unknown_exclusions[:5]}"
        )
    excluded_candidate_ids = {
        row["candidate_queue_row_id"] for row in excluded_rows
    }
    for row in excluded_rows:
        source = eligible_by_review_id[row["source_review_id"]]
        if source["candidate_queue_row_id"] != row["candidate_queue_row_id"]:
            raise ValueError(
                "readiness exclusion candidate identity disagrees with "
                f"source-review ledger: {row['source_review_id']}"
            )
    remaining = [
        row
        for row in eligible
        if row["source_review_id"] not in excluded_review_ids
    ]
    if not remaining:
        raise ValueError("no retained PDF artifacts remain after exclusions")
    if any(
        row["candidate_queue_row_id"] in excluded_candidate_ids
        for row in remaining
    ):
        raise ValueError("excluded candidate identity remains selectable")
    target_size = len(remaining) if args.all_remaining else args.sample_size
    if args.all_remaining:
        selected = sorted(
            remaining,
            key=lambda row: (
                row["source_review_pilot_id"],
                row["priority_for_content_review"],
                row["state"],
                row["unit_type"],
                row["source_review_id"],
            ),
        )
    else:
        selected = select_diverse(
            remaining,
            target_size,
            pilot_id=args.pilot_id,
            state_diversity=args.state_diversity,
            include_prior_batches=args.include_prior_batches,
        )
    if len(selected) != target_size:
        raise AssertionError("planner did not produce exact requested sample")

    output_dir.mkdir(parents=True)
    lanes = balance_lanes(selected, args.num_lanes)
    expected_sizes = [
        target_size // args.num_lanes
        + (1 if index < target_size % args.num_lanes else 0)
        for index in range(args.num_lanes)
    ]
    if [len(lane) for lane in lanes] != expected_sizes:
        raise AssertionError("lane balancing failed")

    manifest_lanes: list[dict[str, object]] = []
    flattened: list[dict[str, str]] = []
    rank = 0
    for lane_index, lane_rows in enumerate(lanes, start=1):
        prepared_rows: list[dict[str, str]] = []
        for source in lane_rows:
            rank += 1
            row = {field: source.get(field, "") for field in IDENTITY_FIELDS}
            row["pdf_readiness_id"] = (
                "pr_"
                + stable_token(
                    args.pilot_id,
                    source["source_review_id"],
                    source["content_hash"],
                )
            )
            row.update(
                {
                    "pdf_readiness_pilot_id": args.pilot_id,
                    "pdf_readiness_lane_id": f"lane_{lane_index}",
                    "pilot_selection_rank": str(rank),
                    "artifact_byte_size_bin": source[
                        "artifact_byte_size_bin"
                    ],
                    "sample_selection_reason": (
                        "complete retained-PDF remainder after readiness "
                        "identity exclusion"
                        if args.all_remaining
                        else "deterministic diversity sample from retained "
                        "hash-addressed PDF artifacts"
                    ),
                }
            )
            prepared_rows.append(row)
            flattened.append(row)
        lane_path = (
            output_dir
            / f"lane_{lane_index}_pdf_readiness_input.csv"
        )
        write_csv(lane_path, prepared_rows)
        input_sha = sha256_file(lane_path)
        audit_path = output_dir / f"lane_{lane_index}_input_audit.md"
        audit_path.write_text(
            "\n".join(
                [
                    f"# PDF-Readiness Lane {lane_index} Input Audit",
                    "",
                    f"- pilot: `{args.pilot_id}`",
                    f"- rows: {len(prepared_rows)}",
                    f"- input SHA-256: `{input_sha}`",
                    "- duplicate readiness IDs: 0",
                    "- duplicate source-review IDs: 0",
                    "- nonblank artifact paths: "
                    f"{sum(bool(r['content_artifact_path']) for r in prepared_rows)}",
                    "- nonblank content hashes: "
                    f"{sum(bool(r['content_hash']) for r in prepared_rows)}",
                    "- URLs opened: 0",
                    "",
                    markdown_distribution(
                        prepared_rows,
                        [
                            "source_review_pilot_id",
                            "priority_for_content_review",
                            "unit_type",
                            "state",
                            "source_officialness_rating",
                            "artifact_byte_size_bin",
                        ],
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_lanes.append(
            {
                "lane_id": f"lane_{lane_index}",
                "expected_rows": len(prepared_rows),
                "input_csv": lane_path.as_posix(),
                "input_sha256": input_sha,
                "input_audit": audit_path.as_posix(),
                "dry_run_output_dir": (
                    ROOT
                    / "tmp"
                    / "pdf_readiness_pilots"
                    / args.pilot_id
                    / f"lane_{lane_index}_dry_run"
                ).as_posix(),
                "future_local_output_dir": (
                    ROOT
                    / "tmp"
                    / "pdf_readiness_pilots"
                    / args.pilot_id
                    / f"lane_{lane_index}_local_attempt1"
                ).as_posix(),
            }
        )

    readiness_ids = [row["pdf_readiness_id"] for row in flattened]
    review_ids = [row["source_review_id"] for row in flattened]
    candidate_ids = [row["candidate_queue_row_id"] for row in flattened]
    if len(readiness_ids) != len(set(readiness_ids)):
        raise ValueError("planner produced duplicate pdf_readiness_id")
    if len(review_ids) != len(set(review_ids)):
        raise ValueError("planner produced duplicate source_review_id")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("planner produced duplicate candidate_queue_row_id")

    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "pilot_id": args.pilot_id,
        "created_at": now_utc(),
        "mode": "local_pdf_readiness_plan_only",
        "source_review_ledger_csv": ledger_path.as_posix(),
        "source_review_ledger_sha256": sha256_file(ledger_path),
        "source_review_ledger_rows": len(rows),
        "eligible_retained_pdf_rows": len(eligible),
        "excluded_readiness_rows": len(excluded_rows),
        "excluded_readiness_ledger_sources": exclusion_sources,
        "eligible_remaining_pdf_rows": len(remaining),
        "selected_rows": len(flattened),
        "num_lanes": len(lanes),
        "lane_rows": [len(lane) for lane in lanes],
        "selection": {
            "sample_size": target_size,
            "all_remaining": bool(args.all_remaining),
            "balance_lanes": bool(args.balance_lanes),
            "state_diversity": args.state_diversity,
            "include_prior_batches": args.include_prior_batches,
            "retained_pdf_only": True,
            "network_access": False,
            "ocr": False,
            "full_text_saved": False,
            "wage_extraction": False,
        },
        "selected_distributions": {
            field: distribution(flattened, field)
            for field in DIVERSITY_FIELDS
        },
        "selected_artifact_bytes": sum(
            int(row["content_byte_size"]) for row in flattened
        ),
        "lanes": manifest_lanes,
    }
    manifest_path = output_dir / "pdf_readiness_pilot_manifest.json"
    write_json(manifest_path, manifest)

    input_audit = output_dir / "pdf_readiness_input_audit.md"
    input_audit.write_text(
        "\n".join(
            [
                "# PDF-Readiness Pilot Input Audit",
                "",
                "## Result",
                "",
                "**PASS.** The offline planner selected exactly "
                f"{len(flattened)} unique retained PDFs from "
                f"{len(eligible)} eligible artifacts.",
                "",
                f"- source ledger rows: {len(rows)}",
                f"- eligible retained PDFs: {len(eligible)}",
                f"- terminal readiness rows excluded: {len(excluded_rows)}",
                f"- retained PDFs remaining after exclusion: {len(remaining)}",
                f"- selected rows: {len(flattened)}",
                f"- lane rows: {' / '.join(map(str, manifest['lane_rows']))}",
                f"- selected artifact bytes: {manifest['selected_artifact_bytes']}",
                "- duplicate readiness/source-review/candidate IDs: 0 / 0 / 0",
                "- nonblank paths/hashes: "
                f"{len(flattened)} / {len(flattened)}",
                "- URLs opened: 0",
                "- PDFs opened or parsed during planning: 0",
                "",
                "## Selected distributions",
                "",
                markdown_distribution(flattened, DIVERSITY_FIELDS),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "pdf_readiness_operating_handoff.md").write_text(
        "\n".join(
            [
                "# PDF-Readiness Operating Handoff",
                "",
                f"Pilot: `{args.pilot_id}`",
                "",
                "Run dry-run validation for every lane before local parsing.",
                "The live-local runner may open only the retained paths in "
                "the locked lane CSVs. It must verify hashes before parsing, "
                "sample at most three pages, retain only counts/statuses, "
                "save no extracted text, and run no OCR.",
                "",
                "This layer records technical parseability only. It must not "
                "be promoted to content relevance, wage evidence, ingestion, "
                "codification, or analysis-ready observations.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "pdf_readiness_merge_prompt_stub.md").write_text(
        "\n".join(
            [
                "# Future PDF-Readiness Merge Prompt Stub",
                "",
                f"Audit all {len(lanes)} locked local readiness lanes. "
                "Merge exactly once only if every lane is completed and "
                "identity, hash, "
                "coverage, terminal-status, no-network, no-OCR, and no-text-"
                "artifact gates pass. Preserve all technical results and stop "
                "before ingestion, codify, wage extraction, wage-gap analysis, "
                "or any empirical claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-review-ledger-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument(
        "--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE
    )
    parser.add_argument(
        "--all-remaining",
        action="store_true",
        help="Select every eligible retained PDF left after readiness exclusions.",
    )
    parser.add_argument("--num-lanes", type=int, default=DEFAULT_NUM_LANES)
    parser.add_argument(
        "--balance-lanes",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--exclude-readiness-ledger-csv",
        action="append",
        default=[],
        help="Terminal readiness ledger whose source-review IDs are excluded; repeatable.",
    )
    parser.add_argument(
        "--state-diversity",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--include-prior-batches",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.plan_only:
        raise SystemExit("planner is offline plan-only; pass --plan-only")
    manifest = create_plan(args)
    print(
        "PDF-readiness plan prepared: "
        f"{manifest['selected_rows']} rows across "
        f"{manifest['num_lanes']} lanes; URLs opened=0."
    )


if __name__ == "__main__":
    main()
