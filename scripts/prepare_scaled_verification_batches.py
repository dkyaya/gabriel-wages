#!/usr/bin/env python3
"""Prepare deterministic, offline candidate-source verification batches.

This planner never opens a candidate URL. It treats the national scout queue as
an immutable candidate-stage input, enriches identities from committed local
municipality files, assigns stable verification and duplicate-group IDs, and
writes plans only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUEUE = (
    ROOT / "docs" / "analysis" / "national_scout_candidate_queue_2026-07-20.csv"
)
DEFAULT_UNIVERSE = ROOT / "docs" / "analysis" / "national_municipality_universe.csv"
DEFAULT_YIELD = (
    ROOT / "docs" / "analysis" / "scout_yield_learning_by_state_2026-07-22.csv"
)
SCHEDULED_BUCKETS = {
    "high_priority_later_verify": "high",
    "medium_priority_later_verify": "medium",
    "low_priority_later_verify": "low",
}
HOLD_BUCKETS = {
    "context_only_hold",
    "insufficient_hold",
    "already_canonical_hold",
    "rejected_from_calibration",
}
DUPLICATE_BUCKET = "likely_duplicate_hold"
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "held": 3}
VERIFICATION_PROFILES = {
    "conservative_250": {"num_lanes": 3, "batch_size": 250},
    "standard_500": {"num_lanes": 3, "batch_size": 500},
    "aggressive_750": {"num_lanes": 3, "batch_size": 750},
    "max_1000": {"num_lanes": 3, "batch_size": 1000},
}
DEFAULT_CONCURRENCY = 8
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_BYTES = 10_485_760
DEFAULT_MAX_REDIRECTS = 5

IDENTITY_FIELDS = [
    "verification_id",
    "candidate_queue_row_id",
    "candidate_queue_stable_key",
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "candidate_url",
    "candidate_title",
    "candidate_source_type",
    "candidate_priority",
    "candidate_status_before_verification",
    "triage_bucket",
    "duplicate_source_group_id",
    "duplicate_group_size",
    "duplicate_group_role",
    "near_duplicate_candidate_key",
    "population",
    "state_candidate_rows_per_covered",
    "unit_type_scouted",
    "source_owner_type",
    "scout_confidence",
    "triage_score",
    "source_wave",
    "verification_stage",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
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


def stable_digest(prefix: str, value: str, length: int = 20) -> str:
    return f"{prefix}{hashlib.sha256(value.encode('utf-8')).hexdigest()[:length]}"


def normalize_url(value: str) -> str:
    """Normalize a URL without making any network request."""

    parsed = urlsplit(value.strip())
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, host, path, parsed.query, ""))


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def candidate_disposition(row: dict[str, str]) -> str:
    bucket = row.get("triage_bucket", "").strip()
    if bucket in SCHEDULED_BUCKETS:
        return "scheduled"
    if bucket == DUPLICATE_BUCKET:
        return "duplicate_hold"
    if bucket == "context_only_hold":
        return "context_hold"
    if bucket == "insufficient_hold":
        return "insufficient_hold"
    if bucket == "already_canonical_hold":
        return "already_canonical"
    if bucket == "rejected_from_calibration":
        return "calibration_rejected"
    return "other_hold"


def candidate_priority(row: dict[str, str]) -> str:
    return SCHEDULED_BUCKETS.get(row.get("triage_bucket", "").strip(), "held")


def load_local_enrichment(
    universe_path: Path = DEFAULT_UNIVERSE,
    yield_path: Path = DEFAULT_YIELD,
) -> tuple[dict[str, dict[str, str]], dict[str, float]]:
    universe = {row["municipality_id"]: row for row in read_csv(universe_path)}
    state_yield = {
        row["state"]: float(row.get("candidate_rows_per_covered_municipality") or 0)
        for row in read_csv(yield_path)
    }
    return universe, state_yield


def enrich_candidates(
    queue_rows: list[dict[str, str]],
    universe: dict[str, dict[str, str]],
    state_yield: dict[str, float],
) -> list[dict[str, object]]:
    required = {
        "queue_id",
        "municipality_id",
        "state",
        "municipality",
        "source_url",
        "document_title",
        "document_type_scouted",
        "triage_bucket",
    }
    if queue_rows:
        missing = required - set(queue_rows[0])
        if missing:
            raise ValueError(f"Candidate queue is missing required fields: {sorted(missing)}")

    normalized_urls: list[str] = []
    for row in queue_rows:
        if not row.get("queue_id", "").strip():
            raise ValueError("Candidate queue contains a blank queue_id")
        if not valid_http_url(row.get("source_url", "")):
            raise ValueError(f"Invalid or missing candidate URL for {row['queue_id']}")
        normalized_urls.append(normalize_url(row["source_url"]))

    url_counts = Counter(normalized_urls)
    first_queue_id: dict[str, str] = {}
    enriched: list[dict[str, object]] = []
    for row, normalized in zip(queue_rows, normalized_urls):
        municipality_id = row["municipality_id"].strip()
        municipality = universe.get(municipality_id)
        if municipality is None:
            raise ValueError(
                f"Candidate {row['queue_id']} has no municipality-universe match"
            )
        if municipality["state"] != row["state"]:
            raise ValueError(f"State mismatch for candidate {row['queue_id']}")
        group_id = stable_digest("URL-", normalized)
        role = "primary" if normalized not in first_queue_id else "linked_duplicate"
        first_queue_id.setdefault(normalized, row["queue_id"])
        title_key = re.sub(
            r"[^a-z0-9]+", " ", row.get("document_title", "").lower()
        ).strip()
        near_key_value = "|".join(
            [
                municipality_id,
                row.get("unit_type_scouted", "").lower().strip(),
                row.get("document_type_scouted", "").lower().strip(),
                title_key,
            ]
        )
        disposition = candidate_disposition(row)
        enriched.append(
            {
                "verification_id": stable_digest("VER-", row["queue_id"]),
                "candidate_queue_row_id": row["queue_id"],
                "candidate_queue_stable_key": row["queue_id"],
                "municipality_id": municipality_id,
                "census_gov_id": municipality["census_gov_id"],
                "state": row["state"],
                "municipality": row["municipality"],
                "government_name": municipality["government_name"],
                "candidate_url": row["source_url"].strip(),
                "candidate_title": row.get("document_title", ""),
                "candidate_source_type": row.get("document_type_scouted", ""),
                "candidate_priority": candidate_priority(row),
                "candidate_status_before_verification": disposition,
                "triage_bucket": row.get("triage_bucket", ""),
                "duplicate_source_group_id": group_id,
                "duplicate_group_size": url_counts[normalized],
                "duplicate_group_role": role,
                "near_duplicate_candidate_key": stable_digest("KEY-", near_key_value),
                "population": int(municipality.get("population") or 0),
                "state_candidate_rows_per_covered": round(
                    state_yield.get(row["state"], 0.0), 6
                ),
                "unit_type_scouted": row.get("unit_type_scouted", ""),
                "source_owner_type": row.get("source_owner_type", ""),
                "scout_confidence": row.get("confidence", ""),
                "triage_score": row.get("triage_score", ""),
                "source_wave": row.get("source_wave", ""),
                "verification_stage": "candidate_lead_planned_not_verified",
            }
        )
    ids = [str(row["verification_id"]) for row in enriched]
    if len(ids) != len(set(ids)):
        raise ValueError("Stable verification IDs are not unique")
    return enriched


def eligible_for_scope(
    row: dict[str, object],
    *,
    priority_scope: str,
    include_held: bool,
    include_duplicates: bool,
    state_scope: set[str] | None,
) -> bool:
    state = str(row["state"])
    if state_scope and state not in state_scope:
        return False
    disposition = str(row["candidate_status_before_verification"])
    priority = str(row["candidate_priority"])
    if priority_scope == "scheduled":
        return disposition == "scheduled"
    if priority_scope in {"high", "medium", "low"}:
        return disposition == "scheduled" and priority == priority_scope
    if priority_scope != "all":
        raise ValueError(f"Unsupported priority scope: {priority_scope}")
    if disposition == "scheduled":
        return True
    if disposition == "duplicate_hold":
        return include_duplicates
    return include_held


def sort_candidates(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            PRIORITY_ORDER[str(row["candidate_priority"])],
            -float(row["state_candidate_rows_per_covered"]),
            -int(row["population"]),
            str(row["state"]),
            str(row["candidate_queue_row_id"]),
        ),
    )


def distribute_lanes(
    rows: list[dict[str, object]],
    num_lanes: int,
    batch_size: int,
    *,
    dedupe_fetch_plan: bool = False,
) -> list[list[dict[str, object]]]:
    selected = rows[: num_lanes * batch_size]
    lanes: list[list[dict[str, object]]] = [[] for _ in range(num_lanes)]
    if not dedupe_fetch_plan:
        for index, row in enumerate(selected):
            lanes[index % num_lanes].append(row)
    else:
        groups: dict[str, list[dict[str, object]]] = {}
        group_order: list[str] = []
        for row in selected:
            group_id = str(row["duplicate_source_group_id"])
            if group_id not in groups:
                group_order.append(group_id)
                groups[group_id] = []
            groups[group_id].append(row)
        remaining = [batch_size] * num_lanes
        for group_id in group_order:
            group = groups[group_id]
            candidates = [
                index
                for index, capacity in enumerate(remaining)
                if capacity >= len(group)
            ]
            if candidates:
                lane_index = max(candidates, key=lambda index: (remaining[index], -index))
                lanes[lane_index].extend(group)
                remaining[lane_index] -= len(group)
            else:
                # Extremely large groups are deterministically split rather than
                # dropping identities. The manifest records any cross-lane group.
                for row in group:
                    lane_index = max(
                        range(num_lanes),
                        key=lambda index: (remaining[index], -index),
                    )
                    if remaining[lane_index] <= 0:
                        raise AssertionError("No remaining lane capacity")
                    lanes[lane_index].append(row)
                    remaining[lane_index] -= 1
    if len(selected) == num_lanes * batch_size and any(
        len(lane) != batch_size for lane in lanes
    ):
        raise AssertionError("Lane distribution did not produce equal full lanes")
    return lanes


def runtime_estimate(
    rows_per_lane: int, concurrency: int, timeout_seconds: float
) -> dict[str, float]:
    """Return transparent rough bounds, not a service-level guarantee."""

    request_waves = math.ceil(rows_per_lane / concurrency)
    return {
        "expected_lower_minutes": round(request_waves * 2 / 60, 1),
        "expected_upper_minutes": round(request_waves * 8 / 60, 1),
        "all_rows_timeout_upper_minutes": round(
            request_waves * timeout_seconds / 60, 1
        ),
    }


def counts_by(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[field]) for row in rows).items()))


def lane_audit_markdown(
    lane_number: int, path: Path, rows: list[dict[str, object]]
) -> str:
    groups = Counter(str(row["duplicate_source_group_id"]) for row in rows)
    return f"""# Verification Round Lane {lane_number} Input Audit

