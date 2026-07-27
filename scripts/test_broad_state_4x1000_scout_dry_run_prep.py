#!/usr/bin/env python3
"""Fail-closed tests for the no-call broad state 4x1000 scout prep."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_broad_state_4x1000_scout_dry_run_prep.py"
SPEC = importlib.util.spec_from_file_location("broad_4x1000", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def rows(name: str) -> list[dict[str, str]]:
    with (runner.OUTPUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def data(name: str):
    return json.loads((runner.OUTPUT / name).read_text(encoding="utf-8"))


def tree_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(runner.OUTPUT.iterdir()):
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    runner.validate_complete()
    context = runner.load_context()
    master = rows("broad_state_4x1000_scout_master_locked_queue.csv")
    assert len(master) == 4000
    assert len({row["scout_target_id"] for row in master}) == 4000
    assert len({row["municipality_id"] for row in master}) == 4000
    assert {row["shard_id"] for row in master} == set(runner.SHARDS)
    assert Counter(row["shard_id"] for row in master) == Counter({shard: 1000 for shard in runner.SHARDS})
    assert not ({row["municipality_id"] for row in master} & context["actual_covered_ids"])
    assert not ({row["municipality_id"] for row in master} & context["prior_locked_ids"])
    allowed = {
        "strong_broad_geographic_target", "strong_source_family_diversification_target",
        "matched_safety_non_safety_target", "acceptable_broad_target",
    }
    assert {row["target_quality_tier"] for row in master} <= allowed
    assert all(row["prior_scout_covered_flag"] == "false" for row in master)
    assert all(row["newly_planned_this_wave_flag"] == "true" for row in master)
    assert all(row["live_status"] == "not_run" for row in master)
    assert all(row["verification_status"] == "not_verified" for row in master)
    assert all(row["download_status"] == "not_downloaded" for row in master)
    assert all(row["extraction_status"] == "not_extracted" for row in master)
    assert all(row["rating_status"] == "not_rated" for row in master)
    assert all(row["ingestion_status"] == "not_ingested" for row in master)
    assert all(row["codification_status"] == "not_codified" for row in master)
    assert all(row["causal_status"] == "not_causal_evidence" for row in master)
    assert all(row["global_analysis_readiness"] == "false" for row in master)
    assert len({row["source_family_query_family"] for row in master}) == 8
    assert set(Counter(row["source_family_query_family"] for row in master).values()) == {500}

    union: list[dict[str, str]] = []
    for number, shard in enumerate(runner.SHARDS, start=1):
        shard_rows = rows(f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue.csv")
        assert len(shard_rows) == 1000
        assert {row["shard_id"] for row in shard_rows} == {shard}
        assert len({row["state"] for row in shard_rows}) >= 48
        assert set(row["region"] for row in shard_rows) == {"Northeast", "Midwest", "South", "West"}
        assert set(Counter(row["source_family_query_family"] for row in shard_rows).values()) == {125}
        summary = data(f"broad_state_4x1000_scout_shard_{number:03d}_locked_queue_summary.json")
        assert summary["independently_runnable"] is True
        assert summary["independently_resumable"] is True
        union.extend(shard_rows)
    assert {row["scout_target_id"] for row in union} == {row["scout_target_id"] for row in master}

    decision = data("broad_state_4x1000_scout_dry_run_prep_decision.json")
    assert decision["decision"] == runner.DECISION
    assert decision["actual_scout_covered_municipalities_before_wave"] == 2922
    assert decision["actual_scout_covered_municipalities_after_dry_run_prep"] == 2922
    assert decision["projected_cumulative_if_all_parseable"] == 6922
    assert decision["prior_review_eligible_candidates_preserved"] == 1205
    assert decision["candidate_review_deferred"] is True
    for key in (
        "hosted_search_calls", "direct_sdk_calls", "api_model_calls", "url_opens",
        "head_get_requests", "downloads", "source_document_accesses",
        "candidate_review_runs", "ocr_runs", "render_runs", "text_extractions",
        "span_extractions", "rating_runs", "ingestion_runs", "codification_runs",
        "wage_gap_calculations", "regressions", "treatment_effect_estimates",
        "national_or_population_prevalence_claims", "final_causal_claims",
        "raw_prompts_saved", "raw_responses_saved",
    ):
        assert decision[key] == 0

    runner_source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
    for forbidden in (
        "openai", "requests.get", "requests.post", "httpx", "urllib.request",
        "web_search", "gabriel.codify", "pytesseract", "pdf2image",
    ):
        assert forbidden not in runner_source

    next_prompt = (runner.OUTPUT / "next_broad_state_4x1000_live_scout_prompt.md").read_text(encoding="utf-8").casefold()
    for phrase in (
        "do not collapse the queues", "candidate review remains deferred",
        "dashboard update requirement", "total scout coverage only",
        "global analysis readiness remains false", "future rating artifact-completeness requirement",
    ):
        assert phrase in next_prompt

    dashboard_spec = importlib.util.spec_from_file_location(
        "dashboard", ROOT / "scripts/build_dashboard_data.py"
    )
    assert dashboard_spec and dashboard_spec.loader
    dashboard = importlib.util.module_from_spec(dashboard_spec)
    dashboard_spec.loader.exec_module(dashboard)
    complete, dashboard_decision = dashboard.broad_state_4x1000_dry_run_prep_status()
    assert complete and dashboard_decision["decision"] == runner.DECISION
    phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
    state = json.loads((ROOT / "docs/dashboard/data/state_summary.json").read_text())
    operations = json.loads((ROOT / "docs/dashboard/data/parallel_scout_status.json").read_text())
    assert phase["current_phase_code"] == runner.DECISION
    assert phase["current_scout_covered"] == 2922
    assert phase["current_candidate_queue_rows"] == 6027
    assert phase["broad_state_4x1000_master_locked_target_count"] == 4000
    assert state["metadata"]["current_map_layer"] == "total_scout_coverage_only"
    assert state["metadata"]["broad_state_4x1000_planned_targets_added_to_map"] == 0
    assert state["totals"]["scout_covered_municipalities"] == 2922
    assert state["totals"]["candidate_rows"] == 6027
    assert state["metadata"]["global_analysis_readiness"] is False
    assert operations["parallel_mode_status"] == "broad_4x1000_dry_run_locked_live_not_run"
    assert operations["current_scout_covered"] == 2922
    assert operations["planned_round_expected_attempted"] == 4000
    assert operations["planned_targets_added_to_actual_coverage"] == 0
    assert operations["candidate_review_deferred"] is True

    before = tree_hash()
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(RUNNER_PATH), "--validate"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    after = tree_hash()
    assert "completed_outputs_valid_zero_writes" in result.stdout
    assert before == after
    print("Broad state 4x1000 scout dry-run prep tests passed")


if __name__ == "__main__":
    main()
