#!/usr/bin/env python3
"""Adversarial tests for the compensation readiness accelerator."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_pipeline_hardening_readiness_accelerator as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


class GuardrailFixtureTests(unittest.TestCase):
    def test_failure_inventory_covers_all_required_modes(self):
        modes = {row[1] for row in runner.FAILURE_MODES}
        required = {
            "ambiguous_span", "unavailable_span", "no_text_layer", "multiple_identical_spans",
            "forbidden_page_access", "ocr_later_attempted_access", "wrong_content_hash",
            "missing_retained_pdf_path", "full_page_text_leakage",
            "duplicate_qualitative_observation_id", "span_hash_offset_corruption",
            "duplicate_non_base_lineage_header", "embedded_newline_csv_record",
            "mixed_historical_join", "non_base_wage_misroute", "quantitative_range",
            "quantitative_formula_pair_multiplier_hours", "missing_cycle", "conflicting_cycle",
            "missing_occupation", "conflicting_occupation", "dashboard_false_readiness",
            "relay_missing_inspection_fields", "future_prompt_missing_hard_constraints",
            "stage_attempts_phase_jump",
        }
        self.assertTrue(required <= modes)
        self.assertGreaterEqual(len(runner.FAILURE_MODES), 25)

    def test_no_text_layer_returns_controlled_status(self):
        self.assertEqual(runner.validate_page_access_fixture(requested_page=3, approved_pages={3}, ocr_later=False, text="  "), "no_text_layer")

    def test_forbidden_page_access_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Non-target"):
            runner.validate_page_access_fixture(requested_page=4, approved_pages={3}, ocr_later=False, text="short text")

    def test_ocr_later_access_fails(self):
        with self.assertRaisesRegex(RuntimeError, "OCR-later"):
            runner.validate_page_access_fixture(requested_page=3, approved_pages={3}, ocr_later=True, text="short text")

    def test_wrong_content_hash_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Wrong retained"):
            runner.validate_identity_fixture(expected_hash="a", actual_hash="b", retained_path="local.pdf")

    def test_missing_retained_path_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Missing retained"):
            runner.validate_identity_fixture(expected_hash="a", actual_hash="a", retained_path="")

    def test_exact_span_round_trip_passes(self):
        page = "Prefix. Wages increase two percent. Suffix."
        span = "Wages increase two percent."
        start = page.index(span)
        runner.validate_span_fixture(span, start, start + len(span), hashlib.sha256(span.encode()).hexdigest(), page)

    def test_span_hash_corruption_fails(self):
        page = "Prefix. Wages increase two percent. Suffix."
        span = "Wages increase two percent."
        start = page.index(span)
        with self.assertRaisesRegex(RuntimeError, "hash"):
            runner.validate_span_fixture(span, start, start + len(span), "0" * 64, page)

    def test_span_offset_corruption_fails(self):
        page = "Prefix. Wages increase two percent. Suffix."
        span = "Wages increase two percent."
        with self.assertRaisesRegex(RuntimeError, "offset"):
            runner.validate_span_fixture(span, 0, len(span), hashlib.sha256(span.encode()).hexdigest(), page)

    def test_full_page_text_leakage_fails(self):
        page = "entire page"
        with self.assertRaisesRegex(RuntimeError, "Full-page"):
            runner.validate_span_fixture(page, 0, len(page), hashlib.sha256(page.encode()).hexdigest(), page)

    def test_historical_mixed_join_cannot_be_active(self):
        with self.assertRaisesRegex(RuntimeError, "Historical"):
            runner.validate_mixed_membership("historical_inactive", treated_as_active=True)

    def test_duplicate_lineage_position_parse_passes(self):
        header = ["id", "source_quantitative_observation_id", "source_mixed_join_key", "source_quantitative_observation_id", "source_mixed_join_key"]
        parsed = runner.parse_duplicate_lineage_fixture(header, ["n1", "q1", "m1", "q1", "m1"])
        self.assertEqual(parsed["package_source_quantitative_observation_id"], "q1")
        self.assertEqual(parsed["repair_source_mixed_join_key"], "m1")

    def test_duplicate_lineage_disagreement_fails(self):
        header = ["id", "source_quantitative_observation_id", "source_mixed_join_key", "source_quantitative_observation_id", "source_mixed_join_key"]
        with self.assertRaisesRegex(RuntimeError, "disagree"):
            runner.parse_duplicate_lineage_fixture(header, ["n1", "q1", "m1", "q2", "m1"])

    def test_embedded_newline_csv_round_trips_one_record(self):
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=["id", "reason"], lineterminator="\n")
        writer.writeheader(); writer.writerow({"id": "wasco", "reason": "line one\nline two"})
        rows = list(csv.DictReader(io.StringIO(buffer.getvalue(), newline="")))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "line one\nline two")

    def test_quantitative_range_fixture_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Ambiguous quantitative"):
            runner.validate_quantitative_candidate({"accelerator_fixture": "unsafe", "raw_value": "$20-$25 range"})

    def test_quantitative_formula_pair_multiplier_hours_fails(self):
        for raw in ("formula CPI*1.02", "current/new pair", "1.5 multiplier", "2080 hours"):
            with self.assertRaisesRegex(RuntimeError, "Ambiguous quantitative"):
                runner.validate_quantitative_candidate({"accelerator_fixture": "unsafe", "raw_value": raw})

    def test_non_base_outcome_misroute_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Non-base"):
            runner.validate_lane_separation([{"base_wage_outcome_eligible": "true"}], [])

    def test_reference_outcome_misroute_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Reference"):
            runner.validate_lane_separation([], [{"outcome_eligible": "true"}])

    def test_dashboard_true_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness true"):
            runner.validate_dashboard_state({"analysis_readiness": True, "overall_status": "analysis_ready"})

    def test_repair_dashboard_false_passes(self):
        runner.validate_dashboard_state({"analysis_readiness": False, "overall_status": "repair_analysis_closed"})

    def test_relay_missing_fields_fails(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            runner.validate_relay_record({"commit_hash": "abc"})

    def test_relay_complete_passes(self):
        runner.validate_relay_record({key: "ok" for key in runner.RELAY_REQUIRED})

    def test_future_prompt_missing_constraints_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing hard constraints"):
            runner.validate_future_prompt("Do not run this prompt without separate explicit user authorization.")

    def test_future_prompt_contract_is_case_insensitive(self):
        text = "\n".join(phrase.upper() for phrase in runner.PROMPT_REQUIRED_PHRASES)
        runner.validate_future_prompt(text)

    def test_stage_phase_jump_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden phase jump"):
            runner.validate_stage_transition("repair", "causal_analysis")

    def test_allowed_stage_transition_passes(self):
        runner.validate_stage_transition("repair", "limited_promotion_prompt")

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial checkpoint"):
            runner.validate_checkpoint({"status": "partial", "processed": 10, "expected": 20})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 20, "expected": 20})

    def test_forbidden_output_boundary_fails(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/accelerator")


class ImmutableLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.tables = runner.validate_material_inputs()
        cls.scopes = runner.qualitative_scope_metrics(cls.tables["exact"]["rows"])

    def test_five_package_hashes_pass(self):
        self.assertTrue(all(self.hashes[key] == expected for key, (_, expected) in runner.PACKAGE_LEDGER_HASHES.items()))

    def test_all_17_hashes_pass(self):
        self.assertEqual(len(self.hashes), 17)

    def test_qualitative_tiers_reconcile(self):
        rows = self.tables["qualitative"]["rows"]
        from collections import Counter
        self.assertEqual(Counter(row["evidence_contract_tier"] for row in rows), {"exact_span_coded_candidate": 759, "ambiguous_exact_span_navigation": 614, "unavailable_span_navigation": 581})

    def test_cycle_matching_counts(self):
        rows = self.tables["cycle"]["rows"]
        self.assertEqual(sum(row["cycle_bridge_status"] == "established_single_exact_pair" for row in rows), 1359)
        self.assertEqual(sum(bool(row["matched_set_id"]) for row in rows), 203)
        self.assertEqual(len({row["matched_set_id"] for row in rows if row["matched_set_id"]}), 91)

    def test_occupation_counts(self):
        rows = self.tables["occupation"]["rows"]
        self.assertEqual(sum(bool(row["controlled_occupation_class"]) for row in rows), 1458)
        self.assertEqual(sum(not row["controlled_occupation_class"] for row in rows), 368)

    def test_lane_counts(self):
        self.assertEqual((len(self.tables["quantitative"]["rows"]), len(self.tables["quantitative_exception"]["rows"]), len(self.tables["non_base"]["rows"]), len(self.tables["reference"]["rows"])), (862, 1045, 4733, 345))

    def test_conflicts_quarantined(self):
        rows = self.tables["conflict"]["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(int(row["observation_count"]) for row in rows), 5)
        self.assertTrue(all(row["resolution_status"] == "unresolved" for row in rows))

    def test_provenance_bridge_complete(self):
        rows = self.tables["provenance"]["rows"]
        self.assertEqual(len(rows), 1826)
        self.assertEqual(len({row["document_identity_id"] for row in rows}), 1826)

    def test_simulation_scope_counts(self):
        self.assertEqual(self.scopes, {"exact_span_evidence_universe": 759, "limited_contract_eligible": 643, "exact_cycle_eligible": 453, "controlled_occupation_eligible": 438, "matched_set_eligible": 77, "strict_primary_matched_eligible": 56})

    def test_dry_run_is_no_write(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "out"
            result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)], cwd=ROOT, capture_output=True, text=True, check=True)
            self.assertFalse(out.exists())
            self.assertEqual(json.loads(result.stdout)["writes"], 0)


class MaterializedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = json.loads((OUTPUT / "pipeline_hardening_readiness_accelerator_decision.json").read_text())
        cls.invariants = json.loads((OUTPUT / "pipeline_hardening_invariant_checks.json").read_text())
        with (OUTPUT / "pipeline_readiness_master_blocker_registry.csv").open(newline="", encoding="utf-8-sig") as handle:
            cls.blockers = list(csv.DictReader(handle))
        cls.fixtures = json.loads((OUTPUT / "pipeline_failure_fixture_inventory.json").read_text())

    def test_decision_limited_promotion_only(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["limited_promotion_allowed_next"])
        self.assertFalse(self.decision["analysis_readiness"])
        self.assertFalse(self.decision["analysis_readiness_review_allowed_next"])

    def test_blocker_registry_required_schema(self):
        required = {"blocker_id", "lane", "source_file", "row_count", "affected_observation_ids_or_grouped_count", "severity", "deterministic_repair_possible", "repair_attempted", "repair_result", "residual_status", "next_action", "downstream_impact", "blocks_global_readiness", "blocks_limited_readiness_only", "quarantined"}
        self.assertEqual(set(self.blockers[0]), required)
        self.assertGreaterEqual(len(self.blockers), 15)

    def test_fixture_inventory_reconciles(self):
        self.assertEqual(self.fixtures["fixture_count"], len(runner.FAILURE_MODES))
        self.assertGreaterEqual(self.fixtures["fixture_count"], 25)

    def test_accelerated_views_byte_identical(self):
        for key, filename in runner.OUTPUT_COPIES.items():
            self.assertEqual(runner.INPUTS[key][0].read_bytes(), (OUTPUT / filename).read_bytes(), key)

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])

    def test_prompt_contract_passes(self):
        runner.validate_future_prompt((OUTPUT / "next_limited_qualitative_promotion_prompt.md").read_text())

    def test_no_forbidden_output_fields(self):
        for filename in runner.OUTPUT_COPIES.values():
            fields, _ = runner.read_csv(OUTPUT / filename)
            self.assertFalse(set(fields) & runner.FORBIDDEN_FIELDS)

    def test_resume_idempotent(self):
        result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT, capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["resume_reused"])
        self.assertEqual(payload["writes"], 0)

    def test_dashboard_global_readiness_false(self):
        payload = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text())
        self.assertIn("analysis_closed", payload["overall_status"])
        self.assertFalse(payload["stage_availability"]["wage_extraction_stage"]["analysis_facing_promotion_allowed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
