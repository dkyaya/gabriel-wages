#!/usr/bin/env python3
"""Prepare isolated, nonoverlapping scout lane inputs and command previews.

This script is offline only. It reads committed priority, coverage, failure,
canonical-status, and deterministic-hint artifacts. It never runs a scout,
calls a backend, opens a URL, verifies a source, rebuilds shared accounting, or
commits. ``--plan-only`` is intentionally required for the current framework:
it writes locked planning artifacts but executes none of the generated commands.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs" / "analysis"
DEFAULT_PRIORITY_TARGETS = (
    ANALYSIS / "national_priority_tier_top_targets_2026-07-22.csv"
)
DEFAULT_PRIORITY_TIERS = (
    ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
)
DEFAULT_COVERAGE = (
    ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
)
DEFAULT_FAILURES = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"
DEFAULT_HINTS = ANALYSIS / "municipality_search_hints_2026-07-22.csv"
EXPECTED_POST_PI_WAVE1_HASH = (
    "56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700"
)
PRIORITY_SOURCE_COMMIT = "3f2f815f4ca4b4e90f6ca1bff769bd300843d703"
PLANNER_BASELINE_COMMIT = "c4cf7d0de79a2a734adeb9eb03ee37ce02125e8a"
PROFILES = {
    "standard_150": {
        "num_lanes": 3,
        "rows_per_lane": 150,
        "stagger_seconds": 240,
    },
    "aggressive_250": {
        "num_lanes": 3,
        "rows_per_lane": 250,
        "stagger_seconds": 420,
    },
    "aggressive_300": {
        "num_lanes": 3,
        "rows_per_lane": 300,
        "stagger_seconds": 480,
    },
}
ALLOWED_GOVERNMENTS = {
    ("municipal", "place"),
    ("township", "county_subdivision"),
}
TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"", "0", "false", "no", "n"}
EXPECTED_UNITS = (
    "municipal police; municipal fire only when the exact target government is "
    "the employer; at least one ordinary general-municipal non-safety unit "
    "(clerical_admin/public_works/sanitation/library) where available; public "
    "arbitration, factfinding, impasse, compensation-plan, or other authoritative "
    "wage-setting material; prioritize overlapping 2014-2024 cycles"
)
OUTPUT_NAMES = {
    "parallel_round_manifest.json",
    "parallel_round_input_audit.md",
    "lane_dry_run_commands.md",
    "lane_live_commands.md",
    "lane_merge_handoff.md",
}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def write_text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_true(value: str) -> bool:
    return value.strip().lower() in TRUE_VALUES


def is_false(value: str) -> bool:
    return value.strip().lower() in FALSE_VALUES


def distribution(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field, "") or "(missing)" for row in rows).items()))


def rendered_distribution(values: dict[str, int]) -> str:
    return ", ".join(f"{key} {count}" for key, count in values.items())


def full_priority_sort_key(row: dict[str, str]) -> tuple[Any, ...]:
    population = row.get("population", "")
    return (
        int(row["priority_tier"].split()[-1]),
        -float(row["total_priority_score"]),
        not bool(population),
        -int(population or 0),
        row["state"],
        row["municipality_id"],
    )


def ensure_unique_index(
    rows: list[dict[str, str]], field: str, label: str
) -> dict[str, dict[str, str]]:
    values = [row.get(field, "") for row in rows]
    if any(not value for value in values):
        raise ValueError(f"{label} contains a blank {field}")
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise ValueError(f"{label} contains duplicate {field}: {duplicates[:5]}")
    return {row[field]: row for row in rows}


def eligibility_failures(
    row: dict[str, str],
    coverage: dict[str, str],
    failure_ids: set[str],
) -> list[str]:
    reasons: list[str] = []
    municipality_id = row["municipality_id"]
    if not is_true(row.get("future_scout_eligible_flag", "")):
        reasons.append("future_scout_eligible_flag is not true")
    if not is_false(row.get("retry_flag", "")):
        reasons.append("retry_flag is true")
    if not is_false(row.get("failure_only_flag", "")):
        reasons.append("failure_only_flag is true")
    if row.get("scout_coverage_status") != "not_scouted":
        reasons.append("priority status is already covered")
    if not is_false(row.get("already_canonical_flag", "")):
        reasons.append("priority status is already canonical")
    if municipality_id in failure_ids:
        reasons.append("municipality appears in failure/retry ledger")
    if coverage.get("scout_coverage_status") != "not_scouted":
        reasons.append("coverage status is already covered")
    if coverage.get("successful_live_scout_count", "0") != "0":
        reasons.append("coverage has a successful live scout")
    if not is_false(coverage.get("already_in_corpus", "")):
        reasons.append("coverage marks canonical corpus presence")
    if (
        row.get("government_type"),
        row.get("geography_type"),
    ) not in ALLOWED_GOVERNMENTS:
        reasons.append("government category is outside intended scope")
    return reasons


def verification_notes(row: dict[str, str]) -> str:
    return (
        f"Scout-stage only. Target exactly {row['government_name']} "
        f"(Census government ID {row['census_gov_id']}; locked municipality ID "
        f"{row['municipality_id']}). County context: "
        f"{row['county_context_summary']}. Do not substitute counties, schools, "
        "transit/port/airport/housing authorities, special districts, universities, "
        "state/federal employers, or private providers. A safety agreement cannot "
        "satisfy the ordinary non-safety request. Return no candidates if no "
        "qualifying exact-employer source is found. Distinguish blocked from dead "
        "links, suppress duplicates, do not make or recommend public-records "
        "requests, and keep results unverified pending later employer/unit/"
        "provenance/date/wage/overlap review."
    )


def validate_lane_rows(
    rows: list[dict[str, str]],
    *,
    expected_count: int,
    lane_id: str,
    priority_by_id: dict[str, dict[str, str]],
    coverage_by_id: dict[str, dict[str, str]],
    failure_ids: set[str],
    hints_by_id: dict[str, dict[str, str]],
) -> None:
    if len(rows) != expected_count:
        raise ValueError(
            f"{lane_id} must contain {expected_count} rows; found {len(rows)}"
        )
    municipality_ids = [row.get("municipality_id", "") for row in rows]
    census_ids = [row.get("census_gov_id", "") for row in rows]
    if not all(municipality_ids) or len(set(municipality_ids)) != expected_count:
        raise ValueError(f"{lane_id} municipality IDs are blank or duplicated")
    nonblank_census = [value for value in census_ids if value]
    if len(nonblank_census) != len(set(nonblank_census)):
        raise ValueError(f"{lane_id} has duplicate nonblank Census IDs")

    for row in rows:
        municipality_id = row["municipality_id"]
        if municipality_id not in priority_by_id:
            raise ValueError(f"{lane_id} ID missing from full priority data: {municipality_id}")
        if municipality_id not in coverage_by_id:
            raise ValueError(f"{lane_id} ID missing from coverage: {municipality_id}")
        if municipality_id not in hints_by_id:
            raise ValueError(f"{lane_id} ID missing from hints: {municipality_id}")
        current = priority_by_id[municipality_id]
        failures = eligibility_failures(
            current, coverage_by_id[municipality_id], failure_ids
        )
        if failures:
            raise ValueError(
                f"{lane_id} row {municipality_id} is not ordinary eligible: "
                + "; ".join(failures)
            )
        if row.get("census_gov_id", "") != current.get("census_gov_id", ""):
            raise ValueError(f"{lane_id} Census ID drift for {municipality_id}")
        for index in range(1, 6):
            field = f"search_hint_{index}"
            if (
                not row.get(field, "")
                or row[field] != hints_by_id[municipality_id][field]
            ):
                raise ValueError(f"{lane_id} hint mismatch for {municipality_id}: {field}")


def build_selected_lane_row(
    *,
    source: dict[str, str],
    hint: dict[str, str],
    round_id: str,
    lane_number: int,
    lane_rank: int,
    rows_per_lane: int,
    priority_targets_path: Path,
    fields: list[str],
) -> dict[str, str]:
    round_rank = (lane_number - 1) * rows_per_lane + lane_rank
    values = {
        "post_pi_wave_rank": str(round_rank),
        "original_priority_rank": source.get(
            "_target_rank", source.get("national_priority_rank", "")
        ),
        "post_pi_wave_id": round_id,
        "worker_batch": f"parallel_lane_{lane_number}",
        "worker_batch_row": str(lane_rank),
        "future_live_queue_id": f"{round_id}-LANE{lane_number}",
        "municipality_id": source["municipality_id"],
        "census_gov_id": source["census_gov_id"],
        "state": source["state"],
        "municipality": source["municipality"],
        "government_name": source["government_name"],
        "government_type": source["government_type"],
        "geography_type": source["geography_type"],
        "population": source["population"],
        "county_relationship_count": source["county_relationship_count"],
        "multi_county_flag": source["multi_county_flag"],
        "county_context_summary": source["county_context_summary"],
        "total_priority_score": source["total_priority_score"],
        "priority_tier": source["priority_tier"],
        "priority_confidence": source["priority_confidence"],
        "population_score": source["population_score"],
        "government_type_score": source["government_type_score"],
        "state_yield_score": source["state_yield_score"],
        "research_design_score": source["research_design_score"],
        "geographic_value_score": source["geographic_value_score"],
        "evidence_signal_score": source["evidence_signal_score"],
        "retry_flag": source["retry_flag"],
        "failure_only_flag": source["failure_only_flag"],
        "scout_coverage_status": source["scout_coverage_status"],
        "candidate_row_count": source["candidate_row_count"],
        "future_scout_eligible_flag": source["future_scout_eligible_flag"],
        "future_scout_exclusion_reason": source["future_scout_exclusion_reason"],
        "priority_reason_summary": source["priority_reason_summary"],
        "source_priority_file": relative(priority_targets_path),
        "source_priority_commit": PRIORITY_SOURCE_COMMIT,
        "search_hints_available": "true",
        "search_hint_1": hint["search_hint_1"],
        "search_hint_2": hint["search_hint_2"],
        "search_hint_3": hint["search_hint_3"],
        "search_hint_4": hint["search_hint_4"],
        "search_hint_5": hint["search_hint_5"],
        "already_canonical_flag": source["already_canonical_flag"],
        "candidate_positive_flag": source["candidate_positive_flag"],
        "expected_units_to_search": EXPECTED_UNITS,
        "verification_notes": verification_notes(source),
        "recommended_scout_status": f"locked_for_{round_id.lower()}_lane_{lane_number}",
        "worker_id": f"lane_{lane_number}",
        "worker_state_scope": "CROSS_STATE_PARALLEL_SCOUT_ROUND",
        "worker_rank_min": str((lane_number - 1) * rows_per_lane + 1),
        "worker_rank_max": str(lane_number * rows_per_lane),
        "worker_assignment_method": "rank_ordered_disjoint_parallel_lane",
    }
    return {field: values.get(field, source.get(field, "")) for field in fields}


def lane_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    scores = [float(row["total_priority_score"]) for row in rows]
    populations = [int(row["population"]) for row in rows if row.get("population")]
    census_ids = [row.get("census_gov_id", "") for row in rows]
    return {
        "row_count": len(rows),
        "unique_municipality_ids": len({row["municipality_id"] for row in rows}),
        "unique_nonblank_census_ids": len({value for value in census_ids if value}),
        "missing_census_ids": sum(not bool(value) for value in census_ids),
        "states": distribution(rows, "state"),
        "priority_tiers": distribution(rows, "priority_tier"),
        "confidence": distribution(rows, "priority_confidence"),
        "score_min": round(min(scores), 3),
        "score_median": round(float(median(scores)), 3),
        "score_max": round(max(scores), 3),
        "population_min": min(populations) if populations else None,
        "population_median": int(median(populations)) if populations else None,
        "population_max": max(populations) if populations else None,
        "search_hints_complete": sum(
            all(row.get(f"search_hint_{index}", "") for index in range(1, 6))
            for row in rows
        ),
    }


def lane_audit_text(
    *,
    round_id: str,
    lane_id: str,
    lane_path: Path,
    rows: list[dict[str, str]],
    copied_unchanged: bool,
) -> str:
    summary = lane_summary(rows)
    return f"""# {round_id} — {lane_id} Input Audit

