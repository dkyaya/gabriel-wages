#!/usr/bin/env python3
"""Prepare a deterministic, offline source-review pilot.

The planner reads only committed metadata-triage and candidate-queue rows. It
does not open URLs, download content, parse documents, run OCR, rate sources,
or alter any upstream accounting or evidence layer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRIAGE_LEDGER = (
    ROOT
    / "docs"
    / "analysis"
    / "content_triage_ledgers"
    / "content_triage_metadata_ledger_cumulative.csv"
)
DEFAULT_QUEUE = (
    ROOT / "docs" / "analysis" / "national_scout_candidate_queue_2026-07-20.csv"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "docs"
    / "analysis"
    / "source_review_pilots"
    / "SOURCE-REVIEW-PILOT1-150-2026-07-24"
)
DEFAULT_PILOT_ID = "SOURCE-REVIEW-PILOT1-150-2026-07-24"

BLOCKED_ROUTING_STATUSES = {
    "blocked_or_forbidden",
    "not_found",
    "error",
    "ssl_error",
    "timeout",
    "connection_error",
}
DUPLICATE_TRIAGE_STATUSES = {"duplicate_defer_to_canonical"}
OVERSIZED_TRIAGE_STATUSES = {"oversized_needs_separate_pass"}
LOWER_DISPOSITIONS = {
    "context_hold",
    "insufficient_hold",
    "duplicate_hold",
    "already_canonical",
    "calibration_rejected",
    "other_hold",
}
REQUIRED_TRIAGE_FIELDS = {
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
}
IDENTITY_FIELDS = [
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
]
PLANNING_FIELDS = [
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
    "source_review_stage",
    "pilot_selection_reason",
]
SOURCE_REVIEW_FIELDS = [
    "source_review_status",
    "source_review_status_detail",
    "url_access_status",
    "download_status",
    "content_artifact_path",
    "content_hash",
    "content_byte_size",
    "content_type_observed",
    "text_layer_status",
    "pdf_page_count",
    "source_officialness_rating",
    "source_relevance_rating",
    "municipality_match_rating",
    "employer_match_rating",
    "bargaining_unit_match_rating",
    "safety_unit_match_signal",
    "non_safety_unit_match_signal",
    "document_type_rating",
    "contract_or_document_period_start",
    "contract_or_document_period_end",
    "wage_table_signal",
    "wage_growth_signal",
    "mechanism_language_signal",
    "extraction_readiness_rating",
    "extraction_mode_recommended",
    "duplicate_canonical_decision",
    "reviewer_notes",
    "reviewer",
    "reviewed_at",
]
SAFETY_COUNTER_FIELDS = [
    "urls_opened",
    "network_calls",
    "documents_downloaded",
    "documents_parsed",
    "pdfs_parsed",
    "ocr_runs",
    "content_artifacts_written",
]
OUTPUT_FIELDS = (
    IDENTITY_FIELDS + PLANNING_FIELDS + SOURCE_REVIEW_FIELDS + SAFETY_COUNTER_FIELDS
)


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=OUTPUT_FIELDS,
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_review_id(pilot_id: str, row: dict[str, str]) -> str:
    identity = (
        f"{pilot_id}|{row['candidate_queue_row_id']}|{row['triage_id']}"
    )
    return f"sr_{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def counts(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    return dict(
        sorted(Counter(str(row.get(field, "")) for row in rows).items())
    )


def validate_inputs(
    triage_rows: list[dict[str, str]], queue_rows: list[dict[str, str]]
) -> None:
    if not triage_rows:
        raise ValueError("Metadata-triage ledger is empty")
    missing = REQUIRED_TRIAGE_FIELDS - set(triage_rows[0])
    if missing:
        raise ValueError(
            f"Metadata-triage ledger lacks required fields: {sorted(missing)}"
        )
    queue_ids = [row["candidate_queue_row_id"] for row in triage_rows]
    triage_ids = [row["triage_id"] for row in triage_rows]
    if any(not value for value in queue_ids + triage_ids):
        raise ValueError("Metadata-triage ledger has blank identities")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Metadata-triage ledger repeats candidate identities")
    if len(triage_ids) != len(set(triage_ids)):
        raise ValueError("Metadata-triage ledger repeats triage identities")
    if queue_rows:
        queue_key = (
            "candidate_queue_row_id"
            if "candidate_queue_row_id" in queue_rows[0]
            else "queue_id"
            if "queue_id" in queue_rows[0]
            else "candidate_id"
            if "candidate_id" in queue_rows[0]
            else ""
        )
        if not queue_key:
            raise ValueError("Candidate queue lacks a stable row identity")
        values = [row.get(queue_key, "") for row in queue_rows]
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("Candidate queue identities are blank or duplicated")
        if set(queue_ids) != set(values):
            raise ValueError(
                "Metadata-triage identities do not equal candidate-queue identities"
            )


def is_duplicate(row: dict[str, str]) -> bool:
    if row.get("triage_status") in DUPLICATE_TRIAGE_STATUSES:
        return True
    try:
        return int(float(row.get("duplicate_group_size") or 0)) > 1
    except ValueError:
        return bool(row.get("duplicate_source_group_id"))


def eligible(
    row: dict[str, str],
    *,
    priority_scope: str,
    source_type_scope: str,
    exclude_duplicates: bool,
    exclude_oversized: bool,
    exclude_blocked: bool,
) -> bool:
    if priority_scope != "p1_download_allowed":
        raise ValueError("Only --priority-scope p1_download_allowed is supported")
    if (
        row.get("priority_for_content_review") != "p1"
        or row.get("recommended_next_action")
        != "content_review_download_allowed_later"
        or row.get("triage_status") != "high_priority_content_review"
    ):
        return False
    if row.get("candidate_status_before_verification") in LOWER_DISPOSITIONS:
        return False
    if source_type_scope == "cba_first" and row.get("candidate_source_type") != "cba":
        return False
    if source_type_scope not in {"cba_first", "all"}:
        raise ValueError(
            "Only --source-type-scope cba_first or all is supported"
        )
    if exclude_duplicates and is_duplicate(row):
        return False
    if exclude_oversized and (
        row.get("verification_status") == "too_large"
        or row.get("triage_status") in OVERSIZED_TRIAGE_STATUSES
    ):
        return False
    if exclude_blocked and row.get("verification_status") in BLOCKED_ROUTING_STATUSES:
        return False
    return True


def row_sort_key(row: dict[str, str]) -> tuple[object, ...]:
    official = 0 if row.get("official_domain_signal") == "likely_official" else 1
    matched = 0 if row.get("matched_set_potential") == "yes" else 1
    unit = {"police": 0, "fire": 1, "non_safety": 2}.get(
        row.get("unit_type_scouted", ""), 3
    )
    try:
        population = -int(float(row.get("population") or 0))
    except ValueError:
        population = 0
    return (
        official,
        matched,
        unit,
        population,
        row.get("municipality_id", ""),
        row.get("candidate_queue_row_id", ""),
    )


def diversify_municipalities(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    def municipality_order(
        unit_rows: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in sorted(unit_rows, key=row_sort_key):
            key = row.get("municipality_id") or row["candidate_queue_row_id"]
            groups[key].append(row)
        keys = sorted(
            groups,
            key=lambda key: (
                row_sort_key(groups[key][0]),
                key,
            ),
        )
        ordered: list[dict[str, str]] = []
        depth = 0
        while True:
            added = False
            for key in keys:
                if depth < len(groups[key]):
                    ordered.append(groups[key][depth])
                    added = True
            if not added:
                return ordered
            depth += 1

    by_unit: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_unit[row.get("unit_type_scouted", "unknown")].append(row)
    unit_order = [
        unit
        for unit in ("police", "fire", "non_safety", "unknown")
        if unit in by_unit
    ] + sorted(set(by_unit) - {"police", "fire", "non_safety", "unknown"})
    ordered_units = {
        unit: municipality_order(by_unit[unit]) for unit in unit_order
    }
    diversified: list[dict[str, str]] = []
    depth = 0
    while True:
        added = False
        for unit in unit_order:
            if depth < len(ordered_units[unit]):
                diversified.append(ordered_units[unit][depth])
                added = True
        if not added:
            return diversified
        depth += 1

def select_state_diverse(
    pool: list[dict[str, str]], pilot_size: int
) -> list[dict[str, str]]:
    by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pool:
        by_state[row.get("state", "")].append(row)
    state_order = sorted(by_state, key=lambda state: (-len(by_state[state]), state))
    ordered = {
        state: diversify_municipalities(by_state[state])
        for state in state_order
    }
    selected: list[dict[str, str]] = []
    depth = 0
    while len(selected) < pilot_size:
        added = False
        for state in state_order:
            if depth < len(ordered[state]):
                selected.append(ordered[state][depth])
                added = True
                if len(selected) == pilot_size:
                    break
        if not added:
            break
        depth += 1
    return selected


def build_rows(
    selected: list[dict[str, str]], pilot_id: str, num_lanes: int
) -> list[list[dict[str, object]]]:
    lane_sizes = [
        len(selected) // num_lanes + (1 if index < len(selected) % num_lanes else 0)
        for index in range(num_lanes)
    ]
    lanes: list[list[dict[str, object]]] = [[] for _ in range(num_lanes)]
    cursor = 0
    for lane_index, lane_size in enumerate(lane_sizes):
        for source in selected[cursor : cursor + lane_size]:
            row: dict[str, object] = {
                field: source.get(field, "") for field in OUTPUT_FIELDS
            }
            row.update(
                {
                    "source_review_id": stable_review_id(pilot_id, source),
                    "pilot_selection_rank": str(cursor + 1),
                    "source_review_lane_id": f"lane_{lane_index + 1}",
                    "source_review_stage": "planned_not_reviewed",
                    "pilot_selection_reason": (
                        "p1 scheduled CBA candidate with reachable PDF/document "
                        "routing; selected from committed metadata only"
                    ),
                    "source_review_status": "planned_not_reviewed",
                    "source_review_status_detail": (
                        "offline pilot planning only; source content not accessed"
                    ),
                    "url_access_status": "not_started",
                    "download_status": "not_started",
                    "content_type_observed": "unknown",
                    "text_layer_status": "unknown",
                    "source_officialness_rating": "unknown",
                    "source_relevance_rating": "unknown",
                    "municipality_match_rating": "unknown",
                    "employer_match_rating": "unknown",
                    "bargaining_unit_match_rating": "unknown",
                    "safety_unit_match_signal": "unknown",
                    "non_safety_unit_match_signal": "unknown",
                    "document_type_rating": "unknown",
                    "wage_table_signal": "unknown",
                    "wage_growth_signal": "unknown",
                    "mechanism_language_signal": "unknown",
                    "extraction_readiness_rating": "unknown",
                    "extraction_mode_recommended": "manual_review",
                    "duplicate_canonical_decision": "not_reviewed",
                    **{field: "0" for field in SAFETY_COUNTER_FIELDS},
                }
            )
            lanes[lane_index].append(row)
            cursor += 1
    return lanes


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def create_plan(args: argparse.Namespace) -> dict[str, object]:
    triage_path = Path(args.triage_ledger_csv)
    queue_path = Path(args.candidate_queue_csv)
    output_dir = Path(args.output_dir)
    if not 100 <= args.pilot_size <= 200:
        raise ValueError("--pilot-size must be between 100 and 200")
    if args.num_lanes < 1 or args.num_lanes > args.pilot_size:
        raise ValueError("--num-lanes must be positive and no greater than pilot size")
    triage_rows = read_csv(triage_path)
    queue_rows = read_csv(queue_path)
    validate_inputs(triage_rows, queue_rows)
    pool = [
        row
        for row in triage_rows
        if eligible(
            row,
            priority_scope=args.priority_scope,
            source_type_scope=args.source_type_scope,
            exclude_duplicates=args.exclude_duplicates,
            exclude_oversized=args.exclude_oversized,
            exclude_blocked=args.exclude_blocked,
        )
    ]
    if len(pool) < args.pilot_size:
        raise ValueError(
            f"Eligible pool has {len(pool)} rows, fewer than requested {args.pilot_size}"
        )
    selected = (
        select_state_diverse(pool, args.pilot_size)
        if args.state_diversity
        else sorted(pool, key=lambda row: (row_sort_key(row), row["state"]))[
            : args.pilot_size
        ]
    )
    lane_rows = build_rows(selected, args.pilot_id, args.num_lanes)
    review_ids = [
        str(row["source_review_id"]) for rows in lane_rows for row in rows
    ]
    queue_ids = [
        str(row["candidate_queue_row_id"]) for rows in lane_rows for row in rows
    ]
    if len(review_ids) != len(set(review_ids)):
        raise ValueError("Planner generated duplicate source-review IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Planner selected duplicate candidate identities")
    output_dir.mkdir(parents=True, exist_ok=True)
    lane_manifest: list[dict[str, object]] = []
    for index, rows in enumerate(lane_rows, start=1):
        lane_id = f"lane_{index}"
        input_path = output_dir / f"{lane_id}_source_review_input.csv"
        write_csv(input_path, rows)
        lane_info = {
            "lane_id": lane_id,
            "input_csv": input_path.as_posix(),
            "input_sha256": sha256_file(input_path),
            "expected_rows": len(rows),
            "dry_run_output_dir": (
                Path("tmp/source_review_pilots")
                / args.pilot_id
                / f"{lane_id}_dry_run"
            ).as_posix(),
            "future_live_output_dir": (
                Path("tmp/source_review_pilots")
                / args.pilot_id
                / f"{lane_id}_live_attempt1"
            ).as_posix(),
        }
        lane_manifest.append(lane_info)
        write_markdown(
            output_dir / f"{lane_id}_input_audit.md",
            f"""# {lane_id.replace('_', ' ').title()} Source-Review Input Audit

