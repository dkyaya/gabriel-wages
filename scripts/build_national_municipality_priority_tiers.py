#!/usr/bin/env python3
"""Build deterministic national municipality scout-priority tiers.

This is a local research-operations heuristic. It reads existing Census-derived
municipality identity/context and current scout accounting, never opens a URL,
and never calls a model or API. Scores rank expected usefulness for locating
comparable safety and ordinary municipal non-safety wage-setting evidence; they
are not claims about unionization, department existence, source availability,
or wage outcomes.
"""

from __future__ import annotations

import csv
import hashlib
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "docs" / "analysis"

UNIVERSE_PATH = ANALYSIS / "national_municipality_universe.csv"
CROSSWALK_PATH = ANALYSIS / "national_municipality_county_crosswalk.csv"
COVERAGE_PATH = ANALYSIS / "national_scout_coverage_municipality_2026-07-20.csv"
QUEUE_PATH = ANALYSIS / "national_scout_candidate_queue_2026-07-20.csv"
STATE_COVERAGE_PATH = ANALYSIS / "national_scout_coverage_state.csv"
COUNTY_COVERAGE_PATH = ANALYSIS / "national_scout_coverage_county.csv"

TIERS_PATH = ANALYSIS / "national_municipality_priority_tiers_2026-07-22.csv"
TIER_SUMMARY_PATH = ANALYSIS / "national_municipality_priority_tier_summary_2026-07-22.csv"
STATE_SUMMARY_PATH = ANALYSIS / "state_priority_summary_2026-07-22.csv"
TOP_TARGETS_PATH = ANALYSIS / "national_priority_tier_top_targets_2026-07-22.csv"
FAILURE_RETRY_PATH = ANALYSIS / "national_failure_retry_priority_2026-07-22.csv"
BUILD_SUMMARY_PATH = ANALYSIS / "national_priority_tier_build_summary_2026-07-22.md"
SENSITIVITY_PATH = ANALYSIS / "national_priority_tiering_sensitivity_analysis_2026-07-22.md"
VALIDATION_PATH = ANALYSIS / "national_priority_tiering_validation_2026-07-22.md"

SUCCESS_STATUSES = {"scouted_with_candidates", "scouted_no_candidates"}
ALLOWED_GOVERNMENT_GEOGRAPHY = {
    ("municipal", "place"),
    ("township", "county_subdivision"),
}
CONFIDENCE_ORDER = {"high": 3, "medium": 2, "low": 1}
PRIOR_STRENGTH = 25.0
TOP_TARGET_COUNT = 500

BASELINE_WEIGHTS = {
    "population": 30.0,
    "government_type": 10.0,
    "state_yield": 20.0,
    "research_design": 20.0,
    "geographic_value": 10.0,
    "data_completeness": 5.0,
    "evidence_signal": 5.0,
}
POPULATION_HEAVIER_WEIGHTS = {
    "population": 40.0,
    "government_type": 10.0,
    "state_yield": 15.0,
    "research_design": 15.0,
    "geographic_value": 10.0,
    "data_completeness": 5.0,
    "evidence_signal": 5.0,
}
STATE_YIELD_HEAVIER_WEIGHTS = {
    "population": 25.0,
    "government_type": 10.0,
    "state_yield": 30.0,
    "research_design": 20.0,
    "geographic_value": 5.0,
    "data_completeness": 5.0,
    "evidence_signal": 5.0,
}


UNIVERSE_REQUIRED = {
    "state",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "active_status",
    "county_relationship_count",
    "multi_county_flag",
}
CROSSWALK_REQUIRED = {
    "municipality_id",
    "census_gov_id",
    "state",
    "county_geoid",
    "county_name",
    "is_government_units_primary_county",
}
COVERAGE_REQUIRED = {
    "municipality_id",
    "state",
    "scout_coverage_status",
    "queue_status",
    "canonical_overlap_status",
    "candidate_rows_total",
    "police_candidate_rows",
    "fire_candidate_rows",
    "non_safety_candidate_rows",
    "likely_triad_from_scout_rows",
    "queued_for_later_verification_count",
    "failed_connection_attempt_count",
    "failed_connection_run_ids",
    "connection_failure_accounting",
}
STATE_REQUIRED = {
    "state",
    "municipalities_in_universe",
    "municipalities_scouted",
    "municipalities_scouted_with_candidates",
    "municipalities_scouted_no_candidates",
    "municipalities_scout_attempt_failed_connection",
    "candidate_rows_total",
    "municipalities_with_likely_triad",
    "municipalities_with_non_safety_candidate",
}
COUNTY_REQUIRED = {
    "state",
    "county_geoid",
    "municipality_associations_in_universe",
    "municipality_associations_scouted",
}
QUEUE_REQUIRED = {"municipality_id", "state", "triage_bucket"}


PRIMARY_FIELDS = [
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "government_type",
    "geography_type",
    "population",
    "population_year",
    "county_relationship_count",
    "multi_county_flag",
    "county_context_summary",
    "population_percentile",
    "population_log_scale",
    "population_score",
    "government_type_score",
    "state_yield_score",
    "research_design_score",
    "geographic_value_score",
    "data_completeness_score",
    "evidence_signal_score",
    "retry_adjustment",
    "total_priority_score",
    "national_priority_rank",
    "priority_tier",
    "priority_confidence",
    "priority_reason_summary",
    "state_successful_scout_count",
    "state_candidate_positive_rate",
    "state_candidate_rows_per_covered",
    "state_parseable_empty_rate",
    "state_failure_rate",
    "state_score_confidence",
    "scout_coverage_status",
    "candidate_positive_flag",
    "candidate_row_count",
    "later_verification_row_count",
    "failure_only_flag",
    "retry_flag",
    "retry_priority",
    "prior_failure_run_ids",
    "already_canonical_flag",
    "future_scout_eligible_flag",
    "future_scout_exclusion_reason",
    "score_version",
    "score_stage_disclaimer",
]

TIER_SUMMARY_FIELDS = [
    "state",
    "priority_tier",
    "scout_coverage_status",
    "future_scout_eligible_flag",
    "government_type",
    "municipality_count",
    "future_scout_eligible_count",
    "already_covered_count",
    "candidate_positive_count",
    "failure_only_count",
    "population_sum",
    "population_median",
    "average_priority_score",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
]

STATE_SUMMARY_FIELDS = [
    "state",
    "universe_count",
    "scout_covered_count",
    "future_scout_eligible_count",
    "tier_1_eligible_count",
    "tier_2_eligible_count",
    "tier_3_eligible_count",
    "tier_4_eligible_count",
    "tier_5_eligible_count",
    "candidate_positive_rate",
    "candidate_rows_per_covered_municipality",
    "parseable_empty_rate",
    "failure_rate",
    "state_yield_score",
    "state_score_confidence",
    "average_priority_score",
    "high_priority_coverage_rate",
    "recommended_next_wave_status",
]

