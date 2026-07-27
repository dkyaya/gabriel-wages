#!/usr/bin/env python3
"""Regression tests for fixed-stagger controlled-overlap candidate scouting."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run_targeted_scouting_four_lane_fixed_stagger_live.py"
SPEC = importlib.util.spec_from_file_location("fixed_stagger", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class FixedStaggerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight, cls.lanes, cls.secret = mod.validate_inputs()

    def test_task_and_lineage_contract(self) -> None:
        self.assertIn("OVERLAP-AUTHORIZED", mod.TASK_ID)
        self.assertEqual(mod.PREP_COMMIT, "b338003063bd1fd2c29fb70c0af6130987c67ffa")
        self.assertEqual(mod.FAILED_ATTEMPT_COMMIT, "e74afe82e31de6fd76b8e2e77571a3ccd0c378e0")
        self.assertTrue(mod.git_ancestor(mod.PREP_COMMIT))
        self.assertTrue(mod.git_ancestor(mod.FAILED_ATTEMPT_COMMIT))

    def test_fixed_stagger_and_overlap_contract(self) -> None:
        self.assertEqual(mod.OFFSETS_SECONDS, {"lane_1": 0, "lane_2": 480, "lane_3": 960, "lane_4": 1440})
        self.assertEqual(self.preflight["maximum_lane_workers"], 4)
        self.assertEqual(self.preflight["intra_lane_parallelism"], 1)
        self.assertEqual(self.preflight["sdk_retry_count"], 0)
        self.assertTrue(self.preflight["controlled_overlap_authorized"])
        checks = {item["check"]: item for item in self.preflight["checks"]}
        self.assertTrue(checks["previous_schedule_conflict_resolved"]["passed"])
        self.assertTrue(checks["bounded_concurrency_contract"]["passed"])

    def test_exact_locked_scope(self) -> None:
        self.assertEqual(self.preflight["locked_target_count"], 2_000)
        self.assertEqual(set(self.lanes), set(mod.LANES))
        combined = []
        for lane in mod.LANES:
            rows = self.lanes[lane]
            self.assertEqual(len(rows), 500)
            ids = [row["scout_target_id"] for row in rows]
            self.assertEqual(len(set(ids)), 500)
            self.assertTrue(all(row["lane_id"] == lane for row in rows))
            self.assertTrue(all(row["live_run_status"] == "not_started" for row in rows))
            combined.extend(ids)
        self.assertEqual(len(combined), 2_000)
        self.assertEqual(len(set(combined)), 2_000)

    def test_lock_hashes_match(self) -> None:
        for lane in mod.LANES:
            queue = mod.PREP_DIR / f"targeted_scouting_{lane}_queue_500.csv"
            lock = mod.read_json(mod.PREP_DIR / "lane_lockfiles" / f"targeted_scouting_{lane}.lock.json")
            self.assertEqual(mod.sha256_path(queue), lock["queue_sha256"])
            self.assertEqual(mod.id_set_hash(self.lanes[lane]), lock["target_id_set_sha256"])

    def test_candidate_schema_and_forced_statuses(self) -> None:
        target = self.lanes["lane_1"][0]
        item = {
            "source_url_or_locator": "https://example.test/contracts/a.pdf",
            "source_title": "Example agreement",
            "unit_type": "clerical_admin",
        }
        candidate = mod.make_candidate(target, item, mod.query_for_target(target))
        assert candidate
        self.assertEqual(set(candidate), set(mod.CANDIDATE_FIELDS))
        self.assertEqual(candidate["lane_id"], "lane_1")
        self.assertEqual(candidate["scout_target_id"], target["scout_target_id"])
        self.assertEqual(candidate["retrieval_status"], "candidate_only")
        self.assertEqual(candidate["verification_status"], "not_verified")
        self.assertEqual(candidate["extraction_status"], "not_extracted")
        self.assertEqual(candidate["rating_status"], "not_rated")
        self.assertEqual(candidate["causal_status"], "not_causal_evidence")

    def test_final_accounting_normalizes_unit_type_from_lock(self) -> None:
        target = self.lanes["lane_1"][0]
        candidate = mod.make_candidate(target, {
            "source_url_or_locator": "https://example.test/a",
            "source_title": "Example",
            "unit_type": "free-form model elaboration",
        }, "q")
        assert candidate
        states = {lane: mod.empty_state(lane) for lane in mod.LANES}
        states["lane_1"]["candidates"] = [candidate]
        retained, duplicates = mod.deduplicate(states, self.lanes)
        self.assertFalse(duplicates)
        self.assertEqual(retained[0]["unit_type"], target["target_unit_type"])

    def test_prompt_preserves_phase_boundaries(self) -> None:
        target = self.lanes["lane_2"][0]
        prompt = mod.build_prompt(target, mod.query_for_target(target))
        for phrase in ("Candidate-source scouting only", "Do not verify", "download", "extract", "rate evidence", "causal claims", "Do not claim that any source is verified"):
            self.assertIn(phrase, prompt)
        self.assertIn(target["scout_target_id"].split("-")[0], target["scout_target_id"])
        self.assertNotIn("HARVARD_SUBSCRIPTION_KEY", prompt)

    def test_raw_persistence_is_not_in_output_schema(self) -> None:
        self.assertNotIn("prompt", [field.lower() for field in mod.CANDIDATE_FIELDS])
        self.assertNotIn("response", [field.lower() for field in mod.CANDIDATE_FIELDS])
        self.assertIn("raw_prompt_saved", mod.REQUEST_FIELDS)
        self.assertIn("raw_response_saved", mod.REQUEST_FIELDS)
        source = RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("raw_outputs.csv", source)
        self.assertNotIn("write_direct_sdk_sanitized_log", source)
        self.assertIn('error_detail_redacted": f"{type(exc).__name__}; detail omitted"', source)

    def test_parse_json_object(self) -> None:
        self.assertEqual(mod.parse_json_object('{"candidates":[]}'), {"candidates": []})
        self.assertEqual(mod.parse_json_object('```json\n{"candidates":[]}\n```'), {"candidates": []})
        with self.assertRaises(Exception):
            mod.parse_json_object("not json")

    def test_candidate_rejects_incomplete_lead(self) -> None:
        target = self.lanes["lane_3"][0]
        self.assertIsNone(mod.make_candidate(target, {"source_title": "No locator"}, "q"))
        self.assertIsNone(mod.make_candidate(target, {"source_url_or_locator": "locator"}, "q"))

    def test_locator_canonicalization(self) -> None:
        a = mod.canonical_locator("HTTPS://EXAMPLE.COM/path/#fragment")
        b = mod.canonical_locator("https://example.com/path")
        self.assertEqual(a, b)

    def test_transport_stop_gate_is_bounded(self) -> None:
        self.assertEqual(mod.MAX_CONSECUTIVE_TRANSPORT_FAILURES, 2)
        self.assertEqual(mod.TIMEOUT_SECONDS, 180.0)

    def test_preflight_never_discloses_credential(self) -> None:
        rendered = json.dumps(self.preflight)
        self.assertTrue(self.secret)
        self.assertNotIn(self.secret, rendered)
        self.assertEqual(self.preflight["raw_prompts_saved"], 0)
        self.assertEqual(self.preflight["raw_responses_saved"], 0)
        self.assertFalse(self.preflight["global_analysis_readiness"])

    def test_atomic_csv_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.csv"
            mod.write_csv(path, [{"a": "1"}], ["a"])
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [{"a": "1"}])
            self.assertFalse(path.with_suffix(".csv.tmp").exists())

    def test_completed_outputs_when_present(self) -> None:
        decision_path = mod.OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_live_decision.json"
        if not decision_path.exists():
            self.skipTest("live outputs not materialized yet")
        mod.validate_complete()
        decision = mod.read_json(decision_path)
        self.assertIn(decision["decision"], {
            "targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready",
            "targeted_scouting_four_lane_fixed_stagger_live_completed_repair_needed",
        })
        self.assertEqual(decision["locked_target_count"], 2_000)
        self.assertFalse(decision["global_analysis_readiness"])
        self.assertEqual(decision["raw_prompts_saved"], 0)
        self.assertEqual(decision["raw_responses_saved"], 0)
        candidates = mod.read_csv(mod.OUTPUT_DIR / "targeted_scouting_four_lane_candidate_sources.csv")
        for row in candidates:
            self.assertEqual(row["retrieval_status"], "candidate_only")
            self.assertEqual(row["verification_status"], "not_verified")
            self.assertEqual(row["extraction_status"], "not_extracted")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
        starts = mod.read_json(mod.OUTPUT_DIR / "targeted_scouting_four_lane_fixed_stagger_start_times.json")
        self.assertTrue(starts["controlled_overlap_authorized"])
        self.assertTrue(starts["all_lanes_started_after_required_offset"])
        self.assertGreaterEqual(starts["actual_offsets_seconds"]["lane_2"], 480)
        self.assertGreaterEqual(starts["actual_offsets_seconds"]["lane_3"], 960)
        self.assertGreaterEqual(starts["actual_offsets_seconds"]["lane_4"], 1440)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FixedStaggerContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"fixed-stagger checks: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