- Pilot: `{args.pilot_id}`
- Rows: {len(rows)}
- SHA-256: `{lane_info['input_sha256']}`
- Unique source-review IDs: {len({row['source_review_id'] for row in rows})}
- Unique candidate-queue IDs: {len({row['candidate_queue_row_id'] for row in rows})}
- States: {json.dumps(counts(rows, 'state'), sort_keys=True)}
- Source types: {json.dumps(counts(rows, 'candidate_source_type'), sort_keys=True)}
- Content types: {json.dumps(counts(rows, 'content_type'), sort_keys=True)}

This is an offline input audit. No URL or source content was accessed.
""",
        )
    selected_flat = [row for rows in lane_rows for row in rows]
    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "status": "planned_not_started",
        "pilot_id": args.pilot_id,
        "created_at": now_utc(),
        "triage_ledger_csv": triage_path.as_posix(),
        "triage_ledger_sha256": sha256_file(triage_path),
        "candidate_queue_csv": queue_path.as_posix(),
        "candidate_queue_sha256": sha256_file(queue_path),
        "metadata_triage_rows": len(triage_rows),
        "p1_rows": sum(
            row.get("priority_for_content_review") == "p1"
            for row in triage_rows
        ),
        "p1_download_allowed_rows": sum(
            row.get("priority_for_content_review") == "p1"
            and row.get("recommended_next_action")
            == "content_review_download_allowed_later"
            for row in triage_rows
        ),
        "eligible_pool_rows_after_exclusions": len(pool),
        "selected_rows": len(selected_flat),
        "pilot_size": args.pilot_size,
        "num_lanes": args.num_lanes,
        "priority_scope": args.priority_scope,
        "state_diversity": args.state_diversity,
        "source_type_scope": args.source_type_scope,
        "exclude_duplicates": args.exclude_duplicates,
        "exclude_oversized": args.exclude_oversized,
        "exclude_blocked": args.exclude_blocked,
        "selected_state_distribution": counts(selected_flat, "state"),
        "selected_source_type_distribution": counts(
            selected_flat, "candidate_source_type"
        ),
        "selected_content_type_distribution": counts(
            selected_flat, "content_type"
        ),
        "selected_candidate_disposition_distribution": counts(
            selected_flat, "candidate_status_before_verification"
        ),
        "selected_unit_type_distribution": counts(
            selected_flat, "unit_type_scouted"
        ),
        "selected_official_domain_signal_distribution": counts(
            selected_flat, "official_domain_signal"
        ),
        "selected_matched_set_potential_distribution": counts(
            selected_flat, "matched_set_potential"
        ),
        "selected_unique_municipalities": len(
            {row["municipality_id"] for row in selected_flat}
        ),
        "urls_opened": 0,
        "network_calls": 0,
        "documents_downloaded": 0,
        "documents_parsed": 0,
        "pdfs_parsed": 0,
        "ocr_runs": 0,
        "content_artifacts_written": 0,
        "lanes": lane_manifest,
    }
    write_json(output_dir / "source_review_pilot_manifest.json", manifest)
    write_markdown(
        output_dir / "source_review_pilot_input_audit.md",
        f"""# Source-Review Pilot Input Audit

