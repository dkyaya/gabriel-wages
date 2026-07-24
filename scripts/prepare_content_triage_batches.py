#!/usr/bin/env python3
"""Prepare deterministic offline content-triage planning batches.

This planner reads durable URL-routing outcomes and committed candidate
metadata. It never opens a URL, downloads content, parses a document, or
changes any upstream accounting/evidence layer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROUTING_LEDGER = (
    ROOT
    / "docs"
    / "analysis"
    / "verification_ledgers"
    / "verified_source_routing_ledger_cumulative.csv"
)
DEFAULT_QUEUE = (
    ROOT / "docs" / "analysis" / "national_scout_candidate_queue_2026-07-20.csv"
)
DEFAULT_STATE_YIELD = (
    ROOT / "docs" / "analysis" / "scout_yield_learning_by_state_2026-07-22.csv"
)

ELIGIBLE_ROUTING_STATUSES = {
    "reachable_pdf_or_document",
    "reachable_html",
    "reachable_http",
    "duplicate_of_verified_source",
    "duplicate_same_url_pending",
}
SUCCESSFULLY_REACHABLE_OR_REUSED = {
    "reachable_pdf_or_document",
    "reachable_html",
    "reachable_http",
    "duplicate_of_verified_source",
}
DEFERRED_ROUTING_STATUSES = {
    "blocked_or_forbidden",
    "not_found",
    "too_large",
    "error",
    "ssl_error",
    "timeout",
    "connection_error",
}
SOURCE_TYPE_ORDER = {
    "cba": 0,
    "wage_schedule_or_compensation_plan": 1,
    "pay_plan": 1,
    "arbitration_award": 2,
    "factfinding": 3,
    "memorandum_or_settlement": 4,
    "ordinance_or_policy": 5,
    "index_page": 6,
    "meeting_minutes": 7,
    "agenda_cover_sheet": 8,
    "context_only": 9,
    "insufficient_source": 10,
    "blocked_or_unreadable": 11,
    "unknown": 12,
}
DIRECT_STATUS_ORDER = {
    "reachable_pdf_or_document": 0,
    "reachable_html": 1,
    "reachable_http": 2,
    "duplicate_of_verified_source": 3,
    "duplicate_same_url_pending": 4,
}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "held": 3}
LOWER_DISPOSITIONS = {
    "context_hold",
    "insufficient_hold",
    "duplicate_hold",
    "already_canonical",
    "calibration_rejected",
    "other_hold",
}
TRIAGE_STATUSES = [
    "triage_planned",
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
]

IDENTITY_FIELDS = [
    "triage_id",
    "candidate_queue_row_id",
    "verification_id",
    "verification_round_id",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "final_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_status_before_verification",
    "verification_status",
    "content_type",
    "source_locator",
]
PLANNING_FIELDS = [
    "triage_bucket",
    "candidate_priority",
    "verification_lane_id",
    "duplicate_source_group_id",
    "duplicate_group_size",
    "duplicate_group_role_for_triage",
    "source_owner_type",
    "unit_type_scouted",
    "population",
    "state_candidate_rows_per_covered",
    "matched_set_potential",
    "official_domain_signal",
    "triage_selection_rank",
    "triage_stage",
]
TRIAGE_FIELDS = [
    "triage_status",
    "triage_status_detail",
    "source_relevance_prelim",
    "source_officialness_prelim",
    "employer_match_prelim",
    "municipality_match_prelim",
    "bargaining_unit_match_prelim",
    "safety_unit_signal_prelim",
    "non_safety_unit_signal_prelim",
    "source_document_type_prelim",
    "source_year_or_period_prelim",
    "wage_table_signal_prelim",
    "wage_growth_signal_prelim",
    "mechanism_language_signal_prelim",
    "extraction_readiness_prelim",
    "priority_for_content_review",
    "recommended_next_action",
    "duplicate_handling_status",
    "oversized_handling_status",
    "manual_review_reason",
    "triage_notes",
    "reviewer",
    "triaged_at",
]
OUTPUT_FIELDS = IDENTITY_FIELDS + PLANNING_FIELDS + TRIAGE_FIELDS


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


def stable_id(prefix: str, value: str, length: int = 20) -> str:
    return f"{prefix}{hashlib.sha256(value.encode('utf-8')).hexdigest()[:length]}"


def counts(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, "")) for row in rows).items()))


def canonical_content_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower() or "unknown"


def is_official_looking(url: str, owner: str) -> bool:
    host = urlsplit(url).hostname or ""
    return (
        host.endswith(".gov")
        or host.endswith(".us")
        or owner in {"city", "state_labor_board", "union"}
    )


def queue_disposition(row: dict[str, str]) -> str:
    bucket = row.get("triage_bucket", "")
    return {
        "high_priority_later_verify": "scheduled",
        "medium_priority_later_verify": "scheduled",
        "low_priority_later_verify": "scheduled",
        "context_only_hold": "context_hold",
        "insufficient_hold": "insufficient_hold",
        "likely_duplicate_hold": "duplicate_hold",
        "already_canonical_hold": "already_canonical",
        "rejected_from_calibration": "calibration_rejected",
    }.get(bucket, "other_hold")


def queue_priority(row: dict[str, str]) -> str:
    return {
        "high_priority_later_verify": "high",
        "medium_priority_later_verify": "medium",
        "low_priority_later_verify": "low",
    }.get(row.get("triage_bucket", ""), "held")


def validate_and_join(
    routing_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    *,
    round_id: str,
) -> list[dict[str, object]]:
    required_routing = {
        "verification_id",
        "candidate_queue_row_id",
        "verification_round_id",
        "municipality_id",
        "census_gov_id",
        "state",
        "municipality",
        "government_name",
        "candidate_url",
        "final_url",
        "candidate_title",
        "candidate_source_type",
        "candidate_status_before_verification",
        "verification_status",
        "content_type",
        "duplicate_source_group_id",
        "verification_stage",
    }
    required_queue = {
        "queue_id",
        "municipality_id",
        "state",
        "municipality",
        "source_url",
        "document_title",
        "document_type_scouted",
        "source_owner_type",
        "unit_type_scouted",
        "triage_bucket",
    }
    if not routing_rows or required_routing - set(routing_rows[0]):
        raise ValueError(
            "Cumulative routing ledger is empty or missing required fields: "
            f"{sorted(required_routing - set(routing_rows[0] if routing_rows else []))}"
        )
    if not queue_rows or required_queue - set(queue_rows[0]):
        raise ValueError(
            "Candidate queue is empty or missing required fields: "
            f"{sorted(required_queue - set(queue_rows[0] if queue_rows else []))}"
        )
    routing_ids = [row["verification_id"] for row in routing_rows]
    routing_queue_ids = [row["candidate_queue_row_id"] for row in routing_rows]
    queue_ids = [row["queue_id"] for row in queue_rows]
    if len(routing_ids) != len(set(routing_ids)):
        raise ValueError("Cumulative routing ledger has duplicate verification IDs")
    if len(routing_queue_ids) != len(set(routing_queue_ids)):
        raise ValueError("Cumulative routing ledger has duplicate candidate queue IDs")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Candidate queue has duplicate queue IDs")
    if set(routing_queue_ids) != set(queue_ids):
        raise ValueError(
            "Routing ledger is not cumulative/complete for the candidate queue"
        )
    if any(
        row.get("verification_stage") != "url_reachability_metadata_verified"
        for row in routing_rows
    ):
        raise ValueError("Routing ledger contains a non-durable verification stage")
    terminal = ELIGIBLE_ROUTING_STATUSES | DEFERRED_ROUTING_STATUSES
    if any(row.get("verification_status") not in terminal for row in routing_rows):
        raise ValueError("Routing ledger contains an unknown/nonterminal status")

    queue_by_id = {row["queue_id"]: row for row in queue_rows}
    state_yield = {}
    if DEFAULT_STATE_YIELD.exists():
        state_yield = {
            row["state"]: float(
                row.get("candidate_rows_per_covered_municipality") or 0
            )
            for row in read_csv(DEFAULT_STATE_YIELD)
        }
    group_sizes = Counter(
        row.get("duplicate_source_group_id", "") for row in routing_rows
    )
    units_by_municipality: dict[str, set[str]] = defaultdict(set)
    for routed in routing_rows:
        qrow = queue_by_id[routed["candidate_queue_row_id"]]
        units_by_municipality[routed["municipality_id"]].add(
            qrow.get("unit_type_scouted", "")
        )

    rows: list[dict[str, object]] = []
    for routed in routing_rows:
        qrow = queue_by_id[routed["candidate_queue_row_id"]]
        if routed["municipality_id"] != qrow["municipality_id"]:
            raise ValueError(
                f"Municipality mismatch for {routed['candidate_queue_row_id']}"
            )
        disposition = queue_disposition(qrow)
        if routed["candidate_status_before_verification"] != disposition:
            raise ValueError(
                f"Disposition mismatch for {routed['candidate_queue_row_id']}"
            )
        locator = routed.get("final_url") or routed["candidate_url"]
        units = units_by_municipality[routed["municipality_id"]]
        matched_potential = (
            any(unit in {"police", "fire"} for unit in units)
            and "non_safety" in units
        )
        group_id = routed.get("duplicate_source_group_id", "")
        rows.append(
            {
                "triage_id": stable_id(
                    "TRI-",
                    f"{round_id}|{routed['candidate_queue_row_id']}|"
                    f"{routed['verification_id']}",
                ),
                "candidate_queue_row_id": routed["candidate_queue_row_id"],
                "verification_id": routed["verification_id"],
                "verification_round_id": routed["verification_round_id"],
                "municipality_id": routed["municipality_id"],
                "census_gov_id": routed["census_gov_id"],
                "state": routed["state"],
                "municipality": routed["municipality"],
                "government_name": routed["government_name"],
                "candidate_url": routed["candidate_url"],
                "final_url": routed.get("final_url", ""),
                "candidate_title": routed.get("candidate_title")
                or qrow.get("document_title", ""),
                "candidate_source_type": routed.get("candidate_source_type")
                or qrow.get("document_type_scouted", ""),
                "candidate_status_before_verification": disposition,
                "verification_status": routed["verification_status"],
                "content_type": canonical_content_type(routed.get("content_type", "")),
                "source_locator": locator,
                "triage_bucket": qrow.get("triage_bucket", ""),
                "candidate_priority": queue_priority(qrow),
                "verification_lane_id": routed.get("verification_lane_id", ""),
                "duplicate_source_group_id": group_id,
                "duplicate_group_size": group_sizes[group_id],
                "duplicate_group_role_for_triage": "",
                "source_owner_type": qrow.get("source_owner_type", ""),
                "unit_type_scouted": qrow.get("unit_type_scouted", ""),
                "population": "",
                "state_candidate_rows_per_covered": round(
                    state_yield.get(routed["state"], 0.0), 6
                ),
                "matched_set_potential": "yes" if matched_potential else "no",
                "official_domain_signal": (
                    "likely_official"
                    if is_official_looking(locator, qrow.get("source_owner_type", ""))
                    else "unknown"
                ),
                "triage_selection_rank": "",
                "triage_stage": "metadata_first_planned_not_reviewed",
                "triage_status": "triage_planned",
                "triage_status_detail": (
                    "offline metadata-only planning; content not opened or reviewed"
                ),
                "source_relevance_prelim": "unknown",
                "source_officialness_prelim": "unknown",
                "employer_match_prelim": "unknown",
                "municipality_match_prelim": "unknown",
                "bargaining_unit_match_prelim": "unknown",
                "safety_unit_signal_prelim": "unknown",
                "non_safety_unit_signal_prelim": "unknown",
                "source_document_type_prelim": "unknown",
                "source_year_or_period_prelim": "unknown",
                "wage_table_signal_prelim": "unknown",
                "wage_growth_signal_prelim": "unknown",
                "mechanism_language_signal_prelim": "unknown",
                "extraction_readiness_prelim": "unknown",
                "priority_for_content_review": (
                    "p1"
                    if queue_priority(qrow) == "high"
                    and disposition == "scheduled"
                    else "p2"
                    if disposition == "scheduled"
                    else "defer"
                ),
                "recommended_next_action": "metadata_review_only",
                "duplicate_handling_status": "",
                "oversized_handling_status": "not_oversized",
                "manual_review_reason": "",
                "triage_notes": "",
                "reviewer": "",
                "triaged_at": "",
            }
        )
    return rows


def sort_key(row: dict[str, object]) -> tuple[object, ...]:
    source_type = str(row["candidate_source_type"])
    return (
        PRIORITY_ORDER.get(str(row["candidate_priority"]), 9),
        DIRECT_STATUS_ORDER.get(str(row["verification_status"]), 9),
        SOURCE_TYPE_ORDER.get(source_type, 20),
        0 if row["official_domain_signal"] == "likely_official" else 1,
        0 if row["matched_set_potential"] == "yes" else 1,
        -float(row["state_candidate_rows_per_covered"] or 0),
        str(row["state"]),
        str(row["candidate_queue_row_id"]),
    )


def mark_duplicate_representatives(
    eligible_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int, int]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in eligible_rows:
        groups[str(row["duplicate_source_group_id"])].append(row)
    representatives: list[dict[str, object]] = []
    duplicate_groups = 0
    duplicate_rows = 0
    for group_rows in groups.values():
        ordered = sorted(group_rows, key=sort_key)
        if len(ordered) > 1:
            duplicate_groups += 1
            duplicate_rows += len(ordered) - 1
        for index, row in enumerate(ordered):
            row["duplicate_group_role_for_triage"] = (
                "canonical_representative" if index == 0 else "linked_duplicate"
            )
            row["duplicate_handling_status"] = (
                "canonical_representative_selected_first"
                if index == 0 and len(ordered) > 1
                else "linked_duplicate_deferred_by_default"
                if len(ordered) > 1
                else "unique_source"
            )
        representatives.append(ordered[0])
    return representatives, duplicate_groups, duplicate_rows


def eligible_for_scope(
    row: dict[str, object],
    *,
    priority_scope: str,
    include_html: bool,
    include_lower_disposition: bool,
) -> bool:
    status = str(row["verification_status"])
    if status not in ELIGIBLE_ROUTING_STATUSES:
        return False
    if not include_html and status == "reachable_html":
        return False
    disposition = str(row["candidate_status_before_verification"])
    if not include_lower_disposition and disposition in LOWER_DISPOSITIONS:
        return False
    if priority_scope == "scheduled_high_priority_reachable":
        return disposition == "scheduled" and row["candidate_priority"] == "high"
    if priority_scope == "scheduled_reachable":
        return disposition == "scheduled"
    if priority_scope == "all_reachable":
        return True
    raise ValueError(f"Unsupported priority scope: {priority_scope}")


def lane_markdown(lane: int, path: Path, rows: list[dict[str, object]]) -> str:
    return f"""# Content-Triage Lane {lane} Input Audit