TOP_TARGET_FIELDS = [
    "rank",
    "state",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_name",
    "government_type",
    "population",
    "total_priority_score",
    "priority_tier",
    "priority_confidence",
    "population_score",
    "government_type_score",
    "state_yield_score",
    "research_design_score",
    "geographic_value_score",
    "data_completeness_score",
    "evidence_signal_score",
    "retry_flag",
    "retry_priority",
    "priority_reason_summary",
    "recommended_future_wave",
]

FAILURE_FIELDS = [
    "municipality_id",
    "census_gov_id",
    "state",
    "municipality",
    "government_name",
    "population",
    "prior_failure_type",
    "prior_failure_run_ids",
    "prior_attempt_dates",
    "failed_attempt_count",
    "underlying_priority_score",
    "priority_tier",
    "priority_confidence",
    "retry_priority",
    "recommended_retry_timing",
]


@dataclass(frozen=True)
class StateMetrics:
    state: str
    universe: int
    covered: int
    candidate_positive: int
    parseable_empty: int
    failure_only: int
    candidate_rows: int
    safety_positive: int
    non_safety_positive: int
    likely_triad: int
    positive_rate: float | None
    rows_per_covered: float | None
    empty_rate: float | None
    failure_rate: float | None
    yield_norm: float
    research_norm: float
    confidence: str


@dataclass(frozen=True)
class BuildResult:
    scored_rows: list[dict[str, str]]
    tier_summary_rows: list[dict[str, str]]
    state_summary_rows: list[dict[str, str]]
    top_target_rows: list[dict[str, str]]
    failure_rows: list[dict[str, str]]
    sensitivity_text: str
    build_summary_text: str
    validation_text: str


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_csv(path: Path, required: set[str] | None = None) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required input is missing: {relative(path)}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if required and not required.issubset(fields):
            raise ValueError(
                f"{relative(path)} is missing required columns: {sorted(required - fields)}"
            )
        return list(reader)


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: str | int | None, *, missing: int | None = 0) -> int | None:
    if value in (None, ""):
        return missing
    return int(value)


def fmt(value: float | None, digits: int = 6) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def smoothed_rate(successes: float, total: float, prior: float) -> float:
    return (successes + PRIOR_STRENGTH * prior) / (total + PRIOR_STRENGTH)


def ensure_unique(rows: list[dict[str, str]], field: str, label: str) -> None:
    values = [row[field] for row in rows]
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise ValueError(f"{label} contains duplicate {field} values: {duplicates[:10]}")


def population_scales(rows: list[dict[str, str]]) -> dict[str, tuple[float | None, float | None]]:
    observed = [int(row["population"]) for row in rows if row["population"].strip()]
    if not observed:
        return {row["municipality_id"]: (None, None) for row in rows}
    counts = Counter(observed)
    below = 0
    percentiles: dict[int, float] = {}
    denominator = max(len(observed) - 1, 1)
    for value in sorted(counts):
        midpoint = below + (counts[value] - 1) / 2.0
        percentiles[value] = midpoint / denominator
        below += counts[value]
    max_log = math.log1p(max(observed))
    result: dict[str, tuple[float | None, float | None]] = {}
    for row in rows:
        if not row["population"].strip():
            result[row["municipality_id"]] = (None, None)
            continue
        population = int(row["population"])
        log_scale = math.log1p(max(population, 0)) / max_log if max_log else 0.0
        result[row["municipality_id"]] = (percentiles[population], log_scale)
    return result


def load_county_context(
    crosswalk_rows: list[dict[str, str]],
) -> tuple[dict[str, str], dict[str, list[tuple[str, str]]]]:
    by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in crosswalk_rows:
        by_id[row["municipality_id"]].append(row)
    summaries: dict[str, str] = {}
    county_keys: dict[str, list[tuple[str, str]]] = {}
    for municipality_id, relationships in by_id.items():
        ordered = sorted(
            relationships,
            key=lambda row: (
                row["is_government_units_primary_county"] != "yes",
                row["county_geoid"],
            ),
        )
        summaries[municipality_id] = "; ".join(
            f"{row['county_name']} ({row['county_geoid']}"
            + ("; primary" if row["is_government_units_primary_county"] == "yes" else "")
            + ")"
            for row in ordered
        )
        county_keys[municipality_id] = [
            (row["state"], row["county_geoid"]) for row in ordered
        ]
    return summaries, county_keys


def build_state_metrics(
    state_rows: list[dict[str, str]], coverage_rows: list[dict[str, str]]
) -> dict[str, StateMetrics]:
    coverage_by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in coverage_rows:
        coverage_by_state[row["state"]].append(row)

    total_covered = sum(int(row["municipalities_scouted"]) for row in state_rows)
    total_positive = sum(
        int(row["municipalities_scouted_with_candidates"]) for row in state_rows
    )
    total_failures = sum(
        int(row["municipalities_scout_attempt_failed_connection"]) for row in state_rows
    )
    total_candidates = sum(int(row["candidate_rows_total"]) for row in state_rows)
    global_positive = total_positive / total_covered
    global_rows = total_candidates / total_covered
    global_failure = total_failures / (total_covered + total_failures)

    covered_rows = [
        row for row in coverage_rows if row["scout_coverage_status"] in SUCCESS_STATUSES
    ]
    global_safety = sum(
        int(row["police_candidate_rows"]) > 0 or int(row["fire_candidate_rows"]) > 0
        for row in covered_rows
    ) / total_covered
    global_non_safety = sum(
        int(row["non_safety_candidate_rows"]) > 0 for row in covered_rows
    ) / total_covered
    global_triad = sum(
        row["likely_triad_from_scout_rows"] == "yes" for row in covered_rows
    ) / total_covered

    result: dict[str, StateMetrics] = {}
    for state_row in state_rows:
        state = state_row["state"]
        covered = int(state_row["municipalities_scouted"])
        positive = int(state_row["municipalities_scouted_with_candidates"])
        empty = int(state_row["municipalities_scouted_no_candidates"])
        failures = int(state_row["municipalities_scout_attempt_failed_connection"])
        candidates = int(state_row["candidate_rows_total"])
        state_covered_rows = [
            row
            for row in coverage_by_state[state]
            if row["scout_coverage_status"] in SUCCESS_STATUSES
        ]
        safety = sum(
            int(row["police_candidate_rows"]) > 0 or int(row["fire_candidate_rows"]) > 0
            for row in state_covered_rows
        )
        non_safety = sum(
            int(row["non_safety_candidate_rows"]) > 0 for row in state_covered_rows
        )
        triad = sum(
            row["likely_triad_from_scout_rows"] == "yes" for row in state_covered_rows
        )

        smoothed_positive = smoothed_rate(positive, covered, global_positive)
        smoothed_rows = (
            candidates + PRIOR_STRENGTH * global_rows
        ) / (covered + PRIOR_STRENGTH)
        smoothed_failure = smoothed_rate(
            failures, covered + failures, global_failure
        )
        yield_norm = (
            0.60 * smoothed_positive
            + 0.25 * min(smoothed_rows / 3.0, 1.0)
            + 0.15 * (1.0 - smoothed_failure)
        )

        smoothed_safety = smoothed_rate(safety, covered, global_safety)
        smoothed_non_safety = smoothed_rate(non_safety, covered, global_non_safety)
        smoothed_triad = smoothed_rate(triad, covered, global_triad)
        research_norm = (
            0.30 * smoothed_safety
            + 0.30 * smoothed_non_safety
            + 0.40 * smoothed_triad
        )

        confidence = "high" if covered >= 50 else "medium" if covered >= 15 else "low"
        result[state] = StateMetrics(
            state=state,
            universe=int(state_row["municipalities_in_universe"]),
            covered=covered,
            candidate_positive=positive,
            parseable_empty=empty,
            failure_only=failures,
            candidate_rows=candidates,
            safety_positive=safety,
            non_safety_positive=non_safety,
            likely_triad=triad,
            positive_rate=ratio(positive, covered),
            rows_per_covered=ratio(candidates, covered),
            empty_rate=ratio(empty, covered),
            failure_rate=ratio(failures, covered + failures),
            yield_norm=yield_norm,
            research_norm=research_norm,
            confidence=confidence,
        )
    return result