Disposition: **PASS — offline locked lane; not live-authorized.**

- Input: `{relative(lane_path)}`
- SHA-256: `{sha256(lane_path)}`
- Rows: {summary['row_count']}
- Unique municipality IDs: {summary['unique_municipality_ids']}
- Unique nonblank Census IDs: {summary['unique_nonblank_census_ids']}
- Missing Census IDs: {summary['missing_census_ids']}
- Existing locked input copied byte-for-byte: `{str(copied_unchanged).lower()}`
- Ordinary current eligibility: PASS
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Search hints complete and exact: {summary['search_hints_complete']}/{summary['row_count']}
- States: {rendered_distribution(summary['states'])}
- Priority tiers: {rendered_distribution(summary['priority_tiers'])}
- Confidence: {rendered_distribution(summary['confidence'])}
- Priority score min/median/max: {summary['score_min']:.3f} / {summary['score_median']:.3f} / {summary['score_max']:.3f}
- Population min/median/max: {summary['population_min']:,} / {summary['population_median']:,} / {summary['population_max']:,}

The lane is a source-discovery scheduling artifact. It does not represent a dry run,
live attempt, verified source, accounting change, or research finding.
"""


def live_command(
    round_id: str, lane_number: int, input_path: Path, rows_per_lane: int
) -> str:
    output_dir = (
        f"tmp/parallel_scout_rounds/{round_id}/"
        f"lane_{lane_number}_live_direct_sdk_attempt1"
    )
    return f"""python scripts/gabriel_state_source_scout.py \\
  --live \\
  --live-backend direct-sdk \\
  --state ALL \\
  --allow-mixed-states \\
  --municipalities-csv {relative(input_path)} \\
  --output-dir {output_dir} \\
  --prompt-mode compact \\
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \\
  --model gpt-5.4-nano \\
  --search-context-size low \\
  --max-prompts {rows_per_lane} \\
  --live-hard-cap {rows_per_lane} \\
  --n-parallels 1 \\
  --sleep-between-prompts 5 \\
  --adaptive-sleep \\
  --adaptive-sleep-min 3 \\
  --adaptive-sleep-base 5 \\
  --adaptive-sleep-max 15 \\
  --adaptive-sleep-backoff 10 \\
  --adaptive-sleep-stability-window 25 \\
  --adaptive-sleep-failure-window 2 \\
  --timeout 90 \\
  --direct-sdk-max-retries 0 \\
  --cost-log-path {output_dir}/batch_cost_log.csv \\
  --candidate-export-dir {output_dir}/candidate_exports"""


def commands_text(
    round_id: str,
    lane_paths: list[Path],
    rows_per_lane: int,
    stagger_seconds: int,
) -> str:
    if rows_per_lane != 150:
        cap_note = (
            f"Generated commands use the requested locked {rows_per_lane}-row cap; "
            "this nonstandard size requires separate review before live authorization."
        )
    else:
        cap_note = "Generated commands use the exact locked 150-row cap."
    sections = []
    for lane_number, lane_path in enumerate(lane_paths, start=1):
        sections.append(
            f"""## Lane {lane_number}

