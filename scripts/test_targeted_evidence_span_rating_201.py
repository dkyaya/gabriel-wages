#!/usr/bin/env python3
"""Regression tests for bounded GABRIEL rating of 201 exact spans."""

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
RUNNER_PATH = ROOT / "scripts/run_targeted_evidence_span_rating_201.py"
SPEC = importlib.util.spec_from_file_location("targeted_evidence_span_rating_201", RUNNER_PATH)
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


class TargetedEvidenceSpanRating201Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.audit = runner.verify_inputs(verify_artifact_bytes=False)

    def response_for(self, row: dict[str, str]) -> dict[str, object]:
        quote = row["span_text"][: min(len(row["span_text"]), 120)]
        return {
            "span_extraction_id": row["span_extraction_id"],
            "rated_mechanism_family": row["target_mechanism_family"],
            "documentary_mechanism_support": "strong",
            "direct_text_support": "moderate",
            "provisional_causal_candidate_support": "weak",
            "direction_of_pressure": "neutral_or_unclear",
            "evidence_strength": "strong",
            "claim_relevance": "documentary_mechanism_claim",
            "quote_used": quote,
            "quote_exact_substring": True,
            "reason_code": "exact_mechanism_wording",
            "claim_boundary": "This rating describes only the supplied documentary wording and does not establish a wage effect or causal conclusion.",
            "no_wage_gap_claim": True,
            "no_final_causal_claim": True,
            "global_analysis_readiness": False,
        }

    def test_exact_201_scope_and_id_hash(self) -> None:
        self.assertEqual(len(self.queue), 201)
        self.assertEqual(len({row["span_extraction_id"] for row in self.queue}), 201)
        self.assertEqual(runner.id_set_hash(self.queue), runner.EXPECTED_ID_SET_HASH)

    def test_mechanism_counts(self) -> None:
        self.assertEqual(dict(Counter(row["target_mechanism_family"] for row in self.queue)), runner.EXPECTED_MECHANISMS)

    def test_only_positive_tier_a_b_unrated_rows(self) -> None:
        for row in self.queue:
            self.assertEqual(row["span_status"], "span_extracted")
            self.assertIn(row["priority_tier"], {"tier_a", "tier_b"})
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_all_inputs_are_pdf_derived(self) -> None:
        self.assertEqual(self.audit["pdf_rows"], 201)
        self.assertEqual(self.audit["html_rows"], 0)

    def test_exact_offsets_and_hashes_revalidate(self) -> None:
        for row in self.queue:
            start, end = int(row["span_start_offset"]), int(row["span_end_offset"])
            self.assertEqual(end - start, len(row["span_text"]))
            self.assertEqual(runner.text_sha256(row["span_text"]), row["span_sha256"])

    def test_context_bounds(self) -> None:
        self.assertTrue(all(len(row["context_before"]) <= 160 and len(row["context_after"]) <= 160 for row in self.queue))

    def test_prompt_omits_source_metadata_and_uses_bounded_payload(self) -> None:
        row = dict(self.queue[0])
        row.update({"source_url_or_locator": "SENTINEL_URL", "source_title": "SENTINEL_TITLE", "municipality": "SENTINEL_CITY", "bargaining_unit_name": "SENTINEL_UNIT"})
        prompt = runner.build_prompt(row)
        for sentinel in ("SENTINEL_URL", "SENTINEL_TITLE", "SENTINEL_CITY", "SENTINEL_UNIT"):
            self.assertNotIn(sentinel, prompt)
        self.assertIn(row["span_text"], prompt)
        self.assertIn(row["context_before"], prompt)
        self.assertIn(row["context_after"], prompt)

    def test_response_schema_is_closed_and_complete(self) -> None:
        schema = runner.response_schema()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))

    def test_valid_rating_passes(self) -> None:
        row = self.queue[0]
        parsed = self.response_for(row)
        self.assertEqual(runner.validate_rating(parsed, row), parsed)

    def test_paraphrased_quote_rejected(self) -> None:
        row = self.queue[0]
        parsed = self.response_for(row)
        parsed["quote_used"] = "This sentence was not present in the supplied span."
        with self.assertRaisesRegex(ValueError, "quote_not_exact_span_substring"):
            runner.validate_rating(parsed, row)

    def test_wrong_mechanism_rejected(self) -> None:
        row = self.queue[0]
        parsed = self.response_for(row)
        parsed["rated_mechanism_family"] = next(value for value in runner.MECHANISMS if value != row["target_mechanism_family"])
        with self.assertRaisesRegex(ValueError, "rated_mechanism_family_invalid"):
            runner.validate_rating(parsed, row)

    def test_final_claim_language_rejected(self) -> None:
        row = self.queue[0]
        parsed = self.response_for(row)
        parsed["claim_boundary"] = "This proves that the mechanism causes the wage gap."
        with self.assertRaisesRegex(ValueError, "forbidden_final_claim_language"):
            runner.validate_rating(parsed, row)

    def test_boundary_boolean_drift_rejected(self) -> None:
        row = self.queue[0]
        parsed = self.response_for(row)
        parsed["global_analysis_readiness"] = True
        with self.assertRaisesRegex(ValueError, "boundary_booleans_invalid"):
            runner.validate_rating(parsed, row)

    def test_preflight_selection_covers_all_mechanisms(self) -> None:
        selected = runner.select_preflight(self.queue)
        self.assertEqual({row["target_mechanism_family"] for row in selected}, set(runner.MECHANISMS))
        self.assertGreaterEqual(len(selected), 4)
        self.assertLessEqual(len(selected), 8)

    def test_mock_calls_persist_no_raw_payload(self) -> None:
        subset = self.queue[:2]

        def caller(items, **kwargs):
            results = []
            for row, (_, _) in zip(subset, items):
                results.append(runner.LiveResult(
                    "request-id", "success", json.dumps(self.response_for(row)), 0.1,
                    10, 20, 30, "", "", "2026-07-26T00:00:00+00:00",
                ))
            return results

        valid, quarantine, metadata, timing = runner.run_calls(
            subset, stage="test", key="not-persisted", model="test-model", timeout=1,
            parallel=1, max_attempts=1, caller=caller,
        )
        self.assertEqual(len(valid), 2)
        self.assertEqual(quarantine, [])
        self.assertEqual(len(metadata), 2)
        self.assertEqual(len(timing), 2)
        self.assertTrue(all(row["raw_prompt_saved"] == "false" and row["raw_response_saved"] == "false" for row in metadata))
        self.assertNotIn("prompt", metadata[0])
        self.assertNotIn("response_text", metadata[0])

    def test_flattened_rating_keeps_downstream_closed(self) -> None:
        row = self.queue[0]
        result = runner.LiveResult("id", "success", "", 0.1, 0, 0, 0, "", "", "now")
        flat = runner.flatten_rating(self.response_for(row), row, result, 1, "model")
        self.assertEqual(flat["rating_status"], "rated_valid")
        self.assertEqual(flat["ingestion_status"], "not_ingested")
        self.assertEqual(flat["codification_status"], "not_codified")
        self.assertEqual(flat["causal_status"], "not_causal_evidence")
        self.assertEqual(flat["global_analysis_readiness"], "false")

    def test_valid_plus_quarantine_reconciliation(self) -> None:
        row = self.queue[0]
        result = runner.LiveResult("id", "success", "", 0.1, 0, 0, 0, "", "", "now")
        valid = [runner.flatten_rating(self.response_for(item), item, result, 1, "model") for item in self.queue]
        checks = runner.validate_final(valid, [], self.queue)
        self.assertTrue(checks["valid_plus_quarantine_reconciles"])

    def test_partial_outputs_cannot_masquerade_as_complete(self) -> None:
        original = runner.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as directory:
            runner.OUTPUT_DIR = Path(directory)
            (runner.OUTPUT_DIR / runner.REQUIRED_FINAL_OUTPUTS[0]).touch()
            self.assertFalse(runner.completed())
        runner.OUTPUT_DIR = original

    def test_completed_outputs_when_present(self) -> None:
        if not (runner.OUTPUT_DIR / "targeted_evidence_span_rating_201_decision.json").is_file():
            return
        runner.validate_complete(self.queue)
        decision = json.loads((runner.OUTPUT_DIR / "targeted_evidence_span_rating_201_decision.json").read_text())
        self.assertEqual(decision["input_rows"], 201)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_rating_gate(self) -> None:
        if not (runner.OUTPUT_DIR / "targeted_evidence_span_rating_201_decision.json").is_file():
            return
        completed, decision = dashboard.targeted_evidence_span_rating_201_status()
        self.assertTrue(completed)
        self.assertEqual(decision["input_rows"], 201)
        self.assertEqual(decision["valid_rating_count"] + decision["quarantine_count"], 201)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_future_prompt_preserves_summary_boundaries(self) -> None:
        prompts = list(runner.OUTPUT_DIR.glob("next_targeted_evidence_span_rating_*_prompt.md")) if runner.OUTPUT_DIR.exists() else []
        if not prompts:
            return
        text = prompts[0].read_text(encoding="utf-8").casefold()
        for phrase in ("do not access urls", "do not", "rating is not causal proof", "global analysis readiness true"):
            self.assertIn(phrase, text)

    def test_runner_has_no_pdf_ocr_render_download_or_search_dependency(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8").casefold()
        for token in ("pytesseract", "ocrmypdf", "pdf2image", "pdftotext", "pdfinfo", "playwright", "selenium", "requests.get", "urllib.request"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
