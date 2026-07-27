#!/usr/bin/env python3
"""Regression tests for the deterministic four-lane candidate review."""

from __future__ import annotations

import ast
import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run_targeted_scouting_four_lane_candidate_review.py"
SPEC = importlib.util.spec_from_file_location("candidate_review", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)
DASHBOARD_RUNNER = ROOT / "scripts/build_dashboard_data.py"
DASHBOARD_SPEC = importlib.util.spec_from_file_location("candidate_review_dashboard", DASHBOARD_RUNNER)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
sys.modules[DASHBOARD_SPEC.name] = dashboard
DASHBOARD_SPEC.loader.exec_module(dashboard)


class CandidateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows, cls.hashes, cls.input_fields = mod.verify_inputs()
        cls.output_exists = mod.OUTPUT_DIR.exists()

    def test_task_lineage_and_decision(self) -> None:
        self.assertEqual(mod.INPUT_COMMIT, "d3a2a094b834986037ba051c87a417e0a9712022")
        self.assertEqual(mod.EXPECTED_TOTAL, 4_228)
        self.assertEqual(mod.DECISION, "targeted_scouting_four_lane_candidate_review_completed_verification_ready")

    def test_immutable_hashes_match(self) -> None:
        for relative, expected in mod.EXPECTED_HASHES.items():
            self.assertEqual(self.hashes[relative], expected)

    def test_exact_scope_and_lane_counts(self) -> None:
        self.assertEqual(len(self.rows), 4_228)
        counts = {lane: sum(row["lane_id"] == lane for row in self.rows) for lane in mod.EXPECTED_LANES}
        self.assertEqual(counts, mod.EXPECTED_LANES)

    def test_candidate_ids_unique(self) -> None:
        self.assertEqual(len({row["candidate_id"] for row in self.rows}), 4_228)

    def test_candidate_only_statuses(self) -> None:
        for row in self.rows:
            self.assertEqual(tuple(row[field] for field in mod.STATUS_FIELDS), mod.STATUS_VALUES)

    def test_scoring_is_deterministic(self) -> None:
        row = self.rows[0]
        self.assertEqual(mod.score_candidate(row), mod.score_candidate(dict(row)))

    def test_scoring_has_fixed_dimensions_and_range(self) -> None:
        result = mod.score_candidate(self.rows[0])
        score_fields = [field for field in mod.QUALITY_EXTRA_FIELDS if field.endswith("_score")]
        self.assertEqual(len(score_fields), 11)  # ten dimensions plus the total
        self.assertGreaterEqual(result["candidate_quality_score"], 0)
        self.assertLessEqual(result["candidate_quality_score"], 100)

    def test_target_reason_does_not_create_mechanism_relevance(self) -> None:
        row = dict(self.rows[0])
        row.update({"source_title": "Record", "notes": "", "occupation_group": "", "bargaining_unit_name": ""})
        row["reason_selected"] = "non safety constraint salary wage contract agreement"
        self.assertEqual(mod.score_candidate(row)["mechanism_relevance_score"], 0)

    def test_quality_thresholds(self) -> None:
        observed = {mod.score_candidate(row)["candidate_quality_label"] for row in self.rows}
        self.assertEqual(observed, {
            "verification_ready_high", "verification_ready_medium", "verification_ready_low",
            "repair_or_review_needed", "deprioritize_this_phase",
        })

    def test_canonical_locator_removes_only_tracking_noise(self) -> None:
        left = mod.canonical_locator("HTTPS://WWW.Example.ORG/a//b/?utm_source=x&id=7#part")
        right = mod.canonical_locator("https://example.org/a/b?id=7")
        self.assertEqual(left, right)
        self.assertIn("id=7", left)

    def test_review_deduplication_is_conservative(self) -> None:
        scored = [mod.score_candidate(row) for row in self.rows]
        deduped, duplicates, summary = mod.review_duplicates(scored)
        self.assertEqual(len(deduped), 4_225)
        self.assertEqual(summary["review_locator_duplicate_groups"], 3)
        self.assertEqual(summary["review_locator_duplicate_exclusions"], 3)
        self.assertEqual(summary["possible_same_city_title_groups"], 9)
        self.assertGreaterEqual(len(duplicates), 6)

    def test_title_similarity_is_not_automatic_exclusion(self) -> None:
        scored = [mod.score_candidate(row) for row in self.rows]
        _, duplicate_rows, _ = mod.review_duplicates(scored)
        title_rows = [row for row in duplicate_rows if row["duplicate_basis"].startswith("same_city")]
        self.assertTrue(title_rows)
        self.assertTrue(all(row["review_status"] == "manual_metadata_comparison_only" for row in title_rows))

    def test_no_network_or_model_client_imports(self) -> None:
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports & {"requests", "httpx", "aiohttp", "openai", "huit", "selenium", "playwright"})

    def test_no_verification_or_download_code_path(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for forbidden in ("urlopen(", "requests.get(", "client.responses.create(", "download_document(", "gabriel.codify"):
            self.assertNotIn(forbidden, source)

    def test_required_output_inventory_is_complete(self) -> None:
        self.assertEqual(len(mod.REQUIRED_OUTPUTS), 36)
        self.assertIn("next_targeted_source_verification_prompt.md", mod.REQUIRED_OUTPUTS)

    def test_completed_output_contract(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        mod.validate_complete()
        decision = mod.read_json(mod.OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json")
        self.assertEqual(decision["candidate_rows_reviewed"], 4_228)
        self.assertEqual(decision["model_api_calls"], 0)
        self.assertEqual(decision["urls_opened"], 0)
        self.assertEqual(decision["sources_verified"], 0)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_verification_queue_excludes_tier_d_and_preserves_status(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        queue = mod.read_csv(mod.OUTPUT_DIR / "targeted_scouting_four_lane_verification_ready_queue.csv")
        self.assertTrue(queue)
        self.assertTrue(all(row["verification_priority_tier"] in {"tier_a", "tier_b", "tier_c"} for row in queue))
        self.assertTrue(all(row["verification_status"] == "not_verified" for row in queue))
        self.assertTrue(all(row["retrieval_status"] == "candidate_only" for row in queue))

    def test_output_scope_reconciles(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        scope = mod.read_json(mod.OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_scope_summary.json")
        self.assertEqual(scope["candidate_rows_reviewed"], 4_228)
        self.assertEqual(scope["candidate_id_unique_count"], 4_228)
        self.assertEqual(scope["lane_candidate_counts"], mod.EXPECTED_LANES)
        self.assertEqual(scope["candidate_only_rows"], 4_228)
        self.assertEqual(scope["not_verified_rows"], 4_228)

    def test_priority_counts_reconcile_after_review_deduplication(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        decision = mod.read_json(mod.OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_decision.json")
        self.assertEqual(sum(decision["verification_priority_tier_counts"].values()), decision["deduped_review_rows"])
        self.assertEqual(decision["verification_priority_tier_counts"].get("tier_d", 0) + decision["verification_ready_count"], decision["deduped_review_rows"])

    def test_future_prompt_preserves_phase_boundaries(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        text = (mod.OUTPUT_DIR / "next_targeted_source_verification_prompt.md").read_text(encoding="utf-8")
        for phrase in (
            "This candidate review did not verify any source", "separately authorized verification stage",
            "must not download documents", "run OCR", "extract text", "ingest", "codify",
            "calculate wage gaps", "regressions", "causal claims", "global analysis readiness true",
        ):
            self.assertIn(phrase, text)

    def test_partial_outputs_cannot_masquerade_as_complete(self) -> None:
        old = mod.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.OUTPUT_DIR = Path(temp)
            (mod.OUTPUT_DIR / mod.REQUIRED_OUTPUTS[0]).touch()
            with self.assertRaises(RuntimeError):
                mod.validate_complete()
        mod.OUTPUT_DIR = old

    def test_dashboard_never_promotes_global_readiness(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        invariants = mod.read_json(mod.OUTPUT_DIR / "targeted_scouting_four_lane_candidate_review_invariant_checks.json")
        self.assertTrue(invariants["global_analysis_readiness_false"])
        self.assertTrue(invariants["no_live_search_or_model_api_call"])

    def test_dashboard_candidate_review_gate(self) -> None:
        completed, decision = dashboard.targeted_scouting_four_lane_candidate_review_status()
        self.assertTrue(completed)
        self.assertEqual(decision["verification_ready_count"], 3_474)
        self.assertTrue(decision["source_verification_ready_next"])
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_generated_status_remains_closed(self) -> None:
        readiness = mod.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        calibration = mod.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        self.assertEqual(readiness["overall_status"], "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready_global_analysis_closed")
        self.assertEqual(calibration["calibration_phase"], "quantitative_direct_text_claim_triage_862_completed_mechanism_linkage_ready")
        self.assertTrue(calibration["targeted_source_verification_ready_next"])
        self.assertTrue(calibration["targeted_source_verification_completed"])
        self.assertFalse(calibration["analysis_facing_promotion_allowed"])
        self.assertNotIn('"global_analysis_readiness": true', json.dumps(readiness, sort_keys=True).casefold())

    def test_no_raw_prompt_or_response_outputs(self) -> None:
        if not self.output_exists:
            self.skipTest("generated outputs not present")
        names = [path.name.casefold() for path in mod.OUTPUT_DIR.rglob("*") if path.is_file()]
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CandidateReviewTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"candidate-review checks: {passed}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
