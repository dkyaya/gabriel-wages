#!/usr/bin/env python3
"""Hardening tests for the bounded internal mechanism-linkage claim memo."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_bounded_internal_mechanism_linkage_claim_memo.py"
spec = importlib.util.spec_from_file_location("bounded_internal_mechanism_linkage_claim_memo", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class BoundedInternalMechanismLinkageClaimMemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        runner.validate_hashes()
        cls.scope = runner.load_scope()
        cls.geography = runner.build_geography(cls.scope)

    def test_scope_reconciles_268_208_90_72(self) -> None:
        self.assertEqual(len(self.scope), 268)
        self.assertEqual(len({row["quantitative_evidence_id"] for row in self.scope}), 208)
        self.assertEqual(len({row["qualitative_evidence_id"] for row in self.scope}), 90)
        self.assertEqual(len({row["shared_source_lineage_key"] for row in self.scope}), 72)

    def test_only_bounded_exact_source_claim_review_rows_enter(self) -> None:
        self.assertTrue(all(row["linkage_status"] == "linked" for row in self.scope))
        self.assertTrue(all(row["linkage_confidence"] == "exact_same_source" for row in self.scope))
        self.assertTrue(all(row["claim_review_status"] == "bounded_reviewed" for row in self.scope))
        self.assertFalse(any(row["claim_type"] == "not_allowed" for row in self.scope))

    def test_claim_types_reconcile(self) -> None:
        self.assertEqual(Counter(row["claim_type"] for row in self.scope), Counter({
            "direct_text_colocation_claim": 15,
            "documentary_mechanism_value_scaffold": 80,
            "provisional_mechanism_linkage_claim": 32,
            "insufficient_for_claim": 141,
        }))

    def test_region_mapping_is_static_and_deterministic(self) -> None:
        expected = {
            "MA": "Northeast", "OH": "Midwest", "TX": "South", "CA": "West",
            "DC": "District of Columbia / Federal district", "": "Unknown", "XX": "Unknown",
        }
        for state, region in expected.items():
            self.assertEqual(runner.region_for_state(state), region)
        self.assertEqual(len(runner.VALID_STATES), 51)

    def test_geographic_counts_derive_from_scope(self) -> None:
        self.assertEqual(self.geography["linked_pair_count"], 268)
        self.assertEqual(self.geography["state_count"], 23)
        self.assertEqual(self.geography["city_state_pair_count"], 64)
        self.assertEqual(self.geography["city_cycle_unit_group_count"], 72)
        self.assertEqual(self.geography["shared_source_lineage_count"], 72)
        self.assertFalse(self.geography["external_lookup_used"])
        self.assertEqual(self.geography["mapping_method"], "deterministic_static_census_style_region_from_existing_state_abbreviation")

    def test_region_counts_reconcile_without_unknowns(self) -> None:
        counts = {row["region"]: row["linked_pair_count"] for row in self.geography["region_rows"]}
        self.assertEqual(counts, {
            "Northeast": 39, "Midwest": 109, "South": 16, "West": 104,
            "District of Columbia / Federal district": 0, "Unknown": 0,
        })
        self.assertEqual(sum(counts.values()), 268)

    def test_missing_geography_is_disclosed_not_invented(self) -> None:
        self.assertEqual(self.geography["missing_geography_counts"], {
            "state": 0, "city": 0, "unit_type": 0, "contract_or_cycle_period": 0,
            "source_family": 0, "unknown_region": 0,
        })
        scope_states = {row["state"] for row in self.scope}
        output_states = {row["state"] for row in self.geography["state_rows"]}
        self.assertEqual(output_states, scope_states)

    def test_original_values_and_closed_boundaries_remain_untouched(self) -> None:
        for row in self.scope:
            for field in [
                "value_normalized", "value_imputed", "value_annualized", "wage_gap_calculated",
                "regression_used", "treatment_effect_estimated", "causal_claim_made",
                "population_or_national_claim_made", "global_analysis_readiness",
            ]:
                self.assertEqual(row[field], "false")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")

    def test_all_input_hashes_are_pinned(self) -> None:
        for path, expected in runner.INPUTS.items():
            self.assertEqual(runner.sha256_file(path), expected)

    def test_runner_has_no_network_model_or_material_document_dependencies(self) -> None:
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
            (path / "bounded_internal_mechanism_linkage_claim_memo_decision.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                runner.validate_complete(path)

    def test_generated_package_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        runner.validate_complete(runner.OUTPUT_DIR)
        decision = json.loads((runner.OUTPUT_DIR / "bounded_internal_mechanism_linkage_claim_memo_decision.json").read_text())
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertTrue(decision["tier_c_verification_recommended_next"])
        self.assertFalse(decision["global_analysis_readiness"])
        for field in [
            "raw_quantitative_values_changed", "value_normalizations", "value_imputations",
            "value_annualizations", "wage_level_outcome_comparisons", "wage_gap_calculations",
            "regressions", "treatment_effect_estimates", "population_prevalence_claims",
            "national_claims", "final_causal_claims", "gabriel_api_model_calls", "url_opens",
            "downloads", "pdf_page_accesses", "retained_file_accesses", "full_extracted_text_accesses",
            "ocr_runs", "pdf_render_runs", "ingestion_runs", "codification_runs",
            "raw_prompts_saved", "raw_responses_saved", "external_geography_lookups",
            "invented_geographic_fields",
        ]:
            self.assertEqual(decision[field], 0)

    def test_memo_has_required_structure_and_bounded_interpretations(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        memo = (runner.OUTPUT_DIR / "bounded_internal_mechanism_linkage_claim_memo.md").read_text(encoding="utf-8").casefold()
        for section in [
            "executive summary", "evidence scope", "geographic and source coverage",
            "what this memo can and cannot claim", "strongest linked mechanisms",
            "thin or unlinked mechanisms", "unit and source-family limits",
            "claim scaffolds supported now", "claims not supported yet", "next data needs",
            "recommended next phase",
        ]:
            self.assertIn(section, memo)
        for phrase in [
            "implementation/retroactivity", "automatic raises", "strike/no-strike",
            "non-safety constraint", "parity/internal equity", "gap narrowing",
            "bounded documentary co-location", "does not support a wage-gap estimate or causal conclusion",
        ]:
            self.assertIn(phrase, memo)

    def test_memo_outputs_contain_no_forbidden_affirmative_claims(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        combined = "\n".join(path.read_text(encoding="utf-8").casefold() for path in runner.OUTPUT_DIR.glob("*.md"))
        for phrase in [
            "this caused the wage gap", "this proves", "nationally,", "the effect is",
            "statistically significant", "safety workers earn", "non-safety workers earn less because",
        ]:
            self.assertNotIn(phrase, combined)

    def test_dashboard_metadata_matches_decision_and_geography(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        decision = runner.read_json(runner.OUTPUT_DIR / "bounded_internal_mechanism_linkage_claim_memo_decision.json")
        metadata = runner.read_json(runner.OUTPUT_DIR / "bounded_internal_mechanism_linkage_claim_memo_dashboard_metadata.json")
        geography = runner.read_json(runner.OUTPUT_DIR / "bounded_internal_mechanism_linkage_claim_memo_geographic_coverage_summary.json")
        self.assertEqual(metadata["memo_decision"], decision["decision"])
        self.assertEqual(metadata["memo_scope"], decision["memo_scope"])
        self.assertEqual(metadata["geographic_coverage"]["state_count"], geography["state_count"])
        self.assertEqual(metadata["geographic_coverage"]["region_pair_counts"]["Midwest"], 109)
        self.assertFalse(metadata["global_analysis_readiness"])
        self.assertFalse(metadata["final_causal_claims"])
        self.assertFalse(metadata["wage_gap_estimates"])
        self.assertIn("bounded_internal_mechanism_linkage_claim_memo.md", metadata["memo_path"])

    def test_future_prompt_preserves_next_phase_boundaries(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        text = (runner.OUTPUT_DIR / "next_targeted_tier_c_verification_prompt.md").read_text(encoding="utf-8").casefold()
        for phrase in [
            "tier c", "strike/no-strike", "non-safety constraint", "parity/internal equity",
            "gap narrowing", "do not fetch", "download before separate authorization", "extract",
            "rate", "normalize", "impute", "annualize", "wage gaps", "regressions",
            "treatment effects", "population", "national", "final causal", "global analysis readiness",
        ]:
            self.assertIn(phrase, text)

    def test_dashboard_gate_when_present(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("memo package not generated yet")
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import build_dashboard_data as dashboard
            self.assertTrue(hasattr(dashboard, "bounded_internal_mechanism_linkage_claim_memo_status"))
            ok, decision, metadata = dashboard.bounded_internal_mechanism_linkage_claim_memo_status()
        finally:
            sys.path.pop(0)
        self.assertTrue(ok)
        self.assertEqual(decision["memo_scope"]["exact_same_source_linked_pair_count"], 268)
        self.assertEqual(metadata["geographic_coverage"]["state_count"], 23)
        self.assertFalse(decision["global_analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
