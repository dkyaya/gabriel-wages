#!/usr/bin/env python3
"""Hardening tests for the 268-pair exact-source claim review."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_mechanism_linkage_claim_review_268.py"
spec = importlib.util.spec_from_file_location("mechanism_linkage_claim_review_268", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class MechanismLinkageClaimReview268Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        runner.validate_hashes()
        cls.scope = runner.build_scope()
        cls.predecessor = {
            row["linkage_id"]: row
            for row in runner.read_csv(runner.INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_exact_same_source_links.csv")
        }

    def test_exact_scope_reconciles_268_208_90(self) -> None:
        self.assertEqual(len(self.scope), 268)
        self.assertEqual(len({row["linkage_id"] for row in self.scope}), 268)
        self.assertEqual(len({row["quantitative_evidence_id"] for row in self.scope}), 208)
        self.assertEqual(len({row["qualitative_evidence_id"] for row in self.scope}), 90)

    def test_only_exact_same_source_linked_pairs_enter(self) -> None:
        self.assertTrue(all(row["linkage_status"] == "linked" for row in self.scope))
        self.assertTrue(all(row["linkage_confidence"] == "exact_same_source" for row in self.scope))
        self.assertTrue(all(row["same_source_match"] == "true" for row in self.scope))
        all_results = runner.read_csv(runner.INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_results.csv")
        excluded = {row["linkage_id"] for row in all_results if row["linkage_status"] != "linked" or row["linkage_confidence"] != "exact_same_source"}
        self.assertFalse(excluded & {row["linkage_id"] for row in self.scope})
        self.assertEqual(len(excluded), 305)

    def test_noncandidate_and_invalid_qualitative_rows_are_excluded(self) -> None:
        quant = {row["evidence_id"]: row for row in runner.read_csv(runner.INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_quant_scope.csv")}
        qual = {row["qualitative_evidence_id"]: row for row in runner.read_csv(runner.INPUT_DIR / "quantitative_to_qualitative_mechanism_linkage_513_qual_scope.csv")}
        for row in self.scope:
            self.assertEqual(quant[row["quantitative_evidence_id"]]["mechanism_linkage_candidate"], "true")
            self.assertEqual(qual[row["qualitative_evidence_id"]]["rating_status"], "rated_valid")
            self.assertNotEqual(qual[row["qualitative_evidence_id"]]["evidence_strength"], "not_supported")

    def test_raw_values_and_claim_boundaries_are_exact(self) -> None:
        for row in self.scope:
            predecessor = self.predecessor[row["linkage_id"]]
            self.assertEqual(row["raw_quantitative_value_string"], predecessor["raw_quantitative_value_string"])
            self.assertEqual(row["quantitative_value_unit"], predecessor["quantitative_value_unit"])
            self.assertEqual(row["quantitative_claim_readiness"], predecessor["quantitative_claim_readiness"])
            self.assertEqual(row["qualitative_claim_boundary"], predecessor["qualitative_claim_boundary"])
            self.assertEqual(row["linkage_reason"], predecessor["linkage_reason"])

    def test_source_and_pair_multiplicity_is_preserved(self) -> None:
        qcounts = Counter(row["quantitative_evidence_id"] for row in self.scope)
        vcounts = Counter(row["qualitative_evidence_id"] for row in self.scope)
        scounts = Counter(row["shared_source_lineage_key"] for row in self.scope)
        for row in self.scope:
            self.assertEqual(int(row["quantitative_pair_multiplicity"]), qcounts[row["quantitative_evidence_id"]])
            self.assertEqual(int(row["qualitative_pair_multiplicity"]), vcounts[row["qualitative_evidence_id"]])
            self.assertEqual(int(row["source_pair_multiplicity"]), scounts[row["shared_source_lineage_key"]])

    def test_deterministic_claim_type_counts(self) -> None:
        self.assertEqual(Counter(row["claim_type"] for row in self.scope), Counter({
            "direct_text_colocation_claim": 15,
            "documentary_mechanism_value_scaffold": 80,
            "provisional_mechanism_linkage_claim": 32,
            "insufficient_for_claim": 141,
        }))
        self.assertTrue(all(row["claim_type"] in runner.CLAIM_TYPES for row in self.scope))
        self.assertTrue(all(row["claim_review_status"] == "bounded_reviewed" for row in self.scope))

    def test_mechanism_unit_and_source_counts(self) -> None:
        self.assertEqual(Counter(row["qualitative_mechanism_family"] for row in self.scope), Counter({
            "implementation_or_retroactivity_advantage": 126,
            "automatic_raise_mechanism": 97,
            "non_base_compensation_signal": 15,
            "rank_or_specialization_premium": 13,
            "market_or_comparability_pressure": 9,
            "bargaining_power_signal": 5,
            "fiscal_constraint_signal": 3,
        }))
        self.assertEqual(Counter(row["unit_type"] for row in self.scope), Counter({"police": 129, "fire": 85, "non_safety": 54}))
        self.assertEqual(Counter(row["source_family"] for row in self.scope), Counter({"cba": 261, "memorandum_or_settlement": 4, "wage_schedule_or_compensation_plan": 3}))

    def test_all_transform_analysis_and_downstream_fields_are_closed(self) -> None:
        for row in self.scope:
            for field in runner.DOWNSTREAM_FALSE_FIELDS:
                self.assertEqual(row[field], "false")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")

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
            (path / "mechanism_linkage_claim_review_268_decision.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                runner.validate_complete(path)

    def test_generated_package_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("claim-review package not generated yet")
        runner.validate_complete(runner.OUTPUT_DIR)
        decision = json.loads((runner.OUTPUT_DIR / "mechanism_linkage_claim_review_268_decision.json").read_text())
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertTrue(decision["claim_memo_allowed_next"])
        self.assertFalse(decision["global_analysis_readiness"])
        for field in [
            "raw_quantitative_values_changed", "value_normalizations", "value_imputations",
            "value_annualizations", "wage_level_outcome_comparisons", "wage_gap_calculations",
            "regressions", "treatment_effect_estimates", "population_prevalence_claims",
            "national_claims", "final_causal_claims", "gabriel_api_model_calls", "url_opens",
            "downloads", "pdf_page_accesses", "retained_file_accesses", "full_extracted_text_accesses",
            "ocr_runs", "pdf_render_runs", "ingestion_runs", "codification_runs",
            "raw_prompts_saved", "raw_responses_saved",
        ]:
            self.assertEqual(decision[field], 0)

    def test_claim_docs_are_bounded(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("claim-review package not generated yet")
        docs = [path for path in runner.OUTPUT_DIR.glob("*.md") if path.name not in {"mechanism_linkage_claim_review_268_claims_not_allowed.md"}]
        combined = "\n".join(path.read_text(encoding="utf-8").casefold() for path in docs)
        for phrase in [
            "this mechanism caused the value", "this proves a wage gap",
            "safety workers earn", "non-safety workers earn less because",
            "statistically significant", "nationally,", "the effect is",
        ]:
            self.assertNotIn(phrase, combined)
        self.assertIn("co-location", combined)
        self.assertIn("does not establish", combined)

    def test_future_prompt_preserves_next_phase_boundaries(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("claim-review package not generated yet")
        text = (runner.OUTPUT_DIR / "next_claim_memo_drafting_prompt.md").read_text().casefold()
        for phrase in [
            "268-pair", "15 direct", "80 documentary", "32 provisional", "141 insufficient",
            "do not fetch", "open urls", "pdfs/pages", "full extracted text", "normalize",
            "impute", "annualize", "wage gap", "regression", "treatment effect", "population",
            "national", "final causal", "global analysis readiness", "not causal proof",
        ]:
            self.assertIn(phrase, text)

    def test_dashboard_gate_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("claim-review package not generated yet")
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_dashboard_data as dashboard
            self.assertTrue(hasattr(dashboard, "mechanism_linkage_claim_review_268_status"))
            ok, decision = dashboard.mechanism_linkage_claim_review_268_status()
        finally:
            sys.path.pop(0)
        self.assertTrue(ok)
        self.assertEqual(decision["claim_review_pair_count"], 268)
        self.assertFalse(decision["global_analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