Pilot: `{args.pilot_id}`

- Durable metadata-triage rows: {len(triage_rows):,}
- p1/download-allowed pool: {manifest['p1_download_allowed_rows']:,}
- Eligible after duplicate/oversized/blocked filters: {len(pool):,}
- Selected: {len(selected_flat):,}
- Lanes: {' / '.join(str(len(rows)) for rows in lane_rows)}
- Unique source-review IDs: {len(set(review_ids)):,}
- Unique candidate-queue IDs: {len(set(queue_ids)):,}
- States represented: {len(manifest['selected_state_distribution'])}
- Unique municipalities: {manifest['selected_unique_municipalities']:,}

Selection used only committed metadata. No URL was opened, no source was
downloaded or parsed, and no source received a final rating.
""",
    )
    write_markdown(
        output_dir / "source_review_operating_handoff.md",
        f"""# Source-Review Pilot Operating Handoff

The `{args.pilot_id}` pilot is locked to {len(selected_flat)} rows in
{args.num_lanes} balanced lanes. Run the dry-run source-review command for each
lane before any separately authorized content-review implementation. The
current runner is dry-run only and must fail closed for live review.

No input label is a final officialness, relevance, employer, bargaining-unit,
document-type, extraction-readiness, wage, or mechanism finding.
""",
    )
    write_markdown(
        output_dir / "source_review_live_prompt_stub.md",
        f"""# Future Live Source-Review Prompt Stub