Fresh output:
`tmp/parallel_scout_rounds/{round_id}/lane_{lane_number}_live_direct_sdk_attempt1`

```bash
{live_command(round_id, lane_number, lane_path, rows_per_lane)}
```
"""
        )
    stagger_minutes = stagger_seconds / 60
    return f"""# {round_id} — Lane Live Command Preview

**Preview only. Do not execute without separate live authorization.**

Before launching any lane, run the stronger preflight gate and require a complete
pass, including an explicitly authorized one-row production probe. Quarantine all
probe outputs from official accounting. {cap_note}

Launch lanes in numeric order. Wait exactly {stagger_seconds} seconds
({stagger_minutes:g} minutes) between starts, confirming the active lanes have not
shown an immediate widespread transport or lifecycle failure before starting the
next lane. Do not run more lanes than the round authorization permits. Stop all
lanes if a widespread transport failure, systematic parser failure, artifact loss,
protected-file mutation, or secret exposure appears.

Each command remains internally serialized with `--n-parallels 1`, uses compact
prompts, exact hints, adaptive pacing, the SDK plus outer 90-second deadline, and a
unique cost log. Timestamped candidate exports are redirected to each lane's
`candidate_exports/` directory; `parsed_candidates.csv` remains at the lane output
root. Lane processes must not rebuild queue/coverage/yield/dashboard, edit final
project docs, or commit. Preserve every artifact.