- Input: `{path.as_posix()}`
- Rows: {len(rows):,}
- SHA-256: `{sha256_file(path)}`
- Unique verification IDs: {len({row['verification_id'] for row in rows}):,}
- Unique candidate queue rows: {len({row['candidate_queue_row_id'] for row in rows}):,}
- Syntactically valid HTTP(S) URLs: {sum(valid_http_url(str(row['candidate_url'])) for row in rows):,}/{len(rows):,}
- Candidate priorities: `{json.dumps(counts_by(rows, 'candidate_priority'), sort_keys=True)}`
- States: `{json.dumps(counts_by(rows, 'state'), sort_keys=True)}`
- Candidate source types: `{json.dumps(counts_by(rows, 'candidate_source_type'), sort_keys=True)}`
- Exact duplicate URL groups represented: {sum(count > 1 for count in groups.values()):,}
- Duplicate rows eligible for in-lane fetch reuse: {sum(count - 1 for count in groups.values() if count > 1):,}

This is an offline locked planning input. No URL was opened, no source was
verified, and no row was promoted beyond candidate-lead status.
"""


def live_commands(
    round_id: str,
    output_dir: Path,
    num_lanes: int,
    *,
    timeout: float,
    concurrency: int,
    max_bytes: int,
) -> str:
    lines = [
        f"# Future Live Verification Commands — {round_id}",
        "",
        "**Do not run these commands without separate explicit live authorization.**",
        "Run each lane only after its dry run passes. Keep concurrency conservative,",
        "write only lane-local artifacts, and stop before any ledger merge.",
        "",
    ]
    for lane in range(1, num_lanes + 1):
        input_path = output_dir / f"lane_{lane}_verification_input.csv"
        live_dir = Path("tmp/verification_rounds") / round_id / f"lane_{lane}_live_attempt1"
        lines.extend(
            [
                f"## Lane {lane}",
                "",
                "```bash",
                "python scripts/verify_candidate_sources.py \\",
                f"  --input-csv {input_path.as_posix()} \\",
                f"  --output-dir {live_dir.as_posix()} \\",
                f"  --candidate-artifact-dir {live_dir.as_posix()}/candidate_artifacts \\",
                f"  --timeout {timeout:g} \\",
                "  --connect-timeout 8 \\",
                "  --read-timeout 15 \\",
                f"  --max-redirects {DEFAULT_MAX_REDIRECTS} \\",
                f"  --max-bytes {max_bytes} \\",
                f"  --concurrency {concurrency} \\",
                "  --no-write-content-samples \\",
                "  --respect-robots-note",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "The bounded live path is implemented, but these commands require a",
            "separate explicit live-verification authorization. They never ingest,",
            "codify, extract wages, or calculate gaps.",
            "",
        ]
    )
    return "\n".join(lines)


def merge_handoff(round_id: str, num_lanes: int) -> str:
    lane_list = ", ".join(f"Lane {index}" for index in range(1, num_lanes + 1))
    return f"""# Verification Merge Handoff — {round_id}