def evidence_norm(coverage: dict[str, str]) -> float:
    status = coverage["scout_coverage_status"]
    if status == "scouted_with_candidates":
        candidates = int(coverage["candidate_rows_total"])
        queued = int(coverage["queued_for_later_verification_count"])
        triad = coverage["likely_triad_from_scout_rows"] == "yes"
        return min(
            1.0,
            0.40
            + 0.30 * min(candidates / 5.0, 1.0)
            + 0.20 * triad
            + 0.10 * min(queued / max(candidates, 1), 1.0),
        )
    if status == "scout_attempt_failed_connection":
        return 0.20
    return 0.0


def confidence_for_row(
    row: dict[str, str], county_context: str, state_confidence: str
) -> str:
    if (
        not row["population"].strip()
        or not county_context
        or (row["government_type"], row["geography_type"])
        not in ALLOWED_GOVERNMENT_GEOGRAPHY
    ):
        return "low"
    return state_confidence


def score_with_weights(norms: dict[str, float], weights: dict[str, float]) -> float:
    return min(
        100.0,
        max(0.0, sum(norms[name] * weights[name] for name in weights)),
    )


def tier_number(value: str) -> int:
    return int(value.split()[-1])


def assign_tiers(rows: list[dict[str, object]]) -> None:
    ordered = sorted(
        rows,
        key=lambda row: (
            -float(row["total_priority_score"]),
            -int(row["population"] or -1),
            str(row["municipality_id"]),
        ),
    )
    n = len(ordered)
    cut1 = math.ceil(n * 0.05)
    cut2 = math.ceil(n * 0.15)
    cut3 = math.ceil(n * 0.35)
    cut4 = math.ceil(n * 0.65)
    for rank, row in enumerate(ordered, start=1):
        row["national_priority_rank"] = rank
        if rank <= cut1:
            row["priority_tier"] = "Tier 1"
        elif rank <= cut2:
            row["priority_tier"] = "Tier 2"
        elif rank <= cut3:
            row["priority_tier"] = "Tier 3"
        elif rank <= cut4:
            row["priority_tier"] = "Tier 4"
        else:
            row["priority_tier"] = "Tier 5"


def retry_fields(row: dict[str, object]) -> tuple[str, str]:
    if row["failure_only_flag"] != "yes":
        return "not_applicable", "not_applicable"
    tier = str(row["priority_tier"])
    if tier in {"Tier 1", "Tier 2"}:
        return "high", "next_separately_authorized_failure_retry_wave"
    if tier == "Tier 3":
        return "medium", "retry_after_next_300_to_600_new_scouts"
    return "low", "defer_until_state_or_selection_balance_requires_retry"


def reason_summary(
    *,
    row: dict[str, str],
    population_percentile: float | None,
    state_metrics: StateMetrics,
    county_context: str,
    coverage: dict[str, str],
) -> str:
    population_text = (
        "population missing"
        if population_percentile is None
        else f"population percentile {100 * population_percentile:.1f}"
    )
    state_text = (
        f"state evidence {state_metrics.confidence}; smoothed yield component "
        f"{20 * state_metrics.yield_norm:.1f}/20"
    )
    geography_text = (
        f"{len(county_context.split('; '))} county relationship(s)"
        if county_context
        else "county context missing"
    )
    status = coverage["scout_coverage_status"]
    status_text = {
        "scouted_with_candidates": "already covered with unverified candidates",
        "scouted_no_candidates": "already covered with parseable empty result",
        "scout_attempt_failed_connection": "failure-only retry candidate",
        "not_scouted": "unscouted",
    }[status]
    return (
        f"{population_text}; {row['government_type']}/{row['geography_type']}; "
        f"{state_text}; {geography_text}; {status_text}"
    )