Use `{args.pilot_id}` only after explicit authorization and after a bounded
content-access implementation has been independently reviewed. Start with dry
runs, use conservative concurrency and byte limits, save lane-local artifacts,
and stop before merge. Do not ingest, codify, extract wages, calculate wage
gaps, or make causal claims.
""",
    )
    write_markdown(
        output_dir / "source_review_merge_prompt_stub.md",
        f"""# Future Source-Review Merge Prompt Stub

Audit every completed `{args.pilot_id}` lane and merge exactly once only if all
identity, terminal-status, artifact, and safety gates pass. Preserve the
metadata-triage layer unchanged. Do not open URLs, ingest, codify, extract
wages, or calculate wage gaps during the serial merge.
""",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--triage-ledger-csv", default=DEFAULT_TRIAGE_LEDGER.as_posix()
    )
    parser.add_argument(
        "--candidate-queue-csv", default=DEFAULT_QUEUE.as_posix()
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR.as_posix())
    parser.add_argument("--pilot-id", default=DEFAULT_PILOT_ID)
    parser.add_argument("--pilot-size", type=int, default=150)
    parser.add_argument("--num-lanes", type=int, default=2)
    parser.add_argument(
        "--priority-scope", default="p1_download_allowed"
    )
    parser.add_argument(
        "--state-diversity",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--source-type-scope", default="cba_first")
    parser.add_argument(
        "--exclude-duplicates",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--exclude-oversized",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--exclude-blocked",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = create_plan(args)
    print(
        "Source-review pilot prepared offline: "
        f"{manifest['selected_rows']} rows across {manifest['num_lanes']} lanes; "
        "0 URL opens, downloads, parses, or content ratings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
