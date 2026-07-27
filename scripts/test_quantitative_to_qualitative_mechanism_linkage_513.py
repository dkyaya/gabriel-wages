#!/usr/bin/env python3
"""Hardening tests for strict linkage of 513 quantitative candidates."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_quantitative_to_qualitative_mechanism_linkage_513.py"
spec = importlib.util.spec_from_file_location("mechanism_linkage_513", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class QuantitativeToQualitativeMechanismLinkage513Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        runner.validate_hashes()
        cls.quant = runner.build_quant_scope()
        cls.qual = runner.build_qual_scope()
        cls.results = runner.link_scopes(cls.quant, cls.qual)
        cls.summary = runner.counts(cls.results)

    def test_exact_quantitative_candidate_scope(self) -> None:
        self.assertEqual(len(self.quant), 513)
        self.assertEqual(len({row["evidence_id"] for row in self.quant}), 513)
        self.assertTrue(all(row["mechanism_linkage_candidate"] == "true" for row in self.quant))
        self.assertTrue(all(row["raw_value_preserved_exactly"] == "true" for row in self.quant))

    def test_noncandidate_quantitative_rows_are_excluded(self) -> None:
        full = runner.read_csv(runner.QUANT_DIR / "quantitative_direct_text_claim_triage_862_results.csv")
        candidates = {row["evidence_id"] for row in full if row["mechanism_linkage_candidate"] == "true"}
        self.assertEqual(candidates, {row["evidence_id"] for row in self.quant})
        self.assertEqual(len(full) - len(self.quant), 349)

    def test_supported_valid_qualitative_scope(self) -> None:
        self.assertEqual(len(self.qual), 609)
        self.assertEqual(len({row["qualitative_evidence_id"] for row in self.qual}), 609)
        self.assertEqual(sum(row["scope_origin"] == "legacy_valid_636_rating" for row in self.qual), 447)
        self.assertEqual(sum(row["scope_origin"] == "targeted_valid_173_rating" for row in self.qual), 162)
        self.assertTrue(all(row["rating_status"] == "rated_valid" for row in self.qual))
        self.assertTrue(all(row["evidence_strength"] != "not_supported" for row in self.qual))

    def test_legacy_and_targeted_quarantines_are_excluded(self) -> None:
        excluded7 = {row["evidence_id"] for row in runner.read_csv(runner.VALID636_DIR / "gabriel_claim_rating_summary_review_excluded_7_manifest.csv")}
        quarantine28 = {row["span_extraction_id"] for row in runner.read_csv(runner.TARGETED_RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv")}
        source_ids = {row["qualitative_source_record_id"] for row in self.qual}
        self.assertFalse(source_ids & excluded7)
        self.assertFalse(source_ids & quarantine28)

    def test_strict_linkage_counts(self) -> None:
        self.assertEqual(len(self.results), 573)
        self.assertEqual(self.summary["linked_pair_count"], 268)
        self.assertEqual(self.summary["linked_quantitative_row_count"], 208)
        self.assertEqual(self.summary["linked_qualitative_record_count"], 90)
        self.assertEqual(self.summary["no_link_quantitative_row_count"], 305)
        self.assertEqual(self.summary["linkage_confidence_counts"], {
            "exact_same_source": 268, "exact_city_unit_cycle": 0,
            "exact_city_cycle_unit_type": 0, "weak_context_only": 0, "no_link": 305,
        })

    def test_every_exact_source_link_has_recorded_shared_identity(self) -> None:
        qindex = {row["evidence_id"]: row for row in self.quant}
        vindex = {row["qualitative_evidence_id"]: row for row in self.qual}
        for row in self.results:
            if row["linkage_confidence"] != "exact_same_source":
                continue
            q = qindex[row["quantitative_evidence_id"]]
            v = vindex[row["qualitative_evidence_id"]]
            self.assertTrue(
                (q["source_review_id"] and q["source_review_id"] == v["source_review_id"])
                or (q["retained_content_hash"] and q["retained_content_hash"] == v["retained_content_hash"])
            )

    def test_targeted_scope_has_no_city_overlap_and_is_not_forced(self) -> None:
        qcities = {(row["state"], runner.norm(row["municipality"])) for row in self.quant}
        targeted = [row for row in self.qual if row["scope_origin"] == "targeted_valid_173_rating"]
        vcities = {(row["state"], runner.norm(row["municipality"])) for row in targeted}
        self.assertFalse(qcities & vcities)
        linked_ids = {row["qualitative_evidence_id"] for row in self.results if row["linkage_status"] == "linked"}
        self.assertFalse(linked_ids & {row["qualitative_evidence_id"] for row in targeted})

    def test_raw_quantitative_values_are_unchanged(self) -> None:
        raw = {row["evidence_id"]: row["raw_value_string"] for row in self.quant}
        for row in self.results:
            self.assertEqual(row["raw_quantitative_value_string"], raw[row["quantitative_evidence_id"]])

    def test_all_transform_and_analysis_flags_are_closed(self) -> None:
        for row in self.results:
            for field in [
                "value_normalized", "value_imputed", "value_annualized", "wage_gap_calculated",
                "regression_used", "treatment_effect_estimated", "causal_claim_made",
                "population_or_national_claim_made",
            ]:
                self.assertEqual(row[field], "false")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_all_input_hashes_are_pinned(self) -> None:
        for path, expected in runner.INPUTS.items():
            self.assertEqual(runner.sha256_file(path), expected)

    def test_runner_has_no_forbidden_dependencies_or_material_reads(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
        for token in [
            "import requests", "import urllib", "httpx", "openai", "pypdf", "pdfplumber",
            "pdftotext", "tesseract", "ocrmypdf", "selenium", "playwright",
            "retained_sources/", "extracted_text/pdf", "extracted_text/html", "corpus/",
        ]:
            self.assertNotIn(token, source)

    def test_partial_outputs_cannot_masquerade_as_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "quantitative_to_qualitative_mechanism_linkage_513_decision.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                runner.validate_complete(path)

    def test_generated_package_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("linkage package not generated yet")
        runner.validate_complete(runner.OUTPUT_DIR)
        decision = json.loads((runner.OUTPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_decision.json").read_text())
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertTrue(decision["claim_review_ready_next"])
        self.assertFalse(decision["global_analysis_readiness"])
        for field in [
            "value_normalizations", "value_imputations", "value_annualizations", "wage_gap_calculations",
            "wage_level_outcome_comparisons", "regressions", "treatment_effect_estimates",
            "final_causal_claims", "population_prevalence_claims", "national_claims",
            "gabriel_api_model_calls", "url_opens", "downloads", "pdf_page_accesses",
            "retained_file_accesses", "full_extracted_text_accesses", "ocr_runs", "pdf_render_runs",
            "ingestion_runs", "codification_runs", "raw_prompts_saved", "raw_responses_saved",
        ]:
            self.assertEqual(decision[field], 0)

    def test_future_prompt_preserves_claim_review_boundaries(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("linkage package not generated yet")
        text = (runner.OUTPUT_DIR / "next_mechanism_linkage_claim_review_prompt.md").read_text().casefold()
        for phrase in [
            "268 exact same-source", "do not fetch", "open urls", "pdfs/pages", "full extracted text",
            "normalize", "impute", "annualize", "wage gap", "regression", "treatment effect",
            "population", "national", "final causal", "global analysis readiness", "co-location is not causation",
        ]:
            self.assertIn(phrase, text)

    def test_dashboard_gate_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("linkage package not generated yet")
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_dashboard_data as dashboard
            self.assertTrue(hasattr(dashboard, "quantitative_to_qualitative_mechanism_linkage_513_status"))
            ok, decision = dashboard.quantitative_to_qualitative_mechanism_linkage_513_status()
        finally:
            sys.path.pop(0)
        self.assertTrue(ok)
        self.assertEqual(decision["quantitative_linkage_candidate_count"], 513)
        self.assertFalse(decision["global_analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
