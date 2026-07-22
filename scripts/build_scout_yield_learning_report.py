#!/usr/bin/env python3
"""Build deterministic state/wave scout-yield learning outputs from local data."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "docs" / "analysis"
STATE_COVERAGE = ANALYSIS / "national_scout_coverage_state.csv"
STATE_OUTPUT = ANALYSIS / "scout_yield_learning_by_state_2026-07-22.csv"
WAVE_OUTPUT = ANALYSIS / "scout_yield_learning_by_wave_2026-07-22.csv"
REPORT_OUTPUT = ANALYSIS / "scout_yield_learning_report_2026-07-22.md"

STATE_FIELDS = [
    "state", "successful_scout_count", "candidate_positive_count",
    "parseable_empty_count", "failure_only_municipality_count",
    "connection_failed_attempt_count", "candidate_row_count",
    "candidate_positive_rate", "candidate_rows_per_covered_municipality",
    "parseable_empty_rate", "failure_only_rate", "connection_failure_attempt_rate",
    "sample_confidence", "recommended_next_wave_status", "interpretation_note",
]
WAVE_FIELDS = [
    "wave_id", "wave_label", "run_id", "attempted_rows", "parseable_rows",
    "candidate_positive_municipalities", "parseable_empty_municipalities",
    "failure_only_rows", "candidate_rows", "runtime_seconds", "rows_per_hour",
    "candidate_rows_per_hour", "candidate_rows_per_parseable_municipality",
    "candidate_positive_rate_among_parseable", "sleep_between_prompts_seconds",
    "source_review_document",
]

WAVES = (
    {
        "wave_id": "wave1", "wave_label": "Coordinator Wave 1 CA/NJ/TX",
        "run_id": "all_2026-07-21_193524", "attempted_rows": 150,
        "parseable_rows": 149, "candidate_positive_municipalities": 112,
        "parseable_empty_municipalities": 37, "failure_only_rows": 1,
        "candidate_rows": 246, "runtime_seconds": 6937.0,
        "sleep_between_prompts_seconds": 15,
        "source_review_document": "docs/analysis/coordinator_150row_serial_live_result_review_2026-07-21.md",
    },
    {
        "wave_id": "wave2", "wave_label": "Coordinator Wave 2 CA/TX/IL",
        "run_id": "all_2026-07-22_114424", "attempted_rows": 150,
        "parseable_rows": 148, "candidate_positive_municipalities": 98,
        "parseable_empty_municipalities": 50, "failure_only_rows": 2,
        "candidate_rows": 223, "runtime_seconds": 6149.884,
        "sleep_between_prompts_seconds": 5,
        "source_review_document": "docs/analysis/wave2_coordinator_150row_serial_live_result_review_2026-07-22.md",
    },
    {
        "wave_id": "tier1_wave1", "wave_label": "Tier 1 Wave 1 cross-state",
        "run_id": "all_2026-07-22_164144", "attempted_rows": 150,
        "parseable_rows": 142, "candidate_positive_municipalities": 99,
        "parseable_empty_municipalities": 43, "failure_only_rows": 8,
        "candidate_rows": 268, "runtime_seconds": 6723.519,
        "sleep_between_prompts_seconds": 5,
        "source_review_document": "docs/analysis/tier1_coordinator_150row_serial_live_after_diag_result_review_2026-07-22.md",
    },
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def as_int(row: dict[str, str], field: str) -> int:
    return int(row.get(field, "") or 0)


def ratio(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.6f}" if denominator else ""


def state_confidence(successful: int) -> str:
    if successful >= 25:
        return "high"
    if successful >= 10:
        return "medium"
    return "low"


def state_recommendation(successful: int, positive_rate: float, density: float) -> str:
    if successful < 10:
        return "calibration_sample_needed"
    if positive_rate >= 0.70 or density >= 1.75:
        return "strong_yield_consider_next_wave"
    if positive_rate >= 0.50 or density >= 1.0:
        return "moderate_yield_use_priority_targets"
    return "lower_yield_use_for_strategic_coverage"


def build_state_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: item["state"]):
        covered = as_int(row, "municipalities_scouted")
        positive = as_int(row, "municipalities_scouted_with_candidates")
        empty = as_int(row, "municipalities_scouted_no_candidates")
        failure_only = as_int(row, "municipalities_scout_attempt_failed_connection")
        failed_attempts = as_int(row, "connection_failed_attempts_excluded_from_coverage")
        candidates = as_int(row, "candidate_rows_total")
        positive_rate = positive / covered if covered else 0.0
        density = candidates / covered if covered else 0.0
        output.append(
            {
                "state": row["state"],
                "successful_scout_count": str(covered),
                "candidate_positive_count": str(positive),
                "parseable_empty_count": str(empty),
                "failure_only_municipality_count": str(failure_only),
                "connection_failed_attempt_count": str(failed_attempts),
                "candidate_row_count": str(candidates),
                "candidate_positive_rate": ratio(positive, covered),
                "candidate_rows_per_covered_municipality": ratio(candidates, covered),
                "parseable_empty_rate": ratio(empty, covered),
                "failure_only_rate": ratio(failure_only, covered + failure_only),
                "connection_failure_attempt_rate": ratio(failed_attempts, covered + failed_attempts),
                "sample_confidence": state_confidence(covered),
                "recommended_next_wave_status": state_recommendation(
                    covered, positive_rate, density
                ),
                "interpretation_note": (
                    "Scout-stage operational yield only; candidates remain unverified."
                ),
            }
        )
    return output


def build_wave_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in WAVES:
        runtime = float(spec["runtime_seconds"])
        attempted = int(spec["attempted_rows"])
        parseable = int(spec["parseable_rows"])
        candidates = int(spec["candidate_rows"])
        positive = int(spec["candidate_positive_municipalities"])
        row = {key: str(value) for key, value in spec.items()}
        row.update(
            {
                "runtime_seconds": f"{runtime:.3f}",
                "rows_per_hour": f"{attempted * 3600 / runtime:.3f}",
                "candidate_rows_per_hour": f"{candidates * 3600 / runtime:.3f}",
                "candidate_rows_per_parseable_municipality": f"{candidates / parseable:.3f}",
                "candidate_positive_rate_among_parseable": f"{positive / parseable:.6f}",
            }
        )
        rows.append({field: row[field] for field in WAVE_FIELDS})
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(state_rows: list[dict[str, str]], wave_rows: list[dict[str, str]]) -> None:
    ranked = sorted(
        [row for row in state_rows if int(row["successful_scout_count"]) >= 10],
        key=lambda row: (
            -float(row["candidate_rows_per_covered_municipality"]),
            -float(row["candidate_positive_rate"]),
            row["state"],
        ),
    )
    lines = [
        "# Scout Yield Learning Report — 2026-07-22",
        "",
        "This deterministic offline report compares discovery-stage operational yield. Candidate rows remain unverified and are not evidence of source validity or wage effects.",
        "",
        "## Wave comparison",
        "",
        "| Wave | Parseable | Positive | Empty | Failures | Candidates | Runtime s | Rows/hour | Candidates/hour | Candidates/parseable |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in wave_rows:
        lines.append(
            f"| {row['wave_label']} | {row['parseable_rows']} | {row['candidate_positive_municipalities']} | {row['parseable_empty_municipalities']} | {row['failure_only_rows']} | {row['candidate_rows']} | {row['runtime_seconds']} | {row['rows_per_hour']} | {row['candidate_rows_per_hour']} | {row['candidate_rows_per_parseable_municipality']} |"
        )
    lines.extend([
        "", "## State-yield learning", "",
        "States with at least 10 successful scouts are ranked by candidate rows per covered municipality; smaller samples remain calibration targets rather than yield conclusions.",
        "", "| State | Covered | Positive rate | Candidate density | Empty rate | Failure-only rate | Confidence | Recommendation |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ])
    for row in ranked[:15]:
        lines.append(
            f"| {row['state']} | {row['successful_scout_count']} | {float(row['candidate_positive_rate']):.1%} | {float(row['candidate_rows_per_covered_municipality']):.3f} | {float(row['parseable_empty_rate']):.1%} | {float(row['failure_only_rate'] or 0):.1%} | {row['sample_confidence']} | {row['recommended_next_wave_status']} |"
        )
    average_density = mean(float(row["candidate_rows_per_parseable_municipality"]) for row in wave_rows)
    confidence = Counter(row["sample_confidence"] for row in state_rows)
    lines.extend([
        "", "## Operating recommendation", "",
        f"Across the three reviewed 150-row waves, mean candidate density was {average_density:.3f} rows per parseable municipality. Use Tier 1 rank as the primary selector, then blend states with medium/high sample confidence and strong observed yield with under-sampled states needed for calibration and geographic coverage.",
        "",
        f"State sample confidence counts: high={confidence['high']}, medium={confidence['medium']}, low={confidence['low']}.",
        "",
        "Refresh this learning report after each wave and rebuild the unchanged priority methodology after 300–600 additional successful scouts (current checkpoint: 646 covered; next refresh window: 804–1,104 covered). Do not let sparse-state extremes dominate selection.",
        "",
        "No network, API/model, URL verification, ingestion, codification, queue rebuild, coverage rebuild, or priority-methodology change occurs in this builder.",
    ])
    REPORT_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    state_rows = build_state_rows(read_csv(STATE_COVERAGE))
    wave_rows = build_wave_rows()
    write_csv(STATE_OUTPUT, state_rows, STATE_FIELDS)
    write_csv(WAVE_OUTPUT, wave_rows, WAVE_FIELDS)
    write_report(state_rows, wave_rows)
    if len(state_rows) != 51 or len(wave_rows) != 3:
        raise ValueError("unexpected yield-learning output row count")
    print(
        "Scout yield learning built: states/DC=51; waves=3; "
        f"latest_rows_per_hour={wave_rows[-1]['rows_per_hour']}; "
        f"latest_candidate_rows_per_parseable={wave_rows[-1]['candidate_rows_per_parseable_municipality']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
