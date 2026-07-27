#!/usr/bin/env python3
"""Hardening tests for deterministic triage of 862 quantitative direct-text rows."""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_quantitative_direct_text_claim_triage_862.py"
spec = importlib.util.spec_from_file_location("quantitative_triage_862", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class QuantitativeDirectTextClaimTriage862Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.manifest = runner.build_queue()
        cls.results = [runner.classify(row) for row in cls.queue]

    def test_exact_preserved_scope_and_unique_identity(self) -> None:
        self.assertEqual(len(self.queue), 862)
        self.assertEqual(len(self.manifest), 862)
        self.assertEqual(len({row["evidence_id"] for row in self.queue}), 862)
        self.assertEqual(len({row["row_document_id"] for row in self.queue}), 862)
        self.assertTrue(all(row["claim_oriented_primary_category"] == "quantitative_direct_text_claim_ready" for row in self.queue))
        self.assertTrue(all(row["quantitative_direct_text_claim_eligible"] == "true" for row in self.queue))

    def test_lineage_is_complete_one_to_one_without_imputation(self) -> None:
        self.assertTrue(all(row["identity_bridge_status"] == "complete_one_to_one" for row in self.queue))
        self.assertEqual(sum(bool(row["negotiation_cycle_id"]) for row in self.queue), 536)
        self.assertEqual(sum(not bool(row["negotiation_cycle_id"]) for row in self.queue), 326)
        self.assertTrue(all(row["imputation_used"] == "false" for row in self.results))
        self.assertTrue(all(row["annualization_performed"] == "false" for row in self.results))
        self.assertTrue(all(row["destructive_normalization_used"] == "false" for row in self.results))

    def test_raw_values_are_preserved_exactly(self) -> None:
        manifest_values = {row["evidence_id"]: row["direct_text_value_fields"] for row in self.manifest}
        for queued, result in zip(self.queue, self.results):
            self.assertEqual(queued["raw_value_string"], manifest_values[queued["evidence_id"]])
            self.assertEqual(result["raw_value_string"], queued["raw_value_string"])
            self.assertEqual(result["raw_value_preserved_exactly"], "true")

    def test_pinned_immutable_input_hashes(self) -> None:
        for path, expected in runner.INPUTS.items():
            self.assertTrue(path.is_file())
            self.assertEqual(runner.sha256_file(path), expected)

    def test_targeted_rating_quarantines_are_excluded(self) -> None:
        quarantine = runner.read_csv(runner.RATING_DIR / "targeted_evidence_span_rating_201_quarantine.csv")
        quarantine_ids = {row["span_extraction_id"] for row in quarantine}
        scope_ids = {row["evidence_id"] for row in self.queue} | {row["row_document_id"] for row in self.queue}
        self.assertFalse(scope_ids & quarantine_ids)

    def test_controlled_classifications_and_reconciliation(self) -> None:
        summary = runner.aggregate_rows(self.results)
        self.assertEqual(sum(summary["claim_readiness_counts"].values()), 862)
        self.assertEqual(sum(summary["value_kind_counts"].values()), 862)
        self.assertEqual(sum(summary["value_unit_counts"].values()), 862)
        self.assertEqual(sum(summary["base_vs_non_base_counts"].values()), 862)
        self.assertTrue({row["value_kind"] for row in self.results} <= set(runner.VALUE_KINDS))
        self.assertTrue({row["value_unit"] for row in self.results} <= set(runner.VALUE_UNITS))
        self.assertTrue({row["claim_readiness"] for row in self.results} <= set(runner.READINESS))
        self.assertTrue({row["base_vs_non_base"] for row in self.results} <= set(runner.BASE_CLASSES))

    def test_missing_cycles_never_become_linkage_candidates(self) -> None:
        missing_cycle = [row for row in self.results if not row["negotiation_cycle_id"]]
        self.assertEqual(len(missing_cycle), 326)
        self.assertTrue(all(row["mechanism_linkage_candidate"] == "false" for row in missing_cycle))

    def test_downstream_statuses_remain_closed(self) -> None:
        for row in self.results:
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_runner_has_no_forbidden_dependencies_or_material_reads(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
        for token in [
            "import requests", "import urllib", "httpx", "openai", "pypdf", "pdfplumber",
            "pdftotext", "tesseract", "ocrmypdf", "selenium", "playwright",
        ]:
            self.assertNotIn(token, source)
        for token in ["retained_sources/", "extracted_text/pdf", "extracted_text/html", "corpus/"]:
            self.assertNotIn(token, source)

    def test_partial_outputs_cannot_masquerade_as_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "quantitative_direct_text_claim_triage_862_decision.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                runner.validate_complete(path)

    def test_generated_package_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("triage package not generated yet")
        runner.validate_complete(runner.OUTPUT_DIR)
        decision = json.loads((runner.OUTPUT_DIR / "quantitative_direct_text_claim_triage_862_decision.json").read_text())
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertEqual(decision["input_rows"], 862)
        self.assertFalse(decision["global_analysis_readiness"])
        for field in [
            "gabriel_api_model_calls", "url_opens", "downloads", "pdf_page_accesses",
            "retained_file_accesses", "full_extracted_text_accesses", "ocr_runs", "pdf_render_runs",
            "ingestion_runs", "codification_runs", "wage_gap_calculations", "regressions",
            "treatment_effect_estimates", "population_prevalence_claims", "national_claims",
            "final_causal_claims", "imputed_values", "destructively_normalized_values", "annualized_values",
        ]:
            self.assertEqual(decision[field], 0)

    def test_generated_queue_and_results_preserve_raw_values(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("triage package not generated yet")
        with (runner.OUTPUT_DIR / "quantitative_direct_text_claim_triage_862_locked_queue.csv").open(newline="", encoding="utf-8") as handle:
            queue = list(csv.DictReader(handle))
        with (runner.OUTPUT_DIR / "quantitative_direct_text_claim_triage_862_results.csv").open(newline="", encoding="utf-8") as handle:
            results = list(csv.DictReader(handle))
        self.assertEqual(len(queue), 862)
        self.assertEqual(len(results), 862)
        self.assertEqual(
            {row["evidence_id"]: row["raw_value_string"] for row in queue},
            {row["evidence_id"]: row["raw_value_string"] for row in results},
        )

    def test_future_prompt_preserves_linkage_boundaries(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("triage package not generated yet")
        text = (runner.OUTPUT_DIR / "next_quantitative_mechanism_linkage_prompt.md").read_text().casefold()
        for phrase in [
            "do not fetch", "do not", "open urls", "pdfs/pages", "full extracted text",
            "impute", "annualize", "wage gap", "regression", "treatment effect", "population",
            "national claim", "final causal claim", "global analysis readiness", "co-location is not causation",
        ]:
            self.assertIn(phrase, text)

    def test_dashboard_gate_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("triage package not generated yet")
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_dashboard_data as dashboard
            self.assertTrue(hasattr(dashboard, "quantitative_direct_text_claim_triage_862_status"))
            ok, decision = dashboard.quantitative_direct_text_claim_triage_862_status()
        finally:
            sys.path.pop(0)
        self.assertTrue(ok)
        self.assertEqual(decision["input_rows"], 862)
        self.assertFalse(decision["global_analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