- Input: `{path.as_posix()}`
- Rows: {len(rows):,}
- SHA-256: `{sha256_file(path)}`
- Unique triage IDs: {len({row['triage_id'] for row in rows}):,}
- Unique candidate queue IDs: {len({row['candidate_queue_row_id'] for row in rows}):,}
- Routing statuses: `{json.dumps(counts(rows, 'verification_status'), sort_keys=True)}`
- Candidate dispositions: `{json.dumps(counts(rows, 'candidate_status_before_verification'), sort_keys=True)}`
- Candidate source types: `{json.dumps(counts(rows, 'candidate_source_type'), sort_keys=True)}`
- Content types: `{json.dumps(counts(rows, 'content_type'), sort_keys=True)}`
- States: `{json.dumps(counts(rows, 'state'), sort_keys=True)}`
- Duplicate representatives: {sum(row['duplicate_group_role_for_triage'] == 'canonical_representative' for row in rows):,}

This is an offline metadata-first planning input. No URL was opened, no source
content was downloaded or parsed, and no row was promoted into evidence.
"""


def prepare(args: argparse.Namespace) -> dict[str, object]:
    routing_path = Path(args.routing_ledger_csv)
    queue_path = Path(args.candidate_queue_csv)
    output_dir = Path(args.output_dir)
    if args.batch_size <= 0 or args.num_lanes <= 0:
        raise ValueError("batch size and lane count must be positive")
    routing_rows = read_csv(routing_path)
    queue_rows = read_csv(queue_path)
    joined = validate_and_join(routing_rows, queue_rows, round_id=args.round_id)

    routing_status_counts = counts(joined, "verification_status")
    routing_eligible = [
        row for row in joined if row["verification_status"] in ELIGIBLE_ROUTING_STATUSES
    ]
    successfully_reachable = [
        row
        for row in joined
        if row["verification_status"] in SUCCESSFULLY_REACHABLE_OR_REUSED
    ]
    scoped_all = [
        row
        for row in routing_eligible
        if eligible_for_scope(
            row,
            priority_scope=args.priority_scope,
            include_html=args.include_html,
            include_lower_disposition=args.include_lower_disposition,
        )
    ]
    representatives, duplicate_groups, linked_duplicate_rows = (
        mark_duplicate_representatives(routing_eligible)
    )
    representative_ids = {str(row["triage_id"]) for row in representatives}
    scoped = [
        row
        for row in scoped_all
        if args.include_duplicates or row["triage_id"] in representative_ids
    ]
    selected = sorted(scoped, key=sort_key)[: args.batch_size]
    for index, row in enumerate(selected, start=1):
        row["triage_selection_rank"] = index
    lanes: list[list[dict[str, object]]] = [
        [] for _ in range(args.num_lanes)
    ]
    for index, row in enumerate(selected):
        lanes[index % args.num_lanes].append(row)

    triage_ids = [str(row["triage_id"]) for row in selected]
    queue_ids = [str(row["candidate_queue_row_id"]) for row in selected]
    if len(triage_ids) != len(set(triage_ids)):
        raise ValueError("Selected triage IDs are not unique")
    if len(queue_ids) != len(set(queue_ids)):
        raise ValueError("Selected candidate queue IDs are not unique")

    output_dir.mkdir(parents=True, exist_ok=True)
    lane_entries: list[dict[str, object]] = []
    for lane_number, lane_rows in enumerate(lanes, start=1):
        input_path = output_dir / f"lane_{lane_number}_content_triage_input.csv"
        write_csv(input_path, lane_rows)
        lane_entries.append(
            {
                "lane_id": f"lane_{lane_number}",
                "input_csv": input_path.as_posix(),
                "input_sha256": sha256_file(input_path),
                "expected_rows": len(lane_rows),
                "dry_run_output_dir": (
                    Path("tmp/content_triage_rounds")
                    / args.round_id
                    / f"lane_{lane_number}_dry_run"
                ).as_posix(),
                "future_live_output_dir": (
                    Path("tmp/content_triage_rounds")
                    / args.round_id
                    / f"lane_{lane_number}_live_attempt1"
                ).as_posix(),
            }
        )
        (output_dir / f"lane_{lane_number}_input_audit.md").write_text(
            lane_markdown(lane_number, input_path, lane_rows),
            encoding="utf-8",
        )

    selected_groups = Counter(
        str(row["duplicate_source_group_id"]) for row in selected
    )
    manifest: dict[str, object] = {
        "schema_version": "1.0.0",
        "round_id": args.round_id,
        "plan_type": "offline_metadata_first_content_triage",
        "status": "planned_not_started",
        "created_date": date.today().isoformat(),
        "routing_ledger_csv": routing_path.as_posix(),
        "routing_ledger_sha256": sha256_file(routing_path),
        "candidate_queue_csv": queue_path.as_posix(),
        "candidate_queue_sha256": sha256_file(queue_path),
        "total_routed_rows": len(joined),
        "reachable_or_successfully_reused_rows": len(successfully_reachable),
        "routing_eligible_rows_including_duplicate_pending": len(routing_eligible),
        "eligible_rows_in_scope_before_duplicate_policy": len(scoped_all),
        "eligible_rows_after_duplicate_policy": len(scoped),
        "selected_rows": len(selected),
        "unselected_rows_in_scope": len(scoped) - len(selected),
        "batch_size_total": args.batch_size,
        "num_lanes": args.num_lanes,
        "priority_scope": args.priority_scope,
        "include_html": args.include_html,
        "include_duplicates": args.include_duplicates,
        "include_lower_disposition": args.include_lower_disposition,
        "exclude_too_large": args.exclude_too_large,
        "routing_status_distribution": routing_status_counts,
        "selected_verification_status_distribution": counts(
            selected, "verification_status"
        ),
        "selected_state_distribution": counts(selected, "state"),
        "selected_source_type_distribution": counts(
            selected, "candidate_source_type"
        ),
        "selected_content_type_distribution": counts(selected, "content_type"),
        "selected_candidate_disposition_distribution": counts(
            selected, "candidate_status_before_verification"
        ),
        "duplicate_group_count_in_routing_eligible_pool": duplicate_groups,
        "linked_duplicate_rows_in_routing_eligible_pool": linked_duplicate_rows,
        "selected_duplicate_group_count": sum(
            count > 1 for count in selected_groups.values()
        ),
        "too_large_rows_deferred": routing_status_counts.get("too_large", 0),
        "blocked_not_found_error_transport_rows_deferred": sum(
            routing_status_counts.get(status, 0)
            for status in DEFERRED_ROUTING_STATUSES
            if status != "too_large"
        ),
        "lower_disposition_routing_eligible_rows": sum(
            row["candidate_status_before_verification"] in LOWER_DISPOSITIONS
            for row in routing_eligible
        ),
        "lower_disposition_rows_selected": sum(
            row["candidate_status_before_verification"] in LOWER_DISPOSITIONS
            for row in selected
        ),
        "triage_stage_boundary": (
            "metadata-first planning only; no URL opening, content review, "
            "download, parsing, extraction, ingestion, codification, or analysis"
        ),
        "network_calls": 0,
        "urls_opened": 0,
        "documents_downloaded": 0,
        "documents_parsed": 0,
        "lanes": lane_entries,
    }
    write_json(output_dir / "content_triage_round_manifest.json", manifest)
    audit = f"""# Content-Triage Round Input Audit — {args.round_id}