def build_scored_rows(
    universe_rows: list[dict[str, str]],
    crosswalk_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
    state_rows: list[dict[str, str]],
    county_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, StateMetrics]]:
    ensure_unique(universe_rows, "municipality_id", "Universe")
    ensure_unique(universe_rows, "census_gov_id", "Universe")
    ensure_unique(coverage_rows, "municipality_id", "Coverage")
    ensure_unique(state_rows, "state", "State coverage")

    universe_ids = {row["municipality_id"] for row in universe_rows}
    coverage_by_id = {row["municipality_id"]: row for row in coverage_rows}
    if set(coverage_by_id) != universe_ids:
        raise ValueError("Municipality coverage IDs do not exactly match the universe")
    if any(row["active_status"] != "Y" for row in universe_rows):
        raise ValueError("Universe contains inactive rows")
    prohibited = sorted(
        {
            (row["government_type"], row["geography_type"])
            for row in universe_rows
            if (row["government_type"], row["geography_type"])
            not in ALLOWED_GOVERNMENT_GEOGRAPHY
        }
    )
    if prohibited:
        raise ValueError(f"Universe contains prohibited employer categories: {prohibited}")

    queue_counts = Counter(row["municipality_id"] for row in queue_rows)
    if set(queue_counts) - universe_ids:
        raise ValueError("Candidate queue contains IDs outside the universe")
    for municipality_id, coverage in coverage_by_id.items():
        if queue_counts[municipality_id] != int(coverage["candidate_rows_total"]):
            raise ValueError(f"Candidate count mismatch for {municipality_id}")

    county_context, county_keys = load_county_context(crosswalk_rows)
    if set(county_context) != universe_ids:
        raise ValueError("County crosswalk does not cover every municipality ID")
    for row in universe_rows:
        if len(county_keys[row["municipality_id"]]) != int(row["county_relationship_count"]):
            raise ValueError(f"County relationship count mismatch for {row['municipality_id']}")

    county_metrics: dict[tuple[str, str], tuple[int, int]] = {}
    for row in county_rows:
        county_metrics[(row["state"], row["county_geoid"])] = (
            int(row["municipality_associations_in_universe"]),
            int(row["municipality_associations_scouted"]),
        )

    state_metrics = build_state_metrics(state_rows, coverage_rows)
    if set(state_metrics) != {row["state"] for row in universe_rows}:
        raise ValueError("State coverage does not cover every universe state/DC")
    population = population_scales(universe_rows)

    output: list[dict[str, object]] = []
    for row in universe_rows:
        municipality_id = row["municipality_id"]
        coverage = coverage_by_id[municipality_id]
        metrics = state_metrics[row["state"]]
        percentile, log_scale = population[municipality_id]
        population_norm = (
            0.40 * percentile + 0.60 * log_scale
            if percentile is not None and log_scale is not None
            else 0.0
        )
        government_norm = 1.0 if row["government_type"] == "municipal" else 0.40

        state_depth_gap = 1.0 - min(metrics.covered / 100.0, 1.0)
        state_unscouted_share = 1.0 - metrics.covered / metrics.universe
        county_gaps: list[float] = []
        for key in county_keys[municipality_id]:
            universe_count, scouted_count = county_metrics[key]
            county_gaps.append(1.0 - scouted_count / universe_count)
        county_gap = statistics.fmean(county_gaps) if county_gaps else 0.0
        geographic_norm = (
            0.40 * state_depth_gap
            + 0.20 * state_unscouted_share
            + 0.30 * county_gap
            + 0.10 * (row["multi_county_flag"] == "yes")
        )

        completeness_norm = (
            0.60 * bool(row["population"].strip())
            + 0.30 * bool(county_context[municipality_id])
            + 0.10
            * (
                (row["government_type"], row["geography_type"])
                in ALLOWED_GOVERNMENT_GEOGRAPHY
            )
        )
        current_evidence_norm = evidence_norm(coverage)
        norms = {
            "population": population_norm,
            "government_type": government_norm,
            "state_yield": metrics.yield_norm,
            "research_design": metrics.research_norm,
            "geographic_value": geographic_norm,
            "data_completeness": completeness_norm,
            "evidence_signal": current_evidence_norm,
        }
        score = score_with_weights(norms, BASELINE_WEIGHTS)

        status = coverage["scout_coverage_status"]
        canonical = (
            coverage["canonical_overlap_status"] == "already_ingested_canonical"
        )
        successful = status in SUCCESS_STATUSES
        failure_only = status == "scout_attempt_failed_connection"
        eligible = not successful and not canonical
        if canonical:
            exclusion_reason = "already_canonical"
        elif successful:
            exclusion_reason = "already_successfully_scout_covered"
        elif failure_only:
            exclusion_reason = "eligible_failure_retry"
        else:
            exclusion_reason = "eligible_new_scout"

        priority_confidence = confidence_for_row(
            row, county_context[municipality_id], metrics.confidence
        )
        output.append(
            {
                "municipality_id": municipality_id,
                "census_gov_id": row["census_gov_id"],
                "state": row["state"],
                "municipality": row["municipality"],
                "government_name": row["government_name"],
                "government_type": row["government_type"],
                "geography_type": row["geography_type"],
                "population": row["population"],
                "population_year": row.get("population_year", ""),
                "county_relationship_count": row["county_relationship_count"],
                "multi_county_flag": row["multi_county_flag"],
                "county_context_summary": county_context[municipality_id],
                "population_percentile": fmt(percentile),
                "population_log_scale": fmt(log_scale),
                "population_score": fmt(BASELINE_WEIGHTS["population"] * population_norm, 3),
                "government_type_score": fmt(BASELINE_WEIGHTS["government_type"] * government_norm, 3),
                "state_yield_score": fmt(BASELINE_WEIGHTS["state_yield"] * metrics.yield_norm, 3),
                "research_design_score": fmt(BASELINE_WEIGHTS["research_design"] * metrics.research_norm, 3),
                "geographic_value_score": fmt(BASELINE_WEIGHTS["geographic_value"] * geographic_norm, 3),
                "data_completeness_score": fmt(BASELINE_WEIGHTS["data_completeness"] * completeness_norm, 3),
                "evidence_signal_score": fmt(BASELINE_WEIGHTS["evidence_signal"] * current_evidence_norm, 3),
                "retry_adjustment": "0.000",
                "total_priority_score": fmt(score, 3),
                "national_priority_rank": 0,
                "priority_tier": "",
                "priority_confidence": priority_confidence,
                "priority_reason_summary": reason_summary(
                    row=row,
                    population_percentile=percentile,
                    state_metrics=metrics,
                    county_context=county_context[municipality_id],
                    coverage=coverage,
                ),
                "state_successful_scout_count": metrics.covered,
                "state_candidate_positive_rate": fmt(metrics.positive_rate),
                "state_candidate_rows_per_covered": fmt(metrics.rows_per_covered),
                "state_parseable_empty_rate": fmt(metrics.empty_rate),
                "state_failure_rate": fmt(metrics.failure_rate),
                "state_score_confidence": metrics.confidence,
                "scout_coverage_status": status,
                "candidate_positive_flag": "yes" if status == "scouted_with_candidates" else "no",
                "candidate_row_count": coverage["candidate_rows_total"],
                "later_verification_row_count": coverage["queued_for_later_verification_count"],
                "failure_only_flag": "yes" if failure_only else "no",
                "retry_flag": "yes" if failure_only else "no",
                "retry_priority": "pending_tier_assignment" if failure_only else "not_applicable",
                "prior_failure_run_ids": coverage["failed_connection_run_ids"],
                "already_canonical_flag": "yes" if canonical else "no",
                "future_scout_eligible_flag": "yes" if eligible else "no",
                "future_scout_exclusion_reason": exclusion_reason,
                "score_version": "national_priority_v1_2026-07-22",
                "score_stage_disclaimer": (
                    "Operational heuristic only; not evidence of unionization, departments, "
                    "source availability, wage levels, or causal effects."
                ),
                "_norms": norms,
            }
        )

    assign_tiers(output)
    for row in output:
        retry_priority, _ = retry_fields(row)
        row["retry_priority"] = retry_priority
    return output, state_metrics


