#!/usr/bin/env python3
"""Adversarial tests for the bounded 636-row provisional claim review."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import build_dashboard_data as dashboard
import run_compensation_evidence_provisional_claim_review_636 as runner


class InputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.audit = runner.verify_inputs()

    def test_all_twenty_inputs_hashed(self): self.assertEqual(len(self.audit["input_file_hashes"]), 20)
    def test_all_expected_hashes_match(self):
        self.assertEqual(self.audit["input_file_hashes"], runner.EXPECTED_HASHES)
    def test_valid_scope_636(self): self.assertEqual(self.audit["valid_summary_rows"], 636)
    def test_excluded_scope_7(self): self.assertEqual(self.audit["excluded_quarantine_rows"], 7)
    def test_scope_reconciles_643(self): self.assertEqual(self.audit["valid_plus_excluded_rows"], 643)
    def test_positive_cells_722(self): self.assertEqual(self.audit["positive_attribute_cells"], 722)
    def test_taxonomy_v1_1(self): self.assertEqual(self.audit["attribute_taxonomy_version"], "v1.1")
    def test_attribute_count_14(self): self.assertEqual(self.audit["attribute_count"], 14)
    def test_quantitative_future_lane_862(self): self.assertEqual(self.audit["quantitative_rows_preserved_not_analyzed"], 862)
    def test_no_model_call(self): self.assertFalse(self.audit["gabriel_api_or_model_called"])
    def test_global_readiness_false(self): self.assertFalse(self.audit["global_analysis_readiness"])
    def test_direction_reconciles(self): self.assertEqual(sum(self.audit["direction"].values()), 722)
    def test_strength_reconciles(self): self.assertEqual(sum(self.audit["strength"].values()), 722)
    def test_relevance_reconciles(self): self.assertEqual(sum(self.audit["relevance"].values()), 722)
    def test_scout_reconciles(self): self.assertEqual(sum(self.audit["scout"].values()), 636)
    def test_safety_advantage_zero(self): self.assertEqual(int(self.audit["presence"]["safety_advantage_signal"]["present_count"]), 0)
    def test_non_safety_constraint_zero(self): self.assertEqual(int(self.audit["presence"]["non_safety_constraint_signal"]["present_count"]), 0)


class ClaimRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claims = runner.build_claims()
        cls.counts = Counter(row["claim_type"] for row in cls.claims)
        cls.by_id = {row["claim_id"]: row for row in cls.claims}

    def test_claim_count_35(self): self.assertEqual(len(self.claims), 35)
    def test_claim_ids_unique(self): self.assertEqual(len(self.by_id), 35)
    def test_all_five_types(self): self.assertEqual(set(self.counts), set(runner.CLAIM_TYPES))
    def test_documentary_count_9(self): self.assertEqual(self.counts["supported_documentary_mechanism_claim"], 9)
    def test_direct_count_5(self): self.assertEqual(self.counts["supported_direct_text_claim"], 5)
    def test_causal_candidate_count_5(self): self.assertEqual(self.counts["provisional_causal_candidate_claim"], 5)
    def test_more_data_count_10(self): self.assertEqual(self.counts["needs_more_data"], 10)
    def test_not_allowed_count_6(self): self.assertEqual(self.counts["not_allowed"], 6)
    def test_all_required_fields_nonblank(self):
        self.assertTrue(all(all(row[field].strip() for field in runner.CLAIM_FIELDS) for row in self.claims))
    def test_all_boundaries_present(self): self.assertTrue(all(row["boundary_language"] for row in self.claims))
    def test_all_non_forbidden_claims_corpus_bounded(self):
        self.assertTrue(all("636 valid-rated" in row["boundary_language"] for row in self.claims))
    def test_causal_candidates_explicitly_provisional(self):
        rows = [row for row in self.claims if row["claim_type"] == "provisional_causal_candidate_claim"]
        self.assertTrue(all("provisional plausible mechanism to investigate" in row["claim_text"].casefold() for row in rows))
    def test_needs_more_data_insufficient(self):
        self.assertTrue(all(row["strength"] == "insufficient" for row in self.claims if row["claim_type"] == "needs_more_data"))
    def test_not_allowed_insufficient(self):
        self.assertTrue(all(row["strength"] == "insufficient" for row in self.claims if row["claim_type"] == "not_allowed"))
    def test_safety_advantage_not_forced_forward(self): self.assertEqual(self.by_id["need_01"]["claim_type"], "needs_more_data")
    def test_non_safety_constraint_not_forced_forward(self): self.assertEqual(self.by_id["need_02"]["claim_type"], "needs_more_data")
    def test_quantitative_only_future_lane(self):
        self.assertIn("future lane", self.by_id["need_10"]["evidence_basis"])
        self.assertIn("no analysis", self.by_id["need_10"]["next_data_needed"])
    def test_registry_contains_no_evidence_ids_or_rows(self):
        self.assertNotIn("evidence_id", runner.CLAIM_FIELDS)
        self.assertNotIn("row_document_id", runner.CLAIM_FIELDS)
    def test_forbidden_phrases_absent(self):
        text = "\n".join(row["claim_text"].casefold() for row in self.claims)
        self.assertFalse(any(phrase in text for phrase in runner.FORBIDDEN_PHRASES))
    def test_mutated_causal_candidate_fails(self):
        rows = [dict(row) for row in self.claims]
        rows[14]["claim_text"] = "Mechanism language exists."
        with self.assertRaisesRegex(RuntimeError, "not explicitly provisional"):
            runner.validate_claims(rows)
    def test_blank_boundary_fails(self):
        rows = [dict(row) for row in self.claims]; rows[0]["boundary_language"] = ""
        with self.assertRaisesRegex(RuntimeError, "blank"):
            runner.validate_claims(rows)
    def test_duplicate_claim_id_fails(self):
        rows = [dict(row) for row in self.claims]; rows[1]["claim_id"] = rows[0]["claim_id"]
        with self.assertRaisesRegex(RuntimeError, "unique"):
            runner.validate_claims(rows)
    def test_unsupported_strength_fails(self):
        rows = [dict(row) for row in self.claims]; rows[19]["strength"] = "weak"
        with self.assertRaisesRegex(RuntimeError, "assigned evidence strength"):
            runner.validate_claims(rows)


class MaterializedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = runner.DEFAULT_OUTPUT_DIR
        cls.decision = runner.read_json(cls.out / "provisional_claim_review_636_decision.json")
        cls.summary = runner.read_json(cls.out / "provisional_claim_review_claim_registry_summary.json")
        cls.invariants = runner.read_json(cls.out / "provisional_claim_review_636_invariant_checks.json")
        cls.rows = runner.read_csv(cls.out / "provisional_claim_review_claim_registry.csv")

    def test_outputs_complete(self): self.assertTrue(runner.completed(self.out))
    def test_decision_exact(self): self.assertEqual(self.decision["decision"], runner.DECISION)
    def test_targeted_scouting_recommended(self): self.assertTrue(self.decision["targeted_scouting_restart_recommended"])
    def test_claim_memo_not_next(self): self.assertFalse(self.decision["claim_memo_allowed_next"])
    def test_materialized_claim_count(self): self.assertEqual(len(self.rows), 35)
    def test_summary_counts_match_rows(self): self.assertEqual(self.summary["claim_type_counts"], dict(Counter(row["claim_type"] for row in self.rows)))
    def test_invariants_pass(self): self.assertTrue(self.invariants["all_invariants_passed"])
    def test_global_readiness_false(self): self.assertFalse(self.decision["global_analysis_readiness"])
    def test_no_model_calls(self): self.assertFalse(self.decision["gabriel_api_or_model_called"])
    def test_quantitative_not_analyzed(self): self.assertEqual(self.decision["quantitative_rows_preserved_not_analyzed"], 862)
    def test_no_raw_payload_files(self):
        names = {path.name.casefold() for path in self.out.iterdir()}
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))
    def test_future_prompt_phase_boundaries(self):
        text = (self.out / "next_targeted_scouting_restart_from_provisional_claim_review_prompt.md").read_text()
        for phrase in ("Scouting is not verification", "Do not run source review", "Do not download documents", "Do not analyze the 862-row quantitative lane", "Do not calculate wage gaps", "Keep global analysis readiness false"):
            self.assertIn(phrase, text)
    def test_quantitative_doc_disclaims_analysis(self):
        text = (self.out / "quantitative_triage_recommendation.md").read_text()
        self.assertIn("No quantitative row was read or analyzed", text)
    def test_sparse_docs_include_zero_signals(self):
        text = (self.out / "sparse_mechanisms_to_target_in_next_scout.md").read_text()
        self.assertIn("safety advantage (0)", text); self.assertIn("non-safety constraint (0)", text)
    def test_partial_outputs_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=runner.ANALYSIS_ROOT) as tmp:
            path = Path(tmp); (path / "partial.txt").write_text("partial")
            with self.assertRaisesRegex(RuntimeError, "partial outputs"):
                runner.output_guard(path, True)
    def test_non_analysis_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "under docs/analysis"):
                runner.output_guard(Path(tmp), False)
    def test_resume_hashes_stable(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir() if p.is_file()}
        self.assertTrue(runner.completed(self.out))
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir() if p.is_file()}
        self.assertEqual(before, after)
    def test_runner_has_no_model_or_network_calls(self):
        source = Path(runner.__file__).read_text()
        for token in ("direct_sdk_batch(", "load_subscription_key(", "requests.get(", "requests.post(", "urlopen("):
            self.assertNotIn(token, source)
    def test_stress_inventory_matches_report(self):
        inventory = runner.read_json(self.out / "provisional_claim_review_636_regression_test_inventory.json")
        report = (self.out / "provisional_claim_review_636_stress_test_report.md").read_text()
        self.assertIn(f"{inventory['failure_mode_count']}/{inventory['failure_mode_count']} passed", report)


class DashboardTests(unittest.TestCase):
    def test_dashboard_status_passes(self):
        completed, decision = dashboard.provisional_claim_review_636_status()
        self.assertTrue(completed); self.assertEqual(decision["claim_rows"], 35)
    def test_dashboard_global_readiness_false(self):
        _, decision = dashboard.provisional_claim_review_636_status()
        self.assertFalse(decision["global_analysis_readiness"])
    def test_dashboard_targeted_scouting_next(self):
        _, decision = dashboard.provisional_claim_review_636_status()
        self.assertTrue(decision["targeted_scouting_restart_recommended"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