Audit {lane_list} together with `scripts/audit_verification_lanes.py`. Require
exact input coverage, unique verification IDs, terminal lane outputs, preserved
duplicate groups, and no ambiguous partial rows. Only a separately authorized
serial task may merge eligible lanes into a durable verified-source ledger.

That merge must not update scout coverage, ingest contracts, run
`gabriel.codify`, extract wages, calculate wage gaps, or turn a verification
status into claim evidence. Candidate, verified, ingested, codified, and
analysis-ready stages remain distinct.
"""


def build_full_backlog(
    *,
    output_dir: Path,
    round_id: str,
    inventory: list[dict[str, object]],
    selected: list[dict[str, object]],
    queue_path: Path,
    batch_size: int,
    num_lanes: int,
    args: argparse.Namespace,
) -> None:
    scheduled = [row for row in inventory if row["candidate_status_before_verification"] == "scheduled"]
    capacity = batch_size * num_lanes
    inventory_path = output_dir / "full_backlog_inventory.csv"
    write_csv(inventory_path, selected, IDENTITY_FIELDS)
    scenarios = [
        ("scheduled_3x750", len(scheduled), 3, 750),
        ("all_url_bearing_3x750", len(inventory), 3, 750),
        ("all_url_bearing_3x1000", len(inventory), 3, 1000),
    ]
    planned: list[dict[str, object]] = []
    for scenario, row_count, scenario_lanes, scenario_batch in scenarios:
        scenario_capacity = scenario_lanes * scenario_batch
        for start in range(0, row_count, scenario_capacity):
            round_number = start // scenario_capacity + 1
            rows_this_round = min(scenario_capacity, row_count - start)
            planned.append(
                {
                    "scenario": scenario,
                    "round_number": round_number,
                    "planned_round_id": (
                        f"{scenario.upper()}-ROUND{round_number}-PLANNED"
                    ),
                    "row_start": start + 1,
                    "row_end": start + rows_this_round,
                    "candidate_rows": rows_this_round,
                    "lanes": scenario_lanes,
                    "nominal_rows_per_lane": scenario_batch,
                    "round_capacity": scenario_capacity,
                    "status": "planned_not_run",
                }
            )
    write_csv(
        output_dir / "planned_rounds.csv",
        planned,
        [
            "scenario",
            "round_number",
            "planned_round_id",
            "row_start",
            "row_end",
            "candidate_rows",
            "lanes",
            "nominal_rows_per_lane",
            "round_capacity",
            "status",
        ],
    )
    scheduled_rounds_3x750 = math.ceil(len(scheduled) / 2250)
    all_rounds_3x750 = math.ceil(len(inventory) / 2250)
    all_rounds_3x1000 = math.ceil(len(inventory) / 3000)
    manifest = {
        "schema_version": "2.0.0",
        "round_id": round_id,
        "plan_type": "full_verification_backlog",
        "status": "planned_not_run",
        "candidate_queue_csv": queue_path.as_posix(),
        "candidate_queue_sha256": sha256_file(queue_path),
        "total_url_bearing_candidate_rows": len(inventory),
        "selected_backlog_rows": len(selected),
        "full_backlog_inventory_csv": inventory_path.as_posix(),
        "full_backlog_inventory_sha256": sha256_file(inventory_path),
        "scheduled_verification_rows": len(scheduled),
        "held_or_other_rows": len(inventory) - len(scheduled),
        "selected_profile": getattr(args, "profile", "aggressive_750"),
        "batch_size_per_lane": batch_size,
        "num_lanes": num_lanes,
        "round_capacity": capacity,
        "scheduled_rounds_required_3x750": scheduled_rounds_3x750,
        "full_backlog_rounds_required_3x750": all_rounds_3x750,
        "full_backlog_rounds_required_3x1000": all_rounds_3x1000,
        "priority_scope": args.priority_scope,
        "include_held": args.include_held,
        "include_duplicates": args.include_duplicates,
        "network_calls": 0,
        "urls_opened": 0,
    }
    write_json(output_dir / "full_backlog_manifest.json", manifest)
    summary = f"""# Full Verification Backlog Plan