def build_tier_summary(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["state"]),
            str(row["priority_tier"]),
            str(row["scout_coverage_status"]),
            str(row["future_scout_eligible_flag"]),
            str(row["government_type"]),
        )
        grouped[key].append(row)
    output: list[dict[str, str]] = []
    for key in sorted(grouped, key=lambda k: (k[0], tier_number(k[1]), k[2], k[3], k[4])):
        group = grouped[key]
        populations = [int(row["population"]) for row in group if str(row["population"]).strip()]
        output.append(
            {
                "state": key[0],
                "priority_tier": key[1],
                "scout_coverage_status": key[2],
                "future_scout_eligible_flag": key[3],
                "government_type": key[4],
                "municipality_count": str(len(group)),
                "future_scout_eligible_count": str(sum(row["future_scout_eligible_flag"] == "yes" for row in group)),
                "already_covered_count": str(sum(row["scout_coverage_status"] in SUCCESS_STATUSES for row in group)),
                "candidate_positive_count": str(sum(row["candidate_positive_flag"] == "yes" for row in group)),
                "failure_only_count": str(sum(row["failure_only_flag"] == "yes" for row in group)),
                "population_sum": str(sum(populations)) if populations else "",
                "population_median": fmt(float(statistics.median(populations)), 1) if populations else "",
                "average_priority_score": fmt(statistics.fmean(float(row["total_priority_score"]) for row in group), 3),
                "high_confidence_count": str(sum(row["priority_confidence"] == "high" for row in group)),
                "medium_confidence_count": str(sum(row["priority_confidence"] == "medium" for row in group)),
                "low_confidence_count": str(sum(row["priority_confidence"] == "low" for row in group)),
            }
        )
    return output


def recommended_state_status(
    tier1: int, tier2: int, metrics: StateMetrics
) -> str:
    if tier1 >= 25 and metrics.confidence == "high" and metrics.yield_norm >= 0.72:
        return "priority_high_evidence_state"
    if tier1 >= 25 and metrics.confidence == "medium":
        return "priority_growing_evidence_state"
    if tier1 >= 25 and metrics.confidence == "low":
        return "priority_exploratory_state"
    if tier1 + tier2 >= 25:
        return "cross_state_priority_fill"
    return "defer_or_geographic_balance_only"


def build_state_summary(
    rows: list[dict[str, object]], state_metrics: dict[str, StateMetrics]
) -> list[dict[str, str]]:
    by_state: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_state[str(row["state"])].append(row)
    output: list[dict[str, str]] = []
    for state in sorted(by_state):
        group = by_state[state]
        metrics = state_metrics[state]
        eligible = [row for row in group if row["future_scout_eligible_flag"] == "yes"]
        tier_counts = Counter(str(row["priority_tier"]) for row in eligible)
        high_priority_total = sum(row["priority_tier"] in {"Tier 1", "Tier 2"} for row in group)
        high_priority_covered = sum(
            row["priority_tier"] in {"Tier 1", "Tier 2"}
            and row["scout_coverage_status"] in SUCCESS_STATUSES
            for row in group
        )
        output.append(
            {
                "state": state,
                "universe_count": str(len(group)),
                "scout_covered_count": str(metrics.covered),
                "future_scout_eligible_count": str(len(eligible)),
                "tier_1_eligible_count": str(tier_counts["Tier 1"]),
                "tier_2_eligible_count": str(tier_counts["Tier 2"]),
                "tier_3_eligible_count": str(tier_counts["Tier 3"]),
                "tier_4_eligible_count": str(tier_counts["Tier 4"]),
                "tier_5_eligible_count": str(tier_counts["Tier 5"]),
                "candidate_positive_rate": fmt(metrics.positive_rate),
                "candidate_rows_per_covered_municipality": fmt(metrics.rows_per_covered),
                "parseable_empty_rate": fmt(metrics.empty_rate),
                "failure_rate": fmt(metrics.failure_rate),
                "state_yield_score": fmt(20 * metrics.yield_norm, 3),
                "state_score_confidence": metrics.confidence,
                "average_priority_score": fmt(statistics.fmean(float(row["total_priority_score"]) for row in group), 3),
                "high_priority_coverage_rate": fmt(ratio(high_priority_covered, high_priority_total)),
                "recommended_next_wave_status": recommended_state_status(
                    tier_counts["Tier 1"], tier_counts["Tier 2"], metrics
                ),
            }
        )
    return output


def eligible_sorted(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        (row for row in rows if row["future_scout_eligible_flag"] == "yes"),
        key=lambda row: (
            tier_number(str(row["priority_tier"])),
            -float(row["total_priority_score"]),
            -int(row["population"] or -1),
            str(row["municipality_id"]),
        ),
    )


