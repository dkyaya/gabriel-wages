#!/usr/bin/env python3
"""Hardening tests for the deterministic 173-rating summary review."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_targeted_evidence_span_rating_summary_173.py"
spec = importlib.util.spec_from_file_location("rating_summary_173", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class TargetedEvidenceSpanRatingSummary173Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid, cls.quarantine, cls.results = runner.validate_inputs()

    def test_exact_scope_counts(self) -> None:
        self.assertEqual(len(self.valid), 173)
        self.assertEqual(len(self.quarantine), 28)
        self.assertEqual(len(self.valid) + len(self.quarantine), 201)

    def test_valid_and_quarantine_are_disjoint(self) -> None:
        valid_ids = {row["span_extraction_id"] for row in self.valid}
        quarantine_ids = {row["span_extraction_id"] for row in self.quarantine}
        self.assertFalse(valid_ids & quarantine_ids)

    def test_only_valid_closed_rows_enter_summary(self) -> None:
        for row in self.valid:
            self.assertEqual(row["rating_status"], "rated_valid")
            self.assertEqual(row["quote_exact_substring"], "true")
            self.assertIn(row["quote_used"], row["span_text"])
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_mechanism_counts(self) -> None:
        rows = runner.mechanism_rows(self.valid)
        actual = {row["mechanism_family"]: row["valid_rating_count"] for row in rows}
        self.assertEqual(actual, {
            "strike_or_no_strike_constraint": 103,
            "market_or_comparability_pressure": 59,
            "non_safety_constraint_signal": 10,
            "fiscal_constraint_signal": 1,
        })

    def test_direction_counts(self) -> None:
        counts = {key: 0 for key in runner.DIRECTIONS}
        for row in self.valid:
            counts[row["direction_of_pressure"]] += 1
        self.assertEqual(counts, {
            "safety_advantage": 0,
            "non_safety_advantage": 1,
            "gap_narrowing": 1,
            "neutral_or_unclear": 148,
            "not_applicable": 23,
        })

    def test_evidence_strength_counts(self) -> None:
        counts = {key: 0 for key in runner.STRENGTHS}
        for row in self.valid:
            counts[row["evidence_strength"]] += 1
        self.assertEqual(counts, {"strong": 110, "moderate": 36, "weak": 16, "not_supported": 11})

    def test_claim_relevance_counts(self) -> None:
        counts = {key: 0 for key in runner.CLAIM_RELEVANCE}
        for row in self.valid:
            counts[row["claim_relevance"]] += 1
        self.assertEqual(counts, {
            "direct_text_claim": 121,
            "documentary_mechanism_claim": 31,
            "provisional_causal_candidate": 0,
            "context_only": 20,
            "not_claim_ready": 1,
        })

    def test_support_counts(self) -> None:
        expected = {
            "direct_text_support": {"strong": 116, "moderate": 21, "weak": 13, "not_supported": 23},
            "documentary_mechanism_support": {"strong": 115, "moderate": 33, "weak": 11, "not_supported": 14},
            "provisional_causal_candidate_support": {"strong": 0, "moderate": 6, "weak": 24, "not_supported": 143},
        }
        for field, wanted in expected.items():
            counts = {key: 0 for key in runner.STRENGTHS}
            for row in self.valid:
                counts[row[field]] += 1
            self.assertEqual(counts, wanted)

    def test_all_required_input_hashes_are_pinned(self) -> None:
        for name, expected in runner.INPUT_HASHES.items():
            self.assertEqual(runner.sha256_file(runner.INPUT_DIR / name), expected)

    def test_runner_has_no_forbidden_dependencies(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
        for token in ["import requests", "import urllib", "httpx", "openai", "pypdf", "pdfplumber", "pdftotext", "tesseract", "ocrmypdf", "selenium", "playwright"]:
            self.assertNotIn(token, source)
        self.assertNotIn("source_url_or_locator]", source)
        self.assertNotIn("local_extracted_text_path]", source)

    def test_partial_outputs_cannot_masquerade_as_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "targeted_evidence_span_rating_summary_173_decision.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                runner.validate_complete(path)

    def test_generated_package_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("summary package not generated yet")
        runner.validate_complete(runner.OUTPUT_DIR)
        decision = json.loads((runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_decision.json").read_text())
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertFalse(decision["global_analysis_readiness"])
        self.assertEqual(decision["gabriel_api_model_calls"], 0)
        self.assertEqual(decision["retained_file_accesses"], 0)
        self.assertEqual(decision["full_extracted_text_accesses"], 0)

    def test_generated_scope_excludes_quarantine(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("summary package not generated yet")
        with (runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_valid_scope.csv").open(newline="", encoding="utf-8") as handle:
            valid = list(csv.DictReader(handle))
        with (runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_excluded_quarantine.csv").open(newline="", encoding="utf-8") as handle:
            excluded = list(csv.DictReader(handle))
        self.assertEqual(len(valid), 173)
        self.assertEqual(len(excluded), 28)
        self.assertFalse({row["span_extraction_id"] for row in valid} & {row["span_extraction_id"] for row in excluded})

    def test_claim_docs_are_bounded(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("summary package not generated yet")
        direct = (runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_supported_direct_text_claims.md").read_text().casefold()
        documentary = (runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_supported_documentary_mechanism_claims.md").read_text().casefold()
        causal = (runner.OUTPUT_DIR / "targeted_evidence_span_rating_summary_173_provisional_causal_candidate_signals.md").read_text().casefold()
        self.assertIn("173 valid rated spans", direct)
        self.assertIn("collected-corpus", documentary)
        self.assertIn("explicitly provisional", causal)
        self.assertNotIn("statistically significant", direct + documentary + causal)
        self.assertNotIn("caused the wage gap", direct + documentary + causal)

    def test_future_prompt_preserves_boundaries(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("summary package not generated yet")
        text = (runner.OUTPUT_DIR / "next_quantitative_claim_triage_prompt.md").read_text().casefold()
        for phrase in ["862 quantitative direct-text rows", "do not fetch", "do not", "wage gap", "regression", "treatment effect", "population", "national claim", "final causal claim", "global analysis readiness"]:
            self.assertIn(phrase, text)

    def test_dashboard_gate_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("summary package not generated yet")
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_dashboard_data as dashboard
            ok, decision = dashboard.targeted_evidence_span_rating_summary_173_status()
        finally:
            sys.path.pop(0)
        self.assertTrue(ok)
        self.assertEqual(decision["valid_rating_count"], 173)
        self.assertFalse(decision["global_analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