## Result

- Total durable routing rows: {len(joined):,}
- Reachable or successfully reused rows: {len(successfully_reachable):,}
- Routing-eligible rows including duplicate-pending: {len(routing_eligible):,}
- Eligible rows in requested scope before duplicate policy: {len(scoped_all):,}
- Eligible rows after duplicate policy: {len(scoped):,}
- Selected rows: {len(selected):,}
- Lanes: {args.num_lanes}
- Lane row counts: `{json.dumps({entry['lane_id']: entry['expected_rows'] for entry in lane_entries}, sort_keys=True)}`
- Selected states: `{json.dumps(counts(selected, 'state'), sort_keys=True)}`
- Selected source types: `{json.dumps(counts(selected, 'candidate_source_type'), sort_keys=True)}`
- Selected content types: `{json.dumps(counts(selected, 'content_type'), sort_keys=True)}`
- Selected dispositions: `{json.dumps(counts(selected, 'candidate_status_before_verification'), sort_keys=True)}`

## Deferred and duplicate boundaries

- Routing-eligible duplicate groups: {duplicate_groups:,}
- Linked duplicate rows in those groups: {linked_duplicate_rows:,}
- Duplicate rows selected: {sum(row['duplicate_group_role_for_triage'] == 'linked_duplicate' for row in selected):,}
- Lower-disposition routing-eligible rows: {manifest['lower_disposition_routing_eligible_rows']:,}
- Lower-disposition rows selected: {manifest['lower_disposition_rows_selected']:,}
- `too_large` rows deferred: {manifest['too_large_rows_deferred']:,}
- Other blocked/not-found/error/transport rows deferred: {manifest['blocked_not_found_error_transport_rows_deferred']:,}

