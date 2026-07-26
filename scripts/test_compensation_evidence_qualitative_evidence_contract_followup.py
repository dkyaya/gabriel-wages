#!/usr/bin/env python3
"""Focused fail-closed tests for the qualitative evidence contract."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_qualitative_evidence_contract_followup as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class TierRuleTests(unittest.TestCase):
    def base_row(self, status: str) -> dict[str, str]:
        row = {
            "qualitative_observation_id": "lobs_test",
            "span_capture_status": status,
            "span_qa_status": "navigation_only_span_not_qa_sufficient",
            "span_qa_pass": "false",
            "qa_status": "provisional_unverified",
            "literal_verbatim_evidence_span": "",
            "span_start": "",
            "span_end": "",
            "span_length": "",
            "span_sha256": "",
        }
        if status == "exact_verified":
            span = "Wages increase by two percent."
            row.update({
                "span_qa_status": "span_exact_unique_verified",
                "span_qa_pass": "true",
                "literal_verbatim_evidence_span": span,
                "span_start": "5",
                "span_end": str(5 + len(span)),
                "span_length": str(len(span)),
                "span_sha256": hashlib.sha256(span.encode()).hexdigest(),
            })
        return row

    def test_exact_maps_to_candidate(self):
        out = runner.tier_row(self.base_row("exact_verified"))
        self.assertEqual(out["evidence_contract_tier"], "exact_span_coded_candidate")
        self.assertEqual(out["evidence_contract_candidate_eligible"], "true")

    def test_ambiguous_maps_to_navigation(self):
        out = runner.tier_row(self.base_row("span_ambiguous_multiple_candidates"))
        self.assertEqual(out["evidence_contract_tier"], "ambiguous_exact_span_navigation")
        self.assertEqual(out["evidence_contract_candidate_eligible"], "false")

    def test_unavailable_maps_to_navigation(self):
        out = runner.tier_row(self.base_row("span_unavailable_or_unverified"))
        self.assertEqual(out["evidence_contract_tier"], "unavailable_span_navigation")
        self.assertEqual(out["evidence_contract_candidate_eligible"], "false")

    def test_historical_qa_is_preserved(self):
        source = self.base_row("exact_verified")
        self.assertEqual(runner.tier_row(source)["qa_status"], "provisional_unverified")

    def test_exact_hash_corruption_fails(self):
        row = self.base_row("exact_verified")
        row["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            runner.validate_span_row(row, exact=True)

    def test_exact_offset_corruption_fails(self):
        row = self.base_row("exact_verified")
        row["span_end"] = str(int(row["span_end"]) + 1)
        with self.assertRaisesRegex(RuntimeError, "offset/length"):
            runner.validate_span_row(row, exact=True)

    def test_exact_multiline_fails(self):
        row = self.base_row("exact_verified")
        row["literal_verbatim_evidence_span"] = "Wages\nincrease"
        with self.assertRaisesRegex(RuntimeError, "multiline"):
            runner.validate_span_row(row, exact=True)

    def test_ambiguous_cannot_claim_exact_qa(self):
        row = self.base_row("span_ambiguous_multiple_candidates")
        row["span_qa_status"] = "span_exact_unique_verified"
        with self.assertRaisesRegex(RuntimeError, "exact-span eligibility"):
            runner.validate_span_row(row, exact=False)

    def test_unavailable_cannot_claim_qa_pass(self):
        row = self.base_row("span_unavailable_or_unverified")
        row["span_qa_pass"] = "true"
        with self.assertRaisesRegex(RuntimeError, "exact-span eligibility"):
            runner.validate_span_row(row, exact=False)

    def test_sample_is_deterministic_and_bounded(self):
        rows = [dict(self.base_row("span_unavailable_or_unverified"), qualitative_observation_id=f"lobs_{i:03}") for i in range(40)]
        self.assertEqual(runner.deterministic_sample(rows), runner.deterministic_sample(list(reversed(rows))))
        self.assertEqual(len(runner.deterministic_sample(rows)), 25)

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/evidence_contract_bad")

    def test_future_prompt_check_allows_pre_report_phase(self):
        self.assertTrue(runner.future_prompt_matches(ROOT / "does-not-exist", required=False))

    def test_future_prompt_check_fails_closed_when_complete_prompt_missing(self):
        self.assertFalse(runner.future_prompt_matches(ROOT / "does-not-exist", required=True))


class FrozenInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.fields, cls.rows, cls.ledger = runner.validate_frozen_layer()

    def test_all_19_input_hashes_pass(self):
        self.assertEqual(len(self.hashes), 19)

    def test_frozen_total_is_1954(self):
        self.assertEqual(len(self.rows), 1954)

    def test_frozen_ids_are_unique(self):
        ids = [row["qualitative_observation_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_frozen_tier_counts(self):
        counts = {status: sum(row["span_capture_status"] == status for row in self.rows) for status in runner.EXPECTED_COUNTS}
        self.assertEqual(counts, runner.EXPECTED_COUNTS)

    def test_historical_and_span_qa_are_separate(self):
        self.assertIn("qa_status", self.fields)
        self.assertIn("span_qa_status", self.fields)
        self.assertNotEqual({row["qa_status"] for row in self.rows}, {row["span_qa_status"] for row in self.rows})

    def test_no_forbidden_page_text_columns(self):
        self.assertFalse(set(self.fields) & runner.FORBIDDEN_PERSISTED_FIELDS)

    def test_prior_invariants_pass(self):
        payload = json.loads(runner.INPUTS["invariants"].read_text())
        self.assertTrue(payload["all_invariants_passed"])

    def test_upstream_analysis_readiness_false(self):
        payload = json.loads(runner.INPUTS["decision"].read_text())
        self.assertFalse(payload["analysis_readiness"])

    def test_no_pdf_library_or_model_import(self):
        source = Path(runner.__file__).read_text()
        for forbidden in ("PdfReader", "pdfplumber", "fitz", "openai", "gabriel"):
            self.assertNotIn(f"import {forbidden}", source)
            self.assertNotIn(f"from {forbidden}", source)


class MaterializedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.combined_fields, cls.combined = read_csv(OUTPUT / runner.OUTPUTS["combined"])
        cls.exact_fields, cls.exact = read_csv(OUTPUT / runner.OUTPUTS["exact"])
        cls.ambiguous_fields, cls.ambiguous = read_csv(OUTPUT / runner.OUTPUTS["ambiguous"])
        cls.unavailable_fields, cls.unavailable = read_csv(OUTPUT / runner.OUTPUTS["unavailable"])
        cls.decision = json.loads((OUTPUT / runner.OUTPUTS["decision"]).read_text())
        cls.audit = json.loads((OUTPUT / runner.OUTPUTS["audit"]).read_text())

    def test_tier_counts_reconcile(self):
        self.assertEqual((len(self.exact), len(self.ambiguous), len(self.unavailable)), (759, 614, 581))
        self.assertEqual(len(self.exact) + len(self.ambiguous) + len(self.unavailable), 1954)

    def test_exact_candidates_all_pass_unique_span_qa(self):
        self.assertTrue(all(row["span_qa_status"] == "span_exact_unique_verified" and row["span_qa_pass"] == "true" for row in self.exact))

    def test_no_ambiguous_or_unavailable_candidate_contamination(self):
        self.assertTrue(all(row["evidence_contract_candidate_eligible"] == "false" for row in self.ambiguous + self.unavailable))
        candidate_ids = {row["qualitative_observation_id"] for row in self.exact}
        nav_ids = {row["qualitative_observation_id"] for row in self.ambiguous + self.unavailable}
        self.assertFalse(candidate_ids & nav_ids)

    def test_combined_ids_unique(self):
        ids = [row["qualitative_observation_id"] for row in self.combined]
        self.assertEqual(len(ids), len(set(ids)))

    def test_combined_order_matches_source(self):
        _, source = read_csv(runner.INPUTS["navigation"])
        self.assertEqual([row["qualitative_observation_id"] for row in self.combined], [row["qualitative_observation_id"] for row in source])

    def test_historical_qa_values_preserved(self):
        _, source = read_csv(runner.INPUTS["navigation"])
        source_qa = {row["qualitative_observation_id"]: row["qa_status"] for row in source}
        self.assertTrue(all(row["qa_status"] == source_qa[row["qualitative_observation_id"]] for row in self.combined))

    def test_no_full_page_text_fields(self):
        self.assertFalse(set(self.combined_fields) & runner.FORBIDDEN_PERSISTED_FIELDS)

    def test_carried_outputs_are_byte_identical(self):
        for input_key, output_key in runner.COPY_MAP.items():
            self.assertEqual(runner.INPUTS[input_key].read_bytes(), (OUTPUT / runner.OUTPUTS[output_key]).read_bytes(), input_key)

    def test_carried_counts(self):
        self.assertEqual(runner.carried_counts()["quantitative_candidate"], 862)
        self.assertEqual(runner.carried_counts()["quantitative_exception"], 1045)
        self.assertEqual(runner.carried_counts()["non_base"], 4733)
        self.assertEqual(runner.carried_counts()["reference"], 345)
        self.assertEqual(runner.carried_counts()["conflicts"], 2)

    def test_decision_is_limited_review_only(self):
        self.assertEqual(self.decision["decision"], "qualitative_evidence_contract_limited_review_allowed_exact_span_only")
        self.assertEqual(self.decision["repeat_review_scope"], "limited_exact_span_only")
        self.assertTrue(self.decision["repeat_analysis_readiness_review_allowed"])
        self.assertFalse(self.decision["analysis_readiness"])
        self.assertFalse(self.decision["analysis_facing_promotion_allowed"])

    def test_full_qualitative_view_not_created(self):
        self.assertFalse(self.audit["full_coded_qualitative_view_created"])
        self.assertTrue(self.audit["limited_exact_span_candidate_created"])

    def test_future_prompt_matches_decision(self):
        self.assertTrue((OUTPUT / "next_analysis_readiness_review_prompt.md").is_file())
        self.assertFalse((OUTPUT / "next_bounded_schema_repair_followup_prompt.md").exists())

    def test_analysis_readiness_dashboard_false(self):
        dashboard = json.loads((ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json").read_text())
        self.assertIn(
            dashboard["calibration_phase"],
            {
                "compensation_extraction_qualitative_evidence_contract_limited_review_allowed_exact_span_only",
                "compensation_extraction_limited_exact_span_qualitative_readiness_review_completed_pass_with_blockers",
            },
        )
        self.assertEqual(dashboard["qualitative_evidence_contract_repeat_review_scope"], "limited_exact_span_only")
        readiness = json.loads((ROOT / "docs/dashboard/data/analysis_readiness.json").read_text())
        self.assertIn(
            readiness["overall_status"],
            {
                "qualitative_evidence_contract_limited_review_allowed_exact_span_only_analysis_closed",
                "limited_exact_span_qualitative_readiness_pass_with_blockers_promotion_prompt_allowed_analysis_closed",
            },
        )
        self.assertIn("analysis_closed", readiness["overall_status"])

    def test_audit_reports_zero_pdf_access(self):
        self.assertEqual(self.audit["pdf_pages_accessed"], 0)
        self.assertEqual(self.audit["ocr_later_accessed"], 0)
        self.assertEqual(self.audit["non_target_pages_accessed"], 0)

    def test_resume_reuses_complete_output_without_writes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_compensation_evidence_qualitative_evidence_contract_followup.py"), "--resume"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["resume_reused"])
        self.assertEqual(payload["writes"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