{''.join(sections)}
## After processes terminate

Run the offline lane auditor against `parallel_round_manifest.json`. Do not run any
national builder or merge command from this file.
"""


def dry_run_command(
    lane_number: int, input_path: Path, rows_per_lane: int, round_id: str
) -> str:
    output_dir = (
        f"tmp/parallel_scout_rounds/{round_id}/"
        f"lane_{lane_number}_dry_run_attempt1"
    )
    return f"""python scripts/gabriel_state_source_scout.py \\
  --dry-run \\
  --state ALL \\
  --allow-mixed-states \\
  --municipalities-csv {relative(input_path)} \\
  --output-dir {output_dir} \\
  --prompt-mode compact \\
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \\
  --live-hard-cap {rows_per_lane} \\
  --sleep-between-prompts 5 \\
  --adaptive-sleep \\
  --adaptive-sleep-min 3 \\
  --adaptive-sleep-base 5 \\
  --adaptive-sleep-max 15 \\
  --adaptive-sleep-backoff 10 \\
  --adaptive-sleep-stability-window 25 \\
  --adaptive-sleep-failure-window 2"""


def dry_commands_text(
    round_id: str, lane_paths: list[Path], rows_per_lane: int
) -> str:
    sections = []
    for lane_number, lane_path in enumerate(lane_paths, start=1):
        sections.append(
            f"""## Lane {lane_number}

```bash
{dry_run_command(lane_number, lane_path, rows_per_lane, round_id)}
```
"""
        )
    return f"""# {round_id} — Lane Dry-Run Command Preview

**Offline previews only. These commands make no backend call.**

Run and audit every lane dry-run before any separately authorized live collection.
Require exact row counts, compact prompts, complete hints, adaptive metadata, and
locked identities. Candidate-export routing applies only to completed live runs.

{''.join(sections)}"""


def merge_handoff_text(round_id: str, manifest_path: Path) -> str:
    return f"""# {round_id} — Post-Lane Merge Handoff

