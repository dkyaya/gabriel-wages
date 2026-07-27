#!/usr/bin/env python3
"""Regression tests for deterministic exact-span extraction over 321 artifacts."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_targeted_evidence_span_extraction_321.py"
SPEC = importlib.util.spec_from_file_location("targeted_evidence_span_extraction_321", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)
DASHBOARD_SPEC = importlib.util.spec_from_file_location("build_dashboard_data", ROOT / "scripts/build_dashboard_data.py")
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
DASHBOARD_SPEC.loader.exec_module(dashboard)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class TargetedEvidenceSpanExtraction321Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.preserved, cls.hashes = runner.verify_inputs(verify_artifact_bytes=False)

    def row_for(self, mechanism: str) -> dict[str, str]:
        return dict(next(row for row in self.queue if row["target_mechanism_family"] == mechanism))

    def extract_synthetic(self, mechanism: str, text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "text.txt"
            path.write_text(text, encoding="utf-8")
            row = self.row_for(mechanism)
            row["extracted_text_path"] = str(path)
            with mock.patch.object(runner, "ROOT", Path("/")):
                return runner.extract_source(row)

    def test_exact_scope_and_lineage(self) -> None:
        self.assertEqual(len(self.queue), 321)
        self.assertEqual(len({row["retained_source_id"] for row in self.queue}), 321)
        self.assertEqual(runner.id_set_hash(self.queue), runner.EXPECTED_ID_SET_HASH)

    def test_pdf_html_split(self) -> None:
        self.assertEqual(sum(row["readiness_status"] == "parse_text_layer_later" for row in self.queue), 289)
        self.assertEqual(sum(row["readiness_status"] == "html_text_later" for row in self.queue), 32)

    def test_lane_and_mechanism_counts(self) -> None:
        self.assertEqual(dict(Counter(row["lane_id"] for row in self.queue)), runner.EXPECTED_LANES)
        self.assertEqual(dict(Counter(row["target_mechanism_family"] for row in self.queue)), runner.EXPECTED_MECHANISMS)

    def test_all_inputs_extracted_ok_tier_a_b_and_closed(self) -> None:
        for row in self.queue:
            self.assertEqual(row["extraction_status"], "extracted_ok")
            self.assertIn(row["priority_tier"], {"tier_a", "tier_b"})
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_artifact_paths_are_task_local(self) -> None:
        for row in self.queue:
            path = (ROOT / row["extracted_text_path"]).resolve()
            self.assertTrue(path.is_file())
            self.assertTrue(path.is_relative_to(runner.TEXT_ROOT.resolve()))

    def test_immutable_hashes_are_pinned(self) -> None:
        self.assertEqual(self.hashes, runner.EXPECTED_HASHES)

    def test_preserved_exclusions_remain_outside(self) -> None:
        self.assertEqual(len(self.preserved), 108)
        ready = {row["retained_source_id"] for row in self.queue}
        excluded = {row.get("retained_source_id", "") for row in self.preserved if row.get("retained_source_id")}
        self.assertFalse(ready & excluded)

    def test_runner_has_no_network_ocr_render_or_model_dependency(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
        for token in ("requests.", "urllib.request", "httpx.", "pytesseract", "ocrmypdf", "pdf2image", "openai", "gabriel.codify"):
            self.assertNotIn(token, source)

    def test_no_strike_clause_is_positive(self) -> None:
        source, spans = self.extract_synthetic(
            "strike_or_no_strike_constraint",
            "Article 12 Labor Peace\n\nThe Union agrees that there shall be no strike or work stoppage during this agreement.",
        )
        self.assertEqual(source["span_status"], "span_extracted")
        self.assertGreaterEqual(len(spans), 1)
        self.assertTrue(all(span["span_status"] == "span_extracted" for span in spans))

    def test_force_majeure_strike_and_lockout_is_not_positive(self) -> None:
        source, spans = self.extract_synthetic(
            "strike_or_no_strike_constraint",
            "A party is excused from delay caused by any strike, lock-out, weather condition, flood, or act of God.",
        )
        self.assertNotEqual(source["span_status"], "span_extracted")
        self.assertFalse(any(span["span_status"] == "span_extracted" for span in spans))

    def test_untied_arbitration_is_ambiguous(self) -> None:
        source, spans = self.extract_synthetic(
            "strike_or_no_strike_constraint",
            "The arbitrator shall schedule arbitration within thirty days and issue a written decision.",
        )
        self.assertEqual(source["span_status"], "ambiguous_span")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["documentary_claim_support"], "weak")

    def test_market_recruitment_with_pay_is_positive(self) -> None:
        source, spans = self.extract_synthetic(
            "market_or_comparability_pressure",
            "The salary adjustment is intended to improve recruitment and retention in a competitive labor market.",
        )
        self.assertEqual(source["span_status"], "span_extracted")
        self.assertTrue(spans)

    def test_market_recruitment_without_pay_is_ambiguous(self) -> None:
        source, spans = self.extract_synthetic(
            "market_or_comparability_pressure",
            "The department will hold a recruitment picnic and community open house next Saturday.",
        )
        self.assertEqual(source["span_status"], "ambiguous_span")
        self.assertEqual(spans[0]["span_specificity"], "low")

    def test_non_safety_wage_freeze_is_positive(self) -> None:
        source, spans = self.extract_synthetic(
            "non_safety_constraint_signal",
            "Employees remain subject to a wage freeze for fiscal year 2021 and receive no step increase.",
        )
        self.assertEqual(source["span_status"], "span_extracted")
        self.assertTrue(spans)

    def test_non_safety_pay_appropriated_is_not_a_constraint(self) -> None:
        source, spans = self.extract_synthetic(
            "non_safety_constraint_signal",
            "The per diem rate of pay appropriated for the employee's placement on the salary schedule shall be used.",
        )
        self.assertNotEqual(source["span_status"], "span_extracted")
        self.assertFalse(any(span["span_status"] == "span_extracted" for span in spans))

    def test_non_safety_generic_budget_is_ambiguous(self) -> None:
        source, spans = self.extract_synthetic(
            "non_safety_constraint_signal",
            "The annual parks budget lists trees, vehicles, and building maintenance projects.",
        )
        self.assertEqual(source["span_status"], "ambiguous_span")
        self.assertTrue(spans)

    def test_fiscal_appropriation_with_salary_is_positive(self) -> None:
        source, spans = self.extract_synthetic(
            "fiscal_constraint_signal",
            "All salary increases are contingent upon appropriation of sufficient funds by the city council.",
        )
        self.assertEqual(source["span_status"], "span_extracted")
        self.assertTrue(spans)

    def test_no_mechanism_term_is_no_span(self) -> None:
        source, spans = self.extract_synthetic(
            "fiscal_constraint_signal",
            "Employees may request vacation leave using the standard form maintained by human resources.",
        )
        self.assertEqual(source["span_status"], "no_span_or_weak")
        self.assertEqual(spans, [])

    def test_exact_offsets_hash_and_context_bounds(self) -> None:
        text = "A" * 300 + " The parties agree to a market adjustment in salary rates. " + "B" * 500
        source, spans = self.extract_synthetic("market_or_comparability_pressure", text)
        self.assertEqual(source["span_status"], "span_extracted")
        for span in spans:
            start, end = int(span["span_start_offset"]), int(span["span_end_offset"])
            self.assertEqual(text[start:end], span["span_text"])
            self.assertEqual(runner.text_sha256(span["span_text"]), span["span_sha256"])
            self.assertLessEqual(len(span["span_text"]), runner.MAX_SPAN_CHARACTERS)
            self.assertLessEqual(len(span["context_before"]), runner.CONTEXT_CHARACTERS)
            self.assertLessEqual(len(span["context_after"]), runner.CONTEXT_CHARACTERS)

    def test_positive_span_cap(self) -> None:
        text = "\n\n".join(f"Clause {index}: no strike or work stoppage shall occur." for index in range(20))
        source, spans = self.extract_synthetic("strike_or_no_strike_constraint", text)
        self.assertEqual(source["span_status"], "span_extracted")
        self.assertLessEqual(len(spans), runner.MAX_POSITIVE_SPANS_PER_SOURCE)

    def test_every_synthetic_record_keeps_downstream_statuses_closed(self) -> None:
        source, spans = self.extract_synthetic(
            "market_or_comparability_pressure",
            "A compensation study compares salary rates with peer municipalities.",
        )
        for row in [source, *spans]:
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_controlled_statuses_exact(self) -> None:
        self.assertEqual(runner.CONTROLLED_STATUSES, {"span_extracted", "no_span_or_weak", "ambiguous_span", "extraction_error"})

    def test_completed_outputs_when_present(self) -> None:
        decision_path = runner.OUTPUT_DIR / "targeted_evidence_span_extraction_321_decision.json"
        if not decision_path.is_file():
            return
        runner.validate_complete()
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(decision["span_extraction_queue_count"], 321)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_completed_positive_spans_exact(self) -> None:
        source_path = runner.OUTPUT_DIR / "targeted_evidence_span_extraction_321_results.csv"
        span_path = runner.OUTPUT_DIR / "targeted_evidence_span_extraction_321_span_records.csv"
        if not (source_path.is_file() and span_path.is_file()):
            return
        sources, spans = rows(source_path), rows(span_path)
        runner.validate_spans(sources, spans)

    def test_dashboard_exact_span_gate(self) -> None:
        completed, decision = dashboard.targeted_evidence_span_extraction_321_status()
        self.assertTrue(completed)
        self.assertEqual(decision["span_extraction_queue_count"], 321)
        self.assertEqual(decision["pdf_span_extraction_count"], 289)
        self.assertEqual(decision["html_span_extraction_count"], 32)
        self.assertEqual(decision["rating_candidate_count"], 201)
        self.assertTrue(decision["evidence_span_rating_ready_next"])
        self.assertFalse(decision["global_analysis_readiness"])

    def test_rating_candidates_are_only_positive_exact_spans(self) -> None:
        path = runner.OUTPUT_DIR / "targeted_evidence_span_extraction_321_rating_candidate_manifest.csv"
        if not path.is_file():
            return
        candidates = rows(path)
        self.assertEqual(len(candidates), 201)
        self.assertTrue(all(row["span_status"] == "span_extracted" for row in candidates))
        self.assertTrue(all(row["rating_status"] == "not_rated" for row in candidates))
        self.assertTrue(all(row["global_analysis_readiness"] == "false" for row in candidates))

    def test_future_prompt_preserves_rating_boundary(self) -> None:
        prompts = list(runner.OUTPUT_DIR.glob("next_targeted_evidence_span_*_prompt.md")) if runner.OUTPUT_DIR.exists() else []
        if not prompts:
            return
        text = prompts[0].read_text(encoding="utf-8").casefold()
        for phrase in ("separate explicit authorization", "exact substring", "do not", "rating is not causal proof", "global analysis readiness true"):
            self.assertIn(phrase, text)

    def test_partial_outputs_fail_closed(self) -> None:
        original = runner.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as directory:
            runner.OUTPUT_DIR = Path(directory)
            (runner.OUTPUT_DIR / runner.REQUIRED_FINAL_OUTPUTS[0]).touch()
            with self.assertRaises(RuntimeError):
                runner.validate_complete()
        runner.OUTPUT_DIR = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