The round is deterministic, metadata-first planning. No URL was opened, no
document was downloaded or parsed, no PDF/OCR operation ran, and no routing
outcome was promoted into source evidence or wage data.
"""
    (output_dir / "content_triage_input_audit.md").write_text(
        audit, encoding="utf-8"
    )
    (output_dir / "content_triage_operating_handoff.md").write_text(
        f"""# Content-Triage Operating Handoff — {args.round_id}

Run both lane inputs through `scripts/content_triage_sources.py --dry-run`,
then audit them together with `scripts/audit_content_triage_lanes.py`.

This plan authorizes metadata-only dry planning. Any future content access,
download, parsing, or human review requires separate authorization and an
implemented bounded content-review path. Do not ingest, codify, extract wages,
or calculate wage gaps.
""",
        encoding="utf-8",
    )
    (output_dir / "content_triage_live_prompt_stub.md").write_text(
        f"""# Future Content-Triage Live Prompt Stub — {args.round_id}

Not executable in this task. Start with fresh dry runs and an exact lane audit.
Live metadata/content review requires separate explicit authorization and a
bounded implementation. Stop before durable triage-ledger merge. Do not ingest,
codify, extract wages, or make wage-gap or causal claims.
""",
        encoding="utf-8",
    )
    (output_dir / "content_triage_merge_prompt_stub.md").write_text(
        f"""# Future Content-Triage Merge Prompt Stub — {args.round_id}

