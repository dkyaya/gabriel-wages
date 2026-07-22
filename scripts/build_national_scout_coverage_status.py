#!/usr/bin/env python3
"""Build national live-scout coverage statuses from preserved local artifacts.

The 35,589-row municipality universe and municipality-county crosswalk are
authoritative inputs. This script does not rebuild or download either source.
It overlays successful PA/TX/MA/NJ/IL/NY/CA live runs, keeps connection/transport-only
attempts as excluded infrastructure failures, joins the deferred-verification
queue, and writes municipality/state/county status outputs under
``docs/analysis``.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "analysis"
AS_OF = "2026-07-22"

UNIVERSE_PATH = DOCS / "national_municipality_universe.csv"
CROSSWALK_PATH = DOCS / "national_municipality_county_crosswalk.csv"
COUNTY_PATH = DOCS / "national_county_universe.csv"
QUEUE_PATH = DOCS / "national_scout_candidate_queue_2026-07-20.csv"
PA_COVERAGE_PATH = DOCS / "gabriel_state_source_scout_municipality_coverage.csv"
COST_LOG_PATH = DOCS / "gabriel_state_source_scout_cost_log.csv"
MIXED_STATE_USAGE_PATHS = [
    DOCS / "coordinator_150row_serial_live_state_usage_2026-07-21.csv",
    DOCS / "wave2_coordinator_150row_serial_live_state_usage_2026-07-22.csv",
]

MUNICIPALITY_OUTPUT = DOCS / "national_scout_coverage_municipality_2026-07-20.csv"
STATE_OUTPUT = DOCS / "national_scout_coverage_state.csv"
COUNTY_OUTPUT = DOCS / "national_scout_coverage_county.csv"

SUCCESSFUL_BATCHES = [
    {
        "state": "TX",
        "wave": "NWMS-2026-07-16-01",
        "run_id": "tx_2026-07-16_164549",
        "scout_date": "2026-07-16",
        "input": DOCS / "national_batch01_tx_scout_input_2026-07-16.csv",
        "backend": "gabriel",
    },
    {
        "state": "MA",
        "wave": "NWMS-2026-07-16-01",
        "run_id": "ma_2026-07-20_150025",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_ma_scout_input_2026-07-16.csv",
        "backend": "gabriel",
    },
    {
        "state": "NJ",
        "wave": "NWMS-2026-07-16-01",
        "run_id": "nj_2026-07-20_165402",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_nj_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
    },
    {
        "state": "IL",
        "wave": "IL25-2026-07-20",
        "run_id": "il_2026-07-20_184849",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_il25_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": ["cog_2025_124994"],
    },
    {
        "state": "IL",
        "wave": "IL25.2-2026-07-20",
        "run_id": "il_2026-07-20_205824",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_il25_2_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
    },
    {
        "state": "IL",
        "wave": "IL25.3-2026-07-20",
        "run_id": "il_2026-07-20_215904",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_il25_3_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
    },
    {
        "state": "NY",
        "wave": "NY25-2026-07-20",
        "run_id": "ny_2026-07-20_200033",
        "scout_date": "2026-07-20",
        "input": DOCS / "national_batch01_ny25_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
    },
    {
        "state": "CA",
        "wave": "CA25-2026-07-20",
        "run_id": "ca_2026-07-21_101012",
        "scout_date": "2026-07-21",
        "input": DOCS / "national_batch01_ca25_scout_input_2026-07-20.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": [
            "cog_2025_123093",
            "cog_2025_211214",
            "cog_2025_161299",
            "cog_2025_207604",
        ],
    },
    {
        "state": "CA",
        "wave": "SERIALIZED-STAGE1-W01-CA25.2-2026-07-21",
        "run_id": "ca_2026-07-21_165516",
        "scout_date": "2026-07-21",
        "input": DOCS / "parallel_worker_01_ca25_scout_input_2026-07-21.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": ["cog_2025_100750"],
    },
    {
        "state": "NJ",
        "wave": "SERIALIZED-STAGE1-W02-NJ25-2026-07-21",
        "run_id": "nj_2026-07-21_172457",
        "scout_date": "2026-07-21",
        "input": DOCS / "parallel_worker_02_nj25_scout_input_2026-07-21.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": ["cog_2025_170189"],
    },
    {
        "state": "ALL",
        "allowed_states": {"CA", "NJ", "TX"},
        "wave": "COORD-SERIAL150-2026-07-21",
        "run_id": "all_2026-07-21_193524",
        "scout_date": "2026-07-21",
        "input": DOCS / "coordinator_150row_serial_live_input_2026-07-21.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": ["cog_2025_161238"],
    },
    {
        "state": "ALL",
        "allowed_states": {"CA", "IL", "TX"},
        "wave": "COORD-SERIAL150-WAVE2-2026-07-22",
        "run_id": "all_2026-07-22_114424",
        "scout_date": "2026-07-22",
        "input": DOCS / "wave2_coordinator_150row_serial_live_input_2026-07-22.csv",
        "backend": "direct-sdk",
        "failed_municipality_ids": ["cog_2025_162476", "cog_2025_162300"],
    },
]

# Preserved failed-run artifacts contain 16 MA connection-only rows, one IL
# no-response timeout, and four CA no-response timeouts. Every affected MA
# municipality later received a successful rerun; Bloomington IL and the four
# CA municipalities did not. These attempts are excluded from successful
# discovery coverage but retained as infrastructure-failure counts.
FAILED_CONNECTION_RUNS = {
    "ma_2026-07-16_183246": [
        "ma_somerville",
        "ma_newton",
        "ma_boston",
        "ma_worcester",
        "ma_arlington",
        "ma_georgetown",
        "ma_franklin",
        "ma_seekonk",
    ],
    "ma_2026-07-16_183534": [
        "ma_worcester",
        "ma_arlington",
        "ma_georgetown",
        "ma_franklin",
        "ma_seekonk",
    ],
    "ma_2026-07-16_183405": [
        "ma_somerville",
        "ma_newton",
        "ma_boston",
    ],
    "il_2026-07-20_184849": ["cog_2025_124994"],
    "ca_2026-07-21_101012": [
        "cog_2025_123093",
        "cog_2025_211214",
        "cog_2025_161299",
        "cog_2025_207604",
    ],
    "ca_2026-07-21_165516": ["cog_2025_100750"],
    "nj_2026-07-21_172457": ["cog_2025_170189"],
    "all_2026-07-21_193524": ["cog_2025_161238"],
    "all_2026-07-22_114424": ["cog_2025_162476", "cog_2025_162300"],
}

QUEUE_VERIFY_BUCKETS = {
    "high_priority_later_verify",
    "medium_priority_later_verify",
    "low_priority_later_verify",
}

MUNICIPALITY_FIELDS = [
    "state",
    "municipality",
    "municipality_id",
    "census_gov_id",
    "government_type",
    "geography_type",
    "population",
    "already_in_corpus",
    "scout_coverage_status",
    "queue_status",
    "verification_coverage_status",
    "later_ingestion_status",
    "canonical_overlap_status",
    "successful_live_scout_count",
    "successful_scout_run_ids",
    "last_successful_scout_date",
    "source_waves",
    "live_backends",
    "failed_connection_attempt_count",
    "failed_connection_run_ids",
    "connection_failure_accounting",
    "candidate_rows_total",
    "police_candidate_rows",
    "fire_candidate_rows",
    "non_safety_candidate_rows",
    "other_candidate_rows",
    "likely_triad_from_scout_rows",
    "queued_for_later_verification_count",
    "calibration_reviewed_candidate_count",
    "verified_later_ingest_candidate_count",
    "already_ingested_canonical_candidate_count",
    "high_priority_queue_count",
    "medium_priority_queue_count",
    "low_priority_queue_count",
    "hold_or_rejected_candidate_count",
    "coverage_as_of",
    "notes",
]

STATE_FIELDS = [
    "state",
    "county_equivalent_count",
    "municipalities_in_universe",
    "municipalities_not_scouted",
    "municipalities_scouted",
    "municipalities_scouted_with_candidates",
    "municipalities_scouted_no_candidates",
    "municipalities_scout_attempt_failed_connection",
    "connection_failed_attempts_excluded_from_coverage",
    "municipalities_scout_positive",
    "municipalities_with_police_candidate",
    "municipalities_with_fire_candidate",
    "municipalities_with_non_safety_candidate",
    "municipalities_with_likely_triad",
    "candidate_rows_total",
    "municipalities_queued_for_later_verification",
    "queued_for_later_verification_candidate_rows",
    "calibration_verified_municipalities",
    "calibration_reviewed_candidate_rows",
    "verified_later_ingest_candidate_rows",
    "scout_covered_municipalities_already_ingested_canonical",
    "already_ingested_canonical_candidate_rows",
    "official_or_union_candidate_rows",
    "high_priority_candidate_rows",
    "scout_total_cost",
    "scout_cost_available",
    "input_tokens_total",
    "reasoning_tokens_total",
    "output_tokens_total",
    "last_updated",
    "notes",
]

COUNTY_FIELDS = [
    "state",
    "county_geoid",
    "county_name",
    "municipality_associations_in_universe",
    "municipality_associations_not_scouted",
    "municipality_associations_scouted",
    "municipality_associations_scouted_with_candidates",
    "municipality_associations_scouted_no_candidates",
    "municipality_associations_scout_attempt_failed_connection",
    "connection_failed_attempts_excluded_from_coverage",
    "municipality_associations_scout_positive",
    "candidate_rows_total",
    "municipality_associations_queued_for_later_verification",
    "queued_for_later_verification_candidate_rows",
    "calibration_verified_municipality_associations",
    "verified_later_ingest_candidate_rows",
    "already_ingested_canonical_municipality_associations",
    "already_ingested_canonical_candidate_rows",
    "likely_triad_municipality_associations",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    parsed = read_csv(path)
    if len(parsed) != len(rows):
        raise ValueError(f"Row count changed on parse-back: {path}")
    if parsed and set(parsed[0]) != set(fields):
        raise ValueError(f"Schema changed on parse-back: {path}")


def load_successful_scouts() -> dict[str, list[dict[str, str]]]:
    successful: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(PA_COVERAGE_PATH):
        successful[row["municipality_id"]].append(
            {
                "run_id": row["run_id"],
                "scout_date": "2026-07-15",
                "wave": row["batch_id"],
                "backend": "gabriel",
                "source": PA_COVERAGE_PATH.relative_to(ROOT).as_posix(),
            }
        )
    for batch in SUCCESSFUL_BATCHES:
        failed_ids = set(batch.get("failed_municipality_ids", []))
        for row in read_csv(batch["input"]):
            allowed_states = set(batch.get("allowed_states", {batch["state"]}))
            if row["state"] not in allowed_states:
                raise ValueError(f"Unexpected state in {batch['input']}: {row['state']}")
            if row["municipality_id"] in failed_ids:
                continue
            successful[row["municipality_id"]].append(
                {
                    "run_id": batch["run_id"],
                    "scout_date": batch["scout_date"],
                    "wave": batch["wave"],
                    "backend": batch["backend"],
                    "source": batch["input"].relative_to(ROOT).as_posix(),
                }
            )
    return successful


def load_failed_connections() -> dict[str, list[str]]:
    failures: dict[str, list[str]] = defaultdict(list)
    for run_id, municipality_ids in FAILED_CONNECTION_RUNS.items():
        for municipality_id in municipality_ids:
            failures[municipality_id].append(run_id)
    return failures


def load_calibration_municipalities() -> set[str]:
    result: set[str] = set()
    for path in [
        DOCS / "national_batch01_tx_source_verification_2026-07-16.csv",
        DOCS / "national_batch01_ma_source_verification_2026-07-20.csv",
    ]:
        result.update(row["municipality_id"] for row in read_csv(path))
    return result


def build_municipality_rows() -> list[dict[str, object]]:
    universe = read_csv(UNIVERSE_PATH)
    universe_ids = {row["municipality_id"] for row in universe}
    if len(universe) != 35_589 or len(universe_ids) != len(universe):
        raise ValueError("Authoritative municipality universe is not the expected unique 35,589 rows")

    queue_by_municipality: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(QUEUE_PATH):
        queue_by_municipality[row["municipality_id"]].append(row)
    successful = load_successful_scouts()
    failures = load_failed_connections()
    calibration_municipalities = load_calibration_municipalities()
    unknown_ids = (set(queue_by_municipality) | set(successful) | set(failures)) - universe_ids
    if unknown_ids:
        raise ValueError(f"Scout accounting IDs are missing from the universe: {sorted(unknown_ids)}")

    pa_expected = {
        row["municipality_id"]: int(row["candidate_count"])
        for row in read_csv(PA_COVERAGE_PATH)
    }
    for municipality_id, expected in pa_expected.items():
        if len(queue_by_municipality[municipality_id]) != expected:
            raise ValueError(
                f"PA candidate count mismatch for {municipality_id}: "
                f"{len(queue_by_municipality[municipality_id])} != {expected}"
            )

    output: list[dict[str, object]] = []
    for municipality in universe:
        municipality_id = municipality["municipality_id"]
        queue_rows = queue_by_municipality.get(municipality_id, [])
        success_rows = successful.get(municipality_id, [])
        failed_run_ids = sorted(failures.get(municipality_id, []))
        candidate_count = len(queue_rows)
        if success_rows:
            scout_status = (
                "scouted_with_candidates" if candidate_count else "scouted_no_candidates"
            )
        elif failed_run_ids:
            scout_status = "scout_attempt_failed_connection"
        else:
            scout_status = "not_scouted"

        queued_rows = [
            row for row in queue_rows if row["triage_bucket"] in QUEUE_VERIFY_BUCKETS
        ]
        if queued_rows:
            queue_status = "queued_for_later_verification"
        elif candidate_count:
            queue_status = "candidate_holds_only"
        elif success_rows:
            queue_status = "scouted_no_candidates"
        elif failed_run_ids:
            queue_status = "scout_attempt_failed_connection"
        else:
            queue_status = "not_scouted"

        calibration_reviewed = [
            row for row in queue_rows if row["calibration_status"] != "not_calibrated"
        ]
        later_ingest = [
            row
            for row in queue_rows
            if row["later_ingestion_queue_status"] == "verified_later_ingest_candidate"
        ]
        canonical_candidates = [
            row
            for row in queue_rows
            if row["later_ingestion_queue_status"] == "already_ingested_canonical"
        ]
        if later_ingest:
            later_ingestion_status = "verified_later_ingest_candidate"
        elif candidate_count:
            later_ingestion_status = "ingestion_deferred"
        else:
            later_ingestion_status = "no_candidate_for_ingestion"

        unit_counts = Counter(row["unit_type_scouted"] for row in queue_rows)
        triad = {"police", "fire", "non_safety"}.issubset(unit_counts)
        successful_run_ids = sorted({row["run_id"] for row in success_rows})
        waves = sorted({row["wave"] for row in success_rows})
        backends = sorted({row["backend"] for row in success_rows})
        dates = sorted({row["scout_date"] for row in success_rows})
        output.append(
            {
                "state": municipality["state"],
                "municipality": municipality["municipality"],
                "municipality_id": municipality_id,
                "census_gov_id": municipality["census_gov_id"],
                "government_type": municipality["government_type"],
                "geography_type": municipality["geography_type"],
                "population": municipality["population"],
                "already_in_corpus": municipality["already_in_corpus"],
                "scout_coverage_status": scout_status,
                "queue_status": queue_status,
                "verification_coverage_status": (
                    "calibration_verified"
                    if municipality_id in calibration_municipalities
                    else "not_verified"
                ),
                "later_ingestion_status": later_ingestion_status,
                "canonical_overlap_status": (
                    "already_ingested_canonical"
                    if municipality["already_in_corpus"] == "yes"
                    else "not_already_ingested_canonical"
                ),
                "successful_live_scout_count": len(successful_run_ids),
                "successful_scout_run_ids": "; ".join(successful_run_ids),
                "last_successful_scout_date": dates[-1] if dates else "",
                "source_waves": "; ".join(waves),
                "live_backends": "; ".join(backends),
                "failed_connection_attempt_count": len(failed_run_ids),
                "failed_connection_run_ids": "; ".join(failed_run_ids),
                "connection_failure_accounting": (
                    "excluded_from_discovery_coverage; later_success_counted"
                    if failed_run_ids and success_rows
                    else (
                        "excluded_from_discovery_coverage; no_successful_rerun"
                        if failed_run_ids
                        else "none"
                    )
                ),
                "candidate_rows_total": candidate_count,
                "police_candidate_rows": unit_counts["police"],
                "fire_candidate_rows": unit_counts["fire"],
                "non_safety_candidate_rows": unit_counts["non_safety"],
                "other_candidate_rows": candidate_count
                - unit_counts["police"]
                - unit_counts["fire"]
                - unit_counts["non_safety"],
                "likely_triad_from_scout_rows": "yes" if triad else "no",
                "queued_for_later_verification_count": len(queued_rows),
                "calibration_reviewed_candidate_count": len(calibration_reviewed),
                "verified_later_ingest_candidate_count": len(later_ingest),
                "already_ingested_canonical_candidate_count": len(canonical_candidates),
                "high_priority_queue_count": sum(
                    row["triage_bucket"] == "high_priority_later_verify"
                    for row in queue_rows
                ),
                "medium_priority_queue_count": sum(
                    row["triage_bucket"] == "medium_priority_later_verify"
                    for row in queue_rows
                ),
                "low_priority_queue_count": sum(
                    row["triage_bucket"] == "low_priority_later_verify"
                    for row in queue_rows
                ),
                "hold_or_rejected_candidate_count": candidate_count - len(queued_rows),
                "coverage_as_of": AS_OF,
                "notes": (
                    "Scout coverage records source-discovery execution only. Calibration, "
                    "verification, ingestion, canonical overlap, and codification remain separate."
                ),
            }
        )

    status_counts = Counter(row["scout_coverage_status"] for row in output)
    if status_counts["scouted_with_candidates"] != 391:
        raise ValueError(f"Expected 391 candidate-positive municipalities: {status_counts}")
    if status_counts["scouted_no_candidates"] != 113:
        raise ValueError(f"Expected 113 successful empty municipalities: {status_counts}")
    if status_counts["scout_attempt_failed_connection"] != 10:
        raise ValueError(f"Expected ten failure-only municipalities: {status_counts}")
    if sum(int(row["failed_connection_attempt_count"]) for row in output) != 26:
        raise ValueError(
            "Expected 16 MA attempts, three IL failures, six CA timeouts, and one NJ timeout"
        )
    return output


def load_state_costs() -> dict[str, dict[str, str]]:
    cost_rows = {row["run_id"]: row for row in read_csv(COST_LOG_PATH)}
    mixed_usage: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "input_tokens_total": Decimal("0"),
            "reasoning_tokens_total": Decimal("0"),
            "output_tokens_total": Decimal("0"),
        }
    )
    for path in MIXED_STATE_USAGE_PATHS:
        for row in read_csv(path):
            for field in [
                "input_tokens_total",
                "reasoning_tokens_total",
                "output_tokens_total",
            ]:
                mixed_usage[row["state"]][field] += Decimal(row[field])
    result: dict[str, dict[str, str]] = {}
    pa = read_csv(DOCS / "gabriel_state_source_scout_state_coverage.csv")[0]
    result["PA"] = {
        "scout_total_cost": pa["total_cost"],
        "scout_cost_available": "yes",
        "input_tokens_total": pa["input_tokens_total"],
        "reasoning_tokens_total": pa["reasoning_tokens_total"],
        "output_tokens_total": pa["output_tokens_total"],
    }
    for state, run_ids in {
        "TX": ["tx_2026-07-16_164549"],
        "MA": ["ma_2026-07-20_150025"],
        "NJ": ["nj_2026-07-20_165402", "nj_2026-07-21_172457"],
        "IL": [
            "il_2026-07-20_184849",
            "il_2026-07-20_205824",
            "il_2026-07-20_215904",
        ],
        "NY": ["ny_2026-07-20_200033"],
        "CA": ["ca_2026-07-21_101012", "ca_2026-07-21_165516"],
    }.items():
        rows = [cost_rows[run_id] for run_id in run_ids]
        cost_values = [row["total_cost"].strip() for row in rows]
        total_cost = (
            str(sum((Decimal(value) for value in cost_values), Decimal("0")))
            if all(cost_values)
            else ""
        )
        usage = mixed_usage.get(state, {})
        result[state] = {
            "scout_total_cost": total_cost,
            "scout_cost_available": "yes" if total_cost else "no",
            "input_tokens_total": str(
                sum(Decimal(row["input_tokens_total"]) for row in rows)
                + Decimal(usage.get("input_tokens_total", "0"))
            ),
            "reasoning_tokens_total": str(
                sum(Decimal(row["reasoning_tokens_total"]) for row in rows)
                + Decimal(usage.get("reasoning_tokens_total", "0"))
            ),
            "output_tokens_total": str(
                sum(Decimal(row["output_tokens_total"]) for row in rows)
                + Decimal(usage.get("output_tokens_total", "0"))
            ),
        }
    return result


def build_state_rows(municipality_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_state: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in municipality_rows:
        by_state[str(row["state"])].append(row)
    county_counts = Counter(row["state"] for row in read_csv(COUNTY_PATH))
    queue_rows = read_csv(QUEUE_PATH)
    queue_by_state: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in queue_rows:
        queue_by_state[row["state"]].append(row)
    costs = load_state_costs()

    output: list[dict[str, object]] = []
    for state in sorted(by_state):
        rows = by_state[state]
        state_queue = queue_by_state.get(state, [])
        scouted = [
            row
            for row in rows
            if row["scout_coverage_status"]
            in {"scouted_with_candidates", "scouted_no_candidates"}
        ]
        state_cost = costs.get(
            state,
            {
                "scout_total_cost": "0",
                "scout_cost_available": "not_applicable",
                "input_tokens_total": "0",
                "reasoning_tokens_total": "0",
                "output_tokens_total": "0",
            },
        )
        output.append(
            {
                "state": state,
                "county_equivalent_count": county_counts[state],
                "municipalities_in_universe": len(rows),
                "municipalities_not_scouted": sum(
                    row["scout_coverage_status"] == "not_scouted" for row in rows
                ),
                "municipalities_scouted": len(scouted),
                "municipalities_scouted_with_candidates": sum(
                    row["scout_coverage_status"] == "scouted_with_candidates" for row in rows
                ),
                "municipalities_scouted_no_candidates": sum(
                    row["scout_coverage_status"] == "scouted_no_candidates" for row in rows
                ),
                "municipalities_scout_attempt_failed_connection": sum(
                    row["scout_coverage_status"] == "scout_attempt_failed_connection"
                    for row in rows
                ),
                "connection_failed_attempts_excluded_from_coverage": sum(
                    int(row["failed_connection_attempt_count"]) for row in rows
                ),
                "municipalities_scout_positive": sum(
                    row["candidate_rows_total"] > 0 for row in scouted
                ),
                "municipalities_with_police_candidate": sum(
                    row["police_candidate_rows"] > 0 for row in scouted
                ),
                "municipalities_with_fire_candidate": sum(
                    row["fire_candidate_rows"] > 0 for row in scouted
                ),
                "municipalities_with_non_safety_candidate": sum(
                    row["non_safety_candidate_rows"] > 0 for row in scouted
                ),
                "municipalities_with_likely_triad": sum(
                    row["likely_triad_from_scout_rows"] == "yes" for row in scouted
                ),
                "candidate_rows_total": len(state_queue),
                "municipalities_queued_for_later_verification": sum(
                    row["queue_status"] == "queued_for_later_verification" for row in rows
                ),
                "queued_for_later_verification_candidate_rows": sum(
                    int(row["queued_for_later_verification_count"]) for row in rows
                ),
                "calibration_verified_municipalities": sum(
                    row["verification_coverage_status"] == "calibration_verified"
                    for row in rows
                ),
                "calibration_reviewed_candidate_rows": sum(
                    int(row["calibration_reviewed_candidate_count"]) for row in rows
                ),
                "verified_later_ingest_candidate_rows": sum(
                    int(row["verified_later_ingest_candidate_count"]) for row in rows
                ),
                "scout_covered_municipalities_already_ingested_canonical": sum(
                    row["canonical_overlap_status"] == "already_ingested_canonical"
                    for row in scouted
                ),
                "already_ingested_canonical_candidate_rows": sum(
                    int(row["already_ingested_canonical_candidate_count"]) for row in rows
                ),
                "official_or_union_candidate_rows": sum(
                    row["source_owner_type"] in {"city", "state_labor_board", "union"}
                    for row in state_queue
                ),
                "high_priority_candidate_rows": sum(
                    row["triage_bucket"] == "high_priority_later_verify"
                    for row in state_queue
                ),
                **state_cost,
                "last_updated": AS_OF,
                "notes": (
                    "Scout coverage is successful source-discovery execution, not verification, "
                    "ingestion, canonical coverage, codification, or claim evidence."
                ),
            }
        )
    if sum(int(row["municipalities_in_universe"]) for row in output) != 35_589:
        raise ValueError("State coverage does not sum to the authoritative universe")
    if sum(int(row["municipalities_scouted"]) for row in output) != 504:
        raise ValueError("State coverage does not sum to 504 successful scout municipalities")
    return output


def build_county_rows(municipality_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    municipality_by_id = {str(row["municipality_id"]): row for row in municipality_rows}
    associations: dict[str, list[dict[str, object]]] = defaultdict(list)
    for relationship in read_csv(CROSSWALK_PATH):
        associations[relationship["county_geoid"]].append(
            municipality_by_id[relationship["municipality_id"]]
        )
    output: list[dict[str, object]] = []
    for county in read_csv(COUNTY_PATH):
        rows = associations.get(county["county_geoid"], [])
        scouted = [
            row
            for row in rows
            if row["scout_coverage_status"]
            in {"scouted_with_candidates", "scouted_no_candidates"}
        ]
        output.append(
            {
                "state": county["state"],
                "county_geoid": county["county_geoid"],
                "county_name": county["county_name"],
                "municipality_associations_in_universe": len(rows),
                "municipality_associations_not_scouted": sum(
                    row["scout_coverage_status"] == "not_scouted" for row in rows
                ),
                "municipality_associations_scouted": len(scouted),
                "municipality_associations_scouted_with_candidates": sum(
                    row["scout_coverage_status"] == "scouted_with_candidates" for row in rows
                ),
                "municipality_associations_scouted_no_candidates": sum(
                    row["scout_coverage_status"] == "scouted_no_candidates" for row in rows
                ),
                "municipality_associations_scout_attempt_failed_connection": sum(
                    row["scout_coverage_status"] == "scout_attempt_failed_connection"
                    for row in rows
                ),
                "connection_failed_attempts_excluded_from_coverage": sum(
                    int(row["failed_connection_attempt_count"]) for row in rows
                ),
                "municipality_associations_scout_positive": sum(
                    row["candidate_rows_total"] > 0 for row in scouted
                ),
                "candidate_rows_total": sum(int(row["candidate_rows_total"]) for row in scouted),
                "municipality_associations_queued_for_later_verification": sum(
                    row["queue_status"] == "queued_for_later_verification" for row in rows
                ),
                "queued_for_later_verification_candidate_rows": sum(
                    int(row["queued_for_later_verification_count"]) for row in rows
                ),
                "calibration_verified_municipality_associations": sum(
                    row["verification_coverage_status"] == "calibration_verified"
                    for row in rows
                ),
                "verified_later_ingest_candidate_rows": sum(
                    int(row["verified_later_ingest_candidate_count"]) for row in rows
                ),
                "already_ingested_canonical_municipality_associations": sum(
                    row["canonical_overlap_status"] == "already_ingested_canonical"
                    for row in scouted
                ),
                "already_ingested_canonical_candidate_rows": sum(
                    int(row["already_ingested_canonical_candidate_count"]) for row in rows
                ),
                "likely_triad_municipality_associations": sum(
                    row["likely_triad_from_scout_rows"] == "yes" for row in scouted
                ),
                "notes": (
                    "County rows count municipality-county associations; multi-county governments "
                    "appear in every associated county, so county rows are not additive."
                ),
            }
        )
    return output


def main() -> int:
    municipality_rows = build_municipality_rows()
    state_rows = build_state_rows(municipality_rows)
    county_rows = build_county_rows(municipality_rows)
    write_csv(MUNICIPALITY_OUTPUT, MUNICIPALITY_FIELDS, municipality_rows)
    write_csv(STATE_OUTPUT, STATE_FIELDS, state_rows)
    write_csv(COUNTY_OUTPUT, COUNTY_FIELDS, county_rows)

    covered = [
        row
        for row in municipality_rows
        if row["scout_coverage_status"]
        in {"scouted_with_candidates", "scouted_no_candidates"}
    ]
    by_state = Counter(str(row["state"]) for row in covered)
    candidate_states = Counter(
        str(row["state"]) for row in covered if int(row["candidate_rows_total"]) > 0
    )
    print(f"municipalities_in_universe={len(municipality_rows)}")
    print(f"scout_covered_municipalities={len(covered)}")
    print("scout_covered_by_state=" + ",".join(f"{s}:{by_state[s]}" for s in sorted(by_state)))
    print(
        "candidate_positive_by_state="
        + ",".join(f"{s}:{candidate_states[s]}" for s in sorted(candidate_states))
    )
    print(
        "connection_failed_attempts_excluded="
        + str(sum(int(row["failed_connection_attempt_count"]) for row in municipality_rows))
    )
    print(f"remaining_unscouted={len(municipality_rows) - len(covered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