- Total URL-bearing candidate rows: {len(inventory):,}
- Scheduled verification rows: {len(scheduled):,}
- Held/context/duplicate/canonical/rejected rows: {len(inventory) - len(scheduled):,}
- Scheduled-only at 3×750 (2,250/round): {scheduled_rounds_3x750} rounds
- All URL-bearing rows at 3×750: {all_rounds_3x750} rounds
- All URL-bearing rows at 3×1,000: {all_rounds_3x1000} rounds
- Candidate priorities: `{json.dumps(counts_by(inventory, 'candidate_priority'), sort_keys=True)}`
- Candidate dispositions: `{json.dumps(counts_by(inventory, 'candidate_status_before_verification'), sort_keys=True)}`
- State distribution: `{json.dumps(counts_by(inventory, 'state'), sort_keys=True)}`

Every original candidate identity remains represented. Exact URL duplicates
share deterministic duplicate-group IDs so later live verification can open a
source once and link all original queue rows without losing provenance.

This is planning only: zero URLs opened, zero network/API/model calls, and zero
verification, ingestion, codification, extraction, or wage analysis.
"""
    (output_dir / "full_backlog_summary.md").write_text(summary, encoding="utf-8")


def prepare(args: argparse.Namespace) -> dict[str, object]:
    queue_path = Path(args.candidate_queue_csv)
    output_dir = Path(args.output_dir)
    profile_name = getattr(args, "profile", None) or "conservative_250"
    if profile_name not in VERIFICATION_PROFILES:
        raise ValueError(f"Unsupported profile: {profile_name}")
    profile = VERIFICATION_PROFILES[profile_name]
    if getattr(args, "batch_size", None) is None:
        args.batch_size = profile["batch_size"]
    if getattr(args, "num_lanes", None) is None:
        args.num_lanes = profile["num_lanes"]
    args.profile = profile_name
    args.concurrency_per_lane = getattr(
        args, "concurrency_per_lane", DEFAULT_CONCURRENCY
    )
    args.verification_timeout = getattr(
        args, "verification_timeout", DEFAULT_TIMEOUT
    )
    args.max_bytes = getattr(args, "max_bytes", DEFAULT_MAX_BYTES)
    args.dedupe_fetch_plan = getattr(args, "dedupe_fetch_plan", False)
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    if args.num_lanes < 1:
        raise ValueError("--num-lanes must be positive")
    if args.num_lanes > 12:
        raise ValueError("--num-lanes above 12 requires a framework change")
    if args.concurrency_per_lane < 1:
        raise ValueError("--concurrency-per-lane must be positive")
    if args.verification_timeout <= 0:
        raise ValueError("--verification-timeout must be positive")
    if args.max_bytes < 1:
        raise ValueError("--max-bytes must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)

    queue_rows = read_csv(queue_path)
    universe, state_yield = load_local_enrichment()
    inventory = enrich_candidates(queue_rows, universe, state_yield)
    state_scope = (
        {value.strip().upper() for value in args.state_scope.split(",") if value.strip()}
        if args.state_scope
        else None
    )
    selected = sort_candidates(
        [
            row
            for row in inventory
            if eligible_for_scope(
                row,
                priority_scope=args.priority_scope,
                include_held=args.include_held,
                include_duplicates=args.include_duplicates,
                state_scope=state_scope,
            )
        ]
    )
    if not selected:
        raise ValueError("No candidate rows match the requested verification scope")

    if args.round_id.startswith("FULL-BACKLOG"):
        build_full_backlog(
            output_dir=output_dir,
            round_id=args.round_id,
            inventory=inventory,
            selected=selected,
            queue_path=queue_path,
            batch_size=args.batch_size,
            num_lanes=args.num_lanes,
            args=args,
        )
        return {"inventory": inventory, "selected": selected, "lanes": []}

    requested = args.batch_size * args.num_lanes
    if len(selected) < requested:
        raise ValueError(
            f"Requested {requested} rows but only {len(selected)} match the scope"
        )
    lanes = distribute_lanes(
        selected,
        args.num_lanes,
        args.batch_size,
        dedupe_fetch_plan=args.dedupe_fetch_plan,
    )
    selected_rows = [row for lane in lanes for row in lane]
    selected_ids = [str(row["verification_id"]) for row in selected_rows]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("Duplicate verification IDs across lanes")

    lane_records: list[dict[str, object]] = []
    for index, lane in enumerate(lanes, start=1):
        input_path = output_dir / f"lane_{index}_verification_input.csv"
        write_csv(input_path, lane, IDENTITY_FIELDS)
        lane_records.append(
            {
                "lane_id": f"lane_{index}",
                "lane_number": index,
                "input_csv": input_path.as_posix(),
                "input_sha256": sha256_file(input_path),
                "expected_rows": len(lane),
                "expected_concurrency": args.concurrency_per_lane,
                "expected_timeout_seconds": args.verification_timeout,
                "expected_max_bytes": args.max_bytes,
                "dry_run_output_dir": (
                    Path("tmp/verification_rounds")
                    / args.round_id
                    / f"lane_{index}_dry_run"
                ).as_posix(),
                "live_output_dir": (
                    Path("tmp/verification_rounds")
                    / args.round_id
                    / f"lane_{index}_live_attempt1"
                ).as_posix(),
            }
        )
        audit_path = output_dir / f"lane_{index}_input_audit.md"
        audit_path.write_text(
            lane_audit_markdown(index, input_path, lane), encoding="utf-8"
        )

    duplicate_groups = Counter(
        str(row["duplicate_source_group_id"]) for row in inventory
    )
    selected_group_lanes: dict[str, set[int]] = {}
    for lane_index, lane in enumerate(lanes, start=1):
        for row in lane:
            selected_group_lanes.setdefault(
                str(row["duplicate_source_group_id"]), set()
            ).add(lane_index)
    selected_groups = Counter(
        str(row["duplicate_source_group_id"]) for row in selected_rows
    )
    estimate = runtime_estimate(
        args.batch_size,
        args.concurrency_per_lane,
        args.verification_timeout,
    )
    manifest = {
        "schema_version": "2.0.0",
        "round_id": args.round_id,
        "plan_type": "scaled_candidate_source_verification",
        "status": "planned_not_run",
        "created_date": date.today().isoformat(),
        "candidate_queue_csv": queue_path.as_posix(),
        "candidate_queue_sha256": sha256_file(queue_path),
        "total_url_bearing_candidate_rows": len(inventory),
        "eligible_rows_in_requested_scope": len(selected),
        "planned_candidate_rows": len(selected_rows),
        "profile": args.profile,
        "batch_size_per_lane": args.batch_size,
        "num_lanes": args.num_lanes,
        "concurrency_per_lane": args.concurrency_per_lane,
        "verification_timeout_seconds": args.verification_timeout,
        "connect_timeout_seconds": 8,
        "read_timeout_seconds": 15,
        "max_redirects": DEFAULT_MAX_REDIRECTS,
        "max_bytes": args.max_bytes,
        "write_content_samples": False,
        "dedupe_fetch_plan": args.dedupe_fetch_plan,
        "runtime_estimate": estimate,
        "priority_scope": args.priority_scope,
        "include_held": args.include_held,
        "include_duplicates": args.include_duplicates,
        "state_scope": sorted(state_scope) if state_scope else "ALL",
        "duplicate_url_groups_in_full_queue": sum(
            count > 1 for count in duplicate_groups.values()
        ),
        "duplicate_url_extra_rows_in_full_queue": sum(
            count - 1 for count in duplicate_groups.values() if count > 1
        ),
        "duplicate_url_groups_in_selected_round": sum(
            count > 1 for count in selected_groups.values()
        ),
        "duplicate_fetch_reuse_rows_in_selected_round": sum(
            count - 1 for count in selected_groups.values() if count > 1
        ),
        "duplicate_groups_split_across_lanes": sum(
            len(lane_numbers) > 1
            for lane_numbers in selected_group_lanes.values()
        ),
        "candidate_stage_boundary": (
            "planned candidate leads only; not verified, ingested, codified, "
            "wage-extracted, or analysis-ready"
        ),
        "network_calls": 0,
        "urls_opened": 0,
        "lanes": lane_records,
    }
    write_json(output_dir / "verification_round_manifest.json", manifest)
    audit = f"""# Verification Round Input Audit — {args.round_id}