This handoff is a future coordinator boundary, not merge authorization.

1. Preserve every lane output and prove the locked input hashes against
   `{relative(manifest_path)}`.
2. Run:

   ```bash
   python scripts/audit_parallel_scout_lanes.py \\
     --manifest {relative(manifest_path)} \\
     --output-dir tmp/parallel_scout_rounds/{round_id}/post_lane_audit
   ```

3. Review lane classifications, parseable/failure/stopped/candidate counts, completed
   ID overlap, and `merge_recommendation.md`.
4. If the recommendation is `merge_all_lanes`, stop and obtain authorization for the
   separate serial accounting task.
5. If it is `merge_completed_lanes_only_with_user_approval`, do not merge until the
   user explicitly accepts the changed round scope.
6. If it is `do_not_merge_until_resume_or_review`, preserve all artifacts and resolve
   lane lineage before accounting.

The auditor never runs shared builders. A later serial merge may rebuild queue and
coverage exactly once, then refresh yield learning and dashboard/project-phase JSON.
No lane independently commits or edits shared accounting.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES))
    parser.add_argument("--num-lanes", type=int)
    parser.add_argument("--rows-per-lane", type=int)
    stagger = parser.add_mutually_exclusive_group()
    stagger.add_argument("--stagger-minutes", type=float)
    stagger.add_argument("--lane-start-stagger-seconds", type=int)
    parser.add_argument("--allow-oversized-lanes", action="store_true")
    parser.add_argument("--existing-lane-input")
    parser.add_argument(
        "--priority-targets-csv", default=str(DEFAULT_PRIORITY_TARGETS)
    )
    parser.add_argument("--priority-tiers-csv", default=str(DEFAULT_PRIORITY_TIERS))
    parser.add_argument("--coverage-csv", default=str(DEFAULT_COVERAGE))
    parser.add_argument("--failure-retry-csv", default=str(DEFAULT_FAILURES))
    parser.add_argument("--search-hints-csv", default=str(DEFAULT_HINTS))
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_defaults = PROFILES.get(
        args.profile,
        {"num_lanes": 2, "rows_per_lane": 150, "stagger_seconds": 180},
    )
    explicit_overrides = {
        "num_lanes": args.num_lanes is not None,
        "rows_per_lane": args.rows_per_lane is not None,
        "stagger": (
            args.stagger_minutes is not None
            or args.lane_start_stagger_seconds is not None
        ),
    }
    args.num_lanes = (
        args.num_lanes
        if args.num_lanes is not None
        else profile_defaults["num_lanes"]
    )
    args.rows_per_lane = (
        args.rows_per_lane
        if args.rows_per_lane is not None
        else profile_defaults["rows_per_lane"]
    )
    if args.stagger_minutes is not None:
        stagger_seconds = round(args.stagger_minutes * 60)
    elif args.lane_start_stagger_seconds is not None:
        stagger_seconds = args.lane_start_stagger_seconds
    else:
        stagger_seconds = profile_defaults["stagger_seconds"]
    if not 1 <= args.num_lanes <= 3:
        raise SystemExit("--num-lanes must be between 1 and 3")
    if args.rows_per_lane < 1:
        raise SystemExit("--rows-per-lane must be positive")
    if args.rows_per_lane > 300 and not args.allow_oversized_lanes:
        raise SystemExit(
            "--rows-per-lane above 300 requires --allow-oversized-lanes"
        )
    if stagger_seconds < 0:
        raise SystemExit("lane start stagger must be nonnegative")
    if not args.plan_only:
        raise SystemExit(
            "This offline framework currently requires --plan-only; generated "
            "commands are previews and are never executed."
        )

    output_dir = resolve_path(args.output_dir)
    priority_targets_path = resolve_path(args.priority_targets_csv)
    priority_tiers_path = resolve_path(args.priority_tiers_csv)
    coverage_path = resolve_path(args.coverage_csv)
    failures_path = resolve_path(args.failure_retry_csv)
    hints_path = resolve_path(args.search_hints_csv)
    existing_path = (
        resolve_path(args.existing_lane_input) if args.existing_lane_input else None
    )
    required = [
        priority_targets_path,
        priority_tiers_path,
        coverage_path,
        failures_path,
        hints_path,
    ] + ([existing_path] if existing_path else [])
    missing = [str(path) for path in required if path is not None and not path.is_file()]
    if missing:
        raise SystemExit("Missing required input: " + ", ".join(missing))

    expected_names = set(OUTPUT_NAMES)
    for number in range(1, args.num_lanes + 1):
        expected_names.update({f"lane_{number}_input.csv", f"lane_{number}_input_audit.md"})
    if output_dir.exists():
        unexpected = sorted(
            path.name for path in output_dir.iterdir() if path.name not in expected_names
        )
        if unexpected:
            raise SystemExit(
                "Output directory contains unexpected files; refusing to mix plans: "
                + ", ".join(unexpected)
            )
    else:
        output_dir.mkdir(parents=True)

    priority_rows = read_csv(priority_tiers_path)
    priority_by_id = ensure_unique_index(
        priority_rows, "municipality_id", "full priority table"
    )
    coverage_rows = read_csv(coverage_path)
    coverage_by_id = ensure_unique_index(
        coverage_rows, "municipality_id", "coverage table"
    )
    failure_rows = read_csv(failures_path)
    failure_ids = {row["municipality_id"] for row in failure_rows}
    hints_rows = read_csv(hints_path)
    hints_by_id = ensure_unique_index(hints_rows, "municipality_id", "search hints")
    target_rows = read_csv(priority_targets_path)

    if existing_path:
        existing_rows = read_csv(existing_path)
        fields = list(existing_rows[0])
        if (
            existing_path.name
            == "post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv"
            and sha256(existing_path) != EXPECTED_POST_PI_WAVE1_HASH
        ):
            raise SystemExit("Existing Post-PI Wave 1 input hash does not match lock")
    else:
        existing_rows = []
        fields = [
            "post_pi_wave_rank",
            "original_priority_rank",
            "post_pi_wave_id",
            "worker_batch",
            "worker_batch_row",
            "future_live_queue_id",
        ] + list(priority_rows[0]) + [
            "source_priority_file",
            "source_priority_commit",
            "search_hints_available",
            "search_hint_1",
            "search_hint_2",
            "search_hint_3",
            "search_hint_4",
            "search_hint_5",
            "expected_units_to_search",
            "verification_notes",
            "recommended_scout_status",
            "worker_id",
            "worker_state_scope",
            "worker_rank_min",
            "worker_rank_max",
            "worker_assignment_method",
        ]
        fields = list(dict.fromkeys(fields))

    required_lane_fields = {
        "municipality_id",
        "census_gov_id",
        "state",
        "municipality",
        "government_name",
        "government_type",
        "geography_type",
        "population",
        "total_priority_score",
        "priority_tier",
        "priority_confidence",
        "retry_flag",
        "failure_only_flag",
        "scout_coverage_status",
        "future_scout_eligible_flag",
        "already_canonical_flag",
        *(f"search_hint_{index}" for index in range(1, 6)),
    }
    missing_fields = sorted(required_lane_fields - set(fields))
    if missing_fields:
        raise SystemExit("Lane schema is missing required fields: " + ", ".join(missing_fields))

    lanes: list[list[dict[str, str]]] = []
    lane_copied_unchanged: list[bool] = []
    selected_ids: set[str] = set()
    selected_census: set[str] = set()
    lane_paths: list[Path] = []

    if existing_path:
        validate_lane_rows(
            existing_rows,
            expected_count=args.rows_per_lane,
            lane_id="lane_1",
            priority_by_id=priority_by_id,
            coverage_by_id=coverage_by_id,
            failure_ids=failure_ids,
            hints_by_id=hints_by_id,
        )
        lanes.append(existing_rows)
        lane_copied_unchanged.append(True)
        selected_ids.update(row["municipality_id"] for row in existing_rows)
        selected_census.update(
            row["census_gov_id"] for row in existing_rows if row["census_gov_id"]
        )

    target_order: list[dict[str, str]] = []
    target_ids: set[str] = set()
    for target in sorted(target_rows, key=lambda row: int(row["rank"])):
        municipality_id = target["municipality_id"]
        if municipality_id not in priority_by_id:
            raise SystemExit(f"Top target missing from full priority data: {municipality_id}")
        current = dict(priority_by_id[municipality_id])
        current["_target_rank"] = target["rank"]
        target_order.append(current)
        target_ids.add(municipality_id)
    target_order.extend(
        row
        for row in sorted(priority_rows, key=full_priority_sort_key)
        if row["municipality_id"] not in target_ids
    )

    next_lane_number = len(lanes) + 1
    while len(lanes) < args.num_lanes:
        selected: list[dict[str, str]] = []
        for candidate in target_order:
            municipality_id = candidate["municipality_id"]
            census_id = candidate["census_gov_id"]
            if municipality_id in selected_ids:
                continue
            if census_id and census_id in selected_census:
                continue
            failures = eligibility_failures(
                candidate, coverage_by_id[municipality_id], failure_ids
            )
            if failures:
                continue
            selected.append(candidate)
            selected_ids.add(municipality_id)
            if census_id:
                selected_census.add(census_id)
            if len(selected) == args.rows_per_lane:
                break
        if len(selected) != args.rows_per_lane:
            raise SystemExit(
                f"Only {len(selected)} ordinary eligible rows available for "
                f"lane_{next_lane_number}; no substitutions were made"
            )
        lane_rows = [
            build_selected_lane_row(
                source=row,
                hint=hints_by_id[row["municipality_id"]],
                round_id=args.round_id,
                lane_number=next_lane_number,
                lane_rank=index,
                rows_per_lane=args.rows_per_lane,
                priority_targets_path=priority_targets_path,
                fields=fields,
            )
            for index, row in enumerate(selected, start=1)
        ]
        validate_lane_rows(
            lane_rows,
            expected_count=args.rows_per_lane,
            lane_id=f"lane_{next_lane_number}",
            priority_by_id=priority_by_id,
            coverage_by_id=coverage_by_id,
            failure_ids=failure_ids,
            hints_by_id=hints_by_id,
        )
        lanes.append(lane_rows)
        lane_copied_unchanged.append(False)
        next_lane_number += 1

    all_municipality_ids = [
        row["municipality_id"] for lane_rows in lanes for row in lane_rows
    ]
    if len(all_municipality_ids) != len(set(all_municipality_ids)):
        raise SystemExit("Duplicate municipality IDs detected across lanes")
    all_census_ids = [
        row["census_gov_id"]
        for lane_rows in lanes
        for row in lane_rows
        if row["census_gov_id"]
    ]
    if len(all_census_ids) != len(set(all_census_ids)):
        raise SystemExit("Duplicate nonblank Census IDs detected across lanes")

    for lane_number, lane_rows in enumerate(lanes, start=1):
        lane_path = output_dir / f"lane_{lane_number}_input.csv"
        if lane_number == 1 and existing_path:
            lane_path.write_bytes(existing_path.read_bytes())
        else:
            write_csv(lane_path, lane_rows, fields)
        lane_paths.append(lane_path)
        reparsed = read_csv(lane_path)
        if reparsed != lane_rows:
            raise SystemExit(f"Lane {lane_number} did not reproduce after write")
        write_text(
            output_dir / f"lane_{lane_number}_input_audit.md",
            lane_audit_text(
                round_id=args.round_id,
                lane_id=f"Lane {lane_number}",
                lane_path=lane_path,
                rows=lane_rows,
                copied_unchanged=lane_copied_unchanged[lane_number - 1],
            ),
        )

    manifest_lanes = []
    for number, (lane_path, lane_rows) in enumerate(zip(lane_paths, lanes), start=1):
        output_path = (
            f"tmp/parallel_scout_rounds/{args.round_id}/"
            f"lane_{number}_live_direct_sdk_attempt1"
        )
        manifest_lanes.append(
            {
                "lane_id": f"lane_{number}",
                "input_csv": relative(lane_path),
                "input_sha256": sha256(lane_path),
                "row_count": len(lane_rows),
                "copied_existing_input_byte_for_byte": lane_copied_unchanged[number - 1],
                "state_distribution": distribution(lane_rows, "state"),
                "priority_tier_distribution": distribution(lane_rows, "priority_tier"),
                "live_output_dir": output_path,
                "cost_log_path": f"{output_path}/batch_cost_log.csv",
                "candidate_export_dir": f"{output_path}/candidate_exports",
                "candidate_export_policy": "lane_local_required_when_parseable",
                "planned_start_offset_seconds": (number - 1) * stagger_seconds,
                "live_status": "planned_not_run",
            }
        )
    manifest_path = output_dir / "parallel_round_manifest.json"
    manifest = {
        "schema_version": "2.0.0",
        "round_id": args.round_id,
        "parallel_mode_status": "planned_not_run",
        "planning_mode": "plan_only_offline",
        "external_calls_performed": 0,
        "profile": args.profile or "legacy_default_2x150",
        "profile_defaults": profile_defaults,
        "explicit_profile_overrides": explicit_overrides,
        "allow_oversized_lanes": args.allow_oversized_lanes,
        "num_lanes": args.num_lanes,
        "rows_per_lane": args.rows_per_lane,
        "total_planned_rows": args.num_lanes * args.rows_per_lane,
        "supported_lanes_initial": 2,
        "supported_lanes_current": 3,
        "supported_lanes_future": 3,
        "maximum_rows_per_lane_without_override": 300,
        "planner_baseline_commit": PLANNER_BASELINE_COMMIT,
        "source_files": {
            "priority_targets": {
                "path": relative(priority_targets_path),
                "sha256": sha256(priority_targets_path),
            },
            "priority_tiers": {
                "path": relative(priority_tiers_path),
                "sha256": sha256(priority_tiers_path),
            },
            "coverage": {
                "path": relative(coverage_path),
                "sha256": sha256(coverage_path),
            },
            "failure_retry": {
                "path": relative(failures_path),
                "sha256": sha256(failures_path),
            },
            "search_hints": {
                "path": relative(hints_path),
                "sha256": sha256(hints_path),
            },
        },
        "lanes": manifest_lanes,
        "cross_lane_checks": {
            "unique_municipality_ids": len(set(all_municipality_ids)),
            "duplicate_municipality_ids": [],
            "unique_nonblank_census_ids": len(set(all_census_ids)),
            "duplicate_nonblank_census_ids": [],
            "missing_census_ids": sum(
                not bool(row["census_gov_id"])
                for lane_rows in lanes
                for row in lane_rows
            ),
            "search_hints_complete": sum(
                all(row.get(f"search_hint_{index}", "") for index in range(1, 6))
                for lane_rows in lanes
                for row in lane_rows
            ),
        },
        "required_live_controls": {
            "live_backend": "direct-sdk",
            "prompt_mode": "compact",
            "search_hints": True,
            "adaptive_sleep": True,
            "adaptive_sleep_min_base_max_backoff": [3, 5, 15, 10],
            "adaptive_sleep_stability_failure_windows": [25, 2],
            "timeout_seconds_inner_and_outer": 90,
            "direct_sdk_max_retries": 0,
            "n_parallels_per_lane": 1,
            "lane_start_stagger_seconds": stagger_seconds,
            "lane_start_stagger_minutes": stagger_seconds / 60,
            "candidate_export_policy": "lane_local_required_when_parseable",
        },
        "accounting_policy": "serial_merge_after_lane_audit",
        "lane_process_prohibitions": [
            "no queue or coverage rebuild",
            "no yield or dashboard refresh",
            "no project documentation update",
            "no commit",
        ],
        "caveat": "No parallel live scout or dry run has been executed.",
    }
    write_json(manifest_path, manifest)

    combined_states = distribution(
        [row for lane_rows in lanes for row in lane_rows], "state"
    )
    audit = f"""# {args.round_id} — Parallel Round Input Audit

Disposition: **PASS — {args.num_lanes} offline lane inputs locked; no live or dry run executed.**

- Lanes: {args.num_lanes}
- Rows per lane: {args.rows_per_lane}
- Profile: `{args.profile or 'legacy_default_2x150'}`
- Lane-start stagger: {stagger_seconds} seconds ({stagger_seconds / 60:g} minutes)
- Total planned rows: {len(all_municipality_ids)}
- Unique municipality IDs: {len(set(all_municipality_ids))}
- Municipality overlap: 0
- Unique nonblank Census IDs: {len(set(all_census_ids))}
- Census-ID overlap: 0
- Missing Census IDs: {manifest['cross_lane_checks']['missing_census_ids']}
- Complete exact five-hint sets: {manifest['cross_lane_checks']['search_hints_complete']}/{len(all_municipality_ids)}
- Retry rows: 0
- Failure-only rows: 0
- Already-covered rows: 0
- Already-canonical rows: 0
- Combined states: {rendered_distribution(combined_states)}

## Locked lane files

"""
    for lane in manifest_lanes:
        audit += (
            f"- `{lane['lane_id']}`: {lane['row_count']} rows; "
            f"SHA-256 `{lane['input_sha256']}`; "
            f"states {rendered_distribution(lane['state_distribution'])}.\n"
        )
    existing_note = (
        "Lane 1 is the existing coordinator input copied byte-for-byte. "
        if existing_path
        else "All lanes were selected in one deterministic pass. "
    )
    audit += f"""

{existing_note}Additional lane rows are selected deterministically from current ranked targets,
then the full priority order if necessary, after exact current coverage, canonical,
failure/retry, government-category, prior selected-ID, and hint gates.
No ad hoc substitution occurred.

The generated commands are previews only. Shared national accounting remains
unchanged and must be rebuilt once, serially, only after a separate post-lane
audit and authorization.
"""
    write_text(output_dir / "parallel_round_input_audit.md", audit)
    write_text(
        output_dir / "lane_dry_run_commands.md",
        dry_commands_text(args.round_id, lane_paths, args.rows_per_lane),
    )
    write_text(
        output_dir / "lane_live_commands.md",
        commands_text(
            args.round_id, lane_paths, args.rows_per_lane, stagger_seconds
        ),
    )
    write_text(
        output_dir / "lane_merge_handoff.md",
        merge_handoff_text(args.round_id, manifest_path),
    )

    print(
        f"Prepared {args.num_lanes} offline lanes x {args.rows_per_lane} rows "
        f"for {args.round_id}; external calls=0"
    )
    for lane in manifest_lanes:
        print(
            f"{lane['lane_id']}: rows={lane['row_count']} "
            f"sha256={lane['input_sha256']}"
        )
    print(relative(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
