#!/usr/bin/env python3
"""Offline contract tests for national municipality priority tiering."""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path

import build_national_municipality_priority_tiers as tiers


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


def main() -> int:
    first = tiers.build_all(write_outputs=False)
    rows = first.scored_rows

    check(len(rows) == 35_589, "all authoritative universe rows are preserved")
    municipality_ids = [row["municipality_id"] for row in rows]
    census_ids = [row["census_gov_id"] for row in rows]
    check(
        len(municipality_ids) == len(set(municipality_ids)),
        "municipality IDs remain unique",
    )
    check(len(census_ids) == len(set(census_ids)), "Census government IDs remain unique")

    eligible = [row for row in rows if row["future_scout_eligible_flag"] == "yes"]
    check(
        all(
            (row["government_type"], row["geography_type"])
            in tiers.ALLOWED_GOVERNMENT_GEOGRAPHY
            for row in eligible
        ),
        "no prohibited employer category is future-scout eligible",
    )
    check(
        all(0.0 <= float(row["total_priority_score"]) <= 100.0 for row in rows),
        "all scores are bounded between 0 and 100",
    )
    check(
        {row["priority_tier"] for row in rows}
        == {f"Tier {number}" for number in range(1, 6)},
        "tier values are limited to Tier 1 through Tier 5",
    )
    check(
        not any(
            row["future_scout_eligible_flag"] == "yes"
            and row["scout_coverage_status"] in tiers.SUCCESS_STATUSES
            for row in rows
        ),
        "already-covered rows are excluded from future scouting",
    )

    failures = [row for row in rows if row["failure_only_flag"] == "yes"]
    check(len(failures) == 10, "all ten failure-only municipalities are preserved")
    check(
        all(
            row["future_scout_eligible_flag"] == "yes"
            and row["retry_flag"] == "yes"
            and row["retry_priority"] in {"high", "medium", "low"}
            for row in failures
        ),
        "failure-only rows use a separate retry path",
    )

    synthetic_population = [
        {"municipality_id": "missing", "population": ""},
        {"municipality_id": "small", "population": "100"},
        {"municipality_id": "large", "population": "1000000"},
    ]
    scales = tiers.population_scales(synthetic_population)
    check(scales["missing"] == (None, None), "missing population remains missing without crashing")
    check(
        scales["large"][0] > scales["small"][0]
        and scales["large"][1] > scales["small"][1],
        "larger otherwise similar municipalities receive a larger population component",
    )

    state_by_code = {row["state"]: row for row in first.state_summary_rows}
    check(
        state_by_code["CA"]["state_score_confidence"] == "high"
        and state_by_code["PA"]["state_score_confidence"] == "medium"
        and state_by_code["AK"]["state_score_confidence"] == "low",
        "state sample-size confidence distinguishes high, medium, and sparse samples",
    )

    identical = {
        "population": 0.8,
        "government_type": 1.0,
        "state_yield": 0.7,
        "research_design": 0.6,
        "geographic_value": 0.7,
        "data_completeness": 1.0,
        "evidence_signal": 0.0,
    }
    municipal_score = tiers.score_with_weights(identical, tiers.BASELINE_WEIGHTS)
    township_norms = dict(identical, government_type=0.4)
    township_score = tiers.score_with_weights(township_norms, tiers.BASELINE_WEIGHTS)
    check(
        abs((municipal_score - township_score) - 6.0) < 1e-9,
        "township government-type penalty is exactly six points",
    )
    check(
        any(
            row["government_type"] == "township"
            and row["priority_tier"] != "Tier 5"
            for row in rows
        ),
        "township penalty does not force every township into Tier 5",
    )

    second = tiers.build_all(write_outputs=False)
    check(
        json.dumps(first.scored_rows, sort_keys=True)
        == json.dumps(second.scored_rows, sort_keys=True)
        and first.sensitivity_text == second.sensitivity_text,
        "scoring and sensitivity outputs are deterministic",
    )

    source_path = Path(tiers.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"openai", "requests", "urllib", "socket", "httpx", "gabriel"}
    check(not imported & forbidden, "builder has no network, API, model, or GABRIEL imports")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        written = tiers.build_all(write_outputs=True, output_dir=output_dir)
        expected = {
            tiers.TIERS_PATH.name,
            tiers.TIER_SUMMARY_PATH.name,
            tiers.STATE_SUMMARY_PATH.name,
            tiers.TOP_TARGETS_PATH.name,
            tiers.FAILURE_RETRY_PATH.name,
            tiers.BUILD_SUMMARY_PATH.name,
            tiers.SENSITIVITY_PATH.name,
            tiers.VALIDATION_PATH.name,
        }
        check(expected == {path.name for path in output_dir.iterdir()}, "isolated build writes the exact expected artifact set")
        check(len(written.top_target_rows) == 500, "top-target output contains exactly 500 eligible municipalities")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