## Scope

- Canonical queue: `{queue_path.as_posix()}`
- Queue SHA-256: `{sha256_file(queue_path)}`
- Total URL-bearing queue rows: {len(inventory):,}
- Requested scope: `{args.priority_scope}`
- Eligible rows in scope: {len(selected):,}
- Planned rows: {len(selected_rows):,}
- Profile: `{args.profile}`
- Lanes: {args.num_lanes}
- Rows per lane: {args.batch_size}
- Concurrency per lane: {args.concurrency_per_lane}
- Bounded timeout: {args.verification_timeout:g} seconds
- Maximum response bytes: {args.max_bytes:,}
- Duplicate-aware lane assignment: {args.dedupe_fetch_plan}
- Expected lane runtime (2–8 second average response assumption): {estimate['expected_lower_minutes']:.1f}–{estimate['expected_upper_minutes']:.1f} minutes
- Timeout-heavy upper bound: {estimate['all_rows_timeout_upper_minutes']:.1f} minutes
- Unique verification IDs across lanes: {len(set(selected_ids)):,}
- Duplicate verification IDs across lanes: {len(selected_ids) - len(set(selected_ids))}
- Syntactically valid HTTP(S) URLs: {sum(valid_http_url(str(row['candidate_url'])) for row in selected_rows):,}/{len(selected_rows):,}
- Candidate priorities: `{json.dumps(counts_by(selected_rows, 'candidate_priority'), sort_keys=True)}`
- Candidate dispositions: `{json.dumps(counts_by(selected_rows, 'candidate_status_before_verification'), sort_keys=True)}`
- States: `{json.dumps(counts_by(selected_rows, 'state'), sort_keys=True)}`
- Candidate source types: `{json.dumps(counts_by(selected_rows, 'candidate_source_type'), sort_keys=True)}`
- Exact normalized URL duplicate groups in full queue: {sum(count > 1 for count in duplicate_groups.values()):,}
- Extra rows linked to exact duplicate URLs in full queue: {sum(count - 1 for count in duplicate_groups.values() if count > 1):,}
- Exact duplicate URL groups in selected round: {sum(count > 1 for count in selected_groups.values()):,}
- Selected duplicate rows eligible for reuse: {sum(count - 1 for count in selected_groups.values() if count > 1):,}
- Selected duplicate groups split across lanes: {sum(len(lane_numbers) > 1 for lane_numbers in selected_group_lanes.values()):,}

