#!/usr/bin/env python3
"""Fail-closed tests for the limited exact-span readiness review."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_limited_exact_span_qualitative_readiness_review as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class RowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exact_fields, cls.exact = read_csv(runner.INPUTS["exact"])
        cls.ambiguous_fields, cls.ambiguous = read_csv(runner.INPUTS["ambiguous"])
        cls.unavailable_fields, cls.unavailable = read_csv(runner.INPUTS["unavailable"])
        cls.combined_fields, cls.combined = read_csv(runner.INPUTS["combined"])

    def test_exact_fixture_valid(self):
        runner.validate_exact_row(self.exact[0])

    def test_missing_provenance_fails(self):
        row = copy.deepcopy(self.exact[0]); row["source_review_id"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing provenance"):
            runner.validate_exact_row(row)

    def test_candidate_tier_contamination_fails(self):
        row = copy.deepcopy(self.exact[0]); row["evidence_contract_tier"] = "ambiguous_exact_span_navigation"
        with self.assertRaisesRegex(RuntimeError, "tier contamination"):
            runner.validate_exact_row(row)

    def test_false_candidate_flag_fails(self):
        row = copy.deepcopy(self.exact[0]); row["evidence_contract_candidate_eligible"] = "false"
        with self.assertRaisesRegex(RuntimeError, "eligibility"):
            runner.validate_exact_row(row)

    def test_span_hash_drift_fails(self):
        row = copy.deepcopy(self.exact[0]); row["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "span hash"):
            runner.validate_exact_row(row)

    def test_span_offset_drift_fails(self):
        row = copy.deepcopy(self.exact[0]); row["span_end"] = str(int(row["span_end"]) + 1)
        with self.assertRaisesRegex(RuntimeError, "round-trip"):
            runner.validate_exact_row(row)

    def test_multiline_span_fails(self):
        row = copy.deepcopy(self.exact[0]); row["literal_verbatim_evidence_span"] += "\nleak"
        with self.assertRaisesRegex(RuntimeError, "multiline"):
            runner.validate_exact_row(row)

    def test_retained_hash_mismatch_fails(self):
        row = copy.deepcopy(self.exact[0]); row["retained_content_hash"] = "f" * 64
        with self.assertRaisesRegex(RuntimeError, "Retained content hash"):
            runner.validate_exact_row(row)

    def test_page_pointer_mismatch_fails(self):
        row = copy.deepcopy(self.exact[0]); row["page_number"] = str(int(row["page_number"]) + 1)
        with self.assertRaisesRegex(RuntimeError, "page pointer"):
            runner.validate_exact_row(row)

    def test_inactive_candidate_fails(self):
        row = copy.deepcopy(self.exact[0]); row["current_active"] = "false"
        with self.assertRaisesRegex(RuntimeError, "current-active"):
            runner.validate_exact_row(row)

    def test_ambiguous_candidate_leak_fails(self):
        row = copy.deepcopy(self.ambiguous[0]); row["evidence_contract_candidate_eligible"] = "true"
        with self.assertRaisesRegex(RuntimeError, "entered coded"):
            runner.validate_navigation_row(row, tier="ambiguous_exact_span_navigation", status="span_ambiguous_multiple_candidates")

    def test_unavailable_exact_qa_leak_fails(self):
        row = copy.deepcopy(self.unavailable[0]); row["span_qa_pass"] = "true"
        with self.assertRaisesRegex(RuntimeError, "exact-span coded"):
            runner.validate_navigation_row(row, tier="unavailable_span_navigation", status="span_unavailable_or_unverified")

    def test_tier_count_drift_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Tier count"):
            runner.validate_tiers(self.exact_fields, self.exact[:-1], self.ambiguous_fields, self.ambiguous, self.unavailable_fields, self.unavailable, self.combined_fields, self.combined)

    def test_duplicate_id_fails(self):
        exact = copy.deepcopy(self.exact); exact[1]["qualitative_observation_id"] = exact[0]["qualitative_observation_id"]
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            runner.validate_tiers(self.exact_fields, exact, self.ambiguous_fields, self.ambiguous, self.unavailable_fields, self.unavailable, self.combined_fields, self.combined)

    def test_forbidden_payload_column_fails(self):
        fields = self.exact_fields + ["full_page_text"]
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_tiers(fields, self.exact, self.ambiguous_fields, self.ambiguous, self.unavailable_fields, self.unavailable, self.combined_fields, self.combined)


class FrozenLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.tables = runner.load_and_validate()
        cls.metrics = runner.review_metrics(cls.tables["exact"])
        cls.carried = runner.carried_counts()

    def test_all_21_hashes_pass(self):
        self.assertEqual(len(self.hashes), 21)

    def test_tier_counts_reconcile(self):
        self.assertEqual((len(self.tables["exact"]), len(self.tables["ambiguous"]), len(self.tables["unavailable"]), len(self.tables["combined"])), (759, 614, 581, 1954))

    def test_exact_ids_unique(self):
        ids = [row["qualitative_observation_id"] for row in self.tables["exact"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exact_qa_all_pass(self):
        self.assertEqual(self.metrics["exact_candidate_span_qa_pass"], 759)
        self.assertEqual(self.metrics["provenance_complete"], 759)
        self.assertEqual(self.metrics["identity_bridge_complete"], 759)

    def test_qa_layers_are_separate(self):
        fields, _ = read_csv(runner.INPUTS["exact"])
        self.assertIn("qa_status", fields)
        self.assertIn("span_qa_status", fields)
        self.assertEqual(self.metrics["current_qa_status"], {"provisional_unverified": 666, "needs_review": 93})

    def test_matching_restrictions_measured(self):
        self.assertEqual(self.metrics["exact_cycle_supported"], 533)
        self.assertEqual(self.metrics["cycle_missing_or_ambiguous"], 226)
        self.assertEqual(self.metrics["exact_matched_set_supported"], 85)

    def test_occupation_restrictions_measured(self):
        self.assertEqual(self.metrics["controlled_occupation_complete"], 520)
        self.assertEqual(self.metrics["controlled_occupation_missing"], 239)

    def test_historical_mixed_never_active(self):
        self.assertEqual(self.metrics["historical_mixed_memberships"], 16)
        self.assertEqual(self.metrics["mixed_membership_status"]["active"], 381)

    def test_other_and_missing_detail_measured(self):
        self.assertEqual(self.metrics["mechanism_type_other_rows"], 8)
        self.assertEqual(self.metrics["rows_without_structured_mechanism_detail"], 4)

    def test_carried_counts(self):
        self.assertEqual(self.carried, {"quantitative_candidate": 862, "quantitative_exception": 1045, "non_base": 4733, "reference": 345, "conflicts": 2, "conflict_observations": 5})

    def test_two_conflicts_remain_explicit(self):
        self.assertEqual(len(self.tables["conflicts"]), 2)
        self.assertTrue(all(row["resolution_status"] == "unresolved" for row in self.tables["conflicts"]))

    def test_no_pdf_or_model_imports(self):
        source = Path(runner.__file__).read_text(encoding="utf-8")
        for forbidden in ("import fitz", "import pdfplumber", "from pypdf", "import openai", "import gabriel"):
            self.assertNotIn(forbidden, source)

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/unsafe-review")

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as temp:
            out = Path(temp) / "review"
            result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)], cwd=ROOT, text=True, capture_output=True, check=True)
            self.assertFalse(out.exists())
            self.assertEqual(json.loads(result.stdout)["writes"], 0)


class MaterializedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = json.loads((OUTPUT / runner.OUTPUTS["decision"]).read_text())
        cls.contract = json.loads((OUTPUT / runner.OUTPUTS["contract_audit"]).read_text())
        cls.join = json.loads((OUTPUT / runner.OUTPUTS["join_audit"]).read_text())
        cls.invariants = json.loads((OUTPUT / runner.OUTPUTS["invariants"]).read_text())

    def test_decision_is_pass_with_documented_blockers(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["future_limited_promotion_prompt_allowed"])
        self.assertFalse(self.decision["analysis_readiness"])
        self.assertFalse(self.decision["analysis_facing_promotion_performed"])

    def test_contract_audit_reconciles(self):
        self.assertTrue(self.contract["tier_counts_reconcile"])
        self.assertEqual(self.contract["exact_candidate_qa_pass_count"], 759)
        self.assertEqual(self.contract["exact_candidate_contamination_count"], 0)

    def test_join_audit_is_restricted_pass(self):
        self.assertEqual(self.join["result"], "pass_with_explicit_join_and_matching_restrictions")
        self.assertEqual(self.join["exact_matched_set_supported"], 85)
        self.assertEqual(self.join["historical_mixed_memberships_not_active_joins"], 16)

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])

    def test_future_prompt_matches_decision(self):
        prompt = (OUTPUT / runner.OUTPUTS["prompt"]).read_text()
        self.assertIn("759-row", prompt)
        self.assertIn("614 ambiguous", prompt)
        self.assertIn("581 unavailable", prompt)
        self.assertIn("Analysis readiness must remain false", prompt)
        self.assertFalse((OUTPUT / "next_qualitative_evidence_contract_repair_prompt.md").exists())

    def test_no_data_outputs_created(self):
        self.assertFalse(any(path.suffix == ".csv" and path.name != runner.OUTPUTS["blockers"] for path in OUTPUT.iterdir()))

    def test_dashboard_analysis_readiness_false(self):
        readiness = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text())
        self.assertNotIn("analysis_ready", readiness["overall_status"].replace("not_analysis_ready", ""))
        summary = json.loads((ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json").read_text())
        self.assertFalse(summary.get("limited_exact_span_qualitative_analysis_readiness", False))

    def test_resume_is_idempotent(self):
        result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertTrue(json.loads(result.stdout)["resume_reused"])
        self.assertEqual(json.loads(result.stdout)["writes"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
