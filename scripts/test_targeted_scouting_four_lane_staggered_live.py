#!/usr/bin/env python3
"""Focused fail-closed tests for the four-lane staggered-live preflight."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/run_targeted_scouting_four_lane_staggered_live.py"
SPEC = importlib.util.spec_from_file_location("staggered_live", SCRIPT)
assert SPEC and SPEC.loader
live = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = live
SPEC.loader.exec_module(live)

DASHBOARD_SCRIPT = ROOT / "scripts/build_dashboard_data.py"
DASHBOARD_SPEC = importlib.util.spec_from_file_location("dashboard", DASHBOARD_SCRIPT)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
sys.modules[DASHBOARD_SPEC.name] = dashboard
DASHBOARD_SPEC.loader.exec_module(dashboard)

OUT = live.OUTPUT_DIR


def read_json(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class StaggeredLivePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        live.validate_completed_failure()
        cls.decision = read_json("targeted_scouting_four_lane_staggered_live_decision.json")
        cls.preflight = read_json("targeted_scouting_four_lane_staggered_live_preflight_checks.json")
        cls.invariants = read_json("targeted_scouting_four_lane_staggered_live_invariant_checks.json")

    def test_decision_is_preflight_failed(self):
        self.assertEqual(self.decision["decision"], live.DECISION)

    def test_completion_status_cannot_masquerade_as_live(self):
        self.assertEqual(self.decision["completion_status"], "preflight_failed_no_live_execution")

    def test_prep_commit_is_exact(self):
        self.assertEqual(self.preflight["prep_commit"], live.PREP_COMMIT)

    def test_input_integrity_checks_pass(self):
        self.assertTrue(self.preflight["all_input_integrity_checks_passed"])

    def test_schedule_check_fails_closed(self):
        self.assertFalse(self.preflight["schedule_check_passed"])

    def test_preflight_does_not_pass(self):
        self.assertFalse(self.preflight["preflight_passed"])

    def test_failure_code_is_specific(self):
        self.assertEqual(self.preflight["failure_code"], "fixed_stagger_conflicts_with_no_simultaneous_lane_execution")

    def test_locked_target_count_is_2000(self):
        self.assertEqual(self.preflight["locked_target_count"], 2000)

    def test_each_lane_is_exactly_500(self):
        self.assertEqual(self.preflight["lane_counts"], {lane: 500 for lane in live.LANES})

    def test_offsets_are_exact(self):
        self.assertEqual(self.preflight["start_offsets_minutes"], live.START_OFFSETS_MINUTES)

    def test_credential_present_without_value(self):
        self.assertTrue(self.preflight["credential_present"])
        self.assertNotIn("HARVARD_SUBSCRIPTION_KEY", json.dumps(self.preflight))

    def test_no_hosted_search_calls(self):
        self.assertEqual(self.preflight["hosted_search_calls"], 0)

    def test_no_model_api_calls(self):
        self.assertEqual(self.preflight["model_api_calls"], 0)

    def test_no_lane_runs_completed(self):
        self.assertEqual(self.decision["lane_runs_completed"], 0)

    def test_no_candidate_sources_created(self):
        self.assertEqual(self.decision["candidate_source_count"], 0)
        self.assertEqual(read_csv(OUT / "targeted_scouting_four_lane_candidate_sources.csv"), [])

    def test_all_targets_are_explicitly_not_run(self):
        rows = read_csv(OUT / "targeted_scouting_four_lane_skipped_targets.csv")
        self.assertEqual(len(rows), 2000)
        self.assertTrue(all(row["live_attempted"] == "no" for row in rows))

    def test_no_duplicate_skipped_target_ids(self):
        rows = read_csv(OUT / "targeted_scouting_four_lane_skipped_targets.csv")
        self.assertEqual(len({row["scout_target_id"] for row in rows}), 2000)

    def test_candidate_review_not_ready(self):
        self.assertFalse(self.decision["candidate_review_ready"])

    def test_repair_is_required(self):
        self.assertTrue(self.decision["repair_required"])

    def test_global_analysis_readiness_false(self):
        self.assertFalse(self.decision["global_analysis_readiness"])
        self.assertTrue(self.invariants["global_analysis_readiness_false"])

    def test_no_live_sdk_implementation_in_fail_closed_runner(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("AsyncOpenAI", source)
        self.assertNotIn("client.responses.create", source)

    def test_no_raw_prompt_or_response_outputs(self):
        names = [path.name.lower() for path in OUT.rglob("*") if path.is_file()]
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))

    def test_search_metadata_has_four_rows(self):
        rows = read_csv(OUT / "targeted_scouting_four_lane_search_metadata.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["hosted_search_attempted"] == "no" for row in rows))

    def test_timing_has_no_actual_starts(self):
        rows = read_csv(OUT / "targeted_scouting_four_lane_timing.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(not row["actual_start_utc"] for row in rows))

    def test_lane_outputs_are_empty_candidate_tables(self):
        for lane in live.LANES:
            path = OUT / "lane_outputs" / lane / f"targeted_scouting_{lane}_candidate_sources.csv"
            self.assertEqual(read_csv(path), [])

    def test_lane_skips_are_500_each(self):
        for lane in live.LANES:
            path = OUT / "lane_outputs" / lane / f"targeted_scouting_{lane}_skipped_targets.csv"
            self.assertEqual(len(read_csv(path)), 500)

    def test_queue_file_hashes_match_locks(self):
        for lane, audit in self.preflight["queue_audits"].items():
            self.assertEqual(audit["queue_sha256"], audit["lock_queue_sha256"], lane)

    def test_target_id_hashes_match_locks(self):
        for lane, audit in self.preflight["queue_audits"].items():
            self.assertEqual(audit["target_id_set_sha256"], audit["lock_target_id_set_sha256"], lane)

    def test_target_id_hash_contract_has_no_terminal_newline(self):
        rows = read_csv(live.PREP_DIR / "targeted_scouting_lane_1_queue_500.csv")
        self.assertEqual(live.target_id_set_sha256(rows), self.preflight["queue_audits"]["lane_1"]["lock_target_id_set_sha256"])

    def test_repair_prompt_requires_one_contract(self):
        prompt = (OUT / "next_targeted_scouting_four_lane_repair_prompt.md").read_text(encoding="utf-8")
        self.assertIn("Choose exactly one scheduling contract", prompt)
        self.assertIn("Sequential lanes", prompt)
        self.assertIn("Fixed stagger with overlap", prompt)

    def test_repair_prompt_preserves_phase_boundaries(self):
        prompt = (OUT / "next_targeted_scouting_four_lane_repair_prompt.md").read_text(encoding="utf-8")
        for phrase in ("Do not download documents", "verify", "extract", "rate", "ingest", "codify", "wage gaps", "regressions", "global analysis readiness false"):
            self.assertIn(phrase, prompt)

    def test_no_candidate_overpromotion_statuses(self):
        summary = read_json("targeted_scouting_four_lane_candidate_sources_summary.json")
        self.assertTrue(summary["candidate_only"])
        self.assertTrue(summary["live_not_run"])

    def test_partial_outputs_guard_passes(self):
        self.assertTrue(self.invariants["partial_outputs_cannot_masquerade_as_complete"])

    def test_resume_validation_is_read_only(self):
        before = {path: live.sha256_path(path) for path in live.output_files()}
        live.validate_completed_failure()
        after = {path: live.sha256_path(path) for path in live.output_files()}
        self.assertEqual(before, after)

    def test_all_required_outputs_exist(self):
        self.assertTrue(all(path.exists() for path in live.output_files()))

    def test_dashboard_gate_recognizes_failed_preflight(self):
        completed, decision = dashboard.targeted_scouting_four_lane_staggered_live_status()
        self.assertTrue(completed)
        self.assertEqual(decision["decision"], live.DECISION)

    def test_dashboard_overall_status_requires_repair(self):
        readiness = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text())
        self.assertEqual(readiness["overall_status"], "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required_global_analysis_closed")

    def test_dashboard_calibration_phase_requires_repair(self):
        calibration = json.loads((ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json").read_text())
        self.assertEqual(calibration["calibration_phase"], "targeted_scouting_four_lane_staggered_live_preflight_failed_repair_required")

    def test_dashboard_never_opens_global_readiness(self):
        readiness = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text())
        self.assertNotIn('"global_analysis_readiness": true', json.dumps(readiness, sort_keys=True).casefold())


def _add_dynamic_test(index: int, check_name: str) -> None:
    def test(self: StaggeredLivePreflightTests) -> None:
        matches = [item for item in self.preflight["checks"] if item["check"] == check_name]
        self.assertEqual(len(matches), 1)
        expected = check_name != "stagger_schedule_compatible_with_no_lane_overlap"
        self.assertIs(matches[0]["passed"], expected)

    setattr(StaggeredLivePreflightTests, f"test_preflight_check_{index:02d}_{check_name}", test)


# Twenty-three individual preflight assertions bring the complete suite to 58
# tests when combined with the 35 explicit tests above.
for _index, _name in enumerate([
    "required_prep_artifacts_present",
    "prep_decision_allows_live_preflight",
    "prep_commit_locked",
    "master_locked_target_count",
    "master_unique_target_ids",
    "lane_1_exact_500_unique_locked_targets",
    "lane_1_queue_hash_matches_lock",
    "lane_1_target_id_hash_matches_lock",
    "lane_1_scope_and_status_locked",
    "lane_2_exact_500_unique_locked_targets",
    "lane_2_queue_hash_matches_lock",
    "lane_2_target_id_hash_matches_lock",
    "lane_2_scope_and_status_locked",
    "lane_3_exact_500_unique_locked_targets",
    "lane_3_queue_hash_matches_lock",
    "lane_3_target_id_hash_matches_lock",
    "lane_3_scope_and_status_locked",
    "lane_4_exact_500_unique_locked_targets",
    "lane_4_queue_hash_matches_lock",
    "lane_4_target_id_hash_matches_lock",
    "lane_4_scope_and_status_locked",
    "combined_scope_exactly_2000_unique",
    "search_credential_present_without_disclosure",
], start=1):
    _add_dynamic_test(_index, _name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