## Gate

**PASS.** Every selected row preserves its original queue identity and has a
unique deterministic verification ID, complete municipality/Census identity,
syntactically valid URL, stable duplicate group, and explicit candidate-stage
status. No URL was opened. No network/API/model call, live verification,
ingestion, codification, extraction, or wage analysis occurred.
"""
    (output_dir / "verification_round_input_audit.md").write_text(
        audit, encoding="utf-8"
    )
    (output_dir / "verification_live_commands.md").write_text(
        live_commands(
            args.round_id,
            output_dir,
            args.num_lanes,
            timeout=args.verification_timeout,
            concurrency=args.concurrency_per_lane,
            max_bytes=args.max_bytes,
        ),
        encoding="utf-8",
    )
    (output_dir / "verification_merge_handoff.md").write_text(
        merge_handoff(args.round_id, args.num_lanes), encoding="utf-8"
    )
    return {"inventory": inventory, "selected": selected, "lanes": lanes}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-queue-csv", default=str(DEFAULT_QUEUE))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument(
        "--profile",
        choices=sorted(VERIFICATION_PROFILES),
        default="conservative_250",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Override the selected profile's per-lane row count.",
    )
    parser.add_argument(
        "--num-lanes",
        type=int,
        help="Override the selected profile's lane count.",
    )
    parser.add_argument(
        "--concurrency-per-lane", type=int, default=DEFAULT_CONCURRENCY
    )
    parser.add_argument(
        "--verification-timeout", type=float, default=DEFAULT_TIMEOUT
    )
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--include-held", action="store_true")
    parser.add_argument("--include-duplicates", action="store_true")
    parser.add_argument(
        "--dedupe-fetch-plan",
        action="store_true",
        help="Keep exact URL groups together where lane capacity permits.",
    )
    parser.add_argument(
        "--priority-scope",
        choices=["scheduled", "high", "medium", "low", "all"],
        default="scheduled",
    )
    parser.add_argument(
        "--state-scope",
        default="",
        help="Optional comma-separated state abbreviations.",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Required safety acknowledgement; this program is offline in all modes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.plan_only:
        raise SystemExit("--plan-only is required; this planner never runs verification")
    result = prepare(args)
    print(
        f"Prepared {args.round_id}: inventory={len(result['inventory']):,}; "
        f"scope={len(result['selected']):,}; lanes={len(result['lanes'])}; "
        "URLs opened=0; network calls=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