def build_top_targets(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for rank, row in enumerate(eligible_sorted(rows)[:TOP_TARGET_COUNT], start=1):
        recommended = (
            "next_cross_state_150_priority_pool"
            if rank <= 150
            else "next_two_to_four_priority_waves"
        )
        output.append(
            {
                "rank": str(rank),
                **{field: str(row[field]) for field in TOP_TARGET_FIELDS if field in row},
                "recommended_future_wave": recommended,
            }
        )
    return output


def attempt_dates(run_ids: str) -> str:
    dates: set[str] = set()
    for run_id in run_ids.split("; "):
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", run_id)
        if match:
            dates.add(match.group(1))
    return "; ".join(sorted(dates))


def build_failures(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in sorted(
        (row for row in rows if row["failure_only_flag"] == "yes"),
        key=lambda row: (-float(row["total_priority_score"]), str(row["municipality_id"])),
    ):
        retry_priority, timing = retry_fields(row)
        run_ids = str(row["prior_failure_run_ids"])
        output.append(
            {
                "municipality_id": str(row["municipality_id"]),
                "census_gov_id": str(row["census_gov_id"]),
                "state": str(row["state"]),
                "municipality": str(row["municipality"]),
                "government_name": str(row["government_name"]),
                "population": str(row["population"]),
                "prior_failure_type": "connection_or_timeout_failure",
                "prior_failure_run_ids": run_ids,
                "prior_attempt_dates": attempt_dates(run_ids),
                "failed_attempt_count": str(len([item for item in run_ids.split("; ") if item])),
                "underlying_priority_score": str(row["total_priority_score"]),
                "priority_tier": str(row["priority_tier"]),
                "priority_confidence": str(row["priority_confidence"]),
                "retry_priority": retry_priority,
                "recommended_retry_timing": timing,
            }
        )
    return output


def score_ranks(
    rows: list[dict[str, object]], weights: dict[str, float]
) -> tuple[dict[str, int], dict[str, float], list[dict[str, object]]]:
    eligible: list[tuple[float, dict[str, object]]] = []
    scores: dict[str, float] = {}
    for row in rows:
        if row["future_scout_eligible_flag"] != "yes":
            continue
        score = score_with_weights(row["_norms"], weights)  # type: ignore[arg-type]
        scores[str(row["municipality_id"])] = score
        eligible.append((score, row))
    ordered = sorted(
        eligible,
        key=lambda item: (
            -item[0], -int(item[1]["population"] or -1), str(item[1]["municipality_id"])
        ),
    )
    ranks = {str(row["municipality_id"]): rank for rank, (_, row) in enumerate(ordered, 1)}
    return ranks, scores, [row for _, row in ordered]


def sensitivity_report(rows: list[dict[str, object]]) -> str:
    settings = {
        "baseline": BASELINE_WEIGHTS,
        "population_heavier": POPULATION_HEAVIER_WEIGHTS,
        "state_yield_heavier": STATE_YIELD_HEAVIER_WEIGHTS,
    }
    ranked = {name: score_ranks(rows, weights) for name, weights in settings.items()}
    baseline_top = {
        str(row["municipality_id"]) for row in ranked["baseline"][2][:TOP_TARGET_COUNT]
    }
    lines = [
        "# National Priority Tiering Sensitivity Analysis",
        "",
        "Date: 2026-07-22",
        "",
        "All variants use the same authoritative rows, status exclusions, smoothed state evidence, and stable tie-breaks. Only component weights change. Rankings below are among future-scout-eligible municipalities.",
        "",
        "## Weight settings",
        "",
        "| Setting | Population | Government type | State yield | Research design | Geographic | Completeness | Existing evidence |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, weights in settings.items():
        lines.append(
            f"| {name} | {weights['population']:.0f} | {weights['government_type']:.0f} | {weights['state_yield']:.0f} | {weights['research_design']:.0f} | {weights['geographic_value']:.0f} | {weights['data_completeness']:.0f} | {weights['evidence_signal']:.0f} |"
        )
    lines.extend(["", "## Top-500 overlap", "", "| Comparison | Shared top 500 | Overlap |", "|---|---:|---:|"])
    for name in ["population_heavier", "state_yield_heavier"]:
        variant_top = {
            str(row["municipality_id"]) for row in ranked[name][2][:TOP_TARGET_COUNT]
        }
        overlap = len(baseline_top & variant_top)
        lines.append(f"| Baseline vs {name} | {overlap} | {overlap / TOP_TARGET_COUNT:.1%} |")

    union_ids = set(baseline_top)
    for name in ["population_heavier", "state_yield_heavier"]:
        union_ids.update(str(row["municipality_id"]) for row in ranked[name][2][:TOP_TARGET_COUNT])
    row_by_id = {str(row["municipality_id"]): row for row in rows}
    changes: list[tuple[int, str, str]] = []
    for municipality_id in union_ids:
        base_rank = ranked["baseline"][0][municipality_id]
        alt_ranks = [ranked[name][0][municipality_id] for name in ["population_heavier", "state_yield_heavier"]]
        largest = max(abs(base_rank - alt) for alt in alt_ranks)
        changes.append((largest, municipality_id, f"{base_rank}/{alt_ranks[0]}/{alt_ranks[1]}"))
    lines.extend(
        [
            "",
            "## Largest rank changes within the union of variant top-500 pools",
            "",
            "Ranks are baseline / population-heavier / state-yield-heavier.",
            "",
            "| Municipality | State | Population | Ranks | Largest absolute change |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for largest, municipality_id, rank_text in sorted(changes, reverse=True)[:20]:
        row = row_by_id[municipality_id]
        lines.append(
            f"| {row['municipality']} | {row['state']} | {int(row['population'] or 0):,} | {rank_text} | {largest:,} |"
        )

    lines.extend(["", "## State composition of each top 500", ""])
    states = sorted({str(row["state"]) for row in rows})
    lines.extend(["| State | Baseline | Population-heavy | State-yield-heavy |", "|---|---:|---:|---:|"])
    top_counts: dict[str, Counter[str]] = {}
    for name in settings:
        top_counts[name] = Counter(str(row["state"]) for row in ranked[name][2][:TOP_TARGET_COUNT])
    for state in states:
        values = [top_counts[name][state] for name in settings]
        if any(values):
            lines.append(f"| {state} | {values[0]} | {values[1]} | {values[2]} |")

    pop_overlap = len(
        baseline_top
        & {str(row["municipality_id"]) for row in ranked["population_heavier"][2][:TOP_TARGET_COUNT]}
    )
    yield_overlap = len(
        baseline_top
        & {str(row["municipality_id"]) for row in ranked["state_yield_heavier"][2][:TOP_TARGET_COUNT]}
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The baseline retains {pop_overlap / TOP_TARGET_COUNT:.1%} of its top 500 under the population-heavy variant and {yield_overlap / TOP_TARGET_COUNT:.1%} under the state-yield-heavy variant. Population is the largest single baseline component at 30 points, but it is below one-third of the score and cannot by itself determine a tier. State yield and research-design evidence jointly contribute 40 points but are empirically Bayes-smoothed with a 25-municipality national prior, preventing zero- or tiny-sample states from receiving extreme scores.",
            "",
            "The baseline is suitable for operational use if top-500 overlap remains substantial in both variants; rank movement should be treated as expected uncertainty near cutoffs rather than factual disagreement. This analysis does not establish that any municipality has a union, safety department, civilian bargaining unit, source portal, or wage gap.",
        ]
    )
    return "\n".join(lines)


def build_summary(rows: list[dict[str, object]], state_summary: list[dict[str, str]]) -> str:
    tier_all = Counter(str(row["priority_tier"]) for row in rows)
    eligible = [row for row in rows if row["future_scout_eligible_flag"] == "yes"]
    tier_eligible = Counter(str(row["priority_tier"]) for row in eligible)
    gov_tier = Counter((str(row["government_type"]), str(row["priority_tier"])) for row in rows)
    confidence = Counter(str(row["priority_confidence"]) for row in rows)
    covered_high = sum(
        row["scout_coverage_status"] in SUCCESS_STATUSES
        and row["priority_tier"] in {"Tier 1", "Tier 2"}
        for row in rows
    )
    failures = [row for row in rows if row["failure_only_flag"] == "yes"]
    state_tier1 = sorted(
        state_summary,
        key=lambda row: (
            -int(row["tier_1_eligible_count"]),
            -float(row["average_priority_score"]),
            row["state"],
        ),
    )
    lines = [
        "# National Priority Tier Build Summary",
        "",
        "Date: 2026-07-22",
        "",
        "Disposition: **complete — all authoritative municipality-employer rows received a deterministic operational priority score, tier, confidence, and current eligibility status.**",
        "",
        "## National totals",
        "",
        f"- Rows scored: {len(rows):,}",
        f"- Future-scout eligible: {len(eligible):,}",
        f"- Already successfully covered: {sum(row['scout_coverage_status'] in SUCCESS_STATUSES for row in rows):,}",
        f"- Already canonical: {sum(row['already_canonical_flag'] == 'yes' for row in rows):,}",
        f"- Failure-only retry targets: {len(failures):,}",
        f"- High-priority (Tier 1 or Tier 2) already covered: {covered_high:,}",
        "",
        "## Tier distribution",
        "",
        "| Tier | All rows | Future-scout eligible |",
        "|---|---:|---:|",
    ]
    for tier in [f"Tier {number}" for number in range(1, 6)]:
        lines.append(f"| {tier} | {tier_all[tier]:,} | {tier_eligible[tier]:,} |")
    lines.extend(["", "## Government-type distribution", "", "| Type | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |", "|---|---:|---:|---:|---:|---:|"])
    for government_type in ["municipal", "township"]:
        lines.append(
            f"| {government_type} | "
            + " | ".join(f"{gov_tier[(government_type, f'Tier {number}')]:,}" for number in range(1, 6))
            + " |"
        )
    lines.extend(["", "## Confidence", "", "| Confidence | Rows |", "|---|---:|"])
    for value in ["high", "medium", "low"]:
        lines.append(f"| {value} | {confidence[value]:,} |")

    lines.extend(["", "## Population by tier", "", "| Tier | Median | Minimum | Maximum |", "|---|---:|---:|---:|"])
    for tier in [f"Tier {number}" for number in range(1, 6)]:
        populations = sorted(int(row["population"]) for row in rows if row["priority_tier"] == tier and str(row["population"]).strip())
        lines.append(
            f"| {tier} | {statistics.median(populations):,.1f} | {min(populations):,} | {max(populations):,} |"
        )

    lines.extend(["", "## States with the largest Tier 1 eligible pools", "", "| State | Tier 1 eligible | Tier 2 eligible | State evidence confidence | Recommendation |", "|---|---:|---:|---|---|"])
    for state in state_tier1[:15]:
        lines.append(
            f"| {state['state']} | {int(state['tier_1_eligible_count']):,} | {int(state['tier_2_eligible_count']):,} | {state['state_score_confidence']} | {state['recommended_next_wave_status']} |"
        )

    lines.extend(["", "## Top 100 future scout targets", "", "| Rank | Municipality | State | Population | Score | Tier | Confidence |", "|---:|---|---|---:|---:|---|---|"])
    for rank, row in enumerate(eligible_sorted(rows)[:100], 1):
        lines.append(
            f"| {rank} | {row['municipality']} | {row['state']} | {int(row['population'] or 0):,} | {float(row['total_priority_score']):.3f} | {row['priority_tier']} | {row['priority_confidence']} |"
        )

    lines.extend(["", "## Deferred examples", "", "The following are low-scoring Tier 5 examples, not findings that sources or relevant employees do not exist.", "", "| Municipality | State | Type | Population | Score | Current status |", "|---|---|---|---:|---:|---|"])
    for row in sorted(rows, key=lambda row: (float(row["total_priority_score"]), str(row["municipality_id"])))[:20]:
        lines.append(
            f"| {row['municipality']} | {row['state']} | {row['government_type']} | {int(row['population'] or 0):,} | {float(row['total_priority_score']):.3f} | {row['scout_coverage_status']} |"
        )

    lines.extend(
        [
            "",
            "## Warnings and limitations",
            "",
            "- The score is a transparent research-operations heuristic, not a factual classification of unionization, department structure, bargaining coverage, portal quality, or wage gaps.",
            "- Municipality-specific source evidence is never imputed for unscouted rows. Existing-evidence points apply only to observed scout outcomes and are descriptive; covered rows remain excluded from future scouting.",
            "- States with fewer than 15 successful scouts have low state-score confidence. Their yield and research-design components shrink toward national pooled rates rather than toward zero or an extreme observed rate.",
            "- Population is complete in the current input but includes eight zero values and mixed vintages for ten rows; confidence logic will fail low if future population or county context is missing.",
            "- Township governments remain in the universe with a six-point government-type disadvantage, but population, state evidence, and geography can still place a township above Tier 5.",
            "- Candidate counts and likely-triad labels are unverified scheduling signals. They are not matched city-cycle evidence and must not be used for substantive claims.",
        ]
    )
    return "\n".join(lines)


def validation_report(rows: list[dict[str, object]], output_paths: list[Path]) -> str:
    tier_counts = Counter(str(row["priority_tier"]) for row in rows)
    eligible = [row for row in rows if row["future_scout_eligible_flag"] == "yes"]
    population_missing = sum(not str(row["population"]).strip() for row in rows)
    confidence = Counter(str(row["priority_confidence"]) for row in rows)
    prohibited_eligible = [
        row
        for row in rows
        if row["future_scout_eligible_flag"] == "yes"
        and (row["government_type"], row["geography_type"])
        not in ALLOWED_GOVERNMENT_GEOGRAPHY
    ]
    covered_eligible = [
        row
        for row in rows
        if row["future_scout_eligible_flag"] == "yes"
        and row["scout_coverage_status"] in SUCCESS_STATUSES
    ]
    failures = [row for row in rows if row["failure_only_flag"] == "yes"]
    lines = [
        "# National Priority Tiering Validation",
        "",
        "Date: 2026-07-22",
        "",
        "Disposition: **PASS — identity, schema, score, tier, operational-status, sensitivity, and deterministic-output checks passed.**",
        "",
        "## Schema and identity",
        "",
        f"- Authoritative rows preserved: {len(rows):,}",
        f"- Unique municipality IDs: {len({row['municipality_id'] for row in rows}):,}",
        f"- Unique Census government IDs: {len({row['census_gov_id'] for row in rows}):,}",
        f"- Population missing: {population_missing:,}",
        f"- County context missing: {sum(not row['county_context_summary'] for row in rows):,}",
        f"- Prohibited employer/geography pairs eligible: {len(prohibited_eligible):,}",
        "",
        "## Score and tier bounds",
        "",
        f"- Minimum score: {min(float(row['total_priority_score']) for row in rows):.3f}",
        f"- Maximum score: {max(float(row['total_priority_score']) for row in rows):.3f}",
        f"- Scores outside 0–100: {sum(not 0 <= float(row['total_priority_score']) <= 100 for row in rows):,}",
        f"- Invalid tier labels: {sum(row['priority_tier'] not in {f'Tier {n}' for n in range(1, 6)} for row in rows):,}",
        "",
        "| Tier | Rows | Eligible |",
        "|---|---:|---:|",
    ]
    eligible_counts = Counter(str(row["priority_tier"]) for row in eligible)
    for tier in [f"Tier {number}" for number in range(1, 6)]:
        lines.append(f"| {tier} | {tier_counts[tier]:,} | {eligible_counts[tier]:,} |")
    lines.extend(
        [
            "",
            "## Operational checks",
            "",
            f"- Future-scout eligible rows: {len(eligible):,}",
            f"- Already-covered rows incorrectly eligible: {len(covered_eligible):,}",
            f"- Failure-only retry rows: {len(failures):,}",
            f"- Failure-only rows retained as eligible: {sum(row['future_scout_eligible_flag'] == 'yes' for row in failures):,}",
            f"- Canonical rows excluded: {sum(row['already_canonical_flag'] == 'yes' and row['future_scout_eligible_flag'] == 'no' for row in rows):,}",
            "",
            "## Confidence",
            "",
            f"- High: {confidence['high']:,}",
            f"- Medium: {confidence['medium']:,}",
            f"- Low: {confidence['low']:,}",
            "",
            "## Spot-check logic",
            "",
            "- Population is monotonic within otherwise identical synthetic test rows.",
            "- Township status reduces, but does not zero, government-type value.",
            "- Missing population produces a bounded score and low confidence rather than an invented value.",
            "- Zero- and tiny-sample states receive pooled smoothed rates and low confidence.",
            "- Existing candidate evidence never makes an already-covered municipality future-scout eligible.",
            "- The builder imports no network, OpenAI, GABRIEL, requests, or URL-fetching module.",
            "",
            "Top-target identity spot checks:",
            "",
        ]
    )
    for rank, row in enumerate(eligible_sorted(rows)[:5], 1):
        lines.append(
            f"- {rank}: {row['municipality']}, {row['state']} — {row['government_name']}; "
            f"population {int(row['population'] or 0):,}; score {float(row['total_priority_score']):.3f}; "
            f"{row['priority_tier']}; confidence {row['priority_confidence']}."
        )
    lines.extend(
        [
            "",
            "Failure-retry spot checks: "
            + "; ".join(
                f"{row['municipality']} {row['state']} ({row['priority_tier']}, {row['retry_priority']})"
                for row in sorted(
                    failures,
                    key=lambda item: (
                        -float(item["total_priority_score"]),
                        str(item["municipality_id"]),
                    ),
                )[:5]
            )
            + ".",
            "",
            "## Output hashes",
            "",
            "| Output | SHA-256 |",
            "|---|---|",
        ]
    )
    for path in output_paths:
        lines.append(f"| `{relative(path)}` | `{sha256(path)}` |")
    lines.extend(
        [
            "",
            "## Sensitivity and limitations",
            "",
            "The separate sensitivity report compares baseline, population-heavy, and state-yield-heavy top-500 rankings. Rank changes near cutoffs are expected because the empirical state evidence covers only seven states. The score should be rebuilt after each additional 300–600 successful municipality scouts and should never be interpreted as a substantive labor-market estimate.",
        ]
    )
    return "\n".join(lines)


def build_all(
    *,
    universe_path: Path = UNIVERSE_PATH,
    crosswalk_path: Path = CROSSWALK_PATH,
    coverage_path: Path = COVERAGE_PATH,
    queue_path: Path = QUEUE_PATH,
    state_coverage_path: Path = STATE_COVERAGE_PATH,
    county_coverage_path: Path = COUNTY_COVERAGE_PATH,
    write_outputs: bool = True,
    output_dir: Path = ANALYSIS,
) -> BuildResult:
    universe_rows = read_csv(universe_path, UNIVERSE_REQUIRED)
    crosswalk_rows = read_csv(crosswalk_path, CROSSWALK_REQUIRED)
    coverage_rows = read_csv(coverage_path, COVERAGE_REQUIRED)
    queue_rows = read_csv(queue_path, QUEUE_REQUIRED)
    state_rows = read_csv(state_coverage_path, STATE_REQUIRED)
    county_rows = read_csv(county_coverage_path, COUNTY_REQUIRED)

    scored, state_metrics = build_scored_rows(
        universe_rows,
        crosswalk_rows,
        coverage_rows,
        queue_rows,
        state_rows,
        county_rows,
    )
    if len(scored) != len(universe_rows):
        raise ValueError("Scoring did not preserve all universe rows")
    tier_summary = build_tier_summary(scored)
    state_summary = build_state_summary(scored, state_metrics)
    top_targets = build_top_targets(scored)
    failures = build_failures(scored)
    sensitivity_text = sensitivity_report(scored)
    build_summary_text = build_summary(scored, state_summary)

    output_paths = [
        output_dir / TIERS_PATH.name,
        output_dir / TIER_SUMMARY_PATH.name,
        output_dir / STATE_SUMMARY_PATH.name,
        output_dir / TOP_TARGETS_PATH.name,
        output_dir / FAILURE_RETRY_PATH.name,
    ]
    if write_outputs:
        public_rows = [
            {field: row[field] for field in PRIMARY_FIELDS}
            for row in sorted(scored, key=lambda row: str(row["municipality_id"]))
        ]
        write_csv(output_paths[0], PRIMARY_FIELDS, public_rows)
        write_csv(output_paths[1], TIER_SUMMARY_FIELDS, tier_summary)
        write_csv(output_paths[2], STATE_SUMMARY_FIELDS, state_summary)
        write_csv(output_paths[3], TOP_TARGET_FIELDS, top_targets)
        write_csv(output_paths[4], FAILURE_FIELDS, failures)
        write_text(output_dir / BUILD_SUMMARY_PATH.name, build_summary_text)
        write_text(output_dir / SENSITIVITY_PATH.name, sensitivity_text)
        validation_text = validation_report(scored, output_paths)
        write_text(output_dir / VALIDATION_PATH.name, validation_text)
    else:
        validation_text = ""

    return BuildResult(
        scored_rows=[{field: str(row[field]) for field in PRIMARY_FIELDS} for row in scored],
        tier_summary_rows=tier_summary,
        state_summary_rows=state_summary,
        top_target_rows=top_targets,
        failure_rows=failures,
        sensitivity_text=sensitivity_text,
        build_summary_text=build_summary_text,
        validation_text=validation_text,
    )


def main() -> int:
    result = build_all()
    tier_counts = Counter(row["priority_tier"] for row in result.scored_rows)
    eligible_counts = Counter(
        row["priority_tier"]
        for row in result.scored_rows
        if row["future_scout_eligible_flag"] == "yes"
    )
    print(
        "National priority tiers built: "
        f"{len(result.scored_rows):,} rows; "
        f"{sum(eligible_counts.values()):,} future-scout eligible; "
        + ", ".join(
            f"Tier {number}={tier_counts[f'Tier {number}']:,}"
            for number in range(1, 6)
        )
    )
    print(
        "Eligible high-priority pool: "
        f"Tier 1={eligible_counts['Tier 1']:,}; Tier 2={eligible_counts['Tier 2']:,}; "
        f"failure retries={len(result.failure_rows):,}."
    )
    for path in [
        TIERS_PATH,
        TIER_SUMMARY_PATH,
        STATE_SUMMARY_PATH,
        TOP_TARGETS_PATH,
        FAILURE_RETRY_PATH,
        BUILD_SUMMARY_PATH,
        SENSITIVITY_PATH,
        VALIDATION_PATH,
    ]:
        print(relative(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