Audit all planned lanes. Merge terminal triage outcomes exactly once only if a
future audit recommends it. Preserve routing provenance and duplicate groups.
Do not open URLs, ingest, codify, extract wages, or update scout accounting.
""",
        encoding="utf-8",
    )
    return {"manifest": manifest, "selected": selected, "lanes": lanes}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--routing-ledger-csv", default=DEFAULT_ROUTING_LEDGER.as_posix()
    )
    parser.add_argument("--candidate-queue-csv", default=DEFAULT_QUEUE.as_posix())
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--num-lanes", type=int, default=2)
    parser.add_argument(
        "--priority-scope",
        choices=[
            "scheduled_high_priority_reachable",
            "scheduled_reachable",
            "all_reachable",
        ],
        default="scheduled_high_priority_reachable",
    )
    parser.add_argument("--include-html", action="store_true")
    parser.add_argument("--include-duplicates", action="store_true")
    parser.add_argument("--include-lower-disposition", action="store_true")
    parser.add_argument(
        "--exclude-too-large",
        action="store_true",
        default=True,
        help="Retained for explicit plan provenance; too_large is always deferred.",
    )
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = prepare(args)
    manifest = result["manifest"]
    print(
        "Content-triage plan prepared offline: "
        f"{manifest['selected_rows']} rows across {manifest['num_lanes']} lanes; "
        "URLs opened=0; documents downloaded=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
